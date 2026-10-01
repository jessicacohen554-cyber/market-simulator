# RESULT (pjm-h4, step 1-2) — the PENDING BENCH MOVE IS LANDED, and the corrected C1
# residual is the real object

**Session** `pjm-h4` · **ISO** PJM · **Date** 2026-09-13 · **Base** `origin/main` @ `33a7c961`
**ZERO LP.** The parent never solved and no shard was launched (rule 32 `[R-SHARD]` (a)).
**PJM keeper `2026-09-11-pjm-d4-4-gasoutage` re-scored BEFORE and AFTER: CALIBRATED, grade 8/8,
zero caveats, zero fails — UNCHANGED.** (Rule 30(c): held-out years never downgrade PJM.)

---

## 1. RESULT

> **The `gov-hydro-seam-1` PS→`OTHER` repair is now IN the committed PJM bench parts.
> `reconcile_vintage_classes` fires in PJM 2021 (×1.033427) and 2022 (×1.032811) and NOWHERE
> ELSE, exactly as `FINDING-pjm-h2-holdout-basis-2026-09-12.md` §3 predicted to five decimal
> places. ZERO determination flips, ZERO status flips on the keeper.**
>
> | | before | after |
> |---|---|---|
> | keeper `2026-09-11-pjm-d4-4-gasoutage` | **CALIBRATED** 8/8, 0 caveats | **CALIBRATED** 8/8, 0 caveats |
> | touchpoint `2026-09-11-pjm-holdout-gasoutage-touchpoint` | **NOT-YET** 4/8, 1 ledgered, 3 fails | **NOT-YET** 4/8, 1 ledgered, 3 fails |
>
> **This is a BASIS CORRECTION, not a model error** — the model side is byte-identical
> (`26f8508b`'s own measurement: "Not solve-affecting … zero dominant-class flips reach a gas
> class"; the model's `gmModel` is unchanged in both run payloads). It was NOT root-caused in
> the model and must not be.

## 2. THE RECIPE IN THE CARD COULD NOT EXECUTE, AND WHY THAT IS NOT A BLOCKER

The card says "rebuild the PJM bench parts (`run_calibration_full.py --rebuild-benchmark
<bundle>`, then register)". **Step 2 of that recipe is unreachable for PJM at HEAD.** Both
registered PJM bundles are the SLIM committed form — `hourly/` sidecars, `meta.json`,
`metrics.json`, `run_config.json`, `calibration_attestation.json`,
`legitimacy_diagnostics.json` and nothing else. `dispatch/<year>_P1.parquet`,
`system.parquet` and `btm.parquet` are gitignored and did not survive their solve container,
and `render_calibration_html.build_payload` reads all three. So `dashboard_add_run.py` cannot
re-render either PJM run, and a literal reading of the recipe costs a **6-year re-solve**
(~2.5-3 h of PJM per-plant LP) to reproduce a model side the change does not touch.

**It is not needed, because the bench part is model-independent where it matters.** The C1
actuals (`bench.classFull`) and the C2 grid series (`bench.e930`) are pure functions of the
benchmark frames; `build_payload` needs the dispatch for exactly TWO things on the bench side —
the per-plant model class set (`classes_p`) and the per-plant zone label (`zone_p`) — and both
are recorded verbatim in the COMMITTED bench part's `plants` block.

So the move was landed at **zero LP**, in three steps:

1. **`--rebuild-benchmark` on both bundles** (no LP by construction — its own docstring: "a pure
   function of ``(year, iso)`` and the reference data … no LP re-solve needed"). All three
   benchmark hashes moved, which is the builder change showing up:
   `eia923-9b08db5fc7d9 → eia923-35c1e6a6ba06`, `eia930-eabb5979cef0 → eia930-a18e7d0dec0e`,
   `campd-ee850c4b7b92 → campd-db315991835d` (keeper bundle).
2. **The three missing solve artifacts reconstructed**, each from a committed source:
   * `dispatch/<year>_P1.parquet` — one row per `(plant_code, klass, zone)` read off the
     committed bench part's own `plants` block. Only the class set and zone label are consumed
     on the bench side.
   * `system.parquet` — a concat of the committed `hourly/system_<year>.parquet` sidecars
     (identical schema: `year / pass / zone / hour / price / slack / dump / demand /
     reserve_price`).
   * **`btm.parquet` — rebuilt through `run_calibration_full._btm_frame` itself**, with the
     identical arguments `rebuild_benchmark` passes to the benchmark frame. This is legitimate
     for one stated reason: that function is **a pure function of committed inputs** by its own
     docstring and design ("The model's dispatch never enters … This frame is now a pure
     function of committed inputs, so two rebuilds are byte-identical"). It is the BTM
     subtrahend of `classFull`, so omitting it is not an option — a first pass that did omit it
     moved CC_CHP +3.3 / CT_CHP +2.4 / ST_CHP +0.9 TWh and suppressed the reconcile entirely.
     Reported here because that intermediate state is exactly the failure mode a reader should
     be able to rule out.
3. **The rebuilt part written through the real writer** (`backcast_artifacts.write_bench_part`),
   so the `builderFingerprint` and the byte layout are the builder's, not a hand edit.

### 2.1 THE GATE THAT MAKES THIS ADMISSIBLE, AND IT PASSED IN ALL SIX YEARS

The reconstruction is accepted ONLY if the rebuilt part's plant key set and every
**dispatch-scoped** field (`name / zone / group / npl / nodata / campd / c_ann / c_mon`) come
back byte-identical to the committed part. Identity there proves the reconstructed dispatch
reproduced `classes_p` / `zone_p` exactly, so anything that then moves in `classFull` / `e930`
is the benchmark-builder change and nothing else. A mismatch aborts and writes nothing.

| year | plants | key set + dispatch-scoped fields | EIA-923 fields moved | Σ Δ(e_ann) |
|---|---:|:--|---:|---:|
| 2020 | 235 | **IDENTICAL** | 1 plant | +0.0003 TWh |
| 2021 | 236 | **IDENTICAL** | 1 plant | +0.0003 TWh |
| 2022 | 233 | **IDENTICAL** | 1 plant | +0.0004 TWh |
| 2023 | 225 | **IDENTICAL** | 1 plant | +0.0003 TWh |
| 2024 | 217 | **IDENTICAL** | 1 plant | +0.0002 TWh |
| 2025 | 214 | **IDENTICAL** | 0 plants | +0.0000 TWh |

The single moving plant is 50479 (Georgia-Pacific Big Island, ST_CHP), +0.0003 TWh — five
orders of magnitude below the 8 TWh C1 band and not attributable to the PS repair.

### 2.2 IT IS THE WHOLE ENGINE DELTA, NOT ONLY `26f8508b` — STATED RATHER THAN IMPLIED

`check_bench_freshness` read **0 STALE, 6 with engine drift** against SIX commits under
`src/market_sim/data|config` since the parts were last committed (2026-09-12T03:02:50Z):
`760012f7` (EIA-860 vintage cache keying), `8852b917` + `26737620` (nyiso-230),
`10bf4e62` (miso-255, gated default off), **`26f8508b` (the PS→`OTHER` + hydro repair)**,
`3497a1d8` (nyiso-229). The regenerated parts carry the aggregate of all six. The PS repair
**dominates** — it is the only one that moves a scored number, and the reconcile trigger it
fires reproduces h2's prediction to five decimals — but the +0.0003 TWh single-plant EIA-923
drift above is most plausibly `760012f7`'s, and this document does not claim otherwise.

## 3. WHAT MOVED IN THE BENCH

`classFull` (TWh, grid-delivered). **No `e930` value moved in any year** (the repair's EIA-930
half touches `hydro`, which `bench.e930` does not carry).

| year | class | before | after | Δ |
|---|---|---:|---:|---:|
| **2020** | OTHER | 7.6000 | **5.8163** | −1.7837 |
| 2020 | hydro | 15.8943 | 9.9324 | −5.9619 |
| **2021** | **CC_REGULAR** | 279.2013 | **288.5339** | **+9.3326** |
| 2021 | **COAL_BIT** | 150.7407 | **155.7794** | **+5.0387** |
| 2021 | OTHER | 7.5434 | 5.6931 | −1.8503 |
| 2021 | hydro | 16.6400 | 10.2909 | −6.3491 |
| 2021 | (every other fossil class) | — | — | ×1.033427 |
| **2022** | **CC_REGULAR** | 297.1303 | **306.8801** | **+9.7498** |
| 2022 | **COAL_BIT** | 136.1140 | **140.5803** | **+4.4663** |
| 2022 | OTHER | 6.9931 | 4.6137 | −2.3794 |
| 2022 | hydro | 15.9967 | 8.8854 | −7.1113 |
| 2022 | (every other fossil class) | — | — | ×1.032811 |
| 2023 | OTHER / hydro | 7.2251 / 15.4676 | 4.7002 / 8.9763 | −2.5249 / −6.4913 |
| 2024 | OTHER / hydro | 7.3210 / 15.8562 | 4.6477 / 8.8612 | −2.6733 / −6.9950 |
| 2025 | OTHER | 4.7776 | 2.1176 | −2.6600 |

**The reconcile fires in 2021 and 2022 ONLY.** Measured scale factors **×1.033427** and
**×1.032811** against h2 §3's predicted ×1.03343 / ×1.03281. **2020 and the whole keeper span
2023-2025 see NO fossil class move** — only `OTHER` and `hydro`, neither of which C1 gates for
PJM. PJM 2025 `hydro` is deliberately unmoved: `26f8508b` discloses that PJM 2025 keeps the
contaminated actual because its class-specific 923 truncation is invisible to the ISO-wide
completeness measure, and the final 2025 vintage discharges it with no code change.

## 4. STEP 2 — THE CORRECTED C1 TABLE, WHICH IS THE REAL OBJECT NOW

Model unchanged; actual on the HEAD bench. Band **8.0 TWh**.

| yr | class | model | act BEFORE | act AFTER | **res BEFORE** | **res AFTER** | gate |
|---|---|---:|---:|---:|---:|---:|:--|
| **2020** | **COAL_BIT** | 153.97 | 131.14 | **131.14** | **+22.83** | **+22.83** | FAIL → FAIL (**UNMOVED**) |
| 2020 | CC_REGULAR | 290.56 | 283.00 | 283.00 | +7.56 | +7.56 | PASS |
| 2020 | ST_GAS | 8.81 | 6.63 | 6.63 | +2.18 | +2.18 | PASS |
| **2021** | **CC_REGULAR** | 305.51 | 279.20 | **288.53** | **+26.31** | **+16.98** | FAIL → FAIL (**−35 %**) |
| 2021 | **COAL_BIT** | 152.07 | 150.74 | **155.78** | +1.33 | **−3.71** | PASS (**SIGN FLIP**) |
| 2021 | CT_PEAKER | 15.83 | 20.63 | 21.32 | −4.80 | −5.49 | PASS |
| 2021 | ST_GAS | 7.00 | 3.79 | 3.92 | +3.21 | +3.08 | PASS |
| **2022** | **CC_REGULAR** | 319.69 | 297.13 | **306.88** | **+22.56** | **+12.81** | FAIL → FAIL (**−43 %**) |
| 2022 | **COAL_BIT** | 143.63 | 136.11 | **140.58** | +7.52 | **+3.05** | PASS |
| 2022 | CT_PEAKER | 17.02 | 18.46 | 19.07 | −1.45 | −2.05 | PASS |
| 2022 | ST_GAS | 8.68 | 5.79 | 5.98 | +2.89 | +2.70 | PASS |

Every predicted magnitude lands: **+16.98**, **+12.81**, **−3.71**, **+3.05**, 2020 **unmoved**.

**The held-out C1 object is now TWO objects, not one, and they are in different years:**

1. **2020 COAL_BIT +22.83 TWh** — untouched by the basis, the single largest C1 residual PJM
   carries, and the one the basis correction proves is *model*.
2. **CC_REGULAR 2021 +16.98 / 2022 +12.81 TWh** — **~40 % smaller than the numbers every prior
   PJM session reasoned about**, and still FAIL against an 8 TWh band. `FINDING-pjm-h2b` §1.2's
   on-hours diagnosis (model CC online +8.8 / +5.8 pp too often, fleet CF flat at 0.606-0.621
   against a meter that moves 5.8 points) is unaffected in kind by a uniform rescale.

## 5. EVERY OTHER SCORED RECORD, AT FULL MAGNITUDE

**Keeper: ZERO status flips** across all 67 records; determination, grade and reason lines
byte-identical. 22 records move and every one is cosmetic:

* 18 × `share_pp` drift ≤ 0.44 pp (the share denominator moves as hydro/OTHER fall out of total
  generation). Largest: CC_REGULAR 2023 +0.42 → −0.02 pp, against a 3.0 pp band.
* C2 2025 actual re-splits: coal 133.27 → **135.05**, gas 379.23 → **377.45** (the G-21b
  split-anchor ratio moves k = 0.989 → 1.002). Both still PASS.

**Touchpoint: TWO status flips, both benign and both predicted.**
`C8 forced_share hydro` **2020 and 2021: PASS → SKIPPED**. Hydro's actual falls ~16 → ~10 TWh,
which drops it under the rubric's 2 %-of-load materiality floor, so it is reported by D-1/D-2
and no longer gated. **C8 as a criterion still PASSES** — a SKIPPED is not a FAIL, it enters no
caveat budget, and the grade is unchanged at 4/8 with 1 ledgered and 3 fails. h2 §3.1 predicted
this exact pair.

Unchanged on the touchpoint: C3a (2020 +22.3 %, 2022 −10.7 %), C3b (0.243 / 0.246), C3c (the
two ledgered rule-22 `[R-C3C]` caveats at 6 h vs 23 h and 3 h vs 92 h), C2, C4, C6, and both
C8 CT_PEAKER grounded-above-budget notes (19.8 % / 18.6 %).

## 6. WHAT I DID NOT DO, AND WHY

* **No LP, no shard, no re-registration.** §2 states the reason: the change is bench-only by the
  committing session's own measurement, the reconstruction gate proves the dispatch-scoped half
  is untouched, and a re-solve would spend ~3 h reproducing an identical model side.
* **The run payloads (`runs/<id>.js`) are NOT regenerated, and two DISPLAY-ONLY fields in them
  are now stale — reported, not hidden.** `volErr` (the signed volume-error heatmap) and
  `nonFosErr` are baked at render time against the actuals of the day. **No gate reads either**:
  `score_fuelmix` recomputes C1 from `ypay.gmModel` and `ybench.classFull`, and `score_sysvol`
  from the bench series, which is why the re-score above is correct. The Run Explorer's heatmap
  for PJM 2021/2022 will under-state the corrected residual by the reconcile factor until those
  runs are next re-rendered from a full bundle. Refreshing them requires the 6-year re-solve
  §2 declines.
* **No model root-cause opened on this.** It is a basis correction (card step 1, explicit).
* **No mechanism tested, so no matrix cell verdict moves** (rule 28 `[R-MECH-MATRIX]`).
* **Nothing deleted** (rule 31 `[R-RETAIN]`).

## 7. RULES

Rule 14 `[R-ACCURATE]` (the corrected basis is kept and the residual it exposes is attributed to
the model, not buried) · rule 15 `[R-DASHBOARD]` (the bench parts are the committed deliverable
and are pushed in the session that produced them) · rule 29 `[R-SCREEN]` clause 0 (zero-LP phase
0 before anything else) · rule 30(c) (no held-out year touches PJM's determination) · rule 31
`[R-RETAIN]` (nothing deleted) · rule 32 `[R-SHARD]` (a) (the parent ran no LP; scoring and
composition stayed here).
