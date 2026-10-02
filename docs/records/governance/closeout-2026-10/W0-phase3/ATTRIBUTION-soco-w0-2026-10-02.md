# SOCO W0 attribution: C2 fuel-mix PASS→FAIL moves (zero LP)

All paths below are relative to `soco_attr/` (the scratch directory) unless they start with `results/`, `data/` or `docs/`. No LP was solved for this note.

The fleet builds are `run_year(fleet_only=True)` runs of the soco96 recipe, made through `scripts/build_fleet_census.py::rebuild_fleet` (`fleet_toggle.py`). Each posture is one of:
- **recorded**: the incumbent soco96 configuration.
- **w0**: all 10 W0 fields on.
- **alone**: recorded with one W0 field turned on.
- **loo** (leave one out): w0 with one field turned off. The loo column shows w0 minus loo-f.

**The fleet rebuild is exact.** The W0 rebuild reproduces the solved W0 legs' Σ pmax×availability for every unit, with a largest difference of 0 MWh, against `results/calibration/w0_soco_span/hourly/unit_hourly_<Y>.parquet` cap_mw for 2019, 2021 and 2022. The unit counts are 425 / 427 / 437, which also match.

Class model totals come from `model_mwh.py`, saved as `out/class_tot_<Y>.csv`:
- The incumbent's are from `results/calibration/soco96_span/hourly/class_hourly_<Y>.parquet`, P1 pass.
- W0's are from `origin/claude/w0-promote-soco:…/w0_soco_span/hourly/class_hourly_<Y>.parquet`.
- Both reproduce the scored moves: COAL_PRB 2022 +2.320 TWh, CC_REGULAR 2019 +2.677 TWh, CC_REGULAR 2021 +2.036 TWh.

**The incumbent's per-plant MWh do not exist.** soco96_span has no committed `unit_marginal` or `unit_hourly` files and no dispatch files, on any ref or in git history. Only class totals can be compared on the incumbent side.

Per-plant attribution therefore pairs:
- the W0 model MWh per plant (`out/w0_unit_mwh_<Y>.parquet`, from the on-disk `dispatch/<Y>_P1.parquet`), with
- the zero-LP change in available energy (Σ_t pmax×availability) per plant and per field (`attr.py` → `out/plants_*.csv` and `out/attr_*.csv`; `plant_tables.py` → `out/ptab_*.md`).

**Why available energy is a fair proxy here.** Almost every plant that moves runs at 0.96–1.00 of its W0 availability ("util" in the tables). For those plants, MWh tracks available energy closely.

---

## (a) Plant 6052 in 2022, and the COAL_PRB 2022 move

### What 6052 is

**6052 is Georgia Power's Wansley plant.** Its census family is COAL, but the model class is **COAL_BIT, not COAL_PRB**.

| | Vintage 2021 | Vintage 2022 | Vintage 2023 |
|---|---|---|---|
| ST 1, Conventional Steam Coal, BIT, 952 MW nameplate / 872 MW summer | OP | RE, retired 2022-09 | RE, retired 2022-09 |
| ST 2, same rating | OP | RE, retired 2022-09 | RE, retired 2022-09 |
| 5A, Petroleum Liquids, DFO, 52.8 / 49 MW | OP | RE, retired 2022-09 | RE, retired 2022-09 |

Source: `data/raw/eia-860/vintage_{2021,2022,2023}/eia860_generator_{operable,retired_and_canceled}.parquet`.

### Generation in 2022

| | MWh |
|---|---|
| **EIA-923 2022 net generation** (`data/raw/eia-923-generation-fuel/eia923_generation_fuel_2019_2025.csv`): ST BIT 883,911; ST DFO 14,316; GT −303 | **897,924** (coal only: 883,911) |
| W0 2022 leg, P1 (`w0_soco_span/dispatch/2022_P1.parquet`): four COAL_BIT bins `COAL_SOCO_GA_p6052_r202209_*`, plus unit 5A (oil) at 0 | **1,250,160**, all COAL_BIT |
| W0 available energy (pmax 1,744 MW coal + 49 MW oil, online January–September, measured outages applied) | 1,388,925 coal + 288,943 oil |
| Incumbent soco96 2022 | **0**: the plant is not in the fleet in the recorded posture (`out/units_2022_recorded.parquet`) |

**The carry is correct.** Wansley really ran in 2022: about 0.9 TWh in January–August before it retired in September 2022. A year-matched 2022 vintage drops it entirely, because the vintage's operable sheet is a year-end snapshot. The W0 model does overshoot its generation by +0.35 TWh: 1.25 TWh modelled against 0.88 TWh of coal.

### Which W0 field carries it

From the zero-LP toggles in `out/units_2022_*.parquet`, for plant 6052:

| Posture | Plant MW | Available GWh |
|---|---|---|
| recorded | 0 | 0 |
| **mid_vintage_exit_carry alone** | **1,793** | **1,678** |
| any other single field alone (9 builds, including partial_plant_exit_carry, backcast_actual_retirement_only and retiree_vintage_status_scope) | 0 | 0 |
| w0 | 1,793 | 1,678 |
| w0 with mid_vintage_exit_carry off | 0 | 0 |
| w0 with any other field off | 1,793 | 1,678 |

The field is **mid_vintage_exit_carry, alone and necessary.**

### Decomposing the COAL_PRB 2022 move (+2.32 TWh in model energy)

Sources: `out/ptab_COAL_PRB_2022.md` and `out/attr_COAL_PRB_2022.csv`.

| Plant | Recorded MW → W0 MW | Recorded → W0 available GWh | Δ available | W0 model GWh (util) | EIA-923 2022 coal GWh |
|---|---|---|---|---|---|
| **6257 Scherer** | 2,580 → 3,440 | 12,270 → 14,759 | **+2,489** | 14,515 (0.98) | **7,286** |
| 6002 James H Miller Jr | 2,778 → 2,778 | 20,506 → 20,462 | −45 | 20,462 (1.00) | 20,873 |
| COAL_PRB class total | 6,362 → 7,364 | 37.040 → 39.485 TWh | **+2.444 TWh** | 38.941 TWh; the incumbent's class total is 36.621 TWh | |

**Scherer (6257) accounts for essentially all of the move.**

What changes at Scherer:
- **Unit 4 is newly carried.** EIA-860 vintage_2022 lists Scherer unit 4 (891 MW, SUB) as **retired 2022-01**, while units 1–3 stay OP. W0 adds unit 4 as an exit-cohort bin, `p6257_r202201`, online for January only: about +0.49 TWh of available energy.
- **The surviving units' availability rises.** The three surviving bins' mean availability goes from **0.543 to 0.631**, which is +1.95 TWh.

No single field produces the move on its own:
- partial_plant_exit_carry alone: +1,002 MW but only +0.489 TWh.
- unit_outage_dispatched_bin_denominator alone: 0.000.
- Turning off partial_plant_exit_carry from w0: −2.569 TWh.
- Turning off the denominator from w0: −2.083 TWh.
- commission_year_cod_fallback: −0.13 / −0.14.

**This is an interaction.** With the unit-4 cohort on the LP roster, the denominator companion takes Scherer's (plant, COAL_PRB) outage denominator from the LP roster, which now holds 3,440 MW instead of 2,580 MW. That dilutes the measured outage derate on units 1–3. As a check, (1 − 0.543) × 2,580 / 3,440 gives an availability of 0.657, close to the observed 0.631. This mechanism is inferred, not traced through `data/outages.py`.

**The live-roster sub-gate does not fix it.** Arming `unit_outage_dispatched_bin_live_denominator` on top of W0 leaves the result unchanged (`live_denom_probe.py`: 0.631, and the COAL_PRB total stays at 39.485 TWh). By design, that sub-gate keeps a cohort that retires *in* the solve year on the roster.

**Real Scherer generation in 2022 was 7.29 TWh.** The incumbent's available energy was already 12.27 TWh, and W0 runs it at 14.5 TWh. This is the plant to look at for the COAL_PRB C2 failure.

---

## (b) CC_REGULAR 2019 and 2021

### Class available energy by field (zero LP, CC_REGULAR units)

Sources: `out/attr_CC_REGULAR_2019.csv` and `out/attr_CC_REGULAR_2021.csv`.

| Field | 2019 alone ΔMW / ΔTWh | 2019 loo ΔTWh | 2021 alone ΔMW / ΔTWh | 2021 loo ΔTWh |
|---|---|---|---|---|
| **seasonal_capacity_basis (E.1)** | **+676 / +4.321** | **+4.670** | **+677 / +4.528** | **+5.070** |
| cc_block_summer_rating (E.3) | −109 / −0.724 (all at 643 Lansing Smith) | −0.900 | 0 / 0 | 0 |
| cc_steam_part_capacity | 0 | 0 | 0 | 0 |
| unit_outage_dispatched_bin_denominator | 0 / 0.000 | +0.534 | 0 / −0.463 (all at 533 McWilliams) | +0.560 |
| commission_year_cod_fallback | 0 / −0.449 | −0.458 | 0 / −0.543 | −0.551 |
| mid_vintage_exit_carry | 0 | 0 | 0 / −0.463 (533) | 0 |
| All other fields | 0 | 0 | 0 | 0 |
| **All of W0** | **+567 MW / +3.497 TWh** | | **+676 MW / +4.066 TWh** | |
| Model ΔMWh (class_hourly) | +2.677 TWh | | +2.036 TWh | |

Grouped into E.1 and the denominator companion:

| Year | E.1 (seasonal basis + CC ratings) | Denominator companion | Other |
|---|---|---|---|
| 2019 | alone +3.60 TWh; loo +3.77 TWh | alone 0; loo +0.53 TWh | commission_year_cod_fallback about −0.45 |
| 2021 | alone +4.53 TWh; loo +5.07 TWh | alone −0.46 TWh; loo +0.56 TWh | commission_year_cod_fallback about −0.54 |

The denominator companion's effect exists only on top of E.1's new pmax, consistent with its purpose: making the denominator follow E.1.

### The census plants 6073 and 57037 are not the W0 cause

Their rating gaps are identical in the recorded and W0 censuses:

| Plant | 2019 gap vs 860 | 2021 gap vs 860 |
|---|---|---|
| 6073 | −710 MW | −727 MW |
| 57037 | −440 MW | −440 MW |

Source: `docs/…/W0-census/SOCO/fleet_census_{2019,2021}_{recorded,w0}.json`. These gaps come from the pre-existing "trusted bound" CC guard clip ("corrupt summer-capacity rows", which removes 751 MW and 440 MW). Under W0, their pmax is unchanged (1,132 MW and 840 MW). Their available energy rises only through E.1's seasonal shape:

| Plant | Year | E.1 | commission_year_cod_fallback | Net |
|---|---|---|---|---|
| 6073 | 2019 | +310 GWh | −144 GWh | +164 GWh |
| 6073 | 2021 | +321 GWh | −191 GWh | +127 GWh |
| 57037 | 2019 | +236 GWh | | +236 GWh |
| 57037 | 2021 | +230 GWh | | +230 GWh |

### Per plant, 2019

Top movers in available energy. Source: `out/ptab_CC_REGULAR_2019.md`; EIA-923 is CA+CT+CS net generation.

| Plant | Recorded → W0 MW | Δ available GWh | E.1 alone | Block rating alone | W0 model GWh (util) | EIA-923 GWh |
|---|---|---|---|---|---|---|
| 710 Jack McDonough | 2,484 → 2,732 | +1,355 | +1,231 | 0 | 20,668 (1.00) | 19,072 |
| 643 Lansing Smith | 620 → 511 | −724 | +176 | −724 | 4,226 (1.00) | 3,913 |
| 7710 H Allen Franklin | 1,902 → 1,980 | +422 | +351 | 0 | 14,374 (1.00) | 12,463 |
| 7946 Wansley Unit 9 | 490 → 557 | +368 | +283 | 0 | 3,781 (1.00) | 3,070 |
| 56150 McIntosh CC | 1,316 → 1,374 | +322 | +241 | 0 | 9,309 (0.99) | 8,435 |
| 55382 Thomas A Smith | 1,192 → 1,192 | +267 | +267 | 0 | 6,938 (0.96) | 6,326 |
| 55411 Hillabee | 765 → 823 | +263 | +245 | 0 | 5,491 (0.99) | 5,035 |
| 55965 Wansley CC | 1,185 → 1,233 | +257 | +237 | 0 | 9,393 (1.00) | 8,847 |
| 57037 Ratcliffe | 840 → 840 | +236 | +236 | 0 | 5,689 (0.88) | 4,610 |
| 6073 Victor J Daniel | 1,132 → 1,132 | +164 | +310 | 0 | 8,428 (1.00) | 8,292 |

### Per plant, 2021

Source: `out/ptab_CC_REGULAR_2021.md`.

| Plant | Recorded → W0 MW | Δ available GWh | E.1 alone | Denominator alone | W0 model GWh (util) | EIA-923 GWh |
|---|---|---|---|---|---|---|
| 710 Jack McDonough | 2,471 → 2,709 | +1,324 | +1,162 | 0 | 19,996 (1.00) | 18,235 |
| 533 McWilliams | 654 → 654 | −444 | +33 | −463 | 1,239 (0.94) | 4,000 |
| 7710 H Allen Franklin | 1,902 → 1,977 | +411 | +329 | 0 | 13,961 (1.00) | 11,357 |
| 7946 Wansley Unit 9 | 478 → 546 | +368 | +306 | 0 | 3,149 (0.82) | 2,982 |
| 55382 Thomas A Smith | 1,192 → 1,192 | +332 | +332 | 0 | 7,067 (0.78) | 7,983 |
| 55411 Hillabee | 753 → 815 | +282 | +253 | 0 | 4,639 (0.86) | 5,148 |
| 7917 Chattahoochee | 466 → 526 | +279 | +254 | 0 | 3,568 (1.00) | 3,176 |
| 56150 McIntosh CC | 1,316 → 1,360 | +238 | +212 | 0 | 9,197 (0.91) | 8,587 |
| 57037 Ratcliffe | 840 → 840 | +230 | +230 | 0 | 6,062 (0.99) | 3,991 |
| 7897 E B Harris | 1,304 → 1,304 | +226 | +226 | 0 | 6,289 (1.00) | 4,701 |

---

## (c) Which single field accounts for most of each move (zero-LP proxy)

| Move | Model Δ (incumbent → W0) | Δ available energy, all W0 | Dominant field | Its contribution | Others |
|---|---|---|---|---|---|
| COAL_PRB 2022 | +2.32 TWh | +2.44 TWh (+1,002 MW), all at Scherer 6257 | **partial_plant_exit_carry**: necessary, since the loo value is −2.57 TWh; it carries Scherer unit 4 (retired 2022-01) | alone only +0.49 TWh. The other ~+2.0 TWh is its **interaction with unit_outage_dispatched_bin_denominator** (alone 0, loo −2.08), which dilutes the surviving units' outage derate (availability 0.543 → 0.631) | Wansley (6052, mid_vintage_exit_carry) is COAL_BIT and does not enter this row |
| CC_REGULAR 2019 | +2.68 TWh | +3.50 TWh (+567 MW) | **seasonal_capacity_basis (E.1)** | +4.32 TWh alone / +4.67 loo; +676 MW pmax; led by 710 McDonough (+1.23 TWh) | block rating −0.72 (643); cod fallback −0.45; denominator 0 alone / +0.53 loo |
| CC_REGULAR 2021 | +2.04 TWh | +4.07 TWh (+676 MW) | **seasonal_capacity_basis (E.1)** | +4.53 TWh alone / +5.07 loo; led by 710 McDonough (+1.16 TWh) | cod fallback −0.54; denominator −0.46 alone (533) / +0.56 loo; mid_vintage −0.46 alone (533) / 0 loo |

## Limitations

- **Available energy is a proxy for MWh.** The LP response is neither additive nor proportional:
  - The CC model Δ is 77 % (2019) and 50 % (2021) of the Δ in available energy.
  - The single-field ("alone") values do not sum to the all-W0 total: COAL_PRB alone-sum is +0.36 TWh against +2.44 TWh all-W0, because of interactions. Both the alone and the leave-one-out values are reported for that reason.
- **The incumbent's per-plant MWh cannot be recovered without an LP**, because soco96_span keeps no per-unit sidecar. The per-plant incumbent-versus-W0 split above is therefore W0 model MWh paired with the Δ in available energy per plant, not a measured incumbent per-plant ΔMWh. The class-level Δ is measured.
- **The Scherer dilution mechanism is inferred** from the arithmetic and the field semantics (`scenarios.py`, the comment block on `unit_outage_dispatched_bin_denominator` and `unit_outage_dispatched_bin_live_denominator`). It has not been traced through `data/outages.py`.
- **EIA-923 comparisons are at plant/prime-mover grain**, not generator grain.

## Addendum: the cross-ISO exit-carry audit (sent to main separately)

Scripts: `carry_census.py`, `carry_audit.py`, `carry_summary.py`. Outputs: `out/carry_audit_final.csv`, `out/table_exit.md`, `out/table_other.md`.

There are 100 census carries over 100 MW, totalling 61,222 MW. They split into:

| Bucket | Rows | MW |
|---|---|---|
| EXIT-CARRY | 30 | 19,279 |
| CLASS-BOUNDARY | 46 | 24,946 |
| FOOTPRINT | 15 | 11,281 |
| PHANTOM (0 available MWh) | 9 | 5,716 |

- **Low-CF exit carries:** 6 of the 30 have under 5 % EIA-923 CF over their online months, 3,574 MW (19 %). They are Redondo Beach (CAISO) 2023, Braunig (ERCOT) 2025, Sterlington (MISO) 2020, Meramec (MISO) 2022, Hammond (SOCO) 2019 and McIntosh-1 (SOCO) 2019.
- **Model overshoot:** the model exceeds EIA-923 in 19 of the 28 exit carries that have a leg on disk, by +9.5 TWh in total.
- **SOCO fields, confirmed by toggle:** Hammond 2019 and Wansley 2022 come from mid_vintage_exit_carry; McIntosh-1 2019 comes from partial_plant_exit_carry.
- **SOCO footprint carries are not W0:** 533, 7063 and 55242 are already in the incumbent's fleet.
