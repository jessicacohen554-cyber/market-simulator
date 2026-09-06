# FINDING — SCN-WS1b (r2): the six-ISO carbon paired probe

**Lane:** SCN-WS1b-r2 (relaunch/re-scope of SCN-WS1b) · **Model:** `claude-opus-5`
**Branch:** `claude/scn-ws1b2-carbon-sixiso-r4hm-t5hdbz` · **Date:** 2026-09-06
**Charter:** plan `docs/handoffs/forecast-scenario-readiness-plan-2026-09.md` §7 "WS-1b" leg 1
(= §3 WS-1 items 4–6); desk ledger `docs/handoffs/scenario-desk-ledger-2026-09.md` §0 r#6 am.1.
**PRECOMMIT:** `docs/handoffs/PRECOMMIT-scn-ws1b-2026-09-06.md` (unedited) +
`docs/handoffs/PRECOMMIT-scn-ws1b-2026-09-06-ADDENDUM.md` (§(a)–(f), all pushed **before** the
first solve). **DATA PROFILE:** `all`.

---

## 0. Bottom line

<!-- FILL: headline after solves -->

---

## 1. The phase-0 result that re-scoped the lane (zero LP)

**The charter's leg 1 as written — six paired 2026-only T0 runs, REF vs `carbon_price_path=mid` —
is structurally unrunnable, and the reason is not the floor.**

`CARBON_PRICE_PATHS` (`src/market_sim/config/fuel_trajectories.py:1132-1137`) anchors **every**
registered RFF path at **$0 in 2026** — 2026 is the paths' common origin knot:

| path | **2026** | 2027 | 2028 | 2030 |
|---|---|---|---|---|
| zero | **0.0000** | 0.0000 | 0.0000 | 0.0000 |
| low | **0.0000** | 2.0000 | 4.0000 | 8.0000 |
| mid | **0.0000** | 3.7500 | 7.5000 | 15.0000 |
| high | **0.0000** | 7.5000 | 15.0000 | 30.0000 |

So **no `carbon_price_path` value of any kind can produce a signal in a 2026-only solve.** All
twelve chartered arms would have been six pairs of *byte-identical configs*, and ~82 minutes of LP
would have measured solver determinism rather than carbon.

Measured through the solves' own builder (`reference_config(iso, 2026, 2030, cmc=False)`),
instrument `docs/handoffs/scn-ws1b/phase0-recensus-path-2026-09-06.py`:

| ISO | REF 2026 | ARM 2026 | **Δ 2026** | Δ 2027 | Δ 2028 | Δ 2030 | cause of the 2026 null |
|---|---|---|---|---|---|---|---|
| ERCOT | 0.0000 | 0.0000 | **0.0000** | +3.75 | +7.50 | +15.00 | **RFF mid knot at 2026 is $0** |
| CAISO | 30.0242 | 30.0242 | **0.0000** | 0.00 | 0.00 | 0.00 | floor: program > path, every year |
| PJM | 0.0000 | 0.0000 | **0.0000** | +3.75 | +7.50 | +15.00 | **RFF mid knot at 2026 is $0** |
| MISO | 0.0000 | 0.0000 | **0.0000** | +3.75 | +7.50 | +15.00 | **RFF mid knot at 2026 is $0** |
| NYISO | 23.6363 | 23.6363 | **0.0000** | 0.00 | 0.00 | 0.00 | floor: program > path, every year |
| NEISO | 26.0545 | 26.0545 | **0.0000** | 0.00 | 0.00 | 0.00 | floor: program > path, every year |

**Two independent causes, and the charter anticipated only one.** The charter expected the arm to
be inert on CAISO / NYISO / NEISO (the S2 floor — correct, and confirmed) and **live on ERCOT /
PJM / MISO**. It is not live there at 2026: both arms resolve to $0 because the path's own 2026
knot is zero. Gate **G1 (premise)** therefore failed in all six ISOs, and under rule 29
`[R-SCREEN]` clause (0) the arms did not reach a solve.

**Re-scope, authorized by the desk and recorded in ADDENDUM §(f) before any LP:** extend to
`--start-year 2026 --end-year 2027` and score at **2027** — the first year the axis is live, and
still below `ccs_retrofit_available_year = 2028`, so ruling **S5**'s `gas_cc_ccs` hold does not
reach it and the pairs keep **zero CCS exposure**. Rule 29's own text prescribes this: *"a
mechanism measured INERT in the candidate screen year (screen it where it is live …)"*.

---

## 2. The resolved carbon trajectory under the S2 floor, per ISO

<!-- FILL -->

## 3. The paired T0 result at 2027

<!-- FILL: headline pair table per ISO -->

### 3.1 STOP-gate verdicts

<!-- FILL -->

### 3.2 Coal→gas re-ordering

<!-- FILL -->

## 4. LEAKAGE — `import_co2_mt_reported` beside `emissions_mt`, per ISO, as a number

<!-- FILL: the six-ISO leakage table + the tranche that moves + displaced fraction -->

## 5. My misses, reported at full magnitude

<!-- FILL -->

## 6. Wall / RSS per solve-year

<!-- FILL -->

## 7. LEG 2 IS HELD BY RULING S5

The NEISO/ERCOT T1-F **2026–2030 carbon ladder** (original PRECOMMIT §3.5) **was not run.**

**Why.** It spans 2028–2030, so it crosses `ccs_retrofit_available_year = 2028` (measured 2028 in
all six ISOs, original PRECOMMIT §2.3), so it moves `gas_cc_ccs`. SCN-WS2b measured that the CCS
emission-rate seam can make that CO2 answer **sign-wrong**: **+9.99 Mt as scored vs −6.01 Mt with
capture applied**, on NEISO 2030 (`FINDING-scn-ws2b-2026-09-06.md` §8). Ruling **S5** holds every
case carrying that exposure, and this ladder carries it in three of its five years.

**What is committed and unrun:** `docs/handoffs/scn-ws1b/launch_ladder.sh` and
`docs/handoffs/scn-ws1b/carbon-ladder-cases.yaml` (rungs `CARB-LO` / `CARB-MID` / `CARB-HI`).

**What releases it:** the capx lane's repair of the CCS emission-rate seam in
`src/market_sim/model/capacity_evolution/ccs.py` — **explicitly not this lane's file** (the routed
defect). After that repair the ladder runs as §3.5 specifies, with no other change. **Note the
form change carries into it:** §3.5's rungs were written as `carbon_price_delta` 15/25/50 while
D-1 was open; under the S2 floor the ladder should be re-expressed on the `carbon_price_path`
axis (`low`/`mid`/`high`), whose rungs are now meaningful — and which, per §1, only bites from
2027 on.

## 8. Scorecard rows and matrix cells landed

<!-- FILL -->

## 9. What remains for Stage A-LOAD

<!-- FILL -->
