# PRECOMMIT closeout-SOCO-w2 phase 0 — coal at marginal replacement (spot) price, zero LP

Lane closeout-SOCO-w2, 2026-10-03, chartered by the backcast close-out desk. Plan
`docs/backcast-closeout-plan-2026-10.md` §3.8 step 1 (L1). Written and committed **before any reach number is
computed**. No LP, no ScenarioConfig field, no src edit in this phase.

## 0. Step 0 (owner-gated)

§3.8 step 0 (caveat-budget eligibility of a λ-referenced BA, same object as §5 R-8) is an owner ruling. The exact
question was sent to the desk at lane start. It cannot change the determination today: C1 CC_REGULAR 2019 (+3.2 pp,
MODEL MISS) fails independently of the budget.

## 1. Object

Keeper `2026-10-03-closeout-soco-3-coalpile` (bundle `results/calibration/closeout_soco_3_span`, R-54). Rubric v3.20.
Keeper readings the bars refer to (status part `frontend/data/backcast/status/SOCO.js`):

| Year | C3a | C3b NRMSE | CC_REGULAR share | COAL_BIT | COAL_PRB |
|---|---|---|---|---|---|
| 2019 | +8.7 % PASS | 0.112 | +3.2 pp **FAIL** | −7.82 TWh CAVEAT (ledgered) | −0.40 TWh |
| 2020 | +8.4 % PASS | 0.113 | +1.8 pp | −3.54 | −0.75 |
| 2021 | −6.7 % PASS | 0.125 | +2.4 pp | −3.59 | +1.19 |
| 2022 | −13.7 % CAVEAT (ledgered) | 0.282 CAVEAT (ledgered) | +0.7 pp | +1.23 | +2.64 |
| 2023 | −0.4 % PASS | 0.091 | +2.4 pp | −3.16 | −1.07 |
| 2024 | −6.0 % PASS | 0.184 | +2.0 pp | −3.51 | −1.88 |
| 2025 | −4.7 % PASS | 0.184 | (prelim, not gated) | −0.89 | +2.76 |

## 2. The mechanism under test

Southern's IIC (§3.1/§3.6) dispatches on marginal *replacement* fuel cost. The model prices every SOCO coal tranche
at the plant-month EIA-923 blended delivered cost (`coal_plant_monthly_pricing` seam). L1 re-prices only the
**econ (`econlo`/`econhi`/`econ`) and `peak` tranches** of SOCO COAL_BIT / COAL_PRB units at the plant's same-month
EIA-923 Page-5 **spot** (`Purchase Type == "S"`) MMBtu-weighted delivered cost. Must-run and committed tranches keep
the blend. Two forms, both evaluated, fixed now:

- **F1 (primary):** plant same-month spot price where that plant-month has spot lots with a reported cost; every
  other plant-month unchanged.
- **F2:** F1, else the plant's same-year spot mean (the `coal_captive_marginal_fuel_price` "plant-monthly, else the
  year's" convention).

The plan's fallback index (EIA weekly basin spot) is **not on disk** (`data/raw/coal-prices/` holds annual
mine-sales prices and a BLS PPI only), so no fallback form is evaluated; plant-months without spot lots stay at
the blend.

Rule 19 map (stated now): the only other mechanism that writes a SOCO coal econ/peak fuel price is
`coal_captive_marginal_fuel_price` (SOCO `U`, never armed). L1, if built, lives inside the same seam and is a
sibling selection (spot lots instead of non-captive lots) — never stacked with it. The coal pile floor
(`coal_monthly_pile_measured_receipts`, keeper) sets a *quantity*; L1 sets the *offer* above it. Interaction is
named in §3 and bounded.

## 3. Method (zero LP)

From the keeper's committed `hourly/unit_marginal_<Y>.parquet` (per unit-hour `mw`, `cap_mw`, P1 `mc`, tranche in
`unit_id`) and `hourly/system_<Y>.parquet` (zone price, demand):

1. **Unit heat rate**: per coal econ/peak unit, the OLS slope of monthly mean `mc` on the plant-month F923 coal price
   the seam writes (`data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet`, fuel_group Coal). Units with
   slope outside 8–14 MMBtu/MWh or R² < 0.8 take their plant's class median measured HR (reported).
2. **Offer delta**: Δmc = HR × (replacement − blended) per unit-month (F1, F2).
3. **Restack (energy + price)**: per hour, the flexible set is every thermal unit-tranche in `econlo/econhi/econ/peak`;
   all other units (must-run, committed, hydro, storage, imports) are held at keeper `mw`. The flexible energy
   E_t = Σ keeper `mw` over the set is re-filled in merit order of `mc` (base) and `mc + Δmc` (arm) within
   `[0, cap_mw]`; the restack price is the `mc` of the marginal flexible unit. Copperplate across SOCO's three zones.
   **Pile floor bound**: a coal unit-hour dispatched in the keeper with `mc` more than $1/MWh above its zone's price
   is treated as floor-bound and its keeper `mw` is held (it cannot fall under the arm).
4. **Delta method**: arm price_zt = keeper price_zt + (restack_arm_t − restack_base_t); arm unit energy = keeper +
   (restack_arm − restack_base). C3a/C3b are recomputed from the system parquet on the scorer's load-weighted
   definitions; C1 by editing the keeper payload's `gmModel` and re-running `calibration_verdict.score_fuelmix`
   (the closeout-SOCO-3 `c1_reach` pattern).
5. **Method validity gate (fixed now)**: the restack base must reproduce the keeper's annual load-weighted price
   within ±5 % and hourly r ≥ 0.85 in every year. A year that fails is reported on the same-setter greedy only
   (price shifts by Δmc in hours whose keeper marginal unit is an armed coal tranche, capped at the next undispatched
   flexible unit's `mc`; no energy shift), and its C1 is reported as not computed.

## 4. Bars (fixed ex ante)

- **Target (plan §3.8 row 1):** C3a 2022 |error| improves by ≥ 2.0 pp (−13.7 % → |e| ≤ 11.7 %).
- **K1:** no C1 PASS → FAIL in any class-year 2019–2025.
- **K2:** no currently passing C3a year leaves ±10 %; no currently passing C3b year leaves its band.
- **K3:** the target is missed.
- **K4 (the open residual must not worsen):** CC_REGULAR 2019 share worsens by > 0.3 pp, or COAL_BIT 2019 volume
  worsens by > 1.0 TWh.
- Reported, not gated: 2022 total coal vs bench 45.5 TWh; C3b 2022; per-year coal-marginal hour share.

**Verdict rule.** A form clears phase 0 iff it hits the target and trips no kill. If F1 clears, F1 is the build form;
else F2 if it clears; else **NOT CHARTERED** (reach table recorded, matrix cell updated) and the lane takes the next
open §3.8 step.

## 5. Next steps named now

If NOT CHARTERED: §3.8 step 2 falls with it; step 3 (pool-vs-BA benchmark-scope census + "purchases at energy cost"
written into the ledger rows) is zero LP and admissible; step 4 needs an owner download (Georgia PSC / Alabama fuel
testimony) and goes to the desk as an ask.
