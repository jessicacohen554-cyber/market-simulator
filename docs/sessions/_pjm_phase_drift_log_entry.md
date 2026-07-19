# Calibration-log entry — fold into `docs/calibration-log.md` under "## Runs" (top), dated 2026-07-15

(Standalone entry file, the `_caiso80_log_entry.md` pattern: the full
calibration-log is too large for the API-only push path from this session;
fold this verbatim as the newest entry and delete this file.)

---

### 2026-07-15 — PJM — DIAGNOSTIC (no solve, no config flip): the PJM-2025 "+1 h phase drift" de-confounded — the 2025 inputs are the CLEANEST year; the drift decomposes into a 2023 wide-extract indexing defect (all columns 1 h late) + a 2022–2024 EIA-930 fueltype-family source defect (all `NG:` columns 1 h early, fixed upstream ~Feb-2025) + a year-invariant ~1 h-early MODEL-side overnight lead (perfect-foresight cycling, the C3c LP-vs-MIP posture seen in phase space) that the 2023 input error was masking; July-2025 coal +1.9 TWh re-confirmed as conduct-by-congestion (in-merit CF 0.83–0.94 vs CEMS 0.47–0.73, NOT price vintage — F923 2025 complete, spread move real — and NOT sub-floor forcing, p5 CF = 0); the real Dominion−AEP premium (+2.8→+7.0 $/MWh 2023→2025, congestion-dominant) has NO model counterpart (model spread 0.0) and forms BELOW the published transfer-interfaces (0 % binding in PJM's own 2025 feed, `pjm_measured_interface_limits` already on and insufficient); NEW owner item: EIA-930 TI 2025 diverges from PJM's tie record by 15 TWh from May-2025 (32.93 vs 17.97; agreed ±0.3 in 2023/24) — the interchange r = −0.164 collapsed with its own benchmark, and on the tie record the model still UNDER-exports every year (−11/−10/−8 TWh); D-1p per-plant cycling instrument built and committed

**Doc:** `docs/DIAGNOSIS-pjm-2025-phase-drift-and-zonal-structure-2026-07.md`
(mechanisms M-1 input-clock repair / M-2 Dominion congestion intake / M-3
overnight commitment inertia, each with pre-committed source-anchored gates —
rule 1). Probes: `scripts/probes/_pjm2025_*.py`,
`scripts/probes/_pjm_d1p_diurnal_cycling.py`. Anchors: PJM `hrl_load_metered`
+ gen-by-fuel feeds (`datetime_beginning_utc`), EIA-930 BALANCE (explicit
hour-ending UTC), the sun (solar-noon centroids), CAMPD CEMS, corrected
`actual_lmp_hourly_PJM.parquet`, PJM hub LMPs (congestion/loss split), PJM
transfer-limits and tie-line records. Scored metrics untouched (shift-
invariant; C3c FAIL stands: 7 vs 59 h > $200); the evening `lmpDeltaHr` band
is ~16–19 % phase artifact, the overnight band is real conduct. EPT-indexed
loaders flagged for M-1: `pjm_net_interchange` / `pjm_zonal_interchange` /
`parse_pjm_shares` (each file carries an ignored `datetime_beginning_utc`
column). Keeper and keepers.json untouched; 2023–2025 only; zero fitted
values; no ScenarioConfig change. Next: hand M-1 (and M-2 scope) to an
Opus solve session per the handoff's spec-then-execute split.
