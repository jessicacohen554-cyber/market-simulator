# HANDOFF — NWPP-NEXT-12: NWPP fidelity levers (keeper #16 stands)

```
SESSION NWPP-NEXT-12 — NWPP calibration, keeper #16 (2026-09-29-nwppnext10-exit-month-routing)
DATA PROFILE: nwpp
MODEL: Opus or Fable
CLAUDE.md is binding. Pay particular attention to rules 1, 5, 13, 14, 19, 21, 23, 24, 28, 29 and 31–36.
The parent never solves (rule 32(a)). Every backcast year gets its own shard (rule 36).

CHAIN DIRECTIONS (owner, standing; pass them on verbatim to every handoff you launch)
- First, when it is safe, archive the previous session: session_01LMqnEAitUeWxs1Aw4rPHSt (NWPP-NEXT-11).
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
- Keeper #16: 2026-09-29-nwppnext10-exit-month-routing. Bundle: results/calibration/nwppnext10xy_span. Years 2019–2025.
- Determination: NOT-YET on {dispatch_corr}, ONE record. C4 coal 2023 is r 0.695 / NRMSE 0.283 against the 0.70 floor.
  Price is UNSCORED (rubric v3.8).
- NEXT-11 was zero LP. Read first:
  - docs/records/nwpp/FINDING-nwppnext11-coal-c1-c4-decomposition-2026-09-29.md (all of it; §5 has the owner rulings)
  - docs/records/nwpp/PRECOMMIT-nwppnext10-exit-ym-routing-2019-2025-2026-09-29.md (§3 G-DRIFT, §4 recipe, §5 hard stops)
  - docs/calibration-log/nwpp.md (latest entry), docs/codebase-site/data/mechanism-matrix/NWPP.js,
    docs/mechanism-testing-matrix.md §5.9

OWNER RULINGS (NEXT-11 cards, 2026-09-29)
- "Fidelity levers": keep keeper #16 and keep C4 coal 2023 open. Work levers 3 and 2 below. Neither is expected to clear
  C4 2023; they are structural fidelity.
- "Route to scorer lane": the uniform fossil reconcile in C1's classFull (k 0.87–0.92) belongs to a separate cross-ISO
  lane, HANDOFF-scorer-coal-reconcile-2026-09-29.md. Do NOT touch the scorer or the bench in this lane.

CLOSED — do NOT redo:
- Everything closed in HANDOFF-nwppnext7 through -nwppnext11.
- C4 coal 2023 inventory-conservation behaviour, in every form with a public identification: measured receipts (R),
  S_min (refuted), and the days-of-burn target (redacted). NEXT-11 §2 confirms it is Jim Bridger's Feb–May
  minimum-load conservation. Pinning monthly burn or stock would be an outcome pin (rule 13).
- Offer-multiplier tuning on C1, C4 or CT (rules 1 and 13).

OPEN LEVERS, highest value first
1. Lever 3: the merit-order guard for NWPP (campd_outage_merit_order_guard + campd_per_unit_attribution; matrix cells U).
   - No -perunit- or -perunitmerit- NWPP extract exists. The standard-family lay-up companion
     (campd-unit-outages-layup-NWPP.csv) has 17 rows, all 2023–2025.
   - Step 1, zero LP: derive the per-unit companions with scripts/data/derive_campd_unit_outages.py --iso NWPP
     --per-unit-crosswalk [--merit-order-guard]. This is a new-data derivation citing no residual (rule 23).
   - Step 2: census which windows move, per plant-year, before any solve. Centralia 2020 Mar–Jul and North Valmy 2020
     Jan–Jun are booked as zero availability now. Does the guard reclassify them?
   - Only then write the PRECOMMIT and solve seven year-isolated shards.
   - Also measure whether the guard separates idling on NWPP's coal panel. The short-gas F2 guard did not (cell note on
     unit_outage_short_windows_gas); if the coal guard does not either, say so and stop.
2. Lever 2: generic coal availability below measured generation (scripts/probes/_nwppnext10_coal_availability_census.py;
   repoint its BUNDLE at nwppnext10xy_span).
   - Naughton 4162 is short by 0.35–0.62 TWh every year 2021–2024. Bridger 8066 is short by 0.92 TWh in 2025.
   - Find the source of the base 0.89 / 0.97 statistical availability (rule 23) before touching it.
3. Boardman 6106 (single unit) has no outage windows. Its CEMS opTime is 0 every Apr–Jun, but the model runs it.
   That is +0.60 TWh in 2020. A whole-plant stop is undetectable as an outage by the peer-online rule. Treat it as the
   same merit-guard question as lever 1, not as a new mechanism.
4. SNV residual shed; internal-link over-flow (a structural FINDING plus an owner question); Jim Bridger has no measured
   COAL tranche row; solve time (the 2019 leg takes ~145 min).

PROCEDURE FOR ANY SOLVE — follow PRECOMMIT-nwppnext10 as the template (§3 G-DRIFT, §4 recipe, §5 hard stops)
- G-DRIFT runs against keeper #16's git_sha (0ec8eb79; NEXT-10 audited to main 526b75ee plus its own diff).
- Replay source: restore NWPP-49 from 909cdd30bfdd8a398b10a4255b1340d0d9ef1943 into /tmp/n49.
  - Use the §4 --set list, which includes unit_outage_exit_ym_from_eia860=true.
  - Add hydro_backfill_year=null for 2019–2022.
- SHARD PROMPTS: tell the shard to NEVER end its turn while the solve runs. It should poll in-turn with bounded wait
  loops until it pushes. Budgets: 2019 ~150 min; other years 40–55 min.
- Hard stops:
  - campd_ct_heat_rates_NWPP.csv sha256 = 29baa2f1ecfa10d9734c7e44cc306a88d527adb28968ea260f3409de37d7ff92.
  - The run_config diff against keeper #16's run_config_<Y>.json may differ only in the arm's key(s).
  - P1 demand: 279.581 / 292.940 / 289.358 / 298.960 / 280.261 / 290.216 / 302.532 TWh.
- Compose, then score and register:
  - scripts/probes/_nwpp42_compose_span.py --skip-diagnostics (2023 leg first);
  - legitimacy_diagnostics.py --bundle <span> --iso NWPP --json-out <span>/legitimacy_diagnostics.json (exit 1 is normal);
  - attestation: wrap scripts/gen_nwppnext10_attestation.py;
  - dashboard_add_run.py --no-prune;
  - calibration_verdict.py --run-id <id> --json, then diff per record against keeper #16.
- A DECLINED probe is pruned with prune_iso_runs.py --iso NWPP after the owner rules.
- Promote by rule 35: keepers/NWPP.json, build_status, audit_keepers (E1), prune, check_promotion_completeness, the
  matrix stamp and cell, §5.9, the calibration log, and the calibration-keeper-auditor subagent.
- Gitignore per-year leg dirs with a pattern that does NOT match the _span dir.

ENVIRONMENT NOTES
- pip install needs --ignore-installed PyYAML (Debian-owned PyYAML blocks the upgrade).
- The bundle's shared inputs (results/calibration/_shared/NWPP/*) are gitignored and absent on a fresh clone. The bench
  parts under frontend/data/backcast/bench/NWPP/ and the run payload carry what zero-LP work needs.

HOUSEKEEPING (owner)
- Leftover shard branches to delete. A session cannot delete refs (HTTP 403):
  - claude/nwppnext10-{2020..2025} and claude/nwppnext10-2019r
  - claude/nwppnext9mr-{2019..2025} (if still present)
- audit_keepers E14: the shard containers solved on newer highspy/pandas/pyarrow/pydantic than requirements.txt pins.
- Known pre-existing test failures, not NWPP's: as listed in HANDOFF-nwppnext10.
```
