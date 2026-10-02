# PRECOMMIT v2 — PJM close-out: Winter Storm Elliott, re-chartered (season gate, winter certificate, de-biased instrument, gas-supply term)

Lane `closeout-PJM` (branch `claude/closeout-pjm-elliott`, PR #7064), 2026-10-02. **Re-charter approved by the desk under R-23 on the owner's ruling ("we should be able to simulate it").** It supersedes v1 (`PRECOMMIT-pjm-closeout-elliott-cold-outage-2026-10-02.md`). v1 failed phase 0 (`RESULT-pjm-closeout-elliott-phase0-2026-10-02.md`: E0c FAIL, E0d 0.64/0.35, Elliott uncertified, instrument biased). **Desk terms: if phase 0 fails a second time, the lever closes and is reported as a DATA-LIMITED residual.** Zero LP. Solves wait for the post-W0 PJM keeper. Every reading below is fixed before the v2 numbers exist.

## 1. Mechanism (one mechanism, rule 19)

The mechanism is still `correlated_forced_outage` with a backcast residual form (`correlated_outage_backcast_residual`, as v1 §2). It is PJM's single cold-event availability mechanism. The excess for class c on day d is one function, with the gas-supply leg folded in rather than a second field:

```
excess_c(d) = 1[d in Dec–Feb] × min(cap_c,
              s_T,c × max(0, t0 − TMIN_d)  +  g_c × s_G,c × max(0, B_d − b0))
```

- **TMIN_d** is the PJM load-weighted daily minimum temperature (v1 inputs). The temperature hinge is unchanged at t0 = −7 °C.
- **B_d** is the measured daily gas-system scarcity driver: Transco Zone 6 NY daily spot minus Henry Hub daily (`data/raw/gas-prices/transco_z6_ny_daily.csv`, EIA Natural Gas Weekly Update spot table, 2018–2025).
  - **b0** is the median Dec–Feb B over 2018–2025. It is an identification point, not a tunable.
  - **Declared limit:** this is the Mid-Atlantic/NE corridor index nearest PJM-East with a free daily series. No free daily Transco Z5 or TETCO M3 series exists (plan §4). It is a proxy for PJM-zone gas deliverability, not PJM's own citygate. B is read the same day; the gas leg's lag behind the cold is what B carries and TMIN does not.
- **g_c** is 1 for gas classes (CC_REGULAR, CT_PEAKER, ST_GAS) and 0 otherwise. Dual-fuel units keep the gas leg only if they are not switched to oil that day (the NEISO `dualfuel_unswitched` premise rule, applied by condition, not by label).
- **Season gate (a):** Dec–Feb only, so the term is identically 0 on every other day.
- **Rule 13:** both drivers are measured daily series with forward analogues: the weather-year TMIN, and a weather-conditioned winter basis distribution in forecast mode. The forecast basis model is a stated follow-on and is not built here.
- **Rules 17 and 21:** the window is Dec–Feb days with TMIN ≤ t0 or B > b0, and the drivers are measured. The slopes s_T,c, s_G,c and caps cap_c are identified from measured events (ledgered with the derive as their source) and fixed by the derive (rule 23).

## 2. Identification (b): de-biased instrument and winter certificate

- **Winter certificate (a):** a window (consecutive days with TMIN ≤ t0 or B ≥ the Dec–Feb p90 of B, gaps ≤ 2 d) is certified iff its peak EIA-930 PJM net load reaches the **p99 of that winter's own Dec–Feb net load**. The annual p99 is a summer statistic and is no longer used (v1 lesson 1). The winter runs Dec of year Y−1 through Feb of year Y.
- **De-biased instrument (b):** per class, cold muster is the best-mustered CAMPD hour fraction on the window's day of minimum TMIN, or maximum B where B binds first, as in v1. The class's **warm reference muster** is the median best-mustered fraction over the same winter's Dec–Feb days with TMIN > 0 °C and net load ≥ that winter's p90. Excess = max(0, warm reference − cold muster). The 1 − EFORd baseline is not used (v1 lesson 2).
- **Fit:** per class, non-negative least squares of excess on (max(0, t0 − TMIN), g_c·max(0, B − b0)) over all certified window-days of winters 2018/19 to 2024/25. cap_c is the maximum certified excess.

## 3. Phase 0 (zero LP) — pre-fixed readings

| # | step | pre-fixed reading (any FAIL closes the lever as DATA-LIMITED) |
|---|---|---|
| E1a | certified windows (winter certificate) | ≥ 3 certified, of which ≥ 2 are outside Dec 2022; otherwise **STOP = FAIL** |
| E1b | leave-Elliott-out re-fit | the predicted 24–25 Dec residual moves ≤ 30 %; otherwise FAIL (the curve would be the event) |
| E1c | footprint | 0 nonzero-residual days outside Dec–Feb (gate check); full list of 2019–2025 days with MW by class reported |
| E1d | Elliott increment, defined exactly as v1 E0d: model thermal unavailable rise over its own 20–22 Dec mean, with the residual applied, ÷ published forced rise over its own 20–22 Dec mean | both 24 Dec and 25 Dec within [0.7, 1.3] |
| E1e | headroom 23–26 Dec = Σcap_mw − Σmw − residual, hourly | hours below the `pjm_primary` requirement are reported only; no threshold, because the solve decides |

Rule 1: the published forced series is the E1d cross-check only, never a fit target. If phase 0 passes, the solve gates are v1 §4 unchanged: S1 identity, S2 footprint (byte-identical outside the window), S3 no non-target flips, and the outcome reading Dec 23–24 mean ≥ $800 and C3b 2022 ≤ 0.20, reported. A pass also builds the field and adds its matrix row in every shard (rule 28).

## 4. Out of scope

- Pipeline EBB critical-day/OFO notices (no free 2019–2025 archive for Transco/TETCO/Columbia was found on disk).
- Any price adder.
- A separate gas-curtailment field, which rule 19 forbids.
