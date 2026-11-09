"""Gap register: domain-level policy / standards gaps with global examples.

For each candidate gap the Policy & Legal Adviser (1) probes the UAE part of the
KB with a retrieval query and checks whether the best-matching UAE chunks contain
all 'explicit provision' terms (found / partial / not found in KB), and (2)
retrieves global examples from named comparator documents.  Results depend on
the KB contents; 'not found in KB' is NOT the same as 'absent from UAE law' –
the KB is incomplete (see kb/not_ingested.json), so every row needs expert review.
"""
from __future__ import annotations
import re
from mizan import retrieval as R
from mizan.agents import UAE_ALL

GAPS = [
 {"id": "G1", "type": "responsibility", "title": "Who notifies residents when a public-service AI agent gives wrong answers?",
  "description": "Personal-data breach duties exist, but the incident here is mainly harmful *advice* (wrong eligibility answers). No role is clearly responsible for notifying and correcting affected residents for AI-output harm that is not a data breach.",
  "trigger": ["E3"], "probe": "notify affected persons when an artificial intelligence system causes harm or incorrect output", "terms": ["artificial intelligence", "notif"],
  "global": [("eu-ai-act-2024", "deployer inform natural persons subject to high-risk AI system use"), ("eu-ai-act-2024", "serious incident reporting providers market surveillance")], "dims": [6, 9, 10]},
 {"id": "G2", "type": "standard", "title": "No AI-incident reporting standard for public-sector GenAI",
  "description": "There is no common taxonomy, threshold or timeline for reporting AI incidents (wrong outputs, unsafe routing, confabulation) by government AI services, separate from cyber or data-breach reporting.",
  "trigger": ["E1", "E3"], "probe": "reporting of AI incidents serious incident artificial intelligence system timeline", "terms": ["incident", "artificial intelligence"],
  "global": [("eu-ai-act-2024", "reporting of serious incidents immediately after causal link"), ("nist-ai-600-1", "incident disclosure generative AI"), ("sg-genai-mgf-2024", "incident reporting")], "dims": [10, 12]},
 {"id": "G3", "type": "technology / legislative", "title": "Automated failover can create a cross-border transfer nobody approved",
  "description": "Transfer rules assume a deliberate transfer decision. Infrastructure automation (failover, load-balancing to other regions) can move personal data abroad without a decision, and AI vendor contracts may not name failover regions or log retention.",
  "trigger": ["E1", "E2", "E5"], "probe": "failover backup region processing location cloud contract personal data outside the State", "terms": ["failover"],
  "global": [("eu-gdpr-2016", "processor contract documented instructions sub-processors"), ("eu-gdpr-2016", "transfers subject to appropriate safeguards")], "dims": [13, 10]},
 {"id": "G4", "type": "objective conflict", "title": "Fixing the model fast vs purpose limitation",
  "description": "Pressure to improve a public AI service quickly (innovation, service quality) conflicts with purpose limitation when the only data that shows the failure is incident data from residents.",
  "trigger": ["E6"], "probe": "use of personal data for training artificial intelligence models purpose", "terms": ["train", "personal data"],
  "global": [("eu-ai-act-2024", "training validation testing data sets data governance"), ("eu-gdpr-2016", "processing for another purpose compatible with original purpose"), ("oecd-ai-principles", "privacy data protection rule of law human rights")], "dims": [1, 7, 10]},
 {"id": "G5", "type": "coordination", "title": "Crisis communication about a government AI incident",
  "description": "Counter-misinformation law, data-protection notification and service communication sit with different actors. Without a joint protocol the public notice can be late, inconsistent, or omit the true part of a partly-false rumour.",
  "trigger": ["E4"], "probe": "coordinated public communication during incident misinformation government AI transparency", "terms": ["artificial intelligence", "communicat"],
  "global": [("nist-ai-600-1", "information integrity"), ("oecd-ai-principles", "transparency responsible disclosure")], "dims": [2, 6, 8]},
 {"id": "G6", "type": "standard", "title": "Record-keeping and log retention for government AI agents",
  "description": "Auditability needs defined logging (inputs, retrieved sources, outputs, human decisions) and retention rules for AI agents, including logs held by vendors.",
  "trigger": ["E5"], "probe": "automatic logging record keeping of events artificial intelligence system retention", "terms": ["log", "artificial intelligence"],
  "global": [("eu-ai-act-2024", "record-keeping automatic recording of events logs"), ("nist-ai-rmf-1", "documentation accountability transparency")], "dims": [9, 10]},
]


def _status(hits, terms):
    best = None
    for h in hits:
        tl = h.text.lower()
        have = [t for t in terms if re.search(r"\b" + re.escape(t), tl)]
        if best is None or len(have) > len(best[1]):
            best = (h, have)
    h, have = best
    st = "provision found in KB" if len(have) == len(terms) else ("partial match in KB" if have else "not found in KB")
    return st, h, have


def build_register(trigger_events: set[str]) -> list[dict]:
    out = []
    for g in GAPS:
        if not set(g["trigger"]) & trigger_events:
            continue
        uae_hits = R.hybrid(g["probe"], k=3, doc_ids=UAE_ALL)
        st, h, have = _status(uae_hits, g["terms"])
        glob = []
        for doc, q in g["global"]:
            gh = R.hybrid(q, k=1, doc_ids=[doc])
            if gh:
                x = gh[0]
                glob.append({"chunk_id": x.chunk_id, "doc_id": x.doc_id, "title": x.title, "section": x.section, "url": x.url,
                             "quote": R.best_sentence(x.text, q), "query": q})
        out.append({**{k: g[k] for k in ("id", "type", "title", "description", "trigger", "dims")},
                    "uae_mapping": {"status": st, "probe": g["probe"], "terms_required": g["terms"], "terms_found": have,
                                    "closest": {"chunk_id": h.chunk_id, "section": h.section, "title": h.title, "url": h.url, "quote": R.best_sentence(h.text, g["probe"])},
                                    "candidates": [x.chunk_id for x in uae_hits]},
                    "global_examples": glob, "confidence": "medium" if st != "provision found in KB" else "low",
                    "needs_expert_review": True, "scope_note": "Domain-level gap for public-service AI; not a country-specific recommendation."})
    return out
