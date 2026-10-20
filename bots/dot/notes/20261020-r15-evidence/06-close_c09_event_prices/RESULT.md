# C09：真实行页审计与事件连接覆盖

2026-10-20，native OpenAI（精确模型 ID 未暴露）。这是旧机制的数据闭合任务，不是新策略、收益回测或达标报告。

## 这次新增的证据

旧审计只有 Parquet footer；本次对三份原有小文件真正解码全部行页，且逐文件 SHA-256 与冻结输入一致。三份都是完整数据容器，不是 LFS 指针、footer JSON 或伪装网页。

- Dinesh 标签：187,094 行，187,094 个唯一 slug，无 slug 重复/冲突。api 169,458 行，convergence 17,636 行；两类都不是本任务独立核实的最终结算。
- Dinesh 2026-07-10 报价：783,350 行、9,266 个 slug。与标签严格按 slug 连接，6,877 个 slug、560,074 条报价能接上；2,389 个 slug 没标签。349,393 行至少缺 bid/ask 一侧。非空值未发现 bid<0、ask>1 或 bid>ask；这不代表流动性或实际可成交。
- 报价时间跨度为 2026-07-10 20:25:46 至 23:59:33，Parquet 时间戳无时区，不能标作已核 UTC。volume24hr 不是单笔成交数量；bid/ask 是报价，不是成交。
- Pancake 2024-11 结算：258 行、258 个市场，全部有 condition_id，但 258/258 evidence_uri 为空；received_at 全晚于 resolved_at。与已有 Marketlens catalog 的 condition_id 和 market_id 严格匹配均为 0。不存在可据此拼接的跨表事件价格链。

## 冻结面板结论

完整面板 = 0。最早完整时间窗为空，按 canonical event ID 排序前 30 个独立事件也为空。不用 slug/市场行数量冒充独立风险事件；不把不同年份、不同标识空间的行强行连起来。

缺的不是计算能力，而是 canonical event/token 映射、事前规则及结束时间版本、真实成交时间/价格/数量、互补侧历史执行报价/深度、费率和独立最终结算证据。本次不重新跑 C09 收益代理，不从赢家筛选样本，不用 1−YES ask 补 NO ask，不把标签 source=api 当作 UMA 最终性证明。

覆盖矩阵见 coverage.csv；20 条可回原文件核实的字段例子只存 LOCAL_ONLY_20_FIELD_EXAMPLES.json（附原文件零基行号），不得提交原始行数据。它们是 10 条确定排序的报价行及 10 条确定排序的结算行，不是 20 个独立事件。

## 阻碍、下一步与停止条件

Gamma 此前存在平台网络拒绝及 HTTP 403/error 1010。本任务没有请求该目标，也没有换工具、域名或路线。无需用户提供交易密钥；不得用凭据填此缺口。旧文件解码和连接检查已完成，依赖外部取证的闭合仍未完成。

前向采集在数据模型上可行，但当前不能声称已开工、已畅通，或两周保证得到 30 个独立结果。重新启动必须先有获准且实际可读的规则/event/token 来源，保存规则版本和首次收到时间，再采集两侧成交/盘口、数量与费用，最后独立核对结算；服务限流或网络拒绝未解除前不试探重试。没有这组来源时，应暂停 C09 收益测试，优先推进已有可重现数据的机制，而不是重复目录扫描或标签收益代理。

## 来源与复现

三份公开数据均沿用 2026-10-19 已下载原件，本任务新市场数据请求为 0；旧请求时刻、HTTP 200 和完整指纹在 source-manifest.json。

- https://huggingface.co/datasets/DineshKumar8399/polymarket-orderbook-dataset/resolve/main/labels.parquet
- https://huggingface.co/datasets/DineshKumar8399/polymarket-orderbook-dataset/resolve/main/quotes/dt%3D2026-07-10/data_0.parquet
- https://raw.githubusercontent.com/usepancake/polymarket-history/356b59b01ae74cc558ae75d8dcf4b7971be5a509/datasets/v1/polymarket/resolutions/2024/11/part-0000.parquet

使用 audit_event_panel.py --base <冻结 operator-c09-data 目录> --out <输出目录>；依赖 PyArrow（版本记录在 aggregate.json），不执行第三方策略代码。然后 python -m unittest discover -s <输出目录> -p test_audit_event_panel.py。8 项测试通过，含文件识别、输入指纹、实际行页计数、连接守恒、20 条例子及禁止伪最终性/收益。运行依赖 runtime/、缓存及原始行例子只留本地。

状态：数据闭合未通过；真实策略回测 0、条件收益模拟 0、新机制 0、达标 0、净收益 null。固定历史数据已见，不称真正未见样本外。
