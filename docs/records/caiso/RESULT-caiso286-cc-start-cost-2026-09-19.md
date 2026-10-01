# RESULT caiso-286 — the measured CC start cost lands BELOW the bar. And caiso-285's exoneration of the decommit screen does not survive a per-gap evaluation

**Lane:** CAISO calibration · **Date:** 2026-09-19 · **Keeper UNCHANGED**
`2026-09-12-caiso-275-gascoupling` · **LP SPENT: ZERO.** No shard was launched, no span, no
`ScenarioConfig` field, no constant changed, no derive re-run, nothing armed, nothing registered,
nothing deleted. Pre-registration:
`docs/PRECOMMIT-caiso286-cc-start-cost-2026-09-19.md`, pushed at
`7562f345d25eb96c7785f82b201c230f00f7402f` **before** the coverage arithmetic was written or run.
Every value, mapping rule, cut and verdict word below was fixed there.

---

## 0. The answer in one paragraph

A CAISO CC's belly gaps are **warm starts** — the belly's own 8–22 h gap distribution sits entirely
inside NREL's 5–40 h Gas-CC warm band — and the measured warm start cost is **$77.14/MW** (2024$),
against the caiso-285 bar of **$96.9/MW**. **G-A: BELOW THE BAR.** Per the handoff's own condition,
**no span follows**, and this session reports the §8.1 outcome it pre-registered itself to be willing
to report. But the exact zero-LP coverage recomputation turned up something sharper than the answer
it was sent to get: caiso-285's §6 finding that the restart inequality *"fails on 100.0 % of belly
weight at the actual price"* — the finding on which it **exonerated the surplus decommit screen** —
was computed by applying **one uniform price (the belly mean, −$6.71) to every gap**. On the
**per-gap** LMP the model code actually uses, the inequality **passes on 270.3 mean-belly-MW at the
incumbent $50**, and the committed floor array shows those gen-hours floored by **nothing at all**.
The inequality does **not** fail first, and the decommit screen is **back in scope**.

---

## 1. Instrument survey — the handoff's three candidates, adjudicated by MEASUREMENT

### (a) CAISO's own published start-up cost bids — **DEAD, measured dead, in one HTTP request**

One live trade date was pulled from the OASIS GroupZip API (`PUB_DAM_GRP`, `20240110`, HTTP 200,
366,685 bytes) and its header and product census read in full. The corpus carries **26 columns** and
**10 market products** — `EN` 34,349 · `SR` 1,587 · `RD` 1,253 · `RU` 1,138 · `NR` 271 · `RMD` 171 ·
`RMU` 163 · `RC` 41 · `LFU` 27 · `LFD` 26 — i.e. **energy and ancillary services only**. There is no
start-up, minimum-load or transition cost column at any date, so re-fetching the 2,919-trade-date
corpus could not have produced one. Rule 28 `[R-MECH-MATRIX]` (a): **do not re-open
`caiso-public-bids` for a commitment cost.**

### (b) The NREL source the constant already cites — **RECOVERED IN FULL, and it is the instrument**

`nrel.gov` and `docs.nrel.gov` are refused by this environment's egress policy (gateway 502 to
CONNECT). The report was retrieved instead from **OSTI**, the DOE system of record —
`https://www.osti.gov/servlets/purl/1046269`, 1,395,634 bytes, **83 pages** — and is the same
document `eia860.py:3230` cites: *Power Plant Cycling Costs*, Kumar, Besuner, Lefton, Agan, Hilleman,
Intertek APTECH, April 2012, **NREL/SR-5500-55433**. Its Table 1-3 is an embedded image and was read
by rendering the page, not by guessing at it.

### (c) A CAMPD start-fuel derive — **available, and DECLINED with the reason stated**

`data/raw/campd-unit-level/CA_{2019..2026}.parquet` carries `heatInput` / `opTime` / `grossLoad`, and
`derive_campd_cc_start_trajectory.py` is a standing precedent. Not executed: Table 1-3 puts CC start
**fuel** at **0.20 MMBtu/MW of capacity** = **$0.44/MW** at the keeper's own 2024 CAISO gas price of
$2.19/MMBtu. A derive whose entire output is **0.4 %** of the bar cannot move any verdict here.

## 2. The measurement — NREL/SR-5500-55433, transcribed

**Table 1-1, "Gas - CC [GT+HRSG+ST]", C&M cost per MW capacity, CY2011 $:**

| start type | ~25th | **median** | ~75th |
|---|--:|--:|--:|
| Hot | 28 | **35** | 56 |
| **Warm** | 32 | **55** | 93 |
| Cold | 46 | **79** | 101 |

**The downtime keying**, Table 1-1 "Startup Time (hours)" row, Gas-CC: **Typical (Warm Start Offline
Hours) = `5 to 40`**, with the report's own reading rule (§1.3): *"any start duration below this range
would be a hot start, and any above this range would be a cold start."*

**Table 1-3, same column:** startup fuel **0.19 / 0.20 / 0.24** MMBtu/MW (hot/warm/cold); *Other
Startup Cost (aux power, water, chemicals)* = **n/a** — APTECH *"did not have a large enough data set
to determine the other start cost values for combined cycle units."* Table 1-3's CC column is
footnoted *"1 GT and 1 HRSG Only, NO ST"*. Both limitations are disclosed; both are immaterial at
$0.44/MW.

**This is the structure the repo dropped.** `BIN_STARTUP_COST_PER_MW["CC_REGULAR"] = 50.0` cites this
report and carries **one flat number** for all 30 CC plants and every gap length.

## 3. The declared value (PRECOMMIT §5, fixed ex ante)

**The belly is a warm start, and the data decides that, not this session.** caiso-285's MW-weighted
belly gap distribution is p1 **8 h** · p25 **10 h** · p50 **11 h** · p75 **13 h** · p99 **22 h**, and
NREL's Gas-CC warm band is **5–40 h**. Every percentile is strictly inside it.

| term | 2011 $/MW | 2024 $/MW |
|---|--:|--:|
| Table 1-1 Gas-CC **warm** C&M, **median** | 55.000 | 76.700 |
| Table 1-3 warm start fuel, 0.20 MMBtu/MW × $2.19 | — | 0.438 |
| Other startup cost | n/a | n/a |
| **DECLARED** | **55.438** | **77.138** |

Escalation: CPI-U, BLS `CUUR0000SA0` annual averages, 2011 **224.939** → 2024 **313.689**
(factor **1.394552**), both pulled from the BLS public API and cross-checked against FRED `CPIAUCNS`,
which reproduces BLS exactly on all nine overlapping years 2011–2019.

## 4. Gate G-C — the reproduction, on SIX independent caiso-285 numbers

The recomputation is not a new measurement of the belly; it must land on caiso-285's published
values or it is wrong. It does, everywhere it can be checked:

| quantity | caiso-285 published | caiso-286 recomputed | |
|---|--:|--:|---|
| rebuilt fleet rows | 1,705 | **1,705** | ✓ |
| belly set `sha256_int32_le[:16]` | `c5948fb0d43620a1` | **`c5948fb0d43620a1`** | ✓ |
| bridge-eligible rows | 74 | **74** | ✓ |
| econ-eligible `CC_REGULAR` rows | 30 / 30 | **30** | ✓ |
| S3_5 belly-touching gaps | 2,481 | **2,481** | ✓ |
| S3_5 belly MW, availability-weighted | 1,193.0 | **1,193.0269** | ✓ |
| actual RA `min_gen` belly mean | 670.470 | **670.4704** | ✓ |
| share failing at uniform $0 | 0.9988 | **0.9992** | ✓ |
| share failing at uniform −$6.71 | 1.0000 | **1.0000** | ✓ |

Row alignment of the P0 sidecar and the `floors/` array against the rebuilt fleet is **asserted, not
assumed**, and passes on both legs.

**A defect in this session's own probe, found and fixed before any number was reported.** The first
draft read `config.zones` for the zone ordering. On a `fleet_only` rebuild that attribute is `None`,
so it fell through to `sorted(unique)` — putting `LA_BASIN` at index 0 where the fleet means `NP15` —
and **every gap LMP came from the wrong zone**. The zone map is now derived from the generators' own
`zone` attribute and asserted one-to-one and dense; the map is printed in the artifact
(`0 NP15 · 1 ZP26 · 2 LA_BASIN · 3 SDGE · 4 SP15_rest · 5 WECC_PNW · 6 WECC_DSW`). Every figure in
this document is post-fix. The pre-fix run is not quoted anywhere.

## 5. Gate G-A — **BELOW THE BAR**

| | $/MW |
|---|--:|
| **declared measured warm start cost** | **77.138** |
| bar, crediting the gap energy at $0 | 96.9 |
| bar, at the belly's actual price | 115.4 |

**$77.138 < $96.9 → `BELOW THE BAR`.** The ratio is **0.796**.

**Invariant to the deflator**, as PRECOMMIT §8.3 required be checked: the unescalated value is
**$55.438** and the escalated value **$77.138**, and *both* sit below the $96.9 bar, so the verdict
does not turn on the escalation choice.

**The refusals held.** Table 1-1's warm **75th centile** is $93 (2011$) = **$130.13** (2024$) and
**would clear both bars** — it was named in the PRECOMMIT as the thing not to pick, precisely because
picking it *because* it clears is the fitted-mechanism selection rule 1 `[R-STRUCT]` forbids. Table
1-2's "best cycling units" warm median ($44) would push the other way and was declined on the same
principle. `startup_per_mw` was never swept against a gate; the response curve in §6 is **CONTEXT
ONLY**.

## 6. Gate G-B — MATERIAL on the pre-registered statistic, and the statistic is measurably loose

Mean belly MW the restart inequality would pass, exhaustive over 2,481 gaps
(**upper bound**, as pre-registered — it omits the `startup_aware` run screen and the surplus
decommit screen, both of which can only *remove* bridges):

| start cost $/MW | | mean belly MW held (upper bound) |
|---|--:|--:|
| `context` warm p25 | 45.06 | 235.4 |
| `context` hot median | 49.23 | 265.8 |
| **incumbent flat** | **50.00** | **270.3** |
| `context` warm median, 2011$ | 55.44 | 305.6 |
| **DECLARED warm median, 2024$** | **77.14** | **491.6** |
| `context` bar at $0 | 96.90 | 679.1 |
| `context` cold median | 110.70 | 836.1 |
| `context` bar at price | 115.40 | 878.8 |
| `context` warm p75 | 130.13 | 1,040.7 |

Pre-registered cut: **MATERIAL** at ≥ 192.1 MW (10 % of the 1,921.4 MW CC belly deficit). The
declared value scores **491.6 MW** → **`MATERIAL`**, and the increment over the incumbent is
**+221.3 MW**.

**G-A and G-B therefore disagree, and this session reports that rather than picking the convenient
one.** The disagreement is not a contradiction: the bar is what it takes to hold the **median** gap,
while the gap distribution is wide, so a value below the median bar still flips the cheap tail.
caiso-285 labelled that inversion `CONTEXT_ONLY` for exactly this reason.

**What decides it is the looseness of the bound, which is measurable at the incumbent.** At
**$50 — the value the model actually ran** — the same upper bound scores **270.3 mean-belly-MW**, and
the committed `floors/2024_P1.npz` says the solve floored those gen-hours with **nothing**:

| | mean belly MW |
|---|--:|
| upper bound at the incumbent $50 | 270.279 |
| of which floored by **another mechanism** | **0.000** |
| of which floored by **nothing at all** | **270.279** |

So the bound overshoots the truth by **100 %** at the incumbent. The two omitted screens remove
*all* of it. Since more gaps qualify at $77 than at $50, the overshoot there is at least as large, and
the **true** increment is bounded above by +221.3 MW with no reason to believe it is not zero.

**A MATERIAL reading on a bound that is 100 % loose where it can be checked cannot carry a span.**
Combined with G-A, the §8.1 branch is the one this session reports — with the §8.2 half of the
disagreement stated at full magnitude rather than dropped.

## 7. THE FINDING — caiso-285 §6's exoneration of the decommit screen does not survive

caiso-285 §6 concluded:

> *"the failure is total at any price the belly can produce, and it is total **before** the decommit
> screen does anything — so the surplus reprice to −$20 is irrelevant, and the decommit screen is
> **EXONERATED from the arithmetic**."*

That rests on its threshold table, which applies **one uniform price to every gap** (the belly mean,
−$6.71). The model code does not do that. `model/commitment.py:1229` computes

```python
lmp_gap = float(np.mean(p1_prices[zone, end_prev:start_next]))
```

— **each gap's own mean LMP, over the whole gap**, including the shoulder hours inside the gap where
the price is well above the belly mean. Evaluated on that basis, over the identical 2,481-gap set:

| basis | share of S3_5 belly MW **failing** at the incumbent $50 |
|---|--:|
| uniform $0 (caiso-285's) | 0.9992 *(published 0.9988)* |
| uniform −$6.71 (caiso-285's) | 1.0000 *(published 1.0000)* |
| **per-gap LMP (what the code computes)** | **0.7735** |

**22.65 % of S3_5 belly weight — 270.3 mean-belly-MW — PASSES the restart inequality at the incumbent
value, and is floored by nothing.** The inequality does **not** fail first on 100 % of belly weight.
Something downstream of it is removing those bridges, and the only two candidates are the
`startup_aware` screen's **gap-merging** (it rebinds `runs = kept_runs`, so a dropped run between two
kept runs fuses two short gaps into one long one, raising `hold_cost` and, past 24 h, hitting the DA
horizon outright) and the **surplus decommit screen** in `_apply_economic_bridges`.

**This re-opens item 3 of caiso-285 §8's closed list, and it does so with new evidence rather than by
re-litigation** (rule 28 `[R-MECH-MATRIX]` (a)). It also refines its item 2: `S4 = 0.0 MW` measured
that the screen never *zeroes a unit outright*, which is a different claim from the screen being
inert — caiso-285 said so itself, and the gap-merging channel is the one its partition could not see.

**Why it could not be split here, and what would split it.** Both candidate screens need the **P0
dispatch in MW**, and the bundle persists only the bit-packed P0 **on/off** pattern
(`hourly/p0_commitment_2024.parquet`) — which is why caiso-285 inverted the inequality in the first
place. Splitting them needs an instrumented replay that persists the P0 dispatch array: **one year,
one shard**, the same shape as caiso-285's own probe.

## 8. A second finding — inside the bridge, the downtime curve degenerates to a single branch

The successor question caiso-285 posed was *"flat versus downtime-dependent."* The gap census answers
it structurally:

| start type | gaps scanned | belly MW at stake |
|---|--:|--:|
| hot (`gap < 5 h`) | **0** | 0.0 |
| **warm (`5 ≤ gap ≤ 40 h`)** | **2,481** | **1,193.0** |
| cold (`gap > 40 h`) | **0** | 0.0 |

The bridge's admissible gap window is bounded below by the unit's own `min_down` (4/6/8 h for CC) and
above by `DA_COMMITMENT_HORIZON_HOURS = 24` — so it lives inside **[4, 24] h**, which is almost
entirely inside NREL's warm band **[5, 40] h**. In 2024 **not one** of the 2,481 gaps falls outside
it.

**So, for this mechanism, installing the downtime structure is arithmetically identical to changing
one number** ($50 → $77.14). The flat-versus-keyed framing is real in the constant and real in the
source, but the RA bridge **never sees more than one branch of the curve**. A unit with
`min_down = 4 h` could in principle present a 4-hour (hot) gap in another year; none did in 2024.

## 9. What this closes, and what it opens

**Closed (rule 28 (a) — do not re-test without new evidence):**

1. **CAISO public bid data as a start-cost instrument** — measured, it carries no commitment cost.
2. **"What does a CAISO CC charge to restart after 8–24 h down?"** — **$77.14/MW** (2024$), NREL
   Gas-CC warm median + start fuel. The question caiso-285 left open is **answered**.
3. **The start cost as the belly's remaining explanation** — the measured value is **below** the bar,
   so the belly deficit is **not** in the start cost either.
4. **"Flat versus downtime-dependent" as a live distinction for this bridge** — §8; the admissible
   gap window sits inside one NREL start type.
5. **A CAMPD start-fuel derive for this object** — the quantity is $0.44/MW.

**RE-OPENED, with new evidence (§7):** the surplus **decommit** screen and the `startup_aware`
**gap-merging** channel, which between them remove 270.3 mean-belly-MW that the restart inequality
passes at the incumbent value. **This is the sharpest remaining object in the CAISO belly**, and it is
sharper than the one this session was sent after: it is a live mechanism removing real coverage,
rather than a constant that turned out to be roughly right.

**The successor, named and costed but NOT launched:** an instrumented 2024 replay persisting the
**P0 dispatch MW** (the one artifact caiso-285 did not land), which splits the 270.3 MW between the
two screens exactly. One year, one shard, its own PRECOMMIT — the caiso-285 shape.

**Left alone:** `S2` (the DA horizon), for caiso-285's own reason.

## 10. Governance ledger

* **Keeper UNCHANGED**, nothing registered, nothing promoted, nothing pruned. **Rule 15
  `[R-DASHBOARD]` is not engaged: no run was produced** — zero LP was spent.
* **Zero LP.** No shard launched (rule 32 `[R-SHARD]` (a): the parent never solves, and never needed
  to). Everything here is a git checkout, one `fleet_only` rebuild and arithmetic over committed
  sidecars.
* **No `ScenarioConfig` field**, no constant changed, no derive re-run (rule 23
  `[R-FROZEN-DERIVE]`), no offer-curve multiplier touched, no mechanism armed.
* **`BIN_STARTUP_COST_PER_MW` was NOT edited**, and PRECOMMIT §9 says why: it is a **shared,
  cross-ISO** constant applied wherever CAMPD bins are built, so changing it moves every CAMPD-binned
  ISO's keeper and re-keys their caches. That is a cross-ISO governance item (rules 25
  `[R-ISO-SCOPE]`, 27 `[R-PUSH]`), not a CAISO-lane edit — and on §5 there is no reason to make it,
  since the measured value does not close the object.
* **Matrix (rule 28 (b)):** no mechanism was *tested* — this measures an input to one already in the
  keeper — so **no cell verdict moves**. The `gas_commitment_bridge` cell stays **K** and its evidence
  line is extended with §5, §7 and §8.
* **Code added:** `scripts/probes/caiso286_start_cost_coverage.py` only. Nothing under `src/` was
  touched.
* **Artifacts:** `results/calibration/_caiso286_start_cost_coverage.json` (the full gate table,
  response curve, gap census and per-gap sample).
* **Rule 31 `[R-RETAIN]`:** the caiso-285 instrumented bundle was **recovered**, not re-solved, from
  `203124e310f7be4f806ad968d6cf5755f96bbc00` (17 files, 96,114,526 bytes); it is `.gitignore`d and was
  unstaged after checkout, so it **cannot reach `main`**. Nothing was deleted. It sits on this
  session's local disk and will not survive container reclamation; recovery remains one
  `git checkout` from that full SHA, at zero LP cost.

**The promotion question, asked rather than pre-empted (rule 31):** there is **nothing to promote** —
no bundle was solved and no candidate mechanism reached a state where promotion is meaningful. The
decision this session puts to the owner is **not** a promotion but a direction: whether to fund the
§9 successor (one instrumented year-shard to split the 270.3 MW between the decommit screen and
`startup_aware` gap-merging), or to leave the CAISO belly where it stands with the keeper unchanged
and `CALIBRATED`.
