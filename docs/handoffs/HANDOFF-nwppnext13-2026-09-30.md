# HANDOFF — NWPP-NEXT-13: NWPP calibration after keeper #17

```
SESSION NWPP-NEXT-13 — NWPP calibration, keeper #17 (2026-09-29-nwppnext12-boardman-membership)
DATA PROFILE: nwpp
MODEL: Opus or Fable
CLAUDE.md is binding. Pay particular attention to rules 1, 5, 13, 14, 19, 21, 23, 24, 28, 29 and 31–36.
The parent never solves (rule 32(a)). Every backcast year gets its own shard (rule 36).

CHAIN DIRECTIONS (owner, standing; pass them on verbatim to every handoff you launch)
- First, when it is safe, archive the previous session: session_01Xerdd7ifEM4wAQeVguciXF (NWPP-NEXT-12).
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
- Keeper #17: 2026-09-29-nwppnext12-boardman-membership. Bundle: results/calibration/nwppnext12mr_span. Years 2019–2025.
  It is keeper #16's recipe + unit_outage_membership_repair (Boardman 6106's measured CAMPD windows).
- Determination: NOT-YET on {dispatch_corr}, ONE record: C4 coal 2023 r 0.695 against the 0.70 floor.
  Price is UNSCORED (rubric v3.8).
- Read first:
  - docs/handoffs/FINDING-nwppnext12-layup-guard-and-coal-availability-2026-09-29.md (all of it)
  - docs/handoffs/RESULT-nwppnext12-boardman-membership-2026-09-30.md
  - docs/handoffs/PRECOMMIT-nwppnext12-boardman-membership-2019-2025-2026-09-29.md (§3 G-DRIFT, §4 recipe, §5 stops)
  - docs/calibration-log/nwpp.md (latest entry), docs/codebase-site/data/mechanism-matrix/NWPP.js,
    docs/mechanism-testing-matrix.md §5.9

CLOSED — do NOT redo:
- Everything closed in HANDOFF-nwppnext7 through -nwppnext12.
- C4 coal 2023 inventory-conservation behaviour, in every public-identification form (Jim Bridger's Feb–May
  conservation; NEXT-11 §2). Pinning monthly burn or stock would be an outcome pin (rule 13).
- Offer-multiplier tuning on C1, C4 or CT (rules 1 and 13).
- campd_outage_merit_order_guard on NWPP: R (NEXT-12 FINDING §2). The fossil-only clearing-cost band ranks units,
  not windows.
- The benchmark fossil reconcile belongs to the scorer lane (HANDOFF-scorer-coal-reconcile-2026-09-29.md).
  Do not touch the scorer or the bench.

OPEN LEVERS, highest value first
1. Lever 2, re-scoped: the statistical coal WEFOR double count (FINDING-nwppnext12 §3). ZERO-LP PHASE 0 first.
   - Derive the NWPP screened set: derive_campd_unit_outages.py --iso NWPP --years 2019..2025 --short-windows
     --emit-screened-set, written to scratch first. That writes campd-unit-outages-short-screened-NWPP.csv.
     Check that the short extract itself is byte-identical to the committed one.
   - Compute the caiso-187 identification per year on the screened set: W_s (statistical term removed) vs X_s
     (measured >= 5-day + short + partial windows). The template is scripts/probes/_miso273_screened_phase0.py.
     Residual = max(0, W_s - X_s) / (screened MW x 8760).
   - wefor_residual_short_screened_coal is fail-closed on unit_outage_dispatched_bin_denominator. Census that flag
     ON ITS OWN first (fleet_only, every class, every year): it is a second mechanism, and it must be justified on
     its own (rule 19) before it is stacked.
   - Read wefor_multiplier = 0.7 (a ledgered free parameter) alongside: relief makes part of it moot. Do not re-tune
     it (rule 1).
   - Payoff on the scored surface is small (coal-only shortfall 0.04–0.61 TWh/yr, material only at Colstrip in
     2022–23). Solve only if phase 0 identifies it cleanly; otherwise record it and stop.
2. Clark 2322 CC routing (campd_per_unit_attribution = O). The per-unit crosswalk moves all 2,951 Clark CC windows
   off CC_REGULAR. Establish which is right from EIA-860 / CAMPD unit types before any arm (rule 14).
3. SNV residual shed; internal-link over-flow (a structural FINDING plus an owner question); Jim Bridger has no
   measured COAL tranche row; solve time (the 2019 leg takes ~120–150 min).

PROCEDURE FOR ANY SOLVE — PRECOMMIT-nwppnext12 is the template
- G-DRIFT against keeper #17's git_sha 0b1d2cfe (NEXT-12 audited main through 0a5eb910 as all inert).
- Replay source: NWPP-49 from 909cdd30bfdd8a398b10a4255b1340d0d9ef1943 into /tmp/n49, with the §4 --set list
  (which now includes unit_outage_membership_repair=true), plus hydro_backfill_year=null for 2019–2022.
- Shard prompts: never end the turn while the solve runs; poll in-turn with bounded wait loops until the push.
  Commit the bundle with the .gitignore negation lines (rule 34(a)), including dispatch/<Y>_P1.parquet.
- Hard stops: campd_ct_heat_rates_NWPP.csv sha 29baa2f1…; campd-unit-outages-memberrepair-NWPP.csv sha 386a64d3…;
  run_config diff vs keeper #17's run_config_<Y>.json only in the arm's key(s); P1 demand
  279.581 / 292.940 / 289.358 / 298.960 / 280.261 / 290.216 / 302.532 TWh.
- IMPORTANT PARENT GOTCHA: `git checkout <sha> -- <leg dir>` STAGES the leg in the index. Follow it with
  `git rm -r --cached <leg dir>` before any commit.
- Compose with scripts/probes/_nwpp42_compose_span.py --skip-diagnostics (2023 leg first). Then:
  - legitimacy_diagnostics.py (exit 1 is normal);
  - an attestation wrapping scripts/gen_nwppnext12_attestation.py;
  - dashboard_add_run.py --no-prune;
  - calibration_verdict.py --run-id <id> --json, diffed per (criterion, year, key) record against keeper #17.
- prune_iso_runs.py needs the owner's explicit approval (the auto-mode classifier blocks it otherwise). Get it on
  the promotion card.

HOUSEKEEPING (owner)
- Leftover shard branches to delete. A session cannot delete refs (HTTP 403):
  - claude/nwppnext12-{2019..2025}
  - claude/nwppnext10-{2020..2025}, claude/nwppnext10-2019r, claude/nwppnext9mr-{2019..2025} (if still present)
- audit_keepers E14: the shard containers solve on newer highspy/pandas/pyarrow/pydantic than requirements.txt pins.
```
