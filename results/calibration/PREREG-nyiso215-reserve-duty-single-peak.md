# PREREG nyiso-215 — the seven single-`_peak` `CC_REGULAR` plants: which path builds them, and does the class peak band reproduce their meters?

**Session:** nyiso-215, NYISO backcast calibration. **Branch:**
`claude/nyiso-backcast-calibration-acwrdd`, on `main` at `dcb609f4`. **Date:** 2026-09-07.
**Keeper:** `2026-09-07-nyiso-213-summer-seam` — CALIBRATED, grade 7/8, fails 0, C3c the lone
ledgered caveat. **ZERO LP planned: no solve is budgeted, no arm is contemplated, nothing is
promoted or registered.** This document is committed and pushed **before P1–P5 are measured**.

**THERE ARE NO IN-SAMPLE RUBRIC FAILURES.** NYISO's keeper reads CALIBRATED with **zero failing
criteria** across 2023–2025. Nothing below is selected because a residual moved (rule 1
`[R-STRUCT]`), and no residual is consulted at any point. The 2022 held-out rung's failures
(C1 `CC_REGULAR`, C3a, C3b) are named nowhere as a target — rule 22 `[R-HOLDOUT]` forbids
identifying anything against a touchpoint year, and this session identifies nothing at all.

---

## 0. WHAT IS ALREADY IN HAND (disclosed before any prediction is written)

Rule 29 `[R-SCREEN]` step-0 census work legitimately precedes a PREREG. A PREREG that hides its
priors is weaker evidence, so every number and fact this session held **before** writing §1–§5:

1. **nyiso-214 §7**, committed on `main`: seven `CC_REGULAR` plants — 10621, 54034, 7784, 10620,
   54592, 50744, 54593 — **441.7 MW**, ~6 % of class capacity, each represented by a **single
   tranche labelled `_peak`**; model/CAMPD annual heat-rate ratios 1.44–2.69 against 0.99–1.04
   for the material fleet; two of them (50744, 54593) carry no EIA-860 `Y` duct row, so the duct
   mechanism is not their path. nyiso-214 named them and made **no claim**.
2. **The cohort file** `data/raw/_processed-legacy/reserve_duty_cc_NYISO.csv`, read in full this
   session **before** this PREREG. It carries 22 `CC_REGULAR` rows with a `reserve_duty` boolean,
   and the `True` set is **exactly** those seven. Their duty statistics: 10620 0.0122,
   7784 0.0173, 50744 0.0239, 54593 0.0246, 54592 0.0398, 10621 0.0470, 54034 0.0635. The
   nearest non-qualifier is 56188 Pinelawn at 0.1700, then 10190 Castleton 0.2237.
3. **The mechanism is armed in the keeper.** `results/calibration/nyiso213_summer_seam/run_config.json`
   reads `cc_reserve_duty_split = True` (also `cc_duct_peaking = True`,
   `cc_peaking_per_plant = True`, `cc_capacity_reconcile = True`,
   `cc_nameplate_summer_derate = True`, `cc_summer_derate_reconciled_basis = True`,
   `chp_layup_duty_curve = True`, `chp_layup_duty_split = False`,
   `cc_duct_peaking_row_scoped = False`, `nyiso_gas_bridge_reserve_duty_exclusions = True`).
4. **The code path**, read this session: `campd_bins.py` (~l. 2345) sets `pct_mc = 0.0` and
   `pct_peak = room` for a `CC_REGULAR` plant in `_reserve_duty_cohort(iso)` when
   `cc_reserve_duty_split` is on. With `pct_mr = 0` for CC, `room = 100`, so `pct_econ = 0` and
   the plant is one band. **The identification of the path is therefore already made, and this
   PREREG does not claim it as a discovery** — P1/P2 are its *reproduction and causation* bars.
5. **The derive script's own defense**, read this session: `scripts/data/derive_reserve_duty_cc.py`
   documents the 0.10 threshold as a **population gap** (`{0.012 … 0.064}` then a 2.7× gap to
   `{0.17, 0.22, 0.34, …}`, so any threshold in (0.064, 0.17) selects the identical set), and
   documents the **two-basis construction**: CAMPD plant-summed *online share* where a CEMS
   record exists, pooled EIA-923 annual net *capacity factor* where none does (7784 Allegany,
   54808 NYU, 57664 Astoria II), asserted to be "the same meter class".
6. **Schemas** of the keeper's committed hourly sidecars: `system_<year>.parquet` carries
   per-**zone** hourly `price`; `class_band_hourly_<year>.parquet` carries per-class per-**band**
   hourly `mw`. Both are committed keeper artifacts (rule 29(b) form 4 — the keeper's committed
   bundle IS the control; **no control solve is spent**).
7. **G-DRIFT**, `51f2fc2d`(keeper) → `dcb609f4`(HEAD), solve-path scope: 11 files,
   +9,341/−22. Classification in §6.

**What is NOT in hand and is measured only after this file is pushed:** the seven plants' MW,
zones and base heat rates on the keeper's own fleet; the tranche count with the flag off; the
CAMPD online share / EIA-923 CF relationship at any plant; every implied on-share; and every
number read out of `class_band_hourly` or `system`.

---

## 1. P1 — REPRODUCTION BAR (with a declared VOID)

nyiso-214's §7 census is reproduced on this session's own HEAD, from the keeper's own
`meta.json` recipe.

**Declared:** rebuilding the keeper's 2025 fleet (`fleet_only`, `full_run_year_kwargs`), the set
of `CC_REGULAR` plants whose carried capacity is **100.0 %** in `_peak`-suffixed unit ids is
**exactly** {10621, 54034, 7784, 10620, 54592, 50744, 54593}, and their summed `pmax` is
**441.7 MW ± 2.0 MW**.

**VOID:** if the summed `pmax` differs from 441.7 MW by **more than 5 %**, or the set differs by
any member, the instrument does not reproduce the committed record and **every number in this
session is withdrawn** — the finding reports the reproduction failure and nothing else.

## 2. P2 — CAUSATION: the single band is `cc_reserve_duty_split`, not a small-band filter

nyiso-198 reported the bin builder's small-band filter dropping 1.2122 MW at Riverbay 52168, so
"a small-band filter artifact" is a live alternative explanation and must be excluded by
execution, not by reading the code.

**Declared:** on an otherwise byte-identical rebuild with **`cc_reserve_duty_split = False`
alone**, at least **5 of the 7** plants acquire **≥ 2** distinct tranches, and the class's summed
`_peak` capacity falls by **≥ 400 MW**.

**REFUTES (live limb, and it kills this session's framing):** if **3 or more** of the seven
remain single-`_peak` with the flag off, the split is **not** their path, §0.4's identification
is wrong, and the object is a builder artifact after all — reported as such, and P4/P5 are
re-read as evidence about a filter rather than about a duty mechanism.

**INDETERMINATE:** 5 or 6 of 7 multi-tranche but the class `_peak` fall < 400 MW.

## 3. P3 — BASIS ASYMMETRY: two statistics, one threshold

The cohort's 0.10 threshold is applied to a CAMPD **online share** at 19 plants and to an
EIA-923 pooled net **capacity factor** at 3. These are not the same statistic: a plant online a
share *s* of hours at mean loading *L* ≤ 1 of its `pmax` posts CF ≈ *s*·*L* ≤ *s*. The fallback
basis is therefore **one-sided toward inclusion**, and 7784 Allegany is the only cohort member
that rides it. (7784 is additionally on nyiso-214's boundary list — it has **no CAMPD facility
of its own** — which is precisely *why* it takes the fallback.)

**Declared (a) — the bias is real and material:** over the `CC_REGULAR` plants that carry BOTH a
CAMPD online share and an EIA-923 record, the **median** CF / online-share ratio is **< 0.85**.
*(≥ 0.85 would say the two bases are interchangeable at this threshold and the derive script's
"same meter class" defense stands unqualified.)*

**Declared (b) — but 7784's membership survives it:** 7784's **implied online share**, taken as
its EIA-923 CF divided by the median ratio measured in (a), is **< 0.10** — i.e. the plant
qualifies on a like-for-like basis too, and the mixed basis changes **no** classification.

**(b) has a live refuting limb:** an implied share **≥ 0.10** would mean the fallback basis
*manufactured* a cohort member, which is a defect in the mechanism's membership rule and would be
reported as this session's principal result. **I expect (a) to fire and (b) to hold** — i.e. I
expect the honest outcome to be "the bias exists, is quantified, and is not load-bearing".

## 4. P4 — CONDUCT: does `2.25 × base` reproduce a 1–6 % duty?

This is the session's substantive question — *does any measured conduct justify offering these
plants' base load at a scarcity multiplier?* — and it is answered against the mechanism's **own
measured target** (the duty statistic it was built from), **never** against a price or volume
residual. Rule 1 `[R-STRUCT]` is not engaged: nothing here selects a mechanism by whether a
criterion moved.

For each of the seven, on the keeper's own fleet and the keeper's own committed hourly zonal
price, the **implied economic on-share** is the share of the year's 8,760 hours in which the
plant's `_peak` band marginal cost is at or below its own zone's committed `P1` LMP. It is an
**upper bound** on the plant's model duty (it ignores reserves, ramping, min-up and outages) and
it is computed identically in 2023, 2024 and 2025.

**Declared:** the capacity-weighted implied on-share across the seven exceeds **3.0 ×** their
capacity-weighted measured duty statistic in **at least 2 of the 3** years — i.e. the class-wide
`2.25` multiplier **under-corrects** and these plants remain materially in-merit.

**REFUTES (live limb — and this is the outcome that vindicates the incumbent):** a ratio
**≤ 1.5 ×** in at least 2 of 3 years says the band is right-sized against the meter it was
built to reproduce, the mechanism is **deliberate and defensible**, and the object closes as a
**clean negative** — which this lane's charter names a SUCCESS, not a null.

**INDETERMINATE:** (1.5, 3.0] in two or more years.

## 5. P5 — the committed bundle's own band dispatch (a bound, not an inference)

P4 is an upper bound computed from prices. P5 is the keeper's **realised** dispatch, read from
the committed `class_band_hourly_<year>.parquet` — no solve, no inference.

The `CC_REGULAR` `peak` band holds two disjoint populations: the duct band at the flagged large
plants (nyiso-214 §6 form A: **716.8 MW**) and these seven (**441.7 MW**). So any hour in which
the class's `peak`-band MW **exceeds the duct population's own available capacity** is an hour in
which reserve-duty capacity is provably generating.

**Declared:** in 2025 the `CC_REGULAR` `peak` band's **mean** dispatch is **≥ 120 MW**, and the
share of hours in which it exceeds **716.8 MW** — the strict lower bound on reserve-duty
generation being non-zero — is **≥ 2.0 %**.

**REFUTES:** a mean **< 40 MW** and an exceedance share **< 0.5 %** would say the band barely
runs at all, P4's upper bound is not realised, and the mechanism is working as designed
regardless of what P4 reads. **P4 and P5 are declared to be mutually consistent and jointly
disjoint from a third outcome:** if P4 fires (under-correction) and P5 refutes (the band is
inert), the correct reading is that **something other than the offer band** is holding these
plants down, and the finding says so rather than claiming the band under-corrects.

## 6. G-DRIFT audit (rule 29(b)) — written before any arm, and no control solve is spent

`git diff 51f2fc2d dcb609f4 -- src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`
= 11 files, +9,341/−22. Classified:

| file | classification | reason |
|---|---|---|
| `config/constants.py` | **INERT** | one CAISO 2022 nuclear-CF row (caiso-262) — another ISO's branch |
| `config/fuel_trajectories.py` | **INERT** | CA-Quebec 2022 carbon-auction rows — another ISO's branch |
| `model/interchange/spec.py` | **INERT** | CAISO 2022 DSW surplus depth — another ISO's branch |
| `pipeline/backcast_config.py` | **INERT** | SPP coal-supply curve crosswalk — another ISO, and NYISO carries no coal |
| `config/scenarios.py` | **INERT** | `capacity_screen_peak_measured_hindcast` default flip + `__post_init__` coercion; consumed only by the capacity screens, which a `mode="backcast"` run never enters |
| `results/cache.py` | **INERT** | the same field's cache-key epoch ledger; a key-provenance record, no solve behaviour |
| `data/eia930/actuals.py` | **LIVE (scoped)** | `_screen_fuel_spike_columns` (lane SPP-41) screens `NG:` unit-slip hours for **every** BA, so it can move the C1/C4 benchmark and the delivered VRE profile. **Inert for THIS session by scope:** nothing measured here reads EIA-930 actuals — P1/P2 read the fleet, P3 reads CAMPD + EIA-860 + EIA-923, P4/P5 read the keeper's own committed parquets. It is recorded, not absorbed: a NYISO lane that re-solves or re-scores C1/C4 owes it a check. |
| `data/raw/_validation-source/*` (3 files + README) | **INERT** | an SPP LMP parquet and a CAISO 2022 demand CSV — other ISOs' benchmark inputs |

**No LIVE hunk touches anything this session measures, so rule 29(b) form 4 stands and no
control solve is earned.** Inertness is additionally **confirmed by execution**, not by reading:
`scripts/probes/nyiso196_rebuild_checks.py --year 2024` must reproduce its committed record with
`git status --porcelain -uno` empty, and P1 is itself a reproduction bar against nyiso-214's
committed census.

## 7. Governance

* **Rule 29 `[R-SCREEN]`:** step 0 only. No screen, no control, no bundle, no LP — so 29(c)'s
  delete-before-merge has nothing to delete and the control question does not arise.
* **Rule 22 `[R-HOLDOUT]`:** training-tier only — 2023–2025 meters and the keeper's own fleet.
  No out-of-training year is solved, scored or registered. `complete` / `frontier` / the
  locked-test freeze all untouched; 2020/2021 stay unspent and are **not this session's spend**.
* **Rule 15 `[R-DASHBOARD]`:** no run is produced, so there is nothing to register and
  keeper-only retention is untouched.
* **Rule 28 `[R-MECH-MATRIX]`:** `cc_reserve_duty_split`'s NYISO cell is re-stamped in this
  session with whatever P1–P5 return, including a negative.
* **Rule 23 `[R-FROZEN-DERIVE]`:** `derive_reserve_duty_cc.py` is **audited, never re-derived**.
  No source data changed, so no re-derivation is licensed whatever P3 reads.
* **Markers:** none move. No promotion is contemplated, so D-5(b) does not attach.
* **The SIX pending owner rulings are untouched and none is prejudged** — including
  nyiso-214 §6's membership card: this session builds, arms, screens and recommends **no** form
  of A/B/C/D/E, and `cc_duct_peaking*` is not modified.

## 8. Basis discipline

CAMPD on both sides in every year, stated at each use. C1 is not quoted anywhere in this session;
where a class total appears it is the keeper's committed metric, not a CAMPD-basis gap. The
bench's split-plant keys (`2500`, `50292`) are not folded. nyiso-214's boundary list —
57664 / 7784 / 54808 (no CAMPD facility of their own) and 55375 / 56196 / 2500 (facility spans
2.05× / 1.25× / 7.05× the model plant) — is applied: **7784 is boundary-contaminated and is a
member of the object**, which is exactly why P3 exists and why no CAMPD-side statistic is quoted
at 7784 anywhere.

*(nyiso-215. Written before P1–P5 were measured; committed and pushed before any of their
numbers were read.)*
