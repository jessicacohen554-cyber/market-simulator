# PRECOMMIT — R-CAISO-8: 2021 partial-year measured intertie pricing + ST_GAS peak registry re-sync (2026-09-27)

Written before any shard is launched. Every direction below is pre-registered.

## 1. What changes

**A. `caiso_intertie_partial_year_measured` (new, default off, CAISO-only).**
- Each WECC intertie hub is priced at its measured print in every hour it prints. The static ladder stays only in
  unprinted hours, per hour, in the existing per-hub injector.
- Before: a hub with a >25 % gap was dropped for the whole year (2021: 5,976 of 8,760 h printed, May–Dec), while
  the raw-print loader still armed ~2.75 GW of DSW clean-depth tranches in those hours. Those tranches sat on the
  $180 placeholder and dispatched 0 (RESULT-r-caiso-7 Object 1).
- After: pricing and arming read one per-hour mask, the printed hours. The ladder-only gas coupling applies in the
  unprinted hours only.
- Rules: 14 (measured over estimate), 19 (no new mechanism; the same injector, per hour), 21/24 (zero parameters;
  registered field + cache-key default in the same commit), 28(c) (matrix row + a cell in every shard).

**B. `ST_GAS_PEAK_MEASURED_HR_MULT_BY_ISO["CAISO"]` 1.166 → 1.154 (Object 3, rule 23).**
- The source moved, not a residual. The artifact's CT_PEAKER peak was re-frozen 1.166 → 1.154 by `df277e89`
  (2026-09-06, CT-side de-contamination), reverted by `c274f1a0`, and re-applied by caiso-257 `48bcd0ec`.
- The registry was written at caiso-240 (2026-09-03) and did not follow. Bypassed ST_GAS plants carried 1.166
  while the ST_GAS class band (the same CT bucket) carried 1.154.
- **This moves the keeper's inputs in every year** (the keeper arms `caiso_st_gas_peak_measured`). It is not a
  new flag, so no recipe field changes; the solve-surface fingerprint re-keys CAISO.

## 2. Solve

Keeper recipe + A, with B in the code. One shard per year (rule 36), 2019–2025 (rules 34(c) / 35(c)). Each shard
pushes its full bundle (rule 34(a)) at a pinned SHA.

- 2019–21: `replay_keeper.py results/calibration/rcaiso6_tp_2019_2021 --years Y`
- 2022–25: `replay_keeper.py results/calibration/rcaiso5_XE_span --years Y`
- Both with `--set caiso_intertie_partial_year_measured=true`.
- The two bundles carry the same recipe; `meta.json` differs only in year-scoped fields (git_sha, gas_prices,
  shared_inputs, years).

## 3. G-DRIFT (zero LP; `scripts/probes/_rcaiso8_gdrift_identity.py`)

Arms: each bundle's own solve sha (`93a38eac` for 2022–25, `6810e68e` for 2019–21), HEAD with the flag off, and
HEAD with the flag on. All LP-visible arrays are compared: mc_base, pmax, pmin, min_gen, availability, heat_rate,
emission_rate, vom, ids, demand, and the topology.

Expected:
- **off → on:** only 2021 `mc_base` moves; nothing else in any year.
- **pin → off:** only what B reaches (bypassed ST_GAS plants' offer arrays), in every year.

Measured: see §6 (filled in before launch).

## 4. Pre-registered directions (2021 unless stated)

| quantity | 2021 fold now | direction |
|---|--:|---|
| DSW net import, TWh (EIA-930 40.9) | 15.8 | **up** |
| total imports, TWh | 37.5 | **up** |
| CC_REGULAR, TWh (actual 49.2) | 68.6 | **down** |
| PNW_midC dispatch | — | **down** (priced at measured Malin, 2021 mean $56.5, vs the $36 static rung) |
| C3a mean LMP, $/MWh (RT 50.87) | 59.83 | **down**. Cheaper DSW in May–Dec outweighs the dearer PNW. |
| C4 gas NRMSE | 0.422 | **down** (improves) |
| 2019, 2020 | — | move only through B; expected ≤ noise |
| 2022–25 (keeper) | — | move only through B. Direction not pre-registered: B raises nothing and lowers the bypassed steamers' peak tranche by 1 %. Magnitude expected small. C4 2025 (0.2987 vs ≤0.30) is thin and is the one to watch. |

First-order upper bound on the DSW move (no price feedback): +24.2 TWh (R-CAISO-7).

## 5. Promotion

- 2021 is a fold year. It is reported and never gates the ISO (rule 30(c)).
- The run is promotable only if 2022–25 stay CALIBRATED under B.
- If B flips a 2022–25 gate, the result is reported at full magnitude. A NOT-YET promotion would withdraw the
  complete marker; that is surfaced to the owner and never taken in-session.
- Rule 1 / owner standing instruction: "If structural integrity improves but gates regress that may still be a
  keeper."
- Report 2021 C1 / C3a / C3b / C4 at full magnitude either way.

## 6. G-DRIFT measured (`results/calibration/_rcaiso8/gdrift_input_identity.json`)

| pair | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| off → on (A) | — | — | mc_base | — | — | — | — |
| pin → off (B + code drift) | hr, mc | hr, mc | hr, mc | hr, mc | hr, mc | hr, mc | hr, mc |

Both rows match §3's expectations.
- **A is 2021-only.** Every other LP-visible array (pmax, pmin, min_gen, availability, emission_rate, vom, ids,
  demand, topology) is byte-identical in all seven years.
- **B row-level check (2025, 1.166 vs 1.154 at HEAD):** exactly 3 rows move, and heat_rate and mc_base move on the
  same set.

  | row | MW | peak HR | Δmc mean |
  |---|--:|--:|--:|
  | ST_GAS_LA_BASIN_p315_peak | 171.3 | 14.800 → 14.648 | −0.525 $/MWh |
  | ST_GAS_LA_BASIN_p335_peak | 33.9 | 13.615 → 13.475 | −0.483 $/MWh |
  | ST_GAS_LA_BASIN_p350_peak | 223.6 | 12.821 → 12.689 | −0.455 $/MWh |

- **Code drift since each pin is INERT for CAISO.** No other array moves. The constants that differ
  (`GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR`, `WINTER_FUELSEC_CONDUCT_MIN_ONLINE_SHARE`, and the set-valued
  `CAMPD_BINNING_ISOS` / `RGGI_MEMBER_STATES_BY_YEAR`, whose hash is order noise) reach no CAISO array. The
  `defaults_changed` entries are worktree path strings.
