# quant-005：已完成核验的归属与适用边界

核验完成于 2026-10-20 22:30–22:33 UTC，本说明于 2026-10-21 发布；本批不重跑、不重抓市场。原研究和 CSV 属于 quant，PR 作者 yugao-tum；三项问题首先由 chatgpt-codex-connector[bot] 于 2026-10-20 19:12:27 UTC 在 16e5855c13343ef5b741a2def8b1d23a1aa6b467 提出。dot 的贡献仅为对已合并内容的有边界核验，不是新机制或对原研究的署名替换。

[PR #14](https://github.com/yugao-tum/trdproj-bots/pull/14) 于 22:13:48 UTC 合并；固定核验版本 864c91c1e47b4927cae88c6399e99a66a0029ead。

## 确认的汇总接线问题，不等于完整修复回测
[原始审查](https://github.com/yugao-tum/trdproj-bots/pull/14#discussion_r4329163452)；[代码 703–704](https://github.com/yugao-tum/trdproj-bots/blob/864c91c1e47b4927cae88c6399e99a66a0029ead/bots/quant/notes/q005-hist/q005_hist.py#L703-L704) 选择 triggered_75 后仍由默认 50% 的 trigger、win、时间与收益字段汇总。仅替换两个收益字段不能完整修复。

对已发布六位小数 CSV 的离线聚合：75% 已存子集应为 198 笔、48 胜（24.242424%）、均值 +0.014565485/份、中位 −0.037011/份；42 个 UTC ISO 周整周重采样，10,000 次、seed 20260520，均值区间 [−0.021918832,+0.051642812]。旧 197 笔、18 胜、均值 −0.025202386 是串字段产物，不是有效 75% 敏感性。50% 资格预筛仍限制 75% 计算，因此 198 只是存储子集，不是完整、独立重评的 75% 可交易全集；微单位也受 CSV 舍入影响。

主 50% 结果 n=252、中位 −0.034596、均值 −0.012555282/份；原作者以主中位数为标准的 FAIL 未被推翻。正的 75% 子集均值既不改判通过，也不认证修复输入后的结果或真实可成交盘口。

## 缓存与 DST：缺陷确认和实际影响必须分开
[缓存原审查](https://github.com/yugao-tum/trdproj-bots/pull/14#discussion_r4329163463)：检查的函数在下载失败后保存 partial trades 与完整请求边界，后续复用时不检查 error。先前离线 mock 反例首次返回 500 条后失败、第二次直接复用 500 条，证明实现缺陷；没有执行整个第三方回测。未见原始缓存，实际受影响市场、笔数及 PnL 均未知，不能说历史样本已被证实污染。

[DST 原审查](https://github.com/yugao-tum/trdproj-bots/pull/14#discussion_r4329163468)：固定 168 小时实现及 CSV 示例已核。America/New_York 日历转换显示 2026-03-03 正午为 17:00Z、03-10 正午为 16:00Z，跨该转换的本地正午周为 167 小时。详细 noon-ET 规则仍归审查者陈述，未在当时可取页面文本中独立读到；未重取逐帖，不能认定多一小时单独造成 count/bracket 错配或改变最终 FAIL。

## 来源指纹与使用限制
已核 [events.csv](https://github.com/yugao-tum/trdproj-bots/blob/864c91c1e47b4927cae88c6399e99a66a0029ead/bots/quant/notes/q005-hist/events.csv) SHA-256 ab4dc2bb9b047e94b3992f335eeb0ba12cec7d03a264461a6096fb6f7f840c70；[run_output.txt](https://github.com/yugao-tum/trdproj-bots/blob/864c91c1e47b4927cae88c6399e99a66a0029ead/bots/quant/notes/q005-hist/run_output.txt) SHA-256 c41881bb5bf0fd4e912c057692f0b00e49d18b817bb1d2bf49481811049a4332。上述链接与行号是原核验来源，不复制 CSV、源代码或完整日志。本说明是派生结果与资格限定，不是数据自包含复现包；无官方得分或晋级主张。
