# FINDING — nyiso-239: C1 `CC_REGULAR` 2022 is a BENCHMARK gas/oil attribution artifact. The repair is a two-line, ZERO-LP bench-construction fix — and its blast radius is 12 cells across 7 ISOs, so it is the owner's call

**Session** nyiso-239 (ORCHESTRATOR — rule 32 `[R-SHARD]` (a); **the parent ran ZERO LP, and no shard was launched**).
**Date** 2026-09-16. **Base** `origin/main` at `4cf338b2`; branch `claude/nyiso-central-east-hydro-830ppy` (`a3453eeb`) verified merged.
**Keeper** `2026-09-16-nyiso-238-hydro-budget` (bundle `results/calibration/nyiso238_hydroperiod_span`), years {2022, 2023, 2024, 2025} — **UNCHANGED by this session. Nothing armed, screened, solved, promoted or registered.**
**Probe** `scripts/probes/nyiso239_c1_bench_oil_phase0.py` → `results/calibration/_nyiso239_bench_oil_phase0.json`. Every number below regenerates from committed artifacts plus the immutable `data/raw` extracts.

> ## HEADLINE
> 1. **The C1 object is not model over-dispatch — it is the ACTUAL.** In 2022 alone, every NYISO
>    fossil class's C1 benchmark is deflated by a uniform **×0.951167** by
>    `render_calibration_html.reconcile_vintage_classes`. `CC_REGULAR`'s actual drops
>    **33.207 → 31.586 TWh**. That 1.62 TWh IS the band breach.
> 2. **The reconcile fires on a boundary mismatch, not a level error.** Its target is EIA-930's
>    `gas + coal` cell and **omits `NG: OIL`**, while EIA-923 books a dual-fuel plant's CC/CT/ST MWh
>    inside the gas classes. On the gas-only basis NYISO 2022 reads **+5.13 %** (fires); on the
>    gas+oil basis it reads **+0.08 %** — the TIGHTEST agreement of any complete vintage (§2).
> 3. **FOUR independent sources arbitrate, and all four say the same thing** (§3) — NYISO's own
>    published hourly fuel mix, the EIA-923 liquid-fuel routing, the shape of the EIA-930 `NG: OIL`
>    block itself, and CEMS on a fixed 67-plant set.
> 4. **The decisive leg is SHAPE, which no level scale can fake:** model(gas+oil) vs 930(gas+oil)
>    beats model(gas) vs 930(gas) on **r AND NRMSE in all four years — 8 of 8** (§4).
> 5. **Counterfactually the keeper reads `CALIBRATED`** (NOT-YET → CALIBRATED, grade 6 → 7, fails
>    2 → 0, C3c the lone ledgered caveat). **Stated at full magnitude: the `CC_REGULAR` share leg
>    then lands at +2.97 pp against a ±3.0 pp band — a 0.03 pp margin — and the model's +3.19 TWh
>    over-run is REAL and stays the lane's open object** (§5).
> 6. **NOT LANDED.** The repair is shared across every ISO and the reconcile currently fires in
>    **12 of 41 committed bench parts, 11 of them other lanes'** (§1). Rule 25 `[R-ISO-SCOPE]` and
>    the nyiso-232 precedent both say this lane does not land that alone. **§7 is the decision.**
> 7. **Two handed-forward leads CLOSED at zero LP** (§6), one of them against an armed cell.

---

## 0. WHAT THE HANDOFF ASKED, AND THE ANSWER

> *"Establish whether the miss is a BENCHMARK attribution artifact or real over-dispatch before
> proposing any mechanism — nyiso-238 showed two prior lanes chased a defect whose repair did not
> exist."*

**It is a benchmark attribution artifact — and it is BOTH.** The benchmark is wrong by 1.62 TWh and
the model still over-runs `CC_REGULAR` by 3.19 TWh against the corrected actual. The gate breach is
the benchmark's; the residual under it is the model's. Both are stated, neither is buried.

The handoff's own candidate — **the CT-only CEMS bench flag** (12 plants in 2022, Riverbay 2.95×,
East River, Lockport) — is **NOT the cause, and is eliminated by construction.** `_flag_ct_only_reporters`
marks a plant so its per-plant *capture* diagnostic is scored on its EIA-923 monthly row instead of its
understating CAMPD series. It never touches `classFull`, which C1 scores against, and `classFull`
is built from `e923_cls` — the EIA-923 class aggregate — independently of the flag. Checked, not assumed.

---

## 1. WHERE THE RECONCILE FIRES TODAY — the blast radius, measured

`reconcile_vintage_classes` scales the EIA-923 grid-delivered fossil classes to the EIA-930
`gas + coal` grid cell whenever they differ by more than ±3 % (`_VINTAGE_RECONCILE_FRAC = 0.97`).
A committed bench part shows it FIRED when its fossil `classFull` sum sits exactly on that target:

| | fires today |
|---|---|
| **NYISO** | **2022** (this object), 2025 |
| PJM | 2021, 2022 |
| SPP | 2023, 2024, 2025 |
| SOCO | 2023, 2024 |
| CAISO | 2025 |
| MISO | 2025 |
| NEISO | 2025 |

**12 of 41.** NYISO 2022 is the **only complete-vintage NYISO year** in which it fires; 2023 (+1.09 %)
and 2024 (−2.82 %) sit inside the deadband and their `classFull` is byte-identical to the raw EIA-923
class total — verified to the fourth decimal, which is what makes 2022's deflation visible at all.

---

## 2. THE ARITHMETIC — gas-only vs gas+oil comparison basis

| yr | 923 fossil (grid) | 930 gas | dev | **fires** | 923 oil | 930 oil | 923+oil | 930+oil | dev | fires |
|---|---:|---:|---:|:--:|---:|---:|---:|---:|---:|:--:|
| **2022** | 63.351 | 60.257 | **+5.13 %** | **YES** | 1.844 | **4.885** | 65.194 | 65.142 | **+0.08 %** | no |
| 2023 | 61.662 | 60.999 | +1.09 % | no | 0.422 | 2.174 | 62.084 | 63.174 | −1.72 % | no |
| 2024 | 65.892 | 67.731 | −2.72 % | no | 0.322 | 0.291 | 66.214 | 68.022 | −2.66 % | no |

`923 fossil − 930 gas = +3.094 TWh`; `930 oil − 923 oil = +3.041 TWh`. **The two match to 0.053 TWh
(1.7 %)** — the signature of a transfer between two cells, not a level error in either.

**This is the completion of the function's own stated design, not a new idea.** Its docstring already
refuses to let EIA-930's *fuel attribution* drive the 923 split, because against CAMPD "EIA-930
MIS-SPLITS coal vs gas by 7–21 TWh/yr". The gas↔oil boundary is the same error one fuel over, and the
reconcile is currently blind to it.

---

## 3. THE FOUR ARBITERS

### 3a. NYISO's OWN published hourly fuel mix — the ISO's meter
NYISO publishes **no `oil` category at all**: an oil-capable unit is filed under **`Dual Fuel`**. The
ISO's own fossil total is `Natural Gas + Dual Fuel + Other Fossil Fuels`, hourly:

| yr | NYISO published | 930 gas | Δ | NRMSE | **930 gas+oil** | **Δ** | **NRMSE** |
|---|---:|---:|---:|---:|---:|---:|---:|
| **2022** | 65.670 | 60.257 | **−5.413** | 0.1067 | 65.142 | **−0.528** | **0.0664** |
| 2023 | 63.336 | 60.999 | −2.337 | 0.0829 | 63.174 | **−0.162** | **0.0634** |
| 2024 | 67.582 | 67.731 | **+0.150** | 0.0769 | 68.022 | +0.440 | 0.0785 |

The repair closes a −5.41 TWh gap in 2022 and a −2.34 TWh gap in 2023, and is a **near no-op in 2024**
— the year the mislabelled block is already gone. **A residual-fitted correction does not switch itself
off in the year the defect is absent.**

### 3b. EIA-923 routes every liquid-fuel row to the `oil` class
`_classify_f923` sends **100 %** of NYISO's DFO / RFO / JF / KER / WO / PC rows to `oil`: 1.844 TWh
(2022), 0.422 (2023), 0.322 (2024). So the 923 `oil` class IS the counterpart of the 930 `NG: OIL`
cell, and **the ~3 TWh EIA-930 calls oil in 2022 is not oil FUEL by the 923 survey.**

### 3c. The EIA-930 `NG: OIL` block is FLAT, then stops
GWh/month: **2022** `[467, 433, 438, 450, 165, 422, 468, 483, 344, 429, 381, 405]` — a ~550 MW
**baseload** every month of the year. **2023** steps to ~zero at **m07** (`… 413, 52, 19, 33, 16, 10, 8`).
**2024** is ~0 throughout. NYISO's liquid fleet is *peaking* plant; a flat year-round 550 MW oil block
is a reporting classification, not a burn pattern, and it was re-tagged mid-2023.

### 3d. CEMS — fixed 67-plant set, metered in all four bench years
`930 gas / CAMPD net` = **0.9061** (2022) vs **0.9554 / 0.9555 / 0.9635** (2023/24/25). Against the one
source whose meters do not move, **2022's 930 gas cell is the outlier, by ~5 %** — the same 5 % the
reconcile then charges to EIA-923.

---

## 4. THE SHAPE LEG — independent of every number above

A uniform level scale cannot move a Pearson correlation, so this test is orthogonal to §§2–3. Model
class-hourly from the keeper's committed `hourly/class_hourly_<yr>.parquet` (no re-solve):

| yr | r gas-only | **r gas+oil** | Δr | NRMSE gas-only | **NRMSE gas+oil** | ΔNRMSE |
|---|---:|---:|---:|---:|---:|---:|
| 2022 | 0.8681 | **0.9507** | **+0.0826** | 0.1901 | **0.1028** | **−0.0873** |
| 2023 | 0.9414 | 0.9547 | +0.0133 | 0.1233 | 0.1003 | −0.0230 |
| 2024 | 0.8960 | 0.9277 | +0.0317 | 0.1367 | 0.1148 | −0.0219 |
| 2025 | 0.8449 | **0.9284** | **+0.0835** | 0.1866 | **0.1262** | **−0.0604** |

**8 of 8 directional wins**, and the two largest gains are the two years with the largest
oil-labelled block. The model's own dual-fuel oil dispatch lines up, hour by hour, with EIA-930's
`NG: OIL` series.

---

## 5. THE COUNTERFACTUAL, AND ITS COST STATED AT FULL MAGNITUDE

Recovered deflation applied to NYISO 2022: **×0.951167**.

| | committed | counterfactual |
|---|---:|---:|
| `CC_REGULAR` actual | 31.586 | **33.207** |
| `CC_REGULAR` model | 36.398 | 36.398 |
| Δ (band) | **+4.812** (±3.766) | **+3.191** (±3.859) |
| share pp (band ±3.0) | **+3.62** | **+2.97** |
| C1 row | **FAIL** | **PASS** |
| run determination | **NOT-YET** (grade 6, fails 2) | **CALIBRATED** (grade 7, fails 0, C3c ledgered) |

C1's `CC_REGULAR` 2022 row is the **only** failing C1 row in the entire four-year span, so removing it
leaves C3c alone, and rule 22 `[R-C3C]`'s standing rule then reads it as a ledgered, non-downgrading
caveat.

**Three things this does NOT do, said plainly:**
1. **It does not fix the model.** +3.19 TWh of `CC_REGULAR` over-run remains, concentrated in
   **NYC (+2.24 of +2.56 TWh plant-level, 88 %)** and in **February (+788 GWh) and November
   (+774 GWh)** — 61 % of the annual miss in two months, with the model *under*-running Jul–Sep.
   Top plants: Zeltmann +0.90, Astoria Energy +0.80, Athens +0.69, Bethlehem +0.60, Astoria II +0.39.
   **That is the lane's object, before and after.**
2. **The share leg passes by 0.03 pp of a 3.0 pp band** — 1.1 % of the band. A keeper that clears C1
   on that margin is one input revision from failing again.
3. **It is not selected on the residual** (rule 1 `[R-STRUCT]`). The discriminating measurements are a
   fuel IDENTITY (§2, §3b), a SHAPE (§4) and a source the model never sees (§3a). The counterfactual
   determination is reported *because it is the consequence*, and it is not the reason.

---

## 6. TWO HANDED-FORWARD LEADS, CLOSED AT ZERO LP

**Lead 1 — "the model runs NUCLEAR +219 MW above the EIA-930 meter in the 2022 fabricated hours
(+195 MW all-hours, ~7 %); `nuclear_unit_availability` is K, so this is new evidence against an armed
cell." — CLOSED. It is not evidence against the cell; it is the same EIA-930 NYIS defect family as the
object of this finding.** EIA-930 `NG: NUC` runs **−201.5 MW/h below EIA-923 across ALL 8,760 hours of
2022** (2023 −402.6, 2024 −141.0) — every year, all hours. nyiso-238's +219 / +195 MW sits inside that
all-hours, all-year under-report. The render's own code already says so and already routes nuclear
away from EIA-930 for exactly this reason (`actuals_source("nuclear", iso) -> eia923`; "EIA-930
under-reports it for some BAs, e.g. NYIS"). **`nuclear_unit_availability` stays `K`. Do not re-open it
on this measurement.**

**Lead 2 — Object B (non-tail price slope 6.432 × gas + 16.29 vs market 7.481 × gas + 11.05;
`CT_PEAKER` 0.74 vs ~2.85 TWh actual in 2025). NOT PURSUED, and it is not a C1 object:** `CT_PEAKER`
2025 is **SKIPPED** by C1 (preliminary EIA-923 vintage, 17 of 20 prior plants missing), so it gates
nothing. It remains open as a marginal-unit question and is handed forward unchanged.

---

## 7. THE DECISION — the owner's, and it is open

The repair is **two edits in `scripts/render_calibration_html.py`**, both in the shared bench path:

1. carry `oil` into `_e930d` when the bundle's `eia930` extract has it — **every non-ERCOT bundle
   already does**, because `_eia930_frame_generic` writes every series
   `load_eia_hourly_benchmark` returns and that dict carries `oil` today. This is the identical
   "carry it when present, fall back cleanly" pattern the `other` (NG: OTH) series already uses, so
   a bundle predating it regresses to today's behaviour rather than crashing;
2. add `oil` to **both** sides of `reconcile_vintage_classes` — the 930 target and the 923 `_cur`.

**ZERO LP to develop, and no ScenarioConfig field moves** — it is a benchmark construction, so no
mechanism-matrix cell changes and no DOF entry is created.

**But it is not free, and it is not this lane's to land:**

- **Cross-ISO reach.** It can change the benchmark in **12 cells across 7 ISOs**, 11 of them other
  lanes' (§1). Rule 25 `[R-ISO-SCOPE]`, and the explicit nyiso-232 precedent — *"the shared-scorer fix
  is NOT landed here (rule 25)"* — both point the same way. I have **not** measured the other 11
  cells' verdict impact; doing so needs each ISO's hydrated profile and is a cross-lane job.
- **Realizing it for NYISO costs a re-solve.** A bench part is regenerated only from a bundle's
  `dispatch/` + `system.parquet`, and the keeper bundle on `main` carries neither (keeper-only
  retention, rule 15). The nyiso-238 shard branches that held them are **already unreachable** —
  `cd86a01a`, `f42ef900`, `40ecf0a8`, `ff7e024e` all return "could not get object info", 4 days after
  they were written. Under rule 34 `[R-SHARD-PROMOTABLE]` (c) the re-solve covers **all four years**:
  **~15 min per year, ~18 min wall in four parallel shards.**
- **ERCOT's 930 path is separate** (`_eia930_frame`, not `_eia930_frame_generic`) and I have not
  checked whether its extract carries `oil`. ERCOT's reconcile fires in **no** year, so nothing moves
  there today — but that is an open item, not a cleared one.

**MY RECOMMENDATION: land it, with sign-off, as a cross-ISO bench repair — not as a NYISO change.**
Rule 14 `[R-ACCURATE]` is explicit that the accurate input stays even when the fit moves, and here
four independent sources agree against one. But the correct shape is a **shared repair plus a
per-ISO re-render census**, not a NYISO lane quietly changing seven ISOs' benchmarks. If the answer
is yes, the NYISO half is one PRECOMMIT and four shards.

**Two questions, then:**
- **Q1.** Land the `reconcile_vintage_classes` gas+oil basis repair? (yes / yes-but-census-first / no)
- **Q2.** If yes — does this lane re-solve NYISO's four years to re-render its bench and re-register,
  or does that wait for the cross-ISO census?

**Nothing is at risk while the answer takes time.** This session solved nothing, so there is no
bundle on ephemeral disk and rule 31 `[R-RETAIN]` has nothing to protect. The probe and this document
are the whole record and both are committed.

---

## 8. GOVERNANCE

* **Rule 1 `[R-STRUCT]`** — `authorized_price_tuning` **NONE**; zero offer-curve multipliers move,
  zero mechanisms armed. The counterfactual determination is reported as a consequence, never as the
  selection criterion; the selecting evidence is §2's identity, §3's four sources and §4's shape.
* **Rule 13 `[R-MEASURED]` / 14 `[R-ACCURATE]`** — the repair prefers the better-grounded of two
  measurements of one physical quantity, and §3a's arbiter is the ISO's own published meter. The
  reconcile's target is defined on a different **fuel boundary** than the 923 classes it scales —
  rule 14's misalignment case exactly, and the remedy is the reconciled version, not a guess.
* **Rule 21 `[R-DOF]`** — **zero free parameters**; no literal, threshold or share is introduced. The
  ±3 % deadband is untouched.
* **Rule 25 `[R-ISO-SCOPE]`** — the reason this is not landed in a NYISO lane. See §7.
* **Rule 28 `[R-MECH-MATRIX]`** — the lever queue and `mechanism-matrix/NYISO.js` were read before
  anything was proposed. **No cell moves**: this is a bench construction, not a `ScenarioConfig`
  mechanism, and it has no matrix row. The DO-NOT-REDO set was honoured — the Central-East seam,
  `nyiso_total_east_cutset_ttc`, the hourly-TTC grain, the West export outlet, the firm-import floor,
  the hydro equality floor and the hydro period lengths are **untouched and not re-tested**.
* **Rule 29 `[R-SCREEN]`** — clause (0) zero-LP phase 0 answered the question outright; no screen was
  owed and none was spent.
* **Rule 32 `[R-SHARD]`** — the parent ran no LP and launched no shard. Nothing to archive (rule 33),
  nothing to retain (rule 31).
* **Class-E parity** — `caiso279_ablate_dswcouple_span` and `soco15_spp_arm` remain pre-existing REDs
  and are **not NYISO's** (rule 25): reported, untouched.
* **`audit_keepers` E11** — the pre-existing warning that former keeper `2026-09-13-nyiso231-anchor-span`
  has no resolvable bundle is unchanged and still handed forward.
