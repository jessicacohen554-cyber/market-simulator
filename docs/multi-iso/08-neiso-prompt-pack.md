# NEISO (ISO-NE) Backcast Prompt Pack (2026-06)

Status: **ready to run.** This is the NEISO instantiation of the v2 playbook
(`05-backcast-playbook.md`), built from the CAISO template
(`06-caiso-prompt-pack.md`) and parallel to the NYISO pack
(`07-nyiso-prompt-pack.md`). Sequenced self-contained prompts for fresh
sessions, plus the upload manifest of data only the user can fetch (the
environment's allowlist blocks EIA/ISO hosts; see `data-acquisition-report.md`).

Target backcast years: **2024 primary, 2023 and 2025 secondary** — NEISO has
the **most complete CEMS coverage** of the new ISOs (all six states for
2023/2024; one 2025 state gap), and unit-outage windows are already derived
for all three years.

NEISO, like NYISO, arrives with topology + zone assignment + outage windows
already landed, so this pack starts at Stage E (calibration reference). Its
weight goes to **Algonquin winter gas basis + dual-fuel switching** (the
single biggest ISO-NE price driver), HQ Phase II imports, Northfield pumped
storage, FCM accounting, and RGGI.

---

## 1. Current state (verified 2026-06-11)

Already in repo — **do not re-build**:

- **Topology (Stage A):** `_neiso_config()` — 4 load zones aggregating
  ISO-NE's 8: `North` (ME/NH/VT, 0.20), `Central` (WCMA/SEMA/RI, 0.30),
  `Boston` (NEMA, 0.21), `Connecticut` (CT, 0.29), plus an `HQ_import` node
  (load_share=0). North–South / Boston-Import / CT-Import / SEMA-RI links
  seeded Tier-3 from the ISO-NE RSP.
- **Zone assignment (Stage B):** FIPS state→zone map (`_NEISO_STATE_ZONES`)
  in `zone_assignment.py`; `_LARGEST_ZONE["NEISO"] = "Central"` fallback
  (WCMA/SEMA/RI holds unlocated plants).
- **EIA-930 hourly:** `data/eia_hourly/ISNE hourly.parquet`; neighbor
  `NYIS` present for the seam.
- **CAMPD unit-level (best coverage of the new ISOs):** CT/MA/ME/RI/VT all
  **2023+2024+2025**; NH **2023+2024** (`NH_2025` missing — upload U1).
- **Unit-outage windows:** `campd-unit-outages-NEISO.csv` already derived —
  **complete 2023 (396) + 2024 (417) + 2025 (379)**. `campd.ISO_STATES["NEISO"]
  = ("ME","NH","MA","CT","RI","VT")`.
- **Market-design registry:** `MarketDesign("NEISO", capacity_market=True,
  net_cone_per_kw_yr=95.0)` (FCM); `voll=2000`.
- **Fuel machinery (national, generalized):** `oil` fuel type, `OIL` offer
  curve, distillate/residual delivered cost, and **dual-fuel detection**
  (`fleet.py::dual_fuel_plant_groups`) all exist — NEISO activates and
  calibrates them.
- **Fleet availability / seasonality:** `FLEET_AVAILABILITY["NEISO"] = 0.85`,
  `GAS_MONTHLY_SEASONALITY["NEISO"]` present.
- **Generalized priced-import node:** `build_import_generators("NEISO")` /
  `build_export_sinks("NEISO")` machinery built (J1) — NEISO needs **constants**
  in `IMPORT_TRANCHES`/`EXPORT_TRANCHES` plus calibration.

Missing (the work below): NEISO blocks in `calibration_reference.json` and
`actual_lmp.json`; zonal LMPs; zonal hourly load; hydro budgets + Northfield
PS wiring; BESS fleet; NEISO import/export tranche constants + calibration;
dual-fuel activation (P13); offer-curve tranche derivation; CHP
identification; Millstone/Seabrook nuclear monthly CF.

**Done by P7 (2026-06-11):** `GAS_BASIS_DIFFERENTIAL["NEISO"]` (+1.10,
EIA-923 normal-year seed); RGGI in marginal cost
(`STATE_CARBON_PRICE_BY_ISO["NEISO"]`, 2023–2025, default-on);
**Algonquin winter basis** as the `gas_hub_basis_overlay` measured
hub-month repricing (U4 satisfied via the ISO-NE MA gas index — 35/36
months 2023–2025 in `data/raw/gas_basis_by_iso_month.csv`; Aug-2025
missing upstream, falls back to EIA-923/shaped); `gas_monthly_actuals`
default-on for NEISO.

**Done by P13 (2026-06-11):** dual-fuel/oil winter switching activated and
validated for NEISO. `dual_fuel_switching` default-on (PJM + NE/NY cluster;
off for ERCOT/CAISO/MISO/SPP); the switch consumes the P7 AGT overlay
(`apply_hub_basis_overlay` runs before `apply_dual_fuel_pricing`, so the
dual-fuel cap sees the blown-out hub gas). Detection: 107 gas tranches /
6,367 MW across 42 plants (incl. Middletown, Montville) plus the oil-primary
steam fleet (135 units / 5,182 MW: Wyman, Canal, New Haven, Montville,
Newington — Mystic is retired in the 2025 EIA-860 vintage). Validation
(2023 smoke): modeled oil 0.24 TWh vs EIA-923 0.39 TWh — same order of
magnitude, not near-zero. **Known limitation:** the committed AGT basis is
*monthly* and monthly averages never reach distillate parity (~$18/MMBtu;
max Jan-2025 $16.9), so the dual-fuel CT/ST switch is wired but does not bind
on monthly data — winter oil comes from the oil-primary steam fleet's
scarcity dispatch; a daily-AGT U4 refinement is what would trip the CT switch.
See `docs/multi-iso/neiso-data-audit.md` §2b.

**Done by P12 + P14 (2026-06-12, Stage G + H sign-off):** full 2023–2025
calibration to sign-off. Three parallel bundles (`neiso_p12_base_2023`,
`neiso_p12_base_2024`, `neiso_p12_hydrofix_2025`); keeper is the structural
defaults — no offer-band tuning. Scorecard: gas ✅ −2.8 to −3.9% vs EIA-930;
nuclear ✅ ≤0.7%; hydro ✅ (2023/24); CO₂ ✅ −8.5 to −9.2% vs eGRID;
interchange ✅ exact. Filed limitations: winter oil shape (U4 daily AGT, gap
#1), PS/BESS over-cycling (AMBER), price level/congestion (P10 held, U2).
P14 wrote `docs/multi-iso/neiso-backcast-2024.md` and updated the status
table (doc-00), manifest (doc-01), data dictionary, offer-curve doc, and
parameter citations. See `docs/calibration-log.md` §NEISO 2 and §NEISO P12.

## 2. Upload manifest (user manual tasks — sessions cannot fetch these)

| # | Item | Source | Destination | Needed by |
|---|------|--------|-------------|-----------|
| U1 | CAMPD unit-level `NH_2025.parquet` (hourly CEMS, same schema as `NH_2024`) — closes the only 2025 CEMS gap | EPA CAMPD bulk download | `data/raw/campd-unit-level/` | P0/P1 (2025 completeness) |
| U2 | DA + RT hourly LMPs at ISO-NE zonal nodes / Hub (esp. .H.INTERNAL_HUB, NEMA/Boston, CT, SEMA, ME) 2023–2025 | ISO-NE Web Services / `da_lmp` & `rt_lmp` CSVs | `data/raw/lmp-data/NEISO/` | P10 |
| U3 | Zonal hourly actual load by ISO-NE load zone (8 zones) 2023–2025 | ISO-NE `hourly_load` / SMD reports | `data/raw/zone-specific-demand/NEISO/` | P8 |
| U4 | **(critical for price level)** Algonquin Citygate (AGT) daily/monthly delivered gas basis 2023–2025 — ISO-NE winter prices are set by AGT spot blowouts far above plant-average 923 | ICE / Platts / EIA NG Weekly (paywalled — web-search may yield monthly) | cite into `constants.py` / gas path | P7/P13 |
| U5 | *(optional)* RGGI allowance clearing prices 2023–2025 | RGGI Inc. auction results (public — web-search likely suffices) | cite into `STATE_CARBON_PRICE_BY_ISO` | P7 |
| U6 | *(optional)* North–South / Boston-Import / CT-Import interface hourly flows + limits | ISO-NE operating-limit postings / RSP | `data/raw/iso-specific-transmission/NEISO/` | P10 (TTC validation) |
| U7 | *(optional)* HQ Phase II HVDC + Highgate + Cross-Sound scheduled flows | ISO-NE interchange reports (EIA-930 carries net) | `data/raw/iso-specific-transmission/NEISO/` | P9 (refinement) |

U2–U4 unblock the full pack. **U4 is the single most important upload for
NEISO** — without the AGT winter basis, ISO-NE's defining January/February
price spikes and the gas→oil switch cannot calibrate. Without U2 price
calibration is level-only; without U3 zonal load stays on static RSP shares.

## 3. NEISO design decisions (made now, applied by the prompts)

1. **Algonquin winter gas basis is THE price driver.** ISO-NE is pipeline-
   constrained; in cold snaps AGT spot gas blows out to many multiples of
   Henry Hub, dual-fuel units switch to oil, and LMPs spike. The measured AGT
   basis (U4) layered onto the gas path + dual-fuel activation (P13) is the
   core of this calibration — more so than for any other ISO. Plant-average
   EIA-923 monthly gas alone will *underprice winter* (playbook §2, doc-01 §4).
2. **Dual-fuel switching is first-order, not a refinement.** Hundreds of MW of
   dual-fuel CT/ST and oil steam (Mystic, Wyman, Middletown, Montville,
   Canal) set winter marginal price. Activate the existing
   `dual_fuel_plant_groups` machinery and drive the switch off the measured
   AGT/oil parity. 0 oil generation in winter is a red flag.
3. **RGGI is in marginal cost.** All six NE states are RGGI; the allowance
   price (~$13–22/t 2023–2025) × emission rate enters in-state fossil MC via
   the `STATE_CARBON_PRICE_BY_ISO` machinery (CAISO precedent). ~$5–9/MWh on a
   CC — material to the price level.
4. **Imports: HQ Phase II + Highgate priced node.** HQ Phase II HVDC (~2000 MW
   into NEMA/Boston), Highgate (VT–HQ), and the Cross-Sound / Northport–Norwalk
   ties to NYISO are priced import tranches; HQ hydro is cheap baseload import.
   For backcast years serve the measured EIA-930 net-interchange schedule;
   validate the priced node with `--priced-interchange`. ISO-NE is a steady
   net importer (HQ) — verify the sign.
5. **Northfield Mountain pumped storage (~1.1 GW) is storage, not energy.**
   Load it from EIA-860 prime-mover PS with duration/RTE per the PJM/CAISO
   pattern; conventional hydro (ME/NH) is modest — monthly EIA-923 energy
   budgets, smaller than NYISO's.
6. **Nuclear: Millstone (CT) + Seabrook (NH) baseload with refuel calendar.**
   ~3.5 GW combined; build per-year monthly CF from EIA-923 (refuel outages —
   verify from data) and wire like ERCOT/CAISO nuclear. Pilgrim is **retired
   (2019)** — confirm absent.
7. **Net-load / BTM convention (playbook §8.1):** demand stays net of BTM PV
   (material in MA/CT); front-of-meter only. Forecast gross-up is the
   build-once BTM module.

## 4. Waves and dependencies

```
WAVE 0 (one session):        P0 audit + calibration reference
WAVE 1 (parallel sessions):  P1 outages    P3 CHP+nuclear   P4 hydro/PS
                             P5 BESS       P6 renewables    P7 gas+carbon
                             P8 demand     P9 imports       P10 LMP benchmark
                             P13 dual-fuel activation
WAVE 1b (after P1+P3):       P2 offer-curve tranches & bins
WAVE 2 (sequential):         P11 smoke 2024 → P12 full 2023–2025 + dashboard
ANY TIME (independent):      P14 docs sign-off (last)
```

Wave-1 packs touch disjoint scripts/data and parallelize safely. P7 (AGT
basis) and P13 (dual-fuel) are tightly coupled — run P7 first or coordinate;
together they are the make-or-break for NEISO winter prices. P2 needs P1+P3.

Every prompt below assumes: read `claude.md`, `docs/multi-iso/05-backcast-playbook.md`,
and the files it names; branch `claude/neiso-<pack>-<slug>`; run the full
test suite; **ERCOT+PJM+CAISO regression guard** (their outputs byte-identical);
commit at the pack boundary; log derived-parameter sources in
`docs/parameter-citations.md`.

---

## 5. The prompts

### P0 — Data audit & calibration reference (Wave 0)

```
NEISO backcast Stage E: extend the calibration reference and audit data
readiness. Read claude.md, docs/multi-iso/05-backcast-playbook.md (§1–2),
docs/multi-iso/08-neiso-prompt-pack.md, and
scripts/build_calibration_reference.py.

1. Add "NEISO" to CALIBRATION_ISOS (years 2023, 2024, 2025) with ba_code
   ISNE. Emit, per year: EIA-930 demand stats from data/eia_hourly/ISNE
   hourly.parquet; EIA-923 by-fuel generation_twh (note the oil column — ISO-NE
   burns real oil in winter); measured Henry Hub; eGRID NEISO
   generation/emissions benchmark; EIA-860 year-end + monthly wind/solar
   capacity with the 4-zone shares. Emit
   data/raw/_validation-source/NEISO_{year}_renewable_capacity.csv and the
   calibration_reference.json blocks. ERCOT/PJM/CAISO outputs byte-identical.
2. Fleet sanity: assemble the NEISO fleet via get_iso_config("NEISO") + the
   ISNE BA filter; report plant count, capacity by class (flag oil and
   dual-fuel prominently), and zone distribution vs ISO-NE CELT/RSP fleet
   totals (web-search the ISO-NE capacity table; cite). Confirm Pilgrim is
   absent. Flag unassigned plants.
3. CEMS coverage: list distinct states of NEISO-fleet fossil plants
   (CT/MA/ME/NH/RI/VT), diff against campd-unit-level/<ST>_<year>.parquet.
   Expected gap: NH_2025 (upload U1).
4. Write/refresh docs/multi-iso/neiso-data-audit.md mapped to the doc-08
   upload manifest (U1–U7).

Acceptance: calibration_reference.json has NEISO 2023–2025 blocks; tests pass;
audit doc committed.
```

### P1 — Unit-outage windows (Wave 1)

```
NEISO backcast: verify/refresh measured unit-outage windows. Read
docs/offer-curve-methodology.md §3 and scripts/derive_campd_unit_outages.py.
NOTE: data/raw/campd-unit-outages-NEISO.csv already exists and is
COMPLETE for 2023+2024+2025 — this pack VERIFIES it (and refreshes 2025 if
NH_2025 lands).

1. If campd-unit-level/NH_2025.parquet exists (upload U1), regenerate to fold
   NH 2025 in; else confirm the CSV is current and note NH-2025 as
   statistical-availability-only.
2. NEISO's fossil fleet is load-following gas (CC/CT/ST) + substantial oil
   peakers/steam, essentially no coal (Merrimack retired): verify the
   event-based rule fires and the coal real-run rule has no NEISO targets.
   Spot-check 5 large plants (e.g. Mystic CCs, Millstone is nuclear so skip,
   Kleen Energy, Canal, Wyman oil steam) against known outages.
3. Verify data/outages.py picks the NEISO CSV up under
   outage_source == "historic" for --iso NEISO, mirroring PJM/CAISO.
4. Document detection coverage: share of NEISO fossil capacity with CEMS
   history vs statistical availability (should be high — full state coverage).

Acceptance: CSV current; overlay loads in a NEISO smoke config;
ERCOT/PJM/CAISO CSVs untouched.
```

### P2 — Offer-curve tranches & bin assignments (Wave 1b — after P1, P3)

```
NEISO backcast: derive per-plant offer-curve tranches and bin assignments.
Read docs/offer-curve-methodology.md, docs/binning-methodology.md,
scripts/derive_cc_committed_pct.py, scripts/derive_thermal_tranches.py, and
the CHP/dual-fuel tags from the P3/P13 sessions.

1. Run committed-% derivation per CC plant from CAMPD NE-state extracts
   (2023–2025). Let the data set committed shares.
2. Derive peaking ranges per CC; tag oil/dual-fuel CT and ST_OIL peakers
   (winter-only, very low annual CF) for the OIL/peaker band.
3. No coal must-run: confirm zero COAL rows; the inflexible layer is CHP BTM
   (P3), nuclear, hydro min-flows, and any reliability/cost-of-service units.
4. Produce NEISO rows for data/raw/reference/custom-bin-assignments.csv (or the per-ISO
   equivalent): Plant_Code, Plant_Group, tranche %s, measured where CAMPD
   supports it, class defaults elsewhere; tag each row's source. Dual-fuel
   facilities split/tag per Plant_Group.
5. Extend tests: NEISO fleet bins load, shares sum to 100, CHP BTM removed
   from LP capacity.

Acceptance: NEISO fleet builds with per-plant tranches; measured-vs-default
breakdown reported; ERCOT/PJM/CAISO bins byte-identical.
```

### P3 — CHP steam hosts & nuclear (Wave 1)

```
NEISO backcast: identify CHP/BTM steam obligations and the nuclear profile.
Read docs/offer-curve-methodology.md §1, the PJM CHP steam-following
implementation (git log 24d5d3d), and data/eia923.py.

1. From EIA-860 (cogen flag, sector) + EIA-923 (fuel use, useful thermal
   output), identify NEISO CHP plants — expect paper-mill cogens (ME),
   university/district-energy hosts (Boston/Cambridge), industrial steam.
   Assign CC_CHP/CT_CHP and per-plant BTM steam must-run % from observed min
   output.
2. Wire through the existing 3-solve steam-following mechanism (config only).
3. Nuclear: build monthly CF per year for Millstone 2&3 (CT) and Seabrook (NH)
   from EIA-923 actuals (refuel outages — verify) and add to
   NUCLEAR_MONTHLY_CF_BY_YEAR. Confirm Pilgrim retired/absent.
4. Emit the CHP plant list + steam floors for P2.

Acceptance: CHP list with measured floors committed (citations); NEISO nuclear
monthly CF in config; ERCOT/PJM/CAISO unchanged.
```

### P4 — Hydro & pumped storage (Wave 1)

```
NEISO backcast: hydro energy budgets and Northfield Mountain PS. Read the
PJM/CAISO hydro+PS wiring (data/hydro.py; model/storage.py) — reuse. NEISO
conventional hydro is modest (ME/NH/VT run-of-river); PS is the bigger item.

1. Build NEISO monthly hydro energy budgets per zone from EIA-923 (2023–2025),
   concentrated in North (ME/NH/VT). Sanity-check vs EIA-930 ISNE hydro.
2. Nameplate caps + min-flow floors from EIA-860.
3. Pumped storage: load Northfield Mountain (~1.1 GW, Central) and Bear Swamp
   from EIA-860 prime-mover PS; duration/RTE per the PJM/CAISO pattern; PS
   dispatch adder knob defaulted off until calibration says otherwise.
4. Tests: monthly hydro dispatch ≤ budget; ERCOT/PJM/CAISO unchanged.

Acceptance: modeled NEISO hydro TWh within ±10% of EIA-923; PS fleet loads
with cited params.
```

### P5 — Battery storage fleet (Wave 1)

```
NEISO backcast: the grid-battery fleet. Read model/storage.py, constants.py
STORAGE_* entries, the CAISO P5 implementation (COD ramp +
battery_dispatch_adder), playbook §8.4.

1. Build the NEISO BESS fleet from
   data/raw/eia-860/eia860_energy_storage_operable.parquet: power MW,
   energy MWh, COD month, zone via plant coords (MA-heavy). Keep co-located
   solar+storage separate.
2. Benchmark vs EIA-930 ISNE battery charge/discharge columns if present.
3. Reuse the battery_dispatch_adder / throughput-cost knob (default 0).
4. Tests: fleet totals vs EIA-860 per year; ramp applies mid-year;
   ERCOT/PJM/CAISO unchanged.

Acceptance: modeled NEISO storage fleet matches EIA-860 totals per year.
```

### P6 — Renewable profiles & curtailment (Wave 1)

```
NEISO backcast: renewable profiles. Read data/renewables.py, the generic ISO
HSL loader, playbook §8.3. NEISO wind/solar is modest and curtailment small —
EIA-930 delivered distribution is the documented default.

1. Wire the EIA-930 ISNE delivered-distribution path for NEISO wind/solar,
   zone-shaped by EIA-860 capacity shares (ME wind in North; distributed
   solar across Central/CT). Benchmark profile means vs EIA-923 CF.
2. If ISO-NE publishes curtailment worth modeling, add the optional
   uncurtailed path + headline; else leave HSL stubbed with a data-needed
   marker. Don't fabricate curtailment.
3. Tests: profile means ≈ EIA-923 CF; ERCOT/CAISO HSL paths untouched.

Acceptance: NEISO dispatch consumes documented renewable profiles;
curtailment treated as fallback.
```

### P7 — Gas pricing, Algonquin winter basis & RGGI (Wave 1) — THE pack

```
NEISO backcast: measured gas costs, Algonquin winter basis, and RGGI in
marginal cost. This is the most important structural pack for NEISO. Read
data/fuel.py (gas_monthly_actuals), policy/carbon.py,
constants.STATE_CARBON_PRICE_BY_ISO, GAS_BASIS_DIFFERENTIAL, and doc-08
design decisions 1–3.

1. Add a GAS_BASIS_DIFFERENTIAL["NEISO"] entry (EIA-923 delivered basis seed,
   cite) — it is currently MISSING. Then enable gas_monthly_actuals for NEISO:
   per-plant EIA-923 monthly delivered gas with nearby-plant/state fallback,
   as PJM/CAISO.
2. Algonquin winter basis (upload U4 — CRITICAL): layer the measured AGT
   daily/monthly basis onto the gas path so Dec–Feb gas MC blows out above
   plant-average 923 (cite). This is what makes ISO-NE winter prices spike and
   is the dual-fuel switch trigger for P13. If U4 absent, document that winter
   will underprice and fall back to measured 923 + a flagged limitation.
3. RGGI: add a NEISO entry to STATE_CARBON_PRICE_BY_ISO for 2023–2025 from
   RGGI auction settlement prices (upload U5 or web-search; cite each year),
   default-on for NEISO backcasts.
4. Tests: NEISO gas MC includes RGGI and the winter basis; ERCOT/PJM/CAISO MC
   unchanged; a CC at 7.0 HR with ~$18/t RGGI shows ~$5–7/MWh uplift, and a
   January AGT-spike hour shows gas MC well above the annual-average level.

Acceptance: measured monthly gas + AGT winter basis + RGGI active in a NEISO
smoke config; citations in parameter-citations.md.
```

### P8 — Demand & zonal load shares (Wave 1)

```
NEISO backcast: demand series and zonal disaggregation. Read data/eia_loader.py,
scripts/derive_load_shares.py, playbook §8.1.

1. System demand: EIA-930 ISNE hourly (td_loss_factor convention). Document
   that NEISO demand is net of BTM PV (front-of-meter only).
2. If data/raw/zone-specific-demand/NEISO/ has zonal load (upload U3):
   derive measured load shares + hourly zonal shapes for the 4 model zones
   (map the 8 ISO-NE zones → North/Central/Boston/Connecticut; document the
   mapping) via derive_load_shares.py, replacing the static RSP
   0.20/0.30/0.21/0.29.
3. Else: keep static shares, Tier 3 — verify, record U3 as the refresh path.
4. Tests: zone shares sum to 1.0; zonal shapes reconcile to the system series.

Acceptance: NEISO demand loads per backcast year with BTM convention
documented; zonal shapes measured if U3 landed.
```

### P9 — Import/export node calibration (Wave 1)

```
NEISO backcast: the priced import/export node. Read
model/transmission.py::build_import_generators / build_export_sinks (the J1
machinery — constants.IMPORT_TRANCHES / EXPORT_TRANCHES),
scripts/derive_import_tranches.py, playbook §8.2, pjm-backcast-2023.md §4.
The HQ_import zone already exists in _neiso_config(); this pack adds tranche
CONSTANTS and calibrates.

1. Add NEISO entries to IMPORT_TRANCHES / EXPORT_TRANCHES: HQ Phase II block
   (cheap hydro into Boston, ~2000 MW), Highgate (VT–HQ), NYISO ties
   (Cross-Sound / Northport–Norwalk into Connecticut); export sinks for export
   hours. Cite the neighbor-price proxy for each (HQ ~ hydro marginal, NYISO ~
   ZONE F/J LBMP). Wire the import zone+links if not already appended.
2. Benchmark: hourly ISNE net interchange from data/eia_hourly/ISNE
   hourly.parquet. ISO-NE is a steady net importer (HQ) — verify sign and
   magnitude.
3. Calibrate tranche prices/quantities so the modeled net-interchange duration
   curve tracks 2023–2025 actuals; serve the measured schedule in backcast
   years; validate the priced node with --priced-interchange.
4. Add net-interchange (annual TWh, duration, diurnal) to the NEISO comparison.

Acceptance: modeled annual net imports within ~±15% of EIA-930; knobs cited
Tier 3; ERCOT/PJM/CAISO unchanged.
```

### P10 — LMP benchmark & zonal-sufficiency test (Wave 1)

```
NEISO backcast: price benchmarks and the 4-zone adequacy test. Read
scripts/derive_actual_lmp.py and data/raw/_validation-source/actual_lmp.json.

1. From data/raw/lmp-data/NEISO/ (upload U2): build NEISO 2023–2025
   entries in actual_lmp.json (DA + RT annual/monthly Hub + zonal averages:
   NEMA/Boston, CT, SEMA, ME) and an hourly series for duration overlays,
   following the ERCOT/PJM/CAISO format.
2. Zonal-sufficiency test (doc-08 design decision): compute actual
   Boston−Hub, CT−Hub, and ME−Hub spread duration curves per year. Report
   p50/p90/p99 spreads, % hours |spread| > $5 and > $20, and where separation
   concentrates (Boston/CT import pockets under summer peak; winter system-wide
   spikes are level, not spread). Gates the 4-zone aggregation.
3. If upload U6 (interface flows+limits) present, run binding-frequency
   analysis to replace Tier-3 RSP TTC seeds with observed limits.
4. Document conclusions in docs/multi-iso/neiso-zonal-adequacy.md.

Acceptance: actual_lmp.json NEISO block complete; spread analysis + TTC
recommendation committed.
```

### P11 — Smoke backcast 2024 (Wave 2)

```
NEISO backcast smoke run. Prereqs: P0–P10 merged (P6/P8/P10 may be in
fallback mode — note which). Read playbook §6 (structural-before-knobs).

1. Run python scripts/run_calibration.py --iso NEISO --year 2024, then
   run_calibration_full.py --iso NEISO --year 2024 --commitment --out-dir
   results/calibration/neiso_smoke_2024.
2. Produce the gap report ordered by the structural checklist: demand/net-load
   → net interchange (HQ) → hydro+PS+storage throughput → gas+AGT basis+RGGI
   price level → dual-fuel/oil coverage → THEN offer-curve bands. Compare
   against the P0 benchmark table (fuel mix incl. oil, LMP level by zone, CO2,
   interchange).
3. Do NOT tune offer bands if a structural row is red — fix or file it.
   NEISO-specific watch items: winter price spikes (AGT basis + dual-fuel),
   oil generation magnitude, HQ import share, Boston/CT congestion.
4. Register the run on the dashboard and log in docs/calibration-log.md.

Acceptance: bundle on the dashboard; ranked gap list with hypotheses and the
owning pack per fix.
```

### P12 — Full calibration loop 2023–2025 (Wave 2)

```
NEISO backcast calibration to sign-off. Prereqs: P11 structural rows green.
Read docs/calibration-log.md (ERCOT/PJM/CAISO passes) for loop discipline and
naming (neiso 1 <slug>, ...).

1. Run 2023–2025 full bundles in parallel with distinct --out-dir; iterate
   offer-curve, hydro/PS, import, gas-basis, and dual-fuel knobs per pass; one
   named hypothesis per pass; register every keeper on the dashboard; log
   every pass.
2. Calibration targets (P0 table): fuel-mix ±5%/class vs EIA-923 (watch oil
   and gas); avg LMP within ~5–10% of zonal actual with duration shape (the
   winter tail is the hard part); CO2 ±10% vs eGRID; net interchange ±15%.
3. NEISO failure modes: winter price tail (AGT basis + dual-fuel switching is
   the make-or-break), oil under/over-generation, HQ import-share drift,
   Boston/CT pocket separation, nuclear refuel months.
4. Record the keeper config; update the doc-00 status table; append citations.

Acceptance: doc-00 Stage G checklist green for NEISO; keeper documented;
dashboard carries the final run set.
```

### P13 — Dual-fuel winter switching activation (Wave 1)

```
NEISO backcast: activate oil/dual-fuel switching — together with P7 this sets
ISO-NE winter prices. Read fleet.py (dual_fuel_plant_groups, the oil fuel type
and OIL offer curve), constants.py oil distillate/residual cost, data/fuel.py,
and doc-08 design decisions 1–2. The machinery exists nationally; this pack
ACTIVATES and validates it for NEISO.

1. From EIA-860 multiple-energy-source / dual-fuel fields, tag NEISO dual-fuel
   CT/ST and oil-steam units (Mystic, Middletown, Montville, Canal, Wyman).
   Confirm dual_fuel_plant_groups returns them.
2. Wire the switch logic: when the measured AGT gas (P7/U4) exceeds distillate
   parity, the unit prices off oil; else gas. Default-off for non-NE/NY ISOs.
3. Validate against a known cold snap (e.g. the Jan/Feb 2023 Arctic event):
   dual-fuel/oil units should price off oil and oil generation should match
   the order of the EIA-923/EIA-930 oil column. ISO-NE burns substantial oil
   in winter — near-0 modeled oil is a red flag.
4. Tests: dual-fuel MC switches on the gas/oil parity; ERCOT/PJM/CAISO MC
   unchanged.

Acceptance: NEISO dual-fuel units switch on measured AGT winter gas; modeled
oil generation matches the winter order of magnitude; citations recorded.
```

### P14 — Documentation sign-off (last)

```
NEISO Stage H. Run the sync-docs flow: reconcile docs (00 status table, 01
manifest staleness, 05/08, data dictionary, offer-curve doc if NEISO
introduced variants) with as-built code; append parameter citations; write
docs/multi-iso/neiso-backcast-2024.md in the style of pjm-backcast-2023.md
(results tables, gaps, hypotheses); CHANGELOG entry.
```
