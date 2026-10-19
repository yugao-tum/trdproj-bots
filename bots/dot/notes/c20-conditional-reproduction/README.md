# C20 条件现金模型：独立复现附录 v1.1

本包只做离线历史研究。没有网络调用、安装依赖、API、账户、下单或资金划转。Python 3.10+ 标准库即可。模型是八个独立 5,000 USDT 情景的条件现金账，保证金存活与实盘可执行性未知；出现已观察到的场所资本代理越限，不能据条件正值宣称策略达标。

## 文件和运行

- `conditional_cash_v1_1.py`：现金账及日线诊断，v1.1 仅改输入输出接口和显示
- `test_conditional_cash.py`：23 项合成现金模型测试
- `prepare_inputs.py` / `test_prepare_inputs.py`：只读既有 ZIP/CHECKSUM 的离线规范化与 10 项测试，不自动下载，不执行归档内容
- `inputs.json`：两份所需 CSV 的完整有序列名、字节数、SHA256
- `official_sources.json`：199 个官方 ZIP/CHECKSUM 的精确 URL、SHA256、成员及相对文件位置；不含原始数据
- `FUNCTION-EQUIVALENCE.json` / `VERIFICATION.json`：版本函数逐字对照与已完成的复现结果
- `PACKAGE-MANIFEST.json`：本包文件摘要

先运行合成测试，不需要行情输入：

```sh
python -m unittest -v test_conditional_cash.py test_prepare_inputs.py
```

准备原始官方归档。两个目录分别保持 `official_sources.json` 的 `relative_archive` 结构：

```text
spot-archives/BTCUSDT/BTCUSDT-1d-2023-01.zip
spot-archives/BTCUSDT/BTCUSDT-1d-2023-01.zip.CHECKSUM
futures-archives/klines/BTCUSDT_241227/BTCUSDT_241227-1d-2024-09.zip
futures-archives/klines/BTCUSDT_241227/BTCUSDT_241227-1d-2024-09.zip.CHECKSUM
futures-archives/markPriceKlines/BTCUSDT_241227/...
```

其中现货 135 对覆盖 BTCUSDT/ETHUSDT/SOLUSDT，2023-01 至 2026-09 共 45 个月；模型仅使用 BTC，但完整冻结输入包括三币，故精确复原需要全部 135 对。期货 64 对为八个固定 BTCUSDT 到期的成交和 mark 月档，每期覆盖预定到期 E−100 日至 E 所在月份。官方来源为 [Binance public data](https://data.binance.vision/) 及 [字段/校验规则 README](https://github.com/binance/binance-public-data/blob/master/README.md)。使用每条指定的官方公开 URL 及同目录 `.CHECKSUM`；遇访问限制或摘要变化应停止，不改用其他端点绕过。

```sh
python prepare_inputs.py --spot-archive-dir spot-archives --futures-archive-dir futures-archives --output-dir normalized
python conditional_cash_v1_1.py --input-dir normalized --output-dir output
```

若已具备下列两个原样 CSV，可跳过规范化，直接使用 `--input-dir`。没有它们且未备齐指定官方归档时，本包不能直接一键运行。两个程序都拒绝覆盖其既有输出。

| 输入 | 行数（不含表头） | 字节 | SHA256 |
|---|---:|---:|---|
| `spot_daily.csv` | 4,107 | 921,335 | `a008fbd0514f4d01bd477fc008de9fb24b8dfae5e83ebda2ced8bbf2e89bcf0a` |
| `FIXED-WINDOW-ROWS.csv` | 1,615 | 782,239 | `6ed2cfd9f6cbace327b888906524090697ef03598a1d5c77aeb2c30fbffee09b` |

规范化同时验证官方 CHECKSUM 和冻结摘要，单文件及解压成员上限 5 MiB；只在内存读 CSV，不解压文件落盘。保留原始毫秒/微秒字段，现货 2025 年起为微秒；期货为毫秒。为精确复原，现货格式保留原规范化的浮点时间转换，模型连接则由原始整数时间归一到 UTC 日期。mark 的 Ignore 字段不解释为成交量。所有月份行先校验，期货输出仅取固定 E−100 至 E 窗口；已知缺日不插值。

## 固定经济规则

八个到期后缀为 `241227,250328,250627,250926,251226,260327,260626,260925`。规则是在读取数据与描述性基差后、计算本条件现金账之前固定，非数据前盲预注册或来源策略复现。

- E−91 日 close 信号 `F/S−1 > 0.017`；E−90 日 open 入场，E−1 日 open 退出，89 天。两个日线 open 只是交易价格代理，非同步执行保证
- 每期总资本 5,000，场所 2,500，外部静置 2,500。现货入场名义 N=1,200，q=N/S0；做空 q BTC，期货入场名义 Q=qF0，初始独立抵押 M0=Q
- 每边成本 c 为 0.003 或 0.006；两成本情景不改变信号/仓位。初始现货钱包 N+cN，期货钱包 M0+cQ；静置场所余款 R=2500−N−M0−c(N+Q)。R<0 拒绝建仓、条件结果 null，不缩仓或借款
- 期间不划转、不追加、不动 R 或外部现金。固定 q 不舍入，历史数量精度尚未验证。M0=Q 只证明初始名义抵押，不能推断全程 1x 或始终全额抵押
- 退出先核期货钱包 `M0+q(F0−F1)−cqF1`，不能用现货卖出款补足；再卖出现货得 `qS1(1−c)`。四边成本严格为 `c[N+qF0+qS1+qF1]`
- 条件净现金变化为 `q[(S1−S0)+(F0−F1)]−c[N+qF0+qS1+qF1]`，只除以 5,000，不跨期复利或年化。未触发的现金 0 有效；信号/入退价格缺失是 null，不能替换为 0
- 任一已见期货 mark 高点/边界权益≤0，或期货离场现金不足，使条件结果不可实现/null。缺 mark 不填值；正权益不代表满足未知历史维持保证金
- 日末 NAV 代理为 `2500+R+q×spot_close+M0+q(F0−mark_close)`。场所 MTM 为该代理减 2500；另检查入场 mark open、退出前 mark open 和条件退出后现金。严格大于 2500 标资本失败。已见越限不改交易信号，也不隐藏条件代数结果；未见越限仍不能证明盘中资本安全
- 持有期检查 E−90 至 E−2 的 89 日，退出日仅使用 open，不使用其 high/close 或交割日 bar。不模拟 TWAP 交割，不收取永续 funding。30/60 bps 是假设成本，不是已验证历史费率或未知摩擦上界

### 手算与测试范围

以 S0=100、F0=102、S1=110、F1=111、c=0.003 为例：q=12，Q=M0=1,224；两笔开仓费 3.60 和 3.672；初始场所资金 2,431.272，静置余款 68.728。退出费为现货 3.96、期货 3.996；期货钱包释放 1,112.004，现货释放 1,316.04。加外部 2,500 和余款后现金 4,996.772，净变化 −3.228；四边费 15.228，价差毛变化 12，两式一致。

初始可行边界是 `1200*(2+u)*(1+c) <= 2500`，其中 u=F0/S0−1。测试覆盖边界内外、两笔入场费、实际四边名义、隔离钱包释放、前日信号/次日开盘、89 日、负权益/退出短缺、未触发与缺数分离、浮盈导致资本越限。23 项测试只验证模型实现，不证明历史手续费、MMR、逐笔同步、交易所过滤器或清算存活。

## 版本与预期产物

冻结 v1 SHA256：`c76a86df510787e81b168e38dfd57b096ceda406973502237071391f6cf4e3c3`。v1 已完整保存结果后，最后一条 stdout 显示因 Decimal 序列化报错；v1.1 将该显示修正，同时把输入/输出路径改为 CLI、去除非公开运行元数据。原 v1 及其输出未覆盖。18 个共同函数/类逐字相同，清单见 `FUNCTION-EQUIVALENCE.json`；现金函数、常量、交易规则未改变。

从上述 199 个已下载官方归档离线恢复两份精确输入后，v1.1 已成功再现：

- `EPISODES-16.csv`：16 行，SHA256 `eca0d4ce47a71fce5342607b07363e9fe5ea0e20869386463c00aea298434409`
- `DAILY-PROXY-LEDGER.csv`：356 行，SHA256 `432c21fd185d24f99f1c069fd072aa93a1334b4eb61c97f9dca4640438c0d86a`
- `RESULTS.json`：16 个记录与冻结 v1 完全一致，共有资本诊断相同。v1.1 未重复输出 `planned_mark_data_gaps` 与 `retrospective_subgroups` 两个顶层汇总字段，对应信息仍逐条保留在 `records.source_quality` / `records.subgroup`；另有版本、输入与审批等元数据变化，因此整个 JSON 字节摘要不同

基准只在 241227 和 250328 入场，条件净现金变化分别约 +2.206935 / +23.223096；压力约 −15.960055 / +9.269478。其余六期现金 0。四个活跃成本情景均见资本代理越限；基准/压力越限点数 95/71。260925 缺 2026-06-29 mark，即使无仓位仍保留缺口。前后四期仅回顾性分组，后四零入场，不是未见 OOS。

计数为一项条件历史模拟机制、16 情景；完整可执行 carry 验证为零。本次版本复现不新增独立机制。包内不含 ZIP、规范化行情 CSV 或内部审查对话；官方归档若被修订导致哈希不符，不能声称重现了相同冻结实验。
