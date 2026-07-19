# Calibration Log — PJM

Continuation of `docs/calibration-log.md` (frozen archive, entries through
2026-07-19) for PJM calibration work. Same entry format — `## YYYY-MM-DD — title`,
newest at the BOTTOM. Only this lane's sessions append here, so parallel
per-ISO calibration sessions never conflict (the per-ISO lane convention,
2026-07-19; see `frontend/data/backcast/keepers/README.md`).

## 2026-07-19 — PJM keeper advanced: pjm-115 recipe on the gas_daily_shape §3.7 true-date fix (CALIBRATED)

Cross-ISO session (full entry: `docs/calibration-log/governance.md` 2026-07-19
gas_daily_shape §3.7). The pjm-115 unit-only-outages recipe replayed on the
fixed national HH daily shape (+ the inherited +1h frame fix): annual mean LMP
Δ ≤$0.01 every year, spike-day relocation only (2024 max |Δ| $81/MWh in the
Heather weekend), **CALIBRATED — every scored criterion PASS**. Keeper →
`2026-07-19-pjm-gasshape-interpfix` (owner-authorized in-session); same-box
base `2026-07-19-pjm-gasshape-interpfix-base` registered. Next number in this
lane: unchanged (this is the cross-ISO correctness lane, not a pjm-N session).
