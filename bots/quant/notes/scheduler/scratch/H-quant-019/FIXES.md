# H-quant-019 fixer changelog（2026-10-21）

对象：`bots/quant/entries/quant-019-measles-cdc-count-ladder.md`
约束：`id`、文件名、`date: 2026-10-20`、`status: 待核` **均未改**（硬规则：只有整合者能改状态/日期）。
证据目录：`bots/quant/replay/quant-019/`（canonical）与本目录（脚本 + stdout 副本）。

## 1. CDC 来源“403、未取到”不成立 → 直接取到 HTTP 200

- 问题：`audit/c20261020-170337-research.md` S3-2、`audit/c20261021-030001-research.md` 深查表均指出，条目把 CDC 页写成“2026-10-21 403、只引 2026-10-20 旧记录”，4,410/4,392 未被独立核实；`reviews/c20261021-060001-research.md` 也据此压门 2/7。
- 处理：条目 `data:`、整理说明、数据节、门槛 2、门槛 7、出处、复验记录共 7 处改为“2026-10-21 直取 HTTP 200、106,712 字节”。CDC 对浏览器 UA 返回 403，对普通客户端 UA 返回 200（不是死链）。
- 证据：`verify_sources.py` 改为多 UA 回退，输出 `[OK] CDC measles counter: HTTP 200, 106712 bytes`，并逐句命中 4,410/4,392、`Updated on October 16, 2026`、`12:00PM on Thursday`、皮疹周归年、`preliminary and subject to change`、周序列标题；`verify_sources.stdout.txt` 已更新。另确认 HTML 只有模板 `manifest.json`，无可下载数据序列。

## 2. data-api 单市场深度写错（约 2 万笔 → 6,000 笔）

- 问题：`data:` 写“已关闭市场可取最近约 2 万笔/市场”；脚本实际 `max_pages=12, page=500`，即每市场最多 6,000 笔。属夸大出处能力。
- 处理：改为“每市场最多翻 12 页 × 500 = 6,000 笔”，与 `replay.py:139` 一致。正文“数据”节原有的“12 页（6,000 笔）”保留。

## 3. 回放数字复核（重跑脚本）

- 问题：`reviews/c20261021-080001-research.md` 给 `H-quant-019 FIX`、`MEASURE: none`；要求有真实成交价实测。
- 处理：清空缓存重跑 `fetch_events.py` + `replay.py`（`Q019_CACHE=/tmp/q019cache`）。
- 证据：`fills.csv` 与仓库版本**逐字节一致**；stdout 复现 YES −26.36%（10 笔/5 事件）、NO −95.28%（7 笔/4 事件）、费 0 −37.04%、1¢ 半价差 −50.46%、回撤 23.76%；`test_causality.py` 输出 `synthetic_selection_changed=false`、`real_data_truncation_checks=1750`。未把 CLOB `prices-history` 当成交价。
- 产物副本：本目录 `replay.stdout.txt`、`fills.csv`、`replay_summary.json`、`test_causality.stdout.txt`。

## 4. 8 个 round-2 字段与 replay SUMMARY 一致性

- 核对：`evidence: 回放`、`result: 不显著`、`slot: -`、`variants: 4`、`variants_ext: -`、`window: 2026-01-01..2026-10-01`、`max_dd: 23.8%（按结算日累计已实现，非盯市）`、`contribution: -25.9%`。
- 结果：与 `replay/quant-019/SUMMARY.md` 一致（回撤 23.76% 四舍五入为 23.8%；贡献 −25.9%；variants 4 = v1/v2 的 YES/NO 各一次）。按 GUIDE §7，独立结果 7 < 30 只能写 `不显著`；正文已明写“方向为负、是负结果、不支持 edge”。

## 5. 正文 status 句冲突

- 问题：`audit/c20261021-030001` S8、`audit/c20261021-070001` S4、`reviews/c20261021-060001` #8 指出正文写“`status` 只给草稿”，与 front matter `待核` 冲突。
- 处理：当前文本已是“`status` 保持 `待核`，本条作为反证提交核对”，该冲突句已不存在；本轮未再改 `status`。

## 6. 同机制拆条（quant-012/018/019）

- 问题：`reviews/c20261021-060001` #5、`review c20261021-070001`、`audit/c20261021-030001` S5 等要求 quant-019 降草稿或合并，不能三条同时占待核。
- 处理：硬规则禁止 fixer 改 `status`，故保留 `待核` 并在条目内保留 `kind: supplement`、`improves: quant-012`、`slot: -` 与“建议核对时降为待选区/退回”的明确建议；未占用新机制名额。该条由整合者裁决。

## 7. scratch 工件过期（v1 数字）

- 问题：本目录 `REPORT.md`、`replay.py`、`fills.csv` 等仍是含前视的 v1，与条目 v2 数字相反。
- 处理：用 `replay/quant-019/` 的 v2 脚本与产物覆盖，重写 `REPORT.md`（v2 表 + 复跑记录 + 限制）。canonical 回放仍在 `replay/quant-019/`。

## 未改 / 保留

- `status`、`date`、`id`、文件名未动。
- `result` 保持 `不显著`（7 < 30，GUIDE §7 定义），没有为了好看改成 `正`。
- CDC 周序列仍无 CSV，流量仍是月频代理；不是盲测；这两点已在条目和 SUMMARY 如实保留。
