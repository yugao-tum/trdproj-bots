## 做了什么

- 新增 `bots/quant/notes/q018-price-test/q018_price_test.py`：Gamma 枚举 43 个已关闭周度事件（Hormuz 31 / Bab 12）；CLOB 逐档价格用 `startTs/endTs` 分段（≤10 天，`fidelity=60`）取全 **242/242** 档；PortWatch 5,682 行日度数据复算。
- 基准率严格用事件周起点前 12 个完整 Mon–Sun 周，Laplace `p_i=(k_i+1)/(12+n)`；市场参考价取周起点 00:00 UTC 前最后一条价格（首价完整 43/43，周起点价完整 34/43）。
- 计算多分类 Brier、配对 t / 符号检验、Bab 买 NO 的历史 P&L（1¢ 半价差，GUIDE §8 地缘费率 0）。

## 关键结果（详见 `run_output.txt` / `REPORT.md`）

- 价格覆盖：首价 **43/43**；周起点价 **34/43**；非空档位 **242/242**。`interval=max` 对 2026-09-07 及更早事件返回空，改用 `startTs/endTs` 后补齐。
- Brier 全部 43 event：模型 **0.7658** vs 市场首价 **0.8060**，差 **+0.0402**；配对 t p=0.4198，符号检验 p=0.5424（不显著）。
- 剔除 2026-03..05 的 9 个复算 MISMATCH 后，MATCH-only n=34≥30：0.7576 vs 0.7998（+0.0422）。
- 分海峡：Hormuz 模型 0.7302 vs 0.8071（+0.0770）；**Bab 模型 0.8580 vs 0.8032（-0.0548，n=12）**。
- 只用 2026-07-13 后的 25 个事件（n<30）：0.7280 vs 0.7764，标准 (3) 应读作 INSUFFICIENT。
- Bab NO 交易（纯周起点价，29 份）：中位毛利 **+0.2250/份**，总毛利 +0.7970，总投入 21.2030，每美元投入 **+0.0376**，命中率 **0.7586**。
- 失败标准：(1) 按 Bab 周起点价 **PASS**；(3) 按全部 43 event **PASS**，但只靠 Hormuz，只做 Bab 的子集 n=12<30 且方向为负，对实际 Bab 规则应读作 **INSUFFICIENT**。

## 复现

```
python3 bots/quant/notes/q018-price-test/q018_price_test.py
```

从 `_cache/` 重跑，`run_output.txt` / `events.csv` / `buckets.csv` / `REPORT.md` 哈希一致。

`python3 tools/check.py lint` 在当前 HEAD 上**退出 1**：`bots/muse/entries/` 的既有 frontmatter 问题（部分文件 frontmatter 前有额外行，缺 `id` 导致 KeyError），与本任务新增的 notes 无关；完整输出见 `lint_output.txt`。

## 限制

- 价格是逐档最后成交价，不是可执行盘口；1¢ 半价差为预先假设，没有历史深度/挂单量。
- PortWatch 为事后修订值；2026-03 至 2026-05 有 9 个事件复算档位与 Gamma 结算不一致。
- Bab 仅 12 个已关闭事件，交易触发 29 份，不是独立 event 数；同周两海峡高度相关。
- 未做前向成交，标准 (2) 不适用；标准 (1) 的正式口径只用周起点价，避免周中首价的前视。
