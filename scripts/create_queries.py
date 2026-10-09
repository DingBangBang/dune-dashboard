#!/usr/bin/env python3
"""Create every SQL file in ``queries/`` as a saved Dune query via the Dune API.

This is the closest thing to "building the Dashboard programmatically": the Dune
Data API can create/update queries (and execute them), but it cannot assemble
Dashboard *widgets* — that final layout step is done in the Dune UI. See
``docs/dashboard_guide.md`` for the UI steps.

Usage
-----
    # 1. Put your API key in .env  (copy .env.example -> .env)
    # 2. run inside the conda env
    conda run -n dune_dashboard python scripts/create_queries.py --dry-run
    conda run -n dune_dashboard python scripts/create_queries.py

It writes ``queries/dune_query_ids.json`` mapping each local file to the Dune
query id + public URL, which you then add as Dashboard widgets.

Notes
-----
* Requires a Dune **Analyst plan or higher** (Query CRUD endpoints).
* The API key is read from the ``DUNE_API_KEY`` env var or a local ``.env``.
* Re-running updates existing queries instead of duplicating them, using the
  id stored in ``queries/dune_query_ids.json``.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
QUERIES_DIR = ROOT / "queries"
IDS_FILE = QUERIES_DIR / "dune_query_ids.json"
API_BASE = "https://api.dune.com/api/v1"

# Query parameters that must be declared when the query is created.
# Keyed by SQL file name. `value` is the default value shown in the editor.
PARAMETERS: dict[str, list[dict]] = {
    "04_token_listing_impact.sql": [
        {"key": "token_symbol", "type": "text", "value": "PEPE"},
        {"key": "listing_date", "type": "text", "value": "2023-05-05"},
    ],
}

# Friendly, dashboard-ready titles per file.
TITLES: dict[str, str] = {
    "01_cex_dex_ratio.sql": "01 · CEX vs DEX Daily Volume & Ratio",
    "02_exchange_net_flow.sql": "02 · Exchange Net Flow (ETH/USDT)",
    "03_aggregator_market_share.sql": "03 · DEX Aggregator Market Share",
    "04_token_listing_impact.sql": "04 · Token CEX-Listing Impact (±7d)",
    "05_unique_traders.sql": "05 · Unique Traders per Protocol",
    "06_cex_flow_by_exchange.sql": "06 · CEX Inflow/Outflow by Exchange",
    "07_dex_volume_by_chain.sql": "07 · DEX Volume by Blockchain",
    "08_top_token_pairs.sql": "08 · Top Token Pairs (30d)",
    "09_stablecoin_share.sql": "09 · Stablecoin Share of DEX Volume",
    "10_trade_size_distribution.sql": "10 · Trade Size Distribution",
}


def load_api_key() -> str | None:
    """Return the Dune API key from env or a local .env file."""
    key = os.getenv("DUNE_API_KEY")
    if key:
        return key.strip()
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line.startswith("DUNE_API_KEY"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def load_ids() -> dict:
    if IDS_FILE.exists():
        try:
            return json.loads(IDS_FILE.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def save_ids(ids: dict) -> None:
    IDS_FILE.write_text(json.dumps(ids, indent=2, ensure_ascii=False) + "\n")


def create_query(api_key: str, name: str, sql: str, params: list[dict]) -> dict:
    resp = requests.post(
        f"{API_BASE}/query",
        headers={"X-DUNE-API-KEY": api_key, "Content-Type": "application/json"},
        json={
            "name": name,
            "description": "Created by dune-dashboard/scripts/create_queries.py",
            "query_sql": sql,
            "parameters": params,
            "is_private": False,
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def update_query(api_key: str, query_id: int, name: str, sql: str, params: list[dict]) -> dict:
    resp = requests.patch(
        f"{API_BASE}/query/{query_id}",
        headers={"X-DUNE-API-KEY": api_key, "Content-Type": "application/json"},
        json={"name": name, "query_sql": sql, "parameters": params},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="print actions only")
    args = parser.parse_args()

    files = sorted(glob.glob(str(QUERIES_DIR / "*.sql")))
    if not files:
        print("No .sql files found in queries/", file=sys.stderr)
        return 1

    api_key = load_api_key()
    if not api_key and not args.dry_run:
        print(
            "ERROR: DUNE_API_KEY not set. Copy .env.example to .env and add your key,\n"
            "       or export DUNE_API_KEY=...  (Or run with --dry-run to preview.)",
            file=sys.stderr,
        )
        return 2

    ids = load_ids()
    for path in files:
        fname = os.path.basename(path)
        sql = Path(path).read_text()
        name = TITLES.get(fname, fname)
        params = PARAMETERS.get(fname, [])

        if args.dry_run:
            existing = ids.get(fname, {}).get("query_id")
            action = f"UPDATE #{existing}" if existing else "CREATE"
            print(f"[dry-run] {action:>12} :: {fname} -> '{name}' (params={len(params)})")
            continue

        existing = ids.get(fname, {}).get("query_id")
        try:
            if existing:
                payload = update_query(api_key, int(existing), name, sql, params)
                print(f"[update] {fname} -> query #{existing}")
            else:
                payload = create_query(api_key, name, sql, params)
                print(f"[create] {fname} -> query #{payload.get('query_id')}")
            qid = payload.get("query_id", existing)
            ids[fname] = {
                "query_id": qid,
                "name": name,
                "url": f"https://dune.com/queries/{qid}",
            }
            save_ids(ids)
        except requests.HTTPError as exc:
            body = exc.response.text[:300] if exc.response is not None else ""
            print(f"[FAILED] {fname}: {exc} :: {body}", file=sys.stderr)

    if not args.dry_run:
        print(f"\nSaved id map -> {IDS_FILE.relative_to(ROOT)}")
        print("Next: open each query URL, pick a visualization, click "
              "'Add to Dashboard', then follow docs/dashboard_guide.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
