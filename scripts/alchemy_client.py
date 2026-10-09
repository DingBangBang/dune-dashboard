#!/usr/bin/env python3
"""Minimal Alchemy client for the local dashboard pipeline.

Covers only what this project needs:
  * JSON-RPC over the Ethereum-mainnet endpoint (``eth_blockNumber`` etc.)
  * ``alchemy_getAssetTransfers`` with pagination
  * Prices API (historical daily prices) for USD conversion

Credentials are read from, in order:
  1. env vars ``ALCHEMY_API_KEY`` / ``ALCHEMY_RPC_URL``
  2. the credential .txt files in the repo root
     (``flipside_cypto_API_ley.txt``, ``etherum_endpoint_url.txt``)

The credential files are git-ignored. Never hardcode or commit the key.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Iterator

import requests

ROOT = Path(__file__).resolve().parents[1]
PRICES_BASE = "https://api.g.alchemy.com/prices/v1"


def load_rpc_url() -> str:
    url = os.getenv("ALCHEMY_RPC_URL")
    if url:
        return url.strip()
    f = ROOT / "etherum_endpoint_url.txt"
    if f.exists():
        return f.read_text().strip()
    key = os.getenv("ALCHEMY_API_KEY")
    if key:
        return f"https://eth-mainnet.g.alchemy.com/v2/{key.strip()}"
    raise RuntimeError(
        "No Alchemy RPC URL. Set ALCHEMY_RPC_URL / ALCHEMY_API_KEY, or place "
        "etherum_endpoint_url.txt in the repo root."
    )


def api_key_from_url(url: str) -> str:
    """Extract the key from .../v2/<key>."""
    tail = url.rstrip("/").split("/")
    return tail[-1] if tail else ""


class AlchemyError(RuntimeError):
    pass


class Alchemy:
    """Tiny, polite Alchemy client (free tier: 15 RPS)."""

    def __init__(self, rpc_url: str | None = None, min_interval: float = 0.10,
                 max_retries: int = 5, verbose: bool = True) -> None:
        self.rpc_url = rpc_url or load_rpc_url()
        self.api_key = api_key_from_url(self.rpc_url)
        self.min_interval = min_interval  # ~10 RPS, safely under the 15 RPS cap
        self.max_retries = max_retries
        self.verbose = verbose
        self._last = 0.0
        self._id = 0
        self.calls = 0

    # -- internals ---------------------------------------------------------
    def _throttle(self) -> None:
        delta = time.time() - self._last
        if delta < self.min_interval:
            time.sleep(self.min_interval - delta)
        self._last = time.time()

    def rpc(self, method: str, params: list[Any]) -> Any:
        self._id += 1
        payload = {"jsonrpc": "2.0", "id": self._id, "method": method, "params": params}
        body = json.dumps(payload)
        last_err: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            self._throttle()
            try:
                resp = requests.post(
                    self.rpc_url,
                    data=body,
                    headers={"Content-Type": "application/json"},
                    timeout=60,
                )
                self.calls += 1
                if resp.status_code == 429:
                    wait = min(2 ** attempt, 20)
                    if self.verbose:
                        print(f"    [429] rate limited, sleeping {wait}s")
                    time.sleep(wait)
                    continue
                if resp.status_code >= 400:
                    raise AlchemyError(f"HTTP {resp.status_code}: {resp.text[:200]}")
                data = resp.json()
                if "error" in data:
                    raise AlchemyError(str(data["error"]))
                return data.get("result")
            except (requests.RequestException, AlchemyError) as exc:
                last_err = exc
                if attempt == self.max_retries:
                    break
                time.sleep(min(2 ** attempt, 15))
        raise AlchemyError(f"{method} failed after {self.max_retries} tries: {last_err}")

    # -- public API --------------------------------------------------------
    def block_number(self) -> int:
        return int(self.rpc("eth_blockNumber", []), 16)

    def asset_transfers(
        self,
        address: str,
        direction: str = "both",
        categories: tuple[str, ...] = ("external", "erc20"),
        max_pages: int = 20,
        page_size: int = 1000,
        stop_before: str | None = None,
    ) -> Iterator[dict]:
        """Yield transfers touching ``address``, newest-first.

        ``direction``: "to" (deposits into the wallet), "from" (withdrawals),
        or "both" (two scans). ``stop_before`` is an ISO-8601 date string; paging
        stops as soon as a transfer is older than it.
        """
        directions = ["to", "from"] if direction == "both" else [direction]
        for d in directions:
            page_key: str | None = None
            for _ in range(max_pages):
                params: dict[str, Any] = {
                    "fromBlock": "0x0",
                    "toBlock": "latest",
                    "category": list(categories),
                    "withMetadata": True,
                    "excludeZeroValue": True,
                    "maxCount": hex(page_size),
                    "order": "desc",
                }
                if d == "to":
                    params["toAddress"] = address
                else:
                    params["fromAddress"] = address
                if page_key:
                    params["pageKey"] = page_key
                try:
                    result = self.rpc("alchemy_getAssetTransfers", [params]) or {}
                except AlchemyError as exc:
                    # A stale/invalid pageKey is the usual 400 cause. Never let one
                    # bad page abort the whole address: stop paging this direction.
                    if page_key:
                        if self.verbose:
                            print(f"    [warn] paging stopped (dir={d} "
                                  f"{address[:10]}…): {exc}")
                        break
                    raise
                transfers = result.get("transfers", [])
                for t in transfers:
                    t["_direction"] = "deposit" if d == "to" else "withdrawal"
                    yield t
                ts_list = [t.get("metadata", {}).get("blockTimestamp") for t in transfers]
                oldest = min([x for x in ts_list if x], default=None)
                page_key = result.get("pageKey")
                if not transfers or not page_key:
                    break
                if stop_before and oldest and oldest < stop_before:
                    break

    def historical_prices(self, symbol: str, start_time: str, end_time: str) -> list[dict]:
        """Daily USD prices for ``symbol``. Returns [{'timestamp':..,'value':float}].

        Alchemy's endpoint requires a **POST with a JSON body** (not query params):
        ``POST /prices/v1/{key}/tokens/historical`` with
        ``{"symbol":.., "startTime":ISO, "endTime":ISO}``.
        Returns [] on any failure so the pipeline can degrade gracefully.
        """
        url = f"{PRICES_BASE}/{self.api_key}/tokens/historical"
        body = {"symbol": symbol, "startTime": start_time, "endTime": end_time}
        for attempt in range(1, self.max_retries + 1):
            self._throttle()
            try:
                resp = requests.post(url, json=body, timeout=60)
                self.calls += 1
                if resp.status_code == 429:
                    time.sleep(min(2 ** attempt, 20))
                    continue
                resp.raise_for_status()
                data = resp.json()
                out: list[dict] = []
                for p in data.get("data", []):
                    ts, val = p.get("timestamp"), p.get("value")
                    if ts is not None and val is not None:
                        out.append({"timestamp": ts, "value": float(val)})
                return out
            except (requests.RequestException, ValueError, KeyError):
                if attempt == self.max_retries:
                    return []
                time.sleep(min(2 ** attempt, 10))
        return []


    def current_prices(self, symbols: list[str]) -> dict[str, float]:
        """Latest USD price per symbol (fallback when historical is unavailable)."""
        url = f"{PRICES_BASE}/{self.api_key}/tokens/by-symbol"
        params = [("symbols", s) for s in symbols]
        try:
            self._throttle()
            resp = requests.get(url, params=params, timeout=60)
            self.calls += 1
            resp.raise_for_status()
            prices: dict[str, float] = {}
            for row in resp.json().get("data", []):
                sym = row.get("symbol")
                for p in row.get("prices", []):
                    if p.get("currency", "usd") == "usd":
                        prices[sym] = float(p.get("value"))
            return prices
        except (requests.RequestException, ValueError, KeyError):
            return {}

