# _validation-source — raw

Calibration/validation benchmark targets — a heterogeneous set of "what
actually happened" series the backcast is scored against. Leading `_` marks
it as not yet migrated to the `data/clean` curation seam (`data/README.md`).

| File(s) | Producing script | Source |
|---|---|---|
| `wecc_intertie_lmp_hourly_CAISO.parquet` | `scripts/fetch_caiso_intertie_lmp.py` | CAISO OASIS `PRC_LMP` DAM query at Malin/Palo Verde intertie scheduling points |
| `actual_lmp_hourly_{MISO,...}.parquet`, Carolinas FERC-714 proxy | `scripts/fetch_neighbor_lmp.py` | `docs.misoenergy.org/marketreports/<date>_{rt_lmp_final,da_expost_lmp}.csv`; FERC Form 714 Part II Schedule 6 |
| `actual_lmp_hourly_zonal_MISO.parquet` | `scripts/derive_miso_hub_lmp.py` | reduces `data/raw/lmp-data/MISO/` hub stagings |
| `actual_lmp_hourly_SPP.parquet`, `actual_lmp_hourly_zonal_SPP.parquet` | `scripts/data/build_spp_lmp_reference.py` (`--per-hub` for the zonal file) | SPP Integrated Marketplace `{DA-LMP,RTBM-LMP}-MONTHLY-SL-YYYYMM.csv` via `portal.spp.org/file-browser-api` (lanes SPP-12 / SPP-14; **extended to 2019–2022 by lane SPP-30, 2026-09-12**). The zonal file is 122,640 rows × **2019–2025**, `zone` ∈ {`SPPNORTH_HUB`, `SPPSOUTH_HUB`} — **SPP TRADING HUBS, not model zones**: each is a fixed node cluster (Nebraska / central Oklahoma, weightings in `data/raw/spp-planning/Hub_Definitions.csv`), never an average over the SPP-North / SPP-South model zone it is named after. The system file is the simple mean of the two (61,320 rows × 2019–2025), and reproduces the zonal file hub-for-hub (SPP-14 cross-check gate, 0.0000 %). Reduced to the `actual_lmp.json` SPP block by `scripts/data/derive_actual_lmp.py --isos SPP`. **SPP-30's 2019–2022 extension re-fetched 2023/2024/2025 as an overlap control and reproduced the committed rows BIT-EXACTLY** — `corr = 1.000000`, `Δannual-mean = 0.000000`, `max|Δ| = 0.00000`, and float32-exact equality on every mutually-finite hour (8,754/8,754; 8,748/8,748 for 2024 RT) across all 18 year × hub × {rt,da} series — so the committed years were preserved byte-for-byte rather than overwritten. Every year, leap years included, is 8,760 rows on the fixed non-leap CST clock with Feb 29 dropped; coverage is 0.9993 in every year (the 6-hour tail whose filler — the next year's first 6 GMT hours — is itself absent at source), and 2024 RT additionally misses hours 738–743, a real RTBM source gap |
| `actual_lmp_hourly_area_SPP.parquet` | `docs/handoffs/spp57/build_area_price.py` (lane SPP-57, 2026-09-07) | The residual-South price of PRECOMMIT-spp-57 §3.4, from the same `RTBM-LMP-MONTHLY-SL-YYYYMM.csv` files as the zonal file, on the same calendar: `p_sps` = the SPS load-zone settlement location `SPS_SPS`; `p_sw` = the simple mean of 28–29 named SWEPCO / AECC settlement locations in AR / LA / TX (`n_sw_sl` per hour); `p_s` = `w_sps`·p_sps + (1−w_sps)·p_sw with `w_sps` the residual zone's measured load composition (0.6053 / 0.6218 / 0.6205). 26,280 rows × 2023–2025, RT only. **NOT a model-zone benchmark and NOT read by any scorer** — it is the third point of the three-point spread the OK↔S link TTC was identified on (FINDING-spp-57 §3), kept so the identification is reproducible without the ~900 MB pull. The rebuilt hubs cross-check the committed zonal file to 5e-5 $/MWh |
| `actual_lmp_components_hourly_zonal_SPP.parquet` | `scripts/data/fetch_spp_hub_lmp_components.py` (lane SPP-80, 2026-09-25) | The SAME `{DA-LMP,RTBM-LMP}-MONTHLY-SL-YYYYMM.csv` files as the zonal file, keeping all three price types SPP publishes per hub (`LMP`, `MCC` congestion, `MLC` loss) instead of LMP alone; `mec = lmp − mcc − mlc` (SPP's LMP identity). Long form: `year`/`hour`/`zone` (`SPPNORTH_HUB`/`SPPSOUTH_HUB`)/`market` (`rt`/`da`)/`lmp`/`mcc`/`mlc`/`mec`, 245,280 rows × 2019–2025, on the zonal file's calendar through the builder's own unmodified `gmt_dense_to_model_clock`. **`lmp` reproduces the committed zonal file bit-exactly** (`--verify`: max |Δ| = 0.000000 $/MWh over every mutually-finite cell, both markets, all seven years). sha256 `c9d227918117e66138c616041452cff3fc912e2ec0c3ec29ee58596706275589`, 4,611,777 B. **Not read by any scorer**: it is the congestion/energy split of the SPP-80 FINDING (`docs/handoffs/FINDING-spp-80-upper-tercile-premium-2026-09-25.md`) |
| `spp_rtbm_or_cleared_hourly.parquet` | `scripts/data/fetch_spp_or_cleared.py` (lane SPP-81, 2026-09-25) | SPP RTBM operating-reserve **cleared MW** (portal product `operating-reserves`, anonymous HTTPS, `RTBM-OR-<stamp>.csv` five-minute files; the 2019–2024 year zips range-read one day per request, no member modified). Per interval the `SPP` system reserve-zone row (present in every landed interval, `src = spp_row`), then the hourly mean on SPP-80's model clock. Long form `year`/`hour`/`regup`/`regdn`/`rampup`/`rampdn`/`spin`/`supp`/`uncup`/`stsuncup` (MW; ramp from 2022, uncertainty from 2023)/`n_int`/`src`, 61,226 hours. **2025 is a SAMPLE**: no year zip exists yet, so one interval (local HH:30) per hour (`n_int = 1`); 2019–2024 are 12-interval means. Hours missing: 2022 1, 2023 36, 2024 8, 2025 49. sha256 `6a5f03d5893a64c7f195f9daa55bf89a377cb9accbf916c103a7614959a85f40`, 1,234,908 B. **Not read by any scorer**: the ramp leg of `docs/handoffs/FINDING-spp-81-residual-upper-tercile-2026-09-25.md` |
| `calibration_reference.json`, per-year `*_renewable_capacity.csv` | `scripts/build_calibration_reference.py` | EIA-860 |
| `actual_lmp_hourly_ERCOT.parquet` (etc.) | `scripts/derive_actual_lmp.py` | per-ISO LMP sources under `data/raw/lmp-data/` |
| `actual_lmp_zonal_ERCOT.parquet` | `scripts/build_ercot_hsl.py` / ERCOT zonal derivation | ERCOT settlement-point data |
| `pjm_border_lmp_hourly_MISO.parquet` | `scripts/build_pjm_border_lmp_miso.py` | PJM/MISO seam LMP |
| `ct_deployment_floor_{CAISO,ERCOT,NEISO,NYISO,PJM}.parquet`, `reliability_deployment_floor_ERCOT.parquet` | `scripts/derive_reliability_deployment.py` / `scripts/derive_ct_deployment.py` | model-side derived reliability-deployment floors |
| `offer_curve_dam_hrmults*.json`, `offer_curve_deltas_*.json` | `scripts/derive_dam_offer_hrmults.py` | ERCOT DAM offer archives |
| `ercot_ordc_lolp_params.csv`, `pjm_ordc_curve.csv`, `cf_emd_baseline_ERCOT.json` | model-side derived reference curves | — |
| `capacity_actuals_{ercot,pjm,nyiso,miso,neiso}.csv`, `actual_as_reserve_NYISO.parquet` | `scripts/data/build_capacity_actuals.py`, validation reconciliation inputs | EIA-860/923 |
| `retired_sheet_coverage_gaps.csv` | hand-curated (RD-5); read by `scripts/data/build_capacity_actuals.py::load_retired_sheet_gap_fix` | this repo's own committed `data/raw/eia-860/vintage_{2021,2022}/` snapshots |

`scripts/curate_validation.py` is the reconciler that reads only the
already-materialized artifacts here (EIA-860 renewable capacity, EIA-923
by-fuel generation, eGRID 2023 emissions, EIA-930 demand totals, Henry Hub
gas price, historical DA LMP) into the `validation` clean datatype — it does
not fetch anything itself.

**Known gap:** `NYISO_2024_renewable_capacity.csv` is absent (2023 and 2025
are present) — a hole in the per-year series, not yet backfilled.

**Regeneration:** each file regenerates from its listed script and the raw
sources those scripts already cite — except `retired_sheet_coverage_gaps.csv`,
which is hand-curated (transcribed verbatim from this repo's own committed
EIA-860 vintage snapshots; see its header for exact provenance).

**RD-5 actuals-coverage fix (2026-07-15, retirement-lane-intake).**
`capacity_actuals_nyiso.csv` and `capacity_actuals_miso.csv` each carry one
retirement row that the current top-level EIA-860 retired sheet cannot supply
on its own — see `retired_sheet_coverage_gaps.csv` (this directory) for the
full provenance:

- **Indian Point 3** (plant 8907, NYISO, 1012 MW nuclear, retired 2021-04) —
  the current top-level EIA-860 snapshot has dropped this plant code from
  every sheet, not just moved it between them. Unambiguous: a genuine
  retirement, correctly scored once the gap-fix row is included.
- **Palisades** (plant 1715, MISO, 811.8 MW nuclear, retired 2022-06) —
  Palisades **restarted generation in 2025** (the first US commercial
  restart of a retired nuclear plant, under a DOE loan + NRC-approved
  restart), which is why the current top-level snapshot shows it back in the
  operable sheet instead of retired. The gap-fix row restores the 2022
  retirement *event* to the actuals target — it does **not** decide how a
  since-reversed retirement should score against a 2021-2025 hindcast (a
  model that "retired" Palisades on schedule and a model that never touched
  it are arguably both defensible against a plant that came back). That
  scoring-adjudication call belongs to the RC-0B identification/scoring memo
  (`docs/handoffs/forecast-retirement-calibration-plan-2026-07.md` §1.1 item
  3, §5 RD-5) — this fix only makes the underlying fact available to score
  against; it does not itself resolve the Palisades restart question.

**FFR-7A physical-exit dating (2026-08-06, owner decision D-21(b)).** The
`capacity_actuals_*.csv` targets are now dated at the EIA-860 **status
transition to OS/RE**, not at the reported `Retirement Year`, and units already
out of service at the fleet-basis vintage are excluded — see
`scripts/data/build_capacity_actuals.py::physical_exit_year` and
`docs/handoffs/ffr-7a-scoring-target-hygiene-2026-08-06.md` for the rule, the
per-ISO delta and the sources of every changed row. Two consequences for this
directory:

- The builder now reads the whole committed EIA-860 **release series**
  (`data/raw/eia-860/vintage_*/` plus the current release), which generalises
  what `retired_sheet_coverage_gaps.csv` does by hand: 106 of the 442 units the
  2022-vintage retired sheet dates to 2021-2022 have since been dropped from the
  current release's retired sheet, and the release series recovers all of them.
  **Indian Point 3 no longer depends on the gap-fix file** (it is recovered
  from `vintage_2021`/`vintage_2022` generically; the union de-duplicates).
- **Palisades still does**, and that is the point: its latest EIA status is
  `OP`, so the status rule correctly declines to call it an exit, and only the
  curated override keeps the 2022 event in the target. The RC-0B adjudication
  above is untouched and still open.
