"""Shared foundations: paths, policy loading, hashing, time, run log and state."""
import csv
import datetime as dt
import hashlib
import json
import os
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DUBAI = dt.timezone(dt.timedelta(hours=4))


class PolicyStop(Exception):
    """Raised when a policy rule ends the run (the engine records the reason and stops)."""

    def __init__(self, status, code, message, route=None):
        super().__init__(message)
        self.status, self.code, self.message, self.route = status, code, message, route


def now():
    return dt.datetime.now(DUBAI)


def iso(t=None):
    return (t or now()).isoformat(timespec="seconds")


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_yaml(rel):
    return yaml.safe_load((ROOT / rel).read_text(encoding="utf-8"))


def load_policy():
    pol = load_yaml("policy/agent_policy.yaml")
    pol["_sha256"] = sha256_file(ROOT / "policy/agent_policy.yaml")
    return pol


def load_config():
    return load_yaml("config/workflow.yaml")


def kill_switch_active(policy):
    if not policy.get("enabled", False):
        return "policy.enabled is false"
    if (ROOT / policy["stop_rules"]["kill_switch_file"]).exists():
        return f"kill-switch file '{policy['stop_rules']['kill_switch_file']}' present at repo root"
    return None


class Run:
    """One run's folder, event log (JSONL) and state (JSON)."""

    def __init__(self, run_id):
        self.id = run_id
        self.dir = ROOT / "runs" / run_id
        self.dir.mkdir(parents=True, exist_ok=True)
        self.events = self.dir / "events.jsonl"
        self.state_path = self.dir / "state.json"
        self.state = json.loads(self.state_path.read_text()) if self.state_path.exists() else {}

    # --- logging -------------------------------------------------------------------------
    def log(self, stage, event, **detail):
        rec = {"ts": iso(), "run_id": self.id, "stage": stage, "event": event, **detail}
        with self.events.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"[{rec['ts']}] {stage:<9} {event}" + (f" — {detail.get('msg')}" if detail.get("msg") else ""))
        return rec

    def save(self, **updates):
        self.state.update(updates)
        self.state_path.write_text(json.dumps(self.state, indent=2, ensure_ascii=False))

    def write(self, name, text):
        p = self.dir / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def rel(self, name):
        return str((self.dir / name).relative_to(ROOT))


def next_run_id(week):
    runs = ROOT / "runs"
    runs.mkdir(exist_ok=True)
    existing = sorted(p.name for p in runs.iterdir() if p.is_dir() and p.name.startswith(f"RUN-{week}-"))
    return f"RUN-{week}-{len(existing) + 1:03d}"


RUN_LOG_FIELDS = [
    # Run identity
    "run_id", "started_at", "ended_at", "operator", "trigger", "workflow_version", "policy_version", "policy_sha256", "week", "manifest",
    # Inputs
    "input_source_ids", "test_fixtures", "redactions", "truncations",
    # Decisions
    "route", "checks_performed", "quarantined", "unavailable", "audit_rounds", "audit_verdict", "decision_notes",
    # Approval
    "approval_request", "approval_request_sha256", "approver", "approval_decision", "approval_statement", "approval_channel", "approval_at",
    # Failures
    "errors", "retry_count", "fallback", "escalation_code", "escalation_recipient",
    # Output
    "final_status", "output_location", "remaining_caveats", "stop_confirmation", "llm_calls", "llm_cost_usd",
]


def write_run_log_row(run):
    """Upsert this run's row in runs/run_log.csv (one row per run, minimum log fields)."""
    path = ROOT / "runs" / "run_log.csv"
    rows = []
    if path.exists():
        with path.open(newline="", encoding="utf-8") as f:
            rows = [r for r in csv.DictReader(f) if r.get("run_id") != run.id]
    s = run.state
    row = {k: s.get(k, "") for k in RUN_LOG_FIELDS}
    for k, v in row.items():
        if isinstance(v, (list, dict)):
            row[k] = json.dumps(v, ensure_ascii=False)
    rows.append(row)
    rows.sort(key=lambda r: r["run_id"])
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=RUN_LOG_FIELDS)
        w.writeheader()
        w.writerows(rows)
