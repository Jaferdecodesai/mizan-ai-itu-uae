"""Retrieval over the Mizan KB.

* vector: ChromaDB `kb_main` through the ITU reference KnowledgeBase.search
  (cosine, nomic-embed-text embeddings)
* lexical: BM25 over the portable export (kb/export/chunks.jsonl) – works with
  no vector store at all (this is what the web KB browser uses, in JS)
* hybrid: reciprocal-rank fusion of the two (default for agents)
"""
from __future__ import annotations
import functools, json, math, re
from collections import Counter
from dataclasses import dataclass

from mizan.refcode import ROOT, CHROMA_DIR

EXPORT = ROOT / "kb" / "export" / "chunks.jsonl"
_STOP = set("a an the of to and or in on for by with from as at is are be been was were that this these those it its into than then which who whom whose shall may must can not no any all such other under where when what how does do".split())


def tokenize(s: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in _STOP and len(w) > 1]


@dataclass
class Hit:
    chunk_id: str
    doc_id: str
    section: str
    title: str
    url: str
    scope: str
    text: str
    score: float
    method: str

    def brief(self):
        return {"chunk_id": self.chunk_id, "doc_id": self.doc_id, "section": self.section, "score": round(self.score, 4), "method": self.method}


@functools.lru_cache
def chunks() -> list[dict]:
    return [json.loads(l) for l in EXPORT.open(encoding="utf-8")]


@functools.lru_cache
def by_id() -> dict:
    return {c["chunk_id"]: c for c in chunks()}


class BM25:
    def __init__(self, docs: list[dict], k1=1.4, b=0.75):
        self.docs = docs
        self.toks = [tokenize(d["title"] + " " + d["section"] + " " + d["text"]) for d in docs]
        self.tf = [Counter(t) for t in self.toks]
        self.dl = [len(t) for t in self.toks]
        self.avg = sum(self.dl) / max(1, len(self.dl))
        df = Counter(w for t in self.tf for w in t)
        n = len(docs)
        self.idf = {w: math.log(1 + (n - f + 0.5) / (f + 0.5)) for w, f in df.items()}
        self.k1, self.b = k1, b

    def search(self, q: str, k=5, doc_ids=None, scope=None):
        qt = tokenize(q)
        scored = []
        for i, d in enumerate(self.docs):
            if doc_ids and d["doc_id"] not in doc_ids: continue
            if scope and d["scope"] != scope: continue
            tf, s = self.tf[i], 0.0
            for w in qt:
                if w in tf:
                    f = tf[w]
                    s += self.idf[w] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * self.dl[i] / self.avg))
            if s > 0: scored.append((s, d))
        scored.sort(key=lambda x: -x[0])
        return [_hit(d, s, "bm25") for s, d in scored[:k]]


def _hit(d, s, m):
    return Hit(d["chunk_id"], d["doc_id"], d["section"], d["title"], d["url"], d["scope"], d["text"], float(s), m)


@functools.lru_cache
def bm25() -> BM25:
    return BM25(chunks())


@functools.lru_cache
def _kb():
    from mizan.refcode import ref_kb_class
    return ref_kb_class()(str(CHROMA_DIR))


def vector_search(q: str, k=5, doc_ids=None, scope=None) -> list[Hit]:
    from mizan.embed import embed_query
    where = None
    conds = []
    if doc_ids: conds.append({"doc_id": {"$in": list(doc_ids)}})
    if scope: conds.append({"scope": scope})
    if len(conds) == 1: where = conds[0]
    elif conds: where = {"$and": conds}
    r = _kb().search(embed_query(q), n_results=k, collection_name="kb_main", where=where)
    out = []
    for cid, dist in zip(r["ids"][0], r["distances"][0]):
        d = by_id().get(cid)
        if d: out.append(_hit(d, 1 - dist, "vector"))
    return out


def vector_available() -> bool:
    try:
        return _kb().count("kb_main") > 0
    except Exception:
        return False


def hybrid(q: str, k=5, doc_ids=None, scope=None, pool=20) -> list[Hit]:
    lists = [bm25().search(q, pool, doc_ids, scope)]
    if vector_available():
        lists.append(vector_search(q, pool, doc_ids, scope))
    fused: dict[str, float] = {}
    keep: dict[str, Hit] = {}
    for L in lists:
        for rank, h in enumerate(L):
            fused[h.chunk_id] = fused.get(h.chunk_id, 0) + 1 / (60 + rank + 1)
            keep.setdefault(h.chunk_id, h)
    ids = sorted(fused, key=lambda c: -fused[c])[:k]
    return [Hit(**{**keep[c].__dict__, "score": fused[c], "method": "hybrid" if len(lists) > 1 else "bm25"}) for c in ids]


def best_sentence(text: str, q: str, max_len=260) -> str:
    """Pick the verbatim sentence in a chunk that best overlaps the query (used as the quoted span)."""
    sents = [s.strip() for s in re.split(r"(?<=[.;:])\s+|\n", text) if len(s.strip()) > 30]
    if not sents:
        return text[:max_len]
    qt = set(tokenize(q))
    best = max(sents, key=lambda s: (len(qt & set(tokenize(s))), -abs(len(s) - 160)))
    return best[:max_len]
