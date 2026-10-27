# RESULT: UC-MISO-MEM. Can an exact change to the UC step fit MISO in 16 GiB? No: the peak is the full-year LP, not UC

```
LANE     : UC-MISO-MEM (desk UC-DESK session_01WX9W5tgYMre3Z134LZoGF6; owner ruling R35 2026-10-26 "Cut memory first")
HEAD     : main b295a6d8 (branch claude/uc-miso-mem). No src/ change. Engine string unchanged.
LP       : two profiling runs of MISO 2019, NOT backcast legs. Nothing registered or promoted. Bundles stay off main.
CONTAINER: 13.36 GiB cgroup ceiling + 9.0 GiB swap = 22.4 GiB; MALLOC_ARENA_MAX=2, 1 HiGHS thread (the solve pins)
OUTCOME  : HARD STOP "gain too small to fit 16 GiB". The ≤ 12.8 GiB target is below the RSS of the full-year P0/P1 LP,
           which every MISO year needs with UC on or off.
```

## 1. Method

`memprof.py` (in `data/uc_miso_mem_readings/`) runs `replay_keeper.py` and samples the process tree's VmRSS and VmSwap every
2 s. Each sample is keyed to the latest log line. The second run also sets `MARKET_SIM_MEM_DEBUG=1`, which turns on the LP
build and extraction checkpoints in `model/lp/model.py`. Both runs replay keeper `closeout_miso_nuc_span`, year 2019:

| run | recipe | outcome |
|---|---|---|
| **UC on** | U4 recipe (`unit_commitment_milp`, `st_gas_mustrun_per_plant=false`, `vlr_pocket_commitment`, `uc_commitment_demand_source="da_forecast"`) | container restarted at t ≈ 3,230 s, after P0 and UC windows 0–118 of 365. P1 not reached. |
| **UC off** | keeper recipe unchanged | completed, 821 s |

## 2. Where the peak is (RSS + swap of the process tree, GiB)

| phase | UC on | UC off |
|---|---|---|
| load / data prep | 5.0 | 4.1 |
| P0 build (492,637 rows × 32.1 M cols, 76.8 M nnz) | → 13.1 | → 5.2 RSS after `addRows` |
| P0 simplex `run()` (500–600 s) | 12.2 median, **13.1 cap** (RSS pinned at the ceiling) | 11.9–13.1 (HWM **13.95 GB** post-run) |
| P0 extraction | **15.8** | 14.0 |
| UC windows | 11.4 median, 12.9 max (prep transient) | — |
| P1 solve + extraction | not reached | **16.25** (cgroup RSS+swap **16.59**) |

Findings:
1. **The year peak is the full-year LP**, i.e. the P0/P1 simplex workspace plus solution extraction, with or without UC.
   - UC off, MISO 2019 peaks at 16.6 GiB RSS+swap (cgroup).
   - The U4 legs with UC on peaked at 16.99 / 16.73 GiB (RESULT-ucmilp4 §2).
   - So UC adds ≤ ~0.4 GiB at the peak, and that small difference could come from the cold-versus-warm P1 route.
2. **HiGHS alone grows from 5.2 GB after `addRows` to ≥ 13.95 GB during `run()`.** That is ~8.7 GB of simplex workspace,
   and the cgroup ceiling caps the RSS reading. The workspace size depends on the solver and its options. Changing those
   is a hard stop.
3. **The UC step is not the peak.** At 11.4 GiB it runs ~4 GiB below P0/P1. Most of it is the live P0 `DispatchModel`, which
   `pipeline/solve.py` keeps until after `p1_fleet_prep(r0)` returns. The model is released only on the cold P1 route,
   once the UC hook has run.

## 3. What an exact UC-scoped change could and could not do

- **Could:** release the P0 model before the UC windows when P1 is certain to go cold. That holds when UC has integers
  and `MARKET_SIM_P1_FLOOR_INPLACE` is off. Export any basis the seed or the cross-year holder needs first. Results stay
  identical, since the UC stage reads `r0` and never the model. The UC-phase plateau would fall from ~11.4 GiB to roughly
  the ~5 GiB of Python-side inputs (estimate, not measured).
- **Could not:** move the year peak. P0 (15.8) and P1 (16.3–16.6) are untouched, so the 1.25× gate would not change
  (1.25 × ~16.6–17.0 ≈ 20.8–21.3 GiB vs the 12.8 target). Under the charter's hard stop the change was **not implemented**,
  because it buys no container class.
- **Outside this lane:** reaching ≤ 12.8 GiB would need the full-year LP itself to shrink. The options are a smaller
  HiGHS workspace (solver options or formulation: hard stop) or a smaller full-year column count. P0/P1 extraction has
  already been reordered for memory (miso-169, PERF-C S2). The remaining transient is the highspy list-typed
  `getSolution()` vectors (~1 GB per 32 M-column vector while a list exists). Removing it needs a highspy numpy
  accessor, which is not in the pinned 1.14 bindings.

## 4. Gate

**No gate proposal.** The measured whole-year peak is unchanged, and the incumbent rule (1.25 × the measured max, 17.89
→ 22.4 GiB) stands. This run adds one data point: **MISO without UC also peaks at 16.6 GiB RSS+swap.** The 22.4 GiB
requirement is therefore a property of MISO's full-year LP, not of the UC stage. It applies equally to non-UC MISO legs
(which are not gated at 22.4 today). That is a desk/owner observation, not a change.

## 5. Identity

Not applicable: no solve-path code changed. No `uc_schedule` or objective comparison was made.

## 6. Files

`docs/records/miso/ucmilp/data/uc_miso_mem_readings/`:
- `rss_uc_on_2019_partial.tsv` (sha256 `314b0ccbc8d5b747…`)
- `rss_uc_off_2019.tsv` (`c3f795779564c8a9…`)
- `uc_off_2019_mem_lines.txt` (MEM checkpoints, phase timing, `memory peak:` line)
- `uc_on_2019_key_lines.txt`
- `memprof.py.txt`

The probe out-dirs `results/calibration/ucmem_base_2019` (partial) and `results/calibration/ucmem_nouc_2019` stay off
main (rule 29(c)) and will not survive the container. They are profiling probes, not promotable legs.
