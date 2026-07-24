# caiso-119 A/B — PRE-REGISTERED gates (written before either arm finished)

**Arms** (same HEAD `150f8b3`, same box, three years one bundle):

- `caiso119_base_A` — byte-faithful `replay_keeper` of the
  `2026-07-23-caiso-netrev-margin-keeper` recipe, no delta.
- `caiso119_minload_B` — the SAME recipe plus ONE delta:
  `caiso_ra_min_load_frac` 0.26 → **0.570**.

**Why 0.570 (rule 13/18 — measured, not fitted).** CEMS unit-level, CAISO bench
fleet: among hours a unit is FULLY online (`opTime == 1.0`), the per-unit 5th
percentile of `grossLoad / pmax`, capacity-weighted p50 across CC units with
≥500 operating hours = **0.565 in 2023, 0.570 in 2024, 0.570 in 2025** — stable
to within 1 % across the three years; the delta uses 0.570.
ERCOT's independently-derived analogue (60-Day DAM disclosure committed
LSL/HSL cap-weighted p50, `ercot_gas_bridge_min_load_frac`) is **0.574**. The
keeper's 0.26 is below any physical CC turn-down and below the code default
0.40. Derivation: `scripts/probes/_caiso119_committed_minload_derive.py`.

**Reference actuals** (CEMS gross, the surviving basis per
`FINDING-caiso119-gas-basis-adjudication-2026-07-24.md`; gross is an UPPER
bound on grid-delivered because it carries parasitic/steam-host load):

| year | belly (hod 10–15) | evening (17–21) | annual | belly/evening |
|---|---|---|---|---|
| 2023 | 5,087 MW | 9,749 | 7,176 | 0.52 |
| 2024 | 4,435 | 8,444 | 6,324 | 0.53 |
| 2025 | 3,535 | 6,627 | 5,262 | 0.53 |

BASE arm expectation (from the keeper sidecar): belly 4,147 / 3,635 / 2,959;
belly/evening 0.40 all years; annual ratio to CEMS 1.03 / 1.03 / 0.99.

---

## PRIMARY (what the delta is for)

**P1 — belly gas closes toward measured.** The BASE belly-gas gap to CEMS gross
is +940 / +800 / +576 MW. PASS if the MARGIN arm closes **≥ 40 %** of that gap
in at least two of three years.

**P2 — the duck stops being too deep.** `belly/evening` rises from 0.40 toward
the measured 0.52–0.53 in all three years.

## GUARD (must not break — a rule-1 keeper is structural, not fitted)

**G1** C1 fuel-mix: every class that PASSES in BASE still PASSES.
**G2** C3a `price_mean`: STAYS PASS in all three years.
**G3** C3b `price_shape`: STAYS PASS in all three years.
**G4** C5a CO₂: improves or is neutral (it is a standing FAIL; it must not worsen).
**G5** C8 forced-energy (D-2): CC_REGULAR either stays inside the 30 % merchant
budget, or clears the rubric-v2.2 grounded-above-budget path — D-4 off-window
binding clean **and** D-1 diurnal shape gates pass. Scored from
`legitimacy_diagnostics.json`, never asserted.

## KILL (any one of these and the delta is rejected, whatever it does to the fit)

**K1 — OVERSHOOT.** Belly gas exceeds the CEMS **gross** level by more than
+10 % in any year. Gross already over-states grid-delivered gas, so exceeding it
means forcing phantom generation — the caiso-118b failure mode this lane exists
to avoid.
**K2 — annual volume.** Total gas TWh moves more than **+7 %** above the CEMS
basis in any year (the EIA-923 guardrail that killed caiso-45).
**K3 — price regression.** C3a or C3b flips PASS → FAIL in any year.
**K4 — evening damage.** Evening (17–21) gas, already ~+1 GW too high in BASE,
rises further.

## Disposition rules

- All PRIMARY met + no GUARD broken + no KILL → candidate for promotion, then
  leave-one-year-out within 2023–2025 (rule 22) before the keeper moves.
- PRIMARY partially met, no KILL → register as a probe, keep the measured value
  (rule 14: the accurate input stays even if the fit is worse) and open the
  root-cause lane for the remainder.
- Any KILL → the delta is rejected as sized; the measured 0.570 is still the
  correct physical value, so a KILL means the BRIDGE's binding scope (which
  plant-hours it floors), not the min-load level, is the defect — that becomes
  the next lane. **A KILL must not be answered by tuning 0.570 back down**
  (rule 13/18/25: that is exactly how 0.26 got there).
