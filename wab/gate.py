"""Human approval gate. The workflow pauses here; only an explicit, recorded YES from an authorised
approver, bound to the exact text shown (SHA-256), lets the publish step run. Silence never approves."""
import datetime as dt
import json

from .core import PolicyStop, iso, now, sha256_file, sha256_text


def request_approval(run, policy, cfg, sources, verdicts, checks, brief_rel):
    brief_path = run.dir / brief_rel
    brief = brief_path.read_text(encoding="utf-8")
    brief_sha = sha256_text(brief)
    expires = now() + dt.timedelta(hours=policy["approval"]["expires_after_hours"])
    week = run.state["week"]
    target = f"{cfg['publish']['repo_url']}/blob/{cfg['publish']['branch']}/{cfg['publish']['folder']}/{week}.md"
    used = [s for s in sources if s["status"] == "AVAILABLE"]
    exc = [s for s in sources if s["status"] != "AVAILABLE"]
    lines = [
        f"# Approval request — {run.id}",
        "",
        f"**Decision needed from:** {', '.join(policy['approval']['approvers'])} (Workflow Owner)  ",
        f"**Requested:** {iso()}  ·  **Expires:** {iso(expires)} — if no explicit decision is recorded by then, the run ends as EXPIRED and nothing is published.  ",
        f"**Policy:** {policy['policy_id']} v{policy['version']}  ·  **Workflow:** v{cfg['workflow_version']}",
        "",
        "## What happens on YES",
        f"The workflow commits exactly one file, `{cfg['publish']['folder']}/{week}.md`, containing the brief below, to "
        f"`{cfg['publish']['repo_url']}` (branch `{cfg['publish']['branch']}`) and pushes it. It becomes public at {target}.",
        "On NO, nothing is published and the run ends as REJECTED.",
        "",
        f"**Text being approved:** SHA-256 `{brief_sha}`. Any change to the text after this request invalidates the approval.",
        "",
        "## Audit result (rubric v1.1)",
        "| Criterion | Verdict | Judge |",
        "|---|---|---|",
    ]
    lines += [f"| {c} | {verdicts[c]['verdict']} | {verdicts[c]['judge']} |" for c in sorted(verdicts)]
    lines += ["", "Deterministic checks: " + ", ".join(f"{c['id']} {c['result']}" for c in checks), "",
              "## Sources",
              f"- Used: {len(used)} — " + ", ".join(f"{s['id']} ({s['grade']})" for s in used),
              f"- Excluded by the workflow: {len(exc)} — " + (", ".join(f"{s['id']} {s['status']}" for s in exc) or "none")]
    q = run.state.get("quarantined") or []
    lines += ["", "## Security and privacy flags",
              f"- Quarantined for instructions aimed at the AI or the workflow: {', '.join(x['id'] for x in q) or 'none'}"
              + (" — routed to the Head of Information Security (INJECTION_QUARANTINED)." if q else ""),
              f"- PII redactions: {run.state.get('redactions') or 'none'}",
              f"- Test fixtures in this run: {run.state.get('test_fixtures') or 'none'}",
              "", "## The brief (exactly as it would be published)", "", "---", "", brief]
    text = "\n".join(lines)
    run.write("approval_request.md", text)
    run.save(status="AWAITING_APPROVAL", approval_request=run.rel("approval_request.md"),
             approval_request_sha256=sha256_text(text), brief_file=run.rel(brief_rel), brief_sha256=brief_sha,
             approval_requested_at=iso(), approval_expires_at=iso(expires), publish_target=target)
    run.log("gate", "approval_requested", msg=f"paused — waiting for an explicit YES/NO from {policy['approval']['approvers']}; expires {iso(expires)}",
            brief_sha256=brief_sha, request=run.rel("approval_request.md"))


def expired(run):
    exp = run.state.get("approval_expires_at")
    return bool(exp) and now() > dt.datetime.fromisoformat(exp)


def record_decision(run, policy, *, decision, approver, channel, statement):
    st = run.state.get("status")
    if st != "AWAITING_APPROVAL":
        raise PolicyStop(st, "APPROVAL_NOT_PENDING", f"run is {st}, not awaiting approval; decision not recorded")
    if expired(run):
        raise PolicyStop("EXPIRED", "APPROVAL_EXPIRED", "approval window closed before a decision was recorded; nothing published", "owner")
    d = (decision or "").strip().upper()
    if d not in policy["approval"]["accepted_decisions"]:
        raise ValueError(f"decision must be one of {policy['approval']['accepted_decisions']}; got {decision!r}. Nothing recorded.")
    if approver not in policy["approval"]["approvers"]:
        raise ValueError(f"{approver!r} is not an authorised approver {policy['approval']['approvers']}. Nothing recorded.")
    if not (statement or "").strip():
        raise ValueError("the approver's own words (--statement) are required. Nothing recorded.")
    current = sha256_file(run.dir.parent.parent / run.state["brief_file"])
    if current != run.state["brief_sha256"]:
        raise PolicyStop("BLOCKED_BY_POLICY", "TEXT_CHANGED_AFTER_REQUEST", "brief text changed after the approval request; a new request is required", "owner")
    rec = {"run_id": run.id, "decision": d, "approver": approver, "channel": channel, "statement": statement.strip(),
           "decided_at": iso(), "brief_sha256": run.state["brief_sha256"], "approval_request_sha256": run.state["approval_request_sha256"],
           "policy_version": policy["version"]}
    run.write("approval.json", json.dumps(rec, indent=2, ensure_ascii=False))
    run.save(approver=approver, approval_decision=d, approval_statement=statement.strip(), approval_channel=channel, approval_at=rec["decided_at"],
             status="APPROVED" if d == "YES" else "REJECTED")
    run.log("gate", "decision_recorded", decision=d, approver=approver, channel=channel, msg=f"{d} by {approver}: {statement.strip()[:120]}")
    return rec
