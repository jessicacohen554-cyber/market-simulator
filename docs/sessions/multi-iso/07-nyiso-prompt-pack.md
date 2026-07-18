# NYISO Backcast Prompt Pack (2026-06)

Status: **ready to run.** This is the NYISO instantiation of the v2 playbook
(`05-backcast-playbook.md`), built from the CAISO template
(`06-caiso-prompt-pack.md`). It is a sequenced set of self-contained prompts
to feed to fresh sessions, plus the upload manifest of data only the user can
fetch (the environment's allowlist blocks EIA/ISO hosts; see
`data-acquisition-report.md`).

Target backcast years: **2023 primary (full CEMS), 2025 secondary; 2024 as
soon as the `NY_2024` CEMS extract lands** (see §2 U1). 2023 is the cleanest
NYISO year for a first pass — full unit-level outage windows already derived.

NYISO is the second non-ERCOT/PJM ISO into the v2 pipeline after CAISO. Unlike
CAISO it is **already multi-zone with topology + zone assignment + outage
windows landed** — so this pack starts at Stage E (calibration reference) and
spends its weight on hydro, downstate congestion, dual-fuel winter switching,
imports, and RGGI, which are the items that actually move NYISO's calibration.

---

## 1. Current state (verified 2026-06-11; P12 sign-off 2026-06-12)

> **P12 sign-off (2026-06-12).** All packs P0–P13 are merged. The 2023
> backcast is at Stage-G keeper (`nyiso p11 smoke 2023` promoted by P12).
> P14 (this doc-sync pass) closes Stage H. Results, gaps, and hypotheses are
> in `docs/multi-iso/nyiso-backcast-2023.md`; keeper config in
> `docs/calibration-best-so-far-nyiso.md`; run log in
> `docs/calibration-log.md` (NYISO P11, P9b, P12). **Update 2026-06-12:** the
> EIA-930 `NYIS hourly` extract was refreshed to span full 2025 and P10/U2 LMP
> landed, so **2025 is now unblocked, run, and price-scored** (`nyiso 2025
> refreshed`, log "NYISO 2025"); only **2024** remains data-blocked (NY_2024
> CEMS). See §5 blocked years in the calibration-best-so-far doc.

Already in repo — **do not re-build**:

- **Topology (Stage A):** `_nyiso_config()` — 5 zones aggregating NYISO's
  11 load zones (A–K): `Upstate_West` (0.365), `Capital_Hudson` (0.175),
  `Lower_Hudson` (0.06), `NYC` (0.28), `Long_Island` (0.12), with
  Central-East / Total-East / UPNY-SENY / Dunwoodie-South / Long-Island
  interface links seeded Tier-3 from the NYISO Gold Book.
- **Zone assignment (Stage B):** full FIPS + lat/lon splitter in
  `zone_assignment.py` (NYC / Long-Island / Lower-Hudson / Capital-Hudson
  county sets; Niagara→Upstate-West, St-Lawrence→Capital-Hudson upstate);
  `_LARGEST_ZONE["NYISO"] = "Upstate_West"` defensive fallback.
- **EIA-930 hourly:** `data/eia_hourly/NYIS hourly.parquet` (demand/fuel/
  interchange); neighbor parquets `PJM`, `ISNE` present for seams.
- **CAMPD unit-level NY:** `NY_2023`, `NY_2025` (`campd-unit-level/`).
  **`NY_2024` is missing** — the one CEMS gap (upload U1).
- **Unit-outage windows:** `campd-unit-outages-NYISO.csv` already derived —
  **2023 (784 windows) + 2025 (706)**; 2024 absent only because `NY_2024`
  CEMS is missing. `campd.ISO_STATES["NYISO"] = ("NY",)`.
- **Market-design registry:** `MarketDesign("NYISO", capacity_market=True,
  net_cone_per_kw_yr=110.0)` (ICAP); `voll=2000` (NYISO bid cap).
- **Fuel machinery (national, generalized):** `oil` fuel type, `OIL` offer
  curve, distillate/residual delivered cost, and **dual-fuel detection**
  (`fleet.py::dual_fuel_plant_groups`) all exist — NYISO needs to *activate
  and calibrate* dual-fuel switching, not build it.
- **Gas basis seed:** `GAS_BASIS_DIFFERENTIAL["NYISO"] = 0.55` (EIA-923
  delivered basis; forecast seed only — backcasts use measured 923).
- **Fleet availability / monthly seasonality:** `FLEET_AVAILABILITY["NYISO"]
  = 0.86`, `GAS_MONTHLY_SEASONALITY["NYISO"]` present.
- **Generalized priced-import node:** `build_import_generators("NYISO")` /
  `build_export_sinks("NYISO")` machinery is built (J1) — NYISO only needs
  **constants** in `IMPORT_TRANCHES`/`EXPORT_TRANCHES` plus calibration.

Missing (the work below): NYISO blocks in `calibration_reference.json` and
`actual_lmp.json`; hub/zonal LMPs; zonal hourly load; Niagara/St-Lawrence
hydro budgets + Blenheim-Gilboa PS; BESS fleet wiring; RGGI in marginal cost;
NYISO import/export tranche constants + calibration; dual-fuel activation;
offer-curve tranche derivation; CHP identification; nuclear monthly CF.

## 2. Upload manifest (user manual tasks — sessions cannot fetch these)

| # | Item | Source | Destination | Needed by |
|---|------|--------|-------------|-----------|
| U1 | CAMPD unit-level `NY_2024.parquet` (hourly CEMS, same schema as `NY_2023`) — unblocks the 2024 backcast year and 2024 outage windows | EPA CAMPD bulk download | `data/raw/campd-unit-level/` | P0/P1 (2024 only) |
| U2 | DA + RT hourly LMPs at NYISO zonal reference buses / trading zones (esp. ZONE A WEST, ZONE F CAPITL, ZONE J N.Y.C., ZONE K LONGIL) 2023–2025 | NYISO OASIS / DAM & RTD LBMP CSVs | `data/raw/lmp-data/NYISO/` | P10 |
| U3 | Zonal hourly actual load by NYISO zone A–K 2023–2025 | NYISO Load Data / OASIS `pal` (Palisades) actual-load CSVs | `data/raw/zone-specific-demand/NYISO/` | P8 |
| U4 | *(critical for price level)* Transco Z6 NY / Iroquois zone daily or monthly delivered gas basis 2023–2025 (winter spikes exceed plant-average 923) | ICE / Platts / EIA NG Weekly (paywalled — web-search may yield monthly) | cite into `constants.py` / gas path | P7 |
| U5 | *(optional)* Niagara / St-Lawrence + Blenheim-Gilboa monthly generation if EIA-923 monthly hydro looks coarse | NYPA reports / EIA-923 (923 is in-repo) | `data/raw/nyiso-hydro/` | P4 (refinement) |
| U6 | *(optional)* RGGI allowance clearing prices 2023–2025 | RGGI Inc. auction results (public — web-search likely suffices) | cite into `STATE_CARBON_PRICE_BY_ISO` | P7 |
| U7 | *(optional)* Central-East / Total-East / Dunwoodie-South interface hourly flows + limits | NYISO OASIS interface-flow / operating-limit postings | `data/raw/iso-specific-transmission/NYISO/` | P10 (TTC validation) |

U2–U4 unblock the full pack. Without U2 the backcast runs but price
calibration is level-only; without U3 zonal load stays on the static Gold-Book
shares; without U4 winter price spikes (the NYISO signature) cannot calibrate.

## 3. NYISO design decisions (made now, applied by the prompts)

1. **Downstate import constraints are the headline congestion story.** The
   NYC (J) and Long Island (K) pockets are import-limited; the Central-East /
   Total-East cutset separates cheap upstate hydro/wind from expensive
   downstate gas/oil. The zonal-sufficiency test (P10) is the empirical gate:
   if modeled J−A and K−A LBMP spread duration curves track actuals, the
   5-zone aggregation holds; if not, refine interface TTCs (U7) before adding
   zones.
2. **Hydro is first-order and must carry an energy budget.** Niagara (~2.4 GW,
   zone A) and St-Lawrence (~0.8 GW, Capital-Hudson upstate) plus conventional
   hydro deliver ~25–30 TWh/yr — model monthly energy budgets from EIA-923,
   not a flat block. Blenheim-Gilboa (~1.2 GW PS) is storage, not energy.
3. **Dual-fuel winter switching sets winter prices.** Downstate CT/ST units
   switch gas→oil when Transco Z6 gas spikes above distillate parity. Activate
   the existing `dual_fuel_plant_groups` machinery for NYISO and let the
   measured monthly gas basis (U4) drive the switch — this is the difference
   between a model that prices a January cold-snap and one that doesn't.
4. **RGGI is in marginal cost, not optional.** NY is a RGGI state; the
   allowance price (~$13–22/t over 2023–2025) × emission rate enters every
   in-state fossil unit's MC. At ~0.4 t/MWh a CC sees ~$5–9/MWh — smaller than
   CA cap-and-trade but still material to the price level. Wire it through the
   same `STATE_CARBON_PRICE_BY_ISO` machinery CAISO uses.
5. **Imports are a calibrated priced node.** HQ (Châteauguay/HVDC into
   Capital-Hudson), PJM (western/Lower-Hudson ties), ISO-NE, and IESO/Ontario
   are all priced import tranches; for backcast years prefer serving the
   measured EIA-930 net-interchange schedule and validate the priced node with
   `--priced-interchange`. NYISO is a net importer (HQ hydro + PJM) — verify
   the sign.
6. **Nuclear: upstate baseload with refuel calendar.** FitzPatrick, Nine Mile
   1&2, Ginna (~3.3 GW upstate, zone A/B/C) run as monthly-CF baseload;
   Indian Point is **retired (Unit 2 2020, Unit 3 2021)** — confirm it is
   absent from the 2023+ fleet. Build the per-year monthly CF from EIA-923.
7. **Net-load / BTM convention (playbook §8.1):** demand stays net of BTM PV;
   only front-of-meter resources are supply. NY's BTM wedge is smaller than
   CA's but growing downstate — document it; forecast gross-up is the
   build-once BTM module.

## 4. Waves and dependencies

```
WAVE 0 (one session):        P0 audit + calibration reference
WAVE 1 (parallel sessions):  P1 outages    P3 CHP+nuclear   P4 hydro/PS
                             P5 BESS       P6 renewables    P7 gas+carbon
                             P8 demand     P9 imports       P10 LMP benchmark
                             P13 dual-fuel activation
WAVE 1b (after P1+P3):       P2 offer-curve tranches & bins
WAVE 2 (sequential):         P11 smoke 2023 → P12 full 2023/2025(+2024) + dashboard
ANY TIME (independent):      P14 docs sign-off (last)
```

Wave-1 packs touch disjoint scripts/data and parallelize safely. P2 needs
P1's unit extracts validated and P3's CHP tags. P7 and P13 share the measured
gas series — run P7 first or coordinate. P11 wants everything except P14.

Every prompt below assumes: read `claude.md`, `docs/multi-iso/05-backcast-playbook.md`,
and the files it names; branch `claude/nyiso-<pack>-<slug>`; run the full
test suite; **ERCOT+PJM+CAISO regression guard** (their outputs byte-identical);
commit at the pack boundary; log derived-parameter sources in
`docs/parameter-citations.md`.

---

## 5. The prompts

### P0 — Data audit & calibration reference (Wave 0)

```
NYISO backcast Stage E: extend the calibration reference and audit data
readiness. Read claude.md, docs/multi-iso/05-backcast-playbook.md (§1–2),
docs/multi-iso/07-nyiso-prompt-pack.md, and
scripts/data/build_calibration_reference.py.

1. Add "NYISO" to CALIBRATION_ISOS and the year override (2023, 2025; add
   2024 when NY_2024 CEMS lands) with ba_code NYIS. Emit, per year: EIA-930
   demand stats from data/eia_hourly/NYIS hourly.parquet; EIA-923 by-fuel
   generation_twh (note the large hydro and the oil column); measured Henry
   Hub; eGRID NYISO generation/emissions benchmark; EIA-860 year-end +
   monthly wind/solar capacity with the 5-zone shares. Emit
   data/raw/_validation-source/NYISO_{year}_renewable_capacity.csv and the
   calibration_reference.json blocks. ERCOT/PJM/CAISO outputs byte-identical.
2. Fleet sanity: assemble the NYISO fleet via get_iso_config("NYISO") + the
   NYIS BA filter; report plant count, capacity by class (flag oil and
   dual-fuel), and zone distribution vs NYISO Gold Book fleet totals
   (web-search the Gold Book capacity table; cite). Confirm Indian Point is
   absent from 2023+. Flag unassigned plants.
3. CEMS coverage: list distinct states of NYISO-fleet fossil plants (expect
   NY only), diff against campd-unit-level/NY_<year>.parquet. Expected gap:
   NY_2024 (upload U1).
4. Write/refresh docs/multi-iso/nyiso-data-audit.md mapped to the doc-07
   upload manifest (U1–U7).

Acceptance: calibration_reference.json has NYISO 2023(/2025) blocks; tests
pass; audit doc committed.
```

### P1 — Unit-outage windows (Wave 1)

```
NYISO backcast: verify/refresh measured unit-outage windows. Read
docs/offer-curve-methodology.md §3 and scripts/data/derive_campd_unit_outages.py.
NOTE: data/raw/campd-unit-outages-NYISO.csv already exists for 2023 +
2025 — this pack VERIFIES it and adds 2024 only if NY_2024 landed.

1. If campd-unit-level/NY_2024.parquet exists (upload U1), regenerate the CSV
   including 2024; else confirm 2023+2025 are current and mark 2024 as
   statistical-availability-only in run configs.
2. NYISO's fossil fleet is load-following gas (CC/CT/ST) plus oil
   peakers/steam, essentially no coal: verify the event-based rule
   (every-hour CF < 2%, ≥ 120 h) fires and the coal real-run rule has no
   NYISO targets. Spot-check 5 large plants (e.g. Ravenswood, Astoria,
   Roseton/Danskammer, Bowline) against known outages.
3. Verify data/outages.py picks the NYISO CSV up under
   outage_source == "historic" for --iso NYISO, mirroring PJM/CAISO wiring.
4. Document detection coverage: share of NYISO fossil capacity with CEMS
   history vs statistical availability.

Acceptance: CSV current for available years; overlay loads in a NYISO smoke
config; ERCOT/PJM/CAISO CSVs untouched.
```

### P2 — Offer-curve tranches & bin assignments (Wave 1b — after P1, P3)

```
NYISO backcast: derive per-plant offer-curve tranches and bin assignments.
Read docs/offer-curve-methodology.md, docs/binning-methodology.md,
scripts/data/derive_cc_committed_pct.py, scripts/data/derive_thermal_tranches.py, and
the CHP/dual-fuel tags from the P3/P13 sessions.

1. Run committed-% derivation per CC plant from CAMPD NY extracts (2023,
   2025; 2024 if present). Let the data set committed shares, don't copy
   ERCOT/CAISO.
2. Derive peaking ranges (duct-firing) per CC; tag ST_GAS/ST_OIL and oil CT
   peakers (spiky, low-CF) for the appropriate offer band.
3. No coal must-run: confirm zero COAL rows; the inflexible layer is CHP BTM
   (P3), nuclear, hydro min-flows, and any RMR/reliability-must-run units
   (web-search NYISO RMR designations; cite).
4. Produce NYISO rows for data/raw/reference/custom-bin-assignments.csv (or the per-ISO
   equivalent): Plant_Code, Plant_Group, Pct_Must_Run/Committed/Economic/
   Peaking, measured where CAMPD supports it, class defaults elsewhere; tag
   each row's source. Mixed/dual-fuel facilities split per Plant_Group.
5. Extend tests: NYISO fleet bins load, shares sum to 100, CHP BTM removed
   from LP capacity.

Acceptance: NYISO fleet builds with per-plant tranches; measured-vs-default
breakdown reported; ERCOT/PJM/CAISO bins byte-identical.
```

### P3 — CHP steam hosts & nuclear (Wave 1)

```
NYISO backcast: identify CHP/BTM steam obligations and the upstate nuclear
profile. Read docs/offer-curve-methodology.md §1 (Must-Run BTM), the PJM CHP
steam-following implementation (git log 24d5d3d), and data/eia923.py.

1. From EIA-860 (cogen flag, sector) + EIA-923 (fuel use, useful thermal
   output), identify NYISO CHP plants — expect NYC steam-district cogens (Con
   Ed steam system: e.g. East River / 74th St), university/industrial hosts.
   Assign CC_CHP/CT_CHP and a per-plant BTM steam must-run % from observed
   minimum output.
2. Wire them through the existing 3-solve steam-following mechanism (config
   only; no new LP code).
3. Nuclear: build monthly CF vectors per year for FitzPatrick, Nine Mile 1&2,
   Ginna from EIA-923 actuals (captures refuel outages — verify from data) and
   add to NUCLEAR_MONTHLY_CF_BY_YEAR the way ERCOT/CAISO nuclear is wired.
   Confirm Indian Point is retired/absent.
4. Emit the CHP plant list + steam floors for P2.

Acceptance: CHP list with measured floors committed (citations); NYISO nuclear
monthly CF in config; ERCOT/PJM/CAISO unchanged.
```

### P4 — Hydro & pumped storage (Wave 1)

```
NYISO backcast: hydro energy budgets and pumped storage. Read the PJM/CAISO
hydro+PS wiring (data/hydro.py; model/storage.py; doc-06 P4) — reuse, not new
design. NYISO hydro is the largest of any ISO in this model (~25–30 TWh/yr).

1. Build NYISO monthly hydro energy budgets per zone from EIA-923 (2023–2025):
   Niagara (~2.4 GW, Upstate-West/zone A), St-Lawrence (~0.8 GW, Capital-
   Hudson upstate), plus conventional/run-of-river. Sanity-check totals vs
   EIA-930 NYIS hydro; preserve the seasonal (spring-freshet) shape.
2. Nameplate caps + min-flow floors from EIA-860 (Niagara/St-Lawrence carry
   treaty min-flows — cite). Split large vs small hydro if warranted.
3. Pumped storage: load Blenheim-Gilboa (~1.2 GW) from EIA-860 prime-mover PS;
   duration/RTE per the PJM/CAISO pattern; include the PS dispatch adder knob
   defaulted off until calibration says otherwise.
4. Tests: monthly hydro dispatch ≤ budget; seasonal shape preserved;
   ERCOT/PJM/CAISO unchanged.

Acceptance: modeled NYISO hydro TWh within ±10% of EIA-923 per year; PS fleet
loads with cited params.
```

### P5 — Battery storage fleet (Wave 1)

```
NYISO backcast: the grid-battery fleet. Read model/storage.py, constants.py
STORAGE_* entries, the CAISO P5 implementation (battery COD ramp +
battery_dispatch_adder), and playbook §8.4.

1. Build the NYISO BESS fleet from
   data/raw/eia-860/eia860_energy_storage_operable.parquet: power MW,
   energy MWh, COD month (intra-year ramp), zone via plant coords. NYISO BESS
   is smaller than CAISO but concentrated downstate (NYC/Long Island) — verify
   the zone split. Keep co-located solar+storage separate.
2. Benchmark vs EIA-930 NYIS battery charge/discharge columns if present.
3. Reuse the battery_dispatch_adder / throughput-cost knob (CAISO precedent)
   defaulted to 0.
4. Tests: fleet totals vs EIA-860 per year; ramp applies mid-year;
   ERCOT/PJM/CAISO unchanged.

Acceptance: modeled NYISO storage fleet matches EIA-860 totals per year.
```

### P6 — Renewable profiles & curtailment (Wave 1)

```
NYISO backcast: renewable profiles. Read data/renewables.py, the generic ISO
HSL loader, playbook §8.3. NYISO wind/solar is modest vs CAISO/ERCOT and
curtailment is small — EIA-930 delivered distribution is the documented
default here.

1. Wire the EIA-930 NYIS delivered-distribution path for NYISO wind/solar,
   zone-shaped by EIA-860 capacity shares (upstate wind in zone A–E; downstate
   + upstate solar). Benchmark profile means vs EIA-923 CF.
2. If NYISO publishes curtailment worth modeling, add it as the optional
   uncurtailed (delivered + curtailed) path and a calibration headline; else
   leave the HSL path stubbed with a clear data-needed marker. Don't fabricate
   curtailment.
3. Tests: profile means ≈ EIA-923 CF; ERCOT/CAISO HSL paths untouched.

Acceptance: NYISO dispatch consumes documented renewable profiles; curtailment
treated as fallback with a clear marker.
```

### P7 — Gas pricing, winter basis & RGGI carbon (Wave 1)

```
NYISO backcast: measured gas costs, winter basis, and RGGI in marginal cost.
Read data/fuel.py (gas_monthly_actuals), policy/carbon.py,
constants.STATE_CARBON_PRICE_BY_ISO, and doc-07 design decisions 3–4.

1. Enable gas_monthly_actuals for NYISO: per-plant EIA-923 monthly delivered
   gas with nearby-plant/state fallback, as PJM/CAISO. Compare the ISO-average
   monthly series to the +0.55 GAS_BASIS_DIFFERENTIAL seed and report the
   delta.
2. Winter basis (upload U4): if a Transco Z6 NY / Iroquois daily-or-monthly
   basis series is present, layer it onto the gas path for downstate plants so
   January/February spikes exceed plant-average 923 (cite). This is the
   dual-fuel switch trigger for P13. If U4 absent, document the limitation and
   fall back to measured 923.
3. RGGI: add a NYISO entry to STATE_CARBON_PRICE_BY_ISO for 2023–2025 from
   RGGI auction settlement prices (upload U6 or web-search; cite each year),
   applied to in-state fossil MC via the existing carbon machinery, default-on
   for NYISO backcasts.
4. Tests: NYISO gas MC includes RGGI; ERCOT/PJM/CAISO MC unchanged; a CC at
   7.0 HR with ~$18/t shows the expected ~$5–7/MWh uplift.

Acceptance: measured monthly gas + RGGI active in a NYISO smoke config; winter
basis applied if U4 landed; citations in parameter-citations.md.
```

### P8 — Demand & zonal load shares (Wave 1)

```
NYISO backcast: demand series and zonal disaggregation. Read data/eia_loader.py
(ERCOT/PJM load patterns), scripts/data/derive_load_shares.py, playbook §8.1.

1. System demand: EIA-930 NYIS hourly (td_loss_factor convention per ERCOT).
   Document that NYISO demand is net of BTM PV (front-of-meter only).
2. If data/raw/zone-specific-demand/NYISO/ has zonal load (upload U3):
   derive measured load shares + hourly zonal shapes for the 5 model zones
   (map A–K → Upstate-West/Capital-Hudson/Lower-Hudson/NYC/Long-Island;
   document the mapping) via the generalized derive_load_shares.py, replacing
   the static Gold-Book 0.365/0.175/0.06/0.28/0.12.
3. Else: keep static shares, tagged Tier 3 — verify, record U3 as the refresh
   path.
4. Tests: zone shares sum to 1.0; zonal hourly shapes reconcile to the system
   series within rounding.

Acceptance: NYISO demand loads per backcast year with BTM convention
documented; zonal shapes measured if U3 landed.
```

### P9 — Import/export node calibration (Wave 1)

```
NYISO backcast: the priced import/export node. Read
model/transmission.py::build_import_generators / build_export_sinks (the
generalized J1 machinery — constants.IMPORT_TRANCHES / EXPORT_TRANCHES),
scripts/data/derive_import_tranches.py, playbook §8.2, and the PJM writeup
(pjm-backcast-2023.md §4). The machinery is built; this pack adds NYISO's
CONSTANTS and calibrates them.

1. Add NYISO entries to IMPORT_TRANCHES / EXPORT_TRANCHES: HQ block
   (cheap hydro into Capital-Hudson, seasonal), PJM block (western/Lower-
   Hudson ties), ISO-NE and IESO/Ontario blocks; export sinks for hours NYISO
   exports. Cite the neighbor-price proxy for each (HQ ~ Mid-C/NE hydro, PJM ~
   Western Hub). Wire extend_with_import_node to append the import zone+links.
2. Benchmark: hourly NYIS net interchange from data/eia_hourly/NYIS
   hourly.parquet (per-neighbor splits if present). NYISO is typically a net
   importer (HQ + PJM) — verify sign and magnitude.
3. Calibrate tranche prices/quantities so the modeled net-interchange duration
   curve tracks 2023–2025 actuals. For backcast years prefer serving the
   measured schedule; validate the priced node with --priced-interchange.
4. Add net-interchange (annual TWh, duration curve, diurnal) to the NYISO
   calibration comparison.

Acceptance: modeled annual net imports within ~±15% of EIA-930; knob values
cited Tier 3; ERCOT/PJM/CAISO unchanged.
```

### P10 — LMP benchmark & zonal-sufficiency test (Wave 1)

```
NYISO backcast: price benchmarks and the 5-zone adequacy test. Read
scripts/data/derive_actual_lmp.py and data/raw/_validation-source/actual_lmp.json.

1. From data/raw/lmp-data/NYISO/ (upload U2): build NYISO 2023–2025
   entries in actual_lmp.json (DA + RT annual/monthly zonal LBMP averages,
   esp. WEST/CAPITL/N.Y.C./LONGIL) and an hourly series file for duration
   overlays, following the ERCOT/PJM/CAISO format.
2. Zonal-sufficiency test (doc-07 design decision 1): compute actual
   J−A (NYC−West) and K−A (LongIsland−West) and CAPITL−WEST spread duration
   curves per year. Report p50/p90/p99 spreads, % hours |spread| > $5 and
   > $20, and where separation concentrates (summer downstate peaks, winter
   gas spikes). This gates the 5-zone aggregation.
3. If upload U7 (interface flows+limits) is present, run the binding-frequency
   analysis to replace Tier-3 Gold-Book TTC seeds with observed limits.
4. Document conclusions in docs/multi-iso/nyiso-zonal-adequacy.md.

Acceptance: actual_lmp.json NYISO block complete; spread analysis + TTC
recommendation committed.
```

### P11 — Smoke backcast 2023 (Wave 2)

```
NYISO backcast smoke run. Prereqs: P0–P10 merged (P6/P8/P10 may be in
fallback mode — note which). Use 2023 as the smoke year (full CEMS; 2024
blocked on NY_2024). Read playbook §6 (structural-before-knobs).

1. Run python scripts/run_calibration.py --iso NYISO --year 2023, then
   run_calibration_full.py --iso NYISO --year 2023 --commitment --out-dir
   results/calibration/nyiso_smoke_2023.
2. Produce the gap report ordered by the structural checklist: demand/net-load
   → net interchange → hydro+storage throughput → gas+RGGI price level →
   dual-fuel/outage coverage → THEN offer-curve bands. Compare against the P0
   benchmark table (fuel mix incl. hydro+oil, LBMP level by zone, CO2,
   interchange).
3. Do NOT tune offer bands if a structural row is red — fix or file it (PJM
   lesson). NYISO-specific watch items: hydro displacement, downstate
   congestion price separation, winter dual-fuel switching.
4. Register the run on the dashboard and log the pass in docs/calibration-log.md.

Acceptance: bundle on the dashboard; ranked gap list with hypotheses and the
owning pack per fix.
```

### P12 — Full calibration loop (Wave 2)

```
NYISO backcast calibration to sign-off. Prereqs: P11 structural rows green.
Read docs/calibration-log.md (ERCOT/PJM/CAISO passes) for loop discipline and
naming (nyiso 1 <slug>, nyiso 2 <slug>, ...).

1. Run 2023 + 2025 (and 2024 once NY_2024 lands) full bundles in parallel with
   distinct --out-dir; iterate offer-curve, hydro, storage, import, and
   dual-fuel knobs per pass; one named hypothesis per pass; register every
   keeper on the dashboard; log every pass.
2. Calibration targets (P0 table): fuel-mix ±5%/class vs EIA-923 (watch hydro
   and oil); avg LBMP within ~5–10% of zonal actual with duration shape; CO2
   ±10% vs eGRID; net interchange ±15%.
3. NYISO failure modes: downstate price separation (interface TTCs), winter
   spikes (gas basis + dual-fuel), hydro over/under-displacement, import-share
   drift, nuclear refuel months.
4. Record the keeper config; update the doc-00 status table; append citations.

Acceptance: doc-00 Stage G checklist green for NYISO; keeper documented;
dashboard carries the final run set.
```

### P13 — Dual-fuel winter switching activation (Wave 1)

```
NYISO backcast: activate oil/dual-fuel switching. Read fleet.py
(dual_fuel_plant_groups, the oil fuel type and OIL offer curve),
constants.py oil distillate/residual cost, data/fuel.py, and doc-07 design
decision 3. The machinery exists nationally; this pack ACTIVATES it for NYISO
and validates against winter behavior.

1. From EIA-860 multiple-energy-source / dual-fuel fields, tag NYISO downstate
   dual-fuel CT/ST units (Ravenswood, Astoria, etc.). Confirm
   dual_fuel_plant_groups returns them.
2. Wire the switch logic: when the measured monthly Transco Z6 gas (P7/U4)
   exceeds distillate parity, the unit's MC follows oil; else gas. Default-off
   for non-NE/NY ISOs.
3. Validate: in a January 2023 (or a known cold-snap) smoke window, dual-fuel
   units should price off oil and oil generation should be non-zero vs the
   EIA-923/EIA-930 oil column (NYISO burns measurable oil in winter — 0 oil is
   a red flag).
4. Tests: dual-fuel MC switches on the gas/oil parity; ERCOT/PJM/CAISO MC
   unchanged.

Acceptance: NYISO dual-fuel units switch on measured winter gas; modeled oil
generation is non-trivial in cold months; citations recorded.
```

### P14 — Documentation sign-off (last)

> **Done — 2026-06-12.** sync-docs pass completed: doc-00 status table
> (P12 already updated it), doc-01 manifest table (NYISO/CAISO/PJM/NEISO
> EIA-930 rows marked present), doc-07 §1 update banner added. New file
> `docs/multi-iso/nyiso-backcast-2023.md` written (results tables, the
> served-interchange structural fix, 2024/2025 data blocks, hypotheses).
> CHANGELOG entry appended.

```
NYISO Stage H. Run the sync-docs flow: reconcile docs (00 status table, 01
manifest staleness, 05/07, data dictionary, offer-curve doc if NYISO
introduced variants) with as-built code; append parameter citations; write
docs/multi-iso/nyiso-backcast-2023.md in the style of pjm-backcast-2023.md
(results tables, gaps, hypotheses); CHANGELOG entry.
```
