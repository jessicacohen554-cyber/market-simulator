# PRECOMMIT — PJM PRICE-TAIL: the backcast tail is **fuel in level and season, merit order in the tail**, and the fuel half is COMMON-MODE — it cannot reach the E&AS operand

**Lane:** PJM PRICE-TAIL. **Branch:** `claude/pjm-price-tail-backcast-h9dzmh`, off `origin/main` `b054988c`.
**DATA PROFILE: pjm.**
**Pushed BEFORE any LP** (rule 29 `[R-SCREEN]`) — and **no LP is spent by this lane at all**:
phase 0 killed both candidate arms. Nothing is armed by this commit; it adds no
solve-path code. Every number below is read from committed artifacts and committed raw data.

Predecessor merged first as instructed: `3dd46efb`
(`claude/pjm-rubric-residual-composition-xhw1kj`) is an ancestor of `origin/main` — the FINDING,
the screen-grade sidecar and the PJM matrix shard update are all on `main`. Nothing was owed.

---

## 0. The question, and the answer in one paragraph

The lane's only question is **what puts the tail in PJM's backcast price surface**. It is the
**fuel-price time series**, and that answer is decisive for the *surface* and **fatal for the
successor arm the predecessor lane routed to it**. The backcast prices gas hour by hour off the
daily Henry Hub series plus monthly/zonal basis (`gas_daily_shape` / `gas_monthly_actuals` /
`gas_plant_monthly_fuel_pricing` / `pjm_zonal_gas_basis`, all `True`); the T1-H forecast lane
carries all four `False` and prices every one of its 8,760 hours at the single annual scalar
`hindcast_realized[2021] + PJM basis = 3.91 + 0.67 = 4.58 $/MMBtu`. The monthly mean price
correlates **0.953** with monthly Henry Hub and only **0.245** with monthly load; the implied
market heat rate (price ÷ delivered gas) is nearly constant across all twelve months
(mean 10.79, **CV 0.082**); the **24 highest-price hours of the entire year are all of
2021-02-17**, the year's single highest gas day (`henry_hub_daily.csv` = **$23.86/MMBtu**), at
100–117 GW of load, while the **149.6 GW annual peak-load hour reaches only $145.94** and ranks
28th of 8,760 by price. But the gas
tail is a **common-mode multiplier, not a merit-order rotation**:
`corr(implied marginal heat rate, delivered gas) = −0.024`, and on the Uri day the market heat
rate is **7.73**, *below* the annual mean of 9.17. It lifts price and cost together. That is why
the fuel axis **cannot** supply the E&AS the failing set needs — and why the predecessor's
`$40.656`/MW-day supply-side number is an artifact, corrected in §3 below.

---

## 1. Phase 0 (zero LP) — the two surfaces, differenced on every remaining axis

Both configs on disk; `run_config.json` `scenario_config` blocks differ in **97 of 818 fields**.
Taking the brief's five named axes in turn.

### A. `scarcity_pricing_enabled` — **ELIMINATED, by inspection**

| | backcast `pjm169_tp2022_2021_f2arm` | hindcast `pjm-2021-2025-realized-t1h-d75rarm` |
|---|---|---|
| `scarcity_pricing_enabled` | **False** | **True** |
| annual max price | **213.46** $/MWh | **52.77** $/MWh |

The flag is **ON in the surface WITHOUT the tail and OFF in the surface WITH it**. It cannot be
the tail's source. (`scarcity_price_overlay` is `False` in both; every `ordc_*` field is
byte-identical in both, `ordc_voll` 5000.0, `voll` 5000.0.)

### B. Scarcity of any kind — **ELIMINATED, by measurement**

Over all 8,760 hours of the backcast 2021 P1 solve: hours with `slack > 0.01` = **0**
(total slack **0.00 MWh**); hours with `dump > 0.01` = **0**. VOLL never binds anywhere in the
surface that carries the tail. **The tail is a merit-order outcome, not a shortage outcome.**

### C. The demand basis — **ELIMINATED, byte-identically**

The hindcast's `evolution_2021.json` records `peak_demand_mw` = **149,590.0**. The backcast
2021 LP's own demand array maxes at **149,590.0 MW** (sum over its nine zones). *The same
number.* Post-D76 the hindcast's screen peak **is** the array its LP dispatches, and it is the
array the backcast dispatches too. Same ISO, same year, same load — and a 4× difference in the
annual maximum price.

### D. `mode` and the fleet basis — **not independently separable, and not needed**

They differ (`backcast`/`forecast`, `plant_level_fleet` True/False, `eia860_vintage_year`
None/2020, and 90-odd companion flags). This lane does **not** claim to have separated them,
and does not need to: axis E below is measured directly and is sufficient to reproduce the
tail's magnitude, its season and its single largest day.

### E. The fuel-price series — **THIS IS THE TAIL**

Delivered gas, the two lanes:

| | backcast | hindcast |
|---|---|---|
| `gas_price_path` | `mid` (superseded — see below) | `hindcast_realized` |
| `gas_price_override` | 6.45 | None |
| `gas_monthly_actuals` / `gas_daily_shape` | **True / True** | **False / False** |
| `gas_plant_monthly_fuel_pricing` / `pjm_zonal_gas_basis` | **True / True** | **False / False** |
| delivered gas seen by the LP | **3.10 → 24.53 $/MMBtu, hourly** | **4.58 $/MMBtu, all 8,760 hours** |

`hindcast_realized[2021] = 3.91` is the **annual mean of the very daily series the backcast
reads hourly** (`henry_hub_daily.csv` 2021 mean = **3.894**, n=251 trading days). *Same data;
one lane collapsed it to a scalar.*

The annual `gas_price_override = 6.45` is **superseded in practice** by the monthly actuals, and
the price surface proves it rather than the code being taken on trust: regressed against
*monthly* Henry Hub the implied market heat rate is flat (CV 0.082); against a flat 6.45 it
would have to swing by the full monthly gas range.

| month | mean price $/MWh | mean load MW | Henry Hub $/MMBtu | implied market HR |
|---|---|---|---|---|
| 1 | 32.94 | 96,438 | 2.71 | 12.15 |
| 2 | 50.92 | 99,847 | 5.35 | 9.52 |
| 3 | 29.28 | 83,565 | 2.62 | 11.17 |
| 4 | 28.69 | 77,492 | 2.66 | 10.79 |
| 5 | 30.95 | 80,118 | 2.91 | 10.64 |
| 6 | 36.74 | 97,940 | 3.26 | 11.27 |
| 7 | 40.80 | 104,019 | 3.84 | 10.62 |
| 8 | 48.13 | 106,794 | 4.07 | 11.83 |
| 9 | 47.89 | 89,974 | 5.16 | 9.28 |
| 10 | 53.96 | 80,188 | 5.51 | 9.79 |
| 11 | 55.97 | 85,999 | 5.05 | 11.08 |
| 12 | 42.61 | 88,751 | 3.76 | 11.33 |

**corr(monthly price, Henry Hub) = 0.9531. corr(monthly price, load) = 0.2449.**
January carries 96.4 GW of mean load and **zero** hours above the hindcast's annual max;
October and November carry 80–86 GW and **393 / 405** such hours. The tail follows the fuel,
not the load.

**The single largest day.** The 24 highest-price hours of backcast 2021 are, in order, every
hour of **2021-02-17** (peak $209.07 at 07h, on 116.7 GW). `henry_hub_daily.csv`:
2021-02-12 $6.12 → **2021-02-16 $11.32 → 2021-02-17 $23.86** → 2021-02-18 $8.56. The 25th hour
is 08-25 15h at $155.93 (on 144.7 GW) — the highest price anywhere outside February. The year's
actual **peak-load** hour, 08-24 16h at **149,590 MW**, prices at only **$145.94** and ranks **28th**
of 8,760, behind every one of the 24 Feb-17 hours. Delivered gas on Feb-17 is
$24.53/MMBtu; $209.07 ÷ $24.53 = an **8.52** MMBtu/MWh marginal heat rate — an ordinary CC, at
an extraordinary fuel price.

---

## 2. THE FUEL AXIS IS COMMON-MODE — the structural result that kills the arm it suggests

The obvious successor to §1 is "give the forecast lane the gas shape." **Phase 0 kills it, at
zero LP, on the mechanism's own arithmetic.** A fuel-price change multiplies price *and*
marginal cost together; it only reaches an out-of-merit unit if high gas hours are also high
**market-heat-rate** hours. They are not:

```
corr(implied marginal heat rate, delivered gas)  =  -0.0235
corr(price,                      delivered gas)  =  +0.8304
```

| gas quintile | mean delivered gas | mean price | **mean implied market HR** |
|---|---|---|---|
| 0 | 3.278 | 29.876 | 9.106 |
| 1 | 3.621 | 32.392 | 8.943 |
| 2 | 4.294 | 40.547 | 9.426 |
| 3 | 5.052 | 47.424 | 9.420 |
| 4 | 6.509 | 58.080 | 8.959 |

The market heat rate is **flat at ~8.9–9.4 across the entire gas range**, and on the Uri day it
is **7.73** against an annual mean of **9.17** — the largest fuel event of the year *lowers* it.
Gas is a scalar on the whole surface. It does not rotate the merit order, so it cannot move a
unit whose heat rate sits above the marginal one into merit.

---

## 3. THE PREDECESSOR'S `$40.656`/MW-day IS A FUEL-BASIS ARTIFACT — corrected, against interest

`PRECOMMIT-pjm-eas-operand-2026-09-07.md` §1D priced the 103 decided gas_st units against the
committed backcast 2021 surface and reported **$119,972,990 = $40.656 per accredited MW-day**,
"four orders of magnitude" above the hindcast's ~$0.004. That number is what motivated the
reserve arm, and it is what the refuted point prediction assumed would arrive.

**This lane reproduces it exactly — `$119,972,990`, `40.656` — and then corrects it.** The
instrument credits each unit with the **backcast's gas-driven prices** while charging it the
**hindcast's flat-gas marginal cost** (`mc_mean_usd_mwh`, computed at 4.58 $/MMBtu). The two
sides are on different fuel bases. Charging the same gas series that produced the prices —
`mc_i(t) = hr_i × gas_t + vom`, `hr_i = (mc_mean_i − vom)/4.58`, `vom = 4.0 $/MWh`
(gas_st, NREL ATB 2024, `constants.VOM`) — gives:

| basis | total E&AS | $/accredited MW-day |
|---|---|---|
| mc **held flat** (phase-0 D as published) | $119,972,990 | **40.656** |
| mc proportional to gas (vom 0) | $34,405,506 | 11.659 |
| **mc = hr×gas + vom(4.0)** | **$34,985,277** | **11.856** |

**VOM sensitivity** (the only free choice in the correction), showing the result is not an
artifact of it:

| vom $/MWh | 0.0 | 2.0 | 3.0 | **4.0** | 5.0 | 6.0 | 8.0 |
|---|---|---|---|---|---|---|---|
| $/acc MW-day | 11.659 | 11.737 | 11.792 | **11.856** | 11.930 | 12.013 | 12.213 |

Phase-0 D **overstates the fuel axis's supply by 3.43×**, and the corrected value lands
**below phase-0 C's own measured $12.7/MW-day threshold** — the level under which the 2022
uncleared set is *exactly* unchanged — across the entire plausible VOM range. Stated plainly:
**on the predecessor's own instrument, corrected, the fuel axis cannot move the failing set.**

Two honest limits, stated before the number is used, as the predecessor stated its own:
this is the **backcast** surface (backcast fleet, offer curves, congestion and demand), so it
bounds an order of magnitude, not an armed value; and **11.856 against 12.700 is only 7 %
below the line** — close enough that it is reported as a *failed pre-solve gate*, never as a
proof of inertness.

---

## 4. The second candidate — the OFFER CURVE — and how it was tested

If the *level* and *season* are fuel, the remaining candidate for the part of the tail that puts
an expensive unit **in merit** is the dispersion of the market heat rate. The two surfaces do
differ in it:

| | backcast 2021 | hindcast 2021 |
|---|---|---|
| implied market HR, mean | 9.168 | 8.069 (= 36.959 / 4.58) |
| implied market HR, **max** | **33.821** | **11.522** (= 52.7715 / 4.58) |
| max / mean | 3.69 | 1.43 |
| hours with implied HR > 10.30 (the *cheapest* failing unit's HR) | 1,417 (16.2 %) | ≤ a handful, by construction of the max |

The 103 failing units have heat rates `(mc_mean − 4.0)/4.58` = **10.30 / 10.30 / 11.33 / 11.76 /
11.84** (min/p25/med/p75/max), so the hindcast's ceiling of 11.52 sits below the upper half of
that cohort.

**The mechanism candidate is `offer_curve_by_group`, and the forecast lane has none.** The
backcast carries a full band structure (`CC_REGULAR` peak **5.0**, `CT_PEAKER` peak **4.0**,
`ST_GAS` peak **3.024**); the hindcast carries **`{}`**, and
`data/offer_curves.py::_offer_curve_for_group` then returns `None` for *every* group
(`curves = getattr(...) or {}`; every branch ends `curves.get(group) or None`), so every class
falls to the legacy CSV heat-rate path with no band markup. This is **not a decision to run
neutral bands**: the construction lives in `pipeline/backcast_config.py`, which a
`mode="forecast"` run never enters, and `scripts/run_capacity_hindcast.py::build_config` builds
`ScenarioConfig(...)` without ever naming the field, so it takes its `default_factory=dict`. The
shared per-ISO base curve that exists for exactly this purpose —
`pipeline/offer_curve_base/base_offer_curve_by_group(iso)`, generic bands overlaid with
`PJM_BASE_OFFER_CURVE_DELTAS` (`CT_PEAKER` peak **13.0**) — has **zero callers in `src/` or
`scripts/`**; only a parity test imports it.

### 4.1 ORDERING, STATED PLAINLY AND AGAINST INTEREST

The gate below (**G-OA**) was written into this file *before* it was run, but **this file had not
yet been pushed** when it ran. It is therefore reported as an **exploratory** zero-LP gate, **not
a pre-registration**, and no weight is placed on it as one. It is recorded verbatim, with its
outcome, because it **failed to discriminate** and because a lane that writes a gate and then
runs it owes the reader that fact. No LP was spent under it, or at all — see §5.

**G-OA as written:** *the maximum offer across the PJM thermal stack at the hindcast's flat
4.58 $/MMBtu, and the implied market-heat-rate ceiling it supports. STOP if the base curve's
ceiling is below 11.84* — the most expensive failing unit's heat rate.

**G-OA's outcome: BOTH ARMS CLEAR, so it killed nothing — and it refuted this section's own
premise.** Measured on `build_base_fleet` for PJM 2021 under the registered T1-H recipe with
exactly one field changed:

| | control `{}` | arm `base_offer_curve_by_group("PJM")` |
|---|---|---|
| thermal LP units | 1,302 | 2,525 |
| thermal MW | 134,555.6 | 134,520.9 |
| **max offer** $/MWh @ 4.58 | **141.470** | **1,604.939** |
| implied market-HR **ceiling** | **30.889** | 350.423 |
| G-OA (STOP below 11.84) | CLEARS | CLEARS |

**The control's own stack already reaches $141.47 — an implied ceiling of 30.9, far above the
11.84 the gate asked for.** So the hindcast's realized $52.77 maximum is **not** a stack-top
limit: the stack goes to $141 and is simply never climbed that far. The premise of this section
as first drafted — that `offer_curve_by_group = {}` is what caps the hindcast price — **is
false**, and the gate that was supposed to test the arm instead falsified the hypothesis behind
it. That is recorded as this lane's own error, corrected in the open.

### 4.2 The measurement that DOES discriminate — and it kills the arm

Because G-OA did not discriminate, the same two stacks were differenced **per fuel class**, which
asks the question that actually matters: does the base curve move the *failing cohort* toward the
margin or away from it? MW-weighted offer percentiles at 4.58 $/MMBtu:

| fuel | MW | control p50 | **arm p50** | control p90 | arm p90 | control max | arm max |
|---|---|---|---|---|---|---|---|
| coal | 35,433.4 | 57.08 | **53.87** | 65.20 | 64.23 | 114.69 | 130.15 |
| gas_cc | 58,818.1 | 35.55 | **40.26** | 41.62 | 57.64 | 107.59 | 153.83 |
| **gas_st** (the failing cohort's class) | 9,490.3 | 64.02 | **72.34** | 73.62 | 226.19 | 93.99 | 332.68 |
| gas_ct | 26,389.4 | 56.20 | **83.13** | 69.26 | 129.42 | 141.47 | 1,604.94 |
| oil | 4,424.4 | 66.33 | 66.33 | 94.13 | 94.13 | 135.76 | 135.76 |

Median offer move: **coal −5.6 %, gas_cc +13.2 %, gas_st +13.0 %, gas_ct +47.9 %.**

**The base offer curve makes the failing cohort MORE expensive, not less.** `gas_st`'s median
offer rises 13.0 % (64.02 → 72.34) and its p90 rises from 73.62 to 226.19, while **coal — the
class PJM under-retires — gets 5.6 % CHEAPER**. The marginal fuels move by less than gas_st does,
so the cohort's position relative to the margin gets *worse*. The arm pushes gas_st further out
of merit, which is the opposite of what the operand needs; and the cumulative supply curve
confirms the direction is common-mode again (thermal MW available below $60 falls 101.2 → 88.8 GW,
i.e. the whole stack lifts together).

---

## 5. NO ARM IS DECLARED AND NO LP WILL BE SPENT BY THIS LANE

Rule 29's phase 0 did exactly what it exists for: it **killed both candidate arms for zero LP
minutes**, on each mechanism's own arithmetic and never on a band or a residual.

1. **Fuel shape / level — killed by §2–§3.** The axis is common-mode
   (`corr(implied market HR, gas) = −0.024`), and the predecessor's supply-side number, corrected
   for its fuel-basis mismatch, is **11.856 $/acc MW-day against phase-0 C's own 12.700
   threshold**, across the whole plausible VOM range.
2. **Offer curve — killed by §4.2.** It raises the failing cohort's own offers 13.0 % while
   making coal 5.6 % cheaper, and the control stack was never the binding ceiling anyway.

Per rule 29 a screen **"may kill an arm; it may never promote one"** — and neither may a phase-0
instrument. Nothing here promotes anything, no bundle is produced, no cache key is declared, and
**the PJM keeper is unchanged**. Because no LP runs, the rule-29(b) **G-DRIFT re-audit is moot**
and is not claimed: form 4 differencing against the registered `pjm-t1h`
(`fb16fda2ddb0a94a`) was used only to read committed numbers, never to license a solve.

### The screen year, recorded for a successor rather than used

Had an arm survived, the screen year is **2021** — the only solved year in the window that
carries the object (`solve_counts` `P0 1 / P1 1` for 2021; `P0 0 / P1 0` for 2022, a **bridged**
year reading 2021's `prior_results`), with the entire gas_st over-exit being the 2022 decision
made off that 2021 surface. `--start-year 2021 --end-year 2022` is one solved year. Any such
bundle would be a throwaway probe under rule 29(c), and any key would be computed **on the
2021–2022 window actually solved**, per the predecessor's
`ADDENDUM-pjm-eas-key-window-2026-09-07.md`.

---

## 6. THE OWNER-FACING QUESTION THIS LANE RAISES AND DOES NOT DECIDE

`scripts/run_capacity_hindcast.py::build_config` never sets `offer_curve_by_group`, so **every
PJM forecast and hindcast run dispatches on flat physical heat rates with no thermal offer-curve
band structure at all**, while PJM's calibrated backcast keeper dispatches on a full band set.
The omission is in the **shared** `build_config`, so it plausibly affects **every ISO's** forecast
lane, not only PJM's. `base_offer_curve_by_group()` — the shared per-ISO base curve built for
exactly this purpose — has **zero callers**.

This is the **same class of lane inconsistency** as the reserve-field gap the predecessor lane
routed to the owner, and **strictly larger**: it is the mechanism that shapes the price
distribution, and it touches every forecast run's cache key. It is raised here as a **consistency
question**, exactly as the brief directs, and is deliberately **not folded into a residual fix** —
the more so because §4.2 shows arming it would move the composition residual the *wrong* way, so
any decision to arm it must rest on rule 1 `[R-STRUCT]` structural grounds and an owner ruling,
never on the fit. The candidate values are themselves governed: PJM's `_PJM_OFFER_CURVE` is
calibrated on PJM's backcast residual, so transplanting it into the forecast lane is a governance
act under rule 1's conditioned carve-out; the un-calibrated base curve is a different and more
defensible candidate. **Choosing between them is an owner decision, not this lane's.**

---

## 7. Rule 28 — the matrix

`energy_reserve_coopt` PJM `fc: "R"` (the predecessor's, on `main`) — **not re-tested**; §2
supplies an *independent* structural reason it could not have worked, recorded as corroboration.
`ordc_scarcity_overlay` stays **G**. `economic_retirement_screen` stays **R**. Q55 / Q56 / the
sector gate are not re-opened. **`offer_curve_by_group` IS tested by this lane** (zero-LP
offer-array delta, §4) and its PJM cell gains an explicit forecast-lane posture and citation in
this session, per duty (b).

## 8. Pre-existing RED on `main` — carried forward, not re-verified, not repaired

The brief lists seven, verified by the predecessor against clean `origin/main` on 2026-09-07:
FR-22 parity (3 FAILs, `miso_seam_neighbour_{anchored_ladder,hourly_ladder,hourly_spp}`);
`test_cache_solve_surface` (2, `NUCLEAR_MONTHLY_CF_BY_YEAR`); `test_caiso_st_gas_peak_measured`
(1.154 != 1.166); `audit_keepers` S1 on `status/ERCOT.js` **and** `status/PJM.js`;
`CAISO_dam_hourly_2022.csv` missing `MGHG` (blocks the `lmp` datatype for every ISO — PJM has no
import node, so not on this lane's path); `emissions-unit-annual` OOM at 15 GB;
`run_capacity_hindcast.py --help` `ValueError` on an unescaped `%`. **None repaired here.**

## 9. Environment

Fresh container. `pip install -e . --no-deps`, then the control's recorded pins —
`highspy==1.14.0 pandas==3.0.3 pyarrow==24.0.0 pydantic==2.13.4 numpy==2.4.6 scipy==1.17.1` —
plus `tzdata` (the container lacks the legacy `US/*` aliases, used on the solve path by
`results/scarcity.py` and `data/eia930/envelopes.py`) and `openpyxl`. `data/raw` hydrated;
`data/clean` rebuilt for `fleet` / `reference` / `egrid` only, which is all the §4 offer-array
instrument reads. No LP was run, so `highspy` was never invoked.
