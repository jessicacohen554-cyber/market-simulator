# FINDING — miso-252: biomass is self-scored and injects behind-the-meter cogen as grid supply; and MISO LPs no longer fit any available container

```
SESSION : miso-252
ISO     : MISO   (the biomass finding is CROSS-ISO — the injection applies to every ISO)
KEEPER  : 2026-09-09-miso-250-ep-gas — UNCHANGED. Nothing promoted; no arm ever solved.
```

## 1. THE LP MEMORY CEILING — three environments, three OOMs, no MISO solve is possible here

A single MISO year (8 zones × 8760 h, ~3,025 fleet members) **cannot be built in any container
this session can reach.** Measured, not inferred:

| attempt | environment | outcome |
|---|---|---|
| shard 1 | `env_016R8xUY4maDbppZ6TEns5V8` (Full access) | OOM at **15 GB** |
| shard 2 | `env_01XWNfnUJbtN9JJfR3DQPJxY` (New) | OOM at **13.94 GB**, ceiling 14 GB |
| shard 3 | `env_01AioCkYntxXbGYXw9qeSCo7` (Default) | OOM at **13.3 GiB** peak RSS vs a **13.34 GiB** cgroup limit, in **LP matrix construction**, ~11.5 min in |

The parent container is the same size (15 GB total). Shard 3 reached matrix construction with the
seam flow limits armed and the data confirmed, and died building the CSC matrix. `replay_keeper.py
--reuse-solved` is not a lever: it byte-copies whole years from another bundle and does nothing for
a single year's peak.

### 1a. CORRECTION — an in-repo memory lever DOES exist, and the first four shards all missed it

This section first read *"no in-repo memory lever exists."* **That was wrong**, and the correction
matters because it is the difference between "MISO cannot be solved here" and "MISO can be solved
here." `src/market_sim/model/lp/model.py:607-614` carries a purpose-built escape hatch whose comment
describes this exact failure:

> *"Memory-constrained boxes can cap HiGHS's thread count (parallel dual simplex keeps per-thread
> factorization workspaces; **on a ~12 GB plant-level ISO-year LP the default all-cores run can spike
> past a small container's RAM and get OOM-killed**). Unset keeps HiGHS's automatic threading; **the
> LP optimum is identical either way.**"*

* **`MARKET_SIM_HIGHS_THREADS=1`** — caps HiGHS's thread count. **Solution-neutral by the code's own
  statement**, so it is not a model change and needs no gate. This is the lever.
* **`MARKET_SIM_HIGHS_LEAN=1`** — additionally sets `simplex_scale_strategy=0`.
* **`MARKET_SIM_MEM_DEBUG=1`** — the built-in per-stage RSS tracer (`_rss()`, model.py:576), which
  logs `MEM <stage>: VmRSS/VmHWM` and locates which build stage spikes. Its own comment notes the
  plant-level ISO-year LPs *"run within ~1 GB of the calibration box's ceiling"* — i.e. this margin
  is a known, routine condition of the repo, not a new regression.

**`OMP_NUM_THREADS` does NOT reach HiGHS** — HiGHS reads its own option, which is precisely why the
env var exists. Shards 1-4 set allocator and BLAS variables but not this one, which is why they all
died at the same place. Two further levers are already spent and should not be re-attempted:
`presolve` is already `"off"` (model.py:620), and the pairwise `sp.vstack` chain was already
replaced by `_vstack_csr_free` for this same OOM.

**Any future MISO/PJM plant-level solve should export all three variables before the solve.**

**Consequence for the lane:** no MISO arm — the 2021 envelope screen, the 2022 ladder arm, or any
future one — can be evaluated until a larger environment exists. Every shard stopped and reported
rather than pushing a partial bundle, which is the correct behaviour (rule 32(c)7).

## 2. BIOMASS IS SELF-SCORED — the "actual" is the model's own input

`_must_run_profiles` injects biomass from EIA-923 and the code states the consequence outright:
*"so the injected biomass equals the benchmark it is scored against"* (`run_calibration_full.py`).
Confirmed against the committed bench (`frontend/data/backcast/bench/MISO/<year>.json.gz`):

| year | `gmModel.biomass` | bench `classFull.biomass` | Δ |
|---|---:|---:|---:|
| 2023 | 8.1281 | **8.1281** | 0.0000 |
| 2024 | 7.2399 | **7.2399** | 0.0000 |
| 2025 | 2.9283 | **2.9283** | 0.0000 |

**That row is structurally incapable of failing C1.** The same is true of `OTHER` (2023: model
10.3253 = bench 10.3253). Two classes therefore pass the fuel-mix gate for free, and the D-10
free-class count (`C1 all 16/16 · free 12/12`) counts them as scored.

This is a **validation gap, not a dispatch error** — and it is the reason the dashboard cannot show
a biomass miss however large the underlying error is.

## 3. THE SUBSTANTIVE DEFECT — two thirds of MISO biomass is behind-the-meter cogen

MISO 2023 biomass in EIA-923 is **8.713 TWh**, and its composition is the finding:

| fuel | TWh | what it is |
|---|---:|---|
| `BLQ` | 3.610 | black liquor — paper-mill chemical-recovery boilers |
| `WDS` | 2.748 | wood solids — the same mills |
| `LFG` | 1.413 | landfill gas |
| others (`MSN`/`MSB`/`OBG`/`AB`/`OBS`/`SLW`) | 0.942 | |
| **total** | **8.713** | |

**By CHP flag: 5.844 TWh (67 %) is `chp=Y`.** `BLQ`+`WDS` alone are **73 %** of the total. That is
industrial cogeneration whose host steam and on-site consumption never reach the ISO grid.

The injection takes EIA-923 **net generation**, shapes it by month and splits it across zones by
demand share — with **no host-steam / BTM carve-out**, unlike the fossil CHP classes. The codebase
knows the problem exists; two lines away in the same file it says *"CHP kept on EIA-923 — the
host-steam split is absent from CAMPD net."* The model holds out only ~0.585 TWh (model 8.128 vs
923's 8.713, a flat ~7 % across every year) where **5.844 TWh is CHP**.

**Net effect: roughly 5–6 TWh/yr of behind-the-meter cogen injected as price-insensitive must-run
grid supply**, displacing marginal gas. MISO 2023 `CC_REGULAR` is **−6.8 TWh** against bench (model
135.0 vs 141.8) — the same order of magnitude and the same direction. Not proof of causation, and
stated as such; it is the reason this is worth an arm.

Scale: ~0.9 % of MISO load. **The injection "applies to EVERY ISO now"** (its own comment), so the
same construction is live in all seven.

## 4. Why this is the strongest remaining arm

Unlike the seam work — whose entire blast radius is the pre-2023 holdout rungs (rule 30(c): they
cannot certify or decertify) — a biomass BTM split **touches 2023–2025 and can therefore move the
keeper itself**. It is a rule 14 `[R-ACCURATE]` repair with a real forward analogue: EIA-923 carries
the CHP flag per plant, so the split regenerates for any year and responds to changed conditions
(rule 13's forward test). Zero new free parameters — it is a partition on a published boolean.

**It cannot be screened until the memory ceiling is lifted.** It is specified here so the next
session with adequate RAM can run it immediately.

## 5. What this session leaves behind, all merged

* EIA-930 MISO interchange back-filled to 2020–2022 (241,872 rows, keyless bulk route). Keeper
  proven unmoved: 78,831 shared 2023 keys, **zero** value changes; all 24 keeper-year envelope rows
  recompute identical.
* `MISO_SEAM_LADDER_BY_YEAR[2022]` derived and committed (rule 23 basis: the source data updated).
  2023–2025 untouched and proven so.
* The pre-2023 seam fallback root cause (bang-bang seam: 2021 at its rail in 8,654 of 8,760 hours
  vs 3/1/2 in the ladder-priced keeper years).
* The 2020/2021 price comparison from the MMU's published annual prices — **2020 is over-priced by
  +26.9 % to +46.8 %**, which qualifies miso-251's reading of 2020 as the clean out-of-regime year.
* Proof the 2025 EIA-923 blackout is blocked on EIA, not on us.

**Nothing was deleted (rule 31).** No bundle was produced to retain — all three shards OOM'd before
writing one.
