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
   - Under (a), the p2 floor in every other keeper, by its own basis ratios. Not measured here; the probe extends by
     adding a `KEEPERS` entry.
   - Expected scored effect: no C1 status flip in SPP or CAISO (§4).
5. **Order with MISO.** The fix must land before any MISO arm of the swap. The MISO > 100 % artifact rows additionally need
   the miso-95 re-derivation (w3g §4).

## 6. Matrix

No cell moves (nothing solved). The lane edits no ISO shard.
