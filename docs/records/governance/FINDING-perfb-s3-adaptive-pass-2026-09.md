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
| 3 · C-1b | [#4744](https://github.com/jessicacohen554-cyber/market-simulator/pull/4744) | `…-c1b` | reuse pass-1's P0 in the adaptive passes |
| controls + draft | [#4752](https://github.com/jessicacohen554-cyber/market-simulator/pull/4752), [#4753](https://github.com/jessicacohen554-cyber/market-simulator/pull/4753) (owner-opened from `…-c1b`) | `…-c1b` | `perfb-s3-before` manifest, NEISO + carve-out `perfb-s3-after` entries, this finding's draft |
| finding | follow-up PR from `claude/perfb-s3-adaptive-pass-soq3wl` restarted on `main` | | the ERCOT forward `perfb-s3-after` entry and this finding, complete |

---

## 0. Headline

**All three items shipped and merged (owner merges #4741 → #4742/#4744 → #4752/#4753), and the
full byte gate is green: `regression_gate.py --mode byte` at `atol=rtol=0` reads PASS on ERCOT
forward 2023-25, `ERCOT__carveout-2023` and NEISO, with 0.000 % reshuffle in every year; the
manifests' `content_hashes` agree 10/10, 6/6, 10/10; and every parquet in each bundle, `hourly/`
sidecars included, is frame-identical (34/34, 14/14, 31/31).** The claim of byte-identity below
is made from those outputs (§4) and from nothing else.

What the three items remove, per ERCOT year, read from the merge-base control's own solve log
(the seconds of the solves that no longer happen) and from the wall totals of the two captures:

| ERCOT config / year | C-1a (pass 2 skipped) | C-1b (pass-2 P0 reused) | year wall, control → shipped | HiGHS runs |
|---|---:|---:|---:|---|
| forward 2023 | — (7 spike days: must not fire, did not) | **298.5 s** (P0 build 10.3 + `h.run()` 288.2) | 1499.0 → 1347.0 s (−152 s) | 4 → 3 |
| forward 2024 | — (3 spike days) | **352.6 s** (8.8 + 343.8) | 1470.2 → 1276.9 s (−193 s) | 4 → 3 |
| forward 2025 | **823.3 s** (the whole pass: 12.2 + 413.0 + 7.9 + 390.2) + its marshalling | (subsumed) | 1890.3 → 968.4 s (**−922 s, −49 %**) | 4 → 2 |
| carve-out 2023 | — (12 spike days) | **369.7 s** (9.7 + 360.0) | 1621.1 → 1358.3 s (−263 s) | 4 → 3 |
| **forward, 3 years** | | | **4859.5 → 3592.3 s (−1267 s, −26 %)** | 12 → 8 |

The removed-solve column is the exact measurement; the wall column is honest but noisy — a
cold HiGHS run of the identical LP varies by ±10-15 % wall between the two captures on this box
(2023 pass-1 P0: 346.6 s in the control, 398.6 s after), which is why 2023/2024 show less than
their removed P0. C-2 removes 0 s by design; it is what makes the other two visible: the
`markup` field on the same year reads 756.7 / 738.0 / 1038.1 / 839.8 s on the control instrument
and **37.1 / 41.3 / 27.9 / 33.9 s** on the shipped one, with `solve_p0` / `solve_p1` /
`data_prep` now carrying what those seconds actually were (§1, §5).

NEISO — one pass, no floor bridge — is provably inert on this code path: no `P0 reused` or
`SKIPPED` line in its log, `n_passes` 1, and byte-identical output (§4).

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

**Where it fired and where it must not (shipped tree, `perfb-s3-after`, from the runs' own log):**

| config / year | pass-1 spike days | `P_hat` max | floor > vom (window h) | decision logged |
|---|---:|---:|---:|---|
| ERCOT forward 2023 | 7 | 0.370 | 768 / 1460 | `re-solving P1 (pass 2, THE scored pass)` |
| ERCOT forward 2024 | 3 | 0.176 | 563 / 1460 | `re-solving P1 (pass 2, THE scored pass)` |
| **ERCOT forward 2025** | **0** | **0.000** | **0 / 1460** | **`pass-2 storage discharge cost is elementwise IDENTICAL to the cost pass 1 solved with (max(vom, floor) == vom for every unit-hour) — pass 2 SKIPPED, pass 1 IS the scored pass (C-1a)`** |
| ERCOT carve-out 2023 | 12 | 0.629 | 749 / 1460 | `re-solving P1 (pass 2, THE scored pass)` |

Identical spike-day / `P_hat` / floor counts to the control in every year (pass 1 is untouched
by every item). The 2025 output is byte-identical to the control's, which solved that pass
(§4) — the s2 finding's "strongly indicated, not proved" (§4.4 there) is now proved on the
bytes. Removed in 2025: the whole second pass, 823.3 s of build + `h.run()` in the control
plus its two solution marshallings (≈22 s), i.e. the 926 s the charter sized from the s2 run,
re-measured at 845 s here.

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

**Where it fired (shipped tree):** every adaptive pass that ran — ERCOT forward 2023 and
2024, carve-out 2023 — logs `P0 reused from the previous pass (C-1b) … P0 build + solve
skipped`, and each year's log shows THREE `Matrix build … Solve … (cold)` lines instead of the
control's four. In 2025 the pass itself was skipped (C-1a), so there was nothing to reuse.
NEISO: never (one pass). The pass-2 P1 still cold-rebuilds on the floored fleet and still logs
its `P1 route: COLD REBUILD … would have been DECLINED anyway` diagnostic — the route is the
same, only the P0 in front of it is gone.

Removed (control-measured, the pass-2 P0 build + `h.run()`): **298.5 s** (2023), **352.6 s**
(2024), **369.7 s** (carve-out 2023) — 20-23 % of each year — plus that pass's `p0_post`
marshalling (≈10 s/yr, visible as `p0_post` falling from ~20 s to ~9.5 s in §5).

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

**`scripts/regression_gate.py --before results/regression-goldens/perfb-s3-before --after
results/regression-goldens/perfb-s3-after --mode byte --skip-smoke --skip-quarantine`:**

```
========================================================================
REGRESSION GATE  (mode=byte, atol=0.0, rtol=0.0)
========================================================================

[1] Golden bundle diff
    PASS  ERCOT: 9 files, 34 numeric columns within tolerance (atol=0.0, rtol=0.0)
    PASS  ERCOT__carveout-2023: 5 files, 22 numeric columns within tolerance (atol=0.0, rtol=0.0)
    PASS  NEISO: 9 files, 32 numeric columns within tolerance (atol=0.0, rtol=0.0)

[2] Reshuffle localization (informational)
  ERCOT 2023: total annual gen  cold 446064.7 GWh  warm 446064.7 GWh  Δ +0.0000 GWh
  ERCOT 2023: Σ|hourly Δ| (gross reshuffle): 0.0 GWh = 0.000% of total gen
  ERCOT 2024: total annual gen  cold 462847.6 GWh  warm 462847.6 GWh  Δ +0.0000 GWh
  ERCOT 2024: Σ|hourly Δ| (gross reshuffle): 0.0 GWh = 0.000% of total gen
  ERCOT 2025: total annual gen  cold 488450.0 GWh  warm 488450.0 GWh  Δ +0.0000 GWh
  ERCOT 2025: Σ|hourly Δ| (gross reshuffle): 0.0 GWh = 0.000% of total gen
  ERCOT__carveout-2023 2023: total annual gen  cold 446065.4 GWh  warm 446065.4 GWh  Δ +0.0000 GWh
  ERCOT__carveout-2023 2023: Σ|hourly Δ| (gross reshuffle): 0.0 GWh = 0.000% of total gen
  NEISO 2023: total annual gen  cold 96984.5 GWh  warm 96984.5 GWh  Δ +0.0000 GWh
  NEISO 2023: Σ|hourly Δ| (gross reshuffle): 0.0 GWh = 0.000% of total gen
  NEISO 2024: total annual gen  cold 103923.3 GWh  warm 103923.3 GWh  Δ +0.0000 GWh
  NEISO 2024: Σ|hourly Δ| (gross reshuffle): 0.0 GWh = 0.000% of total gen
  NEISO 2025: total annual gen  cold 107314.6 GWh  warm 107314.6 GWh  Δ +0.0000 GWh
  NEISO 2025: Σ|hourly Δ| (gross reshuffle): 0.0 GWh = 0.000% of total gen

========================================================================
  PASS  golden-diff
========================================================================
RESULT: PASS
```

**Supplementary, the whole bundle** (a frame-level `DataFrame.equals` per column on every
parquet under each golden dir, `hourly/` sidecars — `class_hourly`, `class_band_hourly`,
`system`, `reserve_family`, `adaptive` — included; plus the manifests' own `content_hashes`):

| config | manifest `content_hashes` | parquet files compared | differing |
|---|---|---:|---:|
| ERCOT forward 2023-25 | 10 / 10 identical | 34 | **0** |
| ERCOT carve-out 2023 | 6 / 6 identical | 14 | **0** |
| NEISO 2023-25 | 10 / 10 identical | 31 | **0** |

The `adaptive_<year>.parquet` sidecar is in that set, so the C-1a skip is also shown not to
change the recorded floor construction. Fidelity oracle PASS on every capture (270 / 270 / 258
recorded flags replayed identically); the 2-field `scenario_config` drift the tool reports
(`ccs_retrofit_capex_kw`, `fixed_om_gas_cc_ccs`, the capx-D41 default advance) is the same on
both sides and is the s2 finding's §5.4 item, not this lane's.

Both manifests are committed (hashes only) and `scripts/check_golden_manifest.py` reads OK on
each — 3 entries enforced, provenance run registered, golden CURRENT for all three.

## 5. Seconds removed, per item, per year

The same year on the two instruments. Control = merge-base tree (s2 sub-timers, pre-C-2
accounting); shipped = final tree (C-2 accounting, C-1a/C-1b active). Six frozen fields plus
the `markup` clause, from the phase-timing lines:

| config / year | tree | data_prep | solve_p0 | **markup** | solve_p1 | results_write | **total** | markup clause |
|---|---|---:|---:|---:|---:|---:|---:|---|
| fwd 2023 | control | 109.0 | 288.2 | **756.7** | 327.6 | 17.4 | **1499.0** | p0_build 24.5, p0_post 22.5, markup 0.4, seam 7.7, p1_post 21.1, prior_build 8.3, **prior_solve 672.2** |
| fwd 2023 | shipped | 135.8 | 398.6 | **37.1** | 762.0 | 13.5 | **1347.0** | p0_post 9.5, markup 0.4, seam 5.1, p1_post 22.1 |
| fwd 2024 | control | 36.8 | 343.8 | **738.0** | 339.4 | 12.3 | **1470.2** | p0_build 23.1, p0_post 19.4, markup 0.8, seam 10.1, p1_post 21.0, prior_build 9.5, **prior_solve 654.0** |
| fwd 2024 | shipped | 63.1 | 446.3 | **41.3** | 715.3 | 10.9 | **1276.9** | p0_post 10.0, markup 0.8, seam 9.5, p1_post 21.0 |
| fwd 2025 | control | 36.7 | 413.0 | **1038.1** | 390.2 | 12.2 | **1890.3** | p0_build 27.5, p0_post 22.2, markup 0.4, seam 9.8, p1_post 22.9, prior_build 9.4, **prior_solve 945.9** |
| fwd 2025 | shipped | 54.1 | 524.0 | **27.9** | 351.3 | 11.2 | **968.4** | p0_post 9.9, markup 0.6, seam 6.1, p1_post 11.3 |
| carve-out 2023 | control | 105.6 | 360.0 | **839.8** | 303.2 | 12.5 | **1621.1** | p0_build 19.5, p0_post 20.0, markup 0.5, seam 8.5, p1_post 20.9, prior_build 7.0, **prior_solve 763.3** |
| carve-out 2023 | shipped | 134.5 | 381.1 | **33.9** | 795.4 | 13.4 | **1358.3** | p0_post 9.0, markup 0.4, seam 4.7, p1_post 19.6 |
| NEISO 2023 | control | 82.0 | 101.8 | 5.0 | 40.4 | 3.6 | 232.7 | p0_post 2.4, markup 0.1, p1_post 2.4 |
| NEISO 2023 | shipped | 83.5 | 115.4 | 6.4 | 46.5 | 6.3 | 258.0 | p0_post 3.1, markup 0.2, seam 0.1, p1_post 2.8 |

Reading it: on the shipped instrument `solve_p0` / `solve_p1` are every pass's `h.run()`
(2023: `solve_p1` 762.0 = both P1 runs, 372.3 + 389.7), the builds sit in `data_prep`, and
`markup` is what is left — the two passes' solution marshalling, the seam, and 0.4-0.8 s of
`compute_monthly_markup`. Per item, per year, the seconds removed are the §0 table: C-2 0 s
everywhere (accounting only); C-1a 823 s + marshalling in 2025, 0 s elsewhere; C-1b 298.5 /
352.6 / 369.7 s (fwd 2023 / fwd 2024 / carve-out) and n/a where C-1a fired. The shipped NEISO
capture ran concurrently with the ERCOT forward control (the one overlap this session
allowed, both under the 15 GB + 8 GiB envelope), which is why its wall is ~10 % higher, not
the code: its log carries no reuse/skip line and its bytes are identical.

## 6. Swap / RSS record

8 GiB swapfile armed before the first launch (`fallocate` / `mkswap` / `swapon`; the box has
15 GB RAM, 4 cores, no swap by default), HiGHS single-threaded by the capture tool's pin.
Peak RSS is the capture process tree sampled every 10 s.

| capture | tree | peak RSS (process tree) | peak swap in use | ran alone? |
|---|---|---:|---:|---|
| ERCOT carve-out 2023 | control | not sampled (sampler added after this first launch) | — | yes |
| NEISO 2023-25 | control | 3.8 GB | 0 | yes |
| ERCOT forward 2023-25 | control | **13.4 GB** | 2.1 GB | no — NEISO (shipped) overlapped its 2023 |
| NEISO 2023-25 | shipped | 3.9 GB | 3.1 GB (system-wide, during the overlap) | no |
| ERCOT carve-out 2023 | shipped | **12.1 GB** | 0.2 GB | yes |
| ERCOT forward 2023-25 | shipped | **12.9 GB** | 0.1 GB | yes |

The 12.5 GB-class peak the charter warned of is real (12.1-13.4 GB), and it is a P1 rebuild
peak, not a P0 one — C-1b removes a P0 build+solve but not the moment two models coexist, so
peak RSS is unchanged within noise. Alone, an ERCOT capture touched swap only marginally
(≤0.2 GB); the 2-3 GB swap readings are the one deliberate overlap. Wall cost of the gate this
session: control captures 27 + 8 + 82 min, shipped captures 8 + 23 + 60 min.

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
