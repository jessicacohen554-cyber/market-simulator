SESSION R-CAISO-24 — CAISO: battery-disaggregation scoping for the RT h18 ramp peak (link 6). SCOPING ONLY.
DATA PROFILE: caiso
MODEL: Opus or Fable

FIRST:
- Archive R-CAISO-23 (its session id is in your launch prompt) with mcp__Claude_Code_Remote__archive_session,
  only once its PR (branch `claude/caiso-midday-rt-spread-root-cause-u0q8et`) reads MERGED on the GitHub MCP.
  If it is not merged, do not archive, and say so.
- Check for unmerged CAISO branches and open CAISO PRs. Salvage anything not on main into your branch,
  close the PRs you salvaged, and report which branches the owner can delete. Deleting a ref returns 403,
  so do not try. Known leftovers that carry nothing absent from main: `claude/r-caiso-22`,
  `claude/caiso-midday-rt-spread-root-cause-u0q8et`.
- Work on a fresh branch off origin/main.

STATE (2026-10-01):
- Keeper `2026-09-30-caiso-r20-overnight` (bundle rcaiso20_A_span, 2022–25) is CALIBRATED with one ledgered
  C3c 2024. The fold `-touchpoints` (2019–21) is NOT-YET, so the ISO determination is NOT-YET under v3.13.
  The fold DSW residual is LEDGERED as data-availability limited (R-CAISO-20). Do not re-open it without a
  new pre-2021 hourly Palo Verde source.
- R-CAISO-21 (zero LP) closed the evening under-price as DART basis + C3c tail.
- R-CAISO-22 (zero LP) found no admissible lever for C3c 2024 (docs/handoffs/r-caiso-22/).
- R-CAISO-23 (zero LP) found no admissible lever for the midday RT N–S spread
  (docs/handoffs/r-caiso-23/FINDING-r-caiso-23-ns-spread-2026-10-01.md; probe
  scripts/probes/_rcaiso23_ns_spread_phase0.py). The spread is collapsed, not wrong-signed: model ~$1 vs
  measured +$11–19, all on Path 15, set by stranded southern solar behind Gates–Midway element limits. It is
  ledgered as data-availability limited (a C3b / D-A fidelity object, not a C3a lever).

TASK (owner card 2026-09-30, link 6):
- SCOPING ONLY (PRECOMMIT, no solve, no build) of a disaggregated battery representation for the RT h18 ramp
  peak. SP15_rest RT model − measured at h18: −13.9 / −6.0 / −1.1 $/MWh (2023–25; R-CAISO-21 FINDING §2b).
  The 2025 residual is near zero, so state up front what payoff is left to buy.
- It must be measured and structural, not a fitted shape. Every existing storage cell is R/I/G:
  caiso_da_rt_two_settlement R, storage_daily_cycling G, ercot_storage_adaptive_expectation I;
  battery_dispatch_adder K at 0. The one untested pointer is the aggregated battery representation
  (caiso-170 re-point). Check the CAISO shard and lever queue (docs/mechanism-testing-matrix.md §5.2)
  before proposing anything. Never re-test an R/I/G cell without new evidence.
- Name the measured inputs a disaggregation would need (per-fleet duration, SOC bounds, the RA must-offer
  window, CAISO's battery bid data), say which the repo holds, and give a zero-LP bound on the h18 payoff.
- End with a decision card to the owner. Build nothing.

QUEUED AFTER YOU (owner cards 2026-09-30 and 2026-10-01, all selected). Carry these into your
end-of-session handoff in this order:
- Link 7, R-CAISO-25: SCOPING ONLY, no solve. Look for a measured same-day/intraday CA citygate gas series
  for the winter event days (Jan 2023, Jan 2024). R-CAISO-22 §3: the measured event price implies HR 15.5
  on the next-day composite print the model uses (the model gets 10.3). A higher same-day fuel price is a
  rule-13-admissible input. The ICE daily index already failed as a 2019–20 hub print (R-CAISO-12), so say
  whether 2022–25 differs. Build nothing; end with a decision card.
- Link 8, R-CAISO-26: SCOPING-ONLY PRECOMMIT, no build. Find a measured, forward-regenerating state
  variable that reduces firm-import delivery when the NW/DSW is short. R-CAISO-22 §2: the firm floor stays
  at 2.4 GW while measured net import fell to 0.6–0.8 GW (Malin $230–255). ADDED by the R-CAISO-23 owner
  card: R-CAISO-23 FINDING §4 — on Jan 13 and 15 2024 the model's PNW node prices at $0 while Malin DAM was
  $177–219 (the node is long). State up front that the delta is 2024-specific (2022/2023 events
  −1.2/−0.75 GW), that the C3c payoff is bounded at ≤ 1 hour (R-CAISO-22 §3), and that caiso-150 §H's
  DO-NOT-REDO list (the self-schedule ceiling, the direction wall) binds.
- Link 9, R-CAISO-27 (ADDED by the R-CAISO-23 owner card 2026-10-01): SCOPING ONLY, no build. Look for a
  measured, backcast-admissible transmission-outage or derate record for the Path-15 / Gates–Midway complex,
  2022–25. It is the only re-arm route for `caiso_fsno_subzonal_topology` (R; caiso-224 caps falsified).
  It must be a physical availability input (rule 13), never a constraint shadow price or curtailment outcome.
  caiso-218 found no published internal-path operating-limit series 2023–25. End with a decision card.

OWNER RULINGS IN FORCE (do not re-ask): all rulings in HANDOFF-r-caiso-19/-20/-21/-22/-23, the R-CAISO-21
FINDING §7, the R-CAISO-22 FINDING §6 and the R-CAISO-23 FINDING §7.

NOTES:
- Fresh container: `pip install -e . pytest tzdata`, then `python3 scripts/hydrate_data.py --profile caiso`.
- Run `ruff format` as a separate command before any push. 4 unrelated tests in tests/unit/config fail on main.
- Shards can fail at start on the weekly limit. Relaunch once, then card the owner.
- Order is register → attest → register. A status/CAISO.js rebase conflict → re-run build_status.py --iso CAISO.
- check_registry_payload_parity flags your own gitignored legs locally (rule 31); they are absent in CI.
- Never `git grep` in a partial clone. Shards read long prompts from an immutable SHA
  (`git show <sha>:<path>`).
- The zero-LP offer-stack rebuild takes ~90 s per year (R-CAISO-22 `--stack`).

HARD RULES: CLAUDE.md is binding, especially rules 1, 13, 14, 19, 21, 22, 23–25, 27, 28, 29(b)/(c), 30–36.
Owner decisions go as clickable decision cards (AskUserQuestion, multiSelect where the choices are not
exclusive), never as inline text.

END OF SESSION:
- Promote if a candidate is good (this link is scoping only, so expect none). PR + rebase-merge. Archive every
  shard and report leftover shard branches.
- Then launch R-CAISO-25 (link 7) with these same directions. It archives you when safe, salvages and closes
  CAISO branches and PRs, uses decision cards, promotes if good, does PR + merge, and archives shards.
- If you are at the nesting limit, make your final message a complete handoff prompt in one code block.
