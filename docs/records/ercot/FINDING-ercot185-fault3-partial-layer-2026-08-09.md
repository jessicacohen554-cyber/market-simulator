# FINDING — ercot-185: the fault-3 partial-layer construction repair

> **STATUS: COMPLETE. A/B SOLVED, BOTH RUNS REGISTERED, ARM PROMOTED TO KEEPER.**
> Pre-registered mechanical verdict: **REJECTED-AS-ARMED** (G-SHED, G-C3c fail). That verdict stands
> and is not re-scored. The arm was **PROMOTED OVER IT** under the owner's standing structural standard,
> given in-session 2026-08-09: *"if structural integrity improves but gates regress that may still be a
> keeper."* Keeper: `2026-08-09-ercot185-shaped-partial` (was `2026-08-09-run181-position-tail`).

**Session ercot-185, 2026-08-09.** Charter: the SIGNED owner ruling of the
2026-08-09 sitting, card D2 option C — *"The ceiling lane stays frozen for
composition-rule work; a fault-3 partial-layer construction re-charter is
authorized as its successor, with G-COAL148 carried live."* Decision rules, the
construction, the DO-NOT-REDO check, the seam proofs, a binding pre-solve screen
and the kill gates were pre-registered and pushed **before any measurement or
derive**
(`docs/PRECOMMIT-ercot185-fault3-partial-layer-construction-2026-08-09.md`);
the gates are `PRECOMMIT-ercot172` §5 inherited verbatim with **G-COAL148
carried live** per the ruling. Keeper at session start:
`2026-08-09-run181-position-tail`, **NOT-YET {C3a, C3b}**.

## 1. What was built, and why it is not any of the three dead arms

`FINDING-ercot174` §3b item 3 named ercot-172 fault 3 — *a multi-week flat
plateau used as an hourly ceiling* — as **the only remaining structural route to
the 2024 object**, untouched by any composition rule. This session attacks it,
and **only** it.

**The defect at code grain.** `scripts/lib/outage_detect.py::_detect` emits one
`derate_factor = median(dmax[i:j]) / ref` per plateau and
`partial_outage_derate_factors` expands it flat across every hour of the window.
W A Parish carries a single `0.363` spanning 2024-03-04 → 05-04, so h2827
(2024-04-28 19:00) is capped at 0.36 against the plant's own same-hour
fuel-matched CEMS of **0.7843**.

**The construction** (`ercot_partial_outage_shaped_derate`, default off, one
gate, **zero new scalars**). Same plateaus, same day spans, same covered hours;
the flat factor becomes a day-resolved profile

```
shaped(d) = clip( f0 × sm[d] / median(sm[i:j]),  0, 1 )
```

with `f0` the incumbent's own emitted factor and `sm` the detector's own centered
`_SMOOTH_DAYS` rolling median of daily-max CF — **the exact series the detector
already thresholds on to decide plateau membership**. `f0` and `sm` are medians
of the SAME daily-maximum series differing only in the median's window, so this
is a **grain refinement in time** of one measured statistic: the temporal
analogue of ercot-174's unit-grain refinement, which was proved grain-only by
BE-1/2/3. `_MIN_DAYS`, `_SMOOTH_DAYS`, `_CEILING_FRAC`, `_RUN_FLOOR_CF` and
`ref` are imported verbatim and never re-valued (rule 23 `[R-FROZEN-DERIVE]`);
the rule-23 **trigger** is the signed ruling plus the ercot-172 measurement,
never a residual, and the derive commit cites it.

**Why it is categorically not the rejected family.** Every composition arm is
**restore-only** (ercot-174 SP-5: `product ≤ unit-scoped ≤ min` pointwise). Here
scaling commutes with the median, so `median(shaped[i:j]) = f0` **exactly** — a
provable **pure re-shaping**, never a net lift or cut. It is a change to how ONE
layer is *constructed*; the `f_window × f_partial` composition is untouched and
**ERCOT-148/149 is not repealed**.

**Why CEMS-shaped and not duration-scoped** (the charter's other candidate):
shortening or splitting windows would **restrict the event-window population**
and reach **G-NEUT** (the ercot-171 gate). Re-shaping restricts no population, so
G-NEUT is not reached — exactly as it was not reached for C1/C2.

## 2. Seam proofs and the pre-solve screen — all measured BEFORE the solve

Record: `results/calibration/ercot185_shaped_seam_proof.json`; probe
`scripts/probes/ercot185_shaped_seam_proof.py`; SP-2/SP-6 additionally asserted
**inside the deriver** (stop-the-line, the ercot-174 BE-3 precedent).

| proof | result |
|---|---|
| **SP-0** unmodified deriver reproduces the committed extract | **PASS** — sha256 `8d6f049e…c736b5`, the ercot-174 BE-1 hash |
| **SP-1** plant-grain file written alongside the shaped emission | **PASS** — same sha256 |
| **SP-2** 501 plateaus tile exactly (deriver assertion) | **PASS** |
| **SP-2L** identical covered-hour sets AFTER `outage_hour_mask` | **PASS** — 0 mismatched plants, all three years |
| **SP-3** gate at default reproduces the incumbent factors | **PASS** |
| **SP-4** movement confined to plateau hours | **PASS** |
| **SP-5/SP-6** profile is the stated construction, median-preserving | **PASS** — max median deviation **0.0005** |

**P-2 two-sidedness — the pre-registered discriminator, and it is decisive.**

| year | changed plant-hours | above incumbent | below incumbent |
|---|---|---|---|
| 2023 | 18,455 | **49.8 %** | 50.2 % |
| 2024 | 24,166 | **51.1 %** | 48.9 % |
| 2025 | 20,781 | **50.8 %** | 49.2 % |

Against the **100 %-above** signature of every composition arm. The
median-preservation property showing up empirically.

**ρ_shaped — the DO-NOT-REDO measurement (rule 28a).** Share of the REJECTED
ercot-173 blanket arm's coal ceiling lift that this repair reproduces:
**0.125 / 0.085 / 0.042** (2023/24/25) — against ercot-174's unit-scoped
**0.938 / 0.959 / 0.961**. The unit-scoped arm *was* the rejected arm; this one
reproduces **4–13 %** of it. The separation is not marginal.

**P-3 — the ercot-172 object moves.** W A Parish (3470) at h2827:
incumbent **0.363 → shaped 0.578**, against the pre-registered bar **0.50** and
the plant's same-hour CEMS-implied **0.7843**. **PASS** — the repair closes
**59 %** of the gap the composition family could not touch at all.

**§5 BOUND — the binding pre-solve screen.** The coal ceiling-**lift energy**
hard-bounds G-COAL148's own quantity with no LP (the cap enforces
`availability ≤ ceiling`, and the control's above-ceiling energy is ≥ 0, so
`rise ≤ arm_above ≤ BOUND`):

| year | BOUND (TWh) | cut side (TWh) | pre-registered verdict |
|---|---|---|---|
| 2023 | **0.5255** | 0.2150 | 0.5 < B < 2.0 ⇒ **SOLVE** |
| 2024 | **0.4715** | 0.2575 | ≤ 0.5 ⇒ **G-COAL148 PASSES BY CONSTRUCTION** |
| 2025 | **0.2165** | 0.1607 | ≤ 0.5 ⇒ **G-COAL148 PASSES BY CONSTRUCTION** |

No year reaches the 2.0 TWh stop bar (the rejected arm realized
+0.98/+1.95/+2.73 TWh). 2023 lands in the pre-registered middle band, so the
solved pair adjudicates it — **the rule was applied as written, not relaxed
because 0.5255 is close to 0.5**.

## 3. THE SOLVED A/B — result, gates, and the verdict

Runs: **`2026-08-09-ercot185-shaped-control`** (gate at default) and
**`2026-08-09-ercot185-shaped-partial`** (armed), a same-HEAD pair, all three
years in one bundle each, both registered (rules 15/16). Retention evicted
exactly the two runs named in the precommit §9 —
`2026-08-04-ercot165-unpooled-tie` and `-unpooled-share`.

### 3a. What moved

| year | C3a | C3b (NRMSE) | model tail >$200 | spurious | shed |
|---|---|---|---|---|---|
| 2023 | −32.4 % → **−32.5 %** | 0.602 → **0.602** | 61 → 61 (actual 181) | 10 → 10 | 4 → 4 |
| 2024 | +2.7 % → **+1.4 %** | **0.205 → 0.160 (PASS)** | 25 → 23 (actual 53) | 12 → 11 | 2 → 2 |
| 2025 | −7.9 % → **−7.9 %** | 0.101 → **0.101** | 3 → 3 (actual 31) | 1 → 1 | 0 → 0 |

**C3b-2024 crosses its ≤0.20 PASS bar** (monthly load-weighted NRMSE-2024
3.007 → 2.794 on the analyzer basis). ERCOT's failing set narrows from
{C3a-2023, C3b-2023, C3b-2024} to **{C3a-2023, C3b-2023}**. 2023 and 2025 are
inert, which is exactly the chartered target ("without disturbing 2023 or
2025"). **The determination is NOT-YET either way** — the promotion buys
structural fidelity and one criterion-year, not a better public claim.

### 3b. The gates — 7 PASS, 2 FAIL

| gate | verdict | detail |
|---|---|---|
| G-BIT | **N/A** | declared pre-solve (year-agnostic rule) ⇒ G-SPAN applies |
| **G-SPAN** | **PASS** | zero class-energy violations in 2023/2025; shed and C3c tails unmoved there |
| **G-SHED** | **FAIL** | 2024 had to FALL; stayed **2 → 2**. No year rose, so the protective half holds |
| **G-SPUR** | **PASS** | 10→10, 12→11, 1→1 |
| **G-C3c** | **FAIL** | 2024 model tail **25 → 23** vs actual 53 — 2 h further away. 2023/2025 unmoved |
| **G-COAL148** | **PASS** | rise **+0.124 / +0.182 / +0.110 TWh** vs the +0.5 bar — the rejected blanket arm failed at +0.98/+1.95/+2.73 |
| **G-DOF** | **PASS** | zero new fitted scalars; DOF ledger carried verbatim |
| **G-D2** | **PASS** | D-2 over-budget zero in both; D-4 FAIL rows identical A↔B (pre-existing CT_PEAKER condition) |
| **G-OWNER** | **PASS** | C3a-2024/2025 keep PASS; C3a-2025 −7.9 %, well inside the −9.1 % bound |
| **LOYO** | **N/A** | parameter-free rule; per-year deltas above stand in its place (ercot-173 precedent). The gain is 2024-only and no year degrades materially — no in-sample gain bought with held-out degradation |

**Two gates fail, so the pre-registered verdict is REJECTED-AS-ARMED.** It is
reported at full magnitude and not renegotiated.

### 3c. The structural result — the two faults are now separated on measurement

**The arm still sheds at exactly h2827 and h3067**, the ercot-172 object hours.
That is not a null result, it is the answer to the question the lane has been
asking since ercot-172. The repair lifts W A Parish's *partial* factor
**0.363 → 0.578** at h2827 — but the ceiling the LP sees is the **product**:

```
f_window × f_partial  =  0.6995 × 0.578  =  0.404      vs same-hour CEMS 0.7843
```

So after fault 3 is repaired, the plant is **still** held at 0.40 of a
capability its own CEMS record puts at 0.78 — and the whole of that remaining
gap is **fault 1, the double-count**, which this charter explicitly fences off.

This **refutes G-SHED's founding hypothesis** — that fault 3 alone drives the
fabricated 2024 shortage — rather than showing a regression: the gate was
written at ercot-172 when the two faults could not yet be told apart. They can
now.

**What that unblocks (measured here, NOT taken here).** With the repaired layer
armed, G-COAL148 consumes only **0.182 of its 0.5 TWh** headroom. That is the
first measured evidence for `DECISION-MEMO` §5's central claim — that removing
the double-count *against a repaired partial layer* may no longer flood
2023/2025, so the ERCOT-148/149 protection and the double-count removal could
finally coexist. **That removal is a separate later adjudication.**
ERCOT-148/149 stays armed and unrepealed, exactly as the ruling requires.

### 3d. Why it is a keeper, and on whose authority

The pre-registered verdict is REJECTED-AS-ARMED. The **promotion rests on the
owner's standing structural standard**, given in-session on 2026-08-09: *"if
structural integrity improves but gates regress that may still be a keeper."*
Applied here:

* It **deletes a mechanism that is measurably wrong** — a multi-week average
  imposed as an hourly ceiling, which forbids output the plant's own CEMS record
  shows it produced — and replaces it with the *same measured statistic at the
  finer grain*. Rule 1 `[R-STRUCT]` and rule 14 `[R-ACCURATE]` both point one way.
* **Zero DOF.** Nothing here can be tuned.
* The residual mostly **improves anyway**: one determination-relevant
  criterion-year crosses its bar, and nothing material degrades.
* Neither failure is a structural regression: G-SHED is a refuted hypothesis
  (nothing got worse), G-C3c is a 2-hour move on the already-ledgered
  model-class caveat.

## 4. A CORRECTION to my own pre-measurement reasoning (variant RAW)

The precommit's amendment A-1 argued RAW (`min(1, sm[d]/ref)`) shifts the
plateau level **in the restrictive direction**. Measured, the sign is the
**opposite**: RAW's mean signed level shift on plateau hours is
**+0.0148 / +0.0009 / +0.0036** and its coal lift is **0.6144 / 0.5188 / 0.2640
TWh** — *higher* than NORMALIZED in every year, i.e. RAW is a net **lift**.

The substantive conclusion is unchanged and is now measured rather than
argued: **RAW changes the plateau's LEVEL as well as its shape**, confounding
the fault-3 shape repair with an unlegislated level move (rule 19
`[R-ONE-MECH]`), which is why it is reported-only and NORMALIZED is the arm.
The directional claim in A-1 was wrong and is corrected here rather than left
standing.

## 5. Disclosed: a pre-existing breakage at HEAD that blocked every solve

The session's first replay failed before reaching the LP:

```
TypeError: run_year() got an unexpected keyword argument 'cc_winter_capability_basis'
```

`run_calibration_full.solve_and_persist` has forwarded
`cc_winter_capability_basis` to `run_year` since the caiso-186 merge, but the
parameter was never added to `run_calibration.run_year`. Reproduced at
`51d4e98e` (this branch's base, an ancestor of main) on an unmodified tree;
ercot-185's own diff touches neither driver. **This blocked every ISO's
calibration path on main, not just this session's.** Repaired by mirroring the
sibling tri-state pattern verbatim, and the whole seam was audited rather than
just the symptom: all **255** kwargs `solve_and_persist` forwards now resolve
against `run_year`'s signature, with no other gaps. Surfaced here because it is
a cross-lane regression other sessions will hit.

## 6. Governance

* **Rule 15 `[R-DASHBOARD]` / 16 `[R-ALLYEARS]`** — both runs registered on the
  dashboard in this session, all three years in ONE invocation and ONE bundle
  each; the rejected-as-armed control is registered alongside the keeper.
  Retention evicted the two runs named in the precommit, and no others.
* **Rule 22 `[R-HOLDOUT]`** — 2023–2025 only. ERCOT holds no `complete` and no
  `final` marker; no out-of-training year was solved, scored or read. The derive
  spans the extract's own committed 2018–2026 as **data prep**, which the
  2026-08-06 amendment places outside the spend gate.
* **Rule 23 `[R-FROZEN-DERIVE]`** — trigger cited in the derive commit; no
  identification constant re-valued; the flat extract is byte-unchanged.
* **Rule 24 `[R-REGISTRY]`** — one registered `ScenarioConfig` field,
  cache-key-dropped at its default, recorded in both bundles' `run_config.json`.
* **Rule 25 `[R-ISO-SCOPE]`** — ERCOT-scoped throughout.
* **Rule 27 `[R-PUSH]`** — every push touching a ≥300-line file blob-verified
  against the **remote** before the next commit.
* **Rule 28 `[R-MECH-MATRIX]`** — the field's matrix row landed in the same PR
  as the field (duty c) and carries this session's verdict (duty b). The
  `--fix-anchors` repair of 229 anchors this session's own line shift caused is
  proved **digits-only** by normalising every number on both sides.

**DO-NOT-REDO honoured in full** — no composition rule touched (blanket `min()`
stays **R**, unit-scoped stays default-off with its record, finer-grain-wins
stays unbuilt); ERCOT-148/149 not repealed; ercot-172's C3 outcome-pin not
attempted; no coal offer lane, no depth lever, no storage offer surface, no
aggregate or per-hour telemetered-HSL cap; West/Panhandle topology stayed
closed; `ercot_storage_rt_offer_surface` stays **R**; the CC-headroom crosswalk
stays FILED-UNLICENSED; no rule-18 grain work (that is D3, sequenced after this).
