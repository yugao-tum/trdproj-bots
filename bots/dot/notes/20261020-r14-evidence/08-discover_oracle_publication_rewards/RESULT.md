# r14 native08：oracle 数据发布酬劳初筛

结论：停止本方向本轮扩搜，不新增认领或 entry。阶段为公开机制草稿初筛；真实付款小样 0、收益回测 0、条件模拟 0、达标 0。不是证明该服务没有收益，也不是完整否决所有 oracle 协议。

## 查重
先读 remote-snapshot 的 known135 与三方 claims；三方 index/log 在快照中，协调者确认已完成全量检查且快照来自 e068c98a。随后 09:34 UTC 实际 connector 回读 dot/muse/quant claims，三个 blob SHA 与快照一致。数据发布者收客户查询费不同于 C38 提案/争议保证金转移，亦不能直接把 C49 AVS 安全服务费换协议算新机制。若主要收入是协议发行，需归并 C27 或补贴族而非新客户费。未发现名称级同题，不代表获得新颖性认定。

## 已读证据与边界
1. [Tellor AutoPay](https://github.com/tellor-io/autoPay)，2026-10-20，README 的创建/资助数据 feed 与 claim 接口：用户可付 tip，reporter 可领取。仅付款接口，不是实际付款记录；未运行代码。
2. [Tellor 2026 白皮书](https://github.com/tellor-io/layer/blob/main/Tellor%20Whitepaper-2026.md)，同日，Tipping/Tokenomics/Dual Delegation：请求 tip 的 98%按报告贡献分配，2%销毁；奖励需解锁并受21日路径约束。另有协议发行奖励，不能把两者混作外部客户收入。双重委托有罚没风险；未核最低资本与实际运营成本，不能宣称2500USDT可做。AutoPay旧接口与 Layer 新规则不得拼接为同一执行版本。
3. [Flare 计算规则](https://github.com/flare-foundation/FTSO-Scaling/blob/main/scripts/rewards/README.md)，同日，Total reward pool/FDC reward calculation/Public reward data：池内可含发行与客户请求费，分配记录还经过最小服务条件/销毁处理。聚合 reward claim 既不是客户费分量，也不是已到账交易。复算需带历史的索引数据库；本任务没有获取它。
4. [Flare 官方分配目录](https://github.com/flare-foundation/fsp-rewards)，同日，README 说明 epoch227起该仓库为分配数据权威来源。按其路径约定试取 flare/227 的两份 JSON，web为 Cache miss，connector各一次返回404。未获得数据内容；不得声称已读取一个历史报酬数据集，也不得将404外推为全部数据不存在。

## 七门槛矩阵（未通过不等于经济反证）
| 门槛 | 状态 | 依据/缺口 |
|---|---|---|
| 1 谁付款及持续原因 | 部分 | 有查询/报告服务客户tip规则；真实持续需求未证 |
| 2 免费收益数据至少12月 | 不满足本轮证据 | 实际付款样本0；只有目录与规则 |
| 3 总5000/场所2500、容量 | 未知 | 质押门槛、服务器/数据源费、gas、罚没和容量未闭合 |
| 4 不重复 | 初步边界清楚 | 区别C38；C49/C27仍需按实际收入归因，未认领 |
| 5 扣成本8%或低相关3% | 未知 | 无实际分配/到账/成本/USDT计价，不算收益 |
| 6 两周30独立结果 | 未知 | epoch/重复报告不自动算独立结果；没有合格事件样本 |
| 7 可查出处 | 规则部分满足 | 已读官方正文与精确失败目标留档；数据数字缺失 |

## 止损与下一步条件
3次GitHub定向搜索、2次X搜索用完；X无相关线索。6个唯一正文目标（其中2个失败文件各再用connector确认一次），仅4个正文成功；不为了耗满15分钟继续无依据扩搜。无真实客户费到账样本，因此提前停止。本轮没有额外授权需求、没有访问拒绝绕行、没有注册/钱包/交易/密钥使用，亦无Pi/meiying/OpenCode调用。
仅当后续独立提供可读的历史付费记录、明确部署版本、客户费和发行拆分及小额准入条件时再重启。首笔分配还须用真实到账交易核验，不将可领取额当已收现金。保留负面筛选记录即可，不创建低质量待核项；不把初筛线索计入新增独立机制20批。
