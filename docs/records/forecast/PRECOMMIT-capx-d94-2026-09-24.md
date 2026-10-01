# PRECOMMIT — capx D94: `neiso-t3`'s FC-6 driver battery, re-measured on the post-D77 basis

**Lane:** capx **D94** · **Date:** 2026-09-24 · **Model:** Opus (rule 27 `[R-PUSH]`) · **Data profile:** `neiso`
**Branch:** `claude/capx-d94-fc6-driver-battery`, fast-forwarded to `origin/main` **`3affcd71`**
**Authority:** OWNER RULING **Q67** (2026-09-24, capx ledger §0bj / §3): *"Charter D94 now."*
**Binding charter:** `docs/handoffs/capx-director-prompt-pack-2026-08.md` "D94"
**Predecessors read:** `FINDING-capx-d92-2026-09-10.md` (§1.5, §4, §5, §6, §11) ·
`PRECOMMIT-capx-d92-2026-09-10.md` + ADDENDA A/B · `scripts/run_driver_battery.py` ·
`scripts/forecast_verdict.py` (`--driver-battery`, `score_fc6`)

**PUSHED BEFORE ANY LP.** The recipe, the G-DRIFT audit, every prediction and the registration
decision rule are fixed at this commit. The shards are pinned to this commit's full SHA.

---

## 0. THE SCOPE IN ONE PARAGRAPH

`neiso-t3` is the only bare T3 verdict. Its FC-6 carries two inputs: the **paired** block (re-based
onto post-D77 arms by D92) and the **driver battery** —
`results/ff-t3-neiso-golden/bau-d46/fc6/driver-battery-neiso-2026-09-03.json`, the T1.6 ladder
(RPS/ACP vs VRE supply, rungs `vre_short` / `vre_long`, 2026–2050), solved 2026-09-03 on the
**pre-D77** basis and carried byte-identical by D92 (its PRECOMMIT §1.5). This lane re-solves those two
rungs, re-assembles the battery, and swaps **only** `--driver-battery` in the `neiso-t3` re-score.
Nothing else in the record moves.

---

## 1. THE RECIPE — AND WHY IT IS NOT THE BATTERY SCRIPT'S RECIPE

### 1.1 What the committed battery actually solved (read from the code, not assumed)

`run_driver_battery.evaluate_rung` builds every rung as

```python
ScenarioConfig(iso=spec.iso, use_campd_bins=False, start_year=..., end_year=..., **overrides)
```

— **dataclass defaults, legacy equal-width bins, and NEITHER `neiso-t3` pin**
(`ccs_retrofit_vom_adder` at its default 2.95, `ccs_retrofit_fixed_cost_co2_scaling` at its default
True). So the 2026-09-03 battery described a **third** model: neither the verdict's golden recipe nor
a control. That is why its `vre_short` rung reads **246.39 Mt** cumulative CO2 while the same-date
golden base arm (`bau-d46` paired base) reads **284.42 Mt** under an identical `entry_rate_limits=True`.

`run_driver_battery.py --paired-arm` is not the fix either: it builds from
`reference_config(..., golden_posture=True)` **unpinned** (D92 PRECOMMIT §3) and has no T1.6 mode.

### 1.2 The D94 recipe — the proven D92 command, plus the rung override

Each rung is solved by the **same invocation D92 used for its four legs**, with the rung's own
`entry_rate_limits` value passed explicitly:

```
MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
PYTHONPATH=.:src python3 scripts/run_full_horizon.py \
  --iso NEISO --start-year 2026 --end-year 2050 --golden-posture --full-solve-authorized \
  --no-ccs-retrofit-fixed-cost-co2-scaling --set ccs_retrofit_vom_adder=8.0 \
  {--entry-rate-limits | --no-entry-rate-limits} \
  --out-dir results/ff-t3-neiso-golden/d94/{vre_short | vre_long}
```

| rung | T1.6 registry override (verbatim from `build_ladders`) | CLI | 
|---|---|---|
| `vre_short` | `{"entry_rate_limits": True}` | `--entry-rate-limits` |
| `vre_long` | `{"entry_rate_limits": False}` | `--no-entry-rate-limits` |

**HOW THE TWO PINS ARE PASSED, exactly:** `ccs_retrofit_fixed_cost_co2_scaling=False` through the
runner's own `--no-ccs-retrofit-fixed-cost-co2-scaling` (a `reference_config` argument, so it is
applied *before* ISO-default resolution, exactly as D92's legs did); `ccs_retrofit_vom_adder=8.0`
through the generic `--set` (recorded verbatim in `run_config.json` `set_overrides`, as D92's legs
record it). The shard **verifies both off its solved `run_config.json`** before it reports — the
helper's `metrics` subcommand REFUSES (exit 2) on any pin, rung-override, mode or ISO mismatch.

### 1.3 The metrics and the assembly — the instrument's own code, not a re-implementation

`docs/handoffs/d94/battery_golden_rung.py` (a measurement record, like D92's `docs/handoffs/d92/`
helpers — **no file under `scripts/` or `src/` is edited**):

* **`metrics`** (in the shard, zero LP, after the solve) — calls the battery instrument's own
  `run_driver_battery._extract_metrics` over the rung's cache (same reads, same rounding, same
  `rps_final / get_rps_acp("NEISO")` ratio) and writes the rung row in the exact shape
  `evaluate_rung` emits.
* **`assemble`** (in the parent, zero LP) — feeds the two rows through `run_driver_battery.run_ladder`
  via its `evaluate_fn` test seam, so the expectation ledger, rung order and ladder shape are the
  instrument's, and writes the JSON + markdown exactly as `main()` does.

### 1.4 THE ASSEMBLY PATH IS VALIDATED, BEFORE ANY LP

Pointed at the committed `bau-d46/fc6/_battery_metrics/NEISO/T1.6__NEISO__{vre_short,vre_long}.json`
rows with `--elapsed-s 662.7`, `assemble` re-emits **both committed files byte-identically**:

```
cmp driver-battery-neiso-2026-09-03.json  ->  identical
cmp driver-battery-neiso-2026-09-03.md    ->  identical
```

That proves the assembly introduces no error. It does not prove anything about the `metrics` half,
which can only run against a solved cache; the shard also prints `co2_mt_total` next to the
summary-grain `Σ trajectory.co2_mt` so the two grains are cross-checked on every rung.

---

## 2. PART 2 — G-DRIFT

### 2.1 CONFIG drift against the control (d92/base, recorded key `dd8203a8bf1546b9`) — zero LP

Each rung's config was built at this HEAD exactly as the runner builds it (`reference_config` →
`apply_set_overrides` → `apply_iso_scenario_defaults`) and diffed field-by-field against
`d92/base/run_config.json` `scenario_config`:

| rung | fields differing from the control's payload | of which REAL | schema growth (absent from the older payload) |
|---|---|---|---|
| `vre_short` | 38 | **0** | 38, **every one registered in `_CACHE_KEY_OPTIONAL_FIELDS` and at its frozen drop value** |
| `vre_long` | 39 | **1 — `entry_rate_limits` True → False (the rung override)** | the same 38 |

No payload field is missing at HEAD. **`vre_short` is the control's configuration** — the golden recipe
with both pins and `entry_rate_limits=True` is exactly what `d92/base` solved.

### 2.2 The KEY literal will not be `dd8203a8bf1546b9` — and every reason is accounted for

| | key |
|---|---|
| `d92/base` recorded | `dd8203a8bf1546b9` |
| `head_key(d92/base payload)` at this HEAD | `f04fd06348e1623d` |
| … with `undrop=["caiso_dsw_lateevening_clean"]` | **`dd8203a8bf1546b9`** — reproduces exactly |
| `vre_short` runner key predicted at this HEAD (`ScenarioConfig.cache_key()`) | **`1be407901f4f8000`** |
| `vre_long` runner key predicted at this HEAD | **`df7b178ae9ccbe41`** |

Two key-rule changes separate the literal from the configuration, neither a config difference:

1. **`caiso_dsw_lateevening_clean` was REGISTERED after D92 solved.** D92's payload carried it at
   `False` and hashed it; today's rule drops it. Consequence already visible on `main`:
   `check_key_provenance.py` at this HEAD lists **all four D92 records** (`d92/{base,carbon_plus25,
   gaspm5,gasup150}/run_config.json`) as new `G1_UNKNOWN` rows — the same `lag` class as the seven D92
   §2 named. **Not this lane's to list (the exceptions record forbids it); named to the key-provenance
   desk (capx D85/D91/D93's desk), §8.**
2. **The NEISO solve-surface fingerprint moved.** `solve_surface.moved_rows("NEISO")` =
   `{RGGI_MEMBER_STATES_BY_YEAR}` (pjm-h22 added the 2020 and 2022 membership rows). Classified
   **INERT for a 2026–2050 forecast**: both consumers read `RGGI_MEMBER_STATES_BY_YEAR.get(year)` or
   `.get(year, table[max(table)])`; the added keys are ≤ 2025 and `max(table)` is still 2025, so every
   2026–2050 lookup returns what it returned before. It moves the literal
   (`f04fd063…` at-declaration → `1be40790…` live), never the solve.

**D93 — RECORDED, AS REQUIRED: THIS PINNED SHA *CONTAINS* D93's REGISTRATION.**
`coal_mustrun_requires_measured_row` is in `_CACHE_KEY_OPTIONAL_FIELDS` at frozen `"False"` at
`3affcd71` (verified in `scenarios.py`), so it is dropped from both rung keys. Measured at `6640becc`
(pre-D93) the same `vre_short` config keyed `2336cd3641492c6d` — the field was unregistered and
entered the hash. Either side was acceptable; this lane is on the **post-D93** side.

### 2.3 CODE / DATA drift — ONE LIVE HUNK, AND IT IS LARGE IN PRINCIPLE

Form 4 on a recorded-key basis audits config only (D88, D90-R). A code-level hunk audit against D92's
solve sha is **not possible from this clone**: `aac390a6` does not resolve (the history is grafted,
as D92 §1 recorded). What *can* be audited is the window `6640becc → 3affcd71` merged while this lane
was being scoped, and it carries **one hunk that is LIVE for every forecast by its own author's
declaration**:

> **F1 (2026-09-24, owner instruction)** — vintage-matched eGRID heat rates re-joined into every
> `eia-860/vintage_*/eia860_generators.parquet`, the **canonical snapshot moved from eGRID 2023 to
> eGRID 2024**, and the per-year CAMPD/CHP heat-rate artifacts re-derived. `results/cache.py`'s epoch
> note: *"A SAME-KEY INVALIDATION … every forecast (the canonical snapshot's heat rates now come from
> eGRID 2024) … a forecast re-solve is owed by each forecast lane on its own cadence."*

The six backcast-default flips F1 made are **coerced off outside a backcast** (verified: every
`measured_*_heat_rates` and `eia860_vintage_tracks_solve_year` resolves `False` on both rung configs),
so F1 reaches this solve through **data, not config** — which is exactly what a config audit cannot see.

**THE CONTROL IS BOUGHT, NOT ARGUED, AND IT COSTS NOTHING EXTRA.** `vre_short` is config-identical to
`d92/base` (§2.1), so the `vre_short` rung **is** a same-HEAD control. Its difference from the committed
`d92/base` trajectory is the measurement of HEAD drift since D92 — very probably F1's — and it is
reported cell-by-cell. This is the one place the charter's instruction (*"rebase onto origin/main
before you push your PRECOMMIT"*) and its purpose (*"so the FC-6 block describes the same model the
verdict describes"*) can pull apart, and the decision is declared here rather than after the result:

* **The pin is post-F1**, because the charter orders the rebase and because a battery pinned to a
  pre-F1 SHA would be stale on arrival.
* **Decision rule, fixed now:** the battery is registered **whatever the drift**. The T1.6 rows compare
  the two rungs **to each other**, both at one HEAD, so a post-F1 battery is an internally coherent
  instrument; and it replaces a battery that was further from the verdict's model on every axis
  (legacy bins, no pins, pre-D77). **If `vre_short` differs from `d92/base`, the FINDING says in its
  first section that `neiso-t3`'s FC-6 battery and its primary bundle then sit on different data
  vintages (post-F1 vs pre-F1), and names the owner of the primary-bundle re-solve** — F1's own note
  assigns it to "each forecast lane on its own cadence", which for `neiso-t3` is the capx director's
  desk; this lane will not re-point the primary bundle unasked (that would move FC-1…FC-8, not FC-6).

---

## 3. PART 3 — THE SHARDS

Two rungs → **two concurrent shards**, each ONE indivisible 2026–2050 invocation (the forecast horizon is
an evolution chain: rule 12 `[R-PARALLEL]`; rule 36 `[R-YEAR-ISOLATION]` (c) leaves it unsharded by year).
**This session runs no LP** (rule 32 `[R-SHARD]` (a)).

* `source_revision` = **this PRECOMMIT's full 40-character SHA**; first hard stop `git rev-parse HEAD`
  equals it. No rebase, pull or sync.
* Own `--out-dir` `results/ff-t3-neiso-golden/d94/<rung>/`, own branch `claude/capx-d94-<rung>`.
* **Rule 34 `[R-SHARD-PROMOTABLE]` (a): the FULL out-dir is pushed** — the shard appends
  `!results/ff-t3-neiso-golden/d94/<rung>/**` to `.gitignore` and uses a **plain** `git add` of `.gitignore`
  and its own out-dir; never `-f`, never `-A` / `.`. Slim files first (one commit), cache parquets after
  (separate commits), so the scored artifacts land even if a large push fails.
* Hard stops: SHA; solved `run_config.json` shows both pins and the rung's `entry_rate_limits`; the
  `metrics` subcommand exits 0. Budget: env preparation (hydrate + `data/clean`, ~45–60 min measured by
  D92) + **~30–47 min solve**; stated in each prompt as a single longer shard, never a fan-out
  (rule 32(b)).
* Forbidden by name: edits under `src/` or `scripts/`, anything under `frontend/data/**`,
  `dashboard_add_run.py` / `build_manifest.py` / `build_status.py` / `prune_iso_runs.py`, opening a PR,
  deleting any result. *"A shard that stops with a clear report is a SUCCESS; a shard that repairs
  infrastructure is a FAILURE."*
* Report: container preparation output, the summary's peak RSS, the cgroup memory peak, wall time,
  cache key, the metrics line, and per-year CO2 at 2026/2029/2030/2035/2040/2050.

**The parent** fetches each branch, verifies the config signature + both pins off `run_config.json`,
**recomputes the rung metrics itself from the fetched cache** (zero LP) and requires them equal to the
shard's, then archives the shard (rule 33). **What lands on `main`** (rule 33(f)): the assembled battery
JSON + md, both rung rows, and each rung's slim bundle (`full_horizon_summary.json`, `run_config.json`,
`config.yaml`, 25 `evolution_<year>.json`) — the forecast-golden precedent (`bau-d46/fc6/`, `d92/`). The
per-year cache parquets are kept **out of `main`** by the `.gitignore` lines added in this commit; after
the shard branches are cut, re-deriving a metric from them costs a re-solve (~35–45 min per rung), and
the FINDING will say so.

---

## 4. PREDICTIONS — GRADED IN ADVANCE, FIXED HERE

Anchors: the committed pre-D77 battery (2026-09-03) and `d92/base` (post-D77, pre-F1, config-identical
to `vre_short`). Metric definitions are the instrument's: `co2_mt_total` = Σ of the per-year summary
emissions; `retired_thermal_gw` = Σ over `coal, gas_cc, gas_ct, gas_st, oil, nuclear` of the positive
first-year → last-year capacity drop (so a **CCS retrofit counts as a `gas_cc` retirement** — the
retrofit moves MW to `gas_cc_ccs`, which is not in the list); `reserve_margin_final` = the 2050 ledger
margin; `rps_dual_over_acp` = 2050 REC dual / $50 ACP.

On `d92/base`'s own trajectory these read: CO2 **154.42 Mt**, retired-thermal proxy **5.41 GW**
(gas_cc 12,886.0 → 7,678.6 MW, i.e. mostly CCS conversion), RM₂₀₅₀ **0.0639**, REC dual **$50.00 in all
25 years**, renewable builds **33,000 MW** (1,802 / 1,198 MW alternating from 2029).

| # | prediction | grading rule |
|---|---|---|
| **P1** | **`vre_short` co2_mt_total ∈ [140, 170] Mt** — DOWN from 246.39 (≈ −37 %), because the recipe moves to the post-D77 golden one (`d92/base` = 154.42) | HIT iff in bracket |
| **P2** | **`vre_long` co2_mt_total > `vre_short`'s, by +3 % to +20 %**, landing in **[150, 195] Mt** — DOWN from 275.50. The sign of the rung difference carries over from the pre-D77 battery (+11.8 %) | HIT iff sign AND both brackets |
| **P3** | **`vre_short` retired_thermal_gw ∈ [4.5, 6.5] GW** — UP from 2.012, because the post-D77 CCS wave books ~5 GW of `gas_cc` as a drop | HIT iff in bracket |
| **P4** | **`vre_long` retired_thermal_gw ≥ `vre_short`'s**, in **[4.5, 8.0] GW** — UP from 3.005 | HIT iff both |
| **P5** | **`vre_short` reserve_margin_final ∈ [0.055, 0.075]** — DOWN from 0.08368 | HIT iff in bracket |
| **P6** | **`vre_long` reserve_margin_final < `vre_short`'s, in [0.035, 0.070]** — DOWN from 0.06353 or flat | HIT iff both |
| **P7** | **`rps_dual_over_acp` = 1.0 on BOTH rungs** (unchanged) — the REC dual sits at the $50 ACP in every year of every D92 leg, the carbon +$25 arm included. **Declared a near-certainty; a hit is worth nothing.** | HIT iff both exactly 1.0 |
| **P8** | **`renewable_build_gw` = 33.0 on BOTH rungs** (unchanged). The lever cannot reach VRE in NEISO: VRE entry is bound by `QUEUE_CAP_PER_TECH_GW["NEISO"]` (wind 1.0 + solar 2.0 GW/yr, `config/capacity_market.py:5794`) netted against the 2-year commissioning pipeline (the documented `K−L+1 = 1` ratchet, `model/capacity_evolution/new_entry.py:1695–1706`), which binds before the `ENTRY_GROWTH_LIMIT_MULTIPLE` ladder does. **Declared a near-certainty.** | HIT iff both exactly 33.0 |
| **P9** | **T1.6a and T1.6b both stay VACUOUS** (PASS on the all-constant series `[1.0, 1.0]` → FC-6 CAVEAT). Follows from P7. **Near-certainty.** | HIT iff FC-6 detail still names both as vacuous |
| **P10** | **G-DRIFT: `vre_short` does NOT reproduce `d92/base` exactly** (F1 is live for every forecast) **but its cumulative CO2 lands within ±8 % of 154.42 Mt**. No direction is claimed — a heat-rate vintage swap can move gas dispatch either way — **so this is a weak prediction and is labelled one.** | HIT iff ≠ exact AND within ±8 % |
| **P11** | **DETERMINATION stays HOLD; FC-1…FC-8 statuses, reasons and caveats unchanged; the FC-6 battery row's detail string byte-identical** (it quotes only the vacuous-row labels and `[1.0, 1.0]`). **Near-certainty** (FC-1/2/3/4/7 already FAIL, and the swap reaches FC-6 only). | HIT iff all hold |
| **P12** | Each rung's solve wall in **[28, 50] min**; peak RSS < 5 GB | HIT iff both rungs |

**The one-sentence summary I will be graded on:** *the post-D77 golden recipe moves every battery level a
long way — CO2 down by about a third, retirements more than doubled by the CCS wave, the terminal margin
down — and moves no score, because the ladder's lever cannot reach NEISO's VRE supply and the REC dual is
pinned at the ACP in both rungs, so T1.6 cannot discriminate on this basis at all.*

**Pre-declared answer to "what WOULD discriminate"** (so it cannot be chosen after the fact): a rung pair
whose `renewable_build_gw` actually differs. On this code that needs a lever on the queue-cap / pipeline
binding — e.g. `entry_pipeline_aware_signal=True` (drops the pending-stock netting) or a different
`QUEUE_CAP_PER_TECH_GW["NEISO"]` — **and** a VRE supply large enough to bring the REC dual off the ACP,
which no committed NEISO leg has shown. Owner ruling Q27 forbids trying a third lever inside the ladder,
so this lane **names it and does not try it**; re-pointing T1.6 is an owner card.

---

## 5. PART 4 — THE RE-SCORE, A CONTROLLED SWAP

**The control is already established, in this container, at this HEAD, before any LP:**
`forecast_verdict.py --tier t3` over the committed inputs —

| flag | artifact |
|---|---|
| `--summary` / `--run-config` / `--dof-ledger` / `--attestation` | `results/ff-t3-neiso-golden/d92/base/*` |
| `--hindcast-score` | `results/hindcast/neiso-2021-2025-realized-t1h-d46/NEISO/da19b85495178949/score.json` |
| `--crossover-score` | `results/hindcast/neiso-2023-2027-crossover-rcrepair/NEISO/07e416f3f8072e7c/crossover_score.json` |
| `--paired-invariants` | `results/ff-t3-neiso-golden/d92/paired_invariants.json` |
| `--corridor` | `results/ff-corridor/dispositions/neiso-t3.json` |
| `--driver-battery` | `results/ff-t3-neiso-golden/bau-d46/fc6/driver-battery-neiso-2026-09-03.json` ← **the ONLY input swapped** |

— reproduces `ff-verdicts.json["neiso-t3"]` **NON-PROVENANCE IDENTICAL**: `categories`, `caveats`,
`determination`, `reasons`, `rubric_version`, `schema`, `tier`, `iso` all identical (only `provenance`
and `notes` differ, as they must).

Then `--driver-battery` alone is swapped for `results/ff-t3-neiso-golden/d94/driver-battery-neiso-2026-09-24.json`.
The prior record is preserved byte-equal at **`neiso-t3-pre-d94`** (suffixed-key convention; bare key =
current). **FC-7 cannot move** — its four inputs are carried — so D90-R Addendum B's four-clause rule is
recorded as not triggered, and would be followed literally if it were. Scoring and registration happen
**after the final rebase**; a later rebase re-stamps `scored_at_sha` by an artifact-only re-score before
merge. This lane is the sole writer of `frontend/data/forecast/ff-verdicts.json` this window.

## 6. RULE 31 `[R-RETAIN]` AND BOUNDARIES

* **No solved bundle is deleted, for any reason.** The per-year parquets are kept off `main` by
  `.gitignore`, never by `rm`. The promotion question is asked in the FINDING's close.
* **No file under `src/` or `scripts/` is edited.** Rule 28 `[R-MECH-MATRIX]` does not fire: no mechanism
  proposed, tested or added; no `ScenarioConfig` field changed.
* No backcast artifact, keeper, marker, shard file or freeze is touched. `program-status.json` moves only
  if a NEISO `fc` letter moves (P11 says it will not).

## 7. NAMED AND LEFT (owners named, or "none")

1. **Four new `G1_UNKNOWN` rows — `d92/{base,carbon_plus25,gaspm5,gasup150}/run_config.json`** — the
   `caiso_dsw_lateevening_clean` registration's `lag` class (§2.2). **OWNER: the key-provenance desk
   (capx D85 / D91 / D93).** Not listed here: the exceptions record forbids a lane appending.
2. **`neiso-t3`'s primary bundle is pre-F1** (§2.3). **OWNER: the capx director's desk** (F1's note
   assigns forecast re-solves to "each forecast lane on its own cadence").
3. **T1.6's lever cannot reach NEISO VRE** (P8 and §4's last paragraph). **OWNER: the owner (a Q27-class
   ruling is required to re-point a ladder); no lane can act on it unasked.**
4. **Every OTHER T3 golden's carried FC-6** (D92 §9.8). Out of this charter by the director's scope check
   (`neiso-t3` is the only bare T3 verdict). **Still HAS NO LIVE OWNER.**
