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

Probe output: `results/phase0/pjm/_pjmnext33_slack_price_census.json` (all seven years, ~25 min in the 13.3 GiB cgroup).

**Q1 — the gap in each population** ($/MWh; Δ = keeper zone price − real zonal DA, population means):

| year | D Δ | D Δ_lvl | D Δ_spr | D keeper / real | L Δ | L keeper / real | A Δ |
|---|---|---|---|---|---|---|---|
| 2019 | +0.30 | +1.40 | −1.10 | 25.55 / 25.25 | +4.44 | 23.10 / 18.65 | +0.48 |
| 2020 | +1.88 | +2.78 | −0.90 | 23.01 / 21.13 | +5.46 | 20.94 / 15.48 | +2.42 |
| 2021 | +1.23 | +1.99 | −0.76 | 34.83 / 33.60 | +7.37 | 33.04 / 25.68 | +0.14 |
| 2022 | −3.95 | −3.06 | −0.89 | 60.66 / 64.61 | +12.65 | 56.75 / 44.10 | −9.39 |
| 2023 | +0.23 | +1.29 | −1.07 | 29.43 / 29.20 | +7.42 | 25.83 / 18.42 | −0.81 |
| 2024 | +0.81 | +0.59 | +0.22 | 29.10 / 28.29 | +12.15 | 29.77 / 17.61 | −2.36 |
| 2025 | +1.05 | +1.55 | −0.50 | 41.73 / 40.68 | +11.20 | 36.44 / 25.24 | −6.76 |

- **In the dark spells the keeper price is about right at zonal grain:** +0.3 / +1.9 / +1.2 $/MWh in 2019–21.
- The real coal zones (AEP-Ohio 0.33–0.34, West-APS 0.33, Dominion 0.22, SWMAAC 0.10 of 2019 D weight) clear
  above the real system price. The zonal spread therefore takes back 0.8–1.1 $/MWh of the system-level gap NEXT-32
  Q3 used.
- In `L_y` the gap is pure level, and it is **larger in the controls** (+7.4 / +12.2 / +11.2 in 2023–25) than in
  the fail years (+4.4 / +5.5 / +7.4).

**Q2 — keeper setter cells, share of Σ w·Δ over D.** Pooled 2019–21 over anchored load:
- CC_REGULAR:econc 0.45, COAL_BIT:econc 0.40, CC_REGULAR:committed 0.20, ST_CHP:committed 0.10, import 0.03.
- Anchored weight is 0.75–0.77; shares are signed, so they can exceed 1.
- In `L_y` the setters are the NEXT-29 cells (COAL_BIT econc and CC_REGULAR econc, ~0.2 each) plus unanchored
  0.29–0.30.

**Q3 — real side.** The IMM marginal fuel is gas-dominant in 0.82–0.84 of D weight (coal-dominant 0.04–0.08).
The share of Σ w·Δ where the keeper setter is coal and IMM gas ≥ 0.5 is 0.55 / 0.29 / 0.32 (pooled 0.33). In
`L_y` it is 0.21–0.27.

**Q4 — CC_REGULAR econ setters.** Measured incremental HR coverage is 0.97–0.99. In D, the offer-above-measured-cost
term is +0.80 / +1.32 / +2.50 against a mean Δ of +1.31 / +2.79 / +0.92. In `L_y` the offer sits at measured cost
(−1.50 / −0.61 / −0.01), and the measured cost at delivered gas is +6.1 / +5.9 / +7.1 above the real price
(median real/gas 5.6–5.9 vs measured incremental HR 6.8–7.1).

**Q5 — year discrimination.**
- D: fail-year minimum +0.30 vs control maximum +0.81.
- L: fail-year minimum +4.44 vs control maximum +12.15.

### Readings

| reading | result |
|---|---|
| Q1 | **LEVEL** (Δ_spr is negative over D in all three fail years) |
| Q2 | **CONCENTRATED**: carrier CC_REGULAR:econc; top two (with COAL_BIT:econc) 0.86 |
| Q3 | **COAL-FOR-GAS** (0.33 pooled ≥ 0.3) |
| Q4 | **OFFER-SIDE** over D (2019 and 2021 pass; 2020 1.32 < 0.5 × 2.79) |
| Q5 | **NOT DISCRIMINATING** in D and in L |

**Decision rule, applied:** Q5 fails in both populations, so neither (a) nor (b) can charter. **NOT CHARTERED.**
- The D gap is small in every year, and the L gap is larger in the controls. The keeper's price level is not what
  separates 2019–21 from 2023–24.
- The low-hour level gap is the NEXT-29 object: real price below measured CC cost at delivered gas. Its channels are
  adjudicated (`pjm_replacement_cost_fuel` R; `zonal_gas_basis` K, hub series DATA-BLOCKED).
- Nothing was built, solved or registered, and no matrix cell moves.

### Post-hoc supplementary (NOT a pre-registered reading)

Probe `scripts/probes/_pjmnext33_dark_offer_margin.py` → `results/phase0/pjm/_pjmnext33_dark_offer_margin.json`.
It takes the keeper's own COAL_BIT offer (capacity-weighted `mc` of the plant's non-floor tranches) over the same
dark spells, weighted by dark MW:

| year | dark TWh | keeper offer | keeper zone p | real zonal DA | offer / gas | in money at real DA | at keeper p |
|---|---|---|---|---|---|---|---|
| 2019 | 8.6 | 21.8 | 25.6 | 25.3 | 6.89 | 0.65 | 0.78 |
| 2020 | 6.4 | 20.9 | 23.0 | 21.1 | 7.89 | 0.47 | 0.69 |
| 2021 | 7.2 | 28.8 | 34.8 | 33.5 | 6.56 | 0.61 | 0.76 |
| 2022 | 8.1 | 51.0 | 60.7 | 64.7 | 7.55 | 0.64 | 0.81 |
| 2023 | 3.1 | 26.7 | 29.5 | 29.3 | 8.28 | 0.60 | 0.79 |
| 2024 | 3.6 | 37.3 | 29.1 | 28.3 | 12.52 | 0.29 | 0.36 |
| 2025 | 4.2 | 34.7 | 41.7 | 40.7 | 8.23 | 0.61 | 0.74 |

**Real coal sat dark at prices that clear the keeper's own coal offer.** At the real zonal DA, 0.47–0.65 of the
2019–21 dark MW is in the money at the keeper offer, which sits 0.2 / 3.4 / 4.7 $/MWh below the real price (2019 / 20 / 21). The excess
energy is cleared by the keeper's coal offer level, not by its price. Only 2024 prices coal out (offer/gas 12.5).
2023 and 2025 look like the fail years per dark MW; what separates them is the dark volume (3–4 vs 6–9 TWh).

## §3 Consequence

- The slack-hour price census charters nothing. The keeper's zone price in the hours real coal sat dark is within
  0.3–1.9 $/MWh of the real zonal DA, and the low-hour level gap is larger in the controls.
- NEXT-32's Q3 inference ("keeper price above real in the spells") is a system-price artefact. At zonal grain the
  margin that clears COAL_BIT is the keeper's **coal offer level** against real coal's revealed going cost. Real coal
  sat out at the real zonal price, which the keeper's offer clears.
- Mechanisms on that rung (D-2): `coal_passthrough_sigmoids` K (gas_mid re-centre R), `committed_band_measured_basis`
  R, `offer_curve_by_group` K (the rule-1 band channel), `pjm_replacement_cost_fuel` R. A NEXT-13 falsifier still
  stands: the keeper already floors COAL_BIT econ up to PJM's measured offers in 41–63 % of econ hours.
- **Candidate next zero-LP question (new evidence, not a re-test):** rebuild the keeper COAL_BIT econ offer
  (HR × fuel + VOM + adders, sigmoid floor) on the dark-spell plant-hours. Compare it with each plant's measured
  going cost (CAMPD heat input / gross load × EIA-923 own delivered coal + VOM) and with PJM's unit-masked coal
  offers in those hours. Ask whether the keeper's coal offer sits below the plant's measured cost in the dark
  spells, year-discriminatingly.
- COAL_BIT 2019–21 remains a frontier candidate on availability (NEXT-13/30/31), commitment (NEXT-32) and price
  formation (NEXT-33). The frontier text belongs to the desk lane.
- The Tait remap stays parked.
