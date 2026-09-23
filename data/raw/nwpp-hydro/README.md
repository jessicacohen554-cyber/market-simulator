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

## NWPP-32 artifacts — the budget, the envelope, the chain (2026-09-14)

Built by `scripts/data/build_nwpp_hydro_budget.py` from the extract above, the
loader's own EIA-860 reader, ORNL EHA FY2024, HILARRI v4 and the 17 per-BA EIA-930
extracts. A join, a reconciliation and a flag — **no modelling, no gap-filling, no
rescaling, no fitted scalar** (rules 13 / 14). Pre-registration
`docs/handoffs/PRECOMMIT-nwpp-32-2026-09-14.md`; result
`docs/handoffs/FINDING-nwpp-32-2026-09-14.md`.

| file | what |
|---|---|
| `nwpp_hydro_budget.parquet` | 877 rows = one per (plant, year) over the union of the 288 EIA-860 `HY` plants and each year's EIA-923 reporters (295 / 294 / 288): `m01..m12` raw monthly MWh (negatives RETAINED — the loader clips them, `loader_clip_mwh` reports the clip), `budget_annual_mwh`, `netgen_annual_mwh_923`, `delta_mwh`, `status`, `max_mw` (EIA-860 nameplate; `max_mw_source` names the loader's peak-monthly-average fallback where 860 is absent), `min_mw` (0 — no floor is stamped by this lane), `zone`, `ba_code`, `river_eha`, `mode_eha`, `dam_owner_eha`, `huc_eha`, `ferc_docket_eha`, HILARRI reservoir-linkage flags, `chain`, `chain_order`, `loader_kept` |
| `nwpp_hydro_reconciliation.csv` | the per-plant-year gate table (same rows, the columns a reader needs) |
| `nwpp_hydro_chain_published.csv` | HAND TRANSCRIPTION of published chain facts — BPA *The Columbia River System Inside Story* pp. 14–15 (storage/run-of-river type, storage MAF, average discharge cfs, capacity kW) and the HRFCPPA 2004 seven-project definition — one source column per row; the only file here written by hand |
| `nwpp_hydro_chain.csv` | the transcription joined to nameplate, 2023–2025 energy, EHA mode/river/HUC/FERC docket and reservoir linkage: **NWPP-36's reach table** |
| `nwpp_hydro_within_month_930.csv` | per (BA, year, month) within-month shaping statistics off EIA-930 `NG: WAT` for the pool and every member: mean MW, diurnal amplitude, daily-energy CV, first-week/last-week ratio, p5/p50/p95/min/max MW |

**Gate (rule 13):** every plant-year reconciles to EIA-923's own annual column at
**0.000 MWh** (tolerance 1.0), all three years; nothing is filled. `status` values:
`RECONCILED`, `ALL_ZERO`, `NON_POSITIVE` (reconcile but carry ≤ 0 energy — the loader
drops them), `NO_923_SERIES` (in EIA-860, absent from that year's EIA-923 — 5 / 8 / **263**
plants; 2025 is the early release), `MISMATCH` (none). `no_860_nameplate` marks the
7 / 6 / 0 EIA-923 reporters with no EIA-860 hydro nameplate — four of them are the
Klamath dams removed in 2023–2024 (Copco 1, Copco 2, Iron Gate, John C. Boyle: 387.4 GWh
of real 2023 energy, 8.8 GWh in 2024), for which the loader's peak-monthly-average
fallback is the correct envelope.

**Pumped storage stays out by design** (one plant, 314.0 MW, BPAT) — storage, not inflow.
The EIA-930 pool `NG: WAT` is NOT the same population as these plants (−2.5 % stable,
decomposed by BA in the FINDING §3) and carries known-defective hours (Oct 2025 +14 %),
so a 2025 `eia930_monthly` repin is refused there; the recommended 2025 posture is
`backfill_year=2024` alone, with the like-for-like wetness declared.

## NWPP-36 artifacts — the cascade coupling measurement (2026-09-16)

The measured inputs of `ScenarioConfig.hydro_cascade_coupling` (owner ruling N3;
`docs/handoffs/PRECOMMIT-nwpp-36-2026-09-16.md` §4, result
`docs/handoffs/FINDING-nwpp-36-2026-09-16.md`). Read by
`market_sim.data.hydro.load_hydro_cascade`. **Every τ, band, η and inflow is
measured; a link that fails a pre-registered gate is left `coupled = False` with
its reason — never a substituted value** (rule 13). Rule 23: re-derive only when
CROHMS, NID or EIA-923 update, never against a residual.

| file | what | built by |
|---|---|---|
| `crohms/nwpp_crohms_hourly.parquet` | 2,103,124 rows, long form `station, series, ts, value, quality`: the 16 hourly-instrumented chain projects (GCL CHJ WEL RRH RIS WAN PRD MCN JDA TDA BON DWR LWG LGS LMN IHR) × `Flow-Out.Ave.1Hour.1Hour.CBT-REV`, `Flow-Spill.…CBT-REV`, `Flow-Gen.…CBT-REV` (kcfs), `Elev-Forebay.Inst.1Hour.0.CBT-REV` (ft), `Power.Total.1Hour.1Hour.CBT-RAW` (MW), 2023-01-01 → 2026-01-01 in the service's fixed standard time, all quality code 0; ≤ 140 missing hours per series (Dworshak), sentinels (−99999 in two Power series, isolated 0.0 forebay readings) screened by the derive, not here | `scripts/data/fetch_nwpp_crohms_hourly.py` — `https://public.crohms.org/dd/common/web_service/webexec/getjson?query=["<STATION>.<series>",…]&startdate=MM/DD/YYYY HH:MM&enddate=…`, calendar-quarter windows, pulled 2026-09-16 |
| `crohms/nwpp_crohms_daily_idp.parquet` | the Idaho Power Hells Canyon series CROHMS carries — DAILY only (`BRN.Flow-Out.Inst.~1Day.0.IDP-COMPUTED-REV`, `HCD.Flow-Out.Ave.~1Day.1Day.IDP-REV`; nothing for Oxbow) — the record behind "unmeasurable at hourly precision"; never used to couple | same |
| `crohms/nwpp_crohms_catalog.json` | the `tscatalog` response for the 19 stations (coordinates, datum, series inventory); the celerity check's distances | same |
| `crohms/SHA256SUMS.txt` | identity record of the pull | same |
| `nwpp_hydro_cascade_nid.csv` | the 16 chain dams' rows from the NID national CSV (`nid.sec.usace.army.mil/api/nation/csv`, "Data Last Updated 2026-9-11"), verbatim columns: surface area, storage, heights, coordinates | `scripts/data/build_nwpp_hydro_cascade.py --nid-national <csv>` |
| `nwpp_hydro_cascade_links.csv` | one row per link (15): τ and its r-table (r(τ), r(τ±1), r(0), 2023-only / 2024-only / 2025 τ), distance and implied celerity, the §4.1 verdict, the downstream plant's band (p99.5−p0.5 forebay by year, the year used, NID area, `pond_kcfsh`, the band in hours of published and measured discharge, the NID max−normal cross-check), and the composite `coupled` / `reason` | same |
| `nwpp_hydro_cascade_monthly.csv` | one row per plant-month (16 × 36): η (EIA-923 net MWh per kcfs·h of CROHMS turbine flow; `eta_source_year` names the nearest-year substitution for McNary / Dworshak 2025), the CROHMS gross ratio and net/gross, monthly-mean outflow and spill, and for plants with an upstream the measured side inflow (raw, floored, the floor magnitude and the 2 % STOP flag) | same |

**Verdict at this pull (details in the FINDING):** 5 of 15 links couple — GCL→CHJ,
CHJ→WEL, RRH→RIS, TDA→BON, LMN→IHR. Ten fail a gate: WEL→RRH (celerity 34.9 mph),
RIS→WAN (per-year τ disagree), DWR→LWG (r 0.02), and seven on the 2 % side-inflow
floor in spill-season months (downstream metered outflow 2–8 % below upstream, a
spill-metering artefact at the federal lower-river projects).

## NWPP-49 artifact — per-plant forebay storage (2026-09-23)

`nwpp_hydro_pondage.csv` — the measured input behind `ScenarioConfig.hydro_pondage_bound`, built
exactly as NYISO's and PJM's (`scripts/data/build_hydro_pondage.py --iso NWPP --nid-csv
data/raw/nid/nid_nwpp_hydro_dams.csv`): USACE NID `Max Storage` × `Hydraulic Height` (else the
labelled `NID Height` proxy) at turbine efficiency 1.0 — a deliberate UPPER bound — over each plant's
distinct HILARRI-linked impoundments. One row per plant with identified storage; **no row means no
bound** (never a substituted value). Zero fitted constants; no registry entry was added for NWPP.

**Coverage on the keeper's LP hydro fleet (2024; 2023 within 0.2 GW):** 280 plants, 35,694.6 MW.

| | plants | MW |
|---|---:|---:|
| NID storage identified (table rows; 161 of them are LP plants, 31,656 MW) | 168 | 31,746.8 |
| UNSET — no HILARRI→NID link or no storage/head (stay on the monthly budget) | 119 | 4,038.2 |
| … of which on the registered chains: McNary 990.5, Lower Granite 810.0, Ice Harbor 603.0, Selis Ksanka Qlispe 227.8, Oxbow 190.0, Box Canyon 90.0 | 6 | 2,911.0 |
| … of which off-chain (largest: Upper Baker 104.8, Summer Falls 92.0, Cowlitz Falls 70.0, Long Lake 70.0) | 113 | 1,127.0 |
| storage ≥ the plant's largest monthly budget (row redundant, dropped by the loader) | 72 | 12,416 |
| storage < largest month (a row would be built) | 89 | 19,240 |

Median storage is 156 nameplate-hours; 18.6 % of the identified MW holds < 24 h. **What NID cannot
see:** the licensed operating band. On the Columbia mainstem the operated band NWPP-36 measured from
CROHMS forebay elevations (`nwpp_hydro_cascade_links.csv` `pond_kcfsh`) is **5–40× smaller** than
NID gross volume (e.g. The Dalles 2.6 vs 62 h of mean output). Which one a given plant should carry,
and under what inflow, is the design question in
`docs/handoffs/FINDING-nwpp-49-pondage-design-2026-09-23.md`.
