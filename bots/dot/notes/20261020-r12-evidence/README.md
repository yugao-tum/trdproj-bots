# 既有证据补充与离线契约验证（2026-10-20）

本次只给既有 C01、C21—C24、C27、C34、C37、C38、C39、C45、C46、C49 补证。没有新增策略机制、真实收益回测、独立策略结果、待核提交或达标成果；41 篇 entry、7 条待核不变。原 entry、冻结规则、原始结果和此前日志均未覆盖。

## C38：五份源码绑定同一版本

[c38-source-binding.json](c38-source-binding.json) 记录共同 commit 62644bbbd6750ebcb20048b5082c195276d1d31c、真实 tree 37e058646d8ad38f34eaf4b94290c0e741e99381，以及 schema、mapping、helper、mainnet、polygon 五份正文的 Git blob/SHA-256。五份保留正文重算 Git blob 后均与树匹配。来源：[UMAprotocol/subgraphs 固定提交](https://github.com/UMAprotocol/subgraphs/commit/62644bbbd6750ebcb20048b5082c195276d1d31c)，2026-10-20 已读；文件定位见清单。此次 4 次只读获取。

这关闭了源码共同版本的缺口，不证明历史部署、query rows、完整争议现金链或 PnL。README 版本标签与 deploy 脚本没有给出已核实的部署内容 ID，不能把源码版本冒充数据运行版本。

## C45：已读两份官方 SQL，不是已取得收益数据

[c45-sql-source-manifest.json](c45-sql-source-manifest.json) 给出固定 commit dd51f6190adb6cf95a0bc4d769c106bb698916d4、两个完整文件URL、9,435 字节及重算匹配的 blob/SHA-256。2026-10-20 已读，4 次只读获取；不在仓库重复上传原始响应或 SQL。

- daily-staking-rewards-per-pool.sql L3—12 读取 query_4067736 的 expected reward，L27—46 按保障期与每日重叠秒数摊分。它不是用户领取交易，不能把 reward_total 当个人净收益。金额单位、上游费用、时区与领取账本仍缺。
- staking-deposits-with-burns.sql 读取 origins_chain 与 query_5734582；origin 主键含 pool_id、token_id、origin_tx_hash、origin_evt_index，依 block_time/evt_index 排序。pool-wide burn 按有效余额摊分，burn_delta 与 withdraw_amount 的加法依赖上游负号约定。生成的 synthetic burn row 不是新链上事件。
- 未执行查询，历史结果行 0。固定上游查询、365 天完整流、凭据所有权、实际奖励/经理费、退出及同刻兑换成本仍缺。G2/G5 不因此通过。

## C01：时区/DST参考实现

在 c01-timezone 目录运行 `python -B -m unittest -v test_normalize`。只依赖 Python 标准库与系统 IANA 时区数据库。25 个 synthetic 场景和3个证据输入检查通过，实际测试是2个 unittest 方法；不把25场景说成25个真实观测。

实现保留回拨的两个 UTC 候选，春季不存在钟面拒绝；无 offset 且缺解析上下文不擅自加 Z。UTC日与站点日分列，任何输入断言都不把 actual_viewer_proven 变为 true。

依据为留存 NOAA [obs.js](https://www.weather.gov/source/wrh/timeseries/obs.js?v202610192130) 摘录：L363—368 的 date_time、STATION[0].TIMEZONE 和 moment(raw).tz(TIMEZONE)，L2481—2485 的图表时区设置。源码摘录此前已读，本次未重新联网核验。新参考实现不是原网页差分复现。

仍缺当次 KLGA TIMEZONE/载荷身份、原时间串及浏览器解析上下文、实际加载脚本绑定、moment/moment-timezone 精确版本。America/New_York 仅是测试输入，不补齐真实观测元数据；更不补齐历史决策时点信息集或最终结算。

## C46：偿还关联器与误配负例

在 c46-repayment 目录运行 `python -B test_matcher.py`。21 个 synthetic 测试通过；源码与 [SCHEMA.md](c46-repayment/SCHEMA.md) 明确 normalized evidence contract，不解码 ABI、不验证 Merkle proof、不提供 finality oracle。

链/币/decimals/bundle/leaf/address 必须精确匹配；仅显式组成分配与已到账证据断言一致才 matched。deposit refund 不因共用退款事件而变成 relayer repayment；deferred 不当现金，重复执行不重复入账，聚合无法分解时 unknown/unallocated。matched 只表示输入断言一致，不表示真实链上证据已认证。真实闭环样本0，不计算 PnL。

[source-map.json](c46-repayment/source-map.json) 给出留存原文定位：SpokePool 固定 commit 555475cdee6109afc85065ca415c740d7f97b992；UMIP-179 为旧 master 摘录，未固定版本，不冒称当前部署。此任务无新网络请求。

## 既有短窗8情景便携复现

[short-window-replay-record.json](short-window-replay-record.json) 记录实际本地验证：9份确定性输出逐字节一致，DATA-QUALITY 仅两项机器路径另列、其余字段一致；13项最终测试通过，139项原始输入完整性检查不变。最初1个加载器测试失败修复后全量重跑，未隐瞒首次失败。

包移动后在禁止网络与原输入路径读取的 Python audit hook 下重放成功。仅是这次运行的可移动性证据，不是安全沙箱保证。含54份ZIP/CHECKSUM和原始warmup的完整包按 GUIDE 不上传；本仓库仅发布记录和包哈希，不声称本提交提供可直接下载的完整新重放包。原先公开复现范围不据此改写。

## C39/C49未关闭的缺口

C39 1次搜索、4次读取后仍未取得可验证的 Votium 原始 epoch 分配文件、资格或票权分母；当前正文与旧缓存 Convex/Snapshot 表述不能混作单轮规则。C49 2次查询、4次读取未取得服务费到 reward submission、root、持有人claim 的关联证据，X原帖403后停止。未查到不等于机制不存在，不计新增有效来源/收益。

所有统计仅为本次明确范围。原始行情、HTTP响应、账户信息、模型原始推理不入仓库。

## C34：小时CSV明确是重构模板，不能补原始逐时行情

作者 DATA_DOCUMENTATION.md L32/L42 明示 06 为重构模板而非原始观测；L125 说明中间小时价格由几何布朗运动并约束端点构造，端点依文件01聚合收益。该新证据不能用于原52事件的独立真实行情复验，也不能凭文档“Actual UTC”声明补齐链上解锁时刻。

[c34-hourly-template-binding.json](c34-hourly-template-binding.json) 固定文档 blob eba0b6d52e2322f48d2000b926083c655464eaee、CSV blob 5fcd4fa2f3291feb8f435d91eabb3093b2ea7f00 与树 cd55c0383b35b2864e3c9f02d5f641e2fbf84926。整份返回字节的 Git blob 重新计算匹配；未绑定根commit，不能把树SHA写成commit。

2026-10-20 已读文档全文、CSV表头和52个offset0/52个−24h行。补证汇编又从留存完整CSV解析确认5,044行及这两组各52行，但未逐行验证经济真值。offset0均为午夜、−24h归一化为100，与结构构造一致而非链上时刻或原始价证明。06无BTC列；BTC网格、真实价格类型及逐行源仍缺。目录包含src代码，但正文未读/未执行。只按作者声明记录，不推断意图或指控造假。旧52行审计及冻结结果不覆盖；原始CSV不上传。

## C27：末端地址到官方部署清单的绑定

[c27-end-deployment-binding.json](c27-end-deployment-binding.json) 保留官方 v4.0.1 部署清单的精确来源哈希和app:lido对象；其implementation.address与留存末端block 26093737的0x028271…cDb0一致，清单deployCommit指向 e45c4d6fb8120fd29426b8d969c19d8a798ca974。对应Lido.sol仅工具可见前段正文，不能由版本名推定source=version4、runtime bytecode等价或编译复现。

起点block 23479243的0x171445…17eb虽在v4清单历史参数出现，仍不足以绑定起点部署。旧v2路径读取被拒后停止，不通过换路重试。起点官方版本/源码、两端code hash与运行字节码仍缺；原shares条件比例不重算、不升级为USD收益。来源：[部署清单](https://raw.githubusercontent.com/lidofinance/core/v4.0.1/deployed-mainnet.json)与[deployCommit源码](https://raw.githubusercontent.com/lidofinance/core/e45c4d6fb8120fd29426b8d969c19d8a798ca974/contracts/0.4.24/Lido.sol)，2026-10-20已读，清单/源码工具可见文本存在截断，清单完整返回另作哈希保存。

## C37：12笔融资归属全部仍unknown

仅根据留存受限payload与Aave [IPool.sol接口](https://github.com/aave-dao/aave-v3-origin/blob/main/src/contracts/interfaces/IPool.sol)正文（2026-10-20已读，未固定commit），不能把成功清算、ERC20流出或没看到FlashLoan当成自有资金证明。12/12分类unknown，own-funds=0、borrowed-or-flashloan=0不是零融资频率，而是两类均无足够归属证据。

tx1部分事件组只给首尾payload，其余交易也未提供完整有序logs、付款方trace/prestate；候选topic0签名哈希绑定及Balancer事件解码缺失。没有新RPC、代码运行或收益重算，不推定原12笔适合无借贷5000 USDT约束。

## 本轮实际执行口径

十项独立研究任务全部有终态：OpenCode Go / deepseek-v4.1-flash / max 三项，dot native七项；不是Pi或免费通道任务。模型步骤数不算独立任务数。三项Go均finish=stop，产物仍证据草稿；七项native包含实际离线测试和有界来源检查。10项完成不等于10个新机制或10份有效收益证据。最终仍0新增机制、0新增真实收益回测、0新增独立结果/待核/采纳/达标。
