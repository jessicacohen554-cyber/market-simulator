# ERCOT run160 — HSL endogenous curtailment (2023–2025)

run157 keeper config (faithful reproduction) + uncurtailed-VRE wiring for the no-HSL years. See
`docs/forecast-methodology-gaps-2026-06.md` G7.

## What changed (vs run157)

ERCOT 2024/25 have **no NP6 HSL parquet**, so they previously consumed the
EIA-930 **net-of-curtailment delivered** generation as the renewable CF — the
historical curtailment was baked in and the LP could not re-curtail or respond
to changed build. They now receive an **uncurtailed potential**: the weather-year
delivered profile grossed up by the per-tech **reference curtailment rate** from
the most recent HSL year (ERCOT 2023 HSL: wind 4.67%, solar 6.29%). The LP
curtails endogenously (renewables are decision variables, MC=0, ub = CF×cap).
2023 is unchanged (consumes its own NP6/UMass HSL). The potential is never scaled
so delivered output lands on actuals — the reference rate is from a *different*
year, a forward-reproducible parameter (rule #11).

## Modeled vs measured curtailment (diagnostic, NOT a fit target — rule #11)

| year | fuel | potential TWh | model gen TWh | model curt % | measured curt % | measured source |
|------|------|--------------:|--------------:|-------------:|----------------:|-----------------|
| 2023 | wind | 113.28 | 110.84 | 2.16 | 4.67 | ISO-reported HSL−GEN |
| 2023 | solar| 33.71  | 33.56  | 0.44 | 6.29 | ISO-reported HSL−GEN |
| 2024 | wind | 117.01 | 114.33 | 2.29 | 4.67 | ref rate (2023 HSL) |
| 2024 | solar| 49.93  | 49.59  | 0.67 | 6.29 | ref rate (2023 HSL) |
| 2025 | wind | 120.77 | 117.91 | 2.36 | 4.67 | ref rate (2023 HSL) |
| 2025 | solar| 71.00  | 69.78  | 1.73 | 6.29 | ref rate (2023 HSL) |

The model curtails **less** than ERCOT reported every year: the reduced 6-zone
ERCOT network omits the local/nodal transmission constraints that drive much of
the real curtailment. This gap is the diagnostic of the curtailment mechanism,
left as-is (no fit applied).

## Calibration caveat — intervening main-code regression (NOT this change)

This run scores **NOT-YET** (C1 CC_REGULAR over-run + C6 unattested). The C1
regression vs the run157 keeper is **dominated by intervening model-code changes
merged to main** since run157 was solved, not by the HSL wiring. Proof: the
**2023 control year** uses renewables byte-identical to run157 (both HSL — the
HSL change cannot touch it), yet regressed on current code:

| 2023 class | run157 model | run158 model | Δ (pure intervening code) |
|------------|-------------:|-------------:|--------------------------:|
| CC_REGULAR | 139.27 | 147.84 | **+8.57 TWh** |
| COAL_PRB   | 46.44  | 42.66  | −3.78 |
| ST_GAS     | 18.43  | 13.33  | −5.09 |

The HSL change adds only ~+1.5 CC / ~−4 COAL_PRB to 2024 on top of this baseline
shift (cheap renewables displacing some thermal). The pre-existing ERCOT
CC-over-run on current main should be investigated separately.
