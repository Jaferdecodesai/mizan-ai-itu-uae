"""Fill the official ITU AI for Good Sandbox Hackathon template with the Mizan AI technical report.
Run: python docs/report/build_report.py <template.docx> <out.docx>
Every number here comes from files in this repo (runs/*.summary.json, kb/eval/RESULTS.md, kb/export/manifest.json)."""
import copy, sys
import docx
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

TPL, OUT = sys.argv[1], sys.argv[2]
REPO = "https://github.com/Jaferdecodesai/mizan-ai-itu-uae"
DEMO = "https://jaferdecodesai.github.io/mizan-ai-itu-uae/"
CF = sys.argv[3] if len(sys.argv) > 3 else ""
BODY_PT, TABLE_PT = 10, 8

d = docx.Document(TPL)
P = d.paragraphs
body = d.element.body

def set_text(p, text, bold=False, size=None):
    for r in p.runs[1:]:
        r._element.getparent().remove(r._element)
    if not p.runs:
        p.add_run("")
    r = p.runs[0]; r.text = text; r.bold = bold or r.bold
    for el in list(r._element):
        if el.tag.endswith('}br'): r._element.remove(el)
    if size: r.font.size = Pt(size)
    return p

proto = copy.deepcopy(P[6]._element)  # a justified Normal body paragraph from the template

def new_par(after_el, parts, size=BODY_PT, space_after=4):
    el = copy.deepcopy(proto)
    for r in el.findall('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r'):
        el.remove(r)
    after_el.addnext(el)
    p = docx.text.paragraph.Paragraph(el, P[6]._parent)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.0
    if isinstance(parts, str): parts = [parts]
    for part in parts:
        b = isinstance(part, tuple)
        t = part[0] if b else part
        r = p.add_run(t); r.font.size = Pt(size); r.bold = b
    return el

# --- header block ---
set_text(P[0], "AI for Good Sandbox Hackathon – AqionLabs – Mizan AI: a multi-agent policy war-room for public-service AI incidents")
set_text(P[1], "Team leader: Jafer Mohammed, AqionLabs (solo founder; solo entry)", size=BODY_PT)
set_text(P[2], "Team members: none.  Contact details: jaferm@aqionlabs.com", size=BODY_PT)
links = f"Github link: {REPO}  ·  Live replay: {DEMO}" + (f"  ·  Mirror: {CF}" if CF else "") + "  ·  Knowledge base: " + REPO + "/tree/main/kb/export (manifest.json, chunks.jsonl)"
set_text(P[3], f"Github link: {REPO}", size=BODY_PT); P[3].alignment = WD_ALIGN_PARAGRAPH.LEFT
_last = P[3]._element
for _line in [f"Live replay: {DEMO}"] + ([f"Mirror (Cloudflare): {CF}"] if CF else []) + [f"Knowledge base: {REPO}/tree/main/kb/export (manifest.json, chunks.jsonl)"]:
    _el = copy.deepcopy(P[3]._element); _last.addnext(_el); _last = _el
    _p = docx.text.paragraph.Paragraph(_el, P[3]._parent)
    for _r in _p.runs[1:]: _r._element.getparent().remove(_r._element)
    _p.runs[0].text = _line

heads = {5: "a", 8: "b", 12: "c", 14: "d", 17: "g", 27: "h"}
for i in heads:
    for r in P[i].runs: r.bold = True; r.font.size = Pt(11)
    P[i].paragraph_format.space_after = Pt(2); P[i].paragraph_format.space_before = Pt(6)

# drop template sample/NOTE paragraphs (keep header, headings, and the table)
drop = [4, 6, 7, 9, 10, 11, 13, 15, 16, 18, 19, 20, 21, 22, 23, 24, 25, 26]
anchors = {i: P[i]._element for i in heads}
for i in drop:
    P[i]._element.getparent().remove(P[i]._element)

def section(anchor, paras):
    last = anchor
    for parts in paras:
        last = new_par(last, parts)
    return last

# a. Introduction
section(anchors[5], [
 [("(a) "), "Mizan AI rehearses how government roles respond when a public-service AI system fails. Six role agents (Service Agent, Service Owner, Data Protection, Digital Government/Regulator, Cyber Security, Policy Adviser) each receive ",
  ("different fragments of a synthetic incident at different times"), ". They exchange typed messages – INFORM, REQUEST, ASSESS, PROPOSE, OBJECT – and every claim must cite either an event the agent has actually seen or a chunk of the policy knowledge base. Only a human approver may DECIDE. Every delivery, message, gap and decision is written to a SHA-256 hash-chained JSONL audit log that anyone can re-verify, including in the browser."],
 ["The knowledge base was built with the ITU reference ingestion code (CrashingGuru/ITUAIReadiness, commit 84010da9, MIT): its parser, 256/30 chunker, metadata builder and ChromaDB store, plus article-level chunking we added for laws. It holds 18 official public documents (10 UAE, 8 global) in 1,275 chunks. The solution is mapped to the ITU-T Y.3172 pipeline and to the 13 dimensions of the ITU AI Readiness framework. ",
  ("Honest scope: "), "agents are deterministic, retrieval-grounded rule engines (no LLM in this build); all incident data is synthetic; agents play institutional roles, not the positions of any real UAE entity; nothing here is legal advice; the solution has not been used in the ITU sandbox."],
])

# b. Description
section(anchors[8], [
 [("(b) Use case – Government services. "), "A GenAI eligibility assistant answers residents' questions on a benefit e-service (synthetic: about 12,000 applications per week; caseworkers approve every decision). Incidents in such services are rarely one-dimensional: the operations team sees a latency failover, the data-protection officer sees a log sample, the contact centre sees complaints, cyber sees a viral post and procurement sees a vendor notice. ",
  ("Gap in existing practice: "), "playbooks and tabletop exercises are usually written per function and assume everyone sees the same facts at the same time. Nobody owns the joined-up picture, decisions are taken from partial facts, and the paper trail is reconstructed afterwards."],
 ["Mizan addresses this by (1) uneven, progressive release of facts so the exercise reproduces partial knowledge; (2) a protocol that forces each claim to carry a citation that a verifier checks against the KB text (SUPPORTED / WEAK / UNCITED / INVALID; INFO for event-sourced statements); (3) a gap register that records where the UAE corpus has no clear provision and attaches global examples; (4) a human DECIDE gate; and (5) a tamper-evident log that turns the exercise into evidence. Judges can inject a new event (CLI --inject) and replay with or without the scripted twist."],
])

# c. Requirements
section(anchors[12], [
 [("(c) "), "Requirements per Y.3172 node, as implemented and checked by the 8 automated tests (all passing):"],
 [("SRC – "), "personal data entering the pipeline must be identified (Emirates-ID-format numbers, income) and its location known; ",
  ("C – "), "the collector/router must not move data across borders without an approved basis; ",
  ("PP – "), "logs may be kept for investigation only; ",
  ("M – "), "training data must have a lawful, compatible purpose (the judge twist tests this); ",
  ("P – "), "eligibility outputs need human oversight and a safe mode; ",
  ("D – "), "failover endpoints must be in-country or contractually covered; ",
  ("SINK – "), "residents and the public must receive accurate, correcting notices; ",
  ("MLFO – "), "the orchestrator must keep a complete, verifiable decision record."],
 ["System requirements: every non-INFO claim cites evidence; only the human role may DECIDE (enforced in protocol.Message.validate); unscripted events must be escalated, not improvised; the audit chain must verify identically in Python and JavaScript (parity test)."],
])

# d/e/f mapping: lead paragraph before the table
lead = section(anchors[14], [
 [("(d) Y.3172, (e) AI Readiness 2.0 and (f) local policies. "), "The table maps each pipeline node of the scenario to the readiness dimensions the agents tag on their messages and to the KB provisions they actually cited in the recorded run (chunk IDs in the repository)."],
])
t = d.tables[0]
rows = [
 ("", "Use case (government benefit e-service)", "AI Readiness 2.0 dimension", "Documents cited (KB chunk)"),
 ("SRC", "Resident prompts with name, ID-format number, income", "Data/Model Marketplace; AI & Policies", "UAE PDPL 45/2021 Art. 22 (cross-border); EU GDPR Art. 45/49; GDPR Art. 28 (processors)"),
 ("C", "Platform router with automatic failover to fx-west-2 (outside UAE)", "Digital Infrastructure", "PDPL Art. 22; UAE Digital Government Strategy (reliable, secure services)"),
 ("PP", "Prompt logs kept 30 days by the vendor abroad", "AI & Policies", "PDPL Art. 9 and 20 (breach notification, controller duties); EU AI Act Art. 12 (record-keeping)"),
 ("M", "GenAI eligibility model; request to fine-tune on incident logs", "Strategy Alignment; AI & Policies", "PDPL Art. 5 (purpose limitation); EU AI Act Art. 10; GDPR Art. 6(4); UAE AI Strategy 2031 p.10"),
 ("P", "Eligibility answers to residents, reviewed by caseworkers", "Human Interface; Impacts of Humans in AI", "UAE AI Charter (human oversight); PDPL Art. 18 (automated decisions); EU AI Act Annex III(5), Art. 14"),
 ("D", "Inference in-country region; secondary region abroad", "Digital Infrastructure", "PDPL Art. 22; GDPR Art. 46 (safeguards)"),
 ("SINK", "Residents, contact centre, public channels (viral post)", "Collaboration with AI; AI for Inclusion", "UAE Cybercrime Law 34/2021 Art. 52; OECD AI Principle 1.3; UAE AI Ethics p.11"),
]
for r_i, row in enumerate(rows):
    for c_i, txt in enumerate(row):
        cell = t.rows[r_i].cells[c_i]
        ps = cell.paragraphs
        for extra in ps[1:]: extra._element.getparent().remove(extra._element)
        p = ps[0]
        for r in p.runs[1:]: r._element.getparent().remove(r._element)
        if not p.runs: p.add_run("")
        p.runs[0].text = txt; p.runs[0].font.size = Pt(TABLE_PT); p.runs[0].font.name = 'Times New Roman'; p.runs[0].bold = (r_i == 0 or c_i == 0)
        p.paragraph_format.space_after = Pt(0); p.paragraph_format.line_spacing = 1.0
# paragraph after the table
after_t = new_par(t._element, [("KB quality. "), "18 documents, 1,275 chunks (UAE laws and EU acts chunked per article; OECD per principle; PDFs per page), embedded with nomic-embed-text-v1.5 into ChromaDB, with a portable JSONL export and a per-document manifest (issuer, date, binding or guidance, URL, language, licence, SHA-256). On 30 hand-written queries (gold document for all 30, gold article for 19) hit@5 was: BM25 30/30 (MRR 0.90), hybrid 29/30 (0.886), vector 28/30 (0.883); section hit@5 was 19/19 for all three. The single hybrid miss was a GenAI-guide query that returned NIST and Singapore pages. Caveat: queries and gold labels were written by the author, so this is a sanity check, not a benchmark. Five relevant sources could not be ingested (e.g. NCEMA 7000, NIAF, Dubai AI Principles: timeouts, 404s or no stable official text) and are listed in kb/not_ingested.json."], space_after=2)

# g. scenarios
section(anchors[17], [
 [("(g) Scenario S1 – overseas inference leak (synthetic). "), "E0 baseline (all roles, T+0) → E1 latency failover to fx-west-2 (Service Owner only, T+10) → E2 log sample shows ID and income in prompts (Data Protection, T+18) → E3 14 complaints of wrong ‘ineligible’ answers (Service Agent T+25, Service Owner T+29) → E4 viral post, about 12,000 shares, claims an ID leak to hackers (Cyber, T+32) → E5 vendor keeps logs 30 days abroad; contract silent (Regulator, T+40) → E6 judge twist: retrain on those logs (T+48–50) → E7 decision round (T+60)."],
 [("Recorded result (twist run). "), "22 messages (9 ASSESS, 7 PROPOSE, 2 OBJECT, 2 INFORM, 1 REQUEST, 1 human DECIDE); 38 claims: 27 SUPPORTED, 3 WEAK, 1 UNCITED, 7 INFO; 6 gaps; 51 audit records, chain verified (head c289efff…). The human approved fail-back in-country, safe mode with caseworker handling, evidence preservation plus a notification assessment, a factual public notice (agents do not request takedowns), and vendor deletion plus a contract fix; and ",
  ("rejected"), " retraining on the incident logs after OBJECT messages from Data Protection and the Policy Adviser (PDPL Art. 5 purpose limitation; EU AI Act Art. 10 and GDPR Art. 6(4) as global examples). The baseline run without the twist gave 19 messages, 22 SUPPORTED / 3 WEAK / 6 INFO and 5 gaps."],
 [("Where it does not work – shown on purpose. "), "(1) The product team's claim “retraining will fix the wrong answers faster than any other option” has no evidence; the verifier marks it UNCITED and it is shown in red rather than hidden. (2) Three proposals are WEAK: the citation is relevant but the quote shares fewer than two key terms with the claim. (3) Judge injection J1 (“answer residents only in Arabic from tomorrow”) is outside every role's playbook: the Service Agent and Policy Adviser post ‘GENERIC-ESCALATE’ messages with the closest KB context and hand it to the human – they do not invent a legal position. A rule-based agent cannot reason about genuinely new situations; an LLM layer would be needed and would have to pass the same citation verifier. (4) The controversy in E4/E6: innovation pressure (AI Strategy 2031) versus purpose limitation, and correcting misinformation versus over-reach (the Cyber role cites the Cybercrime law but leaves enforcement to the competent authorities)."],
])

# h. gaps (table built from a copy of the template table)
gl = section(anchors[27], [
 [("(h) "), "Gaps come from mapping the incident to this KB. “Not found in KB” means not found in this corpus, not that no law exists; every row is flagged for expert review."],
])
gt = copy.deepcopy(t._element)
gl.addnext(gt)
gtab = docx.table.Table(gt, t._parent)
grows = [
 ("ID", "Gap (type)", "UAE mapping in this KB", "Global examples (KB chunk)"),
 ("G1", "Who notifies residents when a public-service AI agent gives wrong answers? (responsibility)", "Partial: AI Ethics guidelines p.15 (‘could consider informing’ – guidance, not a duty)", "EU AI Act Art. 26 (deployers), Art. 73 (serious incidents)"),
 ("G2", "No AI-incident reporting standard for public-sector GenAI (standard)", "Partial: AI Ethics p.17", "EU AI Act Art. 73; NIST AI 600-1 p.56; Singapore GenAI framework p.15"),
 ("G3", "Automatic failover can create a cross-border transfer nobody approved (technology / legislative)", "Not found: PDPL Art. 22 covers transfers, not automated failover", "GDPR Art. 28 (processor contracts), Art. 46 (safeguards)"),
 ("G4", "Fixing the model fast vs purpose limitation (objective conflict; twist only)", "Provision found: AI Ethics p.22; PDPL Art. 5", "EU AI Act Art. 10; GDPR Art. 6(4); OECD Principle 1.2"),
 ("G5", "Crisis communication about a government AI incident (coordination)", "Partial: AI Strategy 2031 p.22", "NIST AI 600-1 p.13; OECD Principle 1.3"),
 ("G6", "Record-keeping and log retention for government AI agents (standard)", "Partial: UAE GenAI Guide p.107", "EU AI Act Art. 12; NIST AI RMF 1.0 p.21"),
]
while len(gtab.rows) > len(grows):
    gtab._tbl.remove(gtab.rows[-1]._tr)
for r_i, row in enumerate(grows):
    for c_i, txt in enumerate(row):
        p = gtab.rows[r_i].cells[c_i].paragraphs[0]
        for extra in gtab.rows[r_i].cells[c_i].paragraphs[1:]: extra._element.getparent().remove(extra._element)
        for r in p.runs[1:]: r._element.getparent().remove(r._element)
        if not p.runs: p.add_run("")
        p.runs[0].text = txt; p.runs[0].font.size = Pt(TABLE_PT); p.runs[0].font.name = 'Times New Roman'; p.runs[0].bold = (r_i == 0 or c_i == 0)
gp = new_par(gt, [("Limitations and next steps. "), "One scenario family; deterministic agents; English-only KB (Arabic originals are authoritative for UAE law); author-written eval; the gap register needs review by UAE legal experts. Next: an LLM layer behind the same citation verifier, Arabic ingestion, more scenarios (health, transport), and inviting regulators to red-team the gap register. Reproduce: pip install -r requirements.txt; python scripts/fetch_sources.py; python -m mizan.kb_build --reset; python -m mizan.kb_eval; python -m mizan.cli run; python -m mizan.cli verify runs/S1-twist.audit.jsonl; python -m pytest -q."], space_after=0)
d.save(OUT)
print("saved", OUT)
