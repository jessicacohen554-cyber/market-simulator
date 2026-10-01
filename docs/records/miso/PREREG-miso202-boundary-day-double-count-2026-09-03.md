# PREREG miso-202 — the ADJACENT-WINDOW BOUNDARY-DAY DOUBLE-COUNT (2026-09-03)

**Registered BEFORE the mechanism exists.** Phase 0
(`results/calibration/_miso202_boundary_day_phase0.json`, probe
`scripts/probes/_miso202_boundary_day_phase0.py`) was committed first, before this
document and before a line of mechanism code.

**Session:** miso-202. **Keeper at open:** `2026-09-02-miso-201-stbasis`
(bundle `results/calibration/miso201_stbasis_B`), determination **NOT-YET** on
`{C3a-2025 −12.3845}` alone, C3c the single ledgered caveat, C6 attested (ledger 40/2).

**Charter position:** queue item 1, the charter's own top-ranked lever and
FINDING-miso201 §7 item 1's named successor — *"with the numerator aligned it is now the
ONLY mechanism still producing steam overflow"*.

---

## 1. The object

`outages.unit_outage_event_window` reconstructs a day-granular extract row as the half-open
window `[outage_start, outage_end + 1 day)`. Two windows of the **same unit** whose first
row's `outage_end` falls on the second row's `outage_start` therefore both cover that
boundary day. `outages._unit_outage_factors_from_events` **SUMS** row shares into the bin
rather than unioning them, so the unit's capacity is subtracted **twice** for 24 h:

```
arr[mask] += removed_frac * ucap / cap[tgt]        # one row at a time, no per-unit ceiling
```

On a day a unit can be at most 100 % out of service, the accumulator credits it with 200 %.

**This is a defect, not a calibration choice.** There is no market, physical or accounting
reading under which one unit is more than fully out. Nothing here is fitted, nothing is
tuned, and the repair has **zero free parameters** (rule 21 `[R-DOF]`).

## 2. What phase 0 established, before this document

| measurement | result |
|---|---|
| **N-1 reproduction gate** | **589 bins checked, 0 mismatches** — every reconstructed pre-clip share reproduces production's `clip(1 − v, 0, 1)` exactly, on all three layers that share the accumulator |
| **N-2 census** | **845 same-unit overlapping pairs** (std5d 648, layup 197, short 0) |
| **N-2 signature** | the overlap-length histogram is a **SINGLE bin at exactly 24.0 h**, 845/845 — the fingerprint of the `+ 1 day` artifact and of nothing else |
| **N-3 counterfactual** | a per-unit clip restores **91.1 / 77.6 / 103.4 GWh** of capability in 2023 / 2024 / 2025 |
| **N-3 reach** | CC_REGULAR **55.9 / 17.3 / 50.2**, ST_GAS **32.0 / 56.3 / 50.6**, COAL 0.7 / 1.5 / 2.4, CC_CHP / ST_CHP small — **not** the four steam bins miso-201 could see |
| **N-4 landing** | only **1.4 % / 0.0 % / 1.4 %** of the restored capability falls in the keeper's own top-1 % price hours |
| **N-5 maxgen twin** | **0 overlapping pairs over 544 unit-series** — its windows are already hour-granular, so the layer is out of scope **BY MEASUREMENT** |

**miso-201 sized this object from a steam-scoped instrument and called it "small
(24–72 h/yr per bin)".** Measured class-agnostically it is neither steam-only nor
bin-local: it is 845 pairs across 63 bins and four classes. That widening is a phase-0
result, recorded here before the arm exists.

## 3. The mechanism to be built

`ScenarioConfig.unit_outage_per_unit_clip` — **GATED, default off, byte-inert off**,
registered in `_CACHE_KEY_OPTIONAL_FIELDS` **in the same commit as the field** (the
nyiso-119 / caiso-186 / miso-201 discipline).

In `_unit_outage_factors_from_events`, accumulate each **unit's** removed MW into its own
hourly array, clip that array at the unit's own capacity, and only then sum the units into
the bin. One statement of one invariant, in the one accumulator all four std-family layers
share (rule 19 `[R-ONE-MECH]`).

**Scope, decided by measurement, not inheritance.** The maxgen layer is **excluded**: N-5
measures **zero** same-unit overlaps in it because its windows are hour-granular, so the
flag would be provably inert there while widening the blast radius. The lay-up layer is
**included** — it shares the accumulator and its contract is that "a lay-up share and an
outage share for the same plant sit on the same basis and are additive", which clipping one
and not the other would break (the same rule-19 reasoning miso-201 recorded).

## 4. The gates — FROZEN

Arithmetic frozen from the keeper's own committed verdict, before the arm exists.

### Soundness

* **S-0 control integrity.** The control leg must be **BIT-IDENTICAL** to the keeper's
  committed sidecars, `max_abs_diff` 0.0, across all 9. Drift is **DISCLOSED**, never
  silently absorbed, and is not itself a kill.
* **S-1 single delta.** Exactly one `ScenarioConfig` field differs between the legs:
  `unit_outage_per_unit_clip`. A failure **VOIDS** the A/B — it did not measure the lever.
* **S-2 liveness.** Measured directly off the production loaders with the flag off and on,
  never inferred from a downstream number something else could have moved. LIVE iff at
  least one bin's availability strictly rises, in each of the std5d and layup layers.
  **Liveness only — never a target.**
* **S-3 MONOTONICITY — a HARD VOID, and this lever's own soundness line.** The per-unit
  clip can only ever remove **less** capacity, never more. So on **every** bin, **every**
  hour and **every** layer, the arm's availability must be **≥** the control's. A single
  hour in which the arm removes more capacity than the control is a bug in the mechanism,
  not a result, and **VOIDS** the A/B. It is checkable without a solve and is checked
  before either leg is run.

### Kills

* **K-1 C1 band, ±8.00 TWh, no band exit anywhere.** Named cells, read off the keeper's
  committed verdict:

  | class-year | keeper face (TWh) | headroom to ±8.00 | expected direction |
  |---|---:|---:|---|
  | ST_GAS-2024 | −7.488 | **0.512** — the tightest cell on the board | UP (favorable) |
  | CC_REGULAR-2024 | **+6.931** | **1.069** | **UP — THE NAMED RISK** |
  | ST_GAS-2025 | −6.681 | 1.319 | UP (favorable) |
  | COAL_PRB-2025 | −4.904 | 3.096 | DOWN — named adverse (displacement) |
  | ST_GAS-2023 | −3.512 | 4.488 | UP (favorable) |
  | CC_REGULAR-2023 | −3.434 | 4.566 | UP (favorable) |
  | CC_REGULAR-2025 | −2.194 | 5.806 | UP (favorable) |

  **THE NAMED RISK is CC_REGULAR-2024.** The model already over-produces CC there and the
  arm restores CC availability, pushing it **further** from zero toward the +8.00 edge.
  The phase-0 capability bound for CC_REGULAR-2024 is **0.017 TWh** against **1.069 TWh**
  of headroom — a 60× margin, and an expectation that can be wrong, never a reason to skip
  the gate.

  **The whole-arm capability bound is 0.091 / 0.078 / 0.103 TWh** (phase-0 N-3), below
  every headroom in the table including the 0.512 TWh at ST_GAS-2024.
* **K-2** C3b: no PASS → FAIL.
* **K-3** D-4: **zero NEW off-window binding.**
* **K-4** D-1 shape: no PASS → FAIL.
* **K-5** zero PASS → non-PASS on any scored record.
* **K-6** DOF / attestation scorable.

**THE miso-200 VACUOUS-PASS TRAP STAYS CLOSED.** A `--replay-bundle` solve writes no
`legitimacy_diagnostics.json` and no `calibration_attestation.json`. K-3 / K-4 / K-6 are
therefore **REFUSED** — reported `UNSCORED`, never `PASS` — unless **both** legs carry
non-empty D1 / D4 rows and attestation entries. Diagnostics and attestations are generated
for both legs **before** the pair is scored.

### Named risk outside the kills

**C8 may move the wrong way, and the reason is stated ex ante.** The lay-up layer feeds the
must-run floor mask, and the clip **reduces** the laid-up share, which **raises** the
floor's clip basis and lets the floor assert on more capacity. This is the same honest
mechanism miso-201 reported: a repair that is right on its own terms can raise forced share.
It is reported at full magnitude against the outcome, whichever way it moves. The keeper's
ST_GAS forced shares are 0.1551 / 0.1529 / 0.2713 against the 0.30 merchant budget.

## 5. What is NOT a gate

**C3a is reported at full magnitude and is NEVER a gate** (rule 1 `[R-STRUCT]`). The
keeper's sole failing criterion is `C3a-2025 −12.3845` and the charter's standing object is
that miss — but this arm's justification is the defect, not the residual, and **no branch of
the scorer reads C3a**. Phase-0 N-4 measured, before the arm existed, that **1.4 % of the
restored capability lands in the keeper's own top-1 % price hours in 2025 and 0.0 % in
2024**, so the honest ex-ante expectation is that C3a barely moves. If it moves the wrong
way the arm still stands or falls on §4; if it moves the right way that is **not** evidence
for the mechanism.

The same holds for **C3c**, the ISO's single ledgered caveat.

## 6. Standing context, recorded before any result, and NOT a licence

The owner's 2026-09-02 re-scoping — *"if structural integrity improves but gates regress
that may still be a keeper"* — is carried forward as context. It **does not** silence a kill
and changes no threshold above. A fired kill is reported as fired, at full magnitude, and
the scorer **never promotes** on that branch: it states the structural case and the
regression side by side and leaves the decision to the owner.

## 7. Discipline

Rule 22: **2023–2025 only** — MISO holds no `complete` or `final` marker and the holdout
freeze is active. Rule 16: all three years in **one** bundle, one invocation, years
sequential. Rule 12: solved in-session, never CI. Rule 15: both legs registered on the
dashboard in this session. Rule 28(b): the tested cell stamped in
`docs/codebase-site/data/mechanism-matrix/MISO.js`; rule 28(c): the new `ScenarioConfig`
field's base row plus a cell in **all six** shards, in the same PR. Rule 25: only MISO's
shard / keeper / status files are touched.
