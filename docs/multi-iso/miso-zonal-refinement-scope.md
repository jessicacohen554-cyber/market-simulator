# MISO Zonal Refinement — Scoping Plan (structure-first, no implementation)

Status: **PHASE 2 IMPLEMENTED 2026-07-02** (branch
`claude/miso-zonal-coopt-phase2-6bj3it`; keeper
`2026-07-02-miso-38-zonal-reserves`): reserve co-opt re-enabled per §6 and
gate 4 (§7) evaluated. Wiring discovery: `--energy-reserve-coopt` had been
**silently inert for MISO on the backcast path** (the `run_year` co-opt
chain ended at NEISO; `_miso_design` was reachable only from the forecast
runner) — every prior MISO "co-opt" dashboard run, incl. probe miso-34,
solved an energy-only LP. Fixed with a `run_year` MISO branch routing to
the UNCHANGED `_miso_design`. Results: market-wide RBDC in-LP is
structurally inert at 6 zones (reserve dual $0 all 26,280 h — probe
miso-37), so phase-2b locational families were added per §6
(`--miso-zonal-reserves`, gated default off): MISO-South family,
requirement = within-zone MSSC 3,953 MW (BPM-002 §3.3.2 largest-zonal-event
basis), priced at the published Zonal ORDC (BPM-002 §5.2.1.2 / Schedule
28-A: $200/$1,100/$3,300 steps). **Gate 4 PARTIAL:** the zonal family
fires (dual nonzero 266/287/875 h, 2025-concentrated) but at re-dispatch
opportunity cost ($8–21/MWh max) — the >$200 tail stays 0 h vs actual
30/37/88 and CT_PEAKER/coal are unchanged; the residual root cause is not
missing reserve structure (perfect-foresight headroom; next levers:
per-gen ramp sub-shortage band — memory-infeasible at plant scale — or D6
per-hub LMP scoring). Gates 1–3 still pass. See
`docs/multi-iso/miso-reserve-coopt.md`.

Phase-1 status (2026-07-02, branch `claude/miso-zonal-impl-y7luam`):
6-zone topology + seasonal CIL/CEL interface caps + full touchpoint remap +
data rebuilds landed per §5/§10; backcast gates per §7 reported in the run
report of the `miso-35-zonal-refinement` dashboard bundle. Implementation
notes: the one-way link floor (`link_bidirectional`) was found unwired in
both runners and connected (the RDT pair had been silently symmetric);
bundles now persist `flows.parquet` for interface-binding diagnostics
(`scripts/report_miso_zonal_gates.py`). Jan–May 2023 caps read the measured
PY2022-23 LOLE values (D5 landed 2026-07-02: annual pre-seasonal CIL/CEL set,
season "annual" in the CSV; the PY2023-24 same-season backfill now applies
only to backcasts reaching before the extraction window). Scoped on branch `claude/miso-zonal-refine-scope-vs1iao`;
all §8 decisions resolved 2026-07-01. Companion data:
`data/raw/capacity-deliverability/miso/miso.csv` (740 rows, PY2023-24 → PY2025-26
× 4 seasons × LRZ 1-10: CIL/CEL/ZIA/LRR/LCR/PRMR, sourced from MISO LOLE Study
Reports and PRA Results PDFs; parser `scripts/lib/capacity_deliverability/miso.py`,
loader `src/market_sim/data/capacity_deliverability.py`).

## 0. Why (established, not re-litigated here)

At 3 zones MISO is a copperplate: in keeper-probe
`2026-07-01-miso-34-reserve-coopt` all three zones price identically in every
one of 8,760 hours (annual zone-mean LMP $32.16/$32.16/$32.16 in 2023,
$29.93/$29.93/$29.94 in 2024, $41.15/$41.15/$41.15 in 2025; max spread $0.30;
0 hours of separation >$1). The inter-zone links never bind — including the
real ~3 GW Central↔South RDT already in config. Consequences: no local
scarcity, so the (correct) MSSC+400 MW RBDC reserve co-opt is inert
(CT_PEAKER 1.8/3.1/4.0 TWh vs bench 25.6/26.5/26.2; scarcity tail 0 h >$200 vs
actual 30/37/88 h; model max price $61/$60/$73), and the surplus backfills into
coal (2025 coal +46.6 TWh over bench, +18.7%, vs +10.5% in the current keeper
`2026-07-01-miso-31-coal-sigmoid`; CC_REGULAR itself is +3.3/+5.3/−3.9 TWh).
No 3-zone offer-curve lever can manufacture locational behavior from a model
with zero locational structure. The reserve design in
`config/reserve_config.py` (`_miso_design`, :559-599) is correct and is reused
as-is once congestion exists — it is zone-count-agnostic
(`zone_mask = np.ones(n_zones)`), so the zonal split requires **no change** to
it; locational reserve families are a later, separate step (§6).

## 1. Target zone set: 6 zones, drawn as whole EIA-930 sub-BA (LRZ) unions

**Binding data constraint discovered in scoping:** EIA-930 reports MISO sub-BA
hourly demand at exactly **six** partitions — `0001` (LRZ 1), `0035` (LRZ 3+5),
`0004` (LRZ 4), `0006` (LRZ 6), `0027` (LRZ 2+7), `8910` (LRZ 8+9+10)
(`data/raw/zone-specific-demand/MISO/miso_subba_demand_2023-2025.csv`;
`eia_loader.py:1794-1812`). That is the finest measured hourly load available.
The repo's standing invariant (zone_assignment.py:202-211 ↔
eia_loader.py:1794-1803, tested at tests/test_zone_assignment.py:216) is that
the fleet and load partitions share identical sub-BA-union boundaries. The
proposed zone set is therefore **exactly the six sub-BA groups** — the maximal
partition with fully measured load, no synthetic disaggregation:

| Zone (new name) | LRZ | EIA-930 sub-BA | States | 2023-25 energy share | Justifying binding constraint (not fit) |
|---|---|---|---|---|---|
| `MISO-West` | 1 | `0001` | MN, ND, SD, MT | 0.1466 | Wind belt behind the MN/ND export interfaces (NDEX, MWEX); chronic wind-driven export congestion and negative-LMP pockets. Summer CIL 5.3-6.5 GW vs LCR 12.2-17.0 GW of LRR 18.4-22.1 GW — heavily self-supply-constrained at peak (CSV rows: PY2023-24 summer LRZ 1 import_limit 5301 / LCR 15076.1 / requirement 20588, LOLE Rpt p.5 + 2023 PRA p.17). |
| `MISO-Plains` | 3+5 | `0035` | IA, MO | 0.1385 | Iowa wind-export corridor into the eastern load centers; Z3's CIL is the most seasonally volatile in the footprint (PY2023-24: summer 6108 → fall 14375 MW, LOLE p.5), i.e. the transfer analysis itself says this boundary moves. |
| `MISO-Illinois` | 4 | `0004` | IL (Ameren) | 0.0676 | The W→E wheel-through zone between the wind west and the Indiana/Michigan load; Illinois Hub is MISO's price reference for validation. Z4 LCR collapses to 452 MW (PY2024-25 summer, PRA p.16) — a structurally import-served zone that should show *low* local scarcity, the counter-pattern that disciplines the topology. |
| `MISO-Indiana` | 6 | `0006` | IN, KY | 0.1340 | Load-east anchor; the IN↔MI interface it hosts is Michigan's import path. Z6 CIL 6.1-9.5 GW, LCR 10.2-13.3 GW (CSV, all seasons). |
| `MISO-East` | 2+7 | `0027` | WI, MI | 0.2422 | The Michigan import pocket + WUMS: Z7 ZIA is only 3.6-6.3 GW against LCR 15.5-20.1 GW of LRR 20.5-24.6 GW (e.g. PY2023-24 summer LRZ 7 import_limit 5087 / LCR 18785.5 / requirement 24428, LOLE p.5 + PRA p.17) — the strongest import-constrained pocket in MISO Midwest and the place local scarcity *must* appear. |
| `MISO-South` | 8+9+10 | `8910` | AR, LA, MS, E.TX | 0.2711 | Unchanged footprint. Electrically separate from Midwest; connects only over the RDT contract path (3,000 MW N→S / 2,500 MW S→N, MISO/SPP JOA Attach. A — already in config as the one-way link pair). Z9 LCR 18.1-20.6 GW of LRR 23.9-25.9 GW — the Entergy import dependence that should produce local scarcity when the RDT binds. |

Static fallback `load_share` values (used only when the zonal-shares parquet is
absent) are the measured 2023-25 energy shares above (sum = 1.0000).

Mapping sanity-check against MISO's 10 LRZs: every LRZ maps to exactly one
zone; the partition is `{1},{3,5},{4},{6},{2,7},{8,9,10}` — strictly finer than
today's `{1,3,5},{2,4,6,7},{8,9,10}` and exactly aligned to the LOLE/PRA data
in the CSV. `config/capacity_area_crosswalk.py:_MISO_LRZ_TO_ZONE` (:145-187)
updates one-for-one.

**What this deliberately does NOT split (and why):**

- **Michigan (Z7) from Wisconsin (Z2).** The most valuable further Midwest
  split — but EIA-930 has no load below `0027`. Splitting requires either
  MISO's per-LRZ "Regional Forecast and Actual Load" report
  (allowlist-blocked, miso-data-audit.md:222-230) or a fixed-share split of
  the `0027` shape using LRR-implied peaks (Z2 ≈ 12.7 GW, Z7 ≈ 20.9 GW summer
  → 38/62). Deferred; see open decision D1.
- **South into Z8/Z9/Z10 (Amite South / WOTAB / Entergy pockets).** Amite
  South and WOTAB are *sub-LRZ-9* load pockets — the CSV cannot see them at
  any granularity; isolating them needs MISO planning-study flowgate limits
  (published bilateral limits, per rule #11), plus a South load split (no
  EIA-930 data below `8910`; LRR-implied summer peak shares Z8/Z9/Z10 ≈
  24/62/14%). Deferred; see open decision D2. Getting the RDT to *bind* (so
  South separates as a whole) is the phase-1 structural win.

## 2. Links, TTCs, and how the CIL/CEL data enters

### 2.1 The decomposition problem, and the proposal that avoids it

CIL/CEL are **island-model** limits from the LOLE transfer analysis: LRZ k's
CIL is its total import capability from *everywhere else simultaneously*, not
a bilateral limit to any neighbor. Decomposing a zone's CIL into per-link
bilateral TTCs is inherently arbitrary (any apportionment is a fitted number
wearing a citation). The structurally faithful mapping is:

> **Use CIL/CEL as per-zone directional `InterfaceLimit`s over all of the
> zone's incident links — the exact quantity the data measures — and keep
> bilateral link `ttc_mw` values loose except where a published bilateral
> limit exists (the RDT).**

The machinery already exists and is proven: `InterfaceLimit`
(iso_configs.py:35-56) caps the signed sum of member-link flows;
`_build_interface_rows` (dispatch.py:608-690) accepts **hourly** caps and an
optional asymmetric reverse-direction bound — CAISO's corridor groups
(transmission.py:518-572) and PJM's per-(month×hod) external envelopes
(transmission.py:1867) both use it. One interface group per zone with
`cap = CIL` in the import direction and `CEL` in the export direction
reproduces the LOLE quantity exactly, with zero invented decomposition.

### 2.2 Proposed link set (7 interfaces, 8 `TransferLink`s)

Adjacency follows physical ties; the network is a light mesh, like PJM's
8-zone/11-link build (iso_configs.py:479-497), not a chain:

| # | Link | Physical basis | Bilateral `ttc_mw` seed | Binding mechanism |
|---|---|---|---|---|
| L1 | West ↔ Plains | MN–IA 345 kV ties | generous placeholder (Tier 3) | West CIL/CEL interface group |
| L2 | West ↔ East | MN–WI corridor (MWEX) | generous placeholder (Tier 3) | West + East interface groups |
| L3 | Plains ↔ Illinois | IA/MO–IL (Ameren) ties | generous placeholder (Tier 3) | Plains CIL/CEL group |
| L4 | Illinois ↔ Indiana | IL–IN ties | generous placeholder (Tier 3) | zone groups both sides |
| L5 | Illinois ↔ East | IL–WI ties | generous placeholder (Tier 3) | zone groups both sides |
| L6 | Indiana ↔ East | IN–MI interface (Michigan import path) | generous placeholder (Tier 3) | **East import group ≈ Z2+Z7 CIL** |
| L7 | Plains → South / South → Plains | RDT contract path across SPP | **3,000 / 2,500 MW one-way pair — kept verbatim** (MISO/SPP JOA Attach. A; today's config values, iso_configs.py:398-409) | the published bilateral limit IS the constraint |

"Generous placeholder" means deliberately non-binding (e.g. 2× the zone's max
seasonal CIL) so that **all congestion is carried by the cited per-zone
CIL/CEL interface groups plus the RDT** — no invented bilateral numbers, per
rule #10's admissibility test (LOLE CIL/CEL regenerate every planning year
from forward drivers and respond to changed conditions; they are a
reproducible market/physical input, not an outcome). The old
`MISO-North→MISO-Central 12,000 MW` reconciled estimate (iso_configs.py:396,
documented as such) is **retired** — replaced by measured limits, per rule #11.

Cross-check on the South: the aggregate S↔N constraint remains the RDT
(3,000/2,500), which is *far* tighter than the sum of Z8+Z9+Z10 CILs
(11.9-17.2 GW — an island-model sum that double-counts intra-South transfers
and is not a Midwest↔South bilateral limit). The published RDT stays
authoritative; a `MISO-South` CIL/CEL interface group is therefore **omitted**
(it could never bind before the RDT does).

Per-zone interface-group values, summer PY2023-24 (illustrative; all four
seasons × three PYs come from the CSV loader):

| Zone group | Import cap = CIL (MW) | Export cap = CEL (MW) | CSV rows (source: PY2023-24 LOLE Study Report p.5) |
|---|---|---|---|
| West (Z1) | 5,301 | 3,959 | LRZ 1 summer import_limit / export_limit |
| Plains (Z3+Z5) | 9,684 (sum; ceiling — see D4) | 4,310 + n/a (Z5 CEL "No Limit Found" summer) | LRZ 3 + LRZ 5 rows |
| Illinois (Z4) | 7,884 | n/a ("No Limit Found" summer → unconstrained) | LRZ 4 rows |
| Indiana (Z6) | 8,492 | 2,703 | LRZ 6 rows |
| East (Z2+Z7) | 8,564 (sum; ceiling — see D4) | 6,503 (sum) | LRZ 2 + LRZ 7 rows |
| South (Z8+9+10) | — RDT governs — | — RDT governs — | JOA, not CSV |

Union-zone caveat (flagged per the task): for East and Plains the member-CIL
**sum is a ceiling**, because each member's island CIL counts help arriving
from the other member, which becomes internal after aggregation. For East the
overstatement is small (direct Z2↔Z7 ties across the Straits of Mackinac are
weak, so nearly all of both CILs is genuinely external); for Plains it is
larger (IA↔MO ties are substantial). Options in D4.

`export_limit` blanks ("No Limit Found": PY2023-24 summer Z4, Z5) mean the
LOLE study found no binding export constraint → model as unconstrained in that
direction for that season (no cap row), not as 0 and not as an invented number.

### 2.3 Seasonal vs annual caps

Seasonal variation is too large to ignore (Z3 CIL: 6,108 summer → 14,375 fall
in PY2023-24; Z4: 10,790 summer vs 3,928 winter across PYs). A single
conservative annual floor would import summer scarcity into shoulder seasons —
manufacturing congestion the real system doesn't have, which fails
structure-first just as badly as the copperplate. **Proposal: per-season hourly
caps.** The LP already accepts `(T,)` interface caps and `(T, n_links)` TTC
(dispatch.py:1519-1520, 608-690); the only wiring needed is expanding 4
seasonal scalars into an 8760 vector — the same pattern as NYISO's monthly TTC
shim (`scripts/run_calibration.py:_apply_iso_monthly_ttc`, :1733-1772,
currently hard-gated `if iso != "NYISO"`), but fed from
`data/capacity_deliverability.py` (which already loads MISO seasonally,
default "summer", :45-48) instead of a constants table.

Delivery-year alignment: PY seasons are Jun-May (Summer Jun-Aug, Fall Sep-Nov,
Winter Dec-Feb, Spring Mar-May). Calendar-year backcasts therefore straddle
two PYs, and **Jan-May 2023 falls in PY2022-23, which is not in the CSV**
(extraction starts PY2023-24). See D5.

## 3. Plant and load remapping

**Plants** (`data/zone_assignment.py`): MISO assignment is state-FIPS-based
(`_MISO_STATE_ZONES`, :212-228) with eGRID `BACODE == "MISO"` membership
filtering — and the six proposed zones are, like today's three, exact unions
of whole states, so the remap is a 15-line dict edit with **no county or
coordinate logic needed**: MN/ND/SD/MT→West; IA/MO→Plains; IL→Illinois;
IN/KY→Indiana; WI/MI→East; AR/LA/MS/TX→South. The latitude-band fallback
(:230-241, South <36° / North ≥43°) can no longer resolve the Midwest zones —
it degrades to South vs a single Midwest default and matters only for plants
whose state is outside the map (rare).

**The 28/1975 fallback-zone plants**: MISO is absent from
`_EIA860_SUPPLEMENT_ISOS` (zone_assignment.py:783-785), so post-eGRID-2023
plants get no EIA-860 lat/lon supplement and land in the largest-share zone.
Two changes: (a) add MISO to the supplement set — resolves most of the 28;
(b) note that "largest zone" flips from MISO-Central (0.444) to MISO-South
(0.2711) under the new shares — an *unacceptable* default for Midwest plants,
so (a) is required, and the residual fallback should be pinned to
`MISO-Illinois`-adjacent Midwest rather than `max(load_share)` (small logic
change at fleet.py:2888-2891 / zone_assignment.py:76-87).

**LRR capacity sanity check** (validation-time, per the task): for each new
zone, compare Σ pmax (fleet after remap) + zonal import ability against the
zone's seasonal LRR from the CSV (`requirement` rows; per-LRZ peak =
LRR / value_pu). Implied summer peaks: West ≈ 18.1-18.9 GW, Plains ≈ 17.6-18.1,
Illinois ≈ 8.8-9.3, Indiana ≈ 17.3-17.8, East ≈ 33.5-34.1, South ≈ 32.9-35.3.
A zone whose installed capacity < LCR or > 2× LRR flags a mis-assignment.

**Load** (`eia_loader.py` + `scripts/curate_zonal_shares.py`): update
`_MISO_SUBBA_ZONE_GROUPS` (:1804-1811) to the 1:1 mapping (each sub-BA its own
zone, `8910`→South), re-run `curate_zonal_shares.py` to regenerate the clean
`zonal-shares` parquet. **Hazard:** `load_zonal_shares`
(eia_loader.py:1758-1791) reindexes by zone name with `fill_value=0.0` — a
renamed zone with a stale parquet silently gets zero load. Mitigation: add a
guard (all-zero zone share → hard error) in the same edit.

**New data needed for §1/§3: none.** Load, fleet, and the CIL/CEL data are all
on disk. (New data is needed only for validation LMPs and the deferred splits —
§7.)

## 4. Renewables, hydro, storage, and the zone-keyed sidecar files

- **Wind shape — the one hard rebuild.** MISO is the only ISO with per-zone
  wind shapes (`_WIND_ZONE_SHAPE_ISOS`, renewables.py:259), and the loader
  **silently reverts to a single ISO-wide shape unless the parquet has a
  column for every model zone name** (renewables.py:1411-1412). The W→E
  congestion story *is* the wind-shape story, so this fallback would defeat
  the whole refinement. `scripts/build_miso_wind_shape.py` must be re-run with
  6 zone columns (NASA POWER WS50M at the largest EIA-860 wind plants per new
  zone; wind concentrates in West/Plains; South stays a placeholder mean).
- **Wind/solar capacity split**: automatic — `_eia860_zone_shares`
  (renewables.py:758-783) re-splits via the updated zone lookup. Fallback
  `RENEWABLE_ZONE_ALLOCATION["MISO"]` (renewables.py:180) re-points wind→West;
  solar target chosen from EIA-860 at implementation time. Same constant feeds
  new-build siting in capacity evolution (capacity.py:1252).
- **Hydro / storage**: automatic — both resolve per-plant via
  `build_zone_lookup` (hydro.py:354-366; storage.py:321-375). Pumped-storage
  zone aggregates re-form (today North 408 / Central 1,979 / South 30 MW → the
  1,979 lands mostly in East (Ludington, MI) — worth eyeballing post-remap).
- **Zone-keyed sidecar files** (all re-keyed, mechanical):
  `data/raw/reference/iso_zone_weather_stations.csv` (11 MISO rows → e.g.
  Minneapolis→West; Des Moines/St Louis→Plains; Chicago→Illinois;
  Indianapolis→Indiana; Detroit/Milwaukee→East; South unchanged);
  `data/raw/miso_zonal_gas_hub.csv` (9 rows; IA basis→West+Plains,
  IL→Illinois+Indiana, LA→South — or add distinct hubs, implementation
  detail); `data/raw/reference/reliability_floor_coeffs_MISO.csv` (39 rows —
  the 2 enabled rows, `MISO-North,ST_GAS,tmax` and `MISO-South,COAL,tmax`,
  must be **re-derived** at the new granularity via
  `scripts/derive_miso_temp_reliability_floor.py`, not just re-keyed);
  `data/raw/miso-weather/miso_zone_temp_daily.csv` (re-fetch via
  `scripts/fetch_zone_temperature.py`); `_validation-source/MISO_*_renewable_capacity.csv`
  and `calibration_reference.json` (rebuild via `build_calibration_reference.py`).
- **Interchange config** (`config/interchange_config.py`): `IMPORT_NODE_LINKS["MISO"]`
  (:199-203; external border links Central 7300 / North 4000 / South 3000 MW)
  re-point to the new border zones (Illinois/Indiana ↔ PJM, West ↔ SPP/Manitoba,
  East ↔ PJM/IESO, South ↔ SPP); `MISO_MANITOBA_FIRM_IMPORT_ZONE` (:447)
  becomes `MISO-West`; the 8,700 MW simultaneous-import limit (:513) carries over.

## 5. Code touchpoints (exact edit list)

| # | File | Edit |
|---|---|---|
| 1 | `config/iso_configs.py:332-418` | 6 zones + shares; 8 links (L1-L7); per-zone seasonal CIL/CEL `InterfaceLimit`s (new seasonal-cap plumbing, see #2); retire the 12,000 MW estimate; docstring |
| 2 | `model/transmission.py` + `data/capacity_deliverability.py` | new builder `build_miso_deliverability_groups` expanding seasonal CIL/CEL → hourly interface caps (pattern: `build_caiso_corridor_flow_groups`, transmission.py:518-572); un-gate or generalize the NYISO-only seasonal-TTC shim in `scripts/run_calibration.py:1698-1772` |
| 3 | `data/zone_assignment.py:212-241, 76-87, 650-668, 783-785` | 6-zone state map; lat-fallback rework; MISO into `_EIA860_SUPPLEMENT_ISOS`; fallback-zone logic |
| 4 | `data/eia_loader.py:1804-1811, 1758-1791` | 1:1 sub-BA map; all-zero-share guard |
| 5 | `scripts/curate_zonal_shares.py` | regenerate zonal-shares parquet (derived, gitignored) |
| 6 | `config/capacity_area_crosswalk.py:145-187` | `_MISO_LRZ_TO_ZONE` 1:1 |
| 7 | `config/interchange_config.py:199-203, 320-343, 447, 513` | border zones, Manitoba import zone |
| 8 | `data/renewables.py:180` + `scripts/build_miso_wind_shape.py` | allocation constants; **rebuild 6-column wind-shape parquets** |
| 9 | `config/reserve_config.py` | **no change for phase 1** (zone-agnostic); phase 2 locational families per §6 |
| 10 | `data/fuel.py:546-548` + `miso_zonal_gas_hub.csv` | re-key zonal gas basis |
| 11 | sidecar CSVs per §4 | re-key / re-derive / re-fetch |
| 12 | `model/capacity.py:1120, 1340, 1634-1638` | new-entry/backstop zone default (largest-share is now South — pin Midwest default) |
| 13 | tests: `test_zone_assignment.py` (26 refs), `test_iso_config.py` (8), `test_miso_firm_imports.py` (6), `test_fuel.py` (6), `test_renewables.py` (3), `test_capacity_area_crosswalk.py` (2), `test_eia_loader.py` (1) | update fixtures/asserts; add seasonal-interface-cap test (trivial case first: 2 zones, 24 h, per CLAUDE.md) |
| 14 | docs: `model-methodology-spec.md`, `docs/multi-iso/miso-data-audit.md`, `docs/parameter-citations.md`, `04-transmission-zones-and-congestion.md` as-built table | via `/sync-docs` at the end |

Rename blast radius: 34 code/data files hardcode `MISO-North/Central/South`
(9 src, 7 scripts, 7 tests, 11 data). `MISO-South` keeps its exact footprint —
reusing that name is safe and shrinks the radius; the five new Midwest names
must NOT reuse `MISO-North`/`MISO-Central` (prevents silent stale-parquet /
stale-CSV collisions — the zero-fill hazard above).

## 6. Reserve co-opt at 6 zones (phase 2 of this workstream, scoped now)

Phase 1 re-runs the existing market-wide `miso_rbdc` family unchanged —
congestion alone may re-fire the tail (South scarcity while the RDT binds
means the *zonal* energy price spikes even with a market-wide reserve
product). If the tail is still short, phase 2 adds locational families using
the **existing NYISO template** (`NYISO_RCPF_LOCATIONAL`,
reserve_config.py:96-112 — zone-name-tuple-keyed nested families;
`_nyiso_design` :605-700 is the only design receiving `zone_names`, so
`_miso_design`'s signature gains that parameter): a `MISO-South`-only family
(reserves deliverable across the RDT are limited) and optionally a
`MISO-East` family (Michigan pocket). Requirement basis: MISO's actual
sub-regional operating-reserve requirements; the PRMR North/South subregional
rows in the CSV (PY2025-26 only) are *capacity* constructs — a cross-check,
not the operating requirement itself.

## 7. Validation plan — structural gates first, MAE later

Gate on congestion existing, not on the residual (rule #1). In order:

1. **Links bind.** Hours with any binding internal interface > 0. Specifically:
   RDT binds N→S in summer peak hours; the West/Plains export groups bind in
   high-wind shoulder hours; East import group binds at Michigan peaks.
   Report per-interface binding-hour counts per year (new run-report table).
2. **Prices separate.** Hours with max inter-zone spread >$1 goes from 0 to
   O(10²-10³); South and East mean LMP move above West; the model's
   West-discount / South-premium sign pattern matches actual hub spreads.
3. **LCR consistency.** Zones with high LCR/LRR (East: Z7 LCR≈19-20 GW of 24.5;
   South: Z9 18.1-20.6 of 24-26; West: 12.2-17.0 of 18.4-22.1) show imports at
   their limits during their scarcity hours; Illinois (LCR→452 MW in PY2024-25
   summer) shows near-zero local scarcity. This uses the CSV's LCR/PRMR as an
   observable cross-check on zonal capacity balance, per the task.
4. **Reserve tail re-fires.** With co-opt re-enabled (miso-34 config, unchanged
   reserve design), scarcity tail moves off 0 h toward actual 30/37/88 h; the
   fleet-mix symptom unwinds (CT_PEAKER lifts from 1.8-4.0 TWh toward bench
   ~26 TWh; 2025 coal overshoot shrinks from +46.6 TWh).
5. **Only then** price-level MAE / duration-curve calibration, all three years
   (2023 2024 2025) in one bundle, registered on the dashboard per rules
   #14/#15 — including rejected probes.

**Validation data gap — CLOSED (D6 landed 2026-07-02):** the per-hub actuals
are in: `scripts/fetch_miso_hub_lmp.py` stages the eight named trading hubs'
RT-final/DA-ex-post rows from MISO's daily market reports (source reachable,
no 403; compact stagings in `data/raw/lmp-data/MISO/`), and
`scripts/derive_miso_hub_lmp.py` reduces them to
`_validation-source/actual_lmp_hourly_zonal_MISO.parquet`
(`year,hour,hub,zone,rt,da`, model Central-prevailing clock — verified
hour-for-hour identical to the committed system series, which turns out to
be the Indiana Hub). Hub→zone: Minn→West, Ill→Illinois, Ind→Indiana,
Mich→East, Ark/La/Tx/MS→South; **Plains has no hub — documented proxy =
MINN+ILLINOIS hub mean** (the two hubs bracketing the IA/MO wheel-through).
`build_miso_lmp_reference.py` adds the per-zone `zones` block to
`actual_lmp.json`, `curate_validation.py` carries per-zone price rows into
the clean `validation` datatype, and `report_miso_zonal_gates.py` gate 2 now
scores spread sign AND magnitude against the actuals. **Measured answer to
the miso-35 question: actual South mean LMP sits BELOW every Midwest zone in
all of 2023/2024/2025, both RT and DA** (2023 RT: Ind 31.79 > East 29.96 >
West 28.75 > Plains 28.48 > Ill 28.20 > South 27.04); the original "South
above West" heuristic in gate 2 was wrong on sign and the gate now uses
pairwise mean-order agreement against the measured hubs instead.

## 8. Open decisions — RESOLVED 2026-07-01

All seven decisions were put to the model owner as decision cards and
resolved as follows. The original option analysis is kept below for the
record.

| # | Decision | Resolution |
|---|---|---|
| D1 | Michigan/Wisconsin split | **Defer — ship 6 zones.** East keeps measured `0027` load; the Michigan pocket is bounded by the Z2+Z7 CIL import group. A 7th zone is a later additive step. |
| D2 | South split (Z8/Z9/Z10, Amite South/WOTAB) | **Defer to a later phase.** Phase 1 gates on the RDT binding; a split waits for a South load disaggregation and published sub-Z9 flowgate limits. |
| D3 | RDT attachment zone | **Decide by probe.** Implement on `MISO-Plains` (truest to the SPP/AECI wheel path); at gate 1, if RDT binding produces spurious Plains congestion, swap the attachment to `MISO-Illinois` in a single diagnostic re-solve before proceeding. |
| D4 | Union-zone caps | **CIL-sum ceiling, documented.** ΣCIL/ΣCEL of members as the cap, with a comment stating it double-counts intra-union help (small for East, larger for Plains). **CIL, not ZIA**, for energy-flow caps; ZIA stays in capacity/RA logic. |
| D5 | Jan–May 2023 coverage | **Extend the extraction to PY2022-23** — run the existing parser on the PY2022-23 LOLE Study Report so every backcast month has measured seasonal limits. **LANDED 2026-07-02** (annual pre-seasonal set, season "annual"; Jan–May 2023 caps now measured). |
| D6 | Zonal LMP validation data | **Request MISO hub RT/DA LMPs 2023–25 now** (manual upload, blocked source). Runs in parallel; gates 1/3/4 don't wait on it. **LANDED 2026-07-02** (source turned out reachable — fetched directly; see §7). |
| D7 | Seasonal vs annual caps | **Per-season caps.** Expand the 4 seasonal scalars per zone/PY into hourly interface-cap vectors (NYISO monthly-TTC shim pattern). |

### Original option analysis (for the record)

- **D1 — Split Michigan (Z7) from Wisconsin (Z2)?** Structurally the best
  Midwest pocket, but no EIA-930 load below `0027`. Options: (a) defer — ship
  6 zones (recommended: East's import group already creates the pocket at
  union granularity); (b) split now using fixed LRR-peak shares (Z2/Z7 ≈
  38/62) on the `0027` shape — loses intra-pair load diversity; (c) request
  MISO per-LRZ load report (blocked source, manual upload).
- **D2 — South split (Z8/Z9/Z10) and Amite South/WOTAB.** Defer to a later
  phase (recommended): needs a South load disaggregation (no EIA-930 data;
  LRR shares ≈ 24/62/14) and, for the true sub-Z9 pockets, published planning
  flowgate limits rather than CIL proxies (rule #11). Phase 1's win is the
  RDT binding at all.
- **D3 — RDT attachment zone.** The contract path wheels across SPP; on the
  Midwest side I propose attaching to `MISO-Plains` (MO/AECI side). Attaching
  to `MISO-Illinois` instead changes which Midwest zone eats the S→N flow.
  Weakly held — pick one and verify against gate 1 binding patterns.
- **D4 — Union-zone import caps: CIL sum vs tighter reconciliation.** For
  East (Z2+Z7) and Plains (Z3+Z5) the member-CIL sum is a ceiling. Options:
  (a) use the sum, documented as a ceiling (recommended for East — weak
  internal ties → small overstatement); (b) subtract an estimate of
  intra-union transfer (Plains: IA↔MO ties are real — but the subtraction is
  itself an estimate); (c) hunt a published bilateral interface (MTEP/OASIS,
  historically 403-blocked). Also: use **CIL** (transmission limit) rather
  than **ZIA** (CIL adjusted for Border External Resources — a capacity
  accounting quantity) for energy-flow caps; ZIA belongs in capacity/RA logic.
  Confirm.
- **D5 — Jan-May 2023 seasonal caps.** PY2022-23 is not in the CSV. Options:
  (a) extend the extraction to the PY2022-23 LOLE report (cleanest, same
  pipeline); (b) backfill those months with PY2023-24 same-season values,
  documented. Recommend (a) if the PDF is obtainable, else (b).
- **D6 — Zonal LMP validation data.** Approve requesting/uploading MISO hub
  RT/DA LMPs 2023-25 (blocked-source manual upload). Not blocking: gates
  1/3/4 run without it.
- **D7 — Seasonal caps vs annual floor.** I recommend per-season caps (§2.3;
  the LP supports it, the data is natively seasonal, and an annual floor
  fabricates shoulder-season congestion). Confirm, since it adds the one new
  plumbing piece (seasonal→hourly expansion for MISO).

## 9. LP scale and RAM headroom

Column arithmetic (`VariableLayout`, dispatch.py:28-140:
`vars/hour = n_gen + 4·n_zones + 3·n_storage + n_links + n_reserve + n_ordc`):
MISO dispatch fleet ≈ 2,353 LP units, n_storage ≈ 9, and with the external
node today's topology is 4 zones/6 links → ≈ 2,414 vars/hour ≈ 21.1M columns
(T=8760, co-opt on). At 6 zones (7 with external) / 8 internal + ~4 external
links: ≈ 2,440 vars/hour — **+1.1% columns**, plus 3 more energy-balance rows
and ~5 seasonal interface-cap rows per hour (trivial nnz: 1-3 entries/row).
The matrix is generator-dominated; zone count is a second-order term.

RAM: the 3-zone co-opt run peaked 12.9 GB on this 15 GB / 4-core box.
Projected 6-zone peak ≈ 13.1-13.5 GB — inside the ceiling but with thin
margin. Mitigations, in order: cap HiGHS threads (per-thread dual-simplex
factorization workspaces are the known blow-up — dispatch.py:1915-1918); run
MISO solo (no concurrent calibration invocations, consistent with rule #12's
~2-run cap); years stay sequential as always. Phase-2 locational reserve
families add `n_reserve = classes × zones` columns (7/hour) and per-family
balance rows — still noise. **Do not** add per-generator reserve rows
(documented memory-infeasible at MISO plant scale,
docs/multi-iso/miso-reserve-coopt.md:63-64). If a future 8-10-zone MISO (D1/D2)
plus commitment screens threatens the ceiling, that's the point to consider
it, not now.

## 10. Suggested implementation order (for the follow-up session)

Stage A→H per `00-iso-addition-protocol.md`, compressed: (1) topology + state
map + sub-BA map + crosswalk + tests green at static caps; (2) seasonal
interface-cap plumbing + trivial-case test; (3) wind-shape rebuild + sidecar
re-keys; (4) full 3-year backcast, gates 1-3; (5) re-enable reserve co-opt,
gate 4; (6) dashboard registration (keeper or probe — either way it goes on
the dashboard, rules #14/#15); (7) `/sync-docs`.
