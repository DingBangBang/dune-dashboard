# Chainbase Historical-Snapshot Board (Tab 2)

The second board of the hub. **Platform: Chainbase Data Cloud. Data: a frozen
snapshot ending `2025-04-24`.** It is *not* live and must not be compared
day-for-day with the Alchemy board (Tab 1).

---

## 1. What it is

`scripts/chainbase_pipeline.py` runs the ten SQL files in `queries/chainbase/`
against the Chainbase SQL API and stores the results in
`dashboard/chainbase_data.json`. `scripts/build_hub.py` renders them as Tab 2.

All ten original panels are present:

| # | Panel | Status on Chainbase |
| --- | --- | --- |
| 01 | CEX vs DEX daily volume & ratio | ✅ (DEX side = router-address proxy) |
| 02 | Exchange net flow | ✅ |
| 03 | Aggregator market share (monthly) | ✅ (aggregator-router proxy) |
| 04 | Token listing impact (±7d) | ✅ (listing date is configurable) |
| 05 | Unique senders / activity | ✅ (sender proxy for traders) |
| 06 | CEX inflow/outflow by exchange | ✅ |
| 07 | DEX-routed volume by chain | ✅ (ethereum + bsc) |
| 08 | Top tokens by volume | ⚠️ adapted from "top token pairs" |
| 09 | Stablecoin share of volume | ✅ |
| 10 | Trade size distribution | ✅ |

---

## 2. Platform facts (verified)

```
POST https://api.chainbase.com/api/v1/query/execute   {"sql": "..."}   header X-API-KEY
  -> {"code":200,"data":[{"executionId":"...","status":"PENDING"}]}
GET  https://api.chainbase.com/api/v1/execution/{id}/status
GET  https://api.chainbase.com/api/v1/execution/{id}/results
```

* Engine is **MySQL/Doris-compatible** (error code 1064 HY000) — use MySQL syntax
  (`date()`, `date_format()`, `datediff()`, `interval N day`), not Trino.
* The table used throughout is **`ethereum.onchain_trades`** (columns:
  `block_timestamp, transaction_hash, token_address, from_address, to_address,
  value, operation, amount, usd_value, symbol, name, ust_value_timestamp`).
* `operation` ∈ {`Transfer`, `NativeTransfer`} — there is **no swap flag**.
* Data ends **2025-04-24 14:59:59 UTC** (110M `Transfer` + 24M `NativeTransfer`
  rows over ~2 months). Only `ethereum` and `bsc` have this table.
* The free tier **rate-limits hard** (HTTP 429; ~20 s back-off per retry), so a
  full 10-query run takes several minutes.

---

## 3. Proxies & caveats (important)

Because `onchain_trades` records token/native **movements**, not decoded swaps:

* **DEX volume** = USD value of transfers touching a curated list of **DEX router**
  addresses (`config/chainbase_targets.json`). This is a proxy, not true swap volume.
* **Aggregator share** = transfers touching a curated list of aggregator router
  contracts (1inch, 0x, CoW Swap, ParaSwap).
* **Unique traders** = `count(distinct from_address)` (no `tx_from` in the table).
* **Top token pairs (08)** cannot be reconstructed (one token per row), so it is
  shown as **top tokens by volume**.
* **USD** comes from the table's own `usd_value` column.

Addresses and windows live in `config/chainbase_targets.json` — edit and re-run.

---

## 4. Run it

```bash
# full run (~several minutes due to rate limits)
conda run -n dune_dashboard python scripts/chainbase_pipeline.py

# subset
conda run -n dune_dashboard python scripts/chainbase_pipeline.py --only 02,06
```

Outputs:

```
dashboard/chainbase_data.json          # all results (drives Tab 2)
dashboard/data/chainbase/NN_*.csv      # per-query CSVs (git-ignored)
```

Then rebuild the hub: `python scripts/build_hub.py`.
