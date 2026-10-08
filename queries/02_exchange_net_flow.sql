/* ============================================================================
 * Query 02 — Exchange Net Flow (ETH / USDT, daily)
 * ----------------------------------------------------------------------------
 * PURPOSE
 *   Track the daily net on-chain flow of ETH/WETH/USDT into and out of the
 *   major centralized exchanges. Positive net flow = net deposits (bearish /
 *   supply moving to venues); negative = net withdrawals (self-custody).
 *
 * DATA SOURCES
 *   cex.flows     -> curated deposit/withdrawal flows with CEX attribution.
 *   cex.addresses -> (reference) CEX address directory, used upstream to build
 *                    cex.flows. Not joined directly here for performance.
 *
 * WHY cex.flows INSTEAD OF cex.balances
 *   The historical `cex.balances` snapshot table was retired in favour of the
 *   event-based `cex.flows` / `cex.deposit_addresses` datasets. Net flow can be
 *   reconstructed from flows without needing a balance snapshot, and it scales
 *   across the 29 supported chains.
 *
 * GRAIN / RANGE
 *   One row per (exchange_name, day), last 90 days.
 *
 * OUTPUT COLUMNS
 *   exchange_name, day, net_flow_usd, inflow_usd, outflow_usd
 *
 * VISUALIZATION
 *   Bar chart (net_flow_usd by day, grouped by exchange_name) or a table.
 * ==========================================================================*/

WITH target_exchanges AS (
    SELECT *
    FROM (
        VALUES
            ('binance'), ('coinbase'), ('okx'), ('bybit'), ('kraken'),
            ('gate.io'), ('htx'), ('kucoin'), ('bitfinex'), ('robinhood')
    ) AS t(cex_name)
),

flows AS (
    SELECT
        f.cex_name AS exchange_name,
        CAST(date_trunc('day', f.block_time) AS DATE) AS day,
        SUM(CASE WHEN lower(f.flow_type) = 'deposit'
                 THEN f.amount_usd ELSE -f.amount_usd END)          AS net_flow_usd,
        SUM(CASE WHEN lower(f.flow_type) = 'deposit'
                 THEN f.amount_usd ELSE 0 END)                      AS inflow_usd,
        SUM(CASE WHEN lower(f.flow_type) = 'withdrawal'
                 THEN f.amount_usd ELSE 0 END)                      AS outflow_usd
    FROM cex.flows f
    INNER JOIN target_exchanges t
        ON lower(f.cex_name) = t.cex_name
    WHERE f.block_month >= date_trunc('month', current_date - INTERVAL '90' DAY)
      AND lower(f.token_symbol) IN ('eth', 'weth', 'usdt')
      AND f.amount_usd IS NOT NULL
    GROUP BY 1, 2
)

SELECT
    exchange_name,
    day,
    ROUND(net_flow_usd, 2) AS net_flow_usd,
    ROUND(inflow_usd, 2)   AS inflow_usd,
    ROUND(outflow_usd, 2)  AS outflow_usd
FROM flows
ORDER BY day DESC, exchange_name;
