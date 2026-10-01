SESSION R-CAISO-22 — CAISO: C3c 2024 price tail, ZERO-LP ROOT CAUSE FIRST
DATA PROFILE: caiso
MODEL: Opus or Fable

FIRST:
- Archive R-CAISO-21 (session_01D3tvHiM7QbHKsEF5j1wXt2) with mcp__Claude_Code_Remote__archive_session.
  - Only once its PR (branch `claude/r-caiso-21`) reads MERGED on the GitHub MCP. If not, do not archive; say so.
- Check for unmerged CAISO branches and open CAISO PRs; salvage anything not on main into your branch, close the
  PRs you salvaged, and report which branches the owner can delete (deleting a ref returns 403 — do not try).
  Known leftovers carry nothing that is not on main: `claude/r-caiso-18-*`, `claude/r-caiso-19*`,
  `claude/r-caiso-20*`, `claude/r-caiso-21`.
- Work on a fresh branch off origin/main.

STATE (2026-09-30):
- Keeper `2026-09-30-caiso-r20-overnight` (bundle rcaiso20_A_span, 2022–25) CALIBRATED with one ledgered C3c 2024.
  Fold `-touchpoints` (2019–21) NOT-YET (fuelmix, dispatch_corr, price_mean 2021); ISO determination NOT-YET
  under rubric v3.13. The fold DSW residual is LEDGERED data-availability limited (R-CAISO-20): do not re-open it
  without a new pre-2021 hourly Palo Verde source.
- R-CAISO-21 (docs/handoffs/r-caiso-21/FINDING-r-caiso-21-evening-2026-09-30.md), zero LP, CLOSED the evening
  under-price: on the gated RT basis the SP15 h17–22 residual is +7.0/−3.7/−2.5/−1.2 $/MWh (2022–25); the DAM gap is
  72–80 % measured DART; 80–100 % of the 2023–25 RT residual lies in the top-5 % measured evening hours. **Those
  tail hours are now yours.** Probe: scripts/probes/_rcaiso21_evening_phase0.py (reuse its clock/hub alignment).
- Prior record on the tail (matrix §5.2): caiso-144 found the reserve pool slack in every real RT >$200 hour
  (`energy_reserve_coopt` I) and read the C3c tail as a winter-morning fuel event, not scarcity; caiso-204/205
  `ercot_storage_adaptive_expectation` I (0/1/0 spike days); storage bid surface closed; caiso-272 DA vs RT on the
  2023/2024 tail. Check the CAISO shard before proposing anything; never re-test an R/I/G cell without new evidence.

TASK (owner card 2026-09-30, link 4 "C3c 2024 price tail"):
1. PHASE 0, ZERO LP, on the keeper's committed hourly sidecars (2022–25 first, 2024 the target):
   - list the measured RT tail hours (C3c's own definition in scripts/calibration_verdict.py) by month/hod/zone and
     the model price in each; separate the winter-morning gas-event hours from summer-evening hours;
   - for each group name the model's marginal tranche and the supply stack vs measured references (imports by
     corridor vs EIA-930, CC/CT, storage vs the CAISO Outlook batteries series, hydro), and the input that would
     have to differ (e.g. daily gas price for the event days) — say which mechanism sets the price and why it is low.
2. Admissible, structural, measured lever (rules 1, 13, 14, 19, 21, 23–25) → PRECOMMIT with pre-registered values
   and decision rule → default-off flag + tests + matrix row (rule 28(c)) → PR → merge → pin full SHA → 7 shards,
   one per year 2019–2025 (rule 36); the parent never solves; the 2025 shard needs a 50-min budget.
3. None → FINDING, build nothing, decision card to the owner. A lone C3c is already a non-downgrading ledgered
   caveat (rule 22 [R-C3C]); closing it is worth a lever only if the mechanism is real.
4. PARENT SEAM (as R-CAISO-20): compose with scripts/probes/rcaiso_compose_span.py + the seven --require flags
   (caiso_eia930_clock_repair=true, caiso_tac_shares_standard_time=true, caiso_ra_bridge_startup_aware=false,
   cc_eia923_identity_emission_basis=true, caiso_supply_consistent_demand=true,
   caiso_intertie_unprinted_year_measured_gas=true, caiso_dsw_overnight_clean_unprinted_arm=true) plus your flag;
   legitimacy_diagnostics.py --bundle … --iso CAISO --json-out …; dashboard_add_run --no-prune; attestation from a
   copy of scripts/gen_rcaiso20_attestation.py (keep its owner-ruling text); register again;
   stamp_touchpoint_holdout.py; audit_keepers; prune_iso_runs.py --iso CAISO --force-uncite --keep <new fold id>;
   build_status.py --iso CAISO. Re-stamp the matrix shard + §5.2 header, keepers/CAISO.json, the
   calibration-complete.json CAISO entry and frontend/data/forecast/program-status.json gate (a) — targeted text
   replacement, never a full JSON re-dump.

QUEUED AFTER YOU (owner card 2026-09-30, all selected) — carry into your end-of-session handoff:
- Link 5, R-CAISO-23: the midday RT north–south spread. The model's NP15–SP15 midday spread has the wrong sign
  (SP15 h10–16 +9.7/+10.9/+7.0, ZP26 +10.8/+10.7/+7.1, NP15 −4.8/−7.9/−3.6 $/MWh, 2023–25, vs RT); zero-LP root
  cause first (Path 15/26 flows vs measured, southern solar/curtailment). Note caiso-167 closed the corridor/export
  family and caiso-202/215 hold the diurnal_price_amplitude (U) evidence.
- Link 6, R-CAISO-24: SCOPING ONLY (PRECOMMIT, no solve) of a disaggregated battery representation for the RT h18
  ramp peak (−13.9/−6.0/−1.1 $/MWh 2023–25). Must be measured and structural, not a fitted shape; every existing
  storage cell is R/I/G (caiso_da_rt_two_settlement R, storage_daily_cycling G, ercot_storage_adaptive_expectation I).

OWNER RULINGS IN FORCE (do not re-ask): all rulings in HANDOFF-r-caiso-19/-20/-21 and the R-CAISO-21 FINDING §7.

NOTES: fresh container → `pip install -e . pytest tzdata`, `python3 scripts/hydrate_data.py --profile caiso`.
`ruff format` in a separate command before any push. 4 unrelated tests in tests/unit/config fail on main.
Shards can fail at start on the weekly limit: relaunch once, then card the owner. Register → attest → register.
status/CAISO.js rebase conflict → re-run build_status.py --iso CAISO. check_registry_payload_parity flags your own
gitignored legs locally (rule 31), absent in CI. Never `git grep` in a partial clone. Shards read long prompts from
an immutable SHA (`git show <sha>:<path>`).

HARD RULES: CLAUDE.md binding, especially rules 1, 13, 14, 19, 21, 22, 23–25, 27, 28, 29(b)/(c), 30–36. Owner
decisions go as clickable decision cards (AskUserQuestion, multiSelect where not exclusive), never inline text.

END OF SESSION: promote if the candidate is good; PR + rebase-merge; archive every shard and report leftover shard
branches; then launch R-CAISO-23 (link 5) with these same directions (it archives you when safe, salvages/closes
CAISO branches and PRs, uses decision cards, promotes if good, PR + merge, archives shards). If at the nesting
limit, make the final message a complete handoff prompt in one code block.
