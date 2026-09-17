# RESULT — nyiso-239: NYISO reads `CALIBRATED`. Zero model fields moved; the C1 benchmark was straddling a fuel boundary

**Session** nyiso-239 (ORCHESTRATOR — rule 32 `[R-SHARD]` (a); **the parent ran ZERO LP**).
**Date** 2026-09-17. **Base** `origin/main` at `73281357`.
**Owner ruling** (2026-09-17, verbatim): *"Is this a recommended keeper candidate? If so plz promote. If structural integrity improves but gates regress that may still be a keeper.."*
**Pre-registration** `docs/PRECOMMIT-nyiso239-bench-oil-rerender-2026-09-17.md`, pushed at `3edb8ad8ce4737b2f860d84e58bae26e4cb6aa1c` **before the first LP**.
**Phase-0 evidence** `docs/FINDING-nyiso239-c1-2022-bench-oil-attribution-2026-09-16.md`; probe `scripts/probes/nyiso239_c1_bench_oil_phase0.py`.

> ## HEADLINE
> 1. **NYISO's registered four-year span goes `NOT-YET` → `CALIBRATED`** — grade 6 → 7, fails 2 → 0,
>    C3c the lone ledgered caveat. C1 / C2 / C3a / C3b / C4 / C6 / C8 all PASS. **Zero PASS → FAIL
>    flips anywhere.**
> 2. **ZERO `ScenarioConfig` fields moved.** The new keeper IS the old one, replayed byte-faithfully —
>    worst per-class deviation **5.0 × 10⁻⁷ TWh** over four years (gate G-1), and every one of the 20
>    committed bundle sidecars is a **`git` `R100` exact rename**, i.e. byte-identical. The model did
>    not change, and that is checkable rather than asserted.
> 3. **What changed is the ruler.** The C1 benchmark's vintage reconcile compared EIA-923's gas classes
>    against EIA-930's `gas` cell **alone**, which omits `NG: OIL`. Four independent sources say that is
>    the wrong boundary; the decisive one is **hourly shape**, which no level scale can fake.
> 4. **The cross-ISO census was done BEFORE the shared edit landed** (rule 25): the reconcile fires in
>    12 of 41 bench parts and the repair moves the verdict in **exactly one — NYISO 2022**. Measured at
>    registration, the only bench bytes that moved anywhere are NYISO's four.
> 5. **The model's `CC_REGULAR` over-run did not go away and is not claimed to have.** It is +3.14 TWh,
>    the share leg passes by **~0.05 pp of a ±3.0 pp band**, and it remains this lane's open object.

---

## 1. WHAT WAS PROMOTED

| | |
|---|---|
| **keeper** | `2026-09-17-nyiso239-bench-oil-basis` |
| bundle | `results/calibration/nyiso239_bench_span` |
| years | 2022, 2023, 2024, 2025 |
| supersedes | `2026-09-16-nyiso-238-hydro-budget` (pruned in this session, rule 35 `[R-PROMOTE]` (a)) |
| `solve_surface.fingerprint` | `bd2b4657f9b5df7e` — **unchanged** |
| `authorized_price_tuning` | **NONE** |
| free parameters | **zero new**; the DOF ledger carries over byte-identical |

Four per-year shards, each `scripts/replay_keeper.py results/calibration/nyiso238_hydroperiod_span
--years <YR>` with **no `--set`**, at the pinned SHA; composed in the parent by
`scripts/probes/nyiso238_compose_span.py` (zero LP). Wall: **~20 min** for all four in parallel.

---

## 2. THE OBJECT — C1 `CC_REGULAR` 2022 was measured against a deflated actual

`render_calibration_html.reconcile_vintage_classes` scales the EIA-923 grid-delivered fossil classes
to the EIA-930 grid series whenever the two differ by more than ±3 %. Its target was EIA-930's
`gas + coal` cell **alone**.

EIA-923 books a plant's MWh under the fuel it **burned**: a dual-fuel unit's oil hours land in the
923 `oil` class while its gas hours stay in the CC/CT/ST classes. EIA-930 books that same generation
under `NG: OIL`. So the comparison **straddled a fuel boundary** and read an **attribution**
difference as a **level** error.

| yr | 923 fossil | 930 gas | dev | **fires** | 923+oil | 930+oil | dev | fires |
|---|---:|---:|---:|:--:|---:|---:|---:|:--:|
| **2022** | 63.351 | 60.257 | **+5.13 %** | **YES** | 65.194 | 65.142 | **+0.08 %** | no |
| 2023 | 61.662 | 60.999 | +1.09 % | no | 62.084 | 63.174 | −1.72 % | no |
| 2024 | 65.892 | 67.731 | −2.72 % | no | 66.214 | 68.022 | −2.66 % | no |

`923 fossil − 930 gas = +3.094 TWh` against `930 oil − 923 oil = +3.041 TWh` — **matching to
0.053 TWh**, the signature of a transfer between two cells rather than a level error in either.

**This completes the function's own design rather than extending it.** Its docstring already refuses
to let EIA-930's *fuel attribution* drive the 923 split, because against CAMPD "EIA-930 MIS-SPLITS
coal vs gas by 7–21 TWh/yr". The gas↔oil boundary is the same error one fuel over.

### 2.1 Four arbiters, and the one that cannot be faked

* **NYISO's own published hourly fuel mix.** The ISO publishes **no `oil` category at all** —
  oil-capable units file under **`Dual Fuel`**. Against its fossil total, 930-gas-alone is
  **−5.413 TWh** in 2022 and **−2.337** in 2023; gas+oil is **−0.528** and **−0.162**. In **2024**,
  the year the mislabelled block is already gone, the repair is a **near no-op** (+0.150 → +0.440).
  *A residual-fitted correction does not switch itself off in the year the defect is absent.*
* **EIA-923's own routing.** `_classify_f923` sends **100 %** of DFO / RFO / JF / KER / WO / PC to
  `oil`. The ~3 TWh EIA-930 calls oil in 2022 is not oil **fuel** by the 923 survey.
* **The block's own shape.** 930 `NG: OIL` GWh/month in 2022:
  `[467, 433, 438, 450, 165, 422, 468, 483, 344, 429, 381, 405]` — a flat ~550 MW **baseload**, every
  month. It steps to ~zero at **2023-m07**. New York's liquid fleet is *peaking* plant.
* **CEMS**, fixed 67-plant set metered in all four years: `930gas/CAMPD` = **0.9061** (2022) vs
  **0.9554 / 0.9555 / 0.9635**.
* **SHAPE — the leg no level scale can move.** model(gas+oil) vs 930(gas+oil) beats model(gas) vs
  930(gas) on **r AND NRMSE in all four years — 8 of 8**; 2022 r 0.8681 → **0.9507**, NRMSE 0.1901 →
  **0.1028**.

---

## 3. THE PRE-REGISTERED GATES — all five, as declared

| gate | prediction | result |
|---|---|---|
| **G-1 replay fidelity** (STOP) | composed legs reproduce the keeper's class hourlies to ≤ 0.001 TWh | **PASS, and far harder than the gate asked** — worst **5.0 × 10⁻⁷ TWh** (2023 `solar`), 0 of 64 class-years over tolerance; then `git` independently detected **all 20** bundle sidecars as **`R100` exact renames**, i.e. the replay is **byte-identical**, not merely within tolerance |
| **G-2 bench confinement** | NYISO 2023 + 2024 `classFull` byte-identical | **PASS** — both **byte-identical**; only the new `e930.oil` key appears there |
| **G-3 the predicted C1 row** | `CC_REGULAR` 2022 actual 31.586 → **33.207**, Δ +3.19 TWh, share +2.97 pp, FAIL → PASS | **PASS on the verdict; the 4th digit MISSED** — landed **33.259**, Δ **+3.139**, share **+2.95 pp**. See §3.1 |
| **G-4 no other ISO moves** | no bench bytes change outside `NYISO/` | **PASS** — the only four changed parts are NYISO's |
| **G-5 determination** (reported, not gated) | NOT-YET → CALIBRATED | **CALIBRATED**, grade 7, fails 0 |

### 3.1 G-3's fourth digit was wrong, and why — recorded rather than smoothed over

I pre-registered the 2022 `CC_REGULAR` actual **to four digits** as 33.207 TWh. It landed at
**33.2590** — **+0.052 TWh, +0.157 %**. The direction, the mechanism and the band verdict were all
right; the precision claim was not.

The cause is named in the phase-0 FINDING itself: the pre-registered value came from a
**reconstruction** of the pre-scale `classFull` (raw EIA-923 through `apply_other_fossil_scoring`,
minus the bench BTM), which does **not** include the CAMPD backfill the render applies. That backfill
is the 0.052 TWh. **A four-digit prediction should not have been written off a three-digit
reconstruction**, and the honest form would have been "33.21 ± 0.06". The gate is scored a PASS on
what it was for — the verdict flip and its magnitude — and the over-claim is recorded here.

---

## 4. CROSS-ISO — measured before landing, not after (rule 25 `[R-ISO-SCOPE]`)

The reconcile fires in **12 of 41** committed bench parts. The repair changes the fire/no-fire
verdict in **exactly one**:

| cell | under the repair |
|---|---|
| **NYISO 2022** | **STOPS FIRING** (+5.13 % → +0.08 %) |
| CAISO 2025, NEISO 2025, NYISO 2025, PJM 2021, PJM 2022, SOCO 2023, SOCO 2024, SPP 2023, SPP 2024, SPP 2025 | NO CHANGE — still fires; scale factor moves **−1.53 % to +0.29 %**, 9 of 10 under **0.30 %**, and only when that ISO next re-renders |
| MISO 2025, all ERCOT | **FALLBACK** — no `oil` series in the extract, byte-identical by construction |

**Verified at registration**: the only bench parts whose bytes moved anywhere are NYISO's four, and
two of those moved only by gaining the `e930.oil` key.

The fallback is the same "carry it when present" contract the `NG: OTH` (`other`) series already
established, so **no committed bundle can regress**. Guard:
`tests/scoring/test_vintage_reconcile_oil_family.py` — 6 tests pinning the live NYISO 2022 numbers on
both bases, the byte-identical fallback, the family invariant, and the CAISO anchor cap.
`tests/scoring` failure-set diff before/after: **zero new failures**.

---

## 5. G-DRIFT (rule 29 `[R-SCREEN]` (b)) — form 4, no control solve spent

`git diff 69c6d4a7 HEAD` over the solve path is 6 files / 333 insertions, and every hunk was
classified **INERT for a NYISO backcast** in the PRECOMMIT **before** the arm was solved: a
NEISO-only default-off `ScenarioConfig` field absent from this recipe, its `floors.py` guard, two
NEISO interchange modules, the NWPP hydro-cascade sidecar (returns `None` unarmed), and the NWPP pool
branch of `_eia930_frame_generic` (NYISO is 1:1). **G-1 then confirmed that classification
empirically — at 5.0 × 10⁻⁷ TWh on the class totals, and at `R100` BYTE-IDENTITY on all 20 committed
bundle sidecars** — which is a stronger result than a control solve would have given,
because it says the code is inert rather than that two numbers happen to agree.

---

## 6. THE SCORECARD, AND WHAT IT STILL MISSES

**C1 — every gated row passes, in every gated year.**

| yr | class | model | actual | Δ | share |
|---|---|---:|---:|---:|---:|
| **2022** | **CC_REGULAR** | 36.398 | **33.259** | **+3.14** | **+2.95 pp** |
| 2022 | CC_CHP / CT_PEAKER / ST_GAS / ST_CHP | | | −1.02 / −0.59 / −0.92 / +0.68 | ≤ 0.6 pp |
| 2023 | CC_REGULAR / ST_GAS | 33.258 / 11.540 | 33.012 / 8.141 | +0.25 / **+3.40** | +0.7 / **+2.8 pp** |
| 2024 | CC_REGULAR / CC_CHP | 37.005 / 19.178 | 34.060 / 17.017 | +2.94 / +2.16 | +2.5 / +1.8 pp |

**Stated at full magnitude, because the determination does not excuse it:**

* **The 2022 `CC_REGULAR` share leg passes by ~0.05 pp of a ±3.0 pp band — under 2 % of the band.**
  A keeper that clears C1 on that margin is one input revision from failing again. **ST_GAS 2023
  (+2.8 pp) and CC_REGULAR 2024 (+2.5 pp) sit nearly as close.** This run is CALIBRATED with three
  rows inside half a band of the line.
* **The model's +3.14 TWh `CC_REGULAR` 2022 over-run is REAL.** It is **88 % in NYC**
  (+2.24 of +2.56 TWh plant-level), and **61 % of it is February (+788 GWh) and November
  (+774 GWh)** — while the model runs those same units **cold in Jul–Sep**. Top plants: Zeltmann
  +0.90, Astoria Energy +0.80, Athens +0.69, Bethlehem +0.60, Astoria II +0.39. **That asymmetry —
  hot in the fuel-delivery months, cold in the heat months — is the successor object, and it is a
  fuel / deliverability question, not a benchmark one.**
* **C3c** stays a ledgered model-class caveat: model 7 / 0 / 0 / 3 h > $300 against 101 / 10 / 13 /
  42 actual. Energy-only LMP with no administrative scarcity adder; not this session's object.
* **The G2 hydro energy loss** (−55.2 / −25.5 GWh in 2022 / 2023) carries over **unchanged as a
  LEDGERED OPEN ROOT-CAUSE ISSUE** (rule 21 `[R-DOF]`), **not** an accepted limitation. Nothing in
  this session touched it and no later session should quietly reclassify it.

---

## 7. RETRIEVABILITY (rule 34 `[R-SHARD-PROMOTABLE]` (e))

The registered composite `results/calibration/nyiso239_bench_span` is **committed**. The four
per-year legs are kept out of `main` (rule 32 (d)) and **gitignored, never `rm`'d** (rule 31
`[R-RETAIN]`). Recovery is by **full SHA**, recorded in `.gitignore` beside the ignore lines because
shard branches are deleted within days:

| year | branch | **commit** | files |
|---|---|---|---|
| 2022 | `claude/nyiso239-bench-2022` | `5802986acd77b69cfeb13720a8f0167f6ccb80a7` | 17 |
| 2023 | `claude/nyiso239-bench-2023` | `0f03dd49b1daee41a1fd0244474e6c4cea7c0c9b` | 17 |
| 2024 | `claude/nyiso239-bench-2024` | `ce299f37da628cf7299cba5422f52f4ab05765bb` | 17 |
| 2025 | `claude/nyiso239-bench-2025` | `9859790c33415e9c6dc54ecfb1c799ecc8fb76da` | 17 |

`git ls-tree -r <sha>` verified 17 files each **before any shard was archived**; each carries
`dispatch/<YR>_P1.parquet` and the bundle-root `system.parquet`.

**A promotion from this state costs zero re-solves.**

---

## 8. GOVERNANCE

* **Rule 1 `[R-STRUCT]`** — `authorized_price_tuning` **NONE**; zero offer-curve multipliers, zero
  mechanisms armed, zero `ScenarioConfig` fields moved. G-1…G-4 are structural/confinement gates;
  the determination (G-5) was declared **reported, not gated**, before the solve.
* **Rule 13 / 14 `[R-MEASURED]` / `[R-ACCURATE]`** — the reconcile's target was defined on a
  different **fuel boundary** than the classes it scaled: rule 14's misalignment case, remedied with
  the reconciled version rather than a guess, and arbitrated by the ISO's own published meter.
* **Rule 21 `[R-DOF]`** — zero free parameters; no literal, threshold or share introduced; the ±3 %
  deadband untouched.
* **Rule 25 `[R-ISO-SCOPE]`** — §4 is the census that made the shared edit safe, and it was run
  **before** landing, not after.
* **Rule 27 `[R-PUSH]`** — Opus session; `render_calibration_html.py` (2,619 lines) edited with the
  Edit tool, and every pushed blob verified against local before the next commit.
* **Rule 28 `[R-MECH-MATRIX]`** — **no cell moves** (a bench construction has no matrix row); the
  promoting-session stamp is landed in `mechanism-matrix/NYISO.js` and the §5.5 prose header, and
  `check_mechanism_matrix.py` is green on both.
* **Rule 35 `[R-PROMOTE]`** — executed in order: year union `{2022, 2023, 2024, 2025}` enumerated
  from the registry **before** the prune (b) and covered exactly (c); promoted and verified with
  `audit_keepers` (E11 `composed_from` declared in the shard prose; M1b determination re-verified),
  **then** the superseded keeper's three stores deleted via `prune_iso_runs.py --force-uncite` (d).
  `audit_keepers --iso NYISO` after: **0 failures, 1 warning** — the E11 lineage warning that is
  inherent to keeper-only retention once the former bundle is gone, and which the check had already
  run and cleared beforehand.

### Reported, not fixed — all pre-existing and none NYISO's

* **`tests/scoring` carries 20 failures on clean `main`** (`test_audit_keepers_lineage` E11/replay
  provenance drift, `test_golden_manifest_provenance`, `test_forecast_parity`, `test_gate_a_provenance`,
  `test_replay_keeper_strict`). Verified by before/after failure-set diff that this session adds
  **zero**. Nobody owns this today.
* **Class-E parity**: `caiso279_ablate_dswcouple_span` and `soco15_spp_arm` remain unmapped REDs and
  are not NYISO's. This session's own four leg dirs also appear in that list — expected, and exactly
  the corrected rule-31 clause: the gate walks the **filesystem**, so gitignored legs turn it RED
  **locally** while CI, which checks out only what is committed, stays green.
* **`check_mechanism_matrix.py` warns that NEISO's §5.x prose header does not name its designated
  keeper** (`2026-09-16-neiso110-dualfuel-derate-scope`) — that lane's rule-28 duty, left owed.
* **`dashboard_add_run.py`'s docstring still describes `enforce_registration_marker_gate`**, which no
  longer exists (removed with `[R-HOLDOUT]`, 2026-09-09). Harmless but stale.
