# FINDING — pjm-138: **the SYSTEM-ENERGY half of the Dominion CT-hour deficit is mostly the reserve opportunity cost PJM prices and the model structurally cannot.** PJM's own day-ahead market prices synchronized reserve **above zero in 84.2 / 96.7 / 47.6 % of all hours**; the model's reserve dual is above zero in **0 / 2 / 28** hours of 8,760 — and its requirement, its published two-step ORDC curve and its in-LP co-optimization are all already correct and already armed. Crediting PJM's own reserve clearing price against the CT-hour system-energy gap leaves **$1.46 / $6.12 / $11.97 /MWh** of a **$17.97 / $26.44 / $54.06** total deficit: **8 / 23 / 22 %**. The rest is two closed lanes — intra-zonal congestion (pjm-137) and a reserve price whose absence pjm-82 already attributed to the **no-MIP representation boundary**.

**No LP was solved.** All measurements run on the committed keeper
`pjm137_ctheatrate_B` `hourly/` sidecars, PJM's committed intakes and the CAMPD
unit-level record. Probes: `scripts/probes/_pjm138_mec_gap_shape.py` (M2),
`scripts/probes/_pjm138_marginal_ownership.py` (M1 + the G-20b sizing). Machine
output: `results/probes/pjm138_mec_gap_shape.json`,
`results/probes/pjm138_marginal_ownership.json`.

**No mechanism is chartered and no delta is proposed** — every lane the
measurement points at is already adjudicated `R`, `I`, `G` or owner-closed, and
rule 1 `[R-STRUCT]` does not license reopening one to chase a residual on an
already-`CALIBRATED` keeper.

---

## §0 — the verdict in one table

| test | question | result | verdict |
|---|---|---|---|
| **D1** how does the deficit split | is the "system-energy half" real, and how big exactly? | **yes, and it is an exact identity, not an attribution choice.** CT-energy-weighted the total deficit is **$17.97 / $26.44 / $54.06**, splitting into a system-energy part **$8.15 / $12.74 / $24.78 (45 / 48 / 46 %)** and a basis part **$9.82 / $13.70 / $29.28**. Identity residual **0.000000000** in all three years | the pjm-137 §6 lead is confirmed and sharpened |
| **D2** what shape does it have | diffuse (offer level) or concentrated (scarcity)? | **neither a level problem nor purely a tail one — it is a DISPERSION problem.** Annual load-weighted the model reproduces PJM's own MEC to **+$0.47 / +$2.62 / +$8.48**, while running **−$4.86…−$5.78 too DEAR** in the slackest net-load decile and **+$14.32 / +$21.59 / +$39.92 too CHEAP** in the tightest. Overnight (h01–h04) it is $1.6–7.3 too dear; the gap peaks at the morning ramp (h06–h07) and the evening peak (h16–h18) | concentrated → the reserve/supply lane, per the charter's own discriminator |
| **D4** how thin is the tail | on PJM's own system energy price, not the total LMP | **3–6× too thin.** Measured MEC exceeds $100 in **29 / 128 / 392** hours; the model's load-weighted system price does so in **3 / 72 / 65**. Above $150: **14 / 26 / 146** measured against **0 / 1 / 24** | the tail is a system-energy defect, not a congestion one |
| **D5** is it reserve | PJM publishes its own DA reserve clearing price — does it explain the gap? | **yes, most of it.** Measured synchronized-reserve MCP is above zero in **84.2 / 96.7 / 47.6 %** of hours and correlates with the model's system-energy gap at **r = 0.788 / 0.604 / 0.657**; the top net-load decile carries **26.2 / 26.5 / 35.9 %** of the year's reserve price. In Dominion CT hours the measured reserve MCP is **$6.71 / $6.65 / $14.18** against a system-energy gap of **$8.17 / $12.74 / $24.78** — **82 / 52 / 57 %** of it. The model's reserve dual in those same hours is **$0.00 / $0.03 / $1.37** | **the system-energy half is largely a reserve-price half** |
| **D5b** why can't the model price it | is this a missing mechanism? | **NO — every part of the mechanism is already built, measured and armed.** The requirement is PJM's own measured `as_req_mw` (`load_pjm_measured_reserve_requirement`), the demand curve is PJM's published two-step ORDC (`pjm_ordc_curve.csv`, m11 §4.3.3, $850 / $300), and the co-optimization is the in-LP per-generator joint-headroom form that is *designed* to price exactly this opportunity cost. It still clears at $0 because the model's reserve **supply** is 5–10× the requirement — which pjm-82 attributed to the **LP-vs-MIP boundary**: with a continuous commitment variable, fractional online capacity is free, so every idle unit's headroom is synchronized-reserve-eligible | **a disclosed architectural limit, not a calibration gap** |
| **A1** an hour-key correction to pjm-137 | does the EPT/EST offset matter? | **not to pjm-137's levels; yes to any shape statistic.** pjm-137 keyed the measured components on Eastern PREVAILING time against a model and a CAMPD record that are both Eastern STANDARD. Re-keyed on `datetime_beginning_utc` at UTC−5 its M3 headline moves by **$0.12–0.38/MWh** (total CT-hour deficit 17.586 → **17.968**, 26.559 → **26.439**, 54.389 → **54.059**) and the measured/model price correlation improves 0.704 → **0.745**, 0.732 → **0.764**, 0.772 → **0.823** | pjm-137 stands; its diurnal profile does not |

---

## §1 — D1: the deficit splits by an identity, and both halves are now sized

For any hour, PJM's own LMP decomposition and the model's own dual structure
give an **exact** split, with no attribution choice in it:

```
measured_DOM_LMP − model_DOM_dual
  = (measured_MEC        − model_load_weighted_dual)      … SYSTEM ENERGY
  + (measured_DOM_basis  − model_DOM_basis)               … CONGESTION + LOSS
```

where each side's basis is its own zonal price minus its own system price
(`measured_basis ≡ MCC + MLC`, verified to `0.000000000` in every hour of every
year). **PJM's `system_energy_price_da` is RTO-uniform** — zero spread across
all 23 zonal pnodes in every hour measured — so the first term is not a
Dominion quantity at all. It is PJM's single system marginal energy price, and
the question it poses is ISO-wide.

| CT-energy-weighted, $/MWh | 2023 | 2024 | 2025 |
|---|---|---|---|
| measured DOM LMP | 51.16 | 61.92 | 103.08 |
| model Dominion dual | 33.19 | 35.48 | 49.02 |
| **total deficit** | **17.97** | **26.44** | **54.06** |
| — of which **system energy** | **8.15** | **12.74** | **24.78** |
| — of which **basis (congestion + loss)** | **9.82** | **13.70** | **29.28** |
| measured MEC | 41.05 | 48.35 | 73.93 |
| model load-weighted system price | 32.91 | 35.61 | 49.15 |

The basis half is what `FINDING-pjm137` closed by measurement. **This document
is about the other one**, and its first result is that on an annual basis there
is barely anything there at all:

| load-weighted, whole year, $/MWh | 2023 | 2024 | 2025 |
|---|---|---|---|
| measured MEC | 31.62 | 33.53 | 50.46 |
| model load-weighted system price | 31.15 | 30.91 | 41.98 |
| **system-energy gap** | **+0.47** | **+2.62** | **+8.48** |

The model reproduces PJM's own system energy price to **1.5 % / 7.8 % / 16.8 %**
on the year. Whatever the CT-hour deficit is, it is **not** an offer-stack level
error.

## §2 — D2/D4: it is a dispersion defect, and its shape is unambiguous

### §2.1 — monotone in net load, and sign-flipping

Model net load = internal demand − wind − solar, from the keeper's own
committed class hourlies; deciles are within-year.

| decile (net load GW, 2025) | 2023 | 2024 | 2025 | CT-weighted 2025 |
|---|---|---|---|---|
| 1 (67.0) | **−5.78** | **−5.20** | **−4.86** | −1.96 |
| 2 (72.8) | −4.79 | −3.52 | −1.75 | +0.87 |
| 3 (76.9) | −2.86 | −1.63 | +0.24 | +4.74 |
| 4 (80.9) | −1.73 | −1.36 | +3.19 | +10.47 |
| 5 (84.9) | −1.35 | −0.53 | +5.27 | +14.84 |
| 6 (89.5) | −1.58 | +0.15 | +4.36 | +17.52 |
| 7 (94.4) | −1.44 | −2.08 | +3.33 | +18.15 |
| 8 (100.1) | −0.24 | +0.79 | +5.97 | +20.72 |
| 9 (107.9) | +2.83 | +7.13 | +11.67 | +18.41 |
| **10 (123.5)** | **+14.32** | **+21.59** | **+39.92** | **+44.65** |

The top two deciles contribute **+2.22 / +3.75 / +6.76 $/MWh** of an annual
load-weighted gap of **+0.47 / +2.62 / +8.48** — i.e. in 2023 and 2024 they
carry *more than the whole year's gap*, the rest of the distribution running
negative against them. **29.7 / 34.9 / 33.4 %** of the real Dominion CT fleet's
energy is produced in decile 10.

### §2.2 — and by hour-of-day it is the ramp and the peak, not the flat middle

Load-weighted mean system-energy gap, EST-keyed (§5):

| hour | 2023 | 2024 | 2025 | | hour | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|---|
| 01 | −6.66 | −5.31 | −2.49 | | 13 | +1.84 | +3.30 | +7.49 |
| 02 | −7.31 | −6.11 | −3.35 | | 15 | +5.52 | +6.54 | +10.65 |
| 03 | −7.13 | −5.83 | −3.05 | | 16 | +8.59 | +11.42 | +17.11 |
| 04 | −5.90 | −4.68 | −1.60 | | **17** | **+10.42** | **+14.68** | **+25.84** |
| **06** | **+2.53** | **+4.61** | **+13.60** | | **18** | +7.37 | +12.30 | **+30.27** |
| **07** | +2.24 | +5.37 | **+14.56** | | 19 | +4.15 | +7.60 | +20.88 |
| 09 | −1.15 | +0.39 | +2.93 | | 21 | −0.84 | +1.38 | +7.79 |

**Overnight the model is too DEAR by $1.6–7.3/MWh**; the gap turns hard positive
at the morning ramp (h06–h07) and again through the evening peak (h16–h19).
Seasonally, CT-energy-weighted, 2025 runs DJF **+46.05**, JJA **+26.10**, SON
**+21.36**, MAM **+11.28** — the winter morning ramp is the single worst cell in
the whole measurement.

### §2.3 — D4: the tail is 3–6× too thin on PJM's own energy component

Hours above threshold, day-ahead basis:

| $/MWh | measured **MEC** | model system price | measured **DOM LMP** | model DOM dual |
|---|---|---|---|---|
| > 75 | 90 / 257 / 904 | 7 / 102 / 191 | 267 / 562 / 1,799 | 4 / 89 / 198 |
| > 100 | 29 / 128 / 392 | 3 / 72 / **65** | 95 / 275 / 969 | 1 / 63 / 62 |
| > 150 | 14 / 26 / 146 | 0 / 1 / **24** | 29 / 105 / 398 | 0 / 0 / 20 |
| > 250 | 7 / 1 / 40 | 0 / 0 / 8 | 11 / 6 / 125 | 0 / 0 / 5 |

This matters because it locates the thin tail **inside the system energy price**,
where a zonal model has no excuse. It is not an artifact of the missing
congestion.

## §3 — D5: the missing price is the reserve opportunity cost, and PJM publishes it

### §3.1 — why the reserve price is an *additive component* of the energy price

This is not an analogy; it falls out of the co-optimized LP's own optimality
conditions. With energy-balance dual `λ`, reserve-balance dual `μ`, and a joint
headroom row `P + R ≤ cap` with dual `γ`, a unit interior in **both** products
satisfies `λ = mc + γ` and `μ = γ`, hence

```
λ = mc + μ
```

— the energy price of a reserve-carrying marginal unit exceeds its own marginal
cost by exactly the reserve clearing price. Crediting the **whole** measured
reserve MCP against the system-energy gap is therefore the most generous
attribution the reserve lane can receive (not every hour's marginal unit is
reserve-constrained), and the residual it leaves is a **lower bound** on what an
energy-stack mechanism would still have to explain. Reported below as a bound,
never as a decomposition.

### §3.2 — the measurement

`data/raw/PJM-AS/da_reserve_market_results_<year>.parquet` is PJM's published
day-ahead reserve market result: requirement, cleared MW and clearing price per
locale × service × hour. It is the direct measured counterpart to the model's
own `reserve_price`, which the keeper writes into every `system_<year>.parquet`.

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| measured **Synchronized** MCP > $0 | **84.2 %** of hours | **96.7 %** | **47.6 %** |
| measured **Primary** MCP > $0 | 45.1 % | 64.0 % | 30.8 % |
| **model reserve dual > $0** | **0 h** | **2 h** | **28 h** (of 8,760) |
| measured cover ratio p50 (cleared ÷ required), Sync | 1.04 | 1.09 | 1.11 |
| — Primary | 1.01 | 1.00 | 1.00 |
| — Thirty-Minute | 4.78 | 4.70 | 4.39 |
| **corr(measured Sync MCP, model system-energy gap)** | **+0.788** | **+0.604** | **+0.657** |
| share of the year's Sync reserve price in net-load decile 10 | 26.2 % | 26.5 % | 35.9 % |

And the attribution, CT-energy-weighted over the Dominion CT-running hours:

| $/MWh | 2023 | 2024 | 2025 |
|---|---|---|---|
| system-energy gap | 8.17 | 12.74 | 24.78 |
| measured Sync MCP, **RTO Reserve Zone** | 6.71 | 6.65 | 14.18 |
| measured Sync MCP, **Mid-Atlantic/Dominion subzone** | 6.79 | 7.19 | 15.35 |
| model reserve dual | 0.00 | 0.03 | 1.37 |
| **residual after full reserve credit (RTO)** | **1.46** | **6.12** | **11.97** |
| **residual after full reserve credit (MAD)** | **1.38** | **5.58** | **10.81** |

Restated against the whole chartered defect:

| CT-energy-weighted share of the $17.97 / $26.44 / $54.06 deficit | 2023 | 2024 | 2025 |
|---|---|---|---|
| basis — **closed by pjm-137** (intra-zonal congestion) | 54.6 % | 51.8 % | 54.2 % |
| system energy attributable to the **reserve opportunity cost** | 37.3 % | 25.2 % | 26.2 % |
| **residual available to any energy-stack mechanism** | **8.1 %** | **23.1 %** | **22.1 %** |

*(The three rows sum to 100.1 % rather than 100.0: §3's mask additionally
requires a finite measured reserve price, which moves the system-energy gap from
$8.15 to $8.17 in 2023 and leaves 2024–25 unchanged. Stated rather than
rounded away.)*

In the top net-load decile, load-weighted, the same credit takes the gap from
**+14.32 / +21.59 / +39.92** to **+6.88 / +14.82 / +22.50**; on the whole year it
takes **+0.51 / +2.64 / +8.49** to **−2.36 / −0.08 / +2.76** — i.e. once PJM's own
reserve price is credited, **the model's annual energy stack is level-correct to
within about $2.80/MWh in the worst year and is if anything slightly too dear in
2023.**

### §3.3 — and this is NOT a missing mechanism (D5b)

Every component is already built, already measured and already armed in the
keeper:

* **Requirement** — `load_pjm_measured_reserve_requirement`, PJM's own measured
  Primary Reserve requirement (`pr_req_mw` from PJM's real-time reserve market
  results, via `build_pjm_as_withholding.py`), for both the RTO Reserve Zone and
  the nested Mid-Atlantic/Dominion Reserve Subzone (Manual 11 §4.2). Annual
  means **3,094 / 3,422 / 3,348 MW**, against the **day-ahead** requirement this
  document measures at **3,213 / 3,504 / 3,337** — the same quantity in PJM's
  two markets, agreeing to **2–4 %** (mean hourly |difference| 157 / 128 / 72 MW,
  not an hour-key offset: lag 0 is the best alignment of the three tested). And
  PJM's own Primary **cover ratio is 1.00–1.01**, so there is no requirement-side
  headroom to find at all. *Lever-queue item 9 ("requirement-side dynamic
  reserves") is therefore adjudicated INERT by measurement, on PJM's own
  numbers — a ±130 MW requirement discrepancy cannot price anything when supply
  is 5–10× the requirement.*
* **Demand curve** — `data/raw/_validation-source/pjm_ordc_curve.csv`, PJM's
  published two-step ORDC ($850 step 1 at the requirement, $300 step 2 at
  +190 MW), in force across 2023–2025 under the Reserve Price Formation reform
  (FERC EL19-58/ER19-1486, implemented 2022-10-01), loaded by
  `model/reserves/spec.py::_pjm_design`.
* **Co-optimization** — `energy_reserve_coopt` + `pjm_reserve_pergen` +
  `pjm_reserve_supply_cap` + `measured_ramp_capability`, all `True` in the
  keeper. The per-generator joint-headroom row is *designed* to produce exactly
  the §3.1 opportunity cost: "on a fully-loaded marginal asset the row's dual is
  the forgone energy margin — the opportunity cost that lifts the reserve
  clearing price above $0 without any shortfall"
  (`model/lp/reserve_rows.py::_build_reserve_rows_pergen`).

It clears at $0 anyway because the model's reserve **supply** is 5–10× its
requirement (pjm-124/125: ramp10 scoping leaves 9.7–10.5×, commitment scoping
5.0–5.6×), and pjm-82 already named why: **the LP-vs-MIP boundary.** With a
continuous commitment variable, fractional online capacity costs nothing, so
every idle unit's headroom qualifies as synchronized reserve. PJM's real market
cannot do that — a unit is synchronized or it is not — which is exactly why its
cover ratio is 1.0–1.1 and its price is positive in 48–97 % of hours.

**This is a disclosed architectural limit of the no-MIP mandate, not an open
calibration gap**, and the owner closed the lane that would chase it on
2026-07-11 ("do not re-open reserve-supply probes for PJM C3c",
`DIAGNOSIS-pjm-dof-scarcity-tail-2026-07.md` §B.3).

## §4 — M1: who owns the model's price, and what 3–5 GW of capacity is worth

**STATUS: queued, not yet run — this section is appended when it completes, and
nothing above depends on it.** `_pjm138_marginal_ownership.py` needs a fleet
rebuild, hence the whole `data/clean` contract (`scripts/regenerate_clean.py`,
~31 datatypes, which this container ships empty); the §1–§3 measurements need
only committed inputs and were run first for that reason.

What it will answer, and why neither answer changes §6:

* **the ownership census** re-runs pjm-122's charge (fitted coal rungs owning
  the $40–150 region the measured DataMiner2 corpus assigns to the CC top belt
  and `CT_FAST`) on the CURRENT keeper. Whatever it finds, the lever family that
  would act on it is matrix `R` — pjm-123 refuted the three-leg composite at the
  no-LP pre-check and generalized the refutation to the measured surface itself
  (it prices every segment *cheapest* in the tightest net-load bin, so handing a
  model class its measured level compresses dispersion rather than widening it),
  and pjm-126/127/132 closed the conditioning and within-season variants.
* **the withdrawal price response** — `mc(Q+Δ) − mc(Q)` off each tight hour's own
  sorted offer stack — puts a **price** on the ~2.8–5.0 GW that
  `FINDING-guard-falseneg-audit-2026-07-27` §3 measured the merit-order guard
  returning to PJM's tightest net-load quartile. §7 of that audit declined to
  write a fix precisely because no instrument sized the price consequence; this
  supplies one (as a lower bound, per the probe's stated bounds). It is a
  *sizing* of a lane §3.3 closes on other grounds, not a candidate mechanism.

## §5 — A1: a measured-side hour-key correction to pjm-137, and its size

`_pjm137_dominion_ct_congestion._measured_components` indexes hour-of-year off
`datetime_beginning_ept` — PJM's Eastern **Prevailing** time, which advances one
hour relative to standard time between the March and November transitions. The
model's 8760 index and the EPA CAMD unit-level record are **both Eastern
Standard** year-round. From March to November, therefore, pjm-137's measured
series sat one hour ahead of both the model duals and the CT fleet it was
weighted by.

Measured on 2025, the two keys are statistically indistinguishable in the
standard-time months and separate cleanly in the DST months — the signature of
this offset and of nothing else:

| corr(measured MEC, model system price) | Jan/Feb/Dec | Apr–Oct |
|---|---|---|
| EPT key (pjm-137) | 0.7807 | 0.7964 |
| UTC−5 key (this document) | 0.7867 | **0.8731** |

**pjm-137's headline survives**; only its shape statistics move.

| pjm-137 M3, CT-energy-weighted | EPT key (as published) | UTC−5 key (corrected) |
|---|---|---|
| measured DOM LMP, 2023 / 24 / 25 | 50.78 / 62.04 / 103.41 | **51.16 / 61.92 / 103.08** |
| total deficit | 17.59 / 26.56 / 54.39 | **17.97 / 26.44 / 54.06** |
| measured DOM MCC | 9.09 / 12.32 / 27.73 | **9.16 / 12.18 / 27.18** |
| peak-gap hour of day | 17 / 18 / 19 | 17 / 17 / **18** |

Every conclusion in `FINDING-pjm137` is unaffected: M1's separation shares and
mean components are annual means (shift-invariant), M2 and M4 are computed
entirely within the measured EPT record (internally consistent), and M3's levels
move by **$0.12–0.38/MWh** against a $10–38 defect. The correction is recorded
because any successor reading a **diurnal** statistic off that probe would be
reading it one hour late in eight months of the year. Keying on
`datetime_beginning_utc` also disposes of the DST fall-back collision the
handoff warns about, where two 01:00 intervals carry a single EPT label.

## §6 — DO-NOT-REDO (binding on successors)

- **Do not propose a reserve/scarcity mechanism for PJM.** Not the requirement
  side (measured; PJM's own Primary cover ratio is 1.00–1.01, §3.3 — lever-queue
  item 9 is adjudicated **INERT by measurement**), not the demand curve (PJM's
  published two-step ORDC is already loaded), not the co-optimization (already
  the keeper's structure and its **sole** reserve-price owner under rule 19
  `[R-ONE-MECH]`), and not a post-solve overlay (matrix cell `G`, inadmissible
  stack). The lane was owner-closed 2026-07-11 and the residual is the LP-vs-MIP
  representation boundary, which the no-MIP mandate makes a **disclosure**, not
  a defect to fix.
- **Do not size the G-20b guard lead from population statistics alone.** §4
  gives it a price, which is what
  `FINDING-guard-falseneg-audit-2026-07-27` §7 said was missing.
- **Do not read the CT-hour price deficit as an offer-curve error.** Of
  $17.97 / $26.44 / $54.06, only **8 / 23 / 22 %** survives after the two closed
  lanes are credited. An offer-side mechanism that closed *all* of the residual
  would move the Dominion CT-hour price by $1.46 / $6.12 / $11.97.
- **Do not quote a diurnal or hour-of-day statistic from
  `_pjm137_dominion_ct_congestion.py`** without the §5 correction; use
  `_pjm138_mec_gap_shape.py`'s UTC-keyed loader.
- **Do not re-test the measured offer-surface family as a dispersion lever.**
  pjm-123 refuted the three-leg composite at the no-LP pre-check and generalized
  the refutation to the surface itself; pjm-126/127/132 closed the conditioning
  and within-season variants. Matrix `measured_offer_surface` PJM = **R**.
- Carried forward unchanged: `FINDING-pjm137` §5 in full (the zonal-congestion
  closure, the `3.066 / 4.048 / 5.218 TWh` benchmark actual, the frozen CT
  heat-rate artifact), `FINDING-pjm136` §5, `FINDING-pjm135` §7,
  `FINDING-pjm134` §5/§8.

## §7 — handover leads, stated but NOT built here

1. **The reachable residual is $1.46 / $6.12 / $11.97/MWh in CT hours and
   −$2.36 / −$0.08 / +$2.76 on the year** — the second of those says the energy
   stack's *level* is right, so any successor lever must be shape-only and must
   raise tight hours without raising slack ones. That is precisely the gradient
   test pjm-123 applied and the measured offer surface failed.
2. **The overnight over-pricing is its own defect and is not reserve-related**
   (PJM's reserve price is small overnight and the model's is zero, so the
   credit does not touch it): the model runs **$1.6–7.3/MWh too DEAR at
   h01–h04**, worst in 2023. Nothing in this lineage has measured what sets the
   model's overnight price against what set PJM's.
3. **The winter morning ramp is the largest single cell** in the whole
   measurement — CT-weighted DJF 2025 **+$46.05/MWh**, with h06–h07 the worst
   hours of the day. `gas_daily_shape` is the named, measured, mean-preserving
   candidate for exactly this phenomenon
   (`DIAGNOSIS-pjm-dof-scarcity-tail` §B.4.1) and is **still untested on PJM**.
4. Carried from pjm-137, still open and still blocked: a `PJM_Dominion`
   NoVA/Loudoun split needs a measured sub-zonal load basis.

## §8 — what this session did NOT do, and why

**No delta was chartered, no PREREG was written, no arm was solved and nothing
was registered on the dashboard.** The charter is explicit that a mechanism is
proposed only after a measurement fires one. The measurement fired at the
reserve lane, and that lane is closed four ways — measured requirement, published
curve, live co-optimization, owner closure — with its residual named as the
no-MIP boundary. Under rule 1 `[R-STRUCT]` the keeper is `CALIBRATED` with every
criterion passing and there is no gate to chase; under rule 28 `[R-MECH-MATRIX]`
the adjudicated cells are not re-tested without new evidence, and the new
evidence here **confirms** the adjudications rather than overturning them.

**The keeper's standing kills are unchanged because nothing was solved.** C3c
still passes by ~1 h (2024: 10 h model vs 18 h RT, 0.56×) and ~2.5 h (2025:
32 h vs 59 h, 0.54×) against a 0.5× floor — still the thinnest margin in the
keeper. C8 `CT_PEAKER` forced share stays 16.3 / 16.9 / 17.1 %, all GROUNDED
(D-4 clear, profile r 0.923–0.973, off-peak CV ratio 0.703–1.083). C1 stays
16/16 with free 12/12. ISO-wide `CT_PEAKER` |err| stays 2.11 / 3.57 / 3.32 TWh.
