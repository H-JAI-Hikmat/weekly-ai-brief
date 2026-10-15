```json
[
  {
    "id": "R07",
    "verdict": "FAIL",
    "evidence": "Bare (P2), (P3) and the For-human-decision use of (P2) all match the context card. The Assumptions row for P4 matches the card word for word. One failing instance: Item 1 Why says \"Direct EU AI Act duties on us depend on our placing nothing on the EU market (Assumption P4).\" The P4 tag covers only the premise. The legal conclusion about when AI Act duties apply carries no (Inference) label and is stated as fact. No pack extract says this (W01, W02).",
    "why_it_matters": "Readers who are not lawyers will take an unlabelled claim about EU AI Act applicability as settled fact. The brief's only EU link to us rests on that claim.",
    "required_fix": "Mark the legal clause as analysis and refer it to Legal, e.g. \"EU AI Act duties may not reach us if we place nothing on the EU market (Inference; Assumption P4); check with Legal.\""
  },
  {
    "id": "R10",
    "verdict": "FAIL",
    "evidence": "Workflow-excluded sources are disclosed as \"none\" (DC05 PASS). There is no personal data (DC06), and officials are named as reported in W01, W02 and W08. Failing instances are legal statements that do not come from the pack:\n(1) Item 4 Why: \"UK law applies to us only if we handle UK personal data.\" This is a definitive rule on UK data protection reach. W06 says nothing about territorial scope.\n(2) Item 1 Why: \"Direct EU AI Act duties on us depend on our placing nothing on the EU market.\" No pack extract states this.\n(3) Item 3 Why: \"so no duty on us follows.\" This is a legal conclusion about the Dubai frameworks, which W08 does not support.",
    "why_it_matters": "These sentences give readers legal conclusions that the pack does not support and that Legal has not checked. Two of them would wrongly reassure leadership that UK and EU rules do not reach us.",
    "required_fix": "Remove or soften the three legal conclusions to questions, e.g. \"Whether UK data protection law reaches us is unconfirmed (Inference); check with Legal.\" Do the same for the EU and Dubai sentences."
  },
  {
    "id": "R11",
    "verdict": "PASS",
    "evidence": "Officials are described by role and action, e.g. \"Henna Virkkunen, Executive Vice-President for Tech Sovereignty, Security and Democracy\" [W01] and \"Dubai Electronic Security Centre CEO Yousuf Hamad Al Shaibani said…\" [W08]. The term \"rogue AI agents\" sits in a sentence attributed \"according to Cryptopolitan citing Reuters\" [W02.1], so it is the source's wording, not the brief's. \"Loss-of-control incidents\" is quoted from W01.2. Headlines and Why lines are neutral. DC07 found no banned terms.",
    "why_it_matters": "Neutral, attributed wording keeps the brief usable as an impartial input to the monthly governance committee.",
    "required_fix": "None"
  }
]
```