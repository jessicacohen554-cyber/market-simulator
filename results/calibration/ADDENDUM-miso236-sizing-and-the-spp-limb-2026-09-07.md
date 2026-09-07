# ADDENDUM miso-236 — two supplementary measurements declared BEFORE they are computed, and one census disclosure declared as POST-HOC

Extends `PREREG-miso236-neighbour-state-and-the-idiosyncratic-residual-2026-09-07.md`
(pushed `92de849b`). On the miso-233 / miso-235 addendum pattern.

**No pre-registered decision rule is touched and NO PRE-REGISTERED VERDICT CAN MOVE.** The
PREREG's provenance gate, census, Q-A and Q-B values are already computed and committed in
`results/calibration/_miso236_neighbour_state_residual_phase0.json`, and they stand exactly as
measured whatever this addendum finds. Nothing here can arm a mechanism, charter a lever, move a
matrix cell, or touch the keeper (`2026-09-07-miso-233-spp-hourly`, CALIBRATED, C3c the single
ledgered caveat, DOF 41/2). Zero LP, as the PREREG declared.

---

## A — the SIZING restatement (declared HERE, before it is computed)

The PREREG's Q-A answers *what share of the measured residual's variance* neighbour state
explains. A successor sizing a candidate needs the same statement in **MW of σ**, which is pure
arithmetic on two already-published quantities and is fixed here so it cannot be shaped:

    sigma_supply(s, year) = sqrt( delta_R2_A_nohydro(s, year) ) * sigma_resid_measured(s, year)

with `sigma_resid_measured` taken from the committed
`_miso235_seam_variance_decomposition_phase0.json` (and reproduced to **0.00 MW** by this
session's own provenance gate). It is reported against that seam's **residual-σ gap**,
`sigma_resid_model − sigma_resid_measured`, likewise from miso-235.

**RULE, fixed here: REPORTED, NOT GATED.** `sigma_supply` is an upper bound on what a *perfect*
use of this block could contribute to that seam's σ under the pre-registered no-hydro block. It
**moves no pre-registered verdict**, is **not** a target for anything, and — stated explicitly
because rule 13 `[R-MEASURED]` and rule 1 `[R-STRUCT]` both bite here — **a successor may not
size, scale or tune any mechanism to make a modelled σ land on it.** It exists to tell a
successor whether an admissible object is *worth chartering at all*, not what value to give it.

## B — WHICH member of Block A carries the SPP increment (declared HERE, before it is computed)

Block A has three members (`nl_nbr`, `vre_nbr`, `hyd_nbr`), of which the PREREG gates the
**no-hydro** pair. For any seam reading **ADMISSIBLE**, the per-member increment is reported:
`ΔR²` of each Block-A member added **singly** on top of Block B, and of the gated no-hydro pair
together (already published). This is a characterisation of an object the PREREG already
adjudicated, not a new adjudication.

**RULE, fixed here: REPORTED, NOT GATED, and it cannot change the seam's verdict** — the verdict
is the pre-registered `ΔR²_A_nohydro` on the joint block and stays exactly as committed, whatever
the per-member split shows. No bar attaches to any per-member value, and no member is selected,
promoted or excluded on the strength of one.

## C — a CENSUS DISCLOSURE that is POST-HOC, and is labelled as such

Stated against interest rather than presented as pre-registered: **the following was computed
AFTER the PREREG's verdicts were read.**

`SIKE` appears in the `MISO_SEAM_DIBA["South"]` pool and the probe's census lists it under
`present_in_balance`, because a `SIKE` balancing-authority row exists in EIA-930 BALANCE from
**2025-06-01** onward. Those rows carry **zero finite `Demand (MW) (Adjusted)` values** — 0 of
5,137 — so `SIKE` contributes **nothing** to the South seam's Block A in any hour.

**It can move nothing, and that is arithmetic, not judgement:**

* Block A sums over its members with NaN-skipping, so the South block is **byte-identical** with
  or without `SIKE`; every South `ΔR²`, `R²_AB` and unexplained share stands unchanged.
* `SIKE` carries **0.00000 / 0.00000 / 0.00006** of the South seam's gross flow magnitude in
  2023 / 2024 / 2025, so the PREREG §2a covered-gross-share reads **1.000 / 1.000 / 0.99994**
  without it against a 0.50 bar — the census verdict is unchanged.

The honest reading is that the census's `present_in_balance` list is **nominal presence**, and
the South block is in substance **SOCO + TVA + AECI + LGEE**. That is how it is described in the
FINDING.

## D — governance

Rule 1 `[R-STRUCT]`: nothing is judged by a residual and nothing is proposed. Rule 13
`[R-MEASURED]`: measurement only; §A states in advance that its number may not be used as a
tuning target. Rule 15: no run produced. Rule 21 `[R-DOF]`: 41/2, unchanged. Rule 22: 2023–2025
only. Rule 23 `[R-FROZEN-DERIVE]`: no derive re-run. Rule 25 `[R-ISO-SCOPE]`: MISO only.
Rule 28(b): evidence-append form; no cell verdict moves. Rule 29 `[R-SCREEN]`: still clause 0,
zero LP.
