# FINDING — ercot-173: the 2023 "excess cheap depth" premise is REFUTED at the aggregate (Phase 0, FILED-REDIRECTED), and the ercot-172-specified C1+C2 ceiling reconciliation, built and solved once, fixes the 2024 object exactly as attributed but is REJECTED-AS-ARMED — the blanket min() re-admits 1–2.7 TWh/yr of the coal phantom the ERCOT-148/149 precedence removed

**Session ercot-173, 2026-08-06.** Charter: the owner directive (THE OBJECT IS
2023 LMP; no fleet/volume lanes; no coal offer work; ONE LP run). Decision
rules, licensing bars, gate assignment and predictions pre-registered and
pushed BEFORE any measurement
(`docs/PRECOMMIT-ercot173-2023-depth-and-ceiling-reconciliation-2026-08-06.md`);
the kill gates are PRECOMMIT-ercot172 §5 inherited verbatim, not renegotiated.
Keeper **UNCHANGED** at `2026-08-05-run168b-year-curves`. Runs registered
(rules 15/16, full span in one bundle each):
`2026-08-06-run173a-reconc-control` (A/B base) and
`2026-08-06-run173b-event-cap-reconc` (**REJECTED-AS-ARMED**).

## 0. The owner's object first — C3a-2023

On the load-weighted hub basis of the standing record (keeper −29.88 %):

| | control (A) | arm (B) | Δ |
|---|---|---|---|
| **C3a-2023 (lw hub)** | **−28.48 %** | **−29.71 %** | **−1.23 pp** (more negative; inside the pre-registered P-C3a-2023 band "0 to −1.5 pp") |
| C3a-2024 (lw hub) | +10.45 % | **+3.05 %** | −7.40 pp (the fabricated maintenance spikes collapse) |
| C3a-2025 (lw hub) | −0.76 % | −3.17 % | −2.41 pp (the coal-flood side effect) |

**Limb 1 was never the 2023 lever and the pre-registration said so.** The 2023
lever the handoff chartered (limb 2, the depth correction) was adjudicated by
Phase 0 under its own pre-registered rule and did NOT land — see §1. The
−1.23 pp is the predicted small cost of clearing over-tightened scarcity hours;
per rule 1 `[R-STRUCT]` the arm is judged on structural fidelity and its
pre-registered gates, which is where it fails (§2).

## 1. Phase 0 — the 2023 depth object: **FILED-REDIRECTED**

Record: `results/calibration/ercot173_depth_phase0.json`; probe
`scripts/probes/ercot173_depth_phase0.py`; no LP. Licences: **L1 corpus
1.0000** (all 160 tail/shed hours resolved over all 12 delivery-2023 months),
**L2 COP 0.9675** per class (bars 0.90). The pre-registered decision rule
fired branch 2:

* **X/M p50 = −1.21** on the 123 missed >$200 hours (−8.05 on the 61 actual
  >$1000 hours) against a **+0.60** actionability bar. The model's sub-$200
  supply (V_m 55.2 GW mean) is **LESS** than what the market itself offered
  below $200 at those same hours (V_r 56.5 GW) — **the model does not carry
  excess cheap depth at the missed hours in aggregate; it carries a deficit.**
* Per class (mean MW over H123): the CC availability face vs the COP
  declaration is REAL — A_model 31.7 GW vs A_mkt 25.1 GW, **ΔA_CC +6.6 GW**
  (the ercot-163/170 headroom object at class grain) — but it is offset by
  the model being **−2.1 GW TIGHT on CT** (A_model 7.4 vs A_mkt 9.5; the
  ercot-172 R-term's sign, reproduced) and **fully neutralized on the offer
  face**: the market's SCED-online sub-$200 offered CC (29.1 GW) matches the
  model's (29.6 GW) almost exactly. A cross-instrument wedge is disclosed:
  SCED online sub-$200 CC exceeds the COP class live MW by ~4–5 GW (W_r_CC
  < 0), so the COP-based ΔA overstates the model-vs-SCED wedge.
* **The re-pointing.** Reality cleared p50 $462 in hours where ≥56 GW of
  sub-$200 offers were on the books — so the >$200 formation at the missed
  hours is NOT a supply-curve-crossing phenomenon that removing model depth
  can reach. What separates the offered curve from the cleared price at those
  hours (SCED ramp/HDL limits, AS holdback, deliverability at 5-min grain,
  and the ledgered storage equilibrium conduct — the C3c model-class caveat's
  very basis) is not represented by any committed instrument as a zero-DOF
  correction. **No limb-2 correction exists on this record; none was built**
  (the hard fences stand: no per-hour telemetered-HSL cap, no aggregate cap,
  no storage offer surface).
* **(a) the ceiling, named:** the model's marginal tranche in the missed
  hours is ordinary mid-merit gas — modal marginal class CT (56 hours) / CC
  (49) / ST_GAS (15), b* ≈ the load-weighted price.
* **(c) the four phantom shed hours:** Jun-20 17:00 is **SAME-DEFECT** as
  ercot-172 (E 1.21× shed; J K Spruce product-ceiling 0.3855 vs same-hour
  CEMS 0.5563, COP 0.5197). The three August VOLL evenings are **NOT** (E =
  0.07× / 0.00× / 0.15× shed) — their tightness is not an event-cap artifact.

## 2. Limb 1 — built, solved once, **REJECTED-AS-ARMED**

**Mechanism** (`ercot_dam_availability_event_cap_reconciliation`, one gate,
default off, zero fitted scalars; matrix row in the same PR): C1 gives
`partial_outage_derate_factors` the `(oris_code, plant_group)` grain its
extract carries, in both ERCOT consumers; C2 composes the event-cap ceiling's
armed measured layers by `min()` instead of the product. **Seam proof, run
before the solve, all PASS**: SP-1 arm == `min(B, ceil_min)` exactly on every
layered scoped tranche (max |Δ| 3.0e-08, 468/506 tranches, 2023/2024); SP-2
out-of-scope byte-identical; SP-3 C1 provably inert on the current bins sheet
(P-C1-INERT confirmed — the whole measured movement is C2's). Pre-registered
2024 prediction confirmed at the seam: **+1,118.8 MW** restored at h2827
(≥ shed 565.1 → clear) and **+353.3 MW** at h3067 (< 550.3 → shrink).

**The 2024 object behaves exactly as ercot-172 attributed.** A/B (same-HEAD
pair, standing span-check conventions):

| gate (inherited verbatim) | result | detail |
|---|---|---|
| G-BIT | **N/A (declared pre-solve)** | year-agnostic rule → G-SPAN |
| **G-SHED** | **PASS** | 2024 shed 2 → 1 (2024-04-28 CLEARS, 2024-05-08 persists — both as predicted); no year rises (2023 5→5, 2025 0→0) |
| **G-SPUR** | **PASS** | spurious falls every year: 10→9, 13→10, 1→0 |
| **G-DOF** | **PASS** | zero new fitted scalars (boolean gate) |
| **G-D2** | **PASS** | D-4 FAIL rows identical A↔B (pre-existing keeper condition, CT_PEAKER reliability-floor off-window; no arm-caused crossing) |
| **G-SPAN** | **FAIL** | class annual energy far past the 0.5 % band: 2023 COAL_PRB +1.9 %, CT_PEAKER −3.4 %, ST_GAS −1.8 %; 2025 COAL_PRB **+5.1 %**, COAL_LIGNITE +3.2 %, CT_PEAKER **−10.4 %**, ST_GAS −4.5 % |
| **G-C3c** | **FAIL** | model >$200 tail counts move AWAY from actual: 2024 26→14 (actual 53), 2025 3→0 (actual 31), 2023 66→64 (actual 181) |
| **G-COAL148** | **FAIL** | coal dispatch above the incumbent PRODUCT ceiling rises **+0.98 / +1.95 / +2.73 TWh** (2023/24/25) vs the +0.5 TWh bar — scored per plant from the bundles' own dispatch parquets against the loader product ceiling (the 4.36/4.98/5.01 TWh comparability basis) |
| LOYO | N/A | parameter-free rule; per-year deltas reported in its place |

Also measured on the pair: NRMSE-2024 3.00 → **2.26** (the C3b-2024 band-cross
root improves exactly as expected), 2024 spike-day day-mean |error| **382 →
120** and **268 → 227** $/h; NRMSE 2023 2.81→2.83 and 2025 0.94→0.95 (slight
degradations).

**Failing any live gate ⇒ REJECTED-AS-ARMED, as pre-registered. Three fail.**

## 3. The structural reading (rule 1), and the named successor

The measurement is decisive in BOTH directions: at the two ercot-172 shed
hours the double-count is real and its removal restores exactly the predicted
capability and clears the fabricated shortage; fleet-wide, the blanket `min()`
re-admits 1–2.7 TWh/yr of coal above the product ceiling and floods 2023/2025
with cheap in-window coal (+2–5 % class energy), moving every year's tail
formation away from actual. These two facts reconcile only one way: **the
`window` and `partial` layers measure the SAME units' downtime at some
overlaps (the ercot-172 named plants — there `min()` is right and the product
double-counts) and DIFFERENT units' downtime at most others (there the
product is right and `min()` under-removes).** A composition-wide fix cannot
be correct; the correction must be **unit-attributed**: the plant-grain
partial extract needs to carry which units its plateau belongs to, so the cap
can `min()` where the layers share units and multiply where they are
disjoint. That is a derive-construction change
(`scripts/data/derive_partial_outages.py` grain, rule 23 — needs its own
charter and owner adjudication) and is the **named successor**. Until it
lands, the incumbent product ceiling stays armed — G-COAL148 did its exact
job: the ERCOT-148/149 adjudication is reconciled, never repealed.

## 4. The ercot-167 SOC-reserve re-gate (re-score, not re-arm)

Scored on the pre-registered RG definitions (`ercot_storage_as_soc_reserve`
stays armed in both A and B; nothing built):

* **RG-1 (was G4-2024): CLEARS on the arm** — both spike days' error falls,
  C3a-2024 improves −7.8 pp, G-SHED holds. The kill's named root (the
  maintenance-season fabricated spikes) is corrected with the SOC reserve
  armed.
* **RG-2 (was G3-2025):** 2025 spurious 1 → 0 and the named hour (2025-10-21
  19:00) is not spurious on the arm — though by under-shoot ($249.6 → $109.1
  vs actual $191.6), with the year's last 3 tail hours lost (G-C3c's 2025
  leg).

**But the arm is rejected, so nothing lands**: the reopen condition of
`FINDING-ercot167` §3 ("after the 2024 defect's fix LANDS") remains unmet.
What this re-score establishes is that the kills DO clear when the 2024
ceiling defect is corrected — the unit-attributed successor, if it lands and
survives its gates, discharges the re-gate.

## 5. Disclosed incidents and drift (reported, not decided)

* **The keeper does not reproduce at current main.** The same-recipe control
  replay reads C3a-2023 −28.48 % lw-hub vs the committed −29.88 %, 2023
  spurious 10 vs the ledgered 3, 2023 model tail 66 vs 61, and a FIFTH 2023
  shed hour (4098 = Jun-20 18:00) the committed keeper does not have; 2024
  spurious 13 vs 7. This is the nyiso-128 K6-class condition measured on
  ERCOT (main moved under the keeper — the dc10345c→82765525 span touches
  `model/lp/rows.py`, `runner.py`, `policy/rps.py` — plus in-container
  regenerated clean inputs). Every gate above is scored on the same-HEAD A/B
  pair, so the mechanism deltas are clean; the keeper-reproduction question
  is its own lane and is surfaced here, not adjudicated.
* **One control solve was discarded unregistered**: the first control began
  before an owner-directed mid-session rebase and the tree moved under it
  (2024/2025 inputs load lazily), so it was not same-HEAD with the arm; it
  was quarantined to the session scratchpad and re-run at HEAD. The owner's
  one-LP-run directive was honoured for the ARM (solved exactly once); the
  control replay ran twice for pair integrity.
* The ledgered spurious/tail counts (3/7/1, 61/25/3) reproduce exactly under
  the standing `_ercot89_span_check` conventions on the committed keeper
  sidecars; the same conventions are used here.
* Pre-existing test failure `NuclearUnitAvailabilityTest::test_unknown_iso_degrades_to_empty`
  verified pre-existing by stash (fails on unmodified code).

## 6. Governance

Rule 15/16: both runs registered, all three years in one bundle each; top-15
retention auto-pruned `2026-08-01-ercot149-gas-event-cap` and
`2026-08-01-ercot150a-control-zerodelta`. Rule 22: 2023–2025 only; no holdout
touched. Rule 23: no derive re-run; the frozen extracts read as they stand
(the successor's grain change needs its own charter). Rule 24: the new gate
is a registered `ScenarioConfig` field, cache-key-dropped at its default,
recorded in both bundles' `run_config.json`. Rule 25: ERCOT-scoped. Rule 27:
every push blob-verified. Rule 28(b)/(c): the new field's matrix row landed
in the same PR as the field; §5.1 item 16 stamped; the
`ercot_dam_availability_event_cap_reconciliation` cell carries verdict **R**;
both event-cap cells re-stamped with the outcome; the
`ercot_storage_as_soc_reserve` cell carries the re-gate result.
`check_mechanism_matrix.py` exit 0.

**DO-NOT-REDO honoured in full** — no coal offer lane touched (the only coal
touched is availability at scarcity/shed hours, the price path); no storage
offer surface; no aggregate cap; no per-hour telemetered-HSL cap; the
West/Panhandle topology stayed closed; `ercot_storage_rt_offer_surface` stays
R; the CC-headroom crosswalk stays FILED-UNLICENSED (its extreme-hour
class-aggregate face is what Phase 0 measured and re-pointed).

**Carried forward, surfaced NOT decided:** (1) the unit-attributed partial
extract (the §3 successor — the only admissible route left to the 2024
ceiling defect and the ercot-167 re-gate); (2) the keeper-reproduction drift
at HEAD (§5); (3) Phase 0's re-pointing of the 2023 tail object to the
offered-vs-deliverable wedge at SCED grain (no committed instrument yet
licenses a mechanism); (4) item 11's crosswalk half stays FILED-UNLICENSED,
with the Phase-0 class-grain measurement (ΔA_CC +6.6 GW vs COP, −2.1 GW CT,
the SCED-vs-COP 4–5 GW wedge) as new input.

**Not a keeper candidate.** Three pre-registered gates fail, and unlike
ercot-167 (kills localizing to a separate defect) these regressions are the
arm's own fleet-wide over-restoration; G-COAL148 — the gate that exists
precisely to protect a prior owner adjudication — fails at 2–5× its bar in
every year. The recommendation is AGAINST promotion; the structural content
(the 2024 repair) is real but needs the unit-scoped form.

**Next shorthand: ercot-174.**
