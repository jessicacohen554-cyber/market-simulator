SESSION R-CAISO-21 — CAISO: evening under-price, ZERO-LP ROOT CAUSE FIRST
DATA PROFILE: caiso
MODEL: Opus or Fable

FIRST:
- Archive R-CAISO-20 (session_01TPg1oReTYpH6BPMgHXofZM) with mcp__Claude_Code_Remote__archive_session.
  - Do this only once PR #6941 (promotion) and this handoff's PR read MERGED on the GitHub MCP.
  - If either is not merged, do not archive, and say so in your first report.
- Check for unmerged CAISO branches and open CAISO PRs:
  - salvage anything not on main into your branch;
  - close the open PRs you salvaged;
  - report which branches the owner can delete. Deleting a ref returns 403, so do not try.
  - Known leftovers carry nothing that is not on main: `claude/r-caiso-18-*`, `claude/r-caiso-19*`,
    `claude/r-caiso-20`, and `claude/r-caiso-20-A-{2019..2025}` (shard transport; the legs are composed into the keeper).
- Work on a fresh branch off origin/main.

STATE (2026-09-30):
- Keeper `2026-09-30-caiso-r20-overnight` (bundle rcaiso20_A_span, 2022–25) is CALIBRATED, with a single ledgered C3c 2024.
- Fold `-touchpoints` (2019–21, bundle rcaiso20_A_tp_2019_2021) is NOT-YET on fuelmix, dispatch_corr and price_mean
  2021. Under rubric v3.13 (rule 30(c) as amended 2026-09-30) the ISO determination is NOT-YET because of the fold.
- R-CAISO-20 (docs/handoffs/r-caiso-20/RESULT-r-caiso-20-2026-09-30.md):
  - armed the overnight clean rung in the unprinted years (an owner ruling);
  - ledgered the remaining fold DSW residual as DATA-AVAILABILITY LIMITED: −9.3 / −15.2 / −10.2 TWh, daytime and
    evening, with no admissible trigger before 2021-04-27. **Do not re-open that ledger without a new pre-2021 hourly
    Palo Verde source.**
- The evening under-price is carried from earlier lanes.
  - In the span, the model's evening (h17–22) price sits below actual.
  - The DSW corridor is also short in h18–23 in every keeper year: −3 to −5 TWh (R-CAISO-19 FINDING §1 table).
  - The late-evening rung (caiso-269) covers only hod 22–23.

TASK (owner card 2026-09-30, link 3 "Evening under-price"; link 4 "C3c 2024 price tail" comes after this one):
1. PHASE 0, ZERO LP. Root-cause the evening under-price on the keeper's committed hourly sidecars, 2022–25 first:
   - measure model vs actual price by hod × month, per zone, against the committed actual-LMP basis;
   - find the marginal unit/tranche in the under-priced hours;
   - decompose supply against the measured references: imports by corridor vs EIA-930, CC/CT, storage discharge vs the
     CAISO Outlook batteries series, and hydro;
   - say which mechanism sets the price in those hours, and why it is below actual.
   - Check the mechanism matrix (CAISO shard + lever queue, docs/mechanism-testing-matrix.md §5) first.
   - Never re-test a cell already adjudicated R/I/G without new evidence.
2. If there is an admissible, structural, measured lever (rules 1, 13, 14, 19, 21, 23–25):
   - PRECOMMIT with pre-registered values and a decision rule;
   - build under a new default-off flag, with tests and the matrix row (rule 28(c));
   - build PR → merge → pin the full SHA;
   - 7 shards, one per year 2019–2025 (rule 36); the parent never solves. **The 2025 shard needs a 50-min budget.**
3. If there is none: record a FINDING, build nothing, and put the next choice to the owner as a decision card.
4. PARENT SEAM, as R-CAISO-20:
   - compose with scripts/probes/rcaiso_compose_span.py plus the seven --require flags:
     caiso_eia930_clock_repair=true, caiso_tac_shares_standard_time=true, caiso_ra_bridge_startup_aware=false,
     cc_eia923_identity_emission_basis=true, caiso_supply_consistent_demand=true,
     caiso_intertie_unprinted_year_measured_gas=true, caiso_dsw_overnight_clean_unprinted_arm=true (plus your new flag);
   - `legitimacy_diagnostics.py --bundle … --iso CAISO --json-out …`;
   - `dashboard_add_run --no-prune`;
   - attestation: a copy of scripts/gen_rcaiso20_attestation.py (it declares the R-CAISO-20 owner ruling; keep that text);
   - register again;
   - `stamp_touchpoint_holdout.py`;
   - `audit_keepers`;
   - `prune_iso_runs.py --iso CAISO --force-uncite --keep <new fold id>`;
   - `build_status.py --iso CAISO`.
   - Re-stamp the matrix shard, update keepers/CAISO.json, the calibration-complete.json CAISO entry (withdrawn block:
     `keeper` + prior_record keeper + a rekeyed_ line) and frontend/data/forecast/program-status.json gate (a) detail.
     Edit JSON by targeted text replacement, never a full re-dump.

OWNER RULINGS IN FORCE (do not re-ask):
- All rulings in docs/handoffs/r-caiso-18/HANDOFF-r-caiso-19.md and docs/handoffs/r-caiso-19/HANDOFF-r-caiso-20.md.
- 2026-09-30: arm the overnight rung pre-2021 (done, promoted); ledger the fold gap (done); the next links are the
  evening under-price (this session), then C3c 2024.

NOTES:
- A fresh container needs `pip install -e . pytest tzdata`, then `python3 scripts/hydrate_data.py --profile caiso`.
- Run `ruff format` in a separate command before any push.
- 4 unrelated tests in tests/unit/config fail on main (d53 / d60 pinned keys).
- Shards can fail at start on the weekly limit. Relaunch once; if it recurs, card the owner.
- Register → attest → register.
- The status/CAISO.js rebase conflict: re-run `build_status.py --iso CAISO`.
- check_registry_payload_parity flags your own local gitignored legs; that is expected (rule 31) and absent in CI.
- Never `git grep` in a partial clone.
- Read the keeper's committed hourly sidecars (class/system/storage/p0) first. For unit-level questions, the
  R-CAISO-20 leg SHAs are in RESULT-r-caiso-20 §Retrievability (`git show <sha>:<path>`, provenance only; the
  refs may be gone, in which case unit-level data costs a re-solve).
- Shards can read long prompts from an immutable SHA: commit the per-year prompts, then give each shard
  `git show <sha>:<path>` (the R-CAISO-20 pattern).

HARD RULES: CLAUDE.md is binding, especially rules 1, 13, 14, 19, 21, 23–25, 27, 28, 29(b)/(c), and 30–36.
- Owner decisions go to the owner as clickable decision cards (AskUserQuestion, multiSelect where choices are not
  exclusive), never inline text.

END OF SESSION:
- Promote if the candidate is good. Create a PR and rebase-merge it.
- Archive every shard, and report leftover shard branches for the owner to delete.
- Then launch R-CAISO-22 (C3c 2024 price tail) with these same directions: archive its parent when safe, salvage/close
  CAISO branches and PRs, present decisions as cards, promote if good, PR + merge, archive shards.
- If at the nesting limit, make the final message a complete handoff prompt in one code block.
