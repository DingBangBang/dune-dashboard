
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
