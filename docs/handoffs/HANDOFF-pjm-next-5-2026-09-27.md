# HANDOFF — PJM-NEXT-5

```
SESSION PJM-NEXT-5 — PJM calibration: close the remaining rubric failures on keeper 2026-09-26-pjm-next-4-midcurve2019
DATA PROFILE: pjm
Model: Opus/Fable only (rule 27 — may write src/market_sim).

READ FIRST: CLAUDE.md (rules 1, 13, 14, 19, 21, 23, 25, 28, 29(b), 31–36); docs/RESULT-pjm-next-4-2026-09-26.md;
docs/PRECOMMIT-pjm-next-4-card1-midcurve-2019-2026-09-26.md; docs/RESULT-pjm-next-3-2026-09-26.md;
docs/FINDING-pjm-next-3-phase0-cards-1-3-4-2026-09-26.md; the PJM lever queue in docs/mechanism-testing-matrix.md §5.3
and docs/codebase-site/data/mechanism-matrix/PJM.js. Never re-test an R/I/G cell without new evidence. In particular,
coal_passthrough_sigmoids re-centring (joint form) is R, committed_band_measured_basis is R, AP South is I, and
Dominion sub-zonal congestion is closed (pjm-137).
Keeper bundle: results/calibration/pjmnext4_c1_span (2019–2025).

STATE: PJM NOT-YET.
- Training span 2023–2025 fails C1 only: CC_REGULAR 2024 −9.33 TWh (band 8).
- Out of span (reported, never gating):
  - COAL_BIT 2019/2020/2021/2022: +25.84 / +10.5 / +20.7 / +8.1 TWh.
  - CC_REGULAR 2019: −8.54 FAIL.
  - C3a 2020 FAIL; C3b 2020 FAIL.
  - C3a 2019 now PASSES (+7.6 %).

WHAT PJM-NEXT-4 ESTABLISHED:
- The pre-2023 coal over-run is NOT a mid-curve-table defect. 2020–2022 over-run on their own measured tables, and
  giving 2019 its own table made it worse: the coal econ rung went $26.68 → $25.05 against CC econ $27.14.
- In 2019 the mid-curve floor binds on 63 % of COAL_BIT econ hours but only 5 % of CC_REGULAR econ hours. So the
  model's CC econ bid already sits ABOVE PJM's own measured CC_LIKE offers almost all year. The merit-order inversion
  may be on the GAS side (CC too expensive), not the coal side.

CARDS, in order. Each gets its own PRECOMMIT pushed before any solve. Zero-LP phase 0 first. Never tune
offer_curve_by_group multipliers.
 (1) CC econ cost vs PJM's measured CC offers, 2019–2022 and 2024.
     - Fleet-only rebuild via replay_keeper.run_year_kwargs (template: scripts/probes/pjm_h20_cardc_phase0.py;
       method in docs/PRECOMMIT-pjm-next-4-card1-midcurve-2019-2026-09-26.md §3).
     - Decompose the cap-weighted CC_REGULAR econ bid (gas × HR + VOM + RGGI + startup amortization) against the
       measured CC_LIKE mid-curve target at the same share.
     - Where is the model CC above PJM's own offers, by zone, and by how much? Name the operand (delivered gas basis,
       heat rate, VOM, RGGI) that carries the excess.
     - pjm-h21 found the LEVEL form erases plant gas basis — do not re-arm it as-is.
     - Only a measured, rule-14 operand correction proceeds to a solve.
 (2) If card 1 finds no admissible operand: phase 0 the coal side's remaining unadjudicated levers from the queue
     (coal_offer_net_revenue_margin is U; coal_fuel_inventory is U), each against its own matrix record.
 (3) OWNER RULINGS (2026-09-27, given in PJM-NEXT-4 — act on them):
     - (a) F2 full outage-extract re-derive: YES. The COAL-SUB deriver fix is on main (rule 23: source/deriver
       change). Re-derive the PJM CAMPD outage extract into a new companion file (never overwrite the committed
       extract in place). Prove which rows move with a zero-LP census by year and class; the 2019 capacity-hour
       drift vs the keeper was CC_REGULAR +20 / ST_GAS −26 TWh. Pre-register it, then solve it as its own card.
     - (b) retiree_cems_cap: PHASE 0 ONLY, then bring a delete-or-repair recommendation to the owner. Cover what it
       touches on the keeper, its admissibility under rules 13/24/26, and what moves if deleted. No model change
       until the owner rules.
     - (c) CC_REGULAR 2024 gas: do card (1)'s gas-side phase 0 first. No licensed hub index is being sourced now.

EXECUTION: the parent never solves (rule 32).
- Shards: one per year 2019–2025 (rule 36), pinned 40-char SHA, created with permission_mode auto, clone_depth 1,
  blob_limit_kb 2048.
- Shard prompts MUST say: when a long job runs in the background, WAIT in the foreground with an until-loop; never
  end the turn while waiting. In PJM-NEXT-4 one shard stalled idle 41 min this way and had to be relaunched.
- Before the solve, shards run `pip install -q -e . pytest`, `hydrate_data.py --profile pjm`,
  `fetch_pjm_da_virtuals.py --years <y>` and a parallel `regenerate_clean.py` (xargs -P4). ercot-wtx-congestion and
  emissions-unit-annual fail harmlessly for PJM.
- Push the full bundle via a .gitignore negation plus a plain git add (rule 34).
- Control = the keeper's committed bundle plus a G-DRIFT audit (rule 29(b)).
- Replay: `replay_keeper.py results/calibration/pjmnext4_c1_span --years <y> [--set <flag>=true]`.
- Compose with a copy of scripts/probes/_pjmnext4_compose_span.py.
- Rebuild the benchmark with `run_calibration_full.py --rebuild-benchmark DIR --iso PJM --year 2019 ... 2025`.
- Attest with scripts/gen_pjmnext4_attestation.py as the template; register with `dashboard_add_run.py --no-prune`;
  score with `calibration_verdict.py --run-id` against the keeper.
- Update the PJM matrix shard, the calibration log and a RESULT doc.
- Archive shards once the bytes are fetched (rule 33); do not ask permission to launch or archive shards.
- Ask the promotion question (rule 31). On promotion follow rule 35: prune, re-key calibration-complete.json +
  program-status gate (a), build_status --iso PJM, audit_keepers, check_promotion_completeness.py.
- Edit governance JSON line-by-line; a full json.dumps rewrite reformats calibration-complete.json.
- Report leftover shard branches for the owner to clear.
```
