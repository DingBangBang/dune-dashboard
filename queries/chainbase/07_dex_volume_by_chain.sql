/* Query 07 (Chainbase) — DEX-routed volume by chain — HISTORICAL SNAPSHOT
 * Source: onchain_trades on the two chains Chainbase exposes for this table:
 * ethereum + bsc. PROXY: transfers touching known DEX router addresses.
 * Window: {{WINDOW_START}} .. {{WINDOW_END}}
 */
SELECT
    chain,
    day,
    round(sum(usd), 2) AS volume_usd,
    count(*)           AS transfers
FROM (
    SELECT 'ethereum' AS chain, date(block_timestamp) AS day, usd_value AS usd
    FROM ethereum.onchain_trades
    WHERE block_timestamp >= '{{WINDOW_START}}' AND block_timestamp < '{{WINDOW_END}}'
      AND (lower(to_address) IN ({{DEX_ROUTERS}}) OR lower(from_address) IN ({{DEX_ROUTERS}}))
    UNION ALL
    SELECT 'bsc' AS chain, date(block_timestamp) AS day, usd_value AS usd
    FROM bsc.onchain_trades
    WHERE block_timestamp >= '{{WINDOW_START}}' AND block_timestamp < '{{WINDOW_END}}'
      AND (lower(to_address) IN ({{DEX_ROUTERS}}) OR lower(from_address) IN ({{DEX_ROUTERS}}))
) u
GROUP BY chain, day
ORDER BY day, chain;
