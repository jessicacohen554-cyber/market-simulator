# HANDOFF — NWPP-NEXT-11: NWPP calibration after NEXT-10 (keeper #16)

```
SESSION NWPP-NEXT-11 — NWPP calibration, keeper #16 (2026-09-29-nwppnext10-exit-month-routing)
DATA PROFILE: nwpp
MODEL: Opus or Fable
CLAUDE.md is binding. Pay particular attention to rules 1, 5, 13, 14, 19, 21, 23, 24, 28, 29 and 31–36.
The parent never solves (rule 32(a)). Every backcast year gets its own shard (rule 36).

CHAIN DIRECTIONS (owner, standing; pass them on verbatim to every handoff you launch)
- First, when it is safe, archive the previous session: session_014W75ZcdDNtobdRjVgGNVdb (NWPP-NEXT-10).
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
  - Recipe: keeper #15's recipe + unit_outage_exit_ym_from_eia860=true.
  - That flag stamps each CAMPD outage row's exit_ym from EIA-860 and routes it to mid_vintage_exit_carry's dated exit
    bin, using PJM-NEXT-8's accumulator. It is live only at plants with a stamped row in the solved year.
  - It moves only Colstrip 2020: 5.86 → 7.91 TWh available, against 7.94 generated.
- Determination: NOT-YET on {dispatch_corr}, ONE record. C4 coal 2023 is r 0.695 / NRMSE 0.283 against the 0.70 floor.
  Price is UNSCORED (rubric v3.8).
- 2019 and 2021–2025 are byte-identical to keeper #15. In 2020, C4 coal went 0.762 → 0.772, C1 COAL_PRB
  +2.14 → +4.20 TWh (worse, still PASS), and CC_REGULAR +2.22 → +0.75.
- Records to read first:
  - docs/records/nwpp/RESULT-nwppnext10-exit-ym-routing-2019-2025-2026-09-29.md (§2, §4 routed)
  - docs/records/nwpp/PRECOMMIT-nwppnext10-exit-ym-routing-2019-2025-2026-09-29.md (§0 lever-1 closure, §3 G-DRIFT,
    §4 recipe, §5 hard stops)
  - docs/calibration-log/nwpp.md, docs/codebase-site/data/mechanism-matrix/NWPP.js, docs/mechanism-testing-matrix.md §5.9

CLOSED — do NOT redo:
- Everything closed in HANDOFF-nwppnext7 through -nwppnext10.
- For C4 coal 2023, an inventory-management / days-of-burn floor. PacifiCorp's targets are redacted, and the only
  public band (2009, Utah-only) is contradicted by the 2023 stocks. Owner card 2026-09-29.
- Measured same-year receipts (NEXT-9, R) and S_min (refuted).
- Offer-multiplier tuning on C1, C4 or CT (rules 1 and 13).

OPEN LEVERS, highest value first
1. C1 COAL_PRB 2020 at +4.20 TWh. Which PRB plants over-run now that Colstrip is physically right?
   - Zero LP: per-plant payload m_mon against CAMPD gross (scripts/probes/_nwppnext4_coal_census.py::campd_plant_hourly).
   - Candidates: Wyodak, Dave Johnston, Naughton, North Valmy.
2. Generic coal availability below measured generation (scripts/probes/_nwppnext10_coal_availability_census.py).
   - Naughton 4162 is short by 0.35–0.62 TWh every year 2021–2024. Bridger 8066 is short by 0.92 TWh in 2025.
     Colstrip is short by 0.05–0.54 TWh in 2021–2025.
   - The base 0.89 / 0.97 statistical coal availability looks tight for high-CF units. Find its source (rule 23) before
     touching it.
3. Economic lay-up booked as outage: Centralia 3845 and North Valmy 8224 show whole spring months at zero
   availability. Check the merit-order guard family (nyiso-177) for NWPP, which is untested here.
4. C4 coal 2023 (the determination). It needs an owner-sourced confidential target, or a new structural idea with a
   measured identification.
5. SNV residual shed; internal-link over-flow (a structural FINDING plus an owner question); Jim Bridger has no
   measured COAL tranche row; solve time (the 2019 leg takes ~145 min).

PROCEDURE FOR ANY SOLVE — follow PRECOMMIT-nwppnext10 as the template (§3 G-DRIFT, §4 recipe, §5 hard stops)
- G-DRIFT runs against keeper #16's git_sha. The pin was 0ec8eb79; NEXT-10 audited to main 526b75ee plus its own diff.
- Replay source: restore NWPP-49 from 909cdd30bfdd8a398b10a4255b1340d0d9ef1943 into /tmp/n49.
  - Use the §4 --set list, which now includes unit_outage_exit_ym_from_eia860=true.
  - Add hydro_backfill_year=null for 2019–2022.
- SHARD PROMPTS: tell the shard to NEVER end its turn while the solve runs. It should poll in-turn with bounded wait
  loops until it pushes. In NEXT-10 the first 2019 shard ended its turn at 60 min with the solve unfinished; the
  parent cannot message cloud shards, so a stalled shard must be replaced. Budgets: 2019 ~150 min; other years 40–55 min.
- Hard stops:
  - campd_ct_heat_rates_NWPP.csv sha256 = 29baa2f1ecfa10d9734c7e44cc306a88d527adb28968ea260f3409de37d7ff92.
  - The run_config diff against keeper #16's run_config_<Y>.json may differ only in the arm's key.
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

HOUSEKEEPING (owner)
- Leftover shard branches to delete. A session cannot delete refs (HTTP 403):
  - claude/nwppnext10-{2020..2025} and claude/nwppnext10-2019r
  - claude/nwppnext9mr-{2019..2025}
  - claude/nwppnext9 (merged)
- audit_keepers E14: the shard containers solved on newer highspy/pandas/pyarrow/pydantic than requirements.txt pins.
  2021–2025 still reproduced keeper #15 byte-identically.
- Known pre-existing test failures, not NWPP's: as listed in HANDOFF-nwppnext10.
```
