"""Fetch every KB source in kb/sources.json from its official public URL into kb/raw/.

Plain HTTPS first (curl-like). Some official sites (uaelegislation.gov.ae, EUR-Lex)
reject non-browser clients with 403/202; for those, use --browser, which drives a
real Chrome via Playwright (pip install playwright; a local Chrome/Chromium).
After fetching, compare sha256 against kb/export/manifest.json: official pages
change over time, so a mismatch means the source moved on, not that you did wrong.
"""
import argparse, hashlib, json, pathlib, sys, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "kb" / "raw"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"


def fetch_http(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=90) as r:
        if r.status != 200:
            raise RuntimeError(f"HTTP {r.status}")
        return r.read()


def fetch_browser(url):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(headless=False)
        try:
            pg = b.new_page()
            if url.lower().endswith(".pdf"):
                resp = pg.request.get(url)
                return resp.body()
            pg.goto(url, wait_until="networkidle", timeout=90000)
            pg.wait_for_timeout(4000)
            return pg.content().encode("utf-8")
        finally:
            b.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--browser", action="store_true", help="fall back to a real browser on HTTP failure")
    ap.add_argument("--only", nargs="*", help="doc_ids to fetch")
    a = ap.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    sources = json.loads((ROOT / "kb" / "sources.json").read_text())
    man = {}
    mp = ROOT / "kb" / "export" / "manifest.json"
    if mp.exists():
        for d in json.loads(mp.read_text()).get("sources", []):
            man[d.get("doc_id")] = d.get("sha256")
    bad = 0
    for s in sources:
        if a.only and s["doc_id"] not in a.only:
            continue
        out = RAW / s["file"]
        try:
            try:
                data = fetch_http(s["url"])
            except Exception as e:
                if not a.browser:
                    raise
                print(f"  http failed ({e}); trying browser", file=sys.stderr)
                data = fetch_browser(s["url"])
            out.write_bytes(data)
            h = hashlib.sha256(data).hexdigest()
            flag = "" if man.get(s["doc_id"]) in (None, h) else "  (sha256 differs from manifest)"
            print(f"OK  {s['doc_id']:<28} {len(data):>9} B  {h[:12]}{flag}")
        except Exception as e:
            bad += 1
            print(f"ERR {s['doc_id']:<28} {s['url']}  {e}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
