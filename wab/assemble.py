"""Workflow-built parts of the brief (v1.3.0). The writer model never writes the Sources table or the
source count: the engine builds both from the manifest, so titles, publishers, dates, grades and links
are copied exactly and cannot drift between revisions."""
import re

from .checks import CITE, ID, sections

COUNT = re.compile(r"\s*·?\s*Sources used:[^\n]*")


def cited_ids(md):
    """Distinct Source IDs cited (in square brackets) outside 'Excluded or unverified' and 'Sources'."""
    secs = sections(md)
    out = set()
    for name, text in secs.items():
        if name in ("Excluded or unverified", "Sources"):
            continue
        for grp in CITE.findall(text):
            out |= set(ID.findall(grp))
    return out


def strip_sources(md):
    """Remove any Sources section (the writer is told not to write one; the workflow rebuilds it)."""
    return re.split(r"^## Sources\s*$", md, maxsplit=1, flags=re.M)[0].rstrip()


def _cell(text):
    return str(text or "").replace("|", "/").replace("\n", " ").strip()


def assemble(md, sources):
    """Return the brief with the workflow-built source count and Sources table, plus the cited IDs."""
    body = strip_sources(md.strip())
    by_id = {s["id"]: s for s in sources}
    used = sorted(i for i in cited_ids(body) if i in by_id)
    n_total = len(sources)
    k = sum(s["status"] in ("QUARANTINED", "UNAVAILABLE") for s in sources)
    count = f"Sources used: {len(used)} of {n_total} ({k} excluded by the workflow)"

    lines = body.splitlines()
    # header line = first non-empty line after the title
    idx = next((i for i, l in enumerate(lines) if i > 0 and l.strip() and not l.startswith("#")), None)
    if idx is not None and not lines[idx].startswith("## "):
        base = COUNT.sub("", lines[idx]).rstrip(" ·")
        lines[idx] = f"{base} · {count}" if base else count
    else:
        lines.insert(1, count)
    body = "\n".join(lines)

    rows = ["## Sources", "",
            "_Built by the workflow from the manifest: every source cited above, with the publisher, title, date and grade exactly as captured._", "",
            "| ID | Publisher | Title | Date | Grade |", "|---|---|---|---|---|"]
    for i in used:
        s = by_id[i]
        title = _cell(s.get("title"))
        link = f"[{title}]({s['url']})" if s.get("url") else title
        rows.append(f"| {i} | {_cell(s.get('publisher'))} | {link} | {_cell(s.get('date'))} | {_cell(s.get('grade'))} |")
    return body + "\n\n" + "\n".join(rows) + "\n", used
