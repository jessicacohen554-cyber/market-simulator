# ERCOT LMP decomposition — "dispatch is spot-on, LMP is off" (run124)

**Date:** 2026-06-17
**Keeper under test:** `results/calibration/run124_storage_as_keeper` (the
AS-aware storage design; CT deployment OFF, `battery_dispatch_adder=10`,
merit-ramp CC, cc-duct, storage vintage COD ramp).
**Companion:** `docs/ordc-overlay.md`, `docs/calibration-best-so-far.md`,
`docs/offer-curve-methodology.md`.
**Tooling (no LP re-solve):** `scripts/archive/analyze_lmp_residual.py`,
`scripts/data/derive_ordc_overlay.py`, the demand-weighted monthly-MAE gate metric
(`derive_ordc_overlay._monthly_mae`).

This is the Task-1 deliverable of the LMP/CT-peaker session: a measured
decomposition of *why* run124 nails per-class VOLUME (5 fails @0.5%, cf_emd
18/18, CO₂ 8/9) yet the energy-only LMP MAE is 32.3 / 7.8 / 2.3 (2023/24/25)
against an actual RT that the volume integral hides. The headline: **the price
BODY is right; the MAE is the scarcity TAIL, which is structurally absent from
the LP duals.** The gap then decomposes into three *separable* things — and
only one of them is a defensible, fixable target.

---

## 1. The framing, confirmed: volume is a forgiving integral, LMP is an unforgiving pointwise margin

Volume is an 8760-h integral dominated by cheap baseload (CC + coal + nuclear +
wind) — a few mispriced scarcity hours barely move a TWh. LMP is the *pointwise*
marginal offer, and ERCOT's RT price spends hundreds of hours per year in a fat
scarcity tail ($100–$5,000) that a perfect-foresight energy-only LP with zero
unserved energy **cannot** produce: its price is the demand-constraint dual,
capped by the most expensive *generator offer* in the stack. So the two metrics
grade completely different things, and a model can be right on one and wrong on
the other with no contradiction.

### Body vs tail split (full year, threshold = actual RT $80)

| year | body hrs (RT<$80) | body hourly MAE | body mean resid | tail hrs (RT≥$80) | tail mean resid | **tail share of total \|$·h\| error** |
|---|---|---|---|---|---|---|
| 2023 | 8,320 | **$7.13** | −$1.51 | 439 (5.0%) | −$487 | **78.3%** |
| 2024 | 8,492 | **$7.13** | −$1.81 | 267 (3.0%) | −$162 | 46.8% |
| 2025 | 8,375 | **$8.74** | +$3.61 | 384 (4.4%) | −$80 | 29.6% |

The body — ~95% of hours, ~all of the dispatched energy — sits at a **$7–9/h**
MAE with a near-zero mean residual (it even runs slightly *high* in 2025,
+$3.61). That is a well-calibrated price. The MAE is carried by a thin tail: in
2023 a 5%-of-hours tail is **78%** of the total dollar-hour error.

### The monthly-MAE gate is tail-month-dominated

The gate metric (demand-weighted monthly MAE) per year, with the months that
drive it:

| year | gate MAE | top-3 months (|monthly resid|) | those 3 = % of MAE |
|---|---|---|---|
| 2023 | **32.3** | Aug $163, Sep $63, Jun $38 | **86%** |
| 2024 | 7.8 | May $19, Aug $14, Jan $11 | 51% |
| 2025 | 2.3 | May $7, Jan $7, Mar $5 | 64% |

2023's entire $32 MAE is essentially **one scarcity month** (August: model
$27.8 vs RT $191.7) plus the Jun/Sep shoulder. 2024/2025 are mild years with no
real tail, so their MAE is already at the noise floor.

### Price duration curve — the structural tail loss is unmistakable

Demand-weighted hourly system price, model energy-only vs actual RT:

| year | series | p50 | p75 | p90 | p95 | p99 | p99.9 | max |
|---|---|---|---|---|---|---|---|---|
| 2023 | model | 20 | 26 | 32 | 35 | 40 | 68 | **226** |
| 2023 | RT | 22 | 29 | 51 | 80 | **644** | 3,669 | 5,046 |
| 2024 | model | 18 | 23 | 27 | 29 | 34 | 49 | 5,000¹ |
| 2024 | RT | 20 | 27 | 42 | 61 | 147 | 973 | 3,060 |
| 2025 | model | 29 | 37 | 44 | 49 | 63 | 112 | 571 |
| 2025 | RT | 26 | 37 | 56 | 77 | 138 | 294 | 1,570 |

¹ one VOLL slack hour. **The body matches to the dollar** (p50/p75 model ≈ RT
every year). From p90 up the two series diverge: the model's P99 is **$40 / $34
/ $63** while RT's P99 is **$644 / $147 / $138**. The model's *entire* tail is a
handful of hours at the CT peak band (~$226 in 2023) plus the occasional VOLL
slack hour — exactly the "P99 $34/$34/$63, max = CT peak band + one VOLL hour"
the session brief predicted. Tail-hour counts make it concrete:

| hours above | 2023 act/model | 2024 act/model | 2025 act/model |
|---|---|---|---|
| >$80 | 439 / 2 | 267 / 6 | 384 / 28 |
| >$200 | 181 / 2 | 53 / 4 | 31 / 5 |
| >$500 | 104 / 0 | 16 / 1 | 3 / 5 |

The actual RT fat tail (hundreds of $100–$5,000 hours, ORDC/RTORPA + AS
co-optimization) is **structurally absent from the LP duals** and supplied only
by the post-solve ORDC overlay (display-only, ungated). So the LMP gate is off
*mostly in 2023 scarcity*, and the fix is three separable things that must not
be conflated.

---

## 2. The three separable pieces

### (a) Energy-only structural tail loss — IRREDUCIBLE, and the marginal unit is RIGHT

The LP cannot price scarcity: with zero unserved energy its price is the
marginal generator's *offer*, and the most expensive offer in the energy stack
is the CT_PEAKER peak band (~$226–$498, see §3). It is wrong to read this as "the
model's marginal unit is the wrong class." It is not. **In the price-setting
hours the model's marginal unit is a CT peaker — and so is reality's.** The
honesty diagnostic in `docs/ordc-overlay.md` confirms the model is genuinely
*thin* (low reserve headroom) in the hours reality was thin (monotone
residual-vs-headroom, Spearman ρ≈−0.39). The model has the right marginal stack;
what it lacks is the **reserve-demand-curve adder** that ERCOT stacks *on top of*
that same marginal generator's energy offer. That adder is computed outside SCED
(ORDC/RTORPA) and is not a generator offer at all, so no offer-curve change can
put it into the duals. This piece is irreducible by construction and is owned by
the post-solve overlay — **a valid negative result.**

### (b) Overlay calibration — the real fixable LMP target (display-only, never gates volumes)

The price line a *user* reads on the dashboard is the ORDC-overlaid series, not
the energy-only dual. So the fixable question is: how well does the **published**
overlay reproduce actual RT? Scored on run124:

| overlay | 2023 MAE | 2023 >$200 (act 181) | 2024 MAE | 2025 MAE |
|---|---|---|---|---|
| energy-only (gated) | 32.3 | model 2 | 7.8 | 2.3 |
| ORDC default (flat σ1400, shift0.5) | **25.0** | 42 | 7.9 | 2.3 |
| **published NP6-576-ER, shift0** | **24.6** | 43 | 7.9 | 2.4 |

The parameter-honest published overlay builds the deep tail (29 hours near the
cap vs 0) and closes **~22%** of the 2023 summer $·h gap, but it **cannot** close
2023 alone, for the documented reason: in the 181 actual >$200 hours the
perfect-commitment LP shows ~8.6 GW median reserve headroom (it counts
cold/slow/AS-held capacity as available), so the ORDC LOLP≈0 exactly where it
should bite. Closing 2023 needs the **reliability-deployment (RTORDPA) offset** —
the explicit, scenario-gated 2023-stress calibration, *not* a published ORDC
parameter.

**New finding — the AS-aware keeper RE-CALIBRATES the reliability-deployment
offset.** On run115b the recommended offset was **2,500 MW** (2023 MAE 32.5 →
12.3, 112 of 181 tail hours). On run124 that same 2,500 MW now **overshoots**
(2023 monthly MAE barely moves 32.3 → 31.8 while hourly hours >$200 blow past
actual to 220, and 2024/2025 degrade to 9.9 / 7.1). The reason is physical and
expected: `--storage-as-commitment` already caps the battery peak dump
(reserving the measured RegUp+RRS+ECRS MW from the discharge power cap), which
*tightens peak-hour reserves on its own* — so the storage-AS lever now supplies
~1 GW-equivalent of the discretionary reliability tightness the 2,500 MW offset
used to carry. Re-swept on run124:

| reliability-deployment offset | 2023 MAE | 2023 >$200 | 2024 MAE | 2025 MAE |
|---|---|---|---|---|
| 0 (published only) | 24.6 | 43 | 7.9 | 2.4 |
| 1,000 MW | 14.6 | 88 | 7.7 | 3.1 |
| **1,500 MW (run124 analogue of run115b's 2,500)** | **12.5** | 120 | 7.6 | 4.1 |
| 2,500 MW (run115b value — now overshoots) | 31.8 | 220 | 9.9 | 7.1 |

So on the AS-aware keeper the offset that reproduces "MAE ~12.5, ~120 of 181
tail hours, 2024 within ~±$1" is **~1,500 MW, not 2,500 MW.** This is a genuine,
defensible interaction worth recording: it is *not* a fit improvement (the
offset is display-only and never gates volumes), it is the AS-commitment lever
doing real, measurable work on the price tail that the old magic number now
double-counts. The published series (`scarcity_np6shift0.parquet`) and the
recalibrated stress series (`scarcity_reldeploy1500.parquet`) are committed to
the bundle.

### (c) Offer-curve heights — they set the model's *body/ceiling* price, not the tail

The CT_PEAKER offer bands (§3) set the model's energy-only price from the
upper-body up to its ceiling. They are the only LP-side lever on the price shape,
and they are the subject of Task 2 — but note up front: lowering them lowers the
model's ceiling (worse for the tail), and raising them does nothing (already
rarely reached). They shape the **$35–$85 upper-body price-setting hours**, which
the model already matches reasonably; they cannot manufacture the scarcity tail.

---

## 3. Task 1c — the marginal/price-setting band (bridge to Task 2)

The model's marginal unit by price level is a clean merit story. The CHP
must-run units run every hour, so "the most expensive class running" is a poor
proxy (it always returns CT_CHP); the defensible read is the analytic offer-band
overlay — each band's offer price = `base_hr × mult × gas + vom`, with measured
cap-weighted base heat rates (gas_ct 10.65, gas_cc 7.16 MMBtu/MWh) and annual
Henry Hub ($2.54 / $2.19 / $3.53):

**CT_PEAKER (run124 offer: committed 1.14, econ_low 1.27, econ_high 2.18, peak 13.15):**

| year | committed | econ_low | econ_high | PEAK (price wall) |
|---|---|---|---|---|
| 2023 | $34 | $38 | $62 | **$359** |
| 2024 | $30 | $33 | $54 | $310 |
| 2025 | $46 | $51 | $86 | $498 |

**CC_REGULAR (committed 0.92, econ_low ~1.16, duct peak ~2.25):**

| year | committed | econ_low | duct_peak |
|---|---|---|---|
| 2023 | $19 | $21 | $43 |
| 2024 | $16 | $19 | $37 |
| 2025 | $25 | $29 | $59 |

Overlaying on the model duration curve: the **body (p50–p90, $18–$32) is set by
the CC_REGULAR econ ramp** and matches RT to the dollar. The **upper body
(p95–p99, $34–$63) is set by the CT_PEAKER committed→econ_high bands.** The
**ceiling (model max ~$226–$498) is the CT_PEAKER peak band** — the cheapest CT
peak units (lower than the 10.65 cap-weighted HR) set the 2023 max at $226 vs
the $359 cap-weighted figure. This is exactly the merit order reality runs (CC
on the margin most hours, peakers in the upper hours), so the model's marginal
unit is **not mis-classed** — reality simply adds the scarcity adder on top.

The bands that matter for Task 2 are therefore the CT econ_high (2.18×, $54–$86)
and peak (13.15×) — the bands that set the model's upper-body and ceiling price
*and* contribute the ~3–4 TWh CT energy. Whether those heights are *defensible*
(grounded in real CT economics, not a volume/price fit) is the Task-2 question.

---

## 4. Decision (which of 2b / 2c to pursue)

- **2b (overlay calibration): PURSUE and BANK.** The published NP6-576-ER series
  is the honest price line and is committed. The reliability-deployment offset
  must be re-set from 2,500 → ~1,500 MW on the AS-aware keeper — a real,
  documented interaction, display-only.
- **2c (CT offer heights): TEST (Task 2), expect a structural-residual verdict.**
  The CT econ ramp *rises* (1.27 → 2.18×), which is the **opposite** of a
  physical CT heat-rate curve (a CT's incremental HR *falls* toward full load).
  That rising ramp is an **offer markup** (startup amortization + scarcity/
  opportunity cost — how real ERCOT peakers actually bid), not a heat rate. A
  "heat-rate-pure" re-derivation (flat efficient econ) is therefore the
  *indefensible* one and is expected to over-run CT and crater ST_GAS; recovering
  the CT volume under-run via a cheaper committed band is expected to pull ST_GAS
  down through the documented −0.25 cross-coupling. Both confirm the under-run is
  the **non-CEMS small-peaker structural gap** (Ector County, Permian Basin,
  Pearsall — no hourly CEMS, unreachable by the merit order). See the Task-2
  log entry.
- **2a (energy-only tail): IRREDUCIBLE.** Valid negative result; owned by the
  overlay.

**Bottom line:** dispatch is spot-on because the volume integral forgives the
thin scarcity tail; the LMP is "off" because the gate metric *is* that tail. The
energy-only tail loss is structural (no offer fixes it); the one genuinely
fixable, defensible LMP target this session surfaces is the **overlay
recalibration** (published series + the 1,500 MW run124 reliability-deployment
offset), which is display-only and never touches the volume gates.
