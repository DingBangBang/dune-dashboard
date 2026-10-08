/* ============================================================================
 * Query 08 — Top Token Pairs on DEXs (last 30 days)
 * ----------------------------------------------------------------------------
 * PURPOSE
 *   Rank the most-traded token pairs and their share of total DEX volume.
 *   Useful to see whether activity is concentrated in majors (ETH/USDC) or
 *   rotated into long-tail pairs (a risk-on indicator).
 *
 * DATA SOURCES
 *   dex.trades -> `token_pair` is normalised alphabetically by Dune.
 *
 * WINDOW FUNCTIONS
 *   volume_share_pct = pair volume / total volume (SUM(...) OVER ())
 *   volume_rank      = RANK() OVER (ORDER BY volume_usd DESC)
 *
 * GRAIN / RANGE
 *   One row per token_pair, last 30 days, top 50 by volume.
 *
 * OUTPUT COLUMNS
 *   token_pair, volume_usd, trades, unique_traders,
 *   volume_share_pct, volume_rank
 *
 * VISUALIZATION
 *   Table (top 50) + bar chart of volume_usd.
 * ==========================================================================*/

WITH pairs AS (
    SELECT
        token_pair,
        SUM(amount_usd)             AS volume_usd,
        COUNT(*)                    AS trades,
        COUNT(DISTINCT tx_from)     AS unique_traders
    FROM dex.trades
    WHERE block_month >= date_trunc('month', current_date - INTERVAL '30' DAY)
      AND block_date  >= current_date - INTERVAL '30' DAY
      AND amount_usd IS NOT NULL
      AND token_pair IS NOT NULL
    GROUP BY 1
)

SELECT
    token_pair,
    ROUND(volume_usd, 2)                                            AS volume_usd,
    trades,
    unique_traders,
    ROUND(100.0 * volume_usd / NULLIF(SUM(volume_usd) OVER (), 0), 2)
                                                                    AS volume_share_pct,
    RANK() OVER (ORDER BY volume_usd DESC)                          AS volume_rank
FROM pairs
ORDER BY volume_usd DESC
LIMIT 50;
