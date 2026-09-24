# PRECOMMIT — miso-268: the coal budget at the grain coal actually sits at (one pile per yard, not one pile per fleet)

```
LANE    : miso-268 (MISO held-out-year rubric failures, structure first)
KEEPER  : 2026-09-23-miso-267-dispatched-bin (results/calibration/miso267_dbd_span, 2020-2025), git_sha 3ea64fa5
ARM     : keeper recipe + coal_fuel_inventory_plant_grain=true. ONE flag. NEW field, built this lane, default off.
CONTROL : the keeper's committed bundle (rule 29(b) form 4). No control solve.
SHARDS  : six, one per year 2020-2025 (rules 36, 34(c)), pinned to the SHA this document is pushed at.
```

## 1. The object, and why this lever

`coal_fuel_inventory` (miso-259, keeper `K`) caps coal energy input against **one fleet pile**:
the footprint's Dec(Y-1) stock plus mean Y-2..Y-1 receipts, summed over every yard. Coal does not
move between yards. The pooled row therefore lets the LP burn coal at a yard that never held it
against tons sitting at another.

**Measured on the keeper's own solved dispatch, zero LP**
(`scripts/probes/_miso268_plant_grain_phase0.py` → `results/calibration/_miso268_plant_grain_phase0.json`;
per-unit P1 dispatch from the miso-267 leg commits, LP heat rates from a `fleet_only` rebuild,
budgets from the exact builder the arm uses):

| year | yards rowed | yards over own supply | **static excess, TWh-equiv** | pooled annual row |
|---|---:|---:|---:|---|
| 2020 | 78 | 13 | **2.64** | slack |
| 2021 | 77 | 20 | **11.76** | slack |
| 2022 | 71 | 27 | **19.01** | slack |
| 2023 | 66 | 11 | **2.33** | slack |
| 2024 | 63 | 4 | **0.49** | slack |
| 2025 | 57 | 16 | **9.38** | slack |

The excess lights up in the years the real fleet ran its piles down (MISO's January 2022 stock
was the lowest in the published record, `FINDING-miso258`) and is small in the others. Named
yards include Meramec (retired Dec 2022; the keeper runs it 2.8 TWh in 2022 on ~0.24 Mt of
supply, CEMS 0.13–0.26 TWh) and Trenton Channel (retired 2022; CEMS ≈ 0).

**Why this and not another queue item.** §5.4 names the coal budget's grain as the open object
(miso-259 stamp: "most of the bite is the MONTHLY NO-CARRY GRAIN"). This lever touches the
*spatial* grain only and adds **no** month grain at the yard, so it does not extend the no-carry
limitation. It is not on the DO-NOT-REDO list. The price-body, C3b and trough objects were
localized at zero LP (FINDING-miso268) and none has an admissible lever this lane can arm (§6).

## 2. The mechanism

`ScenarioConfig.coal_fuel_inventory_plant_grain` (default `False`, cache-key dropped at its
default, TIER 1). Requires `coal_fuel_inventory` (raises otherwise), so it inherits the MISO gate
and the backcast-only guard.

* **One annual row per coal yard**: Σ HR·P over the yard's generators ≤ (Dec(Y-1) stock + mean
  Y-2..Y-1 receipts) × the yard's own prior-years heat content.
* **Yard** = a plant, or a shared-storage entity in `coal-shared-storage-crosswalk.csv` pooled with
  every modelled plant it serves (e.g. Belle River + St Clair + entity 8841 are one yard).
* **No substitute**: a yard with no stock or receipt record in the source window gets no row.
* **Refinement, not a second mechanism** (rule 19): the per-yard budgets sum to the pooled annual
  identity (2,792 vs 2,782 M MMBtu in 2022; the gap is heat content per yard vs pooled). The
  pooled MONTHLY rows are unchanged and remain the timing limb.
* **Rule 13**: same measured inputs as the pooled budget, all predating Y. Forward story unchanged:
  a forecast year's per-yard opening stock is the model's own carried per-yard inventory.
* **ZERO free parameters. DOF ledger: 0 added.**

## 3. G-DRIFT vs keeper `git_sha 3ea64fa5` (rule 29(b))

`git diff 3ea64fa5 <this SHA> -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`.
Three commits on `main` plus this lane's own change:

| hunk | class | reason |
|---|---|---|
| `demand_balance_screen` (pjm-h19): scenarios field, cache-key, `run_calibration.run_year` + `runner._hindcast_measured_demand` pass-through, `data/eia930/demand.py` | INERT | ScenarioConfig flag, default off, absent from the keeper's recipe |
| `ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE` (constants, `run_calibration_full._eia860_current_ba_recoded`), `solve_surface_declared` SOCO row | INERT | SOCO-only branch |
| `benchmark_semantics.EIA930_GAS_FOLD_REFUTED` | INERT | SOCO-only; benchmark side, not solve |
| this lane: `coal_fuel_inventory.build_coal_plant_budget`, `coal_plant_*` kwargs (spec, lp, rows), `run_calibration` call site, scenarios field | the ARM | UNSET/None when off; byte-identical off by construction |

**All non-arm hunks INERT ⇒ form 4 is valid; the keeper's committed bundle is the control.**

## 4. Predictions (fixed before any shard)

Static excess is an **upper bound**: the LP can move coal to yards with slack. Expected net coal
removal is 40–100 % of the static excess.

| year | Δ coal total (TWh) | notes |
|---|---|---|
| 2020 | −1.1 to −2.6 | small |
| 2021 | −4.7 to −11.8 | |
| 2022 | −7.6 to −19.0 | the charter object |
| 2023 | −0.9 to −2.3 | small |
| 2024 | −0.2 to −0.5 | ≈ inert |
| 2025 | −3.8 to −9.4 | |

### 4.1 Class split of the static excess, and cell predictions

Static excess by the keeper's scored class per unit (TWh-equiv; slack = headroom at yards whose
own row does not bind):

| year | COAL_PRB | COAL_BIT | COAL_LIGNITE | slack elsewhere |
|---|---:|---:|---:|---:|
| 2020 | 1.45 | 1.14 | 0 | 138.0 |
| 2021 | 8.69 | 1.82 | 1.18 | 56.9 |
| 2022 | **15.32** | 3.60 | 0 | 30.5 |
| 2023 | 1.55 | 0.58 | 0.19 | 79.7 |
| 2024 | 0.05 | 0.44 | 0 | 102.9 |
| 2025 | 6.03 | 3.34 | 0 | 47.8 |

Cell predictions (central = 60 % of static; range 40–100 %):

| cell | keeper | predicted arm | band |
|---|---:|---|---|
| C1 2022 COAL_PRB | +10.04 FAIL | **+0.9 (−5.3 to +3.9) → PASS** | ±8 |
| C1 2022 CC_REGULAR | −8.99 FAIL | **≈ −3 (−7 to +2) → PASS** | ±8 |
| C1 2022 COAL_BIT | +1.68 | ≈ −0.5 | ±8 |
| C1 2021 COAL_PRB | −0.10 | **≈ −5.3 (−8.8 to −3.6); FAIL possible** | ±8 |
| C1 2021 COAL_BIT | −3.40 | ≈ −4.5 | ±8 |
| C1 2020 COAL_BIT | −6.79 | ≈ −7.5; FAIL possible | ±8 |
| C3a 2022 | −10.2 % FAIL | toward zero; PASS likely | ±10 % |
| C3a 2020 | +12.8 % FAIL | +12.8 to +13.5 %, stays FAIL | ±10 % |
| C3b 2021 | 0.307 FAIL | ≈ 0.30, stays FAIL | ≤0.20 |
| train 2023–2025 | CALIBRATED | CALIBRATED (2025 C1 is SKIPPED; C2 coal family moves ≤ 5.6 TWh) | |

**Directions:** coal down, gas (CC_REGULAR first) up, mean LMP up in every year the rows bind
(the yard duals become coal's opportunity cost). C3a 2022 (−10.2 %) moves toward zero; C3a 2020
(+12.8 %) moves slightly **away** (small); C3b 2021 ≈ unchanged (Feb and Oct–Nov are not coal
objects).

**Cells at risk, named now:** C1 2021 COAL_BIT (−3.40) and COAL_PRB (−0.10); C1 2023 COAL_BIT
(−2.59); C2 2025 coal family; C3a 2020. A move of any of these out of band is reported at full
magnitude and does not retract the arm (rules 1/14).

## 5. Decision rule (fixed now)

Recommend promotion iff all structural gates hold:

* **S-1** single delta: every per-year `run_config` differs from the keeper's only in
  `coal_fuel_inventory_plant_grain`.
* **S-2** the rows are built and honoured: the solve log's `coal per-yard budget` line is present
  in every year, and no yard's annual coal input exceeds its budget (checked from the leg's
  per-unit dispatch).
* **S-3** slack = dump = 0 in every year.
* **S-4** G-DRIFT all INERT (§3).

Gates are reported both ways and decide nothing (owner's standing standard: *"If structural
integrity improves but gates regress that may still be a keeper"*). **Exception, escalate rather
than recommend:** if the train tier (2023–2025) determination leaves CALIBRATED.

The promotion decision is the owner's (rule 31).
