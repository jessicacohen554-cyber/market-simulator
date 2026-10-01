SESSION R-CAISO-20 — CAISO: arm the overnight clean rung in unprinted years (OWNER RULING), then ledger the fold residual
DATA PROFILE: caiso
MODEL: Opus or Fable

FIRST:
- Archive R-CAISO-19 (session_01QtQ4hunsjkvpmmEuzqcXAu) with mcp__Claude_Code_Remote__archive_session.
  - Do this only once PR #6930 (finding) and this handoff's PR read MERGED on the GitHub MCP.
  - If either is not merged, do not archive, and say so in your first report.
- Check for unmerged CAISO branches and open CAISO PRs:
  - salvage anything not on main into your branch;
  - close the open PRs you salvaged;
  - report which branches the owner can delete. Deleting a ref returns 403, so do not try.
  - Known leftovers: `claude/r-caiso-17-*`, `claude/r-caiso-18-*`, `claude/r-caiso-19`, `claude/r-caiso-19-handoff`.
  - None of these carries anything that is not on main.
- Work on a fresh branch off origin/main.

STATE (2026-09-30):
- Keeper `2026-09-30-caiso-r18-dswgas` (bundle rcaiso18_A_span, 2022–25) is CALIBRATED: a single ledgered C3c 2024.
- Fold `-touchpoints` (2019–21, bundle rcaiso18_A_tp_2019_2021) is NOT-YET. It is reported only (rule 30(c)).
- R-CAISO-19 finding (docs/records/caiso/r-caiso-19/FINDING-r-caiso-19-2026-09-30.md, zero LP):
  - the fold's DSW gap (−13.3 / −20.6 / −11.0 TWh vs EIA-930) is the four clean rungs that carry 0 MW in 2019–20;
  - in 2021 the gap is in the unprinted Jan–Apr;
  - no measured arming exists.
- The clean tranches are ALREADY priced on the measured-gas formula hub in the unprinted hours: DSW_overnight_clean mc is $28.12 / $30.03 in 2019 / 20. Only the arming mask blocks them.

OWNER CARD 2026-09-30 (all four selected):
1. "Arm overnight rung pre-2021".
   - This is an OWNER RULING. It carries the 2022–25 measured overnight no-wedge structure into years with no measurement.
   - It is authorised by the ruling, not admitted as a measured input. Say so in the PRECOMMIT, the attestation and the matrix cell.
2. "Ledger the fold gap".
   - Ledger whatever DSW residual remains after (1) as a data-availability limit: OASIS serves nothing before 2021-04-27.
3. "Evening under-price", then 4. "C3c 2024 price tail".
   - These are later links, run one after the other because both touch the 2022–25 keeper.
   - Do NOT start them in this session.

TASK (do only (1) and (2)):
1. Build, under a NEW flag (default off, CAISO-only, backcast-only), e.g. `caiso_dsw_overnight_clean_unprinted_arm`:
   - `inject_caiso_dsw_overnight_clean` arms hod 0–5 in hours where the raw print is absent, but only where the
     `caiso_intertie_unprinted_year_measured_gas` loader prices the hub. Pricing is unchanged.
   - Every other rung stays raw-print-gated: surplus, daytime and late-evening are NOT touched. Their triggers are
     inadmissible without a raw print (FINDING §3).
   - Depth:
     - `derive_caiso_overnight_clean_depth.py`'s own p95 construction over the extra years, so 2019 and 2020 get
       measured depths; for 2021, record in the PRECOMMIT whether its static entry is kept;
     - the percentile is NOT re-sized (rule 1; K);
     - pre-register the values before any solve.
   - The hourly headroom stays net of the firm block and the surplus rung (rule 19).
   - Tests: off path byte-identical; 2022–25 byte-identical on (raw print everywhere except the caiso-253 2023 gap —
     CHECK whether the 2023 Jan–Feb OASIS gap hours would arm; if they would, the flag must be limited to the
     unprinted-year hours the R-CAISO-18 loader fills, so the "closed winter lane" stays closed).
   - Mechanism-matrix row + a cell in every ISO shard (rule 28(c)).
2. Zero-LP first-order estimate of the added DSW TWh per fold year, in the PRECOMMIT.
3. Build PR → merge → pin the full SHA.
4. Then 7 shards, one per year 2019–2025 (rule 36). The parent never solves (rule 32(a)).
   - Template: docs/records/caiso/r-caiso-18/shard-prompt.md, with `{SRC}` = rcaiso18_A_tp_2019_2021 (2019–21) /
     rcaiso18_A_span (2022–25). Add `--set <new flag>=true` and new hard-stop values.
   - **2025 needs a 50-min budget.**
5. PARENT SEAM, as R-CAISO-18:
   - compose with scripts/probes/rcaiso_compose_span.py plus the six --require flags and the new flag;
   - `legitimacy_diagnostics.py`;
   - `dashboard_add_run --no-prune`;
   - an attestation (a copy of scripts/gen_rcaiso18_attestation.py). Declare the owner ruling in the DOF / provenance
     text.
   - register again;
   - stamp the fold;
   - audit_keepers;
   - `prune_iso_runs.py --iso CAISO --force-uncite --keep <new fold id>`.
6. Decision rule, pre-registered:
   - Promote if 2022–25 byte-reproduce the incumbent, the span stays CALIBRATED, and all shards pass their hard stops.
   - The fold is reported, never gating (rule 30(c)).
   - Backstop: if |DSW error| grows in any fold year, the trade goes to the owner as a decision card.
7. Ledger the remaining fold DSW residual in the RESULT and the calibration log, as data-availability limited.

OWNER RULINGS IN FORCE (do not re-ask):
- All rulings in docs/records/caiso/r-caiso-18/HANDOFF-r-caiso-19.md.
- Plus 2026-09-30: arm the overnight rung pre-2021; ledger the fold gap; next links are the evening under-price, then
  C3c 2024.

NOTES:
- A fresh container needs `pip install -e . pytest tzdata`.
- Run `ruff format` in a separate command before any push.
- 4 unrelated tests in tests/unit/config fail on main.
- Shards can fail at start on the weekly limit. Relaunch once; if it recurs, card the owner.
- Register → attest → register.
- The status/CAISO.js rebase conflict: re-run `build_status.py --iso CAISO`.
- Never `git grep` in a partial clone.

HARD RULES: CLAUDE.md is binding, especially rules 1, 13, 14, 19, 21, 23–25, 27, 28, 29(b)/(c), and 30–36.
- Owner decisions go to the owner as clickable decision cards (AskUserQuestion, multiSelect where choices are not
  exclusive), never inline text.

END OF SESSION:
- Promote if the candidate is good. Create a PR and rebase-merge it.
- Archive every shard, and report leftover shard branches for the owner to delete.
- Then launch R-CAISO-21 (the evening under-price, zero-LP root cause first) with these same directions: archive its
  parent when safe, salvage/close CAISO branches and PRs, present decisions as cards, promote if good, PR + merge,
  archive shards, and launch the next link (C3c 2024 after it).
- If at the nesting limit, make the final message a complete handoff prompt in one code block.
