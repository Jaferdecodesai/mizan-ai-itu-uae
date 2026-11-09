"""Typed inter-agent message protocol."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional

TYPES = ("INFORM", "REQUEST", "ASSESS", "PROPOSE", "OBJECT", "DECIDE")
CLAIM_TYPES = ("ASSESS", "PROPOSE", "OBJECT")  # must carry citations
ROLES = {
    "service_agent": "Service Agent",
    "service_owner": "Service Owner",
    "data_protection": "Data Protection role",
    "regulator": "Digital Gov / Regulator role",
    "cyber": "Cyber Security role",
    "policy_adviser": "Policy & Legal Adviser",
    "human": "Human approver",
}


class ProtocolError(ValueError):
    pass


@dataclass
class Citation:
    chunk_id: str
    quote: str              # verbatim span from the chunk
    doc_id: str = ""
    section: str = ""
    url: str = ""
    kind: str = "kb"        # kb | event


@dataclass
class Claim:
    text: str
    citations: list[Citation] = field(default_factory=list)
    status: str = "unverified"   # SUPPORTED | WEAK | UNCITED | INVALID  (set by verifier)
    note: str = ""


@dataclass
class Message:
    id: str
    t: float
    sender: str
    to: list[str]
    type: str
    subject: str
    claims: list[Claim]
    proposal_id: Optional[str] = None
    refs: list[str] = field(default_factory=list)       # message/event ids this responds to
    confidence: float = 0.5
    readiness_dims: list[int] = field(default_factory=list)
    y3172_node: str = ""

    def validate(self):
        if self.type not in TYPES:
            raise ProtocolError(f"unknown type {self.type}")
        if self.sender not in ROLES:
            raise ProtocolError(f"unknown sender {self.sender}")
        if self.type == "DECIDE" and self.sender != "human":
            raise ProtocolError("only the human approver may DECIDE")
        if self.sender == "human" and self.type != "DECIDE":
            raise ProtocolError("human approver only issues DECIDE in this simulator")
        for r in self.to:
            if r not in ROLES and r != "all":
                raise ProtocolError(f"unknown recipient {r}")
        if not self.claims:
            raise ProtocolError("message without claims")
        return self

    def to_dict(self):
        return asdict(self)
