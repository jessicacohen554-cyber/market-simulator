# PRE-REGISTRATION — nyiso-100: retire the mis-attributed simultaneous-import scalar

**Date:** 2026-07-30 · **ISO:** NYISO · **Committed and pushed BEFORE any solve.**
**Charter:** `docs/FINDING-nyiso100-simultaneous-import-misattribution-2026-07-30.md`
**Matrix row:** `nyiso_import_sil_retire` · **Rule:** 14 `[R-ACCURATE]`, 19 `[R-ONE-MECH]`, 22 `[R-DOF]`

---

## 1. The arm — exactly one delta

`ScenarioConfig.nyiso_import_sil_retire: bool = False` → `True`.

When on, `interchange.spec.apply_interchange_topology` calls
`transmission.retire_misattributed_sil`, which drops the
`NYISO_simultaneous_import` `InterfaceLimit` (identified structurally as the
one whose every link originates at the import node — the same identification
`apply_deliverability_seam_limit` already uses). Nothing else changes: the four
border-link TTCs, the internal chain, the monthly reconciliation band, the
priced tranche ladder and every other NYISO mechanism are untouched.

**Aggregate simultaneous import goes 4,350 MW → 6,800 MW** (the border-link
sum), which is inside the measured admissible interval and introduces **no new
number**. DOF ledger: one free parameter **removed**, none added — `n_residual`
must not rise.

## 2. Runs

Both from the same pushed HEAD, `scripts/replay_keeper.py` on the nyiso-99
keeper's own `meta.json`, all three years in one invocation (rule 16),
sequential within each invocation, two invocations concurrent (rule 12).

| run | bundle | delta |
|---|---|---|
| control | `results/calibration/nyiso100_control` | none — flag off |
| arm | `results/calibration/nyiso100_silretire` | `nyiso_import_sil_retire=True` |

## 3. Pre-registered gates

**G0 — control reproduces the keeper.** Control must be **bit-identical** to
`nyiso99_demandfix`: max |Δ class MW| = 0.000000 and max |Δ price| = 0.000000
$/MWh across all zones/hours/years. Any drift stops the session (the container
does not reproduce the keeper, and nothing downstream is interpretable).

**G1 — LIVE-mechanism check (nyiso-89 §4a).** Before reading any result: the
arm's solved topology must carry **zero** interface limits whose links all
originate at `NYISO_external`, and the control's must carry exactly one at
4,350 MW. A silent no-op is a failed arm, not a null result.

**G2 — the mechanism actually releases.** Arm's model import must exceed
4,350 MW in ≥1 hour of ≥1 year, and its annual max must land in
(4,350, 6,800]. If the arm never imports above 4,350 the constraint was not the
binding one and the arm is inert (report as `I`).

**G3 — volume is band-held, not released.** Monthly model/measured import ratio
must stay inside [0.98, 1.02] in every month of every year, and the count of
months at the upper edge must not fall below the control's 10/11/11. This is
the check that the arm **reallocates** a fixed monthly quota rather than
importing more energy. A breach means the band is not doing what §4 of the
finding claims and the interpretation is void.

**G4 — C1 protective gate holds.** C1 must stay **PASS 14/14, free 10/10**. The
2023 `CC_REGULAR` cell is the ISO's tightest (−2.79 of ±2.94, 0.15 TWh margin);
it may move but must not fail.

**G5 — C7/C8 protective gates hold.** C7 PASS. C8 PASS, with the fragile 2024
`ST_GAS` grounded-above-budget cell (30.4%) reported either way.

**G6 — C3c reported, not targeted.** Hours > $300 (model vs actual 10/12/42)
reported for all three years. **C3c is not a gate on this arm** and no C3c
movement, in either direction, is grounds for promoting or rejecting it
(rule 1 `[R-STRUCT]`).

**G7 — item-9 import shape reported, not targeted.** Import `r_hr` reported
against the control's 0.598 / 0.623 / 0.453.

## 4. Directional predictions (recorded now; NOT acceptance criteria)

Stated so the result cannot be re-narrated after the fact:

1. **Import `r_hr` gets worse or stays flat.** The cap binds 54/59/62% overnight
   and only 3/2/2% in h16–h18; releasing it lets the LP buy more of its
   band-fixed quota in its wrong-phase overnight peak.
2. **Peak duals rise slightly, so C3c hours > $300 tick up.** Band-fixed volume
   reallocated overnight means less import at the real peak. Magnitude expected
   to be small: the released energy is ~0.4–0.8 TWh/yr spread over ~8,200
   non-cap hours, ≈50–100 MW/h.
3. **Prediction 2 is NOT a C3c fix and will not be claimed as one.** C3c is a
   diagnosed structural limitation of the five-zone representation with an
   empty lever queue (nyiso-94/95/96/97, re-open conditions FINDING-nyiso97 §5,
   none satisfiable). Any C3c movement here is a by-product of removing a
   mis-attributed constraint, not a C3c mechanism.

## 5. Promotion rule, fixed in advance

Promote to KEEPER-RECOMMENDED **iff** G0, G1, G2, G3, G4 and G5 pass — i.e. the
control reproduces, the mechanism is live and releases, volume stays
band-held, and no protective gate fails. G6/G7 are **reported and cannot veto**.

If G2 fails (inert), the row goes to `I` with the evidence and no keeper change.
If G4 or G5 fails, the row goes to `R` and the finding records the protective-gate
breach as the reason — **not** the residual.

Rejection is registered on the dashboard exactly as a promotion would be
(rule 15), and the matrix cell is updated in this same session (rule 28b).
