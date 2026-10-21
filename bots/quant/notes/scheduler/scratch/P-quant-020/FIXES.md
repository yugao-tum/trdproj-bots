# P-quant-020 修复记录（2026-10-21）

范围：`bots/quant/entries/quant-020-earnings-beat-base-rate.md`、`bots/quant/replay/quant-020/**`、本目录。
只读审计/复核：`reviews/c20261020-170337-research.md`（仅提到 quant-020 与 B29 机制不同，无修正项）、`checks/`（无文件提到 quant-020）、`audit/c20261020-1423-research.md`、`audit/c20261020-170337-research.md`、`audit/c20261021-030001-research.md`。
状态与日期未动：`status: 草稿`、`date: 2026-10-20`。

## 1. S1-2 / S2（高）：`-gaap- 344/537 = 64.06%` 混入 18 个无标签市场

- **问题**：审计 c20261020-1423 S1-2 与 c20261021-030001 S2 均指出，344/537 只有把 18 个无 tag 市场（5 个 MrBeast 推文市场 + 13 个旧 `will-*-beat-earnings-estimate`）全部并入 GAAP 才成立；严格 slug 口径应为 334/519（2026-10-20 快照）。
- **改动**：
  - 证据 1 改为严格 slug：2026-10-20 快照 `-gaap-` 334/519 = 64.35%；2026-10-21 重抓 `-gaap-` 337/523 = 64.44%。
  - 写明 18 个无标签市场的构成（10 YES / 8 NO；MrBeast 1 YES/4 NO；旧财报 9 YES/4 NO），并说明 344/537、347/541 是“全部并入 GAAP”的混合口径，已作废。
  - “钱从哪里来”的 GAAP/非 GAAP 数字改为 64.44% / 80.72%；风险节 16.9pp 改为约 16.3pp（并保留旧值作对照）。
  - 出处里的 `gaap 347/541` 改为严格 337/523，附无标签说明。
- **证据**：`verify_sources.py` / `verify_sources.out`（2026-10-21 重抓）：closed 1393 事件 / 1397 市场；YES 1038/359；gaap 337/523、nongaap 691/856、untagged 10/18；GAAP+旧13=345/535，GAAP+全部18=347/541。审计 c20261021-030001 S2 另给出 1378 快照严格值 334/519。

## 2. S7 / S11（低）：月度表合计 1365，与总数 1378 差 13

- **问题**：审计 c20261020-170337 S7 与 c20261021-030001 S11 指出，表只列近 13 个月，合计与总数差 13，未标注。
- **改动**：月度表改用 2026-10-21 的 1393 快照并标注“仅列近 13 个月”；2026-10 从 28 改为 43（截至 10-20）；补对账行“近 13 个月合计 1380，另 13 个更早事件（2024-01 1、2025-06 1、2025-09 11）未列，合计 1393”。
- **证据**：`verify_sources.out` 的 monthly 段：2025-10..2026-10 共 1380；2024-01=1、2025-06=1、2025-09=11；总 1393。

## 3. S3-4（低）：模板 URL 不可直接请求

- **问题**：审计 c20261020-1423 S3-4 指出 `offset=0..1400` 返回 422、`market=<clobTokenId>` 返回 400。
- **改动**：
  - Gamma 数据节与出处改为 `offset=0` 具体示例，并注明其余页按 100 递增；保留“`0..1400` 模板会 422”的说明。
  - CLOB 数据节加入真实 token 示例：`cof-quarterly-earnings-nongaap-eps-10-20-2026-5pt57` 的 token `104559595660296147678443697835737075405315985842087214448659759392424486465642`，访问 2026-10-21 HTTP 200、68 个点；注明 `<clobTokenId>` 占位符直接请求会 400。
  - data-api 加入真实 conditionId 示例（cof 事件）。
- **证据**：`verify_sources.out` 末尾 “concrete Gamma offset=0 HTTP 200 … / concrete CLOB prices-history HTTP 200 … points=68”；另在本机用同 URL 复核 HTTP 200、68 点。

## 4. 第 2 轮缺 8 字段、缺 replay 目录

- **问题**：条目无 `evidence/result/slot/variants/variants_ext/window/max_dd/contribution`，也没有 `replay/quant-020/`；第 2 轮要求真实成交价回放。
- **改动**：
  - front matter 加 8 字段：`evidence: 回放`、`result: 负`、`slot: -`、`variants: 8`、`variants_ext: -`、`window: 2024-01-19..2026-10-20`、`max_dd: 5.3%（按事件已实现，20 USDT/笔）`、`contribution: -0.1%`。
  - 新建 `bots/quant/replay/quant-020/`：`run_replay.py`（可重跑）、`events_frozen.csv`（派生快照）、`trades.csv`（逐事件）、`results.json`、`run_output.txt`、`SUMMARY.md`（按 `templates/REPLAY-SUMMARY.md`）。
  - 正文新增“第 2 轮回放”段；证据 3 与成本/容量节补年化贡献算法。
- **证据**：`replay/quant-020/run_output.txt`：1,384 事件 / 101 带内；101/101 最后一笔 YES 等价成交与冻结 p24 一致；97/101 有 ask 打印；POOLED n=97 均值 −0.0140/份、CI [−0.1292,+0.0817]；STRICT_OOS n=68 均值 −0.0634/份、中位 −0.4120、CI [−0.1638,+0.0366]；20 USDT/笔总 PnL −8.52、已实现回撤 266.58 USDT=5.3%、年化贡献 −0.12%；result 负。`results.json` 为机读汇总。

## 5. 审计/任务要求“直说是否应丢弃”

- **改动**：“本轮加固结论”改为“本轮结论：建议丢弃”，写明不进待核的三条理由（扣成本后负、容量不足、正结果只在选带窗口内）；正文与 front matter 的 `result: 负` 一致。
- **证据**：条目“本轮结论”“第 2 轮回放”“门槛自查 5”；`replay/quant-020/SUMMARY.md` 的 result/不可靠原因。

## 6. 出处重抓

- **改动**：把引用 `H-quant-020/verify_sources.out` 改为本次 `P-quant-020/verify_sources.out`（旧输出的 gaap 用了混合口径），并保留 H 的 strict_oos / spotcheck 作为严格样本外与抽样复核证据；新增 replay 与 FIXES 出处。
- **证据**：`P-quant-020/verify_sources.out`（Gamma 1393/1397、HIMS 10 个规则短语全命中、CLOB 68 点、SEC HTTP 200 `hits.total=10000 relation=gte`）。

## 7. 未改的内容

- 审查/检查未点名的段落（如 247 样本分桶表、规则原文、风险清单）保持原样，只做与新数字直接冲突的最小改动。
- `checks/` 下没有提到 quant-020 的文件；`reviews/c20261020-170337-research.md` 只确认 quant-020 与 B29 机制不同，无修正项。

## 备注：验证命令

```bash
python3 bots/quant/notes/scheduler/scratch/P-quant-020/verify_sources.py
cd bots/quant/replay/quant-020 && python3 run_replay.py
python3 tools/check.py lint --bot quant
```
