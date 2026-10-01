# FINDING — ERCOT-113 Task B: the per-zone wind SHAPE is REFUTED on the tilt — and the refutation localizes the real defect

**Date** 2026-07-26 · **ISO** ERCOT · **Years** 2023–2025 (one invocation, years sequential) ·
**Gate** `ScenarioConfig.ercot_wind_zone_shape` (new, default **off** — unchanged by this run) ·
**Pre-commit** `results/calibration/PRECOMMIT-ercot113-wind-zone-shape-2026-07-26.md`
(written and pushed **before** the solve was launched) ·
**Scorer** `scripts/probes/ercot113_score_wind_arms.py` ·
**Run id** `2026-07-26-ercot113-per-zone-wind`

| arm | run | delta |
|---|---|---|
| **B** baseline | `ercot_netrev_margin` (keeper `2026-07-23-ercot100-netrev-margin-keeper`) | — |
| **T** treatment | `2026-07-26-ercot113-per-zone-wind` | `+ ercot_wind_zone_shape` |

## 1. Result

| year | arm | wind TWh | actual | Q1 | Q2 | Q3 | Q4 | Q5 | **tilt** |
|---|---|---|---|---|---|---|---|---|---|
| 2023 | baseline | 108.41 | 107.99 | +7.0 | +3.5 | +1.8 | −0.4 | −2.1 | **9.13** |
| 2023 | **shape** | 105.79 | 107.99 | +6.5 | +1.8 | −0.8 | −3.7 | −4.4 | **10.92** |
| 2024 | baseline | 112.33 | 111.54 | +5.5 | +3.6 | +2.1 | +0.2 | −1.4 | **6.95** |
| 2024 | **shape** | 109.73 | 111.54 | +4.9 | +2.5 | −0.9 | −3.5 | −3.0 | **7.91** |
| 2025 | baseline | 116.80 | 115.12 | +3.7 | +2.7 | +2.0 | +1.6 | +0.2 | **3.43** |
| 2025 | **shape** | 114.53 | 115.12 | +3.0 | +1.2 | −0.3 | −1.2 | −1.4 | **4.39** |

The scorer reproduces the baseline tilt published in `FINDING-ercot112-wind-prereqs-2026-07-25.md`
exactly (9.13 / 6.95 / 3.43 pp against the finding's 9.1 / 6.9 / 3.5), so the comparison is pinned.

## 2. Verdict against the pre-committed criteria

| criterion | result |
|---|---|
| **W0** arming proof | **PASS** — gate recorded `true`; the zonal signal moved in 3/3 years |
| **W1** aggregate-preservation falsifier (≤ 0.1 %) | **FAIL** — annual wind moved −2.41 % / −2.31 % / −1.95 % |
| **W2** PRIMARY: tilt narrows | **FAIL** — the tilt **widens** in all three years (0/3) |
| **W3** scarcity-hour surplus (≤ +150 MW) | **PASS** — +370→+336, +430→+403, +238→+296 MW |
| **W4** scarcity price | **PASS** — C3a improves every year; C3c 76→77, 14→13, 1→1 |
| **W5** LOYO | **FAIL** — 0/3 improve |

**Adjudication as pre-committed: FAIL (W1 falsifier).** The mechanism stays **default-off** and the
keeper is untouched.

## 3. W1 is reported as it was written — and what it actually caught

W1 was written from the charter's premise that the mechanism "cannot change annual wind energy …
there it measures zero by construction". Per the pre-commit's own terms the criterion is **not
redefined after the fact**; it fails as written. But the honest diagnosis matters, because W1 did
not catch what it was aimed at:

* **The redistribution is not broken.** `scripts/probes/ercot113_wind_shape_mechanism_proof.py`
  shows `_redistribute_preserving_total` holds the ISO total to **1.8 × 10⁻¹¹ MW** in every hour.
  The *bound* is preserved exactly, as claimed.
* **What moved is DISPATCH, not the bound.** Wind is a decision variable bounded per zone. Moving
  it into the West/Panhandle corridor puts more of it behind a ceiling that binds, so the LP
  curtails more. Annual *dispatch* falls ~2.4 % while the *bound* is untouched.

So the charter's "measures zero by construction" is true of the wind **bound** and false of wind
**dispatch** once curtailment is endogenous. W1 conflated the two. This is recorded as a defect in
the criterion's wording, not a licence to rescore: **W2, the PRIMARY criterion, fails independently
and unambiguously** — the tilt widens in 3/3 years — so the adjudication does not rest on W1.

## 4. The congestion signature — where the wind went

Zonal mean P1 price, baseline → treatment:

| zone | 2023 | 2024 | 2025 |
|---|---|---|---|
| **Panhandle** | 24.88 → 21.73 (**−3.15**) | 10.76 → 9.09 (**−1.68**) | 11.22 → 11.65 (+0.43) |
| West | 39.25 → 39.53 (+0.28) | 26.68 → 26.74 (+0.06) | 32.37 → 32.59 (+0.22) |
| North / Houston / South_Central | +0.46 | +0.29 | +0.37 |

Panhandle collapses while every other zone firms — the textbook signature of energy pushed behind a
binding export/curtailment limit. The per-quintile losses confirm it: the high-wind quintiles lose
most (2023 Q5 −2.1 → −4.4, Q4 −0.4 → −3.7) because that is when the corridor is already full.

## 5. What this means — the refutation is informative, and it is NOT a reason to discard the shape

The per-zone shape is a **measured physical input**: MERRA-2 (NASA POWER WS50M) wind speed at the
ISO's own EIA-860 wind-plant locations through a turbine power curve. Its night/afternoon ratios
reproduce the charter's published values exactly (2024: West 1.15, Panhandle 1.13, North 1.14,
Houston 0.95, South 0.84). One ISO-wide profile applied to every zone is, physically, the *less*
faithful representation — it averages the nocturnal jet and the Gulf sea breeze together.

Rules 1 and 14 govern the read. A structurally-more-faithful measured input that makes the fit
**worse** is a discovered bug elsewhere, not a bad input:

> "If swapping a hand estimate for real data makes the backcast *worse*, that is a signal that
> **something else in the model is miscalibrated** and the estimate was silently compensating."

Here the suspect is explicit. `ercot_wtx_curtail_depth_wind = 0.1004` was derived against the
**flat** wind allocation — with wind spread evenly, a 10 % corridor curtailment depth reproduced the
measured curtailment. Once wind is put where it physically is (concentrated in the West/Panhandle
CREZ corridor), that same depth over-curtails, which is exactly the −2.4 % dispatch loss and the
Panhandle price collapse above. **The flat profile was silently compensating for a curtailment
driver scaled to it.**

Accordingly this session does **not** weaken or revert anything: `ercot_wtx_curtailment_driver`
stays armed and at its derived depth (rule 23 — it re-derives only when its source data changes,
never because a residual moved), and the shape gate stays default-off pending the joint work below.

## 6. Recommended next charter (ERCOT-114 or its own lane)

**The per-zone wind shape and the West/Panhandle curtailment depth must be adjudicated jointly, not
separately.** They are one mechanism split across two parameters, and testing either alone is
confounded by the other. Concretely:

1. Re-derive `ercot_wtx_curtail_depth_wind` (and `_solar`) **on the per-zone allocation** —
   `scripts/data/derive_ercot_wtx_curtailment_share.py` currently sees the flat split. This is a
   source-representation change, not a residual chase, so it is a legitimate re-derivation (rule 23)
   and the commit must cite it as such.
2. Re-run the A/B with both armed, scored on the **same** pre-committed tilt criteria, plus a
   corrected aggregate criterion that separates the wind **bound** (must be invariant) from wind
   **dispatch** (may legitimately move — it is the mechanism's whole point).
3. Only then is the tilt lane readable. Until the depth is re-derived on the correct spatial basis,
   a per-zone-shape A/B measures the stale depth, not the shape.

The charter's named West/Panhandle topology split belongs in the same lane — all three touch the
same corridor.

## 7. Rules observed

Pre-commit written and pushed before the solve; criteria scored exactly as written and not
redefined after the result was read; one invocation covering all three years (rule 16); years
sequential; no out-of-training year touched (rule 22); the run is registered on the dashboard in the
session that produced it (rule 15); the gate is default-off and the keeper is neither re-solved nor
re-pointed; no measured input was weakened or reverted because a residual moved (rules 1, 14, 23).
