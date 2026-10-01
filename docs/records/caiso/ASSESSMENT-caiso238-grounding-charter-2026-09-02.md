# ASSESSMENT — caiso-238: the GROUNDING CHARTER for the four class-(c) live residual DOF rows

**Session caiso-238, 2026-09-02. ZERO SOLVES.** Keeper
`2026-09-01-caiso-231-b1-ungrounded` **unchanged**, determination **NOT-YET**
(C3a the sole load-bearing FAIL). Nothing armed, no `ScenarioConfig` field
added/removed/changed, no verdict moved, no registration due (rule 15 does not
attach — no calibration run was produced). CAISO holds no `complete` and no
`final` marker; the holdout freeze is ACTIVE; every read is inside 2023–2025.

Pre-registered in `PRECOMMIT-caiso238-grounding-charter-2026-09-02.md`, pushed
to `origin` before any measurement was computed. Every number below comes from
`scripts/probes/_caiso238_grounding_charter.py` →
`results/calibration/_caiso238_grounding_charter.json`, reading only the
keeper's own `run_config.json` + `hourly/` sidecars, the committed offer-curve
registries and the fleet basis. **No LP was built and no solver was called.**

**Rule 1 `[R-STRUCT]` / §0.3 of the charter:** C3a is not this session's object
and is used nowhere as a ranking criterion. Where an object's expected C3a
direction is knowable it is **disclosed** — as caiso-231's was, before it was
promoted knowing it cost C3a.

---

## §1 — THE HEADLINE

Of the four rows caiso-236 §10 left "LIVE AND MATERIAL and deliberately not
touched", the measurement says:

| # | object | scalars | class | the ask |
|---|---|---|---|---|
| 1 | `offer_curve_by_group` | 112 | **F4** on the live fitted remainder, **+ a caiso-236 mis-classification** | no ask at this grain; **42 of the 112 scalars are dead or inert on this keeper** and belong in caiso-236's class (a)/(a′), not (c) |
| 2 | `ST_GAS` `committed` = 0.81 | 1 | **F1 — GROUNDABLE NOW** | **the one fundable solve-round ask**: the instrument is already committed in this repo |
| 3 | `offer_curve_smoothing_{n,exp}` | 2 | **F3** at this grain (F2 route named) | no ask now; the corpus that could measure it is payload-untracked |
| 4 | `battery_dispatch_adder` = 5.0 | 1 | **F2 — GROUNDABLE, INSTRUMENT NOT IN HAND** | **a data-intake ask**, and the fastest-growing residual in the ledger |

**Two fundable asks, not the one I pre-registered** (§6 scores that miss). Both
are structural-integrity asks under rules 14/21/25. **Neither is offered as a
C3a instrument, and object 2's disclosed direction is adverse.**

---

## §2 — OBJECT 1: `offer_curve_by_group` (112 scalars)

### Q1/Q2 — the census, and what is actually live

The probe reproduces the ledger's `n_scalars = 112` **exactly** (an independent
cross-check of `build_dof_ledger._count_scalars`), and splits it:

| provenance | scalars | what it is |
|---|---|---|
| `measured` | 15 | the caiso-231/caiso-51 bucket bands (`econ_low`/`econ_high`/`peak` on the five CAISO gas groups) |
| `measured-physical` | 20 | the `phys_*` block — `caiso_campd_marginal_hr_summary.csv` p50s, **LIVE** because `gas_offer_net_revenue_margin = true` on this keeper |
| `derived-from-peak` | 20 | the two `peak_ladder` blocks (5 rungs × (share, mult)), each rung's multiplier **equal to the group's own measured `peak`** |
| `fitted-geometry` | 20 | `econ_low_share` (×13) and `pct_peaking` (×7) |
| `fitted` | 37 | everything else |

**38 of the 112 sit on groups that carry ZERO CAISO dispatch in all three
years** — `CC_INTERMEDIATE`, `CT_INTERMEDIATE`, `ST_GAS_INTERMEDIATE`,
`COAL_LIGNITE`, `COAL_PRB`, `COAL_BIT`, `COAL_WC`. They are family entries the
generic registry carries for other ISOs. `cc_intermediate_split` is `false` on
this keeper, so the three `*_INTERMEDIATE` blocks cannot be reached at all.

**Fitted AND live: 19 scalars**, and they are three distinct things:

* **5 `committed` bands** — CC_REGULAR 1.000, CC_CHP 1.000, CT_PEAKER 1.350,
  CT_CHP 1.100, ST_GAS 0.810. These are the Lever-A-withheld set.
* **5 `econ_low_share`** — 0.50/0.50/0.526/0.50/0.50 on the gas groups.
* **4 `pct_peaking`** + the 5-scalar `COAL` block (1 plant, 50 MW,
  0.083 TWh = 0.04 % of generation).

### Q3/Q4 — instrument and admissibility

**The `committed` bands are F4, exactly as pre-registered.** A measured
counterpart exists in the same committed artifact
(`caiso_offer_curve_measured.json` carries `unarmed.committed` = 1.030 for the
CC bucket and 1.166 for the CT bucket) and arming it is refused by the
**adjudicated Lever-A inversion lesson**: min-load *self-commitment conduct*
belongs to unit commitment, not the P1 offer (rule 19 `[R-ONE-MECH]`; the
mechanism-matrix base row states the withholding in those words). caiso-231
applied the same refusal uniformly to all five CAISO gas classes. **No ask.**
Object 2 below is the one exception, and it is not this route — it grounds on
the *physical* basis, not on bid conduct.

**`econ_low_share` is F3.** There is no measured counterpart, and the
appearance of one is a trap: `derive_caiso_offer_surface.py` line 187 records
that the value it prints under `band_windows_geometry.econ_low_share` is
`ECON_LOW_SHARE[cls]` — *the armed value copied through, "kept, not
re-derived"*. Reading it back as a measurement would be circular. **No ask.**

### THE MIS-CLASSIFICATION, REPORTED AGAINST INTEREST

**`pct_peaking` is not class-(c) at all. All four live scalars are dead or
arithmetically inert on this keeper**, and caiso-236 (and this session's own
falsifier screen, which surfaced them as "fitted, live and material") had it
wrong:

* **CC_REGULAR and CC_CHP: DEAD.** `cc_duct_peaking = True` and
  `cc_peaking_per_plant = True`, and **every one of the 28 CC_REGULAR and 21
  CC_CHP plants is in the EIA-860 duct-burner map** — `n_fall_through_to_
  classwide = 0`, `mw_share_fall_through = 0.0000` for both. The class-wide
  8.0 is overwritten per-plant for 100 % of capacity before any tranche is
  built (`fleet/assembly.py` lines 551–582). The fleet's own cap-weighted
  peaking shares are **3.444 %** (CC_REGULAR) and **2.054 %** (CC_CHP), spread
  over 18 and 6 distinct per-plant values respectively.
* **CT_PEAKER and ST_GAS: INERT.** The offer curve overrides the CSV's
  `pct_peak` with 7.0 and 15.0 — and `bin_assignments_CAISO.csv` carries
  **exactly one distinct value** for each class, **7.0 and 15.0**, with
  `Peaking_Source = class_default` on every plant. The override rewrites each
  value with itself.

That last point also disposes of a tempting F1: the derive's
`band_windows_geometry.CT_PEAKER.pct_peaking = 7.0` is **not** an independent
measurement of anything — it is the class default read back out of the fleet
CSV it was seeded into. Only CC_REGULAR's 3.444 is a real measurement, and that
group's class-wide scalar is already dead.

### VERDICT — object 1

**F4 on the live fitted remainder; no grounding ask at this grain.** Filed for
caiso-236's ledger instead: **42 of 112 scalars** (38 on absent groups + 4
`pct_peaking`) are **class (a)/(a′), not (c)**. They are **not** proposed for
deletion here — the seven absent groups are cross-ISO family entries and the
`pct_peaking` keys are read by other ISOs' recipes, so this is caiso-236's
**(a′) keeper-dead-but-lane-live** class, whose whole point was that deleting
such an entry is a mechanism change, not a ledger repair.

---

## §3 — OBJECT 2: `ST_GAS` `committed` = 0.81 — **THE ONE F1**

### Q1/Q2 — live, and what it prices

`ST_GAS` on CAISO is **exactly three plants, 2,858.8 MW**, and they are the
coastal OTC steamers the caiso-231 bucket note names:

| plant | zone | MW | `Pct_Committed` | source |
|---|---|---|---|---|
| AES Alamitos LLC | SP15 | 1,142.0 | 6.5 % | `campd` |
| AES Huntington Beach LLC | SP15 | 225.8 | 9.3 % | `campd` |
| Ormond Beach | SP15 | 1,491.0 | 6.3 % | `campd` |

**The pre-registered falsifier does NOT fire** — the class is the three OTC/RMR
steamers and nothing else. Dispatch: **0.202 / 0.634 / 0.103 TWh**
(2023/24/25), **0.33 % / 1.13 % / 0.21 %** of CAISO gas energy, ≈0.05–0.29 % of
total generation. The class is small, and the ask below is made on integrity
grounds, not size (rule 14 `[R-ACCURATE]`; caiso-231 is the precedent — it
moved $0.03–0.06/MWh and was promoted).

### THE DEFECT

The `committed` tranche is the **minimum-stable-load block**, whose true
incremental heat rate is **above** the plant average — this is Lever A's own
stated physics (`_CAISO_OFFER_CURVE`, CC_REGULAR comment: *"min-load is
thermally inefficient … 0.90x avg priced the min-load block ~$1.2/MWh BELOW
true marginal cost AND below econ_low — an INVERTED merit order"*). Lever A
raised CC_REGULAR 0.90 → 1.00 and CC_CHP 0.92 → 1.00 on exactly that argument.

**ST_GAS was never given the same treatment.** It sits at **0.810**:

* **below the audit §2 physical floor of 0.85** — the row's own reason for
  existing (issue #1302), and the only CAISO band below it;
* **below its own `econ_low` (1.145) and `econ_high` (1.166)** — the *same
  inverted merit order* Lever A was created to remove, still standing on this
  class three sessions after caiso-231 re-grounded every other band on it;
* **48.1 % of CAISO's OWN measured physical basis.** `phys_committed = 1.683`
  is `avg_committed_p50` from `data/raw/reference/caiso_campd_marginal_hr_
  summary.csv` — CAISO's own CAMPD min-load block burn, already committed in
  this repo and already carried on the band dict. The armed offer prices the
  block at **0.81 / 1.683 = 0.481×** its measured burn.

And the value is **load-bearing, not decorative**: because
`gas_offer_net_revenue_margin` computes `markup = max(0, mult − phys)`, ST_GAS
committed markup is **exactly 0**, so `apply_gas_offer_margin` never touches the
row and the offer stands at the bare `0.81 × Plant_Avg_HR × delivered gas`. The
one measured object attached to this band is loaded and then **arithmetically
discarded**, precisely because the fitted multiplier sits below it.

### Q3/Q4 — instrument and admissibility

**The instrument is in hand.** `phys_committed = 1.683` is committed, frozen
(rule 23 `[R-FROZEN-DERIVE]`), CAISO-derived, and already resolved onto this
band. It is a **physical burn** measurement, not bid conduct — so it is **not**
the object the Lever-A lesson withholds. That refusal covers the measured *bid*
committed multiplier (CT bucket 1.166, self-commitment conduct); grounding on
the physical min-load burn is the same class of instrument Lever A itself used
when it set 1.00 as *"still CONSERVATIVE vs the true (>avg) min-load HR"*.
Rule 13 `[R-MEASURED]`: a class's min-load heat-rate ratio regenerates for a
forward year from CAMPD conduct and responds to fleet change — admissible.
Rule 25 `[R-ISO-SCOPE]`: CAISO-derived, no transfer. **Zero free parameters
added; one ERCOT-inherited scalar retires to measured.**

### Q5 — cost, and the DIRECTION, DISCLOSED

* **DOF:** −1 fitted scalar. `n_residual` 6 → 5 if the row retires entirely.
* **Session shape:** a **solve-round** ask — A/B against a bit-zero control,
  2023–2025 in one bundle (rules 12/16), pre-registered. It needs a gated
  mechanism (the existing `caiso_offer_surface_measured_ungrounded` arms
  `econ_low`/`econ_high`/`peak` only), so it also needs a **matrix row in the
  same PR** (rule 28(c)) — which is why it is an owner ask and not something
  this session may do.
* **DIRECTION — ADVERSE, DECLARED BEFORE ANY SOLVE.** Raising the ST_GAS
  committed offer (0.81 → ≥1.00, or → the measured 1.683) **raises** the floor
  in hours the class is marginal, i.e. it moves C3a the **wrong** way on a gate
  already over by +12.5/+15.6 %. It also un-clips the `gas_offer_net_revenue_
  margin` markup on the tranche. Per rule 1 and the caiso-231 precedent this
  is **not** an argument against the repair; it is what must be on the record
  before it is attempted. **The repair must never be proposed as a C3a lever**
  (caiso-230 DO-NOT-REDO item 3, extended here to the committed band).
* **The design question the owner is actually funding** is which value: the
  conservative **1.00** Lever A gave the CC classes (restores
  `committed ≥ econ_low` ordering, still below the measured burn), or the full
  measured **1.683** (physically faithful, but makes the min-load block the
  most expensive band on the class and restructures its merit order). That
  choice is a mechanism-design call with a real forward consequence, and it is
  the owner's, not a charter's.

---

## §4 — OBJECT 3: `offer_curve_smoothing_{n, exp}` = {6, 1.0}

**Q1 LIVE, and the fifth-outcome leg is REFUTED as pre-registered.** `exp = 1.0`
is **not** an identity: the registered form is
`mult(t) = lo + (pk − lo) · t^exp`, so `exp = 1.0` is a **straight linear ramp
across n slices**, and it is `n ≤ 0` — not `exp = 1` — that recovers the flat
two-block econ curve (`scenarios.py` field comment; `fleet/assembly.py`
`_econ_curve_steps`). The pre-registered falsifier fires exactly as written:
the row stays genuinely live, and caiso-236's class (c) was right for it. Every
gas plant's econ ramp is rendered as **6** sub-tranches on this keeper.

**Q3/Q4 — F3 at this grain, with an F2 route named.** No published object
measures a within-class econ-ramp smoother. The one real route is a
**shape-only, level-cancelling own-curve derive** — the construction MISO
already built (`miso_offer_surface_measured`: a within-unit own-curve price
*rise*, `Δ = price_j − price_1`, which cancels level exactly) — applied to
CAISO's own DAM bid curves. Rule 25 forbids transferring MISO's verdict; CAISO
would have to derive its own. **The blocker is the corpus:**
`data/raw/caiso-public-bids/` is one of the BLOAT-S2 conversions and holds
**only a README at tip** — the payload is untracked and **recovery is re-fetch
only** (no pin). So the honest class is F3 *now*, with a named F2 path that
begins with a re-fetch.

**Taxonomy seam, disclosed rather than force-fitted** (the caiso-236 (a′)
precedent): objects 3 and 4 both need a corpus that is *public and previously
held* rather than never-intaken, and object 3 additionally needs a new frozen
derive rather than a schema. The §1 taxonomy's F2 covers "must be intaken"; a
**re-fetch + derive** is a strictly larger ask than an intake and should be
costed as such if either is ever funded.

**No ask.**

---

## §5 — OBJECT 4: `battery_dispatch_adder` = 5.0 $/MWh — **THE F2**

**Q1/Q2.** Live and rising fast. The adder prices the **li-ion leg only**
(pumped storage takes `pumped_storage_dispatch_adder`, `null` here):

| year | li-ion discharge | share of total generation | all storage |
|---|---|---|---|
| 2023 | 3.903 TWh | **1.87 %** | 2.96 % |
| 2024 | 7.427 TWh | **3.43 %** | 4.46 % |
| 2025 | 11.128 TWh | **5.29 %** | 6.38 % |

**2.8× growth across the training window** — the only residual in the ledger
whose materiality is compounding, and the reason it outranks everything else
here on forward risk.

**Q3/Q4 — F2, exactly as pre-registered, and it is the one row whose ledger
entry already writes its own ask.** The `root_cause` field says it in the
repo's own words: *"reduced-form stand-in for cycling degradation + AS
opportunity cost; forward-valid replacement is the measured AS power
reservation (`storage_as_commitment`) + an ATB-derived degradation cost — open
item to re-derive from those."* Both halves are admissible by inspection: a
measured AS power reservation is the rule-13 class CLAUDE.md names explicitly
as legitimate ("a measured ancillary-service power reservation"), and an ATB
degradation cost is a published forward-native cost curve, not a fit.

**The instrument is NOT in hand, on both halves:**

* `storage_as_commitment = false` and `caiso_storage_as_reservation = false` on
  the keeper — the consuming mechanism is unarmed.
* `data/raw/storage-as-awards/CAISO/` holds **README.md + SHA256SUMS.txt only**
  — the `*.xlsx` payload is a BLOAT-S2 (a)-only conversion, **re-fetch is the
  sole recovery route, and there is no pin**.

**Q5 — cost.** A **data-intake session** under the caiso-218 §F.2/§F.3 fences:
re-fetch the CAISO storage-AS awards, land them through the data contract
(schema-first, `write_clean`, per-ISO registry, tmp-`CLEAN_DIR` tests — the
`gas-ofo-events` shape caiso-226 already proved out), then a separate derive +
solve round. **DOF: −1 fitted scalar, +0** if the replacement is the measured
reservation plus a published ATB cost. **Direction: unknown and not
estimated** — the adder sets storage's round-trip hurdle, so it moves both the
charging trough and the discharge peak, and no first-order bound is available
without the measurement. Nothing is claimed about C3a either way.

**This is the strongest of the four asks on forward risk**, and it is the one I
pre-registered as such.

---

## §6 — PREDICTIONS SCORED: two hits, one miss, one partial, and a ranking miss

| # | predicted | actual | verdict |
|---|---|---|---|
| 1 | F4 on a reduced live surface; falsifier = a fitted non-`committed` band on a ≥1 % class | **F4** — and the falsifier surfaced only **geometry**, which then proved dead/inert | **HIT**, with the sub-claim (1a) confirmed harder than predicted (38 scalars on *seven* absent groups) |
| 2 | F4 offer-side / F2 commitment-side | **F1 — groundable now** | **MISS** |
| 3 | F3, with a real chance of the fifth outcome | **F3**; fifth outcome **refuted** by its own falsifier | **HIT** |
| 4 | F2 | **F2** | **HIT** |
| — | *exactly one* fundable ask | **two** (objects 2 and 4) | **PARTIAL MISS** |

**The miss that matters is object 2, and it is worth stating plainly.** The
prediction reasoned from the Lever-A refusal and stopped there — it treated
"the committed band is withheld" as covering every route to the committed band.
It does not. Lever A withholds the measured **bid** multiplier because
self-commitment conduct is a unit-commitment object; it says nothing about the
measured **physical** min-load burn, which Lever A itself invoked when it set
CC_REGULAR to 1.00. Conflating the two nearly buried the one genuinely
groundable row in the set — a below-cost, below-floor, merit-inverting
multiplier on the only CAISO gas class Lever A skipped.

**The §3 stop rule did not fire** (it was specified at *all four* coming back
fundable; two did). But the ranking miss is recorded as what it is: the charter
found more than it predicted, which is the direction that warrants suspicion,
and both asks are therefore stated with their **adverse or unknown** C3a
directions attached.

---

## §7 — THE (b)-CLASS ROLL-UP (status only — no new measurement, no re-adjudication)

* **caiso-131 A3, the SoCalGas OFO arm.** Source archaeology **final** and the
  availability answer **final** (caiso-225 §5/§9.2). The datatype
  `gas-ofo-events` **already landed** at caiso-226 (2,590 rows, rule-13 verdict
  ADMISSIBLE-as-input) and the arm's design is **fully pre-registered and
  unexecuted** in `PRECOMMIT-caiso227-ofo-arm-2026-08-31.md` (trigger fixed ex
  ante on tariff grounds, gates D0–D4 / G1–G6, four acceptable outcomes
  including two kills). **C3c-side, orthogonal to C3a. Unfunded — an owner
  call.** The remaining work is the solve round, not the data.
* **`IMPORT_TRANCHES[CAISO]`, the caiso-232 defect-2 December LEVEL object.**
  Unfunded. Note for the owner: this row's *depth* estimator lane is **closed**
  — caiso-233/234/235 refused three pre-registered estimators and declared
  `spot_capacity` **NOT IDENTIFIABLE** on a regime break — so any funded work
  here must be the **level** object caiso-232 named, and must not re-enter the
  depth lane (DO-NOT-REDO).

---

## §8 — DO-NOT-REDO ADDS

1. **Do not re-census `offer_curve_by_group`.** The 112-scalar split by
   provenance, the 38 absent-group scalars and the seven absent groups are in
   `_caiso238_grounding_charter.json`. The ledger's `n_scalars = 112` is
   independently reproduced; `build_dof_ledger._count_scalars` needs no audit.
2. **Do not propose CAISO `pct_peaking` as a grounding object, in any group.**
   Dead for CC_REGULAR/CC_CHP (100 % of capacity superseded per-plant) and a
   self-restatement for CT_PEAKER/ST_GAS (one distinct CSV value each, source
   `class_default`).
3. **Do not read `band_windows_geometry.econ_low_share` as a measurement** —
   the derive copies the armed value through and says so (line 187). Likewise
   `band_windows_geometry.*.pct_peaking` for CT_PEAKER is the class default
   read back out of the fleet CSV, not an independent measurement.
4. **Do not re-test whether `offer_curve_smoothing_exp = 1.0` is an identity.**
   It is not; `n ≤ 0` is the identity. Settled from the registered form.
5. **Do not re-propose the measured *bid* `committed` multipliers** (CC 1.030 /
   CT 1.166) for any CAISO gas class — the Lever-A refusal stands, uniformly,
   and caiso-231 already applied it. Object 2's ask is the **physical** basis
   and is a different object; do not merge the two.
6. **Never propose object 2 or object 4 as a C3a instrument.** Object 2's
   direction is adverse and declared; object 4's is unknown and unestimated.
