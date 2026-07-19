### 2026-07-13 — RUBRIC v2.5 (owner amendment): C2 gates ONLY fully-reported EIA-923 families — the preliminary-vintage fallback (G-21b 930-derived / CAISO CEMS anchor) becomes a SKIPPED diagnostic; CAISO/PJM/MISO keepers + twins re-scored in place (C2 → PASS on all six); CAISO run explorer pruned to the caiso-80 pair (pre-honest-demand runs cleared)

Owner ruling (caiso-80 session follow-up): **EIA-923 is the C2 source of
truth.** For complete vintages C2 already worked that way — the family row
auto-PASSes and volume is governed per-class by the C1 universal gate. But a
preliminary vintage (incomplete 923 booking — every ISO's 2025) fired a
family **fallback gate** instead: the G-21b 930-derived family total
(PJM/MISO/ERCOT/…) or the CEMS anchor (CAISO, the corrupted-NG-cell ISO).
That fallback — not 923 — is what printed the caiso-80 C2-2025 −6.6 % FAIL,
and an incomplete benchmark can fabricate a miss in either direction, so per
the owner it is evidence, not a gate — the same treatment C1 already gives
incomplete classes ("not gated; re-gates when the final vintage lands").

- **Scorer change** (`scripts/calibration_verdict.py`, RUBRIC_VERSION 2.4 →
  2.5): both preliminary-family fallback paths in `score_sysvol` (the
  CEMS-anchor branch and the generic G-21b/930 branch) now emit
  **SKIPPED diagnostic rows** — the comparison numbers stay printed
  (model, fallback actual, magnitude, source) but never gate. Fully-reported
  families are unchanged (PASS, governed by C1). Tests updated to the v2.5
  contract (`tests/test_calibration_verdict.py::SysVolTests`, 119 pass).
- **Re-scored in place** (scorer-only, no LP — the bench-rework precedent):
  the current CAISO, PJM, and MISO keepers and their zero-forcing twins —
  `2026-07-13-caiso-80-supply-demand`(+twin) C2 FAIL → **PASS** (2025 gas
  −6.6 % now diagnostic), `2026-07-11-pjm-98-cc-mustrun`(+twin) C2 →
  **PASS** (2025 gas +1.1 % / coal +5.8 % diagnostics),
  `2026-07-13-miso-62-bit-takeorpay`(+twin) C2 → **PASS** (2025 gas −6.8 % /
  coal +4.0 % diagnostics). All determinations remain NOT-YET on their price
  gates; other ISOs' sidecars re-score on the new rubric when next touched.
- **CAISO run-explorer prune (owner directive):** every CAISO registry entry
  before caiso-80 is cleared — 13 entries (caiso65-statmode, the
  caiso-72/73/75/76/77/78 pairs), 26 sidecar+payload files. Those runs
  solved on the corrupt 930 Demand cell and are not comparable to the
  supply-consistent-basis lineage that starts at caiso-80; their bundle
  dirs, FINDINGs, and calibration-log entries remain the historical record.
- Files: this entry; the v2.5 scorer + tests; the six re-scored
  `metrics.json` sidecars; the pruned registry; `status.js` rebuilt.
