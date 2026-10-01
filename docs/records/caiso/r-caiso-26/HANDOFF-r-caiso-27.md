SESSION R-CAISO-27 — CAISO: Path-15 / Gates–Midway derate-data scoping (link 9). SCOPING ONLY, no build.
DATA PROFILE: caiso
MODEL: Opus or Fable

FIRST:
- Archive R-CAISO-26 (its session id is in your launch prompt) with mcp__Claude_Code_Remote__archive_session,
  only once its PR (branch `claude/r-caiso-26`) reads MERGED on the GitHub MCP. If it is not merged, do not
  archive, and say so.
- Check for unmerged CAISO branches and open CAISO PRs. Salvage anything not on main into your branch,
  close the PRs you salvaged, and report which branches the owner can delete. Deleting a ref returns 403,
  so do not try. Known leftovers that carry nothing absent from main: `claude/r-caiso-22`,
  `claude/caiso-midday-rt-spread-root-cause-u0q8et`, `claude/r-caiso-24`, `claude/r-caiso-25`,
  `claude/r-caiso-26`.
- Work on a fresh branch off origin/main.

STATE (2026-10-01):
- Keeper `2026-09-30-caiso-r20-overnight` (bundle rcaiso20_A_span, 2022–25) is CALIBRATED with one ledgered
  C3c 2024. The fold `-touchpoints` (2019–21) is NOT-YET, so the ISO determination is NOT-YET under v3.13.
- R-CAISO-21..-25 (zero LP): evening = DART basis + C3c tail; no lever for C3c 2024; midday N–S spread
  ledgered; h18 body residual ledgered; no public same-day CA gas series.
- R-CAISO-26 (zero LP; docs/records/caiso/r-caiso-26/, probe scripts/probes/_rcaiso26_nw_intertie.py): the
  NW-stress import premise is falsified. Over MLK 2024, 82 % of the net-import collapse was gross EXPORT to
  the NW (+1,847 MW; BPAT −1,170, BANC −554); gross import fell 404 MW. CAISO OASIS `TRNS_USAGE` (hourly
  intertie OTC net of outage derates; mid-2023+; INTERTIES ONLY) shows NW import OTC at full seasonal TTC
  (4,771 MW); the NOB outage cut export OTC 510 → 0. No lever; no cell moved.

TASK — link 9 (owner cards 2026-09-30 / 2026-10-01):
- SCOPING ONLY, no build. Look for a measured, backcast-admissible transmission-outage or derate record for
  the Path-15 / Gates–Midway complex, 2022–25. It is the only re-arm route for `caiso_fsno_subzonal_topology`
  (R; caiso-224 caps falsified). It must be a physical availability input (rule 13), never a constraint
  shadow price or curtailment outcome. caiso-218 found no published internal-path operating-limit series
  2023–25 (TTC/ATC discontinued 2018-11).
- Already checked by R-CAISO-26: OASIS `TRNS_USAGE` carries interties only (no Path 15 / Path 26 rows). Do
  not re-test it for Path 15. Other candidates to scope: CAISO OASIS transmission-outage reports, the CAISO
  Outage Management System public transmission outage report and its retention, PG&E / WECC path-rating
  or derate postings, DMM quarterly/annual congestion chapters (element-level outage attributions), FERC
  filings. State coverage, granularity, retention and the rule-13 test for each.
- End with a decision card.

QUEUED AFTER YOU (all owner-selected). Carry these into your end-of-session handoff in this order:
- Link 10, R-CAISO-28: SCOPING ONLY, no build. Look for a per-class behavioural battery input for CAISO,
  2023–25: per-resource (or per-duration-class) SOC, or unmasked battery bid curves (OASIS PUB_DAM_GRP is
  masked with no fuel tag; caiso-176/178 found it does not identify a battery offer parameter). The only new
  evidence that could re-open R-CAISO-24 §5. State up front that the R-CAISO-24 bound is ≤ $0.5/MWh at h18.
  End with a decision card.
- Link 11, R-CAISO-29: SCOPING ONLY, no build. Decompose CAISO OASIS PRC_FUEL against the model's delivered
  gas (NGI CA composite, flow-dated, + CAISO_CITYGATE_TRANSPORT_ADDER 0.46). R-CAISO-25 §4: PRC_FUEL runs
  +2.9 (SCE/SDG&E) / +4.1 (PG&E) $/MMBtu above it year-round in 2024 (r ≈ 0.97). Evidence for the open
  transport-adder methodology ask (rule 14), not a C3c lever. The keeper's offer-band multipliers were set
  against the model's own delivered series, so the offset is not a price error until decomposed.
  Probe: scripts/probes/_rcaiso25_prc_fuel.py (OASIS returns empty for some months; retry slowly).
  End with a decision card.
- Link 12, R-CAISO-30 (ADDED by the R-CAISO-26 owner card 2026-10-01): DATA INTAKE ONLY, no solve, no arm.
  Intake CAISO OASIS `TRNS_USAGE` (DAM) hourly intertie OTC / seasonal TTC / TRM by ITC and direction, from
  the earliest retained month (present 2023-07-01, empty 2023-06-01; bisect the start) through 2025, via the
  `data-intake` skill (schema-first, write_clean/read_clean). Rolling OASIS retention: earliest months roll
  off while this waits; state what was lost. Purpose: a rule-14 measured basis for the corridor caps (today
  the p95 envelope of measured flows, caiso-162/280). caiso-280 found the envelope binds above actuals, so
  expect no fit gain; do not arm anything. Query: `queryname=TRNS_USAGE&market_run_id=DAM`, ~5 MB CSV/day,
  11 days per request worked. End with a decision card.

OWNER RULINGS IN FORCE (do not re-ask): all rulings in HANDOFF-r-caiso-19..-26, the R-CAISO-21 FINDING §7,
the R-CAISO-22 FINDING §6, the R-CAISO-23 FINDING §7, the R-CAISO-24 PRECOMMIT §7, the R-CAISO-25 FINDING §6
and the R-CAISO-26 PRECOMMIT §6.

NOTES:
- Fresh container: `pip install -e . pytest tzdata`, then `python3 scripts/hydrate_data.py --profile caiso`
  (a full clone reports "re-run with --force"; data is already present then).
- Run `ruff format` as a separate command before any push. 4 unrelated tests in tests/unit/config fail on main.
- Shards can fail at start on the weekly limit. Relaunch once, then card the owner.
- Order is register → attest → register. A status/CAISO.js rebase conflict → re-run build_status.py --iso CAISO.
- check_registry_payload_parity flags your own gitignored legs locally (rule 31); they are absent in CI.
- Never `git grep` in a partial clone. Shards read long prompts from an immutable SHA
  (`git show <sha>:<path>`).
- The zero-LP offer-stack rebuild takes ~90 s per year (R-CAISO-22 `--stack`).
- The keeper's slim bundle has no per-plant dispatch, so link flows are not in the committed hourlies.

HARD RULES: CLAUDE.md is binding, especially rules 1, 13, 14, 19, 21, 22, 23–25, 27, 28, 29(b)/(c), 30–36.
Owner decisions go as clickable decision cards (AskUserQuestion, multiSelect where the choices are not
exclusive), never as inline text.

END OF SESSION:
- Promote if a candidate is good (this link is scoping only, so expect none). PR + rebase-merge. Archive every
  shard and report leftover shard branches.
- Then launch R-CAISO-28 (link 10) with these same directions. It archives you when safe, salvages and closes
  CAISO branches and PRs, uses decision cards, promotes if good, does PR + merge, and archives shards.
- If you are at the nesting limit, make your final message a complete handoff prompt in one code block.
