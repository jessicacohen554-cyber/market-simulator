# PRECOMMIT — SPP-46: the C1-2024 gas split — SPP-44 R-17's two admissible objects, adjudicated at rule-29 phase 0

**Lane** SPP-46 · **Model** Fable (`claude-fable-5-1`) · **Date** 2026-09-07 ·
**Branch** `claude/spp-46-gas-split-object-6i09yn` (base `origin/main` `5de0319b`) · **Data profile** `spp` ·
**Charter** plan §5 row SPP-46 / §8 W5-r#12; FINDING-spp-44 §6 R-17 (the two objects); FINDING-spp-price-family §6 and
FINDING-spp-merit-order §4.3 / §7 (`offer_curve_by_group` is `R` for SPP in both its uniform and per-class form —
not re-tested here); FINDING-spp-40 §5 R-6; FINDING-spp-55 §0 (not a reserve / scarcity object).

**Pushed before any solve — and no solve is run by this lane.** Everything below is either a construction declared
before its number existed, a measured statistic computed at zero LP on keeper-3's committed sidecars and its own
rebuilt input arrays, or a decision rule with its thresholds. Rule 29 step 0 is a kill condition in this charter,
and it fires: §4 records the phase-0 adjudication of BOTH candidates, §5 the screen that is therefore NOT reached.
Nothing here is revised after the fact; the FINDING carries the same numbers.

---

## 0. THE PIN, the control, the G-DRIFT audit

```
5de0319b   origin/main at PRECOMMIT time (branch cut from it)
623184f3   keeper-3 `2026-09-07-spp-3-screened-input` / results/calibration/spp43_screened_B (git.sha in meta.json)
```

| precondition | check | result |
|---|---|---|
| keeper-3 is the control (form 4) | `keepers/SPP.json` → `2026-09-07-spp-3-screened-input`; bundle on disk with `hourly/{class_hourly,class_band_hourly,system,storage}_{2023,2024,2025}.parquet`, `run_config.json` (`git.dirty False`, `changed_files []`) | **yes** |
| keeper-3's recipe reproduces at HEAD (zero LP) | `run_year(fleet_only=True)` per year through `replay_keeper.run_year_kwargs` + `derived_run_year_inputs`: 1,125 / 1,125 / 1,122 LP rows, `mc_base` (n_gen × 8760) assembled on the identical path the LP solved on | **yes** (`spp46/offer_arrays.py`) |
| CAMPD extracts for SPP's 14 states, 2023–2025 | 13 present; **CO absent** in every year (inherited: SPP-44 §2.4) | usable; CO stated |
| the two candidates' cells | `spp_gas_commitment_bridge` **R**, `gas_commitment_bridge` **R**, `offer_curve_by_group` **R** (widened to any per-band / per-class set by the merit-order lane) — an `R` cell is re-opened only on NEW evidence, and this lane's phase 0 is the evidence | read before anything ran |

### 0.1 G-DRIFT (rule 29(b)) — keeper-3 `623184f3` → `5de0319b`, every hunk classified

```
git diff --stat 623184f3 HEAD -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py \
    scripts/lib data/raw/_validation-source data/raw/reference        # 21 files, +2,163 / −73
```

| # | file(s) | what | verdict for an SPP backcast | reason |
|---|---|---|---|---|
| 1 | `config/scenarios.py` (+129), `config/constants.py` (+33), `config/solve_surface_declared.py`, `data/floor_mechanisms.py`, `pipeline/commitment.py` (+174), `pipeline/{__init__,year,kwargs,persist}.py`, `runner.py`, `scripts/run_calibration*.py` | **SPP-44**: `spp_gas_commitment_bridge` (default `False`, cache-key drop value declared) + its constants, builder, wiring, CLI | **INERT** | default-off and absent from keeper-3's recipe (`run_config.scenario_config` has no such key); the builder returns `None` unless the flag is on |
| 2 | `config/scenarios.py`, `data/fuel/basis/{__init__,ercot}.py`, `data/fuel/__init__.py` | `ercot_zonal_spread_ep_referenced` (default `False`) + its ERCOT-only basis implementation | **INERT** | another ISO's branch; default off |
| 3 | `model/reserves/{__init__,spec}.py` (+268), `runner.py` | **SPP-55**: the SPP Contingency Reserve family under `energy_reserve_coopt` | **INERT** | keeper-3 has `energy_reserve_coopt: False`; SPP-55 §0 measured the family as INERT even when armed |
| 4 | `model/interchange/spec.py` (+189/−73) | **SPP-51**: SPP's priced-seam blocks (MISO_West / MISO_South split, `hr_by_year`, ERCOT 835 MW) | **INERT** | read only under `priced_interchange`, whose default set is `{"CAISO"}` (`PRICED_INTERCHANGE_DEFAULT_ISOS`); keeper-3's `calibration_flags.priced_interchange` is `false` and its class list carries no seam class |
| 5 | `pipeline/persist.py` (+34), `scripts/lib/key_provenance.py` (+846, NEW) | **capx D85-R**: the fold-root record in `run_config.environment` and a key-provenance exception checker | **INERT** | run-record only; `cache_key()` never reads it; `key_provenance.py` is imported by no solve script (grep: 0 hits in `scripts/run_calibration*.py`, `src/`) |
| 6 | `scripts/lib/confirmed_retirements/spp.py` (+41/−) | **SPP-60**: first SPP confirmed-retirement rows (Tolk 1/2) | **INERT** | `runner._confirmed_exits_active` is `config.mode == "forecast" and …`; a backcast never enters step 0 |
| 7 | `data/raw/_validation-source/capacity_actuals_spp.csv` (+301) | SPP-60's scoring target | **INERT** | scoring-side file, read by no solve path |

**All seven hunk groups INERT ⇒ form 4 is valid for every year and keeper-3's committed sidecars are the
control. No control solve is earned.** (Consistent with the merit-order lane's audit of the same keeper.)

---

## 1. Rule 19 `[R-ONE-MECH]` — what floors SPP's gas fleet: still nothing

Unchanged from SPP-44 §2: keeper-3's D-2 rows are `nuclear_mustrun` and `chp_steam` only; CC_REGULAR / ST_GAS /
CT_PEAKER carry **0.0 % forced energy**, no reliability-floor limb, no bridge, no drag, every band **1.0**
(`offer_curve_by_group` identity on all ten registered classes; `authorized_price_tuning` NONE). Whatever object
this lane chose would stack on nothing.

**The object as scored** (the SPP shard stamp, keeper-3): C1-2024 CC_REGULAR **−8.60 TWh**, CT_PEAKER **+9.94 TWh**;
2023 in band at CC −4.26 / ST_GAS −7.49 / CT +6.77 (SPP-44 §4); 2025 (merit-order lane §5.1) CT +11.06 / ST −10.27 /
CC −10.19. On the census basis below (keeper-3 P1 minus the bench `classFull`): 2024 CC −8.24, CT +10.06, ST −5.11.
Rule 29: nothing in this document is graded on those rows; they are REPORTED in the FINDING at full magnitude.

---

## 2. PHASE 0.1 — the measured committed-state census (zero LP; `spp46/campd_census.py`)

**Construction, declared before it ran.** Units classified by CAMPD's own `unitType` / `primaryFuelInfo`
(Combined cycle → CC; Combustion turbine → CT; a boiler burning natural gas → ST_GAS), restricted to the facilities
keeper-3's fleet carries in the matching MERCHANT class (the CHP classes fall out through the fleet's own labels), so a
mixed plant (1217 Earl F Wisdom: one boiler + one CT) is split by unit. Online state per unit: `grossLoad ≥
max(_ONLINE_MW, 0.05 × HSL_unit)`, HSL = p99.5 of the unit's pooled load — the SPP-44 derive's own threshold. The
committed-state floor F(t) = Σ over online PLANTS of the plant-basis LSL (p5 of the plant's online-hour load, per year);
footprint = Σ_t max(0, F − D) against keeper-3's class dispatch D(t), decomposed into hours with **D > 0** (the only
hours a P0-anchored online-hours leg can touch — a run the model never starts has no online hours) and **D = 0**.
Duty cohort = plants with online fraction ≥ 0.75. For CT the OVER-run Σ_t max(0, D − G_measured) is split by keeper-3's
own system-load percentile. (SPP-44's 2023 ST_GAS footprint of 3,551 GWh used the derive's pooled three-year LSLs on
its 26 plants against keeper-2; the per-year construction here reads 2,419 GWh against keeper-3 — same object,
tighter LSL, stated rather than reconciled.)

| year | class | CAMPD plants / units | fleet MW covered | **CAMPD gen TWh** | **keeper-3 TWh** | bench TWh | online frac (cap-wtd) | loading when on | footprint GWh (in D>0 / in D=0) | duty plants / MW | CT over-run GWh: mid / low / top-10 % load |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2023 | CC_REGULAR | 21 / 41 | 9,474 of 10,048 | 40.78 | 41.43 | 45.69 | 0.633 | 0.784 | 666 (576 / 91) | 6 / 5,019 | — |
| 2023 | CT_PEAKER | 49 / 133 | 9,141 of 11,708 | 11.51 | **19.99** | 13.21 | 0.222 | 0.718 | 0 | 1 / 240 | **8,640: 4,370 / 2,114 / 600** |
| 2023 | ST_GAS | 26 / 48 | 9,134 of 10,281 | 15.21 | **7.53** | 15.02 | 0.402 | 0.470 | 2,419 (1,977 / 442) | 4 / 1,539 | — |
| 2024 | CC_REGULAR | 21 / 41 | 9,474 | 39.95 | 37.66 | 45.90 | 0.611 | 0.795 | 1,040 (940 / 100) | 7 / 5,170 | — |
| 2024 | CT_PEAKER | 49 / 133 | 9,141 | 13.46 | **25.97** | 15.91 | 0.250 | 0.745 | 2 | 3 / 839 | **13,189: 6,547 / 3,205 / 1,309** |
| 2024 | ST_GAS | 26 / 48 | 9,134 | 18.59 | **14.99** | 20.10 | 0.444 | 0.531 | 311 (286 / 25) | 5 / 1,704 | — |
| 2025 | CC_REGULAR | 21 / 41 | 9,474 | 36.14 | 32.57 | 42.76 | 0.576 | 0.767 | 1,220 (966 / 254) | 7 / 5,441 | — |
| 2025 | CT_PEAKER | 50 / 137 | 9,583 | 11.81 | **22.35** | 11.28 | 0.206 | 0.751 | 1 | 2 / 695 | **10,736: 5,491 / 2,893 / 831** |
| 2025 | ST_GAS | 27 / 50 | 10,152 | 17.56 | **9.83** | 20.10 | 0.409 | 0.494 | 1,038 (931 / 107) | 4 / 2,091 | — |

Two readings that decide the candidates before any offer array is opened:

- **The CT over-run is a MID- and LOW-load phenomenon.** In 2024, 6.5 TWh of the 13.2 TWh gross over-run sits in the
  25–75 % load band and 3.2 TWh below the 25th percentile; only 1.3 TWh is in the top decile. The keeper runs SPP's
  peakers at a 25 % capacity-weighted online fraction — as baseload. No commitment floor on CC / ST_GAS acts there.
- **The committed-state footprint is small against the under-run and mostly sits in hours the class is already
  partly on.** ST_GAS: 2,419 / 311 / 1,038 GWh of footprint against under-runs of 8.0 / 5.1 / 7.9 TWh (the CAMPD
  basis). The D = 0 slice — the never-started slice a P0-anchored leg can never reach — is 442 / 25 / 107 GWh; and
  the D > 0 slice is a class-level over-bound (the class being on does not put the floored plant on).

---

## 3. PHASE 0.2 — the LP's own offer arrays (zero LP; `spp46/offer_arrays.py`, `offer_analysis.py`, `attribution.py`)

**Construction, declared before it ran.** For each year, keeper-3's fleet is rebuilt with `run_year(fleet_only=True)`
— the identical assembly the LP solved on — and the per-row `mc_base`, `fuel_prices` and `availability` arrays are
read directly. Four instruments, none of which reads a criterion:

- **(A) provenance**: each gas row's delivered price split by whether the plant's OWN EIA-923 monthly report priced it
  (`plant_month_price_grid`) or the zone-pool gap-fill did (`nearby_fuel_price_fallback`, `min_state_plants 2`, zone
  tier — every SPP row's `state` is empty, so the state tiers are void), beside the EIA state delivered-to-electric-power
  series `N3045{KS,OK,TX,NM}3` ($/Mcf ÷ 1.037). Keeper-3 prices 383 / 383 / 343 gas rows from their own plant and
  792 / 792 / 820 from the pool.
- **(B) merit overlap**: availability-weighted mc percentiles per class and the CC / CT / ST_GAS crossover shares.
- **(C) in-merit reconstruction** at keeper-3's own P1 zonal prices: strict in-merit (mc < p − $0.25), marginal
  (|mc − p| ≤ $0.25) and out-of-merit capacity per class beside the keeper's dispatch; the count of hours the
  dispatch falls outside [strict, strict + marginal] by > 100 MW; for the under-run classes the cap-weighted
  distribution of price / mc over their out-of-merit row-hours.
- **(D) re-clearing predictor** (the merit-order lane's construction, validated there against a solved arm to
  0.1–0.9 pp on the level): per hour the keeper's cleared thermal quantity is re-cleared against re-priced rows —
  band multipliers scale the FUEL component only, `mc' = vom + (mc − vom) × m` (the HR_Mult construction) — zones
  pooled when the keeper's zonal prices agree, else separately; a strict self-check retains the hours where the
  1.0 reconstruction lands every one of CC / CT / ST_GAS / COAL within 250 MW of the keeper (1,660 / 1,969 / 2,222
  hours), and both all-hour and retained-hour deltas are reported. **It is a REACH test for candidate (B) and
  selects nothing**: the candidate's values, had it survived, were to come from the conduct construction in §4.2,
  never from this table.
- **(E) plant attribution**: model in-merit energy per plant (strict + ½ marginal) beside CAMPD measured gross
  generation, with three INPUT flags read off the row: `fuel_low` (an own-reported month < 0.5 × the state reference
  that month), `fuel_high` (> 2.0 × the reference), `hr_flag` (a CT row whose plant-level heat rate is < 6 MMBtu/MWh,
  or a CC row whose plant-level rate is > 10). The 0.5 / 2.0 band is DECLARED here; a second band [0.6, 1.67] is
  reported as robustness; neither is selected on anything.

### 3.1 What the arrays say

**(C) — CT and ST_GAS dispatch sit exactly on their own marginal costs.** Hours outside the in-merit band: ST_GAS
**0 / 0 / 0**, CT_PEAKER 572 / 287 / 211 (CC_REGULAR 4,867 / 4,352 / 4,269 — its committed tranches carry the $50/MW
start and clear on the P1 bid, not on `mc_base`). So the CT over-run and the ST_GAS under-run are read off the input
arrays without a solve: **the LP runs exactly the CT it is told is cheap and skips exactly the ST_GAS it is told is
dear.** In 2024 the keeper dispatches **7.44 TWh of CT strictly in merit in hours where the zonal price is below the
CC class's median marginal cost ($22.1)** — 3.25 / 7.44 / 7.63 TWh across the years.

**(B) — the crossover is carried by tails, not by the class means.** 2024 availability-weighted mc: COAL p50 $21.2,
CC p50 $22.1, ST_GAS p50 $32.3, CT p50 $36.4 — but CT **p10 = $10.39** and ST_GAS p10 $17.7; 21.8 % of CT capacity is
cheaper than the CC median and 41 % of ST_GAS capacity is dearer than the CT median.

**(A) + (E) — the tails are OWN-REPORTED EIA-923 prices and plant-level eGRID heat rates that are physically
implausible, and they carry the object.** Plant-level model-minus-CAMPD, 2024 (GWh), by flag group:

| class | flag group | plants | MW | model in-merit | CAMPD | **Δ** | the rows |
|---|---|---|---|---|---|---|---|
| CT_PEAKER | **hr_flag** | 1 | 763 | 5,627 | 614 | **+5,013** | 57881 Pioneer (Basin Electric, ND): eGRID `PLHTRT` **3.43 MMBtu/MWh** on 3 × 60.5 MW GTs (+245.7 MW in 2025); EIA-923 gen 1.51 / 1.09 / 0.57 TWh against CAMPD 0.50 / 0.61 / 0.53 (`ct_ratio` 2.95); the model rows sum to 763 MW against a 427 MW nameplate |
| CT_PEAKER | **fuel_low** | 6 | 1,894 | 12,314 | 4,192 | **+8,121** | 58835 Elk Station **$0.16–0.41/MMBtu** all twelve months on 0.8–1.5 M MMBtu/month; 56326 Mustang Station 4 **$0.11–0.28**; 3482 Jones $1.16; 2454 Cunningham $0.91; 2446 Maddox $0.91 (Golden Spread / SPS, TX) |
| CT_PEAKER | clean | 110 | 7,080 | 6,614 | 6,858 | **−244** | the peaker fleet the keeper is right about |
| CT_PEAKER | fuel_high | 8 | 2,018 | 1,717 | 1,794 | −77 | 55972 Cass County $12.31 (mean) |
| ST_GAS | **fuel_low** | 5 | 1,994 | 10,752 | 4,616 | **+6,136** | **6193 Harrington 1,018 MW at $1.48**: CAMPD has all three boilers burning COAL through 2023 and 2024 (3.54 / 2.51 TWh gross) and converting in 2025; its 2023–2024 "gas" price rides on 8–650 k MMBtu/month ignition volumes; the model runs it 1.66 / **5.82** TWh as gas steam, and the bench groups its coal generation under ST_GAS (`e_ann` 3.44 / 2.23) |
| ST_GAS | **fuel_high** | 3 | 2,751 | 1,512 | 5,313 | **−3,801** | 2952 Muskogee (Jan $6.89, Dec $15.39; 2025 Feb $48.30 on 51 k MMBtu), 2956 Seminole (Feb $7.83), 4940 Riverside (2023 Apr **$71.66 on 2,750 MMBtu**, Nov $18.01) — low-volume months carrying fixed transport charges: an AVERAGE cost, not the marginal cost the LP prices |
| ST_GAS | clean | 23 | 5,536 | 2,714 | 8,664 | **−5,949** | 2963 Northeastern −1,257, 3478 Wilkes −1,078, 2964 Southwestern −727, 2965 Tulsa −434, 2951 Horseshoe Lake −316 — the OG&E / PSO / SWEPCO steam fleet at $3.0–3.7 gas, HR 11–13 |
| CC_REGULAR | fuel_low | 2 | 1,898 | 9,879 | 7,657 | +2,222 | 55463 Redbud $2.36; 55065 Mustang Station **−$1.54 to −$0.04 in seven months of 2024** (a NEGATIVE delivered price) |
| CC_REGULAR | hr_flag | 2 | 686 | 361 | 1,524 | −1,163 | 2963 Northeastern CC at the plant blend **12.24** (coal 460 + CC 444 + ST 434 MW on one eGRID row); 2079 Hawthorn |
| CC_REGULAR | clean | 15 | 6,637 | 28,456 | 28,590 | −134 | |

The clean CT cohort — 110 plants, 7.1 GW — is reproduced to **−0.24 TWh**. The 2024 CT over-run is, at plant level,
**13.1 TWh on rows whose own input is outside its plausibility band, against a 12.8 TWh net over-run**. 2023 and
2025 read the same way (`spp46/attribution.log`: hr_flag +5,159 / +5,090, fuel_low +8,122 → −1,220 (2023) /
+7,206 (2025); clean CT +5,024 in 2023 — the one year the clean cohort over-runs, on the high-gas side of the
same seam — and −726 in 2025).

**Across the SPP states, 2023–2025, the EIA-923 monthly gas frame carries 91 plant-months at ≤ $0.50, 31 NEGATIVE,
and 206 at ≥ $10.00 out of 5,707** — the seam has no plausibility screen (`plant_prices.py`: none; `eia923.py`: none),
and `gas_plant_monthly_fuel_pricing=True` in keeper-3's recipe consumes every one of them at face value. The
existing repair precedent on the heat-rate side is `_egrid_boundary_hr_repairs` (a CC above
`EGRID_CC_HR_PHYSICAL_CEILING` = 11.5 is reconciled); there is no simple-cycle FLOOR analogue, so a CT at 3.43 passes.

### 3.2 The offer-array delta of the object phase 0 actually found (reported, not this lane's arm)

Re-clearing (D) with the declared screen — an own-reported month outside [0.5 R_m, 2.0 R_m] replaced by the state
reference R_m; gap-filled rows left as they are (the pool they draw from would move too; stated, not modelled) —
and, in a second line, additionally the simple-cycle physical floor `HEAT_RATE_BINS["gas_ct"]["aero"]` = 9.0 on the
CT rows below 6:

| year | screen | plant-months / rows / MW touched | ΔCC_REGULAR | ΔCT_PEAKER | ΔST_GAS | ΔCOAL | LW price |
|---|---|---|---|---|---|---|---|
| 2023 | band [0.5, 2.0] | 47 / 77 / 6,502 | +0.02 | +0.04 | −0.05 | +0.06 | ×0.999 |
| 2023 | + CT HR floor 9.0 | | +1.13 | **−2.86** | +0.10 | +1.67 | ×1.010 |
| 2024 | band [0.5, 2.0] | 120 / 110 / 12,144 | **+4.26** | **−4.17** | −4.17 | +3.95 | ×1.032 |
| 2024 | + CT HR floor 9.0 | | **+5.11** | **−6.82** | −3.80 | +5.34 | ×1.044 |
| 2025 | band [0.5, 2.0] | 71 / 107 / 10,658 | +2.87 | −6.36 | −0.94 | +4.37 | ×1.045 |
| 2025 | + CT HR floor 9.0 | | +3.92 | **−8.70** | −0.76 | +5.46 | ×1.060 |

Band [0.6, 1.67] moves the same way (2024: +4.55 / −4.44 / −4.11 / +3.87). The ST_GAS delta is NEGATIVE because the
screen removes Harrington's 5.8 TWh of $1.48 gas; the clean steam cohort's −5.9 TWh is not closed by these two
seams and is the residual object (§4.4). The predictor over-states level effects (merit-order lane §4.1), so the
price ratios are bounds.

---

## 4. THE ADJUDICATION — both candidates KILLED at phase 0 (rule 29 step 0.3)

### 4.1 Candidate (A): a measured commitment-STATE input on ST_GAS — INADMISSIBLE in one form, UNREACHABLE in the other

The ercot141 / nyiso-146b construction is the online-hours leg of the shared detector
(`model/commitment.py::caiso_ra_mustoffer_min_gen`, `floor_online_hours=True`): the minimum-load floor covers every
hour of each **P0-detected, commitment-real run** — "runs come from the detector's own P0 pattern, so a unit the
model has offline is never floored"; nyiso-146b scopes it to a duty cohort by measured run length, still on P0 runs.

- **P0-anchored form.** SPP-44 measured the P0 pattern on SPP's gas steam fleet: 1,734 P0 runs, **1,360 dropped as
  phantom**, 1,885 unit-hours floored, 0.059 TWh on gas_st — and 0.414 TWh across every leg against a 4.2 TWh gap.
  The online-hours leg widens the window of the SAME runs; its reach is bounded above by the footprint in hours the
  class is on at all: **≤ 1,977 / 286 / 931 GWh** (§2, the D > 0 slice, itself a class-level over-bound) against
  ST_GAS under-runs of 8.0 / 5.1 / 7.9 TWh — ≤ 25 % / 6 % / 12 % in the impossible case that every P0-online
  plant-hour were a floor hour. And SPP-44 R-18 stands: any P0-anchored SPP floor needs the lay-up membership
  channel first. **Cannot reach the gap — KILLED on reach (step 0.3).**
- **Measured-state form** (the plant's CAMPD online hours as the floor window, with a measured duty membership).
  **Rule 13's forward test, answered explicitly: NO.** A plant's observed online state is its commitment
  OUTCOME — the decision the LP exists to make — not a physical availability event like an outage window or a
  measured fuel price. It cannot be produced for a forward year from forward drivers, and pinning a unit to its
  observed online hours at LSL is the observed-generation pin rule 13 forbids by name, at part load. What would be
  admissible is a market-design object (SPP's vertically-integrated utilities self-commit their steam fleet; SPP's
  own market data records self-committed status) — a build with its own PRECOMMIT, routed in the FINDING — not a
  measured-state input. **INADMISSIBLE.**

### 4.2 Candidate (B): a per-class `offer_curve_by_group` band configuration under the carve-out — KILLED on reach, and REFUSED as a compensator for a measured-input defect

The conduct construction this lane had declared for (B), before any value existed: `m_c` = the RT LMP at which
the class's CAMPD online capacity fraction crosses one half of its annual p95 ÷ the availability-weighted median
`mc_base` of the class — one rule, three values. It was never computed, because the reach test and the input
census kill the candidate first:

- **Reach (predictor §3, retained-hour deltas, 2024).** To move CT by the object's −9.9 TWh the CT fuel component
  must be scaled **×2.0** (−6.7 TWh at a +16.7 % load-weighted price level); ST ×0.6 reaches +7.4 TWh at a −5.8 %
  level; CC ×0.7 reaches +8.5 TWh with coal −5.0 and a −6.9 % level. The merit-order lane's own price-derived
  per-class set (CC 0.803 / CT 0.888 / ST 0.895) moves CT **0.00** TWh and CC +4.8 (2024, retained). Any set that
  reaches the split is a ±40–100 % rescaling of a measured fuel component that moves the price level 6–17 % on a
  stack whose middle is already +25 % too dear (merit-order lane §1) — i.e. it must worsen C3a to move C1.
- **What it would be compensating for (§3.1).** A CT ×2.0 is the multiplier that turns Elk Station's $0.16 gas into
  $0.32 and Pioneer's 3.43 heat rate into 6.9 — it papers over an input defect with a tuned number. Rule 14
  `[R-ACCURATE]`: "Do not bury the error back inside an inaccurate input." Rule 1's carve-out authorizes tuning the
  offer curve ON PRICE against a structurally right system; the playbook's own order (§6.2) is fuel prices (d) BEFORE
  bands (f). A band on a fleet whose fuel and heat-rate inputs are implausible is the compensating error the
  playbook names. **REFUSED — and not on the residual: on the input census.**
- The `offer_curve_by_group` cell stays **R**, with this lane's C1 reach table as the evidence that widens it from
  the price object to the volume object.

### 4.3 The object, named by measurement

The C1-2024 gas split is a **measured-input plausibility defect on three seams** keeper-3's recipe consumes at face
value, plus a residual the seams leave:

1. **EIA-923 own-month gas prices** with no plausibility screen (the cheap tail: Elk / Mustang / Mustang CC negative;
   the dear tail: Riverside $71.66, Muskogee, Cass County) — ~8.1 TWh of the 2024 CT over-run and ~3.8 TWh of the
   ST_GAS under-run, at plant level.
2. **Plant-level eGRID heat rates** applied to every unit: a simple-cycle plant at 3.43 (Pioneer, +5.0 TWh) with no
   CT physical floor to catch it, and mixed plants at the plant blend (Northeastern CC at 12.24, Earl F Wisdom CT at
   19.36) — the registered, default-off, zero-DOF `egrid_family_heat_rates` (nyiso-184) is the on-registry repair
   and reads `U` for SPP.
3. **Fleet fuel vintage**: Harrington (1,018 MW) modelled as ST_GAS in 2023–2024 while CAMPD has it burning coal
   (+5.8 TWh of $1.48 "gas" steam in 2024).
4. **The residual after 1–3**: the OG&E / PSO / SWEPCO steam cohort at plausible inputs (−5.9 TWh in 2024) — the
   never-started object SPP-44 R-17 named — which the predictor says the repaired price surface lifts only partly,
   and whose admissible construction is a market-design (self-commitment) object, not a floor and not a band.

Every one of 1–3 is a rule-14 repair with **zero degrees of freedom** (a screen against a published reference, a
physical floor off an existing cited constant, the plant's own CAMPD fuel by year); each regenerates for a forward
year (forward years price on HH + basis and never read F923, so the screen is backcast-only by construction and
rule 13's forward test is met). None of the three files is in this lane's region (`data/fuel/plant_prices.py`,
`data/fleet/eia860.py`, the fleet curation), so under plan §8.0 rule 5 they are ROUTED with this specification and
their zero-LP predicted delta (§3.2), never edited around.

### 4.4 Kill grading (E-6: thresholds, not directions)

| candidate | kill leg | declared bar | measured | verdict |
|---|---|---|---|---|
| (A) P0-anchored | reach ≥ 0.50 of the ST_GAS under-run in the screen year | 0.50 | ≤ 0.25 (over-bound); 0.007 measured by SPP-44 | **KILLED** |
| (A) measured-state | rule 13 forward test | must be answerable YES | NO (commitment outcome) | **INADMISSIBLE** |
| (B) per-class bands | reach of the 2024 split at a level move ≤ ±5 % | \|ΔCT\| ≥ 5 TWh at \|Δlevel\| ≤ 5 % | CT ×1.3 → −2.4 TWh at +5.9 %; the derived set → 0.00 TWh | **KILLED** |
| (B) | admissibility given the input census | no flagged input carries ≥ 25 % of the object | flagged rows carry ~100 % of the CT over-run | **REFUSED** |

---

## 5. THE SCREEN (rule 29(a)) — NOT REACHED, declared for the record

Had either candidate survived, the screen year was to be named on footprint: **2023** for (A) (the ST_GAS committed-
state footprint 2,419 GWh, largest of the three — and NOT 2024, the year C1 fails), **2025** for (B) (the largest
out-of-merit CC + ST_GAS capacity-energy, 22.6 + 22.7 TWh); recipe keeper-3's plus the one change; gate legs (i)
footprint ⊆ the claimed rows at ≥ 0.80 of the changed class-hours, (ii) sign and order of magnitude of §3's
prediction within [0.5×, 2.0×], (iii) identity on the P0 objective and the input arrays (never P1), (iv) no non-target
load-bearing flip; C1 reported, never gated. **No solve is spent; no bundle exists; `.gitignore` needs no entry.**

## 6. DOF ledger (rule 21)

This lane adds **no parameter, no field, no constant**. The declared screen band [0.5, 2.0] and the CT floor 9.0 are
carried in this document as the specification of a routed repair, not as values in any solve.

## 7. What is not touched

`keepers/SPP.json`, the shard's keeper / gates stamp, the plan, the ledger, `docs/calibration-log/spp.md`,
`CHANGELOG.md`, `frontend/data/forecast/`, any other ISO's anything, every solve-path file. Cells this lane edits
(rule 28(b), evidence lines only): `offer_curve_by_group`, `spp_gas_commitment_bridge`, `gas_commitment_bridge`,
`gas_plant_monthly_pricing`, `egrid_family_heat_rates`, `measured_ct_heat_rates` — all in `mechanism-matrix/SPP.js`.
