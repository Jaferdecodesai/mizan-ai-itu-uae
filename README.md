# Mizan AI: a policy war-room for public-service AI incidents

**ITU AI for Good Lab Hackathon, United Arab Emirates. Domain: government services.**
Author: Jafer Mohammed, AqionLabs (solo entry) · jaferm@aqionlabs.com

- **Live replay:** https://jaferdecodesai.github.io/mizan-ai-itu-uae/ (GitHub Pages, built from `web/` by `.github/workflows/pages.yml`)
- **Cloudflare mirror:** https://mizan-ai-itu-uae.aqionlabs.workers.dev (single-file Worker with CSP; serving 200 since 10 Nov 2026 – see `deploy/README.md`)
- **Technical report:** [docs/report/Mizan-AI_Technical-Report_AqionLabs.pdf](docs/report/Mizan-AI_Technical-Report_AqionLabs.pdf) (4 pages, official template; editable DOCX alongside)
- **Knowledge base (portable export):** [`kb/export/`](kb/export) (`chunks.jsonl` + `manifest.json`)

Mizan (ميزان, "balance") simulates how a GenAI-powered government e-service and the institutions around it react to an incident. Six **role agents** receive *different* fragments of a synthetic incident at *different* times. Each one assesses the incident within its own mandate, cites UAE documents and global policy examples from a knowledge base built with the **ITU AI Readiness reference code**, and passes typed messages to the others. Only a **human approver** can decide. Every step goes into an append-only, SHA-256 hash-chained audit log, and the web replay renders that log directly and re-verifies the chain in your browser.

> **Honesty labels.** All scenario data is synthetic. Agents play institutional *roles*; they are not the positions of any real UAE entity. **No LLM is used in this build.** No authorised model API key was available on the build machine, so the agents are **deterministic and retrieval-grounded**: hand-written playbook rules decide *when* an agent speaks and the template wording of its claims, and live KB retrieval (BM25 + ChromaDB vectors) decides *which sources* are cited. The "reasoning trace" is a structured record (facts known → rule → retrieval candidates → options → choice), not a model's hidden chain of thought. This is not legal advice. It is not affiliated with or endorsed by ITU or any UAE authority, and it does not use the ITU sandbox.

## What is in the repo

| Path | What |
|---|---|
| `third_party/ITUAIReadiness/` | ITU reference code ([CrashingGuru/ITUAIReadiness](https://github.com/CrashingGuru/ITUAIReadiness) @ `84010da9`, MIT, © 2026 Vishnu Ram OV). Code only; its InputDocs PDFs are not copied. |
| `mizan/kb_build.py` | Builds the KB **through the reference ingestion path**: `server.knowledge.ingest` (`parse_file`/PyMuPDF, `chunk_text`, `build_metadata`) and `server.knowledge.kb.KnowledgeBase` (ChromaDB `kb_main`, cosine). Adds article-level chunking for laws. |
| `mizan/embed.py` | Embeddings: `nomic-embed-text-v1.5` (the reference's model family) on CPU via `fastembed`/ONNX, because Ollama was not available. `MIZAN_EMBED=ollama` switches back to the unmodified reference `embed_texts`. |
| `mizan/retrieval.py`, `mizan/kb_eval.py` | BM25, vector and hybrid (RRF) retrieval, plus a 30-query hit@5 evaluation |
| `mizan/engine.py` | Scenario engine: progressive, uneven, per-role event release with delays; coordinator routing; human DECIDE gate; gap register |
| `mizan/agents.py` | The six role agents (mandate, private feed, KB scope, playbook) |
| `mizan/protocol.py` | Typed messages: `INFORM · REQUEST · ASSESS · PROPOSE · OBJECT · DECIDE` (only `human` may `DECIDE`) |
| `mizan/verify.py` | Citation verifier: `SUPPORTED / WEAK / UNCITED / INVALID` per claim |
| `mizan/audit.py` | Append-only JSONL with a SHA-256 hash chain, plus `verify_chain` |
| `mizan/gaps.py` | Domain-level gap register with UAE mapping status and global examples |
| `scenarios/` | S1 "Overseas inference leak" (with an injectable judge twist) + an example judge injection |
| `runs/` | Audit logs and summaries from the recorded runs (baseline, twist, injected) |
| `kb/` | `sources.json` (inputs), `export/` (chunks + manifest with sha256), `eval/`, `not_ingested.json` |
| `web/` | Static replay (vanilla JS, no build). `deploy/` bundles it into one Cloudflare Worker. |
| `tests/` | pytest: hash-chain tamper detection, protocol gate, verifier, KB integrity, uneven release, twist, injection, and JS/Python hash parity |

## Run it

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python scripts/fetch_sources.py          # official URLs -> kb/raw (some sites need a real browser: see the script)
python -m mizan.kb_build --reset         # parse -> chunk -> embed -> ChromaDB + kb/export
python -m mizan.kb_eval                  # hit@5 evaluation -> kb/eval/RESULTS.md
python -m mizan.cli run --no-twist       # baseline run -> runs/S1-baseline.audit.jsonl
python -m mizan.cli run                  # with judge twist -> runs/S1-twist.audit.jsonl
python -m mizan.cli run --no-twist --inject scenarios/judge_inject_example.json   # a judge's live event
python -m mizan.cli run --interactive    # you are the human approver
python -m mizan.cli verify runs/S1-twist.audit.jsonl
python -m mizan.cli ask "cross-border transfer of personal data" --scope UAE
python -m pytest -q
```
CPU only. The vector build took 387 s for 1,275 chunks on an 8-vCPU box. Without a vector store, retrieval falls back to BM25 over `kb/export/chunks.jsonl`.

## Knowledge base

18 official public documents and **1,275 chunks**. Laws are chunked per article (PDPL, Cybercrime Decree-Law, ICT-in-Health law, EU AI Act articles and annexes, GDPR articles), web pages per section, and PDFs per page with the reference chunker (256 words, 30 overlap). Every chunk carries `chunk_id` (for example `uae-pdpl-2021:art-22`), section, issuer, status, scope (UAE or global), language, date and the official URL. The manifest records the sha256 of the fetched file, whether the document is binding or guidance, and a licence note.

| UAE (10) | Global examples (8) |
|---|---|
| National Strategy for AI 2031 · AI Ethics Principles & Guidelines · Generative AI Guide · UAE Charter for the Development and Use of AI · UAE's International Stance on AI Policy · **Federal Decree-Law 45/2021 (PDPL)** · **Federal Decree-Law 34/2021 (Rumours & Cybercrimes)** · **Federal Law 2/2019 (ICT in Health)** · u.ae data-protection laws page · UAE Digital Government Strategy 2025 | **EU AI Act (Reg. 2024/1689)** · **GDPR (Reg. 2016/679)** · OECD AI Recommendation (2024) · NIST AI RMF 1.0 · NIST AI 600-1 GenAI Profile · Singapore Model AI Governance Framework for GenAI · **ITU-T Y.3172** · ITU AI Ready framework report |

These were **not ingested**, for the reasons listed in `kb/not_ingested.json`: NCEMA 7000 (copyright, consent required), the NIAF (host timed out), the National Cloud Security Policy (no direct URL found), Dubai AI Principles (404) and the TDRA cybersecurity strategy page (no strategy text extracted). Raw PDFs and HTML are **not committed**. Only the extracted chunks are published, with attribution, and the official Arabic legal text prevails over the English translations.

### Retrieval evaluation (real run, `kb/eval/results.json`)
30 queries written by the author, each with a gold document; 19 of them also have a gold article.

| method | doc hit@5 | article hit@5 | doc MRR@5 |
|---|---|---|---|
| BM25 | 30/30 | 19/19 | 0.900 |
| **hybrid (used by agents)** | 29/30 | 19/19 | 0.886 |
| vector (ChromaDB, nomic v1.5) | 28/30 | 19/19 | 0.883 |

Caveat: the queries use the vocabulary of the documents, so these numbers are optimistic. An independent, paraphrased query set is future work. An int8-quantised nomic variant was tried first and scored 6/30 on vectors because its batch embeddings were inconsistent, so it was discarded. That attempt is recorded in `evidence/`.

## Scenario S1: "Overseas inference leak" (synthetic)

| T | Event | Delivered to |
|---|---|---|
| 0 | Baseline: GenAI eligibility assistant, in-country inference, humans approve decisions | all |
| 10 | Latency alert; automatic failover to an endpoint outside the UAE | Service Owner only |
| 18 | Data-flow log: name, ID-format number, income in failover prompts | Data Protection only |
| 25 | 14 complaints about wrong "ineligible" answers | Service Agent (Owner +4 min) |
| 32 | Viral, partly false post ("leaked to hackers") | Cyber only |
| 40 | Vendor keeps failover logs abroad for 30 days; contract silent | Regulator only |
| 48 | **Judge twist**: retrain the model on the leaked logs | Owner, then DP and Adviser (+2) |
| 60 | Decision round → human DECIDE | all |

The Service Owner learns that personal data was in the traffic only through the Data Protection role's `INFORM`, never from the raw log, and a test checks this. The Policy & Legal Adviser reads all inter-agent traffic but none of the private feeds.

**Recorded results** (`runs/*.summary.json`):
- Baseline: 19 messages (9 ASSESS, 6 PROPOSE, 2 INFORM, 1 REQUEST, 1 DECIDE), 31 claims: 22 SUPPORTED, 3 WEAK, 6 INFO. Gaps G1, G2, G3, G5, G6. Chain verified (44 records).
- Judge twist: 22 messages including **2 OBJECTs** (Data Protection: purpose limitation under PDPL Art. 5; Adviser: objective conflict, citing EU AI Act Art. 10 and GDPR Art. 6). The product team's claim "retraining will fix the answers faster" is flagged **UNCITED**. The human rejects `P-retrain`. Gap G4 (objective conflict) appears. Chain verified (51 records).
- Judge injection (`J1`, Arabic-only request): no playbook rule matches, so the Service Agent and the Adviser escalate to the human with the closest KB context (`GENERIC-ESCALATE`). This shows the limit of a rule-based agent.

## Gap register (domain-level; every row needs expert review)
G1 responsibility for notifying residents about AI-output harm that is not a data breach · G2 no public-sector AI incident-reporting standard · G3 automated failover creating a cross-border transfer nobody approved, and vendor contracts that are silent on failover · G4 fixing the model fast vs purpose limitation · G5 crisis communication across counter-misinformation, data protection and the service owner · G6 record-keeping and log retention for government AI agents. Each row stores the UAE probe and its status (*provision found*, *partial match* or *not found in this KB*), the closest UAE chunk, and global examples with verbatim quotes (EU AI Act Art. 12/26/73, GDPR Art. 28/46, NIST AI 600-1, Singapore MGF-GenAI, OECD 1.2/1.3). "Not found in KB" does **not** mean "absent from UAE law".

## Alignment with ITU-T Y.3172 and the ITU AI Readiness Framework
Every message is tagged with the Y.3172 node it acts on and the AI Readiness dimensions it touches. The replay shows both counts.

| Y.3172 | Mizan |
|---|---|
| SRC | Synthetic applications, vendor feeds, official documents |
| C | Intake, plus KB ingestion with the ITU reference parser |
| PP | Article chunking, metadata, PII flags in events |
| M | Service model (simulated); nomic embeddings |
| P | Approval gates, residency rule, "claims must cite" rule |
| D | Typed message bus to the role agents |
| SINK | Human approver, public notice, gap register, audit |
| MLFO | Scenario engine and coordinator |
| ML sandbox | The replay itself: rehearse incidents before go-live |
| ML underlay | In-country vs failover region (where the incident starts) |

Readiness 2.0 dimensions most exercised in S1: D10 AI & Policies, D6 Human Interface, D9 Impacts of Humans in AI Integration, D13 Digital Infrastructure, D2 Generated Content (misinformation), D1 Data/Model Marketplace (the retraining twist).

## Security and privacy of the demo
The site is static, has no API, sets no cookies and collects no input. The Worker sets CSP (`script-src 'self'`), nosniff, HSTS, a referrer policy and a permissions policy. No secrets are in the repo, and a secret scan ran before the push (`evidence/secret_scan.txt`). The scenario uses no real personal data.

## Limitations
Rule-based agents: they do not generalise beyond the playbook, and unscripted events only escalate. There is no LLM, so no LLM evaluation. The KB is incomplete (see above) and English-only. The eval is small and author-written. The gap status heuristic uses term matching. The ITU sandbox was not used.

## Licence and attribution
Mizan code: MIT © 2026 Jafer Mohammed / AqionLabs (`LICENSE`). ITU reference code: MIT © 2026 Vishnu Ram OV (`third_party/ITUAIReadiness/LICENSE`). Fonts: Inter and JetBrains Mono (SIL OFL 1.1). KB chunks are excerpts of official public documents, published with attribution to their issuers; see `kb/export/manifest.json` for per-document licence notes. EUR-Lex content is reused under Decision 2011/833/EU, and NIST publications are US Government works.
