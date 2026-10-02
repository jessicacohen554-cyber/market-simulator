# RESULT — NWPP-NEXT-19 arm G: `gas_daily_shape` on keeper #20 (2019–2025)

PRECOMMIT: `PRECOMMIT-nwppnext19-gas-daily-shape-2019-2025-2026-10-02.md`. Run `2026-10-02-nwpp-next-19-arm`, bundle
`results/calibration/nwppnext19g_span` (composed locally from 7 shard legs; scored as a probe, `--no-prune`; registration withdrawn after the owner's reject, rule 15).
A clean A/B: same code (docs-only commit `df78648b` over pin `33014efc`), same libraries, one key moved.

| year | leg SHA | demand TWh |
|---|---|---:|
| 2019 | `e4cc515bef3fc43eda516c68739255780bc55c02` | 279.581 |
| 2020 | `b517e0a7787252a71dde742e9e488bd2231fde4b` | 292.940 |
| 2021 | `97da67243914456366a2b7e240e7fcf65b6bb57b` | 289.358 |
| 2022 | `f68f68fc1b56a8fa16ef66d536182bbe6d6e241c` | 298.960 |
| 2023 | `b9e95b0a8604e51d301866467ba808513c47ee0b` | 280.261 |
| 2024 | `0c1675450ec677cdbba0060fb8c0b490d0b1dcb4` | 290.216 |
| 2025 | `d83319dfd2d6adca4b9b106340ebca16f4754358` | 302.532 |

Every leg passed every hard stop: the `scenario_config` diff is exactly `gas_daily_shape` False → True; demand is exact; and
the arm is live, with the within-month gas_cc `mc` SD at most $20–144/MWh. The 2021 value is February 2021's HH spike during
Winter Storm Uri.

## Verdict diff vs keeper #20 (per criterion × year × key)

- **Status changes: 0.** The determination is unchanged: NOT-YET on {dispatch_corr}, the one record C4 coal 2023.
- fuelmix, sysvol, governance and forced_share PASS in both runs; price stays UNSCORED.

C4 fleet hourly fit (r / NRMSE; floors r ≥ 0.70, NRMSE ≤ 0.30):

| year | coal, keeper #20 | coal, arm G | gas, keeper #20 | **gas, arm G** |
|---|---|---|---|---|
| 2019 | 0.720 / 0.235 | 0.733 / 0.231 | 0.731 / 0.232 | **0.703** / 0.244 |
| 2020 | 0.763 / 0.165 | 0.758 / 0.172 | 0.813 / 0.181 | **0.702** / 0.226 |
| 2021 | 0.765 / 0.186 | 0.790 / 0.177 | 0.847 / 0.150 | **0.766** / 0.180 |
| 2022 | 0.712 / 0.233 | 0.721 / 0.232 | 0.864 / 0.184 | **0.717** / 0.250 |
| 2023 | **0.669 / 0.313 FAIL** | **0.677 / 0.307 FAIL** | 0.781 / 0.181 | 0.762 / 0.190 |
| 2024 | 0.741 / 0.218 | 0.767 / 0.209 | 0.894 / 0.125 | **0.833** / 0.161 |
| 2025 | 0.712 / 0.249 | 0.728 / 0.246 | 0.852 / 0.197 | **0.765** / 0.239 |

**Regressions, at full magnitude.**
- **Gas C4 r falls in every year:** −0.028 (2019), −0.111 (2020), −0.081 (2021), **−0.147 (2022)**, −0.019 (2023),
  −0.061 (2024), −0.087 (2025). NRMSE rises in every year.
- 2019 and 2020 gas now sit **0.003 and 0.002 above the 0.70 floor**.
- **CT_PEAKER energy rises in every year:** +0.03 to +0.54 TWh (2024: 4.50 → 5.04; 2025: 8.05 → 8.48). ST_GAS rises
  2022–2025.

Coal C4 improves by +0.005 to +0.026 in 6 of 7 years (2020: −0.005). 2023 moves 0.669 → 0.677, still a FAIL.

## Why gas gets worse: the shape is the wrong gas signal for this footprint

| | gas daily-mean r, keeper → arm | within-day r, keeper → arm | daily SD MW, model (keeper → arm) / measured |
|---|---|---|---|
| 2020 | 0.811 → **0.677** | 0.822 → 0.795 | 1,335 → 1,584 / 1,756 |
| 2022 | 0.858 → **0.651** | 0.882 → 0.867 | 1,403 → 1,697 / 1,774 |
| 2025 | 0.899 → **0.770** | 0.819 → 0.814 | 1,877 → 2,133 / 1,691 |

- **The loss is between days. The within-day fit is unchanged.** The HH daily swing moves gas energy across days of the month.
  With a monthly hydro budget, the LP shifts hydro onto dear-gas days and gas onto cheap-gas days. The real NW gas fleet does
  not follow that pattern.
- This matches the census: HH explains ~0–5 % of NW between-day price variance, except in January 2024 (FINDING §1). NW gas
  units buy at Sumas, Stanfield, Opal and Kern River, not at Henry Hub.
- The mechanism is admissible in form (measured, forward-reproducible), but the input is **mis-located for NWPP**. The
  measured series is defined at a hub that does not map to this footprint, which is rule 14's boundary case. The measured
  NW-hub series it stands in for has no public daily print.

## Reading

- **Not a promotion candidate on structure.** The arm adds a signal that measurement says is not NWPP's gas price shape, and
  every gas fit degrades through the channel the shape acts on. Adding it does not make the model more faithful.
  The owner standing ruling ("promote if structural integrity improves") is not met. Recommendation: **R** for NWPP.
- The C4 coal 2023 gain (+0.008) comes from a price signal that degrades gas. It is not evidence for the arm (rule 1).
- **Owner card 2026-10-02: "Reject, keep #20".** `gas_daily_shape` is **R** for NWPP. Keeper #20 stays. The probe
  registration is withdrawn (rule 15, keeper-only retention). The composed bundle was never committed; the leg SHAs above are
  its provenance (rule 33).
