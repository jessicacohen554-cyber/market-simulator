# HANDOFF — NWPP-NEXT-19: NWPP price-formation census (gas-daily vs priced interface), after NEXT-18's phase 0

```
SESSION NWPP-NEXT-19 — NWPP calibration: price-formation census, gas-daily vs priced interface, keeper #20
DATA PROFILE: nwpp
MODEL: Opus or Fable
CLAUDE.md is binding. Pay particular attention to rules 1, 5, 13, 14, 17, 19, 21, 23, 24, 26, 28, 29 and 31–36.
The parent never solves (rule 32(a)). Every backcast year gets its own shard (rule 36).

CHAIN DIRECTIONS (owner, standing; pass them on verbatim to every handoff you launch)
- First, when it is safe, archive the previous session: session_01XTvTt5gqyhLhWyi2bDzAPa (NWPP-NEXT-18).
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
- NEXT-18 ran zero LP only. Owner card 2026-10-01: "Both, one census".
- Read first:
  - docs/records/nwpp/FINDING-nwppnext18-hydro-within-month-phase0-2026-10-01.md (THE evidence)
  - docs/records/nwpp/FINDING-nwppnext17-bridger-price-formation-phase0-2026-10-01.md (§3: the measured vs model price table)
  - scripts/probes/_nwppnext18_hydro_freedom_phase0.py (reproduces NEXT-18's tables from the leg root)
  - NWPP.js cells priced_interchange (U), reference_price_interface (U), gas_daily_shape (U); how other ISOs armed them
    (PJM gas_daily_shape K; SOCO/PJM/MISO reference_price_interface; CAISO caiso_intertie_reference_price)
  - data/raw/gas-prices/SOURCES_nwpp_gas.md (which NW hubs have a reachable public series)

TASK — one ZERO-LP census that splits measured NWPP price variance into gas-daily and interface parts, then pick the lever
- The object: keeper #20's north-zone price is flat within each month (within-day / between-day SD ~1/10 of WEIM PACE/IPCO/BPAT
  2023), set by Columbia-chain hydro whose water value equals a flat monthly gas stack. NEXT-18 measured that hydro does NOT
  over-reallocate between days (model/CROHMS 0.75–0.90), so the hydro-period lever is closed for NWPP.
- Census (WEIM hourly 2023-06..2025, Mid-C Peak daily ICE, CAISO hourly RT/DA, Henry Hub daily, Sumas weekly,
  CA citygate daily; all on disk):
  1. Between-day: how much of the daily-mean NW price variance (BPAT, PACE, IPCO, by month) does a daily gas series explain,
     and how much remains for CAISO/West load once gas is controlled for? Say where the NW gas hub series is only weekly
     (Sumas) or absent (Malin, Opal, Stanfield daily), and whether a public daily series is reachable (rule 14).
  2. Within-day: how much of the hourly-demeaned NW price shape does the CAISO shape explain (NEXT-18 §4: PACE r 0.54–0.71,
     BPAT 0.12–0.22)? Is BPAT's low r a clock or data artifact, or real (hydro-dominated BA)?
  3. Price-taker bound: with the measured price imposed, how much do NWPP class energies move (C4 coal 2023 especially)?
     NEXT-17 §4 did this for Bridger only.
  4. Rule 19: reconcile with the fixed EIA-930 interchange schedule. A priced interface REPLACES the fixed schedule, never
     stacks on it. State what holds the measured annual net-interchange energy (rule 13: the quantity must not be pinned
     to observed flows, the price must be forward-reproducible: in a forecast, CAISO is solved by this model).
- Arm a mechanism ONLY if it is measured, forward-reproducible and has a rule-17 window and story. Never a price adder,
  a tuned basis, or a curve fitted to WEIM. Owner card before any solve; 7 shards per arm.
- If C3 price scoring for NWPP is opened by the scorer lane, NEXT-17 §3 is a ready benchmark.

CLOSED — do NOT redo
- Everything closed in HANDOFF-nwppnext7 through -nwppnext18.
- NEXT-18: hydro_budget_period_by_instrument for NWPP (measured between-day freedom is HIGHER than the model's; rule 13).
  Grand Coulee within-day over-shaping (1.44–1.72× CROHMS) is real but not a lever on its own (the LP re-routes swing,
  NWPP-49). hydro_pondage_bound alone (NEXT-17 §2).
- NEXT-17: the Bridger seasonal offer (mis-targeted). NEXT-16 (R): coal_captive_marginal_fuel_price, live-capacity
  screened-coal WEFOR. Offer-multiplier tuning on C1 / C4 / CT.

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
- Model hourly prices per year are on main (results/calibration/nwppnext16c_span/hourly/system_<Y>.parquet). Unit-level
  data (unit_hourly, dispatch) lives only on the leg branches:
  C legs 2019 1e4bd215 · 2020 aa60aa43 · 2021 3b38fefe · 2022 11bb59fb · 2023 a54c7b97 · 2024 91f0bc29 · 2025 1a41ba51
  (`git fetch origin claude/nwppnext16c-<Y>` then `git archive <sha> results/calibration/nwppnext16c_<Y> | tar -x -C <scratch>`).
  Rule 15 asks a keeper to carry unit_marginal_<Y>.parquet on main; keeper #20 does not. The next promotion's
  promote_keeper.py preflight derives it. Report this; do not backfill it outside a promotion.

KNOWN ISSUES on main (not NWPP's; report, do not fix)
- FR-22 parity red for CAISO (caiso_eia930_clock_repair, caiso_tac_shares_standard_time UNACCOUNTED).
- tests/unit/data/test_gas_offer_zonal_anchor_vintage.py fails (2 tests), plus other lanes' fast-tier failures.

HOUSEKEEPING (owner; a session cannot delete refs, HTTP 403)
- Deletable now: claude/nwppnext13-2019 … -2025, claude/nwppnext14, claude/nwppnext14-2019 … -2025,
  claude/nwppnext15-2019 … -2025, claude/nwppnext16d-2019 … -2025, claude/nwppnext16e-2019 … -2025, claude/nwppnext16,
  claude/nwpp-next14-arm-solve-2e8zh1, claude/charming-gates-b7riij, claude/nwppnext17, claude/nwppnext18 (after its PR merges).
- KEEP claude/nwppnext16c-2019 … -2025: they are the only copy of keeper #20's dispatch and unit_hourly parquets.
```
