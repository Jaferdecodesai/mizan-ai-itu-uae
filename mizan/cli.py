"""Mizan AI command line.

  python -m mizan.cli run   [--scenario scenarios/s1_overseas_inference_leak.json] [--no-twist] [--inject event.json] [--interactive] [--out runs]
  python -m mizan.cli verify runs/S1-twist.audit.jsonl
  python -m mizan.cli ask "question" [--scope UAE|global] [-k 5]
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path


def main(argv=None):
    ap = argparse.ArgumentParser(prog="mizan")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run"); r.add_argument("--scenario", default="scenarios/s1_overseas_inference_leak.json")
    r.add_argument("--no-twist", action="store_true"); r.add_argument("--inject", action="append", default=[])
    r.add_argument("--interactive", action="store_true"); r.add_argument("--out", default="runs"); r.add_argument("--run-id")
    v = sub.add_parser("verify"); v.add_argument("path")
    a = sub.add_parser("ask"); a.add_argument("question"); a.add_argument("--scope"); a.add_argument("-k", type=int, default=5)
    args = ap.parse_args(argv)
    if args.cmd == "verify":
        from mizan.audit import verify_chain
        res = verify_chain(Path(args.path)); print(json.dumps(res, indent=1)); return 0 if res["ok"] else 1
    if args.cmd == "ask":
        from mizan import retrieval as R
        for h in R.hybrid(args.question, args.k, scope=args.scope):
            print(f"[{h.chunk_id}] {h.title} – {h.section}  ({h.method} {h.score:.4f})\n    {R.best_sentence(h.text, args.question)}\n    {h.url}")
        return 0
    from mizan.engine import Run
    sc = json.loads(Path(args.scenario).read_text())
    inject = []
    for p in args.inject:
        e = json.loads(Path(p).read_text()); e["injected"] = True; inject.append(e)
    decider = None
    if args.interactive:
        def decider(p, objs):
            print(f"\n{p.id} {p.proposal_id}: {p.subject}\n  " + "\n  ".join(c.text + f"  [{c.status}]" for c in p.claims))
            for o in objs: print(f"  objection {o.id} by {o.sender}: {o.subject}")
            return input("Approve? [y/N] ").strip().lower() == "y"
    rid = args.run_id or f"{sc['id']}-{'baseline' if args.no_twist else 'twist'}{'-injected' if inject else ''}"
    s = Run(sc, rid, Path(args.out), twist=not args.no_twist, inject=inject, decider=decider).run()
    print(json.dumps({k: s[k] for k in ("run_id", "messages", "by_type", "claims", "claim_status", "gaps", "chain")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
