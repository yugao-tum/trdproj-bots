# 非VM来源充分性补证

## 已有C29 / M-M2-amm-lp：池余额不可识别手续费


实际重读 95,297 行、2020-05-18 至 2024-04-10 的 USDC/USDT 池余额快照，供给不变的相邻区间有 82,608 段，但 100-block 采样不识别区间内动作。脚本用精确 Fraction 构造两个期末余额/供给完全相同的路径：双向含费 swap 与零 swap 的 donation（如是 reserves 再 sync），费用不同。这支持“这些观测不能唯一识别 swap fee”，不声称真实样本发生 donation，更不等于所有真实费用为零。

真实快照缺账户 LP 持仓、事件序列、取得/赎回成本与 gas，不能给出账户可兑现净收益。q 起终增长约 30.50% 不能写成 fee 收益率。此项是已知 AMM-LP/C29 数据充分性的有价值负面证据，非新机制、非真实费收益回测。与 VM 的 dot-050 分开归档，不混作其收益结果。


来源为既有r16 GitHub冻结样本，原始CSV不再上传；参考[原来源注册](../20261020-r16-evidence/07-github-data/output/source-registry.json)，访问/实际读取记录2026-10-20。07脚本与精确Fraction反例仅是可识别性证明，不是真实费用估算。

## CoW：单笔真实第三方索引样本


CoW 官方公共 API 3 次 GET 200，auction 14064708 → 固定结算交易 → 单个 fulfilled order → 单笔 trade，9 项连接检查通过，block 26233215 / log 282。新 executedFee 非零而废弃 executedFeeAmount 为零；3 组 protocol fee 另有 token 单位，不能机械相加或重复扣总费。gasCost 是分摊估计而非 receipt 实际 gas。只有 2026-10-20 的一笔记录，creationDate 不是成交时刻。

这是真实第三方成交的索引样本，不是我们账户成交，也不是完整现金链、12 月收益或盈利机制；完整现金链 0。旧 solver 资本/准入否决不恢复。原始 JSON 本地保留，不由本角色断言再分发许可；已发布的小脚本依赖本地样本，不能冒称仓库数据自包含复现。


数据源为CoW官方mainnet API，2026-10-20读取；[官方API文档](https://docs.cow.fi/cow-protocol/integrate/api)。仅字段结构研究，不认领solver或新盈利机制。08验证脚本需本地原始JSON（本仓不含），不得宣称自包含复现。
