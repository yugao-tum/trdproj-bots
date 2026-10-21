# 固定批次发布时间门禁：不通过，证据链未成立

固定目标：KLGA / GFS / 2026-07-15 12Z，决策截点18:00Z。结论为 FAIL_AS_OF_UNPROVEN，不等于认定当时没有发布。

## 本轮实际证据

1. IEM MOS 官方页面说明原始集合报文会拆为站点 PIL，格式为模型前缀加三字符站点。AFOS 官方帮助明确 MAVxxx 为 GFS MOS，因此固定目标使用 MAVLGA，并加 matches=KLGA 身份过滤。
2. 官方 retrieve.py 文档支持 sdate（UTC含起点）、edate（UTC不含终点）、limit、order 以及文本格式。按该契约只查询一次12:00–18:00Z、limit=1、order=asc，没有按预测值挑选。
3. 唯一目标请求 HTTP 200，响应29字节，SHA-256为 66d8f72c0435534fc14043b84302a852ea7fa30332d8d77de54f8a23c0431ef6。过滤结果没有 WMO、MAVLGA、KLGA runtime、DT 或 HR 报文头。未保存/输出原始响应，故不声称其具体诊断文字，也不据此认定整个档案缺失。
4. 因未取得可匹配报文，无法得到并定义该批次的历史 issuance/接收时刻。文档的 near-real-time 描述、HTTP成功、当前抓取时刻，以及先前JSON中的runtime均不能替代这项证据。

## 停止与影响

本次固定来源门禁已结束。不换路径、不改参数补抓，不扩大档案扫描，不回放收益，不提升参赛状态。没有重新获取MOS预测JSON，没有使用预测值、市场价格、Parquet、币圈接口或费用假设。

即使未来发布时间证据补齐，当前独立事件仍最多3个而非30个，历史规则/费率、开关市与执行证据仍未补齐。本轮只形成方法补证的负面结果，不构成可计分的新实测。

## 证据文件

- mos-docs.json、afos-docs.json、retrieve-docs.json：官方文档过滤文本、来源、HTTP状态、响应哈希。
- bulletin-metadata.json：唯一目标请求、响应哈希和过滤元数据。
- GATE-RESULT.json：机器可读结论与边界。
- SHA256SUMS：本地交付文件哈希。响应哈希只证明本轮取回内容，不能追溯证明历史公开时间。

来源链： https://mesonet.agron.iastate.edu/mos/ → https://mesonet.agron.iastate.edu/wx/afos/ → https://mesonet.agron.iastate.edu/cgi-bin/afos/retrieve.py?help 。目标查询完整URL见 bulletin-metadata.json。
