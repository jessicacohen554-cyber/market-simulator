# FINDING — closeout-chp-floor-basis (ZERO LP): the CHP steam-level floor is measured on one capacity and applied to another

**Lane** `closeout-chp-floor-basis`, chartered by the backcast close-out desk after the MISO-w3g phase 0
(`docs/records/miso/closeout-miso-w3/FINDING-closeout-miso-w3g-chp-host-level-phase0-2026-10-05.md`, PR #7210).
No LP was solved. No solve-affecting code was changed.

- **Probe:** `scripts/probes/_closeout_chp_floor_basis_audit.py`
- **Output:** `results/phase0/governance/_closeout_chp_floor_basis_audit.json`
- **Method:** each arming keeper's fleet was rebuilt per year through the sanctioned
  `scripts/lib/bundle_fleet.reconstruct_bundle_fleet`. The realised floor is the `min_gen` rows tagged `MECH_CHP_STEAM`,
  clipped to `pmax × availability`. Dispatch comes from the committed `hourly/unit_marginal_<year>.parquet`. The meter is
  CAMPD whole-plant net (`run_calibration_full._campd_hourly_frame`) and EIA-923 class net (`chp.chp_class_netgen_mwh`).

## 1. Verdict: CONFIRMED (a basis mismatch in shared code)

**How the level is measured.** In `scripts/data/derive_thermal_tranches.py:2316-2333` and `:2398-2409`:

- `steam_level_cf` is `on_freq × p50(acf_on)`, with `acf = net / (artifact nameplate_mw × outage derate)`;
- `chp_pmin_cf` uses the same denominator;
- the EIA-923 lens (`_chp_f923_floor_cf`, `:338-397`) divides by the same `cap[(code, group)]`.

So the level is a percent of the **artifact's** `nameplate_mw`.

**How the level is applied.** In `src/market_sim/data/fleet/assembly.py`:

- `:1021-1047` selects the level (the swap, with the conduct scope);
- `:1093-1094` sets `floor_mw = pmin_cf × (1 − btm) × nameplate`, where `nameplate = b["capacity_mw"]` (`:473`) is the
  **LP bin's** capacity;
- `src/market_sim/data/fleet/arrays.py:3924-3929` then holds `floor_mw` in every hour.

The two capacities are different numbers. Across the 335 floored plant-group-years in the two arming keepers, LP ÷
artifact nameplate has a median of 1.002, 75th percentile 1.062, and range 0.26–1.30. Examples:

| plant | LP ÷ artifact nameplate |
|---|---|
| Eastman 55176 | 448 / 417 MW = **1.074–1.094** |
| Black Hawk 55064 | 1.117 |
| Elk Hills 55400 | 1.046 |
| Los Medanos 55217 | 1.070 |
| Martinez Refining 54912 | 104 / 80 MW = **1.30**, at level 100 % |

When the LP capacity is larger, the floor is above the plant's own measured level. When it is smaller (Fresno Cogen
10156, 0.315), the floor is understated.

The same defect applies to the p2 `chp_pmin_cf` floor (same formula, same denominator). The other path,
`chp_export_floor_measured` (ERCOT), divides by the LP `nameplate` (`assembly.py:1082-1083`) and is therefore
basis-consistent.

**Levels above 100 %.** No SPP or CAISO artifact row carries a level above 100 %. The > 100 % rows MISO-w3g reported
are MISO-artifact-only.

## 2. Which keepers arm the swap

`iso_configs.py` carries no default arm. It arrives only through keeper recipes:

| keeper | `chp_steam_floor_p25` | `conduct_scope` | `duty_window` |
|---|---|---|---|
| SPP `closeout_spp_nuc_span` | on | on | off |
| CAISO `closeout_caiso_w1_a2_span` | on | off | off |
| ERCOT, MISO, PJM, NYISO, NEISO, NWPP, SOCO | off | — | — |

MISO is exposed only prospectively (w3g).

## 3. Floor energy against the meter

`floor_to_meter` = grid floor ÷ (meter × (1 − btm)). This is the floor's plant-total equivalent against the meter, on one
basis. The full per-host table is in the JSON.

| keeper | floored plant-group-years | floor > meter | of which metered (`ok`) | floor energy above meter, TWh/yr | same, after re-basing |
|---|---:|---:|---:|---|---|
| SPP | 61 | 14 | 6 (all Eastman) | 0.00–0.27 | 0.00–0.13 |
| CAISO | 274 | 91 | 35 | 0.13–0.40 | 0.04–0.26 |

**SPP metered hosts.** Eastman CC_CHP is floored at 1.03–1.19× its meter in 2019–2023 and 2025. For 2022:

- floor 1.74 TWh grid;
- CAMPD net 2.26 TWh;
- grid share at 35 % BTM = 1.47 TWh;
- ratio 1.186.

Black Hawk stays below its meter in every year. Lake Road 2098 is scoped out and stays on its p2 floor (on-frequency
0.246).

**SPP CEMS-invisible hosts.** Over-meter rows are small: Russell 7930 (1.6–5.1×, about 1 GWh), GP Muskogee 2019 (1.18),
Wasson 2025 (1.06) and MJMEUC 2024 (1.01).

**CAISO.** Two separate effects, both visible:

- **The basis effect.** Elk Hills is 1.01–1.04× its meter every year. Los Medanos 2020 is 1.015. Martinez Refining is
  1.08–1.26×, entirely the 1.30 basis.
- **The known caiso-293 cycler trickle.** CAISO does not arm `conduct_scope` or `duty_window`:

  | plant | floor ÷ meter |
  |---|---|
  | Kingsburg 10405 | 2.7–12.5× |
  | King City | up to 2.7× |
  | Badger Creek | up to 2.8× |
  | McKittrick | up to 3.4× |
  | Chalk Cliff | up to 6.7× |
  | Midway Sunset | up to 3.1× |

Re-basing alone removes about 70 % of SPP's over-meter energy and about 45 % of CAISO's. The CAISO remainder is the
rule-17 window defect (on-frequency × level held all hours) plus ordinary year-to-year variation of a pooled level. Those
are different defects with existing levers (`chp_steam_floor_conduct_scope`, `chp_steam_duty_window`).

## 4. C1 exposure (upper bound, before LP re-dispatch)

The bound is the energy the keeper dispatched at or below the floor and above a meter-capped floor (`cap_release_twh_ub`).

| keeper | released CHP energy per year | where it would go |
|---|---|---|
| SPP | CC_CHP ≤ 0.27, ST_CHP ≤ 0.013, CT_CHP ≤ 0.003 TWh; total ≤ 0.27 | CC_REGULAR / COAL_PRB, about equally (SPP-100 §2) |
| CAISO | CC_CHP ≤ 0.23, CT_CHP ≤ 0.22 TWh; total ≤ 0.40 (2025) | mainly CC_REGULAR |

**SPP: no C1 status moves.**

- CC_CHP is over actual by 0.06–0.37 TWh in a ±8 TWh band, so the release moves it toward actual.
- The release is too small to clear the CC_REGULAR or COAL_PRB FAILs in 2021/2022. Those need ≥ 0.94 and 2.75 TWh.
- It cannot breach the 2025 margins (CC_REGULAR 0.14, COAL_PRB 0.61, against a 2025 release ≤ 0.10 TWh).

**CAISO: no C1 status moves.**

- CC_CHP is over actual by 0.3–1.0 TWh in a ±4.6–5.3 TWh band, so the release moves it toward actual.
- CT_CHP is excluded from C1 (`FUELMIX_EXCLUDED`).
- The CC_REGULAR FAILs in 2019–2021 are already over-predicted and would deepen by ≤ 0.23 TWh.
- No PASS record sits within 1 TWh of its band.

Neither keeper's determination (both NOT-YET) moves.

## 5. Proposed minimal fix (promotion-grade, for the desk, not landed here)

**Re-base, do not cap at the meter.** A cap at the solve year's own meter fails rule 13: it pins a unit to observed
generation and has no forward analogue. Re-basing changes no statistic. It expresses the measured percent on the capacity
the floor multiplies.

1. **Re-base.** The deriver already emits `nameplate_mw` on every CHP row, so carry it through the artifact loader. In
   `assembly.py`, before `:1093`, set:

   ```
   pmin_cf ← min(100, pmin_cf × artifact_nameplate_mw / nameplate)
   ```

   for any level read from the tranche artifact (`steam_level_cf` swap and p2 `chp_pmin_cf`). Not for
   `chp_export_floor_measured`, which is already on the LP basis.
2. **Rule 24.** Make it a registry field, `chp_floor_artifact_basis` (bool), with a mechanism-matrix row and a `U` cell in
   every shard (rule 28). Rule 26 then deletes the un-rebased path once every keeper carries it.
3. **Default.**
   - *Option (a), recommended: default ON.* It is a repair of a basis bug, not a lever. This re-keys every ISO whose keeper
     arms `chp_steam_following`, because the p2 floor carries the same mismatch. That means all nine.
   - *Option (b), narrow: arm only with `chp_steam_floor_p25`.* Scoped to SPP and CAISO, at the cost of leaving the same
     mismatch in the p2 floor everywhere else.
4. **Keepers touched.**
   - SPP `closeout_spp_nuc_span`: Eastman's floor −7 to −9 %, Black Hawk's −10 %.
   - CAISO `closeout_caiso_w1_a2_span`: Martinez −23 %, Elk Hills / Los Medanos −4 to −7 %, Fresno up 3×.
   - Under (a), the p2 floor in every other keeper, by its own basis ratios. Measured in §7.
   - Expected scored effect: no C1 status flip in SPP or CAISO (§4). Under (a) no PASS→FAIL anywhere (§7).
5. **Order with MISO.** The fix must land before any MISO arm of the swap. The MISO > 100 % artifact rows additionally need
   the miso-95 re-derivation (w3g §4).

## 6. Matrix

No cell moves (nothing solved). The lane edits no ISO shard.

## 7. Option (a) exposure: the p2 floor in all nine keepers (desk follow-up, zero LP)

**Method.** Same probe, now with `--isos`. Output for the other seven keepers is
`results/phase0/governance/_closeout_chp_floor_basis_audit_p2.json`; SPP and CAISO were re-run into the first JSON with
the new columns.

The re-based floor is the realised floor ÷ basis ratio, clipped to `pmax × availability`. Δ is the bound on dispatch
change: energy added above keeper dispatch minus energy held above the re-based floor. It is an upper bound before LP
re-dispatch. Under option (a), SPP and CAISO re-base the p2 rows as well as the swap rows, so their Δ here is the full
option-(a) figure.

**PJM stub.** The PJM rebuild stubs `pjm_da_virtual_bids`, whose licensed DataMiner2 parquets are not in a fresh
container. Those pseudo-units are appended after the physical fleet and never touch a CHP row.

### 7.1 Basis ratio (LP ÷ artifact nameplate), floored CHP plant-group-years

| keeper | rows | artifact-based | p05 | median | p95 | min–max | > 1.05 | < 0.95 |
|---|---:|---:|---:|---:|---:|---|---:|---:|
| ERCOT `closeout_ercot_l1_span` | 261 | 0 | — | — | — | — | — | — |
| PJM `closeout_pjm_nuc_full_span` | 265 | 251 | 0.857 | 1.037 | 1.222 | 0.83–1.35 | 119 | 31 |
| MISO `closeout_miso_nuc_span` | 400 | 353 | 1.000 | 1.095 | 1.927 | 0.58–**2.67** | 234 | 5 |
| NYISO `w0_nyiso_span` | 18 | 18 | 1.051 | 1.099 | 1.221 | 1.03–1.22 | 17 | 0 |
| NEISO `w0_neiso_span` | 58 | 44 | 0.885 | 1.000 | 1.706 | 0.60–1.71 | 7 | 6 |
| SOCO `closeout_soco_3_span` | 66 | 60 | 0.874 | 1.061 | 3.247 | 0.82–**3.25** | 41 | 6 |
| NWPP `nwppnext27_span` | 59 | 59 | 0.892 | 1.109 | 1.150 | 0.89–1.39 | 46 | 5 |
| SPP (§1) | 61 | 61 | 0.777 | 1.065 | 1.250 | 0.78–1.25 | 36 | 9 |
| CAISO (§1) | 274 | 274 | 1.000 | 1.000 | 1.125 | 0.26–1.30 | 57 | 7 |

**ERCOT is untouched.** `chp_export_floor_measured` sets 259 of its 261 rows from EIA-923 over the LP nameplate. The
other two come from the hardcoded CAMPD map, which has no nameplate, so their basis is unknown.

**Rows outside the re-base.** Rows marked "unknown" in other ISOs are floored plant-groups the artifact has no row for:
MISO 47, PJM 14, NEISO 14, SOCO 6. They keep their floor under the re-base.

### 7.2 CHP floor energy before → after re-basing, TWh (range over the keeper's years) and Δ bound

| keeper | class | floor now | floor re-based | Δ dispatch bound |
|---|---|---|---|---|
| ERCOT | CC / CT / ST_CHP | 19.0–23.8 / 2.6–4.3 / 0.03–0.05 | unchanged | 0 |
| PJM | CC_CHP | 3.14–3.90 | 3.03–3.66 | −0.11 to −0.24 |
| PJM | CT_CHP | 0.67–0.70 | 0.61–0.64 | −0.06 to −0.07 |
| PJM | ST_CHP | 0.24–0.34 | 0.24–0.34 | ≈ 0 |
| MISO | CC_CHP | 8.56–8.84 | 7.34–7.62 | **−1.17 to −1.37** |
| MISO | CT_CHP | 2.54–3.28 | 2.10–2.81 | −0.32 to −0.47 |
| MISO | ST_CHP | 0.61–0.79 | 0.59–0.74 | −0.02 to −0.06 |
| NYISO (2021–25) | CC_CHP | 4.30–4.61 | 3.97–4.26 | −0.32 to −0.42 |
| NYISO (2021–25) | CT / ST_CHP | 0.05 / 0.04 | 0.04 / 0.04 | ≈ 0 |
| NEISO | CT_CHP | 0.14–0.17 | 0.14–0.16 | ≤ −0.02 |
| NEISO | ST_CHP | 0.02–0.03 | unchanged | 0 |
| SOCO | CC_CHP | 1.79–1.96 | 1.67–1.81 | −0.13 to −0.16 |
| SOCO | CT / ST_CHP | 0.04 / 0.02–0.05 | ≈ unchanged | ≈ 0 |
| NWPP | CC_CHP | 2.78–3.50 | 2.51–3.16 | −0.27 to −0.33 |
| NWPP | CT_CHP | 0.07–0.12 | 0.07–0.11 | ≈ −0.01 |
| SPP | CC / CT / ST_CHP | 1.59–1.84 / 1.13–1.21 / 0.11 | 1.45–1.68 / 1.01–1.08 / 0.10 | −0.12 to −0.16 / −0.11 to −0.12 / −0.01 |
| CAISO | CC / CT_CHP | 6.51–7.81 / 1.18–1.22 | 6.29–7.46 / 1.17–1.19 | −0.21 to −0.35 / ≤ −0.04 |

The net direction is a release everywhere: the re-based floor adds ≤ 0.001 TWh in any class-year. Largest released
energy per ISO-year:

| keeper | max release, TWh |
|---|---:|
| MISO | 1.73 |
| NYISO | 0.43 |
| CAISO | 0.39 |
| NWPP | 0.35 |
| PJM | 0.31 |
| SPP | 0.29 |
| SOCO | 0.16 |
| NEISO | 0.02 |
| ERCOT | 0 |

### 7.3 C1 records

**PASS→FAIL: none in any keeper.**

**CHP records where |Δ| exceeds 25 % of the remaining band margin.** None flips.

| record | model − actual, TWh | band | margin | Δ | Δ as % of margin | direction |
|---|---:|---:|---:|---:|---:|---|
| MISO 2019 CC_CHP PASS | −5.25 | ±8.00 | 2.75 | −1.18 | 43 % | away from actual |
| MISO 2020 CC_CHP PASS | −4.49 | ±8.00 | 3.51 | −1.18 | 34 % | away from actual |
| MISO 2021 CC_CHP PASS | −5.04 | ±8.00 | 2.96 | −1.18 | 40 % | away from actual |
| MISO 2022 CC_CHP PASS | −5.83 | ±8.00 | 2.17 | −1.17 | **54 %** | away from actual |
| NYISO 2023 CC_CHP PASS | +2.81 | ±3.82 | 1.01 | −0.42 | 42 % | toward actual |

- MISO's share stays inside 3 pp (−0.9 pp → about −1.1 pp).
- NYISO's share moves toward actual (+2.38 pp → lower).

**Receiving classes.** The released energy is re-dispatched elsewhere, so it can only push other classes up. A PASS can
fail only where the class is already over actual by more than its margin minus the release. No record meets that in any
keeper; SPP 2025 CC_REGULAR (margin 0.14) is under actual, so the release moves it toward actual.

Two MISO FAILs are under actual by less than the 1.7 TWh MISO release, so they *could* clear (FAIL→PASS) if enough of the
release went to them:

| record | model − actual, TWh | short of the band by |
|---|---:|---:|
| MISO 2019 ST_GAS | −8.71 | 0.71 |
| MISO 2021 CC_REGULAR | −8.15 | 0.15 |

These are upper bounds, not predictions, and rule 1 does not count them in the fix's favour. No determination moves on
these bounds.

### 7.4 What this changes in the recommendation

- Option (a) is safe on the scored record: no PASS→FAIL in nine keepers.
- MISO carries most of the exposure. Its keeper's p2 CHP floors sit on basis ratios up to 2.67, and those floors over-force
  CC_CHP by about 1.2 TWh/yr against its own artifact level. MISO CC_CHP would then drop further below actual, at up to
  54 % of its margin.
- SOCO's p95 ratio is 3.25 (a small CHP fleet).
- Both are the same basis bug in the p2 floor, not a swap effect. They strengthen the case for (a) over (b).
