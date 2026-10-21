# USGS M5.5+ 周计数回放（T08b，2026-10-21）

脚本：`notes/usgs_weekly_55_replay.py` → `notes/cache/usgs_weekly_55_replay.json`

## 结果（UTC 窗口近似 ET 周）

| 可评分 | USGS 与结算档一致 |
|---:|---:|
| 5 | **3** |

## 说明

- 档位结构因周而异（例 `≤3…9, >9` vs `≤6…>13`）；脚本按 **精确数字 → `>` → `≤`** 映射。
- 不一致多出现在 **ET 边界 vs USGS `starttime/endtime` UTC**（例 4/13 周 USGS=9、结算 `>9`）。
- 008 前向仍应以 **Gamma 描述 ET 窗口** 为准，API 仅辅助。

复现：`python3 notes/usgs_weekly_55_replay.py`
