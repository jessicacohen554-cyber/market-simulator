# ercot-hsl — raw

`ercot_2023_hsl_hourly.parquet`, `ercot_2024_hsl_hourly.parquet`,
`ercot_2025_hsl_hourly.parquet` — uncurtailed-renewable-potential (HSL)
hourly series for all three buildable backcast years. `np6/` holds the
source ERCOT NP4-732/733/737/738-CD wind/solar power-production report
archives 2024/2025 are built from — see `np6/README.md`.

**Source (2023):** not ERCOT's own data — cloned from the UMass
`nodal-curtailment-analysis` public dataset,
<https://github.com/codecexp/nodal-curtailment-analysis> (Maji, Irwin,
Shenoy, Sitaraman, ACM e-Energy 2025), a partial-footprint reconstruction the
renewables loader reconciles up to the EIA-930 delivered level. Used only
because no NP6 upload covers 2023; would be superseded by a published
NP4-732/737 upload in `np6/2023/` if one ever lands.

**Source (2024/2025):** ERCOT's own published NP4-732-CD/NP4-742-CD (wind)
and NP4-737-CD (solar) "Power Production — Hourly Averaged Actual and
Forecasted Values" reports, full-footprint system-wide totals — consumed
directly, no reconciliation. See `np6/README.md` for provenance, coverage,
and the one cited known-bad source window.

**Regeneration:** `scripts/build_ercot_hsl.py --year 2023 2024 2025`.

**Consumer:** `market_sim.data.renewables` (HSL loader).

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
