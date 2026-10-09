/* Query 04 (Chainbase) — Token listing impact (±7 days) — HISTORICAL SNAPSHOT
 * Source: ethereum.onchain_trades, filtered to one token symbol.
 * Token: {{LISTING_TOKEN}}   Listing date: {{LISTING_DATE}}
 * NOTE: we have no real CEX-listing event feed, so LISTING_DATE is a configurable
 * reference date inside the snapshot window used to illustrate the ±7d window.
 */
SELECT
    date(block_timestamp)                                                        AS day,
    symbol,
    datediff(date(block_timestamp), '{{LISTING_DATE}}')                          AS day_offset,
    round(sum(usd_value), 2)                                                     AS usd_volume,
    count(*)                                                                     AS transfers
FROM ethereum.onchain_trades
WHERE block_timestamp >= date_sub('{{LISTING_DATE}}', interval 7 day)
  AND block_timestamp <  date_add('{{LISTING_DATE}}', interval 8 day)
  AND upper(symbol) = upper('{{LISTING_TOKEN}}')
GROUP BY date(block_timestamp), symbol
ORDER BY day;
