#!/usr/bin/env python3
"""Chainbase Data Cloud SQL API client (free tier).

Flow:  POST /query/execute  -> executionId
       GET  /execution/{id}/status  -> FINISHED
       GET  /execution/{id}/results -> columns + rows

Auth header: ``X-API-KEY``. The free tier rate-limits bursts with HTTP 429, so
every call retries with back-off.

Key is read from env ``CHAINBASE_API_KEY`` or ``chainbase_API_key.txt``.

CLI:
    conda run -n dune_dashboard python scripts/chainbase_client.py "SELECT 1 AS x"
    conda run -n dune_dashboard python scripts/chainbase_client.py --tables
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://api.chainbase.com/api/v1"


def load_key() -> str:
    key = os.getenv("CHAINBASE_API_KEY")
    if key:
        return key.strip()
    f = ROOT / "chainbase_API_key.txt"
    if f.exists():
        return f.read_text().strip()
    raise RuntimeError("No Chainbase API key (set CHAINBASE_API_KEY or add chainbase_API_key.txt)")


class ChainbaseError(RuntimeError):
    pass


class Chainbase:
    def __init__(self, key: str | None = None, verbose: bool = True,
                 backoff: float = 20.0, max_retries: int = 8) -> None:
        self.key = key or load_key()
        self.verbose = verbose
        self.backoff = backoff
        self.max_retries = max_retries
        self.calls = 0

    def _headers(self) -> dict:
        return {"X-API-KEY": self.key, "Content-Type": "application/json"}

    def _request(self, method: str, path: str, **kw) -> dict:
        url = f"{BASE}{path}"
        last = None
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = requests.request(method, url, headers=self._headers(),
                                        timeout=90, **kw)
                self.calls += 1
                if resp.status_code == 429 or resp.status_code == 503:
                    wait = self.backoff
                    if self.verbose:
                        print(f"  [429] rate limited, back-off {wait:.0f}s "
                              f"(attempt {attempt}/{self.max_retries})", file=sys.stderr)
                    time.sleep(wait)
                    continue
                if resp.status_code >= 400:
                    raise ChainbaseError(f"HTTP {resp.status_code}: {resp.text[:200]}")
                data = resp.json()
                if data.get("code") == 429:
                    time.sleep(self.backoff)
                    continue
                return data
            except requests.RequestException as exc:
                last = exc
                if attempt == self.max_retries:
                    break
                time.sleep(min(2 ** attempt, 30))
        raise ChainbaseError(f"{method} {path} failed: {last}")

    # -- API ---------------------------------------------------------------
    def submit(self, sql: str) -> str:
        data = self._request("POST", "/query/execute", json={"sql": sql})
        rows = data.get("data") or []
        if not rows:
            raise ChainbaseError(f"no executionId: {json.dumps(data)[:200]}")
        return rows[0]["executionId"]

    def status(self, eid: str) -> dict:
        data = self._request("GET", f"/execution/{eid}/status")
        rows = data.get("data") or [{}]
        return rows[0]

    def results(self, eid: str) -> dict:
        data = self._request("GET", f"/execution/{eid}/results")
        return data.get("data") or {}

    def run(self, sql: str, poll: float = 3.0, timeout: float = 180.0) -> dict:
        """Submit, poll, and return {'columns':[...], 'rows':[[...]], 'meta':{...}}."""
        eid = self.submit(sql)
        deadline = time.time() + timeout
        st: dict = {}
        while time.time() < deadline:
            st = self.status(eid)
            if st.get("status") in ("FINISHED", "FAILED", "CANCELLED"):
                break
            time.sleep(poll)
        else:
            raise ChainbaseError(f"timeout waiting for {eid}")
        if st.get("status") != "FINISHED":
            raise ChainbaseError(
                f"query {st.get('status')}: {str(st.get('message'))[:400]} (eid={eid})")
        res = self.results(eid)
        return {
            "columns": [c["name"] for c in res.get("columns", [])],
            "rows": res.get("data", []),
            "meta": {k: res.get(k) for k in
                     ("status", "total_row_count", "execution_time_millis", "message")},
        }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("sql", nargs="?", help="SQL to execute")
    ap.add_argument("--tables", action="store_true", help="list catalog tables")
    args = ap.parse_args()

    cb = Chainbase()
    if args.tables:
        sql = ("SELECT table_schema, table_name FROM information_schema.tables "
               "ORDER BY table_schema, table_name LIMIT 500")
    elif args.sql:
        sql = args.sql
    else:
        ap.error("provide SQL or --tables")

    out = cb.run(sql)
    print("columns:", out["columns"])
    print("meta   :", out["meta"])
    for row in out["rows"][:60]:
        print("  ", row)
    if len(out["rows"]) > 60:
        print(f"  ... ({len(out['rows'])} rows total)")
    print(f"API calls: {cb.calls}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
