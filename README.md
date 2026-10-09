<!--
  README.md — English is the primary version.
  Chinese translation: README_zh.md
-->

# 📊 Dune Analytics Dashboard — Exchange Market Share Tracker

> A **10-query / 20+ panel** Dune dashboard that maps the competitive landscape of
> **Centralized Exchanges (CEX)**, **Decentralized Exchanges (DEX)** and **DEX aggregators**
> across volume, capital flow, user activity and market structure.

[![Dune](https://img.shields.io/badge/Dune-Dashboard-8A2BE2)](https://dune.com/)
[![Python](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/)
[![SQL](https://img.shields.io/badge/SQL-DuneSQL%20(Trino)-orange)](https://docs.dune.com/query-engine/Functions-and-operators)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

**Dune workspace:** `https://dune.com/workspace/t/bonnieting/home`
**Live dashboard:** `https://dune.com/bonnieting/exchange-market-share-tracker` _(placeholder — see [Screenshots](#-screenshots))_

---

## ⚠️ Platform status — read this first

This project was **designed for Dune Analytics**, and that design is kept fully
intact (`queries/` + `docs/dashboard_guide.md`). It is **not abandoned**. But the
execution environment changed, and this README stays honest about it:

1. **Dune — design kept, execution blocked on the free plan.** Dune moved query
   **creation and execution** behind its **paid plans** (Sept 2025), so the free
   UI/API path no longer works for this account.
2. **Flipside Crypto — not viable: the platform is shut down.** `flipsidecrypto.xyz`,
   `docs.flipsidecrypto.xyz` and `api.flipsidecrypto.xyz` **all 301-redirect to an
   unrelated company** (`edisyl.com`), and `api-v2.flipsidecrypto.xyz` is
   unreachable. There is no Flipside SQL/API left to build on.
3. **The supplied credential is an Alchemy key**, not a Flipside key
   (`alch_…` + an Alchemy Ethereum-mainnet RPC URL). The Alchemy endpoint **works**
   (verified: `eth_blockNumber`, `alchemy_getAssetTransfers`), but Alchemy is a
   node/indexing provider — it has **no SQL engine** and no curated
   `dex.trades` / `dex_aggregator.trades` / `cex.flows` tables.

**Consequence for this repo:**

* ✅ The **full SQL + 20+ panel catalogue is complete and platform-agnostic.**
* ✅ The **Alchemy RPC endpoint is usable** for a subset (CEX net flow,
  address-level flows, token prices).
* ⚠️ Reproducing **all** panels needs a **free SQL-on-chain API** (e.g. Chainbase
  Data Cloud, Space & Time) or a **paid Dune** plan.

📄 **Full evidence, commands and options: [`docs/platform-migration.md`](docs/platform-migration.md).**

> 🔐 The credential files (`flipside_cypto_API_ley.txt`, `etherum_endpoint_url.txt`)
> are **git-ignored** and must never be committed.

---

## 📑 Table of contents

0. [Platform status](#-platform-status--read-this-first)
1. [Why this project exists](#-why-this-project-exists)
2. [Dashboard preview](#-screenshots)
3. [Repository layout](#-repository-layout)
4. [Data sources](#-data-sources)
5. [Core metrics & why they matter in production](#-core-metrics--why-they-matter)
6. [Panel & query catalog](#-panel--query-catalog)
7. [Quick start (reproduce in ~15 min)](#-quick-start)
8. [Dune resources](#-dune-resources)
9. [License](#-license)

---

## 🎯 Why this project exists

A single "total DEX volume" number tells you almost nothing about **who is winning**.
Market structure is the signal. This dashboard was built to answer, on one screen:

| Question | Why it matters |
| --- | --- |
| Is liquidity rotating from CEXs to DEXs (or back)? | The long-term CEX→DEX migration thesis; it drives token economics and exchange strategy. |
| Are users withdrawing coins into self-custody? | CEX net-flow is a classic macro supply indicator (accumulation vs. selling pressure). |
| Which aggregator captures the most routing volume? | Aggregators are the new front-ends; their share decides who owns user intent. |
| Is volume growing because of **more users** or **bigger whales**? | Distinguishes genuine adoption from bot/market-maker churn. |
| Is the market risk-on (long-tail pairs, big trades) or risk-off (stablecoins)? | A regime gauge for trading desks and treasury teams. |

Traditional aggregator stats (DefiLlama etc.) give you volume; they rarely give you
**CEX-vs-DEX ratio, exchange net-flow, unique-trader quality and trade-size mix side by side**,
all reproducible as open SQL. That gap is what this repo fills.

> ⚠️ **Honest data note:** CEX *trading* volume happens off-chain and is **not** available on
> Dune. This project uses the on-chain **CEX settlement flow** (`cex.flows`) as the honest,
> verifiable proxy. See [Metrics](#-core-metrics--why-they-matter) and
> [`docs/development-log.md`](docs/development-log.md) for the reasoning.

---

## 📸 Screenshots

> Placeholders — replace once the dashboard is published. Save PNGs into
> [`docs/screenshots/`](docs/screenshots/) with these exact names.
> (Note: `*.png` is intentionally git-ignored; upload screenshots to Dune/your
> issue tracker and keep them out of git — see the dev log.)

| Panel group | Placeholder | File |
| --- | --- | --- |
| Full dashboard (hero) | `![Dashboard overview](docs/screenshots/00_dashboard_overview.png)` | `00_dashboard_overview.png` |
| CEX vs DEX ratio | `![CEX vs DEX](docs/screenshots/01_cex_dex_ratio.png)` | `01_cex_dex_ratio.png` |
| Exchange net flow | `![Net flow](docs/screenshots/02_exchange_net_flow.png)` | `02_exchange_net_flow.png` |
| Aggregator market share | `![Aggregator share](docs/screenshots/03_aggregator_market_share.png)` | `03_aggregator_market_share.png` |
| Token listing impact | `![Listing impact](docs/screenshots/04_token_listing_impact.png)` | `04_token_listing_impact.png` |
| Unique traders | `![Unique traders](docs/screenshots/05_unique_traders.png)` | `05_unique_traders.png` |

---

## 🗂 Repository layout

```
dune-dashboard/
├── queries/                        # DuneSQL scripts (one file = one Dune query)
│   ├── 01_cex_dex_ratio.sql
│   ├── 02_exchange_net_flow.sql
│   ├── 03_aggregator_market_share.sql
│   ├── 04_token_listing_impact.sql
│   ├── 05_unique_traders.sql
│   ├── 06_cex_flow_by_exchange.sql
│   ├── 07_dex_volume_by_chain.sql
│   ├── 08_top_token_pairs.sql
│   ├── 09_stablecoin_share.sql
│   ├── 10_trade_size_distribution.sql
│   └── dune_query_ids.json         # generated: local file -> Dune query id/url
├── docs/
│   ├── dashboard_guide.md          # step-by-step Dashboard build guide
│   ├── development-log.md          # design rationale, trade-offs, perf notes
│   ├── metrics.md                  # metric definitions + production meaning
│   ├── query-catalog.md            # query -> panel -> visualization mapping
│   └── screenshots/                # dashboard screenshots (.gitkeep tracked)
├── scripts/
│   ├── create_queries.py           # create all queries on Dune via API
│   └── check_environment.py        # env / repo self-check
├── environment.yml                 # conda env (python 3.11 + deps)
├── requirements.txt
├── .env.example                    # DUNE_API_KEY template
├── LICENSE
├── README.md                       # ← you are here (EN)
└── README_zh.md                    # 中文版
```

---

## 🗄 Data sources

All tables are **Dune curated** datasets and are cross-chain (unless noted).

| Table | Used by | What it gives us |
| --- | --- | --- |
| `dex.trades` | 01, 04, 05, 07, 08, 09, 10 | Granular DEX swap events (each pool hop = 1 row) with `amount_usd`, `tx_from`, `token_pair`, `blockchain`. |
| `dex_aggregator.trades` | 03 | **User-intended** aggregated trades — 1 multi-hop route = 1 row. The correct table for aggregator volume/share. |
| `cex.flows` | 01, 02, 06 | CEX deposit/withdrawal events with `cex_name` entity attribution, `flow_type`, `amount_usd`. |
| `cex.addresses` | reference | Directory of CEX-controlled addresses underpinning `cex.flows`. |
| `tokens.transfers` | alternative to 02 | Raw ERC-20/native transfers (Coinpaprika pricing) — used as a fallback if you need token-level balance reconstruction. |

> Schemas verified against the official catalog:
> [`dex.trades`](https://docs.dune.com/data-catalog/curated/dex-trades/evm/dex-trades) ·
> [`dex_aggregator.trades`](https://docs.dune.com/data-catalog/curated/dex-trades/evm/dex-aggregator-trades) ·
> [`cex.flows`](https://docs.dune.com/data-catalog/curated/cex-flows/flows).

---

## 📐 Core metrics & why they matter

| Metric | Definition | Production meaning |
| --- | --- | --- |
| **CEX/DEX ratio** | Daily CEX on-chain settlement volume ÷ DEX traded volume. | Trend, not level. A falling ratio = liquidity rotating on-chain; used as a long-horizon structural bet. |
| **CEX net flow** | `Σ deposits − Σ withdrawals` (USD) per exchange per day. | Positive = coins inbound (potential sell pressure). Negative = self-custody accumulation. Read with price, not alone. |
| **Aggregator market share** | Project routed volume ÷ total aggregator volume for the month. | Shows which front-end owns user intent. A share gain without volume growth = competitor decay, not organic growth. |
| **Unique traders** | `COUNT(DISTINCT tx_from)` per project per day. | Real user base. Pair with volume to separate *adoption* from *whale/bot churn*. |
| **Trades per trader** | `trades ÷ unique_traders`. | A spiking ratio = bot/MEV activity, not retail growth. An important data-quality guard. |
| **Listing impact (±7d)** | Token DEX volume in the 14 days straddling a CEX listing. | Quantifies the "listing pump". Volume rising *before* listing = informed/front-run flow. |
| **Stablecoin share** | Stablecoin-leg volume ÷ total DEX volume. | High = risk-off / de-risking regime. Low = risk-on speculation. |
| **Trade-size mix** | Volume/count share by USD bucket. | Rising `≥$1M` share = institutional participation; rising `<$100` count share = retail. |

Full formulas, edge cases and caveats: [`docs/metrics.md`](docs/metrics.md).

---

## 🧩 Panel & query catalog

10 queries expand to **20+ panels**. Full mapping (query → chart type → columns →
filters): [`docs/query-catalog.md`](docs/query-catalog.md).

| # | Query | Primary visualization |
| --- | --- | --- |
| 01 | CEX vs DEX daily volume & ratio | Mixed bar + line |
| 02 | Exchange net flow (ETH/USDT) | Grouped bar |
| 03 | Aggregator market share (monthly) | Stacked area + table |
| 04 | Token CEX-listing impact (±7d) | Line chart (parameterized) |
| 05 | Unique traders per protocol | Multi-series line |
| 06 | CEX inflow/outflow by exchange | Horizontal bar |
| 07 | DEX volume by blockchain | Stacked area |
| 08 | Top token pairs (30d) | Table + bar |
| 09 | Stablecoin share of DEX volume | Line (+ 7d MA) |
| 10 | Trade size distribution | Stacked bar (100%) |

---

## 🚀 Quick start

### 1. Clone & enter

```bash
git clone https://github.com/DingBangBang/dune-dashboard.git
cd dune-dashboard
```

### 2. Create the conda environment

```bash
conda env create -f environment.yml
conda activate dune-dashboard
conda run -n dune-dashboard python scripts/check_environment.py
```

### 3. Create the queries on Dune

**Option A — manual (works on the FREE plan, recommended).**
Open the editor at <https://dune.com/queries> → **New query**, paste each file from
`queries/` (tip: `pbcopy < queries/01_cex_dex_ratio.sql` then `⌘V`), **Run**, then
**Save** with the names listed in
[`docs/dashboard_guide.md`](docs/dashboard_guide.md) §1.1. For **query 04 only**,
add two *Text* parameters first: `token_symbol` = `PEPE`, `listing_date` = `2023-05-05`.
👉 Full click-by-click walkthrough: **[`docs/dashboard_guide.md`](docs/dashboard_guide.md)**.

**Option B — automated (requires a Dune Analyst plan).**
The Dune Query API is not available on the free plan. If you upgrade, add your key
and run the script:

```bash
cp .env.example .env      # then paste your DUNE_API_KEY (Dune → Settings → API)
conda run -n dune-dashboard python scripts/create_queries.py --dry-run   # preview
conda run -n dune-dashboard python scripts/create_queries.py             # create
```

This writes `queries/dune_query_ids.json` with the query IDs/URLs.


### 4. Build the Dashboard (UI)

The Dune API cannot create dashboard widgets, so this step is in the browser —
full click-by-click instructions in **[`docs/dashboard_guide.md`](docs/dashboard_guide.md)**:

1. Create → **New Dashboard**, name it `exchange-market-share-tracker`.
2. For each query: Run → choose a Visualization → **Add to Dashboard**.
3. Set the dashboard-level **time filter** to *Last 90 days*.
4. **Save** → **Share → Public** → copy the public URL.

### 5. Screenshots & docs

Save the PNGs into `docs/screenshots/` (names in [Screenshots](#-screenshots)),
update the placeholder link at the top of this README, and log what you changed.

---

## 🔁 Reproducing from scratch — checklist

- [ ] `git clone` + `conda env create -f environment.yml`
- [ ] Get a Dune API key (Analyst plan) → `.env`
- [ ] `python scripts/create_queries.py` (or paste 10 SQL files manually)
- [ ] Build the dashboard ([guide](docs/dashboard_guide.md))
- [ ] Apply the *Last 90 days* filter + schedule daily refresh
- [ ] Publish → replace the URL placeholder + add screenshots

---

## 📚 Dune resources

- 🚀 **Build Dashboards (deep dive) → https://docs.dune.com/web-app/dashboards**
- Query editor: <https://docs.dune.com/web-app/query-editor/index>
- Parameters: <https://docs.dune.com/web-app/query-editor/parameters>
- Charts & visualizations: <https://docs.dune.com/web-app/visualizations/charts-graphs>
- Data catalog: <https://docs.dune.com/data-catalog/curated/dex-trades/overview>
- Data API: <https://docs.dune.com/api-reference/api-overview>
- Trino SQL functions: <https://docs.dune.com/query-engine/Functions-and-operators>

---

## 📄 License

[MIT](LICENSE) © 2026 bonnieting / DingBangBang



