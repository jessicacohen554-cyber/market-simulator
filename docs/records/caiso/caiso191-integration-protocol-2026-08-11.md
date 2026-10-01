# caiso-191 — WAVE-2 INTEGRATION PROTOCOL (pre-committed 2026-08-11, BEFORE any Wave-1 result exists)

**This protocol is fixed before any lane has measured anything.** No Wave-1 outcome,
no C3a value, and no composed result may amend it. Deviation requires a fresh
adjudication session and explicit owner authorization (the campaign charter,
`caiso191-owner-rulings-2026-08-11.md`).

## 1. The ladder, fixed now

```
RUNG 0   CONTROL      — the caiso-188 keeper recipe, re-solved (§3)
RUNG 1   + Lane 1     — the merit-order-filtered outage overlay        (caiso-192)
RUNG 2   + Lane 2     — wefor_residual 0.0 {CC_REGULAR,CC_CHP}, mult 1.0 (caiso-193)
RUNG 3   + Lane 3     — gas_st_wefor_base_override = <frozen cited value> (caiso-193)
RUNG 4   + Lane 4     — hydro-plant-modes partition effective          (caiso-194)
RUNG 5   + Lane 5     — per-plant cited-physical PS (only if lane 5 ran) (caiso-195)
```

* **Arm inclusion is strictly the Wave-1 STRUCTURAL verdicts.** An arm whose Wave-1
  gates passed enters the ladder; an arm whose gates failed does not. **C3a is never
  consulted for inclusion, exclusion, or order** — the order above is fixed today,
  before any number exists, and does not reorder on results.
* **One mechanism per rung** (rule 19). Each rung adds exactly one lane's mechanism
  to the previous rung's base.
* **All three years per bundle** (rule 16): every rung solves 2023+2024+2025 in one
  invocation, years sequential (rule 12), and every rung's bundle is registered on
  the dashboard (rule 15) with `legitimacy_diagnostics.json` so C8 stays scored.

## 2. Skipped or degenerate lanes

A lane that never ran (kill-before-solve, null-FINDING, owner withdrawal) is simply
absent; the ladder renumbers by omission and does NOT backfill with a substitute.
**Degenerate case — zero surviving arms:** no new keeper, a null-FINDING recording
the campaign's exhaustion, hand to closeout. The lane inventory is closed; nothing
is improvised.

## 3. The control, and the ratified reproduction tolerance

Every solve session (Wave 1 and Wave 2) re-solves the control in its OWN environment
before running any arm:

* `--replay-bundle results/calibration/caiso188_d1_micseam` — never a remembered CLI
  string (the caiso-187 CONTROL clause).
* **The capacity-deliverability clean partition MATERIALIZED**, verified by the
  `seam import cap set to 16055 / 16452 / 16148 MW` log lines and (on the bundle) a
  seam dual of exactly 0.000 — check the DATA the gate resolves through, never the
  `run_config` flag (caiso-188 §7 item 5).
* **`hydro_ror_split` explicitly False, with no `hydro-plant-modes` partition
  present.** This is the keeper's PROVEN-EFFECTIVE configuration: caiso-188 G-CTRL
  reproduced the committed keeper exactly from an environment without the partition,
  so the committed LP never ran the split. Leaving the flag true would either
  fail-fast on the now-wired `check_clean_partitions` guard or — with a partition
  present — silently include lane 4's mechanism in the control. The override is
  disclosed in every control FINDING. (Rung 4+ arms then arm the split as their own
  single mechanism.)

**RATIFIED TOLERANCE (this session's §7 duty): per year, |ΔC3a| ≤ 0.1 pp and
|ΔC3b| ≤ 0.005 against the committed keeper values.** Rationale, stated so the
closeout can audit it:

* **Bit-zero is the observed CAISO norm** — caiso-184 measured same-head identity at
  BIT-ZERO (0 of 61,320 zone-hours), and caiso-188 G-CTRL reproduced the keeper to
  max |Δ| = 0.00 MW through 22 changed `src/` files and a different highspy build.
  So the EXPECTED control result is exact reproduction.
* **But byte-identity is not ratified as the GATE**, because cross-head drift is a
  measured reality elsewhere in this program (ercot-173: the run168b keeper does not
  reproduce at its later head — the nyiso-128 K6-class condition). A byte-identity
  requirement would convert an environment fact into a gate that head drift fails
  spuriously, forcing exactly the mid-session re-adjudication this protocol forbids.
* **The ceiling is an order of magnitude below every decision margin in play** (C3a
  2024 sits 0.4 pp outside the band, 2025 2.9 pp; the C3b watch margin is ~0.036),
  so no acceptance question can hide inside the tolerance.
* Operational rule: a nonzero-but-in-tolerance control delta is quoted as the NOISE
  FLOOR, at full precision, BEFORE any treated delta is read. A control outside
  tolerance is a **stop-the-line finding about the head** — reported as such, no arm
  solves, escalate. (caiso-187 CONTROL clause, generalized.)

## 4. Per-rung re-verification — what is re-checked, and what is NOT re-litigated

At each rung, on the COMPOSED base:

* **Engagement** — the rung's mechanism demonstrably ran (its lane's G-ENGAGE
  instrument, re-run on the composed bundle; a rung bit-identical to its base is
  INERT at composition and is recorded as such).
* **Ledger arithmetic** — the DOF ledger recomputed on the composed attestation; the
  composed ledger must equal the arithmetic composition of the accepted lanes'
  ledger moves (no entry silently reappears or double-retires).
* **Lane-2 premise recheck** (the one cross-lane arithmetic obligation): at the rung
  where lane 2 composes onto lane 1's filtered extract, re-verify
  `X_c^filtered ≥ W_c` for CC_REGULAR and CC_CHP through the frozen caiso-187 §2
  formula.
* **Wave-1 identification is NOT re-litigated.** Classifications, citations, and
  derivations accepted in Wave 1 are not re-opened at composition; only their
  engagement and arithmetic on the composed base are checked.

**Structural failure at composition ⇒ deterministic skip:** the failing arm is
dropped from that rung, the ladder CONTINUES ON THE PREVIOUS BASE, and the
interaction is recorded in the Wave-2 FINDING (which lanes conflict, on what
arithmetic). No mid-ladder value recomputation, no re-scoping, no substitute arm.

## 5. Criteria-panel flips

A criteria-panel **pass→fail flip** at any rung (C3b is the named watch — the
campaign frame records the 2025 margin as 0.164/0.20, to be re-derived at full
precision on the session's own control) triggers **input-side re-examination
ONLY**:

* If the re-examination finds an INPUT-SIDE DEFECT (a mis-citation, a classifier
  error, a coverage failure — something wrong with the measured input itself), the
  arm is killed on that defect, which is a Wave-1-grade structural failure.
* If the input survives re-examination — the input is accurate and the flip is the
  model reacting to accurate data — the disposition is **ACCEPT-WITH-FLIP, escalate
  to closeout/owner**. Rule 14 forbids rejecting an accurate input on fit; the flip
  is the discovered-bug signal rule 14 describes, and it is surfaced, never buried
  by silently dropping the arm.
* A criteria flip is NEVER resolved by silent rejection, and NEVER by consulting
  C3a.

## 6. Promotion

* **PROMOTION IS C3a-BLIND.** The final accepted rung promotes on **structural
  superiority** — fewer fitted scalars, measured inputs replacing fitted ones,
  mechanisms genuinely engaged — exactly the caiso-183 precedent (and caiso-188's:
  "the accurate input would have stayed even had the fit worsened"). C3a is reported
  in the promotion record for transparency and decides nothing.
* Any verdict flip relative to the incumbent keeper is scored **leave-one-year-out
  within 2023–2025 before promotion** (rule 22's standing LOYO clause).
* **The promotion attestation RE-MEASURES the C3c exceptions on the new bundle.**
  Verbatim carry of magnitudes measured on a superseded bundle would be a false
  attestation — the caiso-189 §8.3 precedent (which found two stale magnitudes on
  exactly this path) is now the rule. Classifications/reasons carry; magnitudes are
  re-measured; a criterion that passes on the new bundle gets no invented entry.
* The promoting session discharges the standing duties: dashboard registration
  (rule 15), matrix re-stamp (rule 28), per-ISO keeper lane files only. CAISO holds
  no `complete` marker, so rule 22 D-5(b) re-keying does not fire;
  `calibration-complete.json` / `holdout-freeze.json` remain owner acts, untouched.
* **If C3a-2025 still fails after the final rung, the campaign output is an
  EXHAUSTION MEMO** (the charter): the ladder's structural gains are promoted on
  their merits if gates pass, the C3a residual stays honestly declared, and no new
  lane is improvised.

## 7. Bookkeeping every rung owes

Each rung's bundle: registered sidecar + run payload (rule 15 transports per Git &
Pushing), `legitimacy_diagnostics.json`, the attestation generated (the caiso-189
E10 check must pass — no more free_parameters-only attestations), and the
calibration-log entry in `docs/calibration-log/caiso.md` in the same session.
