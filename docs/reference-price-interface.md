# Reference-price interface — step (1) validation (PJM)

**Status:** pre-LP. The neighbor-price module is built, tested, and validated
against measured data; it is **not yet wired into the dispatch LP**. This note
records what the validation showed so the step-(2) wiring is informed by it.

## What was built

A forecast-grade, ISO-agnostic neighbor reference price
(`src/market_sim/data/neighbor_price.py`), parameterized per ISO by the
`INTERFACE_NEIGHBORS` registry in `config/constants.py`. For each neighbor:

    neighbor_price[h] = (henry_hub[year] + gas_basis) × marginal_heat_rate
                        × load_shape(neighbor_load[h])

Every term is a forecast input (Henry Hub trajectory, neighbor gas basis,
neighbor EIA-930 load) or a physically-pinned structural constant (marginal
heat rate ~7.5, hurdle $3/MWh, interface limit). **Nothing is tuned to the
net-interchange target** — so reproducing the measured net export *without being
told to* is a genuine validation, not a fit.

Neighbors resolve individually where their EIA-930 load extract exists and fall
back per-neighbor to a proxy BA otherwise. PJM today: **MISO** (own extract),
**NYISO** (own extract), **Carolinas** (no `DUK` extract yet → priced on the
`SOCO` load shape). Drop in a `DUK hourly.parquet` and the Carolinas seam lights
up on its own data with no code change.

## What the validation showed (`scripts/validate_neighbor_price.py`)

Run against PJM 2023/24/25, with no LP, on three measured benchmarks:

**Before calibration** (flat 7.5 heat rate, the placeholder):

| benchmark | result |
|---|---|
| **Neighbor price *shape*** (vs actual NYISO LMP) | tracks: hourly corr +0.39 / +0.40 / +0.49 |
| **Neighbor price *level*** | far too cheap: constructed MISO $19/$16/$22 vs real ~$36/$31/$41 |
| **Seam direction** (spread sign vs measured net export) | **wrong sign**: predicts PJM imports; hit-rate 2–11% |

**After calibration** (effective heat rates anchored to each neighbor's realized
LMP — MISO 14.2, NYISO 13.1, Carolinas 13.5; hurdle $2/MWh):

| year | PJM LMP | neighbor agg | measured export-hrs | predicted | dir hit-rate | corr(spread,−netexp) |
|---|---|---|---|---|---|---|
| 2023 | $28.4 | $36.5 | 0.98 | 0.81 | **0.81** | +0.27 |
| 2024 | $29.5 | $31.6 | 0.96 | 0.68 | **0.69** | +0.25 |
| 2025 | $42.9 | $41.2 | 0.95 | 0.62 | **0.63** | +0.01 |

Anchoring the neighbor to its own realized LMP flips the seam to correctly
predict PJM **export** in the majority of hours (was ~0). The remaining gap
between predicted (62–81%) and measured (95–98%) export hours is a **structural
export floor** — PJM exports scheduled/firm baseload (nuclear that can't back
down, bilateral contracts) even in hours when its price is at or above the
neighbor's. A pure economic price-spread captures the economic majority, not
this floor; step (2) handles it explicitly (a small must-export floor, or
accepting the economic portion) rather than inflating the heat rate to fake it.

### The headline finding (corrected after a literature check)

**The price-spread mechanism is correct and standard; the failure was that the
neighbor price was built too cheap.** A first reading of the validation —
"the spread predicts imports, so PJM's export isn't price-driven" — is *wrong*,
and an external check shows why:

* The field is unanimous that PJM↔neighbor flows follow price spreads net of a
  transaction (hurdle) cost, and that PJM is a structural net *exporter* because
  its resource mix (coal retirements + efficient new CCs, generation near load)
  makes **PJM's LMP lower than its neighbors'**. PJM's 2024 State of the Market
  report and the ACORE / PJM-MISO joint studies say exactly this.
* The numbers confirm the *direction*: MISO's 2024 average real-time LMP was
  **$31/MWh** (Potomac Economics, MISO IMM) vs PJM's ~$29.5 — and ~$36 (MISO)
  vs $28 (PJM) in 2023. So MISO really is the dearer region, and the measured
  net export shrinks as the spread shrinks (+40 TWh in 2023's wide spread →
  +18 TWh in 2025's narrow one).
* Our **constructed** MISO price was **$16 (2024)** — roughly half the real $31.
  The flat 7.5 MMBtu/MWh heat rate and the mean-preserving linear load shape
  reproduce only the gas-*burn* floor; they omit the marginal-unit inefficiency,
  congestion, and scarcity that lift a real RTO's LMP well above gas×7.5. With
  the neighbor mis-priced below PJM, the spread sign flips and the seam predicts
  imports.

So the lesson is not "abandon the spread" — it is "**price the neighbor to its
own realized LMP, not to a bare gas-burn floor**." The shape mechanism is
already sound (hourly corr +0.4 vs actual NYISO LMP); only the level is wrong.

### The fix (now implemented) — calibrate the level to the neighbor, NOT to the flow

The faithful lever is a **per-region marginal heat rate** (and possibly
supply-curve convexity, `load_shape_exponent` > 1) that makes each neighbor's
reference price reproduce *that neighbor's own* annual LMP — MISO ≈ $31 (2024),
etc. This is admissible under rule #11: the anchor is the neighbor's measured
price formation (a reproducible physical/market quantity that responds to
forward gas and load), **never PJM's net-MWh flow**. MISO and the Southeast are
the clean gas-marginal anchors; NYISO downstate is congestion-dominated (implied
HR ~10→18 across 2023-25) and a poor heat-rate anchor — keep its residual as a
documented congestion premium rather than chasing it with HR.

This is now in the `INTERFACE_NEIGHBORS` registry: MISO 14.2, NYISO 13.1,
Carolinas 13.5 MMBtu/MWh, hurdle $2/MWh (the OMS-RSC inter-RTO wheeling adder;
PJM exports at thin spreads, so the hurdle must stay small). The validation
table above is the result.

### Forward heat rate — gas-price-elastic, not a flat mean

A single `marginal_heat_rate` per neighbor is a multi-year *mean* of the
realized LMP/Henry-Hub ratio, and that ratio drifts with gas: it RISES when gas
is cheap (a roughly fixed non-gas adder — congestion, scarcity, non-gas marginal
units — is diluted by a smaller gas number) and FALLS when gas is dear,
especially for a wind-set neighbor whose LMP barely tracks gas at all. So the
flat mean under-prices the seam in dear-gas years and over-prices wind-set
neighbors in those same years.

For backcast years the registry pins each neighbor's measured per-year ratio
(`hr_by_year`). The **forward** fallback is now gas-elastic instead of flat:
each neighbor's realized annual-mean LMP is affine in delivered gas,

    LMP = hr_phys × gas + hr_adder      (neighbor_price._HR_GAS_ELASTIC[name] = (hr_phys, hr_adder))

so the effective implied heat rate is `hr_phys + hr_adder/gas`, easing toward
the gas-proportional `hr_phys` as gas rises. The two coefficients are an OLS fit
of the neighbor's OWN measured `(gas, LMP)` points
(`scripts/derive_neighbor_hr_elasticity.py`) — **blind to the ISO's
interchange** (rule #11) — so the seam reprices forward as the Henry Hub
trajectory moves WITHOUT reading the neighbor's realized LMP for a future year.
`neighbor_price.neighbor_heat_rate` resolves measured backcast → gas-elastic
forward → flat structural (neighbors with no organized-market LMP, e.g. the
Carolinas). MISO's fitted forward HRs: **PJM** `11.06·gas + 3.21` (gas-set),
**SPP** `3.04·gas + 16.27` (wind-set — small slope, large fixed component, so a
gas spike does not spuriously lift it; it reproduces the measured 2025 SPP ratio
7.7 that the flat 10.0 over-priced). `ScenarioConfig.neighbor_hr_forward_skill`
(`"flat"`/`"elastic"`/`None`, threaded through `transmission.
apply_interchange_injections` → `neighbor_price.neighbor_heat_rate`) forces the
seam onto the `flat`/`elastic` forward path for a held-out backcast year, so
the forward formula can be validated against actuals; default `None` is
byte-identical to every keeper.

### Open items for step (2) — the LP wiring

1. **Structural export floor.** The economic spread predicts 62–81% export
   hours vs the measured 95–98%; the ~15–30 pt residual is PJM's
   scheduled/firm baseload export. Handle it explicitly (a small must-export
   floor on the seam, or accept the economic portion) — never by inflating the
   heat rate to fake the floor.
2. **NYISO year-instability.** Its implied HR runs 9.8→13.1→17.7 (2023-25)
   because downstate congestion/scarcity dominates; the single 13.1 anchor
   overshoots 2023 ($40 vs actual $30) and undershoots 2025 ($45 vs $61). NYISO
   is the smallest seam (EMAAC only), so the aggregate impact is limited, but a
   congestion premium or year-grounded NY anchor is the eventual refinement.
3. **Carolinas LMP.** The 13.5 HR is a SERC-bilateral estimate on the SOCO
   proxy; replace with a Duke (DUK) extract + realized LMP when available.

Hurdle rate: production-cost models use ~$2/MWh wheeling/transaction adders on
inter-RTO transactions (OMS-RSC seams study), matching the registry default.

This is consistent with the prior fitted `EXPORT_TRANCHES`, which reproduced
PJM's export only by pricing the export sinks at the *neighbors' avoided cost*
($16–36/MWh) — i.e. the neighbors' marginal price, which the flat-HR reference
price undershoots. The reference-price interface replaces that fit with the
neighbor's *own* gas+load+HR price, anchored to its measured LMP level.

## Step 3 — real interface limits, and the LP over-export finding

Step 2 wired the seam into the dispatch LP. The first full-LP run (`pjm_30`,
2023-25) **over-exported 2.2-3.0×**: modeled net export +88.9 / +66.5 / +54.9
TWh vs measured +40.0 / +32.6 / +18.0. Step 3 set out to bound this with real
published interface limits, then run/score/register.

### What was done — limits from PJM's own published flows (rule #11)

The Tier-3 envelope limits (MISO 10 / NYISO 3 / Carolinas 3.5 GW) were replaced
with the **firm continuous transfer capability** of each seam, derived from
PJM's OWN published per-tie interchange (Data Miner
`import_export_act_sch_interchange`,
`data/raw/iso-specific-transmission/PJM_<year>_*`): each external tie is
mapped to its seam, the per-tie hourly actual flow is summed to the
*simultaneous* seam transfer, and the limit is the **p99.5 of |seam flow|**
pooled over 2023-25 (the duration curve's upper envelope minus the top ~0.5%
transient/loop-flow hours). Reproducible, regenerable for a forward year, and
computed from the flow series *before any LP runs* — not tuned to the net-MWh
target. See `scripts/derive_interface_limits.py` (`--check` guards the constants):

| seam | old | new (p99.5) | why |
|---|---|---|---|
| MISO | 10,000 | **7,300** | old was sum-of-tie-maxima; simultaneous seam never exceeds 8,789 (max), p99.5 7,290 |
| NYISO | 3,000 | **3,900** | old *under*-stated; export p99.5 3,866 (cross-checks Neptune 660 + Hudson HTP 660 + Linden VFT 330 + AC ties ~2,000 ≈ 3,650) |
| Carolinas | 3,500 | **2,400** | Duke/Progress ties |

A structural fact falls out of the per-tie data: **the South/Carolinas seam is a
net importer** — PJM net-imports from Duke/TVA, exporting only ~17% of hours. The
TVA/LGEE south-west ties (~8 TWh/yr of PJM imports) have no neighbor in the
three-seam build yet.

### The finding — honest limits do NOT bound the over-export

Re-running `pjm_30` with the corrected limits left the over-export essentially
unchanged (+88.9 → still +88.9 TWh in 2023). The genuine validation
(`limits from ratings, the TWh falls out`) **fails**, and the reason is
structural, not a limit-magnitude problem:

* The seams **saturate at their caps** — NYISO exports at the limit in **98%** of
  hours, MISO 67%, Carolinas 51%. The LP exports at the cap whenever the spread
  is positive.
* The neighbor reference price is `gas × HR × load_shape` — **flow-independent**.
  When PJM dumps 7.3 GW into MISO, MISO's modeled price stays at its realized
  ~$36.5, the spread ($36.5 − PJM's $30.7 = $5.8) stays well above the $2 hurdle,
  so export pins at the cap.
* Reality's realized MISO transfer averages only **3.3 GW** (far below the 7.3 GW
  physical cap), because the realized economic transfer *self-limits*: as a
  neighbor absorbs imports it climbs down its own supply stack and its price
  falls toward PJM's, closing the spread. The flat reference price omits exactly
  that elasticity.

Lowering the cap to ~3.3 GW to hit +40 would be **fitting the limit to the
outcome** (rule #11 violation), so it was not done. The corrected limits are
kept because they are independently correct; `pjm_30` is registered as the
documented over-export record (gas +9-11 %, coal +11-16 % — PJM over-generates
fossil to feed the excess export; LMP and renewables/nuclear are within
tolerance; the cross-year *ordering* +88.9 > +66.5 > +54.9 tracks measured
+40 > +32.6 > +18, so the spread mechanism has the right *direction*).

### The structural fix — a flow-responsive neighbor price (implemented)

The neighbor price is now made to **slope with net flow** (`SEAM_FLOW_TRANCHES`
= 8 bands per direction, `neighbor_price.seam_tranche_prices`): exporting `E` MW
into a neighbor displaces `E` MW of its native generation, so its price is read
at its load *reduced* by `E` — the willingness-to-pay slides down the neighbor's
own `gas × HR × (load/mean)^exp` supply curve; importing reads it at load + `I`.
As PJM exports more the spread narrows and the seam self-limits instead of
pinning at the cap. This restores the slope the old fitted `EXPORT_TRANCHES`
carried, but anchored to the neighbor's own load and calibrated curve — no new
fitted parameter, nothing tuned to net-MWh (rule #11). The LP seam is built as
`n`-band import/export pseudo-gens (`build_reference_price_node`) and each band
priced at its midpoint flow (`inject_reference_price_mc`).

**Result (`pjm_31`, 2023):** it works *directionally* — the seams de-saturate
(MISO at-cap 67 % → 47 %, NYISO 98 % → 41 % of hours) and the over-export falls
+88.9 → **+77.8 TWh** (gas over-generation +30.7 → +22.1, LMP $30.68 → $30.01 vs
actual $28.44). But the **load-displacement slope is too gentle to reach measured
+40**: a neighbor's load (MISO ~75 GW) dwarfs the seam flow (≤7.3 GW), so
displacing the flow drops its price only ~10 % (~$3.6), not enough to close the
structural ~$5.8 PJM-vs-neighbor spread over the cap range. The deepest export
bands still clear in many hours.

### Next lever — neighbor supply-curve convexity

The residual is now a *slope steepness* problem, not a level or limit one. The
neighbor price uses `load_shape_exponent = 1` (price linear in load), giving the
gentle slope above. A real marginal supply curve is **convex** — price rises
steeply as the fleet approaches its top. Calibrating each neighbor's
price-vs-net-load convexity to **its own** realized LMP/load relationship (a
measurable market quantity, rule #11) would steepen the self-limiting so the
deep export bands fall below PJM's price and the flow settles nearer the
measured ~3.3 GW (MISO). That is the next refinement; it is *not* to be reached
by cranking the exponent to hit +40, but by fitting it to the neighbor's own
price formation.

### Sources

* PJM Data Miner — `import_export_act_sch_interchange` per-tie actual flows
  (2023-25), the source for `scripts/derive_interface_limits.py`.
* NERC Interregional Transfer Capability Study (ITCS) Part 1, Aug 2024; PJM/MISO
  ITCS — corroborating seam transfer-capability context (PDFs network-blocked in
  the build env; used for cross-checks, not the limit values).
* PJM 2024 State of the Market (Monitoring Analytics), §9 Interchange.
* "Billions in Benefits: Expanding Transmission Between MISO and PJM" (ACORE,
  2023) and the PJM/MISO Joint Modeling Case Study — PJM net-exporter rationale.
* 2024 MISO State of the Market Report (Potomac Economics): MISO RT LMP $31/MWh.
* OMS-RSC Seams Study — Interface Pricing (SPP/MISO IMM): hurdle/wheeling
  adders (~$2/MWh) for inter-RTO transactions in production-cost models.

## Files

- `src/market_sim/data/neighbor_price.py` — the module (pure, no LP); the
  `_HR_GAS_ELASTIC` map carries the forward gas-elastic HR coefficients.
- `src/market_sim/config/constants.py` — `NeighborInterface`, `INTERFACE_NEIGHBORS`
  (incl. the per-year measured `hr_by_year` backcast anchors).
- `scripts/validate_neighbor_price.py` — the validation report.
- `scripts/derive_neighbor_hr_elasticity.py` — fits the forward gas-elastic HR
  coefficients (OLS, blind to ISO interchange) + a flat/elastic/measured table.
- `scripts/derive_interface_limits.py` — derives the seam limits from PJM's
  published per-tie flows (`--check` asserts the constants still match).
- `tests/test_neighbor_price.py` — unit + integration tests.
