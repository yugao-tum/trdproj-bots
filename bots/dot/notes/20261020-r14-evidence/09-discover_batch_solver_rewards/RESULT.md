# r14 native09: CoW batch solver 初筛止损

访问日期：2026-10-20，09:35 UTC。阶段：负面初筛 / 草稿，非回测、非条件模拟、非达标。新认领0；新增独立机制0；真实付款样本0；真实收益计算0。native OpenAI任务1，运行时精确模型ID未暴露；OpenCode/Pi/meiying调用0。

## 决策
停止当前 CoW 候选，不建议新增entry或认领。官方规则已证明：自建独立池所需美元部分是单场所2500上限的200倍；即使reduced pool，其最低美元部分也是20倍，另需COW代币。DAO代担保路线不能等同无许可小资金机会，仍需公司/股东身份材料、KYC和白名单。未扩大搜索为其他协议，不泛化为所有batch auction均不可行。

## 已读证据
1. 官方 [bonding pools](https://docs.cow.fi/cow-protocol/reference/core/auctions/bonding-pools)：正文“Setting up a bonding pool”要求500,000 USD及1,500,000 COW；reduced段要求先获团队批准、50,000 USD/ETH及500,000 COW起，后续逐步增资。其准入直接不符合当前资本界限。
2. 官方 [onboarding](https://docs.cow.fi/cow-protocol/tutorials/solvers/onboard)：§1、§4、§5说明DAO池KYC、公司股东材料及白名单路径；§1服务费为入池六个月后周COW奖励的15%；§4还列周奖励25%锁定。奖励不是净现金回报。
3. 官方 [solver-rewards](https://github.com/cowprotocol/solver-rewards)：README提供周会计及付款核对代码，但运行说明依赖Dune/orderbook凭据；本任务未运行、未申请密钥。只有代码存在，不是已执行付款凭据。未取得auctionID—收款币种/数量—时间—实际转账—成本的闭环行。

## 机制边界与查重
候选定义是为批量订单竞争性求解/结算服务获得协议奖励，不是C46垫资跨链快速填单，不是C29 AMM流动性费；与known A-A5-onchain-mev共享执行生态，仍需正式查重认定，不能仅凭名称宣称新机制。已读准备快照known135及dot/muse/quant claims；该快照head为e068c98ad3f5a9aa7834e55ac2ef6caf210b7dd9，未声称完成当前main查重。因资格失败，没有请求新认领或深入回测。

## 七门槛
| 门槛 | 判定 | 依据 |
|---|---|---|
| 机制说得清 | 部分 | 求解服务奖励口径存在，但未构造可执行盈利规则 |
| 免费收益数据 | 未过 | 无真实付款行，无12个月公开免密数据集 |
| 小资金能做 | 未过/止损 | 自有池资本超限；DAO路线受许可及KYC约束 |
| 不重复 | 未定 | 与C46/C29概念可区分，known MEV交叉尚未正式认定 |
| 扣成本够用 | 未过 | 未得净成本及奖励账本；不能用预算或补贴代利润 |
| 两周可检验 | 未过 | 30个独立结果及无许可执行路径均未建立 |
| 出处可查 | 部分 | 上述三官方正文已读；无真实付款出处 |

## 搜索与停止原因
完成2次GitHub定向搜索、2次X定向搜索及3次官方文档定向搜索。X无可核正文，不计X证据。正文页读取4个不同URL（GitHub仓库、文档入口、onboarding、bonding pools），没有超过6正文预算。09:35:46 UTC确认小资金/无许可准入失败后，停止外部搜索，早于父级15分钟无付款止损上限。未遇403/429，未进行绕行、交易、钱包连接、任何账户/密钥使用。

## 建议entry补丁
不建新entry、不改任何旧entry状态；只可将本负面初筛作为r14 note登记。只有未来出现公开、无许可且符合2500资本约束的真实服务付款样本，才值得重新提案，由父级先读最新known/all claims再认领。
