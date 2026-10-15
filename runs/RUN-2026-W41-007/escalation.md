# Escalation — RUN-2026-W41-007

To: Hikmat El Jabi — Workflow Owner
Code: SOURCE_UNAVAILABLE_REQUIRED
Raised: 2026-10-15T16:24:12+04:00
Run status: ESCALATED

## What happened
required source(s) W01, W06 unavailable after the retry limit; no brief is drafted from a partial pack

## What the workflow did
- Retries performed this run: 4 (bounded by policy.retry)
- Fallback: missing sources marked UNAVAILABLE and disclosed; no substitute content; run stopped before drafting
- Nothing was published by this run; no data was invented or substituted.

## Decision needed
Review runs/RUN-2026-W41-007/events.jsonl, resolve the cause, then start a new run (the workflow does not retry on its own).
