# ERCOT-146 — `measured_ct_heat_rates` on ERCOT: INERT BY WIRING, no solve spent

**Session:** 2026-07-31 (matrix §5.1 item 6). **Keeper (unchanged):**
`2026-07-31-ercot145-gas-daily-shape` (bundle `ercot145_gas_daily_arm`).
**Probe:** `scripts/probes/ercot146_ct_heat_rates_phase1.py`. **New measured
artifact (committed either way, rule-23 frozen):**
`data/raw/_processed-legacy/campd_ct_heat_rates_ERCOT.csv` (+ `_units.csv`) —
ERCOT's own derive of the frozen `derive_campd_ct_heat_rates.py`, 2023–2025
only, 34 plants, zero rows outside the physical band. Preconditions verified:
default `cache_key` byte-stable (`603c2498bf71d21d`), `audit_keepers.py`
PASS 0/0.

**Charter.** A/B the NYISO/PJM/CAISO form (`ScenarioConfig.
measured_ct_heat_rates`) on ERCOT's CT fleet — audit-grade, per-ISO artifact
(rule 25; nothing transfers from the three keeper ISOs). Phase 1 pre-committed
as no-LP with the no-solve closure exit (ERCOT-143/145 pattern). Phase 1
adjudicates: **no A/B is licensed because the mechanism cannot reach ERCOT's
dispatched fleet — the cell is stamped `I`**, on byte-level proof, with the
substantive value question answered from the artifact anyway.

## 1. Leg 1 — the flag provably never touches the fleet ERCOT dispatches

The mechanism's consumer is `eia860._rows_to_generators`, i.e. the
`load_fleet_from_csv` path. ERCOT's thermal fleet does not come from there:
under `use_campd_bins=True` (the keeper's config and the ERCOT default),
`assembly.load_or_synthesize_bins` short-circuits to
`load_campd_bins(config.campd_bins_path)` — the curated per-plant sheet —
**without the `measured_ct_heat_rates` kwarg**, and `build_base_fleet` then
keeps only non-aggregatable units (nuclear …) from the eia860 path. Every
gas/coal generator the ERCOT LP dispatches prices off the sheet's
`Plant_Avg_HR_MMBtu_MWh`.

Proven, not argued: the probe builds the full base fleet flag-off and flag-on
— **609 generators, byte-identical** on (name, plant_code, plant_group,
heat_rate, pmax). A replay `--set measured_ct_heat_rates=true` off the keeper
would burn a ~50-minute span to produce a bit-identical bundle. The honest
verdict for the mechanism-as-shipped is **`I` (probe-adjudicated inert)** —
not `R` (nothing was refuted on the merits) and not `G` (nothing had to be
governance-refused; there is no effect to refuse).

## 2. Leg 2 — the substantive question, answered anyway: ERCOT does not have the defect this mechanism fixes

The mechanism exists (nyiso-89, pjm-137, caiso-146) because eGRID publishes
ONE plant-average annual rate — wrong technology at mixed facilities, annual
average instead of loaded rate. **ERCOT's curated sheet already solved that
structurally**: it is CAMPD-derived per-plant (2023–24 gross generation,
`docs/binning-methodology.md`), one row per plant × class.

The independent loaded-window re-derive CONFIRMS the sheet on its own basis:

- **vs the sheet (the dispatched basis), 25 matched curated CT_PEAKER
  plants:** cap-weighted sheet 10.947 → measured loaded **gross** 10.837
  (**−1.0 %**) — agreement within 1 %, no NYISO/PJM-style per-plant noise
  story (their headline was two-directional 2× errors; ERCOT's per-plant
  loaded-gross deltas are small).
- The full delta to the measured loaded **net** rate (11.663, **+6.5 %**) is
  **entirely the gross→net parasitic conversion (+7.6 %)** — a BASIS
  convention question, not a plant-error question. It is one-sided by
  construction (19 plants / 5,497 MW dearer > 0.5 MMBtu/MWh, 1 / 136 MW
  cheaper), because dividing by a ~0.9 parasitic factor moves every plant the
  same way.
- **vs eGRID** (the artifact's recorded column, for cross-ISO comparability):
  cap-weighted 10.979 → 11.880 (**+8.2 %**), gen-weighted +6.2 %; 22 dearer /
  2 cheaper / 10 within ±0.5. Same sign as PJM's +0.229 MMBtu/MWh but ~4×
  larger — and dominated by the same basis term.

Whether ERCOT's LP should carry net-basis heat rates is a **fleet-wide
property of the curated sheet** — CC, coal and ST classes share the identical
`Plant_Avg_HR` convention, and the keeper's recorded physical bases
(`phys_*`, e.g. the CT cap-wt 10.91 in ERCOT-145 §1) are all stated on the
sheet basis. A CT-only net correction through this flag — even if it were
wired — would repair one class's basis while leaving every neighbouring
class's identical convention untouched: an inconsistency, not an accuracy
gain. The basis question belongs to the measured CT-band re-identification
(§4), which owns the offer levels end-to-end.

## 3. Legs 3–4 — coverage is excellent, reach is small, and the incumbent on the rows is still fitted

**Coverage (the caiso-146 template):** 34 plants = 85.7 % of eia860-fleet
CT_PEAKER capacity (7,036/8,211 MW); on the curated sheet, 25 plants = 79.9 %
of curated class capacity (7,045/8,816 MW) and **99.2 % of the class's own
metered CAMPD CT energy** (17.711/17.860 TWh gross 2023–25). No adverse
selection: covered cap-wt sheet HR 10.947 vs uncovered 10.751. The uncovered
tail is structural, nothing to swap in: Denton (225.6 MW), Red Gate
(224.4 MW) and Pearsall (201.6 MW) are reciprocating/no-CEMS (zero CAMPD
rows); Morgan Creek (536.4 MW) is classed `oil` in the eia860 fleet so it was
never in the derive's target set (its 6 CAMPD CTs would individually clear
the loaded screen — a target-population note for the re-identification lane,
not a defect of this artifact).

**Mixed facilities:** 9 artifact plants (1,708 MW of eia860 CT capacity —
T H Wharton, V H Braunig, R W Miller, Decordova, Sand Hill, Colorado Bend,
C R Wing, Dansby, Ray Olinger …) have **no curated CT_PEAKER row at all**:
the one-class-per-plant sheet carries them as CC_REGULAR/ST_GAS/CC_CHP bins.
The flag could not have re-priced them even if wired — their measured CT
rates are recorded in the artifact for the class-composition question (same
family as the open Martin Lake ruling, ERCOT-143 §7.3).

**Reach:** CT_PEAKER is **1.36 / 1.21 / 0.92 %** of ISO load on the keeper's
own sidecars (6.087/5.616/4.500 TWh vs 445.97/462.59/487.75 TWh) — below the
2 % gate line, so C7/C8 never gate it. And the rows a re-price would ride
through still carry the FITTED `offer_curve_by_group` multipliers
(econ_low 1.27 / econ_high 2.18 / peak 13.15 vs phys 0.723/0.727/1.0 — the
+$13/+$35/+$292 per MWh margins of ERCOT-145 §1): a +6.5 % base-HR move
under fitted multipliers shifts the composite offers ~+$2–3 (econ) /
~+$21–32 (peak) per MWh at 2024/25 gas **while the offers remain fitted
objects** — it modulates the incumbent, it does not retire it. The shape is
the near-uniform adder ERCOT-145 §2 already proved wrong for the
signed-both-ways sub-$200 residual.

## 4. Adjudication and the successor this artifact feeds

**Cell verdict: `I` (inert by wiring, proven byte-level, no solve spent).**
No ScenarioConfig change, no solve, no dashboard registration (no run
produced — the ERCOT-142/143/145 no-solve precedent). Keeper, DOF ledger
(n_residual 6) and all gate verdicts unchanged. Holdouts untouched (derive
years 2023–2025 only, rule 22). ERCOT-scoped (rule 25): nothing transferred
from nyiso-89/pjm-137/caiso-146, and this verdict transfers nowhere.

**What would make this measured input live** is unchanged from ERCOT-145 §4,
now with its physical-basis half ready: a **measured re-identification of the
ERCOT CT band levels** (SCED TPO on the CT fleet — the conduct instrument)
that retires the fitted `offer_curve_by_group` CT multipliers. That
identification takes THIS artifact as its physical heat-rate term (with the
gross-vs-net basis decision made explicitly and consistently), the committed
`campd_ct_run_lengths_ERCOT.csv` as its start-amortization term, and the SCED
TPO corpus as its level instrument. Wiring measured rates into the curated
path (`load_campd_bins`/`bins_to_fleet`) is a NEW solve-affecting mechanism
that belongs to that lane, carries its own matrix row (rule 26c), and must
not be built as a stack on the fitted bands (rule 19). The ERCOT-138 closure
still bars using any of this on the CC gas-dearness defect.

**The sub-6.0 MMBtu meter-hour caveat** (caiso-146 side finding: sub-6.0
loaded meter hours drag the shared derive low in every ISO) remains
cross-cutting and unacted-on here — ERCOT's artifact has zero rows outside
the band, and an hour-grain screen would move three committed keepers'
inputs, so it still needs its own charter (rules 24/25).

**Alternates assessed, both data-intake-first (surfaced, not attempted):**
matrix §5.1 item 7 (WP-B nodal curtailment) still lacks the station→area
crosswalk in-repo; `winter_citygate_daily` ERCOT needs an HSC/Katy daily
basis series — `data/raw/gas-prices/` holds daily citygate series for
MISO/NEISO/CAISO/NYISO but no Texas hub daily file, and the pjm-139 W1
day-scale bound applies to whatever it would buy. Both stay queued.

**Open owner rulings carried (surfaced, not decided):** (1)
`gas_hh_monthly_shape` matrix row (26c gap); (2) per-gate dispositions of the
attributed gates (C3a/C3b/C3c tail expressions; C7-2023's non-offer-surface
cell); (3) `split_coal_tranches` delete-vs-inert; (4)
`ercot_offer_hrmult_ep_rebasis`/`_bands` matrix rows (26c); (5) Martin Lake
lignite class composition — to which this session adds the recorded
mixed-facility CT rates of §3 as evidence-in-waiting.
