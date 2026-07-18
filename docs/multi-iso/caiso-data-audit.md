# CAISO Data Audit — Stage E / P0 (2026-06-11)

Status: **complete.** This is the Wave-0 data audit from the CAISO prompt
pack (doc 06, prompt P0), run per playbook §1–2. It records what is in the
repo today, what the calibration reference now carries for CAISO, the fleet
sanity check against published totals, CEMS state coverage, and the open
items mapped to the doc-06 upload manifest (U1–U7).

---

## 1. Calibration reference — extended for CAISO 2023–2025

`scripts/data/build_calibration_reference.py` now derives CAISO alongside
ERCOT/PJM. CAISO uses a per-ISO year override (`CALIBRATION_YEARS_BY_ISO`,
2023–2025 only — the doc-06 target years); ERCOT/PJM keep 2021–2025.

Written artifacts:

- `data/raw/_validation-source/calibration_reference.json` — CAISO blocks for
  2023/2024/2025: EIA-930 demand stats (from `data/eia_hourly/CISO
  hourly.parquet`), measured Henry Hub, EIA-923 by-fuel `generation_twh`,
  EIA-860 wind/solar December totals + NP15/ZP26/SP15 zone shares + monthly
  ramps, and the eGRID 2023 `BACODE=CISO` generation/emissions benchmark.
- `data/raw/_validation-source/CAISO_{2023,2024,2025}_renewable_capacity.csv` —
  per-zone, per-month EIA-860 operable wind/solar capacity.

Headline reference values:

| Year | Demand (TWh) | Peak (MW) | Wind Dec (MW) | Solar Dec (MW) | EIA-923 gas cc/ct/st (TWh) | Nuclear (TWh) |
|---|---|---|---|---|---|---|
| 2023 | 218.1 | 44,007 | 6,149 | 20,407 | 66.3 / 8.4 / 1.4 | 17.7 |
| 2024 | 224.0 | 47,571 | 6,288 | 23,095 | 59.2 / 8.4 / 0.2 | 18.4 |
| 2025 | 224.0 | 43,860 | 6,326 | 24,919 | 50.2 / 4.9 / 0.1 | 17.6 |

### 1a. Zone-lookup supplement (code change in this session)

The eGRID-2023 ORIS→zone lookup cannot know plants that came online after
the eGRID vintage, and `EIA860_OPERABLE_VINTAGE` is now 2025 (so the
proposed-plant augmentation no longer covers 2024/2025 either). Before this
session, CAISO 2024/2025 silently dropped every post-2023 greenfield plant
(~2.6 GW of 2024 solar and ~2.2 GW of 2025 solar — a quarter of the fleet
in the exact years the backcast targets). Fix: the existing ERCOT-only
EIA-860-plant-file supplement in `zone_assignment.build_zone_lookup()` is
generalized (`_EIA860_SUPPLEMENT_ISOS = {ERCOT, CAISO}`) — plants in the
CISO balancing authority missing from eGRID are zoned by lat/lon from
`eia860_plant.parquet`. Gated per ISO, so PJM (and ERCOT, whose path is
functionally unchanged) cannot move.

### 1b. Regression guard — verified, with one finding

The new script was diffed against the pre-change script **run in the same
environment**: all ten ERCOT/PJM renewable-capacity CSVs and both JSON
blocks are byte-identical between the two. The committed ERCOT/PJM outputs
were left untouched.

**Finding (backlog, ERCOT/PJM-owned):** regenerating the reference at HEAD
shifts ERCOT/PJM renewable capacity slightly (e.g. ERCOT 2023 wind Dec
total 36,731 → 36,980 MW) regardless of this session's change, because
commit `b487a5d` rebuilt the EIA-860 parquets from the 2025 Early Release
*after* the reference was last generated (2026-05-22). The committed
ERCOT/PJM blocks are therefore one EIA-860 vintage stale. Re-baselining
them belongs to an ERCOT/PJM calibration session (doc-06 §6 E/J backlog),
not a CAISO pack.

### 1c. Known caveats on the CAISO blocks

- **2025 `generation_twh` is a lower bound.** The `f923_2025` zip is the
  early-release M-file (Dec-2025 vintage, published Feb-2026); annual-only
  respondents are absent. CISO wind has just 19 reporting rows vs 108 in
  the final 2024 file → 4.2 TWh reported vs ~15 TWh expected; solar is
  ~20% light for the same reason. All 12 months are present — this is
  respondent coverage, not a partial year. Re-run the script when the
  final 2025 EIA-923 lands. (ERCOT/PJM 2025 blocks carry the same caveat,
  proportionally smaller because their fleets skew to monthly reporters.)
- **Demand is net load** (playbook §8.1): EIA-930 CISO demand is net of
  ~15+ GW BTM PV. Backcasts model front-of-meter resources only.
- The eGRID benchmark maps GEOTHERMAL into `other` (~8.2 TWh of CISO
  `other` generation is The Geysers et al.) — see §2c.

---

## 2. Fleet sanity — `get_iso_config("CAISO")` + CISO BA filter

`load_fleet_from_csv("CAISO", ...)` (the `plant_level_fleet` path used by
the calibration harness):

- **782 LP generators, 344 distinct plants, 32,010 MW** thermal/other:

| Class | MW | Units |
|---|---|---|
| gas_cc | 16,415 | 148 |
| gas_ct | 12,437 | 424 |
| nuclear | 2,240 | 2 |
| biomass | 746 | 180 |
| oil | 123 | 26 |
| coal | 50 | 2 |

- **Zone distribution:** NP15 12,810 / ZP26 3,913 / SP15 15,287 MW.
  **No unassigned plants** — zero fallback-zone warnings on assembly
  (the §1a supplement also closes the new-plant hole for fleet assembly).
- **States:** CA 31,700 MW (343 plants) + NV 310 MW (1 plant — Desert
  Star Energy Center, ORIS 55077, gas-CC near Boulder City; in the CISO
  BA per EIA-860). Doc-06 design decision 2 keeps other CAISO-owned
  out-of-state resources (Palo Verde shares etc.) inside the import curve.
- **Coal is negligible as expected:** 2×25 MW at Argus Cogen (Trona,
  ZP26) — confirms the doc-06 "no coal must-run layer" premise.

Companion fleets (loaded by their own machinery, reported here for the
totals comparison):

- **Hydro** (`_hydro_fleet`, EIA-923 reporters): 2023 — 166 plants,
  6,433 MW, 23.9 TWh budget; 2024 — 160 plants, 6,568 MW, 21.5 TWh.
  Wet-2023 > 2024 ✓; eGRID 2023 CISO hydro generation is 23.4 TWh ✓.
- **Pumped storage** (`load_eia860_pumped_storage`): 2,078 MW (all NP15;
  Helms 1,212 MW dominates).
- **BESS** (EIA-860 energy-storage operable, CISO via zone lookup):
  **7,492 MW end-2023 → 11,131 MW end-2024 → 15,448 MW end-2025**;
  zones NP15 1,912 / ZP26 3,697 / SP15 9,840 MW.
- **Wind/solar:** §1 table (6.1–6.3 GW wind; 20.4–24.9 GW solar).

### 2a. Comparison vs published totals

| Class | Model | Published benchmark | Verdict |
|---|---|---|---|
| Gas | 28,852 MW (pmax) | eGRID 2023 CISO: 33,841 MW nameplate, 286 plants (in-repo workbook) | −15% vs nameplate; pmax≈summer rating, plus QF/CHP and 2023-retirement edge cases. 923 cross-check: model benchmark gas 76.0 TWh vs eGRID 77.9 TWh (−2.4%) ✓ |
| Nuclear | 2,240 MW | Diablo Canyon, 2,256 MW NQC (CAISO NQC list) | ✓ |
| Wind | 6,149–6,326 MW | eGRID 2023 CISO: 6,209 MW | ✓ |
| Solar | 20,407 (2023) → 24,919 MW (2025) | eGRID 2023: 23,926 MW (incl. hybrid PV components) | 2023 −15% vs eGRID; hybrid co-located PV is partly held in the storage tables — reconcile in P5/P6 |
| BESS | 11,131 MW end-2024; 15,448 end-2025 | CAISO DMM 2024 Special Report on Battery Storage: ~13,000 MW active Dec-2024 (5,800 standalone + 5,700 co-located + ~1,500 hybrid components); FERC State of the Markets 2024: 8.0→11.6 GW over 2024; Modo Energy: ~12 GW end-2024, >15 GW end-2025 | end-2024 within 4% of FERC, −14% vs DMM (which counts hybrid storage components); end-2025 ✓ vs Modo |
| Hydro + PS | 6,568 + 2,078 = 8,646 MW | eGRID 2023 CISO HYDRO: 8,819 MW (incl. PS) | −2% ✓ |
| Geothermal | — (no fleet class) | eGRID 2023 CISO: 2,148 MW, ~8 TWh/yr | see §2c |

Sources: [CAISO 2024 Special Report on Battery Storage (May 29, 2025)](https://www.caiso.com/documents/2024-special-report-on-battery-storage-may-29-2025.pdf);
[FERC State of the Markets 2024 (Mar 2025)](https://www.ferc.gov/sites/default/files/2025-03/25_State-of-the-Market_0320_1200.pdf);
[Modo Energy — CAISO battery fleet crosses 15 GW](https://modoenergy.com/research/en/caiso-battery-fleet-2025-q4-15gw-interconnection-queue-standalone-colocated);
EPA eGRID 2023 (`data/fleet/egrid2023_data_rev2 2.xlsx`, PLNT23, BACODE=CISO).
Note: caiso.com (and EIA/CPUC hosts) return 403 from this environment, so
the DMM annual-report and NQC-list gas-fleet MW figures could not be pulled
directly; the eGRID workbook already in the repo serves as the published
EPA benchmark. Pulling the exact NQC gas total is a one-line check for
whoever has browser access (2024 Summer Loads & Resources Assessment,
Table 2.1).

### 2b. gas_st note

The loader currently classifies CISO gas steam units into `gas_ct` (424
gas_ct units include the ST_GAS-style steamers); the EIA-923 benchmark
carries a separate `gas_st` row (1.4 TWh 2023 → 0.1 TWh 2025 — the last
once-through-cooling steamers aging out). P2 should make sure spiky
ST_GAS runners land on the peaker exclusion list per the prompt.

**P2 resolution (2026-06-11):** the three ST_GAS-group plants — AES
Alamitos LLC (315, legacy boilers 3–5), AES Huntington Beach LLC (335,
boiler 2) and Ormond Beach (350) — are on `outages.ST_GAS_PEAKER_PLANTS`.
CAMPD 2024–25 shows them online only 0.4–2.5% of hours (run-when-called
OTC reliability units), so the event-based detector had flooded them with
economic-idleness "outage" windows (126 of the extract's 1,386 rows); they
now carry no outage overlay and no reliability floor, dispatching purely
economically. Their measured committed floors (5.8–8.9%) stay recorded in
`thermal_tranches_CAISO.csv`.

### 2c. Geothermal (CAISO-specific, no ERCOT/PJM precedent)

CISO has ~2.1 GW / ~8 TWh-yr of geothermal (The Geysers, Imperial Valley)
— bigger than biomass+oil+coal combined. It is not a thermal fleet class;
today it flows through the biomass/OTHER must-run injection in
`run_calibration_full.py`. EIA-930 carries a dedicated `NG: GEO` column
for CISO, so the injection can be benchmarked directly. P2/P3 should
confirm the OTHER injection reproduces the ~0.9 CF baseload shape rather
than a flat average — it is effectively part of CAISO's must-run layer
(doc-06 design decision 4).

**P2 verification (2026-06-11):** confirmed, with one correction to the
benchmark claim above.

- **The injection carries the right energy and a baseload shape.** All 14–15
  CISO geothermal plants classify to `OTHER` (`classify_plant('GEO', …)`)
  and are injected by `_must_run_profiles`: 8.05 TWh (2023) and 7.81 TWh
  (2024), matching eGRID's ~8 TWh, shaped by the EIA-923 monthly profile —
  a band of 871–969 MW (2023) / 835–926 MW (2024, min/max 0.90), flat
  within each month. It is *not* a flat annual average: refuel/maintenance
  months (e.g. May 2024, 835 MW) sit visibly below the band top.
- **The dedicated EIA-930 `GEO` column is empty until mid-Dec 2025** —
  same new-schema pattern as the battery column (§U8). For 2023–24, CISO's
  geothermal is folded into the 930 *Natural Gas* aggregate (85.1 TWh in
  2024 vs ~68 TWh of actual gas; `Other Fuel Sources` is BESS-net,
  annual mean −130 MW, and carries no geothermal). Direct benchmarking is
  only possible for the ~16 populated days (Dec 16–31, 2025): 740 MW mean,
  hourly CV 4.4% — against the EIA-923-derived 2025 level of 746 MW.
  Agreement within 1%, and the flatness confirms the baseload shape.
- **On "~0.9 CF":** realized CF against the 2,148 MW eGRID nameplate is
  ~0.42 (The Geysers steam-field derate); the ~0.9 figure describes the
  *shape* — hourly output holds ≥90% of the fleet's running maximum
  essentially all hours — which the monthly-flat injection reproduces.
- 2025 caveat: the early-release EIA-923 M-file covers only 7 of 14
  plants (6.53 TWh lower bound); re-run when the final file lands (§1c).

---

## 3. CEMS coverage

Distinct states of CAISO-fleet fossil plants: **CA** (259 plants,
31.4 GW) and **NV** (1 plant: Desert Star, 310 MW summer / ~480 MW
nameplate gas-CC).

Diff against `data/raw/campd-unit-level/<ST>_<year>.parquet`:

| State-year | Unit-level | Facility-level | Notes |
|---|---|---|---|
| CA_2023 | **present** (U1 landed 2026-06-11) | present | feeds `campd-unit-outages-CAISO.csv` (612 outage windows) |
| CA_2024 | present | present | feeds `campd-unit-outages-CAISO.csv` (620 outage windows) |
| CA_2025 | present | present | 701 outage windows |
| NV_2023/24/25 | missing | missing | Desert Star only — see below |

**Non-CA CEMS obligations:** Desert Star (ORIS 55077) is the only non-CA
fossil plant in the CISO BA. As a >25 MW gas-fired unit it does carry Part
75 CEMS reporting, so `NV_{2023,2024,2025}` extracts *would* add measured
outage windows for it — but it is ~1% of CISO gas capacity. Verdict:
**optional, low priority**; statistical availability is acceptable. If NV
is uploaded anyway it is three small parquets and a `derive_campd_unit_outages.py
--iso CAISO` rerun (P1).

### Unit-outage detection coverage (P1, verified 2026-06-11)

`campd-unit-outages-CAISO.csv` (1,386 windows: 655 in 2024, 731 in 2025,
38 plants) regenerates **byte-identically** from the committed CA_2024/
CA_2025 extracts via `derive_campd_unit_outages.py --iso CAISO`. Every CA
CAMPD unit is gas-fired (234 pipeline-NG + 3 NG + 2 other-gas + 1 wood;
zero coal), so only the **event-based rule** (every-hour CF < 2%, ≥ 120 h)
fires; the coal real-run rule has no CAISO targets (the fleet's lone
COAL-group plant, Argus Cogen 10684 / 25 MW, has no CEMS extract). A
detector replay on the 5 largest plants (Alamitos, Ormond Beach, Moss
Landing, La Paloma, Mountainview + Delta Energy Center) reproduced the CSV
windows exactly, and the every-hour rule held inside each window. Known-
event check: all four Moss Landing CC units go dark **2025-01-16** for ~27
days — the Vistra battery fire that took the colocated gas plant offline.

Share of CAISO gas capacity (fleet pmax, 28.9 GW) with CEMS unit history:

| Class | Fleet MW | CEMS-covered |
|---|---|---|
| CC_REGULAR | 13,708 | 84% |
| CC_CHP | 2,707 | 51% |
| ST_GAS | 2,859 | 100% |
| CT_CHP | 1,962 | 17% (no overlay anyway) |
| CT_PEAKER | 7,616 | 79% (no overlay by design) |
| **All gas** | **28,852** | **77%** |
| **Overlay-eligible (CC + ST_GAS)** | **19,274** | **82%** |

The remaining 18% of overlay-eligible capacity stays on statistical
availability. Largest gaps: **AES Huntington Beach Energy Project (62116,
630 MW)** and **AES Alamitos Energy Center (62115, 603 MW)** — their CEMS
history exists but reports under the *legacy* ORIS codes (335 / 315), so
their windows currently route to the legacy ST_GAS boiler bins (which were
near-dead all year regardless) instead of the new CC_REGULAR bins. An
ORIS→EIA split-plant remap (like ERCOT's `_unit_outage_target`) would
recover them — follow-up candidate. Then El Segundo Energy Center (57901,
510 MW CC) and Desert Star (55077, NV — see above).

**P2 resolution (2026-06-11): the remap landed** as
`campd.CAMPD_UNIT_PLANT_REMAP` — units CT1/CT2 at ORIS 315 → EIA 62115 and
at ORIS 335 → EIA 62116, applied (a) row-wise wherever unit identity is
known (the unit-level extracts, hence `derive_campd_unit_outages.py`), and
(b) in `campd._read_one` for facility-level loads by substituting the
companion unit-level rows for the split facilities (gross conservation
verified to 0.1 GWh on CA 2024). The regenerated
`campd-unit-outages-CAISO.csv` (1,321 windows) carries 61 properly
attributed CC_REGULAR windows for 62115/62116; every row for a
non-touched facility is byte-identical to the P1 extract. CA 2023 has no
unit-level extract (U1), so 2023 facility-level loads keep the legacy
summing — the loader warns. AES CC_REGULAR CEMS coverage is now 95%+ of
class capacity; the largest remaining gaps are El Segundo and Desert Star
as above.

**P1-2023 resolution (2026-06-11): U1 landed, 2023 windows derived.**
`CA_2023.parquet` (245 units across 109 facilities; all gas/wood, zero
coal — same fuel mix as 2024/2025) is now in
`data/raw/campd-unit-level/`, and `derive_campd_unit_outages.py
--iso CAISO --years 2023 2024 2025` regenerated
`campd-unit-outages-CAISO.csv` to **1,933 windows (612 in 2023, 620 in
2024, 701 in 2025; 37 plants)**. The 2024 and 2025 rows regenerate
**byte-identically** (raw-text and value-level) against the committed
extract — the 2023 addition shifts nothing in the later years. As in
2024/2025, only the event-based rule fires (every CA unit is gas-fired).
A detector replay independent of the script, on the three largest CC
plants with 2023 windows — La Paloma (55151), Moss Landing (260),
Mountainview (358) — reproduced every 2023 window exactly, and the
every-hour CF < 2% rule held inside each one.

`unit_outage_derate_factors(2023, iso="CAISO")` now returns 30 derated
`(plant, group)` bins (was empty), so an `outage_source="historic"` CAISO
2023 fleet assembly **no longer logs the PR #300 "no outage windows cover
CAISO 2023" warning** (verified by capturing
`fleet.generators_to_fleet_arrays` logs). 2023 backcasts now carry
measured unit-outage availability rather than statistical-only.

---

## 4. Upload manifest status (doc-06 U1–U7)

| # | Item | Destination | Status |
|---|---|---|---|
| U1 | CAMPD unit-level `CA_2023.parquet` | `data/raw/campd-unit-level/` | **missing** — the only blocker for 2023 measured outages; facility-level CA_2023 exists as fallback |
| U2 | DA+RT hourly LMPs TH_NP15/TH_SP15/TH_ZP26, 2023–2025 | `data/raw/lmp-data/CAISO/` | **done (as available)** — see §4a. DA 2024+2025 and RT 2024+2025 are full years × 3 hubs; the `actual_lmp.json` CAISO block + `actual_lmp_hourly_CAISO.parquet` and the zonal-sufficiency test are built. **Gaps:** DA 2023 is a ~3-trade-date stub (OASIS ~39-month retention aged it out before the mid-2026 pull) and RT 2023 was never fetched, so there is no usable 2023 price year. OASIS gotcha (2026-06-11): multi-node `PRC_LMP` queries are silently truncated to the last ~2 trade dates (and a 31-day multi-node window errors), so pulls must be single-node; `scripts/data/fetch_caiso_oasis.py` automates the full download (resumable, adaptive windows, run from an unrestricted machine) and `scripts/data/postprocess_oasis_downloads.py` folds the raw windows into the committed hourly aggregates |
| U3 | Wind & solar production-and-curtailment, 2023–2025 | `data/raw/caiso-curtailment/` | **done (as available)** — official 5-min Production+Curtailments workbooks; 2023 (2.66 TWh curtailed) and 2024 (3.42 TWh, matches EIA's published 3.4) are full years; the 2025 workbook is internally inconsistent as published: its Production sheet is the full year (105,120 five-min intervals through Dec 31 — usable for P6/P9 benchmarks), but its Curtailments sheet physically ends 2025-05-31 (verified at the raw sheet-dimension level; re-download byte-identical 2026-06-11). Jun–Dec 2025 curtailment would have to come from the daily curtailment PDFs if ever needed |
| U4 | TAC-area actual hourly load (PGE/SCE/SDGE) | `data/raw/zone-specific-demand/CAISO/` | **partial, wired** — 2023-01 landed (OASIS `SLD_FCST` ACTUAL, verified: 24 h/day for PGE-TAC/SCE-TAC/SDGE-TAC + CA ISO-TAC); remaining months 2023-02 … 2025-12 pending. Already consumed: static `load_share` is now measured from this sample (NP15 0.3969 / ZP26 0.0646 / SP15 0.5385 via `scripts/data/derive_load_shares.py caiso`; PGE-TAC split 0.86/0.14 onto NP15/ZP26, SCE+SDGE+VEA→SP15) and `eia_loader.caiso_zonal_load_shares` serves measured hourly zonal shapes for covered hours (sample-average shares elsewhere). Refresh = drop the remaining monthly pulls into `CAISO_tac_load_hourly_<year>.csv`; shapes upgrade automatically |
| U5 | Path 15/26 hourly flows + limits (optional) | `data/raw/iso-specific-transmission/CAISO/` | **missing** — TTCs stay on WECC-catalog Tier-3 seeds |
| U6 | CARB cap-and-trade auction prices 2023–2025 (optional) | cite into `constants.py` | **not yet in repo** — public auction results are web-searchable from this environment, so P7 can self-serve; no upload strictly required |
| U7 | CA BTM PV + storage trajectory (optional, forecast P13) | `data/raw/caiso-btm/` | **missing** — backcast unaffected (net-load convention) |

Additional gap found (not in the original manifest):

- **U8: EIA-930 six-month BALANCE parquets — complete.** All six halves
  (2023/2024/2025) in `data/raw/eia-930/`, validated 2026-06-11:
  CISO demand reconciles with `data/eia_hourly/CISO hourly.parquet`
  (2023: 218.13 vs 218.14 TWh; 2024: 222.87 vs 224.03 — raw vs adjusted
  demand plus 48 NaN raw hours; same pattern 2025). EIA switched schema
  mid-2024: 2023 + 2024-H1 are the old 44-column layout, 2024-H2 + 2025
  the new 65-column layout. Key finding: CISO never populates the
  dedicated `Battery Storage` column in the new schema (15 other BAs
  do) — CISO batteries live inside **`Other Fuel Sources`**, whose
  hourly swings (−7.4 GW midday charge to +9.4 GW evening discharge in
  2025; −6.7/+7.4 in 2024-H2) are unmistakably the BESS fleet plus a
  small geothermal/biomass baseload. P5's cycling benchmark should use
  the CISO `Other` series net of an estimated baseload in every year,
  not a battery column. Minor: prefer the `(Adjusted)` demand columns
  (raw has 24 NaN hours per 2025 half, 48 in 2024-H2, 2 in 2023-H2).

### 4a. LMP benchmark + zonal-sufficiency (U2 / P10, 2026-06-11)

**Aggregates.** `scripts/data/postprocess_oasis_downloads.py` folds the OASIS raw
window CSVs into the committed hourly aggregates and is idempotent/rerun-safe
(one command re-ingests any future drop; overlapping fetch windows dedupe on
the `(timestamp, node|tac_area)` key). Current coverage:

| Series | 2023 | 2024 | 2025 |
|---|---|---|---|
| DAM (`CAISO_dam_hourly`) | ~3 trade dates (retention stub) | full, 366 d × 3 hubs | full, 365 d × 3 hubs |
| RTM (`CAISO_rtm_hourly`) | **not fetched** | full × 3 hubs | full × 3 hubs |
| TAC load (`CAISO_tac_load_hourly`) | Jan only (hand-downloaded `SLD_FCST`) | full × 5 TACs | full × 5 TACs |

The 126 raw RTM/load window files were staged out in commit `a81eb80`; the
aggregates are the repo's record. The 2023 DAM/RTM gap is OASIS retention
(~39 months — by mid-2026 only late-Feb-2023 survives) and an unfetched RT
2023; not recoverable from OASIS now.

**Calibration reference.** `scripts/data/derive_actual_lmp.py` grew a CAISO
builder alongside ERCOT/PJM (ERCOT/PJM outputs regenerate byte-identically —
regression-checked). CAISO has no single system hub, so the
comparable-to-the-model system price is the three trading hubs **load-weighted
by zone share** (NP15 0.3969 / ZP26 0.0646 / SP15 0.5385, the
`config.iso_configs` `load_share` values), indexed onto the model's
chronological fixed-PST calendar (since the 2026-07-15 all-ISO scoring-clock
fix; the original landing indexed the Pacific prevailing wall clock, which
paired DST hours one real hour off). Written:

- `data/raw/_validation-source/actual_lmp.json` CAISO block — DA + RT **2024 & 2025**
  annual/monthly means + `da_pct`/`rt_pct` duration-curve percentiles
  (2024 DA $35.81 / RT $32.94; 2025 DA $34.62 / RT $33.63). 2023 is omitted:
  a full-year gate (`CAISO_MIN_HOURS`) rejects the DAM stub, and RT 2023 is
  absent.
- `data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet` — the dense
  fixed-8760 system DA/RT series (2 years) for the duration-curve overlay
  (`scripts/archive/analyze_lmp_residual.py`).

**Zonal-sufficiency test (design decision 3).** Full write-up in
`caiso-zonal-adequacy.md`; reproduce with
`scripts/caiso_zonal_sufficiency.py`. Conclusion: **keep 3 zones.** The DA
NP15−SP15 spread exceeds $20/MWh in 16.8% (2024) / 10.3% (2025) of hours
(p99 $46–66), with NP15 the dear side 98–99% of the time and the separation
concentrated in solar shoulder months (Mar–May, Oct–Nov) and midday hours —
Path 15 north-south congestion a single zone cannot reproduce. SP15 and ZP26
move together (>$20 only 0.7–1.3% of hours), so the load-bearing split is
NP15-vs-South; the next refinement lever is the Path 15 TTC (U5), not more
zones.

## 5. Present and verified (do not re-acquire)

- `data/eia_hourly/CISO hourly.parquet` — 2023-01-01 → 2025-12-31, demand
  + forecast + net gen + total interchange + 9 fuel columns (incl. GEO).
- `data/raw/CISO_fueltype.parquet`, `CISO_region.parquet`.
- EIA-860 2025 ER parquets (incl. energy-storage tables), EIA-923 zips
  2023/2024/2025, eGRID 2023 + 2024 workbooks, Henry Hub series.
- CAMPD: unit-level CA 2024/2025, facility-level CA 2023–2025, derived
  `campd-unit-outages-CAISO.csv` (2024–2025).
- Topology/config: `_caiso_config()` (NP15/ZP26/SP15 + WECC_import, VOLL
  $2,000), WECC import machinery, CAISO RA in the market-design registry,
  `GAS_BASIS_DIFFERENTIAL["CAISO"]` seed.
- Calibration reference + per-year renewable CSVs (this session).

## 6. Out-of-scope observations for the backlog

- ERCOT/PJM calibration-reference staleness vs EIA-860 2025 ER (§1b).
- `tests/test_fuel.py::test_coal_supply_pricing_uses_year_trajectory`
  fails on a clean checkout — the known stale test flagged in doc-06 §6
  (E1); unrelated to this change (756 other tests pass).
- `_add_proposed_capacity` hardcodes `assign_zone_by_coords(lat, lon,
  "ERCOT")`; latent (only ERCOT is in `_ISO_HOME_STATES`) but should take
  `iso` when another ISO ever opts into the proposed augmentation.
