# HANDOFF — NWPP-NEXT-14: NWPP calibration after keeper #18

```
SESSION NWPP-NEXT-14 — NWPP calibration, keeper #18 (2026-09-30-nwppnext13-per-unit-attribution)
DATA PROFILE: nwpp
MODEL: Opus or Fable
CLAUDE.md is binding. Pay particular attention to rules 1, 5, 13, 14, 19, 21, 23, 24, 28, 29 and 31–36.
The parent never solves (rule 32(a)). Every backcast year gets its own shard (rule 36).

CHAIN DIRECTIONS (owner, standing; pass them on verbatim to every handoff you launch)
- First, when it is safe, archive the previous session: session_01S4S1ezk3C8WT2R1r6GgvMv (NWPP-NEXT-13).
  Safe means: its PR has merged on main, and get_session shows it idle.
- Check for unmerged NWPP branches and PRs. Salvage anything needed into your branch, and close or merge the PRs.
  Say which branches can be deleted.
- Rebase and merge your work.
- Present every decision for the owner as clickable decision cards (AskUserQuestion), NEVER as inline text.
- When done: promote if it is a good candidate, create a PR and merge it, archive all your shards, and launch the next
  handoff session to continue calibration while rubric failures remain. Give it these same chain directions, including
  "archive the previous session when safe".
- If NWPP becomes calibrated and the rubric clears for all years, check the complete / frontier declaration criteria.
  Settle the keeper config and clear the tasks that enable declaration. If complete / frontier is reached, say so in
  your final message so the owner can approve.
- If you are at the session-nesting limit, make your last message a handoff prompt that starts a new chain.
- Owner standing ruling: promote if structural integrity improves, even if a gate regresses. Report every regression
  at full magnitude.

STATE ON MAIN
- Keeper #18: 2026-09-30-nwppnext13-per-unit-attribution. Bundle: results/calibration/nwppnext13pu_span. Years 2019–2025.
  It is keeper #17's recipe + campd_per_unit_attribution (NWPP -perunit- outage extract and tranche artifact).
- Determination: NOT-YET on {dispatch_corr}, ONE record: C4 coal 2023 r 0.662 / NRMSE 0.317 (floor 0.70 / 0.30).
  Price is UNSCORED (rubric v3.8).
- Read first:
  - docs/handoffs/RESULT-nwppnext13-perunit-attribution-2026-09-30.md (all of it, esp. §2 and §4)
  - docs/handoffs/FINDING-nwppnext13-wefor-and-perunit-phase0-2026-09-30.md
  - docs/handoffs/PRECOMMIT-nwppnext13-perunit-attribution-2019-2025-2026-09-30.md (§3 G-DRIFT, §4 recipe, §5 stops)
  - docs/calibration-log/nwpp.md (latest entry), docs/codebase-site/data/mechanism-matrix/NWPP.js,
    docs/mechanism-testing-matrix.md §5.9

CLOSED — do NOT redo:
- Everything closed in HANDOFF-nwppnext7 through -nwppnext13.
- C4 coal 2023 inventory-conservation behaviour, in every public-identification form (Jim Bridger's Feb–May
  conservation). Pinning monthly burn or stock would be an outcome pin (rule 13).
- Offer-multiplier tuning on C1, C4 or CT (rules 1 and 13).
- campd_outage_merit_order_guard on NWPP: R. unit_outage_dispatched_bin_denominator on NWPP: R (dead exit cohorts in
  the dispatched bin dilute measured outages; FINDING-nwppnext13 §1.3).
- Clark 2322 / Silverhawk 55841 routing: settled by keeper #18 (EIA-860 GT peakers).
- The benchmark fossil reconcile belongs to the scorer lane. Do not touch the scorer or the bench.

OPEN LEVERS, highest value first
1. C4 coal 2023 deepened 0.695 → 0.662 at keeper #18. ZERO-LP decomposition first: Jim Bridger 8066 hourly model vs
   CEMS in 2023, keeper #17 vs #18 (both hourly sidecars are in git history; #17's bundle is at main before this PR).
   Suspect: the per-unit Bridger COAL tranche row pools 2023–2025 on the 2025-vintage 1,049 MW coal bin although
   units 1–2 burned coal in 2023 (the tranche artifact is vintage-static). Establish whether a year-vintage-correct
   tranche construction exists or is a new mechanism (rule 19) before any arm. Never tune to r.
2. CT_PEAKER under-dispatch grows every year and CC_REGULAR over-dispatch grows in 2024–25 (C1 PASS but widening).
   Zero-LP: which CT plants lost energy, and whether the new measured CT tranche rows (Gadsby, Tracy, Harry Allen,
   Silverhawk) or Clark CC availability drive it.
3. Coal WEFOR relief (lever 1 of NEXT-13): identified (residual 0) but blocked on a live-capacity denominator — a change
   to miso-266's shared mechanism that MISO's keeper arms. Owner question (card) before any code.
4. SNV residual shed; internal-link over-flow; solve time (the 2019 leg took ~200 min at keeper #18).

PROCEDURE FOR ANY SOLVE — PRECOMMIT-nwppnext13 is the template
- G-DRIFT against keeper #18's git_sha f2cfda46.
- Replay source: NWPP-49 from 909cdd30bfdd8a398b10a4255b1340d0d9ef1943 into /tmp/n49, with the §4 --set list
  (which now includes campd_per_unit_attribution=true), plus hydro_backfill_year=null for 2019–2022.
- Shard prompts: never end the turn while the solve runs; poll in-turn with bounded wait loops until the push.
  Commit the bundle with the .gitignore negation lines (rule 34(a)), including dispatch/<Y>_P1.parquet. Give the 2019
  shard a 260-min budget.
- Hard stops: campd_ct_heat_rates_NWPP.csv sha 29baa2f1…; campd-unit-outages-perunit-NWPP.csv sha ff5b0644…;
  thermal_tranches-perunit-NWPP.csv sha 2c502ad8…; run_config diff vs keeper #18's run_config_<Y>.json only in the
  arm's key(s); P1 demand 279.581 / 292.940 / 289.358 / 298.960 / 280.261 / 290.216 / 302.532 TWh.
- PARENT GOTCHAS: `git checkout <sha> -- <leg dir>` STAGES the leg; follow with `git rm -r --cached <leg dir>` and add
  the leg family to .gitignore. `gen_*_attestation.py` needs `git fetch --depth=1 origin 909cdd30…` first.
  `legitimacy_diagnostics.py` needs `--json-out <bundle>/legitimacy_diagnostics.json`.
- Compose with scripts/probes/_nwpp42_compose_span.py --skip-diagnostics (2023 leg first). Then:
  - legitimacy_diagnostics.py --json-out (exit 1 is normal);
  - an attestation wrapping scripts/gen_nwppnext13_attestation.py;
  - dashboard_add_run.py --no-prune;
  - calibration_verdict.py --run-id <id> --json, diffed per (criterion, year, key) record against keeper #18.
- prune_iso_runs.py needs the owner's explicit approval (the auto-mode classifier blocks it otherwise). Get it on
  the promotion card.

HOUSEKEEPING (owner)
- Leftover shard branches to delete. A session cannot delete refs (HTTP 403):
  - claude/nwppnext13-{2019..2025}
  - claude/nwppnext12-{2019..2025}, and any older nwppnext* shard branches still present
- The HEAD tranche deriver (scripts/data/derive_thermal_tranches.py) emitted no COAL rows for any ISO between
  COAL-SUB (2026-09-25) and NEXT-13's fix; no committed artifact was affected.
```
