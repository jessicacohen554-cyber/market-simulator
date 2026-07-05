# ERCOT NP6 HSL upload drop zone — DATA NEEDED (2024/2025)

This directory is the drop zone `scripts/build_ercot_hsl.py` scans for
published ERCOT wind/solar power-production reports (NP4-732-CD/NP4-733-CD
wind, NP4-737-CD/NP4-738-CD solar — the "NP6" HSL family) — see the module
docstring. It is intentionally empty for 2024 and 2025.

**Blocked, 2026-07-05.** ERCOT retired the old MIS report-list download path
(`mis.ercot.com/misapp/GetReports.do`, which now redirects every report —
including "Public" classification ones like NP4-732-CD — to a SiteMinder
market-participant login, HTTP 302 to `smgetcred.scc`) in favor of the new
Data Access Portal (`data.ercot.com` / `api.ercot.com`). That portal's API
requires a free-but-interactive registration at `apiexplorer.ercot.com`
(name + email + accepted terms) to obtain a client ID, subscription key, and
OAuth credentials; every unauthenticated call returns
`HTTP 401 {"message": "Access denied due to missing subscription key."}`.
Both hosts are network-reachable from this environment (no proxy-level 403,
unlike the earlier NP6-576-ER attempts) — the gate is account credentials
this automated session does not hold, not an egress block. Full attempt log:
`docs/ercot-hsl-2024-25-intake-attempt-2026-07.md`.

Also checked: the UMass `nodal-curtailment-analysis` GitHub dataset (the
2023 fallback source) covers 2023 only — no 2024/2025 extension exists
upstream (confirmed by cloning `main` and listing `data/`, 2026-07-05).

To populate once a registered ERCOT API Explorer account (or a manual MIS
download) is available: drop the year's NP4-732/737 (or 733/738) CSV/ZIP
files here (flat or under a `<year>/` subdirectory), then run

    python scripts/build_ercot_hsl.py --year 2024 2025

The builder and `market_sim.data.renewables.hsl_potential_mw` already
support this — no code changes are needed once the files land. Until then
the backcast uses the G7 reference-curtailment-rate gross-up fallback
(`renewables._forecast_uncurtailed_cf`), which is forward-admissible.
