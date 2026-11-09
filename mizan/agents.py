"""Six role agents – deterministic, retrieval-grounded.

NO LLM is used in the default build (no authorised model key was available on
the build machine).  Each agent = mandate + private information feed + KB scope
+ a playbook of rules.  A rule fires when the facts the agent *knows* match; the
agent then runs a real retrieval query against the KB (hybrid BM25 + ChromaDB
vectors), attaches the top retrieved chunk(s) as citations with a verbatim
quoted span, and emits a typed message from a template.  The reasoning trace
(facts considered -> rule -> retrieval -> options -> choice) is logged.
Templates are written by the author; retrieval results are not hand-picked.
"""
from __future__ import annotations
from dataclasses import dataclass, field

UAE_ALL = ["uae-ai-strategy-2031", "uae-ai-ethics", "uae-genai-guide", "uae-ai-charter", "uae-ai-intl-stance", "uae-pdpl-2021",
           "uae-cybercrime-2021", "uae-ict-health-2019", "uae-data-protection-portal", "uae-digital-gov-2025"]
GLOBAL = ["eu-ai-act-2024", "eu-gdpr-2016", "oecd-ai-principles", "nist-ai-rmf-1", "nist-ai-600-1", "sg-genai-mgf-2024", "itu-t-y3172", "itu-ai-ready-2025"]


@dataclass
class Q:
    """A retrieval-backed citation request."""
    query: str
    docs: list[str]
    k: int = 1


@dataclass
class Rule:
    rid: str
    when: list[str]                 # all facts required
    unless: list[str] = field(default_factory=list)
    type: str = "ASSESS"
    to: list[str] = field(default_factory=lambda: ["all"])
    subject: str = ""
    claims: list[tuple[str, list]] = field(default_factory=list)   # (claim text, [Q | ("event", id)])
    proposal_id: str | None = None
    options: list[str] = field(default_factory=list)
    choice: str = ""
    teaches: list[str] = field(default_factory=list)  # facts passed to recipients (INFORM)
    dims: list[int] = field(default_factory=list)
    node: str = ""
    confidence: float = 0.6


@dataclass
class Role:
    key: str
    name: str
    mandate: str
    feed: str
    kb_scope: list[str]
    rules: list[Rule]


ROLES: dict[str, Role] = {}


def role(r: Role):
    ROLES[r.key] = r


role(Role("service_agent", "Service Agent", "Answer residents about the e-service within approved policy; never decide eligibility.",
          "resident conversations, answer-quality monitor", ["uae-ai-charter", "uae-ai-ethics", "uae-genai-guide"], [
    Rule("SA-1", ["wrong_answers"], type="ASSESS", subject="Answer quality degraded since failover",
         claims=[("Since the failover the assistant has given eligibility answers that contradict the published criteria, so its autonomous answers are no longer within approved behaviour.", [("event", "E3")]),
                 ("Human judgement and oversight must be able to correct AI errors, so autonomous answering should stop until quality is restored.", [Q("human oversight over AI correct errors or biases", ["uae-ai-charter", "uae-ai-ethics"])])],
         dims=[6, 9], node="SINK", confidence=0.8),
    Rule("SA-2", ["wrong_answers"], type="PROPOSE", to=["service_owner", "policy_adviser"], subject="Suspend autonomous eligibility answers",
         proposal_id="P-suspend-autonomy",
         claims=[("Proposal: switch the assistant to safe mode – no eligibility verdicts, hand every eligibility question to a human caseworker and show residents a plain-language notice.", [Q("human oversight and accountability for AI systems serving the public, ability to intervene", ["uae-ai-charter", "uae-ai-ethics", "uae-genai-guide"])])],
         options=["keep answering (rejected: known wrong answers)", "safe mode + human handoff", "take service offline (rejected: blocks access)"],
         choice="safe mode + human handoff", dims=[5, 6, 9], node="P", confidence=0.75),
    Rule("SA-3", ["decision_round"], type="ASSESS", subject="Residents affected need correction",
         claims=[("Residents who received a wrong 'ineligible' answer should be contacted with a correction; the assistant cannot do this itself without an approved message.", [Q("transparency inform people affected by AI decisions accountability", ["uae-ai-ethics", "uae-ai-charter"])])],
         dims=[11, 6], node="SINK", confidence=0.6),
]))

role(Role("service_owner", "Service Owner", "Keep the e-service running and accountable; owns the vendor relationship.",
          "ops telemetry, complaint queue", ["uae-digital-gov-2025", "uae-ai-strategy-2031", "uae-genai-guide"], [
    Rule("SO-1", ["failover_foreign"], type="ASSESS", subject="Latency incident with overseas failover",
         claims=[("Automatic failover moved inference to an endpoint outside the UAE; I do not yet know what data was in the traffic.", [("event", "E1")]),
                 ("Digital government services are expected to be reliable and secure, so availability fixes must not silently change where data is processed.", [Q("digital government services secure reliable infrastructure", ["uae-digital-gov-2025"])])],
         dims=[13, 5], node="MLFO", confidence=0.6),
    Rule("SO-2", ["failover_foreign"], type="REQUEST", to=["data_protection"], subject="Did personal data reach the failover?",
         claims=[("Request: confirm whether personal data was sent to fx-west-2 and whether any duty is triggered.", [("event", "E1")])], dims=[10], node="MLFO"),
    Rule("SO-3", ["failover_foreign", "pii_in_prompts"], type="PROPOSE", to=["all"], subject="Fail back to in-country inference",
         proposal_id="P-fail-back",
         claims=[("Proposal: disable cross-border failover and fail back to the in-country region, accepting higher latency, until a compliant secondary region exists.", [Q("cross-border transfer of personal data outside the State", ["uae-pdpl-2021"]), ("event", "E2")])],
         options=["keep overseas failover (rejected)", "fail back in-country, degraded latency", "pause service"], choice="fail back in-country, degraded latency",
         dims=[13, 10], node="D", confidence=0.8),
    Rule("SO-4", ["retrain_request"], type="PROPOSE", to=["all"], subject="Fine-tune on failover logs to fix answers",
         proposal_id="P-retrain",
         claims=[("Proposal (from product team): fine-tune the model on the 30-day failover logs to correct the wrong eligibility answers.", [("event", "E6")]),
                 ("Retraining on these logs will fix the wrong answers faster than any other option.", []),
                 ("National AI ambitions favour rapid improvement of government AI services.", [Q("AI in government services objectives", ["uae-ai-strategy-2031"])])],
         options=["retrain on incident logs", "retrain on synthetic/consented data", "rule-based guardrail on criteria"], choice="retrain on incident logs (product team preference)",
         dims=[1, 7], node="M", confidence=0.5),
    Rule("SO-5", ["vendor_retention"], type="PROPOSE", to=["regulator", "data_protection"], subject="Demand vendor deletion and contract fix",
         proposal_id="P-vendor-deletion",
         claims=[("Proposal: require the vendor to delete the overseas failover logs with a certificate, and amend the contract to name every processing and failover region and retention period.", [Q("processor shall process only on documented instructions contract sub-processor deletion", ["eu-gdpr-2016"]), ("event", "E5")])],
         dims=[10, 13], node="SRC", confidence=0.7),
]))

role(Role("data_protection", "Data Protection role", "Assess personal-data processing against the PDPL; advise on notification.",
          "data-flow logs (delayed), DPO case file", ["uae-pdpl-2021", "uae-data-protection-portal"], [
    Rule("DP-1", ["pii_in_prompts"], type="ASSESS", subject="Possible unauthorised cross-border transfer",
         claims=[("Prompts with identity and income data reached an endpoint outside the UAE: this is a cross-border transfer of personal data.", [("event", "E2"), Q("transfer personal data outside the State proper protection level", ["uae-pdpl-2021"])]),
                 ("If the transfer affected privacy, confidentiality or security of the data, the controller's breach-notification duty must be assessed.", [Q("controller notify the Bureau breach of personal data privacy confidentiality security", ["uae-pdpl-2021"])])],
         dims=[10], node="SRC", confidence=0.75),
    Rule("DP-2", ["pii_in_prompts"], type="INFORM", to=["service_owner", "policy_adviser"], subject="Personal data was in failover traffic",
         claims=[("The failover traffic contained personal data (name, ID-format number, income).", [("event", "E2")])], teaches=["pii_in_prompts"], dims=[10], node="C"),
    Rule("DP-3", ["pii_in_prompts"], type="PROPOSE", to=["all"], subject="Preserve evidence and run notification assessment",
         proposal_id="P-preserve-notify",
         claims=[("Proposal: preserve logs for investigation only, document the incident, and complete a notification assessment within the legal timeline.", [Q("notify breach investigation results within the period", ["uae-pdpl-2021"]), Q("security of personal data appropriate technical and organisational measures", ["uae-pdpl-2021"])])],
         dims=[10, 9], node="P", confidence=0.7),
    Rule("DP-4", ["retrain_request"], type="OBJECT", to=["service_owner", "all"], subject="Retraining is a new purpose",
         claims=[("Using incident logs to fine-tune a model is a new processing purpose that the residents did not provide the data for.", [Q("personal data collected for a specific and clear purpose not processed incompatible", ["uae-pdpl-2021"])])],
         dims=[10, 1], node="M", confidence=0.8),
]))

role(Role("regulator", "Digital Gov / Regulator role", "Oversee government digital platforms, cloud and vendor governance.",
          "platform and vendor notices", ["uae-digital-gov-2025", "uae-ai-charter", "uae-ai-intl-stance", "uae-ai-strategy-2031"], [
    Rule("RG-1", ["vendor_retention"], type="ASSESS", subject="Vendor retention abroad; contract silent",
         claims=[("The vendor keeps 30 days of request logs abroad and the contract does not cover failover location or retention.", [("event", "E5")]),
                 ("Governance and accountability expectations for AI apply to the whole supply chain, including failover infrastructure.", [Q("governance and accountability AI ethical transparent", ["uae-ai-charter"])])],
         dims=[10, 13], node="ML-underlay", confidence=0.65),
    Rule("RG-2", ["vendor_retention"], type="INFORM", to=["data_protection", "service_owner", "policy_adviser"], subject="Vendor retention facts",
         claims=[("Vendor confirms 30-day overseas retention of failover logs.", [("event", "E5")])], teaches=["vendor_retention"], dims=[10], node="SRC"),
]))

role(Role("cyber", "Cyber Security role", "Assess threats and information-integrity risk; coordinate with competent authorities.",
          "threat intel, social listening", ["uae-cybercrime-2021"], [
    Rule("CY-1", ["misinfo"], type="ASSESS", subject="Viral post is partly false",
         claims=[("There is no evidence of public exposure or third-party access, but the cross-border routing did happen – the post mixes a true fact with a false claim.", [("event", "E4")]),
                 ("Spreading false news is addressed by criminal law; any enforcement is for the competent authorities, not for agents in this service.", [Q("spreading rumours and false news information network", ["uae-cybercrime-2021"])])],
         dims=[2, 10], node="SINK", confidence=0.65),
    Rule("CY-2", ["misinfo"], type="PROPOSE", to=["all"], subject="Factual public notice, no takedown by agents",
         proposal_id="P-public-notice",
         claims=[("Proposal: the service owner publishes a factual notice; agents do not request takedowns or label individuals.", [("event", "E4")])],
         options=["silence", "factual notice", "takedown requests"], choice="factual notice", dims=[2, 6], node="SINK", confidence=0.6),
]))

role(Role("policy_adviser", "Policy & Legal Adviser", "Map each position to UAE documents and to global examples; surface gaps. Advisory only.",
          "all inter-agent messages (read-only), whole KB", UAE_ALL + GLOBAL, [
    Rule("PA-1", ["pii_in_prompts"], type="ASSESS", subject="Mapping: cross-border transfer",
         claims=[("UAE mapping: cross-border transfer requires an adequate protection level or another lawful basis.", [Q("transfer personal data outside the State legislation protection", ["uae-pdpl-2021"])]),
                 ("Global example: transfers to third countries rely on adequacy decisions or appropriate safeguards.", [Q("transfer to a third country adequacy decision appropriate safeguards", ["eu-gdpr-2016"], 2)])],
         dims=[10, 3], node="P", confidence=0.7),
    Rule("PA-2", ["wrong_answers"], type="ASSESS", subject="Mapping: AI in public-benefit eligibility",
         claims=[("Global example: AI used by public authorities to evaluate eligibility for public assistance benefits is treated as high-risk and needs human oversight.", [Q("high-risk AI systems used by public authorities to evaluate eligibility for essential public assistance benefits and services", ["eu-ai-act-2024"]), Q("human oversight high-risk AI natural persons intervene stop", ["eu-ai-act-2024"])]),
                 ("UAE mapping: the right to object to decisions based solely on automated processing applies if the assistant's output became a decision.", [Q("objecting to decisions based on automated processing profiling", ["uae-pdpl-2021"])])],
         dims=[5, 6, 10], node="P", confidence=0.65),
    Rule("PA-3", ["retrain_request"], type="OBJECT", to=["all"], subject="Objective conflict: innovation vs purpose limitation",
         claims=[("UAE mapping: the request conflicts with purpose limitation for personal data.", [Q("personal data collected for a specific and clear purpose not processed incompatible", ["uae-pdpl-2021"])]),
                 ("Global example: training data for high-risk AI must follow data-governance practices, and further processing needs compatibility with the original purpose.", [Q("training validation testing data sets data governance management practices", ["eu-ai-act-2024"]), Q("processing for a purpose other than that for which the personal data have been collected compatible", ["eu-gdpr-2016"])])],
         dims=[10, 1, 7], node="M", confidence=0.75),
    Rule("PA-4", ["misinfo"], type="ASSESS", subject="Mapping: public communication during an AI incident",
         claims=[("Global example: transparency and responsible disclosure about AI systems help people understand and challenge outcomes.", [Q("transparency responsible disclosure AI systems people understand challenge outcome", ["oecd-ai-principles"])])],
         dims=[2, 6], node="SINK", confidence=0.55),
    Rule("PA-5", ["decision_round"], type="PROPOSE", to=["human"], subject="Consolidated options for the human approver",
         proposal_id="P-consolidated",
         claims=[("Recommended package for decision: fail back in-country, keep safe mode with human handling, preserve logs and complete the notification assessment, publish a factual notice that discloses the transfer, require vendor deletion.", [Q("human oversight accountability AI incident", ["uae-ai-charter"]), Q("serious incident reporting providers market surveillance", ["eu-ai-act-2024"])])],
         dims=[8, 9, 10], node="MLFO", confidence=0.6),
]))
