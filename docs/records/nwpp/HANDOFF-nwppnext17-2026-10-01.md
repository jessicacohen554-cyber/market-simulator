# HANDOFF — NWPP-NEXT-17: Bridger seasonal offer, after keeper #20

```
SESSION NWPP-NEXT-17 — NWPP calibration: Jim Bridger's seasonal dispatch (C4 coal 2023), keeper #20
DATA PROFILE: nwpp
MODEL: Opus or Fable
CLAUDE.md is binding. Pay particular attention to rules 1, 5, 13, 14, 19, 21, 23, 24, 26, 28, 29 and 31–36.
The parent never solves (rule 32(a)). Every backcast year gets its own shard (rule 36).

CHAIN DIRECTIONS (owner, standing; pass them on verbatim to every handoff you launch)
- First, when it is safe, archive the previous session: session_01HaVKmdZywZXNPEZ2Y9Ssf5 (NWPP-NEXT-16).
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

FIRST: CHECK FOR A PARALLEL LANE. List sessions, `git ls-remote --heads origin 'claude/*nwpp*'`, and open NWPP PRs.
If another live NWPP session works the same lever, put that on an owner card before spending LP.

STATE ON MAIN
- Keeper #20: 2026-10-01-nwppnext16c-combined-vintage (bundle results/calibration/nwppnext16c_span, 2019–2025, solved
  on pin 33014efc with the requirements.txt libraries).
  Recipe: keeper #19 with campd_unit_fuel_split -> false and campd_per_unit_vintage_denominator -> true
  (eia923_cc_family_heat_rates stays true). The per-unit fuel-split composition is DELETED (rule 26): arming
  campd_unit_fuel_split with campd_per_unit_attribution now raises.
- NOT-YET on {dispatch_corr}, ONE record: C4 coal 2023 r 0.669 / NRMSE 0.313 (floor 0.70 / 0.30). Price UNSCORED.
- Read first:
  - docs/records/nwpp/RESULT-nwppnext16-combined-captive-live-2026-10-01.md (arms C/D/E, Bridger 2023 by month)
  - docs/records/nwpp/FINDING-nwppnext14-bridger-and-clark-phase0-2026-09-30.md §1 (Bridger's offer, take floor, Jun–Oct)
  - docs/records/nwpp/PRECOMMIT-nwppnext16-combined-captive-live-2019-2025-2026-10-01.md (template: §3 G-DRIFT, §4 recipe,
    §5 stops) and docs/records/nwpp/nwppnext16/shards/shard_c_<Y>.txt (the shard prompt template)
  - docs/calibration-log/nwpp.md (NEXT-16 entry), mechanism-matrix/NWPP.js, matrix doc §5.9

TASK — Bridger seasonal offer (owner card 2026-10-01, NEXT-17 lever)
- The object: keeper #20's Jim Bridger 8066 coal in 2023 by month (TWh) is
  1.37 1.32 0.94 0.61 0.19 0.25 0.36 1.37 0.31 0.21 0.80 0.78 — idle Jun–Oct except August.
  CEMS has Bridger running through Jun–Oct (FINDING-nwppnext14 §1: CEMS in Jun–Oct alone lifts fleet r to 0.821).
- Known: its annual burn equals the soft take floor (93.9 TBtu vs CEMS 100.4), and the LP spends it in dear-gas Q1.
  coal_fuel_inventory_monthly_pile is already armed. Arm D (captive-mine econ price) moved energy into Nov–Dec,
  not Jun–Oct, so the problem is not the econ tranche's price level.
- ZERO LP FIRST: decompose why the LP prefers Q1. Check the monthly pile constraint's binding months and duals, Bridger's
  offer by month vs zonal LMP (keeper #20 dispatch/2023_P1.parquet carries lmp), the must-run / committed tranche by
  month, and outage windows. Use the keeper's committed hourly sidecars plus the dispatch parquet (gitignored; re-derive
  from a shard or ask before spending LP).
- Arm a mechanism ONLY if it is measured, forward-reproducible and per-plant (rule 13), never a tuned passthrough or a
  monthly burn pin (outcome pin). Before proposing, check the matrix lever queue and the CLOSED list below.
- Owner card before any solve; 7 shards per arm.

CLOSED — do NOT redo
- Everything closed in HANDOFF-nwppnext7 through -nwppnext15.
- NEXT-16 (R): coal_captive_marginal_fuel_price (arm D), unit_outage_dispatched_bin_live_denominator +
  wefor_residual_short_screened_coal with wefor_residual 0.0 on coal (arm E). campd_unit_fuel_split under per-unit (deleted).
- Bridger Feb–May 2023 inventory conservation (outcome pin, rule 13); offer-multiplier tuning on C1 / C4 / CT.
- Clark's CC heat rate (settled). cc_subfloor_eia923_heat_rates is DELETED; do not re-add it.
- The benchmark fossil reconcile is the scorer lane's.

PROCEDURE FOR ANY SOLVE (PARENT GOTCHAS, learned in NEXT-15/16)
- Shard setup: `pip install --ignore-installed pyyaml==6.0.3 && pip install -r requirements.txt && pip install -e . --no-deps`
  (plain `pip install -r` fails on the container's Debian PyYAML); STEP-1 hard stop prints highspy/pandas/pyarrow/pydantic
  = 1.14.0 / 3.0.3 / 24.0.0 / 2.13.4.
- Tell every shard: do NOT run legitimacy_diagnostics or any scorer; a legitimacy FAIL is never a shard hard stop; push
  without asking (cloud shards cannot be messaged — a shard that stops to ask strands its bundle).
- Point each shard at a committed prompt file (docs/handoffs/<lane>/shards/shard_<arm>_<Y>.txt) at the pinned SHA; keep
  the create_session prompt short.
- G-DRIFT against keeper #20's pin 33014efc27296bf78842c4a50f311fe191c82b07.
- Hard-stop demand: 279.581 / 292.940 / 289.358 / 298.960 / 280.261 / 290.216 / 302.532 TWh.
- `git checkout <sha> -- <leg dir>` stages the leg; follow with `git rm -r -q --cached <leg dir>` and gitignore the family.
- Compose with scripts/probes/_nwpp42_compose_span.py --skip-diagnostics (2023 leg first); then
  legitimacy_diagnostics.py --bundle B --iso NWPP --years 2019..2025 --json-out B/legitimacy_diagnostics.json (exit 1 is
  normal); `git fetch --depth=1 origin 909cdd30bfdd8a398b10a4255b1340d0d9ef1943`; an attestation wrapping
  scripts/gen_nwppnext16_attestation.py; dashboard_add_run.py --no-prune; calibration_verdict.py --run-id <id> --json,
  diffed per (criterion, year, key) record (criteria.<name>.records, field `model` for C4).
- Promotion + prune on ONE owner card; rule 35: enumerate year set, audit_keepers --iso NWPP between promote and prune,
  prune_iso_runs.py --iso NWPP; re-stamp §5.9 and the matrix keeper/gates; check_forecast_parity NWPP UNACCOUNTED 0.

KNOWN ISSUES on main (not NWPP's; report, do not fix)
- FR-22 parity red for CAISO (caiso_eia930_clock_repair, caiso_tac_shares_standard_time UNACCOUNTED).
- tests/unit/data/test_gas_offer_zonal_anchor_vintage.py fails (2 tests), plus other lanes' fast-tier failures.

HOUSEKEEPING (owner; a session cannot delete refs, HTTP 403)
- Leftover branches: claude/nwppnext13-2019 … -2025, claude/nwppnext14, claude/nwppnext14-2019 … -2025,
  claude/nwppnext15-2019 … -2025, claude/nwppnext16c-2019 … -2025, claude/nwppnext16d-2019 … -2025,
  claude/nwppnext16e-2019 … -2025, claude/nwpp-next14-arm-solve-2e8zh1, claude/charming-gates-b7riij.
```
