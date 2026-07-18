# ISO Backcast Playbook — v2 (2026-06)

Status: **canonical process reference.** This document captures the
end-to-end process for standing up a new-ISO backcast at the fidelity ERCOT
and PJM actually reached — including the machinery built *after* docs 00–04
were written (per-plant CAMPD tranches, unit-level outage windows, CHP
steam-following, measured monthly gas, hydro/pumped-storage LP wiring,
hourly LMP benchmarks, dashboard registration). When this doc and docs 00–04
disagree on *process*, this doc wins; docs 00 (stage checklist), 02 (module
catalogue), and 04 (topology/TTC sourcing per ISO) remain the references for
their specific content.

Use this playbook for **CAISO (doc 06 is its instantiation), NYISO, MISO,
NEISO, and SPP** without further direction. The recipe per new ISO is:
read this doc → copy doc 06's prompt-pack structure → fill in the ISO's
specifics from §8 and doc 04 → run the waves.

---

## 0. What "ERCOT/PJM parity" means today

The bar a new ISO must clear is no longer the 2025-era stub pipeline. As of
2026-06 the calibrated pattern is:

1. **Per-plant fleet** from EIA-860 (one EIA plant = one LP generator;
   mixed facilities split per `Plant_Group`), zone-assigned by lat/lon+FIPS.
2. **Offer curves grounded in the plant's own CAMPD history** — committed %
   (`scripts/data/derive_cc_committed_pct.py`), coal must-run % and peaking
   ranges (`scripts/data/derive_thermal_tranches.py`), n=6 smooth econ ramp
   (`docs/offer-curve-methodology.md`).
3. **CHP behind-the-meter steam obligations** identified from EIA-860 cogen
   flags + EIA-923 fuel/steam data, removed from LP capacity, steam-following
   floors solved by the 3-solve perturbation method (PJM 2026-06 pattern).
4. **Backcast availability from measured unit-level outages** — CAMPD CEMS
   unit extracts → `scripts/data/derive_campd_unit_outages.py` → per-ISO
   `campd-unit-outages-<ISO>.csv` → historic overlay in `data/outages.py`.
   Facility-level detection is the fallback, unit-level is the standard
   (it catches single-unit outages masked by peer units).
5. **Measured fuel prices**: per-plant EIA-923 monthly delivered gas/coal
   with nearby-plant fallback (`gas_monthly_actuals`), not a flat annual
   Henry-Hub-plus-scalar. The flat `GAS_BASIS_DIFFERENTIAL` scalar is a
   seed for forecasts only; backcasts use measured 923.
6. **Hydro + pumped storage in the LP** — monthly energy budgets from
   EIA-923, nameplate caps from EIA-860, PS fleet from prime-mover `PS`
   records with duration/RTE params, plus a dispatch adder / throughput
   cost where pure arbitrage over-cycles vs observed (PJM PS lesson).
7. **Measured renewable profiles** — uncurtailed potential (HSL analogue)
   where the ISO reports curtailment (uncurtailed = delivered + curtailed);
   EIA-930 delivered distribution as the documented fallback.
8. **Hourly system + zonal price benchmarks** — `actual_lmp.json` entries
   and, where uploaded, hourly hub LMP series for duration-curve overlays.
9. **Dashboard registration** of every run
   (`scripts/dashboard_add_run.py` / the calibration-report flow), and a
   per-pass entry in `docs/calibration-log.md`.

The **ERCOT regression guard** still applies to every change: all new
toggles default off; ERCOT (and now PJM) results byte-identical when their
modules aren't selected.

---

## 1. Phase 0 — Scope, benchmarks, and the data audit prompt

Before any build work, one session runs a **data audit** for the ISO:

- Confirm fleet assembly: `get_iso_config("<ISO>")` + BA filter → plant
  count and capacity vs the ISO's published fleet totals (±few %).
- Enumerate CEMS state coverage needed: assemble the fleet, list distinct
  plant states, diff against `data/raw/campd-unit-level/<ST>_<year>.parquet`
  present. Output the missing `<ST>_<year>` list.
- Verify the EIA-930 hourly parquet (`data/eia_hourly/<BA> hourly.parquet`)
  spans the target years with demand + per-fuel generation (+ interchange,
  + battery columns where the BA reports them).
- Check `data/raw/_validation-source/calibration_reference.json` and
  `actual_lmp.json` for the ISO; extend `build_calibration_reference.py`.
- Emit a written gap report → the upload manifest for the user.

**Benchmark set per ISO-year** (the definition of done for Stage G):

| Benchmark | Source | Tolerance (ERCOT/PJM precedent) |
|---|---|---|
| Fuel-mix TWh by class | EIA-923 (primary), EIA-930 (shape/secondary) | ±5% per major class |
| Monthly class shapes | EIA-923 monthly | Pearson r / NRMSE logged per class |
| Avg + duration LMP | ISO hub LMP (DA & RT), `actual_lmp.json` | avg within ~5–10%; duration shape eyeballed via dashboard |
| Zonal price spreads | ISO zonal/hub LMPs | spread duration curve sign+magnitude |
| CO2 | eGRID ISO total | ±5–10% |
| Net interchange | EIA-930 BA interchange | sign + magnitude |
| Curtailment | ISO curtailment report (where published) | sign + magnitude; first-class metric for high-VRE ISOs |
| Storage/PS throughput | EIA-923 / ISO battery reports | annual TWh within ~±30% (cycling realism) |

## 2. Phase 1 — Data acquisition

**Network reality:** the remote environment's allowlist blocks EIA and all
ISO hosts (see `data-acquisition-report.md`). Anything not already in the
repo and not on GitHub mirrors is a **manual upload by the user**. Every
prompt pack therefore starts with an explicit upload manifest, and sessions
never fabricate data values.

Data families (status 2026-06: families 1–5 are in-repo and national or
all-BA; the per-ISO burden is families 6–10):

| # | Family | Repo location | Per-ISO action |
|---|---|---|---|
| 1 | EIA-930 hourly (all BAs) | `data/eia_hourly/<BA> hourly.parquet` | present for all 7 ISOs + neighbors |
| 2 | EIA-860 (incl. storage, enviro, cogen tables) | `data/raw/eia-860/` | none (national) |
| 3 | EIA-923 monthly gen + fuel cost | `data/raw/f923_*.zip`, `data/raw/_processed-legacy/` | none (national) |
| 4 | eGRID 2023/2024 | `data/raw/egrid2024_data.xlsx` etc. | none (national) |
| 5 | Henry Hub daily/monthly | `data/raw/gas-prices/` | none |
| 6 | CAMPD CEMS unit-level | `data/raw/campd-unit-level/<ST>_<year>.parquet` | upload missing state-years from data audit |
| 7 | Hourly hub/zonal LMP | `data/raw/lmp-data/` | upload from ISO portal (DA + RT, all backcast years) |
| 8 | Zonal hourly load | `data/raw/zone-specific-demand/` | upload (multi-zone ISOs) |
| 9 | TTC / interface limits + flows | `data/raw/iso-specific-transmission/` | upload postings or binding-constraint archive |
| 10 | Curtailment / uncurtailed potential | per-ISO dir under `data/raw/` | upload where published (CAISO, SPP, MISO); else EIA-930 fallback |

Gas basis: prefer **measured EIA-923 per-plant monthly** (family 3, already
national) over hub-basis series. Only ISOs whose marginal winter pricing is
set by spot blowouts beyond plant-average 923 costs (NYISO, NEISO) need an
additional hub series (paywalled; see acquisition report §1c).

## 3. Phase 2 — Derivation pipeline (scripts, in dependency order)

```
process_eia860.py / process_f923_fuel_costs.py      # national refresh (rare)
derive_campd_unit_outages.py  --iso <ISO>           # unit outage windows CSV
derive_campd_outages.py       (fallback/cross-check)
derive_cc_committed_pct.py    --iso <ISO>           # per-plant committed %
derive_thermal_tranches.py    --iso <ISO>           # must-run / peaking ranges
tag_mixed_plants.py                                  # mixed-facility splits
build_offer_curve_overrides.py                       # bin assignment CSV
derive_load_shares.py         --iso <ISO>           # zonal shares from metered load
derive_ttc_limits.py          (where binding-constraint archive uploaded)
derive_actual_lmp.py          --iso <ISO>           # actual_lmp.json + hourly series
build_calibration_reference.py                       # per-ISO-year reference block
```

Each derived artifact gets committed with its source + method noted in the
file header or `docs/parameter-citations.md`.

## 4. Phase 3 — Offer-curve design per ISO

- Start from class defaults (`OFFER_CURVES_BY_FUEL` / ERCOT-calibrated
  bands); override per plant only where CAMPD evidence says so.
- Derive per-plant **committed %** (CC) and **must-run %** (coal) before
  any band tuning — the PJM loop showed tranche sizes dominate band
  multipliers.
- **CHP first**: identify steam hosts (EIA-860 cogen flag + 923), assign
  `CC_CHP`/`CT_CHP`, remove BTM steam capacity from the LP. Getting CHP
  wrong contaminates every gas-class benchmark.
- New fuel types (oil, biomass, dual-fuel) per doc 03 Packs F/G when the
  ISO's mix requires them (NYISO/NEISO especially).
- Fleet-specific must-run analogues: where an ISO has little coal, the
  "must-run" layer is whatever is contractually/physically inflexible
  there — CHP steam hosts, nuclear, RMR contracts, hydro min-flows.

## 5. Phase 4 — Market-design module selection (faithfulness rule)

Per doc 02: an ISO runs with exactly the mechanisms it actually has.
Decide and record, per ISO: capacity/RA revenue (M1), reserves (M2,
last), hydro budgets (M3), import/export nodes (M4), RPS/CES (M5),
carbon program (M6 — RGGI / CA cap-and-trade enter marginal cost and are
**price-critical**, not optional, for NYISO/NEISO/CAISO backcasts),
seasonal constructs (M8, MISO). All toggleable, default off.

## 6. Phase 5 — The calibration loop (discipline learned on ERCOT + PJM)

1. **Smoke year first**: one year, `run_calibration.py` (fast, fuel-mix
   only), fix structural absurdities before full bundles.
2. **Structural before knobs.** Tune in this order, never the reverse:
   (a) demand/net-load conventions; (b) interchange/imports; (c) hydro &
   storage fleets and their cycling costs; (d) fuel prices (measured 923);
   (e) outage overlay coverage; **then** (f) offer-curve bands. The PJM log
   shows band-tuning against a structurally wrong system bakes in
   compensating errors that must be unwound later (ERCOT coal/CT after
   hydro/PS landed).
3. Full runs: `run_calibration_full.py --iso <ISO> --year <Y...>
   --commitment`, distinct `--out-dir` per run, independent runs in
   parallel.
4. Register every meaningful pass on the dashboard
   (`dashboard_add_run.py`); keep top runs per ISO; log every pass in
   `docs/calibration-log.md` with config deltas and the keeper decision.
5. Stop when the Phase-0 benchmark table is green for all target years;
   record the keeper config in `docs/calibration-best-so-far.md` style.

## 7. Phase 6 — Sign-off

Per doc 00 Stage H: parameter citations appended, calibration results
logged, market-design caveats documented, status table updated, and
`sync-docs` run at session end.

---

## 8. Cross-cutting conventions (decided once, applied to every ISO)

### 8.1 Behind-the-meter solar, storage, and DER (the net-load convention)

**Backcast convention: demand is net load.** EIA-930 (and ISO) demand is
metered at the transmission level and is already net of behind-the-meter
PV/storage/DER. Therefore in backcasts:

- Model **only ISO-metered, front-of-meter resources** as supply. Never add
  a BTM solar profile on the supply side against net demand — that double
  counts.
- Benchmark utility-scale solar against **EIA-923** (EIA-930 solar columns
  can under-report; PJM 2023 precedent) and treat the EIA-930 series as
  shape + conservative bound.
- Document per ISO how big the hidden BTM wedge is (CAISO ≈ 15+ GW PV;
  material duck-curve shaping lives inside the demand series — that is
  fine and self-consistent for backcasts).

**Forecast convention: gross-up + explicit BTM module.** Forward scenarios
where BTM/VPP growth changes the net-load shape must (a) reconstruct gross
load = net + estimated BTM output for the base year, (b) carry a BTM
PV/storage capacity trajectory (EIA-861 small-scale PV, state agency data,
ISO BTM estimate feeds), and (c) re-net at simulation time. BTM storage /
VPP participation is represented as a load-modifying profile or a small
price-responsive demand block — not as market generators — until an ISO
actually meters them (then they enter the fleet like any resource).
This is a build-once module; CAISO forces it first (doc 06 P13).

### 8.2 Imports/exports

Every non-ERCOT ISO is interconnected and the interchange wedge is
first-order (PJM +40 TWh export; CAISO ~20–25% import share). The pattern
is the per-ISO priced node (`build_import_generators(iso)` /
`build_export_sinks(iso)` off `constants.IMPORT_TRANCHES` /
`EXPORT_TRANCHES`; `extend_with_import_node` appends the zone+links when
not baked into the topology): an import zone with `load_share=0`, links
with TTC, a 3–4 tranche priced supply curve plus priced export sinks.
Calibrate the tranche prices/quantities so the modeled **net-interchange
duration curve** tracks EIA-930 (`scripts/data/derive_import_tranches.py`; the
measured series is typically hourly price-orthogonal, so fit the duration
curve, not the hours). Where a neighbor's price sets the tranche (HQ,
Mid-C, Palo Verde), cite the proxy. Seasonal shaping (NW hydro year) where
the data demands it. For *backcast* years with a measured interchange
series, prefer serving the measured schedule (PJM precedent,
`load_demand(include_interchange=...)`); the priced node is the forward
mechanism and is validated with `--priced-interchange` runs. **Wired
default-on for PJM, NYISO and NEISO** (`_SCALAR_INTERCHANGE_ISOS`;
`{nyiso,neiso}_net_interchange` read the EIA-930 `Total interchange` column,
already export-positive so a net import is negative and lowers the residual
the internal fleet serves). ERCOT (islanded, DC ties in its own extract) and
CAISO (imports modeled by the `WECC_import` node, §8.1) stay out — netting
their interchange into demand would double count. P9b (2026-06) closed both
NYISO and NEISO smoke interchange rows this way: gas fell from +25.6% / +11.2%
over EIA-923 to −9.8% / −5.0%, the served schedule matching the measured to
duration RMSE 0 MW.

### 8.3 Curtailment as a first-class metric

For high-VRE ISOs (CAISO, SPP, MISO, ERCOT) the model must *re-curtail*:
feed uncurtailed potential (delivered + reported curtailment, the HSL
analogue) and compare modeled vs reported curtailment as a headline
calibration metric, not a residual.

### 8.4 Storage fleets

Grid batteries come from the EIA-860 energy-storage tables
(`data/raw/eia-860/eia860_energy_storage_operable.parquet`):
power, energy (duration), COD for mid-year capacity ramps, zone via plant
coords. Hybrid/co-located solar+storage stays two resources. Where the BA
reports battery charge/discharge in EIA-930, use it as the cycling
benchmark. Expect to need a cycling/throughput cost or availability derate
to stop the LP over-cycling vs observed (ERCOT PS and PJM PS precedent).

### 8.5 Session etiquette for prompt packs

- One pack = one fresh session = one branch (`claude/<iso>-<pack>-<slug>`),
  commit at the pack boundary, full test suite + regression guard.
- Waves: packs within a wave are independent (different files/data) and
  can run in parallel sessions; waves are sequential.
- Derived-data packs (pure `scripts/` + `data/` output) parallelize
  safely; config/LP packs that touch shared modules run sequentially.

---

## 9. Per-ISO deltas to remember (beyond doc 04 topology)

| ISO | The items that will dominate its calibration |
|---|---|
| **CAISO** | Imports (~20–25%), grid batteries (~10+ GW), solar curtailment (multi-TWh), seasonal hydro (wet 2023 vs dry years), CA cap-and-trade in MC, net-load/BTM wedge, Diablo Canyon refuel calendar, Kern/refinery CHP. See doc 06. |
| **NYISO** | Downstate import constraints, Niagara/St-Lawrence hydro budgets, oil/dual-fuel winter switching, HQ/PJM/NE/IESO import nodes, RGGI carbon, ICAP revenue. |
| **NEISO** | Algonquin winter gas basis (beyond 923 averages), oil/dual-fuel, HQ Phase II imports, FCM revenue, Northfield PS, RGGI. |
| **MISO** | North–South RDT contract path, seasonal PRA (M8), big wind curtailment north, coal must-run culture, MISO↔PJM/SPP seams. |
| **SPP** | Wind dominance + curtailment, no capacity market (RA obligation), MISO/ERCOT seams, closest to ERCOT in design — cheapest add after CAISO. |
