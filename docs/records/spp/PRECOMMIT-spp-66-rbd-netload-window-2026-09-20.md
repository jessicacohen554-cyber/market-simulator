# PRECOMMIT / PHASE-0 FINDING — SPP-66 successor card **R-bd**: the commitment-floor WINDOW is ranked on system LOAD; SPP's own measured fleet says NET LOAD.

**Lane** SPP-66 (continuation, after R-ba was falsified — `FINDING-spp-66-2026-09-20.md`) ·
**Pin** `d7d1e0a2edfe39901e1532d634a73e3f718959e1` · **Control** keeper 13
`2026-09-20-spp-51-coal-sync` / `results/calibration/spp51_syncfloor_span`, **differenced from its
committed bundle** (rule 29 `[R-SCREEN]` (b) form 4) · **ZERO LP RAN.** No shard, no bundle, no
config change, no code change, no registration. Nothing deleted (rule 31 `[R-RETAIN]`).

**PHASE-0 VERDICT: R-bd IS A CONFIRMED CONSTRUCTION DEFECT under rule 17 `[R-FLOOR-WINDOW]`, on
SPP's own measured driver evidence and not on any residual.** It is **NOT implemented and NOT
solved** in this session — §6 says why, and §4-§5 are the design a successor executes.

---

## 1. The defect, in the code

`src/market_sim/data/fleet/arrays.py:2877-2906`. A coal cycler whose measured `online_frac` is below
`_COAL_SYNC_FORCE_ALL` carries its synchronization floor in the **top-k hours by system load**:

```python
load_rank = np.argsort(-sys_load, kind="stable")   # sys_load = load_shape
...
k = int(round(frac * hours)); hrs = load_rank[:k]
min_gen[g_idx, hrs] = np.maximum(min_gen[g_idx, hrs], pmin_mw)
```

The code comment states the intent in its own words — *"held only in the top-`online_frac` fraction
of hours by **system load** … so the floor lands where the cycler actually runs (the load peaks) and
relaxes in the cheap overnight hours it would real-world shut for."* **That premise is false in a
30-40 %-VRE ISO**, and SPP is one: measured VRE averages 11.8-12.9 GW against a 32.5-34.5 GW load.

## 2. Rule 17's own test, answered: the class's measured behaviour tracks NET load, not load.

EIA-930 `SWPP_fueltype` hourly actuals, three keeper years (trap (f)'s one corrupt 2023 WND hour of
3,589,445 MWh detected and interpolated; trap (e)'s 8,784-hour 2024 handled by computing each side on
its own calendar and never cross-indexing):

| year | corr(measured COAL, **system load**) | corr(measured COAL, **net load**) | corr(measured NG, load) | corr(measured NG, **net**) |
|---|---|---|---|---|
| 2023 | +0.7158 | **+0.9484** | +0.7369 | **+0.9627** |
| 2024 | +0.6605 | **+0.9479** | +0.7289 | **+0.9644** |
| 2025 | +0.6129 | **+0.9319** | +0.6640 | **+0.9530** |

The measured decile profile is monotone under net load and **not** under system load — 2023 coal by
system-load decile runs 15,572 / 12,527 / 9,921 / 8,544 / 8,161 / 7,571 / 7,190 / 7,188 / 6,389 /
**6,443 MW** (it turns back up at the bottom); by net-load decile it is 16,169 / 13,331 / 11,376 /
10,038 / 9,087 / 7,997 / 6,983 / 5,841 / 4,861 / 3,822, monotone throughout.

## 3. THE SHARP TEST — and it is decisive in every year at every k.

Partition the year by whether an hour is in the top-k by **load** and by **net load**, then read the
**measured** coal fleet in each cell. *Actuals only: no model quantity enters this table.*

| year | k | hours the shipped window **HOLDS** but net-ranking would release (`LOAD only`) | hours the shipped window **RELEASES** but net-ranking would hold (`NET only`) | n(`NET only`) | **difference** |
|---|---|---|---|---|---|
| 2023 | 0.40 | 7,360 MW | **10,738 MW** | 1,128 | **+3,378** |
| 2023 | 0.50 | 6,448 | **10,003** | 1,300 | **+3,556** |
| 2023 | 0.60 | 5,717 | **9,327** | 1,384 | **+3,610** |
| 2024 | 0.40 | 7,035 | **10,594** | 1,132 | **+3,559** |
| 2024 | 0.50 | 6,266 | **9,614** | 1,272 | **+3,348** |
| 2024 | 0.60 | 5,417 | **8,807** | 1,303 | **+3,390** |
| 2025 | 0.40 | 9,227 | **12,524** | 1,188 | **+3,298** |
| 2025 | 0.50 | 7,878 | **11,751** | 1,352 | **+3,872** |
| 2025 | 0.60 | 6,954 | **10,686** | 1,357 | **+3,731** |

**The shipped window holds the floor in the hours the real fleet runs LESS coal and releases it in
the hours the real fleet runs MORE coal — by +3.3 to +3.9 GW, in all three years, at every k tested
(0.25 / 0.40 / 0.50 / 0.60 / 0.75).** Rule 17 `[R-FLOOR-WINDOW]`: *"A floor binding in hours its own
driver evidence says the class is offline is a bug by definition, whatever it does to the residual."*
The converse case is the same bug, and this is it. 26-30 % of the top-k hour set differs between the
two rankings at the k values the SPP cyclers actually use.

## 4. Where the symptom shows, measured on the same statistics

The model's coal already tracks net load reasonably (dispatch economics does most of the work); the
whole discrepancy is concentrated in the **bottom net-load deciles**, exactly where the load-ranked
window releases the floor:

| year | metric | MODEL | ACTUAL |
|---|---|---|---|
| 2023 | coal mean MW, net-load decile **10** (lowest) | **2,070** | **3,822** |
| 2023 | decile 9 | 4,092 | 4,861 |
| 2023 | decile 1 (highest) | 15,154 | 16,169 |
| 2024 | decile 10 | **1,945** | **3,729** |
| 2025 | decile 10 | **2,301** | **4,361** |

The top deciles agree within a few percent; the bottom decile is **short by 46-47 % in every year**.
On the robust form of the charter's headline statistic:

| year | model p1/max | actual p1/max | model min/max | actual min/max |
|---|---|---|---|---|
| 2023 | **5.24 %** | **11.47 %** | 1.49 % | 7.58 % |
| 2024 | **5.70 %** | **16.01 %** | 1.00 % | 0.00 % |
| 2025 | **4.50 %** | **16.38 %** | 0.15 % | 10.96 % |

*Correction to the charter, stated rather than buried:* the charter quotes "0.15-2.53 % of annual max
against a real 8.1-17.5 %". The model side reproduces (0.15 % in 2025 exactly), but **`min/max` is
not a robust statistic on the actual side** — EIA-930 records a genuine 0 MW coal hour in 2024, which
makes the real ratio 0.00 % and would read as the model being *right*. **Use `p1/max`**, which is
stable and tells the same story more strongly: the model's 1st-percentile coal is about **one third**
of the real fleet's, in all three years.

## 5. THE DESIGN — validated against the code, ready to implement. Zero free parameters.

**The net-load construction already exists in this repo, verbatim, at six sites in `runner.py`**
(3008-3009, 3047-3048, 3066-3067, 3288-3289, 3784-3785):

```python
demand.sum(axis=0) - (wind_cap[:, None] * wind_cf).sum(axis=0) - (solar_cap[:, None] * solar_cf).sum(axis=0)
```

so nothing is invented and **no scalar is added** (rules 21 `[R-DOF]` / 24 `[R-REGISTRY]`).

- **Seam.** `runner.py:2757`, the `generators_to_fleet_arrays(...)` call that already passes
  `load_shape=year_base_demand.sum(axis=0)`. **Verified in scope at that line:** `wind_cf`,
  `solar_cf`, `wind_cap`, `solar_cap` and `year_base_demand` are all defined and current there
  (`wind_cf`/`solar_cf` at 1512-1519, re-bound for weather years at 2114; caps grown in place by
  2461-2462, i.e. before 2757). **`year_solar_cf` is NOT — it is first assigned at 3217**, so the
  seam must use plain `solar_cf`, which is exactly what three of the six existing sites do.
- **Plumbing.** One new keyword (`netload_shape`) threaded
  `generators_to_fleet_arrays` → `_compose_min_gen_floors` (signature at 2518, `load_shape` at 2528),
  and one `argsort` source swap at 2878-2882.
- **Gate.** One new default-`False` `ScenarioConfig` bool. **Default off is mandatory, not stylistic
  (rule 25 `[R-ISO-SCOPE]`):** census over all 19 committed `run_config.json` shows
  `coal_sync_srmc_tranche` is `True` in **PJM (3 configs) and SPP (2)**, so a defaulted-on change
  moves PJM's keeper.
- **Rule 13 `[R-MEASURED]` forward test — PASSES.** Net load is built from the **model's own** VRE
  capacity × CF, never from measured VRE output, so it regenerates for any forecast year off the
  evolved fleet and responds to changed conditions. (Building it from *measured* VRE output would
  import realized curtailment and would be inadmissible — do not.)

### Rule 19 `[R-ONE-MECH]` — the defect is in FOUR floors, and TWO of them are live on SPP's keeper

The identical `np.argsort(-sys_load)` window appears at `arrays.py` **2878** (coal sync, `coal_sync_any`),
**3012** (`cc_mustrun_per_plant` / **`st_gas_mustrun_per_plant`**), **3118**
(`st_gas_mustrun_p25_level`), **3195** (`ct_mustrun_per_plant`). On keeper 13 **two are armed**: the
coal-sync floor *and* `st_gas_mustrun_per_plant` (SPP-64's mechanism, D-2 16.4 % of class). §2 shows
measured SPP **gas** tracks net load even more tightly than coal (+0.963/+0.964/+0.953). **A successor
must decide scope explicitly and say so in its PRECOMMIT** — gating only the coal floor leaves the
identical defect in the ST_GAS floor on the same ISO in the same solve, which is hard to defend under
rule 19; gating all four widens the blast radius to PJM/MISO/NYISO floors. Recommendation: **one gate
on the shared ranking**, armed per-ISO, so one object moves.

### Pre-registered predictions (rule 1 `[R-STRUCT]` — written BEFORE any solve, never swept)

Sign and rough magnitude, to be scored honestly against the arm whatever it does:

1. **COAL_PRB / COAL_LIGNITE annual TWh: UP, small.** The window moves *when* the floor binds, not
   how much capacity it floors, so annual coal energy should move **< +1.5 TWh/yr**. A large move is
   a red flag that the gate is doing something other than re-windowing.
2. **Bottom net-load-decile coal: UP substantially**, toward the measured 3,822 / 3,729 / 4,361 MW
   from 2,070 / 1,945 / 2,301. This is the mechanism's own target and the statistic it should be
   judged on.
3. **`corr(model coal, net load)`: UP**, from +0.9246 / +0.8899 / +0.8933 toward the measured
   +0.9484 / +0.9479 / +0.9319.
4. **Top net-load-decile coal: essentially UNCHANGED** (already within a few percent). If decile 1
   moves materially the gate is mis-scoped.
5. **CT_PEAKER and CC_REGULAR: DOWN slightly** in the low-net-load hours (displaced), ST_GAS roughly
   unchanged — this card is **not** an ST_GAS repair and must not be sold as one.
6. **C3a mean LMP: DOWN slightly** (more must-run coal in the cheapest hours deepens the trough);
   **C3b shape: risk of getting WORSE**, since the model is already too dear per SPP-63. Pre-register
   this as the most likely adverse leg.
7. **C8 forced-energy share: UP for coal.** The coal D-2 forced share rises because the floor binds in
   *more valuable* hours; the 30 % cap is the live risk and must be reported at full magnitude
   (rule 20 `[R-FORCED-BUDGET]`). If coal goes over budget, the rule-20 conditional-pass route needs
   a cited `D4_WINDOWS` entry for the re-windowed mechanism in `scripts/legitimacy_diagnostics.py`,
   **regenerated in the same bundle** — plan for it up front rather than discovering it at scoring.

### Execution shape, if a successor proceeds

Rules 32 `[R-SHARD]` / 34 `[R-SHARD-PROMOTABLE]` / 36 `[R-YEAR-ISOLATION]`: **SPP carries SEVEN years
(2019-2025) across two registered runs**, so it is **seven shards, one per year**, each solving the
arm only (form 4 — keeper 13's committed bundle is the control; G-DRIFT must be re-audited at the new
pin first), each pushing its **full** bundle including `dispatch/<y>_P1.parquet` via a `.gitignore`
negation and a **plain** `git add`. Compose the 2023-2025 span and the 2019-2022 rung **separately**
(trap (n): they differ on `mid_vintage_exit_carry`), and stamp the rung to the keeper only after the
keeper's payload renders (trap (i)). Rule 28(c): a new `ScenarioConfig` field needs its matrix row
plus a cell line in **every** ISO shard in the same PR.

## 6. Why this session stops here

This lane was chartered on **R-ba**, which it falsified at zero LP. R-bd is the charter's own ranked
successor and this section is its phase 0, done properly. What it is **not** is implemented: R-bd
requires a code change on a **shared LP path** that PJM's keeper also arms, a new registered field
with a matrix row in nine shards, and seven year-isolated shards. Starting that on the back of
another card's phase 0 — without a PRECOMMIT the owner has seen, and with the rule-19 scope question
in §5 genuinely open between two defensible answers — would be spending seven solves on a design
decision nobody has ratified. The measurements above are the expensive part and they are now durable
on `main`'s history; the solve is cheap to schedule and should follow a scope ruling, not precede it.

**The scope question for the owner, stated plainly:** gate the coal-sync floor alone (narrow, leaves
the identical defect in SPP's own ST_GAS floor), or gate the shared `load_rank` for all four floors
and arm it per-ISO (rule-19 clean, wider blast radius)? **This lane recommends the shared gate.**
