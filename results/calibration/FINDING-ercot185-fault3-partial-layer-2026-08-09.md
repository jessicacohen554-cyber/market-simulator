# FINDING — ercot-185: the fault-3 partial-layer construction repair

> **STATUS: PRE-SOLVE RECORD, A/B IN FLIGHT (committed at the solve boundary).**
> Everything below §1–§5 is **measured and final**: the construction, the seam
> proofs, the pre-solve screen and the DO-NOT-REDO measurements all ran BEFORE
> the solve and are not revisited. **No gate that requires the solved pair is
> adjudicated yet** — G-SPAN, G-SHED, G-SPUR, G-C3c, G-COAL148, G-D2, G-OWNER
> and LOYO are **NOT REACHED** at this revision, and no run is registered. The
> A/B verdict section is appended when the pair completes; if the session ends
> first, this file stands as the pre-solve record and nothing in it claims an
> outcome it does not have.

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

## 3. A CORRECTION to my own pre-measurement reasoning (variant RAW)

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

## 4. Disclosed: a pre-existing breakage at HEAD that blocked every solve

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

## 5. Governance

* **Rule 15 `[R-DASHBOARD]` / 16 `[R-ALLYEARS]`** — the A/B pair solves all
  three years in ONE invocation and ONE bundle each. **Not yet registered at
  this revision** (the pair is in flight); both runs are registered whatever the
  outcome, keeper or rejected, in this session.
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
