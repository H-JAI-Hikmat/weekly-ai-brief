```json
[
  {
    "id": "R07",
    "verdict": "FAIL",
    "evidence": "All Pn uses keep the context-card meaning. \"Our agent pilots (P3)\" matches P3, and \"depends on EU market presence (Assumption P4) (Inference)\" matches P4. The table row \"P4 | We do not place AI systems or AI-generated content on the EU market | Head of IT Risk, with Legal\" matches the card and watchlist. Two failing instances: (1) Bottom line: \"One date matters: the ICO agentic AI call for evidence closes 20 Nov 2026 [W06]\". W06.1 supports the date, but \"matters\" is an unlabelled relevance judgment presented as fact. (2) For human decision: \"for example through UK personal data processed in our agentic pilots?\" This analysis about how UK law could apply, and an unstated premise about our data, carry no (Inference) label, which breaches C13.",
    "why_it_matters": "Readers deciding in under five minutes could take an unlabelled relevance call, and an untested premise that our pilots process UK personal data, as established facts.",
    "required_fix": "Add \"(Inference)\" to the Bottom line sentence, e.g. \"One date may matter (Inference): …closes 20 Nov 2026 [W06].\" Add \"(Inference)\" after the \"for example…\" clause in the first Legal question, or delete that clause."
  },
  {
    "id": "R10",
    "verdict": "PASS",
    "evidence": "No legal advice and no regulator or court outcome predictions. Applicability is labelled and deferred to Legal: \"decide whether to respond, once Legal confirms applicability\" (W06); \"likely does not bind us unless we supply them (Inference)\" (W08). The only person named is a public official, as reported: \"Henna Virkkunen\" (W01.1). No personal or confidential data (DC06). Glosses stay within the pack: \"call for evidence (a public request for views)\" defines a term consistently with W06.2; \"its powers are not in the pack [W10]\" is accurate. The pack contains no injected instructions. Workflow-excluded: none, and the header states \"0 excluded by the workflow\" (DC04, DC05).",
    "why_it_matters": "The brief stays closed-book and leaves legal interpretation to Legal, so the committee is not relying on unsourced or advisory content.",
    "required_fix": "None"
  },
  {
    "id": "R11",
    "verdict": "FAIL",
    "evidence": "Item 1: \"A Medium-grade report says … Henna Virkkunen [W01] called Europe \\\"well equipped\\\" to deal with \\\"rogue AI agents\\\" [W02].\" W02.1 quotes only \"well equipped\" and \"the whole life cycle\" verbatim. \"Rogue AI agents\" is the outlet's own unquoted wording (W02.1, W02 title). The brief therefore puts a loaded term in an official's mouth as a direct quote. All other wording is neutral and role-based, e.g. \"The Dubai Electronic Security Centre CEO cited two frameworks\" (W08.3). DC07 found no banned terms.",
    "why_it_matters": "Presenting a trade outlet's emotive phrase as the EU Executive Vice-President's own words misattributes opinion and makes the EU's position sound more alarmist than the pack shows.",
    "required_fix": "Remove the quotation marks around rogue AI agents and attribute the phrase to the outlet, e.g. '…called Europe \"well equipped\" to deal with what the outlet calls rogue AI agents [W02].' Alternatively, use neutral wording such as 'AI agents that escape control'."
  }
]
```