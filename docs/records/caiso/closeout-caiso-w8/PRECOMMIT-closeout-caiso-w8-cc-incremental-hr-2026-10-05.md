# PRECOMMIT closeout-CAISO-w8: CC_REGULAR econ tranches at the measured incremental heat rate (2026-10-05)

**Charter.** Desk GO, 05:46Z: build `cc_econ_incremental_hr` default-off and CAISO-armed, and run 7 legs on w6.
- Leave the authorized CC bands unchanged and declare it.
- Count no-load fuel once (rule 19).
- Freeze the derive (rule 23).
- Kills: C1 CC_REGULAR 2020 or 2021, any C3a or C3b, C8.

**Evidence.**
- closeout-CAISO-w7 FINDING and RESULT: the overnight 2021 wedge is about 1.4 MMBtu/MWh of implied HR. About 0.5 of it is the bands; the rest is unattributed.
- The linear census (`_cc_linear_census.csv`) gives incremental/average = 0.930–0.942, generation-weighted, 2019–2025.

**Build.** `573593b4` on `claude/closeout-caiso-w8`, cut from the w6 lane head so the L1 code is not in the pin. The
shards pin the commit that carries this PRECOMMIT (Addendum A).

## 1. Mechanism and identification

**Incumbent.** A CC_REGULAR plant's tranches are priced at its **average** operating HR × the band multiplier. The
average is `campd_cc_heat_rates_<ISO>.csv`, sum(heatInput) / sum(grossLoad) over steady CC hours, and it embeds the
unit's no-load heat. The bands are committed 1.0, econ_low 1.066, econ_high 1.072, peak 1.386.

**Arm.**
- Each econ step is additionally scaled by the plant's measured **incremental / average** ratio at that step: econ_low
  at x = 0.5 of the LSL–HSL range, econ_high at x = 0.9, linear across the smoothed ramp.
- Source: `cc_incremental_hr_ratio_CAISO.csv` from `scripts/data/derive_cc_incremental_hr_ratio.py`. It uses the
  frozen `derive_campd_marginal_hr.derive_unit_bands` normalized-quadratic I/O slope, over the same plant-year's CEMS
  average, both gross. The pooled year 0 is the mean of the ok years.
- It is the CC sibling of `coal_econ_two_sided` (soco-81).

**Rule 19 (one mechanism; no-load fuel counted once).**
- The committed (min-load) tranche keeps the average HR, and so carries the no-load heat.
- Only the econ steps (incremental output of a running unit) take the slope.
- The peak (duct) band and any must-run tranche are untouched.
- Unlike the coal mechanism, the ratio does **not** replace the band multiplier.

**Rule 1(c).** The authorized bands stay on the econ steps unchanged and are declared here. Re-setting them is the
owner's channel. If the result points to a band re-set, it goes to the owner as a separate question.

**Rules 13, 14, 23, 25.**
- 13: measured CEMS, producible for a forward year from multi-year history.
- 14: the incremental rate is the physical marginal cost the average misstates.
- 23: the derive is frozen; source EPA CAMPD unit-level hourly, `data/raw/campd-unit-level/CA_2019..2025`.
- 25: a per-ISO artifact. SOCO's soco-85 refusal is SOCO's own measurement and does not transfer.

**DOF:** zero fitted parameters.

**Measured ratios** (pooled, large CAISO CCs):

| | Range |
|---|---|
| econ_low | 0.81–0.92 (Moss Landing 0.82, Delta 0.92, Metcalf 0.91, Otay Mesa 0.88, Palomar 0.87) |
| econ_high | 0.84–1.07 (convex curve: the top of the range nears or exceeds the average) |

Small or odd units are flagged by their own numbers (Glenarm 0.67 / 0.58; Sunrise 0.95 / 1.17). All are inside the
(0.5, 1.2) plausibility band.

## 2. Zero-LP reach

- **Size of the effect.** The overnight 2021 marginal CC sits on econ_low / early econ steps. A ratio of about 0.85
  takes its offer about 15 % lower, roughly $7–8/MWh at a $52–55 offer. That is the upper end of the w7 wedge.
- **Effect on T1.** Where gas CC sets λ, λ falls toward max(next CC offer, import-rung print). T1 needs about 1 pp of
  C3a 2021 (+10.6 / +11.0 % → ≤ 10 %).
- **The other side.** Cheaper CC econ steps displace imports, CT_PEAKER and ST_GAS, so CC_REGULAR volume rises in every
  year.
  - CC_REGULAR 2020 sits at +4.00 vs ±4.60 in w6, with 0.60 TWh of headroom.
  - 2021 sits at +2.67 vs ±4.83.
  - This is the main risk (K1).

## 3. Recipe, bars, kills (ex ante)

**Arm A1** = `closeout_caiso_w1_a2_span` replayed with:
- the w6 recipe: `caiso_dsw_daytime_lateevening_unprinted_arm`, `caiso_dsw_clean_depth_own_year`,
  `caiso_intertie_unprinted_daily_gas_shape`, `measured_ct_heat_rates_crosswalk_remap` and `caiso_chp_btm_measured`,
  all `true`;
- **plus `cc_econ_incremental_hr=true`**.

Seven year-isolated legs.

**Control.** The w6 probe `2026-10-05-closeout-caiso-w6-a1`, scored on the same (w6-rendered) bench parts.

**Bars.**
- **T1:** C3a 2021 |model − RT| ≤ 10 %.
- **Report:** C3a / C3b 2022–25, C1 every class and year, C4 gas, C3c, the CC_REGULAR dispatch increase per year, and
  the marginal-setter shift.

**Kills.**

| Kill | Condition |
|---|---|
| K1 | C1 CC_REGULAR 2020 or 2021 PASS → FAIL. Also report every other C1 cell. |
| K2 | Any C3a or C3b cell PASS → FAIL |
| K3 | C8 breach |
| K4 | C4 gas NRMSE > 0.30 in a year that passes now (reported) |
| K5 | C2 out of band (reported) |

**Decision rule.**
- T1 met and K1–K3 clear: RESULT plus a slot request to the desk. This stacks on the pending w6 promotion.
- Otherwise: record, set the CAISO cell, stand down.

## 4. G-DRIFT (w6 pin `23762bed` → build, backcast path)

| Hunk | Classification |
|---|---|
| `campd_bins.cc_incremental_hr_ratios` | **INERT** (new function; read only under the flag) |
| `assembly.bins_to_fleet` CC block | **INERT off.** `_cc_inc_ratio` is empty unless the flag is set, so `econ_steps` is untouched. |
| `scenarios.py` field (default off, optional cache key) | **INERT** |
| The derive script and its artifact | **INERT** for the solve (read only when armed) |

The w8 branch is cut from the w6 lane head (records and registration since the pin; no backcast-path code). No LIVE
hunk, so no control solve.

## 5. Side effects

None on the bench or the payload sources.
