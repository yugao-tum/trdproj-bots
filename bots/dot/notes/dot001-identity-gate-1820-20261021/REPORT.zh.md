# dot001 固定 July15 身份门槛：已补身份与当前规则，未获历史回放许可

## 结果

2026-10-21 18:21:54Z，唯一一次公开 Gamma 请求成功（HTTP 200，7,051 bytes）。返回恰好一条，conditionId 和固定 CSV 题目逐字匹配：纽约 2026-07-15 最高温 108–109°F。日期由 slug 与规则明确，不按目录名推断。原始响应不落盘、不输出；先筛选字段后保存。SHA256：708bea0e0e5b7bc403e27b4d5a75d35c0825b7d40c8e9888a6dc86f566990198。

- Yes token：59684631090894860342627362261547710699304728428578731737561711227655228099733。
- No token：1976253979431492150474990500785584818806292262013039337452843580026487653025。
- 映射由显式 outcomes=[Yes, No] 与 clobTokenIds 对位建立，不是盲猜第一项。CSV condition→文件绑定已重验；同一文件 SHA256 与前轮一致。文件方向仍以 Marketlens 的 YES-centric 来源文档为依据，不冒充文件内自带 token。

## 当前规则与版本限制

站点为 LaGuardia Airport Station / KLGA；结算源为 Wunderground 当日全部记录的最高温，网址 https://www.wunderground.com/history/daily/us/ny/new-york-city/KLGA 。使用源站整数华氏度精度。必须等下一日期首个数据点发布才能结算；在此之前考虑当天温度修订，此后忽略修订。没有明确给出缺测处理、独立舍入算法、时区或精确民用日边界，不自行补写。

这不是 NOAA 直接结算市场。即使后续有 NOAA as-of 资料，它也只能成为另行验证的预测输入/站点对照，不能替代 Wunderground 规则与可知时点证据。

本次 description 与 feeSchedule 都是当前返回版本。市场 updatedAt=2026-07-16T05:59:10.508247Z，晚于 2026-07-15T18:00Z 决策；不知修改的是哪个字段，不能由此断言规则修改过，也不能断言规则当时相同。历史规则、历史费率、源站公布延迟及修订轨迹仍无证。

## 新日期矛盾与覆盖

Gamma market/event endDate 均为 2026-07-15T12:00:00Z；CSV close_time 为 2026-07-16T12:00:00Z，相差24小时。不能把 endDate 自动等同实际停止接受订单时刻，也不能无视它来声称决策时可交易。这是字段语义/日期一致性的新增待证项。

只重读已有固定 Parquet 的 event_type/t 列及 schema、哈希：3,221行，3,161 snapshot、49 delta、11 trade。覆盖 July14 02:07:10.118Z 至 July16 05:58:51.762Z，包含 July15 18:00Z 两侧。此前最近快照为17:59:05.732Z，早54.268秒；下一快照为18:00:05.920Z，晚5.920秒。不能使用后一条冒充当时可知数据。CSV data_end 仍较文件末时刻早96.762秒。

本文件不覆盖 July16 18:00Z；前轮 CSV 为 July15/16/17，目录 README 日期偏移尚未消解。33个市场不是33独立事件日；前轮目录最多3个事件日，本轮实查只有一个选定市场文件，未验证30个独立样本。

## 快照测试与成交边界

官方来源文档自述 YES-centric/compact 快照语义可支持“具明确文件级映射的存储快照”方向，不应新增每行必须 token、双时间戳或 sequence 的万能门槛。纯快照单点检查不需要先解决所有 delta 原始顺序。

但“存在存储快照”不等于“在决策时可执行”。t 的 exchange/receive/采集可知语义、决策前快照的时效性及其至决策时状态变化未独立证明；原始任意时刻 delta 重建另需排序、连续性和重置证据。前轮该快照为0个bid、52个ask，不能推出双边可成交。实际成交还涉及方向、数量、深度、延迟、队列、手续费与订单接受状态，均未在本轮验证。本轮不读价格、不推断收益、不挑选策略、不晋级。

## 下一步建议（本轮未执行）

身份缺口已真实缩小，不应再把 token 映射列为未知。若父任务继续，仅考虑固定 condition 的历史规则/源站 as-of 有限取证及 endDate/实际开关市语义；当前结果并不证明历史存档一定存在。若不能找到可行路径，应退出收益回放队列并转向既有可检验方向，而不是重复同一接口或无限期 STOP。可保留该文件做非收益的存储快照结构验证，且不得把结构验证写成可成交验证。

证据：request-audit.json、filtered-metadata.json、local-validation.json、identity-rules-validation.json。仅本地保存，无远端发布、交易、钱包、密钥、模型调用、CLOB reward 请求或访问拒绝绕过。


## 发布归属与范围

上述“仅本地保存”描述身份核验执行阶段；本报告随后作为18:20复盘附录发布。Marketlens 数据来源固定版本 `6eb9b8efda545eddafb2a8f75acb4bcbca6db019`，遵循其 CC BY 4.0 归属；本包只含说明、身份和结构元数据，不含原始 CSV/Parquet、价格序列或结算结果。来源文档：[YES方向](https://marketlens.trade/docs/orderbook)、[compact导出](https://marketlens.trade/docs/exports)、[市场身份](https://marketlens.trade/docs/markets)。这是对前轮过严万能门槛的追加更正，不改旧冻结记录。
