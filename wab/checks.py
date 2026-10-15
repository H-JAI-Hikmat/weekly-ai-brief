"""Deterministic checks on a draft brief. They run before the AI judges and cannot be overruled by them:
a deterministic FAIL fails the mapped rubric criterion regardless of what any judge says."""
import re

SECTIONS = ["Bottom line", "What changed this week", "Dates ahead", "Excluded or unverified",
            "Assumptions to confirm", "For human decision", "Sources"]
CITE = re.compile(r"\[([^\]]*\bW\d{2}\b[^\]]*)\]")
ID = re.compile(r"\bW\d{2}\b")
BAD_DATE = re.compile(r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}, \d{4}\b|\b20\d{2}-\d{2}-\d{2}\b")


def words(text):
    return sum(1 for t in text.split() if re.search(r"[A-Za-z0-9]", t))


def sections(md):
    out, cur = {"_preamble": []}, "_preamble"
    for line in md.splitlines():
        if line.startswith("## "):
            cur = line[3:].strip()
            out[cur] = []
            continue
        out.setdefault(cur, []).append(line)
    return {k: "\n".join(v) for k, v in out.items()}


def run_checks(md, sources, policy):
    """Return a list of {id, criterion, result PASS/FAIL, detail}."""
    secs = sections(md)
    res = []

    def add(cid, crit, ok, detail):
        res.append({"id": cid, "criterion": crit, "result": "PASS" if ok else "FAIL", "detail": detail})

    # DC01 section order
    found = [k for k in secs if k != "_preamble"]
    order_ok = [s for s in found if s in SECTIONS] == SECTIONS and md.lstrip().startswith("# ")
    add("DC01", "R09", order_ok, f"sections found: {found}")

    # DC02 lengths, item count, headline length
    body = words(secs.get("Bottom line", "")) + words(secs.get("What changed this week", ""))
    whole = words(md.split("\n## Sources")[0])
    heads = re.findall(r"^### \d+\.\s*(.+?)\s+—", md, flags=re.M)
    long_heads = [h for h in heads if words(h) > 12]
    ok = body <= 450 and whole <= 850 and 1 <= len(heads) <= 5 and not long_heads
    add("DC02", "R09", ok, f"BODY {body}/450, WHOLE {whole}/850, items {len(heads)}/5, headlines over 12 words: {long_heads or 'none'}")

    # DC03 every cited ID exists in the pack
    known = {s["id"] for s in sources}
    cited = set()
    for grp in CITE.findall(md):
        cited |= set(ID.findall(grp))
    unknown = sorted(cited - known)
    add("DC03", "R01", not unknown, f"cited IDs: {sorted(cited)}; unknown: {unknown or 'none'}")

    # DC04 workflow-excluded sources are never cited as evidence in the body
    excluded = {s["id"] for s in sources if s["status"] in ("QUARANTINED", "UNAVAILABLE")}
    body_text = secs.get("Bottom line", "") + secs.get("What changed this week", "") + secs.get("Dates ahead", "")
    body_cited = set()
    for grp in CITE.findall(body_text):
        body_cited |= set(ID.findall(grp))
    bad = sorted(body_cited & excluded)
    add("DC04", "R10", not bad, f"excluded sources cited as evidence: {bad or 'none'}")

    # DC05 every workflow-excluded source is disclosed in "Excluded or unverified"
    exc_sec = secs.get("Excluded or unverified", "")
    missing = sorted(i for i in excluded if i not in exc_sec)
    add("DC05", "R10", not missing, f"workflow-excluded: {sorted(excluded) or 'none'}; not disclosed: {missing or 'none'}")

    # DC06 no PII patterns in the brief
    hits = {k: len(re.findall(p, md)) for k, p in policy["security"]["pii_patterns"].items()}
    hits = {k: v for k, v in hits.items() if v}
    add("DC06", "R10", not hits, f"PII pattern hits: {hits or 'none'}")

    # DC07 no banned (loaded) terms
    low = md.lower()
    banned = [t for t in policy["tone"]["banned_terms"] if t in low]
    add("DC07", "R11", not banned, f"banned terms found: {banned or 'none'}")

    # DC08 every item has the four required fields
    items = re.split(r"^### ", secs.get("What changed this week", ""), flags=re.M)[1:]
    need = ["What happened:", "Why it matters to us:", "Action:", "Confidence:"]
    gaps = [f"item {i + 1}: missing {[n for n in need if n not in it]}" for i, it in enumerate(items) if any(n not in it for n in need)]
    add("DC08", "R08", not gaps, f"{gaps or 'all items complete'}")

    # DC09 date format DD Mon YYYY (no 'October 9, 2026' or ISO dates)
    bad_dates = sorted(set(BAD_DATE.findall(md.split("\n## Sources")[0])))  # v1.3.0: Sources table (links) is workflow-built
    add("DC09", "R05", not bad_dates, f"non-standard dates: {bad_dates or 'none'}")

    return res, {"body_words": body, "whole_words": whole, "items": len(heads)}
