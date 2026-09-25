# PRECOMMIT — miso-272: combined-cycle blocks rated on ONE EIA-860 row (the Edwardsport 481 MW phantom), reconciled at the source

```
LANE    : miso-272 (queue: miso-271 RESULT §5 routed item 1; charter candidate 1)
KEEPER  : 2026-09-25-miso-271-wefor-stack (results/calibration/miso271_span, 2019-2025), legs solved at 40d995ba
ARM     : keeper recipe + cc_block_summer_rating=true (NEW ScenarioConfig field, default off; this lane's code)
CONTROL : none solved. G-DRIFT 40d995ba..HEAD is all INERT for MISO (§3), so the keeper bundle IS the control (rule 29(b) form 4)
SHARDS  : 7 arm legs, one year each 2019-2025 (rules 34(c), 36), pinned to this document's commit SHA
DATA    : DATA PROFILE: miso
DOF     : +0. No multiplier moves (offer_curve_by_group byte-identical, sha c5ab11d9b26d2abf). Zero free parameters.
```

## 1. Year set (rules 34(c) / 35(b))

Registered MISO runs at HEAD: one, the keeper, years **{2019 … 2025}**; nothing is stamped to it. This lane
solves all seven.

## 2. Phase 0 — zero LP

Instruments:
- `scripts/probes/_miso272_block_phase0.py`, a fleet-only rebuild of the keeper recipe per variant.
- Record: `results/calibration/_miso272_block_phase0.json`.
- The raw census came from the EIA-860 operable sheets of every vintage.

### 2.1 The defect

Some EIA-860 filers put a combined-cycle block's **whole** net summer rating on the steam-part (`CA`) row and
leave every gas-turbine (`CT`) row in the same `Unit Code` blank. The loader fills each blank CT row with its
nameplate (`pmax = summer, else nameplate`). The block is therefore carried as its rating **plus** its CT nameplates.

The same pattern appears in every vintage 2019–2024 and in the canonical file, at the same **seven MISO plants**:

| plant | block rows | CA summer vs own nameplate | keeper carries (2023) | reported block rating | how the keeper caps it today |
|---|---|---|---:|---:|---|
| 1004 Edwardsport (IGCC) | CT1, CT2 (240.6, blank), ST/CA (331.5) | 555 (595 in 2019–22) | **1,036.2 COAL_BIT** | 555.0 | nothing: coal, so the CC guard does not reach it |
| 55218 Hinds | H01, H02 (176.6, blank), H03/CA (198.1) | 452.1 | 532.1 CC | 452.1 | `cc_capacity_reconcile` cap at CAMPD p999 |
| 55220 Attala | A01, A02, A03/CA | 455.4 | 516.8 | 455.4 | p999 cap |
| 55380 Union (4 blocks) | CTG1–8, STG1–4/CA | 504–511 each | 2,317.7 | 2,031.0 | p999 cap |
| 55418 Hot Spring | CT1, CT2, ST1/CA | 562.7 | 582.1 | 562.7 | p999 cap |
| 55467 Ouachita (3 blocks) | CTG1–3, STG1–3/CA | 236–245 each | 841.4 | 723.7 | p999 cap |
| 55620 Perryville | CT-1, CT-2, ST-1/CA | 576.8 | 637.9 | 576.8 | CC guard clip to nameplate (no p999 row) |

A standalone peaker with no Unit Code (Hinds `H04BS`, Perryville `2-CT`) is never part of a block and never
moves.

**Edwardsport is the one uncapped instance.** Its 481 MW excess has been carried as coal in every year,
on top of a 555–595 MW machine.

The six NG blocks were already capped, but on the wrong basis:
- Five sit at the CAMPD p999 (≈ winter capability), which is 3–16 % above their published summer rating.
- Perryville sits at nameplate.
- All six are in the CC guard's clipped set, so they also take the flat ambient summer derate that
  `summer_derate_basis_aware` removes from every correctly rated plant.

### 2.2 The fix, `cc_block_summer_rating` (new, default off; the one code change in this lane)

**Predicate.** For each `(plant, Unit Code)` of operating `CT`/`CA` rows, a block qualifies when all of these hold:
- it has ≥ 1 CT row and ≥ 1 CA row;
- every CT summer rating is blank;
- every CA summer rating is positive, and at least one exceeds its own nameplate. EIA-860's schema says summer ≤
  nameplate for one generator, so such a row can only be reporting the block.

**Action.** The block's reported total is allocated across its rows **by nameplate**. The block then sums to exactly
what EIA-860 reports, and each unit keeps its share of the block, which is what the CAMPD extracts key on.

**Properties.**
- **Zero free parameters.** Every number is an EIA-860 field of the vintage being loaded (rules 13, 21, 24).
- **Rule 14.** This is the misalignment exception, reconciled rather than guessed: the datum is correct, but it
  is filed on a block boundary and the loader reads it on a generator boundary.
- **Rule 19.** The fix is applied in `_load_fleet_from_parquet`, upstream of the merchant-CC guard and the
  `cc_capacity_reconcile` cap. Those see a block already at its published rating and do not fire, so one
  construction binds per plant.
- **Cap still binds where it should.** The p999 cap still applies where the summer rating exceeds it (Hot Spring
  2019–2022: 605.3 / 590.9 / 592.5 vs 582.1).
- **Fail-closed guard.** At the point of use, the flag refuses to run without
  `unit_outage_dispatched_bin_denominator` under a non-ERCOT historic overlay. The reconstructed outage-capacity
  map does not carry the fix. The keeper arms that denominator.
- **Other load paths.** The CSV override and clean seam raise rather than no-op.
- **Tests:** `tests/unit/data/test_cc_block_summer_rating.py`.

### 2.3 What the arm moves (fleet-only, arm − keeper)

| year | COAL_BIT MW / avail TWh | CC_REGULAR MW / avail TWh | CT_PEAKER avail TWh | units outside the 7 plants that move |
|---|---|---|---:|---:|
| 2019 | −473.0 / −3.683 | −673.7 / −3.639 | +0.049 | 0 |
| 2020 | −473.0 / −3.256 | −666.1 / −3.620 | +0.057 | 0 |
| 2021 | −473.0 / −3.688 | −666.1 / −3.427 | +0.057 | 0 |
| 2022 | −473.0 / −3.688 | −616.9 / −3.177 | +0.057 | 0 |
| 2023 | −481.2 / −3.688 | −626.3 / −3.427 | +0.056 | 0 |
| 2024 | −481.2 / −3.200 | −624.5 / −3.301 | +0.056 | 0 |
| 2025 | −328.6 / −2.262 | −762.3 / −4.060 (incl. Edwardsport −152.6) | +0.057 | 0 |

Heat rates are byte-identical. Three side effects of the fix are declared here, not hidden:

1. **CT_PEAKER +0.05 TWh.** The standalone peakers at Hinds and Perryville leave the CC guard's clipped set with
   their plant. They therefore lose the flat summer derate, as every correctly rated plant already does.
2. **Outage numerator basis.** The CAMPD unit-outage extracts carry each unit at its **nameplate** share
   (Edwardsport CTG = 406.3 MW = ½ × 812.7). The miso-266 denominator divides by LP pmax. A one-train outage
   therefore removes the following share of the block, against a true ~50 %:

   | block | keeper | arm |
   |---|---:|---:|
   | Edwardsport | 39 % | 73 % |
   | Hot Spring | 61 % | 64 % |
   | Union | 13.1 % | 14.9 % (true 12.5 %) |

   Edwardsport's availability fraction falls 0.78 → 0.70 (2023). **The mismatch is pre-existing.** Hot Spring
   already over-removes at 61 %. It belongs to the outage numerator/denominator basis (the
   `unit_outage_extract_basis_share` family), is routed in §7, and is not absorbed here.
3. **2025 reads the canonical file.** That file labels Edwardsport's CTs `NG`, so the allocated 328.6 MW sits in
   CC_REGULAR, as it did in the keeper (481.2 MW). This is pre-existing.

**Direction hazard, declared.** The arm removes about 1.1 GW and 6–7 TWh/yr of available thermal energy, so
price rises and CC dispatch falls. Both work against MISO's open gates:
- **C3a 2019 / 2020** are already +10.8 / +10.9 % high.
- **C1 CC_REGULAR** passes at −5 to −7.7 TWh.

The basis is rule 14 and rule 19, never the residual. The arm stays in whether it helps or hurts, and is reported
at full magnitude (rule 1).

## 3. G-DRIFT (rule 29(b)) — keeper legs `40d995ba` vs this SHA

`git diff 40d995ba <this SHA> -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py
scripts/lib data/raw/_validation-source data/raw/reference`

Seven upstream commits, plus this lane's own change. Every upstream hunk is classified below.

| hunk group | class | reason |
|---|---|---|
| R-SOCO-B2 `ISO_BA_EXITS` (`constants.py`, `eia860.py` `_exit_member_mask` / `drop_current_ba_recoded_rows(year=)`, `arrays.py` BA-exit mask, `run_calibration_full.py` `_iso_plant_ids` / `_eia923_frame`, `solve_surface_declared.py`, `cache.py` prose) | INERT | `{"SOCO": …}` only. Every helper returns empty for MISO. |
| NWPP-NEXT / -2: FERC 714 (`ferc714.py`, `paths.py`), `EIA930_REMOTE_GENERATION_DOUBLE_BOOKED` (PSEI), `eia930/frames.py` `_repair_published_extract`, `eia930/actuals.py`, NWPP 2020 reference rows | INERT | Registered for PSEI / NWPP only; each returns the input unchanged for the MISO BA. |
| R-ERCOT-4 `ercot_partial_outage_day_guard` (`scenarios.py`, `outages.py`, `arrays.py`, `outage_detect.py`) | INERT | A default-off flag absent from the keeper recipe. It acts only with `ercot_partial_outage_shaped_derate`, which is also off. |
| PJM-NEXT `fleet_zone_vintage_coords` (`zone_assignment.py`, `eia860.py` `_assign_zones`, `run_calibration.py`, `runner.py`) | INERT | A default-off flag absent from the keeper recipe; the lookup is `{}` while off. `_eia860_ba_zones(iso, plant_path=None)` is a signature refactor, and its default path is unchanged. |
| PJM-NEXT benchmark vintage-union read (`run_calibration_full.py` `build_benchmark_frames`) | INERT | SCORING-only. The keeper records `benchmark_membership_vintage_union: false`. |
| SPP-80 SPP hub LMP components | INERT | Another ISO's data. |
| **this lane: `cc_block_summer_rating`** (`scenarios.py`, `eia860.py`, `assembly.py`, `run_calibration.py`, `arrays.py`) | the ARM | Byte-inert off. Default key unmoved (tested). |

**All upstream hunks are INERT, so form 4 holds for every year.** The keeper's committed bundle is the control, and
no control solve is earned.

## 4. The arm (exactly one field)

```
python scripts/replay_keeper.py results/calibration/miso271_span --years <Y> \
  --set cc_block_summer_rating=true \
  --out-dir results/calibration/miso272_arm_<Y> --note "miso-272 arm <Y>: CC block summer rating"
```

**Shard check:** `scripts/probes/_miso272_shard_check.py --leg results/calibration/miso272_arm_<Y> --year <Y> --log <log>`.
- Recipe: the keeper plus exactly `cc_block_summer_rating: False → True`.
- Pinned inputs: the miso-271 pins, all re-verified at this SHA.
- Hydro classifier sha `dc2a9d4be30a0727`, re-verified at this SHA.
- Log markers: the miso-271 set plus `CC block summer rating (plant 1004)`.

**Before solving,** a shard builds the three derived `data/clean` partitions the keeper recipe hard-requires:
`curate_hydro_plant_modes.py`, `curate_coal_stocks.py` and `curate_coal_receipts.py`.

## 5. Predictions (fixed before any shard; directions only)

1. **Capacity:** COAL_BIT down about 0.47 GW every year, and CC_REGULAR down about 0.62–0.76 GW.
2. **Price:** load-weighted price up every year, most in high-load months.
   - C3a moves **away** from the band in 2019 and 2020 (both already high).
   - Elsewhere it moves toward whichever side the year's error sits on.
3. **CC_REGULAR dispatch:** down. C1 CC_REGULAR moves away from zero.
4. **Replacement energy:** CT_PEAKER, ST_GAS and imports rise to replace it.
5. **Slack:** it may rise in the tight hours of 2023 and 2024 (h5654–5656, h5700–5706). A rise is reported, not
   fixed.

## 6. Decision rule (fixed now)

Recommend promotion iff every structural gate holds:

* **S-1 recipe.** Every arm leg is the keeper plus exactly §4's one field, with pinned inputs, the pinned hydro
  classifier, and every mechanism log line present, including the reconciliation's own line for plant 1004.
* **S-2 single delta.** Checked zero-LP by the fleet-only rebuild above, and re-checked on each leg's recorded log:
  - arm − keeper pmax moves **only** at the seven census plants;
  - heat rates are byte-identical;
  - each block sums to its EIA-860 reported rating, clipped only by the pre-existing p999 cap.
* **S-3 slack.** Any arm year with more slack than the keeper is **reported with its hours**. It is not a failure:
  removing a phantom can legitimately tighten a year.

Gates C1–C8 are reported per year at full magnitude, both ways, and decide nothing (owner standard, rule 1). The
promotion decision is the owner's (rule 31).

## 7. Routed, not fixed here

1. **Coal statistical-WEFOR stack** (charter candidate 2). Sized at zero LP for 2019:
   - The statistical term removes **34.4 TWh/yr** of coal availability (COAL_BIT 11.6, COAL_PRB 21.6,
     LIGNITE 1.3).
   - The measured short-coal windows remove only 4.4 TWh.
   - All CAMPD overlays together remove 98.3 TWh.

   Short-coal is guarded to baseload units (when-operable CF ≥ 0.55), so which units the measurement covers is
   per unit and per year, and **the committed extract does not record the screened set.** A unit that passed the
   screen with zero events is indistinguishable from one that was never screened. The prerequisite is a derive
   output: the per-unit-year screened set from `derive_campd_unit_outages.py`'s own guard. That is a data step
   (rule 23: new output, same source), and it collides with the open "short-coal extract does not reproduce at
   HEAD" item. Not solved here.
2. **Outage numerator basis at block plants** (§2.3, item 2). Edwardsport's one-train outages over-remove once its
   phantom is gone, and Hot Spring already over-removes today. The construction is one denominator for one
   numerator basis (`unit_outage_extract_basis_share` exists, default off, and is mutually exclusive with the
   dispatched-bin denominator). This is a MISO-lane successor.
3. **C3a 2019/2020 overnight body** (charter item 3). The only remaining channel is the rule-1 coal band multiplier.
   That is the owner's decision, not swept here.
4. **C3b 2021 February gas array** (charter item 4). Owner decision D1 on the storm-month convention is still pending.
5. Out of lane, status only:
   - the forecast gate-(a) row still names miso-268;
   - the cross-ISO `mid_vintage_exit_carry` pairing;
   - `filter_revealed_outages` drops unit-partial plateaus;
   - the std-unitroute / short-coal extracts do not reproduce at HEAD;
   - the 8 pre-existing `tests/unit/config` failures, identical on unmodified `main`, including the unregistered
     NWPP `EIA930_REMOTE_GENERATION_DOUBLE_BOOKED` solve-surface declaration.
