"""Citation verifier.

For every claim in ASSESS/PROPOSE/OBJECT messages:
  UNCITED   – no citation at all
  INVALID   – cited chunk/event id does not exist, or the quote is not a verbatim span of it
  WEAK      – citation exists and quote is verbatim, but lexical overlap between the claim and the
              cited text is below threshold (possible irrelevant citation; flagged for human review)
  INFO      – INFORM/REQUEST/DECIDE content without sources (not a claim type)
  SUPPORTED – verbatim quote from an existing source with overlap above threshold
Nothing here proves legal correctness; SUPPORTED means "traceable and on-topic", not "legally right".
"""
from __future__ import annotations
import re
from mizan.retrieval import by_id, tokenize

WEAK_OVERLAP = 2


def _norm(s):
    return re.sub(r"\s+", " ", s).strip().lower()


def verify_claim(claim, events: dict, requires_citation: bool):
    if not claim.citations:
        claim.status = "UNCITED" if requires_citation else "INFO"
        claim.note = "no source attached" if requires_citation else "informational (event-sourced)"
        return claim
    overlaps = []
    for c in claim.citations:
        if c.kind == "event":
            src = events.get(c.chunk_id)
            text = src["body"] if src else None
        else:
            src = by_id().get(c.chunk_id)
            text = src["text"] if src else None
        if text is None:
            claim.status, claim.note = "INVALID", f"unknown source {c.chunk_id}"
            return claim
        if _norm(c.quote) not in _norm(text):
            claim.status, claim.note = "INVALID", f"quote not found verbatim in {c.chunk_id}"
            return claim
        overlaps.append(len(set(tokenize(claim.text)) & set(tokenize(text))))
    best = max(overlaps)
    claim.status = "SUPPORTED" if best >= WEAK_OVERLAP else "WEAK"
    claim.note = f"max term overlap {best}"
    return claim


def verify_message(msg, events):
    from mizan.protocol import CLAIM_TYPES
    for cl in msg.claims:
        verify_claim(cl, events, msg.type in CLAIM_TYPES)
    return msg
