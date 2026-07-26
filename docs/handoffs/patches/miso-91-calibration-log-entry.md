
## 2026-07-26 — miso-91: `SUMMER_WEFOR_SHARE` DOF-declared and RE-HOMED into registry coverage; the three rule violations share one root cause (wrong module), and the parameter governs six classes, not one

**Lane:** 1 of the miso-91 handoff (the governance defect miso-90 named).
**Keeper UNCHANGED — `2026-07-25-miso-88-egrid-hr`.** No solve was run; no value
changed anywhere. **Determination UNCHANGED: CALIBRATED-WITH-CAVEATS**, 3/3
ledgered caveats, keeper-auditor **PASS / 0**. Charter (written before any edit):
`docs/handoffs/miso-91-summer-wefor-dof-charter-2026-07.md`.

### The defect had one root cause, not three

`_SUMMER_WEFOR_SHARE = 0.30` was uncited (rule 5), unregistered, and undeclared
(rule 21). Those are not three oversights — they are one: the constant lived in
`data/fleet/arrays.py` as a module-private literal, and
`scripts/validate_parameters.py` scans only `vars(constants)` + `ScenarioConfig`
defaults, skipping anything private or non-uppercase (`:59-69`). It was invisible
to the registry **three ways over** — wrong module, leading underscore, not
uppercase. That is a **rule 20 `[R-REGISTRY]` violation by location**, and it is
what let the other two persist.

**Fixed at the root, not papered over.** `SUMMER_WEFOR_SHARE` and its sibling
`SUMMER_CLASS_DERATE` now live in `config/fuel_trajectories.py` beside the
`THERMAL_AVAILABILITY` table they modify, public and uppercase, imported into
`constants.py` so the registry covers them permanently. Private aliases remain in
`arrays.py` so the availability builder, the fleet package's re-export contract,
`results/scarcity.py` and the ERCOT derive script are untouched by the move.
**Values byte-identical**, verified: the per-class branch map is unchanged to
12 decimal places before and after.

Worth stating plainly: the WEFOR *magnitude* was always GADS-cited
("Source: NERC GADS by unit type and age"). Only its *seasonal reallocation* was
uncited.

### It governs SIX classes, not CT_PEAKER alone — a correction to miso-90

miso-90 scoped the parameter to "all 22.39 GW of MISO CT_PEAKER". Measured this
session (no LP, keeper flags from `run_config.json`: `outage_source='historic'`,
**`wefor_residual=None`**, `coal_drop_pof=True`, `cc_nameplate_summer_derate=False`),
it reaches **every non-coal thermal class**. COAL is genuinely exempt —
`coal_drop_pof=True` routes it to a branch that drops summer WEFOR outright
(measured delta 0.0000). Summer availability the 0.30 adds vs a no-reallocation
baseline:

| ST_GAS | ST_CHP | CT_PEAKER | CC_REGULAR | CT_CHP | CC_CHP | COAL |
|---|---|---|---|---|---|---|
| +14.70 pp | +5.60 | +4.29 | +3.15 | +3.06 | +2.52 | exempt |

The closed form is exact: `(1 − share) × wefor(age) × (1 − class_derate)`. Against
the committed per-class nameplates (FINDING-miso89 §5) that is **≈3.9 GW** of
MISO summer-peak capability at a uniform age of 18 y, **≈4.6 GW** at 28 y,
**≈5.8 GW** at 38 y. ST_GAS takes the largest slice because its GADS WEFOR base
(0.21) is the highest in the table.

### Declared, NOT re-tuned

Both constants are now in the keeper's DOF ledger (26 → **28** entries, 2 → **4**
residual), each with an open root cause pointing at the data ask; auditor E8
confirms no bare residual. **On the label:** neither was ever *fitted*.
`"residual"` was chosen because it is the strictest existing enforcement
category — E8 requires every residual entry to carry an open root cause — and
each entry says so in terms, so no future reader reads the label as "we tuned
this". The truthful description is *unidentified*: no sweep, derivation or
calibration lineage exists for the 0.30.

The value was deliberately left alone. Its ≈3.9–5.8 GW blast radius is the same
order as the ~10 GW summer-peak under-derate ledgered as C3b the day before, so a
hand-set value here would be an answer key for an already-ledgered miss
(rule 24). Nothing here is a load-bearing criterion miss, so **nothing was
ledgered** — the 3/3 budget is untouched.

**Physics tension, recorded in the code, the citation and the data ask.** For
*planned* outages, shifting maintenance off the peak is well-founded (and the POF
side is separately grounded by the measured `MAINTENANCE_MONTHLY_SHAPE`). For
*forced* outages the reallocation runs **opposite** to the physics — forced
outages correlate *positively* with heat and load. So the open question is
whether the mechanism has the **right sign at all**, not merely the right
magnitude. Recorded as an unverified directional argument, not a citation.

Data ask updated with a new §2a: `SUMMER_WEFOR_SHARE` is now the ask's named
replacement target, with two added acceptance criteria — **E** forced/planned
must be separated (the parameter reallocates WEFOR only), **F** class coverage
must be stated and never silently generalised (per-class deltas differ ~6×).

### Two governance findings, neither repaired here

1. **The parameter registry check is documented as a CI gate and is not one.**
   `docs/parameter-citations.md`'s header states it "fails CI"; `grep -rn
   validate_parameters .github/workflows/` returns **nothing**. It also **already
   fails on `main`** with **48** missing citations. So even a correctly-homed
   constant would have landed in a pre-existing red backlog. Not wired here
   (wiring an already-red check just breaks CI) and the 48 were **not** mass-
   registered, though `generate_parameter_registry.py` will do it in one run —
   that would mark 48 other lanes' gaps "documented" without anyone sourcing
   them. After registering only this session's constants the count returns to
   exactly **48**: the backlog is not added to. **Owner call.**
2. **`wefor_residual = None` in the MISO keeper**, so the cap at `arrays.py:532`
   never fires. That cap exists specifically to stop the statistical WEFOR
   double-counting the CAMPD overlay for covered classes (coal +
   `_POF_DROP_GROUPS`). With it off, MISO's CC and ST classes carry full
   statistical WEFOR *and* the historic overlay. Whether that is deliberate or a
   latent double-count needs a solve to settle and was outside this charter.
   **Flagged, not diagnosed.**

### Verification

* Determination **CALIBRATED-WITH-CAVEATS**, 3 ledgered caveats — unchanged;
  `status/MISO.js` diff is the timestamp only, every criterion byte-identical.
* `audit_keepers.py --iso MISO` → **PASS / 0 failures**.
* `validate_parameters.py` → **48**, its exact pre-existing count (was 53 after
  the move, before the 5 registry entries were added).
* New `tests/test_summer_availability_constants.py` — 12 tests, all pass: pins
  both values, the registry-visible home, that the `data.fleet` aliases resolve
  to the canonical objects (never a second literal that could drift), the
  six-governed/COAL-exempt branch map, the closed-form delta, and that the
  reallocation conserves annual outage energy.
* `tests/test_fleet.py` + `test_fleet_facade.py` + the new module: **136 passed**.
* `run_calibration_full` importer modules: **8 failed / 186 passed** — exactly the
  inherited baseline; all 8 are pre-existing `test_pipeline_facade_shims`
  failures, untouched by this session.
* Full suite (`-p no:randomly`, the two usual collection-error modules ignored):
  **93 failed / 5020 passed**. Recorded because the inherited number is disputed
  — the handoff says 108, miso-90 measured 90. No failure is in a file this
  session touched.
* Also **appended a dated addendum** to the keeper attestation's
  `governance.note`, whose opening "DETERMINATION NOT-YET" was overtaken by
  miso-90's re-gate. miso-88's prose is left exactly as written and no assertion
  is modified — the addendum only corrects the stale statement of fact.

### Notes for the next session

* **`git push` DOES NOT WORK from this container**, contrary to the miso-91
  handoff. The git proxy rejects `git-receive-pack` by policy — 403 on an empty
  POST, 413 with a body — including for a **zero-object** push, so it is not a
  size problem. CLAUDE.md's API-only guidance is correct. This entry and the
  code change were delivered as `docs/handoffs/patches/README-miso-91-apply.md`.
* **The 3/3 budget still binds.** Nothing here consumed or freed a caveat slot.
* **Lane 2 (memory telemetry) is still unread** — it needs one solve-year to say
  whether the ~1.35 GB unattributed floor is live Python payload or
  allocator/HiGHS-side. Untouched by this session.
* Next number: **miso-92**.
