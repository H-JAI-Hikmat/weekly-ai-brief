# AUDIT RUBRIC v1.0 — Weekly AI Governance Brief

Verdict rule: each criterion is PASS or FAIL. A criterion FAILS if any single instance fails it.
Every verdict, PASS or FAIL, must cite evidence: quote the brief (short quote) and name the source extract ID(s) (e.g. S05.5) or the calculation used.
If a failure cannot be fixed from the source pack (the evidence does not exist, or the call needs human judgment), the required fix must begin "ESCALATE:" and say what a human must decide or obtain.

| ID | Criterion | PASS when | Why it matters | Instruction clause |
|---|---|---|---|---|
| R01 | Citation coverage | Every factual sentence (including in Bottom line, Confidence lines and tables) carries a Source ID that exists in the pack. Inference/Assumption-labelled sentences are exempt. | Untraceable claims were the main failure of earlier briefs. | C1, D1 |
| R02 | Citation accuracy | Each cited extract actually supports the sentence it is attached to — no overstatement, no merged claims the source does not make, no source cited for a fact it does not contain. | A citation that does not support the claim is worse than none: it creates false confidence. | C1, D1 |
| R03 | Source grading and exclusions | Grades follow the C2 definitions; no Low-grade source supports any claim on its own; every excluded source is listed with a reason that is true of that source. | Readers act on the brief; weak sources must not drive decisions. | C2, D2 |
| R04 | Conflict handling | Every disagreement between sources in the pack that bears on a statement in the brief is either resolved with a stated reason or escalated. | Silent conflict resolution hides risk from decision-makers. | C3, D3 |
| R05 | Precision | Dates, numbers, names and titles match the source exactly; dates use DD Mon YYYY. | Wrong dates drive wrong deadlines. | C8 |
| R06 | Scope and recency | Each lead item describes an event dated inside the reporting week (28 Sep – 04 Oct 2026). Older material appears only as labelled background or in Dates ahead. | The brief is a weekly change log, not a reference guide. | C5 |
| R07 | Labelling and assumption integrity | Analysis is labelled (Inference); premises about the organisation are labelled (Assumption Pn) and match the meaning of Pn in the context card; no inference or assumption is phrased as fact. | Mislabelled assumptions turn guesses into apparent facts. | C4 |
| R08 | Relevance and actionability | Each item has a "Why it matters to us" that follows from the profile, and an Action with owner role, action and DD Mon YYYY date (or "No action — monitor"). The Bottom line is consistent with the items. No in-week development in the pack that plainly affects the profile (P1–P6) is omitted without a reason. | Leaders need to know what to do, not just what happened. | D4 |
| R09 | Format and length | Sections appear in the required order with the required fields; BODY ≤ 450 words and WHOLE ≤ 750 words as measured by count_words.py; ≤ 5 items; headlines ≤ 12 words. | The brief must be readable on a phone in under five minutes. | C9, D5 |
| R10 | Safety: legal advice, privacy, closed book | No legal advice or outcome predictions ("check with Legal" used where needed); no confidential or personal data beyond public figures as reported; nothing added from outside the pack. | Protects the organisation and keeps the brief auditable. | C6, C7, D6 |
