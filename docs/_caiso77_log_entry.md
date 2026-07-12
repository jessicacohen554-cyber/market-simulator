### 2026-07-12 — CAISO — caiso-77 (self-scheduled firm import base): C1-2024 clears, every pre-registered direction confirmed, **PROMOTED to keeper**; C2-2025 print adjudicated against CEMS per the pre-registered basis clause

Executes the caiso-76 session's Task-1 mechanism — the pre-registered probe of
`FINDING-caiso77-c1-cluster-firm-selfschedule-2026-07-11.md` §4. Provenance
note: the original one-shot runner (`caiso77-solve-register`, run 29170225341,
2026-07-11) solved both bundles and printed clean D-diagnostics, then lost the
results at its publish step (the runner token may not push a ref whose new
commits touch `.github/workflows/*` — the PR #2037 auto-merge race put main's
workflow files in the diff). Re-solved this session on
`caiso77-solve-register-v2` (identical recipe; Data-API-only publish, no
`git push`), run 29182026361.

- **caiso-77** (`2026-07-12-caiso-77-firm-selfschedule` + zero-forcing
  ablation twin): single delta on the caiso-76 keeper recipe —
  `caiso_firm_import_selfschedule=True`. The firm/contracted import tranches
  become must-flow at their full shaped capability (pmax × availability — the
  published DMM RA-import × MIC-split level × the measured caiso-73
  revealed-base shape, eford preserved), `MECH_FIRM_IMPORT` attribution: in
  the real market these blocks are self-scheduled or bid at/below $0/MWh
  (CPUC D.20-06-028 RA import must-offer; DMM revealed 4.3–5.9 GW
  self-scheduled overnight base) and flow independent of the spot spread,
  while the model price-gated them at the two G-26 static-fitted Tier-3
  contract-cost proxies ($28/$48) — leaving the contracted base untaken and
  CC_REGULAR running flat overnight (the C1 CC-over/CT-under cluster). Zero
  new free parameters; the two static-fitted firm prices can no longer set
  the margin (pmin = pmax), so the delta strictly REDUCES the fitted surface.
  The exact Manitoba/HQ firm must-flow pattern.
- **A/B vs the caiso-76 keeper (v2.4), every pre-registered direction
  confirmed:** C1 CC_REGULAR 2024 **+7.04 TWh FAIL → in band (clears)**, 2023
  +5.05 → +4.54 TWh (FAIL, magnitude down); C1 all-rows 10/12 → 11/12. C3a
  +22.2/+32.1/+40.7 → +21.8/+29.9/+38.2 % (overnight λ eases as the must-flow
  base backs CC down the merit). C3b NRMSE 0.308/0.427/0.434 →
  0.307/0.408/0.413. C4 gas r 2024 0.805 → 0.834, 2025 0.576 → 0.590 (still
  FAIL). C5a CO₂ 2024 +17.9 → +11.8 %, 2025 +32.7 → +28.3 % (still FAIL).
  C3c unchanged (2023 458 h, 2024 0 h). C6/C7/C8 PASS hold. CT_PEAKER
  volumes unchanged (−2.0/−2.5/−0.8 TWh — the bridge-crowding channel was
  untouched, as pre-registered; lead (c) stays open).
- **C2-2025 gas: −4.1 % CAVEAT → −7.6 % FAIL on the 930-family basis — the
  DISCLOSED counter-move, adjudicated per the FINDING §4 subject-to clause
  against the CEMS same-fleet evidence** (not auto-rejected on the gate
  sign): same-fleet CAMPD CC_REGULAR excess moves +6.22/+11.11/+14.32 →
  **+5.74/+7.58/+12.32 TWh** (2023/24/25) — every year toward the CEMS
  truth, 2025 included; corrected belly/evening online gaps narrow
  (2024 −0.8/−1.3 → −0.5/−1.0 GW, 2025 −1.5/−1.4 → −1.3/−1.1 GW). The
  930-family 2025 actual remains mutually inconsistent with same-year CEMS
  (non-CEMS residual −5 → −8 → −17 TWh across 2023→25); the bench-basis
  rework filed in the caiso-76 FINDING §4 stays open, and C2-2025 carries
  this adjudication note until it lands.
- **PROMOTED per the FINDING §4 pre-registered bar:** C6+C7+C8 PASS; no gate
  regressed with C2-2025 adjudicated as above (all other gates improved or
  held); the targeted C1 2023/24 cluster improved with 2024 clearing. v2.4
  determination stays NOT-YET. Keeper `2026-07-11-caiso-76-hydro-budget` →
  `2026-07-12-caiso-77-firm-selfschedule`; more structurally faithful under
  rule 1 (a measured contract behaviour replaces a fitted price gate's
  dispatch influence). LOYO exemption claimed per the caiso-76 precedent —
  nothing is fit, the mechanism is identical in all years by construction —
  noted for owner review.
- **Registry**: caiso-65 superseded-keeper pair pruned (top-15 retention;
  caiso-69/d690187 precedent; the caiso65 bundle dir stays — probe scripts
  read its `run_config.json` for the recipe base).
- **Open after caiso-77** (priority order per rule 1): C1-2023 residual CC
  +4.54 TWh and the CT_PEAKER evening-ramp under-run (lead (c) — the
  caiso-70 bridge-decrowding channel); the 2025 bench basis rework
  (930-family vs CEMS, covers the C2-2025 print and the C5a-2025 CO₂
  actual); Bay-Area local topology for the 2024/25 C3c tail (QUEUED);
  offer-curve level for the ~+22 % C3a body base (LAST, per rule 1).
