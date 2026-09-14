# NWPP Addition Program — plan, wave graph, prompt pack (2026-09)

Status: **CHARTERED 2026-09-13.** Chartering session: the **NWPP ADDITION DESK** (`NWPP-DESK`), sitting
r#0, pinned at `origin/main` **`2c2fc065`**.

This program adds the **Northwest Power Pool / Western Power Pool footprint** as the **ninth
registered region** in `config/iso_configs._ISO_BUILDERS` (eighth is SOCO, chartered 2026-09-12 and
not yet registered — see §0 below). It is the footprint the **Hermiston Generating Plant** sits in:
EIA plant **54761**, Umatilla County OR, **621.2 MW** across four `Natural Gas Fired Combined Cycle`
generators, operating 1996, balancing authority **`PACW`** (PacifiCorp - West), NERC region **WECC**
— confirmed in this session off `data/raw/eia-860/`. The adjacent **Hermiston Power Partnership**
(plant **55328**, 689.4 MW, operating 2002) is balancing authority **`GRID`** (Gridforce Energy
Management). **Two Hermiston plants, two balancing authorities** — which is the whole program in
miniature.

**What makes this region unlike every prior addition, stated at charter so it is never discovered
late.** NWPP is **not a balancing authority and not an ISO — it is a POOL of ~17 balancing
authorities**, the first such region in this repo. SOCO (the sibling program) at least has one BA,
one metered demand series and one fleet. Here there are seventeen of each. Everything downstream of
the registry calls the key an "ISO"; this plan says **"pool"** and **"balancing authority"**
everywhere rather than pretending otherwise, because the distinction is exactly what makes cards
**N1** (what the region even *is*) and **N5** (a zone cannot split a BA) load-bearing.

Director: the **NWPP ADDITION DESK** (lane id `NWPP-DESK`) — handoff prompt
`docs/handoffs/nwpp-desk-handoff-2026-09-13.md`, ledger `docs/handoffs/nwpp-desk-ledger-2026-09.md`.
**The ledger wins where this plan and the ledger diverge on live state.** This plan owns the charters
(§8) and the decisions (§3); the ledger owns who is running what.

Process authority: `docs/multi-iso/05-backcast-playbook.md` (Phase 0→6, §8 conventions), the
Stage A–H checklist of `docs/multi-iso/00-iso-addition-protocol.md` §1–2, and — as the worked
precedent for every mechanical step of an addition — `docs/multi-iso/spp-addition-plan-2026-09.md`
(the SPP program, chartered 2026-09-06, first keeper 2026-09-07). The **non-market** deltas are
shared with `docs/multi-iso/soco-addition-plan-2026-09.md` (chartered 2026-09-12), and §3 card N2
is explicitly coordinated with that program's card S2. Where this plan and the playbook disagree on
*NWPP specifics*, this plan wins; on *process*, the playbook wins. Where this plan is silent on a
mechanical step of registration, **the SPP plan's §2.3 / §7 is the default**.

## 0. Ordering against the SOCO program

SOCO was chartered 2026-09-12 as "the eighth registered region" and **has not registered** at this
plan's pin (`_ISO_BUILDERS` carries seven; measured §2.3). So "eighth" and "ninth" are claims about
*charter order*, not about the tree. Both programs flip the same pin list. The binding consequence:

- **Whichever program's W2 lands second re-counts.** Neither plan's §2.3 may be executed from its own
  number; the registering lane re-measures `SUPPORTED_ISOS` at **its own base sha** and reports the
  count it found (SPP collision rule 6, `spp-addition-plan-2026-09.md` §8.0).
- **The desks do not charter across the boundary.** NWPP-DESK never issues a SOCO lane, never edits a
  SOCO file, and never answers card S2 for that desk. Card **N2** below is *coordinated* with S2 and
  says so; it is not a joint ruling and this desk will not present one.

---

## 1. Definition of done

| # | Done means | Surface |
|---|---|---|
| 1 | `"NWPP"` in `config/iso_configs._ISO_BUILDERS`; `get_iso_config("NWPP").validate_topology()` passes; every ISO-keyed registry has an NWPP entry or a documented exclusion | `src/market_sim/` |
| 2 | A **2023–2025** backcast keeper (rule 16 `[R-ALLYEARS]`) scored under whatever rubric card **N2** produces, and registered on the backcast dashboard **with whatever determination it earns, reported at full magnitude** | `frontend/data/backcast/keepers/NWPP.json`, `backcast-runs.html#iso=NWPP`, `calibration-status.html#iso=NWPP` |
| 3 | `docs/codebase-site/data/mechanism-matrix/NWPP.js` shard live with a cell for every mechanism id; `docs/mechanism-testing-matrix.md` NWPP lever queue | matrix (rule 28 `[R-MECH-MATRIX]`) |
| 4 | `docs/calibration-log/nwpp.md` open; docs/site prose says nine regions (or eight — §0); `docs/multi-iso/00` §0/§3 extended | docs |
| 5 | **Every existing keeper's cache key never moves** at any wave (no new `ScenarioConfig` field, no default flip, no `results/cache.py` edit) | `tests/regression/test_persisted_identity.py`, keeper `run_config.json` |
| 6 | Forecast-program entry (T1-F hindcast, `program-status.json` row, `GOLDEN_ISOS`) — **ROUTED to the capx director, never this desk** (card N9) | `frontend/data/forecast/` |
| 7 | **The determination class card N2 limb (b) ruled actually EXISTS in `scripts/calibration_verdict.py`**, with byte-identical verdicts across every pre-existing keeper — without it an NWPP keeper cannot be scored at all (lane NWPP-22, owner ruling **N11**) | `scripts/calibration_verdict.py`, `tests/scoring/` |

What this plan does **not** charter: any change to how **CAISO** prices its side of the WECC seam
(card N4 routes it); any forecast-namespace write (card N9).

**The rubric prohibition is CARVED, once, by owner ruling N11 (2026-09-13).** This plan originally
refused *any* change to the rubric — written when card N2 was unruled, so that the desk could not
answer its own question. N2 is now ruled, and limb (b) **authorized a determination class that does
not exist in the code**: `scripts/calibration_verdict.py` carries no branch able to express it, so a
solved NWPP keeper would be unscoreable. The owner ruled *send it now*. **Lane NWPP-22 is the sole
exception and its licence is narrow**: ONE added determination branch, a data-driven predicate (never
an `if iso ==` ladder), no existing criterion's thresholds/bands/tiers/budgets touched, and
**byte-identical verdicts over every pre-existing keeper as the pass/fail exit**. No other lane in
this program may touch the scorer.

---

## 2. Verified state at charter (2026-09-13, `origin/main` `2c2fc065`)

Everything in §2.1–§2.7 was **measured in this chartering session** off the committed tree or probed
live from it, at the pin above. No number here is recalled or inferred; anything not measured says
"pending <lane>". Where a measurement **corrects or extends** the facts this desk was handed, it says
so explicitly.

### 2.1 The fleet — measured off EIA-860

Join: `data/raw/eia-860/eia860_plant.parquet` (carries `Balancing Authority Code`) → 
`eia860_generator_operable.parquet` on `Plant Code`, over the 17-BA candidate footprint
(BPAT PACE PACW PGE PSEI AVA IPCO NWMT CHPD DOPD GCPD SCL TPWR AVRN GRID WAUW NEVP).

| Measure | Value |
|---|---|
| Plant-table rows carrying a footprint BA | **1,082** |
| Plants with ≥ 1 **operable** generator | **940** |
| Operable generators | **1,932** |
| Nameplate | **98,738.1 MW** |
| NERC region | **WECC 98,238.1 MW / 1,930 gens** · **TRE 500.0 MW / 2 gens** — a source defect, §2.2 |

**By balancing authority** (plants · generators · MW):

| BA | Plants | Gens | MW | | BA | Plants | Gens | MW |
|---|---:|---:|---:|---|---|---:|---:|---:|
| BPAT | 130 | 388 | 30,513.9 | | AVA | 30 | 79 | 2,309.0 |
| PACE | 173 | 313 | 18,737.4 | | SCL | 9 | 31 | 2,068.1 |
| NEVP | 106 | 261 | 15,656.9 | | CHPD | 3 | 32 | 2,037.8 |
| IPCO | 134 | 204 | 4,871.8 | | DOPD | 2 | 12 | 1,366.8 |
| NWMT | 52 | 119 | 4,265.1 | | GCPD | 1 | 10 | 1,220.0 |
| PGE | 100 | 149 | 4,219.7 | | WAUW | 22 | 46 | 1,128.3 |
| PSEI | 34 | 81 | 3,339.0 | | TPWR | 7 | 21 | 724.8 |
| AVRN | 19 | 25 | 2,848.7 | | GRID | 1 | 3 | 689.4 |
| PACW | 117 | 158 | 2,741.4 | | | | | |

**By technology** (MW): conventional hydro **35,799.5 (36.3 %)** · CC 15,609.3 · onshore wind
14,460.3 · solar PV 10,049.9 · coal 8,910.2 · CT 4,565.5 · batteries 2,522.0 · gas ST 2,163.0 ·
**nuclear 1,200.0** · geothermal 972.6 · gas ICE 732.7 · wood/wood-waste 629.7 · **pumped storage
314.0** · solar thermal 202.2 · petroleum liquids 87.7 · landfill gas 85.8 · pet coke 68.0 · other.

**By state** (MW), from the BA × state pivot: **WA 31,711.8 · UT 9,769.3 · WY 8,654.1 · OR 19,035.4
· NV 15,638.3 · ID 6,431.3 · MT 6,940.4 · TX 500.0 · CA 50.8 · CO 7.5.**

**The four facts that shape the whole program:**

1. **Hydro is the footprint, and it is extraordinarily concentrated.** 288 conventional-hydro plants
   hold 35,799.5 MW. **Eight plants ≥ 1 GW hold 17,821.8 MW — 49.8 % of all hydro** (Grand Coulee
   6,495.0 · Chief Joseph 2,456.2 · John Day 2,160.0 · The Dalles 1,819.7 · Rocky Reach 1,349.2 ·
   Wanapum 1,220.0 · Bonneville 1,162.0 · Boundary 1,159.7). At the other end **141 plants below
   10 MW hold 504.1 MW between them — 1.4 %**. Card **N3**.
2. **Pumped storage is nearly absent**: 314.0 MW, one plant, in BPAT. This footprint's flexibility is
   *inflow* hydro, not storage.
3. **Nuclear is one unit**: Columbia Generating Station, 1,200.0 MW, BPAT.
4. **It is majority vertically-integrated**: by plant `Sector Name`, **Electric Utility 68,860.0 MW
   (69.7 %)**, IPP Non-CHP 26,962.3, IPP CHP 1,568.8, Industrial CHP 1,028.8, the rest < 200 MW. The
   PJM `retirement_sector_gate` precedent (CLAUDE.md capx D53/D78) is therefore *more* relevant here
   than in any registered ISO — flagged for W5, **not** chartered now.

**Coal**, the exit-exposed class (32 units, 8,910.2 MW): Colstrip 1,647.4 (NWMT/MT) · Hunter 1,472.2
(PACE/UT) · Jim Bridger 1,161.9 (PACE/WY) · Huntington 1,015.5 (PACE/UT) · Dave Johnston 816.7
(PACE/WY) · Centralia 729.9 (BPAT/WA) · Bonanza 499.5 · Naughton 380.8 · Wyodak 362.1 · North Valmy
289.8 · TS Power 242.0 · Hardin 115.7 · five units < 60 MW. Only one carries an EIA-860 planned
retirement inside the visible horizon (**229.5 MW of coal dated 2027**); the rest are undated in 860.

### 2.2 What is missing, and one source defect

`actual_lmp.json` NWPP block **and the series behind it — see §2.6, this is card N2** ·
`NWPP_<yr>_renewable_capacity.csv` + `calibration_reference.json` NWPP block ·
`campd-unit-outages-NWPP.csv` (needs ID/OR/UT/WA CEMS — §2.3) · per-zone wind/solar shape ·
inter-zone TTCs (card N5) · zonal gas hub · a **hydro energy budget for 288 plants** (card N3) ·
PRM / VOLL / WRAP citations ·
`scripts/lib/{load_forecast,confirmed_retirements,nuclear_license_status,transmission_expansion}/nwpp.py`.

**The TRE defect.** Two generators totalling **500.0 MW** are filed under balancing authority `DOPD`
(Douglas County PUD, Washington) with **state `TX` and NERC region `TRE`**. A Washington PUD does not
own a 500 MW plant inside ERCOT's interconnection, and DOPD's real fleet is the 866.8 MW Wells
hydro project. This is the direct analogue of the SOCO program's "MA 1.5 MW" row. **NWPP-10
adjudicates it and states the rule it applied**; the desk's reading is that it is a source
mis-key and the two rows leave the footprint, but the desk does not decide it.

### 2.3 The pin list — every place that flips at registration (W2 atomicity list)

Measured at `2c2fc065` by counting `"SPP"` occurrences per file, i.e. by reading the **previous
addition's own footprint**. **22 modules under `src/market_sim/`, 33 under `scripts/` (of which 14
are one-off probes or SPP-specific derives that an NWPP lane does not touch — the real count is
~19), and 48 files under `tests/`.**

| Pin | Path (SPP occurrences) | Action |
|---|---|---|
| Builders + demand loaders | `config/iso_configs.py` (6) `_ISO_BUILDERS:1936` → `SUPPORTED_ISOS:1954`; `data/eia930/demand.py` (1) `DEMAND_LOADERS` + its import-time assert | **same commit** — the assert rejects loader keys ∉ `SUPPORTED_ISOS` |
| Solve-surface fingerprint | `config/solve_surface.py:75` `SURFACE_ISOS` (hardcoded 7-tuple, pinned == `SUPPORTED_ISOS` by `tests/unit/config/test_solve_surface.py`); `config/solve_surface_declared.py` | add `"NWPP"` in the SAME commit; `scripts/solve_surface_register.py --diff origin/main HEAD` must show **zero moved rows** for every existing ISO |
| Interchange | `model/interchange/spec.py` (12), `model/interchange/registry.py` (1) | NWPP's own `INTERFACE_NEIGHBORS` + served-schedule membership (`_SCALAR_INTERCHANGE_ISOS`) — card N4 |
| Constants | `config/constants.py` (11) — PRM, queue caps, RPS floors, ELCC, tail/amplitude keys, **`HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT`** (card N3) | one block, cited per value (rule 5 `[R-NO-MAGIC]`) |
| Capacity market | `config/capacity_market.py` (10) — `MARKET_DESIGN`, `_CURVE_ISOS`, `_CAPACITY_ISOS` | NWPP **absent** from all three (no capacity market) → `DEFAULT_MARKET_DESIGN`; the absence is documented, not accidental (card N7) |
| Zone assignment | `data/zone_assignment.py` (5) — `_SPP_STATE_ZONES:354` is the template | **NWPP does NOT map on state** (card N5: a state holds several BAs and a BA holds several states) — it maps on **`Balancing Authority Code`**, which is a new shape for this module and the one genuinely novel code change in W2 |
| Renewables / fuel / reserves | `data/renewables.py` (5), `config/fuel_trajectories.py` (3), `model/reserves/spec.py` (3) | per cards N5/N7 |
| Pipeline + runner | `pipeline/backcast_config.py` (2), `pipeline/kwargs.py` (1), `pipeline/commitment.py` (1), `runner.py` (1) | one line each |
| Data leaves | `data/campd.py` (`ISO_STATES["NWPP"]`), `data/eia930/{frames,envelopes,demand}.py`, `data/fleet/models.py` (`BA_CODE_TO_ISO` — **a 17→1 mapping, not 1→1; the first such entry**), `data/neighbor_price.py`, `data/transmission_expansion.py`, `config/paths.py` | one key each, except `BA_CODE_TO_ISO` (card N1) |
| Tail threshold ×3 | `scripts/calibration_verdict.py:661` `TAIL_THRESHOLD`, `scripts/data/derive_actual_tail.py`, `derive_actual_amplitude.py` | all three — **but only if card N2 yields a price series** |
| Multi-year set | `scripts/audit_keepers.py:152` `_MULTI_YEAR_ISOS` (currently `{CAISO, PJM, NEISO, NYISO, MISO, SPP}`) | add NWPP (rule 16 `[R-ALLYEARS]`) |
| Memory classes | `scripts/run_isos_concurrent.py:119` `_ISO_MEMORY_CLASSES` | add NWPP (KeyError otherwise) — see the default in §3 |
| Solve workflow dropdown | `.github/workflows/calibration-solve.yml` | add NWPP |
| Matrix | `scripts/lib/mech_matrix.py:61` `ISO_ORDER` + `:65` `ISO_EV_KEY`, `docs/codebase-site/data/mechanism-matrix.js` base `isos`, a new `mechanism-matrix/NWPP.js`, `tests/unit/config/test_mechanism_matrix_shard_migration.py` | NWPP-21, ONE commit (gate G2). **Free ev letters** measured at pin: taken are `E C P M N Q S`; SOCO's charter claims `O`. NWPP takes **`W`** (Western) — §3 default |
| Dashboard colour | `docs/codebase-site/css/shared.css:78-84` (`--iso-caiso … --iso-spp`), `js/backcast-runs.js` | **no `--iso-nwpp`** — NWPP-35 mints it |
| Data profiles | `configs/data-profiles.yaml` | **the worst token trap yet measured — see the table below** |
| Coverage sweeps | `tests/unit/config/test_iso_coverage.py` (`ALL_ISOS = sorted(_ISO_BUILDERS)`) | auto-extends — NWPP must satisfy queue cap, retirement/entry, carbon-`None`, and the **no-import-node** branch |
| ~22 seven-tuple tests | `tests/unit/model/test_capacity.py`, `test_storage.py`, `test_ccs_retrofit.py`, `tests/unit/data/test_fleet.py`, … (48 test files mention `"SPP"`) | extend, or document as deliberate exclusion |
| **Curated fleet parquet** | `data/raw/eia-860/eia860_generators.parquet` | measured: **19,725 rows, exactly 7 BAs** (`CISO ERCO ISNE MISO NYIS PJM SWPP`), **zero NWPP rows**, and its `state` list excludes ID/OR/WA. It is a curated seven-ISO artifact; NWPP must either extend it or read the raw pair. **NWPP-10 states which**, NWPP-20 implements it |

**Token trap (gate G3), measured at this pin** by testing each candidate token against every
`data/raw/` child and every split-directory child:

| Token | Verdict | Evidence |
|---|---|---|
| `ava` (Avista) | **REFUSED** | matches 10 files: `ercot-noncampd-availability.csv`, `ercot-nuclear-availability.csv`, 3 × `ercot-thermal-dam-availability*`, `nuclear-availability-{CAISO,MISO,NEISO,NYISO,PJM}.csv` — it would steal five other ISOs' files |
| `grid` (Gridforce) | **REFUSED** | matches `fleet-egrid` (a `shared` corpus) |
| `pge` (Portland General) | **REFUSED** | matches split-child `reference/pge-helms-ps-plant-2008` — CAISO's Helms pumped-storage record |
| `wpp` | **REFUSED** | matches `SWPP_fueltype.parquet`, `SWPP_region.parquet` — it would steal SPP's files |
| `nwpp`, `bpat`, `pace`, `pacw`, `psei`, `ipco`, `nwmt`, `chpd`, `dopd`, `gcpd`, `scl`, `tpwr`, `avrn`, `wauw`, `nevp` | **clean at this pin** | zero matches among `data/raw/` children and split-children |

So NWPP's tokens are `nwpp` plus the **delimiter-bounded** forms of the four refused codes
(`_ava.`, `-ava.`, `/ava/`, `avrn`, …) exactly as SPP's `spp` trap was solved — and **NWPP-20 pins
the trap with a unit test**, re-measuring at its own base sha (a new `data/raw` child could be added
between this pin and W2).

### 2.4 Host reachability, probed 2026-09-13 from this session

Re-probed at this desk's own pin; every row below is this session's result, not a carried-forward one.

| Host | Result | Consequence |
|---|---|---|
| `api.epa.gov` CAMPD bulk, `emissions/hourly/state/emissions-hourly-2023-or.csv` | **206 on a range request**, anonymous, no key | ID/OR/UT/WA(/CO) CEMS are **session-fetchable**; ~187 MB per state-year |
| `oasis.caiso.com/oasisapi/SingleZip` — `ATL_APNODE` | **200, 29,406-byte zip → 2,330-row CSV** | the apnode catalogue; this is what makes §2.6 measurable rather than speculative |
| `oasis.caiso.com/oasisapi/SingleZip` — `PRC_RTPD_LMP` | **200, 4,817-byte zip → 481-row CSV of real 15-minute LMPs** | **WEIM prices for this footprint's BAs are anonymously fetchable.** §2.6 |
| `www.eia.gov/electricity/wholesale/` + `xls/archive/ice_electric-<yr>final.xlsx` | **200**; the 2023 workbook parses (1,326 rows × 11 cols) | the **Mid C** traded index, §2.6 |
| `transmission.bpa.gov/Business/Operations/Wind/baltwg.txt` | **206** | BPA's own balancing-authority total wind/load/generation feed |
| `westernpowerpool.org` | **200, 66,579 bytes** | WPP/WRAP public documents (card N7) |
| `www.wecc.org` | **200, 50,988 bytes** | the WECC path-rating catalogue route (card N5) |
| `s3.us-west-2.amazonaws.com/pudl.catalyst.coop/nightly/out_ferc714__hourly_planning_area_demand.parquet` | **200, 339,150,766 bytes** | PUDL's FERC-714 ETL — **a cross-check on §2.5, not the spine**, because §2.5 is already on disk |
| `www.ferc.gov` static host | **403** | FERC's own host refuses this egress (unchanged from the handed probe) |
| `www.oatioasis.com` CONNECT tunnel | **502** (handed; not re-probed — no NWPP item depends on it) | OATI OASIS is not a route from here |
| `EIA_API_KEY` | **unset in this container; no `.env`** | any `api.eia.gov` v2 row needs a session that carries the key — **but see §2.5: the load spine does not need one** |

### 2.5 The zonal-load spine is ALREADY ON DISK — this corrects the premise this desk was handed

The desk was handed: *"EIA-930 hourly parquets on disk: CISO ERCO FLA ISNE MISO NYIS PJM SOCO SWPP.
**NOT ONE NWPP BA.** Every one must be fetched."* **The first half is true; the conclusion is not.**

`ls data/raw/eia-930-hourly/` confirms the derived per-BA files cover only those nine. But those files
are *built from* `data/raw/eia-930/EIA930_BALANCE_<yr>_<half>.parquet`, which **are committed for
2019-01 → 2026-06** and carry **every** EIA-930 balancing authority. Measured:

```
EIA930_BALANCE_2023_Jan_Jun.parquet : 269,278 rows × 44 cols, 62 balancing authorities
NWPP BAs PRESENT : all 17 (BPAT PACE PACW PGE PSEI AVA IPCO NWMT CHPD DOPD GCPD SCL TPWR AVRN GRID WAUW NEVP)
NWPP BAs MISSING : none
Columns include   : Demand (MW), Net Generation (MW), Total Interchange (MW), Sum(Valid DIBAs) (MW),
                    Demand (MW) (Adjusted), Local Time at End of Hour, UTC Time at End of Hour
```

**Consequences, all of which make this program cheaper than SOCO's:**

- The per-BA load spine needs **no fetch, no `EIA_API_KEY`, and no sub-BA product**. It is a *derive*
  from committed bytes. (The handed fact that no NWPP BA has EIA-930 **sub-BAs** is correct and
  remains true — it simply does not matter here, because in a multi-BA pool **each BA is itself the
  zone-candidate granularity** and EIA-930 publishes it directly.)
- The corollary is the hard constraint behind card **N5**: since there are no sub-BAs, **a zone may
  not split a BA.** Every zone is a whole-BA group. BPAT alone is 20.3 % of footprint load and cannot
  be divided on this data.

**Measured 2023–2025 over the 17 BAs** (394,424 non-null demand hours; 8,751 / 8,784 / 8,760 hours
per BA per year):

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| Footprint demand | **283.97 TWh** | **291.56 TWh** | **294.86 TWh** |
| Footprint net generation | 277.30 TWh | 288.40 TWh | 300.05 TWh |
| Coincident peak, **after the defect screen below** | **49,290 MW** | **52,564 MW** | **50,953 MW** |
| Load factor | 0.658 | 0.631 | 0.657 |

**Load share by BA (2024, % of footprint demand)** — the input card N5's grouping is built from:

| BA | % | BA | % | BA | % |
|---|---:|---|---:|---|---:|
| BPAT | **20.26** | IPCO | 6.43 | DOPD | 0.82 |
| PACE | **18.10** | AVA | 4.44 | CHPD | 0.68 |
| NEVP | **14.11** | NWMT | 4.18 | WAUW | 0.28 |
| PSEI | 8.53 | SCL | 3.23 | **AVRN** | **0.00** |
| PGE | 7.79 | GCPD | 2.29 | **GRID** | **0.00** |
| PACW | 7.30 | TPWR | 1.56 | | |

**AVRN and GRID are generation-only balancing authorities.** Their `Demand (MW)` is null in **all
26,295 hours** of 2023–2025. They hold 3,538.1 MW of generation (AVRN 2,848.7 wind/solar; GRID 689.4
— the second Hermiston plant) and no load. This is structure, not a defect: they are **in the
footprint on the supply side and are not zone candidates on the load side**, and card N5's grouping
must say where their generation lands.

**Data defects, measured, not assumed.** A median-ratio screen (|D| > 5 × that BA's own median, or
D < 0) flags **30 hours out of 394,424**: AVA 10 (worst **810,948 MW** at 2025-10-12 10:00 UTC, and
**−58,286 MW** at 2024-01-05 16:00), NWMT 11 (worst 100,285), NEVP 6 (six hours ≈ 67–70 GW against a
~9 GW true peak), PACE 1 (65,826 at 2023-08-07 19:00), SCL 2 (worst −54,511). Unscreened, these
inflate the 2025 coincident peak to **835,464 MW**. **The `Demand (MW) (Adjusted)` column already
carries the screened series** — it reproduces the cleaned peaks above to the MW. NWPP-10 confirms
that and states which column every downstream series reads; nothing is padded or interpolated.

### 2.6 THE PRICE PROBLEM — there is no NWPP LMP, but unlike SOCO there IS a measured market price

This is the program's load-bearing decision and it is card **N2**, served at sitting #1.

Three of the rubric's four **load-bearing** criteria are price criteria —
`scripts/calibration_verdict.py::CRITERIA` carries `price_mean` (C3a) and `price_shape` (C3b) at
`TIER_LOAD` and `price_tail` (C3c) at `TIER_SUPPORT`, against `TIER_LOAD` `fuelmix` (C1) and `sysvol`
(C2). Every one scores the model's LP duals against a committed
`_validation-source/actual_lmp_hourly_<ISO>.parquet`.

**The Northwest Power Pool publishes no locational marginal price.** There is no pool-wide day-ahead
market and no pool clearing price in 2023–2025; the footprint's utilities are largely vertically
integrated and dispatch against IRPs and bilateral contracts. But — and this is where NWPP differs
sharply from SOCO — **two genuinely measured public price sources cover it**, and both were pulled in
this session rather than asserted:

**(a) CAISO WEIM/EIM prices, via CAISO OASIS — anonymous, and they return real numbers.**
The `ATL_APNODE` catalogue (2,330 rows) carries **212 nodes of type `EIMT`** (EIM Transfer),
distributed across exactly this footprint's balancing authorities:

```
AZPS 25 · BPAT 23 · SRP 22 · PACW 18 · TEPC 14 · IPCO 13 · NWMT 12 · AVA 12 · PGE 11 · PACE 11
SCL 10 · PSEI 10 · NEVP 10 · LADWP 7 · PNM 5 · TPWR 4 · BCHA 2 · BANC 2 · TIDC 1
```

and three `CASP` nodes `CGAP_{DOPD,CHPD,GCPD}_MIDC`. A live pull of
`PRC_RTPD_LMP` for `PACW_BPAT.PSEI-APND`, 2023-07-15, returned a **481-row CSV of 15-minute LMPs**
(first interval **$63.9213/MWh**). So an hourly price series for this footprint's BAs is
**constructible from measured market clearing prices, fetched anonymously.**

**What it is NOT, stated here so no lane overstates it:** WEIM is a **15-minute imbalance** market.
It clears the *deviation* between a BAA's bilateral/self-schedule position and real-time need — not
the footprint's total energy. It had **no day-ahead counterpart** in 2023–2025 (EDAM post-dates the
window). And an `EIMT` node prices a **transfer between BAAs**, which is not the same object as a
BAA-internal load price. **How much of the footprint's volume WEIM actually clears is not measured
here and is `pending NWPP-13`** — it is the single number that decides whether option (a) is a
rule-14 `[R-ACCURATE]` *reconciled* benchmark or a misaligned one, and the desk will not guess it.

**(b) The Mid-Columbia ("Mid-C") traded index, via EIA's ICE workbooks — measured this session.**
`ice_electric-2023final.xlsx` carries a **`Mid C Peak`** hub with, per trade date, high/low/**weighted
average** price $/MWh, **daily volume MWh, number of trades and number of counterparties**. Measured
for 2023: **244 trade dates**, span 2022-12-28 → 2023-12-22, **4,748,000 MWh** total traded volume,
5–72 trades/day, 5–18 counterparties/day. It is a real, volume-stamped, arm's-length wholesale price
for the Pacific Northwest.

**Its limitation is decisive and must not be wished away: it is PEAK-ONLY and DAILY.** The workbook
carries `Mid C Peak` and **no off-peak row**, and one price per trade date. A daily peak-only series
**cannot score C3b (hourly price duration/shape) or C3c (hourly price tail) at all**, and can anchor
C3a only on a peak-hour subset of a business-day subset.

**What the desk refuses in advance, in writing, so no lane proposes it (gate G17):** substituting a
**neighbouring market's hub** for this footprint's own price — CAISO SP15/NP15, Palo Verde, or an
"adjusted" CAISO series — is exactly the load proxy rule 13 `[R-MEASURED]` forbids. The dispatch
validated would not be the dispatch forecast. **Palo Verde and SP15 are in the same ICE workbook and
are therefore one column away from any lane that opens it; that proximity is the hazard, and this
paragraph is the refusal.** Mid-C is *this footprint's own* traded hub and is not caught by this
refusal; a CAISO hub is.

### 2.7 What the repo's hydro machinery can and cannot express

Measured by reading the code, because card N3 cannot be served from an impression.

**Exists today** (`src/market_sim/data/hydro.py`, `model/lp/rows.py`, `model/lp/__init__.py`):

- `load_hydro_budget(iso, year)` builds, per conventional-hydro generator (prime mover `HY`, fuel
  `WAT`; **pumped storage `PS` excluded by design**), a **monthly energy budget** from EIA-923
  monthly net generation, plus a power envelope (max MW = nameplate, min MW an optional floor).
- The LP row family is `hydro_monthly_min[g,m] ≤ Σ_{t∈m} P[g,t] ≤ hydro_monthly_energy[g,m]` — a
  genuine inter-temporal constraint: the LP chooses *when* within a month, not *how much*.
- `HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT` (gated `hydro_budget_period_by_instrument`) lets a **named
  plant** carry a shorter budget period justified by a **published instrument**. Measured content at
  this pin: **NYISO only, two plants** — Robert Moses Niagara (24 h, treaty/INBC) and Robert Moses
  St. Lawrence (168 h, IJC ponding directive).
- Water-year scenario lever `hydro_year` ∈ {dry, normal, wet} × `HYDRO_YEAR_MULTIPLIER`; a
  measured `hydro_dispatch_envelope`; and three default-off CAISO-derived gates
  (`hydro_min_flow_floor`, `hydro_ror_split`, `hydro_budget_nameplate_aware`).

**Does NOT exist, and a first NWPP keeper therefore cannot express it:**

1. **Hydraulic coupling down a river.** Each generator's budget is independent. On the Columbia
   mainstem, water released at Grand Coulee passes through Chief Joseph, Wells, Rocky Reach, Rock
   Island, Wanapum, Priest Rapids, McNary, John Day, The Dalles and Bonneville in turn — **eight of
   the footprint's ten largest hydro plants are one hydraulic chain.** The model will treat them as
   ten independent monthly budgets that happen to correlate.
2. **Sub-monthly reservoir carryover and refill.** The budget period is a month (or a per-plant
   instrument period). Seasonal drawdown/refill and the April–August freshet are expressible only as
   twelve monthly totals.
3. **Flood-control rule curves and fish-spill obligations.** A spill is water routed *past* the
   turbine: it reduces available energy without being a min-generation floor, and there is no object
   for it. A min-flow floor is the nearest expressible thing and it is not the same constraint.
4. **BPA's cost-based federal rates.** BPA sells at embedded cost under the Northwest Power Act, not
   at marginal cost. The LP prices hydro at its marginal cost (≈ 0 + VOM). Card N3 must say what
   that means for a price benchmark built on WEIM.

**So what would a first NWPP keeper actually be measuring?** With 36.3 % of nameplate under a
monthly-budget approximation whose largest plants are hydraulically coupled and not modelled as such,
C1 (fuel-mix) is mostly a test of whether the **monthly hydro budgets are right**, and C4 (hourly
dispatch correlation) is mostly a test of whether the **within-month hydro shaping** is right.
Neither is a bad thing to measure — but it should be *stated* at the gate, not discovered in W4.
That is why hydro is card **N3** and not a lane detail.

---

## 3. The owner cards N1–N10

Recommendation first and labelled; rulings appended to each row **verbatim** and numbered in the
ledger §2. **N1, N2 and N3 are served at sitting #1** — N1 because every later measurement is scoped
by the footprint, N2 because the scoring design gates what W1 even fetches, N3 because it decides
whether a first keeper is worth solving at all. N4–N8 and N10 are served at **sitting #2**, after
W1's evidence lands (the SPP precedent: *"let the Phase-0 audit decide the topology"*).

| Card | Question | Recommendation to present | Evidence it needs | Ruling |
|---|---|---|---|---|
| **N1** THE REGION | NWPP is a **pool of 17 BAs**, not a BA. What is the registry key, and which BAs are in the footprint? | **Key `NWPP`.** Footprint: **all 17 candidate BAs** = 940 plants / 98,738.1 MW / 294.86 TWh (2025). Rationale, measured: Hermiston forces `PACW`; `PACE` and `PACW` are one company (PacifiCorp) split across two BAs and a boundary between them is a corporate artifact, not a transmission one; `AVRN` and `GRID` serve zero load but hold 3,538.1 MW that physically serves the footprint, so they are **in on the supply side and are not zones** (§2.5). **The one genuinely arguable cut is `NEVP`** — 15,656.9 MW and 14.11 % of load, desert-Southwest thermal rather than Northwest hydro, and a WEIM participant since 2015. Dropping it is defensible; the desk recommends **keeping it**, because excising it creates a 14 %-of-load internal seam this model would then have to price with no price for it, and because WPP membership is the stated definition of the region. **Canada (BC Hydro, AESO) is OUT**: it is in the real pool and entirely outside EIA-930, so it can only ever be an exogenous seam — stated now so no lane re-opens it | §2.1, §2.5 | **RULED 2026-09-13 (sitting #1): ALL 17 BAs** — the desk's recommendation, accepted as presented. Footprint = BPAT PACE PACW PGE PSEI AVA IPCO NWMT CHPD DOPD GCPD SCL TPWR AVRN GRID WAUW NEVP; key `NWPP`; NEVP **in**; Canada **out**; AVRN and GRID supply-side members, not zone candidates |
| **N2** THE PRICE BENCHMARK | There is no NWPP LMP. What do C3a/C3b/C3c score against, and what may an NWPP run be *called*? | **BOTH, as one card: (a) charter NWPP-13 to build a WEIM-derived footprint hourly series with a PRE-REGISTERED STOP GATE, AND (b) rule now on what a run reads if (a) fails.** (a) is buildable — §2.6 pulled real 15-min LMPs anonymously — and its gate must fix, **before any data is read**: the node set, the BAA-weighting, hour aggregation from 15-min, the **minimum WEIM share of footprint volume** below which the series is declared misaligned, and the **reconciliation against the independent Mid-C traded index** with a stated numeric tolerance. **Mid-C is the ANCHOR, never the benchmark** — it is daily and peak-only (§2.6), so it can cross-check a level and can score nothing. For (b), the desk's proposal is a determination that names its own basis (e.g. `PHYSICALLY CALIBRATED — price scored on imbalance prices only`), never a bare `CALIBRATED`, with the misalignment on the determination basis at full magnitude. **Refuse a neighbouring-hub proxy outright** (§2.6 gate G17). ⚠ **COORDINATE, do not merge:** the SOCO program's card **S2** is the same rubric question in a harder form (SOCO has *no* price at all), and that desk's ledger §3 R-b already routes *"the owner should rule the rubric question ONCE, for both"*. This desk **surfaces that** and rules only for NWPP | §2.6; NWPP-13's gate table; the WEIM volume share (`pending NWPP-13`) | **RULED 2026-09-13 (sitting #1): BOTH (a) AND (b)** — the desk's recommendation, accepted as presented. (a) NWPP-13 is chartered to build the WEIM-derived hourly series under a STOP gate pre-registered before any data is read; (b) if the gate fails, a run reads a determination naming its own basis, **never a bare `CALIBRATED`**, with the price gap on the determination basis at full magnitude. The neighbouring-hub substitution stays refused (gate G17). The joint-sitting-with-SOCO option was offered and **not** taken, so R-c stays open and surfaced |
| **N3** HYDRO | 35,799.5 MW (36.3 %) of conventional hydro, eight ≥1 GW plants in one hydraulic chain, on machinery that models independent monthly budgets (§2.7) | **Proceed to a first keeper on the existing monthly-budget machinery, with the four unexpressible constraints (§2.7) DECLARED on the keeper's determination basis and the largest of them pre-declared as lever NWPP-54 (hydraulic coupling of the Columbia mainstem).** Rationale under rule 1 `[R-STRUCT]`: the monthly budget is a *real* structure, not a fitted one, and a structurally-incomplete model that says so is admissible; what would **not** be admissible is closing the resulting residual with a tuned hydro adder. The desk states plainly what the owner is buying: **a first NWPP keeper's C1 is substantially a test of the hydro budgets and its C4 substantially a test of within-month hydro shaping.** The alternative the owner may prefer — build cascade coupling *before* the first keeper — is a materially larger program and is offered as the second option, not hidden | §2.7; NWPP-11's EIA-923 monthly hydro by plant | **RULED 2026-09-13 (sitting #1): BUILD CASCADE COUPLING FIRST — AGAINST the desk's recommendation.** The owner selected the second option: hydraulic coupling of the Columbia mainstem is built **before** any first keeper, not pre-declared as lever NWPP-54. The desk had recommended proceeding on the monthly-budget machinery with the gap declared; the owner ruled that the first NWPP number must mean more than a test of monthly hydro budgets. **Consequences are structural and are implemented in §4/§5/§7 rather than noted**: a new W3b wave, a new `[FABLE]` lane **NWPP-36**, and an amendment to gate G8 (see there — the new field rides `_CACHE_KEY_OPTIONAL_FIELDS`, so no existing keeper's key moves). Lever NWPP-54 is **retired from the W5 queue**, its content promoted into NWPP-36 |
| **N11** THE SCORER BRANCH *(raised r#3, 2026-09-13)* | Card N2 limb (b) authorized a determination naming its own basis. `scripts/calibration_verdict.py` carries **no branch able to express it**, and NWPP-13 has since read **NO**, so NWPP has no admissible price series and a solved keeper would be **unscoreable**. Plan §1 forbade this desk from chartering rubric changes — written when N2 was unruled. Who builds it? | **Charter NWPP-22 `[FABLE]` from this desk**, narrowly: ONE added branch, a data-driven predicate, no existing criterion touched, **byte-identical verdicts over every pre-existing keeper** as the exit. It is the sole thing standing between a solved NWPP keeper and a scored one, and this desk controls the schedule | `FINDING-nwpp-13` §0 (the NO); the seven keepers' verdicts | **RULED 2026-09-13 (r#3): SEND IT NOW.** The owner directed the desk to charter and issue it immediately rather than defer or route it. Plan §1's rubric prohibition is **carved for this one lane only**; gate **G25** holds it to the byte-identity exit |
| **N4** THE CAISO SEAM AND THE DOUBLE-COUNT | CAISO is already registered **with a `WECC_import` node whose counterparty is physically this footprint** | **Served measured EIA-930 `Total interchange` on NWPP's side** for the first keeper (`_SCALAR_INTERCHANGE_ISOS` += NWPP — the PJM/NYISO/NEISO/SPP precedent, playbook §8.2, rule-13 admissible), priced `NeighborInterface`s registered **default-off**. **The exposure, measured and stated rather than implied:** `iso_configs.py:533,570,573` give CAISO a `WECC_import` zone fed by `TransferLink(WECC_import→NP15, 4,800 MW)` and `(WECC_import→SP15_rest, 10,623 MW)` under a 7,500 MW simultaneous cap, and `model/interchange/caiso.py:443` names its firm tranches **`{"PNW_hydro_base", "DSW_solar_PV"}`** — *"PNW hydro"* is this footprint, by name, priced as a Tier-3 contract-cost proxy under CLAUDE.md rule 14's misalignment exception. Registering NWPP therefore puts the same physical energy on both sides of a seam, represented two different ways. **Rule 25 `[R-ISO-SCOPE]` forbids this desk from touching how CAISO prices its side, and it will not.** The CAISO-side question is **ROUTED to the CAISO lane** (ledger §3) and stays visible | §2.1; NWPP-11 DIBA duration curves |**RULED 2026-09-14 (sitting #4): SERVED MEASURED INTERCHANGE, PRICED LINKS DEFAULT-OFF** — the desk's recommendation as presented. `_SCALAR_INTERCHANGE_ISOS += NWPP` (the PJM/NYISO/NEISO/SPP precedent, rule-13 admissible); `NeighborInterface`s registered but default-OFF, because NWPP-13 read NO and a priced seam would be unvalidatable in the first keeper. **Binding caveat measured by NWPP-10 §3.1: BPAT's balance identity FAILS structurally** — mean residual **−3,206 MW**, **81.5 % of hours** miss by > 1 MW, because BPA wheels energy it neither generates nor serves. The derive must handle that, never assume `Demand = NetGen − TotalInterchange`. R-a (the CAISO-side double-count) is untouched and stays routed |
| **N5** TOPOLOGY | Zones are whole-BA groups (§2.5: no sub-BAs, so **a zone may not split a BA** — BPAT alone is 20.26 % of load) | **Five zones**, grouped on transmission geography, with the 2024 load shares measured in §2.5: **`NWPP-NW`** (BPAT · PSEI · SCL · TPWR · CHPD · DOPD · GCPD, + AVRN generation) **37.37 %** · **`NWPP-OR`** (PGE · PACW, + GRID generation) **15.09 %** · **`NWPP-INLAND`** (IPCO · AVA · NWMT · WAUW) **15.33 %** · **`NWPP-EAST`** (PACE) **18.10 %** · **`NWPP-SNV`** (NEVP) **14.11 %**. TTCs from the **WECC published path ratings** where a boundary maps to a rated path (Path 14 Idaho–Northwest, Path 20 "Path C", Path 35 TOT 2C, Path 27 IPP DC) — **a genuinely better TTC story than SPP got**, which registered a 48,700 MW placeholder. Where no rating maps (notably `NWPP-NW ↔ NWPP-OR`, which is a dense multi-point interconnection rather than a rated path), register **Tier-3, documented, non-binding** exactly as SPP-20 and SOCO card S3 do, and pre-declare the derive as lever NWPP-55. **Note plainly:** a WEIM-derived price (card N2) *is* locational, so unlike SOCO these zones do have a potential zonal benchmark — whether it is usable is `pending NWPP-13` | NWPP-12 WECC path ratings; §2.5 shares |**RULED 2026-09-14 (sitting #4): FIVE ZONES, AS SCOPED** — the desk's recommendation as presented. `NWPP-NW` 37.4 % · `NWPP-EAST` 18.1 % · `NWPP-INLAND` 15.3 % · `NWPP-OR` 15.1 % · `NWPP-SNV` 14.1 %. **TTC tiers, from NWPP-12's transcription of the WECC 2024 Path Rating Catalog:** EAST↔SNV **Path 35 TOT 2C 600/580 — Tier-1 candidate**; INLAND↔SNV **Path 16 Idaho–Sierra 500/360 — Tier-1 candidate**; NW↔INLAND **Tier-2** (Paths 8/6/14, aggregation documented); INLAND↔EAST **Tier-2** (Path 20 "Path C" 1,600/1,250); **NW↔OR Tier-3, documented absence** — no WECC path rates a BPAT/PSEI/SCL/TPWR/CHPD/DOPD/GCPD ↔ PGE/PACW interface and none will, because that interconnection is multi-point around Portland; **Paths 4/5/71/86/87/88 are east–west cuts, NOT BA interfaces, and must not be used as one** (Path 5 mixes BPA-internal, BPA→PGE and PGE-internal limbs in one 7,200 MW rating). Declared open, not hidden: `NWPP-INLAND` is the weakest cut (within-group 0.682 vs vs-rest 0.631) and **GCPD's placement is disputed by load correlation** (0.90 with IPCO, 0.08–0.16 with its own zone) — flagged, not moved, because load correlation is not a transmission constraint |
| **N6** TIMEZONES | The footprint spans Pacific and Mountain. The SOCO program carries this as unsolved gate G19 | **Largely CLOSED BY MEASUREMENT, and the residual is a convention choice, not a data question.** Measured this session off `EIA930_BALANCE_2024_Jan_Jun.parquet` by differencing `Local Time at End of Hour` against `UTC Time at End of Hour`: **EIA-930 assigns each BA exactly one timezone**, and the split is clean — **Mountain (UTC−7/−6 DST): `NWMT`, `PACE`, `WAUW`. Pacific (UTC−8/−7 DST): the other 14**, including `IPCO` (Idaho Power files Pacific although southern Idaho is legally Mountain — a reconciliation NWPP-10 records). So the load spine carries its own correct local time per BA and nothing needs inferring. **The decision left for the owner:** the model's canonical hour. The desk recommends **UTC as the canonical solve hour with `America/Los_Angeles` as the declared reporting zone** (the majority of load, 81.6 %), every derived series stating its zone in its SOURCES, and the three Mountain BAs' local-time columns used only for provenance. `fetch_eia930_hourly.BA_TIMEZONE` carries **no entry for any of the 17** and gains them in W1 | measured, §2.5/§2.6 |**RESOLVED BY MEASUREMENT, NOT RULED (sitting #4) — no card was needed.** NWPP-10 §2 item (6) closed it on the data: **14 Pacific / 3 Mountain** (NWMT, PACE, WAUW), stable across all three years, **all 6 DST transitions present and correctly signed**, **IPCO files Pacific** (measured: at UTC 2023-07-28 08:00 IPCO stamps 01:00, PACE 02:00) so `BA_TIMEZONE["IPCO"] = "America/Los_Angeles"`, **not** `America/Boise`. Every BA carries 26,304 unique UTC hours and exactly 3 duplicated LOCAL timestamps. **CONVENTION: UTC is the canonical hour and the only admissible join key; local time is provenance only.** Gate **G19 closed on the data side** |
| **N7** ADEQUACY | No capacity market. What is the reliability floor's requirement? | **Absent from `MARKET_DESIGN`, `_CURVE_ISOS`, `_CAPACITY_ISOS`** (→ `DEFAULT_MARKET_DESIGN`, `capacity_market=False`, the ERCOT/SPP branch). `PLANNING_RESERVE_MARGIN_BY_ISO["NWPP"]` from published sources, **cited per value and per season** — the footprint is winter-peaking in parts and summer-peaking in others and NWPP-10 measures which, per zone, off §2.5's committed hourly demand rather than asserting it. **WRAP (the Western Resource Adequacy Program) is the live construct**, and the question that decides whether it is in-window at all — *when does WRAP's first BINDING season fall relative to 2023–2025?* — is **`pending NWPP-12`, to be answered with a citation, not from memory.** If binding post-dates the window (the desk's expectation, explicitly unverified), WRAP is a **forecast-side** object and the backcast floor rests on the participants' own IRP reserve margins | NWPP-12 WRAP/IRP transcription; §2.5 seasonal peak measurement |**RULED 2026-09-14 (sitting #4): ONE SCALAR NOW, DECLARED; PER-ZONE SEASONAL AS A FORECAST LEVER** — the desk's recommendation as presented. One `PLANNING_RESERVE_MARGIN_BY_ISO["NWPP"]` from the participant IRPs, tested against the footprint **coincident** peak (summer in all three years), with the two-regime mismatch **DECLARED on the determination basis at full magnitude**. **Why this is cheap rather than a fudge:** capacity evolution is forecast-mode, so the reliability floor is largely inert in a 2023–2025 backcast, and the alternative changes a dict all nine registered regions read to fix something that binds in no scored year. **The mismatch, measured by NWPP-10 §1.4 and not to be softened in the declaration:** 8 winter-peaking BAs, 6 summer, 1 flipping (PACW); `NWPP-NW` peaks WINTER all three years (0.86/0.80/0.82) while `NWPP-SNV` peaks SUMMER at **1.95/2.06/1.87×** its own winter load; `NWPP-INLAND` mixes both regimes *inside one zone*, so even a per-zone seasonal PRM would average two regimes there. **WRAP is a FORECAST-SIDE OBJECT ONLY** — NWPP-12 §0.2 cites WPP BPM 109 p. 4: first binding season **Winter 2027–28, from 1 November 2027**, two years past the window; no WRAP obligation binds in any scored year. Pre-declared as lever **NWPP-57** |
| **N8** CEMS SCOPE | CAMPD unit-level is present for MT, NV, WY, CA and **absent for ID, OR, UT, WA** (and CO) — measured §2.4 | **Fetch ID, OR, UT, WA × 2023–2026** (~187 MB/state-year anonymous, probed 206 this session); **CO is one 7.5 MW solar row in PACE and is skipped**, with the skip documented. **Say the quiet part at the gate:** CEMS covers combustion units only, so on a fleet that is 36.3 % hydro + 24.9 % wind/solar + 1.2 % nuclear, **CAMPD reaches at most ~32 % of nameplate.** The per-plant binning path (`use_campd_bins`) is therefore far less of the fleet here than in ERCOT or SPP, and the outage/tranche artifacts it feeds cover correspondingly less. That is a scoping fact for W3, not a reason to skip the fetch | §2.4 |**RULED 2026-09-14 (sitting #4): LEGACY HEAT-RATE BINS FOR THE FIRST KEEPER; CAMPD PER-PLANT AS A LEVER** — the desk's recommendation as presented, so `use_campd_bins=False` and the §3 recorded default `per_plant=True` is **superseded for the memory class**. Measured by NWPP-10 §2 item (8): CAMPD reaches **30.98 %** of footprint nameplate after NWPP-11 (32.63 % upper bound) and **41.8–43.6 %** of EIA-923 energy, proxy validated at **100 % precision / 94.9 % MW recall**. Two reasons beyond precedent: **36.3 % of this footprint is hydro that CEMS can never cover**, so per-plant binning cannot reach most of the fleet; and gate **G21** is real — 939 plants × 1,930 generators × 5 zones is the largest per-plant LP in the repo and nothing is yet known about its solve behaviour. The CEMS data is **not wasted** — outages, emission rates and commitment evidence all still read it. Pre-declared as a W5 lever |
| **N9** W6 ROUTING | who charters forecast-program entry | **ROUTE to the capx director** with a card once a keeper exists; this desk never writes `program-status.json` / `ff-verdicts.json` / `GOLDEN_ISOS` | — | — |
| **N10** FIRST-SOLVE SCREEN (rule 29 `[R-SCREEN]`) | There is no NWPP keeper, so 29(b) "the keeper is the control" is vacuous | **Control = none.** The first full 2023–2025 bundle **is** the baseline and becomes every later NWPP lane's 29(b) control. **Screen year** = the year whose **hydro energy deviates most from the 2023–2025 mean** — a zero-LP, residual-blind statistic computed from committed EIA-923/EIA-930 `NG: WAT`, chosen because hydro is the mechanism under test (card N3) and rule 29 requires the screen year to be where the mechanism's own footprint is largest, **never** where the residual is largest. STOP gate **structural only**: monthly hydro energy lands within its budget; the inter-zone links bind in the measured direction and season; fuel mix within an order of magnitude of EIA-923; no unserved energy or negative-price absurdities. **Never "did C3a improve."** Screen bundle is **gitignored, never `rm`'d** (rule 31 `[R-RETAIN]`) | NWPP-11 monthly hydro; §2.5 | — |

**Defaults recorded here so no lane re-litigates them (no card):** `_MULTI_YEAR_ISOS` gains NWPP in
W2 (rule 16 — a single-year NWPP keeper is refused from day one); **`ISO_EV_KEY["NWPP"] = "W"`**
(`E C P M N Q S` are taken at this pin and SOCO's charter claims `O`); the memory class is registered
`per_plant=True, co_opt=False, peak_gb=<measured in NWPP-40>` — **and NWPP-40's PRECOMMIT must treat
this as a real risk, not a formality: at 940 plants / 1,932 generators × 5 zones this is the largest
per-plant LP in the repo** (SPP is 715 / 1,646 at 2 zones and was estimated at ERCOT's 6.0 GB), so
CLAUDE.md rule 32(c)(8)'s container preflight and the reported `memory peak:` line are load-bearing;
**no import node** (NWPP's seams are served schedules, so neither `IMPORT_TRANCHES` nor `IMPORT_ZONE`
gets an NWPP key — gate G7); offer-curve bands stay **1.0** (gate G5).

---

## 4. Wave graph

```
W1  Phase 0/1 — zero-LP, ADDITIVE files only (parallel; disjoint: docs / data+fetch / documents)
    ┌────────────────────────┐ ┌──────────────────────────┐ ┌────────────────────────────┐
    │ NWPP-10 data audit +   │ │ NWPP-11 CAMPD ID/OR/UT/WA│ │ NWPP-12 WECC paths + WRAP  │
    │ registry-values table  │ │ + per-BA 930 DERIVE +    │ │ + IRPs + NRC + fuel prices │
    │ + the TRE defect       │ │ interchange + EIA-923    │ │                            │
    │ [OPUS] shared          │ │ hydro   [OPUS] shared    │ │ [OPUS] shared              │
    └───────────┬────────────┘ └────────────┬─────────────┘ └─────────────┬──────────────┘
                │        ┌──────────────────┴───────────────────┐         │
                │        │ NWPP-13 the WEIM price index [FABLE] │         │
                │        │  (card N2 option a — STOP-gated)     │         │
                │        └──────────────────┬───────────────────┘         │
                └───────────────────┬───────┴─────────────────────────────┘
                                    ▼   DESK SITTING #2 — cards N4…N8, N10 served with W1 evidence
W1c THE SCORER BRANCH — owner ruling N11, issuable NOW, file-disjoint from every other lane
    ┌──────────────────────────────────────────────────────────────────────────┐
    │ NWPP-22 the determination class card N2 limb (b) ruled  [FABLE]          │
    │   ONE added branch in scripts/calibration_verdict.py; predicate = the    │
    │   ABSENCE of an admissible hourly price series; never a PASS, never an   │
    │   upgrade; gap reported at full magnitude                                │
    │   GATE: byte-identical verdicts over ALL pre-existing keepers (G25)      │
    │   WHY NOW: NWPP-13 read NO (2026-09-13), so limb (b) is LIVE and this    │
    │   branch is the ONLY route to any NWPP determination                     │
    └──────────────────────────────────────────────────────────────────────────┘
                       ▼   (independent of W2/W3; NWPP-40 cannot score without it)
W2  Registration — THE PIN FLIP (one PR)          ∥  matrix shard
    ┌─────────────────────────────────────────┐   ┌────────────────────────────┐
    │ NWPP-20 register + BA-keyed zone map +  │   │ NWPP-21 matrix shard       │
    │ every registry + profile token [FABLE]  │   │ + lever queue + colour     │
    └──────────────────┬──────────────────────┘   └────────────────────────────┘
                       ▼   (every W3 derive calls get_iso_config("NWPP") — W3 is gated by W2 itself)
W3  Phase 2 derivation (parallel; each lane owns only its outputs)   ∥  site/docs wiring
    NWPP-30 outages + tranches │ NWPP-31 benchmarks │ NWPP-32 HYDRO BUDGET [FABLE]
    NWPP-33 zonal shares + VRE shape + gas hub │ NWPP-34 seam derive │ NWPP-35 site JS/CSS/docs
                       ▼
W3b THE CASCADE-COUPLING BUILD — inserted by owner ruling N3, and W4 does not start without it
    ┌──────────────────────────────────────────────────────────────────────────┐
    │ NWPP-36 Columbia mainstem hydraulic coupling  [FABLE]                    │
    │   a new default-OFF ScenarioConfig field on _CACHE_KEY_OPTIONAL_FIELDS   │
    │   (the nyiso-220 hydro precedent) + its LP row family + its matrix row    │
    │   GATE: every existing keeper's cache_key() byte-identical (G8 amended)   │
    └──────────────────────────────────┬───────────────────────────────────────┘
                       ▼
W4  First-ever solve → FIRST KEEPER → dashboard flip (ONE lane, ONE shard, ONE span — rule 32)
    NWPP-40  [FABLE]  --year 2023 2024 2025, one bundle, one registration, coupling ARMED
                       ▼
W5  Lever queue (pre-declared): NWPP-55 WECC path TTC derive · NWPP-56 priced seams (incl. the
    CAISO side, only if that lane rules) · NWPP-57 WRAP adequacy · NWPP-58 zone refinement ·
    NWPP-59 retirement sector gate (§2.1 fact 4)
    (NWPP-54 Columbia hydraulic coupling is RETIRED from this queue — owner ruling N3 promoted it
     into W3b/NWPP-36, ahead of the first keeper)
W6  Forecast-program entry — ROUTED to the capx director (card N9)
```

---

## 5. Lane table

Column key — **Model**: `[FABLE]` = adjudication (topology / market-object design, the pin flip, the
price-benchmark construction, the hydro representation, the first-keeper determination); `[OPUS]` =
execution of a committed recipe (census, fetch, frozen derives, shard emission, site wiring,
pre-declared solves). **Sonnet never** (rule 27 `[R-PUSH]`). **Profile** = the `DATA PROFILE:` line
(`nwpp` exists only after NWPP-20 lands; before that, `shared`).

| Lane | Model · why | Profile | Owns | Zero-LP gate | Exit check |
|---|---|---|---|---|---|
| **NWPP-10** audit | OPUS · census against the MISO/SPP/SOCO audit recipe; recommends, never decides | shared | `docs/multi-iso/nwpp-data-audit.md` (NEW); `00-iso-addition-protocol.md` §0 row + §3; `01-data-needs-and-upload-manifest.md` NWPP rows | — | fleet census by the 17 BAs vs §2.1; **the TRE/TX defect adjudicated with its rule stated**; the `eia860_generators.parquet` seven-ISO limitation resolved; seasonal peak per candidate zone measured off §2.5; **registry-values table with a citation per value**; the `Demand (MW) (Adjusted)` convention established |
| **NWPP-11** data | OPUS · reproducible fetches + one derive through existing scripts | shared | `campd-unit-level/{ID,OR,UT,WA}_{2023..2026}.parquet` + README/SHA256SUMS rows; `eia-930-hourly/<BA> hourly.parquet` × 17 (**DERIVED from committed BALANCE files, not fetched**); `eia-930-interchange/`; ADDITIVE `BA_TIMEZONE` keys; EIA-923 monthly hydro extract | — | 16 CEMS files schema-identical to a sibling; 17 per-BA hourly files reconciled against the BALANCE source **to the MWh**; DIBA duration curves per counterparty per year; per-plant monthly hydro for all 288 plants |
| **NWPP-12** documents | OPUS · fetch + transcription against a manifest | shared | `data/raw/nwpp-planning/` (NEW: WECC path ratings, WRAP filings, PacifiCorp/PGE/Idaho Power/Avista/NorthWestern/Puget/NV Energy IRPs, NRC status for Columbia); `gas-prices/`, `coal-prices/` NWPP rows | — | every transcribed value carries URL + page/table; **the WRAP binding-season date answered with a citation** (card N7); a 403/404 is recorded with its exact URL and STOPS that item — no value from memory |
| **NWPP-13** the price index | **FABLE** · card N2 option (a); *construction of a benchmark*, the most adjudication-heavy act in the program | shared | `data/raw/nwpp-weim/` (NEW — **the desk RESOLVED the charter's conditional at r#2: `caiso-weim` is swept into the CAISO profile, measured**); `scripts/data/build_nwpp_weim_price_index.py` (NEW); `_validation-source/actual_lmp_hourly_NWPP.parquet` **only if the STOP gate passes** | **STOP gate, pre-registered in its PRECOMMIT before any data is read** | either a committed series with its reconciliation table, **or** a documented NO — both are successful outcomes |
| **NWPP-20** registration | **FABLE** · the pin flip | shared→nwpp | every §2.3 row, ONE PR | full test suite + `solve_surface_register.py --diff` zero moved rows | `get_iso_config("NWPP").validate_topology()`; every keeper's `cache_key()` byte-identical |
| **NWPP-21** matrix shard | OPUS | code | `mechanism-matrix/NWPP.js`, base `isos`, `ISO_ORDER`/`ISO_EV_KEY`, html tag, shard-migration test | `scripts/check_mechanism_matrix.py` | ONE commit (gate G2) |
| **NWPP-30/31/33/34** derivation | OPUS · frozen derives | nwpp | outages+tranches · benchmarks · zonal shares/VRE shape/gas hub · seam derive | non-NWPP diff = ∅ (gate G9) | per-lane FINDING |
| **NWPP-32** hydro budget | **FABLE** · card N3 applied; the structural core of the program | nwpp | the hydro budget + envelope artifacts for 288 plants; `HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT["NWPP"]` entries **only where a published instrument justifies one** (the NYISO precedent, §2.7) | budget reconciles to EIA-923 annual by plant | the four §2.7 unexpressible constraints restated with their measured magnitude |
| **NWPP-36** cascade coupling | **FABLE** · **owner ruling N3** — the structural build that now precedes the first keeper | nwpp | the hydraulic-coupling LP row family; ONE new default-OFF `ScenarioConfig` field registered on `_CACHE_KEY_OPTIONAL_FIELDS` + `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` in the same commit; its `mechanism-matrix.js` base row + one `·` cell line per foreign shard (rule 28(c)); its PRECOMMIT and FINDING | **every existing keeper's `cache_key()` byte-identical** (gate G8 as amended) + `scripts/solve_surface_register.py --diff` | the coupling arms and is byte-identical OFF; the reach table (which plants, which chain) measured, not asserted |
| **NWPP-22** the scorer branch | **FABLE** · owner ruling **N11**; the ONLY lane licensed to touch the shared scorer, and the licence is narrow | code | `scripts/calibration_verdict.py` (ONE added determination branch + its guards); a NEW `tests/scoring/` file; its PRECOMMIT + FINDING | **byte-identical verdicts over every pre-existing keeper** (gate G25) | the branch cannot fire for an ISO carrying a price series, DOES fire for one carrying none, and is never a PASS |
| **NWPP-35** site + docs | OPUS | code | site JS/CSS prose, `--iso-nwpp` colour, `docs/calibration-log/nwpp.md` header | `check_registry_payload_parity` | — |
| **NWPP-40** first solve | **FABLE** · first-keeper determination | nwpp | ONE shard, ONE `--year 2023 2024 2025` invocation, ONE bundle, registration | preconditions: NWPP-30/31/32/33 **and NWPP-36** landed | keeper registered with whatever determination it earns |

---

## 6. Fetch / upload manifest

Every row is a **fetch first**; the manual fallback fires only on a documented block (the SPP
charter's owner ruling O-3 carries over).

| # | Item | Target path | Session-fetchable? | Lane | Manual fallback |
|---|---|---|---|---|---|
| 1 | CAMPD hourly CEMS **ID, OR, UT, WA** 2023–2025 (+2026 partial) | `data/raw/campd-unit-level/<ST>_<yr>.parquet` | **YES — probed 206 anonymous, ~187 MB/state-year** (`api.epa.gov/easey/bulk-files/emissions/hourly/state/emissions-hourly-<yr>-<st>.csv`) | NWPP-11 | EPA CAMPD bulk page |
| 2 | Per-BA hourly demand/netgen/interchange × 17 BAs | `data/raw/eia-930-hourly/<BA> hourly.parquet` | **NO FETCH REQUIRED — DERIVE from committed `data/raw/eia-930/EIA930_BALANCE_*.parquet`** (§2.5). No `EIA_API_KEY` needed | NWPP-11 | n/a |
| 3 | BA-to-BA interchange detail (DIBA) 2023–2025 | `data/raw/eia-930-interchange/` | **partly on disk** — BALANCE carries `Total Interchange` and `Sum(Valid DIBAs)`; per-counterparty detail needs the INTERCHANGE product (`EIA_API_KEY` **unset in this container**) | NWPP-11 | EIA Grid Monitor interchange CSV (key-free) |
| 4 | **WEIM 15-min LMPs** for the footprint's EIMT/CASP nodes, 2023–2025 | `data/raw/nwpp-weim/` (**not** `caiso-weim` — desk r#2) | **YES — probed 200, anonymous, real prices** (`oasis.caiso.com/oasisapi/SingleZip?queryname=PRC_RTPD_LMP…`). Volume: 96 intervals/day × ~40 nodes × 1,095 days — NWPP-13 plans the paging | NWPP-13 | none needed |
| 5 | **Mid-C traded index** (the independent anchor, card N2) | `data/raw/nwpp-planning/` | **YES — probed 200**, `eia.gov/electricity/wholesale/xls/archive/ice_electric-<yr>final.xlsx`; 2023 parses, `Mid C Peak`, 244 trade dates | NWPP-13 | EIA wholesale page |
| 6 | EIA-923 monthly net generation per hydro plant (the budget source) | already committed / `data/raw/` | **on disk** — `data.hydro` reads it today for other ISOs | NWPP-11 | — |
| 7 | WECC published path ratings (Paths 8, 14, 20, 27, 35, 65/66) | `data/raw/nwpp-planning/` | likely — `wecc.org` probed 200 | NWPP-12 | owner uploads |
| 8 | WRAP program documents + **the binding-season date** | `data/raw/nwpp-planning/` | likely — `westernpowerpool.org` probed 200 | NWPP-12 | owner uploads |
| 9 | Participant IRPs (PacifiCorp, PGE, Idaho Power, Avista, NorthWestern, Puget, NV Energy) → PRM, LTLF | `data/raw/nwpp-planning/`, `data/raw/load-forecast/nwpp/nwpp.csv` | likely — public PDFs | NWPP-12 | **owner uploads — the LTLF edition+vintage is a W2 PRECONDITION** (gate G12) |
| 10 | NRC licence status, Columbia Generating Station | `data/raw/nuclear-license-status/nwpp.csv` | likely | NWPP-12 | owner uploads |
| 11 | Confirmed retirements (Colstrip, Centralia, Jim Bridger, North Valmy — consent decrees, state orders, IRP commitments) | per registry `data/raw/…` | partial | NWPP-12 | owner uploads |
| 12 | BPA balancing-authority load/wind/hydro feed (cross-check) | `data/raw/nwpp-planning/` | **YES — probed 206** (`transmission.bpa.gov/…/baltwg.txt`) | NWPP-11 | — |
| 13 | Holdout years 2019–2022 of rows 1–4 | same paths | yes, same routes; **BALANCE is committed back to 2019** | after W4 | — |

---

## 7. Hard gates — how this goes wrong

| # | Failure | Wave | Mitigation |
|---|---|---|---|
| G1 | Pin flips half-way: `_ISO_BUILDERS` without `DEMAND_LOADERS` (import-time assert), or `SURFACE_ISOS` left short | W2 | ONE PR; §2.3 is the NWPP-20 checklist, re-measured at its own base sha (§0) |
| G2 | Matrix atomicity: base `isos` + shard + `ISO_ORDER` + `ISO_EV_KEY` + html tag must land together; a shard missing an id hard-errors; every later lane must emit **N** cell lines where N is the count at *its* sha (§0 — SOCO may land first) | W2, forever | NWPP-21 single commit; cross-desk notice; every W3+ charter says "re-count the shards" |
| G3 | **`data-profiles.yaml` token collision — the worst measured yet.** `ava` steals five ISOs' `*-availability*` files, `grid` steals `fleet-egrid`, `pge` steals CAISO's `reference/pge-helms-ps-plant-2008`, `wpp` steals SPP's `SWPP_*` | W2 | delimiter-bounded tokens + a unit test, per §2.3; **re-measure the trap at NWPP-20's own base sha** |
| G4 | Solving before outages / benchmarks / zonal shares / **the hydro budget** exist (an unscorable copperplate) | W3→W4 | NWPP-40 PRECONDITIONS: `git log origin/main --grep=NWPP-3[01236]` all landed — **NWPP-36 included** (owner ruling N3) |
| G5 | C6: `authorized_price_tuning` must be declared **even as NONE**; DOF ledger must exist; any band ≠ 1.0 breaks rule 25 `[R-ISO-SCOPE]` | W4 | charter states it. **Note for NWPP specifically**: the rule-1 carve-out authorizes tuning *market offers*. Most of this footprint is cost-based vertically-integrated dispatch, so a band ≠ 1.0 needs a much stronger story than an RTO's; **the desk's posture is bands stay 1.0 unless the owner rules otherwise** |
| G6 | C3c needs `TAIL_THRESHOLD["NWPP"]` in three files + a regenerated `actual_tail.json` | W2 + W3 | **only if card N2 yields a series**; otherwise the three edits are deliberately skipped and the skip documented. The threshold is set from the *measured* distribution, never chosen to make C3c pass (rule 1) |
| G7 | `test_iso_coverage` sweeps: `QUEUE_CAP_PER_TECH_GW["NWPP"]`, carbon-`None`, "if `IMPORT_TRANCHES` then `IMPORT_ZONE`" | W2 | no import node ⇒ neither key ⇒ `build_import_generators("NWPP") == []` |
| G8 | **Existing keepers' cache keys move** (a new `ScenarioConfig` field, a default flip, a `results/cache.py` edit) | W2, W3, **W3b** | **AMENDED by owner ruling N3, 2026-09-13.** The original bar — *no new `ScenarioConfig` field through W4* — is now in direct tension with N3, which requires a hydraulic-coupling mechanism **before** the first keeper, and a mechanism is a field. **The tension resolves by construction, not by exception**, and NWPP-36 is held to that: the new field is registered **default-OFF on `_CACHE_KEY_OPTIONAL_FIELDS` with its frozen drop value in `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS`, in the same commit**, so it is dropped from the hash at its default and every pre-existing cached run — every ISO's keepers included — keeps its key. **There is a worked hydro precedent to copy rather than invent**: `hydro_budget_period_by_instrument` (lane nyiso-220) is the FIRST entry in that tuple and was added on exactly this basis. NWPP-20 is still forbidden any field at all; the exception is NWPP-36's single field and nothing else. Byte-identity proof is **both** lanes' exit; G-DRIFT audit before any comparison |
| G9 | Shared regenerated files (`actual_tail.json`, `actual_amplitude.json`, `eia_demand_profiles.parquet`) alter other ISOs' rows | W3-31 | `build_reference()` already MERGES per `--isos` (SPP gate G9's structural fix); non-NWPP diff = ∅ as an exit check |
| G10 | Neighbour-name collision in `data/neighbor_price._HR_GAS_ELASTIC` (keys are GLOBAL) | W2 | NWPP's neighbours are `CAISO` / `WECC_SW` / `WECC_CAN`; assert uniqueness |
| G11 | `run_isos_concurrent.py` KeyError; `calibration-solve.yml` dropdown lacks NWPP | W2 | in NWPP-20 |
| G12 | `load_forecast/nwpp.py` cannot register without a real edition/vintage | W1→W2 | manifest row 9 is a **W2 PRECONDITION** |
| G13 | Screen bundle left in `results/calibration/` → parity gate RED (rule 29(c)) — **and its opposite, a bundle stranded on an ephemeral shard container** | W4 | **REWRITTEN r#2, 2026-09-13.** As chartered this read *"`.gitignore` the bundle family — never `rm`"*, which read alone **pre-orders the miso-255 incident**: rule 34 `[R-SHARD-PROMOTABLE]` (a), corrected 2026-09-12, says the SHARD must push its bundle and that *"a shard prompt that tells its shard to gitignore or omit the bundle is a defect in the prompt."* The seam, stated so a W4 charter cannot get it wrong: **`.gitignore` is the PARENT's tree, never the shard's.** The shard appends a `.gitignore` **negation** for its own out-dir and uses a **plain `git add`, never `git add -f`** (the `-f` form is what the auto-mode classifier refuses); the pushed bundle **must** carry `dispatch/<year>_P1.parquet` or registration raises `FileNotFoundError`; the parent keeps per-year dirs out of `main` by composing and committing only the composite (rule 32(d)); and **nothing is ever `rm`'d before the owner rules on promotion** (rule 31 `[R-RETAIN]`, the ercot-255 incident). The SOCO desk found the identical defect in its own plan at its r#2 — this program had it too |
| G14 | Live writers on the same dicts (capx D-lanes on `capacity_market.py`; SCN on `constants.py`; the SPP/MISO lanes on `interchange/spec.py`; **the SOCO desk on all of them, §0**) | W2 | append-last + rebase-last; desk collision check at issuance (ledger §4) |
| G15 | Desk grades a lane LOST on absence; reads green CI as proof | desk | handoff §0.3 |
| G16 | NWPP appears on the forecast board before W6, or anyone but the capx director writes it | W2+ | MUST-NOT-TOUCH line in every charter |
| G17 | **The price gap gets papered over** — a lane substitutes CAISO SP15/NP15 or Palo Verde (both one column away in the same ICE workbook, §2.6) and calls it NWPP's actual | every wave | §2.6 is quoted in every charter that touches scoring; card N2 is the only route |
| G18 | **A zone splits a BA.** There are no sub-BAs (§2.5), so any zone finer than a whole-BA group is unmeasurable on the load side | W2, W3 | card N5's grouping is whole-BA by construction; NWPP-20 asserts it; `_NWPP_BA_ZONES` is keyed on `Balancing Authority Code`, never on state |
| G19 | Two-timezone footprint mis-bins an hour, or a DST transition doubles/drops one | W1→W3 | **largely closed by §2.6's measurement** — EIA-930 assigns one zone per BA (14 Pacific / 3 Mountain) and both time columns are committed. Every derived series still **states** its zone; card N6 fixes the canonical convention |
| G20 | **The 30 defective demand hours (§2.5) propagate into benchmarks or the peak** — unscreened they put the 2025 coincident peak at 835,464 MW against a true ~50,953 | W1→W3 | NWPP-10 establishes the `Demand (MW) (Adjusted)` convention; NWPP-40's PRECOMMIT names the 30 hours; **nothing is padded or interpolated** (rule 13) |
| G21 | **Memory.** 940 plants / 1,932 generators × 5 zones is the largest per-plant LP in the repo | W4 | rule 32(c)(8): run the runner unmodified, never `--no-container-preflight`, report `container preflight:` and `memory peak:`. NWPP-40 budgets for a long single shard, **never a per-year fan-out** (rule 32(b)) |
| G22 | A `DATA PROFILE: code` session sees `integration` tests red for an unbuilt `data/clean`, or a cold first pass of `tests/curation` reporting a spurious failure | every lane | build `data/clean` (`scripts/regenerate_clean.py`) before the gates; read a first-pass curation failure as cold-start until re-run |
| G23 | **Shard containers left holding, or a shard branch deleted while its bundle is the only copy** (rule 33 `[R-SHARD-ARCHIVE]`) | W3b, W4 | **NEW r#2, 2026-09-13** — this program was chartered 2026-09-13 and never folded rule 33 into a gate. Archive on *"the parent HAS it"* (fetched + checked out + verified), never on *"the shard finished"*; verify retrievability with `git ls-tree -r <shard sha> -- <bundle path>` returning **> 0 files** BEFORE archiving (rule 34(d)); pin every recovery line to a **full 40-char SHA**, never a branch name (shards rebase and force-push even when forbidden); **never delete a branch carrying a bundle whose promotion is undecided** (rule 31); and note the measured **HTTP 403** on branch deletion here, whose misleading `Everything up-to-date` symptom reads like the HTTP/2 flake and is not one — a session that cannot delete **says so and leaves the branch** |
| G24 | **A promotion leaves the outgoing keeper registered, or shrinks the ISO's year set** (rule 35 `[R-PROMOTE]`) | W4+ | **NEW r#2, 2026-09-13** — same omission as G23. The promoting session prunes the outgoing keeper's **three stores** via `scripts/prune_iso_runs.py --iso NWPP` **in the session that promotes**; it **enumerates the year union from every NWPP sidecar BEFORE pruning**, because the prune destroys that evidence; the incoming keeper must **cover** that union (in its own bundle or via a run stamped to it — a dangling `holdout.keeper` reads as unstamped and drops the year off the report silently); the order is **promote → verify (`audit_keepers.py` E1) → delete**, never delete-first; scope is **NWPP only**, never another ISO's shard. The invariant is `audit_keepers.py` **E13**. Measured at this desk's r#2 pin: E13 is **already failing for MISO (×4) and SPP (×1)** — this gate exists so NWPP never joins that list |
| G25 | **The determination class card N2 limb (b) ruled does not exist in code, so a solved NWPP keeper cannot be scored at all** — and the fix, being a shared-scorer edit, silently moves another ISO's verdict | W1c, W4 | **NEW r#3, 2026-09-13, owner ruling N11.** Lane **NWPP-22** builds ONE added branch in `scripts/calibration_verdict.py`. Its exit is a **byte-identity proof over every pre-existing designated keeper** — re-score each before and after, diff the FULL verdict payload, **zero bytes moved**, keeper ids read from `frontend/data/backcast/keepers/*.json` at the lane's OWN base sha because a promotion moves them. The predicate is **data-driven — the ABSENCE of an admissible hourly price series — never an `if iso ==` ladder**, which is what makes the same branch cover both failure modes (none was ever built; one was built and its STOP gate refused it, as NWPP-13's did). Fail-closed: unreachable for an ISO that HAS a series; **never a PASS and never an upgrade** (rule 22 `[R-C3C]` guard (d) is the template); the unscored price criteria are named on the determination basis at full magnitude; caveat budgets checked FIRST. **No `ScenarioConfig` field, so no matrix row and no cache-key movement** — adding either would be wrong |

---

## 8. Prompt pack

House style: every prompt implicitly begins — *Read `CLAUDE.md` freshly and in full;
`docs/multi-iso/05-backcast-playbook.md`; this plan (§1–§3, §7 and your §5 row are your charter);
`docs/multi-iso/spp-addition-plan-2026-09.md` §2.3/§7 as the mechanical precedent;
`docs/multi-iso/soco-addition-plan-2026-09.md` as the non-market precedent; the mechanism matrix.
Fresh branch off latest `origin/main`; rebase before pushing; zero solves until your PRECOMMIT is
pushed (where you solve at all).* And ends — *Push by pack size (CLAUDE.md "Git & Pushing"; HTTP/1.1
retry on 408/500); fetch-back verify every pushed file ≥ 300 lines (rule 27); no CI workflows
(private repo, billed minutes); no `ScenarioConfig` default moves; never touch
`frontend/data/forecast/`, any other ISO's keeper shard, log or matrix shard, **or any SOCO program
file**; if you must touch a file outside your regions, STOP and route to NWPP-DESK in your FINDING.
Findings to `docs/handoffs/FINDING-nwpp-<id>-<date>.md` — and NOTHING ELSE shared (§8.0).*

### 8.0 COLLISION RULES (standing — pasted into every lane session)

Inherited in substance from the SPP plan §8.0, which was written after ten lanes collided on the same
shared tables, and from the SOCO plan's §8.0.

1. **A lane touches NO shared record.** Not this plan, not the ledger, not
   `docs/calibration-log/nwpp.md`, not `CHANGELOG.md`, not the shard's `keeper`/`gates` stamp, not
   `docs/mechanism-testing-matrix.md`. The DESK writes every one of those at its next refresh, from
   the lane's FINDING. A lane's record is ONE new file — its FINDING (+ PRECOMMIT) — and the FINDING
   carries a `## Log entry` section in `nwpp.md`'s format that the desk appends verbatim.
2. **The only shared file a lane may edit is its OWN CELL LINE in `mechanism-matrix/NWPP.js`** (and,
   under rule 28(c), one `·` cell line per foreign shard when it adds a field).
3. **Rebase, never merge-in.** `git fetch origin main && git rebase origin/main`, re-run the gates,
   `git push --force-with-lease` on your own branch.
4. **One PR per lane**, opened when the lane is DONE.
5. **Data and code regions stay disjoint by construction** (FILES YOU OWN); a second lane needing the
   same file is the desk's sequencing error — STOP and route.
6. **A gate-repair lane re-verifies the gate at ITS OWN base sha before touching anything.** A red
   gate at the desk's pin can be green by the time you launch. If it is green: do not re-key, do not
   manufacture a supersession that did not happen; report what is still owed and stop.
7. **A lane that may produce a PROMOTABLE run asks the promotion question INSIDE its own session,
   while the bundle is alive** (rule 31 `[R-RETAIN]`; the container is ephemeral).
8. **Every solve runs in a shard; the lane session never runs an LP** (rule 32 `[R-SHARD]`), and a
   registrable run is **ONE shard, ONE `--year 2023 2024 2025` invocation, ONE bundle**
   (rule 32(b) — slim per-year fan-out is banned). The shard **pushes its bundle to its own branch**
   (rule 34 `[R-SHARD-PROMOTABLE]`).
9. **The SOCO program is a sibling desk's lane.** Never edit a `soco*` file, never answer its card
   S2, never charter across the boundary (§0).

### W1 — Phase 0/1 (issuable now; NWPP-10/11/12 are parallel, NWPP-13 needs only card N2's ruling)

#### NWPP-10 `[OPUS]` — data audit + registry-values table + protocol correction

```
You are lane NWPP-10. MODEL: Opus claude-opus-5 — a census against a defined recipe (the MISO, SPP
and SOCO data audits); you RECOMMEND, you never decide topology and you never edit src/.
DATA PROFILE: shared.  Branch stem: claude/nwpp-10-audit-<4 chars>.
Read CLAUDE.md freshly and in full; docs/multi-iso/05-backcast-playbook.md §1 (Phase 0) and §8;
docs/multi-iso/nwpp-addition-plan-2026-09.md (§1-§3, §5 row NWPP-10, §6, §7 — and §2.5, §2.6 and
§2.7 IN FULL, because the load-spine correction, the price problem and the hydro limits each change
what an audit must recommend); docs/multi-iso/spp-data-audit.md and miso-data-audit.md (YOUR
TEMPLATES — status table columns item/source/status got|blocked|partial/file path/notes, then one
section per item, then a copy-paste manual manifest); docs/multi-iso/00-iso-addition-protocol.md
§0-§3.

PRECONDITIONS: none (W1 is additive). NWPP-11/12/13 run in parallel — you consume nothing from them;
where you need a number they will fetch, write "pending NWPP-11/12/13", never a guess.

FILES YOU OWN: docs/multi-iso/nwpp-data-audit.md (NEW); docs/multi-iso/00-iso-addition-protocol.md
(§0 NWPP row + the §3 registered-ISO-count sentence ONLY); docs/multi-iso/01-data-needs-and-upload-
manifest.md (NWPP rows ONLY).
FILES YOU MUST NOT TOUCH: anything under src/, scripts/, configs/, tests/, frontend/, data/;
05-backcast-playbook.md; any other ISO's audit; any soco* file; this plan; the ledger.

TASK — write docs/multi-iso/nwpp-data-audit.md:
(1) FLEET CENSUS off the committed EIA-860 parquets (data/raw/eia-860/eia860_plant.parquet joined to
    eia860_generator_operable.parquet on "Plant Code", over the 17 BA codes in plan §2.1 — do NOT
    call get_iso_config("NWPP"), it does not exist yet). CONFIRM OR CORRECT the plan's numbers:
    1,082 plant-table rows / 940 plants with an operable generator / 1,932 generators / 98,738.1 MW;
    the per-BA, per-state and per-technology tables; hydro 35,799.5 MW over 288 plants with eight
    >= 1 GW holding 17,821.8 MW; nuclear 1,200.0; coal 8,910.2 over 32 units; Electric Utility
    68,860.0 MW of 98,738.1 by plant Sector Name.
(2) THE TRE DEFECT — ADJUDICATE IT AND STATE THE RULE YOU APPLIED. Two generators totalling 500.0 MW
    are filed under BA DOPD (a Washington PUD) with state TX and NERC region TRE. Identify the
    plant, decide in-footprint or source defect, and say what test decided it. This is the direct
    analogue of the SOCO audit's "MA 1.5 MW" row.
(3) THE CURATED-FLEET SEAM. data/raw/eia-860/eia860_generators.parquet is a CURATED seven-ISO file:
    19,725 rows, exactly {CISO ERCO ISNE MISO NYIS PJM SWPP}, ZERO NWPP rows, and its state list
    excludes ID/OR/WA. Establish whether NWPP must extend that file or read the raw plant+generator
    pair, and RECOMMEND which — NWPP-20 implements your answer, so it must be unambiguous.
(4) THE LOAD SPINE. Plan §2.5 found all 17 BAs already committed in
    data/raw/eia-930/EIA930_BALANCE_<yr>_<half>.parquet. CONFIRM that, then:
    (a) confirm or correct 283.97 / 291.56 / 294.86 TWh and the cleaned coincident peaks 49,290 /
        52,564 / 50,953 MW;
    (b) confirm AVRN and GRID carry NULL demand in all 26,295 hours of 2023-2025 and state the
        consequence for zoning (they are supply-side members, not zone candidates);
    (c) run the repo's existing median-ratio defect screen over Demand AND every generation column,
        confirm or correct the 30 flagged hours (AVA 10 incl. 810,948 MW at 2025-10-12 10:00 UTC and
        -58,286 at 2024-01-05 16:00; NWMT 11; NEVP 6; PACE 1; SCL 2), and ESTABLISH THE CONVENTION:
        does "Demand (MW) (Adjusted)" already carry the screened series, and is it what every
        downstream series must read? Do NOT pad, interpolate or rescale anything (rule 13).
(5) SEASONAL PEAK BY CANDIDATE ZONE. Using §2.5's committed hourly demand, measure for each of card
    N5's five candidate groups whether it is summer- or winter-peaking, per year, with the peak hour.
    Card N7 needs this and it must be MEASURED, not asserted from regional reputation.
(6) TIMEZONE. Plan §2.6 measured EIA-930 assigning exactly one zone per BA — Mountain for NWMT,
    PACE, WAUW; Pacific for the other 14, including IPCO (which files Pacific although southern
    Idaho is legally Mountain). CONFIRM or correct it across all three years including both DST
    transitions, RECORD the IPCO reconciliation, and state the convention every downstream series
    must adopt. fetch_eia930_hourly.BA_TIMEZONE has no entry for any of the 17.
(7) THE REGISTRY-VALUES TABLE — one row per value NWPP-20 will need, each with a primary citation
    (URL + page/table) or "pending NWPP-12": planning reserve margin by season and by zone, VOLL
    (there is no offer cap here — most of the footprint takes no offers; propose an economic value
    with a cite and say explicitly why FERC Order 831's $2,000 is a poor fit), BA->zone map
    candidate, gas basis proxy per zone (Sumas / Stanfield / Opal / Kern River), coal price basis
    (PRB vs Uinta vs Colstrip mine-mouth), nuclear monthly CF for Columbia, queue caps by tech,
    state RPS/CES floors (WA CETA, OR HB 2021, NV, MT, ID, UT, WY differ sharply — cite DSIRE per
    state rather than leaving rows blank), LTLF edition + vintage, eGRID vintage,
    TRANSMISSION_BASE_STATIC_VINTAGE candidate. NEVER invent a number: a cell is a cited value or
    "pending".
(8) CEMS COVERAGE ARITHMETIC (card N8): with CAMPD present for MT/NV/WY/CA and absent for ID/OR/UT/WA,
    compute what SHARE OF NAMEPLATE AND OF ENERGY the CAMPD path can reach once NWPP-11 lands the
    four states — the plan's estimate is ~32% of nameplate and it wants your measured number.
(9) ZONE RECOMMENDATION (recommend, do not decide — the desk serves card N5 from this): card N5's
    five groups vs three vs one. Say what the data you can see supports, what NWPP-12 must supply
    (published WECC path ratings), and the part that matters — that no sub-BA product exists, so a
    zone may not split a BA, and BPAT alone is 20.26% of load.
(10) MANUAL MANIFEST: copy-paste block of every item you could not source, with exact URLs.
Then CORRECT docs/multi-iso/00-iso-addition-protocol.md §0 (add an NWPP row saying "not registered —
see nwpp-addition-plan-2026-09.md") and the §3 sentence that counts the registered ISOs — READ that
sentence at your own base sha first, because the SOCO program may have changed the count (plan §0).

RULES THAT BITE: 5 [R-NO-MAGIC], 13 [R-MEASURED] (every value a reproducible physical/market input),
14 [R-ACCURATE], 23 [R-FROZEN-DERIVE] (you derive nothing), 27 [R-PUSH], 28 (you test no mechanism;
no matrix cell moves).
EXIT: the audit doc, the two corrections, docs/handoffs/FINDING-nwpp-10-<date>.md. Report to the
owner with the census table, the TRE adjudication, the defect-screen convention and the seasonal
peak result FIRST.
```

#### NWPP-11 `[OPUS]` — CAMPD fetch + the per-BA 930 DERIVE + interchange + monthly hydro

```
You are lane NWPP-11. MODEL: Opus claude-opus-5 — reproducible fetches and one derive through
existing scripts; no design choices. DATA PROFILE: shared.
Branch stem: claude/nwpp-11-data-<4 chars>.
Read CLAUDE.md freshly and in full; docs/multi-iso/nwpp-addition-plan-2026-09.md (§2.4, §2.5, §2.7,
§5 row NWPP-11, §6 rows 1-3, 6, 12); docs/multi-iso/miso-data-audit.md Item 1 (the CAMPD procedure)
and spp-addition-plan-2026-09.md §6 row 1 (the same route run for four states);
scripts/data/fetch_campd_unit_level.py and fetch_eia930_hourly.py docstrings;
data/raw/campd-unit-level/README.md + SHA256SUMS.txt conventions;
data/raw/zone-specific-demand/MISO/SOURCES.md (your SOURCES template).

PRECONDITIONS: none. NWPP-10/12/13 are parallel; you own no file they own.
FILES YOU OWN: data/raw/campd-unit-level/{ID,OR,UT,WA}_{2023,2024,2025,2026}.parquet (+ README and
SHA256SUMS rows); data/raw/eia-930-hourly/"<BA> hourly.parquet" for the 17 BAs (+ README rows);
data/raw/eia-930-interchange/ NWPP files; data/raw/nwpp-hydro/ (NEW, the EIA-923 monthly extract);
ADDITIVE keys only in scripts/data/fetch_eia930_hourly.py (the 17 BA_TIMEZONE entries).
FILES YOU MUST NOT TOUCH: any existing raw file (data/raw is immutable); src/; configs/; tests/;
docs/multi-iso/nwpp-data-audit.md (NWPP-10's); any soco* file.

TASK, in this order, each its own small commit:
(1) CEMS: for Y in 2023 2024 2025 (then 2026 partial):
      python scripts/data/fetch_campd_unit_level.py --year Y --states ID OR UT WA
    The bulk route was probed 206 anonymous at charter and each state-year CSV is ~187 MB, so plan
    the disk: fetch, convert, verify, and delete the intermediate CSV before the next one. Verify the
    arrow schema equals a sibling (e.g. MT_2024) — the fetcher asserts it — and record
    rows/facilities/units per file. Update README + SHA256SUMS. CO is deliberately SKIPPED (one
    7.5 MW solar row in PACE); document the skip rather than leaving it unexplained.
(2) THE PER-BA 930 DERIVE — THIS IS A DERIVE, NOT A FETCH, AND THAT IS THE POINT.
    Plan §2.5 measured that all 17 NWPP BAs are ALREADY COMMITTED in
    data/raw/eia-930/EIA930_BALANCE_<yr>_<half>.parquet (2019-01 -> 2026-06, 62 BAs, 44 columns
    including Demand, Net Generation, Total Interchange, Sum(Valid DIBAs), Demand (MW) (Adjusted),
    Local Time at End of Hour and UTC Time at End of Hour). So you need NO EIA_API_KEY and NO
    network call for the load spine. Produce the 17 "<BA> hourly.parquet" files in the exact schema
    of the committed siblings (e.g. "SWPP hourly.parquet"), from those committed bytes.
    THE GATE ON THIS ITEM: each derived file must reconcile TO THE MWh against the BALANCE source it
    came from — report per BA per year the annual demand, the hour count, and the residual (which
    should be exactly zero; if it is not, STOP and report rather than adjusting). Apply NWPP-10's
    defect convention if it has landed; if it has not, produce BOTH the raw and Adjusted columns and
    say so, and do NOT choose between them yourself.
(3) INTERCHANGE: the BALANCE files already carry Total Interchange and Sum(Valid DIBAs). For
    per-counterparty DIBA detail use fetch_eia930_interchange.py for the 17 BAs — NOTE this needs
    EIA_API_KEY, which was UNSET in the charter container; if yours has none, use the key-free Grid
    Monitor interchange files and say so in your SOURCES.md. In the FINDING: a net-interchange
    duration-curve summary per counterparty per year with the sign convention stated, and the
    footprint's net position against the plan's measured net generation minus demand.
    CALL OUT SPECIFICALLY the CAISO-facing counterparties — card N4 depends on that magnitude.
(4) MONTHLY HYDRO: extract EIA-923 monthly net generation for all 288 conventional-hydro plants in
    the footprint, 2023-2025, per plant per month, into data/raw/nwpp-hydro/. This is NWPP-32's
    input and card N3's evidence. Report the footprint monthly total and the year-over-year spread,
    and flag any plant whose monthly series is missing or implausible — do not fill it.
(5) BPA CROSS-CHECK: fetch transmission.bpa.gov/Business/Operations/Wind/baltwg.txt (probed 206) and
    reconcile BPA's own published BA load/wind/hydro against the BPAT rows of item (2). Report the
    residual; a divergence is a finding, not something to correct away.
Anything that returns 403/404: record the exact URL + status in the FINDING's blocked table and STOP
that item — no transcription from memory, no secondary-source values.
RULES THAT BITE: 13 [R-MEASURED], 14 [R-ACCURATE], 23 [R-FROZEN-DERIVE] (fetch and derive, do not
model), 26 [R-DELETE], 27 [R-PUSH] (parquets are binary — git push by pack size; split by state-year
if a pack is refused; never push_files a parquet), 28.
EXIT: docs/handoffs/FINDING-nwpp-11-<date>.md with the got/blocked table, per-file row counts and
schema checks, the 17-BA reconciliation table, the DIBA duration summaries and the hydro monthly
table. Report FIRST: which of {ID,OR,UT,WA} x {2023,2024,2025} landed, and whether the 17-BA derive
reconciled to zero.
```

#### NWPP-12 `[OPUS]` — WECC paths + WRAP + IRPs + NRC + fuel prices

```
You are lane NWPP-12. MODEL: Opus claude-opus-5 — fetch + transcription against a manifest.
DATA PROFILE: shared.  Branch stem: claude/nwpp-12-docs-<4 chars>.
Read CLAUDE.md freshly and in full; docs/multi-iso/nwpp-addition-plan-2026-09.md (§3 cards N5/N7,
§5 row NWPP-12, §6 rows 7-11); docs/multi-iso/04-transmission-zones-and-congestion.md (the TTC
tiering convention — Tier-1/2/3 and what "documented misalignment" means);
data/raw/spp-planning/README.md (YOUR TEMPLATE for a planning corpus: a README carrying the verified
source-URL table, the re-fetch command, the retention status and SHA256SUMS.txt);
scripts/lib/nuclear_license_status/ and load_forecast/ (the spec shape a registry module must
satisfy — note test_specs_declare_an_edition_and_a_vintage).

PRECONDITIONS: none.
FILES YOU OWN: data/raw/nwpp-planning/ (NEW); data/raw/nuclear-license-status/nwpp.csv (NEW);
data/raw/load-forecast/nwpp/nwpp.csv (NEW); data/raw/gas-prices/ and data/raw/coal-prices/ NWPP rows
+ SOURCES_nwpp_*.md.
FILES YOU MUST NOT TOUCH: src/; scripts/lib/*/ (the registry MODULES are NWPP-20's — you supply
their DATA); tests/; any other ISO's data; any soco* file.

TASK:
(1) WECC PATH RATINGS — card N5's evidence and the reason NWPP can have a better TTC story than SPP
    got. From wecc.org (probed 200) obtain the published path rating catalogue and transcribe, with
    URL + page/table, the ratings for at least: Path 8 (Montana-Northwest), Path 14 (Idaho-
    Northwest), Path 20 (Path C), Path 27 (IPP DC), Path 35 (TOT 2C), Path 65/66 (PDCI / COI), Path
    4 (West of Cascades North) and Path 3 (Northwest-Canada). For EACH, state which of card N5's
    five-zone boundaries it does or does not correspond to. WHERE NO PUBLISHED RATING MAPS TO A
    BOUNDARY — the desk expects this for NWPP-NW <-> NWPP-OR, a dense multi-point interconnection
    rather than a rated path — SAY SO EXPLICITLY. That finding is what makes the link Tier-3, and a
    documented absence is worth more here than a plausible number.
(2) WRAP — card N7's gating fact. Establish from Western Power Pool's own documents (probed 200),
    WITH A CITATION: when the Western Resource Adequacy Program's FIRST BINDING season falls; which
    of the 17 BAs are participants and from when; and what the binding forward showing and holdback
    requirements are. THE DESK'S EXPECTATION IS THAT BINDING POST-DATES THE 2023-2025 BACKCAST
    WINDOW, AND THE DESK HAS DELIBERATELY NOT ASSERTED IT — your citation decides it. If binding is
    outside the window, say so plainly: WRAP is then a forecast-side object only.
(3) IRPs: the most recent integrated resource plans for PacifiCorp, Portland General, Idaho Power,
    Avista, NorthWestern Energy, Puget Sound Energy and NV Energy. Transcribe into the README's
    values table, each with URL + page: planning reserve margin BY SEASON, the peak-load history,
    the resource plan, announced coal exit dates, and any published internal transfer limit.
(4) NRC: licence expiry and any SLR status for Columbia Generating Station -> nwpp.csv in the shape
    scripts/lib/nuclear_license_status/ expects.
(5) LTLF: a real long-term load forecast with an EDITION and a VINTAGE (>= 2020), footprint-wide or
    assembled from the IRPs with the assembly documented. This is a W2 PRECONDITION (gate G12) — if
    no citable edition exists, say so loudly in your FINDING's first paragraph, because it blocks
    registration.
(6) FUEL: gas basis for this footprint is NOT one hub — name and source the per-zone basis (Sumas,
    Stanfield, Opal, Kern River are the candidates) and say which of card N5's zones prices against
    which, with a public daily/monthly series for each if one is reachable. Coal: PRB vs Uinta vs
    Colstrip mine-mouth, per plant where the IRPs or EIA-923 fuel receipts say so.
(7) CONFIRMED RETIREMENTS: enforceable public instruments for footprint fossil exits — Colstrip,
    Centralia (the plan measured 229.5 MW of coal carrying a 2027 EIA-860 date), Jim Bridger, North
    Valmy, Naughton. The admissibility bar is CLAUDE.md's step-0 bar: an enforceable public
    instrument with a date. An IRP intention is NOT an instrument — record it separately and say so.
Anything blocked: exact URL + status in the FINDING, then STOP that item.
RULES THAT BITE: 5 [R-NO-MAGIC], 13, 14 (and its misalignment exception, which is the whole of item
1's tiering judgement), 27, 28.
EXIT: docs/handoffs/FINDING-nwpp-12-<date>.md with the got/blocked table and the transcribed values
table. Report FIRST: the WRAP binding-season answer, the LTLF availability, and which of card N5's
boundaries have a published path rating.
```

#### NWPP-13 `[FABLE]` — the WEIM price index (card N2 option a; STOP-gated)

```
You are lane NWPP-13. MODEL: Fable — this lane CONSTRUCTS A BENCHMARK, which is the most
adjudication-heavy act in an ISO addition: every later price criterion is scored against what you
build, so a fitted or ill-founded index would corrupt the whole program invisibly.
DATA PROFILE: shared.  Branch stem: claude/nwpp-13-weim-price-<4 chars>.
Read CLAUDE.md freshly and in full — rules 1 [R-STRUCT], 13 [R-MEASURED] and 14 [R-ACCURATE] are the
whole of your charter; docs/multi-iso/nwpp-addition-plan-2026-09.md §2.6 IN FULL, §3 card N2, §5 row
NWPP-13, §7 gate G17; scripts/data/build_spp_lmp_reference.py (the shape of a price-reference builder
in this repo); data/raw/_validation-source/actual_lmp_hourly_SPP.parquet's schema
(year/hour/zone/rt/da) and the cross-check gate SPP-14 applied to it.

ONLY START AFTER the owner has ruled card N2. If N2 is unruled, STOP and say so.

THE PROBLEM: the Northwest Power Pool publishes no LMP and had no day-ahead market in 2023-2025.
What DOES exist, and was pulled anonymously in the charter session rather than assumed:
  - CAISO OASIS carries 212 apnodes of type EIMT (EIM Transfer) across this footprint's BAs
    (BPAT 23, PACW 18, IPCO 13, NWMT 12, AVA 12, PGE 11, PACE 11, SCL 10, PSEI 10, NEVP 10, TPWR 4)
    plus three CASP nodes CGAP_{DOPD,CHPD,GCPD}_MIDC. A PRC_RTPD_LMP pull for PACW_BPAT.PSEI-APND on
    2023-07-15 returned 481 rows of real 15-minute LMPs, first interval $63.9213/MWh.
  - EIA's ICE workbooks (eia.gov/electricity/wholesale/xls/archive/ice_electric-<yr>final.xlsx)
    carry a "Mid C Peak" hub: 2023 has 244 trade dates, 4,748,000 MWh, weighted-average price, daily
    volume, trade count and counterparty count.
Your job is to decide whether a defensible footprint-hourly price index can be built, and either
build it or document why not. BOTH outcomes are a successful lane.

THREE THINGS THE CHARTER HAS ALREADY DECIDED, WHICH YOU MAY NOT REOPEN:
  - MID-C IS AN ANCHOR, NEVER THE BENCHMARK. It is daily and PEAK-ONLY (there is no Mid C Off-Peak
    row), so it cannot score C3b or C3c at all. Use it to reconcile a level; never to score.
  - A NEIGHBOURING MARKET'S HUB IS REFUSED (gate G17). SP15, NP15 and Palo Verde sit in the SAME ICE
    workbook you will open for Mid-C — one column away. Substituting one is the load proxy rule 13
    forbids. Mid-C is this footprint's OWN traded hub and is not caught by that refusal; a CAISO hub
    is.
  - YOU MAY NOT EVALUATE YOUR INDEX BY WHETHER IT IMPROVES ANY RESIDUAL. No NWPP model run exists
    yet and none may be used (rule 1 [R-STRUCT]).

WRITE THE PRECOMMIT FIRST, PUSH IT, AND ONLY THEN TOUCH THE DATA. The PRECOMMIT fixes, ex ante:
  (a) the NODE SET — which EIMT/CASP nodes define each of card N5's zones, and the rule that picked
      them (never "the ones that looked reasonable");
  (b) the WEIGHTING — how per-node 15-minute LMPs become a zonal and a footprint hourly price
      (volume-weighted on what measured quantity? simple mean? state it and justify it);
  (c) the AGGREGATION — 15-minute to hourly; how a missing interval is handled (carried, NaN, or
      dropped — and NEVER interpolated toward anything a model produces); the timezone convention,
      which must match NWPP-10's finding;
  (d) THE STOP GATE, as pass/fail NUMBERS, not adjectives:
        - a minimum hourly coverage over 2023-2025;
        - THE WEIM VOLUME SHARE: the minimum share of the footprint's energy that WEIM actually
          clears, below which this series is declared MISALIGNED to the quantity it would price.
          This is the number the charter deliberately did not guess (§2.6) and it is the crux of the
          whole lane — measure it from CAISO's published WEIM volume/benefit reporting against the
          footprint demand in plan §2.5, and fix the threshold BEFORE you measure it;
        - the RECONCILIATION against Mid-C Peak, as a stated numeric tolerance on the peak-hour
          business-day subset;
  (e) what you will do if the gate FAILS: land nothing to _validation-source, write the NO.
A GATE WRITTEN OR LOOSENED AFTER SEEING THE SERIES IS A FITTED BENCHMARK AND IS REFUSED. Say so in
the PRECOMMIT in your own words, so the record shows you knew.

THEN: fetch the WEIM series (oasis.caiso.com/oasisapi/SingleZip?queryname=PRC_RTPD_LMP...; probed
200 anonymous at charter — plan the paging, it is 96 intervals/day x ~40 nodes x 1,095 days), build
scripts/data/build_nwpp_weim_price_index.py, and run your own gate.

FILES YOU OWN: data/raw/nwpp-weim/ (NEW, with a README in the spp-planning template);
scripts/data/build_nwpp_weim_price_index.py (NEW); data/raw/_validation-source/
actual_lmp_hourly_NWPP.parquet (ONLY if the gate passes); docs/handoffs/PRECOMMIT-nwpp-13-<date>.md
and FINDING-nwpp-13-<date>.md.
FILES YOU MUST NOT TOUCH: src/; any other _validation-source file; actual_lmp.json (NWPP-31's);
tests/; this plan; the ledger; any soco* file. THE DESK HAS ALREADY RESOLVED THE PROFILE QUESTION
THIS CHARTER USED TO ROUTE TO IT — do not re-open it. Measured at desk r#2 (2026-09-13) by running
configs/data-profiles.yaml's own substring rule: a data/raw child named "caiso-weim" CONTAINS the
CAISO token "caiso" and is therefore attributed to the CAISO profile, i.e. it would NOT hydrate for
a `shared` or a future `nwpp` session and WOULD be swept into CAISO's. "nwpp-weim" matches no ISO
token at this pin and resolves to `shared` — which is correct for W1 — and moves into the nwpp
profile automatically the moment NWPP-20 registers the `nwpp` token, with no file to rename. USE
data/raw/nwpp-weim/.

RULES THAT BITE: 13 [R-MEASURED] — the index must be a reproducible market input that would
regenerate for a forward year, never an outcome fitted to anything the model produces; 14
[R-ACCURATE] — if the real data makes the eventual backcast look worse, that is a discovered bug
elsewhere, not a reason to adjust the index; 1 [R-STRUCT]; 23 [R-FROZEN-DERIVE]; 27 [R-PUSH].
EXIT: FINDING with the PRECOMMIT's gate table filled in with measured values, the Mid-C
reconciliation table, the measured WEIM volume share, and a one-line verdict: SERIES LANDED or NO,
with the reason. Report the verdict and the volume share FIRST.
```

### W1c — the scorer branch (owner ruling N11; issuable NOW, file-disjoint from every other lane)

#### NWPP-22 `[FABLE]` — the determination class card N2 limb (b) ruled

```
You are lane NWPP-22. MODEL: Fable — you are editing the SHARED SCORER that produces every registered
ISO's determination. This is the ONLY lane in this program licensed to touch
scripts/calibration_verdict.py, the licence is narrow, and its exit is a byte-identity proof over
every pre-existing keeper.
DATA PROFILE: code.  Branch stem: claude/nwpp-22-verdict-basis-<4 chars>.
Read CLAUDE.md freshly and in full — rule 22 [R-C3C] is your ARCHITECTURAL TEMPLATE and rule 1
[R-STRUCT] is your constraint; scripts/calibration_verdict.py's MODULE HEADER IN FULL (it is the
rubric's genealogy — v3.7 at this pin — and it records how every previous standing rule was
introduced, guarded and measured); _apply_c3c_standing_rule (~line 1210) as the worked pattern;
CRITERIA (~832); _actual_lmp_coverage (~1082); docs/multi-iso/nwpp-addition-plan-2026-09.md §2.6,
§3 cards N2 and N11, §5 row NWPP-22, §7 gate G25; and
docs/handoffs/FINDING-nwpp-13-2026-09-13.md §0 and §3 — WHY this lane exists.

WHY THIS LANE EXISTS, MEASURED RATHER THAN ASSUMED. Owner card N2 was ruled 2026-09-13, both limbs,
limb (b) verbatim: "a failed gate yields a determination naming its own basis, never a bare
CALIBRATED, with the price gap on the determination basis at full magnitude." Lane NWPP-13 then ran
its pre-registered STOP gate and READ NO: WEIM clears 5.5-6.2 % of footprint energy on the declared
net basis (10.6 % pairwise-gross) and PASSED the volume bar, but its on-peak price sits 22.6 / 23.6 /
37.5 % BELOW the independent Mid-C Peak traded index in 2024 / 2025 / 2023 against a pre-registered
+/-10 % bar, with daily correlation 0.67-0.95 against a 0.80 bar. No bar was moved after the series
was seen, and NOTHING was landed to _validation-source. So at this pin NWPP has NO admissible hourly
price series, there is no actual_lmp_hourly_NWPP.parquet, and C3a/C3b/C3c cannot be scored for it by
any admissible route (a neighbouring hub stays refused — gate G17).
THE RULING AUTHORIZED A DETERMINATION CLASS; NOBODY BUILT IT. Until you do, an NWPP keeper cannot be
scored at all. That is the whole of your remit, and it is why the owner ruled "send it now".

WHAT YOU BUILD: ONE added determination branch, and its guards. Five things are NOT negotiable.

(1) THE PREDICATE IS DATA-DRIVEN — NEVER `if iso == "NWPP"`. The branch fires on the ABSENCE of an
    ADMISSIBLE hourly price series for the ISO being scored. That one predicate covers BOTH failure
    modes, which is the point: "no series was ever built" and "a series was built and its STOP gate
    refused it" present identically to the scorer, because a refused series is never landed. It is
    also why NWPP-13's verdict does not change your code — only whether the branch fires.
(2) IT IS NEVER A PASS AND NEVER AN UPGRADE. Copy rule 22 [R-C3C] guard (d) exactly: the price
    criteria read UNSCORED, never PASS; grade_summary.target_grade never absorbs them; each is NAMED
    on the determination basis AT FULL MAGNITUDE with its reason. A determination naming its own
    basis is a STATEMENT OF WHAT WAS NOT TESTED — it is strictly weaker than CALIBRATED, never a
    softer route to it. If your branch could ever make a run read BETTER than the same run scored
    with a price series, you have built the escape hatch rule 22 exists to prevent. Say in the
    PRECOMMIT, in your own words, how you know it cannot.
(3) FAIL-CLOSED AND NARROW. Unreachable for any ISO that HAS a series. A series that exists but is
    PARTIAL is the existing coverage machinery's job (_actual_lmp_coverage) — do NOT widen into it.
    Both caveat budgets are checked FIRST, exactly as rule 22 orders them.
(4) NO ScenarioConfig FIELD, SO NO MATRIX ROW AND NO CACHE-KEY MOVEMENT. This is a scorer branch, not
    a solve mechanism: it changes no LP, no cache key, no bundle, and existing keepers re-score in
    place. Rule 28(c) does NOT fire — adding a matrix row would be WRONG. Run
    scripts/check_mechanism_matrix.py and paste its OUTPUT, not its exit code (gate G15).
(5) YOU TOUCH NO EXISTING CRITERION. No threshold, band, tier, budget, TAIL_THRESHOLD entry or
    standing rule moves. RUBRIC_VERSION: you are adding a determination class, so read the header's
    OWN convention for when it moves and when it deliberately does not, follow it, and state your
    reading in the FINDING rather than guessing.

THE EXIT — BYTE-IDENTITY OVER EVERY PRE-EXISTING KEEPER. Re-score each designated keeper at HEAD
BEFORE your change and AFTER it, and diff the FULL verdict payload. ZERO BYTES MAY MOVE. Measured at
33a7c961 (READ THEM AT YOUR OWN BASE SHA from frontend/data/backcast/keepers/*.json — a promotion
moves them, and grading from this list instead of the tree is exactly the error gate G15 names):
    CAISO 2026-09-12-caiso-275-gascoupling · ERCOT 2026-09-09-ercot265-receipts-fallback ·
    MISO  2026-09-12-miso-255-sil-measured · NEISO 2026-09-09-neiso-108-fuelvintage ·
    NYISO 2026-09-13-nyiso231-anchor-span · PJM   2026-09-11-pjm-d4-4-gasoutage ·
    SPP   2026-09-13-spp-38-vintage-cache
A SINGLE MOVED BYTE IS A STOP: report it, do not explain it away.
PLUS two tests in a NEW tests/scoring/ file: the branch CANNOT fire for an ISO carrying a price
series, and DOES fire for one carrying none. SYNTHESISE the fixture — you are file-disjoint from
NWPP-20 and must NOT wait for NWPP to be registered.

WRITE THE PRECOMMIT FIRST AND PUSH IT BEFORE YOU EDIT THE SCORER. It fixes, ex ante: the predicate;
the exact determination string an unscoreable-price ISO will read; every guard; the RUBRIC_VERSION
decision; and the byte-identity protocol. A guard designed after the diff is seen is not a guard.

FILES YOU OWN: scripts/calibration_verdict.py (the added branch and its guards ONLY); a NEW file
under tests/scoring/; docs/handoffs/PRECOMMIT-nwpp-22-<date>.md and FINDING-nwpp-22-<date>.md.
FILES YOU MUST NOT TOUCH: src/; any registry or ISO config; any keeper shard; any bundle;
frontend/data/**; data/raw/; TAIL_THRESHOLD (gate G6 — it belongs to NWPP-20/31 and only if a series
ever exists); the mechanism matrix; this plan; the ledger; docs/calibration-log/nwpp.md.

RULES THAT BITE: 27 [R-PUSH] — calibration_verdict.py is 3,813 lines at this pin, so it is squarely
the file this rule was written for: edit LOCALLY with the Edit tool, push the EXACT on-disk bytes,
NEVER regenerate the file from response content, and fetch-back verify the blob (line count + hash)
IMMEDIATELY after the push, before doing anything else. A mismatch is a stop-the-line event. 22
[R-C3C] (the template and its guards). 1 [R-STRUCT] — you may not tune, widen or soften any existing
criterion, and you may NEVER evaluate your branch by whether it improves anyone's determination. 26
[R-DELETE]. 5 [R-NO-MAGIC].
EXIT: the branch, the two tests, the keeper byte-identity table, FINDING-nwpp-22-<date>.md. Report
FIRST: the byte-identity result over every keeper, and the exact determination string an
unscoreable-price ISO now reads.
```

### W2 — registration (issued at sitting #2 after N1, N3–N8 are ruled; NWPP-21 may go first, it is disjoint)

#### NWPP-20 `[FABLE]` — the pin flip

```
You are lane NWPP-20. MODEL: Fable — this is the registration adjudication: one PR that adds a
region to the model's registry, and every table that hard-codes the current ISO count must move in it
or the import-time asserts fail. DATA PROFILE: shared (you create the `nwpp` profile).
Branch stem: claude/nwpp-20-register-<4 chars>.
Read CLAUDE.md freshly and in full; docs/multi-iso/nwpp-addition-plan-2026-09.md §2.3 (YOUR
CHECKLIST — work it row by row and report it back row by row), §0 (the SOCO ordering problem), §3
(the RULED cards — implement the rulings, never your own preference), §7 gates G1-G3, G5-G12, G18;
docs/multi-iso/nwpp-data-audit.md (NWPP-10's registry-values table is the SOURCE of every number you
register — a value not in it and not cited in your own docstring is a rule 5 [R-NO-MAGIC]
violation); docs/handoffs/FINDING-spp-20-*.md and src/market_sim/config/iso_configs.py::_spp_config
IN FULL — that function is your worked template, docstring conventions included.

PRECONDITIONS — ALL MET AT DESK r#4 (2026-09-14). Re-verify each at YOUR OWN base sha and STOP if any
has regressed; quote each ruling in your PRECOMMIT:
 - cards N1, N3 RULED at sitting #1; **N4, N5, N7, N8 RULED at sitting #4**; **N6 RESOLVED BY
   MEASUREMENT, not ruled** (plan §3 carries all six verbatim — implement the rulings, never your own
   preference, and never re-litigate one).
 - NWPP-10, NWPP-11, NWPP-12 and NWPP-13 ALL MERGED. NWPP-21 landed the ninth matrix shard.
 - manifest row 9, gate **G12: PASSES.** NWPP-12 §0.1 landed `data/raw/load-forecast/nwpp/nwpp.csv`
   (83 rows) as an ASSEMBLY from participant IRPs, because the pool publishes no footprint-wide LTLF.
   **Declared for your `scripts/lib/load_forecast/nwpp.py`: `edition = "Participant IRP assembly (2025
   cycle)"`, `vintage = 2025`, `default_basis = "unspecified"`.** Use those strings; the assembly rule
   and every publisher supplying no row are documented in that file's `SOURCES.md`.
 - **NWPP-22 landed the PRICE-UNSCORED determination class** (rubric v3.8, on `main`). NWPP has no
   `actual_lmp.json` block, so it reads `PHYSICALLY-CALIBRATED (PRICE UNSCORED)` /
   `...-WITH-CAVEATS (PRICE UNSCORED)`. You add NOTHING to the scorer.

RE-MEASURE BEFORE YOU EDIT (plan §0). The SOCO program may have registered between the charter pin
and your base sha. Read SUPPORTED_ISOS, SURFACE_ISOS, ISO_ORDER and the matrix `isos` list AT YOUR
OWN BASE SHA and report the counts you found. Do NOT execute §2.3 from its charter-time numbers.

ONE PR. Work §2.3 top to bottom. The atomicity that bites: _ISO_BUILDERS + DEMAND_LOADERS +
SURFACE_ISOS must be in the SAME commit (two import-time asserts and one pinned-tuple test).

THE PROOF THAT MATTERS (gate G8): every existing keeper's cache key must not move. Run
`python scripts/solve_surface_register.py --diff origin/main HEAD` and show ZERO moved rows for every
registered ISO; declare only the names whose NWPP projection is new. Then re-derive at least two
committed keepers' cache_key() and show them byte-identical. No new ScenarioConfig field, no default
flip, no results/cache.py edit — if you believe you need one, STOP and route to NWPP-DESK.

WHAT MAKES NWPP DIFFERENT FROM EVERY PRIOR REGISTRATION, and must be visible in the code:
 - It is a POOL OF ~17 BALANCING AUTHORITIES, not an ISO and not a BA. Say so in _nwpp_config's
   docstring, in one sentence, with the Hermiston/plant-54761/BA-PACW provenance, the second
   Hermiston plant (55328, BA GRID) as the illustration, and the Canada exclusion.
 - **`ISO_TO_BA_CODE` — THE R-e BLOCKER, AND IT IS BIGGER THAN THIS PLAN ORIGINALLY SAID.** NWPP-10
   §3 measured it and the desk has adopted the correction: plan §2.3 named `data/zone_assignment.py`
   as "the one genuinely novel code change"; **it is at least five modules and 13+ live call sites,
   and the object is `ISO_TO_BA_CODE`, not the zone map.** `BA_CODE_TO_ISO` handles 17→1 correctly
   everywhere (`.map()`, `.isin()`, and two set comprehensions). Its INVERSE does not:
       # src/market_sim/data/fleet/models.py:221
       ISO_TO_BA_CODE: dict[str, str] = {iso: ba for ba, iso in BA_CODE_TO_ISO.items()}
   With 17 NWPP entries `ISO_TO_BA_CODE["NWPP"]` becomes ONE ARBITRARY BA — whichever inserts last —
   and every consumer compares with `==`. Measured consumers: `data/hydro.py` 607/639/**684**
   (**the hydro nameplate and budget tables would cover 1/17 of the fleet — that is card N3's OWN
   machinery, which lanes NWPP-32 and NWPP-36 both read**), `data/fleet/eia860.py` 1653/2574/2748,
   `data/fleet/campd_bins.py` 168 (the oil-primary screen returns EMPTY, indistinguishable from
   "none"), `data/zone_assignment.py` 1092/1120/1325 (+795, its own 1:1 `_ISO_TO_BA_CODE`), and four
   under `scripts/`. **EVERY ONE FAILS SILENTLY** — an empty or 1/17 result, never an exception.
   NWPP-10's recommended shape, which you may improve on but must not ignore: make the ISO→BA
   direction a **codes-tuple** (`dict[str, tuple[str, ...]]`, or a parallel `ISO_TO_BA_CODES` keeping
   the scalar for the seven 1:1 ISOs), move all call sites to MEMBERSHIP, and pin it with a unit test
   asserting `len(ba_codes("NWPP")) == 17` **and** that a loaded NWPP fleet reproduces
   **939 plants / 1,930 generators / 98,238.1 MW**. **This touches shared code every registered region
   reads, so it is squarely inside your gate-G8 proof**: show the byte-identity for the 1:1 ISOs
   explicitly, and if the fix cannot be made without moving another region's behaviour, STOP and route.
 - ZONES ARE WHOLE-BA GROUPS AND MAY NOT SPLIT A BA (gate G18, plan §2.5: no sub-BA product exists).
   _NWPP_BA_ZONES is keyed on `Balancing Authority Code`, NEVER on state — data/zone_assignment.py's
   existing _SPP_STATE_ZONES is a state-keyed map and is the WRONG shape to copy. A state here holds
   several BAs and a BA holds several states.
   **CARD N5 IS RULED: FIVE ZONES** — `NWPP-NW` (BPAT PSEI SCL TPWR CHPD DOPD GCPD + AVRN generation)
   · `NWPP-OR` (PGE PACW + GRID generation) · `NWPP-INLAND` (IPCO AVA NWMT WAUW) · `NWPP-EAST` (PACE)
   · `NWPP-SNV` (NEVP). **TTC tiers are RULED too and each link states its tier in code:** EAST↔SNV
   Path 35 TOT 2C **600/580 Tier-1**; INLAND↔SNV Path 16 Idaho–Sierra **500/360 Tier-1**; NW↔INLAND
   **Tier-2** (Paths 8/6/14 aggregated, aggregation documented); INLAND↔EAST **Tier-2** (Path 20
   "Path C" 1,600/1,250); **NW↔OR Tier-3 documented ABSENCE** — no WECC path rates that interface and
   none will. **DO NOT substitute Paths 4/5/71/86/87/88**: they are east–west cuts across the Columbia
   and the Cascades, not BA interfaces, and Path 5 mixes BPA-internal, BPA→PGE and PGE-internal limbs
   in one 7,200 MW rating. Values and printed pages: `data/raw/nwpp-planning/README.md` §1.
 - **FLEET REPRESENTATION — CARD N8 IS RULED: `use_campd_bins=False`, legacy heat-rate bins.** This
   SUPERSEDES plan §3's recorded default `per_plant=True` for the memory class. Measured: CAMPD reaches
   30.98 % of nameplate / 41.8–43.6 % of energy, and 36.3 % of the footprint is hydro CEMS can never
   cover. CAMPD per-plant is pre-declared as a W5 lever, not this keeper's construction.
 - **DEMAND CONVENTION — NWPP-10 §1.3 established it and it is NOT optional.** (a) `Demand (MW)
   (Adjusted)` is the series every downstream NWPP demand read uses; it repairs all 30 artifact hours
   and reproduces the cleaned peaks **49,290 / 52,564 / 50,953 MW** to the MW. (b) **Do NOT apply
   `_screen_demand_spikes` on top for NWPP** — it flags 84 hours, and the other 54 are REAL LOAD: all
   CHPD, 12–16 January 2024, a documented cold snap containing CHPD's annual peak (583 MW) and the
   whole NWPP-NW zone's 2024 annual peak (21,560 MW). Its docstring justifies a 2.5 factor on the claim
   that "every legitimate demand series has max/median ≤ 2.1" — **falsified here by CHPD (2.29/2.83/
   2.50) in all three years and by NEVP (2.20–2.37)**. Applying it would delete a real regional cold
   snap: a rule-14 `[R-ACCURATE]` violation by construction. If a belt-and-braces screen is wanted the
   admissible form is the fuel-series two-statistic test (`> 2.5 × median` AND `> 2.5 × p99.9`,
   `data/eia930/actuals.py`), which passes all 54 and still catches all 30. (c) **`_screen_demand_
   dropouts` IS needed** — 17 exactly-zero NEVP demand hours in 2025 survive into Adjusted. (d)
   `Demand (MW) (Imputed)` is NOT a series (447,133 of 447,168 null). **Nothing is padded, interpolated
   or rescaled** (rule 13 `[R-MEASURED]`).
 - **FOOTPRINT ADMISSION PREDICATE — NWPP-10 §1.2 adjudicated the TRE row and found two more.** Encode
   **`BA ∈ NWPP_BAS AND NERC Region == "WECC"`**, NEVER a per-plant exclusion (that would be an
   off-registry dict, rule 24 `[R-REGISTRY]`). Rejected: plant **68906 Pine Forest Solar I**, Hopkins
   County TX, NERC TRE, BA `DOPD`, 500.0 MW — ERCOT and the Western Interconnection are
   **asynchronously separated**, so a Washington PUD cannot balance a resource inside ERCOT. Key (i) is
   dispositive on physics; coordinates corroborate at ~1,900 km. Also found: **Sand Creek Wind (60595)**
   NERC MRO under `WAUW` — **not a defect**, WAPA Upper Great Plains West genuinely straddles the
   seam; canceled and inert, but it proves the NERC key does real work. And **Desert Bloom (69290)**,
   Maricopa County AZ, WECC, BA `DOPD` — **passes the predicate**, caught only by geography, proposed-
   only today and **live the moment it enters service**; consider a Western-Interconnection bounding
   test. **POST-ADJUDICATION FOOTPRINT, and this is the number your fleet load must reproduce:
   939 plants / 1,930 generators / 98,238.1 MW.**
 - **CURATED-FLEET SEAM — NWPP-10 §2 item (3) resolved it: EXTEND `eia860_generators.parquet` through
   its existing producer.** It is the fleet loader's own source (`data/fleet/eia860.py`,
   `EIA_860_PARQUET_NAME`), and `data/hydro.py`, `model/storage.py` and `data/announced_retirements.py`
   read it too; a missing NWPP fleet raises `FileNotFoundError`. `scripts/data/process_eia860.py:203`
   filters on `BA_CODE_TO_ISO`, so adding the 17 codes there and re-running extends the file, its
   retired-window twin and the `iso` column together. Do NOT read the raw pair as a special case.
 - **CENSUS CORRECTIONS from NWPP-10 §1.1 — use these, not the charter's §2.1 numbers where they
   differ:** gas ST **2,393.0** (not 2,163.0), gas ICE **737.5** (not 732.7), solar PV **10,051.3**
   (not 10,049.9), MT **6,939.6** (not 6,940.4). The three technology deltas sum to +236.2 MW out of
   the elided "other" residual and **the total is unchanged**. New from the same lane: summer
   **92,199.2 MW** / winter **96,596.1 MW**; **seven** EIA-860 planned-retirement cohorts, not one.
 - AVRN and GRID serve ZERO load in all 26,295 hours (plan §2.5). Register them as supply-side
   members whose generation lands in card N5's ruled zone; they are not zone candidates. Assert
   their load share is exactly 0.0 and comment why.
 - NO capacity market: absent from MARKET_DESIGN, _CURVE_ISOS, _CAPACITY_ISOS — document the absence
   as deliberate rather than leaving it to be read as an oversight (card N7).
 - NO import node: neither IMPORT_TRANCHES["NWPP"] nor IMPORT_ZONE["NWPP"] (gate G7).
 - Offer-curve bands stay 1.0 (gate G5): the rule 1 [R-STRUCT] carve-out authorizes tuning MARKET
   OFFERS, and most of this footprint is cost-based vertically-integrated dispatch.
 - **TIMEZONES (card N6) — RESOLVED BY MEASUREMENT, not ruled.** `BA_TIMEZONE` gains 14 ×
   `America/Los_Angeles` + 3 × `America/Denver` (NWMT, PACE, WAUW). **`IPCO` takes
   `America/Los_Angeles`, NOT `America/Boise`** — measured: at UTC 2023-07-28 08:00 IPCO stamps 01:00
   while PACE stamps 02:00. All 6 DST transitions present and correctly signed; every BA carries
   26,304 unique UTC hours and exactly 3 duplicated LOCAL timestamps. **CONVENTION: UTC is the
   canonical hour and the only admissible join key; local time is provenance only.** Gate G19 is
   closed on the data side.
 - **ADEQUACY (card N7) — RULED: ONE SCALAR, DECLARED.** One `PLANNING_RESERVE_MARGIN_BY_ISO["NWPP"]`
   from the participant IRPs, tested against the footprint **coincident** peak (summer in all three
   years). **DECLARE the two-regime mismatch in the config docstring at full magnitude** — 8 winter /
   6 summer / 1 flipping BA; NWPP-NW winter (0.86/0.80/0.82) against NWPP-SNV summer (1.95/2.06/1.87×
   its own winter load); NWPP-INLAND mixes both regimes inside one zone. Do NOT extend the registry to
   per-zone seasonal PRM — that is pre-declared lever **NWPP-57**, and it would move a dict all nine
   regions read to fix something that binds in no scored year. **WRAP is forecast-side only**: first
   binding season Winter 2027–28 (WPP BPM 109 p. 4), two years past the window.
 - TTCs per card N5's ruling: published WECC path ratings where NWPP-12 found one, Tier-3 with the
   misalignment stated on the link where it did not — exactly as _spp_config states SPP's.
 - **TAIL_THRESHOLD: NWPP-13 READ NO, so SKIP ALL THREE COPIES** and document the skip where a reader
   will hit it (gate G6). The gate failed on D3, not D2: WEIM cleared the volume bar (5.5–6.2 % net,
   10.6 % pairwise-gross) but its on-peak price sits **22.6 / 23.6 / 37.5 % below** the Mid-C Peak
   traded index against a pre-registered ±10 % bar. Nothing was landed to `_validation-source`, and a
   neighbouring hub stays refused (gate G17). Do NOT invent a threshold and do NOT substitute a hub.
 - DATA PROFILE TOKENS (gate G3): `ava`, `grid`, `pge` and `wpp` are ALL REFUSED as bare tokens —
   they steal five other ISOs' availability files, fleet-egrid, CAISO's pge-helms record and SPP's
   SWPP files respectively. Use `nwpp` plus delimiter-bounded forms, RE-MEASURE the trap at your own
   base sha, and pin it with a unit test.

FILES YOU MUST NOT TOUCH: frontend/data/forecast/**; any other ISO's keeper shard, log or matrix
shard; docs/codebase-site/data/mechanism-matrix/** (NWPP-21's); any soco* file; this plan; the ledger.
EXIT: get_iso_config("NWPP").validate_topology() green; the full unit+curation suites green; the
§2.3 checklist reported row by row with its verification; the cache-key proof; the BA_CODE_TO_ISO
inversion audit; FINDING-nwpp-20.
```

#### NWPP-21 `[OPUS]` — the matrix shard, the ev key, the colour

```
You are lane NWPP-21. MODEL: Opus claude-opus-5 — a mechanical emission against a validated schema.
DATA PROFILE: code.  Branch stem: claude/nwpp-21-matrix-<4 chars>.
Read CLAUDE.md rule 28 [R-MECH-MATRIX] in full; docs/mechanism-testing-matrix.md;
scripts/lib/mech_matrix.py; docs/codebase-site/data/mechanism-matrix/SPP.js (your template — the
seventh shard, emitted by lane SPP-21); scripts/check_mechanism_matrix.py;
docs/multi-iso/nwpp-addition-plan-2026-09.md §0 and §3 (the ev-key default).

BEFORE YOU START: read the base file's `isos` list and mech_matrix.ISO_ORDER AT YOUR OWN BASE SHA and
report what you found. The SOCO program may have added a shard since this charter (plan §0), so
"the eighth shard" may be wrong by one. Never hard-code the count from the charter.

ONE COMMIT (gate G2 — a shard missing an id hard-errors, and a half-landed matrix breaks every lane's
rule-28 duty in every ISO):
 - docs/codebase-site/data/mechanism-matrix/NWPP.js — a cell for EVERY mechanism id in the base file,
   all `U` (untested) except where a mechanism is structurally n/a for NWPP, which is `·` with its
   reason (no capacity market, no import node, no reserve co-optimisation, no offer-curve tuning
   channel);
 - the base file's `isos` list; scripts/lib/mech_matrix.py ISO_ORDER and ISO_EV_KEY — use **"W"**
   (measured taken at charter: E C P M N Q S; SOCO's charter claims O); the mechanism-matrix.html
   tag; tests/unit/config/test_mechanism_matrix_shard_migration.py's expected set;
 - the dashboard colour: an --iso-nwpp token in docs/codebase-site/css/shared.css (the existing block
   is lines 78-84) and its use in js/backcast-runs.js, following the --iso-spp precedent;
 - docs/mechanism-testing-matrix.md §5: the NWPP lever queue, seeded from this plan's W5 list
   (NWPP-54 Columbia hydraulic coupling, NWPP-55 WECC path TTC derive, NWPP-56 priced seams,
   NWPP-57 WRAP adequacy, NWPP-58 zone refinement, NWPP-59 retirement sector gate).
Verify with scripts/check_mechanism_matrix.py and paste its OUTPUT, not its exit code (gate G15).
FILES YOU MUST NOT TOUCH: any other ISO's shard CELL VALUES (you add NWPP's column, you never edit
another ISO's verdict); src/; frontend/data/**; any soco* file.
EXIT: FINDING-nwpp-21 with the checker output and the shard's cell census (n ids, n `U`, n `·`).
```

### W3–W6 — charters issued at the sittings that unblock them

The desk issues these against the SPP program's own W3/W4 charters, which are committed and worked
(`docs/multi-iso/spp-addition-plan-2026-09.md` §8 W3/W4). The NWPP deltas each charter must carry:

- **NWPP-30** (outages + tranches) `[OPUS]` — ID/OR/UT/WA CEMS only landed in W1; the per-plant
  binning recipe is `docs/binning-methodology.md`. **State the coverage arithmetic at the top**: on
  a fleet 36.3 % hydro + 24.9 % VRE + 1.2 % nuclear, CAMPD reaches ~32 % of nameplate (NWPP-10
  measures the exact figure), so this artifact governs far less of the fleet than in ERCOT or SPP.
- **NWPP-31** (benchmarks) `[OPUS]` — `build_reference --isos NWPP` **merges**, so non-NWPP rows must
  diff to ∅ (gate G9); `actual_lmp.json` gets an NWPP block **only if NWPP-13 landed a series**, and
  the determination-side consequence of it not landing is card N2's ruling, applied here.
- **NWPP-32** (hydro budget) **`[FABLE]`** — the monthly-budget layer, and **NWPP-36's input**. Build
  the monthly energy budget and power envelope for all 288 conventional-hydro plants from NWPP-11's
  EIA-923 extract; exclude the 314.0 MW of pumped storage by design. Add a
  `HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT["NWPP"]` entry **only where a published instrument justifies
  one** — the NYISO precedent is two plants with a treaty and an IJC directive behind them (plan §2.7),
  and "the Columbia is complicated" is not an instrument. **Measure and restate the four §2.7
  constraints with their magnitude**: under owner ruling N3 the first of them is no longer a declared
  gap but NWPP-36's specification, so this lane's measurement is what that lane is built against.
- **NWPP-36** (Columbia mainstem hydraulic coupling) **`[FABLE]`, W3b — INSERTED BY OWNER RULING N3**
  and W4 does not start without it. Build the coupling as ONE new **default-OFF** `ScenarioConfig`
  field registered on `_CACHE_KEY_OPTIONAL_FIELDS` **and** `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` in the
  same commit — copy `hydro_budget_period_by_instrument` (lane nyiso-220, the first entry in that
  tuple), which is the worked precedent for a default-off hydro field that moves no keeper's key. The
  charter must fix, **before any code**: which plants are in the chain and on what published evidence
  (the desk measured eight ≥ 1 GW plants and 288 in total — the chain is a hydrological fact to be
  cited, not a list to be chosen); the travel-time or balance formulation; and what the mechanism does
  at the LP row level, vectorized (rule 2 `[R-VECTOR]` — no Python loop over hours). It adds a
  `mechanism-matrix.js` base row plus one `·` cell line per foreign shard in the same PR (rule 28(c)).
  **Exit: the coupling arms, and is byte-identical OFF; every existing keeper's `cache_key()` proven
  byte-identical** (gate G8 as amended).
- **NWPP-33** (zonal shares, VRE shape, gas hub) `[OPUS]` — shares from the committed per-BA 930
  series (§2.5), **not** sub-BA and **not** state; per-zone gas basis per NWPP-12's finding (this
  footprint prices against several hubs, not one).
- **NWPP-34** (seam derive) `[OPUS]` — served EIA-930 `Total interchange` (card N4). **Carries the
  CAISO double-count notice**: it derives NWPP's side only, and the CAISO-side question is routed,
  not fixed here (rule 25 `[R-ISO-SCOPE]`).
- **NWPP-35** (site + docs) `[OPUS]` — region-count prose (re-read at its own sha, §0),
  `--iso-nwpp` colour, `docs/calibration-log/nwpp.md` header.
- **NWPP-40** (first solve) **`[FABLE]`, gated on NWPP-36** — **ONE shard, ONE `--year 2023 2024 2025`, ONE bundle**
  (rule 32(b)); the shard pushes its bundle to its own branch (rule 34); the PRECOMMIT states the
  price posture from card N2 and the hydro posture from card N3 **before** the solve, names the 30
  defective demand hours (gate G20), and budgets memory explicitly (gate G21 — this is the largest
  per-plant LP in the repo). The promotion question is asked **in-session** (rule 31).

---

## 9. Findings index

| Lane | FINDING | Landed |
|---|---|---|
| charter | this plan + `docs/handoffs/nwpp-desk-handoff-2026-09-13.md` + `nwpp-desk-ledger-2026-09.md` | 2026-09-13 |

## 10. Ledger

`docs/handoffs/nwpp-desk-ledger-2026-09.md` — live state, scoreboard, rulings, routed items,
collision register, issuance record, errors against interest.
