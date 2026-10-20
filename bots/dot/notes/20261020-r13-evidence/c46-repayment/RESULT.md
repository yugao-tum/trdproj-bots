# continuation-r13-05 · C46 真实返款链尝试

结论：未闭合。真实返款闭环仍 0；没有新增机制、回测、条件模拟或达标结果。保留草稿/未知，不将未取得回执解释为未付款或坏账。

已核 11/11 输入哈希不变，读过最新 main e068c98ad3f5a9aa7834e55ac2ef6caf210b7dd9 的 known 和全部 claims 快照。本轮不是新策略，目标是 C46 单笔证据链。

## 完成的实质工作

从 https://docs.across.to/api-reference/deposits/get 的官方响应示例冻结 2025-05-05 OP→Polygon、depositId 2996407。此示例在 r03 已读过，本轮新增的是尝试独立核其两个交易，而非重新发现机制。完整哈希及带来源等级字段留在 candidate-lead.json，不编造 chain receipt。

独立读取源交易 https://optimistic.etherscan.io/tx/0x8a0e23bcdc4c5789b027e94f762e195321969bbecd480f0e5ccc1e821677c4c4 和填单 https://polygonscan.com/tx/0xd5320ce6837a0f37643284af60ee99fb41a9ee4907ac6fbc19ffe654555f81d3 均返回“not accessible via this tool”，未提供 HTTP 状态。立即停止这些目标，没有换通道重试。官方 overview 的另一个 bundle 提案示例返回 Cache miss；该提案即使可读也未证明属于选定 fill。

## 精确缺环与 matcher

缺 independently verified deposit/fill 完整日志、repayment chain/token/decimals/address、bundle/leaf 与每笔分量分配、真实现金 transfer（或 deferred claim 到 leaf 的证明）。depositRefund 字段不能代替 relayer repayment；fill 状态不能代替到账。

保持 r12 matcher 原文与语义，实际执行了一次空证据输入。输出 results=[]、observed_sample=false、pnl_computed=false。由于没有可独立认证的 allocation，未向 matcher 塞入虚构 ID/金额来强行产生 unknown 行；空结果是“尚不可评估”，不是通过。cash-ledger.csv 仅表头，不表示真实现金为零。

下一步必须取得该冻结样本可获准读取的独立回执来源及完整 bundle 分解，才有真实样本可匹配；不建议重复请求已不可访问目标。不需要交易、钱包或任何凭据。

## 交付与计数

必需五件交付齐全：actual-evidence-manifest.json、actual-match-input.json、matcher-result.json、cash-ledger.csv、RESULT.md。另有输入完整性校验、候选、逐源结果及离线可复现构建脚本。docs-deposit-body.txt 是本地留存正文，不建议发布原文；父级可仅合批发布清单、结果及适当代码。脚本生成时间可变化，不影响 matcher 核心结果。

运行方：OpenAI native；具体模型 ID 未由可核 runtime 字段提供，记 unknown，不认作 DeepSeek。外部模型 0、费用 unknown。公开检索 2 个 query；source body 请求 6 次（3 成功，含同一文档为本地留存再次读取；3 失败）；真实 API/RPC 请求 0，交易/凭据读写 0。完整 request 结果在 manifest；未新增 X 查询，避免无关检索冒充证据。
