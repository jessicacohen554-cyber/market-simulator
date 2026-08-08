# FINDING nyiso-132 — the NYISO solar CF level: A/B result, and the commissioning-curve defect it opened

**Session nyiso-132, 2026-08-07/08.** Paired A/B on the keeper recipe
`2026-08-07-nyiso-131-taxgs-arm` (bundle `nyiso131_taxgs_arm`), 2023–2025, both
arms registered:

* `2026-08-08-nyiso-132-cf-control` — bundle `nyiso132_cf_control`
* `2026-08-08-nyiso-132-cf-arm` — bundle `nyiso132_cf_arm`

Pre-registration: `PREREG-nyiso132-solar-cf-level-2026-08-07.md` (which itself
discharged §4 of `PREREG-nyiso130-solar-cf-level-2026-08-06.md`).
Gate record: `_nyiso132_ab_gates.json`; realization decomposition:
`_nyiso132_cf_realization.json`.

---

## 1. THE CONTROL REPRODUCES THE KEEPER BYTE-IDENTICALLY

The replay warned that the environment had drifted from the bundle's recorded
one (platform v18→v20, highspy 1.14.0→1.15.1, pandas 3.0.3→3.0.5,
pyarrow 24.0.0→25.0.0), so byte-identity was **not** guaranteed and the
reproduction check was treated as load-bearing rather than a formality.

**It reproduces exactly.** Against the keeper's committed sidecars:

| grain | result |
|---|---|
| class-year energy, all 14 classes × 3 years | **0.000 GWh** |
| hourly, P1, 122,640 rows × 3 years | **max \|Δ\| = 0.000000000 MW** |
| `reserve_family` duals, 7 numeric columns × 3 years | **0.000000000** |

So the comparison baseline is EXACT and the arm's entire delta is attributable
to the CF change alone. The nyiso-128-class hazard — a control that fails to
reproduce its own keeper, putting the whole comparison in question — **does not
fire here**.

## 2. Construction gates — ALL PASS

| gate | result |
|---|---|
| **K1** config isolation | **PASS** — ZERO differing `scenario_config` fields. This arm is an ungated `constants.py` change, so the usual gate is inverted: the configs must be *identical* and the delta lives in the source trees. (Compared after checkout-prefix normalization: the control runs from a sibling tree whose `data/` symlinks back, so six `*_path` fields differ by prefix while resolving to the same files. Normalizing is the same fold `scenarios.py::_normalize_cache_key_paths` applies to the cache key — not a waiver.) |
| **K2** feasibility | **PASS** — zero slack and zero dump, both arms, all three years |
| **K3** liveness | **PASS** — solar energy ratio 1.3010 / 1.3003 / 1.3024 against the expected 0.1955/0.15 = 1.3033. The constant demonstrably reaches the LP |
| **K4** scope | **PASS** — wind energy identical at **0.000 GWh** in every year; the edit did not leak past the solar entry |

## 3. Gated criteria — NOTHING MOVES, AND BOTH ADVERSE CASES FAILED TO MATERIALIZE

**Determination: `CALIBRATED-WITH-CAVEATS` in BOTH arms**, all 8 criterion
statuses identical (C1/C2/C3a/C3b/C4/C6/C8 PASS; C3c the same lone ledgered
caveat, budget 1 of 1).

| criterion | actual | control | **arm** |
|---|---:|---:|---:|
| C3a 2023 | 32.25 | 35.12 (+8.90 %) | **35.08 (+8.78 %)** |
| C3a 2024 | 38.13 | 38.50 (+0.97 %) | **38.40 (+0.71 %)** |
| C3a 2025 | 66.45 | 64.36 (−3.14 %) | **64.16 (−3.45 %)** |
| C3c 2023 | 10 h | 22 h (2.20×) | **21 h (2.10×)** |
| C3c 2024 | 12 h | 3 h | **3 h** |
| C3c 2025 | 42 h | 24 h (PASS) | **24 h (PASS)** |

Both pre-registered adverse cases are **refuted by measurement**:

* **"C3a-2025 crosses −10 %"** — did not happen. −3.14 % → −3.45 %, nowhere near
  the band edge. The largest mean-LMP move in any year is **0.31 %**.
* **"C3c-2025 falls through its band floor of 21 h"** — did not happen. It is
  **unchanged at 24 h** and did not move at all.

C3c-2023 *improves* (22 h → 21 h, 2.20× → 2.10×, toward the measured 10 h) —
reported as a one-hour move on an over-produced tail, not claimed as a fix.
C8 forced shares move by ≤0.0013; C2 gas volume falls ≤0.16 TWh.

## 4. WHAT IT BUYS AND WHAT IT COSTS — reported against interest

The lever is a rule 14 `[R-ACCURATE]` input repair with **zero free parameters**:
`RENEWABLE_AVG_CF["NYISO"]["solar"]` 0.15 → 0.1955, replacing a self-declared
Tier-3 approximation whose own comment asked for exactly this verification
(*"needs-citation: verify against EIA-923 ISO totals before quoting a
forecast"*) with the registered fleet's measured mature-year CF.

**Solar level vs the published Gold Book Table III-2a registry:**

| year | published | control | **arm** |
|---|---:|---:|---:|
| 2023 | 229.9 GWh | 213.6 (−7.1 %) | **277.9 (+20.9 %)** |
| 2024 | 503.2 GWh | 515.4 (+2.4 %) | **670.2 (+33.2 %)** |
| 2025 | 981.8 GWh | 753.5 (−23.3 %) | **981.3 (−0.1 %)** |

**It buys an essentially exact mature year and costs two commissioning years.**
On the ±10 % VRE band that is a trade of ONE breach for TWO, and it is not
presented as a clean win.

Two facts bound how much that costs, and neither is an excuse:

1. That band is `calibration_verdict.VRE_TOL`, explicitly **report-only**, and
   the D-10 diagnostic classifies solar as **`delivered_pinned` — "PINNED
   (advisory-only, excluded from skill claims)"**. So no gated criterion moves
   on it, which §3 confirms empirically.
2. NYISO solar is 0.2–1.0 TWh against ~150 TWh of load, so even the worst year's
   error is ~0.1 % of system energy.

## 5. THE DEFECT THIS OPENED — no commissioning curve (rule 19, NOT bundled)

The ramp-year cost is not noise and has a named cause. The model's monthly
capacity ramp counts a plant as **fully present from its in-service month**,
with no commissioning curve, while the registry's own realized CF runs
**0.1629 / 0.1468 / 0.1955** across 2023/2024/2025 — a 33 % swing driven by
commissioning, worst in 2024, the heavy build year (registered capacity
174.4 → 573.4 MW, mean-month/year-end **0.6800**).

**A single CF cannot track that fleet.** Applying the mature-fleet value
uniformly necessarily over-states the ramp years — which is precisely what §4
measures. This is a **separate object** (rule 19 `[R-ONE-MECH]`), deliberately
not bundled into this arm, and it is recorded as an open item in the arm's
attestation.

**Two honest readings, both on the record.** (a) Rule 14 as written: the
accurate input stays and the worse fit is a *discovered bug elsewhere* — here
the missing commissioning curve — to be fixed at its own root, not buried back
inside the input. (b) Rule 14's documented exception: a mature-fleet quantity is
*time-aggregation misaligned* to a commissioning-year population, which is one
of the cases where an estimate may legitimately be kept. This session's
recommendation follows (a), because the misalignment lives in the **model's
ramp**, not in the data — but (b) is a real argument and is not suppressed.

Note also that `RENEWABLE_AVG_CF` is documented as the **forecast**
normalization. For 2026+ the NYISO market fleet is mature, so the mature-year CF
is the structurally correct forward parameter regardless of how it scores on two
historical commissioning years.

## 6. Falsified on the way — the "realized 0.133" figure

The nyiso-130 prereg attributed the 0.15 → 0.133 gap to *"clipping and the donor
profile"*. **Both limbs are refuted** (`_nyiso132_cf_realization.json`): in all
three years the distribution sums to 1.000000, the realized hourly mean CF is
**0.150000 exactly**, and **zero hours clip**. The donor repair supplies the
shape only; `derive_cf_profile` renormalizes the level.

The whole gap is the **denominator convention** — energy accrues against the
monthly ramp while `installed_mw` is year-end capacity, so `energy/(year-end ×
8760)` under-reads a growing fleet (EIA-860 year-end 0.1345/0.1176/0.1385,
mean **0.1302** = the reported "0.133"; against mean-monthly every year reads
0.149–0.150). On the registered basis in the flat 2025 fleet the two conventions
coincide and the model realizes **0.1500 exactly**.

**This mattered to the sizing, which is why the item existed.** Sized off the
constant: factor 1.3033 → 2025 at 977.5 GWh predicted, **981.3 measured**
(−0.1 %). Sized off the reported 0.133: factor 1.4699 → ~1,102 GWh, **+12.3 %
over the fleet's own published output.**

## 7. Recommendation

**PROMOTE.** Structure improves (a Tier-3 guess carrying `needs-citation`
becomes a measured registry identity, zero free parameters, `n_residual`
unchanged at 6), the mature-year level goes from −23.3 % to −0.1 %, and **no
gated criterion regresses** — the determination and all 8 statuses are identical
and C3c-2023 is marginally better.

This is a weaker ask than nyiso-129, where the owner accepted a determination
*downgrade* for structural integrity under the standing standard *"If structural
integrity improves but gates regress that may still be a keeper."* Here the
gates do not regress at all.

The honest counter is the 1→2 advisory-breach count in §4, whose cause is named
in §5 and carried as an open item rather than absorbed. **Promotion is the
owner's call; the keeper shard is untouched pending it.**

## 8. Rule 25 `[R-ISO-SCOPE]`

NEISO carries the identical Tier-3 `0.15` with the identical `needs-citation`.
It is **NOT** covered by this identification and must derive its own from its own
market's data. No NEISO entry, file or cell is touched.
