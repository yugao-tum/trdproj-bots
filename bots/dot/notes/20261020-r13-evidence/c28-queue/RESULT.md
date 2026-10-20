# C28 r13：真实生命周期获取遇到明确屏障

结论：未完成真实 request→finalization→claim 闭环。主网队列地址由 Lido 当前官方文档链接确认为 `0x889edC2eDab5f40e902b864aD4d7AdE8E412F9B1`，但选定 claim 交易正文首次读取返回 HTTP 403 Forbidden，已停止该来源，没有重复请求或改换路由。请求 ID、锁入金额/份额、owner 变更、请求与到账时间、finalization checkpoint/rate、gas 和利润均留空，不能把搜索索引命中当交易证据。草稿保持，不新增机制、回测或达标。

## 已核实的新发现

- 官方文档当前链接 core v4.1.0 源码。`WithdrawalQueueBase.sol` 的 `_finalize` 发出 `from = lastFinalizedRequestId + 1`，所以该版本事件范围是闭区间 `[from,to]`；文档概述写 `(from,to]`，两者有差异。重建时必须绑定历史实现，不能据当前文档漏掉首个 request。当前源码不是选定历史交易的实现证明。
- `WithdrawalsFinalized` 事件只有区间、批次 ETH locked、shares burned、timestamp，不直接带 checkpoint.maxShareRate。不能把批次平均 ETH/shares 当每个请求的 checkpoint rate；需历史 calldata/storage 或对应实现与 checkpoint 证据。
- 提现计算按 Solidity 整数分支复现：仅当 `amount*1e27//shares > maxShareRate` 才使用 `shares*maxShareRate//1e27`，否则返回锁定额。普通 min 近似可能遗漏整数边界。
- request 与 claim 的 gas 独立留列，未知不设零。二级入场价未知时，策略利润仍未知；排队时长不能替代收益。

## 屏障与后续所需证据

目标：https://etherscan.io/tx/0x97110add3bf62bd5f7c30ee5820422a6951ce2e2e99df22592d052fde3be1545

2026-10-20 08:52:09 UTC，web.open 正文返回 403。没有取得事件日志或完整收据，没有执行后续请求。该线索在观察金额或价格前选定，不是按收益择样。若未来获得合法可访问的原始事件/收据数据，应补 request 交易、区间 finalization、claim 交易、全部 NFT transfer、三段区块时间与历史实现/checkpoint；本轮不通过其他入口绕过该拒绝，也不重试 C27 v2.0.0 路由。

## 产物与测试

queue-lifecycle.json；amount-share-ETH-ledger.csv；source-manifest.json；input-verification.json；reconcile.py；test_reconcile.py。raw/ 为本地保留的官方网页与当前源码，不建议作为原始档案批量发布。

8 个合成单元测试通过，涵盖上限、haircut、整数舍入分支、gas、未知保留及 inclusive range。运行真实空缺记录返回 incomplete_real_evidence，无时长/利润数值。测试不是历史样本。仅写本角色 output，输入三个 SHA256 均匹配。

预算：1 次定向搜索；web 正文读取 2 次（官方文档成功、Etherscan 拒绝）；直接正文读取 3 次（官方文档及两个 v4.1.0 Solidity 文件），公共数据集请求 0。Python requests 模块不存在的本地尝试未发送网络请求，随后使用标准库。调用消耗金额未知。

运行来源：本助手 OpenAI native agent，精确模型标识未暴露，记 unknown；任务 1，DeepSeek/OpenCode/Pi 任务 0。
