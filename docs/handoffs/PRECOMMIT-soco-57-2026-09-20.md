# PRECOMMIT — SOCO-57 (2026-09-20): `measured_cc_heat_rates`, the last thermal class still priced off an unmeasured annual average

**Lane** SOCO-57 · **DATA PROFILE** soco · **Model** Opus 5 (rule 27 `[R-PUSH]` — scope writes
`src/market_sim/` and `scripts/`).
**Control of record** `2026-09-20-soco56-perunit-outage`
(`results/calibration/soco56_perunit_outage`), rule 29 `[R-SCREEN]` (b) **form 4**, no control solve.
**Arm** `measured_cc_heat_rates = True` — ONE new default-off `ScenarioConfig` field, one new derive,
one new per-ISO artifact.

**EVERY NUMBER BELOW WAS WRITTEN BEFORE ANY LP WAS SOLVED.** Phase 0 is entirely zero-LP
(rule 32 `[R-SHARD]` (a)): `fleet_only` rebuilds off the keeper's own `meta.json`, the keeper's
committed hourlies, the raw CAMPD unit-level files and the committed EIA-860 / eGRID artifacts.

---

## 1. THE OBJECT, AND WHAT PHASE 0 DECIDED BETWEEN

The handoff named three candidate readings of the 2024 `CC_REGULAR` failure and required phase 0 to
pick between them **on measurement**. It did.

| reading | verdict | why |
|---|---|---|
| **(1) HEAT RATE** | **TAKEN** | The spread test as posed FAILS — model spread 1.381 vs measured 1.403, essentially identical. But the ERROR IS CONCENTRATED, and **the three plants the model prices too dear are, in rank order, the three it most under-dispatches.** §2. |
| **(2) AVAILABILITY at Lowman** | **SUBSUMED BY (1)** | Lowman's miss is economic, and (1) NAMES ITS CAUSE: a $5.10/MWh heat-rate error. §2.3. |
| **(3) ST_GAS denominator** | **STILL ROUTED** | SOCO-56 §9 item 3 bounded it at ≤ 0.0071 TWh. Phase 0 did not kill (1), so (3) is not taken — one lever, clean A/B (rule 19 `[R-ONE-MECH]`). |

---

## 2. THE MEASUREMENT

### 2.1 Model CC heat rate vs CAMPD-metered steady state (2024, net basis, pf = 0.975)

| plant | name | cap MW | model | measured | Δ MMBtu/MWh | Δ $/MWh | boundary | 2024 dispatch ratio | util_of_avail |
|---|---|---|---|---|---|---|---|---|---|
| **56** | **Charles R Lowman** | 639.0 | **8.105** | **6.303** | **+1.801** | **+5.10** | 1.116 ok | **0.602** | 0.620 |
| **3** | **Barry** | 1821.2 | **7.821** | **7.051** | **+0.770** | **+2.18** | 1.076 ok | **0.729** | 0.719 |
| **6073** | **Daniel** | 1132.4 | **7.553** | **6.852** | **+0.701** | **+1.98** | 1.060 ok | **0.843** | 0.873 |
| 55406 | Bobby C. Smith Jr. | 524.6 | 7.580 | 7.340 | +0.240 | +0.68 | 1.027 ok | 1.058 | 0.938 |
| 55411 | Hillabee | 752.7 | 7.345 | 7.174 | +0.170 | +0.48 | 1.039 ok | 1.063 | 0.992 |
| 55382 | Thomas A. Smith | 1192.0 | 7.279 | 7.178 | +0.101 | +0.28 | 1.037 ok | 1.031 | 1.000 |
| 55440 | Central Alabama | 917.0 | 7.452 | 7.390 | +0.062 | +0.18 | 1.033 ok | **1.455** | 0.968 |
| 7897 | E B Harris | 1304.0 | 6.941 | 6.977 | −0.036 | −0.10 | 1.023 ok | **1.404** | 1.000 |
| 7710 | H. Allen Franklin | 1901.8 | 6.878 | 6.914 | −0.036 | −0.10 | 1.026 ok | 1.126 | 1.000 |
| 55965 | Wansley CC | 1184.8 | 6.934 | 6.974 | −0.040 | −0.11 | 1.023 ok | 1.090 | 1.000 |
| 57037 | David M Ratcliffe | 840.0 | 7.374 | 7.417 | −0.043 | −0.12 | 1.024 ok | **1.431** | 0.982 |
| 7917 | Chattahoochee | 466.0 | 6.874 | 6.927 | −0.053 | −0.15 | 1.017 ok | 0.977 | 1.000 |
| 710 | Jack McDonough | 2471.0 | 6.724 | 6.799 | −0.075 | −0.21 | 1.014 ok | 0.966 | 1.000 |
| 56150 | McIntosh CC | 1315.6 | 7.077 | 7.171 | −0.094 | −0.27 | 1.014 ok | 1.116 | 1.000 |
| **55271** | **Tenaska Lindsay Hill** | 848.0 | 7.304 | 7.411 | −0.107 | −0.30 | 1.032 ok | **2.506** | 0.999 |
| 55241 | Hog Bayou | 230.0 | 7.555 | 7.697 | −0.143 | −0.40 | 1.017 ok | 0.949 | 0.945 |
| *533* | *McWilliams* | *650.0* | *8.041* | *10.776* | — | — | **0.719** | *1.070* | 0.790 |
| *7946* | *Wansley U9* | *462.8* | *7.175* | *10.938* | — | — | **0.675** | *1.016* | 1.000 |

**Applied: 16 of 18 plants, 17,540.1 of 18,652.9 MW = 94.0 %.**

### 2.2 THE BOUNDARY GUARD — and it refuses two plants before any of this is trusted

`heatInput / grossLoad` is a plant's **combined-cycle** heat rate only if CAMPD's gross load includes
the steam turbine. At some sites it does not: the combustion turbines report and the unfired steam
generator does not, so the ratio is the **CT** rate — about 1.5× the true CC rate, because the steam
tail is roughly a third of a CC's output for none of its fuel. Applying that would price a healthy
plant out of merit on a metering artifact.

The guard is an **identity test against an independent source**: pooled CAMPD CC gross over the same
year's EIA-923 CC net, read through the benchmark's own `_eia923_frame`, so the comparator is exactly
the series the run is scored on. The measured clusters:

| cluster | plants | ratio |
|---|---|---|
| steam **metered** | 16 | **1.014 … 1.116** |
| steam **NOT metered** | 533 McWilliams, 7946 Wansley U9 | **0.719 / 0.675** |

Separated by a factor of 1.4 with **nothing between 0.72 and 1.01**. The band `[0.90, 1.25]` sits
inside an empty gap, so **no value in [0.75, 1.00] would change the partition** — it is fixed on
physics ex ante and is not a swept parameter (rules 1 `[R-STRUCT]` / 23 `[R-FROZEN-DERIVE]`).
Independent cross-check: for a metered plant the boundary ratio and the class parasitic factor are
two estimates of one quantity, and they agree (E B Harris 1.023 against 1/0.975 = 1.0256).

### 2.3 THE TRACED CASE, and it answers the handoff's Lowman-vs-Tenaska question

> **Charles R Lowman (plant 56): EIA-860 files BOTH its generators — `LEC1` (CT, 459.0 MW) and `LEC2`
> (CA, 273.7 MW) — at `Operating Year` 2023.** eGRID's 2023 vintage is therefore its
> **commissioning-year** average: first-fire, tuning and acceptance-test fuel against a part-year
> denominator. The model prices it at **8.105 MMBtu/MWh — 42 % HHV, an F-class number** — while its
> own meter reads **6.35 / 6.30 / 6.29 net across 2023 / 2024 / 2025 (≈54 %), stable to ±0.03**,
> which is what a new H-class machine does.

**The handoff asked which explanation applies to Lowman and which to Tenaska Lindsay Hill. Measured:**

- **Lowman — ECONOMIC, and now NAMED.** `util_of_avail` 0.620: it is not at its ceiling, so nothing
  physical stops it. It does not run because the model charges it **$5.10/MWh too much**.
- **Tenaska Lindsay Hill — NOT a heat-rate defect.** Its model rate is **$0.30/MWh CHEAP** against
  its own meter, a rounding error, at `util_of_avail` 0.999. Its 2.506× over-run is the largest
  single outlier in the class and **this lever does not touch it**. ROUTED, unexplained, and said so
  before the solve.

### 2.4 Why this is a mechanism and not a fit

The correction is largest at the three plants the model most under-dispatches, **in rank order**; it
is ~zero at the plants the model already dispatches correctly (McDonough 0.966×, Chattahoochee
0.977×, Hog Bayou 0.949×); **and it is ~zero at the plants the model OVER-dispatches** (Tenaska
2.506×, Central Alabama 1.455×, Ratcliffe 1.431×, E B Harris 1.404×). A lever that repaired both
tails would be a curve fit. This one **repairs one tail and provably leaves the other alone** —
`corr(Δ heat rate, dispatch ratio) = −0.505` over the 16 applied plants.

---

## 3. RULE 19 `[R-ONE-MECH]`, MACHINE-VERIFIED AT FOUR GRAINS BEFORE THE SOLVE

`fleet_only` rebuild off the keeper's own `meta.json`, arm vs control, **keys moved** reported and not
only max|Δ| (the SOCO-56 lesson):

| year | `fuel_prices` | `pmax` | `availability` | `mc_base` | `heat_rate` |
|---|---|---|---|---|---|
| 2023 | **0.000000000000** · 0 rows | **0.000000000000** · 0 | **0.000000000000** · 0 | 6.441073532230 · **59/327** | 1.801497324000 · **59/327** |
| 2024 | **0.000000000000** · 0 rows | **0.000000000000** · 0 | **0.000000000000** · 0 | 6.015920163766 · **59/327** | 1.801497324000 · **59/327** |
| 2025 | **0.000000000000** · 0 rows | **0.000000000000** · 0 | **0.000000000000** · 0 | 8.864447732474 · **59/290** | 1.801497324000 · **59/290** |

**Every moved row is `CC_REGULAR`**, at exactly the 16 applied plants
`[3, 56, 710, 6073, 7710, 7897, 7917, 55241, 55271, 55382, 55406, 55411, 55440, 55965, 56150, 57037]`.
McWilliams (533) and Wansley U9 (7946) are **absent on every grain** — the boundary guard holds
through to the LP. The `heat_rate` delta is year-invariant (the artifact is pooled, by construction);
the `mc_base` delta scales with each year's gas level.

---

## 4. THE DISTANCE, STATED EX ANTE — **THIS LEVER CANNOT CLOSE THE ROW, AND IS NOT TAKEN TO**

The failing row needs **−2.712 TWh of volume and −0.88 pp of share**. The zero-LP greedy re-stack
(exact per-plant Δmc, floors respected, an UPPER bound — it ignores network, ramp, storage and the
LP's own re-optimisation) says the arm moves 2024 `CC_REGULAR` **+0.356 TWh, i.e. the WRONG WAY**:

| year | `CC_REGULAR` | `COAL` | `CT_PEAKER` | `ST_GAS` | `ST_CHP` |
|---|---|---|---|---|---|
| 2023 | **+0.257** | −0.242 | −0.004 | −0.001 | −0.011 |
| 2024 | **+0.356** | −0.126 | −0.185 | −0.025 | −0.020 |
| 2025 | **+0.463** | −0.434 | −0.012 | −0.003 | −0.013 |

**Said plainly, before the solve: the arm makes this lane's own target row WORSE and it will still
FAIL both legs.** It is taken under rule 14 `[R-ACCURATE]` — *"if swapping a hand estimate for real
data makes the backcast worse, that is a signal that something else is miscalibrated… keep the
accurate input"* — and rule 1 `[R-STRUCT]`, never on the residual. A model that prices a 2023-vintage
H-class machine at a 42 %-efficiency rate is not modelling that machine, whatever the class total
reads.

**Why the class total barely moves while 2.6 TWh of dispatch re-allocates.** The dearest *producing*
unit is at or below its own min-gen floor in **75.8 %** of hours (median floor/mw = 1.000) — SOCO's
committed gas boilers, out of merit but synchronized (SOCO-54 §2a). Once floors are respected the
dearest **displaceable** producer is `CC_REGULAR` in 38.4 % of hours, `CT_PEAKER` 35.8 %, `COAL`
17.8 %, `ST_GAS` 7.7 %. **The repair is therefore overwhelmingly a WITHIN-CLASS re-allocation**, which
is exactly what an allocation defect should produce.

---

## 5. PRE-REGISTERED PREDICTIONS, WITH FALSIFIERS

Second-order classes are banded **generously** and floor/forcing **direction is deliberately left
unpredicted** (the SOCO-55 → SOCO-56 lesson). Keeper baselines are FINDING-soco-56 §5.1; C1 bands
7.180 / 7.466 / 7.545 TWh, share cap ±3.00 pp.

| # | prediction | falsifier |
|---|---|---|
| **P1** | **2024 `CC_REGULAR` gets WORSE and still FAILS BOTH legs.** +10.178 → point **+10.53**, band **+9.9 to +11.6 TWh**; share +3.88 → **+3.8 to +4.4 pp** | lands outside the band, or either leg passes |
| **P2** | Determination stays **`NOT-YET`**; **C1 stays 13/14 all · 9/10 free**; **no row changes status** | any row flips status |
| **P3** | 2024 `CT_PEAKER` **IMPROVES**: move −0.05 to −0.45 TWh → **+2.70 to +3.10**; PASS | moves up, or outside the band |
| **P4** | **THINNEST ROW #1** — 2024 `COAL_PRB` (−5.143 of ±7.466; −2.10 pp of ±3.00) worsens by **< 0.45 TWh** and **STAYS PASS** | moves more than 0.45 TWh, or fails |
| **P5** | **THINNEST ROW #2** — 2023 `ST_GAS` (−6.461 of ±7.180, **0.719 TWh of headroom**; −2.70 pp, **0.30 pp of headroom**) moves by **< 0.15 TWh** and **STAYS PASS** | moves more than 0.15 TWh, or fails |
| **P6** | **THINNEST ON SHARE** — 2023 `CT_PEAKER` (+2.52 pp, **0.48 pp of headroom**) moves by **< 0.15 TWh**, direction flat-or-safer; PASS | moves dearer by more than 0.15 TWh, or fails |
| **P7** | 2023 `CC_REGULAR` +5.752 → **+5.80 to +6.60 TWh**; PASS | outside the band, or fails |
| **P8** | **Per-plant allocation IMPROVES at all three repriced plants in every year** (2024 ratios: Lowman 0.602 → **0.70–0.95**, Barry 0.729 → **0.74–0.88**, Daniel 0.843 → **0.85–0.98**) | any of the three moves away from 1.0 |
| **P9** | The two boundary-refused plants are **NOT repriced** — heat rate byte-identical both sides; their dispatch may still fall (they become relatively dearer) | either plant's heat rate moves |
| **P10** | 2025 (**ungated**, preliminary EIA-923) `CC_REGULAR` +0.390 → **+0.6 to +1.3 TWh**; reported, claimed as nothing | outside the band |
| **P11** | Rule 17 `[R-FLOOR-WINDOW]` holds in every plant-year. **DIRECTION OF FLOOR BINDING DELIBERATELY UNPREDICTED** | any plant-year's binding share exceeds its own synchronized share |
| **P12** | C8 forced share stays under the 0.30 merchant cap. **DIRECTION DELIBERATELY UNPREDICTED** | any material class exceeds its cap |
| **P13** | C2 / C4 / C6 **PASS**; **0 ledgered, 0 protective**; C3a/b/c **UNSCORABLE** (not failed) | any of these moves |
| **P14** | **ZERO free parameters added.** DOF **6 entries / 1 residual**, identical to the keeper | `n_entries` or `n_residual` moves |
| **P15** | **No peer ISO moves**: `moved_rows("SOCO") == {}`, zero pre-existing cache keys move, explicit-`False` key == default key | any peer artifact or key moves |
| **P16** | The boundary guard refuses **exactly 2** plants; applied coverage **94.0 %** | a third plant is refused, or either named plant is applied |

**Pre-registered STOP.** If P5 or P6 fails — i.e. the arm pushes the thinnest passing row out of band —
that is a REPORTED cost, not a reason to revert: rule 14 governs and the input stays. It would,
however, change the promotion recommendation from *promote* to *promote with a named new failure*.

---

## 6. WHAT IS BUILT, AND WHAT IS VERIFIED ALREADY

| artifact | status |
|---|---|
| `scripts/data/derive_campd_cc_heat_rates.py` | NEW. The CC sibling of nwpp-42 / soco-53e / nyiso-88, plus the boundary guard |
| `data/raw/_processed-legacy/campd_cc_heat_rates_SOCO.csv` | NEW, derived in-lane from SOCO's own CAMPD + EIA-860 (rules 25 / 28(d)) |
| `ScenarioConfig.measured_cc_heat_rates` | NEW, **default `False`**, in `_CACHE_KEY_OPTIONAL_FIELDS` at frozen drop value `"False"` |
| fleet seam | `campd_bins.measured_cc_heat_rates` + a **group-gated** `eia860.py` row-loop branch, disjoint from CT / COAL / ST_GAS by construction |
| `tests/unit/data/test_measured_cc_heat_rates.py` | NEW, **16 tests, all passing**, incl. 5 for the boundary guard |
| existing suite | `tests/unit/data/` + `tests/unit/config/`: **3,368 passed**; the **10 failures are PRE-EXISTING**, verified identical at the stashed baseline |
| `check_mechanism_matrix --base origin/main` | **GREEN** (exit 0); base row + a cell line in all 9 shards (rule 28(c)) |
| solve surface | `moved_rows("SOCO") == {}` — no touched file is a `SURFACE_MODULE` |

**One wiring defect found and fixed in-lane, and it matters for any successor adding a sibling:**
`scripts/run_calibration.py`'s `fleet_to_bins` call site passes the other three measured-heat-rate
flags but was missing the new one, so the first rule-19 run read **all four grains at exactly zero** —
an arm that looked perfectly inert while simply never arming. The diagnosis was a control toggle of a
KNOWN-armed flag (`measured_coal_heat_rates=false`) through the same channel, which moved 24 rows and
proved the channel sound. **A successor adding a fifth sibling must patch FOUR sites, not three.**

---

## 7. G-DRIFT (rule 29 `[R-SCREEN]` (b) form 4)

Rebased onto `origin/main` at **`202c0a5998ef589af9909469dd23a05899f214c3`** — 20 commits past the
keeper's own base, all SPP-68's curtailment-ceiling lane (`vre_curtailment_ceiling`-family work on
SPP's own branch and its `[R-HOLDOUT]` footprint sweep). **INERT for SOCO** on two independent
grounds: another ISO's branch, and default-off flags absent from this keeper's recipe. SOCO dispatches
**0.000 TWh of wind** in every year. Form 4 holds; the keeper's committed bundle is the control and
no control solve is spent.

**The control's per-plant layer was recovered at ZERO LP for the third consecutive lane**:
`git fetch origin <40-char-sha>` on the SOCO-56 leg SHAs returned 16 files each, and **all twelve
committed hourly sidecars verified byte-identical** to the registered keeper. *The retention window
remains undocumented, so this is not a durability claim (rule 33(d)).*

---

## 8. SOLVE SHAPE (rules 32 / 34 / 36)

**ONE SHARD PER YEAR** (rule 36 `[R-YEAR-ISOLATION]` (a)), each a single `--years <Y>` invocation into
its own out-dir, composed by the parent at zero LP. Each shard pushes its **full 16-file bundle**
including `dispatch/<year>_P1.parquet` and the bundle-root `system.parquet` (rule 34 `[R-SHARD-PROMOTABLE]`
(a)) so the result can back a promotion without a re-solve. The parent never solves (rule 32(a)).

Years: **2023, 2024, 2025** — the full union of SOCO's registered years (rule 35 `[R-PROMOTE]` (b),
enumerated from `frontend/data/backcast/registry/*.json` **before** anything is pruned).
