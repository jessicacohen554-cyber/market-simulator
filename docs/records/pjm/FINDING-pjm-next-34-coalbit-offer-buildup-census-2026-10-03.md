# FINDING — PJM-NEXT-34: COAL_BIT offer build-up census (zero LP)

**Keeper:** `2026-10-02-w0-pjm-fix2` (bundle `w0_pjm_span`). **Zero LP, zero shards at this stage.**
Owner ruling (NEXT-33 card, 2026-10-03, *"Coal offer census (Recommended)"*): *"NEXT-34 = COAL_BIT OFFER BUILD-UP
CENSUS"*. In the hours real coal sat dark, does the keeper's COAL_BIT offer sit below the plant's measured going
cost, does it do so year-discriminatingly (2019–21 vs 2023/24), and which component carries it?
Probe `scripts/probes/_pjmnext34_coal_offer_buildup.py` → `results/phase0/pjm/_pjmnext34_coal_offer_buildup.json`.

## §0 What is already adjudicated (rule 28 check, D-2 enumeration on COAL_BIT non-floor rows)

The mechanisms that set a keeper COAL_BIT `committed` / `econ*` / `peak` bid (rule 19, D-2):

| # | mechanism | keeper value | cell |
|---|---|---|---|
| 1 | measured operating heat rate (`measured_coal_heat_rates`, CAMPD net, own year else pooled) | on | K |
| 2 | plant-monthly EIA-923 delivered coal (`coal_plant_monthly_pricing`) | on | K |
| 3 | `offer_curve_by_group["COAL_BIT"]` band multipliers on the HR (the rule-1 channel) | committed 0.548, econ_low 0.6556, econ_high 1.2664, peak 1.044, econ_low_share 0.55 | K |
| 4 | gas-keyed bituminous passthrough sigmoid on fuel (`coal_passthrough_sigmoids`) | floor 0.65 (override), ceil 1.32, gas_mid 3.40, slope 2.5 | K (gas_mid re-centre R, pjm-h7) |
| 5 | LONG_RUN mid-curve measured-offer floor on `econ*`/`peak` (`pjm_offer_midcurve_conditional`) | on | K |
| 6 | tranche startup amortization (P1 `mc_bid_adjust`) | on | K |
| — | `committed_band_measured_basis` | off | R (pjm-h8) |
| — | `pjm_replacement_cost_fuel` | off | R (NEXT-13: the keeper floors COAL_BIT econ up to PJM's measured offers in 41–63 % of econ hours; real coal offered below spot replacement cost 32–61 %) |
| — | `coal_econ_bound` (SRMC clamp) | off | `.` |
| — | `gas_electric_power_monthly_level` | on (gas side) | K |

Prior measured statements on the offer level: FINDING-pjm-midmerit-level-2026-07 §3 (PJM's submitted LONG_RUN coal
offers imply a flat passthrough ≈ 0.74/0.66/0.79 of full delivered cost, 2023–25: *"A coal offer RAISE is therefore
refuted by the measured submitted offers"*). NEXT-33 (post-hoc): at the real zonal DA, 0.47–0.65 of the 2019–21 dark
MW is in the money at the keeper offer.

**New evidence here:** none of the above decomposed the keeper offer **on the dark-spell plant-hours**, against the
**plant's own** measured going cost, per year. That is this census. No cell is re-tested.

## §1 Readings, fixed ex ante (committed before any number was computed)

**Population `D_y`** (each year 2019–25; fail years 2019/20/21, controls 2023/24; 2022 and 2025 context): the
NEXT-33 dark-spell weights. For each keeper COAL_BIT plant, the M+L uncovered real-dark spells of its coal-fuel CAMPD
units (≥ `COAL_BIN_MIN_DOWN_HOURS`, not covered by a committed extract), weighted `K*·peak_u/Σpeak` (exactly
`_pjmnext33_dark_offer_margin.run_year`). Within a plant-hour the weight is spread over the plant's non-floor
tranches (`committed`, `econ*`, `peak`; not `mustrun`/`sync`) in proportion to their `cap_mw`, as NEXT-33's
capacity-weighted offer did.

**Per tranche-hour quantities** (one paired `fleet_only` rebuild of the keeper recipe per year, through
`scripts/lib/bundle_fleet.py` with the fidelity guard, `pjm_da_virtual_bids` off as in NEXT-13):
- `K` = the keeper P1 offer `mc` in `unit_marginal_<y>` (what the LP saw).
- `HR_t` = rebuilt tranche heat rate; `F` = rebuilt fuel price (the plant-monthly EIA-923 delivered coal);
  `π` = the tranche's fuel passthrough, from `campd_tranche_fuel_frac` called exactly as `assembly.py` calls it;
  `R` = `mc_base − HR_t·F·π` (VOM + emission/NOx/SO2 adders, fuel-independent).
- `HR_m` = the plant's measured operating heat rate (`measured_coal_heat_rates("PJM", y)`, own year else pooled);
  `b` = `HR_t / HR_m` (the effective band multiplier).
- `m` = the mid-curve floor markup (`build_pjm_offer_midcurve_conditional_markup`); `s` = `K − mc_base − m`
  (startup amortization and anything else at the P1 seam).
- **Measured going cost** `G = HR_m·F + R`: the plant's own measured operating HR × its own delivered coal + the
  keeper's VOM and adders. It is forward-reproducible (rule 13: a machine HR and a delivered fuel price both
  regenerate from forward drivers).
- `P_off` = PJM's measured LONG_RUN offer at the row's within-plant share, `mult(LONG_RUN, y, bin(t), share) ×
  gas_day(t)` (`_pjm_midcurve_row_target`, the surface the floor reads; unit-masked DataMiner offers, normalised).

**Decomposition (exact):** `K − G = HR_m·F·(b·π − 1) + m + s`, split symmetrically
- band term `B = HR_m·F·(b − 1)·(π + 1)/2`,
- sigmoid term `S = HR_m·F·(π − 1)·(b + 1)/2`,
- floor term `m`, seam term `s`. `B + S + m + s = K − G` identically.

**Gates (stop and report if failed):**
- **R0 IDENTITY.** Rebuilt unit ids cover ≥ 0.99 of `D_y` weight, and `|mc_base + m − K| ≤ 0.05 $/MWh` OR `s ≥ 0`
  on ≥ 0.99 of it (startup amortization only raises a bid). `R ≥ vom − 0.01` on ≥ 0.99 of it.
- **R0b SOURCES.** Report the `D_y` weight share whose `HR_m` is own-year, pooled or absent (absent ⇒ `b` unread,
  row excluded and counted).

**Readings:**
- **Q1 — BELOW COST.** Per year, mean `K − G` over `D_y` and the share of `D_y` weight with `K < G`.
  `BELOW` iff mean `K − G < 0` and that share ≥ 0.5.
- **Q2 — YEAR DISCRIMINATION.** `DISCRIMINATING` iff min over 2019–21 of mean `G − K` ≥ max over 2023/24 of mean
  `G − K` + 2 $/MWh (the NEXT-33 Q5 margin).
- **Q3 — CARRIER.** Share of pooled 2019–21 mean `G − K` carried by each of `B`, `S`, `m`, `s` (signed; `−term`).
  The carrier is the largest. Also the component split of the difference (pooled 2019–21 mean `G − K`) − (pooled
  2023/24 mean `G − K`): which component carries the discrimination. Reported by tranche kind as well
  (`committed` / `econ*` / `peak`).
- **Q4 — PJM'S OWN OFFERS.** Over `D_y` (`econ*`/`peak` rows, where the floor reads the surface): the share of
  weight where the floor binds (`m > 0`); the mean `P_off`, `K` and `G`; and the share where `P_off < G` (real coal
  offered below its measured going cost).
  `FALSIFIED` iff `P_off ≤ K` on ≥ 0.5 of the 2019–21 `econ*`/`peak` weight in ≥ 2 of 2019–21: PJM's own coal offers
  in the dark spells sit at or below the keeper's, so a raise toward `G` contradicts the measured offers (the
  NEXT-13 and midmerit-level falsifier, on this population).
- **Q5 — COST-CONSISTENT DARKNESS.** The share of `D_y` weight where the real zonal DA sits below `G` (real coal dark
  when the price is below its measured going cost), against the NEXT-33 share below `K`.

**Decision rule (ex ante).** CHARTERED only if Q1 is `BELOW` in ≥ 2 of 2019–21, Q2 is `DISCRIMINATING`, Q4 is not
`FALSIFIED`, and the Q3 carrier is a component whose channel is not R/I/G without new evidence and has a rule-13
measured basis.
- Carrier `B` (the band): the operand is the rule-1 channel only (one value across every scored year, fixed ex ante
  in a PRECOMMIT, never swept). It goes to the owner on a decision card; nothing is built here.
- Carrier `S` (the sigmoid): the operand is a measured-basis replacement of the bituminous econ passthrough. It is a
  registered default-off field with a matrix row, a cell in every shard, tests and G-DRIFT, then a 7-shard solve
  with the Tait remap as the rule-14 rider.
- Carrier `m` or `s` cannot sit below cost (both are ≥ 0), so either one is a contradiction to report.

Otherwise **NOT CHARTERED**: the component and year profile are recorded and the result goes on a decision card.

## §2 Result

*(computed after this section's readings were committed)*
