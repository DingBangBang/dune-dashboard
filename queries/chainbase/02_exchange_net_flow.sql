/* Query 02 (Chainbase) — Exchange net flow — HISTORICAL SNAPSHOT
 * Source: ethereum.onchain_trades. Deposits = transfers INTO a CEX address,
 * withdrawals = transfers OUT of one. USD from the table's usd_value.
 * Output: exchange_name, day, inflow_usd, outflow_usd, net_flow_usd
 * Window: {{WINDOW_START}} .. {{WINDOW_END}}
 */
WITH tagged AS (
    SELECT
        date(block_timestamp) AS day,
        usd_value,
        CASE
            WHEN lower(to_address) IN ({{CEX_ADDRESSES}}) THEN
                CASE
                    WHEN lower(to_address) IN ({{EX_BINANCE}})  THEN 'binance'
                    WHEN lower(to_address) IN ({{EX_COINBASE}}) THEN 'coinbase'
                    WHEN lower(to_address) IN ({{EX_KRAKEN}})   THEN 'kraken'
                    WHEN lower(to_address) IN ({{EX_BITFINEX}}) THEN 'bitfinex'
                    WHEN lower(to_address) IN ({{EX_OKX}})      THEN 'okx'
                    WHEN lower(to_address) IN ({{EX_BYBIT}})    THEN 'bybit'
                    ELSE 'other' END
            ELSE
                CASE
                    WHEN lower(from_address) IN ({{EX_BINANCE}})  THEN 'binance'
                    WHEN lower(from_address) IN ({{EX_COINBASE}}) THEN 'coinbase'
                    WHEN lower(from_address) IN ({{EX_KRAKEN}})   THEN 'kraken'
                    WHEN lower(from_address) IN ({{EX_BITFINEX}}) THEN 'bitfinex'
                    WHEN lower(from_address) IN ({{EX_OKX}})      THEN 'okx'
                    WHEN lower(from_address) IN ({{EX_BYBIT}})    THEN 'bybit'
                    ELSE 'other' END
        END AS exchange_name,
        CASE WHEN lower(to_address) IN ({{CEX_ADDRESSES}}) THEN 'deposit' ELSE 'withdrawal' END AS direction
    FROM ethereum.onchain_trades
    WHERE block_timestamp >= '{{WINDOW_START}}'
      AND block_timestamp <  '{{WINDOW_END}}'
      AND (lower(to_address) IN ({{CEX_ADDRESSES}}) OR lower(from_address) IN ({{CEX_ADDRESSES}}))
)
SELECT
    exchange_name,
    day,
    round(sum(case when direction = 'deposit'    then usd_value else 0 end), 2) AS inflow_usd,
    round(sum(case when direction = 'withdrawal' then usd_value else 0 end), 2) AS outflow_usd,
    round(sum(case when direction = 'deposit'    then usd_value else -usd_value end), 2) AS net_flow_usd
FROM tagged
GROUP BY exchange_name, day
ORDER BY day DESC, exchange_name;
