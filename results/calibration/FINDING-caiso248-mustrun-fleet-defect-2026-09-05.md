# FINDING — caiso-248: STOP-THE-LINE. caiso-247's fleet rebuild carried **184 phantom biomass LP units the scored solve does not have** — `inject_biomass_mustrun` is derived from `solve_and_persist`'s locals, is never recorded in `meta.json`, and is therefore invisible to BOTH `run_year_kwargs` and `run_year_unreachable`. **caiso-247's third headline result (BIOMASS) is WITHDRAWN**: DOM_OTHER falls from 18.1 % / 18.0 % of the gap to **2.6 % / 1.0 %**. **Results 1 and 2 — the HUB ACQUITTAL and the caiso-202 §C confirmation — are BIT-IDENTICAL and stand.** The instrument is repaired in `replay_keeper` for every ISO. ZERO SOLVES.

**Session caiso-248, 2026-09-05.** Branch
`claude/caiso-backcast-calibration-247-zxaba3` off `main` `c234d4da`. Keeper
**`2026-09-05-caiso-246-b1-spot`** unchanged, NOT-YET, C3a +3.9 / +12.3 /
+11.4 %. **Nothing armed; no field, no flag, no solve, no promotion.** This
session opened on the caiso-248 handoff's ranked item A (the biomass offer
surface) and stopped at the first check: **the object does not exist.**

---

## §1 — THE DEFECT

`scripts/run_calibration_full.py` nets the residual must-run classes
(`_INJECTED_MUSTRUN_CLASSES = ("biomass", "OTHER")`) out of demand, re-adds
them as pseudo-units from measured EIA-923 energy, and sets

```
inject_biomass = "biomass" in must_run        # L5242, from LOCALS
... run_year(..., inject_biomass_mustrun=inject_biomass)   # L5438
```

`run_year` passes it straight to the fleet assembly as
`drop_biomass_units=inject_biomass_mustrun` (`run_calibration.py` L3292),
which **removes the raw biomass LP units so biomass is not served twice** —
and that line sits well before the `fleet_only` exit (L4999), so it governs a
fleet-only rebuild too.

**It is never recorded in `meta.json`.** `replay_keeper` says so itself:

> `inject_biomass_mustrun` and `must_run_mw` are also renamed in that call, but
> from LOCALS `solve_and_persist` derives itself — not recorded kwargs — so
> they are plumbing, not recipe

So it is invisible to `run_year_kwargs` (nothing to map) **and** to
`run_year_unreachable` (which can only report keys the bundle *records*). A
fleet-only rebuild therefore silently keeps 184 CAISO biomass LP units —
847.3 MW at a near-flat mc median $31.13 — that the scored solve does not
contain. Their offers price-matched λ and absorbed 18 % of the C3a gap into
caiso-247's `DOM_OTHER` cell.

**The keeper's own sidecar proves the injection**, from committed bytes:
`class_hourly_<year>.parquet`'s `biomass` klass is a **monthly step profile**
— 12 distinct levels, 11 change points — in all three years (2025: 3.2329 TWh,
Jan 365.87 MW … Dec 357.62 MW, std 0.0000 inside every month).

**caiso-202 §C had it right and said so**, and caiso-247 misread it:

> The full runner injects biomass as an EIA-923 monthly must-run profile and
> DROPS the raw biomass LP units … the keeper's sidecar biomass is month-flat,
> confirming it. Exclude those units from the marginal-rung candidates — **they
> never clear the merit order in the scored solve.**

caiso-247 §1 claimed caiso-202 "folded it into unmatched". It did not. It
**excluded it deliberately, for the correct reason.** That sentence is
withdrawn.

---

## §2 — THE CORRECTED DECOMPOSITION

Re-run with the fleet the scored solve actually dispatched
(`_caiso247_residual_regime_anatomy.json`, regenerated). All five gates still
pass; G-BENCH, G-RECON, G-GAP and the month totals are unchanged (they never
depended on the domestic fleet).

| 2025, gap $3.151/MWh | weight | gap $ | share **was → is** | CR **was → is** |
|---|--:|--:|--:|--:|
| HUB_FITTED | 0.7 % | +0.050 | 1.6 % → **1.6 %** | 2.18 → **2.18** |
| HUB_MEASURED | 4.9 % | +0.065 | 2.1 % → **2.1 %** | 0.42 → **0.42** |
| DOM_GAS | 52.4 % | +1.267 | 40.2 % → **40.2 %** | 0.77 → **0.77** |
| **DOM_OTHER** | **0.7 %** | **+0.031** | 18.0 % → **1.0 %** | 2.49 → **1.41** |
| **STORAGE** | **37.4 %** | **+1.678** | 36.5 % → **53.3 %** | 1.17 → **1.43** |
| UNRESOLVED | 3.8 % | +0.060 | 1.6 % → **1.9 %** | 0.47 → 0.50 |

| 2024, gap $3.781/MWh | weight | gap $ | share **was → is** | CR **was → is** |
|---|--:|--:|--:|--:|
| HUB_FITTED | 0.2 % | −0.004 | −0.1 % → **−0.1 %** | −0.48 → **−0.48** |
| HUB_MEASURED | 3.7 % | +0.155 | 4.1 % → **4.1 %** | 1.10 → **1.10** |
| DOM_GAS | 64.6 % | +1.781 | 47.1 % → **47.1 %** | 0.73 → **0.73** |
| **DOM_OTHER** | **1.3 %** | **+0.098** | 18.1 % → **2.6 %** | 2.60 → **1.99** |
| **STORAGE** | **26.4 %** | **+1.632** | 28.7 % → **43.2 %** | 1.33 → **1.63** |
| UNRESOLVED | 3.8 % | +0.120 | 2.1 % → **3.2 %** | 0.70 → 0.85 |

2023 (gap $1.307): DOM_OTHER 14.8 % → **6.2 %**, STORAGE 55.5 % → **63.0 %**,
HUB **unchanged at 37.8 %** (CR 3.461).

**Why the HUB numbers do not move at all.** HUB is identified from the
caiso-244 import-row complementarity plus the landing-zone reach test —
neither touches the domestic fleet. And the priority order puts DOM_GAS
*ahead* of DOM_OTHER, so removing blank-group units can only move zone-hours
from DOM_OTHER into STORAGE / UNRESOLVED. Both are exactly what the corrected
run shows, which is the internal consistency check on the repair.

**What DOM_OTHER is now:** COAL (+$7.40/MWh mean residual, 0.5 % weight),
hydro (−$4.09), nuclear (~0). A residual cell, not an object.

---

## §3 — WHAT SURVIVES, WHAT IS WITHDRAWN

**SURVIVES, unchanged to the digit:**

1. **The HUB is acquitted on the scored statistic.** CR(HUB) = **1.026 (2024) /
   0.642 (2025)**, hub carrying 4.0 % / 3.6 % of the gap on 3.9 % / 5.7 % of
   the weight; robust under DOM_GAS-first (1.188 / 0.583) and tol = 0.75
   (0.959 / 0.516). caiso-247's registered P-5 acquittal branch still fires.
2. **caiso-202 §C's ~5 % import-leg gap share is confirmed** on the positive-part
   basis: **3.6 % (2024) / 5.1 % (2025)**.
3. **The two fitted firm prices are bounded**: HUB_FITTED is 1.6 % of the 2025
   gap, concentrated in December. Item B stays a G-26 honesty item.
4. **The weight-basis disclosure** (caiso-247 §4.5): +0.804 / +0.493 / +0.788
   $/MWh, 37.9 / 11.5 / 20.0 % of the printed gap. Unchanged and still **not**
   offered as a reduction of C3a.
5. **CT_PEAKER's residual is negative** and 2023's DOM_GAS cell is −0.189 —
   the CC-hot / CT-cold split is untouched (biomass was never in DOM_GAS).

**WITHDRAWN:**

* **caiso-247 §1 result 3 (BIOMASS as a new ranked object) — entirely.** There
  are no biomass LP units in the scored solve. Biomass enters as measured
  EIA-923 energy at a monthly step profile and **cannot** set price.
* **caiso-247 §7 item 1** (biomass ranked first in the queue) — void.
* **caiso-247 §4.4's claim that STORAGE "collapses to 3.4 % at tol = 0.75"** —
  that collapse was itself partly biomass absorbing those zone-hours at the
  wide tolerance. Corrected: at tol = 0.75 STORAGE holds **8.7 % / 10.3 %** of
  weight and **18.4 % / 23.8 %** of the gap (CR 2.10 / 2.32).
* **caiso-247's characterisation of caiso-202 §C as having "folded biomass into
  unmatched"** (§1).

**The caiso-247 P-9 and P-10 verdicts are re-scored** on the corrected run:
P-9 (STORAGE 5–20 % of 2025 weight) measured 37.4 % — **still FALSIFIED, by
more.** P-10 (every regime CR in [0.6, 2.2]) — 2025 HUB_MEASURED 0.42 and
UNRESOLVED 0.50 are still outside, so **still FALSIFIED**, but the carrier it
named is gone: the corrected outlier set contains no object, only the
unattributed bucket.

---

## §4 — THE INSTRUMENT REPAIR (every ISO, not just CAISO)

`scripts/replay_keeper.py` gains:

* **`DERIVED_RUN_YEAR_INPUTS`** — the documented list of `run_year` inputs
  `solve_and_persist` derives from its own locals, which the bundle never
  records and neither existing helper can see;
* **`derived_run_year_inputs(bundle, year)`** — recovers them from committed
  sidecars and **raises** rather than defaulting to `False` when the sidecar is
  missing, so the failure is loud;
* a pointer in `run_year_kwargs`' docstring telling every caller to splat it.

The detector is **calendar-agnostic on purpose**. `run_calibration_full._hour_months`
builds its month map from the REAL calendar, so in a leap year the injected
steps sit on 8784-clock boundaries — CAISO 2024's biomass steps at hour
**1440 = 31 d + 29 d** — while every model array is on the 8760 non-leap clock.
A "flat within my months" test misses 2024 entirely; **the first repair attempt
in this session did exactly that and silently left 2024 uncorrected.** Reported
because it nearly shipped a half-repair. The shape test (≤ 12 levels, ≤ 11
change points) catches all three years.

**Blast radius, measured, not assumed.** caiso-244 and caiso-245 used the same
rebuild but read **only** the import rows (`zone in CORRIDOR_LANDING`) and a
`cheapest_gas` diagnostic restricted to `GAS_GROUPS`; blank-group biomass units
enter neither. **Their findings are unaffected.** caiso-247 is the only
casualty. (caiso-202 and caiso-230 already excluded biomass explicitly.)

---

## §5 — DISCLOSURES AGAINST INTEREST

1. **This is my own error, found on my own re-reading, one day after
   publication and after the finding was merged.** It was avoidable: the
   caiso-202 probe comment naming the exact mechanism was in the file I had
   open, and caiso-247 cited caiso-202 §C's table in the same paragraph where
   it mis-stated what §C did with biomass.
2. **The pre-registration did not catch it.** PRECOMMIT-caiso247 §1.1 asserted
   the rebuild was "the fleet the LP saw" and no gate tested that claim. A
   G-FLEET gate — reconstructed class energy vs the committed `class_hourly`
   totals — would have caught it instantly, and **is now the obvious missing
   gate for every fleet-only probe.** It is not added here because that is a
   design change, not a repair; it is filed as §7 item 1.
3. **The withdrawn result was the session's most quotable one**, and the two
   that survive are the ones that were already unfavourable to the lane's
   hypotheses. The correction removes a finding that would have funded a
   session; it does not move C3a in either direction.
4. **A near-zero class can meet the shape test by coincidence** — CAISO 2023's
   `oil` klass (65 MWh total, 2 distinct levels) is flagged by the detector.
   Harmless, because only `biomass` is consumed, but the detector is a shape
   heuristic and is documented as one.
5. **The corrected picture is WORSE for attribution, not better.** DOM_GAS +
   STORAGE is now **90.3 % / 93.5 %** of the gap, and STORAGE — the residual
   "nothing price-matched" bucket — is the single largest cell in 2025
   (53.3 %). The lane knows less about where its residual sits than caiso-247
   claimed, not more.

---

## §6 — WHAT THIS DOES NOT DO

It does not arm anything, change the keeper, register a run, or touch any
other ISO's shard. It does not re-open the HUB question. It does not
adjudicate the DOM_GAS/STORAGE split — that is now the ranked object (§7) and
needs its own pre-registration.

---

## §7 — THE QUEUE, RE-RANKED AGAIN

1. **NEW, ranked first: separate DOM_GAS from STORAGE with a loss-adjusted
   price match** (caiso-247 queue item C, promoted by this correction). The
   keeper runs `caiso_zonal_loss_surface`, so a unit marginal in zone A prices
   zone B at `λ_A/(1 − loss)` and an exact `mc = λ_z` test cannot see it. With
   the delivery factors from `CAISO_loss_surface.csv` the test becomes exact
   and the 53.3 % STORAGE bucket resolves. **Precondition for quoting any
   DOM_GAS number.** Zero LP.
2. **Add a G-FLEET gate to the fleet-only probe protocol** (§5.2): reconstructed
   class energy must reproduce the committed `class_hourly` class totals before
   any attribution is claimed. Cheap, and it is the gate that would have caught
   this.
3. **The CC-hot / CT-cold split** (caiso-247 §4.7) — unchanged, still live,
   still needs a functional-form charter.
4. **Demoted and unchanged:** the import seam (4 % of the gap) and the two
   fitted firm prices (1.6 %) — structural objects under rule 1, not C3a levers.
5. **Owner ask, carried:** the C3a weight basis (caiso-247 §4.5).
6. **Biomass is CLOSED as a C3a object** — it cannot set price in this model.
   The open question it leaves is a *volume* one for another session: whether
   3.2–4.5 TWh/yr of price-insensitive injected biomass is the right
   representation. That is not a C3a lever.

---

## §8 — DO-NOT-REDO ADDS

1. **Never rebuild a keeper fleet with `run_year_kwargs` alone.** Splat
   `derived_run_year_inputs(bundle, year)` too, or the fleet carries phantom
   biomass units. An empty `run_year_unreachable` does **not** mean the rebuild
   is complete — it only reports keys the bundle records.
2. **Never test "injected must-run" by flatness within a non-leap month map.**
   The solve's month map is the real calendar; 2024 breaks it. Use the shape
   test.
3. **Biomass never sets the CAISO price.** Never propose the biomass offer
   surface as a C3a object; never cite caiso-247's DOM_OTHER cell.
4. **caiso-202 §C EXCLUDED biomass deliberately and correctly** — never
   describe it as having folded biomass into "unmatched".
5. **Never quote caiso-247 §4.4's "STORAGE collapses to 3.4 % at tol 0.75"** —
   corrected to 8.7 % / 10.3 % of weight, 18.4 % / 23.8 % of gap.
6. caiso-247 §8 items 1–5 stand (they concern HUB and the weight basis, all
   unaffected); caiso-246 §8, caiso-245 §7, caiso-244 §7, caiso-243 §10,
   caiso-242 §9, caiso-241 §10, caiso-240 §7, caiso-239 §8, caiso-230 §9 stand
   in full.

---

## §9 — DELIVERABLES

This finding; the corrected
`results/calibration/_caiso247_residual_regime_anatomy.json`; the repaired
`scripts/probes/_caiso247_residual_regime_anatomy.py`;
`DERIVED_RUN_YEAR_INPUTS` + `derived_run_year_inputs` in
`scripts/replay_keeper.py`; a CORRECTION banner on
`FINDING-caiso247-residual-regime-anatomy-2026-09-05.md` with its result 3,
§4.4 and §7 item 1 marked withdrawn; the correction banner on the caiso-247
calibration-log entry and the caiso-248 entry; the corrected
`measured_offer_surface` matrix evidence. **No cell verdict moves; no
mechanism was tested; no run registered; keeper unchanged.**

**Next number: caiso-249.**
