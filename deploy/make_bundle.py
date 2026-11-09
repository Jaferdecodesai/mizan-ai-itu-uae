"""Build a single-module Worker that embeds the static site (fallback used because the Workers
static-assets upload endpoint rejected the connector session with 401). Output: deploy/dist/worker.js"""
import base64, hashlib, json, gzip
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
TYPES = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".json": "application/json; charset=utf-8",
         ".jsonl": "application/x-ndjson; charset=utf-8", ".svg": "image/svg+xml", ".woff2": "font/woff2", ".png": "image/png", ".pdf": "application/pdf", ".txt": "text/plain; charset=utf-8"}
files = {}
for p in sorted((ROOT / "web").rglob("*")):
    if not p.is_file() or p.name == "verify_node_check.mjs":
        continue
    raw = p.read_bytes(); ext = p.suffix.lower()
    entry = {"t": TYPES.get(ext, "application/octet-stream"), "e": '"' + hashlib.sha256(raw).hexdigest()[:20] + '"'}
    if ext in (".woff2", ".png", ".pdf"):
        entry["b"] = base64.b64encode(raw).decode()
    else:
        entry["s"] = raw.decode("utf-8")
    files["/" + p.relative_to(ROOT / "web").as_posix()] = entry
src = "const FILES = " + json.dumps(files, ensure_ascii=False) + ";\n" + r'''
const CSP = "default-src 'self'; script-src 'self'; style-src 'self'; style-src-attr 'unsafe-inline'; font-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'none'; object-src 'none'";
const BIN = {};
function body(f) { if (f.s !== undefined) return f.s; if (!BIN[f.e]) { const b = atob(f.b); const u = new Uint8Array(b.length); for (let i = 0; i < b.length; i++) u[i] = b.charCodeAt(i); BIN[f.e] = u; } return BIN[f.e]; }
export default {
  async fetch(request) {
    if (!["GET", "HEAD"].includes(request.method)) return new Response("Method not allowed", { status: 405, headers: { Allow: "GET, HEAD" } });
    let p = new URL(request.url).pathname; if (p.endsWith("/")) p += "index.html";
    let f = FILES[p] || FILES[p + ".html"]; let status = 200;
    if (!f) { f = FILES["/404.html"]; status = 404; }
    const h = new Headers({ "Content-Type": f.t, "ETag": f.e, "Content-Security-Policy": CSP, "X-Content-Type-Options": "nosniff", "Referrer-Policy": "strict-origin-when-cross-origin",
      "Permissions-Policy": "camera=(), microphone=(), geolocation=()", "Cross-Origin-Opener-Policy": "same-origin", "Strict-Transport-Security": "max-age=31536000",
      "Cache-Control": p.startsWith("/assets/fonts/") ? "public, max-age=31536000, immutable" : "public, max-age=300" });
    if (status === 200 && request.headers.get("If-None-Match") === f.e) return new Response(null, { status: 304, headers: h });
    return new Response(request.method === "HEAD" ? null : body(f), { status, headers: h });
  },
};
'''
out = ROOT / "deploy/dist"; out.mkdir(parents=True, exist_ok=True)
(out / "worker.js").write_text(src, encoding="utf-8")
print(len(files), "files", len(src.encode()), "bytes raw", len(gzip.compress(src.encode())), "bytes gzip")
