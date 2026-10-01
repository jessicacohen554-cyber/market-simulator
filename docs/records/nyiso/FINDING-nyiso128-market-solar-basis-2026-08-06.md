# FINDING nyiso-128 — NYISO grid solar is double-counted against the load series; the correction is live, and the keeper does not reproduce on main

**Keeper UNCHANGED** at `2026-08-04-nyiso-125-seam-envelope`. **No promotion.**
Both pre-registered arms solved 2023–2025 and registered (rule 15):
`2026-08-06-nyiso-128-control`, `2026-08-06-nyiso-128-solar-basis`.
Pre-registration: `PREREG-nyiso128-market-solar-basis-2026-08-05.md`, committed
and pushed before either arm was solved.

---

## 1. The defect

The model distributes NYISO solar capacity from the EIA-860 utility-scale
operable schedule, which lists every NY solar plant ≥ 1 MW — **including ~2 GW
of distribution-connected NY-Sun community solar that is not a NYISO market
generator**. That output is already **netted out of the EIA-930 `NYIS` demand
series the model uses as load**: `NG: SUN` is identically zero in every hour of
2023–2025 (nyiso-106 measured 8,760/8,760 zero hours and recorded the reason —
*"structurally absent (NY grid solar is overwhelmingly distribution-connected /
net-metered)"* — without connecting it to the supply side). The same MWh is
counted **twice**: once as reduced demand, once as supply.

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| model solar capacity | 1,645 MW | 2,566 MW | 2,930 MW |
| model solar energy | 1.94 TWh | 2.64 TWh | 3.55 TWh |
| **NYISO registered market fleet** (Gold Book III-2a) | **174.4 MW** | **573.4 MW** | **573.4 MW** |
| **NYISO published market-solar output** (III-2a Net Energy) | **0.23 TWh** | **0.50 TWh** | **1.08 TWh** |

Three independent NYISO instruments agree on the registered level: the III-2a
registry, the 2026 Gold Book (which confirms **no PV market generator entered
during 2025** — the same 15 units), and nyiso-106's own MIS P-63 daylight-bulge
decomposition (0.212 / 0.577 / 0.994 TWh).

**Why it lands on the failing year.** nyiso-126 measured h16–h18 as **70.6 % of
the 2025 signed C3a residual** and decile 10 as **138 %** of it (model $108.69 vs
actual $187.98); nyiso-127 measured the volume twin (ST_GAS −5.07, CT_PEAKER
−1.92 TWh in 2025). In JJA h16–h18 the model ran CT_PEAKER at **0.27 / 0.29 /
0.41×** measured while carrying **689 / 1,120 / 1,545 MW** of solar with no
counterpart in NYISO's published fuel mix.

## 2. The correction

`nyiso_solar_market_generator_basis`, default off, byte-identical off.
**Zero free parameters** — registry membership is an identity; three published
columns (zone letter, nameplate MW, in-service date), the existing A–K →
five-zone crosswalk, and the same month-of-commercial-operation ramp the EIA-860
path already applies. `n_residual` unchanged at 6.

**Independent level check, computed before the correction was built:** the
registry's own Net Energy over its own mid-year capacity gives **12.9 % (2023) /
13.9 % (2024)** — physical utility PV, within a point of the 0.133 the model's
(nyiso-75 donor-repaired) NYISO solar profile already carries. **The shape and
the CF level were already right; only the capacity basis was wrong.**

## 3. K6 FIRED — and it is not the mechanism's fault

PREREG §7 K6 requires the same-HEAD control to reproduce the keeper's C3a to
±0.2 pp. **It does not.**

| C3a | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| keeper `nyiso-125` (recorded) | +7.7 % | −0.8 % | **−10.2 % FAIL** |
| **same-HEAD control, identical recipe** | **+6.2 %** | **−1.7 %** | **−7.0 % PASS** |
| delta | −1.5 pp | −0.9 pp | **+3.2 pp** |

The control runs the keeper's recipe with **all 680 `scenario_config` fields
verified identical** (`_nyiso128_solve_ab.py --verify-only`). **The keeper's sole
FAIL is not present at current HEAD**: C3a-2025 re-solves from −10.2 % (FAIL) to
−7.0 % (PASS) with no mechanism change at all. The benchmark did not move
(actual 66.53 in both), so this is a **model-side** change from main's advance
and/or this container's from-scratch `data/clean` rebuild — not a scoring change.

**PREREG §8-1 is unconditional — any kill gate fires ⇒ no promotion — and it is
honoured here on a favourable result.** A gate that binds only when the answer
is inconvenient is not a gate.

This is an owner-disposition event of the same class as NYISO's recorded
2026-07-26 de-designation (*"former keeper no longer reproduces on main"*).

## 4. The A/B itself is valid, and is read

Both arms are same-HEAD, same recipe; **K1 confirms exactly one differing
`scenario_config` field**. What is invalid is any claim *relative to the keeper*.

| gate | result |
|---|---|
| **K1** no free parameter | **PASS** — sole delta `nyiso_solar_market_generator_basis` |
| **K2** no new unserved energy | **PASS** — zero slack in both arms, all three years |
| **K4** live, not inert | **PASS** — max zonal \|ΔLMP\| 100.5 / 97.3 / 283.0 $/MWh |
| **K5** seam does not absorb it | **PASS** — import p50 +52 / 0 / +42 MW; import energy +0.076 / −0.000 / +0.027 TWh |
| **K3** C1 does not regress | **PASS** — zero per-class C1 FAILs in either arm; no class leaves its band (contrast the nyiso-127 PAR arm, which failed K3 here with ST_GAS 2023 +3.63 TWh) |
| **K6** control reproduces keeper | **FAIL** — §3 |
| **K7** C7/C8 hold | **PASS** — C7 and C8 both PASS in both arms |

**Correction on the gate scoring, recorded because it changes what may be
claimed.** K7 was initially **unscored, not passing**: both arms read C7/C8
`SKIPPED` because their bundles carried no `legitimacy_diagnostics.json`. The
artifact was generated for both arms and K7 then scored PASS. `governance` reads
`UNATTESTED` in both arms (no `calibration_attestation.json` — neither arm is a
keeper), which is why both determinations are NOT-YET independently of C3c.

**K5 is the load-bearing check on the whole claim** and it holds: the removed
solar is replaced by **in-state thermal**, not by imports.

**P1 CONFIRMED — the summer peaking fleet is called.** JJA h16–h18:

| | 2024 | 2025 |
|---|---:|---:|
| CT_PEAKER | +69.8 MW | **+109.4 MW** |
| ST_GAS | +267.3 MW | **+365.4 MW** |
| CC_REGULAR | +117.1 MW | +142.2 MW |
| solar | −916.9 MW | **−1,217.7 MW** |
| import | +257.5 MW | +187.1 MW |

**C3a moves the predicted way, and the adverse case did not materialise:**
+6.2 → **+8.8** (2023), −1.7 → **+0.8** (2024), −7.0 → **−3.2** (2025). All six
PASS. 2025 improves 3.8 pp, 2024 improves 2.5 pp, 2023 worsens 2.6 pp but stays
in band — the pre-registered adverse case (2023 crossing +10 %) **did not**
materialise.

### Reported against interest, twice

1. **C3c REGRESSES.** 2023 goes **18 h → 22 h** against a measured 10 h
   (1.80× → **2.20×** over-produced), flipping **PASS → FAIL**; 2024 2 h → 3 h
   vs 12 h, still failing; 2025 21 h → 24 h vs 42 h, still passing. The arm
   over-produces the 2023 tail it was never aimed at.
2. **The §4 declared limitation bites.** The arm removes **2.80 TWh** of 2025
   solar where the registry's published output implies ~2.47, so ~12 % of the
   removal is over-removal in the tightening direction. On a linear attribution
   **~0.45 pp of the +3.8 pp C3a-2025 gain is UNEARNED**; only ~3.35 pp is
   attributable to the correction itself. This was required by the
   pre-registration before any result existed.

## 5. Disposition

The treatment is the structurally more faithful run (rule 14 input repair, zero
free parameters, three-instrument identification) and it moves the failing year
the predicted way, so on the owner's standing standard it **would** be a
promotion candidate. It is **not promoted here** because the incumbent's
headline defect evaporated on main for reasons nobody has diagnosed, and
promoting on top of that would silently bury a keeper-reproduction failure.

**Two owner decisions are now due, in this order:**

1. **The keeper-reproduction failure (§3).** Diagnose why C3a-2025 moved
   −10.2 % → −7.0 % on an identical recipe. Until that is understood, every
   NYISO A/B against this keeper has an unstable baseline.
2. **Then the promotion.** If the reproduction gap is explained and the control
   is accepted as the true current baseline, the treatment is the recommended
   keeper on rules 1/14 — carrying the C3c-2023 regression openly as the cost.

Matrix cell `vre_market_generator_basis` NYISO stays **O** — the mechanism is
LIVE and unrefuted, and no verdict is minted while the comparison baseline is in
question (rule 28 duty (b)).

**Rule 22:** 2023–2025 only. No out-of-training year was solved, scored, read or
registered; the holdout spend freeze was not touched.

Evidence: `results/calibration/_nyiso128_ab_gates.json`,
`PREREG-nyiso128-market-solar-basis-2026-08-05.md`,
`scripts/probes/_nyiso128_solve_ab.py`, `scripts/probes/_nyiso128_ab_gates.py`.
