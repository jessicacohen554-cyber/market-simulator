# FINDING — caiso-197 (lane 5): the six-plant cited-physical PS parameterization is **ACCEPTED on all six pre-registered gates** — zero MW added, zero fitted scalars, the unrestrained aggregate replaced by published plant physics; the arm moves C3a ANTI-favorably and is accepted anyway (the direction-hazard regime working as written)

**Pre-registration:** `PRECHECK-caiso197-ps-physical-2026-08-16.md` + the full
build, committed and pushed at `56ddf497a` BEFORE the lane-5 solve (parameter
table frozen; G-AGG/G-ZONE/G-CITE measured pre-solve by
`_caiso197_ps_citations.json`). Gate spec applied as written:
`GATESPEC-caiso195-ps-physical-2026-08-11.md` (owner ruling 7 **GO WITH SCOPE
RESTRICTIONS**, FINDING-caiso191 §3). Keeper UNCHANGED this lane. 2023–2025
only; markers and freeze untouched. Registered run:
**`2026-08-16-caiso-197-l5-psphys`** (NOT-YET, C6 UNATTESTED — standard
non-keeper A/B posture). Control shared with lanes 2/3
(`2026-08-16-caiso-197-l2-control`, BIT-ZERO vs the committed keeper).

## 0. Direction-hazard regime (verbatim from the GATESPEC, binding)

> The expected sign of this repair flatters C3a. C3a movement is therefore
> inadmissible as evidence for or against acceptance (rules 1, 13, 14). Acceptance is
> decided solely on the structural gates pre-registered below, authored by caiso-191
> before measurement. C3a is reported for transparency only. If gates pass and C3a
> worsens, the arm is still accepted (caiso-183 precedent). If gates fail and C3a
> improves, the arm is still rejected.

**Measured outcome, reported for transparency: C3a moved ANTI-favorably**
(+4.4/+11.7/+14.5 → +4.4/+12.8/+15.9 %). The clause operates exactly as
written: the gates pass, so the arm is accepted — the accurate cited physics
stays even where the fit worsens (rule 14; caiso-183/188/196 lineage).

**Single-mechanism statement (required verbatim):** The A/B delta is the
six-plant cited-physical PS parameterization; no other input differs.

## 1. Gate tally — 6/6 PASS

| gate | bar | measured | verdict |
|---|---|---|---|
| **G-CITE** | every parameter committed pre-solve with public citations, reproducible from the citations alone | The frozen table (`constants.CAISO_PS_PLANT_PARAMS`) reproduced value-by-value from the committed corpora by the pre-solve probe (`constants_match_citations: true`): Helms 930 MW pump / 200,424 MWh (PG&E's own deck, verbatim quote + Courtright 123,000 AF); Hyatt 387.0 / Thermalito 89.5 / Gianelli 375.8 MW (DWR B132-22 motor ratings 519k/120k/504k hp) with reservoir-derived energy bounds (B132-22 Tables 1-1/1-4); O'Neill 26.8 MW / 4,095 MWh (USBR EWA EIS Ch.16). Eastwood's pump/duration are the disclosed UNCITED components and take the unrestrained/incumbent defaults — nothing invented. | **PASS** |
| **G-ZONE** | mechanical geography only | `build_zone_lookup` output recorded pre-solve: all six plants resolve **NP15** — the zone axis is unchanged and no zone was chosen by this lane. | **PASS** |
| **G-NOSHAPE** | no time-profile input of any kind | The arm's diff is ONE bool (`caiso_ps_plant_params` absent→true — the control predates the field's registration; absence ≡ the default False by the cache-key identity). Every parameter is time-invariant plant physics; Hyatt STAYS IN the storage block as a static cited bound; the LP remains the unrestrained optimizer within the bounds. The caiso-141 §G wall untouched. | **PASS** |
| **G-AGG** | Σ per-plant generating capability = the EIA-860 aggregate; zero MW added | **EXACT**: armed Σ 2,077.6 MW = off Σ 2,077.6 MW (the aggregate's own EIA-860 nameplate rows re-attributed; per-month conservation by construction — same rows, same masks). | **PASS** |
| **G-DOF** | every parameter `measured` (cited); no fitted scalar; ledger does not increase | Built arm ledger **11/8 — unchanged**, zero PS rows (cited inputs are not free parameters); `PUMPED_STORAGE_DURATION_HOURS`/`PUMPED_STORAGE_RTE` byte-untouched for every other ISO; the table registered in config/constants with its matrix row in the same PR (28c). | **PASS** |
| **G-ENGAGE** | per-plant units present in the built fleet; LP differs from control | Fleet half (pre-solve probe): 6 armed units with the cited bounds on the right units. Solve log: "per-plant PS pump caps armed on 5 unit(s)" (Eastwood correctly absent — uncited pump ⇒ no cap row). LP half: prices change in **25,539 / 33,137 / 30,120 of 61,320 zone-hours**, class-hour dispatch moves up to **4,538 / 3,511 / 3,566 MW** — the single largest engagement of the campaign's three arms. | **PASS** |

Environment legs: seam caps 16055/16452/16148 logged; `hydro_ror_split=false`
disclosed; warm-start pinned off; arm solved after lane 3 (rule 12);
highspy 1.14.0 / python 3.11.15.

## 2. The fence discharge, restated (the grant's conditions — held)

* **caiso-140 §D/§G** (no re-testing ≤1.5 GW supply additions against
  C3a-2025): the arm adds **zero MW** (G-AGG exact) and its acceptance is
  C3a-blind — measured C3a moved ANTI-favorably and acceptance stands, which
  is the fence's own discharge demonstrated in data, not argument.
* **caiso-141 §G** (no fabricated shapes): the diff contains static cited
  bounds only; Hyatt keeps full storage-block membership with a cited
  pump-side motor rating whose channel application is tighten-only (its
  387 MW rating exceeds the EIA-860 PS-unit nameplate 293.1, so it clips —
  a disclosed no-op; Hyatt keeps full PS pump treatment, §4.2's conservative
  default with an airtight citation). No energy re-allocation, no schedule.

## 3. What the cited physics does to the LP (model artifacts only)

The aggregate's 10 h fleet-average energy assumption becomes per-plant cited
bounds spanning two orders of magnitude (Thermalito 4.5 GWh/54.8 h …
Gianelli 613 GWh — San Luis is a seasonal reservoir), and two cited
pump-side caps BIND (Helms 930 vs 1,053 MW; Gianelli 375.8 vs 424 MW;
−171.2 MW of fleet pump capability vs the incumbent). The LP responds at
scale: up to 4.5 GW of class-hour dispatch moves, and prices move in 42–54 %
of zone-hours. C3b worsens but PASSES every year (0.098/0.178/0.183 vs the
0.20 bar; control 0.077/0.155/0.176) — **no criteria-panel pass→fail flip**
(§5 silent; the movement is recorded for the composition rung's watch). C1's
only FAIL row remains the control's own 2023 CC_REGULAR (−4.44 → −4.63 TWh,
deeper but already-FAIL — not a flip; lane 2's object, and the composed rung
measures the joint state). C3a: +4.4/+12.8/+15.9 %, reported per §0.

## 4. Composition posture (Wave 2)

Lane 5's gates PASS ⇒ the arm enters the ladder at the final rung (… +L3 →
+L5). The composed rung's watch items, recorded now: C3b 2025 margin
tightened to 0.017 at this arm alone — the §5 flip protocol governs if the
composed rung crosses 0.20; and C1-2023 CC_REGULAR sits −4.63 here vs −3.94
on the lane-2 arm — the composed rung measures whether lane 2's healing
survives the joint state.

## 5. Artifacts

Registered: `2026-08-16-caiso-197-l5-psphys` (bundle
`results/calibration/caiso197_l5_psphys`: `legitimacy_diagnostics.json`,
built attestation ledger 11/8, `metrics.json`, hourly sidecars). Control
shared: `2026-08-16-caiso-197-l2-control`. Records:
`_caiso197_ps_citations.json` (pre-solve; citations + G-AGG + G-ZONE + fleet
half), `_caiso197_l5_gates.json` (G-ONEMECH + engagement; the expected-diff
encoding is [null, true] because the control's recorded config predates the
field — absence ≡ default False by the cache-key identity, disclosed).
Build: `caiso_ps_plant_params` + `CAISO_PS_PLANT_PARAMS` +
`StorageUnit.charge_power_cap_mw` + `caiso_ps_charge_caps` + loader branch +
matrix row + all six shard cells + 5 tests + two provenance corpora
(`pge-helms-ps-plant-2008`, `dwr-b132-22-swp-plants`), all landed at
`56ddf497a` pre-solve. Matrix duty (b): the `caiso_ps_plant_params` CAISO
cell moves **U → O** with this acceptance (K follows the Wave-2 §6
promotion if the final rung survives). Calibration-log entry in-session.
