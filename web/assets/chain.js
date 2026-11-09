// Canonical JSON identical to Python json.dumps(sort_keys=True, separators=(',',':'), ensure_ascii=False)
export function canonical(v) {
  if (v === null || typeof v !== "object") return JSON.stringify(v);
  if (Array.isArray(v)) return "[" + v.map(canonical).join(",") + "]";
  const keys = Object.keys(v).sort();
  return "{" + keys.map(k => JSON.stringify(k) + ":" + canonical(v[k])).join(",") + "}";
}
export async function sha256hex(s, subtle) {
  const buf = await subtle.digest("SHA-256", new TextEncoder().encode(s));
  return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, "0")).join("");
}
export async function verifyChain(lines, subtle) {
  let prev = "0".repeat(64), n = 0;
  for (let i = 0; i < lines.length; i++) {
    const rec = JSON.parse(lines[i]);
    const h = rec.hash; delete rec.hash;
    if (rec.prev_hash !== prev) return { ok: false, records: n, brokenAt: i, reason: "prev_hash mismatch" };
    const calc = await sha256hex(prev + canonical(rec), subtle);
    if (calc !== h) return { ok: false, records: n, brokenAt: i, reason: "hash mismatch (record altered)" };
    prev = h; n++;
  }
  return { ok: true, records: n, head: prev };
}
