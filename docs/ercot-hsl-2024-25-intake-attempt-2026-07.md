# ERCOT NP6 HSL 2024/2025 intake — COMPLETE (2026-07-06)

**Update 2026-07-06 (final).** The credentialed-fetch route below remains
closed per the owner decision in `docs/handoffs/ercot-as-coopt-plan-2026-07.md`
§WS-E (re-verified this session: `apiexplorer.ercot.com`, `api.ercot.com`,
and the legacy MIS path all return the identical 302/401 gate as before).
Separately, the owner manually downloaded ERCOT NP6 reports through the
Data Access Portal UI (not the API) and uploaded them straight to the repo
— a different, already-authorized mechanism than the closed credentialed
fetch. In two rounds the owner supplied full 24/24-month coverage for both
fuels and both years: solar (NP4-737) landed first (complete immediately);
wind initially covered only 2024-05 and 2024-09 (the latter via the NP4-742
by-geography variant, which carries the identical system-wide actual/HSL
column pair as plain NP4-732), then the remaining 22 wind-months landed in
a second upload (2024: all except 05/09; all of 2025).

The uploaded archives also turned out to be a zip-of-zips (one outer
monthly zip of ~700+ per-posting zips, each with one CSV) that
`scripts/build_ercot_hsl.py`'s single-level `_read_csvs` couldn't parse at
all; fixed to recurse to arbitrary depth. Files were relocated from the
top-level `data/raw/ercot-hsl/` into the `np6/<year>/` drop-zone the
builder scans (one redundant solar-geo file, NP4-745 Nov-2024 — already
fully covered by NP4-737 — was set aside under `np6/unused-redundant/`
rather than blended in).

**`python scripts/build_ercot_hsl.py --year 2024 2025` now builds both
years cleanly** (8,760/8,760 hours, no gaps). Validation vs the EIA-923
calibration reference (`data/raw/_validation-source/calibration_reference.json`):

| year | fuel | HSL-source delivered | EIA-923 | delta |
|---|---|---|---|---|
| 2024 | wind | 115.67 TWh | ~112 TWh | +3.4% |
| 2024 | solar | 48.84 TWh | ~40 TWh | +21.9% |
| 2025 | wind | 114.94 TWh | ~115 TWh | −0.2% |
| 2025 | solar | 67.52 TWh | ~56 TWh | +21.0% |

Wind matches EIA-923 tightly in both years — strong evidence the parse/
aggregation pipeline (including the new recursive zip-of-zips fix) is
correct. Solar runs consistently high, but the *existing* 2023 UMass-
sourced file shows the same direction of bias (+11.1% vs the EIA-923
2023 reference), so this reads as a real, pre-existing divergence between
ERCOT's settlement-metered NP4-737 solar telemetry and EIA-923's own
figure (plausibly EIA-923's monthly-survey reporting lag against Texas's
fast-growing utility-scale solar fleet), not a parsing defect — magnitude
grew from 2023→2024/2025 in the same direction as the state's solar
buildout accelerated. Per rule 14, the measured NP4-737 data is kept as-is
(no retuning to the EIA-923 level): `hsl_potential_mw`'s coverage
reconciliation is one-directional (scales a source *up* only when it
*undercounts* EIA-930 delivered; it never scales a source down), so this
divergence flows into the model unmodified, exactly as the published
full-footprint HSL upload is designed to. Flagged here as an open,
documented fidelity note — not a blocker, not something to chase with a
coefficient.

The two new parquets (`ercot_2024_hsl_hourly.parquet`,
`ercot_2025_hsl_hourly.parquet`) supersede the G7 reference-curtailment-
rate gross-up for ERCOT 2024/2025 the moment they're committed —
`renewables.hsl_potential_mw` reads the raw per-year parquet directly by
default, no further wiring needed. `data/clean` is gitignored/derived and
unused by default (`MARKET_SIM_USE_CLEAN` unset), so no clean-tree
regeneration was required for this to take effect.

**Scope.** WS-E of `docs/handoffs/ercot-as-coopt-plan-2026-07.md` / P4 remainder
of `docs/forecast-methodology-gaps-2026-06.md` G7: intake the published ERCOT
NP4-732/737 (wind/solar HSL) reports for 2024 and 2025 so
`renewables.hsl_potential_mw` stops falling back to the reference-curtailment-
rate gross-up (`_forecast_uncurtailed_cf`) for those years. **Result: blocked
on ERCOT account credentials this environment does not hold — the same
outcome as the prior NP6-576-ER attempts (`docs/ordc-overlay.md`), documented
here per the plan's egress caveat.** The G7 fallback is unchanged and remains
the ERCOT 2024/25 default; no code or data changed.

## What was tried

1. **Legacy MIS report list** — `mis.ercot.com/misapp/GetReports.do?
   reportTypeId=13028` (NP4-732-CD's report type, "Public" security
   classification per the product metadata). Returns `HTTP 302` to
   `mis.ercot.com/siteminderagent/cert/.../smgetcred.scc?SMQUERYDATA=...` — a
   SiteMinder market-participant login wall, regardless of the report's public
   classification. This is the same wall the ercot27 WS3 / NP6-576-ER
   attempts hit.

2. **New ERCOT Data Access Portal** — `www.ercot.com/mp/data-products/
   data-product-details?id=NP4-732-CD` (200 OK, reachable) links to
   `data.ercot.com/data-product-details/np4-732-cd`, a React SPA that calls
   `api.ercot.com/api/public-reports/np4-732-cd`. Every call to that API —
   with or without the `emilId` path segment, with or without query params —
   returns:

       HTTP 401
       {"statusCode":401,"message":"Access denied due to missing subscription
       key. Make sure to include subscription key when making requests to an
       API."}

   Per ERCOT's own developer docs (`developer.ercot.com/applications/pubapi/
   user-guide/registration-and-authentication/`), obtaining a subscription
   key requires registering an account at `apiexplorer.ercot.com` (name,
   email, accepted Terms of Use), then authenticating via OAuth against
   ERCOT's Azure B2C tenant using that account's username/password to mint a
   bearer token, which is sent alongside the subscription key on every call.
   This is an interactive account-creation step (email-verified) that cannot
   be completed by this automated session — the same class of blocker as the
   legacy SiteMinder login, just on newer infrastructure.

3. **60-Day SCED Disclosure Reports (NP3-965-ER)** — the underlying per-plant
   telemetry the UMass 2023 fallback dataset (below) was itself built from.
   Checked whether this data product uses a different, unauthenticated path:
   it resolves to the identical `data.ercot.com/data-product-details/
   np3-965-er` → `api.ercot.com` gate. No unauthenticated route exists for
   finer-grained reconstruction either.

4. **UMass `nodal-curtailment-analysis` GitHub dataset** (the existing 2023
   fallback source in `scripts/build_ercot_hsl.py`) — shallow-cloned `main`
   and listed `data/`: every file is suffixed `-2023`; there is no 2024 or
   2025 extension upstream. The repository's README point of contact
   (`dmaji@cs.umass.edu`) is a candidate for a future manual ask, not
   something this session can act on.

**Not a network-level block.** Unlike the prior NP6-576-ER attempts (all
hosts 403 through the egress proxy), `ercot.com`, `data.ercot.com`, and
`api.ercot.com` are all directly reachable (200s on the HTML pages, a clean
401 with a JSON error body from the API — not a proxy-shaped failure). The
proxy status endpoint (`$HTTPS_PROXY/__agentproxy/status`) shows no recent
relay failures. The gate is ERCOT's own authentication requirement, which
this session has no credentials to satisfy.

## Disposition

Per the plan's egress caveat: this is a fidelity upgrade, not a stage-4
blocker. `renewables._UNCURTAILED_FALLBACK_ISOS` / `_forecast_uncurtailed_cf`
already give ERCOT 2024/25 a forward-admissible uncurtailed potential (EIA-930
delivered profile grossed up by the 2023 HSL year's reference curtailment
rate), so the LP still curtails endogenously and the AS-driver series
(`ercot_as_forward_drivers`) are internally consistent, just built on the
gross-up rather than a measured per-year HSL series. No driver-delta
comparison was run here since no new 2024/25 HSL data landed to compare
against — see "Carried consequence" below.

**No code or data changed.** `scripts/build_ercot_hsl.py` already handles a
2024/2025 NP6 upload transparently (`aggregate_np6_hourly` + the `np6/<year>/`
drop-zone convention) — the builder needs no changes once files land. A
placeholder `data/raw/ercot-hsl/np6/README.md` documents the drop zone and
points here.

**To retry:** either (a) a human registers an ERCOT API Explorer account and
either downloads the NP4-732/737 CSV/ZIP files manually and drops them under
`data/raw/ercot-hsl/np6/`, or hands this session a subscription key +
bearer-token credential pair to script the API pull, or (b) the UMass team
publishes a 2024/2025 extension of their nodal-curtailment dataset. Either
unblocks `python scripts/build_ercot_hsl.py --year 2024 2025` with no further
code changes.

## Carried consequence (stage 4 note)

The AS-forward-requirement drivers (`scarcity.ercot_as_forward_drivers`:
net-load, `sigma_fe`, `ramp_up` percentiles) and the WS-A net-load-percentile
online shares continue to be built from the gross-up profile for 2024/25
rather than a measured HSL series — curtailment is still baked out endogenously
by the LP (the gross-up is a valid *potential*, not delivered-net CF), so the
drivers are not using curtailment-suppressed variability; they are simply
built on a reference-year-derived rate rather than the year's own measured
curtailment shape. This is an open fidelity gap to revisit if a credentialed
fetch becomes possible, not a blocker for the stage-4 `ercot40` integration
run, which proceeds on the existing G7 fallback per the plan.
