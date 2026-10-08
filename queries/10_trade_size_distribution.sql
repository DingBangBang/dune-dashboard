/* ============================================================================
 * Query 10 — Trade Size Distribution (weekly)
 * ----------------------------------------------------------------------------
 * PURPOSE
 *   Segment DEX trades into USD size buckets and measure each bucket's share of
 *   trade COUNT vs trade VOLUME. A rising >=$1M volume share signals
 *   institutional / whale activity; a rising <$100 count share signals retail.
 *
 * DATA SOURCES
 *   dex.trades -> amount_usd per trade.
 *
 * WINDOW FUNCTIONS
 *   trade_count_share_pct / volume_share_pct = bucket / weekly total.
 *
 * GRAIN / RANGE
 *   One row per (week, size_bucket), trailing 90 days.
 *
 * OUTPUT COLUMNS
 *   week, size_bucket, trades, volume_usd,
 *   trade_count_share_pct, volume_share_pct
 *
 * VISUALIZATION
 *   Stacked bar chart of volume_share_pct by size_bucket over week.
 * ==========================================================================*/

WITH bucketed AS (
    SELECT
        date_trunc('week', block_time) AS week,
        CASE
            WHEN amount_usd < 100      THEN '1_<$100'
            WHEN amount_usd < 1000     THEN '2_$100-1K'
            WHEN amount_usd < 10000    THEN '3_$1K-10K'
            WHEN amount_usd < 100000   THEN '4_$10K-100K'
            WHEN amount_usd < 1000000  THEN '5_$100K-1M'
            ELSE '6_>=$1M'
        END                            AS size_bucket,
        amount_usd
    FROM dex.trades
    WHERE block_month >= date_trunc('month', current_date - INTERVAL '90' DAY)
      AND amount_usd IS NOT NULL
      AND amount_usd > 0
),

agg AS (
    SELECT
        week,
        size_bucket,
        COUNT(*)            AS trades,
        SUM(amount_usd)     AS volume_usd
    FROM bucketed
    GROUP BY 1, 2
)

SELECT
    week,
    size_bucket,
    trades,
    ROUND(volume_usd, 2)                                   AS volume_usd,
    ROUND(100.0 * trades
          / NULLIF(SUM(trades) OVER (PARTITION BY week), 0), 2)
                                                           AS trade_count_share_pct,
    ROUND(100.0 * volume_usd
          / NULLIF(SUM(volume_usd) OVER (PARTITION BY week), 0), 2)
                                                           AS volume_share_pct
FROM agg
ORDER BY week DESC, size_bucket;
