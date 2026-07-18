# New-ISO Addition Protocol & Checklist

> **Update 2026-06-12:** the *process* description below predates the PJM
> backcast and is superseded by `05-backcast-playbook.md` (v2 process:
> per-plant CAMPD tranches, unit-level outage overlays, CHP
> steam-following, measured monthly gas, hydro/PS wiring, dashboard
> registration). The Stage A–H checklist in §1–2 remains current. Status
> corrections to §0: **PJM is now an 8-zone topology with a 2023–2024
> backcast under active calibration** (see `docs/calibration-log.md`,
> runs pjm 1–8); EIA-930 hourly parquets now exist for **all seven ISOs**;
> CAISO has CAMPD unit-level CA 2024–2025 + a derived outage CSV. CAISO
> execution plan: `06-caiso-prompt-pack.md`. **NEISO has a signed-off
> 2023–2025 backcast** (Stage H complete, 2026-06-12): 4 load zones
> (North/Central/Boston/Connecticut) + HQ_import node, measured AGT
> winter basis, RGGI in MC, dual-fuel switching, measured interchange
> schedule. See `docs/sessions/multi-iso/neiso-backcast-2024.md` (archived).

Status: **topology landed; calibration pending.** All seven ISOs are now
registered in `config/iso_configs.py` with real (cited, Tier-3) zone load
shares and inter-zone TTCs, and each has a plant-to-zone splitter in
`data/zone_assignment.py` (Stages A–B done for every ISO). What remains per
non-ERCOT ISO is the *data and calibration* spine — Stages C–H: EIA-930 demand,
renewable CF profiles, calibration references, market-design module wiring, and
a validated backcast. ERCOT stays the reference for **CAISO, PJM, ISO-NE
(NEISO), MISO, SPP, and NYISO**.

Companion documents in this directory:

- `01-data-needs-and-upload-manifest.md` — every data file each ISO needs,
  its source, and exactly what must be uploaded to the repo.
- `02-market-design-modules.md` — catalogue of market-design features that
  must become on/off modules (capacity/RA, reserves, scarcity/VOLL, hydro,
  state RPS, imports) and a modularity assessment of the dispatch LP.
- `03-prompt-pack-plan.md` — sequenced, self-contained build prompts for the
  modules, new fuel types (oil, biomass), and new fuel classes.
- `04-transmission-zones-and-congestion.md` — per-ISO zone topology,
  congestion corridors, TTC sourcing, and renewable HSL sourcing.

---

## 0. Where we are today (baseline)

| ISO   | Config in `iso_configs.py`               | BA map | Zone assign         | Calib. ref | EIA-930 hourly | Backcast |
|-------|------------------------------------------|--------|---------------------|------------|----------------|----------|
| ERCOT | Full: 7 zones (6 carry load), cited TTCs, real CF/HSL | ERCO   | lat/lon+FIPS        | 2021–2025  | `ERCO hourly`  | **Yes**  |
| CAISO | 3 zones (NP15/ZP26/SP15) + WECC import    | CISO   | Path 15/26 + FIPS   | none       | none           | No       |
| PJM   | 8 zones (ComEd…SWMAAC), cited zonal-peak shares + TTCs | PJM    | FIPS state→zone     | none       | none           | No       |
| MISO  | 3 zones (N/C/S) + South contract path      | MISO   | FIPS state→zone     | none       | none           | No       |
| SPP   | 2 zones (N/S)                              | SWPP   | FIPS state→zone     | none       | none           | No       |
| NYISO | 5 zones (A–K agg), cited TTCs, 154-plant hydro budget | NYIS | FIPS/largest (Tier-3 Gold-Book shares) | 2023, 2025 (2024 blocked) | `NYIS hourly` (2023–2025) | **2023 + 2025** (price-scored 2026-06-12; 2024 data-blocked) |
| NEISO | 4 load zones (North/Central/Boston/CT) + HQ_import node | ISNE | FIPS state→zone map (_NEISO_STATE_ZONES); Central fallback | 2023–2025 | `ISNE hourly` | **Yes (P12, 2023–2025; P14 signed off 2026-06-12; price scored 2026-06-12)** |

All ISOs are registered in `_ISO_BUILDERS` and `_ISO_TO_BA_CODE`. The remaining
gaps are **data + market-design fidelity** (Stages C–H), not topology.

> **NEISO price row — now scored (2026-06-12, P10/U2 landed).** The NEISO P12
> sign-off was price-*level-only*; with the `actual_lmp.json` NEISO block now
> present, the three keepers are **scored** on level + duration + zonal spread
> (see `calibration-log.md` §NEISO price re-score). Outcome: the price does not
> yet meet the duration/level tolerance — modeled hub +50% / +41% / −19% vs
> actual RT (2023/24/25) — but the miss is **filed, not tuned**: the
> **winter Jan/Feb/Dec tail** is the monthly-vs-daily AGT-basis gap (upload
> **U4**, the make-or-break NEISO item) — the modeled winter is a flat monthly
> plateau that never reaches the daily cold-snap spikes; the **CT cheap-side
> zonal tail** is U6 (interface limits); the mid-curve level is the
> served-interchange convention (P9 priced node). No offer band was moved; the
> green fuel-mix / CO₂ / interchange rows are untouched.

**The dispatch LP itself is ISO-agnostic and well-parameterized** on
`n_zones`, `n_storage`, `n_links`, the node-link `incidence` matrix, and per-
link `ttc`. Topology scaling needs no LP changes. The gaps are (a) per-ISO
*data and topology*, and (b) *market-design fidelity* (energy-only LP today;
see doc 02).

The reference implementation to mirror is ERCOT. Every step below has a known
ERCOT analogue — cite it in the per-ISO work so we stay faithful to the
existing, calibrated pattern.

---

## 1. The eight-stage addition protocol

Each ISO moves through these stages in order. A stage is "done" only when its
checklist (Section 2) is green and the regression tests still pass.

### Stage A — Topology definition
Define zones, load shares, transfer links, and TTCs in
`src/market_sim/config/iso_configs.py` (`_<iso>_config()` builder + entry in
`_ISO_BUILDERS`). For single-zone ISOs (start here) this is trivial; for
zonal ISOs (PJM, MISO, SPP) this is the largest topology task — see doc 04.
- ERCOT analogue: `_ercot_config()` with WESTEX/PNHNDL-derived TTCs.
- Validation: `ISOConfig.validate_topology()` (load shares sum to 1.0; links
  reference real zones). Add a case to `tests/test_iso_config.py`.

### Stage B — Plant-to-zone assignment
Map every generator's ORIS plant code to a model zone in
`src/market_sim/data/zone_assignment.py`:
- Add the ISO to `_ISO_TO_BA_CODE` (MISO→`MISO`, SPP→`SWPP`).
- Single-zone ISOs: add to `_SINGLE_ZONE`.
- Multi-zone ISOs: add a geographic splitter (lat/lon + FIPS → zone) and a
  `_LARGEST_ZONE` fallback. ERCOT's Houston-county FIPS logic is the template.
- Validation: extend `tests/test_zone_assignment.py`; every plant in the BA
  must resolve to a real zone, none silently dropped.

### Stage C — Fleet ingestion
Confirm the fleet loader (`data/fleet.py`, `data/eia923.py`, `data/campd.py`,
`data/eia_loader.py`) picks up the ISO's plants. Most of this is automatic
once the BA filter and zone map exist, **but** new fuel types in the fleet
(oil, biomass, MSW, pumped storage) must be added to `FUEL_TYPE_MAP` and given
heat-rate/VOM/emission parameters — see doc 03, Pack F.

### Stage D — Demand & renewable profiles
Per backcast year, build the EIA-930 demand series and the wind/solar CF
profiles (`data/renewables.py`). Multi-zone ISOs need demand disaggregated to
zones via load shares; renewable CF needs zone-level shaping. Best case is an
HSL-style uncurtailed profile (ERCOT 2023 pattern); fallback is the EIA-930
delivered-generation distribution. See doc 01 §3 and doc 04 §4.

### Stage E — Calibration reference
Extend `scripts/data/build_calibration_reference.py` to emit, per ISO-year:
EIA-860 renewable capacity (year-end totals, zone shares, monthly ramp),
measured Henry Hub (or basis-adjusted regional gas) price, EIA-930 demand
totals, and an eGRID generation/emissions benchmark. Output lands in
`data/raw/_validation-source/{ISO}_{year}_renewable_capacity.csv` and
`calibration_reference.json`.

### Stage F — Market-design module wiring
Turn on the modules this ISO needs (capacity/RA accounting, reserves, hydro
energy budgets, state RPS, import/export nodes, scarcity/ORDC). Each is an
on/off feature controlled by `ScenarioConfig` + `ISOConfig`; see doc 02 for
the catalogue and doc 03 for the build prompts. **Faithfulness rule:** an ISO
runs with exactly the mechanisms that ISO actually has — no more, no less.

### Stage G — Backcast run & calibration
Run `scripts/run_calibration_full.py` (the ERCOT harness) for the ISO across
2021–2025. Compare modeled vs EIA actuals on: zonal/system price duration,
fuel-mix generation shares, emissions, curtailment, and net interchange.
Tune within the documented parameter system (no magic numbers).

### Stage H — Documentation & sign-off
Record per-ISO calibration results, parameter citations (append to
`docs/parameter-citations.md`), and any market-design caveats. Update this
directory's per-ISO status table.

---

## 2. Per-ISO checklist (copy one block per ISO)

```
ISO: __________   Owner: __________   Target backcast years: __________

STAGE A — Topology
[ ] Zones enumerated with load shares (sum = 1.0)            src ref: ______
[ ] Transfer links + TTC values with citations
[ ] _<iso>_config() added to _ISO_BUILDERS
[ ] validate_topology() passes; test added

STAGE B — Zone assignment
[ ] ISO added to _ISO_TO_BA_CODE (BA code: ______)
[ ] Single-zone: in _SINGLE_ZONE  /  Multi-zone: geo splitter + fallback
[ ] All BA plants resolve to a zone (no silent drops); test added

STAGE C — Fleet ingestion
[ ] Fleet loads from EIA-860/923 + CAMPD for this BA
[ ] New fuel types registered in FUEL_TYPE_MAP with params
[ ] Plant count & capacity sanity-checked vs ISO published totals

STAGE D — Demand & renewables
[ ] EIA-930 hourly demand uploaded & loads per backcast year
[ ] Demand disaggregated to zones (multi-zone)
[ ] Wind/solar CF profiles built (HSL if available, else EIA-930 dist.)
[ ] Hydro profile / energy budget sourced (if material)

STAGE E — Calibration reference
[ ] build_calibration_reference.py extended for ISO
[ ] {ISO}_{year}_renewable_capacity.csv emitted
[ ] Regional gas price / basis sourced
[ ] eGRID emissions benchmark extracted

STAGE F — Market-design modules
[ ] Capacity/RA mechanism decision (model? exogenous? off?)
[ ] Reserves/ancillary decision
[ ] Hydro energy-budget module (if material)
[ ] State/zonal RPS or CES configured
[ ] Import/export nodes + interchange handling
[ ] VOLL / scarcity mechanism set with citation

STAGE G — Backcast & calibration
[ ] run_calibration_full.py runs clean for all years
[ ] Price duration curve within tolerance vs actuals
[ ] Fuel-mix shares within tolerance
[ ] Emissions within tolerance
[ ] Net interchange sign/magnitude sane

STAGE H — Docs
[ ] Parameter citations appended
[ ] Calibration results logged
[ ] Market-design caveats documented
[ ] Status table updated
```

---

## 3. Suggested sequencing across ISOs

> **Status (now executed):** this section is the *original* build order and
> describes each ISO's pre-build starting state. All seven are now registered
> **multi-zone** in `config/iso_configs.py` — CAISO 3+import, NYISO 5, NEISO
> 4+import, PJM 8, MISO 3, SPP 2 — so phrases like "single zone today" and
> "4-zone stub" below are the historical starting point, not current state.

Order by *incremental difficulty* so each ISO reuses the last one's new
machinery:

1. **CAISO** — already a stub; single main zone + WECC import node already
   exists. Exercises the import-node and hydro/RA modules first. Highest data
   availability (OASIS, CAISO renewables).
2. **NYISO** — single zone today, but real NYISO is 11 zones with major hydro
   (Niagara/St. Lawrence) and heavy oil/dual-fuel. Good second case for hydro
   energy budgets + the oil fuel type, before tackling many-zone ISOs.
3. **ISO-NE (NEISO)** — single zone today; real ISO-NE is load-zone based with
   large oil/dual-fuel peakers, FCM capacity market, and HQ/NYISO imports.
4. **PJM** — 4-zone stub with placeholder TTC/shares; the first *large* zonal
   build (real PJM is 20+ transmission zones; we aggregate). RPM capacity,
   13-state RPS patchwork.
5. **MISO** — built from scratch; very large, seasonal capacity construct
   (PRA), north/central/south sub-regions + the MISO-South contract-path
   constraint, big wind + coal fleet.
6. **SPP** — built from scratch; wind-dominated, large geography, RA construct
   (no centralized capacity market), strong interchange with MISO/ERCOT.

Single-zone first proves the data/calibration pipeline per ISO; multi-zone
later proves topology + congestion. Capacity/hydro/oil modules are introduced
exactly when the first ISO that needs them arrives, then reused.

---

## 4. Non-negotiables carried over from `claude.md`

These constrain every ISO addition; do not regress them:

- No Python loops over hours in LP construction — vectorize with
  `kron`/`tile`/`repeat`/`block_diag`.
- Renewables stay decision variables on the LHS of energy balance (MC=0,
  UB = CF×capacity), never netted from demand.
- Prices remain LP duals on energy-balance rows. No separate pricing model.
- No magic numbers — every per-ISO parameter cites a source (append to
  `docs/parameter-citations.md`) and lives in `ScenarioConfig`/`ISOConfig`/
  `constants.py`.
- Struct-of-arrays before LP construction; full 8760 hours always.
- Raw data in `data/` is never modified in place.
- New market-design modules must be **toggleable** and **default to off** so
  ERCOT's calibrated behaviour is unchanged when its modules aren't selected.
