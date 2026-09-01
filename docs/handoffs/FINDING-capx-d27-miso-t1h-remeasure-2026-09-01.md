# FINDING — capx D27: the S-123 requirement repair bought MISO **14.7 GW of admission headroom exactly as D17 computed — and coal ate all of it**. The missing non-coal exit channel is UNMOVED at 0.000 GW, because admission composition is set by the reliability floor's cheapest-firm-adequacy retention key, not by margin depth

**Lane:** capx D27 — the EXECUTION of D17-R's routed PRIMARY (R1).
**Pre-declaration:** `PREDECL-capx-d27-miso-t1h-remeasure-2026-09-01.md`, pushed at
`67594f08` BEFORE the solve started; graded at full magnitude in §3, misses included.
**Run:** `miso-2021-2025-realized-t1h-d27`, registered to the bare `miso-t1h` key; the prior
FFR-3A-2-vintage record preserved at `miso-t1h-pre-d27`.
**No parameter moved.** No FOM, threshold, execution lag, margin adder or screen parameter was
touched; no mechanism was tested; no `ScenarioConfig` field was added (rule 28 not triggered,
no matrix cell written). D17's standing refusal (rules 21 `[R-DOF]` / 24 `[R-REGISTRY]`) binds
this lane and was honoured — the residual below is ROUTED, not closed.

---

## 0. Verdict (one paragraph)

**D17's ≈14.7 GW headroom arithmetic is VINDICATED AS ARITHMETIC AND REFUTED AS A REMEDY.**
Every requirement-side number lands: the HEAD requirement factor resolves to **1.00715 × peak**
and the pre-S-123 deltas reproduce D17 §4.1's table **to the decimal** (11,157.1 / 11,229.1 /
10,961.3 MW for 2023/2024/2025, plus 3,505.9 MW of external accredited firm), and the admission
cap duly releases — `entry_capped` falls **93,016.7 → 70,790.1 MW in 2023 (−22.2 GW)** and
**105,542.9 → 95,536.4 MW in 2024 (−10.0 GW)**. But **the entire released budget went to coal**:
economic exits rise 11,931.6 → **25,646.6 MW, 100 % coal**, against a 12,434.1 MW coal actual
(**+106.3 %**), while **gas_st, gas_cc, gas_ct and oil all remain at EXACTLY 0.000 GW** — the
object is untouched. `retire.total_gw` moves 12.716 → **26.431 GW**, so the G3 row still FAILs
and its **sign flips** from −27.7 % under- to **+52.2 % over**-retirement, and
`retire.false_retire` flips PASS → FAIL (0.997 → 13.212 GW, 50 % of model). The mechanism,
measured on this run's own enriched `pipeline_events` and then verified on source: **admission
depth only ORDERS the candidate list; the SELECTION is made by `_apply_reliability_floor`, which
un-admits in ASCENDING going-forward-cost-per-firm-MW** (`_floor_retention_merit`). Per-fuel FOM
is gas_ct 21.0 < oil 25.0 < gas_cc 30.0 < gas_st 35.0 < coal 45.0 × 1.3 = **58.5**, so coal is the
last fuel retained and the first released, and the measured capped set is exactly the cheap-FOM
prefix — **~100 % of the ENTIRE gas_ct, gas_st and oil fleets are `entry_capped` in every screen
year**. **This corrects D17 §4.1's expectation that a larger budget "admits by depth order", and
it means no requirement-side repair can ever open the non-coal channel** (§4). Separately, D17's
thread (i-b) is **CONFIRMED on hindcast evidence for the first time** (D17 had only a
forecast-window proxy): the capacity-revenue leg is **$0.00/kW-yr for every fuel in every screen
year**, as is the reserve leg (§5). The over-exit has a real cost: reserve margin falls to 1.7 %
(2024) and **I3 unserved energy FAILs** in 2024 and 2025 while the armed adequacy backstop never
fires (§6). Determination **HOLD, unchanged** — FC-3 FAIL both sides; the repair did not flip
MISO's T1-H verdict, it **relocated the failure**.

---

## 1. The run, and what it is NOT

```
uv run python scripts/run_capacity_hindcast.py \
  --iso MISO --start-year 2021 --end-year 2025 \
  --vintage 2020 --fuel-variant realized \
  --out-dir results/hindcast/miso-2021-2025-realized-t1h-d27
```

Bare invocation at HEAD, every solve-affecting flag omitted — the FFR-3A-3 recipe (§1.3 of that
battery) and the D4-M ERCOT recipe with `--iso` swapped. Solved `[2021, 2023, 2024, 2025]`,
bridged `[2022]`, scored 2023–2025. ~35 min, ~8.2 GB peak RSS (D17 priced ≈25 min / ≈10 GB).
Cache key **`501b5f64b8adf8d4`**, byte-matching the value resolved from committed code BEFORE
the solve (§1.2 of the pre-declaration). `leakage_violations: []`; the solve-year parity
assertion passed.

**Both D17 R1 guards discharged, and both before launch, not after.**
* **(a) fresh solve.** The HEAD key `501b5f64b8adf8d4` is neither FFR-2B's `0a4455fd0d642364`
  nor the legacy arm's `df5c3de1bad16670`, and `run_capacity_hindcast.py` redirects
  `cachemod.CACHE_ROOT = args.out_dir` (line 1841), so an empty fresh out-dir cannot serve a
  stale pre-package bundle at any key. The out-dir was verified absent before launch.
* **(b) current scoring target.** Scored against the CURRENT committed
  `capacity_actuals_miso.csv`. Its 2021–2025 thermal aggregate is **17.369 GW** (coal 12.434 /
  gas_st 2.128 / gas_cc 0.858 / nuclear 0.812 / oil 0.543 / gas_ct 0.399 / biomass 0.196).
  **Both coal signs, per D17 R4:** the BASELINE's 11.932 GW of model coal reads **+9.1 %**
  against the 2026-08-02-era target and **−4.0 %** against this one. Nothing below depends on
  which vintage is right — the non-coal zero is vintage-independent, and this run's own coal is
  +106.3 % on either basis.

### 1.1 THIS IS NOT AN S-123-ISOLATING A/B — declared before the run, restated here

Five MISO-relevant defaults moved after the FFR-3A-3 baseline (2026-08-04):
`miso_rps_compliance_regions` (owner D-26, 2026-08-06) and `miso_clean_tier_rows` (owner D-29,
2026-08-11) — both change the LP's RPS constraint set, hence prices, hence **every screen
margin**; `entry_vre_capacity_revenue`; the two storage-entry gates (owner R-A, 2026-08-31); and
the `hindcast_verified_announced_exits` harness default (2026-08-22). One leg was priced, so no
control arm ran. **No movement in this finding is attributed to S-123 alone**, and none is
claimed to be. What IS attributed, because it is read off committed source rather than off a
delta, is the §4 mechanism.

**One further comparability caveat, disclosed:** the `entry_capped` baseline (93,016.7 /
105,542.9 MW) comes from the **FFR-2B** pipeline arm, whose flags differ from the shipped
defaults. FFR-3A-3 §2.5 established parity with it on **retirement quantities** (total 12.716,
coal 11.932, false 0.997, recall 13/17) — **not** on `entry_capped`, which no committed artifact
reproduces for the FFR-3A-3 leg. The `entry_capped` deltas in §0/§3 therefore carry that
confound. The **direction** is robust (the release is also visible as the 25.6 GW decided cohort,
which has no FFR-2B analogue at any flag setting), the exact GW is not.

---

## 2. What the corrected basis actually bought

The requirement side, computed at HEAD on committed constants
(`resolve_adequacy_requirement_mw`, MISO, this run's own ledger peaks):

| screen year | peak MW | requirement MW | factor | pre-S-123 (1.09952) | Δ | + external firm | total swing |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 120,781 | 121,644.0 | 1.00715 | 132,801.1 | 11,157.1 | 3,505.9 | **14,663.0** |
| 2024 | 121,560 | 122,428.6 | 1.00715 | 133,657.7 | 11,229.1 | 3,505.9 | **14,735.0** |
| 2025 | 118,661 | 119,508.8 | 1.00715 | 130,470.1 | 10,961.3 | 3,505.9 | **14,467.2** |

**D17 §4.1's table is reproduced to the decimal.** The arithmetic was right.

The pipeline events it bought (this run's ledgers; 2022 is the **bridge year — evolved, never
solved, never scored (rule 22)**, shown as mechanism trace only and excluded from every score):

| year | decided | entry_capped | re_confirmed | executed | reversed | reserve_margin |
|---|---:|---:|---:|---:|---:|---:|
| 2021 | — | — | — | — | — | 0.286282 |
| *2022 (bridge)* | *25,646.6 (coal)* | *74,352.5* | — | — | — | — |
| 2023 | — | 70,790.1 | 25,646.6 | — | — | 0.219194 |
| 2024 | — | 95,536.4 | 25,646.6 | 25,646.6 (coal) | — | **0.017280** |
| 2025 | — | — | — | — | — | 0.070449 |

Baseline, for comparison: decided 1,105.3 (2023) + 901.0 (2024); executed 11,931.6 coal (2024);
reversed 2,006.3 (2025); reserve_margin 0.272935 / 0.217566 / 0.119461 / 0.218797.

**The score:**

| row | baseline | D27 re-measure | actual (current target) | band |
|---|---:|---:|---:|---|
| `retire.total_gw` | 12.716 | **26.431** | 17.369 | **FAIL** (+52.2 %, sign flipped) |
| coal | 11.932 | **25.647** | 12.434 | +106.3 % |
| **gas_st** | 0.000 | **0.000** | 2.128 | **−100 %** |
| **gas_cc** | 0.000 | **0.000** | 0.858 | **−100 %** |
| **oil** | 0.000 | **0.000** | 0.543 | **−100 %** |
| **gas_ct** | 0.000 | **0.000** | 0.399 | **−100 %** |
| nuclear | 0.768 | 0.768 | 0.812 | −5.3 % |
| biomass | 0.016 | 0.016 | 0.196 | −91.9 % |
| `false_retire` | 0.997 (7.8 %) PASS | **13.212 (50.0 %)** | — | **FAIL** |
| `unit_recall_gt300` | 13/17 = 0.765 PASS | **15/19 = 0.789** PASS | — | PASS |
| plant-recall (non-gated) | 0.471 | **0.737** | — | — |

**The channel did not open by one megawatt.**

---

## 3. The pre-declaration, graded at full magnitude

### P1 — `entry_capped` direction and magnitude → **DIRECTION HIT, ONE MAGNITUDE MISS**

| year | predicted | measured | grade |
|---|---|---:|---|
| 2023 | DOWN, −8 to −18 GW | **−22.2 GW** | direction HIT, **magnitude MISS** (overshot my band's top by 4.2 GW) |
| 2024 | DOWN, −10 to −20 GW | **−10.0 GW** | **HIT** (at the bottom edge) |

The falsifier (|Δ| < 3 GW in *both* years) did **not** fire, so D17's thread-(iii)
CONFIRMED-PRIMARY stands as a statement about the cap: the corrected basis really did release
the admission budget. I under-estimated 2023 because I sized the release off the 2024 screen's
post-exit position and did not account for the 2022 bridge screen consuming the budget first.

### P2 — "the channel OPENS: non-coal executed strictly positive, 2–8 GW" → **FLAT MISS, REFUTED BY MY OWN FALSIFIER**

Measured: **exactly 0.000 GW**, identical to the baseline, in all four non-coal fossil classes.
The falsifier I wrote — *"non-coal executed stays exactly 0.000 GW"* — **fired**. This is the
central prediction of the lane and it is wrong; §4 is why. The composition sub-prediction
(gas_st over-shoots, the small-unit tail under-produces) is **NOT REACHED** — nothing was
produced to be right or wrong about, and it is not scored either way.

### P3 — `retire.total_gw` → **HIT on all three legs**

| leg | predicted | measured |
|---|---|---|
| model GW | 22–34, central ~28 | **26.431** |
| err_frac vs current target | +25 % to +93 %, central ~+59 % | **+52.2 %** |
| band | FAIL, **sign flipped** to over-retirement | **FAIL, sign flipped** |

The pre-registered ~25 %-likely alternative (lands in the ±10 % band and PASSES) did not occur.
The reasoning that produced this hit is the one that made P2 wrong in the same breath: releasing
~17 GW of accredited headroom into a pool where ~100 GW fails the bar releases ~17 GW of *exits*
— I had the volume right and the composition wrong.

### P4 — verdict rows → **HIT on the determination, ONE MISS on the additions clause**

| prediction | outcome |
|---|---|
| FC-3 stays FAIL | **HIT** |
| FC-7 FAIL → CAVEAT (run_config now written by construction) | **HIT** — `run_config` PASS ("766 config keys"), DOF ledger CAVEAT |
| FC-1, FC-8 stay SKIPPED | **HIT** |
| determination stays HOLD | **HIT** |
| no verdict outside `miso-t1h`'s own rows moves | **HIT** — the ff-verdicts diff is a pure insertion touching exactly `miso-t1h` + `miso-t1h-pre-d27` |
| *"the five addition bands are untouched by a requirement-side repair"* | **MISS** — they moved (below) |

**The additions MISS, at full magnitude.** `add.by_tech.gas_cc` and `add.by_tech.gas_ct` flipped
FAIL → **PASS** (+7.2 % / +8.6 %), `add.shares.wind` flipped FAIL → **PASS**, and
`add.shares.gas_cc` / `add.shares.gas_ct` flipped PASS → **FAIL**. The FC-3 band-FAIL list went
from 8 entries to 9: `['retire.total_gw', 'retire.false_retire', 'add.by_tech.wind',
'add.by_tech.solar', 'add.by_tech.storage', 'add.shares.solar', 'add.shares.gas_cc',
'add.shares.gas_ct', 'add.shares.storage']`. I asserted the additions block was insulated from a
requirement-side repair; it is not — the 25.6 GW exit changes what the entry screen sees, and the
five post-baseline default changes (§1.1) touch entry directly.

**Two movements I did not predict at all**, reported rather than absorbed: `retire.false_retire`
flipped **PASS → FAIL** (0.997 GW / 7.8 % → 13.212 GW / 50.0 %), the direct arithmetic
consequence of +13.7 GW of excess coal; and `unit_recall_gt300` **improved** (13/17 → 15/19, band
PASS both sides) with plant-recall 0.471 → **0.737**, because a bigger coal exit set covers more
real ≥300 MW coal units. One extra FC-7 row (`overlay-off` PASS,
`outage_source='statistical'`) also appeared, which I had not anticipated; it is non-gating.

### P5 — adequacy trace → **HIT, including the exact arithmetic**

| prediction | outcome |
|---|---|
| ledger reproduces factor ≈1.00715 + 3,505.9 MW external firm | **HIT, exact** — §2's table matches D17 §4.1 to the decimal |
| end-of-window `reserve_margin` in 0.02–0.12 | **HIT** — 2025 = **0.070449** (2024 dips to 0.017280) |
| ~40 % chance the backstop fires and/or unserved appears | **unserved: HIT** (I3 FAIL, §6). **Backstop: did NOT fire** — no `backstop`-sourced addition in any year. The minority case was correctly flagged as minority. |

### Scorecard

**P3 and P5 hit cleanly. P1 hit on direction, missed one magnitude band. P4 hit the
determination and missed the additions clause. P2 — the lane's headline prediction — is flatly
refuted by the falsifier I wrote for it.**

---

## 4. WHY the channel stayed shut — the mechanism, and a correction to D17 §4.1

D17 §4.1 recorded, as an honest limit rather than a claim, that *"enlarging the budget admits by
depth order, and hindcast depths are uncommitted"*. **The depths are now committed, and the
premise is wrong: admission is not selected by depth.**

Read on source (`retirements.py`): `candidates.sort(key=lambda item: (-item[1], item[0].unit_id))`
(line 1516) orders the failing candidates worst-first by depth — but that only builds the list.
The **selection** is made by `_apply_reliability_floor` (lines 1286–1370), which *un-admits*
candidates until accredited firm capacity clears the requirement, iterating
`sorted(eligible, key=lambda g: _floor_retention_merit(config, g))`. That key (lines 1263–1283) is
**annual going-forward cost per firm MW, ascending** — "cheapest firm adequacy first", CO2 then
heat rate as tie-breaks. Per-fuel FOM (`_THERMAL_FOM`, × the coal multiplier):

| fuel | FOM $/kW-yr | retention order |
|---|---:|---|
| gas_ct | 21.0 | retained **1st** |
| oil | 25.0 | 2nd |
| gas_cc | 30.0 | 3rd |
| gas_st | 35.0 | 4th |
| **coal** | **45.0 × 1.3 = 58.5** | retained **LAST** |

**Retained = kept online = `entry_capped`. So coal is the last fuel retained and therefore the
first — and, until the requirement clears, the only — fuel released.** The measured capped set is
exactly that cheap-FOM prefix:

| year | coal capped / fleet | gas_cc | gas_ct | gas_st | oil |
|---|---|---|---|---|---|
| 2022 (bridge) | 5,284.8 / 55,564.5 = 9.5 % | 84.0 % | **100.0 %** | **100.0 %** | **100.0 %** |
| 2023 | 9.5 % | 81.1 % | 98.5 % | **100.0 %** | 9.3 % |
| 2024 | 29,917.9 / 55,564.5 = 53.8 % | 70.8 % | **100.0 %** | **100.0 %** | **100.0 %** |

**~100 % of the entire gas_ct, gas_st and oil fleets are refused admission in every screen year**,
while coal is the only fuel that is ever partially released. The depth medians confirm the
selection is not depth-ordered: at the 2022 screen the *decided* coal has a **shallower**
weighted-median depth (17.05 $/kW-yr) than the *capped* coal (24.87), the capped gas_st (35.0) or
the capped oil (25.0). The deepest-failing units were refused; shallower coal was admitted.

**The consequence, which is the lane's real result:** the non-coal exit channel **cannot be
opened by any requirement-side repair**. Enlarging the admission budget only walks further down a
monotone ordering whose entire tail is coal; non-coal is reached only if the requirement goes
slack enough that the floor retains *nothing*, which cannot happen while ~100 GW of a 142.6 GW
fleet fails the bar. D17 attributed the zero to requirement rationing and expected the repair to
un-starve the channel; the repair un-starved the **budget**, and the **ordering** kept the channel
shut.

---

## 5. D17 thread (i-b) CONFIRMED on hindcast evidence — the capacity leg is $0 everywhere

D17 §4.2 had to carry its bar decomposition from the **forecast** window, explicitly flagged
("never quoted as the hindcast number"). This run commits the hindcast-window numbers. Capacity-
weighted $/kW-yr over the 2024 screen's event rows:

| fuel (2024) | net revenue | bar | energy leg | reserve leg | **capacity leg** | attribute |
|---|---:|---:|---:|---:|---:|---:|
| coal (capped) | 17.06 | 58.50 | 17.06 | 0.00 | **0.00** | 0.00 |
| coal (executed) | 9.30 | 58.50 | 9.30 | 0.00 | **0.00** | 0.00 |
| gas_cc | 20.79 | 30.00 | 20.79 | 0.00 | **0.00** | 0.00 |
| gas_ct | 1.22 | 21.00 | 1.22 | 0.00 | **0.00** | 0.00 |
| gas_st | 1.06 | 35.00 | 1.06 | 0.00 | **0.00** | 0.00 |
| oil | **0.00** | 25.00 | 0.00 | 0.00 | **0.00** | 0.00 |

**Confirmed at hindcast grain: the modelled capacity-revenue leg pays $0.00/kW-yr to every unit
of every fuel in every screen year** — the documented ONE-POSITION LIMIT firing exactly as D17
predicted — and so does the reserve leg, so net revenue **is** the energy leg. MISO's real PRA
cleared ≈$3.4/kW-yr (PY 2023-24) and ≈$7.3/kW-yr (PY 2024-25) in the same years. **gas_st and oil
— the two largest real non-coal exit categories (2.128 and 0.543 GW) — earn ≈$0 and $0.00
respectively, because they essentially never run.** gas_cc is the one non-coal class anywhere near
its bar (20.79 vs 30.00).

**Answering the exit brief's D28 question directly.** The bar's under-reward is **binding on
VOLUME but not on COMPOSITION**, and the two residuals are now separable:

* **(a) the bar fails ~100 GW of a 142.6 GW thermal fleet** (capacity leg $0, reserve leg $0,
  energy-only net revenue). This is what forces the floor to bind hard every year.
* **(b) the floor's retention key is monotone in cost-per-firm-MW**, so whatever the floor
  releases is coal-first-from-the-expensive-end (§4).

**(b) is the proximate cause of the missing non-coal channel** — it would hold even if the bar
were perfectly calibrated, *as long as the floor binds*. But (a) is **upstream and could dissolve
(b)**: a capacity leg that paid MISO's actual PRA prices would lift far fewer units below the bar,
the floor might not bind at all, and then whatever fails would simply exit — non-coal included.
So the honest answer is that **the D28 cause is not "now the binding residual" in place of D17's;
it is the one that makes D17's mechanism bind**, and it is the only one of the two whose repair
has published-data identification available (D17 R2).

---

## 6. The cost of the over-exit (reported, not celebrated)

The 25.6 GW coal exit is not a free improvement in "exit volume". Invariants on the registered
bundle: **I3 unserved/dump FAILS** — 2024: 29 h, 133.2 GWh, peak 15,224 MW; 2025: 57 h,
143.2 GWh, peak 7,340 MW (both 0.02 % of load). Reserve margin falls to **1.7 %** (2024) and
**7.0 %** (2025). **I12 WARNs** (2021 28.6 %, 2023 21.9 %, band [0.7 %, 15.7 %]). I1, I2, I4–I11,
I13, I14 all PASS — including **I7 "held"**. The armed adequacy backstop
(`reserve_margin_build_enabled=None` ⇒ ON for a capacity-market ISO) **never fires**: exactly the
endogenous signature S-123-V measured in the 2029/2030 forecast years.

**Board note (scoring convention, deliberate):** the registered verdict is scored on the canonical
T1-H command (`--hindcast-score` + `--run-config`, no `--invariants`), the same command
`rescore_forecast_verdicts.py` uses for every other T1-H board record, so FC-1 reads **SKIPPED**
and MISO stays comparable with its peers. The I1–I14 block above is nevertheless now **committed
in the sidecar**, so a future lane can score FC-1 without a re-solve — it would read **FAIL** on
I3. That is reported-only here and gates nothing.

---

## 7. What remains of the object, and what is routed

**The object is unchanged in magnitude and better understood in cause.** MISO's economic screen
still produces **0.000 GW** of the 3.93 GW of real non-coal fossil exits (3.458 GW on the era
basis). What this lane closes is D17's R1 and its thread-(iii) *expectation*: the requirement
basis WAS starving the cap, the repair IS shipped and effective, and it moves **coal only**.

1. **R1 — CLOSED.** The HEAD re-measure is solved, scored and registered; the hindcast per-fuel
   depths, bar decompositions and event rows D17 had to bound around are committed.
2. **R2 — capacity-revenue realism at long positions: PROMOTED to the primary lever**, on §5's
   hindcast-grain confirmation (previously forecast-proxy only). It is the only one of the two
   residuals with published-data identification (the in-repo PRA seasonal clearing record + the
   published RBDC/CONE tables). Still explicitly NOT admissible: any flat adder or floor tuned to
   the retirement residual (D17 K7).
3. **R5 — NEW, this lane's own: the floor-retention key's exit-composition monopoly.**
   `_floor_retention_merit` buys adequacy cheapest-first, which is defensible as *procurement* but
   makes the model's realized exit composition a pure function of per-fuel FOM ranking whenever
   the floor binds. Whether a real ISO's retirement composition is FOM-rank-ordered in this way is
   a **structural question with an external observable** (the actual 2021–2025 cohort is 3 large
   gas steamers plus a 158-unit small tail — emphatically not FOM-rank-ordered). Routed as a
   mechanism question, **not** built here and **not** parameterised: rule 21 forbids closing this
   with a tuned retention weight.
4. **R3 / R4 — unchanged**, still routed as D17 left them.
5. **Tracked-set addition, flagged for the director:** this bundle's `evolution_*.json` are
   un-ignored by a rule scoped to **this one bundle** (`.gitignore`, the NEISO-RC-R R4 precedent),
   because they are the sole evidence for §4. The T1-H slim-set convention is unchanged for every
   other run; generalise or prune as the director prefers.

## 8. Governance

Rule 12 (years sequential in one invocation) honoured. Rule 22: solve years `{2021, 2023, 2024,
2025}`, 2022 bridged and never scored, scoring bounded to 2023–2025, holdout freeze active and
neither spent nor worked around, no marker touched, nothing scored against measured H1-2026.
Rule 27: `register_forecast_run.py` (792 → 804 lines) was edited in place with a targeted edit and
pushed as the exact on-disk bytes, blob-verified after push. Rule 28 not triggered — no mechanism
tested, no `ScenarioConfig` field added, no matrix cell written; MISO's lever queue was checked
and this lane adds no lever. No keeper, shard, marker or backcast surface was written. The
ff-verdicts edit is a **pure insertion** touching exactly two keys, and the board edit touches
MISO's `t1h_provenance` / `t1h_retire_g3` plus one new top-level block — **no gate leg, no
determination and no other ISO's rows moved**, so no cross-lane re-grade was triggered and
nothing needed routing on that account. Collision check at start and at push: only D29
(`run_full_horizon.py`) in flight; no overlap.
