# quant-023 加强版（未提交，已放弃）的 glm-5.3 事实核查报告

# Fact-check report — R023.md (quant-023, MSTR mNAV BTC switch)

**Sources re-fetched (16 fetches): all VERIFIED.** Yahoo MSTR: 1,612 days 2020-05-20..2026-10-19, last close 136.02, split `1723123800 10:1`, max 473.83@2024-11-20, range=max 341 pts/3 splits — exact match, incl. byte size 173,458. Binance: 2026-10-19 close 81,938.4 with microsecond open_time ✓; 2026-10 monthly zip 404/349B ✓; 2026-08..2026-09 closes consistent with B1 final 7.0642 ✓. EDGAR: submissions 157,204B, "Strategy Inc", recent 1,001/210 8-K/15 10-Q/5 10-K, earliest 2021-08-09 ✓; sub001 165,018B/1,029 ✓; EX-99.1 "purchased 21,454 bitcoins at an aggregate purchase price of $250 million" ✓; "As of September 13, 2026… 845,050 bitcoin" ✓; "447,470 bitcoins" (2024 10-K) ✓; "762,099 bitcoins… $51.65 billion" (2026 Q1) ✓; cover shares 267,713,485+19,640,250 ✓; XBRL concepts 404 ✓; stooq 200/796B JS-challenge ✓; strategy.com 403/370B ✓.

**Problems:**

1. **MISMATCH (major, systematic): all CAGR figures are mis-annualized.** `final_run.py` `met()` uses `yrs = (idx[-1] - idx[0]) / 365.25` — trading-day count (panel ≈251/yr), not calendar years. From their own pasted finals: "全样本 CAGR **58.33%**" → true ≈37.2% (6.188y); "R1b…53.01%" → 34.0%; "样本外 CAGR 44.99% 对买入持有 36.74%" → ≈26.9% vs ≈23.9%; per-fold "+190.7%/+38.2%/−13.8%" and "+52pp" alpha likewise wrong. Pre-registered rule "(a) 44.99% > 39.74% ✓" likely flips to fail after fix. Fix: divide by calendar days/365.25 and recompute every percentage (maxDD, switch counts, %days-in-market unaffected; the ABANDON conclusion survives, the numbers don't).
2. **Off-by-one:** "解出 2,484 个交易日（2020-01-01..2026-10-19）" — that span has at most 2,483 calendar days.
3. **Count inconsistency:** "共 **39** 个持仓锚点" but the enumerated list has 37 (script's 39 includes duplicate-value anchors 2021-09-30=114,042 and 2023-02-02=132,500); align list or count.
4. **Re-run (step 3b):** saved all 4 scripts; `build_run.py`/`final_run.py` abort on `FileNotFoundError: mstr_daily.json` / `run_output.json`; `fetch_edgar.py` needs an unprovided `data/filings.json`. Pipeline not reproducible from the log alone — supply the intermediate JSONs or the builder for them.
5. Minor/time-varying: sub001 range "..2021-08-07" vs actual 2021-08-06; XBRL 404 byte sizes drifted (372/350/345 → 352/370/365); 2026-10-20 zip "330 字节" → now 350; "全 74 个月" table has 75 monthly rows; "和公开记忆里的 MSTR 溢价史对得上" should carry the "记忆，未核实" label per GUIDE §10.

**Compliance:** front-matter fields/values all valid (name_zh exactly 18 chars); status 草稿; no keys/paid data (EDGAR contact-UA is proper); Polymarket fee formula N/A; 门槛自查 honest (admits #1, #6 fail); backtests were run (output pasted) — no phantom claims. **Duplication:** none — KNOWN.md and other bots have no MSTR/mNAV; quant-013 (Coinbase premium) and TSMOM entries are different variables; this is an in-place revision of the bot's own quant-023, allowed by GUIDE ("出错就改"); its correction of the prior version (median 0.870, 22/251) matches the existing entry.

VERDICT: FIX — every cited source and quote verifies (much of it byte-exact), but the headline return numbers are systematically mis-annualized and must be recomputed before this can be trusted or submitted.
GATES_PASSING: 5/7 (2,3,4,5,7 pass; 1 and 6 fail as the entry itself admits).
