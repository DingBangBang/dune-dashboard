<!-- README_zh.md — 中文版。英文为主版本，见 README.md -->

# 📊 Dune Analytics 仪表盘 — 交易所市场份额追踪

> 一个 **10 条查询 / 20+ 个 Panel** 的 Dune 仪表盘，从交易量、资金流、用户活跃度和市场结构
> 四个维度刻画 **中心化交易所（CEX）**、**去中心化交易所（DEX）** 与 **DEX 聚合器** 的竞争格局。

[![Dune](https://img.shields.io/badge/Dune-Dashboard-8A2BE2)](https://dune.com/)
[![Python](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/)
[![SQL](https://img.shields.io/badge/SQL-DuneSQL%20(Trino)-orange)](https://docs.dune.com/query-engine/Functions-and-operators)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

**Dune 工作区：** `https://dune.com/workspace/t/bonnieting/home`
**线上仪表盘：** `https://dune.com/bonnieting/exchange-market-share-tracker` _（占位符，待发布后替换）_

---

## ⚠️ 平台状态（重要，请先读）

本项目**原本为 Dune Analytics 设计**，该设计**完整保留**（`queries/` +
`docs/dashboard_guide.md`），**并未放弃**。但运行环境发生了变化，README 如实记录：

1. **Dune——设计保留，免费版无法执行。** Dune 于 2025 年 9 月将查询的
   **创建与执行**改为**付费计划**才可用，因此本账号走免费 UI/API 路径已不可行。
2. **Flipside Crypto——不可行：平台已关停。** `flipsidecrypto.xyz`、
   `docs.flipsidecrypto.xyz`、`api.flipsidecrypto.xyz` **全部 301 跳转到一家无关公司**
   （`edisyl.com`），`api-v2.flipsidecrypto.xyz` 无法连通。已无 Flipside SQL/API 可用。
3. **提供的凭据其实是 Alchemy 的 key**，而非 Flipside（`alch_…` + Alchemy 以太坊主网 RPC）。
   该 Alchemy 端点**可用**（已验证 `eth_blockNumber`、`alchemy_getAssetTransfers`），
   但 Alchemy 是节点/索引服务，**没有 SQL 引擎**，也没有 curated 的
   `dex.trades` / `dex_aggregator.trades` / `cex.flows` 表。

**对本仓库的影响：**

* ✅ **完整的 SQL + 20+ Panel 清单已就绪，与平台无关。**
* ✅ **Alchemy RPC 端点可用**，可支撑部分分析（CEX 净流、地址级流水、代币价格）。
* ⚠️ 要复现**全部** Panel，需要一个**免费的链上 SQL API**（如 Chainbase Data Cloud、
  Space & Time），或**付费的 Dune** 计划。

📄 **完整证据、命令与方案：[`docs/platform-migration.md`](docs/platform-migration.md)。**

> 🔐 凭据文件（`flipside_cypto_API_ley.txt`、`etherum_endpoint_url.txt`）已被
> **git 忽略**，切勿提交。

---

## 📑 目录

0. [平台状态](#-平台状态重要请先读)
1. [项目背景（为什么做这个）](#-项目背景为什么做这个)
2. [截图占位符](#-截图占位符)
3. [仓库结构](#-仓库结构)
4. [数据源说明](#-数据源说明)
5. [核心指标定义与生产环境意义](#-核心指标定义与生产环境意义)
6. [查询 / Panel 清单](#-查询--panel-清单)
7. [如何复现](#-如何复现)
8. [Dune 官方资源](#-dune-官方资源)
9. [License](#-license)

---

## 🎯 项目背景（为什么做这个）

单看一个「DEX 总交易量」数字几乎没有信息量，**市场结构**才是信号。这个仪表盘把以下问题
浓缩到一屏之内：

| 问题 | 为什么重要 |
| --- | --- |
| 流动性是否正从 CEX 向 DEX 迁移？ | 长期 CEX→DEX 迁移叙事，直接影响代币经济与交易所战略。 |
| 用户是否在把币提到自托管钱包？ | CEX 净流入/流出是经典的宏观供给指标（吸筹 vs 抛压）。 |
| 哪个聚合器拿下最多路由交易量？ | 聚合器是新的「前端」，其份额决定谁掌握用户意图。 |
| 交易量增长来自「更多用户」还是「更大鲸鱼」？ | 区分真实采用与机器人/做市商刷量。 |
| 市场是 risk-on（长尾币种、大额交易）还是 risk-off（稳定币）？ | 交易台与资金团队判断市场状态的温度计。 |

传统聚合数据源（DefiLlama 等）给的是交易量，很少能**并排**给出
**CEX/DEX 比值、交易所净流、去重交易者质量与交易规模结构**，更无法以开源 SQL 复现。
这正是本项目要填补的空白。

> ⚠️ **诚实的数据说明：** CEX 的**撮合交易量发生在链下**，Dune **没有**该数据。
> 本项目使用链上可验证的 **CEX 结算流**（`cex.flows`，充提）作为代理指标。
> 详见 [`docs/development-log.md`](docs/development-log.md) 与 [`docs/metrics.md`](docs/metrics.md)。

---

## 📸 截图占位符

> 待仪表盘发布后替换。PNG 请保存到 [`docs/screenshots/`](docs/screenshots/)，
> 文件名需与下表一致。（`*.png` 已被 git 忽略——截图单独管理，见开发日志。）

| Panel 组 | 占位符 | 文件名 |
| --- | --- | --- |
| 整盘总览（主图） | `![Dashboard overview](docs/screenshots/00_dashboard_overview.png)` | `00_dashboard_overview.png` |
| CEX vs DEX 比值 | `![CEX vs DEX](docs/screenshots/01_cex_dex_ratio.png)` | `01_cex_dex_ratio.png` |
| 交易所净流入/流出 | `![Net flow](docs/screenshots/02_exchange_net_flow.png)` | `02_exchange_net_flow.png` |
| 聚合器市场份额 | `![Aggregator share](docs/screenshots/03_aggregator_market_share.png)` | `03_aggregator_market_share.png` |
| 代币上市影响 | `![Listing impact](docs/screenshots/04_token_listing_impact.png)` | `04_token_listing_impact.png` |
| 去重交易者 | `![Unique traders](docs/screenshots/05_unique_traders.png)` | `05_unique_traders.png` |

---

## 🗂 仓库结构

```
dune-dashboard/
├── queries/                        # DuneSQL 脚本（一个文件 = 一条 Dune 查询）
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
│   └── dune_query_ids.json         # 自动生成：本地文件 -> Dune 查询 id/url
├── docs/
│   ├── dashboard_guide.md          # 仪表盘搭建分步指南
│   ├── development-log.md          # 设计思路、取舍、性能优化
│   ├── metrics.md                  # 指标定义 + 生产意义
│   ├── query-catalog.md            # 查询 -> Panel -> 可视化 映射
│   └── screenshots/                # 截图目录（.gitkeep 被跟踪）
├── scripts/
│   ├── create_queries.py           # 通过 API 在 Dune 上批量创建查询
│   └── check_environment.py        # 环境 / 仓库自检
├── environment.yml                 # conda 环境（python 3.11 + 依赖）
├── requirements.txt
├── .env.example                    # DUNE_API_KEY 模板
├── LICENSE
├── README.md                       # 英文主版本
└── README_zh.md                    # 中文版（本文件）
```

---

## 🗄 数据源说明

以下均为 **Dune 官方 curated** 数据集，跨链（除非特别说明）。

| 表 | 用于 | 说明 |
| --- | --- | --- |
| `dex.trades` | 01、04、05、07、08、09、10 | 细粒度 DEX 兑换事件（每个池子跳转 1 行），含 `amount_usd`、`tx_from`、`token_pair`、`blockchain`。 |
| `dex_aggregator.trades` | 03 | **用户意图级**聚合交易——一条多跳路由 = 1 行。计算聚合器份额的正确来源。 |
| `cex.flows` | 01、02、06 | CEX 充提事件，含 `cex_name` 实体归属、`flow_type`、`amount_usd`。 |
| `cex.addresses` | 参考 | CEX 地址目录，是 `cex.flows` 的底层数据。 |
| `tokens.transfers` | 02 备选 | 原始 ERC-20/原生转账（Coinpaprika 定价），需要按代币重建余额时的替代方案。 |

> Schema 已对照官方数据目录核验：
> [`dex.trades`](https://docs.dune.com/data-catalog/curated/dex-trades/evm/dex-trades) ·
> [`dex_aggregator.trades`](https://docs.dune.com/data-catalog/curated/dex-trades/evm/dex-aggregator-trades) ·
> [`cex.flows`](https://docs.dune.com/data-catalog/curated/cex-flows/flows)。

---

## 📐 核心指标定义与生产环境意义

| 指标 | 定义 | 生产环境意义 |
| --- | --- | --- |
| **CEX/DEX 比值** | 当日 CEX 链上结算量 ÷ DEX 交易量。 | 看**趋势**而非绝对水平。下降=资金上链；长周期结构性判断依据。 |
| **CEX 净流入** | 每所每日 `Σ 充值 − Σ 提现`（USD）。 | 为正=币流入（潜在抛压）；为负=自托管吸筹。需结合价格解读。 |
| **聚合器市场份额** | 项目路由量 ÷ 当月聚合器总量。 | 谁掌握前端/用户意图。份额上升但总量不涨=对手衰退，而非自身增长。 |
| **去重交易者** | 每个协议每日 `COUNT(DISTINCT tx_from)`。 | 真实用户盘。与交易量对照可区分「采用」与「鲸鱼/机器人刷量」。 |
| **人均交易数** | `交易数 ÷ 去重交易者`。 | 比值飙升即机器人/MEV，而非散户增长，是重要的数据质量护栏。 |
| **上市影响（±7d）** | CEX 上市前后各 7 天的代币 DEX 交易量。 | 量化「上市拉盘」。上市**前**放量=知情/抢跑资金。 |
| **稳定币份额** | 稳定币腿交易量 ÷ DEX 总量。 | 高=避险/去杠杆（risk-off）；低=投机（risk-on）。 |
| **交易规模结构** | 按 USD 分档的交易量/笔数占比。 | `≥$1M` 份额上升=机构参与；`<$100` 笔数占比上升=散户。 |

完整公式、边界情况与注意事项见 [`docs/metrics.md`](docs/metrics.md)。

---

## 🧩 查询 / Panel 清单

10 条查询可展开为 **20+ 个 Panel**，完整映射（查询 → 图表类型 → 字段 → 过滤）
见 [`docs/query-catalog.md`](docs/query-catalog.md)。

| # | 查询 | 首选可视化 |
| --- | --- | --- |
| 01 | CEX vs DEX 日交易量与比值 | 柱状 + 折线混合 |
| 02 | 交易所净流（ETH/USDT） | 分组柱状 |
| 03 | 聚合器市场份额（月度） | 堆叠面积 + 表格 |
| 04 | 代币上市影响（±7d） | 折线（带参数） |
| 05 | 各协议去重交易者 | 多序列折线 |
| 06 | 各交易所充提 | 横向柱状 |
| 07 | 各链 DEX 交易量 | 堆叠面积 |
| 08 | Top 交易对（30d） | 表格 + 柱状 |
| 09 | 稳定币在 DEX 中的占比 | 折线（+7 日均线） |
| 10 | 交易规模分布 | 100% 堆叠柱状 |

---

## 🚀 如何复现

### 1. 克隆并进入

```bash
git clone https://github.com/DingBangBang/dune-dashboard.git
cd dune-dashboard
```

### 2. 创建 conda 环境

```bash
conda env create -f environment.yml
conda activate dune-dashboard
conda run -n dune-dashboard python scripts/check_environment.py
```

### 3. 在 Dune 上创建查询

**方式 A（手动，免费版可用，推荐）。**
打开 <https://dune.com/queries> → **New query**，把 `queries/` 下每个文件粘贴进去
（小技巧：`pbcopy < queries/01_cex_dex_ratio.sql` 后 `⌘V`），**Run**，再按
[`docs/dashboard_guide.md`](docs/dashboard_guide.md) §1.1 的名字 **Save**。仅查询 04 需先加两个
*Text* 参数：`token_symbol` = `PEPE`、`listing_date` = `2023-05-05`。
👉 完整逐步指南：**[`docs/dashboard_guide.md`](docs/dashboard_guide.md)**。

**方式 B（自动，需要 Dune Analyst 套餐）。**
免费版无法使用 Dune Query API。升级套餐后，填入 Key 再运行脚本：

```bash
cp .env.example .env      # 粘贴 DUNE_API_KEY（Dune → Settings → API）
conda run -n dune-dashboard python scripts/create_queries.py --dry-run   # 预览
conda run -n dune-dashboard python scripts/create_queries.py             # 创建
```

脚本会生成 `queries/dune_query_ids.json`（本地文件 → 查询 ID/URL 映射）。


### 4. 搭建仪表盘（浏览器 UI）

Dune API 无法创建仪表盘 widget，因此这一步在浏览器完成——逐步点击说明见
**[`docs/dashboard_guide.md`](docs/dashboard_guide.md)**：

1. Create → **New Dashboard**，命名为 `exchange-market-share-tracker`。
2. 对每条查询：Run → 选择 Visualization → **Add to Dashboard**。
3. 在仪表盘层设置时间过滤为 *Last 90 days*。
4. **Save** → **Share → Public** → 复制公开链接。

### 5. 截图与文档

把 PNG 存入 `docs/screenshots/`（文件名见[截图占位符](#-截图占位符)），
替换本文件顶部的占位链接，并在开发日志记录变更。

---

## 🔁 从零复现清单

- [ ] `git clone` + `conda env create -f environment.yml`
- [ ] 申请 Dune API Key（Analyst 套餐）→ `.env`
- [ ] `python scripts/create_queries.py`（或手动粘贴 10 个 SQL 文件）
- [ ] 搭建仪表盘（[指南](docs/dashboard_guide.md)）
- [ ] 应用 *Last 90 days* 过滤 + 配置每日自动刷新
- [ ] 发布 → 替换 URL 占位符 + 补充截图

---

## 📚 Dune 官方资源

> 想深入了解仪表盘搭建，请跳转 **Dune 官方文档（Dashboards）：
> 👉 https://docs.dune.com/web-app/dashboards**

- 查询编辑器：<https://docs.dune.com/web-app/query-editor/index>
- 参数（Parameters）：<https://docs.dune.com/web-app/query-editor/parameters>
- 图表与可视化：<https://docs.dune.com/web-app/visualizations/charts-graphs>
- 数据目录：<https://docs.dune.com/data-catalog/curated/dex-trades/overview>
- Data API：<https://docs.dune.com/api-reference/api-overview>
- Trino SQL 函数：<https://docs.dune.com/query-engine/Functions-and-operators>

---

## 📄 License

[MIT](LICENSE) © 2026 bonnieting / DingBangBang


