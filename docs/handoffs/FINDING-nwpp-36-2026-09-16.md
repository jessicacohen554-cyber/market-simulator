# FINDING — lane NWPP-36: Columbia mainstem hydraulic coupling (owner ruling N3)

**Lane:** NWPP-36 (desk r#6 charter) · **Model:** Fable (`claude-fable-5-1`) · **Base:**
`6d1a144d62949b53af088df51787de68d2edf738` (`origin/main` at this session's start) · **Branch:**
`claude/upbeat-edison-93gxck` (harness-designated, as the PRECOMMIT and NWPP-32 both recorded for
their own lanes) · **DATA PROFILE:** `nwpp` · **PRECOMMIT:**
`docs/handoffs/PRECOMMIT-nwpp-36-2026-09-16.md` (on main at `04706651`, base `edd40943`, written by
the first NWPP-36 session, which pushed nothing beyond it — this is a FRESH session executing that
PRECOMMIT as binding, per the issuance notice; nothing in it was re-decided) · **Zero calibration
LP** (rule 32: every solve in this lane is a ≤ 19-generator × 744-hour unit test; no shard, no
bundle, nothing on disk to retain under rule 31).

## 0. Report first

1. **Gate G8 (keeper byte-identity, nine regions): PASS.** All 25 keys — every designated keeper's
   every `run_config*.json` re-keyed at base and head, SOCO and NWPP default + backcast-default,
   and the two pinned literals — are byte-identical (§4.1). The assembled LP is sha256-identical
   OFF at base and head for both fixtures and differs ARMED (§4.2).
2. **τ per link, measured from CROHMS hourly outflow anomalies (2023–24 train, 2025 check):**
   GCL→CHJ **0 h** (r 0.84) · CHJ→WEL **1 h** (0.48) · WEL→RRH 1 h (0.64, *celerity 34.9 mph — STOP*) ·
   RRH→RIS **1 h** (0.93) · RIS→WAN 23 h (0.33, *2024 says 0 h — STOP*) · WAN→PRD 0 h (0.63) ·
   PRD→MCN 13 h + IHR→MCN 0 h (joint 2-D, 0.35) · MCN→JDA 0 h (0.67) · JDA→TDA 0 h (0.88) ·
   TDA→BON **0 h** (0.43) · DWR→LWG 39 h (0.02 — *STOP*) · LWG→LGS 0 h (0.71) · LGS→LMN 0 h (0.79) ·
   LMN→IHR **0 h** (0.74). Bold = the five links that cleared EVERY pre-registered gate (§3.5);
   seven of the ten others cleared τ but trip the PRECOMMIT's 2 % side-inflow floor in
   spill-season months (§3.4), and are left uncoupled as the PRECOMMIT says.
3. **Armed within-month redistribution (real chain, one-zone reduced system, Jan + May 2023):**
   the mechanism arms, the rule-19 invariant holds exactly (**0.000 %** of any coupled plant's
   monthly energy moves ON vs OFF), the water-balance identity holds to 1e-5, the May spill
   object appears and closes on the measured CROHMS spill within ±10 % at Bonneville and Ice
   Harbor, and the lag signature holds — **but G-A3 FAILS as pre-registered**: within-day
   amplitude at the coupled run-of-river plants falls 1–10 % (Chief Joseph 2.34→2.13, Ice Harbor
   4.28→3.83), not ≥ 30 %, because a coupled plant INHERITS its upstream's hourly shape. The
   visible redistribution is the reverse one the gate did not anticipate: Grand Coulee's own
   January amplitude falls **3.71→2.15** as the row transmits Chief Joseph's turbine capacity back
   up the chain (§5). Reported at full magnitude; nothing was tuned to pass.

## 1. Drift from the PRECOMMIT, stated

| item | PRECOMMIT | this session |
|---|---|---|
| base sha | `edd40943` | `6d1a144d` (main moved; every count re-taken here; keeper ids identical) |
| branch | `claude/jolly-keller-8j3ht6` | `claude/upbeat-edison-93gxck` (the environment pins it) |
| CROHMS series | `Flow-Out.Inst.1Hour.0.CBT-REV` etc. | the catalog's hourly outflow / spill / turbine-flow series are `*.Ave.1Hour.1Hour.CBT-REV` (the `Inst` form returns `{}`); forebay is `Elev-Forebay.Inst.1Hour.0.CBT-REV`, power `Power.Total.1Hour.1Hour.CBT-RAW`. Same quantities, same source, same URL — a series-id correction, not a method change |
| pull range | ≤ 3-month calls | calendar-quarter calls, 2023-01-01 → 2026-01-01; the service returns the boundary hour twice (deduplicated) |
| environment | — | the container's interpreter had no numpy/scipy/pandas/highspy/pytest/tzdata; installed from `pyproject.toml` before any measurement |

Nothing in §1–§9 of the PRECOMMIT was re-derived. The reach table, the formulation, the field, the
ledgers, the gates and the STOP rules are executed as written.

## 2. What was built

| file | what |
|---|---|
| `src/market_sim/model/lp/hydro_cascade.py` (NEW) | `HydroCascadeSpec` (the LP-ready arrays + `validate`) and `build_hydro_cascade_rows` — one `coo_matrix` per coefficient family from `np.arange(T)` and modular lag indexing; the only loop is over the O(15) links (rule 2) |
| `model/lp/layout.py` | `n_cascade` block (spill `S[c,t]`, pond `V[c,t]`) appended after `dis_tranche`; `_cas_s_off`, `_cas_v_off`, `cas_s_col`, `cas_v_col`; 0 leaves every offset and `vars_per_hour` byte-identical |
| `model/lp/rows.py` | zero energy-balance block for the water columns; the cascade rows appended right after the hydro budget rows (before oil/coal/RPS/reserve, so no dual position moves); `row_offsets` out-dict records the block for dual read-back |
| `model/lp/bounds.py`, `costs.py` | `0 ≤ S < ∞`, `0 ≤ V ≤ B_c` (the measured band); ε = `STORAGE_TIEBREAKER_EPSILON` on both columns, no other cost |
| `model/lp/model.py`, `lp/__init__.py` | `hydro_cascade` kwarg through `DispatchModel` / `solve_dispatch`; `DispatchResult.hydro_cascade_{spill,storage,water_value,plant_codes}`; the cross-year column map carries both blocks |
| `config/scenarios.py` | `hydro_cascade_coupling: bool = False` + `_CACHE_KEY_OPTIONAL_FIELDS` + `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` (`"False"`), all in the same commit, HOUSE-3 position (shared field, very end) |
| `data/hydro.py::load_hydro_cascade` | reads `data/raw/<iso>-hydro/<iso>_hydro_cascade_{links,monthly}.csv`; only `coupled` links; a coupled plant absent from the year's fleet drops with its links (logged); an upstream with no spill column (a head, an uncoupled plant) contributes its generation column and its measured monthly-mean spill on the RHS, or its measured monthly-mean outflow when it is not an LP unit that year; `None` when nothing resolves |
| `pipeline/kwargs.py::resolve_hydro_cascade`, `pipeline/spec.py` (`hydro_cascade: Any = UNSET`), `pipeline/__init__.py` | ONE resolver, wired into BOTH `runner.py` and `scripts/run_calibration.py` beside `resolve_hydro_period_hours` (the nyiso-220 lesson); `UNSET` is omitted from the kwargs so every unarmed run's key set is unchanged |
| `scripts/data/fetch_nwpp_crohms_hourly.py` (NEW) | the CROHMS pull (16 stations × 5 series × 12 quarters + the two Idaho Power daily series + the station catalog), `SHA256SUMS.txt` |
| `scripts/data/build_nwpp_hydro_cascade.py` (NEW) | the §4 measurement, gates applied verbatim, STOPs written into the artifact |
| `data/raw/nwpp-hydro/crohms/*`, `nwpp_hydro_cascade_{links,monthly,nid}.csv`, README rows | the artifacts (§3) |
| `tests/unit/model/test_hydro_cascade.py` (NEW) | the trivial 1-link/24-h tier and the real-chain reduced-system tier (§5) |
| `docs/codebase-site/data/mechanism-matrix.js` + nine shard cells | base row `hydro_cascade_coupling`; NWPP cell `O` with the measurement; eight foreign cells `·` (rule 28(c)) |

Not touched: NWPP-32's artifacts and `HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT` (still empty);
`constants.py`; `solve_surface_declared.py`; `scripts/calibration_verdict.py`; `frontend/data/**`;
the plan, the ledger, `docs/calibration-log/nwpp.md`, `CHANGELOG.md`,
`docs/mechanism-testing-matrix.md`; any other region's files. `git diff --stat` at the end: 24 files
changed, 566 insertions, **0 deletions**.

## 3. The measurement (PRECOMMIT §4)

Source: `public.crohms.org` DataQuery, 2,103,124 hourly values, **every one quality code 0**; ≤ 140
missing hours per series over three years (Dworshak the worst; 0–16 elsewhere); sentinels screened
before any statistic (−99999 in the RIS/RRH Power series, isolated 0.0 forebay readings at PRD/WEL,
a −579.3 Flow-Gen at DWR) and reported as `hours_missing_gen` in the monthly artifact.

### 3.1 τ per link (§4.1) — anomaly cross-correlation, 0..72 h

| link | u→d | τ (h) | r(τ) | r(τ−1) | r(τ+1) | r(0) | τ 2023 / 2024 / 2025 | miles | mph | verdict |
|---|---|---:|---:|---:|---:|---:|---|---:|---:|---|
| 1 | GCL→CHJ | 0 | 0.840 | — | 0.827 | 0.840 | 1 / 0 / 0 | 30.7 | — | accepted |
| 2 | CHJ→WEL | 1 | 0.479 | 0.467 | 0.441 | 0.467 | 1 / 1 / **72** | 10.9 | 10.9 | accepted (2025 hold-out disagrees: its curve peaks at the search edge, r 0.39) |
| 3 | WEL→RRH | 1 | 0.640 | 0.587 | 0.626 | 0.587 | 1 / 2 / 2 | 34.9 | **34.9** | **STOP (iii)** celerity > 30 mph |
| 4 | RRH→RIS | 1 | 0.932 | 0.814 | 0.775 | 0.814 | 1 / 1 / 1 | 16.4 | 16.4 | accepted |
| 5 | RIS→WAN | 23 | 0.328 | 0.320 | 0.269 | 0.319 | **23 / 0** / 0 | 32.7 | 1.4 | **STOP (ii)** per-year τ differ (a diurnal alias: r is flat 0.32 at 0 h and 0.34 at 23 h) |
| 6 | WAN→PRD | 0 | 0.626 | — | 0.476 | 0.626 | 0 / 0 / 0 | 16.2 | — | accepted |
| 7 | PRD→MCN | 13 | 0.354 | 0.350 | 0.333 | 0.233 | 13 / 13 / 13 | 57.0 | 4.4 | accepted (joint 2-D with IHR) |
| 8 | IHR→MCN | 0 | 0.354 | — | 0.316 | 0.354 | 0 / 0 / 0 | 29.5 | — | accepted |
| 9 | MCN→JDA | 0 | 0.667 | — | 0.610 | 0.667 | 0 / 0 / 0 | 68.9 | — | accepted |
| 10 | JDA→TDA | 0 | 0.876 | — | 0.827 | 0.876 | 0 / 0 / 0 | 22.3 | — | accepted |
| 11 | TDA→BON | 0 | 0.435 | — | 0.404 | 0.435 | 0 / 0 / 0 | 39.2 | — | accepted |
| 12 | DWR→LWG | 39 | 0.021 | 0.019 | 0.020 | 0.002 | 9 / 40 / 10 | 54.8 | 1.4 | **STOP (i)** r < 0.30 (Dworshak is ~10 % of Lower Granite's inflow; the Snake above LWG is not a CROHMS project) |
| 13 | LWG→LGS | 0 | 0.710 | — | 0.626 | 0.710 | 0 / 0 / 0 | 28.9 | — | accepted |
| 14 | LGS→LMN | 0 | 0.792 | — | 0.739 | 0.792 | 0 / 0 / 0 | 24.3 | — | accepted |
| 15 | LMN→IHR | 0 | 0.741 | — | 0.719 | 0.741 | 0 / 0 / 0 | 27.0 | — | accepted |

Every accepted peak is unique. Cumulative mainstem τ (GCL→BON = 0+1+1+1+23+0+13+0+0+0 = 39 h on
the raw peaks) is monotone in cumulative distance by construction of non-negative lags; **on the
five coupled links it is 0–1 h per link, i.e. the pooled reaches respond within the hour** — P5
("well under a day GCL→BON, the wave runs through pools") is confirmed on the links that
measured cleanly, and the two long lags (RIS→WAN 23 h, PRD→MCN 13 h, both on reaches whose
downstream project peaks on its own schedule) are exactly the ones whose r is weakest (0.33–0.35).

### 3.2 The pondage band (§4.2) — NID area × measured forebay range

| d | fed. RoR | NID | acres | NID max−normal (ft, cross-check only) | band 2023 / 2024 (ft) | used | p99 within-day range (ft) | B_d (kcfs·h) | hours of published / measured discharge |
|---|---|---|---:|---:|---|---|---:|---:|---|
| CHJ | yes | WA00299 | 8,400 | 9.17 | 3.10 / 3.10 | 3.10 | 2.50 | 315.1 | 2.9 / 3.8 |
| WEL | no | WA00098 | 9,700 | 17.42 | 8.77 / 5.16 | 5.16 | 4.80 | 605.8 | — / 7.0 |
| RRH | no | WA00086 | 9,810 | 0.82 | 2.83 / 2.81 | 2.81 | 2.83 | 333.6 | — / 3.9 |
| RIS | no | WA00084 | 3,120 | 5.54 | 2.37 / 2.50 | 2.37 | 2.54 | 89.5 | — / 1.0 |
| WAN | no | WA00085 | 14,590 | 14.12 | 7.44 / 6.38 | 6.38 | 4.54 | 1,126.3 | — / 12.1 |
| PRD | no | WA00088 | 7,580 | 0.00 | 5.11 / 5.17 | 5.11 | 4.67 | 468.9 | — / 5.1 |
| MCN | yes | OR00616 | 38,800 | (NID max storage 0) | 2.27 / 2.13 | 2.13 | 1.16 | 1,000.0 | 5.9 / 7.6 |
| JDA | yes | OR00011 | 55,000 | 36.36 | 3.21 / 3.01 | 3.01 | 1.10 | 2,003.2 | 11.6 / 14.7 |
| TDA | yes | OR00002 | 11,200 | 4.73 | 2.17 / 1.92 | 1.92 | 2.03 | 260.3 | 1.5 / 2.0 |
| BON | yes | OR00001 | 20,600 | 12.62 | 4.00 / 4.00 | 4.00 | 2.20 | 997.0 | 5.4 / 6.9 |
| LWG | yes | WA00349 | 8,900 | (NID max storage 0) | 4.29 / 4.13 | 4.13 | 1.81 | 444.8 | 9.0 / 11.2 |
| LGS | yes | WA00331 | 10,025 | 0.00 | 4.39 / 4.32 | 4.32 | 1.98 | 524.4 | 11.1 / 13.6 |
| LMN | yes | WA00270 | 6,590 | 8.35 | 2.45 / 2.28 | 2.28 | 1.63 | 181.9 | 3.8 / 4.7 |
| IHR | yes | WA00347 | 8,375 | (NID max storage 0) | 2.40 / 2.32 | 2.32 | 1.58 | 235.2 | 4.9 / 5.9 |

Every federal run-of-river band lies inside the 0.5–15 ft sanity band — **1.9–4.3 ft against BPA's
published "three to five feet"** — so no plant STOPs on its band. The NID `Max − Normal` column is,
as the PRECOMMIT anticipated, not an operating band (0.8 ft at Rocky Reach, 0 or undefined at four
Corps projects whose NID max storage is filed as 0) and was used for nothing. The p99 within-day
range (1.1–4.8 ft) is the tighter "pondage actually exercised daily" statistic — reported, not used.

### 3.3 η per plant-month (§4.3)

η = EIA-923 net MWh ÷ Σ CROHMS `Flow-Gen` (kcfs·h), per plant and calendar month, 2023–2025:
CHJ 13.0–13.4, GCL 19.4–26.5, DWR 39.6–46.8, JDA 7.0–7.9, TDA 5.7–6.4, BON 3.5–5.0, MCN 4.4–5.1,
RRH 6.4–7.2, WEL 4.4–5.3, WAN 5.6–6.0, PRD 5.3–5.9, RIS 2.5–3.2, LWG/LGS/LMN 6.0–7.4, IHR 6.6–7.6
MWh per kcfs·h. The EIA-923-net ÷ CROHMS-gross ratio (`eta_net_over_gross`) lies in **0.965–1.02
at 13 of 16 plants**, the expected 0.97–1.00 band; the exceptions are Grand Coulee (0.82–1.07 —
its `Power.Total` and EIA-923 `HY` disagree month to month around the pump-generating plant) and
McNary / John Day (0.88–0.95 in some months). Reported, not adjusted. Substitutions per the rule:
**McNary 2025 and Dworshak 2025** (`NO_923_SERIES` in NWPP-32's artifact) take each month's η from
2024. Missing turbine-flow hours (≤ 69 per plant-year) are scaled to the full month, stated in the
artifact's `hours_missing_gen`.

### 3.4 Side inflow and head flows (§4.4)

Measured monthly means of `Flow-Out_d + ΔV_d − Σ_u Flow-Out_u(t−τ)` in kcfs, ΔV from the forebay
series × NID area (so a month that drew its pond down is not booked as inflow):

| d | mean side inflow (kcfs) | months negative | max floor / arriving | months over the 2 % STOP |
|---|---:|---:|---:|---:|
| CHJ | 0.62 | 5 | 1.8 % | 0 |
| WEL | 4.34 | 1 | 0.4 % | 0 |
| RRH | 0.12 | 27 | 3.3 % | **6** |
| RIS | 3.63 | 0 | 0 | 0 |
| WAN | 3.76 | 0 | 0 | 0 |
| PRD | 0.09 | 34 | 3.5 % | **13** |
| MCN | 2.33 | 16 | 3.8 % | **6** |
| JDA | 4.33 | 7 | 4.9 % | **3** |
| TDA | 0.50 | 21 | 8.4 % | **15** |
| BON | 11.64 | 0 | 0 | 0 |
| LWG | 35.63 | 0 | 0 | 0 |
| LGS | 0.09 | 22 | 6.8 % | **13** |
| LMN | 0.47 | 12 | 2.6 % | **1** |
| IHR | 0.80 | 11 | 1.9 % | 0 |

The floors are not noise and not my arithmetic: they concentrate in **April–August at the
federal lower-river and lower-Snake projects and scale with spill** (The Dalles: −3.4 % in April,
−7.2 to −8.4 % in June–July of both years, when 50–140 kcfs is spilling; annual outflow ratio
TDA/JDA 0.970, LGS/LWG 0.971), i.e. a spill-discharge metering artefact between adjacent gauges,
exactly the "metering or timing artefact" the PRECOMMIT's floor rule names. The rule says a
plant-month floor above 2 % of arriving water STOPs the link, and it is applied as written:
**seven links STOP on it** (RRH←WEL, PRD←WAN, MCN←PRD/IHR, JDA←MCN, TDA←JDA, LGS←LWG, LMN←LGS).
Head spill means: GCL 0.10 / 0.04 / 0.02 kcfs (2023/24/25), DWR 0.06 / 0.07 / 0.10 — the heads
spill almost nothing on the annual mean.

### 3.5 Verdict — five coupled links, ten uncoupled, none substituted

| link | verdict | reason |
|---|---|---|
| GCL→CHJ, CHJ→WEL, RRH→RIS, TDA→BON, LMN→IHR | **coupled** | every gate cleared |
| WEL→RRH | uncoupled | τ (iii): implied celerity 34.9 mph |
| RIS→WAN | uncoupled | τ (ii): 2023 τ 23 h vs 2024 τ 0 h |
| DWR→LWG | uncoupled | τ (i): r 0.02 |
| WAN→PRD, PRD→MCN + IHR→MCN, MCN→JDA, JDA→TDA, LWG→LGS, LGS→LMN | uncoupled | side-inflow floor > 2 % of arriving water in 13 / 6 / 3 / 15 / 13 / 1 plant-months |
| Brownlee→Oxbow→Hells Canyon | never in scope | daily-only on CROHMS (PRECOMMIT §2), the daily series committed for the record |

So the delivered coupling is **five coupled plants — Chief Joseph, Wells, Rock Island, Bonneville,
Ice Harbor: 5,717 MW = 16.0 % of NWPP conventional-hydro nameplate** — below two heads (Grand
Coulee, Dworshak-less: Lower Granite's head link failed) and three UNCOUPLED upstreams (Rocky
Reach, The Dalles, Lower Monumental) whose generation column enters the row and whose measured
monthly-mean spill enters the RHS. The PRECOMMIT's reach table (14 coupled, 16,637 MW) is what the
measurement was asked to deliver; **it delivered a third of it**, and the reason is a property of
the source data the PRECOMMIT's own rules were written to catch, not a modelling choice. What would
recover the other ten links is stated in §7, and is a new PRECOMMIT, not this lane's.

## 4. Byte identity (PRECOMMIT §6)

### 4.1 Keeper `cache_key()` — nine regions, base `6d1a144d` vs head

Re-keyed by `ScenarioConfig(**run_config["scenario_config"]).cache_key()` on a sparse worktree at
the base sha and on the branch head, stored absolute paths re-rooted onto each tree, importing
`market_sim` from each tree's own `src` (asserted). **25 of 25 identical.**

| region | keeper (from `keepers/<ISO>.json` at base — unchanged from the PRECOMMIT) | config(s) | key (base = head) |
|---|---|---|---|
| ERCOT | `2026-09-09-ercot265-receipts-fallback` | `run_config.json` / `_forward_2024_2025` | `0f89d4c5f45043f7` |
| | | `_carveout_2021_2022` | `134b04a671c81d61` |
| | | `_carveout_2023` | `c30e0c40f1d5dee2` |
| CAISO | `2026-09-12-caiso-275-gascoupling` | `run_config.json` / `_2023` | `bab5e9b08681e54c` |
| | | `_2024` | `2e44a9d55550e56a` |
| | | `_2025` | `3506d4d485ff212e` |
| PJM | `2026-09-11-pjm-d4-4-gasoutage` | `run_config.json` | `b05e09c319c2c5f5` |
| MISO | `2026-09-12-miso-255-sil-measured` | `run_config.json` / `_2023` | `b35a8f20b73a5fbf` |
| | | `_2020` / `_2021` / `_2022` | `3a0d04116c118479` / `bc66008dae312904` / `f378aaf652de32b5` |
| | | `_2024` / `_2025` | `dd3ad6888d090e2c` / `4e5ff5fac1b84abf` |
| NYISO | `2026-09-14-nyiso-235-gas-repair` | `run_config.json` | `4df176fd40335d4a` |
| NEISO | `2026-09-09-neiso-108-fuelvintage` | `run_config.json` | `28266b333667e16f` |
| SPP | `2026-09-13-spp-38-vintage-cache` | `run_config.json` | `6d6205e381e982c2` |
| SOCO | (no keeper) | `ScenarioConfig(iso="SOCO")` / backcast | `98e45f524d922839` / `63cf200dd91f6ad9` |
| NWPP | (no keeper) | `ScenarioConfig(iso="NWPP")` / backcast | `4e9a865340b97c0b` / `ec6346d7378c35fe` |
| pins | | `ScenarioConfig()` / `mode="backcast"` | `9ca2c6052b4850ea` / `c5345ea9bc1cf730` |

### 4.2 LP identity and the guards

| check | result |
|---|---|
| sha256 over `(A.indptr, indices, data, row bounds, col bounds, cost, layout)` — hydro fleet fixture, 24 h | base `bed13e69…` = head `bed13e69…` OFF; ARMED `6cac8fdb…` (72 rows × 240 cols vs 48 × 192) |
| same, 720 h | base `f97b5bd3…` = head `f97b5bd3…` OFF; ARMED `6b4eadf8…` |
| `check_cache_key_registration.py --base 6d1a144d` | ok: 1 new field, registered; 305 registered, 305 declared defaults match; 305 solve-surface names declared |
| `solve_surface_register.py --diff 6d1a144d HEAD` | 305 → 305 names, 0 moved, 0 added, 0 removed |
| `check_mechanism_matrix.py --base 6d1a144d` | ratchets OK; only the pre-existing NYISO stamp-drift warnings (NYISO's lane) |
| `ruff check` / `ruff format --check` on every touched file | clean |
| `tests/unit/data/test_hydro.py` (the budget family) | 112 passed |
| unit lanes `tests/unit/{model,data,pipeline,config}` + `tests/regression/test_persisted_identity.py` | see §4.3 |

### 4.3 Unit lanes

First run (before `tzdata` was installed): 2,069 passed, 2 failed, both outside this lane's files
and neither touching hydro — `test_firm_import_selfschedule` (`ZoneInfoNotFoundError: US/Pacific`,
the container had no `tzdata` package) and `test_caiso_st_gas_peak_measured::
test_registry_value_matches_the_committed_artifact` (1.154 ≠ 1.166, a CAISO registry-vs-artifact
check on files this lane never touched). Second run after installing `tzdata`, no `-x`:
**4,892 passed, 44 skipped, 8 failed** — `test_persisted_identity::test_solve_surface_fingerprint_is_pinned[NYISO]`,
`test_caiso_st_gas_peak_measured` (1), `test_gas_offer_zonal_anchor_vintage` (2),
`test_data_profiles_tokens::test_soco_token_collides_with_no_other_raw_name`,
`test_mechanism_matrix_keeper_stamp` (2, the NYISO stamp drift the matrix guard already warns on),
`test_fleet::test_neiso_includes_mystic_cc`. **All eight fail identically on a detached checkout of
the base sha `6d1a144d` in this same tree with the same hydrated data** (re-run there, 8 failed in
2.3 s, then returned to the branch) — pre-existing, in NYISO / CAISO / NEISO / SOCO / gas-anchor
files this lane never touched; none is routed here beyond noting them. Every test touching the
files this lane changed passes (`test_hydro.py` 112, `test_hydro_cascade.py` 11 + 1 strict xfail).

## 5. The armed response (PRECOMMIT §7)

`tests/unit/model/test_hydro_cascade.py::TestColumbiaChainReduced`: the sixteen chain plants at
EIA-860 nameplate with NWPP-32's EIA-923 monthly budgets, the measured spec sliced to the month,
one zone, a three-class gas stack ($30 / $80 / $200, 30 GW each), demand shaped as BPAT's own
EIA-930 hourly demand for the month and scaled so the chain supplies 55 % of energy; January 2023
and May 2023, each solved OFF (budget only) and ON. Both solve `Optimal` in < 1 s.

| plant | month | E_off (MWh) | E_on | amp OFF → ON | peak OFF → ON (MW) | LP spill (kcfs·h) | pond max / B | arrivals mean (kcfs) |
|---|---|---:|---:|---|---|---:|---|---:|
| CHJ | Jan | 837,261 | 837,261 | 2.339 → 2.131 | 2456 → 2456 | 75 | 0 / 315 | 84.6 |
| WEL | Jan | 319,732 | 319,732 | 2.153 → 2.088 | 867 → 867 | 800 | 0 / 606 | 86.0 |
| RIS | Jan | 204,144 | 204,144 | 2.489 → 2.394 | 629 → 606 | 447 | 0 / 89 | 89.7 |
| BON | Jan | 440,086 | 440,086 | 2.045 → 2.027 | 1162 → 1162 | 2,358 | 0 / 997 | 129.9 |
| IHR | Jan | 131,774 | 131,774 | 4.275 → 3.825 | 603 → 603 | 346 | 0 / 235 | 24.4 |
| GCL (head) | Jan | — | — | **3.714 → 2.151** | | | | |
| CHJ | May | 1,280,479 | 1,280,479 | 1.466 → 1.431 | 2456 → 2456 | 11,428 | 0 / 315 | 146.9 |
| WEL | May | 421,654 | 421,654 | 1.577 → 1.573 | 867 → 867 | 31,895 | 0 / 606 | 171.8 |
| RIS | May | 216,291 | 216,291 | 2.268 → 2.197 | 629 → 602 | 50,258 | 0 / 89 | 183.0 |
| BON | May | 457,095 | 457,095 | 1.980 → 1.958 | 1162 → 1162 | 125,412 | 0 / 997 | 345.4 |
| IHR | May | 149,248 | 149,248 | 3.438 → 3.295 | 603 → 603 | 77,484 | 0 / 235 | 134.6 |
| GCL (head) | May | — | — | 2.327 → 2.240 | | | | |

| gate | verdict | measured |
|---|---|---|
| **G-A1** rule-19 invariant | **PASS** | every coupled plant's monthly energy identical ON vs OFF (0.000 % move) in both months — both equal the budget |
| **G-A2** identity | **PASS** | row residual 0 to 1e-5; `P_d/η ≤ arrivals + V(t−1)` every coupled plant-hour |
| **G-A3** direction & magnitude, January | **FAIL** | amplitude reductions CHJ 8.9 %, RIS 3.8 %, BON 0.9 %, IHR 10.5 % — median ≈ 6 %, against the pre-registered ≥ 30 %; RIS's peak 606 MW exceeds the flat-arrivals bound η·(Q̄_arr + B) = 552 MW because Rocky Reach, its UNCOUPLED upstream, peaks into it |
| **G-A4** spill season | **PASS** | May: Σ S_BON > 0, and LP monthly spill at BON and IHR within ±10 % of the measured CROHMS monthly spill (closes by construction, P4 confirmed); January: LP spill ≤ measured + 5 % of arrivals at every coupled plant |
| **G-A5** lag signature | **PASS** | on every link with B_d ≤ 6 h of flow, r(P_d(t), P_u(t−τ)) is higher ON than OFF |
| **G-A6** OFF identity | **PASS** | §4.2 |

**Why G-A3 fails, and what the mechanism actually does.** The gate assumed a coupled plant's
arrivals are near-flat so that ponding, not inflow, sets its peak. In the LP the arrivals are the
UPSTREAM plant's own dispatch, and every coupled link measured at τ = 0–1 h: Chief Joseph's hourly
shape is Grand Coulee's (r > 0.99 ON), Rock Island's is Rocky Reach's, Bonneville's is The Dalles'.
With one price signal in the reduced system the upstream already peaks in the hours the
downstream would choose, so the pond is never drawn (0 / B at every plant in both months) and the
coupled plant's amplitude is bounded by the upstream's, not reduced by 30 %. The redistribution the
rows DO produce is upward: Grand Coulee cannot release 199 kcfs into a Chief Joseph that can turbine
184 (2,456 MW at η 13.3) without spilling water Chief Joseph needs for its own budget, so Grand
Coulee's January amplitude falls from 3.71 to 2.15 and Chief Joseph's peak is held at nameplate.
That is hydraulic succession expressed correctly — a head's peaking is limited by the plant below it
— and it is the ONLY within-month redistribution a 0-h link can add on top of the budget when the
two plants face the same price. The magnitude prediction P2 (ON amplitude ≤ 0.8 at BON/TDA/JDA) was
therefore wrong in its premise; the direction the gate asked for (a coupled run-of-river plant
cannot shape independently of the plant above it) is what the ON dispatch shows. With three of the
five coupled plants sitting below an UNCOUPLED upstream that keeps its full 1/CF freedom (a
consequence of §3.5), the shape they inherit is the budget LP's, not the river's.

Predictions scored: P1 (G-A1 leak < 0.2 %) **confirmed, 0.000 %**; P2 **refuted** (above); P3 (the
head's shape nearly unchanged) **refuted in January** — GCL's amplitude is what moves most; P4 (May
spill closes within ±5 %) confirmed at the ±10 % gate (the test asserts the gate); P5 (τ well under
a day GCL→BON) **confirmed on the coupled links** (0–1 h each).

The trivial tier (1 zone, 1 link, 24 h: OFF identity, +2 columns and +T rows ARMED, invariant,
identity, lag signature, zero-budget feasibility) passes 6/6; the chain tier passes 5 with G-A3
encoded as a **strict expected failure** (`xfail(strict=True)`) so CI is green today and turns red
the day the measured chain changes enough for the gate to pass — a re-read trigger, not a hidden
result.

## 6. What this lane delivers, and the question it cannot answer

Delivered against the charter's exit: the mechanism (default-off, one field, both ledgers, one
commit); the matrix base row and nine cells; the nine-region keeper byte-identity table (all
identical); the OFF-identity proof (sha256); the armed-response measurement on the real chain. The
mechanism arms, changes no monthly total, produces the spill object the ROD season needs, and
transmits capacity constraints up the chain.

What it does NOT deliver: the reach the PRECOMMIT's table asked for. Ten of fifteen links are
uncoupled by the PRECOMMIT's own measurement gates — three on τ and seven on a 2 % side-inflow floor
that the source data's spill-season gauge artefact trips at every federal lower-river project. As
built, arming `hydro_cascade_coupling` on the NWPP footprint couples 16 % of hydro nameplate, not
66 %, and at test scale the within-month redistribution it adds over the monthly budget is small
(amplitude 1–10 %, Grand Coulee's own shape the largest move). **My recommendation is that
NWPP-40 does NOT arm it for the first keeper in this state**, because 5 links coupling three plants
to uncoupled upstreams is not the object ruling N3 named; the mechanism should be armed after the
follow-up in §7 recovers the lower-river links. **That is a recommendation, not a decision (rule 31)
— the owner routinely promotes what a session declined, and the field is built so that arming it is
one flag on NWPP-40's recipe.** Nothing was solved that needs retaining: no bundle, no shard, no
gitignored directory; the artifacts are committed.

## 7. Routed to NWPP-DESK (not fixed here — outside FILES YOU OWN or outside this PRECOMMIT)

1. **The side-inflow floor rule (§3.4) is what uncouples the lower river, and it is a measurement
   rule, not a physics one.** A follow-up PRECOMMIT could (a) compute side inflow from the
   TURBINE-flow balance (`Flow-Gen` is metered far better than `Flow-Spill`) with spill carried as
   its own measured term, or (b) declare a per-link gauge reconciliation (annual outflow ratios
   0.970–0.993) under rule 14's misalignment clause and re-measure. Either recovers seven links;
   neither is admissible after the numbers were seen without its own PRECOMMIT.
2. **WEL→RRH** fails only the 30 mph celerity ceiling at τ = 1 h over 34.9 river-adjacent miles
   (2024 alone reads 2 h = 17 mph and passes). A τ search at half-hour resolution, or the celerity
   bound applied to the per-year τ, would decide it — a PRECOMMIT amendment.
3. **RIS→WAN** is a diurnal alias (r flat 0.32–0.34 between 0 h and 23 h); a de-diurnalised
   anomaly (subtract the mean daily cycle as well as the 25-h trend) is the obvious re-measure.
4. **DWR→LWG** cannot be coupled from CROHMS alone: the Snake above Lower Granite (Hells Canyon +
   Salmon + Grande Ronde + Clearwater) enters as side inflow and Dworshak is ~10 % of it. Lower
   Granite is correctly on its monthly budget until that inflow is measured (USGS 13334300 Snake
   near Anatone + 13342500 Clearwater at Spalding are the gauges).
5. Persisting `hydro_cascade_{spill,storage,water_value}` into the calibration bundle's `hourly/`
   sidecars is `scripts/run_calibration_full.py`'s (NWPP-40's) — the arrays exist on
   `DispatchResult` now.
6. `docs/codebase/` (the LP layout inventory) and `CHANGELOG.md` gain a line for the `n_cascade`
   block and the field at the desk's refresh (`/sync-docs`); this lane touched no shared record.
7. `check_mechanism_matrix.py` still warns on the NYISO keeper-stamp drift (`nyiso-232` vs
   `nyiso-235`) — pre-existing, NYISO's lane.

## Log entry

```
## NWPP-36 — 2026-09-16 — Columbia mainstem hydraulic coupling (owner ruling N3) — BUILT, MEASURED, ARMED AT TEST SCALE; G8 PASS; G-A3 FAIL as pre-registered; 5 of 15 links couple
Base 6d1a144d, branch claude/upbeat-edison-93gxck, DATA PROFILE nwpp, zero calibration LP. Executes
PRECOMMIT-nwpp-36-2026-09-16.md as binding (fresh session; the first lane pushed only the PRECOMMIT).
FIELD: ScenarioConfig.hydro_cascade_coupling (default off) + both cache-key ledgers in one commit;
loader data/hydro.py::load_hydro_cascade, ONE resolver pipeline/kwargs.py::resolve_hydro_cascade in
BOTH orchestrators; LP family model/lp/hydro_cascade.py (n_cascade block after dis_tranche, one hourly
water-balance equality per coupled plant, spill S >= 0 and pond 0 <= V <= B, epsilon cost only).
G8: all 25 keeper/default cache keys byte-identical base -> head (nine regions); LP sha256-identical
OFF at base and head for both fixtures, differs ARMED; cache-key guard, solve-surface diff (0 moved),
matrix guard, ruff all clean. MEASUREMENT (CROHMS hourly 2023-2025, 2.10 M values all quality 0; NID
2026-09-11; EIA-923): tau GCL->CHJ 0 h, CHJ->WEL 1, RRH->RIS 1, TDA->BON 0, LMN->IHR 0 (coupled);
WEL->RRH STOP celerity 34.9 mph; RIS->WAN STOP per-year tau 23 vs 0 (diurnal alias); DWR->LWG STOP
r 0.02; seven links STOP on the 2 % side-inflow floor in Apr-Aug (downstream metered outflow 2-8 %
below upstream at the federal lower-river projects, a spill-metering artefact). Bands 1.9-6.4 ft
(federal RoR 1.9-4.3 vs BPA's published 3-5), 89-2,003 kcfs.h. RESULT: 5 coupled plants (CHJ WEL RIS
BON IHR, 5,717 MW = 16 % of NWPP hydro nameplate). ARMED TEST (real chain, Jan + May 2023): G-A1
PASS (0.000 % monthly-energy move, rule 19), G-A2 PASS (1e-5), G-A4 PASS (May spill closes on CROHMS
within 10 % at BON/IHR), G-A5 PASS, G-A3 FAIL (amplitude falls 1-10 %, not >= 30 %: a coupled plant
inherits its upstream's shape; Grand Coulee's own Jan amplitude 3.71 -> 2.15 is the move). Encoded as
xfail(strict). RECOMMENDATION (not a decision, rule 31): NWPP-40 does not arm it until the seven
lower-river links are re-measured under a follow-up PRECOMMIT (turbine-flow balance or a declared
gauge reconciliation). Matrix: base row + NWPP cell O + eight foreign cells. Artifacts under
data/raw/nwpp-hydro/{crohms/,nwpp_hydro_cascade_{links,monthly,nid}.csv}; scripts/data/
{fetch_nwpp_crohms_hourly,build_nwpp_hydro_cascade}.py; tests/unit/model/test_hydro_cascade.py.
FINDING-nwpp-36-2026-09-16.md.
```
