/* ============================================================================
 * Query 03 — DEX Aggregator Market Share (monthly)
 * ----------------------------------------------------------------------------
 * PURPOSE
 *   Rank DEX aggregators (1inch, 0x, CoW Protocol, ParaSwap, Odos, ...) by
 *   monthly routed volume and compute each project's share of the total
 *   aggregator market, plus month-over-month growth.
 *
 * DATA SOURCES
 *   dex_aggregator.trades -> one row per *user-intended* aggregated trade
 *   (multi-hop routes are condensed into a single row, unlike dex.trades).
 *
 * WINDOW FUNCTIONS
 *   - market_share_pct: SUM(...) OVER (PARTITION BY month)
 *   - mom_growth_pct  : LAG(...)    OVER (PARTITION BY project ORDER BY month)
 *
 * GRAIN / RANGE
 *   One row per (month, project), trailing 12 months.
 *
 * OUTPUT COLUMNS
 *   month, project, volume_usd, trades, unique_traders,
 *   market_share_pct, mom_growth_pct
 *
 * VISUALIZATION
 *   Stacked area/bar of volume_usd by project over month, or a table.
 * ==========================================================================*/

WITH monthly AS (
    SELECT
        CAST(date_trunc('month', block_time) AS DATE) AS month,
        project,
        SUM(amount_usd)                 AS volume_usd,
        COUNT(*)                        AS trades,
        COUNT(DISTINCT tx_from)         AS unique_traders
    FROM dex_aggregator.trades
    -- block_month is a TIMESTAMP partition column on this table:
    WHERE block_month >= CAST(date_trunc('month', current_date - INTERVAL '365' DAY) AS TIMESTAMP)
      AND amount_usd IS NOT NULL
    GROUP BY 1, 2
)

SELECT
    month,
    project,
    ROUND(volume_usd, 2)                                                AS volume_usd,
    trades,
    unique_traders,
    ROUND(100.0 * volume_usd
          / NULLIF(SUM(volume_usd) OVER (PARTITION BY month), 0), 2)    AS market_share_pct,
    ROUND(100.0 * (volume_usd - LAG(volume_usd) OVER (PARTITION BY project ORDER BY month))
          / NULLIF(LAG(volume_usd) OVER (PARTITION BY project ORDER BY month), 0), 2)
                                                                        AS mom_growth_pct
FROM monthly
ORDER BY month DESC, volume_usd DESC;
