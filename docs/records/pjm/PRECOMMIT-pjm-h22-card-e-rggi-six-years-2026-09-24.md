# PRECOMMIT — pjm-h22 Card E: RGGI allowance cost on the keeper, all six PJM years (2026-09-24)

Written and pushed **before any solve**. The six shards pin to this commit's full SHA.

**Keeper (control):** `2026-09-23-pjm-h19-dbs-span` (2023–25, CALIBRATED 8/8) + folded
`2026-09-23-pjm-h19-dbs-touchpoint` (2020–22, NOT-YET: C1, C3a, C3b). Bundles
`results/calibration/pjm_h19_dbs_{span,touchpoint}`, every leg solved at `2d57aa20`.
**Charter:** `docs/FINDING-pjm-h21-card-d-cc-volume-is-locational-2026-09-24.md` §6.1 (owner: build the
2020–22 inputs, run six shards). **Rules:** 1, 13, 14, 16/34(c), 19, 21, 28, 29(b), 31, 32/34/36.

## 1. The arm — one existing default-off switch

`pjm_rggi_allowance_pricing = true`. Everything else is the keeper recipe. `offer_curve_by_group` is
untouched: `authorized_price_tuning.used = false`. Member fossil units get
`mc += m[g] × P_RGGI(y) × emission_rate[g]` (per-plant EIA-860 state test; rule 19: one seam, the
pjm-146 one).

## 2. Data build (this commit and its parent, zero LP, zero free parameters)

| table | added | source / check |
|---|---|---|
| `RGGI_MEMBER_STATES_BY_YEAR` | 2020 (NJ in, VA out — identical to the 2025 set), 2022 (VA in) | Published membership. 2022 was omitted under the removed `[R-HOLDOUT]` quarantine and fell back to the 2025 set, dropping VA. |
| `PJM_RGGI_ALLOWANCE_PRICE_PER_TONNE` | 2020 **7.07**, 2021 **10.44**, 2022 **14.84** $/t | Four quarterly RGGI auctions per year, simple mean, ×1.10231. Same as NEISO's series; test re-derives each year from `carbon-auction-results.csv`. |
| `PJM_RGGI_ZONE_SHARE` | 2020–22 | `derive_pjm_rggi_zone_share.py` on `vintage_2020..2022`. The same run reproduces 2023–25 **exactly**. Synthetic-row fallback only (plant-level fleet). |

Solve-surface: the membership table has no ISO token, so **every ISO's cache key moves** (a cache miss;
no committed number changes, no other ISO reads membership in any armed path). Ledgered per ISO in
`tests/regression/test_persisted_identity.py`.

## 3. Phase 0 — predicted move (zero LP)

`scripts/probes/pjm_h22_carde_phase0.py` → `results/calibration/_pjm_h22_carde_phase0.json`.
Response = pjm-146's own solved per-zone Δ (git `25dd3b3d`, older keeper) for 2023–25. For 2020–22 the
response is scaled by price ratio against the year with the same membership (2021/22 ← 2023; 2020 ←
mean of 2024/25). **Linear scaling is an approximation, stated, not fitted.** Per-$ EMAAC CC response:
−0.79 / −0.77 / −0.46 TWh per $/t (2023/24/25), so bands are wide (±30 % on 2021/22).

**CC_REGULAR, model − actual, TWh (bench plants): keeper → predicted arm**

| zone | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|
| **EMAAC** | +13.0 → **+8.6** | +14.3 → **+6.1** | +13.2 → **+1.5** | +11.8 → **+0.1** | +13.8 → **−3.9** | +3.8 → **−7.4** |
| SWMAAC | −2.7 → −3.6 | −1.9 → −4.9 | −3.8 → −8.1 | −0.5 → −4.9 | −3.1 → −7.3 | −6.4 → −8.1 |
| **Dominion** | −10.5 → −10.0 | −4.4 → **−5.9** | −1.7 → **−3.9** | −13.7 → **−16.0** | −12.3 → −9.8 | −4.0 → −3.1 |

**C1 CC_REGULAR (class, grid-delivered; band 8 TWh): keeper → predicted**

| | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|
| keeper | +2.2 | +0.8 | **+11.1 FAIL** | +3.8 | +0.7 | +2.6 |
| Δ (phase 0) | −3.7 | −9.0 | −12.8 | −12.8 | −14.8 | −10.0 |
| predicted | −1.5 PASS | **−8.2 ~FAIL** | −1.7 **PASS** | **−9.0 FAIL** | **−14.1 FAIL** | −7.4 ~PASS |

## 4. Gates and predictions — declared before any solve

Decided on structure (rule 1). A failed gate does not kill the arm; a passed gate does not promote it.

- **G1 liveness.** (a) Shard hard stop: the solve log line
  `PJM <y>: partial-footprint carbon adder — N/M generators … (program RGGI, P $/t)` shows
  `P` = 7.07 / 10.44 / 14.84 / 14.87 / 22.83 / 24.35 and `N > 0`, with 2021–23 `N` clearly above
  2020/2024/2025 (VA in). (b) Load-weighted LMP rises vs control in every year.
  (c) EMAAC CC TWh falls vs control in every year.
- **G2 targeted predictions (direction, then size):**
  - EMAAC CC over-run shrinks in every year; in 2024–25 it crosses to under (≈ −4 / −7).
  - SWMAAC CC falls every year (it is ~100 % member).
  - **Dominion CC falls in 2021–23** (VA taxed): 2023 worsens to ≈ −16. Dominion 2020/24/25 moves ≤ ±3
    (not a member; leakage only).
  - C1 CC_REGULAR per §3: **2022 FAIL → PASS; 2023 and 2024 PASS → FAIL; 2021 and 2025 near the bar.**
  - COAL_BIT rises slightly (leakage, pjm-146 +3.5/+2.3/−0.1): 2020/21 over-run (+25.5/+19.2) worsens.
  - CT_PEAKER rises (pjm-146 +3.7..+5.9): helps 2021 (−8.7).
  - Price: +$1.3–1.4 in 2023–25 (pjm-146), ≈ +$0.4 / +$1.0 / +$1.4 in 2020/21/22 (scaled).
    C3a 2020 (+14.5 %) worsens by ~2 pp; 2022 (−10.4 %) moves toward PASS; 2023 (+0.6 %) rises
    to +4…+9 % (pjm-146 moved +3.0 → +11.1 % on its keeper, so a 2023 C3a FAIL is possible).
  - **Determination: span CALIBRATED → NOT-YET (C1 2023/2024) is the expected outcome.**
    Touchpoint stays NOT-YET.
- **G3 no silent breakage:** full rubric C1–C8, every year, vs the control on the same (rebuilt)
  benchmark. D-1/D-2/D-4 once per bundle, sequential. D-2 CT forced share should fall (pjm-146).

## 5. Population the lever CANNOT reach — named before the solve

1. **Dominion's under-run** (−1.7 … −13.7 TWh): sub-zonal congestion an 8-zone network cannot see
   (pjm-137, CLOSED). RGGI **worsens** it in 2021–23 and leaves it in 2020/24/25.
2. CC in the non-member West zones ("all other zones", +0.9 … +12.4): untaxed; RGGI can only push
   more energy there.
3. COAL_BIT 2020/21 over-run in non-member zones: leakage raises it.
4. Winter Storm Elliott 2022 (Card B).
5. Price-tail / reserve scarcity (C3c).

So the expected class-level result is **the cancellation removed from one side only**: EMAAC is fixed,
Dominion is not, and C1 CC goes short in 2023–24. That is the owner's stated trade (FINDING §6.1).

## 6. G-DRIFT `2d57aa20` → this pin (rule 29(b)) — zero LP

| hunk | PJM control |
|---|---|
| `ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE` + its declaration + `_eia860_current_ba_recoded` + `benchmark_semantics` SOCO fold | INERT: SOCO-keyed |
| `coal_fuel_inventory_plant_grain` (scenarios, `coal_fuel_inventory.py`, LP rows/spec/model, `run_calibration.py`) | INERT: default off, requires `coal_fuel_inventory` (MISO-gated), absent from the recipe |
| `campd_dark_unit_year_windows` (scenarios, `outages.py`, `arrays.py`, `resolved_inputs.py`) | INERT: default off, needs `campd_per_unit_attribution` (keeper: false); `-perunitdark-` extract exists for SOCO only |
| `forecast_parity_registry.py` | INERT: forecast-parity bookkeeping |
| this lane's three tables | INERT for the control: read only under `pjm_rggi_allowance_pricing` (flag off → $0 adder → scalar path) |

**All INERT ⇒ form 4 valid; the committed keeper bundles are the control.** `--rebuild-benchmark` on
the arm; keeper re-scored on the same benchmark.

## 7. DOF (rule 21)

Zero new free parameters. The ledger carries the RGGI price as `measured-external` (as pjm-146).
Rule 13: price and membership regenerate for a forward year from a forward allowance-price path.

## 8. Shards (rules 32 / 34 / 36)

Six, one per year, pinned to this commit's full SHA. Out-dir `results/calibration/pjm_h22_rggi_<y>`,
branch `claude/pjm-h22-rggi-<y>`.

1. `git rev-parse HEAD` = pinned SHA, else STOP.
2. `uv sync`; use `.venv/bin/python`.
3. `hydrate_data.py --profile pjm` (skip on a full clone), then `scripts/regenerate_clean.py` (full;
   an `emissions-unit-annual` OOM is harmless).
4. `scripts/data/fetch_pjm_da_virtuals.py --years <y> --feeds hrl_da_incs_decs`.
5. `scripts/data/curate_hydro_plant_modes.py --iso PJM` must report **57 run-of-river-class of 82**, else STOP.
6. Zero-LP self-check: `resolve_carbon_program(ScenarioConfig(iso="PJM", mode="backcast",
   pjm_rggi_allowance_pricing=True), <y>).price_adder` equals §4 G1(a)'s price, else STOP.
7. `scripts/replay_keeper.py <control> --years <y> --set pjm_rggi_allowance_pricing=true
   --out-dir results/calibration/pjm_h22_rggi_<y> --note "pjm-h22 Card E RGGI, <y>"`.
   The log must show G1(a)'s line, else STOP without pushing.
8. Commit the full bundle incl. `dispatch/<y>_P1.parquet` via a `.gitignore` negation and a plain
   `git add`. Push.

| year | control bundle |
|---|---|
| 2020, 2021, 2022 | `results/calibration/pjm_h19_dbs_touchpoint` |
| 2023, 2024, 2025 | `results/calibration/pjm_h19_dbs_span` |

**Retrievability (rule 34(e)):** the parent fetches every leg, composes, and lands the registered
bundles on `main` before this lane's PR merges. Shard SHAs are provenance only.
