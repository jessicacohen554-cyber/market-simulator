# HANDOFF — NWPP-NEXT-18: NWPP hydro within-month freedom (price formation), after NEXT-17's phase 0

```
SESSION NWPP-NEXT-18 — NWPP calibration: hydro within-month freedom (flat monthly water value), keeper #20
DATA PROFILE: nwpp
MODEL: Opus or Fable
CLAUDE.md is binding. Pay particular attention to rules 1, 5, 13, 14, 17, 19, 21, 23, 24, 26, 28, 29 and 31–36.
The parent never solves (rule 32(a)). Every backcast year gets its own shard (rule 36).

CHAIN DIRECTIONS (owner, standing; pass them on verbatim to every handoff you launch)
- First, when it is safe, archive the previous session: session_019W6gJV9net5Nj9BPwTtMcj (NWPP-NEXT-17).
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
- Keeper #20 unchanged: 2026-10-01-nwppnext16c-combined-vintage (bundle results/calibration/nwppnext16c_span, 2019–2025,
  pin 33014efc). NOT-YET on {dispatch_corr}, ONE record: C4 coal 2023 r 0.669 / NRMSE 0.313. Price UNSCORED.
- NEXT-17 ran zero LP only. Owner card 2026-10-01: "Redirect to hydro".
- Read first:
  - docs/records/nwpp/FINDING-nwppnext17-bridger-price-formation-phase0-2026-10-01.md (THE evidence; all of it)
  - scripts/probes/_nwppnext17_bridger_price_phase0.py (reproduces every table from one leg dir)
  - ScenarioConfig.hydro_budget_period_by_instrument docstring + constants.HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT
  - NYISO's rejection of that mechanism (mechanism-matrix/NYISO.js hydro_budget_period_by_instrument, nyiso-236..238)
  - NWPP.js cells hydro_pondage_bound (NWPP-49 design a2, not adopted), hydro_cascade_coupling (K), hydro_dispatch_envelope (K)
  - docs/calibration-log/nwpp.md (NEXT-17 entry), matrix doc §5.9

TASK — phase-0 design of NWPP hydro within-month freedom (no solve until its own owner card)
- The object: keeper #20's north-zone price (EAST/INLAND/NW/OR clear at one price) is the monthly hydro water value. In
  2023, within-day and between-day SD are ~1/10 of WEIM PACE/IPCO/BPAT in every month Jun–Dec. Jul and Oct means are
  $15–30 low. C4 coal 2023 (Bridger idling Jun–Oct) is the visible symptom.
- Keeper #20's per-year legs carry dispatch/<Y>_P1.parquet and hourly/unit_hourly_<Y>.parquet (mc, red_cost):
  C legs 2019 1e4bd215 · 2020 aa60aa43 · 2021 3b38fefe · 2022 11bb59fb · 2023 a54c7b97 · 2024 91f0bc29 · 2025 1a41ba51
  (`git fetch origin claude/nwppnext16c-<Y>` then `git archive <sha> results/calibration/nwppnext16c_<Y> | tar -x -C <scratch>`).
- ZERO LP FIRST:
  1. Which plants carry the water value system-wide (all north zones, all years with WEIM 2023-06..2025)? By pondage,
     cascade membership (nwpp_hydro_chain.csv), nameplate. Is it the Columbia storage projects, or many small reservoirs?
  2. Does measured within-month variance exist for those plants' output (EIA-930 NG:WAT by BA, CROHMS hourly/daily for
     cascade projects)? The model must lose freedom only where measurement says the plant lacks it.
  3. For each candidate price setter: the governing instrument that limits day-to-day reallocation (license, BiOp flow
     objectives, Hanford Reach / Vernita Bar for Priest Rapids, Columbia River Treaty operating plans, irrigation contracts).
     Registry entries need a citation each (rule 17 driver / window / forward story; rule 5).
  4. Rule 19: reconcile with hydro_dispatch_envelope, hydro_cascade_coupling, hydro_ror_split, hydro_min_flow_floor before
     adding anything. Also check whether the envelope ceiling is ever binding in the price-setting hours.
- Arm a mechanism ONLY if it is measured, forward-reproducible and per-plant (rule 13). Never a price adder, a hydro
  shape pin, or a tuned period length. Owner card before any solve; 7 shards per arm.
- Optional if C3 price scoring for NWPP is opened by the scorer lane: the §3 table is a ready benchmark.

CLOSED — do NOT redo
- Everything closed in HANDOFF-nwppnext7 through -nwppnext17.
- NEXT-17: the "Bridger seasonal offer" lever is CLOSED as mis-targeted (a Bridger-specific offer change would be fitted to
  the flat-price error; rules 1, 13). The Oct–Dec 2023 Jim Bridger Mine captive price spike ($3.7 → $5.3/MMBtu) is real
  but worth ~0.1 TWh; not a lever on its own.
- hydro_pondage_bound on low-pondage plants alone: §2 of the FINDING shows the ≥720 h plants still set the price.
- NEXT-16 (R): coal_captive_marginal_fuel_price, live-capacity screened-coal WEFOR. Offer-multiplier tuning on C1 / C4 / CT.

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
  claude/nwppnext15-2019 … -2025, claude/nwppnext16d-2019 … -2025, claude/nwppnext16e-2019 … -2025, claude/nwppnext16,
  claude/nwpp-next14-arm-solve-2e8zh1, claude/charming-gates-b7riij, claude/nwppnext17 (after its PR merges).
- Session session_01HaVKmdZywZXNPEZ2Y9Ssf5 (NEXT-16): NEXT-17's archive call was refused by the permission classifier;
  archive it if it is still live.
- KEEP claude/nwppnext16c-2019 … -2025 until NEXT-18's phase 0 is done: they are the only copy of keeper #20's dispatch
  and unit_hourly parquets (gitignored on main).
```
