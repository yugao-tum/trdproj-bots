## 做了什么

用 Wayback CDX 快照恢复历史“当时已出评论数 `(k, m)`”，用 data-api 已关闭市场真实成交构造可成交价，对 quant-016（RT All Critics Tomatometer 累积阈值链，Beta-Binomial）做了历史回测。

- Universe：Gamma `tag_slug=rotten-tomatoes&closed=true` 全量 **85 个 event / 530 个 market**；日期跨度 **2026-03-02 .. 2026-10-19**（另 1 个 `mufasa` `endDate=null`，`closedTime=2024-12-23`）。
- 映射：RT 搜索页完全同名片名 + 上映年最接近，**85/85 映射成功**；`mufasa` 区间写法整 event 排除（5 个 market）。
- 快照：CDX 主窗口 `[T−72h, T−12h]` 有可用快照 **73** 个；敏感性 `[T−7d, T−24h]` **80** 个；无主快照跳过 **11** 个。主快照滞后中位 **30.70h**。
- 模型：`Beta(k+1, m+1)`，`P(floor(100p) ≥ T)=1−I_{T/100}(k+1,m+1)`；快照有显示分时“到期无分数”尾部设为 0（73/73 都有分，实际未触发）。
- 成交价：`[t−6h,t]` 最后一笔 data-api 成交换算 YES 价，`ask=mid+1¢`、`bid=mid−1¢`，保守 taker；费 `0.05×p×(1−p)`；edge 需超过 `费+半价差+2¢`；持有到 Gamma 结算。
- 独立结果 1 event = 1 个；event-cluster bootstrap 10,000 次，seed 20261021。

## 验证命令

```bash
cd bots/quant/notes/q016-hist
python3 q016_hist.py > run_output.txt
sha256sum run_output.txt events.csv
```

从 `_cache/` 连续重跑两次，`run_output.txt` 与 `events.csv` 均逐字节一致：

- `run_output.txt`：`dbfce42c1e03c802eecf3a8e719068e703ea2ba18bf86b97375fdd060058a9fa`
- `events.csv`：`d0e9121aebadb6e5a8872294aef06b38f1e9f15b6ad7e07e99d02083a1628065`

## 关键结果（复制自 `run_output.txt`）

```
-- primary window [T-72h, T-12h], price [t-6h, t]
   independent priced events=66  scored thresholds=192
   triggered trades=92  events/triggered=52  YES=40  NO=52
   median event net/share=-0.113876  mean event net/share=-0.079474
   event-cluster bootstrap 95% CI of mean: [-0.168443, +0.017816]
   median trade gross/share=-0.034787  median trade net/share=-0.036465  mean trade net/share=-0.044920
   hit rate (net>0)=9/92 = 0.098
   total net=-4.132638 on staked=12.708319 -> per $ staked=-0.325192
   Brier  model=0.066637 market=0.035369 diff=+0.031268
   LogLoss model=0.214928 market=0.121872 diff=+0.093056
   event-level Brier model=0.070931 market=0.039374  LogLoss model=0.226112 market=0.135803
-- sensitivity [T-7d, T-24h], price [t-6h, t]
   independent priced events=73  scored thresholds=218
   triggered trades=103  events/triggered=57  YES=49  NO=54
   median event net/share=-0.104500  mean event net/share=-0.071619
   event-cluster bootstrap 95% CI of mean: [-0.168442, +0.031436]
   median trade gross/share=-0.041000  median trade net/share=-0.042966  mean trade net/share=-0.039634
   hit rate (net>0)=14/103 = 0.136
   total net=-4.082294 on staked=17.535528 -> per $ staked=-0.232801
   Brier  model=0.070161 market=0.045723 diff=+0.024439
   LogLoss model=0.224015 market=0.149771 diff=+0.074244
   event-level Brier model=0.076955 market=0.055868  LogLoss model=0.242717 market=0.177844

snapshot lag T-t: median=30.70h min=12.86h max=69.02h
primary snapshots with displayed score: 73/73
snapshot score equals final settlement interval (exact YES-range): 51/73  (all-NO events consistent with below-min: 11/12)
```

**VERDICT: FAIL**。66 个独立 priced event（≥30），模型 Brier/log loss 均差于市场，event 净中位与已成交份额毛利中位均为负；敏感性窗口同样为负。因此 gate 5 不通过；gate 6 的方法障碍（历史评论数取不到）已被 Wayback 解除，但策略本身仍未通过冻结标准，不应升级。

## 局限

- **Wayback 时点偏差**：主快照滞后中位 30.70h（12.86–69.02h），模型不是用结算前最后一刻的评论数；CDX 覆盖稀疏时窗口内向前回退会进一步加大偏差。
- **快照分 ≠ 结算分**：51/73 精确落入最终区间；11 个全 NO 低于最低档（一致），10 个漂移 + 1 个全 NO 但快照分不低于最低档。条目担心的“早期评论选择偏差”正是主要失败原因。
- **无分数尾部未检验**：73/73 主快照都有显示分，`q0=0` 实际生效；“到期无数据 → 全 NO”尾部未在本样本触发。
- **成交价近似**：只有 data-api 成交打印，没有 L2 历史；用最后成交 ±1¢ 近似 taker touch，未建模滑点/成交量；条目原提案是 maker，maker 排队与逆向选择仍未量化。
- **样本相关性**：66 个 priced event 中 52 个触发；同片各阈值高度相关，bootstrap CI 仍宽。
- **区间写法**：`mufasa` 的 5 个 market 按条目“不做区间写法”整 event 排除。
