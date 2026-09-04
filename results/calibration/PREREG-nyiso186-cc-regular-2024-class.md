# PRE-REGISTRATION — nyiso-186 (`cc-regular-2024-class` lane): WHICH combined cycles carry the 2024 `CC_REGULAR` excess, WHICH mechanism owns it, and the ONE admissible repair form per hypothesis — bars fixed before the first per-plant measurement

**Session:** nyiso-186, NYISO backcast-calibration track, 2026-09-04.
**Branch:** `claude/nyiso-186-cc-regular-2024-b16yp7`, fresh off `origin/main` at
`26c67788` (carries PR #4679, the nyiso-185 keeper bundle + promotion).
**Keeper at entry:** `2026-09-04-nyiso-185-family-hr`
(`results/calibration/nyiso185_family_hr`) — determination **NOT-YET**, target
grade 5, fail set **{C1-2024 `CC_REGULAR` +3.87 TWh / share +3.18 pp, C3a-2025
−10.5 % (owner-court, NOT touched here), C3c}**. Sibling cells: C1-2023
`CC_REGULAR` +0.58 TWh (PASS), C1-2025 +2.57 TWh (SKIPPED, preliminary 923).

**THIS DOCUMENT IS COMMITTED AND PUSHED TO `origin` BEFORE THE FIRST
PER-PLANT MEASUREMENT OF THIS SESSION.** No unit-hourly dispatch, no CAMPD or
EIA-923 per-plant energy, no eGRID plant row, no residual by plant and no
solve of this session's making exists at the time of writing.

---

## §0 — DISCLOSURE: every read made before this file was written

Read in full or in the named sections: `docs/FINDING-nyiso185-…` (§1–§8),
`PREREG-nyiso185-…`, `FINDING-nyiso184-…` §1, §3, §3.1, §4, §4.1, §5,
`FINDING-nyiso181b-…` §5–§6.1, §12, `FINDING-nyiso177-…` §5–§5.4, the matrix
§5.5 header + nyiso-185 and nyiso-184 queues, the NYISO shard cells named in
the brief plus `cc_capacity_reconcile` (U), `cc_nameplate_summer_derate` (K),
`cc_duct_peaking` (K), `cc_winter_capability_basis` (U),
`unit_outage_lp_capacity_basis` (U), `unit_outage_per_unit_clip` (U);
`CLAUDE.md` rules 1, 5, 12–16, 19, 21–25, 27, 28.

Code read (mechanics only): `data/fleet/eia860.py` (`_apply_egrid_boundary_hr_repairs`,
`_apply_egrid_family_heat_rates`, `apply_egrid_identity_heat_rates`, the
`_rows_to_generators` heat-rate seam, `_reconcile_cc_pmax_to_nameplate`,
`_eia923_plant_class_totals`, `CC_REGULAR_COMMITTED_PCT_BY_PLANT`),
`data/offer_curves.py` (`plant_tranche_bands`, `_offer_curve_for_group`,
`apply_gas_offer_margin`), `data/reserve_duty.py`, `data/fleet/campd_bins.py`
(`_reserve_duty_cohort`, `cc_duct_peaking_pct`, the reconcile hook),
`data/outages.py` (`unit_outage_derate_factors`), `pipeline/commitment.py`
(`_NYISO_BRIDGE_FUELS`), `config/scenarios.py` (`cc_capacity_reconcile`),
`config/iso_configs.py` (the five NYISO floor limbs), `scripts/calibration_verdict.py`
(`score_fuelmix`, `_fuelmix_vol_band`), `scripts/lib/campd_measured_classes.py`,
`scripts/lib/bundle_fleet.py` (API), `scripts/probes/nyiso184_heat_rate_basis.py`
(helpers), `scripts/probes/nyiso185_grounding.py`, `scripts/run_calibration_full.py`
(`_unit_hourly_frame` columns).

Inputs read (NOT residuals, NOT dispatch — disclosed at full magnitude):
* The keeper's `run_config.json` / `meta.json` / `resolved_inputs` (every
  armed field; the `CC_REGULAR` band multipliers committed 0.90 / econ 0.95–1.00
  / peak 2.25 / pct_peaking 8; `phys_*` and the zonal margin anchors; the
  extract `campd-unit-outages-perunitmerit-NYISO.csv` sha `45bc4f7c…`).
* The keeper's attestation `free_parameters` (13 entries, names only).
* **The keeper fleet reconstruction, 2023–2025** (`reconstruct_bundle_fleet`,
  no LP): 23 `CC_REGULAR` plants / 129 LP rows / 8,156.4 MW in 2024; per-plant
  MW and tranche heat rates. Noted from it: Cricket Valley 57185 carries
  1,312.5 MW (296.6 MW of it a 15.78 MMBtu/MWh peak band), Athens 55405
  1,221.6 MW with NO peak band, Astoria Energy II 57664 650.0 MW.
* `data/raw/_processed-legacy/cc_capacity_reconcile_NYISO.csv` (14 rows; the
  CAMPD p99.9 demonstrated peaks: Cricket Valley 1,086.9 vs model 1,312.5,
  Athens 1,064.7 vs 1,221.6, Zeltmann 560.0, Flynn 108.2 vs 243.1, …) — the
  artifact of a registered flag the keeper carries OFF (`cc_capacity_reconcile=False`).
* `reserve_duty_cc_NYISO.csv` (23 rows): the CAMPD plant online-share
  `duty_stat` per plant (Ravenswood CC 0.949, Bethlehem 0.936, Athens 0.583,
  Cricket Valley 0.901, Astoria Energy 0.992, Astoria Energy II **e923_pooled_cf
  0.714 — no CEMS record found for 57664**, Valley 0.872, Zeltmann 0.868,
  Caithness 0.858, Bethpage 0.876, Flynn 0.413, Saranac 0.426, Castleton
  0.224, Carr Street 0.345, Pinelawn 0.170, NYU 0.514; the seven reserve-duty
  members ≤ 0.1).
* `egrid_family_heat_rates_NYISO.csv` (the 15 rows; CC rows 2500 → 7.35,
  50292 → 9.56).
* **The outage extract's CC_REGULAR mass per plant per year** (unit-MW-days
  overlapping each year ÷ plant-MW × 365): Athens 0.726 / 0.475 / 0.529,
  Cricket Valley 0.171 / 0.409 / 0.355, Saranac 0.754 / 0.611 / 0.597,
  Caithness 0.049 / 0.282 / 0.063, Valley 0.190 / 0.089 / 0.145, Astoria
  Energy 0.062 / 0.066 / 0.228, Bethlehem 0.050 / 0.082 / 0.072, Zeltmann
  0.106 / 0.095 / 0.186, Bethpage 0.368 / 0.346 / 0.199, Ravenswood 0.011 /
  0.010 / 0.010 (denominator 2,082 MW, the whole facility); **no rows in any
  year for 57664 Astoria Energy II, 7314 Flynn, 50744 Sterling, 50978 Carr
  Street, 54592 Massena, 54593 Batavia** (7784 and 54808 appear in 2025 only).
* `_egrid_boundary_hr_repairs()` at HEAD returns `{55641}` only — no NYISO
  plant is boundary-repaired. `EGRID_CC_HR_PHYSICAL_CEILING = 11.5`,
  `UNIT_OUTAGE_MIN_DAYS = 5`.

Scores held from the nyiso-185 finding (class level only, no plant grain):
`CC_REGULAR` 2023 / 2024 / 2025 model 33.587 / 37.934 / 36.117 vs actual
33.012 / 34.060 / 33.544; `CC_REGULAR` ex-Ravenswood moved +0.79 / +0.50 /
+0.31 TWh under the family repair and Ravenswood's own CC +0.004 / +0.034 /
+0.010; `ST_GAS` 2024 −1.09; C8 `CC_REGULAR` D-2 0.049 / 0.034 / 0.033.

**Not read:** any `unit_hourly_<year>.parquet` (none exists in this container
— they are gitignored and were produced by nyiso-185's solves elsewhere); any
`class_hourly` / `system` sidecar; any CAMPD hourly or annual value by plant;
any EIA-923 plant row; any eGRID `PLNT23` / `GEN23` / `UNT23` row; the
keeper's `metrics.json` per-class rows beyond the headline above;
`legitimacy_diagnostics.json`.

---

## §1 — THE OBJECT

C1-2024 `CC_REGULAR` fails on the SHARE leg (+3.18 pp against ±3.0; the
volume leg's band is min(max(2 % load, 3 % actual gen), 8 TWh)). The object
is the **+3.87 TWh** of 2024 combined-cycle energy the model dispatches above
the EIA-923 grid-delivered actual, decomposed **by plant** on source
evidence, with the **owning mechanism named** before any repair is proposed.
Three hypotheses, mutually exclusive as *primary* attribution, fixed now:

* **H-A — OFFER POSITION at named plants.** A plant-level heat-rate BASIS
  error of the nyiso-184 kind (a plant-grain eGRID `PLHTRT` blend at a
  CC+GT or CC+ST site, a co-located-facility boundary, or a vintage/window
  artifact) prices a few large CCs below their measured basis, and they
  take energy from the others. The family artifact already reaches the only
  two multi-family CC sites (2500, 50292).
* **H-B — AVAILABILITY / CAPACITY BASIS.** The over-run sits at plants whose
  LP capacity × availability exceeds what the meter says they could deliver:
  (B1) LP `pmax` above the demonstrated peak (the OFF `cc_capacity_reconcile`
  artifact names Cricket Valley +225.6 MW and Athens +156.9 MW at model
  vs p99.9), and/or (B2) plants with NO outage rows and no CEMS conduct in
  the per-unit extract (57664 and the five small no-CEMS plants), which the
  model therefore carries at class-generic availability.
* **H-C — DEMAND-SIDE FILL (class object).** The excess is diffuse across
  the merchant CC fleet in proportion to available cheap capacity and is the
  mirror of the other classes' 2024 deficits in the same zones (`ST_GAS`
  −1.09 scored; `CT_PEAKER`, `CC_CHP`, imports as measured). Then no CC
  mechanism owns it; the object belongs to the deficit class and this lane
  proposes NO CC lever.

## §2 — RULE 19 `[R-ONE-MECH]`: every armed mechanism that sets a `CC_REGULAR` unit's offer or availability on this keeper (from the code, before proposing anything)

| # | mechanism (armed value) | what it sets on a CC_REGULAR row | reaches in NYISO |
|---|---|---|---|
| O1 | eGRID plant-grain join (`process_eia860._join_egrid_heat_rate`, always on) | base `heat_rate` = `PLNT23.PLHTRT` ÷ 1000 on every generator row of the plant | all 23 plants |
| O2 | `_apply_egrid_boundary_hr_repairs` (always on, four-condition rule, ceiling 11.5) | overwrites base HR where `PLHTIAN` spans a co-located CEMS facility | **{55641} only — no NYISO plant** |
| O3 | `egrid_family_heat_rates=True` (K) | family `HTIAN/GENNTAN` at ≥2-family plants | 2500 CC 7.35, 50292 CC 9.56 |
| O4 | `egrid_identity_heat_rates=True` (K) | pooled identity rate | 7784 only |
| O5 | `measured_ct_heat_rates` / `measured_chp_heat_rates` | CT_PEAKER / CHP rows only | **no CC_REGULAR row** |
| O6 | `offer_curve_by_group["CC_REGULAR"]` (K, DOF entry 1) | tranche multipliers committed 0.90 / econ 0.95→1.00 in 6 smoothed steps / peak 2.25 or duct-burner mult by turbine class | all 23 |
| O7 | `cc_committed_per_plant=True` | per-plant committed % from `CC_REGULAR_COMMITTED_PCT_BY_PLANT` | **dict holds ERCOT codes only — inert here** |
| O8 | `cc_duct_peaking=True` + `cc_peaking_per_plant=True` (K) | peak-band share = EIA-860 duct flag × (nameplate − net summer)/nameplate (0 at non-duct plants) | duct plants (e.g. 57185 296.6 MW, 57664 109.9, 55375 36.9); Athens 0 |
| O9 | `cc_reserve_duty_split=True` (K) | whole dispatchable capacity → peak band | the 7 ≤0.1 online-share plants (7784, 10620, 10621, 50744, 54034, 54592, 54593) |
| O10 | `gas_offer_net_revenue_margin=True` + zonal anchors (K, nyiso-72/167) | markup as fixed $/MWh margin at the zone anchor | all gas tranches |
| O11 | `nyiso_zonal_gas_basis` / `gas_hub_basis_daily` / `dual_fuel_*` (K) | delivered fuel price by zone-day | all gas |
| A1 | `campd_per_unit_attribution` + `campd_outage_merit_order_guard` (K) → `perunitmerit` extract | availability derate = unit MW ÷ plant MW over ≥5-day windows | 15–17 of 23 plants carry rows (§0) |
| A2 | `cc_nameplate_summer_derate=True` (K) | seasonal capability ratio on CC pmax | all |
| A3 | `_reconcile_cc_pmax_to_nameplate` (always-on summer guard) | clips plant pmax sum to max(nameplate, demonstrated peak) | as loaded |
| A4 | `cc_capacity_reconcile=False` (**U**, artifact present) | would cap / raise plant pmax to CAMPD p99.9 | OFF — 14-row artifact unarmed |
| A5 | `correlated_outage_*` / `nuclear_unit_availability` | class-generic winter derate | all |
| C1 | `nyiso_gas_commitment_bridge=True` (K; CC min-load 0.523, min-run 21 h) | P0→P1 min-gen floor on merchant slow-start gas | CC_REGULAR (D-2 share 0.034 in 2024) |
| C2 | reliability-floor limbs | NYC / LI / CH `ST_GAS` and `CT_PEAKER` limbs only | **no CC_REGULAR limb** |

**Ownership rule, fixed now.** H-A can only be owned by O1–O3 (the base
heat rate; O6–O10 are class-uniform and cannot pick plants). H-B1 can only
be owned by A3/A4 (capacity basis); H-B2 by A1's population (a plant with no
extract rows has an availability the extract never touched). H-C is owned
by no CC mechanism. O6's multipliers, O10's anchors and C1's fractions are
**not on the table** in any hypothesis — moving them is fitting (rule 21).

## §3 — MEASUREMENT (step 3, NO LP FIRST — the only new solve is the control replay that produces the unit sidecars)

**M0 — control replay.** `run_calibration_full.py --replay-bundle
results/calibration/nyiso185_family_hr --year 2023 2024 2025 --out-dir
results/calibration/nyiso186_control`, years sequential. **G-CONTROL:** its
hourly zonal prices against the committed keeper's `hourly/system_<year>.parquet`;
bit-identical (0 hours differ, max |Δ| 0.0, all three years) ⇒ the committed
keeper is the baseline, the replay registers nothing (rule 15 has nothing to
register) and its `unit_hourly_<year>.parquet` IS the keeper's dispatch.
Non-identical ⇒ the drift is named (hours, max |Δ|, per year) and the
control is registered as the baseline before anything else.

**M1 — per-plant model energy, 2024** (and 2023 / 2025 alongside): Σ `mw`
over the plant's `CC_REGULAR` rows of `unit_hourly_2024.parquet`.

**M2 — per-plant measured energy, two bases, both reported:**
(i) EIA-923 plant × class net MWh via `eia860._eia923_plant_class_totals(2024)`
(the scorer's own grid-delivered basis, `CC_REGULAR` class); (ii) CAMPD
gross MWh over the plant's CC units on the keeper's crosswalk —
`corrected_unit_class` over the plant's model groups, raw unit-grain rows
passed through `campd.merge_stack_duplicate_units` + `stack_duplicate_mask`
before any sum (nyiso-184 §4 discipline). Ranking and the concentration
statistic use basis (i); basis (ii) is the cross-check and the source of
hourly conduct.

**M3 — concentration statistic (decides H-C vs {H-A, H-B}).** Over the 23
plants, `E_p = model − actual(i)`, `E⁺ = Σ max(0, E_p)`. **C3 = share of
E⁺ carried by the three largest positive `E_p`.** Fixed bars:
**C3 ≥ 0.60 ⇒ CONCENTRATED** (a plant object: proceed to M4/M5 at those
plants); **C3 ≤ 0.40 ⇒ DIFFUSE** (H-C; M6 decides where the energy came
from and NO CC lever is proposed); 0.40 < C3 < 0.60 ⇒ MIXED — both legs run
and the finding reports both, the repair (if any) confined to the named
plants only if M4/M5 fire there.

**M4 — H-A basis test at each top-3 plant.** `r_p` = model base HR (the
committed tranche HR ÷ 0.90, i.e. the plant's loaded `heat_rate` before O6)
÷ CAMPD running-hour HR over the plant's CC units, merged, `REAL_RUN_CF` /
`MIN_REAL_RUN_HOURS` as in `nyiso184_heat_rate_basis.measured_hr_merged`.
Band = `[min, max]` of `r_q` over every OTHER CC_REGULAR plant with a
qualifying CAMPD record and CF ≥ 0.20 (the peers, printed before the
plant's value). **H-A FIRES at p iff `r_p` < min(band)** (priced cheaper
than any peer relative to its own meter) — and then the JOIN is inspected
for a named cause (eGRID `PLNGENAN`/`PLHTIAN` boundary vs CAMPD facility
heat; a second family; vintage). `r_p` inside the band ⇒ the plant's basis
is the class's basis and H-A does not fire there.

**M5 — H-B tests at each top-3 plant.** (B1) `pmax_model` ÷ CAMPD p99.9
gross (the reconcile artifact's own statistic, recomputed): H-B1 FIRES iff
> 1.05 AND the plant's model dispatch exceeds `p99.9 × 8760 × measured
online share` — i.e. the phantom capacity is actually being run. (B2)
availability ratio `a_p` = model mean availability (fleet_arrays, 2024) ÷
CAMPD online share (the reserve-duty definition); band `[min, max]` over
the peers as in M4; H-B2 FIRES iff `a_p` > max(band) AND the plant carries
no extract rows or CEMS conduct the extract could have read. A plant with
no CAMPD record at all (57664 if so) is reported with the EIA-923 CF in
place of the online share and H-B2 is stated as UNTESTABLE on conduct,
not fired.

**M6 — H-C accounting (always reported; decisive when DIFFUSE).** Per zone,
2024: the `CC_REGULAR` excess against the sum of same-zone deficits in
`ST_GAS`, `CT_PEAKER`, `CC_CHP`, `CT_CHP` and net imports (class sidecar +
bench). Reported as an accounting identity at fixed offers, never a causal
claim (nyiso-179 discipline).

## §4 — ADMISSIBLE REPAIR FORMS (fixed now) and the A/B rule

Exactly one repair may be A/B-solved this session, and only where its
hypothesis FIRED on the bars above:

* **H-A fired** → a repair of the NAMED JOIN by a generic rule reading
  published eGRID fields (the family construction's own predicate extended,
  or the boundary rule's four conditions met on data), zero parameters,
  regenerating per vintage. Never a per-plant rate.
* **H-B1 fired** → the registered flag `--cc-capacity-reconcile` with its
  committed NYISO artifact as derived (no re-derivation, no row edit).
  Cell `U` → adjudicated.
* **H-B2 fired** → the extract's POPULATION defect (a CC plant with CEMS
  units the per-unit crosswalk did not route) repaired in the derive as a
  generic rule, re-derivation citing the data defect (rule 23); if the plant
  has no CEMS record at all, NO repair — reported as a population gap.
* **H-C (diffuse)** → NO CC lever. The finding names the deficit class and
  zone and hands the object to that lane.

**A/B protocol** (rules 16, 12): arm = the keeper replay plus exactly the
one field, `--out-dir results/calibration/nyiso186_<name>`, 2023 + 2024 +
2025 in ONE invocation, years sequential; G-DELTA = one field. **Verdict
rule:** the arm is a **REJECTED PROBE** iff any of C2 / C3a / C3b / C8
flips PASS → FAIL against the baseline; otherwise a **KEEPER CANDIDATE**
put to the owner with C1 in all three years for `CC_REGULAR` AND `ST_GAS`,
C3a all years, every regression at full magnitude, DOF ledger (zero
added), LOYO from committed artifacts. **Expected side effects declared:**
2024 / 2025 `ST_GAS` move with any CC repair (the classes trade energy);
C3a-2025 stays owner-court whatever it does; no price claim.

## §5 — FORBIDDEN

F1 no band multiplier, anchor, min-load fraction or floor coefficient
moves; F2 no per-plant dict or per-plant carve; F3 no availability
haircut, no pin to CEMS output, no rescaling to the residual; F4 no edit of
the `ST_GAS` floors or of any nyiso-181 lever; F5 no touch of C3a-2025; F6
no CAISO 315/335 edits; F7 no second solve-affecting change in any arm; F8
no edit of any bar after M3 is read; F9 the second object (the Astoria
merit-panel stack-duplicate defect) is its OWN pre-registration, never in
this arm; F10 2023–2025 only, no marker requested, freeze untouched.

## §6 — STOP CONDITIONS

S0 the control replay is not bit-identical and the drift cannot be named
⇒ stop, instrument failure. S1 DIFFUSE ⇒ no solve beyond M0. S2 memory: at
most two concurrent invocations. S3 every completed non-control solve is
registered THIS session (rule 15). S4 G-DELTA fails ⇒ re-solve, never
register. S5 a repair whose hypothesis did not fire is not built.

---

## §7 — ADDENDUM (written AFTER M0–M6 were read; every bar in §3–§6 is untouched, F8 honoured): the ONE A/B this session runs, its license, and its pre-declared consequence

**Pushed to `origin` BEFORE the artifact is re-derived and BEFORE the arm is solved.**

### 7.1 What the pre-registered bars read (full magnitude, control = keeper, bit-identical: 0 of 52,560 hourly zonal prices differ in every year)

| year | class model / EIA-923 (unit sidecar, TWh) | E⁺ | top-3 | C3 | verdict |
|---|---|---|---|---|---|
| 2023 | 33.666 / 33.012 | 3.759 | 57185 +1.244, 56196 +1.109, 57664 +0.937 | **0.875** | CONCENTRATED |
| **2024** | 38.175 / 34.060 | 4.715 | 57185 +1.838, 56196 +0.868, 57664 +0.805 | **0.745** | CONCENTRATED |
| 2025 (prelim. 923) | 36.784 / 28.562 | 6.173 | 57664 +2.648, 56196 +1.397, 57185 +1.223 | 0.853 | CONCENTRATED |

The same three plants in every year. **M4 (H-A) at the top-3, 2024:** `r` = 1.031
(57185), 1.036 (56196), 0.950 (57664, on the facility meter) against the peers'
[0.707, 1.412] — **none < min, H-A does not fire.** **M5 (H-B) at the top-3:** B1
57185 `pmax/p99.9` 1.198 > 1.05 but dispatch 6.0 TWh < 8.4 TWh deliverable — does
not fire; 56196 0.891 — no; B2 `a_p` 0.790 / 0.918 inside [0.532, 2.816] — no;
57664 untestable on conduct as pre-declared (no own CAMPD record). **The bars are
too loose to discriminate** — the M4 band is set by Flynn 0.707 and Carr Street
0.816 (plants whose eGRID annual rate and CAMPD loaded rate disagree by 30–40 %)
and the M5 band by the same two — and this is reported as a defect of the bars,
not repaired post hoc. **§6 S5 stands: no repair is built on the bars.**

**M6, 2024, class-sidecar basis:** the gas FAMILY is exact — model 67.80 TWh vs
EIA-930 67.80 — so the `CC_REGULAR` +3.87 and `CC_CHP` +1.90 are the
within-family fill of `CT_PEAKER` −1.66, `CT_CHP` −1.29 and `ST_GAS` −1.09
(`ST_CHP` +0.12). **Mechanism, from the when-online comparison (2024):** Zeltmann
runs at 0.96 loading when on against a 0.68 meter (on-share 0.90 vs 0.90); the
Astoria facility 0.84 vs 0.77 (on 1.00 vs 1.00); Cricket Valley is on 0.995 of
hours vs 0.878 (loading 0.54 vs 0.50); Athens and Valley track their meters
(0.55/0.61, 0.77/0.84). The excess is the cheapest available NYC / Capital-Hudson
combined cycles loading up to fill the CT-class and steam holes — the nyiso-175
and nyiso-181 objects, not a CC mechanism.

### 7.2 A data defect found on INPUTS during M2 (never on a residual): the Astoria registry split

* EIA-860 files generators CT3 / CT4 / ST2 under plant **57664 Astoria Energy
  II**; eGRID-2023 lists the same six generators (CT1–CT4, ST1, ST2) under ONE
  plant, **55375**, with 1,245 MW; CAMPD facility 55375 carries four CT units;
  **there is no eGRID row for 57664 in any vintage.**
* **Identity, to the MWh:** eGRID `PLNGENAN(55375)` equals EIA-923 net generation
  (55375) + (57664) to < 0.5 MWh in **all seven vintages 2018–2024**
  (6,341,472 / 5,989,392 / 5,447,419 / 5,899,776 / 7,207,809 / 7,998,042 /
  8,162,646). This is the committed identity rule's own exactness standard
  (`derive_egrid_identity_heat_rates`, `MATCH_TOL_MWH` 0.5, `MIN_OVERLAPS` 2),
  met at the TWO-plant sum. The derive's own docstring names "the Astoria
  55375↔57664 family" as the object class; its one-to-one predicate cannot
  reach it.
* Consequence in the keeper: the fleet parquet carries `heat_rate = NaN` for
  57664, so it takes the `HEAT_RATE_BINS['gas_cc']['f_class']` default **6.70**
  while its sibling block at the same facility carries eGRID's 7.258 and the
  facility meter reads 7.05 (running-hour, merged). A class-default estimate is
  in use where a measured, seven-vintage, exact-identity input exists.

**License: rule 14 `[R-ACCURATE]` + rule 1 `[R-STRUCT]`, NOT a §3 bar.** The
brief's admissible form for H-A ("a repair of the NAMED JOIN by a generic rule
reading published eGRID fields, zero parameters, regenerating per vintage")
describes it exactly; only H-A's *firing* bar was missed, and §7.1 records why
that bar cannot fire on anything. Direction: the repair makes Astoria Energy II
DEARER; under M6's pinned family total the released energy goes to OTHER
combined cycles first.

### 7.3 The arm, fixed now

* **Change:** `scripts/data/derive_egrid_identity_heat_rates.py` gains a
  MERGED-identity leg: for a CAMPD-less EIA-923 plant `p`, an eGRID plant `q ≠
  p` of the same state that is itself an EIA-923 plant, with `PLNGENAN(q) ==
  netgen(p) + netgen(q)` to `MATCH_TOL_MWH` in EVERY overlapping vintage,
  `≥ MIN_OVERLAPS`, run over the whole population. Same tolerance, same
  overlap rule, same pooled `ΣPLHTIAN / ΣPLNGENAN` rate rule, same LOYO
  record. **Dry-run result (read before this addendum, disclosed): exactly ONE
  pair in the 187-plant NYISO fossil population — 57664 ↔ 55375, 7 vintages,
  pooled 7.3792, per-vintage 7.2576–7.5436.** The one-to-one rows are unchanged
  (Allegany 7784 byte-identical). Zero parameters; zero config fields.
* **Arm:** `--replay-bundle results/calibration/nyiso185_family_hr --year 2023
  2024 2025 --out-dir results/calibration/nyiso186_astoria_identity`, years
  sequential, with the re-derived artifact on disk. **G-DELTA:** the arm's
  `scenario_config` differs from the keeper's in ZERO fields; the artifact
  differs in exactly one row (57664). **Verdict rule: §4 verbatim** (rejected
  probe iff C2 / C3a / C3b / C8 flips PASS → FAIL; else keeper candidate, put
  to the owner with every regression at full magnitude).
* **Pre-declared expectations (falsifiable, not bars):** (i) 57664's energy
  FALLS every year; (ii) 55375, 56196 and the other NYC CCs RISE; (iii) the
  class C1-2024 cell moves LITTLE — its share leg may stay FAIL — because the
  family total is pinned (M6); (iv) `ST_GAS` / CT classes ~unchanged; (v) no
  price claim; C3a-2025 owner-court whatever it does.
* **What this arm does NOT carry (F7):** the availability half of the same
  split — the `perunitmerit` extract routes CT3 / CT4 (313.0 MW each, of a
  1,221 MW plant denominator) and CT1 / CT2 (297.5 MW) ALL to 55375, so Astoria
  Energy II is never derated and Astoria Energy I is derated for its sibling's
  outages (2025: 57664's EIA-923 falls to 2.12 TWh on a long outage the model
  cannot see, +2.65 TWh); and the tranche artifact reads 55375 at a 150 %
  median CF. Sized and handed to the outage-derive lane (the caiso-196
  `CAMPD_UNIT_PLANT_REMAP` precedent is the repair form there).
* **Also NOT carried:** Bethlehem 2539 — eGRID `PLHTRT` 6.87 (2018–21) → 8.26
  (2022) → 9.67 (2023) → 10.44 (2024) while CAMPD's per-unit running HR reads
  10.0–10.2 in 2022–23 and 6.6–7.1 in 2024–25 with 2022–23 CAMPD gross BELOW
  EIA-923 net — a CEMS reporting regime change, not a plant property. The model
  prices it at 9.665 in every year; under-run −2.28 (2023) / loading 0.56 vs
  0.75 when on (2024). Opposite sign to this object; handed forward.
