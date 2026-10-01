# PRE-COMMIT — ERCOT-114 Task B: the JOINT per-zone wind SHAPE × West-Texas curtailment DEPTH

**Written and pushed BEFORE the solve is launched.** Criteria are scored exactly as written and are
not redefined after the result is read (the ERCOT-112/113 discipline).

**Date** 2026-07-26 · **ISO** ERCOT · **Years** 2023–2025, one invocation, years sequential
(rules 12, 16) · **Baseline** the committed keeper bundle `results/calibration/ercot_netrev_margin`
(`2026-07-23-ercot100-netrev-margin-keeper`) · **Scorer**
`scripts/probes/ercot113_score_wind_arms.py` (PINNED — reproduces the published baseline tilt
9.13 / 6.95 / 3.43 pp exactly) plus `scripts/probes/ercot114_wtx_depth_basis.py` for the
curtailment-quantity criterion.

| arm | config |
|---|---|
| **B** baseline | keeper as committed: `ercot_wind_zone_shape=False`, `ercot_wtx_curtail_depth_wind=0.1004` |
| **T** treatment | `ercot_wind_zone_shape=True` **+** `ercot_wtx_curtail_depth_wind=0.0920` |

Solar depth is **unchanged at 0.1637**: the gate redistributes wind only, so the measured corridor
share of solar potential is identical under both allocations (0.4822 → 0.4822, ratio 1.0000).

---

## 1. Why the depth moves, and why to *this* value

ERCOT-113 refuted the shape-only arm and attributed it to a depth derived against the flat
allocation. `scripts/probes/ercot114_wtx_depth_basis.py` measured that coupling and found the
defect is sharper than "the flat profile was compensating":

**The derivation and the application are on different spatial bases.**
`derive_ercot_wtx_curtailment_share.py::_depth` computes
`depth = Σ(HSL_ISO − GEN_ISO) / Σ(HSL_ISO · share)` — both terms **ISO-total** — while
`curtailment_share.wtx_curtail_multipliers` applies `1 − depth·share` to the **West/Panhandle rows
only**. The corridor carries only a fraction `f` of ISO wind potential, and `f` is exactly what the
per-zone SHAPE changes:

| allocation | corridor share of wind potential (pooled 2023–25) |
|---|---|
| flat | **0.5882** |
| per-zone MERRA-2 | **0.6421** |

**The correction is quantity-preserving, and deliberately so.** The naive fix — re-deriving the
depth so the driver alone delivers 100 % of measured curtailment (0.1599 per-zone) — is **refuted
by measurement**, because the driver is not the model's only curtailment source. Wind is an LP
decision variable at MC ≈ 0, so the dispatch curtails endogenously as well:

| year | measured curtailment | baseline model curtailment | shape-only arm (ERCOT-113) |
|---|---|---|---|
| 2023 | 6.03 TWh | 5.63 (−0.40) | 8.25 (**+2.22**) |
| 2024 | 7.17 TWh | 6.38 (−0.80) | 8.98 (**+1.80**) |
| 2025 | 8.76 TWh | 6.89 (−1.87) | 9.16 (**+0.41**) |

Centring the driver alone on the full measured quantity would double-count against that endogenous
curtailment and over-curtail badly. So the depth is instead corrected to hold the mechanism's
**calibrated curtailment quantity invariant** while changing only the spatial basis it is applied
on:

```
depth_per_zone = depth_flat × corridor_share_flat / corridor_share_per_zone
               = 0.1004 × 0.5882 / 0.6421 = 0.0920
```

This is a **source-representation change, not a residual chase** (rule 23): the anchor quantity is
untouched, no price or backcast residual enters, and the commit cites the representation change as
its reason. It is what makes the A/B a clean test of the SHAPE — with the level held fixed, any
movement in the tilt is attributable to spatial allocation alone, which is the confound ERCOT-113
could not escape.

**Note for the record:** holding the quantity at baseline preserves a *pre-existing* level gap —
the model under-curtails wind by 0.40 / 0.80 / 1.87 TWh against measured, and the gap grows with
year. That is a real, separate defect. It is deliberately **not** fixed here, because fixing it in
the same arm would confound the shape test. It is named as ERCOT-115 work below.

---

## 2. Pre-committed criteria

### W0 — ARMING PROOF (hard gate)
`run_config.json` records `ercot_wind_zone_shape=true` **and**
`ercot_wtx_curtail_depth_wind=0.092`, **and** the per-zone wind SHAPE arming log line fires for
all three years (the ERCOT-113 silent-inertness guard). Any miss ⇒ the run is void, not a FAIL.

### W1a — BOUND INVARIANCE (hard falsifier)
The ISO-wide wind **bound** must be preserved exactly by the redistribution
(`_redistribute_preserving_total`, tolerance 1 × 10⁻⁶ MW per hour, established no-LP by
`scripts/probes/ercot113_wind_shape_mechanism_proof.py` at 1.8 × 10⁻¹¹ MW). Failure ⇒ the
mechanism is mis-specified ⇒ **FAIL**.

> **This replaces ERCOT-113's W1, which was wrong as written.** That criterion demanded annual wind
> *energy* be unchanged within 0.1 %. The bound is invariant; **dispatch is not, and is not
> required to be** — relocating wind into a ceiling-bound zone makes the LP curtail more, which is
> the mechanism's whole point. The two are separated here and dispatch movement is explicitly
> **not** a falsifier.

### W1b — CURTAILMENT-QUANTITY PRESERVATION (confound check)
Total model wind curtailment (measured potential − model dispatch) must land within **±0.5 TWh of
the baseline's** in every year (baseline: 5.63 / 6.38 / 6.89 TWh). This is the test of whether the
depth re-derivation actually isolated the shape.
*If W1b fails, the arm is reported **INCONCLUSIVE on the shape question** regardless of W2* — the
level moved, so the tilt is still confounded — and the measured miss is published so the next
session can size the correction. A W1b failure is not scored as a refutation of the shape.

### W2 — PRIMARY: does the tilt narrow?
High-wind-quintile bias spread against the pinned baseline **9.13 / 6.95 / 3.43 pp**.
**PASS iff the tilt narrows in ≥ 2 of 3 years.**

### W3 — scarcity-hour surplus (hard gate)
Scarcity-hour surplus must not degrade by more than **+150 MW** in any year against baseline
(+370 / +430 / +238 MW). A breach is a **FAIL** — it would break the scarcity lane.

### W4 — scarcity price (supporting)
C3a (load-weighted ORDC-inclusive price error) must not degrade in more than one year; C3c
(count ≥ $200/MWh) within ±3 of baseline (76 / 14 / 1). Reported; does not by itself flip the
verdict.

### W5 — LOYO (supporting)
Leave-one-year-out: ≥ 2 of 3 held-out years improve on the tilt. Reported; required for
**promotion**, not for a PASS.

---

## 3. Adjudication rule, fixed in advance

* **Void** if W0 misses.
* **FAIL** if W1a or W3 fails.
* **INCONCLUSIVE** if W1b fails (level not isolated; tilt unreadable).
* Otherwise **PASS iff W2 passes**; **FAIL** if W2 does not.
* **Promotion to default-on** requires W0 + W1a + W1b + W3 **and** W2 at 3/3 **and** W5 ≥ 2/3.
  Anything less and the gate stays **default-off** and the keeper is untouched.

Whatever the verdict, **nothing measured is reverted or weakened** (rules 1, 13, 14, 23): the
per-zone shape is a measured physical input, `ercot_wtx_curtailment_driver` stays armed, and a
worse fit is read as a discovered bug elsewhere, not as a bad input.

---

## 4. Prediction (recorded so it can be wrong)

The depth correction should return total curtailment to ≈ baseline, so wind dispatch should recover
most of the 2.4 / 2.3 / 1.9 % it lost in the shape-only arm, and Panhandle's price collapse
(−3.15 / −1.68) should largely reverse. The tilt is genuinely uncertain: the shape is physically
more faithful, but ERCOT-113's quintile damage was driven by the corridor ceiling binding, and only
part of that was level. **A narrowing in 2/3 years is the honest expectation; a 3/3 narrowing would
be a strong result and a 0/3 would say the corridor ceiling — not the depth level — is the binding
defect, which is the topology question below.**

## 5. Explicitly out of scope for this arm

The charter places the **West/Panhandle topology split** in this same lane, and it stays there — it
is not opened as a separate lane. It is not run *in this arm* because changing the zone/link
structure at the same time as the allocation and the depth would confound all three. It is the
named next step, and this session's measurements (corridor share `f`, the quantity-preserving
depth, and the curtailment level gap) are exactly the inputs it needs.
