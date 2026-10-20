---
id: dot-027
name_zh: 小资金LST质押净收益
name_en: Small-Capital LST Staking Yield
bot: dot
date: 2026-10-19
market: crypto
pm_category: -
kind: supplement
improves: Y-Y2-lst-hold
category: Y
return_type: carry
instruments: stETH, wstETH
venues: Lido（以太坊主网）、二级市场（Curve/Uniswap/CEX，未逐一核）
data: Lido APR API免费免密钥，当前2.22%（非12个月历史）；Lido docs/GitHub/Ethereum.org；现已取得固定12月恒定shares接口两端读数，完整rebase/市场汇率/gas/赎回队列路径未取得；PM不适用。
test_2w: 前向14天记录APR、stETH/ETH、wstETH汇率、gas、赎回队列；这是12个月持有的前置观察，不是完整持有期；日度rebase不算独立；30个独立结果未知；12个月主检验失败=全期按5000本金计费后纯carry低于预设门槛或无法完成退出；14天往返净carry<0仅否决短持有分支。折价>1%或负rebase作为风险警报。
status: 草稿
confidence: 中
---

## 一句话

纸面规则：用USDT/USDC买入stETH或wstETH并持有12个月，赚每日rebase/兑换率累积的质押净收益；不追求32ETH验证者，不做14天来回，退出走二级或FIFO赎回队列；不执行交易。

## 钱从哪里来

以太坊共识层发行（attestation/proposal rewards）加执行层priority fees/MEV；Lido节点运营商赚取后，扣10%协议费，按stETH rebase或wstETH汇率传给持有者。罚没/离线惩罚是负现金流，不是付款方。小持有者不是32ETH验证者，不需32ETH，也不直接出块或运维。

## 规则

标的stETH或wstETH；纸面入场先以现货取得ETH，再按Lido规则以ETH铸造stETH（名义ETH:stETH为1:1）；wstETH按当时兑换率包装，并非1:1美元或wstETH铸造，所有兑换腿和gas须计成本；二级LST折价>0.5%属C28类收敛，不是C26，不混入本条。纸面资金：2,400名义部署＋100费缓冲＋2,500场外＝5,000；单场所≤2,500；不把5,000全投Lido；无杠杆、不借款。持有固定12个月，不用6-12个月任挑；14天只作成本筛。退出：二级折价<0.5%卖出，否则FIFO赎回（min 100 wei，max 1000 stETH/请求，不可取消，汇率不高于请求时）。用net APR，不再重复扣10%；若用gross才扣一次。UTC日界，shares有1-2 wei舍入，记账用shares/wstETH。PM无腿，规则缺失。

## 证据

Lido docs：stETH每日rebase，奖励含CL rewards与MEV/EL fees并复投；协议费10%（节点运营商/treasury各半）从rebase扣；赎回FIFO；明确stToken二级可能低于内在价值、赎回限制使无风险套利不可能；罚没最多可使质押资金全损（来源自报）。Lido API 2026-10-19 12:23 UTC报APR 2.22%，chainId=1（已读JSON；来源自报，未重算）。ethereum.org：奖励按epoch发放，base_reward公式存在；孤立罚没烧小部分，相关罚没可扩至全部有效余额（已读）。GitHub摘要：Accounting处理oracle报告、rebase、协议费；5/9 quorum；Lido.sol注释区分gross与net APR。X摘要：2026-07-25 rebase少报2.04% vs 预期2.15%，后修正2.29%；2023-08周均APR 3.81%。均来源自报。未测收益：backtest_count=0，observed_net_return=null，Sharpe=null，DD=null。

## 数据

新增2026-10-19核查：[恒定份额历史账面数量](../notes/20261019-staking-share-endpoints.md)。同一10^18 shares在固定365日两端对应ETH数量的接口整数比增长2.48049172%；不是USDT收益或实际提款，也不能拆分全部奖励、捐赠和份额销毁。抽取前冻结区间，不是投资前预注册；两端合约version 2→4、历史源码等价性及完整期间路径未证，完整回测仍0。

Lido APR API `https://eth-api.lido.fi/v1/protocol/steth/apr/last` 免费免密钥，仅当前值。12个月rebase/APR、stETH/ETH二级价、wstETH汇率、gas、赎回队列未取得；GitHub摘要称有reward history API/subgraph，本worker未调用。PM无腿，不适用。

## 两周内怎么检验

计划2026-10-19至11-02每日UTC记录（尚未启动该采集）APR、stETH/ETH买卖价、wstETH.stEthPerToken、gas、赎回队列；2,400 USDT名义模拟买入并持有，不交易。这是12个月持有的前置观察，不是完整持有期；日度rebase同协议同program、高度重叠，不自动算独立；30个独立结果未知。主检验失败：12个月按5000总资金计费后纯carry低于预设组合腿3%门槛，或无法按规则退出；低相关性亦未证，不能仅收益达标就晋级。14天往返净carry<0仅否决短持有分支，不否决12个月方案。折价>1%、队列>14天、负rebase/罚没、APR<2%是预注册风险警报；费用重复扣属于实现错误，须修正账本而非策略否证。

## 成本与容量

基准往返0.60%（0.30%/边×2），压力1.20%，gas假设20-50 USDT/往返（未实测）；无杠杆。14天：3% APR→0.115%，2.22%→0.085%，均<0.60%，但只作短期carry成本筛，不证明长期不行。12个月约定：2,400名义部署、100费缓冲、2,500场外；0.60%只近似覆盖两次市场换币（入场USDT→ETH、退出ETH→USDT），按2,400名义近似14.4 USDT；staking、withdrawal、claim及包装gas另减，二级LST退出若另需兑换腿也另扣，不假定完整路径仅两腿；这是已投入本金分母的近似，不是5,000组合收益。2,500部署上限毛2.22%最多1.11%/5,000；按2,400实际毛约1.07%/5,000，扣费/gas后更低。3.6% APR在2,400上毛约1.73%/5,000，不代表组合3%达标。3%假设的gross/net口径未核，不额外扣10%。全年收益按5,000总资本、触发频率、持有/闲置时间、所有notional费用计算，未知。无盘口/成交数据，纸面容量不等于实际可成交。

## 风险

ETH/USD价格风险独立于staking carry，不能只用APR判总USDT收益；总USDT收益=carry+ETH价格变动-费用/gas。罚没/惩罚造成负rebase；合约、oracle、桥风险；FIFO队列与二级折价使急退受损；APR随质押量/MEV/费用变化，当前2.22%非保证；协议费可改、会计错误有先例；小资金gas拖累大。

## 改进了什么

本条改按 `kind: supplement`，`improves: Y-Y2-lst-hold` 归类。分类依据是 [known 中的 Y-Y2-lst-hold](https://github.com/yugao-tum/trdproj-bots/blob/bc5dd79aa7da5e07cdd3ed2d22a158ab620222fb/known/KNOWN.md#L141)（2026-10-20 UTC 核对，仅含名称，不含既有规则或绩效）。持有流动质押币收基础质押收益；shares会计核查是补充。

本条提供的研究补充：整理基础质押付款来源与恒定 shares 的固定全年两端会计读数；ETH 数量增长不等于 USDT 净收益，完整价格、gas 和退出路径仍缺。

补充材料相对既有实现的新增性与采纳价值仍待核；本次不主张新机制、已证改进、盈利或已采纳，状态保持草稿。

## 门槛自查

1. 机制说得清：满足。付款方是共识发行+执行费/MEV；罚没是负现金流；小持有者不是32ETH验证者。
2. 有免费数据能检验：不确定。当前APR及固定12月两端shares会计读数已取；完整rebase/市场汇率/gas/队列历史缺失。
3. 小资金能做：不确定。纸面2,400名义+100缓冲+2,500场外；gas占比、退出路径与可成交性未实测。
4. 不重复：同机制补充，非新策略——对应 `Y-Y2-lst-hold`；补充材料的新增性与采纳价值仍待核，不据 dot 内部区别主张全局新颖性。
5. 扣成本后粗算够用：不确定。当前低APR纯carry按12个月约定毛约1.07-1.11%/5,000，扣0.60%和gas后可能不足；但总USDT收益含ETH价格，长期全策略未测，不能只用APR判定。
6. 两周内能检验：不确定。日度rebase不独立，两周只是1个前置观察；30个独立结果未知，不硬说不可能。
7. 出处可查：满足。URL/日期/位置齐全；来源自报、摘要、未取得历史均标注。

## 出处

- https://docs.lido.fi/guides/lido-tokens-integration-guide/ — 2026-10-19 — 已读（stETH、Fees、Withdrawals、Risks）
- https://eth-api.lido.fi/v1/protocol/steth/apr/last — 2026-10-19 — 已读（JSON 2.22%）
- https://ethereum.org/en/developers/docs/consensus-mechanisms/pos/rewards-and-penalties/ — 2026-10-19 — 已读（Rewards/Penalties/Slashing）
- https://github.com/lidofinance/docs/blob/ff75aae0414ded4e9938bcd6b811aed97777fa00/docs/contracts/accounting.md — 2026-10-19 — 摘要（GitHub检索摘要）
- https://x.com/LidoFinance/status/2081077386737549616 — 2026-10-19 — 摘要（2026-07-25 rebase 2.04%）
- https://x.com/LidoFinance/status/1696425806870839412 — 2026-10-19 — 摘要（2023-08周均3.81%）

- 新增数据：2026-10-19已读官方部署/份额接口、固定历史RPC两个端点；[完整单位、原始整数与SHA说明](../notes/20261019-staking-share-endpoints.md)。单RPC提供者、历史实现匹配与提款现金链缺口均保留。
