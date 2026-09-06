# SCOPE NOTE — SCN-LOAD: the six-source `load-forecast` curated intake (owner ruling S4 / card D-4)

**Lane** SCN-LOAD · **Model** Opus (`claude-opus-5`) · **Date** 2026-09-06 ·
**Branch** `claude/scn-load-forecast-intake-t17qxj` (the desk's issuance record names the stem
`claude/scn-load-forecast-intake-w9tf`; the harness provisioned and binds pushes to the branch
above — the same stem mismatch SCN-WS4a and SCN-WS4b each recorded, no other difference) ·
**Base** `origin/main` at `81022b2d` · **Solves** none (intake; no PRECOMMIT owed under rule 29).

**Purpose.** Rule-29-adjacent discipline for an intake: this note is pushed **before any constant
is written**, so the gap list's closure is scored against a *prediction* rather than narrated
afterwards. The FINDING (`FINDING-scn-load-2026-09-06.md`) will carry the per-row
CLOSED / PARTIAL / BLOCKED table and will be scored against §2 and §3 below, including where the
prediction was wrong.

**Posture on the ruling.** Ledger §2 records **S4 (2026-09-06): FUND THE FULL DATATYPE**, which
overrode both the plan's and SCN-WS4a's recommendation to defer. This lane executes the full
scope and reports faithfully what it buys and what it does not; it does not re-litigate the call.

---

## 1. Obtainability — measured today, not assumed

Every URL below was fetched in-session on 2026-09-06 through the environment's egress proxy. **All
six published sources are obtainable.** The one *predicted* blocker (MISO's driver-level per-LRZ
data behind the 403-walled `www.misoenergy.org`) is unchanged and is re-confirmed as walled.

| # | source | edition read | obtainable? | grain actually published |
|---|---|---|---|---|
| 1 | **ERCOT 2025 LTLF** — `ErcotAdjustedForecast.xlsb` (48.4 MB), `ERCOT-Peak-Demand-Scenarios.xlsx`, `Summer-and-Winter-Peaks.xlsx`, `2025-ERCOT-Monthly-Peak-Demand-and-Energy-Forecast.xlsx`, `2025_LTLF_Report.docx` | 2025 LTLF (posted 2025-04-08); ERCOT's page still lists 2025 as the current LTLF vintage | **YES** — all five, `www.ercot.com/files/docs/2025/04/08/…` | The `.xlsb` is an **hourly 8760 × 20-year, per-weather-zone, per-COMPONENT** forecast: `base_economic_<zone>`, `<zone>_ev`, `<zone>_pv`, `<zone>_contracts`, `<zone>_officer_letters`, `<zone>_net`. Two published cases: **ERCOT Adjusted** (vetted central) and **TSP Provided** (un-vetted upper). |
| 2 | **CEC CED 2025-2045** (2025 IEPR, adopted 2026-01-21) — Total State baseline forms; **Form 1.1c Data Center allocations** | CED 2025-2045 / 2025-2050 extrapolation, Jan/Feb 2026 | **YES** — `efiling.energy.ca.gov/GetDocument.aspx?tn=268179-9…`, `…tn=268504…` | Annual GWh by sector 2000–2045(-2050). Form 1.1c publishes DC deliveries **by agency, by year, in TWO scenarios**: *Planning Forecast* and *Local Reliability Scenario*. |
| 3 | **PJM 2026 LTLF** (posted 2026-01-14) — report PDF + **`2026-load-report-data.xlsx`** + **`total-load-adjustments-breakdown.xlsx`** | 2026 Load Forecast Report | **YES** | The adjustments workbook **IS Table B-9b** — "Total Adjustments to Summer Peak Load (MW) for Each PJM Zone and RTO (2026–2046)", per zone and sub-area. The data workbook carries **monthly PEAK_MW + ENERGY_GWH per zone, 2026–2046**. |
| 4 | **NYISO 2026 Gold Book** | 2026 Load & Capacity Data Report | **YES** — re-fetched from the URL recorded in `data/raw/NYISO/README.md`; **sha256 verifies byte-exact** against the committed `SHA256SUMS.txt` record (`43865c1c…b908bf`). The payload is gitignored (BLOAT-B-2), not missing. | Table I-1a/I-1b Baseline energy; I-15a/I-16a Lower/Higher energy; **Table I-11b EV Annual Energy Usage** and **Table I-13a Building Electrification Annual Energy Usage**, both **by NYISO zone A–K, 2026–2056**; Table I-14 Large Load Forecast. |
| 5 | **ISO-NE 2026 CELT** — `2026_celt.xlsx` + the Final 2026 **Heat Pump** and **EV** Forecast decks | CELT 2026 (2026-05-01) | **YES** — `iso-ne.com/static-assets/documents/100035/2026_celt.xlsx`, `…/100034/heatfx2026final.pdf`, `…/100034/transfx2026final.pdf` | CELT sheet **1.7 Electrification Forecast** publishes the FULL annual-energy series 2026–2035 for heating AND transportation, by state and NE total, plus summer/winter peak MW. Sheets 1.5.1/1.5.2 give net energy and summer/winter peaks with the ISO's own CAGRs. |
| 6 | **MISO 2026 LTLF** (Workshop 2026-04-13) | 2026 LTLF Results Summary — **an edition bump** over the Sept-2025 vintage `DEMAND_GROWTH_RATES["MISO"]` still cites | **YES** by exact CDN URL (`cdn.misoenergy.org`), as SCN-WS4a §5 item 3 recorded | Slide deck: **charts, not tables**. Text-published anchors: regional energy CAGRs 2026–46 (N 2.6 % / C 2.7 % / S 1.9 %, shares 23/51/25 %); driver growth ranges 2026–46 low–high; 2046 net energy range ~885–1,404 TWh; peak 124 GW (2026) → 184 GW (2046) with per-driver ranges; "2030 MISO data center demand 20 GW". |

**The flagged blocker, re-measured.** `https://www.misoenergy.org/planning/…` → **403** again today,
`cdn.misoenergy.org` → 200. **The MISO driver-level per-LRZ forecast data is still walled**, so the
per-LRZ refinement of `DATACENTER_ZONE_SHARE["MISO"]` does **not** land in this lane. Per the
gate instruction, no worked-around substitute is used and SCN-WS4a's published-regional
decomposition stands.

---

## 2. What I predict will close, per row

Scored in the FINDING as **CLOSED** (published series now on disk and consumed),
**PARTIAL** (curated but the constant cannot fully move), **BLOCKED** (source unavailable).

| row | prediction | why |
|---|---|---|
| **G-D4-1 `DEMAND_GROWTH_RATES`** | **CLOSED for the `mid` path in all 6 ISOs; PARTIAL on low/high.** | Every ISO publishes a central annual series, so the 12 `mid` numbers become computed CAGRs over the model's own eras. Published low/high **growth** bands exist only for **NYISO** (Lower/Baseline/Higher), **MISO** (Low/Current/High) and **ERCOT** (Adjusted vs TSP-Provided — an upper case, no published low). **PJM** publishes a single forecast; **ISO-NE**'s §1.6 band is a **weather** distribution (P90/P10 around one growth path), not a demand-scenario band; **CEC**'s variants are load-modifier scenarios. Those stay a documented band and are re-stated as measured nulls. |
| **G-D4-2 `DATACENTER_ADDITIONS_MW`** | **CAISO `high := mid` CLOSED; MISO `high` extrapolation CLOSED; PJM/NYISO `low := 0` PARTIAL.** | CEC Form 1.1c publishes a second, higher DC scenario (Local Reliability) — the "high-DC table never read". MISO publishes the DC driver's 2046 range 22–44 GW directly, retiring the ratio-extrapolation. PJM's B-9b **is** the vetted subset, so a `low = 0` floor is expected to survive as an honest measured null; NYISO Table I-14 to be checked. |
| **G-D4-3 `DATACENTER_ZONE_SHARE`** | **PJM 7 residual zones CLOSED; ERCOT reproducibility CLOSED; MISO unchanged (not superseded).** | Table B-9b gives the full per-zone adjustment series, retiring the DOM-anchor-plus-`load_share`-residual. The ERCOT `.xlsb` `<zone>_contracts + <zone>_officer_letters` columns **reproduce SCN-WS4a's aggregation to within rounding (52,304 vs 52,306 MW)** — so ERCOT's shares are *verified*, not superseded, and per this lane's charter they are **not** re-written. MISO's per-LRZ refinement stays **BLOCKED** on the 403 wall. |
| **G-D4-4 `ELECTRIFICATION_LAYERS`** *(the priority row)* | **NEISO `heat_pump` CLOSED (refined 2 anchors → published 10-year series); NYISO `heat_pump` CLOSED (currently `{}`); ERCOT `ev` CLOSED; NEISO/NYISO/MISO `ev` PARTIAL.** | The `heat_pump` profile builder is ISO-general (NOAA GHCN degree-hours) and all six ISOs have weather archives, so a heat-pump layer arms wherever anchors exist. **The NYISO comment "the memo records no annual ENERGY component series" is stale** — Gold Book Tables I-11b and I-13a publish exactly that, by zone. `ev` is **fail-closed on its hourly profile, not its anchors**: only ERCOT publishes a machine-readable hourly EV series (the `.xlsb` `<zone>_ev` columns); ISO-NE, NYISO and MISO publish the shape as charts or cite third-party (NREL/DOE) profiles, so their anchors are curated and their layers stay `{}` with the blocker's identity changed from "no numbers" to "no citable 8760". |
| **G-D4-5 `DEMAND_GROWTH_TRANSITION_YEAR`** | **Unchanged — disclosed null.** | No published source exists and none will be invented. After this lane it is the family's one unsourced constant, stated as such. |

---

## 3. Two things I expect to find that are NOT on the gap list

Recorded here **before** the numbers are written so they cannot be presented as post-hoc rationale.

1. **The transcribed CAGRs use the publications' headline windows, not the model's eras.** PJM's
   `mid.near = 0.036` is the report's *10-year summer-peak* CAGR (2026→2036), but the model's near
   era ends at **2030**; over PJM's own 2026–2030 series the summer-peak CAGR is materially higher.
   Expect most `near` values to move on the window fix alone, independent of any basis question.
2. **The table is not internally consistent about what the scalar reproduces.** ERCOT/CAISO/PJM/MISO
   rows are derived from **peak** series, NYISO from **energy**, NEISO from a **blend** of the two.
   The model applies one flat multiplicative scalar (`runner.py::_scale_demand`), so peak CAGR ≡
   energy CAGR by construction and only one can be honoured. In DC-heavy ISOs the two diverge
   sharply (ERCOT's own Adjusted forecast: 2025→2030 **energy +15.2 %/yr vs peak +10.1 %/yr**,
   because DC raises the load factor). **This lane will curate BOTH metrics, re-derive each ISO on
   its EXISTING declared basis, quantify the divergence per ISO, and ROUTE the basis question to
   SCN-DESK** — changing the basis is a modelling-posture decision with large forecast
   consequences, not an intake, and it is not this lane's to take.

---

## 4. Method commitments (so the FINDING can be checked against them)

- **Schema-first**, through the `data-intake` skill: `data/dictionary/schema/load-forecast.schema.yaml`,
  a **tidy long** frame (the ISOs' layouts do not agree), per-ISO registry modules under
  `scripts/lib/load_forecast/`, `scripts/data/curate_load_forecast.py` writing only via
  `clean_io.write_clean`, the datatype registered in `regenerate_clean.py`, and
  `CleanDirTestCase` tests on tiny fixtures.
- **The curation script depends only on project dependencies** (`openpyxl`, stdlib `csv`). No PDF or
  `.xlsb` parser is added to `pyproject.toml`. Sources that are only published as PDF or `.xlsb`
  are **transcribed once into committed CSVs** under `data/raw/load-forecast/<iso>/`, each carrying
  its document/table/page citation, validated against the publication's own totals; the source
  document remains the immutable provenance record. This is the repo's existing convention
  (`data/raw/NYISO/README.md`: *"transcription sources, not machine inputs"*).
- **Large payloads go to the corpus convention** (gitignored payload + tracked `README.md` +
  `SHA256SUMS.txt`), not into the tracked tree: the 48.4 MB ERCOT `.xlsb` above all. The NYISO Gold
  Book is **not duplicated** — the curated rows cite the existing `data/raw/NYISO/` corpus entry.
- **Rule 14 [R-ACCURATE] binds.** Where a curated value moves a forecast result, the accurate value
  is kept, the movement is reported at full magnitude, and the root-cause question is opened. No
  value is reconciled back toward the constant it replaces.
- **Rule 25 [R-ISO-SCOPE] binds.** No ISO's series, share, profile or band is used as another's
  fallback, including where a cell would otherwise stay empty.
- **Rule 23 [R-FROZEN-DERIVE].** Every constant that moves cites the **data change** (a new edition
  read, or a series newly on disk) — never a residual. No solve is run by this lane.
- **`DATACENTER_ZONE_SHARE` is touched only where a newly-read table supersedes SCN-WS4a's value**,
  and where it does, both are shown side by side.

**Out of scope / STOP-and-route:** `policy/*`, `model/lp/*`, `config/scenarios.py`,
`configs/scenario_campaign_matrix.yaml`, `results/*`, `scripts/report_scenario_deltas.py`,
`scripts/register_forecast_run.py`, `frontend/data/*`. Anything found there is routed to SCN-DESK
in the FINDING, not edited.
