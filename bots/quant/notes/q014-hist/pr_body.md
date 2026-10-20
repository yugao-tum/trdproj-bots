## 做了什么

在 `bots/quant/notes/q014-hist/` 新增可复现历史回测：用 **data-api 真实成交**（不是 CLOB prices-history）给已关闭的 SPX 收盘市场定价。Universe 包括日频 `spx-up-or-down-on-<date>` 252 个、weekly above 2 个、monthly above 3 个、monthly close bracket 2 个，共 259 events / 303 legs（2025-10-15..2026-10-19）。SPX 日线用 **FRED SP500 CSV**（stooq 被 JS challenge 挡住）；随机 5 个结算日用 FRED 收盘重算，**5/5** 与 `outcomePrices` 一致。

脚本头先冻结：决策时点（主 = 收盘前 6h，敏感 = 前一美股收盘）、20 日已实现波动率零漂移对数正态、`ask=trade+1¢ / bid=trade−1¢`、`fee=0.04×p×(1−p)`、entry 的 `2×(fee+half_spread)` 阈值和失败标准。ISO 周 block bootstrap 10,000 次，seed 20261020。

## 验证命令

```bash
cd bots/quant/notes/q014-hist
python3 q014_hist.py
diff <(python3 q014_hist.py) run_output.txt   # 从缓存重跑应完全一致
```

## 关键结果（抄自 run_output.txt）

- 漏斗：259 events → 259 有报价 → 231 触发；251/303 legs 触发；8 legs 无 6h 成交。
- 全部触发腿：均值 **−0.01018**/份，中位数 **−0.13452**，命中率 0.247，每 $1 **−0.0406**。
- 日频 `|p6−0.5|≥0.10` 子集（entry 口径）：
  - FADE（本任务规则）：194 legs，毛 **+0.02267**，净 **+0.00650**，中位数 **−0.14482**，命中率 0.222；事件级 95% CI **[-0.04872, +0.06235]**。
  - FOLLOW（entry“按 p6 那一侧吃单”）：毛 **−0.02267**，净 **−0.03835**。
- 校准：模型 Brier **0.25000** vs 常数 0.53 **0.24923**（252 events）；市场 p6 Brier **0.17783**。
- **VERDICT: FAIL** —— entry 第 3 条“模型 Brier 劣于常数 0.53”命中；第 1 条在 FADE 下为 +0.0065 但中位数与 CI 都不支持正 EV，在 FOLLOW 下为 −0.0384。

## 局限

- 阶梯类只有 7 个 event，且历史决策固定为结算前一日/前 6h（T≈1/252），没有复现 entry 到期前约 72 天的远端阶梯错价。
- data-api 只有成交价、没有盘口深度；`±1¢` 是任务规定近似，容量与逆向选择未量化。
- 仅约一年、一个波动率 regime；未取 VIX/隐含波动率；未计 maker 返佣与结算滞后。
- `tools/check.py lint` 在 muse 文件上崩溃（与本条无关），原始输出在 `lint_output.txt`。
