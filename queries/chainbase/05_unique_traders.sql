/* Query 05 (Chainbase) — Unique senders / activity — HISTORICAL SNAPSHOT
 * Source: ethereum.onchain_trades. onchain_trades has no tx_from, so we count
 * DISTINCT from_address as the closest available "unique participant" proxy.
 * Window: {{WINDOW_START}} .. {{WINDOW_END}}
 */
SELECT
    date(block_timestamp)                     AS day,
    count(distinct lower(from_address))       AS unique_senders,
    count(*)                                  AS transfers,
    round(sum(usd_value), 2)                  AS volume_usd,
    round(count(*) / nullif(count(distinct lower(from_address)), 0), 2) AS transfers_per_sender
FROM ethereum.onchain_trades
WHERE block_timestamp >= '{{WINDOW_START}}'
  AND block_timestamp <  '{{WINDOW_END}}'
GROUP BY date(block_timestamp)
ORDER BY day;
