# PRECOMMIT — neiso-112: the NEISO keeper's marginal emission rate, one shard per year

```
SESSION : neiso-112 (parent = ORCHESTRATOR, rule 32 [R-SHARD] (a): it runs NO LP)
ISO     : NEISO           LANE: marginal-abatement data production
KEEPER  : 2026-09-16-neiso110-dualfuel-derate-scope
          bundle results/calibration/neiso110_dualfuel_span, git_sha c0916408,
          years 2020-2025, determination CALIBRATED (rubric 3.8, 8 scored,
          0 FAIL, lone ledgered C3c). THE KEEPER IS NOT CHANGING.
DELIVER : marginal_emission_rate (tCO2/MWh, the emissions dual) as a per-zone-hour
          column in hourly/system_<year>.parquet, for ALL SIX years, for the
          marginal-abatement page (docs/codebase-site/marginal-abatement.html).
LP      : SIX shards, ONE YEAR EACH, one container each (rule 36
          [R-YEAR-ISOLATION] (a); owner instruction this session: "launch a
          single shard for each year of the solve bc warm start has been proven
          to no longer be neutral and therefore shouldn't be used for backcast").
PIN     : <PINNED_SHA>
```

---

## 1. WHY A RE-SOLVE IS REQUIRED AT ALL

`marginal_emission_rate` landed in `fba0ecd7` ("Emit the marginal emission rate from
every solve"), which is **after** the keeper's `c0916408`. Verified against the
committed bundle: no `system_<year>.parquet` in `neiso110_dualfuel_span/hourly/`
carries the column. It is an **LP dual** — `r_B' B^-1`, the CO2 rate vector in place
of the cost vector at the solve's own optimal basis — so it cannot be reconstructed
from any committed sidecar. A solve is the only route.

NEISO is one of the eight grids the marginal-abatement page still reports as pending
(`docs/codebase-site/js/marginal-abatement.js`: only SOCO carries the underlying
hourly measurement as of 2026-09-19).

## 2. THE RECIPE — THE KEEPER'S OWN, UNCHANGED

Every shard runs, with NOTHING added:

```
python scripts/replay_keeper.py results/calibration/neiso110_dualfuel_span \
  --years <YEAR> \
  --out-dir results/calibration/neiso112_mer_<YEAR> \
  --note "neiso-112: year-isolated MER re-solve of the neiso110 keeper recipe (rule 36)"
```

`replay_keeper.py` reconstructs `solve_and_persist`'s kwargs from the keeper's own
`meta.json`, so the recipe is the keeper's by construction. **No `--set`, no
`--offer-curve-json`, no `--enable-legacy-p2`.** `--years` + `--out-dir` make this a
NEW run rather than the keeper fixed in place (the driver's own `_restore_display_date`
guard), which is correct: the keeper's id and bundle are untouched.

Config signature each shard must self-check before it pushes (from the keeper's
`run_config.json`):

| field | required value |
|---|---|
| `iso` | `NEISO` |
| `passes` | `["P1"]` (`commitment: false` — P2 is archived) |
| `outage_source` | `historic` |
| `neiso_coldsnap_derate_dualfuel_unswitched` | `true` |
| `neiso_winter_fuel_inventory` | `true` |
| `offer_curve_overrides.CC_REGULAR.committed` | `1.212469` |
| `offer_curve_overrides.CT_PEAKER.committed` | `1.288845` |
| `offer_curve_overrides.ST_GAS.committed` | `0.754213` |
| gas price for its year | 2020 `2.03` · 2021 `3.72` · 2022 `6.45` · 2023 `2.54` · 2024 `2.19` · 2025 `3.52` |

A shard that sees otherwise **STOPS and does not push**.

## 3. G-DRIFT — the code-level drift audit (rule 29 [R-SCREEN] (b)), run BEFORE any solve

`git diff c0916408 HEAD -- src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/replay_keeper.py scripts/lib
data/raw/_validation-source data/raw/reference` = 30 files, 19 non-merge commits.
Every changed hunk on the backcast path, classified:

| change | commits | verdict for NEISO backcast | reason |
|---|---|---|---|
| **MER emit** | `fba0ecd7` | **LIVE — and the point of this run** | additive; computed by freezing the cost-optimal basis, swapping the objective to the CO2 rate vector and re-pricing at **zero simplex iterations**, then restoring the basis and the iteration-limit option. No pivot can occur, so the primal, the basis and every dual already extracted are untouched. Solve-invariant by construction. |
| **warm start / P1 basis seed default OFF** | `cb1e60b7` | **INERT on this path** | `replay_keeper.py` has pinned `MARKET_SIM_WARMSTART_XYEAR=0` since long before the flip (`DETERMINISM_ENV`), and `MARKET_SIM_P1_BASIS_SEED` is armed only inside that gate. The flip changes the CLI default, not this driver. |
| 5 new `ScenarioConfig` fields — `measured_coal_heat_rates`, `measured_st_heat_rates`, `soco_gas_st_campaign_commitment`, `coal_prb_proxy_own_iso`, `mid_vintage_exit_carry` | `cc1bcb24` `1b289fcf` `9961a6a5` `666343a2` `72373757` | INERT | all default `False` and all absent from the keeper's recipe. `backcast_config` arms `coal_prb_proxy_own_iso` only for `iso == "NWPP"`. |
| `eia860.py`, `campd_bins.py`, `fleet/arrays.py`, `fleet/assembly.py`, `data/coal.py`, `data/fuel/coal.py` | same | INERT | reachable only under those flags. |
| `pipeline/commitment.py`, `pipeline/year.py`, `runner.py`, `floor_mechanisms.py` (mech 25) | `1b289fcf` | INERT | SOCO-gated (`soco_gas_st_campaign_commitment`). |
| `model/interchange/spec.py` | `3b719484` `9d1322ad` | INERT | new rows in the **PJM** and **MISO/NYISO** seam-ladder tables only. |
| `--persist-p0-commitment` / `--persist-p0-dispatch` | `45192ce0` `eec172c0` | INERT | opt-in, not passed. |
| storage SOC sidecar | `8c8b16e9` | INERT (additive) | write-only sidecar, read after both LPs have run. |
| `replay_keeper` ERCOT receipts-fallback key routing | `b642a803` | INERT | ERCOT top-level key; NEISO's meta does not carry it. |
| `outages.py` `retiree_year`/`mid_vintage_exit_carry` params | `72373757` | INERT | `runner.py` passes `year=` on the pre-existing `_rvs or _ppx` predicate plus the new `_mvx`, which is `False` here — the argument is unchanged for this recipe. |

**Solve surface:** `src/market_sim/config/solve_surface.py`, `solve_surface_declared.py`
and all seven `SURFACE_MODULES` are **byte-identical** between `c0916408` and HEAD, so
the keeper's recorded NEISO fingerprint `9d35c270c69e9eee` (197 rows) still holds.

**Conclusion: all hunks INERT except the MER emit, which is solve-invariant.** Form 4
is valid and the keeper's committed bundle is the control — no control solve is spent.

## 4. THE PRE-REGISTERED EXPECTATION, AND THE ONE THING THAT WILL MOVE

Because §3 finds no live mechanism change, the **only** channel that can move a number
is the one the owner's instruction names: **year grouping**. The keeper solved all six
years in ONE invocation; each shard solves ONE year alone.

Measured in MISO on 2026-09-19 (`docs/RESULT-miso262-mer-control-and-the-year-grouping-defect-2026-09-19.md`),
this is not nothing: a keeper year re-solved standalone reproduced the **first** year of
each invocation leg and diverged in the later ones, up to **24.18 TWh** of class energy
and 43,160 of 70,080 price cells, deterministically, with the 2022 swap moving 24 TWh
off CC_REGULAR at $54.52/MWh median `mc` onto coal at $31.93 — ~$500 M of objective, so
the multi-year solve was **not at the optimum**. That finding is what produced rule 36
`[R-YEAR-ISOLATION]`.

So, stated before the solves:

* **2020 is the control.** It is the keeper invocation's first year, so if the
  year-grouping effect is the whole story, 2020 should reproduce the committed keeper
  to within alternate-optimum noise.
* **2021-2025 may diverge, and divergence is NOT a defect of this run.** Under rule 36
  the year-isolated solve is the CORRECT one; the keeper's later years carry the
  artifact. Any divergence is reported at full magnitude (§6), never absorbed.
* **NEISO's exposure is expected to be smaller than MISO's**, because the mechanism
  MISO measured ran through a large coal/CC marginal swap and NEISO has effectively no
  coal on the margin. That is a prediction, not a claim — it is what the numbers will
  settle.
* No gate, criterion, determination or keeper designation moves in this session.

## 5. THE SHARD PLAN (rules 32 / 33 / 34)

Six shards, launched concurrently, each pinned to the immutable SHA of this commit.

| year | out-dir | branch |
|---|---|---|
| 2020 | `results/calibration/neiso112_mer_2020` | `claude/neiso112-mer-2020` |
| 2021 | `results/calibration/neiso112_mer_2021` | `claude/neiso112-mer-2021` |
| 2022 | `results/calibration/neiso112_mer_2022` | `claude/neiso112-mer-2022` |
| 2023 | `results/calibration/neiso112_mer_2023` | `claude/neiso112-mer-2023` |
| 2024 | `results/calibration/neiso112_mer_2024` | `claude/neiso112-mer-2024` |
| 2025 | `results/calibration/neiso112_mer_2025` | `claude/neiso112-mer-2025` |

`DATA PROFILE: neiso` — each shard hydrates only NEISO's `data/raw` subtree.

**Every shard PUSHES ITS FULL BUNDLE** (rule 34 `[R-SHARD-PROMOTABLE]` (a)), including
`dispatch/<year>_P1.parquet`, by appending a `.gitignore` negation for its own out-dir
and using a **plain `git add`** — never `git add -f`, never `git add -A`. A bundle
stranded on an ephemeral container cannot back a promotion, which is the miso-255
incident this rule closes.

**All six years are solved** (rule 34 (c)): the ISO's registered year set is exactly the
keeper's `[2020…2025]` — `frontend/data/backcast/registry/*.json` carries one NEISO
sidecar and no NEISO run is stamped to the keeper as a folded touchpoint. No year is
deliberately left out.

Budget: **35 minutes** per shard. NEISO is four trading zones plus the HQ import node,
so one year should land well inside that; a shard approaching the budget with no
artifact **STOPS and reports** rather than pushing a half-written bundle (rule 27
`[R-PUSH]`). The runner calls `ensure_solve_container` itself, so no shard carries a
memory recipe of its own and none passes `--no-container-preflight`.

## 6. WHAT EACH SHARD REPORTS, IN NUMBERS

The parent may never read a shard's disk, so the final message carries:

1. the commit SHA it pushed and `git ls-tree -r <sha> -- results/calibration/neiso112_mer_<Y>` file count;
2. MER coverage: rows, null count, load-weighted mean, p10 / median / p90, min / max, and the share of zone-hours at exactly 0.0;
3. the differencing against the committed keeper for its own year — max |Δ class TWh| and the class, price cells moved of 70,080, annual load-weighted price before/after, max |Δ price|;
4. the four config-signature values from §2 as its run actually recorded them;
5. the `container preflight:` and `memory peak:` log lines, and wallclock.

## 7. WHAT THIS SESSION WILL NOT DO

No dashboard registration from a shard, no `build_manifest.py` / `build_status.py` /
`prune_iso_runs.py`, nothing under `frontend/data/backcast/**`, no edit under `src/` or
`scripts/`, no PR, no deletion of any result (rule 31 `[R-RETAIN]`). The parent owns the
seam: composition, reporting, and **the promotion question, asked explicitly before this
session ends** — these bundles live on gitignored parent disk plus their own shard
branches, and this container is ephemeral.

**"A shard that stops with a clear report is a SUCCESS; a shard that repairs
infrastructure is a FAILURE."**
