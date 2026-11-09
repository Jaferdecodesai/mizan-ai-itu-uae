"""Scenario engine: progressive, uneven, per-agent event release + coordinator (MLFO-like) routing."""
from __future__ import annotations
import heapq, json
from dataclasses import asdict
from pathlib import Path

from mizan import retrieval as R
from mizan.agents import ROLES, Q, Rule
from mizan.audit import AuditLog, verify_chain
from mizan.gaps import build_register
from mizan.protocol import Citation, Claim, Message, ROLES as ROLE_NAMES
from mizan.verify import verify_message

ADVISER = "policy_adviser"


class Run:
    def __init__(self, scenario: dict, run_id: str, out_dir: Path, twist: bool = True, inject: list[dict] | None = None,
                 decider=None):
        self.sc = scenario
        self.run_id = run_id
        self.events = [e for e in scenario["events"] if twist or not e.get("twist")] + list(inject or [])
        self.ev = {e["id"]: e for e in self.events}
        self.out = Path(out_dir); self.out.mkdir(parents=True, exist_ok=True)
        self.audit = AuditLog(self.out / f"{run_id}.audit.jsonl", run_id)
        self.facts = {k: set() for k in ROLES}
        self.seen_events = {k: [] for k in ROLES}
        self.fired = {k: set() for k in ROLES}
        self.messages: list[Message] = []
        self.q = []
        self.n = 0
        self.decider = decider
        self.delivered_log = []

    def push(self, t, kind, target, obj):
        heapq.heappush(self.q, (t, self.n, kind, target, obj)); self.n += 1

    # ---------- citations ----------
    def _cite(self, spec, trace):
        if isinstance(spec, tuple) and spec[0] == "event":
            e = self.ev[spec[1]]
            return [Citation(chunk_id=e["id"], quote=e["body"][:160], kind="event", section=e["title"])]
        assert isinstance(spec, Q)
        hits = R.hybrid(spec.query, k=max(3, spec.k), doc_ids=spec.docs)
        trace["retrieval"].append({"query": spec.query, "scope": spec.docs, "candidates": [h.brief() for h in hits]})
        return [Citation(chunk_id=h.chunk_id, quote=R.best_sentence(h.text, spec.query), doc_id=h.doc_id, section=h.section, url=h.url)
                for h in hits[: spec.k]]

    # ---------- agent step ----------
    def fire(self, role_key, rule: Rule, t):
        trace = {"facts_known": sorted(self.facts[role_key]), "events_seen": list(self.seen_events[role_key]), "rule": rule.rid,
                 "rule_condition": {"when": rule.when}, "retrieval": [], "options": rule.options, "choice": rule.choice or rule.subject}
        claims = []
        for text, specs in rule.claims:
            cits = []
            for s in specs:
                cits += self._cite(s, trace)
            claims.append(Claim(text=text, citations=cits))
        to = rule.to
        msg = Message(id=f"M{len(self.messages)+1:02d}", t=t, sender=role_key, to=to, type=rule.type, subject=rule.subject, claims=claims,
                      proposal_id=rule.proposal_id, refs=list(self.seen_events[role_key][-1:]), confidence=rule.confidence,
                      readiness_dims=rule.dims, y3172_node=rule.node).validate()
        verify_message(msg, self.ev)
        self.messages.append(msg)
        self.audit.append("message", role_key, t, {"message": msg.to_dict(), "reasoning_trace": trace,
                                                   "model": "deterministic-rule-engine (no LLM)", "embedding": __import__("mizan.embed", fromlist=["x"]).backend_label()})
        recips = [r for r in ROLES if r != role_key] if "all" in to else [r for r in to if r in ROLES]
        if ADVISER not in recips and role_key != ADVISER:
            recips.append(ADVISER)  # adviser reads all inter-agent traffic
        for r in recips:
            self.push(t + 1, "message", r, msg)

    def evaluate(self, role_key, t):
        for rule in ROLES[role_key].rules:
            if rule.rid in self.fired[role_key]:
                continue
            if set(rule.when) <= self.facts[role_key] and not (set(rule.unless) & self.facts[role_key]):
                self.fired[role_key].add(rule.rid)
                t += 0.5
                self.fire(role_key, rule, t)

    def generic(self, role_key, e, t):
        """Fallback for injected events no rule covers: retrieve from the role's KB scope and escalate."""
        trace = {"facts_known": sorted(self.facts[role_key]), "events_seen": list(self.seen_events[role_key]), "rule": "GENERIC-ESCALATE",
                 "rule_condition": {"when": "no playbook rule matched an injected event"}, "retrieval": [], "options": ["act", "escalate"], "choice": "escalate to human"}
        cits = self._cite(Q(e["body"], ROLES[role_key].kb_scope, 2), trace)
        msg = Message(id=f"M{len(self.messages)+1:02d}", t=t + 0.5, sender=role_key, to=["human", ADVISER] if role_key != ADVISER else ["human"], type="ASSESS",
                      subject=f"Unscripted event {e['id']}: escalate", claims=[
                          Claim(text=f"New event outside my playbook: {e['title']}. Closest KB context attached; a human must decide.", citations=cits)],
                      refs=[e["id"]], confidence=0.3, readiness_dims=[9], y3172_node="MLFO").validate()
        verify_message(msg, self.ev)
        self.messages.append(msg)
        self.audit.append("message", role_key, t + 0.5, {"message": msg.to_dict(), "reasoning_trace": trace, "model": "deterministic-rule-engine (no LLM)"})

    # ---------- main loop ----------
    def run(self):
        self.audit.append("run_start", "engine", 0, {"scenario": self.sc["id"], "title": self.sc["title"], "disclaimer": self.sc["disclaimer"],
                                                     "events": [e["id"] for e in self.events], "roles": {k: v.name for k, v in ROLES.items()},
                                                     "kb": json.loads((R.ROOT / "kb/export/manifest.json").read_text())["chunks"],
                                                     "vector_store": R.vector_available()})
        for e in self.events:
            for role_key, delay in e["deliver"].items():
                self.push(e["t"] + delay, "event", role_key, e)
        while self.q:
            t, _, kind, target, obj = heapq.heappop(self.q)
            if kind == "event":
                self.seen_events[target].append(obj["id"])
                before = set(self.facts[target])
                self.facts[target] |= set(obj["facts"])
                self.delivered_log.append({"t": t, "event": obj["id"], "to": target})
                self.audit.append("event_delivery", target, t, {"event_id": obj["id"], "title": obj["title"], "body": obj["body"], "facts": obj["facts"],
                                                                "private_to": target, "twist": bool(obj.get("twist")), "injected": bool(obj.get("injected"))})
                fired_before = len(self.fired[target])
                self.evaluate(target, t)
                if obj.get("injected") and len(self.fired[target]) == fired_before:
                    self.generic(target, obj, t)
            else:
                msg: Message = obj
                src_rule = next((r for r in ROLES[msg.sender].rules if r.subject == msg.subject), None)
                if src_rule and src_rule.teaches:
                    self.facts[target] |= set(src_rule.teaches)       # explicit information sharing (INFORM)
                if src_rule and target == ADVISER:
                    self.facts[target] |= set(src_rule.when)          # adviser reads all traffic and infers the situation
                self.seen_events[target].append(msg.id)
                self.evaluate(target, t)
        self.decide()
        trig = {e["id"] for e in self.events}
        self.gaps = build_register(trig)
        tlast = max(m.t for m in self.messages) + 2
        for g in self.gaps:
            self.audit.append("gap", ADVISER, tlast, g)
        summary = self.summary()
        self.audit.append("run_end", "engine", tlast + 1, summary)
        summary["chain"] = verify_chain(self.audit.path)
        (self.out / f"{self.run_id}.summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False))
        return summary

    def decide(self):
        props = [m for m in self.messages if m.type == "PROPOSE" and m.proposal_id and m.proposal_id != "P-consolidated"]
        objections = [m for m in self.messages if m.type == "OBJECT"]
        dec = self.sc["human_decisions"]["default"]
        claims, refs = [], []
        for p in props:
            if self.decider:
                ok = self.decider(p, objections)
            else:
                ok = p.proposal_id in dec["approve"] and p.proposal_id not in dec["reject"]
            refs.append(p.id)
            claims.append(Claim(text=f"{'APPROVE' if ok else 'REJECT'} {p.proposal_id} ({p.subject}) proposed by {ROLE_NAMES[p.sender]}",
                                citations=[]))
        claims.append(Claim(text="Rationale: " + dec["rationale"], citations=[]))
        t = max(m.t for m in self.messages) + 1
        msg = Message(id=f"M{len(self.messages)+1:02d}", t=t, sender="human", to=["all"], type="DECIDE", subject="Human decision",
                      claims=claims, refs=refs, confidence=1.0, readiness_dims=[8, 9], y3172_node="SINK").validate()
        verify_message(msg, self.ev)
        self.messages.append(msg)
        self.audit.append("decision", "human", t, {"message": msg.to_dict(), "approver": dec["approver"],
                                                   "mode": "interactive" if self.decider else dec["mode"],
                                                   "objections_on_record": [o.id for o in objections]})

    def summary(self):
        st = {}
        for m in self.messages:
            for c in m.claims:
                st[c.status] = st.get(c.status, 0) + 1
        return {"run_id": self.run_id, "messages": len(self.messages), "by_type": {t: sum(1 for m in self.messages if m.type == t) for t in ("INFORM", "REQUEST", "ASSESS", "PROPOSE", "OBJECT", "DECIDE")},
                "claims": sum(len(m.claims) for m in self.messages), "claim_status": st, "gaps": [g["id"] for g in self.gaps],
                "deliveries": self.delivered_log, "knowledge_end": {k: sorted(v) for k, v in self.facts.items()}}
