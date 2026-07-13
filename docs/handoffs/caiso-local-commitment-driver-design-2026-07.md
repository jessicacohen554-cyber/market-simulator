# CAISO local-commitment driver — design for owner review (2026-07-12)

> **STATUS (2026-07-13, caiso-81): REFUTED AT THE ESTIMATION STAGE — never
> implemented, no solve run.** The §2 response curve fails its own §4 LOYO
> pre-commitment before any LP: every candidate driver (the filed evening
> net-load ramp and two storage-conditioned variants) overpredicts held-out
> 2025 pocket committed energy by +375 % to +3,600 % — commitment collapsed
> ~80-97 % at *equal-or-steeper* ramps (a regime break coincident with the
> pocket battery build and the 2025 slice-of-day RA reform), the same
> not-year-stable signature that rejected the NYISO ST_GAS drag alternative.
> Adjudication: `scripts/derive_caiso_local_commitment.py`; full record:
> `results/calibration/FINDING-caiso81-local-commitment-driver-refuted-2026-07-13.md`.
> The CT_PEAKER deficit stays OPEN pending a measured per-year
> local-commitment source (DMM ED/min-online volumes by area) or an
> RA-regime field. Nothing below is enabled.

The caiso-79 STEP-0 fork deliverable
(`results/calibration/FINDING-caiso79-step0-greaterbay-bind-2026-07-12.md`
§3): the Greater Bay import cap was measured non-binding, so the CT_PEAKER
evening lane cannot be closed by topology. What remains — per caiso-71 §3,
now with the import-cap alternative eliminated by measurement — is that real
CAISO pocket CTs are **committed locally** (local RA must-offer + RMR +
exceptional dispatch + minimum-online constraints for contingency
positioning), a mechanism the pure-LP merit order cannot produce because the
cheapest CT offer sits $43–82/MWh above the marginal CC (caiso-78 STEP-0).
This document is the rule-12-compliant design for that mechanism, filed
BEFORE any solve. **No implementation exists yet; nothing here is enabled.**

## 1. The mechanism (one sentence)

A per-pocket evening min-gen floor on the *named* LCR-area CT units whose
committed MW is a measured function of the pocket's net-load ramp — the
model's analogue of the local commitment CAISO actually performs, sized from
CEMS starts conditioned on a forward-native driver, never from a residual.

## 2. Rule-12 declaration (window, driver, forward story)

* **Driver (external):** the pocket's evening net-load ramp — pocket load
  share × (zone net load at HE18–21 minus its midday trough), a pure
  function of model demand + solar inputs. Physically: the steeper the
  pocket's own duck ramp, the more local capacity CAISO positions online for
  N-1-1 security inside the pocket (LCT criteria), and the DMM-documented
  exceptional-dispatch/minimum-online practice follows exactly that need.
* **Window:** HE15–23, the measured window: CAMPD GB CT is ON in 22–43 % of
  evening hours (2023→2025) with p90 evening output 402/309/87 MW, and
  near-zero overnight (fast-start LM6000/LMS100 physics, min-down ≤ 2 h —
  rule 18 forbids bridging them beyond it, and this floor never does: it is
  a within-window commitment, not an overnight bridge).
* **Forward story:** the commitment share is a fitted-once *measured
  response curve* `share_committed(ramp decile, season)` estimated from
  CAMPD 2023–2025 unit-hours conditioned on the driver — the same
  rule-13-admissible construction as the forward CO₂-rate estimator and the
  CT measured-runs lever: in a forecast year it REGENERATES from forecast
  load/solar (more solar → steeper ramp → more local commitment; pocket
  load decline → less), and it would have produced different values under
  different 2023–2025 conditions. It is NOT a pin to observed CT MWh: the
  curve maps driver→committed-MW-online; the LP still dispatches
  economically above the floor.

## 3. Scope and named units

Pockets = the LCR areas with committed membership crosswalks
(`data/raw/reference/lcr_area_membership_CAISO.csv`): **Greater Bay**
(Marsh Landing, Mariposa, Gilroy Peaker, the Lambie trio, Riverview — 1,362
MW), and — only if their zonal topology (which already exists) still leaves
a measured CT deficit after the honest-bench re-tune — LA Basin / SDGE
CT_PEAKER members. The floor binds per pocket, mapped onto the pocket's
plants inside their model zone (GB inside NP15 — no zone split; the floor is
plant-scoped, so no topology change).

## 4. Governance pre-commitments

* **Rule 19 (one mechanism per phenomenon):** the only mechanism that floors
  CAISO CT today is `ra_mustoffer_bridge` at 0.1–0.3 % of class energy
  (D-2). This driver REPLACES nothing and stacks with nothing: CT floor
  provenance would read `local_commitment_<area>` in the D-2 attribution,
  and the RA bridge's CT contribution must not grow.
* **Rule 12 / D-4:** a cited `D4_WINDOWS` entry in
  `scripts/legitimacy_diagnostics.py` (window HE15–23, driver: pocket
  net-load ramp, evidence: CAMPD GB CT hod profile + this design doc) lands
  IN THE SAME PR as the mechanism, so off-window binding fails D-4 from the
  first bundle.
* **Rule 20 (registry):** one `ScenarioConfig` field
  (`caiso_local_commitment`, default off) + the response-curve artifact
  under `data/raw/reference/` with its derive script; no env knobs, no
  per-plant literals in code.
* **Rule 23:** the response curve re-derives only on new CAMPD vintages.
* **C8 budget:** CT_PEAKER is below the 2 % materiality line (reported, not
  gated), but the D-1/D-2 diagnostics must still show the forced share and
  the shape match — the pre-registered targets are the measured ones:
  NorCal CT evening 14 → ~300–400 MW, D-1 CT profile advancing into
  h15–18, the 2024/25 C3c tail forming (or honestly failing to form —
  a local commitment floor does NOT create local prices without a binding
  constraint, so the C3c payoff must be re-assessed under the honest bench
  before this lane is credited with it).
* **LOYO:** the response curve is estimated on 2023–2025 pooled; the probe
  is scored leave-one-year-out before any promotion (not LOYO-exempt — the
  curve is fitted, unlike the caiso-78 code fix).

## 5. Decision requested

Owner review of §2's driver choice and §4's pre-commitments before any
implementation/solve. Alternative considered and NOT proposed: an
import-limited GREATER_BAY zone (refuted ex-ante, FINDING §2); a hard-coded
evening CT floor with no driver (fails rule 12 by construction). Note the
sequencing dependency: the honest-bench C3a/C1 re-tune (caiso-79 plan §4)
may move the CC/CT margin and should land first — this driver sizes against
whatever CT deficit survives it.
