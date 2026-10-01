# HANDOFF — NYISO-NEXT-9 (written by NYISO-NEXT-8, 2026-09-27)

This file is the prompt NYISO-NEXT-8 launched NYISO-NEXT-9 with, committed so the chain is auditable.

```
SESSION NYISO-NEXT-9: the 900 MW HQ_hydro always-on firm-import floor — a rule-17 [R-FLOOR-WINDOW] question routed by NEXT-8 — identified at zero LP, then (only if a zero-DOF structural correction is identified) A/B'd against the keeper on every registered year and promoted on structure if its pre-registered gates pass. Phase 0 is ZERO LP. This parent never runs an LP (rule 32); any solve is year-isolated shards (rule 36).
DATA PROFILE: nyiso
MODEL: Opus or Fable (rule 27)

FIRST (standing owner directions — do these every session and pass them to every chained handoff verbatim):
1. Archive the previous NYISO session (NYISO-NEXT-8, session_01PSE3PknCuETEzvQjKV3EvQ) once its PR #6810 is confirmed merged on main. If #6810 is still open, drive it (it is NEXT-8's promotion PR; the only known red is the WARN-only FR-21 job, red on another lane's stale CAISO gate-(a) row) — do not redo its change.
2. Check for any unmerged branches or PRs for NYISO; determine if anything needs to be salvaged; integrate it into your branch and close the open PRs, or state what can be deleted (a session cannot delete refs — list them for the owner). Rebase and merge.
3. When done: promote if a good candidate (per the pre-registered rule), create a PR and merge, archive every shard, and launch the next handoff to continue NYISO calibration if rubric failures remain. Give that handoff these same standing directions, including: archive its predecessor when safe, and continue the chain. If you are at the session nesting limit, make your LAST MESSAGE a complete handoff prompt that starts a new chain.
4. Any decision for the owner is presented as clickable decision cards (AskUserQuestion), NOT inline text.
5. If the lane is CALIBRATED and the rubric clears for all years, check the complete / frontier declaration criteria, settle the keeper config and clear the tasks that block the declaration; if at complete / frontier, say so in the final message so the owner can approve.

READ FIRST. CLAUDE.md is binding, especially rules 1, 13, 14, 17, 19, 20, 21, 23, 24, 25, 28, 31, 32, 33, 34, 35 and 36.
- docs/records/nyiso/RESULT-nyiso-next8-hq-dedupe-2026-09-27.md and docs/records/nyiso/PRECOMMIT-nyiso-next8-hq-dedupe-2026-09-27.md sec. 3 (the floor numbers)
- docs/records/nyiso/FINDING-nyiso-next7-star-node-2026-09-27.md (eastern over-delivery; why per-neighbour routing is refused)
- src/market_sim/model/interchange/nyiso.py inject_nyiso_firm_imports; src/market_sim/model/interchange/spec.py NYISO_FIRM_IMPORT_FLOOR_FRAC and the NYISO ladders
- scripts/data/derive_nyiso_import_tranches.py (FIRM_BASE_MW = 900, "kept at its established value")
- NYISO matrix shard docs/codebase-site/data/mechanism-matrix/NYISO.js: nyiso_firm_imports (K; NEXT-8 routed question in its ev), import_hub_pricing (K), seam_neighbour_anchored_ladder (G — do not re-test without the neighbour-price intake). Lever queue: docs/mechanism-testing-matrix.md sec. 5.5 ("Queue after NEXT-8").

STATE
- Keeper: 2026-09-27-nyisonext8-hq-dedupe-span (bundle results/calibration/nyisonext8_span, 2022-2025) + stamped 2021 run 2026-09-27-nyisonext8-hq-dedupe-2021. Determination NOT-YET.
- Load-bearing failures: C3a 2022 -11.3 %, 2025 -11.2 % (model under-prices). C3c fails, not lone. C1, C2, C3b, C4, C6, C8 PASS every year; 2021 CALIBRATED.
- NEXT-8 measured (zero LP): the 900 MW HQ_hydro block is floored at frac 1.0 in every hour, but measured TOTAL net import is below 900 MW in 1.2/3.7/3.3/0.5/3.7/3.2/6.5/5.9 % of hours 2018-2025 (min -852 MW), and the HQ seam alone is a net EXPORT on average in 2024-2025 (-153 / -545 MW). The keeper's hourly import minimum is exactly 900 MW in 2023-2025, so the floor binds. FIRM_BASE_MW is an inherited constant ("kept at its established value"), not a measured contract quantity — capacity_market.py says as much.

TASK
1. G-DRIFT from the keeper's git_sha to your HEAD, written into your PRECOMMIT before any solve.
2. Phase 0, zero LP:
   - Footprint on the keeper: hours the floor binds (import at 900 MW), the MW it forces above what the ladder would clear, per year, and where that energy lands by zone; the price effect bound.
   - Identification: what is the floor's driver (the HQ Chateauguay/Cedars firm contract)? Find a published, forward-regenerable source for the firm quantity/availability (contract MW, NYISO Gold Book external capacity purchases, HQ outage/derate postings). A floor fitted to measured hourly flow is an OUTCOME pin (rule 13) — refused. Removing an unsupported always-on floor, or windowing it by its own driver, is admissible; tuning its level is not.
   - Decide ex ante: remove / window / re-base (with source) / keep (with the reason), one mechanism (rule 19). If nothing admissible is identifiable, stop at phase 0 with a FINDING and move to the next queue item.
3. If a correction is identified: fix footprint, gates and promotion rule ex ante (rule 1: promote on structure, never on C3a moving); gated field (rule 28(c) matrix row + every shard cell) vs direct correction — decide and justify.
4. Solves: one shard per registered year 2021-2025 (rules 34/36), pinned to a FULL 40-char SHA. SHARD PROMPT LESSONS FROM NEXT-8 — include all of these:
   - After hydrate, the shard MUST run `uv run python scripts/regenerate_clean.py` (data/clean is gitignored and absent from a fresh clone; the solve fails without it). The time budget starts after it.
   - Solve with `uv run python scripts/replay_keeper.py results/calibration/<keeper bundle> --years <y> --out-dir results/calibration/<lane>_<y>` (2021 from the 2021 bundle) plus the arm's --set if a field is used.
   - Push the full bundle via a `.gitignore` negation + plain `git add` (never -f / -A / .); hard stops, forbidden list and numeric report as in the NEXT-8 template (docs/records/nyiso/PRECOMMIT-nyiso-next8-hq-dedupe-2026-09-27.md sec. 6 and the shard prompts recorded in the NEXT-8 RESULT).
   - Parent side: compose with scripts/probes/nyisonext8_compose_span.py (adapt), then `run_calibration_full.py --rebuild-benchmark <span>` (the composite inherits single-year benchmark frames; the span frames match the keeper's), `legitimacy_diagnostics.py --bundle <span> --iso NYISO --json-out`, `run_calibration_full.py --restore-shared-inputs <2021 bundle>`, then `dashboard_add_run.py --no-prune`.
   - Promotion: `stamp_touchpoint_holdout.py ... --holdout-year 2021` (the default is 2022 — wrong for NYISO's 2021 run), and `prune_iso_runs.py --iso NYISO --force-uncite --keep <new 2021 run id>` (without --keep it prunes the new stamped run too).
5. Archive every shard once its bytes are verified (rule 33). Open a PR and merge. If CI is red only on known base-red, comment once, then merge.
6. If C3a 2022/2025 still fail, draft and launch the next handoff with these same standing directions. Remaining named objects after this one:
   - eastern over-delivery (needs intake of IESO hourly price, PJM LMP at the NYIS interface + the Neptune/HTP/VFT source pnodes, ISO-NE LMP at the NY external nodes, 2021-2025 — use the data-intake skill; network permitting);
   - the >$300 RT tail (nyiso-242: worth $5.44/MWh in 2022, foreclosed by idle sub-gate capacity);
   - the in-city commitment requirement (MyNYISO access is owner-held);
   - the 2025 downstate level shortfall.

REPORT: numbers only for phase 0 and gates per year, the verdict, the PR number and the next handoff.
```
