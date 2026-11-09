// Mizan AI – static replay site. Serves Workers static assets and adds security headers. No API, no data collection.
const CSP = "default-src 'self'; script-src 'self'; style-src 'self'; style-src-attr 'unsafe-inline'; font-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'none'; object-src 'none'";
export default {
  async fetch(request, env) {
    if (!["GET", "HEAD"].includes(request.method)) return new Response("Method not allowed", { status: 405, headers: { Allow: "GET, HEAD" } });
    const res = await env.ASSETS.fetch(request);
    const h = new Headers(res.headers);
    h.set("Content-Security-Policy", CSP);
    h.set("X-Content-Type-Options", "nosniff");
    h.set("Referrer-Policy", "strict-origin-when-cross-origin");
    h.set("Permissions-Policy", "camera=(), microphone=(), geolocation=(), interest-cohort=()");
    h.set("Cross-Origin-Opener-Policy", "same-origin");
    h.set("Strict-Transport-Security", "max-age=31536000");
    const p = new URL(request.url).pathname;
    if (p.endsWith(".jsonl")) h.set("Content-Type", "application/x-ndjson; charset=utf-8");
    if (p.startsWith("/assets/fonts/")) h.set("Cache-Control", "public, max-age=31536000, immutable");
    return new Response(res.body, { status: res.status, statusText: res.statusText, headers: h });
  },
};
