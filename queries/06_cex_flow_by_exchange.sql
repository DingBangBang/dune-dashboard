/* ============================================================================
 * Query 06 — CEX Inflow / Outflow / Net Flow by Exchange (90d)
 * ----------------------------------------------------------------------------
 * PURPOSE
 *   Leaderboard of centralized exchanges by on-chain settlement volume,
 *   split into deposits (inflow), withdrawals (outflow) and net flow.
 *   A persistent negative net flow is the classic "coins leaving exchanges"
 *   (accumulation / self-custody) signal.
 *
 * DATA SOURCES
 *   cex.flows -> curated deposit/withdrawal events with CEX entity attribution.
 *
 * GRAIN / RANGE
 *   One row per exchange_name, last 90 days.
 *
 * OUTPUT COLUMNS
 *   exchange_name, inflow_usd, outflow_usd, net_flow_usd,
 *   total_volume_usd, unique_users
 *
 * VISUALIZATION
 *   Horizontal bar chart of net_flow_usd, or a table with progress bars.
 * ==========================================================================*/

SELECT
    cex_name                                                   AS exchange_name,
    ROUND(SUM(CASE WHEN lower(flow_type) = 'deposit'
                   THEN amount_usd ELSE 0 END), 2)              AS inflow_usd,
    ROUND(SUM(CASE WHEN lower(flow_type) = 'withdrawal'
                   THEN amount_usd ELSE 0 END), 2)              AS outflow_usd,
    ROUND(SUM(CASE WHEN lower(flow_type) = 'deposit'
                   THEN amount_usd ELSE -amount_usd END), 2)    AS net_flow_usd,
    ROUND(SUM(amount_usd), 2)                                   AS total_volume_usd,
    COUNT(DISTINCT tx_from)                                     AS unique_users
FROM cex.flows
WHERE block_month >= date_trunc('month', current_date - INTERVAL '90' DAY)
  AND amount_usd IS NOT NULL
GROUP BY 1
HAVING SUM(amount_usd) > 1000000
ORDER BY total_volume_usd DESC;
