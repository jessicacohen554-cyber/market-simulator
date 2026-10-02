# HANDOFF — NWPP-NEXT-21: solve the re-registered NWPP priced interface (7 shards on pin 86b73d6f)

```
SESSION NWPP-NEXT-21 — NWPP calibration: solve the priced interface (NWPP-56) on pin 86b73d6f, keeper #20
DATA PROFILE: nwpp
MODEL: Opus or Fable
CLAUDE.md is binding. Pay particular attention to rules 1, 5, 13, 14, 16, 19, 20, 21, 24, 25, 26, 28, 29 and 31–36.
The parent never solves (rule 32). Every backcast year gets its own shard (rule 36).

CHAIN DIRECTIONS (owner, standing; pass them on verbatim to every handoff you launch)
- First, when it is safe, archive the previous session: session_01GpoZnzVZBHaRnQ9TQH5Ztp (NWPP-NEXT-20).
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
If another live NWPP session works the same lever, put that on an owner card before spending LP. Re-check whether the
CAISO lane has ruled on card N4 / R-a (Path 66's 4,800 MW on both sides) — still unruled at NEXT-20.

STATE ON MAIN
- Keeper #20 unchanged: 2026-10-01-nwppnext16c-combined-vintage (bundle results/calibration/nwppnext16c_span, 2019–2025,
  pin 33014efc). NOT-YET on {dispatch_corr}, ONE record: C4 coal 2023 r 0.669 / NRMSE 0.313. Price UNSCORED.
- NEXT-20 (read first): docs/records/nwpp/FINDING-nwppnext20-seam-phase0-2026-10-02.md (§A gate, §B anchor, §C wheel,
  §D price-taker, §E residual, §F code). Probe: scripts/probes/_nwppnext20_seam_phase0.py <leg root>.
- Registry now (all default-off; arming = --set reference_price_interface=true):
  CAISO_COI (4,800 MW, NW+OR) and CAISO_NEVP (1,933 MW, SNV): MALIN anchor, CAISO NET load shape, hurdle 3.
  WECC_CAN (3,150 MW, NW): BCHA WEIM ELAP anchor HR 37.64/20.60/10.51, priced ONLY 2023–2025 (anchored_years_only).
  Each seam in its own external zone (IMPORT_SEAM_ZONES); no pooled bus. WECC_SW deleted (failed the SPP-51 gate).
  Served residual = keeper schedule − priced seams' measured legs (eia930.envelopes.nwpp_unpriced_residual_interchange):
  TWh −1.96 / 4.27 / −10.39 / −9.28 / −22.12 / −19.06 / −6.15 (2019–2025).

TASK (owner cards 2026-10-02, NEXT-20; the solve was deferred: "don't launch a shard")
1. PRECOMMIT before any shard: arm = keeper #20 recipe per year + reference_price_interface=true. Gates, declared ex ante:
   (a) structural STOP gate: per priced seam, the annual net flow has the measured SIGN in every priced year, and the
       hourly r of seam flow vs the measured leg is > 0 (measured: COI +7.0/+15.3/+12.1/+12.5/+1.1/+2.2/+3.0,
       NEVP −0.3/+3.1/+8.6/+8.6/+7.6/+9.1/+9.4, BC +9.5/+7.5/+2.8 TWh export-positive);
   (b) no load-bearing criterion (C1/C2/C3a/C3b/C4) flips PASS→FAIL vs keeper #20 without a stated root cause;
   (c) rule 20 forced energy and CT_PEAKER volume (NEXT-19 §3: 2–2.7× at a West-shaped price);
   (d) report hours of simultaneous COI import + BC export (the physical BC↔CA wheel through NW, FINDING §C).
   Expected risk, stated: at price-taker the priced seams export 20–62 TWh/yr vs 10–19 measured because keeper #20's NW
   price sits $2–35 below every seam; the LP will lift NWPP's price and thermal output. Read C1 gas/coal at full magnitude.
2. PIN: claude/nwppnext20-pin = 86b73d6f910d4b3a179f6158727b5e31b5f8c265 = 33014efc + four cherry-picks: NEXT-19
   wiring 24a3dce7 (from cd34b960, docs dropped), NEXT-20 code 89b134af, two ruff-format commits (AST-identical). G-DRIFT vs 33014efc: those
   hunks only — NEXT-19 §7 and NEXT-20 §F classify every one INERT for the keeper; the arm itself is the one LIVE
   change. Re-verify with `git diff 33014efc 86b73d6f -- src scripts` before launching. 741 interface/NWPP tests pass
   at the pin.
3. 7 shards, one per year, source_revision = the full pin SHA. Copy NEXT-19's shard template
   (docs/records/nwpp/nwppnext19/shards/shard_g_<Y>.txt): replay each year from ITS OWN keeper leg
   (`replay_keeper.py /tmp/leg/results/calibration/nwppnext16c_<Y> --set reference_price_interface=true`). Legs by full SHA:
   2019 1e4bd215c635aa876ab3ad75f8fb4657f4e47cec · 2020 aa60aa43a9e27da9c7e14a8c7bcf09db1ad4dcc6 ·
   2021 3b38fefe402b5168c1557459a28978eb9274ed92 · 2022 11bb59fbf0d6a4b8716362f0e8c2f1899a601d11 ·
   2023 a54c7b97a9c588564bab90746f2dbbc44fd56838 · 2024 91f0bc2928bd348ac48f9d13c6fce7b3c8b460e8 ·
   2025 1a41ba5122095ef749302ddf2cb9d67f4fe89dfe
   (`git fetch --depth=1 origin <sha> && git archive <sha> results/calibration/nwppnext16c_<Y> | tar -x -C <dir>`).
   Each shard's STEP-1 hard stop also prints: the three NWPP_ext_* zones in the topology, the band count
   (2×8×3 = 48 rows in 2023–25, 32 in 2019–22), and the served residual's annual TWh (must equal the table above).
4. Compose, score, register (probe) per the procedure below; diff calibration_verdict per (criterion, year, key)
   against keeper #20; one owner card on promotion + prune. Update the matrix cells reference_price_interface /
   priced_interchange in docs/codebase-site/data/mechanism-matrix/NWPP.js with the verdict.

CLOSED — do NOT redo
- Everything closed in HANDOFF-nwppnext7 through -nwppnext20.
- NEXT-20: WECC_SW as a priced seam (fails SPP-51 P0-b: NEVP<->LDWP 0.28/0.33/0.31, PACE<->WACM 0.27–0.40); the pooled
  NWPP_external bus; the Mid-C Peak anchor; a gas-scaled BC price for 2019–2022.
- NEXT-19: gas_daily_shape for NWPP (R). NEXT-18: hydro_budget_period_by_instrument. NEXT-17: Bridger seasonal offer.
  NEXT-16: captive-mine price, live-capacity screened-coal WEFOR, offer-multiplier tuning on C1/C4/CT.

PROCEDURE FOR ANY SOLVE (PARENT GOTCHAS, NEXT-15/16/19)
- Shard setup: `pip install --ignore-installed pyyaml==6.0.3 && pip install -r requirements.txt && pip install -e . --no-deps`;
  STEP-1 hard stop prints highspy/pandas/pyarrow/pydantic = 1.14.0 / 3.0.3 / 24.0.0 / 2.13.4.
- Tell every shard: do NOT run legitimacy_diagnostics or any scorer; push without asking.
- Hard-stop demand (the keeper's, unchanged by the arm): 279.581 / 292.940 / 289.358 / 298.960 / 280.261 / 290.216 /
  302.532 TWh — NOTE the served residual replaces the full schedule, so the demand the LP serves moves by the priced
  legs; state which demand the hard stop checks (EIA-930 native load, not load + schedule).
- Stage legs: `git checkout <sha> -- <leg dir>` then `git rm -r -q --cached <leg dir>`; gitignore the family.
- Compose: scripts/probes/_nwpp42_compose_span.py --skip-diagnostics (2023 leg first); restore shared inputs with
  run_calibration_full.py --restore-shared-inputs if needed; legitimacy_diagnostics.py --bundle B --iso NWPP --years
  2019 … 2025 --json-out B/legitimacy_diagnostics.json; attestation: wrap scripts/gen_nwppnext16_attestation.py arm "c"
  and add the arm's keys to base._ARMED/_SOURCES; dashboard_add_run.py --no-prune; calibration_verdict.py --run-id <id>
  --json for BOTH runs, diffed per (criterion, year, key) record.
- Promotion + prune on ONE owner card; rule 35 (promote_keeper.py; audit_keepers --iso NWPP; prune_iso_runs.py --iso NWPP;
  re-stamp §5.9 and the matrix keeper/gates; check_forecast_parity NWPP UNACCOUNTED 0). Rule 15: promote_keeper.py
  preflight derives unit_marginal_<Y>.parquet; keeper #20 lacks it (do not backfill outside a promotion).
- A rejected probe: remove its registry sidecar + runs/<id>.js, revert bench parts; never commit the span bundle.
- Never `ln -sf` onto a system path (NEXT-20 clobbered /dev/null once and restored it with mknod).

KNOWN ISSUES on main (not NWPP's; report, do not fix)
- Fast lane under the nwpp sparse profile: ~211 failures, other ISOs' data absent; two pre-existing code failures on main
  (tests/iso/spp/test_spp_mmu_offer_unavailability.py::TestAvailabilitySeam::test_bands_after_overlays,
  tests/unit/data/test_local_capacity.py::TestLocalCapacityT5RhsBuilder::test_rhs_clips_to_zero_below_the_import_cap).
- FR-22 parity red for CAISO; tests/unit/data/test_gas_offer_zonal_anchor_vintage.py (2 tests).

HOUSEKEEPING (owner; a session cannot delete refs, HTTP 403)
- Keep claude/nwppnext20-pin until NEXT-21's legs are on main (it is the solve pin). Deletable after NEXT-20's PR
  merges: claude/nwppnext20.
- Every earlier NWPP branch is already gone from origin.
```
