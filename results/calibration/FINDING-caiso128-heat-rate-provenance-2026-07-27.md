# FINDING — caiso-128: the CT offer heat rate is **NOT** wrong — on a consistent NET basis the model's CT_PEAKER rate matches its own measured CEMS rate to **0 %** in all six ISOs, the reported "+27–54 %" is a **net-vs-gross basis artifact plus a real measured DAM bid multiplier**, and the one large ISO-generic heat-rate defect that survives is **CHP** (CAISO CT_CHP +40 %, five ISOs' CHP −12 to −62 %)

**Keeper `2026-07-27-caiso-126-ror-split` UNCHANGED. Derive/measurement session —
no mechanism armed, no A/B, nothing registered.** The owner lead
("the CT classes' offer heat rates are 27–54 % above their own measured CEMS
rates, which is why 2.9 TWh/yr of CT_PEAKER energy never clears") is
**REFUTED on measurement**. The TASK 2/3 build it authorized is therefore **not
built** — it would have been a fix to a defect that is not there. What the same
instrument *did* find is a real, large, ISO-generic heat-rate defect in a
different place (§4), filed as a design in §6.

Instrument (committed, no LP built or solved):
`scripts/probes/_caiso128_heat_rate_source_audit.py`. Every number below is
reproducible from `data/raw/` primary sources — CAMPD unit-level CEMS, the three
eGRID vintages, EIA-860 — plus the model's own fleet loader. No bundle is needed
for §1–§5.

---

## §1 — TASK 1: the provenance chain, and the bin-fallback lead

The lead nominated the `HEAT_RATE_BINS` fuel × vintage fallback (a poor
description of an LMS100/LM6000 aeroderivative). **Measured: not the story.**

1. **EIA-860 carries no heat rate at all** — the Generator_Y schedule publishes
   none, and `eia860_generator_operable.parquet` has no such column.
2. `scripts/data/process_eia860._join_egrid_heat_rate` fills the model's
   `eia860_generators.parquet` `heat_rate` from **eGRID PLNT23 `PLHTRT`**
   (`PLHTIAN / PLNGENAN`), plant-level, mapped to every generator at the plant.
3. `fleet/eia860._rows_to_generators` prefers that value; `HEAT_RATE_BINS`
   fires only where it is missing.
4. `fleet/eia860._egrid_boundary_hr_repairs` is scoped to
   `Natural Gas Fired Combined Cycle`, so no simple-cycle plant is ever
   repaired. **The lead's reading of that scope is correct** — it is simply not
   the source of any CT error, because there is no CT error (§3).

**Bin-fallback split, CAISO:**

| class | gens | on-bin | MW | MW on-bin | **% MW on bin** |
|---|---|---|---|---|---|
| CT_PEAKER | 282 | 111 | 7 616 | 860 | **11 %** |
| CC_REGULAR | 92 | 10 | 13 677 | 1 743 | 13 % |
| CT_CHP | 136 | 7 | 1 962 | 15 | 1 % |
| CC_CHP | 56 | 3 | 2 707 | 130 | 5 % |
| ST_GAS | 6 | 0 | 2 859 | 0 | 0 % |

**89 % of CT_PEAKER capacity carries a real eGRID rate.** Lead refuted.

## §2 — the reported gap decomposes into TWO non-defects

The prompt's per-plant numbers (Sentinel 11.00 vs 8.41, +31 %) compared the
model's **cheapest tranche** heat rate against a **gross-basis** CEMS rate. Both
sides of that comparison are wrong for the question being asked.

**(a) The tranche/base ratio is a MEASURED BID, not a cost error.** Every CAISO
CT plant's cheapest tranche sits at exactly **1.147 ×** its base rate — that is
`caiso_offer_curve_measured.json`'s `CT_PEAKER.bands.econ_low`, the cap-weighted
median of the CT fleet's own **OASIS DAM energy bids**
(`scripts/data/derive_caiso_offer_surface.py`, armed in the keeper by
`caiso_offer_surface_measured=True`). `econ_high` is 1.182, which reproduces the
prompt's "Sentinel runs 11.00 → 11.28" exactly (9.56 × 1.147 = 10.97;
9.56 × 1.182 = 11.30). **A bid above marginal cost is the market, not an error** —
real CT operators bid a start-cost/opportunity hurdle into their energy curve,
and the model is reproducing the measured one.

**(b) The remaining gap is a NET-vs-GROSS basis mismatch.** eGRID `PLHTRT` is
`PLHTIAN / PLNGENAN` — heat input per **NET** MWh — and the model dispatches
**net** MW (`pmax` is net summer capability). CEMS reports **gross** load.
Comparing the model's net-basis rate to a gross-basis CEMS rate understates the
measured side by the entire auxiliary-load fraction and manufactures a spurious
"the model is too high".

The gross→net ratio is measured **same-year**, per plant, and is validated by
**two independent derivations off different field pairs**:

| CAISO class | 2023 `r_gen` = CEMS gross / eGRID net | 2023 `r_hr` = PLHTRT / CEMS gross-basis HR | 2024 `r_gen` | 2024 `r_hr` |
|---|---|---|---|---|
| CT_PEAKER | **1.193** | **1.195** | **1.180** | **1.181** |
| CC_REGULAR | 1.036 | 1.035 | 1.043 | 1.040 |
| ST_GAS | 1.047 | 1.064 | 1.041 | 1.044 |

Agreement to three decimals is not a coincidence and it carries a second
conclusion: `r_hr = (heat_eGRID / heat_CEMS) × (gross / net)` equals `r_gen`
only if `heat_eGRID = heat_CEMS`, so eGRID's heat input **is** CEMS's heat
input — there is no plant-vs-facility boundary mismatch inflating the ratio.
(A CEMS facility covering *more* units than the eGRID plant would push the two
estimates apart, not together.) CAISO CTs carry a genuine ~18 % parasitic load —
consistent with an LMS100 fleet's intercoolers, fuel-gas booster compressors and
desert inlet chilling.

## §3 — the headline: on a consistent NET basis the CT heat rate is RIGHT

2024, cap-weighted, model offer base rate vs CEMS put on the model's own net
basis (`× g2n`):

| ISO | class | model | annual NET | loading-cond. NET | **vs annual** | vs loading-cond. |
|---|---|---|---|---|---|---|
| CAISO | **CT_PEAKER** | 10.29 | 10.28 | 11.34 | **0 %** | −9 % |
| ERCOT | CT_PEAKER | 11.00 | 11.35 | 11.90 | **−3 %** | −8 % |
| PJM | CT_PEAKER | 11.32 | 11.34 | 11.72 | **−0 %** | −3 % |
| MISO | CT_PEAKER | 11.93 | 11.91 | 12.13 | **0 %** | −2 % |
| NYISO | CT_PEAKER | 11.35 | 11.25 | 12.19 | **+1 %** | −7 % |
| NEISO | CT_PEAKER | 10.13 | 10.02 | 11.34 | **+1 %** | −11 % |

**Zero error, in every ISO.** And against the *loading-conditional* rate the
model is **−2 to −11 %**, i.e. if anything its CT offers are slightly too
**cheap** relative to full-load cost — the opposite of the lead's direction, and
one more reason the CT under-dispatch cannot be a heat-rate story.

The same table for the other classes (2024, net basis, cap-weighted, model vs
annual-NET):

| class | CAISO | ERCOT | PJM | MISO | NYISO | NEISO |
|---|---|---|---|---|---|---|
| CC_REGULAR | −2 % | −4 % | −2 % | −3 % | −2 % | −16 % |
| COAL | — | +1 % | +1 % | −1 % | — | — |
| ST_GAS | **+15 %** | +1 % | +6 % | +2 % | +7 % | — |
| **CC_CHP** | **−13 %** | **−38 %** | **−19 %** | **−33 %** | **−22 %** | **−35 %** |
| **CT_CHP** | **+40 %** | **−62 %** | **−12 %** | **−33 %** | **−30 %** | — |
| **ST_CHP** | — | — | **−56 %** | **−41 %** | — | — |

**CC_REGULAR, CT_PEAKER and COAL are accurate everywhere.** The incumbent eGRID
input is doing its job for every non-CHP class. The defect is CHP — and, on
CAISO only, ST_GAS.

## §4 — what IS broken: CHP, in both directions, in every ISO

eGRID reports CHP plants at a **steam-credited** rate (fuel allocated between
power and process steam), which is not a power-only energy-offer rate.
`data/chp._correct_chp_steam_credit_hr` corrects for that with **hand factors** —
`CAISO_EOR_TOPPING_FACTOR = 1.8` for CT_CHP, `1.15` with a 6.3 floor for
CC_CHP — and only for the ISOs in `CHP_STEAM_CREDIT_HR_CORRECTION_ISOS`
(CAISO, PJM).

The result is a hand factor that is wrong in both directions at once:

* **Where it is armed it over-corrects.** CAISO CT_CHP: eGRID 6.70 × 1.8 =
  ~13.8 model, against a CEMS-measured power-only net rate of **11.58** →
  **+40 %**.
* **Where it is not armed the model under-states badly.** ERCOT CT_CHP −62 %,
  NEISO CC_CHP −35 %, MISO CC_CHP −33 %, PJM ST_CHP −56 %.

A single universal topping factor cannot be right in both places. Each plant's
own CEMS `heatInput / grossLoad` **is** its power-only rate (steam is a
co-product, not netted from CEMS heat input), so the measurement that would
replace the estimate is already on disk. This is a textbook rule-14
`[R-ACCURATE]` case: *"prefer accurate/measured data over estimates whenever it
is available."*

**CAISO ST_GAS (+15 % annual, +33 % loading-conditional)** is the second real
gap — the three OTC/RMR steamers (Alamitos / Huntington Beach / Ormond Beach,
2.9 GW), which run rarely and at part load.

**Coverage of the replacement input is the binding constraint**, and it is worst
exactly where the defect is worst:

| CAISO class | plants | covered | GW | GW covered | **% MW** | cross-year `r` | median CV |
|---|---|---|---|---|---|---|---|
| ST_GAS | 3 | 3 | 2.86 | 2.86 | **100 %** | 0.999 | 0.014 |
| CC_REGULAR | 28 | 22 | 13.68 | 11.49 | 84 % | 0.747 | 0.005 |
| CT_PEAKER | 134 | 44 | 7.62 | 5.99 | 79 % | 0.904 | 0.009 |
| CC_CHP | 21 | 6 | 2.71 | 1.38 | 51 % | 0.998 | 0.009 |
| **CT_CHP** | 71 | 7 | 1.96 | 0.34 | **17 %** | 0.906 | 0.038 |

A median per-plant coefficient of variation of **0.9 %** across 2023–2025 says
the measured rate is a stable *physical property*, not a noisy annual statistic —
which is what would make it forward-derivable (rule 13). But **CT_CHP is only
17 % covered**: most CT_CHP capacity is small behind-the-meter cogen below the
CEMS reporting threshold, so a measured swap can only reach a sixth of the class
that carries the +40 % error.

## §5 — why the lane's registered PRIMARY was unreachable regardless

Even if the heat rate had been wrong, the pre-registered PRIMARY
(`CT_PEAKER energy 0.42 → toward 3.30 TWh`, `C5a narrows`) could not have been
delivered by correcting it:

1. **The CT offer is bid-pinned, not cost-pinned.** With
   `caiso_offer_surface_measured` armed, the CT_PEAKER `econ_low/econ_high/peak`
   offers are `mult × base_HR_class × gas + VOM + carbon`, and `mult` was
   **derived by dividing the measured DAM bid by that same `base_HR_class`
   (10.862)**. The product round-trips the measured bid by construction. Lower
   the base and leave `mult` alone and the model offers *below* a measured bid —
   a rule-13 regression dressed as an accuracy gain. Lower the base and
   re-derive `mult` — the correct move, since the *bid* is the measurement — and
   the offer level is unchanged.
2. **The within-class CF tilt is flat.** Spearman rank corr(CF, error) =
   **+0.026** across the CAISO CT fleet (error by CF quartile: +7/+15/+8/+7 %),
   so there is no merit-order re-ordering to harvest — the plants that never
   clear are not the ones differentially over-priced.
3. **A per-plant measured bid is unavailable.** The OASIS public bids are
   **masked**; `derive_caiso_offer_surface.py` states it outright — *"The masked
   ids cannot be plant-mapped, so the derive is per-CLASS only (the charter's
   'plant?' resolves to NO)."*

The `_caiso128_ct_peaker_attribution` evidence points where FINDING-caiso127 §4
already put it: reality reaches the model's **own** cheapest CT offer 1.3–1.6× as
often as the model's λ does (0.442/0.204/0.131 vs 0.334/0.130/0.084). That is a
**λ-side** deficiency — the model serves the evening from a flat
CC_REGULAR/import continuum whose next rung is a median **+0.59 $/MWh** away —
not a CT-offer-level one. And FINDING-caiso127 §2 showed that on 53–76 % of days
the storage pin re-equalizes any such rung anyway.

## §6 — the design that the surviving defect deserves (filed, NOT built)

Not built, because it targets a defect the owner did not authorize a build for,
its dominant class is 17 %-covered, and the paired re-derive in (e) needs an
owner call. Filed so the next session starts from a design, not a search.

**One mechanism (rule 19 `[R-ONE-MECH]`): replace the CHP steam-credit hand
factors with each plant's own CEMS power-only rate where CEMS covers it.**

* **(a) Input.** Per plant-year from CAMPD unit-level:
  `Σ heatInput / Σ grossLoad` over unit-hours with `opTime ≥ 0.99` and
  `grossLoad > 0.5 × unit peak`, then **× the plant's own same-year measured
  gross→net ratio** (§2) to land on the model's net basis. The basis
  reconciliation is not optional — it is what this session got wrong first, and
  it is rule 14's named "different boundary" exception: a *reconciled* real
  value, never a guess.
* **(b) Scope.** CHP classes (`CC_CHP`, `CT_CHP`, `ST_CHP`) — the only classes
  with a measured defect. `CT_PEAKER`, `CC_REGULAR` and `COAL` are **explicitly
  out of scope**: §3 measures them accurate, and rule 1 forbids changing a
  correct input to chase a residual.
* **(c) Fallback where CEMS does not cover** (CT_CHP's 83 %): the existing chain
  unchanged — eGRID `PLHTRT` then the hand factor. No new estimator, no new
  free parameter.
* **(d) Zero fitted parameters** (rule 24 `[R-REGISTRY]`). `opTime ≥ 0.99` and
  the half-peak gate are *definitional* ("full-clock, near-full-load"), not
  thresholds swept against a residual; frozen at derive time (rule 23).
* **(e) Paired re-derive, and an owner call.** `caiso_offer_curve_measured.json`
  multipliers are defined as `bid / (base_HR_class × gas)`. Re-basing any class's
  `base_HR` requires re-deriving them so the measured **bid** stays invariant —
  a *definitional* re-derive (source bid data untouched), which rule 23 permits
  but which must be stated in the commit. CHP is not in that JSON's two classes,
  so as scoped in (b) **no re-derive is triggered** — but any later widening to
  CT_PEAKER/CC_REGULAR would trigger it and should not proceed without the call.
* **(f) ISO-generic** (rule 25 `[R-ISO-SCOPE]`): one gate, no per-ISO literal —
  §3/§4 show CHP broken in all six. This would also retire
  `CHP_STEAM_CREDIT_HR_CORRECTION_ISOS` as a per-ISO channel wherever CEMS
  covers the plant.
* **(g) Forward story (rule 13), the CO2-rate precedent.** Exactly
  `data/emission_rates.py` / `docs/handoffs/emissions-co2-rate-plan-2026-07.md`:
  backcast years consume the target year's measured rate, forecast years a
  gen-weighted trailing average of the plant's own CAMPD history with a
  class-median fallback. The 0.9 % cross-year CV says it is stable enough to
  carry.
* **(h) Gated, default off, byte-identical off.**

**Honest expected effect:** CAISO CT_CHP energy is floor-forced by
`chp_steam_floor_p25`, so a rate change moves **λ, not MWh** — the exposure is
price-formation in the hours CT_CHP is marginal, and **C3a is the kill guard**.
The larger prize is the five ISOs whose CHP is under-stated by 12–62 % and whose
CHP therefore clears too cheaply.

## §7 — DO-NOT-REDO (this lane)

* Re-testing the `HEAT_RATE_BINS` fallback as the CT cause (§1 — 11 % of MW).
* **Comparing a model/eGRID heat rate to a CEMS `grossLoad`-basis rate without
  the gross→net reconciliation** (§2). This is the trap: it invents a +8…+20 %
  error in every low-duty class and is how the "+27–54 %" headline was produced.
  Any future heat-rate comparison states its basis explicitly.
* Treating the `econ_low` 1.147 / `econ_high` 1.182 tranche lift as a modelling
  error (§2a) — it is the measured OASIS DAM bid.
* Re-measuring the provenance chain, the cross-ISO net-basis error table, the
  coverage/stability table, the CF tilt or the gross→net ratios (§1–§4;
  instrument committed).
* Proposing a **per-plant measured DAM bid** multiplier for CAISO (§5.3 — ids
  are masked; the derive's own charter resolves it NO).
* Re-basing `base_HR` for CT_PEAKER or CC_REGULAR **without** re-deriving the
  measured bid multipliers (§5.1/§6e).
* Pre-registering any heat-rate change against `CT_PEAKER energy → 3.30 TWh` or
  against C5a (§5).
* Treating CT under-dispatch as an offer-**level** defect: it is a λ-side/rung-
  continuum question owned by FINDING-caiso127 §4 and gated behind the storage
  pin (§2 there).
* A fitted heat-rate multiplier, offset or threshold tuned to the CT residual
  (rules 13/24).

Next number: caiso-129.
