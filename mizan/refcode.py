"""Loader for the vendored ITU reference code (third_party/ITUAIReadiness, MIT, (c) 2026 Vishnu Ram OV)."""
from __future__ import annotations
import functools, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REF_SIM = ROOT / "third_party" / "ITUAIReadiness" / "simulation"
CHROMA_DIR = ROOT / "data" / "chromadb"


def _path():
    os.environ.setdefault("AIREADY_CHROMADB_DIR", str(CHROMA_DIR))
    if str(REF_SIM) not in sys.path:
        sys.path.insert(0, str(REF_SIM))


@functools.lru_cache
def ref_ingest():
    _path()
    from server.knowledge import ingest  # noqa
    return ingest


@functools.lru_cache
def ref_kb_class():
    _path()
    from server.knowledge.kb import KnowledgeBase  # noqa
    return KnowledgeBase
