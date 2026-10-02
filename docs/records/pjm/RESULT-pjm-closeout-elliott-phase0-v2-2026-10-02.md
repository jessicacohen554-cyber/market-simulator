# RESULT — PJM close-out Elliott phase 0 v2 (E1a–E1e): FAIL — lever CLOSED, Elliott is a DATA-LIMITED residual

Lane `closeout-PJM` (branch `claude/closeout-pjm-elliott`, PR #7064), 2026-10-02. **Zero LP.** Executes `PRECOMMIT-pjm-closeout-elliott-cold-outage-v2-2026-10-02.md` §3 against its pre-fixed readings (committed `90aa68bf` before any v2 number). Probe `scripts/probes/_pjmco_e1_elliott_phase0_v2.py` → `results/phase0/pjm/_pjmco_e1_elliott_phase0_v2.json`, `_pjmco_e1_footprint.csv`, `_pjmco_e1_headroom_hourly.csv`. **Desk terms: a second phase-0 failure closes the lever and reports the residual as DATA-LIMITED. That applies.**

## Verdict

| step | reading | result | verdict |
|---|---|---|---|
| E1a | ≥ 3 certified, ≥ 2 outside Dec 2022 | 14 certified (13 outside); **Elliott now certified** (1.098 × winter p99) | PASS |
| E1b | leave-Elliott-out moves the 24–25 Dec residual ≤ 30 % | −38.8 % (462 → 283 MW) | **FAIL** |
| E1c | 0 nonzero days outside Dec–Feb | 0 (320 in-season days carry a residual) | PASS |
| E1d | 24 / 25 Dec model rise ÷ published rise in [0.7, 1.3] | 0.197 / 0.139 | **FAIL** |
| E1e | hours below `pjm_primary` 23–26 Dec (reported) | 0 of 96; min headroom 17.9 GW | — |

## Fit (NNLS, 104 class-day points from 26 instrumented certified days)

| class | s_T (/°C) | s_G (/$ per MMBtu) | cap |
|---|---|---|---|
| COAL | 0 | — | 0 |
| CC_REGULAR | 0.00729 | 0.00276 | 0.164 |
| CT_PEAKER | 0 | 0.00044 | 0.107 |
| ST_GAS | 0 | 0.00062 | 0.095 |

b0 = $0.09/MMBtu (Z6 NY − HH, Dec–Feb median 2018–2025); dual-fuel units exempted from the gas leg by condition (Z6 ≥ PJM delivered-oil parity — 35 winter days, including 22–26 Dec 2022).

Elliott by day (curve / CAMPD overlay already captured / residual, MW): 22 Dec 2,959 / 0 / 2,959; 23 Dec 6,204 / 1,453 / 4,752; 24 Dec 5,486 / 5,411 / 221; 25 Dec 4,138 / 6,159 / 241; 26 Dec 3,908 / 7,001 / 213.

## Why it is data-limited, not unmodelled by choice

1. **The de-biased instrument is too weak to carry the event.** Measured against warm high-load winter days, PJM's classes show small cold excess (CC cap 0.16; CT and ST respond barely at all). Real Elliott unavailability (published forced +20–25 GW in two days) is far larger than any certified cold day in 2019–2025 shows in CAMPD muster. CAMPD sees only output, so it cannot separate a unit that was forced out from one that was not called. That is exactly what Elliott's forced-outage record would need, and no free per-unit outage record exists (GADS is not public).
2. **The warm reference is missing in 3 of 7 winters** (2018/19, 2021/22, 2024/25: no Dec–Feb day with TMIN > 0 °C and net load ≥ the winter p90), so the Jan 2019, Jan 2022 and Jan 2025 polar-vortex windows are uninstrumented.
3. **The gas driver is a proxy that cannot time the event.** Transco Z6 NY daily (the nearest free daily series) spiked on 22 Dec, a day before the cold, and carries the 23 Dec print flat through the holiday weekend. So the gas leg loads the pre-event baseline (raising the 20–22 Dec reference) rather than 24–25 Dec. No free daily PJM-zone gas series (Transco Z5, TETCO M3) and no free 2019–2025 archive of pipeline critical-day notices exist (plan §4 "not free").
4. **Elliott-dependence remains** (E1b −38.8 %): with only nine instrumented certified windows, the one large event moves the fit.

**Residual ledger entry — ACCEPTED by the owner ("Accept as data-limited", 2026-10-02; ledgered in `docs/calibration-log/pjm.md`):** C3a / C3b / C3c 2022 Winter Storm Elliott. About 20 GW of published forced outage on 23–26 Dec 2022 does not enter the LP. Two ex-ante phase-0 attempts (v1 temperature-only; v2 season-gated, de-biased, gas-supply leg) failed their pre-fixed readings. **DATA-LIMITED:** identifying it needs per-unit forced-outage records (GADS, not public) or a daily PJM-zone gas-deliverability series (Transco Z5 / TETCO M3, not free). Re-open condition: either dataset becomes available.

## Status

The lever is closed, and nothing was built or solved. Cell `correlated_forced_outage` PJM stays `.` / fc `I`: the mechanism was never built for PJM, so rule 28 has no tested verdict to record. The closure and its re-open condition are recorded here and in the desk report. The rest of the lane (R-13, L2) waits for the post-W0 PJM keeper.
