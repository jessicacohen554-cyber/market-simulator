# FINDING — PJM-NEXT-32: coal multi-day slack decommitment census (ZERO LP)

Lane: PJM-NEXT-32 (branch `claude/pjm-next-32`). Owner ruling 2026-10-03 (NEXT-31 card):
NEXT-32 runs a commitment census. Keeper under test: `2026-10-02-w0-pjm-fix2`
(`results/calibration/w0_pjm_span`, 2019–2025). Probe:
`scripts/probes/_pjmnext32_coal_commitment_census.py`. Output:
`results/phase0/pjm/_pjmnext32_coal_commitment_census.json`.

**Question.** Does the real PJM coal fleet shut units across slack periods (nights,
weekends, shoulder weeks) that the pure-LP keeper keeps at or near its cap? If so, what
holds them on in the model: a coal floor (commitment scaffolding) or the model's own
price?

## 0. Matrix check (rule 28) and what already floors COAL_BIT (D-2, rule 19)

| Cell (PJM.js) | Verdict | Bearing |
|---|---|---|
| `coal_sync_window_commitment_grain` | K | Day-grain placement of the coal sync floor. Armed. |
| `tranche_startup_amortization` | K | Startup cost amortized into the econ/peak offers. Armed. |
| `mustrun_commitment_feasibility_clip` | R | CC/ST clip. Not re-tested. |
| `committed_band_measured_basis` | R | Committed band at measured HR. Not re-tested. |
| `pjm_gas_commitment_bridge` | R | Gas leg. Not re-tested. |
| `coal_committed_nested_on_mustrun`, `commitment_floor_window_netload`, `mustrun_window_commitment_grain` | U | Untested here. |
| `mustrun_layup_window_mask` | U | Masks the CC/ST_GAS must-run floors only. It does not reach the coal seam (`data/fleet/arrays.py`, CC and ST_GAS branches). |

What floors COAL_BIT in the keeper (D-2): the per-plant coal must-run tranche
(`coal_mustrun_per_plant`, `coal_mustrun_online_pmin`; suffix `mustrun`, offered near
VOM) and the coal synchronization tranche (`coal_sync_srmc_tranche` with
`coal_sync_window_commitment_grain`; suffix `sync`). The `committed`, `econc*`, and
`peak` tranches are priced offers with no floor. In this census "floor tranche" means
`mustrun` + `sync`.

Rule-18 parameters (cited, not tuned): `COAL_BIN_MIN_DOWN_HOURS = 16` and
`BIN_STARTUP_COST_PER_MW["COAL_BIT"] = 100 $/MW` (`data/fleet/eia860.py`, NREL
SR-5500-55433).

## 1. Readings (fixed ex ante, before any number is computed)

Population: keeper COAL_BIT plants (`unit_marginal_<Y>` `plant_group == COAL_BIT`) and
their CAMPD units whose `primaryFuelInfo` contains "Coal" (NEXT-31 lesson x). Unit
weight `w_u` = the unit's peak gross over the plant's coal-unit peak sum. `K*` is the
plant's keeper year-max `cap_mw`. "Uncovered dark" is NEXT-31's definition: `opTime == 0`
(or no row) and not inside any of the three committed extracts at the loader's day grain.
Spell bands use the rule-18 min-down: **S** < 16 h, **M** 16–119 h, **L** ≥ 120 h.

- **Q1 MATERIALITY.** Per plant-hour, model-runs-freed MW
  `X = min(max(0, mw − K*·ON_real), K*·Σ_u w_u·uncovered_dark_u)`, where `ON_real` is the
  real online coal-capacity share. `X` is MW the keeper generates above what the real
  online units could carry at full `K*`, charged to uncovered dark capacity up to its
  size. Annual `ΣX` (TWh) is read against the keeper's C1 COAL_BIT overage
  (+19 / +13 / +15 TWh, 2019 / 20 / 21).
  - **MATERIAL** if `ΣX ≥ 0.5 ×` the overage in each of 2019, 2020 and 2021.
  - **PARTIAL** if `ΣX ≥ 0.25 ×` the overage in each of those years.
  - **IMMATERIAL** otherwise.
- **Q2 DRIVER.** `X` is allocated over the plant's dispatched tranches from the highest
  `mc` downward (the order an LP backs off). The floor share is the part of `X` that
  lands in `mustrun` + `sync`.
  - **FLOOR-HELD** if the floor share pooled over 2019–21 is ≥ 0.5.
  - **PRICE-CLEARED** otherwise.

  Also reported: the share of `X` in hours where the keeper's own zone price is ≥ the
  `mc` of the plant's highest dispatched tranche.
- **Q3 ECONOMIC.** For each uncovered dark spell in bands M and L, the forgone margin per
  MW is `Σ_h (p_real − mc_plant)`. `p_real` is the real PJM DA system LMP
  (`actual_lmp_hourly_PJM.parquet`). `mc_plant` is the keeper's capacity-weighted `mc`
  over the plant's non-floor tranches (`committed`, `econc*`, `peak`) in that hour.
  - A spell is **economic** if its forgone margin is below the startup cost of
    100 $/MW. Over such a spell, staying on would have earned less than a restart costs.
  - **ECONOMIC** if economic spells hold ≥ 0.5 of the M+L uncovered dark MWh pooled over
    2019–21.

  Also reported: the same spells' keeper margin, using the keeper's zone price in place
  of `p_real`. This separates a model price-level gap from a commitment-state gap.
- **Q4 TIMING (rule 18, informational).** Real coal unit stops per unit-year and dark
  spell length p10/p50/p90, with the share of stops shorter than the 16 h min-down.
  Against these: the keeper's implied plant off-events (`mw` from > 0 to 0) and the hours
  the floor tranches carry `mw > 0` inside real M+L spells.
- **VERDICT.** **CHARTERED** iff Q1 is MATERIAL or PARTIAL, Q2 is FLOOR-HELD and Q3 is
  ECONOMIC. The operand would then be a coal floor binding through real economic
  multi-day decommitment (rule 17). The candidate mechanism is a coal-seam
  decommitment screen identified by rule-18 parameters (min-down 16 h, startup
  100 $/MW) against the model's own P0 prices, so it regenerates forward (rule 13).
  Any other combination is **NOT CHARTERED**:
  - If Q2 is PRICE-CLEARED, the keeper runs the capacity on its own price. That is a
    price-formation question, not commitment state.
  - If Q1 is IMMATERIAL, the census does not explain the overage.

Pre-registration: these readings are committed before the probe is written.

## 2. Results

(Filled after the probe runs.)
