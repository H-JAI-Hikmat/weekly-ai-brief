# Changelog

Every change below was made because a run or a monitoring alert showed a problem. Old runs are never rewritten; each run folder records the workflow and policy version it ran under. A run that was interrupted is only closed later, by appending a terminal state to it.

## After the proof runs — 15 Oct 2026 (tests and documents only; workflow code unchanged since 1.3.0)

- 8 offline tests added for failure paths the proof runs did not exercise: kill switch, non-public data, the weekly run cap, a model failure (3 attempts, no model swap), the model-call and wall-time budgets, too many unavailable sources, invalid judge output (one repair, then FAIL with ESCALATE), and a push failure (3 attempts, approved text kept). 25 tests in total.
- SOP corrected: after `PUBLISH_FAILED`, `resume` does not retry. The owner pushes the local publish commit by hand, or resets it and starts a new run.

### Known issues to fix in 1.3.1

- An `INJECTION_QUARANTINED` notice is written to `escalations.md` and to the run's events, but not to the run-log fields `escalation_code` and `escalation_recipient`, so the monitor's repeat-failure alert cannot count it.
- A refused decision (for example "No preference") raises an error at the command line but is not written to `events.jsonl`.
- After `PUBLISH_FAILED`, `resume` cannot retry; the owner must act by hand (see the SOP).
- The weekly run cap restarts with each policy version, and the owner, operator and approver are one person. 1.3.1 should add an absolute weekly ceiling, or a second sign-off for policy changes.
- The approver is identified by a name string, not authenticated. Production use needs an authenticated approval channel (for example SSO or a signed review).
- Log wording: a run closed as interrupted after the week was published says the brief "exists from an earlier run", even when a later run published it. The preflight message "no interrupted runs left open" counts only runs past the 60-minute limit.
- Field values truncated at 200 characters in `events.jsonl` can cut error messages mid-word.
- Captures are made by an operator-run capture step whose tool summarises each page body (quoted phrases stay verbatim). The SHA-256 proves that a capture was not changed, not that it is faithful to the page, and the judges check the brief against the capture. 1.3.1 should store verbatim page text where the network allows.

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
- Revision limit raised from 2 to 3; model-call budget from 14 to 20; weekly run cap from 5 to 6 (one shakedown run had used a slot).

## Workflow 1.0.0 · policy 1.0 — 15 Oct 2026

First release: engine, policy, offline tests, the Week 41 inbox and the Week 40 lineage from the mid-course project.
