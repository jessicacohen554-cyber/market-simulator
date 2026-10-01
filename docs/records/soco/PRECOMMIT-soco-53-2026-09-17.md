# PRECOMMIT — SOCO-53: the `CT_PEAKER` / `ST_GAS` merit-order lever

**Lane** SOCO-53 · **Model** Opus 5 · **Date** 2026-09-17 ·
**Branch** `claude/wizardly-edison-xc8fq4` · **Data profile** `soco` ·
**Incumbent keeper (the control, rule 29 `[R-SCREEN]` (b) form 4)**
`2026-09-16-soco-1-baseline`, bundle `results/calibration/soco40_coalsplit_B`,
basis `71884144abf4f08a4063d3c7a32e03a2c2f5d04d`.
**Predecessors** `FINDING-soco-40-2026-09-16.md` (§4 is this lane's object, §10 the queue
recommendation), `PRECOMMIT-soco-40-2026-09-16.md`, `ADDENDUM-soco40-armB-relaunch-and-gdrift-2026-09-16.md`.
**Rules that bind** 1 `[R-STRUCT]`, 12 `[R-PARALLEL]`, 13 `[R-MEASURED]`, 14 `[R-ACCURATE]`,
15 `[R-DASHBOARD]`, 16 `[R-ALLYEARS]`, 18 `[R-PHYSICS]`, 19 `[R-ONE-MECH]`, 20 `[R-FORCED-BUDGET]`,
21 `[R-DOF]`, 24 `[R-REGISTRY]`, 25 `[R-ISO-SCOPE]`, 28 `[R-MECH-MATRIX]`, 29 `[R-SCREEN]`,
31 `[R-RETAIN]`, 32 `[R-SHARD]`, 33 `[R-SHARD-ARCHIVE]`, 34 `[R-SHARD-PROMOTABLE]`, 35 `[R-PROMOTE]`.

**Pushed before the arm is solved.** Every number below is ZERO-LP: the committed keeper bundle's
own `hourly/` sidecars, the fleet loaders called directly, the CAMPD unit-level corpus read
directly, and the two derive scripts. No LP of any length ran in this session (rule 32(a): the
parent never solves). The phase-0 findings, the G-DRIFT audit, the refusals, the arm and the
ex-ante prediction are fixed here; nothing is revised after the solve is read.

---

## 0. THE PRICE POSTURE IS UNCHANGED AND UNCHALLENGED

SOCO publishes no LMP and never will. `data/raw/_validation-source/actual_lmp.json` carries **no
SOCO block and must not gain one** — a placeholder breaks
`calibration_verdict._price_reference_absent` and silently moves SOCO onto the ordinary
determination path. C3a / C3b / C3c are **UNSCORABLE, not failed**. The ceiling is rubric v3.8
`PHYSICALLY-CALIBRATED (PRICE UNSCORED)`; SOCO can **never** read `CALIBRATED`. Scored on
**C1 / C2 / C4 / C6 / C8 only**. Gate **G17** absolute: no neighbouring hub, no proxy, no
cost-stack price, ever.

**Every `offer_curve_by_group` band stays at the identity 1.0 and `authorized_price_tuning` stays
declared NONE.** With no price benchmark there is no price residual, so the rule-1 authorized
channel is **unreachable here, not merely unused**. This lane touches no band, share, floor or
threshold.

---

## 1. PHASE 0 — WHAT THE MEASUREMENT SAYS, AND HOW IT OVERTURNS THE LANE'S PREMISE

The handoff framed the object as a **merit-order / offer-construction** defect. **Measurement
refutes that framing.** Five independent zero-LP findings, in the order they bind.

### 1.1 Every offer-curve-shaped lever is INERT for SOCO *by construction*

`backcast_config._SOCO_OFFER_CURVE` sets **every** heat-rate multiplier band
(`committed` / `econ_low` / `econ_high` / `peak`) to **1.0 on all 13 groups**, deep-merged for
`iso == "SOCO"` only (declared 2026-09-14 at lane SOCO-20, before any SOCO solve existed). A SOCO
tranche therefore offers at its **own measured heat rate × delivered fuel + VOM**, and each class
collapses to a **single flat price block** — the tranche shares still partition capacity, but
nothing prices it differently.

Confirmed in the keeper's own committed `class_band_hourly` sidecar (TWh, P1):

| year | class | committed | econ_low | econ_high | peak | total |
|---|---|---|---|---|---|---|
| 2023 | `CT_PEAKER` | 0.903 | 5.742 | 5.183 | 0.928 | 12.755 |
| 2023 | `ST_GAS` | 1.117 | 1.138 | 1.141 | 0.600 | 3.996 |

`ST_GAS` is **flat across all four bands** — the all-or-nothing signature of a single price point,
not a rising curve. **Consequence, and it is a program-level fact rather than this lane's opinion:**
`ct_intermediate_split`, `st_gas_intermediate_split` and every other curve-shaped lever route to a
curve that is also all-1.0, so they are **provably inert for SOCO** and are recorded `I` in the
matrix on this construction, not on a solve. **SOCO's only available levers are physics and data
levers.**

### 1.2 The two classes are within ~$1.3/MWh on MEASURED cost — a price gap cannot make a 7× CF split

Measured from the CAMPD unit-level corpus (AL + GA + MS, 2023–2025 pooled, loaded hours,
`heatInput / grossLoad`, net of the 0.99 parasitic factor), against the model's assigned rates:

| | model (eGRID plant blend) | measured (CAMPD) | model − measured |
|---|---|---|---|
| `CT_PEAKER` cap-wtd HR | **12.798** | **10.911** | **+1.887** |
| `ST_GAS` cap-wtd HR | **10.815** | **10.198** | **+0.617** |
| **CT − ST separation** | **+1.983** | **+0.713** | — |

**The model already separates the two classes by 2.8× the measured separation, and `CT_PEAKER`
still over-runs by 8.221 TWh.** At $2.54 gas the measured separation is ~$1.3/MWh net of the
VOM difference (CT 3.50 vs ST 4.00). **No admissible cost-side change can turn a $1.3/MWh gap into
the observed capacity-factor ratio** — measured 2023 `CT_PEAKER` CF ~5.4 % against `ST_GAS` ~38 %.
This is positive evidence that the missing object is **not price**.

### 1.3 What the real system actually does — SOCO's own CAMPD conduct, at UNIT grain

Plant grain is **unsound for SOCO** and this is the reason: SOCO's facilities are multi-class under
one CEMS facility id (Barry 3 carries gas boilers *and* a coal unit *and* four CC blocks; Gaston 26
carries four gas boilers and a coal unit; Greene County 10 and Watson 2049 each carry boilers
*and* combustion turbines). Measured at **unit** grain, splitting on CAMPD `unitType`:

| | gas boilers (`ST`) | combustion turbines (`CT`) |
|---|---|---|
| median run length | **94 – 144 h** | **8 – 9 h** |
| mean run length | 299 – 366 h | 9.7 – 10.6 h |
| starts / unit / yr | **8.9 – 11.4** | **57 – 60** |
| capacity factor | ~31 % | ~6 % |

**A SOCO gas boiler runs multi-week campaigns and starts ~10 times a year; a SOCO combustion
turbine runs 8–9 hour blocks and starts ~58 times a year.** The model gives **both** classes
`min_run_hours = 0` and `min_down_hours = 0`, and with `tranche_startup_amortization` off the
`CT_PEAKER` **econ and peak tranches carry zero startup cost** — the tranches that hold
**10.9 of the 12.755 TWh** (§1.1). The separation the real system produces by **commitment** has
no representation in the model at all.

### 1.4 The commitment-bridge arm is REFUSED on SOCO's own measured data

The NYISO / SPP-shaped `*_gas_commitment_bridge` holds a slow-start unit at min load across an
idle gap shorter than its min-down. Measured boiler downtime-gap distribution, 2023–2025:

| gap | n | share | gap-hours |
|---|---|---|---|
| 0–4 h | 36 | 9.3 % | 62 |
| 4–8 h | 17 | 4.4 % | 88 |
| 8–12 h | 8 | 2.1 % | 72 |
| 12–24 h | 17 | 4.4 % | 266 |
| 24–72 h | 43 | 11.1 % | 1,943 |
| **> 72 h** | **265** | **68.7 %** | **169,303** |

**98.6 % of boiler downtime-hours sit in gaps longer than 72 h; only 150 unit-hours across three
years fall inside the 8 h `ST_GAS` min-down.** SOCO's boilers do not two-shift — they go on for
weeks and off for weeks. A gap bridge would floor ~150 unit-hours against a 6.5 TWh/yr residual:
**inert by measurement.** Recorded `R` for SOCO on this evidence, before any solve was spent on it.

The existing plant-basis derive is **unsound for SOCO** for the §1.3 reason and its output is
recorded here so no successor re-reads it as fact: `campd_gas_commitment_params_plant_SOCO.csv`
reports `ST_GAS` `min_load_frac` **0.0848** and `run_hours_p50` **6.0 h** — combustion-turbine
conduct, because Greene County's and Watson's turbines are summed into the "plant" series. The
**unit-grain** statistic, computed here with the derive's own construction (HSL = p99.5,
online ≥ max(`_ONLINE_MW`, 0.05 × HSL), LSL = p5 of online hours), is `min_load_frac` cap-wtd
p50 **0.1782** (p25 0.1708 / p75 0.2731) over 13 units / 3,533 MW. **Neither number is used by
this lane**; both are recorded as evidence.

### 1.5 `tranche_startup_amortization` is REFUSED ex ante — `U` → `G`

The mechanism is the **FERC Order-825 fast-start PRICING** object: bid markup only,
`min_run`/`min_down` stay 0, so it puts start costs **into the LMP**. CAISO's cell is `G` on
precisely this ground (the four `K` cells "are the four ISOs that HAVE the rule"). **SOCO has no
LMP, no offers, no fast-start pricing rule and no market at all** — the ground that refused it for
CAISO bites SOCO harder, and this is SOCO's own reading of SOCO's own market design, not a
transferred verdict (rule 28(d)). Arming a market-design pricing rule on a footprint with no
market is the rule-1 `[R-STRUCT]` prohibition verbatim: *never reach the right number through a
mechanism that isn't real.* **No reopen condition.**

Recorded, and deliberately **not** acted on: `gas_st_startup_spread` is `True` in the keeper's
recipe and is a **dead flag** — `compute_monthly_markup` skips every `gas_st` row before reading
it, because `gas_st_startup_cost` is `False`.

---

## 2. THE ARM — `measured_ct_heat_rates = True`, on SOCO's own derived artifact

**This is a rule 14 `[R-ACCURATE]` data repair, and it is mandated by that rule irrespective of
which way the residual moves.** eGRID publishes **one** rate per plant, so a mixed facility's
turbines inherit its steam boilers' rate. SOCO is the worst case in the fleet: Greene County's
**nine combustion turbines and two gas boilers carry the identical heat rate, 10.482689**.

Derived this session from SOCO's own CAMPD record
(`scripts/data/derive_campd_ct_heat_rates.py --iso SOCO`, pooled 2023–2025, restricted to
`unitType == 'Combustion turbine'`, MMBtu per **net** MWh):
`data/raw/_processed-legacy/campd_ct_heat_rates_SOCO.csv` — **19 of 26 plants, 8,452.5 / 9,634.2 MW
(87.7 % of `CT_PEAKER` capacity)**. Rule 25 `[R-ISO-SCOPE]`: SOCO's own measurement, no other ISO's
number. Rule 13 `[R-MEASURED]`: a machine's loaded heat rate is a physical characteristic that
regenerates for a forward year and responds to changed conditions — an INPUT, never an outcome fed
back. Rule 21 `[R-DOF]`: **zero free parameters**; nothing is fitted, and with no price benchmark
nothing could be.

**The errors are large and run in BOTH directions**, which is why no multiplier substitutes for the
measurement:

| plant | MW | model (eGRID) | measured | ratio |
|---|---|---|---|---|
| Greene County (10) | 740.0 | 10.483 | **12.849** | 0.816 |
| Watson CT (2049) | 33.0 | 10.418 | **14.266** | 0.730 |
| Walton County (55128) | 449.7 | 9.969 | 10.193 | 0.978 |
| Washington County (55332) | 623.4 | **17.185** | 10.702 | 1.606 |
| Calhoun (55409) | 704.0 | **17.099** | 10.422 | 1.641 |
| McIntosh (6124) | 657.6 | **18.740** | 12.494 | 1.500 |
| MPC Generating (7764) | 302.5 | 14.227 | 11.415 | 1.246 |

Verified end-to-end, zero-LP, through the live consumer
(`load_fleet_from_csv(..., measured_ct_heat_rates=True)`): `CT_PEAKER` cap-wtd HR
**12.6921 → 11.2666**; **`ST_GAS` unchanged at 10.8151** — the mechanism is applied per generator
by class, so only the turbines of a mixed plant are repriced (rule 19 `[R-ONE-MECH]`: one
mechanism, one seam).

### 2.1 A REGISTRY GAP THIS LANE REPAIRS (rule 24 `[R-REGISTRY]`)

`ScenarioConfig.measured_ct_heat_rates` is registered, cache-key-registered
(`_CACHE_KEY_OPTIONAL_FIELDS`, default `"False"`, so an armed run earns a distinct key and every
existing keeper keeps its key), has a derive script, has a live consumer in `fleet/eia860.py`, and
is carried `True` by **five ISOs' keepers** (CAISO / MISO / NEISO / NYISO / PJM) — **and it has no
CLI flag in `scripts/run_calibration_full.py`, the orchestrator every keeper is solved with.**
Measured: `--help` lists `--egrid-identity-heat-rates`, `--egrid-family-heat-rates` and
`--egrid-steam-collapse-heat-rates` and **no** `--measured-ct-heat-rates`; `default_scenario_overrides`
does not reach `backcast_config` (verified on NEISO: all six overrides differ from the built
backcast config). The mechanism was unreachable for SOCO, NWPP and SPP.

**Repair, additive and byte-identical unset:** the flag is wired along the identical eight-site
path `egrid_identity_heat_rates` already takes — argparse (`BooleanOptionalAction`, `default=None`),
`main()` forwarding, `solve_and_persist` signature, `recorded_cfg.with_overrides`, the `run_year`
call, the `meta` dict, and `run_calibration.py`'s `run_year` signature + `with_overrides`. **Unset
means no override, so every other ISO and every existing keeper is byte-identical.** No
`ScenarioConfig` default moves, no `src/market_sim` solve-path file is touched, and
`scripts/check_cache_key_registration.py` passes (851 fields, 306 registered, all resolve; 305
solve-surface names across 7 modules, all declared).

### 2.2 EX-ANTE PREDICTION — registered BEFORE the solve, and it is ADVERSE

Cap-weighted `CT_PEAKER` heat rate falls **12.909 → 11.284 (−12.6 %)**; 7,229.8 MW over 16 plants
gets cheaper, 1,222.7 MW over 3 plants gets more expensive. Against the model's marginal `ST_GAS`
plant (Yates, HR 10.814) at each year's own Henry Hub:

| year | gas | `ST_GAS` marginal mc | CT capacity priced BELOW it: before → after |
|---|---|---|---|
| 2023 | $2.54 | $31.47/MWh | 2,354.7 → **4,176.0 MW** (**+1,821.3**) |
| 2024 | $2.19 | $27.68/MWh | 2,354.7 → **4,176.0 MW** (**+1,821.3**) |
| 2025 | $3.52 | $42.07/MWh | 2,354.7 → **4,176.0 MW** (**+1,821.3**) |

**So this lane PREDICTS, before solving, that `CT_PEAKER` energy RISES and the one gating C1 row
this lane was opened to fix gets WORSE.** It is armed anyway, and that is not defiance of the
brief — it is rules 1 and 14 operating exactly as written: *"If swapping a hand estimate for real
data makes the backcast worse, that is a signal that something else in the model is miscalibrated
and the estimate was silently compensating for it. Treat the worse fit as a discovered bug: keep
the accurate input, find and fix the real root cause."* The eGRID plant blend was **silently
compensating for the missing commitment physics** of §1.3. Whatever C1 reads afterwards is reported
at full magnitude and nothing is reverted.

**Falsifier.** If `CT_PEAKER` energy does **not** rise, the §2.2 construction is wrong and the
FINDING says so rather than claiming a success.

### 2.3 What this lane does NOT do

No band, share, floor or threshold is touched. No commitment bridge is armed (§1.4). No
`tranche_startup_amortization` (§1.5). No new `ScenarioConfig` field, so no new matrix row is owed
under rule 28(c) — only cell updates in SOCO's own shard. The `ST_GAS` side of the same eGRID
plant-blend defect (Barry's boilers inherit a CC-contaminated 8.995 against a measured 11.252;
Gaston's carry 11.551 against a measured 10.503) has **no registered mechanism** and is **routed,
not half-repaired** (rule 19).

---

## 3. G-DRIFT (rule 29 `[R-SCREEN]` (b)) — recorded BEFORE the arm is solved

`git diff 71884144abf4f08a4063d3c7a32e03a2c2f5d04d HEAD -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`
→ 6 files, +246 / −6.

| file | verdict | reason |
|---|---|---|
| `scripts/run_calibration.py` | **INERT** | One NEISO-only kwarg (`neiso_coldsnap_derate_dualfuel_unswitched`) threaded to `with_overrides`; `None` unset, so no config moves. |
| `src/market_sim/config/scenarios.py` | **INERT** | The same NEISO-only field, declared default `False`, plus its `_CACHE_KEY_OPTIONAL_FIELDS` registration **dropped at its default** — so SOCO's key does not move. `TIER_TAGS` entry only. |
| `src/market_sim/data/fleet/floors.py` | **INERT** | Body of `apply_neiso_coldsnap_derate`, reached only from the NEISO derate; guarded by `getattr(config, "neiso_coldsnap_derate_dualfuel_unswitched", False)`, which SOCO never sets. |
| `src/market_sim/model/interchange/neiso.py` | **INERT** | `inject_neiso_gas_coldsnap_derate`, which returns at `if iso != "NEISO"` (line 105). New `dual_switch_active` parameter defaults to `None` = the legacy path, byte-identical. |
| `src/market_sim/model/interchange/spec.py` | **INERT** | +96 lines are **2020 and 2021 vintages appended to `MISO_SEAM_LADDER_BY_YEAR`** (miso-260). MISO's neighbour ladder; SOCO solves 2023–2025 and serves **measured EIA-930 `Total interchange`** with no priced `NeighborInterface` (card S4). |
| `scripts/run_calibration_full.py` | **INERT** | (a) the same NEISO flag; (b) NWPP-40's pool-benchmark branch. **Verified mechanically, not asserted:** `_is_pool_region("SOCO")` is **False**, `_POOL_HOURLY_MEMBERS` has exactly one key (`NWPP`), so SOCO keeps `load_eia_hourly_benchmark`. The `bench is None` → `not bench` change is a no-op for SOCO: the bench is **truthy in all three years** (`coal/gas/nuclear/wind/solar` present), and the genuine 2025 `NG: NG` spike repair still fires on exactly the four hours the keeper's own log names (1172, 1240, 2751, 7527). |

**All hunks INERT ⇒ rule 29(b) form 4 is valid, the committed keeper bundle IS the control, and no
control solve is spent.** This lane's own changes to `run_calibration_full.py` / `run_calibration.py`
(§2.1) are additive and `None`-defaulted, so they do not disturb the audit.

---

## 4. THE SOLVE (rules 16 / 32 / 34)

**ONE shard, ONE invocation, ONE bundle, all three registered years.** SOCO's registered year union,
enumerated from `frontend/data/backcast/registry/*.json` **before** anything is pruned (rule 35(b)):
**{2023, 2024, 2025}**.

```
uv run python scripts/run_calibration_full.py --iso SOCO --year 2023 2024 2025 \
    --measured-ct-heat-rates \
    --out-dir results/calibration/soco53_measured_ct_hr \
    --note "soco-53: measured CT_PEAKER loaded heat rates from SOCO's own CAMPD record (rule 14 [R-ACCURATE]); all-defaults otherwise, every offer band 1.0, authorized_price_tuning NONE"
```

No other flag. Years sequential inside one invocation (rule 12). The shard **pushes its bundle**
to its own branch via a `.gitignore` negation and a **plain `git add`** — never `git add -f`
(rule 34(a)) — including `dispatch/<year>_P1.parquet`, without which registration raises
`FileNotFoundError`. Budget from the keeper's measured timing: **< 11 min wall, cgroup peak RSS
2.65 GiB** — one shard comfortably.

**Config signature the shard must see, as its hard stop:** `measured_ct_heat_rates: true`,
every `offer_curve_by_group` band exactly `1.0`, `authorized_price_tuning` absent.

## 5. DOF ledger (rule 21 `[R-DOF]`) — unchanged at n_entries 3 / n_residual 1

This lane adds **no free parameter**. `offer_curve_by_group` stays at the identity on all 13
groups; `offer_curve_smoothing` stays unset; the single inherited residual entry
(`wefor_multiplier` = 0.7, audit C-15) is untouched. `measured_ct_heat_rates` is a
**measured-physical** input, not a parameter: its value is a committed per-plant measurement from
SOCO's own CAMPD record with zero degrees of freedom. `authorized_price_tuning` is declared
**NONE** and is unreachable in principle here.
