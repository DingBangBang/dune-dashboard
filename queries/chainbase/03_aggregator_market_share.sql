/* Query 03 (Chainbase) — DEX aggregator market share (monthly) — HISTORICAL SNAPSHOT
 * Source: ethereum.onchain_trades. PROXY: volume routed to/from known aggregator
 * router contracts (1inch, 0x, CoW Swap, ParaSwap). onchain_trades has no decoded
 * route, so this approximates routing share from transfers touching those routers.
 * Window: {{WINDOW_LONG_START}} .. {{WINDOW_END}}
 */
WITH m AS (
    SELECT
        date_format(block_timestamp, '%Y-%m') AS month,
        CASE
            WHEN lower(to_address) IN ({{AGG_1INCH}})   OR lower(from_address) IN ({{AGG_1INCH}})   THEN '1inch'
            WHEN lower(to_address) IN ({{AGG_0X}})      OR lower(from_address) IN ({{AGG_0X}})      THEN '0x'
            WHEN lower(to_address) IN ({{AGG_COWSWAP}}) OR lower(from_address) IN ({{AGG_COWSWAP}}) THEN 'cowswap'
            WHEN lower(to_address) IN ({{AGG_PARASWAP}}) OR lower(from_address) IN ({{AGG_PARASWAP}}) THEN 'paraswap'
        END AS project,
        usd_value
    FROM ethereum.onchain_trades
    WHERE block_timestamp >= '{{WINDOW_LONG_START}}'
      AND block_timestamp <  '{{WINDOW_END}}'
      AND (lower(to_address) IN ({{AGGREGATORS}}) OR lower(from_address) IN ({{AGGREGATORS}}))
),
agg AS (
    SELECT month, project, sum(usd_value) AS volume_usd, count(*) AS transfers
    FROM m
    WHERE project IS NOT NULL
    GROUP BY month, project
)
SELECT
    month,
    project,
    round(volume_usd, 2) AS volume_usd,
    transfers,
    round(100 * volume_usd / sum(volume_usd) over (partition by month), 2) AS market_share_pct
FROM agg
ORDER BY month DESC, volume_usd DESC;
