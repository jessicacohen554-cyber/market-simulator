# FINDING — PJM-NEXT-33: slack-hour price census (zero LP)

**Keeper unchanged:** `2026-10-02-w0-pjm-fix2` (bundle `w0_pjm_span`). **Zero LP, zero shards.**
Owner ruling (NEXT-32 card, 2026-10-03): *"NEXT-33 = SLACK-HOUR PRICE CENSUS"*. Why does the keeper's price sit above
the real DA price in the hours real coal sits dark, and in low-price hours generally, so that COAL_BIT clears?
Probe `scripts/probes/_pjmnext33_slack_price_census.py` → `results/phase0/pjm/_pjmnext33_slack_price_census.json`.

## §0 What is already adjudicated (rule 28 check, D-2 enumeration)

- NEXT-29: setters in real low hours `L_y` are COAL_BIT `econc` and CC_REGULAR `econc`; the setter offer sits
  +1.3…+2.0 implied MMBtu/MWh above the real price; the model is quantity-short below the real price. NOT CHARTERED:
  every channel on the CC rung is adjudicated. `offer_curve_by_group` K (econ_low 0.96, the rule-1 band),
  `pjm_midcurve_belt` K (L2 closed at phase 0), `measured_offer_surface` R, `gas_offer_margin_anchor_vintage` R,
  `zonal_gas_basis` K (hub series DATA-BLOCKED), `pjm_replacement_cost_fuel` R.
- NEXT-28: committed rungs set price in only 2–7 % of load-hours; sunk no-load is not the floor lever.
- `coal_passthrough_sigmoids` K, `committed_band_measured_basis` R: the coal econ/committed offer level.
- `measured_interface_limits` K: the measured TTC keeper topology.

NEXT-29 used the **system** DA price. This census adds the **zonal** real DA (`actual_lmp_zonal_PJM.parquet`, the eight
model zones 1:1) and the NEXT-32 dark-spell population. Neither has been read against the keeper before.

## §1 Readings, fixed ex ante (committed before any number was computed)

**Populations** (each year 2019–25; fail years 2019/20/21, controls 2023/24):
- `D_y`: zone-hours weighted by the NEXT-32 M+L uncovered real-dark coal-fuel MW of COAL_BIT plants (`K*·unc_ml`,
  spells ≥ `COAL_BIN_MIN_DOWN_HOURS`, not covered by a committed extract), attached to each plant's keeper zone.
  Built with the NEXT-32 helpers (`coal_units`, `covered_masks`, `keeper_plants`).
- `L_y`: NEXT-29 real low hours (system DA / delivered gas < 6.5), zone-hours weighted by keeper zone demand.
- `A_y`: all zone-hours, keeper-demand weighted (context only).

**Gap.** `Δ(z,h) = p_keeper(z,h) − p_real(z,h)`: keeper P1 zone price against real zonal DA. `PJM_external` is
excluded.

- **Q1 — level vs spread.** Split `Δ = Δ_lvl(h) + Δ_spr(z,h)`. `Δ_lvl` is the keeper system price minus the real
  system price, both weighted by keeper zone demand. `Δ_spr` is the keeper zone spread minus the real zone spread.
  Report the population-mean Δ, Δ_lvl and Δ_spr over `D_y`, `L_y` and `A_y`.
  Reading: **SPREAD-carried** iff mean Δ_spr over `D_y` ≥ 0.4 × mean Δ over `D_y` in ≥ 2 of 2019/20/21; else **LEVEL**.
- **Q2 — who sets the keeper price in `D_y`.** Anchor zone-hours with the NEXT-28 rule: `marginal == 1`, nearest `mc`
  in ratio, within `ANCHOR_TOL` = 0.06. Cells follow NEXT-29 (`plant_group:tranche`, econ split
  econc/econlo/econhi). The `import`, `hydro`, `nuclear`, `VIRTUAL_*` units are kept as cells, plus `unanchored`.
  Credit `w·Δ` to the anchored cell. Report the share of Σ `w·Δ` by cell.
  Reading: the **carrier** is the top cell pooled over 2019–21. **CONCENTRATED** iff the top two cells hold ≥ 0.6 of
  anchored Σ `w·Δ`.
- **Q3 — the real side.** Use the IMM time-weighted marginal fuel by hour. Bucket each `D_y` hour by its dominant real
  fuel (share ≥ 0.5: gas, coal; else mixed). Report the share of Σ `w·Δ` and the mean Δ per bucket, and separately
  the share of Σ `w·Δ` in hours the keeper setter is coal while IMM gas ≥ 0.5.
  Reading: **COAL-FOR-GAS** iff that last share ≥ 0.3 pooled over 2019–21.
- **Q4 — offer side vs real side, CC carrier.** For anchored CC_REGULAR econ zone-hours, `p_meas` is the plant's
  measured CAMPD incremental HR (`_pjmco_0d` plant artifact, `inc_hr_net`) × NEXT-11 delivered gas + `VOM["gas_cc"]`.
  Split the setter's Δ = (`mc − p_meas`) + (`p_meas − p_real`).
  Reading: **OFFER-SIDE** iff the first term ≥ 0.5 of the mean Δ in ≥ 2 fail years; else **REAL-BELOW-COST**: the real
  price clears below what a measured CC costs at delivered gas. For a COAL_BIT carrier report median `mc`/gas against
  median `p_real`/gas only; no measured coal incremental HR artifact exists.
- **Q5 — year discrimination.** Reading: **DISCRIMINATING** iff min over 2019–21 of mean Δ over `D_y` ≥ max over
  2023/24 + 2 $/MWh. Repeat over `L_y` with the same test.

**Decision rule (ex ante).** Chartered only if Q5 discriminates and either:
- (a) Q1 is SPREAD and the spread names a zone/interface object whose matrix cell is not R/I/G without new evidence; or
- (b) Q4 is OFFER-SIDE on a carrier rung whose channel is not R/I/G without new evidence and has a rule-13 measured
  basis.

A COAL-FOR-GAS Q3 with a LEVEL Q1 and a REAL-BELOW-COST Q4 restates NEXT-29 on the dark population: **NOT CHARTERED**.
The setter class and component are named and recorded. Any build follows (b) of the lane: a default-off registered
field, a matrix row with a cell in every shard, tests, G-DRIFT, then a 7-shard solve with the Tait remap as the
rule-14 rider.

## §2 Result

(Filled after the probe runs; §1 is not edited.)
