# RESULT — neiso-109: the repaired AGT series, screened and solved across all six years

**Session** neiso-109 · **Date** 2026-09-16 · **Keeper under test** `2026-09-09-neiso-108-fuelvintage`
(+ its folded touchpoint `…-touchpoints`), **UNCHANGED by this session**.
**Pre-registration:** `docs/PRECOMMIT-neiso109-gas-repair-screen-2026-09-16.md` +
`docs/ADDENDUM-neiso109-run-all-years-2026-09-16.md`, both pushed before any solve.
**The repair itself:** `docs/FINDING-neiso109-the-agt-series-is-contaminated-2026-09-16.md`.

> ## THE SHORT VERSION
> **The input repair is unambiguously correct** — 82 rows of the committed file were other
> trading hubs' prices. **Two pre-registered gates fire**, and both trace to gates I wrote
> wrong rather than to the repair. **And the fit on oil gets WORSE in four of six years.**
>
> Under rule 14 `[R-ACCURATE]` that last fact is not a reason to revert — it is the discovery.
> The model's ISO-NE winter oil burn was being produced by **New York's and Waha's gas prices
> crossing Boston's oil-parity line**. Take the contamination out and the parity channel yields
> a different, mostly smaller oil burn — while the measured actual stays where it always was.
> **The parity channel is not what drives ISO-NE's winter oil burn**, and the contaminated data
> had been concealing that.
>
> **A screen may kill an arm; it may never promote one. Nothing here is promoted.**

---

## 1. WHAT WAS SOLVED

| shard | years | legs | wall-clock | branch / commit |
|---|---|---|---|---|
| screen | 2025 | control + arm | ~14 min both legs | `claude/neiso109-screen-2025` · **`619e7a26`** |
| span | **2020–2025** | arm | **736 s** (12.3 min, all six years) | `claude/neiso109-span` · **`554fa733ac1483fc7342c8ac09d739cee0773f55`** |

One invocation, one bundle, years sequential (rules 16 / 32(b) / 34(c)). The arm is the keeper's
frozen recipe with **the repaired gas file as the only difference**: zero `ScenarioConfig` choices
move, no flag armed, the DOF ledger and the keeper's `authorized_price_tuning` declaration
(neiso-106's 0.95470) carried forward untouched.

The span's `scenario_config` differs from the keeper's in 17 fields, **all accounted for**: 15 are
fields that **did not exist** when the keeper solved (2026-09-09) and now materialize at their
defaults (other lanes' additions, all default-off, none NEISO's); `spp_curtail_depth_wind` is an SPP
default; and `gas_price_override` 2.54 → 2.03 with `weather_year` 2023 → 2020 are **the first solved
year's value echoed into the recorded config** — the span starts at 2020, the keeper started at 2023.
Predicted by the pre-solve check in ADDENDUM §5 and measured inert by §2 below.

## 2. G-DRIFT — SETTLED EMPIRICALLY, AND THE ANSWER IS ZERO

PRECOMMIT §5 could not validate rule 29(b) form 4: the keeper's `git_sha 52a2f519` and
`basis_sha cfc6672…` both fail to resolve, and the diff from its registration commit runs to **57
files / +6,555 lines** across the backcast path. That is why the screen solved a paired control.

**The control leg reproduces the keeper's committed 2025 BIT-IDENTICALLY:**

```
zone-hours differing        0  of 43,800
load-weighted price   69.687839  ==  69.687839      (6 dp)
annual class energy   0.00000 TWh delta, max 0.0 ppm, all 14 classes
slack / dump          0.000000 / 0.000000  both
```

**NEISO HEAD drift is exactly zero**, materialized default fields included. Form 4 is valid, the
keeper's and touchpoint's committed bundles are the controls for all six years, and no control span
was spent. This is what rule 29(b) means by G-DRIFT being *stronger* than a control solve — and here
it took a control solve to establish it, because the code-level audit was not available.

## 3. THE GATES — TWO FIRE

| gate | result |
|---|---|
| **G-1 (i) mean preservation** | **PASS**, pre-solve. Max \|Δ monthly mean\| **3.6e-15 $/MMBtu** over every month of every year. The frozen `gas_offer_margin_anchor = 4.0763` is unmoved, confirmed in both solved configs. |
| **G-1 (ii) month confinement** | **PASS**, pre-solve. Moved months ⊆ print-changed months in all six years. |
| **G-1 (iii) LP confinement** | **FAILS AS WRITTEN** — §3.1 |
| **G-2 direction** | **PASS**. 2025-01-17…19 **190.56 → 157.53 (−33.03)**; 2025-01-25…28 **96.60 → 154.77 (+58.17)**. Both windows, both signs, exactly as pre-registered for a two-signed repair. |
| **G-3 order of magnitude** | **PASS**. Zone-hour price delta **+67.04 / −71.32**, inside the pre-solve Δmc band **[−457.17, +181.74]**. The LP is repricing, not amplifying. |
| **G-4 no structural break** | **FIRES on 2021** — §3.2 |
| **G-5 identity** | **PASS on its conditional half**. Oil is the only class past 10 %; **100.00 %** of the 2025 rise sits inside the touched months, and oil **+768,656 MWh** against gas family **−780,456 MWh** is one-for-one to **1.54 %**. |

### 3.1 G-1(iii) fails, and the gate was mis-specified — not reinterpreted after the fact

The gate says untouched hours show **zero** price change. **1,460 zone-hours outside Jan/Feb/Jul
moved.** I re-derived the gas array to check I had not mis-stated the footprint: I had not — it moves
in exactly **2,160 hours across months 1, 2, 7** and nowhere else.

The channel is **storage, through the cyclic SOC boundary the LP formulation specifies**:

```
month 6:  thermal −8,116.00 MWh   storage net +8,115.47 MWh   residual −0.53 MWh
month 8:  thermal −2,184.00 MWh   storage net +2,184.76 MWh   residual +0.76 MWh
```

Energy-conserving to **0.007 %**, **0.132 %** of total movement, 292 of 5,832 out-of-window hours,
one-signed. It is **not** NYISO's anchor channel — that was a near-uniform level shift across every
untouched month with ratio 1.02 to the anchor delta; here the anchor provably did not move. So
PRECOMMIT §2(b)'s prediction holds **on its substance** while the gate fails **on its letter**.

**The gate should have been written over the gas-driven price change.** I did not account for cyclic
storage when I wrote it. Narrowing it now is exactly what pre-registration exists to prevent, so it
stands as a failure and the owner weighs it.

### 3.2 G-4 fires on 2021 — and the control fires identically

2021 dumps **1,380.617467 MWh** in one zone-hour (model hour 1415). So does the **control**, to the
same six decimals, in the same hour, at the same price (−26.001 $/MWh), against a **negative zone
demand** (−8.6 MW) — the model shedding a net-negative load artifact. The only difference between
the legs is the zone label (Boston vs North), an alternate-optimum tie. The gas array moves
−0.0144 $/MMBtu in that hour.

**Pre-existing, not caused by the repair.** But my gate says "zero in BOTH legs", and the control
is not zero — so the gate was wrong for a year whose control already dumps. Same discipline as
§3.1: reported as a failure, cause measured, not rewritten.

## 4. EVERY YEAR, AT FULL MAGNITUDE

**Slack is 0.000000 in all six years, both legs.** Dump is 0.000000 in five and the 2021 artifact above.

| year | control $/MWh | arm $/MWh | Δ | zone-h changed | max +Δ | min −Δ |
|---|---:|---:|---:|---:|---:|---:|
| 2020 | 26.6329 | 26.6650 | +0.0321 | 12,020 | +32.51 | −18.77 |
| 2021 | 50.0221 | 50.2253 | +0.2032 | 23,035 | +41.71 | −28.42 |
| 2022 | 88.7906 | 88.7109 | −0.0797 | 16,800 | +100.20 | −45.99 |
| 2023 | 37.5896 | 37.5012 | −0.0883 | 23,955 | +35.29 | −91.16 |
| 2024 | 42.4175 | 42.5297 | +0.1121 | 14,945 | +69.20 | −51.00 |
| 2025 | 69.6878 | 70.6941 | **+1.0062** | 12,235 | +67.04 | −71.32 |

## 5. THE PRE-REGISTERED CALLS — THREE LAND, ONE MISSES

PRECOMMIT §3.1 fixed the oil direction per year **from the parity table, before any solve**:

| year | pre-registered | control TWh | arm TWh | Δ | verdict |
|---|---|---:|---:|---:|---|
| 2023 | **FALL to ~0** | 0.31028 | **0.00345** | **−98.9 %** | ✅ the falsifiable one |
| 2024 | FALL | 0.24971 | 0.04844 | −80.6 % | ✅ |
| 2025 | RISE | 1.62744 | 2.39610 | +47.2 % | ✅ |
| 2022 | no change | 0.15018 | 0.13067 | −13.0 % | ❌ **missed** |
| 2020 / 2021 | no change | 0.00029 / 0.02044 | 0.00147 / 0.02120 | immaterial | ✅ |

**Why 2022 missed, stated as my error:** I set that call from the oil-parity **hour count**, which is
48 → 48 unchanged. An unchanged count does not mean the *same hours* — January 2022 is a moved month
and its level shifted, moving **−20,495 MWh** of January oil. 98.3 % of the 2022 oil move is inside
moved months, so the footprint logic held; my inference from the count did not.

## 6. THE RESULT THAT MATTERS — THE FIT ON OIL GETS WORSE

Against NEISO's measured actuals (`bench/NEISO/<year>.json.gz`, `classFull`):

| year | oil actual | control err | arm err | | gas-family actual | control err | arm err |
|---|---:|---:|---:|---|---:|---:|---:|
| 2020 | 0.149 | −0.149 | **−0.148** | | 49.357 | −0.084 | **−0.079** |
| 2021 | 0.239 | −0.219 | **−0.218** | | 53.831 | **+0.145** | +0.166 |
| 2022 | 1.852 | **−1.702** | −1.721 | | 53.342 | **+0.961** | +0.973 |
| 2023 | 0.390 | **−0.079** | −0.386 | | 55.007 | −0.618 | **−0.380** |
| 2024 | 0.312 | **−0.062** | −0.263 | | 59.364 | **−0.043** | +0.162 |
| 2025 | 0.909 | **+0.718** | +1.487 | | 59.756 | +1.666 | **+0.886** |

**Oil: the arm is worse in four of six years, materially in 2023, 2024 and 2025.**
**Gas family: the arm is better in 2023 and 2025, the two biggest misses.**

And the combined pair, which is what the dual-fuel switch actually moves between:

| year | gas+oil actual | control err | arm err | closer |
|---|---:|---:|---:|---|
| 2020 | 49.506 | −0.233 | −0.227 | arm |
| 2021 | 54.070 | −0.074 | −0.052 | arm |
| 2022 | 55.195 | −0.741 | −0.749 | control |
| 2023 | 55.396 | −0.697 | −0.766 | control |
| 2024 | 59.676 | −0.106 | −0.102 | arm |
| 2025 | 60.665 | +2.384 | **+2.373** | arm |

**The combined total barely moves — the repair changes the LABEL, not the quantity.** In 2025 the arm
shifts 0.77 TWh from gas to oil and the pair stays 2.37 TWh over actual either way.

### What that means, under rule 14 `[R-ACCURATE]`

Rule 14 is explicit: *"If swapping a hand estimate for real data makes the backcast worse, that is a
signal that something else in the model is miscalibrated and the estimate was silently compensating
for it. Treat the worse fit as a discovered bug… Do not bury the error back inside an inaccurate
input."* PRECOMMIT §3.4 pre-registered that a worse fit would not be grounds to revert, **and a
better number would not be grounds to promote**.

The discovered bug is this: **the model was burning oil in February 2023 because it believed Boston
gas reached $30.13/MMBtu. Boston gas peaked at $15.77. The $28–30 print was Transco Z6 NY's** — New
York's price, harvested by an extremum pattern with no Algonquin anchor, and cited in
`hubs.iso_hub_daily_gas_prices`'s own docstring as the worked example of the mechanism succeeding.

Strip it and 2023 has **no hour above oil parity at all**. The oil burn that the parity channel was
producing is gone — while the measured actual (0.390 TWh in 2023, **1.852 TWh in 2022**, 0.909 in
2025) stays where it was. The model is short 1.7 TWh of 2022 oil **before and after** the repair.

**So the parity channel is not the mechanism that drives ISO-NE's winter oil burn**, and contaminated
data had been standing in for the one that is. NEISO already carries the candidates —
`neiso_winter_fuel_mustrun`, `neiso_winter_fuel_inventory`, `neiso_oil_burn_budget`,
`neiso_gas_coldsnap_derate` — and this result says the weight is on them, not on price parity. That
is the successor object for this lane, and it is a **root cause to fix, not a residual to absorb**.

## 7. RETRIEVABILITY (rule 34 `[R-SHARD-PROMOTABLE]` (e))

| bundle | where | promotion cost from this state |
|---|---|---|
| span 2020–2025 (212 MB, 67 files, `dispatch/<year>_P1.parquet` × 6 + root `system.parquet`) | commit **`554fa733ac1483fc7342c8ac09d739cee0773f55`**, branch `claude/neiso109-span` | **zero re-solve** — `git archive 554fa733ac1483fc7342c8ac09d739cee0773f55 results/calibration/neiso109_gasrepair_span \| tar -x` |
| screen 2025 control + arm (36 MB each) | commit **`619e7a26`**, branch `claude/neiso109-screen-2025` | zero re-solve, same route |

Both are on immutable SHAs reachable from pushed branches. **Nothing has been deleted** (rule 31
`[R-RETAIN]`), and nothing will be until the owner rules.

## 8. WHAT WAS NOT DONE

* **No promotion, no registration, no keeper change.** The dashboard still shows
  `2026-09-09-neiso-108-fuelvintage`.
* **No mechanism cell moved** (rule 28 `[R-MECH-MATRIX]` (b)) — no `ScenarioConfig` field was added
  or changed, so there is no cell to carry a verdict.
* **No gate was rewritten after seeing its result**, and no criterion was treated as a gate in
  either direction.
* **The oil root cause was not opened.** It is named here as the successor and left for its own
  session with its own pre-registration.
