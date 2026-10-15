```json
[
  {
    "id": "R01",
    "verdict": "PASS",
    "evidence": "Every factual sentence carries a valid pack ID. Examples: \"closes 20 Nov 2026 [W06]\"; \"a WAM report says... [W10]\"; \"Henna Virkkunen [W01] called Europe... [W02]\"; \"33 Dubai Government entities... [W08]\"; the Confidence lines cite [W01], [W06] and [W08]; the For human decision entry cites \"news-agency report [W10]\". The table rows name their Source ID. The uncited sentences are labelled (Inference) or (Assumption P4), so they are exempt. DC03: cited IDs W01, W02, W06, W07, W08, W10; unknown: none.",
    "why_it_matters": "Leadership can trace every stated fact to a pack extract before acting on it.",
    "required_fix": "None"
  },
  {
    "id": "R02",
    "verdict": "FAIL",
    "evidence": "Item 1: \"Henna Virkkunen [W01] called Europe \\\"well equipped\\\" to deal with \\\"rogue AI agents\\\" [W02]\". W02's capture note says quoted phrases are verbatim. W02.1 quotes only \"well equipped\" and \"the whole life cycle\". \"rogue AI agents\" is the outlet's paraphrase, not a quotation from Virkkunen, so the brief presents it as her words without support. All other sentences check out against their extracts: W01.2 for the loss-of-control quote, W06.1–W06.2 for the call for evidence, W08.2–W08.3 for the accelerator, W07.4 for \"gives no number\", W03 metadata, and W09.2.",
    "why_it_matters": "Presenting a journalist's paraphrase as a direct quote from an EU Executive Vice-President misrepresents what an official actually said.",
    "required_fix": "Remove the quotation marks around rogue AI agents, e.g. 'called Europe \"well equipped\" to deal with rogue AI agents [W02]'."
  },
  {
    "id": "R03",
    "verdict": "PASS",
    "evidence": "No Low-grade source (W04, W09) is cited as evidence for any claim (DC04; DC03 cited IDs exclude W04 and W09). Item 2 has High confidence and rests on a single High-grade source [W06], so the two-source cap does not apply. W04 and W09 appear under Excluded, and their reasons are true: \"W07 dated 13 Oct 2026 and gives no number\" (W07.4); \"W03 shows no adoption date\" (W03 capture note); \"single source, no corroboration in pack\" (Norway, W04.4 only); \"repeats W08; analysis is outlet's own\" (W09.2).",
    "why_it_matters": "Readers can trust that no claim rests only on the third-party newsletter or the aggregator.",
    "required_fix": "None"
  },
  {
    "id": "R04",
    "verdict": "PASS",
    "evidence": "Disagreements that bear on the brief are handled. On the ICO findings date, W04.3 gives 08 Oct and W07 is dated 13 Oct with no developer count; the Excluded row \"W07 dated 13 Oct 2026 and gives no number [W07]\" resolves this in favour of the High-grade source. On the standardisation proposal date, W04.1 gives 6 Oct while W03 shows no date; the brief excludes the claim because the week is unconfirmed. No other pack sources contradict each other on dates, names or rule existence: W01 and W02 agree on the panel meeting, and W08 and W09 agree on 33 entities and 300+ use cases.",
    "why_it_matters": "Readers are not left with unresolved contradictions about what happened in the reporting week.",
    "required_fix": "None"
  },
  {
    "id": "R05",
    "verdict": "PASS",
    "evidence": "Dates match their sources: \"09 Oct 2026\" (W01), \"08 Oct 2026\" and \"20 Nov 2026\" (W06.1), \"05 Oct 2026\" (W08), \"13 Oct 2026\" (W07) and \"12 Oct 2026\" (W13). Numbers match: \"33\" and \"more than 300\" (W08.2). Names match: \"Henna Virkkunen\", \"Agentic AI for Government Services Accelerator\", \"Dubai Electronic Security Centre\" and \"Federal Authority for Artificial Intelligence and Data\". \"Commission Executive Vice-President\" is a faithful shortening of the W01.1 title. All dates use DD Mon YYYY (DC09: non-standard dates none). The W04 title \"5–11 October 2026\" is copied verbatim from the source.",
    "why_it_matters": "Exact dates such as the 20 Nov 2026 closing date drive the only action and the only Dates ahead entry.",
    "required_fix": "None"
  }
]
```