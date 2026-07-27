# FINDING — caiso-128: the CT offer heat rate is wrong, but not the way the lead said and not by enough to matter — the model's CT_PEAKER base rate is **+8 %** over its own measured CEMS rate (not +36 %), the remaining +15 % is a **measured DAM bid multiplier** that is real market conduct, and the eGRID annual-average basis is an **ISO-generic** defect whose big victims are CT_CHP (+46 %) and ST_GAS (+40 %), not CT_PEAKER

**Keeper `2026-07-27-caiso-126-ror-split` UNCHANGED. Derive/measurement session —
no mechanism armed, no A/B, nothing registered.** The owner lead
("CT peakers never run in my model when they do in reality … the offer heat
rates are 27–54 % above their own measured CEMS rates") is **partly refuted on
measurement**, and the refutation changes what the lane should build. This
document is the evidence; the design that follows from it is §6.

Instruments (committed, no LP built or solved):
`scripts/probes/_caiso128_heat_rate_source_audit.py` (this session — provenance,
cross-class, cross-ISO, coverage, stability, CF tilt) and the pre-existing
`scripts/probes/_caiso128_ct_peaker_attribution.py`. Every number below is
reproducible from `data/raw/` primary sources (CAMPD unit-level CEMS, the three
eGRID vintages, EIA-860) plus the model's own fleet loader — no bundle needed
for §1–§4.

---

## §1 — TASK 1: where the offer heat rate actually comes from (the lead, tested)

The lead nominated the `HEAT_RATE_BINS` fuel × vintage fallback (a poor
description of an LMS100/LM6000 aeroderivative). **Measured: it is not the
story.** The provenance chain, read off the code and then measured:

1. **EIA-860 carries no heat rate at all.** `eia860_generator_operable.parquet`
   has no such column; the Generator_Y schedule does not publish one.
2. `scripts/data/process_eia860._join_egrid_heat_rate` fills the model's
   `eia860_generators.parquet` `heat_rate` column from **eGRID PLNT23
   `PLHTRT`** — a plant-level **annual, all-fuel average** (`PLHTIAN /
   PLNGENAN`), mapped onto *every* generator at the plant, filtered to a
   3,000–30,000 Btu/kWh window.
3. `fleet/eia860._rows_to_generators` prefers that value; only where it is
   missing does `HEAT_RATE_BINS[fuel_type][efficiency_bin]` fire.
4. `fleet/eia860._egrid_boundary_hr_repairs` — the one eGRID reconciliation —
   is **scoped to `Natural Gas Fired Combined Cycle`** (`cc_codes`), so no
   simple-cycle plant is ever repaired. The lead's reading of this scope is
   correct; it is just not where the CT error comes from.

**The bin-fallback split (the lead's hypothesis), CAISO:**

| class | gens | on-bin | MW | MW on-bin | **% MW on bin** |
|---|---|---|---|---|---|
| CT_PEAKER | 282 | 111 | 7 616 | 860 | **11 %** |
| CC_REGULAR | 92 | 10 | 13 677 | 1 743 | 13 % |
| CT_CHP | 136 | 7 | 1 962 | 15 | 1 % |
| CC_CHP | 56 | 3 | 2 707 | 130 | 5 % |
| ST_GAS | 6 | 0 | 2 859 | 0 | 0 % |

**89 % of CT_PEAKER capacity carries a real eGRID rate, not a bin.** The
fallback is a 11 %-of-MW tail on the smallest plants. **Lead refuted as the
primary cause** — but see §2, which finds a real defect in the eGRID rate the
other 89 % carries.

## §2 — TASK 1b: the +27–54 % decomposes into +8 % of error and +15 % of *real conduct*

The prompt's per-plant gaps were measured as **cheapest-tranche** heat rate vs
CEMS. A tranche heat rate is `base_HR × band_multiplier`, so that comparison
conflates the cost input with the offer markup. Separated:

| plant | zone | model **base** HR | cheapest **tranche** HR | CEMS `hr_load` | base vs CEMS | tranche vs CEMS |
|---|---|---|---|---|---|---|
| Panoche Energy Center (56803) | NP15 | 9.35 | 10.75 | 8.65 | **+8 %** | +27 % |
| Sentinel Energy Center (57482) | LA_BASIN | 9.56 | 11.00 | 8.76 | **+9 %** | +31 % |
| Walnut Creek (57515) | LA_BASIN | 9.30 | 10.70 | 8.48 | **+10 %** | +27 % |
| Marsh Landing (57267) | NP15 | 11.60 | 13.33 | 10.58 | **+10 %** | +31 % |
| Gilroy Peaking (55810) | NP15 | 11.58 | 13.32 | 9.14 | **+27 %** | +54 % |

The tranche/base ratio is **1.147** on every plant. That is not a modelling
artifact and not a fitted knob: it is `caiso_offer_curve_measured.json`'s
`CT_PEAKER.bands.econ_low = 1.147`, the **cap-weighted median of the CAISO CT
fleet's own OASIS DAM energy bids** (`scripts/data/derive_caiso_offer_surface.py`,
armed in the keeper by `caiso_offer_surface_measured=True`). `econ_high` is
1.182 — which reproduces the prompt's "Sentinel runs 11.00 → 11.28 across
tranches" exactly (9.56 × 1.147 = 10.97; 9.56 × 1.182 = 11.30).

**A bid above marginal cost is the market, not an error.** Real CT operators bid
a start-cost/opportunity hurdle into their energy curve, and the model is
reproducing the *measured* one. So of the headline 27–54 %:

* **~+15 % is measured bid conduct** — correct, rule-13-admissible, and the
  thing `caiso_offer_surface_measured` exists to carry;
* **~+8–10 % is a genuine input error** — §3.

## §3 — the real defect: eGRID `PLHTRT` is an ANNUAL ALL-FUEL AVERAGE

`PLHTRT = PLHTIAN / PLNGENAN` — every MMBtu the plant burned in the year,
including **startup, shutdown and part-load fuel**, over its net generation. An
energy offer must carry the *loading-conditional* (near-full-load) rate, because
**the model already charges startup cost separately** — so the incumbent input
double-counts start fuel into the energy offer.

CAISO 2024, cap-weighted, model offer base HR vs CAMPD CEMS (`hr_load` = heat
input / gross load over full-clock hours, `opTime ≥ 0.99`, above half the
*unit's* own observed peak):

| class | GW | % MW on bin | model | eGRID24 | `hr_all` | `hr_load` | **vs `hr_load`** |
|---|---|---|---|---|---|---|---|
| CC_CHP | 2.7 | 5 % | 6.82 | 6.76 | 7.12 | 7.12 | −4 % |
| CC_REGULAR | 13.7 | 13 % | 7.54 | 7.53 | 7.39 | 7.34 | **+3 %** |
| **CT_CHP** | 2.0 | 1 % | 13.63 | 6.70 | 8.98 | 9.31 | **+46 %** |
| **CT_PEAKER** | 7.6 | 11 % | 10.83 | 10.77 | 9.01 | 9.99 | **+8 %** |
| **ST_GAS** | 2.9 | 0 % | 11.85 | 11.15 | 10.02 | 8.47 | **+40 %** |

**CC_REGULAR at +3 % is the control that proves the mechanism.** A high-CF
baseload plant starts rarely, so its annual average ≈ its loading-conditional
rate and eGRID is accurate. The error appears exactly where duty cycle is low.

**The CF tilt WITHIN CT_PEAKER is flat, though** — the error does not
concentrate on the plants that never run:

| CF quartile | n | CF | model | `hr_load` | err |
|---|---|---|---|---|---|
| Q1 low | 11 | 0.012 | 12.67 | 11.86 | +7 % |
| Q2 | 11 | 0.022 | 11.28 | 9.83 | +15 % |
| Q3 | 11 | 0.030 | 11.03 | 10.21 | +8 % |
| Q4 high | 11 | 0.095 | 9.83 | 9.17 | +7 % |

Spearman rank corr(CF, err) = **+0.026**. So correcting the rate is a **level**
correction within the class, not a merit-order re-ordering — the hypothesis that
it would differentially cheapen the idle peakers is **refuted**.

**CT_CHP is a different defect entirely** and the largest one. eGRID reports a
*steam-credited* rate (6.70), and `data/chp._correct_chp_steam_credit_hr`
multiplies it by the hand **`CAISO_EOR_TOPPING_FACTOR = 1.8`** to recover a
power-only rate → 13.63, where the plant's own CEMS power-only rate is **9.31**.
A 1.8× estimate is standing in for a measurement that is on disk. This is the
cleanest rule-14 `[R-ACCURATE]` case in the fleet.

**ST_GAS** is the three OTC/RMR steamers (Alamitos / Huntington Beach / Ormond
Beach, 2.9 GW). They run rarely and at part load, so their annual average (10.02)
badly overstates their full-load rate (8.47).

## §4 — TASK 2(d): the defect is ISO-GENERIC (rule 25 — do NOT scope to CAISO)

2024, cap-weighted `model vs hr_load`, all six ISOs:

| class | CAISO | ERCOT | PJM | MISO | NYISO | NEISO |
|---|---|---|---|---|---|---|
| CC_REGULAR | +3 % | 0 % | +2 % | +1 % | +5 % | −14 % |
| **CT_PEAKER** | **+8 %** | +1 % | +4 % | +7 % | +4 % | +4 % |
| **ST_GAS** | **+40 %** | +12 % | +24 % | +11 % | +18 % | +31 % |
| **COAL** | — | +13 % | +14 % | +11 % | — | −19 % |
| CC_CHP | −4 % | **−29 %** | −17 % | **−29 %** | −13 % | −28 % |
| CT_CHP | **+46 %** | **−57 %** | −12 % | −14 % | −25 % | **−54 %** |

Three generic patterns, all consistent with §3's mechanism:

1. **CC_REGULAR is accurate in five of six ISOs** — the high-duty control holds
   everywhere.
2. **The low-duty classes are over-stated everywhere** — CT_PEAKER +1…+8 %,
   ST_GAS +11…+40 %, COAL +11…+14 %. Same sign, same cause, every ISO.
3. **CHP is broken in both directions.** Where the steam-credit correction is
   NOT armed the model *under*-states by 12–57 % (ERCOT CT_CHP −57 %, NEISO
   −54 %); where CAISO's 1.8× *is* armed it *over*-states by +46 %. A hand factor
   cannot be right in both places — only the plant's own measurement can.

**CAISO's CT_PEAKER +8 % is the worst of the six but the same order as the
rest.** A CAISO-scoped literal would be a rule-25 `[R-ISO-SCOPE]` violation.

**Coverage and stability of the replacement input (CAISO):**

| class | plants | covered | GW | GW covered | % MW | cross-year `r` | median CV |
|---|---|---|---|---|---|---|---|
| CT_PEAKER | 134 | 44 | 7.62 | 5.99 | **79 %** | 0.904 | **0.009** |
| CC_REGULAR | 28 | 22 | 13.68 | 11.49 | 84 % | 0.747 | 0.005 |
| ST_GAS | 3 | 3 | 2.86 | 2.86 | **100 %** | 0.999 | 0.014 |
| CC_CHP | 21 | 6 | 2.71 | 1.38 | 51 % | 0.998 | 0.009 |
| CT_CHP | 71 | 7 | 1.96 | 0.34 | **17 %** | 0.906 | 0.038 |

A median per-plant coefficient of variation of **0.9 %** across 2023–2025 says
`hr_load` is a stable *physical property*, not a noisy annual statistic — which
is what makes it forward-derivable (rule 13). CT_CHP's 17 % coverage is the one
weak spot: most CT_CHP capacity is small BTM cogen below the CEMS threshold, so
that class stays mostly on the incumbent chain whatever we do.

**One real basis mismatch, disclosed:** the model dispatches **net** MW (`pmax`
is net summer capability) while CEMS `grossLoad` is **gross**. CAISO CT_PEAKER's
cap-weighted CEMS-gross / eGRID-net ratio is **0.948** (p50 0.964), i.e. a
gross-basis rate understates fuel per net MWh by a few percent. It is small
against the +8…+46 % it would correct, but it is a real rule-14 "different
boundary" case and a reconciliation belongs in the build (§6).

## §5 — the load-bearing consequence: **this fix cannot deliver the lane's PRIMARY**

The prompt pre-registered `CT_PEAKER energy 0.42 → toward 3.30 TWh` and
`C5a gas deficit narrows`. **Measurement says a heat-rate correction cannot
produce that, and it would be dishonest to solve toward it.** Three reasons:

1. **The CT offer is bid-pinned, not cost-pinned.** With
   `caiso_offer_surface_measured` armed (it is, in the keeper), the CT_PEAKER
   `econ_low/econ_high/peak` offers are `mult × base_HR_class × gas + VOM +
   carbon`, where `mult` was **derived by dividing the measured DAM bid by that
   same `base_HR_class` (10.862)**. The product round-trips the measured bid by
   construction. Lower `base_HR` and leave `mult` alone and the model offers
   **below** a measured bid — that is not an accuracy gain, it is a rule-13
   regression dressed as one. Lower `base_HR` and re-derive `mult` (the correct
   move — the *bid* is the measurement, the multiplier is only its
   representation) and the offer level is **unchanged at the class level**.
2. **The within-class CF tilt is flat** (+0.026), so there is no merit-order
   re-ordering to harvest either — the plants that never clear are not the ones
   being differentially over-priced.
3. **A per-plant measured bid is impossible.** The OASIS public bids are
   **masked** — `derive_caiso_offer_surface.py` states it: *"The masked ids
   cannot be plant-mapped, so the derive is per-CLASS only (the charter's
   'plant?' resolves to NO)."* So the fleet-median multiplier applied per plant
   cannot be refined into per-plant conduct from this source.

The `_caiso128_ct_peaker_attribution` evidence is consistent with this and points
elsewhere: reality reaches the model's **own** cheapest CT offer 1.3–1.6× as
often as the model's λ does (0.442/0.204/0.131 vs 0.334/0.130/0.084). That is a
**λ-side** deficiency — the model serves the evening from a flat
CC_REGULAR/import continuum whose next rung is a median **+0.59 $/MWh** away
(FINDING-caiso127 §4) — not a CT-offer-level deficiency. And FINDING-caiso127 §2
established that on 53–76 % of days the storage pin re-equalizes any such rung
anyway.

**So: the heat-rate correction is worth making because it is more accurate
(rule 14 `[R-ACCURATE]`, rule 1 `[R-STRUCT]` — "never revert to an estimate
because it fits better", and equally never *claim* an accuracy fix as a
dispatch fix). It is NOT the CT under-dispatch fix, and it must not be
pre-registered as one.**

## §6 — TASK 2: the design that follows (filed, not built)

**One mechanism (rule 19 `[R-ONE-MECH]`): replace the model's offer heat rate
with each plant's own CEMS loading-conditional measured rate wherever CEMS
covers it.** That single swap subsumes all three defects above — the eGRID
annual-average basis, the 1.8×/1.15× CHP topping-factor estimates, and the
`HEAT_RATE_BINS` tail — instead of stacking three corrections.

* **Input.** Per plant-year, from CAMPD unit-level: `Σ heatInput / Σ grossLoad`
  over unit-hours with `opTime ≥ 0.99` and `grossLoad > 0.5 × unit peak`,
  reconciled gross→net by the plant's own measured CEMS-gross / eGRID-net ratio
  (rule 14's named "different boundary" exception — a *reconciled* real value,
  never a guess).
* **Fallback where CEMS does not cover** (CT_CHP's 83 %, new entrants): the
  existing chain, unchanged — eGRID `PLHTRT`, then `HEAT_RATE_BINS`. No new
  fallback estimator, so no new free parameter.
* **Zero fitted parameters** (rule 24 `[R-REGISTRY]`). `opTime ≥ 0.99` and the
  half-peak load gate are *definitional* — they define "full-clock, near-full-
  load" — not thresholds swept against a residual. Both are frozen at derive
  time (rule 23 `[R-FROZEN-DERIVE]`).
* **Forward story (rule 13 `[R-MEASURED]`), exactly the CO2-rate precedent** in
  `data/emission_rates.py` (`docs/handoffs/emissions-co2-rate-plan-2026-07.md`):
  backcast years consume the target year's measured rate; forecast years consume
  a gen-weighted trailing average of the plant's own CAMPD history with a
  class-median fallback. The quantity regenerates for a forward year from
  forward drivers and responds to changed operation — it passes the
  admissibility test, and its 0.9 % cross-year CV says it is stable enough to
  carry.
* **ISO-generic** (rule 25 `[R-ISO-SCOPE]`): one gate, no per-ISO literal — §4
  shows the defect in all six.
* **Gated, default off, byte-identical off.**
* **Paired multiplier re-derive, mandatory.** Because
  `caiso_offer_curve_measured.json`'s multipliers are *defined as*
  `bid / (base_HR_class × gas)`, re-basing `base_HR` requires re-deriving them so
  the measured **bid** — the actual measurement — stays invariant. This is a
  *definitional* re-derive, not a residual-driven one, and rule 23 is satisfied
  because the source bid data is untouched; the commit must say so explicitly.
  The same applies to any other artifact keyed on `base_HR`.

**Honest expected effect, pre-registered as such:** CT_PEAKER offers ~unchanged
(bid-pinned, §5); the real movement is in CT_CHP (−32 % HR), ST_GAS (−29 %),
the un-armed `committed`/`mustrun` bands, the **CO2 emission rate**
(`get_emission_rate = heat_rate × fuel factor`), the **economic-retirement**
screen's variable cost, and the forecast path. λ will move where CT_CHP and
ST_GAS are marginal. **C3a is the kill guard**, exactly as the prompt specified.

## §7 — DO-NOT-REDO (this lane)

* Re-testing the `HEAT_RATE_BINS` fallback as the CT cause (§1 — 11 % of MW).
* Re-measuring the provenance chain, the cross-class/cross-ISO error table, the
  coverage/stability table or the CF tilt (§1–§4; instrument committed).
* Proposing a **per-plant measured DAM bid** multiplier for CAISO (§5 — the
  OASIS ids are masked; the derive's own charter resolves it NO).
* Re-basing `base_HR` **without** re-deriving the measured bid multipliers
  (§5/§6) — it lowers the model's offer below a measured bid and would read as
  an accuracy gain while being a rule-13 regression.
* Pre-registering a heat-rate correction against `CT_PEAKER energy → 3.30 TWh`
  or against C5a (§5 — the offer is bid-pinned and the CF tilt is flat).
* Treating the CT under-dispatch as an offer-**level** defect at all: the
  measured evidence (reality reaches the model's own CT offer 1.3–1.6× as often)
  makes it a λ-side/rung-continuum question, already owned by
  FINDING-caiso127 §4 and gated behind the storage pin (§2 there).
* A fitted heat-rate multiplier, offset or threshold tuned to the CT residual
  (rules 13/24) — the measured rate is on disk.

Next number: caiso-129.
