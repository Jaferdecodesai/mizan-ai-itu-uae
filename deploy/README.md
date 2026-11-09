# Deploy

Two deploy targets serve the same static `web/` folder:

1. **GitHub Pages** (primary): `.github/workflows/pages.yml` uploads `web/` on every push to `main`.
   https://jaferdecodesai.github.io/mizan-ai-itu-uae/
2. **Cloudflare Worker** (mirror): `python deploy/make_bundle.py` embeds every file under `web/` into a single
   module Worker (`deploy/dist/worker.js`, with CSP and security headers). `python deploy/make_deploy_js.py <out.js>`
   writes a Cloudflare API program (PUT the script, enable its workers.dev route) that was run through the
   Cloudflare MCP `execute` tool. `deploy/worker.js` is the alternative Workers Static Assets version
   (unused: the assets-upload session returned HTTP 401 for the token available at build time).

Status on 9 Nov 2026 (Dubai, UTC+4): script `mizan-ai-itu-uae` uploaded and deployed at 100%, workers.dev route
enabled, but https://mizan-ai-itu-uae.aqionlabs.workers.dev/ returned `404 error code: 1042`. A fresh one-line
probe Worker (`mizan-probe`) behaved the same, while older Workers on the same account answered 200, so the
problem is with routing for newly created Workers on that account, not with this code.
