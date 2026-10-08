/* ============================================================================
 * Query 09 — Stablecoin Share of DEX Volume (daily)
 * ----------------------------------------------------------------------------
 * PURPOSE
 *   What fraction of DEX volume is stablecoin-related? High share = defensive /
 *   de-risking market; low share = risk-on / speculative rotation. Also a
 *   useful proxy for on-chain "cash" velocity.
 *
 * DATA SOURCES
 *   dex.trades -> inspect both token_bought_symbol and token_sold_symbol.
 *
 * NOTE
 *   A trade is counted once even if both legs are stablecoins (stable<->stable
 *   swaps such as USDC->USDT). This slightly under-counts pure stablecoin
 *   churn; documented as an intentional simplification in the dev log.
 *
 * GRAIN / RANGE
 *   One row per day, last 90 days.
 *
 * OUTPUT COLUMNS
 *   day, total_volume_usd, stablecoin_volume_usd,
 *   stablecoin_share_pct, share_7d_ma
 *
 * VISUALIZATION
 *   Line chart: stablecoin_share_pct + share_7d_ma over day.
 * ==========================================================================*/

WITH daily AS (
    SELECT
        block_date                          AS day,
        SUM(amount_usd)                     AS total_volume_usd,
        SUM(CASE
                WHEN token_bought_symbol IN ('USDC','USDT','DAI','USDS','FRAX','USDE','PYUSD','TUSD','FDUSD')
                  OR token_sold_symbol   IN ('USDC','USDT','DAI','USDS','FRAX','USDE','PYUSD','TUSD','FDUSD')
                THEN amount_usd ELSE 0 END) AS stablecoin_volume_usd
    FROM dex.trades
    WHERE block_month >= date_trunc('month', current_date - INTERVAL '90' DAY)
      AND amount_usd IS NOT NULL
    GROUP BY 1
)

SELECT
    day,
    ROUND(total_volume_usd, 2)                              AS total_volume_usd,
    ROUND(stablecoin_volume_usd, 2)                         AS stablecoin_volume_usd,
    ROUND(100.0 * stablecoin_volume_usd
          / NULLIF(total_volume_usd, 0), 2)                 AS stablecoin_share_pct,
    ROUND(AVG(100.0 * stablecoin_volume_usd
              / NULLIF(total_volume_usd, 0)) OVER
          (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 2)
                                                            AS share_7d_ma
FROM daily
ORDER BY day;
