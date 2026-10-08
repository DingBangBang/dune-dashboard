# Dune Dashboard Build Guide — Exchange Market Share Tracker

> **Audience:** you, on the `bonnieting` account, logged in at
> <https://dune.com/workspace/t/bonnieting/home>.
>
> **Goal:** go from the SQL files in this repo to a published, public Dune
> Dashboard with 20+ panels.
>
> **Time:** ~15–25 minutes.

---

## 0. Prerequisites

| Requirement | Notes |
| --- | --- |
| Dune account `bonnieting` | Already set up. |
| A **Dune API key** (only for the automated path) | Settings → API → *Create new API key*. Needs an **Analyst** plan for the Query CRUD endpoints. |
| `gh` / `git` | Already installed and authenticated on this machine. |

> **What can be automated, and what cannot.**
> The Dune REST API can **create/update/execute queries**, but it has **no
> endpoint for creating dashboard widgets or dashboards**. So:
> * **Steps 1–3 (queries)** → scriptable via `scripts/create_queries.py`.
> * **Steps 4–9 (dashboard, visuals, filter, publish, screenshot)** → must be done
>   in the browser UI. The instructions below are click-by-click on purpose.

---

## Part A — Create the 10 queries

### A1. Automated (recommended)

```bash
cd ~/Desktop/dune-dashboard

# 1. Add your key
cp .env.example .env
#   open .env and set DUNE_API_KEY=...   (Dune → Settings → API)

# 2. Preview, then create
conda run -n dune-dashboard python scripts/create_queries.py --dry-run
conda run -n dune-dashboard python scripts/create_queries.py
```

Expected output:

```
[create] 01_cex_dex_ratio.sql -> query #XXXXXXX
...
Saved id map -> queries/dune_query_ids.json
```

`queries/dune_query_ids.json` now maps every local file to its Dune query ID +
URL — keep it, it's your manifest for the dashboard.

### A2. Manual fallback

If you don't have an API key (or want to review each query first):

1. Open the query editor: <https://dune.com/queries/7552102>.
2. Copy the contents of `queries/01_cex_dex_ratio.sql` into the editor.
3. **Save** (top-right). When asked, name it e.g. `01 · CEX vs DEX Daily Volume & Ratio`.
4. For each remaining file: **New query** → paste → **Save**.
5. For **query 04 only**, add two parameters (*Parameters* panel):
   * `token_symbol` — Text — default `PEPE`
   * `listing_date` — Text — default `2023-05-05`

> If a query errors on a column name, the catalog may have shifted. All schemas
> here were checked against
> <https://docs.dune.com/data-catalog/curated/dex-trades/overview> and
> <https://docs.dune.com/data-catalog/curated/cex-flows/overview>.

---

## Part B — Create the Dashboard

1. Click the **Create** button (top-left) → **New Dashboard**.
2. Name it exactly: `exchange-market-share-tracker`.
   > ⚠️ The name you type here becomes the **URL slug and cannot be changed later**.
   > You can rename the *display* title afterwards, but not the slug.
3. Click **Save and Open**. You are now inside the dashboard (empty).
4. Click **Edit** (top-right) to enter edit mode.

---

## Part C — Add widgets (the 20+ panels)

The universal loop for every query:

> **Open query → Run → pick Visualization type → map the columns →
> "Add to Dashboard" → choose `exchange-market-share-tracker`.**

Widgets are appended at the bottom; drag to reposition, drag the bottom-right
corner to resize. Save often (top-right **Save**).

Use the table below. "Viz" is the visualization type; "X / Y / Series" is the
column mapping inside the chart editor.

| # | Query file | Viz | X axis | Y axis / Value | Series / Group by |
| --- | --- | --- | --- | --- | --- |
| 1 | `01_cex_dex_ratio.sql` | **Mixed (bar + line)** | `day` | bars: `dex_volume_usd`, `cex_onchain_volume_usd`; line: `cex_dex_ratio` | — |
| 2 | `01_...` | Counter | — | latest `cex_dex_ratio` | — |
| 3 | `02_exchange_net_flow.sql` | **Bar (grouped)** | `day` | `net_flow_usd` | `exchange_name` |
| 4 | `02_...` | Table | — | all columns | — |
| 5 | `03_aggregator_market_share.sql` | **Stacked Area** | `month` | `volume_usd` | `project` |
| 6 | `03_...` | Table | — | `month, project, volume_usd, market_share_pct, mom_growth_pct` | — |
| 7 | `04_token_listing_impact.sql` | **Line** | `day_offset` | `dex_volume_usd`, `trailing14d_avg_usd`, `forward14d_avg_usd` | — |
| 8 | `05_unique_traders.sql` | **Multi-series Line** | `day` | `unique_traders` | `project` |
| 9 | `05_...` | Line | `day` | `trades_per_trader` | `project` |
| 10 | `06_cex_flow_by_exchange.sql` | **Horizontal Bar** | `net_flow_usd` | `exchange_name` (category) | — |
| 11 | `06_...` | Table | — | all columns | — |
| 12 | `07_dex_volume_by_chain.sql` | **Stacked Area** | `week` | `volume_usd` | `blockchain` |
| 13 | `07_...` | Line | `week` | `chain_share_pct` | `blockchain` |
| 14 | `08_top_token_pairs.sql` | **Table** (top 50) | — | all columns | — |
| 15 | `08_...` | Bar | `token_pair` | `volume_usd` | — |
| 16 | `09_stablecoin_share.sql` | **Line** | `day` | `stablecoin_share_pct`, `share_7d_ma` | — |
| 17 | `10_trade_size_distribution.sql` | **Stacked Bar (100%)** | `week` | `volume_share_pct` | `size_bucket` |
| 18 | `10_...` | Stacked Bar (100%) | `week` | `trade_count_share_pct` | `size_bucket` |
| 19 | Header / KPI row | **Text widget** | — | Markdown title + context | — |
| 20 | Section labels | **Text widget** | — | e.g. `## A. CEX ↔ DEX flows` | — |

> Tip: you can produce several visualizations from a single query — you do **not**
> need to duplicate the query. Each visualization can be added to the dashboard.

### Text widgets (panels 19–20)

Use text widgets as section headers so a viewer can navigate. Markdown subset is
supported. Example:

```markdown
# Exchange Market Share Tracker
_last updated: daily 06:00 UTC · source: Dune curated tables_

## A. CEX ↔ DEX structural flows
## B. Aggregator routing market
## C. Token-level & user-level dynamics
```

---

## Part D — Time filter (Last 90 days)

Dune has two ways to constrain time. Use **both** where relevant:

1. **Query-level (already in the SQL).** Every query filters
   `block_month >= date_trunc('month', current_date - INTERVAL '90' DAY)`.
   `block_month` is the **partition column**, so this is also what keeps queries
   fast (see `docs/development-log.md`).
2. **Dashboard-level filter (for interactivity).** On the dashboard, click
   **Filter** (or the funnel icon) → **Add filter** → **Time range** →
   select **Last 90 days** → apply to the time-series widgets.
   This lets a viewer switch to 30d/180d without editing SQL.

To change the default window for everything, edit the `INTERVAL 'N' DAY` literal
in each SQL file and re-run `scripts/create_queries.py` (it updates in place).

---

## Part E — Layout

Recommended reading order (top → bottom):

```
[ KPI counters: CEX/DEX ratio · aggregator leader · total DEX 24h volume ]
[ A. text ]  [ 01 mixed chart (wide) ]  [ 02 net flow bar ]
[ 06 exchange bar ]  [ 03 aggregator stacked area ]  [ 03 table ]
[ B. text ]  [ 07 chain stacked area ]  [ 08 top pairs table ]  [ 08 bar ]
[ C. text ]  [ 05 unique traders ]  [ 09 stablecoin share ]  [ 10 size mix ]
[ 04 listing impact (own row, parameterized) ]
```

Drag widgets in edit mode; each dashboard row is a 12-column grid. Make the hero
charts full-width (12 cols) and the small ones 4–6 cols.

---

## Part F — Schedule refresh

1. On the dashboard, click the **clock / schedule** icon (top-right).
2. Choose a frequency (e.g. **Daily**).
3. Pick an execution tier (use the cheapest that fits your plan).
4. **Save**.

You can also schedule *individual* queries if only a few need frequent updates
(e.g. daily for 01/05/07, weekly for 03/08/10).

---

## Part G — Publish & get the public URL

1. **Save** the dashboard.
2. Click **Share** (top-right).
3. Set visibility to **Public** (and enable embedding if you want iframes).
4. Copy the public URL — it will look like:

   ```
   https://dune.com/bonnieting/exchange-market-share-tracker
   ```

5. Paste it into:
   * `README.md` — the *Live dashboard* line at the top (replace the placeholder).
   * `README_zh.md` — same line.
   * `docs/query-catalog.md` — header block.

> **Read more:** <https://docs.dune.com/web-app/share>

---

## Part H — Screenshots

Save PNGs (e.g. via `⌘⇧4` on macOS) into `docs/screenshots/` using these names:

```
00_dashboard_overview.png     ← full dashboard, hero image
01_cex_dex_ratio.png
02_exchange_net_flow.png
03_aggregator_market_share.png
04_token_listing_impact.png
05_unique_traders.png
06_cex_flow_by_exchange.png
07_dex_volume_by_chain.png
08_top_token_pairs.png
09_stablecoin_share.png
10_trade_size_distribution.png
```

> `*.png` is **git-ignored by design** (see `.gitignore`): screenshots are large
> binaries and are "managed separately". Upload them to Dune, a GitHub issue, or
> an image host, then embed by URL in the README. If you *do* want them in git,
> remove the `*.png` line from `.gitignore` (and keep them small).

**Embedding in a Dune text widget** (Dune can't host files): upload the image
somewhere public and use `![alt text](https://.../image.png)` inside a text
widget. See <https://docs.dune.com/web-app/dashboards>.

---

## Part I — Update the README placeholders

After publishing, replace the placeholders:

* `README.md` / `README_zh.md`:
  `**Live dashboard:** https://dune.com/bonnieting/exchange-market-share-tracker`
* Add real screenshots or image URLs in the **Screenshots** table.
* Append a line to `docs/development-log.md` under *Changelog* with the publish date.

---

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `create_queries.py` → `401` | API key wrong/expired. Regenerate in Settings → API. |
| `create_queries.py` → `402/403` | Query API needs an **Analyst** plan. Use the manual path (A2). |
| `Column 'block_date' cannot be resolved` on `cex.flows` | `cex.flows` uses `block_time` (+ `block_month` partition); the SQL already casts `date_trunc('day', block_time)`. |
| Query is slow / times out | Confirm the `block_month` filter survived your edits; never widen it to `block_time`. See dev log. |
| Aggregator volume looks tiny | Make sure you're on `dex_aggregator.trades`, not `dex.trades` (the latter double-counts hops). |
| Chart shows a flat line | The column mapped to Y may be a string; cast `ROUND(...)` outputs are already numeric. |
| Time filter hides data | Dashboard filter and SQL filter are independent — align them. |

---

## Reference: official docs

* Build Dashboards — **https://docs.dune.com/web-app/dashboards**
* Charts & Graphs — https://docs.dune.com/web-app/visualizations/charts-graphs
* Tables — https://docs.dune.com/web-app/visualizations/tables
* Counters — https://docs.dune.com/web-app/visualizations/counters
* Parameters — https://docs.dune.com/web-app/query-editor/parameters
* Share & Embed — https://docs.dune.com/web-app/share
* Schedule queries — https://docs.dune.com/web-app/query-editor/schedule (see *Keep your dashboard up to date*)

