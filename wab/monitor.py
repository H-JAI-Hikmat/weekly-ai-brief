"""Monitoring: reads every run's state and events and writes monitoring/status.md with alerts."""
import collections
import datetime as dt
import json

from .core import ROOT, iso, now, load_policy


def build():
    pol = load_policy()
    mon = pol["monitoring"]
    runs = []
    for d in sorted((ROOT / "runs").glob("RUN-*")):
        sp = d / "state.json"
        if sp.exists():
            s = json.loads(sp.read_text())
            s["_events"] = [json.loads(l) for l in (d / "events.jsonl").read_text().splitlines() if l.strip()] if (d / "events.jsonl").exists() else []
            runs.append(s)
    alerts = []
    last = runs[-mon["alert_if_nonsuccess_in_last_n"]["n"]:]
    nonsucc = [r for r in last if r.get("final_status") not in ("COMPLETED", "REJECTED") and r.get("status") != "AWAITING_APPROVAL"]
    if len(nonsucc) >= mon["alert_if_nonsuccess_in_last_n"]["threshold"]:
        alerts.append(f"{len(nonsucc)} failed/blocked runs in the last {len(last)}: {[r['run_id'] for r in nonsucc]}")
    codes = collections.Counter(r.get("escalation_code") for r in runs[-mon["alert_if_same_failure_code_in_last_n"]["n"]:] if r.get("escalation_code"))
    for code, n in codes.items():
        if n >= mon["alert_if_same_failure_code_in_last_n"]["threshold"]:
            alerts.append(f"failure code {code} repeated {n} times in the last {mon['alert_if_same_failure_code_in_last_n']['n']} runs")
    week_ago = now() - dt.timedelta(days=7)
    per_domain = collections.Counter()
    for r in runs:
        for e in r["_events"]:
            if e["event"] == "fetch_failed" and dt.datetime.fromisoformat(e["ts"]) > week_ago:
                per_domain[e.get("domain")] += 1
    for dom, n in per_domain.items():
        if n >= mon["alert_if_fetch_failures_per_domain_7d"]:
            alerts.append(f"{n} failed fetch attempts for {dom} in the last 7 days — check the capture job and the network path")
    for r in runs:
        if r.get("status") == "AWAITING_APPROVAL":
            age_h = (now() - dt.datetime.fromisoformat(r["approval_requested_at"])).total_seconds() / 3600
            if age_h >= mon["alert_if_awaiting_approval_hours"]:
                alerts.append(f"{r['run_id']} has waited {age_h:.0f} h for approval")
    lines = [f"# Monitoring status — generated {iso()}", "", f"Policy {pol['policy_id']} v{pol['version']} · {len(runs)} run(s) on record", "",
             "## Alerts", *(f"- ⚠ {a}" for a in alerts), *(["- None"] if not alerts else []), "",
             "## Runs", "| Run | Week | Final status | Escalation | Retries | Model calls | Cost (USD) | Output |", "|---|---|---|---|---|---|---|---|"]
    for r in runs:
        lines.append(f"| {r['run_id']} | {r.get('week')} | {r.get('final_status') or r.get('status')} | {r.get('escalation_code', '')} | "
                     f"{r.get('retry_count', 0)} | {r.get('llm_calls', 0)} | {r.get('llm_cost_usd', 0)} | {r.get('output_location', '') or '—'} |")
    lines += ["", "## Failed fetch attempts by domain (last 7 days)", *(f"- {d}: {n}" for d, n in per_domain.items()), *(["- None"] if not per_domain else [])]
    (ROOT / "monitoring").mkdir(exist_ok=True)
    (ROOT / "monitoring/status.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return alerts
