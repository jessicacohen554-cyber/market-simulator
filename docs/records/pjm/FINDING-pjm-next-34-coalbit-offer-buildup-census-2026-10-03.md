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

Probe output: `results/phase0/pjm/_pjmnext34_coal_offer_buildup.json`. Readings were committed in `cd775b97` before
any number was computed. All seven years ran, one `fleet_only` rebuild per year, one process per year: the 13.3 GiB
cgroup cannot hold two rebuilds.

**Gates.**
- R0 passes in every year: unit-id cover 1.000, identity 0.999–1.000, `R ≥ vom` 1.000.
- `HR_m` is own-year on all of the weight it covers. It is absent (eGRID fallback, row excluded) on 0.006 / 0.000 /
  0.118 / 0.019 / 0.000 / 0.015 / 0.000 of `D_y`, 2019–25.
- Cross-check: the census `K` reproduces the NEXT-33 dark-MW-weighted keeper offer (21.85 vs 21.8 in 2019, 37.46
  vs 37.3 in 2024).

**Q1/Q2: the build-up** ($/MWh, `D_y`-weighted; `G` = measured HR × own delivered coal + VOM/adders):

| year | dark TWh | K | G | K − G | share K < G | B (band) | S (sigmoid) | m (floor) | s (seam) | b | π | HR_m | F $/MMBtu |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | 8.6 | 21.85 | 29.24 | **−7.39** | 0.89 | −3.70 | −5.43 | +1.67 | +0.07 | 0.82 | 0.76 | 10.67 | 2.26 |
| 2020 | 6.4 | 20.91 | 29.50 | **−8.58** | 0.93 | −3.45 | −7.03 | +1.70 | +0.19 | 0.82 | 0.68 | 10.79 | 2.20 |
| 2021 | 7.2 | 28.53 | 31.58 | **−3.05** | 0.70 | −4.67 | −0.65 | +2.13 | +0.14 | 0.80 | 0.97 | 10.74 | 2.21 |
| 2022 | 8.1 | 51.27 | 40.27 | +11.00 | 0.32 | −5.49 | +8.09 | +8.33 | +0.07 | 0.83 | 1.32 | 11.26 | 2.49 |
| 2023 | 3.1 | 26.68 | 37.82 | **−11.14** | 0.84 | −7.20 | −7.06 | +2.71 | +0.41 | 0.74 | 0.75 | 10.91 | 2.97 |
| 2024 | 3.6 | 37.46 | 46.21 | **−8.75** | 0.90 | −5.71 | −6.12 | +1.14 | +1.95 | 0.80 | 0.77 | 11.02 | 2.78 |
| 2025 | 4.2 | 34.72 | 39.73 | −5.00 | 0.72 | −8.35 | +1.48 | +1.37 | +0.49 | 0.75 | 1.04 | 10.71 | 3.07 |

- **Q1: BELOW in all three fail years** (and in 2023/24/25). The keeper's coal offer sits 3.0–8.6 $/MWh below the
  plant's measured going cost in the hours real coal sat dark.
- **Q2: NOT DISCRIMINATING.** `G − K` is 7.4 / 8.6 / 3.0 in 2019–21 against 11.1 / 8.7 in 2023/24. The controls sit
  **further** below cost than the fail years (fail-year minimum 3.0 vs control maximum 8.7 + 2).

**Q3: carrier.** Pooled 2019–21 shares of `G − K`: sigmoid `S` 0.69, band `B` 0.62, floor `m` −0.29, seam `s`
−0.02. Carrier `S`, with `B` a close second.
- The sigmoid term is gas-driven: π = 0.76 / 0.68 at 2019/20 gas, 0.97 in 2021, 0.75–0.77 again in 2023/24.
- The band term is `b` = 0.80–0.82 cap-weighted. By tranche, `committed` rows run at `b` = 0.548 (K 14.4 vs G 27.1
  in 2019), `econ*` at 0.92 and `peak` at 1.04.
- Fail-minus-control split of `G − K` (total −3.5: the fail years are *less* below cost):
  B −2.5, S −2.2, m +0.04, s +1.1. No component carries a fail-year excess.

**Q4: PJM's own offers** (`econ*`/`peak` rows, 0.51–0.76 of the weight):

| year | floor binds | P_off | K | G | share P_off < G |
|---|---|---|---|---|---|
| 2019 | 0.60 | 23.4 | 24.7 | 30.1 | 0.88 |
| 2020 | 0.54 | 21.1 | 23.2 | 30.0 | 0.91 |
| 2021 | 0.45 | 29.1 | 33.4 | 32.9 | 0.69 |
| 2023 | 0.67 | 31.3 | 34.4 | 39.4 | 0.72 |
| 2024 | 0.17 | 27.8 | 41.6 | 48.8 | 0.95 |

- **FALSIFIED** as worded in all seven years (`P_off ≤ K` on 0.66–0.91 of the weight).
- **Disclosure: as worded, the reading holds by construction on these rows.** The floor sets
  `K = max(mc_base, P_off) + s`, so `P_off ≤ K` wherever the surface prices the row. This was missed when the
  reading was fixed.
- The informative, non-tautological numbers are the two beside it:
  - **PJM's own LONG_RUN offers sit below the plant's measured going cost on 0.69–0.91 of the 2019–21 weight**
    (mean 21–29 vs 30–33 $/MWh).
  - The keeper's own construction (`mc_base`, before the floor) sits below those offers on only 0.45–0.60 of it.
- So the keeper floors coal **up** to PJM's offers, and those offers are themselves below cost. The NEXT-13 and
  midmerit-level statement (real coal offered below its replacement or full cost) holds on the dark-spell population.
- A raise toward `G` contradicts the measured offers in the fail years. That conclusion does not depend on the
  tautological reading.

**Q5: cost-consistent darkness.** Real zonal DA sat below `G` in 0.73 / 0.86 / 0.54 of the 2019–21 dark weight,
against 0.35 / 0.53 / 0.39 below the keeper offer `K` (NEXT-33). In the controls the share is 0.75 / 0.90.
- At the plant's measured going cost, most real darkness is price-consistent.
- It is equally price-consistent in the controls, so it does not separate the years.

### Readings

| reading | result |
|---|---|
| R0 / R0b | PASS (cover 1.000, identity ≥ 0.999; HR_m absent ≤ 0.12) |
| Q1 | **BELOW** in 2019, 2020 and 2021 (and 2023–25) |
| Q2 | **NOT DISCRIMINATING** (controls 8.7–11.1 below cost vs 3.0–8.6) |
| Q3 | carrier **S** (sigmoid) 0.69, **B** (band) 0.62; no fail-year excess in any component |
| Q4 | **FALSIFIED** (as worded, holds by construction; see the disclosure); PJM's own offers below `G` on 0.69–0.91 |
| Q5 | real DA < `G` on 0.54–0.86 of dark weight; not year-discriminating |

**Decision rule, applied:** Q2 fails and Q4 is FALSIFIED, so the decision rule cannot charter. **NOT CHARTERED.**
Nothing was built, solved or registered, and no matrix cell moves.

## §3 Consequence

- **The keeper's COAL_BIT offer is below the plant's measured going cost in the dark spells.** The sigmoid's
  cheap-gas discount and the `committed`/`econ_low` bands carry it. This is not what separates 2019–21 from 2023/24:
  the controls sit further below cost.
- **PJM's own coal offers are below measured going cost in the same hours.** The keeper floors its coal up to them
  in 0.45–0.60 of the fail-year econ weight. A below-cost coal offer is measured conduct, not a keeper defect.
  Raising the offer toward `G` is refuted on this population, as it was on the full fleet (FINDING-pjm-midmerit-level
  §3, NEXT-13).
- **Real darkness is cost-consistent at `G`** (0.54–0.86) and equally so in the controls. Real coal sitting out when
  the price is below its going cost, while still offering below cost, is commitment and availability conduct. The
  price-formation side cannot represent that difference by year.
- With NEXT-13/30/31 (availability), NEXT-32 (commitment), NEXT-33 (price) and NEXT-34 (offer level), every
  channel on COAL_BIT 2019–21 is now censused at zero LP and none charters.
  - COAL_BIT 2019–21 is a **frontier candidate on every channel**.
  - The frontier text and the frontier card belong to the desk lane (closeout-PJM-2), which holds the card until
    PJM-nuc promotes.
- The rule-1 band channel (`offer_curve_by_group`) is the only price channel. The census gives it no year-uniform
  operand: one value across years cannot close 2019–21 without moving 2023/24, which already sit further below cost.
- The Tait remap stays parked for the next PJM solve with a real lever.
