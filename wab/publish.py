"""Publish step — the only action that changes an external system. It re-validates the approval
itself (it does not trust the caller), writes one file and pushes it with bounded retry."""
import datetime as dt
import json
import subprocess
import time

from .core import ROOT, PolicyStop, iso, now, sha256_file


def _git(*args, check=True):
    p = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=120)
    if check and p.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {p.stderr.strip()[-300:]}")
    return p.stdout.strip()


def validate_approval(run, policy):
    """Every condition must hold, or publishing is refused. Returns the approval record."""
    ap = run.dir / "approval.json"
    if not ap.exists():
        raise PolicyStop("AWAITING_APPROVAL", "NO_APPROVAL_RECORDED",
                         "publish refused: no explicit decision has been recorded (silence is never approval)")
    rec = json.loads(ap.read_text())
    if rec.get("decision") != "YES":
        raise PolicyStop("REJECTED", "APPROVAL_IS_NO", "publish refused: the recorded decision is NO")
    if rec.get("approver") not in policy["approval"]["approvers"]:
        raise PolicyStop("BLOCKED_BY_POLICY", "UNAUTHORISED_APPROVER", f"publish refused: {rec.get('approver')!r} is not an authorised approver", "owner")
    if rec.get("policy_version") != policy["version"]:
        raise PolicyStop("BLOCKED_BY_POLICY", "POLICY_CHANGED", "publish refused: policy version changed since approval", "owner")
    if sha256_file(ROOT / run.state["brief_file"]) != rec["brief_sha256"]:
        raise PolicyStop("BLOCKED_BY_POLICY", "TEXT_CHANGED_AFTER_APPROVAL", "publish refused: brief text differs from the approved text", "owner")
    if now() > dt.datetime.fromisoformat(run.state["approval_expires_at"]):
        raise PolicyStop("EXPIRED", "APPROVAL_EXPIRED", "publish refused: approval window has closed", "owner")
    return rec


def publish(run, policy, cfg):
    rec = validate_approval(run, policy)
    week = run.state["week"]
    rel = f"{cfg['publish']['folder']}/{week}.md"
    dest = ROOT / rel
    if dest.exists() and policy["stop_rules"]["one_publication_per_week"]:
        raise PolicyStop("BLOCKED_BY_POLICY", "ALREADY_PUBLISHED", f"{rel} already exists; one publication per week", "owner")
    _git("fetch", "origin", cfg["publish"]["branch"])
    ahead = _git("rev-list", "--count", f"origin/{cfg['publish']['branch']}..HEAD")
    if ahead != "0":
        raise PolicyStop("BLOCKED_BY_POLICY", "UNPUSHED_LOCAL_COMMITS",
                         f"publish refused: {ahead} local commit(s) not on origin; the publish push must carry only the brief", "owner")
    brief = (ROOT / run.state["brief_file"]).read_text(encoding="utf-8")
    header = (f"<!-- Published by the Weekly AI Governance Brief workflow. Run {run.id}; approved by {rec['approver']} "
              f"at {rec['decided_at']} ({rec['channel']}); approved text SHA-256 {rec['brief_sha256']}; policy v{rec['policy_version']}; "
              f"audit {run.state.get('audit_verdict')}. Evidence: runs/{run.id}/ -->\n\n")
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(header + brief, encoding="utf-8")
    _git("add", rel)
    _git("commit", "-m", f"Publish {week} brief ({run.id}; approved by {rec['approver']})", "--", rel)
    commit = _git("rev-parse", "HEAD")
    rp = policy["retry"]["publish"]
    err = None
    for attempt in range(1, rp["max_attempts"] + 1):
        try:
            _git("push", "origin", f"HEAD:{cfg['publish']['branch']}")
            remote = _git("ls-remote", "origin", f"refs/heads/{cfg['publish']['branch']}").split()[0]
            if remote != commit:
                raise RuntimeError(f"remote head {remote[:10]} != published commit {commit[:10]}")
            run.log("publish", "pushed", attempt=attempt, commit=commit, file=rel)
            err = None
            break
        except Exception as e:
            err = str(e)[:300]
            run.log("publish", "push_failed", attempt=attempt, msg=err)
            run.save(retry_count=run.state.get("retry_count", 0) + (1 if attempt < rp["max_attempts"] else 0))
            if attempt < rp["max_attempts"]:
                time.sleep(rp["backoff_seconds"][min(attempt - 1, len(rp["backoff_seconds"]) - 1)])
    if err:
        raise PolicyStop("PUBLISH_FAILED", "PUBLISH_FAILED", f"push failed after {rp['max_attempts']} attempts; approved text kept at {run.state['brief_file']} ({err})", "owner")
    run.save(output_location=f"{cfg['publish']['repo_url']}/blob/{cfg['publish']['branch']}/{rel}", published_commit=commit, published_at=iso())
    return rel, commit
