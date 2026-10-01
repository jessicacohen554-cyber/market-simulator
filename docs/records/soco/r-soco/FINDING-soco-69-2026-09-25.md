# FINDING — soco-69: the ST_GAS deficit is merit order, and in 2019–2022 the displacer is an UNMEASURED coal must-run slab

Lane soco-69, 2026-09-25. DATA PROFILE soco. Zero LP in this document; the parent solves nothing (rule 32(a)).

**Keeper / control of record:** `2026-09-25-soco68-summer-basis` (bundle `results/calibration/soco68_span`,
2019–2025; legs solved at `34f3d4aa696110a0841ac76a3ae0710a1ac85ea1`). PR #6667 is merged; `keepers/SOCO.json`
names it.

**Per-plant legs:** recovered at zero LP from the soco-68 shard branches, which still exist, into
`results/calibration/soco68_<Y>`:

| year | commit |
|---|---|
| 2019 | `39228944` |
| 2020 | `9017282f` |
| 2021 | `0f431169` |
| 2022 | `8b145a7b` |
| 2023 | `b0b25e10` |
| 2024 | `44c34569` |
| 2025 | `44f8cb64` |

The legs are gitignored and nothing is tracked.

**Probes:**

- `scripts/probes/_soco69_phase0.py`: the decomposition, plus a `greedy` subcommand.
- `scripts/probes/_soco69_arm_census.py`: `fleet_only` rebuilds, keeper vs arm.
- `scripts/probes/_soco69_gdrift_identity.py`: G-DRIFT.

## 0. G-DRIFT against `34f3d4aa` (rule 29(b))

`_soco69_gdrift_identity.py`, which is the soco-68 instrument re-pointed at `soco68_span`, found **every LP input
bit-identical in all seven years**, labels included.

| instrument | what changed | classification |
|---|---|---|
| ScenarioConfig defaults | 5 path defaults (`campd_bins_path`, `control_retrofit_path`, `plant_emission_rates_path`, `plant_emission_rates_v2_path`, `plant_registry_path`) | INERT: the absolute worktree path differs, and the fleet arrays prove it |
| ScenarioConfig fields added | 2 (`nwpp_demand_plant_basis`, `nyiso_ldc_generator_delivered_gas`) | INERT: other ISOs' gated fields, absent from the recipe |
| top-level constants | `CAMPD_BINNING_ISOS`, `RGGI_MEMBER_STATES_BY_YEAR` | INERT: the arrays are identical |

**Form 4 is valid. The committed `soco68_span` is the control, and no control solve is spent.**

## 1. Task 1: the ST_GAS deficit, per plant and year

**Method.** Hours are partitioned exactly, and the construction was declared in the probe docstring before any
number was read.

- `A_t` is CEMS gross MW over the plant's ST_GAS boiler units (the committed `campd_st_heat_rates_SOCO_units.csv`
  map), scaled to the benchmark row.
- `M_t` is model P1 MW; `C_t` is tranche availability; `gap` is the plant's cheapest available tranche `mc` minus
  the zone price.

The legs are:

- **(c) avail:** CEMS synced, model unavailable.
- **(a) hours:** CEMS synced, model available but off, split by gap band.
- **(b) load:** both on. `b_cap` is the part where the model sits at its ceiling; `b_econ` is below the ceiling.
- **extra:** model on, CEMS off.

The legs sum to D exactly (asserted).

**Class totals, TWh** (plant-block sum; Crist's 2021–22 rows have no CEMS boiler series and sit in "other"):

| year | D | (c) avail | (a) ≤$1 | $1–3 | $3–6 | >$6 | (b) b_cap | b_econ | other |
|---|---|---|---|---|---|---|---|---|---|
| 2019 | **7.59** | 0.08 | 0.24 | 1.70 | 0.74 | 2.02 | 0.14 | 2.69 | 0 |
| 2020 | 5.62 | 0.11 | 0.21 | 1.05 | 0.51 | 1.99 | 0.04 | 1.72 | 0 |
| 2021 | 6.60 | 0.24 | 0.13 | 0.36 | 0.62 | 2.99 | 0.01 | 0.69 | 1.56 (Crist) |
| 2022 | 5.70 | 0.36 | 0.11 | 0.13 | 0.69 | 2.14 | 0.06 | 1.68 | 0.54 (Crist) |
| 2023 | 5.50 | 0.12 | 0.49 | 0.45 | 0.23 | 1.26 | 0.20 | 2.76 | 0 |
| 2024 | 4.90 | 0.13 | 0.37 | 0.84 | 0.51 | 1.27 | 0.13 | 1.65 | 0 |
| 2025 | 5.23 | 0.17 | 0.30 | 0.38 | 0.63 | 1.78 | 0.11 | 1.86 | 0 |

**2019 per plant, TWh:**

| plant | CEMS h | model h | bench | model | D | hours | load | median gap off, $/MWh |
|---|---|---|---|---|---|---|---|---|
| Gaston (26) | 6,180 | 1,434 | 2.90 | 0.24 | **2.66** | 2.06 | 0.58 | 6.1 |
| Watson (2049) | 7,116 | 3,217 | 2.55 | 0.52 | 2.04 | 1.09 | 0.93 | 8.7 |
| Yates (728) | 6,774 | 3,205 | 2.05 | 0.25 | 1.80 | 0.95 | 0.84 | 9.9 |
| Greene County (10) | 8,760 | 5,367 | 1.72 | 0.79 | 0.93 | 0.45 | 0.48 | 9.4 |
| Barry (3) boilers | 1,091 | 0 | 0.17 | 0 | 0.17 | 0.15 | 0 | 11.5 |

**Reading, by leg:**

- **(c) Availability and outage windows are not the channel.** They account for 0.08–0.36 TWh a year, set aside
  Crist's boundary rows. The Barry-boiler → CC_REGULAR routing (≤0.06 TWh) sits inside this and is immaterial.
- **(a) Hours and (b) loading are both merit order (d).**
  - An available boiler that is off sits **$1–10+/MWh above the model's clearing price**.
  - A synced boiler runs only its committed tranche: `b_econ` 0.7–2.8 TWh against `b_cap` ≤0.2. Its econ bands
    are out of merit.
  - The soco-62 "commitment hours" deficit is this same object seen from the commitment side.
- **So the lever is whatever sets the clearing price below the boilers.** That differs by period.

## 2. What displaces the boilers: two regimes

**Class errors, model − EIA-923, TWh (keeper):**

| year | ST_GAS | COAL (BIT+PRB) | CT_PEAKER | CC_REGULAR |
|---|---|---|---|---|
| 2019 | −7.94 | **+4.37** | −0.77 | −2.15 |
| 2020 | −6.23 | **+4.46** | 0.01 | −4.68 |
| 2021 | −6.87 | **+9.48** | −2.02 | −2.08 |
| 2022 | −5.90 | **+9.07** | −2.48 | −3.85 |
| 2023 | −5.65 | −4.30 | **+4.60** | +3.86 |
| 2024 | −5.09 | −5.82 | **+3.15** | +2.88 |

- **2023–2024: CT displaces the boilers.** This is the start-cost object (SOCO-62/64/65), and
  `tranche_startup_amortization` is `G`. The owner question stays open and is **not** armed here.
- **2019–2022: COAL displaces the boilers.** CT is itself under-dispatched, so no CT cost lever reaches these
  years.

**Where the coal excess sits.** `thermal_tranches_SOCO.csv` (derived on 2023–2025 CEMS) carries **measured COAL
rows for only Bowen (703), Miller (6002) and Scherer (6257)**. Every other SOCO coal plant has no row and falls to
`_DEFAULT_TRANCHE_PCT_BY_GROUP`:

- a **45 %-of-nameplate `_mustrun` tranche**;
- priced at **$4.50/MWh**, VOM only;
- present in all 8,760 hours unless an outage window zeroes it.

The unmeasured plants are Barry (3), Gaston (26), Crist (641), Wansley (6052) and Daniel (6073); in 2025 also Gorgas
(8) and Hammond (708), which are dark.

| year | unmeasured must-run output, TWh | unmeasured plants: model / EIA-923, TWh | of which bound while the plant's own CEMS coal units are OFFLINE, TWh |
|---|---|---|---|
| 2019 | 15.86 | 16.31 / 13.50 | **3.99** |
| 2020 | 15.16 | 15.46 / 8.72 | **7.34** |
| 2021 | 12.20 | 17.51 / 10.54 | **4.72** |
| 2022 | 6.60 | 12.49 / 7.81 | 0.23 |
| 2023 | 4.60 | 4.60 / 4.96 | 0.67 |
| 2024 | 4.01 | 4.41 / 3.99 | 1.09 |
| 2025 | 4.22 | 7.31 / 4.51 | 0.93 |

**Wansley (6052) is the extreme.** Its 695 MW slab binds all 8,760 h in 2019–2021 and yields **6.28 TWh** a year.
Its CEMS coal units were on only 3,781 / 511 / 2,173 h, and EIA-923 shows 1.82 / 0.14 / 1.11 TWh.

- `campd-unit-outages-perunitdark-SOCO.csv` has **no row for 6052 coal**: the outage deriver's in-merit filter
  correctly excludes economic reserve-shutdown.
- The only thing holding it on is the unmeasured default.

**The same defect elsewhere:**

- Crist is bound 8,760 h against 7,621 / 5,155 CEMS-on h in 2019 / 2020.
- Barry coal is bound 8,760 h against 3,958 / 1,794 / 2,095 h in 2023–2025.
- At Gaston and Daniel, and Barry in 2019–2021, the slab binds almost only inside CEMS-on hours, because the outage
  overlay windows it there. The *level* (45 %) is still unmeasured.

**This is rule 17 `[R-FLOOR-WINDOW]` by definition.** The floor states no driver, no window and no measured level,
and it binds in 0.2–7.3 TWh a year of hours in which the plant's own record shows it offline.

`campd_bins.py` states the defect in its own comment (pjm-h14): "The plants with the LEAST evidence therefore carry
the STRONGEST and WIDEST floor."

## 3. The lever: `coal_mustrun_requires_measured_row` (existing field; SOCO cell `U`)

**The field.** It is registered (pjm-h14; PJM `K`, NEISO `K`), default off, and dropped at `"False"`. It already
has a matrix row and a SOCO cell (`U`). With the field armed, a coal plant with no measured row carries **no
must-run tranche**: that capacity moves to the plant's own econ bands at its own `mc`. No code changes.

**Rule check:**

| rule | how this lever meets it |
|---|---|
| 21 / 24 | Zero free parameters. It withdraws an unmeasured assertion and sets no level. |
| 19 | It removes one mechanism and adds none. The measured Bowen, Miller and Scherer rows are untouched. |
| 17 / 14 | See §2. |
| 25 | SOCO's own census. PJM's and NEISO's `K` fill no SOCO cell. |

**Arm census** (`_soco69_arm_census.py`, `fleet_only` on the keeper recipe, every year):

- **What moves.** Exactly the unmeasured `_mustrun` tranches disappear:

  | years | tranches removed |
  |---|---|
  | 2019–2020 | 5 |
  | 2021 | 4 |
  | 2022–2024 | 3 |
  | 2025 | 6, three of them dark |

- **Where the capacity goes.** It moves into the same plants' `econlo` / `econhi`, for example Wansley 2019
  `econlo` 407.9 → 790.3 MW and `econhi` 333.8 → 647.4 MW. **Their `mc` is unchanged.**
- **What does not move.** Class availability and class `min_gen` are identical, and nothing else moves. The arm is
  a pure merit-order change at five plants.

**Greedy estimate** (`_soco69_phase0.py greedy`). The removed MW are refilled hour by hour, cheapest first, from
dispatchable thermal headroom priced at or above the hour's price, plus the freed capacity at the plant's own
econ-low `mc`:

| year | ST_GAS | COAL_BIT | COAL_PRB | CT_PEAKER | CC_REGULAR |
|---|---|---|---|---|---|
| 2019 | +1.20 | −11.17 | +2.15 | +3.64 | +4.05 |
| 2020 | +1.19 | −12.20 | +0.28 | +6.21 | +4.39 |
| 2021 | +0.05 | −4.99 | +0.54 | +0.21 | +4.19 |
| 2022 | +0.09 | −1.42 | −0.07 | +0.34 | +1.05 |
| 2023 | +0.55 | −3.41 | −0.35 | +2.11 | +1.04 |
| 2024 | +0.25 | −2.26 | −0.39 | +1.26 | +1.09 |
| 2025 | +0.06 | −1.07 | −0.32 | +0.43 | +0.88 |

**C1 in the greedy (band ±3 pp):**

- **2019 ST_GAS:** −3.12 → **−2.65 pp, PASS.**
- **2019 COAL_BIT:** +0.45 → **−3.93 pp, FAIL.**
- **2020 COAL_BIT:** +2.12 → −2.94 pp, a 0.06 pp margin.
- **2023 CT_PEAKER:** +1.90 → +2.77 pp.

The greedy therefore predicts the failing row **moves** from ST_GAS to COAL_BIT in 2019. The reason is stated, not
hidden:

- The unmeasured BIT plants carry econ `mc` of $37–50/MWh (Gaston coal $50, Wansley $42, Barry $38, Crist $38).
- Without the slab they barely run.
- EIA-923 shows them running 13.5 TWh in 2019.

That is a **second, pre-existing defect the slab was masking**: these plants' cost, or their measured commitment
row, which they lack. Rule 14 says to keep the accurate structure and find that root cause, not to keep the slab.
The greedy has no intertemporal or commitment state, so it is an estimate, not a prediction of the LP.

## 4. Routed, not taken

1. **The CT start-cost object (2023–2024 regime).** `tranche_startup_amortization` is `G`, and the SOCO-65 §4
   owner question is open. This lane's decomposition confirms it is the 2023–2024 channel. **Owner question
   re-raised; not armed.**
2. **Measured coal rows for the unmeasured plants.** Extend the `thermal_tranches_SOCO.csv` derive window to cover
   plants that ran in 2019–2022 (Wansley, Crist) and give Barry, Gaston and Daniel their own measured rows. It is
   the constructive half of this lever. It is a re-derivation, and it owes a source-data citation under rule 23. It
   is also where §3's COAL_BIT loss would be answered.
3. **Crist (641) ST_GAS 2021–22** (1.56 / 0.54 TWh on EIA-923, 0 in the model): a Gulf Power boundary row, left to
   the boundary lane.
