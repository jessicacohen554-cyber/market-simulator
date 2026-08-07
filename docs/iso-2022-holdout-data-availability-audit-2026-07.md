# Cross-ISO holdout data-availability audit — 2022 validation touchpoint + 2018–2021 ladder

**Date:** 2026-07-31
**Task:** audit ALL SIX ISOs for *identical* data availability for every
measured-backed input for the 2022 validation-holdout touchpoint (parity bar:
the exact same input families the 2023–2025 training years carry), and census
the degree of collection for 2018–2021 so the remaining ladder/locked years are
ready when authorized.
**Method:** read-only repo scans — file existence, per-year row counts, year
spans, NaN coverage — plus keeper `run_config.json` flag extraction to ground
materiality. **No LP was constructed, solved, or scored for any year** (rule 22
channel-1-style no-LP validation). Scanner:
`scripts/archive/audit_holdout_data_availability_2026_07.py`.
**Status:** §§1–6 are the 2026-07-31 read-only audit as first written. **§7 is
the 2026-07-31 owner-authorized data-intake session** that worked §4.1 + §5 —
read it for what has since closed, for the correction to §4.1's demand-profile
blocker (it is **not** a hard blocker), and for the two items it hands back to
the owner.
**Governance context at audit time:** the HOLDOUT SPEND FREEZE
(`frontend/data/backcast/holdout-freeze.json`, declared 2026-07-25, HELD
2026-07-26) is **ACTIVE** — nothing in this doc is spendable until the owner
lifts it. Markers: `complete` = {NEISO, NYISO, PJM}; `final` = {} (empty;
NEISO's locked test **NEVER GRANTED** — *corrected 2026-08-06, owner decision D-23;
this read "already SPENT", which was false: no NEISO 2019/H1-2026 year has ever been
solved, scored or registered. `final` stays empty either way*). ERCOT / CAISO / MISO carry **no marker**,
so their 2022 solves are quarantined regardless of data readiness. 2019 is
**locked-test tier** — although inside the "2018–2021" span, its data is
censused here (intake is marker-free) but it is *not* part of the validation
ladder ({2018, 2020, 2021, 2022} per `scripts/lib/holdout_policy.py`).

Keeper recipes graded against (current at audit):
ERCOT `2026-07-31-ercot144-coal-perplant-offer`, CAISO
`2026-07-31-caiso146-ct-heat-rates`, PJM `2026-07-30-pjm-140-rampenv`,
MISO `2026-07-28-miso-101b-tempgrain`, NYISO `2026-07-30-nyiso-100-silretire`,
NEISO `2026-07-23-neiso-61-netrev-margin`.

---

## 1. Headline verdicts — 2022 touchpoint readiness

| ISO | 2022 data verdict | marker | blocking gaps (data only; freeze applies to all) |
|---|---|---|---|
| **NEISO** | **READY** — confirmed. Every keeper-consumed input and every bench series has a 2022 partition at the same grain as 2023–2025 | `complete` ✓ | none hard. Known DEGRADED (accepted/graded in the register): Algonquin daily gas falls back to monthly plateau; LMP-bench clock re-derive required before scoring (§5.6) |
| **NYISO** | **NEAR-READY** — register gaps mostly closed since 2026-07-12; 3 real items left | `complete` ✓ | v2 emission rates 2022 (tool gate); `IMPORT_TRANCHES_BY_YEAR` 2022 constant; `nuclear-availability-NYISO.csv` 2022 (new keeper flag, post-register); LMP clock re-derive |
| **PJM** | **NEAR-READY** — drivers/fleet/bench all landed; 4 keeper-flag inputs short | `complete` ✓ | measured interface limits 2022; short-window outages 2022 (derivable); seam import ladder blocked on MISO 2022 hub LMP; PJM-AS reserve series 2022 (partial file only) |
| **MISO** | **GAPPED — but the widest gap (LMP bench) is derivable from raws already on disk** | none | LMP bench 2022 (raws committed, bench not built); ASM reserve requirements 2022; zonal gas hub + citygate daily 2022; wind shape 2022; maxgen/short-window 2022; calref/renew-cap 2022; EIA-930 wide-hourly 2022 hole |
| **ERCOT** | **GAPPED** — the 2026-07-04 intake covered fuel/CAMPD/930, but the availability + scoring families were never extended | none | 60-Day DAM availability family (5 files) 2022; storage capability 2022; HSL 2022; v2 emission rates 2022; **LMP bench 2022 (no raws on disk either)**; DAM AS agg 2022 |
| **CAISO** | **GAPPED — but most of the queue CLOSED 2026-07-31** (see §3.2; the intake landed HSL 2022, the wide-hourly fill, the MIC+LCR registry, gas, interchange, AS_REQ and calref). The residual is the one that matters: the **LMP bench is SOURCE-BLOCKED, not merely absent** | none | LMP bench + raws 2022; v2 emission rates 2022; HSL 2022 (2019–2021 exist, 2022 does not); capacity-deliverability 2022 (keeper flag ON); zonal gas hub + citygate daily 2022; measured offer surface (2023–25-fit artifact, no 2022 bids raw); interchange actuals 2022; calref/renew-cap 2022; EIA-930 wide-hourly 2022 hole; CAISO-AS requirements 2022 |

The user-stated expectation "NEISO should be ready" is **confirmed**: NEISO is
the only ISO whose 2022 partition is fully at parity today. NYISO and PJM are
each a short, enumerated list away. ERCOT/CAISO/MISO each still miss their
**scoring target** (hourly LMP bench) for 2022 — the single most disqualifying
gap, since a touchpoint that cannot be scored cannot be spent (only MISO has
the raws on disk to close it without a new fetch).

---

## 2. Cross-ISO parity matrix — shared measured-input families, 2022 vs 2023–2025

`✓` = 2022 partition present at training-year grain · `△` = present but
degraded (grain/coverage/vintage) · `✗` = missing · `(d)` = derivable from
committed data with an existing committed producer, no new fetch needed.

| input family (path) | ERCOT | CAISO | PJM | MISO | NYISO | NEISO |
|---|:--:|:--:|:--:|:--:|:--:|:--:|
| Demand driver (`eia-930/eia_demand_profiles.parquet`, 2021–2025 all ISOs) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| EIA-930 wide hourly (`eia-930-hourly/<BA> hourly.parquet`) | ✓ | **✗** (9 stray h) | ✓ | **✗** (6 stray h) | ✓ | ✓ |
| EIA-930 long-form fueltype+region (bench) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| EIA-930 BALANCE bulk (2018–2026 both halves) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Zonal/native load actuals (`zone-specific-demand/…`) | ✓ | ✓ | ✓ | ✓ | ✓ | n/a (never existed, accepted) |
| CAMPD unit-level hourly (fleet binning + bench) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Unit-outage windows (`campd-unit-outages*.csv`, uniform 2026-07-24 detector) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Partial-outage derate (`campd-partial-outages*.csv`) | ✓ | n/a | ✗ (2023–25 only) | n/a | n/a | n/a |
| Short-window outages (`campd-unit-outages-short-*.csv`; keeper flag PJM+MISO) | n/a | n/a | ✗ (d) | ✗ (d) | n/a | n/a |
| F923 delivered fuel + generation (monthly, per plant) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Gas basis by ISO-month (`gas_basis_by_iso_month.csv`) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Zonal gas hub (`<iso>_zonal_gas_hub.csv`) | ✓ | ✗ (2023+) | ✓ | ✗ (2023+) | ✓ | n/a |
| Daily citygate/hub gas overlay | n/a | ✗ (2023+) | n/a | ✗ (2023+) | ✓ (Transco Z6, Elliott-week hole graded) | △ (monthly fallback) |
| Plant emission rates v2 (same-year measured CO2/NOx basis) | **✗** | **✗** | ✓ | ✓ | **✗** | ✓ |
| Plant emission rates v1 (pooled `year==0` consumed; see §5.2) | △ | △ | △ | △ | △ | △ |
| eGRID true-year vintage workbook | ✓ (2022) | ✓ | ✓ | ✓ | ✓ | ✓ |
| EIA-860 vintage snapshot (`vintage_2022`) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Weather (zone temp raws) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Renewable HSL / potential | ✗ (2023–25 only → 930-delivered-as-CF fallback) | **✗** (2019–21 + 2023–25, no 2022) | n/a | ✗ (wind shape 2023–25) | n/a | n/a |
| ISO availability overlay (DAM/operable/estimated) | **✗** (60-Day DAM family 2023–25) | ✗ (DAM-outage parquet 2023–25; probe) | ✓ (gen_outages 2018–2026; gate default-off) | ✓ (estimated 2022–26) | ✗ (nuclear avail 2023–25) | ✓ (operable capacity 2018–2026; gate default-off) |
| Measured reserve/AS inputs (keeper-consumed) | △ (AS plan ✓ 2022, RTORDPA ✓ 2022; DAM AS agg ✗, storage capability ✗) | ✗ (asreq 2023+) | ✗ (PJM-AS 2023+; DA reserve 2022 partial) | ✗ (ASM 2023+) | ✓ (req 2022 ✓; AS prices validation-side ✓) | ✓ (co-opt static) |
| Interchange actuals (`eia-930-interchange/`, priced-interchange ISOs) | n/a | ✗ (2023–25) | ✗ (2023–25) | ✗ (2023–25) | ✓ (interface flows 2018–2026) | ✗ (2023–25) |
| Import-ladder constants (`IMPORT_TRANCHES_BY_YEAR`) | n/a | ✗ (2023–25) | (seam ladder ✗, blocked on MISO LMP) | △ (firm-import floors; seam ladder ✗ 2022) | ✗ (2023–25) (d — PJM/NEISO 2022 hub means now exist) | ✗ (2023–25) |
| Capacity-deliverability registry (keeper flag: CAISO ON; NYISO LCR/TSL ON) | n/a | **✗** (2023–25) | ✗ (2023/24+; flag off) | ✓ (2022/23 ✓) | ✓ (2022/23 ✓) | ✗ (2023/24+; flag off) |
| **LMP bench hourly (scoring target)** | **✗** | **✗** | ✓ (2018–2025) | **✗ (d — 2022 DA+RT raw CSVs on disk)** | ✓ (clock re-derive owed) | ✓ (clock re-derive owed) |
| LMP bench annual (`actual_lmp.json`) | ✗ | ✗ | ✓ | ✗ (d) | ✓ | ✓ |
| Scarcity tail (`actual_tail.json`; marker-aware deriver) | ✗ (no marker) | ✗ (no marker) | ✗ (d — marker now exists, auto-emits on next derive run) | ✗ (no marker) | ✓ | ✓ |
| `calibration_reference.json` + `<ISO>_2022_renewable_capacity.csv` | ✓ | ✗ | ✓ | ✗ | ✓ | ✓ |

---

## 3. Per-ISO gap detail (2022) — keeper-flag-grounded

Materiality is judged against the CURRENT keeper's ON flags, not the register's
older keeper baselines.

### 3.1 ERCOT (`ercot-144`; no marker)

| gap | keeper flag consuming it | coverage today | materiality / fix |
|---|---|---|---|
| 60-Day DAM availability family: `ercot-thermal-dam-availability{,-hourly}.csv`, `ercot-outages.csv`, `ercot-noncampd-availability.csv`, `ercot-nuclear-availability.csv` | `ercot_thermal_dam_availability{,_hourly,_coal,_plant}`, `ercot_noncampd_plant_availability`, `ercot_nuclear_unit_availability` — all ON | 2023–2025 only | **HIGH** — this is the keeper's availability envelope. Fix: fetch ERCOT 60-Day DAM disclosure archives for 2022 and re-run the committed derives (60d disclosures are public back years) |
| `ercot-storage-capability.csv` | `ercot_storage_as_reserve` + `storage_as_commitment` (from_year 2023 — **verify the 2022 semantics of every `*_from_year=2023` gate before a 2022 solve**: several ERCOT AS mechanisms simply do not arm before 2023) | 2023–2025 hourly | **HIGH if armed for 2022; moot if the from_year gates leave 2022 unarmed** — an owner/methodology call on what the 2022 recipe even is, before a data fetch |
| ERCOT HSL (`ercot-hsl/`) | renewables potential + `ercot_gtc_limits_measured` per-year gate | 2023–2025 | **HIGH** — without 2022 HSL, renewables ride EIA-930-delivered-as-CF (no endogenous curtailment) AND the measured GTC overlay self-disables for 2022 (its gate needs measured HSL) even though `SCEDBTCNP686` GTC raws for 2020–2025 are on disk (§5.7). Fix: NP4-732/737 published HSL upload for 2022 |
| DAM AS agg (`DAMASAGGNP419_*.parquet`) | `ercot_dam_as_overlay_from_year=2024` | 2023–2025 (+2022 for `ASPLANNP433` ✓, RTORDPA ✓ 2022–2025) | LOW for 2022 (overlay arms from 2024) — census only |
| Plant emission rates v2 — no ERCOT 2022 rows | `use_plant_emission_rates_v2` | 2018–2021 + 2023–2025 (2022 is a gap year) | **MEDIUM-HIGH** (same-year measured CO2 cost basis). Fix: `curate_emissions_unit_annual.py --years 2022` + `derive_plant_emissions_v2.py --iso ERCOT --years 2022` — tools are marker-gated and ERCOT has no marker (the N3 policy-skew item, owner call) |
| **LMP bench 2022** (`actual_lmp_hourly_ERCOT.parquet`, `actual_lmp.json`, zonal parquet) | scoring target | 2023–2025; `lmp-data/ERCOT/` empty, no 2022 DA/RT raws anywhere | **BLOCKING** — un-scorable. Fix: fetch ERCOT MIS DA/RT SPP archives for 2022 (public), extend `derive_actual_lmp.py` |
| `actual_tail.json` 2022 | tail diagnostic | marker-aware deriver; no ERCOT marker | governance, not data |

Present and at parity for 2022: EIA-930 (all forms), native zonal load,
CAMPD unit-level, unit+partial outage windows, F923, N3045 delivered gas,
7-zone Sch5/Waha hub file, eGRID2022, EIA-860 vintage, weather, calref +
renewable-capacity sidecars, GTC raws, AS plan, RTORDPA.

### 3.2 CAISO (`caiso-146`; no marker)

| gap | keeper flag | coverage today | materiality / fix |
|---|---|---|---|
| **LMP bench 2022** + raw OASIS zips | scoring target | bench 2023–2025; `lmp-data/CAISO` raws are 2023-only | **BLOCKING — and the fix below is REFUTED (2026-07-31).** The stated fix ("OASIS `PRC_LMP` group fetch for 2022 (public), committed builder") does not exist: OASIS's ~39-month retention has aged past the whole 2018–2022 window. Binary-searched 2026-07-31, the earliest DAM trade date `PRC_LMP` still serves is **2023-04-19**; 2018/2020/2022 all return ERR_CODE 1000 for DAM and RTM alike. Only hand-downloaded GRP bulk zips can close it — a procurement task, not a scripting task. See the register §CAISO N-CA-1 |
| Plant emission rates v2 CAISO 2022 | `use_plant_emission_rates_v2` | 2018–2021 + 2023–2025 | MEDIUM-HIGH; same marker-gated-tool issue as ERCOT |
| CAISO HSL 2022 | renewables potential / endogenous spill (`caiso_solar_endogenous_spill`) | ~~2019–2021 + 2023–2025~~ → **CLOSED 2026-07-31** | **RESOLVED.** The blocker was the wide-hourly 2022 hole below, not the curtailment workbook; with it closed the committed builder produces 2022 unchanged in recipe (and re-derives 2019/2020/2021/2023/2024/2025 byte-identically). 2018 stays withheld — 4,343 of 4,380 H1-2018 hours have null EIA-930 wind/solar, so the loader's bfill fabricates a flat series |
| Capacity-deliverability registry 2022 | `capacity_deliverability_limits=True` (keeper-ON; MIC → WECC_import half) | ~~2023–2025~~ → **CLOSED 2026-07-31 for 2018–2022** | **RESOLVED** by `scripts/data/curate_caiso_mic.py` + `curate_caiso_lcr.py`, both `--verify`-proven against the committed 2023–2025 rows. Local-area peak loads remain MISSING: the committed rows' own table citations do not resolve in the reports they cite |
| Zonal gas hub 2022 (`caiso_zonal_gas_hub.csv`) | zonal gas basis | ~~2023–2025~~ → **CLOSED 2026-07-31 for 2020–2022** | **RESOLVED.** 2018–2019 are not derivable at grain: the older EIA weekly narrative carries almost no PG&E Citygate row (2 prints in 2018, 7 in 2019 vs ~50/yr later) |
| Citygate daily 2022 (`gas-prices/caiso_citygate_daily.csv`) | `gas_daily_shape`/`gas_hub_basis_overlay` refinement | ~~2023–2026~~ → **CLOSED 2026-07-31 for 2018–2022** (1,114 new prints) | **RESOLVED.** H1-2026 stays at 12 prints through Jan-21 — EIA's weekly archive lists 3 editions for 2026 and every later 2026 edition URL 404s |
| Measured offer surface (`caiso_offer_surface_*`, `caiso-public-bids/` empty) | `caiso_offer_surface_measured=True` | condbinned artifact fit on 2023–2025 | **METHODOLOGY DECISION, not just data**: does a 2022 solve reuse the 2023–25-fit surface (vintage asymmetry) or require 2022 public bids (raws not on disk)? Adjudicate before the one-shot; record in the register |
| EIA-930 wide-hourly 2022 hole | bench/bulk paths | ~~9 rows~~ → **CLOSED** (dense 8760 h) | **RESOLVED** by the landed-long-form rebuild, independently by two sessions on 2026-07-31 to byte-identical output |
| Interchange actuals 2022 (`eia-930-interchange/CISO`) | `priced_interchange` + firm-import shape | ~~2023–2025~~ → **CLOSED 2026-07-31 for 2019–2022 + H1-2026** | **RESOLVED.** 2018 is a source gap, not a fetch gap: EIA's interchange-data route returns `total: 0` for CISO in any 2018 window |
| `IMPORT_TRANCHES_BY_YEAR["CAISO"]` 2022 | backcast import ladder | {2023, 2024, 2025} | MEDIUM — hand-derived constant; needs neighbor/intertie 2022 prices (WECC intertie parquet is 2023–2025 too) |
| calref + renewable capacity 2022 | scoring sidecars | ~~2023–2025~~ → **CLOSED 2026-07-31 for 2021–2022** | **RESOLVED** for every year the builder can produce; 2018–2020 stay blocked on the §4.1 demand-profile artifact |
| CAISO-AS requirements (`asreq_*`) 2022 | AS requirement inputs | ~~2023+~~ → **CLOSED 2026-07-31 for 2018–2022 + H1-2026** | **RESOLVED.** `AS_REQ` carries no OASIS retention limit, unlike `PRC_LMP` |
| storage-as-awards 2022 | `caiso_storage_as_reservation` (default OFF, probe-inert) | 2023–2025 quarterlies | NONE for the keeper; census only |
| DAM outage windows parquet 2022 | not keeper-consumed (`outage_source=historic` covers it) | dense 2023–2025 only | LOW |

### 3.3 PJM (`pjm-140`; `complete` marker 2026-07-31)

| gap | keeper flag | coverage today | materiality / fix |
|---|---|---|---|
| Measured interface limits (`iso-specific-transmission/PJM_*_transfer_limits_and_flows.csv`) | `pjm_measured_interface_limits=True` | 2023–2025 | **HIGH** (keeper mechanism). Fix: PJM DataMiner transfer-limits export for 2022 (same feed as the committed files) |
| Short-window outages (`campd-unit-outages-short-PJM.csv`) | `unit_outage_short_windows=True` | 2023–2025 | MEDIUM — **derivable (d)** from on-disk CAMPD 2022 with the committed derive |
| Seam import ladder (`pjm_seam_measured_ladder`) | keeper-ON | needs neighbor (MISO) 2022 hub LMP — `actual_lmp.json["MISO"]` is 2023–2025 | MEDIUM — cross-ISO: closes for free once MISO's 2022 bench is built (§3.4, raws on disk) |
| PJM-AS reserve series | `pjm_reserve_supply_cap`, `pjm_reserve_pergen` | 2023–2025 (+`da_reserve_market_results_2022_partial.parquet`) | MEDIUM — grade the 2022-partial file vs the keeper's actual consumption window; extend from DataMiner if short |
| Nuclear availability (`nuclear-availability-PJM.csv`) | (not in pjm-140 flag set — census only) | 2023–2025 | LOW for this keeper |
| Partial-outage derate (`campd-partial-outages-PJM.csv`) | ERCOT-style derate (PJM file exists but 2023–2025) | 2023–2025 | LOW-MEDIUM — derivable (d) from CAMPD 2022 if the recipe consumes it |
| interchange actuals 2022 | `priced_interchange` | 2023–2025 | MEDIUM (same fix as CAISO) |
| `measured_ct_heat_rates` / `measured_ramp_capability` artifacts | keeper-ON | derived from CAMPD/eGRID (2022 sources ✓ on disk) | verify the artifacts' year handling at recipe-freeze; derivable (d) |

At parity: demand (930 + `hrl_load_metered` 2018–2026), CAMPD, unit outages,
v2 emission rates 2022 ✓, F923, 8-zone gas hub 2022 ✓, delivered-gas basis,
gen_outages_by_type 2018–2026 (DAM-availability gate, default-off),
gen_by_fuel 2020–2026, **LMP bench 2018–2025 full** — PJM is the only ISO whose
hourly LMP bench already spans the entire ladder. `actual_tail.json` PJM 2022
auto-emits at the next marker-aware derive run (marker landed 2026-07-31).

### 3.4 MISO (`miso-101b`; no marker)

| gap | keeper flag | coverage today | materiality / fix |
|---|---|---|---|
| **LMP bench 2022** | scoring target | bench 2023–2025, **but `lmp-data/MISO/miso_hub_lmp_2022_{da,rt}_p*.csv` raws (94 files) are COMMITTED** | **BLOCKING but (d)** — run the committed MISO builder over the on-disk 2022 raws; no fetch needed. (Zonal bench parquet 2023–2025 would need its own extension) |
| ASM measured reserve requirements (`MISO-AS/asm_*`) | `miso_measured_reserve_requirements`, `miso_zonal_reserves` etc. | 2023–2026 | **HIGH** (keeper mechanism). Fix: MISO market reports archive fetch for 2022 |
| Zonal gas hub + citygate daily (`miso_zonal_gas_hub.csv` 2023–25; `miso_citygate_daily.csv` 2023–25) | `miso_zonal_gas_basis`, `miso_winter_citygate_daily` | 2023–2025 | MEDIUM-HIGH. Fix: same EIA/citygate producers, 2022 window |
| Wind zone shape (`miso-wind-shape/`) | zonal wind profiles | 2023–2025 | MEDIUM. Fix: same derive from 930/EIA for 2022 |
| Maxgen events (`maxgen-events/miso/miso.csv`) | `unit_outage_maxgen_events=True` | 2023–2025 events | MEDIUM — extend from MISO IMM/event records for 2022 |
| Short-window outages (`campd-unit-outages-short-MISO.csv`) | `unit_outage_short_windows=True` | 2023–2025 | MEDIUM — derivable (d) from CAMPD 2022 |
| EIA-930 wide-hourly 2022 hole | bench/bulk | **6 rows** — §5.1 | HIGH; rebuild from landed long-form (d) |
| calref + renewable capacity 2022 | scoring sidecars | 2023–2025 | MEDIUM (builder extension) |
| interchange actuals 2022 | `priced_interchange`, `miso_firm_imports` | 2023–2025 | MEDIUM (PJM border LMP parquet also 2023–2025; MISO 2022 needs its neighbor prices — PJM's are ✓ 2018–2025) |
| PRA clearing prices | capacity side | 2023–2026 | LOW (validation-side) |

At parity: demand profile ✓, subba demand 2019–2026 ✓, CAMPD ✓, unit outages ✓,
estimated generation-outages 2022–2026 ✓, v2 emission rates 2022 ✓, F923 ✓,
monthly basis ✓, capacity-deliverability 2022/23 ✓, weather ✓.

### 3.5 NYISO (`nyiso-100`; `complete` marker 2026-07-31)

The register's §NYISO (2026-07-12) remains the authoritative per-input grading;
delta since then, re-graded against the **current** keeper:

| item | status change |
|---|---|
| Unit-outage windows 2022 ("MISSING + DEGRADED vintage", the register's largest gap) | **CLOSED 2026-07-24** — the all-ISO re-derivation landed `campd-unit-outages-NYISO.csv` 2018–2026 on the uniform current detector (533 windows in 2022); the vintage asymmetry is gone (all years same detector). The layup over-count (freeze cause) still hangs over the whole family cross-ISO — that is the freeze's exit condition, not a NYISO-specific gap |
| Plant emission rates v2 2022 | **STILL MISSING** (v2 has NYISO 2018–2021 + 2023–2026; 2022 gap year). Tools remain marker-gated — NYISO now HAS a marker, so the register's N3 blocker is lifted: run `curate_emissions_unit_annual.py --years 2022 --holdout-intake NYISO` + `derive_plant_emissions_v2.py --iso NYISO --years 2022 --holdout-intake NYISO` |
| Capacity-deliverability 2022/23 | **CLOSED 2026-07-13** (LCR/TSL row landed) ✓ |
| `IMPORT_TRANCHES_BY_YEAR["NYISO"]` 2022 | **STILL MISSING — but now unblocked**: the cross-ISO blocker (PJM/NEISO `actual_lmp.json` 2022 blocks) is resolved (PJM 2018–2025 ✓, NEISO 2020–2025 ✓); re-run `derive_nyiso_import_ladder.py` with 2022 |
| `nuclear-availability-NYISO.csv` 2022 | **NEW GAP (post-register keeper delta)** — nyiso-100 has `nuclear_unit_availability=True`; the CSV is 2023–2025. NRC power-reactor-status raws on disk are 2023–2025 too; NRC publishes all back years — fetch + derive 2022 |
| New measured flags since the register baseline (`measured_ct_heat_rates`, `dual_fuel_oil_daily_parity`, `hydro_dispatch_envelope`/`hydro_min_flow_floor`, `nyiso_gas_commitment_bridge` params) | **RE-GRADE at recipe freeze** — derived from CAMPD/F923/930 sources that ARE on disk for 2022, but the artifacts' per-year handling needs the same verify-then-derive pass the register applied to the older flags |
| LMP bench 2022 | ✓ landed, but **must be re-derived on the fixed clock** before scoring (§5.6) |
| In-sample flag (unchanged) | `calibration_reference.json` `isos.NYISO.2024` + `NYISO_2024_renewable_capacity.csv` still MISSING (builder pinning) — an **in-sample** defect worth fixing regardless of holdouts |

### 3.6 NEISO (`neiso-61`; `complete` marker; locked test NEVER GRANTED — *corrected 2026-08-06, D-23; this header read "locked test SPENT", which was false*)

Confirmed READY for 2022 — every keeper-consumed family present at parity:
demand ✓, CAMPD ✓, unit outages 2018–2026 ✓, v2 rates 2022 ✓ (179 units),
F923 + oil rows ✓, monthly basis ✓, zone/load-weighted temps ✓, winter-fuel
statics ✓, calref + renewable capacity 2021–2025 ✓, LMP bench 2020–2025 ✓,
tail 2022 ✓, operable-capacity 2018–2026 ✓ (gate default-off). Standing
DEGRADED items are exactly the register's: Algonquin daily 2018–2022 missing
(monthly plateau fallback, rule-14-clean), fleet statics year-agnostic
(accepted), detector-family caveat (freeze). Only the clock re-derive (§5.6)
and the freeze stand between NEISO and a spendable 2022 touchpoint.

---

## 4. 2018–2021 census (validation ladder 2018/2020/2021 + locked 2019)

Data intake is marker-free (rule 22 channel 1), so all four years are censused
together; **2019 remains locked-tier for solve/score forever-once**.

### 4.1 Cross-ISO blockers (all six ISOs)

| blocker | detail | fix |
|---|---|---|
| **Demand profiles 2018–2020** | `eia_demand_profiles.parquet` carries 2021–2025 ONLY, for every ISO. Without it `load_demand` hard-fails — **no ISO can dispatch 2018–2020 at all.** 2021 is present for all six | The F3-class gap: the artifact is hand-uploaded, no in-repo builder. Needs an owner-supplied rebuild (raw wide extracts underlying it DO cover 2018–2020 for every BA) |
| eGRID vintages 2018–2021 | `fleet-egrid/` holds ONLY egrid2022/2023(rev2)/2024 workbooks (§5.3 — the register believed 2018–2021 were on disk; they are not) | re-fetch from epa.gov (public archive), register vintages in `egrid.py` |
| `fossil_co2_rates.parquet` 2018–2021 | only 2022–2026 | blocked on the eGRID vintages above; LOW while v2 (primary path) covers 2018–2021 everywhere |
| `calibration_reference.json` + renewable-capacity 2018–2020 | no ISO has them (ERCOT/PJM/NEISO stop at 2021) | builder hard-requires the missing demand profiles — same F3 root |
| Parasitic load factors 2018–2021 | pooled `year==0` fallback only | accepted (designed fallback) |
| v1 emission rates | `{0, 2023, 2024}` only — pre-existing structural gap, pooled rows consumed | accepted |

### 4.2 Per-ISO 2018–2021 readiness (beyond the cross-ISO blockers)

| ISO | already at parity for 2018–2021 | additional per-ISO gaps vs 2022's list |
|---|---|---|
| **ERCOT** | CAMPD ✓, outages ✓, v2 rates ✓, F923 ✓, monthly basis ✓, native load ✓, weather ✓, 930 wide+long ✓, GTC raws 2020–2021 ✓, calref/renew-cap 2021 ✓ | everything in §3.1 for 2022 also for each year, PLUS: zonal gas hub + N3045 (2022+ only), partial outages (2022+ only), GTC 2018–2019, LMP bench (nothing pre-2023) |
| **CAISO** | CAMPD ✓, outages ✓, v2 ✓, F923 ✓, monthly basis ✓, zone demand ✓, weather ✓, HSL **2019–2021 ✓**, curtailment xlsx ✓ | §3.2 list for each year (LMP raws exist for NO back year), minus HSL for 2019–2021 |
| **PJM** | LMP bench 2018–2021 ✓✓, `hrl_load_metered` ✓, gen_by_fuel 2020–2021 ✓, gen_outages ✓, CAMPD/outages/v2/F923 ✓, monthly basis ✓, weather ✓, calref/renew-cap 2021 ✓ | interface limits, PJM-AS, zonal gas hub (2022+), short windows, partial outages — same fixes as 2022 per year |
| **MISO** | CAMPD/outages/v2/F923/monthly basis ✓, subba demand 2019–2021 ✓ (2018 ✗), weather ✓ | §3.4 list per year; hub-LMP raws exist ONLY for 2022 — 2018–2021 need fresh fetches; estimated generation-outages start 2022 |
| **NYISO** | the register's 2026-07-13 section stands: LMP bench 2018–2021 ✓ (clock caveat), AS reference ✓, facility-level ✓, interface flows ✓, zonal hub annuals ✓, SOM prices ✓, fuel-mix ✓ | reserve-requirements hourly 2018–2021 (real LRR-schedule coverage gap — methodology decision); Transco daily/monthly + basis re-base; weather merge; capacity-deliverability 2019/20+2020/21; downstate gas rows |
| **NEISO** | register §NEISO stands: temps ✓, outages ✓, v2 ✓, LMP bench 2020–2021 ✓, calref 2021 ✓ | **2018–2019 SMD workbooks are NOW ON DISK** (`lmp-data/NEISO/2018,2019_smd_hourly.xlsx` — landed after the register declared them unobtainable): the 2018–2019 LMP bench is now derivable (d) with the committed builder + `lw_retrofit`. Remaining: `HOLDOUT_YEARS` widening decision for tail 2018–2021 (cross-ISO constant, owner call) |

---

## 5. Discrepancies & drift found by this audit (repo vs its own records)

1. **CISO/MISO EIA-930 wide-hourly 2022 hole.** `CISO hourly.parquet` has **9**
   2022 rows and `MISO hourly.parquet` has **6** (Jan-1 UTC-boundary spillover
   only); every other year 2018–2026 is dense. The 2026-07-08 intake landed the
   2022 **long-form** files but the wide extension covered only 2018 + H1-2026.
   Any wide-extract consumer silently sees an empty 2022. Fix is the committed
   `build_eia930_hourly_from_raw.py` (append-only, PJM-2022 precedent).
2. **v1 `plant_emission_rates.parquet` lost its intaken 2022/2026 rows.** The
   2026-07-04 F5 intake records "Added **2022** (130 TX plants) and **2026 Q1**
   (128)"; at HEAD the artifact carries `{0, 2023, 2024}` only (last touched in
   the PR #3098 lineage). Either the landing never reached main or a later
   rebuild dropped the rows. LOW direct materiality (the pooled `year==0` rows
   are what `egrid._campd_rate_map` consumes) but it is recorded-intake drift —
   calibration owner should reconcile the record.
3. **eGRID 2018–2021 vintages absent.** The register's NYISO 2018–2021 section
   grades eGRID "EQUIVALENT (pre-existing) — `egrid{2018..2021}_data.xlsx` on
   disk"; `data/raw/fleet-egrid/` holds only 2022/2023/2024. Blocks true-vintage
   `fossil_co2_rates` 2018–2021 (v1-adjacent path; v2 unaffected).
4. **Register outage rows superseded (favorably).** The 2026-07-24 all-ISO
   re-derivation gives every ISO uniform-detector unit-outage windows for
   2018–2026, closing the register's NYISO-2022 "MISSING" row and the
   NEISO/NYISO detector-vintage *asymmetry* (all years now share one vintage).
   The remaining issue is the freeze's layup over-count — cross-ISO, owned by
   the fix charter, with `campd-unit-outages-layup*.csv` companions (2018–2026)
   already on disk.
5. **NEISO 2018/2019 SMD workbooks now on disk** — the register's "MISSING
   2018-2019 … did not yield a scriptable free download" is stale; the bench is
   now derivable in-repo.
6. **Scoring-clock caveat (register, 2026-07-15) still owed.** The
   out-of-training LMP blocks built pre-fix (NYISO 2018–2022 + 2026-H1, NEISO
   2020–2022) remain byte-frozen on the OLD prevailing-clock indexing. Before
   ANY authorized validation scoring these blocks must be re-derived with the
   fixed `derive_actual_lmp.py` — an hourly-paired score against them would
   re-import the ±1 h DST artifact. (PJM's 2018–2022 blocks should be
   spot-checked for the same lineage before use.)
7. **ERCOT GTC archives landed.** `iso-specific-transmission/SCEDBTCNP686_*`
   now covers 2020–2025, retiring the `ercot_gtc_limits_measured` "DATA
   NEEDED" note for those years (the overlay-audit doc's data-status paragraph
   is stale) — but the overlay stays self-disabled for any year without
   measured HSL, which today means it is armable only for 2023–2025.
8. **NYISO 2024 in-sample sidecars still missing** (`isos.NYISO.2024`,
   `NYISO_2024_renewable_capacity.csv`) — flagged in the register, unchanged;
   an in-sample parity defect independent of holdouts.

---

## 6. What must happen, in order, for each ISO's 2022 touchpoint

Common preconditions (every ISO): **(a)** owner lifts the holdout spend freeze
(layup charter exit); **(b)** the ISO holds a `complete` marker (missing for
ERCOT/CAISO/MISO — an owner determination, not a data task); **(c)** register
section signed off (G-19); **(d)** clock-fixed re-derivation of any
pre-2026-07-15 LMP bench block the score will read.

- **NEISO:** nothing further on data. (Optional: derive 2018–2019 LMP bench
  from the now-on-disk workbooks while the lane is warm.)
- **NYISO:** v2 rates 2022 (tools now unblocked by the marker) → import-ladder
  2022 constant (now unblocked cross-ISO) → nuclear-availability 2022 → clock
  re-derive → re-grade the four post-register keeper flags.
- **PJM:** interface limits 2022 (DataMiner) → short-window derive 2022 →
  PJM-AS 2022 grading/extension → (seam ladder waits on MISO bench) → verify
  `measured_ct_heat_rates`/`ramp` artifact year-handling.
- **MISO:** build 2022 LMP bench from committed raws (no fetch) → ASM 2022
  fetch → zonal hub + citygate 2022 → wide-hourly 2022 rebuild → short-window/
  maxgen/wind-shape 2022 → calref/renew-cap 2022.
- **ERCOT:** 60-Day DAM availability family 2022 (+ storage capability, with
  the `*_from_year` semantics decision) → HSL 2022 upload → LMP bench 2022
  fetch+derive → v2 rates 2022 (marker-gated) → calref ✓ already.
- **CAISO:** *(mostly executed 2026-07-31 — register §CAISO.)* DONE: HSL 2022,
  wide-hourly rebuild, capacity-deliverability 2018–2022, zonal hub 2020–2022 +
  citygate daily 2018–2022, interchange 2019–2022 + H1-2026, AS_REQ 2018–2022 +
  H1-2026, calref/renew-cap 2021–2022, LMP bench H1-2026. RECORDED, not
  resolved: v2 rates 2022 (its tool gate is already loosened) and the
  offer-surface vintage adjudication. **STILL BLOCKING and no longer a
  scripting task: the 2018–2022 LMP bench** (OASIS retention ends 2023-04-19;
  hand-downloaded GRP bulk zips only) and the WECC intertie prices + import
  ladder behind the same wall.

**H1-2026 (locked tier, with 2019):** unchanged from the register — CAMPD
Q2-2026, EIA delivered-gas May+, F923/eGRID/SOM vintages, and the full-8760
demand-profile contract are publication-horizon blocked for every ISO; no new
gap class found by this audit. 2019 solves additionally ride on the §4.1
2018–2020 demand-profile blocker.

---

*Scan artifacts: per-family JSON census produced by
`scripts/archive/audit_holdout_data_availability_2026_07.py` (re-runnable,
read-only). All row counts and year spans in §§1–6 are from the 2026-07-31
scan of the working tree at `ab4e910`.*

---

## 7. 2026-07-31 intake session — what closed, what moved, what is still MISSING

Rule 22 Option-2 **DATA INTAKE ONLY**, owner-authorized 2026-07-31 for 2018–2022
+ H1-2026 across all six ISOs (verbatim authorization in
`frontend/data/backcast/calibration-complete.json` → `intake_log`). **No LP was
constructed, solved or scored; nothing was registered on any dashboard; the
spend freeze is untouched.** All validation below is no-LP (loader
resolvability, byte/value identity, row-count census). 2019 data landed like
any other year — intake is marker-free — and remains locked-tier for
solve/score forever-once.

### 7.1 Closed

| audit row | what landed | freeze verification |
|---|---|---|
| §4.1 / §5.3 **eGRID 2018–2021 vintages absent** | all four workbooks fetched from EPA's historical archive into `data/raw/fleet-egrid/` (2018 `_v2`, 2019, 2020 `_v2`, 2021 — latest revision, US units; URLs in that dir's README) and registered in `egrid.py::_EGRID_FILES` + `curate_egrid.EGRID_FILES`. 2018–2021 now anchor on their OWN release instead of the 2024 stand-in | — |
| §4.1 **`fossil_co2_rates.parquet` 2018–2021** | one `derive_fossil_co2_rates.py --years 2018 2019 2020 2021` run on the true vintages: 2018 2,572 / 2019 2,547 / 2020 2,536 / 2021 2,619 fossil plants. Artifact spans 2018–2026, 22,958 rows | 2022–2026 rows value-identical (12,684 rows, sha256 `5802d577…`, `DataFrame.equals` True) |
| §4.2 / §5.5 **NEISO 2018–2019 LMP bench** | built from the on-disk SMD workbooks — da/rt $44.13/$43.54 (2018), $31.22/$30.67 (2019) | see below |
| §5.6 **NEISO scoring-clock re-derive (2020–2022)** | re-derived on the fixed clock in the same run; `--lw-retrofit` for all five years. Legacy equal-hour means are clock-invariant so 2020–2022 keep theirs; the hourly indexing and `*_pct` / `*_lw` moved (2020 `rt_lw` 25.09 → 25.14, 2022 91.00 → 91.16) | NEISO 2023–2025 parquet rows value-identical (26,280); `actual_lmp.json` diffed record-by-record — NEISO 2018–2022 the ONLY changed entries |
| §5.1 **CISO/MISO EIA-930 wide-hourly 2022 hole** | `build_eia930_hourly_from_raw.py` gains `--fill-years` (splice missing hours of a named year — `--append-only` cannot reach a hole in the middle). CISO spliced 8,751 rows, MISO 8,753 → both now carry 8,760 local-2022 hours | every pre-existing row value-identical for both BAs |
| §5.2 **v1 `plant_emission_rates.parquet` 2022/2026 drift** | explained and re-landed — see §7.3 | pooled `year==0` (131), 2023 (130), 2024 (129) value-identical; `master-plant-registry.csv` byte-identical |
| §3.3 / §3.4 **short-window outages 2022 (PJM, MISO — both keeper-ON)** | extended to the full 2018–2026 span with the committed producer: MISO 290 → 987 windows, PJM 285 → 934 | MISO 2023–2025 **reproduced identically** by the full-span run; PJM's did not — see §7.4 |

### 7.2 §4.1's "no ISO can dispatch 2018–2020 at all" is **WRONG** — correct it

The row claims `eia_demand_profiles.parquet` (2021–2025 only) is a hard blocker
because "without it `load_demand` hard-fails". It does not. Every one of the six
ISOs has a dedicated per-BA loader in
`market_sim.data.eia930.demand.DEMAND_LOADERS` that reads
`eia-930-hourly/<BA> hourly.parquet` and **takes precedence over** the
demand-profiles parquet; those extracts span 2018–2026. Measured directly (no
LP, `load_demand(iso, year, get_iso_config(iso))`):

| ISO | 2018 | 2019 | 2020 | 2021 | 2022 |
|---|--:|--:|--:|--:|--:|
| ERCOT | 376 | 383 | 379 | 391 | 429 |
| CAISO | 226 | 214 | 217 | 219 | 224 |
| PJM | 821 | 800 | 768 | 796 | 810 |
| MISO | 668 | 650 | 623 | 642 | 653 |
| NYISO | 133 | 131 | 128 | 124 | 124 |
| NEISO | 102 | 96 | 92 | 99 | 100 |

(TWh, zero NaN in every cell.) 2026 is the year that genuinely fails
(`ValueError`) — the full-8760 contract, unchanged from F3.

What the demand-profiles gap **does** still block is narrower and worth
carrying forward as its own row: `build_calibration_reference.py` (hence the
§4.1 calref / renewable-capacity 2018–2020 row, which stands), and — before
this session — CAISO/MISO **2022**, the two ISOs whose per-BA extract had the
§5.1 hole and therefore fell through to the demand-profiles path with the
explicit "falling back to the corrupted legacy series" warning. Filling the
hole moved both onto the real per-BA extract, so that fallback is gone.

Owner decision still needed on the artifact itself — see §7.5.

### 7.3 §5.2 resolved: the rows never reached `main`

The artifact has **exactly one blob in all of git history**
(`19ecb0f8…`), first *added* 2026-07-22 in the ercot-99 lineage (`66fd940`)
carrying `{0, 2023, 2024}`, and unchanged at every commit since. No later
rebuild dropped anything.

The 2026-07-04 F5 rows were uncommittable when they were produced, on both
sides of the W1 relocation. `docs/out-of-sample-results-2026-07.md` §F5 records
that `derive_plant_emissions.py` "still wrote to the pre-W1 `inputs/processed`
tree" — and `/inputs/` is gitignored and has **never** been a tracked path in
this repo. The path fix pointed the script at
`data/raw/_processed-legacy/`, but that directory's `*.parquet` were gitignored
too: the `!…plant_emission_rates.parquet` negation only landed in `66fd940`,
eighteen days later. The rows lived on the F5 container's disk and went away
with it.

Re-landed by re-deriving from the on-disk CAMPD TX extracts, reproducing the F5
record exactly — **2022 → 130 TX plants** (full year), **2026 → 128** (`TX_2026`
spans 2026-01-01..03-31, so **PARTIAL**, Q1-weighted starts/rates, the same
caveat F5 recorded). Materiality is unchanged from the audit's grading: the
model reads only the pooled `year == 0` block (both
`fleet._plant_emission_rate_map` and `egrid._campd_rate_map` filter it), so no
solve is affected.

Two guards added so the failure class cannot repeat:
`derive_plant_emissions.py` now merges by year and **preserves the pooled
block** unless `--repool` is passed (the old script recomputed the pool from
whatever `--years` it was handed — running it for a back year would have
silently re-pooled every solve's CO2/NOx/SO2 basis), and `.gitignore` names
`fossil_co2_rates.parquet` in the `_processed-legacy` allowlist, which was in
the same tracked-but-ignored state.

### 7.4 Still MISSING after this session, with fix notes

| item | grade | fix |
|---|---|---|
| **MISO 2022 LMP bench — Nov/Dec tail** | **PARTIAL, 86.3% RT / 94.0% DA** | The bench builds from the committed raws with no fetch (audit §3.4 "(d)") — but the 2022 *staging* is short: chunks stop at `_da_p49` / `_rt_p45`, leaving DA missing 2022-12-10..12-31 and RT missing 2022-11-12..12-31. Not fetchable here: `docs.misoenergy.org` keeps a rolling ~3.5-yr window (re-verified — 2022-12-15 → **404**, 2023-12-15 → 200) and the documented fallback needs `MISO_PRICING_API_KEY`, absent from this environment. **Owner: supply the key (or re-fetch before more of 2023 ages off).** Jan–Oct is complete and real. The record now carries `da_cov`/`rt_cov` = `{annual, mon[12]}` so the partiality is machine-readable beside the statistic it qualifies — without it the one-hour December read as a $22.82/MWh December RT price |
| **PJM short-window 2023–2025 boundary sensitivity** | open, in-sample | The full-span rebuild drops SIX committed in-sample windows and adds none (1384/1 2025-09-24 + 2025-10-01, 1384/2 2023-02-03, 3954/1 2023-09-07, 10343/SG-101 2023-01-14 + 2023-03-08). Cause: the in-merit filter's high-load percentile is measured over a **centered** window, so Jan-2023 and late-2025 spans now see real neighbouring-year load instead of a truncated window. PJM is committed as a MERGE (committed 2023–2025 preserved byte-identical); whether the boundary-corrected detection is the better input is a rule-14 question **for a PJM calibration session**, not a data-intake one |
| everything else in §§3–4 | unchanged | The §3 per-ISO gap tables and the §4.2 per-ISO rows stand as written, minus the rows closed in §7.1. In particular ERCOT and CAISO still have **no LMP bench and no LMP raws** for any pre-2023 year — the single most disqualifying gap for both, and the one this session could not touch (ERCOT MIS SPP archives and CAISO OASIS `PRC_LMP` are separate fetch lanes) |

### 7.5 Two decisions that are the owner's, not this session's

1. **`eia_demand_profiles.parquet` 2018–2020 rebuild.** Downgraded from "hard
   blocker" to a **scoped** one by §7.2 — dispatch demand resolves for every ISO
   2018–2022 without it. It still gates `build_calibration_reference.py`
   (calref + `<ISO>_<year>_renewable_capacity.csv` for 2018–2020, no ISO has
   them). There is **no in-repo builder**; the artifact is hand-uploaded, and
   the underlying raw wide extracts DO cover 2018–2020 for every BA. So the
   choice is: **(a)** supply the rebuilt artifact, or **(b)** authorize writing
   a builder from the per-BA extracts. This session did neither — writing one
   would fix the ISO-total series' provenance for every downstream consumer at
   once, and that is a methodology commitment, not an intake.
2. **`derive_actual_tail.py::HOLDOUT_YEARS` widening.** It is `(2022, 2026)`
   today, so the 2018–2021 blocks now on disk (NEISO 2018–2021, NYISO
   2018–2021, PJM 2018–2021) emit no `actual_tail.json` entry. Widening it is
   the obvious mechanical step — **but the deriver is TIER-BLIND**: it gates
   every holdout year on the `complete` block alone
   (`_marker_isos()` reads `data.get("complete")`), which predates the
   2026-07-31 two-marker amendment. Widening it as-is would let a `complete`-only
   ISO emit a **locked-test** year (2019, and 2026 already), which is exactly
   the hole `scripts/lib/holdout_policy.py` was created to close. So the ask is
   two-part: **(a)** which years to add — the validation ladder {2018, 2020,
   2021} only, or the full 2018–2021 span; and **(b)** sign-off to route the
   deriver through `holdout_policy.py` so `final` gates 2019/2026 and `complete`
   gates the rest. Not changed here — it is a governance-gate edit, not data.

---

## 8. CORRECTION (2026-07-31, owner-prompted re-check) — the ERCOT 60-Day DAM Gen Resource Data 2018–2022 is already in the repo

This audit's §2 row "ISO availability overlay — ERCOT ✗ (60-Day DAM family
2023–25)" and §3.1's "Fix: fetch ERCOT 60-Day DAM disclosure archives for
2022", and the register §ERCOT verdict built on them ("MISSING 2018-2022 —
STRUCTURALLY UNOBTAINABLE"), are all **wrong about the source data**. Committed
under `data/raw/ercot-AS/` since 2026-07-28 (PR #3098 merge lineage):

- `60d_DAM_Gen_Resource_Data_{2018..2022}_*.parquet` — 18 files, ~39.8M rows.
  Each label year spans deliveries Nov-2 (y−1) → Nov-1 (y) (the 60-day
  publication lag); combined with the already-committed
  `ercot/60_DAY_DAM_DISCLOSURE_..._2023_Jan-Mar.parquet` fragment (deliveries
  2022-11-02..12-31), calendar coverage is **365/365/366/365/365 distinct
  delivery days for 2018–2022 — no gaps** (verified no-LP this session).
- Column set is a strict **superset** of the consumed
  `data/raw/ercot/60_DAY_DAM_DISCLOSURE_*` schema (extra: startup costs,
  Min Gen Cost, DME, per-product AS MCPCs) — so every consumer of the
  2023–2025 files can read these.
- Companions for the same span: `60d_DAM_Load_Resource_Data_{2018..2022}`,
  `60d_DAM_{Generation,Load}_Resource_ASOffers` back years, EnergyBids /
  EnergyOnlyOffers / Awards series.

Consequences: the whole availability family
(`ercot-thermal-dam-availability{,-hourly}.csv`, `ercot-noncampd-availability.csv`,
`ercot-nuclear-availability.csv`, and — via the PWRSTR rows the derive already
reads — `ercot-storage-capability.csv`) is **derivable for 2018–2022 from
committed data**: point the derives' input glob at (or map in) the `ercot-AS`
files, handle the label-vs-delivery-year offset (calendar year y needs label-y
AND label-(y+1) files), re-prove 2023–2025 byte-identical, then derive. No
fetch, no owner upload, no credentialed archive. The HSL, GTC-2018-2019 and
DAMASAGG "unobtainable" verdicts stand — none of those products is in
`ercot-AS`.

Root cause of the miss, both times: this audit's scanner truncated the
`ercot-AS/` directory listing to its first 20 entries (alphabetically, the
json.zip bundles), and the ERCOT intake session graded reachability from the
live MIS retention windows without checking what earlier AS-lane sessions had
already landed locally. Register §ERCOT carries the matching correction block.

### 8.1 CLOSED 2026-07-31 (follow-up derive session) — the family is derived

The derive session this correction called for has run (owner-authorized rule-22
Option-2 intake, no LP, no solve, no scoring, no registration). Outcome:

* **Wiring is a registry change, not a per-file list.** `config/paths.py` gained
  `ERCOT_DAM_DISCLOSURE_DIRS = (ERCOT_MIS_DIR, ERCOT_AS_DIR)` and
  `ercot_dam_disclosure_files(family, label_year)`, which globs both lanes under
  both filename conventions and sorts by (filename, directory). All four derives
  (`derive_ercot_{thermal_dam_availability,noncampd_availability,
  nuclear_availability,storage_capability}.py`) now resolve inputs through it.
* **Label-vs-delivery offset confirmed empirically, not assumed.** A label-`y`
  archive spans deliveries `y-1`-11-02 .. `y`-11-01, and the extract's
  `_Oct-Dec` fragment is the *remainder* of that archive — the previous
  November-December tail **plus** Oct 1 – Nov 1 of the label year (60 + 32 = the
  observed 92 distinct days). Scanning label `y` and `y+1` and filtering on
  Delivery Date therefore yields **365 / 365 / 366 / 365 / 365** days for
  2018-2022, with 2022's Nov 2 – Dec 31 tail coming from the committed
  `ercot/..._2023_Jan-Mar.parquet` fragment exactly as this block predicted.
* **This section's "strict superset" claim was too strong** — it holds for 2022
  only. The 2018-2021 files LACK `RRSFFR/RRSPFR/RRSUFR Awarded` (the RRS split
  post-dates them) and 2018-2019 also lack `QSE`. Immaterial to the availability
  derives, which consume only Delivery Date / Hour Ending / Resource Name /
  Resource Type / HSL / Resource Status / Settlement Point Name — **verified
  present in all 18 back-year files**, with identical arrow types and an
  identical `Resource Type` vocabulary to the 2023+ lane.
* **Recipes re-proved before any new year was derived**; four of five reproduce
  their committed 2023-2025 slice byte-identically. The nuclear CSV does not,
  and the cause is **pre-existing staleness, not the glob change** — proven by
  the pre-change and post-change scripts emitting sha256-identical output.

Graded caveats, coverage census, the Uri finding and the recovered DAM-AS
content are in register §ERCOT.
