"""Copy recorded runs + KB export + eval into web/data for the static Cloudflare site."""
import shutil
from mizan.refcode import ROOT
D = ROOT / "web" / "data"
(D / "runs").mkdir(parents=True, exist_ok=True); (D / "kb").mkdir(parents=True, exist_ok=True)
for r in ("S1-baseline", "S1-twist"):
    shutil.copy(ROOT / "runs" / f"{r}.audit.jsonl", D / "runs" / f"{r}.audit.jsonl")
    shutil.copy(ROOT / "runs" / f"{r}.summary.json", D / "runs" / f"{r}.summary.json")
shutil.copy(ROOT / "kb/export/chunks.jsonl", D / "kb/chunks.jsonl")
shutil.copy(ROOT / "kb/export/manifest.json", D / "kb/manifest.json")
shutil.copy(ROOT / "kb/eval/results.json", D / "kb/eval.json")
print("web/data updated")
