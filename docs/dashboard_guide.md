# Dune Dashboard Build Guide — Exchange Market Share Tracker

> **适用对象：** 你本人，`bonnieting` 账号，已登录
> <https://dune.com/workspace/t/bonnieting/home>
>
> **目标：** 从 `queries/` 里的 SQL 文件，手工搭出一个 **已发布、公开可访问** 的
> Dune Dashboard（10 个 widget 数据源 → 20+ 个 Panel）。
>
> **方式：** **免费版（Free plan）+ 纯手动**。不需要 API Key，不需要 Analyst 套餐。
>
> **预计耗时：** 首次约 40–60 分钟（跟着做即可，每一步都写死了点哪里）。

---

## 0. 先读这一节：免费版能做什么、不能做什么

| 能力 | 免费版 | 说明 |
| --- | --- | --- |
| 写查询（DuneSQL） | ✅ | 免费版有月度 Credit 额度（约 2500 credits/月）；本项目的查询都做了分区裁剪，单次执行很省。 |
| 保存查询 | ✅ | 无数量限制（合理使用）。 |
| 新建 Dashboard | ✅ | 数量够用。 |
| 添加 Visualization / widget | ✅ | 免费可用。 |
| 发布为**公开** Dashboard | ✅ | 免费版 Dashboard 默认就是公开的，任何人可访问。 |
| **Query API**（`scripts/create_queries.py`） | ❌ | 需要 **Analyst** 及以上套餐。所以本指南走**手动**路径。 |
| 私有 Dashboard / 定时刷新高级档 | ❌ | 免费版仅公开。定时刷新可用低档执行层。 |

> 因此：**本指南是唯一可行的搭建路径**。`scripts/create_queries.py` 请忽略（将来升级套餐再用）。
> 你需要的只是一双手 + 浏览器。

**做完后你会得到：**

1. 10 条已保存的 Dune 查询（前缀 `01 ·` … `10 ·`）。
2. 1 个名为 `exchange-market-share-tracker` 的公开 Dashboard。
3. 约 20 个 Panel（图表 + 表格 + 计数器 + 文字块）。
4. `docs/screenshots/` 下的一批截图。

---

## 1. 准备：把 SQL 文件放到手边

所有 SQL 在本机：

```
/Users/dingbangchu/Desktop/dune-dashboard/queries/
```

**推荐做法（最快）：** 打开一个终端，用 `pbcopy` 把文件内容直接送进剪贴板，
再去 Dune 编辑器里 `⌘V` 粘贴。逐条执行：

```bash
cd /Users/dingbangchu/Desktop/dune-dashboard
pbcopy < queries/01_cex_dex_ratio.sql    # 内容已进剪贴板，去 Dune 粘贴
```

或者用编辑器打开整个目录：

```bash
code /Users/dingbangchu/Desktop/dune-dashboard/queries   # VS Code
```

### 1.1 文件清单与建议的 Dune 查询名

保存查询时，**用下面这一列的名字**（和 `docs/query-catalog.md` 一致，方便对照）：

| 本地文件 | 存到 Dune 时用的名字 | 是否带参数 |
| --- | --- | --- |
| `01_cex_dex_ratio.sql` | `01 · CEX vs DEX Daily Volume & Ratio` | 否 |
| `02_exchange_net_flow.sql` | `02 · Exchange Net Flow (ETH/USDT)` | 否 |
| `03_aggregator_market_share.sql` | `03 · DEX Aggregator Market Share` | 否 |
| `04_token_listing_impact.sql` | `04 · Token CEX-Listing Impact (±7d)` | **是（2 个）** |
| `05_unique_traders.sql` | `05 · Unique Traders per Protocol` | 否 |
| `06_cex_flow_by_exchange.sql` | `06 · CEX Inflow/Outflow by Exchange` | 否 |
| `07_dex_volume_by_chain.sql` | `07 · DEX Volume by Blockchain` | 否 |
| `08_top_token_pairs.sql` | `08 · Top Token Pairs (30d)` | 否 |
| `09_stablecoin_share.sql` | `09 · Stablecoin Share of DEX Volume` | 否 |
| `10_trade_size_distribution.sql` | `10 · Trade Size Distribution` | 否 |

---

## 2. 逐条创建查询

### 2.0 通用循环（10 条查询都照这个做一遍）

> 你打开的 <https://dune.com/queries/7552102> 是一个临时查询页。为了干净，我们每条都
> 用「新建查询」而不是复用同一个。

1. **新建空查询。** 点左上角 **Create**（或 **+ New**）→ **New query**。
   （也可以直接访问 <https://dune.com/queries> 后点 **New query**。）
2. **清空编辑器。** 点进代码区，按 `⌘A` 全选 → `Delete`，确保是空白。
3. **粘贴 SQL。** `pbcopy < queries/01_cex_dex_ratio.sql` 后在该页 `⌘V`。
4. **确认引擎 = DuneSQL。** 编辑器右上角应显示 **DuneSQL**（默认即是；若显示 v2/SparkSQL 请切回 DuneSQL）。
5. **运行。** 点右上角 **Run** 或按 `⌘⏎`。等状态从 *Executing* 变为 *Completed*（首次可能 10–40 秒）。
6. **看结果网格。** 下方 **Results** 标签会显示表头 + 数据行；右上角有 **rows / 耗时**。若报错，见 [§12 排错](#12-排错troubleshooting)。
7. **保存并命名。** 按 `⌘S`（或点 **Save**）→ 在弹出的名称框里填 §1.1 表里的名字 → **Save**。
8. **记下 Query ID。** 保存后地址栏形如 `https://dune.com/queries/7XXXXXX`，把编号
   填进 `docs/query-catalog.md` 的 `_TBD_` 列（可选，但很有用）。
9. **（仅 04）加参数** —— 见 §2.12。
10. 回到第 1 步做下一条。

> **省时技巧：** 10 条里除 04 外结构完全一致，熟练后每条 1 分钟。
> 但**不要**在同一个查询里堆多条 SQL —— Dune 一条查询只返回一个结果集。

### 2.1 查询 01 — CEX vs DEX Daily Volume & Ratio
* 粘贴 `queries/01_cex_dex_ratio.sql` → Run → Save 为 `01 · CEX vs DEX Daily Volume & Ratio`。
* **预期：** 约 90 行；列 `day, dex_volume_usd, dex_trades, cex_onchain_volume_usd, cex_net_flow_usd, cex_dex_ratio`。
* **检查：** `day` 最新一行应是昨天/今天；`dex_volume_usd` 应在 1e8–1e10 量级（USD）。
* 若 `cex_onchain_volume_usd` 为 `NULL` 但 `dex_volume_usd` 有值 → 正常（右侧表当天还没数据）。

### 2.2 查询 02 — Exchange Net Flow (ETH/USDT)
* Run → Save 为 `02 · Exchange Net Flow (ETH/USDT)`。
* **预期：** 约 10 交易所 × 90 天 ≈ 最多 900 行；列 `exchange_name, day, net_flow_usd, inflow_usd, outflow_usd`。
* **检查：** `exchange_name` 只应出现 binance/coinbase/okx/bybit/kraken/gate.io/htx/kucoin/bitfinex/robinhood。

### 2.3 查询 03 — DEX Aggregator Market Share
* Run → Save 为 `03 · DEX Aggregator Market Share`。
* **预期：** 约 12 个月 × ~8 个聚合器；列 `month, project, volume_usd, trades, unique_traders, market_share_pct, mom_growth_pct`。
* **检查：** 每个月内 `market_share_pct` 之和应约等于 100。

### 2.4 查询 04 — Token CEX-Listing Impact (±7d)  ⚠️ 需先加参数
* **先加参数，再运行**（顺序很重要，否则 `{{token_symbol}}` 会报语法错）：
  1. 保存为 `04 · Token CEX-Listing Impact (±7d)`。
  2. 在编辑器下方/右侧找到 **Parameters** 面板（有的版本在查询名下方「Parameters」按钮）。
  3. 点 **Add parameter**，添加第 1 个：
     * Name: `token_symbol` · Type: `Text` · Value: `PEPE`
  4. 再添加第 2 个：
     * Name: `listing_date` · Type: `Text` · Value: `2023-05-05`
  5. 保存（`⌘S`），然后 Run。
* **预期：** 最多 15 行（±7 天），列 `day_offset, day, dex_volume_usd, buy_volume_usd, sell_volume_usd, trades, trailing14d_avg_usd, forward14d_avg_usd`。
* **换代币：** 改 `token_symbol`（如 `WIF`、`JUP`、`ARB`）与对应上市日 `listing_date`，重新 Run 即可。
* 若某个代币在 `dex.trades` 里没有 symbol 记录，会返回 0 行 —— 换个更主流的代币试。

### 2.5 查询 05 — Unique Traders per Protocol
* Run → Save 为 `05 · Unique Traders per Protocol`。
* **预期：** 90 天 × ~10 协议；列 `day, project, unique_traders, trades, trades_per_trader, volume_usd, volume_per_trader_usd`。
* **检查：** 某项目某天缺失属正常（当天无交易）。

### 2.6 查询 06 — CEX Inflow/Outflow by Exchange
* Run → Save 为 `06 · CEX Inflow/Outflow by Exchange`。
* **预期：** 10 行左右（已 `HAVING total_volume > $1M` 过滤）；列 `exchange_name, inflow_usd, outflow_usd, net_flow_usd, total_volume_usd, unique_users`。

### 2.7 查询 07 — DEX Volume by Blockchain
* Run → Save 为 `07 · DEX Volume by Blockchain`。
* **预期：** ~26 周 × 各链；列 `week, blockchain, volume_usd, trades, unique_traders, chain_share_pct`。

### 2.8 查询 08 — Top Token Pairs (30d)
* Run → Save 为 `08 · Top Token Pairs (30d)`。
* **预期：** ≤50 行；列 `token_pair, volume_usd, trades, unique_traders, volume_share_pct, volume_rank`。

### 2.9 查询 09 — Stablecoin Share of DEX Volume
* Run → Save 为 `09 · Stablecoin Share of DEX Volume`。
* **预期：** 90 行；列 `day, total_volume_usd, stablecoin_volume_usd, stablecoin_share_pct, share_7d_ma`。

### 2.10 查询 10 — Trade Size Distribution
* Run → Save 为 `10 · Trade Size Distribution`。
* **预期：** ~26 周 × 6 档 = ~156 行；列 `week, size_bucket, trades, volume_usd, trade_count_share_pct, volume_share_pct`。

### 2.11 全部完成后自检
* 打开 <https://dune.com/workspace/t/bonnieting/home> 或用左上角搜索，
  应能看到 10 条以 `01 ·` … `10 ·` 开头的查询。
* 任意打开一条，结果区非空即算通过。

### 2.12 关于查询 04 的参数（细节）
* 参数是「文本」类型，SQL 里用 `CAST('{{token_symbol}}' AS VARCHAR)` 和
  `CAST('{{listing_date}}' AS DATE)` 转成所需类型 —— 所以**日期也填成 `YYYY-MM-DD` 文本**。
* 参数值会随查询一起保存；Dashboard 上的那个 widget 会用保存的默认值渲染。
* 想固定展示某个代币就把它设为默认值；想让观众自己切换，参数在 Dashboard 上会显示为可编辑控件。

---

## 3. 输出列速查表（配置图表时对照）

| # | 查询 | 输出列（顺序即结果网格顺序） |
| --- | --- | --- |
| 01 | cex_dex_ratio | `day`, `dex_volume_usd`, `dex_trades`, `cex_onchain_volume_usd`, `cex_net_flow_usd`, `cex_dex_ratio` |
| 02 | exchange_net_flow | `exchange_name`, `day`, `net_flow_usd`, `inflow_usd`, `outflow_usd` |
| 03 | aggregator_market_share | `month`, `project`, `volume_usd`, `trades`, `unique_traders`, `market_share_pct`, `mom_growth_pct` |
| 04 | token_listing_impact | `day_offset`, `day`, `dex_volume_usd`, `buy_volume_usd`, `sell_volume_usd`, `trades`, `trailing14d_avg_usd`, `forward14d_avg_usd` |
| 05 | unique_traders | `day`, `project`, `unique_traders`, `trades`, `trades_per_trader`, `volume_usd`, `volume_per_trader_usd` |
| 06 | cex_flow_by_exchange | `exchange_name`, `inflow_usd`, `outflow_usd`, `net_flow_usd`, `total_volume_usd`, `unique_users` |
| 07 | dex_volume_by_chain | `week`, `blockchain`, `volume_usd`, `trades`, `unique_traders`, `chain_share_pct` |
| 08 | top_token_pairs | `token_pair`, `volume_usd`, `trades`, `unique_traders`, `volume_share_pct`, `volume_rank` |
| 09 | stablecoin_share | `day`, `total_volume_usd`, `stablecoin_volume_usd`, `stablecoin_share_pct`, `share_7d_ma` |
| 10 | trade_size_distribution | `week`, `size_bucket`, `trades`, `volume_usd`, `trade_count_share_pct`, `volume_share_pct` |

---

## 4. 创建 Dashboard 容器

1. 点左上角 **Create** → **New Dashboard**。
2. 名称填：`exchange-market-share-tracker`。
   > ⚠️ **这里输入的名字会成为 URL slug，之后无法修改。** 显示标题以后能改，slug 不能。
3. 点 **Save and Open**。此时是一个空白 Dashboard。
4. 点右上角 **Edit** 进入编辑模式（此后所有 widget 操作都在这个模式下做）。
5. 先拖入两个 **Text widget** 作为标题区（见 §5.0），再做图表。

> 结束后别忘了点 **Save**。编辑模式下每加几个 widget 保存一次，避免丢失。

---

## 5. 逐个 Panel 配置 Visualization（核心章节）

### 5.0 如何「添加 widget」——两种入口

**入口 A（从查询页，最常用）：**
1. 打开某条查询 → Run 出结果。
2. 结果区上方点 **New visualization**（或 **Visualization** 标签）。
3. 顶部 **Chart type** 下拉选类型（Bar / Line / Area / Pie / Scatter / **Mixed** / **Table** / **Counter**）。
4. 按下表填 **X Column / Y Column / Group by**，调右侧 **Options**。
5. 右上角点 **Add to Dashboard** → 选 `exchange-market-share-tracker` → 确认。
   > widget 会追加到 Dashboard **最底部**；切回 Dashboard 编辑模式拖到想要的位置、拖右下角改大小。

**入口 B（从 Dashboard 里）：** `Edit` → `Add widget` → `Visualization` → 选查询 → 同样配置。

**三类控件的通用字段（Dune 版本略有措辞差异）：**

* **Chart（Bar/Line/Area/Mixed）：**
  * `X Column` — 横轴字段
  * `Y Column`（可 `+ Add Y Column` 加多条）— 纵轴字段
  * `Group by` / `Series` — 把某列拆成多条/堆叠
  * `Options` → `Stack series`（堆叠）、`Show legend`、`Show data labels`、
    `X-axis type`（*Category* / *Date/Datetime*）、`Y-axis scale`（*Linear* / *Log*）、
    `Format`（单位 / 小数位）、`Sort`、`Limit`
  * **Mixed Chart** 额外有：每条 Y 列可单独设 `Type`（Bar/Line/Area）和 `Axis`（Left/Right）。
* **Table：** `Columns` 勾选/改名、每列 `Format`（千分位/百分比/小数）、`Show row numbers`、`Sort`、`Limit`。
* **Counter：** `Column`（取值列）、`Label`、`Format`、`Compare to`（对比上一周期）。

> 下面每个 Panel 的 **Y 轴格式** 建议统一：
> USD 金额用 **千分位 + 0 位小数**（或 `$`/`B`/`M` 单位）；`*_pct` 用 **2 位小数 + `%` 后缀**。

### 5.0.1 两个 Text widget（面板 19–20）
1. Dashboard `Edit` → `Add widget` → `Text`。
2. 第一个填标题（Markdown）：
   ```markdown
   # Exchange Market Share Tracker
   _updated daily 06:00 UTC · source: Dune curated tables (dex.trades / cex.flows / dex_aggregator.trades)_
   ```
3. 第二个作章节分隔，重复添加若干个小 Text，正文分别填：
   `## A. CEX ↔ DEX structural flows`、`## B. Aggregator routing market`、`## C. Token & user dynamics`。
4. 每个 Text 都要 `Save`。

---

### Panels 1–9

#### Panel 1 — CEX vs DEX 混合图（来自查询 01）
* **Chart type:** `Mixed Chart`
* **X Column:** `day`
* **Y Columns:** 加三条 —— `dex_volume_usd`、`cex_onchain_volume_usd`、`cex_dex_ratio`
* 每条 Y 列的设置：
  | Y Column | Type | Axis |
  | --- | --- | --- |
  | `dex_volume_usd` | **Bar** | **Left** |
  | `cex_onchain_volume_usd` | **Bar** | **Left** |
  | `cex_dex_ratio` | **Line** | **Right** |
* **Options:** `Show legend` ✅ · `X-axis type` = **Date** · 左轴 `Format` = 千分位/0 位小数 · 右轴 `Format` = 2 位小数
* **Add to Dashboard** → 放到第一行，宽度占 8–12 列（主图）。

#### Panel 2 — CEX/DEX 比值计数器（来自查询 01）
* 回到查询 01，再点 **New visualization**。
* **Chart type:** `Counter`
* **Column:** `cex_dex_ratio`
* **Label:** `CEX/DEX ratio (latest)`
* **Format:** 3 位小数
* **Options:** 可选 `Compare to` = 上一期（会显示涨跌箭头）
* **Add to Dashboard** → 放到顶部 KPI 行，宽度 3–4 列。

#### Panel 3 — 交易所净流分组柱（来自查询 02）
* **Chart type:** `Bar Chart`
* **X Column:** `day`
* **Y Column:** `net_flow_usd`
* **Group by / Series:** `exchange_name`
* **Options:** `X-axis type` = **Date** · 建议 `Limit` 到较大的值（如 1000）避免截断 · `Format` USD 千分位
* **Add to Dashboard** → 与 Panel 1 同排或下一排，6 列宽。

> 净流有正有负 → 柱子会围绕 0 轴上下分布，这是预期效果（上=净流入，下=净流出）。

#### Panel 4 — 交易所净流表格（来自查询 02）
* **Chart type:** `Table`
* **Columns:** 全选；`Format` 里 `net_flow_usd/inflow_usd/outflow_usd` 设千分位
* **Sort:** `day` 降序
* **Add to Dashboard** → 4 列宽。

#### Panel 5 — 聚合器份额堆叠面积（来自查询 03）
* **Chart type:** `Area Chart`
* **X Column:** `month`
* **Y Column:** `volume_usd`
* **Group by:** `project`
* **Options:** `Stack series` ✅ · `Show legend` ✅ · `X-axis type` = **Date** · `Format` USD 千分位
* **Add to Dashboard** → 第二区（B 区）主图，8–12 列宽。

#### Panel 6 — 聚合器份额表格（来自查询 03）
* **Chart type:** `Table`
* **Columns:** `month, project, volume_usd, market_share_pct, mom_growth_pct`（隐藏 `trades/unique_traders` 可选）
* **Format:** `volume_usd` 千分位；`market_share_pct`、`mom_growth_pct` 用 2 位小数 + `%`
* **Sort:** `month` 降序
* **Add to Dashboard** → 6 列宽。

#### Panel 7 — 代币上市影响折线（来自查询 04）
* **Chart type:** `Line Chart`
* **X Column:** `day_offset`
* **Y Columns:** `dex_volume_usd`、`trailing14d_avg_usd`、`forward14d_avg_usd`（三条）
* **Options:** `X-axis type` = **Category**（`day_offset` 是 -7…+7 的整数，用分类轴更整齐）·
  `Show legend` ✅ · `Format` USD 千分位
* **Add to Dashboard** → 单独一行（宽度 12 列）。
> 提示：想竖一条「上市日」参考线，Dune 原生不支持；可在 Text widget 里用文字标注
> 「`day_offset = 0` 为上市日」。

#### Panel 8 — 各协议去重交易者（来自查询 05）
* **Chart type:** `Line Chart`
* **X Column:** `day`
* **Y Column:** `unique_traders`
* **Group by / Series:** `project`
* **Options:** `X-axis type` = **Date** · `Show legend` ✅ · `Format` 千分位（0 位小数）
* **Add to Dashboard** → C 区，6 列宽。

#### Panel 9 — 交易强度 trades/trader（来自查询 05）
* 查询 05 再 **New visualization**。
* **Chart type:** `Line Chart`
* **X Column:** `day`
* **Y Column:** `trades_per_trader`
* **Group by / Series:** `project`
* **Options:** 2 位小数
* **Add to Dashboard** → 与 Panel 8 并排。

### Panels 10–18

#### Panel 10 — 交易所净流横向柱（来自查询 06）
* **Chart type:** `Bar Chart`
* **X Column:** `exchange_name`（分类）
* **Y Column:** `net_flow_usd`
* **Options:** 打开 **Swap axes / Horizontal**（或把 `exchange_name` 设为 Category 轴自动横向）·
  `Sort` = 按 `net_flow_usd` 升序（让最长的柱在最上面）· `Format` USD 千分位
* **Add to Dashboard** → B 区，6 列宽。

#### Panel 11 — 交易所充提表格（来自查询 06）
* **Chart type:** `Table`
* **Columns:** 全选
* **Format:** 四个 USD 列千分位；`unique_users` 千分位
* **Sort:** `total_volume_usd` 降序
* **Add to Dashboard** → 6 列宽。

#### Panel 12 — 各链交易量堆叠面积（来自查询 07）
* **Chart type:** `Area Chart`
* **X Column:** `week`
* **Y Column:** `volume_usd`
* **Group by:** `blockchain`
* **Options:** `Stack series` ✅ · `Show legend` ✅ · `X-axis type` = **Date** · USD 千分位
* **Add to Dashboard** → B 区主图，8–12 列宽。
> 链很多会让图很乱：可在 `Options → Limit` 或对结果做 `Sort` 后只留 Top 8；
> 若要永久精简，可把查询 07 的结果过滤成 top N 链（自行加 `WHERE blockchain IN (...)`）。

#### Panel 13 — 各链份额折线（来自查询 07）
* 查询 07 再 **New visualization**。
* **Chart type:** `Line Chart` · **X** `week` · **Y** `chain_share_pct` · **Group by** `blockchain`
* **Options:** 2 位小数 + `%`；`Show legend` ✅
* **Add to Dashboard** → 与 Panel 12 并排。

#### Panel 14 — Top 交易对表格（来自查询 08）
* **Chart type:** `Table`
* **Columns:** 全选（共 6 列）
* **Format:** `volume_usd` 千分位；`volume_share_pct` 2 位小数 + `%`；`volume_rank` 整数
* **Sort:** `volume_usd` 降序 · `Limit` 50（查询已 `LIMIT 50`）
* **Add to Dashboard** → B 区，6 列宽。

#### Panel 15 — Top 交易对柱状（来自查询 08）
* 查询 08 再 **New visualization**。
* **Chart type:** `Bar Chart` · **X** `token_pair` · **Y** `volume_usd`
* **Options:** `Limit` 15（否则太挤）· USD 千分位
* **Add to Dashboard** → 与 Panel 14 并排。

#### Panel 16 — 稳定币占比折线（来自查询 09）
* **Chart type:** `Line Chart`
* **X Column:** `day`
* **Y Columns:** `stablecoin_share_pct`、`share_7d_ma`（两条）
* **Options:** `X-axis type` = **Date** · 2 位小数 + `%` · `Show legend` ✅
* **Add to Dashboard** → C 区，6 列宽。
> 想让 7 日均线更醒目：把 `stablecoin_share_pct` 设为细线、`share_7d_ma` 设为粗线（Options 里的线条/示样设置）。

#### Panel 17 — 交易规模「量占比」100% 堆叠柱（来自查询 10）
* **Chart type:** `Bar Chart`
* **X Column:** `week`
* **Y Column:** `volume_share_pct`
* **Group by / Series:** `size_bucket`
* **Options:** `Stack series` ✅ · 打开 **100% stacked / Normalize**（若有）· `Show legend` ✅ ·
  `X-axis type` = **Date** · 2 位小数 + `%`
* **Add to Dashboard** → C 区，6 列宽。
> `size_bucket` 前缀 `1_`…`6_` 保证图例按小→大排序。

#### Panel 18 — 交易规模「笔数占比」100% 堆叠柱（来自查询 10）
* 查询 10 再 **New visualization**。
* **Chart type:** `Bar Chart` · **X** `week` · **Y** `trade_count_share_pct` · **Group by** `size_bucket`
* **Options:** 同 Panel 17
* **Add to Dashboard** → 与 Panel 17 并排。
> 对比 Panel 17 与 18 就是本项目想表达的「大额交易 vs 散户笔数」背离。

---

## 6. 布局（建议）

```
[ Text 标题 ]
[ Panel 2 计数器 ][ Panel 2b …可加更多计数器 ]        ← KPI 行
[ Text: A. CEX ↔ DEX structural flows ]
[ Panel 1 混合图 (12列) ]
[ Panel 3 净流柱 (6) ][ Panel 4 净流表 (6) ]
[ Text: B. Aggregator routing market ]
[ Panel 5 聚合器面积 (8) ][ Panel 6 聚合器表 (4) ]
[ Panel 10 交易所横向柱 (6) ][ Panel 11 交易所表 (6) ]
[ Panel 12 各链面积 (8) ][ Panel 13 各链份额 (4) ]
[ Panel 14 交易对表 (6) ][ Panel 15 交易对柱 (6) ]
[ Text: C. Token & user dynamics ]
[ Panel 8 去重交易者 (6) ][ Panel 9 交易强度 (6) ]
[ Panel 16 稳定币占比 (6) ][ Panel 17 规模量占比 (6) ]
[ Panel 18 规模笔数占比 (6) ]
[ Panel 7 上市影响 (12) ]
[ Panel 19/20 文字块 ]
```
编辑模式里拖动 widget 排序、拖右下角改宽高；每个 Dashboard 行按 12 列网格对齐。
最后一定点 **Save**。

---

## 7. 时间范围过滤（Last 90 days）

Dune 有两层时间控制，**两层都要用**：

1. **查询层（SQL 里已内置）。** 每条查询都带了
   `block_month >= date_trunc('month', current_date - INTERVAL '90' DAY)`。
   `block_month` 是**分区列**，这既限定时间又保证性能（详见开发日志）。
   * 想改默认窗口：编辑 SQL 里的 `INTERVAL 'N' DAY` 数字 → 重新 Run → 重新 Save。
   * 改完若已加到 Dashboard，widget 会在下次 Run 时用新结果。
2. **Dashboard 层（可交互过滤器）。**
   1. Dashboard 顶部点 **Filter**（漏斗图标）→ **Add filter**。
   2. 类型选 **Time range**（或 `Date range`）。
   3. 预设选 **Last 90 days**（也可同时给出 `Last 30 days` / `Last 180 days` 选项）。
   4. 选择应用到哪些 widget（时间序列类的都勾上：Panel 1、3、8、9、13、16、17、18）。
   5. **Save**。

> 有了 Dashboard 过滤器，观众不用改 SQL 就能切换 30/90/180 天。
> 注意：过滤器**不会**突破 SQL 的 90 天上限，两者要一致（想支持 180 天就把 SQL 窗口也放大）。

---

## 8. 配置刷新计划

1. Dashboard 右上角点 **clock / schedule**（时钟）图标。
2. 选频率：**Daily**（免费版可用低档执行层）。
3. 选一个执行档位（越高级越快，消耗越多 credit；免费版选基础档即可）。
4. **Save**。

只想让部分图更新？在**查询页**分别给 01/05/07/09 设 Daily、给 03/08/10 设 Weekly，
04（带参数）留手动。

---

## 9. 发布 & 获取公开链接

1. 先 **Save** Dashboard。
2. 右上角点 **Share**（分享）。
3. 可见性设为 **Public**（免费版默认公开；可同时打开 **Embed** 以便 iframe 嵌入）。
4. 复制公开链接，形如：

   ```
   https://dune.com/bonnieting/exchange-market-share-tracker
   ```

   > **注意：** 若你之前给 Dashboard 起的名字不是 `exchange-market-share-tracker`，
   > slug 会不同，以实际复制到的为准。
5. 顺便点 **Run** 让所有 widget 出最新结果，再截图（下一步）。

> 官方文档：<https://docs.dune.com/web-app/share>

---

## 10. 截图：截哪些区域、怎么截

### 10.0 工具与快捷键（macOS）

| 目的 | 操作 |
| --- | --- |
| 截**某个矩形区域**（单个 Panel 用这个） | `⌘⇧4` → 拖动框选 → 松手，自动存到桌面 |
| 截**某个窗口** | `⌘⇧4` → 按 `空格` → 点窗口 |
| 截**整屏** | `⌘⇧3` |
| 截**整页长图**（整盘总览首选） | Chrome：`⌘⇧P` → 输入 `screenshot` → 选 **Capture full size screenshot** |
| 截完改存到项目目录 | 见下方 `mv` 命令 |

把截图统一存进项目：

```bash
mkdir -p ~/Desktop/dune-dashboard/docs/screenshots
mv ~/Desktop/*.png ~/Desktop/dune-dashboard/docs/screenshots/ 2>/dev/null
# 然后按下面的表格重命名
```

### 10.1 必截的图（对应 README 占位符）

| 文件名 | 截取区域 | 画面里必须能看到 | 建议宽度 |
| --- | --- | --- | --- |
| `00_dashboard_overview.png` | **整个 Dashboard 全页**（用「Capture full size screenshot」） | 顶部 Dashboard 标题、所有 Panel、顶部的 **Last 90 days** 过滤器 | 全宽 |
| `01_cex_dex_ratio.png` | Panel 1 与 Panel 2 的**卡片区域** | 图标题、图例、左右 Y 轴、X 轴日期；计数器数值 | ~1200px |
| `02_exchange_net_flow.png` | Panel 3（净流柱）单独卡片 | 图例里的交易所名、围绕 0 轴的柱 | ~1200px |
| `03_aggregator_market_share.png` | Panel 5（聚合器堆叠面积）单独卡片 | 图例项目名（1inch/0x/…）、X 轴月份 | ~1200px |
| `04_token_listing_impact.png` | Panel 7（上市影响折线）单独卡片 | X 轴 `-7…+7`、三条线（实际量 + 前/后均线）、参数值（PEPE / 2023-05-05） | ~1600px |
| `05_unique_traders.png` | Panel 8 + Panel 9 的卡片区域 | 图例里的协议名、Y 轴数值/比值 | ~1200px |
| `06_cex_flow_by_exchange.png` | Panel 10（交易所横向柱）单独卡片 | 交易所名、正负柱方向 | ~1200px |
| `07_dex_volume_by_chain.png` | Panel 12（各链堆叠面积）单独卡片 | 图例里的链名、周轴 | ~1200px |
| `08_top_token_pairs.png` | Panel 14（Top 交易对表）单独卡片 | 表头 6 列、前若干行 | ~1000px |
| `09_stablecoin_share.png` | Panel 16（稳定币占比折线）单独卡片 | 两条线（占比 + 7 日均线）、百分比 Y 轴 | ~1200px |
| `10_trade_size_distribution.png` | Panel 17 + Panel 18 的卡片区域 | 六档 `size_bucket` 图例、100% 堆叠 | ~1600px |

> **要点：** 每个单图截图都要带上 **widget 标题**。先把 widget 拉宽到目标比例，
> 再框选「标题栏 + 图表本体」，别把旁边的 widget 切进来。

### 10.2 选截图（增强可信度，非必需）

| 文件名 | 区域 | 作用 |
| --- | --- | --- |
| `share_dialog.png` | 点 Share 后的弹窗 | 证明 Dashboard 是 **Public** |
| `query_01_editor.png` | 查询编辑器（左 SQL / 下 Results） | 证明数据来自真实 DuneSQL |
| `url_public.png` | 浏览器地址栏含公开 URL | 证明可公开访问 |

### 10.3 命名与存放

* 全部放进 `docs/screenshots/`，文件名**严格**用上面的表格。
* 只保留 PNG（`.gitignore` 已忽略 `*.png` —— 截图按项目约定单独管理，不进 git；
  若要进 git，删掉 `.gitignore` 里的 `*.png` 行并压缩体积）。

### 10.4 把截图用到文档里（两种方式）

1. **本地路径（README 里已预填占位符）**，例如
   `![CEX vs DEX](docs/screenshots/01_cex_dex_ratio.png)`
   —— 仅在有人 clone 仓库且本地有图时可显示。
2. **公网 URL（推荐，Dune 不能托管文件）**：把图上传到某图床 / GitHub Issue 附件，
   拿到 URL 后写 `![CEX vs DEX](https://.../01.png)`。
   也可在 Dune 的 **Text widget** 里用同样语法 `![alt](https://.../x.png)` 嵌入。

---

## 11. 回填文档占位符

发布并截完图后，逐项替换：

1. `README.md` 与 `README_zh.md` 顶部：
   `**Live dashboard:** https://dune.com/bonnieting/<你的-slug>`
2. `README.md` / `README_zh.md` 的 **Screenshots** 表：把
   `docs/screenshots/xx.png` 换成真实文件或公网 URL。
3. `docs/query-catalog.md`：把每条查询的 `_TBD_` 换成真实 Query ID。
4. `docs/development-log.md` → **Changelog**：追加一行
   `| 2026-XX-XX | Published public dashboard: <URL> |`。
5. 提交：

   ```bash
   cd ~/Desktop/dune-dashboard
   git add -A && git commit -m "docs: publish dashboard URL and screenshots mapping"
   git push
   ```

---

## 12. 排错（Troubleshooting）

| 现象 | 原因 / 解决 |
| --- | --- |
| 编辑器提示 `Column '{{token_symbol}}' cannot be resolved` / 语法错 | 查询 04 忘了加参数。按 §2.4 先加两个 Text 参数再 Run。 |
| `Table 'dex.trades' does not exist` | 引擎不是 DuneSQL。右上角切回 **DuneSQL**。 |
| `Column 'block_date' cannot be resolved`（`cex.flows`） | `cex.flows` 用的是 `block_time`（+ `block_month` 分区）；SQL 已用 `date_trunc('day', block_time)` 处理，别把它改成 `block_date`。 |
| 查询超时 / 很慢 | 确认 `block_month >= ...` 过滤还在；**不要**把它换成只过滤 `block_time`。 |
| 聚合器交易量小得离谱 | 别用 `dex.trades`（会重复计多跳），要用 `dex_aggregator.trades`（查询 03 已是）。 |
| 图表是一条平的线 | Y 列可能被当成文本；本项目 `ROUND(...)` 输出都是数字，若自改过请检查类型。 |
| 添加的 widget 不见了 | 加完要切回 Dashboard 并 **Save**；未保存时刷新会丢。 |
| Dashboard 过滤器不起作用 | 过滤器要**逐个 widget 勾选**应用；且不能突破 SQL 的 90 天上限。 |
| 免费版报 credit 用尽 | 减少不必要的手动 Run；把 03/07/08/10 的窗口调小或降低刷新频率。 |
| 找不到 Add to Dashboard | 必须在**已 Run 出结果**的可视化页右侧；左侧结果未刷新时按钮可能灰。 |

---

## 13. 官方文档

* Build Dashboards —— **https://docs.dune.com/web-app/dashboards**
* Charts & Graphs —— https://docs.dune.com/web-app/visualizations/charts-graphs
* Tables —— https://docs.dune.com/web-app/visualizations/tables
* Counters —— https://docs.dune.com/web-app/visualizations/counters
* Parameters —— https://docs.dune.com/web-app/query-editor/parameters
* Share & Embed —— https://docs.dune.com/web-app/share
* Query Editor —— https://docs.dune.com/web-app/query-editor/index
* Data Catalog（表结构）—— https://docs.dune.com/data-catalog/curated/dex-trades/overview






