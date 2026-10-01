# PRECOMMIT — miso-298 — the owner-ruled MISO gas form ALONE over the full span 2019–2025: marginal commodity at the zone's measured daily hub PLUS the plant's measured variable transport; no coal change

```
STATUS  : LAUNCHED on this document's commit SHA (the pin; every shard carries it as source_revision)
LANE    : miso-298 (owner ruling 2026-10-01, miso-297 decision card "miso-298 lane": "Gas form alone, full span (Recommended)")
KEEPER  : 2026-09-28-miso-280-splitremap (results/calibration/miso280_span, 2019-2025), legs solved at 8f765fef
ARM     : keeper recipe + EXACTLY TWO declared fields (§2): miso_gas_marginal_commodity_pricing=true,
          miso_gas_variable_transport=true. offer_curve_by_group byte-identical to the keeper (K cell untouched)
CONTROL : none solved. G-DRIFT 8f765fef..this SHA (§4): the keeper bundle IS the control (rule 29(b) form 4)
SHARDS  : 7 arm legs, one year each 2019-2025 (rules 32-36), pinned to this document's commit SHA; 2022 first (--budget 120)
DATA    : DATA PROFILE: miso — no intake; every input the shards read is pinned in _miso298_shard_check.INPUT_SHA
DOF     : +0. Zero fitted scalars: a traded hub and a frozen-derive transport table (rule 23); nothing tuned
PHASE 0 : zero LP — the miso-297 census already measured this form's static footprint in every year: the
          "joint|1.00" rows of results/phase0/miso/_miso297_joint_census.json (§3). Nothing here needed a solve
```

## 1. The ruling, and how rules 1, 13 and 14 are met

**Owner ruling (2026-10-01, miso-297 decision card *"What should miso-298 do?"*; miso-297 could not log it — recorded
verbatim here and in `docs/calibration-log/miso.md`):** **"Gas form alone, full span (Recommended)"** — described in the
card as: 7 shards of the owner-ruled convention only (hub + measured variable transport, no coal change). Settles the
two O cells over 2019–2025. Census says: no static coal collapse; CC fuel up $0.07–0.14/MMBtu in 2019–2022 (q1–q2
error +0.3 to +1.2), down in 2023–2025 (−0.8/−0.4/0.0). C1 over the span is the open question. The alternatives the
owner declined: re-identify the coal econ multiplier at the census hump (m = 0.80); record and move on; other.

**What the form is.** The convention the owner ruled on 2026-09-06 (miso-225 PRECOMMIT §1): a MISO gas offer's fuel
cost is the marginal commodity — the zone's measured daily hub (Chicago Citygate flow-day staircase for the Chicago and
MidCon zones, Henry Hub for MISO-South; `data/raw/gas-prices/miso_citygate_daily.csv`, `henry_hub_daily.csv`,
zone→hub map `data/raw/miso_zonal_gas_hub.csv`) — PLUS the plant's measured variable transport
(`data/raw/reference/miso_gas_variable_transport.csv`, a frozen derive from EIA-923 plant receipts: the burn-varying
part of each plant's print-over-hub wedge; the fixed/reservation part is NOT in the offer). It replaces the EIA-923
monthly average delivered print (a lagged average that carries fixed charges) on every MISO gas row.

| rule | requirement | how this arm meets it |
|---|---|---|
| 1 `[R-STRUCT]` | right structure first; fit is not the objective | this is the owner-ruled structural convention for what a gas unit's marginal fuel cost is. A worse fit in any year is REPORTED at full magnitude, never hidden, and does not by itself kill the arm unless a §5 kill rule fires. No band, adder, haircut or multiplier is touched (`offer_curve_by_group` byte-identical, shard check HARD 1) |
| 13 `[R-MEASURED]` | a reproducible physical/market input, never the answer | a traded hub price and a per-plant transport rate are inputs a forward year produces from forward drivers (the forecast path's hub trajectory + basis; the transport table is a plant attribute). Neither is pinned to a generation or price actual; the table was derived on 2023–2025 receipts and is applied unchanged to 2019–2022 (rule 23: no re-derive without new source data) |
| 14 `[R-ACCURATE]` | measured over estimated; never revert to an estimate because it fits | the hub + variable transport is the measured marginal cost; the average print it replaces is the estimate (it averages fixed charges into a $/MMBtu). The census (§3) says the swap WORSENS the static low-load price in 2019–2022; under rule 14 that is reported as a discovered question (what else prices the 2019–2022 CC margin), not a reason to keep the print |
| 19 `[R-ONE-MECH]` | one mechanism per phenomenon | the hub form supersedes, on every gas row, the print, the winter shape overlay, the winter daily-delivered form (`miso_winter_gas_daily_delivered`, keeper `true`, INERT under the first field: `run_calibration.py` ~5177 — the marginal applier returns a written-mask so the winter-delivered applier is never called) and the zonal basis increment. Nothing is stacked |
| 24/25 | on-registry, ISO-scoped | both fields are `ScenarioConfig` fields recorded in `run_config.json`; both are MISO-gated |

## 2. The arm (exactly two fields; one config for 2019–2025)

| field | keeper | arm | what it does |
|---|---|---|---|
| `miso_gas_marginal_commodity_pricing` | false | **true** | every MISO gas row priced at its zone's daily hub (`data.fuel.basis.miso.apply_miso_gas_marginal_commodity`); supersedes the EIA-923 average print, the winter shape overlay, the winter daily-delivered form and the zonal increment on those rows (rule 19) |
| `miso_gas_variable_transport` | false | **true** | adds the plant's measured variable transport over the hub: own-plant rung, else `zone\|group` pooled rung, else `group` rung, else the MISO-wide $0.5036/MMBtu (`.pool.csv`) — the declared ladder of the frozen derive. Refuses to run without the first field, and refuses the BARE hub when the table is absent (the killed miso-224 form) |

Everything else is the keeper recipe: `offer_curve_by_group` (the K table, including the four coal subclasses' bands),
`coal_econ_srmc_bound`, the seven `-splitremap-` companions, the two data-forced reserve fields partitioned at 2023,
the per-year `gas_offer_margin_anchor`. `miso_winter_gas_daily_delivered` stays `true` in the recorded config and is
inert by construction (above); the shard check requires its log line ABSENT and the marginal-commodity line PRESENT
**with** the transport clause.

**The log lines the shard check requires** (`src/market_sim/data/fuel/basis/miso.py` ~599–615): PRESENT
`"MISO gas marginal-commodity pricing ("` AND `"PLUS the derived per-plant variable transport"`; ABSENT
`"MISO winter daily delivered gas ("`, `"MISO winter citygate daily ("`, `"with NO transport adder (the bare-hub
miso-224 form)"`.

## 3. Phase 0 (zero LP): the form's static footprint, from the miso-297 census

Every number below is the `"joint|1.00"` row of `results/phase0/miso/_miso297_joint_census.json` (the ruled gas form
armed, coal multiplier 1.00 = this arm exactly) against the `"coal_only|1.00"` row (= the keeper stack), both the
fleet-only rebuild of the recipe cleared at the keeper's own P1 thermal quantity every hour (the miso-296 block-B
construction; `scripts/probes/_miso297_joint_census.py`). Static re-merits at a fixed quantity; the LP decides.

### 3.1 Fuel level (identity: the two legs differ on gas rows only; `non_gas_rows_identical = true` in every year)

| cap-weighted $/MMBtu | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| all gas: keeper print → ruled form | 2.958 → 3.299 | 2.441 → 2.748 | 4.855 → 5.053 | 6.882 → 7.203 | 3.076 → 3.121 | 2.757 → 2.903 | 3.871 → 4.066 |
| CC_REGULAR: keeper → ruled | 2.686 → 2.796 | 2.238 → 2.306 | 4.529 → 4.616 | 6.670 → 6.809 | 2.920 → 2.675 | 2.606 → 2.477 | 3.674 → 3.626 |
| CC_REGULAR Δ | **+0.110** | **+0.068** | **+0.087** | **+0.139** | **−0.245** | **−0.129** | **−0.048** |
| CC_REGULAR econ: max \|Δmc − HR·Δfuel\| $/MWh | 6.69 | 1.65 | 2.12 | 3.89 | 3.44 | 1.80 | 1.87 |

Reading: the own-plant variable transport on CC_REGULAR ($0.35/0.36/0.28/0.26/0.25/0.26/0.24 cap-weighted, 2019–2025)
exceeds the print-over-hub wedge in 2019–2022, so the ruled form RAISES CC fuel there, and is below it in 2023–2025,
so it LOWERS CC fuel there. All-gas fuel rises in every year (CT_PEAKER v = $1.33, ST_GAS v = $0.99 in 2019).

### 3.2 Transport-table coverage per fleet (the table was derived on 2023–2025 receipts; §3.7 of PRECOMMIT-miso297)

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| gas plants in fleet / with own-plant rung | 321 / 89 | 324 / 93 | 321 / 95 | 322 / 98 | 324 / 100 | 327 / 100 | 350 / 102 |
| gas capacity on own-plant rung | 68 % | 68 % | 70 % | 72 % | 73 % | 73 % | 74 % |
| CC_REGULAR capacity on own-plant rung | 86 % | 86 % | 88 % | 89 % | 91 % | 90 % | 91 % |
| CT_PEAKER / ST_GAS own-plant share | 64 / 77 % | 65 / 76 % | 66 / 79 % | 66 / 82 % | 67 / 86 % | 66 / 84 % | 67 / 88 % |
| v cap-wtd: CC_REGULAR / all gas | 0.35 / 0.84 | 0.36 / 0.81 | 0.28 / 0.72 | 0.26 / 0.75 | 0.25 / 0.71 | 0.26 / 0.72 | 0.24 / 0.71 |

**Fallback, named:** a plant absent from the table takes the derive's own ladder — `zone|group` pooled rung, else
`group`, else the MISO-wide $0.5036 (`miso_gas_variable_transport.pool.csv`). That is the mechanism's documented
behaviour, not a choice made here; 26–32 % of gas capacity (9–14 % of CC_REGULAR) is on a pooled rung.

### 3.3 Static census (P1 bid-stack coal marginal share) and static dispatch move

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| IMM SOM Table 1 coal SMP share | 0.47 | 0.40 | 0.35 | 0.24 | 0.36 | 0.36 | n/a |
| coal share all hours: keeper → arm | 0.432 → 0.462 | 0.254 → 0.275 | 0.371 → 0.384 | 0.177 → 0.161 | 0.215 → 0.221 | 0.197 → 0.204 | 0.277 → 0.282 |
| coal share q1: keeper → arm | 0.16 → 0.20 | 0.07 → 0.08 | 0.38 → 0.41 | 0.32 → 0.29 | 0.11 → 0.10 | 0.07 → 0.08 | 0.22 → 0.25 |
| coal share q5: keeper → arm | 0.63 → 0.63 | 0.48 → 0.50 | 0.28 → 0.29 | 0.06 → 0.06 | 0.29 → 0.33 | 0.34 → 0.34 | 0.17 → 0.15 |
| static Δ mean GW, coal | +0.36 | +0.22 | +0.25 | +0.07 | −0.15 | −0.01 | +0.02 |
| static Δ mean GW, CC_REGULAR | −0.46 | −0.40 | −0.27 | −0.16 | +0.48 | +0.05 | −0.00 |
| static Δ mean GW, all gas | −0.55 | −0.41 | −0.31 | −0.21 | +0.39 | +0.09 | −0.03 |
| static Δ mean GW, seam imports | +0.19 | +0.19 | +0.07 | +0.14 | −0.23 | −0.07 | +0.01 |

Pooled 2019–2024 coal share 0.274 → 0.284 (+0.010): **no static coal collapse** (the miso-224 bare hub, with the
transport stripped, took −11.9 TWh of COAL_PRB in 2023). ×8.76 converts GW to TWh/yr; miso-224/225 measured the LP
converting ~0.27× of a static coal move.

### 3.4 Static price (bid stack vs the zone-resolved actual, load-weighted by measured zonal demand)

| $/MWh | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| actual q1 / q2 median | 19.2 / 21.2 | 15.1 / 17.1 | 23.3 / 25.8 | 40.2 / 48.4 | 19.6 / 23.1 | 16.9 / 20.4 | 24.2 / 27.7 |
| keeper stack q1 / q2 median | 22.5 / 25.1 | 18.2 / 21.4 | 27.4 / 29.9 | 41.1 / 45.8 | 25.4 / 28.6 | 21.5 / 24.9 | 30.5 / 33.7 |
| arm stack q1 / q2 median | 23.3 / 25.8 | 19.1 / 21.6 | 27.8 / 30.3 | 42.1 / 47.1 | 24.5 / 27.7 | 20.8 / 25.0 | 30.7 / 33.6 |
| LW error all hours: keeper → arm | +1.38 → +1.84 | +1.80 → +2.24 | −4.77 → −4.36 | −12.43 → −11.62 | +1.69 → +1.22 | +0.55 → +0.45 | −2.74 → −2.60 |
| LW error q1–q2: keeper → arm | +2.87 → +3.41 | +3.33 → +3.81 | −0.48 → −0.13 | −1.72 → −0.54 | +4.82 → +4.06 | +3.56 → +3.17 | +3.19 → +3.18 |
| Δ q1–q2 error (arm − keeper) | **+0.54** | **+0.48** | +0.35 | +1.18 | **−0.76** | **−0.39** | −0.01 |
| startup markup at the q1–q2 margin (median) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### 3.5 Keeper baselines the shards are read against (committed bundle `miso280_span`; `_miso297_readout_keeper.json`)

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| C1 COAL_PRB (model − actual TWh, band ±8) | +6.40 | +3.62 | +5.69 | +5.28 | −2.65 | −0.27 | SKIPPED |
| C1 COAL_BIT | −0.94 | −4.52 | −0.37 | +5.69 | −1.53 | −0.64 | SKIPPED |
| C1 CC_REGULAR | +4.20 | −2.39 | −6.01 | −4.09 | +0.21 | +1.82 | SKIPPED |
| C1 ST_GAS | **−8.00 FAIL** | −6.40 | −5.24 | −5.11 | −0.23 | −1.90 | SKIPPED |
| C1 CT_PEAKER | +0.82 | −3.62 | −4.92 | −5.25 | −3.39 | −4.09 | SKIPPED |
| C3a (LW mean price, %) | +8.7 | **+11.6 FAIL** | −5.6 | −5.1 | +8.4 | +5.1 | −1.1 |
| C3b (shape) | PASS | PASS | **0.201 FAIL** | PASS | PASS | PASS | PASS |
| K-3 keeper P1 coal marginal share (IMM) | 0.432 (0.47) | 0.254 (0.40) | 0.371 (0.35) | 0.177 (0.24) | 0.215 (0.36) | 0.197 (0.36) | 0.277 (n/a) |
| K-4 keeper P1 q1–q2 LW error $/MWh | +3.81 | +4.09 | +1.08 | +4.34 | +5.62 | +4.10 | +4.57 |
| K-4 keeper P1 all-hours LW error | +2.24 | +2.54 | −2.20 | −3.81 | +2.54 | +1.50 | −0.46 |

(2025 C1 cells are SKIPPED by the preliminary EIA-923 vintage and are read from the C2 family reconcile. The K-4 keeper
row is the P1 LP's own price; §3.4 is the static bid stack — the two differ by the LP's commitment and congestion.)

## 4. G-DRIFT — keeper legs `8f765fef` vs this SHA (rule 29(b))

Two records: `docs/records/miso/GDRIFT-miso297-keeper-8f765fef-2026-10-01.md` (8f765fef..06394e30: 190 files, 0 LIVE)
and `docs/records/miso/GDRIFT-miso298-keeper-8f765fef-2026-10-01.md` (06394e30..7a65272a, the branch point: 7
solve-path files, 0 LIVE — the rule-15 `unit_marginal` sidecar writer, INERT for dispatch; `ercot_ordc_published_curve`
and its ORDC code, ERCOT-gated; the NWPP-NEXT-16 per-unit fuel-split deletion, unreachable under
`campd_per_unit_attribution=False`; the `(n_steps,)` ORDC penalty broadcast, value-identical).
`solve_surface_register.py --diff 8f765fef HEAD`: 19 names added (declared, move no key), 2 moved re-keying ERCOT 1 /
PJM 1 / **MISO 0**. Form 4 holds: the committed keeper is the control; no control solve.

**This arm's own code and data are byte-identical to what miso-225 solved** (AST-sliced `apply_miso_gas_marginal_commodity`
and `_miso_gas_variable_transport_vector`, both field declarations, the transport table + pool, the zone→hub map, both
daily hub series: `git diff --stat 8f765fef HEAD` empty on all of them — GDRIFT-miso297 last table row).

## 5. Predictions and kill rules (fixed now; directions only; nothing is selected on a result)

Predictions (from §3; the LP converts a static move at well under 1:1):

1. **CC_REGULAR** falls in 2019–2022 (CC fuel +$0.07–0.14) and rises in 2023–2025 (−$0.05 to −$0.25); **coal** (COAL_PRB
   first, COAL_BIT) is the mirror: up in 2019–2022, down in 2023–2024. 2019 is the exposed year (COAL_PRB +6.40 inside
   an 8 TWh band; static coal +0.36 GW ≈ +3.2 TWh before conversion).
2. **ST_GAS** moves further from actual in every year (own-plant v ≈ $0.99–1.0/MMBtu on a steam heat rate = +$10/MWh);
   CT_PEAKER likewise (v ≈ $1.33) but it is rarely marginal.
3. **Imports** move with the internal price: up in 2019–2022, down in 2023–2024 (the seam ladders clear against the
   internal price; miso-224/225).
4. **C3a 2019 and 2020 worsen** (+8.7 → higher; +11.6 → higher); **C3a 2023 and 2024 improve**; 2021/2022/2025 (already
   negative) move toward zero.
5. **C3b 2021** (Uri + fall coal conservation, routed) does not change status; C1 ST_GAS 2019 (routed) stays FAIL.

Kill rules (the arm is KILLED and no promotion is recommended if any fires):

- **K-1 no C1 class PASS→FAIL in any year** (band ±8 TWh / ±3 pp; 2025 C1 SKIPPED cells are read from the C2 family
  reconcile and reported, not gated).
- **K-2 C1 COAL_PRB, COAL_BIT, COAL_LIGNITE, COAL_WC and CC_REGULAR within band in every year, or moving toward actual.**
- **K-4 the quintile-1–2 load-weighted price error shrinks in 2023 and in 2024** (the two years where the form lowers
  the CC margin by more than $0.1/MMBtu; zone-resolved actual, measured zonal demand, `_miso297_shard_readout.py`
  on the composed span against `_miso297_readout_keeper.json`).
- Structural stops: S-1 recipe (every leg = keeper + exactly §2, shard check HARD 1; `offer_curve_by_group` byte-
  identical), S-1b the seven `-splitremap-` companions read (HARD 1b), S-2 log (marginal-commodity line WITH transport;
  winter-delivered and bare-hub lines ABSENT; HARD 5), S-3 slack reported with its hours, S-4 `hourly/unit_marginal_
  <year>.parquet` present in every leg (HARD 6, rule 15).

REPORTED at full magnitude, never gates here: **C3a 2020 (+11.6 %, predicted worse)**, C3a 2019, C3a 2022 (routed; the
Elliott tail), C3b 2021 (routed), C1 ST_GAS 2019 (routed, South steam out of merit), K-3 (the coal marginal share per
year beside the IMM — the census predicts +0.01 to +0.03 in 2019–2021 and ≈0 elsewhere; it is a readout, not a gate),
West/Plains congestion (`internal_congestion_split`, G), C3c (ledgered caveat), D-A amplitude, slack hours.

## 6. Decision rule and the promotion question's form

Every gate C1–C8 is reported per year, keeper and arm side by side, at full magnitude. **Promotion is the owner's**
(rule 31): no solved bundle is deleted before the ruling, and the RESULT names where each leg sits on `main`.

- If no kill rule fires: the RESULT states the full-span determination beside the keeper's (NOT-YET on C1 ST_GAS 2019,
  C3a 2020, C3b 2021) and asks, as a decision card, *"Promote 2026-10-01-miso-298-gas-form over
  2026-09-28-miso-280-splitremap?"* with the gate table. The recommendation follows rule 1: the structurally ruled
  convention is the keeper candidate unless the determination is worse (more failing criterion-years) — then the RESULT
  says so and the card carries both readings.
- If a kill rule fires: the RESULT says KILLED, names the rule and the number, and asks what the next lane is.
- Either way the two `O` cells move on the scored result (`K` if promoted; `R` if killed by a rule, with the numbers;
  the full-span test the `O` verdicts waited for has then been run) in `docs/codebase-site/data/mechanism-matrix/MISO.js`
  and §5.4 of `docs/mechanism-testing-matrix.md`.

## 7. DOF ledger and attestation text (written into the composite before the PR)

`governance.mechanism_armed` (replaces the inherited block; the keeper's is carried to `mechanism_armed_inherited`):

- `field`: "miso_gas_marginal_commodity_pricing + miso_gas_variable_transport"
- `value`: true / true
- `level`: "NO LEVEL PARAMETER. Fuel = the zone's measured daily hub (Chicago Citygate flow-day for Chicago/MidCon zones,
  Henry Hub for MISO-South) + the plant's measured variable transport (frozen derive, own-plant rung else zone|group /
  group / MISO-wide $0.5036); zero fitted scalars"
- `free_parameters_added`: 0
- `basis`: "owner ruling 2026-09-06 (convention: MISO gas = marginal commodity + variable transport) and 2026-10-01
  (miso-297 card 'Gas form alone, full span'); rules 13/14: a traded hub and a per-plant transport rate, forward
  analogue = the forecast path's hub + basis"
- `one_mechanism`: "rule 19: supersedes on every gas row the EIA-923 average print, the winter shape overlay, the winter
  daily-delivered form (miso_winter_gas_daily_delivered inert under this field) and the zonal increment"
- `control`: "the committed keeper results/calibration/miso280_span (rule 29(b) form 4); G-DRIFT 8f765fef..pin 0 LIVE
  (GDRIFT-miso297 + GDRIFT-miso298); solve_surface_register MISO moved rows 0"
- `prereg`: "docs/records/miso/PRECOMMIT-miso298-gas-form-alone-2026-10-01.md @ <pin>, pushed BEFORE any shard"
- A `miso298` block: precommit, pin, delta (the two fields), ruling (verbatim), legs (year → shard SHA), control,
  dof_added 0, measured_inputs (daily hubs, EIA-923 plant receipts behind the transport derive).

`authorized_price_tuning` is UNCHANGED (the K table is not touched). DOF ledger (`build_dof_ledger.py`): **+0**.

## 8. Arm command, shard check, compose

Per year Y, one shard each (`scripts/shard_prompt.py --iso MISO --all-years --sha <pin> --lane miso-298 --bundle
results/calibration/miso280_span --set miso_gas_marginal_commodity_pricing=true --set miso_gas_variable_transport=true
--note "..."`; `--budget 120` for the 2022 leg, launched first):

```
python3 scripts/replay_keeper.py results/calibration/miso280_span --years <Y> \
  --out-dir results/calibration/miso_298_<Y> \
  --set miso_gas_marginal_commodity_pricing=true \
  --set miso_gas_variable_transport=true \
  --note "miso-298 gas form alone <Y>: MISO gas at the zone's daily hub + measured per-plant variable transport (owner-ruled convention; no coal change)"
```

Shard check: `scripts/probes/_miso298_shard_check.py --leg results/calibration/miso_298_<Y> --year <Y> --log <log>`
(recipe = keeper + exactly §2; the seven `-splitremap-` companions; pinned inputs incl. the two daily hubs, the transport
table + pool and the zone→hub map; vintage; classifier; log markers; `unit_marginal_<Y>.parquet`). Compose:
`scripts/probes/_miso298_compose_span.py --out results/calibration/miso298_span` (MUST_AGREE carries both gas fields).
Score: `scripts/calibration_verdict.py`; `scripts/legitimacy_diagnostics.py`; K-3/K-4 `scripts/probes/
_miso297_shard_readout.py --bundle results/calibration/miso298_span --out results/phase0/miso/_miso298_readout_arm.json`.

## 9. Launch record

Filled in the RESULT (`docs/records/miso/RESULT-miso298-gas-form-alone-2026-10-01.md`): the pin, each leg's shard
session and commit SHA, wall time and memory peak, and the shard-check verdicts. This document is not edited after the
pin.
