# Query Catalog & Panel Mapping

The authoritative mapping between **SQL file → Dune query → visualization → panel**.
Use it as the build checklist for the dashboard.

**Dune workspace:** <https://dune.com/workspace/t/bonnieting/home>
**Live dashboard:** `https://dune.com/bonnieting/exchange-market-share-tracker` _(placeholder)_

---

## Summary

| Local file | Dune query id | Table(s) | Grain | Range | Default viz |
| --- | --- | --- | --- | --- | --- |
| `01_cex_dex_ratio.sql` | _TBD_ | `dex.trades`, `cex.flows` | day | 90d | Mixed bar+line |
| `02_exchange_net_flow.sql` | _TBD_ | `cex.flows` | exchange × day | 90d | Grouped bar |
| `03_aggregator_market_share.sql` | _TBD_ | `dex_aggregator.trades` | month × project | 365d | Stacked area |
| `04_token_listing_impact.sql` | _TBD_ | `dex.trades` | day (±7d) | ±7d | Line (param) |
| `05_unique_traders.sql` | _TBD_ | `dex.trades` | day × project | 90d | Multi-line |
| `06_cex_flow_by_exchange.sql` | _TBD_ | `cex.flows` | exchange | 90d | Horizontal bar |
| `07_dex_volume_by_chain.sql` | _TBD_ | `dex.trades` | week × chain | 180d | Stacked area |
| `08_top_token_pairs.sql` | _TBD_ | `dex.trades` | token_pair | 30d | Table + bar |
| `09_stablecoin_share.sql` | _TBD_ | `dex.trades` | day | 90d | Line |
| `10_trade_size_distribution.sql` | _TBD_ | `dex.trades` | week × bucket | 90d | Stacked bar 100% |

> `_TBD_` values are filled automatically in `queries/dune_query_ids.json` when you
> run `scripts/create_queries.py`.

---

## Panel-by-panel detail

### Panel 1 — CEX vs DEX daily volume & ratio
* **Query:** `01_cex_dex_ratio.sql`
* **Viz:** Mixed chart — `dex_volume_usd` & `cex_onchain_volume_usd` as bars
  (left axis), `cex_dex_ratio` as a line (right axis).
* **X:** `day` · **Y:** volumes + ratio
* **Read it as:** structural on-chain vs CEX-rail activity.

### Panel 2 — CEX/DEX ratio counter
* **Query:** `01_...` (same query, second visualization)
* **Viz:** Counter on the latest `cex_dex_ratio` value.
* **Purpose:** a single headline number for the hero row.

### Panel 3 — Exchange net flow
* **Query:** `02_exchange_net_flow.sql`
* **Viz:** Grouped bar, **X** `day`, **Y** `net_flow_usd`, **Group** `exchange_name`.
* **Read it as:** which venues are bleeding/absorbing coins.

### Panel 4 — Net-flow table
* **Query:** `02_...` · **Viz:** Table (all columns), sorted by `day desc`.

### Panel 5 — Aggregator market share
* **Query:** `03_aggregator_market_share.sql`
* **Viz:** Stacked Area, **X** `month`, **Y** `volume_usd`, **Series** `project`.

### Panel 6 — Aggregator share table
* **Query:** `03_...` · **Viz:** Table — `month, project, volume_usd,
  market_share_pct, mom_growth_pct`; format `*_pct` columns as percentages.

### Panel 7 — Token listing impact
* **Query:** `04_token_listing_impact.sql` (parameters)
* **Viz:** Line, **X** `day_offset`, **Y** `dex_volume_usd`,
  `trailing14d_avg_usd`, `forward14d_avg_usd`.

### Panel 8 — Unique traders
* **Query:** `05_unique_traders.sql`
* **Viz:** Multiple-series Line, **X** `day`, **Y** `unique_traders`, **Series** `project`.

### Panel 9 — Trading intensity
* **Query:** `05_...` · **Viz:** Line, **Y** `trades_per_trader`, **Series** `project`.
* **Read it as:** a spike = bot/MEV, not retail growth.

### Panel 10 — CEX inflow/outflow leaderboard
* **Query:** `06_cex_flow_by_exchange.sql`
* **Viz:** Horizontal Bar, **Category** `exchange_name`, **Value** `net_flow_usd`.

### Panel 11 — CEX flow table
* **Query:** `06_...` · **Viz:** Table (all columns).

### Panel 12 — DEX volume by chain
* **Query:** `07_dex_volume_by_chain.sql`
* **Viz:** Stacked Area, **X** `week`, **Y** `volume_usd`, **Series** `blockchain`.

### Panel 13 — Chain share
* **Query:** `07_...` · **Viz:** Line, **Y** `chain_share_pct`, **Series** `blockchain`.

### Panel 14 — Top token pairs
* **Query:** `08_top_token_pairs.sql` · **Viz:** Table (top 50).

### Panel 15 — Top pairs volume
* **Query:** `08_...` · **Viz:** Bar, **X** `token_pair`, **Y** `volume_usd`.

### Panel 16 — Stablecoin share
* **Query:** `09_stablecoin_share.sql`
* **Viz:** Line, **Y** `stablecoin_share_pct` and `share_7d_ma`.

### Panel 17 — Volume by trade size
* **Query:** `10_trade_size_distribution.sql`
* **Viz:** Stacked Bar (100%), **X** `week`, **Y** `volume_share_pct`, **Series** `size_bucket`.

### Panel 18 — Count by trade size
* **Query:** `10_...` · **Viz:** Stacked Bar (100%), **Y** `trade_count_share_pct`.

### Panels 19–20 — Text widgets
* Section headers / methodology note (Markdown). See `docs/dashboard_guide.md`.

---

## Filters applied

| Scope | Filter | Value |
| --- | --- | --- |
| SQL | `block_month >=` | `date_trunc('month', current_date - INTERVAL '90' DAY)` (deep-history queries use 180/365) |
| Dashboard | Time range | **Last 90 days** |
| Query 04 | Parameters | `token_symbol` (text), `listing_date` (text) |

---

## Refresh schedule (proposed)

| Queries | Frequency |
| --- | --- |
| 01, 05, 07, 09 | Daily |
| 02, 06 | Daily |
| 03, 08, 10 | Weekly |
| 04 | On demand (parameterized) |
