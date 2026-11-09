"""Retrieval evaluation: hit@5 (document-level and article/section-level) and MRR@5
for BM25, vector (ChromaDB via ITU reference KB) and hybrid retrieval.

    python -m mizan.kb_eval
Writes kb/eval/results.json and kb/eval/RESULTS.md. Numbers are whatever the run produces.
"""
from __future__ import annotations
import json, time
from datetime import datetime, timezone
from mizan import retrieval as R
from mizan.embed import backend_label
from mizan.refcode import ROOT

K = 5


def sec_match(cid, golds):
    return any(cid == g or cid.startswith(g + "-") for g in golds)


def main():
    qs = json.loads((ROOT / "kb/eval/queries.json").read_text())
    methods = {"bm25": lambda q: R.bm25().search(q, K), "hybrid": lambda q: R.hybrid(q, K)}
    if R.vector_available():
        methods["vector"] = lambda q: R.vector_search(q, K)
    res = {"run_at": datetime.now(timezone.utc).isoformat(), "k": K, "n_queries": len(qs), "embedding": backend_label(), "methods": {}, "per_query": []}
    per = [{"q": q["q"], "gold_doc": q["doc"], "gold_sections": q["sections"]} for q in qs]
    for name, fn in methods.items():
        t0 = time.time(); dh = sh = sn = 0; mrr = 0.0
        for q, p in zip(qs, per):
            hits = fn(q["q"])
            ids = [h.chunk_id for h in hits]
            d_rank = next((i for i, h in enumerate(hits) if h.doc_id == q["doc"]), None)
            dh += d_rank is not None
            mrr += 1 / (d_rank + 1) if d_rank is not None else 0
            if q["sections"]:
                sn += 1; sh += any(sec_match(c, q["sections"]) for c in ids)
            p[name] = ids
        res["methods"][name] = {"doc_hit@5": round(dh / len(qs), 3), "doc_hits": dh, "section_hit@5": round(sh / sn, 3) if sn else None,
                                "section_hits": sh, "section_queries": sn, "doc_mrr@5": round(mrr / len(qs), 3), "seconds": round(time.time() - t0, 2)}
    res["per_query"] = per
    (ROOT / "kb/eval/results.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    lines = [f"# KB retrieval evaluation ({res['run_at']})", "", f"{len(qs)} hand-written queries, gold document per query, gold article/section for {per and sum(1 for q in qs if q['sections'])} of them. k={K}. Embedding: {res['embedding']}.", "",
             "| method | doc hit@5 | section hit@5 | doc MRR@5 |", "|---|---|---|---|"]
    for n, m in res["methods"].items():
        lines.append(f"| {n} | {m['doc_hits']}/{len(qs)} ({m['doc_hit@5']}) | {m['section_hits']}/{m['section_queries']} ({m['section_hit@5']}) | {m['doc_mrr@5']} |")
    lines += ["", "Misses (hybrid):"]
    for q, p in zip(qs, per):
        if not any(c.startswith(q["doc"] + ":") for c in p["hybrid"]) or (q["sections"] and not any(sec_match(c, q["sections"]) for c in p["hybrid"])):
            lines.append(f"- {q['q']} → got {p['hybrid'][:3]}")
    (ROOT / "kb/eval/RESULTS.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
