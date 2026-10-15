"""Command line: python -m wab <command>

  run      --manifest inbox/<week>/manifest.yaml [--trigger schedule|manual] [--operator NAME]
  approve  RUN_ID --decision YES|NO --approver NAME --channel TEXT --statement "approver's own words"
  resume   RUN_ID                     (publishes only after a valid recorded YES)
  status   [RUN_ID]
  monitor                             (rebuilds monitoring/status.md and prints alerts)
  stop     --reason TEXT              (creates the STOP kill-switch file; delete the file to re-enable)
"""
import argparse
import json
import sys

from . import engine, monitor
from .core import ROOT, Run, iso, load_policy


def main(argv=None):
    ap = argparse.ArgumentParser(prog="wab", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run"); r.add_argument("--manifest", required=True); r.add_argument("--trigger", default="manual", choices=["manual", "schedule"]); r.add_argument("--operator")
    a = sub.add_parser("approve"); a.add_argument("run_id"); a.add_argument("--decision", required=True); a.add_argument("--approver", required=True)
    a.add_argument("--channel", required=True); a.add_argument("--statement", required=True)
    s = sub.add_parser("resume"); s.add_argument("run_id")
    st = sub.add_parser("status"); st.add_argument("run_id", nargs="?")
    sub.add_parser("monitor")
    k = sub.add_parser("stop"); k.add_argument("--reason", required=True)
    args = ap.parse_args(argv)

    if args.cmd == "run":
        run = engine.start(args.manifest, args.trigger, args.operator)
        print(json.dumps({k: run.state.get(k) for k in ("run_id", "status", "audit_verdict", "escalation_code", "approval_request")}, indent=2))
    elif args.cmd == "approve":
        run = engine.approve(args.run_id, args.decision, args.approver, args.channel, args.statement)
        print(json.dumps({k: run.state.get(k) for k in ("run_id", "status", "approval_decision", "approver", "approval_at")}, indent=2))
    elif args.cmd == "resume":
        run = engine.resume(args.run_id)
        print(json.dumps({k: run.state.get(k) for k in ("run_id", "status", "output_location", "published_commit", "stop_confirmation")}, indent=2))
    elif args.cmd == "status":
        ids = [args.run_id] if args.run_id else sorted(p.name for p in (ROOT / "runs").glob("RUN-*"))
        for i in ids:
            s = Run(i).state
            print(f"{i}: {s.get('final_status') or s.get('status')} · {s.get('route', '')}")
    elif args.cmd == "monitor":
        alerts = monitor.build()
        print("\n".join(alerts) or "No alerts.")
    elif args.cmd == "stop":
        pol = load_policy()
        (ROOT / pol["stop_rules"]["kill_switch_file"]).write_text(f"Stopped at {iso()}: {args.reason}\n")
        print(f"Kill switch set: {pol['stop_rules']['kill_switch_file']} created. No run will start or resume until it is deleted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
