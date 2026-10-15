"""The bounded workflow. One call to start() performs at most one run and ends either paused at the
approval gate or in a terminal state. Nothing loops without a counter; every stop is logged."""
import datetime as dt
import json
from pathlib import Path

import yaml

from . import audit, gate, llm, monitor, prompts, publish, sources
from .core import (ROOT, PolicyStop, Run, iso, kill_switch_active, load_config, load_policy, next_run_id,
                   now, write_run_log_row)



def _ctx(manifest, srcs):
    w = manifest["reporting_window"]
    s, e = (dt.date.fromisoformat(w["start"]), dt.date.fromisoformat(w["end"]))
    watch_path = ROOT / manifest["previous_watchlist"] if manifest.get("previous_watchlist") else None
    return {"window_label": f"{s:%d %b} – {e:%d %b %Y}", "issue_date": f"{now():%d %b %Y}",
            "n_total": len(srcs), "n_available": sum(x["status"] == "AVAILABLE" for x in srcs),
            "watchlist": watch_path.read_text(encoding="utf-8") if watch_path and watch_path.exists() else "None."}


def _escalate(run, policy, code, message, route):
    who = policy["escalation"]["security_contact"] if route == "security_contact" else policy["escalation"]["owner"]
    text = (f"# Escalation — {run.id}\n\nTo: {who}\nCode: {code}\nRaised: {iso()}\nRun status: {run.state.get('final_status') or run.state.get('status')}\n\n"
            f"## What happened\n{message}\n\n## What the workflow did\n"
            f"- Retries performed this run: {run.state.get('retry_count', 0)} (bounded by policy.retry)\n"
            f"- Fallback: {run.state.get('fallback') or 'none'}\n"
            f"- Nothing was published by this run; no data was invented or substituted.\n\n"
            f"## Decision needed\nReview runs/{run.id}/events.jsonl, resolve the cause, then start a new run (the workflow does not retry on its own).\n")
    run.write("escalation.md", text)
    (ROOT / "monitoring").mkdir(exist_ok=True)
    with (ROOT / "monitoring/escalations.md").open("a", encoding="utf-8") as f:
        f.write(f"- {iso()} · {run.id} · {code} · to {who} · {message}\n")
    run.save(escalation_code=code, escalation_recipient=who)
    run.log("escalate", code, recipient=who, msg=message)


def _finish(run, policy, status, code=None, message="", route=None):
    week = run.state.get("week")
    pub = ROOT / "published" / f"{week}.md"
    run.save(status=status, final_status=status, ended_at=iso())
    if code:
        errs = run.state.get("errors") or []
        errs.append(f"{code}: {message}")
        run.save(errors=errs)
    if route:
        _escalate(run, policy, code, message, route)
    published_by_this_run = status == "COMPLETED"
    run.save(stop_confirmation=(f"Run ended in terminal state {status} at {iso()}. "
                                + ("Published once; no further actions." if published_by_this_run
                                   else f"Nothing published by this run (published/{week}.md {'exists from an earlier run' if pub.exists() else 'absent — verified'}).")))
    run.log("stop", status, msg=run.state["stop_confirmation"])
    write_run_log_row(run)
    monitor.build()


def start(manifest_path, trigger="manual", operator=None):
    policy, cfg = load_policy(), load_config()
    mpath = (ROOT / manifest_path).resolve()
    manifest = yaml.safe_load(mpath.read_text(encoding="utf-8"))
    week = manifest["week"]
    run = Run(next_run_id(week))
    run.save(run_id=run.id, started_at=iso(), operator=operator or cfg["operator_default"], trigger=trigger,
             workflow_version=cfg["workflow_version"], policy_version=policy["version"], policy_sha256=policy["_sha256"],
             week=week, manifest=str(mpath.relative_to(ROOT)), status="STARTED", retry_count=0, llm_calls=0, llm_cost_usd=0.0,
             input_source_ids=[s["id"] for s in manifest["sources"]],
             test_fixtures=[s["id"] for s in manifest["sources"] if s.get("test_fixture")])
    run.write("inputs/manifest.yaml", mpath.read_text(encoding="utf-8"))
    run.log("trigger", "run_started", trigger=trigger, manifest=str(mpath.relative_to(ROOT)),
            msg=f"workflow v{cfg['workflow_version']}, policy v{policy['version']}")
    route = ["preflight"]
    try:
        # ---- preflight (stop rules) -------------------------------------------------------
        ks = kill_switch_active(policy)
        if ks:
            raise PolicyStop("STOPPED", "KILL_SWITCH", f"run refused: {ks}")
        if manifest.get("classification") != "public":
            raise PolicyStop("BLOCKED_BY_POLICY", "DATA_NOT_PUBLIC", "manifest classification is not 'public'; only public data is permitted", "owner")
        if (ROOT / cfg["publish"]["folder"] / f"{week}.md").exists():
            raise PolicyStop("BLOCKED_BY_POLICY", "ALREADY_PUBLISHED", f"{week} is already published; one publication per week")
        started = len(list((ROOT / "runs").glob(f"RUN-{week}-*")))
        if started > policy["budgets"]["max_runs_started_per_week"]:
            raise PolicyStop("BLOCKED_BY_POLICY", "TOO_MANY_RUNS", f"{started} runs started for {week} (limit {policy['budgets']['max_runs_started_per_week']})", "owner")
        run.log("preflight", "ok", msg="kill switch off; data classification public; week not yet published; run count within limit")
        checks_done = ["kill switch", "data classification", "one publication per week", "runs per week"]

        # ---- collect → screen → grade -----------------------------------------------------
        route.append("collect")
        try:
            srcs = sources.collect(run, policy, manifest, mpath.parent)
        except PolicyStop:
            run.save(fallback="missing sources marked UNAVAILABLE and disclosed; no substitute content; run stopped before drafting",
                     route=" → ".join(route), checks_performed=checks_done + ["capture hashes", "fetch allowlist", "required sources"])
            raise
        route += ["screen", "grade"]
        srcs = sources.grade(run, sources.screen(run, policy, srcs))
        checks_done += ["capture hashes", "fetch allowlist", "required sources", "injection screen", "PII screen", "length limit", "source grading"]
        run.write("inputs/source_status.json", json.dumps([{k: v for k, v in s.items() if k != "text"} for s in srcs], indent=2, ensure_ascii=False))
        ctx = _ctx(manifest, srcs)
        if any(s["status"] == "UNAVAILABLE" for s in srcs):
            run.save(fallback="unavailable source(s) disclosed in the brief; no substitute content")

        # ---- draft → audit → bounded targeted revision -------------------------------------
        route.append("draft")
        brief = llm.call(run, policy, purpose="draft", system=prompts.DRAFT_SYSTEM, prompt=prompts.draft_prompt(ctx, srcs), model=cfg["models"]["drafter"])
        run.write("drafts/v1.md", brief)
        max_rev = policy["retry"]["audit_revisions"]
        version = 1
        for round_no in range(1, max_rev + 2):  # audits = revisions + 1 (bounded)
            verdicts, checks, fails, counts = audit.audit(run, policy, cfg, ctx, srcs, brief, round_no)
            route.append(f"audit r{round_no} ({11 - len(fails)}/11)")
            run.save(audit_rounds=round_no, audit_verdict=f"{11 - len(fails)}/11 PASS (round {round_no})")
            if not fails:
                break
            esc = [f for f in fails if str(f.get("required_fix", "")).strip().upper().startswith("ESCALATE")]
            if esc:  # policy v1.1: carried to the approver, never resolved by finding or inventing evidence
                seen = run.state.get("judge_escalations") or []
                seen += [{"round": round_no, "criterion": f["id"], "judge": f["judge"], "fix": f["required_fix"][:500]} for f in esc]
                run.save(judge_escalations=seen)
                run.log("audit", "judge_escalation", round=round_no, msg="; ".join(f"{f['id']}: {f['required_fix'][:160]}" for f in esc))
            if round_no > max_rev:
                if esc:
                    raise PolicyStop("ESCALATED", "AUDIT_ESCALATE", "; ".join(f"{f['id']}: {f['required_fix']}" for f in esc)[:600], "owner")
                raise PolicyStop("ESCALATED", "AUDIT_FAIL_AFTER_MAX_REVISIONS",
                                 f"still failing after {max_rev} revisions: {[f['id'] for f in fails]}", "owner")
            failures = [{"id": f["id"], "source": f.get("deterministic_fail") or f["judge"], "detail": f.get("evidence", ""),
                         "fix": f.get("required_fix", "")} for f in fails]
            brief = llm.call(run, policy, purpose=f"revise_{round_no}", system=prompts.DRAFT_SYSTEM,
                             prompt=prompts.revise_prompt(ctx, srcs, brief, failures, counts), model=cfg["models"]["drafter"])
            version += 1
            run.write(f"drafts/v{version}.md", brief)
            route.append(f"revise v{version}")
        run.write("brief_final.md", brief)
        run.save(audit_verdict="PASS 11/11", checks_performed=checks_done + ["deterministic brief checks DC01–DC09", "3-judge audit R01–R11"],
                 decision_notes=f"{version - 1} targeted revision(s); final text = drafts/v{version}.md",
                 remaining_caveats=_caveats(brief))

        # ---- approval gate: pause --------------------------------------------------------
        route.append("approval gate (paused)")
        run.save(route=" → ".join(route))
        gate.request_approval(run, policy, cfg, srcs, verdicts, checks, "brief_final.md")
        write_run_log_row(run)
        monitor.build()
        return run
    except PolicyStop as e:
        run.save(route=" → ".join(route) + f" → STOP {e.code}")
        _finish(run, policy, e.status, e.code, e.message, e.route)
        return run


def _caveats(brief):
    sec = brief.split("## For human decision")
    if len(sec) < 2:
        return ""
    return sec[1].split("## Sources")[0].strip()[:900]


def approve(run_id, decision, approver, channel, statement):
    policy = load_policy()
    run = Run(run_id)
    try:
        rec = gate.record_decision(run, policy, decision=decision, approver=approver, channel=channel, statement=statement)
    except PolicyStop as e:
        if e.status in ("EXPIRED", "BLOCKED_BY_POLICY"):
            _finish(run, policy, e.status, e.code, e.message, e.route)
        else:
            run.log("gate", "decision_refused", msg=e.message)
        return run
    if rec["decision"] == "NO":
        run.save(route=run.state.get("route", "") + " → decision NO")
        _finish(run, policy, "REJECTED", None, "")
    else:
        write_run_log_row(run)
    return run


def resume(run_id):
    """Continue a paused run. Publishes only if publish.validate_approval() passes."""
    policy, cfg = load_policy(), load_config()
    run = Run(run_id)
    ks = kill_switch_active(policy)
    if ks:
        run.log("resume", "refused", msg=f"kill switch: {ks}")
        _finish(run, policy, "STOPPED", "KILL_SWITCH", f"resume refused: {ks}")
        return run
    st = run.state.get("status")
    if st == "AWAITING_APPROVAL" and gate.expired(run):
        _finish(run, policy, "EXPIRED", "APPROVAL_EXPIRED", "no explicit decision before expiry; nothing published", "owner")
        return run
    if st not in ("AWAITING_APPROVAL", "APPROVED"):
        run.log("resume", "refused", msg=f"run is {st}; nothing to resume")
        return run
    try:
        rel, commit = publish.publish(run, policy, cfg)
        run.save(route=run.state.get("route", "") + f" → decision YES → published {rel} ({commit[:10]})")
        _finish(run, policy, "COMPLETED")
    except PolicyStop as e:
        if e.status == "AWAITING_APPROVAL":
            # silence is not approval: refuse, stay paused, record the attempt
            run.log("publish", "refused", code=e.code, msg=e.message)
            run.save(errors=(run.state.get("errors") or []) + [f"{e.code}: {e.message}"])
            write_run_log_row(run)
            monitor.build()
        else:
            _finish(run, policy, e.status, e.code, e.message, e.route)
    return run
