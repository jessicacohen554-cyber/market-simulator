# PRECOMMIT — SPP-60: the SPP T1-H recipe + forecast data intake (owner ruling Q59)

**Lane:** SPP-60 · **Model:** Fable `claude-fable-5-1` · **Data profile:** spp (full clone, 185 raw subtrees) ·
**Branch:** `claude/spp-60-t1h-recipe-hindcast-x67gbz` (stem `claude/spp-60-t1h-recipe-w3pd`) ·
**Session date:** 2026-09-07 · **HEAD at write:** `9708d69e`.

**Discipline.** Written and pushed BEFORE the solve. §1 (the gap table) and §2 (the recipe) are
zero-LP; every number in them was read from committed artifacts or produced by a loader call
that builds no LP. Nothing in this lane is a mechanism test: no `ScenarioConfig` field is added or
moved, no offer band moves, no matrix cell is written (rule 28 not triggered), the backcast keeper
`2026-09-07-spp-3-screened-input` and every backcast surface are untouched.

**Preconditions, verified at HEAD.** SPP-43 LANDED — keeper-3 `2026-09-07-spp-3-screened-input`,
bundle `results/calibration/spp43_screened_B` (`run_config.json` `git_sha` **`623184f3`**). SPP-45
LANDED — the board row `frontend/data/forecast/program-status.json::isos.SPP.gate.a_keeper_marker`
already cites keeper-3 ("RE-KEYED 2026-09-07 BY THE SPP GATE-(a) RE-KEY LANE … at origin/main
32516df6", PR #5548). Its legs (b)/(c) still read "NO FORECAST EVIDENCE OF ANY KIND EXISTS FOR SPP" —
the two cells this lane fills, from measured results only, after §3.

**Rule 12 (ask the desk before solving).** No other solve is running in this container (verified:
`ps`, 15 GB RAM / 4 cores, 13 GB free at launch). The desk is not reachable synchronously from an
autonomous session; the charter's own memory-class line (per_plant, ~5.3 GB/yr) is the budget, one
invocation, years sequential, and the launch is recorded here before it happens (§2.5). If the desk
had another SPP per-plant solve in flight on THIS host it would have to be this container, and there
is none.

---

## 1. THE GAP TABLE — every input a T1-H hindcast reads, for SPP

Walked from the MISO T1-H recipe (`PREDECL-/FINDING-capx-d27-miso-t1h-remeasure-2026-09-01.md`),
`scripts/run_capacity_hindcast.py::build_config`, the runner's hindcast year loop and CLAUDE.md's
capacity-evolution steps 0–7. Status vocabulary: **EXISTS** (cited) / **PLACEHOLDER** (registered by
SPP-20, empty) / **MISSING**. Every row carries the rule-13 `[R-MEASURED]` test — *could the same
quantity be produced for a forward year from forward drivers, and would it respond to changed
conditions?*

### 1.1 Dispatch-side inputs (what the four solved years read)

| # | Input | Status | Evidence (zero-LP) | Rule 13 |
|---|---|---|---|---|
| D1 | EIA-860 **2020-vintage** fleet basis (`eia860_vintage_year=2020`) | **EXISTS** | `data/raw/eia-860/vintage_2020/`: plant sheet maps **687 plants** to BA `SWPP`; operable sheet **1,527 generator rows / 91,097 MW**; proposed sheet **62 rows / 9,589 MW** (2023 vintage: 739 / 1,576 rows / 99,366 MW; current: 828 / 1,646 / 103,331). `BA_CODE_TO_ISO["SWPP"] == "SPP"` (`data/zone_assignment.py:80`) | a dated registry snapshot; regenerates per vintage |
| D2 | **Measured hourly zonal demand** for the solved years 2021 / 2023 / 2024 / 2025 (`runner._hindcast_measured_demand` → `eia930.demand.load_demand`) | **EXISTS** | `data/raw/zone-specific-demand/SPP/spp_subba_demand_{2019,2020,2021,2022,2023-2025}.csv` (SPP-11 + SPP-15). Loaded at HEAD with the resolved config: 2021 **269.65 TWh / peak 51,380 MW**; 2023 284.52 / 54,589 (one metering-spike hour repaired by the SPP-41 screen); 2024 290.89 / 53,914; 2025 301.84 / 57,227. Two zones, 8760 h each. Interchange folded (no import node, owner ruling P2) — the EIA-930 SWPP schedule is 2019–2025 (SPP-15 byte-identity widening) | the realized year's metered profile — a physical input the LP takes, never a target (plan §1.3) |
| D3 | **Renewable CF profiles** — the harness reads the weather year, `ScenarioConfig().weather_year = 2024`, for every solved year (`crossover_solve_year_weather=False`) | **EXISTS** for 2024 | `data/raw/spp-wind-shape/spp_{2023,2024,2025}_wind_zone_shape.parquet` (SPP-30) + EIA-930 `SWPP_fueltype.parquet` (2015-01 → 2026, complete). `load_renewable_profiles("SPP", 2024)`: wind CF mean **0.361 / 0.359** (N/S), solar 0.19 / 0.19. **Disclosed limitation:** no 2021 wind shape exists — `load_renewable_profiles("SPP", 2021)` returns the flat `RENEWABLE_AVG_CF` 0.36 in both zones — but the harness never reads 2021 weather (every ISO's T1-H runs on weather 2024), so it is inert here; it would bite a `--crossover-solve-year-weather` / full-forward arm, which this lane does not run | a weather-year resource shape; regenerates from any weather year |
| D4 | **Realized fuel** — `gas_price_path="hindcast_realized"` (annual Henry Hub spot, `fuel_trajectories.py:180`) × SPP basis | **EXISTS** | `GAS_BASIS_DIFFERENTIAL["SPP"] = −0.26` (SOM 2025 Panhandle restatement, `fuel_trajectories.py:377`), `COAL_PRICE_BASE["SPP"] = 1.8` (EIA-923 SWPP plant-weighted 2023–25 mean, line 446). The per-plant EIA-923 monthly overlay and the OK/KS/TX/NM delivered-gas series are **backcast overlays** and are NOT read in `mode="forecast"` (the harness asserts no backcast-gated loader is consulted) | published annual fuel series + a measured basis; regenerates from any fuel path |
| D5 | **Outages** — statistical `EFORD` by class (`constants.py:2559`), forecast mode | **EXISTS** | not ISO-keyed; the CAMPD historic windows of the backcast keeper are an overlay and are not read | NERC GADS class rates; forward by construction |
| D6 | **Hydro** — normal-water-year EIA-923 climatology | **EXISTS** | `complete_923_hydro_years("SPP") == (2021, 2022, 2023, 2024)` — the coverage gate excludes preliminary 2025 (the SPP-42 R-8 object: 0.0233 TWh / 1 plant); `hydro_year="normal"`. The keeper's `--hydro-backfill-year 2024 --hydro-eia930-monthly` pair is a **backcast** vintage repair (run_calibration_full's, not the harness's) and is not part of the forecast recipe | a climatology that regenerates as 923 finals land |
| D7 | **Topology** — 2 zones, N↔S link **3,400 MW** (SPP-53), no import node, scalar EIA-930 interchange, three default-off neighbour blocks | **EXISTS** | `iso_configs._spp_config` (keeper-3's own topology, byte-identical) | structural |
| D8 | **Fleet representation** — `use_campd_bins=True` (per-plant tranches), neutral offer bands (`offer_curve_by_group == {}` in the resolved config; the backcast `_SPP_OFFER_CURVE` identity 1.0 is a `pipeline/backcast_config.py` object the harness never applies) | **EXISTS** | resolved config, §2.1; rule 25 `[R-ISO-SCOPE]` intact — SPP carries no fitted band anywhere | structural |
| D9 | **Scarcity footing** in the hindcast — `scarcity_pricing_enabled=True` engages each ISO's `default_scenario_overrides`; SPP has **none** (`{}`, P4/P5 deferred to SPP-56/SPP-55), `scarcity_price_overlay=False`, `energy_reserve_coopt=False` | **EXISTS as a declared absence** | the screens therefore see bare perfect-foresight LP duals — the ERCOT `s2` defect class `build_config`'s docstring names, and exactly what keeper-3's C3a/C3c FAILs already say about SPP prices. **Stated at the gate, not repaired here**: SPP-55 (VRL/scarcity) and SPP-56 (reserve co-opt) own it; this lane arms nothing | — |

### 1.2 Capacity-evolution inputs (steps 0–7, CLAUDE.md "Capacity Evolution")

| Step | Input / gate | Status | Evidence (zero-LP) | Rule 13 |
|---|---|---|---|---|
| 0 confirmed exits | `confirmed_exits_enabled=True`; `data/raw/confirmed-retirements/spp.csv` → clean partition | **PLACEHOLDER → FILLED (forward rows), INERT for T1-H** | SPP-20 registered `scripts/lib/confirmed_retirements/spp.py` with no CSV; `curate_confirmed_retirements.py` `[skip]`s SPP, so the loader's `_registry_curated()` branch returns the warn-only empty list (the datatype root exists) — no refusal, no exits. **This lane lands `spp.csv` (§1.4)**: Tolk 1 + 2 (SWEPCO/SPS, EIA 6194, 2 × 567.9 MW), `regulatory_order` NMPRC Case **22-00286-UT** final order **2023-10-19** (retire by end-2028), deferred to **2029-03-31** by the NMPRC's 2026-05-07 approval of SPS's 2025 NM IRP. Both instruments post-date the 2020 information cutoff (`IS2020_CUTOFF`, `instrument_date <= vintage`), so **step 0 applies nothing in a 2020-vintage hindcast by the gate's own rule**, and the rows are live only in forecast / 2023-vintage runs. Candidates evaluated and NOT rows: North Omaha 4/5 (OPPD board resolution Dec-2025 *defers* coal past 2028 with no binding date — announced-stage, reversible); Lawrence 4/5 (Evergy IRP filings only — an IRP is not an instrument); Northeastern 3 (PSO, 2026 — 860-dated, no OCC order located); Pirkey (SWEPCO, 721 MW) and Horseshoe Lake ST6/ST7 (OG&E) — real in-window exits that the **860 owner-filed dates already carry (step 1b)**, so a confirmed row would decide the same exit twice (rule 19) | an enforceable dated instrument; regenerates at each intake vintage |
| 1 announced (860 dates) + 1b fossil owner-filed dates, reversal registry | `fossil_announced_exits_enabled=True`, `hindcast_verified_announced_exits=True` (harness default) | **EXISTS** | 2020-vintage operable sheet, SWPP, `Planned Retirement Year` in 2021–2025: **17 rows / 2,226.7 MW** — 2021 LFG 2 MW; 2022 NG 335; 2023 **LIG 721 (Pirkey)** + NG 568; 2024 NG 188; 2025 NG 414. Reversal registry = the same (empty) SPP partition → nothing suppressed; under `hindcast_verified_announced_exits` later vintages (2021–2024 on disk) re-verify each date | the owner's own filed plan at the vintage; regenerates from the then-current 860 |
| 2 CCS retrofit | `ccs_retrofit_available_year=2028` | inert (window ≤ 2025) | by construction | — |
| 3 economic retirement | `retirement_rule="pipeline"`, per-fuel lags, FOM registry, `screen_reserve_value_enabled=True`, reliability floor on `PLANNING_RESERVE_MARGIN_BY_ISO["SPP"] = 0.16` (SPP Planning Criteria, manifest row 12), `ADEQUACY_EXTERNAL_TIE_FIRM_MW["SPP"] = 0.0`, `capacity_screen_peak_measured_hindcast=True` (Q58, every ISO — the screen peak IS the D2 measured array), `retirement_sector_gate=False` (MISO/PJM arms only), no capacity market (SPP absent from `MARKET_DESIGN` → `capacity_price_firm` 0 $/MW-yr) | **EXISTS** | readiness walk `capacity_market_clearing: OK — clearing=False; planning_reserve_margin=0.16`. Reserve-value leg: with no co-opt and no ORDC overlay the screen's reserve signal is the LP's own (see D9) | shipped structure; nothing SPP-specific tuned |
| 4 known additions | `load_planned_additions("SPP", vintage_2020)` | **EXISTS** | loader runs on SPP (BA map + lat/lon zone assignment): **2 thermal rows** from the 2020 proposed sheet with 2021 effective years (wind/solar/storage additions ride the zonal pools and the storage screen, never this loader) | the 860 proposed pipeline at the vintage |
| 5 economic entry | ATB2024 (7 techs), `QUEUE_CAP_PER_TECH_GW["SPP"]` wind 3.5 / solar 1.0 / gas_cc 1.0 / gas_ct 1.5 / nuclear 0.5 / geo 0 / OSW 0 GW·yr⁻¹ (SPP-30, measured 2021–25 COD peaks), `QUEUE_CAP_GW["SPP"] = 4.5`, storage base 340/450/520 MW, ceiling 28,000, annual cap 500 MW, `entry_rate_limits` + `entry_commissioning_lag` True, `entry_vre_capacity_revenue=False` (MISO-only default), `renewable_elcc_curves=True`, IRA windows (OBBBA cliff 2027) | **EXISTS** | readiness walk: `atb_entry_costs OK (7 techs, ATB2024)`; `capacity_price_firm NA` (0.0 — energy-only); `ira_* INFO` | published costs, caps measured from the ISO's own COD record |
| 5′ **RPS floor** (`STATE_RPS_FLOORS["SPP"]`) | **PLACEHOLDER (declared 0.0)** | `capacity_market.py:4942`: the row is `{2026: 0.0, …}` with the derivation named — a load-weighted SPP-wide blend of the two real IOU mandates (MO Prop C 15 % by 2021, RSMo §393.1030; NM ETA 2019 SB 489 50 % by 2030 / 80 % by 2040, SPS as an NM IOU) — "a cited derivation the capx director charters with card P8 (SPP-60)". **Zero-LP arithmetic on why it is inert for T1-H**: SPP's load-weighted share of those two mandates is ≤ ~3 % of SPP load over 2021–2025 (MO-SPP + SPS-NM retail ≈ 10–12 % of SPP energy × 15–40 % mandates), against a measured SPP wind+solar energy share of **≈ 38–41 %** (D3 caps × CF over D2 load) — the constraint cannot bind in any solved year, so the hindcast is byte-identical with or without it. **Not edited in this lane**: `STATE_RPS_FLOORS` sits in `capacity_market`, one of the seven `solve_surface.SURFACE_MODULES`, and an SPP-projected value change is exactly what the capx D79 surface fingerprint exists to catch — it may move SPP's *backcast keeper* key, which this charter forbids touching. Routed to the desk as an adjudication (§4 R-2) with the derivation sketched; a forward run that needs it lands it as its own PRECOMMIT with a key-move census | a published mandate; regenerates per statute vintage |
| 6 reserve-margin backstop | `reserve_margin_build_enabled=None` → `resolve_reserve_margin_build_enabled` | **OFF by market design** | SPP is absent from `MARKET_DESIGN` ⇒ `DEFAULT_MARKET_DESIGN` (energy-only, bilateral RA) ⇒ backstop OFF, the ERCOT branch (`adequacy.py:805`). Consequence stated up front: an under-build leaves through load slack (I3), never a force-build | — |
| 7 RPS as LP constraint | floor 0.0 → no row | inert (see 5′) | readiness walk `rps_target NA` | — |

### 1.3 Scoring, registration and forward-only inputs

| # | Input | Status | Evidence / action | Rule 13 |
|---|---|---|---|---|
| S1 | **Scoring target** `data/raw/_validation-source/capacity_actuals_spp.csv` (FC-3 reads `score.json`, which `score_capacity_hindcast.py` computes against this file) | **MISSING → BUILT this lane** | `scripts/data/build_capacity_actuals.py --iso SPP` (BA `SWPP`, fleet vintage 2020, physical-cessation dating across releases 2018–2025): **110 retirements / 2.2 GW** (coal 0.72 — Pirkey 1, 721 MW, 2023; gas_st 1.01 — incl. Horseshoe Lake ST7 220 + 6 163 MW, 2024; gas_ct 0.17; oil 0.08; wind 0.16; biomass 0.01) and **185 additions / 13.9 GW** (wind 10.96, gas_ct 1.44, solar 1.04, storage 0.43). A registry-outcome validation target only (rule 13 benchmark branch); never read by a solve. **The thermal window is small (≈ 2.0 GW) so the ±10 % total band is ±0.2 GW** — reported as the band's own property, not softened | benchmark branch |
| S2 | Registration path | **EXISTS** | `scripts/register_forecast_run.py --bundle <out-dir>` → `frontend/data/hindcast/<run_id>.json`; verdict via `scripts/forecast_verdict.py --tier t1h --hindcast-score … --run-config …` written into `frontend/data/forecast/ff-verdicts.json` under a NEW key, and the `run_id → key` line added to `VERDICT_MAP` (`register_forecast_run.py`, ≥300 lines → Edit + `git push` + blob verify, rule 27). `--reindex` locally proves the row renders; the generated namespace is never committed (rule 15, forecast paragraph) | — |
| F1 | **Load forecast** (manifest rows 11/13; plan §7 G12) | **EXISTS** — and the census found a newer vintage | `scripts/lib/load_forecast/spp.py` registers edition **`2025 ITP`, vintage 2025** (4 Base-Reliability study years 61.7 / 66.5 / 69.8 / 76.4 GW for 2026 / 2029 / 2034 / 2044, `data/raw/load-forecast/spp/spp.csv`, SPP-12) — G12 is MET at HEAD; `DEMAND_GROWTH_RATES["SPP"]` near 0.019095 / long 0.009206 derive from it. **Edition census (this lane, 2026-09-07):** SPP publishes no standalone LTLF; the next vintage is the **2026 ITP** load forecast, whose scoping previews read **Future 1 ≈ 91 GW and Future 2 ≈ 110 GW by 2035** (≈ 30 GW of surveyed "spot" large loads vs 11 GW in the 2025 cycle) — a step change against the 2025 ITP's 69.8 GW for 2034. The 2026 ITP Assessment Report is not published (SPP issues it ~Nov; the 2025 report is dated 2025-11-25); the scope document (`2026 itp & cpp transition assessment scope_v1.6.pdf`, fetched here, 64 pp) is being read for a printed futures table — outcome in the FINDING. Rule 23: the registered vintage re-derives only on that source landing, never on a residual. **Inert for T1-H** (realized demand, D2); a forward-only object | forward-looking published input |
| F2 | Nuclear licence status | **EXISTS** (SPP-12; Wolf Creek 2045-03-11 `announced_intent`, Cooper **2034-01-18** `under_review`) | not consumed by any ISO's solve path (`ff-g5-nuclear-registry-2026-07.md`); carried forward as the standing R-g caveat on any SPP forecast horizon ≥ 2034 | instrument registry |
| F3 | Transmission expansion (`transmission-expansion/spp.csv`) | **PLACEHOLDER — MANUAL MANIFEST ROW** | spec registered (SPP-20/35), no rows. Source located in the committed transcription (`2025_ITP_Report_v1.0.txt`): the **765 kV overlay Woodward – Viola – Anthem – Seminole – Minco – Crawfish Draw** (+ Seminole – SW Shreveport; Table 6.14, §7 "765 kV Transmission Overlay – Phase 1", p. 172 ff.), of which "the Board approved a portion" (§8.4). Viola is a named constituent of the SPP-53 corridor, so this is the one project family that maps to the `link` row. **Inert for T1-H** (in-service ≥ 2029) and NOT curated here: a `link` row needs a `delta_mw` reconciled against the 3,400 MW ψ-based base (FINDING-spp-53 §6 O-4 — a rule-14 reconciliation, not a transcription), which is the SPP-53 construction's to extend. Manifest row: "2025 ITP 765 kV overlay → `link` delta, reconciled through ψ; owner: SPP-53 successor" | a Board-approved dated portfolio; regenerates per ITP vintage |
| F4 | Demand growth / DC / electrification (forward years only) | **EXISTS**, with one declared thinness | readiness walk: `demand_growth_rate PLATEAU` (held flat from 2031 — the 2025 ITP's last knot is 2044, so the hold is the F1 interpolation rule's flat tail read through the near/long CAGR pair); `datacenter_block_mw NA` (0.0 — `DATACENTER_ADDITIONS_MW["SPP"] = {}` by design, the ITP's spot loads are folded into its peak); `ELECTRIFICATION_LAYERS["SPP"]` empty. `DEMAND_GROWTH_RATES_VINTAGES` (2021 / 2023 vintages) has **no SPP entry**, so `--fuel-variant asknown` / `demand_growth_vintage` is **impossible for SPP** at HEAD (`scenario_resolvers.py:146` raises) — realized is the only T1-H variant, declared. None of this is read by a realized hindcast year | forward drivers |
| F5 | Fuel trajectories (forward AEO paths) | **EXISTS** | readiness walk: gas / coal / oil OK 2026–2050 | published series |
| F6 | `GOLDEN_ISOS` (`ff_readiness_battery.py:102`) | six ISOs; **not edited** (charter) | the battery's `resolve` / `config` parts accept `--iso SPP` and were run (§1.5); `GOLDEN_ISOS` membership is the capx director's call and is reported, never asserted | — |

### 1.4 Intake landed by this lane (raw immutable; rule 22 — data intake needs no authorization)

1. `data/raw/_validation-source/capacity_actuals_spp.csv` — S1 above (a derived scoring target from committed EIA-860 releases; the builder is unchanged).
2. `data/raw/confirmed-retirements/spp.csv` — Tolk 1 / 2 (step 0 row above), + README table row for SPP (binding instrument classes: state commission orders — NMPRC / OCC / KCC / MPSC / NPSC / PUCT — consent decrees, statutes; SPP runs no deactivation process) and the candidate-evaluation record. Re-curated into `data/clean/confirmed-retirements/SPP` in-session; **applies nothing in the 2020-vintage T1-H by the information gate** (verified in the bundle's `evolution_*.json` after the solve — the FINDING reports the confirmed channel's row count per year, expected 0).
3. `docs/handoffs/PRECOMMIT-spp-60-2026-09-07.md` (this file) — the manual manifest rows: F3 (765 kV overlay `link` delta, reconciled), 5′ (RPS blend), F1 (2026 ITP vintage when the report lands).

### 1.5 Readiness battery (parts a + b, zero-LP, `--iso SPP`) — reported, GOLDEN_ISOS untouched

`resolve` (input-resolution walk, 20 rows): **no HARD FAIL**. Rows: `demand_growth_rate PLATEAU`
(hold-flat from 2031), `gas/coal/oil OK`, `atb_entry_costs OK`, `capacity_market_clearing OK`
(clearing=False, PRM 0.16), `weather_year_pool OK` (2024 ∈ {2023, 2024, 2025}),
`confirmed_retirements MISSING` at walk time — the clean partition was unbuilt (the walk ran before
`regenerate_clean.py` finished; re-run after curation is reported in the FINDING), `datacenter /
carbon / ces / rps_target / capacity_price_firm NA` (inactive for this ISO/posture), `ira_* INFO`.
`config` (completeness): **green** — `cache_key_stable_round_trip` `fee0b1058ee93f08`,
`run_config_full_surface` 822 fields, posture checks all OK (`capacity_market_clearing want=False
got=False`). Parts c (kill-resume, a T0 solve) and d (wall/RSS projection) are run after the T1-H
and reported in the FINDING. **Verdict form the desk carries to the capx director:** "SPP resolves
green on parts a/b with one PLATEAU (the forecast tail) and no hard fail; whether that admits SPP to
`GOLDEN_ISOS` is the director's decision under §2.1b(c), not this lane's."

---

## 2. THE RECIPE

### 2.1 The invocation (declared; bare at HEAD, the D4-M / FFR-3A-3 / D27 form with `--iso` swapped)

```
uv run python scripts/run_capacity_hindcast.py \
  --iso SPP --start-year 2021 --end-year 2025 \
  --vintage 2020 --fuel-variant realized \
  --out-dir results/hindcast/spp-2021-2025-realized-t1h-spp60
```

Every solve-affecting flag omitted → each inherits its shipped default, then
`apply_iso_scenario_defaults(config, "SPP")`, whose SPP override set is **`{}`**. Solve years
`{2021, 2023, 2024, 2025}`, **2022 bridged** (evolved, never solved), scored 2023–2025. No
out-of-training backcast year is solved or scored; the holdout freeze is untouched; nothing reads
H1-2026 (rule 22; plan §2.3).

**Resolved HEAD posture (read BEFORE the solve, no LP; `build_config(...)` +
`apply_iso_scenario_defaults`):** cache key **`e586d7cae19eab13`**.

| field | resolved | note |
|---|---|---|
| `mode` / `hindcast` / `eia860_vintage_year` | forecast / True / 2020 | |
| `hindcast_fuel_variant` / `gas_price_path` | realized / `hindcast_realized` | the only variant possible for SPP (F4) |
| `weather_year` / `crossover_solve_year_weather` | **2024** / False | harness default; renewables from 2024 for every year (D3) |
| `use_campd_bins` | **True** | per-plant tranches — the memory class the charter names (per_plant); SPP is 2 zones, so ≪ the 5.3 GB/yr of a 6–8-zone ISO — priced at ≤ 3 GB/yr from keeper-3 (P0 ≈ 60–110 s, P1 ≈ 25–35 s per year) |
| `scarcity_pricing_enabled` / `scarcity_price_overlay` / `energy_reserve_coopt` | True / False / False | no SPP footing (D9) |
| `retirement_rule` | pipeline | |
| `entry_lookahead_reprice` / `correlated_forced_outage` / `entry_rate_limits` / `entry_commissioning_lag` | True / True / True / True | the FFR-3A-3 §1.3 quartet |
| `exit_rate_limits` | False | FFR-3F D-8 present, unarmed |
| `capacity_screen_unified_lookahead` / `_scarcity_restoration` / `entry_pipeline_aware_signal` / `entry_margin_exhaustion` / `entry_forward_reserve_leg` / `entry_forward_expectation_signal` | all False | |
| `storage_entry_availability_gate` / `storage_entry_cost_normalized_rank` | True / True | owner R-A |
| `hindcast_verified_announced_exits` / `fossil_announced_exits_enabled` / `confirmed_exits_enabled` / `forecast_fossil_retirement_economic` | True / True / True / True | |
| `entry_vre_capacity_revenue` | **False** | MISO ISO default only |
| `capacity_market_clearing_by_iso` | {PJM, MISO, CAISO, NEISO: True} — **SPP absent** | energy-only; `capacity_market_supply_clearing_by_iso` None |
| `screen_reserve_value_enabled` / `reserve_margin_build_enabled` | True / None ⇒ **OFF** (no capacity market) | step 6 |
| `capacity_screen_peak_measured_hindcast` | True | Q58 |
| `capacity_deliverability_limits` / `retirement_sector_gate` / `pjm_*` / `nyiso_*` / `neiso_*` | off / False | other ISOs' arms |
| `ccs_retrofit_capex_co2_scaling` | True | inert < 2028 |
| `renewable_elcc_curves` / `planning_reserve_margin` (generic field) | True / 0.1375 | the registry value 0.16 is what the SPP screen reads |
| `coal_prb_passthrough_sigmoid` / `_tiered` / `coal_plant_monthly_pricing` / `temp_dependent_derate` | False / False / True / False | the keeper's sigmoid + tiered flags are `run_calibration_full` calibration flags, not `ScenarioConfig` forecast defaults |
| `spp_gas_commitment_bridge` (SPP-44) / `ercot_zonal_spread_ep_referenced` | False / False | both default-off, cache-key drop declared (§2.3) |
| `offer_curve_by_group` | `{}` | neutral bands (rule 25) |
| `demand_growth_rate` / `datacenter_load_path` / `electrification_path` | 0.01 / off / off | never read by a realized year |

**What "keeper-3's recipe in forecast mode" means, exactly.** The harness does not call
`pipeline/backcast_config.py`, so the keeper's *calibration overlays* — `outage_source=historic`
(CAMPD windows), the EIA-923 plant-monthly fuel overlay, the weather pin to the solve year, the coal
PRB sigmoid / tiered passthrough flags, `--hydro-backfill-year 2024 --hydro-eia930-monthly`, the SPP-41
screened-loader seam on 2023 wind — are **dropped by construction** (rule 13: they are backcast-only
inputs). What carries is the keeper's **structure**: the two-zone topology and 3,400 MW corridor,
no import node and the scalar interchange, the per-plant CAMPD-bin fleet representation, the neutral
offer surface, the measured demand (the same EIA-930 sub-BA loader), and every registry value SPP-20
through SPP-53 landed. That is the forecast-lane definition of "same config" for every other ISO's
T1-H, applied unchanged.

### 2.2 The crossover window (2024–H1 2026), declared and NOT solved in this lane

The charter names the crossover window as part of the recipe. The instrument that solves it is
`run_capacity_hindcast.py --crossover --vintage 2023 --start-year 2023 --end-year 2027` (plan §2.2,
T1-X): 2023–2025 on realized inputs, 2026–2027 on pure forward drivers, scored 2023–2025 only, the
scorer structurally refusing any year ≥ 2026 — which is how "no measured H1-2026 actuals" is
enforced. For SPP it would resolve identically to §2.1 except `eia860_vintage_year=2023`,
`crossover_forward_year=2026`, `weather_year=2025`. **It is a second 5-year invocation the charter's
item (2) does not name** ("THE HINDCAST SOLVE" — T1-H), so it is declared here as the *recipe* and
left for a T1-X lane; nothing about SPP's forward years is scored or claimed in this session.

### 2.3 G-DRIFT vs keeper-3 (`623184f3` → HEAD `9708d69e`), the solve path

`git diff --stat 623184f3 HEAD -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`
→ 13 files, +538 / −1, from exactly **two commits**:

| commit | hunks | classification |
|---|---|---|
| `19e1c867` SPP-44 `spp_gas_commitment_bridge` | `scenarios.py` (+field, default `False`, `_CACHE_KEY_OPTIONAL_FIELDS` + frozen default), `constants.py` (+33, measured plant-basis constants), `floor_mechanisms.py` (D-2 id), `pipeline/commitment.py` (+174, the bridge), `pipeline/year.py` / `runner.py` (wiring), `run_calibration*.py` (CLI flags), `solve_surface_declared.py` (+2) | **INERT** — a `ScenarioConfig` flag that is **default-off AND absent from this recipe** (resolved `False`, §2.1) with its cache-key drop value declared; SPP-44's own screen was KILLED (log spp-7). The `commitment.py` seam runs only when the flag is on |
| `7f8dcbc6` ERCOT zonal gas spread EP-referenced | `data/fuel/basis/ercot.py` (+118), `data/fuel/__init__.py`, `basis/__init__.py`, `scenarios.py` (`ercot_zonal_spread_ep_referenced`, default `False`) | **INERT** — another ISO's branch (ERCOT basis), default-off |

**All hunks INERT ⇒ keeper-3's structure at HEAD is the structure that solved keeper-3.** Note what
G-DRIFT is and is not here: the T1-H is a *different mode* from the keeper, so the keeper's committed
numbers are not a control for it (there is nothing to difference) — the audit establishes only that
no solve-path change since the keeper's sha could make "keeper-3's recipe" mean something else.

### 2.4 Cache-key freshness (the D17 R1 guard (a), discharged before launch)

`run_capacity_hindcast.py` sets `cachemod.CACHE_ROOT = args.out_dir`, so a fresh, empty
`--out-dir` cannot serve any pre-existing bundle at any key; the out-dir is verified absent before
launch. The realized key is recorded in the FINDING; a key ≠ `e586d7cae19eab13` is itself a
reportable finding (pre-solve and solve-time resolution disagreeing).

### 2.5 Budget, ordering, retention

* `data/clean` (plan §2.4 prerequisite) is being built in this container (`regenerate_clean.py`,
  ~55 min, started before this file was written); the SPP confirmed-retirements partition is
  re-curated after §1.4 item 2 lands and before launch.
* One invocation, four LP years sequential (rule 12), priced ≤ ~15 min wall / ≤ 3 GB RSS from
  keeper-3's per-year timings (P0 47.8–113.2 s, P1 24.7–33.6 s) plus the screens. No control arm
  (rule 29(b)): there is no incumbent T1-H for SPP, so the first measurement is the record.
* **Rule 31 `[R-RETAIN]`:** the bundle stays on local disk until the owner rules; the committed set
  is the slim record every other T1-H commits (`meta.json`, `run_config.json`,
  `<ISO>/<key>/score.json`, `evolution_*.json` — ~3 MB for MISO) — the parquet hourlies are
  gitignored under the `results/hindcast` scratch family and are never pushed.

---

## 3. PREDICTIONS (graded at full magnitude in the FINDING, misses included)

Stated so the result cannot be narrated afterwards. Basis: the S1 target, the step-1 census and
D9.

* **P1 — the retirement channel is dominated by the 860 dates, not the economic screen.** The
  2020-vintage owner-filed dates (2,226.7 MW in-window, incl. Pirkey 721 MW LIG 2023) reproduce
  most of the target's 2.2 GW; the confirmed channel applies **exactly 0 rows** (information gate).
  Falsifier: any `confirmed` row in `evolution_*.json`.
* **P2 — `retire.total_gw` reads OUT of the ±10 % band, on the OVER side.** The screen sees bare
  LP duals with no scarcity footing (D9) and SPP prices already read low in the keeper (C3a FAIL);
  with no capacity market and a $0 capacity leg, gas steam / oil / small CT units sit below the
  going-forward bar. Central: model thermal retirements **3–8 GW** against ~2.0 GW actual
  (+50 % to +300 %). Explicit alternative (~25 %): the reliability floor at PRM 0.16 on the
  measured peak retains them and the total lands **inside** ±0.2 GW — recorded as a magnitude MISS
  if so. Either way `unit_recall_gt300` is decided by ≤ 3 large units (Pirkey; Horseshoe Lake is
  < 300 MW), so it is reported and named as a small-N statistic.
* **P3 — additions: wind lands inside ±15 % or under; solar and storage read FAIL.** Wind
  10.96 GW actual vs `QUEUE_CAP_PER_TECH_GW` 3.5 GW·yr⁻¹ × 4 solved years = 14 GW ceiling — the
  cap does not bind, so the entry screen's own economics decide; solar (1.04 GW actual) and storage
  (0.43 GW) are small enough that a single screened block breaks the band. Tech-mix shares Δ > 5 pp
  on at least one of {gas_cc, storage}.
* **P4 — the verdict rows:** FC-3 **FAIL** (P2/P3); FC-7 `run_config` PASS, `overlay-off` PASS
  (`outage_source` statistical), `dof ledger` CAVEAT (no DOF ledger — the same row every bare T1-H
  carries); FC-1 / FC-8 SKIPPED (no invariant record / no perf ledger in a hindcast summary);
  FC-2/4/5/6 n/a. **Determination: HOLD** — the same reading every ISO's bare T1-H has at HEAD.
  This is what the legs (b)/(c) of the SPP board row will say, at full magnitude.
* **P5 — no verdict outside the new SPP key moves**; the ff-verdicts edit is a pure insertion of
  one key; `program-status.json` moves only `isos.SPP` legs (b)/(c) + `fc` + `tier_reached`.

---

## 4. Routed adjudications (owner + desk), stated before the result

| # | Object | Owner | Why it is not this lane's |
|---|---|---|---|
| R-1 | `GOLDEN_ISOS` membership for SPP | capx director (§2.1b(c)) | charter: report the battery, never assert |
| R-2 | `STATE_RPS_FLOORS["SPP"]` blend (MO Prop C + NM ETA, load-weighted) | SPP desk → a forward lane with a solve-surface key census | may re-key the backcast keeper via the D79 surface; inert for T1-H by arithmetic (§1.2 5′) |
| R-3 | 765 kV overlay `link` row reconciled through ψ | SPP-53 successor | rule-14 reconciliation against the 3,400 MW base, not a transcription; inert < 2029 |
| R-4 | 2026 ITP load-forecast vintage (Future 1 / Future 2) | load-forecast intake on report publication | rule 23: re-derive on the source, the report is unpublished; scope-doc read reported in the FINDING |
| R-5 | SPP scarcity footing for the screens (the D9 absence) | SPP-55 / SPP-56 | a structural object; arming it here would be a mechanism test on a hindcast, which rule 29 sends to a screen first |
| R-6 | Cooper 2034 / Wolf Creek 2045 (R-g) | any SPP forecast horizon ≥ 2034 | not reached by T1-H (≤ 2025) |
