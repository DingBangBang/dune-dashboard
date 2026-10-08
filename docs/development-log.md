# Development Log — Exchange Market Share Tracker

Design rationale, key trade-offs, performance notes and a forward roadmap.
Newest entries at the bottom under **Changelog**.

---

## 1. Design thinking per query

### 01 — CEX/DEX ratio
* **Intent:** one glance at the structural tug-of-war between off-chain order books
  and on-chain AMMs.
* **Reality check:** there is **no CEX trading-volume table on Dune** — CEX trades
  settle off-chain in exchange databases. The only on-chain, verifiable CEX signal
  is **settlement flow** (`cex.flows`: deposits + withdrawals).
* **Decision:** compute the ratio as `CEX on-chain flow ÷ DEX traded volume` and
  label it explicitly. It is a *relative on-chain activity gauge*, not a literal
  CEX-vs-DEX volume ratio. Documenting this honestly is more valuable than faking a
  number.
* **Join:** `FULL OUTER JOIN` on `day` so a day missing on either side (e.g. a CEX
  table lag) still appears instead of silently disappearing.

### 02 — Exchange net flow
* **Intent:** reproduce the classic "coins leaving exchanges" indicator.
* **Source choice:** `cex.flows` (event-based) instead of a balance snapshot.
  Net flow = `Σ deposits − Σ withdrawals`; it needs no snapshot and scales across
  the 29 chains the dataset covers. `cex.balances`-style snapshots are a legacy
  pattern.
* **Scope:** restricted to ETH/WETH/USDT and a fixed 10-exchange list to keep the
  query cheap and the chart readable.
* **`lower(flow_type)`:** the exact casing of `flow_type` values is not guaranteed
  in docs, so we normalise with `lower()` to be safe (`='deposit'` / `='withdrawal'`).

### 03 — Aggregator market share
* **Why `dex_aggregator.trades` and not `dex.trades`:** `dex.trades` records **each
  pool hop** of a route separately. Summing it would double-count multi-hop routes.
  `dex_aggregator.trades` condenses a route into **one user-intended trade** — the
  correct denominator for market share.
* **Window functions:** `SUM(...) OVER (PARTITION BY month)` for the share, and
  `LAG(...) OVER (PARTITION BY project ORDER BY month)` for MoM growth. This keeps
  everything in one scan instead of a self-join.
* **`block_month` is `TIMESTAMP` here** (unlike `dex.trades` where it is `DATE`), so
  the partition filter casts the boundary to `TIMESTAMP`.

### 04 — Token listing impact
* **Intent:** quantify the "listing pump" and detect front-running.
* **Parameterised** (`token_symbol`, `listing_date`) so one query serves any token —
  far better than hard-coding.
* **Three-layer CTE:** `daily` → `enriched` (adds `day_offset`) → `windowed`
  (trailing/forward 14-day averages) → final filter to ±7 days.
  *Why the order matters:* the window frame is computed **before** the ±7 filter, so
  the averages see the full surrounding context rather than a truncated frame.
* **`date_diff('day', listing_date, day)`** gives a clean `-7..+7` x-axis.

### 05 — Unique traders
* **Dedupe key = `tx_from`, not `taker`:** `taker` can be a router contract, which
  would collapse thousands of users into one address. `tx_from` is the EOA that
  signed the swap — a much better proxy for a unique wallet.
* **Intensity metrics** (`trades_per_trader`, `volume_per_trader_usd`) are added so
  the panel warns you when "growth" is actually one bot looping.

### 06 — CEX flow by exchange
* Aggregate leaderboard; `HAVING total_volume > $1M` trims dust addresses so the
  chart isn't a long tail of one-off wallets.

### 07 — DEX volume by chain
* Weekly grain (daily per-chain is noisy and returns 90×chains rows). A windowed
  `chain_share_pct` shows *rotation* — the interesting signal — not just raw volume.

### 08 — Top token pairs
* `token_pair` is already alphabetically normalised by Dune, so `ETH/USDC` and
  `USDC/ETH` collapse to one row — no manual `LEAST/GREATEST` needed.
* `RANK()` for the leaderboard and a `SUM(...) OVER ()` share in a single scan.

### 09 — Stablecoin share
* Both legs are inspected (bought **or** sold). **Known simplification:** a
  stable↔stable swap is counted once, so pure stablecoin churn is slightly
  under-counted. Chosen for simplicity/readability over decimal precision; noted
  here rather than hidden.
* A 7-day moving average (`ROWS BETWEEN 6 PRECEDING AND CURRENT ROW`) smooths the
  day-of-week noise so the regime signal is legible.

### 10 — Trade-size distribution
* Buckets are **string-prefixed** (`1_`, `2_`, …) so Dune's default alphabetical
  sort of the legend is also the correct size order — a small UX trick that avoids
  custom sorting.
* Reports share of **count** and share of **volume** separately: the divergence
  between the two is the actual insight.

---

## 2. Key trade-offs

| Decision | Chosen | Alternative | Why |
| --- | --- | --- | --- |
| **Window length** | **90 days** default | 30 days | 30d is one regime; it can't distinguish a structural trend from a two-week spike. 90d spans a full quarter → seasonality, a couple of macro events, and enough points for moving averages. Deep-history queries (03, 07) go to 180–365 days. |
| **CEX volume proxy** | on-chain `cex.flows` | fabricating a CEX number | Dune has no CEX trade volume. A documented proxy beats an invented metric. |
| **Aggregator source** | `dex_aggregator.trades` | `dex.trades` | avoids multi-hop double counting. |
| **Trader identity** | `tx_from` | `taker` / `maker` | `taker` can be a contract; `tx_from` ≈ unique EOA. |
| **Screenshots in git** | ignored (`*.png`) | committed | large binaries bloat the repo; per project rules screenshots are managed separately. |
| **Query reuse** | 1 SQL file → many visualizations | 1 viz per query | Dune lets one query feed multiple widgets; no duplication. |
| **Time filtering** | partition column `block_month` | `block_time` | `block_month` enables partition pruning → order-of-magnitude speedups. |
| **Parameters** | only query 04 | all queries | Parameters add friction; only the listing analysis genuinely needs input. |

---

## 3. Dune query performance optimisation

1. **Always filter on the partition column.** `dex.trades`/`tokens.transfers` use
   `block_month` (DATE); `dex_aggregator.trades` uses `block_month` (TIMESTAMP).
   Filtering here lets Trino skip whole partitions.
2. **Never filter only on `block_time`.** It scans everything and is the #1 cause
   of timeouts. Keep the `block_month` predicate even if you also filter `block_date`.
3. **Aggregate early.** `daily` CTEs shrink the data before any join/window step.
4. **Prefer window functions over self-joins** (used for share / MoM / moving avg).
   One scan instead of two.
5. **`COUNT(DISTINCT ...)` is expensive** — run it only where it earns its keep
   (queries 05, 06). Don't sprinkle it into every panel.
6. **Restrict `project`/`cex_name` with `IN (...)`** to cut cardinality.
7. **`LIMIT`** the exploratory panels (08) so the result payload stays small.
8. **Avoid `SELECT *`** in production queries — list columns to reduce I/O.
9. **Materialise heavy queries** (Dune "materialized views" / scheduled runs) once a
   query is stable and reused across panels.
10. **Reuse a query for multiple charts** instead of re-running the same SQL.

---

## 4. Roadmap / next steps

- [ ] **Add a MEV dimension** using `dex.sandwiched` / `dex.sandwiches` — sandwich
      volume as a share of DEX volume is a strong market-quality signal.
- [ ] **Stablecoin net-flow per exchange** (USDT/USDC only) as a dedicated panel.
- [ ] **Solana coverage** via `dex_solana.trades` + `jupiter_solana.aggregator_swaps`
      to compare EVM vs Solana aggregator dynamics.
- [ ] **Cost-to-trade proxy**: median gas-per-swap by chain (joins `gas.fees`).
- [ ] **Alerting**: schedule a query and push a Slack/Discord alert when the
      CEX/DEX ratio crosses a threshold or a whale-print spikes.
- [ ] **API export pipeline**: pull published results with `dune_client` into a
      CSV/Parquet for BI tools (Metabase/Hex via the Trino connector).
- [ ] **Cross-check vs DefiLlama** to quantify coverage gaps in the curated tables.
- [ ] **Tests**: a `scripts/validate_results.py` that hits the Execution API and
      asserts non-empty / sane ranges (smoke test for CI).
- [ ] **LLM summary widget**: feed the daily aggregates to an LLM to auto-write the
      dashboard's "what changed" text block.

---

## 5. Changelog

| Date | Change |
| --- | --- |
| 2026-10-09 | Initial scaffold: 10 DuneSQL queries, automation script, docs, git repo. Queries not yet published (pending API key / UI build). |
| 2026-10-09 | Expanded `docs/dashboard_guide.md` for the **free-plan manual path**: no API required; added per-query creation steps, per-panel visualization config, time-filter/publish steps and a detailed screenshot-region guide. READMEs updated to lead with the manual path. |

> **TODO after publishing:** add a row with the public dashboard URL and the date
> the dashboard first went live, plus a screenshot link.

