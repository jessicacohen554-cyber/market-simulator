# PRECOMMIT — the ERCOT 2021 validation rung, on the keeper's carve-out recipe with the PUBLISHED pre-Uri ORDC order parameters (ercot-253)

> **Committed BEFORE the solve.** Every delta, prediction, reporting duty and stop
> rule below is fixed at this commit; the result that arrives after it may not move
> any of them. **2021 is validation tier and iterable; ERCOT holds a `complete`
> marker; the locked test (2019 / H1-2026) is not touched and stays frozen for
> every ISO.** Nothing here is a rule-29 screen — the owner has ruled every delta
> in (§1), so no gate below promotes or kills anything.

## 1. The owner rulings this rung executes (2026-09-06, clickable decision cards, session ercot-253)

| id | ruling | effect |
|---|---|---|
| **D1** | *"Declare in the keeper recipe"* — `ercot_reserve_supply_cap_from_year` and `ercot_load_resource_reserve_from_year` move 2023 → 2020 in the ERCOT keeper's OWN recipe, not as per-rung overrides. | Applied to `results/calibration/ercot248_two_config_keeper/{meta,run_config,run_config_carveout_2023,run_config_forward_2024_2025}.json`. **NO re-solve, and this is a proof rather than an assertion:** both gates are simple monotone `year >= from_year` comparisons (`results/scarcity.py:2333`, `model/reserves/spec.py:1355`, `results/scarcity.py:2621`), and every training year is ≥ 2023 ≥ 2020, so the arming is identical in 2023/2024/2025 by construction. |
| **D2** | *"2021 only, decide on 2020 after"* | One rung this session. 2020 is not solved, not scored, not registered. |
| **D3** | *"Vintage it: $9,000 / 2,000 MW for 2021"* | ERCOT's ORDC price-formation order parameters become **year-vintaged published values**: `ordc_voll` (the system-wide offer cap, HCAP) and `ordc_mcl_mw` (minimum contingency level X) read $9,000 / 2,000 MW through 2021 and $5,000 / 3,000 MW from 2022-01-01 (16 TAC 25.509 / PUCT Project 52631; OBDRR038 / PUCT Project 52373). |
| **D4** | *"Neutralize the surface in the field-arming pins"* | The capx-D79 solve-surface neutralization (`config_identity_only`) becomes the default for cache-key pins, so a registry repair fails the surface's OWN pins and nothing else. Test-infrastructure only; no solve-path behaviour. |

## 2. The recipe, and every delta from the 2022 rung

The rung replays **`results/calibration/ercot252_2022_touchpoint_repair`** — the
CARVE-OUT config (`ercot236_k33_clip`) carrying the ercot-251 R2 provenance-predicate
repair and the R4 reserve gates. **The config is named HERE, before the solve.** The
2022 designation was settled after both arms were seen and the record says so; this
one cannot be, and no second config will be solved for 2021.

```
python3 scripts/run_calibration_full.py \
  --replay-bundle results/calibration/ercot252_2022_touchpoint_repair \
  --year 2021 --holdout-authorized --no-p1-basis-seed \
  --out-dir results/calibration/ercot253_2021_touchpoint \
  --note "ercot-253: 2021 validation rung on the carve-out recipe; published pre-Uri ORDC order parameters (HCAP 9000 / MCL 2000, owner ruling D3); from_year gates declared in the keeper recipe (D1)"
```

No `--ercot-*-from-year` flags: the replayed bundle already records 2020 for both,
and after D1 so does the keeper.

### 2a. Solve-affecting deltas (all four are measured or published inputs; ZERO free parameters)

| # | delta | admissibility |
|---|---|---|
| **D3** | `ERCOT_ORDC_PUBLISHED_ORDER_PARAMS_BY_YEAR` (new `constants.py` table) resolved onto `ordc_voll` / `ordc_mcl_mw` at the one seam holding both ISO and year (`pipeline/backcast_config.py`), so it reaches a replay through `meta.json` — which records neither field — and is written into `run_config.json` as the number the LP solved with (rule 24). | Rule 14 `[R-ACCURATE]`: PUCT order values, fixed by regulatory order, not by any result. Rule 21 `[R-DOF]`: zero free parameters. **Byte-identical for 2022-2025** (those years are listed at exactly the shipped defaults) and for every non-ERCOT ISO; a year absent from the table falls through to the shipped default, which is the correct forward posture. |
| **M1** | ERCOT 60-Day DAM thermal availability extended to **2021** (`ercot-thermal-dam-availability{,-hourly}.csv`, `-site-hourly.parquet`) from the four on-disk 2021 `Gen_Resource` fragments. | Rule 22: data is never held out. Committed 2022-2025 rows kept **byte-identical to HEAD** (verified by `diff` against `git show HEAD:`); the joint 2021-2025 re-derive would move `rating_mw` on 2,956/5,724 committed day rows by exactly 100.0 MW (max `avail` delta 0.0069, `live_mw` — the measurement — identical), and that move is **REPORTED, NOT APPLIED**, exactly as the 2022 completeness pass decided. |
| **M2** | `NUCLEAR_MONTHLY_CF_BY_YEAR["ERCOT"][2021]` derived by `derive_nuclear_monthly_cf.py`; the 2022 and 2023 rows re-derived byte-identically in the same run as the producer re-proof. | Rule 22. Moves ERCOT's solve-surface row (ledgered; `PINNED_SURFACE_ROWS_BY_ISO` advanced with a dated cause block). No existing year's values move. |
| **M3** | `data/clean/gtc-limits/ERCOT/gtc-limits_2021.parquet` curated from the committed NP6-86 raws (13,538 rows / 14 GTCs; the same run reproduces 2022 at 13,321 rows, identical to the ercot-252 PRECOMMIT). `ercot_gtc_limits_measured` therefore arms on 2021 instead of falling back to static TTC. | Rule 22 + rule 14. |
| **M4** | `parse_ercot_shares` reads the NP3-565-CD native-load report in its **CSV** container as well as `.xlsx` (2018-2021 and 2026 are published as CSV; identical columns, stamps and MW; the only drift is the `HourEnding`/`Hour Ending` header spelling). `.xlsx` is tried FIRST, so all three training years resolve exactly as before. | Rule 14 + rule 22. Without it 2021 silently drops to the static per-zone `load_share` and loses every ERCOT zone's measured diurnal shape — measured data held out. |

### 2b. Pre-solve plumbing verified at this commit (zero-LP)

`reconstruct_bundle_fleet(ercot252_2022_touchpoint_repair, 2021)` rebuilds: 2,323
units / 80,752 MW / 391.27 TWh demand; `ercot_reserve_supply_cap_from_year = 2020`
and `ercot_load_resource_reserve_from_year = 2020` both live; GTC 2021 EASTEX /
PNHNDL / WESTEX measured caps active over 193 / 2,955 / 1,696 h; thermal DAM
availability applied at plant grain for all four classes; four reactors on measured
daily windows; no native-load warning. Measured 2021 series present:
`ercot_2021_as_up_mw.parquet` (RRS-UFR mean 561.6 MW) and
`ercot_2021_ordc_reserves_hourly.parquet` (RTOLCAP mean 10,945 MW).
`actual_tail.json` ERCOT 2021 = 258 RT h / 214 DA h > $200.

### 2c. What is NOT extended, stated at the gate

The year-scoped SCED conduct tables (`ercot_faststart_pool_*`, the cleared-share RT
basis, `ercot_offer_midcurve_*`, the coal peak-tranche year level, the per-plant
year-windowed coal curves) carry 2023-2025 only and **cannot** be extended: full-year
2021 SCED 60-day disclosures are past MIS retention. 2021 takes the same pooled /
static fall-through 2022 takes. The ORDC **LOLP curve** (`ordc_lolp_params_path`) is
NOT vintaged by D3 — only the cap and the MCL are — so 2021 prices on the keeper's
curve shape with the published 2021 anchors.

### 2d. G-DRIFT (rule 29(b)), keeper `git_sha` 0334c35e → HEAD 9a67ecb6

`git diff` over `src/market_sim scripts/run_calibration*.py scripts/lib
data/raw/_validation-source data/raw/reference` = +1,310 / −30, classified **INERT
for an ERCOT backcast**: (i) the SPP intake — a seventh ISO's branch an ERCOT solve
never enters; (ii) pjm-169 F2 `pjm_interface_feed_admissibility_gate`, armed on
`iso.upper() == "PJM"` alone; (iii) pjm-169 F4 `gas_offer_margin_anchor_vintage`,
GATED default `False`, dropped from the hash at its declared `False`, absent from the
ERCOT recipe. `data/raw/_validation-source` and `data/raw/reference` are unchanged —
no measured-input drift. **No LIVE hunk, so no control solve is earned** (and none is
spent: this is a rule-30 rung, not an A/B).

## 3. Predictions, fixed before the solve

**Uri (2021-02-13..20) will dominate every price criterion, and three structural
limits mean the model cannot reproduce it. They are named here, before the result,
so none of them can be offered afterwards as an explanation that was reached for:**

1. **Demand is METERED load.** ~20 GW of firm load shed during Uri is absent from the
   demand the LP must serve, so the LP faces a materially easier Uri than the market
   did. This is a property of the backcast demand basis, not of this recipe.
2. **The DAM availability view is shallow at Uri.** The 60-Day DAM disclosure reads
   CC_REGULAR 0.886 → 0.691 across Feb 14-18 — a day-ahead declaration, far above the
   real-time freeze-off. How deep the model's Uri outage actually goes is decided by
   the CAMPD measured-event precedence cap, which bounds the DAM restore, not by this
   overlay.
3. **Only the ORDC anchors are vintaged**, not the curve shape (§2c).

| quantity | prediction | basis |
|---|---|---|
| **C3a** mean LMP | **FAIL, LOW — central estimate ≈ −40 %, range −25 % to −55 %** | Uri carries the majority of 2021's annual mean; limits 1-3 above |
| **C3c** tail (RT > $200) | **60-160 h vs 258 actual**, i.e. below the 0.5× floor (129 h) | same |
| C3c determination | **auto-ledgered CAVEAT whatever else fails** | rubric v3.6: on an out-of-training year the lone-failure condition is DROPPED |
| **C3b** NRMSE | **FAIL, 0.25-0.60** | the shape is dominated by an event the model cannot form |
| **C1** CC_REGULAR | **inside ±8.00 TWh, negative — −3 to −9 TWh** | 2021 is a no-HSL year, so renewables ride `forecast_uncurtailed` re-curtailed by the armed ceilings, as in 2022 (−6.87 TWh); less wind capacity in 2021. Genuinely uncertain. |
| C2, C4, C6, C8 | **hold** | untouched by every delta |
| **determination** | **NOT-YET on {C3a, C3b}**, C3c ledgered | above |

**The counterfactual D3 closes, stated ex ante:** without the vintage the model would
price 2021's scarcity against a $5,000 cap the market did not have — a ceiling 44 %
below the published one in *every* scarcity hour. D3 does not make 2021 pass; it makes
the miss attributable to price FORMATION rather than to a known-wrong parameter.

## 4. Reporting duties (rules 15, 22, 26, 30)

1. Register the moment it finishes (rule 15), keeper-only retention, `--no-prune`.
2. `stamp_touchpoint_holdout.py --holdout-year 2021 --keeper-id 2026-09-05-ercot248-two-config-keeper` (rule 30(a)); `build_status.py --iso ERCOT` (rule 30(b)).
3. **Rule 30(c): ERCOT stays CALIBRATED on 2023-2025 whatever 2021 reads.** A validation number is iterable model-SELECTION evidence and is never quoted as a certified out-of-sample skill number.
4. The `complete` marker's `config_2022_designation` / `tier_authorized` gain a dated addendum recording D1-D3 and the new run id; prior text preserved verbatim.
5. Matrix (rule 26): ERCOT shard evidence only. **No cell verdict changes** — a holdout-year result never adjudicates a cell, and D3 is a published input, not a mechanism under test.

## 5. Stop rules — what the result does NOT license

* **No second arm.** One solve, one report. If C3a fails as predicted, nothing is re-chosen: the depths stay frozen (rule 23), the ORDC curve is not re-shaped, the cap is not re-picked, no multiplier is swept.
* **Nothing re-enters training from 2021.** Any parameter this result implicates goes back to the 2023-2025 loop (rule 22 step 3).
* **The keeper does not change.** This is a rung, not a promotion.
* **The C3c object (work item B) is identified on 2023-2025 ONLY** and is not permitted to read 2021 for identification, whatever 2021 shows.
