const fmtUSD = v => (v < 0 ? '-' : '') + '$' + Math.abs(v).toLocaleString('en-US', {maximumFractionDigits: 0});
const fmtC = v => (v < 0 ? '-' : '') + '$' + Math.abs(v).toLocaleString('en-US', {notation: 'compact', maximumFractionDigits: 1});
const t = DATA.totals;
const kpis = [
  {v: fmtUSD(t.net), l: 'Net flow (window)', c: t.net >= 0 ? 'pos' : 'neg'},
  {v: fmtC(t.inflow), l: 'Total inflow'},
  {v: fmtC(t.outflow), l: 'Total outflow'},
  {v: DATA.exchanges.length, l: 'Exchanges tracked'},
  {v: DATA.n_transfers.toLocaleString(), l: 'Transfers analysed'},
  {v: DATA.window_days + 'd', l: 'Window'},
];
document.getElementById('kpis').innerHTML = kpis.map(k =>
  `<div class="kpi"><div class="v ${k.c || ''}">${k.v}</div><div class="l">${k.l}</div></div>`).join('');

const PAL = ['#58a6ff', '#3fb950', '#d29922', '#f85149', '#bc8cff', '#39c5cf', '#ff7b72', '#7ee787'];
const axis = {x: {ticks: {color: '#8b949e'}, grid: {color: '#21262d'}},
              y: {ticks: {color: '#8b949e', callback: c => fmtC(c)}, grid: {color: '#21262d'}}};
const legend = {labels: {color: '#c9d1d9'}};

const days = DATA.days;
new Chart(document.getElementById('cNet'), {type: 'bar',
  data: {labels: days, datasets: DATA.exchanges.map((e, i) => ({
    label: e.exchange, backgroundColor: PAL[i % PAL.length],
    data: days.map(d => {const r = DATA.daily.find(x => x.exchange === e.exchange && x.day === d); return r ? r.net_flow_usd : 0;})}))},
  options: {responsive: true, plugins: {legend: legend}, scales: axis}});

new Chart(document.getElementById('cFlow'), {type: 'bar',
  data: {labels: DATA.exchanges.map(e => e.exchange), datasets: [
    {label: 'Inflow (deposits)', data: DATA.exchanges.map(e => e.inflow_usd), backgroundColor: '#3fb950'},
    {label: 'Outflow (withdrawals)', data: DATA.exchanges.map(e => e.outflow_usd), backgroundColor: '#f85149'}]},
  options: {responsive: true, plugins: {legend: legend}, scales: axis}});

new Chart(document.getElementById('cAsset'), {type: 'bar',
  data: {labels: DATA.assets.map(a => a.asset), datasets: [
    {label: 'Inflow', data: DATA.assets.map(a => a.inflow_usd), backgroundColor: '#3fb950'},
    {label: 'Outflow', data: DATA.assets.map(a => a.outflow_usd), backgroundColor: '#f85149'}]},
  options: {indexAxis: 'y', responsive: true, plugins: {legend: legend}, scales: axis}});

let html = '<tr><th>Exchange</th><th>Inflow</th><th>Outflow</th><th>Net</th><th>Transfers</th></tr>';
DATA.exchanges.forEach(e => {html += `<tr><td>${e.exchange}</td><td>${fmtUSD(e.inflow_usd)}</td><td>${fmtUSD(e.outflow_usd)}</td><td class="${e.net_flow_usd >= 0 ? 'pos' : 'neg'}">${fmtUSD(e.net_flow_usd)}</td><td>${e.transfers}</td></tr>`;});
document.getElementById('tExch').innerHTML = html;

document.getElementById('pending').innerHTML =
  DATA.pending.map(p => `<li><b>${p[0]}</b> ${p[1]} <span class="sub">— ${p[2]}</span></li>`).join('');
