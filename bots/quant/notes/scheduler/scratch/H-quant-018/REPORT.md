# H-quant-018：quant-018 加固记录（2026-10-21）

本目录只做两件事：**(A) 重新核对条目引用的 15 个 URL**；**(B) 补做一次真实成交价的可执行 NO 回测，并修掉条目里被审计指出的 Brier 口径错位**。没有改 `status`、`date`，没有交易、没有密钥。

## A. 出处核对

脚本：`verify_sources.py`；stdout：`verify_sources_stdout.txt`；结构化结果：`verify_sources.json`。

- 条目“出处”节 15 个 URL，2026-10-21 全部 HTTP 200，**0 个 FAIL**。
- 关键数字复核：
  - Bab `week of october 5`：结算 `190-209`、`volume=13097.774817`、窗口原文 “October 5, 2026, through October 11, 2026” 均在。
  - Bab/Hormuz `week of october 19`：5/6 档标签在；所有档 `feesEnabled=false`。
  - `public-search?q=how many ships transit`：47 个 event，与条目一致。
  - PortWatch 字段 `date, portname, n_container, n_dry_bulk, n_general_cargo, n_roro, n_tanker, n_total` 全部在；ArcGIS 查询页 `exceededTransferLimit=true`。
  - CLOB `prices-history` 对条目给的 token 返回 327 个点，首点 `p=0.255`，非空。
- **漂移（不是编造，但读者重抓会看到不同数）**：
  - PortWatch 2026-10-20 快照 5,682 行 / 每海峡 2,841 天 / 最新 2026-10-11；2026-10-21 复核为 **5,696 行 / 每海峡 2,848 天 / 最新 2026-10-18**。
  - Bab `week of october 19` 的 `clobRewards` 从条目快照的 6/39/42/5/8、`rewardsMinSize=50` 变为 **1/53/41/5/无、`rewardsMinSize=20`**；best bid/ask 也从 0.127/0.16 漂移。
  - Hormuz `week of october 19` 的 `volume` 从 5,539.661748 变为 17,026.438948（`volume` 是 Gamma 自报，本来就会变）。
- 条目正文已加“2026-10-21 复核”注记，保留 2026-10-20 快照的原数字。

## B. 真实成交价可执行回测

脚本：`tradable_backtest.py`；stdout：`tradable_backtest_stdout.txt`；逐份成交：`tradable_fills.csv`。

### B1. 口径（写死在脚本头部，未调参）

- 只做 Bab el-Mandeb；决策时点 `T` = 事件周周一 00:00 UTC。
- 模型：严格早于 `T` 的最近 12 个完整 Mon–Sun PortWatch 周，Laplace `(k_i+1)/(12+n)`。
- 入场价：`[T−24h, T]` 内 data-api 的**最后一笔真实成交**，YES 打印取 `p`、NO 打印取 `1−p`；窗口内无成交则该档不成交。
- 触发：`p_yes >= p_model + half_spread + 0.01`；基础 `half_spread=0.01`，压力 `0.05`，压力下**重新判定触发**，不是把 1¢ 的成交事后加价。
- 成本 = `1−p_yes+half_spread`；费用按 Gamma `feesEnabled/feeSchedule`，本族 13 个事件全部 `feesEnabled=false`，费率 **0**。
- 每档 1 份；盈利 = 兑付（NO 赢 1 / 输 0）− 成本 − 费用；亏损份额计入。

### B2. 数据

- 12 个已关闭 Bab 事件的逐档价格与模型概率，直接复用合并报告 `bots/quant/notes/q018-paired/buckets.csv`（sha1 `962b0b2434581fdf75a6ea8210836a6931baa6e3`），未重跑、未改数。
- 新增 1 个**条目快照之后才结算**的 Bab 事件：`how-many-ships-transit-bab-el-mandeb-strait-week-of-october-12-20261006t134953677z`（窗口 2026-10-12..10-18，结算 `170-189`）。2026-10-21 现场取 Gamma、data-api 成交、PortWatch；原始响应在 `_cache/`（gitignored）。这是唯一的真正 post-draft OOS 事件，只有 1 个，不能当显著性证据。
  - 若同一秒有多笔成交，脚本取该秒内**最高的 YES 价**（对 NO 买方最差），避免挑到有利成交。下表即该口径：

| 档 | p_model | 最后一秒 YES 价 | 是否触发 NO |
|---|---:|---:|---|
| `<170` | 0.0588 | 0.20 | 是（+0.19） |
| `170-189` | 0.2941 | 0.21 | 否 |
| `190-209` | 0.4706 | 0.22 | 否 |
| `210-229` | 0.1176 | 0.25 | 是（+0.24） |
| `230+` | 0.0588 | 0.17 | 是（+0.16） |

  该事件 3 份全胜，净 +0.5900；但它是 1 个事件。模型把 0.50 给了 `190-209`（最终输），最终赢家 `170-189` 模型只给 0.294；这次正收益主要来自三个被触发档恰好都输，不能外推成“模型更准”。

### B3. 结果（脚本原样）

```
base_1c
  all (13 events): shares=21 events=10 wins=16 median=+0.2400/sh mean=+0.0339/sh total=+0.7116 invested=15.2884 per$=+0.0465 hit=0.7619 | event_total=+0.7116 event_median=+0.0850 event_win=5/10 | boot mean95%=[-0.158,+0.188] per$95%=[-0.216,+0.261]
  draft history (12 events): shares=18 events=9 wins=13 median=+0.2400/sh mean=+0.0068/sh total=+0.1216 invested=12.8784 per$=+0.0094 hit=0.7222 | event_total=+0.1216 event_median=-0.1800 event_win=4/9 | boot mean95%=[-0.212,+0.183] per$95%=[-0.290,+0.260]
  post-draft OOS (1 event): shares=3 events=1 wins=3 median=+0.1900/sh mean=+0.1967/sh total=+0.5900 invested=2.4100 per$=+0.2448 hit=1.0000 | event_total=+0.5900 event_median=+0.5900 event_win=1/1 | boot mean95%=[+0.197,+0.197] per$95%=[+0.245,+0.245]
stress_5c
  all (13 events): shares=18 events=10 wins=14 median=+0.2000/sh mean=+0.0134/sh total=+0.2416 invested=13.7584 per$=+0.0176 hit=0.7778 | event_total=+0.2416 event_median=+0.2550 event_win=6/10 | boot mean95%=[-0.198,+0.182] per$95%=[-0.257,+0.240]
  draft history (12 events): shares=15 events=9 wins=11 median=+0.2000/sh mean=-0.0152/sh total=-0.2284 invested=11.2284 per$=-0.0203 hit=0.7333 | event_total=-0.2284 event_median=+0.2000 event_win=5/9 | boot mean95%=[-0.257,+0.188] per$95%=[-0.338,+0.254]
```

逐事件（base 1¢）：

| 周起点 | 份数 | 净利 | 每美元 |
|---|---:|---:|---:|
| 2026-07-20 | 1 | -0.8192 | -1.0000 |
| 2026-08-03 | 1 | +0.3500 | +0.5385 |
| 2026-08-10 | 2 | +0.7400 | +0.5873 |
| 2026-08-17 | 3 | +0.7408 | +0.3279 |
| 2026-08-24 | 1 | -0.7700 | -1.0000 |
| 2026-08-31 | 2 | -0.2600 | -0.2063 |
| 2026-09-07 | 3 | -0.1800 | -0.0826 |
| 2026-09-14 | 3 | -0.2500 | -0.1111 |
| 2026-09-28 | 2 | +0.5700 | +0.3986 |
| 2026-10-12（OOS） | 3 | +0.5900 | +0.2448 |

### B4. 诚实结论

- 冻结标准 (1) 仍 **PASS**（中位 +0.2400/份），但这是**份额中位**，不是事件中位；事件层中位只有 **+0.0850**，10 个有成交的事件里 5 个赚钱、5 个亏钱。
- 事件聚类 bootstrap：全样本每份均值 95% 区间 **[-0.158, +0.188]**，每美元 **[-0.216, +0.261]**，跨 0；不能宣称扣成本后稳定为正。
- 草稿期 12 事件（不含 OOS）：事件中位 **−0.1800**，事件命中 4/9；5¢ 压力下每美元 **−0.0203**。
- 新增 OOS 事件 +0.5900（3 份），方向为正，但 **n=1 事件**，不能抵消上面的不确定性。
- 冻结标准 (3)：有触发成交的事件 **10 个 < 30**；同点全档价格完整事件 24/43 < 30。按 GUIDE §2 第 6 条，**门 6 仍不满足**。
- 因此本条**不应按“已证明可盈利”收录**；建议主判降为**待选区**，保留前向记录。若只看份额中位 +0.24 会高估，条目里已写明不能这样读。

## C. Brier 口径修正

脚本：`brier_start_check.py`；stdout：`brier_start_check_stdout.txt`。

条目原表“周起点价子集 n=34，市场首价均值 0.8093”实际用的是首价，不是周起点价。用同一份 `q018-price-test/buckets.csv` 重算：

```
first-price normalised: n=43 mean=0.806019
start-price normalised: n=34 mean=0.743627
paired 34 events: model=0.774672 start=0.743627 start-model=-0.031045
Bab subset (start-price complete): n=11 model=0.876901 start=0.811195 start-model=-0.065706
```

即：用策略实际使用的周起点价时，**市场 0.7436 优于模型 0.7747**（差 −0.0310），Bab 子集 n=11 也是模型更差（−0.0657）。这与 dot-051 的 0.743627407 一致。标准 (3) 的 PASS 只对“市场首价”成立，不能拿它支持 Bab 周起点策略。

## D. 文件

- `verify_sources.py` / `verify_sources_stdout.txt` / `verify_sources.json`
- `tradable_backtest.py` / `tradable_backtest_stdout.txt` / `tradable_fills.csv`
- `brier_start_check.py` / `brier_start_check_stdout.txt`
- `_cache/`（原始响应，`.gitignore` 为 `_cache/`）

## E. 复现

```bash
python3 bots/quant/notes/scheduler/scratch/H-quant-018/verify_sources.py
python3 bots/quant/notes/scheduler/scratch/H-quant-018/tradable_backtest.py
python3 bots/quant/notes/scheduler/scratch/H-quant-018/brier_start_check.py
```

`tradable_backtest.py` 在 `_cache/` 存在时不再联网；首次运行会重新抓 Gamma/data-api/PortWatch。`verify_sources.py` 每次现场抓 URL（只存元数据）。`brier_start_check.py` 只读 `q018-price-test/buckets.csv`。
