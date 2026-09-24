# AUDIT — backcast inputs: EIA-860 vintage, plant heat rates, CAMPD outages (all ISOs, 2019–2025)

Owner instruction 2026-09-24 (verbatim): *"Do an audit to make sure every iso is using EIA 860 and plant
specific heat rates for all model run years in the backcast. Things keep popping up where an iso is
revisiting 860 data or plant specific heat rates in backcast runs when it should be default for all ISOs
to have correct vintage for all years including holdouts and be using plant heat rates not asset class.
Same thing with campd outage data we should have granular outage data running thru the model for all
ISOs and all backcast years 2019-2025. After you identify what's not currently correct issue prompts to
fix and rerun ISOs."*

Audit HEAD: `40f4ed7a`. Zero LP spent — every number below is a committed `run_config*.json` read or a
zero-LP fleet load (`load_fleet_from_csv` / `load_retired_within_window`), reproducible with the census
commands in §6.

## 1. Verdict

**Not correct in any ISO.** Three systemic defects, one of which silently invalidates the one ISO that
*did* arm year-matched EIA-860:

| # | Defect | Severity |
|---|---|---|
| D1 | **Year-matched EIA-860 vintages carry NO heat rate.** `vintage_2019/2021/2022` `eia860_generators.parquet` have no `heat_rate` column; `vintage_2020`'s is 100 % null. With `eia860_vintage_tracks_solve_year` armed, **95–100 % of every ISO's thermal MW falls to the `HEAT_RATE_BINS` asset-class table in 2019–2022.** | CRITICAL |
| D2 | **The base heat rate is eGRID 2023 for every solve year.** `process_eia860._join_egrid_heat_rate` reads only `egrid2023_data_rev2.xlsx`/`PLNT23` — for the canonical snapshot, every vintage, and the within-window retiree parquet — though eGRID 2018–2024 workbooks are all committed in `data/raw/fleet-egrid/`. Any plant not in eGRID 2023 (i.e. most pre-2023 retirees) gets the class table. | HIGH |
| D3 | **Only SPP arms year-matched EIA-860**; every other ISO solves 2019–2025 on the 2025-ER snapshot + COD ramp (the pjm-167 finding: PJM 2021 coal understated by 9,986 MW / 39 % this way). **NWPP and SOCO carry ZERO within-window retirees** (channel returns nothing), so their holdout years would be missing every retired plant. | HIGH |
| D4 | **Measured CAMPD plant heat rates are a patchwork** — each class armed in a different subset of ISOs, and every artifact pools 2023–2025 only, so plants that retired before 2023 are never covered. | MEDIUM-HIGH |
| D5 | **CAMPD outage coverage and granularity are inconsistent.** NWPP and SOCO extracts cover 2023–2025 only (raw CAMPD absent for AL, GA, AZ, ID, OR, UT, WA, WY 2019–2022; CO/FL absent entirely); PJM short-gas starts 2020; the sub-5-day / partial-derate families are armed in 3 of 9 ISOs; the partial-derate family is armed nowhere outside ERCOT's plant-grain path. | MEDIUM-HIGH |
| D6 | **Registered year spans fall short of 2019–2025** in 8 of 9 ISOs. | MEDIUM |

**Contaminated verdict (new evidence under rule 28(a)):** PJM `eia860_vintage_tracks_solve_year` = **R**
(pjm-168, 2021 screen, "the model spends the restored coal to its rail"). That arm ran on `vintage_2021`,
which per D1 priced **100 % of PJM thermal at class-table heat rates** (every coal unit 8.8/10.0/10.8, every
CC 6.3/6.7/7.5). Its G3 kill ("the object is coal-vs-gas offer ordering") was measured on a fleet whose
coal-vs-gas ordering the defect itself set. The R is re-opened by this audit. Likewise SPP's registered
2019–2022 rung (`2026-09-22-hydro-5-spp-rung`) was solved on 100 % class-table heat rates.

## 2. Keeper-by-keeper configuration (committed `run_config*.json`)

`860trk` = `eia860_vintage_tracks_solve_year`; HR columns = `measured_<class>_heat_rates`; eFam/eId/eSC =
eGRID family/identity/steam-collapse; out = CAMPD outage file armed; short C/G = sub-5-day coal/gas
windows; part = unit partial-derate windows.

| ISO | keeper (registered years) | 860trk | CT | coal | ST | CC | CHP | eGRID repairs | outage extract | short C/G | part |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CAISO | caiso-290-leftedge (2022–25) | off | ✔ | n/a | ✗ | ✗ | ✔ | eFam | `-CAISO` (2018–26) | ✗/✗ | ✗ |
| ERCOT | ercot266-mer-five-year (2021–25) | off | ✗ (I) | bins | bins | bins | ✗ | — | `campd-unit-outages.csv` (2018–26) + ERCOT partial-shaped | ✗/✗ | plant-grain ✔ |
| MISO | miso-268-coal-yard (2020–25) | off | ✔ | ✗ | ✗ | ✗ | ✔ | — | `-unitroute-MISO` (2018–26) | ✔/✗ | ✗ |
| NEISO | hydro-5-neiso-ror (2020–25) | off | ✔ | ✗ | ✗ | ✗ | ✔ | — | `-NEISO` (2018–26) | ✗(R)/✗ | ✗ |
| NWPP | nwpp-49-ror-split (2023–25) | off | ✗ | ✔ | ✗ | ✗ | ✗ | — | `-NWPP` (**2023–25 only**) | ✗/✗ | ✗ |
| NYISO | nyiso-hydro3-ror-split (2022–25) | off | ✔ | n/a | ✗ | ✗ | ✔ | eId+eFam+eSC | `-perunitmerithour-NYISO` (2019–26) | ✗(I)/✗(I) | ✗ |
| PJM | pjm-h19-dbs-span (2023–25) + touchpoint (2020–22) | off (**R, contaminated**) | ✔ | ✗ | ✗ | ✗ | ✔ | — | `-PJM` (2018–26) | ✔/✔ (gas from 2020) | ✗ |
| SOCO | soco61-dark-unit (2023–25) | off | ✔ | ✔ | ✔ | ✔ | ✗ | eFam | `-perunitdark-SOCO` (**2023–25 only**) | ✗/✗ | ✗ |
| SPP | hydro-5-spp-floor (2023–25) + rung (2019–22) | **on** (D1 ⇒ 2019–22 class-table) | ✗ | ✗ | ✗ | ✗ | ✗ | — | `-SPP` (2019–25) | ✔/✗(R) | ✗ |

SPP-78 (`PRECOMMIT-spp-78-measured-heat-rates-2026-09-24.md`, in flight at audit HEAD) is arming SPP
CC/ST/coal measured rates — it does not touch D1/D2 and will need re-solving after F1.

## 3. Measured sizes (zero-LP fleet census)

**3a. D1 — share of thermal nameplate at an asset-class heat rate, by EIA-860 source** (pre-measured-overlay):

| ISO | canonical 2025ER | vintage_2021 | vintage_2023 |
|---|---|---|---|
| CAISO | 10.2 % | **95.4 %** | 10.1 % |
| MISO | 5.8 % | **100 %** | 5.1 % |
| NEISO | 4.1 % | **100 %** | 3.7 % |
| NWPP | 5.8 % | **100 %** | 5.3 % |
| NYISO | 6.3 % | **100 %** | 6.0 % |
| PJM | 2.5 % | **100 %** | 2.3 % |
| SOCO | 4.3 % | **100 %** | 4.1 % |
| SPP | 6.3 % | **100 %** (2019, 2020, 2021, 2022 all 100 %) | 4.2 % |

**3b. D2 — within-window retirees at an asset-class heat rate** (class-table MW / retiree MW online that year):

| ISO | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| PJM | **13,391 / 18,993** | 8,317 / 13,920 | 6,717 / 11,599 | 5,584 / 10,467 | 1,441 / 6,316 | 309 / 1,269 |
| MISO | **9,766 / 11,420** | 6,655 / 8,309 | 5,493 / 7,147 | 3,667 / 5,321 | 1,613 / 3,267 | 645 / 2,299 |
| NYISO | 1,593 / 2,054 | 1,207 / 1,644 | 527 / 964 | 523 / 960 | 0 / 437 | 0 / 21 |
| SPP | 1,168 / 2,038 | 1,111 / 1,980 | 86 / 956 | 86 / 956 | 32 / 902 | 27 / 33 |
| ERCOT | 1,670 / 1,671 | 840 / 841 | 840 / 841 | 840 / 841 | 840 / 841 | 0 / 1 |
| CAISO | 908 / 2,229 | 859 / 1,700 | 140 / 981 | 127 / 968 | 124 / 965 | 98 / 105 |
| NEISO | 678 / 2,636 | 674 / 2,632 | 660 / 2,618 | 437 / 1,874 | 308 / 1,745 | 78 / 1,493 |
| NWPP | **0 / 0** | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| SOCO | **0 / 0** | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |

Whole retiree parquet: 52,812 MW, **74 % with a null heat rate**.

**3c. ERCOT** builds from `data/raw/reference/custom-bin-assignments.csv` (hand-curated, one snapshot for every
year): 1,160 MW (1,126 CC_REGULAR + 33 CT) carry a null `Plant_Avg_HR_MMBtu_MWh` → `BIN_GROUP_HR_DEFAULT`;
the table's measurement years are undocumented.

**3d. D5 — CAMPD outage extract windows by start year** (armed file):

| ISO | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| NWPP `-NWPP` | — | — | — | — | 719 | 790 | 761 |
| SOCO `-perunitdark-SOCO` | — | — | — | — | 332 | 356 | 432 |
| PJM `-shortgas-PJM` | — | 283 | 291 | 409 | 317 | 323 | 236 |
| all others (std extract) | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |

Raw `data/raw/campd-unit-level/` state-years missing for 2019–2022: **AL, GA** (SOCO), **AZ, ID, OR, UT, WA,
WY** (NWPP); **CO and FL absent for every year**. `-short-CAISO` / `-short-NYISO` are empty by construction
(coal-scoped, no coal) — the correct granular channel there is short-gas, which exists only for PJM/SPP.

**3e. D6 — registered years vs the 2019–2025 target:** CAISO 2022–25 (missing 2019–21), ERCOT 2021–25
(2019–20), MISO 2020–25 (2019), NEISO 2020–25 (2019), NWPP 2023–25 (2019–22), NYISO 2022–25 (2019–21), PJM
2020–25 (2019), SOCO 2023–25 (2019–22), SPP 2019–25 (complete, but 2019–22 contaminated by D1).

## 4. Fix plan

Two ISO-agnostic foundation lanes land first (parallel, disjoint files), then nine per-ISO re-solve lanes.
All foundation work is backcast-only and zero-free-parameter (rules 13/14/21/24); the forecast path keeps
its snapshot.

- **F1 — heat rate + EIA-860 vintage (fixes D1, D2, D3, D4).** Year-matched eGRID join into every
  `vintage_<Y>/` and the retiree parquet with a nearest-vintage fallback so the class table is reached only
  by a plant absent from **every** eGRID vintage; measured CAMPD heat-rate artifacts for **every class × every
  ISO** re-derived over 2019–2025; NWPP/SOCO retiree channel repaired; `eia860_vintage_tracks_solve_year`
  flipped to default-on in backcast mode (frozen cache-key drop value `False`, the D76 (b′-1) pattern);
  the measured-HR flags likewise flipped default-on in backcast mode.
- **F2 — CAMPD outages (fixes D5).** Raw CAMPD intake for the missing state-years; every ISO's std / short-coal
  / short-gas / partial-derate extracts re-derived over 2019–2025 with `.meta.json` sidecars.
- **R-<ISO> ×9 (fixes D6, re-solves on the corrected inputs).** Dispatched only after F1 **and** F2 merge,
  pinned to the post-merge SHA. One shard per year (rule 36), 2019–2025 wherever the ISO has benchmarks.

## 5. Prompts

### 5.1 F1 — heat rate + EIA-860 vintage foundation

```text
SESSION F1 — BACKCAST HEAT-RATE + EIA-860 VINTAGE FOUNDATION (ISO-agnostic; code + derived data; NO LP)
DATA PROFILE: all
MODEL: Opus or Fable (rule 27 — writes src/market_sim/ and scripts/)

READ FIRST: docs/handoffs/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md (§1 D1–D4, §3a–3c),
src/market_sim/config/scenarios.py (eia860_vintage_year … measured_cc_heat_rates block, ~L5225–5620),
scripts/data/process_eia860.py::_join_egrid_heat_rate, src/market_sim/data/fleet/eia860.py
(load_fleet_from_csv, load_retired_within_window, _rows_to_generators ~L1377), the mechanism matrix rows
for eia860_vintage_tracks_solve_year and measured_*_heat_rates.

OWNER INSTRUCTION (2026-09-24): every ISO's backcast uses the year-correct EIA-860 vintage for every year
2019–2025 including holdouts, and plant-specific heat rates — never the asset-class table — by DEFAULT.

DELIVERABLES
1. D1+D2 — YEAR-MATCHED eGRID HEAT RATE. Make _join_egrid_heat_rate vintage-aware: vintage_<Y> joins eGRID
   <Y> (eGRID 2018–2024 are committed in data/raw/fleet-egrid/; the canonical 2025ER snapshot joins the
   latest vintage, eGRID 2024, and state that choice in the docstring). Fallback order, zero free
   parameters: same-year eGRID PLHTRT → the plant's nearest eGRID vintage (tie → earlier) → only then
   HEAT_RATE_BINS. Apply the SAME join to eia860_generator_retired_within_window.parquet using each
   retiree's last operating year. Keep the existing EGRID_HR_WINDOW_BTU_KWH plausibility window and the
   boundary-repair / CT-floor / CHP seams (they must read the matched vintage, not egrid2023 hard-coded —
   grep every "egrid2023" / "PLNT23" on the solve path and route each through one resolver, rule 19).
   Regenerate vintage_2018…2024 eia860_generators.parquet + the canonical + retiree parquets.
2. D3 — RETIREE CHANNEL FOR NWPP AND SOCO returns zero rows for every year (audit §3b). Root-cause it
   (BA-code membership is the first suspect: NWPP spans ~17 BAs, SOCO's BA set) and fix at the membership
   seam, not per plant.
3. D4 — MEASURED CAMPD HEAT RATES, EVERY CLASS × EVERY ISO. Re-derive campd_{ct,coal,st,cc}_heat_rates_<ISO>
   and chp_power_only_heat_rates_<ISO> for ALL nine ISOs over 2019–2025 (not 2023–2025), so pre-2023
   retirees are covered. Emit a per-(plant, year) rate AND the plant's pooled rate; the loader takes the
   solve year's own rate where the plant has steady-state hours that year, else its pooled rate — decide
   and justify the minimum-hours rule from the derive's existing identification (no new swept threshold).
   Keep every existing boundary guard (the CC unmetered-steam refusal, class scoping, CHP out of the CC
   scope). ERCOT CT is matrix-I (bins already carry CAMPD HR) — leave ERCOT's measured flags alone; ERCOT
   is handled in R-ERCOT.
4. DEFAULTS. Flip eia860_vintage_tracks_solve_year and measured_{ct,coal,st,cc,chp}_heat_rates to
   default-ON for mode=="backcast" ONLY, by the capacity_screen_peak_measured_hindcast (b′-1) pattern:
   append to _CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS with the frozen drop value left at the old default,
   plus a __post_init__ coercion back to False whenever mode != "backcast", so forecast / hindcast /
   crossover keys and outputs are byte-identical. Explicit --no-… reaches the old posture.
   carry_operating_mothballs: flip it on in backcast too iff item 1 makes it consistent (it reads the same
   vintage); otherwise state why not.
5. CENSUS (commit it, zero LP): rerun the audit §3a/§3b census after the fix for all nine ISOs × 2019–2025.
   ACCEPTANCE: class-table share of thermal nameplate ≤ the canonical-2023 share in every ISO-year
   (i.e. D1 gone), retiree class-table MW reduced to plants absent from every eGRID vintage (list them),
   NWPP/SOCO retiree rows > 0 where EIA-860 shows retirements. Report the residual class-table MW per
   ISO-year with the plant list.
6. MATRIX: re-open PJM eia860_vintage_tracks_solve_year R → O citing audit §1 (the pjm-168 arm ran on 100 %
   class-table heat rates). Update every ISO shard's measured_*_heat_rates / eia860 cells to record the
   default flip (no verdict change except PJM's R→O).
7. Tests: trivial-case unit tests for the vintage-aware join, the fallback order, the retiree join, the
   backcast-only coercion (forecast config byte-identical), and a key-stability test over every committed
   keeper run_config for the FLAG FLIPS (declared, so keys must not move). The DATA regeneration in items
   1–3 is an intended solve-input change — record it in solve_surface / the PR, and state which keeper
   years it moves (every ISO's will; the R-<ISO> lanes re-solve them).

HARD RULES (CLAUDE.md is binding; these are the ones this lane is most likely to trip):
- Rule 27 [R-PUSH]: Opus/Fable only; edit locally, push exact bytes, blob-verify any ≥300-line file after push.
- Rule 13/14/21/24/25: every value is measured or published, zero fitted scalars, per-ISO artifacts only,
  no env-var knobs, every new ScenarioConfig field gets a mechanism-matrix row + a cell in EVERY ISO shard
  in the same PR (rule 28(c), CI-enforced).
- Rule 23 [R-FROZEN-DERIVE]: re-derivations cite this audit (a data-completeness defect) as the data change.
- Rule 26: nothing is zeroed; a replaced path is deleted.
- Never touch frontend/data/backcast/** or any keeper shard; this is not a promotion lane.

DO NOT run any LP, register anything, or touch keepers. Open a PR to main with the census as its evidence;
final report = the census table, the residual class-table plant list, files changed, test results.
```

### 5.2 F2 — CAMPD outage coverage foundation

```text
SESSION F2 — CAMPD OUTAGE COVERAGE 2019–2025, EVERY ISO (data intake + derive; NO LP)
DATA PROFILE: all
MODEL: Opus or Fable (rule 27 — scripts/ + src/ outage loader touch)

READ FIRST: docs/handoffs/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md (§1 D5, §3d),
scripts/data/fetch_campd_unit_level.py, scripts/data/derive_campd_unit_outages.py (std / --short-windows /
--short-window-groups gas --merit-order-guard / --partial-windows / --per-unit-crosswalk modes),
src/market_sim/data/outages.py, each ISO's committed campd-unit-outages*-<ISO>.meta.json, and the
mechanism-matrix outage rows. Use the data-intake skill for the raw intake.

OWNER INSTRUCTION (2026-09-24): granular CAMPD outage data runs through the model for ALL ISOs and ALL
backcast years 2019–2025.

DELIVERABLES
1. RAW INTAKE. Fetch CAMPD hourly unit-level for the missing state-years: AL, GA, AZ, ID, OR, UT, WA, WY for
   2019–2022; CO and FL for 2019–2025 (check each ISO's plant registry for any other state its fleet
   touches that is missing — derive the list, don't trust mine). Update the corpus README + SHA256SUMS.
   If the EPA API or the network policy blocks it, STOP that item, read_documentation(environment.network)
   and report exactly what is blocked — do not substitute another source.
2. RE-DERIVE, SAME DERIVER, SAME FROZEN CONSTANTS, --years 2019..2025, for every ISO, in each ISO's
   CURRENTLY-ARMED form (the keeper's resolved_inputs.campd_unit_outages path names it: -unitroute-MISO,
   -perunitmerithour-NYISO, -perunitdark-SOCO, …) so a keeper replay on 2023–2025 stays byte-identical —
   PROVE that by diffing the regenerated 2023–2025 rows against the committed file (must be identical;
   any difference is a finding, report it, do not paper over it).
   Families per ISO: std (≥5 d) everywhere; short-coal where the ISO has coal; short-gas (merit-guarded) for
   EVERY ISO; unit partial-derate (--partial-windows) for EVERY non-ERCOT ISO. Write each .meta.json.
   PJM -shortgas must reach 2019. ERCOT: extend campd-unit-outages.csv only if its deriver has a gap; its
   partial-shaped path is ERCOT's own.
3. COVERAGE TABLE (commit it): ISO × family × year window counts 2019–2025 + MW-weighted outage share, with
   every empty cell explained (no coal, no raw data, etc.).
4. Do NOT flip any outage flag's default and do NOT arm anything — arming is per ISO in the R-<ISO> lanes
   (rule 25). No new ScenarioConfig fields unless unavoidable (then rule 28(c)).

HARD RULES (CLAUDE.md is binding; these are the ones this lane is most likely to trip):
- Rule 27 [R-PUSH]: Opus/Fable only; edit locally, push exact bytes, blob-verify any ≥300-line file after push.
- Rule 13/14/21/24/25: every value is measured or published, zero fitted scalars, per-ISO artifacts only,
  no env-var knobs, every new ScenarioConfig field gets a mechanism-matrix row + a cell in EVERY ISO shard
  in the same PR (rule 28(c), CI-enforced).
- Rule 23 [R-FROZEN-DERIVE]: re-derivations cite this audit (a data-completeness defect) as the data change.
- Rule 26: nothing is zeroed; a replaced path is deleted.
- Never touch frontend/data/backcast/** or any keeper shard; this is not a promotion lane.

DO NOT run any LP or register anything. Open a PR to main; final report = the coverage table, the
2023–2025 byte-identity proof per ISO, raw files fetched, anything blocked.
```

### 5.3 Per-ISO re-solve prompts — dispatch only after F1 AND F2 merge

#### 5.3.1 R-CAISO

```text
SESSION R-CAISO — RE-SOLVE CAISO 2019–2025 ON CORRECTED BACKCAST INPUTS (vintage EIA-860, plant heat rates, granular CAMPD outages)
DATA PROFILE: caiso
MODEL: Opus or Fable
PRECONDITION: F1 AND F2 (docs/handoffs/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md §5) are MERGED to
main. If either is not, STOP and report — do not solve on the old inputs.

READ FIRST: the audit doc (§1–§3, the CAISO rows), the F1 and F2 PRs' census/coverage tables,
frontend/data/backcast/keepers/CAISO.json, results/calibration/xiso8_leftedge_span/run_config*.json (the
incumbent recipe), docs/codebase-site/data/mechanism-matrix/CAISO.js + docs/mechanism-testing-matrix.md
§5 CAISO lever queue (rule 28(a)).

OWNER INSTRUCTION (2026-09-24): every backcast year 2019–2025 runs on the year-correct EIA-860 vintage,
plant-specific heat rates (never the asset-class table), and granular CAMPD outage data.

INCUMBENT: 2026-09-20-caiso-290-leftedge (bundle results/calibration/xiso8_leftedge_span, registered 2022–2025).

CAISO-SPECIFIC:
- EIA-860: vintage tracking now default-on (F1) — confirm run_config shows it resolved per year.
- Heat rates: keeper arms CT, CHP, egrid_family. ADD measured ST + CC (F1 artifacts). No coal in CAISO.
- Outages: std extract armed; short-coal is I (no coal). ARM short-gas and unit partial-derate (F2
  artifacts; cells U). caiso_dam_outages exists (from 2021-06-18) — it is a measured ISO-native
  source (rule 14): state whether it should replace CAMPD windows where it covers, and if yes arm it
  for the years it covers; CAMPD stays the fallback.
- Years: extend to 2019–2025 (missing 2019–2021). Check benchmark availability for 2019–2021 first.

PROCEDURE
0. Phase 0 (zero LP, in this session): enumerate the ISO's registered years (rule 34(c)/35(b)) and write
   them down; for each year 2019–2025 confirm benchmarks exist; run a fleet-only census per year showing
   (a) the EIA-860 vintage resolved, (b) thermal MW at a class-table heat rate (target: only plants absent
   from every eGRID vintage and CAMPD — list them), (c) outage windows/MW per family. G-DRIFT the keeper
   (rule 29(b)) — the F1/F2 hunks are LIVE by design; name them. Write the PRECOMMIT with the recipe
   (incumbent recipe + the arms above, offer-curve multipliers UNCHANGED — this is an input correction,
   rule 1(c): no re-tuning against the gates) and push it; pin its full 40-char SHA.
1. Solve: ONE SHARD PER YEAR, 2019…2025 (rule 36), launched via create_session with that SHA,
   own --out-dir results/calibration/<lane>_<year>/, own branch, full bundle pushed incl.
   dispatch/<year>_P1.parquet via the .gitignore negation + plain git add (rule 34(a)), the rule-32(c)
   launch checklist verbatim (hard stops, forbidden commands, "a shard that stops with a clear report is a
   SUCCESS; a shard that repairs infrastructure is a FAILURE", report container-preflight + memory-peak
   lines). Launch all years at once; do not ask permission.
2. Parent: fetch each leg, verify config signature (vintage resolved = solve year, measured-HR flags on,
   outage files + sha256), compose (zero LP), attest (DOF ledger; the multiplier block unchanged), score,
   register on the dashboard (rule 15), update the CAISO matrix shard cells touched (rule 28(b)).
3. Archive every shard once its bytes are in hand (rule 33); land what must survive on main (rule 33(f)).
4. REPORT at full magnitude, per year, old keeper vs re-solve: C1–C8 table + determination, class TWh
   deltas, price MAE/bias, and the census deltas from step 0. Recommend promote / not — then ASK the owner
   the promotion question explicitly (rule 31); do NOT promote or prune on your own reading.

HARD RULES: CLAUDE.md is binding — rules 1, 13, 14, 16, 21, 25, 27, 28, 31–36 especially. The parent never
solves (rule 32(a)). No new tuning channel; if a gate regresses, report it and root-cause it (rule 14),
never re-tune multipliers to recover it.
```

#### 5.3.2 R-ERCOT

```text
SESSION R-ERCOT — RE-SOLVE ERCOT 2019–2025 ON CORRECTED BACKCAST INPUTS (vintage EIA-860, plant heat rates, granular CAMPD outages)
DATA PROFILE: ercot
MODEL: Opus or Fable
PRECONDITION: F1 AND F2 (docs/handoffs/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md §5) are MERGED to
main. If either is not, STOP and report — do not solve on the old inputs.

READ FIRST: the audit doc (§1–§3, the ERCOT rows), the F1 and F2 PRs' census/coverage tables,
frontend/data/backcast/keepers/ERCOT.json, results/calibration/ercot_mer20260919_five_year/run_config*.json (the
incumbent recipe), docs/codebase-site/data/mechanism-matrix/ERCOT.js + docs/mechanism-testing-matrix.md
§5 ERCOT lever queue (rule 28(a)).

OWNER INSTRUCTION (2026-09-24): every backcast year 2019–2025 runs on the year-correct EIA-860 vintage,
plant-specific heat rates (never the asset-class table), and granular CAMPD outage data.

INCUMBENT: 2026-09-19-ercot266-mer-five-year (bundle results/calibration/ercot_mer20260919_five_year, registered 2021–2025).

ERCOT-SPECIFIC:
- ERCOT is NOT plant_level_fleet: it builds from data/raw/reference/custom-bin-assignments.csv (hand-curated,
  ONE snapshot for every year). Audit §3c: 1,160 MW (1,126 CC_REGULAR + 33 CT) have a null
  Plant_Avg_HR_MMBtu_MWh → BIN_GROUP_HR_DEFAULT; the table's measurement years are undocumented.
  Deliver: (a) document the Plant_Avg_HR provenance (which CAMPD years); (b) give every bin a
  plant-specific rate from CAMPD/eGRID (year-matched per solve year if the bin path can carry it,
  else pooled 2019–2025) — zero rows at BIN_GROUP_HR_DEFAULT unless the plant is absent from every
  source (list them); (c) EIA-860 vintage tracking (F1 default) feeds ERCOT's COD map + retiree
  channel — confirm it resolves per year; ERCOT's retiree channel had 840–1,670 MW at class HR
  (§3b), which F1 fixes — verify.
- ERCOT keeps its partitioned configs (carve-out 2021–2023 / forward 2024–2025); every leg re-solves.
- Outages: std extract (2018–26) + ERCOT partial-shaped + noncampd availability are armed. ARM short-gas
  if F2 produced an ERCOT artifact and its merit guard clears; short-coal is I.
- Years: extend to 2019–2025 (missing 2019–2020); state which partition config 2019–2020 take and why
  (structure, never the residual).

PROCEDURE
0. Phase 0 (zero LP, in this session): enumerate the ISO's registered years (rule 34(c)/35(b)) and write
   them down; for each year 2019–2025 confirm benchmarks exist; run a fleet-only census per year showing
   (a) the EIA-860 vintage resolved, (b) thermal MW at a class-table heat rate (target: only plants absent
   from every eGRID vintage and CAMPD — list them), (c) outage windows/MW per family. G-DRIFT the keeper
   (rule 29(b)) — the F1/F2 hunks are LIVE by design; name them. Write the PRECOMMIT with the recipe
   (incumbent recipe + the arms above, offer-curve multipliers UNCHANGED — this is an input correction,
   rule 1(c): no re-tuning against the gates) and push it; pin its full 40-char SHA.
1. Solve: ONE SHARD PER YEAR, 2019…2025 (rule 36), launched via create_session with that SHA,
   own --out-dir results/calibration/<lane>_<year>/, own branch, full bundle pushed incl.
   dispatch/<year>_P1.parquet via the .gitignore negation + plain git add (rule 34(a)), the rule-32(c)
   launch checklist verbatim (hard stops, forbidden commands, "a shard that stops with a clear report is a
   SUCCESS; a shard that repairs infrastructure is a FAILURE", report container-preflight + memory-peak
   lines). Launch all years at once; do not ask permission.
2. Parent: fetch each leg, verify config signature (vintage resolved = solve year, measured-HR flags on,
   outage files + sha256), compose (zero LP), attest (DOF ledger; the multiplier block unchanged), score,
   register on the dashboard (rule 15), update the ERCOT matrix shard cells touched (rule 28(b)).
3. Archive every shard once its bytes are in hand (rule 33); land what must survive on main (rule 33(f)).
4. REPORT at full magnitude, per year, old keeper vs re-solve: C1–C8 table + determination, class TWh
   deltas, price MAE/bias, and the census deltas from step 0. Recommend promote / not — then ASK the owner
   the promotion question explicitly (rule 31); do NOT promote or prune on your own reading.

HARD RULES: CLAUDE.md is binding — rules 1, 13, 14, 16, 21, 25, 27, 28, 31–36 especially. The parent never
solves (rule 32(a)). No new tuning channel; if a gate regresses, report it and root-cause it (rule 14),
never re-tune multipliers to recover it.
```

#### 5.3.3 R-MISO

```text
SESSION R-MISO — RE-SOLVE MISO 2019–2025 ON CORRECTED BACKCAST INPUTS (vintage EIA-860, plant heat rates, granular CAMPD outages)
DATA PROFILE: miso
MODEL: Opus or Fable
PRECONDITION: F1 AND F2 (docs/handoffs/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md §5) are MERGED to
main. If either is not, STOP and report — do not solve on the old inputs.

READ FIRST: the audit doc (§1–§3, the MISO rows), the F1 and F2 PRs' census/coverage tables,
frontend/data/backcast/keepers/MISO.json, results/calibration/miso268_yard_span/run_config*.json (the
incumbent recipe), docs/codebase-site/data/mechanism-matrix/MISO.js + docs/mechanism-testing-matrix.md
§5 MISO lever queue (rule 28(a)).

OWNER INSTRUCTION (2026-09-24): every backcast year 2019–2025 runs on the year-correct EIA-860 vintage,
plant-specific heat rates (never the asset-class table), and granular CAMPD outage data.

INCUMBENT: 2026-09-24-miso-268-coal-yard (bundle results/calibration/miso268_yard_span, registered 2020–2025).

MISO-SPECIFIC:
- Heat rates: keeper arms CT + CHP. ADD coal, ST, CC measured (F1). MISO had 9.8 GW of 2019 retirees on
  class-table HR (§3b) — F1 fixes; verify in your phase-0 census.
- EIA-860 vintage default-on (F1) + keeper already carries mothball carry + retiree vintage scope — confirm
  they compose (no double carry; rule 19).
- Outages: unitroute std + short-coal armed. ARM short-gas + unit partial-derate (U cells).
- Years: extend to 2019–2025 (missing 2019).

PROCEDURE
0. Phase 0 (zero LP, in this session): enumerate the ISO's registered years (rule 34(c)/35(b)) and write
   them down; for each year 2019–2025 confirm benchmarks exist; run a fleet-only census per year showing
   (a) the EIA-860 vintage resolved, (b) thermal MW at a class-table heat rate (target: only plants absent
   from every eGRID vintage and CAMPD — list them), (c) outage windows/MW per family. G-DRIFT the keeper
   (rule 29(b)) — the F1/F2 hunks are LIVE by design; name them. Write the PRECOMMIT with the recipe
   (incumbent recipe + the arms above, offer-curve multipliers UNCHANGED — this is an input correction,
   rule 1(c): no re-tuning against the gates) and push it; pin its full 40-char SHA.
1. Solve: ONE SHARD PER YEAR, 2019…2025 (rule 36), launched via create_session with that SHA,
   own --out-dir results/calibration/<lane>_<year>/, own branch, full bundle pushed incl.
   dispatch/<year>_P1.parquet via the .gitignore negation + plain git add (rule 34(a)), the rule-32(c)
   launch checklist verbatim (hard stops, forbidden commands, "a shard that stops with a clear report is a
   SUCCESS; a shard that repairs infrastructure is a FAILURE", report container-preflight + memory-peak
   lines). Launch all years at once; do not ask permission.
2. Parent: fetch each leg, verify config signature (vintage resolved = solve year, measured-HR flags on,
   outage files + sha256), compose (zero LP), attest (DOF ledger; the multiplier block unchanged), score,
   register on the dashboard (rule 15), update the MISO matrix shard cells touched (rule 28(b)).
3. Archive every shard once its bytes are in hand (rule 33); land what must survive on main (rule 33(f)).
4. REPORT at full magnitude, per year, old keeper vs re-solve: C1–C8 table + determination, class TWh
   deltas, price MAE/bias, and the census deltas from step 0. Recommend promote / not — then ASK the owner
   the promotion question explicitly (rule 31); do NOT promote or prune on your own reading.

HARD RULES: CLAUDE.md is binding — rules 1, 13, 14, 16, 21, 25, 27, 28, 31–36 especially. The parent never
solves (rule 32(a)). No new tuning channel; if a gate regresses, report it and root-cause it (rule 14),
never re-tune multipliers to recover it.
```

#### 5.3.4 R-NEISO

```text
SESSION R-NEISO — RE-SOLVE NEISO 2019–2025 ON CORRECTED BACKCAST INPUTS (vintage EIA-860, plant heat rates, granular CAMPD outages)
DATA PROFILE: neiso
MODEL: Opus or Fable
PRECONDITION: F1 AND F2 (docs/handoffs/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md §5) are MERGED to
main. If either is not, STOP and report — do not solve on the old inputs.

READ FIRST: the audit doc (§1–§3, the NEISO rows), the F1 and F2 PRs' census/coverage tables,
frontend/data/backcast/keepers/NEISO.json, results/calibration/hydro5_neiso_ror_span/run_config*.json (the
incumbent recipe), docs/codebase-site/data/mechanism-matrix/NEISO.js + docs/mechanism-testing-matrix.md
§5 NEISO lever queue (rule 28(a)).

OWNER INSTRUCTION (2026-09-24): every backcast year 2019–2025 runs on the year-correct EIA-860 vintage,
plant-specific heat rates (never the asset-class table), and granular CAMPD outage data.

INCUMBENT: 2026-09-22-hydro-5-neiso-ror (bundle results/calibration/hydro5_neiso_ror_span, registered 2020–2025).

NEISO-SPECIFIC:
- Heat rates: keeper arms CT + CHP. ADD ST, CC (and coal if any NEISO coal remains in 2019–2025 — Merrimack,
  Bridgeport — check).
- Outages: std armed. short-coal is R — read its evidence; re-open only if that rejection ran on the D1/D2
  contaminated inputs, else leave it. ARM short-gas + unit partial-derate (U cells).
- Years: extend to 2019–2025 (missing 2019).

PROCEDURE
0. Phase 0 (zero LP, in this session): enumerate the ISO's registered years (rule 34(c)/35(b)) and write
   them down; for each year 2019–2025 confirm benchmarks exist; run a fleet-only census per year showing
   (a) the EIA-860 vintage resolved, (b) thermal MW at a class-table heat rate (target: only plants absent
   from every eGRID vintage and CAMPD — list them), (c) outage windows/MW per family. G-DRIFT the keeper
   (rule 29(b)) — the F1/F2 hunks are LIVE by design; name them. Write the PRECOMMIT with the recipe
   (incumbent recipe + the arms above, offer-curve multipliers UNCHANGED — this is an input correction,
   rule 1(c): no re-tuning against the gates) and push it; pin its full 40-char SHA.
1. Solve: ONE SHARD PER YEAR, 2019…2025 (rule 36), launched via create_session with that SHA,
   own --out-dir results/calibration/<lane>_<year>/, own branch, full bundle pushed incl.
   dispatch/<year>_P1.parquet via the .gitignore negation + plain git add (rule 34(a)), the rule-32(c)
   launch checklist verbatim (hard stops, forbidden commands, "a shard that stops with a clear report is a
   SUCCESS; a shard that repairs infrastructure is a FAILURE", report container-preflight + memory-peak
   lines). Launch all years at once; do not ask permission.
2. Parent: fetch each leg, verify config signature (vintage resolved = solve year, measured-HR flags on,
   outage files + sha256), compose (zero LP), attest (DOF ledger; the multiplier block unchanged), score,
   register on the dashboard (rule 15), update the NEISO matrix shard cells touched (rule 28(b)).
3. Archive every shard once its bytes are in hand (rule 33); land what must survive on main (rule 33(f)).
4. REPORT at full magnitude, per year, old keeper vs re-solve: C1–C8 table + determination, class TWh
   deltas, price MAE/bias, and the census deltas from step 0. Recommend promote / not — then ASK the owner
   the promotion question explicitly (rule 31); do NOT promote or prune on your own reading.

HARD RULES: CLAUDE.md is binding — rules 1, 13, 14, 16, 21, 25, 27, 28, 31–36 especially. The parent never
solves (rule 32(a)). No new tuning channel; if a gate regresses, report it and root-cause it (rule 14),
never re-tune multipliers to recover it.
```

#### 5.3.5 R-NWPP

```text
SESSION R-NWPP — RE-SOLVE NWPP 2019–2025 ON CORRECTED BACKCAST INPUTS (vintage EIA-860, plant heat rates, granular CAMPD outages)
DATA PROFILE: nwpp
MODEL: Opus or Fable
PRECONDITION: F1 AND F2 (docs/handoffs/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md §5) are MERGED to
main. If either is not, STOP and report — do not solve on the old inputs.

READ FIRST: the audit doc (§1–§3, the NWPP rows), the F1 and F2 PRs' census/coverage tables,
frontend/data/backcast/keepers/NWPP.json, results/calibration/nwpp49_ror_span/run_config*.json (the
incumbent recipe), docs/codebase-site/data/mechanism-matrix/NWPP.js + docs/mechanism-testing-matrix.md
§5 NWPP lever queue (rule 28(a)).

OWNER INSTRUCTION (2026-09-24): every backcast year 2019–2025 runs on the year-correct EIA-860 vintage,
plant-specific heat rates (never the asset-class table), and granular CAMPD outage data.

INCUMBENT: 2026-09-24-nwpp-49-ror-split (bundle results/calibration/nwpp49_ror_span, registered 2023–2025).

NWPP-SPECIFIC:
- EIA-860: NWPP's retiree channel returned ZERO rows every year (§3b) — F1 repairs it; verify retirees now
  appear (Colstrip 1–2, Boardman, Centralia 1, North Valmy 1, Naughton coal units, …) with plant HRs.
- Heat rates: keeper arms coal only. ADD CT, ST, CC (F1); CHP if the artifact is non-empty.
- Outages: std extract was 2023–2025 only (raw CAMPD missing for AZ/ID/OR/UT/WA/WY 2019–2022) — F2 extends.
  ARM short-coal, short-gas, partial-derate (all U) where the F2 artifacts are non-empty.
- Years: extend to 2019–2025 (missing 2019–2022). Check benchmarks (EIA-930 BA sums, Mid-C/Palo Verde
  hub prices) exist for 2019–2022 before launching; a year with no benchmark is named in the PRECOMMIT.

PROCEDURE
0. Phase 0 (zero LP, in this session): enumerate the ISO's registered years (rule 34(c)/35(b)) and write
   them down; for each year 2019–2025 confirm benchmarks exist; run a fleet-only census per year showing
   (a) the EIA-860 vintage resolved, (b) thermal MW at a class-table heat rate (target: only plants absent
   from every eGRID vintage and CAMPD — list them), (c) outage windows/MW per family. G-DRIFT the keeper
   (rule 29(b)) — the F1/F2 hunks are LIVE by design; name them. Write the PRECOMMIT with the recipe
   (incumbent recipe + the arms above, offer-curve multipliers UNCHANGED — this is an input correction,
   rule 1(c): no re-tuning against the gates) and push it; pin its full 40-char SHA.
1. Solve: ONE SHARD PER YEAR, 2019…2025 (rule 36), launched via create_session with that SHA,
   own --out-dir results/calibration/<lane>_<year>/, own branch, full bundle pushed incl.
   dispatch/<year>_P1.parquet via the .gitignore negation + plain git add (rule 34(a)), the rule-32(c)
   launch checklist verbatim (hard stops, forbidden commands, "a shard that stops with a clear report is a
   SUCCESS; a shard that repairs infrastructure is a FAILURE", report container-preflight + memory-peak
   lines). Launch all years at once; do not ask permission.
2. Parent: fetch each leg, verify config signature (vintage resolved = solve year, measured-HR flags on,
   outage files + sha256), compose (zero LP), attest (DOF ledger; the multiplier block unchanged), score,
   register on the dashboard (rule 15), update the NWPP matrix shard cells touched (rule 28(b)).
3. Archive every shard once its bytes are in hand (rule 33); land what must survive on main (rule 33(f)).
4. REPORT at full magnitude, per year, old keeper vs re-solve: C1–C8 table + determination, class TWh
   deltas, price MAE/bias, and the census deltas from step 0. Recommend promote / not — then ASK the owner
   the promotion question explicitly (rule 31); do NOT promote or prune on your own reading.

HARD RULES: CLAUDE.md is binding — rules 1, 13, 14, 16, 21, 25, 27, 28, 31–36 especially. The parent never
solves (rule 32(a)). No new tuning channel; if a gate regresses, report it and root-cause it (rule 14),
never re-tune multipliers to recover it.
```

#### 5.3.6 R-NYISO

```text
SESSION R-NYISO — RE-SOLVE NYISO 2019–2025 ON CORRECTED BACKCAST INPUTS (vintage EIA-860, plant heat rates, granular CAMPD outages)
DATA PROFILE: nyiso
MODEL: Opus or Fable
PRECONDITION: F1 AND F2 (docs/handoffs/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md §5) are MERGED to
main. If either is not, STOP and report — do not solve on the old inputs.

READ FIRST: the audit doc (§1–§3, the NYISO rows), the F1 and F2 PRs' census/coverage tables,
frontend/data/backcast/keepers/NYISO.json, results/calibration/hydro3_nyiso_ror_span/run_config*.json (the
incumbent recipe), docs/codebase-site/data/mechanism-matrix/NYISO.js + docs/mechanism-testing-matrix.md
§5 NYISO lever queue (rule 28(a)).

OWNER INSTRUCTION (2026-09-24): every backcast year 2019–2025 runs on the year-correct EIA-860 vintage,
plant-specific heat rates (never the asset-class table), and granular CAMPD outage data.

INCUMBENT: 2026-09-22-nyiso-hydro3-ror-split (bundle results/calibration/hydro3_nyiso_ror_span, registered 2022–2025).

NYISO-SPECIFIC:
- Heat rates: keeper arms CT, CHP, eGRID identity/family/steam-collapse. ADD ST, CC measured (F1) — rule 19:
  confirm precedence with the eGRID repairs (the measured CAMPD rate wins where it covers; eGRID repairs
  cover the CAMPD-less plants). NYISO had 1.6 GW of 2019 retirees on class HR.
- Outages: perunitmerithour extract armed (2019–26). short-coal I (no coal), short-gas I — read the I
  evidence; if it was measured on contaminated inputs re-screen, else leave. ARM unit partial-derate (U).
- Years: extend to 2019–2025 (missing 2019–2021).

PROCEDURE
0. Phase 0 (zero LP, in this session): enumerate the ISO's registered years (rule 34(c)/35(b)) and write
   them down; for each year 2019–2025 confirm benchmarks exist; run a fleet-only census per year showing
   (a) the EIA-860 vintage resolved, (b) thermal MW at a class-table heat rate (target: only plants absent
   from every eGRID vintage and CAMPD — list them), (c) outage windows/MW per family. G-DRIFT the keeper
   (rule 29(b)) — the F1/F2 hunks are LIVE by design; name them. Write the PRECOMMIT with the recipe
   (incumbent recipe + the arms above, offer-curve multipliers UNCHANGED — this is an input correction,
   rule 1(c): no re-tuning against the gates) and push it; pin its full 40-char SHA.
1. Solve: ONE SHARD PER YEAR, 2019…2025 (rule 36), launched via create_session with that SHA,
   own --out-dir results/calibration/<lane>_<year>/, own branch, full bundle pushed incl.
   dispatch/<year>_P1.parquet via the .gitignore negation + plain git add (rule 34(a)), the rule-32(c)
   launch checklist verbatim (hard stops, forbidden commands, "a shard that stops with a clear report is a
   SUCCESS; a shard that repairs infrastructure is a FAILURE", report container-preflight + memory-peak
   lines). Launch all years at once; do not ask permission.
2. Parent: fetch each leg, verify config signature (vintage resolved = solve year, measured-HR flags on,
   outage files + sha256), compose (zero LP), attest (DOF ledger; the multiplier block unchanged), score,
   register on the dashboard (rule 15), update the NYISO matrix shard cells touched (rule 28(b)).
3. Archive every shard once its bytes are in hand (rule 33); land what must survive on main (rule 33(f)).
4. REPORT at full magnitude, per year, old keeper vs re-solve: C1–C8 table + determination, class TWh
   deltas, price MAE/bias, and the census deltas from step 0. Recommend promote / not — then ASK the owner
   the promotion question explicitly (rule 31); do NOT promote or prune on your own reading.

HARD RULES: CLAUDE.md is binding — rules 1, 13, 14, 16, 21, 25, 27, 28, 31–36 especially. The parent never
solves (rule 32(a)). No new tuning channel; if a gate regresses, report it and root-cause it (rule 14),
never re-tune multipliers to recover it.
```

#### 5.3.7 R-PJM

```text
SESSION R-PJM — RE-SOLVE PJM 2019–2025 ON CORRECTED BACKCAST INPUTS (vintage EIA-860, plant heat rates, granular CAMPD outages)
DATA PROFILE: pjm
MODEL: Opus or Fable
PRECONDITION: F1 AND F2 (docs/handoffs/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md §5) are MERGED to
main. If either is not, STOP and report — do not solve on the old inputs.

READ FIRST: the audit doc (§1–§3, the PJM rows), the F1 and F2 PRs' census/coverage tables,
frontend/data/backcast/keepers/PJM.json, results/calibration/pjm_h19_dbs_span/run_config*.json (the
incumbent recipe), docs/codebase-site/data/mechanism-matrix/PJM.js + docs/mechanism-testing-matrix.md
§5 PJM lever queue (rule 28(a)).

OWNER INSTRUCTION (2026-09-24): every backcast year 2019–2025 runs on the year-correct EIA-860 vintage,
plant-specific heat rates (never the asset-class table), and granular CAMPD outage data.

INCUMBENT: 2026-09-23-pjm-h19-dbs-span (bundle results/calibration/pjm_h19_dbs_span, registered 2020–2025 (keeper 2023–25 + touchpoint 2020–22)).

PJM-SPECIFIC:
- EIA-860: the pjm-168 R on vintage tracking is RE-OPENED by the audit (the arm ran on 100 % class-table HR).
  With F1's default-on it is now simply on — REPORT the 2021 coal registry (expect ~48.7 GW) and the
  coal dispatch vs EIA-930/CEMS at full magnitude; if coal still runs to its rail with correct HRs, that
  is a finding about offers, not a reason to switch the vintage off (rules 1/14).
- Heat rates: keeper arms CT + CHP. ADD coal, ST, CC measured (F1). 13.4 GW of 2019 retirees were on class
  HR (§3b).
- Outages: std + short-coal + short-gas armed (short-gas began 2020 — F2 extends to 2019). ARM unit
  partial-derate — NOTE the plant-grain partial path over-fired PJM (~43 TWh/yr, DIAGNOSIS-pjm-c3c §7);
  the UNIT-grain family is a different detector — screen it on its own terms and report.
- Years: 2019–2025 in ONE keeper bundle (fold the touchpoint in; missing 2019).

PROCEDURE
0. Phase 0 (zero LP, in this session): enumerate the ISO's registered years (rule 34(c)/35(b)) and write
   them down; for each year 2019–2025 confirm benchmarks exist; run a fleet-only census per year showing
   (a) the EIA-860 vintage resolved, (b) thermal MW at a class-table heat rate (target: only plants absent
   from every eGRID vintage and CAMPD — list them), (c) outage windows/MW per family. G-DRIFT the keeper
   (rule 29(b)) — the F1/F2 hunks are LIVE by design; name them. Write the PRECOMMIT with the recipe
   (incumbent recipe + the arms above, offer-curve multipliers UNCHANGED — this is an input correction,
   rule 1(c): no re-tuning against the gates) and push it; pin its full 40-char SHA.
1. Solve: ONE SHARD PER YEAR, 2019…2025 (rule 36), launched via create_session with that SHA,
   own --out-dir results/calibration/<lane>_<year>/, own branch, full bundle pushed incl.
   dispatch/<year>_P1.parquet via the .gitignore negation + plain git add (rule 34(a)), the rule-32(c)
   launch checklist verbatim (hard stops, forbidden commands, "a shard that stops with a clear report is a
   SUCCESS; a shard that repairs infrastructure is a FAILURE", report container-preflight + memory-peak
   lines). Launch all years at once; do not ask permission.
2. Parent: fetch each leg, verify config signature (vintage resolved = solve year, measured-HR flags on,
   outage files + sha256), compose (zero LP), attest (DOF ledger; the multiplier block unchanged), score,
   register on the dashboard (rule 15), update the PJM matrix shard cells touched (rule 28(b)).
3. Archive every shard once its bytes are in hand (rule 33); land what must survive on main (rule 33(f)).
4. REPORT at full magnitude, per year, old keeper vs re-solve: C1–C8 table + determination, class TWh
   deltas, price MAE/bias, and the census deltas from step 0. Recommend promote / not — then ASK the owner
   the promotion question explicitly (rule 31); do NOT promote or prune on your own reading.

HARD RULES: CLAUDE.md is binding — rules 1, 13, 14, 16, 21, 25, 27, 28, 31–36 especially. The parent never
solves (rule 32(a)). No new tuning channel; if a gate regresses, report it and root-cause it (rule 14),
never re-tune multipliers to recover it.
```

#### 5.3.8 R-SOCO

```text
SESSION R-SOCO — RE-SOLVE SOCO 2019–2025 ON CORRECTED BACKCAST INPUTS (vintage EIA-860, plant heat rates, granular CAMPD outages)
DATA PROFILE: soco
MODEL: Opus or Fable
PRECONDITION: F1 AND F2 (docs/handoffs/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md §5) are MERGED to
main. If either is not, STOP and report — do not solve on the old inputs.

READ FIRST: the audit doc (§1–§3, the SOCO rows), the F1 and F2 PRs' census/coverage tables,
frontend/data/backcast/keepers/SOCO.json, results/calibration/soco61_dark_unit_span/run_config*.json (the
incumbent recipe), docs/codebase-site/data/mechanism-matrix/SOCO.js + docs/mechanism-testing-matrix.md
§5 SOCO lever queue (rule 28(a)).

OWNER INSTRUCTION (2026-09-24): every backcast year 2019–2025 runs on the year-correct EIA-860 vintage,
plant-specific heat rates (never the asset-class table), and granular CAMPD outage data.

INCUMBENT: 2026-09-24-soco61-dark-unit (bundle results/calibration/soco61_dark_unit_span, registered 2023–2025).

SOCO-SPECIFIC:
- EIA-860: SOCO's retiree channel returned ZERO rows every year (§3b) — F1 repairs; verify (Plant Hammond,
  Plant Gadsden, Barry 1–3, Gaston 1–4 conversions, …).
- Heat rates: keeper arms CT, coal, ST, CC, eGRID family — the most complete ISO. ADD CHP if the F1 artifact
  is non-empty.
- Outages: perunitdark extract was 2023–2025 only (raw CAMPD missing for AL/GA 2019–2022) — F2 extends.
  ARM short-coal, short-gas, partial-derate (U) where non-empty.
- Years: extend to 2019–2025 (missing 2019–2022). SOCO has no price benchmark; confirm the volume
  benchmarks (EIA-930 SOCO BA, EIA-923) exist for each year.

PROCEDURE
0. Phase 0 (zero LP, in this session): enumerate the ISO's registered years (rule 34(c)/35(b)) and write
   them down; for each year 2019–2025 confirm benchmarks exist; run a fleet-only census per year showing
   (a) the EIA-860 vintage resolved, (b) thermal MW at a class-table heat rate (target: only plants absent
   from every eGRID vintage and CAMPD — list them), (c) outage windows/MW per family. G-DRIFT the keeper
   (rule 29(b)) — the F1/F2 hunks are LIVE by design; name them. Write the PRECOMMIT with the recipe
   (incumbent recipe + the arms above, offer-curve multipliers UNCHANGED — this is an input correction,
   rule 1(c): no re-tuning against the gates) and push it; pin its full 40-char SHA.
1. Solve: ONE SHARD PER YEAR, 2019…2025 (rule 36), launched via create_session with that SHA,
   own --out-dir results/calibration/<lane>_<year>/, own branch, full bundle pushed incl.
   dispatch/<year>_P1.parquet via the .gitignore negation + plain git add (rule 34(a)), the rule-32(c)
   launch checklist verbatim (hard stops, forbidden commands, "a shard that stops with a clear report is a
   SUCCESS; a shard that repairs infrastructure is a FAILURE", report container-preflight + memory-peak
   lines). Launch all years at once; do not ask permission.
2. Parent: fetch each leg, verify config signature (vintage resolved = solve year, measured-HR flags on,
   outage files + sha256), compose (zero LP), attest (DOF ledger; the multiplier block unchanged), score,
   register on the dashboard (rule 15), update the SOCO matrix shard cells touched (rule 28(b)).
3. Archive every shard once its bytes are in hand (rule 33); land what must survive on main (rule 33(f)).
4. REPORT at full magnitude, per year, old keeper vs re-solve: C1–C8 table + determination, class TWh
   deltas, price MAE/bias, and the census deltas from step 0. Recommend promote / not — then ASK the owner
   the promotion question explicitly (rule 31); do NOT promote or prune on your own reading.

HARD RULES: CLAUDE.md is binding — rules 1, 13, 14, 16, 21, 25, 27, 28, 31–36 especially. The parent never
solves (rule 32(a)). No new tuning channel; if a gate regresses, report it and root-cause it (rule 14),
never re-tune multipliers to recover it.
```

#### 5.3.9 R-SPP

```text
SESSION R-SPP — RE-SOLVE SPP 2019–2025 ON CORRECTED BACKCAST INPUTS (vintage EIA-860, plant heat rates, granular CAMPD outages)
DATA PROFILE: spp
MODEL: Opus or Fable
PRECONDITION: F1 AND F2 (docs/handoffs/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md §5) are MERGED to
main. If either is not, STOP and report — do not solve on the old inputs.

READ FIRST: the audit doc (§1–§3, the SPP rows), the F1 and F2 PRs' census/coverage tables,
frontend/data/backcast/keepers/SPP.json, results/calibration/hydro5_spp_floor_span/run_config*.json (the
incumbent recipe), docs/codebase-site/data/mechanism-matrix/SPP.js + docs/mechanism-testing-matrix.md
§5 SPP lever queue (rule 28(a)).

OWNER INSTRUCTION (2026-09-24): every backcast year 2019–2025 runs on the year-correct EIA-860 vintage,
plant-specific heat rates (never the asset-class table), and granular CAMPD outage data.

INCUMBENT: 2026-09-22-hydro-5-spp-floor (bundle results/calibration/hydro5_spp_floor_span, registered 2019–2025 (keeper 2023–25 + rung 2019–22)).

SPP-SPECIFIC:
- The registered 2019–2022 rung (2026-09-22-hydro-5-spp-rung) was solved on 100 % class-table heat rates
  (D1) — it is invalid and is replaced by this re-solve.
- COORDINATE with SPP-78 (PRECOMMIT-spp-78-measured-heat-rates-2026-09-24.md, arming CC/ST/coal measured):
  if SPP-78 promoted, start from its recipe; if it is still open, subsume it (F1 flips those flags on by
  default anyway) and say so in the PRECOMMIT.
- Heat rates: ADD CT (+CHP if non-empty) — all measured classes on.
- Outages: std + short-coal armed. short-gas is R — read its evidence; re-open only if contaminated by D1
  (the rung years were), else leave. ARM unit partial-derate (U).
- Years: 2019–2025 in ONE keeper bundle (fold the rung in).

PROCEDURE
0. Phase 0 (zero LP, in this session): enumerate the ISO's registered years (rule 34(c)/35(b)) and write
   them down; for each year 2019–2025 confirm benchmarks exist; run a fleet-only census per year showing
   (a) the EIA-860 vintage resolved, (b) thermal MW at a class-table heat rate (target: only plants absent
   from every eGRID vintage and CAMPD — list them), (c) outage windows/MW per family. G-DRIFT the keeper
   (rule 29(b)) — the F1/F2 hunks are LIVE by design; name them. Write the PRECOMMIT with the recipe
   (incumbent recipe + the arms above, offer-curve multipliers UNCHANGED — this is an input correction,
   rule 1(c): no re-tuning against the gates) and push it; pin its full 40-char SHA.
1. Solve: ONE SHARD PER YEAR, 2019…2025 (rule 36), launched via create_session with that SHA,
   own --out-dir results/calibration/<lane>_<year>/, own branch, full bundle pushed incl.
   dispatch/<year>_P1.parquet via the .gitignore negation + plain git add (rule 34(a)), the rule-32(c)
   launch checklist verbatim (hard stops, forbidden commands, "a shard that stops with a clear report is a
   SUCCESS; a shard that repairs infrastructure is a FAILURE", report container-preflight + memory-peak
   lines). Launch all years at once; do not ask permission.
2. Parent: fetch each leg, verify config signature (vintage resolved = solve year, measured-HR flags on,
   outage files + sha256), compose (zero LP), attest (DOF ledger; the multiplier block unchanged), score,
   register on the dashboard (rule 15), update the SPP matrix shard cells touched (rule 28(b)).
3. Archive every shard once its bytes are in hand (rule 33); land what must survive on main (rule 33(f)).
4. REPORT at full magnitude, per year, old keeper vs re-solve: C1–C8 table + determination, class TWh
   deltas, price MAE/bias, and the census deltas from step 0. Recommend promote / not — then ASK the owner
   the promotion question explicitly (rule 31); do NOT promote or prune on your own reading.

HARD RULES: CLAUDE.md is binding — rules 1, 13, 14, 16, 21, 25, 27, 28, 31–36 especially. The parent never
solves (rule 32(a)). No new tuning channel; if a gate regresses, report it and root-cause it (rule 14),
never re-tune multipliers to recover it.
```

## 6. Reproducing the census

```bash
# thermal class-table share by EIA-860 source (audit §3a) — scratch script logic:
#   set_eia860_vintage(v); gens = load_fleet_from_csv(iso, year=v or 2025)
#   share = MW with heat_rate in HEAT_RATE_BINS values / thermal MW (coal, gas_cc, gas_ct, gas_st, oil)
# retiree class-table MW (audit §3b):
#   load_retired_within_window(iso, year=Y), units online in Y, same test
# keeper flags (audit §2): results/calibration/<bundle>/run_config*.json -> scenario_config.*,
#   resolved_inputs.campd_unit_outages.path
```
