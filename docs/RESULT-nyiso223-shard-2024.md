# RESULT — nyiso-223 shard `nyiso223-y2024` (NYISO 2024 hub gap-fill arm)

**Status: STOPPED — NO SOLVE. Environment blocker, not a model or config fault.**
Pinned revision `ce4779ecd62db3c732e0d0cd7b910b80bc23ed99` (verified). Date 2026-09-10.

Per rule 32 `[R-SHARD]` (b) — "a shard approaching 20 minutes with no artifact stops
and reports; it never pushes a half-written bundle" — and this shard's own hard stop
("If that would exceed 20 minutes, STOP and name the datatype").

## 1. Hard stops — ALL PASSED

| Check | Expected | Observed | Verdict |
|---|---|---|---|
| `git rev-parse HEAD` | `ce4779ec…23ed99` | `ce4779ecd62db3c732e0d0cd7b910b80bc23ed99` | PASS |
| `nyiso_fuelvintage_A/meta.json` `iso` | `NYISO` | `NYISO` (years 2023/2024/2025) | PASS |
| `grep -c nyiso_hub_gap_month_level scenarios.py` | ≥ 4 | 4 | PASS |

## 2. PRE-SOLVE GATE — PASSED, EXACTLY ON THE REGISTERED VALUES

Zero-LP. Reproduced the PRECOMMIT prediction to the digit:

| Quantity | PRECOMMIT expected | Observed | Verdict |
|---|---|---|---|
| Annual mean hub gas, off → on | 2.7969 → 2.7969 | **2.7969 → 2.7969** | PASS (identical to 4 dp) |
| Dec 22–31 mean, off → on | 3.877 → 4.061 | **3.877 → 4.061** | PASS |
| Hours moved | 5880 | **5880** | PASS |

**This is the one substantive result the shard produced, and it is real evidence.**
The arm's *mean-preservation* claim holds at the fuel-price layer for 2024: the gap
fill redistributes 5,880 hours (67.1 % of the year) while leaving the annual mean
unchanged to 4 decimal places, and it lifts the Dec 22–31 window by
**+0.184 $/MMBtu** (+4.7 %). What it does NOT establish — because no LP ran — is
whether that redistribution is energy-neutral *in dispatch*, which is exactly what
report item 8 (any class moving > 0.10 TWh) was meant to test. **That question is
still open.**

## 3. THE BLOCKER — `data/clean` DOES NOT EXIST IN THIS CONTAINER

`ls data/clean/` → *No such file or directory*. The entire curated layer is absent.
`data/clean` is gitignored ("DERIVED, disposable"), and `hydrate_data.py --profile
nyiso` does not build it — in this container it reported *"This is a FULL clone —
every blob is already local, so hydrating changes nothing."* So a shard launched this
way has raw data but no curated data, and the model reads through
`scripts.lib.clean_io.read_clean`.

Two consecutive solve attempts died in the year loop, each naming a different missing
partition. Both failed in **~5 seconds** — no LP was ever entered.

1. `ValueError: nyiso_li_lcr_tsl=True but no published Long Island
   transfer_security_limit for delivery year 2024/2025 … available areas: []`
   — `src/market_sim/model/interchange/nyiso.py:279`.
   The raw row **exists** (`data/raw/capacity-deliverability/nyiso/nyiso.csv` carries
   `NYISO,2024/2025,annual,Long Island,locality,transfer_security_limit,940`); the
   loader reads the *clean* partition, which was absent. **Fixed** by
   `curate_capacity_deliverability.py --isos NYISO` (35 rows); verified
   `transfer_security_limit_by_area('NYISO','2024/2025')` → `{'Long Island': 940.0}`.
   This consumed the shard's one authorized "regenerate the named datatype, retry once".

2. `FileNotFoundError: nyiso_seam_par_attribution 2024: could not read the
   'nyiso-interface-flows' clean partition … (the mechanism never silently no-ops)`
   — `src/market_sim/data/nyiso_par_attribution.py:378`, reached from
   `run_calibration.py:2921`.

Both loaders **raise rather than degrade** because their mechanisms are explicitly
enabled in the keeper recipe — correct behaviour (rule 1 `[R-STRUCT]`: a mechanism
must never silently no-op), but it means every clean datatype the recipe touches is a
hard prerequisite. Datatype 2 would not have been the last.

## 4. WHY REGENERATION DOES NOT FIT THE BUDGET — MEASURED, NOT ESTIMATED

`scripts/regenerate_clean.py` is the named remedy, but it has **no per-ISO and no
per-year filter** — it rebuilds every registered datatype for **all seven ISOs across
all years**. Measured in this container:

- **~50 datatypes** in `DATATYPES`.
- After **682 s (11.4 min)**: **5 complete** — `load`, `demand-profile`,
  `ancillary-services`, `generation`, `renewables` — and it had just entered
  `emissions` (`curate_emissions.py`, CAMPD unit-level, all ISOs/years), one of the
  heaviest, with `lmp`, `fleet`, `outages`, `emissions-unit-annual` still ahead.
- That is **10 % of the tree in 11.4 min**, with the expensive datatypes not yet
  started. A full rebuild is plausibly **45–90 min**, *before* the ~15-minute NYISO
  2024 LP.

Total wall clock at the stop decision: **~28 min, no artifact**. Continuing would have
put this shard at 60–105 min — 3–5× the owner's 20-minute rule — so it stopped.

**The regeneration was left RUNNING, not killed**, so a follow-up in this same
container can reuse the completed partitions. Note the container is ephemeral: it does
not survive session reclamation.

## 5. NOTHING WAS DELETED (rule 31 `[R-RETAIN]`)

No result was removed. `results/calibration/nyiso223_gapfill_2024/` exists but contains
only an empty `dispatch/` directory — the solve never produced a bundle, so there is
nothing promotable and nothing to retain. The path is already gitignored and was left
in place. No file under `src/` or `scripts/` was edited; no bundle was committed.

## 6. WHAT THE PARENT SHOULD DO

The fix belongs in **shard setup**, not in the model. Options, best first:

1. **Add a clean-tree build to the shard SETUP block**, scoped to NYISO — the launch
   recipe currently ends at `hydrate_data.py`, which does not build `data/clean`.
   `curate_capacity_deliverability.py` accepts `--isos`, so per-ISO scoping exists at
   the curate-script layer even though `regenerate_clean.py` exposes no such flag; a
   NYISO-scoped build should be far cheaper than the ~50-datatype all-ISO sweep.
2. **Or pre-build `data/clean` once in the parent** and hand shards a container that
   already has it — this cost is paid per shard today, so it multiplies across a fan-out.
3. **Or determine the exact datatype set** the NYISO keeper recipe touches and
   regenerate only those. The discovery loop is cheap (each failure names its datatype
   and costs ~5 s), but it is serial and needs a budget of its own.

Until one of those lands, **no NYISO shard launched this way can solve**, and this is
not specific to 2024 or to the gap-fill arm — the 2023 and 2025 shards will hit the
identical wall.

## 7. ITEMS 1–8 OF THE REPORTING CONTRACT

**Not answerable — no LP ran.** C3a, C3b (the 0.179-vs-0.20 margin the parent flagged
as tightest), C3c, C1 per-class TWh, C8 forced shares, the Dec 22–31 vs Dec 1–21 price
split, the determination, and the >0.10 TWh class-movement falsification test all
require the solved bundle. No number for any of them is reported here, and none should
be inferred from §2 — the gate is a fuel-price identity, not a dispatch result.
