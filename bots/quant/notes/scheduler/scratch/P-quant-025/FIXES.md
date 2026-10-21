# P-quant-025 / quant-025 — fixer changelog

Date: 2026-10-21 (UTC). Target: `bots/quant/entries/quant-025-spc-tornado-outlook-lag.md`.
Filename, `id: quant-025`, `date: 2026-10-20` and `status: 草稿` unchanged. No other repository file touched in the R1 fix; the round-2 addendum below adds `bots/quant/replay/quant-025/`.

Files read for this fix:
- `bots/quant/notes/scheduler/reviews/c20261020-1423-research.md` (B22 section and both re-checks)
- `bots/quant/notes/scheduler/checks/B22.md` (all sections; B22 = quant-025)
- `bots/quant/notes/scheduler/checks/B23.md` (only mentions quant-025 as a different mechanism; no action)
- `bots/quant/notes/scheduler/audit/c20261021-030001-research.md` (S6, S10, table row)
- `bots/quant/notes/scheduler/queue.tsv` (P-quant-025 note)

All scripts and stdout are under this directory. `_cache/` is gitignored and every file is < 1 MB.

## Re-run (from an empty cache)

```bash
python3 fetch_outlooks.py     # events 63 / markets 1575 (2026-10-21 live); then filter to entry sample
python3 filter_62.py          # kept 62 events, 2026-08-19..2026-10-19, 1550 markets
python3 fetch_headers.py      # rows 186, status {200: 186}
python3 classify.py           # markets 1550, final mismatch 0, 10 YES / 1540 NO, 6 events with >=1 YES
python3 fetch_trades.py       # 1550/1550 markets, 10,674 trades
python3 reproduce.py          # strict 6/3, cost $16.03, net +$658.23; broad 10/7, cost $16.93, net +$674.71
python3 verify_sources.py     # all 10 cited URLs HTTP 200; sizes / ranges / capacity arithmetic
python3 verify_rules.py       # Aug-19 and Sep-30 live rule text
python3 verify_trades.py      # Wichita / Columbus trades cited in the entry
```

The fresh run matches the entry: 62 events / 1,550 markets / 10,674 trades / 0 settlement mismatches / 10 YES / 6 events with YES / 1630→2000 0 flips / 2000→final 5 flips / 15→10 (66.7%). Strict and broad P&L match the numbers in `scratch/B22/reproduce.out`.

## Problems -> changes -> evidence

1. **Rule 4 entry text contradicted the script** (checks/B22 §7.1; audit S6).
   Old: “第一笔 `BUY Yes` ... 若第一笔不是 `BUY Yes` 或价格 >0.25，则跳过” — read literally, a preceding `SELL Yes`/`BUY No` blocks entry, which would drop Indianapolis 8/26 and Wichita 9/30 and change strict to 4 trades / +$646.55.
   Changed to: “窗口内第一笔 `BUY Yes` 成交（之前的 `SELL Yes`/`BUY No` 不计），价格 ≤0.25；若窗口内没有 `BUY Yes` 或该笔价格 >0.25，则跳过”。 This matches the 6-trade script.
   Evidence: `reproduce.out` (`strict BUY YES: trades=6 events=3 ... net=$658.23`); the 6 strict fills include Wichita 16:50:35 `BUY Yes` and Indianapolis 20:46:03 `BUY Yes` after earlier opposite-side trades.

2. **Risk size range was wrong** (checks/B22 §7.2).
   The check saw “5–185 份”; the checked-out file had already been partly changed to “单笔 20–300 份”, which still missed the broad minimum (4.99).
   Changed to: “单笔 5–300 份（宽口径最小 4.99、最大 300；严格 20.01–300）”.
   Evidence: `verify_sources.out` — strict size min/max 20.01/300; broad size min/max 4.99478/300.

3. **Gate 3 was mis-classified as “不满足”** (audit S10).
   GUIDE §2 gate 3 asks whether ~5,000 USDT can do it (per venue ≤~2,500) and whether capacity is written down, not whether 5,000 can be fully deployed. The entry already caps $50/market, $250/day, $2,500/venue.
   Changed gate 3 to **“满足（容量很小）”**, with the $16/$17 full-sample and ~$2.6–2.7/day (10×) numbers kept as capacity caveats. Moved the economic-capacity point into “成本与容量” and gate 5, and clarified that it is an economic-capacity flaw, not a small-capital threshold failure.
   Evidence: `verify_sources.out` capacity arithmetic (`16.93×10/62 = $2.73/day`; `16.03×10/62 = $2.59/day`; `9.61×10 = $96.10` max-day upper bound); GUIDE.md §2 gate 3.
   Note: checks/B22 still said gate 3 “不满足”; the later audit (2026-10-21 03:00) explicitly identifies that as a misjudgment and prescribes this wording. The later audit is followed here.

4. **One “verbatim” settlement quote was not verbatim** (found by this re-fetch).
   Old: “If **a** city's coordinates fall inside ...”.
   Live Aug-19 Chicago rule: “If **the** city's coordinates fall inside ...”.
   Changed one word to “the”. This is the only quote mismatch; the other five quoted sentences are exact.
   Evidence: `verify_rules.out` — with the corrected wording the sentence is `QUOTE_PRESENT` on the Aug-19 market, and the old “a city's” variant is `OLD_A_VARIANT_ABSENT`; the other five Aug-19 quotes are `QUOTE_PRESENT`.

5. **Queue asked for a historical tradable-price backtest net of fees.**
   The backtest already existed and is reproducible. Added an explicit label at the top of “证据” saying it is an executed-fill (tradable-price) replay using data-api trades, net of 0.05 taker fee + 1¢/share buffer, and that it does not prove we could get the same price/size.
   Evidence: `reproduce.out`; `verify_trades.out` (Wichita 16:33:41 SELL Yes 0.05×38 and 16:50:35 BUY Yes 0.08×20.1; Columbus 16:57:25 BUY Yes 0.01×42).

6. **Sources re-verified, and the sample snapshot has moved.**
   All 10 cited URLs returned HTTP 200 on 2026-10-21; SPC values match (1630 updated 16:26:43 UTC, 2000 19:58:05, final 00:35:04; 1630 zip Last-Modified 16:30:16; Sep-30 volume 4,935.376533; fee 0.05/takerOnly/rebateRate 0.25).
   Live Gamma now has **63** closed events (2026-10-20 added). The entry sample is kept at the verified 62 events (2026-08-19..2026-10-19); added a dated snapshot note so a future checker does not read 63 as a mismatch.
   Evidence: `verify_sources.out`; `verify_numbers.out` (62 events × 25 markets, volume sum 410,598.793553, 1,550/1,550 `restricted=true`, 1,550/1,550 fee rate 0.05); `issue_range.out` (62 sample final files: ISSUE 00:28–01:37 UTC, Last-Modified 00:35–01:41 UTC).

7. **Verdict written plainly in the entry.**
   Added “本轮结论：不应丢弃” — keep as a 待选区 candidate, not a this-round `待核` promotion. It is not dropped because the mechanism, free data and sources hold; it cannot be promoted because gate 6 is structurally unmet (3–7 independent low-price signals) and gate 5 is uncertain (one day = 94.7% of strict PnL, capacity ~$17/62 days).

## Gate verdict after fix

| Gate | Verdict | Reason |
|---|---|---|
| 1 mechanism | 满足（持续解释弱） | SPC 2% geographic area vs literal 2%; payer clear; persistence only weakly explained |
| 2 data | 满足（仅前向记录替代口径） | free keyless data; history has only 6 events with YES / 7 broad / 3 strict signals |
| 3 small capital | 满足（容量很小） | $50/market, $250/day, $2,500/venue fit; economic capacity ~$17/62 days |
| 4 not duplicate | 满足 | SPC polygons vs site temperature / GISTEMP / USDM; different payer |
| 5 net of cost | 不确定 | in-sample +$658.23 strict / +$674.71 broad, but 3 event-days, 9/30 = 94.7%, fill-price proxy |
| 6 two-week test | **不满足** | 1–2 signals per two weeks; 30 independent signals need ~8–9 (broad) / ~20 (strict) months |
| 7 sources | 满足 | all 10 URLs HTTP 200, rules/scripts re-runnable, ISSUE range correct |

## Open problems

- Gate 6 is structural; no text fix can create 30 independent events in two weeks.
- Gate 5 remains uncertain: the positive P&L is one event-day and uses executed fills, not order-book depth.
- Capacity (~$17 over 62 days) is an economic flaw; it does not block gate 3 but makes the strategy undeployable at 5,000 USDT.
- Recommendation: keep as 待选区候选 (草稿), do not promote this round and do not drop.

---

## 第 2 轮补丁（2026-10-21，w06，P-quant-025）

问题：条目缺第 2 轮 8 个字段与 `replay/quant-025/`；`result` 若照样本内正收益写 `正` 会违反 GUIDE §7 的“独立结果 ≥30”；旧文还有一处数据风险说法与本次复跑不符。

1. **缺 8 个字段** → 在 front matter 补：
   - `evidence: 回放`、`result: 不显著`、`slot: 新机制`、`variants: 4`、`variants_ext: -`、`window: 2026-08-19..2026-10-19`、`max_dd: -`、`contribution: 77.5%`。
   - 证据：`GUIDE.md` §2.1/§7、`templates/ENTRY.md`；`result` 按严格 6 笔/3 个独立日、宽 10 笔/7 个，均 <30（`replay_results.json`）。`slot` 与 `kind: new` 一致；草稿不占名额（lint 仅提示）。
2. **没有回放目录** → 新建 `bots/quant/replay/quant-025/`：`run_replay.py` 从零抓取并跑完，`reproduce.py`/`reproduce.out`/`replay_results.json`/`SUMMARY.md` 与 5 个抓取/分类脚本；`_cache/` 已 `.gitignore`，仓库文件均 <1 MB。
   - 证据：`run_replay.out`（2026-10-21 从空缓存起跑，57.6 秒；62 事件/1,550 市场/10,674 笔成交/0 结算不一致；严格 6 笔/3 日 +$658.23、宽 10 笔/7 日 +$674.71）。
3. **`result` 只能是不显著** → 在“证据”开头和第 2 轮字段说明写死：独立结果 <30，样本内 +$658.23 只是点估计，不能记 `正`；结论也改成“可作待核候选、预期最多待选区”。
   - 证据：`GUIDE.md` §7 result 定义；`replay_results.json` 的 `strict.events=3`、`broad.events=7`。
4. **`contribution` / `max_dd` 缺** → 写 `77.5%`（严格：`658.23 ÷ 5,000 × 365/62`；宽口径 79.4%）并在“成本与容量”写明算法和容量 caveat；Polymarket 的 `max_dd` 按模板写 `-`，并注明未构造逐日权益、不是“没测”。
   - 证据：`replay_results.json` 的 `contribution_strict_pct=77.5`、`contribution_broad_pct=79.44`、`max_dd="-"`。
5. **旧数据风险句“Last-Modified 晚 30–60 分钟”与实测不符** → 改为“本轮 186 个文件 `Last-Modified − ISSUE` 为 3.1–31.3 分钟（中位 6.2）”。
   - 证据：`fetch_headers.py` 本次输出：`delay minutes min/median/max 3.1 6.2 31.3`（`replay/quant-025/run_replay.out`）。
6. **来源与数字再核** → 2026-10-21 05:14–05:16 UTC 重抓 10 个引用 URL，全部 200；Gamma live 已 63 个 closed event，样本仍固定 62 个（2026-08-19..2026-10-19），条目已有快照说明；SPC 1630/2000/final 的 Updated 与 Last-Modified 未变。
   - 证据：`verify_sources.out`（本次重跑；series 200/46,687B、events 200、SPC 200、data-api 200）；`reproduce.out` 与本轮重跑逐项一致。
7. **`data` 字段的“每市场最近约 2 万笔”无法核实** → 改为“data-api 逐笔成交（免费免密钥；本样本每市场 1–27 笔）”。证据：本次 1,550 个成交文件，单市场最少 1 笔、最多 27 笔、合计 10,674 笔（`reproduce.out` 与 `_cache/trades/*.json`）。
8. **结论写明白** → “不应丢弃”：机制/数据/出处成立，回放已交；但门 6 结构性不满足（3–7 个独立信号），门 5 不确定，容量约 $17/62 天，预期最多待选区，不能按收录处理。

第 2 轮补丁只改：`bots/quant/entries/quant-025-spc-tornado-outlook-lag.md`、`bots/quant/replay/quant-025/**`、本文件与 `scratch/P-quant-025/` 下已有脚本/输出。`status: 草稿`、`date: 2026-10-20`、文件名和 `id` 未动。

---

## 第 2 轮复核修正（2026-10-21，f1-04，P-quant-025）

读取的复核/核查文件：`reviews/c20261021-070001-research.md`（P-quant-025 节，VERDICT: FIX）、`reviews/c20261020-1423-research.md`（B22 三次核查）、`checks/B22.md`、`audit/c20261021-030001-research.md`（S6/S10）、`audit/c20261021-070001-research.md`。文件名、`id: quant-025`、`date: 2026-10-20`、`status: 草稿` 均未变。

1. **复核第 2 条：`待核` 候选的措辞可能被误读为可按收录提交** → 把“本轮结论”改为“只按新机制名额候选（`slot: 新机制`），不得按收录/已验证收益提交；前向记录 8–9 个月后再复核。是否占用本轮名额由 integrator 决定。”保留“不应丢弃”，因为机制/数据/出处成立，回放也可复现。
   - 证据：`reviews/c20261021-070001-research.md` P-quant-025 第 2 条；`replay_results.json` 的严格 3 个独立日/宽 7 个，均 <30。

2. **复核第 3 条：门 3 需要明确“容量极小、77.5% 不是 5,000 账户可实现贡献”** → 在门 3 的判断里补“（容量极小，约 $17/62 天；不能把 77.5% 当 5,000 账户可实现的贡献）”；门 3 仍为满足（小资金门槛），容量问题留在“成本与容量”和门 5。
   - 证据：`GUIDE.md` §2 门 3；`verify_sources.out` 容量算术（严格放大 10 倍 $2.59/日，宽 $2.73/日，最大单日上限 $96.10）。

3. **复核第 4 条：`contribution: 77.5%` 是样本内算术** → “成本与容量”的年化贡献句改为“这是**样本内、仅约 $16 投入**的算术”，并保留“不是预期，也不代表能把 5,000 部署出去；`result` 仍是不显著”。
   - 证据：`replay_results.json`（strict net +$658.23、cost $16.03；broad +$674.71、cost $16.93）；条目 `:113`。

4. **复核第 5 条：`result: 不显著`、`name_zh` 15 字、8 字段有效** → 未改数值/字段；`result` 仍为 `不显著`（严格 6 笔/3 日、宽 10 笔/7 日，均 <30）。`evidence: 回放`、`slot: 新机制`、`variants: 4`、`variants_ext: -`、`window: 2026-08-19..2026-10-19`、`max_dd: -`、`contribution: 77.5%` 与 `bots/quant/replay/quant-025/SUMMARY.md` 一致。
   - 证据：`python3 tools/check.py lint --bot quant` → 问题 0 个；`replay/quant-025/SUMMARY.md`。

5. **复核第 1 条：门 5/门 6 的结论** → 未改结论；门 5 仍“不确定”（2026-09-30 占严格 PnL 的 94.7%），门 6 仍“不满足”（3–7 个独立信号，30 个需 8–9/20 个月前向）。第 1 条要求的是不要把当前 3 天样本当 PASS，这正是条目现在的写法。
   - 证据：`replay_results.json`、`reproduce.out`（`strict max event cost=$9.61; event PnL: 2026-09-30:+623.63`）。

6. **回放从零复跑（本轮）** → 在 `bots/quant/replay/quant-025/` 重新抓取并重跑。首次运行 `day1otlk_20260930_0100_torn.nolyr.geojson` 遇到一次 HTTP 502，重跑后 189/189 个 GeoJSON 全部取到；为让回放可重复，给 `fetch_outlooks.py` 和 `fetch_headers.py` 加了 3 次重试（只改重试，不改参数/成交/成本逻辑）。最终 `run_replay.py` 返回 0，62 事件/1,550 市场/10,674 笔/0 结算不一致；strict 6 笔/3 日、成本 $16.03、净 +$658.23；broad 10 笔/7 日、成本 $16.93、净 +$674.71。
   - 证据：`replay/quant-025/run_replay.out`、`reproduce.out`、`replay_results.json`（本轮重跑后内容与条目逐项一致）；`replay/quant-025/fetch_outlooks.py`、`fetch_headers.py` 的重试代码。

7. **来源复核（本轮）** → 10 个引用 URL 全部 HTTP 200；Gamma live 仍 63 个 closed event（2026-10-20 新增），样本固定 62 个（2026-08-19..2026-10-19）；Sep-30 volume 4,935.376533、费率 0.05/takerOnly/rebateRate 0.25、resolutionSource 不变；SPC 1630/2000/final 的 Updated 与 1630 zip 的 Last-Modified 16:30:16 不变；Aug-19 六条规则引文逐字存在，Sep-30 版本的缺数据兜底/修订截止也逐字存在；final ISSUE 00:28–01:37、Last-Modified 00:35–01:41。
   - 证据：`verify_sources.out`、`verify_rules.out`（本目录，2026-10-21 重跑）。

结论：**不应丢弃**，但也不满足七门 PASS；保持 `status: 草稿`。可作第 2 轮新机制名额候选（`slot: 新机制`），前提是 integrator 接受 3–7 个独立日的样本；不得按“已验证收益/收录”提交。前向需 8–9 个月（宽）或约 20 个月（严格）才能到 30 个独立信号。
