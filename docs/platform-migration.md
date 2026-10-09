# Platform Migration Record (ADR) — why the dashboard moved, and to what

**Status:** Investigation complete · **Date:** 2026-10-09 · **Author:** Cline (for `bonnieting`)

This document records, truthfully and with reproducible evidence, the platform
history of this project. It exists so the repo does not silently pretend the
original Dune plan went ahead unchanged.

---

## 1. TL;DR

| Question | Answer |
| --- | --- |
| Did we build on Dune? | **Design yes, execution no.** Dune now requires a **paid plan** (Analyst+) to create *and* execute queries via the UI/API, so the free path is closed. The full Dune SQL + panel plan is **kept** in this repo (it is the canonical design). |
| Did we move to Flipside? | **No — Flipside is defunct.** Its domains all redirect to an unrelated company (`edisyl.com`), and its API host is unreachable. |
| What credential was actually supplied? | An **Alchemy** key (`alch_…`) + an **Alchemy Ethereum-mainnet RPC URL**. Not a Flipside key. |
| Can Alchemy run our SQL? | **No.** Alchemy is an RPC + indexed-data (transfers/token/prices) platform. It has **no SQL engine** and no curated `dex.trades` / `dex_aggregator.trades` / `cex.flows` equivalents. |
| Net result | The SQL + panel catalogue is complete and platform-agnostic; the *executable* target must be chosen (see §5). |

---

## 2. Evidence (reproducible)

### 2.1 The supplied "Flipside key" is an Alchemy key

```
$ tr -d '\n' < flipside_cypto_API_ley.txt | head -c 4
alch          # <-- Alchemy key prefix, not a Flipside UUID
$ wc -c < flipside_cypto_API_ley.txt
26            # 25-char key + newline
```

The companion file `etherum_endpoint_url.txt` contains:

```
https://eth-mainnet.g.alchemy.com/v2/***REDACTED***
```

…i.e. a standard Alchemy Ethereum-mainnet JSON-RPC endpoint.

### 2.2 That Alchemy endpoint works

```
POST https://eth-mainnet.g.alchemy.com/v2/***  {"method":"eth_blockNumber"}
-> {"jsonrpc":"2.0","id":1,"result":"0x18f0966"}      # live, authenticated

POST ... {"method":"alchemy_getAssetTransfers",
          "params":[{"toAddress":"0x28c6...1d60"  (Binance hot wallet),
                     "category":["external","erc20"], ...}]}
-> {"result":{"transfers":[{"asset":"LINK","value":2014.11,
             "metadata":{"blockTimestamp":"2026-10-08T02:44:11Z"}}, ...]}}
```

### 2.3 Flipside is shut down

```
$ curl -s -o /dev/null -w '%{http_code} -> %{redirect_url}\n' https://flipsidecrypto.xyz
301 -> https://edisyl.com/
$ curl -s -o /dev/null -w '%{http_code} -> %{redirect_url}\n' https://docs.flipsidecrypto.xyz
301 -> https://edisyl.com/
$ curl -s -o /dev/null -w '%{http_code} -> %{redirect_url}\n' https://api.flipsidecrypto.xyz
301 -> https://edisyl.com/
$ curl -s -o /dev/null -w '%{http_code}\n' https://api-v2.flipsidecrypto.xyz
000                 # DNS resolves but host unreachable
```

**All Flipside domains (site, docs, API) now redirect to `edisyl.com`, an
unrelated company.** There is no Flipside SQL/API service to build on.

---

## 3. What Alchemy CAN and CANNOT do for this project

| Capability | Alchemy? | Notes |
| --- | --- | --- |
| Ethereum RPC (`eth_getLogs`, `eth_call`, `eth_blockNumber`) | ✅ | Works; free tier 15 RPS, 30M CU/month, 5 apps. |
| Indexed transfers (`alchemy_getAssetTransfers`) | ✅ | Verified. Gives from/to, value, asset, timestamp. Great for **CEX net flow**. |
| Token / Prices / Portfolio APIs | ✅ | Metadata + historical USD prices. |
| **Run SQL** | ❌ | No SQL engine at all. |
| Curated `dex.trades` (per-swap, USD, multi-chain) | ❌ | Would need us to *build an indexer* from raw logs. |
| Curated `dex_aggregator.trades` | ❌ | Same. |
| `cex.flows` with entity attribution | ❌ | We can approximate from a hardcoded CEX-address list + Transfers API (Ethereum only). |
| 90 days × all chains aggregation | ❌ | Free-tier CU/RPS and `eth_getLogs` block-range limits make a full re-index impractical. |

**Consequence:** an RPC/transfers-only free tier cannot reproduce the 10 planned
multi-chain, 90-day, curated-table analyses. Full parity requires a **free SQL
warehouse with an API**, or re-enabling Dune.

---

## 4. Security note

`flipside_cypto_API_ley.txt` and `etherum_endpoint_url.txt` hold a live key.
They are **untracked and now git-ignored** (`*.txt` + explicit filenames).
**Never `git add` them.** If this key was ever exposed, rotate it in the Alchemy
dashboard. Remove them from the working tree before any `git add -A`.

---

## 5. Options going forward

| # | Option | Full 20+ panels? | Cost | Needs |
| --- | --- | --- | --- | --- |
| A | **Free SQL-on-chain API** (e.g. Chainbase Data Cloud SQL API, Space & Time) — port the 10 queries to that engine and build the dashboard there via API | ✅ (with SQL rewrite) | Free tier | A key for that platform |
| B | **Alchemy-only local pipeline + local HTML dashboard** — executable now; covers CEX net flow, address-level flows, token prices; cannot cover aggregator share / multi-chain DEX volume | ⚠️ partial | Free | Already have it |
| C | **Upgrade Dune** (Analyst) — run `scripts/create_queries.py` unchanged | ✅ | Paid | Dune Analyst |
| D | **Keep Dune as design + publish the free-platform guide** — document and leave execution to the user's chosen platform | ✅ (by user's hand) | Free | User runs it |

**Recommendation:** **A** (best parity on a free tier) with **D** as the fallback.

---

## 6. Changelog

| Date | Change |
| --- | --- |
| 2026-10-09 | Recorded: Dune paywalled for query create/execute; Flipside defunct (domains → edisyl.com); supplied credential is an Alchemy key (Ethereum RPC works, no SQL). Git-ignored credential files. |
