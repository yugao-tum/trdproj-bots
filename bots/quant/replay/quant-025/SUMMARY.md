# 回放汇总：quant-025

**条目**：`bots/quant/entries/quant-025-spc-tornado-outlook-lag.md`
**运行日期**：2026-10-21（UTC）
**结论**：`evidence: 回放`，`result: 不显著`。严格口径 6 笔 / 3 个独立日事件、宽口径 10 笔 / 7 个，均少于 30；样本内净收益为正，但只能当点估计。

## 如何复现

- 脚本：`run_replay.py`（从零抓取并顺序运行下面 6 步）；依赖 `python3` + `requests`（本次实测 Python 3.13.5 / requests 2.34.2）。
  ```bash
  cd bots/quant/replay/quant-025
  python3 run_replay.py
  ```
- 分步：`fetch_outlooks.py` → `filter_62.py` → `fetch_headers.py` → `classify.py` → `fetch_trades.py` → `reproduce.py`。
- 参数（完整、非只报最佳）：
  - 结算：次日 0100Z 归档 `torn.nolyr.geojson` 中 `LABEL ≥ 0.02` 的多边形；排除 `cigtorn`/SIGN 斜线；城市坐标取市场规则里的坐标。
  - 信号窗口：`[LM(1630Z)+2min, LM(2000Z)+2min)` 与 `[LM(2000Z)+2min, LM(final)+2min)`；`LM` 为归档 GeoJSON 的 HTTP `Last-Modified`，缺失时分别退回 `[16:45,19:55)` / `[20:20,次日01:15)`。
  - 入场：窗口内第一笔 `BUY Yes`（之前的 `SELL Yes`/`BUY No` 不计），成交 YES 价 `≤ 0.25`；无 `BUY Yes` 或价格 `>0.25` 跳过。
  - 仓位：`min(该笔成交 size, $50/价格)`；单市场 ≤$50、单日 ≤$250、场所 ≤$2,500；持有到结算，不设止损。
  - 成本：吃单费 `0.05×p×(1−p)` + 缓冲 `1¢/份`；另做 3¢、5¢ 敏感性。
  - 价格来源：Polymarket data-api 逐笔成交（`side`/`outcome`/`size`/`timestamp`），不是 CLOB `prices-history`，也不是盘口。
- 数据下载地址（公开、免密钥，2026-10-21 访问）：
  - `https://gamma-api.polymarket.com/series?slug=tornado-risk-daily`
  - `https://gamma-api.polymarket.com/events?series_id=12689&closed=true&limit=100&offset=0`
  - `https://data-api.polymarket.com/trades?market=<conditionId>&limit=1000`
  - `https://www.spc.noaa.gov/products/outlook/archive/2026/day1otlk_YYYYMMDD_HHMM.html`
  - `https://www.spc.noaa.gov/products/outlook/archive/2026/day1otlk_YYYYMMDD_HHMM_torn.nolyr.geojson`
- 数据本身起点：Polymarket series 最早已关闭事件为 2026-08-19；SPC 归档同日可取。
- 开发窗口：`2026-08-19..2026-10-19`（62 个日事件固定，2026-10-20 新增事件不计入，避免改变已核对样本）。
- 切分依据：Polymarket 无 GUIDE §9 加密窗口限制；本回放是事后全样本规则检验，没有留出 2025+ 之类的盲段，故 `result` 按独立结果数 3/7 记为不显著。

## 成交和成本

- 成交价和时点：data-api 每笔已执行成交；信号时点严格晚于该归档文件的 `Last-Modified + 2min`，无前视。`reproduce.out` 逐笔列出时间戳、方向、价格、份数、结算。
- 全部成本：手续费 `0.05×p×(1−p)`（p=0.011 时约 0.05¢/份，p=0.20 时约 0.80¢/份）+ 1¢/份缓冲；没有资金费/借币费。未计 UMA 结算锁仓的机会成本。
- 资金和容量：严格 6 笔共 712.1 份、投入 $16.03；单笔最大成本 $6.00，单日最大 $9.61（2026-09-30）。宽口径 10 笔投入 $16.93。按 10 倍放大也只有约 $2.6–2.7/日、最大单日约 $96，**无法部署 5,000 USDT**；这是经济容量硬伤。

## 汇总结果

- 独立结果数及计法：按日事件计（同一事件 25 个城市市场算 1 个；同一事件的同向多笔仍算 1 个）。严格口径 **3** 个独立日事件（6 笔），宽口径 **7** 个（10 笔），均 <30。
- 扣成本后净收益：严格 **+$658.23**（成本 $16.03，5 胜 1 负）；宽口径 **+$674.71**（成本 $16.93，5 胜 5 负）；缓冲 3¢ → +$643.99、5¢ → +$629.75。`reproduce.py` 生成 `replay_results.json`。
- 最大回撤：`-`（Polymarket，按 `templates/ENTRY.md` 可选；未构造逐日账户权益，不是“没测”）。
- 对 5,000 USDT 的年化贡献：严格 `658.23 ÷ 5,000 × 365/62 = 77.5%`；宽口径 `674.71 ÷ 5,000 × 365/62 = 79.4%`。这是 3 个独立日、容量约 $16/62 天的样本内算术，不能当预期。
- result：**不显著**（独立结果 <30；正收益集中在 2026-09-30 一天，严格口径该日占 94.7%）。
- 不可靠或失败原因：样本只有 2 个月、3–7 个独立信号；价格是成交代理，无法证明同价同量可成交；深度薄；SPC 多边形与平台结算样本内 0/1,550 不一致，但只覆盖 2 个月。

## 所有变体（所有市场都要写，看了不用的也算）

- variants（自己的）：**4**
- variants_ext（外部来源）：**-**（没有引用外部策略变体；Gamma/SPC 只是本条数据源）

| 序号 | 自己 / 外部来源 | 规则与全部参数 | 窗口 | 结果和位置 |
|---|---|---|---|---|
| 1 | 自己 | 严格：窗口内第一笔 `BUY Yes` ≤0.25；0.05 费 + 1¢ 缓冲 | 2026-08-19..2026-10-19 | 6 笔/3 事件，成本 $16.03，净 +$658.23；`replay_results.json:strict` |
| 2 | 自己 | 严格同上；缓冲 3¢ | 同上 | 6 笔/3 事件，净 +$643.99；`reproduce.out` |
| 3 | 自己 | 严格同上；缓冲 5¢ | 同上 | 6 笔/3 事件，净 +$629.75；`reproduce.out` |
| 4 | 自己 | 宽口径：窗口内任一笔成交的 YES 价 ≤0.25（不要求 `BUY Yes`）；0.05 费 + 1¢ 缓冲 | 同上 | 10 笔/7 事件，成本 $16.93，净 +$674.71；`replay_results.json:broad` |

未测试（不写入 variants）：NO 侧、最终 0100Z 后入场、maker 挂单、按盘口深度成交。它们不是本回放跑过的变体。
