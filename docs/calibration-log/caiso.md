# Calibration Log — CAISO

Continuation of `docs/calibration-log.md` (frozen archive, entries through
2026-07-19) for CAISO calibration work. Same entry format — `## YYYY-MM-DD — title`,
newest at the BOTTOM. Only this lane's sessions append here, so parallel
per-ISO calibration sessions never conflict (the per-ISO lane convention,
2026-07-19; see `frontend/data/backcast/keepers/README.md`).

## 2026-07-19 — gas_daily_shape §3.7 fix A/B on the caiso-97 recipe: 2025-only, small; probes registered, no keeper action

Cross-ISO session (full entry: `docs/calibration-log/governance.md` 2026-07-19
gas_daily_shape §3.7). On the caiso-97 recipe the fix is price-identical in
2023/2024 (the measured citygate daily overlay supersedes the national HH
shape) and small in 2025 (mean −$0.04, 207 hours >|$1|, max |Δ| $22).
Registered `2026-07-19-caiso-gasshape-interpfix`(+`-base`) as probes only —
the CAISO keeper advanced to caiso-102-hourfix mid-session (PR #2563), so no
keeper recommendation from this A/B; the fix itself is on main and any future
CAISO solve carries it.
