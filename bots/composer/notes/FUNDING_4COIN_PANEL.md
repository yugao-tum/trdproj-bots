# OKX 四币 funding 面板（T03b，2026-10-21）

脚本：`notes/funding_4coin_panel.py` → `notes/funding_4coin_panel.json`

## 数据边界

- 公开 `funding-rate-history` 对每 `instId` **`after` 分页最多约 278 条**（约 **92.7 天**），最早约 **2026-07-20 UTC**（SOL 实测）。
- **未满 12 个月**；四币并行面板仍补全 003「横截面选币」证据，并标明 API 上限。

## 四币摘要（z>0.5 且 f>0 闸门）

| 币 | n | 全样本 mean (bps/8h) | 粗年化 | gated n | gated 粗年化 |
|---|---:|---:|---:|---:|---:|
| SOL | 278 | 0.29 | 3.22% | 86 | **9.34%** |
| XRP | 278 | 0.45 | 4.88% | 109 | **10.02%** |
| ADA | 278 | 0.49 | 5.32% | 109 | **10.77%** |
| AVAX | 278 | 0.38 | 4.13% | 115 | **10.57%** |

推断：四币在可用窗口内 **gated carry 均 >8% 粗年化**（未扣现货+永续手续费、无价格 PnL）；横截面轮换时 XRP/ADA/AVAX 与 SOL 同量级。

复现：`python3 notes/funding_4coin_panel.py`
