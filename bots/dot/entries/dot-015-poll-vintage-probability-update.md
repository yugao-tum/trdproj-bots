---
id: dot-015
name_zh: 民调发布批次概率更新
name_en: Poll-Vintage Probability Update
bot: dot
date: 2026-10-19
market: polymarket
pm_category: politics
kind: new
improves: -
category: S
return_type: direction
instruments: 同一选举race的获胜者二元合同；民调首次公开后的概率更新
venues: Polymarket global；仅研究
data: The Economist公开README与Stan模型；2008–2020方法资料可读，poll首次发布时间、胜率映射与PM历史可成交报价未闭合
test_2w: 两周核poll发布时点和选举合同映射，按race及共同选举冲击聚类；需30独立完整结果，缺发布时间、模型映射或费后优势非正即不晋级
status: 草稿
confidence: 中
---

## 一句话

用真实公开可得的民调发布批次更新选举概率，仅当同一合同的模型胜率相对可成交报价的保守优势超过全部成本与模型误差缓冲时纸面买入对应一侧。

## 钱从哪里来

假说：市场对新调查信息、调查机构偏差与调查对象差异调整不充分，准确映射胜率的一方从错误报价者取得收益。核心变量是民调抽样与发布时间，不是 dot-009 的历史价格分桶校准；没有保证收益的合同付款机制。

## 规则

- 每个输入须保存调查实施起止日、首次公开日时、抓取时、样本量、pollster、调查模式与adult/LV/RV人群。调查结束日、PDF生成时间和Stan日期索引均不自动等于公众可得时刻。
- 来源模型含州/全国信息、pollster、mode和population效应；population类别不是完整结构化turnout模型。须先核清份额尺度的predicted_score如何转为具体合同胜率，不能直接把民调得票份额当获胜概率。
- 拟定吃单规则用YES或NO自身实际ask；模型对应概率减ask须覆盖每份费用、滑点和预先冻结的误差缓冲。下一同race民调发布或最多7个UTC日先到者，按可成交bid退出；这只是未执行研究草案。
- 总资本5,000 USDT等值、单场所含费约2,500，单race初拟500等值名义。相关州与同选举多合约合并风险预算，不借款。
- 市场规则必须逐项核指定权威结果源、日期/时区、获胜者定义、重计票与缺数据处理；模型的总统选举方法不得直接迁移参院race。2–3个符合相同模板的PM合同链接、完整规则与feeSchedule尚未核实，本条不能视为可执行信号。

## 证据

- The Economist README“File dictionary”和Stan正文支持动态分层模型及模式/人群调整；Stan直接输出predicted_score，当前保存核读未闭合2020 R层的胜率映射。
- README的2008、2012、2016模型表现均是“来源自报，未核实”；它们不是PM交易收益，也未包含本条的市场费用和历史执行。
- 已读Marist宾州2024选举发布页，页面日期2024-06-12，调查为6月3–6日，说明调查结束日至公开页日期相差6天；未核小时级首次挂网时刻，PDF生成日期也不能替代公开时刻。
- 本研究未运行模型或回测，净收益、年化、最大回撤与真实月机会数未知/null。多数选举结果线索只有结果，没有联合发布时间/盘口；不能据州数宣称30独立。

## 数据

- https://github.com/TheEconomist/us-potus-model 为公开免密钥方法库；重点为README及scripts/model/poll_model_2020.stan；保存目录树SHA为b89e602ec03e81c797c66cf2743af6fdae4aa526，非本稿新下载。
- 民调发布页示例见出处；还需逐pollster证明首次公开时间，最终修订版本不可回填。PM端需Gamma规则/结算和CLOB触价记录；免费历史盘口覆盖未取得，起始可检验日期未知。
- 没有把2020方法库当作2026实时模型，也没有开始前向采集。

## 两周内怎么检验

先固定模型版本、份额到胜率映射、发布日期定义、训练/留出与信号阈值；按同一race归并重复民调，按共同选举周期冲击检查相关性。再联合当时可见盘口及最终合同结果计净额。目标30独立完成结果，当前未取得；两周能否完成此联合样本未知。发布时间、规则或胜率映射不可核即剔除并记录，样本不足单列；费用后期望下界不为正或校准留出失败则不晋级。

## 成本与容量

吃单每腿用该历史市场feeSchedule与C×feeRate×p×(1−p)；实际touch价已含价差，若以mid作诊断则另加半价差，不能重复扣。到期与提前退出分别记现金，固定5,000分母与持仓天数同时报告。500等值为草案容量上限而非实测；月内民调次数不等于独立盈利机会，相关选举暴露、深度与资金占用尚未验证。

## 风险

民调发布时间前视、最终修订污染、调查误差相关、投票率模型错配、州胜率与全国获胜条件混淆、盘口抢跑和制度性结算差异。过去拟合良好不保证新周期校准；平台、稳定币与争议锁资风险须保留。

## 改进了什么

不适用（kind为new）。C15已在第二批收集；新增正式文稿不新增机制，重复民调或换州不新增策略。

## 门槛自查

1. 机制说得清：满足描述要求；公开民调信息调整不足假说，持续收益未证
2. 有免费数据能检验：不满足；模型资料可读，但发布时间、胜率映射与历史触价未齐
3. 小资金能做：不确定；预算框架有，深度、相关暴露和占资未证
4. 不重复：满足初步分类；民调vintage变量不同于价格桶校准，换race仍是同机制
5. 扣成本后粗算够用：不满足证据要求；无本条费后收益，不能借用其他机制结果
6. 两周内能检验：不满足；30独立联合结果及可执行采集方案未闭合
7. 出处可查：方法出处满足；合同、PIT发布时间与执行数据仍缺

## 出处

- https://github.com/TheEconomist/us-potus-model — 访问2026-10-19 UTC — 已读保存README；定位File dictionary、Model performance，模型表现为来源自报未核实
- https://github.com/TheEconomist/us-potus-model/blob/master/scripts/model/poll_model_2020.stan — 访问2026-10-19 UTC — 已读保存正文；定位data中的day_state/day_national、poll_mode/pop，model的binomial_logit及generated quantities的predicted_score；只读未执行
- https://maristpoll.marist.edu/polls/the-2024-elections-in-pennsylvania/ — 访问2026-10-19 UTC — 已读保存正文；定位页面2024-06-12日期及interviews June 3–6, 2024，未验证小时级发布时间
- https://docs.polymarket.com/trading/fees — 访问2026-10-19 UTC — 已读保存正文；定位Fee Structure，历史仍须逐市场回源
- [第二批初验](../notes/20261019-batch02-initial-screen.md) — 记录2026-10-19 UTC — 已读；定位C15的发布时间、映射与样本缺口
