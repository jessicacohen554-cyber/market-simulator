# Holdout data-equivalency register (G-19) — 2026-07

The owner-ordered gating deliverable (2026-07-07): **no holdout solve, score,
or recorded result for ANY ISO until this register exists and the owner signs
off per ISO** (method + format:
`docs/handoffs/holdout-data-equivalency-register-handoff-2026-07.md`). The
question, per ISO × holdout window, series by series: is the holdout year's
input set **EQUIVALENT** to the keeper years' (2023–2025) — same source, same
series, same granularity, same vintage/derivation recipe — for every input the
keeper recipe consumes and every bench series the verdict scores against?
"Present" is not the bar; **parity** is.

Grades: **EQUIVALENT** (same source + grain + recipe) / **DEGRADED** (present
but sparser grain, different derivation vintage, proxy vintage, partial
coverage, or a source substitution) / **MISSING** (absent). Every DEGRADED /
MISSING row carries materiality and a fix (or "accepted").

## Summary matrix

| ISO | 2022 | H1-2026 | Register section |
|---|---|---|---|
| ERCOT | intaken 2026-07-04 (§1.1), **not yet equivalency-audited** | intaken, publication-blocked tail (CAMPD Q2+, gas May+) | pending |
| PJM | intaken 2026-07-04 (§1.1), **not yet equivalency-audited** | same | pending |
| CAISO | zero intake — rows start MISSING | blocked + zero intake | pending |
| MISO | zero intake — rows start MISSING | blocked + zero intake | pending |
| NYISO | **THIS DOC §NYISO** — EQUIVALENT 24 / DEGRADED 4 / MISSING 5 (2026-07-12 intake) | not intaken (publication-blocked tail per G-19; only the 2018–H1-2026 Ask-B/C/D series span it) | **§NYISO below** |
| NEISO | intaken 2026-07-07 (§1.2) — register section pending; **landing residuals found 2026-07-12** (see §NEISO note) | blocked per G-19 | pending |

---

## NYISO — 2022 validation-holdout (intake 2026-07-12, this session)

Keeper: **`2026-07-11-nyiso-61-downstate-import`**
(`frontend/data/backcast/keepers.json`; bundle
`results/calibration/nyiso61_downstate_import`, flags from its
`run_config.json`). Data-consuming flags ON:
`nyiso_dynamic_reserve_requirements`, `nyiso_local_selfsupply`,
`nyiso_{nyc,li}_lcr_tsl`, `nyiso_firm_imports`, `nyiso_import_reconciliation`,
`nyiso_import_hub_prices`, `energy_reserve_coopt`, `reliability_floor`,
`priced_interchange`, gas stack (`gas_monthly_actuals`, `gas_daily_shape`,
`gas_hub_basis_overlay`, `gas_hub_basis_daily`, `nyiso_zonal_gas_basis`,
`nyiso_downstate_ct_gas_daily`, `dual_fuel_oil_reattribution`,
`dual_fuel_switching`, `coal_plant_monthly_pricing`,
`gas_plant_monthly_fuel_pricing`), `use_plant_emission_rates(+v2)`,
`use_campd_bins`, `plant_level_fleet`, `maintenance_monthly_shape`,
`chp_steam_following`, `outage_source=historic` (unit-level file;
`historic_outage_overlay=False` so the facility overlay is not consumed).
OFF (files not consumed): `nyiso_downstate_ct_gas_basis`,
`nyiso_iroquois_winter_spread`, `nyiso_rcpf_enabled`,
`temp_dependent_derate`, `gt_ambient_derate`,
`capacity_deliverability_limits` (but the LCR/TSL flags above read the same
registry file).

### Model inputs

| input | keeper-years source + grain | 2022 status | materiality / fix |
|---|---|---|---|
| Hourly demand (`eia-930/eia_demand_profiles.parquet`) | EIA-930 full-8760, 2021–2025 | **EQUIVALENT** (pre-existing) | — |
| Zonal load shares (`zone-specific-demand/NYISO/NYISO_load_actuals_<y>.csv`) | NYISO P-58 zonal actuals, hourly | **EQUIVALENT** (2018–2025 pre-existing) | — |
| EIA-930 NYIS wide + fueltype/region long | 2015–2026 multi-year files | **EQUIVALENT** (pre-existing; 2022 long-form landed earlier) | — |
| CAMPD unit-level NY + NJ (`campd-unit-level/{NY,NJ}_2022.parquet`) | EPA CAMPD hourly, per unit | **EQUIVALENT** (intaken 2026-07-10; arrow schema == sibling) | — |
| CAMPD facility-level NY + NJ | EPA facility bulk vintage (2023–2025) | **EQUIVALENT-derived** (this session: derived from the landed unit-level files by `scripts/derive_campd_facility_from_units.py`; recipe **proven cell-exact on 5 of 6 committed state-years**, and on NY-2025 exact except a known in-sample lineage drift — see note N1) | derive-time input only; persefoni registry joined from the 2023 sibling (sparse attribute) |
| Unit-outage windows (`campd-unit-outages-NYISO.csv`) — the keeper's outage layer | derived windows, 2023–2025, committed vintage | **MISSING 2022 + DEGRADED vintage** — the committed 1,598 windows do NOT reproduce from `derive_campd_unit_outages.py` at HEAD defaults (re-derivation → 2,641 windows; every committed window is contained in the re-derivation but +~1,000 appear). Same detector-vintage class as the NEISO item (register handoff §2). 2022 windows were **deliberately NOT derived** — a HEAD-vintage 2022 next to committed-vintage 2023–2025 would be a lineage asymmetry | **HIGH** (outage overlay shapes prices + volumes; a 2022 solve would silently run outage-free). Fix: calibration-owner adjudication — reconstruct the committed recipe/args or re-derive ALL years at a pinned vintage (changes keeper inputs), then derive 2022 with that vintage |
| Reserve requirements hourly (`NYISO-AS/requirements/NYISO_reserve_requirements_<y>.csv`) — `nyiso_dynamic_reserve_requirements` hard-requires it | derived from LRR schedule × TSA event windows | **EQUIVALENT** (this session: producer `derive_nyiso_reserve_requirements_hourly.py` re-verified — 2023–2025 re-derivation **byte-identical** to committed — then 2022 derived with the same recipe; v2021 LRR regime covers all of 2022; 17 TSA windows / 69 h zeroed) | — |
| LRR schedule + operating events (clean `nyiso-reserve-requirements`, `nyiso-operating-events`) | dated published versions + MIS logs 2018–H1-2026 | **EQUIVALENT** (pre-existing §1.2 intake) | — |
| Henry Hub daily/monthly | EIA, 1997–2026 | **EQUIVALENT** | — |
| Transco Z6 NY daily (`gas-prices/transco_z6_ny_daily.csv`) | EIA NG Weekly Update table + narrative prints, ~227/yr | **EQUIVALENT, one documented hole** — 239 prints for 2022 (238 table + 1 narrative; same producers, same grain). The EIA weekly archive has **no editions 2022-12-22 → 2023-01-12**, so the Winter-Storm-Elliott week (Dec 23–31) has no daily prints — the same holiday-hole class as the committed Dec-2024 gap, and it clips the year's costliest spike (rule 14 forbids fabricating dailies) | **medium** (Dec-2022 daily shape + monthly mean under-read the Elliott blowout). Accepted unless a free citable daily source appears; a paywalled NGI/ICE daily is a licence ask |
| Transco/Iroquois monthly (`transco_z6_iroquois_monthly.csv`) | monthly mean of daily prints + SOM annual Iroquois−Transco spread | **EQUIVALENT** (this session: 12 rows, identical construction; SOM-2022 spread $1.78 from the committed `nyiso_som_hub_fuel_annual.csv`; annual mean/SOM ratio 0.944 vs the in-sample years' own 0.90–1.045 band) | — |
| NYISO monthly basis rows (`gas_basis_by_iso_month.csv`) | Iroquois Z2 − Henry Hub, per month | **EQUIVALENT** (this session: the pre-existing 2022 rows carried a different construction — statewide-citygate proxy − HH; **re-based** onto the in-sample construction, hub/source labels updated; all non-NYISO-2022 rows byte-frozen) | was DEGRADED (proxy vintage); fixed on out-of-training rows only |
| Zonal gas hub annuals (`nyiso_zonal_gas_hub.csv`) | SOM Figure A-6 annual per-hub transcription | **EQUIVALENT** (this session: 5 zone rows from the NYISO **2022** SOM report Fig A-6 — Tenn Z4 200L $5.75 / Iroquois Z2 $8.82 / Transco Z6 NY $7.04 — same transcription convention and source format) | — |
| Downstate CT citygate premium (`nyiso_downstate_ct_gas_basis_monthly.csv`) | EIA N3050NY3 − Transco Z6 hub, monthly | **EQUIVALENT** (this session: same producer `fetch_nyiso_downstate_gas_basis.py`, window-parameterized, 12 2022 rows merged, in-sample byte-frozen; 2022 premium mean $2.32) | keeper flag for this file is OFF (`nyiso_downstate_ct_gas_basis=False`); extended for parity anyway |
| Downstate LDC non-firm transport (`nyiso_downstate_ldc_transport_monthly.csv`) — consumed by `nyiso_downstate_ct_gas_daily` | National Grid statnfdr PDFs, monthly, KEDNY SC-22 / KEDLI SC-19 Tier-1 | **EQUIVALENT** (this session: all 24 2022 statements fetched from the National Grid archive with the same producer — statement numbering extrapolates cleanly to 2022 — merged LDC-major, in-sample byte-frozen) | the keeper's downstate CT delivered-fuel path is fully 2022-covered (Transco daily + transport rate) |
| Weather zone temp (`nyiso-weather/nyiso_zone_temp_daily.csv`) | NOAA GHCN load-weighted zonal TMAX/TMIN daily | **EQUIVALENT** (this session: 1,825 zone-days merged from the on-disk `_2022h1/h2` split raws; zone-major layout preserved, in-sample byte-frozen) | consumed by floor/drag derives, not the keeper solve directly |
| Downstate NYC-metro TMAX (`nyiso_downstate_tmax_daily.csv`) | NCEI daily-summaries, Central Park/LGA/JFK mean | **EQUIVALENT** (this session: 365 days fetched with the same `fetch_nyc_tmax` producer, merged, in-sample byte-frozen) | loader `_downstate` sentinel input; keeper derate flags OFF |
| F923 delivered fuel + generation (`_processed-legacy/eia923_monthly_*.parquet`) | EIA-923, monthly, per plant | **EQUIVALENT** (2022 Final Revision landed 2026-07-04; 80 NY cost rows) | — |
| eGRID vintage | true-year workbook | **EQUIVALENT** (`egrid2022_data.xlsx` on disk, vintage registered) | — |
| Plant emission rates v1 (`plant_emission_rates.parquet`) | per-plant year rows {0, 2023, 2024} | **MISSING** 2022 (v1 also lacks 2025 in-sample; pooled `year==0` rows are what `egrid._campd_rate_map` consumes, so a 2022 run falls back to the pooled vintage) | **medium**. Fix: `derive_plant_emissions.py` extension — but see N3 (marker-gated tooling) |
| Plant emission rates v2 (`plant_emission_rates_v2.parquet`) | per-plant-year measured rates, 2018–2021 + 2023–2025 | **MISSING** — 2022 is a *gap year* inside an otherwise 2018–2025 artifact | **medium-high** (same-year measured rates are the backcast's CO2/NOx cost basis; the v2 estimator's fallback degrades to trailing/class rates). Fix: `curate_emissions_unit_annual.py --years 2022 --holdout-intake NYISO` + `derive_plant_emissions_v2.py --iso NYISO --years 2022 --holdout-intake NYISO` — **blocked today**: both tools hard-require a calibration-complete MARKER, encoding the pre-amendment rule-22 gate; under the 2026-07-06/07 Option-2 amendment intake needs only session-logged owner authorization. Owner decision: loosen the tools' gate to accept an `intake_log` authorization, or run them at one-shot time under the marker |
| Capacity-deliverability registry (`capacity-deliverability/nyiso/nyiso.csv`) — read by `nyiso_{nyc,li}_lcr_tsl` | NYISO LCR/TSL per delivery year, 2023/24–2025/26 | **MISSING** the 2022/23 delivery year | **medium** (downstate locality caps). Fix: transcribe the published NYISO 2022/23 ICAP LCR values + TSLs into the registry (public ICAP filings; same transcription convention) |
| Firm-import floors (`interchange_config.firm_import_floor_by_year`) | hand-derived constants for 2023/2024/2025 | **MISSING** a 2022 entry (code constant, not data) | **medium** (import-node structure under `nyiso_firm_imports`). Fix: derive from the now-landed 2022 interface flows + 2022 LMPs — calibration-owner derivation, same method note as the committed constants |
| Interface flows (`NYISO/interface-flows/`) | MIS P-32 hourly, 18 interfaces | **EQUIVALENT** (2018–2026 pre-existing) | — |
| Import hub prices / neighbor LMPs | committed hourly actuals per neighbor | **EQUIVALENT for NYISO-side 2022** (this intake); note the NEISO-side proxy parquet (`nyiso_proxy_lmp_hourly_NEISO.parquet`) is a NEISO-lane artifact | verify per-neighbor at one-shot config freeze |
| Fleet statics (EIA-860 vintage, `custom-bin-assignments.csv`, `master-plant-registry.csv`) | single registry snapshot, year-agnostic | **DEGRADED (accepted)** — same static vintage for every year including 2022; identical caveat already applies in-sample | accepted; note the 2022 fleet (e.g. units retired 2022–2023) reads through the same snapshot |
| NYISO-AS price CSVs (`NYISO-AS/NYISO_as_{da,rt}_2022.csv`) | NYISO MIS, hourly/zonal | **EQUIVALENT** (pre-existing) — **validation-side only** (rule 13: reserve prices are never an input) | — |

### Bench / scoring series

| series | keeper-years grain | 2022 status | note |
|---|---|---|---|
| `actual_lmp_hourly_NYISO.parquet` | dense 8760 hub-mean DA+RT, from MIS damlbmp_zone + realtime_zone archives | **EQUIVALENT** (this session: 2022 block built by the committed `derive_actual_lmp.py` NYISO builder on the same MIS lineage — 12 DA + 12 RT monthly zips — full coverage both markets; 2023–2025 rows asserted frozen pre/post write) | independent anchor: SOM-2022 published averages — derived equal-hour vs SOM load-weighted ratios 0.90–0.95 across NYC/LI/Capital DA + LI RT, the expected LW wedge sign/size |
| `actual_lmp.json` NYISO annual/monthly/pct + zones | same derivation | **EQUIVALENT** (2022: DA $72.74 / RT $74.77; all other ISO blocks byte-identical) | — |
| `actual_tail.json` NYISO 2022 | marker-aware `derive_actual_tail.py` | **READY, deliberately not emitted** — the deriver is marker-gated by design; the extended hourly parquet will auto-emit the NYISO 2022 row the moment the calibration-complete marker lands (verified: current re-run is byte-identical) | not a gap — quarantine machinery working as designed |
| `actual_as_reserve_NYISO.parquet` (RCPF/reserve validation analogue) | per (year,hour) stacked RT reserve prices | **EQUIVALENT** (this session: rebuilt 2022–2025 with its own producer `process_nyiso_as.build_reference`; 2023–2025 rows verified identical) | — |
| `calibration_reference.json` `isos.NYISO.2022` | EIA-860/-923/-930 per-year block | **EQUIVALENT** (this session: spliced ONLY the 2022 block from a full rebuild; all other churn restored) | **in-sample flag**: `isos.NYISO.2024` and `NYISO_2024_renewable_capacity.csv` are MISSING (builder pins NYISO to (2023, 2025); its "gated on NY_2024 unit-level outages" rationale is stale — NY_2024 CEMS exists). Flagged to the NYISO calibration owner; NOT fixed here |
| `NYISO_2022_renewable_capacity.csv` | EIA-860 per-zone monthly wind/solar MW | **EQUIVALENT** (same builder, same 121-row shape as 2023/2025) | — |
| EIA-930 fuel-mix bench (`NYIS_fueltype/region`) | hourly, 2015–2026 | **EQUIVALENT** | — |
| CAMPD generation bench (NY/NJ unit-level) | hourly | **EQUIVALENT** | — |
| EIA-930 storage breakout (C5b/C5c) | exists in-sample | **accepted structural absence** — the breakout does not exist for 2022 in the NYIS BA; C5b/C5c will SKIP for 2022 | recorded per the register handoff §6; not a gap to fill |

### Notes

- **N1 (in-sample finding, calibration owner):** the committed
  `campd-facility-level/NY_2025.parquet` disagrees with the committed
  unit-level lineage on exactly 53 Edgewood Energy (55786) Jan-2025 hours
  (so2/co2/nox mass + heatInput, uniformly ×~0.938) — an EPA resubmission
  between the two files' fetch dates. Itemized as `KNOWN_VINTAGE_DRIFT` in
  `scripts/derive_campd_facility_from_units.py`; every other committed
  state-year (NY/NJ × 2023–2025) reproduces cell-exact from the unit files.
- **N2 (misfiled reference data):** every `lmp-data/**/dartmonthlylmpindex_*.csv`
  — including the three under `lmp-data/NYISO/` — is an **ISO-NE** monthly LMP
  index report (`.H.INTERNAL_HUB`, `.Z.*` locations), not NYISO. No
  NYISO-published machine-readable monthly LMP index exists in-repo; the SOM
  annual tables are the independent anchor used instead.
- **N3 (tooling/policy skew):** `curate_emissions_unit_annual.py` and
  `derive_plant_emissions_v2.py` `--holdout-intake` still hard-require the
  ISO's calibration-complete marker — the pre-amendment gate. The rule-22
  Option-2 amendment (2026-07-06/07) authorizes intake on session-logged owner
  authorization without a marker. Not changed here (quarantine machinery);
  owner call.
- **N4 (LDC transport 2022):** RESOLVED EQUIVALENT — National Grid's archive
  carries the 2022 statnfdr statements and the committed producer's statement-
  number extrapolation reaches them without modification.
- **N5 (NEISO landing residuals, observed 2026-07-12):** at this branch's base
  the NEISO §1.2 bench artifacts are still absent from main
  (`actual_lmp_hourly_NEISO.parquet` / `actual_lmp.json` / `actual_tail.json`
  carry no NEISO 2022; `NEISO_2022_renewable_capacity.csv` absent;
  `docs/gap-register-2026-07.md` a placeholder stub). A parallel NEISO
  readiness session logged its own 2026-07-12 intake authorization and landed
  `scripts/land_neiso_2022_readiness.py` the same day — the residuals resolve
  when that lander runs. NEISO lane, not touched here; both sessions' JSON
  merges are additive per-ISO, so they compose.

### What still blocks a NYISO 2022 one-shot

1. **Owner calibration-complete declaration** (the IMM Rec 2021-1 frontier gap
   — frontier ≠ complete): no `complete.NYISO` marker exists, and rule 22
   forbids any 2022 solve/score/registration until it does. The global
   one-shot HOLD (G-19) also stands.
2. **Register sign-off** (this section) by the owner.
3. The three grade-bearing input gaps above if the owner wants full parity
   before scoring: unit-outage windows (vintage adjudication — the largest),
   emission-rates 2022 (tool gate decision), capacity-deliverability 2022/23 +
   firm-import-floor 2022 constants (small transcriptions/derivations).

Data availability itself is otherwise no longer on the blocking list: drivers,
overlays, and every bench series are landed and lineage-verified.

---

## ERCOT / PJM / CAISO / MISO / NEISO

Sections pending their own lanes. Seed material:
`docs/out-of-sample-results-2026-07.md` §1.1 (ERCOT/PJM, incl. the known Waha
annual-basis and PJM wide-extract-lineage DEGRADED candidates), §1.2 (NEISO,
incl. the Algonquin weekly-anchored daily and the outage-window vintage), and
the register handoff's known-items list (§"Known DEGRADED/asymmetric items").
