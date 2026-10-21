# H-quant-026 / quant-026 加固报告（2026-10-21）

对象：`bots/quant/entries/quant-026-drought-d4-weekly-continuity.md`
未改 `status: 待核`、未改 `date: 2026-10-20`、未改文件名/id。

## 1. 复用了什么

- 旧口径数据与回放已由 `bots/quant/notes/scheduler/checks/B23.md` 从零重跑：
  16 个 closed event/368 个市场、2,344 笔成交、320/320 结算一致、67,056 个州-周转移、
  23 笔/1,020.57 份/$766.93/$245.64/+32.03%。
- 本轮没有重复这份复算；重新抓同一批数据用于“可成交价”一层，旧口径逐笔复现一致。

## 2. 来源复核（`verify_sources.py` / `verify_sources.out`）

- 10 个远程 URL：全部 HTTP 200。
- 州名单/州数两段规则引文与 live `description` **逐字相等**（2,082 / 2,032 字符）。
- `feeSchedule` 均是 `rate=0.05, takerOnly=true, rebateRate=0.25`；州名单 40/40、州数 6/6 `restricted=true`。
- `resolutionSource=https://droughtmonitor.unl.edu/DmData/DataTables.aspx`（market 字段；event 字段为 None）。
- 37 个 drought tag 事件 = 16 周度 + 2 deadline + 19 ag/其他（与条目一致）。
- 更正：USDM REST **不带** `Accept: text/csv` 也返回 200/922 B（旧条写“0 字节”）。
- 更正：`restricted=true` 是全部市场，不是“部分市场”。

## 3. 可成交价回测（`harden_backtest.py` / `harden_backtest.out`）

| 口径 | 笔数 | 活跃周 | 成本 USD | 净 USD | 每份 ROI |
|---|---:|---:|---:|---:|---:|
| 旧报价（决策前最后 ask，中位 37.1h） | 23 | 5 | 766.93 | +245.64 | +24.22% |
| 决策后第一笔真实成交，发布前 | **2** | **1** | **14.24** | **+1.76** | **+14.21%** |
| 限价单（原 ask+1¢，发布前成交） | **1** | **1** | **4.19** | **+0.81** | **+19.47%** |

- 23 个信号中 19 个的下一笔成交在周四发布后（0.92–0.996），2 个 72h 内无后续成交。
- 报价年龄收紧：72h→23 笔；24h→7 笔；6h→4 笔；1h→0 笔。edge 主要在旧报价。
- 时间外：前 4 周选 margin（最优 0¢），后 4 周 14 笔 +8.43%（旧报价）；可成交口径后 4 周只有 10/06 的 2 笔 +1.76 USD。
- CLOB `prices-history` 对已关闭市场只留约 3–7 天（本样本，160/320），且是中间价不是 ask：
  `state-d4-drought-2026-10-13-ar` 截止 p=0.915、data-api 0 笔、结算 [1,0]、series 最后 0.525。
  用中间价做“上界”会得到 72 个触发 +30.33%，是不可成交的假机会，未采用。

## 4. 七门判定（本轮）

1. 机制：**不确定**（延续率真实，但可成交口径下找不到付钱方）
2. 免费数据：满足（仅前向记录替代口径）
3. 小资金：**不满足**（可成交容量 8 周 14.24 USD）
4. 不重复：满足
5. 扣成本：**不满足**（可成交净 +1.76 USD / 8 周）
6. 两周 30 个独立结果：**不满足**（8 个 weekly release）
7. 出处：满足（10 URL 全 200；规则逐字；两处旧表述已更正）

## 5. 建议

建议核对方**退回**（原 +32% 是旧报价上限，可成交证据只有 2 笔 +1.76 USD）。
若主审认为 USDM 状态延续仍值得观察，最多降为**待选区**，从 2026-10-22 起做前向记录；
不能按“收录”处理，也不能用 0.50–0.55 的旧报价当成交价。

## 6. 文件

- `fetch_data.py` / `fetch_data.out`
- `verify_sources.py` / `verify_sources.out`
- `harden_backtest.py` / `harden_backtest.out`
- `_cache/`（gitignored，全部 <1 MB；events_closed 已 gzip）
