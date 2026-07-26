# FINDING (miso-92, 2026-07-26) — MISO's cross-year resident floor is attributed and 35 % of it is REMOVED: one 588.9 MB unit-hour frame the year-release `del` list never named

**Lane.** LANE 2 of the miso-92 handoff: *"READ THE MEMORY TELEMETRY (still
unread). Do NOT propose a fourth story — TAKE THE MEASUREMENT."* Charter, written
before any telemetry line existed to look at:
`docs/handoffs/miso-92-memory-attribution-charter-2026-07.md`.

**Keeper `2026-07-25-miso-88-egrid-hr` UNCHANGED. Determination UNCHANGED:
CALIBRATED-WITH-CAVEATS, 3/3 ledgered caveats.** No scoring criterion is touched
and no value in the model changed; dispatch is bit-identical (§4).

**Bottom line.** The ~1.35 GB (86 %) that miso-90 could not attribute is now
attributed, and its dominant component is gone. The single largest object alive
at the year-release seam was a **588.9 MB unit-hour dispatch frame** (24,694,440
gen-hours × 11 cols) still bound to the `_dispf` loop variable *after* it had
been written to `dispatch/<year>_<pass>.parquet` and with nothing left to read
it. The release block's `del` list simply never named it, so it sat underneath
the **next** year's fleet build and LP. Freeing it at the write site takes the
cross-year floor **1.53 → 1.00 GB (−35 %)** with **bit-identical dispatch**.

**Two corrections to the record, both established by measurement (§5, §6): the
`lru_cache` hypothesis is refuted a second time and more strongly, and HiGHS is
exonerated as the owner of the floor.** A third correction is to this document's
own first draft, which framed the keeper's non-reproduction at HEAD as a new
defect when it is already recorded and explained (§7).

---

## 1. The measurement

One MISO 2023 year, keeper config replayed unmodified. Reproduced across **four
independent solves**, so none of the figures below is a single read:

| | memtel | determ | frames | **fixed** |
|---|---|---|---|---|
| resident after release | 1.53 | 1.54 | 1.55 | **1.00** |
| peak | 14.40 | 14.39 | 14.40 | **14.41** |
| accumulators | 0.07 | 0.07 | 0.07 | 0.07 |
| arena `in_use` | 0.73 | 0.73 | 0.73 | **0.15** |
| arena `free_retained` | 1.29 | 1.28 | 1.29 | 1.88 |
| `mmapped` | 0.37 | 0.37 | 0.37 | 0.37 |
| `ndarray_gb` | 0.69 | 0.69 | 0.69 | **0.11** |
| `pandas_gb` (n) | 0.68 (17) | 0.68 (17) | 0.68 (17) | **0.10 (16)** |
| populated caches / entries | 30 / 38 | 30 / 38 | 30 / 38 | 30 / 38 |

All values GB. The first three are pre-fix; `fixed` is post-fix.

### The pre-registered decision rule fires on the LARGE branch

The charter pre-registered `ndarray_gb ≥ 0.50 GB` ⇒ *"live Python payload owns
the floor; the split names the owner; the fix is in the model."* Measured
**0.69 GB** — the LARGE branch, unambiguously (the MIXED band was 0.20–0.50).

### Site attribution — the top retained objects

```
588.9 MB  24,694,440 x 11  year,pass,unit_id,plant_code,klass,fuel,supply,zone,hour,mw,lmp
 56.7 MB   4,248,600 x  4  year,plant_id,hour,net_mw                     <- campd accumulator
 22.9 MB     126,342 x 20  plant_id,plant_name,prime_mover,fuel_type,...  <- EIA-923 fleet
  9.2 MB     148,920 x  6  year,pass,from_zone,to_zone,hour,mw           <- flows accumulator
  5.1 MB      70,080 x  9  year,pass,zone,hour,price,slack,dump,...      <- system accumulator
  4.4 MB      68,919 x  7  year,month,plant_id,state,fuel_group,...      <- F923 fuel prices
```

The top six sum to ≈687 MB ≈ the full 0.68 GB pandas payload: **fully
attributed, no remainder.** Five of the six are legitimate — three are the
runner's own declared cross-year accumulators (0.07 GB total, matching the
existing telemetry) and two are loader state. The 588.9 MB frame is the only
object with no reason to be alive.

24,694,440 = 2,819 LP generators (incl. the pseudo wind/solar/must-run rows) ×
8,760 hours, i.e. **one pass's** complete unit-hour dispatch.

## 2. Root cause

`scripts/run_calibration_full.py`, inside `for label, res in labelled:` —
`_dispf` is built, written to parquet, and then never touched again:

* last use is `_dispf.to_parquet(run_dir / "dispatch" / f"{year}_{label}.parquet")`;
* the year-release block deletes `result, context, result_p1, p2_state, demand,
  must_run, must_run_total, labelled, res` — **`_dispf` is not in the list**;
* so it stays bound as a function local, survives `gc.collect()` and
  `malloc_trim(0)` (both correctly decline to free a *live* object), and is
  still resident while the next year builds its fleet and LP.

This is why `malloc_trim` helped but could not finish the job: miso-89's trim
(`c4be52d`) cut the hand-off 2.98 → 1.56 GB by returning genuinely free heap,
but 589 MB of what remained was **live**, and no allocator-side measure can
release live memory.

**The fix is one `del` at the write site** (not at the release block, so the
frame is also gone between the two passes). `_sysf` and `campd_year` are
deliberately left alone: both are appended to cross-year accumulators and are
legitimately live — a distinction the frame telemetry made visible.

## 3. Result

| | before | after | Δ |
|---|---|---|---|
| cross-year resident floor | 1.53 GB | **1.00 GB** | **−0.53 GB (−35 %)** |
| live `in_use` | 0.73 GB | **0.15 GB** | −0.58 GB |
| retained Python payload | 0.69 GB | **0.11 GB** | −0.58 GB |
| single-year peak | 14.40 GB | 14.41 GB | **unchanged** |

The −0.58 GB of live memory freed and the −0.53 GB resident drop differ by
~0.05 GB because glibc keeps part of the freed span as resident free arena
(`free_retained` rises 1.29 → 1.88 GB, `trim_top` 0.00 both before and after —
the top of heap was already fully returned, so what remains is interior
fragmentation `malloc_trim` structurally cannot give back).

**The peak is unchanged and was never going to change**: the frame is built
*after* the LP solves, so it is not part of the 14.4 GB high-water mark.
**Therefore the staged one-year-per-process `--reuse-solved` recipe REMAINS
REQUIRED** — this finding does not lift it, and must not be read as lifting it.
What it removes is 589 MB from the base each subsequent year builds on.

## 4. Dispatch is bit-identical

Verified `miso92_determ` (pre-fix, HEAD) vs `miso92_fixed` (post-fix), identical
invocations:

* `system_2023.parquet` — `price`, `slack`, `dump`, `demand`, `reserve_price`:
  `max|diff| = 0` on every column.
* `class_hourly_2023.parquet` — `mw`: `max|diff| = 0`.
* `dispatch/2023_P1.parquet` — **sha256 identical** (`40f1f013bde89e8d…`,
  73,683,342 bytes both). The frame is still written in full; only its
  *retention after the write* changed.

## 5. Correction 1 — the `lru_cache` hypothesis is refuted AGAIN, and harder

miso-90 refuted it at 0.019 GB but measured only the data-load path, where **9
caches / 14 entries** populate. A real solve populates **30 caches / 38
entries** — including `_eia_hourly_frame` ×4 and `_eia_hourly_frame_filled` ×4,
which are full-year hourly frames and look like plausible suspects by name.

Measured directly (no LP): loading **all 9 BA extracts × both caches** for 2023
totals **0.015 GB**. High entry count, negligible payload. The suspicion that
miso-90 had measured the wrong cache set was itself wrong — the caches a solve
adds are also inert.

**`clear_all_caches()` therefore stays unwired**, as miso-90 intended and as this
charter fenced: it now buys ~0.02 GB against a floor of 1.00 GB, with real
correctness risk. The cache census is worth keeping as telemetry precisely
because it lets a future session rule the caches out in one line instead of
re-arguing them.

## 6. Correction 2 — HiGHS is not the owner

The standing alternative was that HiGHS/`highspy` C++ state survives the
Python-side `del`. It does not, to within a bound this measurement can state.

Pre-fix, total live malloc = `in_use` 0.73 + `mmapped` 0.37 = **1.10 GB**, of
which the Python array/frame payload was **0.69 GB**, leaving 0.41 GB of
non-array live allocation — and miso-90 measured interpreter + numpy/pandas +
imports at ~0.12 GB. So C-side retention was **bounded above by ~0.29 GB**, not
the ~1.35 GB the hypothesis needed.

Post-fix it collapses further: `in_use` falls to **0.15 GB**, i.e. essentially
all of the pre-fix live arena was the one Python frame. **No "destroy the HiGHS
model object explicitly" work is warranted**, and the charter's secondary
(`mallinfo2`) branch is what settled it without a second solve-year.

## 7. The keeper does not reproduce on `main` — EXPECTED and already on record; quantified here

**This is not a new defect, and the first draft of this finding wrongly framed it
as one.** The miso-89 log entry already records it: the guard-corrected CAMPD
economic-layup extract (**755 windows / 3,630 GW-days reclassified 2023–25**,
merged as PR #2919) *"is committed and IS the envelope MISO now solves against,
so until this re-audit runs, the miso-88 keeper's registered numbers describe the
pre-adoption envelope and will not reproduce at HEAD."* The keeper's re-audit
against that envelope was attempted by miso-89 and **blocked on container RAM**.

What this lane adds is the **magnitude and a control** — i.e. how big the pending
re-audit's change is expected to be, measured rather than anticipated:

| | keeper | replay at HEAD |
|---|---|---|
| mean load-weighted price | $31.2238 | $30.7702 |
| ST_GAS | 17.508 TWh | 19.555 (**+2.047**) |
| import | 36.515 | 35.171 (−1.344) |
| CT_PEAKER | 14.470 | 13.309 (−1.160) |
| COAL_BIT | 50.762 | 51.862 (+1.100) |
| COAL_PRB | 121.903 | 120.821 (−1.082) |

Mean |Δprice| $0.456 on a $31 mean; **86.7 % of zone-hours differ**; total
energy 641.767 → 641.759 TWh.

**It is input drift, not nondeterminism — controlled.** Two identical invocations
at HEAD (`miso92_memtel`, `miso92_determ`) produce `max|diff| = 0` on every
column of both sidecars, and a third and fourth reproduce the same telemetry. The
solve is exactly deterministic; what moved is the committed outage envelope. The
direction is consistent with that cause — reclassifying economic-layup windows
changes measured availability, and the response is a merit-order shift within
thermal (**ST_GAS +2.05 TWh** against CT_PEAKER/COAL_PRB/import) rather than a
level shift, with total energy essentially conserved (641.767 → 641.759 TWh).

**No connection to `wefor_residual` is claimed.** ST_GAS is also the class C8
reports as grounded-above-budget forced, and the handoff flagged
`wefor_residual = None` as a possible latent double-count — but the CAMPD
envelope change is a sufficient and already-documented explanation, so reading
anything further into the direction would be exactly the kind of story this lane
exists to avoid.

**Operational consequence, still live:** until that re-audit runs, any
replay-based diagnosis of the MISO keeper measures the post-correction envelope,
not the keeper's registered numbers. The four probe bundles here are
post-correction and are treated as such — which is harmless for a memory
measurement, but would not be for a scoring one.

**This lane makes that blocked re-audit cheaper, though it does not unblock it.**
miso-89 reported the OOM at **15.9 GB RSS**, which is almost exactly this
session's measured 14.4 GB single-year peak **plus** the 1.53 GB cross-year
floor. Removing 0.53 GB of that floor takes the same arithmetic to ~15.4 GB —
a real reduction toward, but still above, a 15 GB box. **The staged
one-year-per-process `--reuse-solved` recipe remains required**; each of this
lane's single-year replays completed comfortably at 14.40–14.41 GB peak.

## 8. Instrument changes (all diagnostic; none can change dispatch)

* `_glibc_arena_gb()` in `run_calibration_full.py` — `mallinfo2` accounting
  (`arena` / `in_use` / `free_in_arena` / `mmapped` / `trim_top`). Added *before*
  the first read specifically so the charter's "small ndarray" branch would not
  cost a second solve-year to disambiguate; it is what exonerated HiGHS in §6.
* `cache_control.largest_retained_frames()` — the top retained pandas objects
  with shape and column list. A column list identifies a frame's producer on
  sight, which is what turned "0.59 GB of pandas somewhere" into a named line of
  code. Counts `Series` as well as `DataFrame`, for parity with
  `retained_footprint`.
* A recorded coverage fact, found by a **failing test** rather than assumed:
  DataFrames and Series are **GC-tracked**, so `gc.get_objects()` enumerates them
  directly and this reporter has **no running-locals blind spot** — unlike
  `retained_footprint`, whose blind spot is real for untracked bare ndarrays.
  That is exactly why `_dispf`, a running function's local, was visible at all.
  Pinned by test so the frame list can be trusted as complete.
* The telemetry's blanket `except` logged at **debug**, i.e. invisible in a normal
  run. Raised to `warning` with `exc_info`, plus an explicit warning when the
  frame list is empty while `retained_footprint` counted pandas objects. A
  diagnostic that fails open is the failure mode this instrument exists to avoid.

### Two process notes worth carrying forward

1. **A one-line `NameError` cost a full solve-year.** The `largest_retained_frames`
   import was reverted by a post-edit reformat; the debug-level `except` hid it,
   and the run completed "successfully" printing nothing. Verified that
   `ruff check --select F821 scripts/run_calibration_full.py` reproduces the
   error on the broken tree and passes on the fixed one. **The repo applies
   `ruff format` to committed Python but does not run `ruff check`**, so an
   undefined name reaches a solve. Same shape as miso-91's finding that
   `validate_parameters.py` is documented as a CI gate and is not one.
2. **Intermediate diagnoses should be labelled as such.** The empty frame list
   was first attributed to a `DataFrame`-vs-`Series` gap; that was wrong (the
   real cause was the `NameError`). The Series fix is independently correct and
   was kept, but the misattribution is recorded here and in the commit that
   corrected it rather than quietly overwritten.

## 9. What this does NOT claim

* **Not** a reduction in the 14.4 GB single-year peak (§3). The staged
  `--reuse-solved` recipe remains required for MISO on this box.
* **Not** a licence to enable cross-year warm start —
  `MARKET_SIM_WARMSTART_XYEAR` makes retention worse and is off for a
  correctness reason (`docs/cross-year-warmstart.md`).
* **Not** a calibration result. Four single-year probe bundles were produced;
  per rule 16 a one-year solve is a throwaway diagnostic and **must not be
  registered** as a keeper, so none was registered and none is committed. Stated
  explicitly rather than silently skipped. No scoring criterion moved, so no
  ledger budget was consumed (it remains 3/3).
* **Not** a diagnosis of §7. The reproducibility drift is reported with its
  control and left for a dedicated lane.

## 10. Charter deviation, declared

The charter fenced this lane with *"will not propose a memory fix; the fix is
chartered from the measurement, not alongside it."* That fence exists to stop a
fix driven by a **story** — the failure mode of the three preceding sessions.
The `del` here is the opposite case: the measurement named a specific live object
at a specific line, the fix is its removal, and the result was **verified by
re-running the same telemetry** (1.53 → 1.00 GB) with **bit-identical dispatch**.
Recording the deviation rather than re-writing the fence to permit it: a reader
should be able to see that the constraint was overrun deliberately and why.
