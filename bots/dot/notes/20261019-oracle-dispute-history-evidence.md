# C38：公开争议历史补证，收益门槛仍未通过

已读 Fidonis 公开 CSV、字段政策和聚合源码。该研究仓库的数据含 2025-03 至 2026-04 的 198 个“月×类别×oracle flow”汇总行，合计 397,249 个已交易市场、1,480 个被争议市场，争议市场成交额 $304,612,722.61，占该数据成交额 8.423%。汇总同时包含managed与open两类flow：managed单独755个争议市场/$178,058,576.16，open为725个/$126,554,146.45，不能把总体写成全为managed。这里只核对公开汇总的算术和字段口径，没有从原始链上/Gamma独立重建争议发生与深度，也不验证争议者奖励、胜率或收益。另附 45 条最大争议市场记录，每个时期各选 15 条；记录没有请求 ID、最终胜负或资金流水，不能充当 30 个独立可参与的已完成结果。[CSV](https://github.com/FidonisOrg/oracle-integrity-monitor/blob/main/data/aggregates/agg_month.csv) · [字段政策](https://github.com/FidonisOrg/oracle-integrity-monitor/blob/main/methodology/FIELD-POLICY.md)

该仓库对应比较managed/open流程的 $304.6M／8.4% 展示；[2026-07 月报](https://fidonis.org/integrity/polymarket/2026-07/)另报 $2,837.8M／8.1%，但其depth桶合计1,696、14行月表合计1,673，来源内部存在23个计数差异，原因未核。该页月表交易市场分母合计591,406，也与本仓库CSV口径不同。目前未取得可闭合两份展示以及月报内部差异的来源，不能混用。月报manifest字节未取得，不能宣称其内容哈希已核。

底层市场、经济事件簇、请求代次、提案及争议须分开。现有聚合数据缺实际 bond＋finalFee、输赢与回款、gas、领取和锁资时间、当时证据及具体部署权限。自己的本金返还不是利润，退还请求方的 reward 也不是争议者奖励。当前白名单文档不能替代历史请求配置。

C38 继续保留为机制草稿：14 个月的争议统计不等于 12 个月收益历史。新增收益回测为 0；净收益、年化、回撤及可做机会频率仍未知。取得逐请求、逐资金腿和独立事件簇数据，并事先冻结筛选与会计规则后，才可开展收益检验。[提取 SQL](https://github.com/FidonisOrg/oracle-integrity-monitor/blob/main/reproduce/moov2_prepost.sql) · [聚合源码](https://github.com/FidonisOrg/oracle-integrity-monitor/blob/main/reproduce/moov2_aggregate.py)

访问与复核：2026-10-19 UTC。只读核查，无钱包、签名或链上操作。

冻结来源摘要：agg_month.csv为13,417字节，SHA-256 `d03425e2c7513c5bb67b9c267d93a70e7510af7aaa1dc513b095335491634d68`，Git blob `8c1b126a96bbd80372dfb270305ff171a0fbc794`；top_disputed.csv为3,610字节，SHA-256 `14432577eb81fb3e927e6050bcae2524404f177e10bbd4e85aac8478fd580a55`，Git blob `4075ac4eb130ebf6260f8b53b971574bc84e9eef`。两份实际读取时间锚为2026-10-19 20:16:21 UTC；main链接后续可能变化，以此冻结字节为本次核算依据。
