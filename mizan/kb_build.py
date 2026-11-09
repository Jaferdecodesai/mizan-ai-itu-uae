"""Build the Mizan UAE government-services knowledge base.

Pipeline (Y.3172 SRC -> C -> PP): official public documents (kb/raw, fetched
from the URLs in kb/sources.json) -> text extraction -> article/section/page
chunks with metadata -> embeddings -> ChromaDB collection `kb_main` via the ITU
reference KnowledgeBase (server.knowledge.kb) -> portable export
(kb/export/chunks.jsonl + kb/export/manifest.json).

    python -m mizan.kb_build [--reset]
"""
from __future__ import annotations
import argparse, hashlib, json, logging, re, sys, time
from datetime import datetime, timezone
from pathlib import Path

from mizan import embed, textextract as tx
from mizan.refcode import ROOT, CHROMA_DIR, ref_ingest, ref_kb_class

log = logging.getLogger("mizan.kb_build")
RAW = ROOT / "kb" / "raw"
EXPORT = ROOT / "kb" / "export"
COLLECTION = "kb_main"


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40]


def chunks_for(src: dict) -> list[tuple[str, str]]:
    path = RAW / src["file"]
    kind = src["kind"]
    if kind == "pdf":
        return tx.chunk_pdf(str(path))
    text = tx.html_to_text(path.read_text(encoding="utf-8", errors="replace"))
    if kind == "law_uae":
        return tx.chunk_uae_law(text)
    if kind == "law_eu":
        return tx.chunk_eu_law(text)
    if src["doc_id"] == "oecd-ai-principles":
        return tx.chunk_oecd(text)
    # portal pages: drop site chrome before the page title
    t0 = text.find(src["title"].split(" (")[0][:30])
    return tx.chunk_html_page(text[t0:] if t0 > 0 else text)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true")
    ap.add_argument("--no-vector", action="store_true", help="only write the portable export")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    sources = json.loads((ROOT / "kb" / "sources.json").read_text())
    EXPORT.mkdir(parents=True, exist_ok=True)
    ing = ref_ingest()
    all_rows, manifest = [], []
    for src in sources:
        p = RAW / src["file"]
        if not p.exists():
            log.error("missing %s (run scripts/fetch_sources.sh)", p); continue
        sha = hashlib.sha256(p.read_bytes()).hexdigest()
        pieces = chunks_for(src)
        seen = {}
        for i, (label, text) in enumerate(pieces):
            base = f"{src['doc_id']}:{slug(label.split(' – ')[0])}"
            seen[base] = seen.get(base, 0) + 1
            cid = base if seen[base] == 1 else f"{base}-{seen[base]}"
            # metadata built with the ITU reference build_metadata, plus Mizan fields
            meta = ing.build_metadata(p, i, len(pieces), {
                "document_category": "UAE_GovServices" if src["scope"] == "UAE" else "Global_Examples",
                "doc_id": src["doc_id"], "chunk_id": cid, "section": label, "title": src["title"],
                "issuer": src["issuer"], "status": src["status"], "scope": src["scope"], "url": src["url"],
                "language": src["language"], "doc_date": src["date"]})
            meta["country"] = "United Arab Emirates" if src["scope"] == "UAE" else meta["country"]
            all_rows.append({"id": cid, "text": text, "meta": meta})
        manifest.append({**{k: src[k] for k in ("doc_id", "title", "issuer", "date", "status", "scope", "url", "language", "licence")},
                         "binding": "binding" if "binding" in src["status"] and "non-binding" not in src["status"] else "guidance/non-binding",
                         "local_file": f"kb/raw/{src['file']}", "sha256": sha, "bytes": p.stat().st_size,
                         "chunks": len(pieces), "chunking": {"law_uae": "article", "law_eu": "article/annex", "pdf": "page (ITU chunk_text 256w/30)", "html": "section/part (ITU chunk_text)"}[src["kind"]] if src["doc_id"] != "oecd-ai-principles" else "principle",
                         "fetched": datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat()})
        log.info("%-28s %4d chunks", src["doc_id"], len(pieces))
    with open(EXPORT / "chunks.jsonl", "w", encoding="utf-8") as f:
        for r in all_rows:
            m = r["meta"]
            f.write(json.dumps({"chunk_id": r["id"], "doc_id": m["doc_id"], "section": m["section"], "title": m["title"],
                                "issuer": m["issuer"], "status": m["status"], "scope": m["scope"], "url": m["url"],
                                "language": m["language"], "doc_date": m["doc_date"], "text": r["text"]}, ensure_ascii=False) + "\n")
    info = {"built_at": datetime.now(timezone.utc).isoformat(), "documents": len(manifest), "chunks": len(all_rows),
            "embedding_backend": embed.backend_label(), "vector_store": "ChromaDB (ITU reference KnowledgeBase, collection kb_main, cosine)",
            "not_ingested": json.loads((ROOT / "kb" / "not_ingested.json").read_text()), "sources": manifest}
    (EXPORT / "manifest.json").write_text(json.dumps(info, indent=1, ensure_ascii=False))
    log.info("export: %d docs, %d chunks", len(manifest), len(all_rows))
    if a.no_vector:
        return
    kb = ref_kb_class()(str(CHROMA_DIR))
    if a.reset:
        try: kb.delete_collection(COLLECTION)
        except Exception: pass
    t0 = time.time()
    B = 64
    for i in range(0, len(all_rows), B):
        batch = all_rows[i:i + B]
        embs = embed.embed_docs([r["text"] for r in batch])
        kb.add_documents([r["text"] for r in batch], embs, [r["meta"] for r in batch], COLLECTION, [r["id"] for r in batch])
        log.info("embedded %d/%d", min(i + B, len(all_rows)), len(all_rows))
    info["vector_build_seconds"] = round(time.time() - t0, 1)
    info["vector_count"] = kb.count(COLLECTION)
    (EXPORT / "manifest.json").write_text(json.dumps(info, indent=1, ensure_ascii=False))
    log.info("vector store: %d chunks in %.1fs", info["vector_count"], info["vector_build_seconds"])


if __name__ == "__main__":
    main()
