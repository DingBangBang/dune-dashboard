/* ============================================================================
 * Query 04 — Token CEX-Listing Impact on DEX Volume (±7 days)
 * ----------------------------------------------------------------------------
 * PURPOSE
 *   Measure how a token's DEX trading volume changes in the window around a
 *   centralized-exchange listing. Classic "listing pump/dump" analysis: does
 *   DEX activity spike before (front-running) or after (rotation) a CEX list?
 *
 * DATA SOURCES
 *   dex.trades -> the token's on-chain DEX volume, filtered by symbol.
 *
 * PARAMETERS  (define these in the Dune query editor / via the API script)
 *   {{token_symbol}}  text  e.g. PEPE, WIF, JUP, ARB
 *   {{listing_date}}  text  ISO date e.g. 2024-01-31
 *
 * OUTPUT COLUMNS
 *   day_offset (-7..+7), day, dex_volume_usd, buy_volume_usd,
 *   sell_volume_usd, trades, trailing14d_avg_usd, forward14d_avg_usd
 *
 * VISUALIZATION
 *   Line chart: dex_volume_usd vs day_offset; overlay trailing/forward averages.
 * ==========================================================================*/

WITH params AS (
    SELECT
        CAST('{{token_symbol}}' AS VARCHAR) AS token_symbol,
        CAST('{{listing_date}}' AS DATE)    AS listing_date
),

daily AS (
    SELECT
        CAST(date_trunc('day', t.block_time) AS DATE) AS day,
        SUM(CASE WHEN t.token_bought_symbol = p.token_symbol
                 THEN t.amount_usd ELSE 0 END)        AS buy_volume_usd,
        SUM(CASE WHEN t.token_sold_symbol = p.token_symbol
                 THEN t.amount_usd ELSE 0 END)        AS sell_volume_usd,
        COUNT(*)                                      AS trades
    FROM dex.trades t
    CROSS JOIN params p
    WHERE t.block_month >= date_trunc('month', p.listing_date - INTERVAL '30' DAY)
      AND t.block_month <= date_trunc('month', p.listing_date + INTERVAL '30' DAY)
      AND (t.token_bought_symbol = p.token_symbol
           OR t.token_sold_symbol = p.token_symbol)
      AND t.amount_usd IS NOT NULL
    GROUP BY 1
),

enriched AS (
    SELECT
        day,
        buy_volume_usd,
        sell_volume_usd,
        buy_volume_usd + sell_volume_usd AS dex_volume_usd,
        trades,
        date_diff('day', (SELECT listing_date FROM params), day) AS day_offset
    FROM daily
),

windowed AS (
    SELECT
        *,
        AVG(dex_volume_usd) OVER (ORDER BY day
            ROWS BETWEEN 14 PRECEDING AND 1 PRECEDING) AS trailing14d_avg_usd,
        AVG(dex_volume_usd) OVER (ORDER BY day
            ROWS BETWEEN 1 FOLLOWING AND 14 FOLLOWING) AS forward14d_avg_usd
    FROM enriched
)

SELECT
    day_offset,
    day,
    ROUND(dex_volume_usd, 2)        AS dex_volume_usd,
    ROUND(buy_volume_usd, 2)        AS buy_volume_usd,
    ROUND(sell_volume_usd, 2)       AS sell_volume_usd,
    trades,
    ROUND(trailing14d_avg_usd, 2)   AS trailing14d_avg_usd,
    ROUND(forward14d_avg_usd, 2)    AS forward14d_avg_usd
FROM windowed
WHERE day BETWEEN CAST((SELECT listing_date FROM params) - INTERVAL '7' DAY AS DATE)
              AND CAST((SELECT listing_date FROM params) + INTERVAL '7' DAY AS DATE)
ORDER BY day;
