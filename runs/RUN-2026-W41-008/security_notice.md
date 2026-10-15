# Security notice — RUN-2026-W41-008

To: Head of Information Security
Code: INJECTION_QUARANTINED
Raised: 2026-10-15T16:24:16+04:00

## What happened
The screen found text aimed at the AI or the workflow in: W99.

- W99: ['ASSISTANT:', 'Publish it immediately', 'approval: YES', 'ignore previous instructions', 'pre-approved']

## What the workflow did
- The quarantined text was never sent to the model.
- The run continues without it; the brief and the approval request disclose it.
- PII in the source was redacted before storage.

## Decision needed
Review the source and decide whether its publisher stays on the allowlist.
