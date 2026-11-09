"""Text extraction and structure-aware (article / section / page) chunking.

PDF parsing re-uses the ITU reference parser (server.knowledge.ingest.parse_file
falls back to PyMuPDF); here we call PyMuPDF page-by-page so every chunk keeps
its page number for source attribution. Generic text is chunked with the ITU
reference chunker (server.knowledge.ingest.chunk_text, 256 words / 30 overlap).
"""
from __future__ import annotations
import html as _html
import re
from typing import Iterator

from mizan.refcode import ref_ingest

MAX_WORDS = 320


def html_to_text(raw: str) -> str:
    t = re.sub(r"(?is)<script.*?</script>|<style.*?</style>|<nav.*?</nav>|<header.*?</header>|<footer.*?</footer>", "", raw)
    t = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</li>|</h\d>|</tr>|</td>", "\n", t)
    t = _html.unescape(re.sub(r"<[^>]+>", " ", t))
    t = re.sub(r"[ \t\xa0\u200b]+", " ", t)
    t = re.sub(r"\n\s*\n+", "\n", t)
    return t.strip()


def _split_long(label: str, body: str) -> list[tuple[str, str]]:
    words = body.split()
    if len(words) <= MAX_WORDS:
        return [(label, body.strip())]
    parts = ref_ingest().chunk_text(body, chunk_size=MAX_WORDS - 30, overlap=30)
    return [(f"{label} (part {i+1}/{len(parts)})", p) for i, p in enumerate(parts)]


def chunk_uae_law(text: str) -> list[tuple[str, str]]:
    """uaelegislation.gov.ae pages: a table of contents, then the body. Split body by 'Article (n)'."""
    starts = [m.start() for m in re.finditer(r"\n\s*Article \(1\)", "\n" + text)]
    body = ("\n" + text)[starts[-1]:] if starts else text
    # cut trailing site chrome
    for stop in ["\n Related Legislations", "\nRelated Legislations", "Was this page helpful"]:
        k = body.find(stop)
        if k > 0:
            body = body[:k]
    pieces = re.split(r"\n[^\n]{0,80}?(Article \(\d+\)[^\n]*)", body)
    out = []
    for i in range(1, len(pieces), 2):
        head = pieces[i].strip()
        num = re.search(r"\((\d+)\)", head).group(1)
        title = head.split(")", 1)[1].strip() if ")" in head else ""
        out += _split_long(f"Art. {num}" + (f" – {title}" if title else ""), head + "\n" + pieces[i + 1])
    return out


def chunk_eu_law(text: str) -> list[tuple[str, str]]:
    k = text.find("HAVE ADOPTED THIS REGULATION")
    body = text[k:] if k > 0 else text
    pieces = re.split(r"\n\s*((?:Article \d+|ANNEX [IVXL]+)\s*\n[^\n]*)", body)
    out = []
    for i in range(1, len(pieces), 2):
        head = " ".join(pieces[i].split())
        m = re.match(r"(Article (\d+)|ANNEX ([IVXL]+))\s*(.*)", head)
        label = (f"Art. {m.group(2)}" if m.group(2) else f"Annex {m.group(3)}") + (f" – {m.group(4)}" if m.group(4) else "")
        out += _split_long(label, head + "\n" + pieces[i + 1])
    return out


def chunk_oecd(text: str) -> list[tuple[str, str]]:
    k = text.find("THE COUNCIL")
    body = text[k:] if k > 0 else text
    pieces = re.split(r"\n\s*(\d\.\d\.\s[^\n]*)", body)
    out = _split_long("Preamble & definitions", pieces[0])
    for i in range(1, len(pieces), 2):
        head = " ".join(pieces[i].split())
        if head.startswith("2.5"):
            pieces[i + 1] = " ".join(pieces[i + 1].split()[:260])
        out += _split_long(f"Principle {head[:3]} – {head[4:].strip()[:80]}", head + "\n" + pieces[i + 1])
    return out


def chunk_html_page(text: str) -> list[tuple[str, str]]:
    parts = ref_ingest().chunk_text(text)
    return [(f"Part {i+1}/{len(parts)}", p) for i, p in enumerate(parts)]


def chunk_pdf(path: str) -> list[tuple[str, str]]:
    import fitz  # PyMuPDF, same parser the ITU reference falls back to
    doc = fitz.open(path)
    out = []
    for pno, page in enumerate(doc, start=1):
        txt = re.sub(r"[ \t]+", " ", page.get_text()).strip()
        if len(txt.split()) < 25:
            continue
        for j, c in enumerate(ref_ingest().chunk_text(txt)):
            out.append((f"p. {pno}" + (f" ({j+1})" if j else ""), c))
    return out
