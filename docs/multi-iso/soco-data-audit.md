# SOCO Data-Acquisition Audit (Phase 0)

Lane **SOCO-10** · 2026-09-13 · branch `claude/soco-10-audit-k3m9` · MODEL Opus
`claude-opus-5` · DATA PROFILE `shared` · base `origin/main` `2c2fc065`.

Charter: `docs/multi-iso/soco-addition-plan-2026-09.md` §5 row SOCO-10. Templates:
`docs/multi-iso/spp-data-audit.md`, `docs/multi-iso/miso-data-audit.md`. Process
authority: `docs/multi-iso/05-backcast-playbook.md` §1 (Phase 0) and §8.

**This lane RECOMMENDS. It decides nothing.** No topology is chosen here; no file under
`src/`, `scripts/`, `configs/`, `tests/`, `frontend/` or `data/` is touched; no parameter
is derived (rule 23 `[R-FROZEN-DERIVE]`); no mechanism is tested and no mechanism-matrix
cell moves (rule 28). Every number below is either **measured off a committed repo
artifact** — with the reproduction command in §8 — or **cited to a primary published
source** (URL + page/table). A cell with neither is written `pending SOCO-11/12/13`, never
a guess (rules 5 `[R-NO-MAGIC]`, 13 `[R-MEASURED]`, 14 `[R-ACCURATE]`).

The desk serves cards **S3** (topology), **S5** (VOLL), **S6** (adequacy), **S7** (CAES)
and **S8** (Vogtle) from §§5–7 of this document.

---

## 0. Headline

1. **The fleet census reconciles, and the charter's headline total is internally
   inconsistent with its own state list by exactly the row it flags.** EIA-860
   `Balancing Authority Code == "SOCO"` gives **336 plants with operable generators /
   788 generators / 70,667.2 MW nameplate** (66,161.2 MW summer, 69,096.8 MW winter). The
   charter's "335 / 786 / 70,665.7" is that figure **minus the 1.5 MW Massachusetts
   plant**, while the charter's per-state list (which includes `MA 1.5`) sums to
   70,667.2. Both are arithmetically right about different sets; only one of them is
   labelled. Every per-state figure is confirmed to 0.1 MW (§1.2).
2. **The MA row is a source defect and is REJECTED; the six FL plants are real and are
   KEPT.** Plant 67241 "401 South" (Berkshire County MA, 42.464 N / −73.184 W, NERC region
   **NPCC**, 1.0 MW battery + 0.5 MW PV, IPP) cannot be in a SERC balancing authority
   1,200 km away. The six Florida plants (309.6 MW, Escambia/Santa Rosa/Okaloosa/Jackson
   counties) are all **NERC SERC**, in the western Florida panhandle, contiguous with
   Alabama Power's territory. The rule applied is a **two-key consistency test** stated in
   §1.4 — it is geographic and regulatory, not a size threshold, and it rejects exactly one
   row out of 788.
3. **THE CEMS GAP IS TWICE AS SEVERE AS SPP's AND IT IS THE PROGRAM'S CRITICAL PATH.**
   `data/raw/campd-unit-level/` carries **no `AL_*`, no `GA_*` and no `FL_*` parquet for
   any year**. MS is present 2019–2026. The missing files for the backcast window are
   **{AL, GA} × {2023, 2024, 2025} = 6** (8 with the 2026 partials the SPP-11 precedent
   pulls; FL is a judgement call, §2.3). What the gap is worth: **91.6 % of SOCO's
   CEMS-eligible fossil capacity** — 45,797.3 MW of 50,005.0 MW — including **91.0 % of
   coal** and **90.5 % of gas-CC**. SPP's gap at its own audit was 44.9 %.
4. **GATE G19 IS CLOSED, BY MEASUREMENT, AND THE CONVENTION IS `America/Chicago`.** The
   committed `SOCO hourly.parquet`'s `Local time` column matches the DST-aware
   `America/Chicago` wall clock in **26,304 of 26,304 hours, zero mismatches**; it matches
   `America/New_York` in 3, fixed CST in 9,171 and fixed EST in 17,133. The route that
   wrote it is `scripts/data/convert_eia930.py`, whose `BA_TIMEZONES` **already carries
   `"SOCO": "US/Central"`**. The charter's concern was right but its premise was
   incomplete: the dict it checked (`fetch_eia930_hourly.BA_TIMEZONE`) has no SOCO key —
   **and neither does `build_eia930_hourly_from_raw.BA_TIMEZONE`, and both default to
   `America/New_York`.** So the *next* SOCO fetch through either route — including
   **SOCO-11's interchange pull, which imports that very dict** — writes **Eastern** local
   columns and silently one-hour-shifts against the committed file. That is a concrete,
   named, pre-solve defect (§3.4).
5. **The 2025 "7 hours short" is NOT missing data.** The file is a complete UTC block:
   26,304 consecutive hours, 2023-01-01 00:00 → 2025-12-31 23:00 UTC, **zero gaps, zero
   duplicate UTC hours**. Converting to Central shifts the window back 6 hours, so 7 rows
   land on local-date 2022-12-31 and the same 7 hour-ending labels (18–24 on 2025-12-31)
   were never fetched. `7 + 8,760 + 8,784 + 8,753 = 26,304` exactly. The fix is a 7-hour
   tail extension, not a repair (§3.2).
6. **`NG: PS` is not a SOCO reporting failure — it is a taxonomy cut-over, and the charter's
   framing hides a second, larger defect.** `NG: BAT`, `NG: PS`, `NG: SNB` and `NG: OES`
   have **byte-identical null patterns**: all four begin at **2024-07-15 01:00** local and
   all four are null again from **2024-07-16 01:00 to 2025-01-06 00:00** (4,177 h). The
   first window (13,470 h) is the pre-taxonomy period. Critically, **`NG: WAT` never goes
   negative before the cut-over** (min +32 MW over 13,470 h), so pumped-storage charging was
   **not** booked into hydro — it was not reported at all. **For 2023 and most of 2024
   there is no observable pumped-storage signal in EIA-930**, which is a direct constraint
   on the C1 `fuelmix` benchmark SOCO-31 will build (§3.3).
7. **The median-ratio screen finds ONE real fuel-column defect, and the repo catches
   neither it nor two others.** `NG: NG` posts **~70,000 MW in four 2025 hours**
   (2025-02-18 21:00, 2025-02-21 17:00, 2025-04-25 17:00, 2025-11-10 16:00) against a
   13,558 MW annual median and a **36,336 MW total gas nameplate** — 1.95× the entire gas
   fleet, physically impossible. Separately, the identity `Net generation = Demand + Total
   interchange` holds to **0.0000 TWh in 2023 and 2024** and breaks in **2025 only**
   (595 hours, max 13,120 MW, +0.696 TWh); and `Demand` notches to **12,638 MW** for one
   hour on 2025-10-23 16:00 between neighbours of 23,065 and 23,653. `_screen_demand_spikes`
   (high side only) and `_screen_demand_dropouts` (exact 0.0 only) catch **none** of the
   three; no screen in the repo touches a fuel column at all (§3.5).
8. **CARD S8 IS ANSWERED AND THE ANSWER IS WORSE THAN THE CARD ASSUMED.** The machinery
   resolves a within-year COD — but from a **capacity-weighted plant-level mean**, and
   `cod_ramp.effective_cod` prefers that plant mean over the generator's own
   `Operating Month` for the **online** date always (the per-unit preference exists only for
   *retirement*, the Homer City seam). Measured live: `load_cod_map()[649]` = **`(2005, 5)`**,
   so **Vogtle 3 and 4 are held online all 12 months of 2023, 2024 and 2025**; `[3]` =
   **`(1991, 3)`**, so **Barry A3 is online all of 2023**. Quantified against measured
   EIA-923 unit CFs (Vogtle 3 88.6 %, Vogtle 4 89.1 %): **+12.98 TWh of phantom nuclear in
   2023 (+24.8 %)**, which would put modelled 2023 nuclear at **65.4 TWh — above the
   measured 2025 value of 64.2 TWh, inverting the observed 52.4 → 63.0 → 64.2 step
   entirely** — and +2.17 TWh (+3.4 %) in 2024. **SOCO is the worst-affected footprint in
   the registered set** (3,040.3 MW trapped, 2.7× SPP's 1,127.4 MW) and Vogtle 3 and 4 are
   the two largest trapped units in the national fleet (§4).
9. **FERC-714 has EIGHT respondents in this footprint, not three — so the OpCo sum cannot
   reconcile to the BA and SOCO-11 must not expect it to.** Measured off PUDL's
   `core_ferc714__respondent_id`: Alabama Power (2), Georgia Power (183), Mississippi Power
   (184), **Gulf Power (185)**, **Oglethorpe (107)**, **MEAG (210)**, **PowerSouth (1)**, and
   **"Southern company" (142, `eia_code` 18195)** — the last of which is very likely a
   BA-level planning-area filer and therefore a *direct* cross-check against EIA-930.
   Oglethorpe (6,472.2 MW) and MEAG (594.1 MW) own generation inside Georgia and serve
   Georgia load that Georgia Power's own planning area does not. This is why §6 recommends
   the 3-zone split **on the fleet's state FIPS, never on OpCo identity**.
10. **SOCO is winter-peaking in 2 of 3 backcast years.** Annual peaks: 45,558 MW on
    2023-08-25 16:00 (summer), **47,368 MW on 2024-01-17 07:00** and **46,490 MW on
    2025-01-22 08:00** (both winter morning). In 2025 the summer peak (46,372 MW) sits
    **0.25 %** below the winter peak. A scalar `PLANNING_RESERVE_MARGIN_BY_ISO["SOCO"]`
    would misrepresent this system; Georgia Power's own TRM is stated by season for exactly
    this reason (§5 row 1).

---

## 1. Status table

| # | Item | Source | Status | File path | Notes |
|---|------|--------|--------|-----------|-------|
| 1 | SOCO fleet census (plants / gens / MW by tech, state, owner) | EIA-860 current vintage, `Balancing Authority Code == "SOCO"` | **got** | `data/raw/eia-860/eia860_plant.parquet` + `eia860_generator_operable.parquet` | 336 plants / 788 gens / 70,667.2 MW nameplate; 335 / 786 / 70,665.7 after the MA rejection (§1.4). 401 plants carry the SOCO BA code before the operable join. Reconciled to Southern Company's 2024 10-K on a stated bridge (§1.5). |
| 2 | CAMPD/CEMS state coverage vs the SOCO footprint | `data/raw/campd-unit-level/<ST>_<yr>.parquet` | **BLOCKED — the critical path** | MS 2019–2026 present; **AL, GA, FL absent for every year** | Missing for the window: **{AL, GA} × {2023, 2024, 2025}**; +2026 partials and +FL per §2.3. Worth **91.6 %** of CEMS-eligible fossil MW. **SOCO-11.** |
| 3 | EIA-930 SOCO hourly demand + fuel mix | EIA Hourly Electric Grid Monitor | **got (4 defective hours + 2 unscreened artifacts + a taxonomy cut-over)** | `data/raw/eia-930-hourly/SOCO hourly.parquet` | 26,304 rows, complete UTC block 2023-01-01 → 2025-12-31, 20 columns. Nuclear cross-validates against EIA-923 to **0.6 / 0.1 / 0.1 %** (§3.6). Defects §3.5. |
| 4 | EIA-930 SOCO per-BA long extracts | EIA API v2 | **got** | `data/raw/SOCO_fueltype.parquet` (243,517 rows), `SOCO_region.parquet` (105,213 rows) | UTC-stamped twins of item 3, same span. 12 fuel codes / 4 region codes. |
| 5 | Timezone convention for every SOCO series | measured off item 3 | **got — GATE G19 CLOSED** | — | `America/Chicago`, DST-aware, hour-ending 1..24 (25 on fall-back day). 0/26,304 mismatches. Two sibling dicts still default SOCO to Eastern (§3.4). |
| 6 | **A price series for SOCO** | — | **DOES NOT EXIST → card S2** | `_validation-source/actual_lmp_hourly_SOCO.parquet` (absent) | Southern publishes no LMP; SEEM publishes no price (plan §2.6). **SOCO-13**, STOP-gated. Nothing in this audit assumes one. |
| 7 | `actual_lmp.json` SOCO block | `scripts/data/derive_actual_lmp.py` | **absent** | `data/raw/_validation-source/actual_lmp.json` | Downstream of item 6. **SOCO-31**, and only if S2 yields a series. |
| 8 | EIA-923 monthly delivered fuel costs, SOCO plants | EIA-923 | **got** | `data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet` | 471 / 441 / 471 rows over **30 / 31 / 31** SOCO plants for 2023/24/25 (2026 partial: 102 rows / 20 plants). The rule-13 measured fuel input playbook §0.5 requires. |
| 9 | EIA-923 monthly generation, SOCO plants | EIA-923 | **got (2025 partial)** | `data/raw/_processed-legacy/eia923_monthly_generation.parquet` | SOCO plant-rows **524 (2023) / 541 (2024) / 218 (2025)** over 311 / 330 / **108** plants — 2025 is a preliminary release, the same caveat SPP-10 recorded. Nuclear is complete for every year and is what closes §4. |
| 10 | FERC-714 hourly planning-area demand (the zonal-load spine) | PUDL ETL of FERC Form 714 | **partial — respondent list got, hourly series pending** | `data/raw/zone-specific-demand/SOCO/` (does not exist) | **Eight** footprint respondents identified and named (§6.2), not three. Hourly series + the BA reconciliation are **SOCO-11**. |
| 11 | SOCO BA-to-BA interchange | `fetch_eia930_interchange.py --ba SOCO` | **pending SOCO-11** | `data/raw/eia-930-interchange/SOCO interchange hourly.parquet` | Needs `EIA_API_KEY`. ⚠ **Will write Eastern local columns unless §3.4's dict gap is fixed first.** |
| 12 | eGRID plant database | EPA eGRID 2023 | **got (national)** | `data/fleet/egrid2023_data_rev2.xlsx` | `zone_assignment._EGRID_VINTAGE = 2023` is a **module-level scalar, not a per-ISO dict** — SOCO needs no entry, exactly as SPP needed none. |
| 13 | Southern IRP / SERC assessment / SEEM reports / NRC status | public PDFs | **pending SOCO-12** | `data/raw/soco-planning/` (does not exist) | Georgia Power's 2025 IRP TRM values are cited at §5 row 1 from an intervenor-testimony route; the **primary** IRP volume is SOCO-12's. Alabama Power files no comparable public IRP (§5 row 1 note). |
| 14 | Southern long-term load forecast (LTLF) edition + vintage | Georgia Power IRP / Alabama PSC | **blocked → SOCO-12; a W2 PRECONDITION** | `data/raw/load-forecast/soco/soco.csv` (does not exist) | Gate G12. One citable anchor already in hand: Georgia Power winter peak **16,284 MW**, +8,205 MW growth to winter 2030/31 (§5 row 12). |
| 15 | Delivered gas to electric power, AL/GA/MS monthly | EIA series `N3045{AL,GA,MS}3m` | **pending SOCO-12** | `data/raw/gas-prices/eia_delivered_gas_<ST>_monthly_2023-2025.csv` | Exact series codes and the committed SPP naming convention at §5 row 6. |
| 16 | State RPS floors AL / GA / MS | DSIRE | **got — all three are NONE** | cited inline | §5 row 10. The row is *answered*, not blank. |
| 17 | Data-profile token `soco` collision check | `ls data/raw` | **got — clean** | — | Only `SOCO_fueltype.parquet` / `SOCO_region.parquet` match. But see §7 note: a `soco` profile does **not** pull `eia-930-hourly/SOCO hourly.parquet`, which lives under a `shared` directory. |

---

## 2. Item 1/2 — the fleet census and the CEMS state diff

### 2.1 Method

`data/raw/eia-860/eia860_plant.parquet` filtered to `Balancing Authority Code == "SOCO"`
(Balancing Authority Name, single value: **"Southern Company Services, Inc. - Trans"**),
inner-joined on `Plant Code` to `eia860_generator_operable.parquet`. This is the **same
BA-code crosswalk the model itself uses** (`zone_assignment._ISO_TO_BA_CODE`,
`fleet.models.BA_CODE_TO_ISO`), so SOCO's future entry is `"SOCO"` and the census boundary
is the registration boundary. `get_iso_config("SOCO")` was **not** called: it does not
exist. `eia860_generators.parquet` was **not** read — it is a curated seven-ISO file with
no SOCO rows, and reading it as the fleet is the trap the charter warns about.

Three numeric conventions, stated because they drive every reconciliation below:

* **Whole-unit, not ownership share.** EIA-860 reports each generator once, at its full
  nameplate, under its *operator*. Southern's 10-K reports each registrant's *percentage
  share*. These measure different things (§1.5 / §2.5).
* `Summer Capacity (MW)` / `Winter Capacity (MW)` arrive as **strings** in this parquet and
  must be `pd.to_numeric`-coerced; a naive `.sum()` concatenates them.
* Counts are **plants with at least one operable generator** (336). The plant table alone
  carries **401** SOCO plants — 65 of them have no operable generator row.

### 2.2 Census — 788 operable generators, 70,667.2 MW nameplate

| Technology | Plants | Gens | Nameplate MW | Summer MW | Winter MW |
|---|---:|---:|---:|---:|---:|
| Natural Gas Fired Combined Cycle | 24 | 105 | 20,702.8 | 19,484.1 | 20,707.7 |
| Conventional Steam Coal | 6 | 16 | 12,234.7 | 11,512.0 | 11,512.0 |
| Natural Gas Fired Combustion Turbine | 32 | 110 | 11,676.8 | 9,985.2 | 11,443.3 |
| Nuclear | 3 | 8 | 8,282.4 | 8,080.0 | 8,080.0 |
| Solar Photovoltaic | 164 | 168 | 5,825.9 | 5,813.8 | 5,819.2 |
| Natural Gas Steam Turbine | 13 | 26 | 3,839.2 | 3,338.2 | 3,341.8 |
| Conventional Hydroelectric | 44 | 141 | 3,317.6 | 3,296.8 | 3,299.5 |
| Wood/Wood Waste Biomass | 28 | 51 | 1,719.2 | 1,632.0 | 1,653.6 |
| Petroleum Liquids | 25 | 93 | 1,340.5 | 1,120.8 | 1,341.8 |
| Hydroelectric Pumped Storage | 3 | 9 | 1,306.6 | 1,569.4 | 1,568.2 |
| Batteries | 7 | 7 | 148.7 | 148.7 | 148.7 |
| Natural Gas with Compressed Air Storage | 1 | 1 | 110.0 | 25.0 | 25.0 |
| Petroleum Coke | 1 | 2 | 90.0 | 83.8 | 84.6 |
| Landfill Gas | 12 | 44 | 61.8 | 60.4 | 60.5 |
| Natural Gas Internal Combustion Engine | 2 | 5 | 7.0 | 7.0 | 7.0 |
| Other Gases | 1 | 1 | 3.8 | 3.8 | 3.8 |
| Other Natural Gas | 1 | 1 | 0.2 | 0.2 | 0.2 |
| **Total** | **336** | **788** | **70,667.2** | **66,161.2** | **69,096.8** |

Every technology row **confirms the charter to 0.1 MW**. Three observations the charter's
list does not draw out:

* **There is no wind in the SOCO fleet at all** — zero generators, and `NG: WND` is
  identically 0.000 TWh in all three EIA-930 years. Any SOCO registry entry that assumes a
  wind class (ELCC, queue cap, offer band) is describing an empty set.
* **Pumped storage has summer/winter capacity ABOVE nameplate** (1,569.4 / 1,568.2 vs
  1,306.6). This is the normal EIA convention for PSH (turbine rating vs generator
  nameplate) and is not a defect — but a loader that assumes `summer ≤ nameplate` will trip
  on exactly these 9 rows.
* **The CAES unit** (McIntosh, plant 7063, 110.0 MW nameplate but **25.0 MW summer and
  winter**) derates 77 % against nameplate. Card S7's "map to a gas CT" recommendation
  should map on the **25 MW rating**, not the 110 MW nameplate, or it injects 85 MW of
  capacity that the source itself says is not there.

### 2.3 By state, and the CEMS diff

| State | Plants | Gens | Nameplate MW | Summer MW | Winter MW | Charter | CEMS files present |
|---|---:|---:|---:|---:|---:|---|---|
| GA | 252 | 539 | 41,284.4 | 38,462.2 | 40,324.4 | 41,284.4 ✓ | **none, any year** |
| AL | 62 | 200 | 24,494.0 | 23,246.8 | 24,129.5 | 24,494.0 ✓ | **none, any year** |
| MS | 15 | 32 | 4,577.7 | 4,152.0 | 4,324.6 | 4,577.7 ✓ | 2019–2026 ✓ |
| FL | 6 | 15 | 309.6 | 298.8 | 316.8 | 309.6 ✓ | **none, any year** |
| MA | 1 | 2 | 1.5 | 1.5 | 1.5 | 1.5 ✓ — **REJECTED, §1.4** | n/a |

**The missing list, stated as SOCO-11's work order:**

| Priority | Files | Why |
|---|---|---|
| **1 — blocking** | `AL_2023`, `AL_2024`, `AL_2025`, `GA_2023`, `GA_2024`, `GA_2025` | 91.6 % of CEMS-eligible fossil MW. Without these there is no per-plant binning, no unit outage overlay, and no C1 attribution for the fossil fleet. |
| 2 — precedent | `AL_2026`, `GA_2026` | SPP-11 pulled 2026 partials alongside; costs one fetch each and pre-positions the next window. |
| 3 — judgement | `FL_2023..2025` | The 6 FL plants hold **102.0 MW** of CEMS-eligible fossil (0.2 % of the footprint), all **Industrial CHP** at one site (Ascend Performance Materials Pensacola). Recommendation: **pull them**, because `load_campd_hourly` filters every loaded state to the ISO's own fleet, so an extra state costs storage rather than correctness — and *not* pulling them makes the FL adjudication of §1.4 unverifiable against metered data. |

**`campd.ISO_STATES["SOCO"]` should be `("AL", "GA", "MS", "FL")`** on the §1.4 ruling.
Whether FL's files are fetched is separable from whether FL is in the state list.

### 2.4 What the gap is worth

CEMS-eligible = the fossil technologies that report Part 75 hourly data (coal, gas CC/CT/ST,
petroleum liquids, petroleum coke, other gases, gas ICE, CAES).

| | Total MW | Present (MS) | **Missing (AL+GA+FL)** | Missing % |
|---|---:|---:|---:|---:|
| All CEMS-eligible fossil | 50,005.0 | 4,207.7 | **45,797.3** | **91.6 %** |
| Conventional steam coal | 12,234.7 | 1,096.6 | 11,138.1 | **91.0 %** |
| Natural gas combined cycle | 20,702.8 | 1,972.4 | 18,730.4 | **90.5 %** |

For scale: the equivalent SPP number at its own Phase-0 audit was **44.9 %**
(`spp-data-audit.md` §2.4). **SOCO's CEMS gap is twice as severe**, and unlike SPP's it
covers the *entire* coal fleet bar one Mississippi plant. Plan §6 row 1 is correct that
this is the critical path; this census says by how much.

### 2.5 Reconciliation against Southern Company's published fleet

Primary source: **Southern Company Form 10-K for fiscal year 2024, Item 2 "Properties",
"Generating Capacity" table, printed pages I-30 through I-33**
([SEC EDGAR, `so-20241231.htm`](https://www.sec.gov/Archives/edgar/data/92122/000009212225000018/so-20241231.htm)).
The table's own headnote states the basis: *"for jointly-owned facilities, the nameplate
capacity shown represents the Registrant's portion of total plant capacity, with ownership
percentages provided if less than 100%."*

| 10-K line (KW) | MW | In the SOCO BA? |
|---|---:|---|
| Total Alabama Power Generating Capacity — 12,942,377 | 12,942.4 | yes |
| Total Georgia Power Generating Capacity — 14,789,068 | 14,789.1 | yes |
| Total Mississippi Power Generating Capacity — 3,517,874 | 3,517.9 | yes |
| Total SEGCO Generating Capacity — 1,019,680 | 1,019.7 | yes (Gaston 1–4, Wilsonville AL) |
| Total Southern Power Generating Capacity — 12,647,880 | 12,647.9 | **mostly NO** — NC, TX, CA, NM, NV, WY, SD, OK, WV, DE |
| **Total Southern Company System — 44,916,879** | **44,916.9** | nationwide, ownership share |

**The two figures are not comparable as stated, and the bridge is the finding.** EIA-860's
70,667.2 MW is *whole-unit nameplate for every owner in the balancing authority*; the
10-K's 44,916.9 MW is *Southern's ownership share, everywhere in the United States*. The
bridge, measured:

1. **Southern regulated + SEGCO, in footprint, ownership share:**
   12,942.4 + 14,789.1 + 3,517.9 + 1,019.7 = **32,269.1 MW**.
2. **Southern Power, in footprint:** EIA-860 attributes **6,563.4 MW** to `Southern Power
   Co` inside SOCO (AL 3,299.7 + GA 3,263.7); the 10-K's AL/GA lines for Southern Power
   (Franklin, Harris, Wansley 6–7, Addison, Dahlberg, Pawpaw, Sandhills) total **5,853.0
   MW** on the share basis. The 710 MW difference is the share-vs-whole basis on Wansley CC
   plus smaller Georgia solar.
3. **Non-Southern owners inside the BA, whole-unit:** Oglethorpe **6,472.2**, PowerSouth
   **2,070.9**, USACE-Mobile District federal hydro **1,142.2**, MEAG **594.1**, and ~150
   further IPP / industrial-CHP owners making up the balance. `Electric Utility` sector is
   50,832.2 MW of the total; `IPP Non-CHP` 17,253.7; `Industrial CHP` 2,110.2.
4. **The joint-ownership wedge, demonstrated on one line.** 10-K system **Nuclear =
   4,786,706 KW = 4,786.7 MW** (Farley 100 %, Hatch 50.1 %, Vogtle 45.7 %) against EIA-860
   SOCO **Nuclear = 8,282.4 MW** whole-unit. The 3,495.7 MW difference is the co-owners'
   share of Vogtle and Hatch — Oglethorpe 30 %, MEAG 22.7 %, Dalton 2.2 %. That the two
   bases differ by exactly the published co-ownership percentages is the cleanest available
   check that the census filter is right.

**Verdict: the census reconciles.** No unexplained capacity appears on either side, and the
gaps are all attributable to a stated basis difference or a named non-Southern owner.

### 2.6 The adjudications the charter asked for

**(a) The 1.5 MW "MA" row — REJECTED as a source defect.**

| Field | Value |
|---|---|
| Plant Code | 67241 |
| Plant Name | 401 South |
| Location | Berkshire County, **MA**; 42.464 N, −73.184 W |
| NERC Region | **NPCC** |
| Utility | Madison Energy Investments LLC (IPP Non-CHP) |
| Generators | `401SB` 1.0 MW Batteries + `4SPV1` 0.5 MW Solar PV, both COD 2023-12 |

**The rule applied — a two-key consistency test, not a size threshold:**

> A plant self-reporting `Balancing Authority Code == "SOCO"` is admitted to the footprint
> only when **both** (i) its `NERC Region` is `SERC` — the region the SOCO BA sits in — **and**
> (ii) its state is one of AL / GA / MS / FL-panhandle, the states the SOCO transmission
> system reaches. A row failing **either** key is a self-reporting error in EIA-860's BA
> field, not a footprint member.

"401 South" fails both keys: NPCC, and western Massachusetts, ~1,200 km from the nearest
Southern asset, inside the ISO-NE (`ISNE`) footprint. The BA field is a **respondent-entered
free field** in EIA-860 and mis-entry is a known failure mode; nothing else about the row is
anomalous. Rejecting it costs 1.5 MW (0.002 % of the fleet) and 1 of 788 generators. The
practical consequence is small but the *rule* is not: it is what SOCO-20 should encode so
the next vintage's mis-entry is caught rather than silently zoned.

**Consequence for SOCO-20:** `_SOCO_STATE_ZONES` must have **no FIPS 25 (MA) key**, and the
zone splitter should **fail loud rather than fall back** on a SOCO-coded plant outside
AL/GA/MS/FL — a silent `_LARGEST_ZONE` fallback would put a Massachusetts battery in Georgia.

**(b) The six Florida plants — KEPT, in footprint.**

| Plant | County | NERC | Technology | MW | Sector |
|---|---|---|---|---:|---|
| 10416 Pensacola Florida Plant (Ascend Performance Materials) | Escambia | SERC | Gas ST ×3 + Gas CT | 102.0 | Industrial CHP |
| 50250 International Paper Pensacola | Escambia | SERC | Wood biomass ×2 | 82.8 | Industrial CHP |
| 56522 Springhill Gas Recovery | Jackson | SERC | Landfill gas ×6 | 4.8 | IPP |
| 59689 Gulf Coast Solar Center I | Okaloosa | SERC | Solar PV | 30.0 | IPP |
| 59690 Gulf Coast Solar Center II | Santa Rosa | SERC | Solar PV | 40.0 | IPP |
| 59691 Gulf Coast Solar Center III | Escambia | SERC | Solar PV | 50.0 | IPP |
| **Total** | | | | **309.6** | |

All six pass both keys: **NERC region SERC** (not FRCC — the Florida panhandle west of the
Apalachicola is in SERC, which is precisely the historic Gulf Power service area) and
geographic contiguity (Escambia County FL borders Escambia County AL; the northernmost is
30.93 N, well inside the Southern system's reach). They are kept.

**Two caveats that belong to other lanes, stated so nobody is surprised:**

1. **Generation membership ≠ load membership.** Gulf Power was a Southern operating company
   until January 2019, was sold to NextEra and merged into Florida Power & Light in January
   2021, and **Gulf Power still files FERC Form 714 as its own planning-area respondent**
   (id 185, §6.2). Whether the *load* of the former Gulf Power territory is inside the
   metered `SOCO hourly.parquet::Demand` series is a **question about the demand series, not
   the fleet**, and it is **SOCO-11's** to settle during the FERC-714 reconciliation. This
   audit takes no position; the 309.6 MW of generation is in the BA on the evidence
   available, which is what the fleet census answers.
2. **Zone assignment.** If card S3 lands 3 zones, FIPS 12 (FL) needs an explicit key. The
   recommendation is `12 → Alabama Power` (the panhandle interconnects west), stated in §6.4.

---

## 3. Item 3/5 — EIA-930, the timezone, and the defect screen

### 3.1 Span, shape and energy

`data/raw/eia-930-hourly/SOCO hourly.parquet`: **26,304 rows × 20 columns**, a *complete*
UTC block **2023-01-01 00:00 → 2025-12-31 23:00 UTC** — zero gaps, zero duplicate UTC
hours. Columns: `UTC time`, `Local date`, `Hour`, `Local time`, `Demand forecast`, `Demand`,
`Net generation`, `Total interchange`, and `NG:` {`COL`, `NG`, `NUC`, `WAT`, `SUN`, `WND`,
`OIL`, `BAT`, `PS`, `SNB`, `OES`, `OTH`}. All value columns `float32`.

| TWh (local-date year) | 2023 | 2024 | 2025 | charter |
|---|---:|---:|---:|---|
| Demand | 229.469 | 239.326 | 239.359 | 229.47 / 239.33 / 239.36 ✓ |
| Net generation | 239.625 | 250.157 | 251.683 | 239.63 / 250.16 / 251.68 ✓ |
| Total interchange | 10.156 | 10.831 | 13.021 | 10.2 / 10.8 / 13.0 ✓ |
| `NG: NG` gas | 129.592 | 126.057 | 125.397 | 129.6 / 126.1 / 125.4 ✓ |
| `NG: NUC` nuclear | 52.435 | 62.989 | 64.167 | 52.4 / 63.0 / 64.2 ✓ |
| `NG: COL` coal | 38.252 | 40.532 | 44.047 | 38.3 / 40.5 / 44.0 ✓ |
| `NG: WAT` hydro | 8.446 | 6.917 | 5.926 | 8.45 / 6.92 / 5.93 ✓ |
| `NG: SUN` solar | 8.362 | 10.141 | 9.981 | 8.36 / 10.14 / 9.98 ✓ |
| `NG: OTH` | 2.537 | 2.466 | 1.874 | — |
| `NG: WND` | **0.000** | **0.000** | **0.000** | — (no wind in the fleet) |
| hours | 8,760 | 8,784 | **8,753** | ✓ |

**Every charter figure is confirmed.** Peak demand and its season (card S6 evidence):

| Year | Annual peak | When (local, America/Chicago) | Winter (DJF) peak | Summer (JJAS) peak | Load factor |
|---|---:|---|---:|---:|---:|
| 2023 | 45,558 MW | 2023-08-25 16:00 — **summer** | 37,890 | 45,558 | 0.575 |
| 2024 | 47,368 MW | 2024-01-17 07:00 — **winter** | 47,368 | 44,882 | 0.575 |
| 2025 | 46,490 MW | 2025-01-22 08:00 — **winter** | 46,490 | 46,372 | 0.588 |

**Interchange sign convention:** `Total interchange` is **positive = NET EXPORT**. The
identity `Demand + Total interchange = Net generation` closes to **0.0000 TWh in 2023 and
2024** and TI is positive in 25,269 of 26,304 hours, so SOCO is a net exporter of
**10.156 / 10.831 / 13.021 TWh**. (The 2025 break in the identity is a *defect in
`Net generation`*, §3.5c — not a different convention.)

### 3.2 The "7 missing hours" of 2025 — explained, and NOT a defect

Local-date row counts are `2022: 7`, `2023: 8,760`, `2024: 8,784`, `2025: 8,753`, summing
to exactly 26,304. The arithmetic:

* The file is bounded on **UTC**, 2023-01-01 00:00 → 2025-12-31 23:00.
* Central local time is UTC−6 (CST) at both ends, so the *local* window is
  2022-12-31 18:00 → 2025-12-31 17:00 (hour-ending labels).
* **7 hour-ending labels therefore spill off the front** into local-date 2022-12-31 (hours
  ending 1–7 on that date, i.e. local 18:00 through 00:00), and **the same 7 labels are
  absent from the tail**: hours ending **18, 19, 20, 21, 22, 23, 24 on 2025-12-31**, which
  are UTC 2026-01-01 00:00–06:00.

So **nothing is missing from the source**; the fetch was bounded on UTC and the last 7
Central hours of 2025 were never requested. Two correct remedies, and one wrong one:

* **Correct (a):** extend the fetch by 7 UTC hours (through 2026-01-01 06:00 UTC).
* **Correct (b):** bound future SOCO fetches on **local** time, not UTC.
* **WRONG:** padding, interpolating or holding the 7 hours forward. A backcast year that
  synthesises its own last 7 hours is scoring the model against 7 invented hours. The plan
  §7 G19 mitigation already says "explained, not padded"; this is the explanation.

The same arithmetic applies to the 7-row 2022 sliver: **drop it**, do not fold it into
2023. Its 0.150 TWh of demand belongs to a year outside the window.

### 3.3 `NG: PS` — a taxonomy cut-over, not a SOCO failure

The charter reports `NG: PS` NaN in 17,647 of 26,304 hours "despite 1,306.6 MW of pumped
storage in the fleet". Measured, the pattern is sharper and it is shared:

| Column | Nulls | First non-null | Last non-null |
|---|---:|---|---|
| `NG: BAT` | 17,647 | **2024-07-15 01:00** | 2025-12-31 17:00 |
| `NG: PS` | 17,647 | **2024-07-15 01:00** | 2025-12-31 17:00 |
| `NG: SNB` | 17,647 | **2024-07-15 01:00** | 2025-12-31 17:00 |
| `NG: OES` | 17,647 | **2024-07-15 01:00** | 2025-12-31 17:00 |

All four are **byte-identical**, and they resolve into two windows:

| Window | Hours | Reading |
|---|---:|---|
| 2022-12-31 18:00 → 2024-07-15 00:00 | 13,470 | **Pre-taxonomy.** These four fuel-type codes did not exist in the EIA-930 fuel-type breakdown before 2024-07-15. Their absence is a schema fact, not a SOCO reporting gap. |
| 2024-07-16 01:00 → 2025-01-06 00:00 | 4,177 | **A genuine reporting gap.** SOCO reported the four new codes for exactly **24 hours**, then stopped, resuming 2025-01-06 01:00. `NG: WAT` is *also* null over the last 1,464 hours of this window (2024-11-06 01:00 → 2025-01-06 00:00) — which is what the 1.051 TWh 2024 gap between `sum(NG:*)` and `Net generation` is made of. |

**The load-bearing finding — and it is a C1 constraint, not a curiosity.** `NG: WAT`
**never goes negative before the cut-over**: min **+32 MW** over 13,470 hours, zero negative
hours. After it, `NG: PS` ranges **−1,655 to +1,732 MW with 4,850 negative (charging)
hours**. Pumped-storage charging was therefore **not folded into hydro** in the pre-taxonomy
period — it was **not reported at all**. Consequences SOCO-31 must design around, and
SOCO-40 must not discover mid-solve:

1. For **2023 and 202 days of 2024, SOCO's 1,306.6 MW of pumped storage is invisible in
   EIA-930.** A `fuelmix` benchmark built from these columns has **no PS row** for those
   periods and cannot score PS dispatch in them.
2. `Net generation` for those hours is **net of PS charging** without attributing it, so the
   fuel shares are shares of a quantity that already nets an unobserved sink.
3. EIA-923 monthly generation **does** carry the three PS plants (Wallace Dam, Carters,
   Rocky Mountain) for every year and is the fallback anchor. That is a monthly, not hourly,
   constraint — state it rather than dressing it as an hourly benchmark.

### 3.4 GATE G19 — the timezone convention, closed by measurement

**The evidence, not an assumption.** Over all 26,304 rows, `Local time` compared against
each candidate:

| Candidate convention | Mismatching hours |
|---|---:|
| **`America/Chicago`, DST-aware** | **0** |
| `America/New_York`, DST-aware | 26,301 |
| Fixed UTC−6 (CST year-round) | 9,171 |
| Fixed UTC−5 (EST year-round) | 17,133 |

Corroborating detail, all measured:

* The UTC→local offset takes exactly **two values, −6 (CST, 9,171 h) and −5 (CDT,
  17,133 h)** — a Central pair. An Eastern file would show −5/−4.
* The offset **switches on the correct US DST dates** in each year: the 2024 and 2025
  Mar 8–11 and Nov 1–4 windows each contain both offsets; the 2023 windows contain one each,
  because 2023's transitions were Mar 12 and Nov 5, outside those windows.
* **Three duplicate `Local time` values**, one per year, at **2023-11-05 01:00, 2024-11-03
  01:00, 2025-11-02 01:00** — the fall-back repeated hour, present exactly as a DST-aware
  wall clock produces it, and **absent** from the `UTC time` column (zero duplicates there).

**`Hour` is EIA's hour-ENDING label, 1..24 (25 on the fall-back day), and `Local date` is
the date the hour BEGINS in.** `Hour == Local time.hour` for hours ending 1–23; for hour
ending 24, `Local time` is **00:00 of the following day** while `Local date` stays on the
previous day. That accounts for all **1,096** rows where `Local date != Local time.date()`.
Worked example, row 30: `UTC 2023-01-02 06:00`, `Local date 2023-01-01`, `Hour 24`,
`Local time 2023-01-02 00:00`.

**The convention every downstream SOCO series must adopt:**

> **`America/Chicago`, DST-aware, hour-ending.** Every SOCO series — EIA-930 interchange,
> FERC-714 zonal load, CEMS unit hourlies, derived solar shapes, the calibration reference,
> and any price series card S2 yields — is stamped in `America/Chicago` and aligned to the
> committed `SOCO hourly.parquet`'s `UTC time` column, which is the unambiguous join key.
> **Join on `UTC time`, never on `Local time`** — `Local time` is non-unique once a year by
> construction, and a join on it silently doubles one hour and drops another.

**Why Central is the right choice even though Georgia is Eastern.** This is not a
convenience: the whole footprint is one balancing authority, dispatched from one control
centre, and EIA publishes it on one clock. `convert_eia930.BA_TIMEZONES` records that clock
as `US/Central` with the source *"EIA Hourly Electric Grid Monitor, BA reference table"*,
and the measurement above confirms the committed file was written that way. Splitting a
zone's series onto Eastern because its fleet sits in Georgia would put the Georgia zone's
hour *t* against the Alabama zone's hour *t+1* in the same LP row — a one-hour
mis-registration of ~40 GW of load against ~41 GW of fleet. **The timezone is a property of
the BA, not of the zone.** If card S3 lands 3 zones, all three are Central.

**THE LIVE DEFECT THIS AUDIT FOUND — and it fires on SOCO-11, not later.** There are
**three** BA-timezone dicts in the repo and **only one** knows about SOCO:

| Dict | SOCO entry? | Default | Written by it |
|---|---|---|---|
| `scripts/data/convert_eia930.py::BA_TIMEZONES` (line 55) | **`"SOCO": "US/Central"` ✓** | n/a (KeyError) | the committed `SOCO hourly.parquet` |
| `scripts/data/fetch_eia930_hourly.py::BA_TIMEZONE` (line 48) | **NO** | `America/New_York` | any future SOCO hourly fetch |
| `scripts/data/build_eia930_hourly_from_raw.py::BA_TIMEZONE` (line 45) | **NO** | `America/New_York` | any rebuild from the long extracts |

And `scripts/data/fetch_eia930_interchange.py` line 57 **imports
`fetch_eia930_hourly.BA_TIMEZONE`** and applies it at line 76. So **manifest row 3 — the
SOCO interchange pull, SOCO-11's deliverable — will write Eastern local columns** and sit
one hour off the committed demand file for most of the year, with no error raised.

> **ROUTED TO SOCO-20 (code) with a WARNING TO SOCO-11 (now).** The fix is two one-line
> additions — `"SOCO": "America/Chicago"` in both missing dicts — and it belongs in the
> registration PR, not here (this lane touches no `scripts/`). **Until it lands, SOCO-11
> must either patch locally before fetching, or join its interchange output on `UTC time`
> and re-derive the local columns from `convert_eia930`'s convention.** Note the two dicts
> also disagree in *spelling* (`US/Central` vs `America/Chicago`); they are the same zone
> and `zoneinfo` resolves both, but SOCO-20 should use `America/Chicago` to match the
> majority convention in the two IANA-named dicts.

### 3.5 The defect screen, run over every column

**Method.** Two screens exist in the repo and both are **demand** screens. Applied per
(column, local year):

* `scripts/data/curate_demand_profile.py::screen_physical_bounds` — flags `v <= 0` or
  `v > MAX_MEDIAN_RATIO (5.0) × median`.
* `src/market_sim/data/eia930/demand.py::_screen_demand_spikes` — repairs
  `v > 2.5 × annual median`; `_screen_demand_dropouts` repairs literal `0.0`.

**Result on `Demand`: clean, and both screens are no-ops.** Max/median ratios are
**1.835 / 1.829 / 1.789** for 2023/24/25 — far under the 2.5× repair threshold and under
the 5.0× bound. Zero literal-`0.0` hours. **SOCO needs no demand-spike repair**, unlike SPP.

**Result on the fuel columns — the screen is the wrong instrument for most of them, and
that matters.** `screen_physical_bounds` flags 3,975–4,031 hours of `NG: SUN` per year at
>5× median, and thousands of `v <= 0` hours on `SUN`, `OIL`, `WND`, `BAT`, `PS`. **These are
definitional, not defects**: a diurnal solar series has a night-dominated median of 41–56 MW,
so its noon peak is naturally 87–121× the median, and a storage series is *supposed* to go
negative. **Do not wire `screen_physical_bounds` onto a fuel column** — it was derived on
demand series and its 5.0× constant has no meaning against a diurnal or signed one.

**The one genuine flag it raises, and two it cannot:**

**(a) Four `NG: NG` unit slips in 2025 — REAL, and nothing in the repo catches them.**

| Local time (America/Chicago) | `NG: NG` MW | Prior hour | Next hour |
|---|---:|---:|---:|
| 2025-02-18 21:00 | **70,683** | 15,137 | 14,761 |
| 2025-02-21 17:00 | **69,216** | — | — |
| 2025-04-25 17:00 | **70,453** | — | — |
| 2025-11-10 16:00 | **70,593** | — | — |

SOCO's **entire** gas fleet is **36,336.0 MW** nameplate (CC 20,702.8 + CT 11,676.8 +
ST 3,839.2 + ICE 7.0 + CAES 110.0 + Other NG 0.2). These hours post **1.95×** that. They are
physically impossible and they sit in an implausibly tight 69.2–70.7 GW band, the signature
of a sentinel or a fixed digit insertion rather than a metering excursion. Magnitude if
unrepaired: **≈ +0.224 TWh on a 125.4 TWh gas year (+0.18 %)**, distributed into 4 hours —
small in the annual share, material in any hourly gas-dispatch comparison, and it is
**C1 `fuelmix`** that carries the weight once card S2 removes the price criteria.

**(b) The `Net generation` identity breaks in 2025 only — 595 hours, +0.696 TWh.**

| Year | hours with \|TI − (NetGen − Demand)\| > 1 MW | signed annual residual |
|---|---:|---:|
| 2023 | 0 | 0.0000 TWh |
| 2024 | 0 | 0.0000 TWh |
| **2025** | **595** | **+0.6963 TWh** |

Distribution of the 595: 500 exceed 100 MW, 298 exceed 500 MW, 248 exceed 1,000 MW, 178
exceed 2,000 MW, 6 exceed 5,000 MW, max **13,120 MW**. **`Net generation` is the corrupted
side, not `Demand`**: the two worst hours (2025-07-15 15:00 and 2025-07-14 15:00) carry the
**identical** `Net generation` value of **34,413 MW** on two different days, a stuck reading,
while their `Demand` values (44,914 / 44,251 MW) sit plausibly below the 46,490 MW annual
peak. `sum(NG:*)` reconciles to `Net generation` in 2025 to 0.011 TWh, so **the fuel columns
track the corrupted net-generation series** and the distortion propagates into fuel shares
for 6.8 % of 2025's hours.

**(c) A one-hour partial dropout in `Demand` — and both demand screens miss it.**

| Local time | Demand | Demand forecast | Net generation | `NG: COL` | `NG: NG` | `NG: NUC` |
|---|---:|---:|---:|---:|---:|---:|
| 2025-10-23 15:00 | 23,065 | 24,834 | 24,701 | 4,733 | 10,572 | 7,297 |
| **2025-10-23 16:00** | **12,638** | 25,132 | **15,559** | 4,743 | 10,901 | 7,299 |
| 2025-10-23 17:00 | 23,653 | 25,140 | 26,045 | 4,506 | 11,636 | 7,301 |

`Demand` and `Net generation` both notch by ≈ **−10,400 MW** in the same hour while **every
fuel column stays on trend** and `Demand forecast` is unbroken at 25,132 MW — the signature
of a partial-hour meter dropout scaled to the hour. `_screen_demand_spikes` is high-side
only; `_screen_demand_dropouts` fires only on literal `0.0`; `screen_physical_bounds`'
`v <= 0` test does not fire at 12,638 MW. **Nothing catches it.** It is the low-side twin of
the SPP 2025-06-21 dropout (`spp-data-audit.md` §3.4) at a different magnitude.

> **ROUTED to SOCO-20 / SOCO-31, named before any solve** (plan §7 G19's "named, not
> padded" discipline): three artifact hours-plus-four across `Demand`, `Net generation` and
> `NG: NG`, none reachable by an existing screen. This audit **recommends no new screen
> constant** — deriving one here would be a rule-23 violation and a lane that sets a
> threshold after seeing the outliers has fitted it. What it recommends is that SOCO-20
> record the seven hours explicitly and that SOCO-31 decide the treatment against a
> pre-registered rule.

### 3.6 Independent validation of the EIA-930 extract

EIA-930 `NG: NUC` against EIA-923 monthly generation summed over the three SOCO nuclear
plants (649 Vogtle, 6001 Farley, 6051 Hatch) — two independent EIA collection programs:

| TWh | EIA-923 | EIA-930 | Δ |
|---|---:|---:|---:|
| 2023 | 52.135 | 52.435 | **+0.58 %** |
| 2024 | 63.060 | 62.989 | **−0.11 %** |
| 2025 | 64.232 | 64.167 | **−0.10 %** |

This validates two things at once: the EIA-930 SOCO extract's fuel attribution, and the
**BA-code fleet filter itself** — the 923 side is selected by `Plant Code` from the census of
§2, so agreement to 0.1 % means the census is picking up the right plants.

---

## 4. Card S8 — Vogtle 3/4 and Barry A3: the fleet-vintage machinery DOES resolve a month, but not for these units

### 4.1 The EIA-860 facts, confirmed

| Plant | Code | Unit | Technology | Nameplate MW | Operating | Status |
|---|---:|---|---|---:|---|---|
| Vogtle | 649 | 1 | Nuclear | 1,215.0 | 1987-05 | OP |
| Vogtle | 649 | 2 | Nuclear | 1,215.0 | 1989-05 | OP |
| **Vogtle** | 649 | **3** | Nuclear | **1,114.0** | **2023-07** | OP |
| **Vogtle** | 649 | **4** | Nuclear | **1,114.0** | **2024-04** | OP |
| Barry | 3 | A3C1 | Gas CC | 464.0 | 2023-11 | OP |
| Barry | 3 | A3ST | Gas CC | 310.0 | 2023-11 | OP |

**The charter is confirmed exactly**: Vogtle 3 = 1,114 MW operating 2023-07, Vogtle 4 =
1,114 MW operating 2024-04, Barry A3 = **774.0 MW** (464.0 + 310.0) operating 2023-11.

### 4.2 What the machinery actually does — measured live, not read

`src/market_sim/data/cod_ramp.py` implements a **month-precise** COD ramp
(`monthly_online_mask`), applied in `data/fleet/arrays.py` under `config.cod_ramp_enabled`
(default on for backcasts). So the answer to the card's literal question is: **yes, the
machinery resolves a within-year commercial-operation month.** But two further facts
determine whether it *fires*:

1. **`_load_cod_map` reduces to one record PER PLANT, as a CAPACITY-WEIGHTED MEAN of its
   units' continuous CODs** — `cont = oy + (om−1)/12`, weighted by nameplate, then floored
   back to `(year, month)` (`_reduce_cod_groups`). *(Note for `/sync-docs`: the module
   docstring says "the plant's earliest unit defines its online date". The code computes a
   capacity-weighted mean. Code is the source of truth; the docstring is stale.)*
2. **`effective_cod` ALWAYS prefers that plant record over the generator's own
   `Operating Month`/`Operating Year` for the ONLINE date.** The per-unit preference exists
   **only for the retirement date** — added for the Homer City seam. Online date: plant map
   wins whenever `plant_code > 0` and the plant is in the map.

**Measured, by calling the live code** (§8 command 5):

```
load_cod_map()[649]  -> (2005, 5, None, None)     # Vogtle
load_cod_map()[3]    -> (1991, 3, None, None)     # Barry
load_cod_map()[56]   -> (2023, 9, None, None)     # Lowman Energy Center

effective_cod(649, 2023, 7, None, None, m) -> (2005, 5, None, None)   # Vogtle 3's own 2023-07 DISCARDED
effective_cod(649, 2024, 4, None, None, m) -> (2005, 5, None, None)   # Vogtle 4's own 2024-04 DISCARDED
effective_cod(3,   2023,11, None, None, m) -> (1991, 3, None, None)   # Barry A3's own 2023-11 DISCARDED

monthly_online_mask((2005,5,None,None), 2023) -> 111111111111
monthly_online_mask((1991,3,None,None), 2023) -> 111111111111
monthly_online_mask((2023,9,None,None), 2023) -> 000000001111   # the ramp DOES work...
```

**So the ramp is not broken — it is bypassed for exactly the units that need it.** Lowman
Energy Center (plant 56) is a **greenfield** plant whose only units are the 2023-09 CC, so
its plant mean *is* 2023-09 and it ramps correctly. Vogtle and Barry are **brownfield
additions at multi-vintage plants**, where the capacity-weighted mean lands decades before
the new unit and the mask returns all-True.

### 4.3 The energy error, quantified against measured CFs

The capacity factors are **measured from EIA-923 monthly generation**, not assumed:

* **Vogtle 3, Jul–Dec 2023**: 4,356,291 MWh ÷ (1,114 MW × 4,416 h) = **88.6 %**
* **Vogtle 4, Apr–Dec 2024**: 6,549,893 MWh ÷ (1,114 MW × 6,600 h) = **89.1 %**

| Year | Phantom unit | Phantom window | Phantom TWh | vs measured `NG: NUC` |
|---|---|---|---:|---|
| 2023 | Vogtle 3 | Jan–Jun (4,344 h) | 4.285 | |
| 2023 | Vogtle 4 | Jan–Dec (8,760 h) | 8.693 | |
| **2023** | **both** | | **12.979** | **+24.8 % on 52.435 TWh** |
| **2024** | Vogtle 4 | Jan–Mar (2,184 h) | **2.167** | **+3.4 % on 62.989 TWh** |
| 2025 | — | — | 0.000 | both units online all year |

**The decisive consequence: a 2023 SOCO backcast would show ≈ 65.41 TWh of nuclear, ABOVE
the measured 2025 value of 64.17 TWh.** The measured commissioning step 52.4 → 63.0 →
64.2 TWh would be **inverted** by the model, and ~13 TWh of must-run nuclear would displace
gas one-for-one in the 2023 dispatch — roughly **10 % of the measured 129.6 TWh gas year**.
With card S2 removing C3a/C3b/C3c, **C1 `fuelmix` becomes one of only two load-bearing
criteria left**, and this error hits it directly, in the two largest classes.

**Barry A3 — a capacity and merit-order error, stated as such.** 774.0 MW of gas CC becomes
available **10 months early** (Jan–Oct 2023), 2.1 % of the gas fleet. A CC is dispatchable,
so its phantom *energy* is endogenous to the LP rather than a fixed product; the honest
bound uses two measured endpoints:

* at the **measured SOCO 2023 gas-fleet CF of 40.7 %** (129.592 TWh ÷ 36,336 MW ÷ 8,760 h):
  **≈ 2.30 TWh**;
* at **Barry's own measured 2024 CC capacity factor of 81.3 %** (EIA-923: 13.173 TWh of
  CA+CT netgen ÷ 1,844.8 MW ÷ 8,784 h — the first full year with A3): **≈ 4.59 TWh**.

The upper end is the better estimator, because a new high-efficiency CC sits *below* the
fleet average in the merit order and therefore runs *more* than the average. **Band: 2.3 –
4.6 TWh of phantom 2023 gas-CC energy.** Note this is **not independently checkable today**
— Barry is in Alabama and `AL_2023.parquet` does not exist (§2.3). The two findings are the
same finding from different directions.

### 4.4 The blast radius, and why this is a desk decision

Every plant in the current EIA-860 vintage with a 2023–2025 unit whose plant-collapsed COD
year is earlier, by registered footprint:

| Footprint | Plants | Units | **Phantom-early MW** |
|---|---:|---:|---:|
| **SOCO** | 6 | 9 | **3,040.3** |
| SPP | 9 | 19 | 1,127.4 |
| ERCOT | 13 | 21 | 1,091.4 |
| CAISO | 19 | 24 | 1,037.2 |
| MISO | 15 | 28 | 927.4 |
| PJM | 9 | 14 | 177.2 |
| NYISO | 11 | 19 | 72.9 |
| NEISO | 13 | 13 | 50.0 |

**SOCO carries 2.7× the next-worst footprint's exposure, and Vogtle 3 and 4 are the two
largest trapped units in the entire national fleet.** SOCO's 3,040.3 MW is Vogtle (2,228.0)
+ Barry A3 (774.0) + four sub-30 MW rows. The defect is **general**; it is **material** only
where a GW-scale brownfield addition lands inside a backcast window, and SOCO is the only
such footprint.

**Options for the desk, with blast radius stated — this lane recommends, it does not
choose:**

| Option | What it is | Blast radius |
|---|---|---|
| **A — prefer the unit's own online date, as `effective_cod` already does for retirements** | One clause in `cod_ramp.effective_cod`, symmetric with the Homer City seam it already contains | **Cross-ISO.** Changes results (not cache keys) for all seven registered keepers — 1.1 GW SPP, 1.1 GW ERCOT, 1.0 GW CAISO, 0.9 GW MISO. Gate **G8** territory and a rule-1 `[R-STRUCT]` question: this is a *correctness* repair, so rule 14 `[R-ACCURATE]` says keep the accurate input and root-cause the fit, but the decision is the owner's, not a lane's. |
| **B — SOCO-scoped handling** | Some SOCO-only route to the per-unit date | Keeps the seven byte-identical, but a per-ISO branch on a physical commissioning date is hard to justify structurally: a COD is a fact about a turbine, not about a market. |
| **C — document the misalignment, solve anyway** | Record +12.98 TWh / +24.8 % on 2023 nuclear as a known bias on the determination basis | Cheapest, and honest, but it biases **C1 in the two largest classes** in a run whose price criteria are already gone. |

**This lane's recommendation: A, raised as an owner card at desk sitting #2, with the
cross-ISO A/B run as its own lane rather than inside SOCO-20.** Rationale: the unit's own
`Operating Month` is the *accurate measured input* and the plant mean is the *estimate*, so
rule 14 `[R-ACCURATE]` points one way — "if swapping a hand estimate for real data makes the
backcast worse, that is a signal something else is miscalibrated." Whatever the desk rules,
**option C is the floor**: the bias must be on the determination basis of SOCO's first
keeper either way.

---

## 5. The registry-values table — one row per value SOCO-20 needs

**Rules of this table (rules 5 `[R-NO-MAGIC]`, 13 `[R-MEASURED]`, 23 `[R-FROZEN-DERIVE]`):**
every cell is a **cited value** (URL + page/table) or **`pending <lane>`**. Nothing here is
derived by this lane, and nothing is a guess. A `pending` row is a *complete* row —
it names the target, the registry key, the source to fetch and who fetches it.

| # | Registry key / target | Value | Source (URL + page/table) | Status |
|---|---|---|---|---|
| 1 | `PLANNING_RESERVE_MARGIN_BY_ISO["SOCO"]` — **BY SEASON** | Georgia Power 2025 IRP target reserve margin: **26 % winter**, **20 % summer** (raised from **16.25 %** summer). Measured evidence that a *seasonal* value is required: SOCO is winter-peaking in 2024 (47,368 MW, Jan 17) and 2025 (46,490 MW, Jan 22) and summer-peaking in 2023 (45,558 MW, Aug 25); in 2025 summer sits 0.25 % below winter (§3.1) | Georgia PSC Docket **56002**, Georgia Power 2025 IRP. Reached this lane via intervenor testimony (Direct Testimony of M. Roumpani for Georgia Conservation Voters, 2025-05-02, [psc.ga.gov doc 222501/103611](https://services.psc.ga.gov/api/v1/External/Public/Get/Document/DownloadFile/222501/103611), PDF pp. 3, 12) and Georgia Power's own [2025 IRP docket overview](https://www.georgiapower.com/about/company/filings/irp.html). **The primary IRP volume with a page cite is SOCO-12's.** | **partial — cite the PRIMARY, SOCO-12** |
| 1b | Same, Alabama Power | — | Alabama does **not** run a public IRP docket comparable to Georgia's; Alabama Power's resource plan reaches the APSC largely under confidential treatment. Candidate substitutes: APSC Rate CNP Certificate filings; the **SERC Reliability Corporation** and **NERC Long-Term Reliability Assessment** anticipated-reserve-margin series for SERC-SE | **pending SOCO-12** |
| 1c | Same, Mississippi Power | — | Mississippi PSC docket filings; MP is 6 % of the footprint by capacity and may reasonably inherit 1/1b | **pending SOCO-12** |
| 2 | **VOLL** (the LP slack penalty) — card **S5** | **Do NOT use $2,000/MWh.** See the note below this table. Recommended construction: the **DOE/LBNL Interruption Cost Estimate (ICE) Calculator**, run for the SERC/Southeast region on the AL/GA/MS customer-class mix | [LBNL ICE Calculator](https://icecalculator.com/) / [LBNL EMP, ICE Calculator 2.0](https://emp.lbl.gov/news/updated-ice-calculator-now-available) (24 US utility service territories). Methodological precedent for an economic VOLL: Brattle, *Value of Lost Load Study for the ERCOT Region*, PUCT Project **55837**, Sept 2024 — **an ERCOT number that must NOT be transferred to SOCO** (rule 25 `[R-ISO-SCOPE]`); it is cited as *method*, not value | **pending SOCO-12** |
| 3 | `_SOCO_STATE_ZONES` (FIPS → zone) | 3-zone candidate: `1 (AL) → SOCO-Alabama`, `13 (GA) → SOCO-Georgia`, `28 (MS) → SOCO-Mississippi`, `12 (FL) → SOCO-Alabama`. **No key for FIPS 25 (MA)** — §2.6(a). 1-zone candidate: no map needed | measured, §2.3 / §6.4 | **got (candidate)** — card S3 decides |
| 4 | Zone load shares (the fallback if FERC-714 cannot be reconciled) | **Fleet-MW shares, measured**: GA 58.4 % / AL 34.7 % / MS 6.5 % / FL 0.4 %. **This is a fallback of last resort, not a load share** — a zone's generation share is not its demand share in a net-exporting, jointly-owned footprint | measured, §2.3 | **got (fallback only)**; the real spine is **SOCO-11** |
| 5 | Zone hourly load (the spine) | — | FERC Form 714 Part 3 Schedule 2, via PUDL `out_ferc714__hourly_planning_area_demand.parquet`. **Eight** footprint respondents, §6.2 | **pending SOCO-11** |
| 6 | Gas basis / delivered gas | Per-plant **EIA-923 monthly delivered fuel cost** is present and is the backcast source (471 / 441 / 471 rows over 30 / 31 / 31 SOCO plants, §1 item 8). State monthly series to fetch: **`N3045AL3m`, `N3045GA3m`, `N3045MS3m`** (EIA natural gas delivered to electric power, $/Mcf), matching the committed SPP naming `eia_delivered_gas_<ST>_monthly_2023-2025.csv` | EIA Natural Gas Navigator series `N3045{AL,GA,MS}3m`; convention `data/raw/gas-prices/SOURCES_eia_delivered_gas_electric_power_by_state.md` | **pending SOCO-12** (923 half **got**) |
| 6b | Pipeline / hub reference for the basis narrative | Candidates named in the charter: **Transco Zone 4** and **Southern Natural Gas (SONAT)**. Which pipeline actually serves which plant is **already on disk, per plant**: `eia860_plant.parquet` carries `Natural Gas Pipeline Name 1/2/3` for every SOCO plant — read it rather than assuming | `data/raw/eia-860/eia860_plant.parquet`, columns `Natural Gas Pipeline Name 1..3` | **got (route);** the basis *value* is **pending SOCO-12** |
| 7 | Coal price basis | Per-plant **EIA-923 monthly delivered coal cost** (present, item 8). SOCO coal is 6 plants / 12,234.7 MW; basin mix (ILB / NAPP / CAPP / PRB / imported) is readable from EIA-923's `fuel_group` + EIA-860 `Energy Source 1` | `data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet` | **got** |
| 8 | Nuclear monthly CF (`nuclear-license-status/soco.csv` + monthly budgets) | **Measured from EIA-923, per unit.** Vogtle 3 first-operation CF **88.6 %** (Jul–Dec 2023); Vogtle 4 **89.1 %** (Apr–Dec 2024). Plant annual energy 2023/24/25 (TWh): Vogtle 23.04 / 33.87 / 37.14, Farley 14.76 / 15.08 / 13.01, Hatch 14.34 / 14.10 / 14.08. Monthly refuelling-outage signature is visible per unit (e.g. Hatch each Feb–Mar, Farley Apr–Jun 2025) | `data/raw/_processed-legacy/eia923_monthly_generation.parquet`, plant codes 649 / 6001 / 6051, §8 command 7 | **got** |
| 8b | NRC licence expiry dates (the registry's other column) | — | NRC "Operating Reactors" licence-renewal pages for Farley 1–2, Hatch 1–2, Vogtle 1–4. Format precedent: `data/raw/nuclear-license-status/spp.csv` | **pending SOCO-12** |
| 9 | `QUEUE_CAP_PER_TECH_GW["SOCO"]` | **Measured demonstrated peak annual COD by technology, SOCO, from EIA-860** (the convention this table documents — "modestly above demonstrated peak annual COD"): solar 2023 **1.11 GW** / 2024 **0.72 GW** / 2025 **0.34 GW**; gas CC 2023 **1.51 GW**; batteries 2024 **0.065 GW**; **wind 0.000 GW in every year — there is no wind in the footprint**. The *cap* is a 0.5 GW-step choice above the demonstrated peak and is **SOCO-20's to set and cite**, not this lane's (rule 23) | measured, §8 command 3 | **got (the basis);** the cap value is SOCO-20's |
| 10 | State RPS floors, AL / GA / MS | **ALL THREE ARE ZERO — there is no RPS in any state of the footprint.** DSIRE: *"Alabama does not have a renewable energy portfolio standard or a voluntary renewable energy target"*; the same for Georgia; Mississippi has no RPS and therefore no SREC market. The registry entry is an explicit **0.0 / absent with this citation**, never a blank | DSIRE state pages: [AL](https://programs.dsireusa.org/system/program/al), [GA](https://programs.dsireusa.org/system/program/ga) | **got** |
| 11 | `MARKET_DESIGN` / `_CURVE_ISOS` / `_CAPACITY_ISOS` | **SOCO absent from all three** → `DEFAULT_MARKET_DESIGN`, `capacity_market=False` (the ERCOT/SPP branch). The absence is a *documented decision*: Southern runs no capacity auction of any kind | plan card S6; `config/capacity_market.py` | **got (recommendation)** — card S6 |
| 12 | LTLF edition + vintage (`scripts/lib/load_forecast/soco.py`) — **W2 PRECONDITION, gate G12** | One citable anchor in hand: Georgia Power **current winter peak 16,284 MW**; risk-adjusted forecast **+8,205 MW** of load growth winter 2024/25 → winter 2030/31 (+2,200 MW vs the 2023 IRP Update); **up to +9,400 MW** through winter 2034/35. **This is Georgia Power's retail peak, NOT the SOCO BA's** — see §6.2 | Georgia PSC Docket 56002, 2025 IRP, *Attachment 2.0-1: Budget 2025 Forecast Annual Summary*, quoted in the Roumpani testimony at PDF p. 14 (its footnotes 5–6) | **partial — needs the primary + the AL/MS legs, SOCO-12** |
| 13 | eGRID vintage | **No SOCO entry is needed.** `zone_assignment._EGRID_VINTAGE = 2023` is a module-level scalar, not a per-ISO dict — the same finding SPP-10 recorded (`spp-data-audit.md` §4 row 17) | `src/market_sim/data/zone_assignment.py:543` | **got** |
| 14 | `TRANSMISSION_BASE_STATIC_VINTAGE["SOCO"]` | The dict is `{ERCOT 2024, CAISO 2023, MISO 2025, PJM 2024, NYISO 2025, NEISO 2023, SPP 2026}` — a per-ISO **int**, the vintage of the static base topology. SOCO's value is the publication year of whatever base-topology document SOCO-20 actually uses; **candidate 2026** on the SPP precedent, but it must follow the document, not the precedent | `src/market_sim/data/transmission_expansion.py:81` | **pending — SOCO-20 sets it with its source document** |
| 15 | `TAIL_THRESHOLD["SOCO"]` (3 files) + `actual_tail.json` | — | **Gate G6: deliberately SKIPPED unless card S2 yields a price series.** With no price there is no tail. The skip is documented, not forgotten | **blocked on card S2 / SOCO-13** |
| 16 | `ISO_EV_KEY["SOCO"]` | `"O"` (`S` is SPP's) | plan §3 defaults | **got** |
| 17 | Inter-zone TTCs (if card S3 lands 3 zones) | — | **No published internal Southern transfer limit exists.** Registers **Tier-3, non-binding**, exactly the SPP N↔S precedent; derivation becomes pre-declared lever **SOCO-54** | **pending — by construction** |
| 18 | Interchange / seam counterparties | SOCO is a net exporter of **10.156 / 10.831 / 13.021 TWh** (2023/24/25), measured. Neighbour names for `data/neighbor_price._HR_GAS_ELASTIC` (keys are GLOBAL — gate G10): `TVA`, `DUKE`, `FLORIDA`, `SANTEE`; **`MISO` already exists and must not be re-keyed** | measured §3.1; plan card S4 | **partial;** per-counterparty duration curves are **SOCO-11** |

> **CARD S5 — THE $2,000 NOTE, STATED EXPLICITLY AS THE CHARTER ASKS.**
> Every market ISO in this repo carries VOLL = $2,000/MWh, and that number is **FERC Order
> 831's hard offer cap** — the ceiling above which an incremental energy **offer** may not be
> accepted without cost verification. **SOCO takes no offers.** It is vertically integrated:
> dispatch is cost-based against an IRP, there is no day-ahead market, no LMP, and no
> centralized capacity market, so there is nothing for an offer cap to cap. Importing $2,000
> into `SOCO` would be importing a number whose *referent does not exist in this market* —
> and in the LP it is not a cap at all but the **slack penalty**, i.e. the price at which the
> model prefers to shed load. The correct construction is an **economic** value of lost
> load for this footprint's customer mix (row 2). If Phase 0 produces no citable Southeast
> value, the charter's fallback of $2,000 is acceptable **only with the misalignment written
> on the field** — that it is an offer cap borrowed into a market that takes no offers,
> carried as a placeholder, and that it is a free parameter in the DOF ledger (rule 21
> `[R-DOF]`).

---

## 6. Card S3 — zone recommendation (RECOMMEND ONLY)

### 6.1 The recommendation, in one line

**Register 3 zones — SOCO-Alabama / SOCO-Georgia / SOCO-Mississippi — split on the fleet's
state FIPS, with Tier-3 non-binding TTCs**, *provided* SOCO-11 delivers a reconciled hourly
load series per zone. **If that reconciliation fails, register 1 zone and say why**, rather
than splitting load on a generation share.

That is the plan's own recommendation, and this audit's job is to say what the data
supports and where it breaks. The answer is: **the fleet side supports 3 zones cleanly; the
load side is genuinely uncertain and is not this lane's to settle; and the validation side
is weaker than any prior addition, in a way §6.5 states plainly.**

### 6.2 What the data supports — and the reconciliation trap

**The fleet splits cleanly on state.** 336 plants, 4 in-footprint states, and after the §2.6
adjudication **every generator carries an unambiguous FIPS state**: GA 41,284.4 MW /
AL 24,494.0 / MS 4,577.7 / FL 309.6. No plant straddles a state; no zone is a rump. Compare
PJM (four straddling states needing county-level treatment) and SPP (an `EDE` sub-BA
straddle) — SOCO's fleet-side split is **the cleanest of any registered ISO**.

**The load side is where it gets hard, and the charter's premise needs correcting.** Plan
§2.5 says *"Alabama Power, Georgia Power and Mississippi Power each file as separate
respondents"* and directs SOCO-11 to *"reconcile the three respondents' hourly sum against
`SOCO hourly.parquet::Demand`"*. Measured off PUDL's FERC-714 respondent table, **there are
eight respondents in this footprint, not three**:

| `respondent_id_ferc714` | Name | `eia_code` |
|---:|---|---:|
| 2 | Alabama Power Company | 195 |
| 183 | Georgia Power Company | 7,140 |
| 184 | Mississippi Power Company | 12,686 |
| 185 | **Gulf Power Company** | 7,801 |
| 107 | **Oglethorpe Power Company** | 13,994 |
| 210 | **Municipal Electric Authority of Georgia** | 13,100 |
| 1 | **PowerSouth Energy Cooperative** | 189 |
| 142 | **"Southern company"** | 18,195 |

**The three OpCos will not sum to the BA, and a lane expecting a ~1.00 ratio will burn a
day proving it.** The reasons are structural, not data quality:

* **Oglethorpe (6,472.2 MW) and MEAG (594.1 MW)** own generation inside Georgia and serve
  Georgia EMC and municipal load *inside the same balancing authority*. Their load is in
  `SOCO hourly.parquet::Demand`; it is **not** in Georgia Power's planning area.
* The scale of that wedge is measurable from the load side too: Georgia Power's own current
  winter peak is **16,284 MW** (§5 row 12) against a SOCO BA winter peak of **47,368 MW**,
  while Georgia holds **58.4 %** of the fleet's MW. Georgia Power's retail peak is
  **not** Georgia's share of BA demand and must never be used as one.
* **PowerSouth (2,070.9 MW)** is an Alabama/Florida G&T with the same relationship on the
  Alabama side.
* **Respondent 142, "Southern company" (`eia_code` 18195)**, is the one to check **first**:
  if it files whole-BA planning-area demand, SOCO-11 has a *direct* BA-level cross-check
  against EIA-930 and the OpCo shares can be reconciled against it rather than against a sum
  that structurally cannot close.

> **ROUTED TO SOCO-11 as a scope correction, before it starts:** enumerate all eight
> respondents, establish what respondent 142 actually is, and reconcile **against the right
> denominator**. Report the residual as a *number with an attribution*, not as an error.
> Expect a large, explainable Georgia-side residual; that residual **is** the EMC/municipal
> load, and it is a zone-share input, not a defect.

### 6.3 What SOCO-11 must supply for 3 zones to be admissible

1. **Hourly demand for the eight respondents, 2023–2025**, on the §3.4 timezone convention.
2. **A reconciliation table** against `SOCO hourly.parquet::Demand` with the residual named
   and attributed — including whether the former Gulf Power (FPL Northwest Florida) load is
   inside or outside the metered BA series (§2.6(b) caveat 1).
3. **A per-zone hourly series** built by assigning each respondent to a zone, with the
   assignment rule written down *before* the numbers are seen.
4. **A stated failure mode**: what residual magnitude means "the zonal split is not
   supported by the data", declared in advance. Without it, a lane can rationalise any
   residual, and card S3 gets decided by a number rather than by structure.

### 6.4 FIPS mechanics of each option

**3 zones.** `zone_assignment._SOCO_STATE_ZONES: dict[int, str]`, on the
`_SPP_STATE_ZONES` / `_MISO_STATE_ZONES` pattern:

```
 1 (AL) -> "SOCO-Alabama"
13 (GA) -> "SOCO-Georgia"
28 (MS) -> "SOCO-Mississippi"
12 (FL) -> "SOCO-Alabama"      # the SERC panhandle, 309.6 MW, interconnects west (§2.6b)
                               # NO key for 25 (MA) — §2.6(a); the splitter should FAIL LOUD,
                               # not fall back to _LARGEST_ZONE, on a SOCO-coded out-of-
                               # footprint plant
```

`_LARGEST_ZONE["SOCO"] = "SOCO-Georgia"` (58.4 % of fleet MW). **No lat/lon seam fallback is
needed** — unlike SPP's `_SPP_SEAM_LAT`, SOCO's zones *are* whole states, so FIPS alone is
total over the admitted footprint. Requires: 3 zone entries in `_soco_config()`, 2 inter-zone
links (AL↔GA, AL↔MS — Mississippi Power connects to the system through Alabama, not
Georgia), per-zone load shares, per-zone solar shapes.

**Name the zones for their geography, not their owner** — `SOCO-Alabama`, not
`Alabama-Power`. §2.5 and §6.2 show why: Georgia Power owns 241.6 MW *in Alabama*,
Oglethorpe and MEAG own 7.1 GW in Georgia that is not Georgia Power's, and a zone named for
an operating company invites exactly the OpCo-vs-state confusion this audit had to unpick.
The zone is a **geographic/topological** object; the OpCo is a **commercial** one.

**1 zone.** No `_SOCO_STATE_ZONES` at all, no inter-zone links, no per-zone shares or solar
shapes; every §2.3 row collapses. Strictly less work at every wave and it removes SOCO-11's
FERC-714 dependency from the W2 critical path entirely.

### 6.5 THE PART THAT MATTERS — what a zone split can and cannot be validated against

**This is where SOCO differs from every prior addition in this repo, and the difference is
not one of degree.**

In MISO, SPP, PJM, NYISO and NEISO, a zonal topology is validated on the **price spread
between zones**. That is what makes a TTC falsifiable: if the model's zonal price spread is
flat when the market's is not, the seam limit is wrong. Card S2 establishes that **SOCO has
no price at all** — no LMP, no day-ahead clearing price, no hourly index, and SEEM
deliberately publishes none. So:

**A SOCO zone split CAN be validated against:**

* **Per-zone load** — if and only if SOCO-11's FERC-714 reconciliation closes (§6.3). This
  is the primary and possibly only quantitative check.
* **Per-zone generation by fuel**, from EIA-923 monthly generation aggregated by plant state
  — a monthly, not hourly, check, and it is genuine measured evidence.
* **Per-zone hourly fossil generation**, from CEMS, **once AL and GA land** (§2.3). This is
  the strongest available zonal check and it is currently **blocked**: 91.6 % of the
  CEMS-eligible fleet is unobservable.
* **Internal consistency**: the three zones' flows must sum to the measured `Total
  interchange`, and each zone's dispatch must respect its own fleet.

**A SOCO zone split CANNOT be validated against:**

* **Any zonal price or price spread.** None exists, and none can be manufactured. Even if
  SOCO-13's EQR index succeeds, it is a **footprint-hourly** index — a single series for the
  whole BA — not a locational one.
* **Congestion.** No shadow prices, no binding-constraint list, no congestion rent are
  published for this footprint. SPP-10 could rank SPP's lever queue on the MMU's measured
  constraint shadow prices; **no equivalent evidence exists for SOCO and none will.**
* **The TTCs themselves, in either direction.** A Tier-3 non-binding TTC is unfalsifiable
  when it never binds, and there is no price signal that would reveal it *should* have.

**The honest implication, and the one the desk should weigh:** the 3-zone split is
**structurally justified** (rule 1 `[R-STRUCT]`: a real structure enters regardless of fit —
three operating companies with their own load, their own fleet and their own state
regulator is real structure) but it is **less validated than any prior addition's**, and it
will stay that way. The zones would buy: a real load distribution, a real fleet
distribution, and the *possibility* of a congestion story later. They would **not** buy any
testable claim about inter-zone transfer, ever.

**Two things that follow, whichever way card S3 goes:**

1. **A zone split must not be sold as improving accuracy.** With non-binding TTCs and a
   copperplate interior, a 3-zone SOCO and a 1-zone SOCO produce **the same dispatch** until
   a TTC binds. If the desk chooses 3 zones, choose them for structure and say the fit is
   unchanged by construction — anything else invites a later lane to "tune" a TTC against a
   residual, which is the rule-1 failure this program can least afford.
2. **The lever that would make zones matter is SOCO-54 (the inter-OpCo TTC derive), and it
   has no public source.** It should be pre-declared in the lever queue with its evidence
   problem stated, so nobody discovers in W5 that the number cannot be sourced.

---

## 7. Notes routed to other lanes

Collected so the desk can dispatch them; **none of these is this lane's to fix** (rule 28,
collision rule 5 — I touch no file outside my three).

| # | To | Item |
|---|---|---|
| R-1 | **SOCO-20** | Add `"SOCO": "America/Chicago"` to `fetch_eia930_hourly.BA_TIMEZONE` **and** `build_eia930_hourly_from_raw.BA_TIMEZONE`. Both default to `America/New_York` today (§3.4). |
| R-2 | **SOCO-11, NOW** | Do not fetch SOCO interchange before R-1 lands, or join on `UTC time` and re-derive the local columns. The interchange fetcher imports the Eastern-defaulting dict (§3.4). |
| R-3 | **SOCO-11, scope correction** | FERC-714 has **eight** footprint respondents, not three. Reconcile against the right denominator; check respondent 142 "Southern company" first (§6.2). |
| R-4 | **SOCO-DESK → owner card** | The `cod_ramp.effective_cod` online-date precedence. SOCO is the worst-affected footprint in the registered set (3,040.3 MW); the fix is cross-ISO (§4.4). |
| R-5 | **SOCO-20 / SOCO-31** | Seven unscreened EIA-930 artifact hours: 4 × `NG: NG` ≈ 70 GW, 595 h of broken net-generation identity in 2025, 1 h partial demand dropout. No existing screen reaches any of them (§3.5). |
| R-6 | **SOCO-31 / SOCO-40** | Pumped storage is **unobservable in EIA-930 for 2023 and most of 2024** (§3.3). The C1 benchmark must say so rather than scoring a PS row that does not exist. |
| R-7 | **SOCO-20** | `campd.ISO_STATES["SOCO"] = ("AL", "GA", "MS", "FL")`; the zone splitter must **fail loud**, not fall back, on a SOCO-coded plant outside the footprint (§2.6a). |
| R-8 | **SOCO-20** | Card S7: map the CAES unit on its **25 MW summer/winter rating**, not its 110 MW nameplate — a 77 % derate the source itself states (§2.2). |
| R-9 | **SOCO-20** | Loaders that assume `summer ≤ nameplate` will trip on the 9 pumped-storage rows, where summer (1,569.4) exceeds nameplate (1,306.6) by EIA convention (§2.2). |
| R-10 | **SOCO-20** | Data-profile token `soco` is **collision-free** (only `SOCO_fueltype.parquet` / `SOCO_region.parquet` match). But a `soco` profile does **not** pull `eia-930-hourly/SOCO hourly.parquet`, which lives in a `shared` directory — verify the profile actually hydrates what a SOCO solve reads (gates G3/G18). |
| R-11 | `/sync-docs` | `cod_ramp.py`'s module docstring says "the plant's earliest unit defines its online date"; `_reduce_cod_groups` computes a **capacity-weighted mean** (§4.2). |
| R-12 | **SOCO-20 / SOCO-30** | There is **no wind** in the SOCO fleet (0 generators, 0.000 TWh in all three years). Any wind-keyed registry entry describes an empty set (§2.2). |

---

## 8. Reproduction

Container prep: `python3 -m pip install pandas pyarrow pydantic` (none are preinstalled).
All commands from the repo root at `origin/main` `2c2fc065`, `DATA PROFILE: shared`.

```bash
# 1  Fleet census: plants / gens / MW by state, technology, owner (§2.2, §2.3, §2.5)
python3 - <<'PY'
import pandas as pd
P = pd.read_parquet('data/raw/eia-860/eia860_plant.parquet')
G = pd.read_parquet('data/raw/eia-860/eia860_generator_operable.parquet')
soco = P[P['Balancing Authority Code'] == 'SOCO']
M = soco[['Plant Code','Plant Name','State','County','Latitude','Longitude',
          'NERC Region','Utility Name','Sector Name']].merge(
    G.drop(columns=['State','County','Plant Name','Utility Name','Sector Name']),
    on='Plant Code', how='inner')
for c in ('Nameplate Capacity (MW)','Summer Capacity (MW)','Winter Capacity (MW)'):
    M[c] = pd.to_numeric(M[c], errors='coerce')          # <-- these arrive as STRINGS
print(M['Plant Code'].nunique(), len(M), M['Nameplate Capacity (MW)'].sum())
print(M.groupby('State')[['Nameplate Capacity (MW)']].sum())
print(M.groupby('Technology')[['Nameplate Capacity (MW)']].sum().sort_values(
    'Nameplate Capacity (MW)', ascending=False))
print(M[M.State.isin(['MA','FL'])][['Plant Code','Plant Name','State','County',
    'Latitude','Longitude','NERC Region','Utility Name','Technology',
    'Nameplate Capacity (MW)']])                          # the §2.6 adjudications
PY

# 2  CEMS state diff (§2.3) — AL / GA / FL return nothing
ls data/raw/campd-unit-level/ | grep -E '^(AL|GA|MS|FL)_'

# 3  Queue-cap basis: demonstrated peak annual COD by technology (§5 row 9)
#    (same M as command 1)  M[M['Operating Year'].between(2023,2025)]
#       .groupby(['Operating Year','Technology'])['Nameplate Capacity (MW)'].sum()

# 4  TIMEZONE — gate G19, the decisive test (§3.4)
python3 - <<'PY'
import pandas as pd
d = pd.read_parquet('data/raw/eia-930-hourly/SOCO hourly.parquet')
utc = d['UTC time'].dt.tz_localize('UTC')
for tz in ('America/Chicago','America/New_York'):
    wall = utc.dt.tz_convert(tz).dt.tz_localize(None)
    print(tz, 'mismatches:', int((wall != d['Local time']).sum()), '/', len(d))
print('fixed UTC-6:', int(((d['UTC time']-pd.Timedelta(hours=6)) != d['Local time']).sum()))
print('fixed UTC-5:', int(((d['UTC time']-pd.Timedelta(hours=5)) != d['Local time']).sum()))
off = (d['Local time'] - d['UTC time']).dt.total_seconds()/3600
print(off.value_counts().sort_index())                    # -> only -6 and -5
print('UTC dups', d['UTC time'].duplicated().sum(),
      'local dups', d['Local time'].duplicated().sum())    # -> 0 and 3 (fall-back hours)
print(d['Local date'].dt.year.value_counts().sort_index()) # -> 2022:7 2023:8760 2024:8784 2025:8753
PY

# 5  CARD S8 — the COD map, live (§4.2).  Needs pydantic.
PYTHONPATH=src python3 - <<'PY'
from market_sim.data.cod_ramp import load_cod_map, monthly_online_mask, effective_cod
m = load_cod_map()
print('Vogtle  649 ->', m[649])      # (2005, 5, None, None)
print('Barry     3 ->', m[3])        # (1991, 3, None, None)
print('Lowman   56 ->', m[56])       # (2023, 9, None, None)  <- a greenfield plant DOES ramp
for pc, oy, om, lbl in ((649,2023,7,'Vogtle 3'), (649,2024,4,'Vogtle 4'), (3,2023,11,'Barry A3')):
    ec = effective_cod(pc, oy, om, None, None, m)
    print(lbl, 'own COD', f'{oy}-{om:02d}', '-> effective', ec,
          '2023 mask', ''.join(str(int(x)) for x in monthly_online_mask(*ec, 2023)))
PY

# 6  Blast radius of the COD trap across all eight footprints (§4.4)
#    join eia860_plant[BA code] + generator_operable, map Plant Code -> load_cod_map()[.][0],
#    keep rows with Operating Year in 2023-2025 AND map_year < Operating Year, group by BA.

# 7  Nuclear CFs and the EIA-930 / EIA-923 cross-check (§3.6, §5 row 8)
python3 - <<'PY'
import pandas as pd
d = pd.read_parquet('data/raw/_processed-legacy/eia923_monthly_generation.parquet')
s = d[d.plant_id.isin([649,6001,6051]) & d.year.between(2023,2025)]
print(s.groupby('year')['netgen_annual_mwh'].sum()/1e6)    # 52.135 / 63.060 / 64.232 TWh
print(4_356_291/(1114*4416), 6_549_893/(1114*6600))        # Vogtle 3 .886, Vogtle 4 .891
PY

# 8  FERC-714 respondents (§6.2) — 17 KB, no EIA key needed
curl -sS -o /tmp/r714.parquet \
  https://s3.us-west-2.amazonaws.com/pudl.catalyst.coop/nightly/core_ferc714__respondent_id.parquet
python3 -c "import pandas as pd; d=pd.read_parquet('/tmp/r714.parquet'); \
print(d[d.respondent_name_ferc714.str.contains('Alabama Power|Georgia Power|Mississippi Power|Southern compan|Oglethorpe|Municipal Electric Authority|PowerSouth|Gulf Power',case=False,na=False)])"
```

---

## 9. Manual manifest — copy-paste

Everything this lane could **not** source, with the exact URL or command. Each row is a
fetch first; the manual fallback fires only on a documented block (the SPP charter's owner
ruling O-3 carries over). **Nothing below was fetched by SOCO-10 — these are work orders.**

```text
=============================================================================
SOCO MANUAL MANIFEST  —  lane SOCO-10, 2026-09-13
=============================================================================

[1] CAMPD HOURLY CEMS — AL, GA (+FL)   *** THE CRITICAL PATH — 91.6 % of fossil MW ***
    Lane: SOCO-11        Target: data/raw/campd-unit-level/<ST>_<yr>.parquet
    Fetch:  python scripts/data/fetch_campd_unit_level.py --year 2023 --states AL GA
            python scripts/data/fetch_campd_unit_level.py --year 2024 --states AL GA
            python scripts/data/fetch_campd_unit_level.py --year 2025 --states AL GA
            python scripts/data/fetch_campd_unit_level.py --year 2026 --states AL GA
            (recommended, §2.3 priority 3:  --states FL  for 2023-2025)
    Direct: https://api.epa.gov/easey/bulk-files/emissions/hourly/state/emissions-hourly-<YYYY>-<st>.csv
            e.g. .../emissions-hourly-2023-al.csv   (probed 200 anonymous, ~187 MB/state-year)
    Fallback: EPA CAMPD bulk data page  https://campd.epa.gov/data/bulk-data-files
    Exit check: schema identical to data/raw/campd-unit-level/MS_2024.parquet

[2] FERC FORM 714 HOURLY PLANNING-AREA DEMAND  — EIGHT respondents, not three (§6.2)
    Lane: SOCO-11        Target: data/raw/zone-specific-demand/SOCO/
    Fetch:  https://s3.us-west-2.amazonaws.com/pudl.catalyst.coop/nightly/out_ferc714__hourly_planning_area_demand.parquet
            (probed 206 rangeable;  respondent index, 17 KB:
             https://s3.us-west-2.amazonaws.com/pudl.catalyst.coop/nightly/core_ferc714__respondent_id.parquet )
    Respondent ids: Alabama Power 2 | Georgia Power 183 | Mississippi Power 184 |
                    Gulf Power 185 | Oglethorpe 107 | MEAG 210 | PowerSouth 1 |
                    "Southern company" 142  (eia_code 18195 — CHECK THIS ONE FIRST)
    Fallback: FERC Form 714 bulk CSV  https://www.ferc.gov/industries-data/electric/general-information/electric-industry-forms/form-no-714-annual-electric/data
            (FERC's own host 403s from this egress — plan §2.4)
    Exit check: reconcile against SOCO hourly.parquet::Demand and REPORT THE RESIDUAL
                with its attribution.  Do NOT expect the three OpCos to sum to the BA.
    TIMEZONE: America/Chicago, hour-ending; join on UTC.

[3] EIA-930 SOCO BA-TO-BA INTERCHANGE
    Lane: SOCO-11        Target: data/raw/eia-930-interchange/SOCO interchange hourly.parquet
    Fetch:  python scripts/data/fetch_eia930_interchange.py --ba SOCO     (needs EIA_API_KEY)
    *** BLOCKER: that script imports fetch_eia930_hourly.BA_TIMEZONE, which has NO SOCO key
        and defaults to America/New_York.  It will write EASTERN local columns.  Either wait
        for SOCO-20's fix (routed item R-1) or join on 'UTC time' and re-derive the local
        columns as America/Chicago.  See soco-data-audit.md §3.4.
    Fallback (key-free): EIA Grid Monitor six-month interchange CSV
            https://www.eia.gov/electricity/gridmonitor/  (Download Data)

[4] EIA-930 SOCO HOURLY — 7-HOUR TAIL EXTENSION  (§3.2; NOT a repair, an extension)
    Lane: SOCO-11        Target: data/raw/eia-930-hourly/SOCO hourly.parquet
    Need:  UTC 2026-01-01 00:00 .. 06:00  = local hours ending 18..24 on 2025-12-31 Central.
    DO NOT PAD OR INTERPOLATE the 7 hours.  Drop the 7-row 2022-12-31 sliver.

[5] EIA DELIVERED NATURAL GAS TO ELECTRIC POWER — AL, GA, MS monthly
    Lane: SOCO-12        Target: data/raw/gas-prices/eia_delivered_gas_<ST>_monthly_2023-2025.csv
    Series: N3045AL3m, N3045GA3m, N3045MS3m
    Fetch:  https://www.eia.gov/dnav/ng/hist/n3045al3m.htm  (and ...ga3m / ...ms3m)
            or EIA API v2 (project key) — convention:
            data/raw/gas-prices/SOURCES_eia_delivered_gas_electric_power_by_state.md

[6] GEORGIA POWER 2025 IRP — PRIMARY VOLUME  (PRM by season + LTLF; gate G12)
    Lane: SOCO-12        Target: data/raw/soco-planning/ , data/raw/load-forecast/soco/soco.csv
    Need:  target reserve margin 26 % winter / 20 % summer (from 16.25 % summer) WITH a page
           cite from Georgia Power's own filing, not from intervenor testimony; and the
           Budget 2025 load forecast (Attachment 2.0-1) for the LTLF edition + vintage.
    Fetch:  https://www.georgiapower.com/about/company/filings/irp.html
            Georgia PSC Docket 56002 document search:  https://psc.ga.gov/search/facts-document/
            (already in hand, secondary: intervenor testimony, psc.ga.gov doc 222501/103611)

[7] ALABAMA POWER / MISSISSIPPI POWER RESOURCE PLANS + SERC ASSESSMENT
    Lane: SOCO-12        Target: data/raw/soco-planning/
    Note:  Alabama runs no public IRP docket comparable to Georgia's.  Substitutes:
           - Alabama PSC Rate CNP certificate filings   https://psc.alabama.gov/
           - Mississippi PSC docket filings             https://www.psc.ms.gov/
           - SERC Reliability Corporation assessments   https://www.serc1.org/
           - NERC Long-Term Reliability Assessment (SERC-SE anticipated reserve margin)
             https://www.nerc.com/pa/RAPA/ra/Pages/default.aspx

[8] VOLL — ECONOMIC VALUE FOR THE SOUTHEAST  (card S5; NOT the $2,000 offer cap)
    Lane: SOCO-12        Target: cited value for constants.py
    Fetch:  DOE/LBNL Interruption Cost Estimate (ICE) Calculator   https://icecalculator.com/
            LBNL EMP ICE Calculator 2.0 release notes    https://emp.lbl.gov/news/updated-ice-calculator-now-available
    Method precedent ONLY (an ERCOT number, never to be transferred — rule 25):
            Brattle, "Value of Lost Load Study for the ERCOT Region", PUCT Project 55837,
            Sept 2024   https://www.brattle.com/wp-content/uploads/2024/09/Value-of-Lost-Load-Study-for-the-ERCOT-Region.pdf
            (403 from this egress; try a browser UA or the PUCT Interchange for 55837)

[9] NRC LICENCE STATUS — Farley 1-2, Hatch 1-2, Vogtle 1-4
    Lane: SOCO-12        Target: data/raw/nuclear-license-status/soco.csv
    Fetch:  https://www.nrc.gov/reactors/operating/licensing/renewal/applications.html
            https://www.nrc.gov/info-finder/reactors/
    Format: copy data/raw/nuclear-license-status/spp.csv

[10] SEEM PUBLIC REPORTS  (for the record — SEEM publishes NO price; plan §2.6)
    Lane: SOCO-12        Target: data/raw/soco-planning/
    Fetch:  https://southeastenergymarket.com/   (participation + matched-volume statistics)

[11] CONFIRMED RETIREMENTS — SOCO instruments
    Lane: SOCO-12        Target: data/raw/confirmed-retirements/
    Need:  an enforceable public instrument per row (consent decree, PSC order, statute).
           Candidates: Plant Barry coal, Plant Miller, Georgia PSC 2025 IRP decertifications
           (Docket 56003 — "CERTIFICATION, DECERTIFICATION, AND AMENDED DSM PLAN").

[12] A PRICE SERIES FOR SOCO
    Lane: SOCO-13 (FABLE, STOP-gated).  NOT sourceable by this lane and NOT substitutable.
    FERC EQR viewer (probed 200):  https://eqrreportviewer.ferc.gov/
    *** Gate G17: no neighbouring hub, no "adjusted" MISO-South series, no cost-stack
        "price" may be used as SOCO's actual.  Card S2 is the only route. ***
=============================================================================
```
