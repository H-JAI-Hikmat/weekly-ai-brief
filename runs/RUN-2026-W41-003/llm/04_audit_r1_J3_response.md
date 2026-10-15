```json
[
  {
    "id": "R07",
    "verdict": "FAIL",
    "evidence": "Two analytical sentences are written as fact with no (Inference) label. (1) Item 1 Why: \"It would reach us directly only if we place AI on the EU market (Assumption P4).\" This is a legal-scope conclusion, not a premise from the context card. Only the P4 premise is labelled, and P4's meaning is used correctly. (2) Item 4 Why: \"It signals local security expectations for agentic AI.\" This has no label and no citation. W08.3 reports a CEO's view, not a set of expectations. The other labels match the card: P2 in the Bottom line and Item 1 is used with its card meaning (US-provider APIs), and the Assumptions table row for P4 matches the card.",
    "why_it_matters": "Leaders could read 'only if we place AI on the EU market' as a settled conclusion and close the EU exposure question before the P4 check with Legal is done.",
    "required_fix": "Add (Inference) to both sentences. Rewrite Item 1's second sentence as a hedged view, e.g. 'Direct application to us may depend on our EU market role (Inference) (Assumption P4); check with Legal.'"
  },
  {
    "id": "R10",
    "verdict": "FAIL",
    "evidence": "(1) Item 1 Why: \"It would reach us directly only if we place AI on the EU market.\" This states the scope of EU law as settled. No pack extract supports it (W01, W02 do not address scope), and the brief does not say 'check with Legal' at that point. (2) Excluded table, W09 reason: \"repeats W08's origin, so not independent.\" W09 cites Dubai Future Foundation as its origin, but W08 states no origin, so this link is a gloss not found in the pack. Passing points: W99 is disclosed with the workflow's quarantine reason (DC05). No personal or confidential data appears (DC06). The officials named are as reported in W01, W02 and W08. No outcome predictions were found.",
    "why_it_matters": "A legal-scope conclusion the pack does not support could lead IT leadership to treat EU duties as out of reach without legal review.",
    "required_fix": "Replace the Item 1 sentence with a hedged inference ending 'check with Legal'. Change the W09 reason to a sourced one, e.g. 'Low grade; repeats facts in W08, not relied on'."
  },
  {
    "id": "R11",
    "verdict": "FAIL",
    "evidence": "Item 1 What happened: \"Henna Virkkunen said Europe is 'well equipped' to deal with rogue AI agents [W02].\" The official is named without her role. W01.1 gives her role as Executive Vice-President for Tech Sovereignty, Security and Democracy, and W02.1 calls her 'the EU's tech chief'. Elsewhere the tone is neutral and the wording is factual. 'Rogue AI agents' is quoted and attributed to her. The Dubai Electronic Security Centre CEO, Yousuf Hamad Al Shaibani, is described by role, and his framework view is attributed to him (W08.3). DC07 found no banned terms.",
    "why_it_matters": "Without her role, readers cannot weigh whether the 'well equipped' remark is the Commission's official position or a personal view.",
    "required_fix": "Write 'Henna Virkkunen, the Commission's Executive Vice-President for Tech Sovereignty, Security and Democracy [W01], said Europe is \"well equipped\" to deal with rogue AI agents [W02].'"
  }
]
```