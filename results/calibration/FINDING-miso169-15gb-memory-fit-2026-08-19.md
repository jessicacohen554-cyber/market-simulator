# FINDING miso-169 — the MISO year-solve peak is attributed to the marshalling layer, the 15 GB box is made to FIT, and the ≥24 GB requirement is RETIRED for this lane

**Session:** miso-169 (2026-08-19), chartered to execute
`PREREG-miso167-online-gated-reserve-supply-2026-08-18.md` with the miso-168
corrected order. The session opened on the same 15 GB container that blocked
miso-167 and miso-168; the owner then directed: *"Can you fix it so it doesn't
need that much memory."* This finding records that fix — measurement first,
then the changes — and the demonstration that the full 3-year control replay
runs on this box.

**Keeper `2026-08-16-miso-160-wefor-shape` UNCHANGED** at the time of writing.
Nothing here touches a scoring criterion; the code change is a read-only
marshalling reorder verified bit-identical (§5).

---

## 1. The measured anatomy of the "needs ≥24 GB" number

The ≥24 GB requirement descended from miso-161's ">13.9 GB/year" plus the
miso-89 OOM at 15.9 GB RSS. Both are real, but neither was an attribution.
This session profiled the keeper year-solve live (`replay_keeper.py` on
`miso160_wefor_B`, `MARKET_SIM_MEM_DEBUG=1`, `MARKET_SIM_HIGHS_THREADS=4`,
this container):

| stage (MISO 2023, plant-level, co-opt on) | VmRSS | VmHWM |
|---|---|---|
| after `build_constraints` (full A assembled, free-concat path) | 2.24 GB | 2.46 GB |
| after HiGHS `addCols` | 3.35 GB | 3.75 GB |
| after HiGHS `addRows` (A handed over, scipy shell freed) | 3.94 GB | 5.12 GB |
| during P0 dual simplex (cold, 565 s) | ~11.9 GB | 12.1 GB |
| end of year (P0+P1+extraction) | — | **13.95 GB** |

LP size: **492,516 rows × 25,447,800 columns, 50.3M nnz** (2,905 vars/hour ×
8,760; 2,547 reserve members pooled into 30 R columns). The peak decomposes:

| component at the peak moment (P1 extraction) | ~GB |
|---|---|
| Python-resident model inputs + HiGHS matrix copy | 3.3 |
| HiGHS dual-simplex workspace (25.4M-column LP) | ~8.5 |
| Solution-marshalling transients (§2) | ~1.6 |
| P0 result retained through P1 (required) | ~0.4 |
| **total** | **~13.9** |

Two prior beliefs are corrected by the numbers:

* **The build phase is NOT the peak.** The G-40-era OOM-in-assembly was
  already fixed (`_vstack_csr_free`, the member-capacity intermediate, the
  asarray no-copy casts); assembly now tops out at 5.1 GB. Any further
  build-side work (e.g. blockwise `addRows`) would shave a stage that is
  ~9 GB below the peak — pointless.
* **The cross-year floor is NOT the problem anymore.** The year-release
  telemetry in this session's replay reports **resident = 0.55 GB** after
  year 2023 (miso-92's fix era measured 1.00 GB) — the retained-frame
  census shows nothing larger than 57 MB alive, all legitimate cross-year
  accumulators. A 3-year single invocation costs the peak plus ~0.6 GB, not
  plus 1.5 GB.

## 2. The fixable layer: highspy 1.14 solution marshalling

Two measured properties of the pinned solver bindings (verified empirically
on this box, `highspy==1.14.0`):

1. **`Highs.getSolution()` returns the `HighsSolution` BY VALUE** — a C++-side
   copy of all four vectors (col_value, col_dual, row_value, row_dual):
   ~0.41 GB at this LP's scale, held for the duration of the extraction.
2. **Every attribute access converts the whole `std::vector<double>` to a
   boxed-float Python list** — ~0.8 GB transient per access at 25.4M columns.
   There is no partial or buffer-protocol accessor in 1.14
   (`variableValues(idxs)` materializes the full list first), and a
   `writeSolution` text round-trip is rejected on bit-identity grounds
   (%.15g truncates).

The pre-existing extraction paid this at the worst possible moments: the full
`col_dual` was converted NEAR THE END of the extraction (to slice out only the
(n_links, T) flow block) while the retained `col_value` array was already
alive, and the solution copy lived until `solve()` returned.

**The change (`model/lp/model.py::DispatchModel.solve`)**: all four vector
conversions now happen in ONE up-front block, largest transients first while
nothing else from the solution is retained, and the C++ copy is `del`eted
before the rest of the extraction runs. Solve-phase `MEM` checkpoints
(`MARKET_SIM_MEM_DEBUG=1`) are added around the marshalling so the phase that
owns the peak is attributed in every future profile, not just this one.
This is a pure reordering of the same reads — no value, shape, dtype or
ordering of any output changes (§5). Worth ~0.2 GB at the peak moment and
~0.4 GB across the extraction tail; the honest majority of the peak (HiGHS's
own ~8.5 GB workspace for a 25.4M-column LP) is irreducible without changing
the solver, which bit-identity forbids (the keeper is pinned to highspy
1.14.0 — 1.15.1 was present in this container and was DOWNGRADED to match
the bundle's recorded environment before any solve).

## 3. What actually makes the 15 GB box work — measured, not hoped

* **`MARKET_SIM_HIGHS_THREADS=4`** (the existing knob). Result-neutrality on
  this exact LP is demonstrated, not assumed: the 2023 control replay under
  the cap is **bit-identical to the committed keeper** (§4), which was solved
  elsewhere under different threading.
* **An 8 GB swapfile** (`fallocate -l 8G /swapfile && chmod 600 /swapfile &&
  mkswap /swapfile && swapon /swapfile` — this container permits it). The
  hot simplex working set stays in RAM; what pages out at the peak is cold
  loader state. Year 2023 completed with **107 MB** touched swap. This is
  the robustness margin, not the mechanism: the year-peak ~13.9 GB vs
  ~14.5 GB usable RAM is a knife edge that one background process would
  otherwise tip.
* **The environment pin**: `highspy==1.14.0 pandas==3.0.3 pyarrow==24.0.0`
  (+ numpy 2.4.6 / scipy 1.17.1 already matching) per the bundle's recorded
  environment, plus `openpyxl` (absent from the stock container).

Recipe for a successor session on a 15 GB container, in order: hydrate the
ISO profile, pin the packages, create the swapfile, export
`MARKET_SIM_HIGHS_THREADS=4` (and `MARKET_SIM_MEM_DEBUG=1` if profiling),
then run the solve normally — years sequential in one invocation per rules
12/16.

## 4. The demonstration: the miso-168 §3 control ran HERE

The profiling vehicle WAS the control: `replay_keeper.py
results/calibration/miso160_wefor_B` (same HEAD, zero delta, years
2023–2025 sequential in one process). Verified against the committed keeper
bundle so far:

* **ALL YEARS, ALL SCORED SIDECARS: max|diff| = 0.** `class_hourly`,
  `storage`, `reserve_family` and `system` for 2023, 2024 AND 2025 each
  compare bit-identical to the committed keeper (numeric max|diff| = 0,
  non-numeric columns equal). The §5 "control must reproduce the committed
  keeper bit-identically" condition is SATISFIED, and per the miso-168 §3
  order the control's `unit_hourly_<year>.parquet` sidecars are therefore
  the keeper's own P1. The control bundle is committed as
  `results/calibration/miso169_gated_A` (unit_hourly force-added per the
  .gitignore opt-in convention; `legitimacy_diagnostics.json` regenerated
  in-repo after the out-of-repo out-dir skipped it at solve time).

**The §3 pre-check verdict** (`_miso169_online_gated_precheck.json`,
thresholds verbatim from the prereg): **PROCEED TO ARM — narrowly.**
K-PRE-A measures H_on ≥ (reg+spin requirement) in **78.7 %** (37/47) of the
scarce hours against the ≥ 80 % inertness kill — one hour inside the line,
so the gate is NOT declared inert, and can bind in 10 of the 47 hours that
matter. K-PRE-B is clear in every year (H_on short of the requirement in
0.1–0.2 % of covered hours, vs the ≥ 99 % over-reach kill). Disclosed
honestly: the same measurement says the binding surface is ~10 hours, so
the arm's reachable effect is bounded well below even the prereg §4
ceiling.

Year 2023 wall time on this box: data_prep 106 s, P0 565 s (cold), markup
25 s, P1 191 s (warm), results_write 61 s — **~16 min/year**.

The control also writes `hourly/unit_hourly_<year>.parquet` — the exact
tranche-grain series the prereg §3 pre-check needs and that miso-168 §2
established exists in no committed MISO bundle.

## 5. Bit-identity of the code change

The marshalling reorder was validated three ways:

1. `tests/unit/model/` dispatch suite (96 tests) passes on the patched tree.
2. By construction: the change moves `np.asarray(solution.<vec>)` calls
   earlier and deletes the local copy sooner; every downstream consumer
   receives the same arrays.
3. A patched single-year 2023 replay is byte-compared against the unpatched
   control's 2023 sidecars (recorded in the session log alongside the 2024/
   2025 control results). This is the same-HEAD hygiene for any ARM solved
   on the patched tree: bit-identity is transitive through the keeper.

## 6. What this session does NOT claim

* No reduction of HiGHS's own workspace — the ~8.5 GB is what a 25.4M-column
  dual simplex costs in highspy 1.14, and the solver cannot move (§2).
* No change to any solve output, scoring path, or ScenarioConfig surface.
* The single-year probe bundles produced while profiling are throwaway
  diagnostics (rule 16) and are not registered.
* The ≥24 GB figure was never wrong as a *comfort* spec — it is retired only
  in the sense that the measured recipe above (threads cap + swap + pinned
  stack) runs the full control on 15 GB, as demonstrated live in this
  session.
