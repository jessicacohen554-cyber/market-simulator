# FINDING — PJM PRICE-TAIL: the tail is the **FUEL PRICE SERIES**, it is **COMMON-MODE**, and phase 0 kills **both** candidate arms for **zero LP**. The predecessor's `$40.656`/MW-day supply number is a fuel-basis artifact; corrected it is **$11.856**, below the threshold that moves anything.

**Lane:** PJM PRICE-TAIL. **Branch:** `claude/pjm-price-tail-backcast-h9dzmh`. **DATA PROFILE: pjm.**
Pre-registration and the full measurement record: `PRECOMMIT-pjm-price-tail-2026-09-07.md`,
pushed in the same commit and **before any LP — of which this lane ran none**.
**NOTHING ARMS. No bundle was produced. The PJM keeper is unchanged.**

---

## 0. Verdict

**The question is answered and both arms it suggests are dead at zero LP.**

| | result |
|---|---|
| **What puts the tail in PJM's backcast price surface** | **the fuel-price time series** — its level (1.555× delivered gas) and, decisively, its intra-year **shape**. `corr(monthly price, monthly Henry Hub) = 0.9531`; `corr(monthly price, monthly load) = 0.2449`; implied market heat rate constant across all 12 months (mean 10.79, **CV 0.082**). |
| **Arm 1 — give the forecast lane the gas shape** | **KILLED.** The axis is **common-mode**: `corr(implied market HR, delivered gas) = −0.0235`. It lifts price and cost together and cannot move an out-of-merit unit into merit. |
| **Arm 2 — give the forecast lane an offer curve** | **KILLED.** The base curve raises the failing cohort's own median offer **+13.0 %** while making coal **−5.6 %** cheaper — it pushes gas_st *further* out of merit. And the control stack was never the binding ceiling. |
| **Predecessor's phase-0 D** | **CORRECTED.** `$40.656`/acc MW-day reproduced exactly, then corrected for a fuel-basis mismatch to **`$11.856`** — **below** phase-0 C's own `$12.700` threshold. |

---

## 1. The tail, named and measured

Zero slack and zero dump in all 8,760 hours of the backcast 2021 P1 solve — **the tail is a
merit-order outcome, not a shortage outcome**. `scarcity_pricing_enabled` is **True in the
surface WITHOUT the tail and False in the one WITH it**, so it is eliminated by inspection. The
demand basis is eliminated byte-identically: the hindcast's `peak_demand_mw` = **149,590.0 MW**
is the backcast LP's own demand max, to the tenth of an MW.

What remains is fuel. The backcast prices gas hour by hour (`gas_daily_shape`,
`gas_monthly_actuals`, `gas_plant_monthly_fuel_pricing`, `pjm_zonal_gas_basis` all `True`),
seeing **3.10 → 24.53 $/MMBtu**; the T1-H lane carries all four `False` and prices every hour at
**4.58 $/MMBtu** — which is the **annual mean of the very same daily series**
(`henry_hub_daily.csv` 2021 mean 3.894; `hindcast_realized[2021]` 3.91). *Same data, one lane
collapsed it to a scalar.*

**The signature.** The 24 highest-price hours of the entire backcast year are, in order, **every
hour of 2021-02-17** — the year's single highest gas day, `henry_hub_daily.csv` **$23.86/MMBtu**
— at 100–117 GW of load, while the year's **actual peak-load hour (08-24 16h, 149,590 MW) prices at
only $145.94 and ranks 28th of 8,760**, behind every one of those 24 hours; the highest price
anywhere outside February is $155.93. January carries
96.4 GW of mean load and **zero** hours above the hindcast's annual max; October and November
carry 80–86 GW and **393 / 405** such hours. Price follows fuel, not load. The peak hour
decomposes as market heat rate **8.52** × delivered gas **24.53** = **$209.07**: an ordinary CC at
an extraordinary fuel price. At flat gas that same hour would be a **$39** hour.

## 2. Why the tail is USELESS to the operand — the structural result

```
corr(implied market heat rate, delivered gas)  =  -0.0235
corr(price,                    delivered gas)  =  +0.8304
```

By gas quintile the implied market heat rate is **flat at 8.94 – 9.43** across the whole range
$3.28 → $6.51, and on the Uri day it is **7.73** against an annual mean of **9.17** — the largest
fuel event of the year *lowers* it. Gas is a scalar on the whole surface: it does not rotate the
merit order, so it cannot move a unit whose heat rate sits above the marginal one into merit.

## 3. The predecessor's supply-side number, corrected against interest

`PRECOMMIT-pjm-eas-operand-2026-09-07.md` §1D reported the 103 decided gas_st units earning
**$119,972,990 = $40.656 per accredited MW-day** on the committed backcast 2021 surface. That
number motivated the reserve arm and was the level the refuted point prediction assumed.

**This lane reproduces it exactly — `$119,972,990`, `40.656` — and then corrects it.** The
instrument credits each unit with the **backcast's gas-driven prices** while charging it the
**hindcast's flat-gas marginal cost** (`mc_mean_usd_mwh`, computed at 4.58 $/MMBtu): the two
sides sit on different fuel bases. Charging the same gas series that produced the prices,
`mc_i(t) = hr_i × gas_t + vom` with `hr_i = (mc_mean_i − vom)/4.58` and `vom = 4.0` (gas_st,
NREL ATB 2024, `constants.VOM`):

| basis | total E&AS | $/accredited MW-day |
|---|---|---|
| mc **held flat** (as published) | $119,972,990 | **40.656** |
| mc proportional to gas (vom 0) | $34,405,506 | 11.659 |
| **mc = hr×gas + vom(4.0)** | **$34,985,277** | **11.856** |

VOM sensitivity — the only free choice in the correction: **11.659 / 11.737 / 11.792 / 11.856 /
11.930 / 12.013 / 12.213** at vom = 0 / 2 / 3 / **4** / 5 / 6 / 8. Phase-0 D **overstates the
fuel axis's supply by 3.43×**, and the corrected value lands **below phase-0 C's own measured
$12.700/MW-day threshold** — the level under which the 2022 uncleared set is *exactly* unchanged
— across the entire plausible VOM range.

**Two honest limits, stated as the predecessor stated its own:** this is the *backcast* surface
(backcast fleet, offer curves, congestion, demand), so it bounds an order of magnitude, not an
armed value; and **11.856 against 12.700 is only 7 % below the line**. It is reported as a failed
pre-solve gate, never as a proof of inertness.

## 4. The offer curve — tested, and it moves the residual the WRONG WAY

`scripts/run_capacity_hindcast.py::build_config` never sets `offer_curve_by_group`, so it takes
its `default_factory=dict`; `_offer_curve_for_group` then returns `None` for **every** group and
every class falls to flat physical heat rates. The shared per-ISO base curve built for exactly
this purpose, `pipeline/offer_curve_base/base_offer_curve_by_group(iso)`, has **zero callers in
`src/` or `scripts/`**.

Measured at zero LP on `build_base_fleet` for PJM 2021 under the registered T1-H recipe, one
field changed (`docs/handoffs/pjmtail/phase0_offer_array_delta.py`):

| | control `{}` | arm `base_offer_curve_by_group("PJM")` |
|---|---|---|
| thermal LP units / MW | 1,302 / 134,555.6 | 2,525 / 134,520.9 |
| max offer $/MWh @ 4.58 | **141.470** | 1,604.939 |
| implied market-HR ceiling | **30.889** | 350.423 |

**First result, and it refutes this lane's own hypothesis:** the control stack **already reaches
$141.47** — a ceiling of 30.9 — so the hindcast's realized **$52.77 max is not a stack-top
limit**. The stack goes to $141 and is simply never climbed. `offer_curve_by_group = {}` is *not*
what caps the hindcast price. Recorded as this lane's error, corrected in the open; the gate
written to test the arm (**G-OA**, STOP below 11.84) **cleared for both arms and killed nothing**,
and it was written before it was run but in a file not yet pushed, so it is reported as
**exploratory, not a pre-registration**.

**Second result, which does discriminate.** MW-weighted offer percentiles at 4.58 $/MMBtu:

| fuel | MW | control p50 | arm p50 | move | control p90 | arm p90 |
|---|---|---|---|---|---|---|
| coal | 35,433.4 | 57.08 | 53.87 | **−5.6 %** | 65.20 | 64.23 |
| gas_cc | 58,818.1 | 35.55 | 40.26 | +13.2 % | 41.62 | 57.64 |
| **gas_st** (the failing cohort) | 9,490.3 | 64.02 | 72.34 | **+13.0 %** | 73.62 | 226.19 |
| gas_ct | 26,389.4 | 56.20 | 83.13 | +47.9 % | 69.26 | 129.42 |
| oil | 4,424.4 | 66.33 | 66.33 | 0.0 % | 94.13 | 94.13 |

**The base offer curve makes the failing cohort more expensive and coal cheaper** — the opposite
of what the composition residual needs (PJM over-exits gas_st and under-exits coal). Thermal MW
available below $60 falls 101.2 → 88.8 GW: the whole stack lifts together, common-mode again.

## 5. What is NOT re-opened, and what is raised

**DO-NOT-REDO, added by this lane:** do not propose restoring the gas shape or level to the PJM
forecast lane *as a fix for the retirement-screen E&AS operand*. §2 shows the axis is common-mode
and §3 shows its corrected supply is below the threshold that moves anything. (This is
independent of, and corroborates, the predecessor's `energy_reserve_coopt` `fc: "R"`.)

`ordc_scarcity_overlay` stays **G**. `economic_retirement_screen` stays **R**. Q55 / Q56 and the
sector gate are not re-opened. `energy_reserve_coopt` `fc: "R"` is not re-tested.

**RAISED, OWNER-FACING, NOT DECIDED HERE.** Every PJM forecast and hindcast run dispatches with
**no thermal offer-curve band structure at all**, while PJM's calibrated backcast keeper
dispatches on a full band set — and because the omission is in the *shared* `build_config`, it
plausibly affects **every ISO's** forecast lane. This is the same class of lane inconsistency as
the reserve-field gap the predecessor routed to the owner and is **strictly larger**: it shapes
the price distribution and touches every forecast run's cache key. It is raised as a consistency
question and deliberately **not folded into a residual fix** — the more so because §4 shows
arming it would move the residual the *wrong* way, so any decision to arm must rest on rule 1
`[R-STRUCT]` structural grounds and an owner ruling, never on the fit. The candidate values are
themselves governed: PJM's `_PJM_OFFER_CURVE` is calibrated on PJM's backcast residual (rule 1's
conditioned carve-out); the un-calibrated base curve is a different and more defensible
candidate. **Choosing between them is an owner decision.**

## 6. Governance

- **Rule 29 `[R-SCREEN]`**: phase 0 first, committed artifacts and committed raw data only.
  Phase 0 **killed both candidate arms**, so **no screen was earned and no LP was spent** —
  clause (0) working as written. Nothing is promoted: a phase-0 instrument, like a screen, *may
  kill an arm and may never promote one*. Clause (c) is vacuous here: **no bundle exists** to
  delete, and every number this lane will ever cite is in this document and the PRECOMMIT.
- **Rule 29(b)**: **moot** — no solve ran, so no G-DRIFT re-audit is claimed. Form-4 differencing
  against the registered `pjm-t1h` (`fb16fda2ddb0a94a`) was used only to read committed numbers.
- **Rule 16 `[R-ALLYEARS]`**: untouched — nothing solved, nothing registered.
- **Rule 15 `[R-DASHBOARD]`**: no run was produced, so there is nothing to register.
- **Rule 1 `[R-STRUCT]` / 14 `[R-ACCURATE]`**: no mechanism was rejected for worsening a band.
  Both arms were killed on their **own arithmetic** — a zero correlation and a wrong-signed offer
  move — never on a criterion. The one place a band appears (§3's 12.700 threshold) is a
  *measured mechanism threshold* from phase-0 C, not a scored criterion.
- **Rule 28**: `offer_curve_by_group`'s PJM cell gains an explicit forecast-lane posture and
  citation in this session (duty b). No cell adjudicated R/I/G was re-tested.
- **This lane's own error, corrected in the open**: §4's first hypothesis — that
  `offer_curve_by_group = {}` caps the hindcast price at $52.77 — is **false**, refuted by the
  lane's own instrument, and the gate written to test it did not discriminate.

### 6.1 Environment and pre-existing RED

Fresh container: `pip install -e . --no-deps`, then the control's recorded pins
(`highspy==1.14.0 pandas==3.0.3 pyarrow==24.0.0 pydantic==2.13.4 numpy==2.4.6 scipy==1.17.1`),
plus `tzdata` and `openpyxl`. `data/clean` rebuilt for `fleet` / `reference` / `egrid` only —
all the §4 instrument reads. `highspy` was never invoked. The seven pre-existing RED items on
`main` named in the brief are carried forward unrepaired and unre-verified; see PRECOMMIT §8.
