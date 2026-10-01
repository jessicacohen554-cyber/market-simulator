# PREREG miso-212 — THE SOUTH GAS DELIVERED-COST BASIS: decompose the $17 the model's South gas is priced above the market that ran it, leg by leg beside its measured counterpart; a solve ONLY if a MEASURED input carries it (2026-09-04)

**Pushed BLIND** before any adjudicating statistic. Keeper at open
`2026-09-04-miso-210-clock` (bundle `miso210_clock_B`), NOT-YET on {C3a-2025
−12.3845} alone, C3c ledgered, C6 attested (41/2). HEAD `a276e8c7` =
`origin/main`. Rule 22: 2023–2025 only. **No LP planned**; G-5 is the only
branch that solves, and its condition is stated in §4.

---

## 1. The object (miso-211, settled) and the keeper's cost chain (read, not measured)

In the 177 Jun–Jul 2025 p75–p99 shoulder hours where MISO's RDT bound
South→North, the model's South gas fleet has 20.27 GW available, runs
15.56 GW against 18.90 measured, leaves 3.52 GW idle within $20 of the
model's South price ($48.3; actual South hubs $41.6), and the marginal MW to
reach the measured level is offered at $65 (p50) / $117 (mean). Same signs
2023/2024.

The keeper's gas marginal cost, per tranche `g` and hour `t`
(`assembly.bins_to_fleet` → `resolve_fuel_prices` → `assemble_mc` →
`apply_gas_offer_margin`; the P1 bid adds startup amortization):

```
mc_base[g,t] = HR_tr[g] × F[g,t] + VOM[g] + markup_hr[g] × (anchor − F[g,t])
             = HR_phys[g] × F[g,t] + VOM[g] + markup_hr[g] × anchor        (anchor 3.0492 $/MMBtu, MISO)
bid_P1[g,t]  = mc_base[g,t] + startup amortization (tranche_startup_amortization)
```

* `F` = annual HH (3.52 in 2025) × seasonality × daily HH shape → **overwritten
  per plant-month by the EIA-923 delivered print** (`gas_plant_monthly_fuel_
  pricing`, class-aware / nearby fallback) → **+ the mean-zero zonal basis**
  (`miso_zonal_gas_basis`: South +0.343 raw from EIA N3045LA3 − HH, applied to
  EVERY South gas unit, 923-priced or not) → dual-fuel cap. **A layering
  question to be sized, not assumed**: a 923-priced South plant's print already
  embeds its regional delivered premium; the zonal basis then adds the regional
  premium again.
* `HR_tr` = plant base HR × band multiplier (CC econ_low 0.95 / econ_high 1.08 /
  **peak 2.25 = the measured F-class duct-burner ratio, `phys_peak`**; CT peak
  4.0; ST_GAS committed 1.32 measured). `markup_hr = base_hr × max(0, mult −
  phys_mult)`: zero on peak (phys = offer), positive on CC econ (0.95 vs 0.887;
  1.08 vs 1.008) and CT econ (1.0 vs 0.69).
* Prior adjudications, NOT re-tested: `gas_hub_basis_overlay` R (miso-156 —
  the model's fleet delivered gas is ABOVE measured by +0.35/+0.09/+0.89
  $/MMBtu; the flat overlay refused on rule 14, MISO being per-plant faithful);
  `miso_zonal_gas_basis` K (miso-119); `miso_offer_level_dispersion` R /
  `miso_offer_spread_anchored` I (system-wide dispersion levers).

**Rule-14 posture, stated in advance:** miso-156 recorded that lowering the
model's gas would worsen C3a. That is NOT a reason to keep an inaccurate input.
If a leg below is shown mis-measured against its own source, the correction is
kept whichever way C3a moves; C3a is reported, never argued.

## 2. Instrument (zero-solve)

Populations and the real S→N binding hours as miso-211 (`_miso211_rdt_binding_
state.py` readers). Per South gas tranche in those hours: `F`, `HR_tr`, `VOM`,
`markup_hr × anchor` from `build_year` (the keeper's own chain), the P1 bid from
`hourly/unit_hourly` (`mc`), availability-derated capacity, the band suffix
(mustrun / committed / econ / peak) and class. Measured counterparts: Henry Hub
daily spot (`gas-prices/henry_hub_daily.csv`); the plant's own EIA-923 print
(`eia923_monthly_fuel_costs.parquet`) and the zonal-basis increment (the two
components of `F`); CAMPD heat input / gross load per unit in the same hours
(WP-3 construction, `campd.load_campd_hourly`) for the heat rate; and **the
market's own declarations**: MISO's masked RT submitted-offer corpus
(`data/raw/miso-energy-offers/rt/`, Jun–Jul 2023–2025 fetched this session, 183
days; curated through `curate_miso_energy_offers.py`, outcome columns dropped
by construction), Region = South, the offered supply curve (cumulative MW at
price ≤ p) per binding hour. No fuel attribute exists in that corpus, so the
comparison is the WHOLE South offered stack vs the model's whole South supply
curve (all fuels) at the same hours.

## 3. Predictions — each with its mechanism

* **P-1 composition of the 3.5 GW idle-within-$20 South gas block** (2025
  binding shoulder hours, capacity-weighted): CC_REGULAR ≥ 50 %, ST_GAS
  15–35 %, CT ≤ 20 % (0.6); by band, **peak tranches ≥ 30 %** (0.55) —
  mechanism: 2.25 × ~7 MMBtu/MWh × $3.5 ≈ $55 fuel leg puts the duct block at
  $60–65, inside the $48+20 window.
* **P-2 fuel leg.** Model South gas `F` in those hours, capacity-weighted, =
  HH daily + **$0.35–0.55** (0.6): the 923 South prints sit ≈ HH + 0.13
  (quantity-weighted, read at open) and the zonal basis adds ≈ +0.28 after
  the mean-zero centroid. Midwest zones' `F` ≈ HH + 0.05–0.20. **Rule-19
  layering: the basis increment on 923-priced South plants is worth $1.5–3
  /MWh at CC/ST heat rates** (0.65). The whole fuel leg vs HH spot explains
  **≤ $4 of the $17 at the margin** (0.65).
* **P-3 heat-rate leg.** Model CC phys HR vs CAMPD (Σ heat input / Σ gross,
  the unit's own hours) within **±7 %** (0.6) → ≤ $2/MWh; ST_GAS model HR
  (committed 1.32×) ABOVE CAMPD by ≥ 10 % (0.5) → $4–6 on the ST_GAS share.
* **P-4 markup leg.** `markup_hr × anchor` on the block's CC econ tranches
  **$2–5/MWh** (0.6); zero on peak by construction; CT econ larger per MW but
  small in the block.
* **P-5 startup amortization (P1 − base).** $3–10 on CT/CC econ-peak
  tranches in the block (0.5); zero on committed.
* **P-6 the market's own stack.** At the measured South generation level
  (29.9 GW total in those hours) the South region's RT offered supply curve
  prices at **≤ $45 (p50 over hours)** (0.55) against the model's $65 —
  mechanism: the actual South LMP cleared $41.6 with that generation online,
  so the offers that cleared were at or below it.
* **P-7 the G-3 verdict.** No single MEASURED input carries ≥ $17 on ≥ 2 GW
  of the block (0.65). Decomposition predicted: fuel ≤ $4 (of which the
  basis layering ~$2), HR ≤ $2 (CC) / $4–6 (ST_GAS), markup $2–5, startup
  $3–10, **the remainder the peak-tranche shape (a measured physical HR
  bound, not a lever)**. Under ALL measured counterfactuals combined (fuel →
  HH spot, basis increment removed, HR → CAMPD) the model's South gas that
  becomes economic at its South price recovers **0.8–1.5 GW of the 3.3** (0.6).
* **P-8 leave-one-year-out.** 2023/2024 decompose with the same ordering of
  legs (0.7).

## 4. Decision rules

* **G-5 fires** (a single-delta A/B on the miso-210 ten-gate scorer, with the
  S→N flow / South boundary net / free-tier binding / Indiana−South spread
  pre-registered per the miso-211 handoff) iff ONE measured-input correction
  — a delivered-price basis (923 print vs spot, or the zonal-basis layering)
  or a heat-rate basis — recovers **≥ 2.0 GW** of the 3.3 GW gap at the
  model's South price in the 2025 binding hours AND holds sign in 2023/2024.
  Predicted NOT to fire (0.65).
* **If a leg is a structural defect regardless of size** (the rule-19
  layering of the zonal basis on 923-priced plants, if confirmed), it is
  NAMED as a repair with its own A/B charter, sized here, not armed here.
* **Otherwise** mint `miso_south_gas_delivered_cost_basis` (field-less row,
  the miso-182 precedent) **R** at MISO with the decomposition, `.` elsewhere;
  no field, no solve. The residual — the market's South stack offering ≥ $17
  below the model's at the same quantity — is then CONDUCT/offer-shape, and
  the finding says so beside the offer-corpus measurement (P-6).

## 5. Reported against interest, in advance

* If P-6 shows the South offers clustered near $60+ at the measured level,
  the model's stack is NOT over-priced and miso-211's "priced out" reading is
  wrong — the gap would be a dispatch/commitment object; said so.
* If the 923 South prints carry a large tail (p90 $4.69 read at open), the
  fuel leg may be plant-concentrated; reported per plant.
* The offer corpus is region-, not zone-, resolved and fuel-blind; the
  comparison is whole-stack.

## 6. Governance

Zero-solve unless G-5 fires. Rule 28(b): `rdt_tcdc`/`gas_hub_basis_overlay`/
`miso_zonal_gas_basis` evidence appended as relevant (verdicts unchanged
unless a defect is confirmed → named, not re-verdicted); the new row + six
cells if minted; §5.4 stamp. Rule 25: MISO only. Rule 22: 2023–2025 (the
offer fetch refused other years by construction). Rule 13: offers, 923, CAMPD,
HH are measured inputs read as diagnostics. Rule 27: blob-verify.
Instrument: `scripts/probes/_miso212_south_gas_cost_basis.py` → record
`results/calibration/_miso212_south_gas_cost_basis.json`.

Next shorthand: **miso-213**.
