# composer-003 回放摘要（OKX 资金费 z 闸门 · R2 开发窗）

**条目**：`composer-003-okx-funding-zscore-gate`  
**生成**：见 `replay_results.json` 的 `generated_utc`（UTC）

## 窗口与数据

| 项 | 值 |
|---|---|
| **开发窗（R2）** | `2022-01-01..2024-12-31`（UTC） |
| 数据源 | OKX `GET /api/v5/public/funding-rate-history`（免密钥） |
| 标的 | SOL / XRP / ADA / AVAX `*-USDT-SWAP` |
| 规则 | 30 期 z-score > 0.5 且当期 funding > 0 时持有 short-perp+long-spot 名义 **2,000 USDT** |
| 成本 | 开/平或换状态：每边 **0.30%** × 2（GUIDE §9） |
| 变体 | **1**（单组 z 窗=30、阈值=0.5） |

## 独立结果与结论

| 币 | 窗内 funding 条数 | 可计独立结果（8h/条） | 闸门后净结论 |
|---|---:|---:|---|
| SOL | 0 | 0 | 窗内无数据 |
| XRP | 0 | 0 | 窗内无数据 |
| ADA | 0 | 0 | 窗内无数据 |
| AVAX | 0 | 0 | 窗内无数据 |

**结论（R2 字段 `result`）**：**不显著** — 公开 API 分页约 **278 条/币（≈93 日）**，最早观测落在 **2025-07 之后**；按 GUIDE §9 **不得**将 2025+ 数字写入 R2 开发回放。在 **2022–2024** 窗内 **0 条** 可复现观测，独立结果 **<30**。

**`max_dd` / `contribution`**：窗内无序列 → **不清楚**（非“未跑脚本”）。

## 复现

```bash
cd bots/composer
python3 replay/composer-003/run_replay.py
```

产物：`replay/composer-003/replay_results.json`（<1 MB）。

## 后续（不编造）

- 若 OKX 扩展公开历史或提供免密钥归档 URL，在同一脚本窗过滤逻辑下重跑即可。
- R1 正文中的 2026 自测快照保留为「API 近端样本」，**不**替代 R2 开发窗结论。
