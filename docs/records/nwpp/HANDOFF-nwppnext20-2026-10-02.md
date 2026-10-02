# HANDOFF — NWPP-NEXT-20: fix the two seam objects, then solve the NWPP priced interface (keeper #20)

```
SESSION NWPP-NEXT-20 — NWPP calibration: priced interface (NWPP-56), CAISO seam net-load shape + WECC_CAN anchor, keeper #20
DATA PROFILE: nwpp
MODEL: Opus or Fable
CLAUDE.md is binding. Pay particular attention to rules 1, 5, 13, 14, 17, 19, 21, 23, 24, 25, 26, 28, 29 and 31–36.
The parent never solves (rule 32(a)). Every backcast year gets its own shard (rule 36).

CHAIN DIRECTIONS (owner, standing; pass them on verbatim to every handoff you launch)
- First, when it is safe, archive the previous session: session_012zjpfwNZTvSPZnPk5UPi7w (NWPP-NEXT-19).
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
If another live NWPP session works the same lever, put that on an owner card before spending LP. Also check whether a
CAISO lane has ruled on card N4 (CAISO's WECC_import node represents this footprint; docs/mechanism-testing-matrix.md
NWPP-56 entry) — rule 25.

STATE ON MAIN
- Keeper #20 unchanged: 2026-10-01-nwppnext16c-combined-vintage (bundle results/calibration/nwppnext16c_span, 2019–2025,
  pin 33014efc). NOT-YET on {dispatch_corr}, ONE record: C4 coal 2023 r 0.669 / NRMSE 0.313. Price UNSCORED.
- NEXT-19 (read first):
  - docs/records/nwpp/FINDING-nwppnext19-price-census-phase0-2026-10-02.md (§1–§4 census; §6 the seam checks; §7 the wiring)
  - docs/records/nwpp/RESULT-nwppnext19-gas-daily-shape-2026-10-02.md (arm G, R)
  - scripts/probes/_nwppnext19_price_census_phase0.py (every table; §6 = seam_shape())
- Wiring on main (default-off): IMPORT_ZONE["NWPP"]="NWPP_external", IMPORT_EFORD 0.0,
  IMPORT_NODE_LINKS["NWPP"] = seam_derived_border_links("NWPP") (sum of seam limits per border zone),
  require_priced_interchange_rows (an empty priced build is refused). INTERFACE_NEIGHBORS["NWPP"] (spec.py, the NWPP-20
  block): CAISO@MALIN 6,733 MW, WECC_SW@PALOVRDE (proxy NEVP) 6,049 MW, WECC_CAN@Mid-C Peak (proxy BPAT) 3,475 MW.
  Arming = --set reference_price_interface=true (it forces priced interchange; the measured schedule is dropped, rule 19).

TASK (owner card 2026-10-02: "Fix both, then solve")
1. Read SPP-51 first (the identical seam form was killed at rule-29 phase 0 on SPP's measured record; copy the method, do
   not inherit the verdict, rule 28(d)).
2. CAISO seam: set load_shape_kind="net" (demand − solar − wind of CISO). Categorical, physical (CAISO's price is set by its
   net load; the CAISO Desert-SW corridor already uses "net"). NEXT-19 §6a: within-day r vs CAISO RT gross 0.37/0.24/0.08,
   net 0.56/0.58/0.62 (2023/24/25). The hr_by_year anchors are annual means and do not change with the shape (mean 1).
3. WECC_CAN anchor: the Mid-C PEAK daily index is peak-only (declared upward-biased); the seam sits $12–38 above measured
   BPAT in 2023–25 and at $170 in 2022 (HR 13.9–37.1, flat 27.25 for 2019–2022). Find an admissible all-hours anchor
   (rule 14; NOT the footprint's own WEIM price — that is the outcome, rule 13, and not forward-reproducible). If none
   exists, keep the Canada leg on its MEASURED schedule (split the schedule by counterparty from the per-DIBA files,
   NWPP-11) and price only CAISO + WECC_SW — a rule-19 design: each counterparty either priced or scheduled, never both.
   Owner card on the design before code.
4. Zero LP before shards: with the fixed seams, compute the price-taker flows (seam price vs keeper #20's zonal price) and
   the implied annual net interchange per seam vs measured (−6.6 / −3.1 / +5.4 TWh 2023/24/25, export-positive); state
   the 2019–2022 HR fallback values. Card before solving; 7 shards (one per year), G-DRIFT vs pin 33014efc (or pin a
   docs-only commit over a code commit that carries the fix, and classify every hunk).
5. Watch CT_PEAKER (NEXT-19 §3: a West-shaped price lifts CT 2–2.7× at price-taker), rule 20 forced energy, C4 gas.

CLOSED — do NOT redo
- Everything closed in HANDOFF-nwppnext7 through -nwppnext19.
- NEXT-19: gas_daily_shape for NWPP (R: HH is not the NW gas signal; C4 gas regresses every year, between days).
  A daily NW-hub gas series does not exist publicly (Sumas weekly; Malin/Stanfield/Opal none) — re-test only with one.
- NEXT-18: hydro_budget_period_by_instrument (closed). NEXT-17: Bridger seasonal offer. NEXT-16: captive-mine price,
  live-capacity screened-coal WEFOR, offer-multiplier tuning on C1/C4/CT.

PROCEDURE FOR ANY SOLVE (PARENT GOTCHAS, NEXT-15/16/19)
- Keeper #20 leg branches claude/nwppnext16c-* are GONE from origin; the commits still resolve by full SHA:
  2019 1e4bd215c635aa876ab3ad75f8fb4657f4e47cec · 2020 aa60aa43a9e27da9c7e14a8c7bcf09db1ad4dcc6 ·
  2021 3b38fefe402b5168c1557459a28978eb9274ed92 · 2022 11bb59fbf0d6a4b8716362f0e8c2f1899a601d11 ·
  2023 a54c7b97a9c588564bab90746f2dbbc44fd56838 · 2024 91f0bc2928bd348ac48f9d13c6fce7b3c8b460e8 ·
  2025 1a41ba5122095ef749302ddf2cb9d67f4fe89dfe
  (`git fetch --depth=1 origin <sha> && git archive <sha> results/calibration/nwppnext16c_<Y> | tar -x -C <dir>`).
- NEXT-19's shard template (docs/records/nwpp/nwppnext19/shards/shard_g_<Y>.txt on commit df78648b) replays each year
  from ITS OWN keeper leg (`replay_keeper.py /tmp/leg/results/calibration/nwppnext16c_<Y> --set ...`), which carries the
  exact per-year recipe (hydro_backfill_year differs by year). It worked first time for all 7 years (2019 ~3.5 h).
- Shard setup: `pip install --ignore-installed pyyaml==6.0.3 && pip install -r requirements.txt && pip install -e . --no-deps`;
  STEP-1 hard stop prints highspy/pandas/pyarrow/pydantic = 1.14.0 / 3.0.3 / 24.0.0 / 2.13.4.
- Tell every shard: do NOT run legitimacy_diagnostics or any scorer; push without asking.
- Hard-stop demand: 279.581 / 292.940 / 289.358 / 298.960 / 280.261 / 290.216 / 302.532 TWh.
- Stage legs: `git checkout <sha> -- <leg dir>` then `git rm -r -q --cached <leg dir>`; gitignore the family.
- Compose: scripts/probes/_nwpp42_compose_span.py --skip-diagnostics (2023 leg first); restore shared inputs with
  run_calibration_full.py --restore-shared-inputs if needed; legitimacy_diagnostics.py --bundle B --iso NWPP --years
  2019 … 2025 --json-out B/legitimacy_diagnostics.json; `git fetch --depth=1 origin 909cdd30bfdd8a398b10a4255b1340d0d9ef1943`;
  attestation: wrap scripts/gen_nwppnext16_attestation.py arm "c" and add the arm's keys to base._ARMED/_SOURCES
  (NEXT-19 did this in a throwaway gen script); dashboard_add_run.py --no-prune; calibration_verdict.py --run-id <id>
  --json for BOTH runs, diffed per (criterion, year, key) record (C4: field `model`, e.g. "r=0.677 nrmse=0.307").
- Promotion + prune on ONE owner card; rule 35 (promote_keeper.py; audit_keepers --iso NWPP; prune_iso_runs.py --iso NWPP;
  re-stamp §5.9 and the matrix keeper/gates; check_forecast_parity NWPP UNACCOUNTED 0). Rule 15: promote_keeper.py
  preflight derives unit_marginal_<Y>.parquet; keeper #20 lacks it (do not backfill outside a promotion).
- A rejected probe: remove its registry sidecar + runs/<id>.js, revert bench parts; never commit the span bundle.

KNOWN ISSUES on main (not NWPP's; report, do not fix)
- Fast lane under the nwpp sparse profile: ~211 failures, other ISOs' data absent; two pre-existing code failures on main
  (tests/iso/spp/test_spp_mmu_offer_unavailability.py::TestAvailabilitySeam::test_bands_after_overlays,
  tests/unit/data/test_local_capacity.py::TestLocalCapacityT5RhsBuilder::test_rhs_clips_to_zero_below_the_import_cap).
- FR-22 parity red for CAISO; tests/unit/data/test_gas_offer_zonal_anchor_vintage.py (2 tests).

HOUSEKEEPING (owner; a session cannot delete refs, HTTP 403)
- Deletable now: claude/nwppnext16, claude/nwppnext16d-2019, claude/nwppnext17, claude/nwppnext18,
  claude/nwppnext19g-2019 … -2025 (arm G rejected; SHAs in the RESULT), claude/nwppnext19-pin,
  claude/nwppnext19 (after its PR merges).
- NEXT-18 session_01XTvTt5gqyhLhWyi2bDzAPa: archive (NEXT-19's archive call was refused by the permission classifier).
```
