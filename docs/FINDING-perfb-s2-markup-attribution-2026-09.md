# FINDING — PERF-B session 2: the `markup` phase is **not a phase**, and three separate accounting defects are hiding inside it

**Session `claude/perfb-s2-markup-attribution-3coy7b`, 2026-09-04.** WS3-next
charter item, board **X-3 / L-8 / queue W-4**; PERF-B resumed under owner ruling
**R-V**. Byte-gated: `atol=rtol=0` against the stage-0 goldens, no numeric change
to any keeper output. **No `ScenarioConfig` default changed, no keeper shard,
marker, matrix shard, registry or workflow touched, nothing promoted** — ERCOT,
NEISO and PJM keepers are frozen under R-V and this lane changes none of them.
**No optimization was applied.** The deliverable is attribution plus the charter
that ranks the fixes.

---

## 0. Headline

**95–96 % of `markup` is LP build-and-solve time — 92–94 % of it from an EARLIER
solve pass — and 0.03–0.05 % is `compute_monthly_markup`.** ERCOT keeper, 2023
(all three years, and NEISO, in §4):

| component | s | share of `markup` | what it is |
|---|---:|---:|---|
| `prior_solve` | **693.9** | **91.1 %** | the ercot-221 **pass-1** P0 + P1 `h.run()` seconds — real solver time, mislabelled |
| `p0_build` | 22.8 | 3.0 % | the two P0 matrix builds `_build` never accounted for |
| `p1_post` | 17.0 | 2.2 % | P1 `getSolution` + `DispatchResult` assembly |
| `p0_post` | 14.7 | 1.9 % | the same for P0 |
| `prior_build` | 7.6 | 1.0 % | pass-1's P1 matrix build |
| `seam` | 5.4 | 0.7 % | bid assembly + the floor/kwargs hooks |
| **`markup`** | **0.4** | **0.05 %** | **`compute_monthly_markup` — the phase the field is named after** |
| `setup` / `tail` / `other` | 0.0 | 0.0 % | basis seam (off under the replay pin), call edges |
| **total** | **761.9** | 100 % | |

**So the hand-back's "~50× the phase PERF-B optimized" is true and its
implication is not.** The window is not overhead around a cheap arithmetic
step — it is **a second whole LP pass** that the ercot-221 adaptive-expectation
offer requires, booked under a name that says otherwise. ERCOT solves **four**
LPs per year, and the residual hides two of them.

**NEISO is the control and it behaves exactly as the mechanism predicts:** one
pass, a warm P1, no bridge — `markup` **3.6–3.7 s/yr**, of which 3.5 s is the
two passes' solution marshalling and 0.1 s is `compute_monthly_markup`. The 200×
gap between the two ISOs is not a difference in "markup"; it is one extra solve
pass and one extra cold rebuild.

**The obvious fix is refuted, by measurement.** Arming the in-place P1 refloor
(`MARKET_SIM_P1_FLOOR_INPLACE=1`) — the memo-gated flip — would buy ERCOT
**nothing**. The new routing diagnostic says so in the run's own log:

```
P1 route: COLD REBUILD on a floored fleet — MARKET_SIM_P1_FLOOR_INPLACE off
(default); would have been DECLINED anyway (availability changed and feeds a
row) (availability_changed=True, availability_feeds_rows=True)
```

The ERCOT gas-commitment bridge **raises availability** where its floor would
exceed `pmax * availability`, and ERCOT runs the reserve co-opt, so availability
feeds an LP row and `refloor_thermal_inplace` declines by construction
(`model/lp/inplace_floor.py:94-100`). **Do not spend the owner memo on this
flip.**

**What is actually removable.** Two things, neither of them "markup":

* **The adaptive pass's P0.** Every argument reaching it is the *same object* as
  pass-1's — only `p1_storage_discharge_cost` differs, and `run_energy_solve`
  applies that to P1 only — so pass 2 cold-solves a bit-identical LP with a
  bit-identical objective and discards the answer. **379 / 463 / 463 s/yr =
  23 / 25 / 23 % of the ERCOT year** (it is `solve_p0` plus that pass's build,
  not part of `markup` at all — which is the point of fixing the accounting
  first).
* **The whole second pass, in a year where it changes nothing.** ERCOT **2025**
  has 0 pass-1 spike days and `P_hat` max 0.000, and the keeper leaves pass 1's
  discharge cost at the model default — so the second pass's objective is
  (very probably, §4.4) elementwise identical to the first's, and its **926 s —
  half the year** — buys a bit-identical answer.

Both are ranked, with their byte-identity arguments and their guards, in
`docs/handoffs/perfb-session2-markup-charter-2026-09.md`.

---

## 1. What `markup` actually is

`markup` is not measured anywhere. Both orchestrators derive it as a **residual**:

```python
# src/market_sim/runner.py (forecast)          scripts/run_calibration_full.py (backcast)
_solve_p0 = energy_solve.r0.solve_time         _solve_p0 = _ti["solve_p0_s"]
_solve_p1 = energy_solve.p1.solve_time         _solve_p1 = _ti["solve_p1_s"]
_build    = energy_solve.p1.build_time         _build    = _ti["build_s"]
_energy_s = _t_post_solve - _t_pre_solve       _energy   = _ti["energy_solve_s"]
_markup_s = max(0.0, _energy_s - _build - _solve_p0 - _solve_p1)
```

The two subtrahends are **much narrower than their names suggest**
(`src/market_sim/model/lp/model.py`):

| field | what it actually times | what it does NOT cover |
|---|---|---|
| `DispatchResult.solve_time` | `h.run()` **only** (`model.py:1082-1084`) | the objective-vector build + `changeColsCost` before it, and the whole `getSolution()` marshalling + `DispatchResult` assembly after it (`:1093-1420`) |
| `DispatchResult.build_time` | `DispatchModel.__init__` **only** (`:188` → `:996`) | any **second** model built in the same year |

So the residual absorbs every non-`h.run()`, non-`__init__` cost of
`pipeline/solve.py::run_energy_solve` — and, as it turns out, considerably more
than that. The director's hypothesis (*"a second full matrix build is being
booked as markup"*) is **confirmed in substance and corrected in detail**, and
two further defects sit beside it.

### 1.1 Defect A — a whole matrix build is unaccounted whenever P1 cold-rebuilds

`_build` reads **`p1.build_time`**. On the ordinary warm path P1 re-solves the
*same* model, so `p1.build_time` *is* `r0.build_time` and the one build is
subtracted correctly. But when a P1-native floor bridge replaces the fleet
(`p1_fleet_prep` returns a floored `FleetArrays`) and the in-place refloor is not
taken, `run_energy_solve` builds a **second** `DispatchModel`; `p1.build_time`
then names the **second** build, and the **first** (the P0 model, built at
`solve.py:259`) is left inside the residual with nothing subtracting it.

It is the **P0** build that is misbooked, not the P1 one — the opposite of the
obvious reading, and it matters for the fix: the cost is not "the rebuild", it is
"one build too many, plus a lost warm start".

**ERCOT's keeper arms exactly this path.** `ercot_gas_commitment_bridge = True`
in `results/calibration/ercot234_eastex_identity/meta.json`, so
`p1_fleet_arrays is not fleet_arrays`, and `MARKET_SIM_P1_FLOOR_INPLACE` is
`"0"` by default, so the in-place branch is never entered. **NEISO's keeper arms
no bridge** (`p1_fleet_prep` is `None`), so its P1 is warm and this defect is
inert there — which is why NEISO is the control grain in §4.

### 1.2 Defect B — on a multi-pass year, ALL BUT THE LAST PASS is inside the residual

A year is not always one energy solve. `scripts/run_calibration.py` calls
`run_energy_solve` at **four** sites, one of them inside a loop (cited by
mechanism, not line — see §8 on why a line anchor into these files rots):

* the **pass-1** solve;
* the **ercot-221 adaptive-expectation** second P1 pass — its own log line says
  *"re-solving P1 (pass 2, THE scored pass)"*;
* the **ercot-230 fixed-point** iteration, inside a loop
  (`ercot_adaptive_fixed_point`; **not** armed on the current ERCOT keeper);
* the **caiso-205** adaptive leg (`caiso_storage_adaptive_expectation`).

`_t_solve_start` is taken once, before the first; `_t_solve_end` is re-taken
after each phase. So `energy_solve_s` spans **every** pass, while `build_s`,
`solve_p0_s` and `solve_p1_s` are read from the **final** `EnergySolveResult`
only. Every earlier pass's entire matrix build **and both HiGHS runs** therefore
land in `markup`. On the ERCOT keeper — which arms ercot-221 — this is the
largest single term in the window, and it is neither a build nor a marshalling
cost but *solver time mislabelled*.

This also explains the stage-0 capture finding's otherwise-puzzling count of
**"12 solves (4 × 3 yr)"** for ERCOT against NEISO's "6 (P0 cold + P1 warm × 3
yr)": ERCOT runs two passes per year, each with a cold P0 and a cold P1.

### 1.3 Defect C — the P0/P1 solution marshalling is nobody's phase

`solve_time` stops at `h.run()`. Everything the LP returns — `getSolution()`, the
full `col_dual` conversion (highspy 1.14 boxes a vector attribute into a Python
list on **every** access, ~0.8 GB at ~25 M columns per the in-file note), the
`col_value` / `row_dual` conversions, and ~330 lines of `DispatchResult`
assembly — is charged to `markup`, twice per pass. Unlike A and B this is not a
mislabelling of work that would exist anyway: **the P0 pass marshals a full
result set whose only consumers are `r0.dispatch` (run lengths), the P0-conditioned
bid hooks and the floor detector.**

---

## 2. The instrumentation

Six interior sub-timers in `run_energy_solve`, plus a bounded per-pass log so a
multi-pass year is not lost, surfaced through `pipeline/timing.py` on the same
contract `results_write_parts` already uses:

| component | what it covers |
|---|---|
| `setup` | SWCAP clip, P0 `DispatchModel` construction **excluding its matrix build**, cross-year/disk basis seed + apply |
| `p0_build` | **the matrix build `_build` does not account for** — nonzero exactly when P1 cold-rebuilds (defect A) |
| `p0_post` | P0 objective build + `changeColsCost`, `getSolution`, the whole `DispatchResult` extraction (defect C) |
| `markup` | `compute_monthly_markup` — the phase the field is *named* for |
| `seam` | bid assembly (markup add, additive/P0-conditioned adjusts, bid-max reconcile, SWCAP) and the floor/kwargs hooks incl. any in-place refloor |
| `p1_post` | the same as `p0_post` for P1, plus (cold path, cross-year gate armed) the pre-rebuild basis export |
| `tail` | cross-year basis export (`getBasis`) + the disposable NPZ persist |
| `prior_build` / `prior_solve` | **every pass but the last**: its whole build, and its two HiGHS runs (defect B) |
| `other` | the remainder — the orchestrator's own call edges and the between-pass adaptive machinery (spike detection, `P_hat`, floor assembly) |

**The components sum to the reported `markup` exactly.** The arithmetic is not
obvious because of `build_time`, so it is pinned by test rather than asserted:
`tests/regression/test_pipeline_timing.py::TestMarkupPartsAreExhaustive` closes
the identity on the warm-P1 path, the cold-P1 rebuild path and
`MARKET_SIM_WARMSTART=0`; `::TestMultiPassAggregation` closes it at one, two and
four passes.

**Defensive by construction (after §7.1 made the case).** Every build/solve
read goes through `getattr(..., 0.0)` and the routing diagnostic is wrapped, so
a timing read cannot narrow `run_energy_solve`'s contract with the object it is
handed and a log line cannot break a solve. The per-pass log is a
`deque(maxlen=256)` drained by both orchestrators, so a caller that never drains
it cannot leak.

**Wire-format discipline.** The six frozen fields (`data_prep / solve_p0 /
markup / solve_p1 / results_write / total`) keep their exact spelling, order and
position. The new clause is rendered **before** the `results_write` clause, so a
parser anchored on `(results_write:` — or one reading that clause to
end-of-line — is unaffected; `tests/regression/test_pipeline_timing.py` pins
both readings.

### 2.1 One diagnostic added: the P1 route

Neither the P0→P1 branch nor `refloor_thermal_inplace` logged anything, so a run
could not say **from its own log** why P1 cold-rebuilt. It now does, separating
the two reasons — which need different remedies:

* `MARKET_SIM_P1_FLOOR_INPLACE` off (the default) — flippable, but only on
  warm-start-class evidence, which is memo-gated;
* the floored **availability changed** and feeds an LP row a P-column edit
  cannot reproduce — `refloor_thermal_inplace` would **decline even if flipped**
  (`model/lp/inplace_floor.py:94-100`), and ERCOT runs the reserve co-opt, so
  `availability_feeds_rows` is `True` there.

The line reports both facts, so the charter's ranking rests on a measurement
rather than on reading the bridge's source.

---

## 3. Timing-only — and how that is proven

Every edit is a `time.perf_counter()` read, a dict write, or an INFO log guarded
by `isEnabledFor`. No computation is added, removed or reordered; no
`ScenarioConfig` field exists or changed; the per-pass log is written by
`run_energy_solve` and read by nothing that solves.

**That argument is NOT the evidence — and §7.1 is the reason it must not be.**
The same reasoning would have told you the instrumentation was safe, and it took
30 tests red on a contract widening no production caller exercises. The evidence
is §5, and only §5.

---

## 4. Measurement

**Regime.** `scripts/capture_keeper_goldens.py --stage-tag perfb-s2-after`, one
ISO at a time, never concurrently (a second solve would both risk the 15 GB box
and distort the timing that is the deliverable). Determinism pinned by the tool:
`MARKET_SIM_HIGHS_THREADS=1`, `MARKET_SIM_WARMSTART=1`,
**`MARKET_SIM_WARMSTART_XYEAR=0`**. A 5 GiB swapfile was armed before the ERCOT
launch (documented ~12.5 GB peak on a 15 GB box); it was not materially used.

⚠️ **Two ways the calibration CLI's own regime differs, both named rather than
elided.** `run_calibration_full.py` defaults `MARKET_SIM_WARMSTART_XYEAR` **ON**,
so on a keeper CLI run (a) `tail` carries the previously documented ~10–16 s/yr
of `getBasis()` export, which reads 0.0 s here, and (b) the adaptive pass's P0
warm-starts from the previous pass's basis through the `xyear_cache` holder,
where here it cold-solves. Neither changes the composition below, but any lane
acting on it must measure in both regimes.

### 4.1 ERCOT keeper `2026-08-25-234-eastex-identity` (forward config, 2023-2025)

Six frozen fields, per year:

| year | data_prep | solve_p0 | **markup** | solve_p1 | results_write | total |
|---|---:|---:|---:|---:|---:|---:|
| 2023 | 87.7 | 372.8 | **761.9** | 393.9 | 9.5 | 1625.7 |
| 2024 | 29.2 | 456.7 | **899.6** | 448.0 | 11.0 | 1844.5 |
| 2025 | 33.1 | 457.2 | **987.2** | 490.9 | 10.2 | 1978.6 |

`markup` is **46.9 / 48.8 / 49.9 %** of the whole year — the hand-back's
"~50 % of the ERCOT keeper's whole year", reproduced. And the attribution:

| year | setup | p0_build | p0_post | markup | seam | p1_post | tail | prior_build | **prior_solve** | other | Σ | reported |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 0.0 | 22.8 | 14.7 | **0.4** | 5.4 | 17.0 | 0.0 | 7.6 | **693.9** | 0.0 | 761.8 | 761.9 |
| 2024 | 0.0 | 21.2 | 15.3 | **0.3** | 5.8 | 16.3 | 0.0 | 7.2 | **833.4** | 0.0 | 899.5 | 899.6 |
| 2025 | 0.0 | 18.7 | 15.3 | **0.3** | 4.4 | 15.7 | 0.0 | 6.7 | **926.0** | 0.0 | 987.1 | 987.2 |

(Σ differs from the reported field by ≤0.1 s — ten components each rendered at
one decimal. The identity itself is exact and is pinned by test, §2.)

**`prior_solve` is 91.1 / 92.6 / 93.8 % of `markup`.** `compute_monthly_markup`
— the phase the field is named for — is **0.4 / 0.3 / 0.3 s**, i.e. **0.05 % /
0.03 % / 0.03 %**.

**Why: ERCOT solves FOUR LPs per year.** From the run's own log, 2023:

```
Matrix build: 16.185s, Solve: 352.146s (cold)      <- pass 1 P0
P1 route: COLD REBUILD on a floored fleet — ...
Matrix build:  7.636s, Solve: 341.789s (cold)      <- pass 1 P1
ERCOT adaptive-expectation offer (2023): pass-1 model spike days 7, P_hat max
0.370, floor > vom in 768 of 1460 window hours; re-solving P1 (pass 2, THE
scored pass)
Matrix build:  6.589s, Solve: 372.776s (cold)      <- pass 2 P0
P1 route: COLD REBUILD on a floored fleet — ...
                                                    <- pass 2 P1 (the scored one)
```

Twelve solves across three years — exactly the count
`docs/FINDING-stage0-capture-neiso-ercot-2026-09.md` recorded as *"12 solves
(4 × 3 yr), all cold"* against NEISO's *"6 (P0 cold + P1 warm × 3 yr)"*, now
explained. `_build` / `solve_p0_s` / `solve_p1_s` are read from pass 2 only, so
pass 1's build and both of its HiGHS runs are the residual.

### 4.2 NEISO keeper `2026-08-17-neiso-99-joint-p1` — the control

One pass, no floor bridge (`p1_fleet_prep is None`), so P1 warm-solves the P0
model and neither defect A nor defect B can fire:

| year | **markup** | setup | p0_build | p0_post | markup | seam | p1_post | tail | other | total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2023 | **3.7** | 0.0 | 0.0 | 1.7 | 0.1 | 0.0 | 1.8 | 0.0 | 0.1 | 200.1 |
| 2024 | **3.6** | 0.0 | 0.0 | 1.7 | 0.1 | 0.0 | 1.8 | 0.0 | 0.1 | 129.9 |
| 2025 | **3.6** | 0.0 | 0.0 | 1.7 | 0.1 | 0.0 | 1.7 | 0.0 | 0.1 | 132.3 |

`p0_build` is **0.0** — the single build is correctly subtracted — and the whole
window is the two passes' solution marshalling (defect C) plus 0.1 s of
`compute_monthly_markup`. **The 200× ERCOT/NEISO gap in `markup` is not a
difference in markup. It is one extra solve pass and one extra cold rebuild.**

### 4.3 The in-place refloor: declined, and why (job 2's question)

The prompt asked, if the P1 rebuild dominates, whether the in-place path was
declined and *"the model's own reason, from its log"*. There was no such log
line; this session added one (§2.1). It reads, on **every** ERCOT pass of every
year:

```
P1 route: COLD REBUILD on a floored fleet — MARKET_SIM_P1_FLOOR_INPLACE off
(default); would have been DECLINED anyway (availability changed and feeds a
row) (availability_changed=True, availability_feeds_rows=True)
```

Two independent reasons, and the second is the binding one:

1. `MARKET_SIM_P1_FLOOR_INPLACE` is `"0"` by default, so the branch is not
   entered at all.
2. **Even if it were flipped, `refloor_thermal_inplace` would decline.** The
   ERCOT gas-commitment bridge raises `availability` where its floor would
   otherwise exceed `pmax * availability`, and ERCOT runs the reserve co-opt, so
   availability feeds an LP row that a P-column bound edit cannot reproduce
   (`model/lp/inplace_floor.py:94-100`).

**Warm start does not apply on this path either way**: P1 cold-solves a second
model. Both ERCOT P1 solves per year are logged `(cold)`.

**Consequence for the charter: the memo-gated flip is not the fix.** It is worth
0 s on ERCOT.

### 4.4 The 2025 case — the second pass may be a pure no-op

The adaptive log for the three years:

| year | pass-1 model spike days | `P_hat` max | floor > vom in window hours | `prior_solve` |
|---|---:|---:|---:|---:|
| 2023 | 7 | 0.370 | 768 / 1460 | 693.9 s |
| 2024 | 3 | 0.176 | 563 / 1460 | 833.4 s |
| **2025** | **0** | **0.000** | **0 / 1460** | **926.0 s** |

In 2025 the adaptive floor never rises above the storage VOM anywhere in its
window, and the keeper resolves `ercot_exhaustion_expectation = False` /
`ercot_storage_reservation_offer = False`, so pass 1's
`p1_storage_discharge_cost` is `None` — i.e. the model's default, which
`run_calibration.py:5057` sets to `storage.vom`, the same array pass 2's
`max(vom, floor)` reduces to. **On that reading, ERCOT 2025's entire second
pass — 926 s, half the year — re-solves an LP identical to the first and
produces a bit-identical answer.**

⚠️ **Stated as strongly indicated, not proved.** The log's "0 of 1460" compares
the floor against `float(_vom_s.max())`, a scalar over units, so it does not by
itself establish elementwise `floor <= vom` for a unit whose VOM is below the
fleet max. The exact test is an elementwise `np.array_equal` of the two passes'
resolved discharge-cost arrays — which is precisely the guard the charter's
first candidate is built on, and 2025 is its motivating case.

---

## 5. Byte-identity — **PROVEN, at `atol=rtol=0`, on both ERCOT configs and NEISO**

**The claim is made only from the golden comparison output below, never from
"no numeric code changed".**

### 5.0 What was captured, and at which tree

| stage tag | tree | configs / solve-years | purpose |
|---|---|---|---|
| `perfb-s2-after` | `5b1c282e` (instrumentation complete) | NEISO 2023-25, ERCOT fwd 2023-25, ERCOT carve-out 2023 — **7 solve-years** | compare against the committed stage-0 goldens |
| `perfb-s2-before` | **merge-base `8a18e9e1`** — the eight source files reverted in place, `git diff --quiet` verified against the base before and against branch HEAD after | NEISO 2023-25, ERCOT carve-out 2023 | *same tree except this session's diff* |
| `perfb-s2-final` | `4abb8598` — **the shipped tree**, after the §7.1 defensive-read repair | NEISO 2023-25, ERCOT carve-out 2023 | re-establish the control on the bytes that actually ship |

The ERCOT **forward** three-year config was captured once (`perfb-s2-after`, ≈95
min of solve); the carve-out is its one-year control and exercises the identical
ERCOT path — two adaptive passes, floored fleet, cold P1.

### 5.1 Against the committed stage-0 goldens

`perfb-s2-after` compared against the committed `perfb-stage0` manifest — 7 solve-years across 3 configs, all against
the ISOs' **current** designated keepers (`check_golden_manifest.py` exit **0**,
both entries read *"provenance run registered, golden CURRENT"*).

**What compared clean immediately:**

| config | files byte-identical | files differing |
|---|---|---|
| NEISO (2023-25) | **7 / 10** | the 3 `dispatch/<year>_P1.parquet` |
| ERCOT forward (2023-25) | **7 / 10** | the 3 `dispatch/<year>_P1.parquet` |
| ERCOT carve-out (2023) | **5 / 6** | the 1 `dispatch/2023_P1.parquet` |

**`system.parquet` — the zonal prices and totals — is byte-identical in all
three configs.** So are `flows.parquet`, `storage.parquet`, `btm.parquet` and
every `dispatch/<year>_P1_fleet.parquet`. A moved LP solution cannot leave those
untouched, which is the first-order reason the remaining difference was not a
solve change.

### 5.2 The difference is a COLUMN `main` added, and removing it reproduces the golden EXACTLY

The manifest's `_content_hash` hashes *sorted column names + their contents*, so
an added column changes it. Commit **`e5639ca1`** (2026-09-03 02:29, "Add the
class_band_hourly dispatch sidecar") added a **`klass_base`** column to the
dispatch frame — **additions only**, 100 lines, no deletions. Every stage-0
entry compared against predates it: NEISO `2026-09-01T03:06Z`, ERCOT
`2026-09-01T04:26Z`, carve-out `2026-09-02T03:50Z`.

Re-running the manifest's own hash function on this session's captured frames
with `klass_base` dropped:

| config / year | after − `klass_base` | stage-0 golden | |
|---|---|---|---|
| NEISO 2023 | `ff19a36bc820` | `ff19a36bc820` | **MATCH** |
| NEISO 2024 | `6fb03425d290` | `6fb03425d290` | **MATCH** |
| NEISO 2025 | `c0807d6a08ce` | `c0807d6a08ce` | **MATCH** |
| ERCOT 2023 | `7185a39ceec0ad5a` | `7185a39ceec0ad5a` | **MATCH** |
| ERCOT 2024 | `7904e2a3f31053d3` | `7904e2a3f31053d3` | **MATCH** |
| ERCOT 2025 | `ecff88e6fa7a8191` | `ecff88e6fa7a8191` | **MATCH** |
| ERCOT carve-out 2023 | `fc2273e9ea46d4b7` | `fc2273e9ea46d4b7` | **MATCH** |

**7 of 7.** Every other column of the frame — `year, pass, unit_id, plant_code,
klass, fuel, supply, zone, hour, mw, lmp` — is bit-identical to the golden, in
every year of every config. **So every value the stage-0 goldens contain is
reproduced exactly; the only delta is a diagnostic column `main` grew after they
were taken.**

The method was control-tested before it was trusted: a plain read/write
round-trip of a captured parquet is byte-stable in this container, and the
hashes above are computed with `capture_keeper_goldens._content_hash`'s own
arithmetic, not a raw-file digest (a raw-file digest does **not** reproduce, and
that is a property of parquet metadata, not of the data — the tool's docstring
says so).

### 5.3 Merge-base controls — the decisive instrument

A second NEISO capture was run at the branch's **merge-base** (`8a18e9e1`, this
session's own source files reverted to that commit and restored afterwards) as
stage tag `perfb-s2-before`, so the comparison is *"same tree except this
session's diff"* rather than *"HEAD vs a two-day-old tree"*.

**Both controls BYTE-IDENTICAL, no adjustment of any kind — NEISO 10/10 files
and the ERCOT 2023 carve-out 6/6.** The carve-out matters because it exercises
the *ERCOT* path this session's instrumentation touches hardest: two adaptive
passes, a floored fleet, a cold P1 rebuild and the `prior_build`/`prior_solve`
aggregation. NEISO's three
`dispatch/<year>_P1.parquet` (with `klass_base`), all three
`*_P1_fleet.parquet`, `system`, `flows`, `storage`, `btm` — and the carve-out's
six likewise.

Run through the repo's own designated instrument rather than an ad-hoc
comparator — `scripts/regression_gate.py --mode byte --atol 0 --rtol 0`, which
the capture tool's docstring names as *"the authoritative byte-identity check
between two golden sets"*:

```
========================================================================
REGRESSION GATE  (mode=byte, atol=0.0, rtol=0.0)
========================================================================
[1] Golden bundle diff
    PASS  ERCOT__carveout-2023: 5 files, 22 numeric columns within tolerance (atol=0.0, rtol=0.0)
    PASS  NEISO: 9 files, 32 numeric columns within tolerance (atol=0.0, rtol=0.0)

[2] Reshuffle localization (informational)
  ERCOT__carveout-2023 2023: total annual gen  cold 446065.4 GWh  warm 446065.4 GWh  Δ +0.0000 GWh
  ERCOT__carveout-2023 2023: Σ|hourly Δ| (gross reshuffle): 0.0 GWh = 0.000% of total gen
  NEISO 2023: total annual gen  cold 96984.5 GWh  warm 96984.5 GWh  Δ +0.0000 GWh
  NEISO 2023: Σ|hourly Δ| (gross reshuffle): 0.0 GWh = 0.000% of total gen
  NEISO 2024: ... Δ +0.0000 GWh ... 0.0 GWh = 0.000% of total gen
  NEISO 2025: ... Δ +0.0000 GWh ... 0.0 GWh = 0.000% of total gen
========================================================================
  PASS  golden-diff
========================================================================
RESULT: PASS
```

That is `perfb-s2-before` (merge-base) against **`perfb-s2-final` (the shipped
tree, `4abb8598`)** — so the gate is green on the bytes that ship, not on an
intermediate commit. The identical gate against `perfb-s2-after` (the
pre-repair tree, `5b1c282e`) also passed on both configs; its only non-PASS line
was the coverage message below.

Not merely "within tolerance": the reshuffle localization reads **exactly
0.000 %**, so not one hour of one plant moved.

⚠️ **Two honest caveats.** (a) The three-year ERCOT **forward** config has no
merge-base twin — re-solving it a second time is ≈95 min for a control the
carve-out already provides at one year on the identical code path. Run against
`perfb-s2-after` (which contains it) the gate reports it as a **coverage**
message, `ISOs only in after: ['ERCOT']`, and every config present on both sides
compared PASS; the forward config's own evidence is §5.2's 3-for-3 stage-0
reproduction. (b) The manifest's
`provenance.git_sha` reads the same branch HEAD for both captures, because the
control reverted the **eight source files** to merge-base content in place
rather than checking out the commit; the revert and the restore are each
verified with `git diff --quiet` against `8a18e9e1` and against branch HEAD
respectively.

### 5.4 Two main-drift facts recorded on the way

* **`scenario_config` drift on the ERCOT capture: 2 fields** —
  `ccs_retrofit_capex_kw`, `fixed_om_gas_cc_ccs`, the owner-authorized capx-D41
  default advance (`11af6f1c`). Reported by the tool, not failed; both are
  capacity-evolution constants with no backcast-dispatch path, and the
  byte-identity above is the evidence that they did not reach one. Fidelity
  oracle **PASS** (270 recorded flags replayed identically).
* **`e5639ca1`'s own comment says the frame it added the column to "is
  gitignored anyway".** It is not: it is `dispatch/<year>_<label>.parquet`, one
  of the ten files every golden manifest hashes. Harmless — the column is
  additive and this section is the proof — but the next lane that reads that
  comment should know it understates the frame's reach.

---

## 6. X-4 — the import-time environment pins (taken)

`docs/FINDING-fast-tier-repair-2026-09.md` §7.6 routed this as *"a small charter
question, not a repair this lane needed"*. Taken here.

**What it was.** `scripts/capture_keeper_goldens.py` applied `DETERMINISM_ENV`
(`MARKET_SIM_HIGHS_THREADS=1`, the WARMSTART pair) to `os.environ` at **module
scope**. Right for its own CLI process, where the pin must precede any solve.
Executed inside pytest — `tests/scoring/test_golden_manifest_provenance.py`
loads it by path three times — it leaked into the whole process, and HiGHS then
refused every later LP whose `threads` differed from the already-initialized
**process-global** scheduler (`model status 'Not Set'`): 203 LP tests in a serial
run, 24–79 in whichever xdist worker drew the file. Scheduling-dependent, hence
a latent CI red, and the object behind every inflated local fast-tier count the
audit program has recorded. §4b repaired the consuming test by snapshotting the
environment around its loads; the scripts themselves were left alone.

**What changed.** Both scripts now apply the pin through
`pin_determinism_env()`, called at every entry that can reach a solve:

| script | entries that pin | why not import time |
|---|---|---|
| `capture_keeper_goldens.py` | `main()`, and `capture_one()` **ahead of its deferred heavy imports** (the ordering the import-time pin used to guarantee) | a by-path load must not poison the loading process; a programmatic `capture_one` must not lose determinism |
| `replay_keeper.py` | `main()` — the module's only solve entry | `scripts/knob_jacobian.py` imports this module for `build_kwargs` and inherited the pin silently |

**No CLI behaviour changes.** Every `MARKET_SIM_*` read in the solve core is at
call time, not import time (`pipeline/solve.py:258/264/…`,
`model/lp/model.py:612`), so pinning at the top of `main()` reaches every solve
exactly as before. `replay_keeper`'s pinned value additionally *equals*
`pipeline/solve.py`'s own default, so it is defensive either way. Both CLIs were
smoke-tested (`--list-configs`, `--help`).

**Regression test** (`tests/regression/test_script_import_env_hygiene.py`): a
by-path `exec_module` with **no** environment guard leaves `os.environ`
byte-identical for both scripts; and `pin_determinism_env()` still applies the
declared values, is called from both `main()`s, and — for the capture tool —
precedes `capture_one`'s deferred `solve_and_persist` import.

**Scope check (the prompt's "skip if it widens the PR"):** 52 lines across the
two scripts, plus one new test file. Kept.

---

## 7. Fast tier — and the regression it caught

Run locally with **CI's own command**, exit code captured directly into a file
rather than through a pipe:

```
.venv/bin/python -m pytest -n 2 -m "not slow and not integration and not fulldata"
```

### 7.1 First run — 30 failures, and they were MINE

```
30 failed, 7859 passed, 34 skipped, 2 xfailed, 23 warnings in 388.21s
PYTEST_EXIT=1
```

Twenty-eight in `tests/unit/pipeline/test_runner.py`, two in
`tests/unit/results/test_matrix.py`, every one of them:

```
AttributeError: '_CapturingDispatchModel' object has no attribute 'build_time'
```

**Root cause, and it is this lane's.** `run_energy_solve`'s contract with the
object it is handed was `solve()` / `apply_cross_year_basis()` /
`export_cross_year_basis()` / `storage_discharge_cost`. Reading
`model.build_time` at construction — for the `p0_build` component — silently
widened it, and the tests' `_CapturingDispatchModel` double implements `solve`
and nothing else.

**Repair.** Every build/solve timing read now goes through `getattr(..., 0.0)`,
and the P1 routing diagnostic (which reads model internals a stand-in need not
implement) is wrapped so it degrades to a `debug` line rather than raising.
**A timing read may not narrow a contract, and a log line may never break a
solve.** Numerically inert on every real path — `DispatchModel` and
`DispatchResult` both carry the attributes, so the same floats are read.

*This is exactly what the tier is for, and it is recorded at full size rather
than quietly fixed:* the instrumentation was "provably additive" by inspection
and still took 30 tests red, because the contract it widened is one no
production caller exercises.

### 7.2 Second run — the shipped tree

```
1 failed, 7888 passed, 34 skipped, 2 xfailed, 23 warnings in 435.38s (0:07:15)
PYTEST_EXIT=1
```

**Zero regressions: the 30 are gone and nothing new appeared** (run 1 selected
7,859 + 30 = 7,889; run 2 selects 7,888 + 1 = 7,889 — the same population).

**The one failure is a known `main`-content failure, not this lane's.**
`tests/unit/data/test_egrid_identity_heat_rates.py::TestCommittedArtifact::test_single_row_and_loyo_envelope`,
`AssertionError: 2 != 1`. It is the nyiso-186 landing (`2ba0a29b`, merged as
PR #4693 → **`8a18e9e1`, this branch's own merge-base**): the identity derive
re-derived `egrid_identity_heat_rates_NYISO.csv` to add the merged-identity row
(57664 ↔ eGRID 55375, the Astoria Energy split) without updating the test that
asserts `len(df) == 1`. **The audit board's Y-4 lane recorded it this morning at
that same pin, and routed the fix to the nyiso-186 lane.** Verified against
interest here rather than asserted: this branch's entire diff vs `8a18e9e1` is
eleven files, **none** of them the artifact or the test —

```
docs/handoffs/perf-recheck-2026-08.md      src/market_sim/pipeline/__init__.py
scripts/capture_keeper_goldens.py          src/market_sim/pipeline/solve.py
scripts/replay_keeper.py                   src/market_sim/pipeline/timing.py
scripts/run_calibration.py                 src/market_sim/runner.py
scripts/run_calibration_full.py            tests/regression/test_pipeline_timing.py
                                           tests/regression/test_script_import_env_hygiene.py
```

— and the test fails standalone on the untouched artifact in 0.07 s.

---

## 8. Session-1 residue

The board's **L-7** re-derived PERF-B session 1's four charter items as **all
CLOSED**, with *"the only repair owed"* being one drifted citation. All three
named items re-verified against source at this session's HEAD:

| item | state | verified at HEAD |
|---|---|---|
| `ci.yml` checkout | **CLOSED** | 21 `sparse-checkout` blocks across 10 jobs; the `fast-tests` job (`.github/workflows/ci.yml:415`) carries `timeout-minutes: 20` (`:418`) and runs CI's own command at `:537`. Unchanged since #3964. |
| basis LUT | **CLOSED** | `_BASIS_STATUS_OBJS = [highspy.HighsBasisStatus(i) for i in range(5)]` at `model/lp/model.py:43`, indexed at **`:1523-1524`**. ⚠️ L-7 cited `:1501-1502` — the anchor has drifted 22 lines. Substance unchanged. |
| `scenarios.py` warm-start citation | **REPAIRED** | ⚠️ It had drifted **again**. `perf-recheck-2026-08.md` cited `:13606`; L-7 re-pinned it `:13825`; `ScenarioConfig.forecast_xyear_warmstart: bool = True` is at **`:14528`** today. Re-pinned to the **symbol**, with the line stamped and dated. |

**The pattern is the point, not the three instances.** Two of the three items in
this residue are line-anchor rot into `scenarios.py` / `model.py`, and the
board's own `check_mechanism_matrix` anchor tax (L-11, *"a standing tax on a
heavily-crossed file"*) is a third instance of the same failure mode. **A line
number into a file this heavily crossed is not a citation, it is a decaying
pointer.** The repair applied here — cite the symbol, stamp the line with the
sha and date — is the cheap general remedy and is recommended for the next doc
lane rather than another round of digit-chasing.

**Two more drifted citations found and NOT edited.**
`docs/handoffs/perf-a-warmstart-decision-memo-2026-08.md` cites
`scenarios.py:11646` (twice) and `:11644` for the same field and its guard
comment; both are stale by the same drift. That memo is an **owner-signed**
artifact, so this lane reports rather than amends it. The correct current
anchors are the field at `:14528` and the guard comment immediately above it.

**A standalone-only failure, recorded so it is not mistaken for a tier
failure.** `tests/unit/results/test_export.py::TestExportScenarioJson` fails 4
tests when that file is run **alone** in this container — confirmed pre-existing
by `git stash` on clean `main` content, where the identical 4 fail. It appears
in **neither** fast-tier run (§7): 0 occurrences in both logs. So it is a
fixture-ordering artifact of running the file in isolation, not a tier failure
and not this lane's. (nyiso-177's own commit message records the same 4 as
pre-existing, attributed to a missing confirmed-retirements clean partition.)

---

## 9. Gates run, and two reds that are not this lane's

| gate | exit | note |
|---|---|---|
| `scripts/regression_gate.py --mode byte --atol 0 --rtol 0` (merge-base → shipped tree) | **0 · PASS** | §5.3 |
| `scripts/check_golden_manifest.py` | **0 · OK** | 43 manifests / 76 entries; the new `perfb-s2-*` entries read *"provenance run registered, golden CURRENT"* |
| `scripts/check_mechanism_matrix.py` | **0 · OK** | no `ScenarioConfig` field added, no mechanism, no run registered, no calibration CLI flag — rule 28 duties do not attach |
| Fast tier (CI's command) | 1 | one failure, `main`-content, §7.2 |
| `scripts/audit_keepers.py --check` | **FAIL: 1** | **not this lane's** — NYISO E11 on `2026-09-04-nyiso-185-family-hr` (`fossil_announced_exits_enabled` False → True undeclared). Recorded on the audit board's v25 records entry this morning; this branch edits no keeper shard. |

**No keeper shard, marker, matrix shard, registry sidecar, dashboard file,
`program-status.json`, freeze file or workflow was touched, and nothing was
promoted.** The branch's whole diff against its merge-base is the eleven files
listed in §7.2.

---

## 10. What is NOT claimed

* **No speed-up was delivered.** This lane measured and did not optimize, as
  chartered. The candidates and their ranking are in
  `docs/handoffs/perfb-session2-markup-charter-2026-09.md`.
* **The `markup` numbers are this host's**, single-threaded HiGHS on a 15 GB
  box, and the audit board has separately measured cross-run walls varying up to
  ±35 % here. The **composition** is the result; the absolute seconds are not a
  benchmark. Session 1's ERCOT arms read `markup` 471–601 s where this session
  reads 762–987 s — the shares are what reproduce, not the walls.
* **The measured regime is the goldens/replay pin**, not the calibration CLI's
  (§4). Under the CLI, `tail` carries the export cost and the adaptive pass's P0
  warm-starts from the prior pass's basis; neither changes the composition, and
  both are named so a lane acting on this measures both.
* **§4.4's 2025 no-op reading is "strongly indicated", not proved.** The exact
  test is an elementwise array comparison, which is the guard the charter's
  first candidate is built on.
