import json, subprocess, shutil
from pathlib import Path
import pytest

from mizan.audit import AuditLog, verify_chain
from mizan.protocol import Message, Claim, Citation, ProtocolError
from mizan.verify import verify_claim
from mizan import retrieval as R

ROOT = Path(__file__).resolve().parent.parent


def test_hash_chain_detects_tampering(tmp_path):
    log = AuditLog(tmp_path / "a.jsonl", "t")
    for i in range(5):
        log.append("message", "x", i, {"n": i, "text": "تجربة – unicode ✓", "f": 0.123456})
    assert verify_chain(tmp_path / "a.jsonl")["ok"]
    lines = (tmp_path / "a.jsonl").read_text().splitlines()
    rec = json.loads(lines[2]); rec["payload"]["n"] = 99; lines[2] = json.dumps(rec)
    (tmp_path / "b.jsonl").write_text("\n".join(lines) + "\n")
    res = verify_chain(tmp_path / "b.jsonl")
    assert not res["ok"] and res["broken_at"] == 2


def test_only_human_can_decide():
    with pytest.raises(ProtocolError):
        Message("M1", 0, "policy_adviser", ["all"], "DECIDE", "x", [Claim("x")]).validate()
    Message("M2", 0, "human", ["all"], "DECIDE", "x", [Claim("ok")]).validate()


def test_unknown_message_type_rejected():
    with pytest.raises(ProtocolError):
        Message("M1", 0, "cyber", ["all"], "ORDER", "x", [Claim("x")]).validate()


def test_verifier_statuses():
    c = R.by_id()["uae-pdpl-2021:art-22"]
    quote = c["text"].split("\n")[0][:80]
    ok = verify_claim(Claim("transfer of personal data outside the State", [Citation(c["chunk_id"], quote)]), {}, True)
    assert ok.status == "SUPPORTED"
    assert verify_claim(Claim("retraining fixes everything", []), {}, True).status == "UNCITED"
    assert verify_claim(Claim("x", [Citation("nope:art-1", "q")]), {}, True).status == "INVALID"
    assert verify_claim(Claim("x", [Citation(c["chunk_id"], "this sentence is not in the law")]), {}, True).status == "INVALID"


def test_kb_export_integrity():
    man = json.loads((ROOT / "kb/export/manifest.json").read_text())
    rows = [json.loads(l) for l in (ROOT / "kb/export/chunks.jsonl").open()]
    assert man["chunks"] == len(rows) and len({r["chunk_id"] for r in rows}) == len(rows)
    assert all(s["sha256"] and s["url"].startswith("https://") for s in man["sources"])
    assert {r["doc_id"] for r in rows} == {s["doc_id"] for s in man["sources"]}


def test_scenario_uneven_release_and_twist(tmp_path):
    from mizan.engine import Run
    sc = json.loads((ROOT / "scenarios/s1_overseas_inference_leak.json").read_text())
    base = Run(sc, "b", tmp_path, twist=False).run()
    tw = Run(sc, "t", tmp_path, twist=True).run()
    assert base["chain"]["ok"] and tw["chain"]["ok"]
    # E2 (data-flow log) is private to the data protection role
    assert [d["to"] for d in base["deliveries"] if d["event"] == "E2"] == ["data_protection"]
    # service owner learns about personal data only via the DP INFORM, not the event
    assert "pii_in_prompts" in base["knowledge_end"]["service_owner"]
    assert "OBJECT" in tw["by_type"] and tw["by_type"]["OBJECT"] >= 2 and base["by_type"]["OBJECT"] == 0
    assert "G4" in tw["gaps"] and "G4" not in base["gaps"]
    assert tw["claim_status"].get("UNCITED", 0) >= 1   # product-team assertion without a source is flagged
    assert tw["by_type"]["DECIDE"] == 1


def test_injected_event_escalates(tmp_path):
    from mizan.engine import Run
    sc = json.loads((ROOT / "scenarios/s1_overseas_inference_leak.json").read_text())
    inj = {"id": "J1", "t": 50, "title": "Judge: ministry asks to switch assistant to Arabic-only", "injected": True,
           "body": "A ministry asks the service to answer only in Arabic from tomorrow.", "deliver": {"service_agent": 0, "policy_adviser": 0}, "facts": ["judge_arabic_only"]}
    s = Run(sc, "j", tmp_path, twist=False, inject=[inj]).run()
    lines = [json.loads(l) for l in (tmp_path / "j.audit.jsonl").open()]
    gen = [l for l in lines if l["kind"] == "message" and l["payload"]["reasoning_trace"]["rule"] == "GENERIC-ESCALATE"]
    assert len(gen) == 2 and s["chain"]["ok"]


def test_js_verifier_matches_python(tmp_path):
    if not shutil.which("node"):
        pytest.skip("node not installed")
    log = AuditLog(tmp_path / "a.jsonl", "t")
    log.append("message", "x", 1.5, {"text": "تجربة – “quotes” \n newline", "n": [1, 2.25, None, True]})
    log.append("gap", "y", 2, {"k": {"b": 1, "a": 2}})
    out = subprocess.run(["node", str(ROOT / "web/verify_node_check.mjs"), str(tmp_path / "a.jsonl")], capture_output=True, text=True)
    assert out.stdout.strip() == "OK 2", out.stdout + out.stderr
