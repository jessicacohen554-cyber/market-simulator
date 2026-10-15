# FINDING — UC-SPP-SPIN: SPP's ≥ ½ Spinning share as a synchronized sub-requirement

**Lane:** UC-SPP-SPIN (engine/spec) · **Chartered by:** UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`), owner ruling r13 (2026-10-15) · **Date:** 2026-10-15 · **Branch / PR:** `claude/uc-spp-spin`, #7261 (not merged).
**Nothing tuned, nothing registered.** SPP default off (`spp_spinning_reserve_share = False`).

## 0. Result

| item | status |
|---|---|
| Spec | Done. `_spp_design` adds a nested class-1 family `spp_spinning_reserve` = ½ × the Contingency Reserve requirement, with one shortfall step at $250/MW. |
| Rule 19 | One mechanism. The SPP family system is extended (the NYISO 10-in-30 nesting); no second reserve system. `lp/reserve_rows.py` is untouched. |
| Synchronized | The UC stage restricts class 1 to integer-cluster members. The uc-1.6 u-gate then carries it on committed headroom (window), and P1 caps it at a·u/n. Offline fast-start CTs still count toward the pooled requirement. |
| Registry | `spp_spinning_reserve_share` (SPP-only; refused without `unit_commitment_milp`). It is in `_CACHE_KEY_OPTIONAL_FIELDS` at False and in TIER_TAGS at 1. Matrix row added; cells are SPP `U`, other ISOs `.` (ISO-exclusive). |
| Tests | 8 new tests (1 zone / 24 h). Fast lane: 11,708 passed, 0 failed. |
| Repro (SPP 2020) | **The sub-row binds.** The spin dual is > 0 in 1,944 h, and committed steam/coal headroom at peak rises from 0.42 to 0.80 GW. C3a +36.8 % → +30.1 %; C3b 0.421 → 0.355. The extra commitment is carried by coal, not ST_GAS (§4). |

## 1. Sources (rule 5)

- `SPP_RSG_SPIN_MIN_SHARE = 0.5`: RSG Operating Process 0820EXT00002 v4.0, Definitions p. 5: "At least half of the Contingency Reserve shall be Operating Reserve - Spinning" (transcribed in PRECOMMIT-spp-55 §2).
- `SPP_SPINNING_RESERVE_VRL = 250`: Integrated Marketplace Protocols v119 §4.1.4, Exhibit 4-1 (printed p. 71), "Spinning Reserve Constraint … for each SPP Balancing Authority Area: $250". Under §4.1.4.1(5) the requirement is reduced by the violation, so the shortfall is modelled as one step at $250 spanning the whole sub-requirement.

## 2. Construction

```
class 0 (pooled CR):  ΣP + R0 ≤ Σ_{elig} pmax·a        R0 ≥ req          ($275/$550/$1,100 steps)
class 1 (Spinning):   ΣP + R1 ≤ Σ_{elig ∩ integer} cap  R1 ≥ ½·req        ($250 step)
                      cap = pmax·a·u/n in the UC window (uc-1.6), a·u/n·pmax in P1
```

- The class-1 headroom set H_sync is a subset of H_all. The two rows are therefore exactly "CR ≥ req, of which ≥ ½·req Spinning": the same MW counts in both, as in the NYISO cascade.
- `ReserveDesign.synchronized` is passed as the kwarg `reserve_synchronized`. `pipeline/uc.py::synchronized_reserve_overrides` intersects class 1 with `params.integer_member_gens`, after budget-pin demotion, for the windows. `solve.py` composes the same override into `p1_kwargs_prep`, inside the existing UC hunk.
- P0 keeps the unrestricted design. There class 1 has the same set as class 0, so the spin row is inert.

**Declared limitations**
- (a) An online fast-start CT's headroom is not credited to Spinning, because the LP has no state for it. Measured below: about 30 MW at peak, ≈ 4 % of the spin requirement.
- (b) Nuclear, hydro and non-cluster rows are out of class 1. Their headroom is ≈ 0 when running.
- (c) The integer gate is by min-down / start cost, not measured start time (as in FIX-6).

## 3. Tests (`tests/unit/model/uc/test_window_spinning_share.py`)

The toy fleet is: baseload 60 MW; ST_GAS 2 × 100 MW (the integer cluster, mlf 0.5); CT 150 MW (fast-start). Night load is 80 MW. CR is 80 MW, so spin is 40 MW.

| test | asserts |
|---|---|
| without the spin row | ST off at night (u = 0, h 0–6); the CT's offline 150 MW covers the 80 MW |
| with the spin row | u ≥ 1 every hour; spin = 40 MW ≤ 100·u − P_ST; pooled = 80 MW; 2T rows u-gated |
| override | class 0 keeps [ST, NUC, CT]; class 1 keeps [ST] only; no synchronized class → `{}` |
| design | off → one family, no kwarg; on → spin requirement = ½ CR, class 1, $250 step, eligibility (2, n) |
| refusal | armed without UC → ValueError |
| `solve_dispatch` | the P1 cold route accepts the kwarg (regression for the first shard's TypeError) |
| negative check | with the override stubbed out, the "with spin" test fails (u = 0 at night) |

## 4. Repro — SPP 2020, arm B + UC + reserves + spin (uc-1.6)

The recipe is `closeout_spp_nuc_span` with `unit_commitment_milp=true`, `st_gas_mustrun_per_plant=false`, `energy_reserve_coopt=true` and `spp_spinning_reserve_share=true`.

- Shard `session_01GLmY71DzMJi1ScnJWKNp4P` at pin `994a7905`. Bundle commit `8254198720ec135b72c7758af7faf1672302f68b` on `claude/ucspin-spp-b-res-spin-2020`: 21 files, including `dispatch/2020_P1.parquet`, `uc_schedule`, `uc_uplift`, `unit_marginal` and `reserve_family`. I fetched and read the bytes.
- The first attempt, at `4c194477`, stopped at P1 on a `solve_dispatch` TypeError. That was fixed in `994a7905`, and its UC stage reproduced identically.
- Readings come from `data/fix6/repro_metrics.py`, plus the `reserve_family` sidecar and `unit_marginal` headroom. The EIA-923 values are the benchmark `classFull`.

| reading (2020) | EIA-923 | keeper | FIX-6: arm B + res (uc-1.6) | **+ spin sub-row** |
|---|---|---|---|---|
| COAL_PRB TWh | 66.13 | 63.10 | 61.97 | **66.11** |
| COAL_LIGNITE TWh | 10.83 | 8.61 | 9.45 | **9.42** |
| CC_REGULAR TWh | 45.11 | 46.78 | 47.26 | **45.93** |
| ST_GAS TWh | 12.08 | 9.47 | 5.30 | **4.83** |
| CT_PEAKER TWh | 8.86 | 15.94 | 19.75 | **17.65** |
| C3a | — | +27.7 % | +36.8 % | **+30.1 %** |
| C3b (NRMSE) | — | 0.345 | 0.421 | **0.355** |
| C8 ST_GAS forced share | — | 15.7 % | 2.0 % | **2.6 %** |
| Hours with a CT_PEAKER unit marginal | — | 1,559 | 2,848 | **2,692** |
| Top-100 load h: committed integer headroom, ST_GAS / coal / CC (MW) | — | — | 5 / 418 / 0 | **90 / 710 / 0** |
| Top-100 load h: ST_GAS committed online | — | 3.67 GW | 1.30 GW | **1.47 GW** |
| All hours: committed integer coal headroom (MW mean) | — | — | 1,883 | **2,401** |
| Online CT headroom at top-100 h (bias (a)) | — | — | 30 MW | **32 MW** |
| Pooled CR: requirement / shortfall / dual | — | — | 1,413 MW / 0 / $0 | 1,413 MW / 0 / **$0** |
| **Spin: requirement / shortfall / dual** | — | — | — | 707 MW mean / **0** / **> 0 in 1,944 h**, mean $0.80, p99 $10.2, max $65.6/MW |
| Unserved MWh | — | 0 | 0 | **0** |
| Uplift ÷ λ·load | — | — | 0.08 % | **0.31 %** |
| Mean price N / S ($/MWh) | — | — | — | 20.82 / 20.93 |
| Class 1 rows kept (integer members / eligible) | — | — | — | 401 / 1,275 |
| UC windows Optimal / time-limit hits | — | — | 365 / 0 | 365 / 0 |
| UC stage s; year total s | — | — | 2,254; 2,662 | 940; 1,239 (different container) |
| Peak RSS (cgroup) GiB | — | — | 7.89 | 7.78 |
| D-4 FAIL rows | — | — | 0 | **1**: coal_mustrun at plant 2079 binds 45 h (7.6 GWh), measured zero in 82 % of hours |

**Reading.**
- The spinning sub-requirement **binds** where the pooled family did not. The UC now holds ≈ 0.8 GW of committed slow-start headroom at peak, against ≈ 0.42 GW without it. That is ≥ the ~0.73 GW spin requirement at peak.
- **Coal carries most of it**: +0.3 GW of committed headroom at peak, +0.5 GW on average. Coal PRB generation therefore rises 4.1 TWh, which lands on the EIA-923 value (66.11 vs 66.13). CC moves toward measured (−1.3 TWh), CT_PEAKER falls 2.1 TWh, C3a improves 6.7 pp and C3b improves 0.066.
- **ST_GAS does not recover** (4.83 TWh vs 12.08 measured; 1.47 GW online at peak vs 3.67 GW in the keeper). The spin MW are cheapest on coal that is already near-committed, not on steam gas. The arm-B ST_GAS gap is therefore not a spin object. UC-DIAG cause #2 (DA-forecast commitment) and the per-unit `ut_h` remain the open candidates.
- **Bias (a) is small.** Online CT headroom at peak is ≈ 30 MW, ≈ 4 % of the spin requirement.

**Caveats**
- One year only, and no control solve: FIX-6 is the comparator at the same engine (uc-1.6, plus this PR's inert-when-off code).
- Uplift rises from 0.08 % to 0.31 %, as committed headroom costs no-load.
- The new D-4 row is a pre-existing floor (`coal_mustrun_per_plant`, keeper recipe) that now binds in 45 hours; it did not bind in FIX-6. I have not traced the cause. The magnitude is small (7.6 GWh), but it is a FAIL row the desk should see.
- `campd_split_remap_companions` logs the same pre-existing provenance warning as FIX-6 and the keeper.
- Wall times are from different containers and are not comparable.

**Disclosures.** The shard ran `uv sync` once (no venv in the container). The bundle is not registered and not on `main`; it is held on the shard branch only.
