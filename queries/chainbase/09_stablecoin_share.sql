/* Query 09 (Chainbase) — Stablecoin share of volume — HISTORICAL SNAPSHOT
 * Source: ethereum.onchain_trades. Stablecoin legs = rows whose symbol is in the
 * stablecoin set. Window: {{WINDOW_START}} .. {{WINDOW_END}}
 */
WITH d AS (
    SELECT
        date(block_timestamp) AS day,
        sum(usd_value) AS total_volume_usd,
        sum(case when upper(symbol) IN ({{STABLECOINS}}) then usd_value else 0 end) AS stablecoin_volume_usd
    FROM ethereum.onchain_trades
    WHERE block_timestamp >= '{{WINDOW_START}}'
      AND block_timestamp <  '{{WINDOW_END}}'
    GROUP BY date(block_timestamp)
)
SELECT
    day,
    round(total_volume_usd, 2)      AS total_volume_usd,
    round(stablecoin_volume_usd, 2) AS stablecoin_volume_usd,
    round(100 * stablecoin_volume_usd / nullif(total_volume_usd, 0), 2) AS stablecoin_share_pct
FROM d
ORDER BY day;
