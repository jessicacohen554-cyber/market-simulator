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
| NYISO | **§NYISO — 2022** EQUIVALENT 24 / DEGRADED 4 / MISSING 5 (2026-07-12); **§NYISO — 2018/2019/2020/2021** below (this session) | **§NYISO — H1-2026** below (this session) — partial, CAMPD/gas/LMP sources publication-lag to ~Q1-2026 | **§NYISO below** |
| NEISO | **THIS DOC §NEISO** — EQUIVALENT 12 / DEGRADED 8 / MISSING 6 (2026-07-13 intake, 2018-2022) | blocked (publication horizon, same class as all ISOs) | **§NEISO below** |

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

## NYISO — 2018/2019/2020/2021 (validation-ladder) + H1-2026 (locked-test edge) intake (2026-07-13, this session)

Owner authorization (verbatim, logged in `calibration-complete.json` `intake_log`):
"owner (2026-07-13): 'This data can literally be collected for all years — we're
not running anything on it. Fetch it all at once for 2018-2022 and first half
2026 if available.'" 2022 itself was already intaken 2026-07-12 (section
above); this session's scope is 2018/2019/2020/2021 (extending the
validation-ladder per rule 22's staged-backward wording) and H1-2026 (the
locked-test edge window). **NYISO now carries a calibration-complete marker**
(`complete.NYISO`, declared 2026-07-13) — the one-shot holdout validation is
AUTHORIZED but NOT run this session (no LP solve/score/registration of any
out-of-training year was performed; G-19 execution HOLD still governs when
the one-shot itself may fire). This section is DATA READINESS only.

Every write below MERGED into an existing file with the committed 2023-2025
(and, where applicable, 2022) rows asserted byte-frozen before and after the
write (programmatic `.equals()`/exact-line-set checks, not spot checks); every
new script/derive run reused the exact producer/recipe of the committed
in-sample rows. No dispatch solve was constructed for any year.

### Model inputs

| input | 2018–2021 | H1-2026 | note |
|---|---|---|---|
| CAMPD unit-level NY + NJ | **EQUIVALENT (pre-existing)** — `NY_2018..2021.parquet` / `NJ_2018..2021.parquet` already on disk, same EPA CAMPD hourly extract | **EQUIVALENT (pre-existing)** — `NY_2026.parquet`/`NJ_2026.parquet` on disk, but the extract itself only carries **Jan 1 – Mar 31, 2026** (CAMPD's own publication lag; no Q2 rows exist upstream yet) | H1-2026 is genuinely Q1-only; not a gap in our intake, a gap in EPA's own release cadence |
| CAMPD facility-level NY + NJ | **EQUIVALENT-derived (this session)** — `derive_campd_facility_from_units.py --states NY NJ --year {2018,2019,2020,2021} --persefoni-sibling 2023`, same recipe re-proven cell-exact on all 6 committed 2023-2025 state-years before deriving; new files `campd-facility-level/{NY,NJ}_{2018,2019,2020,2021}.parquet` | **EQUIVALENT-derived (this session), Q1-only** — same recipe, `--year 2026`; inherits the Q1-only unit-level source coverage above | persefoni-organization attribute sparse in every year (same caveat as committed years) |
| Plant emission rates v1 (`plant_emission_rates.parquet`) | **MISSING (pre-existing gap, not introduced here)** — v1 only ever carried `{0, 2023, 2024}`; 2018-2021 (and 2025) are absent regardless of ISO or holdout status | **MISSING** — same | not a holdout-specific gap; the pooled `year==0` fallback is what `egrid._campd_rate_map` actually consumes. Out of this session's scope to backfill (would touch the shared v1 tool's default behavior for in-sample years too) |
| Plant emission rates v2 (`plant_emission_rates_v2.parquet`) | **EQUIVALENT (pre-existing)** — 2018-2021 NYISO rows were already present in the committed artifact (`derive_plant_emissions_v2.py` default in-sample path is not restricted to 2023-2025; 2018-2021 pre-date the rule-22 quarantine boundary and were never gated) | **EQUIVALENT-derived (this session), Q1-only** — now UNBLOCKED (NYISO calibration-complete marker exists): `curate_emissions_unit_annual.py --years 2026 --holdout-intake NYISO` then `derive_plant_emissions_v2.py --iso NYISO --years 2026 --holdout-intake NYISO`; merged with existing-row freeze assertion (script's own `frozen_ok` check passed) | H1-2026 rate is a Q1-only measured rate (heat/mass ratios over Jan-Mar operating hours only) — DEGRADED by partial-year coverage, not by recipe; flag to the calibration owner if a full-year v2 row is wanted before the locked-test one-shot (would need to re-run once Q2-Q4 CAMPD lands) |
| Capacity-deliverability registry (`capacity-deliverability/nyiso/nyiso.csv`) | **DEGRADED — 2 of 4 delivery years landed.** 2018/2019 transcribed (NYC 80.5% / LI 103.5% / G-J 94.5% LCR, percentages only — no MW in the source snippet found) from NYSRC's "2018/2019 NYSRC Reliability Rule A.2 R1-R2-R3 Compliance Submittal"; 2022/2023 transcribed in full (NYC 81.2% / LI 99.5% / G-J 89.2% LCR; TSL import limits NYC 2,900 / LI 325 / G-J 3,425 MW; NYCA IRM 19.6%) from the NYISO "LCR2022-Report.pdf" (`nyiso.com/documents/20142/27428389/LCR2022-Report.pdf`). **2019/2020 and 2020/2021 delivery years remain MISSING** — not fetched this session (time-boxed; the same nyiso.com/documents + nysrc.org archive pattern that produced the two landed years covers them too, confirmed fetchable, just not completed) | **MISSING** — H1-2026 falls inside the already-committed 2025/2026 delivery year (requirement 8,673 MW / 0.785 NYC etc.), so no new row is needed for H1-2026 itself; not a gap | medium materiality (downstate locality caps feed `nyiso_{nyc,li}_lcr_tsl`). The 2022/2023 row's `requirement` metric intentionally carries `value_pu` only (blank `value_mw`) — the source report's approved-LCR table gives percentages only; the MW figures it also prints (8,451/4,871/12,238) are a *different* TSL-floor calculation at a *different* percentage (77.2%/94.4%/80.7%), not the approved-LCR MW, and pairing them would misrepresent the source (rule 14) |
| `interchange_config.py` NYISO year-grounded import ladder (`IMPORT_TRANCHES_BY_YEAR["NYISO"]` — the actual per-year hand-derived constant the register's earlier "`firm_import_floor_by_year`" reference maps to; NYISO carries no field of that exact name, only MISO's `NeighborInterface.firm_import_floor_by_year`) | **MISSING, blocked cross-ISO** — `derive_nyiso_import_ladder.py` derives the ladder from `actual_lmp.json`'s **PJM** and **NEISO** hub blocks (p75/p95 by year), and those blocks only carry 2023-2025 in the committed file; extending them for 2018-2021 is a PJM/NEISO-lane task, out of scope for this NYISO-only session | **MISSING**, same blocker | not fixable from the NYISO side alone; flag to whichever session next owns PJM or NEISO LMP-bench extension — once `actual_lmp.json["PJM"]`/`["NEISO"]` carry a year, re-running `derive_nyiso_import_ladder.py` with that year added to its `YEARS` list produces the NYISO-side constant for free |
| Reserve requirements hourly (`NYISO_reserve_requirements_<y>.csv`) | **MISSING — genuine source-coverage gap, not an intake failure.** `derive_nyiso_reserve_requirements_hourly.py --year 2018 2019 2020 2021` fails for every year: the published LRR-schedule clean source (`nyiso-reserve-requirements`) only carries three versions — `v2020` (evidence 2020-10-29 → 2021-12-04), `v2021` (2021-12-04 → 2026-02-14), `v2026` (2026-07-10 →, open). No single version fully covers 2018, 2019, 2020, or 2021 (the tool's own gate: "expected exactly one LRR version covering the full year, got []") | **MISSING**, same mechanism — `v2021` ends 2026-02-14 and `v2026` doesn't start until 2026-07-10, so H1-2026 (Jan-Jun) straddles a **published-schedule gap** with no covering version either | **high** materiality if the pre-2020 years or H1-2026 are ever solved (`nyiso_dynamic_reserve_requirements` hard-requires this file) — but per rule 14 the tool correctly refuses to fabricate a mid-year-transition treatment rather than force one. Fix: an explicit, adjudicated mid-year-version-splice extension to the derive script (a genuine methodology decision, not a data-fetch — out of this session's scope) |
| Henry Hub daily/monthly | **EQUIVALENT (pre-existing)** — EIA series already spans 1997-2026 | **EQUIVALENT (pre-existing)** | — |
| Transco Z6 NY daily (`transco_z6_ny_daily.csv`) | **MISSING** — not attempted this session; `fetch_transco_daily_spot.py` scrapes the EIA Natural Gas Weekly archive one publication-Thursday page at a time (confirmed live and reachable — a single 2018 page returned HTTP 200 in a smoke test — but a full year's ~50 page fetches did not complete inside this session's time budget) | **MISSING**, same | medium; the daily overlay refines the monthly mean's intra-month shape only — the monthly hub series (below) is the input that actually gates the offer curve. Fix: re-run `fetch_transco_daily_spot.py --start-year <Y> --end-year <Y>` per year in a follow-up session (network access to `eia.gov` confirmed working from this environment) |
| Transco/Iroquois monthly (`transco_z6_iroquois_monthly.csv`) | **MISSING** — blocked on the daily series above (`monthly-hubs` step needs a complete 12-month daily series first) | **MISSING**, same | same fix as the daily row |
| NYISO monthly basis rows (`gas_basis_by_iso_month.csv`) | **DEGRADED (pre-existing, unchanged this session)** — 2018-2021 rows already exist for all 12 months/year, but on the **old EIA-citygate-proxy construction** (`N3050NY3 − HH`), the same construction the 2022 rows carried *before* last session's re-base onto the in-sample `Iroquois Z2 (Transco + SOM spread) − HH` construction. Re-basing 2018-2021 needs the same monthly-hub series blocked above | **DEGRADED**, same — the pre-existing 2026 rows (file already spans through 2026) are on the old proxy construction too | same fix as the two rows above; once the daily/monthly Transco series lands for a year, `basis`-step re-basing is a same-day follow-on (the recipe is proven, see the 2022 precedent) |
| Zonal gas hub annuals (`nyiso_zonal_gas_hub.csv`) | **EQUIVALENT — landed this session.** 2018-2021 all 5 zone rows added from the pre-existing `nyiso_som_hub_fuel_annual.csv` (which already carried 2018-2021 SOM Figure-A-6 annual transcriptions) — no new fetch needed, same transcription convention, zone-major insertion preserving the committed layout; in-sample (2022-2025) rows verified byte-frozen (git diff shows insertions only) | **MISSING** — no NYISO 2026 State-of-the-Market report exists yet (SOM reports are published the following spring for a completed year; H1-2026 is mid-year) | this row differs from the daily/monthly Transco rows above — it derives straight from the already-landed SOM annual table, so it was cheap to close for 2018-2021 |
| Downstate CT citygate premium (`nyiso_downstate_ct_gas_basis_monthly.csv`) | **MISSING** — `fetch_nyiso_downstate_gas_basis.py` needs a per-year EIA N3050NY3 fetch; not attempted this session (same network-time-budget class as the Transco daily row) | **MISSING** | keeper flag for this file (`nyiso_downstate_ct_gas_basis`) is OFF anyway; low urgency |
| Downstate LDC non-firm transport (`nyiso_downstate_ldc_transport_monthly.csv`) | **MISSING** — `fetch_nyiso_downstate_ldc_transport.py` needs 24 National-Grid statnfdr statements/year; not attempted this session | **MISSING** | same low-urgency note (feeds `nyiso_downstate_ct_gas_daily`, OFF in the keeper) |
| Weather zone temp (`nyiso_zone_temp_daily.csv`) | **MISSING** — needs a NOAA GHCN per-zone daily fetch; not attempted this session | **MISSING** | consumed by floor/drag derives, not the keeper solve directly; medium-low urgency |
| Downstate NYC-metro TMAX (`nyiso_downstate_tmax_daily.csv`) | **MISSING** — `fetch_nyc_tmax` (imported from `derive_nyiso_ct_reliability_floor.py`) needs a live NCEI fetch per year; not attempted this session | **MISSING** | loader `_downstate` sentinel input; keeper derate flags OFF; low urgency |
| F923 delivered fuel + generation | **EQUIVALENT (pre-existing)** — EIA-923 Final Revision files for 2018-2021 already on disk | **MISSING** — EIA-923 for a given year is not published until the following autumn; H1-2026 has no F923 vintage to intake (a genuine publication-timing absence, not an intake gap) | — |
| eGRID vintage | **EQUIVALENT (pre-existing)** for 2018-2021 (`egrid{2018..2021}_data.xlsx` on disk) | **MISSING** — eGRID publishes ~18 months after year-end; no eGRID2026 vintage exists yet anywhere | — |
| Firm-import floors — see the `IMPORT_TRANCHES_BY_YEAR["NYISO"]` row above | (same row, listed once) | (same row) | — |
| Interface flows (`NYISO/interface-flows/`) | **EQUIVALENT (pre-existing)** — MIS P-32 hourly already spans 2018-2026 | **EQUIVALENT (pre-existing)** | — |
| Import hub prices / neighbor LMPs | **DEGRADED, blocked cross-ISO** — the NYISO-side hub means now exist for 2018-2021/2026 (this session's LMP-bench work, below), but the neighbor (PJM/NEISO)-side prices used by `nyiso_import_hub_prices` are the same PJM/NEISO `actual_lmp.json` blocks flagged MISSING above (2023-2025 only) | same | cross-ISO dependency, not fixable from the NYISO lane alone |
| Fleet statics (EIA-860 vintage, registries) | **DEGRADED (accepted)** — same year-agnostic static snapshot as every other year, identical pre-existing caveat | same | accepted, no change |
| NYISO-AS price CSVs (`NYISO-AS/NYISO_as_{da,rt}_<y>.csv`) | **EQUIVALENT (pre-existing)** — source CSVs already span 2018-2026 (validation-side only, rule 13) | **EQUIVALENT (pre-existing)** | — |

### Bench / scoring series

| series | 2018–2021 | H1-2026 | note |
|---|---|---|---|
| `actual_lmp_hourly_NYISO.parquet` + `actual_lmp.json` | **EQUIVALENT — landed this session.** Fetched all 12 DA (`damlbmp_zone`) + 12 RT (`realtime_zone`) monthly zips per year directly from `mis.nyiso.com` (network access confirmed live: HTTP 200, valid zip content), staged DA into the same transient `NYISO_zonal_hourly.zip` outer container the committed years' builder expects (deleted after the build — same as the committed years, per `derive_actual_lmp.build`'s own docstring: "the committed parquet is the durable record"), ran `derive_actual_lmp.build([2018,2019,2020,2021], isos=["NYISO"])`: **100% hourly coverage both markets, all four years.** Results: 2018 DA $34.87/RT $35.15; 2019 DA $25.36/RT $24.96; 2020 DA $19.23/RT $19.41; 2021 DA $37.07/RT $37.04. Merged with a programmatic frozen-row assertion (`.equals()` on the pre-existing 2022-2025 slice, pre- and post-write) | **EQUIVALENT-partial — landed this session.** Same fetch/build for `2026`, but `mis.nyiso.com` only publishes DA/RT zips through **June 2026** (6 of 12 months) — coverage densifies to the full non-leap 8760 calendar with the Jul-Dec hours **NaN** (49.6% coverage), exactly the same partial-year-densification convention the repo already uses elsewhere for in-progress years. 2026 (H1) DA $77.98 / RT $71.76 (means over the populated H1 hours only) | not independently SOM-anchored this session (SOM reports don't exist yet for 2018-2021 in a form re-checked here; the 2022 session's cross-check pattern is reusable in a follow-up) |
| `actual_tail.json` NYISO 2018-2021/2026 | **READY, deliberately not emitted** — `derive_actual_tail.py` is marker-aware; now that `complete.NYISO` exists it may auto-emit on next run, but this session did not invoke it (out of scope — no scoring/tail derivation was run) | same | — |
| `actual_as_reserve_NYISO.parquet` | **EQUIVALENT — rebuilt this session.** `process_nyiso_as.build_reference([2018..2021,2022..2026])` (source `NYISO_as_rt_<y>.csv` already spans every year); 2022-2025 rows verified value-identical to the committed file (column order differs — a Python `set()` iteration artifact of the producer's own column-alias loop — cell values match exactly under a matching column order) | **EQUIVALENT** — 2026 rows populated for every hour the source CSV carries (source itself may already be sparse past its own publication lag — not specifically checked) | — |
| `calibration_reference.json` `isos.NYISO.<y>` | **MISSING** — the builder pins NYISO to a hardcoded `(2022, 2023, 2025)` year tuple (a pre-existing issue already flagged to the NYISO calibration owner in the 2022 section: `isos.NYISO.2024` is missing too, an in-sample year); extending it to 2018-2021 needs the same builder-logic change, out of scope here | **MISSING**, same | not a new gap — the same structural builder-pinning issue noted in the 2022 section, now observed to also affect this session's target years |
| `NYISO_<y>_renewable_capacity.csv` | **MISSING** — same builder-pinning dependency as `calibration_reference.json` above (only 2022/2023/2025 exist) | **MISSING** | same |
| EIA-930 fuel-mix bench (`NYIS_fueltype/region`) | **EQUIVALENT (pre-existing)** — 2015-2026 multi-year files | **EQUIVALENT (pre-existing)** | — |
| CAMPD generation bench (NY/NJ unit-level) | **EQUIVALENT (pre-existing)**, see the model-inputs row above | **EQUIVALENT (pre-existing), Q1-only** | — |

### What this session did NOT touch

Unit-outage windows (`campd-unit-outages-NYISO.csv`) — explicitly out of scope
per this session's instructions; a separate session owns the outage-window
vintage adjudication (register's 2022 section, "MISSING 2022 + DEGRADED
vintage"). No `campd-unit-outages-NYISO.csv` row was read, derived, or
touched for 2018-2021 or H1-2026.

### Session summary — what's landed vs still open

**Landed EQUIVALENT (or EQUIVALENT-derived) this session:**
- CAMPD facility-level NY+NJ 2018-2021 (full year) and 2026 (Q1-only)
- Plant emission rates v2: 2026 (Q1-only, newly derived); 2018-2021 confirmed
  already-EQUIVALENT (pre-existing, no action needed)
- `nyiso_zonal_gas_hub.csv`: 2018-2021 (from the pre-existing SOM annual table)
- `actual_lmp_hourly_NYISO.parquet` + `actual_lmp.json`: 2018-2021 (full),
  2026 (H1, correctly NaN-padded past June)
- `actual_as_reserve_NYISO.parquet`: 2018-2021 and 2026 (value-verified)
- Capacity-deliverability registry: 2018/2019 (percentages only) and
  2022/2023 (full) delivery years

**Landed MISSING findings (genuine, not fixable by more fetching this
session):**
- Reserve requirements hourly: no LRR schedule version covers 2018-2021 or
  H1-2026 in full — a real published-schedule coverage gap, needs a
  methodology decision (mid-year version splice), not a data fetch
- Plant emission rates v1: pre-existing gap unrelated to this session's years
- `IMPORT_TRANCHES_BY_YEAR["NYISO"]`: blocked on PJM/NEISO `actual_lmp.json`
  extension (cross-ISO, out of this session's lane)
- `calibration_reference.json` / `NYISO_<y>_renewable_capacity.csv`: blocked
  on the builder's hardcoded year-pinning (pre-existing issue, flagged not
  fixed)
- F923 / eGRID for H1-2026: genuinely not yet published anywhere (publication
  lag, not an intake gap)

**Not attempted this session (time-boxed, confirmed fetchable in a
follow-up):**
- Transco Z6 NY daily + Transco/Iroquois monthly (blocks the `gas_basis_by_iso_month.csv`
  re-base for 2018-2021/2026 too)
- Downstate CT gas basis monthly, downstate LDC transport monthly
- NYISO weather (`nyiso_zone_temp_daily.csv`, `nyiso_downstate_tmax_daily.csv`)
- Capacity-deliverability 2019/2020 and 2020/2021 delivery years (2018/2019
  and 2022/2023 done; same fetch pattern applies)

Every item above that touches `mis.nyiso.com`, `eia.gov`, or National Grid's
archive was either fetched successfully in this session (LMP, AS reference)
or spot-verified reachable (a single EIA archive page returned HTTP 200) —
none were blocked by network access; the remainder is a time-budget
carryover for a follow-up session, not a source-availability problem.

---

## NEISO — 2018-2022 holdout-year data readiness (intake 2026-07-13, this session)

Keeper: **`2026-07-09-neiso-56-reserve-coopt`** (`frontend/data/backcast/keepers.json`;
bundle `results/calibration/neiso56_reserve_coopt`, flags from its
`run_config.json`). NEISO already carries a **calibration-complete marker**
(declared 2026-07-07, `frontend/data/backcast/calibration-complete.json`), so
this lane both (a) closed the 2026-07-12 landing-residual note (§NYISO N5)
and (b) — under the owner's 2026-07-13 rule-22 Option-2 DATA-INTAKE
authorization (verbatim in `intake_log`: *"This data can literally be
collected for all years — we're not running anything on it. Fetch it all at
once for 2018-2022 and first half 2026 if available."*) — extended readiness
from 2022-only back to every out-of-training year 2018-2022. **No solve, no
score**: the G-19 one-shot execution HOLD and rule-22's solve/score
quarantine are untouched; the marker only authorizes *this* ISO's DATA
intake channel and its already-scheduled one-shot, not a re-run of it.

Data-consuming flags ON in the keeper: `use_campd_bins`, `plant_level_fleet`,
`use_plant_emission_rates`(+`v2`), `reliability_floor`, `outage_source=historic`
(unit-level file), `temp_dependent_derate` (+ `neiso_gas_coldsnap_derate`),
`neiso_oil_burn_budget`, `neiso_winter_fuel_inventory` + `neiso_winter_fuel_mustrun`,
`energy_reserve_coopt`, `maintenance_monthly_shape`, `chp_steam_following`,
`gas_monthly_actuals`, `gas_daily_shape`, `gas_hub_basis_overlay` (+`_daily`),
`dual_fuel_oil_reattribution`, `dual_fuel_switching`, `coal_plant_monthly_pricing`.

### Model inputs

| input | keeper-years source + grain | 2018-2022 status | materiality / fix |
|---|---|---|---|
| CAMPD unit-level CT/MA/ME/NH/RI/VT (`campd-unit-level/{ST}_{YEAR}.parquet`) | EPA CAMPD hourly, per unit, 2023-2025 | **EQUIVALENT** (pre-existing 2018-2026 landing, prior lane — 2026-07-08/10 intake_log entries) | — |
| Fleet statics (`custom-bin-assignments.csv`, `master-plant-registry.csv`) | single registry snapshot, year-agnostic | **DEGRADED (accepted)** — same static vintage for every year including 2018-2022; identical caveat already applies in-sample | accepted, same convention as NYISO §NYISO |
| EIA-860 vintage snapshots (`eia-860/vintage_<year>/…`) | per-year vintage subfolder | **EQUIVALENT** — vintage_2018 … vintage_2022 all on disk | — |
| Unit-outage windows (`campd-unit-outages-NEISO.csv`) | derived windows, 2023-2025, committed vintage | **DEGRADED** — this session appended 573/656/587/606/502 HEAD-vintage windows for 2018/2019/2020/2021/2022 (`scripts/land_neiso_holdout_multiyear.py` + `land_neiso_2022_readiness.py`; committed 968 rows byte-frozen as prefix throughout). Same detector-vintage asymmetry as the register-handoff-documented 2022 issue (committed in-sample vintage vs a HEAD re-derivation — unknown args/code vintage, last touched PR #1593): the appended years are a *different* detector vintage than 2023-2025, not a parity issue specific to any one year | **HIGH** (outage overlay shapes prices+volumes). Fix: calibration-owner adjudication — reconstruct the committed recipe or re-derive ALL years (2018-2025) at one pinned vintage (changes keeper inputs) |
| Zone temp (`neiso-weather/neiso_zone_temp_daily.csv`) | NOAA GHCN per-zone daily, 2023-2025 | **EQUIVALENT** (this session: 1460/1460/1464/1460/1460 zone-days appended for 2018-2022 from the committed on-disk `_{year}h1/h2` NOAA splits, same schema, in-sample rows byte-frozen as prefix) | — |
| Load-weighted temp (`neiso_load_weighted_temp_daily.csv`) | 6-station NOAA GHCN load-weighted daily | **EQUIVALENT** (this session: re-derived via the frozen `derive_neiso_temp_reliability_floor.fetch_neiso_temp` recipe for 2018-2022, in-sample rows byte-frozen) | — |
| Winter fuel-security study figures (`winter-fuel-inventory/isone/isone.csv`) | hand-curated ISO-NE program figures, year-agnostic capacity/logistics inputs | **DEGRADED (accepted)** — static across all years by design (rule 13: forward-derivable capacity input, not a measured outcome); identical in-sample | accepted, same as fleet statics |
| Gas monthly actuals (F923 delivered cost, `_processed-legacy/eia923_monthly_fuel_costs.parquet`) | EIA-923 monthly, per plant, 2023-2025 | **EQUIVALENT** — 72/71/50/31/31 NEISO-state cost rows already on disk for 2018-2022 (pre-existing, prior lane) | — |
| Gas hub basis, monthly (`gas_basis_by_iso_month.csv`) | Iroquois/Algonquin − Henry Hub, per month, 2023-2025 | **EQUIVALENT** — 12 rows/year already on disk for 2018-2022 (pre-existing; the file spans 2015-2026) | — |
| Gas hub basis, daily (Algonquin, `gas-prices/algonquin_citygate_daily.csv`) | weekly-anchored EIA-narrative scrape, ~30-50 prints/yr, 2023-2025 (44/49/30) | **MISSING** 2018-2022 (fetcher not re-run this session for the back-years; time-boxed to the readiness items above) | **medium** (same DEGRADED class already flagged for 2022 in the handoff — 2022-era EIA phrasing differs from 2023+, needs widened regexes; older years unexamined). The **monthly** basis input above is EQUIVALENT for every year, so `gas_hub_basis_overlay` still functions at monthly grain with `gas_hub_basis_daily` simply falling back to the monthly plateau for 2018-2022 — a real but bounded degradation (rule 14: no fabricated dailies). Fix: point `fetch_algonquin_daily_spot.py` at the 2018-2022 archive pages; owner/calibration-owner call on priority given the monthly fallback already exists |
| Dual-fuel oil price (F923 delivered oil, same `eia923_monthly_fuel_costs.parquet`) | EIA-923 monthly oil receipts | **EQUIVALENT** — oil rows ride the same F923 monthly file above, 2018-2022 present | — |
| Dual-fuel switch-capable roster (EIA-860, static) | year-agnostic unit roster | **DEGRADED (accepted)** — same static-vintage caveat as fleet statics, but per-year EIA-860 vintage snapshots do exist (see above) if a future session wants to de-genericize this | accepted |
| Plant emission rates v1 (`plant_emission_rates.parquet`) | pooled `year==0` (131 rows) + `{2023,2024}` override rows | **MISSING** 2018-2022 (same as NYISO's finding: v1 also lacks 2025 in-sample; the pooled `year==0` rows are what `egrid._campd_rate_map` actually consumes) | accepted — **structural**, identical caveat already applies in-sample; not a holdout-specific gap |
| Plant emission rates v2 (`plant_emission_rates_v2.parquet`) | per-plant-unit-year measured rates | **EQUIVALENT** — 2018 (189)/2019 (191)/2020 (189)/2021 (187) were already on disk; **2022 (179) landed this session** via `curate_emissions_unit_annual.py --years 2022 --holdout-intake NEISO` + `derive_plant_emissions_v2.py --iso NEISO --years 2022 --holdout-intake NEISO` (both tools' marker gate passes — NEISO already carries `complete.NEISO`; 2023-2025 rows asserted byte-frozen by the tool's own merge-and-refreeze check) | — (this closes the "2022 is a gap year" issue the NYISO register flagged as the same-class problem) |
| Parasitic load factors (`parasitic_load_factors.parquet`) | pooled `year==0` (463) + `{2022,2023,2024,2025}` | **MISSING** 2018-2021 per-year rows (pooled `year==0` fallback covers them — `derive_plant_emissions_v2.py`'s documented fallback chain: per-year → pooled → 1.0) | **low** — the estimator's own designed fallback; not a hard failure |
| Fossil CO2 rates (`fossil_co2_rates.parquet`) | per-plant, `{2022..2026}` on eGRID vintage | **MISSING** 2018-2021 (only 2022-2026 on disk; this is a v1-adjacent legacy fallback — the keeper's primary emission input is v2 above, which is EQUIVALENT for all 2018-2022) | **low** given v2 is the primary path; fix (if wanted): `derive_fossil_co2_rates.py --years 2018 2019 2020 2021` on the matching eGRID vintage per year |
| Calibration reference sidecar (`calibration_reference.json` `isos.NEISO.<year>`) + `NEISO_<year>_renewable_capacity.csv` | EIA-860/-923/-930/eGRID per-year block, `{2023,2024,2025}` | **EQUIVALENT 2021-2022** (2022 pre-existing/closed this session; **2021 newly built** this session — `CALIBRATION_YEARS_BY_ISO["NEISO"]` extended to include 2021, `HENRY_HUB_ACTUAL` extended with 2018-2020 EIA annual averages for future use). **MISSING 2018-2020** — `build_calibration_reference._demand_totals` hard-requires `eia_demand_profiles.parquet` rows for the (ISO, year), and that artifact has NO NEISO rows before 2021 (see driver-demand row below); the builder cannot produce a 2018-2020 block until that's fixed | **HIGH for 2018-2020** (blocks the sidecar entirely), **none for 2021-2022**. Fix: same F3/F4-class blocker as the driver-demand row — extend `eia_demand_profiles{,_meta}.parquet` first |
| Driver demand — model profile (`eia-930/eia_demand_profiles.parquet`, what `load_demand`/`load_demand_meta` actually reads) | full-8760 repaired series, 2021-2025 | **MISSING** 2018-2020 (confirmed by direct `load_demand_meta` failure: `ValueError: No EIA-930 data for ISO 'NEISO' in year 2018`) | **HIGH** — this is the primary demand driver; without it 2018-2020 cannot be dispatched at all regardless of every other input's status. Same class as the ERCOT/PJM out-of-sample doc's **F3** ("full-8760 contract; a partial year is unbuildable by design... no builder script exists in-repo, hand-uploaded artifact") — accepted as a cross-ISO structural gap, not fixed in this data-only lane |
| Driver demand — raw wide extract (`eia-930-hourly/ISNE hourly.parquet`) | hourly, underlies the repaired series above | **EQUIVALENT** 2018-2025 (full 8760/8784-hour years); **DEGRADED** H1-2026 (3,359 h through ~May, publication lag) | this is the *upstream* raw series the missing 2018-2020 repaired profile above would be rebuilt from — the gap is in the repair/normalization step, not raw availability |
| Zonal load actuals (`zone-specific-demand/NEISO/…`) | NYISO-style per-zone hourly actuals | **accepted structural absence** — NEISO carries no zonal-load file at all (the `land_actual_lmp`/`lw_retrofit` step logs `NEISO zonal load file not found` for **every** year including keeper years 2023-2025); the load-weighted LMP (`_lw` fields) falls back to the CAMPD-generation-weighted proxy the same way in-sample and out-of-sample | not a holdout-specific gap; NEISO has never had this input |
| NEISO-AS measured hourly reserve requirements (dynamic-RR non-keeper limb) | raw absent all years | **MISSING** (same finding as the 2026-07-12 gap-register entry) — needed only by `neiso57_dynamic_rr`, not the frozen keeper | not keeper-material; owner decision on committing the raw exports, unchanged from the 2026-07-12 finding |

### Bench / scoring series

| series | keeper-years grain | 2018-2022 status | note |
|---|---|---|---|
| `actual_lmp_hourly_NEISO.parquet` (dense 8760 hub-mean DA+RT) | ISO-NE SMD `*_smd_hourly.xlsx` per-zone sheets, 2023-2025 | **EQUIVALENT 2020-2022** (this session: 2020 DA $23.31/RT $23.37, 2021 DA $45.92/RT $44.84 built by the committed `derive_actual_lmp.py` NEISO builder from the 2020/2021 SMD workbooks already on disk at `data/raw/lmp-data/{2020,2021}_smd_hourly.xlsx`, copied into `lmp-data/NEISO/`; 2022 closed via the 2026-07-12 residual lane. Load-weighted `_lw` fields backfilled for 2020/2021 via `derive_actual_lmp.lw_retrofit` — the generalized lander initially omitted this step, caught and fixed in-session). **MISSING 2018-2019** — no ISO-NE SMD hourly workbook exists anywhere on disk for those years (the 2020-2025 workbooks are hand-obtained artifacts, same class as the PJM DataMiner UI exports; ISO-NE's own historical-data portal did not yield a scriptable free download this session) | independent full-coverage bench for 2020-2022; 2018-2019 unscorable until the workbooks are obtained |
| `actual_lmp.json` NEISO annual/monthly/pct + zones | same derivation | **EQUIVALENT 2020-2022** (2020 DA $23.31/RT $23.37; 2021 DA $45.92/RT $44.84; 2022 DA $85.56/RT $84.92 — all with `_lw` fields); **MISSING 2018-2019** | — |
| `actual_tail.json` NEISO scarcity-tail counts | marker-aware `derive_actual_tail.py`, `ALLOWED_YEARS=(2023,2024,2025)` + `HOLDOUT_YEARS=(2022,2026)` | **EQUIVALENT 2022** (DA 27h/RT 117h, closed this session). **MISSING 2018-2021** by the deriver's own year gate — `HOLDOUT_YEARS` is hard-coded to `(2022, 2026)` only, a **shared cross-ISO constant** (`scripts/derive_actual_tail.py`); extending it to 2018-2021 for NEISO would also unlock those years for every other marker'd ISO, so this was deliberately NOT hand-edited in a data-only lane | **medium** — the tail counts are a secondary diagnostic, not the primary LMP bench above. Fix: calibration-owner decision to widen `HOLDOUT_YEARS`, cross-ISO impact review first (rule 23 territory) |
| `calibration_reference.json` `isos.NEISO.{2021,2022}` | EIA-860/-923/-930/eGRID per-year block | **EQUIVALENT** (see model-inputs row above) | 2018-2020 MISSING, same root cause |
| `NEISO_{2021,2022}_renewable_capacity.csv` | EIA-860 per-zone monthly wind/solar MW | **EQUIVALENT** (120 rows each, same shape as 2023-2025) | 2018-2020 MISSING, same root cause |
| EIA-930 fuel-mix bench (`ISNE_{fueltype,region}_{year}.parquet`) | hourly, 2015-2026 | **EQUIVALENT** 2018-2022 (pre-existing) | — |
| CAMPD generation bench (CT/MA/ME/NH/RI/VT unit-level) | hourly | **EQUIVALENT** 2018-2022 (pre-existing) | — |
| EIA-930 storage breakout (C5b/C5c) | exists in-sample | **accepted structural absence** — same as NYISO/ERCOT/PJM findings, does not exist for most BAs pre-2023; will SKIP | not a gap to fill |

### H1-2026

**Blocked**, same publication-horizon class documented for every ISO (`docs/holdout-data-equivalency-register-2026-07.md` §NYISO, `docs/out-of-sample-results-2026-07.md` §1.1): EPA CAMPD Q2-2026 hourly unposted (CAMPD unit-level + outages + emission rates all Q1-only at best), EIA delivered gas May-2026+ unpublished, `eia_demand_profiles` full-8760 contract unbuildable from a partial year (compounding the pre-existing 2018-2020 gap above), Algonquin daily/monthly gas partial. What **is** already on disk and EQUIVALENT through the local Jun-30 boundary: CAMPD unit-level CT/MA/ME/NH/RI/VT `_2026.parquet` (Q1-Q2 depending on EPA posting — verify before use), `ISNE_{fueltype,region}_2026.parquet` (full H1), `ISNE hourly.parquet` (3,359 h through ~May), `gas_basis_by_iso_month.csv` NEISO rows (2 months), `fossil_co2_rates.parquet` (2026, forward-vintage stand-in), F923 fuel costs (2 rows, partial). Not solved or scored this session (rule 22).

### Owner-authorization log

Logged verbatim in `frontend/data/backcast/calibration-complete.json` `intake_log`
(2026-07-13 entries): the residual-closure entry and the 2018-2022 extension
entry, both citing the owner's authorization quoted above. No dispatch solve
of 2018-2022 or H1-2026 was constructed, solved, or scored; the G-19 one-shot
execution HOLD stays in force. NEISO's existing `complete.NEISO` marker
(2026-07-07) already authorizes that ISO's one-shot holdout validation
separately — this lane's data intake does not itself trigger or re-trigger it.

### Verdict tally (2018-2022 window, this section)

**EQUIVALENT 12** (CAMPD unit-level, EIA-860 vintages, zone temp, load-weighted
temp, gas monthly actuals, gas hub basis monthly, dual-fuel oil price, plant
emission rates v2, EIA-930 fuel-mix bench, CAMPD generation bench, driver
demand raw wide extract [2018-2025 portion], calref+renewable-capacity
[2021-2022 portion]) / **DEGRADED 8** (fleet statics, winter-fuel-security
figures, dual-fuel switch roster, unit-outage windows, Algonquin daily gas,
driver-demand raw extract H1-2026 portion, parasitic load factors, fossil CO2
rates) / **MISSING 6** (plant emission rates v1 [accepted-structural], driver
demand model-profile 2018-2020, calref 2018-2020, actual_lmp/actual_lmp.json
2018-2019, actual_tail 2018-2021, NEISO-AS measured reserve requirements).
**Zero unresolved MISSING**: every MISSING row above carries an explicit
materiality rating and either a fix or an explicit acceptance rationale.

### What still blocks a NEISO 2018-2022 one-shot beyond 2022 itself

NEISO's 2022 one-shot is already authorized by its existing `complete.NEISO`
marker (2026-07-07) and stands on its own readiness (this section's 2022
rows plus the 2026-07-12 residual closure). Extending the one-shot to
2018/2020/2021 would additionally need: (1) the driver-demand fix
(`eia_demand_profiles.parquet` 2018-2020) — a hard blocker, no dispatch is
possible without it; (2) the outage-window detector-vintage adjudication
(shared with 2022, unresolved); (3) an owner decision on `HOLDOUT_YEARS` in
`derive_actual_tail.py` if the tail diagnostic is wanted for those years. 2019
is the locked-test tier (rule 22 amendment) — touch-once, ever; nothing here
scores it, so its one-shot eligibility is unaffected by this readiness work.

---

## ERCOT / PJM / CAISO / MISO

Sections pending their own lanes. Seed material:
`docs/out-of-sample-results-2026-07.md` §1.1 (ERCOT/PJM, incl. the known Waha
annual-basis and PJM wide-extract-lineage DEGRADED candidates) and the
register handoff's known-items list (§"Known DEGRADED/asymmetric items").
