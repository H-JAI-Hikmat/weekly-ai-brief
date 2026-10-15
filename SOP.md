# SOP — Weekly AI Governance Brief workflow

Policy WAB-POLICY v1.2 · Workflow v1.3.0 · Owner and sole approver: Hikmat El Jabi · Repo: github.com/H-JAI-Hikmat/weekly-ai-brief

**Goal.** Every Monday, turn last week's captured public sources into a one-page, source-grounded AI-governance brief for the IT Leadership Team. Publish it only after the owner explicitly approves the exact text.

**Access (least privilege).**
- The model drafts and audits as text only (`claude -p`, all tools disabled, no MCP servers).
- It may read only the week's captures, and may fetch only from allowlisted domains.
- The only external action is one commit to `published/<week>.md` in this repo.
- Inputs must be public. The organisation profile is fictional.

**Run.**
1. Check that the capture step has filled `inbox/<week>/` (a manifest plus captures).
2. Run: `python -m wab run --manifest inbox/<week>/manifest.yaml --trigger schedule|manual`.
3. The run either pauses at the approval gate (`AWAITING_APPROVAL`) or ends in a named terminal state.
4. Check where it stands with `python -m wab status`.

**Supervise.**
- Read `runs/<id>/approval_request.md` in full. It contains the brief exactly as it would be published, the audit verdict for all 11 criteria, source status (used, excluded, quarantined, unavailable), security and PII flags, any non-blocking reviewer notes from the judges, the brief's SHA-256, and the exact action a YES triggers.
- Open any cited source you doubt; the URLs are in the Sources table.

**Approve.**
- Only the owner records a decision: `python -m wab approve <id> --decision YES|NO --approver "Hikmat El Jabi" --channel <how> --statement "<own words>"`.
- Then run `python -m wab resume <id>`.
- A YES covers only the text whose hash was shown. Any edit voids it.
- Silence is never approval: the request expires after 72 h, the run ends `EXPIRED`, and nothing is published.
- Running `resume` without a recorded YES is refused and logged.

**Escalation.** The workflow writes `runs/<id>/escalation.md` and adds a line to `monitoring/escalations.md`.

| Code | Goes to | What the workflow does |
|---|---|---|
| `SOURCE_UNAVAILABLE_REQUIRED`, `TOO_MANY_UNAVAILABLE` | Owner | Stops before drafting |
| `AUDIT_FAIL_AFTER_MAX_REVISIONS`, `AUDIT_ESCALATE` | Owner | Stops before approval |
| `LLM_UNAVAILABLE`, `BUDGET_EXCEEDED` | Owner | Stops |
| `PUBLISH_FAILED` | Owner | Keeps the approved text |
| `RUN_INTERRUPTED`, `INTERNAL_ERROR` | Owner | Closes the run; nothing is published |
| `INJECTION_QUARANTINED` | Head of Information Security | Continues without the quarantined source and discloses it |

**Retry and fallback.** Every retry has a fixed limit:

| Step | Limit |
|---|---|
| Source fetch | 3 attempts (2 s, then 4 s backoff; 10 s timeout) |
| Model call | 3 attempts (10 s, then 30 s backoff) |
| Mechanical fixes (deterministic-check failures, before the judges) | 2 per run |
| Targeted revisions | 3, each followed by a full re-audit |
| Push | 3 attempts |
| Per run | 20 model calls and 60 minutes |

A missing source is marked `UNAVAILABLE` and disclosed, never substituted or reconstructed. A failed model call is not silently replaced by another model.

**Monitor.**
- After every run, and weekly, run `python -m wab monitor` and read `monitoring/status.md`.
- Alerts fire on:
  - 2 or more failed or blocked runs in the last 4
  - the same failure code twice in the last 8 runs
  - 3 or more failed fetches for one domain in 7 days
  - an approval waiting more than 48 h
  - a run interrupted without a terminal state
- Each run's own record is `runs/run_log.csv` plus `runs/<id>/events.jsonl`.

**Recover.**
- Unavailable source: re-capture it, then start a new run. A new run has a new ID; old runs are never edited.
- Audit failure or escalation: fix the input or the policy, raise the version if you change the policy, then re-run.
- Push failure: check repo access, then run `resume` again. The approval stays valid until it expires.
- Expired or rejected run: start a new run.
- Interrupted run (crash or restart): the next run's preflight closes it as `RUN_INTERRUPTED`, or run `python -m wab close-interrupted`. Then start a new run.

**Stop.**
- Anyone on the IT Leadership Team may ask the operator to stop the workflow.
- Stop: `python -m wab stop --reason "…"` creates `STOP`, and no run starts or resumes until the owner deletes it.
- Alternatively set `enabled: false` in the policy.
- Built-in stops: one publication per week, at most 6 runs per week under one policy version, and every run ends in a terminal state with a logged stop confirmation.
