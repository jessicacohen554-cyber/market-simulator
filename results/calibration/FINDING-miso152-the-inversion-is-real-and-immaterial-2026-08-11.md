# FINDING — miso-152: the base-band inversion is DELIBERATE, its dispatch consequence is REAL and near-universal, and on the only scope this session can trust it is IMMATERIAL (0.31–0.45 % of CC energy)

**Session** miso-152 · **ISO** MISO · **Keeper** `2026-08-09-miso-148-basis-aware`
(`miso148_basis_B`), **UNCHANGED — nothing promoted, nothing solved** ·
**Date** 2026-08-11 · **Charter** (B), the thread miso-151 §8 named and did not
open · **PREREG** `PREREG-miso152-tranche-fill-order-2026-08-11.md`, pushed
before any adjudicating statistic · **Branch fired: B-2 IMMATERIAL** (a
pre-committed branch — this outcome was anticipated in writing).

---

## 1. The one-paragraph answer

miso-151 asked why MISO's `econ_low` bands price *below* their own plant's
committed block. **They do it on purpose**: `_MISO_OFFER_CURVE` grounds the
committed band in the measured CAMPD part-load premium, and the source comment
records the *previous* state (committed 0.92 < econ_low 0.95) as the defect it
was fixing. So the inversion is not itself a bug. **What it opens is a bug**:
the LP fills a plant's tranches in COST order while physics fills them in
OUTPUT-POSITION order, there is **no same-plant fill-order constraint anywhere
in the LP**, and MISO floors **nothing** on the CC committed tranche
(`pmin` and `min_gen` are 0.0 on all 44 CC_REGULAR committed rows, all 8760
hours). A MISO CC plant therefore produces its incremental bands while its
515.97 MW min-load block sits idle — an output the physical unit cannot
deliver, confirmed on a real `solve_dispatch`. It happens in **half of all
plant-band-hours** and touches **39–43 of 44 CC plants**. And it is
**immaterial**: the physically-impossible energy is **0.36 / 0.31 / 0.45 %** of
CC energy (2023/24/25), against a pre-registered prior of 25 % [5 %, 60 %] —
**refuted by ~55×**, below the band's floor. The lane closes on charter (B)
with the object documented, not repaired.

---

## 2. Gate results

| gate | bar / prior | measured | verdict |
|---|---|---|---|
| **G-1** fill-order constraint exists? | binary | **NO** — `lp/bounds.py` sets `col_lower = min_gen` else `pmin`, `col_upper = pmax × availability`, per independent column; the only group row in `lp/rows.py` is the hydro envelope | object stands |
| **G-2** effective mc non-monotone in position? | 3 classes [2, 5] | **3** — CC_REGULAR, CT_PEAKER, ST_GAS (COAL clean) | **P-3 held** |
| **G-3** real LP fills econ before min-load? | binary | **YES**, 4/4 tests on `solve_dispatch` | confirmed |
| **G-4** out-of-order share of CC energy | 25 %, band [5 %, 60 %] | **0.36 / 0.31 / 0.45 %** | **P-1 REFUTED ~55×, below band** |
| **G-5** sign of the repair | +$0.60, band [−0.50, +2.50] | **repair-dependent, both limbs small** | see §5 |
| **T-6** reconstruction vs committed `class_hourly` | ±10 % | CC **−1.83 / −1.01 / +9.42 %** | **PASSES** (2025 narrowly) |

**G-2 detail (CC_REGULAR, 2025).** The committed block is dearer than an econ
sub-tranche in **1,167,048 of 2,312,640** plant-band-hours (**50.5 %**), mean
gap **$0.833/MWh**, on **142 of 264** (plant × econ-sub) pairs — i.e. about
**3 of the 6** smoothed sub-tranches per plant, exactly what G-3 predicts from
the registered bands (committed 1.005 straddled by econ_low 0.95 → econ_high
1.08, smoothed into `econc00..econc05`).

**The stack, measured on real plant p991 (2025).** committed **515.97 MW @
$26.184**; econc00–02 **36.85 MW each @ $25.122 / $25.643 / $26.164** — all
three *cheaper* than the min-load block they physically sit on top of —
then econc03–05 @ $26.686 / $27.207 / $27.729. The plant can deliver ~110 MW
while its own minimum stable output is 516 MW.

---

## 3. Why it is immaterial despite being near-universal

The two facts are not in tension. The inversion is **wide but thin**: only ~3
of 6 econ sub-tranches sit below the committed block, each is **36.85 MW against
a 515.97 MW** min-load block (7 %), and the price window between `mc(econc00)`
and `mc(committed)` is about **$1/MWh** wide. Out-of-order fill needs the hourly
price to land inside that window — 7,118 / 7,200 / 10,693 plant-hours a year —
and even then it can only mis-place ~110 MW of a 737 MW plant. Half the
plant-band-hours are *inverted in price*; a half-percent of the energy is
actually *mis-dispatched*.

---

## 4. What this does NOT license (T-6 did its job)

The pre-registered G-4/G-5 scope was CC. G-2 then found the same inversion on
**CT_PEAKER** (mean gap **$12.50–25.89/MWh**, ~15–30× CC's) and **ST_GAS**
(**$3.79–4.03/MWh**), and a `min_gen` census found **CT_PEAKER's 79 committed
rows are as unfloored as CC's** (ST_GAS is partly pinned, 16/23 rows, 27.7 % of
hours). So the pre-registered scope **under-counts the object**, and this
session extended the measurement — **labelled NOT PRE-REGISTERED in the probe
and here**.

**Those extended numbers are DESCRIPTIVE ONLY and no verdict rests on them**,
because the T-6 counter-measurement **FAILS** on both: the price-taking
reconstruction misses CT_PEAKER by **+38.8 / +37.9 / +40.1 %** and ST_GAS by
**−38.0 / −39.2 / −59.3 %** of class energy. CT dispatch is commitment- and
startup-driven and ST_GAS is partly floored, so a pure merit reconstruction
does not describe them. For the record and **not as a result**: the CT_PEAKER
out-of-order share reconstructs at 1.20 / 0.54 / **6.47 %**. The 2025 CT figure
is the one number in this session that would clear the 5 % materiality floor,
and it is precisely the number T-6 says is untrustworthy.

**This is the successor thread, and it is NOT opened here:** CT_PEAKER carries
the largest per-MWh inversion gap in the fleet and no floor at all, but
measuring it needs an instrument that reproduces CT commitment — not this
reconstruction.

---

## 5. G-5: the sign is repair-dependent, and this session declines to pick

Two repairs exist and they move price in **opposite directions** (change in CC
supply at the keeper's own hourly prices, 2023/24/25):

* **R-a PIN** — the min-load block is must-take whenever the plant produces
  (the ERCOT-141 `floor_online_hours` mechanism): **+1.06 / +0.87 / +1.49 %**
  supply → price **DOWN**, the *wrong* way for a −15.6 % miss.
* **R-b GATE** — a plant may only produce upper bands in hours its own min-load
  block clears: **−0.36 / −0.31 / −0.45 %** supply → price **UP**, the right
  way, and tiny.

PREREG P-2 was registered with a band **spanning zero** for exactly this reason,
and §7 disclosed that this session's author expected "UP" before measuring.
Neither limb is worth a mechanism at this magnitude, and picking one to get a
sign would be fitting the repair to the residual (rule 1 `[R-STRUCT]`, second
half). **No lever is proposed.**

---

## 6. Verdict and what changes

**Branch B-2 IMMATERIAL.** Charter (B) is **CLOSED**: the inversion is
explained (deliberate, measured, documented), its dispatch consequence is
confirmed real at three independent levels (source, effective mc, live LP
solve), and its magnitude on the only trustworthy scope is **< 0.5 %** — below
the 5 % floor this PREREG fixed in advance for proposing a repair.

**No run was solved and none is registered** — Phase 0 charter, declared in
PREREG §6 and honoured. Rule 15 is not engaged because no run exists. The
keeper is untouched; MISO's fail set is unchanged at {C3a, C3b}.

**Matrix (rule 28(b)):** `gas_offer_curve_tranches` MISO keeps cell **`K`** —
the mechanism is not refuted, and this session adds the measured
fill-order caveat to its evidence. No new `ScenarioConfig` field, so rule 28(c)
is not engaged.

---

## 7. Disclosures — including one defect this session created and caught

1. **The probe's first result was a spurious exact `0.0`.** Collapsing the six
   smoothed econ sub-tranches into one dict entry per band kept only the
   *dearest* (`econc05`, $38.38 > committed $36.27), so "committed off ⟹ upper
   off" held by construction and out-of-order energy came back exactly zero on
   a run that otherwise looked healthy. **This is the miso-151 pattern
   precisely** — an aggregation bug that cannot fail loudly. Caught by
   disbelieving a clean zero and dumping the real suffix inventory; the fix
   carries the sub-tranches as a list and the reason is a comment in the code.
2. **The reused miso-134 chain is hard-wired to the miso-132 bundle.**
   Importing its helpers unchanged would have screened the **wrong keeper**.
   `BUNDLE` is repointed to `miso148_basis_B` at import and asserted to exist.
3. **The extended CT_PEAKER / ST_GAS scope was not pre-registered** and is
   reported as descriptive only (§4), with its failing T-6 stated at full
   magnitude rather than omitted.
4. **CC_INTERMEDIATE has no rows in the assembled fleet** — `plant_group` stays
   `CC_REGULAR` under `cc_intermediate_split` (the split routes the offer
   curve, not the class label). The pre-registered two-class CC scope is
   therefore CC_REGULAR in practice; both classes register identical bands, so
   nothing changes numerically.
5. **T-6 passes 2025 narrowly** (+9.42 % against a ±10 % bar). Reported rather
   than rounded; the reconstruction over-dispatches because it ignores
   transmission, reserves and commitment.
6. **Every comparison carries an explicit tolerance** (1e-9 / 1e-6), never
   bit-identity (T-5), and magnitudes are reported in both branches.
7. Rule 22 `[R-HOLDOUT]`: **2023/2024/2025 only**, MISO holds no marker. No
   solve, no holdout spend, no registration.

**Artifacts.** `results/calibration/_miso152_fillorder.json`; probe
`scripts/probes/_miso152_fillorder.py`; G-3 tests
`tests/test_miso152_fillorder.py` (4 passing).
