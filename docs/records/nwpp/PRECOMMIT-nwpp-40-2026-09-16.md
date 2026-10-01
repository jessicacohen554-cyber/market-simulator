# PRECOMMIT — NWPP-40: the first-ever NWPP solve and the first NWPP keeper (owner ruling N10-R: NO SCREEN)

Lane **NWPP-40** · model Fable · `DATA PROFILE: nwpp` · branch `claude/kind-keller-p4a1k0`
(the harness assigned this session's branch; the charter's stem `claude/nwpp-40-first-keeper-<4>`
is recorded here as the intended name and nothing else keys on it) · zero LP in this session
(rule 32 `[R-SHARD]` (a) — the solve is ONE shard, launched only after this file is pushed).

Charter: `docs/multi-iso/nwpp-addition-plan-2026-09.md` §8 W4 (issued r#9, 2026-09-16), read with
§3 (every ruled card N1–N12), §7 (every gate) and the FINDINGs of NWPP-10, 11, 12, 13, 30, 31, 32,
33, 34, 36, 37, 37b, 38, 39 — inputs, re-derived nowhere below. Every number in this file was
measured in this session at the pin, or is quoted from one of those FINDINGs with its section.

---

## 0. The pin, the branch, the preconditions

```
63a3a5aee802d69511d9230e0d4f5ebec1dcf38e   origin/main at PRECOMMIT time (this branch's base)
<sha of the commit carrying this file>     the shard pin — a FULL 40-char SHA, recorded verbatim in the shard prompt and the FINDING
```

| precondition (gate G4) | check at the pin | result |
|---|---|---|
| NWPP-30 outage windows | `data/raw/campd-unit-outages-NWPP.csv` (2,270 rows, sha `39bb3416…`) present; `thermal_tranches_NWPP.csv` present and **NOT read** by this recipe (card N8) | yes |
| NWPP-31 benchmarks | `calibration_reference.json` `isos.NWPP` + `egrid_benchmark.NWPP`; `NWPP_{2023,2024,2025}_renewable_capacity.csv` | yes |
| NWPP-32 hydro budget | `data/raw/nwpp-hydro/nwpp_hydro_budget.parquet`; `load_hydro_budget("NWPP", y)` reproduces 280 plants / 106.9353 · 107.9575 · (2025 backfilled) 113.1555 TWh | yes — §3 |
| NWPP-33 zonal shares / VRE shape / gas basis | `parse_nwpp_shares` in `curate_zonal_shares.py`; `nwpp-{wind,solar}-shape/`; `nwpp_zonal_gas_hub.csv` (R-1/R-2/R-3 **unarmed**, as landed) | yes |
| NWPP-34 served interchange | `envelopes.nwpp_net_interchange` + `_SCALAR_INTERCHANGE_ISOS["NWPP"]`; `load_demand` net −13.745 / −12.891 / −4.785 TWh reproduced | yes — §3 |
| **NWPP-36 cascade coupling** | `ScenarioConfig.hydro_cascade_coupling` at `scenarios.py:3770`, on `_CACHE_KEY_OPTIONAL_FIELDS` (1820) with frozen default `"False"` (2470); `load_hydro_cascade("NWPP", y, …)` resolves **5 coupled plants / 5 links** in every year | yes — §3 |
| NWPP-37 / 37b / 39 fuel-screen seam + zero-baseline guard | `frames._eia_hourly_frame` screens at the constructor; pool screened per member; `_FUEL_SPIKE_PLATEAU_PCT` guard in `actuals.py` | yes — §4.4 |
| NWPP-38 PNCA measurement | `data/raw/nwpp-hydro/nwpp_pnca_*` + `README-nwpp-38.md` | yes — §4.2 |
| rubric v3.8 price-unscored class | `calibration_verdict._price_reference_absent` keyed on the ABSENCE of an `actual_lmp.json` block; the store names exactly `CAISO ERCOT MISO NEISO NYISO PJM SPP` — **no NWPP block, and it must stay that way** | yes |
| `TAIL_THRESHOLD["NWPP"]` | absent from all three copies (gate G6 skip, executed by NWPP-31) | yes |
| rule 12: another per-plant solve running from this account? | `list_sessions` at launch | recorded in the FINDING |

**NWPP has ZERO registered runs** (`frontend/data/backcast/registry/` carries no NWPP sidecar,
`keepers/NWPP.json` does not exist, `status/NWPP.js` does not exist). This run is the first.

---

## 1. Owner ruling N10-R — no screen, one shard, one invocation, one bundle

Card N10 as chartered prescribed a screen year chosen by a residual-blind hydro statistic. The owner
ruled instead (N10-R, 2026-09-16): **solve all three years directly.** There is no screen, no screen
year and no screen gate in this lane. The form is rule 32(b)'s: **ONE shard, ONE
`--year 2023 2024 2025` invocation, ONE bundle**, years sequential inside it (rule 12), the bundle
pushed by the shard to its own branch (rule 34(a)), fetched, scored and registered by this session
(collision rule 1's exception: this lane IS the registering session).

**Control = none.** There is no NWPP keeper, so rule 29(b) form 4 is vacuous and no control solve
is spent; G-DRIFT has nothing to difference against. **This bundle becomes the rule-29(b) control
for every later NWPP lane** — which is why its `hourly/` sidecars are committed with it.

The bundle is registered **whatever the determination reads** (rule 15; the SPP-40 precedent), and
the promotion question — whether it becomes `keepers/NWPP.json`'s first keeper — is put to the owner
in this session (rule 31), never decided here.

---

## 2. The recipe — every value fixed before the solve

### 2.1 The invocation (the shard's exact command line)

```
python3 scripts/run_calibration_full.py --iso NWPP --year 2023 2024 2025 \
    --hydro-backfill-year 2024 \
    --hydro-cascade-coupling \
    --out-dir results/calibration/nwpp40_span_A \
    --note "nwpp-40 first NWPP solve: five whole-BA zones on WECC-catalogue TTC tiers (card N5), served measured EIA-930 interchange with priced seams default-off (card N4), one PRM scalar 0.144 (card N7), legacy heat-rate bins (card N8), Columbia mainstem hydraulic coupling ARMED (owner rulings N3/N12), 2025 hydro backfilled from 2024 for the 263 NO_923_SERIES plants (NWPP-32, R-f), every offer band 1.0, authorized_price_tuning NONE, price UNSCORED (card N2 limb b, rubric v3.8)"
```

**No other flag.** No `--hydro-eia930-monthly` (REFUSED — §4.4), no `--set`, no
`--offer-curve-json`, no `--commitment` / `--enable-legacy-p2`, no `--no-container-preflight`,
no `--no-xyear-warmstart` (the calibration CLI's default ON stands, as it does for every keeper).
The runner is run **unmodified at the pin**.

### 2.2 The two runner edits this lane lands BEFORE the pin, and why they are admissible

NWPP-36 built the field with **no CLI surface** on either orchestrator (its FINDING §1.1; measured
here: neither `run_calibration_full.py` nor `run_calibration.py` carried a `--hydro-cascade*`
argument). The only arming routes were a recipe, an `ISOConfig.default_scenario_overrides` entry
(a `src/` edit this lane may not make), or `replay_keeper.py --set` (which needs an existing
bundle — there is none). So this lane adds, in `scripts/run_calibration_full.py`:

1. **`--hydro-cascade-coupling` / `--no-hydro-cascade-coupling`** (`BooleanOptionalAction`,
   default `None`), riding the **generic `prb_overrides` ScenarioConfig channel** — the same
   channel `gas_hub_basis_daily`, `chp_startup_covered`, `mustrun_chp_btm_holdout` and the coal
   sigmoid family use — so the value reaches `run_year`'s config AND `recorded_cfg`, and
   `run_config.json` / `meta.json` record it (rule 24 `[R-REGISTRY]`: every tunable in the
   registry and in the run's record). Unset moves no cache key (the field is on
   `_CACHE_KEY_OPTIONAL_FIELDS`); no existing run's key can move.
2. **`hourly/hydro_cascade_<year>.parquet`** — the per-coupled-plant hourly spill / pond / water
   value sidecar from the three `DispatchResult.hydro_cascade_*` arrays NWPP-36 exposed and whose
   persistence its FINDING §7 item 5 routed to exactly this lane. `None` on every unarmed or inert
   run, so no other bundle gains a file. Five plants × 8,760 rows.

Guard: `tests/unit/pipeline/test_hydro_cascade_cli_flag.py` (tri-state parse, channel routing under
the field name, field existence, cache-key movement only when armed, sidecar frame shape). Neither
edit is a mechanism, a scalar, or a matrix row (rule 28(c) does not fire: the field's row exists
since NWPP-36); `check_mechanism_matrix.py`'s new-CLI-flag warning is answered by naming
`hydro_cascade_coupling` in the NWPP shard cell this lane stamps.

### 2.3 What the recipe is — the CLI's ISO-agnostic backcast construction, measured zero-LP

`backcast_config(year, "NWPP", 8760, <Henry Hub>)` under the calibration CLI's defaults
(`coal_prb_sigmoid=True`, `prb_sigmoid_tiered=True`, `coal_mustrun_per_plant=True`,
`coal_drop_pof=True`, `outage_source="historic"`, `coal_prb_passthrough=1.0`,
`hydro_year="normal"`) yields **850 `ScenarioConfig` fields, 24 non-default** — every one set by
`pipeline/backcast_config.py` or the per-ISO registries, none by this lane:

| field | recipe value | default | why |
|---|---|---|---|
| `iso` / `mode` | NWPP / backcast | ERCOT / forecast | the backcast construction; `mode` is the explicit switch |
| `plant_level_fleet`, `cc_committed_per_plant`, `cc_peaking_per_plant`, `cc_duct_peaking`, `chp_steam_following` | true | false | one LP unit per EIA-860 generator + per-plant CC tranche structure |
| `outage_source` / `historic_outage_overlay` / `correlated_forced_outage` | historic / false / false | statistical / true / true | measured unit-level outage windows (NWPP-30: 2,270 windows, 55 plants / 95.2 % of CEMS-qualifying MW) in place of statistical draws |
| `gas_plant_monthly_fuel_pricing`, `nearby_fuel_price_fallback`, `gas_st_startup_spread`, `f923_gas_price_plausibility_screen` | true | false | measured EIA-923 delivered fuel (NWPP-12 §2.5: 38 plants file; **Colstrip and Centralia file none** — §4.6) |
| `gas_price_override` | 2.54 / 2.19 / 3.52 | None | measured Henry Hub (`henry_hub_actual`, NWPP-31 §2.5) |
| `wefor_multiplier` | **0.7** | 1.0 | the CLI's non-MISO default — an inherited generic scalar, ledgered §5, **not re-chosen** |
| `cc_capacity_reconcile_path` | `…/cc_capacity_reconcile_NWPP.csv` | ERCOT file | ISO-keyed; `cc_capacity_reconcile` is False and the file does not exist → inert |
| `offer_curve_by_group` | 13 groups | {} | **every band NWPP dispatches is 1.0** — §2.4 |
| `rps_enabled` / `datacenter_load_path` / `entry_lookahead_reprice` / `storage_entry_*` / `capacity_market_clearing_by_iso` | false / off / false / false / None | forecast defaults | forecast-only machinery a backcast never enters |
| **+ `hydro_cascade_coupling`** | **true** (this lane, §2.1) | false | owner rulings N3 / N12 — §4.1 |

`use_campd_bins` reads `True` in the config and is **inert**: NWPP is absent from
`CAMPD_BINNING_ISOS` (card N8), so `load_or_synthesize_bins` returns `None` and the fleet takes the
legacy `aggregate_fleet` path with `plant_level_fleet=True`. `hydro_backfill_year` is a solve kwarg,
not a config field, recorded in `meta.json`.

**Expected per-year cache keys** (computed at the pin from the construction above; the shard's
`run_config.json` is compared against them after it lands — a mismatch is a stop-the-line finding,
not a silently different recipe): armed 2023 `678d38882c2bcfca` · 2024 `3977fcf867296207` ·
2025 `ff5254b07b104419` (the same construction unarmed: `b40c352048c144cc` / `e54ec61ffddaf915` /
`1750859025f0ea4e` — the coupling is the only difference).

### 2.4 Offer arrays — gate G5, rule 25 measured at the config

`build_offer_curve_overrides.py --iso NWPP --list` and the constructed `offer_curve_by_group`
agree: `CC_CHP`, `CC_REGULAR`, `COAL`, `COAL_BIT`, `COAL_LIGNITE`, `COAL_PRB`, `COAL_WC`, `CT_CHP`,
`CT_PEAKER`, `ST_GAS` all read **1.0 on `committed` / `econ_low` / `econ_high` / `peak`**; the delta
JSON is `{}`; **no `phys_*` row exists**. The three `*_INTERMEDIATE` curves carry their generic
non-unit bands (`CC_INTERMEDIATE` 0.92 / 0.95 / 1.08 / 2.25 etc.) and are **inert**:
`ct_intermediate_split`, `cc_intermediate_split` and `st_gas_intermediate` are all False, so no
unit is ever assigned to them. Only the structural shares differ by class (`econ_low_share`
0.5–0.55, `pct_peaking` 7–15) and they are not the tuning channel. No ERCOT- or other-ISO-fitted
multiplier leaks into NWPP (rule 25; `backcast_config` deep-merges the SPP coal-identity bands, all
1.0, for NWPP).

**`authorized_price_tuning` is declared NONE** (§5). Most of this footprint is cost-based
vertically-integrated dispatch and there is no NWPP price residual to tune on in any case; a band
≠ 1.0 would need a far stronger story than an RTO's and would break rule 25.

---

## 3. Phase-0 census (zero-LP, called on the recipe at the pin)

| object | 2023 | 2024 | 2025 | source |
|---|---|---|---|---|
| thermal LP units (`load_fleet_from_csv`) | 445 / 29,639.8 MW | 445 / 29,639.8 | 445 / 29,639.8 | EIA-860 canonical; per-year vintages differ in the shard's own load (NWPP-20 §1 row 19) |
| hydro budget plants / annual TWh / envelope MW | 280 / **106.9353** / 35,808.2 | 280 / **107.9575** / 35,694.6 | 280 / **113.1555** (2024 backfill) / 35,694.6 | `load_hydro_budget`; NWPP-32 §2–§3 |
| cascade resolve (armed) | **5 coupled / 5 links** | 5 / 5 | 5 / 5 | `load_hydro_cascade`; plants **3921 Chief Joseph · 3886 Wells · 6200 Rock Island · 3075 Bonneville · 3925 Ice Harbor**, τ by link **0 / 1 / 1 / 0 / 0 h** |
| gross demand TWh / coincident peak MW | 284.206 / 49,290 | 290.540 / 52,564 | 293.483 / 50,953 | `load_demand(include_interchange=False)`, 5 × 8,760 |
| served interchange TWh (export +) | −13.745 | −12.891 | −4.785 | net-of-TI 270.461 / 277.649 / 288.698 TWh; NWPP-34 §3 |
| net-of-TI peak MW | 45,430 | 48,484 | 45,977 | |
| zone peaks NW / OR / INLAND / EAST / SNV (MW) | 19,790 / 8,377 / 8,000 / 8,941 / 9,249 | **21,560** / 8,342 / 8,389 / 9,562 / 9,797 | 21,186 / 7,997 / 8,230 / 9,717 / 9,239 | NWPP-NW 2024 peak = the January cold snap (§4.3) |
| zones / links | 5 zones; 9 directed links: EAST↔SNV 600/580, INLAND↔SNV 500/360, INLAND↔EAST 1,600/1,250 (Tier 1/1/2), INLAND→NW 8,877 / NW→INLAND 2,550 (Tier 2), NW→OR 43,600 (Tier-3 placeholder, non-binding by construction) | | | `get_iso_config("NWPP")`; card N5 |
| VOLL | $2,000/MWh, **declared interim** (WEIM hard offer cap; not a customer damage function) | | | `iso_configs._nwpp_config`; NWPP-10 §7.1 |
| memory class (registry) | `IsoMemoryClass("NWPP", peak_gb=5.5, per_plant=False, co_opt=False)` — an ESTIMATE, measured here | | | `run_isos_concurrent.py` |

The census reproduces NWPP-20 §4 and NWPP-32 §2 to the MWh and the MW. Nothing below was chosen by
looking at any of it.

---

## 4. The five ex-ante declarations (charter, "FIVE THINGS THE PRECOMMIT MUST DECLARE")

### 4.1 The G-A3 miss, at full magnitude — and what the coupling actually is

NWPP-36's pre-registered armed-response gate **G-A3 FAILED**. It expected the within-day amplitude
`(daily max − daily min) / daily mean` at coupled run-of-river plants to fall by **≥ 30 %** at the
median plant when the coupling is armed. Measured (January 2023, real chain): Chief Joseph
**2.339 → 2.131** (−8.9 %), Wells 2.153 → 2.088 (−3.0 %), Rock Island 2.489 → 2.394 (−3.8 %),
Bonneville 2.045 → 2.027 (−0.9 %), Ice Harbor **4.275 → 3.825** (−10.5 %); May 2023 the same
1–5 %. Median ≈ 6 % against 30 %. Rock Island's armed peak (606 MW) also exceeds the flat-arrivals
bound (552 MW) because Rocky Reach, its UNCOUPLED upstream, peaks into it. **The cause is physics,
not a bug**: a coupled plant INHERITS its upstream's hourly shape (every coupled link measured
τ = 0–1 h; Chief Joseph's shape is Grand Coulee's at r > 0.99 when armed) and the pond is never
drawn (0 / B at every plant, both months). The real visible effect is the reverse one the gate did
not anticipate: **Grand Coulee's own January amplitude falls 3.71 → 2.15** as the row transmits
Chief Joseph's turbine capacity back up the chain. The owner ACCEPTED this (ruling **N12**,
2026-09-16) as a **mis-specified gate, not a passing one** — the lane explained the physics instead
of moving the bar — and it **rides this keeper's determination basis**. It is not softened here.

What is armed is also smaller than the mechanism's docstring says: the PRECOMMIT asked for 14 coupled
plants / 15 links (65.9 % of hydro nameplate); the measurement **delivered 5 coupled plants / 5
links = 5,717 MW = 16.0 % of NWPP conventional-hydro nameplate** — 3 links uncoupled on τ (Wells→Rocky
Reach celerity 34.9 mph, Rock Island→Wanapum diurnal alias, Dworshak→Lower Granite r = 0.02) and
7 on the 2 % side-inflow floor (a spill-metering artefact at the federal lower-river projects,
NWPP-36 §7 item 1). Every other armed gate PASSED: G-A1 monthly energy moves **0.000 %** (rule 19
— the coupling redistributes WHEN, never how much), G-A2 water balance to 1e-5, G-A4 spill season,
G-A5 lag signature, G-A6 OFF identity, G8 25 of 25 keeper cache keys byte-identical. NWPP-36's own
recommendation was NOT to arm it for the first keeper until the seven lower-river links are
re-measured; **the owner ruled otherwise (N12: "W4 proceeds")** and this lane implements the ruling.

### 4.2 The PNCA discontinuity (R-j) — declared regardless of NWPP-38's null

The 1997 Pacific Northwest Coordination Agreement — the instrument that coordinated the Columbia's
storage projects, and the one that defines *"Period means a calendar month"*, the model's own budget
period — **terminated 2024-09-15 with no successor text found**. The Columbia's coordinating
instrument therefore changes INSIDE the scored window, and this is declared on the determination
basis whatever any measurement says. NWPP-38's result is reported alongside it: **verdict (a), no
measurable change** — 0 of 56 treated cells (the coordinated system BPAT · CHPD · DOPD · GCPD)
reach the |z| ≥ 4.07 detection threshold in 2024 or 2025 (max 2.45 / 3.04), while the **control
group (independent tributaries PGE · TPWR · PACW) moved MORE**: 1 cell past threshold in 2024 and 8
in 2025 (PGE's intraday ramp z = 10.95). A placebo date of 2022-09-15 returns a bigger "effect"
(t = +4.76) than the real one (t = −1.17). Power: a change of roughly one fifth in how the mainstem
shapes water within a day would have been detected and was not; a change of a tenth would not have
been. *"The systems the PNCA never coordinated moved more than the one it did … the signature of
hydrology, not of an instrument."* The monthly budget is therefore kept as the period, and no
mechanism is proposed for the termination.

### 4.3 The 30 defective demand hours (gate G20), named individually, and the demand convention

Convention (NWPP-10 §1.3 / audit §4.4, implemented by NWPP-20 in `eia930/{frames,demand}.py`): the
LP demand reads **`Demand (MW) (Adjusted)`** per member BA; **`_screen_demand_dropouts` IS applied
per member** (it removes the **17 exactly-zero NEVP hours of 2025** — 06:00/07:00 UTC pairs on
04-18, 04-25, 05-15, 05-23, 06-20, 07-18, 08-22, 09-19, 11-21, raw and Adjusted both 0.0);
**`_screen_demand_spikes` is NOT applied** — at 2.5 × median it would delete 54 REAL hours of the
12–16 January 2024 CHPD cold snap (Adjusted byte-identical to raw; CHPD's 583 MW annual peak on
2024-01-13; the NWPP-NW zone's own 2024 annual peak, 21,560 MW at 2024-01-13 19:00 UTC, sits in
that block). **Nothing is padded, interpolated or rescaled** (rule 13): the Adjusted column is
EIA's own repair of its raw feed, a measured input, and every one of the 30 artifacts below is
already repaired in it.

Measured in this session off the committed spine (`data/raw/eia-930-hourly/<BA> hourly.parquet`,
raw `Demand`, per BA per year, `|D| > 2.5 × annual median` or `D < 0`): **84 flagged hours = the 54
real CHPD hours + these 30 artifacts**, reproducing the audit's groups exactly (AVA 10, NWMT 11,
NEVP 6, PACE 1, SCL 2). Unscreened, the raw column would put the 2025 coincident peak at
835,464 MW; Adjusted reproduces 49,290 / 52,564 / 50,953 MW.

| # | BA | year | UTC hour (end) | raw MW | Adjusted MW | raw ÷ median |
|---|---|---|---|---:|---:|---:|
| 1 | AVA | 2024 | 2024-01-05 10:00 | 11,319 | 1,349 | 7.8× |
| 2 | AVA | 2024 | 2024-01-05 11:00 | 11,331 | 1,332 | 7.9× |
| 3 | AVA | 2024 | 2024-01-05 12:00 | 11,343 | 1,342 | 7.9× |
| 4 | AVA | 2024 | 2024-01-05 13:00 | 11,381 | 1,382 | 7.9× |
| 5 | AVA | 2024 | 2024-01-05 14:00 | 11,502 | 1,491 | 8.0× |
| 6 | AVA | 2024 | 2024-01-05 15:00 | 11,615 | 1,610 | 8.1× |
| 7 | AVA | 2024 | 2024-01-05 16:00 | −58,286 | 1,692 | −40.4× |
| 8 | AVA | 2025 | 2025-04-22 14:00 | 11,359 | 1,466 | 7.8× |
| 9 | AVA | 2025 | 2025-10-12 10:00 | 810,948 | 1,064 | 558.1× |
| 10 | AVA | 2025 | 2025-10-12 11:00 | 191,180 | 1,003 | 131.6× |
| 11 | NEVP | 2024 | 2024-06-03 00:00 | 68,633 | 5,729 | 16.6× |
| 12 | NEVP | 2025 | 2025-06-16 15:00 | 67,261 | 4,281 | 16.0× |
| 13 | NEVP | 2025 | 2025-07-01 04:00 | 69,812 | 7,053 | 16.6× |
| 14 | NEVP | 2025 | 2025-07-23 02:00 | 69,290 | 7,020 | 16.5× |
| 15 | NEVP | 2025 | 2025-08-25 05:00 | 68,580 | 6,661 | 16.3× |
| 16 | NEVP | 2025 | 2025-09-16 01:00 | 68,917 | 6,313 | 16.4× |
| 17 | NWMT | 2023 | 2023-08-23 16:00 | −798 | 1,414 | −0.6× |
| 18 | NWMT | 2024 | 2024-06-20 19:00 | −409 | 1,311 | −0.3× |
| 19 | NWMT | 2024 | 2024-07-01 19:00 | 21,967 | 1,448 | 16.2× |
| 20 | NWMT | 2024 | 2024-08-27 20:00 | 66,960 | 1,416 | 49.5× |
| 21 | NWMT | 2024 | 2024-10-07 20:00 | 66,777 | 1,274 | 49.4× |
| 22 | NWMT | 2024 | 2024-11-14 04:00 | 7,071 | 1,465 | 5.2× |
| 23 | NWMT | 2025 | 2025-07-08 20:00 | 28,423 | 1,667 | 21.5× |
| 24 | NWMT | 2025 | 2025-10-14 19:00 | 33,507 | 1,356 | 25.4× |
| 25 | NWMT | 2025 | 2025-10-14 20:00 | 100,285 | 1,344 | 76.0× |
| 26 | NWMT | 2025 | 2025-10-29 21:00 | 18,233 | 1,338 | 13.8× |
| 27 | NWMT | 2025 | 2025-12-02 21:00 | 30,346 | 1,547 | 23.0× |
| 28 | PACE | 2023 | 2023-08-07 19:00 | 65,826 | 6,911 | 11.5× |
| 29 | SCL | 2024 | 2024-04-02 18:00 | −2,030 | 1,167 | −1.9× |
| 30 | SCL | 2025 | 2025-06-27 18:00 | −54,511 | 997 | −51.5× |

### 4.4 The 2025 data posture, and which state of the fuel columns this lane reads

- **EIA-923 2025 is an early release.** 25 of 288 conventional-hydro plants report; **263 read
  `NO_923_SERIES`** (NWPP-32 §2) and are flagged, not filled. **`backfill_year=2024` stands**
  (`--hydro-backfill-year 2024`, §2.1): those 263 plants carry their 2024 monthly water, giving a
  2025 budget of **113.156 TWh over 280 plants** — 66.2 % measured 2025 energy (the 25 reporters,
  every ≥ 1 GW plant among them; the same panel ran +6.1 % / +7.5 % vs 2023 / 2024, a wetter year,
  not a drought) and 33.8 % carried 2024 water. This is the pre-declared NWPP-32 posture, taken
  unchanged.
- **The 2025 `eia930_monthly` repin is REFUSED** (card R-f; NWPP-32 §3.2), on rule-14 grounds: the
  −2.5 % 930-vs-923 gap is a **population mismatch** by BA (Priest Rapids files 860→BPAT / 930→GCPD;
  WAUW −2.6 / −2.8 TWh), so the pool level is not the plant panel's level, and a repin would rescale
  a measured input to a different boundary.
- **Which state of the fuel columns this lane reads.** Since NWPP-32 solved nothing and NWPP-37 /
  37b / 39 have landed at this pin, every `NG: <CODE>` reader now goes through the screened frame
  constructor with the pool screened **per member** and the zero-baseline guard on the anchor. The
  concrete state, measured by those lanes at their exits and inherited here: pooled `NG: WAT` 2025
  peak **23,607 MW** (was 817,202 raw); `measured_monthly_hydro` 2025 annual **110.2639 TWh**
  (October 7,095.6 GWh, from 8,243.5 raw); 2024 annual 105.0374 TWh; 2023 unchanged; the 2025
  NWPP member slips (AVA `NG: OTH`/`NG: WAT`, NWMT `NG: COL`/`NG: WAT`) all still caught; NWPP-39
  moved no 2025 series. **What this solve reads from that state:** the benchmark (NWPP-31's
  committed `calibration_reference.json` block — `load_eia_hourly_benchmark` was already screened,
  so the C1/C4 actuals are unchanged: hydro 106.9281 / 107.9002 / **110.2719** TWh, the 2025 value
  swapped to EIA-930 by the 0.80 rule), the C4 hourly actuals, and the envelope readers. **What it
  does NOT read:** the `eia930_monthly` budget repin (refused above) and the 930-derived hydro
  floors (none is armed; `min_flow_fraction` default 0). The committed `nwpp_hydro_budget.parquet`
  is EIA-923-derived and never carried a 930 hour, so NWPP-37's note that
  `build_nwpp_hydro_budget.py` "would move on next legitimate re-derive" concerns its 930
  reconciliation columns, not the budget this solve dispatches against.
- **Consequence for scoring, stated now:** 2025 C1 rows on the preliminary vintage are gated only
  where the completeness audit reads COMPLETE; `eia923_incomplete: true` (BA total ÷ EIA-930
  0.7881) routes the rest to the C2 EIA-930 family fallback. Wind 2025 is swapped to EIA-930
  (923/930 = 0.5746). None of this is a hole to fill in-lane.

### 4.5 Memory (gate G21) and the shard budget

- The registry estimate is `peak_gb=5.5` (zonal / no co-opt, from CAISO's measured 4.5 GB + one
  zone + the 280-plant budget rows). This lane's own reading of the LP size: 445 thermal units +
  280 hydro budget generators + 5 × (wind, solar, storage) per zone + 9 links, **plus the cascade
  block 5 × 8,760 rows / 10 × 8,760 columns** — a smaller thermal column set than SPP's 1,212 LP
  units (which peaked at 5.25 GB / 369 s for the span). Expectation: **5–8 GB peak, 15–45 min wall
  for the three years**; recorded as an expectation, never a gate.
- **Budget stated to the shard: 150 minutes of wall clock for the whole invocation.** Rule 32(b)
  governs the case: a span that cannot fit the 20-minute ceiling gets **a longer single shard with
  its budget stated**, never a per-year fan-out. **A shard at 150 min with no `dispatch/2025_P1.
  parquet` STOPS and reports; it never pushes a half-written bundle** (rule 27).
- The shard runs the runner **unmodified**, never passes `--no-container-preflight`, and REPORTS
  the `container preflight:` and `memory peak:` log lines verbatim (rule 32(c)(8)). This
  orchestrator's own container measures a **13.36 GiB** nested-cgroup ceiling (`memory.limit_in_
  bytes`) on a box whose `free` reads 15 — the shard's will be read by the runner's preflight, not
  assumed.
- The measured `peak_gb` is recommended to the desk in the FINDING; the `run_isos_concurrent.py`
  registry edit is the desk's, not this lane's.

---

## 5. The DOF ledger — declared before the solve (rule 21; gate G5)

`build_dof_ledger.py` on this recipe is expected to list the same config-derived entries SPP-40's
and SOCO-40's did, and nothing else — no curated per-ISO constant is keyed on NWPP; no floor,
bridge, adder, seam ladder or scarcity overlay is armed:

| entry | value in this recipe | identification, stated honestly | residual-identified on NWPP? |
|---|---|---|---|
| `offer_curve_by_group` | 1.0 on every band of every class NWPP dispatches (§2.4) | the **identity** — every unit offers at its own heat rate × delivered fuel + VOM; **0 tuned scalars**. The ledger tool tags the container `residual` by construction (it is the rule-1 channel); on NWPP the channel is unused | **no** |
| `offer_curve_smoothing` (n = 6, exp = 1.0) | generic | the econ-ramp interpolation between `econ_low` and `econ_high`; with both at 1.0 the ramp has **zero span** — inert | **no** |
| `wefor_multiplier` | 0.7 | the CLI's non-MISO default, an inherited generic scalar the audit (C-15) classifies residual-identified on ERCOT; **neither 0.7 nor 1.0 has an NWPP identification**, so the default is kept, NOT re-chosen, ledgered `residual` with its open root cause | **no — inherited** |
| `hydro_cascade_coupling` | true | **not a free parameter**: a gate on a measured artifact whose every τ, band, η and inflow is measured (NWPP-36 §4; rule 13) — 0 scalars chosen. Recorded in `governance.measured_input_switches`, not in `free_parameters` | no |
| `voll` | 2,000 | **declared interim** (NWPP-10 §7.1 / `iso_configs`): the WEIM hard offer cap, not a customer damage function; ledgered as a free parameter with `published` identification and the LBNL-ICE derivation as its routed successor | no — never swept |

**The ledger is short, and that is the claim**: this recipe carries **zero values chosen on an NWPP
residual**, because no NWPP residual existed when it was fixed. **`authorized_price_tuning`: NONE**
— declared in `calibration_attestation.json` as the four governance assertions all `true`, **no
`authorized_price_tuning` block** (a block names a channel in use; there is none), plus the explicit
prose line `authorized_price_tuning_declared: "NONE — …"` so C6 reads the declaration rather than its
absence (gate G5; the SOCO-40 §8 form).

---

## 6. The shard — launch form (rule 32(c)), verbatim prompt

`mcp__Claude_Code_Remote__create_session` with `source_revision` = the FULL 40-char SHA of the commit
carrying this file (never a branch), `source_url` = this repo, `outcome_branch`
`claude/nwpp-40-span-a`. The prompt the shard receives is reproduced in the FINDING; its binding
content:

- **Hard stop 1:** `git rev-parse HEAD` equals the pin. Never `git pull`, `git rebase`, or any
  "sync". **Hard stop 2 (config signature, read off `run_config.json` after year 1 and before
  pushing anything):** `iso == "NWPP"`, `mode == "backcast"`, `hydro_cascade_coupling == true`,
  every `committed / econ_low / econ_high / peak` band on `CC_REGULAR`, `CC_CHP`, `CT_PEAKER`,
  `ST_GAS`, `COAL*` equal to 1.0 — anything else STOPS and does not push. **Hard stop 3:** the
  solve log shows `hydro cascade coupling — 5 coupled plants [3921, 3886, 6200, 3075, 3925]` for
  the first year; an "armed but INERT" line STOPS.
- **Budget:** 150 min wall for the whole invocation; at the budget with no
  `dispatch/2025_P1.parquet` → STOP and report, push nothing under `results/`.
- **Push form (rule 34(a)):** `printf '\n!results/calibration/nwpp40_span_A/**\n' >> .gitignore`,
  then `git add .gitignore && git add results/calibration/nwpp40_span_A` — a **PLAIN `git add`,
  NEVER `git add -f`** — then `git status --short` must show nothing outside those two paths, then
  ONE commit and `git push -u origin claude/nwpp-40-span-a`. The pushed tree MUST carry
  `dispatch/{2023,2024,2025}_P1.parquet` and the bundle-root `system.parquet`.
- **Report** (its final message AND one file `docs/handoffs/SHARDREPORT-nwpp-40-span-2026-09-16.md`
  in the same commit): the pinned SHA; wall clock per year and per pass; the `container preflight:`
  and `memory peak:` lines verbatim; the cascade resolve line per year; per-year
  `metrics.json` headline (load-weighted price, slack MWh, dump MWh, hours > $200) and the
  class TWh table; the three cache keys from `run_config.json`; the commit SHA the bundle lives at.
- **FORBIDDEN by name:** `git add -A`, `git add .`, `git add -f`, `dashboard_add_run.py`,
  `build_manifest.py`, `build_status.py`, `prune_iso_runs.py`, anything under
  `frontend/data/backcast/**`, any edit under `src/` or `scripts/`, opening a PR, deleting any
  result, `--no-container-preflight`, `--hydro-eia930-monthly`, any `--set`, any second
  invocation, any per-year split.
- **"A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is
  a FAILURE."**

---

## 7. After the shard lands — what this session does, in order (zero LP)

1. `git fetch origin claude/nwpp-40-span-a`; **`git ls-tree -r <shard sha> -- results/calibration/
   nwpp40_span_A` must list > 0 files** (rule 34(d)), including `dispatch/<year>_P1.parquet` ×3.
2. `git checkout <shard sha> -- results/calibration/nwpp40_span_A`, then
   `git reset HEAD -- results/calibration/nwpp40_span_A` (the checkout STAGES gitignored paths —
   the SPP-40 trap) so only the slim set + `hourly/` are re-added with a plain `git add`. The
   shard's `.gitignore` negation is NOT taken into this branch (the parent keeps `main` slim).
3. Verify the config signature and the three cache keys against §2.3; verify the cascade sidecar
   exists for each year.
4. `scripts/legitimacy_diagnostics.py` → `legitimacy_diagnostics.json`; `scripts/build_dof_ledger.py`
   + `scripts/gen_nwpp40_attestation.py` → `calibration_attestation.json` (§5).
5. `scripts/dashboard_add_run.py --label "nwpp 1 cascade" --bundle results/calibration/nwpp40_span_A
   --no-prune` (the promotion question is open, so no sweep); read `DETERMINATION:`;
   `scripts/calibration_verdict.py results/calibration/nwpp40_span_A --json` for the criterion
   table; `scripts/build_manifest.py` for the local preview.
6. `scripts/check_registry_payload_parity.py` — **read before acting** (rule 31 / charter): it
   sweeps `results/calibration/` on the FILESYSTEM, so any unmapped dir it names is checked against
   this lane's own paths; nothing is deleted.
7. Stamp the NWPP matrix cell for `hydro_cascade_coupling` (rule 28(b)) — verdict `K` only if the
   owner rules promote in-session; otherwise the measured outcome with the citation, leaving
   `keeper` / `gates` empty until a ruling.
8. Commit the bundle slim set + `hourly/`, the registry sidecar + `runs/<id>.js` + any changed
   `bench/NWPP/`, in ONE commit over `git push` (the payload exceeds `push_files`' cap); FINDING in
   a second commit. `keepers/NWPP.json` + `status/NWPP.js` ONLY on an in-session promotion ruling.
9. Archive the shard once (1)–(3) hold (rule 33(a)); record recovery by full SHA; the shard branch
   stays until the owner rules (rule 33(f)(3)).
10. **Ask the promotion question, explicitly, in the final report** (rule 31): this is the first
    NWPP bundle that has ever existed.

---

## 8. The determination basis — the lines the FINDING must carry

1. **The price gap** — no admissible NWPP hourly price series (NWPP-13 read NO: WEIM on-peak
   −37.5 / −22.6 / −23.6 % vs Mid-C against a ±10 % bar, at 5.5–6.2 % of footprint energy);
   C3a / C3b / C3c **UNSCORED, never PASS**; the determination reads `PHYSICALLY-CALIBRATED
   (PRICE UNSCORED)` or `…-WITH-CAVEATS (PRICE UNSCORED)`, **never a bare `CALIBRATED`**; the
   model's own annual mean LMP printed MODEL-ONLY / UNVERIFIED at full magnitude.
2. **G-A3** (§4.1) — the coupling's amplitude response is 1–10 %, not ≥ 30 %; owner ruling N12.
3. **The coupled set is 16 %, not 66 %** of hydro nameplate (§4.1) — 10 of 15 links uncoupled on
   the measurement gates; the lower river dispatches on its monthly budget.
4. **PNCA terminated 2024-09-15 inside the window** (§4.2); NWPP-38 verdict (a).
5. **Card N7's two-regime PRM mismatch** — one scalar 0.144 tested against the summer coincident
   peak while NWPP-NW peaks in WINTER every year (0.86 / 0.80 / 0.82), NWPP-SNV in SUMMER at
   1.95 / 2.06 / 1.87× its winter load, and NWPP-INLAND mixes both regimes inside one zone; largely
   inert in a backcast (capacity evolution is forecast-mode) and lever NWPP-57.
6. **2025 posture** (§4.4) — 263 plants on 2024 water; `eia923_incomplete`; 930 repin refused.
7. **VOLL $2,000 interim** — the WEIM hard cap, not a customer damage function.
8. **NW↔OR is a Tier-3 placeholder** (43,600 MW, non-binding by construction) — no WECC path rates
   that boundary and none will (card N5); lever NWPP-55.
9. **Colstrip and Centralia file no EIA-923 fuel price** (26.7 % of coal MW, the whole coal fleet of
   NWPP-INLAND and NWPP-NW); they price on the supply-class trajectory (NWPP-12 §2.5).
10. **The served interchange is a footprint scalar spread by load share** (NWPP-34 §3): CAISO-facing
    flow lands on every zone, including the two with no California leg; and the schedule sits on
    two reporting bases (BPAT's balance-identity step at UTC 2025-06-01 07:00).

Every one is reported at full magnitude; none is absorbed, and none moves a gate.

---

## 9. What this lane is NOT allowed to do

No screen or screen year (N10-R). No second invocation, no per-year fan-out, no control solve. No
`--hydro-eia930-monthly`, no price series, no neighbouring-hub substitute (G17), no
`TAIL_THRESHOLD["NWPP"]`, no edit to `scripts/calibration_verdict.py`, nothing under
`frontend/data/forecast/**`, no `src/` edit, no other region's shard / registry / payload / log. No
band ≠ 1.0, no adder, offset, haircut, proxy or floor. No re-derive of any NWPP-3x artifact. Nothing
deleted from `results/` at any point (rule 31), and the promotion is the owner's decision.

---

## ADDENDUM 1 (2026-09-16 09:20 UTC) — the first shard STOPPED at its 150-minute budget; the budget is re-set to 480 minutes on the MEASURED rate, and nothing else changes

**What happened (from `docs/handoffs/SHARDREPORT-nwpp-40-span-2026-09-16.md`, shard commit
`4e218d0f01d603c1f14b6866a2486a80dc896ead`, branch `claude/nwpp-40-span-a`).** The shard ran the §2.1
invocation unmodified at the pin. Year 2023 solved in **7,004.0 s = 116.7 min** (P0 cold 1,728.6 s /
523,199 simplex iterations; P1 warm **5,217.1 s** / 533,017 iterations); year 2024 was ~32 min into
P0 when the 150-minute budget expired at 09:16 UTC, and the shard STOPPED and pushed nothing under
`results/`, exactly as instructed (rule 32(b) STOP rule). §4.5's expectation of 15–45 min for the
span was **wrong by a factor of ~8** — the measured rate implies **~350 min for three years** on this
container class (single-thread solve profile, 4 vCPU, 13.36 GiB cgroup ceiling, 10 GiB swap
provisioned by the preflight). Memory was NOT the constraint: peak 3.13 GB after 2023's release,
process RSS 2.55–3.28 GB during the solves — below the registry's 5.5 GB estimate.

**Decision, under rule 32(b) exactly as written:** *"where a whole span genuinely cannot fit the
20-minute ceiling the answer is a longer single shard with the budget stated in its prompt, not a
fan-out."* A second shard is launched with the **IDENTICAL invocation** (§2.1 — no flag added, none
removed, no solver setting touched, the runner unmodified) and a stated budget of **480 minutes**
(the measured 350 min plus a 37 % margin for 2024/2025 running slower than 2023). No per-year
split; no `--reuse-solved` chain (it cannot compose across containers — rule 32(b)); no change to
the solve profile (the preflight's single-thread pins are the runner's own and rule 32(c)(8) says a
shard names no memory or thread recipe of its own).

**Two things the 2023 leg already shows, recorded here BEFORE the second shard runs so they cannot
be read as discovered afterwards, and both REPORTED rather than repaired (rules 1 / 13 / 14):**

1. **NWPP-SNV prices at VOLL.** In 2023 P1, **23 NWPP-SNV zone-hours clear at exactly $2,000**
   (hours 4721–4724, 4743–4748, 4841–4844, 4937–4940, 4962, 5801–5804 — July and August), and a
   further **738 SNV zone-hours** sit in ($200, $1,000); no other zone exceeds $144.12. Slack MWh
   could not be read off the shard's disk (the zone-hour frame is an end-of-span write). The
   candidate cause is structural and was declared at the gate: NWPP-SNV (NEVP, 14.1 % of load,
   summer-peaking at 9,249 MW in 2023) is reached only through the two Tier-1 WECC paths
   (EAST→SNV 600 MW, INLAND→SNV 500 MW) while its measured external ties — NEVP↔CISO
   +7.6 / +9.2 / +9.5 TWh export and NEVP↔LDWP −8.7 / −9.3 / −7.5 TWh import (NWPP-11 §4) — enter
   only as the footprint-wide served scalar spread by load share (§8 line 10). Whatever the FINDING
   measures on the full span is reported at full magnitude; nothing is added to SNV's supply.
2. **`hourly/system_<year>.parquet` is not written per year** by the runner on this path (only at
   the end of the span, with `run_config.json` / `meta.json` / `metrics.json`); a budget STOP
   therefore leaves no scorable artifact at all. Pre-existing runner behaviour, not this lane's to
   change; recorded so the budget is understood as all-or-nothing.

The 2023 dispatch (`dispatch/2023_P1.parquet`, 666 LP units × 8,760 h, 270.505 TWh) and the cascade
sidecar (`hourly/hydro_cascade_2023.parquet`, 43,800 rows) exist on the first shard's ephemeral
disk. They are **not a bundle** and cannot be composed into one (rule 32(b)); they are asked to be
pushed to the shard's branch as a labelled diagnostic record (never `main`, never registered) so the
2023 evidence survives the container (rule 31 `[R-RETAIN]`), and the shard is archived only after
that push is verified (rule 33(a)).

Class TWh the 2023 leg produced (model only; the benchmark is scored by the parent on the full
span): hydro 106.872 · CC_REGULAR 53.467 · COAL 38.542 · wind 30.410 · solar 13.003 · nuclear 8.429 ·
CC_CHP 7.377 · OTHER 5.915 · CT_PEAKER 2.973 · biomass 2.772 · CT_CHP 0.578 · ST_GAS 0.133 ·
ST_CHP 0.034. Generation-weighted mean LMP 47.63 $/MWh (MODEL-ONLY / UNVERIFIED; no price series).

---

## ADDENDUM 2 (2026-09-16 15:12 UTC) — shard B's timeline, one container restart, and the budget extended to 600 minutes

Shard B (session `session_01MFciPYgGSZcAsqp8UKDxs7`, branch `claude/nwpp-40-span-b`, pin
`9580bdd040a10ba5998ccf303129b2cca26bd4f4`) launched the §2.1 invocation at 09:26:44 UTC. **That
attempt was killed by a container restart at ~10:30 UTC while the shard session sat idle** (its log
is retained as `results/calibration/nwpp40_span_A.launch.attempt1-killed-by-container-restart.log`
and is committed beside the shard's report). The shard **relaunched the identical invocation at
10:31:30 UTC**; that relaunch is THE run — an identical invocation restarted after an infrastructure
kill is not a second recipe and not a fan-out. To stop a second idle-kill the parent pokes the shard
by routine every 30 minutes (`:18` / `:48`), and the shard has answered every poke since.

Measured on the relaunch (`SHARDREPORT-nwpp-40-span-b-STATUS-2026-09-16.md`, commit `324bb027`):

| year | data_prep | solve_p0 (cold) | solve_p1 (warm) | total |
|---|---:|---:|---:|---:|
| 2023 | 17.0 s | 1,236.5 s | 3,674.2 s | **4,942.9 s = 82.4 min** |
| 2024 | 3.2 s | 2,235.8 s | **8,156.4 s** | **10,412.0 s = 173.5 min** |
| 2025 | started ~14:47 UTC; cascade resolved (5 plants, 5 links); 255 non-reporting plants backfilled from 2024 (38,219 GWh); 113,155.5 GWh budget over 280 plants | | | |

2024 took 2.1× 2023 (P1 2.2×). At that rate 2025 lands ~17:40 UTC, inside the 480-minute budget
(18:31:30 UTC) by under an hour, and a slower 2025 would have been killed by the shard's own STOP
rule with the whole span lost. **The budget is therefore extended to 600 minutes from the relaunch
(expires 20:31:30 UTC)**, under rule 32(b) exactly as addendum 1 applied it — a longer single shard
with its budget stated, never a fan-out; no flag, no solver setting and no recipe changes. The
directive was delivered to the shard at 15:14 UTC before the original budget could bind.

Nothing in the 2024 leg is read, scored or interpreted here; the parent scores the full span once
the bundle lands.
