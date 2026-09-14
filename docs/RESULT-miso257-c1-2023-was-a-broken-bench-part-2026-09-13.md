# RESULT (miso-257) — MISO's last rubric failure was a BROKEN BENCH PART, not a model miss.
# The train tier now reads CALIBRATED.

```
SESSION : miso-257           ISO: MISO           KEEPER: 2026-09-12-miso-255-sil-measured
BASE    : origin/main @ 1d533985
LP SPENT: ZERO. The parent solved nothing and NO SHARD WAS LAUNCHED (rule 32 [R-SHARD] (a)).
RESULT  : The C1-2023 CC_CHP -19.71 TWh and COAL_PRB +8.02 TWh cells are BOTH artifacts of a
          benchmark part the miso-255 registration wrote WITHOUT the behind-the-meter CHP
          subtrahend. Regenerating MISO's six bench parts at zero LP closes both cells and the
          MISO TRAIN TIER (2023-2025) FLIPS **NOT-YET -> CALIBRATED**.
```

---

## 1. RESULT

> **The committed MISO **2023** and **2025** bench parts do not subtract the BTM CHP host
> supply from `classFull`. Every other MISO year does, the pre-registration parts did, and the
> rubric requires it — C1 scores a GRID-ONLY model against `EIA-923 minus the per-class BTM
> host supply`. The model was being asked to match a number that includes ~21 TWh of
> generation it never dispatches.**
>
> | | before | after |
> |---|---|---|
> | keeper `2026-09-12-miso-255-sil-measured`, **train tier 2023-2025** | **NOT-YET** (C1 FAIL) | **CALIBRATED** |
> | keeper, full span 2020-2025 | NOT-YET | NOT-YET (unchanged; held-out 2020/21/22) |
> | superseded `2026-09-09-miso-250-ep-gas` (2023-2025) | NOT-YET, grade 6, 1 fail | **CALIBRATED**, grade 7, 0 fails |
> | `2026-09-10-miso-251-{tp2020,tp2021,screen2022}` | NOT-YET | NOT-YET (byte-unchanged) |
>
> **This is a BASIS CORRECTION and must not be root-caused in the model** (the task card's own
> instruction, and the pjm-h4 precedent). The model side is untouched: no solve, no config, no
> `ScenarioConfig` field, no mechanism, no matrix cell verdict.

## 2. THE EVIDENCE, IN THE ORDER IT DECIDES

### 2.1 The identity that `classFull` must satisfy

For a CHP class, `bench.classFull[k] = EIA-923 class total[k] − btm.parquet subtrahend[k]`
(modulo small multi-class-split adjustments). Measured on the keeper's own committed shared
EIA-923 input and the rebuilt `btm.parquet` (TWh):

| yr | class | e923 total | btm | e923 − btm | **committed** | committed − (e923−btm) |
|---|---|---:|---:|---:|---:|---:|
| 2020 | CC_CHP | 39.7575 | 19.3411 | 20.4163 | 20.4163 | **−0.0000** |
| 2021 | CC_CHP | 35.4811 | 17.5958 | 17.8852 | 17.8852 | **−0.0000** |
| 2022 | CC_CHP | 38.8687 | 19.9150 | 18.9536 | 18.9536 | **−0.0000** |
| **2023** | **CC_CHP** | 42.2726 | 20.9613 | 21.3113 | **39.0080** | **+17.6967** |
| 2024 | CC_CHP | 42.1764 | 20.8375 | 21.3389 | 21.3389 | **−0.0000** |
| **2025** | **CC_CHP** | 37.1245 | 20.1775 | 16.9470 | **37.1245** | **+20.1775** |

2025's committed value is the EIA-923 class total **to the last digit** — the subtrahend was
not applied at all. 2023's is short by 17.70 of the 20.96 TWh it should carry. Four of six
years satisfy the identity exactly.

### 2.2 The git record dates the defect to the miso-255 REGISTRATION

`frontend/data/backcast/bench/MISO/<year>.json.gz`, `classFull.CC_CHP`:

| commit | when | 2023 | 2024 | 2025 |
|---|---|---:|---:|---:|
| `4a44e53d` (pre-miso-255) | 2026-09-11T20:22 | **21.3113** | 21.3389 | 17.7504 |
| `3cd1021b` (miso-255 registration) | 2026-09-13T05:18 | **39.0080** | 21.3389 | 37.1245 |
| **this session's rebuild** | 2026-09-13 | **21.3113** | 21.3389 | 17.7796 |

The rebuild reproduces the pre-registration 2023 value **exactly** and 2025 to +0.029 TWh
(genuine engine drift over two days). 2024 never moved in either direction.

**Cause, stated to the limit of what is measurable.** The proximate cause is the `btm.parquet`
inside the composite bundle the miso-255 parent registered: it did not carry the 2023 and 2025
subtrahend. That artifact is gitignored and did not survive the registering container, so the
exact defect cannot be reconstructed and this document does not guess at one. Two candidate
causes were tested and **eliminated**: `760012f7` (the EIA-860 vintage cache re-keying) is
byte-inert for MISO, which does not arm `eia860_vintage_tracks_solve_year`, and it landed
*after* the registration; and the whole engine delta `4a44e53d → HEAD` is inert here too,
proved by the 2023 rebuild reproducing `4a44e53d`'s value bit for bit.

The structural lesson is the one pjm-h4 §2 already recorded from the other side: **omitting
`btm.parquet` at render time silently inflates every CHP class's metered actual**, and nothing
in the registration path notices.

### 2.3 The gate that makes the reconstruction admissible

The keeper bundle is the SLIM committed form, so `dispatch/`, `system.parquet` and
`btm.parquet` had to be reconstructed before `build_payload` could run
(`scripts/probes/_miso257_bench_rebuild.py`, recipe from
`docs/RESULT-pjm-h4-bench-move-landed-2026-09-13.md` §2). The rebuilt part is accepted ONLY if
its plant key set and every dispatch-scoped field (`name / zone / group / npl / nodata / campd
/ c_ann / c_mon`) come back byte-identical (`scripts/probes/_miso257_bench_gate.py`):

| year | plants | key set + dispatch-scoped fields |
|---|---:|:--|
| 2020 | 266 | **IDENTICAL** |
| 2021 | 260 | **IDENTICAL** |
| 2022 | 256 | **IDENTICAL** |
| 2023 | 248 | **IDENTICAL** |
| 2024 | 244 | **IDENTICAL** |
| 2025 | 244 | **IDENTICAL** |

**2020, 2021, 2022 and 2024 come back with ZERO movement in `classFull`, `e930` or `avgLMP`** —
so the rebuild is a no-op in four of six years and the two that move are the two the
registration broke. (2020 and 2021 still change on disk: they were written by miso-256 through
a different serializer, which is what
`tests/scoring/test_backcast_artifacts.py::test_committed_bench_parts_rewrite_byte_identical`
was failing on. Both failures are now closed — see §5.)

## 3. THE CORRECTED C1-2023 TABLE — the step-2 deliverable

Model unchanged. Band 8.0 TWh volume / 3.0 pp share.

| class | model | act BEFORE | act AFTER | res BEFORE | res AFTER | gate |
|---|---:|---:|---:|---:|---:|:--|
| CC_REGULAR | 135.326 | 130.865 | **141.817** | +4.46 | **−6.49** | PASS → PASS |
| **CC_CHP** | 19.302 | 39.008 | **21.311** | **−19.71** | **−2.01** | **FAIL → PASS** |
| CT_PEAKER | 16.539 | 15.723 | 17.038 | +0.82 | −0.50 | PASS → PASS |
| ST_GAS | 14.194 | 12.863 | 13.940 | +1.33 | +0.25 | PASS → PASS |
| ST_CHP | 2.460 | 6.165 | 5.203 | −3.71 | −2.74 | PASS → PASS |
| **COAL_PRB** | 120.296 | 112.275 | **121.671** | **+8.02** | **−1.38** | **FAIL → PASS** |
| COAL_LIGNITE | 6.335 | 6.503 | 7.047 | −0.17 | −0.71 | PASS → PASS |
| COAL_BIT | 53.767 | 52.662 | 57.069 | +1.11 | −3.30 | PASS → PASS |

**COAL_PRB was the same defect, not a second object.** The task card asked whether the two
cells share a displacement; they share a *cause*. The CHP classes' inflated actuals had to come
out of the other classes' actuals — the 2023 part put ~29 TWh into CC_CHP/CT_CHP/ST_CHP that
the correct part puts in CC_REGULAR/COAL_PRB/COAL_BIT — so COAL_PRB's actual was understated by
9.40 TWh and the model read +8.02 over it. Rule 19 `[R-ONE-MECH]` is satisfied by construction:
one repair, both cells.

**No status flips in 2024 or 2025** on any C1 class. Every 2025 C1 row is SKIPPED on the
preliminary EIA-923 vintage in both readings, so the (larger) 2025 bench move touches no gate.

## 4. EVERY OTHER SCORED RECORD, AT FULL MAGNITUDE

* **C2 system volume moves and improves**: 2025 gas −8.4 % → **−7.1 %**, coal +0.6 % → **−1.0 %**
  (both SKIPPED-reported, both PASS as a criterion before and after).
* **The held-out years 2020 / 2021 / 2022 are byte-unchanged** — their bench parts did not move,
  and their failures stand exactly as before: C1 2021 CC_REGULAR −15.94; C1 2022 CC_REGULAR
  −28.52 / COAL_PRB +32.04 / COAL_BIT +10.39; C3a 2020 +22.9 % / 2022 −23.4 %; C3b 2020 0.246 /
  2021 0.290 / 2022 0.288; C4 2022 gas r = 0.838. Under rule 30(c) they are REPORTED and never
  downgrade the ISO. The `miso-256` passthrough-slope finding is untouched by this repair.
* **C3a / C3b / C3c / C4 / C6 / C8 do not move in any year** — none of them reads `classFull`.
* **The `runs/<id>.js` payloads are NOT regenerated, and the Run Explorer's `volErr` /`nonFosErr`
  heatmaps for MISO 2023 and 2025 are now stale — reported, not hidden.** They are baked at
  render time against the actuals of the day; **no gate reads either** (`score_fuelmix`
  recomputes C1 from `ypay.gmModel` and `ybench.classFull`), which is why the re-score above is
  correct. Refreshing them needs a full bundle, i.e. a six-year re-solve, which §6 declines.

## 5. TESTS

`tests/scoring/test_backcast_artifacts.py::test_committed_bench_parts_rewrite_byte_identical`
FAILED on `MISO/2020` and `MISO/2021` at base ("carries HEAD's stamp yet differs") and **passes
now**. The cause was not non-determinism in the writer: `miso-256` wrote those two parts with a
compact `json.dumps` (`{"bench":{...` , no separator spaces) instead of
`backcast_artifacts.write_bench_part`, so the payloads were equal and the bytes were not.
Re-writing them through the real writer closes it.

## 6. WHAT I DID NOT DO, AND WHY

* **No LP, no shard, no re-registration.** The change is bench-only; the reconstruction gate
  proves the dispatch-scoped half is untouched; a re-solve would spend ~35-70 min per arm
  reproducing an identical model side.
* **No CC_CHP mechanism was proposed or screened.** The task card's step 2 said "if CC_CHP moves
  materially, the object changed and step 3 is re-chartered". It moved 17.70 TWh and the
  residual is now −2.01 TWh against an 8.0 TWh band. **There is no object left to charter**, and
  spending a screen on it would be spending LP on a closed cell.
* **No model root-cause opened**, per the card.
* **Nothing deleted beyond the rule-35 prune in §7**, which the owner's miso-255 promotion
  already authorized (rule 31 `[R-RETAIN]` trigger (i)).

## 7. HOUSEKEEPING — rule 35 `[R-PROMOTE]`, discharged

**(b) The year union, enumerated BEFORE anything was deleted.** Over every MISO registry
sidecar:

| run | years | stamped to |
|---|---|---|
| `2026-09-09-miso-250-ep-gas` | 2023, 2024, 2025 | (none) |
| `2026-09-10-miso-251-screen2022` | 2022 | `2026-09-09-miso-250-ep-gas` |
| `2026-09-10-miso-251-tp2020` | 2020 | `2026-09-09-miso-250-ep-gas` |
| `2026-09-10-miso-251-tp2021` | 2021 | `2026-09-09-miso-250-ep-gas` |
| **`2026-09-12-miso-255-sil-measured` (KEEPER)** | **2020–2025** | — |
| **UNION** | **2020, 2021, 2022, 2023, 2024, 2025** | |

**(c) The incoming keeper covers the union in its own bundle**, so no year is lost and no
re-stamp is owed. **PRUNE, not re-stamp**, is the correct disposition of the other four: rule
30(a)'s fold is for *the keeper's own frozen recipe replayed on another year*, and all three
`miso-251` touchpoints are replays of the SUPERSEDED `miso-250` recipe on years the keeper
already carries in-bundle. Folding them would put a different configuration's years in the
keeper's own year selector.

## 8. RULES

Rule 14 `[R-ACCURATE]` (the corrected basis is kept, and the residual it exposes — or removes —
is reported at full magnitude) · rule 15 `[R-DASHBOARD]` (the bench parts are the committed
deliverable, pushed in the session that produced them) · rule 19 `[R-ONE-MECH]` (one repair,
both cells) · rule 29 `[R-SCREEN]` clause 0 (zero-LP phase 0 first — and it ended the lane) ·
rule 30(c) (no held-out year touches MISO's determination) · rule 31 `[R-RETAIN]` (nothing
deleted whose promotion is undecided) · rule 32 `[R-SHARD]` (a) (the parent ran no LP) · rule 35
`[R-PROMOTE]` (the outgoing keeper's stores are swept in §7).
