### 2026-07-12 — PJM — KEEPER PROMOTED `2026-07-11-pjm-98-cc-mustrun` replaces `pjm-97-measured-interfaces` (G-21 benchmark-basis re-score; owner-directed)

**Owner decision (2026-07-12): promote pjm-98 to PJM keeper**, resolving the
G-20 §5 over-forcing flag that had held it as a candidate. The decision rests on
the G-21 benchmark-basis finding
(`docs/handoffs/pjm-cc-overrun-benchmark-basis-g21-2026-07.md`): pjm-98's headline
"aggregate CC overshoot" was ~60–90% a **scoring artifact**, not model dispatch.
The old `reconcile_vintage_classes` forced the CEMS-validated EIA-923 gas/coal
split onto EIA-930's unreliable fuel attribution (PJM 930 over-counts coal
+7..+11 TWh/yr, under-counts gas by ~the same), dumping a spurious ~−15 TWh onto
CC_REGULAR's *actual*. The merged fix (combined-family reconcile preserving the
CEMS split, commit 870d6ef; + unit-class CAMPD backfill, aecf00b) corrects the
CC benchmark upward: 2024 CC_REGULAR actual 317.0 → 335.1.

**Corrected-basis re-score (no re-solve).** This clone lacks the measured
`transfer-interface-limits` raw data the keeper recipe needs, so a faithful
re-solve is impossible here; instead the PJM bench parts
(`frontend/data/backcast/bench/PJM/{2023,2024,2025}.json.gz`) had their
`classFull` regenerated on the corrected basis via the production benchmark
helpers (`_benchmark_eia923_frame` with the fixed backfill, `_btm_frame`,
`reconcile_vintage_classes`) — validated against G-21 §2 (2024 CC_REGULAR
335.12 vs target 335.1; 2023 325.67 vs 325.7; CT_PEAKER/ST_GAS match). Only
`classFull` was spliced (deterministic gzip); e930/avgLMP/co2/plants untouched.
Both bundles + both `-ablation` twins were re-scored with
`calibration_verdict.py --write-metrics` (reads committed run payload × corrected
bench parts — the sanctioned #2049 path, no LP touch).

**The fix REVERSES the C1 comparison:**
- **pjm-98 (new keeper): C1 fuel-mix PASS — all 16/16, free 12/12.** target-grade 5 / 4 fails.
- **pjm-97 (old keeper): C1 fuel-mix FAIL** — 2023 CC_REGULAR −11.1 TWh under-run,
  out of band. target-grade 4 / 5 fails. The corrected higher CC actual exposes the
  eastern CC under-run pjm-98's out-of-market commitment floor closes; the deflated
  old benchmark had hidden it.

pjm-98's structural case was already sound (measured eastern-CC LDA/voltage
commitment, rule-13 measured, rule-18 self-targeting, zero fitted DOF, D-4 clean,
C8 forced-share PASS at 5.9–11.6% of CC_REGULAR). Honest residuals that stand:
C7 2023 CT_PEAKER diurnal worsening (off-peak cv_ratio 0.491→0.436) and a small
real 2024 CC over (+3.0→+5.1 TWh on the scored official/classFull basis, well
inside the 8-band — the G-21 draft's CAMPD-column +8.8→+11.0 was a non-scored
comparison actual). Both runs remain determination
**NOT-YET** on the SHARED, unrelated C3 peak price-formation gap (mean LMP /
duration / >$200 tail — G-21 §5/§8), not on this promotion — as pjm-97 was.
Rule-22 LOO clause is vacuous (zero fitted scalars in the pjm-97→pjm-98 delta).
`keepers.json` + both sidecars + status.js updated; keeper-auditor run.
**Remaining #2049 follow-up:** a full-data re-render (co2.byClass, per-plant
tables, all ISOs) where the measured-interface source data lives.
