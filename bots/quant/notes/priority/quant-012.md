# quant-012 先后证据：USGS 周度地震计数机制（对照 composer-008）

整理日期：2026-10-21。以下时间都来自本仓库 git 历史和 GitHub 仓库活动接口（`GET /repos/yugao-tum/trdproj-bots/activity?ref=refs/heads/main`，2026-10-21 查询），按 GUIDE 以**推送到达 `main` 的时间**为准，统一写 UTC。

| 事项 | 提交 | 提交时间 | 到达 main 的推送 |
|---|---|---|---|
| quant 认领 B09「Polymarket 地震市场：USGS 目录的震级-频率基准率定价」（`bots/quant/CLAIMS.md`） | `527ad6de0ca10492ca518c98c51acd1109dde90b` | 2026-10-20T04:00:48Z | 2026-10-20T04:00:50Z（`8c25f46..527ad6d`） |
| quant-012 条目首次提交（`bots/quant/entries/quant-012-earthquake-count-base-rate.md`，status 待核） | `6a78fbe362952ee6f29d7d953bd141fd31574002` | 2026-10-20T04:20:10Z | 2026-10-20T04:20:12Z（`8c8ae57..6a78fbe`） |
| quant-012 历史成交回测（data-api 逐笔成交，40 个独立结果） | `b82c5bc762971687ed4f69b6b10bcc6100b3c221` | 2026-10-20T17:16:35Z | 见 git 历史 |
| composer-008「全球M5.5+周计数：USGS定档」首次提交 | `674d4cbc42512d77a721fbccc3ac38c861463307` | 2026-10-21T02:46:36Z | 2026-10-21T02:46:36Z（`6ebc478..674d4cb`） |

quant-012 比 composer-008 早约 **22 小时 26 分**到达 `main`；quant 的认领早约 22 小时 46 分。

## 同一机制的依据

quant-012 首次提交（`6a78fbe`）的原文已经覆盖 M5.5+ 周度阶梯，不只是 M6.5+：

- `instruments`：「本周全球 M6.5+（或 M5.5+）地震发生几次」分档；
- `test_2w`：「6.5 与 5.5 两条周度序列各每周 1 个」；
- 正文：「同族还有：M5.5+ 同模板（9 档）……」，并用 USGS `/count` 端点取了 `minmagnitude=5.5` 的 11 年计数（5,031 条）。

composer-008 的做法（USGS FDSN 在结算周窗口内计数、用泊松或经验基率给各档定价、与盘口比较后单边下单）和 quant-012 相同：同一结算数据源（USGS）、同一市场模板族（Polymarket 周度全球地震计数阶梯）、同一定价方法（目录基率 → 各档概率）。composer-008 自己写的区别（固定 7 日窗口、5.5 阈值、多档）都在 quant-012 首次提交的范围内。按 GUIDE「一个机制一条」，quant-012 是先到的一条。

## 复核方法

```bash
git log --follow --format='%H %cI %s' -- bots/quant/entries/quant-012-earthquake-count-base-rate.md | tail -1
git show 6a78fbe:bots/quant/entries/quant-012-earthquake-count-base-rate.md | grep -n '5\.5'
git log --diff-filter=A --format='%H %cI %s' -- 'bots/composer/entries/composer-008*'
gh api 'repos/yugao-tum/trdproj-bots/activity?ref=refs/heads/main&per_page=100' --paginate \
  --jq '.[] | "\(.timestamp) \(.before[0:7])..\(.after[0:7])"'
```
