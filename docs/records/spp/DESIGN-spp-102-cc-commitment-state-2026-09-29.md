# DESIGN — SPP-102: a CC commitment state for SPP. Phase 0 at zero LP, and a recommendation

**Charter.** Owner decision card after SPP-101, *"Charter commitment lane"*, 2026-09-29. This is a design lane:
nothing solve-affecting is built before the owner rules on this document.
**Control.** Keeper `2026-09-28-spp-100-chp-scope` (bundle `spp100_arm_span`, 2019–2025). **LP spent: 0.**
**Object.** In 2021/22, actual CC ran 7.3 / 4.8 TWh in hours where actual RT LMP ≤ $15. The keeper ran
2.2 / 0.6 TWh there, and coal took the energy (`results/calibration/_spp89_coal_cc_swap.json`). The failing
validation rows it feeds are C1 CC_REGULAR −9.65 / −10.84 TWh and C1 COAL_PRB +13.20 / +13.17 TWh
(2021 / 2022), and C4 gas 0.307 / 0.356. The C1 band is 8 TWh (`FUELMIX_VOL_CAP_TWH`), so CC needs
**+1.7 TWh (2021) and +2.9 TWh (2022)** to pass, and coal needs −5.2 TWh.

**Probes** (all zero LP; outputs in `docs/handoffs/spp102/`):
- `scripts/probes/_spp102_cc_commitment_drivers.py` → `cc_commitment_drivers.json` (driver census)
- `scripts/probes/_spp102_trough_physics.py` → `trough_physics.json` (gap vs min-down, DA)
- `scripts/probes/_spp102_stack_dump.py` + `_spp102_commit_dp.py` → `commit_dp.json` (physics bound)

## 1. Verdict

**No candidate clears an admissible bar. Recommend recording the 2019–22 CC/coal/gas rows as model-class
limits, and building nothing.**

- Hourly forward drivers carry little information about when SPP's CCs are online at low prices.
- Commitment **physics** is admissible, but even a perfect binary version of it adds at most
  **+0.8–0.9 TWh CC in 2021 and +0.1 TWh in 2022**. That is below what the rows need, and it is an
  upper bound.
- The one strong signal is **which plant** it is. Turning that into a floor fails rule 17 by construction,
  and it is the pinned CEMS profile the charter already records as dead.

## 2. Phase 0 — what keys SPP CC online at low LMP

Unit: 21–22 SPP CC_REGULAR plants with a CEMS series (bench `campd`), plant-hours inside actual-RT ≤ $15
hours. Online = CF ≥ 5 % (CEMS) or ≥ 1 % (keeper), the SPP-97 convention. Scored by AUC, which fits no
threshold. 0.5 = no information.

### 2.1 The gap, per year

| year | low hours | CEMS online rate | keeper online rate | gap at min-load (TWh) | share in spells > 48 h | median spell (h) |
|---|---|---|---|---|---|---|
| 2019 | 2,980 | 0.49 | 0.47 | 0.91 | 0.86 | 378 |
| 2020 | 3,978 | 0.50 | 0.48 | 1.35 | 0.87 | 303 |
| **2021** | 2,958 | 0.37 | **0.11** | **2.42** | 0.76 | 181 |
| **2022** | 2,119 | 0.35 | **0.04** | **1.99** | 0.79 | 162 |
| 2023 | 2,665 | 0.49 | 0.26 | 2.05 | 0.82 | 185 |
| 2024 | 3,353 | 0.52 | 0.32 | 2.21 | 0.85 | 282 |
| 2025 | 2,634 | 0.43 | 0.17 | 2.19 | 0.82 | 309 |

The real fleet's low-price online rate barely moves across years. The keeper's collapses in 2021/22, when gas
was expensive against coal. This is SPP-75's finding (the model's commitment is far more fuel-price-elastic
than the real fleet's), now per plant-hour. **76–87 % of the real low-price online hours sit inside online
spells longer than two days.**

### 2.2 Candidate drivers (AUC inside low-price hours)

| driver | forward-reproducible? | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|---|
| net load now | yes | 0.63 | 0.56 | 0.63 | 0.62 | 0.62 | 0.59 | 0.60 |
| max net load, next 24 h | yes | 0.61 | 0.58 | 0.59 | 0.59 | 0.58 | 0.61 | 0.58 |
| max net load, gas day (09–09 CPT) | yes | 0.61 | 0.55 | 0.59 | 0.59 | 0.57 | 0.59 | 0.58 |
| heating season (Nov–Mar) | yes | 0.46 | 0.47 | 0.48 | 0.50 | 0.47 | 0.49 | 0.46 |
| DA LMP ≤ $15 (diagnostic; an outcome) | no | 0.47 | 0.45 | 0.44 | 0.43 | 0.44 | 0.44 | 0.45 |
| plant conduct, leave-year-out on-frequency | measured unit attribute | 0.78 | 0.83 | 0.75 | 0.77 | 0.75 | 0.70 | 0.77 |

Within-plant AUCs (plant identity removed) for net load are 0.61–0.70. **Load, net load, gas day and season
are weak. The only strong signal is plant identity.**

### 2.3 Commitment physics: min-down and start cost

**Off-gap length.** Where the gap sits in the keeper's own off-gaps (TWh at min-load):

| year | gap | in gaps ≤ 8 h (ASOM min-down) | in gaps ≤ 24 h | in gaps > 24 h | in hours with DA > $15 |
|---|---|---|---|---|---|
| 2019 | 0.91 | 0.33 | 0.59 | 0.30 | 0.24 |
| 2020 | 1.35 | 0.38 | 0.89 | 0.43 | 0.26 |
| 2021 | 2.42 | 0.23 | 1.14 | 1.22 | 0.97 |
| 2022 | 1.99 | 0.11 | 0.65 | 1.25 | 1.02 |
| 2023 | 2.05 | 0.40 | 1.03 | 0.95 | 0.62 |
| 2024 | 2.21 | 0.46 | 1.12 | 1.05 | 0.51 |
| 2025 | 2.19 | 0.36 | 1.14 | 1.05 | 0.62 |

**Real SPP CCs do cycle.** Their CEMS off-spells have a median of 10–12 h and a p25 of 6–8 h, and 29–40 % are
≤ 8 h. So the ASOM min-down (8 h) is consistent with measured conduct. But in 2021/22 half the gap sits in
keeper off-gaps longer than a day, where no min-down constraint reaches.

**Perfect-physics bound.** Per plant, a binary unit commitment was solved by DP against the keeper's own P1
zonal price, with the keeper's own offer cost and availability (stack rebuilt with no LP). Two admissible
physics sets were fixed before the run:
- ASOM: min-up 21 h, min-down 8 h, start cost $50/MW (the keeper's CC committed tranche);
- NREL: `CC_COMMITMENT_PARAMS` by heat rate.

Price is held fixed, but committing at pmin would only lower it. The DP also has perfect foresight over the
whole year, while SPP's DA SCUC sees one day. Both make this an **upper bound**.

| year | Δ CC all hours, TWh (ASOM / NREL) | Δ CC low hours | precision of added low hours vs CEMS | CEMS base rate | recall of the gap |
|---|---|---|---|---|---|
| 2019 | +1.05 / +1.03 | +0.88 | 0.45 | 0.49 | 0.79 |
| 2020 | +1.17 / +1.09 | +1.15 | 0.44 | 0.50 | 0.69 |
| **2021** | **+0.83 / +0.93** | +0.95 | 0.55 | 0.37 | 0.35 |
| **2022** | **+0.11 / +0.11** | +0.40 | 0.54 | 0.35 | 0.17 |
| 2023 | −0.17 / −0.11 | +0.50 | 0.49 | 0.49 | 0.30 |
| 2024 | +0.39 / +0.44 | +0.82 | 0.57 | 0.52 | 0.42 |
| 2025 | +0.70 / +0.82 | +0.85 | 0.58 | 0.43 | 0.40 |

Against the +1.7 / +2.9 TWh the 2021/22 CC rows need, the physics bound reaches **about half of 2021 and
4 % of 2022**. In 2019/20 its added hours land **below the base rate**, i.e. worse than chance. The 2022
recall is 0.17: a cost-minimizing commitment at the keeper's costs does not keep these plants on.

## 3. The three forms considered

### A. Relaxed commitment state in the LP (the SPP-83 successor form) — admissible, too small

- **Form.** A continuous commitment variable u ∈ [0,1] per CC plant-hour, with P ≥ pmin·u, P ≤ avail·u,
  start variables with cost, and min-up/min-down coupling. It is still an LP, and prices are still duals
  (rule 4).
- **Driver, window, forward story (rule 17).** The driver is unit physics: times from the SPP MMU ASOM
  (published, by fuel) and start cost from the keeper's committed tranche. It binds wherever the unit's own
  economics make a stop dearer than idling. It regenerates for any forward year from the same parameters.
- **Parameters (rule 21).** Zero fitted: ASOM min-up 21 h / min-down 8 h, keeper start cost $50/MW, SPP-44
  min-load 0.209. **Gap:** SPP publishes no per-class start-up dollars (SPP-73/83 STOP), so start cost is
  the keeper's generic value, not a measured SPP number.
- **Rule 19.** It would replace, not stack on, the start-up amortization channel
  (`tranche_startup_amortization`, R) and every CC bridge (`spp_gas_commitment_bridge`, R). It must also be
  reconciled with `coal_sync_ensemble_level` (K), `chp_steam_floor_*` (K) and
  `mustrun_commitment_feasibility_clip` if CC is ever extended to coal or CHP.
- **D-4 exposure.** DP precision against CEMS is about 0.54–0.57 in 2021/22 (§2.3). So roughly 45 % of the
  low-price hours it adds in 2021/22 are hours SPP had the plant off, and in 2019/20 its added hours are
  worse than chance (0.44–0.45 against a 0.49–0.50 base rate).
- **Predicted effect.** Bounded by §2.3: +0.8–0.9 TWh CC in 2021 and +0.1 TWh in 2022, all hours. It flips
  **no** row. The LP relaxation is weaker than the binary DP, so the real effect is smaller still.
- **Cost.** It is an engine lane, not an SPP lever. It adds about 3 × n_CC × 8760 columns plus min-up/down
  rows with up to 21 nonzeros each. Every ISO would need the same A/B before it could arm anywhere, and
  P2 (the archived MIP commitment path) is the precedent for how much engine that is.
- **How it could fail.** Fractional u at low cost: the relaxation can commit 10 % of a plant and dispatch
  it at pmin·0.1, so the tight-formulation choice is load-bearing. It would also add CC in 2023–25
  (+gap 2.0–2.2 TWh at min-load). That is the right sign for CC there, but it lowers train-year trough
  prices, and C3a 2023–25 is passing by a margin this doc has not measured.

### B. Conduct-scoped committed floor — refused

- **Form.** Plants whose leave-year-out on-frequency is above 0.5 are held at min-load whenever available.
  This is the SPP-100 `chp_steam_floor_conduct_scope` selector, used here as the floor itself rather than
  as a scope.
- **Why refused.** Precision inside low-price hours is **0.48 / 0.48** in 2021/22 (0.60–0.66 in other years),
  so the floor binds in hours when SPP had the plant **off** 34–52 % of the time. Rule 17 calls that a
  bug by definition. It also has no hourly window or driver, only a plant list, which makes it the
  static form of the pinned CEMS online profile the charter records as dead under rule 13.
- For the record: reach in low hours is 5.2 / 4.1 TWh at min-load (2021/22), of which 2.4 / 1.9 is correct.

### C. Hourly driver gate (net load, gas day, season) — refused

AUC is 0.55–0.63 pooled and 0.60–0.70 within plant (§2.2), so a gate on any of these would have precision
near the base rate. It would reproduce SPP-97's gap-bridge failure mode, which failed at or below chance.

## 4. What the residual is

Put §2 together:
- Half the 2021/22 gap sits in hours where SPP's own DA market priced above $15 (0.97 / 1.02 TWh).
- Even the perfect-foresight physics bound cannot hold CC on through it at the keeper's relative costs.

So the residual is not a missing commitment **state**. It is one or both of two known objects:
1. **The DA-SCUC horizon / forecast wedge.** SPP commits day-ahead on a forecast, then RT prices collapse.
   This is SPP-29/73/75/77, model-class for an hourly perfect-foresight LP.
2. **The 2021/22 relative coal-vs-gas cost basis.** Real SPP loaded CC on through troughs, and coal at 0.83–0.92
   of available, even though the keeper's costs make that uneconomic. This is SPP-89 / SPP-44's 2022 coal
   markup, which is procurement-blocked.

**Neither is a lever this lane can build.**

## 5. Rules

| rule | status |
|---|---|
| 1 `[R-STRUCT]` | Form A is structurally real and was not rejected on the residual. It is recommended against on cost vs. a bounded, row-neutral effect, and it stays open as an engine lane if the owner wants the structure for its own sake. |
| 13 `[R-MEASURED]` | CEMS online state was used only as the scoring target. Conduct was computed leave-year-out and is refused as a floor (§3B). DA LMP is diagnostic only. |
| 14 / 18 / 21 | ASOM times are published physics. Start cost has no SPP source (SPP-83 STOP). Zero fitted parameters in A. |
| 17 / 19 | See §3. |
| 28(b) | Matrix: `online_capacity_envelope` stays U with this evidence appended. No new field, because nothing was built. |
| 31–36 | No arm, no solve, no shard, no bundle. Nothing to promote and nothing stranded. |
