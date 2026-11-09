import { verifyChain } from "./chain.js";

const ROLES = [
  ["service_agent", "Service Agent", "resident conversations"],
  ["service_owner", "Service Owner", "ops telemetry"],
  ["data_protection", "Data Protection", "data-flow logs"],
  ["regulator", "Digital Gov / Regulator", "vendor notices"],
  ["cyber", "Cyber Security", "social listening"],
  ["policy_adviser", "Policy & Legal Adviser", "reads all traffic"],
  ["human", "Human approver", "only role that may DECIDE"],
];
const RNAME = Object.fromEntries(ROLES.map(r => [r[0], r[1]]));
const SHORT = {
  "uae-ai-strategy-2031": "UAE AI Strategy 2031", "uae-ai-ethics": "UAE AI Ethics", "uae-genai-guide": "UAE GenAI Guide",
  "uae-ai-charter": "UAE AI Charter", "uae-ai-intl-stance": "UAE Intl AI Stance", "uae-pdpl-2021": "PDPL 45/2021",
  "uae-cybercrime-2021": "Cybercrime DL 34/2021", "uae-ict-health-2019": "ICT Health Law 2/2019", "uae-data-protection-portal": "u.ae Data Protection",
  "uae-digital-gov-2025": "UAE Digital Gov 2025", "eu-ai-act-2024": "EU AI Act", "eu-gdpr-2016": "GDPR", "oecd-ai-principles": "OECD AI Rec.",
  "nist-ai-rmf-1": "NIST AI RMF", "nist-ai-600-1": "NIST AI 600-1", "sg-genai-mgf-2024": "SG GenAI MGF", "itu-t-y3172": "ITU-T Y.3172", "itu-ai-ready-2025": "ITU AI Ready",
};
const Y = [
  ["SRC", "Source", "Synthetic applications, vendor & policy docs"], ["C", "Collector", "Intake + KB ingestion (ITU parser)"],
  ["PP", "Pre-processor", "Article chunking, metadata, PII flags"], ["M", "Model", "Service model; nomic embeddings"],
  ["P", "Policy", "Approval gates, residency, citation rule"], ["D", "Distributor", "Typed message bus to roles"],
  ["SINK", "Sink", "Human approver, notices, gap register"],
];
const YO = [["MLFO", "ML function orchestrator", "Scenario engine and router"], ["ML-sandbox", "ML sandbox", "This replay: test before go-live"], ["ML-underlay", "ML underlay", "In-country vs failover region"]];
const DIMS = ["Data/Model Marketplace", "Generated Content Marketplace", "Cross-Domain Correlation", "Contextualization & Regional Impact", "AI in Workflows", "Human Interface", "Strategy Alignment", "Collaboration with AI", "Impacts of Humans in AI", "AI & Policies", "AI for Inclusion", "Granular Priorities", "Digital Infrastructure"];

const $ = s => document.querySelector(s);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const state = { run: "S1-baseline", runs: {}, raw: {}, chunks: [], byId: {}, t: 999, playing: false, sel: null, node: null, scope: "" };

async function getText(u) { const r = await fetch(u); if (!r.ok) throw new Error(u + " " + r.status); return r.text(); }

function parseRun(text) {
  const lines = text.split("\n").filter(Boolean);
  const recs = lines.map(l => JSON.parse(l));
  const items = [], gaps = [];
  let summary = null, start = null;
  for (const r of recs) {
    if (r.kind === "event_delivery") items.push({ kind: "event", id: r.payload.event_id, lane: r.agent, t: r.sim_t, rec: r });
    else if (r.kind === "message" || r.kind === "decision") { const m = r.payload.message; items.push({ kind: "msg", id: m.id, lane: m.sender, t: r.sim_t, m, rec: r }); }
    else if (r.kind === "gap") gaps.push(r.payload);
    else if (r.kind === "run_end") summary = r.payload;
    else if (r.kind === "run_start") start = r.payload;
  }
  const maxT = Math.ceil(Math.max(...items.map(i => i.t)) + 3);
  return { lines, items, gaps, summary, start, maxT };
}

function docLabel(c) {
  const ch = state.byId[c.chunk_id];
  if (c.kind === "event") return `${c.chunk_id} · event`;
  return `${SHORT[ch?.doc_id || c.doc_id] || c.doc_id} · ${(ch?.section || c.section || "").split(" – ")[0]}`;
}

/* ---------- lanes ---------- */
function x(t, R) { return (t / R.maxT) * 100; }
function renderLanes() {
  const R = state.runs[state.run];
  const lanes = $("#lanes");
  let h = "";
  for (const [k, name, feed] of ROLES) {
    h += `<div class="lane ${k === "human" ? "human" : ""}" role="listitem"><div class="lane-name">${esc(name)}<small>${esc(feed)}</small></div><div class="track" data-lane="${k}">`;
    let prevT = -99, n = 0;
    for (const it of R.items.filter(i => i.lane === k).sort((a, b) => a.t - b.t)) {
      let pos = "up", dx = 0;
      if (it.kind === "msg") { pos = "down"; n = it.t - prevT < R.maxT * 0.03 ? n + 1 : 0; prevT = it.t; dx = n * 20; }
      const flags = it.kind === "msg" ? it.m.claims.map(c => c.status) : [];
      const flag = flags.includes("UNCITED") || flags.includes("INVALID") ? "flag uncited" : flags.includes("WEAK") ? "flag" : "";
      const cls = it.kind === "event" ? `ev ${it.rec.payload.twist ? "twist" : ""}` : `msg ${it.m.type} ${flag}`;
      const label = it.kind === "event" ? it.id : "";
      const aria = it.kind === "event" ? `Event ${it.id} delivered to ${name} at T+${it.t}` : `${it.m.type} ${it.m.subject} from ${name} at T+${it.t}`;
      h += `<button class="item ${cls} ${pos}" style="left:calc(${x(it.t, R)}% + ${dx}px)" data-key="${it.kind}:${it.id}:${k}" data-t="${it.t}" aria-label="${esc(aria)}">${label}</button>`;
    }
    h += `</div></div>`;
  }
  let ax = `<div class="axis">`;
  for (let t = 0; t <= R.maxT; t += 10) ax += `<span style="left:${x(t, R)}%">T+${t}</span>`;
  ax += `</div>`;
  lanes.innerHTML = h + ax + `<svg class="links" id="links"></svg><div class="playhead" id="playhead"></div>`;
  lanes.querySelectorAll(".item").forEach(b => b.addEventListener("click", () => select(b.dataset.key)));
  $("#scrub").max = R.maxT;
  renderFeed();
  applyTime();
}

function renderFeed() {
  const R = state.runs[state.run];
  const seen = new Set();
  const rows = [...R.items].sort((a, b) => a.t - b.t || (a.kind === "event" ? -1 : 1)).filter(it => {
    if (it.kind !== "event") return true; const k = it.id + "@" + it.t; if (seen.has(k)) return false; seen.add(k); return true; });
  $("#feed").innerHTML = rows.map(it => {
    const key = `${it.kind}:${it.id}:${it.lane}`;
    if (it.kind === "event") {
      const p = it.rec.payload;
      return `<li data-key="${key}" data-t="${it.t}" tabindex="0"><span class="t">T+${it.t}</span><i class="g ev"></i><div><div class="who">${(() => { const to = R.items.filter(i => i.kind === "event" && i.id === it.id && i.t === it.t).map(i => RNAME[i.lane]); return to.length >= 6 ? "Delivered to all roles" : "Private to " + esc(to.join(", ")); })()}${p.twist ? " · <b style='color:var(--bad)'>judge twist</b>" : ""}</div><div class="subj">${esc(it.id)} · ${esc(p.title)}</div></div></li>`;
    }
    const m = it.m; const bad = m.claims.filter(c => !["SUPPORTED","INFO"].includes(c.status)).map(c => c.status);
    return `<li data-key="${key}" data-t="${it.t}" data-node="${esc(m.y3172_node)}" tabindex="0"><span class="t">T+${it.t}</span><i class="g ${m.type}"></i><div><div class="who">${m.type} · ${esc(RNAME[m.sender])} → ${esc(m.to.map(r => r === "all" ? "all" : RNAME[r]).join(", "))}${bad.length ? ` · <span class="st ${bad[0]}">${[...new Set(bad)].join(" ")}</span>` : ""}</div><div class="subj">${esc(m.subject)}</div></div></li>`;
  }).join("");
  $("#feed").querySelectorAll("li").forEach(li => {
    li.addEventListener("click", () => select(li.dataset.key));
    li.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); select(li.dataset.key); } });
  });
}

function applyTime() {
  const R = state.runs[state.run];
  const t = Math.min(state.t, R.maxT);
  $("#clock").textContent = `T+${Math.round(t)}`;
  $("#scrub").value = t;
  const ph = $("#playhead");
  if (ph) ph.style.left = `calc(150px + (100% - 150px) * ${t / R.maxT})`;
  document.querySelectorAll(".item,.feed li").forEach(el => {
    el.classList.toggle("future", +el.dataset.t > t);
    if (state.node && el.matches(".feed li")) el.classList.toggle("future", +el.dataset.t > t || (el.dataset.node !== undefined && el.dataset.node !== state.node) || el.dataset.node === undefined);
  });
  document.querySelectorAll(".item.msg").forEach(el => {
    const it = findItem(el.dataset.key);
    el.classList.toggle("dimmed", !!state.node && it?.m?.y3172_node !== state.node);
  });
}

function findItem(key) {
  const [kind, id, lane] = key.split(":");
  return state.runs[state.run].items.find(i => i.kind === kind && i.id === id && i.lane === lane);
}

function drawLinks(it) {
  const svg = $("#links"); if (!svg) return;
  svg.innerHTML = "";
  if (!it || it.kind !== "msg") return;
  const R = state.runs[state.run];
  const lanesEl = $("#lanes"), box = lanesEl.getBoundingClientRect();
  const laneY = k => { const tr = lanesEl.querySelector(`.track[data-lane="${k}"]`); const b = tr.getBoundingClientRect(); return b.top - box.top + b.height / 2; };
  const trackX = t => { const tr = lanesEl.querySelector(".track"); const b = tr.getBoundingClientRect(); return b.left - box.left + b.width * (t / R.maxT); };
  svg.setAttribute("viewBox", `0 0 ${box.width} ${box.height}`);
  svg.setAttribute("width", box.width); svg.setAttribute("height", box.height);
  const to = it.m.to.includes("all") ? ROLES.map(r => r[0]).filter(r => r !== it.lane && r !== "human") : it.m.to;
  const x1 = trackX(it.t), y1 = laneY(it.lane);
  let p = "";
  for (const r of to) {
    if (!RNAME[r]) continue;
    const x2 = trackX(it.t + 1), y2 = laneY(r);
    p += `<path class="hl" d="M${x1},${y1} C${x1 + 70},${y1} ${x2 + 70},${y2} ${x2 + 6},${y2}"/>`;
  }
  svg.innerHTML = p;
}

/* ---------- dossier ---------- */
function select(key) {
  state.sel = key;
  document.querySelectorAll(".sel").forEach(e => e.classList.remove("sel"));
  document.querySelectorAll(`[data-key="${CSS.escape(key)}"]`).forEach(e => e.classList.add("sel"));
  const it = findItem(key); if (!it) return;
  if (it.t > state.t) { state.t = it.t; applyTime(); }
  drawLinks(it);
  const d = $("#dossier");
  const R = state.runs[state.run];
  if (it.kind === "event") {
    const p = it.rec.payload;
    const all = R.items.filter(i => i.kind === "event" && i.id === it.id).map(i => `${RNAME[i.lane]} at T+${i.t}`);
    d.innerHTML = `<span class="badge ev">PRIVATE EVENT ${esc(it.id)}</span>${p.twist ? ` <span class="badge OBJECT">JUDGE TWIST</span>` : ""}
      <h3>${esc(p.title)}</h3><p>${esc(p.body)}</p>
      <dl class="kv"><dt>delivered</dt><dd>${esc(all.join(" · "))}</dd><dt>not seen by</dt><dd>${esc(ROLES.filter(r => r[0] !== "human" && !R.items.some(i => i.kind === "event" && i.id === it.id && i.lane === r[0])).map(r => r[1]).join(", ") || "—")}</dd>
      <dt>facts</dt><dd class="mono">${esc(p.facts.join(", "))}</dd><dt>audit</dt><dd class="mono">seq ${it.rec.seq} · ${it.rec.hash.slice(0, 16)}…</dd></dl>`;
  } else {
    const m = it.m, tr = it.rec.payload.reasoning_trace;
    const claims = m.claims.map(c => `<div class="claim"><p><span class="st ${c.status}">${c.status}</span>${esc(c.text)}</p>
      <div class="cites">${c.citations.map(ct => `<button class="cite ${ct.kind === "event" ? "event" : (state.byId[ct.chunk_id]?.scope === "global" ? "global" : "")}" data-chunk="${esc(ct.chunk_id)}" data-kind="${ct.kind}" data-quote="${esc(ct.quote)}">${esc(docLabel(ct))}</button>`).join("") || `<span class="small dim">${esc(c.note)}</span>`}</div>
      ${c.citations[0] ? `<p class="quote">“${esc(c.citations[0].quote)}”</p>` : ""}</div>`).join("");
    const traceH = tr ? `<details class="trace"><summary>REASONING TRACE · rule ${esc(tr.rule)}</summary><ol>
      <li><b>Facts known</b>: <span class="mono">${esc(tr.facts_known.join(", "))}</span></li>
      <li><b>Seen so far</b>: <span class="mono">${esc(tr.events_seen.join(", "))}</span></li>
      <li><b>Rule</b>: <span class="mono">${esc(JSON.stringify(tr.rule_condition))}</span></li>
      ${tr.retrieval.map(r => `<li><b>Retrieve</b> “${esc(r.query)}” in <span class="mono">${esc(r.scope.map(s => SHORT[s] || s).join(", "))}</span>${r.candidates.map(c => `<span class="cand">${esc(c.chunk_id)} · ${c.method} ${c.score}</span>`).join("")}</li>`).join("")}
      ${tr.options?.length ? `<li><b>Options</b>: ${esc(tr.options.join(" | "))}</li>` : ""}
      <li><b>Choice</b>: ${esc(tr.choice)}</li></ol></details>` : "";
    d.innerHTML = `<span class="badge ${m.type}">${m.type}</span> ${m.proposal_id ? `<span class="mono small dim">${esc(m.proposal_id)}</span>` : ""}
      <p class="route">${esc(RNAME[m.sender])} → ${esc(m.to.map(r => r === "all" ? "all roles" : RNAME[r]).join(", "))} · T+${m.t}</p>
      <h3>${esc(m.subject)}</h3>${claims}
      <dl class="kv"><dt>Y.3172</dt><dd class="mono">${esc(m.y3172_node)}</dd><dt>Readiness</dt><dd>${m.readiness_dims.map(n => `D${n} ${esc(DIMS[n - 1])}`).join(" · ")}</dd>
      <dt>confidence</dt><dd class="mono">${m.confidence}</dd><dt>engine</dt><dd class="mono">${esc(it.rec.payload.model || it.rec.payload.mode || "")}</dd><dt>audit</dt><dd class="mono">seq ${it.rec.seq} · ${it.rec.hash.slice(0, 16)}…</dd></dl>${traceH}`;
    d.querySelectorAll(".cite").forEach(b => b.addEventListener("click", () => openSource(b.dataset.chunk, b.dataset.quote, b.dataset.kind)));
  }
  if (matchMedia("(max-width:1100px)").matches) d.scrollIntoView({ behavior: "smooth", block: "start" });
}

/* ---------- source drawer ---------- */
let lastFocus = null;
function openSource(id, quote, kind) {
  lastFocus = document.activeElement;
  const dr = $("#drawer");
  if (kind === "event") {
    const R = state.runs[state.run]; const ev = R.items.find(i => i.kind === "event" && i.id === id)?.rec.payload;
    $("#drId").textContent = `${id} · scenario event (synthetic)`; $("#drTitle").textContent = ev?.title || id;
    $("#drMeta").textContent = "Evidence from the scenario feed, not a KB source."; $("#drText").textContent = ev?.body || ""; $("#drLink").hidden = true;
  } else {
    const c = state.byId[id];
    $("#drId").textContent = id; $("#drTitle").textContent = `${c.title} — ${c.section}`;
    $("#drMeta").innerHTML = `<span class="scope ${c.scope === "global" ? "global" : ""}">${c.scope === "global" ? "GLOBAL EXAMPLE" : "UAE"}</span> ${esc(c.issuer)} · ${esc(c.status)} · ${esc(c.doc_date)} · ${esc(c.language)}`;
    const t = esc(c.text), q = quote ? esc(quote) : "";
    $("#drText").innerHTML = q && t.includes(q) ? t.replace(q, `<mark>${q}</mark>`) : t;
    $("#drLink").hidden = false; $("#drLink").href = c.url;
  }
  dr.hidden = false; $("#drClose").focus();
}
function closeDrawer() { $("#drawer").hidden = true; lastFocus?.focus(); }

/* ---------- gaps ---------- */
function renderGaps() {
  const R = state.runs[state.run];
  $("#gapList").innerHTML = R.gaps.map(g => {
    const u = g.uae_mapping; const cls = u.status.startsWith("provision") ? "found" : u.status.startsWith("partial") ? "partial" : "none";
    return `<article class="gap"><div style="display:flex;gap:8px;align-items:center"><span class="gid">${g.id}</span><span class="pill">${esc(g.type)}</span><span class="review" style="margin-left:auto">needs expert review</span></div>
      <h3>${esc(g.title)}</h3><p>${esc(g.description)}</p>
      <div class="map"><h4>UAE mapping (this KB)</h4><div><span class="ustat ${cls}">${esc(u.status)}</span> <span class="small dim">terms ${esc(u.terms_required.join(" + "))}; found ${esc(u.terms_found.join(", ") || "none")}</span></div>
        <div class="cites"><button class="cite" data-chunk="${esc(u.closest.chunk_id)}" data-quote="${esc(u.closest.quote)}">closest: ${esc(docLabel(u.closest))}</button></div></div>
      <div class="map"><h4>Global examples</h4><div class="cites">${g.global_examples.map(e => `<button class="cite global" data-chunk="${esc(e.chunk_id)}" data-quote="${esc(e.quote)}">${esc(docLabel(e))}</button>`).join("")}</div>
        ${g.global_examples[0] ? `<p class="quote">“${esc(g.global_examples[0].quote)}”</p>` : ""}</div>
      <p class="small dim">Triggered by ${esc(g.trigger.join(", "))} · Readiness ${g.dims.map(d => "D" + d).join(", ")} · confidence ${esc(g.confidence)}</p></article>`;
  }).join("");
  $("#gapList").querySelectorAll(".cite").forEach(b => b.addEventListener("click", () => openSource(b.dataset.chunk, b.dataset.quote)));
}

/* ---------- pipeline + dims ---------- */
function renderAlign() {
  const R = state.runs[state.run];
  const msgs = R.items.filter(i => i.kind === "msg").map(i => i.m);
  const cnt = k => msgs.filter(m => m.y3172_node === k).length;
  const node = ([k, n, im]) => `<button class="node" data-node="${k}" aria-pressed="${state.node === k}"><b>${k}</b><span class="nm">${n}</span><span class="im">${im}</span><span class="ct">${cnt(k) || ""}</span></button>`;
  $("#pipeline").innerHTML = `<div class="over">${YO.map(node).join("")}</div>` + `<div class="flow" style="display:contents">${Y.map(node).join("")}</div>`;
  $("#pipeline").querySelectorAll(".node").forEach(b => b.addEventListener("click", () => {
    state.node = state.node === b.dataset.node ? null : b.dataset.node; renderAlign(); applyTime();
    if (state.node) $("#warroom").scrollIntoView({ behavior: "smooth" });
  }));
  const dc = DIMS.map((n, i) => msgs.filter(m => m.readiness_dims.includes(i + 1)).length);
  const mx = Math.max(...dc, 1);
  $("#dims").innerHTML = DIMS.map((n, i) => `<div class="dim-row"><span class="mono">D${i + 1}</span><span>${esc(n)}</span><span class="mono">${dc[i]}</span><span class="bar"><i style="width:${(dc[i] / mx) * 100}%"></i></span></div>`).join("");
}

/* ---------- KB ---------- */
const STOP = new Set("a an the of to and or in on for by with from as at is are be been was were that this these those it its into than then which who whom whose shall may must can not no any all such other under where when what how does do".split(" "));
const tok = s => (s.toLowerCase().match(/[a-z0-9]+/g) || []).filter(w => !STOP.has(w) && w.length > 1);
let IDX = null;
function buildIndex() {
  const docs = state.chunks.map(c => { const t = tok(c.title + " " + c.section + " " + c.text); const tf = new Map(); t.forEach(w => tf.set(w, (tf.get(w) || 0) + 1)); return { tf, len: t.length }; });
  const df = new Map(); docs.forEach(d => d.tf.forEach((_, w) => df.set(w, (df.get(w) || 0) + 1)));
  const N = docs.length, avg = docs.reduce((a, d) => a + d.len, 0) / N;
  const idf = new Map([...df].map(([w, f]) => [w, Math.log(1 + (N - f + 0.5) / (f + 0.5))]));
  IDX = { docs, idf, avg };
}
function search(q, scope) {
  const qt = tok(q); const out = [];
  IDX.docs.forEach((d, i) => {
    const c = state.chunks[i]; if (scope && c.scope !== scope) return;
    let s = 0; for (const w of qt) { const f = d.tf.get(w); if (f) s += IDX.idf.get(w) * f * 2.4 / (f + 1.4 * (0.25 + 0.75 * d.len / IDX.avg)); }
    if (s > 0) out.push([s, c]);
  });
  return out.sort((a, b) => b[0] - a[0]).slice(0, 12);
}
function hl(text, q) {
  const words = tok(q).filter(w => w.length > 2); let t = esc(text);
  if (!words.length) return t;
  return t.replace(new RegExp(`\\b(${words.map(w => w.replace(/[^a-z0-9]/g, "")).join("|")})`, "gi"), "<mark>$1</mark>");
}
function renderKB() {
  const q = $("#kbQ").value.trim() || "cross-border transfer of personal data";
  const res = search(q, state.scope);
  $("#kbResults").innerHTML = res.map(([s, c]) => `<li><button data-chunk="${esc(c.chunk_id)}"><div class="h">${esc(SHORT[c.doc_id] || c.title)} · ${esc(c.section)}</div><div class="s"><span class="scope ${c.scope === "global" ? "global" : ""}">${c.scope === "global" ? "GLOBAL" : "UAE"}</span> ${esc(c.chunk_id)} · bm25 ${s.toFixed(2)}</div><div class="x">${hl(c.text.slice(0, 420), q)}</div></button></li>`).join("") || `<li class="dim">No matches.</li>`;
  $("#kbResults").querySelectorAll("button").forEach(b => b.addEventListener("click", () => openSource(b.dataset.chunk)));
}
function renderManifest(man, ev) {
  const nU = man.sources.filter(s => s.scope === "UAE").length;
  $("#kbMeta").textContent = `${man.documents} official public documents (${nU} UAE, ${man.documents - nU} global examples) · ${man.chunks.toLocaleString()} article/section/page chunks · built with the ITU reference ingestion code · embeddings ${man.embedding_backend} in ChromaDB. In-browser search below is BM25 over the exported chunks.`;
  $("#manifest").innerHTML = man.sources.map(s => `<div class="mrow"><span class="mt">${esc(s.title)}</span><span class="scope ${s.scope === "global" ? "global" : ""}">${s.scope === "global" ? "GLOBAL" : "UAE"}</span><span class="small dim">${esc(s.issuer)} · ${esc(s.status)} · ${s.chunks} chunks (${esc(s.chunking)})</span><span class="ms">sha256 ${s.sha256.slice(0, 20)}… · <a href="${esc(s.url)}" target="_blank" rel="noopener">source</a></span></div>`).join("");
  $("#notIngested").innerHTML = man.not_ingested.map(n => `<li><b>${esc(n.title)}</b>: ${esc(n.reason)}</li>`).join("");
  if (ev) {
    const rows = Object.entries(ev.methods).map(([k, m]) => `<tr><td>${k}</td><td>${m.doc_hits}/${ev.n_queries}</td><td>${m.section_hits}/${m.section_queries}</td><td>${m.doc_mrr5 ?? m["doc_mrr@5"]}</td></tr>`).join("");
    $("#evalBox").innerHTML = `<table><tr><th>retrieval</th><th>doc hit@5</th><th>article hit@5</th><th>MRR@5</th></tr>${rows}</table><p>Real run on ${ev.run_at.slice(0, 10)} with ${ev.n_queries} queries written by the author. Gold = expected document, plus the expected article for ${Object.values(ev.methods)[0].section_queries} of them. Scores are optimistic because the queries use legal wording. Agents use hybrid retrieval. File: <span class="mono">kb/eval/results.json</span>.</p>`;
    $("#facts").innerHTML = [`<b>${man.documents}</b> documents`, `<b>${man.chunks.toLocaleString()}</b> chunks`, `hybrid doc hit@5 <b>${ev.methods.hybrid.doc_hits}/${ev.n_queries}</b>`, `<b>6</b> role agents + human gate`, `uneven, delayed delivery`, `deterministic agents · <b>no LLM</b>`].map(s => `<li>${s}</li>`).join("");
  }
}

/* ---------- verify ---------- */
async function doVerify() {
  const out = $("#verifyOut"); out.className = "mono small"; out.textContent = "verifying…";
  const r = await verifyChain(state.runs[state.run].lines, crypto.subtle);
  out.classList.add(r.ok ? "ok" : "bad");
  out.textContent = r.ok ? `✓ ${r.records} records · head ${r.head.slice(0, 10)}…` : `✕ broken at line ${r.brokenAt}: ${r.reason}`;
  $("#verifyBtn").textContent = r.ok ? "Chain verified" : "Chain broken";
  setTimeout(() => { $("#verifyBtn").textContent = "Verify audit chain"; }, 2500);
}

/* ---------- player ---------- */
let raf = null, last = 0;
function tick(ts) {
  if (!state.playing) return;
  const dt = (ts - last) / 1000; last = ts;
  state.t = Math.min(state.t + dt * 2 * +$("#speed").value, state.runs[state.run].maxT);
  applyTime();
  if (state.t >= state.runs[state.run].maxT) { stop(); return; }
  raf = requestAnimationFrame(tick);
}
function play() { if (state.t >= state.runs[state.run].maxT) state.t = 0; state.playing = true; $("#playBtn").textContent = "❚❚"; $("#playBtn").setAttribute("aria-label", "Pause replay"); last = performance.now(); raf = requestAnimationFrame(tick); }
function stop() { state.playing = false; $("#playBtn").textContent = "▶"; $("#playBtn").setAttribute("aria-label", "Play replay"); cancelAnimationFrame(raf); }

function setRun(id) {
  state.run = id; stop();
  document.querySelectorAll(".seg button").forEach(b => b.setAttribute("aria-checked", b.dataset.run === id));
  $("#verifyOut").textContent = ""; $("#verifyOut").className = "mono small";
  state.t = state.runs[id].maxT; state.sel = null;
  $("#dossier").innerHTML = `<p class="dim">${id === "S1-twist" ? "Judge twist run: at T+48 the product team asks to retrain on the leaked logs. Look for the OBJECT messages and the UNCITED flag." : "Baseline run without the judge twist."} Select an item to inspect it.</p>`;
  renderLanes(); renderGaps(); renderAlign();
  history.replaceState(null, "", id === "S1-twist" ? "#twist" : "#");
}

async function init() {
  const [b, t, ch, man, ev] = await Promise.all([
    getText("data/runs/S1-baseline.audit.jsonl"), getText("data/runs/S1-twist.audit.jsonl"), getText("data/kb/chunks.jsonl"),
    fetch("data/kb/manifest.json").then(r => r.json()), fetch("data/kb/eval.json").then(r => r.ok ? r.json() : null)]);
  state.runs["S1-baseline"] = parseRun(b); state.runs["S1-twist"] = parseRun(t);
  state.chunks = ch.split("\n").filter(Boolean).map(l => JSON.parse(l));
  state.byId = Object.fromEntries(state.chunks.map(c => [c.chunk_id, c]));
  buildIndex(); renderManifest(man, ev); renderKB();
  setRun(location.hash === "#twist" ? "S1-twist" : "S1-baseline");
  document.querySelectorAll(".seg button").forEach(btn => btn.addEventListener("click", () => setRun(btn.dataset.run)));
  $("#verifyBtn").addEventListener("click", doVerify);
  $("#playBtn").addEventListener("click", () => state.playing ? stop() : play());
  $("#scrub").addEventListener("input", e => { stop(); state.t = +e.target.value; applyTime(); });
  $("#kbQ").addEventListener("input", () => renderKB());
  document.querySelectorAll(".chip").forEach(c => c.addEventListener("click", () => { state.scope = c.dataset.scope; document.querySelectorAll(".chip").forEach(x => x.setAttribute("aria-checked", x === c)); renderKB(); }));
  $("#drClose").addEventListener("click", closeDrawer);
  $("#drawer").addEventListener("click", e => { if (e.target.id === "drawer") closeDrawer(); });
  document.addEventListener("keydown", e => { if (e.key === "Escape" && !$("#drawer").hidden) closeDrawer(); });
  addEventListener("resize", () => { if (state.sel) drawLinks(findItem(state.sel)); });
}
init().catch(e => { document.querySelector("main").insertAdjacentHTML("afterbegin", `<p style="color:#b42318">Failed to load data: ${esc(e.message)}</p>`); });
