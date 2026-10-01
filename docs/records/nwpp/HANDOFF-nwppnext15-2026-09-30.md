# HANDOFF — NWPP-NEXT-15: NWPP calibration after keeper #19

> **SUPERSEDED IN PART (NWPP-NEXT-15, session 01VviGf2, 2026-10-01).** A NEXT-15 session ran from the OTHER lane's
> handoff. It solved the vintage-denominator arm (not promoted; it tied #19), built lever 1 (`coal_captive_marginal_fuel_price`)
> and lever 2 (`unit_outage_dispatched_bin_live_denominator`). The current prompt is `HANDOFF-nwppnext16-2026-10-01.md`.


```
SESSION NWPP-NEXT-15 — NWPP calibration, keeper #19 (2026-09-30-nwppnext14-clark-hr-bridger)
DATA PROFILE: nwpp
MODEL: Opus or Fable
CLAUDE.md is binding. Pay particular attention to rules 1, 5, 13, 14, 19, 21, 23, 24, 28, 29 and 31–36.
The parent never solves (rule 32(a)). Every backcast year gets its own shard (rule 36).

CHAIN DIRECTIONS (owner, standing; pass them on verbatim to every handoff you launch)
- First, when it is safe, archive the previous session: session_01VuR49nvpqa7pyyAQ2wWpet (NWPP-NEXT-14).
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

STATE ON MAIN
- Keeper #19: 2026-09-30-nwppnext14-clark-hr-bridger. Bundle: results/calibration/nwppnext14_span. Years 2019–2025.
  It is keeper #18's recipe + eia923_cc_family_heat_rates (Clark 2322's CC rows: eGRID 3.007 -> EIA-923 9.0–9.6
  MMBtu/MWh) + campd_unit_fuel_split composed with per-unit attribution (Jim Bridger's coal row on per-year vintage
  bins).
- Determination: NOT-YET on {dispatch_corr}, ONE record: C4 coal 2023 r 0.670 / NRMSE 0.317 (floor 0.70 / 0.30).
  Price is UNSCORED (rubric v3.8).
- Read first:
  - docs/records/nwpp/FINDING-nwppnext14-bridger-and-clark-phase0-2026-09-30.md (all of it, esp. §1)
  - docs/records/nwpp/RESULT-nwppnext14-clark-hr-bridger-vintage-2026-09-30.md (§2 regressions, §4 open)
  - docs/records/nwpp/PRECOMMIT-nwppnext14-clark-hr-bridger-vintage-2019-2025-2026-09-30.md (§3 G-DRIFT, §4 recipe, §5 stops)
  - docs/calibration-log/nwpp.md (latest entry), docs/codebase-site/data/mechanism-matrix/NWPP.js,
    docs/mechanism-testing-matrix.md §5.9

CLOSED — do NOT redo:
- Everything closed in HANDOFF-nwppnext7 through -nwppnext14.
- C4 coal 2023 inventory-conservation behaviour, in every public-identification form (Jim Bridger's Feb–May
  conservation). Pinning monthly burn or stock would be an outcome pin (rule 13).
- Offer-multiplier tuning on C1, C4 or CT (rules 1 and 13). No tuned coal passthrough / sigmoid for Bridger.
- The vintage-static per-unit tranche row (fixed at #19; FINDING-nwppnext14 §1.1: not the C4 cause).
- Clark 2322 heat rate (fixed at #19).
- The benchmark fossil reconcile belongs to the scorer lane. Do not touch the scorer or the bench.

OPEN LEVERS, highest value first
0. RULE-19 DEBT: campd_per_unit_vintage_denominator (parallel NEXT-14 lane, default off) and the armed
   campd_unit_fuel_split composition repair the same defect, the per-unit tranche artifact's head-vintage denominator.
   - Theirs is broader: it also repairs North Valmy 8224's must-run (40.7 -> 24.5 %).
   - Test it as the REPLACEMENT: arm vintage_denominator, disarm campd_unit_fuel_split (the selector refuses both),
     run 7 shards, and diff against keeper #19.
   - If promoted, DELETE the per-unit fuel-split path (rule 26).
   - Do NOT launch the other lane's docs/records/nwpp/nwppnext14/shards/* or PRECOMMIT-nwppnext14-vintage-denominator:
     they arm the DELETED cc_subfloor_eia923_heat_rates. Write a fresh PRECOMMIT on keeper #19's recipe.
   - Also read DESIGN-nwppnext14-captive-mine-marginal-fuel-2026-09-30.md (lever 1 below): in 2023 the captive mine
     was booked at $4.21/MMBtu while contract sources ran $2.42–2.62.
1. C4 coal 2023 (0.670) is Jim Bridger's OFFER (FINDING-nwppnext14 §1):
   - Bridger's delivered-cost offer ($38–51/MWh, F923 $3.42/MMBtu at 11.02 MMBtu/MWh) idles it Jun–Oct.
   - Its 2023 burn equals the soft take floor exactly (93.9 TBtu vs CEMS 100.4), and the LP spends the take in
     dear-gas Q1.
   - CEMS in Jun–Oct alone lifts fleet r to 0.821.
   - Owner card "Both" (2026-09-30) opened a ZERO-LP IDENTIFICATION lane: Bridger Coal Company is a captive mine
     (PacifiCorp 2/3, Idaho Power 1/3). Do public filings (PacifiCorp / Idaho Power IRPs, rate cases, FERC Form 1,
     WY/ID/UT PSC dockets) split its delivered cost into fixed and variable parts?
   - Arm an offer input ONLY if a measured, forward-reproducible, per-plant number exists (rule 13); otherwise record
     the negative result. Never a tuned passthrough (rule 1).
   - Check first whether an existing mechanism already carries a captive-mine / take-or-pay variable-cost share
     (coal_takeorpay_*, coal_*_passthrough*), and what the matrix says about each on NWPP.
2. Lever 3 (coal WEFOR relief). Owner card "New sub-gate, default off" (2026-09-30):
   - build a live-capacity denominator as a NEW default-off field, never changing miso-266's
     unit_outage_dispatched_bin_denominator (MISO's keeper arms it);
   - scope wefor_residual to screened coal (FINDING-nwppnext13 §1.3);
   - arm it with the WEFOR relief.
   Zero-LP census first, then a solve.
3. C1 CC_REGULAR under-dispatch 2021–23 grew at #19 (−2.15 / −4.06 / −1.84 TWh), while 2024–25 over-dispatch is still
   +6.27 / +7.47 (PASS). Zero-LP per-plant decomposition of where Clark's energy went.
4. SNV residual shed; internal-link over-flow; solve time (the 2019 leg took ~135 min of LP at #19).

PROCEDURE FOR ANY SOLVE — PRECOMMIT-nwppnext14 is the template
- G-DRIFT against keeper #19's pin 54edd9e324913a2c915199ca2af8e46abfed582b. If it is unreachable, use NEXT-14's PR
  merge commit on main as the base (as NEXT-14 did for #18).
- Replay source: NWPP-49 from 909cdd30bfdd8a398b10a4255b1340d0d9ef1943 into /tmp/n49, with the PRECOMMIT-nwppnext14 §4
  --set list (which now includes eia923_cc_family_heat_rates=true and campd_unit_fuel_split=true), plus
  hydro_backfill_year=null for 2019–2022.
- Shard prompts: never end the turn while the solve runs; poll in-turn with bounded wait loops until the push.
  Commit the bundle with the .gitignore negation lines (rule 34(a)), including dispatch/<Y>_P1.parquet. Give the 2019
  shard a 260-min budget.
- Hard stops:
  - sha256: campd_ct_heat_rates_NWPP.csv 29baa2f1…; campd-unit-outages-perunit-NWPP.csv ff5b0644…;
    thermal_tranches-perunit-fuelsplit-NWPP.csv cf912778…; eia923_cc_family_heat_rates_NWPP.csv cc9ac299…
  - run_config diff vs keeper #19's run_config_<Y>.json only in the arm's key(s);
  - P1 demand 279.581 / 292.940 / 289.358 / 298.960 / 280.261 / 290.216 / 302.532 TWh.
- PARENT GOTCHAS:
  - `git checkout <sha> -- <leg dir>` STAGES the leg; follow with `git rm -r --cached <leg dir>`. The leg family
    `results/calibration/nwppnext14_20[0-9][0-9]/` is already gitignored; add yours.
  - `gen_*_attestation.py` needs `git fetch --depth=1 origin 909cdd30…` first.
  - `legitimacy_diagnostics.py` needs `--json-out <bundle>/legitimacy_diagnostics.json`.
  - The clone may be shallow: `git fetch --deepen=400 origin` before a G-DRIFT diff.
  - The coal pile builders need data/clean: run scripts/data/curate_coal_{stocks,receipts}.py first
    (`pip install -e . --no-deps`).
  - The pre-push ruff gate uses `uv run ruff`; format with it (not pip's ruff) in a separate call BEFORE the push
    command.
- Compose with scripts/probes/_nwpp42_compose_span.py --skip-diagnostics (2023 leg first). Then:
  - legitimacy_diagnostics.py --json-out (exit 1 is normal);
  - an attestation wrapping scripts/gen_nwppnext14_attestation.py;
  - dashboard_add_run.py --no-prune;
  - calibration_verdict.py --run-id <id> --json, diffed per (criterion, year, key) record against keeper #19 (records
    live under criteria.<name>.records).
- prune_iso_runs.py needs the owner's explicit approval; get it on the promotion card.
- check_forecast_parity: any new keeper field must classify wired / declared, NWPP UNACCOUNTED 0.

HOUSEKEEPING (owner)
- Leftover shard branches to delete. A session cannot delete refs (HTTP 403):
  - claude/nwppnext14-{2019..2025}
  - claude/nwppnext13-{2019..2025}, and any older nwppnext* shard branches still present
- CI on main is red in checks owned by other lanes (FINDINGS on PR #6932): CAISO gate-(a) / FR-22 rows after R-CAISO-18,
  and ~25 fast-tier tests. None is NWPP's; do not widen an NWPP PR to fix them.
```
