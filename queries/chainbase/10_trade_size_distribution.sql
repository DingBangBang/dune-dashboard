/* Query 10 (Chainbase) — Trade size distribution (daily) — HISTORICAL SNAPSHOT
 * Source: ethereum.onchain_trades. Buckets by usd_value.
 * NOTE: uses a 7-day sub-window of the snapshot so the daily series stays
 * readable; window is configurable.
 * Window: {{WINDOW_START}} .. {{WINDOW_END}}
 */
WITH b AS (
    SELECT
        date(block_timestamp) AS day,
        case
            when usd_value < 100      then '1_<$100'
            when usd_value < 1000     then '2_$100-1K'
            when usd_value < 10000    then '3_$1K-10K'
            when usd_value < 100000   then '4_$10K-100K'
            when usd_value < 1000000  then '5_$100K-1M'
            else '6_>=$1M'
        end AS size_bucket,
        usd_value
    FROM ethereum.onchain_trades
    WHERE block_timestamp >= '{{WINDOW_START}}'
      AND block_timestamp <  '{{WINDOW_END}}'
      AND usd_value IS NOT NULL
      AND usd_value > 0
),
agg AS (
    SELECT day, size_bucket, count(*) AS transfers, sum(usd_value) AS volume_usd
    FROM b
    GROUP BY day, size_bucket
)
SELECT
    day,
    size_bucket,
    transfers,
    round(volume_usd, 2) AS volume_usd,
    round(100 * transfers / sum(transfers) over (partition by day), 2) AS count_share_pct,
    round(100 * volume_usd / sum(volume_usd) over (partition by day), 2) AS volume_share_pct
FROM agg
ORDER BY day, size_bucket;
