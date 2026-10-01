SESSION R-CAISO-23 — CAISO: midday RT north–south spread (link 5), ZERO-LP ROOT CAUSE FIRST
DATA PROFILE: caiso
MODEL: Opus or Fable

FIRST:
- Archive R-CAISO-22 (session_01M1WsbMKj3Uuyj5GPxcihAq) with mcp__Claude_Code_Remote__archive_session,
  only once its PR (branch `claude/r-caiso-22`) reads MERGED on the GitHub MCP. If it is not merged, do not
  archive, and say so.
- Check for unmerged CAISO branches and open CAISO PRs. Salvage anything not on main into your branch,
  close the PRs you salvaged, and report which branches the owner can delete. Deleting a ref returns 403,
  so do not try. Known leftovers that carry nothing absent from main: `claude/r-caiso-20*`,
  `claude/r-caiso-21`, `claude/r-caiso-22`.
- Work on a fresh branch off origin/main.

STATE (2026-09-30):
- Keeper `2026-09-30-caiso-r20-overnight` (bundle rcaiso20_A_span, 2022–25) is CALIBRATED with one ledgered
  C3c 2024. The fold `-touchpoints` (2019–21) is NOT-YET, so the ISO determination is NOT-YET under v3.13.
  The fold DSW residual is LEDGERED as data-availability limited (R-CAISO-20). Do not re-open it without a
  new pre-2021 hourly Palo Verde source.
- R-CAISO-21 (zero LP) closed the evening under-price as DART basis + C3c tail.
- R-CAISO-22 (zero LP) found no admissible lever for C3c 2024:
  - The Jan-2024 event price sits above the in-state gas stack's cost at the day's print. Adding +2.3 GW
    of gas demand gives $195; +4 GW gives $201–206; measured is $207–286.
  - The event-hour import excess is 2024-specific.
  - Record: docs/records/caiso/r-caiso-22/FINDING-r-caiso-22-c3c-2024-tail-2026-09-30.md.
  - Probe: scripts/probes/_rcaiso22_tail_phase0.py. Part A is the tail census; `--stack` is the zero-LP
    offer-stack bound via reconstruct_bundle_fleet. Reuse both.

TASK (owner card 2026-09-30, link 5 "midday RT north–south spread"):
1. PHASE 0, ZERO LP, on the keeper's committed hourly sidecars (2022–25):
   - The model's NP15–SP15 midday spread has the wrong sign on RT. Model − measured, h10–16:
     SP15 +9.7/+10.9/+7.0, ZP26 +10.8/+10.7/+7.1, NP15 −4.8/−7.9/−3.6 $/MWh (2023–25). Source:
     R-CAISO-21 FINDING §5, probe scripts/probes/_rcaiso21_evening_phase0.py.
   - ADDED by the R-CAISO-22 owner card: the 7 Jan-2024 C3c tail hours of midday Path-15 congestion
     (Jan 13/15/16, plus Oct 7). Measured NP15 − SP15 is +$579 (NP15 $500–850, SP15 ≈ $0); the model has
     +$4. The sign there is the REVERSE of the chronic midday object. Put both in one Path-15/26 census.
   - Decompose: Path 15/26 flows and limits vs measured, southern solar and curtailment, the WEIM clean
     rungs, and the Palo Verde midday leg. Name the mechanism that sets the zonal split and why it has the
     wrong sign.
   - Prior record: caiso-167 closed the corridor/export family. caiso-202/215/232 hold the
     `diurnal_price_amplitude` (U) evidence; caiso-215 found the compression SOUTH-concentrated.
     caiso-230 found zonal congestion a non-lever for C3a, because C3a is the load-weighted mean.
     Check the CAISO shard and lever queue (docs/mechanism-testing-matrix.md §5.2) before proposing
     anything. Never re-test an R/I/G cell without new evidence.
2. If an admissible, structural, measured lever exists (rules 1, 13, 14, 19, 21, 23–25):
   PRECOMMIT with pre-registered values and a decision rule → default-off flag + tests + matrix row
   (rule 28(c)) → PR → merge → pin the full SHA → 7 shards, one per year 2019–2025 (rule 36). The parent
   never solves. The 2025 shard needs a 50-min budget.
3. If there is none: FINDING, build nothing, and a decision card to the owner.
4. PARENT SEAM (as R-CAISO-20):
   - Compose with scripts/probes/rcaiso_compose_span.py and the seven `--require` flags plus yours:
     caiso_eia930_clock_repair=true, caiso_tac_shares_standard_time=true,
     caiso_ra_bridge_startup_aware=false, cc_eia923_identity_emission_basis=true,
     caiso_supply_consistent_demand=true, caiso_intertie_unprinted_year_measured_gas=true,
     caiso_dsw_overnight_clean_unprinted_arm=true.
   - Then, in order: legitimacy_diagnostics.py --bundle … --iso CAISO --json-out …;
     dashboard_add_run --no-prune; the attestation from a copy of scripts/gen_rcaiso20_attestation.py
     (keep its owner-ruling text); register again; stamp_touchpoint_holdout.py; audit_keepers;
     prune_iso_runs.py --iso CAISO --force-uncite --keep <new fold id>; build_status.py --iso CAISO.
   - Re-stamp the matrix shard and §5.2 header, keepers/CAISO.json, the calibration-complete.json CAISO
     entry, and frontend/data/forecast/program-status.json gate (a). Use targeted text replacement, never a
     full JSON re-dump.

QUEUED AFTER YOU (owner cards 2026-09-30, all selected). Carry these into your end-of-session handoff in
this order:
- Link 6, R-CAISO-24: SCOPING ONLY (PRECOMMIT, no solve) of a disaggregated battery representation for the
  RT h18 ramp peak (−13.9/−6.0/−1.1 $/MWh 2023–25). It must be measured and structural, not a fitted
  shape. Every existing storage cell is R/I/G: caiso_da_rt_two_settlement R, storage_daily_cycling G,
  ercot_storage_adaptive_expectation I.
- Link 7, R-CAISO-25: SCOPING ONLY, no solve. Look for a measured same-day/intraday CA citygate gas series
  for the winter event days (Jan 2023, Jan 2024). R-CAISO-22 §3: the measured event price implies HR 15.5
  on the next-day composite print the model uses (the model gets 10.3). A higher same-day fuel price is a
  rule-13-admissible input. The ICE daily index already failed as a 2019–20 hub print (R-CAISO-12), so say
  whether 2022–25 differs. Build nothing; end with a decision card.
- Link 8, R-CAISO-26: SCOPING-ONLY PRECOMMIT, no build. Find a measured, forward-regenerating state
  variable that reduces firm-import delivery when the NW/DSW is short. R-CAISO-22 §2: the firm floor stays
  at 2.4 GW while measured net import fell to 0.6–0.8 GW (Malin $230–255). State up front that the delta
  is 2024-specific (2022/2023 events −1.2/−0.75 GW), that the C3c payoff is bounded at ≤ 1 hour (§3), and
  that caiso-150 §H's DO-NOT-REDO list (the self-schedule ceiling, the direction wall) binds.

OWNER RULINGS IN FORCE (do not re-ask): all rulings in HANDOFF-r-caiso-19/-20/-21/-22, the R-CAISO-21
FINDING §7 and the R-CAISO-22 FINDING §6.

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
- Promote if the candidate is good. PR + rebase-merge. Archive every shard and report leftover shard branches.
- Then launch R-CAISO-24 (link 6) with these same directions. It archives you when safe, salvages and closes
  CAISO branches and PRs, uses decision cards, promotes if good, does PR + merge, and archives shards.
- If you are at the nesting limit, make your final message a complete handoff prompt in one code block.
