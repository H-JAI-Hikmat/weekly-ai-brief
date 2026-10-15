# Weekly AI Governance Brief — a governed, bounded agentic workflow

End-of-course project, *Agentic AI in Practice* (Hikmat El Jabi). It automates the mid-course manual workflow: every week the workflow turns a captured source pack into a one-page, source-grounded AI-governance brief for an IT leadership team, audits it, **pauses for an explicit human YES**, and only then publishes it to this repository.

- **Policy (enforced at runtime):** [`policy/agent_policy.yaml`](policy/agent_policy.yaml) — goal, permitted tools and data, approval, escalation, retry, budgets, stop rules
- **Published briefs:** [`published/`](published/) — written only by the publish step after a valid approval
- **Run evidence:** [`runs/`](runs/) — one folder per run (events log, inputs, drafts, audit verdicts, approval request and decision, escalation) and [`runs/run_log.csv`](runs/run_log.csv)
- **Monitoring:** [`monitoring/status.md`](monitoring/status.md) and [`monitoring/escalations.md`](monitoring/escalations.md)
- **Earlier stages (unchanged):** [`lineage/2026-W40/`](lineage/2026-W40/) — mid-course instruction, sources, frozen baseline and final brief

## How it works (one run)

```
trigger ─► preflight ─► collect ─► screen ─► grade ─► draft ─► audit ─┬─► PASS ─► APPROVAL GATE (pause) ─► YES ─► publish ─► stop
 (Mon 07:00   (kill switch,  (captures;   (PII redact,  (registry  (Claude,  (9 checks +   │                 │ NO / silence ─► stop, nothing published
  or manual)   one per week)  bounded      injection     rules)     no tools) 3 AI judges)  └─► FAIL ─► targeted revision (max 2) ─► still FAIL / ESCALATE ─► escalate, stop
                              fetch, no    quarantine)
                              substitutes) ── required source missing ─► escalate, stop before drafting
```

Every loop has a counter (fetch 3 attempts, model call 3 attempts, revisions 2, push 3 attempts, 14 model calls and 60 minutes per run). Every run ends in a named terminal state with a stop confirmation in its log.

## Setup (operator machine)

Requirements: Python 3.10+, `git`, and [Claude Code](https://docs.claude.com) signed in (the model provider). No API keys are stored in this repository.

```bash
git clone https://github.com/H-JAI-Hikmat/weekly-ai-brief && cd weekly-ai-brief
pip install pyyaml requests
python -m unittest -v tests.test_controls        # offline tests of the gates — no model calls, no pushes
```

The model is called as `claude -p --tools "" --strict-mcp-config --system-prompt … --model <sonnet|opus> --no-session-persistence`, from an empty folder, so the model has **no tools at all**: text in a source cannot make it act. A self-hosted OpenAI-compatible endpoint (e.g. vLLM) can replace it by changing `wab/llm.py`; the gates do not depend on the provider.

## Operating it

```bash
python -m wab run --manifest inbox/2026-W41/manifest.yaml --trigger schedule   # Monday 07:00 Asia/Dubai via cron
python -m wab status                                                          # where every run stands
# read runs/<RUN_ID>/approval_request.md, then the approver records an explicit decision in their own words:
python -m wab approve <RUN_ID> --decision YES --approver "Hikmat El Jabi" --channel "…" --statement "…"
python -m wab resume <RUN_ID>          # publishes only if a valid YES is on record for the exact text (SHA-256)
python -m wab monitor                  # rebuilds monitoring/status.md, prints alerts
python -m wab stop --reason "…"        # kill switch: creates STOP; delete the file to re-enable
```

Cron example: `0 7 * * 1 cd /path/to/weekly-ai-brief && TZ=Asia/Dubai python -m wab run --manifest inbox/$(date +%G-W%V)/manifest.yaml --trigger schedule`

## Inputs

`inbox/<week>/manifest.yaml` lists each source (ID, URL, publisher, date, required flag) and its capture file with a SHA-256. Captures are made by the capture step (Claude web search and page capture in the proof environment). If a capture is missing, the workflow tries a GET-only fetch from an allowlisted domain ([`config/source_registry.yaml`](config/source_registry.yaml)). It never fills a gap with other content.

## Secrets and personal data

No secrets are stored here. Commits use a GitHub no-reply address. The organisation profile in [`policy/context_card.md`](policy/context_card.md) is fictional. The red-team fixture [`tests/fixtures/W99_redteam.md`](tests/fixtures/W99_redteam.md) is synthetic test data; its contact details are fake and are redacted by the screen.
