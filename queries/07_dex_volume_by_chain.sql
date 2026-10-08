/* ============================================================================
 * Query 07 — DEX Volume by Blockchain (weekly)
 * ----------------------------------------------------------------------------
 * PURPOSE
 *   Track how DEX liquidity/activity is distributed across chains over time.
 *   Reveals rotation from Ethereum L1 to L2s and between competing ecosystems.
 *
 * DATA SOURCES
 *   dex.trades -> curated cross-chain EVM DEX trades (`blockchain` column).
 *
 * WINDOW FUNCTION
 *   chain_share_pct = chain volume / total volume of the same week
 *                     (SUM(...) OVER (PARTITION BY week)).
 *
 * GRAIN / RANGE
 *   One row per (week, blockchain), trailing 180 days.
 *
 * OUTPUT COLUMNS
 *   week, blockchain, volume_usd, trades, unique_traders, chain_share_pct
 *
 * VISUALIZATION
 *   Stacked area chart of volume_usd by blockchain over week.
 * ==========================================================================*/

SELECT
    date_trunc('week', block_time)                        AS week,
    blockchain,
    ROUND(SUM(amount_usd), 2)                             AS volume_usd,
    COUNT(*)                                              AS trades,
    COUNT(DISTINCT tx_from)                               AS unique_traders,
    ROUND(100.0 * SUM(amount_usd)
          / NULLIF(SUM(SUM(amount_usd)) OVER
                   (PARTITION BY date_trunc('week', block_time)), 0), 2)
                                                          AS chain_share_pct
FROM dex.trades
WHERE block_month >= date_trunc('month', current_date - INTERVAL '180' DAY)
  AND amount_usd IS NOT NULL
GROUP BY 1, 2
ORDER BY week DESC, volume_usd DESC;
