/* ============================================================================
 * Query 05 — Unique Traders per Protocol (daily)
 * ----------------------------------------------------------------------------
 * PURPOSE
 *   Count distinct wallets that traded on each major EVM DEX each day, plus
 *   intensity metrics (trades per trader, volume per trader). This separates
 *   "real user growth" from "volume from a handful of bots/market makers".
 *
 * DATA SOURCES
 *   dex.trades -> `tx_from` is the EOA that initiated the swap. We dedupe on
 *   tx_from (not `taker`, which can be a router contract) to approximate a
 *   unique human/agent wallet.
 *
 * GRAIN / RANGE
 *   One row per (day, project), last 90 days, curated project list.
 *
 * OUTPUT COLUMNS
 *   day, project, unique_traders, trades, trades_per_trader,
 *   volume_usd, volume_per_trader_usd
 *
 * VISUALIZATION
 *   Line chart of unique_traders by project over day.
 * ==========================================================================*/

SELECT
    block_date                                        AS day,
    project,
    COUNT(DISTINCT tx_from)                           AS unique_traders,
    COUNT(*)                                          AS trades,
    ROUND(COUNT(*) * 1.0
          / NULLIF(COUNT(DISTINCT tx_from), 0), 2)    AS trades_per_trader,
    ROUND(SUM(amount_usd), 2)                         AS volume_usd,
    ROUND(SUM(amount_usd)
          / NULLIF(COUNT(DISTINCT tx_from), 0), 2)    AS volume_per_trader_usd
FROM dex.trades
WHERE block_month >= date_trunc('month', current_date - INTERVAL '90' DAY)
  AND tx_from IS NOT NULL
  AND amount_usd IS NOT NULL
  AND project IN (
        'uniswap', 'curve', 'sushiswap', 'pancakeswap', 'balancer',
        'kyberswap', 'dodo', 'trader_joe', 'quickswap', 'camelot'
      )
GROUP BY 1, 2
ORDER BY day DESC, unique_traders DESC;
