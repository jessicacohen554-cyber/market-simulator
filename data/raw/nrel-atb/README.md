# nrel-atb — raw

Source root for the `nrel-atb` clean datatype
(`data/dictionary/schema/nrel-atb.schema.yaml`). Fetched by
`scripts/fetch_nrel_atb.py` from NREL's public OEDI data lake distribution of
the Annual Technology Baseline (not a scrape of `atb.nrel.gov`, which is
blocked by this environment's outbound network policy — see below) and
curated by `scripts/curate_nrel_atb.py`, which reads
`atb_2024_electricity_filtered.csv` in this directory and writes schema-valid
Parquet to `data/clean/nrel-atb/nrel-atb.parquet`.

## Why this exists

D4 in the forecast-driver audit: `NEW_ENTRY_COSTS` in `constants.py` is a
single hardcoded snapshot per technology, cited "NREL ATB 2024" but never
actually sourced from ATB's own calendar-year trajectory — cost decline is
applied only via a separate Wright's-Law curve on hardcoded global
deployment. `TECH_COST_MULTIPLIERS` (the low/mid/high tech-cost-path lever)
is even more explicit about the gap: its own comment says "this environment
could not reach atb.nrel.gov to pull the exact 2024 scraped case ratios."
This directory lands the real ATB 2024 year-by-year, cost-case-by-cost-case
data so both gaps can be closed with real numbers instead of hand-set ratios.

## Network note: `atb.nrel.gov` / `nrel.gov` is blocked here

Every `nrel.gov` subdomain (`atb.nrel.gov`, `docs.nrel.gov`, `www.nrel.gov`)
fails at the proxy with a CONNECT 502 in this environment — confirmed via
`curl` and the proxy's own `recentRelayFailures` log
(`host: atb.nrel.gov:443`, `kind: connect_rejected`). **The OEDI S3 data
lake (`oedi-data-lake.s3.amazonaws.com`) is a separate AWS-hosted domain and
is fully reachable** — it is also NREL's own recommended machine-readable
distribution channel for ATB
(<https://data.openei.org/submissions/4129>), not a workaround or a scrape.
This intake used that path exclusively.

One consequence: the ATB 2024 **dollar-year convention** (2022$, per
`atb.nrel.gov/electricity/2024/index` — "All monetary values are in 2022 USD
based on the Consumer Price Index... (BLS, 2024)") could only be confirmed
via search-indexed content, not a direct fetch of the source page. Flagged
in the schema's `unit` column description for verification with browser
access if a session needs higher confidence before using these values in a
constants.py re-derivation.

## Source file and filter

Full source: `oedi-data-lake.s3.amazonaws.com/ATB/electricity/csv/2024/v3.0.0/ATBe.csv`
(~572,232 rows, ~94MB — every ATB electricity technology x resource class x
parameter x financial/tax-credit/cost case x cost-recovery-period x year
NREL publishes). Landing the full file would make it the largest file in the
repo for no benefit — this model only needs ~19 technology/techdetail
combinations. `scripts/fetch_nrel_atb.py` downloads the source and filters
it to exactly this list (verified reproducible: re-running the script against
the same source file byte-for-byte reproduces `atb_2024_electricity_filtered.csv`):

| technology | techdetail | model tech | selected via |
|---|---|---|---|
| LandbasedWind | Class4 | wind | ATB `default`=1 |
| UtilityPV | Class5 | solar | ATB `default`=1 |
| NaturalGas_FE | NG 2-on-1 Combined Cycle (F-Frame) | gas_cc | explicit (no ATB default for this tech) |
| NaturalGas_FE | NG Combustion Turbine (F-Frame) | gas_ct | explicit |
| NaturalGas_FE | NG 2-on-1 Combined Cycle (F-Frame) 95% CCS | gas_cc_ccs (95%) | explicit |
| NaturalGas_FE | NG 2-on-1 Combined Cycle (F-Frame) 97% CCS | gas_cc_ccs (97%) | explicit |
| Nuclear | Nuclear - Large | nuclear_large | ATB `default`=1 |
| Nuclear | Nuclear - Small | nuclear_smr | ATB `default`=0 (SMR is the non-default class) |
| Utility-Scale Battery Storage | 2/4/6/8/10Hr Battery Storage | li_ion_4hr / 8hr / (12hr has no exact ATB match — 10Hr is nearest) | all 5 durations landed |
| Coal_FE | Coal-new | existing-coal FOM cross-reference | ATB `default`=1 |
| Biopower | Dedicated | biomass | ATB `default`=1 |
| Hydropower | NPD1 | hydro | ATB `default`=1 |
| Geothermal | HydroFlash | geothermal (conventional cross-reference) | ATB `default`=1 |
| Geothermal | NFEGSFlash, NFEGSBinary, DeepEGSFlash, DeepEGSBinary | geothermal EGS (`GEOTHERMAL_PARAMS`) | explicit — all four ATB EGS classes (added 2026-07-19) |
| OffShoreWind | Class3, Class12 | offshore_wind | both ATB `default`=1 (fixed-bottom + floating) |

Parameters landed: `CAPEX`, `Fixed O&M` only — exactly the D4 calendar-year
capex/FOM trajectories scope (see "Why this exists" above and
`docs/handoffs/forecast-driver-capacity-revenue-audit-plan-2026-07.md` §4 N8:
"capex/FOM by tech x year x case"). ATB also publishes `Variable O&M`, `CF`,
and `Heat Rate` under the same filter, plus finance-internals parameters
(WACC, CRF, FCR, debt fraction, interest/tax rates) — all excluded: not
consumed by this model's cost tables (VOM/CF/heat-rate inputs come from the
fleet/offer-curve pipeline, not ATB), and keeping the committed extract
scoped to what D4 needs keeps it small. A future session needing ATB's
Variable O&M/CF/Heat Rate series can add them to `PARAMETERS` in
`scripts/fetch_nrel_atb.py` and re-run against a fresh OEDI download.
Financial case: `Market` only (ATB's `R&D`/program-cost case is out of
scope). All three ATB cost cases (`Advanced`/`Moderate`/`Conservative`) are
landed — these map to this model's `tech_cost_path` low/mid/high lever.

**`crpyears` (cost-recovery period) is dropped.** ATB publishes each row
across up to 3 `crpyears` options (20/30/45/55/60 depending on technology),
but verified against the full source: CAPEX/Fixed O&M are **byte-identical**
across every `crpyears` option for the same (technology, techdetail,
parameter, case, tax_credit_case, scenario, year) — `crpyears` only affects
ATB's own derived LCOE/finance metrics, which this extract doesn't carry.
Keeping it would triple row count for zero information, so
`scripts/fetch_nrel_atb.py` drops it (keeping the first occurrence per key)
after verifying invariance. A session that needs the original
crpyears-differentiated LCOE calculation should re-run the OEDI fetch
directly and skip the dedup step.

**On-disk layout note:** `atb_2024_electricity_filtered.csv` is committed as
numbered, header-repeating parts (`atb_2024_electricity_filtered.part00.csv`,
`.part01.csv`, ...) rather than one file — an artifact of this session's push
tooling (the git-API push path used here caps individual file-content size),
not a change to the data. `scripts/curate_nrel_atb.py` reads the single-file
name if present, else concatenates the parts (same convention as
`data/raw/coal-prices/`, see that directory's README); both layouts are
byte-identical once joined. A future `fetch_nrel_atb.py` re-run writes a
single file again, which the curate script also reads fine.

## Regeneration

```
python scripts/fetch_nrel_atb.py          # downloads ~94MB, filters, writes the CSV above
python scripts/curate_nrel_atb.py         # raw CSV (or its .part*.csv pieces) -> clean Parquet
```

`--atb-year`/`--atb-version` select a different ATB edition once one is
released (each edition/version is its own immutable OEDI object, so this
regenerates cleanly rather than overwriting history).

## DATA (landed)

- [x] `atb_2024_electricity_filtered.csv` — 3,858 rows (23 tech/techdetail
      combos x up to 2 parameters (CAPEX, Fixed O&M) x 3 cost cases x 27
      years, crpyears-deduped as above; not every combination populated for
      every tech).

> **FF-1E completeness fix (2026-07):** the extract was previously committed as
> only `.part00`/`.part01` (600 rows, the four alphabetically-first techs —
> Biopower/Coal_FE/Geothermal/Hydropower); the entry technologies wind, solar,
> gas, nuclear and battery were **absent**, so `NEW_ENTRY_COSTS` could not be
> derived from it. Re-fetched the full 3,162-row extract from the OEDI S3 data
> lake (`scripts/data/fetch_nrel_atb.py`, byte-reproducible) and re-committed it
> complete. See `docs/handoffs/ff-1e-entry-cost-atb-wiring-2026-07.md`.

> **EGS extension (2026-07-19, capacity-cost-grounding session):** the four ATB
> EGS classes (NFEGSFlash/NFEGSBinary/DeepEGSFlash/DeepEGSBinary, 696 rows)
> were added as **appended** parts `part11`/`part12` — the FF-1E parts 00-10
> are byte-untouched. Two consequences, both deliberate: (1) row order no
> longer equals a fresh `fetch_nrel_atb.py` regeneration (which would sort the
> EGS rows into the Geothermal block mid-file); `curate_nrel_atb.parse` is
> order-independent (keyed dedup/validation), so this is layout-only. (2) At
> this re-fetch the OEDI source object's float *serialization* had drifted on
> 9/3,162 pre-existing rows (last-digit repr only, e.g. `…5144` vs `…51434`;
> numeric identity verified at rtol 1e-12) — the committed FF-1E bytes were
> kept rather than churning attested parts for ulp noise. A from-scratch
> regeneration therefore reproduces every VALUE but not byte order. ATB 2024
> remains the **final ATB edition** (no 2025/2026 edition exists — verified
> 2026-07-19 against the renamed lab's site and the OEDI listing, which ends
> at `csv/2024/`), so this extract is the current-latest, not a stale vintage.

## What this doesn't cover

- **Compressed-air storage** — not an ATB-covered technology; the model's
  existing DOE LDES Liftoff citation for `compressed_air` stands unchanged.
- **Oil (peaker) FOM** — not a distinct ATB technology; the model's existing
  Lazard/EIA citation for `fixed_om_oil` stands unchanged.
- **WACC/financing differentiation** — ATB does publish per-tech financing
  parameters (excluded here per the parameter filter above); the model's
  single `nominal_discount_rate=0.08` gap is DOCUMENT-AS-LIMITATION per the
  capacity-economics plan and out of scope for this intake.

## Consumers

`scripts/data/derive_entry_costs_from_atb.py` (FF-1E) derives
`NEW_ENTRY_COSTS`, `CCUS_PARAMS` (gas_cc_ccs) and `ATB_TECH_WACC_REAL` from
this extract; `tests/test_atb_entry_cost_consistency.py` asserts the committed
constants equal that derivation (CLAUDE.md rule 23).
`scripts/data/derive_cost_benchmark_envelope.py` (capacity-cost-grounding,
2026-07-19) additionally derives the li-ion `STORAGE_TECHS` costs (4/8 hr
direct, 12 hr via ATB's exactly-linear power/energy split),
`OFFSHORE_WIND_PARAMS`, the EGS `fom_kw_yr`, and — joined with
`data/raw/new-build-cost-benchmarks/benchmarks_2026.csv` — the
literature-envelope `TECH_COST_MULTIPLIERS` low/high capex ratios;
`tests/test_cost_benchmark_envelope.py` asserts those. A future extension can
add ATB's CF rows to also re-derive `base_cf`.
