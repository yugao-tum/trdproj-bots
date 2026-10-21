# dot001 单文件来源门槛：未通过完整数据契约

归属：Marketlens, https://marketlens.trade，CC BY 4.0（保留发现阶段归属；本轮未越出指定目录另读许可证）。固定 commit 6eb9b8efda545eddafb2a8f75acb4bcbca6db019。

## 真正新增的证据

- 已取得且只取得一份 compact Parquet，438,119 bytes。git blob a7543cfb10551a66232976d6b5df89eca0f51863 与固定目录元数据一致；SHA256 9f23926cd1e02dcbacdfa32fd65d42c312c1ec4b50aa5300cb0f4b453cf0a857。CSV 的 git blob 也一致。
- 真实内容有 3,161 snapshot、49 delta、11 trade，367 snapshot 标记 reseed；不是纯成交代理，也不是另一个 snapshots.csv 的5分钟摘要。snapshot 间隔中位数60.8535秒；不能由此推定逐撮合事件完整性。
- CSV event/question 实际为 July15/16/17，各11个市场；README 却写 July16/17/18。按最早实际事件日+文件名固定选 July15 的 history-01a77489…，对应纽约108–109°F档。不是按价格、成交量或结算挑选。
- July15 14:00纽约时间为18:00Z。最后存储 snapshot 在17:59:05.732Z，第一之后 snapshot 在18:00:05.920Z；此前快照0个bid、52个ask，不能声称双边可执行。全文件跨度 July14 02:07:10.118Z 至 July16 05:58:51.762Z。

## 尚未跨越的门槛

CSV 仅提供 condition→文件绑定；Parquet 内也没有 token_id、condition_id 或市场规则。YES/NO方向和token映射未证。t与epoch毫秒吻合，但没有 exchange/receive 双时间或来源语义。

49个delta全部与11组trade共享时间戳。文件时间非递减，但没有sequence、连接ID或compact变换说明，不能把文件行序当原始交易所顺序。367次reseed和最大248.304秒记录间隔不能自行证明重连边界/丢包时长。局部完整depth重建未运行，因为前置映射和连续性不成立。只能确认“含snapshot的压缩资料”，不能确认“有效的任意时刻原始盘口”。

CSV data_end还比Parquet末时刻早96.762秒，记录为来源元数据矛盾。July16 18:00Z不在选中文件内；不得把July15事件按目录名移成July16。July18覆盖也未成立，CSV没有该事件。

历史feeSchedule、原始结算规则、NOAA当时可知资料、标签as-of与官方可采纳性分别UNKNOWN。3天至多3个事件日且可能相关，33文件绝不是33独立样本，更不是30样本达标。

## 范围、原门槛修订与下一步

原验收门槛要求CSV缺token/规则即停止；后续验收范围明确修订为可检查同一确定文件schema，避免把“CSV不含字段”误当“整个源不含字段”。本轮schema实查后仍缺关键字段。fresh known与dot claims已读，本项仅补已有C01，不新开认领、不改entry。

下一步只有获取token方向、t来源、compact排序/重连语义及原始规则的公开文档才有意义。root README不在本轮指定目录，未打开；若扩展到该单一元数据文件，应明确限定不读取混合crypto资料。不得立即回测或晋级。

原始CSV/Parquet只保存在本地；不得提交到项目仓库。无SDK、key、付费API、crypto文件、PnL、交易、远端写入或拒绝绕过。格式工具首次不支持binary后使用同文件官方base64接口成功；不是权限拒绝重试。

审计限制：首个CSV诊断预览和目录README返回意外露出结算/成交量；首次结构诊断打印一个价格层。均未用于文件选择、收益或结论；后续输出仅身份、字段、计数和时间。完整记录见 SOURCE-GATE.json。

复现：使用已安装 pyarrow 的 Python 环境，将下列固定来源文件放在 inspect_source.py 同目录，运行 python inspect_source.py。该脚本只做字段/结构/时序检查，不计算收益。原始数据不随本报告再分发。SOURCE-GATE.json为结论，FILE-INSPECTION.json和ORDERING.json为实查证据。

固定下载来源：https://github.com/marketlenstrade/polymarket-historical-data/blob/6eb9b8efda545eddafb2a8f75acb4bcbca6db019/nyc-weather-2026-07-16/history-01a77489-79e6-55b6-95f0-a47778dd0bcf-compact.parquet

CSV：https://github.com/marketlenstrade/polymarket-historical-data/blob/6eb9b8efda545eddafb2a8f75acb4bcbca6db019/nyc-weather-2026-07-16/markets.csv
