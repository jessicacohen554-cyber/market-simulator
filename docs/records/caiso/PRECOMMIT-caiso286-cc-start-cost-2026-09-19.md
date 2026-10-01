# PRECOMMIT caiso-286 — the MEASURED downtime-dependent CC start cost, declared before the coverage arithmetic is run

**Lane:** CAISO calibration · **Date:** 2026-09-19 · **Keeper UNCHANGED**
`2026-09-12-caiso-275-gascoupling` · **LP spent so far: ZERO, and none is authorized by this
document.** Predecessor: `docs/RESULT-caiso285-bridge-candidacy-2026-09-17.md`, whose §8 named this
session's job — *"find out what a CAISO CC actually charges to restart after 8–24 hours down"* — as a
**measured-input question (rule 14 `[R-ACCURATE]`)**, to be answered before any solve and with its
own PRECOMMIT.

This document exists to fix **one number and two verdict words before the coverage arithmetic is
run**. §5 states the declared value. §7 states the cuts. §8 names BOTH outcomes, including the one
this lane is instructed to be willing to report.

---

## 1. The object, inherited and NOT re-derived (rule 28 `[R-MECH-MATRIX]` (a))

caiso-285 closed the CAISO RA bridge's belly-coverage deficit down to a single term. Its measured
findings are inputs here, not questions:

* The bridge holds a gap iff `startup_per_mw > (mc_gap − lmp_gap) × min_load_frac × gap_hours`
  (`model/commitment.py:1225-1240`, verified in place at HEAD this session).
* MW-weighted over all 1,866 belly-touching `S3_5` gaps: `mc_gap` **$31.36/MWh**, gap **11 h**,
  `min_load_frac` **0.26** → the bridge needs a gap LMP of **+$14.24/MWh**. The belly clears at
  **−$6.71**. 99.88 % of belly weight fails at $0; 100.0 % fails at the actual price.
* Inverting that gives **THE BAR**: holding the median belly gap needs a start cost of
  **$96.9/MW** crediting the energy at $0, or **$115.4/MW** at the belly's actual price
  (p75 gap: $124.5 and $145.7).
* Every other suspect is dead: min-down eligibility (0.0 MW, 30/30 CC plants clear it),
  `caiso_ra_bridge_startup_aware` (0.0 MW), the surplus decommit screen (never reached), "the fleet
  does not anchor" (0.014), `caiso_ra_mustoffer_quantity_gate` (OFF on the keeper), and the
  storage-energy premise (falsified and inert).

**THE BAR IS NOT A TARGET.** It was obtained by inverting a residual. §8.3 records what this session
refuses to do with it.

## 2. What the model carries today

`BIN_STARTUP_COST_PER_MW["CC_REGULAR"] = 50.0` $/MW (`src/market_sim/data/fleet/eia860.py:3230`),
cited to *NREL/SR-5500-55433 (Kumar et al. 2012), consistent with the legacy CC_STARTUP_PARAMS /
CT_STARTUP_PARAMS midpoints.*

Path verified at HEAD this session: for a CAMPD bin `_ra_bridge_unit_params`
(`model/commitment.py:561-606`) takes `startup = gen.startup_cost_per_mw`, i.e. the bin constant —
so **$50.0 flat is exactly what the restart inequality sees**, on all 30 CC plants and on every gap
from 4 h to 24 h alike. Nothing in this repo carries a hot/warm/cold or downtime-dependent start
cost anywhere: `CC_STARTUP_PARAMS` / `CT_STARTUP_PARAMS` (`config/constants.py:589-598`) are single
values per heat-rate class.

## 3. Instrument survey — the handoff's three candidates, adjudicated by MEASUREMENT

### (a) CAISO's own published start-up cost bids — **DEAD, and measured dead, not assumed**

One trade date was fetched from the live OASIS GroupZip API
(`PUB_DAM_GRP`, `20240110`, 366,685 bytes, HTTP 200) and its CSV header and product census read in
full. The corpus carries **26 columns and 10 market products**, and **none of them is a commitment
cost**:

| | |
|---|---|
| products present | `EN` 34,349 · `SR` 1,587 · `RD` 1,253 · `RU` 1,138 · `NR` 271 · `RMD` 171 · `RMU` 163 · `RC` 41 · `LFU` 27 · `LFD` 26 |
| commitment-cost columns | **none** — no start-up, no minimum-load, no transition cost |
| what the curve columns hold | `SCH_BID_XAXISDATA` / `SCH_BID_Y1AXISDATA`, i.e. energy and AS bid curves only |

CAISO's Public Bid Data publishes **energy and ancillary-service bids**. Start-up cost, minimum-load
cost and transition cost are Master File / commitment-cost data and are **not in this corpus**, at
any date, so no amount of re-fetching reaches them. **Cost of establishing this: one HTTP request.**
Rule 28 (a): do not re-open `caiso-public-bids` for a start cost.

### (b) The NREL source the constant already cites — **RECOVERED IN FULL, and it is the instrument**

`docs.nrel.gov` and `www.nrel.gov` are refused by this environment's egress policy (gateway 502 to
CONNECT). The report was retrieved instead from **OSTI**, the DOE system of record:
`https://www.osti.gov/servlets/purl/1046269` → 1,395,634 bytes, 83 pages,
*Power Plant Cycling Costs*, N. Kumar, P. Besuner, S. Lefton, D. Agan, D. Hilleman, Intertek APTECH,
April 2012, NREL/SR-5500-55433. **This is the same document `eia860.py:3230` cites**, and it
distinguishes hot / warm / cold starts and keys them to offline hours — structure the repo took a
midpoint of and dropped. §4 reproduces it.

### (c) A CAMPD-derived start-fuel curve — **AVAILABLE, AND NOT NEEDED**

`data/raw/campd-unit-level/CA_{2019..2026}.parquet` carries `heatInput`, `opTime` and `grossLoad`,
and `scripts/data/derive_campd_cc_start_trajectory.py` is a standing precedent for exactly this
construction. It is **not executed**, because §4's Table 1-3 shows the quantity it would measure —
CC start-up **fuel** — is **0.20 MMBtu/MW of capacity**, i.e. **$0.44/MW** at the keeper's own 2024
CAISO gas price of $2.19/MMBtu. A derive whose entire output is 0.4 % of the bar cannot change any
verdict here, and rule 19 `[R-ONE-MECH]` and rule 23 `[R-FROZEN-DERIVE]` both argue against spending
a derive to learn it. Recorded as available and declined, with the reason, rather than left
unexamined.

## 4. THE MEASUREMENT — NREL/SR-5500-55433, transcribed verbatim

### Table 1-1, "Gas - CC [GT+HRSG+ST]" column — C&M cost per MW capacity, **CY2011 $**

| start type | ~25th centile | **median** | ~75th centile |
|---|--:|--:|--:|
| Hot | 28 | **35** | 56 |
| **Warm** | 32 | **55** | 93 |
| Cold | 46 | **79** | 101 |

### The downtime keying — Table 1-1, "Startup Time (hours)" row

> **Typical (Warm Start Offline Hours), Gas - CC [GT+HRSG+ST]: `5 to 40` (ST Different)**

and the report's own reading rule, §1.3 verbatim:

> *"The typical ranges of 'hour offline' for warm starts for each unit type are also presented — any
> start duration below this range would be a hot start, and any above this range would be a cold
> start."*

### Table 1-3 — Startup Fuel Input and Other Startup Costs, Gas-CC column

| | hot | warm | cold |
|---|--:|--:|--:|
| Startup Fuel (MMBTU/MW capacity) | 0.19 | **0.20** | 0.24 |
| Other Startup Cost (aux power, water, chemicals) $/MW | **n/a** | **n/a** | **n/a** |

Table 1-3's CC column is footnoted *"Data is for 1 GT and 1 HRSG Only, NO ST"*, and the report states
APTECH *"did not have a large enough data set to determine the other start cost values for combined
cycle units and has not reported the same."* Both are disclosed rather than papered over; both are
immaterial at $0.44/MW (even a 3× understatement is $1.3/MW against a $96.9 bar).

### Table 1-2 (the "Type 8" best-cycling-unit subset) — recorded, NOT used

Gas-CC medians: hot **31**, warm **44**, cold **60**. §8.3 states why this table is not the one
selected.

## 5. THE DECLARED VALUE — fixed here, ex ante, and never swept

**The belly is a WARM start, at every percentile, and this is decided by the data rather than
chosen.** caiso-285's MW-weighted belly gap distribution is p1 **8 h**, p25 **10 h**, p50 **11 h**,
p75 **13 h**, p99 **22 h**. NREL's Gas-CC warm band is **5 to 40 h**. **Every one of those five
percentiles lies strictly inside the warm band** — there is no percentile of the belly at which the
hot or the cold row is the applicable one, so the mapping rule below never has to adjudicate a
boundary case for this object.

**Mapping rule (fixed before the coverage arithmetic):** `gap < 5 h` → hot · `5 ≤ gap ≤ 40 h` →
**warm** · `gap > 40 h` → cold.

**Central estimate (fixed):** the **MEDIAN of Table 1-1** — the general population, not Table 1-2's
best-cycling subset, and not a centile of the spread.

**Escalation (fixed):** CPI-U, BLS series `CUUR0000SA0`, annual averages, **2011 → 2024**.
2011 = **224.939**, 2024 = **313.689** → factor **1.394552**. Both values were pulled from the BLS
public API this session; the 2024 value was cross-checked against FRED `CPIAUCNS`, which reproduces
BLS exactly on all nine overlapping years 2011–2019. Applied to the C&M term only — the fuel term is
already priced at the model's own 2024 gas price.

### THE NUMBER

| term | 2011 $/MW | 2024 $/MW |
|---|--:|--:|
| Table 1-1 Gas-CC **warm** C&M, median | 55.000 | 76.700 |
| Table 1-3 Gas-CC **warm** start fuel, 0.20 MMBtu/MW × $2.19/MMBtu | — | 0.438 |
| Other startup cost (aux/water/chemicals) | n/a | n/a |
| **DECLARED MEASURED WARM START COST** | **55.438** | **77.138** |

For completeness and for the response curve only, the same construction on the other two rows:
hot **$49.25** (2024$), cold **$110.61** (2024$).

## 6. What is being asked, in one line

**Does the measured, downtime-appropriate CC start cost reach the bar the belly's own arithmetic
sets?** $77.138/MW against $96.9/MW at a $0 credit, and against $115.4/MW at the belly's actual
price.

## 7. PRE-REGISTERED GATES

**G-A — the bar test.** Compare the §5 declared value to the caiso-285 bar. Verdict words, fixed:
* **CLEARS** iff declared ≥ **96.9** $/MW (the $0-credit bar).
* **BELOW THE BAR** iff declared < **96.9** $/MW.

**G-B — the exact coverage test, ZERO LP.** Recompute, exhaustively rather than from percentiles,
the mean belly MW whose restart inequality flips at the declared value. Method, fixed here:

1. Recover the caiso-285 instrumented 2024 bundle from its immutable SHA
   (`git checkout 203124e310f7be4f806ad968d6cf5755f96bbc00 -- results/calibration/caiso285_instr_2024`
   — 17 files, 96,114,526 bytes; **done before this document was written**, gitignored, unstaged, and
   incapable of reaching `main`).
2. Rebuild the keeper's own 2024 fleet through the **sanctioned** zero-LP route,
   `scripts.lib.bundle_fleet.reconstruct_bundle_fleet` **as repaired at caiso-285** (the repair that
   removed 200 phantom biomass rows; row alignment is re-asserted, not assumed).
3. Take `runs` from the bundle's committed `hourly/p0_commitment_2024.parquet` at the detector's own
   `0.05 × pmax` threshold — the equality caiso-285 asserted as its gate G2 and which is re-asserted
   here.
4. Over every eligible unit × every belly-touching gap, evaluate
   `startup_per_mw > (mc_gap − lmp_gap) × 0.26 × gap_hours` at the declared value, and weight the
   flips by the floor the LP would actually write (`target_mw × availability`).

**G-B is an UPPER BOUND and is reported as one.** It omits the `startup_aware` run screen (measured
at **0.0 MW** of belly coverage by caiso-285, so the omission is quantified rather than hoped) and
the surplus decommit screen, which can only **remove** bridges. If the upper bound is immaterial, the
true figure is immaterial a fortiori.

**Pre-registered materiality cut:** the CC_REGULAR belly deficit is **1,921.4 MW**.
* **MATERIAL** iff held ≥ **10 %** of it = **192.1 MW**.
* **IMMATERIAL** iff held < 192.1 MW.

**G-C — reproduction.** The rebuild must re-assert caiso-285's G2 row alignment and reproduce its
published $50 baseline coverage. A mismatch **stops the session** and is reported as a defect rather
than worked around.

## 8. THE OUTCOMES, BOTH NAMED BEFORE THE ANSWER IS COMPUTED

Rule 1 `[R-STRUCT]`, and the handoff's §4 trap, require this section to exist before §7 is executed.

**8.1 `MEASURED-BELOW-BAR` — the belly deficit is not in the start cost either.** If G-A returns
BELOW THE BAR and G-B returns IMMATERIAL, this session reports that the measured value **fails**, that
the single term caiso-285 left open is therefore **also exonerated**, and that the CAISO belly deficit
has no remaining identified mechanism in the RA bridge. It proposes no value, arms nothing, launches
no span, and says so plainly. **This lane is explicitly willing to report this outcome, and on the
numbers already in §5 it is the expected one.**

**8.2 `MEASURED-CLEARS` — the start cost is the object.** If G-A returns CLEARS and G-B returns
MATERIAL, the measured value becomes a candidate mechanism. Even then it is **not armed in this
session**: it would require its own arming PRECOMMIT, and a registrable span is **four year-shards**
(2022–2025, rule 34 `[R-SHARD-PROMOTABLE]` (c), rule 35 `[R-PROMOTE]` (c)), which is the owner's cost
to authorize.

**8.3 WHAT THIS SESSION REFUSES, named so it can be checked.**
* **The 75th centile is refused as a central estimate.** Table 1-1's warm 75th is $93 (2011$) =
  **$129.7** (2024$), which **would clear both bars**. Selecting it *because* it clears is precisely
  the fitted-mechanism selection rule 1 forbids. The spread is reported as a spread.
* **Table 1-2 is refused as a substitute.** Its warm median ($44) is *lower*; it is declined on the
  same principle, not because of which way it moves.
* **No sweep.** `startup_per_mw` is never varied against G-A or G-B to find a passing value. A
  response curve may be reported and, exactly as caiso-285 labelled its own threshold table, it is
  **CONTEXT ONLY**.
* **The escalation is not a free knob.** The conclusion is checked for invariance to it: at the
  median, **both** the unescalated $55.44 and the escalated $77.14 sit below the $96.9 bar, so the
  §8.1/§8.2 branch does not turn on the deflator. That invariance is reported either way.

## 9. Scope limits this session accepts up front

* **`BIN_STARTUP_COST_PER_MW` is a SHARED, CROSS-ISO constant**, applied wherever CAMPD bins are
  built (`eia860.py`), not a CAISO field. Any change to it moves every CAMPD-binned ISO's keeper and
  re-keys their caches. That makes the structural repair §8.2 would imply a **cross-ISO governance
  item**, not a CAISO-lane edit — rule 25 `[R-ISO-SCOPE]` and rule 27 `[R-PUSH]` both bear on it, and
  this session will not make it unilaterally whatever G-A returns.
* **No `ScenarioConfig` field is added.** No derive is re-run (rule 23 `[R-FROZEN-DERIVE]`).
* **No mechanism cell verdict moves** unless a mechanism is actually tested (rule 28 (b)); the
  `gas_commitment_bridge` cell's evidence line is extended with whatever §7 returns.
* **THE PARENT NEVER SOLVES** (rule 32 `[R-SHARD]` (a)). Everything in §7 is zero-LP: a git checkout,
  a `fleet_only` rebuild, and arithmetic over committed sidecars.
* **Nothing is deleted** (rule 31 `[R-RETAIN]`). The recovered caiso-285 bundle stays on local disk,
  gitignored; the promotion question is surfaced in the RESULT rather than pre-empted.

## 10. Cost, stated before it is spent

§7 costs **zero LP**. Should §8.2 fire and the owner authorize it, a registrable CAISO span is
**four year-shards (2022, 2023, 2024, 2025)**, one shard per year, each pushing its whole bundle
(rule 34 (a)), each pinned to a full 40-character SHA. **Nothing in this document authorizes that**,
and no shard is launched from it.
