## 做了什么

- 新增 `q009_hist.py`：用 Gamma public-search（22 条查询）枚举全部可找到的已关闭「<token> 在 <交易所> 上币截止日」二元市场，按 conditionId 去重；再用 data-api `/trades` 的 `start/end` 窗口取 `endDate−7d` 前的最后一笔真实成交（`No` 成交换算为 `1−price`），加 1¢ 半价差，按 GUIDE §8 的 0.07 费率，持到 Gamma 结算。
- 模型按 entry 原文：`p_model = 1 − exp(−λ·T)`；`λ` 只用进场前已结算市场做走前估计（`#Yes / 暴露天数`），最低 8 个市场 / ≥1 Yes / 365 天暴露，不满足则跳过；公告分支因无全场所免密钥历史时间戳未实现（已在脚本头部声明）。
- 预先写死宇宙、进场、费用、独立性口径与 PASS/FAIL/INSUFFICIENT 映射；输出 `run_output.txt`、`markets.csv`（190 行）、`REPORT.md`、`lint_output.txt`。原始下载在 `_cache/`（gitignore）。

## 验证命令

```bash
cd bots/quant/notes/q009-hist
python3 q009_hist.py
```

从缓存连续重跑两次，`run_output.txt` 与 `markets.csv` 逐字节一致（diff 退出码 0）。

## 关键结果（脚本原样）

- 枚举：37 个 event / 95 个 market / **27 个独立簇**；`endDate−7d` 时只有 17 个 market 仍有成交、10 个簇有价；触发 11 笔 / 5 个簇（YES 10、NO 1）。
- 主窗口：每簇中位净损益 **−0.019237/份**，均值 **+0.005535**，95% 簇 bootstrap CI `[−0.026675, +0.063828]`，命中率 **1/11**，每美元投入 **−0.143694**。
- 敏感性 `endDate−3d`：7 笔 / 2 簇，中位=均值 **−0.013987**，命中率 **0/7**。
- 走前模型 Brier **0.003467** vs 市场 **0.001712**；log loss **0.058913** vs **0.029309**（17 个有价市场全部结算 No）。
- 62/95 个 market 在 `endDate−7d` 前已结算，固定进场时点拿不到 30 个“进场时仍活着”的独立簇。

## 判定

**INSUFFICIENT**（27 个独立簇 < 30；仅 10 个有价、5 个触发）。按 entry 字面“少于 30 个独立事件即失败”的标准同时记 **FAIL**；可交易子样本的中位净损益也为负，模型 Brier 差于市场价。

## 局限

- 成交量小且集中：`next-coin-listed-on-binance` 一个 event 占 7 笔互斥选项；CI 很宽。
- 用最后成交价 +1¢ 近似 ask，无 L2；固定 0.07 费、无滑点/资金占用。
- λ 为常数风险率，多选 event 的互斥选项也计入暴露；公告分支未实现。
- Gamma public-search 有返回上限，枚举不保证全量；未修改任何 entry/INDEX/LOG/CLAIMS。

Lint：`python3 tools/check.py lint` 仍因既有 `muse-700/701` 缺字段失败，与本次无关（见 `lint_output.txt`）。
