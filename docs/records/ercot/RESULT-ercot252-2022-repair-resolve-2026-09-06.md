# RESULT — the ERCOT 2022 touchpoint re-solve under the two owner rulings: **CALIBRATED on 2022, 8/8 PASS**, with C3a and C3c inside their bands by 0.7 pt and 4 h (ercot-252)

> Scored against `docs/PRECOMMIT-ercot252-2022-repair-resolve-2026-09-06.md`, committed before
> the solve. Run `2026-09-06-run252-2022-touchpoint-repair` (bundle
> `results/calibration/ercot252_2022_touchpoint_repair`), registered, stamped to keeper
> `2026-09-05-ercot248-two-config-keeper`, replacing `2026-09-05-run250-2022-touchpoint-carveout`
> on the site (ONE 2022 run). **Rule 22: 2022 is validation tier — this is model-SELECTION
> evidence, never a certified out-of-sample skill number. Rule 30(c): ERCOT's determination is
> the train-tier verdict, CALIBRATED, and this result neither certifies nor decertifies it.**

## 1. C1 and C3a together, as the owner asked — every criterion, both runs

| criterion | tier | run250 (verbatim carve-out on 2022) | **run252 (+ R2 repair + R4 gates)** | band |
|---|---|---|---|---|
| **C1** CC_REGULAR | load-bearing | FAIL −10.39 TWh (121.69 vs 132.09), share −2.4 pp | **PASS −6.87 TWh** (125.22 vs 132.09), share −1.5 pp | ±8.00 TWh, ±3 pp |
| C1 other classes | | all PASS | all PASS (CC_CHP −0.18, CT_PEAKER −1.11, ST_GAS +2.76, COAL_PRB +4.22, COAL_LIGNITE +0.66, ST_CHP −0.14) | |
| C2 system volume | load-bearing | PASS (gas 166.47 / coal 75.54) | PASS (gas 170.72 vs 176.26 / coal 76.10 vs 71.22) | per-class via C1 |
| **C3a** mean LMP | load-bearing | PASS **+0.0 %** ($62.30 vs $62.30) | **PASS +9.3 %** ($68.08 vs $62.30) | ±10 % — **0.7 pt inside** |
| **C3b** price shape | load-bearing | FAIL NRMSE 0.220 | **PASS NRMSE 0.088** | ≤ 0.20 |
| **C3c** price tail (RT > $200) | supporting | CAVEAT 64 h vs 196 (0.33×) | **PASS 101 h vs 196 (0.52×)** | [0.5×, 2×] — **4 h inside** |
| C4 dispatch corr | supporting | PASS gas r 0.991 / coal 0.785 | PASS gas r 0.991 (NRMSE 0.076) / coal 0.775 | r ≥ 0.70 |
| C6 governance | protective | PASS | PASS (attested, deltas declared) | |
| C8 forced share | protective | PASS (CC 3.5 %, COAL 1.8 %, ST_GAS 27.0 %) | PASS (CC 3.1 %, COAL 1.6 %, ST_GAS 25.8 %) | < 30 % (peakers 15 %) |
| **determination** (rubric v3.6) | | **NOT-YET** on {C1, C3b}, C3c ledgered | **CALIBRATED** — scored 8, target-grade 8, caveats 0 | |

DA diagnostics (not gated): C3a +5.9 % vs DA ($64.31); tail 101 h vs 238 h DA.

## 2. What moved, and what the sidecars say moved it

| quantity | run250 | run252 | reading |
|---|---|---|---|
| wind / solar grid TWh (actual 107.38 / 23.67) | 112.23 / 25.24 | **108.28 / 24.33** | the armed ceilings took back 4.86 of the 6.42 TWh excess (76 %); residual excess **+1.56 TWh** |
| dump / slack | 0 / 0 | 0 / 0 | the excess still displaces thermal one-for-one |
| CC_REGULAR grid TWh | 121.73 | **125.26** | +3.53 TWh, 73 % of the renewable take-back at the measured 0.555 capture would be 2.70 — slightly above it |
| ORDC total-family requirement (mean MW) | 10,700 | **9,658** | the LR credit (2022 series, mean 1,042 MW) applied |
| reserve-supply cap | off (from_year 2023) | **on**, tier caps 10,389 / 15,710 MW mean | the cap net of the LR credit (ercot-212 `net_credits`) |
| hours the total family binds (dual > 0) | 199 | **811** | the cap re-scopes reserve to the measured RTOLCAP |
| ORDC shortfall | 310 GWh / 199 h | **1,490 GWh / 811 h** | |
| load-weighted mean LMP | $62.30 | **$68.08** | +9.3 % |
| hours > $200 | 64 | **101** | |
| solve wall-clock | — | 974 s (P0 295, P1 584) | 16 min, ~9 GB, swap untouched |

Plumbing (PRECOMMIT G-1 analogue, from the solve log): `ercot_wtx_curtailment_driver: 2022
West/Panhandle VRE ceiling active (depth wind=0.1354 solar=0.1614, unpooled families,
panhandle_owner=share)`; `gtc-limits 2022` read (constraints with no representable link in the
reduced topology ignored, as in every year); `energy+reserve co-opt … per-product req means
[359, 1821, 0, 3897]` (RRS 2,863 → 1,821 = the LR credit); `ERCOT reserve-supply cap ON: 2
headroom row(s), mean cap MW [10389, 15710]`. D-10 rows still read `forecast_uncurtailed` for
wind and solar — the bound is the reference-rate gross-up, now re-curtailed, not a measured
potential.

## 3. Scored against the PRECOMMIT's predictions, at full magnitude

| prediction (§3 of the PRECOMMIT) | outcome | verdict on the prediction |
|---|---|---|
| C1 CC_REGULAR back inside ±8.00 TWh | −6.87 TWh | **correct** |
| renewable excess 6.42 → +1 to +2.5 TWh | +1.56 TWh | **correct** |
| C3a falls to −8 … −14 %, likely outside the band | **+9.3 %**, inside | **WRONG on sign and on the verdict.** The 2023 screen measured the repair alone at −11.3 pts; here the R4 cap moved mean price the other way and the net is +9.3 pts — an implied cap effect of the order of +20 pts. |
| C3c tail up from 64 h | 101 h | correct |
| C3b direction unknown | 0.220 → 0.088 | resolved toward actual |
| C2/C4/C6/C8 hold | hold | correct |
| determination stays NOT-YET, C3a replacing C1 | **CALIBRATED** | **WRONG** — for the reason above |

**The two effects were NOT separately measured.** The PRECOMMIT's one-arm rule (§5: "no second
arm, one solve, one report") forbade a cap-only or repair-only control, so the decomposition
above is an inference from the 2023 screen, not a measurement on 2022. Both rulings preceded the
solve and neither was chosen on this result, so the CALIBRATED reading is not holdout selection —
but it is also not a claim that either mechanism is right on its own on 2022: C3a sits 0.7 pt
inside a ±10 % band with the cap pushing up and the repair pushing down, and that near-cancellation
is exactly the kind of number rule 22 says must never be quoted as skill.

## 4. What this does and does not change

* **ERCOT's determination: unchanged, CALIBRATED on 2023–2025** (rule 30(c)). The status page's
  holdout ladder now shows 2022 CALIBRATED beside it; the Run Explorer renders 2022 as an ordinary
  year column of the keeper's report (rule 30(a)); the tier caveat travels with it.
* **The keeper recipe: unchanged for 2023–2025.** The R2 predicate is byte-identical wherever an
  HSL parquet exists — every training year — and the R4 gates already read ≥ 2023 there. The two
  rulings change what a *no-HSL / pre-2023* year does, i.e. the validation ladder (2020, 2021 next)
  and, one day, 2019.
* **The from_year values are recipe state for the touchpoint, not a new recipe.** They are carried
  as replay-only overrides on the run's `meta.json` (`ercot_reserve_supply_cap_from_year = 2020`,
  `ercot_load_resource_reserve_from_year = 2020`); the keeper bundle's own `meta.json` still says
  2023. Whether the keeper recipe itself moves to 2020 is a follow-on owner call — it would change
  nothing in-sample and everything on the ladder, which is why it should be declared rather than
  inherited.
* **Nothing was tuned on 2022.** The predicate carries no value; each from_year is the measured
  series' first year; depths, reference rates and every other tunable are as the keeper left them.
* **R1 stays open.** With a measured 2022 HSL the bound stops being a gross-up at all, the D-10 rows
  read `measured_potential`, and the ceilings arm on the *original* predicate; the owner's "not now
  but eventually" is recorded in the marker.

## 5. Observations for the next session (recorded, not acted on)

1. **C3a +9.3 % with the cap binding 811 h** is the ORDC price function doing on 2022 what
   ercot-249 §3 said it never did — pricing the selected shortfall hours. That the mean lands
   6 % high while the tail is still half the actual (101 vs 196 h) says the adder is spread across
   too many mid-band hours and not steep enough in the true tail: the same "shape, not level"
   reading ercot-221/226 reached on 2023. The next C3c object on 2022 is the adder's *distribution*
   over the 811 hours, and it must be identified on 2023–2025 (rule 22 step 3), where the cap has
   been armed all along.
2. **CC_REGULAR still −6.87 TWh with +1.56 TWh of renewable excess** — the residual gap is
   ~5.3 TWh beyond what the excess explains at 0.555 capture. ST_GAS +2.76, COAL_PRB +4.22 and
   CT_PEAKER −1.11 are the counterparties; the 2022 conduct-side discount (no year-scoped SCED
   tables) is the standing explanation, and it is permanent.
3. **The D-4 off-window rows** (`chp_steam` unit-conduct; `reliability_floor × CT_PEAKER h14-21`,
   off-window share 0.19) fail on both run250 and run252 identically and are un-gated because every
   class is under its C8 budget — a 2022 conduct-window question, not this session's.

## 6. Provenance and governance

* Solved in-session (never on CI), one solve, on `8fbcd0e6` (the commit carrying the PRECOMMIT
  and the code). `--no-p1-basis-seed` passed; the seed is globally OFF on the replay path anyway.
* Registered via `dashboard_add_run.py` (DETERMINATION printed CALIBRATED at registration);
  `legitimacy_diagnostics.py` artifact written; attestation by `scripts/gen_ercot252_attestation.py`
  (DOF ledger n_entries 10 / n_residual 7, carried unchanged from the keeper; the two deltas are
  declared in the disclosures, and the generic touchpoint generator was not used because its
  recipe-identity check refuses a declared delta by design).
* `stamp_touchpoint_holdout.py` → `holdout.keeper`; `prune_iso_runs.py --force-uncite` removed
  run250 (its two citations, in `calibration-complete.json` and `keepers/ERCOT.json`, were first
  rewritten as deliberate historical mentions); `build_status.py --iso ERCOT` rebuilt.
* Gates: `audit_keepers --iso ERCOT` PASS; registry/payload parity OK; `build_status --check` in
  sync; `check_mechanism_matrix --base origin/main` OK (NEISO stamp drift + two anchor warnings
  pre-existing); `tests/scoring` the same 11 pre-existing failures as at clean HEAD.
* Matrix (rule 26): ERCOT shard evidence updated on `wtx_curtailment_driver`,
  `measured_interface_limits`, `vre_reference_rate_curtailment_grossup` and
  `ercot_multiproduct_as`; **no cell verdict changed** — a holdout-year result never adjudicates
  a cell.
* Locked test untouched. Companion records: `docs/FINDING-ercot252-2022-cc-routes-phase0-2026-09-06.md`
  (the phase-0 that preceded the rulings), `docs/FINDING-ercot251-nohsl-curtailment-gate-2026-09-06.md`,
  `docs/RESULT-ercot251-nohsl-ceiling-screen-2026-09-06.md`, `docs/calibration-log/ercot.md` (ercot-252).
