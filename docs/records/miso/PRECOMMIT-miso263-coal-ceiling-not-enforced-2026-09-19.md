# PRECOMMIT — miso-263: the 2022 coal over-run is a DROPPED CONSTRAINT, not a missing one. Re-solve all six years with the ceiling actually enforced

```
SESSION : miso-263        ISO: MISO
KEEPER  : 2026-09-19-miso-262-cold-year (results/calibration/miso262_cold_span),
          span 2020-2025, train tier 2023-2025 CALIBRATED.
OBJECT  : the 2022 coal over-run -- C1 2022 COAL_PRB +32.08 TWh, COAL_BIT
          +10.42, CC_REGULAR -28.20.
PHASE 0 : ZERO LP, from committed bytes + a fleet_only rebuild. ANSWERED, and
          it changes the object: coal_fuel_inventory IS armed, its cap DOES
          bind -- and the keeper's dispatch VIOLATES it. The constraint was
          never built in the containers that solved the keeper.
PLAN    : six per-year shards (rule 36 [R-YEAR-ISOLATION]), the keeper's own
          recipe replayed with the clean partitions present, composed at zero
          LP in the parent.
PROBE   : scripts/probes/_miso263_coal_ceiling_phase0.py (every number below).
```

---

## 0. WHAT I WAS ASKED, AND WHAT I FOUND INSTEAD

The charter's phase 0 was: *"is `coal_fuel_inventory` binding in 2022 at all,
and if so where does it stop biting?"* — on the named hypothesis that the model
has **no binding coal SUPPLY ceiling**.

The mechanism is armed (`run_config_2022.json`: `coal_fuel_inventory = True`),
its cap binds, and **the keeper's coal dispatch is infeasible under it**. The
hypothesis is right about the *state* — 2022 has no binding coal ceiling — and
wrong about the *reason*. The ceiling is not missing from the model. It is
missing from the **solve**.

## 1. THE PROOF, WHICH NEEDS NO CLASS CROSSWALK AND NO LP

The LP row (`model/lp/rows.py`, via `_build_oil_budget_rows`) is one pooled
fleet row per month capping coal energy **input**:

```
sum_{g in coal, t in month m}  HR[g] * P[g,t]  <=  CAP[m]      (MMBtu)
CAP[m] = (opening stock + prior-years delivery rate) * MMBtu/ton / 12
```

subject to `0 <= P[g,t] <= pmax[g] * availability[g,t]`. So the **most coal
ENERGY** any feasible dispatch can deliver in month `m` is the
efficiency-ordered greedy fill of `CAP[m]` against each unit's monthly headroom
— a fractional knapsack, optimal by the exchange argument, and deliberately
**loosened** by aggregating the hourly bounds to a monthly total. Call it
`MAX[m]`. It is an upper bound on **every** feasible dispatch, whatever the
class mix, the offers, the floors or the zonal balance.

`CAP[m]` is not re-derived here: it comes from
`market_sim.data.coal_fuel_inventory.build_coal_fuel_budget` called on the
fleet a `fleet_only` rebuild of the keeper's own recipe produces — the
identical call `scripts/run_calibration.py` makes.

**If the committed sidecar's own P1 coal MWh exceeds `MAX[m]`, no dispatch
satisfying the row produced it.** One-sided: coal *under* the bound proves
nothing, which is why the bound is reported beside the physical ceiling.

### 1.1 2022, month by month (GWh)

| mo | COLD keeper | `MAX` under cap | excess | phys ceiling | WARM keeper | warm vs `MAX` |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 24,536.2 | 20,612.5 | **+3,923.7** | 25,282.2 | 20,417.9 | −194.6 |
| 2 | 21,061.9 | 20,111.8 | **+950.1** | 21,990.5 | 19,953.4 | −158.4 |
| 3 | 18,468.0 | 19,190.6 | −722.6 | 19,190.6 | 18,468.9 | −721.6 |
| 4 | 15,652.8 | 15,957.0 | −304.2 | 15,957.0 | 15,652.8 | −304.1 |
| 5 | 18,798.6 | 19,053.8 | −255.2 | 19,053.8 | 18,798.6 | −255.2 |
| 6 | 26,133.2 | 20,715.7 | **+5,417.5** | 27,291.4 | 20,483.7 | −232.0 |
| 7 | 30,904.3 | 21,224.3 | **+9,680.0** | 31,956.3 | 20,972.3 | −252.0 |
| 8 | 29,881.8 | 21,144.1 | **+8,737.7** | 30,466.9 | 20,904.7 | −239.4 |
| 9 | 24,031.4 | 20,766.4 | **+3,264.9** | 25,363.9 | 20,534.3 | −232.1 |
| 10 | 17,447.1 | 18,157.9 | −710.8 | 18,157.9 | 17,451.9 | −706.0 |
| 11 | 17,243.3 | 18,543.8 | −1,300.6 | 18,543.8 | 17,243.2 | −1,300.6 |
| 12 | 21,559.6 | 20,360.6 | **+1,198.9** | 22,932.2 | 20,154.9 | −205.7 |

**COLD violates its own declared cap in 7/12 months, by +33.17 TWh. WARM
violates it in 0/12** — and in exactly those seven months WARM sits 0.8–1.2 %
under the bound, i.e. hard against the cap with the bound's own slackness as
the gap. That is the signature of a row that binds. miso-259 measured the same
thing from the other side on this run — "seven binding months", implied heat
rate 11.056–11.621 tight around the fleet's dispatch-weighted 11.320.

### 1.2 The whole span, and the pattern that settles the cause

| year | months COLD violates | excess TWh | miso-262's max \|Δ class TWh\| |
|---|---:|---:|---:|
| 2020 | **0/12** | 0.00 | 0.0048 |
| 2021 | 4/12 | +8.83 | 7.1586 |
| 2022 | **7/12** | +33.17 | 24.1796 |
| 2023 | **0/12** | 0.00 | 0.1440 |
| 2024 | **0/12** | 0.00 | 0.0023 |
| 2025 | 3/12 | +4.92 | 4.0034 |

The three years the cold keeper violates its cap are **exactly** the three
miso-262 found diverging from the warm keeper, and the magnitudes track. The
warm keeper violates in 0/12 months of every year.

## 2. THE CAUSE, REPRODUCED RATHER THAN INFERRED

`build_coal_fuel_budget` resolves through `data/clean/coal-stocks` and
`data/clean/coal-receipts`. Those are **derived, gitignored and disposable**;
`scripts/hydrate_data.py` hydrates `data/raw` and does **not** build them.
Absent, `opening_stock_tons` and `prior_years_delivery_rate` both return
`None`, the builder returns `None`, `run_calibration.py` logs

> `coal fuel-inventory budget (MISO 2022): NOT APPLIED — ... The solve is
> byte-identical to an unarmed run`

and the solve proceeds. **This container reproduced that exact state on the
first attempt**: a fresh checkout, `hydrate_data.py --profile miso`, and the
budget came back `None` with the raw CSVs sitting on disk.

The keeper's `meta.composed_from` names six `miso262_mer_*` bundles — one per
year, each solved by `replay_keeper.py` in its own fresh shard container under
the miso-262b per-year instruction. Nothing in the solve path curates the clean
tree.

## 3. WHAT THIS DOES TO THE RECORD (reported, not quietly absorbed)

* **`RESULT-miso262` §3's "year-grouping defect" is a MISDIAGNOSIS.** Its
  position-in-leg story predicts 2024 (leg-middle, warm-started) diverges; 2024
  is the cleanest year in the grid at 0.0023 TWh **and** violates in 0/12
  months. The cap story predicts the observed set exactly. Its own "still
  unexplained either way" residue — 2023 at 0.144 — remains unexplained by
  either, and is two orders of magnitude below the three real ones.
* **miso-262c's promotion argument inverts.** It reads: *"It is the better
  optimum, not merely a different one — the predecessor's 2022 served identical
  demand while running 24 TWh more CC_REGULAR ($54.52/MWh) and 24 TWh less coal
  ($31.93), ~$500 M of objective."* Relaxing a binding constraint **always**
  improves the objective. The $500 M is the shadow value of the dropped fuel
  row, not evidence of a better solve.
* **Rule 36 `[R-YEAR-ISOLATION]` loses its empirical basis but not its
  architectural one.** The measurement cited for it — the 24 TWh divergence —
  was not warm start; the warm-start hypothesis was never tested and is now
  unsupported. Its *architectural* argument (a backcast's years are independent
  by construction; the LP basis was the only cross-year channel) is untouched by
  anything here, and the owner's instruction stands. **I am not reverting it**,
  I am recording that its evidence was something else, and this session solves
  one year per shard exactly as it requires.
* **MISO's CALIBRATED headline rests on an affected year.** 2025 is train tier
  and violates in 3/12 months; 2023 and 2024 do not. The determination is not
  re-opened here — it is re-scored after the repair.

## 4. THE FIX ALREADY LANDED (commit `13aaedd4`)

`coal_fuel_inventory` is now a `PartitionRequirement` in
`market_sim.data.input_completeness`, the guard caiso-157 wrote and caiso-188
wired to both solve paths for precisely this defect class — *"the run advertises
a mechanism in its `run_config`/`meta` that never ran"* — and whose registry
documents itself as **"ADDITIVE by design"**. It was never extended when
miso-259 introduced the mechanism. Severity: the `hydro_ror_split` class, **no
fallback**, fatal in every mode, because an absent partition leaves coal with
floors and no ceiling at all.

No `ScenarioConfig` field, no threshold, no tunable, zero cache-key movement
(rules 21 `[R-DOF]` / 24 `[R-REGISTRY]`): a pure config-vs-disk assertion. A
container in the keeper's state now stops with both curate commands in the
error text instead of silently solving the wrong LP.

## 5. G-DRIFT (rule 29 `[R-SCREEN]` (b)) — ALL HUNKS INERT, SO THE KEEPER IS THE CONTROL

`git diff 4583e70b..HEAD` over `src/market_sim`, `scripts/run_calibration*.py`,
`scripts/lib`, `data/raw/{_validation-source,reference}` is 16 files / 1,558
insertions across seven commits. Classified:

| commit | change | verdict for a MISO backcast |
|---|---|---|
| `cb1e60b7` | warm start + P1 basis seed default OFF | **INERT** — the keeper's own legs ran through `replay_keeper.py`, which already pins both off (`DETERMINISM_ENV`). The flip makes the CLI match what the keeper did. |
| `3b719484` | `PJM_SEAM_LADDER_BY_YEAR` 2020 row | **INERT** — another ISO's table; the recipe carries `pjm_seam_measured_ladder=False`, `miso_seam_measured_ladder=True`. |
| `03eed7e9` | nyiso-240 keeper promotion | **INERT** — another ISO, zero LP. |
| `1b289fcf` | `soco_gas_st_campaign_commitment: bool = False` | **INERT** — default-off, absent from the recipe. |
| `72373757` | `mid_vintage_exit_carry: bool = False` | **INERT** — default-off, absent from the recipe. |
| `9961a6a5` | `measured_coal_heat_rates: bool = False` | **INERT** — default-off, absent from the recipe. *(Noted forward, not acted on: NWPP measured its coal fleet's assigned cap-weighted HR at 11.868 against a metered operating 11.066. MISO's assigned cap-weighted rate is 11.865, the same eGRID annual-average construction. That is a MISO lever for a later session, not this one.)* |
| `eec172c0` | `--persist-p0-dispatch` opt-in sidecar | **INERT** — opt-in, output only. |
| `13aaedd4` | this session's guard | **INERT for a passing solve** — it can only raise. |

**All INERT ⇒ G-DRIFT form 4 holds and the keeper's committed numbers are the
control.** So the movement the re-solve produces is attributable to the restored
coal budget rather than to HEAD drift. *(Classified per commit on each
mechanism's gate and its absence from the recipe, not hunk-by-hunk; that is
stated so a reader can weigh it.)*

## 6. THE PLAN, AND THE DECISION RULE, BOTH BEFORE THE SOLVE

**Six shards, one per year** (rule 36 `[R-YEAR-ISOLATION]` (a); rule 34
`[R-SHARD-PROMOTABLE]` (c) — 2020-2025 is the ISO's whole registered year set,
enumerated before this session's rule-35 prune and recorded in commit
`a3af7ca3`). Each shard:

1. pins the full 40-char SHA of this commit, and stops if `git rev-parse HEAD`
   differs;
2. runs `uv sync --no-dev` and then **`scripts/regenerate_clean.py`**, which
   carries `coal-stocks` and `coal-receipts` (lines 60-69) — the step the
   miso-262b shards omitted;
3. **verifies the budget was built** by requiring the runner's
   `coal fuel-inventory budget (MISO <y>): ... annual ... monthly cap ...`
   INFO line in its log. The new guard already makes the absent case fatal;
   this is the positive confirmation on top of it;
4. replays the keeper's own recipe for its single year —
   `replay_keeper.py results/calibration/miso262_cold_span --years <y>
   --out-dir results/calibration/miso263_coalcap_<y>` — so the config is
   **identical** to the keeper's and the only difference is that the declared
   constraint now exists. Zero `ScenarioConfig` deltas, zero free parameters
   added (rules 1 `[R-STRUCT]` / 21 `[R-DOF]`);
5. pushes its FULL bundle including `dispatch/<y>_P1.parquet` to its own branch
   (rule 34 (a)), by appending a `.gitignore` negation and a plain `git add`.

**The decision rule, stated ex ante.** This is a **repair, not a mechanism
A/B**: there is no arm to promote and no gate to pass, so no criterion is
consulted to choose anything (rule 1 `[R-STRUCT]`). The re-solve restores a
constraint the keeper's own config declares. I will report every movement at
full magnitude — including any that makes a criterion worse, and explicitly
including any change to the CALIBRATED train tier — and the owner rules on
promotion (rule 31 `[R-RETAIN]`). **I expect the repaired run to land near the
warm keeper**, since the cap is what separated them; if it does not, that is a
finding and it gets reported rather than explained away.

**What I am NOT doing.** Not re-opening the seam (miso-262 `G`/`R`/spent), not
touching a coal offer multiplier (rule 1's carve-out condition (b) refuses it —
the price bias flips sign across the span), not reverting rule 36, and not
arming anything new. No mechanism is tested, so no matrix cell verdict moves
(rule 28 `[R-MECH-MATRIX]` (b)); `coal_fuel_inventory` stays **`K`** with this
session's evidence appended.

## 7. WHAT PHASE 0 ALSO SETTLED, IN PASSING

* **The cap is NOT a loose annual budget in the binding years.** Annual headroom
  looks ample (2022: 2,782.2 M MMBtu against ~2,700 burned) but the flat 1/12
  monthly grain is what bites — `MAX` falls *below* the physical ceiling in
  Jan/Feb/Jun–Sep/Dec 2022 and sits *above* it in Mar–May/Oct–Nov. That is the
  monthly-no-carry limitation miso-259 declared at the gate, visible as the
  shape of the constraint rather than as a defect.
* **The physical ceiling, not the fuel row, is what caps the cold run.** Cold
  2022 coal runs at 97.0 % of `sum(pmax * availability)` in January and 96.7 %
  in July. A fleet pinned that hard against its own availability is the
  signature of an unconstrained-fuel optimum in a $6.45 gas year.
* **`build_coal_fuel_budget`'s footprint is larger than the bench proxy**: 86
  plants (1 shared-storage) and 783 coal generators in 2022, against the
  59-plant bench-derived set `_miso259_coal_budget_phase0.py` warns is a proxy.
  The phase-0 table here is scored on the LP's own footprint.
