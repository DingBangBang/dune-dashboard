/* Query 01 (Chainbase) — CEX vs DEX daily volume & ratio — HISTORICAL SNAPSHOT
 * Source: ethereum.onchain_trades (Chainbase Data Cloud, MySQL/Doris dialect).
 * CEX = transfers to/from known CEX addresses.
 * DEX = transfers to/from known DEX router addresses (PROXY — onchain_trades has
 *       no swap flag, only Transfer / NativeTransfer operations).
 * Window: {{WINDOW_START}} .. {{WINDOW_END}}  (last ~30 days of the snapshot)
 */
SELECT
    day,
    round(sum(case when is_dex then usd_value else 0 end), 2) AS dex_volume_usd,
    round(sum(case when is_cex then usd_value else 0 end), 2) AS cex_volume_usd,
    round(sum(case when is_cex then usd_value else 0 end)
          / nullif(sum(case when is_dex then usd_value else 0 end), 0), 3) AS cex_dex_ratio
FROM (
    SELECT
        date(block_timestamp) AS day,
        usd_value,
        (lower(to_address)   IN ({{DEX_ROUTERS}}) OR lower(from_address) IN ({{DEX_ROUTERS}})) AS is_dex,
        (lower(to_address)   IN ({{CEX_ADDRESSES}}) OR lower(from_address) IN ({{CEX_ADDRESSES}})) AS is_cex
    FROM ethereum.onchain_trades
    WHERE block_timestamp >= '{{WINDOW_START}}'
      AND block_timestamp <  '{{WINDOW_END}}'
      AND ((lower(to_address) IN ({{DEX_ROUTERS}}) OR lower(from_address) IN ({{DEX_ROUTERS}}))
        OR (lower(to_address) IN ({{CEX_ADDRESSES}}) OR lower(from_address) IN ({{CEX_ADDRESSES}})))
) t
GROUP BY day
ORDER BY day;
