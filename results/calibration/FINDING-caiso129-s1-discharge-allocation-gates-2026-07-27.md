# FINDING — caiso-129: S1 (the DA/RT allocation on the DISCHARGE side) is **KILLED at the derive gates**. D2 fails on stability (r 0.9726 < 0.99, charge-side control 0.9919), and D3 fails STRUCTURALLY — the floor leaves the overnight 2.9–5.2× free **for any day total**, and its own overnight limb would FORCE +65/+146/+192 MW/h of *extra* overnight discharge against a defect that needs 151/99/98 MW **removed**.

**Keeper `2026-07-27-caiso-126-ror-split` UNCHANGED. NO LP WAS SOLVED, no
mechanism was built, nothing was registered.** This is the correct execution
of the owner grant, not an abandonment of it: D3 was granted as a **hard
kill-before-solve** gate and it fired. The one deliverable of a failed
kill-before-solve gate is the measurement that killed it.

Instrument (committed): `scripts/probes/_caiso129_s1_gates.py` — D1–D4 plus
the charge-side control, every number reproducible from the committed CAISO
Daily Energy Storage Report xlsx and the committed keeper bundle's own
`hourly/storage_<year>.parquet` sidecars. No LP is built or solved anywhere in
it. The live rule-23 derive
(`scripts/data/derive_caiso_charge_allocation.py`) is **untouched** — the
discharge statistic is computed in the probe by a lifted copy of that script's
own `side_stats` code path, so no production artifact was regenerated for a
candidate the gates killed.

---

## §1 — D1: the measured discharge-side allocation (PASSES, it exists)

From the same LESR `EN` rows as the charge side with the sign flipped
(`+EN` = discharge), same clock convention (`hod = HOUR-1`, fall-back 25th
hour and Feb-29 dropped), HYBD excluded:

| year | `da_frac_dis` | IFM dis | RTD dis | overnight(0-6) share | belly(10-14) | evening(17-21) |
|---|---|---|---|---|---|---|
| 2023 | 0.7957 | 4.340 TWh | 4.542 TWh | **0.090** | 0.000 | 0.807 |
| 2024 | 0.8015 | 7.246 | 8.270 | **0.100** | 0.000 | 0.780 |
| 2025 | 0.7782 | 9.806 | 12.068 | **0.108** | 0.000 | 0.734 |

The statistic is well-defined and the DA share (0.778–0.802) is in the same
band as the charge side's 0.760–0.840. **The evening share is high and the
belly share is exactly zero, as the ask predicted** — but the overnight share
is *not* zero, and §3 shows that is the fact that destroys the mechanism.

## §2 — D2: STABILITY **FAILS** (kill), and the charge-side control proves it is the measurement

Gates (the ask §5, the caiso-106/107 discipline): pairwise cross-year
`r >= 0.99` and per-hod `CV <= 0.20`.

| basis | min pairwise r | max gated per-hod CV |
|---|---|---|
| **charge** `alloc_share` (control) | **0.9919** | 0.392 |
| **discharge** `alloc_share_dis` | **0.9726** | 0.464 |
| charge fleet-norm rate (control) | **0.9935** | 0.411 |
| discharge fleet-norm rate | **0.9755** | 0.444 |

Pairwise on the discharge share: r(2023,2024) 0.9960, **r(2023,2025) 0.9726**,
r(2024,2025) 0.9877.

**Verdict: FAIL on the r limb.** The charge control clears 0.99 on both bases
(0.9935 on the fleet-normalized basis — the basis FINDING-caiso103 §1A's
"r ≥ 0.994" was measured on, consistent to rounding), and the discharge side
does not clear it on either. Because both sides ran through an identical code
path, the difference is a property of the measurement, not of this probe's
basis choice.

**Stated honestly: the CV limb of D2 is non-discriminating and carries no
weight here.** The charge side — the mechanism the owner already accepted —
also exceeds `CV <= 0.20` (0.392), so that limb as written would have failed
M1 too. The D2 verdict rests entirely on the r limb, which separates the two
sides cleanly (0.9919 vs 0.9726 against a 0.99 gate).

**What the instability *is*, physically.** It is not noise; it is a monotone
drift with the fleet build-out. The discharge shape migrates *later and
flatter* as the fleet grows: hod 22 share 0.032 → 0.049 → 0.071, hod 23
0.014 → 0.018 → 0.040, hod 0 0.009 → 0.009 → 0.015, while the evening block
falls 0.807 → 0.780 → 0.734. A 3.5× charge fleet held its shape; the discharge
shape does not. That is exactly the "year-specific outcome, not a conduct
statistic" the gate was written to catch — and it means the latest-year-carry
forward story (the caiso-99/104 precedent this ask leaned on) is not supported
on this side.

## §3 — D3: the BINDING PRE-CHECK **FAILS**, and this is the load-bearing refutation

Run for information after D2's kill (it authorizes nothing) because it decides
whether a *repaired-shape* variant would be worth chartering. It would not.
Computed against the keeper's own committed hourly `li_ion` P1 discharge
surface — never a replay.

| year | floor shortfall | days with a binding hour | keeper overnight(0-6) | residual overnight **ALLOWANCE** |
|---|---|---|---|---|
| 2023 | 0.561 TWh (13.8 %) | 0.956 | 150 MW/h | **431 MW/h (2.87× free)** |
| 2024 | 1.125 (14.8 %) | 0.997 | 159 MW/h | **817 MW/h (5.15× free)** |
| 2025 | 1.483 (12.9 %) | 1.000 | 394 MW/h | **1 356 MW/h (3.45× free)** |

Three independent facts, each sufficient on its own:

**(a) The construction can never bind on the overnight — and this is
scale-invariant.** Both quantities are fractions of the day total `D[d]`:
the allowance is `D × (1 − da_frac_dis × s_non_overnight)` = **0.271 / 0.274 /
0.302 × D**, against a keeper overnight position of **0.094 / 0.053 / 0.088 ×
D**. The ratio holds for *any* `D` the LP would re-optimize to, so the
refutation does not depend on the keeper's own volume. To make the allowance
merely *equal* the keeper's own overnight discharge, `da_frac_dis` would have
to be **0.989 / 1.045 / 1.018** — arithmetically impossible in two of three
years, against a measured 0.778–0.802.

**(b) The overnight limb pushes the defect the WRONG WAY.** The measured
shape puts 9–11 % of discharge in hod 0–6, so the floor *forces* overnight
discharge: it binds on **59–77 % of days at hod 0, 5 and 6**, adding
**+65 / +146 / +192 MW/h** of extra overnight discharge — against a defect
that needs **151 / 99 / 98 MW removed**. In 2024 and 2025 the mechanism's own
overnight limb is roughly 1.5–2× the size of the defect, in the opposite
direction.

**(c) The general form of the refutation — a floor can only ADD.** The M1
construction is a lower bound on an hour's fleet volume. The defect
FINDING-caiso127 §3 identified is an **over**-position in the overnight. No
floor, on any shape, can remove volume from an hour. The intended channel was
indirect (bind the evening ⇒ the SOC budget starves the overnight), but (a)
shows the overnight allowance is 2.9–5.2× the position for any day total, so
the budget never tightens enough to reach it. **This kills the
allocation-floor family for this defect, not merely this shape** — including
an evening-only-scoped variant, since the allowance in (a) counts only the
non-overnight floors and is therefore *unchanged* by dropping the overnight
limb.

## §4 — D4 (not reached)

Not evaluated as a gate — D2 and D3 both killed the family first. For the
record the property it tests does hold by construction (`Σ_hod
alloc_share_dis = 1`, so the day-total floor is `da_frac_dis × D[d]` and
`D[d] = 0` stays feasible); it was never the binding question.

## §5 — what this closes, and what it leaves standing

- **CLOSED — S1 as filed.** The DA/RT allocation on the discharge side is
  refuted at the derive gates. Do not re-file it with a re-derived shape, a
  different support threshold, a different window scoping, or a raised
  `da_frac_dis`: §3(a) is scale-invariant and §3(c) is a property of the
  floor form itself. Raising `da_frac_dis` to the ~1.0 that would be required
  is a fitted value, not a measured one (rule 13 `[R-MEASURED]`, rule 24
  `[R-DOF]`).
- **CLOSED — the whole allocation-floor family against this defect.** Per
  §3(c). An instrument that only adds volume cannot fix an over-position.
- **STANDING, and now the sharpest open question:** the defect itself is
  unchanged and still load-bearing — FINDING-caiso127 §2's storage pin
  (192/197/276 of 365 days) is still the whole compression, and it is still
  the prerequisite gating every evening-scoped supply-side candidate.
- **What the kill teaches about the candidate space.** The surviving
  instruments must be able to *remove* overnight discharge, i.e. an **upper**
  bound or a **price** on the overnight position, not a floor. The ask's own
  §4 already refuted the price instruments on volume grounds
  (`battery_dispatch_adder`, caiso-100/101) and the power/SOC upper bounds on
  slackness grounds (the AS family, caiso-74; the caiso-99 p95 cap, which the
  model uses only 5–11 % of). Every *shaped* instrument in the space is now
  refuted from one side or the other. That is the honest state: **candidate
  S2 (the DA/RT two-settlement separation — the LP's single-market
  perfect-foresight arbitrage itself) is the remaining diagnosis**, exactly as
  the ask §4 anticipated as its fallback, and per that memo it is a structural
  change of a different size that must be **chartered separately**, not
  approximated by a shaped floor.

## §6 — DO-NOT-REDO (new, binding)

Re-filing S1 in any shaped-floor form (re-derived shape, altered
`SUPPORT_MIN_SHARE`, evening-only scoping, raised `da_frac_dis`); re-measuring
the discharge-side allocation statistic or its cross-year stability (§1/§2
carry it, and the charge-side control with it); re-checking whether an
allocation FLOOR can reduce an overnight over-position (§3(c) — it cannot, by
form); treating the D2 CV limb as discriminating between the two sides (§2 —
the charge side fails it too); regenerating
`data/raw/reference/caiso-charge-allocation-profile.csv` with discharge
columns (no consumer, dead mechanism).

Carried forward unchanged: everything in FINDING-caiso127 §7 and
FINDING-caiso128's DO-NOT-REDO.

## §7 — status of the rest of the caiso-127 grant

Untouched by this session, exactly as granted: the **caiso-114 refinement**
stays unfunded as a first delta; **`hydro_budget_nameplate_aware`** still
arms only in its OWN single-delta A/B; **pumped storage** remains flagged not
built (no shape restraint of any kind, +58/+85/+89 MW of the overnight
excess). Promotion was not granted and nothing here changes the keeper.
