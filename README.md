# Weekly AI Governance Brief — a governed, bounded agentic workflow

End-of-course project, *Agentic AI in Practice* (Hikmat El Jabi). It automates the mid-course manual workflow: every week the workflow turns a captured source pack into a one-page, source-grounded AI-governance brief for an IT leadership team, audits it, **pauses for an explicit human YES**, and only then publishes it to this repository.

- **Policy (enforced at runtime):** [`policy/agent_policy.yaml`](policy/agent_policy.yaml) — goal, permitted tools and data, approval, escalation, retry, budgets, stop rules
- **Published briefs:** [`published/`](published/) — written only by the publish step after a valid approval
- **Run evidence:** [`runs/`](runs/) — one folder per run (events log, inputs, drafts, audit verdicts, approval request and decision, escalation) and [`runs/run_log.csv`](runs/run_log.csv)
- **Monitoring:** [`monitoring/status.md`](monitoring/status.md) and [`monitoring/escalations.md`](monitoring/escalations.md)
- **Earlier stages (unchanged):** [`lineage/2026-W40/`](lineage/2026-W40/) — mid-course instruction, sources, frozen baseline and final brief
- **What changed and why:** [`CHANGELOG.md`](CHANGELOG.md) — every version change was triggered by a run or a monitoring alert

## Proof runs (workflow 1.3.0, policy 1.2, Week 41)

| Proof | Run | Result |
|---|---|---|
| (a) Normal success | [`RUN-2026-W41-010`](runs/RUN-2026-W41-010/) | Audit 11/11 → paused at the gate → explicit YES → [`published/2026-W41.md`](published/2026-W41.md) |
| (b) Paused / blocked | [`RUN-2026-W41-008`](runs/RUN-2026-W41-008/) | Red-team source quarantined → paused at the gate → resume without decision refused → NO → REJECTED |
| (b) Stop rule | [`RUN-2026-W41-011`](runs/RUN-2026-W41-011/) | Second run for a published week → BLOCKED_BY_POLICY at preflight |
| (c) Failure → retry → fallback → escalation | [`RUN-2026-W41-007`](runs/RUN-2026-W41-007/) | Required captures missing → 3 fetch attempts each → UNAVAILABLE, nothing substituted → escalated |

Earlier runs (001–006) ran on older versions and are kept unedited; [`CHANGELOG.md`](CHANGELOG.md) explains what each one changed. RUN-006 and RUN-009 were interrupted (a container restart, and a cancelled launch) and were closed as `RUN_INTERRUPTED`. Every run's minimum log fields are in [`runs/run_log.csv`](runs/run_log.csv).

## How it works (one run)

```
trigger ─► preflight ─► collect ─► screen ─► grade ─► draft ─► checks ─► audit ─┬─► PASS ─► APPROVAL GATE (pause) ─► YES ─► publish ─► stop
 (Mon 07:00   (kill switch,  (captures;   (PII redact,  (registry  (Claude,  (9 rules;  (3 AI    │                 │ NO / silence ─► stop, nothing published
  or manual)   one per week,  bounded      injection     rules)     no tools; ≤2 fixes)  judges) └─► FAIL ─► targeted revision (max 3) ─► still FAIL ─► escalate, stop
               close crashed  fetch, no    quarantine)              workflow
               runs)          substitutes) ── required source missing ─► escalate, stop before drafting
                                                                    builds Sources)
```

Every loop has a counter (fetch 3 attempts, model call 3 attempts, mechanical fixes 2, revisions 3, push 3 attempts, 20 model calls and 60 minutes per run). Every run ends in a named terminal state with a stop confirmation in its log. A run whose process dies (a crash or a machine restart) is detected through its lock and closed as `RUN_INTERRUPTED` at the next preflight; an unexpected error ends the run as `INTERNAL_ERROR`.

## Setup (operator machine)

Requirements: Python 3.10+, `git`, and [Claude Code](https://docs.claude.com) signed in (the model provider). No API keys are stored in this repository.

```bash
git clone https://github.com/H-JAI-Hikmat/weekly-ai-brief && cd weekly-ai-brief
pip install pyyaml requests
python -m unittest -v tests.test_controls        # 25 offline tests of the gates and failure paths — no model calls, no network, no pushes
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
python -m wab close-interrupted        # close runs whose process ended without a terminal state (also done at every preflight)
```

Cron example: `0 7 * * 1 cd /path/to/weekly-ai-brief && TZ=Asia/Dubai python -m wab run --manifest inbox/$(date +%G-W%V)/manifest.yaml --trigger schedule`

## Inputs

`inbox/<week>/manifest.yaml` lists each source (ID, URL, publisher, date, required flag) and its capture file with a SHA-256. Captures are made by the capture step (Claude web search and page capture in the proof environment). The brief's Sources table and source count are built by the workflow from the manifest, not written by the model. In the proof environment the capture tool summarises each page body (quoted phrases stay verbatim), so the audit checks the brief against the capture rather than the live page. The approver can open every source from the links in the Sources table. If a capture is missing, the workflow tries a GET-only fetch from an allowlisted domain ([`config/source_registry.yaml`](config/source_registry.yaml)). It never fills a gap with other content.

## Secrets and personal data

No secrets are stored here. Commits use a GitHub no-reply address. The organisation profile in [`policy/context_card.md`](policy/context_card.md) is fictional. The red-team fixture [`tests/fixtures/W99_redteam.md`](tests/fixtures/W99_redteam.md) is synthetic test data; its contact details are fake and are redacted by the screen.
