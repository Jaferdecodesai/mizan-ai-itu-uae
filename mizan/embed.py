"""Embeddings.

The ITU reference code embeds with Ollama `nomic-embed-text`. Ollama is not
installed on the build box, so by default we run the *same model family*
(nomic-embed-text-v1.5, ONNX; the int8 "-Q" variant was tested and rejected: batch-inconsistent vectors) on CPU through `fastembed`.
Set MIZAN_EMBED=ollama to use the unmodified reference `embed_texts`
(requires a running Ollama with nomic-embed-text).
"""
from __future__ import annotations
import functools, os

MODEL = os.environ.get("MIZAN_EMBED_MODEL", "nomic-ai/nomic-embed-text-v1.5")
BACKEND = os.environ.get("MIZAN_EMBED", "fastembed")


@functools.lru_cache
def _model():
    from fastembed import TextEmbedding
    return TextEmbedding(MODEL)


def embed_docs(texts: list[str]) -> list[list[float]]:
    if BACKEND == "ollama":
        from mizan.refcode import ref_ingest
        return ref_ingest().embed_texts(texts)
    return [v.tolist() for v in _model().embed(["search_document: " + t[:2000] for t in texts], batch_size=16)]


def embed_query(q: str) -> list[float]:
    if BACKEND == "ollama":
        from mizan.refcode import ref_ingest
        return ref_ingest().embed_texts([q])[0]
    return list(_model().embed(["search_query: " + q]))[0].tolist()


def backend_label() -> str:
    return f"ollama:nomic-embed-text" if BACKEND == "ollama" else f"fastembed:{MODEL}"
