# FINDING — PERF-B session 3: the adaptive pass, skipped when vacuous and never re-solving its P0

**Session `claude/perfb-s3-adaptive-pass-soq3wl` (+ `-c1a`, `-c1b`), 2026-09-05.**
Executes the WS3-next charter (`docs/handoffs/perfb-session2-markup-charter-2026-09.md`,
director 2026-09-04) in its §5 order under its §6 constraints. Evidence it opens from:
`docs/FINDING-perfb-s2-markup-attribution-2026-09.md`. **Byte-gated at `atol=rtol=0`**
against merge-base control captures of the stage-0 ERCOT configs (ERCOT forward 2023-25 +
`ERCOT__carveout-2023`) and NEISO as the one-pass control. **No `ScenarioConfig` default
changed, no keeper shard, marker, matrix shard, registry or workflow touched, nothing
promoted** (ERCOT / NEISO / PJM frozen, R-V). C-4 was not chartered and no warm-start memo
was requested (charter §3). Goldens are never dashboard-registered (R-L).

One PR per charter item, stacked in order:

| item | PR | branch | what |
|---|---|---|---|
| 1 · C-2 | [#4741](https://github.com/jessicacohen554-cyber/market-simulator/pull/4741) | `claude/perfb-s3-adaptive-pass-soq3wl` | count every build and every pass in the phase-timing accounting |
| 2 · C-1a | [#4742](https://github.com/jessicacohen554-cyber/market-simulator/pull/4742) | `…-c1a` | skip the ercot-221 adaptive pass when its P1 objective is elementwise identical to pass 1's |
| 3 · C-1b | [#4744](https://github.com/jessicacohen554-cyber/market-simulator/pull/4744) | `…-c1b` | reuse pass-1's P0 in the adaptive passes; this finding |

---

## 0. Headline

__HEADLINE__

## 1. C-2 — the instrument, repaired first (0 s, zero numeric effect)

`markup` is the residual `energy_solve − build − solve_p0 − solve_p1`. Both orchestrators read
the three subtrahends from the FINAL `EnergySolveResult` (`p1.build_time`, `r0.solve_time`,
`p1.solve_time`) while `energy_solve` spans every pass — so an earlier pass's whole build and
both HiGHS runs, and the P0 model's build on a cold-P1 year, were booked as `markup`
(s2 finding §1). Now:

* `EnergySolveResult.build_s` is **every** `DispatchModel` matrix build of the pass (P0 model
  + the second model on the cold-P1 route; both under `WARMSTART=0`); `solve_p0_s` /
  `solve_p1_s` are its two `h.run()` seconds. The per-pass log carries the same three.
* `run_calibration._aggregate_pass_timing` **sums** them over every pass of the year into
  `_timing`; `runner.py` reads the result's own totals. The `p0_build` / `prior_build` /
  `prior_solve` residual components are retired — what they named is now subtracted.
* Wire format untouched (six frozen fields, optional clauses); builds land in `data_prep`
  (the pre-#2137 convention), `markup` is the genuine non-solve, non-build residual.

The same year read on both instruments — the merge-base tree (s2 sub-timers) and the final
tree (C-2 accounting) — is in §5.1; the C-2 half of the change is what makes the C-1a/C-1b
savings visible in `solve_p0` rather than hidden inside `markup`.

## 2. C-1a — the exact-equality guard

Before the ercot-221 pass 2, `run_calibration._p1_storage_cost_identical` compares the pass-2
`(n_storage, T)` discharge cost `max(vom, floor)` **elementwise** (`np.array_equal`, no
tolerance) against the cost pass 1's P1 actually solved with — its own
`p1_storage_discharge_cost` when set, else the kwargs `storage_discharge_cost`, broadcast
exactly as `lp.costs.build_cost_vector` does. Every other argument of the pass-2 call is the
same object pass 1 received, so equality of that one array is identity of the LP; pass 1's
result **is** what pass 2 would have produced, and the pass is skipped. The decision is on
the adaptive phase's own log line (`pass 2 SKIPPED, pass 1 IS the scored pass (C-1a)` vs
`re-solving P1 (pass 2, THE scored pass)`); the adaptive sidecar is recorded either way.

Not the log's `floor > vom.max()` counter: that is a scalar over units and misses a unit whose
VOM sits below the fleet max (`tests/regression/test_adaptive_pass_guard.py` pins the case).
ercot-230 and caiso-205 untouched.

__C1A_RESULTS__

## 3. C-1b — reuse pass-1's P0

`run_energy_solve(reuse_p0_from=<previous EnergySolveResult>)` reuses its `r0` and skips the
P0 build + solve. **Admissible only when the previous pass's P1 was cold** (new result field
`p1_cold`): on that route P1 solves a fresh model, so no live P0 model is needed and the
reused pass takes the identical cold route (the same hooks on the same `r0` object — the
ERCOT bridge's per-`r0` memo even hits). A warm-P1 pass is never reused: a cold P1 in its
place would move marginal ties, which is warm-start class and not provable on the byte gate.
The in-place refloor is skipped when there is no model; the warm branch raises rather than
silently cold-solving if the hooks ever failed to reproduce the route. Wired at the ercot-221
pass-2 call and inside the ercot-230 loop; **caiso-205 deliberately left unwired** (no CAISO
golden in this gate).

**The `xyear_cache` holder, both regimes (charter ⚠ on C-1b).** A reused pass neither
seeds/applies nor exports a basis. Under the calibration CLI's `MARKET_SIM_WARMSTART_XYEAR=1`
the previous pass's cold-P1 route already exported *its* P0 basis into the holder — the basis
of the identical LP — so the holder reads the same either way; the only thing removed is the
adaptive pass's own P0 warm-start *from* that holder, which is the solve being skipped.
Under the goldens/replay pin (`XYEAR=0`, the regime measured here) the holder is never read
or written on any route. Timing: a reused pass books 0 s of P0 (its seconds were counted by
the pass that produced it); `p0_reused` is on the result and the per-pass log.

__C1B_RESULTS__

## 4. Byte gate — merge-base controls vs the shipped tree

**Instrument.** `scripts/capture_keeper_goldens.py` (determinism pin
`MARKET_SIM_HIGHS_THREADS=1`, `WARMSTART=1`, `WARMSTART_XYEAR=0`), one ERCOT-class solve at a
time. The **control** (`perfb-s3-before`) was captured in a separate git worktree checked out
at the merge-base `b1964e7` (`MARKET_SIM_DATA_ROOT` pointed at the main tree's `data/raw`,
`PYTHONPATH` at the worktree's `src`, verified by `market_sim.__file__`) — so the comparison
is *same tree except this session's three commits*, and the `klass_base` column `main` grew
after the stage-0 captures is on both sides (charter §6). The **after** set
(`perfb-s3-after`) is the final tree (`ca4795f`, C-1b HEAD, which contains C-2 and C-1a).
Compared through the repo's designated instrument, `scripts/regression_gate.py --mode byte`
(`atol=rtol=0`), plus a supplementary frame-level comparison of **every** parquet in each
bundle including the `hourly/` sidecars (the gate itself reads `dispatch/*` + `system` /
`flows` / `storage`), and the manifests' own `content_hashes`.

__GATE_RESULTS__

## 5. Seconds removed, per item, per year

__SECONDS__

## 6. Swap / RSS record

8 GiB swapfile armed before the first launch (`fallocate` / `mkswap` / `swapon`; the box has
15 GB RAM, 4 cores, no swap by default), HiGHS single-threaded by the capture tool's pin.
Peak RSS is the capture process tree sampled every 10 s.

__RSS__

## 7. What was not done, and why

* **C-3** (narrow P0 extraction) — skipped. The charter admits it only on the memory argument;
  the peak-RSS record in §6 is the number that argument would rest on, and the seconds
  (≈15 s/yr) do not justify it alone. Left to a lane that wants the memory.
* **C-4** — never (refuted in the charter: 0 s on ERCOT). No warm-start memo requested.
* **caiso-205** — the same seam as ercot-221, deliberately not wired for C-1a/C-1b here:
  no CAISO golden in this lane's gate, and the discipline is "gated before it ships".
  A CAISO desk lane can wire both in one PR against a CAISO merge-base control.
* **Stage-0 manifest** — not re-stamped. `scripts/check_golden_manifest.py` validates
  manifests per stage-tag directory; nothing in this session changes a stage-0 entry, and the
  gate passes on the new `perfb-s3-before` / `perfb-s3-after` manifests (committed,
  hashes-only; the parquet is gitignored as always).
* **Pre-existing fast-tier red, not this lane's**:
  `tests/curation/test_clean_io.py::TestRegenerateEntrypoint::test_datatype_list_matches_schemas`
  — `ra-import-allocations` (caiso-245 intake) has a schema file but is missing from
  `clean_io.DATATYPES`. Fails identically on the merge-base tree; reported on #4741.
