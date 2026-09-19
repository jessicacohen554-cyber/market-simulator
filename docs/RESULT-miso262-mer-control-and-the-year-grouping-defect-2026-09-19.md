# RESULT — miso-262: the marginal-carbon control is in hand for all six MISO years, and it uncovered a REPLAY DEFECT — a keeper year does not reproduce when solved standalone

```
SESSION : miso-262        ISO: MISO        LP: SIX per-year control replays (owner
          instruction 2026-09-19: "launch one shard per year then compile").
KEEPER  : 2026-09-16-miso-260-seam-ladder (results/calibration/miso260_seam_span),
          UNCHANGED. Nothing registered, no dashboard id minted, no re-registration.
DELIVERED: marginal_emission_rate (the emissions dual, main 2ec09663) for all six
          years 2020-2025, every bundle pushed to its own shard branch in full.
FINDING : the replay reproduces the keeper EXACTLY in the FIRST year of each of the
          keeper's two solve legs and DIVERGES in the later years -- up to 24.18 TWh.
          The injected min_gen FLOORS differ, so it is a different LP, not solver
          noise. G-DRIFT form 4 is therefore NOT confirmed for MISO, and the span
          was deliberately NOT composed.
```

---

## 1. THE MARGINAL-CARBON DATA — COMPLETE, ALL SIX YEARS

`marginal_emission_rate` is a per-zone-hour tCO2/MWh column in
`hourly/system_<year>.parquet`: 70,080 zone-hours per year, **zero nulls** in every
year.

| year | load-weighted mean | p10 | median | p90 | min | max | exactly 0.0 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2020 | **0.6176** | −0.0000 | 0.4675 | 0.9908 | −0.8016 | 1.3432 | 22.88 % |
| 2021 | **0.6011** | −0.0000 | 0.5130 | 1.0182 | −1.1330 | 1.5298 | 13.12 % |
| 2022 | **0.4789** | −0.0000 | 0.3988 | 0.9808 | −1.0692 | 1.5173 | 19.70 % |
| 2023 | **0.5407** | −0.0000 | 0.5001 | 0.9925 | −1.1457 | 1.3850 | 21.89 % |
| 2024 | **0.5271** | −0.0000 | 0.4882 | 0.9441 | −0.8552 | 1.2457 | 20.56 % |
| 2025 | **0.5560** | −0.0000 | 0.5464 | 0.9703 | −1.3265 | 1.4103 | 18.18 % |

The shape is what a coal-margin ISO should produce: a p90 near 1.0 tCO2/MWh (coal on
the margin), ~13-23 % of zone-hours at exactly zero (a non-emitting unit or an import
band marginal), and a real negative limb to −1.33 (a marginal MWh of load that absorbs
otherwise-curtailed VRE or reshuffles the seam LOWERS system CO2). 2022 carries the
lowest mean, consistent with that year's $6.45 gas pushing gas up the stack.

**These bundles also carry two artifacts no MISO keeper has**, because a shard pushes
its full bundle under rule 34 `[R-SHARD-PROMOTABLE]` (a) while a keeper gitignores
them: `hourly/network_<y>.parquet` and `hourly/unit_hourly_<y>.parquet`. That
unblocks the per-seam MODEL flow this session's own FINDING had to record as
unreachable, and miso-261's per-unit `mc` quantiles.

## 2. RETRIEVABILITY — EVERY BUNDLE, WITH ITS FULL SHA (rule 34 (e))

For the marginal-abatement page. All seven are pushed, verified by
`git ls-tree -r <sha> -- <path>` returning **17 files** each, checked out and read on
the parent container.

| year | bundle path | branch | **full recovery SHA** |
|---|---|---|---|
| 2020 | `results/calibration/miso262_mer_2020` | `claude/miso262-mer-2020` | `232631ac446026b64de4dccb16272b2556ebc7a9` |
| 2021 | `results/calibration/miso262_mer_2021` | `claude/miso262-mer-2021` | `857511d3dab9d096702033aa75a7d9f24f245a1e` |
| 2021 *(independent duplicate)* | `results/calibration/miso262_mer_2021` | `claude/miso262-mer-2021-retry` | `4481abcd08bdf5e1becfef0e29c103a3cdf8e5c6` |
| 2022 | `results/calibration/miso262_mer_2022` | `claude/miso262-mer-2022` | `ad015dd4b3f6fff02ef5f4723c9aabe136792bd2` |
| 2023 | `results/calibration/miso262_mer_2023` | `claude/miso262-mer-2023` | `bb46e5ffdaeb6e27d8999f152d7b4e07130264b2` |
| 2024 | `results/calibration/miso262_mer_2024` | `claude/miso262-mer-2024` | `a19fffd19e0adb084d8e13c771b7d9aaa81aca27` |
| 2025 | `results/calibration/miso262_mer_2025` | `claude/miso262-mer-2025` | `7ee73d88d45a6984b67b2e5da9c757a375cbb513` |

Recover any of them with
`git checkout <sha> -- results/calibration/miso262_mer_<year>`. **A promotion from
this state costs ZERO re-solves.** The bundles are also on the parent's disk,
gitignored rather than committed — rule 32 `[R-SHARD]` (d) keeps per-year dirs out of
`main` and rule 31 `[R-RETAIN]` forbids deleting them; the `.gitignore` entry carries
the recovery line. **The shard branches are NOT deleted** (rule 33 `[R-SHARD-ARCHIVE]`
(f)(3)): they hold bundles a promotion would register and the owner has not ruled.

## 3. THE DEFECT — A KEEPER YEAR DOES NOT REPRODUCE WHEN SOLVED STANDALONE

*(§3.2 carries a CORRECTION to this session's first diagnosis: the D-2 floor rows
are an outcome of the divergence, not its cause. The measurements in §3 and §3.1
are unaffected.)*

Each replay differenced against the committed keeper's own `class_hourly` and
`system` sidecars, on P1, at the same pinned HEAD `4583e70b`:

| leg position | year | **max \|Δ class TWh\|** | worst class | price cells moved |
|---|---|---:|---|---:|
| **V leg, first** | 2020 | **0.0048** | CC_CHP | 2,722 / 70,080 |
| V leg, middle | 2021 | **7.1586** | COAL_PRB | 24,403 / 70,080 |
| V leg, last | 2022 | **24.1796** | COAL_PRB | 43,160 / 70,080 |
| **T leg, first** | 2023 | **0.1440** | COAL_PRB | 10,161 / 70,080 |
| T leg, middle | 2024 | **0.0023** | ST_GAS | 1,991 / 70,080 |
| T leg, last | 2025 | **4.0034** | COAL_PRB | 19,886 / 70,080 |

2022 in full: COAL_PRB **+24.18**, COAL_BIT **+9.87**, CC_REGULAR **−19.08**,
CT_PEAKER −4.15, imports **−6.92 TWh**; max Δprice $29.57, load-weighted price
$59.05 → $53.70.

**The first year of each leg reproduces; later years do not.** The keeper is solved as
two invocations — `--years 2020 2021 2022` and `--years 2023 2024 2025`, the data-forced
partition — while each replay solves ONE year. The pattern tracks position in the
invocation, not the calendar.

### 3.1 It is NOT solver noise, and NOT the config

Ruled out by measurement, each on its own evidence:

* **Determinism.** Two INDEPENDENT 2021 shards, different containers, same pinned SHA,
  produced **byte-identical** `system_2021.parquet` and the identical 7.1586 TWh
  divergence with the identical 24,403 moved price cells. The replay is reproducible;
  the difference from the keeper is systematic.
* **Config.** `scenario_config` differs in 4 fields, all accounted for: two
  `None → False` defaults added since the keeper's `36ac2560`, and two STALE STAMPS
  (below). `resolved_inputs` differ only in the same year-keyed stamp. Demand is
  identical to the MWh. `highspy` 1.14.0 throughout.
* **Gas price.** The keeper's `run_config_2022.json` reads `gas_price_override: 2.03`,
  which looks like the cause and is not: **2024 is the control.** Its stamp reads 2.54
  while the replay used 2024's own 2.19, and 2024 still reproduces to 0.0023 TWh — so
  the stamps are stale and both sides used per-year gas. The replay's own unit `mc`
  confirms it (2022 CC_REGULAR median $54.52, an expensive-gas world).

### 3.2 CORRECTED — the D-2 floor rows are an OUTCOME, not the cause

From the committed `legitimacy_diagnostics.json` D-2 mechanism attribution, keeper
against replay, forced TWh:

| year | mechanism | keeper | replay |
|---|---|---:|---:|
| **2020** | every row | — | **identical to ~1e-4** |
| 2021 | `CT_PEAKER ct_netload_drag` | 6.9513 | 7.3138 |
| 2021 | `ST_GAS st_gas_mustrun_per_plant` | 4.7955 | 5.0623 |
| 2021 | `CC_CHP chp_steam` | 5.1348 | 5.4572 |
| 2022 | `CT_PEAKER ct_netload_drag` | 5.0067 | **6.6063** |
| 2022 | `ST_GAS st_gas_mustrun_per_plant` | 4.3727 | 5.0457 |
| 2022 | `CC_CHP chp_steam` | 5.3601 | 5.9436 |
| 2022 | `COAL reliability_floor` | 0.8280 | 0.4241 |

**CORRECTION, made before this doc was acted on.** An earlier revision of this section
read *"the min_gen floors the LP is built with are not the same, so it is a different
LP."* **That inference does not hold and is withdrawn.** D-2's `forced_twh` is the
energy sitting AT a binding floor — an OUTCOME of the dispatch, not the floor level fed
into it — and the same rows' `class_total_twh` moves in the same direction (CT_PEAKER
18.509 → 15.2715). `apply_ct_netload_drag_floor(fleet_arrays, generators, net_load_mw,
config, ...)` takes **net load**, a pure data quantity (demand − wind − solar), so the
floor LEVEL cannot differ between two solves of the same year on the same config. The
D-2 table above is a symptom, correctly measured and wrongly attributed.

**What IS established, and it is still decisive:** the two runs are not two optima of
one LP. The swap is 24 TWh from CC_REGULAR (replay median `mc` $54.52/MWh) onto coal
(median $31.93/MWh) — of order $500 M of objective. Two optimal solutions to the same
LP cannot differ by that; so either the two runs solve genuinely different problems, or
one of them is not at the optimum.

**The live hypothesis, with the experiment that settles it.** The one deliberate
solve-path difference is that `replay_keeper.py` pins `MARKET_SIM_WARMSTART_XYEAR=0`
(its `DETERMINISM_ENV`), while the keeper's legs ran through the calibration CLI, which
defaults it ON — and per `pipeline/solve.py` the **same-year P1 basis seed**
(`MARKET_SIM_P1_BASIS_SEED`) is *"armed only inside the cross-year gate"*, so the pin
disarms that too. Both are documented as basis-neutral (*"objective and total generation
identical"*). **If that claim is false in the presence of MISO's P1-native floor
bridges — where P1 builds a SECOND `DispatchModel` on the floored fleet and seeds it
`alien=True` — then a warm-started later year can land somewhere a cold solve does not,
and the first year of each leg, which has no prior basis, would agree. That is exactly
the observed pattern.**

**THE DECISIVE TEST IS ONE SHARD, ~40 minutes:** re-solve the V leg `--years 2020 2021
2022` exactly as the keeper did but with cross-year warm-start OFF. If its 2022 then
reproduces the REPLAY, warm-start/basis-seed is the cause and "basis-neutral" is false
for MISO. If it reproduces the KEEPER, the cause is year-grouping through some other
in-process state and the warm-start hypothesis dies. Not run here.

**Still unexplained either way:** the T leg's shape. 2023 (leg-first) is 0.144 rather
than ~0, and 2024 (leg-middle, warm-started) is the *cleanest* year in the whole grid at
0.0023. A pure warm-start story predicts the opposite ordering, so whatever the
successor finds must account for that too.

### 3.3 What this costs, stated plainly

* **G-DRIFT form 4 is NOT confirmed for MISO.** Rule 29 `[R-SCREEN]` (b) lets a lane
  use the incumbent keeper's committed numbers as its control instead of spending a
  control solve. That is valid only against an arm solved with the SAME year grouping.
  A single-year arm differenced against this keeper would attribute up to 24 TWh of
  year-grouping artifact to its mechanism. **Any MISO lane running a per-year arm must
  difference it against a per-year CONTROL, and the six bundles in §2 are that control**
  — which is the one unambiguously good thing to come out of this.
* **THE SPAN WAS NOT COMPOSED.** `_miso260_compose_span.py` would have produced a
  six-year composite whose 2021/2022/2025 rows are not the keeper's, and scoring it
  would have read as a model regression. Composition is a zero-LP file operation and
  remains available the moment the defect is understood.
* **The keeper's own scored numbers are not reproducible standalone.** That does not
  make them wrong — the keeper solved the years the way the runner solves a span — but
  it means "replay the keeper" is not currently a way to verify it.

### 3.4 Two provenance defects in the committed keeper, found on the way

1. **The per-year `run_config_<y>.json` files are stale copies of each leg's FIRST
   year.** 2020/21/22 all read `gas_price_override 2.03` / `weather_year 2020`;
   2023/24/25 all read 2.54 / 2023. `_miso260_compose_span.py`'s own docstring asserts
   the opposite — *"The per-year `run_config_<y>.json` files carry the truth"* — and
   that sentence is false as committed.
2. **The composite's `meta.json` carries `gas_prices` for only `{2020, 2021, 2022}`** —
   the V leg's, never merged with T's.

Neither changes what was solved (§3.1 proves the solves used per-year gas). Both make
the bundle's provenance record unreliable for exactly the question this session asked.

## 4. SHARDS (rules 32 / 33)

Nine shard sessions, all Opus 5, all pinned to `4583e70b864a7d5c99a206b06eddf3c36af495bf`.

| shard | outcome | archived |
|---|---|---|
| control V (2020-2022), control T (2023-2025) | interrupted ~9 min in, superseded by the owner's per-year instruction; nothing solved, nothing lost | yes |
| 2020, 2022, 2024 | solved and pushed first pass | yes |
| 2021, 2023 (originals) | went idle mid-task; **both did eventually push** | yes |
| 2021, 2023, 2025 (retries) | solved and pushed; 2021-retry reproduced the original byte-identically | yes |
| 2025 (first attempt) | **KILLED by disk exhaustion** at an 18.36 GiB swap budget, no MER produced | yes |

**The 2025 disk kill is a finding about the emissions dual, reported not absorbed.** A
MISO per-plant year needs ~16.4-18.9 GiB RSS+swap against a ~13.34 GiB nested-cgroup
ceiling, so the runner's swapfile provisioning is load-bearing and it is bounded by FREE
DISK. The retry cleared it after reclaiming regenerable caches only. Two further
environment notes from the shards, both costing sibling time: containers ship **without
numpy/highspy** (`uv sync --no-dev` must run first), and platform drift fc-v33 → fc-v37
was flagged — the latter is NOT the §3 cause, since 2020 and 2024 reproduce to ~1e-3 on
the same platform.

Cross-session messaging could not reach the idle shards from the parent
(`ListAgents` sees no CCR remote peers), which is why the stalled 2021/2023 were
replaced rather than nudged.

## 5. THE PROMOTION QUESTION (rule 31 `[R-RETAIN]`)

**Nothing here should be promoted, and nothing is being proposed for promotion.** A
replay that reproduces its keeper is not a new run, and three of these do not reproduce
it. The six bundles are a **control set and a marginal-carbon dataset**, not a keeper
candidate. They are fully retrievable at the SHAs in §2 at zero cost, on branches that
stay until the owner rules.

**What needs a decision:** whether the §3 year-grouping defect is chased now (it makes
every MISO per-year A/B mis-attributable) or the lane proceeds with per-year controls.

## 6. RULES

* Rule 34 `[R-SHARD-PROMOTABLE]` (a)/(d)/(e) — every shard pushed its full bundle
  including `dispatch/<y>_P1.parquet`; `git ls-tree` verified >0 files before any
  archive; every path and SHA is named here.
* Rule 33 `[R-SHARD-ARCHIVE]` (a)/(f)(3) — fetch, checkout, verify, THEN archive; the
  branches are kept because they carry bundles a promotion would register.
* Rule 31 `[R-RETAIN]` — nothing deleted; the parent's copies are gitignored, not
  removed, and the promotion question is asked here rather than pre-empted.
* Rule 32 `[R-SHARD]` (a)/(d) — the parent ran ZERO LP; composition, scoring and the
  seam are the parent's and the composite was deliberately not built.
* Rule 1 `[R-STRUCT]` / 21 `[R-DOF]` — no mechanism armed, no parameter tuned, zero
  free parameters added. The replays are the keeper's own recipe.
* Rule 15 `[R-DASHBOARD]` — nothing registered: no dashboard id minted, the keeper
  bundle untouched, no re-registration.
