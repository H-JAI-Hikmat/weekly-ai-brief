"""The bounded workflow. One call to start() performs at most one run and ends either paused at the
approval gate or in a terminal state. Nothing loops without a counter; every stop is logged."""
import datetime as dt
import json
import traceback
from pathlib import Path

import yaml

from . import audit, gate, llm, monitor, prompts, publish, sources
from .assemble import assemble
from .checks import run_checks
from .core import (ROOT, PolicyStop, Run, acquire_lock, append_escalation_log, interrupted_reason, iso, kill_switch_active, last_event_at,
                   load_config, load_policy, next_run_id, now, release_lock, write_run_log_row)

# v1.3.0: what the drafter is asked to do when a deterministic check fails before the judges run
MECH_FIX = {
    "DC01": "Use exactly the required section headings in the required order.",
    "DC02": "Shorten: BODY ≤ 430 and WHOLE ≤ 800 words, at most 5 items, headlines ≤ 12 words. Delete or shorten; add nothing.",
    "DC03": "Remove or correct every citation of a Source ID that is not in the pack.",
    "DC04": "Do not cite a workflow-excluded source as evidence.",
    "DC05": "List every workflow-excluded source under 'Excluded or unverified' with the workflow's reason.",
    "DC06": "Remove the personal data.",
    "DC07": "Replace the loaded term with neutral wording.",
    "DC08": "Give every item all four fields: What happened, Why it matters to us, Action, Confidence.",
    "DC09": "Write every date as DD Mon YYYY.",
}



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
    append_escalation_log(f"- {iso()} · {run.id} · {code} · to {who} · {message}")
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
    release_lock(run)
    write_run_log_row(run)
    monitor.build()


def _route_from_events(run):
    """Rebuild the route of a run that never reached its own end (used when closing an interrupted run)."""
    route = []
    for line in run.events.read_text(encoding="utf-8").splitlines():
        e = json.loads(line)
        if e["stage"] == "audit" and e["event"] == "verdict":
            route.append(f"audit r{e['round']} ({e['msg'].split(' PASS')[0]})")
        elif e["stage"] == "llm" and e["event"] == "call_ok" and str(e.get("purpose", "")).startswith(("revise_", "fix_checks_")):
            route.append(e["purpose"].replace("_", " "))
        elif e["stage"] in ("preflight", "draft") or (e["stage"] == "llm" and e.get("purpose") == "draft"):
            route.append("draft" if e["stage"] == "llm" else e["stage"])
        elif e["stage"] in ("collect", "screen", "grade") and (not route or route[-1] != e["stage"]):
            route.append(e["stage"])
    out = []
    for r in route:
        if not out or out[-1] != r:
            out.append(r)
    return " → ".join(out)


def close_interrupted(policy, closed_by, exclude=None):
    """Close every run whose process ended without a terminal state. Returns the IDs closed."""
    closed = []
    for d in sorted((ROOT / "runs").glob("RUN-*")):
        if d.name == exclude or not (d / "state.json").exists():
            continue
        run = Run(d.name)
        why = interrupted_reason(run, policy)
        if not why:
            continue
        last = last_event_at(run)
        msg = (f"Run interrupted: {why}. It never reached a terminal state; its last event was at {iso(last) if last else 'n/a'}. "
               f"Closed by {closed_by}. Nothing was published by this run. Start a new run if this week still needs a brief.")
        run.log("recovery", "run_interrupted", closed_by=closed_by, msg=msg)
        run.save(route=(run.state.get("route") or _route_from_events(run)) + " → INTERRUPTED (closed later)",
                 fallback="run closed as interrupted; no partial output used")
        _finish(run, policy, "ESCALATED", "RUN_INTERRUPTED", msg, "owner")
        closed.append(run.id)
    return closed


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
    acquire_lock(run)
    run.log("trigger", "run_started", trigger=trigger, manifest=str(mpath.relative_to(ROOT)),
            msg=f"workflow v{cfg['workflow_version']}, policy v{policy['version']}")
    route = ["preflight"]
    try:
        return _start(run, policy, cfg, manifest, mpath, week, route)
    except Exception as e:  # v1.3.0: an unexpected error still ends in a terminal state with a stop confirmation
        run.write("error.txt", traceback.format_exc())
        run.save(route=" → ".join(route) + " → STOP INTERNAL_ERROR")
        _finish(run, policy, "ESCALATED", "INTERNAL_ERROR", f"unexpected error: {e!r}"[:400] + f" (traceback: runs/{run.id}/error.txt)", "owner")
        return run


def _start(run, policy, cfg, manifest, mpath, week, route):
    try:
        # ---- preflight (stop rules) -------------------------------------------------------
        ks = kill_switch_active(policy)
        if ks:
            raise PolicyStop("STOPPED", "KILL_SWITCH", f"run refused: {ks}")
        if manifest.get("classification") != "public":
            raise PolicyStop("BLOCKED_BY_POLICY", "DATA_NOT_PUBLIC", "manifest classification is not 'public'; only public data is permitted", "owner")
        if (ROOT / cfg["publish"]["folder"] / f"{week}.md").exists():
            raise PolicyStop("BLOCKED_BY_POLICY", "ALREADY_PUBLISHED", f"{week} is already published; one publication per week")
        closed = close_interrupted(policy, closed_by=f"{run.id} preflight", exclude=run.id)
        if closed:
            run.log("preflight", "closed_interrupted_runs", runs=closed, msg=f"closed {closed} as RUN_INTERRUPTED (escalated to the Owner)")
        same = []
        for d in (ROOT / "runs").glob(f"RUN-{week}-*"):
            sp = d / "state.json"
            if sp.exists() and json.loads(sp.read_text()).get("policy_version") == policy["version"]:
                same.append(d.name)
        if len(same) > policy["budgets"]["max_runs_started_per_week"]:
            raise PolicyStop("BLOCKED_BY_POLICY", "TOO_MANY_RUNS",
                             f"{len(same)} runs started for {week} under policy v{policy['version']} (limit {policy['budgets']['max_runs_started_per_week']})", "owner")
        run.log("preflight", "ok", msg=f"kill switch off; data classification public; week not yet published; "
                                       f"run {len(same)} of {policy['budgets']['max_runs_started_per_week']} this week under policy v{policy['version']}; no interrupted runs left open")
        checks_done = ["kill switch", "data classification", "one publication per week", "runs per week (per policy version)", "interrupted runs"]

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
        raw = llm.call(run, policy, purpose="draft", system=prompts.DRAFT_SYSTEM, prompt=prompts.draft_prompt(ctx, srcs), model=cfg["models"]["drafter"])
        brief, used = assemble(raw, srcs)  # v1.3.0: Sources table and count built by the workflow
        run.write("drafts/v1.md", brief)
        max_rev = policy["retry"]["audit_revisions"]
        max_mech = policy["retry"].get("mechanical_fixes", 0)
        version, mech_used, history = 1, 0, []
        for round_no in range(1, max_rev + 2):  # audits = revisions + 1 (bounded)
            # v1.3.0: cheap deterministic checks first; failures go back for a bounded mechanical fix before any judge runs
            checks, counts = run_checks(brief, srcs, policy)
            while any(c["result"] == "FAIL" for c in checks) and mech_used < max_mech:
                mech_used += 1
                bad = [c for c in checks if c["result"] == "FAIL"]
                run.log("audit", "precheck_failed", round=round_no, fix=mech_used,
                        msg=f"{[c['id'] for c in bad]} — mechanical fix {mech_used} of {max_mech} before the judges run; " + "; ".join(c["detail"][:120] for c in bad))
                failures = [{"id": c["id"], "source": "deterministic check", "detail": c["detail"], "fix": MECH_FIX.get(c["id"], "Fix this check.")} for c in bad]
                raw = llm.call(run, policy, purpose=f"fix_checks_{mech_used}", system=prompts.DRAFT_SYSTEM,
                               prompt=prompts.revise_prompt(ctx, srcs, brief, failures, counts, mechanical=True), model=cfg["models"]["drafter"])
                brief, used = assemble(raw, srcs)
                version += 1
                run.write(f"drafts/v{version}.md", brief)
                route.append(f"fix checks v{version}")
                checks, counts = run_checks(brief, srcs, policy)
            verdicts, checks, fails, counts = audit.audit(run, policy, cfg, ctx, srcs, brief, round_no, history)
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
            history += [{"round": round_no, "id": f["id"], "fix": str(f.get("required_fix", ""))} for f in fails]
            raw = llm.call(run, policy, purpose=f"revise_{round_no}", system=prompts.DRAFT_SYSTEM,
                           prompt=prompts.revise_prompt(ctx, srcs, brief, failures, counts), model=cfg["models"]["drafter"])
            brief, used = assemble(raw, srcs)
            version += 1
            run.write(f"drafts/v{version}.md", brief)
            route.append(f"revise v{version}")
        run.write("brief_final.md", brief)
        notes = [{"criterion": c, "judge": v["judge"], "note": str(v.get("notes")).strip()} for c, v in sorted(verdicts.items())
                 if str(v.get("notes") or "").strip() and str(v.get("notes")).strip().lower() not in ("none", "n/a", "-")]
        run.save(audit_verdict="PASS 11/11", sources_cited=used, judge_notes=notes,
                 checks_performed=checks_done + ["workflow-built Sources table and count", "deterministic brief checks DC01–DC09",
                                                 f"{mech_used} mechanical fix(es) before judging", "3-judge audit R01–R11"],
                 decision_notes=f"{mech_used} mechanical fix(es) and {round_no - 1} targeted revision(s); final text = drafts/v{version}.md",
                 remaining_caveats=_caveats(brief))

        # ---- approval gate: pause --------------------------------------------------------
        route.append("approval gate (paused)")
        run.save(route=" → ".join(route))
        gate.request_approval(run, policy, cfg, srcs, verdicts, checks, "brief_final.md")
        release_lock(run)
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
    acquire_lock(run)
    try:
        rel, commit = publish.publish(run, policy, cfg)
        run.save(route=run.state.get("route", "") + f" → decision YES → published {rel} ({commit[:10]})")
        _finish(run, policy, "COMPLETED")
    except Exception as e:
        if not isinstance(e, PolicyStop):
            run.write("error.txt", traceback.format_exc())
            _finish(run, policy, "ESCALATED", "INTERNAL_ERROR", f"unexpected error during publish: {e!r}"[:400], "owner")
            return run
        if e.status == "AWAITING_APPROVAL":
            # silence is not approval: refuse, stay paused, record the attempt
            run.log("publish", "refused", code=e.code, msg=e.message)
            run.save(errors=(run.state.get("errors") or []) + [f"{e.code}: {e.message}"])
            release_lock(run)
            write_run_log_row(run)
            monitor.build()
        else:
            _finish(run, policy, e.status, e.code, e.message, e.route)
    return run
