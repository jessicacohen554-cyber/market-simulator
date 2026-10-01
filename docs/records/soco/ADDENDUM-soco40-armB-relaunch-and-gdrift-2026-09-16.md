# ADDENDUM (soco-40, 2026-09-16) — arm B was LOST, and the G-DRIFT audit for its re-launch

Written by the SOCO-40 **continuation** session, BEFORE the re-solve is launched
(rule 29 `[R-SCREEN]` (b): the drift audit is recorded before the arm is solved, so it
cannot be written to fit the result).

## 1. What happened to arm B

PRECOMMIT §11 designated a coal-split re-solve as the keeper: one shard, pinned to
`81540853c29fd7a9e96472f890e949f8cb997047`, out-dir `results/calibration/soco40_coalsplit_B`,
branch `claude/soco-40-coalsplit-2023-2025`.

**It never produced a bundle.** Measured at handoff:

- Shard `session_011JYECedtW7ZwpeqP9D54WD` created `2026-09-16T06:39:41Z`, last updated
  `06:46:15Z`, `session_status = ARCHIVED`, post-turn status *"SOCO backcast in progress;
  waiting on year solves"*. It was archived roughly seven minutes in, mid-solve — arm A's
  whole three-year invocation took just under eleven minutes, so the solve was still running.
- `git ls-remote origin` returns **no** `claude/soco-40-coalsplit-2023-2025` ref. The only
  surviving soco-40 shard branches are `claude/soco-40-screen-2024` (`d6b7b7d4…`) and
  `claude/soco-40-span-2023-2025` (`9458759f…`).

This is rule 33 `[R-SHARD-ARCHIVE]` (b) — *never archive a shard that is still running* —
violated against a shard that had not yet pushed. Nothing was deleted, so rule 31
`[R-RETAIN]` is not implicated; the bytes never existed. The parent's own container was
reclaimed as well, taking its working tree (the local extractions, the arm-A registration
files and the arm-A verdict/attestation scratch) with it. Everything the parent had
**committed** survived: `b7f6b494…` is an ancestor of `main`, so the bench parts
`frontend/data/backcast/bench/SOCO/{2023,2024,2025}.json.gz`, the `keepers/index.json`
SOCO row, `data/raw/_processed-legacy/coal_supply_SOCO.csv` and PRECOMMIT §11 are all on
`main`.

**Cost stated before re-solving (rule 31 `[R-RETAIN]`, final clause):** one shard,
`--year 2023 2024 2025` in a single invocation, ~11 minutes of LP by arm A's measured
timing (P0 22.9 + 9.8 + 4.3 s, P1 7.2 + 7.3 + 2.3 s; whole invocation 06:18:22Z →
06:29:11Z). The owner was asked and ruled **re-launch**.

## 2. Retrievability of what DID survive (rule 34 `[R-SHARD-PROMOTABLE]` (d))

`git ls-tree -r <sha> -- results/calibration/<bundle>` returns > 0 files for both:

| bundle | full SHA | files | recovery |
|---|---|---|---|
| `_soco40_screen` (2024 screen, rule 29 throwaway) | `d6b7b7d4dc9571b4058fbc9d13487cd9edfee900` | 15 | `git archive <sha> results/calibration/_soco40_screen \| tar -x` |
| `soco40_baseline_B` (span arm A, unsplit coal) | `9458759f6b8c875a9a302e4b64db9e212420ddf9` | 34 | `git archive <sha> results/calibration/soco40_baseline_B \| tar -x` |

Both carry `dispatch/<year>_P1.parquet`; arm A additionally carries `launch.log`, from which
the full calibration report, the solve timings and `memory peak: cgroup_peak_rss_gib=2.65`
were recovered in this session.

## 3. G-DRIFT — the audit that fixes arm B's pin

Arm A solved on `131989516176b113203fed1aa4b06e502d3abf79` (the PRECOMMIT SHA). Arm B is
re-launched on **this addendum's own commit**, which is `origin/main`
(`5e7cbb7d7d3ff0e85a0edb99d74ae02708eb6357`) plus this file. `main` is chosen over the
PRECOMMIT's original `81540853…` for one reason: `81540853…` was rebased away and is now an
**unreferenced** commit (its content reached `main` as `31b9a174`). It still fetches today,
but an unreferenced object is a GC hazard for a shard clone, and a pin must be durable.

Solve-path diff `13198951… → this addendum's commit` (identical to `13198951… → origin/main 5e7cbb7d…`, since this addendum adds only a doc), every hunk classified:

| file | verdict | reason |
|---|---|---|
| `src/market_sim/data/eia930/envelopes.py` | **INERT** | Docstring/comment only — no executable line changes. |
| `src/market_sim/data/eia930/frames.py` | **INERT** | Entirely the NWPP **pool** path (`_screen_pool_member_frame`, `_pool_member_frames`, `_pool_hourly_frame`). `_POOL_HOURLY_MEMBERS` has exactly one key, `NWPP`, and SOCO is not a member — SOCO is a single-BA extract (`data/raw/eia-930-hourly/SOCO hourly.parquet`). |
| `scripts/run_calibration_full.py` | **INERT** | Purely additive: `_hydro_cascade_frame` returns `None` when `result.hydro_cascade_spill is None`, so an unarmed run gains no file; plus a new tri-state `--hydro-cascade-coupling` flag, left unset, on `_CACHE_KEY_OPTIONAL_FIELDS` (no key move). SOCO never arms `hydro_cascade_coupling`. |
| `src/market_sim/data/eia930/actuals.py` | **LIVE** | Lane NWPP-39's zero-baseline guard on the fuel unit-slip screen (`_FUEL_SPIKE_PLATEAU_PCT = 99.0`). |

### 3.1 The one LIVE hunk, named rather than absorbed

NWPP-39's guard releases a `NG:` column from the unit-slip screen when its p99.9 is itself
more than `_FUEL_SPIKE_RATIO` times its p99.0 — i.e. when the top 0.1 % of the series is a
tail rather than a plateau, so the screen's own premise is falsified by the series. Of the
21 flagged series repo-wide, exactly four are released, and **two of them are SOCO's**:

- `NG: OIL` **2023** h7975 (390 MW; a 2023-11-29 morning start 146 → 390 → 100 MW)
- `NG: OIL` **2024** h386–392 (Winter Storm Heather; 530 → 649 → 660 → 687 → 762 → 801 →
  350 MW, tracking SOCO demand from 41.0 to 47.4 GW), 4.4 GWh

Arm A's `launch.log` shows both being **repaired away** (`repairing 1 … spike hour(s)
[7975]`; `repairing 7 … spike hour(s) [386…392]`). That is exactly the false positive the
PRECOMMIT already carries as determination-basis disclosure **R-w**, and NWPP-39 fixes it
under rule 14 `[R-ACCURATE]`.

**Consequences, stated plainly:**

1. The hunk is **benchmark-side only** — it touches the EIA-930 *actuals* series SOCO is
   scored against, not the LP. SOCO's model oil generation is 0.00 TWh in 2023 and 2024.
2. Arm A → arm B is therefore **not** a single-variable comparison. It carries **two**
   changes: the coal split (the owner's instruction, the intended variable) and this
   benchmark oil repair. The second is ~4.4 GWh in 2024 and ~0.29 GWh in 2023 against a
   ~250 TWh system — **~0.002 %** — and lands on the benchmark `oil` row, a row neither arm
   competes on. It cannot move C1's coal or gas rows, which is where the comparison lives.
3. Disclosure **R-w** is expected to be **discharged** by arm B rather than carried. The
   FINDING reports what the bundle actually shows, not this expectation.
4. Taking the guard is the rule 14 `[R-ACCURATE]` call: the alternative — pinning
   `13198951… + the coal CSV` for a cleaner comparison — would knowingly solve the keeper
   against a benchmark containing a documented weather event deleted as telemetry noise.
   A cleaner A/B is not worth a keeper scored against data we know to be wrong.

## 4. The re-launch (unchanged from PRECOMMIT §11 except the pin)

```
uv run python scripts/run_calibration_full.py --iso SOCO --year 2023 2024 2025 \
    --out-dir results/calibration/soco40_coalsplit_B \
    --note "soco-40 coal-split keeper: COAL split to COAL_BIT/COAL_PRB on the measured
            EIA-923 supply census (owner instruction), all-defaults otherwise, every offer
            band 1.0, authorized_price_tuning NONE"
```

No other flag (§3.1's stop list stands). Years sequential in one invocation (rule 12), one
bundle (rules 16 / 32(b)). Rule 34 `[R-SHARD-PROMOTABLE]` (a) applies and is the correction
to the lost shard: the bundle is **pushed** to the shard's own branch via a `.gitignore`
negation and a plain `git add` — never `git add -f`.
