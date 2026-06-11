# NEISO (ISO-NE) Data Audit — Stage E / P0 (2026-06-11)

Status: **complete.** Wave-0 data audit from the NEISO prompt pack (doc 08,
prompt P0), run per playbook §1–2. Records what is in the repo today, what the
calibration reference now carries for NEISO, the fleet sanity check against
ISO-NE CELT/RSP, CEMS state coverage, and the open items mapped to the doc-08
upload manifest (U1–U7). Done together with the NYISO audit
(`nyiso-data-audit.md`) in one pass — both ISOs share
`scripts/build_calibration_reference.py` + `calibration_reference.json`.

---

## 1. Calibration reference — extended for NEISO 2023–2025

`scripts/build_calibration_reference.py` now derives NEISO (and NYISO)
alongside ERCOT/PJM/CAISO. NEISO uses a per-ISO year override
(`CALIBRATION_YEARS_BY_ISO["NEISO"] = (2023, 2024, 2025)`) with BA code `ISNE`
— NEISO has the most complete CEMS coverage of the new ISOs, so all three years
are first-class.

Written artifacts:

- `inputs/calibration/calibration_reference.json` — NEISO blocks for
  2023/2024/2025: EIA-930 demand stats (`data/eia_hourly/ISNE hourly.parquet`),
  measured Henry Hub, EIA-923 by-fuel `generation_twh` (now including **hydro**
  and the **oil** columns — ISO-NE burns real oil in winter — see §1a), EIA-860
  wind/solar December totals + 4-zone shares + monthly ramps, and the eGRID
  2023 `BACODE=ISNE` generation/emissions benchmark.
- `inputs/calibration/NEISO_{2023,2024,2025}_renewable_capacity.csv` —
  per-zone, per-month EIA-860 operable wind/solar capacity.

Headline reference values:

| Year | Demand (TWh) | Peak (MW) | HH ($/MMBtu) | Wind Dec (MW) | Solar Dec (MW) | EIA-923 gas cc/ct/st (TWh) | Nuclear (TWh) | Hydro (TWh) | **Oil (TWh)** |
|---|---|---|---|---|---|---|---|---|---|
| 2023 | 112.0 | 23,475 | 2.54 | 1,536 | 2,924 | 54.3 / 1.9 / 0.4 | 23.2 | 8.5 | **0.39** |
| 2024 | 114.4 | 24,255 | 2.19 | 1,536 | 3,354 | 58.6 / 2.1 / 0.3 | 26.5 | 6.7 | **0.31** |
| 2025 | 115.3 | 25,898 | 3.52 | 1,721 | 3,618 | 51.3 / 0.8 / 0.3 | 27.6 | 0.1 | **0.91** |

eGRID 2023 ISNE benchmark (headline): gas_cc 53.1 TWh / gas_ct 4.3 TWh
(eGRID heat-rate CC/CT split; 923's prime-mover split is the more reliable
class benchmark), hydro 8.2 TWh, nuclear 23.2 TWh, oil 0.18 TWh, coal 0.16 TWh,
biomass 5.53 TWh; CO2 totals gas_cc 20.10 + gas_ct 1.89 + biomass 2.67 +
oil 0.18 + coal 0.17 ≈ **25.1 Mt**.

### 1a. Hydro + oil added to the EIA-923 benchmark (code change this session)

The shared `_eia923_generation` masks previously emitted only
coal/gas_cc/gas_ct/gas_st/nuclear/wind/solar. For NEISO the **oil** column is
first-order (ISO-NE's winter dual-fuel burn, doc-08 design decisions 1–2) and
hydro is worth tracking. Two scoped additions:

- **hydro** = EIA-923 fuel code `WAT` + prime mover `HY` (conventional hydro
  only; pumped storage `WAT`/`PS`, which nets negative, is excluded — it is
  storage, not energy, per doc-08 design decision 5).
- **oil** = fuel codes `DFO`/`RFO`/`JF`/`KER`/`WO`/`PC`, any prime mover.

Gated through `_EIA923_EXTRA_FUELS_BY_ISO = {NYISO, NEISO}`, so the
already-calibrated ERCOT/PJM/CAISO `generation_twh` blocks are untouched. eGRID
already mapped `HYDRO`/`OIL` generically, so the benchmark needed no change
beyond the new `NYIS`/`ISNE` BACODE entries.

### 1b. Regression guard — verified, with the known ERCOT/PJM drift finding

The merged `calibration_reference.json` was diffed against the committed
version: **every ERCOT/PJM/CAISO block and all top-level fields are
byte-identical** (zero removed/changed lines; only the NYISO/NEISO `isos` and
`egrid_benchmark` entries are added). The committed ERCOT/PJM/CAISO
renewable-capacity CSVs were left untouched.

**Finding (backlog, ERCOT/PJM-owned — same item as caiso-data-audit §1b):**
re-running the script at HEAD *would* shift the committed ERCOT/PJM blocks,
because the ERCOT topology gained a `Northeast` zone (committed ERCOT CSVs carry
6 zones, current `iso_configs` has 7) and the EIA-860 parquets were rebuilt,
both *after* the ERCOT/PJM reference was last generated (2026-06-10). To honor
the byte-identical guard this session **preserved** the committed
ERCOT/PJM/CAISO blocks verbatim (load committed JSON → insert only NYISO/NEISO →
re-dump) and restored the ERCOT/PJM CSVs from HEAD. Re-baselining ERCOT/PJM
belongs to an ERCOT/PJM calibration session. CAISO (regenerated 2026-06-11)
reproduces byte-identically.

### 1c. Known caveats on the NEISO blocks

- **2025 `generation_twh` is a lower bound.** The `f923_2025` zip is the
  early-release M-file; annual-only respondents are absent. ISNE shows it
  starkly: only **322 reporting rows** vs ~1,700 in the final 2023/2024 files,
  with just **6 hydro rows** (vs ~170) → 2025 hydro reads 0.09 TWh (vs 8.5 in
  2023) and solar 1.02 TWh (vs 4.53 in 2024). All 12 months are present — this
  is respondent coverage, not a partial year. Demand (EIA-930) is complete;
  only the 923 by-fuel mix is preliminary. **P11/P12 must treat the 2025
  fuel-mix targets (especially hydro/solar/oil) as preliminary** and re-run the
  script when the final 2025 EIA-923 lands. (ERCOT/PJM/CAISO/NYISO 2025 carry
  the same national caveat; ISNE is hit hardest because its early-release skews
  hard to the large gas/nuclear monthly reporters.)
- **Demand is net load** (playbook §8.1): EIA-930 ISNE demand is net of MA/CT's
  material BTM PV wedge. Backcasts model front-of-meter resources only.

## 2. Fleet sanity — `get_iso_config("NEISO")` + ISNE BA filter

`load_fleet_from_csv("NEISO", get_iso_config("NEISO"))` (the per-plant EIA-860
path; wind/solar/hydro/storage load via their own machinery and are excluded
here):

- **431 LP generators, 199 distinct plants, 24,588 MW** fossil + nuclear:

| Class | MW | Units |
|---|---|---|
| gas_cc | 13,264 | 97 |
| **oil** | **5,182** | **135** |
| nuclear | 3,355 | 3 |
| gas_ct | 1,631 | 127 |
| biomass | 1,047 | 68 |
| coal | 108 | 1 |

- **Oil is the second-largest class (5,182 MW)** — the largest oil fleet of any
  ISO in the model, the defining ISO-NE winter feature. **Dual-fuel: 6,367 MW
  across 42 plants** carry an EIA-860 oil/gas switch flag — the gas→oil
  switching machinery P13 activates (doc-08 design decision 2).
- **Coal is essentially gone:** a single ~108 MW unit (Merrimack retired);
  confirms the doc-08 "no coal must-run layer" premise. (The
  `campd-unit-outages-NEISO.csv` carries a `COAL` group for this lone unit.)
- **Zone distribution (MW):** North 6,105 / Central 6,042 / Boston 3,770 /
  Connecticut 8,672 / HQ_import 0 (the import node, no in-area plants —
  correct). **No unassigned plants** (zero fallback-zone warnings).
- **States:** CT 8,669 MW (74 plants), MA 7,937 (64), NH 3,259 (20), ME 2,648
  (19), RI 1,875 (11), VT 197 (10), **NY 2 MW (1)** — Fishers Island (ORIS
  57600, a 2 MW island diesel off the CT coast, electrically ISO-NE; correct).
- **Pilgrim confirmed ABSENT** (retired 2019). The 3 nuclear units are
  Millstone 2 (863 MW) & 3 (1,245) in CT and Seabrook (1,247) in NH — ~3.4 GW,
  matching doc-08 design decision 6.

### 2a. Comparison vs published totals (ISO-NE CELT / FCM)

The fleet loader covers fossil + nuclear only; renewables, hydro, and storage
load through their own machinery (P4/P5/P6). Reconstructed nameplate:
fossil+nuclear 24.6 GW + wind 1.5 + solar 2.9 + hydro (~2 GW nameplate, ME/NH/VT
run-of-river) + Northfield Mountain + Bear Swamp PS (~1.7 GW) ≈ **~33 GW
nameplate**, consistent with the published ISO-NE fleet.

| Class | Model | Published benchmark | Verdict |
|---|---|---|---|
| Fossil + nuclear | 24,588 MW | ISO-NE FCM: ~28.5 GW generation cleared (FCA for 2027/28); ~31–34 GW total nameplate incl. hydro/VRE/storage | reconciles once companion fleets applied |
| Nuclear | 3,355 MW (3 units) | Millstone 2&3 + Seabrook, ~3.4 GW | ✓ Pilgrim retired |
| Wind | 1,536 MW (Dec-2023) | eGRID 2023 ISNE: 1,536 MW (923 CF cross-check 3.34 TWh) | ✓ |
| Solar | 2,924 MW (Dec-2023) | utility-scale only; large MA/CT BTM PV excluded (net-load) | ✓ direction |

Source: [ISO-NE CELT Reports](https://www.iso-ne.com/system-planning/system-plans-studies/celt);
[ISO-NE Key Grid and Market Stats](https://www.iso-ne.com/about/key-stats);
[ISO-NE Forward Capacity Auction (2027/28) results](https://isonewswire.com/2024/02/09/new-englands-forward-capacity-auction-closes-with-adequate-power-system-resources-for-2027-2028/)
(~28,478 MW generation cleared). Note: iso-ne.com returns 403 from this
environment (EIA/ISO hosts blocked, playbook §2), so the CELT per-state
capacity table could not be pulled directly; the headline FCM figure is from
the public ISO Newswire release, and the in-repo eGRID 2023 workbook
(`BACODE=ISNE`) serves as the EPA fleet benchmark.

## 3. CEMS coverage

Distinct states of NEISO-fleet **fossil** plants and the diff against
`inputs/raw-data/campd-unit-level/<ST>_<year>.parquet`:

| State | Plants | MW | CEMS present | Missing |
|---|---|---|---|---|
| CT | 67 | 6,421 | 2023, 2024, 2025 | — |
| MA | 53 | 7,675 | 2023, 2024, 2025 | — |
| ME | 8 | 2,305 | 2023, 2024, 2025 | — |
| NH | 9 | 1,830 | 2023, 2024 | **2025 (upload U1)** |
| RI | 8 | 1,835 | 2023, 2024, 2025 | — |
| VT | 6 | 118 | 2023, 2024, 2025 | — |
| NY | 1 | 2 | 2023, 2025 | 2024 (Fishers Island, 2 MW — immaterial) |

- **Expected gap confirmed: `NH_2025`** is the one missing extract (doc-08
  U1) — the only 2025 CEMS gap. NH 2025 (1,830 MW, ~7% of fossil) runs on
  statistical availability until it lands; CT/MA/ME/RI/VT 2025 are complete.
- `campd.ISO_STATES["NEISO"] = ("ME","NH","MA","CT","RI","VT")` — the 2 MW
  NY/Fishers Island unit is outside the scope and immaterial.
- Unit-outage windows `campd-unit-outages-NEISO.csv` are already derived and
  **complete for all three years** (start-year counts: 2023 = 431, 2024 = 452,
  2025 = 422; 34 facilities; groups CC_REGULAR/CC_CHP/CT_CHP/ST_GAS + the lone
  COAL unit). P1 verifies; a `--iso NEISO` rerun folds NH 2025 in once U1 lands.

## 4. Upload manifest status (doc-08 U1–U7)

| # | Item | Destination | Status |
|---|------|-------------|--------|
| U1 | CAMPD unit-level `NH_2025.parquet` | `inputs/raw-data/campd-unit-level/` | **missing** — the only 2025 CEMS gap; CT/MA/ME/RI/VT 2025 + all 2023/2024 present |
| U2 | DA+RT hourly Hub + zonal LMP (NEMA/Boston, CT, SEMA, ME) 2023–2025 | `inputs/raw-data/lmp-data/NEISO/` | **missing** — needed by P10; price calibration is level-only without it |
| U3 | Zonal hourly load (8 ISO-NE zones) 2023–2025 | `inputs/raw-data/zone-specific-demand/NEISO/` | **missing** — zonal load stays on static RSP shares (0.20/0.30/0.21/0.29) until landed (P8) |
| U4 | Algonquin Citygate (AGT) delivered gas basis 2023–2025 | cite into `constants.py` / gas path | **partial (done as available)** — per doc-08 §P7, the ISO-NE MA gas index satisfies 35/36 months 2023–2025 in `inputs/raw-data/gas_basis_by_iso_month.csv` (Aug-2025 missing upstream, falls back to 923/shaped). The single most important NEISO upload — drives winter spikes + the dual-fuel switch (P13) |
| U5 | RGGI allowance prices 2023–2025 (optional) | cite into `STATE_CARBON_PRICE_BY_ISO` | **satisfied (web-search)** — done by P7: `STATE_CARBON_PRICE_BY_ISO["NEISO"]` active default-on |
| U6 | North–South / Boston-Import / CT-Import interface flows + limits (optional) | `inputs/raw-data/iso-specific-transmission/NEISO/` | **missing** — TTCs stay on Tier-3 RSP seeds (P10 validation) |
| U7 | HQ Phase II HVDC + Highgate + Cross-Sound scheduled flows (optional) | `inputs/raw-data/iso-specific-transmission/NEISO/` | **missing** — EIA-930 carries net interchange; priced-node refinement only (P9) |

U2 unblocks price calibration; U4 (largely landed) + P13 are the winter
make-or-break. The Stage-E reference and fleet/CEMS audit are complete now.

### Already done by earlier NEISO packs (for reference)

- **P7 (2026-06-11, doc-08):** `GAS_BASIS_DIFFERENTIAL["NEISO"]` (+1.10 seed),
  RGGI in marginal cost (`STATE_CARBON_PRICE_BY_ISO["NEISO"]`, 2023–2025,
  default-on), Algonquin winter basis via `gas_hub_basis_overlay` (35/36
  months), `gas_monthly_actuals` default-on. P13 still owes the dual-fuel
  switch activation that consumes the overlay.
- **Outage windows (P1 scope):** `campd-unit-outages-NEISO.csv` complete for
  2023–2025 (§3); `ISO_STATES["NEISO"]` set.

## 5. Present and verified (do not re-acquire)

- `data/eia_hourly/ISNE hourly.parquet` (demand/fuel/interchange); neighbor
  `NYIS` parquet for the seam.
- CAMPD unit-level CT/MA/ME/RI/VT 2023–2025 + NH 2023–2024; derived
  `campd-unit-outages-NEISO.csv` (2023–2025 complete).
- EIA-860 (incl. multifuel/storage tables), EIA-923 zips 2023/2024/2025,
  eGRID 2023 workbook, Henry Hub series — all national, in-repo.
- Topology/config: `_neiso_config()` (4 zones + HQ_import node + interface
  links), FIPS state→zone assignment, `MarketDesign("NEISO",
  capacity_market=True, net_cone=95)` (FCM), `voll=2000`,
  `FLEET_AVAILABILITY["NEISO"]=0.85`, generalized import-node machinery, and
  the P7 gas/RGGI/AGT-basis wiring above.
- Calibration reference + NEISO 2023/2024/2025 renewable CSVs (this session).

## 6. Out-of-scope observations for the backlog

- ERCOT/PJM calibration-reference staleness vs the new `Northeast` zone +
  EIA-860 vintage (§1b) — ERCOT/PJM-owned re-baseline.
- 2025 EIA-923 early-release respondent coverage (§1c) — national; ISNE hit
  hardest. Re-run on the final file.
- `tests/test_eia_loader.py::test_caiso_zonal_shares_fall_back_without_file`
  and `::test_caiso_zone_rows_are_static_share_split` fail on a clean checkout
  (CAISO zonal-share float tolerance) — pre-existing, unrelated to this change
  (941 other tests pass).
