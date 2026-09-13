# NWPP conventional-hydro monthly net generation (EIA-923)

The input for **NWPP-32**'s monthly hydro budget and the measured evidence
behind owner card **N3** (`docs/multi-iso/nwpp-addition-plan-2026-09.md` §2.7,
§6 row 6). Landed by NWPP-11, 2026-09-13 —
`docs/handoffs/FINDING-nwpp-11-2026-09-13.md` §5.

## Files

| file | what |
|---|---|
| `nwpp_hydro_monthly_923.parquet` | 7,212 plant-months, long form: `plant_id, plant_name, ba_code, prime_mover, fuel_type, year, month, netgen_mwh, netgen_annual_mwh, nameplate_mw_860, state, hours_in_month, capacity_factor` |
| `nwpp_hydro_monthly_923_flags.csv` | one row per plant-year with the four source-quality flags below |

Rebuild (pure extract — a filter, a reshape, one EIA-860 nameplate join; no
modelling, no gap-filling, no rescaling):

    python scripts/data/build_nwpp_hydro_monthly.py

## Population

`prime_mover == "HY"` (conventional hydro, fuel `WAT`) in one of the 17 NWPP
balancing authorities. **Pumped storage (`PS`) is excluded by design**, matching
`market_sim.data.hydro.load_hydro_budget`'s own population; the footprint holds
exactly one PS plant (314.0 MW, BPAT), available via `--include-ps` for the
record but never mixed into the budget population.

Sources, both already committed:
`data/raw/_processed-legacy/eia923_monthly_generation.parquet` (the same extract
`load_hydro_budget` reads) and `data/raw/eia-860/{eia860_plant,
eia860_generator_operable}.parquet` for the nameplate envelope and the
`Balancing Authority Code` the footprint is defined on.

## Coverage — and the 2025 early release, stated at the gate

| year | plants | net generation | 860 nameplate joined |
|---|---:|---:|---:|
| 2023 | 290 | 106.928 TWh | 35,719.5 MW |
| 2024 | 286 | 107.900 TWh | 35,707.5 MW |
| **2025** | **25** | 74.936 TWh | 24,515.6 MW |

**2025 is an EIA-923 EARLY RELEASE carrying only the monthly-survey reporters.**
`EIA923_LATEST_FINAL_VINTAGE` is 2024 at this pin, and the committed 2025 rows
hold 25 of ~290 footprint hydro plants (139 of 1,391 nationally; 3,427 of 13,210
plants across all fuels). **Verified 2026-09-13 to be the newest 2025 vintage
that exists**: EIA's own `archive/xls/f923_2025.zip`
(`EIA923_Schedules_2_3_4_5_M_12_2025_20FEB2026.xlsx`) carries the identical
7,653 rows / 3,427 plants / 139 national HY plants / **25 footprint HY plants**.
The shortfall is a *source* state, not a repo gap, and is the same one
`load_hydro_budget`'s `backfill_year` and `monthly_target_mwh` arguments already
document for CAISO and NEISO 2025. **Nothing is filled here.** Choosing between
backfill, repin and wait is NWPP-32's call.

**The 25-plant panel is not a random sample and must not be read as one.** It is
a strict subset of both complete years, covers **68.6 % of nameplate and 66.0 %
of 2023 energy**, and contains **all eight ≥ 1 GW plants** (McNary, 990.5 MW, is
the largest absentee). So a like-for-like comparison is available and is the
only honest one: on the same 25 plants, 2025 runs **+6.1 % against 2023 and
+7.5 % against 2024**. Comparing the raw annual totals (74.9 vs 107.9 TWh) would
read as a 31 % drought and would be **wrong**.

## Flags — reported, never filled

`nwpp_hydro_monthly_923_flags.csv`, one row per plant-year. All four are
statements about the **source**:

| flag | 2023 | 2024 | magnitude (2023) |
|---|---:|---:|---|
| `missing_months` | 0 | 0 | — the series are complete wherever a plant reports |
| `all_zero` | 7 | 3 | 34.1 MW, 0.10 % of nameplate, 0.00 % of energy |
| `cf_over_1` | 31 | 31 | 757.9 MW, 2.12 % of nameplate, 3.83 % of energy |
| `negative_months` | 41 | 30 | 811.9 MW, 2.27 % of nameplate, 1.60 % of energy |

* **`cf_over_1`** — a month whose 923 energy exceeds 860 nameplate × hours, so
  the two records disagree. Concentrated in small plants and worst at Nooksack
  Hydro (PSEI, 860 nameplate 1.5 MW, max monthly CF **1.78**), Wanship (PACE,
  1.9 MW, 1.29), Ryan (NWMT, 55.2 MW, 1.26). The likely cause is a **stale or
  partial 860 nameplate**, not inflated 923 energy — relevant to NWPP-32's MW
  envelope under rule 14 `[R-ACCURATE]`, which is why it is surfaced rather
  than clipped.
* **`negative_months`** — physically real where station service exceeds output.
  Four plants report negative in every month of a year (Prospect 3 −174 MWh,
  Prospect 4 −60, Weber −185, Hydro III −70); all are tiny.
* **`all_zero`** — largest is Electron (PSEI, 22.8 MW) at zero across both 2023
  and 2024, consistent with a multi-year outage. `Port Townsend Paper` (BPAT)
  carries a 923 hydro row with **no** EIA-860 hydro nameplate at all.

## What this artifact cannot express (plan §2.7, card N3)

Restated here so it is not rediscovered in W4: the model's hydro object is an
independent **monthly** energy budget per plant. It cannot express hydraulic
coupling down a river (eight of the footprint's ten largest hydro plants are one
Columbia-mainstem chain), sub-monthly reservoir carryover and refill, or
flood-control / fish-spill obligations. Those are NWPP-32's and NWPP-36's
problem, not this extract's — but the extract is what they will be built on.
