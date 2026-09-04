# WS3-NEXT CHARTER — the `markup` phase, attributed

**Written by PERF-B session 2 (`claude/perfb-s2-markup-attribution-3coy7b`,
2026-09-04)** to discharge board **L-8 / queue W-4**: *"no prompt is issued and
none should be until WS3's next charter is written — this is the measurement
that charter should open from."* It opens from the measurement.

Evidence: `docs/FINDING-perfb-s2-markup-attribution-2026-09.md`.

**Standing constraints this charter inherits and does not relax.** Keepers
ERCOT / NEISO / PJM are **FROZEN** (R-V): no lane chartered here changes a
config, promotes anything, or edits a keeper shard, marker, matrix shard or
workflow. Every candidate below is byte-gated at `atol=rtol=0` against the
stage-0 goldens. Rule 27 `[R-PUSH]` applies to every file touched; the
`MARKET_SIM_P1_FLOOR_INPLACE` flip is **memo-gated** (plan §6) and is proposed
here, never flipped.

---

## 1. The attribution

`markup` is not a phase. Both orchestrators derive it as
`energy_solve - build - solve_p0 - solve_p1`, where `solve_time` covers only
`h.run()` and `build_time` covers only ONE `DispatchModel.__init__`. Measured
with per-component sub-timers that sum to the reported field exactly (ERCOT
keeper `2026-08-25-234-eastex-identity`, 2023; NEISO keeper
`2026-08-17-neiso-99-joint-p1`; `MARKET_SIM_HIGHS_THREADS=1`,
`MARKET_SIM_WARMSTART_XYEAR=0`):

| component | ERCOT 2023 (s) | share | NEISO 2023 (s) | what it is |
|---|---:|---:|---:|---|
| `prior_solve` | **693.9** | **91.1 %** | — | the ercot-221 **pass-1** P0 + P1 `h.run()` seconds |
| `p0_build` | 22.8 | 3.0 % | 0.0 | P0 matrix builds `_build` never accounts for |
| `p1_post` | 17.0 | 2.2 % | 1.8 | P1 `getSolution` + `DispatchResult` assembly |
| `p0_post` | 14.7 | 1.9 % | 1.7 | the same for P0 |
| `prior_build` | 7.6 | 1.0 % | — | pass-1's P1 matrix build |
| `seam` | 5.4 | 0.7 % | 0.0 | bid assembly + floor/kwargs hooks |
| **`markup`** | **0.4** | **0.05 %** | **0.1** | **`compute_monthly_markup`** |
| `setup` / `tail` / `other` | 0.0 | 0.0 % | 0.1 | basis seam (off under the pin), call edges |
| **reported `markup`** | **761.9** | | **3.7** | |

Two facts drive everything below.

1. **ERCOT solves FOUR LPs per year, and the residual hides two of them.** The
   ercot-221 adaptive-expectation offer runs a second P1 pass
   (`run_calibration.py:5680`), and ercot-230's fixed point can iterate further,
   but `_timing` reads `build_s` / `solve_p0_s` / `solve_p1_s` from the FINAL
   `EnergySolveResult` while `energy_solve_s` spans the whole bracket. **93 % of
   `markup` is solver and build time under the wrong name.**
2. **NEISO — one pass, warm P1, no floor bridge — reads 3.6–3.7 s/yr.** The 200×
   gap between the ISOs is not a difference in "markup"; it is one extra pass
   and one extra cold rebuild. `markup` is a *structure* signal, not a
   *performance* one.

**And the flip that looks like the fix is refuted.** The run's own log, from the
routing diagnostic this session added:

```
P1 route: COLD REBUILD on a floored fleet — MARKET_SIM_P1_FLOOR_INPLACE off
(default); would have been DECLINED anyway (availability changed and feeds a
row) (availability_changed=True, availability_feeds_rows=True)
```

---

## 2. Candidate fixes, ranked

Expected saving is per ERCOT keeper solve-year, read off §1's measured split.
"Byte-identity risk" is against the stage-0 goldens at `atol=rtol=0`, which is
the gate every one of these must clear before it ships.

### C-1a · Skip the adaptive pass entirely when its objective is unchanged — **up to ~930 s/yr (half the ERCOT year), LOWEST risk of anything here**

**The 2025 case.** `P_hat` max **0.000**, **0** pass-1 spike days, floor above
VOM in **0 of 1460** window hours — and the keeper resolves
`ercot_exhaustion_expectation = False` / `ercot_storage_reservation_offer =
False`, so pass 1's `p1_storage_discharge_cost` is `None`, i.e. the model
default, which `run_calibration.py:5057` sets to `storage.vom` — the same array
pass 2's `max(vom, floor)` reduces to. **ERCOT 2025 then re-solves an LP
identical to pass 1's, twice (P0 and P1), for 926 s — half the year — and lands
on a bit-identical answer.**

**The change.** Before entering the adaptive pass, compare the resolved
discharge-cost array elementwise against the one pass 1 solved
(`np.array_equal`, broadcasting the `None` default to `storage.vom`); when they
are equal, keep pass 1's `EnergySolveResult` and skip the pass.

**Byte-identity risk: the LOWEST on this list, because the guard is an exact
equality rather than an argument.** If the two objectives are elementwise equal,
the second pass is solving the identical LP with the identical objective, so
reusing the first result is the definition of what it would have produced. No
determinism assumption is needed at all.

⚠️ **Do not weaken the guard to the log's own "floor > vom in N of 1460"
counter** — that compares against `float(_vom_s.max())`, a scalar over units, so
it does not establish elementwise equality for a unit below the fleet-max VOM.
The array comparison is the test; the counter is only the symptom.

**Sizing, honestly:** worth ~930 s in 2025, and **0 s in 2023 and 2024** (7 and
3 spike days, floor above VOM in 768 / 563 window hours — those passes are
real). So this is a *variance* fix, not a mean fix: it removes the case where
half a year is spent confirming that nothing changed. Whether that case is
common outside 2025 is unmeasured.

### C-1b · Reuse pass-1's P0 in the adaptive pass when it DOES run — **379-463 s/yr (23-25 % of the ERCOT year), LOW risk**

**The mechanism.** All four `run_energy_solve` call sites in
`scripts/run_calibration.py` pass the **same objects** — `fleet`,
`fleet_arrays`, `demand`, `mc_base`, `dispatch_kwargs`, `config` — and differ in
exactly one argument, `p1_storage_discharge_cost`, which `run_energy_solve`
applies to **P1 only** (`solve.py`: *"P0 (already solved) is untouched"*).
`fleet_arrays` is rebound only after every pass (`run_calibration.py:5922`). So
the adaptive pass's P0 builds a matrix and cold-solves an LP that is
**bit-identical, objective included, to the pass before it**, then discards the
answer. Measured on ERCOT 2023: **6.6 s build + 372.8 s `h.run()`**.

**The change.** Let `run_energy_solve` accept a precomputed `r0` (and the markup
/ floored fleet derived from it, all three being pure functions of that `r0`)
and skip the P0 build+solve when given one; the adaptive call sites pass pass-1's.
Measured saving, per year: the reported `solve_p0` (which IS the adaptive pass's
P0) plus that pass's matrix build — **379 s (2023) / 463 s (2024) / 463 s
(2025)**, i.e. **23 / 25 / 23 % of the whole year** — plus that pass's share of
`p0_post` (~7 s), `seam` (~2.7 s) and `markup` (~0.2 s). It applies in every year
the adaptive pass actually runs, so it is the **complement** of C-1a, not a
substitute for it.

⚠️ **Note where the saving comes from: `solve_p0`, not `markup`.** The reported
`solve_p0` is the *final* pass's P0, so this candidate does not shrink the
`markup` field at all — it shrinks a field that looks legitimate. That is
exactly why C-2 is listed as "do it first": on the current instrument, the
largest safe win is invisible.

**Byte-identity risk: LOW, and it is a *reduction* in nondeterminism.** Under
the determinism pin the capture tool sets (`MARKET_SIM_HIGHS_THREADS=1`) a
cold-vs-cold re-solve of the same LP is bit-identical — the capture tool's own
docstring is the authority — so reusing the result *is* what the second solve
would produce. Multi-threaded HiGHS is already not bit-identical, so reuse can
only make that path more reproducible, never less. **Still gated on the goldens
before it ships.**

⚠️ **One real interaction to check first.** Under the calibration CLI (which
defaults `MARKET_SIM_WARMSTART_XYEAR` **ON**) the `xyear_cache` holder is
refreshed by every pass, so today the adaptive pass's P0 **warm-starts from the
previous pass's own basis** — a *within*-year use of the cross-year seam. Under
the goldens/replay pin (`XYEAR=0`) that path is off, which is the regime §1
measures. A C-1 implementation must state what it does with that holder, and be
measured in **both** regimes.

### C-2 · Count every build and every pass in `_build` / `solve_*` — **0 s, ZERO risk, do it first**

Not a speed-up: a **reporting** repair, and the precondition for trusting any
future measurement. `_build` reads one pass's `p1.build_time`, so `markup`
currently over-reads by ~724 s on an ERCOT year and `data_prep` under-reads by
the same amount (it is computed as the complement). The per-pass log this
session added already carries every number needed; summing it into `_timing`
turns `markup` into the genuine non-solve residual it claims to be.

Do this before C-1, so C-1's before/after is read on an instrument that is not
itself lying.

### C-3 · Skip the P0 pass's unneeded solution marshalling — **≈15 s/yr on ERCOT, ≈1.7 s/yr on NEISO, LOW–MEDIUM risk**

`DispatchResult.solve_time` stops at `h.run()`, so `getSolution()`, the full
`col_dual` conversion (highspy boxes a vector attribute into a Python list on
every access — ~0.8 GB at ~25 M columns, per the in-file note) and ~330 lines of
extraction are charged to `markup` on **both** passes. Audited, the **P0**
result's only consumers are `r0.dispatch`, `r0.prices`, `r0.wind_dispatched`,
`r0.solar_dispatched` (`pipeline/commitment.py`, `run_calibration.py:4167`,
`:5913`) — never `gen_reduced_cost`, `flow_dual`, the reserve/LCR/interface
duals or any sidecar input, all of which are written from P1.

**Shape:** an extraction-scope argument on `DispatchModel.solve`, default
`full`, with the P0 call opting into the narrow set. **Risk is a missed
consumer, not a moved solution** — the LP is untouched, so dispatch and prices
cannot move; the audit above must be re-run against HEAD in the implementing
session, because `2966b0c4` (nyiso-180) has already widened this extraction once.

**Sizing honestly: this is the smallest of the three real levers on ERCOT** and
is worth doing for the *memory* argument (the extraction transients are the top
of the documented 14.4 GB year peak) at least as much as for the seconds.

### C-4 · Arm the in-place P1 refloor — **REFUTED for ERCOT. Do not charter it.**

`MARKET_SIM_P1_FLOOR_INPLACE=1` is the obvious reading of "a second build is
being booked as markup", and it is **worth 0 s on ERCOT**. The bridge raises
`availability` where its floor would exceed `pmax * availability`, ERCOT runs
the reserve co-opt, so availability feeds an LP row and
`refloor_thermal_inplace` **declines by construction**. Measured in the run's
own log (§1). It would still pay on an ISO whose floor bridge leaves
availability untouched — none of the current keepers.

The *mechanism-level* version — make the bridge floor respect
`pmax * availability` so no availability raise is needed, which would make the
in-place path admissible — is a **calibration-lane change to a keeper mechanism,
not a perf change**, and is out of scope for WS3 under the R-V freeze.

### C-5 · `compute_monthly_markup` — **CLOSED, again, and this time from the phase's own timer**

**0.4 s of a 761.9 s window on ERCOT (0.05 %); 0.1 s on NEISO.** PERF-A §2.6
closed this flag on a cProfile reading of 0.127 s and the hand-back reopened the
question only because the *window* had grown. It had not grown for this reason.
Nothing to do.

### C-6 · The basis seam (`tail`) — **already gated, nothing owed**

**0.0 s** in the measured regime, because the goldens/replay pin sets
`MARKET_SIM_WARMSTART_XYEAR=0` and PERF-B (e) already gated the export on its
consumer. Under the calibration CLI's default-ON regime it costs the previously
documented ~10–16 s/yr of `getBasis()` enum materialization. Report only.

---

## 3. What needs an owner memo

**Nothing in C-1 … C-3 does — and that is the useful result.** The plan-§6
memo gate covers the `MARKET_SIM_P1_FLOOR_INPLACE` default flip, because it is a
warm-start-class change validated by `diff_warmstart_bundles.py` rather than by
`--mode byte`. **That flip is C-4, and C-4 is refuted on the merits**: it buys
ERCOT zero seconds. **The memo should not be requested.**

Two things a future lane *would* need a memo for, neither chartered here:

1. **Warm-starting the adaptive pass's P1 from the previous pass's basis**
   (re-costing the live model instead of rebuilding it — the natural extension
   of C-1 into the P1 half). That is warm-start class by construction: it would
   change marginal-tie dispatch by the documented ≤0.0033 % and cannot be
   proved on the byte goldens. It is worth roughly the pass-2 P1 build plus most
   of its solve, so it is the largest remaining item — and it is exactly the
   kind of change the memo gate exists for.
2. **Changing the ERCOT gas-commitment bridge so its floor never raises
   availability** (which would unlock C-4). That is a keeper-mechanism change
   under the R-V freeze and belongs to the ERCOT calibration desk, not to WS3.

---

## 4. Session-1 residue

Board **L-7** re-derived PERF-B session 1's four charter items as **all CLOSED**,
leaving one repair owed. All three named items were re-verified against source
this session (`docs/FINDING-perfb-s2-markup-attribution-2026-09.md` §8):

| item | state | note for the next lane |
|---|---|---|
| `ci.yml` checkout | **CLOSED**, unchanged | 21 sparse-checkout blocks / 10 jobs; `fast-tests` `timeout-minutes: 20` at `.github/workflows/ci.yml:418`. Nothing owed. |
| basis LUT | **CLOSED**, unchanged | `_BASIS_STATUS_OBJS` at `model/lp/model.py:43`, indexed `:1523-1524`. L-7's `:1501-1502` has drifted 22 lines. |
| `scenarios.py` warm-start citation | **REPAIRED this session** | It had drifted a second time: `:13606` → L-7's `:13825` → **`:14528`** at HEAD. Re-pinned to the **symbol**, line stamped and dated. |

**One systemic item this raises, and the reason it belongs in a charter rather
than a fix list.** Two of the three residue items — and the board's own
`check_mechanism_matrix` anchor tax (L-11: *"a standing tax on a heavily-crossed
file"*) — are the same failure: **a line number into `scenarios.py` or
`model.py` is not a citation, it is a decaying pointer.** Chasing digits is the
tax; citing the symbol is the fix. Recommended as a standing convention for docs
lanes, and as the shape of any answer to the director's open question of whether
a matrix anchor should be a line number at all.

**Two further drifted citations, found and deliberately NOT edited.**
`docs/handoffs/perf-a-warmstart-decision-memo-2026-08.md` cites
`scenarios.py:11646` (twice) and `:11644` for the same field and its guard. It is
an **owner-signed** memo, so this lane reports rather than amends. Correct
anchors: the field at `:14528`, the guard comment immediately above it.

---

## 5. What a WS3-next lane should do, in order

1. **C-2 first** (0 s, zero risk). Land the reporting repair so the instrument
   the rest is measured on is not itself lying. One PR, no golden capture
   needed beyond the fast tier.
2. **C-1a** (the exact-equality guard). Small, self-contained, and the guard
   makes the byte argument trivial. Gate it on ERCOT **2025** — the year whose
   whole second pass it removes — plus one year where the pass is real (2023),
   to prove it does not fire when it must not.
3. **C-1b** (reuse pass-1's `r0`). Larger change, still low risk; gate on all
   three ERCOT years **and** NEISO (which must be untouched — it has one pass,
   so the code path must be provably inert there).
4. **C-3** only if the memory argument is wanted; the seconds do not justify it
   alone.
5. **Never C-4.** Refuted; and do not request the memo for it.

**Budget note for whoever schedules this.** Capturing the ERCOT byte gate costs
~95 min of solve for the three-year forward config and ~30 min for the
2023 carve-out, measured this session on a 15 GB box with a 5 GiB swapfile and
single-threaded HiGHS. **The carve-out alone is a sound ERCOT-side control** —
it exercises the identical multi-pass, floored-fleet, cold-P1 path for one
year — so a lane iterating on C-1a/C-1b should gate on the carve-out and spend
the full three-year capture once, at the end.

## 6. Standing constraints (restated so this charter is self-contained)

* **Keepers ERCOT / NEISO / PJM are FROZEN (R-V).** No lane chartered here
  changes a `ScenarioConfig` default, promotes anything, or edits a keeper
  shard, marker, matrix shard, registry or workflow.
* **Byte gate at `atol=rtol=0`** against the stage-0 goldens, through
  `scripts/regression_gate.py --mode byte`, before anything merges. Note that
  `main` has grown a `klass_base` column in the dispatch frame since the
  stage-0 captures (`e5639ca1`, 2026-09-03), so a comparison against
  `perfb-stage0` needs that column accounted for; a **merge-base control
  capture** avoids the question entirely and is the cleaner instrument.
* **Rule 27 `[R-PUSH]`** on every file touched — `run_calibration.py` and
  `run_calibration_full.py` are both far past 300 lines, so edit locally and
  verify the pushed blob.
* **Rule 12** — years sequential within a run; separate invocations concurrent,
  capped at ~2 for per-plant multi-zone LPs. An ERCOT capture peaks ~12.5 GB.
* **No GitHub-runner solves.**
