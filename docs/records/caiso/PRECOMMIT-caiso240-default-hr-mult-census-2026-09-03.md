# PRECOMMIT — caiso-240: the `_DEFAULT_HR_MULT_BY_GROUP` CENSUS (rule 24 `[R-REGISTRY]`)

**Registered 2026-09-03, session caiso-240. Branch
`claude/caiso-239-hr-mult-census-ycpdgu`, at `origin/main` (`c73f78f5`), zero
commits ahead at cut. PUSHED BEFORE ANY FOOTPRINT MEASUREMENT AND BEFORE ANY
SOLVE. No fleet has been rebuilt, no LP has been built and no solver has been
called in this session.**

Keeper at entry: **`2026-09-02-caiso-239-b1-stgas`** (bundle
`results/calibration/caiso239_b1_stgas_committed_measured`), determination
**NOT-YET**, **C3a the SOLE load-bearing FAIL** (+4.1 % 2023 **PASS** / +12.6 /
+15.6 %); C1 12/12 free 8/8; C2 / C3b / C4 PASS; C3c the single ledgered caveat
(standing rule, non-downgrading); C6 attested; C8 PASS; `audit_keepers --iso
CAISO` PASS 0/0. DOF ledger 9 entries / 6 residual. CAISO holds **no `complete`
and no `final` marker**; the holdout spend freeze is **ACTIVE**. Every read and
every solve in this session stays inside **2023–2025**.

---

## §0 — WHAT THIS SESSION IS, AND THE DISCLOSURES THAT CONDITION IT

**§0.1 — The object is caiso-239 §9 item 1: the `_DEFAULT_HR_MULT_BY_GROUP`
CENSUS.** It is a rule-24 `[R-REGISTRY]` **structural-integrity** lane, **NOT a
C3a lever**. Per rule 1 `[R-STRUCT]` and the caiso-238/239 charters, **no
conclusion in this session is argued from the price residual**, in either
direction. The owner's standing standard applies: *structural integrity
improving while a gate regresses may still be a keeper.* The deliverable is a
**costed, pre-adjudicated ask per cell**; execution is capped at **at most ONE**
CAISO cell, under the pre-registered decision rule of §6.

**§0.2 — THE OBJECT ITSELF.** `data/fleet/campd_bins.py::_DEFAULT_HR_MULT_BY_GROUP`
carries **28 uncited float literals** — seven plant groups (`CC_CHP`,
`CC_REGULAR`, `CT_CHP`, `CT_PEAKER`, `ST_GAS`, `ST_CHP`, `COAL`) × four bands
(`mr`, `mc`, `econ`, `peak`):

| group | mr | mc | econ | peak |
|---|--:|--:|--:|--:|
| CC_CHP | 1.05 | 1.05 | 1.00 | 1.45 |
| CC_REGULAR | 1.10 | 1.08 | 1.00 | 1.55 |
| CT_CHP | 1.05 | 1.10 | 1.00 | 1.15 |
| CT_PEAKER | 1.05 | 1.12 | 1.00 | 1.10 |
| ST_GAS | 1.10 | **1.15** | 1.00 | 1.10 |
| ST_CHP | 1.05 | 1.10 | 1.00 | 1.10 |
| COAL | 1.00 | 1.15 | 1.00 | 1.05 |

None appears in any `run_config.json`; none is counted by
`build_dof_ledger._count_scalars` (which reads `offer_curve_by_group` only);
none carries a citation. caiso-239 repaired exactly **one** cell — `ST_GAS.mc`,
CAISO only, via the gated `caiso_st_gas_committed_measured`. The other 27 stand
unaudited, in every ISO.

**§0.3 — FULL DISCLOSURE: WHAT WAS READ BEFORE THIS FILE WAS PUSHED.** Following
the caiso-238 §0.6 / caiso-239 §0.2 pattern, and stated first because it
conditions what §4 can honestly pre-register. Before pushing I read **source**
(`campd_bins.py`, `assembly.py`, `offer_curves.py`, `scenarios.py`) and the
**committed config artifacts** of all six keepers' `run_config.json`, plus the
six `data/raw/reference/<iso>_campd_marginal_hr_summary.csv` headers. That is
the *route* half of the census and it is reported as §2 below. **No fleet has
been rebuilt and no footprint has been measured** — the whole of §3's method,
§4's predictions, §5's grades and §6's decision rule are registered against
**unmeasured** quantities. The caiso-238 error is precisely what §3 exists to
avoid: **a scalar's VALUE is not its FOOTPRINT, and no cell gets a grade in
this census until its footprint is measured on the built fleet.**

**§0.4 — HARD STOPS.** Training window only (2023 / 2024 / 2025); if a solve
happens, all three years in **one invocation and one bundle** (rule 16
`[R-ALLYEARS]`), **sequential** (rule 12 `[R-PARALLEL]`). No
`calibration-complete.json`, `holdout-freeze.json`, keeper shard, or other ISO's
files touched except as §8 names. **No mechanism is armed outside CAISO**
(rule 25 `[R-ISO-SCOPE]`) — a cell measured live in another ISO produces an ASK
for that ISO's lane, never an arm here, and never a cross-ISO value transfer.
No P2. No off-registry knob (rule 24). No derive script re-run (rule 23
`[R-FROZEN-DERIVE]`). Object 2 (§7) is **PROPOSE ONLY — DO NOT EXECUTE**.

**§0.5 — DO-NOT-REDO acknowledged (rule 28(a)).** Re-read in full: caiso-239 §8
and caiso-230 §9. Not re-opened, not re-proposed, and not offered as a C3a
instrument anywhere below:
1. `offer_curve_by_group["ST_GAS"]["committed"]` as a repair target for CAISO's
   OTC steamers, and `avg_committed_p50` armed on it — both adjudicated on
   measurement (footprint 2/25, both plants retired; disjoint population).
2. Transferring CAISO's 1.683 to ERCOT's six bypassed ST_GAS plants
   (3504/3453/3490/3507/3576/4266) — their matrix cell is `U`; an ERCOT lane
   derives ERCOT's own `avg_committed_p50` or the cell stays `U` (rule 25).
3. `st_gas_committed_measured_bypass` as a C3a lever (it COSTS C3a).
4. The measured **BID** committed multipliers (CC 1.030 / CT 1.166) for any
   CAISO gas class — the Lever-A refusal stands uniformly (rule 19
   `[R-ONE-MECH]`). Every grounding proposed below is on the **PHYSICAL** basis,
   a different object, deliberately not merged with it.
5. Re-censusing `offer_curve_by_group` (caiso-238 did it: 112 scalars, 42
   dead/inert).
6. The whole caiso-229 / 230 / 233 / 234 / 235 / 224 / 221 closure list; the
   W-1/W-2/W-3 sweep, **DATED** to the Order-881 AAR effective date
   (≤ 2026-12-01) and **not swept here**.

**§0.6 — PROCESS DEVIATION, DECLARED: NO CONTROL ARM.** Standing owner directive
recorded at caiso-231 (*"that's one in like 1000 runs … I don't want to measure
drift"*): a single-delta calibration arm is solved ONCE and scored against the
committed keeper. If §6 fires, this session solves **one** arm and scores it
against `caiso239_b1_stgas_committed_measured`'s committed metrics. **G-CTRL is
not a spent LP run.**

**§0.7 — TWO INHERITED GATE-SPEC DEFECTS, ADOPTED HERE, NOT RE-DISCOVERED**
(caiso-239 §6):
1. **G-CTRL as "one `run_config` field differs" is UNSATISFIABLE** against a
   keeper more than a day old — caiso-239 measured 22 differing fields, every
   one HEAD drift. **G-CTRL is specified here as a DISPATCH-IDENTITY check
   instead**: in every year in which the armed mechanism is measured INERT, the
   arm's class energy must reproduce the keeper's to **0.001 TWh in every
   class**. That is strictly stronger evidence than a field diff, and it is the
   route the caiso-231 directive itself prescribes (a source diff, never a spent
   run).
2. **The caiso-230 §H bound is DEGENERATE at zero** when no responsive tranche
   is ever the matched marginal rung. Every bound in §5 is therefore stated as
   *"zero to within the estimator's attribution tolerance"*, never as an exact
   zero, so the gate cannot self-falsify on rounding. The §H form counts only
   zone-hours where the repriced rung is itself the matched marginal rung within
   the estimator's $0.75 tolerance and cannot represent indirect re-dispatch;
   that limitation is disclosed in advance, not after a miss.

**§0.8 — RAISED FOR THE OWNER, UNRESOLVED (carried from caiso-239 §6.1).** The
caiso-231 "NO CONTROL ARMS" directive rests on the warrant that a control once
reproduced the keeper to the cent. caiso-239 could only check that because its
mechanism was inert in two of three years. **If the cell §6 executes is measured
LIVE IN ALL THREE YEARS, there is NO independent check at all** — the §0.7(1)
dispatch-identity route needs at least one inert year to bind, and the
`run_config` field diff supplies nothing. This session will state explicitly, in
its FINDING, whether its arm had an inert year, and will flag the gap to the
owner if it did not.

---

## §2 — THE ROUTE CENSUS (source + committed config; §0.3 disclosed)

This is the *analytic* half — which code paths can reach each cell. It fixes
**where to look**; §3 measures **what is actually there**. Recorded here so
§4's predictions are falsifiable against it.

**§2.1 — TWO consumption sites, with different reach.**
* **Site A — `campd_bins.py:1063`**, the ERCOT curated-CSV bin path
  (`use_campd_bins=True, plant_level_fleet=False`). The default is a
  **blank-cell fill**: `_fill_hr_multiplier(csv_value, default)` uses the
  literal only where the sheet's `HR_Mult_<tranche>` cell is blank or ≤ 0.
* **Site B — `campd_bins.py:2337`, inside `fleet_to_bins`**, the per-plant
  non-ERCOT path (`plant_level_fleet=True` — PJM, CAISO, NYISO, NEISO, MISO).
  **Every** band heat rate is set unconditionally to `base_hr × default`:
  `hr_mr`, `hr_mc`, `hr_econ`, `hr_peak`. The literals are the sole source.

**§2.2 — What `bins_to_fleet` then overrides, band by band** (`assembly.py`
713–1005). `offer = _offer_curve_for_group(group, plant_code, config)`:
* `committed_hr` ← `base_hr × offer["committed"]` **only when `offer is not
  None`**.
* `peak_hr` ← `offer["peak"]` (or the CC duct-burner map) **only when `offer is
  not None`**.
* the econ tranche(s) ← `offer["econ_low"/"econ_high"]` **only when `offer is
  not None`** (or a per-plant sheet `ov`, or `econ_split_by_group` — both empty
  on all six keepers). Otherwise the single flat tranche is built at `econ_hr`,
  i.e. at the literal.
* **`mustrun_hr` IS NEVER OVERRIDDEN BY AN OFFER CURVE.** The only writer is the
  per-plant sheet `ov`. It flows straight into the `mustrun` and `sync`
  tranches (lines 1155, 1265).

**§2.3 — CONSEQUENCE, registered as the census's structural claim.** On the five
plant-level ISOs the seven **`mr`** literals are **structurally unreachable by
the offer-curve registry**: no value in `offer_curve_by_group` can move them,
and `gas_offer_margin_markup_mult` explicitly returns **0.0** for the `mustrun`
and `sync` suffixes, so those tranches are also outside the
`gas_offer_net_revenue_margin` physical-basis decomposition. They price fully
fuel-scaled at an uncited literal. That is a *route* claim; §3 measures whether
any such tranche carries capacity.

**§2.4 — Where `mc` / `econ` / `peak` can still be live: the BYPASS SET.**
`_offer_curve_for_group` returns `None` when (a) the group key is absent from
the ISO's `offer_curve_by_group`, (b) `group == "ST_GAS"` and the plant is in
`ST_GAS_PEAKER_PLANTS`, or (c) COAL resolves neither a supply-specific nor a
generic `COAL` entry. Read off the six committed keeper `run_config.json`s:

| ISO | keeper | path | groups with NO offer-curve key |
|---|---|---|---|
| ERCOT | `2026-08-25-234-eastex-identity` | A (CSV) | **ST_CHP, COAL** (+ all four COAL_* keys absent) |
| PJM | `2026-08-15-pjm-162-inputclock` | B | **ST_CHP** |
| CAISO | `2026-09-02-caiso-239-b1-stgas` | B | **ST_CHP** |
| NYISO | `2026-09-02-nyiso-177-vintage-matched` | B | **ST_CHP** |
| NEISO | `2026-08-17-neiso-99-joint-p1` | B | **ST_CHP** |
| MISO | `2026-09-02-miso-201-stbasis` | B | **ST_CHP** |

`ST_CHP` carries **no offer curve in any of the six keepers**, so its `mc`,
`econ` and `peak` literals are on the bypass route in **every ISO**. ERCOT
additionally has **no COAL key at all**, putting `COAL.mc` / `COAL.econ` /
`COAL.peak` on the bypass route there (attenuated by site A's blank-cell rule).
`ST_GAS` is on the bypass route for `ST_GAS_PEAKER_PLANTS` members in every ISO.
`econ_split_by_group` is `{}` and both per-band overrides
(`gas_st_committed_hr_override`, `cc_committed_hr_override`) are `None` on all
six.

**§2.5 — The 29th exposure, named so it is not missed.** Line 1063 and line 2337
both fall back to `_DEFAULT_HR_MULT_BY_GROUP["CC_REGULAR"]` for any
`Plant_Group` absent from the dict. CC_REGULAR's four literals therefore also
price any unlisted group. §3 measures whether any such group exists in any
keeper fleet.

---

## §3 — THE CENSUS METHOD, FIXED BEFORE ANY MEASUREMENT

**Instrument:** `scripts/probes/_caiso240_default_hr_mult_census.py` →
`results/calibration/_caiso240_default_hr_mult_census.json`. **ZERO SOLVES.**
The rebuild harness is imported UNCHANGED from
`scripts/probes/_caiso239_st_gas_committed_footprint.py` (itself the caiso-230
§H form re-pointed), and the marginal-rung attribution / §H bounding form come
from `_caiso230_abovefloor_decomposition.py`, re-pointed at **each ISO's own
keeper** as caiso-230 §9 and rule 25 require.

**§3.1 — Footprint, per (ISO, group, band).** For each ISO, rebuild its keeper's
offer surface with `run_year(fleet_only=True)` (assembles the fleet,
availability and the P0 objective; builds no matrix, calls no solver), reading
the kwargs from the keeper bundle's own `meta.json`. Rebuild **once at
baseline** and **once per perturbation pass** with
`campd_bins._DEFAULT_HR_MULT_BY_GROUP` mutated in place, then diff `mc_base`
**row by row**. A tranche is **responsive** to a cell iff its `mc_base` moves.
Because every LP row belongs to exactly one `(group, tranche-band)`, one
perturbation pass that scales **all 28 cells** by a common factor attributes
each responding row to its own cell unambiguously.

**§3.2 — TWO perturbation magnitudes, both reported.** ×1.02 (small: cannot flip
a band ordering, cannot cross a clip) and ×1.25 (large: reaches a cell whose
response is suppressed by a clip at small amplitude). A cell live at ×1.25 and
dead at ×1.02 is **reported as clip-suppressed**, never silently merged.

**§3.3 — CACHE HAZARD, declared with its own falsifier.**
`campd_bins._CAMPD_BINS_CACHE` and several `lru_cache`d loaders would defeat an
in-place mutation. The probe clears them between passes. **Method falsifiers,
both of which must pass before any census row is reported:**
* **M-1 (null pass):** a baseline→baseline rebuild with **no** mutation is
  **byte-identical** in `mc_base` for every row. Falsifier: any row moves.
* **M-2 (two-point validation against caiso-239's own measured result):** on the
  **caiso-231 predecessor recipe** (`results/calibration/caiso231_b1_ungrounded`)
  the `ST_GAS.mc` cell is responsive on **exactly 3** CAISO tranches — plants
  **315, 335, 350** — reproducing caiso-239 F-1; and on the **caiso-239 keeper**
  the SAME cell is responsive on **ZERO** tranches, because
  `caiso_st_gas_committed_measured` retired it. Falsifier: either count differs.
  M-2 validates the instrument **and** independently verifies that caiso-239's
  repair actually retired the literal it claimed to retire.

**§3.4 — Materiality, per live cell.** Available capacity-hours
(`Σ pmax × availability`), tranche count, distinct plant count, and the cell's
share of the ISO's own keeper class dispatch, read from the keeper's committed
`hourly/` sidecars — never from a replay.

**§3.5 — Counterpart, per live cell.** Does a **population-matched** measured
counterpart exist and is it **already committed**? The candidate instrument is
`data/raw/reference/<iso>_campd_marginal_hr_summary.csv`
(`avg_committed_p*` = the measured part-load block-average burn ratio;
`avg_econ_low_p*` / `avg_econ_high_p*` = measured incremental burn at the ramp
endpoints; `n_units` and `base_hr` per class). **Population match is a
measurement, not an assertion**: the probe resolves the CAMPD unit population
behind the ISO's row (via `campd_gas_commitment_params_<ISO>_units.csv` where
present) and compares it to the plant set the cell actually prices, per §3.1.
A counterpart whose population is disjoint from the cell's footprint is
**REFUSED**, on rule 14 `[R-ACCURATE]`'s own stated boundary exception — the
caiso-239 F-3 form.

**§3.6 — Adverse C3a bound, per live CAISO cell.** caiso-230 §H form
(`|Δλ| ≤ Σ ω·p_z·|Δmult/mult|` over the zone-hours where the tranche is the
matched marginal rung, annualised on the scorer's zone-hour load-weighted
basis), re-run on the **caiso-239 keeper**. Stated per §0.7(2). For non-CAISO
cells the bound is computed **on that ISO's own keeper** and reported as
information for that ISO's lane — never as a reason to arm anything here.

---

## §4 — PREDICTIONS, EACH WITH ITS FALSIFIER (registered before measurement)

Scored against interest in the FINDING, whatever they read.

* **P-1 — the `mr` family is the census's largest exposure.** On the five
  plant-level ISOs, at least one `mr` cell is measured live on ≥ 10 LP tranches,
  and the `mr` family's total live capacity exceeds the `mc` family's.
  **Falsifier:** the `mr` family's live tranche count is ≤ the `mc` family's, or
  zero.
* **P-2 — `mc` / `econ` / `peak` are live ONLY inside §2.4's bypass set.** No
  responsive `mc`, `econ` or `peak` row appears for a (ISO, group) pair that
  resolves an offer curve. **Falsifier:** any such row.
* **P-3 — ST_CHP's three bypass cells are live in at least one ISO.** MISO's
  measured summary carries an `ST_CHP` row (`n_units = 1`), so at least one
  ISO's fleet contains ST_CHP plants whose `mc`/`econ`/`peak` are set entirely
  by uncited literals. **Falsifier:** zero ST_CHP LP tranches in all six keeper
  fleets — in which case those three cells are **DEAD**, not off-registry, and
  are reported as such.
* **P-4 — ERCOT's exposure is materially SMALLER than the plant-level ISOs'**,
  because site A only fills blank cells. Specifically I predict ERCOT's total
  responsive tranche count is below the median of the five plant-level ISOs'.
  **Falsifier:** ERCOT is at or above that median.
* **P-5 — `COAL.mc` / `COAL.peak` are DEAD or near-dead on ERCOT** despite the
  missing COAL offer key, because ERCOT's curated bin sheet populates the
  `HR_Mult_*` columns for coal. **Falsifier:** ≥ 1 responsive ERCOT coal
  tranche.
* **P-6 — CAISO's largest remaining exposure by capacity is an `mr` cell, not an
  ST_GAS cell.** After caiso-239 the ST_GAS bypass reaches three plants
  (2,858.8 MW) on three bands; a live `mr` cell would reach the whole gas fleet.
  **Falsifier:** CAISO's largest live cell by capacity-hours is not in the `mr`
  family.
* **P-7 — the DOF ledger will NOT move**, for any outcome of this session, for
  the caiso-239 §7 reason: `build_dof_ledger._count_scalars` reads
  `offer_curve_by_group` only and is blind to `campd_bins.py`. Predicted
  `n_entries` 9 / `n_residual` 6, unchanged. **Falsifier:** either moves. (This
  is a gate-specification defect, disclosed for the third time, not a claim that
  the repair is worthless.)

---

## §5 — THE PER-CELL GRADING TAXONOMY

The caiso-238 F1–F4 classes, **with a mandatory footprint precondition in front
of them** — the caiso-238 error, made structurally impossible:

* **F0 — DEAD / INERT.** Measured footprint is **zero tranches** on that ISO's
  keeper (or non-zero but at zero availability in every hour of every year).
  **No ask.** The cell is recorded as a latent literal that would become live
  under a config change, and that condition is named.
* **F1 — GROUNDABLE NOW.** Footprint non-zero AND a **population-matched**
  measured counterpart at the model's own grain exists AND is already committed
  in this repo AND arming it is a zero-free-parameter substitution admissible
  under rules 13/19/24/25. → a **solve-round** ask.
* **F2 — GROUNDABLE, INSTRUMENT NOT IN HAND.** Footprint non-zero; a counterpart
  is identified and publicly available but must be intaken through the data
  contract first. → a **data-intake** ask.
* **F3 — NOT GROUNDABLE AT THIS GRAIN.** Footprint non-zero; no measured object
  maps onto the quantity at the model's representation grain. → **no ask**; the
  literal is declared to the owner as residual.
* **F4 — REFUSED ON RULE.** Footprint non-zero; a counterpart exists and arming
  it is refused by a standing rule or an adjudicated lesson (rule 19, rule 13,
  rule 25 — including a **population-disjoint** counterpart, the caiso-239 F-3
  form). → **no ask**, and the refusal is recorded so it is never re-proposed.

**A cell in a NON-CAISO ISO can never be graded above an ASK here** (rule 25):
its grade and its bound are handed to that ISO's lane, and its matrix cell
enters as `U`.

---

## §6 — THE EXECUTION DECISION RULE, FIXED BEFORE MEASUREMENT

At most **ONE** CAISO cell is executed, and only if **all four** hold:

1. **F1** under §5 — footprint measured non-zero on the caiso-239 keeper AND a
   population-matched, already-committed measured counterpart.
2. It is the **largest** such CAISO cell by measured available capacity-hours
   (ties broken by tranche count, then by the keeper's own class dispatch).
3. **Zero free parameters**: the armed value is the measurement, read from the
   committed artifact, not chosen from a range. Where the artifact offers p25 /
   p50 / p75, **p50** is taken, fixed here in advance.
4. It clears the caiso-239 bar: gated, **default off**, CAISO-only with a **hard
   `ValueError`** for an ISO with no registry entry (never a silent fallback),
   **exactly one band moves**, threaded onto `--replay-bundle` as a single-flag
   delta, unit-tested, and matrix base row + a cell line in every ISO shard in
   the same PR (rule 28(c)).

**If no CAISO cell meets all four, NOTHING is executed.** That is a fully
legitimate pre-registered outcome — the deliverable is then the census plus the
asks, exactly as caiso-238 delivered. **The session will not manufacture an arm
to have solved something.**

**DIRECTION, DECLARED PER CELL BEFORE ANY ARM SOLVES.** For **every** min-load
cell (`mr`, `mc`) the direction is **ADVERSE**: CAISO's measured
`avg_committed_p50` exceeds every armed `mr`/`mc` literal for every gas class
(CC_CHP 1.028, CC_REGULAR 1.103, CT_CHP 1.073, CT_PEAKER 0.991, ST_GAS 1.683 vs
literals of 1.05–1.15), so a measured-faithful repair **raises** the min-load
offer and pushes C3a **UP** in years already over. Per rule 1 `[R-STRUCT]` that
is **never an argument against the repair** — it goes on the record first, and
the per-cell §3.6 bound is registered before the arm solves. **The single
exception, declared now:** `CT_PEAKER` is the one CAISO class whose measured
`avg_committed_p50` (0.991) sits *below* its `mr` literal (1.05); if that cell is
the one §6 selects, its direction is **FAVOURABLE**, which is disclosed as such
and is **equally not** a reason to prefer it — selection is by rule 2 above,
capacity, and nothing else.

**GATES, IF §6 FIRES — each with its falsifier.** (Adapted from caiso-239 §5,
with §0.7's two repairs already applied.)
* **G-CTRL** *(dispatch identity, per §0.7(1); a source diff, never a spent
  run)*: in every year in which the mechanism is measured inert, class energy
  reproduces the keeper's to **0.001 TWh in every class**; and the arm's
  `run_config.json` differs from the keeper's in the one new flag plus HEAD
  drift only, with **every** drifting field enumerated and attributed in the
  FINDING. **Falsifier:** an inert year whose class energy moves, or a drifting
  field that is a solve input.
* **G-STRUCT**: on the rebuilt fleet, **exactly** the pre-identified tranches of
  the pre-identified plants change heat rate, at the exact ratio
  `measured / literal`; **0** other bands, **0** other groups, **0** other ISOs.
  Verified pre-solve AND on the solved fleet. **Falsifier:** any other row or
  band moves.
* **G-INERT**: the arm is **not** byte-identical to the keeper in all three
  years — the mechanism must actually do something. **Falsifier:** identical
  annual metrics in all three years (in which case the repair is registered as a
  provably-inert structural correction and is **not** proposed as keeper on
  dispatch grounds).
* **G-C3a**: measured |ΔC3a| ≤ the §3.6 bound in every year, on the §0.7(2)
  tolerance reading; **no year flips verdict; 2023 stays PASS**. **Falsifier:**
  any year flips, or a move exceeding the bound (a bound violation is a defect
  in the estimator or the mechanism, reported as such, **never re-fitted**).
* **G-C1**: 12/12, free 8/8, unchanged. **Falsifier:** any C1 criterion
  regresses.
* **G-C3b**: PASS, with the 2025 composition-watch tripwire explicitly re-read.
  **Falsifier:** C3b fails, or 2025 crosses.
* **G-C8**: PASS — no material class over its forced-energy budget.
  **Falsifier:** any material class crosses.
* **G-CAVEAT**: the ledgered-caveat budget stays **1 of 1** (C3c alone).
  **Falsifier:** a second ledgered, or any protective, caveat appears.

**Promotion rule, fixed in advance:** the arm is proposed as keeper **only if**
G-CTRL, G-STRUCT, G-INERT, G-C1, G-C3b, G-C8 and G-CAVEAT all pass and G-C3a
shows **no verdict flip**. A C3a regression **within** the bound does not block
promotion (caiso-231/239 governing precedent); a verdict flip does.

---

## §7 — SECOND OBJECT: the `ST_GAS_PEAKER_PLANTS` DOUBLE DUTY — **PROPOSE ONLY**

caiso-239 §9 item 2. `data/outages.py::ST_GAS_PEAKER_PLANTS` is ONE frozenset
carrying **two distinct phenomena** (rule 19 `[R-ONE-MECH]`): (i) its documented
purpose — no outage overlay and no reliability floor for the OTC steamers — and
(ii) an offer-curve bypass in `_offer_curve_for_group` and
`_econ_split_for_group`, whose stated warrant is *"matching the
`gas_st_*_hr_override` scope"* — and **those overrides are `None` on the
keeper**, so the warrant is stale.

This session will **design and cost** the split — the two scopes separated into
two named sets, what each would then govern, which plants move, and the blast
radius (splitting it would move the OTC steamers' `econ` and `peak` bands too,
i.e. it is a real mechanism change, not a refactor). **It will NOT be armed, no
`ScenarioConfig` field is added for it, and no solve tests it.** The deliverable
is a costed ask.

**Also carried, PROPOSE-ONLY, NOT STARTED:** caiso-238 object 4
(`battery_dispatch_adder` → measured AS reservation + ATB degradation; F2, and
the strongest standing ask — materiality COMPOUNDING, li-ion 1.87 → 5.29 % of
generation), object 3 (own-curve shape derive), the SoCalGas OFO arm
(`PRECOMMIT-caiso227-ofo-arm-2026-08-31.md`), and the `IMPORT_TRANCHES[CAISO]`
LEVEL object.

---

## §8 — DELIVERABLES

1. **This PRECOMMIT, pushed to `origin` before any footprint measurement and
   before any solve.**
2. `scripts/probes/_caiso240_default_hr_mult_census.py` +
   `results/calibration/_caiso240_default_hr_mult_census.json` — the 28-cell ×
   6-ISO census with M-1 and M-2 reported first, zero solves.
3. `ASSESSMENT-caiso240-default-hr-mult-census-2026-09-03.md` — the census
   table, the per-cell F0–F4 grade with its footprint, the counterpart finding,
   the adverse bound, and a **costed, pre-adjudicated ask per cell**; plus §7's
   split design and cost.
4. **If and only if §6 fires:** the mechanism (gated, default off, CAISO-only,
   cited constant, `--replay-bundle` thread, unit tests), ONE arm — `--year 2023
   2024 2025` sequential, one invocation, one bundle (rules 12 / 16) —
   registered on the backcast dashboard **in this session** whether keeper or
   rejected probe (rule 15).
5. `FINDING-caiso240-default-hr-mult-census-2026-09-03.md` with §4's predictions
   and §6's decision rule **scored against interest**, and the §0.8 owner flag
   answered.
6. The `docs/calibration-log/caiso.md` caiso-240 entry; the CAISO mechanism-matrix
   shard updated whatever the outcome (rule 28(b)), with **non-CAISO cells
   entered as `U`**, never filled from a CAISO verdict (rule 25).
