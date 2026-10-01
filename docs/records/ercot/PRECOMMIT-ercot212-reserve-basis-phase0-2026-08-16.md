# PRECOMMIT — ercot-212 (RESERVE-BASIS-1, card X item X-3): Phase-0 measurement plan and the pre-registered mechanical viability rule

**Session ercot-212, 2026-08-16, branch `claude/ercot-reserve-basis-x3-gjpsh9`.
Pushed BEFORE the Phase-0 probe runs (the ercot-208 Phase-0 discipline; the
ercot-206 B0 precedent for pre-registering even a read-only phase).** Keeper at
fetch: **`2026-08-15-ercot204-rule26-delete`** (resolved fresh from
`frontend/data/backcast/keepers/ERCOT.json`). X-3 signed by dispatch of
RESERVE-BASIS-1; the signature text is appended to
`docs/ASSESSMENT-ercot209-2023-scarcity-calibration-path-2026-08-15.md`
"RESOLUTIONS — CARD X" in this session.

Phase-0 is READ-ONLY: no LP, no solve, no year scored, no run registered, no
`ScenarioConfig` field, no matrix cell or row edit. Sources are committed
artifacts and published telemetry only:

* keeper sidecars `results/calibration/ercot204_rule26_delete/hourly/`
  (`reserve_family_<year>.parquet` — the ONLY artifact where the
  `ercot_ordc_total` family's binding is observable — plus
  `system_<year>.parquet`, `class_hourly_<year>.parquet`) and its resolved
  `run_config.json`;
* published NP6-905-CD telemetry
  `data/raw/ercot/ercot_<year>_ordc_reserves_hourly.parquet`
  (`rtorpa`, `rtordpa`, `rtolcap`, `rtoffcap`, `prc`, `system_lambda`);
* the armed credit series the solve itself read:
  `data/raw/ercot-AS/ercot_<year>_as_up_mw.parquet` (`rrsufr_mw`, the
  load-resource credit) and the measured storage AS-award series
  (`results/scarcity.ercot_storage_as_reserve_mw`);
* the published NP6-576-ER seasonal LOLP table
  `data/raw/_validation-source/ercot_ordc_lolp_params.csv` (2025-vintage; used
  ONLY as a comparison curve per the ercot-206 B0 year-keyed split — never
  armed here);
* curve arithmetic via the model's own `ercot_ordc_demand_steps` /
  `scarcity.lolp` with the keeper's resolved parameters (VOLL 5,000, MCL 3,000,
  μ 0, σ 1,400, shift 0.5σ, OBDRR048 floor on) — the code path the keeper ran.

## §1 The question (X-3, verbatim scope)

Measure WHERE the ORDC pricing region sits relative to the model's reserve
representation at the 2024/2025 published-fired hours, and why 2023 is healthy.
The armed counterpart (the `ercot_ordc_total` balance dual, sidecar
`ordc_adder`) reads ≈ zero across the 560/253 published-fired hours while the
keeper's family `held_mw` is BELOW published RTOLCAP (6,955 vs 8,854 MW 2024;
6,638 vs 9,654 MW 2025) and its own row records non-zero shortfall in 40/4 of
those hours (ercot-204 §A.3).

**Fired-hour definitions, fixed ex ante:** published-fired = `rtorpa > 1e-9` on
the non-leap hourly clock, 2025 restricted to the pre-RTC+B window
(`hour < 8112`); the ercot-198 settlement-closure guard applies (2025 h4334,
the one uncorrected archive print, reported as an excluded variant at full
magnitude, per FINDING-ercot198 §4). Model-fired = sidecar `ordc_adder > 1e-9`.

## §2 The armed construction, stated ex ante (what the terms attach to)

From the keeper's resolved `run_config.json` and
`model/reserves/spec.py::_ercot_multiproduct_design` +
`results/scarcity.py::{ercot_ordc_demand_steps, resolve_lolp_params,
ercot_rtolcap_supply_cap_mw}`:

1. **Curve**: one static 40-band step curve from
   `req_total = MCL + (μ + 0.5σ) + 5σ = 10,700 MW` down to 0, penalties
   `0.5·VOLL·(LOLP_full + LOLP_half)` at each band's lower edge, OBDRR048
   floor applied **unconditionally** (the post-solve path date-gates it at
   2023-11-01; the LP path does not). `resolve_lolp_params` returns the flat
   fallback (μ=0, σ=1,400; `ordc_lolp_params_path=None`), and the family
   builder collapses any μ/σ to **annual-mean scalars** regardless
   (`spec.py` `mu_s = float(np.mean(mu))`).
2. **Requirement**: `requirement_mw(t) = max(10,700 − lr(t) − sas(t), 3,000)`
   — the measured load-resource RRS-UFR and storage AS-award series are
   netted OFF the demand side (both from_year 2023 on this keeper).
3. **Supply**: per-product held bounded by two shared-headroom tiers capped at
   **measured RTOLCAP** (fast: RegUp/RRS/ECRS on non-quick-start units) and
   **RTOLCAP + RTOFFCAP** (all: + NonSpin, quick-start); storage is NOT an
   endogenous reserve supplier on this keeper
   (`ercot_storage_as_endogenous=False`).
4. **Marginal placement**: the balance fills shortfall cheapest-band-first, so
   the marginal band's reserve edge sits at `held_mw(t) + credits(t)` where
   `credits(t) = 10,700 − requirement_mw(t)`. The dual (the model's RTORPA)
   is the curve price at that level when shortfall > 0, else ~0.

The published counterpart prices `RTORPA = 0.5(VOLL−λ)·LOLP_full(RTOLCAP +
RTOFFCAP) + 0.5(VOLL−λ)·LOLP_half(RTOLCAP)` on seasonal NP6-576-ER parameters
with the floor from 2023-11-01 (ordc-overlay.md; Nodal Protocols §6.5.7.3).

## §3 Measurements, pre-registered (A0–A6)

* **A0 — construction validation.** Verify §2.4 against the committed record:
  in shortfall hours the sidecar `dual` must reproduce the curve price at
  `held+credits` (tolerance: step discretization). If A0 fails, the attribution
  follows whatever the record shows; every A0 discrepancy is reported.
* **A1 — the honest held↔RTOLCAP crosswalk (dispatch: FIRST).** Component
  table of the two constructions: model `held_mw` (procured product MW,
  demand-limited at the credited requirement, supply-capped at
  RTOLCAP/RTOLCAP+RTOFFCAP) vs telemetered RTOLCAP (capability of everything
  on line: thermal headroom + ESR + Load Resources). Reconciled comparison on
  the common basis `B_model(t) = held_mw(t) + lr(t) + sas(t)` vs RTOLCAP(t)
  and vs RTOLCAP(t)+RTOFFCAP(t), full-year and fired-hours distributions.
  Deliverable: either a component reconciliation, or the measured statement of
  which components cannot be reconciled and why (award ≠ capability).
* **A2 — term: held-quantity basis + requirement basis.** In the fired hours,
  the joint distribution of (held, requirement, shortfall, marginal level
  `held+credits`): in how many fired hours is held = requirement (curve top,
  price ≡ 0 by construction) vs shortfall > 0; the credit series' size in
  those hours.
* **A3 — term: reserve-supply cap basis.** In the shortfall hours, what binds:
  held vs RTOLCAP, vs RTOLCAP+RTOFFCAP, vs requirement; the wedge between the
  model's marginal level (`held+credits`) and the telemetry basis (RTOLCAP)
  in those hours — the credit double-count question, measured.
* **A4 — term: demand-curve placement.** The armed flat curve and the
  published-table curve (shift 0 per ordc-overlay.md) evaluated at (i) the
  model's marginal level, (ii) published RTOLCAP/(RTOLCAP+RTOFFCAP) on the
  published two-basis form — a 2×2 at the fired hours, reproducing the
  ercot-206 B0 rows on this session's construction as the cross-check.
* **A5 — term: floor date-gating.** Both fired windows (2024/2025) post-date
  2023-11-01, so the LP's undated floor should be non-explanatory for the
  zero; verify, and measure the converse 2023 exposure (hours Jan–Oct-2023
  where the undated LP floor could price when the real floor did not exist).
* **A6 — the 2023 contrast.** The same A2–A4 decomposition on 2023's 42
  model-fired and 1,705 published-fired hours: what places the model's
  marginal level inside the pricing region in 2023 but not 2024/2025.

## §4 The pre-registered mechanical viability rule (STOP at it if it fails)

Phase-1 (an armed A/B in this lane) is entered ONLY if a candidate mechanism
clears ALL of V1–V5. Otherwise **STOP**: report the attribution, hand the
object back, run the item-8 read-only screen if time permits (dispatch queue
box 2), and end.

* **V1 — zero fitted scalars (rules 13/20/23).** Every quantity in the
  candidate is an already-armed measured series, a published ORDC design
  parameter, or arithmetic on them. No scalar chosen on any residual; no new
  measured series intake.
* **V2 — one mechanism (rule 19).** The candidate repairs the basis/arithmetic
  of the ARMED `ercot_ordc_total` family. It adds no second pricing channel
  for the same phenomenon. Candidate class C-A only:
  supply/requirement/placement **basis consistency** of the armed family.
* **V3 — no adjudicated cell re-opened without new evidence (rule 28a).**
  Barred by standing record: published-RTORPA overlay (ercot-204 §A, rule 19);
  `ordc_scarcity_overlay` (R, ERCOT-97); `online_capacity_envelope` (R,
  ERCOT-107/108); `energy_online_capability_cap` (R, ERCOT-155); blanket
  NP6-576-ER LOLP-table arming (ercot-206 B0 year-keyed split: 2023/2024
  refute it) — a year-keyed curve parameter is a NEW DOF shape needing its own
  charter (ercot-206 §5.4) and is NOT Phase-1-eligible in this lane; conduct
  layer (ercot-211, Door A closed); tightness-conditioned identification / E1
  dispersion repair (V0 / ercot-201 DO-NOT-REDO).
* **V4 — mechanical sufficiency, out-of-LP, direction-blind.** Computed from
  committed artifacts alone (no solve): the candidate's implied marginal
  reserve level at the 2024 published-fired hours, priced on the ARMED flat
  curve, must yield an implied 2024 adder incidence `h > $1` within
  **[0.25×, 4×] of the settled published count (78 h; ercot-206 B0)**. Below
  the band the candidate is still dead (STOP); above it the candidate
  over-fires and is equally refused (STOP). Band fixed before measurement.
* **V5 — 2023 non-destruction, out-of-LP.** The same implied construction in
  2023 must keep deep-tail incidence `h > $100` within **[0.25×, 4×] of the
  settled published 17 h** (ercot-206 B0 measured-settled row). The current
  keeper's healthy 2023 deep tail may not be structurally destroyed by a
  repair aimed at 2024/2025. (Any resulting C3a/C3b/C3c-2023 movement in a
  Phase-1 solve is side-effect-reported at full magnitude under Q-B/R-A
  phrasing, never a basis — X-3.)

**Named falsifier for the C-A candidate, stated ex ante:** if A2/A3 show the
fired-hour zeros are NOT a basis artifact — e.g. the model sits at the curve
top because `RTOLCAP + RTOFFCAP` (the telemetry the caps already read) itself
stays above the 10,700 MW curve span in the fired hours, so no
basis-consistent arithmetic of the armed series can move the marginal level
into the pricing region without importing the published table (barred by V3)
— then no C-A candidate exists and Phase-0 STOPs.

## §5 Phase-1 sketch (entered only on V1–V5 PASS)

Single delta on the keeper recipe; its own precommit pushed BEFORE any solve
with direction-blind kill gates inherited from the ercot-202/204 family
(G-REPRO control, G-SHED, G-C3c no-2023-drain, G-SPAN, G-COAL148, G-OWNER,
G-DOF, G-D2), roster effects named ex ante. Environment pinned to the keeper
`run_config.json` `environment.packages` (highspy 1.14.0, pandas 3.0.3,
pyarrow 24.0.0) BEFORE the control replay, `./.venv/bin/python` directly
(`uv run` silently reverts the pin — the ercot-204 lesson). Full span
`--year 2023 2024 2025` in ONE invocation, years sequential (rule 12). Both
runs registered on the BACKCAST registry with payloads (rule 15; payloads over
`git push`), matrix 28b cell verdict + any 28c row in the same landing,
promotion RECOMMENDATION only — the keeper cannot change in-session.

## §6 Fences

Rule 22: {2023, 2024, 2025} only, read-only in Phase-0, no marker sought.
Rule 25: ERCOT only. Rule 27: edit locally, push exact bytes, blob-verify
pushed files ≥300 lines. RTOLCAP enters as **telemetry read for measurement**
in Phase-0 (the FFR-8B §4 validate-never-parameterize role); the armed supply
cap's own use of it is the keeper's standing construction, not this session's
addition. Q-B FINAL and R-A cited, never re-litigated. No new workflows.
`check_mechanism_matrix.py` exit 0 before landing. No PR (push-and-stop on
the designated branch; the owner merges).
