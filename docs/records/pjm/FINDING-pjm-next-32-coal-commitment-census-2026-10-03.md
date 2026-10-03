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

Verdict: **NOT CHARTERED.** No ScenarioConfig field is built and nothing is solved.
The keeper `2026-10-02-w0-pjm-fix2` is unchanged.

| Year | X (TWh) | X / C1 overage | Floor share of X | Price-cleared share | Uncovered dark S / M / L (TWh) | Economic share, M+L (real price) | Economic share, M+L (keeper price) | Stops per unit | Stop p50 (h) | Stops < 16 h |
|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | 5.34 | 0.28 | 0.09 | 0.93 | 0.28 / 6.64 / 2.02 | 0.42 | 0.26 | 12.8 | 94 | 0.18 |
| 2020 | 3.53 | 0.27 | 0.09 | 0.84 | 0.24 / 5.09 / 1.28 | 0.73 | 0.33 | 11.3 | 83 | 0.22 |
| 2021 | 4.23 | 0.28 | 0.11 | 0.96 | 0.20 / 6.48 / 0.80 | 0.38 | 0.26 | 15.5 | 83 | 0.19 |
| 2022 | 4.32 | — | 0.09 | 0.99 | 0.22 / 5.66 / 2.44 | 0.34 | 0.17 | 12.8 | 79 | 0.19 |
| 2023 | 1.13 | — | 0.23 | 0.70 | 0.13 / 2.69 / 0.46 | 0.41 | 0.21 | 11.2 | 94 | 0.23 |
| 2024 | 0.85 | — | 0.24 | 0.45 | 0.13 / 2.54 / 1.12 | 0.77 | 0.68 | 11.8 | 101 | 0.20 |
| 2025 | 2.60 | — | 0.19 | 0.87 | 0.21 / 3.51 / 0.68 | 0.37 | 0.26 | 13.5 | 84 | 0.23 |

Exact values are in the JSON. The overage ratio is defined only for the 2019–21 pool.

- **Q1: PARTIAL (0.27–0.28).** In 2019–21 the keeper generates 3.5–5.3 TWh/yr in coal
  capacity whose real units were dark outside any committed window. That is about a
  quarter of the +13 to +19 TWh overage. Most of the overage, about 72 %, is loading on
  units the real fleet also had online.
- **Q2: PRICE-CLEARED.** The floor tranches (`mustrun` + `sync`) hold 0.095 of `X`,
  pooled over 2019–21. In 0.92 of `X` the keeper's own zone price is at or above the
  `mc` of the plant's highest dispatched tranche. `X` follows a daytime shape, peaking
  at 12:00–19:00, not a night or weekend trough. The LP runs this capacity because its
  own price clears it, not because a coal floor holds it through slack periods.
- **Q3: NOT ECONOMIC (0.496 pooled; 0.42 / 0.73 / 0.38).** At real prices, about half of
  the M+L dark MWh sits in spells that were uneconomic to stay on through, net of the
  100 $/MW start. At the keeper's prices, 0.17–0.33 of the same spells read uneconomic
  in 2019–22. The keeper's price runs above the real price in these spells. That is a
  price-level gap, not a missing commitment state.
- **Q4 timing (rule 18).** Real coal units stop 11–15 times a year. The median stop lasts
  79–101 h (multi-day). 0.18–0.23 of stops are shorter than the 16 h min-down. The keeper's implied plant off-events (229–887 a year across about 46 plants) come from LP plant-level zero crossings, not a commitment state. The
  real fleet does decommit across multi-day slack periods. But the keeper capacity in
  those hours clears on price, so a coal decommitment screen against the model's own P0
  prices would leave most of it running. Also from Q2 and Q3: floor MW inside real M+L
  spells is 1.6–2.2 TWh/yr (2019–22). Its allocated share of `X` is only 0.3–0.5 TWh,
  because those floor MW sit below the price-cleared econ rungs.

**Reading.** The census answers the owner's question:
- Yes, real PJM coal decommits across multi-day spells that the keeper keeps running.
- No floor holds that capacity on in the model, and the mechanism family the owner
  asked about (commitment state, rule 18) has no operand here. What keeps it running is
  the keeper's own clearing price sitting above both the real price and the plant's
  offer.

That is the same price-formation residue NEXT-28/29/30 measured from the offer side.
COAL_BIT 2019–21 C1 is therefore a frontier candidate on the availability family
(NEXT-13/30/31), and now on the commitment family as well. The frontier text belongs to
the desk lane closeout-PJM-2.

**Tait rider.** It stays parked. There is no real lever to carry it.

**Matrix.** No mechanism was armed or solved, so no PJM.js cell moves.
