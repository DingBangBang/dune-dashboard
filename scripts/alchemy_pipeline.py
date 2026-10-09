#!/usr/bin/env python3
"""Local dashboard pipeline: Alchemy -> aggregates -> CSV -> self-contained HTML.

What it computes (the parts Alchemy can actually support):
  * CEX on-chain net flow (ETH/WETH + major stablecoins) per exchange per day
  * Inflow / outflow / net per exchange over the window
  * Asset breakdown and a raw-transfers sample

What it CANNOT compute (needs a SQL warehouse with curated DEX tables) is
listed explicitly in the generated HTML under "Pending platform" — see
docs/alchemy-local-dashboard.md.

Usage
-----
    conda run -n dune-dashboard python scripts/alchemy_pipeline.py --days 3 --max-pages 3
    conda run -n dune-dashboard python scripts/alchemy_pipeline.py --days 30 --max-pages 50
    conda run -n dune-dashboard python scripts/alchemy_pipeline.py --smoke   # 1 addr, 1 page

Outputs -> dashboard/index.html and dashboard/data/*.csv
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
from collections import defaultdict
from pathlib import Path

from alchemy_client import Alchemy

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "cex_addresses.json"
OUT_DIR = ROOT / "dashboard"
DATA_DIR = OUT_DIR / "data"


def load_config() -> dict:
    return json.loads(CONFIG.read_text())


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--days", type=int, default=7, help="window length in days (default 7)")
    p.add_argument("--max-pages", type=int, default=5, help="max transfer pages per address/direction")
    p.add_argument("--exchanges", type=str, default="", help="comma list to restrict exchanges")
    p.add_argument("--smoke", action="store_true", help="1 address, 1 page (fast connectivity test)")
    return p.parse_args()


def day_of(iso_ts: str | None) -> str | None:
    return iso_ts[:10] if iso_ts else None


def fetch_prices(client: Alchemy, days: int) -> tuple[dict[str, float], dict[str, float]]:
    """Return (daily_eth_price_by_date, latest_price_by_symbol)."""
    end = dt.datetime.now(dt.timezone.utc)
    start = end - dt.timedelta(days=days + 1)
    daily: dict[str, float] = {}
    hist = client.historical_prices(
        "ETH", start.strftime("%Y-%m-%dT00:00:00Z"), end.strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    for row in hist:
        d = day_of(row.get("timestamp"))
        if d:
            daily[d] = row["value"]
    latest = client.current_prices(["ETH", "USDT", "USDC", "DAI"])
    return daily, latest


def usd_value(asset: str, amount: float, day: str, daily_eth: dict[str, float],
              latest: dict[str, float], stablecoins: set[str]) -> float | None:
    if asset in stablecoins:
        return amount  # 1 stablecoin ~= 1 USD (documented assumption)
    if asset in ("ETH", "WETH"):
        price = daily_eth.get(day) or latest.get("ETH")
        return amount * price if price else None
    return None


def collect(config: dict, client: Alchemy, days: int, max_pages: int,
            only: list[str]) -> list[dict]:
    cutoff = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)).date().isoformat()
    whitelist = set(config["asset_filter"])
    stablecoins = set(config["stablecoins"])
    daily_eth, latest = fetch_prices(client, days)
    print(f"  price rows: {len(daily_eth)} daily ETH points, latest ETH="
          f"{latest.get('ETH', 'n/a')}")

    rows: list[dict] = []
    for exch, addresses in config["exchanges"].items():
        if only and exch not in only:
            continue
        for addr in addresses:
            n = 0
            try:
                transfers = client.asset_transfers(addr, direction="both",
                                                   max_pages=max_pages, stop_before=cutoff)
                for t in transfers:
                    ts = t.get("metadata", {}).get("blockTimestamp")
                    day = day_of(ts)
                    asset = t.get("asset")
                    if not day or day < cutoff or asset not in whitelist:
                        continue
                    amount = float(t.get("value") or 0)
                    if amount <= 0:
                        continue
                    usd = usd_value(asset, amount, day, daily_eth, latest, stablecoins)
                    rows.append({
                        "exchange": exch,
                        "address": addr,
                        "day": day,
                        "direction": t["_direction"],
                        "asset": asset,
                        "amount": amount,
                        "usd": round(usd, 2) if usd is not None else "",
                        "tx_hash": t.get("hash", ""),
                        "category": t.get("category", ""),
                    })
                    n += 1
            except Exception as exc:  # a single bad address must not kill the run
                print(f"  {exch:<10} {addr} -> ERROR: {exc}")
                continue
            print(f"  {exch:<10} {addr} -> {n} transfers in window")
    return rows


def aggregate(rows: list[dict]) -> dict:
    daily: dict[tuple[str, str], dict] = defaultdict(lambda: {"in": 0.0, "out": 0.0, "n": 0})
    exch: dict[str, dict] = defaultdict(lambda: {"in": 0.0, "out": 0.0, "n": 0})
    asset: dict[str, dict] = defaultdict(lambda: {"in": 0.0, "out": 0.0, "amt": 0.0})
    for r in rows:
        usd = float(r["usd"]) if r["usd"] != "" else 0.0
        key = (r["exchange"], r["day"])
        daily[key]["n"] += 1
        exch[r["exchange"]]["n"] += 1
        asset[r["asset"]]["amt"] += r["amount"]
        if r["direction"] == "deposit":
            daily[key]["in"] += usd
            exch[r["exchange"]]["in"] += usd
            asset[r["asset"]]["in"] += usd
        else:
            daily[key]["out"] += usd
            exch[r["exchange"]]["out"] += usd
            asset[r["asset"]]["out"] += usd

    daily_rows = [
        {"exchange": e, "day": d, "inflow_usd": round(v["in"], 2),
         "outflow_usd": round(v["out"], 2), "net_flow_usd": round(v["in"] - v["out"], 2),
         "transfers": v["n"]}
        for (e, d), v in sorted(daily.items(), key=lambda kv: (kv[0][1], kv[0][0]))
    ]
    exch_rows = [
        {"exchange": e, "inflow_usd": round(v["in"], 2), "outflow_usd": round(v["out"], 2),
         "net_flow_usd": round(v["in"] - v["out"], 2), "transfers": v["n"]}
        for e, v in sorted(exch.items(), key=lambda kv: -(kv[1]["in"] + kv[1]["out"]))
    ]
    asset_rows = [
        {"asset": a, "inflow_usd": round(v["in"], 2), "outflow_usd": round(v["out"], 2),
         "net_flow_usd": round(v["in"] - v["out"], 2), "amount": round(v["amt"], 4)}
        for a, v in sorted(asset.items(), key=lambda kv: -(kv[1]["in"] + kv[1]["out"]))
    ]
    total_in = sum(r["inflow_usd"] for r in exch_rows)
    total_out = sum(r["outflow_usd"] for r in exch_rows)
    days = sorted({r["day"] for r in daily_rows})
    return {
        "daily": daily_rows,
        "exchanges": exch_rows,
        "assets": asset_rows,
        "total_inflow_usd": round(total_in, 2),
        "total_outflow_usd": round(total_out, 2),
        "total_net_flow_usd": round(total_in - total_out, 2),
        "days": days,
        "n_transfers": len(rows),
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"  wrote {path.relative_to(ROOT)} ({len(rows)} rows)")


PENDING = [
    ("01", "CEX vs DEX Daily Volume &amp; Ratio", "Needs DEX trade volume (curated dex.trades)."),
    ("03", "DEX Aggregator Market Share", "Needs dex_aggregator.trades (decoded aggregator routes)."),
    ("04", "Token CEX-Listing Impact (±7d)", "Needs per-token DEX swap history."),
    ("05", "Unique Traders per Protocol", "Needs decoded DEX swaps keyed by tx_from."),
    ("07", "DEX Volume by Blockchain", "Needs multi-chain DEX trades."),
    ("08", "Top Token Pairs (30d)", "Needs decoded DEX swaps with token symbols."),
    ("09", "Stablecoin Share of DEX Volume", "Needs DEX swap volume by leg."),
    ("10", "Trade Size Distribution", "Needs per-swap USD size."),
]

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
 body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;margin:0;background:#0d1117;color:#e6edf3}
 header{padding:20px 28px;background:#161b22;border-bottom:1px solid #30363d}
 h1{margin:0 0 4px;font-size:20px}
 .sub{color:#8b949e;font-size:13px}
 .wrap{padding:20px 28px;max-width:1400px;margin:0 auto}
 .kpis{display:flex;gap:14px;flex-wrap:wrap;margin:16px 0 24px}
 .kpi{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:14px 18px;min-width:170px}
 .kpi .v{font-size:22px;font-weight:600}
 .kpi .l{color:#8b949e;font-size:12px;margin-top:4px}
 .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:18px}
 .card{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:16px}
 .card h2{font-size:14px;margin:0 0 10px;color:#c9d1d9;font-weight:600}
 table{width:100%;border-collapse:collapse;font-size:13px}
 th,td{padding:7px 9px;text-align:right;border-bottom:1px solid #21262d}
 th:first-child,td:first-child{text-align:left}
 th{color:#8b949e;font-weight:500}
 .pos{color:#3fb950}.neg{color:#f85149}
 .pending{margin-top:26px;background:#1c1408;border:1px solid #4d3800;border-radius:10px;padding:16px}
 .pending h2{color:#d29922}
 .pending li{margin:4px 0;font-size:13px;color:#c9d1d9}
 code{background:#21262d;padding:1px 5px;border-radius:4px;font-size:12px}
 footer{color:#8b949e;font-size:12px;padding:20px 28px;border-top:1px solid #21262d;margin-top:30px}
 canvas{max-height:320px}
</style></head><body>
<header>
  <h1>__TITLE__</h1>
  <div class="sub">Local dashboard built from the Alchemy Ethereum-mainnet endpoint · window: last __WINDOW__ days · generated __GENERATED__</div>
</header>
<div class="wrap">
  <div class="kpis" id="kpis"></div>
  <div class="grid">
    <div class="card"><h2>Daily net flow by exchange (USD)</h2><canvas id="cNet"></canvas></div>
    <div class="card"><h2>Inflow vs outflow by exchange (USD)</h2><canvas id="cFlow"></canvas></div>
    <div class="card"><h2>Net flow by asset (USD)</h2><canvas id="cAsset"></canvas></div>
    <div class="card"><h2>Exchange summary</h2><table id="tExch"></table></div>
  </div>
  <div class="pending">
    <h2>⏳ Pending platform (needs a SQL warehouse with curated DEX tables)</h2>
    <ul id="pending"></ul>
    <p class="sub">These panels are specified and ready in <code>queries/</code>; they cannot be computed from an RPC/transfers API alone.</p>
  </div>
</div>
<footer>
  Data: Alchemy Transfers + Prices API (Ethereum mainnet). USD = stablecoins at $1.00 · ETH/WETH at daily close.
  Address list: <code>config/cex_addresses.json</code> (illustrative — verify before trusting). Transfers fetched: __N__.
</footer>
<script>const DATA = __DATA__;</script>
<script src="dashboard.js"></script>
</body></html>
"""

JS_TEMPLATE = r"""const fmtUSD = v => (v < 0 ? '-' : '') + '$' + Math.abs(v).toLocaleString('en-US', {maximumFractionDigits: 0});
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
"""


def render_html(agg: dict, window_days: int, calls: int) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "days": agg["days"],
        "daily": agg["daily"],
        "exchanges": agg["exchanges"],
        "assets": agg["assets"],
        "totals": {"inflow": agg["total_inflow_usd"], "outflow": agg["total_outflow_usd"],
                   "net": agg["total_net_flow_usd"]},
        "n_transfers": agg["n_transfers"],
        "window_days": window_days,
        "pending": PENDING,
    }
    html = (HTML_TEMPLATE
            .replace("__TITLE__", "Exchange Market Share Tracker — Local (Alchemy)")
            .replace("__WINDOW__", str(window_days))
            .replace("__GENERATED__", dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
            .replace("__N__", str(agg["n_transfers"]))
            .replace("__DATA__", json.dumps(payload)))
    (OUT_DIR / "index.html").write_text(html)
    (OUT_DIR / "dashboard.js").write_text(JS_TEMPLATE)
    print(f"  wrote {(OUT_DIR / 'index.html').relative_to(ROOT)}")
    print(f"  wrote {(OUT_DIR / 'dashboard.js').relative_to(ROOT)}")


def main() -> int:
    args = parse_args()
    cfg = load_config()
    only = [x.strip() for x in args.exchanges.split(",") if x.strip()]
    days, max_pages = args.days, args.max_pages
    if args.smoke:
        days, max_pages = 1, 1
        first = next(iter(cfg["exchanges"]))
        only = [first]
        cfg = {**cfg, "exchanges": {first: cfg["exchanges"][first][:1]}}
    print(f"Alchemy local pipeline · window={days}d · max_pages={max_pages} · "
          f"exchanges={only or 'all'}")

    client = Alchemy()
    print(f"  endpoint reachable, latest block = {client.block_number()}")
    rows = collect(cfg, client, days, max_pages, only)
    agg = aggregate(rows)

    write_csv(DATA_DIR / "net_flow_daily.csv", agg["daily"])
    write_csv(DATA_DIR / "exchange_summary.csv", agg["exchanges"])
    write_csv(DATA_DIR / "asset_breakdown.csv", agg["assets"])
    write_csv(DATA_DIR / "transfers_sample.csv", rows[:500])
    render_html(agg, days, client.calls)

    print("\n=== SUMMARY ===")
    print(f"  transfers : {agg['n_transfers']}")
    print(f"  inflow    : ${agg['total_inflow_usd']:,.2f}")
    print(f"  outflow   : ${agg['total_outflow_usd']:,.2f}")
    print(f"  net flow  : ${agg['total_net_flow_usd']:,.2f}")
    print(f"  API calls : {client.calls}")
    print(f"\nOpen: {(OUT_DIR / 'index.html').resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



