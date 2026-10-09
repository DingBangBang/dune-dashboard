# Local Dashboard (Alchemy) — what runs today

This document describes the **executable** layer of the project: a local pipeline
that pulls Ethereum-mainnet data from the supplied **Alchemy** endpoint, aggregates
it, and renders a self-contained HTML dashboard.

Why it exists: Dune now paywalls query creation/execution, and Flipside is shut
down. The Alchemy key that was supplied has no SQL engine, so it cannot run the
`queries/*.sql` files — but it *can* power a subset of the analyses directly.
See [`platform-migration.md`](platform-migration.md) for the full story.

---

## 1. What it produces

```
dashboard/
├── index.html            # open this in a browser
├── dashboard.js          # Chart.js rendering
└── data/                 # raw aggregates (CSV, git-ignored)
    ├── net_flow_daily.csv
    ├── exchange_summary.csv
    ├── asset_breakdown.csv
    └── transfers_sample.csv
```

### Implemented panels (from the original catalogue)

| Original # | Panel | Status |
| --- | --- | --- |
| 02 | Exchange net flow (ETH/USDT) | ✅ implemented (Ethereum mainnet) |
| 06 | CEX inflow/outflow/net by exchange | ✅ implemented |
| — | Daily net-flow-by-exchange bar chart | ✅ (extra panel) |
| — | Net flow by asset (ETH vs stablecoins) | ✅ (extra panel) |
| — | Exchange summary table | ✅ |
| — | KPI counters (net/in/out/transfers/window) | ✅ |

### Pending platform (cannot be computed from RPC/transfers alone)

Listed inside the HTML too:

| # | Panel | Why it needs a SQL warehouse |
| --- | --- | --- |
| 01 | CEX vs DEX ratio | needs DEX trade volume |
| 03 | Aggregator market share | needs decoded `dex_aggregator` routes |
| 04 | Token listing impact | needs per-token swap history |
| 05 | Unique traders per protocol | needs decoded swaps keyed by `tx_from` |
| 07 | DEX volume by blockchain | needs multi-chain trades |
| 08 | Top token pairs | needs decoded swaps w/ symbols |
| 09 | Stablecoin share of DEX volume | needs per-swap legs |
| 10 | Trade size distribution | needs per-swap USD size |

These remain fully specified in `queries/` and are ready to port to any SQL engine.

---

## 2. How to run

```bash
# the conda env is named dune_dashboard (underscore)
conda run -n dune_dashboard python scripts/check_environment.py     # optional
conda run -n dune_dashboard python scripts/alchemy_pipeline.py --smoke
conda run -n dune_dashboard python scripts/alchemy_pipeline.py --days 7 --max-pages 10
```

Flags:

| Flag | Default | Meaning |
| --- | --- | --- |
| `--days N` | 7 | rolling window length |
| `--max-pages N` | 5 | max transfer pages per address/direction (1000 transfers/page) |
| `--exchanges a,b` | all | restrict to specific exchanges |
| `--smoke` | off | 1 address, 1 page — fast connectivity test |

Then open `dashboard/index.html` in a browser.

---

## 3. Method & assumptions (read before quoting numbers)

* **Source:** Alchemy **Transfers API** (`alchemy_getAssetTransfers`) for
  `external` + `erc20` transfers touching each configured CEX address, and the
  Alchemy **Prices API** for ETH/USD.
* **Direction:** a transfer **to** a CEX address = `deposit` (inflow); **from**
  = `withdrawal` (outflow). `net = inflows − outflows`.
* **USD:** stablecoins (USDT/USDC/DAI) valued at **$1.00**; ETH/WETH at the
  **daily close** from the Prices API (falls back to the latest price, and to
  *excluded* if no price is available).
* **Scope:** **Ethereum mainnet only.** No L2s, no other chains.
* **Address list:** `config/cex_addresses.json` — **illustrative labels**, not an
  authoritative directory. **Verify before trusting.**
* **Completeness:** bounded by `--max-pages`. High-traffic wallets produce more
  transfers than one page captures; increase `--max-pages` for fuller coverage.
* **Free-tier limits:** 15 req/s, 30M CU/month. The client throttles to ~10 req/s
  and backs off on 429.

### Known limitations

1. Only the configured addresses are counted → CEX totals are a **lower bound**.
2. One hot wallet per exchange is not the whole exchange.
3. Stablecoin $1.00 is an approximation (depeg events ignored).
4. `erc721`/`erc1155` (NFT) transfers are not included.

---

## 4. Architecture

```
alchemy_client.py     Alchemy RPC + Prices, pagination, throttle, retry/backoff
alchemy_pipeline.py   fetch -> aggregate -> CSV -> index.html + dashboard.js
config/cex_addresses.json   editable exchange -> [addresses] map
```

The client reads the RPC URL/key from `ALCHEMY_RPC_URL` / `ALCHEMY_API_KEY` env
vars, or from the git-ignored `etherum_endpoint_url.txt` / `flipside_cypto_API_ley.txt`.
