# Changelog

Every change below was made because a run or a monitoring alert showed a problem. Old runs are never edited: each run folder records the workflow and policy version it ran under.

## Workflow 1.3.0 · policy 1.2 — 15 Oct 2026 (proof set)

Triggers: monitoring alert *AUDIT_FAIL_AFTER_MAX_REVISIONS repeated 2 times* (RUN-002, RUN-005), and RUN-006 left without a terminal state after the container restarted mid-run.

- **Interrupted runs are closed, not forgotten.** Each run holds a lock (process ID + machine boot ID). If its process has gone or the machine has restarted, or a run without a lock has been silent for longer than the 60-minute wall-time budget, the next preflight (or `wab close-interrupted`) closes it as `ESCALATED / RUN_INTERRUPTED` and reports it to the Owner.
- **Unexpected errors still end cleanly.** Any unexpected error ends the run as `ESCALATED / INTERNAL_ERROR`, with a stop confirmation and the traceback saved.
- **The workflow builds the Sources table and the "Sources used" count** from the manifest (`wab/assemble.py`), so titles, dates, grades and links are copied exactly. The model no longer writes them (instruction v1.3, rubric v1.3).
- **Cheap checks first.** The nine deterministic checks run before the AI judges. Failures go back to the drafter for at most 2 mechanical fixes per run, so judges are not spent on a draft that is simply too long.
- **Judges stay consistent.** From round 2, each judge sees the fixes required in earlier rounds and may not reverse them. A materiality rule means wording preferences on accurate text become non-blocking notes, which are shown to the approver.
- **Quarantine notices are written down.** `INJECTION_QUARANTINED` now writes `runs/<id>/security_notice.md` for the Head of Information Security and adds a line to `monitoring/escalations.md`.
- **Monitoring fix.** Runs still in progress are no longer counted as failures; interrupted runs raise an alert.
- **Weekly run cap counted per policy version.** Policy v1.1's six runs for Week 41 were used by two shakedown runs, three proof-set runs and one interrupted run. A policy change is itself an Owner decision recorded in the change log, so it starts a new, equally bounded allowance.
- Tests: 17 offline tests (7 new).

## Workflow 1.2.0 · policy 1.1 — 15 Oct 2026

Trigger: shakedown RUN-002 did not pass the audit within 3 revisions (length; wording of "For human decision").

- Instruction and rubric v1.2: whole-brief limit of 850 words; each "For human decision" entry is one question to a named role; the watchlist is not restated; "Sources used" is defined.
- The revision prompt carries deterministic word counts and a target, and asks for a full self-check.

## Workflow 1.1.0 · policy 1.1 — 15 Oct 2026

Trigger: shakedown RUN-001 stopped at the first audit round because a judge marked an item ESCALATE.

- A judge's ESCALATE item is handled by a targeted revision that removes the point or moves it to "For human decision", and is shown to the approver. The run stops only if the criterion still fails after the revision limit.
- Revision limit raised from 2 to 3; model-call budget from 14 to 20; runs per week from 5 to 6.

## Workflow 1.0.0 · policy 1.0 — 15 Oct 2026

First release: engine, policy, offline tests, the Week 41 inbox and the Week 40 lineage from the mid-course project.
