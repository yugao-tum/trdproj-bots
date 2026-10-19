# 解锁事件数据的BTC控制列核验

草稿数据质量记录，访问/执行：2026-10-19 UTC。策略回测计数0，利润未知。

## 发现

公开冻结CSV的52行中，21行BTC控制收益在“unlock_date按UTC、按论文实际公式”的假设下超出官方日线OHLC所容许的必要区间。缺失0。暂不采信此列为收益证据，先澄清时间和价格口径。该检查不能推出数据合成或造假，也没有验证各token价格、真实解锁数量或解锁事件本身。

## 来源与方法

- [原始事件表](https://github.com/gameworkerkim/vibe-investing/blob/main/01.Trading%20Strategy/Token%20unlock%2072h%20shock%20analysis%20/data/01_binance_token_unlock_events_2023_2025.csv)，定位`unlock_date`与`btc_change_72h_pct`列
- [不可变CSV blob](https://api.github.com/repos/gameworkerkim/vibe-investing/git/blobs/1cf3447a4688d04457ea941e20d4309fa897b6bd)，6747字节，保留BOM与CRLF；SHA256 `b195292750a94428e1aee4718c05f27fdb068e74aa3c3bafb9d8cb80a59029c7`
- [不可变英文论文](https://api.github.com/repos/gameworkerkim/vibe-investing/git/blobs/0bd7a8e46404885d5aba84fcb0c9c2ad5cb86f01)，定位§3.2第126–129行：R72=P(T+72h)/P(T−24h)−1，实际跨度96小时；BTC对照同公式
- 官方BTCUSDT日OHLC来自[公开月归档示例](https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-2025-06.zip)及对应CHECKSUM，实际读取/校验2026-10-19。使用2023-01至2026-09合并日线

若解锁日为d，原文公式下任何同一精确时点端点收益必须在以下宽界内：

`[low(d+3)/high(d−1)−1, high(d+3)/low(d−1)−1]`

容差0.005个百分点，仅处理来源两位小数舍入。价格落在宽界内不是准确性证明；越界只证明在所列日期/价格定义假设下不一致。

| 例子 | 源BTC收益 | 官方必要宽界 |
|---|---:|---:|
| ME 2025-06-10 | +2.1% | [−7.116%, +0.818%] |
| IO 2025-06-11 | +2.2% | [−5.525%, −1.919%] |
| TIA 2024-10-31 | +3.8% | [−7.514%, −2.863%] |

另做T→T+72h（d到d+3）敏感性，同样21/52越界，但名单不同，不能混作同一21行。主检验仍按论文d−1到d+3口径。

## 对C34的影响

解锁前转现金、之后回补只是一条待验证规则。避免持币下跌的收益是相对一直持币的基准差，不是自动获得USDT绝对利润；所有卖出和回补费用必须扣。当前来源事件表未经时间/价格口径澄清不能用于收益回测；≥30独立事件、事先公告vintage与真实执行价格仍待建立。相关公开源付费墙/钥匙限制未绕过。

本次只执行自编标准库必要区间检查，没有执行外部项目脚本。详细52行结果保留本次独立研究归档，原始数据不提交仓库。
