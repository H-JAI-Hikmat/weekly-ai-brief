"""Audit gate: deterministic checks + three independent AI judges (rubric from config, 11 criteria)."""
import json

from . import llm, prompts
from .checks import run_checks

CRITERIA = [f"R{i:02d}" for i in range(1, 12)]


def audit(run, policy, cfg, ctx, sources, brief, round_no, history=None):
    checks, counts = run_checks(brief, sources, policy)
    checks_text = "\n".join(f"{c['id']} [{c['criterion']}] {c['result']}: {c['detail']}" for c in checks)
    run.write(f"audit/round{round_no}_deterministic.json", json.dumps({"checks": checks, "counts": counts}, indent=2))
    run.log("audit", "deterministic_checks", round=round_no,
            msg=f"{sum(c['result'] == 'PASS' for c in checks)}/{len(checks)} PASS; BODY {counts['body_words']}, WHOLE {counts['whole_words']}, items {counts['items']}")

    verdicts = {}
    for jid, (name, crits, _) in prompts.JUDGES.items():
        prompt = prompts.judge_prompt(jid, ctx, sources, brief, checks_text, history)
        parsed = None
        for attempt in (1, 2):  # one repair attempt for malformed JSON, then the judge counts as failed
            text = llm.call(run, policy, purpose=f"audit_r{round_no}_{jid}", system=prompts.judge_system(name),
                            prompt=prompt if attempt == 1 else prompt + "\n\nYour previous reply was not a valid JSON array. Reply with the JSON array only.",
                            model=cfg["models"]["judges"])
            try:
                arr = llm.extract_json_array(text)
                got = {o["id"]: o for o in arr if o.get("id") in crits and o.get("verdict") in ("PASS", "FAIL")}
                if set(got) == set(crits):
                    parsed = got
                    break
                raise ValueError(f"criteria returned {sorted(got)} != {crits}")
            except Exception as e:
                run.log("audit", "judge_output_invalid", judge=jid, attempt=attempt, msg=str(e)[:200])
        if parsed is None:
            for c in crits:
                verdicts[c] = {"id": c, "verdict": "FAIL", "judge": jid, "evidence": "judge output invalid twice",
                               "why_it_matters": "criterion could not be verified", "required_fix": "ESCALATE: judge failed to return a valid verdict"}
        else:
            for c, o in parsed.items():
                verdicts[c] = dict(o, judge=jid)

    # deterministic FAIL overrides a judge PASS on the mapped criterion
    for c in checks:
        if c["result"] == "FAIL":
            v = verdicts[c["criterion"]]
            if v["verdict"] == "PASS":
                v.update(verdict="FAIL", evidence=f"Deterministic check {c['id']} failed: {c['detail']}",
                         required_fix=f"Fix deterministic check {c['id']}: {c['detail']}")
            else:
                v["evidence"] = f"{v.get('evidence', '')} | Deterministic {c['id']}: {c['detail']}"
            v["deterministic_fail"] = c["id"]

    run.write(f"audit/round{round_no}_verdicts.json", json.dumps([verdicts[c] for c in CRITERIA], indent=2, ensure_ascii=False))
    fails = [verdicts[c] for c in CRITERIA if verdicts[c]["verdict"] == "FAIL"]
    run.log("audit", "verdict", round=round_no, msg=f"{11 - len(fails)}/11 PASS" + (f"; FAIL: {[f['id'] for f in fails]}" if fails else ""))
    return verdicts, checks, fails, counts
