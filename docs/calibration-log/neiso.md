# Calibration Log — NEISO

Continuation of `docs/calibration-log.md` (frozen archive, entries through
2026-07-19) for NEISO calibration work. Same entry format — `## YYYY-MM-DD — title`,
newest at the BOTTOM. Only this lane's sessions append here, so parallel
per-ISO calibration sessions never conflict (the per-ISO lane convention,
2026-07-19; see `frontend/data/backcast/keepers/README.md`).

## 2026-07-19 — Intake: ISO-NE Morning Report operable-capacity (DAM-equivalent outages/availability)

Data-intake session (no solve, no keeper change). Intaken the ISO-NE **Morning
Report Section 3 Operable Capacity Analysis** — the ISO-NE analogue of ERCOT's
measured DAM class-day availability (`ercot-thermal-dam-availability.csv`): daily
published **Generation Outages and Reductions (Planned + Forced)** and **Total
Available Capacity** MW, 2018-07-01 → present (~2,940 days; parse identity
`H=A+B−C−D+E−F−G` = 0 MW/row). Committed per-year CSVs
`data/raw/neiso-operable-capacity/neiso_operable_capacity_<YYYY>.csv`
(ERCOT-analogue committed-CSV precedent — the API-only push path can't
round-trip binary and carries content inline, so CSV partitioned by year;
`build --parquet` emits a columnar copy locally)
(fetch + build scripts + README + test). New loader
`data.neiso_operable_capacity.neiso_thermal_availability_series` (committed) is
the consumption API; a **default-OFF** gate
`ScenarioConfig.neiso_operable_capacity_availability` + a fleet-builder block
apply the measured fleet thermal availability (`1 − outages/(CSO+EcoMax-above-
CSO)`) by the ERCOT-style bidirectional water-fill, superseding the CAMPD
unit-outage fallback for the covered thermal classes when enabled. The gate +
fleet block ship as `docs/handoffs/patches/neiso-operable-capacity-wiring.patch`
(scenarios.py/fleet.py are ~0.5 MB each — too large for the API push), verified
to apply cleanly onto pristine main and inert when off. Fleet grain only
(ISO-NE publishes no public per-unit outage series). Rule-22 authorization +
registry: `docs/out-of-sample-results-2026-07.md §1.5`; design + admissibility:
`docs/handoffs/neiso-operable-capacity-intake-2026-07.md`. Turning the gate on /
promoting is a future NEISO-lane decision — this session delivers data + opt-in
wiring, verified inert when off.

## 2026-07-19 — gas_daily_shape §3.7 fix A/B: NEISO exactly price-inert (hub overlay supersedes); probes registered

Cross-ISO session (full entry: `docs/calibration-log/governance.md` 2026-07-19
gas_daily_shape §3.7). On the neiso-60 keeper recipe the fix is exactly
price-inert in all three years — the AGT hub-basis daily overlay replaces every
covered gas row, so the national HH shape never reaches NEISO dispatch.
Registered `2026-07-19-neiso-gasshape-interpfix`(+`-base`) as the inertness
record; no keeper action.
