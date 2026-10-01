# RESULT — miso-263: MISO's coal ceiling was DECLARED IN EVERY RUN CONFIG AND NEVER ENFORCED. Repaired, all six years, and the "year-grouping defect" is falsified

```
SESSION : miso-263        ISO: MISO        PARENT LP: ZERO (rule 32 [R-SHARD] (a)).
KEEPER  : 2026-09-19-miso-262-cold-year (results/calibration/miso262_cold_span) — UNCHANGED.
NEW RUN : 2026-09-19-miso-263-coal-ceiling (results/calibration/miso263_coalcap_span),
          2020-2025, registered. NOT promoted — the promotion question is §7.
OBJECT  : the 2022 coal over-run (C1 2022 COAL_PRB +32.08 / COAL_BIT +10.42 /
          CC_REGULAR -28.20 TWh).
ANSWER  : the ceiling is not missing from the MODEL. It was missing from the SOLVE.
LP      : 9 shard-years (6 first wave, 3 re-run after a second defect).
```

---

## 1. THE FINDING, PROVED FROM COMMITTED BYTES

`coal_fuel_inventory: true` appears in all six of the keeper's per-year
`run_config`s. Its LP row caps coal energy **input** per month:

```
sum_{g in coal, t in m} HR[g]*P[g,t] <= (opening stock + delivery rate)*MMBtu/ton / 12
```

So the most coal **energy** any feasible dispatch can deliver in month `m` is
the efficiency-ordered greedy fill of that budget against each unit's
`pmax*availability` — a bound that holds for every feasible dispatch whatever
the class mix, offers or floors, and deliberately loosened by aggregating the
hourly bounds to a monthly total. The keeper's own committed `class_hourly`
**exceeds that bound**:

| year | months the keeper violates its own cap | excess | miso-262's "divergence" |
|---|---:|---:|---:|
| 2020 | 0/12 | — | 0.0048 |
| 2021 | 4/12 | +8.83 TWh | 7.1586 |
| 2022 | **7/12** | **+33.17 TWh** | 24.1796 |
| 2023 | 0/12 | — | 0.1440 |
| 2024 | 0/12 | — | 0.0023 |
| 2025 | 3/12 | +4.92 TWh | 4.0034 |

The superseded WARM keeper violates it in **0/12 months of every year**, sitting
0.8–1.2 % under the bound in exactly the months the cold run sails past — the
signature of a row that binds.

**Cause, reproduced rather than inferred.** `build_coal_fuel_budget` resolves
through the derived, gitignored partitions `data/clean/{coal-stocks,
coal-receipts}`, which `hydrate_data.py` does not build. Absent, it returns
`None`, appends zero rows, logs a warning, and the solve proceeds. This session's
own container hit that state on the first attempt. The keeper's
`meta.composed_from` names six `miso262_mer_*` bundles solved in fresh shard
containers that hydrated `data/raw` and never ran `regenerate_clean.py`.

## 2. THE REPAIR, AND WHAT IT MEASURES

Six shards, one year each (rule 36 `[R-YEAR-ISOLATION]`), replaying the keeper's
**own recipe** with the partitions present. Zero `ScenarioConfig` deltas, zero
free parameters, 43 DOF entries carried and **0 added**.

| year | cap violations | coal TWh (was) | **max \|Δ class TWh\| vs the WARM keeper** |
|---|---:|---:|---:|
| 2020 | 0/12 | 188.84 (188.84) | 0.000016 |
| 2021 | 0/12 | 241.71 (251.74) | 0.000016 |
| 2022 | 0/12 | **231.04 (265.72)** | 0.000016 |
| 2023 | 0/12 | 180.42 (180.60) | **0.000000** |
| 2024 | 0/12 | 167.52 (167.52) | **0.000000** |
| 2025 | 0/12 | 196.19 (201.79) | **0.000000** |

Every year landed at or just under the ceiling **registered before any shard
reported** (`ADDENDUM-miso263-the-prediction…`, commit `891f892c`), by 0.00–1.51
TWh — the bound's own slackness.

**RESULT-miso262 §3's year-grouping / warm-start diagnosis is FALSIFIED.** A
**cold, year-isolated** solve now reproduces the **warm, span-grouped** keeper
essentially exactly, so the warm-start channel it hypothesised (and never
tested) measures as **null**. All six of its divergences are accounted for by
whether the coal cap binds — including 2023's 0.144 TWh, which it recorded as
"still unexplained either way": that is the cap binding lightly in July and
August. Its position-in-leg story predicted 2024 (leg-middle, warm-started)
would diverge; 2024 is the cleanest year in the grid *and* violates 0/12.

**miso-262c's promotion argument inverts.** It read the cold run's ~$500 M
objective improvement as "the better optimum". Relaxing a binding constraint
always improves the objective; that figure is the shadow value of the dropped
fuel row.

**Rule 36 keeps its architectural basis, loses its evidence.** Its argument —
a backcast's years are independent, the LP basis was the only cross-year
channel — is untouched by anything here, and the owner's instruction stands.
This session solved one year per shard exactly as it requires. What changed is
that the 24 TWh it was justified by was something else. **Not reverted.**

## 3. THE SECOND DEFECT, FOUND MID-FLIGHT

`replay_keeper.py` builds its recipe from the bundle's **span-wide `meta.json`**
and has no per-year dimension. MISO's keeper is two configs partitioned at 2023
by data (`miso_measured_reserve_requirements` / `miso_reserve_online_gated`
False for 2020–2022, **True** for 2023–2025, because
`load_miso_reserve_requirements` hard-errors before 2023), and the composite's
meta carries the 2020 leg's values. So the first-wave 2024 and 2025 legs solved
on the **validation leg's reserve configuration**.

Measured across all six years, the exposure is exactly those two fields:
`gas_price_override` and `weather_year` are unaffected (`bundle_gas_price` falls
back to the per-year Henry Hub actual and reproduces every recorded value).
Those two bundles were **discarded and re-solved** with `--set` restoring the
keeper's own declared per-year values; 2020/2021/2022 were unaffected. The
composer's `check_recipes` partition guard would have aborted rather than
produce a mixed-config span — the guard worked.

**Credit:** the first-wave 2025 shard flagged the confound itself. It was right,
and narrower than the truth. Its claim was verified against the artifacts rather
than accepted on report. Full record:
`ADDENDUM-miso263-replay-keeper-has-no-per-year-dimension-2026-09-19.md`.

## 4. THE FIX THAT PREVENTS RECURRENCE

`coal_fuel_inventory` is now a `PartitionRequirement` in
`market_sim.data.input_completeness` — the guard caiso-157 wrote and caiso-188
wired to both solve paths for precisely this defect class (*"the run advertises
a mechanism in its `run_config`/`meta` that never ran"*), and whose registry
documents itself as **"ADDITIVE by design"**. It was never extended when
miso-259 introduced the mechanism. Severity: the `hydro_ror_split` class, **no
fallback**, fatal in every mode. No `ScenarioConfig` field, no threshold, no
tunable, zero cache-key movement. Verified end-to-end: a container in the
keeper's state now stops with both curate commands in the error text.

## 5. GATES, AS SCORED

| gate | verdict |
|---|---|
| `calibration_verdict` **train tier 2023-2025** | **CALIBRATED** — zero failing criteria, C3c the lone ledgered caveat |
| `calibration_verdict` full span | **NOT-YET** — validation rungs only (§6) |
| `check_registry_payload_parity` | **as charted** — `caiso279_ablate_dswcouple_span` (pre-existing, not MISO's) + this lane's 6 gitignored per-year dirs, each verified via `git check-ignore`; the composed span is tracked. The local FILESYSTEM-sweep RED rule 31 documents; CI stays green |
| `audit_keepers --iso MISO` | **E13 RED — EXPECTED AND UNRESOLVED BY DESIGN.** Two registered runs, one not the keeper: that *is* the open promotion decision. Clearing it either way is the owner's call (§7). E3 warning pre-existing |
| `build_status --iso MISO --check` | **PASS** (in sync) |
| `check_cache_key_registration --base origin/main` | **PASS** — no new field, zero key movement |
| `check_gate_a_provenance --iso MISO` | **PASS** |
| `check_bench_freshness --iso MISO` | **PASS** — 6 parts, 0 STALE |
| `_miso260_bench_parity` | **max \|Δ actual class TWh\| = 0.000000** — see §5.1 |
| `pytest tests/scoring` | 22 failed / 1547 passed vs a 21-failure baseline measured in this container. The one new failure is `test_the_live_keepers_are_on_pin`, and it is **SOCO's** keeper off-pin on highspy/pandas/pyarrow/pydantic, introduced on main by `7022723a`. This session's commits touch only `.gitignore`, `docs/`, MISO's registry/runs and the MISO bundle. Not MISO's (rule 25) |
| `node --check` | n/a at commit time; run on the matrix shard edit |

### 5.1 THE BENCH MOVES AT HEAD, AND THIS RUN WAS DELIBERATELY NOT SCORED ON IT

Rebuilding the benchmark at HEAD moves the **actual** side by up to **2.651 TWh**
(an `oil` → `OTHER_FOSSIL` reclassification across years). Traced to `e63f730a`
(spp-49, benchmark-membership repair), which changes
`scripts/run_calibration_full.py` — where `--rebuild-benchmark` lives. That is
HEAD drift from another lane.

Scoring a promotion candidate against a moved actual side is the **miso-257
defect**: a moving actual reads exactly like a model result. So the bench parts
were restored to `origin/main` and this run is scored against the **same bench
the incumbent was scored against**; parity then reads 0.000000. Against the
committed bench the numbers reproduce the superseded warm keeper's published
figures exactly (−10.29 / −9.47 / +16.3 % / −14.6 % / 0.299).

**The bench move is real and is ROUTED, not absorbed.** It belongs to whoever
owns spp-49, and any MISO lane that rebuilds the benchmark will meet it.

## 6. THE SCORED COMPARISON, AT FULL MAGNITUDE

Both runs, same scorer, same bench, same session:

| | incumbent `miso-262-cold-year` | **this run** |
|---|---|---|
| coal cap actually enforced | **no** (7/12, 4/12, 3/12 months violated) | **yes** (0/12 every year) |
| failing criteria | 4 | **3** |
| failing C1 cells | 5 | **2** |
| C1 2020 COAL_BIT | −10.30 | −10.29 |
| C1 2021 CC_REGULAR | −9.62 **FAIL** | **PASS** |
| C1 2022 CC_REGULAR | −28.20 | **−9.47** |
| C1 2022 COAL_PRB | +32.08 **FAIL** | **PASS** |
| C1 2022 COAL_BIT | +10.42 **FAIL** | **PASS** |
| C3a 2022 | −23.3 % | **−14.6 %** |
| C3b 2021 / 2022 | 0.305 / 0.287 **FAIL** | 0.299 / **PASS** |
| C4 dispatch correlation | **FAIL** (2022 gas r 0.838) | **PASS** |
| train tier 2023-2025 | CALIBRATED | **CALIBRATED** |
| DOF entries added | 0 | **0** |

**Reported against this run:** it is NOT a clean sweep. C1 2020 COAL_BIT stays
out of band at −10.29 TWh, C3a 2020 stays at +16.3 %, C3b 2021 stays at 0.299,
and the full span still reads **NOT-YET** on those validation rungs (rule 30(c):
they never gate). The 2020 object miso-262 routed to the price residual is
untouched by this session and remains open. Nothing here closes it.

## 7. THE PROMOTION QUESTION (rule 31 `[R-RETAIN]`)

**I recommend promoting `2026-09-19-miso-263-coal-ceiling`.**

The owner's standard was *"if structural integrity improves but gates regress
that may still be a keeper."* This run does not require that allowance — **it
improves both.** The incumbent's dispatch is infeasible against a constraint its
own configuration declares, in 14 month-years; this one is not. Structure is
strictly better and every gate is equal or better.

**Stated against the recommendation, so the decision is informed:**

* This run's numbers are the **superseded warm keeper's** numbers. Promoting it
  restores, with the constraint genuinely enforced and years properly isolated,
  the position miso-262c moved away from.
* It is scored on the committed bench while the bench **moves at HEAD** (§5.1).
  A later MISO re-solve will meet that move.
* `audit_keepers` **E13 is RED until this is decided** either way.

**Retrievability (rule 34 (e)):** the registered composite is committed. Every
per-year leg is on its own branch at a full SHA, recorded in `.gitignore`; a
promotion costs **zero re-solves**. Nothing was deleted (rule 31). All nine
shard sessions are archived; the two superseded first-wave branches could not be
deleted (HTTP 403 — rule 33(f)(5)) and are left, said plainly rather than
reported as cleaned.

**If declined:** prune `2026-09-19-miso-263-coal-ceiling` to clear E13, and the
finding in §1 still stands — the designated keeper would then knowingly carry a
declared-but-unenforced constraint, which §4's guard prevents recurring but does
not retroactively fix.
