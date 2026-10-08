/* ============================================================================
 * Query 01 — CEX / DEX Volume Ratio (daily)
 * ----------------------------------------------------------------------------
 * PURPOSE
 *   Compare on-chain DEX trading volume against centralized-exchange on-chain
 *   settlement flow, and compute the CEX/DEX ratio per day.
 *
 * DATA SOURCES
 *   dex.trades        -> DEX swap volume (curated, cross-chain EVM).
 *   cex.flows         -> CEX deposit/withdrawal flows (curated).
 *
 * IMPORTANT DESIGN NOTE
 *   CEX *trading* volume happens off-chain (order books live in exchange
 *   databases) and is NOT available on Dune. The honest on-chain proxy is the
 *   CEX settlement flow (deposits + withdrawals) from `cex.flows`.
 *   DEX volume IS on-chain, so it is a true trading volume.
 *   The ratio therefore measures "value settling in/out of CEXs" vs
 *   "value traded on DEXs" — read it as a relative activity gauge, not as
 *   literal CEX trading volume.
 *
 * GRAIN / RANGE
 *   One row per day, last 90 days.
 *
 * OUTPUT COLUMNS
 *   day, dex_volume_usd, dex_trades, cex_onchain_volume_usd,
 *   cex_net_flow_usd, cex_dex_ratio
 *
 * VISUALIZATION
 *   Mixed: bar = dex_volume_usd & cex_onchain_volume_usd, line = cex_dex_ratio.
 * ==========================================================================*/

WITH dex_daily AS (
    SELECT
        block_date                          AS day,
        SUM(amount_usd)                     AS dex_volume_usd,
        COUNT(*)                            AS dex_trades
    FROM dex.trades
    WHERE block_month >= date_trunc('month', current_date - INTERVAL '90' DAY)
      AND amount_usd IS NOT NULL
    GROUP BY 1
),

cex_daily AS (
    SELECT
        CAST(date_trunc('day', block_time) AS DATE) AS day,
        SUM(amount_usd)                             AS cex_onchain_volume_usd,
        -- deposit  => value moving INTO an exchange (positive)
        -- withdrawal => value moving OUT (negative)
        SUM(CASE WHEN lower(flow_type) = 'deposit'
                 THEN amount_usd ELSE -amount_usd END) AS cex_net_flow_usd
    FROM cex.flows
    WHERE block_month >= date_trunc('month', current_date - INTERVAL '90' DAY)
      AND amount_usd IS NOT NULL
    GROUP BY 1
)

SELECT
    COALESCE(d.day, c.day)                                          AS day,
    ROUND(d.dex_volume_usd, 2)                                      AS dex_volume_usd,
    d.dex_trades                                                    AS dex_trades,
    ROUND(c.cex_onchain_volume_usd, 2)                              AS cex_onchain_volume_usd,
    ROUND(c.cex_net_flow_usd, 2)                                    AS cex_net_flow_usd,
    ROUND(c.cex_onchain_volume_usd / NULLIF(d.dex_volume_usd, 0), 3) AS cex_dex_ratio
FROM dex_daily d
FULL OUTER JOIN cex_daily c ON d.day = c.day
WHERE COALESCE(d.day, c.day) >= current_date - INTERVAL '90' DAY
ORDER BY day;
