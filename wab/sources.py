"""Collect → screen → grade. Deterministic; no model involved.

collect: read each manifest capture; if a capture is missing, try a GET-only fetch from an
         allowlisted domain with bounded retry. Failure is recorded as UNAVAILABLE — never replaced.
screen:  strip hidden characters, quarantine sources containing instructions aimed at the AI or the
         workflow, redact PII patterns, truncate over-long text (data minimisation).
grade:   assign High / Medium / Low from config/source_registry.yaml (instruction v1.1, C2).
"""
import re
import time
from urllib.parse import urlparse

import requests

from .core import ROOT, PolicyStop, append_escalation_log, iso, load_yaml, sha256_text


def _domain(url):
    return (urlparse(url).hostname or "").lower()


def collect(run, policy, manifest, manifest_dir):
    reg = load_yaml("config/source_registry.yaml")
    allow = set(reg["domains"])
    rp = policy["retry"]["fetch"]
    out = []
    for m in manifest["sources"]:
        src = dict(m, status="AVAILABLE", attempts=0, text=None, origin=None)
        cap = m.get("capture")
        cap_path = (manifest_dir / cap).resolve() if cap else None
        if cap_path and cap_path.exists():
            text = cap_path.read_text(encoding="utf-8")
            if m.get("sha256") and sha256_text(text) != m["sha256"]:
                src.update(status="UNAVAILABLE", reason="capture hash does not match manifest (file changed after capture)")
                run.log("collect", "capture_hash_mismatch", source=m["id"])
            else:
                src.update(text=text, origin=str(cap_path.relative_to(ROOT)))
        else:
            dom = _domain(m["url"])
            if dom not in allow:
                src.update(status="UNAVAILABLE", reason=f"no capture and domain {dom} is not on the fetch allowlist")
                run.log("collect", "fetch_refused_not_allowlisted", source=m["id"], domain=dom)
            else:
                run.log("collect", "capture_missing_try_live_fetch", source=m["id"], url=m["url"])
                err = None
                for attempt in range(1, rp["max_attempts"] + 1):
                    src["attempts"] = attempt
                    try:
                        r = requests.get(m["url"], timeout=rp["timeout_seconds"], headers={"User-Agent": "wab/1.0 (+governed brief workflow)"})
                        if r.status_code != 200 or len(r.text) < 200:
                            raise RuntimeError(f"HTTP {r.status_code}, {len(r.text)} bytes")
                        src.update(text=r.text, origin=f"live fetch {m['url']}")
                        run.log("collect", "fetch_ok", source=m["id"], attempt=attempt)
                        err = None
                        break
                    except Exception as e:
                        err = str(e)[:200]
                        run.log("collect", "fetch_failed", source=m["id"], domain=dom, attempt=attempt, msg=err)
                        run.save(retry_count=run.state.get("retry_count", 0) + (1 if attempt < rp["max_attempts"] else 0))
                        if attempt < rp["max_attempts"]:
                            time.sleep(rp["backoff_seconds"][min(attempt - 1, len(rp["backoff_seconds"]) - 1)])
                if err:
                    src.update(status="UNAVAILABLE", reason=f"capture missing; live fetch failed after {rp['max_attempts']} attempts ({err})")
        if src["status"] == "UNAVAILABLE":
            run.log("collect", "source_unavailable", source=m["id"], required=bool(m.get("required")), msg=src["reason"])
        out.append(src)

    unavailable = [s for s in out if s["status"] == "UNAVAILABLE"]
    run.save(unavailable=[{"id": s["id"], "required": bool(s.get("required")), "reason": s["reason"]} for s in unavailable])
    req_missing = [s["id"] for s in unavailable if s.get("required")]
    if req_missing:
        raise PolicyStop("ESCALATED", "SOURCE_UNAVAILABLE_REQUIRED",
                         f"required source(s) {', '.join(req_missing)} unavailable after the retry limit; no brief is drafted from a partial pack", "owner")
    if out and len(unavailable) / len(out) > 0.25:
        raise PolicyStop("ESCALATED", "TOO_MANY_UNAVAILABLE", f"{len(unavailable)} of {len(out)} sources unavailable (> 25%)", "owner")
    return out


def screen(run, policy, sources):
    sec = policy["security"]
    inj = [re.compile(p) for p in sec["injection_patterns"]]
    hidden = [re.compile(p) for p in sec["hidden_text_patterns"]]
    pii = {k: re.compile(v) for k, v in sec["pii_patterns"].items()}
    limit = sec["max_chars_per_source"]
    redactions, truncations, quarantined = [], [], []
    for s in sources:
        if s["status"] != "AVAILABLE":
            continue
        text = s["text"]
        flags = []
        for h in hidden:
            if h.search(text):
                text = h.sub("", text)
                flags.append("hidden characters removed")
        for kind, p in pii.items():  # data minimisation first, so even quarantined text is stored redacted
            n = len(p.findall(text))
            if n:
                text = p.sub(f"[REDACTED-{kind.upper()}]", text)
                redactions.append({"id": s["id"], "type": kind, "count": n})
                flags.append(f"{n} {kind} redacted")
                run.log("screen", "pii_redacted", source=s["id"], type=kind, count=n)
        hits = sorted({m.group(0)[:60] for p in inj for m in p.finditer(text)})
        if hits:
            s.update(status="QUARANTINED", text=text, flags=flags, reason=f"contains instructions aimed at the AI or the workflow: {hits}")
            quarantined.append({"id": s["id"], "matches": hits})
            run.log("screen", "quarantined", source=s["id"], msg=f"{len(hits)} instruction pattern(s): {hits}")
            continue
        if len(text) > limit:
            truncations.append({"id": s["id"], "from_chars": len(text), "to_chars": limit})
            text = text[:limit] + "\n[TRUNCATED by workflow: data minimisation limit]"
            flags.append("truncated")
        s.update(text=text, flags=flags)
    run.save(redactions=redactions, truncations=truncations, quarantined=quarantined)
    run.log("screen", "done", msg=f"{len(quarantined)} quarantined, {len(redactions)} redaction(s), {len(truncations)} truncation(s)")
    if quarantined:
        who = policy["escalation"]["security_contact"]
        ids = ", ".join(q["id"] for q in quarantined)
        # v1.3.0: the notice is a written record for the security contact, not only a log line
        run.write("security_notice.md", f"# Security notice — {run.id}\n\nTo: {who}\nCode: INJECTION_QUARANTINED\nRaised: {iso()}\n\n"
                  f"## What happened\nThe screen found text aimed at the AI or the workflow in: {ids}.\n\n"
                  + "\n".join(f"- {q['id']}: {q['matches']}" for q in quarantined)
                  + "\n\n## What the workflow did\n- The quarantined text was never sent to the model.\n- The run continues without it; the brief and "
                  "the approval request disclose it.\n- PII in the source was redacted before storage.\n\n## Decision needed\nReview the source "
                  "and decide whether its publisher stays on the allowlist.\n")
        append_escalation_log(f"- {iso()} · {run.id} · INJECTION_QUARANTINED · to {who} · {ids} quarantined; run continued without it (runs/{run.id}/security_notice.md)")
        run.log("screen", "escalation_notice", code="INJECTION_QUARANTINED", route="security_contact", recipient=who,
                msg=f"notice to {who} (runs/{run.id}/security_notice.md); run continues without {ids}; disclosed in the brief and the approval request")
    return sources


def grade(run, sources):
    reg = load_yaml("config/source_registry.yaml")
    for s in sources:
        cls = reg["domains"].get(_domain(s["url"]), "unknown")
        if cls in ("established_news", "trade_press") and any(b.lower() in (s.get("author") or "").lower() for b in reg["official_agency_bylines"]):
            cls = "official_relay"
        s["class"], s["grade"] = cls, reg["class_grades"][cls]
    run.log("grade", "done", msg=", ".join(f"{s['id']}={s['grade']}" for s in sources))
    return sources
