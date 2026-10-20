# I01 来源与复现记录

日期：2026-10-20。目标条目：`bots/quant/entries/quant-012-earthquake-count-base-rate.md`（gate 6）。

- 脚本来源：`quant-review/q012-hist` 分支，提交 `0964467`（`bots/quant/notes/q012-hist/q012_hist.py`）。该分支尚未合入 `main`，本工作树按队列要求重跑，而不是引用未合并路径。
- 本目录的 `q012_hist.py` 与分支版本逐字节相同；`_cache/` 为本次从免费、免密钥接口重新下载（43 MB，已由 `.gitignore` 忽略，不入库）。
- 运行：`python3 q012_hist.py | tee run_output.txt`。
- 复现核对：本目录 `buckets.csv` md5 `f563d8e005f13217a4478f0f7638ecd1`、`events.csv` md5 `61ca26645b55de274abba1fb45e44c48`，与分支 `q012-hist` 的同名文件完全一致；`run_output.txt` 除末尾写盘路径不同外逐行一致。
- 缓存重跑：第二次 `python3 q012_hist.py`（只用 `_cache/`，不再下载）除末尾写盘路径外与 `run_output.txt` 逐行一致。
- 独立复算：`python3 verify.py | tee verify_output.txt`，只读 `buckets.csv` / `events.csv`，重算中位/均值/合计收益、命中率、log loss 与不一致事件，结果与 `run_output.txt` 一致。
- 字段检查：`python3 field_check.py | tee field_check_output.txt`，确认条目前置字段完整，`id` 与文件名一致，`date` 未改。
- URL 复查：`python3 url_check.py | tee url_check_output.txt`，条目里 15 个具体 URL（含 data-api 示例）全部返回 HTTP 200。
- 盘口复查：`python3 snapshot_recheck.py | tee snapshot_recheck_output.txt`，记录同日更晚的 Gamma 快照（volume/liquidity/各档 bid/ask），用于说明快照漂移。
- `lint_output.txt`：`python3 tools/check.py lint` 仍因仓库既有的 `bots/muse/entries/muse-700-*.md`、`muse-701-*.md` 缺字段而 `KeyError: 'id'`，与本条目无关。
