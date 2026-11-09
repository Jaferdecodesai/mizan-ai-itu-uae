"""Append-only, SHA-256 hash-chained JSONL audit log.

Each line is a JSON object.  hash = sha256(prev_hash + canonical(record without 'hash')),
canonical = json.dumps(sort_keys=True, separators=(',', ':'), ensure_ascii=False).
The web viewer re-computes the same chain in the browser (SubtleCrypto).
"""
from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone, timedelta
from pathlib import Path

GENESIS = "0" * 64
DUBAI = timezone(timedelta(hours=4))


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _round(o):
    if isinstance(o, float):
        r = round(o, 4)
        return int(r) if r == int(r) else r  # JS-compatible number formatting
    if isinstance(o, dict):
        return {k: _round(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_round(v) for v in o]
    return o


class AuditLog:
    def __init__(self, path: Path, run_id: str, clock=None):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id
        self.seq = 0
        self.prev = GENESIS
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.path.write_text("")  # new run file
        self.records: list[dict] = []

    def append(self, kind: str, agent: str, sim_t: float, payload: dict) -> dict:
        now = self.clock()
        rec = _round({"run_id": self.run_id, "seq": self.seq, "kind": kind, "agent": agent, "sim_t": sim_t,
                      "ts_utc": now.isoformat(timespec="seconds"), "ts_dubai": now.astimezone(DUBAI).isoformat(timespec="seconds"),
                      "payload": payload, "prev_hash": self.prev})
        rec["hash"] = hashlib.sha256((self.prev + canonical(rec)).encode("utf-8")).hexdigest()
        with self.path.open("a", encoding="utf-8") as f:
            f.write(canonical(rec) + "\n")
        self.prev = rec["hash"]
        self.seq += 1
        self.records.append(rec)
        return rec


def verify_chain(path: Path) -> dict:
    prev = GENESIS
    n = 0
    for i, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines()):
        rec = json.loads(line)
        h = rec.pop("hash")
        if rec.get("prev_hash") != prev:
            return {"ok": False, "records": n, "broken_at": i, "reason": "prev_hash mismatch"}
        calc = hashlib.sha256((prev + canonical(rec)).encode("utf-8")).hexdigest()
        if calc != h:
            return {"ok": False, "records": n, "broken_at": i, "reason": "hash mismatch (record altered)"}
        prev = h
        n += 1
    return {"ok": True, "records": n, "head": prev}
