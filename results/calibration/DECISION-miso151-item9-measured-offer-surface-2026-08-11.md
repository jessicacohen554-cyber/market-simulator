# DECISION PACKAGE — miso-151: item 9, a MISO `measured_offer_surface`, position-conditioned, subsuming `gas_offer_margin`

**Session** miso-151 · **ISO** MISO · **Keeper** `2026-08-09-miso-148-basis-aware`
(`miso148_basis_B`), **UNCHANGED — nothing armed, no `ScenarioConfig` field
added, NO LP SOLVE** · **Date** 2026-08-11 · **Status: AWAITING OWNER DECISION.**

Item 9 is not self-chartering (miso-145 §8, miso-146 PREREG §9, miso-150 §11).
This document puts it to the owner. Nothing in it is a recommendation to act on
my own object, and nothing was armed to produce it.

---

## §0 — Keeper determination, re-verified from committed artifacts

`scripts/calibration_verdict.py --run-id 2026-08-09-miso-148-basis-aware`
(stdlib-only, run pre-venv):

**NOT-YET**, rubric 3.2, scorable years 2023/2024/2025.
**FAIL SET {C3a, C3b}** — C3a 2025 −15.6 % (2023/2024 PASS); C3b 2025 NRMSE
0.212 (fails its 0.200 gate; 2023/2024 PASS at 0.082/0.125). C3c CAVEAT,
ledgered, **1 of 1 SPENT**. C1/C2/C4/C6 PASS. C8 PASS with ST_GAS **grounded
above budget** at 34.1/35.8/**48.4 %** and CT_PEAKER-2023 at 16.8 %.

MISO holds **no marker** — rule 22: 2023–2025 only, one invocation, all three
years (rule 16).

---

## §1 — The object

**The missing offer wall.** Re-measured at miso-150 on the CURRENT keeper, on a
**symmetrised** model-side universe (U1 = model fleet + its own VRE at its own
offers), `JJA_h12_17`, `lo` bracket:

| year · market | model wall | **real wall** | model $/GW | **real $/GW** |
|---|---|---|---|---|
| 2023 RT | 6.4322 GW | 0.8261 GW | $0.7004 | **$51.69** |
| 2024 RT | 8.0215 GW | −0.0078 GW | $1.8809 | **$56.06** |
| 2025 RT | **8.3024 GW** | **0.7081 GW** | **$0.7197** | **$73.4591** |
| 2025 DA | 8.3024 GW | 1.0723 GW | $0.7197 | $17.8987 |

The model holds **8.30 GW** of capability priced between its own clearing price
and the hour's actual price where MISO's real book holds **0.71 GW**; just above
its own clearing the real curve rises **$73.46/GW** against the model's
**$0.72/GW** — a **102×** ratio. The model clears at the **79.1st** percentile
of its own capability where MISO clears at the **93.8th** (RT) / **87.8th** (DA).

It is a curve-**SHAPE** object, distinct from every family already closed: not
quantity (miso-142), not merit order (miso-143), not dispatch (miso-144), not a
floor (miso-144 exonerated them), not commitment (miso-149 G-3: 95.4 % of the CC
deficit is out of merit at the model's own price).

**It is universe-robust, and that is now proven rather than argued.** miso-150
built the model-side VRE fix miso-146 §8(a) named; the wall and the ladder slope
move by **0.0000 GW and $0.0000/GW in all 24 cells**, and TRAP-2 (the one
algebraic breach channel, anchor ≤ VRE offer) is **EMPTY** — 0 of 552 JJA and 0
of 793 W1 hours, every year. **Item 9's stated prerequisite is DISCHARGED.**

---

## §2 — Why this is the only named route with the right sign

Steepening the model's supply curve immediately above its clearing point raises
the clearing price. Every other named route on this lane:

* **Item 8 (universe correction) — CLOSED.** Max ΔLEVEL over the model's
  COMPLETE offerable universe (VRE + storage, nothing left to add) is
  **+$2.594** against a **+$18** reinstatement bar. G-4 ceiling: reaching the bar
  by universe correction alone needs **3.7×–24.1× MISO's entire VRE nameplate**
  in zero-priced capability.
* **Import-representation share of the wall** — bounded at **9–12 %** of the
  wall; ΔLEVEL +2.236 RT / +3.293 DA in 2025. Worth more than the VRE asymmetry,
  still nowhere near the bar. Not adjudicated; needs its own charter.
* **The plant-grain fossil rating repair (miso-149 §7)** — 7,915 MW in 2025
  across 86 plants below their own CAMPD total p99. This moves the level the
  **WRONG WAY**: more capability lowers price, exactly as miso-148 measured
  (C3a worse in all three years). It is a rule 14 `[R-ACCURATE]` repair, **not**
  a level repair, and is **not** offered as progress against the level miss.

---

## §3 — Where the miss lives, and why the landed corpus matches it

C3a reproduced from committed artifacts (run payload load-weighted across zones
vs `bench/MISO/<y>.json.gz` `avgLMP.rt_lw`):

| year | model lw | actual lw | Δ $/MWh | Δ % | committed C3a |
|---|---|---|---|---|---|
| 2023 | 32.197 | 32.85 | **−0.65** | −1.99 % | −1.98 % |
| 2024 | 29.704 | 32.30 | **−2.60** | −8.04 % | −8.03 % |
| 2025 | 38.372 | 45.46 | **−7.09** | −15.59 % | −15.58 % |

**Demand-weighted monthly decomposition of the deficit:**

| year | JJA share | Jun+Jul share | May |
|---|---|---|---|
| 2023 (C3a PASSES) | **−9.6 %** | 8.5 % | −0.145 |
| 2024 | **52.8 %** | 57.8 % | −0.398 |
| 2025 | **61.1 %** | 56.6 % | **+0.382** |

2025 monthly (model lw-across-zones vs bench simple monthly RT mean):
Jun **−13.12**, Jul **−16.34**, Sep −7.88, Jan −6.86, **May +5.01 (+15.1 %,
OVER)**.

**The landed corpus is JJA 2023–2025, both markets — exactly the window carrying
the miss, in exactly the two years that miss it.**

> **BASIS CAVEAT, stated because it matters.** The monthly table mixes bases:
> the model side is zone-load-weighted monthly, the actual side is the bench's
> **simple** monthly RT mean, so the monthly aggregate (−4.997 for 2025) is NOT
> the C3a load-weighted deficit (−7.09). The **shares** are the robust reading;
> the levels in that table are descriptive only.

---

## §4 — The identification (rule 13 `[R-MEASURED]` forward-analogue test)

**Corpus.** MISO Market Reports masked **submitted** offer books,
`docs.misoenergy.org/marketreports/YYYYMMDD_{da,rt}_co.zip`, ~90-day lag,
curated to the `energy-offers` datatype v2 (`iso, market, unit_code,
interval_start_utc, step_idx`). Ten cumulative MW/price breakpoints;
`ecomin_mw` / `ecomax_mw` / `self_scheduled_mw` present and **0.0000 null** on
the 2025 DA partition; economic / emergency / must-run / unit-available
declarations; slope flag; Region ∈ {North, Central, South}.

**Rule 13 is enforced at curation, not by discipline.** The source files carry
dispatch **awards** — RT `Cleared MW1`–`Cleared MW12`, DA `MW`,
`Target MW Reduction`. Those are OUTCOMES. They have no column in the schema and
are dropped by `curate_miso_energy_offers.py::OUTCOME_COLS`; they cannot be read
downstream.

**Masked identity is persistent** — day-over-day 1351/1351, cross-year 92–99 %
(miso-136) — so per-unit longitudinal statistics are meaningful. **No class
crosswalk may be asserted**: the corpus carries 0 fuel/technology columns and
miso-138 built and REFUTED the offer-side class bridge.

**Conditioning — POSITION, never class:**

1. **own-curve position** — each step's cumulative MW as a fraction of that
   unit's own `ecomax_mw` (headroom position). A *unit-relative* coordinate that
   needs no class, which is what makes a class-free surface constructible at
   all.
2. **system state** — the hour's net-load (or load) percentile within the
   training window, on the registered cross-ISO bin geometry
   `[0.80, 0.90, 0.97]`.
3. **delivered gas price** — the same `data.fuel.trajectories._gas_series` the
   `gas_offer_margin` anchor is identified on.

**Estimated by POOLING all three years, applied identically to every year.**
Never per-year. That is the CEMS-emission-rate precedent: a parameter derived
from multi-year history, conditioned on drivers that exist in a forecast year,
which regenerates forward and responds to changed conditions.

**EXPLICITLY EXCLUDED AND FORBIDDEN** (miso-146 PREREG §9, standing, binding on
any successor): *a measured same-year offer curve pinned into the backcast is a
measured **outcome** overlay with no forward analogue — forbidden as
methodology, and admissible at most as an explicitly-labelled, default-**off**
diagnostic probe.* This proposal is a pooled multi-year surface, not a per-year
pin.

---

## §5 — THE CENTRAL RISK, stated first and against interest

**miso-145's LEVEL term is NEGATIVE on every instrument, universe, year and
hour-subset.** At matched position in the stack the real book offers **$8 to
$15/MWh CHEAPER** than the model does (2025 JJA h12–17: RT **−$14.376**, DA
**−$8.298**; the 2024 DA cell is **−2.401** per the authoritative artifact, not
the −4.996 printed in that finding's body).

**A surface that transfers the real book's LEVEL would make C3a WORSE, not
better.** The mechanism has the right sign only if it transfers **SHAPE** — the
near-vertical rise just above clearing — while the level stays on the
physical/fuel basis. Getting that wrong inverts the sign of the whole exercise.
It is precisely why the object is specified *position-conditioned* rather than
"adopt the measured curve", and it is the first thing the kill gates test (K1).

**Second risk: the wall does not size the fix.** It is measured at the model's
own clearing percentile, and the LP **re-clears** when the curve changes.
Nothing in this package predicts the magnitude of the price move, and I make no
claim that it closes −$7.09. Against-interest bound carried from the charter:
**2023 carries nearly the same CC gap and C3a-2023 PASSES** — do not predict,
claim, or size any repair to 2025's −15.6 %.

**Third: the open design question is real, not a detail** (miso-145 §8). A
position-conditioned surface must map a *fleet-level* shape onto *per-unit*
offers without inventing a class. Item (1) above — own-`ecomax` fraction — is
my proposed answer, and it is the part of this proposal least supported by prior
measurement.

---

## §6 — How it subsumes `gas_offer_margin` (rule 19 `[R-ONE-MECH]`)

**Armed on the keeper today:** `gas_offer_net_revenue_margin = True`,
`gas_offer_margin_anchor = 3.0492` $/MMBtu, `gas_offer_margin_zonal_anchor =
False`. The anchor is **measured** — the mean of the model's own merit-order
delivered-gas series over 2023–2025, an identification constant, rule-23 frozen,
re-derived only when the gas source workbooks change. It is **not** a DOF.

The mechanism reprices every gas tranche whose band declares a measured physical
basis as

```
phys × HR_base × fuel(t)  +  (mult − phys) × HR_base × anchor
```

— the above-physical markup becomes a **fuel-invariant $/MWh net-revenue
margin**. **The markup it prices comes from the FITTED `offer_curve_by_group`
multipliers.**

A position-conditioned measured surface supplies exactly that $/MWh markup term,
from measurement. So:

* **KEEP the form.** The fuel-invariance is the identified, externally-validated
  part — the multiplicative form was rejected by the 2022 NEISO validation
  rotation (bulk 40–80 overshoot +57.7 $/MWh at ~2.9× anchor gas) and by the
  within-window winter-over/summer-under signature (neiso-45/46/47).
* **REPLACE its source.** `(mult − phys) × HR_base × anchor` → the measured
  surface's $/MWh at that (position, state, gas) cell.

**One mechanism, one phenomenon. `gas_offer_margin` is SUBSUMED, not stacked.**
The CAISO precedent is the same shape and is already adjudicated `K`:
`caiso_offer_surface_measured` replaced the fitted `_CAISO_OFFER_CURVE` gas band
multipliers, and the matrix records it as a rule-24/25 **SHRINK**.

---

## §7 — DOF ledger

**Today** (`miso148_basis_B/calibration_attestation.json`, schema
`dof-ledger/v1`): **30 entries, `n_residual` = 2**, and those two ARE MISO's
entire fitted offer surface:

| entry | identification | n_scalars |
|---|---|---|
| `offer_curve_by_group` | **residual** (≥39 solves) | **92** |
| `offer_curve_smoothing` (`n`=6, `exp`=1.0) | **residual** | **2** |
| 24 further entries | measured-physical | — |
| 4 further entries | measured | — |

`offer_curve_by_group` splits: **gas 67** (of which **20** are measured `phys_*`
→ **47 fitted**), **coal 25**.

**Item 9's scope, gas block only: −47 fitted scalars, +0 free parameters.** The
surface is a derived artifact from a rule-23-frozen derive; bin geometry follows
the registered cross-ISO convention `[0.80, 0.90, 0.97]` and is likewise frozen.
`n_residual` **2 → 1** (`offer_curve_smoothing` survives; coal's 25 survive
under rule 19 — MISO-53 adjudicated the coal deep-discount premise on a
different mechanism).

**This is the only route on MISO's queue that REDUCES the DOF ledger.** Every
other named candidate is DOF-neutral at best.

---

## §8 — Cost, stated honestly

* **The corpus is JJA-only.** 552 files = 92 days × 3 years × 2 markets,
  429.6 MB. A surface applied to all 8760 h needs the full year:
  `fetch_miso_energy_offers.py --months 1 … 12` → **2,190 files ≈ 1.7 GB raw +
  ~1.15 GB clean, ~8 min fetch**. That competes for the same writable allowance
  as the **8 GB swap** a solve requires (~17 GB total, ~15 GB host).
  The alternative — scope the arm to JJA hours only, leaving the rest on the
  incumbent surface — covers 61 % of the 2025 miss but makes it a **seasonal**
  mechanism, which then owes a window story under rule 17 `[R-FLOOR-WINDOW]`.
  **I recommend the full-year corpus**; a seasonal offer surface with no
  seasonal driver is the kind of thing rule 17 exists to catch.
* **Solves.** Same-HEAD zero-delta control + one arm, 3 years each
  (`--year 2023 2024 2025`, single invocation, years sequential per rule 12),
  ≈ 50 min per invocation, run concurrently → ~1 h wall clock. Both registered
  on the dashboard per rule 15, keeper or rejected.

---

## §9 — KILL GATES (pre-registered; a breach is reported at FULL MAGNITUDE and escalated, never silent, never auto-fatal)

* **K1 — SIGN.** If the arm moves C3a-2025 in the **negative** direction at all,
  **STOP**: that is the level-transfer inversion of §5 and it is fatal to the
  mechanism as specified.
* **K2** — C3b-2025 NRMSE ≤ **0.212** AND MUST NOT RISE (already failing its
  0.200 gate).
* **K3** — C3b 2023/2024 stay PASS (0.082 / 0.125); C3a 2023/2024 stay PASS
  (−1.98 % / −8.03 %).
* **K4 — MAY 2025.** Report the May effect **explicitly, in $ and %, whatever
  the sign.** May is already **+12–15 % OVER**; a surface that raises summer
  offers can push it further over.
* **K5 — C8.** No material class's forced share rises; no D-4 break. ST_GAS is
  already grounded at **48.4 %** in 2025 and CT_PEAKER-2023 at **16.8 %** —
  headroom is thin.
* **K6 — C3c is 1/1 SPENT.** The tail may not motivate any parameter. Fail-set
  must stay **⊆ {C3a, C3b}**.
* **K7** — C1/C2 PASS on gated years; 2025 descriptive vs EIA-930 only
  (preliminary EIA-923).
* **K8** — leave-one-year-out within 2023–2025 before any promotion (rule 22).
* **K9** — the derive is **frozen against residuals** (rule 23
  `[R-FROZEN-DERIVE]`): it re-derives only when the corpus updates, and any
  re-derivation commit must cite the data change.

Instrument caveat inherited and not re-litigated: the keeper is **not
bit-reproducible at HEAD** (miso-148 K0; max |Δ| 912.5 MW, ~0.1 % of annual
dispatch). **Every quoted delta will be arm-vs-a-SAME-HEAD-CONTROL.** A
zero-delta control is solved first, every time.

---

## §10 — The decision being asked

1. **CHARTER item 9 as specified** — full-year corpus, position-conditioned,
   subsuming `gas_offer_margin`, kill gates as §9. I write the PREREG, push it
   before any adjudicating statistic, then Phase 0 → control → one arm.
2. **CHARTER it NARROWED** — JJA-only corpus and a JJA-scoped surface, cheaper
   and faster, at the cost of owing rule 17 a seasonal-window story.
3. **DEFER** — I fall to path (B): the import-representation share of the wall
   (miso-150 §7), Phase 0 only, its own PREREG, no VRE question, no fitted
   adder.

**Nothing is armed until this is answered.**

---

## §11 — Disclosures

* **No LP solve, no mechanism tested, no `ScenarioConfig` field added, no cell
  verdict moved, no run produced** — so nothing to register on the backcast
  dashboard (rule 15; the miso-149/150 Phase-0 precedent).
* Rule 22 `[R-HOLDOUT]`: 2023/2024/2025 only. MISO holds no marker. No year is
  spent in any sense.
* The charter's kill gates are **inert** here: no solve was taken, so no scored
  criterion can move. The determination is unchanged at **NOT-YET**, fail set
  **{C3a, C3b}**, re-verified from committed artifacts at session open (§0).
* **Everything computed for this document, in full:** the §0 verdict re-run;
  the §3 C3a reproduction and monthly decomposition, from the committed run
  payload `frontend/data/backcast/runs/2026-08-09-miso-148-basis-aware.js` and
  `frontend/data/backcast/bench/MISO/<y>.json.gz`; the §7 scalar counts, from
  `results/calibration/miso148_basis_B/{run_config,calibration_attestation}.json`.
  Every other number is **quoted** from a committed artifact (miso-145 §§1/6/8,
  miso-146 PREREG §9, miso-149 §§7–8, miso-150 §§4–8/11) and none was
  re-derived.
* **Concurrent-session check** at open: no other MISO backcast session — one
  open PR (#3848, ERCOT), no remote MISO branches. `claude/fh-4-miso-leg-*`
  (forecast battery) absent.
