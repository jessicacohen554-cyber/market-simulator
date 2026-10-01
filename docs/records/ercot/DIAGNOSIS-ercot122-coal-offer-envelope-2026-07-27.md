# DIAGNOSIS — ERCOT-122: the coal offer-top reconciliation settles AGAINST the chartered lever; the coal-specific defect is offer REACH, not offer LEVEL

**Date** 2026-07-27 · **ISO** ERCOT · **Lane** ercot122-coal-offer-envelope ·
**Keeper under audit** `2026-07-26-ercot115-coal-marginal-hr` (bundle
`results/calibration/ercot115_coal_floor_only`) — **unchanged by this session** ·
**Chartered by** `docs/DIAGNOSIS-ercot121-fleet-representation-2026-07-27.md` §3.2
(the paired arm: measured availability envelope × measured coal offer top) ·
**Method** Phase 1 only — raw-direct measurement from the 60-Day DAM disclosure
plus one no-LP model-side capture (`scripts/probes/ercot117_coal_gas_ranking.py`,
which builds the fleet and aborts before HiGHS). **No year was solved. No arm was
registered. No keeper file was touched.**

**Outcome: the charter's Phase-1 gate — "settle the basis/quantile/instrument
reconciliation BEFORE designing the mapping" — was settled, and it refutes the
mapping.** The fleet-representative measured coal offer level sits *below* the
model's, so a measured offer-level rebasis moves coal **up**, compounding the
ERCOT-116 envelope's over-run instead of clawing it back. Phase 2 was therefore
not run; §5 states the recommendation and §4 routes the successor the
measurement actually supports.

---

## 1. The reconciliation the charter required — settled, with both numbers explained

The charter posed two quantities that "cannot both describe the same quantity":

| source | quantity | value |
|---|---|---|
| `FINDING-ercot112` §6 | "the real fleet's ~$21 top submitted DAM coal offer" | ~$21/MWh |
| `ercot_dam_offer_hrmult_summary.csv` | `COAL_LIGNITE econ_high` | 2.856 (hr-mult) |

Both are real measurements of different things, and the charter's own arithmetic
for the second was off:

**(a) The $74 premise is wrong — the pooled COAL rows are already on a COAL
basis.** The charter read 2.856 as a GAS-price-basis multiplier ("~$74 at $2.5
gas"). `derive_dam_offer_hrmults.py::coal_fuel_price` divides coal offers by the
**delivered coal** trajectory, not Henry Hub (that is why the summary's
`COAL_LIGNITE` and `COAL_PRB` rows differ at identical `base_hr` 10.341 and
identical `n_resources` 19 — only the divisor changes). On lignite's $1.45/MMBtu
the pooled `econ_high` implies **2.856 × 1.45 × 10.341 = $42.8/MWh**, not $74.

**(b) $21 is the top-of-curve; $42.8 is the `rel ≥ 0.67` band — and only ~half
the fleet submits into it.** Measured raw-direct from the CLLIG (Coal and
Lignite) fleet, 1,365,309 curve points, 19 resources, delivery years 2023–2025:

| year | econ_low ($/MWh) | econ_high ($/MWh) | **econ_high capacity coverage** | typical top-of-curve ($/MWh) |
|---|---|---|---|---|
| 2023 | 20.48 | 42.70 | **0.47** (8 of 18 resources) | **21.07** |
| 2024 | 20.75 | 18.61 | **0.21** (3 of 16) | **20.80** |
| 2025 | 20.86 | 17.96 | **0.28** (3 of 12) | **21.82** |

`econ_low` and the top-of-curve carry **100 % capacity coverage**; `econ_high`
carries 21–47 %, because most ERCOT coal resources submit **no curve point above
`rel = 0.67` at all**. Its capacity-weighted p50 is therefore the offer behaviour
of the minority that do reach that high — and they are the expensive ones
(2023 per-resource: LEG_LEG_G1 $44.40, WAP_WAP_G7 $44.90, FPPYD1_FPP_G1_J02
$114.00, against Martin Lake / Coleto Creek / most of Fayette contributing
nothing). Per-resource the bands are perfectly ordered (`econ_high ≤ top-of-curve`
in every case); the $42.70-over-$21.07 inversion is **pure subsample selection**,
not a real inversion.

**Verdict.** `FINDING-ercot112` §6's ~$21 is the **typical (median-day)
top-of-curve, capacity-weighted p50 over the whole fleet** — reproduced by this
session's derivation to the cent as **$21.07 / $20.80 / $21.82**. The pooled
`econ_high` 2.856 is a **21–47 %-coverage subsample statistic** and is **refuted
as a fleet-representative coal offer level**. It must not be re-armed, on the
pooled artifact or per-year.

## 2. What was built (Phase 1a/1b — shipped, default-off, no solve path touched)

`scripts/data/derive_dam_offer_hrmults.py --coal-yearly` →
`data/raw/_validation-source/offer_curve_dam_hrmults_coal_yearly.json`.

The ERCOT-118 `derive_ep_basis_yearly` measurement applied to the coal fleet,
with the one basis change coal requires: **the per-point divisor is the
delivered coal price the model dispatches on** (`COAL_PRICE_LIGNITE_BY_YEAR` /
`COAL_PRICE_PRB_BY_YEAR`), never Henry Hub. The EP correction is a *gas* basis
fix with no coal analogue; what carries over from ERCOT-118 is the principle —
divide by the same fuel series the model later multiplies — not the gas series.
Rule 23 honoured: derived from the raw disclosure against the charter's
measurement question, no residual entered the derivation.

The artifact records, per year and per rank class, what an adoption decision
needs in order not to repeat the pooled artifact's mistake:

* **`coverage`** per band — the selection-bias receipt (§1b).
* **`peak_typical`** alongside the lineage's mode-B `peak`. Mode-B peak is each
  resource's *annual maximum* top-of-curve and on coal it swings
  **$46.56 → $80.49 → $61.03** — the same per-year instability ERCOT-118 §4.2
  found on CC and ERCOT-119 proved inert. `peak_typical` reduces each resource
  to its **median daily** top first and is stable to ±$0.5.
* **`committed`** — absent, identical data destruction to ERCOT-118 (Min-Gen-Cost
  dropped by the 2026-07-22 slimming; parsed intermediate never committed; free
  MIS retention has lost 2023; credentialed archive owner-declined). Declared
  ex ante as the charter required.
* **`_reach`** — §3.

**LOYO stability (rule 24):** the two fleet-representative bands are stable
across 2023–2025 — `econ_low` $20.48/$20.75/$20.86 and `peak_typical`
$21.07/$20.80/$21.82. The two non-representative bands are not
(`econ_high` $42.70/$18.61/$17.96; mode-B `peak` $46.56/$80.49/$61.03). Stability
tracks coverage exactly.

**Byte-identity.** The shared raw loader gained an opt-in
`with_hour_status`/`resource_types` parameterization; the CC artifact
(`offer_curve_dam_hrmults_ep_yearly.json`) was re-derived and is **byte-identical**
to the committed version. No `ScenarioConfig` field, cache-key surface or solve
path was touched, so no config pin moved and no existing run can change.

## 3. The measurement that refutes the chartered lever

**Model side** (`ercot117_coal_gas_ranking.py` §D on the keeper, 2023, cap-weighted
P1 bid $/MWh — the array the LP actually ranks on):

| supply | band | pmax MW | summer bid | shoulder bid |
|---|---|---|---|---|
| lignite | committed | 255 | 17.25 | 16.71 |
| lignite | econ_high | 435 | 19.72 | 19.24 |
| lignite | econ_low | 545 | 21.13 | 20.60 |
| lignite | peak | 128 | **26.96** | 26.01 |
| prb | committed | 2,493 | 20.57 | 21.63 |
| prb | econ_ramp | 5,886 | **23.99** | 25.28 |
| prb | peak | 570 | **32.17** | 34.00 |

Against the fleet-representative measured level (**$20.5 econ_low, $21.1
top-of-curve**): the model's coal is already *at* the measured level at the
bottom (lignite econ bands $19.7–21.1) and **$3–11 DEARER at the top** (prb
econ_ramp $23.99, prb peak $32.17, lignite peak $26.96 — 6.6 GW of coal priced
above the measured top-of-curve).

2025 reproduces it (same probe, same bundle): lignite peak **$27.96**, prb
econ_ramp **$22.32**, prb peak **$29.81** against that year's measured
`econ_low` $20.86 / top-of-curve $21.82 — the same sign, the same ~6.6 GW.

**Therefore a measured coal offer-level rebasis LOWERS the model's coal offers
over ~6.6 GW and makes coal run MORE** — the opposite of the clawback the paired
arm was chartered to produce, and directly additive to the ERCOT-116 envelope's
already-adverse +6.8/+9.2/+12.9 TWh and its new C4 2024 coal FAIL. The direction
is arithmetic, not a residual argument: the measured curve is **flat** at
$20.5–21.8 across the whole operating range while the model's **rises** $17 → $32.

This is *why* the reconciliation had to be settled first, and the charter was
right to gate on it. Adopting the other reading (`econ_high` 2.848 / mode-B peak
3.105) *would* have raised the model's coal top and produced the predicted
clawback — but only by importing a 21–47 %-coverage subsample as if it described
the fleet, which §1 refutes. **The clawback the charter expected was an artifact
of the biased statistic, not a property of the real coal offer curve.**

## 4. The coal-specific defect the measurement DOES support: offer REACH

The share of **online** coal operating headroom (HSL − LSL) that carries any
submitted incremental energy offer, with resource-hours that submit no curve
counted as zero offered (over half of online coal resource-hours are in exactly
that state — median `relmax` = 0.000):

| year | **COAL** | CC (control) |
|---|---|---|
| 2023 | **0.168** | 0.622 |
| 2024 | **0.184** | 0.594 |
| 2025 | **0.161** | 0.677 |

Coal exposes roughly **a quarter** as much of its ramp range to the DAM energy
merit order as CC does — stable across all three years, and coal-specific (it is
not an artifact of ERCOT's small DAM awards: award share of HSL is 16–18 % for
CC, CT and nuclear alike, and 9–10 % for coal, i.e. the same order; the
instrument is admissible for coal on exactly the basis ERCOT-118 adopted it for
CC). The model, by contrast, offers essentially **100 %** of coal headroom into
merit — ERCOT-121 §1a measured the consequence directly: all five Oak Grove
tranches, peak included, at max 744/744 h in July 2023.

**This is the structurally-faithful reading of "the model's coal runs far above
the real fleet at matched price": the error is in how much coal is offered, not
what it is offered at.**

**It does not yet license a mechanism, and this session deliberately did not
build one.** DAM reach alone cannot say whether the unoffered 83 % is withheld,
self-scheduled (price-taking, in which case the model's *must-run* share is too
small — the opposite correction), or simply priced in RT through SCED's
three-part offer, a different instrument. That is precisely the question
`FINDING-ercot117` §E was written to answer and left open. Choosing a price for
the unoffered block without that evidence would be a fitted wall (rule 13) and a
second mechanism stacked on the same phenomenon (rule 19).

## 5. Recommendation — recommend-and-STOP (keeper untouched; owner decides)

1. **Do not run the chartered paired arm as specified.** Its offer-level half is
   refuted ex ante by its own Phase-1 gate: it would lower the model's coal top
   over 6.6 GW and add to the envelope's over-run. The result is arithmetic, so
   a ~50-minute full-span solve would confirm a foregone conclusion rather than
   test a hypothesis. Stated so the owner can overrule with one instruction — if
   a registered controlled refutation is wanted for the record (the ERCOT-118 /
   ERCOT-119 precedent), the arm is one `replay_keeper` invocation away and this
   diagnosis is its pre-commit.
2. **Do not re-arm the pooled `econ_high` 2.856, on any basis.** §1 refutes it as
   fleet-representative; the pooled artifacts stay frozen as the old-basis record.
3. **The measured coal artifact stands as the committed measured record** —
   default-off in the sense that nothing reads it yet. Its
   `econ_low`/`peak_typical` pair is the fleet-representative, LOYO-stable coal
   offer level whenever a mechanism does need one.
4. **Route the successor to the reach question via the SCED TPO instrument**
   (`FINDING-ercot117` §E), not to another offer-level probe: measure what the
   unoffered 83 % of coal headroom is doing in real time — withheld, self-
   scheduled, or telemetered down — and only then design the mechanism. That is
   the one lane that can settle ERCOT-121's observations #1 and #2 together.
5. **ERCOT-120** (tail-hour decomposition) remains a separate, un-renumbered lane
   and is unaffected by this session.

## 6. Closed items honoured

No year solved; no run registered; `frontend/data/backcast/keepers/ERCOT.json`
untouched. Holdout years untouched — the measurement span is exactly
{2023, 2024, 2025} and no LP ran at all. The EP-rebasis lane as a C3c fix, the
peak-p50/quantile-ladder legs, the pooled HH-0.50 artifacts, the committed-band
data gap, `ercot_zonal_gas_basis` ablations, the West/Panhandle topology split
and age/temp coal derates all stay closed; the wtx Panhandle stack and CC
offer-dispersion lanes were not touched. Environment parity for the model-side
capture matched the ercot115–121 baselines (fresh container, gtc-limits clean
partition absent → "static TTC kept" fallback; the lineage
`ercot_wtx_curtailment_driver` kwarg-vs-prb stomp WARNING appeared, prb `True`
active as in every baseline).
