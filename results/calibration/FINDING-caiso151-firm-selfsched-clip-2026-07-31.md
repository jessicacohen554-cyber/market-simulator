# FINDING — caiso-151: `caiso_firm_import_selfsched_clip` **BUILT, SOLVED and PROMOTED**. The caiso-77 firm must-flow floor is now clipped at CAISO's own measured price-insensitive intertie ceiling. All four frozen derive gates PASS; the single-flag A/B leaves **every criterion verdict unchanged** and **both protective gates PASS**, at a **knowingly accepted, pre-registered E1-adverse** cost of +0.045/+0.626/+0.494 pp on C3a. New keeper `2026-07-31-caiso-151-firm-selfsched` (2026-07-31)

Lever: mechanism-matrix §5.2 CAISO queue **item 2**, whose only live prerequisite
was ANSWERED at caiso-150. This session did the **BUILD** caiso-150 §F specified
and deliberately did not attempt. Matrix cell `caiso_firm_selfsched_clip`
**`O` → `K`**.

Pre-registration: `PREREG-caiso151-firm-selfsched-clip-2026-07-31.md`, committed
and pushed **before either arm solved** and before any derive value existed.
Instruments: `scripts/data/derive_caiso_intertie_selfsched.py` (the frozen
derive), `scripts/probes/_caiso151_selfsched_clip_exposure.py` (pre-arm
exposure + plumbing check), `scripts/probes/_caiso151_arm_compare.py` (the A/B).

---

## §A — the mechanism

```
min_gen[t] = min( pmax × availability[t] , ceiling[t] )
```

the system ceiling allocated across the two firm tranches pro rata by their own
shaped capability in that hour — the pointwise min at the system level, with
**no allocation parameter**.

Three properties, all load-bearing:

1. **It clips the FLOOR, never the CAPABILITY.** Above the measured
   price-insensitive ceiling the import is still *available*; it is merely
   price-ELASTIC, so it is handed to the LP as economic capability instead of
   forced. Clipping availability — which is the right move for caiso-138's
   *deliverability* limit — would delete real import capability here.
2. **It COMPOSES with `caiso_firm_import_envelope_clip` as a second pointwise
   min, on its own flag** (rule 19 `[R-ONE-MECH]`). The two reconcile different
   objects: caiso-138 against the corridor's measured deliverability, this one
   against measured bid conduct. Arming it on caiso-138's flag was explicitly
   forbidden (caiso-150 §H) and was not done.
3. **Zero new DOF.** A pointwise min of two measured series. It *reconciles* the
   caiso-73 shape rather than stacking a mechanism on top of it.

---

## §B — the derive: all four frozen gates PASS

`scripts/data/derive_caiso_intertie_selfsched.py` →
`data/raw/_processed-legacy/caiso_intertie_selfsched_ceiling.csv` (288 rows).
Gates were declared **ex ante** in the script's docstring and in the
pre-registration, before any value was computed.

Corpus: **357 balanced trade days**, **1,574,341** (resource × hour) records,
1,531 masked resource seqs, 9–10 sampled days per (year, month), **zero archive
holes**. The caiso-150 corpus was gitignored and its container is gone, so this
is a genuinely **independent re-fetch** on the same balanced design.

| gate | statistic | measured | threshold | |
|---|---|---|---|---|
| **G1** | year-stability CV of the three annual mean levels | **0.042** | ≤ 0.20 | PASS |
| **G2** | LOYO **level**, each held-out year | **4.6 / 8.4 / 4.6 %** | ≤ 25 % | PASS |
| **G3** | LOYO **shape**, median over all 288 buckets | **19.3 / 12.3 / 18.6 %** | ≤ 25 % | PASS |
| **G4** | coverage, buckets sampled in all three years | **288 / 288** | 288 | PASS |

**It reproduces caiso-150 independently** on every dimension that can be
checked: unclassifiable share of self-scheduled MW **94.54 %** (caiso-150:
94.91 %), diurnal swing **1.52×** (1.49×), overnight ceiling **3,388–3,542 MW**
(3,381–3,443), evening peak **5,160–5,165 MW** at h18–h19 (4,990–5,215 at
h18–h20).

**The caiso-138 §C signature, re-measured on conduct.** Per-year ceiling levels
are **flat at 3,886 / 4,241 / 3,886 MW** while the DMM RA level the floor is
sized from steps **2,323 → 3,371 MW**. The floor grows; measured
price-insensitive conduct does not.

---

## §C — pre-arm exposure, and the plumbing check

`_caiso151_selfsched_clip_exposure.py`, no LP. Against the caiso-150 §C
prediction the pre-registration recorded:

| year | forced → clipped | forcing removed | caiso-150 predicted | clip binds |
|---|---|---|---|---|
| 2023 | 18.856 → 17.938 TWh | **0.919 TWh (4.9 %)** | 0.969 / 5.1 % | 2,006 h (22.9 %) |
| 2024 | 27.232 → 22.684 TWh | **4.548 TWh (16.7 %)** | 4.634 / 17.0 % | 4,068 h (46.4 %) |
| 2025 | 27.989 → 22.494 TWh | **5.495 TWh (19.6 %)** | 5.705 / 20.4 % | 4,469 h (51.0 %) |

The forced totals reproduce caiso-150 §A **exactly** (18.856 / 27.232 / 27.989),
and the removed energy lands within ~5 % of a prediction made on a *different
corpus* — well inside the pre-registration's §4(c) factor-of-two REJECT band.
60.5–64.1 % of the removed forcing is overnight (h22–h05), as registered.

**Plumbing check PASSES.** The 2024 fleet rebuilt with the flag armed through
the same generic override channel `replay_keeper --set` writes to reproduces the
predicted clipped floor at **max|Δ| = 0.000000 MW**, and the injector logs the
caiso-151 suffix *only* on the armed build. (This exists because caiso-150 §E2
recorded a silent trap: CAISO's firm-import flags have no CLI flag and no
top-level `meta.json` key and reach a solve only via the channel whose meta name
is `coal_prb_sigmoid_overrides`.)

---

## §D — the A/B: every verdict unchanged, both protective gates PASS

Two arms, `--year 2023 2024 2025` each in one invocation, run concurrently,
single-flag delta verified on the metas (`caiso_firm_import_selfsched_clip:
None → True`, the only difference).

**Forced ≠ removed, and the difference is the mechanism working.** Only
**0.042 / 1.099 / 0.628 TWh** of import energy actually stops flowing against
0.919 / 4.548 / 5.495 TWh of *forcing* removed. The rest flows anyway, on
economics — which is precisely the designed behaviour: the clip converts forced
import into **elastic** import, it does not delete it.

Displacement is import → domestic **CC_REGULAR** almost 1:1 (2024: import
−1,098.8 GWh, CC_REGULAR +1,055.7 GWh; 2025: −628.3 / +596.2 GWh).

| criterion | control | arm |
|---|---|---|
| C1 fuel-mix | PASS | PASS |
| C2 system volume | PASS | PASS |
| C3a mean LMP | CAVEAT | CAVEAT |
| C3b price shape | PASS | PASS |
| C3c price tail | CAVEAT | CAVEAT |
| C4 dispatch corr | PASS | PASS |
| C6 governance | PASS | PASS |
| **C7 diurnal shape (protective)** | **PASS** | **PASS** |
| **C8 forced share (protective)** | **PASS** | **PASS** |

Determination **CALIBRATED-WITH-CAVEATS**, **0 FAILs**, C1 **all 12/12 · free
8/8**, the same **2 of 3** ledgered slots, protective **0/1** — identical to the
caiso-148 keeper on every scored dimension.

**Binding protective gates, on the classes that ABSORB the change** (CC_REGULAR,
CT_PEAKER; nuclear and the CHP classes are exempt from both C7 and C8 by
explicit class list and none of their numbers is quoted here as a gate):

- CT_PEAKER C7 `profile_r` 0.881 / 0.933 / 0.866 → **0.881 / 0.932 / 0.865**
- CT_PEAKER C8 forced share 0.0015 / 0.0059 / 0.0007 → **0.0015 / 0.0058 /
  0.0007**, against the 0.15 peaker cap
- CC_REGULAR C8 `ra_mustoffer_bridge` share **FALLS** 0.0795 → 0.0784 (2024),
  0.0953 → 0.0937 (2025)

ST_GAS 2024/2025 raw D-1 rows read FAIL on **both** arms and have since before
caiso-148 — pre-existing, below the 2 % materiality floor, **not** attributable
to this lever. (2024 `profile_r` 0.231 → 0.173 is recorded for completeness.)

---

## §E — the registered E1-adverse cost, paid knowingly

The pre-registration stated the direction before either arm solved, so it cannot
be spun now. **It is confirmed on both legs.**

- Overnight (h22–h05) λ **RISES**: **+$0.043 / +$0.376 / +$0.224** per MWh.
- CAISO's model λ already sits **ABOVE** the RT actual, so the **C3a miss GROWS**:
  **+3.01 → +3.06 %** (2023), **+8.05 → +8.68 %** (2024), **+11.23 → +11.72 %**
  (2025) — movements of **+0.045 / +0.626 / +0.494 pp**.

All three are **below** the **1.0 pp** materiality trigger `PREREG-caiso151` §6
fixed in advance, so none is built upon. But the 2025 movement is an order of
magnitude larger than the 0.0 pp caiso-148 recorded, and it lands on a
**ledgered caveat**, so it is stated plainly rather than left to be discovered.
It does **not** reopen C3a-2025: reopening requires new evidence against a named
caiso-140/141/142/143/144 DO-NOT-REDO cell, or the owner-funded non-public
hourly pumped-storage intake.

**Rule 1 `[R-STRUCT]` governs the promotion.** A structurally-correct mechanism
stays in even when the fit worsens, and the response to a worse fit is to name
the root cause, never to revert. Equally, rule 1 forbids adopting a mechanism
*because* a residual moved — this one is adopted because the floor it clips
forces more price-insensitive import than CAISO's own bid record can support in
roughly half of all hours.

**Rule 22 leave-one-year-out** is discharged at the derive stage: the mechanism
introduces **no fitted parameter**, so there is nothing to overfit, and gates G2
(level) and G3 (shape) are themselves leave-one-year-out within 2023–2025 and
pass in every held-out year. The in-solve effect is same-signed and monotone
across all three years, so no single year drives it.

---

## §F — CORRECTION to caiso-150 §A, and to this session's own first claim

caiso-150 §A reported that `MECH_FIRM_IMPORT` is invisible to the D-4
off-window check **because** it carries no `D4_WINDOWS` entry. This session
added that entry — and **the `firm_import` row still does not appear** in either
arm's `legitimacy_diagnostics.json`. The first commit of this session asserted
the entry would deliver visibility; that assertion was wrong and is corrected
here.

**Measured cause.** The diagnostics harness scores a **plant-aggregated** matrix
built from CAMPD plant ids (`all_pids`, `legitimacy_diagnostics.py`). The
intertie tranches carry `plant_code = 0` and an empty `plant_group`, so they are
dropped from the matrix that D-1, D-2 **and** D-4 all score. Run `run_d4`
directly on the unaggregated LP rows and the row appears immediately:

```
{'year': 2024, 'floor': 'firm_import', 'window': 'h0-23',
 'floored_twh': 15.4689, 'offwindow_twh': 0.0, 'offwindow_share': 0.0,
 'verdict': 'pass'}
```

So the floor's gate-invisibility has **two** causes, and the **binding one is
the plant-set restriction, not the missing window**. The `D4_WINDOWS` entry is
kept because it is a correct rule-12/17 declaration and is *required* for the
row ever to appear — it is necessary but not sufficient.

**FILED, NOT ABSORBED.** This is an **ISO-generic diagnostics-harness defect**:
it equally hides MISO's Manitoba and NYISO's HQ firm must-flow blocks. It
belongs to the diagnostics lane, not a CAISO lever session.

---

## §G — disposition

- **Verdict `K`. PROMOTED.** New keeper `2026-07-31-caiso-151-firm-selfsched`,
  CALIBRATED-WITH-CAVEATS, 0 FAILs, C1 12/12 · free 8/8, 2 of 3 ledgered slots,
  protective 0/1. Control `2026-07-31-caiso-151-control-zerodelta`.
- **Item 2 (corridor/export-path congestion)**: caiso-143 §H's "then re-examine
  whether any sink is wanted, with `F` reduced" is now **reachable** — `F` is
  reduced by 4.9/16.7/19.6 %. Nothing in caiso-142/143's refusals is reopened by
  this; the export half stays closed with nothing unbuilt.
- CAISO still holds **no** rule-22 calibration-complete marker. This session
  solved 2023/2024/2025 only and wrote no marker.

## §H — DO-NOT-REDO (new, binding)

* **Re-deriving `caiso_intertie_selfsched_ceiling.csv` against a residual.**
  Rule 23 `[R-FROZEN-DERIVE]`: it re-runs only on a source-corpus change, and
  such a commit must cite the data change. The four gates are frozen; do not
  retune a threshold to move a verdict.
* **Re-litigating the E1-adverse cost as a rejection ground.** It was registered
  before the solve, measured after it, and accepted under rule 1 by the owner's
  standing instruction that structural integrity may outweigh gate regression.
  A successor may revisit the *root cause* of CAISO's over-priced λ; it may not
  revert this clip to recover 0.5 pp of C3a.
* **Arming this clip on the caiso-138 envelope-clip flag**, or replacing the
  envelope clip with it. They reconcile different objects and compose as two
  pointwise mins (rule 19).
* **Clipping CAPABILITY instead of the FLOOR.** Above the ceiling the import is
  real and available; only its *forcing* is unsupported.
* **Attempting the import/export split of intertie self-schedules** by any route
  — caiso-150 §H is carried forward unchanged and the wall is re-confirmed here
  at 94.54 %.
* **Quoting the midday ratio as under-forcing.** Midday is where CAISO export
  self-schedules peak, so the unsigned ceiling is most generous there.
* **Absorbing §F's diagnostics-harness defect into a CAISO lever session.** It
  is ISO-generic and belongs to the diagnostics lane.
* **Citing the D4_WINDOWS entry as evidence the floor is now gate-visible.** It
  is not; §F measures why.

Carried forward unchanged: `FINDING-caiso150` §H, `FINDING-caiso149` §G,
`FINDING-caiso148` §G, `FINDING-caiso147` §G, `FINDING-caiso146` §G,
`FINDING-caiso144` §G, caiso-143 §I, caiso-142 §H, caiso-141, caiso-138 §G,
caiso-137b §6, caiso-131 §10.

Next number: caiso-152.
