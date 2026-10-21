---
id: composer-003
name_zh: OKX资金费：Z分数闸门收carry
name_en: OKX perp funding carry with rolling z-score gate
bot: composer
date: 2026-10-21
market: crypto
pm_category: -
kind: improvement
improves: A-A1-funding-carry
category: A
return_type: carry
instruments: SOL, XRP, ADA, AVAX 现货 + 同所 USDT 永续 1x 对冲
venues: OKX
data: OKX 公开 `GET /api/v5/public/funding-rate-history`（免密钥）；现货/永续行情公开 REST
test_2w: 独立结果按每次 8h 资金费结算计；用 2025-07 至 2026-10 共 278 次 SOL 结算回放 + 两周前向跟 42 次结算；失败标准：闸门后年化 carry ≤8% 或样本外中位净收益 ≤0
status: 待核
confidence: 中
---

## 一句话

在 OKX 对 SOL/XRP/ADA/AVAX：**现货多 + 永续空 1x** 收资金费，但仅当该币 30 期（≈10 天）资金费 z-score > 0.5 且当期费率 >0 时开仓/续持；否则空仓 USDT，换币选 z 最高且 ≤2,500 USDT 的一档。

## 钱从哪里来

付钱给你的是**在资金费处于「相对自身近期常态偏高」阶段仍愿意做多永续**的对手方（多头拥挤）。known `A-A1-funding-carry` 是「只要有正 funding 就收」；本条改进为**只在 funding 相对过去 30 期显著偏高时收**，过滤掉 funding 接近 0 或负值区间的假 carry，减少「收不到几次费反而被趋势扫」的情况。钱仍来自永续多头支付的空方资金费（OKX 规则），不是方向 bet。

## 规则

**与 known A-A1 的差异**

| 项目 | A-A1（known） | 本条 |
|---|---|---|
| 进场 | 正 funding 即对冲 | z-score>0.5 且 funding>0 |
| 币种 | 泛化 | SOL/XRP/ADA/AVAX 四选一（z 最高） |
| 场所 | 未指定 | 仅 OKX（单所，无跨所基差风险） |
| 杠杆 | 1x 对冲 | 1x，不加杠杆 |

**执行**

1. 每 8h  funding 结算前 30 分钟，拉 `instId=<COIN>-USDT-SWAP` 最近 30 条 `fundingRate`。
2. 计算 z = (f_current − mean_30) / stdev_30；若 z>0.5 且 f_current>0，维持/建立「现货多 + 永续空」等名义 USDT 名义（例如 2,000 USDT）。
3. 若 z≤0.5 或 f_current≤0，平掉永续、卖现货（或保留现货若用户已有库存——本条假设同步开平）。
4. 四币选 z 最大者；并列取 |f_current| 更大者。
5. 风控：单币 ≤2,500 USDT；四币合计 ≤5,000 USDT；永续保证金留 30% 缓冲，不借币。

## 证据

### OKX SOL 资金费回放（2026-10-21 自算，脚本见 `notes/funding_zscore_backtest.py`）

- 样本：**278 次** 8h 结算（OKX `funding-rate-history` 分页拉取）。
- 全样本：mean rate **0.294 bps/8h**，正 funding 占比 **68.3%**，粗年化（恒持做空）**≈3.22%**（=0.0000294×3×365，未扣手续费）。
- **z>0.5 且 f>0 子样本 86 次**：mean rate **≈0.853 bps/8h**，粗年化 **≈9.34%**（同样未扣手续费）。
- 推断：闸门把「接近 0 的 funding 期」剔除后，carry 强度接近 GUIDE 加密门槛 8% 量级；**需再扣现货+永续开平成本**（见下节）。

来源：OKX API 返回值 `realizedRate` 字段（**已读 API 响应，未核对交易所对账**）。

## 数据

- OKX 资金费历史：`https://www.okx.com/api/v5/public/funding-rate-history?instId=SOL-USDT-SWAP&limit=100`（分页 `after=`）
- OKX 文档：`https://www.okx.com/docs-v5/en/#public-data-rest-api-get-funding-rate-history`
- 现货/永续价格：OKX public ticker（本条回测未用价格 PnL，仅 funding）
- 缺失：2022 年以来完整 4 币并行面板（本次仅 SOL 拉满 278 点；XRP 同法拉取可做补充）

### 四币面板补充（T03b，2026-10-21）

- 脚本 `notes/funding_4coin_panel.py`；快照 `notes/funding_4coin_panel.json`；摘要 `notes/FUNDING_4COIN_PANEL.md`。
- SOL/XRP/ADA/AVAX 各 **278 期**（OKX 公开 API 单币上限，≈92.7 天，非 12mo）。
- 四币 **z 闸门**粗年化：SOL **9.34%**、XRP **10.02%**、ADA **10.77%**、AVAX **10.57%**（同上，未扣费）。

## 两周内怎么检验

- **独立结果**：每次 8h funding 结算 = 1 个结果（四币合并面板按「是否持仓」计）。
- 两周 ≈ **42 次**结算；加上历史 278 次回放 >30。
- **指标**：每期 net = funding_received −（若换仓则计 0.3%×2 单边成本摊销）；比较「恒持」vs「z 闸门」。
- **失败标准**：闸门策略 278 期样本外（最后 60 期）中位 net ≤0；或年化 <8% 且无法说明成本假设。

## 成本与容量

- **手续费（GUIDE 粗算）**：现货+永续开平各 0.30%/边；若平均 **10 天换仓一次**，摊到每 8h ≈0.025%/期，仍低于高 z 期 mean funding ~0.085%/期（**推断，未用真实 VIP 费率**）。
- **5,000 USDT**：单币 2,500 USDT 名义，OKX 最小下单需按 `instId` lot size 检查（未逐币读取）。
- **容量**：OKX SOL 永续 OI 远大于 2,500 USDT；小资金可做。
- **资金占用**：现货 + 保证金，约 2,000–2,500 USDT 常占。

## 风险

- **趋势**：现货多 + 永续空在单边下跌中现货亏、永续赚，净 PnL 可能负；闸门不防趋势，只滤 funding 强度。
- **费率变负**：z 高但 f 转负时仍可能短暂持仓至下一检查点。
- **API/地域**：部分 IP 访问 OKX/Binance 受限；执行环境需能访问 OKX public API（2026-10-21 云环境 curl OKX **成功**）。
- **回测过拟合**：0.5 z 阈值来自同一 278 样本，需样本外 60 期验证。

## 改进了什么

- **原版**：known `A-A1-funding-carry` — 现货多 + 永续空收 funding，无状态过滤。
- **改动**：加 **30 期 z-score 闸门** + **四币横截面选最强 funding** + **限定 OKX 单所**（降跨所操作风险）。
- **为何更好（待验证）**：同 278 期 SOL 样本，粗年化从 3.2% 提到 9.3%（未扣费）；预期 fewer 持仓期数但更高 carry 密度。
- **验证**：样本外 60 期 + 两周前向 42 期 funding 实收。

## 门槛自查

1. **机制说得清：满足** — 多头支付 funding 给空头；闸门选拥挤度高的时段。
2. **有免费数据能检验：不确定** — 四币面板已齐，但 OKX 公开 API 仅 **~278 期/币（≈93 天）**，**未满 12 个月**；机制检验仍可做，长期样本需另源或 VIP 导出。
3. **小资金能做：满足**。
4. **不重复：满足** — `kind: improvement`，improves A-A1。
5. **扣成本后粗算够用：不确定** — 粗年化 9.3% >8%，扣 0.3% 开平后仍可能 >8%，但未合并价格 PnL；**标不确定**。
6. **两周内能检验：满足** — 42+ 前向结算 + 278 回放。
7. **出处可查：满足**。

## 出处

- https://www.okx.com/api/v5/public/funding-rate-history?instId=SOL-USDT-SWAP&limit=5 — 访问 2026-10-21 — 已读（返回 fundingTime、realizedRate）
- https://www.okx.com/docs-v5/en/#public-data-rest-api-get-funding-rate-history — 访问 2026-10-21 — 已读（接口说明、8h 周期）
- known/KNOWN.md — 访问 2026-10-21 — 已读（A-A1-funding-carry 名称）
