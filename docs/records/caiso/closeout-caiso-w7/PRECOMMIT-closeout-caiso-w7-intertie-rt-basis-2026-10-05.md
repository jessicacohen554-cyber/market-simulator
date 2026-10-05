# PRECOMMIT closeout-CAISO-w7: the RTM intertie-print basis for the CAISO import ladder (2026-10-05)

**Charter (desk, 05:13Z).**
- Work C3a 2021 (+11.0 %, the last load-bearing FAIL) on the w6 basis.
- Write the FINDING and PRECOMMIT.
- Launch shards on the w6 configuration.

**Records.** `FINDING-closeout-caiso-w7-c3a2021-phase0-2026-10-05.md`.

**Build.** `34d35456` on `claude/closeout-caiso-w7`; the shards pin the commit that adds the 2023–25 RTM rows (Addendum A).

## 1. Mechanism and identification

**What the keeper does now.** In printed hours, every hub-priced CAISO import object takes its offer price from the
measured **OASIS DAM** delivered nodal LMP at the intertie scheduling points (PALOVRDE; MALIN/CAPTJACK). That covers:
- the DSW surplus, overnight, daytime and late-evening clean rungs (raw hub);
- the CCGT, CT and scarcity tranches (hub + wheel + border carbon);
- the surplus trigger.

**The arm** (`caiso_intertie_print_rt_basis`):
- In every hour where the **RTM** delivered nodal LMP prints, it replaces the DAM value. The RTM series uses
  PRC_INTVL_LMP 5-min averaged per hour, on the identical MCE + MCC + MCL construction, GHG excluded, hub-averaged.
- Every other hour keeps the DAM print and the existing gap-fill / formula chain.
- It is one overlay at the three readers (`envelopes._read_intertie_frame`), set per solve at the run_year seams.

**Rule 14 / rule 1.**
- The LP is a single-settlement real-time analogue, and C3a scores it on RT.
- The rubric says the DA−RT premium is a forward risk premium the LP must not price. The DAM print carries exactly that
  premium into λ through the import offers.
- Measured intertie RT − DAM on the model's construction:
  - PALOVRDE −5.8 (2021 Apr–Dec) and −15.9 (2022);
  - MALIN −9.4 and −17.6.
- One measured series is swapped for another of the same market, on the LP's settlement. Zero fitted parameters.

**Rule 13.** The forward analogue is the forward RT hub price. The forecast never reads this overlay (it is
backcast-only data).

**Declared caveat.** The late-evening rung's spread band (measured DA CAISO − hub) is left as coded. That makes it a
mixed basis under the arm, and it is reported, not changed.

**Admissibility question, put to the desk/owner.** Real imports are mostly DA-scheduled and paid DA. The arm reads the
boundary as the RT market the LP represents. The solve proceeds on the desk's charter; the ruling decides promotion.

**Coverage.**

| Year | RTM print | Hours on RTM |
|---|---|---|
| 2019 | none (unprinted year) | 0, byte-identical |
| 2020 | none (unprinted year) | 0, byte-identical |
| 2021 | Apr 27–Dec | 5,712 |
| 2022 | full | 8,759 |
| 2023 | 2023-06-25 onward (OASIS retention) | about 4,500; Jan–Jun stay DAM |
| 2024 | full | full |
| 2025 | full | full |

2023 and 2024–25 come from the in-flight OASIS intake.

## 2. Zero-LP reach

- Greedy upper bound: in every hour where a hub-priced rung is marginal (80 % of 2021 hours), λ falls by that hour's
  intertie RT − DAM, with no re-dispatch.
- That takes C3a 2021 from +9.9 % to −2.5 % on the hub basis. The scorer reads +10.6 / +11.0 %.
- T1 needs ≥ 1.0 pp, so the upper bound is about 12× the bar.
- The same mechanism moves 2022–25 down, and 2022 carries the largest spread.

## 3. Recipe, bars, kills (ex ante)

**Arm A1.** `closeout_caiso_w1_a2_span` replayed with:
- the w6 recipe: `caiso_dsw_daytime_lateevening_unprinted_arm`, `caiso_dsw_clean_depth_own_year`,
  `caiso_intertie_unprinted_daily_gas_shape`, `measured_ct_heat_rates_crosswalk_remap` and `caiso_chp_btm_measured`,
  all `true`;
- **plus `caiso_intertie_print_rt_basis=true`**.

Seven year-isolated legs. 2019 and 2020 are expected byte-identical in price to w6 (no RTM print); they run anyway
(rule 16).

**Control.** The w6 probe `2026-10-05-closeout-caiso-w6-a1`. No control solve (§4).

**Bars.**
- **T1:** C3a 2021 |model − RT| ≤ 10 %.
- **Report:** C3a / C3b 2022–25, C1 every class and year, C4 gas, C3c, imports vs EIA-930 by hour.

**Kills.**

| Kill | Condition |
|---|---|
| K1 | Any C1 cell PASS → FAIL. Watch CC_REGULAR 2023 (−1.94 vs ±5.27) and 2024 (−2.50 vs ±5.29): cheaper imports displace CC. |
| K2 | Any C3a or C3b cell PASS → FAIL. 2022 carries the largest spread, so watch it on the low side (−10 %). |
| K3 | C4 gas NRMSE > 0.30 in any year that passes now |
| K4 | C8 breach |
| K5 | C2 leaves its band |
| K6 | C3c: any PASS → FAIL |

**Decision rule.**
- T1 met and K1–K6 clear: report to the desk with a slot request, conditional on the owner's admissibility ruling (§1).
- T1 missed or any kill fires: record the result, set the matrix cell, stand down.

## 4. G-DRIFT (w6 pin `23762bed` → build, backcast path)

| Hunk | Classification |
|---|---|
| `envelopes._read_intertie_frame` + three readers | **INERT off.** Returns `pd.read_parquet(path)` unchanged when the toggle is off. |
| `set_caiso_intertie_rt_basis` at the runner / run_calibration seams | **INERT off.** Sets False unless the field is armed. |
| `scenarios.py` field (default off, optional cache key) | **INERT** |
| `fetch_caiso_intertie_lmp.py --rtm`, the RTM sibling artifact | **INERT for the solve** (read only when armed) |
| The w6 records merge (#7211, records + matrix only) | **INERT** |

No LIVE hunk, so no control solve.

## 5. Side effects

- None on the bench. No benchmark or payload source is touched.
- The data intake adds raw RTM rows to `data/raw/lmp-data/CAISO/CAISO_rtm_hourly_{2023,2024,2025}.csv` for the
  intertie nodes. The existing hub rows are unchanged; the postprocess de-duplicates on (timestamp, node).
