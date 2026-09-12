# FINDING — the MISO plant-level year LP does not fit in any available container, and it is not the arm

```
SESSION : miso-253
ISO     : MISO
SHA     : eaa9d6f196fcc5103164a6432dcab2856d95bb4c (carries the ~461 MB lifetime fix)
VERDICT : MISO 2023 CANNOT be solved in any container reachable from this program.
          The cause is arm-independent, environment-independent, and inside HiGHS.
```

Three shards, three environments, one pinned SHA, ~60 min budget each. **All three OOM-killed
within 113 seconds.**

## 1. The evidence

| shard | config | peak anon-RSS at kill | survived | bundle |
|---|---|---:|---:|---|
| **A** | arm ON, default solver | 13,945,980 kB = **13.301 GiB** | 110 s | none |
| **B** | arm ON, `HIGHS_THREADS=1`, scaling ON | 13,946,972 kB = **13.301 GiB** | 113 s | none |
| **C** | **arm OFF** (keeper recipe), default solver | 13,943,628 kB = **13.297 GiB** | 89 s | none |

Every kill: `CONSTRAINT_MEMCG`, `oom_memcg=/process_api/<id>/claude-code-bash`. Every ceiling:
**14,327,676,928 B = 13.344 GiB**, confirmed exactly by all three with the corrected nested
probe. `total-vm` ~30.3 GiB in all three.

## 2. What the three arms establish

**(a) IT IS NOT THE ARM.** Shard C ran the keeper recipe with `mustrun_chp_btm_holdout` OFF —
verified three independent ways (flag not passed; the string absent from the replayed
`run_config.json`; zero matches for the holdout log line) — and OOM-killed at **13.297 GiB**,
within 4 MB of the two armed shards. The arm changes no LP dimension and no memory behaviour.

**(b) IT IS NOT THE ENVIRONMENT.** Three different environments
(`env_016R8xUY4maDbppZ6TEns5V8`, `env_01MuEURKxFyu3AELJoBEHHPE`,
`env_01XWNfnUJbtN9JJfR3DQPJxY`) all report the **identical** 13.344 GiB nested ceiling.
**There is no larger container to be had by relaunching.** `MemTotal` reads 15.70 GiB and the
root cgroup reads unlimited in all three — both misleading, which is the trap that cost
miso-252 three containers and miso-253 two more.

**(c) THE THREAD CAP ALONE DOES NOTHING.** Shard B (`threads=1`, scaling ON) peaked 1 MB above
shard A's default settings and died 3 s later. This closes the one untested cell in the
memory-lever matrix — `MARKET_SIM_HIGHS_THREADS` was the last plausible lever and it is inert.

**(d) THE BLOW-UP IS INSIDE HiGHS, NOT PYTHON.** The complete checkpoint series ends at
`after addRows` = **5.06 GiB**; the process then takes a further **~8.2 GiB in ~33 s with no
Python-side allocation logged**. LP dimensions: **1,026,876 rows × 29,643,840 cols,
86,198,400 nnz (int32)**. Python-side work — `_vstack_csr_free`, `presolve off`, and this
session's own ~461 MB lifetime fix (all of which acts in `solve()`, downstream of the last
checkpoint) — had already done its job and handed off. **No Python-side optimisation can close
an 8.2 GiB gap.**

## 3. What was confirmed anyway

**G-1 footprint confinement, a third and fourth time.** Both armed shards emitted the
pre-registered line exactly:

```
must-run CHP/BTM holdout 2023 MISO: dropping 12.514 TWh of chp=Y host-steam
generation from the injected residual classes (170 of 2994 rows)
```

**12.514 TWh, 170 of 2,994 rows** — matching the PRECOMMIT prediction to the digit, now
confirmed in the parent at zero LP and on the solve path in three separate shards.

**No HEAD drift.** Shard C read the committed bench at this SHA: `biomass` 8.128, `OTHER`
10.325 (the un-partitioned values), CC_REGULAR 141.817, `classFull` total 616.259 TWh — every
committed-side number matches the reference, corroborating the parent's G-DRIFT conclusion
that HEAD has not drifted from the keeper.

## 4. The arithmetic, stated plainly

- MISO 2023 needs **> 13.344 GiB**. Best estimate of the true demand is **unknown and
  unmeasurable from these runs**: a process killed by its cgroup always reports ~the limit as
  its RSS, so 13.30 GiB is the *ceiling*, not the requirement. The only bound available is
  "more than 13.344".
- Python hands off at **5.06 GiB**; HiGHS adds **≥ 8.2 GiB** on a 29.6M-column model.
- Available: **13.344 GiB**, in every environment.

**Therefore only two classes of fix exist, and neither is a memory-hygiene change:**

1. **A bigger container** — the nested `claude-code-bash` cgroup must clear roughly 14.5–15 GiB.
   This is platform/environment configuration, not repo configuration. Raising it from inside
   the container works mechanically but trips the sandbox's `[Containment Escape]` refusal on
   the follow-on workload, so it is not a route an agent session can take.
2. **A smaller LP** — 3,384 columns/hour is the MISO fleet (~3,000 plant-level units from
   CAMPD per-plant binning × tranches). Reducing it is a **modelling decision that changes
   results** (rule 1 `[R-STRUCT]`), not a knob, and belongs to the owner.

A third option exists and is **deliberately not taken**: HiGHS solver/pricing options (IPM,
PDLP, Devex vs steepest-edge) would cut the per-column working set, but they can land on a
different optimal basis and therefore different **duals** — and prices *are* duals here
(rule 4 `[R-DUALS]`). That is a model-affecting change requiring owner sign-off, never a
silent memory fix.

## 5. Spent levers — DO NOT RE-TEST

| lever | verdict | measured |
|---|---|---|
| `MARKET_SIM_HIGHS_THREADS=1` | **INERT** | shard B: 13.301 GiB, 1 MB above default |
| `MARKET_SIM_HIGHS_LEAN=1` (scaling off) | **avoids the OOM, destroys convergence** | parent: no OOM, still grinding at **6h11m**, never converged |
| allocator / BLAS env vars | inert | miso-252 |
| `presolve` | already off | `model.py:620` |
| `_vstack_csr_free` | already landed | for this same OOM |
| `miso_seam_export_limit=false` | 18 MiB | miso-252 |
| Python lifetime fixes (`cost`, `mc`, `_all_cols`) | **~461 MB, landed, insufficient** | this session, `ee40acd2` + `eaa9d6f1` |
| relaunching in another environment | **inert** | three environments, identical 13.344 GiB |

## 6. Consequence for the biomass arm

`mustrun_chp_btm_holdout` remains **UNADJUDICATED** — matrix cell `O`, not a rejection. Its
footprint gate is confirmed four times over; its dispatch half (G-2/G-4/G-5) cannot be measured
until a MISO year LP can complete. **The arm is one successful solve from an answer, and that
solve is blocked on infrastructure, not on modelling.**
