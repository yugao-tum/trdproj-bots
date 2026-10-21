# quant 的工作日志

只追加，不改旧记录。

## 2026-10-20
- 做了什么：建目录；读完 README、GUIDE、templates、known（135 条）、reviews、tools/check.py、dot 与 muse 的目录。
- 新增或修改的文件：bots/quant/README.md、INDEX.md、CLAIMS.md、LOG.md
- 查了多少个来源：0（仅仓库内文件）
- 遇到的问题：无

## 2026-10-20（认领）
- 做了什么：按 known/ 135 条与 dot C01–C49 逐题查重（grep 关键词：mention/tweet/tennis/leaderboard/FDV/roadmap/netflix/draw/coinbase premium/breadth 等，仓库内无同机制），认领 3 个迁移题和第 1 批 10 个新题。放弃了“USDC/USDT 稳定币对区间挂单”（与 dot-026 锚定偏离回归太近）。
- 新增或修改的文件：bots/quant/CLAIMS.md、LOG.md
- 查了多少个来源：0（仓库内查重）
- 遇到的问题：无

## 2026-10-20（迁移 x-quant-trials）
- 做了什么：读私有研究工作台 x-quant-trials 的 README、ARCHITECTURE、CANDIDATE、COLLECTED_POOL、PROMOTE_CHECKLIST、CONTINUOUS 和相关脚本。收藏池 303 个“孪生”= VM 基础 158 + VCB 基础 144 + 1 个其他，每个只是换一个 BTC 指标开关，按 GUIDE“拆条不算”合并为一个机制（quant-001，改进 T-T2-vm）。VM 本身=T-T2-vm、VCB≈T-T1-vcb-mcld、逆波动风险平价=T-T2-rptrend、ETH 时序动量=T-T2-tsmom、RS 轮动=T-T3-rotation、FOMC/NFP 周开关≈E-E1-macro-window，均不另立条目；TIPP/CPPI、ATR×唐奇安、周度 TSMOM 等私有研究自己已否决，丢弃。另写 1 条日历反证补充（quant-002）和 1 条广度闸门补充草稿（quant-003）。
- 因私有仓库评审打不开，新写 reproduce.py 只用 data.binance.vision 公开日线重算，VM、SAR、CCI 版本与私有日志一致；%B 版本未复现，不用。发现私有代码里日历窗口错后一天，已在 quant-002 中两种都列出。
- 新增或修改的文件：entries/quant-001、002、003；notes/xqt-migration/README.md、reproduce.py、results.csv、.gitignore；CLAIMS、INDEX、LOG
- 查了多少个来源：4（data.binance.vision 213 个日线包；Barroso & Santa-Clara 2015 的 RePEc 与 ScienceDirect 摘要）
- 遇到的问题：api.binance.com 在本机返回 451，改用 data.binance.vision；SSRN 返回 403。

## 2026-10-20 第 1 批（B01–B10）

- 10 个并行 pi（meiying/deepseek-flash）各写一题草稿 + 自留核对日志；10 个 glm-5.3 逐 URL 重抓、逐数字核查：1 个 KEEP、9 个 FIX，无编造，无重复。
- 按核查报告修正：占位 id、B01 spread 最大值 0.82→0.86 与搜索网址、B02 时间换算、B04 资金 386→120、B05 规则原文按 slug 分开引用（2026 vs 2027 截止）、B06 两个周度市场成交量张冠李戴、B07 流动性改为带时间的实抓值、B08 百分比口径 −0.06%→−0.3%、B09 107→114（0.0767→0.0817）与 M5.5 计数复核、B10 arXiv 10→7 条与 name_zh。
- 待核 8 条（quant-005/006/007/009/010/011/012/013），草稿 2 条（quant-004 无回测；quant-008 门槛 5、6 不过）。本轮待核累计 10/15。
- 核对日志移出正文，存 notes/batch1-verification/。

## 2026-10-20 第 2 批认领

- 先认领再动手：B11–B18（8 个 Polymarket，含未碰过的 finance、geopolitics 板块）、B19–B20（加密）、Q04（quant-004 回测）。

## 2026-10-20 第 2 批（B11–B20）与 Q04

- 10 个 deepseek-flash 写稿（多数附可复跑脚本）→ glm-5.3 重抓、重跑脚本：2 个 KEEP、8 个 FIX，无编造。修正：占位 id、B12 回归样本含 2026（“走前检验”改为样本内）、B13 两处算术（0.94%→1.25%，±3.1→±5.0）、B14 卖价和口径、B15 三个数字（rewardsMinSize 50、18/30、模板 6 个）并改为补充 quant-012、B18 年度计数不可复现已删、B20 若干日期/计数。
- 待核 5 条：quant-014（SPX）、016（烂番茄）、018（海峡通行，补充 quant-012）、019（麻疹）、020（财报超预期）。草稿 5 条：015、017、021、022、023。本轮待核累计 15/15。
- Q04：quant-004 补了已结算提及市场回测（1,313 个已关闭事件，取最近 200 个），本人用缓存重跑结果一致；表面 R1 有正收益，但 endDate 不是讲话开始时间，有前视偏差，去掉期间类后不显著 → quant-004 仍为草稿。

## 2026-10-20 第 2 轮准备（一）

- 查 GUIDE §3 与 tools/check.py：每轮限额对**所有** `待核` 条目生效（`ROUND_CAP = 15`，按条目 `date` 所在轮计），不分 `kind`；改进条目同样占额度，待选区是核对结局，不是单独状态。所以不另开“额度外”的改进条目；第 2 轮仍按 15 条挑最强的，同等条件下优先 `improvement`（采纳 2 分，高于待选区 1 分）。
- quant-015：加真正的走前校准（2000 年起 321 个月，每月只用之前的数据估参），log loss 1.3638，均匀分布 2.0794；glm 重跑脚本逐字一致。价格侧只有 1 个已关闭事件有价格历史，仍为草稿。
- quant-003：十币预注册宇宙、6 个年度样本外折，闸门按 Sharpe 只赢 3/6 折（预注册 ≥4/6）→ 放弃，证据保留。
- quant-008、quant-022 放弃（门槛结构性不满足 / 结论为负）。quant-023 扩到 2020-08 后不稳健，且加强版年化算法有误（按交易日折年），不提交加强版，直接放弃。
- 第 3 批短名单（预研，未回测）存 notes/batch3-shortlist.md，先认领 B21–B25。

## 2026-10-20 第 2 轮准备（二）

- quant-004 按真实讲话开始时间重跑（Q04b）：前作 H6 有 45.3% 入场点在开始之后；修正后 R1 样本外不显著，R3 显著为负 → 不升待核，留草稿。核查发现原稿“309 个点”不可复现，已在报告中更正。

## 2026-10-20 第 2 轮准备（三）

- quant-021（F1）加强：49 个有完整价格历史的已结算事件，2024–2026 样本外；预注册规则扣 1¢ 半价差 + 0.05 费净 +0.343/份（21 笔），半价差 5¢ 时约 +0.303；但价格是最后成交价、不是可成交盘口，基于名次差的模型样本外 log loss 0.7236 劣于常数 0.6960。glm 核查重跑脚本一致。暂留草稿，列为第 2 轮待核候选。

## 2026-10-20 第 2 轮准备（四）

- quant-017（App Store）加强：用 Wayback 存档的结算源网页算名次黏性。预注册口径（04–08/14–18 UTC）2025 年 54 天，06:00 的第 1 名到 16:00 仍是第 1 名 47/54 = 87.0%；实际执行时窗口放宽到 04–09/14–19（71 天，90.1%），已在正文标为事后放宽口径。已结算 117 个周度榜，`Other` 14/117 = 12.0%，关闭后仍带 Reserved 臂 8/117。两轮 glm 核查，所有指出的错误已更正。仍无收益回测，留草稿，第 2 轮待选区候选。

## 第 2 轮（2026-10-26 起）排队

- 待核候选（届时把 `date` 改为提交日、状态改 `待核`；上限 15）：quant-021（F1，49 事件样本外）、quant-017（App Store）、quant-015（全球月均温，走前校准）。
- 第 3 批新题：B21 NFL、B22 龙卷风风险区、B23 干旱 D4、B24 板球、B25 大学橄榄球（短名单见 notes/batch3-shortlist.md）。
- 不再提交：quant-003/008/022/023（已放弃），quant-004（去掉前视后不显著）。

## 2026-10-20 第 1 轮复核修正

- quant-013：按 PR #2（`bots/quant/notes/q013-oos/REPORT.md`）补入预注册 TRUE_OOS（2021-05-04..2025-08-14）：BTC 109 个事件、事件级 3 日净收益中位 −0.4019%、规则 −33.272% vs 买入持有 +122.3591%；SOL 109 个事件、中位 −0.2460%、规则 −74.0305% vs +351.4260%；两条预注册失败标准均触发，判定 FAIL；门槛 5 改为不满足，`status` 改 `草稿`，撤回第 1 轮复核。
- quant-001：按 PR #1（`bots/quant/notes/xqt-migration/q001-robustness/REPORT.md`）补入 106 个预先指定闸门的多重检验：DSR N=106 为 0.991354、N=224000 为 0.851374；PBO 0.3810；Holm/BH 校正后均值差与 Sharpe 差均 0/105 显著；Sharpe/回撤/收益胜出比例 26/105、94/105、6/105。改写“一句话”与“改进了什么”：稳健改进是更低回撤/仓位，不是更高收益/Sharpe。
- quant-018：按 PR #4（`bots/quant/notes/q018-price-test/REPORT.md`）补入 43 个已关闭事件的价格侧检验：首价 43/43、周起点价 34/43；Brier 全样本 0.7658 vs 0.8060（p=0.4198，不显著）、Bab 子集 n=12 为 0.8580 vs 0.8032（更差）；Bab 周起点价交易 n=29、中位 +0.2250/份；两周检验一节改为历史侧已完成。
- quant-019：按 PR #3（`bots/quant/notes/r1-audit/AUDIT.md`）认定与 quant-012 同机制、仅更换计数源；改 `kind: supplement`、`improves: quant-012`，并改写“改进了什么”与门槛 4。
- quant-021：占用 quant-013 撤回后空出的 1 个待核名额，`status` 改 `待核`（`date` 仍为 2026-10-20）；补一行“CLOB prices-history 是最后成交价/小时级抽样、不是可执行 ask”的复核关注；门槛自查 7 条完整。
- INDEX：quant-013 状态改 `草稿`、quant-021 改 `待核`；LOG 追加本条。013→021 的名额替换是建议，由 owner 在 2026-10-25 23:59 UTC 前决定接受或拒绝。
- 未改动允许范围外的文件；复核笔记保留在各自 PR 分支，本分支只按路径引用。

## 2026-10-20 第 1 轮名额调整：quant-006 降草稿，quant-015 升待核

- quant-006：按 `bots/quant/notes/q006-hist/REPORT.md`（PR #7）的历史可成交价回测（2080 场有价、1366 笔触发，主窗口净中位 −0.114895/份、每美元 −0.063537；Elo Brier 0.216187 劣于市场 0.196510），预先写死的失败标准触发 → FAIL。`status` 改 `草稿`，正文顶部加降级说明，门槛 5、6 改为不满足；原稿其余内容保留。
- quant-015：占用空出的 1 个待核名额，`status` 改 `待核`（`date` 仍为 2026-10-20）。选择理由：剩余草稿中 003/008/022/023 已放弃、004 去前视后不显著、013 样本外 FAIL；017 与已待核的 quant-007 同机制（r1-audit 判变体，007 先到），同轮并列会按“拆条不算”合并；015 无重复（dot-001/002 是城市日最高温），有 321 个月走前校准（log loss 1.3638 vs 均匀 2.0794）且 glm 核查 KEEP，预期结局待选区（1×1.3），无编造风险。门槛 5、6 仍如实写不满足，未新增任何数据。
- INDEX：006 改 `草稿`、015 改 `待核`，补登 notes/q006-hist/ 6 个文件。本轮待核仍为 15/15。
- 新增或修改的文件：entries/quant-006、entries/quant-015、INDEX.md、LOG.md
- 查了多少个来源：0（只用仓库内已有报告与核对日志）

## 2026-10-20 第 1 轮名额更新：011 降草稿，018/020 写入可成交价检验结果

- quant-011：按 `bots/quant/notes/q011-hist/REPORT.md`（PR #9）的历史可成交价回测，主窗口 161 场触发（≥30）、每份净收益中位 −0.2389、每美元投入 −22.82%、命中率 18.6%，预先写死的失败标准触发 → FAIL。`status` 改 `草稿`，正文顶部加降级说明，门槛 5 改“不满足”、门槛 6 改“满足（历史口径）”；原稿其余内容保留。
- quant-018：按 `bots/quant/notes/q018-paired/REPORT.md`（PR #8）补“同时点可成交价配对检验”：覆盖 24/43（Hormuz 19/31、Bab 5/12），冻结标准 (1) PASS（Bab n=18，中位净利 +0.2400/份），标准 (3) INSUFFICIENT（n=24<30），总体 INSUFFICIENT；旧 Brier 优势与 Bab 交易经济性未在同时点可成交价下复现，5¢ 压力每美元 −0.0203。门槛 5 仍不确定、门槛 6 改“不满足（同时点口径）”，`confidence` 改 `低`；另以中性一句记录 dot-051 的 start 价 Brier 方向。
- quant-020：按 `bots/quant/notes/q020-oos/REPORT.md`（PR #10）补“可成交价时间切分样本外检验”：HOLDOUT n=47 按冻结判据 PASS（中位 +0.4376/份），但 DISCOVERY 中位 −0.4313、POOLED 均值 +0.0081，HOLDOUT/POOLED 的周聚类 bootstrap 均值 95% CI 均跨 0。门槛 5 改“不确定”，门槛 6 按 GUIDE §2 第 6 条记“满足（历史口径，47 个独立公司-季度事件）”，并注明前向 14 天带内最多 24 个。
- 新增 `bots/quant/notes/q020-forward/`：预注册前向复核，复用 `../q020-oos/q020_oos.py` 逻辑（未改动该文件），只评估 `endDate ∈ [2026-10-21T00:00Z, 2026-10-26T00:00Z)` 的事件；本轮运行窗口内 29 个事件全部未结算，输出 `PENDING`，无判定。
- INDEX：quant-011 改 `草稿`；补登 notes/q011-hist/（7 个）、q018-paired/（8 个）、q020-oos/（7 个）、q020-forward/（4 个）文件。
- 名额：待核 15→14。空出的 1 个名额**有意留给 owner**（Quant Bot 正在进行的 quant-030/031），本轮不把任何草稿升为待核。
- 新增或修改的文件：entries/quant-011、entries/quant-018、entries/quant-020、INDEX.md、LOG.md、notes/q020-forward/{README.md,q020_forward.py,run_output.txt,.gitignore}
- 查了多少个来源：0（只用仓库内已有报告；q020_forward.py 本轮运行只读公开 Gamma/data-api，用于确认 PENDING）

## 2026-10-20 调度批次 c20261020-1423-research（research）

- 调度批次（profile research），10 个 OpenCode 工作者；合并：B21 merged、B22 merged、B23 merged、B24 merged、w07 merged、I01 merged、w10 merged、w08 failed。
- 审核结论：B21 DROP、B22 FIX、B23 FIX、B24 DROP、I01 DROP。
- 升为待核：无（只出草稿）；推送时 origin/main 第 1 轮待核 15 条。

## 2026-10-20 quant-009 历史可成交价回测笔记（PR #13）

- 新增 `bots/quant/notes/q009-hist/`：`q009_hist.py` 用 Gamma public-search 枚举已关闭的上币截止日市场，data-api 取 `endDate−7d` 前最后成交 +1¢ 半价差、0.07 费率，走前基准率模型；结果 27 个独立簇 < 30 → INSUFFICIENT（按条目字面标准同时记 FAIL），详见 `REPORT.md`。
- 本 PR 未修改 entries/quant-009 的字段与 `status`（仍 `待核`）；是否据此降级留给 owner 决定。
- INDEX：补登 notes/q009-hist/ 7 个文件。
- 新增或修改的文件：notes/q009-hist/{.gitignore,REPORT.md,lint_output.txt,markets.csv,pr_body.md,q009_hist.py,run_output.txt}、INDEX.md、LOG.md
- 查了多少个来源：0（只读公开 Gamma/data-api 接口，无密钥）

## 2026-10-20 第 1 轮名额更新 3：005/009 按可成交价回测结果降草稿

- quant-005：按 `bots/quant/notes/q005-hist/REPORT.md`（PR #14）的历史可成交价回测（xtracker 逐条帖时间戳 + data-api 已关闭市场成交），50% 决策点触发 **252 个独立事件（≥30）**，每份净收益中位 **−0.034596**、均值 **−0.012555**、每美元投入中位 **−1.047500**、命中率 **0.0992（25/252）**；ISO 周 block bootstrap 均值 95% CI **[-0.048273, 0.026127]** 跨 0；模型 log loss（原始 **2.269900**、NB **1.802055**）劣于市场归一化价 **1.473311**（n=225），75% 决策点 n=197、中位 **−0.036922** 同为负；预先写死的失败标准触发 → **FAIL**。`status` 改 `草稿`，正文顶部加降级说明，门槛 5 改“不满足”、门槛 6 记“满足（历史口径）”；风险节补一句 tracker 最终计数落档与 Gamma 结算档 **20/257 不一致（7.8%）** 的结算源风险。字面口径 `run_output_literal_le.txt`（只保留 `partial ≤ n_elapsed`、去掉“最终计数 ≥ n_elapsed”硬约束）n=257、中位 **−0.023076**、命中率 **0.0778（20/257）**，结论同为 FAIL。原稿其余内容保留。
- quant-009：按 `bots/quant/notes/q009-hist/REPORT.md`（PR #13）的历史可成交价回测（Gamma 枚举 + data-api 成交 + 走前基准率），独立簇 **27 < 30**、有价簇 **10 < 30**，5 个簇触发 11 笔，每簇净收益中位 **−0.019237**、命中率 **1/11 = 0.091**、每美元投入 **−0.143694**；走前模型 Brier **0.003467** 劣于市场 **0.001712**（log loss **0.058913** vs **0.029309**）。脚本判 **INSUFFICIENT**，按条目字面“<30 个独立事件 → FAIL”同时记 **FAIL**。`status` 改 `草稿`，正文顶部加降级说明，门槛 5、6 改为不满足；原稿其余内容保留。
- 复现校验（本任务）：q009 从缓存重跑，`run_output.txt` 与提交版 `diff` 为空（退出码 0），`markets.csv` sha256 同为 `e11b63405ba1e503e58b30efa55097351a786c12ca4f274d2bcfc97c4e37d324`；q005 无提交缓存、重跑时上游新增 1 个已关闭事件与 13 条帖（closed 385→386、posts 13683→13700），stdout 的 n 由 252→253，但判定仍为 FAIL、每份净收益中位仍为 **−0.034596**，差异不改变结论；本条引用仍以提交版 `run_output.txt` 的 252 为准。
- INDEX：quant-005、quant-009 状态改 `草稿`；补登 `notes/q005-hist/` 7 个文件（q009-hist 的 7 行已由 PR #13 登记，未重复添加）。
- 名额：待核 14→12（`grep -c '^status: 待核' bots/quant/entries/*.md` 汇总为 12）。空出的 2 个名额**有意留给 owner**（Quant Bot 正在进行的 quant-030/031/017），本轮不把任何草稿升为待核。
- 新增或修改的文件：entries/quant-005、entries/quant-009、INDEX.md、LOG.md
- 查了多少个来源：0（只用仓库内已有报告；两个脚本重跑只读公开 Gamma/data-api/xtracker，未用密钥）

## 2026-10-21 登记 quant-005 历史回测笔记（PR #14）

- quant-005：`bots/quant/notes/q005-hist/REPORT.md` 历史可成交价回测，触发样本 n=252，每份净收益中位数 −0.034596 ≤ 0 → 冻结标准判 FAIL（字面版规则结论相同）。本次只登记笔记，entry 文件未改动。
- INDEX：补登 notes/q005-hist/ 7 个文件。
- 新增或修改的文件：INDEX.md、LOG.md
- 查了多少个来源：0（只用仓库内已有报告）

## 2026-10-21 调度批次 c20261020-201107-research（research）

- 调度批次（profile research），10 个 OpenCode 工作者；合并：B25 failed、B22 merged、B23 merged、I02 merged、w09 failed、B31 failed、w08 merged。
- 审核结论：无。
- 升为待核：无（只出草稿）；推送时 origin/main 第 1 轮待核 14 条（原记录的 15 是按过期工作区计的，已更正）。

## 2026-10-21 调度批次 c20261020-170337-research（research）

- 调度批次（profile research），10 个 OpenCode 工作者；合并：B29 merged、B30 merged、quant-015 merged、quant-017 merged、I03 merged、w07 merged、w08 merged、w09 failed（2026-10-21 更正：原记录把后来被中止的 fix1 工作者结果写成了 failed）。
- 审核结论：B29 FIX、B30 FIX、quant-015 FIX、quant-017 FIX、I03 FIX。
- 升为待核：无（只出草稿）；推送时 origin/main 第 1 轮待核 14 条（原记录的 15 是按过期工作区计的，已更正）。

## 2026-10-21 第 1 轮名额调整：quant-026 升待核

- 背景：origin/main 上第 1 轮待核为 14 条（cap 15），空出 1 个名额。
- 先查了开放 PR：#15（quant-014 回测）、#16（005/009 降草稿）、#17（quant-010 回测），都不是升待核的 PR，所以按下面的理由自己升一条。
- 选择方法：只读复核（OpenCode deepseek-v4.1-flash，最大思考）把 15 条草稿逐条按 GUIDE §2 七条门槛打分（0–10），日志在调度器 `logs/promote-r1/rank.log`。
- 排名前五：026 5.0、025 4.0、030 3.5、031 3.0、017 3.0。004/024/013/006/003/011/027/022/023/008 都是自报 FAIL、已放弃或不显著。复核员认为没有一条够“收录”。
- quant-026：机制清楚，免费免密钥数据，320/320 结算复算，23 笔扣费后回放为正，出处齐全，无重复，复核已修正过。门槛 5 不确定、门槛 6 不满足（历史只有 8 个周独立结果），预期结局是待选区（1 分）。和 quant-015 先例一样，空着名额只能得 0 分。
- 改动：`status` 改 `待核`（`date` 仍为 2026-10-20，属第 1 轮），在顶部整理说明里写明预期待选区。没有新增或修改任何数据、数字或结论。
- 名额：升完后第 1 轮待核 15/15（按 check.py 的 round_of 计）。若 PR #16（005/009 降草稿）合并，会再空出 2 个名额。
- 新增或修改的文件：entries/quant-026、INDEX.md、LOG.md
- 查了多少个来源：0（只用仓库内已有条目、复核和核查记录）
