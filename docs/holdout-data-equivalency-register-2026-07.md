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

> **Coverage baseline 2026-07-31:** the cross-ISO availability audit
> `docs/iso-2022-holdout-data-availability-audit-2026-07.md` supersedes this
> matrix's coverage claims for ERCOT/PJM/CAISO/MISO (keeper-flag-grounded 2022
> parity matrix + 2018–2021 census, per-family row counts). The per-input
> equivalency GRADING (source/grain/recipe parity + owner sign-off) for those
> four lanes remains pending **except PJM, graded in §PJM below (2026-07-31)**;
> the audit doc is the seed for the other three. Corrections that section makes
> to the audit: the audit's PJM "AS reserve series 2022 (partial file only)"
> row graded a file the keeper does not read (§PJM, N-P1 / the `as_up_mw` row),
> and its §5.6 request to spot-check PJM's 2018–2022 LMP clock lineage is
> answered CLEAN.

| ISO | 2022 | H1-2026 | Register section |
|---|---|---|---|
| ERCOT | intaken 2026-07-04 (§1.1); **coverage-audited 2026-07-31: GAPPED** (DAM-availability family, HSL, v2 rates, LMP bench all missing 2022 — audit doc §3.1); equivalency grading pending | intaken, publication-blocked tail (CAMPD Q2+, gas May+) | pending (seed: audit doc §3.1) |
| PJM | **§PJM below** (2026-07-31 intake + grading) — 2022 READY on data: interface limits, tie interchange, AS series, short-window outages and the 930 interchange all landed at parity; LMP bench clock-lineage CLEAN (no re-derive owed); `actual_tail` 2022 emitted. Residual: 2 recipe-freeze adjudications + the freeze | **§PJM below** — raws landed (transfer/interchange/AS/hub-LMP, all `_partial`-suffixed); locked tier, not built or scored | **§PJM below** |
| CAISO | **§CAISO below** — EQUIVALENT 17 / DEGRADED 6 / MISSING 12 (2026-07-31 intake, 2018-2022 + H1-2026). Much of the audit doc's §3.2 queue is now CLOSED (wide-hourly hole, HSL 2022, MIC+LCR registry, gas, interchange, AS_REQ, calref) — but the **LMP bench is SOURCE-BLOCKED, not merely missing**: OASIS retention now stops at 2023-04-19 (N-CA-1) | **§CAISO below** — LMP bench BUILT (DA $20.22 / RT $19.59), 930 + CAMPD + AS_REQ + interchange landed; gas/curtailment/emissions publication- or discontinuation-blocked | **§CAISO below** |
| MISO | **no longer zero-intake** (same waves + 2022 hub-LMP raws on disk); **coverage-audited 2026-07-31: GAPPED, LMP bench derivable from committed raws** (audit doc §3.4) | blocked + partial intake | pending (seed: audit doc §3.4) |
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
| CAMPD facility-level NY + NJ | EPA facility bulk vintage (2023–2025) | **EQUIVALENT-derived** (this session: derived from the landed unit-level files by `scripts/data/derive_campd_facility_from_units.py`; recipe **proven cell-exact on 5 of 6 committed state-years**, and on NY-2025 exact except a known in-sample lineage drift — see note N1) | derive-time input only; persefoni registry joined from the 2023 sibling (sparse attribute) |
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
  `scripts/data/derive_campd_facility_from_units.py`; every other committed
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
  `scripts/archive/land_neiso_2022_readiness.py` the same day — the residuals resolve
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

> **Clock caveat (added 2026-07-15, all-ISO scoring-clock fix):** the
> out-of-training `actual_lmp_hourly_*.parquet` blocks registered here (NYISO
> 2018–2022 + 2026-H1; NEISO 2020–2022) were built on the OLD prevailing-clock
> indexing and were preserved byte-frozen when the 2023–2025 rows were rebuilt
> chronologically (2026-07-15 calibration-log entry). Before any authorized
> validation-year scoring, these blocks must be re-derived with the fixed
> `derive_actual_lmp.py` (raws for NYISO 2022 RT and NEISO 2020–2022 workbooks
> are committed; NYISO 2018–2021/2026 re-fetch from `mis.nyiso.com`) — an
> hourly-paired score against the frozen blocks would re-import the ±1 h DST
> pairing artifact.

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
| Unit-outage windows (`campd-unit-outages-NEISO.csv`) | derived windows, 2023-2025, committed vintage | **DEGRADED** — this session appended 573/656/587/606/502 HEAD-vintage windows for 2018/2019/2020/2021/2022 (`scripts/archive/land_neiso_holdout_multiyear.py` + `land_neiso_2022_readiness.py`; committed 968 rows byte-frozen as prefix throughout). Same detector-vintage asymmetry as the register-handoff-documented 2022 issue (committed in-sample vintage vs a HEAD re-derivation — unknown args/code vintage, last touched PR #1593): the appended years are a *different* detector vintage than 2023-2025, not a parity issue specific to any one year | **HIGH** (outage overlay shapes prices+volumes). Fix: calibration-owner adjudication — reconstruct the committed recipe or re-derive ALL years (2018-2025) at one pinned vintage (changes keeper inputs) |
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
| `actual_tail.json` NEISO scarcity-tail counts | marker-aware `derive_actual_tail.py`, `ALLOWED_YEARS=(2023,2024,2025)` + `HOLDOUT_YEARS=(2022,2026)` | **EQUIVALENT 2022** (DA 27h/RT 117h, closed this session). **MISSING 2018-2021** by the deriver's own year gate — `HOLDOUT_YEARS` is hard-coded to `(2022, 2026)` only, a **shared cross-ISO constant** (`scripts/data/derive_actual_tail.py`); extending it to 2018-2021 for NEISO would also unlock those years for every other marker'd ISO, so this was deliberately NOT hand-edited in a data-only lane | **medium** — the tail counts are a secondary diagnostic, not the primary LMP bench above. Fix: calibration-owner decision to widen `HOLDOUT_YEARS`, cross-ISO impact review first (rule 23 territory) |
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

## PJM — 2022 validation-holdout + 2018-2021 ladder + H1-2026 (intake 2026-07-31, this session)

Keeper: **`2026-07-30-pjm-140-rampenv`** (`frontend/data/backcast/keepers/PJM.json`;
bundle `results/calibration/pjm140_rampenv_B`, flags from its `run_config.json`).
Marker: `complete.PJM` declared 2026-07-31 — **validation tier only (2022)**;
PJM is absent from `final`, so 2019 and H1-2026 stay locked, and the owner's
authorization for THIS session states that 2018/2020/2021 are likewise outside
the validation grant (the backward ladder rungs are separate owner decisions).
The **holdout spend freeze is ACTIVE** and outranks the marker. Accordingly
**nothing here was solved or scored** — this section grades DATA READINESS only
(rule 22 channel 1: intake under session-logged owner authorization, validated
no-LP).

Data-consuming flags ON in the keeper: `pjm_measured_interface_limits`,
`pjm_seam_measured_ladder`, `pjm_reserve_supply_cap`, `pjm_reserve_pergen`,
`pjm_east_interface_cut`, `pjm_external_net_position_cut`, `pjm_seam_flow_limit`,
`pjm_seam_export_limit`, `pjm_congestion`, `pjm_zonal_loss_surface`,
`pjm_zonal_gas_basis`, `pjm_da_virtual_bids`, `pjm_offer_midcurve_conditional`,
`unit_outage_short_windows`, `measured_ct_heat_rates`,
`measured_ramp_capability`, `ramp_limits`, `use_campd_bins`,
`plant_level_fleet`, `use_plant_emission_rates(+v2)`, `coal_plant_monthly_pricing`,
`gas_plant_monthly_fuel_pricing`, `gas_monthly_actuals`, `gas_daily_shape`,
`energy_reserve_coopt`, `reliability_floor`, `state_carbon_pricing`,
`outage_source=historic`, `reference_price_interface`.
OFF (files NOT consumed, census only): `pjm_dam_availability`,
`unit_partial_outage_windows`, `unit_outage_maxgen_events`,
`capacity_deliverability_limits`, `nuclear_unit_availability`,
`historic_outage_overlay`.

### Model inputs

| input | keeper-years source + grain | 2022 | 2018-2021 | H1-2026 | materiality / fix |
|---|---|---|---|---|---|
| Measured interface transfer limits (`iso-specific-transmission/PJM_<y>_transfer_limits_and_flows.csv` → clean `transfer-interface-limits`) — `pjm_measured_interface_limits` | PJM DataMiner2 `transfer_limits_and_flows`, hourly per interface | **EQUIVALENT** (this session) | **EQUIVALENT** 2018-2021 (this session) | **EQUIVALENT-partial** (`PJM_2026_..._partial.csv`, Jan 1-Jun 30, 43,430 rows) | was the audit's §3.3 **HIGH** gap. Same feed, same public key, byte-schema identical to the committed 2023-2025 drops (7 columns, 87,600 rows/yr; 87,840 in leap 2020). Curated + loader-verified: `load_interface_hourly('PJM', y)` returns 87,600 rows / **10 interfaces / 8 mapped link series for EVERY year 2018-2025**, identical interface vocabulary 2022 vs 2023 |
| Tie-line interchange (`PJM_<y>_import_export_act_sch_interchange.csv`) — seam ladder flow source, `pjm_seam_flow_limit`/`_export_limit`, `eia_loader.pjm_net_interchange` | DataMiner2 `act_sch_interchange`, hourly per tie | **EQUIVALENT** (this session, 192,718 rows) | **EQUIVALENT** (2018 200,730 / 2019 192,708 / 2020 193,222 / 2021 192,710) | **EQUIVALENT-partial** (`_partial.csv`, 91,201 rows) | 8-column schema identical to committed. 2018's higher row count is a wider tie roster, not duplication |
| PJM-AS RT reserve market results (`PJM-AS/reserve_market_results_<y>.parquet`) — **the keeper's reserve requirement source** | DataMiner2 RT Reserve Market Results | **EQUIVALENT** | **EQUIVALENT** | **EQUIVALENT-partial** (312,764 rows) | see N-P1: full schema parity restored this session (`_dt_ept`) |
| **Derived reserve-withholding / requirement series (`PJM-AS/pjm_<y>_as_up_mw.parquet`)** — what `pjm_reserve_pergen` + the MAD/sync families ACTUALLY read | `build_pjm_as_withholding.py` from the RT feed; 8760 rows × `pr_req_mw`, `mad_pr_req_mw`, `sr_req_mw`, `mad_sr_req_mw` | **EQUIVALENT — already on disk** | **EQUIVALENT — already on disk** | **MISSING, by design** | **The audit's "PJM-AS reserve series 2022 (partial file only)" row graded the wrong file.** The keeper never reads `da_reserve_market_results_*`; it reads this derived RT series, which is dense 8760 with all four requirement columns non-zero for **every year 2018-2025**. Re-derived from the re-fetched source this session and asserted **value-identical** (0 differing cells, all columns, all 5 years). 2026 is absent because the builder refuses a partial year (`_partial` suffix convention) — correct, not a gap to fill |
| PJM-AS DA reserve market results (`da_reserve_market_results_*`) | DataMiner2 DA | **EQUIVALENT-partial** (Oct 1-Dec 31 only) | **structurally ABSENT 2018-2021** | **EQUIVALENT-partial** | **NOT keeper-consumed** (graded per the owner's request). The DA feed's `firstAvailable` is 2022-10-01 — PJM's Reserve Price Formation redesign, a genuine "does not exist", never padded. The 2022 file is right-sized at 11,025 rows for its 3-month window |
| PJM-AS AS product prices (`ancillary_services_*`, `da_ancillary_services_*`) | DataMiner2 RT/DA AS product LMPs | **EQUIVALENT** (RT 68,267 rows; DA partial 11,050) | **EQUIVALENT** RT 2018-2021; DA structurally absent | **EQUIVALENT-partial** both | validation-side only (rule 13 — reserve prices are never an input). Landed this session by fixing a fetcher bug: see N-P1 |
| Short-window unit outages (`campd-unit-outages-short-PJM.csv`) — `unit_outage_short_windows` | `derive_campd_unit_outages.py --short-windows`, per-unit coal windows < 5 d | **EQUIVALENT-derived** (134 windows) | **EQUIVALENT-derived** (2018 167 / 2019 113 / 2020 87 / 2021 125) | **EQUIVALENT-partial** (23 windows, CAMPD Q1-only) | derived this session from on-disk CAMPD; merged append-only with the 285 committed 2023-2025 rows asserted **byte-identical**. Overlay loader exercised (no LP) for every year 2018-2026 — resolves 14-34 (zone,class) derate keys per year. **Detector-vintage caveat: see N-P2** |
| Partial-outage derates (`campd-partial-outages-PJM.csv`) | `derive_campd_unit_outages.py --partial-windows` | **NOT PRODUCED** | **NOT PRODUCED** | **NOT PRODUCED** | `unit_partial_outage_windows=False` in the keeper — census only. The producer is **inert at HEAD for PJM in EVERY year**: it emits 0 plateau windows for 2018-2022, 2026 *and for the committed 2023-2025 span* (which carries 76 rows). Not a year-specific gap — a producer/vintage non-reproduction, recorded in N-P2. The committed file was NOT overwritten |
| `measured_ct_heat_rates` (`_processed-legacy/campd_ct_heat_rates_PJM.csv`) | CAMPD loaded heat rate, per plant | **n/a — no year dimension** | **n/a** | **n/a** | **VERIFIED NOT PER-YEAR** (the owner's step-4 question): one pooled row per `plant_code`, `years == "2023-2024-2025"`, loader keys on `plant_code` alone. Nothing to derive per year. Vintage exposure quantified: a 2018-2022-pooled re-derive finds 70 ok plants vs the artifact's 71, **69 shared**; exactly **1 plant** ran 2018-2022 and is absent from the artifact (falls back to its eGRID rate — the documented per-plant fallback). Shared-plant rates agree tightly: median \|Δ\| 0.183, mean 11.967 vs 11.986 MMBtu/MWh. **DEGRADED (accepted)** — see N-P3 |
| `measured_ramp_capability` (clean `ramp-capability`) | EIA-860 fast-start + CAMPD 1-h envelope, per plant | **n/a — no year dimension** | **n/a** | **n/a** | **VERIFIED NOT PER-YEAR**: written with `year=None`, no `--years` CLI. `POOLED_VINTAGES = (2023, 2024, 2025)` is an explicit rule-22 quarantine constant ("2022 and H1-2026 are the designated holdouts … excluded by construction"). **DEGRADED (accepted)** + an owner adjudication — see N-P3. Separately: the clean partition is gitignored and absent from a fresh container; `load_measured_ramp_capability` RAISES rather than degrading (pjm-119), so it must be regenerated before ANY solve — an in-sample fact, not a holdout gap |
| EIA-930 per-DIBA interchange (`eia-930-interchange/PJM interchange hourly.parquet`) | EIA-930 `TI` family, 7 DIBAs, hourly | **EQUIVALENT** (60,984 rows, 99.5 %) | **EQUIVALENT 2019-2021** (99.7 / 99.4 / **95.5 %**); **2018 MISSING (source floor)** | **EQUIVALENT-partial** (28,930 rows to hour-ending 2026-07-01, 95.1 %) | committed 2023-01-01 01:00 .. 2026-01-01 00:00 block asserted content-identical across the merge. **2018 is a publication floor, not a fetch gap**: the EIA API v2 `interchange-data` route returns `total: 0` for PJM in every 2018 month probed (01/04/07/08/09/10/12), first rows 2019-01 — recorded rather than padded. 2021's dip is a hole in EIA's own submission (CPLE complete at 8,759 h; the other six DIBAs each cut to 8,303 h) — same class as the committed 2025 block's 97.0 % |
| Demand (`eia-930/eia_demand_profiles.parquet`, `hrl_load_metered`) | EIA-930 8760 + PJM metered | **EQUIVALENT** (pre-existing) | **MISSING 2018-2020** (cross-ISO F3 blocker, audit §4.1); 2021 ✓ | blocked (publication horizon) | the 2018-2020 demand-profile gap is a **hard blocker for every ISO** — no dispatch is possible without it. Untouched here |
| CAMPD unit-level, unit-outage windows, F923, monthly gas basis, 8-zone gas hub, weather, EIA-860 vintage, eGRID | per audit §3.3 / §4.2 | **EQUIVALENT** (pre-existing) | **EQUIVALENT** (pre-existing) | CAMPD Q1-only; gas May+ unpublished | not touched this session |

### Bench / scoring series

| series | 2022 | 2018-2021 | H1-2026 | note |
|---|---|---|---|---|
| `actual_lmp_hourly_PJM.parquet` (scoring target) | **EQUIVALENT** | **EQUIVALENT** 2018-2021 | **raw landed, block not built** | **Clock lineage CLEAN — audit §5.6's spot-check request is answered definitively.** Every committed 2018-2025 row reproduces **bit-for-bit** from the current fixed-clock `derive_actual_lmp.py` (0 differing cells in rt and da, 0 NaNs, all 8 years), so no re-derive is owed and the in-sample rows are trivially frozen. Structural reason: PJM's DataMiner export carries a real `datetime_beginning_utc` column, so `_hub_mean_hourly` indexes the chronological calendar directly — PJM was never exposed to the prevailing-clock artifact that hit NYISO/NEISO. H1-2026: `lmp-data/PJM_2026_rt_da_monthly_lmps_partial.csv` (52,116 rows) landed this session; the parquet block is deliberately NOT built (locked tier, no `final` marker) |
| `actual_lmp.json` PJM | **EQUIVALENT** (2018-2025 pre-existing) | **EQUIVALENT** | not built | — |
| `actual_tail.json` PJM 2022 | **EMITTED this session** — DA 73 h / RT 92 h > $200, coverage 1.00 | not emitted (outside the grant) | not emitted (locked tier) | closes the audit's "(d) — marker now exists, auto-emits on next derive run". Required a tier fix first: see N-P4 |
| Seam-import ladder neighbour price (`actual_lmp_hourly_MISO.parquet`) — `pjm_seam_measured_ladder` / `reference_price_interface` | **CLOSED mid-session** | n/a | n/a | the audit's cross-ISO blocker ("closes for free once the MISO lane lands its LMP bench") **resolved while this session ran**: PR #3182 landed MISO's 2022 hub block on main (2026-07-31). It is **PARTIAL — rt 86.3 % / da 94.0 % coverage** on 8,760 rows, so the ladder's 2022 neighbour leg is a lower-coverage input than its 2023-2025 counterpart; grade it explicitly at recipe freeze. The ladder's own two inputs (PJM tie flows, PJM DA LMP) are now complete 2018-2022 |
| EIA-930 fuel-mix bench, CAMPD generation bench | **EQUIVALENT** | **EQUIVALENT** | partial | pre-existing |
| `calibration_reference.json` + `PJM_<y>_renewable_capacity.csv` | **EQUIVALENT** (pre-existing) | 2021 ✓; **MISSING 2018-2020** | blocked | same F3 demand-profile root as the driver row |

### Notes

- **N-P1 (fetcher bug found and fixed — the AS-price feeds were never
  machine-fetchable).** `fetch_pjm_as.py` sorted and filtered all four
  DataMiner2 feeds on `datetime_beginning_utc`. The two `*ancillary_services`
  feeds **reject that key with HTTP 400** — for every year probed including
  2023, a year already on disk — and `pjm_dataminer.fetch_page` maps 400 to
  "no data for this window", so the script reported five straight years as
  "not yet published" and wrote nothing. That is why those parquets were
  hand-pulled from the DataMiner UI. Fixed with a per-feed `filter_field`
  (`datetime_beginning_ept` for the two AS-price feeds); all five years plus
  both 2026 partials then landed. Two schema deltas surfaced in the same pass
  and were also fixed: machine-fetched files lacked the derived `_dt_ept`
  column that **all four** feeds' committed siblings carry — not cosmetic,
  `scripts/report_pjm_posture_gate.py:70` indexes `reserve_market_results` on
  it and would `KeyError` on the 2018-2022 files the 2026-07-10 session
  landed — and this container's pandas writes `large_string`/`timestamp[us]`
  where the committed files use `string`/`timestamp[ns]`, which breaks a
  multi-year `ds.dataset` schema unification. After the fix **all four feeds ×
  all years are at full column+dtype parity**. The re-fetch was verified
  non-destructive: rebuilding `pjm_<y>_as_up_mw.parquet` from the re-fetched
  source reproduced the baseline **value-identically**, and those derived
  files were then restored to avoid pure-encoding churn.
- **N-P2 (detector-vintage asymmetry in the CAMPD outage derives — reported,
  not papered over).** The owner's precondition was "re-prove committed years
  byte-identical first". It **fails**, in two different ways, and neither was
  resolved by overwriting in-sample data:
  (a) *Short windows.* Re-deriving 2023-2025 at HEAD gives **279 of the 285**
  committed windows, every shared row numerically identical (capacity,
  duration, unit-percent all exact) and **zero new** windows. The six that
  drop are short marginal spans at three plants (John S. Cooper ×3, Mount
  Storm, Mt. Carmel ×2), consistent with the in-merit (revealed-availability)
  filter's net-load percentile boundary moving. The extension was therefore
  merged **append-only**, with the committed rows byte-frozen, so the keeper's
  in-sample input is untouched and the asymmetry is a documented lineage note
  rather than a silent re-tune. Adjudication (re-derive all years at one
  vintage, which changes keeper inputs) is a calibration-owner call — the same
  disposition the register's NYISO §2022 outage row took.
  (b) *Partial windows.* `--partial-windows` emits **0 rows for PJM in every
  year**, in-sample included, against 76 committed rows. This is a whole-file
  non-reproduction, not a holdout gap. Materiality is low — the keeper has
  `unit_partial_outage_windows=False` — but it means the committed file has no
  reproducible provenance at HEAD.
- **N-P3 (year-agnostic measured artifacts — the step-4 answer, and one owner
  decision).** Neither `measured_ct_heat_rates` nor `measured_ramp_capability`
  is per-year, so "derive every missing year" is a no-op: there is nothing
  missing. Both are pooled 2023-2025 plant-level constants. Grading them
  **DEGRADED (accepted)** for an out-of-training solve rests on the same
  rationale as the register's "fleet statics year-agnostic (accepted)" row —
  a CT's loaded heat rate and a plant's demonstrated hourly ramp envelope are
  physical constants of the machine, both derives are frozen against residuals
  (rule 24 `[R-FROZEN-DERIVE]`), and the measured 2018-2022 vs 2023-2025 rate
  agreement above (0.16 % on the shared mean) supports it. **Owner decision
  deferred, deliberately:** `POOLED_VINTAGES` could now legally widen — the
  authorization this session carries is exactly the one its comment names as
  the blocker — but widening it would change the **in-sample** pooled envelope
  and therefore silently re-tune the 2023-2025 keeper. That is a calibration
  decision at recipe freeze, not a data-readiness action, so it was NOT taken
  here. It is the direct analogue of CAISO's measured-offer-surface vintage
  adjudication (§3.2).
- **N-P4 (rule-22 tier leak found and closed in `derive_actual_tail.py`).**
  The deriver was **tier-blind**: `_marker_isos()` read only the `complete`
  block, so any ISO holding the validation marker also unlocked **H1-2026**,
  a locked-test year whose `final` block is deliberately empty. This was not
  hypothetical — the committed `actual_tail.json` carried a **NYISO 2026 row**
  (DA 151 h / RT 86 h > $300 at 49.6 % coverage, i.e. the H1 window) emitted on
  a validation-only declaration. The deriver now reads
  `scripts/lib/holdout_policy` — the same tier map the other three rule-22
  gates use — so a year is emitted only when the ISO holds **that year's**
  tier marker. The run this session therefore **added PJM 2022** and
  **withdrew NYISO 2026**; no other ISO-year row changed value, and MISO's
  newly-landed 2022 bench is correctly not emitted (no marker). The
  considered-holdout set is deliberately held at `{2022, 2026}` rather than
  the full `VALIDATION_YEARS` ladder, so the fix closes a leak without opening
  2018/2020/2021 — which the owner's authorization explicitly places outside
  the current grant.
- **N-P5 (H1-2026 naming).** `fetch_pjm_transmission.py` gained an
  `--h1-2026` flag that hard-caps at Jun 30 and writes `_partial`-suffixed
  filenames, mirroring `fetch_pjm_as.py`. Every consumer resolves the plain
  `PJM_<year>_<feed>.csv` name directly, so the suffix makes a half-year file
  invisible to them rather than quietly wrong; `--years 2026` is refused
  outright. The interface-limits curator's glob (`PJM_*_transfer_limits_and_flows.csv`)
  correctly does not match the partial file.

### What still blocks a PJM 2022 one-shot

1. **The holdout spend freeze** (`holdout-freeze.json`, 2026-07-25, HELD
   2026-07-26) — outranks the marker; only the owner lifts it.
2. **G-19 sign-off** on this section.
3. **`data/clean` regeneration** before any solve: `ramp-capability` and
   `transfer-interface-limits` are gitignored, and both loaders RAISE rather
   than degrade (pjm-119). `transfer-interface-limits` was regenerated and
   verified for 2018-2025 this session; `ramp-capability` was not built.
4. **Two recipe-freeze adjudications** (neither a data gap): the N-P2 outage
   detector vintage, and the N-P3 pooled-vintage question.
5. **Not blocking, but grade it:** the MISO 2022 neighbour LMP that unblocks
   the seam ladder is PARTIAL (rt 86.3 % / da 94.0 %).

Nothing above applies to **2018-2021 or H1-2026**, which are outside the
current grant entirely — their data is now largely READY (this section), but
readiness is not authorization.

---

## CAISO — 2022 + 2018/2019/2020/2021 (validation ladder + locked 2019) + H1-2026 (locked-test edge) intake (2026-07-31, this session)

Keeper: **`2026-07-31-caiso146-ct-heat-rates`**
(`frontend/data/backcast/keepers/CAISO.json`; bundle
`results/calibration/caiso146_ctheatrate_B`, flags from its `run_config.json`).
CAISO holds **no calibration-complete marker of either tier**, and the
**holdout spend freeze** (`frontend/data/backcast/holdout-freeze.json`) is
active, so every year in this section is quarantined for solve/score/
registration regardless of its data grade. This lane is rule-22 **channel 1**
only — data intake under explicit, session-logged owner authorization, all
validation no-LP (byte-identity, row counts, loader resolvability, producer
re-derivation). **No dispatch was constructed, solved or scored for any year,
and nothing was registered on any dashboard.**

Owner authorization (verbatim, logged in `calibration-complete.json`
`intake_log`): *"I (the owner) explicitly authorize out-of-training data
intake for CAISO for ALL of 2018-2022 and H1-2026 in this session under
CLAUDE.md rule 22 (Option 2) — fetch each source's full year span at once. …
All validation is no-LP only. Do NOT solve, score, or register any
out-of-training year — CAISO has NO calibration-complete marker, the freeze
is in force, 2019 is locked-tier (intake fine, touch never). Data readiness
only."*

Data-consuming flags ON in the keeper (the materiality basis for every grade
below): `use_campd_bins`, `plant_level_fleet`, `use_plant_emission_rates`
(+`v2`), `outage_source=historic`, `reliability_floor`,
`capacity_deliverability_limits`, `caiso_ra_mustoffer` (+`_ra_startup_bridge`,
`_ra_bridge_decommit`, `_ra_bridge_startup_aware`, `_ra_startup_trajectory`),
`caiso_offer_surface_measured` + `caiso_offer_surface_conditional`,
`caiso_solar_endogenous_spill` + `caiso_solar_deliverability`,
`caiso_supply_consistent_demand`, `caiso_demand_clock_realign`,
`caiso_firm_import_{shape,selfschedule,envelope_clip}` +
`caiso_perhub_firm_base` + `caiso_per_hub_intertie`,
`caiso_corridor_flow_limit`, `caiso_citygate_{flow_date,spot_level}`,
gas stack (`gas_monthly_actuals`, `gas_daily_shape`, `gas_hub_basis_overlay`,
`gas_plant_monthly_fuel_pricing`, `coal_plant_monthly_pricing`),
`measured_ct_heat_rates`, `hydro_dispatch_envelope` + `hydro_min_flow_floor`,
`temp_dependent_derate`, `chp_steam_following`, `maintenance_monthly_shape`,
`state_carbon_pricing`, `storage_capacity_value`, `renewable_elcc_curves`,
`caiso_scarcity_pricing`.

### Model inputs

| input | keeper-years source + grain | 2018-2022 / H1-2026 status | materiality / fix |
|---|---|---|---|
| Hourly demand driver (`eia-930/eia_demand_profiles.parquet`) | EIA-930 repaired full-8760, 2021-2025 | **EQUIVALENT 2021-2022** (8760 rows each, pre-existing). **MISSING 2018-2020 and 2026** — the artifact has no CAISO rows outside 2021-2025 | **HIGH for 2018-2020**: without it `load_demand` hard-fails and those years cannot be dispatched at all, whatever every other row says. Same cross-ISO F3-class blocker already recorded for NEISO (hand-uploaded artifact, no in-repo builder); not fixed in a data-only lane |
| EIA-930 CISO wide hourly (`eia-930-hourly/CISO hourly.parquet`) | wide extract the loader filters by local year | **EQUIVALENT 2018-2022** (this session: the **2022 hole is CLOSED**, 9 rows → dense 8760, by `build_eia930_hourly_from_raw.py --ba CISO --merge-missing --merge-years 2018 … 2022 2026` from the already-landed API v2 long extracts; every one of the 65,711 pre-existing rows verified byte-identical). **DEGRADED H1-2026** (4,343 h through 2026-06-30, publication lag) | closes audit-doc §5.1. `NG: GEO` is null for 2022 — but it is null for **every** year including in-sample 2023/2024, so this is a standing taxonomy gap, not a holdout degradation |
| EIA-930 CISO long form (`eia-930/CISO_{region,fueltype}_<y>.parquet`) | API v2 tidy extracts | **EQUIVALENT 2018-2022 + 2026** (pre-existing; 2018 covers Jul-Dec only — see the HSL row) | — |
| Zonal/TAC load actuals (`zone-specific-demand/CAISO/CAISO_tac_load_hourly_<y>.csv`) | OASIS SLD_FCST ACTUAL, hourly per TAC | **EQUIVALENT 2018-2025** (pre-existing) | — |
| CAMPD unit-level CA (`campd-unit-level/CA_<y>.parquet`) | EPA CAMPD hourly per unit | **EQUIVALENT 2018-2026** (pre-existing) | — |
| Unit-outage windows (`campd-unit-outages-CAISO.csv`) | uniform 2026-07-24 all-ISO detector | **EQUIVALENT 2018-2026** (449/530/497/535/442 windows 2018-2022; 235 in 2026) — one detector vintage across every year, so the NYISO/NEISO vintage asymmetry does not apply here | the freeze's cross-ISO layup over-count still hangs over the whole family; that is the freeze's exit condition, not a CAISO gap |
| Renewable HSL / uncurtailed potential (`caiso-hsl/caiso_<y>_hsl_hourly.parquet`) | delivered EIA-930 + reported curtailment, 2019-2021 + 2023-2025 | **EQUIVALENT 2019-2022** — **2022 BUILT AND COMMITTED this session** once the wide-extract hole above was closed; the same run re-derived 2019/2020/2021/2023/2024/2025 **byte-identically**, so 2022 is the committed producer on the committed recipe. **MISSING 2018** (built, QA-failed, deliberately withheld) and **MISSING H1-2026** (source discontinued) | 2022 closes the audit-doc §3.2 "one hole in an otherwise 2019-2025 series". **2018**: 4,343 of 4,380 H1 hours have null `NG: WND`/`NG: SUN` (EIA-930 per-fuel reporting for CISO did not exist for H1-2018), so `eia_loader`'s `.interpolate().bfill().ffill()` fabricates a flat wind series — annual wind 24.87 TWh vs 15.9/14.9/18.3 in 2019-2021, `min = 18 MW`, `nonzero_frac = 1.000`. Committing it would put a fabricated series ahead of the delivered-profile fallback; the `eia_loader` imputation defect is the open issue. **2026**: CAISO stopped publishing the Production-and-Curtailments report 2025-06-01 (stated on its own library page) — a source discontinuation, not a fetch gap |
| Capacity-deliverability registry, MIC half (`capacity-deliverability/caiso/caiso.csv`, `branch_group` / `import_limit`) — read by the keeper's `capacity_deliverability_limits` | CAISO annual "Maximum RA Import Capability" filing, per branch group | **EQUIVALENT 2018-2022** (this session: 174 rows — 32/35/35/36/36 branch groups — transcribed by the new `scripts/data/curate_caiso_mic.py`, whose `--verify` reproduces the committed **2023, 2024 and 2025** rows value-for-value, 36/36/33) | closes the audit-doc §3.2 HIGH item for the half that actually fires in a backcast (MIC → `WECC_import`). Committed bytes frozen: the merge byte-appends and never rewrites |
| Capacity-deliverability registry, LCR half (`local_area` / `requirement`) | CAISO Local Capacity Technical Study, 10 local areas | **EQUIVALENT 2021-2022**, **DEGRADED 2018-2020** (this session: 50 rows via the new `scripts/data/curate_caiso_lcr.py`, `--verify` reproduces committed 2023-2025 exactly). The 2018/2019 reports publish Category B and Category C(with operating procedure) triplets and the 2020 report a Category B/C pair; only 2021+ carries the single post-TPL-001-4 `Capacity Needed` column the committed rows use | the transcription takes the **last numeric cell of each area row** — the most-severe-criterion total including deficiency — which is exactly what the 2021+ single column reports, and is asserted against 2023-2025. Pre-2021 rows carry `Category C total` in `source_page` so the criterion vintage is visible in the data itself |
| Capacity-deliverability, zone peak load + system PRM (`zone` / `peak_load`, `rto` / `system_requirement`) | LCT §3.2 "Total Zonal Resource Needs" (NP26/SP26 CEC load forecast) + CPUC minimum PRM | **EQUIVALENT 2020-2022** (6 zone rows + 3 PRM rows; zone values verified against committed 2023-2025). **MISSING 2018-2019** — the §3.2 zonal section postdates those reports | the PRM rows are a documented **source substitution**: committed 2023-2025 take 0.16/0.17/0.17 from a CPUC fact sheet because each study is published a year early and can predate a later CPUC decision; for 2018-2022 there is no such lag (15% throughout) and each study states it, so the study is cited |
| Capacity-deliverability, local-area peak load (`local_area` / `peak_load`) | 3 rows/yr (LA Basin, San Diego/IV, Greater Bay) | **MISSING 2018-2022** | LOW-MEDIUM. The committed rows' own citations (`Table 3.3-7 Load+Losses+Pumps`, `Table 3.3-29`) **do not resolve** in the reports they cite — Table 3.3-7 in the 2023 report is "Fulton LCR Sub-area Requirements" — so the extraction convention cannot be reproduced without a calibration-owner clarification. Flagged rather than guessed |
| Zonal gas hub (`caiso_zonal_gas_hub.csv`) | PG&E / SoCal Citygate weekly Wednesday prints, month-balanced annual basis | **EQUIVALENT 2020-2022** (15 rows this session; the derive re-produced committed 2023/2024/2025 **exactly** — 4.042/4.533, 0.875/0.336, 0.098/0.282 — before the back-years were written). **MISSING 2018-2019** | 2020-2022 coverage (44-48 weeks / 12 months) is at or better than the in-sample years' own (23-49 weeks). 2018-2019 fail at source: the older EIA weekly narrative carries almost no PG&E Citygate row (2 prints in 2018, 7 in 2019 against ~50/yr later), so the NP15/ZP26 basis is not derivable at the committed grain |
| Daily citygate composite (`gas-prices/caiso_citygate_daily.csv`) — `gas_daily_shape` / `caiso_citygate_spot_level` | EIA NG Weekly Update "Cal. Comp. Avg", ~224-232 prints/yr | **EQUIVALENT 2018-2022** (this session: 224/213/213/231/233 prints merged, against in-sample 232/224/224; committed rows preserved verbatim). **DEGRADED H1-2026** — 12 prints, Jan-05 to Jan-21 only | the 2026 shortfall is EIA's, not ours: its weekly archive index lists **3** editions for 2026 and every later 2026 edition URL 404s (probed directly). The monthly basis below covers the rest at plateau grain, the NEISO-2022 Algonquin precedent. 11 of 292 back-year pages fail to parse (older layouts) — a ~4% within-year hole, same class as the committed years' own gaps |
| Weekly hub prints (`gas-prices/pge_socal_citygate_weekly.csv`) | the zonal-hub input above | **EQUIVALENT 2020-2022**, **MISSING 2018-2019**, **DEGRADED 2026** (2 PG&E prints, 0 SoCal) | 40 same-date CONFLICT flags across the 292 back-year pages (the producer's own mis-parse detector; first-seen value kept) — concentrated in 2021-2022 SoCal, disclosed rather than suppressed |
| Gas basis by ISO-month (`gas_basis_by_iso_month.csv`) | EIA citygate monthly, 12 rows/yr | **EQUIVALENT 2018-2022** (pre-existing, 12 rows every year); **DEGRADED 2026** (3 months) | this is what `gas_hub_basis_overlay` falls back to wherever the daily series is short |
| F923 delivered fuel + generation (`_processed-legacy/eia923_monthly_*.parquet`) | EIA-923 monthly per plant | **EQUIVALENT 2018-2022** (176/187/191/188/186 CA cost rows vs 184/189/185 in-sample); **DEGRADED 2026** (57 rows, partial) | — |
| Plant emission rates v2 (`plant_emission_rates_v2.parquet`) | per-plant-unit-year measured CO2/NOx, CAISO 2018-2021 + 2023-2025 | **MISSING 2022 and 2026** — 2022 is a *gap year* inside an otherwise 2018-2025 CAISO block (252/245/245/245 rows 2018-2021, 245/240/240 in 2023-2025, **0** in 2022) | **MEDIUM-HIGH** (same-year measured rates are the backcast's CO2 cost basis). **The N3 tool gate is already resolved in code** — both `curate_emissions_unit_annual.py` and `derive_plant_emissions_v2.py` now accept a logged `intake_log` authorization *instead of* a calibration-complete marker, so with this session's entry landed the pair is runnable as `--holdout-intake CAISO`. Deliberately **not run here** (the owner's scope for this lane is "record, don't resolve"): it rewrites a keeper-consumed artifact and is the calibration owner's call. 2026 additionally waits on EPA CAMPD Q2-2026 |
| Plant emission rates v1 (`plant_emission_rates.parquet`) | pooled `year==0` + `{2023, 2024}` | **MISSING** all holdout years | accepted — **structural**, identical in-sample; `egrid._campd_rate_map` consumes the pooled rows |
| Measured offer surface (`caiso_offer_surface_condbinned.json`, `caiso_offer_surface_summary.csv`) — `caiso_offer_surface_measured` + `_conditional`, both keeper-ON | condbinned ladder fit on OASIS Public Bid Data, `_provenance.source` = "trade years [2023, 2024, 2025]" | **METHODOLOGY ADJUDICATION, recorded not resolved** (see §CAISO notes N-CA-2) | the artifact is a frozen 2023-2025-conduct surface; `data/raw/caiso-public-bids/` is gitignored and empty, and the OASIS bid archive is the same API whose LMP retention now stops at 2023-04-19 |
| WECC intertie hub prices (`_validation-source/wecc_intertie_lmp_hourly_CAISO.parquet`) — `caiso_per_hub_intertie`, `caiso_perhub_firm_base` | MALIN + PALOVRDE hourly, 8760/yr | **MISSING 2018-2022 + 2026** (2023/2024/2025 only) | **HIGH** — same root cause as the LMP bench: these are OASIS intertie LMPs and the API no longer serves the window. Fix requires hand-downloaded GRP bulk zips |
| Interchange actuals (`eia-930-interchange/CISO interchange hourly.parquet`) — `caiso_firm_import_shape`, export-cap derivation | EIA-930 BA-to-BA hourly per DIBA | **EQUIVALENT 2019-2022 + H1-2026** (this session: 8,759 distinct local hours × 11 DIBAs per year, identical grain to in-sample; all 289,344 committed rows verified preserved with exact values and multiplicities). **MISSING 2018** | 2018 is a **source** gap: EIA's `interchange-data` route returns `total: 0` for CISO for any 2018 window (probed) — the product begins 2019-01-01 UTC for this BA |
| `IMPORT_TRANCHES_BY_YEAR["CAISO"]` | hand-derived per-year ladder constants | **MISSING** all holdout years (`{2023, 2024, 2025}`) | MEDIUM — a code constant, and its derivation needs the neighbour/intertie prices that are themselves missing (row above). Blocked behind the OASIS retention wall, not behind effort |
| CAISO-AS requirements (`CAISO-AS/asreq_ALL_*.csv`) | OASIS `AS_REQ` DAM, hourly MW per AS region × product | **EQUIVALENT 2018-2022 + H1-2026** (this session: 15/15/14/15/15 window files for 2018-2022 and 8 for H1-2026, byte-schema and per-window row count identical to the in-sample files — 31,201 rows for a 25-day window in both 2018 and 2023) | closes the audit-doc §3.2 `asreq` item. `AS_REQ` carries **no** OASIS retention limit, unlike PRC_LMP |
| Fleet statics (EIA-860 vintage, `custom-bin-assignments.csv`, `master-plant-registry.csv`) | single registry snapshot, year-agnostic | **DEGRADED (accepted)** — same static vintage every year; identical caveat in-sample | accepted, same convention as §NYISO / §NEISO |
| Weather (CAISO zone temp raws) — `temp_dependent_derate` | NOAA daily | **EQUIVALENT 2018-2022** (pre-existing) | — |
| DAM outage windows parquet (`caiso-dam-outages/`) | not keeper-consumed (`outage_source=historic` covers it) | census only | LOW |
| storage-as-awards (`storage-as-awards/CAISO/`) | `caiso_storage_as_reservation`, default OFF, probe-inert | census only | NONE for the keeper |

### Bench / scoring series

| series | keeper-years grain | 2018-2022 / H1-2026 status | note |
|---|---|---|---|
| **`actual_lmp_hourly_CAISO.parquet` + `actual_lmp.json` CAISO block** | load-weighted TH_NP15/TH_SP15/TH_ZP26 DAM + RTM hourly, 2023-2025 | **MISSING 2018-2022 — SOURCE-BLOCKED, not a fetch task.** OASIS's ~39-month LMP retention has aged past the entire holdout window: binary-searched 2026-07-31, the earliest DAM trade date `PRC_LMP` still serves is **2023-04-19**; 2018, 2020 and 2022 all return `ERR_CODE 1000` "No data returned", and `PRC_INTVL_LMP` RTM matches. **H1-2026 EQUIVALENT — BUILT this session**: DA $20.22 / RT $19.59 over 4,343 dense hours (Jan-Jun), from 3 hubs × both markets; committed 2023-2025 records and parquet rows unchanged (the JSON diff is 59 pure insertions, zero deletions). No `*_lw` fields on 2026 — the load-weighted basis needs a demand profile the artifact does not carry for that year | **This refutes the audit doc's stated fix** ("OASIS `PRC_LMP` group fetch for 2022 (public), committed builder") — the API cannot serve it at any window size. The only route to aged-out history is a hand-downloaded GRP bulk zip (`fold_caiso_oasis_grp_zips.py`, the same route that produced the committed 2023-01 zips). **CAISO's 2022 touchpoint is therefore un-scorable until someone hand-downloads those zips** — the single most disqualifying gap in this section, and it is now a procurement task, not a scripting task |
| `actual_tail.json` CAISO | marker-aware `derive_actual_tail.py` | **MISSING** — deriver is marker-gated and CAISO has none | governance, not data; and moot for 2018-2022 while the hourly bench above is source-blocked |
| `calibration_reference.json` `isos.CAISO.<y>` | EIA-860/-923/-930 per-year block | **EQUIVALENT 2021-2022** (this session: only the two new blocks spliced in; every other block, including CAISO 2023-2025 in-sample, left exactly as committed, and all unrelated rebuild churn restored). **MISSING 2018-2020 + 2026** | 2022 demand 223.64 TWh / peak 51,104 MW; 2021 219.07 TWh / 43,615 MW. 2018-2020 blocked by the demand-profile row above (`_demand_totals` hard-requires it) — same F3 root as NEISO's |
| `CAISO_<y>_renewable_capacity.csv` | EIA-860 per-zone monthly wind/solar MW | **EQUIVALENT 2021-2022** (new); **MISSING 2018-2020 + 2026** | same root cause |
| EIA-930 fuel-mix bench (`CISO_{fueltype,region}_<y>.parquet`) | hourly | **EQUIVALENT 2018-2022 + H1-2026** | — |
| CAMPD generation bench (CA unit-level) | hourly | **EQUIVALENT 2018-2026** | — |
| Curtailment actuals (`caiso-curtailment/*.xlsx`) | CAISO 5-minute report | **EQUIVALENT 2018-2022**; **MISSING 2026** (report discontinued 2025-06-01) | validation side of the HSL row |
| EIA-930 storage breakout (C5b/C5c) | exists in-sample | **accepted structural absence** for the back years — will SKIP | same finding as §NYISO / §NEISO |

### Notes

- **N-CA-1 (the LMP retention wall — the headline finding of this lane).**
  The audit doc graded CAISO's 2022 LMP bench "BLOCKING. Fix: OASIS `PRC_LMP`
  group fetch for 2022 (public), committed builder". That fix does not exist:
  the OASIS API's retention boundary **moves forward with the calendar** and
  has now passed the whole 2018-2022 window. Measured this session by binary
  search, not inferred: `2023-03-24` aged out → `2023-04-19` serves, and every
  probe at 2018-06-01 / 2020-06-01 / 2022-06-01 returns ERR 1000 for both DAM
  and RTM. `fetch_caiso_oasis.py`'s docstring is corrected accordingly. The
  practical consequence for the register: **no amount of scripting closes
  CAISO's out-of-training bench** — it needs the bulk GRP zips, which are a
  hand-download from the OASIS UI (the 2023-01 zips already in
  `data/raw/lmp-data/CAISO/` came that way). Same wall blocks the WECC
  intertie hub prices and, in all likelihood, the public-bid corpus of N-CA-2.
- **N-CA-2 (measured-offer-surface vintage — ADJUDICATION RECORDED, NOT
  RESOLVED).** `caiso_offer_surface_measured` and
  `caiso_offer_surface_conditional` are both keeper-ON and read a condbinned
  ladder whose `_provenance` records "trade years [2023, 2024, 2025]". A
  2018-2022 or H1-2026 solve has exactly two options, and choosing between
  them is a **methodology** decision for the calibration owner, not a data
  task: **(a)** reuse the 2023-2025-fit surface unchanged, accepting a
  vintage asymmetry — the offer conduct of a year is then imported from a
  different regime (2022's gas crisis and 2018-2020's pre-storage fleet are
  not the 2023-2025 market), which is a *forward-analogue* question under
  rule 13 rather than an outright violation, since the surface is a measured
  behavioural input and not an outcome; or **(b)** re-derive per window from
  that window's own public bids — for which **no raw exists**:
  `data/raw/caiso-public-bids/` is gitignored and holds only its README, and
  the OASIS `PUB_DAM_GRP` GroupZip route is the same API as N-CA-1's
  (queued "in Processing" on every probe this session, so its own retention
  boundary is unconfirmed — but the LMP boundary is the strong prior).
  Recorded here for the register's sign-off; **no flag was changed and no
  surface was re-derived.**
- **N-CA-3 (v2 emission-rate marker gate — DECISION RECORDED, NOT
  EXERCISED).** The register's standing N3 blocker ("both tools hard-require
  a calibration-complete MARKER, encoding the pre-amendment rule-22 gate") is
  **stale**: at HEAD both `curate_emissions_unit_annual.py` and
  `derive_plant_emissions_v2.py` accept *either* the marker *or* a logged
  `intake_log` authorization. With this session's `intake_log` entry landed,
  `--holdout-intake CAISO` passes the gate, so CAISO 2022 (and, when EPA
  posts Q2-2026, 2026) can be derived without any marker. Not run here: the
  owner scoped this lane to record the decision, and the derive rewrites a
  keeper-consumed artifact (`plant_emission_rates_v2.parquet`) whose
  in-sample rows every CAISO keeper reads. Owner/calibration-owner call.
- **N-CA-4 (in-sample defect surfaced, NOT fixed).** An unscoped
  `--merge-missing` rebuild of the wide extract filled **9 missing local-2025
  hours** (2025-12-31 16:00-23:00, supplied by the 2026 long extract's
  leading UTC hours) and thereby moved `caiso_2025_hsl_hourly.parquet` — an
  in-sample keeper input. The merge was re-scoped to the authorized holdout
  years only and 2025 was restored byte-identical; a `--merge-years` flag now
  makes that scoping explicit so no future holdout back-fill can move a
  training year by accident. The 2025 tail gap is real and is flagged to the
  CAISO calibration owner.
- **N-CA-5 (transcription lineage).** Both new capacity-deliverability
  transcribers ship a `--verify` mode that asserts they reproduce the
  **committed** 2023-2025 rows before any back-year row is written, and both
  merge by **byte-append** rather than rewrite (the committed registry
  carries mixed line endings from successive hand-appends, so re-emitting it
  through `csv.writer` would churn every committed line). The same
  discipline applies to the gas derivation, which reproduced the committed
  2023-2025 basis values exactly before the 2020-2022 rows were added.
  `tests/iso/caiso/test_capacity_deliverability_caiso.py` pins both the new
  total (386) and the unchanged in-sample subtotal (153).

### Verdict tally (this section)

**EQUIVALENT 17** (wide hourly 2018-2022, long form, TAC load, CAMPD
unit-level, unit outages, HSL 2019-2022, MIC 2018-2022, LCR 2021-2022, zonal
peak/PRM 2020-2022, zonal gas hub 2020-2022, citygate daily 2018-2022,
weekly hub prints 2020-2022, monthly gas basis, F923, AS_REQ 2018-2022 +
H1-2026, interchange 2019-2022 + H1-2026, calref/renew-cap 2021-2022,
930 fuel-mix + CAMPD bench, curtailment actuals) /
**DEGRADED 6** (LCR 2018-2020 criterion vintage, PRM citation substitution,
wide hourly H1-2026, citygate daily H1-2026, weekly prints H1-2026, monthly
gas basis 2026, fleet statics) /
**MISSING 12** (demand profile 2018-2020 + 2026, HSL 2018 + 2026, LMP bench
2018-2022, WECC intertie all years, import-tranche constants, v2 emission
rates 2022 + 2026, v1 emission rates, local-area peak load, zonal gas hub
2018-2019, weekly prints 2018-2019, calref/renew-cap 2018-2020 + 2026,
`actual_tail`). **Zero unresolved MISSING**: every row carries a materiality
rating and either a fix or an explicit acceptance/blocking rationale.

### What still blocks a CAISO out-of-training touchpoint

1. **The holdout spend freeze** (`holdout-freeze.json`) — outranks every
   marker; nothing is spendable while it stands.
2. **No calibration-complete marker of either tier.** CAISO is absent from
   both `complete` and `final`, so 2022 (validation) and 2019 / H1-2026
   (locked) are all quarantined. An owner determination, not a data task.
3. **Register sign-off** (this section) by the owner.
4. **The LMP bench (N-CA-1)** — the hard data blocker, and now known to be a
   hand-download rather than a fetch. A touchpoint that cannot be scored
   cannot be spent, so this gates 2018-2022 outright even if 1-3 clear.
5. **The demand-profile artifact** for 2018-2020 (and 2026) — a hard blocker
   below which no dispatch of those years is possible at all.
6. Optional-for-parity, in descending materiality: v2 emission rates 2022
   (now runnable, N-CA-3), the WECC intertie prices + import-tranche
   constants (same wall as 4), the offer-surface vintage adjudication
   (N-CA-2), local-area peak loads, zonal gas hub 2018-2019.

**H1-2026** additionally rides the publication horizon shared by every ISO:
EPA CAMPD Q2-2026, EIA delivered gas from May-2026, the full-8760 demand
contract, and — CAISO-specific — the EIA weekly gas archive's 3-edition 2026
coverage and the permanently discontinued curtailment report. What **is**
landed and EQUIVALENT through 2026-06-30: `CISO hourly` (4,343 h),
`CISO_{region,fueltype}_2026`, CAMPD `CA_2026`, AS_REQ (8 windows),
interchange (4,317 h), and — uniquely for this window — the **DAM and RTM
hub LMPs**, which OASIS serves for 2026 because the retention wall is
behind, not ahead of, it.

---

## ERCOT / MISO

Sections pending their own lanes (PJM's and CAISO's are above). Seed material:
`docs/iso-2022-holdout-data-availability-audit-2026-07.md` (2026-07-31
cross-ISO coverage audit — keeper-flag-grounded per-family 2022 parity matrix,
per-ISO gap tables §3.1–§3.4, 2018–2021 census §4, and the repo-vs-record
discrepancy list §5; its CAISO rows were re-graded on 2026-07-31 by the
§CAISO lane above, which CLOSED the wide-hourly hole and REFUTED its stated
CAISO LMP fix); plus `docs/out-of-sample-results-2026-07.md` §1.1 (ERCOT,
incl. the known Waha annual-basis DEGRADED candidate) and the register
handoff's known-items list (§"Known DEGRADED/asymmetric items").
