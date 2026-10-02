# PRECOMMIT: ERCOT L1, coal fuel-delivery ceiling (ERCOT arm of `coal_fuel_inventory`, monthly pile, ceiling only)

Lane `closeout-ERCOT`, plan step 1 (`docs/backcast-closeout-plan-2026-10.md` §3.5). Written 2026-10-02, **before any solve**. The census it rests on is `FINDING-closeout-w1-zero-lp-censuses-2026-10-02.md` §1 (zero LP).

**Owner authority.** R-3 (plan §5.0, 2026-10-02) makes EIA-923 monthly receipts and month-end stocks admissible as a backcast per-plant take *ceiling* with a declared `stock_min`, never the burn. The desk charter approves the ERCOT arm (plan §5 D-ERCOT "Yes to both", L1).

**Launch gate.** HOLD until the W0 foundation lane (`claude/closeout-b-w0-foundation`) merges and the desk says launch. W0 changes every ERCOT year's fleet (the Decker Creek steam miss of FINDING §3 is one example), so a pre-W0 span would be paid twice.

## 1. Mechanism (no new ScenarioConfig field, zero DOF)

The existing row family `coal_fuel_inventory_plant_grain` + `coal_fuel_inventory_monthly_pile` + `coal_monthly_pile_measured_receipts`, armed **ceiling-only** (no take floor). One cumulative row per coal yard per month-end:

```
Σ_{g ∈ yard, t ≤ end of m} HR[g]·P[g,t]  ≤  (S_dec(Y−1) − stock_min)·hc  +  cumR_Y(m)      m = 1..12
```

- `S_dec(Y−1)` = EIA-923 Page 2 December stock.
- `cumR_Y(m)` = the year's own Page 5 receipts, every lot, each at its reported heat content (`build_coal_measured_receipts`).
- `stock_min` = **0 t, declared**. Citation: `src/market_sim/data/coal_fuel_inventory.py` module docstring ("Minimum operating stock = ZERO … a floor may be added later only from a cited days-of-burn source"). No days-of-burn source is cited, so no non-zero value is admissible. Zero is the loosest physically valid ceiling: any bind is fuel the yard never held.
- A yard with no same-year receipts row keeps the ratable prior-years profile, unchanged NEXT-9 behaviour. In practice that means **2025** unless its receipts are curated first (§3).
- Coal floors (`coal_mustrun_per_plant`, take-or-pay) stay as armed. No coal floor may demand fuel the pile does not hold (rule 17), so the floor reconciliation (§2.3) runs at month grain.

**Why it is admissible (rule 13 forward test).** Delivered fuel quantity is the quantity twin of the admitted F923 delivered price. Forward years carry a contract/rail delivery rate plus the model's own carried pile, and both respond to changed conditions. Backcast-only: `resolve_coal_budget_arms` already refuses forecast mode.

**Rule 19.** Nothing in the ERCOT keeper caps coal energy, so this is a missing limb, not a stacked mechanism. `coal_offer_level_rebasis` (R) is an offer-level lever and is untouched.

## 2. Code delta (build lane: Opus/Fable, rule 27; matrix cells only, no new row)

1. `scripts/run_calibration.py`: add `"ERCOT"` to `COAL_PLANT_GRAIN_ISOS`. Add `COAL_PILE_CEILING_ISOS = ("ERCOT",)`. In this tuple `resolve_coal_monthly_pile` / `resolve_coal_measured_receipts` accept the pile **without** the take floor; NWPP keeps its floor requirement byte-identically.
2. Same file: build the pile when `_coal_pile_armed` regardless of `_coal_floor_armed`, passing `floor_parts=None`. The builder already supports this (`build_coal_monthly_pile` returns `floor=None`).
3. `src/market_sim/data/coal_fuel_inventory.py::reconcile_floors_to_yard_budget`: add a month-grain path. A yard whose cumulative coal `min_gen` draw exceeds its cumulative ceiling at any month-end has its floors scaled by the smallest month-end ratio. Every already-feasible yard stays byte-identical. Unit test: 1 yard, 2 gens, 24 h split into 2 "months", floor > month-1 ceiling.
4. **Data precondition.** Curate 2025 Page 5 receipts from `f923_2025.zip` (EIA-923 Final 2025, landed per plan §4 ★2) with the existing `scripts/data/fetch_eia923_coal_receipts.py` + `curate_coal_receipts.py`. The Dec-2024 opening stock is already on disk. If the Final workbook lacks plant-level Page 5 rows, 2025 runs on the ratable rate and §4 uses the ratable prediction. No other substitute.
5. Tests: fast tier, plus a resolver test that ERCOT accepts the ceiling-only pile and NWPP still refuses a pile without a floor.

**Arm.** Backcast run config `coal_fuel_inventory_plant_grain=True`, `coal_fuel_inventory_monthly_pile=True`, `coal_monthly_pile_measured_receipts=True`, `coal_fuel_inventory_take_floor=False`. This is the same on every year and every config partition (forward 2024–25, 2023 carve-out, 2019–22).

## 3. Span and shards

Full span 2019–2025: 7 shards, one per year (rules 16 / 32 / 36), `scripts/shard_prompt.py --all-years`, full 40-char SHA. Compose with `scripts/probes/_miso260_compose_span.py`, score with `calibration_verdict.py`, promote only via `scripts/promote_keeper.py`.

Before launch, the parent re-runs `scripts/probes/_ercot_closeout_l1_coal_fuel_census.py` on the **post-W0 keeper** bundle (zero LP). If any plant-year's form-B excess moves by more than 0.5 TWh against FINDING §1.3, the §4 numbers are re-pinned in an addendum **before** the shards launch. Never after.

## 4. Predictions (on the r-24 keeper; re-pinned per §3 if W0 moves them)

| Gate | Keeper r-24 | Predicted |
|---|---|---|
| 2022 C1 CC_REGULAR | −10.07 TWh FAIL | **−4 to −6 (PASS, band ±8.0)**: 5.5 TWh PRB + 0.45 lignite removed, mostly to CC |
| 2022 C1 COAL_PRB | +5.84 | ≈ 0 to +1 |
| 2022 C3a | −9.9 % | −6 to −8 % (coal under CC leaves summer merit) |
| 2019 C1 COAL_PRB | −10.48 FAIL | −10.5 to −10.8 (still FAIL: Coleto 0.24 binds; the 2019/20 coal-conduct object is step 4, not this) |
| 2021 (CALIBRATED) | PRB −1.67, LIG +0.49 | PRB ≈ −2.2, LIG ≈ −0.1; stays CALIBRATED |
| 2023 | LIG +1.40, PRB −2.17 | LIG ≈ +0.5, PRB ≈ −2.4; C3a/C3b unchanged within 1 pt (R-6 carve-out) |
| 2024 | LIG +1.25, PRB −0.95 | LIG ≈ +0.2 (Oak Grove 0.67, Twin Oaks 0.35 bind), PRB unchanged; C3a ±0.5 pt |
| 2025 (ratable unless §2.4 lands) | PRB +3.64 | PRB ≈ 0 to +0.5 (Parish 2.58, Limestone 1.00 bind on the ratable rate). With measured 2025 receipts: re-pinned per §3 |
| VOLL slack | 0 except 2021 3,194 MWh | unchanged |

## 5. Kill rules (ex ante)

- **K1 (primary).** 2022 C1 CC_REGULAR still outside ±8.0 TWh → the arm is **R** for the 2022 C1 object. Record it; do not promote.
- **K2 (binding where the census says).** In every year, the pile rows' duals must be non-zero only for yards whose census form-B excess is > 0 (±1 month). A yard binding where the census shows slack > 5 % of its annual budget is a construction bug. Stop and diagnose before scoring (rule 17 analogue).
- **K3 (no manufactured scarcity).** No year's VOLL slack MWh or shed hours may rise above the keeper's. Any new shed hour is a stop.
- **K4 (no new legitimacy family).** D-4 / rule-20 forced-budget: no new failing family in `legitimacy_diagnostics.json`.
- **K5 (determination).** No year's determination may worsen, and no criterion may go PASS → FAIL, in any year.
- **K6 (2025 basis).** If 2025 ran on the ratable rate, report it as such in the RESULT. A ratable 2025 bind is admissible (prior-years rate, rule 13 clean) but is labelled as not measured.

**Promotion.** If K1–K5 pass, promote on structure (owner standing instruction "Is it an improvement? Then promote"; rules 31/35). If only K1 fails, the mechanism is still structurally real (rule 1). Report it, and the owner rules on promotion.

## 6. Matrix

Rule 28: ERCOT cells for `coal_fuel_inventory_plant_grain`, `coal_fuel_inventory_monthly_pile` and `coal_monthly_pile_measured_receipts` move U → (verdict) in the session that scores the span, citing that RESULT. `coal_fuel_inventory` (the pooled MISO limb) and `coal_fuel_inventory_take_floor` stay **U / unarmed** for ERCOT: no ERCOT contract census exists, and the take floor is NWPP's own evidence.
