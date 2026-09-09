# PREREG miso-248 — **Re-derive MISO's SPP seam ladder on the clock `86e45462` repaired.** Rule 23 `[R-FROZEN-DERIVE]` is the licence, the cited data change is the trigger, and **rule 29 `[R-SCREEN]` is owed in full**

**Pushed BEFORE any adjudicating quantity exists**, with the phase-0 probe
`scripts/probes/_miso248_spp_rederive_phase0.py`, per the handoff's binding process clause.
Every decision rule, materiality floor, gate bar and selection rule below is fixed **here**, before
the number it governs is computed.

**KEEPER (incumbent, unchanged by this document): `2026-09-09-miso-247-p19-posture`**, bundle
`results/calibration/miso247_fullspan_K`, DETERMINATION **CALIBRATED**, C3c the single ledgered
caveat, DOF **41/2**. **Rule 22 `[R-HOLDOUT]`: 2023–2025 ONLY.** MISO holds no `complete` marker;
**none is sought, inferred or granted here**, and no out-of-training year will be solved, scored or
registered.

**Queue item taken (rule 28(a)): the handoff's RECOMMENDED item 1.**

---

## 1. THE OBJECT — and a **CORRECTION TO THE HANDOFF'S NAMING** that is declared before it is tested

The handoff names the object *"`MISO_SEAM_LADDER_BY_YEAR`'s SPP ENTRIES"*. **Reading the code
BEFORE any measurement, that is not the table the failing pin tests, and it is not the table the
repaired series can reach:**

| table | derived against | reached by `86e45462`? | live on the keeper? |
|---|---|---|---|
| `MISO_SEAM_LADDER_BY_YEAR["…"]["SPP"]` | MISO hub DA × EIA-930 seam flow (`derive`) | **NO — it never reads an SPP price** | **NO** — displaced by the hourly overlay |
| **`MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR`** | **`spread = MISO hub DA − SPP NORTH hub DA`** (`derive_spp_neighbour_hourly`) | **YES** | **YES** (`miso_seam_neighbour_hourly_spp = True`) |

`86e45462` rewrote **both** `actual_lmp_hourly_SPP.parquet` (the file the predecessor's addendum
names) **and** `actual_lmp_hourly_zonal_SPP.parquet` — and it is the **zonal** file that
`derive_miso_seam_ladders.load_spp_hub_da` and the solve-time anchor
`eia_loader.measured_miso_spp_hub_prices` both read. The failing pin is
`TestHourlySppOverlay::test_registry_reproduces_the_frozen_derivation`, which pins the **hourly
overlay**. So the substance of the handoff's citation is right and its table name is not.

**`P-1` DECISION RULE, fixed here.** The probe re-derives **every** entry of
`MISO_SEAM_LADDER_BY_YEAR` (all four seams × 2 sides × 8 bands × 3 years = **192**) as well as the
hourly SPP overlay (48).
* **If the 192 reproduce at `atol=0.005`**, the handoff's named table is **out of scope**, the
  correction above stands as measured, and **only the 48 hourly SPP offsets are re-derived.**
* **If any of the 192 does not reproduce**, both tables are in scope and both are re-derived in the
  same arm.
Either way the session's exit condition is unchanged: **both pins pass with NO exceptions at
`atol=0.005`, carrying all 192 + 48 entries.**

## 2. WHAT IS NOT DONE — each is the thing the standing instruction forbids

* **`atol=0.005` is NOT widened**, in either pin.
* **`_MISO244_KNOWN_LADDER_DIVERGENCES` is NOT re-added.** It was DELETED, not zeroed, under rule 26
  `[R-DELETE]`; a deleted exception list stays deleted.
* **No test is skipped, `xfail`ed or silenced.**
* **No residual, criterion, band or actual appears in any bar in this document.** The trigger is the
  cited source-data change `86e45462` and rule 23 alone. **ZERO free parameters:** the estimator,
  the depth grid, the anchor hub (`SPPNORTH_HUB`, named on topology at miso-233) and the no-wash
  reconciliation are all unchanged; only the input series moved.

## 3. THE STRUCTURAL FACT THIS SESSION EXPECTS TO ESTABLISH — **stated as a hypothesis with a refuting rule, not as a finding**

The solve-time anchor `measured_miso_spp_hub_prices` reads the **same** parquet `86e45462`
rewrote, and it is **ungated data** — no `ScenarioConfig` field, no cache-key entry. The keeper's
committed offsets were derived against the **pre-repair** series. If so, then at HEAD the applied
SPP band offer `hub(t) + δ_k` is a **MIXTURE** — a repaired-clock anchor carrying pre-repair-clock
offsets — and the keeper is already unreproducible at HEAD on this seam, exactly as it was on
`_apply_simple_cycle_hr_floor` at miso-247. **This makes the re-derive a repair of a HALF-APPLIED
change rather than a discretionary lever.**

**`P-2` DECISION RULE, fixed here.** The probe reads the hub series at HEAD and at the keeper's own
basis `f29b7ab0` (`git show <sha>:<path>`) and reports hours moved, `max |Δ|`, and whether the
sorted value multiset is preserved (a pure re-index).
* **If the two series are IDENTICAL, the premise above is FALSIFIED**: the session **STOPS**,
  publishes that at full magnitude, makes **no** re-derive, and hands the divergence's true cause
  forward unclosed. No bar moves in either direction.

## 4. `P-3` — THE RE-DERIVE, WITH THREE STOP CONDITIONS

`derive_spp_neighbour_hourly` is run at HEAD for 2023 / 2024 / 2025 on `joined.loc[[year]]` (the
miso-243 row-count pin). **Each of the following FAILS the re-derive and is published unrepaired
rather than patched:**
1. the join changes the row count (the miso-243 invariant);
2. any year's import offsets are not weakly rising, or its export offsets not weakly falling;
3. any year's `max(export) >= min(import)` (the same-seam no-wash reconciliation).

## 5. `P-4` — THE MECHANISM'S OWN MEASURED FOOTPRINT, AND THE SCREEN-YEAR SELECTION RULE

**Declared before either is computed. The statistic is the mechanism's own arithmetic and touches no
actual, no criterion and no residual.**

At HEAD the anchor is common to arm and control, so the mechanism's entire effect on the LP's inputs
is the hour-constant offer shift `δ_new_k − δ_old_k` on the 16 SPP band rows. Those offsets reach the
LP **only** through whether a band clears. So:

> **`F(year)` = Σ over the 16 SPP bands of `cap_band × #{t : clear_old(k,t) ≠ clear_new(k,t)}`**, in
> MWh, where `cap_band = interface_limit(SPP) / 8` MW,
> `clear(k,t) = [p(t) > hub(t) + δ_k]` for an **import** band and `[p(t) < hub(t) + δ_k]` for an
> **export** band (the LP's own optimality convention: an import column sits at its upper bound when
> `mc < price`, an export column at its lower bound when `mc > price`),
> `p(t)` = **the keeper's own committed P1 price at `MISO_external`** (`hourly/system_<year>.parquet`),
> `hub(t)` = `measured_miso_spp_hub_prices("MISO", year, 8760)` **at HEAD**.

**SELECTION RULE.** The screen year is **`argmax_year F(year)`**. If the top two are within **1 %**
of each other, the tie is broken by the larger `max_k |δ_new,k − δ_old,k|`; if still tied, by the
**earliest** year. **The residual plays no part, and the year with the largest residual is not
consulted.**

**DECLARED POWER, against interest.** `F` is computed on the keeper's *frozen* internal price. The LP
will re-price in response, so `F` is a **first-order** footprint, not a forecast of the response. It
is used **only** to pick where the mechanism is largest — which is exactly what rule 29 asks of it —
and for nothing else.

## 6. `P-5` — THE PRE-SOLVE PREDICTION THE SCREEN GATE TESTS

On the same frozen-price construction, the predicted change in the **SPP seam's net import energy**:

> `ΔE_pred(year) = Σ_{import k} cap × (n_new − n_old) − Σ_{export k} cap × (n_new − n_old)`, TWh,
> `n` = hours the band clears.

Reported for all three years; the screen year's value is the operand of `G-1`.

## 7. THE SCREEN GATES — **STRUCTURAL, STOP-ONLY, and gated on the mechanism's own arithmetic, never on a residual**

Solved on the **screen year alone**, as an **arm** (re-derived offsets) and a **control** (HEAD,
committed offsets) — see §8 for why a control is earned.

* **`G-1` — direction and order of magnitude.** Realised `Δ(SPP seam net import energy)` = arm −
  control, measured from each bundle's own `hourly/unit_hourly_<year>.parquet` over the rows whose
  `unit_id` carries the SPP reference-import / reference-export mark.
  * **Form A**, if `|ΔE_pred| ≥ 0.05 TWh`: PASS iff the realised delta has the **same sign** as
    `ΔE_pred` **and** `|realised| / |ΔE_pred| ∈ [1/3, 3]`.
  * **Form B**, if `|ΔE_pred| < 0.05 TWh` (the mechanism measures near-inert): PASS iff
    `|realised| ≤ 0.15 TWh` — i.e. an inert prediction must produce an inert response.
  * The `[1/3, 3]` band is the one this lane has used since miso-243 and is **not** re-set here.
  * **Fallback, declared now with its reduced power:** if a bundle carries no `unit_hourly`, `G-1`
    falls back to the **aggregate** `import` class of `hourly/class_hourly_<year>.parquet`, which
    pools all four seams and therefore **cannot separate the SPP response from the other seams'
    re-clearing**. The fallback's use, if it fires, is reported in the headline.
* **`G-2` — confinement, proved at ZERO LP.** Running the injector at HEAD with the old and the new
  registry on the same fleet, the two `mc` matrices differ **only** on rows tagged `SPP`, and on
  those rows by **exactly** `δ_new_k − δ_old_k`, hour-constant. Any other differing row FAILS.
* **`G-3` — the applied identity holds in the SOLVED year.** In the arm's own `unit_hourly`, every
  SPP band row satisfies `mc[row, t] == hub(t) + δ_new,k` to `atol = 0.01 $/MWh` in **every** hour;
  in the control, `mc[row, t] == hub(t) + δ_old,k` on the same bar. A single violating hour FAILS.
* **`G-4` — collateral.** `scripts/screen_collateral_gate.py --bundle <arm>
  --keeper-run-id 2026-09-09-miso-247-p19-posture --years <screen year>`. PASS iff **zero**
  load-bearing criterion flips PASS → FAIL. Band moves in either direction are **reported, not
  gated** (rule 1 `[R-STRUCT]`).

**The screen may KILL the arm; it may NEVER promote one.** A clear does not authorise the full span
by itself: the full span is spent on rules 23 / 14 and the structural argument of §3, and — if the
`P-2` premise is falsified — it is not spent at all.

**IF A GATE FAILS AND WAS SATISFIABLE, IT IS A RESULT AND NOT A BROKEN GATE.** It is published
first, at full magnitude, **no bar is moved**, and no re-scoping is done. This lane left `G-1`
standing at 3.279× one session ago and does the same here.

## 8. `G-DRIFT` — rule 29(b), re-run from the NEW keeper's own sha

`git diff f29b7ab0 HEAD -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py
scripts/lib data/raw/_validation-source data/raw/reference`, every hunk classified INERT (with a
cited reason) or LIVE. **The expectation, stated in advance so it cannot be written to fit:
`86e45462` is itself a LIVE hunk** — it moves the solve-time SPP anchor — **so form 4 is falsified
and a control solve is EARNED**, on the screen year only. `_apply_simple_cycle_hr_floor` is **not**
a drift hunk against this keeper (miso-247 solved with it live); that changes nothing, because one
LIVE hunk is enough.

The audit is recorded **before** the arm is solved. Its by-product is the session's attribution:
`arm − control` isolates the **offset re-derive**, `control − keeper` isolates the **anchor clock
repair** the keeper could not carry.

## 9. RULE 31 `[R-RETAIN]` AND THE FULL SPAN

* **No solved bundle is deleted.** Screen, control and any full-span bundle are retained on local
  disk (gitignored / scratchpad, never `rm`), and **the promotion question is surfaced explicitly in
  the final report**, with the statement that the bundles do not survive the session.
* **Full span, if reached: `--year 2023 2024 2025` in ONE invocation and ONE bundle** (rule 16
  `[R-ALLYEARS]`). The screen bundle is a throwaway diagnostic probe, never registered, never
  quoted as a keeper number, and its year is re-solved inside the full bundle.
* Rule 12 `[R-PARALLEL]`: years sequential within every invocation.

## 10. NON-CLAIMS, fixed in advance

1. **No rubric failure is being tuned for**, and no criterion is a target in any direction. C3c is
   untouched.
2. **No marker is sought, inferred or granted**; 2022 is not solved.
3. **Zero free parameters.** No `ScenarioConfig` field is created; no offer, adder, offset or
   multiplier is touched.
4. **The handoff's table name is corrected on the code, before any measurement** (§1), and the
   correction is reported whether or not it favours this session.
5. **A number that agrees with a predecessor's is EXPECTED, not corroboration**, wherever the two
   read the same committed artifact.
