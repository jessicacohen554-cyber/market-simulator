SESSION R-CAISO-18 — CAISO: fold CC_REGULAR over-dispatch 2019–2021 (zero-LP root cause first)
DATA PROFILE: caiso
MODEL: Opus or Fable

FIRST:
- Archive R-CAISO-17 (session_01QbVsxRpsJvq36qfcur1qZu) with mcp__Claude_Code_Remote__archive_session.
  - Do this only once PR #6918 (promotion) and this handoff's PR read MERGED on the GitHub MCP.
  - If either is not merged, do not archive, and say so in your first report.
- Check for unmerged CAISO branches and open CAISO PRs:
  - salvage anything not on main into your branch;
  - close the open PRs you salvaged;
  - report which branches the owner can delete. Deleting a ref returns 403, so do not try.
  - Known leftovers:
    - the R-CAISO-16 legs `claude/r-caiso-16-A-2019` … `-2025`, plus `claude/r-caiso-16-interchange-lag`, `-promote` and `-handoff`;
    - the R-CAISO-17 legs `claude/r-caiso-17-A-2019` … `-2025`, plus `claude/r-caiso-17-clockscan`, `-promote` and `-handoff`.
  - None of these carries anything that is not on main (the legs are transport only, rule 33(f)).
- Work on a fresh branch off origin/main.

STATE (2026-09-30):
- Keeper `2026-09-30-caiso-r17-earlyclock` (bundle rcaiso17_A_span, 2022–25) is CALIBRATED: a single ledgered C3c 2024.
  - C4 gas NRMSE 0.252 / 0.247 / 0.247 / 0.288.
- Fold `-touchpoints` (2019–21, bundle rcaiso17_A_tp_2019_2021) is NOT-YET. It is reported only (rule 30(c)).
- `caiso_eia930_clock_repair` is armed with the late windows (R-CAISO-13/16) and the 2019-01 .. 2022-06-13 EARLY
  generation window (R-CAISO-17). The fold's clock is therefore now repaired.
- Owner card 2026-09-30: next link = "Fold CC over-dispatch".

THE TARGET (bundle rcaiso17_A_tp_2019_2021, calibration_verdict.py):

| Year | C1 CC_REGULAR model vs actual EIA-923 | C4 gas r / NRMSE | Also failing |
|---|---|---|---|
| 2019 | 59.14 vs 36.07 TWh (+23.1) | 0.892 / 0.564 | — |
| 2020 | 68.41 vs 43.14 TWh (+25.3) | 0.902 / 0.514 | — |
| 2021 | 59.68 vs 49.16 TWh (+10.5) | 0.853 / 0.354 | C3a +12.5 % (57.22 vs 50.87) |

- Every other C1 class passes. C2 (gas family) passes.
- The keeper years sit at 54.1 / 52.0 / 46.8 / 40.0 TWh CC_REGULAR and pass.
- So the defect is specific to the older years:
  - something that displaces CC in reality (imports, hydro, CC_CHP / other gas classification, demand, fleet
    membership, EIA-923 basis) is under-represented in 2019–21;
  - or the benchmark basis differs in those years.

TASK (do nothing else):
1. Phase 0, zero LP. Attribute the +23 / +25 / +10 TWh from the committed fold bundle plus measured inputs.
   - Compare against EIA-930 CISO NG: NG (repaired), CEMS CA gas, EIA-923 per-plant CC_REGULAR and CAISO Outlook
     natural_gas (2019–21):
     - is the ACTUAL itself on a different basis in 2019–21 (plant set, BA assignment, CHP split)?
     - or is the MODEL over-dispatching?
   - If the model is over-dispatching, which supply is it displacing? Compare the model with measured values for:
     imports by corridor, hydro (incl. the WAT backfill), solar/wind, storage, and demand level.
   - Check the fleet: CC_REGULAR nameplate and availability in 2019–21 vs EIA-860 / CAMPD operating units.
   - Before proposing a lever, check the mechanism matrix CAISO shard and lever queue (rule 28). Do not re-test R/I/G
     cells without new evidence.
   - Record the attribution table in a PRECOMMIT before anything is built.
2. If a measured-input or structural root cause is found (rules 1, 13, 14; no fitted adder, no haircut):
   - build it under a flag, with zero or measured parameters;
   - tests: off path byte-identical;
   - then 7 shards, one per year 2019–2025 (rule 36). Use docs/handoffs/r-caiso-17/shard-prompt.md as the template:
     `{SRC}` = rcaiso17_A_tp_2019_2021 (2019–21) / rcaiso17_A_span (2022–25), with new hard-stop counts.
     Pin the full SHA after your build PR merges. The parent never solves (rule 32(a)).
3. If the residual is a benchmark-basis artifact, or has no admissible lever:
   - build nothing;
   - record the finding;
   - put the next-link choice to the owner as a decision card.
4. PARENT SEAM, as R-CAISO-17:
   - compose with scripts/probes/rcaiso_compose_span.py and the five --require flags:
     caiso_eia930_clock_repair=true, caiso_tac_shares_standard_time=true, caiso_ra_bridge_startup_aware=false,
     cc_eia923_identity_emission_basis=true, caiso_supply_consistent_demand=true (plus your new flag);
   - `legitimacy_diagnostics.py --bundle … --iso CAISO --json-out …`;
   - `dashboard_add_run --no-prune`;
   - a copy of scripts/gen_rcaiso17_attestation.py;
   - register again;
   - stamp the fold;
   - PRUNE WITH `prune_iso_runs.py --iso CAISO --force-uncite --keep <new fold id>`.
5. Decision rule, pre-registered in your PRECOMMIT:
   - Promote on structure (rule 14) if 2022–25 stays CALIBRATED and the repair is complete.
   - Report the fold's movement: the fold can never downgrade the ISO (rule 30(c)).
   - Otherwise the trade goes to the owner as a decision card.

OWNER RULINGS IN FORCE (do not re-ask):
- SD floor static 1,436; LA Basin: "SD only".
- EIA930_GAS_FOLD_REFUTED: keep as is.
- startup_aware disarmed.
- tac_shares_standard_time armed.
- PS wall kept.
- The caiso-80 demand basis stands.
- Clock repair complete on frame / demand / HSL / battery envelope.
- TI on its true clock.
- Pre-2022 early window promoted (2026-09-30).
- The sub-hour (fractional) clock form is NOT built: it was offered, and the owner chose this link instead.
- Next link: "Fold CC over-dispatch" (2026-09-30).

NOTES:
- A fresh container needs `pip install -e . pytest tzdata`.
- Run `ruff format` in a separate command before any push.
- The keeper tracks the solve-year EIA-860 vintage. Any reader-side re-derivation that loads the fleet must pin the vintage its
  committed derivation used and restore the solve's own (R-CAISO-15 ADDENDUM §8).
- The model clock is the extract's row POSITION grid: local STANDARD time (UTC−8), start-of-hour. EIA `UTC time` is hour-ENDING.
- check_registry_payload_parity flags local gitignored legs. That is expected (rule 31) and absent in CI.
- Never `git grep` in a partial clone; use rg.
- The status/CAISO.js part conflicts on rebase whenever another lane touches status. Take either side and re-run
  `build_status.py --iso CAISO`.

HARD RULES: CLAUDE.md is binding, especially rules 1, 13, 14, 19, 21, 23–25, 27, 28, 29(b)/(c), and 30–36.
- Owner decisions go to the owner as clickable decision cards (AskUserQuestion), never inline text.

END OF SESSION:
- Promote if the candidate is good. Create a PR and merge it (rebase-and-merge).
- Archive every shard, and report leftover shard branches for the owner to delete.
- If CAISO still has rubric failures, put the next-link choice to the owner as a decision card. Then launch R-CAISO-19
  with these same directions: archive its parent when safe, salvage/close CAISO branches and PRs, present decisions as
  cards, promote if good, PR + merge, archive shards, and launch the next link.
- If at the nesting limit, make the final message a complete handoff prompt in one code block.
