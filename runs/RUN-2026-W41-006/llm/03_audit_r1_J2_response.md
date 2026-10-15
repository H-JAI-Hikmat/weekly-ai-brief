```json
[
  {
    "id": "R06",
    "verdict": "FAIL",
    "evidence": "Item 2, \"UAE federal report cites agentic AI project and new AI authority\", treats an 11 Oct 2026 year-in-review report [W10] as the event. The events it describes are not dated inside 05–11 Oct 2026. The brief admits \"announcement date and powers are not given\". The Federal Authority was already on the Week 40 watchlist, so it was announced before this week. The National Committee approval is undated [W10.2, W10.3]. None of these sentences carries the label \"Background:\". Items 1 (09 Oct, W01/W02), 3 (05 Oct, W08) and 4 (08 Oct, W06) are in-week.",
    "why_it_matters": "Readers will take the federal authority and the Agentic AI Project as this week's news, when the pack shows they predate the week or are undated.",
    "required_fix": "Prefix item 2's project, committee and authority sentences with \"Background:\" and state that only the report is dated in the week. Alternatively, drop item 2 as a lead item and keep the Legal action under the relevant section."
  },
  {
    "id": "R08",
    "verdict": "PASS",
    "evidence": "Each Why ties to the profile: P2/P3/P4 in item 1, P3 in items 2 and 4, and no duty in item 3. Each Action follows from its Why. Item 2: \"Legal · find the primary instrument… by 06 Nov 2026\". Item 4: \"Head of IT Risk · ask Legal… by 30 Oct 2026\". Items 1 and 3: \"No action — monitor\". The Bottom line (\"No pack source reports a new binding rule…\"; \"Two actions…\") matches the items. Several sources are out-of-week or not plainly tied to P1–P6, and each is excluded with a reason: W07 (13 Oct), W11 (04 Oct), W12 (01 Oct), W13 (12 Oct), W05 (healthcare). No in-week P1–P6 development is omitted.",
    "why_it_matters": "Owners and dates trace cleanly from profile to action, so readers know who acts and when.",
    "required_fix": "None"
  },
  {
    "id": "R09",
    "verdict": "FAIL",
    "evidence": "DC02: \"BODY 664/450, WHOLE 912/850\". Both length limits are exceeded. The header field \"Sources used: 13 of 13\" conflicts with DC03, which lists 5 cited IDs (W01, W02, W06, W08, W10), so n is misstated. Section order passes (DC01). There are 4 items, all with required fields (DC08). All headlines are 12 words or fewer.",
    "why_it_matters": "At 664 body words, the brief exceeds the one-page, under-five-minute phone read its IT leadership audience depends on.",
    "required_fix": "Cut at least 214 words from Bottom line plus What changed by trimming each 'What happened' to one or two sentences and removing Bottom line detail repeated in items. This also brings the whole brief to 850 words or fewer. Correct the header to \"Sources used: 5 of 13 (0 excluded by the workflow)\", or to the count matching the cited IDs."
  }
]
```