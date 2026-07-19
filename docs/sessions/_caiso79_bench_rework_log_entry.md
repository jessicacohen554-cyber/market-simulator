### 2026-07-12 — CAISO — bench-basis rework EXECUTED (930-NG FINDING §5, owner-signed): CEMS-anchored fossil actual, caiso-78 + twin re-scored in place — C4-2024 flips PASS, C5a-2025 +25.0→+14.6%, C2-2025 −10.2% under → +19.3% over (honest), **C1 CC reopens FAIL (+7.7/+10.6 TWh) as pre-registered**

Owner sign-off obtained this session on the
`FINDING-caiso-c2c4-bench-basis-930ng-2026-07-12.md` §5 design: scorer/bench
layer, CAISO only, NO re-solve. The CISO EIA-930 NG cell carries a growing
noon-peaked solar-shaped block from ~2024-05 (+4.2/+7.9 TWh unexplained in
2024/25 vs CEMS + cogens + fold-in); the G-21 combined reconcile was scaling
the whole CAISO fossil classFull to it (×1.104/×1.211/×1.438).

- **Mechanics** (all committed, rule 23: benchmark-data correction citing a
  demonstrated source defect, never a residual-chase):
  `render_calibration_html` writes CEMS-anchor fields into the CAISO bench
  `e930` (`gas_cems_grid` = CAMPD-net bench-gas − BTM; `gas_cogen_grid` = the
  923 non-CEMS gas-class block, 2025 carrying 2024's complete-vintage block;
  `fossil_cems_grid` = + the 923 coal grid block) and
  `reconcile_vintage_classes` CAPS the combined reconcile at the anchor for
  `EIA930_NG_CELL_CORRUPT = {CAISO}` (one-directional; other ISOs carry no
  anchor and are byte-unchanged). `calibration_verdict`: the C2 gas
  preliminary fallback gates on the anchor instead of the 930 cell; C4 gas
  r/NRMSE is recomputed from the committed hourly series (payload
  `plants[].m` vs bench `plants[].campd` + flat cogen block) from vintage
  2024 (2023 keeps 930 — the bases agree pre-onset); the C5a preliminary
  vintage is rebuilt at complete coverage (full-plant fossil scaled to the
  CEMS anchor before the intensity multiply — the caiso-76 §4 filing).
  `scripts/regen_caiso_bench_cems.py` splices the three committed parts
  (guards: the UNCAPPED recompute must reproduce the committed classFull;
  the CEMS gas block must match the FINDING §3 measured values). Tests:
  `TestCemsAnchorCap` (4) + CEMS sysvol/dispatch-corr verdict tests (5).
- **Bench moves**: classFull CC_REGULAR 57.21/55.64/53.84 →
  **51.84/45.99/40.59** TWh (2023/24 land inside the ±3% deadband of the
  anchor — no scale at all; 2025 scales ×1.084 to the anchored 51.67 instead
  of ×1.438 to the corrupt 68.53); 2025 CO2 actual 21.68 → 23.65 Mt
  (complete-coverage rebuild).
- **caiso-78 re-score** (`calibration_verdict.py --write-metrics`, keeper
  unchanged, v2.4 determination stays NOT-YET): C4 gas r/NRMSE
  0.888·0.249 PASS / **0.899·0.279 PASS** (was FAIL-family) / 0.829·0.38
  (r floor clears; 2025 now FAILs on NRMSE alone = the honest ~+10 TWh level
  miss, not the noon corruption). C5a +3.2% PASS / +9.1% CAVEAT / **+14.6%**
  (was +25.0 on the understated actual). C2-2025 **+19.3% over** (was −10.2%
  fabricated under) — the same story C1 tells. **C1 CC_REGULAR +2.32/+0.97
  → +7.69/+10.62 TWh FAIL (2023/24)** — the pre-registered rule-14
  counter-move, disclosed at sign-off: the inflated actual was flattering
  the CC level; the CC lane reopens honestly (twin: +8.48/+12.12). C7
  CT_PEAKER drops below the 2% materiality floor on the honest actuals
  (SKIPPED — reported, not gated; D-1 profile r 0.899/0.822/0.724). C6/C8
  PASS hold. All other C1 classes in band (10/12 cells).
- **Reading**: four bench-side FAILs are retired or honestly re-based
  (C2-2025, C4-2024, C4-2025, C5a-2025), and the ONE real model miss is now
  visible on a single consistent basis — ~8–11 TWh/yr of model CC the
  measured fleet didn't run, the same root-cause family as the C3a/C3b body
  overprice. That is the open CC/price-formation lane (caiso-79 plan §4
  decomposition), NOT a reason to revert the honest benchmark (rule 14).
  Earlier CAISO bundles' metrics sidecars predate this rework and re-score
  on the new basis only when next touched.
