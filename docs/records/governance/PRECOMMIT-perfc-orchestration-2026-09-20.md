# PERF-C — wall-clock levers that leave the LP untouched (orchestration record, 2026-09-20)

**STATUS: PRECOMMIT / orchestration.** Parent session `claude/model-performance-optimization-dlrhi3`,
main @ `ac0374b3`. The parent runs **no LP** (rule 32 `[R-SHARD]`); each lever below is executed
and measured by its own shard. Owner ask, verbatim: *"maintain the exact math and integrity … but
figure out places to reduce time it takes to run."*

## 0. Where a year goes today (measured, not estimated)

Per-year phase seconds at HEAD, every keeper replayed under the determinism pin
(`docs/handoffs/wallclock-baseline-2026-07.md` §WALLCLOCK 3a; ERCOT 2023 columns from
`FINDING-perfb-s3-adaptive-pass-2026-09.md` §5):

| ISO / year | data_prep | HiGHS P0 | seam+marshal | HiGHS P1 | results_write | total | HiGHS share |
|---|---:|---:|---:|---:|---:|---:|---:|
| ERCOT 2024 | 45 | 298 | 27 | 575 | 34 | 979 | 89 % |
| ERCOT 2025 | 40 | 335 | 19 | 364 | 29 | 786 | 89 % |
| CAISO 2024 | 14 | 638 | 16 | 738 | 23 | 1428 | 96 % |
| MISO 2023 | 35 | 320 | 20 | 254 | 46 | 675 | 85 % |
| PJM 2023 | 43 | 410 | 21 | 144 | 54 | 672 | 82 % |
| NEISO 2023 | 14 | 80 | 5 | 27 | 8 | 135 | 80 % |

Reading: **80–96 % of a year is inside `h.run()`**. The Python side (loaders, matrix build,
marshalling, parquet) is 10–15 % and its large items already landed (A-1 COD map, A-2 eGRID
mirror, A-3 sidecar, A-4 disk memo, C-1a/C-1b pass removal — `wallclock-desk-log-2026-09.md`).

LP shape (ERCOT 2025 keeper): 326,680 rows × 21,759,840 cols; MISO 2023: 1,026,876 × 29,643,840,
86 M nnz. Zero-LP census this session (`ERCOT 2023` carve-out, `run_year(fleet_only=True)`):
of 20,349,480 generator columns, 4.5 % have `ub == 0` and 6.9 % have `lb == ub > 0` — so
pre-slicing fixed columns out of the matrix would shrink the LP by ~11 %, not by half. Wind at
zonal grain is 61,320 columns (28.6 % fixed at 0); solar 61,320 (0.3 %). Matrix slicing is a
minor lever here; the solver path is the major one.

## 1. The levers, by expected seconds, with their identity class

| # | lever | class | expected | shard |
|---|---|---|---|---|
| L1 | **Same-year P0→P1 basis seed, un-nested from the cross-year gate.** Owner flipped it ON 2026-09-06 (desk-log item B: ERCOT 2024 year 991 → 606 s, −39 %; ON vs OFF objective and total gen identical, price moves dual-degenerate-only). Owner ruled both env knobs OFF 2026-09-19 (rule 36, miso-262) on **cross-year** evidence; the same-year seed went dark only because `pipeline/solve.py:473` arms it inside `_xwarm`. | warm-start (same optimum; tie-break may differ) | −200 to −550 s per ERCOT/CAISO/NYISO year | S1 |
| L2 | **P0 extraction slimming + skip the MER re-pricing run on P0.** P0's `DispatchResult` is consumed for 4 attributes; `_marginal_emission_rate` runs an extra `h.run()` (0 iterations) + 18 chunked `changeColsCost` over 21.8 M cols on every pass and its P0 value is never read. Plus collapse the ~20 successive `np.concatenate` on `row_lower/row_upper` and memoize `_fleet_group_by_code`. | byte-identical for every reported value | −10 to −25 s per pass; lower build-peak RSS | S2 |
| L3 | **HiGHS presolve.** `model.py:648` sets `presolve off` on a rationale written when the LP was ~1.8 M columns ("solves in a few seconds"). Never benched since; LP presolve is exact and postsolve recovers duals. Same shard benches Devex dual edge weights on the cold P0 (the one un-benched HiGHS knob). | exact LP; vertex path may differ | unknown — could be ±; must measure | S3 |
| L4 | In-place P1 refloor via `changeRowsBounds` (removes the second `DispatchModel` build + workspace). | warm-start | −15 to −27 s + ~1 GB peak | deferred: L1 subsumes most of the wall win |
| L5 | Memoize per-year pre-LP arrays (availability, CF, demand) to disk keyed on config. | byte-identical | −20 to −30 s/yr on ERCOT | deferred: small vs L1–L3 |
| L6 | Pre-eliminate fixed columns in the builder. | equivalent LP; path may differ | ~11 % fewer columns | deferred until L3 answers whether presolve already does it |

**Not re-opened** (disposed in `wallclock-baseline-2026-07.md` §79–226): IPM+crossover (did not
converge under caps), PAMI/`parallel`, `threads`, Dantzig, LEAN scaling.

## 2. Shard discipline (rule 32/33/34)

- Each shard: own branch `claude/perfc-<lane>`, pinned `source_revision` = this doc's commit SHA,
  `git rev-parse HEAD` must equal it as the first hard stop; never rebase, pull or sync.
- No shard registers a run, touches `frontend/data/backcast/**`, `dashboard_add_run.py`,
  `build_manifest.py`, `build_status.py`, `prune_iso_runs.py`, or opens a PR. `git add -A` / `git add .`
  forbidden. Bench bundles are scratch and are **not** pushed (they are not promotable runs; the
  numbers live in the FINDING doc).
- Model assignment (rule 27): S1/S2 edit `src/` → Opus. S3 edits no infrastructure (scratch
  driver + FINDING doc) → Sonnet.
- Memory: run the unmodified runners (they call `ensure_solve_container`), never
  `--no-container-preflight`; arms run **sequentially**, one ERCOT solve at a time; report the
  `container preflight:` and `memory peak:` log lines.
- "A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a
  FAILURE."
- The parent composes: reads each FINDING, verifies the branch, and puts the owner decisions
  (L1 default, L3 adoption) in its final report. Nothing here changes a keeper.

## 2b. RESULT (2026-09-22) — what the shards returned, and what this branch carries

| lever | shard verdict | on this branch? | record |
|---|---|---|---|
| L1 same-year P1 seed | **Landed.** Gate un-nested from `_xwarm`; optimality guard (non-Optimal or raising seeded solve → cold re-solve, provenance on `p1_seed_fallback`); default stays OFF. NEISO byte gate PASS (atol=rtol=0); 29 tests incl. two pre-existing rule-36 test failures repaired. | yes | `FINDING-perfc-s1-p1-seed-2026-09-20.md` |
| L2 P0 slim extraction + bound-vector collapse | **Landed** (changes 1 and 3). NEISO byte gate PASS, 16/16 golden files hash-identical, all six cold P0 solves reproduce to the iteration. | yes | `FINDING-perfc-s2-p0-slim-2026-09-20.md` |
| L2 skip MER re-pricing on P0 | **Refused on measurement.** Its closing `setBasis` is what P1's warm `run()` starts from on the live-model route; skipping it moved P1's vertex (NEISO: 78.9–130.5 GWh of marginal-tie reshuffle, same objective). Warm-start class, not byte-identical. | no | same |
| L2 `_fleet_group_by_code` memo | **Dropped by the parent**: correct but hits zero times on the solve path (one call per year, distinct key each time). | no | same |
| L3 HiGHS presolve | **Rejected.** ERCOT 2025: presolve removes 39–41 % of columns but costs 1,014–1,059 s per pass before simplex starts (the dependent-equations search burns its whole 1,000 s budget and removes 0 rows); each `h.run()` 1,432–1,455 s vs 335–364 s on record — **3.9× dearer**. The reduced LP's simplex (~400 s) was no faster than the full LP's, which also disposes of L6 (fixed-column pre-elimination): fewer columns do not buy simplex time here. Vertex moved on 5.7 % of zone-hours (confounded with the keeper's unknown 2026-09-19 warm-start state). | no code (`presolve off` stays) | `FINDING-perfc-s3-presolve-2026-09-20.md` |
| L5 input-array disk memo | **Built, measured, declined by the parent.** Demand + renewable CF memoized byte-identically (28/28 arrays), but they cost 2.86 s of a 25 s rebuild — ~0.3 % of an ERCOT year — and the availability matrix and fleet load were left out on soundness grounds. 745 new lines for 3 s/yr fails rule 26's spirit. Branch `claude/perfc-s5-input-memo` holds the code if the owner disagrees. | doc only | `FINDING-perfc-s5-input-memo-2026-09-20.md` |

| P0 solve cache keyed on the LP bytes (S6, 2026-09-22) | **Built, default OFF.** Key = blake2b over the exact CSR/bounds/cost handed to HiGHS + highspy version/options/threads pin; hit = `setBasis` of the stored optimal basis, 0 simplex iterations, objective identical to every digit in all six NEISO years. Miss path byte gate PASS. **Hit path byte gate FAIL on the live-model P1 route** (NEISO/PJM/MISO): a replayed basis is not a searched basis as far as HiGHS's factorization goes, so the warm P1 that follows lands on a different tie vertex (same objective, 0.08–0.13 % reshuffle — the identical phenomenon S2 refused). Digest costs 0.5 s on NEISO, ~3 s on MISO. **Untested and expected byte-neutral on the cold-rebuild P1 route** (ERCOT/NYISO/CAISO, where P1 is a fresh model) — which is where P0 costs 300–640 s. Arming it there needs one NYISO or ERCOT before/after gate. | yes, inert | `FINDING-perfc-s6-p0-cache-2026-09-22.md` |

Net: the only material lever that survives measurement is **L1**, and it is a default the owner
must rule on (rule 36(d)'s "arms the second only inside the first's gate" is now false in code).
The Python-side trims are byte-identical housekeeping. Presolve and column-slicing are closed.

## 3. Owner decisions this lane will surface

1. **L1 default.** Rule 36(d) ruled the env knobs OFF "together because `solve.py` arms the second
   only inside the first's gate". Once S1 un-nests it, the same-year seed can be ON while the
   cross-year one stays OFF. The parent will not flip the default; it asks.
2. **L3 adoption** if presolve or Devex is faster: it is the same LP but not the same vertex path,
   so it is adopted (if at all) as a declared, cache-keyed setting, not a silent flip.
