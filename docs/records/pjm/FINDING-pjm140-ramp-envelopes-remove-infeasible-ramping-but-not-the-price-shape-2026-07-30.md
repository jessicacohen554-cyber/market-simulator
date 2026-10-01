# FINDING — pjm-140: **the measured ramp envelope is a real physics correction and a near-null price lever.** Arming it removes **85–91 % of the physically infeasible hourly ramping** in the keeper's own dispatch — **0.54 / 0.59 / 0.54 TWh/yr** the real PJM fleet's own measured maxima say those machines could not have delivered that fast — while moving the DJF h04→h07 morning-ramp price by **+$0.07 / +$0.05 / +$0.03 /MWh** against a chartered target of **+$11.35 / +$17.08 / +$28.94**. Every rubric criterion is unchanged, C1 stays **16/16 free 12/12**, the C3c tail count is **identical at 3 / 10 / 32 h**, and slack and dump are **zero**. The pjm-139 pre-check was not wrong about the model out-ramping the real fleet; it was measuring the wrong quantile. It compared the model's **p99** 1-h move against the fleet's **p99** (1.4–1.7×), but the derive writes each plant's **MAX** — and the model's own p99 sits at **0.28×** that max. So the rows can only bind in the extreme tail, and they do: **0.32–0.46 %** of group-transitions.

**Two arms solved, all three years each, arms sequential (rule 12), years sequential
within each (rule 16).** Control `pjm140_control_A` reproduces the committed keeper
**BYTE-IDENTICALLY** — `0.000000000` MW over **166,440** class-hours in every one of
2023/2024/2025 — so the single delta is provably isolated.
Registered: `2026-07-30-pjm-140-control` and `2026-07-30-pjm-140-rampenv`.
Machine output: `results/probes/pjm140_rampenv_ab.json`,
`results/probes/pjm140_ramp_coverage.json`, `results/probes/pjm140_env_binding_<year>.csv`.
Probes: `scripts/probes/_pjm140_ramp_coverage.py`, `scripts/probes/_pjm140_rampenv_ab.py`.

Chartered by `FINDING-pjm139-winter-morning-ramp-is-a-ramp-rate-deficit-2026-07-30.md`
§5 and gated by `PREREG-pjm140-ramp-envelopes-2026-07-30.md`, committed **before**
either arm solved. **The PREREG is not revised** — where it was refuted, the
refutation is recorded as such (the pjm-137 precedent).

---

## §0 — the verdict in one table

| gate | question | result | verdict |
|---|---|---|---|
| **STEP 1 coverage** | does the derive cover PJM? | `derive_campd_ramp_envelopes.py --iso PJM` run for the FIRST time (rule 23, the pjm-137 pattern): **209 rows**, **145** well-observed plant-family groups, 61 sparse rows the loader never reads, 3 `class_fraction` rows. Loader puts a **live envelope on 194 of 323** (plant, family) groups = **124.1 GW = 90.1 %** of ramp-eligible thermal capacity | **K7 PASS** |
| **STEP 2 memory** | does it fit? | one-year probe peaked **15.3 GB** RSS with ~3.1 GB swap; arm B (3 yr) peaked **15.55 GB** vs arm A's **15.18 GB**. The rows add **1,699,246** LP rows (each two-sided) and **~23.3 M** nonzeros | **fits, on swap** |
| **K5 control identity** | is the A/B valid? | `0.000000000` MW over 166,440 class-hours, all three years | **PASS** |
| **K6 primary direction** | does the DJF h04→h07 model rise INCREASE? | **+3.933 → +4.004**, **+4.554 → +4.600**, **+6.512 → +6.546**. UP in all three years — but **0.5 / 0.2 / 0.1 %** of the gap to PJM's own +$15.28/+$21.63/+$35.45 | **PASS on direction, REFUTED on magnitude** |
| **K1 inert** | < 0.1 % class energy in EVERY class? | worst class **+0.262 / −0.184 / −0.219 %** (`COAL_PRB` / `VIRTUAL_INC` / `ST_GAS`), so the literal test is **not** met — but every **material** class moves < 0.06 % (`CC_REGULAR` +0.053/+0.032/+0.009, `COAL_BIT` −0.019/+0.012, `CT_PEAKER` −0.158/−0.055) | **does not fire; near-inert** |
| **K2 C1** | 16/16, free 12/12? | **16/16, free 12/12** in BOTH arms; pinned `CC_CHP`/`ST_CHP` excluded as always | **PASS** |
| **K3 C3c both bounds** | tail hours in range? | model tail **3 / 10 / 32 h** in **BOTH** arms — **identical**. The keeper's thinnest margin was **not touched**, in either direction | **PASS** |
| **K4 slack/dump** | zero? | **0 / 0** MWh, both arms, all three years. The envelope is not infeasibly tight | **PASS** |
| **D-ENV (new)** | does the bound actually do anything? | arm A crosses its own envelope in **0.393 / 0.463 / 0.319 %** of 1,699,246 group-transitions, carrying **555,882 / 587,079 / 536,940 MWh** of infeasible ramping; arm B cuts that to **51,161 / 64,048 / 82,425 MWh** — a **90.8 / 89.1 / 84.6 %** reduction | **the mechanism WORKS** |
| **determination** | | **CALIBRATED** in both arms; C1 · C2 · C3a · C3b · C3c · C4 · C6 · C7 · C8 all **PASS** | **no kill fires** |

---

## §1 — STEP 1: the artifact, and its coverage disclosed before any verdict

`scripts/data/derive_campd_ramp_envelopes.py --iso PJM --years 2023 2024 2025`
→ `data/raw/_processed-legacy/campd_ramp_envelopes_PJM.csv`. **No derive logic
changed**: this is the existing frozen derive run for a new ISO for the first
time, exactly as pjm-137 ran `derive_campd_ct_heat_rates.py --iso PJM`. It is
**not** a re-derivation against a residual (rule 23 `[R-FROZEN-DERIVE]`).

### §1.1 — artifact rows

| bucket | `plant` (enveloped) | `sparse` (< 4,000 online h) | `class_fraction` |
|---|---|---|---|
| CC | **73** | 5 | 1 |
| CT | **35** | 50 | 1 |
| ST | **37** | 6 | 1 |

145 well-observed groups carrying **121,443 MW** of observed gross pmax; the 61
sparse rows (17,740 MW) are informational — **the loader never reads them**. The
class fallback fractions (up / down, of pmax): **CC 0.4435 / 0.5801**,
**CT 0.7606 / 0.7535**, **ST 0.3152 / 0.4365**. The loader applies **CC and ST
only** — a CT without a measured trace gets **no row at all**, because bang-bang
is the measured norm for the class.

### §1.2 — what the loader actually builds (2024; 2023/2025 differ only in pmax)

| resolution path | groups | capacity | pruned | live |
|---|---|---|---|---|
| measured MW row (rebased gross→net) | 144 | 115,268 MW | 6 | **138** |
| CC/ST `class_fraction` × group pmax | 56 | 9,513 MW | 0 | **56** |
| **no row** (CT, no measured trace) | 123 | 12,932 MW | — | 0 |
| **total ramp-eligible** | **323** | **137,713 MW** | **6 (664 MW)** | **194** |

**K7: live envelope on 194 groups = 124,117 MW = 90.1 % of ramp-eligible thermal
capacity** (56.7 % of all generator capacity). Pruning is negligible — 6 groups,
664 MW, 2 CC and 4 CT — so this is a fleet-level representation, not a sliver.
Live up-envelope as a fraction of group pmax: min 0.18 / p25 0.32 / **median
0.40** / p75 0.53 / max 1.10; down-envelope median 0.53.

**Gross→net rebasis** (the ercot-132 leg A repair) is applied on **142 measured
per-plant EIA-923-net / CAMPD-gross factors** — min 0.8252, median 0.9700, max
0.9968 — with **2** groups falling to the cited class default (0.9750). The
`class_fraction` rows need no conversion (gross-over-gross ratio × net pmax).

The probe calls the **production loader** `build_ramp_groups` and cross-checks
group-for-group: **194 groups / 1,330–1,336 member columns, MATCH** in all three
years.

## §2 — STEP 2: the memory cost, measured before the three-year arm

PREREG §7.1 required a one-year solve first. Measured on a 15 GB box with 8 GB
swap:

| | peak RSS | swap at peak |
|---|---|---|
| one-year probe (2024, `ramp_limits=True`, THROWAWAY, deleted) | **15.32 GB** | ~3.1 GB |
| arm A, three years, no ramp rows | **15.18 GB** | ~0.1 GB |
| arm B, three years, ramp rows | **15.55 GB** | ~0.8 GB |

The rows cost **~0.4 GB of peak RSS** and push the solve further onto swap. It
fits, and every year completed — but **arming this in the keeper makes swap a
requirement, not a cushion, for a PJM per-plant solve on a 15 GB box.** That is
a real operational cost and it is disclosed, not buried.

## §3 — the A/B result, in the PREREG's own terms

### §3.1 — K6, the primary, and the pre-registered ceiling

The committed W5 statistic (`_pjm139_winter_ramp.py --bundle <arm>`), which arm A
reproduces to the FINDING's published figures **exactly** (+3.93 / +4.55 / +6.51):

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| measured MEC DJF h04→h07 rise | **+15.28** | **+21.63** | **+35.45** |
| arm A (keeper) | +3.933 | +4.554 | +6.512 |
| **arm B (ramp envelope)** | **+4.004** | **+4.600** | **+6.546** |
| **delta** | **+0.071** | **+0.046** | **+0.034** |
| model as % of measured | 25.7 → **26.2 %** | 21.1 → **21.3 %** | 18.4 → **18.5 %** |
| share of the remaining gap closed | **0.6 %** | **0.2 %** | **0.1 %** |

DJF whole-day trough-to-peak: **5.23 → 5.27**, **6.22 → 6.24**, **8.34 → 8.36**,
against measured 16.56 / 23.24 / 40.33.

**K6 passes on its literal test — the primary moves UP in all three years — and
is REFUTED on magnitude.** PREREG §2 pre-registered the claimable target as
2024–25 only, bounded by **+$5.55 / +$13.44 /MWh** load-weighted in DJF h06–h07.
This delivers **+$0.05 / +$0.03**. Recorded as a refutation of the expectation,
not as a success: **the winter morning ramp is not closed and its root cause
remains open.**

### §3.2 — K1, and why "inert" is the wrong word but "near-inert" is right

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| worst class, % of its own energy | `COAL_PRB` **+0.262** | `VIRTUAL_INC` **−0.184** | `ST_GAS` **−0.219** |
| `CC_REGULAR` | +0.053 | +0.032 | +0.009 |
| `COAL_BIT` | −0.019 | (−0.000) | +0.012 |
| `CT_PEAKER` | −0.158 | −0.055 | — |
| ISO total, TWh | 787.890 → 787.892 | 816.738 → 816.740 | 847.806 → 847.811 |
| Σ\|Δ\| across classes, TWh | 0.357 | 0.214 | 0.129 |

The PREREG's literal K1 (**every** class under 0.1 %) is **not** met, so K1 does
not fire and the cell is not `I` on the PREREG's own definition. But no material
class moves as much as 0.06 %, and the ISO total moves by **2–5 GWh out of
~820 TWh**. The honest description is **near-inert on dispatch and on price**.

Note the **direction** of what little moves: `CC_REGULAR` **up** and `CT_PEAKER`
**down** in 2023–24 — the *opposite* of PREREG §4's secondary expectation 1,
which predicted `CT_PEAKER` volume would rise as capped steam ceded the morning
ramp. Also recorded as a refutation.

### §3.3 — K3, the standing kill, and it is untouched

C3c is the keeper's thinnest margin (PREREG §6 K3, watched in **both**
directions). Model tail-hour counts are **3 / 10 / 32 h in BOTH arms** —
identical — so the delta neither rescued nor endangered it. `C8 CT_PEAKER` forced
share is **16.3 / 16.9 / 17.1 %** in both arms, all **GROUNDED** (every binding
mechanism clears D-4; profile r 0.923–0.973, off-peak CV ratio 0.705–1.084) — as
PREREG §4 secondary 4 predicted, a ramp row adds no D-2 mechanism id and forced
energy is unchanged.

D-1 and D-2 read `FAIL` in **both** arms — and identically in the **committed
keeper's own** `legitimacy_report.md`. These are pre-existing keeper diagnostic
states that the rule-20 materiality filter and the C7/C8 grounding logic resolve
to PASS; **the delta changes neither.**

## §4 — D-ENV: the measurement that actually settles it

The PREREG could not pre-specify this because it needs the arms' own per-unit
dispatch. For every live ramp group, the share of the 8,759 hour transitions in
which the arm's **own** summed dispatch moves by more than that group's envelope:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| **arm A** crossings, of 1,699,246 group-transitions | **6,681 (0.393 %)** | **7,862 (0.463 %)** | **5,426 (0.319 %)** |
| arm A groups ever crossing, of 194 | 149 | 167 | 147 |
| **arm A infeasible ramping** | **555,882 MWh** | **587,079 MWh** | **536,940 MWh** |
| **arm B** crossings | 2,004 (0.118 %) | 2,232 (0.131 %) | 2,461 (0.145 %) |
| **arm B infeasible ramping** | **51,161 MWh** | **64,048 MWh** | **82,425 MWh** |
| **reduction** | **−90.8 %** | **−89.1 %** | **−84.6 %** |

**This is the structural result, and it is not small.** The keeper's dispatch
performs **0.54–0.59 TWh a year** of hourly ramping that the real PJM fleet's own
measured maxima say those machines could not deliver. Arming the envelope removes
**85–91 %** of it.

Arm B's residual is **by design, not leakage**: `_build_ramp_rows` widens the
bound at availability edges by exactly the capacity discontinuity the model
itself imposes (`RU_eff = RU + max(0, cap[t] − cap[t−1])`), because an outage
onset forces `dP = −P[t−1]` regardless of any envelope and a return restores
capacity in one hour. That guard is the **only** slack in the row, so every
remaining crossing sits at a capacity discontinuity.

### §4.1 — and this is where the pjm-139 pre-check went wrong

W7 measured the model's **p99** 1-h up-move against the real fleet's **p99** as a
fraction of each side's own fleet peak, got **CC 1.42/1.72/1.53, CT
1.38/1.70/1.52, ST 1.61/1.62/1.50**, and concluded that aggregate excess
**"PROVES per-plant rows would bind."** The measurement is sound; the inference
does not follow, because **the envelope is not the fleet's p99 — it is each
plant's MAX**, pooled over 26,280 hours. Measured on arm A's own dispatch:

| ratio, median over the 194 live groups | 2023 | 2024 | 2025 |
|---|---|---|---|
| model **p99** 1-h up ÷ **envelope** | **0.281** | **0.293** | **0.289** |
| model **max** 1-h up ÷ **envelope** | 1.415 | 1.478 | 1.361 |
| (p90 of the max ratio) | 2.533 | 2.825 | 2.548 |

The typical group's 99th-percentile hourly move is **under 30 % of its own
measured maximum**. A model p99 can therefore sit 1.5× above the *actual* p99 and
remain far below the bound — which is precisely what happens. Binding lives in
the top fraction of a percent of transitions, and the price consequence of
reshaping 0.4 % of transitions is the +$0.03–0.07 measured in §3.1.

**This generalises, and it is the transferable lesson: a MAX-based envelope
cannot be pre-checked with a p99-based excess statistic.** The ERCOT note on this
same matrix row said it first, from the other side — "the real fleet violates the
envelope 0–10 times a year" (ERCOT-127 §1). PJM now measures the same property on
its own fleet.

## §5 — the disposition, and the rule that governs it

Under **rule 1 `[R-STRUCT]`** and **rule 14 `[R-ACCURATE]`** this delta goes in
on accuracy, not on fit, and the fit result does not change that:

* With `ramp_limits=False` the LP asserts that **every thermal plant can move
  from any output to any other output in one hour.** That is false as physics, and
  §4 shows the model **acts on it** — 0.54–0.59 TWh/yr of moves no PJM machine
  ever made.
* The replacement carries **zero fitted degrees of freedom**. The DOF ledger goes
  **17 → 18 entries with `n_residual` UNCHANGED at 6**. No magic number is
  introduced (rule 5), the flag is a declared `ScenarioConfig` field recorded in
  `run_config.json` (rule 24), the artifact is PJM's own from PJM's own plants
  (rule 25), and no other keeper mechanism owns intertemporal thermal coupling
  (rule 19 — `commitment_enabled` / `pjm_commitment_posture` False,
  `committed_ramp_spread` 0.0, the three P1-native bridges ISO-exclusive to
  CAISO/ERCOT/NYISO, `measured_ramp_capability` governing reserve **eligibility**
  not energy ramping).
* **PREREG §5's no-feedback ceiling was honoured absolutely**: no multiplier,
  scale, haircut, blend, floor, cap, widening, tightening, per-plant override or
  quantile swap was applied to the derived envelopes, and none may be. The only
  knob touched was the flag's on/off state.
* **Nothing regresses.** Every criterion PASSES in both arms, C1 is 16/16 free
  12/12, C3c is identical at 3/10/32 h, C8 is unchanged and grounded, and slack
  and dump are zero.

**The cost, stated plainly:** 1,699,246 LP rows, ~23.3 M nonzeros, ~0.4 GB extra
peak RSS, and swap becomes a requirement rather than a cushion for a PJM
per-plant solve on a 15 GB box.

**Recommended to the owner as a keeper on structural grounds** — it improves
physical fidelity measurably (§4) while regressing nothing (§3.3) — with the
honest scope leading, not trailing: **it does not close the winter morning ramp,
and that defect's root cause is still unidentified.**

## §6 — DO-NOT-REDO (binding on successors)

- **Do not re-test `ramp_envelopes` on PJM.** The cell is adjudicated on PJM's own
  artifact and its own dispatch: near-inert on price (+$0.03–0.07 on the chartered
  statistic), materially real on physics (−85–91 % infeasible ramping). There is
  no second version of this lever to try, because **PREREG §5 forbids tuning the
  envelope** — no quantile swap to p95, no tightening, no scaling. A successor
  who wants a *binding* ramp representation needs a **different mechanism with its
  own charter**, not a re-parameterised envelope.
- **Do not pre-check a MAX-based envelope with a p99-based excess statistic**, in
  any ISO. §4.1: the model's p99 1-h move is **0.28×** its own measured max, so a
  p99-vs-p99 excess of 1.4–1.7× is fully consistent with binding in **0.3–0.5 %**
  of transitions. Pre-check a bound against **the bound**.
- **Do not quote the pjm-139 W7 pre-check as proof that ramp rows bind.** It
  proved the model out-ramps the real fleet at the p99 — which is true, and is a
  different claim.
- **The winter morning ramp defect is still OPEN and `ramp_envelopes` is now
  spent.** The reachable residual is unchanged: DJF h06–h07 load-weighted
  **−$0.37 / +$5.55 / +$13.44** after the two closed lanes (pjm-137 basis,
  pjm-138 reserve). 2023 remains fully explained; 2024–25 are not. The next
  instrument in the queue is `FINDING-pjm139` §8 lead 2 — the overnight
  bottom-of-distribution miss and the marginal-**tranche** question at h01–h04,
  whose instrument is the committed `--with-fleet` W6 census, **now runnable**
  because `data/clean/` is complete.
- **`ramp_limits=True` requires swap on a 15 GB box** for a PJM per-plant solve
  (§2). A successor re-solving the keeper with it armed must re-assert
  `swapon /swapfile` before every arm.
- Carried forward unchanged and still binding **in full**: `FINDING-pjm139` §6
  (including the `gas_daily_shape` PJM-`K` closure and the all-ISO day-scale
  resolution bound), `FINDING-pjm138` §6, `FINDING-pjm137` §5,
  `FINDING-pjm136` §5, `FINDING-pjm135` §7, `FINDING-pjm134` §5/§8.

## §7 — record corrections and matrix duties discharged this session

- `docs/codebase-site/data/mechanism-matrix.js` — `ramp_envelopes` PJM cell
  **`U` → `K`** (armed in the recommended keeper, adjudicated on PJM's own
  evidence), the note extended with the coverage, the A/B result, the D-ENV
  measurement and the p99-vs-max scope bound. The `P` evidence key is **extended,
  not replaced** (rule 28 duty b). ERCOT's `R` and CAISO's `I` are untouched
  (rule 25).
- `docs/mechanism-testing-matrix.md` §5.3 item 11 — closed with the result and
  the p99-vs-max lesson, rather than deleted, so the inference error is not
  re-made.
- A **probe defect found and fixed in-session**, disclosed because it changed a
  reported number: the first D-ENV pass mapped the dispatch parquet's `klass`
  through `_RAMP_BUCKET_BY_GROUP` directly, which silently dropped **every coal
  group** — the fleet's `plant_group` is the single `COAL` while `klass` splits
  into `COAL_BIT`/`COAL_PRB`/`COAL_WC` — losing 42 of 194 live groups and
  **38.6 GW (31 %)** of live capacity, i.e. exactly the class the defect
  implicates. Fixed by collapsing the coal variants before mapping; the probe now
  reports its own match rate (**194/194**, full 124.1 GW) so the denominator can
  never be silent again. All §4 figures are post-fix.
