# Forecast-methodology gap — prompt pack

> **⚠️ STALE (2026-07-17) — do not execute.** This June prompt pack is superseded:
> its parent gap sweep handed tracking to `docs/gap-register-2026-07.md`, and all
> forecast session planning now lives in `docs/forecast-development-plan-2026-07.md`.

Ready-to-paste handoff prompts, one per build-order workstream from
`docs/forecast-methodology-gaps-2026-06.md`. Each is self-contained: drop it into
a fresh Claude Code session on this repo and it has the anchors, forward design,
validation gate, honesty constraints, and deliverable it needs. Ordered P0→P6.

**Shared rules every prompt inherits (CLAUDE.md):** right structure first, tune
the level second (#1); measured data only as a reproducible forward-regenerating
input, never an outcome pinned to the residual (#10/#11); a structurally-correct
mechanism stays even if it worsens a metric — fix the root cause, don't bury it
(#11); every completed backcast run is registered on the dashboard
(`calibration-report` skill + `scripts/build_manifest.py`) and committed in the
same session (#12); always solve ALL scoreable years in one bundle, never a
single-year keeper (#13); no Python loops over hours in LP construction.

---

## P0 — Retire the forbidden `ct_deployment_overlay` from the NEISO keeper

```
The NEISO keeper (neiso-32-btm-solar) has a live CLAUDE.md #10 violation:
ct_deployment_overlay is ACTIVE. It floors each NEISO CT-peaker to its measured
out-of-merit CEMS net output (data/raw/_validation-source/ct_deployment_floor_NEISO.parquet,
~3,048 binding floor-hours / ~171 GWh over 2023-25). This is the "pin a unit to
its observed CEMS generation" pattern that methodology spec §1.7 names FORBIDDEN
and that the ERCOT run124 audit required OFF in keepers. It has NO forward
analogue. See docs/forecast-methodology-gaps-2026-06.md Finding 0.

How it hides: the flag is not a headline lever — it rides in through the generic
prb_overrides bag. Confirm in results/calibration/neiso_32_btm_solar_3yr/run_config.json
that scenario_config.ct_deployment_overlay == true and mode == "backcast"
(fleet.py:982 guards: config flag + backcast + floor artifact present — all pass).

Task:
1. Re-solve the NEISO keeper across ALL scoreable years (--year 2023 2024 2025,
   --iso NEISO) with ct_deployment_overlay OFF and every other lever byte-identical
   to neiso-32. Find the exact keeper recipe from its meta.json/run_config.json.
2. Audit the OTHER five keepers' prb_overrides / coal_bit_sigmoid_overrides bags
   (results/calibration/<keeper>/run_config.json) for any other stowaway
   FAIL-pattern flags (ct_deployment_overlay, reliability_deployment_overlay,
   ordc_reliability_deployment_mw, retiree-CEMS *generation* pins). Report findings.
3. Compare the overlay-off NEISO metrics to neiso-32 (C1 fuelmix, C2 sysvol, C3
   price level/shape/tail, CO2, storage). Per #11 the overlay-off run is the
   correct keeper EVEN IF a metric worsens; if CT_PEAKER under-runs more, that is
   the honest reserve/scarcity-incidence gap (documented in the neiso attestation),
   not something to re-floor.
4. Register the overlay-off run on the dashboard as the new NEISO keeper (or, if
   it regresses materially, register it as the honest keeper and open a follow-up),
   write a calibration_attestation.json, update frontend/data/backcast/keepers.json,
   and re-run scripts/build_status.py. Commit + push the bundle + registry sidecar
   + runs/<id>.js + keepers.json + status.js in the same session.
5. Prune ct_deployment_overlay/ct_deployment_floor_frac from the NEISO lineage's
   override bag so it can't silently return.

Honesty gate: this is keeper hygiene, not a fit exercise. The deliverable is the
overlay-off keeper and the cross-keeper bag audit, not a lower MAE.
```

---

## P1 [FLAGSHIP] — Endogenous multi-product AS co-optimization (ERCOT)

```
Build the forward analogue of the ERCOT DAM AS-scarcity overlay
(ercot_dam_as_overlay_series, results/scarcity.py:495): an ENDOGENOUS
multi-product AS demand-curve co-optimization, so the binding product's reserve
dual reproduces the measured binding DAM AS MCPC WITHOUT reading it from disk.
Read first: docs/forecast-methodology-gaps-2026-06.md G1 + Finding 1, spec §1.7,
and results/scarcity.py:604-907 (the single-product co-opt that already exists:
ercot_ordc_demand_steps, ercot_reserve_coopt_inputs, energy_reserve_coopt).

The single-product half is forward-native already; close two gaps:

1. MULTI-PRODUCT STACK. Replace the one lumped contingency-reserve product with a
   co-opt demand curve per AS product (RegUp / RRS / ECRS / NonSpin), each with
   its own requirement and VOLL-anchored penalty schedule, cascading (higher-
   quality substitutes down). The per-hour max reserve dual across products = the
   MCPC the overlay currently reads. Wire into model/dispatch.py as additional
   reserve-balance rows sharing the headroom constraint. NO Python loop over hours
   — build the rows vectorized (block-diag / kron).
2. PHANTOM HEADROOM. The perfect-foresight LP leaves cold slow-start units idle,
   so on acute-but-not-thin days (May 2024 8/24/26: high load, ample MODELED
   headroom) it can't form co-opt scarcity. Make the reserve-eligible set reflect
   what is actually online/responsive (reserve_headroom's on-line/off-line split
   already does this post-solve); this likely needs the P2 commitment screen so
   idle units don't count as reserve.

Requirement-setting feeds from P1b (ECRS/RegUp/RRS forward requirements). Until
that lands, use the measured ASPLANNP433 requirement as the backcast realization
to validate the demand curves against.

GREENLIGHT GATE (must pass before the overlay retires from forward): the
endogenous per-product reserve dual reproduces the ERCOT acute days
(May 2024 8/24/26 → load-wtd LMP ~$45) WITHOUT the measured overlay, while
holding the other months/years (don't over-fire Aug 2024 / 2023-H2 / 2025). The
measured DAM-AS overlay STAYS as the pre-RTC+B backcast bridge (it is already
regime-gated off for RTC+B / year >= 2026); it is retired only from the FORWARD
path once the gate passes.

Deliverable: the multi-product co-opt in dispatch.py + scarcity.py with tests
(trivial case first: 1 gen, 1 zone, 24 h, one binding product), an ERCOT
all-years re-solve registered on the dashboard, and the May-2024 acute-day
reproduction documented (overlay-on vs overlay-off vs endogenous). Honesty gate:
the reserve dual must form from the LP, never an adder tuned to the MCPC.
```

---

## P1b — AS requirement-setting methodology (ERCOT ECRS / RegUp / RRS)

```
Replace the read of measured ERCOT AS-plan series (ercot_ecrs_requirement_mw,
results/scarcity.py:756, reads ASPLANNP433_<year>.parquet) with a forward
requirement-setting formula per ERCOT's published AS methodology, feeding the P1
multi-product co-opt. Read: docs/forecast-methodology-gaps-2026-06.md G3.

Forward design: req_product(t) = f(forecast net-load, ramp(t), VRE_share(t),
forecast-error quantiles, largest-contingency / load-ratio share), per product.
ECRS ~2 GW held out of the energy stack every active hour from 2023-06-10; the
co-opt under-states reserve and under-prices the tight-but-not-scarce mid-range
when this is inert. Keep the measured ASPLANNP433 series as the backcast
realization to validate the formula (modeled vs measured requirement, not a
price fit). Forward response: more VRE -> larger ramp/forecast-error -> larger
requirement, automatically.

Deliverable: requirement formulas wired into ercot_reserve_coopt_inputs, a
modeled-vs-measured requirement comparison (2023-H2/2024/2025), and the ERCOT
all-years re-solve on the dashboard. Honesty gate: requirement from forward
drivers, never the measured MW reverse-engineered onto a price target.
```

---

## P2 — CAISO intertie reference-pricing + corridor deliverability

```
CAISO prices its WECC ties at MEASURED hub LMP (caiso_per_hub_intertie,
model/transmission.py:410,840, reads wecc_intertie_lmp_hourly Malin/Palo-Verde
OASIS) and caps corridor flow at a MEASURED p95 ATC envelope
(caiso_corridor_flow_limit, transmission.py:513 + eia_loader.py:739). Both go
inert in forecast (static ladder / physical TTC). Read:
docs/forecast-methodology-gaps-2026-06.md G8; the CAISO keeper is
caiso_corridor_flow_3yr.

Forward design:
1. Price each per-hub corridor with the SAME reference-price interface PJM/MISO
   use (reference_price_interface, transmission.py:696): per-hub price =
   (neighbor HH + basis) x neighbor marginal HR x load-shape. Wire a per-hub
   neighbor (PNW @ Malin, DSW @ Palo-Verde) with its own gas hub + HR.
2. Set corridor flow limit from posted/forecast ATC, or a deliverability derate
   indexed to the corridor's congestion frequency — NOT measured p95. Keep export
   direction at physical TTC.

Keep the measured hub LMP + p95 envelope as the backcast realization to validate
against. Deliverable: per-hub reference-price seam + ATC-based corridor limit,
a CAISO all-years re-solve on the dashboard, and a measured-vs-formula import
price/volume comparison. Honesty gate: import price formation from forward gas/HR,
deliverability from a capability limit — neither a flow nor a price pinned to the
measured realization.
```

---

## P3 — Storage energy-vs-AS opportunity-cost co-optimization (ERCOT)

```
Make ERCOT storage CHOOSE energy vs upward-AS endogenously, replacing the
measured battery AS-award reservation. Today storage_as_commitment subtracts the
MEASURED 60-Day DAM battery AS-award MW from the storage power cap and
ercot_storage_as_reserve credits it back to the reserve RHS (results/scarcity.py:721)
— i.e. the model reads how much AS batteries cleared. Read:
docs/forecast-methodology-gaps-2026-06.md G5.

Forward design: add upward-AS as a storage decision variable in the P1 co-opt,
competing with arbitrage on the same power cap, priced by the AS demand curves.
The battery holds AS when the reserve dual exceeds its energy-arbitrage
opportunity cost — the real bid. Forward response: as the fleet grows and AS
saturates, the AS price falls and batteries tilt back to energy, endogenously.
Depends on P1 (needs the per-product reserve duals). Keep the measured awards as
the backcast realization to validate the chosen energy/AS split against.

Deliverable: storage-reserve coupling in the LP (storage SOC + reserve rows,
vectorized), tests, ERCOT all-years re-solve on the dashboard, measured-vs-modeled
battery AS-vs-energy split. Honesty gate: the split is the LP's choice, not the
measured award.
```

---

## P4 — HSL forecast VRE CF + endogenous curtailment

```
2024/25 (ERCOT & CAISO) have no HSL parquet, so hsl_potential_mw
(data/renewables.py:382,876) falls back to EIA-930 NET-OF-CURTAILMENT delivered
generation as CF — curtailment is then baked in, not modeled, and the LP can't
re-curtail or respond to changed build. Read:
docs/forecast-methodology-gaps-2026-06.md G7 and the HSL-resolution section of
docs/backcast-measured-data-audit-2026-06.md.

Forward design: supply an uncurtailed VRE potential (published NP6-732/737 HSL
where available, else a forecast per-tech CF profile shaped by the weather year)
as the renewable upper bound, and let dispatch curtail endogenously when
transmission/oversupply binds (renewables are decision variables with MC=0,
ub = CF x capacity — already the design). The modeled-vs-reported curtailment gap
is a DIAGNOSTIC, never a fit target (#11).

Deliverable: 2024/25 HSL potential wired in (prefer published NP6; fall back to
forecast CF), endogenous curtailment confirmed, ERCOT+CAISO all-years re-solves on
the dashboard, modeled-vs-measured curtailment ratio reported. Never scale the
potential so delivered output lands on actuals (the resolved anti-pattern).
```

---

## P5a — ERCOT load-resource RRS-UFR forward (enrollment-driven)

```
Replace the read of measured NP3-911 RRS-UFR MW (ercot_load_resource_reserve_mw,
results/scarcity.py:688) with an enrollment-driven forecast of load-resource AS
participation. Read: docs/forecast-methodology-gaps-2026-06.md G4.

Forward design: lr_rrs(t) = enrolled_DR_MW(year) x availability_shape(t), where
enrolled_DR_MW is a forecast of demand-response MW in RRS-UFR (a growing market/
policy trend). Forward response: DR enrollment grows -> more load-side reserve ->
fewer scarcity hours. ~0.8-0.9 GW today. Keep measured NP3-911 as backcast
realization. Feeds the P1 reserve balance. Deliverable: the forward credit + an
ERCOT all-years re-solve on the dashboard.
```

## P5b — ERCOT Waha neg-day frequency from net-load

```
Close the last measured input in apply_ercot_west_netload_gas_shape
(data/fuel.py:1632; neg_day_freq read measured at data/fuel.py:1310). The price
split is already computed from the model's own West net-load; only the collapse
FREQUENCY is measured. Read: docs/forecast-methodology-gaps-2026-06.md G6.

Forward design: model neg_day_freq as a function of forecast West/Panhandle
net-load oversupply (frequency of West wind+solar > local load + export limit) —
a quantity the model already computes. Forward response: more West VRE -> more
oversupply days -> higher collapse frequency. Keep measured neg_day_freq as the
backcast realization to validate. Deliverable: endogenous collapse-frequency +
ERCOT all-years re-solve on the dashboard.
```

## P5c — MISO neighbor-HR gas elasticity (PJM seam)

```
The MISO PJM-seam neighbor HR (hr_by_year, constants.py:2562; resolved in
data/neighbor_price.py:62; derived by scripts/data/derive_neighbor_hr_by_year.py from
measured PJM RT LMP) has a forward fallback (flat structural marginal_heat_rate),
but the flat mean under-prices dear-gas years — the effect that motivated the
measured anchor. Read: docs/forecast-methodology-gaps-2026-06.md G11.

Forward design: make the neighbor implied HR gas-price-elastic — HR(gas, load)
rather than a flat mean — so the seam reprices forward as gas moves, without
reading the measured PJM LMP per year. Keep the measured-LMP-implied HR as the
backcast realization to fit/validate the elasticity. Deliverable: elastic HR in
neighbor_price.py + a MISO all-years re-solve on the dashboard; confirm the
2024 dear-gas seam direction improves without ingesting MISO's own interchange
(#11 — the derivation must stay blind to MISO flow).
```

## P5d — NYISO import reconciliation forward

```
nyiso_import_reconciliation (model/transmission.py:1688; eia_loader.py:1992) bands
the priced node's monthly net interchange to MEASURED EIA-930 NYIS Total
interchange (+/-2%). Read: docs/forecast-methodology-gaps-2026-06.md G10.

Forward design: band around the NEIGHBOR's forecast net position (PJM/HQ/Ontario
forecast) instead of measured net interchange; relax to the priced-seam economics
when no forecast exists. Keep measured net interchange as backcast realization.
Deliverable: forward band source + NYISO all-years re-solve on the dashboard.
NYISO net imports are price-material — confirm the seam still clears within the
forecast envelope, not pinned to the measured monthly total.
```

---

## P6a — Hydro forward energy budget (CAISO/NEISO)

```
hydro_eia930_monthly repins the hydro monthly-energy budget to MEASURED EIA-930
NG:WAT (scripts/run_calibration.py:1259; the budget LP constraint lives in
data/hydro.py + model/dispatch.py hydro_monthly_energy). The budget MECHANISM
(dispatch chooses when within the month) is already the forward path; only the
LEVEL is measured. Read: docs/forecast-methodology-gaps-2026-06.md G9.

Forward design: a forecast hydro budget from streamflow/snowpack or a
normal-water-year climatology, as a wet/dry scenario lever. Keep measured EIA-930
monthly as backcast realization. Deliverable: forecast budget source + a
hydro-year scenario knob; light-touch, level input.
```

## P6b — Outage statistical monthly maintenance profile (§1.7 roadmap)

```
Replace the flat shoulder-POF heuristic (THERMAL_AVAILABILITY in
config/constants.py; _CC_SHOULDER_MONTHS) with a historically-derived MONTHLY
maintenance shape learned from CAMPD/GADS, applied in FORECAST mode — distinct
from the backcast historic outage overlay (data/outages.py). This is spec §1.7's
documented roadmap item. Read: docs/forecast-methodology-gaps-2026-06.md G12 and
spec §1.7.

Forward design: learn the magnitude/timing of spring/autumn maintenance from
historic outage data and apply it as a forecast-mode seasonal availability shape
(NOT pinned to any one backcast year). Deliverable: the monthly maintenance
profile in the statistical availability path + a forecast-mode sanity run.
Low risk — the statistical default already works; this sharpens its seasonal shape.
```

## P6c — Weather-year ensemble

```
Forecast pins one representative historical weather year for load + VRE CF shapes
(config.weather_year; data/fleet.py:1019). Read:
docs/forecast-methodology-gaps-2026-06.md G13.

Forward design: a weather-year sample/ensemble — run multiple weather draws and
report the distribution (a weather draw is an admissible input, not an outcome).
Deliverable: an ensemble runner over weather years + distributional reporting.
Methodological robustness, not a #10 issue.
```
