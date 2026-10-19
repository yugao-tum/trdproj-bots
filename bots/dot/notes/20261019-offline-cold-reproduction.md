# 离线冷启动复现核验

核验日期：2026-10-19 UTC；本次主流程与独立对照于21:07 UTC前后完成。

在全新目录、CPython 3.12.14/Linux 下，按两份公开 README 从既有官方 ZIP/CHECKSUM 重建输入，7 条运行命令全部正常退出，复现既有 42 个情景：26 个现货/基准情景及 16 个 C20 条件现金情景。

13 份 CSV 与冻结结果逐字节一致；现货的 5 份结构化 JSON 在明确排除运行元数据后完全一致。C20 的 16 条记录、356 行日账和全部共有顶层字段一致；省略的两项诊断汇总可由记录精确重建。本次 C20 v1.1 的三份结果也与此前 v1.1 复现结果逐字节一致。

76 项不同的合成/单元测试及 1 项历史账务回归均通过。此次仅核验可复现性，不增加策略机制或独立回测数量，不证明实盘可执行性；C20 原 v1 保存结果后 stdout 报错、exit 1 的历史保留，公开 v1.1 本次 exit 0。

## 使用入口与边界

- [26个现货/基准情景](reproduction/README.md) · [16个条件carry情景](c20-conditional-reproduction/README.md)
- 两包需先备齐官方ZIP/CHECKSUM；本次验证298对不同归档，433次包内引用含135对共享现货归档，不能计为433个独立来源。本次没有重新下载，亦未重新核所有原网址的在线状态
- 本次实际执行C20说明为[发布版本352f4b89](https://github.com/yugao-tum/trdproj-bots/blob/352f4b89026676726c3b58ee672d9c13bf1f33aa/bots/dot/notes/c20-conditional-reproduction/README.md)，README SHA256为`1bc7cc160d68cc6127b36be1136650fe8aa7c897636f304436d8c852b190a5b2`，原包manifest为`37870e4d7e88c332a967da7927f05fd7a39b2d04be51a8dab90596666f91d311`
- 后续仅纠正README：v1.1省略`planned_mark_data_gaps`与`retrospective_subgroups`顶层摘要，但对应信息仍在records中。新文档及manifest并非本次运行前的原字节，所有代码保持一致
- 5项覆盖/输出保护均按预期拒绝；七条主命令执行前后666份指定源包、原始归档和冻结文件的SHA均不变。未验证不同Python版本或Windows/macOS兼容性

本地核验交付清单SHA256：`586035822403d738ffe2d3238cf13604d5f9e843e3df7897fe13cfec3192bff9`。公开包本身提供输入清单、恢复方式与结果摘要；原始数据和完整大账本没有随本说明入仓。
