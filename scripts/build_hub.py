#!/usr/bin/env python3
"""Build dashboard/index.html — a tabbed hub over the two datasets.

Tab 1: Alchemy real-time board      (dashboard/alchemy_data.json)   ← recent data
Tab 2: Chainbase historical snapshot (dashboard/chainbase_data.json) ← 2025-04 snapshot

The two boards are kept strictly separate, and every panel is labelled with its
data time range so the different windows can never be confused.

Usage:
    conda run -n dune_dashboard python scripts/build_hub.py
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "dashboard"

HTML = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Exchange Market Share Tracker — Dashboard Hub</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
 :root{--bg:#0d1117;--card:#161b22;--bd:#30363d;--mut:#8b949e;--fg:#e6edf3}
 body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;margin:0;background:var(--bg);color:var(--fg)}
 header{padding:18px 28px;background:#161b22;border-bottom:1px solid var(--bd)}
 h1{margin:0 0 4px;font-size:20px}.sub{color:var(--mut);font-size:13px}
 .tabs{display:flex;gap:8px;padding:14px 28px 0}
 .tab{padding:10px 18px;border:1px solid var(--bd);border-bottom:none;border-radius:10px 10px 0 0;
      background:#0d1117;color:var(--mut);cursor:pointer;font-size:14px}
 .tab.active{background:var(--card);color:var(--fg);font-weight:600}
 .wrap{padding:18px 28px;max-width:1500px;margin:0 auto}
 section{display:none}section.active{display:block}
 .srcnote{border-left:3px solid #58a6ff;padding:8px 12px;background:#111827;border-radius:6px;margin:12px 0 18px;font-size:13px;color:#c9d1d9}
 .kpis{display:flex;gap:14px;flex-wrap:wrap;margin:14px 0 22px}
 .kpi{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:12px 16px;min-width:160px}
 .kpi .v{font-size:20px;font-weight:600}.kpi .l{color:var(--mut);font-size:12px;margin-top:4px}
 .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(440px,1fr));gap:18px}
 .card{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:14px;overflow:hidden}
 .badge{display:inline-block;font-size:11px;padding:3px 8px;border-radius:999px;margin-bottom:8px}
 .b-live{background:#0f2b1a;color:#3fb950;border:1px solid #1f6f3f}
 .b-snap{background:#2b1f0a;color:#d29922;border:1px solid #6b4e12}
 .card h2{font-size:14px;margin:0 0 6px;color:#c9d1d9;font-weight:600}
 table{width:100%;border-collapse:collapse;font-size:12px}
 th,td{padding:5px 7px;text-align:right;border-bottom:1px solid #21262d;white-space:nowrap}
 th:first-child,td:first-child{text-align:left}
 th{color:var(--mut);font-weight:500}
 .pos{color:#3fb950}.neg{color:#f85149}
 .pending{margin-top:22px;background:#1c1408;border:1px solid #4d3800;border-radius:10px;padding:14px}
 .pending h2{color:#d29922}.pending li{font-size:13px;margin:4px 0;color:#c9d1d9}
 .err{color:#f85149;font-size:12px}
 code{background:#21262d;padding:1px 5px;border-radius:4px;font-size:12px}
 canvas{max-height:300px}
 footer{color:var(--mut);font-size:12px;padding:18px 28px;border-top:1px solid #21262d;margin-top:28px}
 .scroll{max-height:300px;overflow:auto}
</style></head><body>
<header>
  <h1>Exchange Market Share Tracker — Dashboard Hub</h1>
  <div class="sub">Two independent boards · different platforms · different data windows · never mixed</div>
</header>
<div class="tabs" id="tabs"></div>
<div class="wrap">
  <section id="tab-alchemy"></section>
  <section id="tab-chainbase"></section>
</div>
<footer id="footer"></footer>
<script>const DATA = __DATA__;</script>
<script src="hub.js"></script>
</body></html>
"""


def main() -> int:
    a_path = OUT_DIR / "alchemy_data.json"
    c_path = OUT_DIR / "chainbase_data.json"
    alchemy = json.loads(a_path.read_text()) if a_path.exists() else None
    chainbase = json.loads(c_path.read_text()) if c_path.exists() else None
    payload = {
        "alchemy": alchemy,
        "chainbase": chainbase,
        "generated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }
    html = HTML.replace("__DATA__", json.dumps(payload))
    (OUT_DIR / "index.html").write_text(html)
    (OUT_DIR / "hub.js").write_text(JS)
    print(f"wrote {(OUT_DIR / 'index.html').relative_to(ROOT)}")
    print(f"wrote {(OUT_DIR / 'hub.js').relative_to(ROOT)}")
    print(f"  alchemy  : {'present' if alchemy else 'MISSING'}")
    print(f"  chainbase: {'present' if chainbase else 'MISSING'}")
    return 0


JS = r"""
const A = DATA.alchemy, C = DATA.chainbase;
const PAL = ['#58a6ff','#3fb950','#d29922','#f85149','#bc8cff','#39c5cf','#ff7b72','#7ee787','#a5d6ff','#ffa657'];
const fmtC = v => (v < 0 ? '-' : '') + '$' + Math.abs(+v).toLocaleString('en-US', {notation:'compact', maximumFractionDigits:1});
const fmtN = v => (+v).toLocaleString('en-US', {maximumFractionDigits:2});
const isNum = v => v !== null && v !== '' && v !== undefined && !isNaN(Number(v));
function numCols(cols, rows){ return cols.filter(c => rows.slice(0,12).some(r => isNum(r[c]))); }
function esc(s){ return String(s).replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c])); }

function makeTable(card, cols, rows, limit){
  const wrap = document.createElement('div'); wrap.className = 'scroll';
  let h = '<table><tr>' + cols.map(c => '<th>' + esc(c) + '</th>').join('') + '</tr>';
  rows.slice(0, limit).forEach(r => {
    h += '<tr>' + cols.map(c => {
      const v = r[c];
      const cls = c.includes('net_flow') ? (Number(v) >= 0 ? 'pos' : 'neg') : '';
      return '<td class="' + cls + '">' + (isNum(v) ? fmtN(v) : esc(v == null ? '' : v)) + '</td>';
    }).join('') + '</tr>';
  });
  wrap.innerHTML = h + '</table>'; card.appendChild(wrap);
}

function autoChart(card, cols, rows){
  const nums = numCols(cols, rows);
  const xcol = cols.find(c => ['day','month','week'].includes(c));
  const canvas = document.createElement('canvas'); card.appendChild(canvas);
  const y = nums.filter(c => c !== xcol).slice(0, 3);
  let cfg = null;
  if (xcol && y.length){
    const labels = [...new Set(rows.map(r => String(r[xcol])))].sort();
    const datasets = y.map((c, i) => ({label:c, borderColor:PAL[i], backgroundColor:PAL[i], tension:.25, spanGaps:true,
      data: labels.map(l => {const r = rows.find(x => String(x[xcol]) === l); return r ? Number(r[c]) : 0;})}));
    cfg = {type:'line', data:{labels, datasets}, options:{responsive:true, plugins:{legend:{labels:{color:'#c9d1d9'}}},
      scales:{x:{ticks:{color:'#8b949e', maxTicksLimit:12}, grid:{color:'#21262d'}}, y:{ticks:{color:'#8b949e'}, grid:{color:'#21262d'}}}}};
  } else if (nums.length && cols.length >= 2){
    const cat = cols.find(c => !nums.includes(c)) || cols[0];
    const rs = rows.slice(0, 15);
    cfg = {type:'bar', data:{labels: rs.map(r => String(r[cat])), datasets:[{label:y[0]||nums[0], backgroundColor:PAL[0],
      data: rs.map(r => Number(r[y[0]||nums[0]]))}]},
      options:{indexAxis: rs.length > 5 ? 'y' : 'x', responsive:true, plugins:{legend:{labels:{color:'#c9d1d9'}}},
      scales:{x:{ticks:{color:'#8b949e'}, grid:{color:'#21262d'}}, y:{ticks:{color:'#8b949e'}, grid:{color:'#21262d'}}}}};
  } else { canvas.remove(); }
  if (cfg) new Chart(canvas, cfg);
}

function card(host, badgeClass, badgeText, title){
  const c = document.createElement('div'); c.className = 'card';
  c.innerHTML = '<span class="badge ' + badgeClass + '">' + esc(badgeText) + '</span><h2>' + esc(title) + '</h2>';
  host.appendChild(c); return c;
}
function renderAlchemy(el){
  const m = A.meta, live = 'LIVE · last ' + m.window_days + ' days';
  el.innerHTML = '<div class="srcnote"><b>Board 1 — Alchemy (real-time / recent).</b> Source: ' + esc(m.source) +
    '. Rolling window: last <b>' + m.window_days + ' days</b>. Updated ' + esc(m.generated) +
    '. Transfers analysed: <b>' + A.n_transfers.toLocaleString() + '</b>.</div>' +
    '<div class="kpis" id="a-kpis"></div><div class="grid" id="a-grid"></div>';
  const t = A.totals;
  document.getElementById('a-kpis').innerHTML = [
    {v: fmtC(t.net), l: 'Net flow (window)', c: t.net >= 0 ? 'pos' : 'neg'},
    {v: fmtC(t.inflow), l: 'Total inflow'},
    {v: fmtC(t.outflow), l: 'Total outflow'},
    {v: A.exchanges.length, l: 'Exchanges tracked'},
    {v: A.n_transfers.toLocaleString(), l: 'Transfers analysed'},
    {v: m.window_days + 'd', l: 'Window'}].map(k =>
      '<div class="kpi"><div class="v ' + (k.c||'') + '">' + k.v + '</div><div class="l">' + k.l + '</div></div>').join('');
  const grid = document.getElementById('a-grid');
  const c1 = card(grid, 'b-live', live, 'Daily net flow by exchange (USD)');
  new Chart(c1.appendChild(document.createElement('canvas')), {type:'bar',
    data:{labels:A.days, datasets:A.exchanges.map((e,i)=>({label:e.exchange, backgroundColor:PAL[i%PAL.length],
      data:A.days.map(d=>{const r=A.daily.find(x=>x.exchange===e.exchange&&x.day===d); return r?r.net_flow_usd:0;})}))},
    options:{responsive:true, plugins:{legend:{labels:{color:'#c9d1d9'}}}, scales:{x:{ticks:{color:'#8b949e'},grid:{color:'#21262d'}},y:{ticks:{color:'#8b949e'},grid:{color:'#21262d'}}}}});
  const c2 = card(grid, 'b-live', live, 'Inflow vs outflow by exchange (USD)');
  new Chart(c2.appendChild(document.createElement('canvas')), {type:'bar',
    data:{labels:A.exchanges.map(e=>e.exchange), datasets:[
      {label:'Inflow', data:A.exchanges.map(e=>e.inflow_usd), backgroundColor:'#3fb950'},
      {label:'Outflow', data:A.exchanges.map(e=>e.outflow_usd), backgroundColor:'#f85149'}]},
    options:{responsive:true, plugins:{legend:{labels:{color:'#c9d1d9'}}}, scales:{x:{ticks:{color:'#8b949e'},grid:{color:'#21262d'}},y:{ticks:{color:'#8b949e'},grid:{color:'#21262d'}}}}});
  const c3 = card(grid, 'b-live', live, 'Net flow by asset (USD)');
  new Chart(c3.appendChild(document.createElement('canvas')), {type:'bar',
    data:{labels:A.assets.map(a=>a.asset), datasets:[
      {label:'Inflow', data:A.assets.map(a=>a.inflow_usd), backgroundColor:'#3fb950'},
      {label:'Outflow', data:A.assets.map(a=>a.outflow_usd), backgroundColor:'#f85149'}]},
    options:{indexAxis:'y', responsive:true, plugins:{legend:{labels:{color:'#c9d1d9'}}}, scales:{x:{ticks:{color:'#8b949e'},grid:{color:'#21262d'}},y:{ticks:{color:'#8b949e'},grid:{color:'#21262d'}}}}});
  const c4 = card(grid, 'b-live', live, 'Exchange summary');
  makeTable(c4, ['exchange','inflow_usd','outflow_usd','net_flow_usd','transfers'], A.exchanges, 20);
  const pend = document.createElement('div'); pend.className = 'pending';
  pend.innerHTML = '<h2>⏳ Not on this board (needs curated DEX tables)</h2><ul>' +
    A.pending.map(p => '<li><b>' + p[0] + '</b> ' + p[1] + ' <span class="sub">— ' + p[2] + '</span></li>').join('') +
    '</ul><p class="sub">Where data exists these are covered by the historical snapshot board (Tab 2).</p>';
  el.appendChild(pend);
}
function renderChainbase(el){
  if (!C){ el.innerHTML = '<div class="srcnote">Chainbase results not generated yet. Run <code>scripts/chainbase_pipeline.py</code>.</div>'; return; }
  const snap = 'HISTORICAL SNAPSHOT · ' + C.window_start + ' → ' + C.snapshot_end;
  el.innerHTML = '<div class="srcnote"><b>Board 2 — Chainbase Data Cloud (historical snapshot).</b> Source: ' +
    esc(C.source) + '. This board is a <b>frozen snapshot ending ' + esc(C.snapshot_end) +
    '</b> — it is NOT live and must not be compared day-for-day with Board 1. Generated ' + esc(C.generated) + '.</div>' +
    '<div class="kpis" id="c-kpis"></div><div class="grid" id="c-grid"></div>';
  const qs = Object.keys(C.queries).sort().map(k => C.queries[k]);
  const ok = qs.filter(q => q.status === 'ok').length;
  document.getElementById('c-kpis').innerHTML = [
    {v: ok + '/' + qs.length, l: 'Queries OK'},
    {v: C.snapshot_end, l: 'Snapshot end'},
    {v: C.window_start, l: 'Window start'},
    {v: qs.reduce((s,q)=>s+(q.row_count||0),0).toLocaleString(), l: 'Rows returned'}].map(k =>
      '<div class="kpi"><div class="v">' + k.v + '</div><div class="l">' + k.l + '</div></div>').join('');
  const grid = document.getElementById('c-grid');
  qs.forEach(q => {
    const c = card(grid, 'b-snap', snap, q.id + ' · ' + q.title);
    if (q.status !== 'ok'){ c.innerHTML += '<div class="err">query failed: ' + esc(q.error || '') + '</div>'; return; }
    autoChart(c, q.columns, q.rows);
    makeTable(c, q.columns, q.rows, 15);
    c.innerHTML += '<div class="sub" style="margin-top:6px">' + (q.row_count||0).toLocaleString() + ' rows</div>';
  });
}

const tabs = [];
if (A) tabs.push({id:'alchemy', label:'🟢 Alchemy — real-time (last ' + A.meta.window_days + ' days)'});
if (C) tabs.push({id:'chainbase', label:'🟡 Chainbase — historical snapshot (' + C.snapshot_end + ')'});
const tabsEl = document.getElementById('tabs');
tabsEl.innerHTML = tabs.map((t,i) => '<div class="tab' + (i===0?' active':'') + '" data-id="' + t.id + '">' + t.label + '</div>').join('');
tabsEl.querySelectorAll('.tab').forEach(btn => btn.onclick = () => {
  tabsEl.querySelectorAll('.tab').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('section').forEach(s => s.classList.remove('active'));
  document.getElementById('tab-' + btn.dataset.id).classList.add('active');
});
if (tabs.length){
  document.getElementById('tab-' + tabs[0].id).classList.add('active');
  if (A) renderAlchemy(document.getElementById('tab-alchemy'));
  if (C) renderChainbase(document.getElementById('tab-chainbase'));
}
document.getElementById('footer').innerHTML =
  'Board 1: Alchemy (real-time, rolling window). Board 2: Chainbase (historical snapshot ending ' +
  (C ? C.snapshot_end : 'n/a') + '). Generated ' + esc(DATA.generated) + '. Data windows differ by design.';
"""


if __name__ == "__main__":
    raise SystemExit(main())

