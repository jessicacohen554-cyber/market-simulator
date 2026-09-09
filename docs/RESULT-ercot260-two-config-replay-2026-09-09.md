# RESULT — the two-config replay defect is FIXED, and the keeper's 2023 leg now replays BIT-IDENTICALLY (ercot-260)

> Card 1 of the ercot-260 charter. **Plumbing, not a mechanism** — no
> `ScenarioConfig` field, no CLI flag, no solve-path change, so no PRECOMMIT
> (rule 29 `[R-SCREEN]` governs mechanism arms). One LP was spent, purely as
> proof. **Card 2 is not started: it is blocked on an owner promotion ruling,
> not on this fix.**

## 0. Bottom line

| | |
|---|---|
| **Is the defect fixed?** | **YES.** §2–§3 |
| **Proof** | A `--replay-bundle` of the keeper's **2023 carve-out year** now solves `swcap=True` / CC_REGULAR `peak=151.008`, and its dispatch is **bit-identical** to the keeper's committed 2023 leg — 61,320 zone-hour rows, max \|Δ\| **0.000000e+00** on price, demand, slack, dump and reserve price. §3 |
| **C3a** | **−7.17 %** (model 59.708 vs actual 64.32), matching the keeper's committed **−7.2 % PASS**. The broken replay read **−39.6 %**. §3 |
| **Does it unblock the ERCOT full span?** | **Yes**, one recipe group per invocation, chained. §2.3 |
| **Any keeper, determination or scored number changed?** | **NO.** Nothing under `src/` was touched; no bundle was registered. §5 |
| **Card 2 (the ercot-259 merit-allocation arm)** | **NOT started — awaiting the owner's promotion ruling.** §6 |

---

## 1. The defect, restated from the artifacts

ERCOT is a **two-config keeper** (owner ruling 2026-08-26): a FORWARD config
for 2024–2025 and a CARVE-OUT for 2021–2023. A bundle's `meta.json` is the
authoritative snapshot of the kwargs `solve_and_persist` was called with — but
it can hold only **one** config, and for the composite keeper it holds the
forward one. The carve-out's two distinguishing keys —
`ercot_offer_swcap_clip=true` and the ×33.0 `offer_curve_by_group` peak bands
(CC_REGULAR `peak` 151.008 against the forward 4.576) — are **`ScenarioConfig`
fields, not `solve_and_persist` kwargs**, so they appeared in *no* `meta.json`
at all and had *no* CLI flag. They entered the keeper's carve-out legs by hand,
through `--set`, at solve time.

Consequence: `--replay-bundle` silently solved the **forward** config on a
carve-out year and reported the result as the keeper's. Measured by ercot-259,
whose control replayed the keeper on 2023 and got `swcap=False` / `peak=4.576`,
**C3a −39.6 %** — against the keeper's own **−7.2 % PASS**. Both of that
session's arms carried the error, which is why C3a read −39.6 % in each.

This is `RESULT-ercot256` §10's unfixed open item, verbatim: *"the composite
still records neither key … The fix is a per-year recipe map in the composite
writer."* It blocked any ERCOT full-span re-solve, by any lane, for any
mechanism.

---

## 2. The fix — two halves, and neither invents a value

### 2.1 WRITER — `scripts/stamp_config_partition.py` (new)

`meta.json[config_partition_overrides]` records, per solved year, the exact
extra `ScenarioConfig` keys that year carried on top of the meta recipe. The
block already existed on the keeper (ercot-256 wrote it **by hand**, as
provenance nothing consumed). It is now **derived**, never transcribed: each
leg's own committed `run_config*.json` records the resolved `scenario_config`
it solved, so a leg's overlay is that dump **diffed against the bundle's base
`run_config.json`**. Every value's source is a committed artifact of the solve
it describes; there is no free parameter and nothing is fitted.

Four **year-driven** fields are excluded (`YEAR_DRIVEN_FIELDS`) because they
differ between legs by virtue of covering different *years*, not different
recipes — recording them would pin one year's inputs onto another:
`weather_year`, `gas_price_override` (the year's Henry Hub actual), and
`ordc_voll` / `ordc_mcl_mw` (ERCOT's **own published** ORDC parameters by year:
VOLL $9,000 → $5,000 and MCL 2,000 → 3,000 MW after 2021). `RESULT-ercot256`
§8a measured this exclusion directly.

`--check` re-derives without writing, so a later session or CI can prove a
stamped block still reproduces from the artifacts beneath it.

**The derivation was validated against the hand-typed keeper block**, which it
reproduces:

```
OK: config_partition_overrides re-derives from the committed run_config legs
    — every year resolves identically (3 overlaid year(s): 2021, 2022, 2023)
  note: 2021 pins ercot_zonal_spread_ep_referenced at the base value (redundant, behaviour-identical)
  note: 2022 pins ercot_zonal_spread_ep_referenced at the base value (redundant, behaviour-identical)
```

`--check` tests **effective-config equivalence**, not raw dict equality: a
stamped key whose value already equals the base is a redundant pin, not drift.
The hand-typed block pins `ercot_zonal_spread_ep_referenced=True` on 2021/2022,
which *is* the base value; raw equality would fail on that and say nothing true.
A key that **resolves differently** is real drift and still fails.

### 2.2 CONSUMER — `replay_keeper.enforce_single_recipe_partition`

`replay_keeper._IGNORE` carried the block as provenance with the comment
*"consuming this block automatically is the FIX, and it is deliberately not
attempted here."* It is attempted now. Both replay entry points —
`replay_keeper.main` and `run_calibration_full.run_replay_bundle` — call the
**same** consumer, so the two paths cannot diverge (a fix on one would have left
`--replay-bundle`, the CI-dispatchable form, still defective).

The overlay is routed down the **same two channels `--set` uses** — the explicit
`solve_and_persist` kwarg where one exists, *and* the generic `prb_overrides`
`ScenarioConfig` channel — because `run_year`'s application order is mixed and a
single-channel write is silently re-stomped by the other (the ERCOT-65 defect
class). That is exactly the channel the ercot-256 promotion set these keys
through by hand, so a consumed overlay **reproduces** the leg rather than
approximating it. It is applied **before** `--set`, so an operator override
still wins, and a key that maps to nothing is a **hard error**, never a silent
drop (the miso-50..53 lossy-reconstruction class).

### 2.3 A mixed-recipe span is REFUSED, not silently mis-solved

One `solve_and_persist` call carries one config. Asking for a span whose years
do not share an overlay now hard-fails and names the groups:

```
bundle records a config_partition_overrides overlay that splits the requested
span into 3 recipe groups ([2021, 2022] -> ercot_offer_swcap_clip, …;
[2023] -> …; [2024, 2025] -> the base recipe). One solve carries ONE config, so
replaying them together would solve a single group's recipe over every year —
the two-config replay defect this block exists to close. Chain one invocation
per group with --years (and --reuse-solved to carry solved years forward).
```

Refusing is the honest behaviour and it is not a new burden: the per-invocation
chain is already the ERCOT idiom under rule 12 `[R-PARALLEL]`, whose single-year
LP needs 6–9 GB (this session's measured 9.9–11.7 GB RSS). The keeper's span
partitions into exactly its **three original solve legs** —
`[2021, 2022] / [2023] / [2024, 2025]` — which the code derives independently
of the filenames.

A bundle with **no** overlay block is untouched: the consumer returns
immediately and does not so much as create an empty override bag, so every
one-config replay stays byte-identical.

---

## 3. THE PROOF — one LP, and it is bit-identical

`--replay-bundle results/calibration/ercot256_five_year_keeper --year 2023`,
written to a scratch dir (never `results/calibration/`, never registered).

**Resolved config of the replay** (`run_config.json` `scenario_config`):

| key | replay | keeper carve-out | forward (what the broken replay solved) |
|---|---|---|---|
| `ercot_offer_swcap_clip` | **True** | True | False |
| `offer_curve_by_group` CC_REGULAR `peak` | **151.008** | 151.008 | 4.576 |
| CC_CHP `peak` | **123.684** | 123.684 | — |
| CT_PEAKER `peak` | **433.95** | 433.95 | — |
| ST_GAS `peak` | **105.6** | 105.6 | 3.2 |
| `ercot_zonal_spread_ep_referenced` | **False** | False (2023) | True |

**Scored outcome**, model side computed from the committed `hourly/system_<year>.parquet`
P1 rows as the demand-weighted mean price — a construction validated by
reproducing the scorer's own recorded keeper value (59.71) to 59.708:

| | model LW mean LMP | vs actual `rt_lw` 64.32 |
|---|---|---|
| keeper's committed 2023 | 59.708 | **−7.17 %** (scorer: −7.2 % **PASS**) |
| **this replay** | **59.708** | **−7.17 %** |
| ercot-259's broken replay | — | **−39.6 %** |

**And the stronger claim holds: the replay is bit-identical to the keeper's
committed 2023 leg.** Over all 61,320 P1 zone-hour rows:

| field | max \|keeper − replay\| |
|---|---|
| `price` | 0.000000e+00 |
| `demand` | 0.000000e+00 |
| `slack` | 0.000000e+00 |
| `dump` | 0.000000e+00 |
| `reserve_price` | 0.000000e+00 |

That is what `replay_keeper.py`'s own docstring promises ("byte-faithful
re-solve") and what was silently broken for the carve-out years.

---

## 4. Tests

`tests/scoring/test_config_partition_replay.py` — **24 tests**, all passing.
They pin: the overlay read (annotation keys are never recipe keys; an absent
year is the base recipe; a bundle with no block is unaffected); the partition;
the consumer (the overlay reaches the generic channel, a base-recipe year leaves
`kwargs` untouched entirely, a mixed span is refused, an unconsumable key is a
hard error); **that the overlay never mutates the caller's `meta`**; the writer's
derivation and its year-driven exclusion set; that **both** entry points call the
same consumer; and a round-trip on the committed ERCOT keeper — its carve-out
years carry the two keys that had no home, its forward years are the base
recipe, a 2023 replay resolves the carve-out, and the full span refuses.

**One bug in my own code was caught by these tests before any solve:**
`build_kwargs` binds the override bag straight off `meta`, so a
`setdefault`-and-mutate consumer wrote *through* it — contaminating the base
recipe for every later group of the same span (a forward-leg replay picked up
the preceding carve-out leg's `swcap`/`peak`) and mutating the caller's parsed
`meta.json`. Fixed with the defensive copy the per-flag override blocks in
`run_replay_bundle` already use, and pinned by two tests.

---

## 5. What did NOT change

* **No file under `src/market_sim/`** — `git diff --stat origin/main -- src/` is
  empty. No `ScenarioConfig` field, no CLI flag, no solve-path change, so the
  mechanism matrix takes no cell (`check_mechanism_matrix --base origin/main`
  exits 0) and no cache key moves.
* **No keeper, no determination, no scored number.** The keeper's committed
  artifacts are untouched; the proof bundle is unregistered and lives outside
  `results/calibration/`.
* **Gates:** `check_registry_payload_parity` OK (23 runs, 55 bundle dirs),
  `audit_keepers --iso ERCOT` PASS (0 failures, 0 warnings),
  `build_status --check --iso ERCOT` in sync, `check_mechanism_matrix` exit 0.
  `tests/scoring` is **15 failed / 1509 passed** both before and after — the
  same 15, baselined on this branch before any edit.

**Two pre-existing reds observed and NOT touched**, neither caused by nor
fixable within this change:

1. `check_cache_key_registration --base origin/main` **FAILS** on
   `HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT`, undeclared in
   `solve_surface_declared.py`. Both files are under `src/market_sim/config/`,
   which this branch does not touch, so it reproduces on `main`. It belongs to
   whichever lane added the constant; declaring it here would be an unrelated
   core-infrastructure edit inside a plumbing PR.
2. The report's `[7c]` operating-shape gate reports **4 regressions** for 2023
   against its keeper baseline. Since this run is *bit-identical* to the
   keeper's own 2023 leg, the keeper reproduces those same 4 — i.e. the
   **baseline is stale**, and the gate is not measuring what it names.

---

## 6. NAMED, and not taken here

* **Card 2 — re-solving the ercot-259 merit-allocation arm across 2021–2025.**
  Not started, and *not* because of this defect: the mechanism is already on
  `main` behind `--netload-drag-merit-allocation`, and the span is now
  reproducible. It waits on **the owner's promotion ruling**, which ercot-259
  explicitly left open (its own recommendation was *against*, on evidence
  reported at full magnitude: the 3452 D-4 conviction stands, and C8 ST_GAS
  rises 0.1347 → 0.1775). Rule 31 `[R-RETAIN]` is why this session did not
  pre-empt it. Cost if ruled promote: **~30 min of LP per ERCOT year × 5 years,
  sequential**, plus registration.
* **A CI gate binding the two.** An ISO whose keeper shard carries a
  `config_partition` block could be *required* to carry a
  `config_partition_overrides` block in its bundle meta, verified with
  `stamp_config_partition.py --check`. That would stop the defect recurring on a
  future composite rather than relying on the assembling session to remember.
  Not taken here: it touches `audit_keepers` / CI, ERCOT is the only ISO with a
  partition block today, and `tests/scoring/test_golden_manifest_provenance.py`
  already carries 6 pre-existing failures in exactly that area — a gate added on
  top of a red surface would not be readable.
* **Automating the composite *assembly*.** `plan_reuse_solved` refuses reuse
  precisely when configs differ, so `--reuse-solved` cannot compose a two-config
  bundle; the keeper's was assembled by hand. The writer makes the resulting map
  derived and checkable, but the assembly itself is still manual.

---

*Generated by [Claude Code](https://claude.ai/code)*
