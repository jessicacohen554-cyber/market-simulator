# ercot-hsl — raw

`ercot_2023_hsl_hourly.parquet`, `ercot_2024_hsl_hourly.parquet`,
`ercot_2025_hsl_hourly.parquet` — uncurtailed-renewable-potential (HSL)
hourly series for all three buildable backcast years. `np6/` holds the
source ERCOT NP4-732/733/737/738/742/745-CD wind/solar power-production
report archives all three years are built from — see `np6/README.md`.

**Source (all three years):** ERCOT's own published NP6 power-production
reports, full-footprint system-wide totals — consumed directly, no
reconciliation. 2024/2025 from NP4-732-CD (wind) / NP4-737-CD (solar)
"Hourly Averaged Actual and Forecasted Values"; 2023 from the
by-geographical-region variants NP4-742-CD (wind) / NP4-745-CD (solar)
(owner upload 2026-07-22, `np6/2023/`), whose per-region HSL is the COP HSL
(no actual-HSL column in the GEO family). The 2023 NP6 upload **superseded**
the prior UMass `nodal-curtailment-analysis` reconstruction
(<https://github.com/codecexp/nodal-curtailment-analysis>, Maji, Irwin,
Shenoy, Sitaraman, ACM e-Energy 2025) — a partial-footprint derived source
the renewables loader had to reconcile up to the EIA-930 delivered level;
the NP6 2023 delivered totals match EIA-930 directly (wind 108.0 vs 108.0
TWh, solar 31.9 vs 31.9 TWh), so the reconciliation is now a no-op for every
year. (The UMass fallback path remains in the builder for a tree with no
2023 NP6 upload.) See `np6/README.md` for provenance, coverage, and the one
cited known-bad source window.

`ercot_<year>_hsl_zonal_hourly.parquet` — the per-region **zonal sidecar**
(long format: `hour`, `fuel`, `region`, `gen_mw`, `hsl_mw`) built in the
same pass from every upload that carries per-region columns: the GEO
report families (wind `panhandle`/`coastal`/`south`/`west`/`north`, solar
`centerwest`/`northwest`/`farwest`/`fareast`/`southeast`/`centereast`) and
the NP4-732 wind load-zone columns (`lz_south_houston`/`lz_west`/
`lz_north`). Per-region `hsl_mw` is the report's **COP HSL** (aggregated
operating-plan HSLs of On-Line resources — no NP6 family publishes a
per-region telemetered actual HSL); hours outside a region vocabulary's
posted coverage are NaN, never interpolated across month-scale holes.
2023 has full-year coverage of both GEO vocabularies (sum-of-regions
reproduces the system-wide delivered total to 1.0000); 2024/2025 carry the
full-year wind LZ split plus scattered GEO months.

**Regeneration:** `scripts/data/build_ercot_hsl.py --year 2023 2024 2025`
(add `--zonal-only` to refresh sidecars without rewriting the system-wide
parquets).

**Consumer:** `market_sim.data.renewables` (HSL loader) for the system-wide
parquets; the zonal sidecar is a diagnostics input (ERCOT-98 scarcity/
deliverability lane), not yet a dispatch input.

## 2018–2022 / H1-2026 holdout intake — confirmed ungettable (2026-07-10)

Checked for this rule-22 holdout intake and found **blocked**, not merely
unattempted: ERCOT's Data Access Portal (`data.ercot.com/data-product-archive/NP4-732-CD`)
is a JavaScript SPA behind Incapsula bot-protection that requires an
authenticated sign-in for any historical archive — confirmed by direct
fetch (302 redirect to a login-gated `/error/404-not-found` route for
anonymous requests; the static HTML payload is just the SPA shell). The
live rolling-window listing API (`ercot.com/misapp/servlets/IceDocListJsonWS`)
returns an empty document list for this report type from this environment,
and even where it does return recent documents (tested against a
neighboring report family) it only retains a short rolling window, not
2018–2022 history. This matches the precedent already on file: the 2024/2025
NP6 uploads in `np6/` were pulled by hand through an `apiexplorer.ercot.com`
account the owner registered — not a script-reproducible path — and
`data/raw/iso-specific-transmission/README.md` documents the same
Data-Portal-sign-in wall for the neighboring NP6-86-CD product.

The UMass `nodal-curtailment-analysis` fallback used for 2023 (see above) is
**2023-only by construction** — confirmed by cloning the dataset directly:
its `data/` directory contains only `*-2023.csv` files, derived from a
one-time per-plant reprocessing of ERCOT's 60-Day SCED Disclosure Reports
for that single paper. Extending it to other years would mean redoing that
per-plant 15-minute reconstruction from raw SCED disclosures — a new
derivation project, not a fetch, and out of scope for this holdout intake
(same category as "NYISO/MISO don't publish hourly per-plant HSL at all").

**Net: no new ERCOT HSL years were added.** 2018–2022 and H1-2026 remain
unfetchable without ERCOT Data Portal credentials this session does not
have.
