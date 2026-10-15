```json
[
  {
    "id": "R01",
    "verdict": "FAIL",
    "evidence": "Uncited factual sentences: (1) Bottom line: \"The pack shows no new binding UAE AI rule this week.\" has no ID and no (Inference) label. (2) Bottom line: \"The EU Scientific Panel met on agentic AI loss-of-control incidents.\" has no ID; the citation sits on the next sentence. (3) Item 1: \"The panel has been investigating recent loss-of-control incidents and was to present recommendations.\" has no ID, although W01.2 and W01.3 support it. (4) Item 2 Why: \"This is a High-grade source for the authority's existence, which the watchlist previously held only on Low sources.\" is stated as fact with no ID; the (Inference) label covers only the next sentence. DC03 (all cited IDs exist) is noted.",
    "why_it_matters": "Readers on a phone cannot trace the Bottom line's lead EU claim or the UAE authority's grade upgrade to any pack extract.",
    "required_fix": "Add [W01] to the Bottom line panel sentence and to the Item 1 'investigating…recommendations' sentence. Label the 'no new binding UAE AI rule' sentence (Inference). Cite [W10] for the High-grade claim in Item 2 Why and label the watchlist comparison (Inference)."
  },
  {
    "id": "R02",
    "verdict": "FAIL",
    "evidence": "(1) Bottom line: \"met on agentic AI loss-of-control incidents\". W01.2 says only \"recent loss-of-control incidents\"; 'agentic' comes from W02.2, so this merges two sources under one ID. (2) Item 1: \"held a special meeting… on 09 Oct 2026 [W01]\". The W01 extracts give no meeting date; 09 Oct 2026 is only the publication date. (3) Item 2 headline: \"UAE announces federal AI and data authority; agentic AI project advances\". W10.3 says the UAE \"also announced\" the authority with no date, inside a 2026 round-up, and W10.2 gives no date for the framework approval. The brief presents these as this-week events without support.",
    "why_it_matters": "Leadership could treat the UAE authority as a new development this week and the EU meeting as focused on agents, when the cited extracts say neither.",
    "required_fix": "Change the Bottom line to 'met on recent loss-of-control incidents [W01]'. Change Item 1 to 'in a press release dated 09 Oct 2026 [W01]'. Retitle Item 2 so it reports what the 11 Oct 2026 WAM round-up says, and state that the announcement date is not given [W10]."
  },
  {
    "id": "R03",
    "verdict": "PASS",
    "evidence": "Low-grade W04 appears only in Excluded and in For human decision (\"only Low-grade W04 gives one [W03][W04]\"). Each Excluded reason is true: \"W07 gives no number\" (W07.4); \"W03 shows no date\" (W03 capture note); Norway \"no other pack source\" (W04.4). Low-grade W09 is excluded as a derivative aggregator (W09 capture note cites Dubai Future Foundation). Confidence levels fit the sources: Item 1 High rests on W01 (High) for the meeting; Item 3 High rests on W06 (High); Item 4 Medium rests on single Medium-grade W08. No Low source supports any claim alone.",
    "why_it_matters": "Unverified newsletter claims, such as the ICO count and Norway's plans, are kept out of the brief's findings.",
    "required_fix": "None"
  },
  {
    "id": "R04",
    "verdict": "PASS",
    "evidence": "Standardisation date conflict (W03 shows no date; W04.1 says 06 Oct 2026) is escalated: \"Legal: Can the adoption date… be confirmed, given W03 shows none and only Low-grade W04 gives one [W03][W04]?\". The ICO developer-count discrepancy (W04.3 says ten; W07.4 states no number) is resolved in Excluded with a reason. The UAE authority's grade change versus the watchlist's Low-grade basis is addressed in Item 2 (W10). No other pack disagreement bears on the brief.",
    "why_it_matters": "The disputed EU date and ICO figure are not presented as settled facts.",
    "required_fix": "None"
  },
  {
    "id": "R05",
    "verdict": "FAIL",
    "evidence": "(1) Header \"Sources used: 10 of 14\": DC03 lists 8 cited IDs (W01, W02, W03, W04, W06, W07, W08, W10), so n should be 8. (2) Sources table titles do not match the source text. W05 reads \"Government response to National Commission on regulation of AI in healthcare\"; the source title is \"…to the National Commission's recommendations on the regulation of AI in healthcare\". W07 drops \": our work to create regulatory certainty\". W13 drops \": enforcement proceedings, access to file, confidentiality, and limitation periods for penalties\". W03 is shortened. Dates and numbers in the body (20 Nov 2026, 33, 300, 50%) match W06, W08 and W10. DC09 passes.",
    "why_it_matters": "A wrong source count and altered titles undermine traceability for the governance committee that relies on this brief.",
    "required_fix": "Change the header to 'Sources used: 8 of 14 (1 excluded by the workflow)'. Copy the W03, W05, W07 and W13 titles exactly as given in the pack."
  }
]
```