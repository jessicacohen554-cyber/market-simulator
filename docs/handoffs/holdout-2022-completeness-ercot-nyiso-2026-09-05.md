# 2022 validation-touchpoint data completeness — ERCOT + NYISO (2026-09-05)

> Status: RECORD of a rule-22 `[R-HOLDOUT]` data-completeness pass. Both ISOs hold a
> `complete` marker (`frontend/data/backcast/calibration-complete.json`), so the 2022
> validation tier is authorized for solve/score/register; the locked test (2019 / H1-2026)
> stays frozen and untouched. No parameter was tuned. Every change below is a measured-input
> extension applied to the year it belongs to (data is never held out — the score is).

## 0. Method

1. **No-LP fleet rebuild** of each keeper recipe on 2022 via
   `scripts/lib/bundle_fleet.reconstruct_bundle_fleet(bundle, 2022)` (`run_year(fleet_only=True)`,
   the same reconstruction `legitimacy_diagnostics.py` uses) — proves loader-resolvability of
   fleet, offers, demand, renewables, TTC/interchange, availability overlays.
2. **Per-file year census** over every ERCOT/NYISO-token file under `data/raw` and every
   file-level reference in `src/market_sim` (scratch scripts, read-only), because several
   per-year overlays are deliberately **inert when a year has no rows** (`outages.py`,
   `results/scarcity.py`, `model/storage.py`, `nyiso_market_solar.py` all return empty/ones/
   `None`) and a fleet rebuild cannot see that.
3. Producer re-proof before every extension: each derive/fetch was re-run over the committed
   2023–2025 span and compared to the committed bytes/rows before 2022 rows were added.

Keepers assessed: ERCOT `2026-09-05-ercot248-two-config-keeper` (carve-out `ercot236_k33_clip`
for 2023; forward `ercot234_eastex_identity` for 2024–25) and NYISO
`2026-09-05-nyiso-189-steam-identity`.

## 1. NYISO — COMPLETE after three extensions (2022 solved this session)

| item | before | action |
|---|---|---|
| Long Island N-1-1 `transfer_security_limit`, delivery year 2022/2023 (`nyiso_li_lcr_tsl` + `nyiso_li_tsl_n11_security` ON) | **MISSING — hard fail** (`apply_nyiso_li_tsl_import_cap` raises) | Row added to `data/raw/capacity-deliverability/nyiso/nyiso.csv`: 940 MW, source the 2024-25 Locality Bulk Power Transmission Capability Report p.7 — **the same construction the committed 2023/2024 row already uses** (nyiso-130). The 2023-24 edition (fetched: NYISO "2023 Locality Bulk Power Transmission Capability Report") states only the loss-of-source-net Zone K limit (325 MW, unchanged 2022→2023 per its Table 4) and the 660 MW Neptune loss-of-source; it does not print the N-1-1 figure. **Owner should confirm** carrying 940 back one more year (alternative: 325+660 = 985 inferred from the 2023-24 Table 1, not a published number). |
| NY Harbor ULSD daily spot 2022 (`dual_fuel_oil_daily_parity`) | 2023–2025 only → 2022 daily oil shape silently = 1.0 (monthly-flat oil cap) | `fetch_ny_harbor_distillate_daily.py --start-year 2022 --end-year 2025`; 2023–2025 rows byte-identical to committed; +249 trading days for 2022 |
| NYISO market-generator solar 2022 (`nyiso_solar_market_generator_basis`) | 2023–2025 only → 2022 falls back to the EIA-860 basis (the double-count the input exists to remove) | `derive_nyiso_market_solar.py` `YEARS` extended to 2022 = the 2023 Gold Book vintage back-projected on published in-service dates (2022 is a PDF vintage, no workbook). 2023–2025 rows identical. Limitation stated in the script: units deregistered during 2022 are invisible. |
| `data/clean` partitions (`capacity-deliverability`, `nyiso-interface-flows`, `gtc-limits`) | absent in a fresh container (disposable, gitignored) | curated in-session; raw sources carry 2022 |

Verified present for 2022 with no action: EIA-930 (8,760 h), zonal load actuals, LMP bench
2018–2026 (clock-fixed, register 2026-07-31), AS DA/RT prices, reserve requirements 2022
(61,320 rows), CAMPD unit/partial/layup/short outage windows, nuclear availability 2018–2025,
`NUCLEAR_MONTHLY_CF_BY_YEAR` 2022, `IMPORT_TRANCHES_BY_YEAR` 2022, `NYISO_INTERFACE_TTC_BY_YEAR`
2022, plant emission rates v2 2022 (380 rows), Transco Z6 daily / Iroquois monthly / downstate
CT basis / LDC transport 2022, weather 2022, SCR/EDRP enrollment 2022, PAR outages 2022,
capacity-deliverability LCR/import-limit 2022/23, `actual_tail.json` 2022, PJM/NEISO 2022
hourly DA LMPs (import hub pricing). Designed 2022 fallbacks (not gaps): `NYISO_loss_surface.csv`
uses its pooled (`year=0`) rows outside 2023–2025; NYSDEC 227-3 restrictions gate on
effective dates, so none are active in 2022.

## 2. ERCOT — COMPLETE for a touchpoint solve after three extensions; two items remain owner-side

| item | before | action / status |
|---|---|---|
| 60-Day DAM thermal availability family 2022 (`ercot_thermal_dam_availability{,_hourly,_plant}` ON) — `ercot-thermal-dam-availability.csv`, `-hourly.csv`, `-site-hourly.parquet` | **2023–2025 only** (the 2026-07-31 derived 2018–2022 block is not in the tree; the file was re-added 2026-09-04 at the 2023–25 slice) → the overlay is **silently inert** in 2022 (`ercot_thermal_dam_availability_series` returns `{}`) | Re-derived from the on-disk 60-Day Gen_Resource disclosures (four `ercot-AS/…2022_*` fragments + `ercot/…2023_Jan-Mar` for Nov 2–Dec 31: 365/365 days). 2022 rows taken from the joint 2022–2025 derive (ruling-#8 cross-year rating fallback) and **prepended ahead of the byte-frozen committed 2023–2025 rows**. Note: a joint re-derive also moves 274 committed 2023–25 rows (max avail delta 0.0135) — NOT applied, to keep keeper byte-identity; flagged for the owner. |
| `NUCLEAR_MONTHLY_CF_BY_YEAR["ERCOT"][2022]` (level anchor for the measured nuclear windows) | 2023–2025 only → pre-2023 nuclear block was a timing series with an unreconciled level | `derive_nuclear_monthly_cf.py --isos ERCOT --years 2022 2023`: 2023 reproduces the committed row exactly; 2022 row added to `constants.py` |
| `actual_tail.json` ERCOT 2020–2022 (C3c scoring bench) | missing (deriver is marker-gated; ERCOT had no marker when last run) | `derive_actual_tail.py` re-run under the `complete` marker: ERCOT 2022 = 238 DA h / 196 RT h > $200 (2020, 2021 also landed as measured bench rows) |
| **ERCOT HSL 2022** (`ercot-hsl/ercot_2022_hsl_hourly.parquet`) | **MISSING — owner manual upload only** (NP4-732-CD wind / NP4-737-CD solar, or the NP4-742/745 GEO family, via the login-gated Data Access Portal; `data/raw/ercot-hsl/README.md`). | **OPEN.** Consequence in 2022: renewables ride the `RENEWABLE_BOUND_FORECAST_UNCURTAILED` construction (delivered profile grossed up by a recent HSL year's measured curtailment rate — the forecast method), and `ercot_gtc_limits_measured` self-disables (its gate needs measured HSL) although the 2022 GTC clean partition exists (13,321 rows). Drop the 2022 archives in `data/raw/ercot-hsl/np6/2022/` and run `build_ercot_hsl.py --year 2022`. |
| ERCOT `ercot_zonal_gas_hub.csv` 2022 | 7 zones present | no action |
| Plant emission rates v2 ERCOT 2022 | 2022 gap year | **not needed** — neither ERCOT config arms `use_plant_emission_rates_v2`; optional: `curate_emissions_unit_annual.py --years 2022 --holdout-intake ERCOT` + `derive_plant_emissions_v2.py --iso ERCOT --years 2022 --holdout-intake ERCOT` |

Verified present for 2022 with no action: LMP bench hourly + 15-point zonal 2018–2026
(clock-clean), EIA-930 8,760 h, native zonal load, CAMPD unit/partial outages, non-CAMPD
availability, nuclear windows, storage capability (hourly), ORDC reserves/price adders
(`rtolcap`, `rtordpa`, …), AS plan (ASPLANNP433), AS by resource type, delivered gas N3045TX3,
F923 monthly plant fuel costs, weather, `calibration_reference` + renewable capacity 2022, SCED
offer-wall tables (2022–2025), GTC raws.

**2022 recipe semantics the owner must read before scoring (structural, not data):**

- **`*_from_year = 2023` gates** leave `ercot_reserve_supply_cap`, `ercot_load_resource_reserve`,
  `ercot_storage_as_deployment` (and `ercot_storage_as_reserve`, from_year 2025) **unarmed in
  2022** by construction; `ercot_ecrs_requirement` is correctly zero (ECRS launched June 2023).
  The comments on the first two say the mechanism is "physically correct in every year" and the
  from_year is a modeling default because the measured series began 2023. The measured 2022
  series for the RTOLCAP cap exists (`ercot_2022_ordc_reserves_hourly.parquet`); the RRS-UFR
  load-resource award series does not (`ercot_2022_as_up_mw.parquet` missing — buildable from
  the back-year 60-Day DAM AS awards, which unlike 2023+ carry MCPC too). Running the recipe
  verbatim is the rule-22 touchpoint; arming these in 2022 is a recipe decision, not a data fix.
- **Year-scoped SCED conduct tables** (`ercot_faststart_pool_*`, `ercot_dam_cleared_share_*`,
  `ercot_offer_midcurve_*`, `ercot_commitment_loading_state`, `ercot_storage_rt_offer_*`,
  `reliability_deployment_floor_ERCOT`, `ct_deployment_floor_ERCOT`) carry 2023–2025 only.
  Measured 2022 behaviour in the rebuild: fast-start pool **inert** ("year 2022 absent — every
  surface byte-identical"), cleared-share boundary **pooled**, coal peak yearly level **static**;
  cleared-share RT basis and SCED offer wall DO have 2022 tables. Full-year 2022 SCED 60-day
  disclosures are past MIS retention (`ercot/SCED/` starts 2023-03), so these cannot be extended.
- **Storage AS products 2022** (`ercot_2022_storage_as_products_hourly.parquet`) missing → the
  storage AS credits read zeros (inert); moot while the from_year gates hold.
- The **carve-out config** (`ercot_offer_swcap_clip` + k_peak 33) was ruled for the 2023 ECRS-era
  regime; the two-config partition ruling designates no config for 2022. Running BOTH on 2022 is
  the owner's explicit instruction for this touchpoint.

## 3. Not applicable / unchanged

No mechanism was tested; no matrix cell changes. No keeper changed. The `data/clean` tree is
disposable and was rebuilt locally only.
