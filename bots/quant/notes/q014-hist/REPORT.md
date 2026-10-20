# quant-014 历史可成交价回测（SPX 收盘市场）

访问日期：2026-10-20。脚本：`q014_hist.py`；原始输出：`run_output.txt`；明细：`events.csv`；lint：`lint_output.txt`。

## 结论

**FAIL**（按 entry 冻结的失败标准）。日频 fade 侧扣费后每份净损益均值为 **+0.00650**（中位数 **−0.14482**，ISO 周 bootstrap 95% CI **[-0.04872, +0.06235]**），没有稳定正 EV；更关键的是 entry 自己的第 3 条：模型 Brier **0.25000** 劣于常数 0.53 的 **0.24923**（252 个日频 event），命中该条。全部触发腿（含阶梯）均值 **−0.01018**、中位数 **−0.13452**、每 $1 投入 **−0.0406**。

## 数据源与取数

- SPX 日线：**FRED `SP500` CSV**，`https://fred.stlouisfed.org/graph/fredgraph.csv?id=SP500`，访问 2026-10-20，2,512 个交易日，2016-10-20..2026-10-19。stooq `^spx` 本次仍返回 JS challenge 页（未取到），故未用 stooq。
- Polymarket 规则/结算：Gamma `events?series_id=10383`（日频 Up/Down）、`10603`（weekly above）、`10856`（monthly close），以及 `public-search` 关键词 `SPX, S&P 500, spx close, spx above, S&P 500 above`，访问 2026-10-20。
- 可成交价：`https://data-api.polymarket.com/trades?market=<conditionId>&limit=500&offset=N`，访问 2026-10-20；`No`/`Down` 成交按 `1 - price` 映射成 YES 价。
- 交叉核对：随机抽 5 个已结算 market，用 FRED 收盘价重算 YES/No，结果 **5/5 与 `outcomePrices` 一致**（见 `run_output.txt` 的 cross-check 段）。
- 费用：Gamma `feeSchedule.rate = 0.04`（takerOnly），按 GUIDE 第 8 节 `0.04 × p × (1−p)`/份；未计 maker 返佣。

## 方法（脚本头已冻结）

- Universe：所有能枚举到的已关闭 SPX 收盘事件——日频 `spx-up-or-down-on-<date>` **252** 个（2025-10-15..2026-10-19）；weekly above `spx-above-on-<date>` **2** 个；monthly above **3** 个；monthly close bracket **2** 个。共 **259 events / 303 legs**。排除 `spx-opens-up-or-down`（同一交易日重复计）、`spx-hit-*`（曾经触及，不同模型）、SPY 与未关闭事件。
- 决策时点：主结果 = 结算收盘前 **6 小时**（entry 的 p6）；敏感性 = **前一个美股收盘**。模型 spot 用决策时点前最后一个官方收盘；市场价 = 决策前 6 小时内最后一笔 data-api 成交。
- 模型：零漂移对数正态，σ = 决策前 **20** 个交易日对数收益的年化标准差（√252），`T = 剩余交易日/252`，`P(S_T>K)=Φ((ln(S/K)−σ²T/2)/(σ√T))`；日频 Up/Down 按 entry 原文取 **P(up)=0.5000**。
- 规则：`threshold = 2 × (fee + half_spread)`，`half_spread=1¢`；`p_model − ask ≥ threshold` 买 YES，`bid − p_model ≥ threshold` 买 NO；`ask = trade+1¢`、`bid = trade−1¢`；持有到 `outcomePrices`。事件损益 = 该 event 触发腿等权平均。
- 独立结果：一个交易日一个 event；bootstrap 以 **ISO 周** 为 cluster，10,000 次，固定 seed 20261020。

## 结果（均抄自 `run_output.txt`）

样本漏斗：259 events → 259 有报价 → 231 至少一条触发（251/303 legs 触发），8 legs 在 6h 窗口内无成交。

分类型触发腿：

| 类型 | events | priced | 触发 events | 触发 legs | 均值/份 | 中位数/份 | 每 $1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| daily_updown | 252 | 252 | 224 | 224 | −0.00090 | −0.15510 | −0.0038 |
| weekly_above | 2 | 2 | 2 | 9 | −0.01363 | −0.01144 | −1.0394 |
| monthly_above | 3 | 3 | 3 | 11 | −0.11584 | −0.02078 | −0.2433 |
| monthly_close | 2 | 2 | 2 | 7 | −0.13662 | −0.07260 | −0.2442 |

日频 `|p6−0.5| ≥ 0.10` 子集（entry 的吃单子集）：

- **FADE**（本任务规则：模型 0.5 反向做）：194 legs，毛 **+0.02267**，净 **+0.00650**，中位数 **−0.14482**，命中率 **0.222**，total net **+1.26**，每 $1 **+0.0311**。
- **FOLLOW**（entry 原文“按 p6 那一侧吃单”的方向）：194 legs，毛 **−0.02267**，净 **−0.03835**，中位数 **+0.11578**，命中率 **0.773**。
- 事件级 FADE：194 events，均值 **+0.00650**，中位数 **−0.14482**，54 个 ISO 周，bootstrap 95% CI **[-0.04872, +0.06235]**。

敏感性（前一个美股收盘决策）：233 legs 有报价、100 触发；全部触发腿均值 **+0.06135**、中位数 **−0.02132**；日频事件级均值 **−0.00593**，95% CI **[-0.08416, +0.07569]**。

校准：日频 252 events，模型 Brier **0.25000**、常数 0.50 **0.25000**、常数 0.53 **0.24923**、市场 p6 **0.17783**；log loss 模型 **0.69315**、常数 0.53 **0.69161**、市场 **0.52842**。全部 295 priced legs 的 Brier：模型 **0.27416**，市场 **0.16054**。

## 对 gate 5/6 的含义

- **gate 5（扣成本粗算）**：日频 fade 侧均值微正但中位数 −0.14482、bootstrap CI 跨 0，不能当作“扣成本后够用”；entry 原文的 −0.0288 更接近 **FOLLOW** 方向，本次 252-event 复现为毛 −0.02267、净 −0.03835。entry 用这个负数否掉日频，但符号上它支持的是“反向（fade）毛为正”，只是净值和显著性都很弱。阶梯腿在“结算前一日”决策下全部为负（weekly −0.01363、monthly above −0.11584、monthly close −0.13662），但这不等于否掉 entry 的远端阶梯论点（见局限）。
- **gate 6（两周可检验）**：日频历史有 252 events / 54 个 ISO 周，数量上够；但 54 周仍只是约一年、一个波动率 regime，周内交易日高度相关，block bootstrap CI 很宽。entry 说的“严格独立结果远少于 30”在历史样本里仍成立。

## 局限

- 阶梯类只有 7 个 event；且历史回测把决策固定为“结算前一日/前 6h”，`T≈1/252`，**没有复现 entry 在到期前约 72 天看到的远端阶梯错价**。远端阶梯需要事件上市初期的 CLOB 历史，本次 data-api 成交可取但未按“上市初期”决策，故阶梯结论不能外推到 entry 的原始主张。
- data-api 只给成交价，不给盘口深度；`ask = trade + 1¢` 是任务规定的近似，100 份能否成交、逆向选择均未量化。
- 结算源：日频用 WSJ、monthly close 用 Yahoo；本次只用 FRED 做模型输入，5/5 交叉核对通过，但档界附近仍可能有几分钱差异。
- 样本仅 2025-10..2026-10 一个上涨为主的市场环境（日频上涨率约 52.8%，由 Brier 常数 0.53 反推），不能外推。
- 未取 VIX/隐含波动率；未计 maker rebate、资金占用和结算滞后。
- 运行环境里 `python3 tools/check.py lint` 在 `bots/muse/entries/muse-700*.md` / `muse-701*.md` 因缺字段崩溃（`KeyError: 'id'`），与本条无关，原始输出见 `lint_output.txt`。

## 复现

```bash
cd bots/quant/notes/q014-hist
python3 q014_hist.py            # 首次会下载到 _cache/，之后完全走缓存
python3 ../../../tools/check.py lint   # 已知在 muse 文件上崩溃
```

两次从缓存重跑 `run_output.txt` 已 `diff` 一致。
