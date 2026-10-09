/* Query 08 (Chainbase) — Top tokens by transfer volume — HISTORICAL SNAPSHOT
 * Source: ethereum.onchain_trades.
 * ADAPTED: the original panel was "top token pairs". onchain_trades stores one
 * token per row, so pairs cannot be reconstructed cheaply here; we rank single
 * tokens by USD transfer volume instead (clearly labelled in the dashboard).
 * Window: {{WINDOW_START}} .. {{WINDOW_END}}
 */
WITH t AS (
    SELECT
        symbol,
        sum(usd_value) AS volume_usd,
        count(*)       AS transfers
    FROM ethereum.onchain_trades
    WHERE block_timestamp >= '{{WINDOW_START}}'
      AND block_timestamp <  '{{WINDOW_END}}'
      AND symbol IS NOT NULL
    GROUP BY symbol
)
SELECT
    symbol,
    round(volume_usd, 2) AS volume_usd,
    transfers,
    round(100 * volume_usd / sum(volume_usd) over (), 2) AS volume_share_pct,
    rank() over (order by volume_usd desc) AS volume_rank
FROM t
ORDER BY volume_usd DESC
LIMIT 30;
