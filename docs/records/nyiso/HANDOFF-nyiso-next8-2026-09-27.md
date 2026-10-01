# HANDOFF — NYISO-NEXT-8

```
SESSION NYISO-NEXT-8: fix the HQ double count in NYISO's import-ladder derivation (a rule-14 derivation correction, zero DOF), A/B it against the keeper on every registered year, and promote on structure if its gates pass. Phase 0 is ZERO LP. This parent never runs an LP (rule 32); any solve is year-isolated shards (rule 36).
DATA PROFILE: nyiso
MODEL: Opus or Fable (rule 27)

FIRST: archive the previous NYISO session (NYISO-NEXT-7) once its PR is confirmed on main.

READ FIRST. CLAUDE.md is binding, especially rules 1, 13, 14, 19, 21, 23, 24, 25, 28, 31, 32, 34, 35 and 36.
- docs/FINDING-nyiso-next7-star-node-2026-09-27.md (sec. 2 eastern over-delivery; sec. 3 why per-neighbour routing is refused; sec. 4 the HQ double count)
- results/calibration/_nyisonext7_phase0.json and scripts/probes/nyisonext7_star_node_phase0.py
- docs/RESULT-nyiso-next6-li-posted-limit-2026-09-27.md
- docs/FINDING-nyiso-next4-c3a-decomposition-2026-09-26.md
- scripts/data/derive_nyiso_import_tranches.py (EXTERNAL_SEAMS["HQ"] lists SCH - HQ_IMPORT_EXPORT)
- src/market_sim/data/nyiso_par_attribution.py (ACCOUNTING_DUPLICATE already excludes that row)
- src/market_sim/model/interchange/spec.py: IMPORT_TRANCHES["NYISO"] and IMPORT_TRANCHES_BY_YEAR["NYISO"] (2018-2025)
- NYISO matrix shard docs/codebase-site/data/mechanism-matrix/NYISO.js: import_hub_pricing (K, the defect is in its ev), nyiso_firm_imports, seam_neighbour_anchored_ladder (G, do not re-test without the neighbour-price intake). NYISO lever queue: docs/mechanism-testing-matrix.md sec. 5.5 (NYISO-NEXT-7 queue update).

STATE
- Keeper: 2026-09-27-nyisonext6-li-cap-span (bundle results/calibration/nyisonext6_span) plus the stamped 2021 run. Determination NOT-YET.
- Load-bearing failures: C3a 2022 -11.5 %, 2025 -10.9 %. C3c also fails, but not as the lone failure.
- NEXT-7 measured (zero LP):
  - The committed ladder is derived on a net import that counts HQ twice. Derivation net 3,979 / 3,786 / 2,694 / 2,146 / 1,671 MW vs true 3,108 / 3,080 / 2,546 / 2,360 / 2,197 MW (2021-2025).
  - SCH - HQ_IMPORT_EXPORT correlates 0.977-0.993 with SCH - HQ - NY in every year.
  - Offline re-derivation without the duplicate: 2022 rungs rise (top $126.79 -> $174.89); 2025 low rungs fall ($31.32 -> $20.40) and high rungs rise.
  - Separately, the keeper over-delivers import east of Central-East by 4.85-7.60 TWh/yr. That object needs neighbour prices the repo lacks; it is NOT this lane's lever.

TASK
1. G-DRIFT from the keeper's git_sha (671fa815) to your HEAD, written into your PRECOMMIT before any solve.
2. Phase 0, zero LP.
   - Confirm the duplicate on 2018-2025, not only 2021-2025.
   - Decide ex ante whether the fix is (a) drop HQ_IMPORT_EXPORT from EXTERNAL_SEAMS["HQ"], or (b) import ACCOUNTING_DUPLICATE from nyiso_par_attribution so the two cannot drift again. One mechanism (rule 19).
   - Re-derive every IMPORT_TRANCHES_BY_YEAR["NYISO"] year and the pooled static entry. Cite the defect, not a residual (rule 23).
   - Report the offline reproduction score (offline_score) old vs new per year.
   - Check that the HQ_hydro firm base (900 MW, always-on floor) is still below the measured lightest-import hour. HQ ran net NEGATIVE in 2024-2025 (-176 / -508 MW mean on SCH - HQ - NY). If the floor now exceeds measured, say so and route it; do not tune it.
3. The derivation fix replaces measured inputs rather than adding a mechanism.
   - Decide in the PRECOMMIT whether it lands as a gated default-off field (rule 28(c): matrix row plus a cell in every shard) or as a direct correction of the committed ladder with a keeper re-solve. Justify the choice.
   - Fix footprint, gates and promotion rule ex ante. Promotion is on structure (rule 1), never on C3a moving.
4. Launch one shard per registered year 2021-2025 (rules 34/36). Each shard pushes its full bundle, including dispatch/<y>_P1.parquet, via a .gitignore negation and a plain git add.
   - Compose at zero LP.
   - Score against the keeper (G-CTRL form 4).
   - Promote per rule 35 if the structural gates pass. Otherwise keep every bundle, state where each is, and ask the owner the promotion question (rule 31).
5. Archive every shard once its bytes are in hand (rule 33). Open a PR and merge it. If CI is red only on known base-red, comment once, then merge.
6. If C3a 2022/2025 still fail, draft the next handoff. Remaining named objects:
   - eastern over-delivery (needs intake of the IESO hourly price, PJM LMP at the NYIS interface and the Neptune/HTP/VFT source pnodes, and ISO-NE LMP at the NY external nodes, 2021-2025);
   - the >$300 RT tail (nyiso-242: worth $5.44/MWh in 2022, foreclosed by idle sub-gate capacity);
   - the in-city commitment requirement (MyNYISO access is owner-held);
   - the 2025 downstate level shortfall.

REPORT: numbers only for phase 0 and gates per year, the verdict, the PR number and the next handoff.
```
