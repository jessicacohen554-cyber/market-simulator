# PRECOMMIT — miso-253: host-steam / BTM partition of the injected must-run residual classes

```
SESSION    : miso-253
ISO        : MISO   (the mechanism is ISO-GENERIC — the injection runs in all seven)
MECHANISM  : ScenarioConfig.mustrun_chp_btm_holdout  (NEW, default off, byte-identical off)
KEEPER     : 2026-09-09-miso-250-ep-gas — bundle results/calibration/miso_fuelvintage_A
             (CALIBRATED; C3c ledgered caveat, every other criterion PASS)
CONTROL    : that COMMITTED bundle. Rule 29(b) form 4. NO CONTROL SOLVE.
SCREEN YEAR: 2023  — named HERE, before any solve, on measured FOOTPRINT (§4)
```

Written and pushed **before the first LP**. Every number in §2–§5 is zero-LP: it comes
from EIA-923, EIA-930 and the committed keeper bundle, not from any solve of this arm.

---

## 1. The defect (rule 14 `[R-ACCURATE]`)

`scripts/run_calibration_full.py::_must_run_profiles` injects each residual class's
EIA-923 **net generation** as price-insensitive must-run grid supply, with **no
host-steam carve-out**.

Every *fossil* cogen class has had one for years: `classify_plant` splits gas cogens into
their own `CC_CHP` / `CT_CHP` / `ST_CHP` classes, and `data.chp.chp_btm_pct` then holds a
measured host share out of them; coal cogen has `coal_chp_overrides`. But
`classify_plant` returns `"biomass"` **regardless of the CHP flag**, and everything else
falls to `"OTHER"` the same way — so the two injected classes are exactly the two that
never received the partition.

They are also the two where cogeneration *dominates*. MISO 2023, measured:

| model class | TWh | of which `chp=Y` | what it is |
|---|---:|---:|---|
| `biomass` | 8.128 | 5.805 (71.4 %) | BLQ 3.610 + WDS 2.748 — paper-mill recovery boilers; LFG 1.413 is 96 % non-CHP and stays |
| `OTHER` | 10.325 | 6.709 (65.0 %) | BFG 3.054 + OG 2.859 — integrated-steel blast-furnace and coke-oven gas; PC, WH, PUR |
| **pair** | **18.453** | **12.514 (67.8 %)** | |

That electricity powers the host mill. It never reaches the ISO grid, and injecting it as
must-run supply displaces marginal gas.

## 2. Independent grid-side corroboration — and why this is not a self-referential repair

The finding this session inherited (`FINDING-miso252` §2) established that biomass is
**self-scored**: bench and injection are the same EIA-923 number, so the class cannot fail
C1 however wrong it is. A partition read only off that same number would be equally
unfalsifiable. It is not: there is an independent authority.

**EIA-930's `OTH` bucket is MISO's own BA telemetry** of everything outside
coal / gas / nuclear / solar / hydro / wind. Two facts make it admissible here:

1. **MISO reports no `OIL` or `BIO` bucket**, so the model's `biomass`, `OTHER` *and*
   `oil` classes must all live inside `OTH` — a clean like-for-like union.
2. **The split is exhaustive, not a residual.** MISO's 930 fuel-type series sums to
   **616.519 TWh** against the BA's own reported net generation of **616.516 TWh** in
   2023 — a gap of 0.0002 %. Nothing is hiding in an unmapped bucket.

| MISO | LP-side "other" (biomass+OTHER+oil) | EIA-930 `OTH` | ratio | **armed** |
|---|---:|---:|---:|---:|
| 2023 | 18.916 | 4.491 | 4.2× | **6.402** |
| 2024 | 15.920 | 2.737 | 5.8× | **5.418** |
| 2025 | 9.114 | 3.650 | 2.5× | **3.852** |

The partition lands the injection on the *same order* as the telemetry, and still slightly
**above** it — the correct side, because the flag is a partition, not an export model (a
cogen may export some of its output; none of it is claimed back).

**Stated at the gate, because it limits the claim:** this comparator does **not**
generalise. Measured across all seven ISOs the ratio runs from 0.55 (PJM 2025, model
*below* telemetry) to a *negative* `OTH` in CAISO (a known 930 artifact). Any other ISO
adopting this must establish its own grid-side authority first (rule 25 `[R-ISO-SCOPE]`).

## 3. Construction, and what it is not

**One seam.** The filter lives in `_eia923_frame`, scoped to `_INJECTED_MUSTRUN_CLASSES`,
and drops rows whose plant carries the published EIA-923 CHP flag. Both roads to those
classes — the injection (`_must_run_profiles` → `_reconciled_mustrun_class`) and the
benchmark (`_benchmark_eia923_frame`) — pass through it, so **bench and model move in
lockstep and the partition cannot manufacture a miss**.

- **Row grain, not plant grain.** A mill reporting a `chp=Y` recovery boiler and a
  `chp=N` grid unit under one plant code keeps the grid unit.
- **Rule 19 `[R-ONE-MECH]`.** Gas cogen is already partitioned; coal cogen has its own
  channel; `_plant_class_shares` filters to `_BACKFILL_TARGET_KLASSES` before it ever
  sees these rows; `_vintage_completeness` reads `generation` directly and is untouched.
  Nothing stacks.
- **Rules 21 / 24 — zero free parameters.** A partition on one published per-plant
  boolean. No share, no threshold, no level. Registered in `_CACHE_KEY_OPTIONAL_FIELDS`
  + `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` + `TIER_TAGS` in the same commit as the field
  (the nyiso-119 discipline); dropped at its `False` default, so **every pre-existing
  cache key in every ISO stays valid** (test: `test_default_cache_key_is_unmoved_by_the_new_field`).
- **Rule 13 `[R-MEASURED]` forward test.** EIA-923 carries the CHP flag per plant per
  vintage, so the identical construction regenerates for a forward year and re-partitions
  a plant whose cogen status changes. It is an input to what the grid is supplied with,
  never an outcome the dispatch is fitted to.

**What it does NOT close, said plainly:** biomass and `OTHER` remain **self-scored**. The
single seam feeds bench and injection alike — which is what keeps the arm honest, and also
what leaves `FINDING-miso252` §2's validation gap open. Closing that needs a bench sourced
independently of the model's own input; EIA-930 `OTH` is the named route, and it is **not
this flag**.

## 4. Screen year — 2023, named on footprint, never on the residual

Rule 29 requires the screen year to be the year the mechanism's own **measured footprint**
is largest. Measured `chp=Y` energy inside the injected pair:

| year | footprint (TWh) | vintage |
|---|---:|---|
| **2023** | **12.514** | complete (2,994 rows, 132 biomass plants) |
| 2024 | 10.502 | complete |
| 2025 | 5.262 | **partial** — the known EIA-923 blackout (37 biomass plants) |

**2023 wins on footprint and is the only defensible choice anyway**: 2025's number is the
vintage *carry*, not the mechanism, so a 2025 screen would measure the wrong object.
The residual played no part in this choice.

### Exact pre-solve prediction (zero LP, reproducible)

| year | injected pair off → armed | removed | rows dropped |
|---|---|---:|---|
| **2023** | 18.4534 → **5.9398** TWh | **12.5136** | 170 of 2,994 |
| 2024 | 15.5224 → 5.0207 | 10.5017 | 165 of 3,076 |
| 2025 | 8.7612 → 3.4991 | 5.2621 | 97 of 1,014 |

Per class, 2023: `biomass` 8.1281 → **2.3233** (−5.8048); `OTHER` 10.3253 → **3.6165**
(−6.7088). No carry fires in 2023 (complete vintage), so the reconciled path equals the
raw frame exactly.

## 5. G-DRIFT (rule 29(b)) — form 4 is VALID, no control solve

The keeper's own solve sha `7167b99a` is **unreachable**: this is a shallow clone and the
miso-250 branch was auto-merged and deleted. The audit base is therefore `1274b44e^` =
**`25675896`**, the main-line commit immediately before the miso-250 promotion —
justified because **the promotion commit itself touches no solve-path file** (verified:
`git diff --stat 1274b44e^ 1274b44e -- src/market_sim scripts/run_calibration*.py scripts/lib data/raw/_validation-source data/raw/reference` is empty), and the promotion was a
`replay_keeper --set` config change, not a code change.

23 solve-path files changed. **Every hunk classified INERT for a MISO 2023–2025 backcast:**

| file(s) | classification |
|---|---|
| `runner.py`, `data/renewables.py`, `data/curtailment_share.py` (new), `scripts/lib/spp63_g5.py` (new), `data/raw/reference/spp_curtailment_share.csv` | SPP-only branch (`iso == "SPP"`) + default-off flag absent from the keeper recipe |
| `pipeline/ttc.py`, `data/fuel/hubs.py`, `config/constants.py`, `config/solve_surface_declared.py`, `data/raw/reference/reliability_floor_coeffs_NYISO.csv` | NYISO-only (`if iso != "NYISO": return ttc`); constants change is a pure addition with **zero** MISO mentions and **zero** removed non-comment lines; the two new declared surface names are dropped at their as-committed hashes, so **MISO does not re-key** |
| `model/interchange/{spec,caiso,__init__}.py` | CAISO-only (`caiso_per_hub` predicate) |
| `data/fuel/basis/ercot.py`, `data/raw/_validation-source/actual_lmp.json` | ERCOT-only; the LMP benchmark diff is 10 leaves, **all ERCOT** |
| `data/outages.py` | `ST_GAS_PEAKER_PLANTS` gains 11 **PJM** plant codes — **measured**, not assumed: zero overlap against MISO's 381-plant bin sheet |
| `data/raw/_validation-source/calibration_reference.json` | 44 changed leaves, 43 MISO — **all `None → value` for year 2020 only**. 2023/2024/2025 untouched |
| `data/raw/.../MISO_2020_renewable_capacity.csv` (new) | MISO, but **2020-only** |
| `scripts/lib/holdout_policy.py`, `scripts/run_calibration*.py` (holdout-gate removal) | a **gate**, not a mechanism — removing it changes no LP. Surviving consumers are the scorer and the forecast hindcast; `tier_for_year` returns TRAIN for 2023–2025 |
| `scripts/lib/forecast_parity_registry.py` | consumed only by `check_forecast_parity.py` (CI) |
| `scripts/run_calibration*.py` (rest) | SPP / CAISO-replay / ERCOT flags, all default `None`/`False`; plus `%`→`%%` help-string escaping |

**All hunks INERT ⇒ the committed keeper bundle is the control. No control solve is spent.**

## 6. The screen gate — STRUCTURAL, STOP-ONLY, and NOT keyed to the residual

Rule 29: the screen asks whether the mechanism does what its own arithmetic says. **It may
kill this arm; it may not promote it.** It contributes to no determination.

**It is explicitly NOT gated on C1 `CC_REGULAR` improving, nor on C3a improving.** Those
are the *target* residuals; gating on them is the fitted-mechanism selection rule 1
`[R-STRUCT]` forbids, done one year at a time. They are **reported at full magnitude,
in both directions**, and a failure to improve does **not** kill the arm.

| gate | test on the 2023 screen | STOP if |
|---|---|---|
| **G-1 footprint confinement** | the injected must-run arrays for `biomass` / `OTHER` equal 2.3233 / 3.6165 TWh | either differs by > 0.01 TWh, or **any other** injected class moves at all |
| **G-2 response direction & order** | the LP must replace the withdrawn 12.5136 TWh; measure Δ(total model generation of all dispatchable classes) + Δ(net imports) | the replacement is **negative**, or falls outside **[60 %, 140 %]** of 12.5136 TWh (a response of the wrong sign or wrong order means the seam is not doing what the arithmetic says) |
| **G-3 lockstep identity** | `gmModel.biomass` vs bench `classFull.biomass`, and the same for `OTHER` | they diverge by > 0.0001 TWh — i.e. the partition reached one side only and manufactured a miss |
| **G-4 off-path load-bearing flip** | C2 `sysvol`; C1 on the classes the mechanism makes **no** claim about (`nuclear`, `wind`, `solar`, `hydro`) | any of these flips **PASS → FAIL** |
| **G-5 governance** | C6 must stay PASS; `run_config.json` must record `mustrun_chp_btm_holdout: true` | C6 fails, or the posture is not recorded (rule 24) |

If the screen clears, the full span `--year 2023 2024 2025` runs as ONE invocation and ONE
bundle (rule 16 `[R-ALLYEARS]`); the screen bundle is a throwaway diagnostic probe, never
registered, never a keeper, and its year is re-solved inside the full bundle (rule 29(2)).

## 7. Execution protocol

- **Rule 32 `[R-SHARD]`: the parent runs NO LP.** All of §1–§6 is zero-LP and was done in
  the parent. The screen runs in a shard pinned to a full 40-char SHA.
- **The memory ceiling is the live risk** (`FINDING-miso252` §1b): MISO's single-year LP
  peaked at **13.29 GiB**. Every shard **prints its own ceiling first and STOPS** if it is
  under ~14 GiB. `/sys/fs/cgroup/memory.max` (v2) is read where it exists; this parent is
  **cgroup v1 with no limit and 16.46 GB MemTotal (15.70 GiB)**, so the check must handle
  both layouts rather than assuming v2.
  - **New information miso-252 did not have.** Its 13.29 GiB measurement was taken in the
    *Default* environment (13.344 GiB cap). Its one attempt in *Full access* (15.70 GiB)
    OOM'd at 15 GB — but that was **shard 1, before the lean settings existed**. The
    combination *(Full access ceiling + `MARKET_SIM_HIGHS_THREADS=1` + `_LEAN=1`)* has
    **never been tested**, and against a 13.29 GiB peak it has ~2.4 GiB of headroom. That
    is the hypothesis the screen shard tests, at the cost of one shard, with a cheap
    early stop if the ceiling reads low.
  - **Do NOT re-test** anything miso-252 already measured: the HiGHS thread cap as a
    *fix* (ineffective there), allocator/BLAS vars, `presolve` (already off),
    `_vstack_csr_free` (already landed), `miso_seam_export_limit=false` (saved 18 MiB).
- **Rule 31 `[R-RETAIN]`:** no bundle is deleted. `.gitignore` discharges
  delete-before-merge; the promotion question goes to the owner in the final report.
- **Rule 15 `[R-DASHBOARD]`:** whatever comes back — keeper or rejection — is registered
  this session.

## 8. Status of the code at this SHA

Implemented, tested and gate-clean in the parent, with no LP spent:

- 13/13 new tests pass (`tests/unit/data/test_mustrun_chp_btm_holdout.py`), covering
  byte-identity off, scope (gas CHP untouched), row-grain, monthly-shape consistency,
  bench/injection lockstep, the partitioned vintage carry, and all four cache-key guards.
- 844 `tests/unit/config` pass; `test_biomass_mustrun_injection` + the EIA-923 backfill
  curation suite pass unchanged (16/16).
- `scripts/check_mechanism_matrix.py --base origin/main` **exits 0** — base row + a cell
  in all seven ISO shards (MISO `O`; the other six `U`, since the injection is ISO-generic
  and rule 25 transfers no verdict).
- Zero new anchor churn: 257 unresolvable anchors at HEAD, 257 with this change (the
  field is appended at the END of the field list, per the convention stated in
  `scenarios.py` itself).

**One pre-existing failure, NOT introduced here and not repaired here:**
`tests/regression/test_persisted_identity.py::test_solve_surface_fingerprint_is_pinned[NYISO]`
fails identically at HEAD with this branch's changes stashed. It is nyiso-224's constants
landing; `scenarios.py` is not one of the seven `SURFACE_MODULES`, so nothing in this
change can move any ISO's fingerprint. It belongs to the NYISO lane.

---

# ADDENDUM A — a weakness in §2, recorded BEFORE the screen result

Written after the screen shard launched and **before any solve number came back**, because
it qualifies a claim §2 already makes and the record must not be tidied afterwards.

## A.1 The partition breaks a reconciliation that currently holds almost exactly

The committed 2023 benchmark's `classFull` total is **616.259 TWh** against MISO's EIA-930
reported net generation of **616.516 TWh** — a gap of **−0.04 %**. Armed, the bench total
falls to **603.746 TWh**, i.e. **−2.07 %** against the same grid total.

That is a real cost of the arm and it is stated as one. §2 did not mention it.

## A.2 But that aggregate match is NOT evidence of a clean benchmark

Decomposed by fuel family, 2023, bench `classFull` vs the EIA-930 buckets:

| family | bench | EIA-930 | bench − 930 |
|---|---:|---:|---:|
| coal | 185.787 | 174.961 | **+10.827** |
| gas | 207.651 | 241.177 | **−33.526** |
| nuclear | 87.177 | 87.842 | −0.664 |
| wind | 91.715 | 91.721 | −0.006 |
| solar | 6.348 | 6.348 | +0.000 |
| hydro | 9.979 | 9.980 | −0.001 |
| **other** (oil+biomass+OTHER+OTHER_FOSSIL) | 27.602 | 4.491 | **+23.111** |
| **TOTAL** | **616.259** | **616.519** | **−0.259** |

The −0.259 TWh headline is the residue of **68.1 TWh of absolute per-family discrepancy**
that happens to cancel. So "the bench total matches the grid" is a coincidence of
offsetting errors, not a property worth protecting — and the two largest errors point in
exactly the directions this arm moves: **+23.1 TWh too much "other" and −33.5 TWh too
little gas.** Armed, the "other" family error falls **+23.111 → +10.598**.

## A.3 The competing hypothesis, named because it would INVALIDATE the premise

§2 treats EIA-930 `OTH` as a like-for-like comparator for the model's `biomass` + `OTHER`
+ `oil`. There is a coherent rival reading in which it is not:

> MISO's BA telemetry may label a blast-furnace-gas or coke-oven-gas **steam** unit as
> `NG`, not `OTH`. If ~12.5 TWh of the chp=Y block is telemetered as gas, then 930's `NG`
> already contains it, `OTH` is not a pure comparator, and the cogen **is** on the grid —
> in which case the injection is right and this arm's premise is wrong. On that reading
> the honest pairing is bench (gas+other) 235.25 vs 930 (NG+OTH) 245.67 = **−10.4 TWh**,
> i.e. the benchmark under-counts *gas*, and the repair is on the gas side, not here.

**This session cannot discriminate the two readings at zero LP, and does not claim to.**
The argument that favours §2's reading is a structural one rather than a measurement: a
paper mill's recovery boiler serving its own load is not a MISO market participant and
would not appear in the BA's telemetry under *any* fuel label. That is a reason, not a
proof. What would actually discriminate it is a per-generator EIA-930 fuel-attribution
source, or MISO's own registered-resource roster — neither is on disk, and both are
**intake work, not a solve**.

Consequence, stated plainly: **§2's corroboration is weaker than §2 states.** It shows the
"other" family is over-counted by 23.1 TWh on the 930 basis and that the partition removes
about half of it; it does **not** establish that 930 `OTH` is the exact quantity the
injected classes should equal.

## A.4 New pre-registered gate — REPORTED, never a kill

| gate | test on the 2023 screen | disposition |
|---|---|---|
| **G-6 bench-total consequence** | bench `classFull` total, armed, against EIA-930 net generation 616.516 TWh; and the per-family table above recomputed armed | **REPORTED at full magnitude, in both directions. NOT a kill gate**, because the bench moving is the intended behaviour of a bench-and-model seam, and killing on it would be gating the screen on a residual (rule 1 `[R-STRUCT]`, rule 29). Expected armed: total 603.746 (−2.07 %), "other" family error +23.111 → +10.598 |

The five STOP gates of §6 are unchanged. G-6 joins the reported set, not the kill set.

## A.5 What this does to the arm's standing

The arm remains worth its one screen shard: it is a rule 14 `[R-ACCURATE]` repair with zero
free parameters, a real forward analogue, and a measured 12.514 TWh footprint whose sign
matches the two largest benchmark family errors. But the **promotion bar is higher than
§2 implied.** On this record, a screen that clears G-1..G-5 is evidence the *seam works as
built* — it is **not** evidence that the level it lands on is right, and this session will
not present it as such. The competing hypothesis of A.3 stays open and goes to the owner.
