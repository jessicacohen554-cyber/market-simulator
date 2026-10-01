# PRE-REGISTRATION — xiso-3: close the CROSS-ISO SHARED-STEM rule-28(c) backlog

**Date:** 2026-08-04 · **Session:** xiso-3 (cross-ISO lane) · **Target:** the SHARED
(non-ISO-prefixed) `ScenarioConfig` fields that an ISO's designated keeper arms with no
matrix cell anywhere · **Branch:** `claude/xiso-3-shared-stem-e4y67p`
**Committed and pushed BEFORE any matrix row is written, before any anchor is repaired,
and before the construction probe is run.**

**No keeper changes in any ISO. No solve. No year touched. No `ScenarioConfig` value, no
constant, no derive script changed.**

---

## §1 — why this session, and the measured starting point

`nyiso-121` closed MISO's own-family column — the LAST ISO family column — and named the
cross-ISO shared-stem backlog as its successor and the ONLY remaining rule-28(c) debt.
The sweep was **re-run this session** rather than trusted from the handoff:

```
PYTHONPATH=.:src python scripts/mechanism_matrix_gap_sweep.py --write-baseline
```

| ISO | family | absent | prose | armed-no-cell | **shared-gap** | invisible |
|---|---|---|---|---|---|---|
| CAISO | 62 | 0 | 0 | 0 | **5** | 1 |
| ERCOT | 86 | 0 | 0 | 0 | **14** | 12 |
| MISO | 25 | 0 | 0 | 0 | **17** | 12 |
| NEISO | 20 | 0 | 0 | 0 | **0** | 0 |
| NYISO | 41 | 0 | 0 | 0 | **0** | 0 |
| PJM | 35 | 0 | 0 | 0 | **18** | 0 |

All six family columns read **0 / 0 / 0**, confirming the handoff's DO-NOT-REDO. The
shared backlog is **45 distinct fields / 54 (ISO, field) pairs**; nine fields are armed in
two ISOs at once. The ratchet baseline `mechanism-matrix-gaps.json` is byte-unchanged by
the re-run, so these counts are main's, not this session's.

## §2 — scope A: register all 45 fields on 19 EXISTING rows, chosen on CODE DEPENDENCY

Every home is the row whose **code** owns the mechanism the field modifies — the read site
is cited in the registration text, never a thematic association. Where two rows both
qualify, the tie-break is pre-declared in §5. **ZERO new rows.**

| # | field | armed on | home row | read site (the dependency) |
|---|---|---|---|---|
| 1 | `coal_bit_passthrough_sigmoid` | PJM | `coal_passthrough_sigmoids` | `data/fuel/trajectories.py::coal_passthrough_series` gate |
| 2 | `coal_bit_passthrough_floor` | PJM | `coal_passthrough_sigmoids` | `coal_sigmoid_params` param of #1 |
| 3 | `coal_sub_passthrough_sigmoid` | PJM | `coal_passthrough_sigmoids` | same gate, subbituminous rank |
| 4 | `coal_sub_passthrough_floor` | PJM | `coal_passthrough_sigmoids` | `coal_sigmoid_params` param of #3 |
| 5 | `coal_lignite_passthrough_floor` | ERCOT | `coal_passthrough_sigmoids` | same, lignite rank |
| 6 | `coal_lignite_passthrough_ceil` | ERCOT | `coal_passthrough_sigmoids` | same, lignite rank |
| 7 | `coal_prb_passthrough_floor` | ERCOT | `coal_passthrough_sigmoids` | param of the already-named `coal_prb_passthrough_sigmoid` |
| 8 | `coal_prb_follower_floor` | ERCOT | `coal_passthrough_sigmoids` | `trajectories.py::prb_follower_passthrough_series`, gated `assembly.py` |
| 9 | `coal_mustrun_online_pmin` | PJM | `coal_mustrun_per_plant` | `fleet/campd_bins.py` sizes THIS row's must-run tranche |
| 10 | `coal_sync_srmc_tranche` | PJM | `coal_mustrun_per_plant` | `fleet/assembly.py`; hard-requires #9 |
| 11 | `coal_takeorpay_from_data` | MISO | `coal_takeorpay_committed` | the row's def already carries it as the abbreviation `_from_data` |
| 12 | `coal_warm_committed` | MISO | `p1_bidcost_pass` | `model/commitment.py::compute_monthly_markup` class exemption |
| 13 | `gas_st_startup_cost` | ERCOT, MISO | `p1_bidcost_pass` | same function, ST_GAS class gate |
| 14 | `coal_nameplate_summer_derate` | ERCOT | `cc_nameplate_summer_derate` | `fleet/arrays.py::_availability_matrix`, the coal analogue of the row's flag |
| 15 | `ct_intermediate_split` | MISO, PJM | `offer_curve_by_group` | `data/offer_curves.py::_offer_curve_for_group` |
| 16 | `ct_intermediate_cf_threshold` | PJM | `offer_curve_by_group` | same function, cohort threshold of #15 |
| 17 | `st_gas_intermediate_split` | MISO | `offer_curve_by_group` | same function, ST_GAS leg |
| 18 | `cc_intermediate_split` | MISO | `offer_curve_by_group` | same function, CC_REGULAR leg |
| 19 | `offer_curve_smoothing_mid` | ERCOT, PJM | `offer_curve_by_group` | `fleet/assembly.py` econ-ramp shape of this row's curves |
| 20 | `ct_drag_slope_per_gw` | CAISO, PJM | `netload_drag_floors` | `fleet/floors.py::apply_ct_netload_drag_floor` |
| 21 | `ct_drag_intercept` | CAISO, PJM | `netload_drag_floors` | same |
| 22 | `ct_drag_cap` | CAISO, PJM | `netload_drag_floors` | same |
| 23 | `gas_st_drag_slope_per_gw` | PJM | `netload_drag_floors` | `fleet/floors.py::apply_gas_st_netload_drag_floor` |
| 24 | `gas_st_drag_intercept` | PJM | `netload_drag_floors` | same |
| 25 | `gas_st_drag_cap` | PJM | `netload_drag_floors` | same |
| 26 | `gas_st_drag_seasonal` | ERCOT | `netload_drag_floors` | same function; the row's def abbreviates it as `(+seasonal)` |
| 27 | `temp_derate_classes` | MISO | `temp_dependent_derate` | `fleet/arrays.py::_availability_matrix` scope |
| 28 | `temp_derate_hourly_grain` | MISO | `temp_dependent_derate` | same, input grain |
| 29 | `temp_derate_mean_anchored` | MISO | `temp_dependent_derate` | same, curve anchor |
| 30 | `temp_derate_slope_st_chp` | MISO | `temp_dependent_derate` | same, per-class slope |
| 31 | `temp_derate_slope_ct_chp` | MISO | `temp_dependent_derate` | same, per-class slope |
| 32 | `chp_export_floor_measured` | ERCOT | `chp_steam_following` | `fleet/assembly.py`; row def abbreviates it |
| 33 | `chp_steam_floor_p25` | CAISO | `chp_steam_following` | `fleet/assembly.py`; row def abbreviates it |
| 34 | `cc_outage_derate_from_top` | CAISO, PJM | `campd_outage_windows` | `fleet/arrays.py::_apply_outage_overlays`, the function this row owns |
| 35 | `st_gas_mustrun_p25_level` | MISO | `st_gas_mustrun_p25` | `fleet/arrays.py`; row def abbreviates it as `p25 level` |
| 36 | `class_aware_fuel_price_fallback` | MISO | `gas_plant_monthly_pricing` | `data/fuel/plant_prices.py`; row def abbreviates it as `class_aware` |
| 37 | `gas_hh_monthly_shape` | ERCOT | `gas_daily_shape` | `data/fuel/trajectories.py::gas_seasonal_shape`, the monthly-grain sibling |
| 38 | `oil_primary_bin_fuel` | ERCOT | `use_campd_bins` | `fleet/assembly.py::bins_to_fleet`, the function this row owns |
| 39 | `carry_operating_mothballs` | MISO | `plant_level_fleet` | `fleet/eia860.py::load_mothballed_but_operating` |
| 40 | `gas_st_wefor_base_override` | MISO | `wefor_statistical_stack` | `fleet/arrays.py` ST_GAS WEFOR base |
| 41 | `wefor_residual` | ERCOT, PJM | `wefor_statistical_stack` | `fleet/arrays.py`; row def abbreviates the family as `etc.` |
| 42 | `wefor_residual_groups` | ERCOT | `wefor_statistical_stack` | `fleet/arrays.py`, scope of #41 |
| 43 | `unit_outage_maxgen_events` | MISO | `unit_outage_short_windows` | `fleet/arrays.py` — "the third window shape" of this row's family |
| 44 | `storage_as_commitment` | ERCOT | `storage_measured_anchors` | `model/reserves/spec.py` measured storage-AS reservation |
| 45 | `tranche_startup_conditional_runs` | MISO, PJM | `tranche_startup_amortization` | `model/commitment.py` `run_ratio_t`; row def abbreviates it |

**Expected: 19 rows edited, ZERO new rows, all six ISOs' shared-gap counts → 0, ratchet
`shared_armed_on_keeper` empty for all six.**

## §3 — scope B: repair EVERY stale line anchor in the file (mechanical, measured first)

`nyiso-121` found all 20 MISO anchors stale and filed a standing checker as a suggestion.
**Measured this session across the whole file, the damage is near-total:**

| anchor form | total | resolves | **STALE** | skipped |
|---|---|---|---|---|
| `<field> :<line>` (sub-scalar registrations) | 152 | **4** | **120** | 26 (token is not a `ScenarioConfig` field) |
| row-`id` `scenarios.py:<line>` | 43 | **0** | **43** | 140 rows with no such anchor |
| `<path>.py:<line>` in-range | 99 | 31 in range, 0 out of range | 0 | 68 unresolvable path |

**163 stale anchors, 4 correct.** Most are off by ~900–1,400 lines (`scenarios.py` grew);
several are off by exactly 10, the same authoring-vs-merge drift nyiso-121 recorded.
This session repairs **all 163 mechanically**: the field literal uniquely determines the
correct line, and **only the digits change**. Verified by K-4 below.

Anchors whose token is **not** a `ScenarioConfig` field are **NOT touched** — that bucket
holds both the deliberate `miso_pjm_lmp :2914` defect quotation and ordinary prose
false-positives (`a stale :2138`, `read :3618`).

## §4 — scope C (TASK 1b): the standing anchor-resolution check, with a ratchet

Add an anchor leg to `scripts/check_mechanism_matrix.py`, three sub-checks:

* **A.** every `<field> :<line>` whose token IS a `ScenarioConfig` field must resolve to a
  `scenarios.py` line whose stripped text starts `<field>:`. **Existence is checked
  first**, so a non-field token is skipped — the deliberate-quotation carve-out.
* **B.** every row whose `id` is a `ScenarioConfig` field and whose `def` carries
  `scenarios.py:<line>` must resolve the same way.
* **C.** every `<path>.py:<line>` whose path resolves must have `<line>` within the file;
  an unresolvable path is skipped and COUNTED, never silently dropped.

Ratchet `docs/codebase-site/data/mechanism-matrix-anchors.json`, same contract as
`mechanism-matrix-gaps.json`: CI fails on any unresolvable anchor not already allowed, so
the list can only SHRINK. Target after §3: **empty**.

## §5 — pre-declared tie-breaks and the ONE cell mismatch, declared BEFORE writing

Two homes have a defensible alternative. The rule, fixed now: **prefer the row whose code
owns the function the field is read in; where both qualify, prefer the row whose cell
state does not MISREPRESENT the field's keeper-armed status** — because a census may not
change a cell to fix the misrepresentation (rule 28(d)).

* #13 `gas_st_startup_cost` → `p1_bidcost_pass`, not `gas_st_startup_spread`. Both are
  legs of `compute_monthly_markup`; `p1_bidcost_pass` owns that function outright, and its
  cells are `KKKKKK` against the field being armed on the ERCOT **and** MISO keepers,
  whereas `gas_st_startup_spread` reads `U` in both.
* #37 `gas_hh_monthly_shape` → `gas_daily_shape` (`KKKKKK`, ERCOT armed), not
  `gas_monthly_actuals`, whose ERCOT cell is `G` for the **LEVEL** swap this field's own
  comment records as the rejected alternative to its SHAPE claim.

**ONE mismatch survives and is DECLARED, not fixed:** #14 `coal_nameplate_summer_derate`
is ARMED on the ERCOT keeper, and its only code-level home
(`cc_nameplate_summer_derate`) carries ERCOT `U` — correctly, because that row's own flag
is `False` on the ERCOT keeper. **The cell is NOT touched.** The registration states the
mismatch and FILES it for the ERCOT lane. Any other mismatch discovered while writing is
recorded the same way and never resolved by a cell edit.

## §6 — the KILLS that govern this session

* **K-1 — ZERO `cells:` changes, anywhere, including audit rows.** Stricter than
  nyiso-121, which minted one audit status: this session mints **nothing at all**.
  NEISO's `matrix_gap_census` `O` is NEISO's lane's call and is not touched.
* **K-2 — ZERO verdicts and ZERO transcribed adjudications.** Every sentence added is
  either (a) a description of what the field does, sourced to the field's own committed
  comment/docstring, or (b) a CONSTRUCTION fact measured in this session and labelled as
  an observation. If a registration cannot be written without asserting a verdict, the
  field is registered with its description alone and the question is FILED.
* **K-3 — no re-derivation, no solve, no tuning.** No `ScenarioConfig` value, no constant,
  no derive script, no artifact. Rule 22: the holdout spend freeze is ACTIVE; no year
  outside 2023–2025 is solved, scored or read, and no year is solved at all.
* **K-4 — the anchor repair changes ONLY digits.** Discharged mechanically: with every
  `:\d+` in the file normalised to `:N`, the before and after texts must be
  **byte-identical outside the 19 registration edits**.
* **K-5 — NO shared field is enumerated as a bare literal in any row's PROSE.** This is
  the nyiso-121 §6.2 finding applied to the lane it was found for. Registrations go in
  `def:`, which is where `coverage()` looks; the census note gets a **count plus a pointer
  to the committed `_matrix_gap_sweep_<ISO>.json`**, never a list.

## §7 — the ONE measurement, pre-specified (observation O-1)

A `run_config.json` recording a scalar overstates what the solve read when the scalar's
**gate** is off — the caiso-161 §5 / pjm-151 / nyiso-121 G-1 shape. Scanning the six
keepers' configs for each of the 45 fields' code-level gate surfaces **7 candidate pairs
in 2 ISOs**, pre-registered here as observations, never as cell verdicts:

* **CAISO** — `ct_drag_slope_per_gw` 0.00901 / `ct_drag_intercept` −0.1124 /
  `ct_drag_cap` 0.36, with `ct_netload_drag=False`.
* **ERCOT** — `coal_prb_passthrough_floor` 0.76 with `coal_prb_passthrough_sigmoid=False`;
  `coal_lignite_passthrough_floor` 0.675 + `coal_lignite_passthrough_ceil` 1.0 with
  `coal_lignite_passthrough_sigmoid=False`; `coal_prb_follower_floor` 0.76, gated on
  `coal_prb_passthrough_sigmoid AND coal_prb_passthrough_tiered`.

**GATE O-1, written on CONSTRUCTION and not on a solved dual** (the nyiso-115 G2 /
nyiso-118 lesson, and the nyiso-121 G-1 pattern). Build each quantity **twice at one
HEAD** — the scalar at its keeper value vs a large perturbation — with the gate at its
keeper setting, and diff with `np.array_equal` on float32, **exact equality, not a
tolerance**.

* **O-1 PASS (inert):** exactly equal ⇒ the scalar is provably unreadable on that keeper.
* **O-1 FAIL (live):** any difference ⇒ the hypothesis is WRONG and **that is recorded as
  a failed pre-registration**, never quietly redefined (nyiso-115 G2 / nyiso-117 G2a /
  nyiso-119 G4 / nyiso-121 §6 discipline).
* **O-1 UNINFORMATIVE:** if a quantity cannot be built, it is reported UNINFORMATIVE,
  never as a pass.
* **MANDATORY POSITIVE CONTROL:** the same perturbation with the gate **ON** must
  SEPARATE. If it does not, that quantity's result is VOID — an instrument must be shown
  to separate before its silence is trusted.

**No cell moves on O-1.** Whether an inert scalar is cosmetic, a rule-19 `[R-ONE-MECH]`
question, or a rule-26 `[R-DELETE]` candidate belongs to a lane that may adjudicate that
ISO. A census may not (rule 28(d)).

## §8 — what this session does NOT do

* **No mechanism is tested, chartered or queued in any ISO**, and no lever queue is
  touched. A census does not manufacture a successor.
* **No ISO's own-family column is re-opened** (rule 28(a) DO-NOT-REDO: all six are closed).
  MISO's two filed-not-adjudicated observations (`miso_pjm_border_anchor`,
  `miso_firm_imports`) stay the MISO lane's, and NEISO's `matrix_gap_census` `O` stays
  NEISO's.
* **No keeper, gate, determination or `calibration-complete.json` entry changes** in any
  ISO. No promotion is made, so rule 22 D-5(b) does not fire and no determination
  re-verification is owed.

## §9 — falsifiable success criteria

1. `mechanism_matrix_gap_sweep.py` reports **shared-gap 0** for all six ISOs, and the
   ratchet's `shared_armed_on_keeper` is empty for all six.
2. Every ISO's family counts stay **0 absent / 0 prose-only / 0 armed-no-cell**, and the
   row count is **169 → 169** (zero new rows).
3. **Every `cells:` string is byte-identical to main.** Zero cell changes (K-1).
4. `scripts/check_mechanism_matrix.py` passes, **including the new anchor leg**, and the
   anchor ratchet is **empty** (0 unresolvable anchors of forms A and B).
5. The anchor repair is digits-only: with `:\d+` normalised, the diff is confined to the
   19 registration edits (K-4).
6. **The `live_but_invisible` count may only SHRINK, and every field that leaves a
   live-but-invisible list must be one of the 45 registered ON A ROW** — never a prose
   mention. This is the nyiso-121 §6.2 criterion restated for the lane it was filed for;
   a shrink attributable to prose is a FAILURE, not a pass.
7. O-1 is reported for all 7 pairs with its positive control, whichever way each lands.
