#!/usr/bin/env python3
"""Run the Chainbase historical-snapshot queries and save their results.

Reads queries/chainbase/*.sql, substitutes {{PLACEHOLDERS}} from
config/chainbase_targets.json + config/cex_addresses.json, executes each against
the Chainbase SQL API, and writes:

  dashboard/data/chainbase/NN_*.csv        per-query CSV (git-ignored)
  dashboard/chainbase_data.json            all results + metadata for the hub

The free tier rate-limits hard, so every query is submitted and polled with
back-off (handled inside Chainbase client). Expect several minutes for all ten.

Usage:
    conda run -n dune_dashboard python scripts/chainbase_pipeline.py
    conda run -n dune_dashboard python scripts/chainbase_pipeline.py --only 02,06
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import sys
from pathlib import Path

from chainbase_client import Chainbase

ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = ROOT / "queries" / "chainbase"
OUT_DIR = ROOT / "dashboard"
DATA_DIR = OUT_DIR / "data" / "chainbase"

TITLES = {
    "01": "CEX vs DEX daily volume & ratio",
    "02": "Exchange net flow (daily)",
    "03": "DEX aggregator market share (monthly)",
    "04": "Token listing impact (±7d)",
    "05": "Unique senders / activity (daily)",
    "06": "CEX inflow/outflow by exchange",
    "07": "DEX-routed volume by chain",
    "08": "Top tokens by volume",
    "09": "Stablecoin share of volume",
    "10": "Trade size distribution",
}


def qlist(items: list[str]) -> str:
    return ", ".join("'" + str(i).strip().lower() + "'" for i in items)


def build_placeholders() -> dict[str, str]:
    tgt = json.loads((ROOT / "config" / "chainbase_targets.json").read_text())
    cex = json.loads((ROOT / "config" / "cex_addresses.json").read_text())
    w = tgt["window"]
    ex = cex["exchanges"]
    all_cex = [a for addrs in ex.values() for a in addrs]
    aggs = tgt["aggregators"]
    ph = {
        "WINDOW_START": w["start"],
        "WINDOW_END": w["end"],
        "WINDOW_LONG_START": w["long_start"],
        "LISTING_TOKEN": w["listing_token"],
        "LISTING_DATE": w["listing_date"],
        "CEX_ADDRESSES": qlist(all_cex),
        "DEX_ROUTERS": qlist(tgt["dex_routers"]),
        "AGGREGATORS": qlist([a for v in aggs.values() for a in v]),
        "STABLECOINS": ", ".join("'" + s.upper() + "'" for s in tgt["stablecoins"]),
    }
    for name, addrs in ex.items():
        ph[f"EX_{name.upper()}"] = qlist(addrs)
    for name, addrs in aggs.items():
        ph[f"AGG_{name.upper().replace('0X', '0X')}"] = qlist(addrs)
    return ph


def substitute(sql: str, ph: dict[str, str]) -> str:
    for key, val in ph.items():
        sql = sql.replace("{{" + key + "}}", val)
    leftover = re.findall(r"\{\{[A-Z0-9_]+\}\}", sql)
    if leftover:
        raise ValueError(f"unsubstituted placeholders: {sorted(set(leftover))}")
    # The Chainbase (MySQL/Doris) engine rejects a trailing semicolon.
    sql = sql.strip()
    while sql.endswith(";"):
        sql = sql[:-1].rstrip()
    return sql


def rows_to_dicts(columns: list[str], rows: list) -> list[dict]:
    return [dict(zip(columns, r)) for r in rows]


def write_csv(path: Path, columns: list[str], rows: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        w = csv.writer(fh)
        if columns:
            w.writerow(columns)
        w.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", default="", help="comma list of query prefixes, e.g. 02,06")
    args = ap.parse_args()
    only = [x.strip() for x in args.only.split(",") if x.strip()]

    ph = build_placeholders()
    cb = Chainbase()
    files = sorted(SQL_DIR.glob("*.sql"))
    if only:
        files = [f for f in files if f.name[:2] in only]

    payload = {
        "source": "Chainbase Data Cloud (ethereum.onchain_trades / bsc.onchain_trades)",
        "snapshot_end": ph["WINDOW_END"],
        "window_start": ph["WINDOW_START"],
        "generated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "queries": {},
    }

    for f in files:
        qid = f.name[:2]
        raw = f.read_text()
        sql = substitute(raw, ph)
        print(f"\n=== {f.name} :: {TITLES.get(qid, '')} ===", flush=True)
        entry = {"id": qid, "file": f.name, "title": TITLES.get(qid, ""), "status": "ok"}
        try:
            out = cb.run(sql)
            entry["columns"] = out["columns"]
            entry["rows"] = rows_to_dicts(out["columns"], out["rows"])
            entry["row_count"] = out["meta"].get("total_row_count")
            print(f"  rows={entry['row_count']} cols={out['columns']}", flush=True)
            write_csv(DATA_DIR / f"{qid}_{f.stem[3:]}.csv", out["columns"], out["rows"])
        except Exception as exc:  # keep going; record the failure
            entry["status"] = "error"
            entry["error"] = str(exc)[:400]
            print(f"  ERROR: {exc}", file=sys.stderr, flush=True)
        payload["queries"][qid] = entry
        # persist after each query so a crash still leaves partial results
        (OUT_DIR / "chainbase_data.json").write_text(json.dumps(payload, indent=2))

    ok = sum(1 for q in payload["queries"].values() if q["status"] == "ok")
    print(f"\n=== done: {ok}/{len(payload['queries'])} queries succeeded; "
          f"API calls={cb.calls} ===")
    print(f"wrote {(OUT_DIR / 'chainbase_data.json').relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
