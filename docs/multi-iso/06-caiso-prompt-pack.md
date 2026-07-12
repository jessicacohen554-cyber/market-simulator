# CAISO Backcast Prompt Pack (2026-06)

Status: **ready to run.** This is the CAISO instantiation of the v2 playbook
(`05-backcast-playbook.md`) — a sequenced set of self-contained prompts to
feed to fresh sessions, plus the upload manifest of data only the user can
fetch (the environment's allowlist blocks EIA/ISO hosts; see
`data-acquisition-report.md`). It also doubles as the template prompt pack
for NYISO/MISO/NEISO/SPP.

Target backcast years: **2024 primary; 2023 and 2025 as data lands**
(2023 = wet hydro + Diablo at full output; 2024/2025 = the big-battery era).

---

## 1. Current state (verified 2026-06-10)

Already in repo — do not re-acquire:

- Topology: `_caiso_config()` — NP15/ZP26/SP15 + `WECC_import` node, Path
  15/26 TTCs (WECC catalog, Tier 3), COI/WOR import links; lat-band zone
  splitter in `zone_assignment.py`.
- WECC import machinery: generalized per-ISO in J1 (2026-06-11) —
  `model/transmission.py::build_import_generators("CAISO")` /
  `build_export_sinks("CAISO")` off `constants.IMPORT_TRANCHES` /
  `EXPORT_TRANCHES` (tranche supply curve + export sink), with
  `scripts/derive_import_tranches.py` to fit them — needs calibration,
  not construction. The runner now also wires the CAISO export sink in.
- `data/eia_hourly/CISO hourly.parquet` (EIA-930 demand/fuel/interchange).
- `data/raw/CISO_fueltype.parquet`, `CISO_region.parquet`.
- CAMPD unit-level CA **2023, 2024, 2025**
  (`campd-unit-level/CA_{2023,2024,2025}.parquet`); facility-level CA
  2023–2025; derived `campd-unit-outages-CAISO.csv` (2023–2025 windows,
  1,933 total).
- EIA-860 (incl. energy-storage operable/proposed/retired parquets), EIA-923
  zips 2023–2025, eGRID 2023/2024, Henry Hub daily/monthly — all national.
- Market-design registry: CAISO RA (`capacity_market=True`), CA RPS entry,
  VOLL $2,000, `GAS_BASIS_DIFFERENTIAL["CAISO"] = +1.20` (Tier-3 seed).

Missing (the work below): CAISO entries in `actual_lmp.json`; hub LMPs;
TAC-area load; curtailment/uncurtailed profiles;
hydro/PS/BESS fleet wiring for CAISO; calibrated import curve; offer-curve
tranche derivation for the CAISO fleet; CHP identification. Done since:
calibration reference (P0); gas + carbon (P7 — measured monthly gas
default-on, CARB allowance in MC, border carbon on import tranches).

## 2. Upload manifest (user manual tasks — sessions cannot fetch these)

| # | Item | Source | Destination | Needed by |
|---|---|---|---|---|
| U1 | CAMPD unit-level `CA_2023.parquet` (hourly CEMS, same schema as CA_2024) — **done (2026-06-11)**: landed and `derive_campd_unit_outages.py --iso CAISO` regenerated `campd-unit-outages-CAISO.csv` (612 new 2023 windows; 2024/2025 byte-identical) | EPA CAMPD bulk download | `data/raw/campd-unit-level/` | P1 (only for the 2023 year) |
| U2 | DA + RT hourly LMPs at TH_NP15, TH_SP15, TH_ZP26 (gen hubs), 2023–2025 | CAISO OASIS `PRC_LMP` (DAM) + `PRC_INTVL_LMP` (RTM, hourly-averaged) | `data/raw/lmp-data/CAISO/` | P10 |
| U3 | Wind & Solar Production-and-Curtailment data, 2023–2025 (hourly or 5-min) | CAISO "Managing Oversupply" / daily curtailment reports | `data/raw/caiso-curtailment/` | P6 |
| U4 | TAC-area actual hourly load (PGE/SCE/SDGE TACs), 2023–2025 | CAISO OASIS `SLD_FCST` with `market_run_id=ACTUAL` (monthly loops; ≥5 s between calls) | `data/raw/zone-specific-demand/CAISO/` | P8 |
| U5 | *(optional)* Path 15 / Path 26 hourly flows + limits | CAISO OASIS transmission-interface usage reports | `data/raw/iso-specific-transmission/CAISO/` | P10 (TTC validation) |
| U6 | *(optional)* CARB cap-and-trade auction settlement prices 2023–2025 | CARB auction results (public PDFs/CSV; web-search may suffice) | cite into `constants.py` | P7 |
| U7 | *(optional, forecast module)* CA BTM PV + storage capacity by year | EIA-861 small-scale PV / CEC tracking | `data/raw/caiso-btm/` | P13 |

U1–U4 unblock the full pack. Without U2 the backcast still runs but price
calibration is level-only; without U3 renewables fall back to the EIA-930
delivered distribution (no re-curtailment fidelity); without U4 zonal load
stays on static shares.

## 3. CAISO design decisions (made now, applied by the prompts)

1. **BTM solar / DER — net-load convention** (playbook §8.1): backcast
   demand stays net of BTM; only front-of-meter resources are supply.
   The ~15+ GW BTM PV wedge lives inside the demand shape, which is
   correct and self-consistent for backcasts. Forecast-side gross-up is
   P13, a separate build-once module.
2. **Imports are a calibrated supply curve, not a fixed schedule**:
   keep the existing WECC pseudo-generator pattern; calibrate tranches to
   the EIA-930 net-interchange duration curve; seasonal (NW hydro)
   shaping if the residuals demand it. CAISO-owned out-of-state plants
   (e.g. Palo Verde shares) stay inside the import curve initially —
   don't model AZ/NV CEMS units.
3. **Zonal granularity — keep 3 zones until the hub-spread test fails**:
   NP15/ZP26/SP15 match CAISO's trading hubs, so the actual hub LMP
   spreads (U2) are the direct empirical test: if modeled NP15–SP15
   spread duration tracks actuals, 3 zones suffice; if actual spreads
   show congestion regimes the model can't reproduce, refine TTCs first
   (U5), and only then consider more zones. Intra-zonal/local congestion
   (e.g. SDG&E pocket) is out of scope at hub fidelity.
4. **Must-run profile without coal**: CAISO's inflexible layer = CHP steam
   hosts (Kern EOR, refineries), Diablo Canyon, hydro min-flows, and any
   RMR units — not a coal floor. Tranche derivation reflects this.
5. **Carbon is in marginal cost**: CA cap-and-trade allowance price
   (~$30–42/t over 2023–2025) × emission rate enters every in-state
   fossil unit's MC *and* the import tranche price (CAISO levies a border
   carbon adjustment on unspecified imports). At ~0.4 t/MWh a CC sees
   ~$12–17/MWh — without this the price level cannot calibrate.
6. **Storage is first-order**: ~10+ GW of grid BESS by 2024–2025 sets the
   evening net-load peak price. Fleet from EIA-860 storage tables with
   COD-based intra-year ramp; cycling benchmarked to the EIA-930 CISO
   battery columns; expect a throughput/cycling cost knob (ERCOT/PJM PS
   precedent).

## 4. Waves and dependencies

```
WAVE 0 (one session):        P0 audit + calibration reference
WAVE 1 (parallel sessions):  P1 outages   P3 CHP+nuclear   P4 hydro/PS
                             P5 BESS      P6 renewables    P7 gas+carbon
                             P8 demand    P9 imports       P10 LMP benchmark
WAVE 1b (after P1+P3):       P2 offer-curve tranches & bins
WAVE 2 (sequential):         P11 smoke 2024 → P12 full 2023–2025 + dashboard
ANY TIME (independent):      P13 BTM/DER forecast module   P14 docs sign-off (last)
```

Wave-1 packs touch disjoint scripts/data and parallelize safely. P2 needs
P1's unit extracts validated and P3's CHP tags. P11 wants everything except
P13.

Every prompt below assumes: read `claude.md`, `docs/multi-iso/05-backcast-playbook.md`,
and the files it names; branch `claude/caiso-<pack>-<slug>`; run the full
test suite; **ERCOT+PJM regression guard** (their outputs unchanged); commit
at the pack boundary; log derived-parameter sources in
`docs/parameter-citations.md`.

---

## 5. The prompts

### P0 — Data audit & calibration reference (Wave 0)

```
CAISO backcast Stage E: extend the calibration reference and audit data
readiness. Read claude.md, docs/multi-iso/05-backcast-playbook.md (§1–2),
and scripts/build_calibration_reference.py.

1. Add CAISO to build_calibration_reference.py for 2023–2025: EIA-930
   demand stats from data/eia_hourly/CISO hourly.parquet; EIA-923 by-fuel
   generation_twh; measured Henry Hub; eGRID CAISO generation/emissions
   benchmark; EIA-860 year-end + monthly wind/solar capacity with
   NP15/ZP26/SP15 zone shares. Emit data/raw/_validation-source/CAISO_{year}_renewable_capacity.csv
   and the calibration_reference.json blocks. ERCOT/PJM outputs must be
   byte-identical.
2. Fleet sanity: assemble the CAISO fleet via get_iso_config("CAISO") +
   the CISO BA filter; report plant count, capacity by class, and zone
   distribution vs CAISO published fleet totals (web-search for the NQC
   list / CAISO annual report figures; cite). Flag unassigned plants.
3. CEMS coverage: list distinct states of CAISO-fleet fossil plants, diff
   against data/raw/campd-unit-level/<ST>_<year>.parquet. Expected
   gap: CA_2023. Confirm whether any non-CA plants in the CISO BA carry
   CEMS obligations worth covering.
4. Write docs/multi-iso/caiso-data-audit.md: what is present, what is
   missing, mapped to the doc-06 upload manifest (U1–U7).

Acceptance: calibration_reference.json has complete CAISO 2023–2025
blocks; tests pass; audit doc committed.
```

### P1 — Unit-outage windows (Wave 1)

```
CAISO backcast: regenerate measured unit-outage windows. Read
docs/offer-curve-methodology.md §3 and scripts/derive_campd_unit_outages.py.

1. If data/raw/campd-unit-level/CA_2023.parquet exists (upload U1),
   include 2023; otherwise run 2024–2025 and note 2023 as statistical-
   availability-only in the run config.
2. Regenerate data/raw/campd-unit-outages-CAISO.csv for all
   available years. CAISO's fossil fleet is load-following gas (CC/ST/CT,
   essentially no coal): verify the event-based rule (every-hour CF < 2%,
   ≥ 120 h) is what fires; confirm the coal real-run rule has no CAISO
   targets. Spot-check 5 large plants (e.g. Moss Landing CCs, Delta
   Energy Center) against known 2024 outages.
3. Verify data/outages.py picks the CAISO CSV up under
   outage_source == "historic" for --iso CAISO, mirroring the
   campd-outages-PJM.csv wiring.
4. Document detection coverage: share of CAISO gas capacity with CEMS
   history vs statistical availability.

Acceptance: regenerated CSV committed with 2024+2025 (and 2023 if U1
landed); overlay loads in a CAISO smoke config; ERCOT/PJM CSVs untouched.
```

### P2 — Offer-curve tranches & bin assignments (Wave 1b — after P1, P3)

```
CAISO backcast: derive per-plant offer-curve tranches (committed %,
must-run, peaking ranges) and build the CAISO bin assignments. Read
docs/offer-curve-methodology.md, docs/binning-methodology.md,
scripts/derive_cc_committed_pct.py, scripts/derive_thermal_tranches.py,
and the CHP tags from the P3 session (CC_CHP/CT_CHP assignments).

1. Run committed-% derivation per CC plant from CAMPD unit-level CA
   extracts (2024–2025; 2023 if present) — CAISO CCs cycle daily on the
   solar ramp, so expect committed shares well below ERCOT's; let the
   data speak, don't copy ERCOT values.
2. Derive peaking ranges (duct-firing share) per CC and flag ST_GAS
   peaker-style spiky runners for the exclusion list.
3. No coal must-run: confirm zero COAL rows; the must-run layer is CHP
   BTM (P3), nuclear, hydro min-flows.
4. Produce the CAISO rows for data/raw/reference/custom-bin-assignments.csv (or the
   per-ISO equivalent the loader expects): Plant_Code, Plant_Group,
   Pct_Must_Run/Committed/Economic/Peaking, using measured values where
   CAMPD supports them and class defaults elsewhere; tag each row's
   source. Mixed facilities split per Plant_Group (tag_mixed_plants.py).
5. Extend tests: CAISO fleet bins load, shares sum to 100, CHP BTM
   capacity is removed from LP capacity.

Acceptance: CAISO fleet builds with per-plant tranches; tranche-source
breakdown (measured vs default) reported; ERCOT/PJM bins byte-identical.
```

### P3 — CHP steam hosts & nuclear (Wave 1)

```
CAISO backcast: identify CHP/BTM steam obligations and the Diablo Canyon
profile. Read docs/offer-curve-methodology.md §1 (Must-Run BTM), the PJM
CHP steam-following implementation (git log 24d5d3d and the code it
touched), and data/eia923.py.

1. From EIA-860 (cogen flag, sector) + EIA-923 (fuel use, useful thermal
   output where reported), identify CAISO CHP plants — expect Kern County
   EOR steam cogens, refinery cogens, industrial hosts. Assign
   CC_CHP/CT_CHP groups and a per-plant BTM steam must-run % consistent
   with their observed minimum output (CAMPD where available, 923 monthly
   floor otherwise).
2. Wire them through the same steam-following mechanism PJM uses (3-solve
   commitment + steam-floor perturbation) — config only; no new LP code.
3. Diablo Canyon: build the monthly CF vector per year from EIA-923
   actuals (captures refueling outages: one unit down ~Oct 2023, etc. —
   verify from the data, don't assume) and wire it the way ERCOT's
   nuclear monthly CF is wired.
4. Emit the CHP plant list + steam floors for P2's bin assignment.

Acceptance: CHP list with measured floors committed (citations); nuclear
monthly CF in config; ERCOT/PJM unchanged.
```

### P4 — Hydro & pumped storage (Wave 1)

```
CAISO backcast: hydro energy budgets and pumped storage. Read the PJM
hydro/PS wiring (docs/calibration-log.md 2026-06 entries; data/hydro.py;
model/storage.py) — this is reuse, not new design.

1. Build CAISO monthly hydro energy budgets per zone from EIA-923
   (2023–2025). 2023 was an extreme wet year; verify the year-to-year
   swing is preserved (roughly 2x between wet and dry — sanity-check
   totals against EIA-930 CISO hydro).
2. Nameplate caps + min-flow floors from EIA-860; small-hydro vs large
   split if the data warrants.
3. Pumped storage: load CAISO PS plants from EIA-860 prime-mover PS
   (Helms ~1.2 GW, others); duration/RTE params per the PJM pattern;
   include the PS dispatch adder knob (PJM's $10/MWh reduced-form reserve
   duty) defaulted off for CAISO until calibration says otherwise.
4. Tests: monthly hydro dispatch ≤ budget; wet-vs-dry year totals differ
   accordingly; ERCOT/PJM unchanged.

Acceptance: CAISO 2023 vs 2024 modeled hydro TWh within ±10% of EIA-923;
PS fleet loads with cited params.
```

### P5 — Battery storage fleet (Wave 1)

```
CAISO backcast: the grid-battery fleet. Read model/storage.py,
constants.py STORAGE_* entries, and playbook §8.4.

1. Build the CAISO BESS fleet from
   data/raw/eia-860/eia860_energy_storage_operable.parquet: power
   MW, energy MWh (duration), COD month (CAISO added GWs mid-year every
   year — model the intra-year capacity ramp, not just year-end), zone
   via plant coords. Keep co-located solar+storage as separate resources.
2. Benchmark: check data/eia_hourly/CISO hourly.parquet and
   data/raw/CISO_fueltype.parquet for the EIA-930 battery
   charge/discharge columns; if present, add battery throughput and the
   evening-discharge shape to the CAISO calibration comparison.
3. Add a cycling/throughput cost knob (cite degradation-cost literature,
   Tier 3) defaulted to 0 so calibration can tame over-cycling — the
   ERCOT PS over-discharge (9–10 vs 3–4 TWh) is the cautionary precedent.
4. Tests: fleet totals vs published CAISO battery capacity (~10+ GW by
   2024 — cite); ramp applies mid-year; ERCOT/PJM unchanged.

Acceptance: modeled CAISO storage fleet matches EIA-860 totals per year;
benchmark columns wired if present.
```

### P6 — Renewable profiles & curtailment (Wave 1)

```
CAISO backcast: uncurtailed renewable potential (the HSL analogue). Read
data/renewables.py, scripts/build_ercot_hsl.py, playbook §8.3.

1. If data/raw/caiso-curtailment/ exists (upload U3): build hourly
   uncurtailed wind/solar = EIA-930 delivered + reported curtailment,
   zone-shaped by EIA-860 capacity shares; emit a CAISO HSL-style parquet
   mirroring ercot-hsl/ and teach load_renewable_profiles() to use it for
   CAISO. CAISO solar curtailment is multi-TWh — this is the difference
   between a model that can re-curtail and one that can't.
2. If U3 hasn't landed: wire the EIA-930 delivered-distribution fallback
   for CAISO explicitly, and leave the HSL path stubbed with a clear
   data-needed marker. Don't fabricate curtailment.
3. Add modeled-vs-reported curtailment (TWh per year, monthly shape) to
   the CAISO calibration report as a headline metric.
4. Tests: profile means ≈ EIA-923 CF; uncurtailed ≥ delivered everywhere;
   ERCOT HSL path untouched.

Acceptance: CAISO dispatch consumes uncurtailed profiles (or documented
fallback); curtailment metric appears in the comparison output.
```

### P7 — Gas pricing & carbon cost (Wave 1)

```
CAISO backcast: measured gas costs and CA cap-and-trade in marginal cost.
Read data/fuel.py, the gas_monthly_actuals flag (PJM 2026-06 work),
policy/carbon.py, and doc-06 design decision 5.

1. Enable gas_monthly_actuals for CAISO: per-plant EIA-923 monthly
   delivered gas with the nearby-plant/state fallback, exactly as PJM.
   Compare the resulting ISO-average monthly series against the +1.20
   GAS_BASIS_DIFFERENTIAL seed and report the delta (SoCal vs PG&E
   territories will differ; the per-plant path should capture it).
2. CA cap-and-trade: add a CAISO-default carbon price series 2023–2025
   from CARB auction settlement prices (upload U6 or web-search the
   public auction results; cite each year), applied to in-state fossil MC
   via the existing carbon machinery, default-on for CAISO backcasts and
   off elsewhere.
3. Import carbon: add the border adjustment to WECC import tranche prices
   (unspecified-source emission factor × allowance price; cite CARB's
   0.428 t/MWh unspecified factor).
4. Tests: CAISO gas MC includes carbon; ERCOT/PJM MC unchanged; a CC at
   7.0 HR with $35/t shows the expected ~$13/MWh uplift.

Acceptance: monthly measured gas + carbon both active in a CAISO smoke
config with citations in parameter-citations.md.
```

### P8 — Demand & zonal load shares (Wave 1)

```
CAISO backcast: demand series and zonal disaggregation. Read
data/eia_loader.py (ERCOT native-load and PJM metered-load patterns),
scripts/derive_load_shares.py, playbook §8.1.

1. System demand: EIA-930 CISO hourly (generation-side; td_loss_factor
   convention per ERCOT). Document in the data dictionary that CAISO
   demand is net of ~15+ GW BTM PV and that backcasts model front-of-
   meter resources only (net-load convention) — this is the convention
   note future ISOs will copy.
2. If data/raw/zone-specific-demand/CAISO/ has TAC-area load
   (upload U4): derive measured load shares + hourly zonal shapes
   (PGE-TAC→NP15+ZP26 split, SCE+SDGE→SP15; document the mapping) via a
   generalized derive_load_shares.py, replacing the static 0.43/0.07/0.50.
3. Else: keep static shares, tagged Tier 3 — verify, and record U4 as the
   refresh path.
4. Tests: zone shares sum to 1.0; zonal hourly shapes reconcile to the
   system series within rounding.

Acceptance: CAISO demand loads per backcast year with documented BTM
convention; zonal shapes measured if U4 landed.
```

### P9 — Import/export calibration (Wave 1)

```
CAISO backcast: calibrate the WECC import node. Read
model/transmission.py::build_import_generators / build_export_sinks (the
J1-generalized machinery — constants.IMPORT_TRANCHES / EXPORT_TRANCHES),
scripts/derive_import_tranches.py (the PJM fitting workflow to reuse),
playbook §8.2, and the PJM writeup (docs/sessions/multi-iso/pjm-backcast-2023.md
§4, archived). The machinery is built AND on by default for CAISO
(constants.PRICED_INTERCHANGE_DEFAULT_ISOS — CAISO backcasts serve the
priced WECC node without the --priced-interchange flag, since CAISO has no
measured-schedule mode); this pack only fits CAISO's tranche entries.

1. Benchmark: hourly CISO net interchange from data/eia_hourly/CISO
   hourly.parquet (and per-neighbor splits if the parquet carries them).
   CAISO imports ~20–25% of energy — this is the single biggest supply
   block after gas.
2. Calibrate the import tranche prices/quantities so the modeled
   net-interchange duration curve tracks 2023–2025 actuals: cheap
   hydro/baseload block (NW, seasonal by hydro year), mid block (desert
   Southwest solar hours), expensive marginal block; export sink for
   midday oversupply (CAISO exports during solar peak — verify the model
   reproduces the sign flip).
3. Apply P7's border-carbon adder to tranche prices.
4. Add net-interchange (annual TWh, duration curve, diurnal shape) to the
   CAISO calibration comparison.

Acceptance: modeled annual net imports within ~±15% of EIA-930 and the
diurnal import/export sign pattern reproduced; knob values cited as
Tier 3 calibration parameters.
```

**Status — tranche fit DONE (2026-06-12).** `IMPORT_TRANCHES["CAISO"]` /
`EXPORT_TRANCHES["CAISO"]` were fitted to the pooled 2023-2025 CISO
net-interchange duration curve with `derive_import_tranches.py` (measured-only
mode — the existing CAISO bundle has no priced node, so a bundle-mode price fit
would be circular). Six import blocks (PNW hydro baseload → desert-SW gas →
west-wide scarcity, 11.4 GW total) + two export sinks (midday-solar surplus +
$0 curtailment floor, 6.5 GW). Price-orthogonal fit vs the measured series:
annual net imports within 1-3%, duration-curve RMSE ~560 MW (was ~1,400 for the
placeholder), import-hour share 83-88% vs 86-91% measured; aggregate import
capacity sits between the deepest measured hour (11.0 GW) and the ~12-15 GW WECC
simultaneous-import rating. Remaining: re-score the *modeled* net-interchange
(clearing frequency vs the solved CAISO price duration curve) once P10/P11 run
a CAISO bundle with the priced node on.

### P10 — LMP benchmark & zonal-sufficiency test (Wave 1)

```
CAISO backcast: price benchmarks and the 3-zone adequacy test. Read
scripts/derive_actual_lmp.py and data/raw/_validation-source/actual_lmp.json.

1. From data/raw/lmp-data/CAISO/ (upload U2): build CAISO
   2023–2025 entries in actual_lmp.json (DA + RT annual/monthly hub
   averages) and an hourly series file for duration-curve overlays,
   following the ERCOT/PJM format.
2. Zonal-sufficiency test (doc-06 design decision 3): compute the actual
   TH_NP15 − TH_SP15 (and ZP26) spread duration curves per year. Report:
   p50/p90/p99 spreads, % hours with |spread| > $5 and > $20, and the
   months/hours where separation concentrates. This is the empirical
   gate: 3 zones stand unless actual spreads show regimes the topology
   cannot produce.
3. If upload U5 (Path 15/26 flows+limits) is present, run
   derive_ttc_limits.py-style binding-frequency analysis to replace the
   Tier-3 WECC-catalog TTC seeds with observed limits.
4. Document conclusions in docs/multi-iso/caiso-zonal-adequacy.md.

Acceptance: actual_lmp.json CAISO block complete; spread analysis + TTC
recommendation committed.
```

### P11 — Smoke backcast 2024 (Wave 2)

```
CAISO backcast smoke run. Prereqs: P0–P10 merged (P6/P8/P10 may be in
fallback mode — note which). Read playbook §6 (structural-before-knobs).

1. Run python scripts/run_calibration.py --iso CAISO --year 2024, then a
   full bundle: run_calibration_full.py --iso CAISO --year 2024
   --commitment --out-dir results/calibration/caiso_smoke_2024.
2. Produce the gap report ordered by the playbook's structural checklist:
   demand/net-load level → net interchange → hydro+storage throughput →
   gas+carbon price level → outage coverage → THEN offer-curve bands.
   Compare against the P0 benchmark table (fuel mix, LMP level, CO2,
   interchange, curtailment, battery throughput).
3. Do NOT tune offer bands in this session if a structural row is red —
   fix or file the structural item instead (PJM lesson: band-tuning a
   structurally wrong system bakes in compensating errors).
4. Register the run on the dashboard and log the pass in
   docs/calibration-log.md.

Acceptance: bundle on the dashboard; ranked gap list with hypotheses and
which pack owns each fix.
```

### P12 — Full calibration loop 2023–2025 (Wave 2)

```
CAISO backcast calibration to sign-off. Prereqs: P11 structural rows
green. Read docs/calibration-log.md (ERCOT + PJM passes) for loop
discipline and naming (caiso 1 <slug>, caiso 2 <slug>, ...).

1. Run 2023–2025 (years with data) full bundles in parallel with
   distinct --out-dir; iterate offer-curve and storage/import knobs per
   pass; one named hypothesis per pass; register every keeper on the
   dashboard; log every pass.
2. Calibration targets (P0 table): fuel-mix ±5%/class vs EIA-923; avg
   LMP within ~5–10% of hub actual with duration shape; CO2 ±10% vs
   eGRID; net interchange ±15%; curtailment sign+magnitude vs reported;
   battery/PS throughput sane vs benchmark.
3. Watch CAISO-specific failure modes: evening ramp prices (battery
   depth), midday negatives (curtailment + export sink), wet-2023 vs
   dry-year hydro displacement, Diablo refuel months, import share drift.
4. Record the keeper config in docs/calibration-best-so-far.md style;
   update the doc-00 status table; append citations.

Acceptance: doc-00 Stage G checklist green for CAISO; keeper documented;
dashboard carries the final run set.
```

### P13 — BTM/DER & VPP forecast module (any time; build-once)

```
Forecast-side BTM module (not needed for backcast). Read playbook §8.1
and design decision 1 in doc 06.

1. Implement gross-load reconstruction: gross = net (EIA-930) + estimated
   BTM PV output (capacity trajectory × a solar shape from the ISO's
   utility-scale profile, derated; document the method).
2. Carry a per-ISO BTM PV + BTM storage capacity trajectory input
   (data/raw/caiso-btm/ from upload U7; EIA-861/CEC cited), and
   re-net demand at simulation time so forecast BTM growth deepens the
   duck curve instead of being frozen into the historical net shape.
3. Represent BTM storage / VPP programs as a load-modifying profile or a
   small price-responsive demand block, NOT as market generators, until
   an ISO meters them; make participation share a scenario knob.
4. Toggleable, default off; backcasts and ERCOT/PJM outputs unchanged.

Acceptance: a CAISO forecast scenario with 2x BTM PV shows a visibly
deeper midday net-load trough and later evening peak; all regression
tests pass.
```

### P14 — Documentation sign-off (last)

```
CAISO Stage H. Run the sync-docs flow: reconcile docs (00 status table,
01 manifest staleness, 05/06, data dictionary, offer-curve doc if CAISO
introduced variants) with the as-built code; append parameter citations;
write docs/multi-iso/caiso-backcast-<year>.md in the style of
docs/sessions/multi-iso/pjm-backcast-2023.md (archived; results tables, gaps, hypotheses); CHANGELOG entry.
```

---

## 6. ERCOT & PJM parity backlog (2026-06 audit)

Items found while auditing both ISOs against the v2 bar. Each is
prompt-sized; E* and J* can run as independent sessions. None block the
CAISO waves, but **J1 shares design with P9** — run P9 first and
generalize.

### E1 — ERCOT: measured monthly gas (backport) + 2024 coal retune

ERCOT still prices gas off annual Henry Hub + shape while PJM uses
measured per-plant EIA-923 monthly (`gas_monthly_actuals`). Backport to
ERCOT; then revisit the known 2024 coal −12% (cheap-gas year prices PRB
out at `coal_prb_passthrough=0.83`) — measured monthly gas may resolve
part of it without touching the passthrough. Also fix the stale
`test_coal_supply_pricing_uses_year_trajectory` on main.

### E2 — ERCOT: storage realism + nuclear refuel overlay — **DONE (2026-06-11)**

Model BESS discharge ran +48% over the EIA-930 measured 2025 window
(8.1 vs 5.4 TWh; the audit's "PS 9–10 TWh" figure was the same
over-cycling read in an earlier environment) and coal/CT tuning
compensated. Fixed by `ScenarioConfig.battery_dispatch_adder` (the
battery analogue of the PJM pumped-storage adder; CAISO P5 reuses the
same knob via `load_eia860_storage`), calibrated against the new
EIA-930 BAT/UES bundle benchmark (`storage.parquet` + report §3d).
Nuclear: the per-year EIA-923 monthly-CF overlay
(`NUCLEAR_MONTHLY_CF_BY_YEAR`) had already landed (PR #252) and holds
all three years at −0.7%; `scripts/derive_nuclear_monthly_cf.py` now
derives/validates the table (`--check`) as the backcast analogue of
`forecast_nuclear_refuel.py`. See docs/calibration-log.md (E2 entry)
for the keeper run and the residual coal/CT items handed to E1.
Oil ~0 vs 0.6–0.9 TWh actual still ties to winter gas pricing (E1).

### E3 — ERCOT: HSL coverage + curtailment metric

`ercot-hsl/` holds 2023 only; 2024–2025 backcasts re-use stale potential
shapes. Extend `build_ercot_hsl.py` through 2025 (needs NP6 HSL upload
for those years) and add modeled-vs-reported curtailment as a headline
ERCOT metric (CAISO P6 pattern) — ERCOT West curtailment is large enough
to matter.

*Status 2026-06: code landed.* `build_ercot_hsl.py` builds any year —
2024/2025 ingest ERCOT MIS wind/solar production reports (system-wide
GEN + actual HSL) from `data/raw/ercot-hsl/np6/` once uploaded;
the HSL profile path in `renewables.py` is per-year; and both
calibration reports print the modeled-vs-reported curtailment headline
(annual TWh/% + monthly shape). **Open: the NP6 report uploads for
2024–2025.** First 2023 reading: model curtails wind 2.0% vs 4.7%
reported, solar 0.4% vs 6.3% — under-curtailment to chase.

### J1 — PJM: import/export node (the +40 TWh structural gap) — DONE 2026-06-11

Note: the structural gap itself was already closed by M4 (2026-06-05,
measured tie-line schedule in `load_demand`) — the pjm-6 baseline served
823 TWh (783 internal + 40 export) and gas dispatch had already risen.
This pack delivered the remaining piece: the **generalized priced node**
(P9's design, built here first since P9 hasn't run). `PJM_external` zone +
import tranches + export sinks in `IMPORT_TRANCHES` / `EXPORT_TRANCHES`,
fitted to the measured 2023 net-interchange duration curve by
`scripts/derive_import_tranches.py` (2023: 100% of actual, duration RMSE
~570 MW; 2024 drifts +37% — re-fit per vintage). Forward PJM scenarios
(previously **zero** interchange) now carry price-responsive interchange;
backcasts keep the measured schedule. Validation runs:
`results/calibration/pjm_j1_baseline` (measured; pjm-6 regression) and
`pjm_j1_priced` (`--priced-interchange`).

### J2 — PJM: winter fidelity (CT runtime, ST_GAS, oil, dual-fuel)

Open items from the pjm-7 loop: CT −16/−21% concentrated in
winter/shoulder commitment behavior; ST_GAS 2024 winter −15%; oil 0 vs
0.9 TWh. These are one cluster: winter gas economics + dual-fuel
switching (doc 03 Packs F/G). Start with a dual-fuel flag from EIA-860
multiple-energy-source fields and an oil price series; gate on PJM.

### J3 — PJM: benchmark + coverage upgrades

(a) **Done 2026-06-11** — the `lmp-data/` PJM exports were already hourly
(12 hubs; the `_monthly_` filename is a misnomer). `derive_actual_lmp.py`
now emits `actual_lmp_hourly_PJM.parquet` + duration-curve percentiles in
`actual_lmp.json`, and `analyze_lmp_residual.py` localizes the residual:
Jul/Aug −4.9 (2023) / −6.4 (2024), concentrated in the 11:00–18:00 ramp
and the actual ≥$75 regime (92% of the 2024 $·h gap), p50 matches —
see `docs/sessions/multi-iso/pjm-lmp-residual.md` (archived) before any reserve/ORDC work.
(b) CAMPD unit-level gaps: MD/DE/NC/TN (and MI 2023/2025) still on
statistical availability — upload + regenerate `campd-unit-outages-PJM.csv`
(TN is now in `campd.ISO_STATES["PJM"]`, so the derivation widens
automatically once extracts land).
(c) Nuclear refuel overlay (shared with E2).

### Cross-cutting (build once, all ISOs benefit)

- Import/export node generalization — built in J1 (constants-driven
  `build_import_generators` / `build_export_sinks` /
  `extend_with_import_node` + `derive_import_tranches.py`); P9 now only
  needs to *calibrate* CAISO's entries; NYISO/NEISO only need constants.
- Storage cycling/throughput cost (P5 → E2).
- Curtailment as headline metric (P6 → E3 → SPP/MISO later).
- Reserve co-optimization (doc 03 Pack I) stays LAST, after the summer
  scarcity residual is quantified against hourly LMPs (J3a) — don't
  reach for the deepest LP change while cheaper structural fixes remain.
