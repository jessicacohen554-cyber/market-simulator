# Grounding the thermal offer-curve bands in the ERCOT 60-Day DAM offers

**Date:** 2026-06-17
**Closes:** the open **Task-2** gap from `docs/lmp-decomposition-2026-06.md` — *"the
CT/CC/ST band SHAPE is defensible but the HEIGHTS are fitted, not validated against
the real offer distribution."*
**Deliverables:** `scripts/data/parse_ercot_dam_offers.py` (wide→tidy parser),
`scripts/archive/analyze_dam_offer_multipliers.py` (offer→multiplier overlay),
`data/raw/_processed-legacy/ercot_dam_offers.parquet` (canonical tidy offers, regenerable),
`data/raw/_processed-legacy/ercot_resource_settlement_crosswalk.csv`,
`data/raw/_processed-legacy/ercot_offer_multiplier_summary.csv`.
**Status:** ANALYSIS / ingestion only — **no model change, no calibration run is
gated on it.** It identifies *one* defensible re-derivation target (the CT econ
ramp), which — per the guardrails — is a SEPARATE, gated change.

---

## 1. What was built

`scripts/data/parse_ercot_dam_offers.py` reshapes the wide 60-Day DAM Disclosure
"Gen Resource Data" (one row per resource × delivery-hour, the 10-point energy
offer curve spread across 20 columns) into a **tidy long** table — one row per
`(resource, hour, curve point)` carrying the melted `point / mw / price` plus the
three-part fields (`min_gen_cost`, `startup_hot/inter/cold`), the operating
envelope (`hsl`/`lsl`/`awarded_qty`), the settlement point, the realized SPP, and
the per-resource AS awards. It maps `Resource Type → model class`
(CCGT90/CCLE90→CC, SCGT90/SCLE90→CT_PEAKER, GSREH/GSNONR/GSSUP→ST_GAS,
CLLIG→COAL, DSL→OIL; non-thermal skipped) and tags each row `committed` from the
resource status. Every offering row is kept regardless of award, because the
QSE-submitted curve **is** the offer — a peaker bids its full curve on the
hundreds of hours it clears OFF, and that bid distribution is exactly what grounds
the offer curve.

`scripts/archive/analyze_dam_offer_multipliers.py` inverts each offer into the model's
heat-rate-multiplier space, `mult = (offer_price − vom) / (base_hr × gas)`, and
overlays the measured distribution on the run124 bands.

### Coverage — the flagged gap is now closed

The session brief flagged "2023 Oct-Nov ONLY so far." The repository now carries
the full 60d DAM Gen Resource Data set, and the parser ingests all of it:
**19.5 M tidy offer-point rows spanning 2022-11-02 → 2025-11-01** (the file labels
are 60-day-lagged; actual delivery dates run a full three years). That includes
the wanted cheap-gas 2024 months (delivered gas avg **$1.78**/MMBtu) and 2025
(**$2.94**), so the grounding is no longer a single-window snapshot.

| class | tidy point rows | resources (crosswalk) |
|---|---|---|
| CC | 9.35 M | (385 thermal total) |
| CT_PEAKER | 5.37 M | |
| ST_GAS | 2.34 M | |
| COAL | 1.39 M | |
| OIL | 1.04 M | |

---

## 2. The three-part offer → model bands (the crux)

ERCOT offers are three-part: **Startup** ($/start) + **Min Gen Cost** ($/MWh at
LSL) + an **Energy Offer Curve** that is *incremental energy above LSL*. The
verified worked example is `AEEC_ELK_1` (SCGT90 peaker): Min Gen $34.58, Startup
(cold) $5,902, but its **energy curve sits at $23–28/MWh** — i.e. right at fuel
cost (delivered gas × 10.65 HR ≈ $22), *not* the all-in price. The mapping used:

| model band | ERCOT source | notes |
|---|---|---|
| **committed** | Min Gen Cost + amortized Startup (per-start ÷ typical run-MWh) | the real measured grounding for the committed hurdle the model proxies |
| **econ_low → econ_high** | the energy-curve points across LSL→HSL, bucketed by load fraction | the bottom-/mid-/top-third of the operating span |
| **peak** | top economic curve point, and the **offer-cap price wall** ($5,000) | ERCOT masks the normal-hours deep top; only the ≥50×FIP scarcity segment is posted on a 7-day lag |

**Normalization.** `base_hr` is the class cap-weighted reference (CT **10.65**, CC
**7.16** — matching the `lmp-decomposition` overlay; ST **10.75** from the ERCOT
registry), `gas` = delivery-date Henry Hub daily + ERCOT basis (−0.50), `vom` =
class VOM (gas_ct 3.5, gas_cc 2.0, gas_st 4.0). The distribution is taken as each
resource's median multiplier per band, then described across resources, so a few
high-frequency QSEs don't dominate.

---

## 3. The measured distribution vs the run124 bands

**Per-class overlay (measured = per-resource median):**

| class | committed model | committed meas (min-gen / +startup) | econ_low model | econ_low meas p50 | econ_high model | econ_high meas p50 | peak model | peak meas (econ-top p50) |
|---|---|---|---|---|---|---|---|---|
| **CT_PEAKER** | 1.14 | 1.19 / 1.42 | 1.27 | **1.08** | **2.18** | **1.11** | 13.15 | 4.82 (cap-wall above) |
| **CC** | 0.92 | 0.99 / 1.07 | 1.16 | 0.98 | 1.41 | 1.51 | 2.25 | 4.92 |
| **ST_GAS** | 0.91 | 2.39 / 3.59 | 1.15 | 1.61 | 1.55 | 1.91 | 4.20 | 13.22 |

**CT econ-ramp multiplier is FLAT across every year** (per-resource median),
delivered-gas in parentheses — the rising ramp never appears:

| year (gas) | econ_low | econ_mid | econ_high |
|---|---|---|---|
| 2023 ($1.99) | 1.08 | 1.07 | 1.07 |
| 2024 ($1.78) | 1.02 | 1.14 | 1.17 |
| 2025 ($2.94) | 1.03 | 0.89 | 1.07 |

---

## 4. Verdict — which heights are inside the observed distribution

**CT_PEAKER — the rising econ ramp is the one defensible re-derivation target.**
- *committed 1.14* → **INSIDE.** Measured min-gen-only is 1.19; adding amortized
  startup lifts it to 1.42. The run124 effective 1.14 sits at the low edge; the
  run57 baseline 1.48 brackets the +startup figure. Keep (arguably could rise).
- *econ_low 1.27* → **marginally high.** Measured p50 1.08, p75 1.20.
- *econ_high 2.18* → **OUTSIDE.** The measured top-of-curve multiplier is **1.11**
  (p90 2.11) and flat across all three years. The observed CT energy curve sits at
  fuel cost from LSL to HSL; **the model's rising 1.27→2.18 econ ramp is an offer
  markup, not the observed energy-curve shape.** This confirms
  `lmp-decomposition` §2c exactly: the markup ERCOT peakers actually carry lives
  in **startup (committed band) + the scarcity wall**, not in a rising incremental
  heat rate. ⇒ **defensible re-derivation target.**
- *peak 13.15* → **defensible as a price wall.** The real wall is the $5,000 offer
  cap (the masked deep top); 13.15× ($359–$498) is a conservative floor sitting
  between the typical econ-top (~5×) and the cap. Keep.

**CC_REGULAR — INSIDE, keep.** committed (model 0.92 vs measured 0.99), econ_low
(1.16 vs 0.98, within p25–p50), econ_high (1.41 vs **1.51**, dead-on), peak duct
2.25 (conservative vs measured econ-top 4.9). No re-derivation warranted.

**ST_GAS — model bands sit BELOW observed, but this is the documented swing, not a
clean target.** Measured min-gen 2.39 and econ 1.61→1.91 are well above the model's
0.91 / 1.15 / 1.55. Real ERCOT gas-steamers bid expensive. But ST_GAS is the
deliberate marginal-swing class (small fleet, 32–37 resources, wide distribution),
and `lmp-decomposition` Task-2 already records the **−0.25 CT↔ST cross-coupling**:
a cheaper CT offer craters ST_GAS. Raising ST toward its observed offers is *not*
independently defensible without re-solving that coupling. Flag, do not move.

---

## 5. Guardrails honored / what a re-derivation would require

This artifact is **ingestion + analysis**; it changes no band and gates no run.
The single defensible target it surfaces — **flatten the CT econ ramp toward the
observed flat-at-fuel-cost shape and move the markup into committed (startup) +
the scarcity wall** — is a SEPARATE, gated change that must:

1. Re-run the **offer-curve Jacobian** (`scripts/data/derive_offer_curve_jacobian.py`)
   and the universal volume gate — the `lmp-decomposition` Task-2 result is that a
   "heat-rate-pure" flat CT econ **over-runs CT and craters ST_GAS** through the
   −0.25 coupling, so any re-derivation must be defensible AND non-regressing.
2. Register the probe bundle on the dashboard.

The expected outcome (per the decomposition's own forecast) is a **structural
residual**: the CT under-run is the non-CEMS small-peaker gap (Ector County,
Permian Basin, Pearsall — no hourly CEMS, unreachable by the merit order), which
no offer height fixes. This analysis confirms the *premise* of that forecast (the
rising ramp is not in the offers) without yet paying the re-derivation cost.

**DAM-vs-RT caveat.** These are **day-ahead** offers; the model is more RT-like.
DAM energy curves are the cleanest available picture of how QSEs price the
LSL→HSL band, but RT (SCED) offers can re-shape intraday. The companion
`60d_SCED_Gen_Resource_Data` (RT offers) is the next refinement if the
re-derivation is pursued.

**The crosswalk long pole.** Multipliers here are normalized by the **class**
cap-weighted base_hr, not each unit's own heat rate, because the
`resource_name → EIA-plant` join does not yet exist. The parser emits the
resource→settlement-point half
(`data/raw/_processed-legacy/ercot_resource_settlement_crosswalk.csv`, 385 resources), which
also seeds the nodal-pocket session's resource→pocket map; the EIA-plant join
(settlement point + EIA-860 plant names) is the remaining step for per-plant
grounding and is scoped, not done.

---

## 6. Reproduce

```bash
# 1. Parse the wide disclosure → tidy offers + resource/settlement crosswalk
python scripts/data/parse_ercot_dam_offers.py

# 2. Overlay the measured multiplier distribution on the run124 bands
python scripts/archive/analyze_dam_offer_multipliers.py
python scripts/archive/analyze_dam_offer_multipliers.py --committed-only   # online-only check
```

The canonical `ercot_dam_offers.parquet` (160 MB) is regenerable and therefore
git-ignored under the `data/raw/_processed-legacy/*.parquet` rule; the small CSV summaries
and the crosswalk are committed.
