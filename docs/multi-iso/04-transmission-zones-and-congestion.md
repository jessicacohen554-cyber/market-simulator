# Transmission Zones, Congestion Corridors, TTC & Renewable HSL

> **As-built note:** the topologies *proposed* below have since landed in
> `config/iso_configs.py`, in several cases at a finer grain than this plan
> sketched. **The authoritative, current per-ISO zone/link counts live in
> `config/iso_configs.py`** (summarized in CLAUDE.md's Architecture section) — this
> doc no longer maintains a duplicate topology table, which had drifted from code
> (e.g. it still listed MISO at 3 zones N/C/S after the live build refined MISO to
> 6 zones, per the MISO section below).
>
> Read the per-ISO "Target topology" / "Start" lines below as the original
> sourcing plan, not current state. **Code is the source of truth for topology.**

Status: **planning (topologies since landed — see as-built note above).** This
proposes an aggregated zone topology and the major congestion corridors for each
ISO, identifies where to source TTC (transfer-limit) data, and identifies where to
source uncurtailed renewable potential (the ERCOT "HSL" analogue). Pairs with
Stage A/D in `00-iso-addition-protocol.md` and Pack A/B in `03-prompt-pack-plan.md`.

## Modeling philosophy (carried from ERCOT)

The model uses **aggregated transmission zones** connected by `TransferLink`s
with a single `ttc_mw`, *not* full nodal/PTDF. ERCOT collapses real GTCs into
7 zones (6 carry load) and 9 links; the same aggregation applies to every ISO — pick zones
that bound the ISO's real recurring congestion, then set each link's TTC from
the binding interface's observed limit.

**TTC sourcing method (the ERCOT gold standard, `scripts/derive_ttc_limits.py`):**
take the ISO's binding-constraint / shadow-price archive, find the interface's
mean observed limit and how often it binds, and use the mean limit as `ttc_mw`.
An aggregate interface that the model splits across two links is apportioned by
a fixed ratio (ERCOT splits WESTEX 8:3 West→North : West→South_Central). Until
that archive is processed, seed TTCs from the ISO's published path/flowgate
ratings and tag them **Tier 3 (calibration) — verify**, exactly like PJM's
current placeholders.

**Renewable HSL method:** ERCOT feeds the dispatch the *uncurtailed* High
Sustained Limit so the LP re-curtails under modeled transmission limits. For
other ISOs, uncurtailed potential ≈ delivered generation **+ reported
curtailment** where the ISO publishes curtailment; where it doesn't, fall back
to the EIA-930 delivered distribution (already embeds curtailment), which
`data/renewables.py` handles today.

---

## CAISO

**Start:** 1 zone (`CAISO_main`) + `WECC_import` node already in config.
**Target topology:** 3 trading zones — **NP15** (north), **ZP26** (central),
**SP15** (south) — plus the WECC import node. This matches CAISO's congestion-
revenue-rights regions and its real north–south split.

**Congestion corridors / links:**
- **Path 26** (NP15 ↔ SP15, via ZP26) — the dominant north–south intertie.
- **Path 15** (within NP15 corridor) — historic constraint.
- WECC import node → NP15/SP15 via the major DC/AC ties (Path 66 / COI to the
  north, Path 46 / West of River + Palo Verde to the south).

**TTC source:** CAISO OASIS transfer capabilities; WECC Path Rating Catalog
(Path 15, Path 26, Path 66 ratings); CAISO congestion/shadow-price data for the
binding-frequency method.

**Renewable HSL source:** CAISO **Production and Curtailment** data
(Wind/Solar) → uncurtailed = delivered + curtailed (economic + self-sched).
CAISO curtailment is large (multi-TWh/yr solar), so this matters. OASIS gives
hourly wind/solar; the curtailment report gives the add-back.

**Hydro:** large, snowpack-driven seasonal energy budget (Pack E essential).

---

## PJM

**As-built:** **8 zones / 11 links** in `config/iso_configs.py` — `PJM_ComEd`,
`PJM_AEP_Ohio`, `PJM_ATSI`, `PJM_West_APS`, `PJM_Central_PA`, `PJM_Dominion`,
`PJM_EMAAC`, `PJM_SWMAAC` — with cited zonal-peak load shares. (The "~4–5 zone
stub" described in the original plan below was superseded by this finer build;
PJM has 20+ real transmission zones, and this aggregation captures the chronic
west→east congestion.)

**Congestion corridors / links:**
- **AP South / 5004-5005 West interface** (West → East) — the classic PJM
  binding interface.
- **AEP–Dominion interface** (West → South).
- **Eastern / ChesPenn interface** (Central → East, into the Mid-Atlantic
  load pocket).

**TTC source:** PJM OASIS transfer limits; PJM RTEP; PJM interface-limit and
transfer-limit postings; PJM Data Miner congestion data for binding frequency.
Replace the placeholder 10/8/5/4/3 GW link values with cited postings.

**Load shares:** replace the approximate 0.37/0.28/0.20/0.15 with PJM Metered
Load by zone (State of the Market zonal peaks / PJM load data) via a generalized
`derive_load_shares.py`.

**Renewable HSL source:** PJM has historically modest curtailment; EIA-930
delivered distribution is an adequate first pass. PJM Data Miner solar/wind for
refinement.

---

## MISO

**Start:** absent — built from scratch; refined to six zones 2026-07-02.
**As-built topology (6 zones, whole EIA-930 sub-BA / LRZ unions):**
**MISO-West** (LRZ 1), **MISO-Plains** (LRZ 3+5), **MISO-Illinois** (LRZ 4),
**MISO-Indiana** (LRZ 6), **MISO-East** (LRZ 2+7), **MISO-South**
(LRZ 8+9+10) — the finest partition with fully measured hourly load
(`docs/multi-iso/miso-zonal-refinement-scope.md`). The original 3-region
build (North/Central/South) was a copperplate and was retired; the old zone
names must not be reused (stale-parquet collision hazard).

**Congestion corridors / links (as built):**
- **RDT contract path (Plains ↔ South)** — the defining constraint: the two
  MISO footprints connect only through a **contract path across SPP** with the
  **Regional Directional Transfer limit**, encoded verbatim as a one-way link
  pair (3,000 MW N→S / 2,500 MW S→N, one-way bounds enforced via
  `link_bidirectional`).
- **Six internal Midwest pipes** (West↔Plains, West↔East, Plains↔Illinois,
  Illinois↔Indiana, Illinois↔East, Indiana↔East) carry deliberately
  NON-binding placeholder TTCs; all internal congestion is carried by
  **per-zone directional CIL/CEL interface groups** — the exact island-model
  quantity MISO's LOLE transfer analysis publishes — expanded to per-season
  hourly caps in backcasts (`transmission.build_miso_deliverability_groups`).
  MISO-South carries no CIL group (the RDT is far tighter).

**Limit source:** MISO LOLE Study Reports (PY2023-24 → PY2025-26 CIL/CEL per
LRZ per season, `data/raw/capacity-deliverability/miso/miso.csv`); the RDT
limit is published in the MISO/SPP Joint Operating Agreement.

**Special:** MISO capacity construct is **seasonal** (4 seasons) — see Pack D /
module M8. Large wind (North) + coal (Central) fleet.

**Renewable HSL source:** MISO Market Reports publish wind curtailment /
manual redispatch → uncurtailed = delivered + curtailed. Significant in the
wind-rich north.

---

## SPP

**Start:** absent — build from scratch.
**Target topology:** 2 zones — **SPP-North** and **SPP-South** — a simple split
that bounds SPP's main north–south wind-export congestion. (Closest of all the
ISOs to ERCOT in market design: energy + RA obligation, no central capacity
market.)

**Congestion corridors / links:**
- **North ↔ South** wind-export corridor (SPP is wind-dominated; congestion is
  driven by moving northern/western wind to load).
- Seams with **MISO** (the RDT contract path above) and **ERCOT** (DC ties:
  but ERCOT↔SPP is small, model as import node if needed).

**TTC source:** SPP OASIS; SPP Integrated Transmission Planning (ITP); SPP
flowgate/binding-constraint data for binding frequency.

**Renewable HSL source:** SPP Market Reports / wind curtailment data →
uncurtailed = delivered + curtailed. Large — SPP routinely sets wind-penetration
records.

---

## NYISO

**Start:** 1 zone.
**Target topology:** NYISO has **11 zones (A–K)**. A faithful aggregation is
**Upstate-West (A–E)**, **Capital/Hudson (F–G)**, **Lower-Hudson (H–I)**,
**NYC (J)**, **Long Island (K)** — preserving the critical downstate import
constraints. A first pass can use Upstate / Downstate (2 zones) and refine.

**Congestion corridors / links:**
- **Total East / Central-East** interface (Upstate-West → Capital) — the major
  west-to-east constraint.
- **UPNY–SENY** and **Dunwoodie–South** (Hudson → NYC) — the downstate import
  limits into zone J.
- **Long Island (K)** import limit.

**TTC source:** NYISO publishes interface transfer limits directly (Central-
East, Total East, UPNY-ConEd, Dunwoodie-South, etc.) in the NYISO **Gold Book**
and operating limits postings — no archive reconstruction needed.

**Hydro:** very large — **Niagara (zone A)** and **St. Lawrence** — monthly
energy budgets essential (Pack E). Big **oil/dual-fuel** downstate (Pack F/G).

**Imports:** Hydro-Québec (Châteauguay/HQ ties into zone D), PJM (western
ties), ISO-NE, IESO/Ontario — model as priced import nodes (Pack C).

**Renewable HSL source:** smaller wind/solar; EIA-930 delivered distribution
adequate; NYISO curtailment data for refinement.

---

## ISO-NE (NEISO)

**Start:** 1 zone.
**Target topology:** ISO-NE has **8 load zones** (ME, NH, VT, CT, RI, SEMA,
WCMA, NEMA/Boston). Faithful aggregation: **North (ME/NH/VT)**, **Central
(WCMA/SEMA/RI)**, **Boston (NEMA)**, **Connecticut (CT)** — preserving the
Boston and CT import pockets. First pass can be North / South-Coast / Connecticut.

**Congestion corridors / links:**
- **North–South** interface (Maine wind/hydro → southern load).
- **Boston/NEMA import** and **Connecticut import** — the two load pockets.
- **SEMA/RI export.**

**TTC source:** ISO-NE publishes interface limits (North–South, Boston Import,
SE Mass/RI Export, Connecticut Import) in operating documents and the Regional
System Plan — directly usable.

**Imports:** **Hydro-Québec Phase II HVDC** (~2000 MW into NEMA), **Cross-Sound
Cable** and **Northport–Norwalk** to NYISO, **Highgate** to HQ — priced import
nodes (Pack C).

**Fuels:** large **oil / dual-fuel** peaking + the winter gas-to-oil switching
that drives ISO-NE winter prices (Pack F/G central here). Pumped storage
(Northfield Mountain) — Pack E / storage.

**Renewable HSL source:** modest; EIA-930 delivered distribution adequate;
ISO-NE curtailment data for refinement.

---

## Summary: where TTC and HSL come from

| ISO | TTC source (binding-freq method input) | HSL / uncurtailed source |
|-----|----------------------------------------|--------------------------|
| ERCOT | NP6-86 SCED binding constraints (done) | NP6 HSL (done) |
| CAISO | CAISO OASIS + WECC Path Ratings | CAISO Production & Curtailment |
| PJM | PJM OASIS / RTEP / Data Miner | EIA-930 dist. (+ Data Miner) |
| MISO | MISO OASIS / MTEP + RDT agreement | MISO Market Reports curtailment |
| SPP | SPP OASIS / ITP / flowgates | SPP Market Reports curtailment |
| NYISO | NYISO Gold Book interface limits (published) | EIA-930 dist. (+ NYISO curt.) |
| ISO-NE| ISO-NE RSP interface limits (published) | EIA-930 dist. (+ ISO-NE curt.) |

All proposed link MW values start **Tier 3 (calibration) — verify**, then move
to Tier 1/2 once sourced and validated against binding frequency, exactly as
ERCOT's WESTEX/PNHNDL limits were. Every final value gets a citation appended
to `docs/parameter-citations.md`.
