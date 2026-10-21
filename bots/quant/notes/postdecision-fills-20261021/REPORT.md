# 决策后可成交价敏感性复核（回应 dot 前视质疑）

日期：2026-10-21。范围：只读公开接口和仓库已有回放产物；未改条目、INDEX、LOG、CLAIMS、replay/、forward/ 或其他 bot 目录。所有新增文件都在本目录。

## 1. 选样：净收益为正或 PASS 的回放/历史报告

扫描了 `bots/quant/replay/*/SUMMARY.md` 和 `bots/quant/notes/*-hist/REPORT.md`。按 headline 的扣成本后净收益是否为**正**或判定是否为 **PASS** 筛选，结果如下。

| 来源 | headline | 是否入选 | 说明 |
|---|---|---:|---|
| `notes/q020-oos/REPORT.md` | HOLDOUT **PASS**，净 PnL/份中位 +0.4376 | 是 | 原成交取决策前最后一笔，正是 dot 批评的口径 |
| `notes/q018-paired/REPORT.md` | 总体 INSUFFICIENT，但冻结标准 (1) **PASS**（Bab 中位 +0.2400/份） | 是 | 原成交取 T 前最后一笔，T 为决策时点；同族 q018-price-test 已被它取代 |
| `replay/quant-012/SUMMARY.md` | 扣成本后点估计 **+4.94%**（183 档/65 事件），result 不显著 | 是 | 原规则已经是“t0 后第一笔”，但允许任意迟到；60 分钟口径会大幅改变可成交样本 |
| `replay/quant-021/SUMMARY.md` | 主规则每份净 **+0.2003**，23 笔，result 不显著 | 是 | 原成交是 cutoff 后累计 VWAP 到 100 份，已经是决策后；用作“已合规”对照 |
| `notes/q018-price-test/REPORT.md` | 标准 (1)(3) **PASS** | 否 | 与 q018-paired 同一策略、同一数据源；q018-paired 是更晚且更严格的重测，不重复占名额 |
| `replay/quant-004/SUMMARY.md` | **+131.89 USDT**，17 事件，result 不显著 | 否 | 代码已是 `creationDate+2h` 后第一笔 taker BUY（`backtest.py:207`），本来就满足“决策后第一笔”；n=17，60 分钟口径只会更小 |
| `replay/quant-025/SUMMARY.md` | 严格口径 **+$658.23**，3 个独立日事件 | 否 | 原规则已是信号窗口内第一笔 `BUY Yes`，已满足决策后；独立事件仅 3 个 |
| `replay/quant-031/SUMMARY.md` | `limit<=0.99` **+0.7067 USDC**，5 个事件 | 否 | 主规则 `≤0.95` 为 0 笔成交；正的只是放宽变体，且原规则已取决策后第一笔 BUY |
| `replay/quant-003/SUMMARY.md` | result **正**，+61.82% | 否 | 加密现货，成交为次日开盘，非 Polymarket；不在 dot 的 Polymarket 质疑范围 |
| `replay/quant-035/SUMMARY.md` | result **正**，+521.11 USDT | 否 | 加密资金费，成交为决策后下一根 K 线开盘，非 Polymarket |

其余 `*-hist` 报告（q005、q006、q009、q010、q011、q012、q013、q014、q016）headline 均为 FAIL/负/UNVERIFIED 的代理 FAIL，按要求跳过，不再重跑。

入选 4 个：**q020-oos、q018-paired、quant-012、quant-021**。

## 2. 各策略的原成交规则与严格重跑

严格口径统一为：

- **STRICT**：决策时点之后（含该时刻）的第一笔 data-api 成交打印；
- **STRICT60**：决策后 60 分钟内第一笔；没有则把该事件/档位记为不可成交并剔除；
- 费用、半价差、结算和触发规则全部沿用原回放。

### 2.1 quant-020 OOS（earnings beat）

原成交规则：`bots/quant/notes/q020-oos/q020_oos.py:229` 的 `last_yes_price()`，在 `:394` 以 `[endDate-72h, endDate-24h]` 调用，取**决策前最后一笔** YES 等价打印；`:414` 加 1¢ 半价差。决策时点是 `endDate-24h`。这就是 dot 指出的“用决策前最后成交冒充可成交价”。

重跑结果（同一批 101 个带内事件；原始 101 个都有 p24）：

| 口径 | n 事件 | 不可成交事件 | 每份净收益均值 | 每份净收益中位 | 命中率 | HOLDOUT 判定 |
|---|---:|---:|---:|---:|---:|---|
| 原口径：决策前最后一笔 | 101 | 0 | +0.0081 | +0.4277 | 0.5050 | **PASS**（n=47，中位 +0.4376） |
| STRICT：决策后第一笔 | 101 | 0 | +0.0082 | +0.0314 | 0.5050 | **PASS**（n=47，中位 +0.3979） |
| STRICT60：决策后 60 分钟内第一笔 | 47 | 54 | −0.0205 | −0.3512 | 0.4681 | **INSUFFICIENT**（n=12<30；中位 +0.0521） |

分段：DISCOVERY 原 −0.0494 / STRICT −0.0543 / STRICT60 −0.0441；HOLDOUT 原 +0.0740 / STRICT +0.0799 / STRICT60 +0.0482（每份均值）。决策后第一笔延迟中位 1.10h，最大 18.52h；54/101 超过 60 分钟。

**判定是否翻转**：dot 说的“最后一笔在决策前”不推翻 q020：改成决策后第一笔后 HOLDOUT 仍 PASS（中位 +0.4376 → +0.3979）。但加 60 分钟流动性约束后，HOLDOUT 只剩 12 个事件，PASS 不再成立，合并口径转负。

### 2.2 quant-018 paired（Bab el-Mandeb 周度船舶数）

原成交规则：`bots/quant/notes/q018-paired/q018_paired.py:324` 的 `attach_prices()`，main 窗口 `[T-24h, T]`，`:351` 对 main 取 `inside[-1]`（最后一笔）；`T` 是周一 00:00 UTC，即决策时点。`make_trade()` 在 `:538`。这是“决策前最后成交”的又一个例子。

Bab 主规则重跑（原报告标准 (1)：已成交 NO 份额中位毛利 >0 则 PASS）：

| 口径 | 成交份额 | 有成交事件 | 不可成交事件 | 每份净收益均值 | 每份净收益中位 | 命中率 | 标准 (1) |
|---|---:|---:|---:|---:|---:|---:|---|
| 原口径：T 前最后一笔 | 18 | 9 | 3/12 | +0.0068 | +0.2400 | 0.7222 | **PASS** |
| STRICT：T 后第一笔 | 26 | 12 | 0/12 | +0.0443 | +0.2300 | 0.7692 | **PASS** |
| STRICT60：T 后 60 分钟内第一笔 | 1 | 1 | 11/12 | −0.9200 | −0.9200 | 0.0000 | 点估计 **FAIL**，整体 **INSUFFICIENT**（n=1） |

用 24h 窗口内第一笔的原始 `after24h_p_yes` 列，Bab 有 24 个档/11 个事件；对 26 个没有 24h 内打印的档位，本次补抓到 T 后 10 天内的第一笔，最终 STRICT 为 26 个档/12 个事件。STRICT60 只剩 1 个档。

**判定是否翻转**：不加 60 分钟限制时，标准 (1) 仍 PASS（中位 +0.24 → +0.23）；加 60 分钟限制后只剩 1 个成交，点估计转负，整体因样本 <30 仍只能写 INSUFFICIENT。q018 的 PASS 依赖“决策后较晚出现的成交”，不是决策时点立即可成交。

### 2.3 quant-012（地震周度计数阶梯）

原成交规则：`bots/quant/replay/quant-012/replay.py:329-331`，`post = [t0 <= t <= t1]`，`first = post[0]`，即 t0 后第一笔；`delay_h` 在 `:404` 记录延迟。**原始 STRICT 与它完全相同**，所以本项严格口径只增加 60 分钟约束。

| 口径 | n 成交档 | n 事件 | 不可成交事件 | 每份净收益均值 | 每份净收益中位 | 命中率 | result |
|---|---:|---:|---:|---:|---:|---:|---|
| 原口径 = STRICT | 183 | 65 | 0 | +0.0393 | +0.1147 | 0.8415 | 不显著（点估计正） |
| STRICT60 | 43 | 29 | 36 | +0.0381 | +0.1051 | 0.7442 | 仍为不显著（n=29<30） |

事件层（每个事件内各档净收益求和）：原/STRICT 65 事件中位 +0.2194，STRICT60 29 事件中位 +0.2105。成交延迟中位 6.30h，75 分位 13.46h，140/183 超过 60 分钟。

**判定是否翻转**：没有从正翻负，但 60 分钟口径让 36/65 个事件完全不可成交，独立事件降到 29，低于 30 的判定门槛；原结论本来也只是“不显著”，不能因此升级。

### 2.4 quant-021（F1 杆位冠军）

原成交规则：`bots/quant/replay/quant-021/run_replay.py:257` 取成交，`:379-381` 只保留 cutoff 后、正赛前的 taker BUY，并按时间累计 VWAP 到 100 份；主规则用 `exec100`（`:433`）。它已经是“决策后第一笔/前若干笔”，不存 dot 说的决策前前视。

| 口径 | n 事件 | 不可成交事件 | 每份净收益均值 | 每份净收益中位 | 命中率 | result |
|---|---:|---:|---:|---:|---:|---|
| 原口径：cutoff 后累计 100 份 VWAP | 23 | 0 | +0.2003 | +0.5789 | 0.5652 | 不显著（n=23<30） |
| STRICT：cutoff 后第一笔 | 23 | 0 | +0.1994 | +0.5789 | 0.5652 | 不显著 |
| STRICT60：cutoff 后 60 分钟内第一笔 | 19 | 4 | +0.1921 | +0.5789 | 0.5789 | 仍为不显著（n=19<30） |

首笔 taker BUY 延迟中位 0.625h，最大 2.986h；4/23 超过 60 分钟。

**判定是否翻转**：不翻转。严格口径几乎不变，60 分钟口径只少了 4 个事件，点估计仍为正，但样本仍远低于 30，不能写成已证实 edge。

## 3. 汇总结论

| 策略 | 原判定 | STRICT（决策后第一笔） | STRICT60（60 分钟内） | 结论 |
|---|---|---|---|---|
| q020-oos | PASS | PASS（中位 +0.3979，n=47） | INSUFFICIENT（n=12） | dot 的“决策前最后成交”不推翻它；但 60 分钟流动性约束下 PASS 消失 |
| q018-paired | 标准 (1) PASS | PASS（中位 +0.2300） | 点估计 FAIL，整体 INSUFFICIENT（n=1） | 正收益依赖决策后较晚成交；决策时点即时可成交证据不足 |
| quant-012 | 不显著（点估计正） | 同原口径 | 点估计正，但 36/65 事件不可成交，n=29 | 不翻负，但失去 ≥30 事件基础 |
| quant-021 | 不显著（点估计正） | 几乎不变 | 点估计正，n=19 | 不翻转；样本仍不足 |

**总体**：dot 的批评对 q020 和 q018 的**成交口径**是成立的——原 headline 确实用了决策前最后成交。改成“决策后第一笔”后，q020 的 HOLDOUT 和 q018 的标准 (1) 中位数仍然为正；但一旦要求“60 分钟内必须有成交”，两者都无法维持 PASS/30 事件门槛。quant-012/021 原本就使用决策后成交，60 分钟口径下点估计仍为正，但独立事件数分别降到 29 和 19。**本轮没有发现一个在 60 分钟严格可成交口径下仍有 ≥30 独立事件且 PASS 的 Polymarket 策略。**

## 4. 复现命令

在仓库根目录执行（公开、免密钥；原始响应缓存在 `/tmp`，不入库）：

```bash
python3 bots/quant/notes/postdecision-fills-20261021/q020_strict.py | tee bots/quant/notes/postdecision-fills-20261021/q020_strict.out
python3 bots/quant/notes/postdecision-fills-20261021/q018_strict.py | tee bots/quant/notes/postdecision-fills-20261021/q018_strict.out
python3 bots/quant/notes/postdecision-fills-20261021/q012_strict.py | tee bots/quant/notes/postdecision-fills-20261021/q012_strict.out
python3 bots/quant/notes/postdecision-fills-20261021/q021_strict.py | tee bots/quant/notes/postdecision-fills-20261021/q021_strict.out
```

说明：

- q020/q018 使用 `common.py` 的 data-api 抓取器，缓存目录默认 `/tmp/postdecision-fills-cache`，可用 `POSTDECISION_FILLS_CACHE` 改；删缓存后重跑会重新抓公开数据。
- q020 读 `bots/quant/notes/q020-oos/events.csv`；q018 读 `bots/quant/notes/q018-paired/{events,buckets}.csv`；q012 读 `bots/quant/replay/quant-012/trades.csv`。
- q021 复用原回放的 `/tmp/quant-021-cache`（缓存不存在时会按原脚本的公开 URL 重新抓取）。
- 本目录脚本：`common.py`、`q020_strict.py`、`q018_strict.py`、`q012_strict.py`、`q021_strict.py`。输出：`q020_strict.out`、`q018_strict.out`、`q012_strict.out`、`q021_strict.out`，以及逐事件/逐档 CSV `q020_strict_events.csv`、`q018_strict_buckets.csv`。

## 5. 限制

1. data-api 成交打印仍只是“有人以该价成交”的证据，不是当时 L2 深度；60 分钟口径把“没有打印”直接当作不可成交，是保守下界。
2. q020 的 STRICT 用决策后第一笔任一 outcome 打印映射为 YES 等价价，与原脚本的 `yes_price()` 映射一致；不是只看 `BUY Yes`。
3. q018 对 24h 内无打印的档位补抓 `[T, T+10d]` 第一笔；若市场在 10 天后才有成交，仍会被当作不可成交（事件周本身只有 7 天，影响可忽略）。
4. q012 的原成交已经是 t0 后第一笔，所以 STRICT 不可能改变数字；60 分钟口径只是按 `delay_h` 过滤已有成交，不重新选信号。
5. 本轮只复核了上面 4 个；q018-price-test 与 q018-paired 同族，未单独重跑，避免重复计算。
