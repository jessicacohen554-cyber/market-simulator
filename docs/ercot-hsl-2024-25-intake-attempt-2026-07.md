# ERCOT NP6 HSL 2024/2025 intake attempt — BLOCKED (2026-07-05)

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
