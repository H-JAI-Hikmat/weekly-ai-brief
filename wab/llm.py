"""Model provider. Every call is text-only: Claude Code headless with ALL tools disabled, no MCP
servers, no session persistence, run inside an empty sandbox folder. Calls are counted against the
run budget and retried a bounded number of times (policy.retry.llm)."""
import datetime as dt
import json
import shutil
import subprocess
import time

from .core import PolicyStop, now, sha256_text


def call(run, policy, *, purpose, system, prompt, model):
    budget = policy["budgets"]
    if run.state.get("llm_calls", 0) >= budget["max_llm_calls_per_run"]:
        raise PolicyStop("ESCALATED", "BUDGET_EXCEEDED", f"model-call budget of {budget['max_llm_calls_per_run']} reached", "owner")
    elapsed = (now() - dt.datetime.fromisoformat(run.state["started_at"])).total_seconds() / 60
    if elapsed > budget["max_wall_minutes"]:
        raise PolicyStop("ESCALATED", "BUDGET_EXCEEDED", f"wall-time budget of {budget['max_wall_minutes']} min exceeded ({elapsed:.0f} min)", "owner")
    rp = policy["retry"]["llm"]
    sandbox = run.dir / "llm_sandbox"
    sandbox.mkdir(exist_ok=True)
    if shutil.which("claude") is None:
        raise PolicyStop("ESCALATED", "LLM_UNAVAILABLE", "claude CLI not found", "owner")
    cmd = ["claude", "-p", "--tools", "", "--strict-mcp-config", "--system-prompt", system,
           "--model", model, "--output-format", "json", "--no-session-persistence"]
    n = run.state.get("llm_calls", 0) + 1
    tag = f"llm/{n:02d}_{purpose}"
    run.write(f"{tag}_prompt.md", f"<!-- model={model} purpose={purpose} -->\n# SYSTEM\n{system}\n\n# PROMPT\n{prompt}")
    last_err = None
    for attempt in range(1, rp["max_attempts"] + 1):
        t0 = time.time()
        try:
            p = subprocess.run(cmd, input=prompt, capture_output=True, text=True, cwd=sandbox, timeout=rp["timeout_seconds"])
            data = json.loads(p.stdout) if p.stdout.strip().startswith("{") else {}
            result = (data.get("result") or "").strip()
            if p.returncode != 0 or data.get("is_error") or not result:
                raise RuntimeError(f"exit={p.returncode} is_error={data.get('is_error')} stderr={p.stderr[-300:]!r}")
            cost = float(data.get("total_cost_usd") or 0)
            run.save(llm_calls=n, llm_cost_usd=round(run.state.get("llm_cost_usd", 0) + cost, 4))
            run.write(f"{tag}_response.md", result)
            run.log("llm", "call_ok", purpose=purpose, model=model, attempt=attempt, seconds=round(time.time() - t0, 1),
                    cost_usd=round(cost, 4), prompt_sha256=sha256_text(prompt), response_file=run.rel(f"{tag}_response.md"))
            return result
        except Exception as e:  # bounded retry
            last_err = str(e)[:400]
            run.save(retry_count=run.state.get("retry_count", 0) + (1 if attempt < rp["max_attempts"] else 0))
            run.log("llm", "call_failed", purpose=purpose, attempt=attempt, msg=last_err)
            if attempt < rp["max_attempts"]:
                time.sleep(rp["backoff_seconds"][min(attempt - 1, len(rp["backoff_seconds"]) - 1)])
    run.save(llm_calls=n)
    raise PolicyStop("ESCALATED", "LLM_UNAVAILABLE", f"{purpose}: model call failed after {rp['max_attempts']} attempts ({last_err})", "owner")


def extract_json_array(text):
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError("no JSON array found")
    return json.loads(text[start:end + 1])
