# PRECOMMIT — SOCO-40: the first-ever SOCO solve, the rule-29 screen, and the first keeper

**Lane** SOCO-40 · **Model** Fable (`claude-fable-5-1`) · **Date** 2026-09-16 ·
**Branch** `claude/soco-40-first-keeper-mxma` · **Data profile** `soco` ·
**Charter** `docs/multi-iso/soco-addition-plan-2026-09.md` §8 W4 (issued r#9, pinned `a2dc6d3a`) plus
the r#10 ADDENDUM; §1 rows 2/5/7; §3 cards S2 / S3 / S4 / S5 / S6 / S7 / S12; §5 row SOCO-40;
§7 gates G4 / G5 / G6 / G13 / G17 / G19 / G20 / G21.
**Predecessors** FINDING-soco-30 / 31 / 32 / 33 (W3, all on `main`), FINDING-soco-13 (the price
VERDICT: NO), FINDING-soco-22 (rubric v3.8), FINDING-soco-15 (the COD seam), FINDING-soco-34 (site).
**Rules that bind** 1 `[R-STRUCT]`, 12 `[R-PARALLEL]`, 13 `[R-MEASURED]`, 15 `[R-DASHBOARD]`,
16 `[R-ALLYEARS]`, 20 `[R-FORCED-BUDGET]`, 21 `[R-DOF]`, 22 `[R-C3C]`, 29 `[R-SCREEN]`,
31 `[R-RETAIN]`, 32 `[R-SHARD]`, 33 `[R-SHARD-ARCHIVE]`, 34 `[R-SHARD-PROMOTABLE]`, 35 `[R-PROMOTE]`.

**Pushed before any solve.** Every number below is ZERO-LP: `get_iso_config`, the CLI's own
`backcast_config` construction (its argparse defaults captured without invoking the runner), the
fleet / demand / renewable / hydro / storage / interchange loaders called directly, and the committed
W3 artifacts read. No `run_calibration.py` smoke, no 24-hour recipe dump, no LP of any length ran in
this session (rule 32(a): the parent never solves — not "just the smoke"). The STOP gate, the screen
year, the recipe, the price posture and the DOF ledger are fixed here; nothing is revised after a
solve is read, and a miss of any declared condition is reported at full magnitude in the FINDING.

---

## 0. The pin and the preconditions

The charter pinned `a2dc6d3a`, which PREDATES SOCO-32 (merged `af764ec8`, PR #6205, its own
precondition). The lane therefore bases on the `origin/main` that carries it:

```
89a500b783957036bd1b3ff813891ed1a8ddf3dc   origin/main at PRECOMMIT time (branch base; SOCO-32 at af764ec8, desk r#10 at 621de208)
<sha of the commit carrying this file>     the shard pin — a FULL 40-char SHA, recorded verbatim in each shard prompt and in the FINDING
```

| precondition | check | result |
|---|---|---|
| SOCO-30 landed | `git log origin/main --grep=SOCO-30` | PRs #6179 / #6181 — **yes** (`data/raw/campd-unit-outages-SOCO.csv` 1,119 windows: 332 / 355 / 432 starting in 2023 / 2024 / 2025; `thermal_tranches_SOCO.csv` present, NOT read by this recipe — §4.1) |
| SOCO-31 landed | `--grep=SOCO-31` | PR #6185 — **yes** (`calibration_reference.json` SOCO block 2023–2025, three `SOCO_<yr>_renewable_capacity.csv`) |
| **SOCO-32 landed** | `git log origin/main --grep=SOCO-32` → `af764ec8` `99dc674b` `2c692a4f` `a05347a8` `31517355` | **yes** — gate G4 fully discharged (desk r#10) |
| SOCO-34 | PR #6191 merged 04:43:09 UTC | yes — the charter's "register anyway" clause is moot |
| rule 12: another per-plant solve running? | `list_sessions` at launch | **no** — the only other RUNNING sessions are three NWPP desk-charter sessions (no LP); no SOCO-DESK session exists to message, so the check is recorded here |
| `actual_lmp.json` has NO SOCO block | `grep -c SOCO data/raw/_validation-source/actual_lmp.json` | **0** — and it MUST stay 0 (§1) |

---

## 1. THE PRICE POSTURE, FIXED BEFORE THE SOLVE (charter item (a); card S2; rubric v3.8)

- **No public SOCO price exists and none will be built or borrowed.** Southern Company publishes no
  LMP; SEEM publishes matched volumes, no price. SOCO-13 built the FERC-EQR candidate behind a STOP
  gate pre-registered before any data was read and the gate read **NO** — D2.2 volume share 3.66 /
  2.69 / 2.64 % against a 5 % bar, D3.1 level +11.7 / +54.2 / +72.1 % against ±15 %, D4.2 2.008
  against 0.8–2.0; no bar moved after the series was seen.
- **Gate G17 is absolute.** No MISO-South hub, no TVA / PJM proxy, no EIA state average, no
  cost-stack "price" enters `actual_lmp.json`, the bench parts, or this lane's reasoning. The
  committed reference file's top-level keys are the seven price-carrying ISOs (plus none); the string
  `SOCO` appears in it **0** times, and an empty or placeholder block would break
  `calibration_verdict._price_reference_absent("SOCO")`, which keys on ABSENCE.
- **The determination class is rubric v3.8's** `PHYSICALLY-CALIBRATED (PRICE UNSCORED)` or
  `PHYSICALLY-CALIBRATED-WITH-CAVEATS (PRICE UNSCORED)` — or `NOT-YET`. **It can NEVER read
  `CALIBRATED`**, whatever the run does. Scored on **C1 / C2 / C4 / C6 / C8 only**. **C3a / C3b /
  C3c are UNSCORABLE, NOT FAILED**: they are reported as `UNSCORABLE`, consume no caveat slot, and the
  rule-22 C3c standing rule never fires because there is no C3c.
- **The price gap is reported at FULL MAGNITUDE on the determination basis**: the scorer prints the
  model's own load-weighted mean price per year, labelled MODEL-ONLY and UNVERIFIED, and the FINDING
  repeats it in those words. It is never treated as absent and never dressed as a scored number.
- TAIL_THRESHOLD and amplitude stay SKIPPED (gate G6's pre-specified branch, card S9 n/a). SOCO-31
  verified the skip by execution. This lane registers no threshold.

---

## 2. THE SCREEN YEAR: **2024** (charter item (b)) — a structural criterion, never a residual

There is no residual: SOCO has never been solved. The criterion is *the year that exercises the most
novel objects at once on the cleanest measured input*. Phase-0 measurements (§4) confirm the desk's
reading and add one more reason:

| object | 2023 | **2024** | 2025 |
|---|---|---|---|
| EIA-930 balance identity `NG − D − TI` | exactly 0 every hour | **exactly 0 every hour** | 633 nonzero hours, −0.6963 TWh (SOCO-31 §4.4) |
| demand artifacts | — | — | one-hour partial post `min_mw` 12,638 MW (SOCO-31 §4.3); 7 trailing UTC hours flat-filled |
| span peak | 45,558 (summer) | **47,368 MW, 2024-01-17 07:00 — the span's winter peak** | 46,490 (winter) |
| Vogtle 3 / 4 | 3 from July; 4 absent | **both in service for three quarters** (3 all year, 4 from April) | both all year |
| EIA-923 vintage | final | **final** | preliminary: 6 / 23 `CT_PEAKER` and 1 / 6 `CC_CHP` plants filed (SOCO-31 §4.5) |
| EIA-923 hydro budget the LP reads (§4.5) | 42 plants, 6.8150 TWh | **42 plants, 6.3015 TWh** | **5 plants, 0.3275 TWh against 6.01 TWh actual** — an input-vintage hole |
| pumped-storage comparator (R-i) | none | none (24 h) | present |

2025 is the year in which a data artifact would be graded as a structural failure; 2023 lacks
Vogtle 4 and the winter peak. **2024 is the screen year.** Pre-registered here; not revisited.

---

## 3. The recipe — every value fixed before the solve

### 3.1 The invocations (the shards' exact command lines)

```
uv run python scripts/run_calibration_full.py --iso SOCO --year 2024 \
    --out-dir results/calibration/_soco40_screen \
    --note "soco-40 screen 2024 (rule 29(a) throwaway probe; never registered; numbers live in PRECOMMIT/FINDING-soco-40)"

uv run python scripts/run_calibration_full.py --iso SOCO --year 2023 2024 2025 \
    --out-dir results/calibration/soco40_baseline_B \
    --note "soco-40 first SOCO solve: all-defaults baseline, three geographic zones on measured FERC-714 shares, Tier-3 non-binding links (24,400 / 4,300 MW), served EIA-930 interchange (card S4), VOLL 61,900 (card S5), every offer band 1.0, authorized_price_tuning NONE"
```

**No other flag.** No `--commitment`, no `--enable-legacy-p2`, no `--run-p2` (P2 is archived; the
shard STOPs if any appears). No `--set`, no `--offer-curve-json`, no `--hydro-backfill-year`, no
`--hydro-eia930-monthly` (§6 names the 2025 hydro hole and routes it; arming a repair for one year
inside the first keeper is a lever decision the desk queue owns, not this lane's). Years run
**sequentially in one invocation** (rule 12), one bundle (rules 16 / 32(b)). The runner runs
UNMODIFIED with its own `ensure_solve_container` preflight (no `--no-container-preflight`).

### 3.2 What the recipe is — the CLI's ISO-agnostic backcast construction, measured zero-LP

`argparse` defaults captured for `--iso SOCO --year 2024` without running the solver:
`coal_prb_sigmoid=True`, `prb_sigmoid_tiered=True`, `coal_mustrun_per_plant=True`,
`coal_drop_pof=True`, `outage_source="historic"`, `coal_prb_passthrough=1.0`, `hydro_year="normal"`.
`backcast_config(year, "SOCO", 8760, <Henry Hub>)` with those kwargs yields **849 `ScenarioConfig`
fields, 28 non-default** — every one set by `pipeline/backcast_config.py`, none by this lane:

| field | recipe value | dataclass default | why |
|---|---|---|---|
| `mode` / `iso` | backcast / SOCO | forecast / ERCOT | the backcast construction |
| `plant_level_fleet`, `cc_committed_per_plant`, `cc_peaking_per_plant`, `cc_duct_peaking`, `coal_mustrun_per_plant`, `chp_steam_following` | true | false | per-plant EIA-860 fleet + per-plant CAMPD tranche structure |
| `outage_source` / `historic_outage_overlay` / `coal_drop_pof` / `correlated_forced_outage` | historic / false / true / false | statistical / true / false / true | measured unit-level outage windows (SOCO-30, 1,119 windows) in place of statistical draws |
| `gas_plant_monthly_fuel_pricing`, `nearby_fuel_price_fallback`, `gas_st_startup_spread`, `f923_gas_price_plausibility_screen` | true | false | measured EIA-923 delivered fuel (29 of 67 fossil plants file own prices in 2024; the rest gap-fill from state/zone — §4.6) |
| `gas_price_override` | 2.54 / 2.19 / 3.52 by year | None | measured Henry Hub (`_henry_hub_actual`) |
| `coal_prb_passthrough_sigmoid`, `coal_prb_passthrough_tiered` | true | false | CLI defaults; **inert for SOCO** — SOCO coal carries `plant_group` `COAL` (16 units, no `COAL_PRB` / `COAL_BIT` class in the fleet), so no sigmoid engages |
| `cc_capacity_reconcile_path` | `cc_capacity_reconcile_SOCO.csv` | ERCOT file | ISO-keyed; **`cc_capacity_reconcile` is False** and the file does not exist, so the path is inert. The four corrupt EIA-860 CC rows are reconciled at fleet load by the trusted-bound guard instead (§4.1) |
| `rps_enabled` / `datacenter_load_path` / `entry_lookahead_reprice` / `storage_entry_*` / `capacity_market_clearing_by_iso` | false / off / false / false / None | forecast defaults | forecast-only machinery a backcast never enters |
| `wefor_multiplier` | **0.7** | 1.0 | the CLI's non-MISO default — an inherited generic scalar, ledgered in §8, **not** re-chosen |
| `offer_curve_by_group` | 13 groups | {} | **every band SOCO carries is 1.0** — §3.3 |

`use_campd_bins` reads `True` in the config and is **inert**: `load_or_synthesize_bins(cfg, "SOCO",
…)` returns `None` because SOCO is absent from `CAMPD_BINNING_ISOS` (measured, all three years), so
the fleet takes the legacy `aggregate_fleet` path with `plant_level_fleet=True` (one LP unit per
EIA-860 generator). This is also the reconciliation the charter asked for (§4.1).

**Per-year cache keys of the recipe** (the run_config.json of the shard must reproduce them, or the
shard solved a different recipe): 2023 `e8e76d903a5c3916` · 2024 `33a2a47b3206274b` ·
2025 `0c1568b5f7031c13`.

### 3.3 Offer arrays — rule 25 measured at the config, gate G5

`build_offer_curve_overrides.py --iso SOCO --list` and the constructed `offer_curve_by_group`
agree: all 13 classes (`CC_CHP`, `CC_INTERMEDIATE`, `CC_REGULAR`, `COAL`, `COAL_BIT`,
`COAL_LIGNITE`, `COAL_PRB`, `COAL_WC`, `CT_CHP`, `CT_INTERMEDIATE`, `CT_PEAKER`, `ST_GAS`,
`ST_GAS_INTERMEDIATE`) read **1.0 on `committed` / `econ_low` / `econ_high` / `peak`**; **no
`phys_*` row exists**; the delta JSON is `{}`. Only the structural shares differ by class
(`econ_low_share` 0.5–0.556, `pct_peaking` 5–15) and they are not the tuning channel. No ERCOT- or
other-ISO-fitted multiplier leaks into SOCO. **`authorized_price_tuning` is declared NONE** (§8):
SOCO is a cost-based BA that takes no offers, so a band ≠ 1.0 would need a far stronger story than an
RTO's, and there is no price residual to tune on in the first place.

---

## 4. Phase-0 census (zero-LP, called on the recipe)

### 4.1 Fleet, and the memory-class reconciliation the charter asked for

`load_fleet_from_csv("SOCO", iso_config, year=<y>)`: **393 thermal generators / 110 plants /
55,092.3 MW**, identical in 2023, 2024 and 2025 (`eia860_vintage_tracks_solve_year` is False, so one
snapshot; COD / retirement masks apply per year at run time). 2024 by `plant_group` (MW): `CC_REGULAR`
90 / 18,652.9 · `COAL` 16 / 11,512.0 · `CT_PEAKER` 100 / 9,634.2 · nuclear 8 / 8,080.0 · `ST_GAS`
12 / 3,131.1 · biomass 92 / 1,680.5 · oil 34 / 1,121.5 · `CC_CHP` 14 / 746.6 · `CT_CHP` 14 / 336.4 ·
`ST_CHP` 13 / 197.1. By zone: SOCO_AL 20,882.7 · SOCO_GA 30,250.2 · SOCO_MS 3,959.4 MW.
**Every class with a benchmark row has units; no zone is empty.**

- **Vogtle (649)**: units 1 / 2 online 1987-05 / 1989-05; **unit 3 online 2023-07; unit 4 online
  2024-04** — the units' OWN dates, carried by SOCO-15's repair (`effective_cod` prefers the
  generator's own record; the plant map still reads `(2005, 5)` and is not consulted for a real
  unit). The STOP gate tests this (§5 leg E).
- **McIntosh (7063)**: unit 1 is a **25 MW gas CT** (card S7); the 110 MW nameplate does not appear;
  the storage loader lists no McIntosh CAES object. Settled.
- **Four CC plants with corrupt EIA-860 summer-capacity rows** (6073, 7897, 55382, 57037) are
  reconciled at load to their trusted bound — **1,412.3 MW removed** — exactly as SOCO-30 §6.3
  recorded (desk R-s). Every ratio in this lane sits on that basis.
- **Plant 67241 (MA)** is rejected at load, unzoned (audit §2.6(a)).
- **The reconciliation.** `run_isos_concurrent.py` registers `IsoMemoryClass("SOCO", peak_gb=6.0,
  per_plant=True, co_opt=False)`; the `ScenarioConfig` dataclass default is `plant_level_fleet=False`
  and `_soco_config` sets nothing. **Measured by calling the code, the two agree**: the CLI's
  `backcast_config` sets `plant_level_fleet=(iso != "ERCOT")` → **True for SOCO**, and
  `load_or_synthesize_bins` returns **None** for SOCO (absent from `CAMPD_BINNING_ISOS`), so the solve
  takes the **per-plant EIA-860 fleet on the legacy aggregate path** — one LP unit per generator, no
  CAMPD tranche bins. `per_plant=True` in the memory registry describes that path correctly; the
  dataclass default is simply not the operative value for any non-ERCOT backcast. **No finding, no
  route**: the registries do not disagree once the construction is called. `thermal_tranches_SOCO.csv`
  is therefore NOT an input to this keeper (it is the input to the pre-declared per-plant-binning
  lever), and SOCO is deliberately NOT added to `CAMPD_BINNING_ISOS` (NWPP ruling N8 posture; a
  declared solve-surface value; gate G8; not this lane's call). `peak_gb` is measured by the shards.

### 4.2 Zones and load — BOTH share sets reported (addendum item 3)

`load_demand("SOCO", y, iso_config)` returns 3 × 8,760 in every year, no NaN, **0 zero-load hours**:

| year | LP load = demand + served export, TWh | LP peak / min MW | demand-only TWh (peak / min) | measured hourly zone shares AL / GA / MS |
|---|---:|---|---|---|
| 2023 | 239.6251 | 48,064 / 17,442 | 229.4688 (45,558 / 17,432) | 0.3024 / 0.6382 / 0.0593 |
| 2024 | 249.5057 | 48,373 / 17,619 | 238.6990 (47,368 / 17,007) | 0.2976 / 0.6451 / 0.0573 |
| 2025 | 252.5897 | 51,268 / 15,559 | 239.5576 (46,490 / 12,638) | 0.2943 / 0.6494 / 0.0563 |

The demand-only totals reproduce SOCO-31's committed `demand.total_twh` to the fourth decimal; the
LP-load totals reproduce SOCO-32's "system TWh 239.6 / 249.5 / 252.6". **The operative shares are the
MEASURED FERC-714 hourly shares** (SOCO-32; five respondents, Southern Power 186 excluded — card S3);
the static `load_share` **0.3510 / 0.5842 / 0.0648** in `_soco_config` is the fleet-MW FALLBACK that
fires only if both the clean parquet and the raw file are absent. The shard's hard stop still checks
the static triple (a cheap config-identity check) and this table says which object the solve used.
`data/clean/` is absent in this container and the raw fallback is byte-identical to the clean path
(SOCO-32 §1.5), so a fresh shard reads the same arrays. Links: AL↔GA 24,400 MW, AL↔MS 4,300 MW,
Tier-3 upper bounds that cannot bind (card S3); `validate_topology()` passes.

### 4.3 Served interchange (card S4)

`soco_net_interchange(y)`: **+10.1562 / +10.8067 / +13.0321 TWh** (8,760 hours each; positive =
export in 8,267 / 8,451 / 8,527 hours; range −1,397…+4,432 / −1,659…+4,858 / −933…+5,147 MW) —
reproducing SOCO-31 §0.1 and SOCO-33 §0 to the fourth decimal. It enters the LP as load
(`include_interchange=True`), which is why the LP load exceeds demand by exactly the export. **This
run does not read any `interface_limit_mw`**: all eight `INTERFACE_NEIGHBORS["SOCO"]` blocks are
default-off (`reference_price_interface=False`, measured on the recipe), so SOCO-33's finding that
seven of eight registered limits would refuse 35.6 / 39.0 / 41.7 % of measured flow is lever SOCO-56's
precondition (desk R-t) and does not bite here. `build_import_generators("SOCO")` → `[]` (gate G7).

### 4.4 Storage

`load_eia860_storage` / `load_eia860_pumped_storage`: **pumped storage 1,306.6 MW / 13,066 MWh in
SOCO_GA** (all three years); batteries 81.2 MW / 164.4 MWh (2023) → 146.2 MW / 424.4 MWh (2024–25)
in SOCO_GA plus 1.5 MW / 1.5 MWh in SOCO_MS. No McIntosh object. R-i (§10) is the consequence: the
model will cycle 1,306.6 MW of PS in 2023–2024 and EIA-930 carries no `NG: PS` comparator for those
years.

### 4.5 Hydro — and the 2025 input hole, named before the solve

`load_hydro_budget("SOCO", y)` (the loader `build_hydro_fleet` reads, no backfill armed in the
recipe): **2023 42 plants / 6.8150 TWh · 2024 42 plants / 6.3015 TWh** (SOCO_AL + SOCO_GA, max_mw
3,314.0) — reproducing SOCO-31's committed EIA-923 hydro to the fourth decimal — but **2025 5 plants /
0.3275 TWh (SOCO_GA only, 368 MW)** against **6.0123 TWh measured** (EIA-930 `NG: WAT`, which SOCO-31
swapped in for the 2025 *benchmark*). The LP input reads the preliminary EIA-923 vintage in which the
large hydro filers have not yet reported; the benchmark reads the meter. **This is the SPP-40 R-8
defect shape, carried into SOCO's 2025 exactly as it was into SPP's**: ~5.7 TWh of hydro absent from
the LP in 2025, backfilled by whatever is next in merit (gas, most likely) and, at a tight winter
hour, possibly by slack. It is named here so the STOP gate does not grade it as a structural failure
(2025 is not the screen year for this reason among others), it is NOT repaired in this lane (a
`--hydro-backfill-year 2024` or `--hydro-eia930-monthly` arm is a lever decision on the SOCO queue,
and arming it for one year inside the first keeper would be exactly the year-scoped fix rule 1
forbids the lane from choosing on its own), and it is reported at full magnitude in the FINDING's
2025 column and routed to SOCO-DESK. Informational bound, zero-LP: `backfill_year=2024` would carry
the 2024 census into 2025 (measured in the FINDING).

### 4.6 Renewables, outages, fuel, and the refusals

- **Solar only, no wind** (`load_renewable_profiles`): capacity 4,912.9 / 5,707.9 / 6,047.9 MW
  (AL / GA / MS 2025: 700.7 / 5,030.7 / 316.5), potential 8.3622 / 10.1268 / 9.9852 TWh — the
  SOCO-32 measured per-zone shape, live. Wind capacity 0.0 MW in every year.
- **Outages**: `outage_source="historic"`, `historic_outage_overlay=False`, unit-level
  `campd-unit-outages-SOCO.csv` (1,119 windows) + `campd-partial-outages-SOCO.csv` (12 rows) are the
  overlay; `unit_outage_short_windows` False (default); `temp_dependent_derate` False.
- **Fuel**: `gas_plant_monthly_fuel_pricing=True` — EIA-923 delivered prices exist for **29 of 67**
  SOCO fossil plants in 2024 (28 in 2023, 29 in 2025); the remainder gap-fill from state/zone
  neighbours (`nearby_fuel_price_fallback=True`), then the Henry Hub curve. Stated, not repaired.
- **VOLL**: the LP's slack penalty is `iso_config.voll` = **61,900 $/MWh** (card S5; `runner.py`
  passes `voll=iso_config.voll`). `ScenarioConfig.voll` reads 5,000 and is not the LP's operand
  (`pipeline/spec.py` says so; the one `config.voll` read in `pipeline/solve.py` is the ERCOT swcap
  tiebreak, ERCOT-only).
- **No reserves, no capacity market, no import node**: `energy_reserve_coopt=False` on the recipe,
  and `reserves.spec` REFUSES SOCO by name (`ValueError: SOCO clears no ancillary-service market`)
  if anyone arms it; `MARKET_DESIGN` has no SOCO key (→ `DEFAULT_MARKET_DESIGN`, card S6). A
  reserve or capacity result in this bundle is a bug, not a finding.
- **Commitment bridges**: `ercot_gas_commitment_bridge`, `nyiso_gas_commitment_bridge`,
  `caiso_ra_mustoffer` all False; `commitment_enabled` False (P2 archived).
- **Clock**: every series above is `America/Chicago`, DST-aware, hour-ending (gate G19, SOCO-10 /
  SOCO-33); this lane re-decides nothing.

---

## 5. THE STRUCTURAL STOP GATE (charter item (c)) — pre-registered, falsifiable, kill-only

The screen (2024) is graded on the legs below and nothing else. It may kill the arm; it can never
promote it; no leg reads C1–C8; no leg reads a residual against a benchmark as a *target* (leg C
uses the benchmark only as an order-of-magnitude sanity band, the charter's literal wording). Each
leg is gradable from the committed `hourly/system_2024.parquet`, `class_hourly_2024.parquet` and the
bundle's `metrics.json` alone.

**Leg A — the served export is served.** SOCO is a net EXPORTER (+10.8067 TWh in 2024) and the
served schedule enters as load. **STOP** if the bundle's net position reads net-importing, or if
total generation − demand differs from the served +10.8067 TWh by more than 1 % (the LP would have
dropped or double-counted the schedule). Reported: generation, demand, the implied export.

**Leg B — no unserved energy outside tolerance.** **STOP** if `Slack` exceeds **0.05 % of annual LP
load (> 124.8 GWh)** or occurs in more than **50 hours**. Reported: slack MWh and hours, the hours'
dates, dump MWh.

**Leg C — fuel classes within an order of magnitude of SOCO-31's committed benchmark** (EIA-923
2024: coal 40.2395, gas_cc 113.7601, gas_ct 6.2537, gas_st 9.4821, nuclear 63.0598, hydro 6.3014,
solar 10.3849 TWh; EIA-930 gas-all 125.6844). **STOP** if any class with an actual ≥ 5 TWh lands
outside **[0.1×, 10×]** of it, or a class with units carries zero energy, or a zone carries zero
load. Reported: every class ratio, with the factor-3 band as information (a factor-3 miss is a
structural finding for the lever queue, never a kill, never a tuning target).

**Leg D — no negative-price absurdity.** SOCO has no wind and no PTC offer, so the model's price floor
is the storage ε / solar MC=0. **STOP** if any zonal dual falls below **−$5/MWh** (a dump-cost
degeneracy) or if more than **5 % of zone-hours** are negative. Reported: negative hours by zone,
hours > $200 and > $1,000 (the C3c object, reported only — there is no C3c).

**Leg E — Vogtle 3 and 4 OFF before their CODs and ON after.** From the unit-level record
(`hourly/unit_hourly_2024.parquet` if written; else the nuclear class series and the fleet's
availability): nuclear class energy in Jan–Mar 2024 must be consistent with THREE Vogtle units + the
other six reactors, and Apr–Dec with FOUR — **STOP** if the nuclear monthly series shows no step
between March and April 2024 of the order of +1,100 MW × hours, or if it exceeds the 8,080 MW
nuclear nameplate in any hour. In the full span, 2023 Jan–Jun must carry no Vogtle 3 energy. (Card
S12: the residual COD bias — month grain, and whatever the ramp construction leaves — is stated on
the determination basis regardless of this leg's outcome.)

**Leg F — no reserve, no capacity, no import object.** **STOP** if `reserve_price` is non-zero in
any hour, if any capacity-market artifact is written, or if an import generator appears in the fleet.

Kill ⇒ the FINDING reports it as the session's result and the remaining years are **not** spent.
Pass ⇒ the full span runs unchanged (the screen year is re-solved inside it).

---

## 6. Known input artifacts named BEFORE the solve (reported, never repaired in-lane)

| artifact | where it bites | status |
|---|---|---|
| **2025 EIA-923 hydro budget 0.3275 TWh vs 6.0123 measured** (§4.5) | the 2025 LP input; gas backfill, possible slack | routed to SOCO-DESK as a lever-queue item; reported at full magnitude |
| **SOCO 2024 `NG: OIL` rule-14 FALSE POSITIVE** (addendum item 2, desk R-w): the EIA-930 unit-slip screen deletes 4.4 GWh of a REAL Winter Storm Heather oil run, 2024-01-17 03:00–09:00 (155→530→660→762→801→350 MW, tracking the 47,368 MW winter peak hour for hour); the benchmark's oil reads 0.0056→0.0012 TWh | the C1 oil benchmark is biased LOW in 2023–24; a model that dispatches the oil correctly scores as over-generating it | stated on the determination basis; benchmark NOT corrected, hours NOT excluded, nothing tuned. Contrast: the 2025 `NG: NG` flags (70,683 MW of gas in a 32,574 MW hour, four hours) are correct and stay |
| 2025 `min_mw` 12,638 MW — a one-hour partial post 2025-10-23 21:00 UTC (SOCO-31 §4.3) | ~10 GWh, 0.004 % | passes through; not a real minimum |
| 2025 `NG − D − TI` residual, 633 hours / −0.6963 TWh (SOCO-31 §4.4) | benchmark-side accounting | reported |
| the seven UTC-bounded trailing hours of 2025 flat-filled at 28,408 MW (SOCO-11 [4], R-x(1)) | +0.1989 TWh on the 2025 total | reported |
| 2025 peaker census: 6 / 23 `CT_PEAKER`, 1 / 6 `CC_CHP` filed (R-v; SOCO-31 §4.5) | no SOCO pair gate-eligible for 2025; the gas split defers to EIA-930 | stated on the determination basis |
| four corrupt EIA-860 CC summer rows, 1,412.3 MW reconciled at load (R-s) | every capacity ratio | reported |
| F923 own-plant fuel prices at 29 / 67 fossil plants | gap-fill from state/zone | reported |

No new `ScenarioConfig` parameter, no new constant, no threshold, no screen bar (rules 5 / 23 / 24).

---

## 7. Control, memory, and what this bundle becomes (charter item (d))

**Control = none.** There is no SOCO keeper, so rule 29(b) form 4 is vacuous and no control solve is
spent. **This bundle becomes the rule-29(b) control for every later SOCO lane** (SOCO-5x): its
committed numbers and `hourly/` sidecars are what each lever is differenced against without a re-solve.

Memory class registered for the `soco` profile: `per_plant=True`, `co_opt=False`,
`peak_gb=6.0 (ESTIMATE, to be MEASURED here)`. The shards run the runner unmodified with
`ensure_solve_container` (no memory recipe of their own) and report the `container preflight:` and
`memory peak:` lines verbatim; the FINDING records wall-clock per year / pass and the cgroup peak, and
recommends the measured `peak_gb` to the desk (the registry edit is `scripts/`, not this lane's).

**Rules 15 / 16 / 29(c) / 31 / 34.** The full bundle is registered whatever the determination reads
(`2026-09-16-soco-1-baseline`, `results/calibration/soco40_baseline_B/` slim files + `hourly/`
sidecars), becomes `keepers/SOCO.json`'s keeper because it is the most structurally faithful SOCO run
that exists (rule 1), and the screen bundle `_soco40_screen` is **kept out of `main`** by `.gitignore`
in the parent's tree — never `rm`'d (rule 31) — while every number this lane will ever cite from it is
in the FINDING. Both shards **push their bundles** to their own branches (rule 34(a)), so a promotion
of either is a checkout, never a re-solve.

---

## 8. The DOF ledger — declared before the solve (rule 21; gate G5)

`build_dof_ledger.py` on this recipe is expected to list the same config-derived entries SPP-40's did
and nothing else — no per-ISO curated constant is keyed on SOCO; no floor, bridge, adder, seam ladder
or scarcity overlay is armed:

| entry | value in this recipe | identification, stated honestly | residual-identified on SOCO? |
|---|---|---|---|
| `offer_curve_by_group` | 1.0 on every band of every class (§3.3) | the **identity** — every unit offers at its own heat rate × delivered fuel + VOM; **0 tuned scalars** | **no** |
| `offer_curve_smoothing` (n = 6, exp = 1.0) | generic | the econ-ramp interpolation between `econ_low` and `econ_high`; with both at 1.0 the ramp has **zero span** — inert; 0 scalars | **no** |
| `wefor_multiplier` | 0.7 | the CLI's non-MISO default, an inherited generic scalar the audit (C-15) classifies residual-identified on ERCOT; **neither 0.7 nor 1.0 has a SOCO identification**, so the default is kept, NOT re-chosen, and it is ledgered `residual` with its open root cause (the overlay/statistical double-count `wefor_residual` names) | **no — inherited** |

**`authorized_price_tuning`: NONE** — declared in `calibration_attestation.json` as the four
governance assertions all `true`, no `authorized_price_tuning` block (a declaration block names a
channel in use; there is none), and an explicit `authorized_price_tuning_declared: "NONE — …"` prose
line so C6 reads the declaration rather than its absence (gate G5). **Expected: zero
residual-identified values chosen on SOCO** (the one `residual`-tagged entry is inherited and
un-chosen). No parameter in this recipe was set by looking at a SOCO residual, because none exists.

---

## 9. What the screen and this lane are NOT allowed to do

- Never read C1–C8 as a gate on the screen (rule 29: "did C1 improve" is the forbidden form).
- Never move a TTC, a band, a floor, a VOLL, a hydro budget or an adder — a structural miss opens a
  lever from SOCO's queue (`docs/mechanism-testing-matrix.md` §5.8) as a NEW chartered lane.
- Never touch `actual_lmp.json`, any other region's shard / status / bench / log / keeper file,
  `frontend/data/forecast/**`, `ScenarioConfig` defaults, or any `offer_curve_by_group` band.
- Never delete a result (rule 31): the screen bundle and the span bundle stay on their shard branches
  and on local disk until the owner has ruled on promotion; the promotion question is asked
  in-session while they are alive.
- Never re-decide the clock (G19), the zone count (S3), the seam construction (S4), the VOLL (S5),
  the adequacy scalar (S6) or the McIntosh mapping (S7).

---

## 10. The determination basis — the SIX lines the FINDING must carry (charter item 3 + addendum 2)

1. **The price gap** — no public SOCO price exists; C3a / C3b / C3c UNSCORABLE (not failed);
   SOCO-13's NO cited; the model's own mean price printed as MODEL-ONLY / UNVERIFIED.
2. **R-i** — 1,306.6 MW of pumped storage UNOBSERVABLE in EIA-930 for 2023 (0 / 8,760 h) and 99.7 %
   of 2024; `NG: WAT` never negative before the 2024-07-15 cut-over, so PS charging was NOT REPORTED
   (not folded into hydro): a hard constraint on the C1 `fuelmix` benchmark, never a hole to fill.
3. **Card S3** — Southern Power (respondent 186) excluded from the zonal shares; residual
   3.03 / 2.92 / 1.26 % (SOCO-11; 1.18 % on the model clock, SOCO-32).
4. **Card S12 / SOCO-15's COD bias** — the units' own online months now govern (Vogtle 3 2023-07,
   Vogtle 4 2024-04); what the month-grain ramp leaves is stated at full magnitude, whatever it is.
5. **R-v** — 2025 carries no `eia923_incomplete` flag (ratio 0.9533) but its peaker census does not
   (6 / 23 `CT_PEAKER`, 1 / 6 `CC_CHP` filed); no SOCO pair is gate-eligible and the 2025 gas split
   defers to EIA-930.
6. **R-w** — the SOCO 2024 `NG: OIL` rule-14 false positive in the committed benchmark (§6).

Plus, from this lane's own census: the 2025 hydro input hole (§4.5), stated beside the 2025 column.
