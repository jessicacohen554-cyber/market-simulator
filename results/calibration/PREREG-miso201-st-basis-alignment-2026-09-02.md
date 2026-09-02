# PREREG miso-201 — the ST-SIDE CAPACITY BASIS ALIGNMENT

**Written and committed BEFORE the mechanism exists and before either leg is solved.**
Every threshold below is frozen here. A threshold is never re-chosen after its number is
read (the miso-172 discipline; the miso-200 precedent where a frozen kill fired and was
reported as fired rather than renegotiated).

**Session:** miso-201 (2026-09-02).
**Keeper at open:** `2026-09-02-miso-200-unitroute`, bundle
`results/calibration/miso200_unitroute_B`. Determination NOT-YET on
`{C3a-2025 −12.2745}` alone; C3c the single ledgered caveat; C6 attested.
**Charter:** FINDING-miso200 §8 item 1 — the ST_GAS/ST_CHP analogue of
`unit_outage_lp_capacity_basis`, which is CC-only
(`outages._CC_NAMEPLATE_BASIS_GROUPS == ("CC_REGULAR", "CC_CHP")`) and can never reach a
steam bin.

---

## 1. What phase 0 established, before any gate was chosen

Recorded in `_miso201_st_basis_phase0.json` and committed at `d331c1cb`, ahead of this
document.

**N-1 reproduction PASS on 988 bins.** The pre-clip removed share is reconstructed from
the production code path and every bin asserted to reproduce `clip(1 − v, 0, 1)` exactly,
for BOTH overlays that reach steam bins — the ≥5-day std extract and the maxgen
declared-event extract, which does **not** share the std accumulator and therefore gets
its own faithful reconstruction rather than being run through the wrong one.

**The charter's caution is confirmed, and then superseded by the same measurement.** At
Ninemile Point 1403 and Moselle 2070 the pre-clip *overflow* is indeed inert: the units
carrying the windows are exactly the units in the bin, so a concurrent full stop means the
bin genuinely is 100 % out and availability 0.0000 is correct. **But the overflow was
never the object.** The basis gap over-removes in **every hour a steam unit is out**, and
the clip hides only the extreme. At 1403 itself, unit 5 alone out removes
`895.1 / 1465.4 = 0.611` of the bin against a correct `742.6 / 1465.4 = 0.507` — real
over-removal, in exactly the hours that do NOT overflow. **The lever is live at the very
facility the charter named as inert**, and the charter's instruction to find where the
overflow is "not already landing on the correct answer" is what surfaced it.

**Root cause, pinned at primary source (EIA-860 operable generator sheet).** The numerator
is a per-unit **nameplate** (`capacity_source == eia_exact`) or a CEMS **observed peak**;
the denominator is the fleet bin's **net summer** capacity. Ninemile Point 1403 generator
`5`: nameplate 895.1 MW, net summer 742.6 MW.

**Two families that are NOT this object**, separated rather than absorbed: the
`eia923_netzero` whole-plant lay-up rows (one synthetic `NET0-923` row carrying the
plant's total nameplate against a single group's bin; 58 of 61 rows are full-year 2025),
and an extract/fleet **unit-set mismatch** (bins where the extract carries units the fleet
does not model, boiler-vs-generator grain, naming conventions). Both are reported in the
phase-0 artifact; neither is repaired by this arm.

---

## 2. The mechanism, declared before it is written

`ScenarioConfig.unit_outage_st_capacity_basis` — **GATED, default off, byte-inert off.**

For steam bins (`ST_GAS`, `ST_CHP`) only, each ≥5-day std-extract full-stop row's removed
MW is put on **the LP's own basis**: the fleet unit's `pmax_mw`, which is precisely the
capacity the availability multiplier is applied to. Numerator and denominator then sit on
one basis by construction, so a bin all of whose units are out lands on **exactly 1.0** —
never 1.13, never 0.94.

**Applied ALL-OR-NOTHING per bin.** A bin is aligned only when every extract unit that
ever appears in it resolves 1-1 onto a distinct fleet unit of that bin, by three
zero-DOF routes in order: (1) exact normalised-generator-id hit; (2) an unambiguous
trailing-digit hit (a single fleet unit in the bin carries those digits — the deriver's
own rule); (3) a unique 1-1 **residual** pairing, where exactly one extract unit and
exactly one fleet unit are left over so the pairing is *forced, not chosen* (this is what
resolves 1403, whose CAMPD unit `4` cannot match EIA generator `6(4)` on digits). A bin
with any unresolved unit is left **entirely untouched**: a half-aligned bin — some units
on the LP basis, some on nameplate — is less coherent than either basis alone, so partial
application is refused rather than counted.

**Coverage, measured in phase 0:** 32 of 55 steam bins eligible, 8,553 of 12,291 MW
(69.6 %). Eligibility is computed over the whole extract, so it is a **static property of
the bin** and does not shift with the years solved (verified: the 2023–25 window and the
whole extract give the identical eligible set).

**Zero free parameters** (rule 21 `[R-DOF]`): every capacity is the fleet's own, no scalar
is chosen, no threshold is fitted. **Rule 13 `[R-MEASURED]` forward-regenerable**: both the
fleet's `pmax_mw` and the extract's unit ids exist for a forecast year, and the alignment
responds to changed conditions because the fleet does.

**Scope, stated as a measurement and not an assumption.** The short-window overlay is
COAL-only by construction and carries no steam rows. The partial overlay is off at the
keeper. **The maxgen overlay is deliberately OUT of scope and this is not a rule-19
`[R-ONE-MECH]` violation**: its rows carry a measured `derate_mw` — a partial MW reduction
revealed by CEMS, *not* a unit capacity — so substituting a fleet `pmax_mw` for it would
be substituting a capacity for a derate and would be simply wrong. The routing repair
(miso-200) had to move both layers together because a unit routed to *different bins* in
the two layers is incoherent; a numerator basis is per-layer and carries no such coupling.
The maxgen numerator's own basis question (CEMS gross against net summer) is **named as
open, not silently inherited**.

---

## 3. The A/B, and the one delta

* **CONTROL leg A** — the keeper recipe replayed unchanged
  (`--replay-bundle results/calibration/miso200_unitroute_B`), 2023 + 2024 + 2025 in one
  invocation, years sequential (rule 12 `[R-PARALLEL]`, rule 16 `[R-ALLYEARS]`).
* **ARM leg B** — the identical replay with per-arm override
  `unit_outage_st_capacity_basis=True`, and **nothing else**.

Both legs solve from the same committed keeper recipe and the same code state. Drift
between the legs is **measured, never assumed** (the charter's instruction; main moves at
5+ merges per solve).

---

## 4. THE GATES — frozen here, before the mechanism and before the solve

### Soundness lines (checked at build time, before any solve is spent)

* **L-3a — SOUNDNESS. A violation KILLS the arm.** On the eligible steam bins, the
  **aligned** pre-clip share must not exceed 1.0 in any bin-hour, **except** where that
  hour's excess is attributable to two or more rows of the SAME `unit_id` overlapping —
  the adjacent-window boundary-day double-count already on the record as an independent,
  unrepaired defect (FINDING-miso200 §8 item 2). Any *other* aligned overflow means the
  alignment is not doing what it claims and kills the arm.
* **L-3b — IDENTITY.** The arm must differ from the control in exactly one
  `ScenarioConfig` field, and the resulting availability arrays must differ **only** on
  eligible steam bins. Any out-of-scope array change voids the A/B — it did not measure
  the lever.

### Result kills (checked after the solve)

* **K-1 — C1 BAND. No class-year may EXIT the ±8.00 TWh volume band**
  (`FUELMIX_VOL_CAP_TWH = 8.0`). The arithmetic is frozen from the keeper's own committed
  verdict, **before the arm exists**:

  | class-year | keeper face (TWh) | headroom to the edge | expected direction | reading |
  |---|---:|---:|---|---|
  | **ST_GAS-2024** | **−7.854** | **0.146** to −8.00 | **UP** | favorable, and the tightest cell on the board |
  | **CC_REGULAR-2024** | **+7.075** | **0.925** to +8.00 | **DOWN** | favorable |
  | ST_GAS-2025 | −6.862 | 1.138 to −8.00 | UP | favorable |
  | ST_GAS-2023 | −3.834 | 4.166 to −8.00 | UP | favorable |
  | **CC_REGULAR-2023** | **−3.319** | **4.681** to −8.00 | **DOWN** | **THE NAMED RISK** — already negative, and displacement pushes it further |
  | **COAL_PRB-2025** | **−4.865** | **3.135** to −8.00 | **DOWN** | **THE NAMED RISK** — second-tightest adverse cell |
  | CC_REGULAR-2025 | −2.086 | 5.914 to −8.00 | DOWN | adverse, wide |

  **The capability bound (a rigorous UPPER bound on what the arm can add to steam energy,
  not a prediction):** +1.576 / +1.968 / +1.403 TWh for 2023 / 2024 / 2025. Every adverse
  headroom above exceeds the bound for its year, so K-1 is expected to hold — **stated as
  an expectation that can be wrong, never as a reason to skip the gate.**
* **K-2 — C3b (`price_shape`): no PASS → FAIL.**
* **K-3 — D-4 conduct: zero NEW off-window binding.** Scored on real
  `legitimacy_diagnostics.json` rows for BOTH legs (see K-6).
* **K-4 — D-1 shape: no PASS → FAIL.**
* **K-5 — zero PASS → non-PASS on any criterion.**
* **K-6 — THE miso-200 VACUOUS-PASS TRAP, closed in advance.** A `--replay-bundle` solve
  writes **no** `legitimacy_diagnostics.json` and **no** `calibration_attestation.json`, so
  K-3/K-4 compared empty against empty on miso-200's first scoring run and passed
  **vacuously**. Here the diagnostics **and** the attestation are generated for **BOTH**
  legs *before* the pair is scored, by the `gen_miso186/187/188/198/200` pattern
  (`build_dof_ledger.py` is never run on a promoted bundle). **A gate that cannot be
  scored is reported UNSCORED and disclosed as such — never counted as a PASS.**

### Never a gate

**C3a (`price_mean`) is reported at full magnitude and is NEVER a gate** (rule 1
`[R-STRUCT]`: the backcast fit is not the objective, and the keeper's sole failing
criterion is not this arm's target). No branch of the scorer reads it. The same holds for
C3c, which is the ISO's single ledgered caveat.

---

## 5. Disposition, declared before the result

* Every kill silent **and** L-3a/L-3b clean → the arm is a **candidate**, judged on the
  structural case (a measured input put on the basis the LP actually applies it to,
  rule 14 `[R-ACCURATE]`) rather than on any residual movement.
* A kill fired → reported **as fired, at full magnitude**, and the arm is not promoted on
  the scorer's own authority. The miso-200 owner re-scoping (*"if structural integrity
  improves but gates regress that may still be a keeper"*) is recorded as **standing
  context, not as a licence this session grants itself**: a fired kill is escalated with
  the structural case and the regression side by side, never silently absorbed and never
  reclassified as a pass.
* **The arm not moving the residual is not a reason to reject it** (rule 1). The arm being
  *inert* — no measurable value movement at all — is a reason to report it inert and land
  the mechanism default-off.

---

## 6. Registration

Whatever the outcome, both legs are registered on the backcast dashboard in this session
(rule 15 `[R-DASHBOARD]`), all three years in one bundle each (rule 16
`[R-ALLYEARS]`), the tested cell is stamped in MISO's mechanism-matrix shard alone
(rule 28(b), rule 25 `[R-ISO-SCOPE]`), and the new `ScenarioConfig` field carries its base
matrix row plus a cell in all six shards in the same PR (rule 28(c)).

MISO holds **no** `complete`/`final` marker: 2023–2025 only, holdout freeze ACTIVE
(rule 22 `[R-HOLDOUT]`).
