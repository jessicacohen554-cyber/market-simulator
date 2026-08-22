# PREREG nyiso-149 — the CHP lay-up duty CURVE (graded successor to the rejected single-band split)

Session nyiso-149, 2026-08-22. Committed and pushed BEFORE any arm solves.
Charter: nyiso-148's Job-2 successor (`RESULT-nyiso148-chp-layup-duty-2026-08-21.md`
§4: *"the identification the successor needs is a price-conditional on-share,
not a band level"*), gated behind the Job-1 benchmark ruling
(`FINDING-nyiso149-bench-root-cause-2026-08-22.md`), which is LANDED: the
authoritative benchmark is the regenerated (measured-BTM) one, and the
nyiso-149 pin makes it byte-stable against any registering run's flags — the
moving-target objection to re-calibration is closed.

**Keeper at HEAD: `2026-08-19-nyiso-146c-state-scoped` (NOT-YET, C1-2024
CC_REGULAR). Holdout spend freeze ACTIVE; years 2023/2024/2025 only, one
bundle per arm (rule 16); years sequential, arms sequential (rule 12).**

---

## 1. THE IDENTIFICATION (already derived and FROZEN before this prereg)

* **Phase 0** (`scripts/probes/_nyiso149_chp_duty_curve_phase0.py`,
  `_nyiso149_chp_duty_curve_phase0.json`) — mechanism-blind: CAMPD plant gross
  × own-model-zone MIS RT LBMP, pooled 2023–2025, for the FROZEN 7-plant
  census (membership NOT re-derived, rule 23). Measured: the on-share is
  strongly GRADED and monotone in own-zone price for every plant (e.g.
  Oswego s(lo/mid/hi) = 0.036/0.161/0.437 at price bands <p40/p40–p80/≥p80),
  and the envelope availability tracks the metered live-hour share within
  ~0.02 for six of seven plants (Lockport 54041 the exception: ~1.0 available
  vs 0.12–0.44 live — its lay-up is nowhere in the availability record).
* **The artifact** `data/raw/_processed-legacy/chp_duty_curve_NYISO.csv`
  (`scripts/data/derive_nyiso_chp_duty_curve.py`): per census plant,
  `pct_econ = 100·s_mid·L·HSL/pmax` and `pct_peak = 100·(s_hi−s_mid)·L·HSL/pmax`,
  with the on-shares measured **conditional on envelope-live hours** (the same
  frozen `campd-unit-outages-NYISO.csv` windows the recipe applies) so the
  envelope and the offer never double-count the same mothball spells (rule 19)
  — for Lockport, envelope-live = all hours and the offer carries the whole
  duty; for Selkirk, the envelope carries the spells and the offer only the
  residual conduct. Composition-correct by construction, plant by plant.
* **DOF ledger (rule 21): zero free parameters.** Membership frozen
  (census); HSL and pmax are the census's own frozen fields; the p40/p80
  band quantiles were declared in the committed phase-0 probe before this
  mechanism existed and are not swept; offer LEVELS are the class curve's
  existing identified band multipliers — no new price constant anywhere.
* Rule 13: every statistic regenerates for any vintage from CAMPD + MIS LBMP
  + the outage extract, and responds to changed conditions (a plant returning
  to service raises its own measured duty; a dearer year raises the bands'
  absolute price levels with the zone distribution).

## 2. THE MECHANISM (built and default-off before this prereg; committed with it)

`ScenarioConfig.chp_layup_duty_curve` (default False; mutually exclusive with
`chp_layup_duty_split`, enforced at the consumption seam — rule 19). A census
plant offers `pct_econ` of model capacity at the class ECON band and
`pct_peak` at the class PEAK band, and the REMAINDER IS WITHHELD from the
offer entirely — energy and reserves (`grid_cap` shrinks to the offered
total): the measured "never seen at any price" share; a mothballed train does
not return for a price spike. Wired at **all three seams**, the load-bearing
`assembly.py::bins_to_fleet` override at the **CAP level** (the econ residual
would silently re-absorb a pct-level withhold — the nyiso-146b/148 seam
defect, third recurrence class, this time pinned by unit test
`tests/iso/nyiso/test_chp_layup_duty_curve.py` BEFORE any solve), plus the
`fleet_to_bins` frame and the `offer_curves` dashboard mirror.

## 3. ARMS (solved in this order, years sequential within each)

* **BASE** — `--replay-bundle results/calibration/nyiso147_armA_recipe`
  (keeper recipe + `nyiso_chp_btm_measured`), re-solved at this HEAD.
  Expected **bit-identical** to the registered `2026-08-20-nyiso-147a-chp-btm`
  (max |Δprice| = 0 across every zone-hour of all three years, the nyiso-148
  precedent) — which doubles as the end-to-end proof that BOTH of this
  session's code changes (the Job-1 `btm_bench_twh` column and the whole
  duty-curve machinery) are byte-inert at their defaults. If the identity
  holds, the base is NOT re-registered (its results are already on the
  dashboard; a twin spends a retention slot for no information).
* **ARM F** — the same recipe + `chp_layup_duty_curve=True`. Single delta.

## 4. GATES (pre-declared; scored against the AUTHORITATIVE benchmark)

| gate | bar |
|---|---|
| **F-K1 exactness** | the arm's `run_config.json` differs from the base's in exactly one field: `chp_layup_duty_curve` |
| **F-K2 liveness** (band composition, never a price delta) | every census plant enters the LP with committed = 0, peak ≈ `pct_peak`·pmax and offered total ≈ `(pct_econ+pct_peak)`·pmax (±0.1 MW); **zero** non-census CHP plants change tranche composition |
| **F-K3 graded conduct** | per plant-year, model CHP-class energy vs the plant's CAMPD-gross meter: meter ≥ 20 GWh → multiple ∈ **[0.25, 2.5]**; meter < 20 GWh → abs gap ≤ 40 GWh. PLUS the graded signature: cohort total model energy is HIGHEST in 2025 (the metered ordering). ARM D failed 9 plant-years below 0.25× and Lockport-2025 at 3.96×; this gate is the arm's reason to exist |
| **F-K4 conduct rows** | zero NEW failing D-1 / D-2 / D-4 rows vs the base |
| **F-K5 criteria** | C1 grid-mix PASS for every gated class in all three years (CC_REGULAR-2024 above all — the keeper's blocking failure); no criterion that PASSes on the base flips to FAIL on the arm |
| **F-K6 (REPORTED, never gated)** | 2025 system lw recovery vs the base's −12.2 %, C3a/C3b-2025, C8/ST_GAS-2024 forced share. nyiso-148 §3 PROVED the 2025 level is not a CHP object ($1.50 of $8.07 recoverable; the $6.57 remainder is the owner card's offer-level object) — imposing a recovery bar here would contradict that finding, so the D-K6-style bar is deliberately ABSENT |

Verdicts are read from the committed scorer over committed artifacts
(`calibration_verdict.py`), the D-tables from `legitimacy_diagnostics.py`, and
the A/B numbers from a committed gates probe
(`scripts/probes/_nyiso149_duty_curve_gates.py`, written before the arm is
scored). The bench parts the registration re-renders are expected to be
BYTE-IDENTICAL to the committed authoritative ones (the Job-1 pin, live
end-to-end check).

## 5. DISPOSITIONS (pre-declared)

1. **F-K1–F-K5 all pass** → the arm is a **keeper candidate**: the owner-facing
   promotion note states what it closes (the C1-2024 blocking failure, the CHP
   conduct prerequisite that unblocks `nyiso_chp_btm_measured`'s R cell) and
   what it leaves open (the 2025 offer-level object, C3c). Promotion, if
   taken, follows the FULL protocol: attestation, keeper shard + `build_status
   --iso NYISO`, rule-22 D-5(b) marker re-key WITH determination
   re-verification, `calibration-keeper-auditor`, matrix keeper/gates
   re-stamp.
2. **Any of F-K1–F-K5 fails** → the arm registers as a rejected probe
   (rule 15), the matrix leg is stamped R with the failing gate named, and the
   next identification must state what statistic would fix it — no re-arm on
   this artifact without new evidence.
3. **The base replay breaks bit-identity** → STOP before the arm: that is a
   default-inertness defect in this session's own code and outranks the lane.
4. Both completed solves register per rule 15 (the base only if it broke
   identity, per §3); every run's bundle carries hourly sidecars per rule 15.

## 6. GOVERNANCE

* Rule 22: freeze ACTIVE; every year read or solved is 2023/2024/2025.
* Rule 28: the lever comes off the NYISO queue (the named nyiso-148
  successor); the base matrix row's def registers the field (28c, the
  offer_curve_by_group leg precedent); the NYISO shard cell is stamped with
  the tested verdict in this session (28b).
* DO-NOT-REDO honoured: census membership and BTM shares frozen; the
  single-band split is not re-litigated; nyiso-146's min-run/online-hours
  adjudications, the Zone-K bound, LI CC/ST and 7314 untouched.
* OUT OF LANE: RHO_CLIP, `nyiso_iroquois_winter_spread`, the D-4
  vintage-guard charter, the Astoria attribution, other ISOs' bench parts.
