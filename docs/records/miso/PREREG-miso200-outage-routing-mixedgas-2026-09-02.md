# PREREG miso-200 — the CHARTER FORK is taken toward the AVAILABILITY object: the CAMPD unit-outage extract MIS-ROUTES a mixed CC+ST facility's steam units onto its CC bin (2026-09-02)

**Session:** miso-200 (2026-09-02). **Keeper at open: `2026-09-01-miso-198-oomlevel`**
(bundle `results/calibration/miso198_oom_B`), NOT-YET on exactly {C3a-2025 −12.2745 %},
C3c the single ledgered caveat, C6 attested (38/2), C8 PASS with ST_GAS forced share
0.2001 / 0.2100 / 0.3186, `audit_keepers --iso MISO` PASS 0/0.

**This document is committed and pushed BEFORE any adjudicating quantity is computed**
(the standing miso-196/197/198/199 pattern). Every threshold below is stated here, in
advance, and is not revisited.

---

## 1. THE CHARTER FORK — the availability object is taken, the bid-side lever is NOT

The charter offered two objects and required exactly one. **This session takes the
AVAILABILITY / outage-extract object (FINDING-miso199 §7a, plant 1403 Feb-2024) and
does NOT build the bid-side self-schedule form.** Five reasons, all stated before any
measurement:

1. **It is an input-ACCURACY defect with a root cause in code, not a new mechanism.**
   Rule 14 `[R-ACCURATE]` governs it directly. The bid-side form is a new mechanism and
   would need a new `ScenarioConfig` field, a new deriver, a rule 28(c) six-shard matrix
   edit, and a contested rule-28(a) DO-NOT-REDO argument.
2. **The repair channel already exists and was built for this exact phenomenon.**
   `data/outages.py::_FLEET_GROUP_OVERRIDE` carries NYISO Ravenswood (2500) with a
   docstring that describes the identical symptom verbatim: *"its outage rows route to a
   (2500, CC_REGULAR) bin that does not exist, so the ST_GAS bin reads near-fully-available
   and over-runs (and the steam reliability floor, frac × pmax × availability,
   over-forces it)."* That is miso-199 §7a's cell, at a different ISO, already named.
3. **It is the largest single defect on the record** — 320.5 GWh in one (plant, month)
   cell, **0.5438 of the entire three-year misplacement** (miso-199 L-X1a).
4. **Rule 19 `[R-ONE-MECH]` is clean.** Availability is not a floor. There is no
   stack-or-replace question to adjudicate, and no keeper mechanism is disarmed.
5. **The bid-side form's only clear gain is C8 headroom on a criterion that already
   PASSES**, while its own declared C3a face (miso-198 M-4 form (c),
   `_miso198_stgas_oom_conduct_phase0.json`) is **DOWN in the body** — against the
   keeper's sole failing criterion. Its M-4 record also carries
   `L4a_shape_faithful=false` with `profile_r_vs_measured_oom = NaN`, i.e. its
   shape leg is UNDEFINED for a zero-forcing form and was never actually tested.

**No claim is made here that the bid-side form is refuted.** It is NOT tested, NOT
adjudicated, and its cell is NOT minted. It stays open for a successor, and the
rule-28(a) argument it needs stays unwritten rather than stretched — which is the
charter's own stand-down instruction, exercised.

## 2. THE OBJECT — a class-attribution defect in `_resolve_unit_group`, stated as a mechanism

`scripts/data/derive_campd_unit_outages.py::_resolve_unit_group` routes each CAMPD unit's
outage window to a model `(plant_code, plant_group)` bin. Its third branch is a
short-circuit:

```
if fac_group in QUALIFYING_PLANT_GROUPS and fac_group != "COAL":
    return str(fac_group)
```

`fac_group` comes from `group_by_code`, built as
`group_by_code[int(g.plant_code)] = g.plant_group` over the model fleet — **last writer
wins**, so at a facility carrying more than one gas bin the group is whichever fleet row
happened to come last. The short-circuit then hands **every** unit at that facility to
that one bin and the per-unit `unitType` resolution below it is never reached.

The function's own docstring already flags this branch as a known conservatism rather
than a physical claim — *"that short-circuit was a deliberate pjm-75 conservatism
('single-group gas facilities are byte-identical') rather than a physical claim"* — and
neiso-99 already carved one exception out of it (the liquid-only combustion-turbine
guard, placed BEFORE it, under rule 14). **The premise names its own scope: the branch is
sound only where the facility carries ONE gas group.** This session tests the case it does
not cover.

**THE REPAIR (declared in full, ex ante).** Gate the short-circuit on the facility
carrying exactly one qualifying non-COAL group. At a facility carrying two or more, fall
through to the resolver's EXISTING per-unit `unitType` routing — no new logic, no new
data source, no new threshold. Zero free parameters (rule 21 `[R-DOF]`); the
discriminator is CAMPD's own `unitType`, a static unit attribute that regenerates for any
forward year (rule 13 `[R-MEASURED]`); it is a general rule, not a per-plant enumeration
(rule 24 `[R-REGISTRY]`).

**PRE-FREEZE SATISFIABILITY, disclosed rather than absorbed** (the miso-196 pattern —
a structural feasibility fact about the repair path, computed before this document was
frozen and carrying no adjudicating quantity): MISO plant 1403 Ninemile Point files four
CAMPD units, and `unitType` separates them cleanly — **4 and 5 "Tangentially-fired"
(boilers), 6A and 6B "Combined cycle"** — against a model fleet carrying
`(1403, ST_GAS) = 1,465.4 MW` and `(1403, CC_REGULAR) = 649.5 MW`
(`bin_assignments_MISO.csv`, `Mixed_Facility = CC+ST`). The repair therefore has a live
path at the cell under test. **This is satisfiability, not evidence**: it establishes only
that the resolver CAN route these units, never that it currently mis-routes them, how much
that is worth, or what it does to the model. Those are N-1/N-2/N-4 below.

## 3. GOVERNANCE — which cell is entered, and why no verdict binds it

**The bid-side cell is NOT entered** (§1), so the charter's rule-28(a) DO-NOT-REDO problem
does not arise in this session and its `R`/`I` verdicts (miso-179, miso-180, miso-178
lever 1) are neither re-opened nor cited as licensed.

The cell entered is the **outage-extract PROVENANCE / routing** cell, and its MISO
verdicts do not bar it:

| MISO cell | verdict | does it bind? |
|---|---|---|
| `outage_artifact_provenance` | **`O` (open)** | No — open is the invitation. |
| `unit_outage_lp_capacity_basis` | `U` | No — untested. |
| `historic_outage_overlay` | `U` | No — untested. |
| `campd_outage_windows` | `K` (armed on the keeper) | No — this session does not re-test the mechanism, it repairs the POPULATION the mechanism reads. miso-195 refuted a *fleet-grain remove-only cap* fed by a different source; nothing there speaks to unit→bin routing. |
| `dam_availability_rebasis` | `R` (miso-85/86) | No — a different SOURCE (DAM re-basis), not the CAMPD extract's routing. |
| `mustrun_online_frac_per_year` | `R` (miso-172) | No — not touched; this is not a window-size lever. |

**WHAT WOULD MAKE THIS SESSION STAND DOWN.** If N-1 finds no MISO facility clearing L-1a,
or if L-1b shows the 1403 cell is not this family, the object is immaterial or
mis-identified at MISO and the session **escalates WITHOUT SOLVING** and mints no verdict.

## 4. PHASE 0 — the census, zero solve. Record `_miso200_outage_routing_phase0.json`

Probe `scripts/probes/_miso200_outage_routing_phase0.py`, rule frozen in its own
docstring, pushed and blob-verified before any adjudicating quantity.

**Bases.** The model fleet is `run_year`'s own chain
(`fleet_to_bins(load_fleet_from_csv) → build_base_fleet → build_dispatch_fleet`), never
`assembly.load_or_synthesize_bins` (miso-197 §6, Cottonwood 55358). Availability arrays
come from `outages.unit_outage_derate_factors` with the KEEPER's own flags. Class energy
and the load shape come from the keeper's committed `hourly/` sidecars, never a replay.
`generators_to_fleet_arrays` is always given `load_shape` read from the keeper's own
`hourly/system_<year>` `demand.sum(axis=0)` (arrays.py:2861), and the rebuilt 2023 ST_GAS
floor is **asserted equal to the keeper's logged 9.9319 TWh** as a regression test
(inherited from miso-199, kept verbatim).

**LEVEL-SLOT PRECEDENCE.** This keeper arms `st_gas_mustrun_oom_level`, and arrays.py:2512
merges the oom map OVER `thermal_tranche_p25_measured_level`; any level patch goes to
`thermal_tranche_oom_level` and the probe ABORTS if a patch fails to move the assertion
(miso-199 X-2's disclosed defect, inherited as a guard).

### N-1 — the mis-routing population
For every MISO facility with a window in `campd-unit-outages-MISO.csv` touching 2023–2025:
classify `single_gas` (exactly one qualifying non-COAL model group) or `multi_gas` (≥2),
and count units whose `unitType`-implied group differs from the facility group.

* **L-1a THE DEFECT IS REAL AND MATERIAL** iff ≥1 MISO facility is `multi_gas` AND its
  mis-routed units carry **≥ 500 MW** of `unit_capacity_mw` in **≥ 2 of 3** years. The
  threshold states what "a bin large enough to matter to a class band" means physically —
  it is ~6 % of the ST_GAS class nameplate and is not tuned to anything. **If no facility
  clears, the session escalates WITHOUT SOLVING.**

### N-2 — the two-sided signature, on the INCUMBENT extract
Per affected bin-year: the pre-clip removed share `v_t` (the accumulator's own
`removed_frac × ucap / cap[tgt]` sum), and per-bin row coverage.

* **over-removal** = `max_t v_t`; `> 1.0` proves the receiving bin is removed beyond its
  own capacity (the Stony Brook / Cottonwood signature, miso-186).
* **zero-coverage** = a model bin with `cap ≥ 100 MW` at a `multi_gas` facility receiving
  ZERO rows, i.e. availability ≡ 1.0 all year.
* **L-1b THE 1403 CELL IS THE MIS-ROUTING FAMILY — re-derived on THIS session's line.**
  The charter's CAUTION is honoured: miso-199's frozen L-X1b did NOT classify this cell
  (it missed its online-share leg by 5.7 pp) and is NOT cited as a passed test. The
  classification here is structural, not a threshold on a residual, and is declared TRUE
  iff **all three** hold: (i) `(1403, ST_GAS)` is zero-coverage in 2024; (ii) ≥1 unit at
  facility 1403 carries a February-2024 window in the incumbent extract; (iii) that unit's
  `unitType`-implied group is `ST_GAS`. If any leg fails, **the 1403 cell is NOT this
  family** and the session reports that against its own interest.

### N-3 — the repair's own soundness, on the REGENERATED extract
* **L-3a NO NEW OVER-REMOVAL**: no MISO bin-hour in 2023–2025 whose pre-clip removed share
  exceeds 1.0 after the repair but did not before. The repair must REMOVE overflow, never
  add it. A violation KILLS the arm.
* **L-3b SINGLE-OBJECT DELTA**: every row differing between the incumbent and repaired
  extracts differs only in `plant_group` (and the columns that are functions of it), and
  every changed row sits at a `multi_gas` facility. A changed row at a `single_gas`
  facility is a scope violation and KILLS the arm.

### N-4 — the C1 exposure, projected arithmetically (a bound, never an LP result)
Per class-year, from the incumbent and repaired availability arrays against the keeper's
own committed hourly class dispatch:
* **capability bound** = `Σ_t |Δavail_t| × pmax` over the affected bins — a rigorous
  UPPER bound on the class energy movement, since the LP can never move more than the
  capability that changed.
* **class headroom** = `Σ_t (class pmax×avail − class dispatch)` in the affected hours,
  reported so the substitution channel is visible rather than assumed away.

* **L-4 CLEAR-TO-SOLVE.** The A/B is spent **unless** N-1/L-1a or N-2/L-1b has already
  stood the session down. **There is deliberately NO refuse-without-solving branch on
  N-4.** A rigorous LOWER bound on a CLASS decrement does not exist here — other ST_GAS
  plants can substitute — so refusing on the projection would mean refusing on a bound
  this session cannot make rigorous. N-4 is **reported, and informs nothing that is
  gated.** If the pessimistic corner of the capability bound leaves both named 2024 bands
  intact, that is recorded as a prediction of silence; it is not a gate either way.

## 5. PHASE 1 — the A/B, and the gates. Scorer committed BLIND

Control `2026-09-02-miso-200-control`, arm `2026-09-02-miso-200-unitroute`, both
`--year 2023 2024 2025` in ONE invocation at one HEAD, **legs SEQUENTIAL** (rule 12; the
MISO per-plant LP peaks ~13.95 GB and forbids the two-concurrent pattern). Scorer
`scripts/probes/_miso200_ab_gates.py`, **written and committed before either leg's numbers
are read**, and — the miso-198 scorer defect, NOT inherited — it orders the **kills-silent**
branch BEFORE record-identity and tests **VALUE MOVEMENT, not status identity**, so an arm
that moves every value without flipping a status can never be reported as `INERT`.
`_miso198_ab_gates.py` is left unrepaired on purpose and is not imported.

| gate | line |
|---|---|
| **S-0** control integrity | control BIT-IDENTICAL to the keeper's 12 committed sidecars, `max_abs_diff` 0.0 |
| **S-1** single delta | exactly one `ScenarioConfig` field differs between the legs |
| **S-2** liveness | arm `(1403, ST_GAS)` 2024 mean availability **< 1.0** AND arm ST_GAS forced energy **< control's**. Liveness only — never a target |
| **K-1** C1 band | **THE NAMED RISK, with its arithmetic stated here.** `CC_REGULAR-2024` sits at **+6.748** against a ±8.00 band = **1.252 TWh** headroom, and the repair frees spuriously-removed CC capability at 1403, so it moves **UP**. `ST_GAS-2024` sits at **−7.553** = **0.447 TWh** headroom, and the repair removes ST_GAS capability, so it moves **DOWN**. **A band exit on either is a KILL and the arm is NOT promoted** (the miso-196 precedent, same class pair). Both class-years are named EX ANTE, here, before the solve |
| **K-2** C3b | no PASS→FAIL |
| **K-3** D-4 conduct | zero NEW off-window binding, any year. The 1403 rows are EXPECTED to improve; an improvement is reported, never counted as clearing another gate |
| **K-4** D-1 shape | `profile_r` / `cv_ratio` no PASS→FAIL |
| **K-5** record flips | zero PASS→non-PASS anywhere |
| **K-6** DOF | replay bundles carry no attestation ⇒ scored **UNSCORED** and disclosed as such, never counted as a PASS (miso-196's disclosure discipline). Analytically the lever adds ZERO free parameters |

**PROMOTION RULE.** Promote **iff every kill (K-1…K-5) is silent** and S-0/S-1/S-2 pass.
If **K-1 fires**, the arm is **NOT promoted**, the keeper is unchanged, and the session
reports the repair as a *measured, structurally correct, band-blocked input fix* under
rule 14 `[R-ACCURATE]`'s own compensating-error reading — the estimate was silently
carrying an error elsewhere — and hands the root cause on. **Under no circumstance is the
repair narrowed, scoped, or weakened to protect a band**: scoping an accurate input to the
residual is rule 1 `[R-STRUCT]`'s forbidden path.

## 6. THE C3a FACE — pre-registered, reported, NEVER the criterion (rule 1)

C3a is **not** a gate in this session and appears in no promotion condition.

**Declared direction: UP, confidence 0.55 — deliberately low, and the competing channel is
named.** Two opposing limbs: removing a 688 MW price-TAKING floor in hours the plant is
out raises the clearing price (**UP**); freeing 649.5 MW of cheap CC capability at the
same plant lowers it (**DOWN**). The net is not predictable from the ex-ante information,
and this is said HERE rather than after the number is read. **A DOWN outcome is therefore
not a surprise and will not be re-narrated as one.**

**The honest note the charter demanded, in this session's own terms.** C3a-2025 is the
keeper's SOLE failing criterion at −12.2745 %. This session's own K-1 kill is the one that
would fire on the class movements, and it is pre-registered against BOTH classes in the
adverse direction — so a favourable C3a movement cannot be the reason anything here is
kept, because C3a movement cannot silence K-1 and no gate reads it.

## 7. Governance

Rule 22 `[R-HOLDOUT]`: 2023–2025 ONLY; MISO holds no `complete`/`final` marker; the
holdout freeze is untouched and **no marker is read or written**. Rule 12 `[R-PARALLEL]`:
solves run IN-SESSION, never CI; years sequential within the invocation; the two legs
sequential. Rule 15 `[R-DASHBOARD]`: both legs registered same-session if they run; if no
run is produced, the deliverable is the probe record + FINDING and there is nothing to
register. Rule 16 `[R-ALLYEARS]`: all three years in one bundle, never a single-year
keeper. Rule 25 `[R-ISO-SCOPE]`: **only MISO's shard/keeper/status files are edited, and
only MISO's extract is regenerated** — the resolver change is shared code, so its
cross-ISO blast radius is MEASURED and REPORTED but no other ISO's committed extract is
rewritten in this session. Rule 27 `[R-PUSH]`: every push touching a ≥300-line file is
blob-verified against a fresh fetch. Rule 28(b): the tested cell is stamped in
`docs/codebase-site/data/mechanism-matrix/MISO.js` in-session; rule 28(c): if a
`ScenarioConfig` field is added, its base row plus a cell in ALL SIX shards land in the
same PR.

**Known-failing, NOT this lane's:** 11 `tests/unit/config` cache-key pin tests fail on
clean `main` (the capx-d24 repair moved the default key `603c2498bf71d21d` →
`7a57fadff595ca83` without updating its literal pins). Verified pre-existing; untouched.
