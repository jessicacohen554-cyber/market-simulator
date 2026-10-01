SESSION R-CAISO-19 — CAISO: fold DSW import residual 2019–21 (zero-LP root cause first)
DATA PROFILE: caiso
MODEL: Opus or Fable

FIRST:
- Archive R-CAISO-18 (session_018sCe4LdBd1WwwvC3wJ9xhR) with mcp__Claude_Code_Remote__archive_session.
  - Do this only once PR #6927 (promotion) and this handoff's PR read MERGED on the GitHub MCP.
  - If either is not merged, do not archive, and say so in your first report.
- Check for unmerged CAISO branches and open CAISO PRs:
  - salvage anything not on main into your branch;
  - close the open PRs you salvaged;
  - report which branches the owner can delete. Deleting a ref returns 403, so do not try.
  - Known leftovers:
    - the R-CAISO-17 legs `claude/r-caiso-17-A-2019` … `-2025`, plus `claude/r-caiso-17-clockscan`, `-promote` and
      `-handoff`;
    - the R-CAISO-18 legs `claude/r-caiso-18-A-2019` … `-2025`, plus `claude/r-caiso-18-ccfold`, `-promote` and `-handoff`.
  - None of these carries anything that is not on main (the legs are transport only, rule 33(f)).
- Work on a fresh branch off origin/main.

STATE (2026-09-30):
- Keeper `2026-09-30-caiso-r18-dswgas` (bundle rcaiso18_A_span, 2022–25) is CALIBRATED: a single ledgered C3c 2024.
  - C4 gas NRMSE 0.252 / 0.247 / 0.247 / 0.288.
- Fold `-touchpoints` (2019–21, bundle rcaiso18_A_tp_2019_2021) is NOT-YET. It is reported only (rule 30(c)).
- `caiso_intertie_unprinted_year_measured_gas` (R-CAISO-18) now prices the unprinted WECC intertie hub hours on the
  measured-gas reference formula:
  - all of 2019–20 (OASIS GroupZip serves nothing before 2021-04-27);
  - Jan–Apr 2021.
  - The AZ/OR N3045 gas it uses is rebuilt from EIA-923 receipts where EIA withholds it.
  - Record: docs/handoffs/r-caiso-18/.
- Owner card 2026-09-30: next link = "Fold DSW residual".

THE TARGET (bundle rcaiso18_A_tp_2019_2021, calibration_verdict.py):

| Year | C1 CC_REGULAR model − EIA-923 | DSW import model / EIA-930 | C4 gas r / NRMSE | Also failing |
|---|---|---|---|---|
| 2019 | +14.5 TWh | 31.4 / 44.7 | 0.870 / 0.454 | — |
| 2020 | +22.4 TWh | 21.3 / 42.0 | 0.889 / 0.470 | — |
| 2021 | +10.7 TWh | 29.9 / 40.9 | 0.847 / 0.369 | C3a +12.5 % |

- PNW over-imports: 16.8 / 21.5 / 15.9 TWh vs EIA-930 9.2 / 17.4 / 13.6.
- The formula Palo Verde price ($28 / $30 in 2019 / 20) plus wheel plus carbon clears near the model λ. So the DSW gas
  blocks (DSW_CCGT 1,764 MW, DSW_CT 2,156 MW, WECC_scarcity) run only part of the time.
- The DSW "clean" rungs (daytime / overnight / surplus / lateevening_clean) are armed only by a RAW measured print
  (`measured_intertie_hub_price_raw`), so they stay at 0 MW in 2019–20.
  - In 2021 they carry 15.8 TWh.
  - In 2022–25 they carry much of the DSW volume.

TASK (do nothing else):
1. Phase 0, zero LP. Decompose the remaining DSW deficit per year and per tranche from the R-CAISO-18 legs.
   - Read the legs from their shard commits, which are provenance only. SHAs are in RESULT-r-caiso-18 §Retrievability.
   - Break it down by hour-of-day and month: offer (formula hub + wheel + carbon) vs model λ, and cleared vs capacity.
   - Compare 2022–25, where the clean rungs are armed:
     - how much of the keeper years' DSW volume do the clean rungs carry;
     - what does their arming trigger read;
     - is there an admissible measured or structural arming for 2019–20 without a raw print?
   - Check the carbon and wheel terms on the formula-priced tranches against what 2022–25 applies (rule 19: one
     mechanism, no double count).
   - Check the mechanism matrix CAISO shard and the §5.2 lever queue first (rule 28). Do not re-test R/I/G cells without
     new evidence. `caiso_import_solar_shape` is R, and the clean-rung percentiles are K and may not be re-sized (rule 1).
   - Record the decomposition in a PRECOMMIT before anything is built.
2. If a measured-input or structural root cause is found (rules 1, 13, 14; no fitted adder, no haircut, no percentile
   sweep):
   - build it under a flag, with zero or measured parameters;
   - tests: off path byte-identical;
   - then 7 shards, one per year 2019–2025 (rule 36). Use docs/handoffs/r-caiso-18/shard-prompt.md as the template:
     `{SRC}` = rcaiso18_A_tp_2019_2021 (2019–21) / rcaiso18_A_span (2022–25), with new hard-stop counts.
   - **2025 needs a 50-min budget.** The solve takes about 44 min.
   - Pin the full SHA after your build PR merges. The parent never solves (rule 32(a)).
3. If there is no admissible lever:
   - build nothing;
   - record the finding;
   - put the next-link choice to the owner as a decision card.
4. PARENT SEAM, as R-CAISO-18:
   - compose with scripts/probes/rcaiso_compose_span.py and the six --require flags:
     caiso_eia930_clock_repair=true, caiso_tac_shares_standard_time=true, caiso_ra_bridge_startup_aware=false,
     cc_eia923_identity_emission_basis=true, caiso_supply_consistent_demand=true,
     caiso_intertie_unprinted_year_measured_gas=true (plus your new flag);
   - `legitimacy_diagnostics.py --bundle … --iso CAISO --json-out …`;
   - `dashboard_add_run --no-prune`;
   - a copy of scripts/gen_rcaiso18_attestation.py;
   - register again;
   - stamp the fold with `stamp_touchpoint_holdout.py`;
   - audit_keepers;
   - PRUNE WITH `prune_iso_runs.py --iso CAISO --force-uncite --keep <new fold id>`.
5. Decision rule, pre-registered in your PRECOMMIT:
   - Promote on structure (rule 14) if 2022–25 stays CALIBRATED and the repair is complete.
   - Report the fold's movement: the fold can never downgrade the ISO (rule 30(c)).
   - Declare a backstop: if |DSW error| grows in any year, the trade goes to the owner as a decision card.

OWNER RULINGS IN FORCE (do not re-ask):
- SD floor static 1,436; LA Basin: "SD only".
- EIA930_GAS_FOLD_REFUTED: keep as is.
- startup_aware disarmed.
- tac_shares_standard_time armed.
- PS wall kept.
- The caiso-80 demand basis stands.
- Clock repair complete.
- TI on its true clock.
- Pre-2022 early window promoted.
- The sub-hour clock form is NOT built.
- The unprinted-year measured-gas hub pricing is promoted (2026-09-30).
- Next link: "Fold DSW residual" (2026-09-30).

NOTES:
- A fresh container needs `pip install -e . pytest tzdata`. This clone is full, so hydrate_data refuses; continue.
- Run `ruff format` in a separate command before any push.
- 4 tests in tests/unit/config fail on main independent of CAISO: d53 / d60 pinned keys and summer COAL. They are not
  yours.
- Shards can fail at start on the account weekly limit. Relaunch once; if it recurs, card the owner.
- calibration_verdict.py needs a registered run: register → attest → register.
- check_registry_payload_parity flags local gitignored legs. That is expected (rule 31) and absent in CI.
- Never `git grep` in a partial clone; use rg.
- The status/CAISO.js part conflicts on rebase whenever another lane touches status. Take either side and re-run
  `build_status.py --iso CAISO`.

HARD RULES: CLAUDE.md is binding, especially rules 1, 13, 14, 19, 21, 23–25, 27, 28, 29(b)/(c), and 30–36.
- Owner decisions go to the owner as clickable decision cards (AskUserQuestion), never inline text.

END OF SESSION:
- Promote if the candidate is good. Create a PR and merge it (rebase-and-merge).
- Archive every shard, and report leftover shard branches for the owner to delete.
- If CAISO still has rubric failures, put the next-link choice to the owner as a decision card. Then launch R-CAISO-20
  with these same directions: archive its parent when safe, salvage/close CAISO branches and PRs, present decisions as
  cards, promote if good, PR + merge, archive shards, and launch the next link.
- If at the nesting limit, make the final message a complete handoff prompt in one code block.
