# Metric Definitions — Exchange Market Share Tracker

Precise formulas, units, edge cases and production interpretation for every
metric surfaced on the dashboard.

---

## Conventions

* All timestamps are **UTC**. "Day" = `date_trunc('day', block_time)`.
* **USD values** come from Dune's `amount_usd` (execution-time price). They are
  subject to oracle/pricing gaps for long-tail tokens — treat tail-token USD
  figures as approximate.
* Unless stated, an "aggregator"/"DEX" row is one **user-intended trade**, not one
  pool interaction.
* `null`/missing is rendered as a gap, never as `0`, except where `CASE ... ELSE 0`
  is explicit.

---

## 1. CEX/DEX ratio · `01_cex_dex_ratio.sql`

```
cex_dex_ratio = cex_onchain_volume_usd / dex_volume_usd
```

| Component | Formula |
| --- | --- |
| `dex_volume_usd` | `SUM(amount_usd)` over `dex.trades`, per day |
| `cex_onchain_volume_usd` | `SUM(amount_usd)` over `cex.flows` (deposits + withdrawals), per day |
| `cex_net_flow_usd` | `SUM(deposit) − SUM(withdrawal)` in USD, per day |

**Edge cases:** divide-by-zero → `NULL` (guarded by `NULLIF`). Days present on only
one side survive via `FULL OUTER JOIN`.

**Production meaning:** a *ratio*, so read the **trend**. Falling = value moving
on-chain (DEX/self-custody growth); rising = value concentrating in CEX rails.
⚠️ **Not** a literal CEX-vs-DEX *trading* volume comparison — see dev log §1.01.

---

## 2. Exchange net flow · `02_exchange_net_flow.sql`

```
net_flow_usd = Σ deposit_usd − Σ withdrawal_usd      (per exchange, per day)
inflow_usd   = Σ deposit_usd
outflow_usd  = Σ withdrawal_usd
```

Scope: ETH, WETH, USDT only; fixed 10-exchange set.

**Production meaning:** persistent negative net flow = coins leaving exchanges
(bullish supply setup / self-custody). Persistent positive = coins inbound (often
pre-sell). Normalise against exchange size before comparing venues.

---

## 3. Aggregator market share · `03_aggregator_market_share.sql`

```
volume_usd       = Σ amount_usd                              (project, month)
market_share_pct = 100 × volume_usd / Σ_month volume_usd
mom_growth_pct   = 100 × (volume_usd − LAG(volume_usd)) / LAG(volume_usd)
```

`LAG` is partitioned by `project`, ordered by `month`; the first month per project
yields `NULL` (no prior period) — expected.

**Production meaning:** a share gain with flat volume means a *competitor shrank*,
not that you grew. Always read share together with absolute volume.

---

## 4. Listing impact · `04_token_listing_impact.sql`

```
dex_volume_usd      = buy_volume_usd + sell_volume_usd
buy_volume_usd      = Σ amount_usd where token_bought_symbol = {{token_symbol}}
sell_volume_usd     = Σ amount_usd where token_sold_symbol   = {{token_symbol}}
day_offset          = date_diff('day', listing_date, day)    ∈ [-7, +7]
trailing14d_avg_usd = AVG(dex_volume_usd) over previous 14 days
forward14d_avg_usd  = AVG(dex_volume_usd) over next 14 days
```

Both legs are counted, so a self-trade of the token could be double-represented —
negligible in practice.

**Production meaning:** volume rising **before** `day_offset = 0` suggests informed
positioning ahead of the listing; a spike **after** suggests retail rotation.
Compare trailing vs forward averages for a single "listing multiplier".

---

## 5. Unique traders · `05_unique_traders.sql`

```
unique_traders        = COUNT(DISTINCT tx_from)
trades_per_trader     = trades / unique_traders
volume_per_trader_usd = volume_usd / unique_traders
```

**Edge cases:** `tx_from` is an EOA; a smart-contract wallet (bot) still counts as
one trader. Choosing `tx_from` avoids the `taker`-is-a-router pitfall.

**Production meaning:** growth in `unique_traders` = real adoption. Growth in
`trades_per_trader` alone = automation/MEV. Healthy markets grow both slowly and
together.

---

## 6. CEX flow by exchange · `06_cex_flow_by_exchange.sql`

Same definitions as §2, aggregated over 90 days, filtered to
`total_volume_usd > $1,000,000`. `unique_users = COUNT(DISTINCT tx_from)`.

**Production meaning:** an exchange leaderboard by on-chain settlement scale. Use
it to weight the net-flow series (§2) — a small venue's large %-change is noise.

---

## 7. DEX volume by chain · `07_dex_volume_by_chain.sql`

```
volume_usd      = Σ amount_usd                              (chain, week)
chain_share_pct = 100 × volume_usd / Σ_week volume_usd
```

**Production meaning:** tracks chain rotation (L1 ↔ L2 ↔ alt-L1). Rising share on
low-fee chains while total volume is flat = fee-driven migration, not new demand.

---

## 8. Top token pairs · `08_top_token_pairs.sql`

```
volume_share_pct = 100 × pair_volume / Σ_all pairs volume
volume_rank      = RANK() OVER (ORDER BY volume_usd DESC)
```

`token_pair` is alphabetised by Dune → direction-agnostic.

**Production meaning:** concentration in majors (ETH/USDC, WETH/USDT) = a "safe"
market; rotation into long-tail pairs = risk-on. The top-pair share is a
single-number concentration index.

---

## 9. Stablecoin share · `09_stablecoin_share.sql`

```
stablecoin_volume_usd = Σ amount_usd where either leg ∈ stablecoin_set
stablecoin_share_pct  = 100 × stablecoin_volume_usd / total_volume_usd
share_7d_ma           = 7-day moving average of stablecoin_share_pct
```

Stablecoin set: USDC, USDT, DAI, USDS, FRAX, USDe, PYUSD, TUSD, FDUSD.

**Edge case:** stable↔stable swaps are counted once (documented simplification).

**Production meaning:** a rising share = de-risking / defensive positioning; a
falling share = risk-on rotation into volatile assets. A regime thermometer.

---

## 10. Trade size distribution · `10_trade_size_distribution.sql`

Buckets: `< $100`, `$100–1K`, `$1K–10K`, `$10K–100K`, `$100K–1M`, `≥ $1M`.

```
volume_share_pct      = 100 × bucket_volume / weekly_volume
trade_count_share_pct = 100 × bucket_trades / weekly_trades
```

**Production meaning:** rising `≥$1M` *volume* share = institutional/whale flow.
Rising `<$100` *count* share = retail. The gap between a bucket's count share and
its volume share is the whole story (few big trades vs many small ones).

---

## Data-quality caveats (read before quoting numbers)

1. **CEX trading volume is unavailable on-chain** (see §1).
2. **`amount_usd` pricing** for illiquid tokens can be stale/imputed.
3. **Cross-chain dedupe**: the same user trading on two chains counts twice in any
   per-chain aggregation; our trader metric is per-project-per-day.
4. **Coverage**: curated tables cover many but not *all* venues; treat absolute
   totals as lower bounds and focus on relative/share trends.
5. **Bots & MEV**: count-based metrics include automated flow; always pair with
   `trades_per_trader`.

