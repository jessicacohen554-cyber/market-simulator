# PRECOMMIT — ERCOT-149 Phase 2: `ercot_dam_availability_gas_event_cap` (measured event windows cap the DAM COP restore on the DAM-covered gas classes)

**Date** 2026-08-01 · **ISO** ERCOT · pushed BEFORE the solve (rule-15/ercot145b
protocol; the ERCOT-148 template). Basis keeper
`2026-07-31-ercot148-dam-event-cap` (bundle `ercot148_dam_event_cap_arm`,
determination NOT-YET, fail set {C3a, C3b(2023-only), C3c, C7(2023-lignite
cv-leg)}, C6 ATTESTED+PASS, n_residual 6). Diagnosis:
`docs/DIAGNOSIS-ercot149-gas-cop-window-2026-08-01.md`; committed record
`results/calibration/ercot149_gas_outage_phase0.json`; probe
`scripts/probes/ercot149_gas_outage_phase0.py` (+ the reused
`scripts/probes/ercot148_availability_capture.py` for the seam proof).

## 1. The arm (single delta)

`ercot_dam_availability_gas_event_cap=true` off the keeper recipe — one new
default-off ScenarioConfig gate (cache-key-optional; default key byte-stable
at `0e9fce2fb55b889f`; matrix row added in the same PR, rule 26c). Semantics:
the SAME `min()` cap block ERCOT-148 armed, its class scope widened to the
DAM-covered gas classes (CC_REGULAR / ST_GAS / CT_PEAKER) — after the DAM COP
rescale, every scoped bin's availability is capped at the product of its
ARMED measured event-window factors (≥ 5-day CAMPD unit windows + ERCOT
plant-grain partial plateaus; short/unit-partial layers join only when their
gates are armed). One mechanism, one block, never a second cap layer
(rule 19). The COP overlay keeps its remove direction and every non-window
hour untouched; CT_PEAKER is in scope on principle and provably inert (no
windows by the detector's design). Zero fitted parameters — a precedence rule
between two already-armed measured instruments (rules 14/19). Full span
`--year 2023 2024 2025` in ONE invocation (rules 12/16; the ERCOT-148
chained-replay incident is the recorded counterexample), bundle
`ercot149_gas_event_cap_arm`, via `replay_keeper.py --set` off
`ercot148_dam_event_cap_arm`.

**Seam verification (no LP), done before this push (2024 captures,
flag-off vs flag-on off the keeper bundle):** non-scoped classes (COAL, CHP,
everything else) **byte-identical**; all 1,138 scoped gas tranches satisfy
`armed == min(base, event-window ceiling)` **exactly** (max |diff| 0.0); no
change outside windows; 466 gas tranches actually capped in-window;
CT_PEAKER byte-identical (inert as stated). The flag-off path logs the
keeper's own "40 COAL tranche(s) capped" through the widened code — the
coal-only arm is byte-identical after the refactor (the widened loop's
`(plant_code, plant_group)` key is the former `(plant_code, "COAL")` literal
for coal generators).

## 2. Expectation management (the lane's object, stated before the numbers)

The object is availability CORRECTNESS (rule 14): the keeper dispatches
4.27 / 5.93 / 4.14 TWh (2023/24/25) of CC_REGULAR + ST_GAS during committed
measured dead spans — capacity the CEMS record certifies produced nothing for
weeks, restored over the armed window layer by the DAM overlay's pin /
water-fill (diagnosis §3–§4: config-collapse train-aliasing, partial site
acceptance, true OFF-at-HSL, class water-fill). The C3a/C3b/C3c residual
stays attributed to RT scarcity formation (closed lane, ERCOT-144
attribution); any gate movement from correct windows is reported UN-TARGETED
(rule 1) and is never the promotion basis. If correct windows make a gate
WORSE, that is rule-14 territory: keep the accurate input, open the root
cause.

## 3. Ex-ante quantification and predicted directions

Phantom above the measured-window ceiling (the envelope the cap removes;
keeper payload): CC_REGULAR **4.116 / 5.195 / 3.870** TWh, ST_GAS
**0.158 / 0.735 / 0.272** TWh; mapped pin 1.42 / 3.42 / 2.22, unmapped
water-fill 2.86 / 2.51 / 1.92. Top plants (2024): Jack County 1.10,
Guadalupe 0.92, V H Braunig 0.64, Bastrop 0.30, Nueces Bay 0.28.

Honest per-direction predictions (model − actual, e923/bench basis):

- **CC_REGULAR class** (+0.0 % / +0.7 % / +1.3 % on the keeper): net move
  DOWN by **much less than the gross phantom** — windowed-hour dispatch
  re-splits mostly within the class (shoulder headroom is large); 2023 may
  cross to a small under. Worst case (zero intra-class re-dispatch) the class
  delta moves ≤ the gross phantom (≤ 5.2 TWh), inside the C1 band
  (min(2 % load, 8 TWh) / 3 pp).
- **ST_GAS class** (+24.8 % / +21.4 % / +20.1 % over): DOWN toward actual —
  |dev| IMPROVES (its phantom 0.16/0.74/0.27 is a fraction of its +3.7/+3.3/
  +2.4 TWh over-run).
- **COAL**: may pick up windowed-hour dispatch; the keeper's 2024 −8.9 %
  under may improve un-targeted. C7-2024/25 lignite legs must HOLD (guard).
- **Named plants toward CAMPD**: Nueces Bay (+63/+62/+69 % over) improves
  materially every year; Jack County 2024 (+3.7 %) → under; Bastrop
  (≈ exact) → small under. **Guadalupe 2023 (−18.7 % under already) goes
  FURTHER under — PRE-REGISTERED as the rule-14 compensating-error unwind**:
  its phantom (dispatch inside certified dead weeks) was masking the CC
  econ-band under-dispatch that is the ERCOT-138/139 object (its own lane).
  V H Braunig stays deeply under (offer-economics + the §6.3 remove-direction
  asymmetry, out of scope, recorded).
- **Prices**: removing phantom capacity in windowed (shoulder/winter-heavy)
  hours raises shoulder prices → C3a predicted to IMPROVE (less negative),
  un-targeted; C3b improve-or-held.
- **Scarcity formation**: windowed-out scoped-gas capacity on real event days
  (Jun-2023 ≈ 1.9 GW, Jan-2024 Heather 1.2–2.0 GW, 2024-05-08 9.4 GW,
  Aug-2024 1.8 GW, 2025 events 2.4–2.5 GW) means capping strengthens tail
  formation TOWARD actual; the Sep-2023 C3c days carry ZERO windowed gas, so
  no channel exists to move them either way. Peak window-envelope days are
  deep-shoulder (Apr/Nov, 17–21 GW) where real margins were wide — the
  actual system ran with that capacity out and produced no tails, so a
  correctly-margined model should not either; the spurious guard protects
  this.

## 4. Guards (pre-registered against the ercot148 promotion-note baselines)

| guard | baseline (2023/24/25) | rule |
|---|---|---|
| C3c actual→tail hours | 54 / 7 / 0 | NO DRAIN (the ERCOT-119 signature is the kill); ±1 threshold-straddling hour adjudicated hour-level per the ercot145b precedent |
| C3c spurious | 2 / 3 / 0 | must stay ≤ 2 / 3 / 0 (±1 straddle adjudicated hour-level) |
| C3a load-weighted | −34.3 / −10.4 / −11.6 % | predict IMPROVE (less negative), un-targeted; any material worsening (> 1 pp) escalates to hour-level attribution before promotion |
| C3b monthly NRMSE | 0.618 / PASS / PASS | predict improve-or-held; 2024 and 2025 stay PASS |
| C1 | 16/16, free 12/12 | HELD. CC_REGULAR may cross to a small under; ST_GAS improves; bands hold in the worst case (§3) |
| C2 | PASS | HELD (same per-class roll-up bands) |
| C7-2024/25 COAL_LIGNITE | both legs PASS | HELD (the cap does not touch coal availability; re-dispatch must not break the lignite diurnal legs — hard kill if either leg fails) |
| C4/C8 | PASS | HELD (no floor touched, no forced share added) |
| n_residual | 6 | MUST NOT RISE (zero fitted parameters added) |
| C6 | ATTESTED+PASS | governance block copied to the new bundle and attested honestly BEFORE the verdict run |

**LOYO:** zero fitted parameters (the cap has no level to fit — a precedence
rule between two committed measured artifacts) ⇒ structurally LOYO-exempt,
per-year guard table standing in (the ERCOT-145b/148 precedent).

**Decision rule:** keeper-or-rejected on the guard table + the owner's
standing in-session standard ("structural integrity outranks gate
regression", re-affirmed 2026-07-31). Registered on the dashboard either way,
matrix cell + calibration log same session (rules 15/26b).

## 5. Open owner rulings carried (surfaced, not decided)

(1) `gas_hh_monthly_shape` matrix row (26c); (2) per-gate dispositions of the
attributed gates; (3) `split_coal_tranches` delete-vs-inert;
(4) `ercot_offer_hrmult_ep_rebasis/_bands` matrix rows (26c); (5) Martin Lake
lignite class composition; (6) authorization for the ERCOT-147 three-part CT
reopen intake (matrix §5.1 item 8). (7) the gas-side COP-vs-window collision
— **this lane's object: measured MATERIAL and adjudicated a DEFECT of the
ERCOT-148 class (diagnosis §5); the arm result is surfaced through this
precommit + the registered run for the owner's disposition of the keeper**.
(8) the DAM deriver rating-basis gap for all-year-OUT sites (ERCOT-148
§6.2). NEW from this lane: (9) the DAM deriver `_site()` cross-train
collapse + the gas crosswalk's partial site acceptance (diagnosis §6.1–6.2 —
a rule-23 derive/crosswalk lane that would re-derive all three grains and
re-gate every armed DAM keeper); (10) the pin's remove-direction
over-removal at partial-coverage plants (diagnosis §6.3, V H Braunig 2025).
