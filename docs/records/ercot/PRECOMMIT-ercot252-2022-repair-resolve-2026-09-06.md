# PRECOMMIT — the ERCOT 2022 touchpoint RE-SOLVE under two owner rulings: the admitted provenance-predicate repair + both reserve from_year gates 2023 → 2020 (ercot-252)

> **Committed BEFORE the solve.** Every prediction, reporting duty and stop rule below is
> fixed at this commit; the result that arrives after it may not move any of them. This is
> **not a rule-29 screen** — the owner has already ruled both arms in (§1), so no gate here
> promotes or kills anything. What this document fixes is (a) exactly what changes, (b) what
> is predicted, so the report cannot be written to fit the result, and (c) what the result may
> and may not be quoted as under rule 22 `[R-HOLDOUT]`. **2022 is validation tier and
> iterable; ERCOT holds a `complete` marker; the locked test (2019 / H1-2026) is not touched.**

## 1. The two owner rulings, verbatim (2026-09-06, clickable decision card, session ercot-252)

| decision | ruling | effect on this solve |
|---|---|---|
| R1 — 2022 HSL archive | *"I can't do it now but eventually"* | R1 stays **OPEN**, not closed. When it lands, the bound becomes `measured_potential`, the repair below is moot on 2022 by construction, and the touchpoint is re-run on the measured bound. |
| R2 — provenance-predicate repair | *"Admit as a correctness fix; re-solve 2022"* | The ercot-251 predicate (`_renewable_bound_is_delivered_pinned`) is **re-applied, no longer screen-only**: both curtailment gates skip their ceiling only when the bound is `delivered_pinned`, never merely because no HSL parquet exists. Byte-identical in every training year (all `measured_potential`), live on no-HSL years. |
| R4 — `ercot_reserve_supply_cap_from_year` 2023 → 2020 | *"Arm both gates (cap + LR credit) and re-solve 2022"* | Both `ercot_reserve_supply_cap_from_year` and `ercot_load_resource_reserve_from_year` move **2023 → 2020** on the 2022 touchpoint, as one paired recipe change (the ercot-212 `net_credits` construction nets the LR series off the cap rows). The LR series for 2022 is the one built by ercot-252 (`ercot_2022_as_up_mw.parquet`, measured 60-Day awards). |

Everything else in the recipe is the carve-out config replayed verbatim (`ercot236_k33_clip`
via the committed `ercot250_2022_touchpoint_carveout` bundle). **No parameter is identified
on 2022**: the predicate carries zero degrees of freedom, and a `from_year` is a
data-availability gate whose new value is the first year the measured series exists (RTOLCAP
2020; LR awards 2018), not a fitted number.

## 2. The command (fixed here)

```
python3 scripts/run_calibration_full.py \
  --replay-bundle results/calibration/ercot250_2022_touchpoint_carveout \
  --year 2022 --holdout-authorized --no-p1-basis-seed \
  --ercot-reserve-supply-cap-from-year 2020 \
  --ercot-load-resource-reserve-from-year 2020 \
  --out-dir results/calibration/ercot252_2022_touchpoint_repair \
  --note "ercot-252: 2022 touchpoint on the carve-out recipe + owner-admitted provenance-predicate repair (R2) + reserve from_year gates 2023->2020 (R4, paired)"
```

* The two `--…-from-year` flags are new **REPLAY-ONLY overrides** on `run_replay_bundle`
  (`None` keeps the bundle's value, so every existing replay is byte-identical; guarded by
  `tests/regression/test_recipe_replay_gates.py`, 10 pass).
* `--no-p1-basis-seed` is passed for the record; on the replay path the seed is already
  globally OFF (its own help text), so the one LIVE G-DRIFT hunk (`bf37a0dc`) is inert here.
* Pre-solve plumbing verified at this commit: `_renewable_bound_is_delivered_pinned("ERCOT",
  2022) → False` (the ceilings arm) and `False` for 2023 (training years unchanged);
  `data/clean/gtc-limits/ERCOT/gtc-limits_2022.parquet` re-curated from the committed NP6-86
  raws at **13,321 rows across 15 GTCs** (identical to the 2026-09-05 completeness pass);
  `ercot_2022_as_up_mw.parquet` present (mean 1,042 MW); `ercot_2022_ordc_reserves_hourly.parquet`
  present (RTOLCAP mean 11,432 MW).

## 3. Predictions, fixed before the solve

Reference: the folded touchpoint `2026-09-05-run250-2022-touchpoint-carveout` (C1 FAIL
CC_REGULAR −10.39 TWh; C2 PASS; C3a +0.0 %; C3b 0.220 FAIL; C3c 64 h vs 196 CAVEAT; C4/C6/C8
PASS; renewable +6.42 TWh over actual; ORDC shortfall 310 GWh over 199 h).

| quantity | prediction | basis |
|---|---|---|
| **C1 CC_REGULAR** | back **inside the ±8.00 TWh band** | ercot-251 G-4: on 2023 the same repair put CC_REGULAR within 0.52 TWh of the measured-HSL keeper; ercot-251 §3.1 sized the 2022 ceiling at 5.46 TWh of the 6.42 excess |
| renewable excess | 6.42 → roughly +1 to +2.5 TWh | ercot-251 G-3 recovered 80.5 % of the injection on 2023 |
| **C3a mean LMP** | falls from +0.0 % to roughly **−8 to −14 %**, i.e. **likely OUTSIDE the ±10 % band** | ercot-251 G-5: −11.3 pts on 2023 from the same construction; the cap (R4) pushes the other way (§2.3 of the FINDING: 4,149 cap-binding hours), magnitude unknown — this is the one genuinely open number |
| **C3c tail** | **up** from 64 h | the cap re-scopes reserve supply to the measured RTOLCAP in 4,149 h; the LR credit removes ≤149 GWh of the 310 GWh shortfall (opposing, smaller) |
| C3b NRMSE | direction unknown (0.220 now) | both the renewable repair (softer troughs) and the cap (sharper tail) move shape |
| C2, C4, C6, C8 | hold | not touched by either change |

**The determination is predicted to stay NOT-YET** — with C3a plausibly replacing C1 as a
failing load-bearing criterion. That is the trade the owner admitted with open eyes (RESULT
ercot-251 §4/§6); it is recorded here so the result cannot be presented as a surprise.

## 4. Reporting duties (rule 22, rule 30, the owner's "report C1 AND C3a together")

1. **C1 and C3a are reported together, never C1 alone**, beside the run250 numbers, criterion
   by criterion — one table, both runs.
2. The run registers (rule 15), is stamped to the keeper (rule 30(a),
   `stamp_touchpoint_holdout.py --keeper-id 2026-09-05-ercot248-two-config-keeper`), and
   **replaces** run250 on the site (owner ruling 2026-09-06: ONE 2022 run) via
   `prune_iso_runs.py`; `build_status.py --iso ERCOT` rebuilt. Run250's numbers survive in
   `FINDING-ercot249-250` §1 / Addendum 1 and in git history (rule 15).
3. Rule 30(c): **ERCOT stays CALIBRATED** on 2023–2025 whatever 2022 reads. The 2022 result is
   model-SELECTION evidence and is never quoted as a certified out-of-sample skill number.
4. The `complete` marker's `config_2022_designation` gains a dated addendum recording both
   rulings and the new run id; the prior text is preserved verbatim.
5. Matrix (rule 26): the ERCOT shard's `wtx_curtailment_driver`, `measured_interface_limits`
   (the GTC leg), `vre_reference_rate_curtailment_grossup` (no longer dormant on ERCOT) and
   `ercot_multiproduct_as` (the two from_year legs) cells get evidence citations; no cell
   verdict changes from a holdout-year result.

## 5. Stop rules — what the result does NOT license

* **No second arm.** One solve, one report. If C3a fails, the depths
  (`ercot_wtx_curtail_depth_wind/solar`) stay FROZEN (rule 23), the reference curtailment
  rates stay the loader's own, the from_year values are not re-chosen, and nothing is swept —
  a value picked to make a 2022 criterion pass is holdout selection, refused.
* **Nothing re-enters training.** Any parameter this result implicates goes back to the
  2023–2025 loop (rule 22 step 3); it is never tuned here.
* **The keeper does not change.** This is the touchpoint, not a promotion.

## 6. Reversal checklist

None owed: the code change is admitted (not screen-only), the bundle is registered (not a
screen bundle), and no file is moved aside. The 8 GB swapfile is container-local.
