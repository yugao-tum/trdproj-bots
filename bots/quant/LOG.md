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
