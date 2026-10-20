# C36：真实回购成交重建，不是收益回测

## 结论
固定窗口为 2026-10-12 00:00 至 2026-10-19 00:00 UTC（左闭右开），未重新选择窗口。4 页真实官方 fills 共 6659 行，6 行内容完全一致的分页重叠，按 (coin, tid) 去重后实际使用 6653 行；无冲突 identity。spotMeta 确认 @107 = token 150 HYPE / token 0 USDC。

用 Decimal 从原始字符串计算：买入 156264.38 HYPE，执行名义金额 12644608.32880 USDC，API 报告费用 0 HYPE / 0 USDC，VWAP 80.9180462546870886 USDC/HYPE。这里的现金是 px × sz 与已报费用的成交推导支出，不是银行式完整现金账户对账，更不是持有人利润或策略净收益。

成交边界库存从 47962416.9547392279 到 48118681.3347392285 HYPE，差额 156264.3800000006 HYPE，相对净买入残差 0.0000000006 HYPE。6652 条相邻边中 6337 条存在非零的源字符串小数残差，最大 0.0000000072 HYPE，均小于 HYPE 的 1 基础单位（0.00000001）。因此不能沿用先前 float 诊断的“严格零差异”说法。时间相同的成交按 startPosition 排序，不按 hash 或 tid 假定成交顺序；3490 个时间组。

## 证据边界与未闭合部分
- 这些是官方 API 返回的真实历史成交，不是合成数据；尚不是一个真实策略回测，也没有达标/收益结论。gross buyback 不可计为可得利润。
- 第一笔为 10 月 12 日 00:30:53.539 UTC，末笔为 10 月 18 日 21:26:08.084 UTC。仅凭末页不足 2000 行不能证明两端空白确实无交易。API 文档明确单页最多 2000 条、只能获取最近 10000 条；未取得独立 archive 或窗口边界快照，所以完整七天覆盖仍未证明。已看到成交的子集对账，不等于完整现金/供应桥。
- 1289 笔返回零 hash。每行保留 API tid、oid、time 和 hash，但不能说每笔都已获得独立链上交易证明；hash 不能作为去重主键。其余非零 hash 也没有额外 explorer 验证。
- 162 条 nonFundingLedgerUpdates 均为向 AF 转入 KNTQ，不能拿这些 token amount/usdcValue 当作 USDC 协议手续费收入，也不能由未出现 HYPE outbound 推断销毁为零。
- 请求时的 spot state 晚于窗口，不能代替 10 月 19 日零点余额。
- 官方 Fees 文档将 AF HYPE 描述为烧毁并退出流通/总供应；这是协议声明，与当前可见库存字段并存。没有独立销毁事件或供应总量快照闭合，不能将买入和 burn 作为两次供应减少。supply-bridge.csv 的未知量留空，不伪填 0。
- 仍缺：两端 UTC 午夜 HYPE/USDC 账面快照、覆盖完整窗口和之后到提取时间的归档成交以排除 10000 条裁剪、协议手续费入账明细、销毁/总量调整与铸造解锁事件。仅补上述证据即可推进，不需要重复已有下载。

## 时间与输入保护
24 份 retained 文件 SHA256 全部匹配 handoff。原 freeze 文件保留不改。其人工填写的 09:07 时间不是实测写入瞬间，tool-17 显示写入运行于 09:06:30.127–09:07:39.053 UTC，首次 fills 请求 tool-18 开始于 09:07:42.756 UTC。记录支持冻结写入完成先于本次首次 fills 请求，不证明其他会话从未见过价格。原文“最近已完成午夜”不准确：10 月 20 日提取时 10 月 19 日不是最近午夜；此处透明更正措辞，保留原选窗。

## 产物与复现
- code/reconcile_native.py：纯离线 Decimal 重建、冲突去重、单位验证、边界检查。
- code/test_reconcile_native.py：12 个明确标注 synthetic 的单元测试 + 1 个真实 retained-input 对账测试，全部通过，详见 test-results.txt。
- buyback-ledger.csv：6653 条逐笔派生账本，仅本地留存，不发布市场明细 archive。
- buyback-daily-summary.csv：七天聚合，可发布。
- supply-bridge.csv：现金/库存/供应分层，未知供给和现金账户项目显式留空。
- reconciliation-summary.json、source-body-manifest.json：精确总数、残差、真实来源正文 hashes、来源时间和覆盖限制。
复现命令：python code/reconcile_native.py；python code/test_reconcile_native.py。需本地 raw 输入；不得为运行测试自动重新抓取或绕过限制。

## 来源
https://api.hyperliquid.xyz/info （公开、无 key，留存 4 页 fills、spotMeta、ledger 与窗口后的 state）
https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees
https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint

## 实际执行归属
同一逻辑任务 continuation-r13-02，仍计 1 个角色、0 个新机制。前半由 OpenCode Go / deepseek-v4.1-flash / max 执行，原 prompt 1 次及同会话窄范围修复续接 1 次，已被用户停止并核验 idle。后半由 native OpenAI agent 离线接手；精确 native 模型标识工具未披露，不冒充 DeepSeek。
Native：0 网络请求、0 搜索、0 外部模型调用；成本未知。继承已用预算：0/8 搜索、4/32 source-body reads、8/64 数据请求；未重复取证。未新增 OpenCode、Pi 或 meiying 调用；没有交易、钱包或凭据动作。未自行发布，由父级合批。
