# 2026-10-19 七小时研究计划

下文是 OpenCode DeepSeek V4.1 Flash Free/max 实际交付的执行计划。仅为计划，候选尚未成为已验证策略。

**执行计划（仅计划；未访问来源、未回测、无收益数字）**

15:35–22:33:15 UTC。只写 `bots/dot`；不交易、不登录、不用密钥、不付费；所有候选、数据和收益均待实测。20 个批次槽位不代表 7 小时内跑满，宁可少交也不凑数。

**时间表**
- 15:35–15:50：pull；读 scoreboard、reviews、各 claims/index/log、known；跑 stats/dupes。
- 15:50–16:10：建目录、首批 20 条认领并推送、公开数据探针。
- 16:10–17:10 B01；17:10–17:25 初筛。
- 17:25–18:25 B02；18:25–18:40 初筛。
- 18:40–19:40 B03；19:40–19:55 初筛。
- 19:55–20:55 B04；20:55–21:10 初筛。
- 21:10–21:50 B05，仅绿色模式；21:50 冻结检索。
- 21:50–22:20 审计、lint、条目、提交；22:20–22:33 缓冲。每小时 :35 反馈卡。

**10 worker（互斥、只读检索，主规划唯一写仓库）**
W1 天气；W2 宏观数据；W3 政治/官方结果；W4 体育规则与阵容；W5 文化/科技/提及；W6 PM 结构：重复、阶梯、完整集；W7 PM 跨平台与奖励；W8 PM 行为/期限/成交流；W9 加密资金费/基差/借贷；W10 加密期权/事件/再平衡。每批每人约 2 个机制，跨域线索交主规划。

**首批 20 机制（假设，关键词为检索种子）**
1 天气结算滞后：`polymarket weather resolution lag`；2 天气预报模型：`GFS ECMWF prediction market`；3 宏观 nowcast：`CPI nowcast polymarket`；4 官宣未结算：`election called settlement lag`；5 重复上市：`polymarket duplicate market`；6 完整集套利：`negative risk arbitrage polymarket`；7 阶梯/单调性：`ladder arbitrage prediction market`；8 跨平台：`polymarket kalshi arbitrage`；9 冷门高估：`favorite longshot prediction market`；10 截止日衰减：`deadline effect binary market`；11 新闻过度反应：`prediction market overreaction`；12 体育结算规则：`overtime push settlement sports market`；13 伤病/首发滞后：`lineup news prediction market`；14 票房/奖项实际值：`box office prediction market`；15 民调模型：`polling average election market`；16 成交流不平衡：`polymarket order flow`；17 新市场漂移：`new market underpricing`；18 PM 加密 vs 期权：`bitcoin binary options implied probability`；19 资金费 carry：`funding rate arbitrage delta neutral`；20 期货基差：`crypto futures basis cash carry`。

**查重/认领**
每批先 pull，读榜、评价、全部 claims/index/log 最近 20 行、known；`grep -ril` + `check.py dupes`。同付款人+同关键变量=重复；只换币/市场/参数=变体，交 supplement；明显更优交 improvement。认领先推送再开工；冲突即放弃并记 LOG。15 条待核账本，其余草稿/notes；只有过门槛且 lint 通过才标待核，优先 PM（1.3）。

**真实回测**
数据探针记录 URL、访问时间、无密钥、覆盖期、时区、哈希；原始数据放 `/tmp`，不入库。PM 用 Gamma/CLOB/data-api+官方结算源；历史盘口不可得则只做 forward。加密至少 12 个月；PM 至少 30 个独立事件，同事件/同源多市场算 1。5000 总资金、单场所 2500、无杠杆。加密每边 0.3%+资金费+滑点，2 倍成本压力；PM 按 `份数×费率×p(1-p)`+半价差+资金占用天数。预注册进出场、样本切分与失败线；按时间 60/20/20 或 walk-forward，发布时点、禁未来修订、事件聚类、多重检验。否证：成本翻倍、剔除最大事件、安慰剂、子期稳定性；净收益≤0、OOS 翻负、<30 独立、集中度过高、规则源不明、容量不足即失败。

**批次状态机**
S0 排队→S1 已认领→S2 收集中→S3 去重满 20→S4 数据就绪→S5 快测→S6 OOS 深检→S7 条目→S8 关闭；收集、测试、写作各限 1 批并行。不足 20 个不同机制就并批，不用变体补位。B01–B20 为槽位，7 小时现实推进 4–5 批。

**降载/恢复**
绿 10 人；黄 7–8 人停新批；红 4–6 人只验证；黑收尾。429 即停、退避、缓存、换免费源，不绕限；数据缺失换官方源或转 forward，仍无则 blocked/notes；worker 失败重试 2 次再分配，检查点续跑；模型/网络故障时主规划接管关键验证。协调者负责 git pull/rebase/push、`check.py`、长回测、打开公开页面/GitHub/X、确认认领时间、重启 worker；无 Git 权限则提交“路径+全文+说明”。

## 调度与质量修正
- 10个独立DeepSeek会话已实测同时进入推理，免费调用成本记录为0；该结果不是服务并发上限承诺。
- 主规划首次因32000推理token上限无最终文本，精简继续提示后成功交付；未调低max。
- 子计划中出现的0.6%往返表述仅适用于单腿；两腿策略必须逐腿计费，不能遗漏四次执行。Polymarket使用当前真实费率，不能机械套0.3%。
- 首批20个认领是候选假设，结算信息滞后等跨板块重复必须合并；没有20个真正不同机制就不计作满批。
- 主项目正式回测与独立研究初筛分开；本次无权宣称通过主项目关卡。
- 原始数据及本次独立回测明细保留在本地，不上传仓库。
