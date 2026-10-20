# C38 真实结算事件获取：身份入口拒绝，现金生命周期未取得

2026-10-20 UTC。先读 main e068c98ad3f5a9aa7834e55ac2ef6caf210b7dd9 的 known135 与 dot/muse/quant claims 快照，并验证 10/10 输入 SHA-256。仅补现有 C38，不新增机制。

按保留 top_disputed.csv 原顺序，先冻结首行“Will Zelenskyy wear a suit before July?”，标注 pre / 2025-06 / open / depth=5；选择未使用现金结果。这个聚合行本身不是一笔可唯一识别的已结算争议，depth=5 也不等于五笔已读取链上事件。

尝试公开 Gamma 市场只读接口 https://gamma-api.polymarket.com/markets?slug=will-zelenskyy-wear-a-suit-before-july ，实际 HTTP 403，响应 error code: 1010，时间及正文哈希见 acquisition-log.json。停止该来源，未重试、未更换线路、未访问私有接口。响应头未保留，所以 Retry-After 未知，不声称已获重试许可。此前 Python requests 模块缺失只发生在网络调用前，改用标准库；不是拒绝后的绕行。

精确缺证：市场至 condition/requester/adapter 的身份映射；原始 identifier、request timestamp、ancillary bytes/hash；当时 oracle 合约与实现；propose/dispute/settle 的 block/hash/tx/logIndex；currency/decimals、原始 bond/finalFee、赢家 payout 与 ERC20 transfer、双方退款/手续费/gas。旧共同源码 commit 62644bbbd6750ebcb20048b5082c195276d1d31c 仍不构成部署或历史交易绑定。

因此 dispute-event-ledger.csv 只有字段头，零真实事件，绝不用空缺填零或伪造账本。payout-reconciliation.json 所有现金项为 null：finalFee 的旧 mapping 在不同路径代表 2×fee、fee+bond 或 totalBond，不能直接当纯手续费；赢家 payout 也不能直接当净利润。open 是聚合标签，未验证历史 adapter 路由，不混 managed 样本。

下一步需要合法可读的市场身份导出或该题一笔可核验的请求/争议交易定位，再按完整复合键读取公开链上回执；不是再次做聚合计数，也不是继续试被拒 Gamma 来源。没有进一步权限请求、充值或模型调用。

预算：2 搜索查询（1 次工具调用，发现结果不作证据）；1 次公开数据请求，0 成功正文、1 拒绝。Native OpenAI 任务 1，运行时精确模型未向本 worker 暴露，父级须按实际记录绑定；OpenCode/Pi 0，成本未知。测试 10/10 仅验证证据记账。真实生命周期/回测/模拟/达标/新机制均 0，状态保持草稿缺证。

发布建议仅 RESULT.md、账本字段、manifest、reconciliation 与复现验证脚本；原始响应留本地。不要发布为实得现金证据。
