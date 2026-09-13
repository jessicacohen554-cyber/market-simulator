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

Status: **topology landed for all SEVEN registered ISOs; calibration pending.**
**SPP IS registered** since 2026-09-06 (lane SPP-20,
`docs/handoffs/FINDING-spp-20-2026-09-06.md`) — this doc's earlier "SPP is not
registered" correction is now itself stale and is repaired here. The **seven**
ISOs in `config/iso_configs._ISO_BUILDERS` (ERCOT, CAISO, PJM, MISO, NYISO,
NEISO, SPP) each
have real (cited, Tier-3) zone load shares and inter-zone TTCs and a
plant-to-zone splitter in `data/zone_assignment.py` (Stages A–B done for each of
those seven — with the one disclosure that SPP's single N↔S TTC is a **Tier-3
placeholder that cannot bind**, not a rated interface; see the §0 row). What
remains per non-ERCOT registered ISO is the *data and
calibration* spine — Stages C–H: EIA-930 demand,
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
| SPP   | **REGISTERED 2026-09-06** (lane SPP-20): 2 zones (SPP-North/SPP-South), measured sub-BA load shares 0.5125/0.4875, VOLL $2,000. Its ONE N↔S link's 48,700 MW TTC is a **Tier-3 placeholder that cannot bind** — no public document states an SPP North↔South capability (FINDING-spp-13 §0) — so seam TTC is **pending lever SPP-53**; see `spp-addition-plan-2026-09.md` | SWPP | FIPS state→zone (`_SPP_STATE_ZONES`) | none yet (SPP-31) | `SWPP hourly` **present** | No — first solve is lane SPP-40 |
| NYISO | 5 zones (A–K agg), cited TTCs, 154-plant hydro budget | NYIS | FIPS/largest (Tier-3 Gold-Book shares) | 2023, 2025 (2024 blocked) | `NYIS hourly` (2023–2025) | **2023 + 2025** (price-scored 2026-06-12; 2024 data-blocked) |
| NEISO | 4 load zones (North/Central/Boston/CT) + HQ_import node | ISNE | FIPS state→zone map (_NEISO_STATE_ZONES); Central fallback | 2023–2025 | `ISNE hourly` | **Yes (P12, 2023–2025; P14 signed off 2026-06-12; price scored 2026-06-12)** |
| SOCO | **NOT REGISTERED** — chartered 2026-09-12, see `soco-addition-plan-2026-09.md`. A *balancing authority*, not an ISO: Southern Company Services, vertically integrated, no day-ahead market, no LMP, no capacity market. Topology (1 zone vs 3) is owner card **S3**, served from `soco-data-audit.md` §6 | SOCO (BA code, not yet in `_ISO_TO_BA_CODE`) | none yet — `_SOCO_STATE_ZONES` candidate in `soco-data-audit.md` §6.4 | none | `SOCO hourly` **present** (26,304 h, 2023–2025, `America/Chicago`) | No — and **there is no price benchmark to score one against** (plan §2.6, card S2) |
| NWPP | **NOT REGISTERED** — chartered 2026-09-13, see `nwpp-addition-plan-2026-09.md`. A **POOL of 17 balancing authorities**, not a BA and not an ISO — the first such region here. Vertically integrated, no pool-wide day-ahead market, no LMP, no capacity market. Topology (5 whole-BA zones vs 3 vs 1) is owner card **N5**, served from `nwpp-data-audit.md` §9; the price benchmark is card **N2** | 17 BA codes (BPAT PACE PACW PGE PSEI AVA IPCO NWMT CHPD DOPD GCPD SCL TPWR AVRN GRID WAUW NEVP) — a **17→1** map, not 1→1, and the first such entry | none yet — a **`Balancing Authority Code`**-keyed splitter, never state (a state holds several BAs and a BA holds several states); candidate in `nwpp-data-audit.md` §9.2 | none | **not as per-BA files** — but all 17 BAs are already committed in `eia-930/EIA930_BALANCE_*.parquet` (447,168 rows / 26,304 UTC h per BA for 2023–2025, zero gaps), so the load spine is a **derive, not a fetch** | No — first solve is lane NWPP-40, and **NWPP publishes no LMP** (plan §2.6, card N2) |

**Seven** ISOs are registered in `_ISO_BUILDERS` and `_ISO_TO_BA_CODE` — ERCOT,
CAISO, PJM, MISO, NYISO, NEISO and, since 2026-09-06, **SPP** (`_spp_config()`,
`_ISO_TO_BA_CODE["SPP"] = "SWPP"`, `zone_assignment._SPP_STATE_ZONES`; wave W2 of
`docs/multi-iso/spp-addition-plan-2026-09.md`, lane SPP-20). For all seven the
remaining gaps are **data + market-design fidelity** (Stages C–H), not topology.
SPP carries one topology item still open: the **N↔S seam TTC**, a Tier-3
placeholder pending lever **SPP-53** (owner ruling P13). SPP's Phase-0 data
census is `docs/multi-iso/spp-data-audit.md`; its first solve and first keeper
are lane SPP-40.

**TWO further regions are chartered but NOT registered — `SOCO` and `NWPP`.** Both are
absent from `_ISO_BUILDERS`, `_ISO_TO_BA_CODE`, `SURFACE_ISOS` and every other ISO-keyed
registry, so **the registered count is still SEVEN** (re-measured at `_ISO_BUILDERS`
2026-09-13, lane NWPP-10); "eighth" and "ninth" below are claims about *charter order*,
not about the tree.

- **`SOCO`** (Southern Company Services), chartered **2026-09-12** by
  `docs/multi-iso/soco-addition-plan-2026-09.md`; the pin flip is that plan's wave W2
  (lane SOCO-20). SOCO is a **balancing authority, not an ISO** — no day-ahead market,
  no LMP, no capacity market — so three of the rubric's four load-bearing price criteria
  have no benchmark to score against; that is owner card **S2** and it is unresolved. Its
  Phase-0 data census is `docs/multi-iso/soco-data-audit.md` (lane SOCO-10, 2026-09-13).
- **`NWPP`** (the Northwest Power Pool / Western Power Pool footprint), chartered
  **2026-09-13** by `docs/multi-iso/nwpp-addition-plan-2026-09.md`; the pin flip is that
  plan's wave W2 (lane NWPP-20). NWPP is **neither a balancing authority nor an ISO — it
  is a POOL of 17 balancing authorities**, the first such region here, which is why its
  `BA_CODE_TO_ISO` entry is a **17→1** mapping and its plant-to-zone splitter must key on
  `Balancing Authority Code` rather than state. It publishes no LMP (owner card **N2**),
  has no capacity market, and is **36 % conventional hydro** whose eight largest plants sit
  on one hydraulic chain (owner card **N3**). Its Phase-0 data census is
  `docs/multi-iso/nwpp-data-audit.md` (lane NWPP-10, 2026-09-13) — which confirms the
  fleet at 940 plants / 1,932 generators / 98,738.1 MW, rejects one 500 MW ERCOT-side row
  as a BA-code source defect, and establishes `Demand (MW) (Adjusted)` and UTC as the
  footprint's demand and time conventions.

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

> **Status (partly executed):** this section is the *original* build order and
> describes each ISO's pre-build starting state, so phrases like "single zone
> today" and "4-zone stub" below are the historical starting point, not current
> state. **Seven** ISOs are now registered **multi-zone** in
> `config/iso_configs.py` — CAISO 3+import, NYISO 5, NEISO 4+import, PJM 8,
> MISO (six zones since the zonal refinement; this note's older "3" is stale —
> not this lane's to restate, see `docs/multi-iso/miso-zonal-refinement-scope.md`),
> SPP 2. **Seven is still the registered count**, re-measured at `_ISO_BUILDERS`
> on 2026-09-13 (lane NWPP-10) — **two** further regions are chartered and NOT
> registered, both absent from `_ISO_BUILDERS` and every other ISO-keyed
> registry: **`SOCO`** (Southern Company Services — a *balancing authority*, not
> an ISO), chartered 2026-09-12, topology owner card **S3**, still open; and
> **`NWPP`** (the Northwest Power Pool footprint — a **pool of 17 balancing
> authorities**, neither a BA nor an ISO), chartered 2026-09-13, topology owner
> card **N5**, still open. "Eighth" and "ninth" are charter order, not the tree.
> See `docs/multi-iso/soco-addition-plan-2026-09.md` +
> `docs/multi-iso/soco-data-audit.md`, and
> `docs/multi-iso/nwpp-addition-plan-2026-09.md` +
> `docs/multi-iso/nwpp-data-audit.md`.
> **Item 6, SPP, IS built and registered** as of 2026-09-06 (lane SPP-20,
> `docs/handoffs/FINDING-spp-20-2026-09-06.md`): `_spp_config()`, the
> `_ISO_BUILDERS` and `_ISO_TO_BA_CODE` entries and the
> `_SPP_STATE_ZONES` splitter all exist. *(This paragraph previously said the
> opposite — that correction was written by lane SPP-10 before the registration
> landed and is repaired here by SPP-34, routed item R-5 of FINDING-spp-20 §5.)*
> One Stage-A item stays open: the N↔S seam TTC is a **Tier-3 placeholder that
> cannot bind**, pending lever **SPP-53** (owner ruling P13). The rest of the
> addition is chartered end-to-end by
> `docs/multi-iso/spp-addition-plan-2026-09.md`; the Phase-0 data census that
> preceded registration is `docs/multi-iso/spp-data-audit.md`, and the first
> solve / first keeper is lane SPP-40.

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
6. **SPP** — **registered 2026-09-06** (see the status note above); built from
   scratch; wind-dominated, large geography, RA construct (no centralized
   capacity market — SPP is deliberately absent from
   `capacity_market.MARKET_DESIGN`), strong interchange with MISO/ERCOT served as
   the measured EIA-930 `Total interchange` schedule. Measured at Phase 0
   (`spp-data-audit.md`): 103,330.8 MW nameplate over 715 plants in 14 states,
   36.6 % of 2025 net generation from wind, and 11–13 % of real-time hours at a
   negative hub price.

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
