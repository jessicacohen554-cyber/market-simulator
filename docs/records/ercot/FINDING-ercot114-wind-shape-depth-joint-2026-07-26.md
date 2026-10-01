# FINDING — ERCOT-114 Task B: the joint arm is INCONCLUSIVE on the shape, and it proves the defect is TOPOLOGY, not depth

**Date** 2026-07-26 · **ISO** ERCOT · **Years** 2023–2025 (one invocation, years sequential) ·
**Pre-commit** `results/calibration/PRECOMMIT-ercot114-wind-shape-depth-joint-2026-07-26.md`
(written and pushed **before** the solve was launched) ·
**Run id** `2026-07-26-ercot114-joint-per-zone` ·
**Scorers** `scripts/probes/ercot113_score_wind_arms.py` (PINNED),
`scripts/probes/ercot114_wtx_depth_basis.py`

| arm | run | delta |
|---|---|---|
| **B** baseline | `ercot_netrev_margin` (keeper `2026-07-23-ercot100-netrev-margin-keeper`) | — |
| **S** shape-only | `ercot113_wind_zone_shape` | `+ ercot_wind_zone_shape` |
| **T** treatment | `2026-07-26-ercot114-joint-per-zone` | `+ ercot_wind_zone_shape`, `depth_wind 0.1004 → 0.0920` |

## 1. Verdict against the pre-committed criteria

| criterion | result |
|---|---|
| **W0** arming proof | **PASS** — `run_config.json` records `ercot_wind_zone_shape=true` and `ercot_wtx_curtail_depth_wind=0.092`; the arming line fired in 3/3 years at `depth wind=0.0920 solar=0.1637` |
| **W1a** bound invariance (hard falsifier) | **PASS** — redistribution preserves the ISO wind bound to 1.8 × 10⁻¹¹ MW/hour |
| **W1b** curtailment-quantity preservation (±0.5 TWh) | **FAIL** 3/3 — **+2.32 / +2.28 / +1.95 TWh** vs baseline |
| **W2** PRIMARY: tilt narrows | **FAIL** — widens 3/3 (9.13→10.76, 6.95→7.77, 3.43→4.25) |
| **W3** scarcity-hour surplus (≤ +150 MW) | **PASS** — −27, −18, +69 MW |
| **W4** scarcity price | **PASS** — C3a −16.8→−16.1, 0.2→1.0, 0.7→1.4; C3c 76→75, 14→13, 1→1 |
| **W5** LOYO | **FAIL** — 0/3 improve |

**Adjudication as pre-committed: INCONCLUSIVE on the shape question.** The pre-commit fixed this in
advance: *"If W1b fails, the arm is reported INCONCLUSIVE on the shape question regardless of W2 —
the level moved, so the tilt is still confounded — and a W1b failure is not scored as a refutation
of the shape."* W1b failed in all three years, so **W2's failure is not scored as a refutation.**
The gate stays **default-off**, the depth default stays **0.1004**, and the keeper is untouched.

Note the pinned ERCOT-113 scorer prints its own verdict line, `FAIL (W1 falsifier)`, using the
**superseded** W1 (annual wind energy within 0.1 %). That criterion was replaced *before this solve*
by W1a/W1b for the reason ERCOT-113 itself documented — it conflates the bound with dispatch. The
scorer's line is reported here for provenance and is not this run's adjudication.

## 2. Why W1b failed — and why that is the result

The depth correction was sized offline to hold the driver's own curtailment quantity fixed. **It
did exactly that, and it barely mattered.** Measured against the shape-only arm:

| year | baseline wind | shape-only | joint | level effect (S−B) | recovered by depth (T−S) | **share attributable to depth** |
|---|---|---|---|---|---|---|
| 2023 | 108.411 | 105.793 | 106.088 | −2.618 TWh | +0.295 TWh | **11.3 %** |
| 2024 | 112.331 | 109.735 | 110.050 | −2.596 TWh | +0.315 TWh | **12.1 %** |
| 2025 | 116.804 | 114.532 | 114.857 | −2.272 TWh | +0.325 TWh | **14.3 %** |

The offline calculation predicted the driver's *bound* reduction would move by only
+0.02 / +0.02 / −0.04 TWh under the correction, and it did. Realized curtailment instead moved
**+2.3 TWh**. That difference cannot come from the WTX ceiling — it is **endogenous** curtailment:
the LP curtailing relocated wind behind the zonal transmission limit.

**So 86–89 % of the shape arm's level effect was never the depth at all.**

## 3. The congestion signature confirms it

Zonal mean P1 price change vs baseline — the depth correction leaves it essentially untouched:

| zone | 2023 shape-only → joint | 2024 shape-only → joint | 2025 shape-only → joint |
|---|---|---|---|
| **Panhandle** | −3.15 → **−3.27** | −1.68 → **−1.79** | +0.43 → +0.31 |
| West | +0.28 → +0.23 | +0.06 → +0.02 | +0.22 → +0.18 |
| North / Houston / South_Central | +0.46 → +0.42 | +0.29 → +0.26 | +0.37 → +0.33 |

The Panhandle collapse is the signature of energy pushed behind a binding export limit. Correcting
the curtailment depth by 8.4 % moved it by 0.12 $/MWh — and in the *wrong* direction. **The binding
constraint is the corridor's zonal transmission limit, not the curtailment ceiling.**

## 4. The pre-commit called this branch in advance

> *"a 0/3 would say the corridor ceiling — not the depth level — is the binding defect, which is the
> topology question below."*

That is the outcome, and it is now quantified rather than asserted: the depth accounts for 11–14 %
of the level effect and ~0 % of the price signature.

## 5. What is established, and what carries forward

**Established and banked** (no re-derivation needed by a successor):

* The derive/apply **spatial-basis mismatch is real**: `_depth` divides by ISO-total HSL while
  `wtx_curtail_multipliers` applies to West/Panhandle rows only. Corridor share of wind potential
  is **0.5882 flat → 0.6421 per-zone** (pooled 2023–25).
* The **quantity-preserving depth for the per-zone allocation is 0.0920** (= 0.1004 × 0.9161);
  solar is unchanged at 0.1637 because the gate redistributes wind only (ratio 1.0000).
* Centring the driver *alone* on 100 % of measured curtailment (0.1599 wind / 0.3463 solar) is
  **refuted** — the driver is not the model's only curtailment source.
* The model **under**-curtails wind against measured by **0.40 / 0.80 / 1.87 TWh** at baseline, and
  the gap **grows with year**. This is a real, separate level defect, deliberately not fixed here
  because it would confound the shape test.

**Carried forward to ERCOT-115 — the West/Panhandle topology split is now the head of this lane,
not a companion to it.** The evidence promotes it: the depth is measured out as a minor actor, and
the corridor limit is measured in as the dominant one. The inputs it needs are all in this session's
committed probes.

The per-zone shape itself remains **unrefuted and unadopted**: it is a measured physical input
(NASA POWER WS50M at the ISO's own EIA-860 wind-plant locations through a turbine power curve) whose
2024 night/afternoon ratios reproduce the charter's published values exactly (West 1.15, Panhandle
1.13, North 1.14, Houston 0.95, South 0.84 — logged by the solve). It cannot be adjudicated until
the corridor it loads is represented correctly, which is precisely the topology work.

## 6. Rules observed

Pre-commit written and pushed before the solve; criteria scored exactly as written and **not**
redefined after the result was read — including honouring the pre-committed INCONCLUSIVE branch
rather than taking W2's failure as a refutation. One invocation covering all three years (rule 16);
years sequential (rule 12); no out-of-training year touched (rule 22); the run is registered on the
dashboard in the session that produced it (rule 15). Nothing measured was weakened or reverted
because a residual moved (rules 1, 13, 14): `ercot_wtx_curtailment_driver` stays armed, the default
depth stays 0.1004, the shape gate stays default-off, and the keeper is neither re-solved nor
re-pointed. The depth re-derivation is a source-representation change with the anchor quantity held
fixed, cited as such (rule 23).
