# Forecast-methodology gap sweep — giving every backcast-only overlay a forward analogue

**Date:** 2026-06-25
**Scope:** every *active* measured-data lever in the current per-ISO calibration
keepers (ERCOT run157, CAISO corridor-deliverability, PJM 48-sync-srmc,
NYISO 27-cc-offer, NEISO 32-btm-solar, MISO 9-pjm-seam-hranchor), classified by
whether it has a **forward analogue** that regenerates from forward drivers and
responds to changed conditions.
**Method:** code reads of `results/scarcity.py`, `data/{fuel,fleet,renewables,outages,hydro}.py`,
`model/transmission.py`, `config/scenarios.py`, plus each keeper's resolved
`run_config.json` / `calibration_attestation.json`. Design/audit pass — **no
model code changed.** Extends `docs/backcast-measured-data-audit-2026-06.md`
(which audited the ERCOT keeper alone) to all six ISOs.
**Source-of-truth rule:** where a keeper attestation and the resolved
`run_config.json` disagree, the resolved config wins (see Finding 0).

---

## The admissibility test (CLAUDE.md #10, spec §1.7)

A measured input is **allowed even in backcast** when it is grounded in physics
or market design **and** passes:

> *Could this same quantity be produced for a forward year from forward drivers,
> and would it respond to changed conditions?*

If yes → it is an **input** (outage window, fuel price, emission rate, AS
reservation). If it is a measured **outcome** fed back to drive the residual to
zero (observed CEMS generation, observed LMP, an input rescaled so the model's
*output* lands on actuals) → **forbidden** in a keeper: it has no forward
analogue, so the dispatch being validated stops being the dispatch being
forecast.

The whole point of this sweep is the distinction between:

- **IMPLEMENTED** — forecast code already *computes* the forward analogue; the
  measured series is used only as the backcast realization of the same formula.
- **PARTIAL** — a forward path exists but is incomplete, or the code currently
  *ingests the measured realization* for the calibrated effect rather than
  regenerating it.
- **DESIGN-ONLY** — the forward methodology is understood and specified here but
  not built.
- **MISSING / FORBIDDEN** — no defensible forward analogue exists; the lever
  would have to go inert or be replaced in forecast.
- **BACKCAST-BRIDGE** — a measured overlay that legitimately *retires forward*
  because a market-design change replaces it (ERCOT RTC+B); the forward analogue
  is the post-change endogenous mechanism, and the overlay is correctly
  regime-gated off in forward years.

---

## Headline findings (lead with these)

**Finding 0 — RESOLVED 2026-06-25 (keeper now overlay-off).** The NEISO keeper
is now **`neiso-33-no-ctfloor`** (`results/calibration/neiso_33_no_ctfloor_3yr`),
a byte-identical re-solve of `neiso-32-btm-solar` with **`ct_deployment_overlay`
OFF** and the `ct_deployment_overlay`/`ct_deployment_floor_frac` keys pruned from
its `prb_overrides` bag so they cannot silently return via a replay. Removal is
**dispatch- AND determination-neutral**: the floor only ever injected
0.076/0.041/0.054 TWh/yr (the ~171 GWh below), so gas-family
(54.23/58.81/61.60 TWh), system mean LMP (33.95/38.91/66.70 $/MWh), CO2 and the
verdict all hold — NEISO stays NOT-YET with the identical basis (undocumented
fuelmix / price_tail / storage). CT_PEAKER falls to ~0 (the energy-only LP cannot
dispatch out-of-merit peakers), which is the honest reserve/local-reliability
under-production (~0.5–0.9 TWh/yr) the overlay was masking — a MODEL MISS recorded
in the new keeper's `calibration_attestation.json`, not something to re-floor (#11).
**Cross-keeper bag audit (all six keepers' `scenario_config` +
`prb_overrides`/`coal_bit_sigmoid_overrides`): clean.** Only NEISO carried the
stowaway. `reliability_deployment_overlay`, `ordc_reliability_deployment_mw`,
`rtcb_reliability_deployment_mw`, `ordc_as_plan_mw` are all False/0 everywhere.
PJM's `retiree_cems_cap=True` is an *upper availability cap* on winding-down
retirees (the LP still dispatches economically below it — the admissible
outage/derate family, opposite in sign to a floor/pin), **not** a generation pin.
Original finding, for the record:

The **NEISO keeper
(`neiso-32-btm-solar`) had `ct_deployment_overlay = True` active.** This floored
each NEISO CT-peaker to its **measured out-of-merit CEMS net output**
(`data/raw/_validation-source/ct_deployment_floor_NEISO.parquet`, 3,048 nonzero
floor-hours, ~171 GWh over 2023–25). This is the exact mechanism methodology
spec §1.7 names **FORBIDDEN** ("pinning a unit to its observed CEMS generation
(`ct_deployment_overlay`...)") and that the ERCOT run124 audit required **OFF**
in keepers. It is a measured **outcome** with **no forward analogue**, and it
contradicts neiso-32's own attestation (`"no_pinning_to_actuals": true`, "No
unit pinned to its observed CEMS generation"). The flag rides in through the
generic `prb_overrides` bag (`run_config.json:scenario_config.ct_deployment_overlay = true`,
`mode = "backcast"`), so it is *not* surfaced as a headline lever — which is how
it survived. **Action (DONE 2026-06-25): re-solved the NEISO keeper with the
overlay off (`neiso-33-no-ctfloor`), confirmed the metrics hold, and pruned the
flag from the lineage** (see Build Order P0). This was a governance/keeper-hygiene
fix, not a new forward build.

**Finding 1 — the flagship.** The ERCOT DAM AS-scarcity overlay
(`ercot_dam_as_overlay_series`) is the canonical "measured realization ingested
in place of a forward formula." Its forward analogue is the **endogenous
multi-product AS demand-curve co-optimization**. The single-product half of that
co-optimization **already exists and is forward-native**
(`ercot_ordc_demand_steps` / `energy_reserve_coopt`); the gap is (a) the
**multi-product stack** (RegUp/RRS/ECRS/NonSpin each a co-opt demand curve) and
(b) **phantom headroom** — the perfect-foresight LP leaves cold units idle, so on
acute-but-not-thin days (May 2024 8/24/26) it cannot form the co-optimization
scarcity the measured MCPC carries. Note the overlay is **regime-gated off under
RTC+B** (2025-12-05+), so in a pure forward run it is *already* inert; the build
matters for the 2024-style pre-RTC+B bridge and as the proof that the endogenous
co-opt reproduces the acute days without the measured series.

**Finding 2 — most levers pass.** Of ~40 active levers, the large majority are
IMPLEMENTED (forward-native fuel paths, emission rates, firm-import contracts,
reference-price seams, local self-supply, net-load-indexed drags) or are
legitimate BACKCAST-BRIDGEs (RTORDPA). The genuine forward gaps cluster in three
places: **ERCOT AS co-optimization** (flagship + ECRS/load-resource/storage AS),
~~CAISO intertie pricing & deliverability~~ (**BUILT 2026-06-25**, G8 — forward
reference-price seam + ATC corridor cap), and **HSL/curtailment** (2024/25 have no
HSL → curtailment unmodeled).

---

## Master inventory

Status legend: **IMPL** = implemented forward · **PART** = partial / ingests
measured realization · **DSGN** = design-only · **BRIDGE** = backcast-bridge,
retires forward · **FORBID** = no forward analogue. Effort: S/M/L.

### A. Cross-ISO shared levers

| Lever | Code anchor | Backcast input | Forward driver | #10 | Status | Eff | Risk |
|---|---|---|---|---|---|---|---|
| Historic outage overlay (`outage_source="historic"`, `coal_drop_pof`) | `data/outages.py:201,243` | CAMPD ≥48 h CF<5% windows + unit derate | statistical WEFOR/POF (`THERMAL_AVAILABILITY`) **+ historically-derived monthly maintenance shape (`MAINTENANCE_MONTHLY_SHAPE`, §1.7 — now BUILT, G12)** | PASS | **IMPL** | — | Low |
| F923 per-plant monthly delivered fuel (`coal_plant_monthly_pricing`) | `data/fuel.py:2075` | EIA-923 Sch-5 plant-month $/MMBtu | AEO supply-class trajectory (`HENRY_HUB_TRAJECTORIES`, PRB/lignite supply path) | PASS | **IMPL** | — | Low |
| ISO-month gas actuals (`gas_monthly_actuals`) | `data/fuel.py:445` | EIA-923 Sch-5 ISO-month gas | AEO HH + ISO basis differential | PASS | **IMPL** | — | Low |
| Per-plant CEMS emission **rates** (`use_plant_emission_rates`) | `data/fleet.py:4625` | `plant_emission_rates.parquet` (lb/MMBtu) | fuel-class default rates (applies in **both** modes) | PASS | **IMPL** | — | None |
| Coal PRB/BIT passthrough sigmoid (`coal_prb/bit_passthrough_sigmoid`) | `data/fuel.py` (sigmoid) | take-or-pay + measured passthrough floors | structural sigmoid (price-responsive, forward) | PASS | **IMPL** | — | Low |
| ST_GAS net-load reliability drag (`gas_st_netload_drag`) | `data/fleet.py:1855` | CAMPD-regressed slope/intercept/cap | **endogenous net-load** × regression curve | PASS | **IMPL** | — | Low |
| Offer-curve overrides/deltas (CC/CT/ST/coal tranche multipliers) | `config/scenarios.py` | CAMPD marginal-HR reach | structural CAMPD HR (regenerates per year, responds to gas/fleet) | PASS¹ | **IMPL** | — | Low |

¹ The allowed "tune the level on the right structure" second step (CLAUDE.md #1).
The landing point is the grounded CAMPD/SRMC reach, not a residual-zeroing value.

### B. ERCOT AS / scarcity cluster (run157)

| Lever | Code anchor | Backcast input | Forward driver | #10 | Status | Eff | Risk |
|---|---|---|---|---|---|---|---|
| **DAM AS MCPC overlay** (`ercot_dam_as_overlay`) **[FLAGSHIP]** | `results/scarcity.py:495` | measured binding DAM AS MCPC (60-Day DAM Disclosure) | endogenous multi-product AS co-opt demand curves | PASS | **PART** | L | Med |
| RTORDPA reliability-deployment overlay (`ercot_rtordpa_overlay`) | `results/scarcity.py:419` | measured RTORDPA $/MWh (`ordc_reserves_hourly`) | **retires under RTC+B**; pre-RTC+B = endogenous reliability deployment | PASS | **BRIDGE** | — | Low |
| Energy+reserve co-opt, single-product ORDC steps (`energy_reserve_coopt`) | `results/scarcity.py:618,808` | none — VOLL-anchored LOLP curve | endogenous reserve dual (this **is** the forward co-opt) | PASS | **IMPL**² | — | — |
| ECRS requirement series (`ercot_ecrs_requirement`) | `results/scarcity.py:756` | measured ASPLANNP433 ECRS MW | AS requirement-setting methodology (net-load ramp-risk / load-ratio share) | PASS | **DSGN** | M | Med |
| Load-resource RRS-UFR credit (`ercot_load_resource_reserve`) | `results/scarcity.py:688` | measured NP3-911 RRS-UFR MW | enrollment-driven load-resource AS participation | PASS | **DSGN** | M | Low-Med |
| Storage up-AS reservation (`ercot_storage_as_reserve` + `storage_as_commitment`) | `results/scarcity.py:721`; `data/fleet.py` storage cap | measured 60-Day DAM battery AS awards MW | endogenous storage **energy-vs-AS opportunity-cost** co-opt (`ercot_storage_as_endogenous`) — **BUILT 2026-06-27, G5** | PASS | **IMPL** | — | Med |
| ORDC LOLP distribution (`ordc_lolp_params_path`) | `results/scarcity.py:139,393` | optional measured LOLP table | slow-varying market-design param; default μ/σ forward | PASS | **IMPL** | — | Low |
| West/Panhandle Waha net-load gas shape (`ercot_west_netload_gas_shape`, `ercot_west_gas_endogenous_collapse`) | `data/fuel.py:1632`, `fuel.ercot_west_oversupply_collapse_freq` | (was measured Waha neg-price-day freq) | **endogenous West net-load oversupply** → collapse freq | PASS | **IMPL** (G6 closed 2026-06-25) | — | Low |
| BTM CHP host steam (`CHP_PMIN_CF`, `chp_overrides`, `btm.parquet`) | `data/fleet.py:4195` | CAMPD p2 CF floors (ERCOT) / EIA-923 sector BTM% | CHP host-load forecast (sector BTM share) | PASS | **PART** | M | Low |
| HSL uncurtailed VRE potential (`hsl_potential_mw`, `_forecast_uncurtailed_cf`) | `data/renewables.py:382,876` | ERCOT/CAISO HSL parquet; no-HSL years → delivered grossed up by ref curtailment rate | forecast VRE CF profiles + **endogenous curtailment** | PASS | **IMPL** (2026-06-25, G7) | — | Med |
| Weather-year pinning (`config.weather_year`) | `config/scenarios.py:33`; `data/fleet.py:1019` | historical-year load + VRE CF | weather-year **sampling / ensemble** (`market_sim.ensemble`, `WEATHER_YEAR_POOL`) | PASS³ | **IMPL** | — | Low |
| Storage cycling / battery adder (`storage_daily_cycling`, `battery_dispatch_adder=10`) | `config/scenarios.py` | none (calibration param) | forward adder param (PS per-ISO; battery config) | PASS | **IMPL** | — | Low |

² Single-product only — the multi-product stack is the flagship gap, see Finding 1.
³ A weather *draw* is an admissible input, not an outcome; the gap is methodological (single representative year vs ensemble), not a #10 violation.

### C. CAISO cluster (corridor-deliverability)

| Lever | Code anchor | Backcast input | Forward driver | #10 | Status | Eff | Risk |
|---|---|---|---|---|---|---|---|
| Priced interchange (`priced_interchange`, IMPORT/EXPORT_TRANCHES) | `model/transmission.py:154,229`; `constants.py:1645` | fitted per-ISO tranche ladder | reference-price interface (gas×HR×load) — **CAISO keeper uses the static ladder, not the forward seam** | borderline⁴ | **PART** | M | Med |
| Per-hub intertie pricing (`caiso_per_hub_intertie`) | `model/transmission.py:410,840` | measured WECC hub LMP (Malin/Palo-Verde OASIS) | neighbor **reference-price** (gas×HR×load-shape) per hub — **BUILT** (`caiso_intertie_reference_price`, `inject_caiso_per_hub_reference_prices`, `neighbor_price.caiso_hub_reference_price`) | PASS⁴ | **IMPL** | — | Med |
| Corridor flow limit (`caiso_corridor_flow_limit`) | `model/transmission.py:513`; `eia_loader.py:739` | EIA-930 BA-BA interchange p95 by month×hod | forecast **transfer capability / posted ATC** — **BUILT** (`caiso_corridor_atc_forward`, `forward_corridor_atc_envelope` = TTC × posted-ATC frac × forward solar derate) | PASS⁴ | **IMPL** | — | Med |
| Import gas coupling (`caiso_import_gas_coupling`) | `model/transmission.py:1081` | measured commodity-vs-F923 gas delta | forecast commodity-vs-delivered gas spread | PASS | **PART** | S-M | Low |
| Hydro monthly repin (`hydro_eia930_monthly`) | `scripts/run_calibration.py:1259`; `data/hydro.py:299` | EIA-930 NG:WAT monthly hydro total | forecast hydro **energy budget** (streamflow / normal-year) | PASS | **PART** | M | Low |
| Monthly gas-hub basis overlay (`gas_hub_basis_overlay`) | `data/fuel.py:1089` | measured monthly hub basis | forecast basis path | PASS | **PART** | S | Low |

⁴ A neighbor *price* and a transfer *capability limit* are admissible inputs, but
the code **ingests the measured realization** (OASIS hub LMP, p95 envelope)
rather than regenerating it from forward drivers; both fall back to the static
ladder / physical TTC in forecast, so CAISO imports lose their price-formation
and deliverability shaping forward. This is the largest CAISO forecast gap.

### D. PJM cluster (48-sync-srmc)

| Lever | Code anchor | Backcast input | Forward driver | #10 | Status | Eff | Risk |
|---|---|---|---|---|---|---|---|
| Priced interchange + **reference-price interface** (`reference_price_interface`) | `model/transmission.py:696,771` | neighbor gas basis + EIA-930 neighbor load shape; structural HR | **forward-native** (HH+basis)×HR×load-shape | PASS | **IMPL** | — | Low |
| Retiree CEMS availability cap (`retiree_cems_cap`) | `data/fleet.py:1261` | measured monthly CEMS availability **envelope** of mid-year retirees | known-retirement scheduling (capacity→0 at retire date) | PASS⁵ | **IMPL/PART** | — | Low |
| Coal sub/bit sigmoid passthrough, offer overrides | (see Cross-ISO) | — | structural | PASS | **IMPL** | — | Low |

⁵ This is an availability **cap** (upper bound on a winding-down unit), not a
min-gen floor — it cannot pin output up to actuals, only prevent a retired unit
over-generating. Same family as the outage overlay; forward analogue is the
scheduled retirement. Contrast with `ct_deployment_overlay` (a *floor*, Finding 0).

### E. NYISO cluster (27-cc-offer)

| Lever | Code anchor | Backcast input | Forward driver | #10 | Status | Eff | Risk |
|---|---|---|---|---|---|---|---|
| Energy+reserve co-opt (RCPF) (`energy_reserve_coopt`) | `results/scarcity.py`; `model/dispatch.py` | published RCPF demand curve | forward-native reserve dual | PASS | **IMPL** | — | Low |
| Long-Island local self-supply (`nyiso_local_selfsupply`) | `model/transmission.py:1529` | `NYISO_LOCAL_SELFSUPPLY_FRAC{LI:0.45}` × zonal load | forward-reproducible (LMIC market rule), load-responsive | PASS | **IMPL** | — | Low |
| Firm imports HQ/Ontario (`nyiso_firm_imports`) | `model/transmission.py:1632` | firm-contract floor frac const | firm contract schedule | PASS | **IMPL** | — | Low |
| Import reconciliation band (`nyiso_import_reconciliation`) | `model/transmission.py:1688`; `eia_loader.py:1992` | EIA-930 NYIS Total-interchange monthly (±2% band) | forecast **neighbor net position** (`nyiso_forward_net_import_twh`), else relax | PASS⁶ | **IMPL** | — | Med |
| Gas monthly actuals + hub basis daily (`gas_hub_basis_daily`, `dual_fuel_oil_reattribution`) | `data/fuel.py:957,2184` | measured Transco Z6 daily basis; dual-fuel oil parity | forecast basis path; structural oil-parity cap | PASS | **PART/IMPL** | S | Low |

⁶ A *band* around the measured monthly net interchange is softer than a pin (it
leaves the priced tranches free to set the marginal price within the envelope),
but the band *target* is the measured realization. **Resolved (2026-06-25, G10):**
`build_import_node_reconciliation` is now **mode-aware** — backcast targets the
measured EIA-930 schedule (the realization, unchanged), while forecast targets
the **neighbor's forecast net position** (`ScenarioConfig.nyiso_forward_net_import_twh`
→ `eia_loader.nyiso_forward_net_import_monthly`, an annual NYISO net import shaped
to monthly by the forecast load) and **relaxes to the bare priced-seam economics**
when no forecast is supplied. The dispatch validated in backcast is therefore the
dispatch forecast (rule #10). Still Med-materiality because NYISO net imports are
price-material — the keeper re-solve (`nyiso-30-fwd-band`) confirms the seam
clears *within* the ±2% band (model −23.03/−20.23/−19.18 vs measured
−23.45/−20.35/−19.09 TWh), not pinned to the measured monthly total.

### F. NEISO cluster (32-btm-solar)

| Lever | Code anchor | Backcast input | Forward driver | #10 | Status | Eff | Risk |
|---|---|---|---|---|---|---|---|
| **CT deployment CEMS floor (`ct_deployment_overlay=TRUE`)** | `data/fleet.py:982`; `data/outages.py:756` | measured out-of-merit CT-peaker **CEMS net output** floor | **NONE — measured outcome pin** | **FAIL** | **FORBID** | — | **HIGH** (Finding 0) |
| BTM solar netting (EIA-930 net-load) | `data/renewables.py:41` | implicit in EIA-930 net-load demand | forecast **gross BTM PV** (EIA-860 dist + EIA-861 net-metering) on both sides | PASS | **PART**⁷ | M-L | Low |
| Storage vintage ramp (`storage_vintage_ramp`) | `config/scenarios.py:900`; `data/cod_ramp.py` | EIA-860 COD ramp | endogenous capacity evolution | PASS | **IMPL** | — | Low |
| Hydro backfill / monthly repin (`hydro_backfill_year`, `hydro_eia930_monthly`) | `scripts/run_calibration.py` | EIA-930 hydro monthly | forecast hydro budget | PASS | **PART** | — | Low |
| CC committed 1.27 min-load (CAMPD min-stable-load HR) | `scripts/run_calibration.py:884` | CAMPD measured min-stable-load HR | structural CAMPD min-load (forward) | PASS | **IMPL** | — | Low |

⁷ The *implicit* netting (BTM PV already in EIA-930 net-load demand) is itself
forward-valid and energy-balance-correct. The PART status is for the documented,
default-off forecast-grade **gross BTM PV** reconstruction (explicit PV on both
supply and demand sides) — DESIGN-ONLY, must never scale solar to hit EIA-923.

### G. MISO cluster (9-pjm-seam-hranchor)

| Lever | Code anchor | Backcast input | Forward driver | #10 | Status | Eff | Risk |
|---|---|---|---|---|---|---|---|
| PJM-seam neighbor HR anchor (`hr_by_year`) | `constants.py:2562`; `data/neighbor_price.py:62`; `scripts/derive_neighbor_hr_by_year.py` | measured PJM realized RT LMP ÷ (HH×K) | structural `marginal_heat_rate` (used when no measured LMP) | PASS⁸ | **PART** | S | Med |
| Reference-price interface (`reference_price_interface`) | `model/transmission.py:696` | forward-native (HH+basis)×HR×load | forward-native | PASS | **IMPL** | — | Low |
| Manitoba firm imports (`miso_firm_imports`, 1400 MW @ $8) | `model/transmission.py:1786` | contract-band midpoint const | firm contract schedule | PASS | **IMPL** | — | Low |

⁸ The forward fallback (structural HR) exists and the derivation never sees
MISO's own interchange (so it is not residual-fit), but for backcast years the
code ingests the measured neighbor LMP. Forward years use the single structural
HR, which under-prices dear-gas years — the very effect that motivated the
measured anchor. The forward improvement is a **neighbor-implied-HR forecast**
(e.g. a gas-price-elastic HR, not a flat mean); low effort, Med materiality on
the seam direction.

### H. Default-off scaffolds the sweep brief named (NOT active in any keeper)

These are not keeper levers, but the brief asked about them. Each already has a
forward formula and is correctly default-off:

| Scaffold | Anchor | Status | Note |
|---|---|---|---|
| CAISO operating-reserve withholding (`as_reserve_formula`) | `data/fleet.py:735` | **IMPL (forward formula), inactive** | `R = max(MSSC, 6.7%×load) + 1%×load` — WECC MORC load-ratio, no fitted constant; forward-native. To be swapped to measured OASIS AS once available. |
| ERCOT AS withholding (`as_reserve_withholding`) | `data/fleet.py:600,669` | **measured probe, inactive** | reads measured cleared-AS partition; backcast diagnostic only. |
| PJM ORDC reserve cascade (`pjm_reserve_coopt`, `pjm_ordc_curve`) | `results/scarcity.py:1002,1065,1330` | **IMPL (published curve), inactive** | published two-step ORDC demand curve (`pjm_ordc_curve.csv`); forward-native co-opt, simply not engaged in the current PJM keeper (which clears on energy + reference-price imports). |

---

## Per-gap design notes

Only the PART / DSGN / FORBID items need a forward design. Ordered by cluster.

### G1 [FLAGSHIP] Endogenous multi-product AS co-optimization (ERCOT DAM-AS overlay)

**Forward analogue.** Replace the post-solve measured-MCPC adder with the
endogenous AS demand-curve co-optimization that the RTC+B market actually runs.
The single-product version exists (`ercot_ordc_demand_steps` builds a
VOLL-anchored ORDC reserve demand curve; `model.dispatch` co-optimizes energy and
reserve via the shared-headroom row, so the reserve dual lifts the energy LMP —
RTSPP = LMP + reserve price, *endogenously*). Two pieces are missing:

1. **Multi-product stack.** Build a co-opt demand curve per AS product
   (RegUp / RRS / ECRS / NonSpin), each with its own requirement (driver →
   formula below) and its own VOLL/penalty schedule, cascading (a higher-quality
   product can substitute down). The binding product's reserve dual becomes the
   MCPC; the per-hour max across products reproduces `binding_mcpc` that the
   overlay currently reads from disk. Today the LP holds **one** lumped
   contingency-reserve product (`scarcity.py:762` "it never grew when ECRS was
   introduced"), which is why the measured ECRS/load/storage credits (G3–G5) are
   bolted on as RHS adjustments instead of falling out of the co-opt.
2. **Phantom-headroom fix.** The perfect-foresight LP leaves cold slow-start
   units idle, so on acute-but-not-reserve-thin days (May 2024 8/24/26: elevated
   load, ample *modeled* headroom) it cannot form co-optimization scarcity — the
   documented reason the overlay is needed. The fix is to make the reserve-
   eligible set reflect what is *actually online/responsive* (the on-line/off-line
   split `reserve_headroom` already does for the post-solve ORDC adder), which
   likely requires the **commitment screen** (P2) so idle units aren't counted as
   reserve. Only responsive capacity should back the AS demand curves.

**Driver → formula → forward response.** Requirement per product set from
forecast net-load / VRE per ERCOT's AS methodology (G3); the demand-curve prices
are fixed VOLL-anchored schedules (market design, slow-varying); the *incidence*
of scarcity comes endogenously from the hourly availability in the shared-headroom
RHS — a tighter forecast fleet clears reserve lower on the curve at a higher
price. Responds to changed conditions automatically (more VRE → more net-load
ramp → higher RegUp/RRS requirement → more scarcity hours).

**Greenlight gate (from the brief).** The endogenous per-product reserve dual
must reproduce the ERCOT acute days (May 2024 8/24/26) **without** the measured
overlay, while holding the other months/years. Only then does the overlay retire
from forward — it stays the **pre-RTC+B backcast bridge** (it is already
regime-gated off for RTC+B / year ≥ 2026).

**Effort L.** Touches `model/dispatch.py` (multi-product reserve rows), `results/scarcity.py`
(per-product demand steps), and likely the commitment screen.

### G2 ERCOT RTORDPA overlay — BACKCAST-BRIDGE (no build)

Forward analogue is simply **RTC+B**: the real market replaced the RTORPA/RTORDPA
adders with co-optimized AS demand curves on 2025-12-05, and the overlay is
regime-gated off (`ercot_market_regime → "rtcb"`, `RTCB_GOLIVE_HOUR`) for forward
years. No forward build needed; it remains the pre-RTC+B calibration bridge. Its
endogenous replacement is exactly G1.

### G3 ERCOT ECRS (and the other AS) requirement-setting methodology

**Forward analogue.** ERCOT sizes ECRS/RegUp/RRS from forward drivers it
publishes: net-load ramp risk, forecast-error quantiles, and largest-contingency
/ load-ratio shares. Implement the requirement as `req_product(t) = f(net_load(t),
ramp(t), VRE_share(t))` per ERCOT's published AS methodology, replacing the read
of `ASPLANNP433_<year>.parquet`. This feeds G1's per-product demand curves. The
measured ASPLANNP433 series stays as the backcast realization to validate the
formula against. **Forward response:** more VRE → larger ramp/forecast-error →
larger ECRS requirement, automatically. **Effort M, Risk Med** — ECRS holds ~2 GW
out of the energy stack every active hour, so a forward run with it inert
under-prices the broad tight-but-not-scarce mid-range from mid-2023 on.

### G4 ERCOT load-resource RRS-UFR credit

**Forward analogue.** Load-resource AS participation is **enrollment-driven**: a
forecast of demand-response MW enrolled in RRS-UFR (a growing, policy/market
trend), shaped by availability. Replace the read of measured NP3-911 RRS-UFR MW
with `lr_rrs(t) = enrolled_MW(year) × availability_shape(t)`. **Forward response:**
DR enrollment grows → more load-side reserve supply → fewer scarcity hours.
**Effort M, Risk Low-Med** (~0.8–0.9 GW today; matters most in tight hours).

### G5 ERCOT storage up-AS reservation — energy-vs-AS opportunity-cost co-opt — **BUILT (2026-06-27)**

**Built.** `ScenarioConfig.ercot_storage_as_endogenous` (CLI
`--ercot-storage-as-endogenous`) makes the battery CHOOSE energy vs upward-AS
inside the multi-product co-opt, replacing the measured reservation. Full battery
power cap to the co-opt (no `reserve_storage_as_power` subtraction), the measured
credit guarded off, and the cleared storage AS competing with arbitrage on the
same power cap in the existing vectorized shared-headroom rows
(`dispatch._build_reserve_rows`) — priced by the per-product AS demand curves
(`reserve_price_by_family`). Paired with `ercot_reserve_supply_cap`, the cleared
storage AS counts toward the measured RTOLCAP online-responsive supply (which
already includes online batteries — RTOLCAP grows 13.5→16.7→19.1 GW with the
2023→25 fleet). The measured 60-Day DAM award is kept ONLY as the backcast
realization to validate against (`storage_as.parquet`,
`scripts/probes/storage_as_split.py`), never pinned to. Forward response:
fleet grows → AS saturates → reserve dual falls → batteries tilt back to energy.
Run `164`; tests `tests/test_ercot_storage_as_endogenous.py`; design doc
`docs/ercot-storage-as-endogenous-2026-06.md`. **Was: Effort L, Risk Med.** The
original design note follows.

**Forward analogue (DSGN/MISSING).** Today `storage_as_commitment` subtracts the
*measured* battery AS-award MW from the storage power cap, and `ercot_storage_as_reserve`
credits the same MW back into the reserve RHS — i.e. the model reads how much AS
batteries cleared. The forward version makes the battery **choose** energy vs AS
endogenously: add upward-AS as a decision variable for storage in the co-opt,
competing against arbitrage on the same power cap, priced by the AS demand curves
(G1). The battery holds AS when the reserve dual exceeds its energy-arbitrage
opportunity cost — exactly the real bid. **Forward response:** as the battery
fleet grows and AS saturates, the AS price falls and batteries tilt back to
energy — endogenously, no measured award needed. **Effort L** (new storage-reserve
coupling in the LP), **Risk Med** (largest in 2025+, where the battery AS fleet is
biggest).

### G6 ERCOT West/Panhandle Waha net-load gas shape — CLOSED (2026-06-25)

**Now fully forward.** The price split is computed from the model's **own
net-load** distribution (deep-collapse vs firm regime), preserving a measured
annual Waha basis; the **collapse frequency** `neg_day_freq` was the last measured
input and is now **endogenous**. `config.ercot_west_gas_endogenous_collapse`
(env `ERCOT_WEST_ENDOGENOUS_COLLAPSE=1`) derives the split frequency from forecast
West/Panhandle oversupply — the fraction of hours West+Panhandle wind+solar
generation exceeds local West load plus the region's export TTC (WESTEX 10.0 GW +
PNHNDL 2.68 GW); see `fuel.ercot_west_oversupply_collapse_freq`. Every input is a
forecast quantity the model already builds (VRE capacity×CF, load forecast,
transmission topology), so it regenerates forward and responds to changed
conditions: more West VRE → more oversupply hours → higher collapse frequency
(unit-tested). The measured `neg_day_freq` stays as the **backcast realization to
validate against**, logged alongside the endogenous value on every solve and never
re-pinned.

**Validation (backcast, run158 = the run157 keeper recipe + endogenous collapse,
the only change).** The endogenous oversupply frequency tracks the measured Waha
negative-day frequency in the VRE-driven years and under-predicts the
gas-infrastructure-driven 2024 record — exactly as expected, since 2024's 42% was a
Permian gas-pipeline-takeaway event (a measured *outcome* with no forward analogue,
#12), not a power-oversupply event the proxy models: endogenous **0.017 / 0.003 /
0.006** vs measured **0.030 / 0.420 / 0.110** for 2023/2024/2025 (in-run, on the
dispatched demand+VRE; 2024/25 clamped to the 0.01 floor). The proxy is near-zero in
2024/25 because West local load plus the 12.68 GW WESTEX+PNHNDL takeaway absorbs
essentially all West VRE, so West *power* oversupply almost never occurs. Removing
the measured frequency makes West gas firm ~99% of hours, dropping the West CTs out
of the cheap collapse hours. The **isolated** effect (same run157 recipe + same main,
measured vs endogenous collapse — a one-variable A/B): CT_PEAKER (TWh)

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| measured collapse | 5.95 | **7.48** | 5.54 |
| endogenous collapse | 5.90 | **5.22** | 5.00 |
| EIA-923 | 7.56 | 8.21 | 7.11 |

— almost the entire effect is **2024 (−2.26 TWh)**, the measured-0.42 year, with the
freed energy absorbed by CC_REGULAR (+1.4 TWh); 2023/25 barely move (measured
collapse already small). The measured-collapse keeper's in-band 2024 West-CT fit
(−8.9%) was thus partly carried by the non-forward measured collapse; the endogenous
under-run (−36%) is a documented residual kept per #1/#11 — the forward model must
respond to VRE build, which a frozen measured 0.42 cannot. (The ST_GAS/gas-family
fuelmix-C1 and sysvol-C2 misses are **identical in the measured baseline** — a
run157-recipe-on-current-main artifact with STGAS-drag off, *not* from this lever;
the price residuals are the inherited energy-only-dual limitation.) Registered as a
NOT-YET probe (`ercot_run158_netload_gas_endog_collapse`, all 3 years on the backcast
dashboard, attestation documents the residuals). **Done (was: Effort M, Risk Low).**

### G7 HSL uncurtailed VRE potential + endogenous curtailment — **BUILT (2026-06-25)**

**Forward analogue.** Forecast VRE CF profiles (per-tech, weather-year-shaped)
give the uncurtailed potential as the renewable upper bound; the LP then curtails
endogenously when transmission/oversupply binds (the intended design). The gap
*was*: 2024/25 had **no HSL parquet**, so they fell back to EIA-930
**net-of-curtailment** delivered generation as CF — curtailment baked in, the
model could not re-curtail or respond to changed build.

**Built.** `renewables.py` now gates the high-curtailment ISOs
(`_UNCURTAILED_FALLBACK_ISOS = {ERCOT, CAISO}`): when no HSL parquet covers a
backcast year, the dispatch is handed a **forecast uncurtailed CF** — the
weather-year delivered profile grossed up by the per-tech **reference
curtailment rate** from the ISO's most recent HSL year
(`_reference_curtailment_rate` / `_forecast_uncurtailed_cf`), so the potential is
always ≥ delivered with headroom equal to that rate and the LP curtails
endogenously. The reference rate is a forward-reproducible parameter from a
*different* year, so the potential is never scaled to land delivered output on
the target year's actuals (rule #11). ERCOT 2024/25 (no NP6 upload) and CAISO
2025 (partial-year curtailment workbook) now run on this; CAISO build remains
data-needed for a full-year 2025 workbook. Validated on the dashboard
(`run158-hsl-endogenous-curtailment`, `caiso-29-hsl-curtailment`): ERCOT models
wind ~2.2–2.4% / solar ~0.4–1.7% endogenous curtailment vs measured/reference
4.67%/6.29% (the reduced 6-zone network curtails less than ERCOT's local
transmission constraints — a **diagnostic**, not a fit target). **Open finding:**
CAISO models ~0% curtailment in every year (incl. the unchanged HSL years),
absorbing surplus via negative offers + priced WECC export rather than curtailing
— a separate investigation (G8 territory), not blocked by this wiring.

**ERCOT 2024/25 NP6 intake — attempted, blocked (2026-07-05).** The P4
remainder (below) was worked: ERCOT's legacy MIS report list now redirects
every report, including "Public"-classified NP4-732-CD, to a SiteMinder
market-participant login, and the replacement Data Access Portal
(`data.ercot.com`/`api.ercot.com`) — reachable, not egress-blocked — gates
every call behind a subscription key obtained only via an interactive
ERCOT API Explorer account registration this session cannot complete. The
UMass `nodal-curtailment-analysis` GitHub dataset (the 2023 fallback source)
has no 2024/2025 extension upstream either. Full attempt log:
`docs/ercot-hsl-2024-25-intake-attempt-2026-07.md`. The reference-rate
gross-up fallback is unchanged and remains forward-admissible; this is a
fidelity upgrade still pending credentials, not a blocker.

### G8 CAISO intertie reference-pricing + corridor deliverability — **BUILT (2026-06-25)**

**Forward analogue (now implemented).** CAISO used to price its WECC ties at
**measured** hub LMP (Malin/Palo-Verde OASIS) and cap corridor flow at a
**measured** p95 ATC envelope; both went inert in forecast. The forward path is
now built as the same **reference-price interface** PJM and MISO use, specialized
to the two physical corridors:

- **Price (`caiso_intertie_reference_price`).** Each per-hub corridor is priced at
  `(henry_hub[year] + gas_basis) × marginal_heat_rate × load_shape`
  (`neighbor_price.caiso_hub_reference_price`, injected by
  `transmission.inject_caiso_per_hub_reference_prices`). COI/Path-66 proxies the
  Pacific-NW at Malin (gross-load shape); Path-46/WOR the desert-SW at Palo Verde
  (**net-load** shape — load − solar − wind — so its midday price dips with the
  solar glut, the duck the measured Palo Verde hub carries). The shape is built
  from the EIA-930 CISO extract (the only in-repo WECC hourly series; the
  desert-SW shares CAISO's solar resource), a forward driver. The HR anchors are
  3-year-mean structural values (NOT per-year measured anchors), so forecast years
  are byte-stable and the backcast carries the documented gas-insensitivity
  residual (the WECC hubs are hydro/solar-set, so they do not rise with Henry Hub
  the way a pure gas margin does — the SPP effect).
- **Deliverability (`caiso_corridor_atc_forward`).** The corridor import cap is now
  `TTC × posted-ATC base fraction × clip(1 − k × solar_frac(t), floor, 1)`
  (`transmission.forward_corridor_atc_envelope`, `eia_loader.caiso_solar_fraction`)
  — a capability limit shaped by the region's **forward** solar penetration, not
  the measured p95 flow. Export keeps the physical TTC.

The measured hub LMP + p95 envelope are kept **only** as the backcast realization
the formula is validated against (`scripts/compare_caiso_intertie_formula_vs_measured.py`).
**Honesty gate met:** import price from forward gas/HR/shape, deliverability from a
capability — neither a flow nor a price pinned to the measured realization
(CLAUDE.md #10/#12). **Validation (2024):** the formula reproduces the measured
desert-SW diurnal shape at corr **0.96** with no measured LMP input; the forward
3-year re-solve keeper is `caiso_intertie_forward_3yr`. The Pacific-NW corridor is
the weaker proxy (gross-load shape ≠ the hydro-following Mid-C price; corr ~0.46) —
the documented residual.

### G9 CAISO/NEISO hydro monthly budget forward — IMPLEMENTED (2026-06)

**Forward analogue.** The hydro **monthly-energy-budget** LP constraint (dispatch
chooses *when* within the month) is itself the forward mechanism; only the
*level* is repinned to measured EIA-930 NG:WAT. Forward driver: a forecast hydro
budget from streamflow/snowpack forecast or a normal-water-year climatology,
responding to wet/dry scenarios. **Effort M, Risk Low** (a hydro-year scenario
lever, mostly a level input).

**Status — done (level input + scenario knob).** The forecast budget level is a
**normal-water-year climatology** — the per-month mean of measured EIA-930
NG:WAT across `constants.HYDRO_CLIMATOLOGY_YEARS` (2021–2025), built by
`data.eia_loader.climatological_monthly_hydro` — scaled by a **wet/dry
hydro-year lever** (`constants.HYDRO_YEAR_MULTIPLIER`: dry 0.85, normal 1.0, wet
1.15, bracketing the ±15% central reservoir-system inter-annual range).
`data.hydro.forecast_monthly_hydro(iso, hydro_year)` returns the scaled
climatology, fed to the *same* `load_hydro_budget(monthly_target_mwh=…)` seam the
measured backcast pin uses (per-plant within-month shares preserved; only the
level moves). Surfaced as the `ScenarioConfig.hydro_year` scenario knob and the
`--hydro-forecast-budget` / `--hydro-year {dry,normal,wet}` CLI flags (the
forward mirror of `--hydro-eia930-monthly`, mutually exclusive with it). The
within-month dispatch mechanism is unchanged — this is a pure level input, never
pinned to a realized outcome (CLAUDE.md #12).

### G10 NYISO import reconciliation forward — **IMPLEMENTED (2026-06-25)**

**Forward analogue (built).** `build_import_node_reconciliation` is now
mode-aware. In **backcast** the ±2% band still targets the **measured** EIA-930
NYIS net interchange (the realization — byte-identical to the prior keeper). In
**forecast** the target is the **neighbor's forecast net position** supplied via
`ScenarioConfig.nyiso_forward_net_import_twh` (an annual NYISO net import in TWh
derived from the PJM / Hydro-Québec / Ontario / ISO-NE forward export outlook),
shaped to the twelve monthly targets by the forecast load distribution
(`eia_loader.nyiso_forward_net_import_monthly` — imports track load, so the band
responds to changed conditions, the rule-#12 forward-reproducibility test). When
no forecast is supplied the band **relaxes** to the bare priced-seam economics
(returns `None`), so the seam clears endogenously and is never pinned to a
measured monthly total. Validated by the `nyiso-30-fwd-band` all-years keeper
(backcast metrics identical to `nyiso-27-cc-offer`; the priced seam clears
*within* the band — model net interchange −23.03 / −20.23 / −19.18 TWh vs
measured −23.45 / −20.35 / −19.09) and by `tests/test_import_node_reconciliation.py`
`::TestForwardBandSource`. **Effort M, Risk Med — done.**

### G11 MISO neighbor-HR forward

**Forward analogue exists (structural HR fallback)** but is a flat mean that
under-prices dear-gas years. Improve to a **gas-price-elastic implied HR** (the
neighbor's market heat rate as a function of its gas price / load), so the seam
reprices forward as gas moves — instead of reading the measured PJM LMP-implied
HR per year. **Effort S, Risk Med** on the seam direction.

### G12 Outage statistical monthly maintenance profile (§1.7 roadmap) — **BUILT**

**Forward analogue (IMPLEMENTED).** The flat shoulder-POF heuristic is replaced
by a historically-derived **monthly maintenance shape** (`MAINTENANCE_MONTHLY_SHAPE`,
`config/constants.py`; derived by `scripts/derive_maintenance_shape.py` from the
committed CAMPD unit-outage extracts, all six ISOs pooled). Per plant group, the
shape is the planned-maintenance excess over the annual-minimum month, normalized
to a month-length-weighted mean of 1, so each group's **annual POF budget is
conserved exactly** (`Σ maint[m]·hours[m] = POF·shoulder_hours`) while the
seasonal distribution is sharpened (peaks Apr/Oct–Nov, ≈0 at the Jul/Aug summer
peak, modest in winter). Applied in **forecast** mode only
(`ScenarioConfig.maintenance_monthly_shape`, default on), in
`data.fleet.generators_to_fleet_arrays`; backcast runs keep the measured overlay
unchanged. Distinct from the backcast overlay — it never reads a specific year's
windows, only the pooled shape. **Effort M, Risk Low** (the statistical forecast
default already works; this sharpened its seasonal shape).

### G13 Weather-year ensemble — **BUILT**

**Forward analogue.** Forecast currently pins one representative historical
weather year for load + VRE CF shapes. The forward-grade version is a
**weather-year sample/ensemble** (run multiple weather draws, report the
distribution) — admissible because a weather draw is an input, not an outcome.
**Effort M, Risk Low** (methodological robustness, not a #10 issue).

**Status: implemented** (`src/market_sim/ensemble.py`,
`tests/test_ensemble.py`). The same forecast scenario is run once per weather
draw over `constants.WEATHER_YEAR_POOL` (2023-2025, bounded by EIA-930 hourly
coverage; extend as later years land) — only `weather_year` varies, so each
member caches under its own config hash and the members run in parallel
(CLAUDE.md #16). `summarize_ensemble` reuses the canonical `export._summarize_year`
aggregation and reports, per forecast year and metric, the cross-draw
distribution (mean/std/min/p10/p50/p90/max), per-fuel generation distributions,
and the raw per-member summaries. CLI: `market-sim ensemble --config <forecast.yaml>
[--iso ISO] [--weather-years 2023 2024 2025] [--workers N] [--out dist.json]`.
The runner rejects a `backcast`-mode base config — a backcast pins a single
historical year by design.

---

## Recommended build order

Priority = forecast-materiality × gap-size ÷ effort, with live #10 violations
first.

| # | Item | Why now | Effort | Forecast materiality |
|---|---|---|---|---|
| **P0 ✅ DONE 2026-06-25** | **Retire `ct_deployment_overlay` from the NEISO keeper** (Finding 0): re-solved as `neiso-33-no-ctfloor` with it off (dispatch- & determination-neutral), pruned the flag from the lineage `prb_overrides` bag; cross-keeper bag audit clean (only NEISO carried it; PJM `retiree_cems_cap` is an admissible availability cap, not a pin). | Live #10 violation in a keeper; pure hygiene, no new methodology. | S | n/a (correctness/governance) |
| **P1** | **Flagship: endogenous multi-product AS co-opt (G1)** + its requirement-setting (G3) and the commitment-screen phantom-headroom fix. Bundle ECRS/load/storage requirements since they feed the same stack. | The single largest "ingests measured realization" lever; unblocks ERCOT scarcity pricing forward and is the spec's documented B5a structural gap. | L | High (scarcity → entry/retirement/revenue signals) |
| ~~**P2**~~ | ~~**CAISO intertie reference-pricing + corridor ATC (G8)**~~ **DONE 2026-06-25** | CAISO is import-dominated; both levers went fully inert in forecast. **Built**: `caiso_intertie_reference_price` + `caiso_corridor_atc_forward`; keeper `caiso_intertie_forward_3yr`. | M×2 | Med-High (CAISO price formation) |
| ~~**P3**~~ | ~~**Storage energy-vs-AS opportunity-cost co-opt (G5)**~~ **DONE 2026-06-27** | Completes the AS stack; matters more each year as the battery fleet grows. **Built**: `ercot_storage_as_endogenous`; run `164`. | L | Med (rising) |
| **P4** | **HSL forecast VRE CF + endogenous curtailment (G7)** | Curtailment is first-order and rises with penetration; 2024/25 currently unmodeled. **ERCOT NP6 2024/25 intake attempted 2026-07-05, blocked on ERCOT account credentials — G7 gross-up fallback stands.** | M-L | Med |
| **P5** | **Load-resource RRS-UFR (G4), Waha neg-day (G6), MISO neighbor-HR elasticity (G11)** ~~NYISO import-recon forward (G10)~~ ✅ **G10 done 2026-06-25** | Smaller residual measured inputs with clear, cheap forward formulas. | S-M each | Low-Med |
| **P6** | **Hydro budget forward (G9 — ✅ done 2026-06), outage monthly maintenance shape (G12 — ✅ done 2026-06-25), weather-year ensemble (G13 — ✅ done 2026-06)** | Robustness/shape refinements; forecast defaults already function. | M each | Low |

**Do-nothing-needed (already forward):** F923 → AEO supply path, gas monthly
actuals → AEO, CEMS emission rates, ST_GAS net-load drag, offer-curve overrides,
PJM/MISO reference-price seams, firm-import contracts (NYISO HQ/Ontario, MISO
Manitoba), NYISO local self-supply, storage vintage ramp, RTORDPA (BRIDGE).

---

## Risk register — levers without a defensible forward analogue

| Lever | ISO | Verdict | Forecast consequence if unaddressed |
|---|---|---|---|
| `ct_deployment_overlay` | NEISO (active!) | **FORBIDDEN — no forward analogue** | Measured-CEMS peaker floor; must go inert in forecast → NEISO peaker dispatch loses the propped energy and the keeper's validation isn't the forecast dispatch. **Fix = P0 (retire now).** |
| DAM-AS overlay (G1) | ERCOT | PART → needs flagship build | Without the endogenous co-opt, forecast under-prices acute AS-scarcity days (already inert under RTC+B, so impact is the pre-RTC+B bridge + proving the co-opt). |
| Measured AS requirements / credits (G3–G4) | ERCOT | DSGN | Forecast holds too little reserve / mis-credits load AS → under-prices the tight mid-range; grows with VRE. |
| ~~Storage up-AS reservation (G5)~~ | ERCOT | **RESOLVED 2026-06-27** | Endogenous storage energy-vs-AS co-opt built (`ercot_storage_as_endogenous`); the battery chooses, counts toward RTOLCAP, measured award validation-only. Run `164`. |
| ~~CAISO intertie LMP + corridor ATC (G8)~~ | CAISO | **RESOLVED 2026-06-25** | Forward reference-price seam + ATC corridor cap built (`caiso_intertie_reference_price` / `caiso_corridor_atc_forward`); forward years now carry import price-formation + deliverability shaping. Backcast validation corr 0.96 (desert-SW). |
| HSL 2024/25 + curtailment (G7) | ERCOT/CAISO | PART | Forecast cannot represent rising curtailment with penetration. |

Everything else either passes #10 with an implemented forward path or is a
legitimate backcast-bridge. The single hard stop is **Finding 0**.
