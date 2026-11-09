"""Generate the Cloudflare API program run via the Cloudflare MCP `execute` tool:
uploads deploy/dist/worker.js (site embedded) as Worker SCRIPT and enables its workers.dev route."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
SCRIPT = "mizan-ai-itu-uae"
worker = (ROOT / "deploy/dist/worker.js").read_text(encoding="utf-8")
js = "async () => { const WORKER=" + json.dumps(worker) + ";\nconst SCRIPT='" + SCRIPT + "';" + """
const A=`/accounts/${accountId}`; const out={};
const meta={main_module:'worker.js',compatibility_date:'2026-11-01',bindings:[]};
const fd=new FormData(); fd.append('metadata',new Blob([JSON.stringify(meta)],{type:'application/json'})); fd.append('worker.js',new Blob([WORKER],{type:'application/javascript+module'}),'worker.js');
const u=await cloudflare.request({method:'PUT',path:`${A}/workers/scripts/${SCRIPT}`,body:fd}); out.upload={id:u.result.id,etag:u.result.etag,modified_on:u.result.modified_on,size:WORKER.length};
try{ const r=await cloudflare.request({method:'POST',path:`${A}/workers/scripts/${SCRIPT}/subdomain`,body:{enabled:true,previews_enabled:false}}); out.subdomain=r.result; }catch(e){ out.subErr=String(e.message).slice(0,300); }
try{ const r=await cloudflare.request({method:'GET',path:`${A}/workers/subdomain`}); out.account_subdomain=r.result.subdomain; }catch(e){ out.subdomainErr=String(e.message).slice(0,300); }
return out; }"""
Path(sys.argv[1]).write_text(js)
print(len(js), "bytes")
