# PRE-REGISTRATION — nyiso-239: re-solve NYISO 2022–2025 to re-render the bench on the oil-inclusive reconcile family, then re-register and promote

**Session** nyiso-239 (ORCHESTRATOR — rule 32 `[R-SHARD]` (a); **the parent runs ZERO LP**).
**Date** 2026-09-17. **Base** `origin/main` at `73281357`.
**Incumbent keeper** `2026-09-16-nyiso-238-hydro-budget` (bundle `results/calibration/nyiso238_hydroperiod_span`), years {2022, 2023, 2024, 2025}.
**Owner ruling that authorizes this** (2026-09-17, verbatim): *"Is this a recommended keeper candidate? If so plz promote. If structural integrity improves but gates regress that may still be a keeper.."* — given on
`docs/FINDING-nyiso239-c1-2022-bench-oil-attribution-2026-09-16.md`, whose §7 put exactly this
question (Q1 land the repair, Q2 re-solve to realize it).

**THIS IS PUSHED BEFORE THE FIRST LP.** Its commit SHA is the `source_revision` every shard pins.

---

## 1. WHAT MOVES, AND WHAT DOES NOT

**ZERO `ScenarioConfig` fields move. The MODEL is untouched.** The recipe the shards replay is the
incumbent keeper's own `meta.json`, byte-faithfully, via `scripts/replay_keeper.py` with **no
`--set`**. This is not a new mechanism, a new arm or a new configuration: it is the **same keeper
re-solved so its bundle carries the `dispatch/` + `system.parquet` artifacts a bench re-render
needs**, which the committed keeper does not (keeper-only slim retention, rule 15 `[R-DASHBOARD]`)
and which the nyiso-238 shard branches no longer hold (`cd86a01a`, `f42ef900`, `40ecf0a8`,
`ff7e024e` are all unreachable).

**What changes is the BENCHMARK**, through three edits landed in this same commit:

| file | change |
|---|---|
| `scripts/lib/benchmark_semantics.py` | new `OIL_GROUPS = ("oil",)` — the third reconcile-family member |
| `scripts/render_calibration_html.py` | carry EIA-930's `NG: OIL` cell into the bench part's `e930` **when the bundle's extract has it** |
| `scripts/render_calibration_html.py` | `reconcile_vintage_classes`: oil joins the family on **both** sides (target and current), and the CAISO CEMS-anchor cap gains the 923 oil block so the cap spans the same boundary as the sum it caps |

Guard: `tests/scoring/test_vintage_reconcile_oil_family.py` (6 tests) pins the live NYISO 2022
numbers on both bases, the byte-identical fallback, the family invariant, and the anchor cap.

---

## 2. WHY — and it is NOT the residual (rule 1 `[R-STRUCT]`, rule 14 `[R-ACCURATE]`)

EIA-923 books a plant's MWh under the fuel it **burned**, so a dual-fuel unit's oil hours land in the
923 `oil` class while its gas hours stay in the CC/CT/ST classes. EIA-930 books that same generation
under `NG: OIL`. The reconcile's target was EIA-930's `gas + coal` cell **alone**, so the comparison
straddled a fuel boundary and read an **attribution** difference as a **level** error.

This is the identical failure the function **already refuses to propagate one fuel over** — its own
docstring declines to force EIA-930's coal/gas attribution onto the 923 split because that
attribution is unreliable against CAMPD. The repair completes that design; it does not extend it.

The selecting evidence is a fuel IDENTITY, a SHAPE and a source the model never sees — never a gate:

* NYISO 2022 reads **+5.13 %** gas-only and **+0.08 %** with oil on both sides, the tightest
  agreement of any complete NYISO vintage; `923 fossil − 930 gas = +3.094` against
  `930 oil − 923 oil = +3.041` TWh.
* **NYISO's own published hourly fuel mix** (no `oil` category; oil-capable units file as
  `Dual Fuel`): the repair closes a **−5.413 TWh** gap in 2022 and **−2.337** in 2023 and is a
  **near no-op in 2024**, the year the mislabelled block is already gone.
* **EIA-923 routes 100 %** of DFO/RFO/JF/KER/WO/PC to `oil`.
* The **930 `NG: OIL` block is flat** at ~550 MW every month of 2022 and steps to ~zero at 2023-m07.
* **CEMS**, fixed 67-plant set: `930gas/CAMPD` **0.9061** in 2022 vs 0.9554 / 0.9555 / 0.9635.
* **SHAPE**, which no level scale can fake: model(gas+oil) vs 930(gas+oil) beats model(gas) vs
  930(gas) on **r AND NRMSE in all four years, 8 of 8**.

Full record: `docs/FINDING-nyiso239-c1-2022-bench-oil-attribution-2026-09-16.md`; probe
`scripts/probes/nyiso239_c1_bench_oil_phase0.py`.

---

## 3. CROSS-ISO BLAST RADIUS — measured before landing, not after (rule 25 `[R-ISO-SCOPE]`)

The reconcile fires in **12 of 41** committed bench parts. The repair changes the fire/no-fire
verdict in **exactly ONE: NYISO 2022.**

| cell | verdict under the repair |
|---|---|
| **NYISO 2022** | **STOPS FIRING** (+5.13 % → +0.08 %) |
| CAISO 2025, NEISO 2025, NYISO 2025, PJM 2021, PJM 2022, SOCO 2023, SOCO 2024, SPP 2023, SPP 2024, SPP 2025 | NO CHANGE — still fires |
| MISO 2025, and all ERCOT | **FALLBACK** — extract carries no `oil` series, byte-identical |

Where it still fires the scale factor moves by **−1.53 % to +0.29 %**, and **9 of 10 by less than
0.30 %** — and only **when that ISO next re-renders**, which is its own lane's action, not this one's.
The single outlier is NYISO 2025 (−1.53 %), this lane's own ISO and a preliminary-vintage year
where C1 is SKIPPED regardless. No other lane's committed bytes move today.

---

## 4. G-DRIFT (rule 29 `[R-SCREEN]` (b)) — form 4 is VALID, no control solve is spent

`git diff 69c6d4a7 HEAD -- src/market_sim scripts/run_calibration*.py scripts/lib …` is 6 files /
333 insertions. Every hunk classified **INERT for a NYISO backcast**, with its reason:

| hunk | classification |
|---|---|
| `scenarios.py` `neiso_coldsnap_derate_dualfuel_unswitched: bool = False` | new field, **default-off AND absent from the keeper's recipe** |
| `data/fleet/floors.py` conditional dual-fuel exemption | guarded by that flag |
| `model/interchange/neiso.py`, `model/interchange/spec.py` | **another ISO's branch** |
| `run_calibration*.py` `_hydro_cascade_frame` | returns `None` unless `hydro_cascade_coupling` is armed (NWPP); pure persistence accounting |
| `run_calibration*.py` `_eia930_frame_generic` pool branch | dispatched on `_is_pool_region`; NYISO is 1:1 and takes the unchanged loader path |

**All INERT ⇒ the incumbent keeper's committed bundle IS the control**, and the replay must reproduce
it. That is checkable and is gate G-1 below.

---

## 5. THE SHARDS — four, one per year (rule 32 `[R-SHARD]` (b), as read for THIS LANE by the nyiso-238 PRECOMMIT addendum-1 owner instruction)

```
python3 scripts/replay_keeper.py results/calibration/nyiso238_hydroperiod_span \
  --years <YR> --out-dir results/calibration/nyiso239_bench_<YR>
```

No `--set`. No config override. Each shard pushes its **FULL** bundle to **its own branch** under
rule 34 `[R-SHARD-PROMOTABLE]` (a), via a `.gitignore` **negation** and a **plain `git add`** (never
`-f`, never `-A`), and the bundle **must** include `dispatch/<YR>_P1.parquet` and the bundle-root
`system.parquet` or registration raises `FileNotFoundError`.

Rule 34 (c): the ISO's registered year union is **{2022, 2023, 2024, 2025}** — enumerated from
`frontend/data/backcast/registry/*.json` **before** anything is pruned (rule 35 `[R-PROMOTE]` (b)) —
and all four are launched. None is deliberately omitted.

---

## 6. PRE-REGISTERED GATES — declared before any solve, and none is a C1/C3a gate

**G-1 REPLAY FIDELITY (the STOP gate).** Each year's composed class annual TWh must reproduce the
incumbent keeper's committed `hourly/class_hourly_<YR>.parquet` to **≤ 0.001 TWh per class**. This is
the G-DRIFT prediction of §4 made falsifiable. **A miss STOPS the lane** — it would mean a hunk I
classified INERT is live, and the right response is to re-classify it, not to register a run whose
model result silently moved. *(Structural, not a fit gate: it compares the arm to itself.)*

**G-2 BENCH CONFINEMENT.** The re-rendered bench part must change, versus the committed one, in
**exactly** `classFull` (NYISO 2022 fossil classes + `oil`) and the new `e930.oil` key. NYISO
**2023 and 2024 `classFull` must be byte-identical** — they sit inside the deadband on both bases,
so a move there is a defect in the repair.

**G-3 THE PREDICTED C1 ROW.** NYISO 2022 `CC_REGULAR` actual **31.586 → 33.207 TWh**, model
unchanged at 36.398, Δ **+4.81 → +3.19 TWh**, share **+3.62 → +2.97 pp**, row **FAIL → PASS**.
Pre-registered to four digits from the phase-0 probe; a miss is a plumbing error, not a result.

**G-4 NO OTHER ISO'S COMMITTED BYTES MOVE.** `git status` after the re-render must show no change
under `frontend/data/backcast/bench/` outside `NYISO/`.

**G-5 DETERMINATION, REPORTED NOT GATED.** Expected NOT-YET → **CALIBRATED** (grade 6 → 7, fails
2 → 0, C3c the lone ledgered caveat). **This is an OUTCOME, not a criterion**: G-1…G-4 are what
decide whether the lane proceeds, and they are all structural or confinement gates. If the
determination lands elsewhere it is reported as it falls.

---

## 7. STATED AT THE GATE, BEFORE THE RESULT IS KNOWN

* **The share leg passes by 0.03 pp of a ±3.0 pp band** (+2.9676 vs 3.0) — **1.1 % of the band**. A
  keeper that clears C1 on that margin is one input revision from failing again, and this document
  says so in advance so the RESULT cannot present it as comfortable.
* **The model still over-runs `CC_REGULAR` 2022 by +3.19 TWh** and that remains the lane's open
  object: NYC **+2.24 of +2.56 TWh** plant-level (88 %), February **+788** and November **+774** GWh
  (61 % of the annual miss, with the model *under*-running Jul–Sep); Zeltmann +0.90, Astoria Energy
  +0.80, Athens +0.69, Bethlehem +0.60, Astoria II +0.39. **The repair corrects how that miss is
  MEASURED, not the miss.**
* **The G2 hydro loss** (−55.2 / −25.5 GWh in 2022 / 2023) stays a **ledgered OPEN ROOT-CAUSE ISSUE**
  on this keeper, not an accepted limitation, and is not re-litigated here.
* **C3c** remains a ledgered model-class caveat (0 / 0 / 3 h > $300 vs 10 / 13 / 42) and is **not**
  this session's object.

---

## 8. GOVERNANCE

* **Rule 1 `[R-STRUCT]`** — `authorized_price_tuning` **NONE**; zero offer-curve multipliers, zero
  mechanisms armed, zero `ScenarioConfig` fields moved. The gates in §6 are structural/confinement;
  the determination is reported, never gated on.
* **Rule 13/14** — a measured-input boundary repair: the reconcile's target was defined on a
  different **fuel boundary** than the classes it scales, which is rule 14's misalignment case, and
  the remedy is the reconciled version rather than a guess.
* **Rule 21 `[R-DOF]`** — **zero free parameters**. No literal, threshold or share is introduced; the
  ±3 % deadband is untouched. The keeper's DOF ledger carries over byte-identical.
* **Rule 23 `[R-FROZEN-DERIVE]`** — no derive script re-runs.
* **Rule 25 `[R-ISO-SCOPE]`** — §3 is the census that makes the shared edit safe: one cell's verdict
  moves and it is this ISO's. No other ISO's committed bytes change today.
* **Rule 27 `[R-PUSH]`** — Opus session; `render_calibration_html.py` (2,619 lines) is edited with
  the Edit tool and its pushed blob is verified against local before anything else.
* **Rule 28 `[R-MECH-MATRIX]`** — **no cell moves**: a bench construction is not a `ScenarioConfig`
  mechanism and has no matrix row. The promotion re-stamp is already landed (commit `a1608bcb`).
* **Rule 31 `[R-RETAIN]`** — nothing is deleted before the owner has ruled; the incumbent keeper's
  three stores are pruned only **after** the incoming one is registered and `audit_keepers` E1
  passes (rule 35 (e)).
* **Rule 32/33/34** — parent runs no LP; four shards, each pushing its full bundle to its own
  branch; archived once fetched, checked out and verified.
* **Pre-existing, NOT mine, reported:** `tests/scoring` carries **20 failures on clean `main`**
  (`test_audit_keepers_lineage` E11/replay provenance drift, `test_golden_manifest_provenance`,
  `test_forecast_parity`, `test_gate_a_provenance`, `test_replay_keeper_strict`). Verified by
  before/after failure-set diff: **this change introduces ZERO new failures and fixes none.**
  `caiso279_ablate_dswcouple_span` and `soco15_spp_arm` remain pre-existing Class-E parity REDs and
  are not NYISO's.
