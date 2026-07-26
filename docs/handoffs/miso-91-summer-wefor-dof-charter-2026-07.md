# miso-91 charter — DOF-declare and re-home `_SUMMER_WEFOR_SHARE`

**Session:** miso-91 · **Lane:** 1 (governance defect named by miso-90) · **Date:** 2026-07-26
**Keeper:** `2026-07-25-miso-88-egrid-hr` — **unchanged by this session, no solve run.**
**Determination at entry:** CALIBRATED-WITH-CAVEATS, 3/3 ledgered caveats, keeper-auditor PASS/0.

This charter is written **before** any edit, per the miso-91 handoff's instruction to
pre-register scope and a pass/fail bar. It is a governance/plumbing repair with **no
value change and no solve**, so it carries no calibration hypothesis.

---

## 1. The defect

`_SUMMER_WEFOR_SHARE = 0.30` (`src/market_sim/data/fleet/arrays.py:167`) sets the
fraction of a thermal unit's WEFOR (forced-outage rate) that applies during the
summer peak; the remaining 70 % is redistributed into the shoulder months. It is:

* **uncited** — its comment describes the mechanic and names no source (rule 5 `[R-NO-MAGIC]`);
* **unregistered** — absent from `docs/parameter-citations.md` / `frontend/data/parameters.json` (0 hits);
* **undeclared** — absent from the keeper's 26-entry DOF ledger (rule 21 `[R-DOF]`);
* **off-registry by location** — it lives in a `data/` module, so it is in neither
  `ScenarioConfig` nor `constants.py`, which is what rule 20 `[R-REGISTRY]` requires.

### Root cause (measured, not assumed)

`scripts/validate_parameters.py` is the check that should have caught this. Its scope is
exactly `vars(constants)` plus `ScenarioConfig` dataclass defaults, and it skips any name
that `startswith("_")` or is not `isupper()` (`validate_parameters.py:59-69`). A private
literal in `data/fleet/arrays.py` is invisible to it three times over: wrong module,
leading underscore, not uppercase.

**Two things found while verifying that claim, both corrections to the record:**

* `docs/parameter-citations.md`'s own header states "`scripts/validate_parameters.py`
  fails CI if any constant ... lacks an entry". **It is not wired into CI at all** —
  `grep -rn validate_parameters .github/workflows/` returns nothing. The documented
  enforcement does not exist.
* The check **already fails on `main`**, with **48** parameters missing a citation entry.
  So even a correctly-homed constant would have landed in an existing red backlog.

Neither is repaired here (wiring a check that is already red would just break CI, and the
48-entry backlog is a separate program — see §7). This session's obligation is only to
**not add to the backlog**: after registering the constants moved here, the count returns
to exactly 48.

**So the three rule violations share one cause: the constant is in the wrong home.**
Its GADS-cited sibling `THERMAL_AVAILABILITY` lives in `config/fuel_trajectories.py`
and *is* registered (`thermal_availability.*`, 8 entries). The WEFOR *magnitude* is
cited ("Source: NERC GADS by unit type and age"); only its *seasonal reallocation* is not.

## 2. Measured blast radius (no LP; DOF sizing only)

Verified by building the availability matrix under the keeper's four decisive flags
(`outage_source='historic'`, `wefor_residual=None`, `coal_drop_pof=True`,
`cc_nameplate_summer_derate=False`, read from the bundle's `run_config.json`) and
detecting dependence by patching the constant.

**This corrects the miso-90 finding's framing.** That finding scoped the parameter to
"all 22.39 GW of MISO CT_PEAKER". In fact it governs **six** plant groups — every
non-coal thermal class. COAL is exempt: `coal_drop_pof=True` routes it to a branch
where summer WEFOR is dropped entirely (`arrays.py:586-593`), measured at delta 0.0000.

| group | nameplate GW | summer availability added by share=0.30 |
|---|---|---|
| ST_GAS | 11.61 | **+14.70 pp** |
| ST_CHP | 1.94 | +5.60 pp |
| CT_PEAKER | 22.39 | +4.29 pp |
| CC_REGULAR | 28.31 | +3.15 pp |
| CC_CHP | 7.04 | +2.52 pp |
| CT_CHP | 2.63 | +3.06 pp |
| COAL | 44.39 | exempt (0.0000) |

The per-unit effect is exactly `(1 − share) × wefor(age) × (1 − class_derate)`.
Against the committed per-class nameplates (FINDING-miso89 §5), the total summer
capacity the 0.30 choice creates relative to a flat-WEFOR baseline is
**≈3.9 GW at a uniform age of 18 y, ≈4.6 GW at 28 y, ≈5.8 GW at 38 y**. The real
fleet has an age distribution, so treat ≈3.9 GW as a soft lower bound.

ST_GAS carries the largest per-unit effect because its GADS WEFOR base (0.21) is the
highest in the table. Noted, **not** claimed causal: ST_GAS is also the class C8
reports as grounded-above-budget forced (35.7 / 36.9 / 51.1 %). A future session may
want to look at whether those two facts are related; this session does not.

## 3. What this session will NOT do

* **It will not change the value of `_SUMMER_WEFOR_SHARE`.** Re-tuning 0.30 against a
  residual is the rule 24 answer-key move, and doing it in the session after C3b was
  ledgered as a ~10 GW summer-peak under-derate would be indistinguishable from tuning
  to the ledgered miss. The C3b ledger explicitly does not license a fitted
  availability number.
* **It will not reopen C3b**, propose an offer adder, a summer multiplier, or widen C3c.
* **It will not ledger a new caveat.** The budget is saturated at 3/3
  (`MAX_LEDGERED_CAVEATS = 3`, check is `> 3`); one more entry forces NOT-YET.
  Nothing here is a load-bearing criterion miss, so nothing needs ledgering.
* **It will not run a solve**, so rule 15 dashboard registration is not triggered
  (no run is produced). The keeper's attestation is edited in place — the same
  scorer-only seam miso-90 used.

Note the blast radius (≈3.9–5.8 GW) is the same order as the ~10 GW gap C3b ledgers.
That is precisely the argument for grounding this parameter **from a source** rather
than by hand: a hand-set value here would be an answer key for an already-ledgered
miss. It belongs to the data ask, not to a sweep.

## 4. Scope

1. **Re-home the constants** — move `_SUMMER_WEFOR_SHARE` and its sibling
   `_SUMMER_CLASS_DERATE` to `config/fuel_trajectories.py` beside `THERMAL_AVAILABILITY`,
   as public uppercase `SUMMER_WEFOR_SHARE` / `SUMMER_CLASS_DERATE`, imported into
   `constants.py` so `validate_parameters.py` covers them from now on. **Values byte-identical.**
2. **Cite them** in `frontend/data/parameters.json`, regenerating `docs/parameter-citations.md`
   via `scripts/generate_parameter_registry.py` (the file is generated — never hand-edited).
3. **Declare `SUMMER_WEFOR_SHARE` in the keeper's DOF ledger** with
   `identification: "residual"` and an open `root_cause` pointing at the data ask.
   On the label: the parameter was never actually fitted to a residual — it is an
   a-priori heuristic (`market-sim-build-plan.md` calls it a "flat per-plant-group POF
   heuristic"). `"residual"` is chosen because it is the strictest existing enforcement
   category: `audit_keepers.py` E8 requires every `residual` entry to carry an open
   root cause. The entry prose states plainly that it is uncited-a-priori, not fitted,
   so no future reader mistakes the label for "we tuned this".
4. **Name it as a target of the data ask** in
   `docs/handoffs/miso-outage-grain-data-ask-2026-07.md`.
5. **Record the physics tension** (below) in the citation and the code comment.

### The physics tension, recorded

For **planned** outages, scheduling maintenance away from the peak is well-founded —
operators genuinely do it, and the POF side is separately grounded by the measured
`MAINTENANCE_MONTHLY_SHAPE`. For **forced** outages the same reallocation runs
*opposite* to the physics: forced outages correlate *positively* with heat and high
load. `SUMMER_WEFOR_SHARE < 1` therefore encodes a claim about forced-outage
seasonality whose sign is the reverse of the expected physical one. This is stated as
an unverified directional argument, not a citation — quantifying it is exactly what the
data ask is for.

## 5. Pre-registered pass/fail bar

**PASS** requires all of:

1. `calibration_verdict.py results/calibration/miso88_egrid_hr` still reports
   **CALIBRATED-WITH-CAVEATS** with **3** ledgered caveats — unchanged.
2. `audit_keepers.py --iso MISO` → **PASS / 0 failures**, with E8 now reporting one
   more entry and one more residual.
3. `validate_parameters.py` reports **exactly its pre-existing 48** missing-citation
   count — i.e. both constants are newly in scope AND registered, adding nothing to the
   backlog. (It cannot reach 0; see §2's correction.)
4. **No value changes anywhere.** `SUMMER_WEFOR_SHARE == 0.30` and
   `SUMMER_CLASS_DERATE == {CC_REGULAR: 0.10, CC_CHP: 0.10, CT_PEAKER: 0.125, CT_CHP: 0.125}`
   after the move, asserted by a test.
5. The targeted regression baseline is unchanged: the `run_calibration_full` importer
   modules stay at **8 failed / 186 passed**, and the fleet/facade suites that import
   these names pass.

**FAIL** (and revert) if the relocation changes any availability value, breaks the
facade re-export contract, or moves the determination.

## 6. Deliverables

* The relocation + citations + regenerated registry doc.
* A DOF ledger entry on the keeper (scorer-only; no bundle regen, no solve).
* A regression test pinning the values and the six-class/COAL-exempt branch map, so a
  future edit cannot silently re-privatise or re-tune either constant.
* `docs/calibration-log/miso.md` entry miso-91.

## 7. Named follow-ups, NOT taken here

1. **The parameter registry check is documented as a CI gate but is not one, and is
   already red (48 missing).** Wiring it would need the backlog triaged first. Owner
   call: triage the 48, then wire it — otherwise the header's claim should be corrected.
   Note `scripts/generate_parameter_registry.py` will auto-register all 48 as
   `needs-citation` stubs in one run; that was deliberately **not** done here, because
   mass-registering other lanes' gaps as stubs would mark them documented without
   anyone having sourced them.
2. **`wefor_residual = None` in the MISO keeper**, so the WEFOR cap at `arrays.py:532`
   never fires. That cap exists specifically to stop the statistical WEFOR
   double-counting the CAMPD overlay for covered classes (coal + `_POF_DROP_GROUPS`).
   With it off, MISO's CC and ST classes carry full statistical WEFOR *and* the historic
   overlay. Whether that is deliberate or a latent double-count was **not** determined —
   it needs a solve to settle and is outside this charter. Flagged for a future session.
3. **ST_GAS** takes the largest share of this DOF (+14.70 pp summer availability) and is
   also the class C8 reports as grounded-above-budget forced. Possibly related, possibly
   coincidence; not investigated.
