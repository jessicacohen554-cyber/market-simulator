# Calibration Log — NYISO

Continuation of `docs/calibration-log.md` (frozen archive, entries through
2026-07-19) for NYISO calibration work. Same entry format — `## YYYY-MM-DD — title`,
newest at the BOTTOM. Only this lane's sessions append here, so parallel
per-ISO calibration sessions never conflict (the per-ISO lane convention,
2026-07-19; see `frontend/data/backcast/keepers/README.md`).

## 2026-07-19 — gas_daily_shape §3.7 fix A/B: NYISO exactly price-inert (Transco hub overlay supersedes); probes registered

Cross-ISO session (full entry: `docs/calibration-log/governance.md` 2026-07-19
gas_daily_shape §3.7). On the nyiso-62/63 recipe the fix is exactly
price-inert in all three years — the Transco Z6 NY / Iroquois hub-basis daily
overlay replaces every covered gas row. Registered
`2026-07-19-nyiso-gasshape-interpfix`(+`-base`) as the inertness record; no
keeper action (the NYISO keeper advanced mid-session to nyiso-64-outage-refix,
whose gas path uses the same overlay, so the inertness conclusion transfers).

## 2026-07-20 — phantom nyiso-65 keeper diagnosed + resync keeper nyiso-66-resync-base

The NYISO keeper `2026-07-19-nyiso-65-scr-edrp` was MIA on the Run Explorer and
scored "not calibrated" because it was a **phantom registration**: only the
registry sidecar + keeper pointer were committed; its run payload
(`runs/<id>.js`) and solve bundle (`results/calibration/nyiso65_scr_edrp/`)
appear in **0 commits** (register commit `b9caa32` said "remaining files
follow" — they never did). Tracked in `scripts/lib/known_unsynced_keepers.py`.
The nyiso-65 recipe is **not reproducible from the tree**: two of its three
defining ingredients were also never committed — the `nyiso_scr_edrp` SCR/EDRP
demand-response lever (`src/market_sim/data/nyiso_demand_response.py` is
orphaned: imported nowhere, not a `ScenarioConfig` field, not a
`solve_and_persist` param; its data-build `scripts/data/build_nyiso_scr_edrp.py`
is un-synced) and the 2,641-row corrected `campd-unit-outages-NYISO.csv` extract
(the tree carries 1,599 rows). Only the eastern-seam `Capital_Hudson 1,600 MW`
landing (code-level) is on the tree.

Action: removed the Frontier designation from the keeper shard; re-solved the
**reproducible on-tree base** — the nyiso-62 `cc_hr_regate` meta replay
(`replay_keeper.py`) across 2023-2025 — and registered
`2026-07-20-nyiso-66-resync-base` as the new keeper (real, committed artifacts:
payload + slim bundle + `hourly/` sidecars + attestation +
`legitimacy_diagnostics.json`). Deleted the phantom nyiso-65 sidecar; dropped
nyiso-65 from `known_unsynced_keepers`. **DETERMINATION NOT-YET**: C1 fuel-mix
FAIL (13/14, 2023 CC_REGULAR −3.76 TWh), C3b price-shape FAIL (2024 NRMSE
0.201), C3c tail FAIL; C3a mean-LMP PASS all years (2023 +8.8%, 2024 −7.2%,
2025 −8.1%); C2/C4 PASS; C6/C7/C8 PASS (C8 ST_GAS grounded-above-budget); C5a
CO₂ commercial-band caveat (2025 +9.5%). Closing C1/C3b requires **restoring the
un-synced nyiso-64/65 ingredients** (wire the DR lever into the engine +
re-derive the 2,641-row outage extract & ST reliability floors) — the named
follow-up.
