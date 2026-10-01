# PRECOMMIT — SOCO-60 (2026-09-23): merge SOCO's two hydro repairs into one recipe, then the 2024 CC_REGULAR phase 0

> Filed as `soco-60b` on rebase: a concurrent session also named SOCO-60 merged its own `PRECOMMIT-soco-60-2026-09-23.md` first. This file was pushed at `f8e534e6` / `71a23bb0` / `eab5c585` under the original name, before any solve.

**Lane** SOCO-60 · **DATA PROFILE** soco · **Model** Opus (rule 27).
Written and pushed **before any LP**. Parent LP cost: zero (rule 32 (a)).

## 0. WHY THIS LANE CHANGED SHAPE — the precondition failed, and the owner ruled

The handoff's precondition was that `keepers/SOCO.json` on `main` names `2026-09-22-soco59-hydro-split`.
It did not. At `fbe00eb1`, `main` names **`2026-09-22-soco-h4-hydro-ror`** (SOCO hydro-4, promoted
2026-09-23 03:21 UTC). SOCO-59's promotion commit (`ef1455df`) and its registration never reached `main`.
Only its PRECOMMIT and the `EIA930_PS_SPLIT_COMPLETE_FROM["SOCO"] = 2025` registry row did (#6486, #6492).
Both lanes promoted themselves over soco58.

The lane stopped and asked. The owner ruled **option 3: merge the two recipes** — a new span, solved
before any CC_REGULAR work.

**Rescued from the unmerged SOCO-59 branch** (rule 33 (f)(4)(i): unique records): its FINDING,
PRECOMMIT addendum B, the soco-data-audit §3.3 correction, `gen_soco59_attestation.py`, and its
`.gitignore` leg block. **Not rescued**: its registry sidecar, run payload and bundle (the merged run
supersedes them), its keeper-shard edit, and its matrix cells, which claim a keeper that never landed.
This lane writes the SOCO-59 cells fresh.

## 1. THE MERGED RECIPE

**Control of record** (rule 29 (b) form 4): keeper `2026-09-22-soco-h4-hydro-ror`, bundle
`results/calibration/soco_h4_ror_span`. That is SOCO-58's recipe plus `hydro_ror_split=True`, with
`hydro_backfill_year=2024` on its 2025 leg. Its per-year legs were recovered at zero LP from
`ba61f313…` / `f2511588…` / `9d113ba2…`. All 12 hourly sidecars are **byte-identical** to the committed
composite.

**Arm = control + `hydro_eia930_monthly=True`** (with `hydro_backfill_year=2024` on every leg; that
setting is array-equal in 2023/2024). No new field and no free parameter. The registry row is already
at HEAD.

**Rule 19: one pipeline, not stacked.** `build_hydro_fleet` repins each plant's monthly budget to the
EIA-930 monthly total (2025 only). `hydro_ror_split` then reads the run-of-river flat level
`budget[g,m]/hours[m]` off **that same budget**. Nothing floors or caps the same MW twice.

**G-DRIFT** (`git diff a5e5f237 HEAD` over the backcast path): every hunk is NWPP-47
(`nwpp_grid_carried_wind_served`, another ISO's branch, default off) **except** the SOCO
`EIA930_PS_SPLIT_COMPLETE_FROM` row. That row is consulted only under `hydro_eia930_monthly` /
`hydro_forecast_budget`, both off in the control, so it is **INERT for the control's LP**. On the
benchmark side it is LIVE (`_hydro_benchmark_is_923_only`), handled in §3. Form 4 is valid.

## 2. PHASE 0 — THE MERGED HYDRO INPUT, MEASURED (zero LP, `build_hydro_fleet`)

| year | control budget | **arm budget** | RoR plants / RoR energy | RoR flat, MW-avg | RoR over-nameplate clip |
|---|---|---|---|---|---|
| 2023 | 6.8150 | **6.8150** (pin refused, PS-folded year) | 14 / 2.424 | 278 | 0.2 GWh |
| 2024 | 6.3015 | **6.3015** (pin refused) | 14 / 2.188 | 251 | 0.1 GWh |
| 2025 | 6.3290 (backfill) | **5.9258** (2025 clean EIA-930) | 14 / 2.028 | 233 | **5.4 GWh** |

17 of the 45 classified plants are RoR-class. 14 of them are LP units, because three are not in the
EIA-923 hydro census. The 2025 repin scales plant budgets by up to 1.53× in May, which puts 5 RoR
plant-months above nameplate. They are clipped: 5.4 GWh, 0.09 % of hydro. The loss is recorded, not
repaired. The reservoir class has zero over-nameplate energy.

2025 monthly shape moves a lot. Arm January is 0.432 TWh (control 0.856), May 0.959 (control 0.626).
The level is 0.403 TWh lower overall.

## 3. PREDICTIONS (ex ante, with falsifiers)

2025 predictions use a difference-in-differences: the arm ≈ SOCO-59's 2025 leg + (hydro-4 ror 2025 −
hydro-4 fix 2025). Each band is ±2× that delta, symmetric (SOCO-58 §5 / SOCO-59 §5).

| # | prediction | falsifier |
|---|---|---|
| P1 | 2023 and 2024 legs: `class_hourly`, `system`, `storage` and `class_band_hourly` **byte-identical** to the control legs | any byte differs |
| P2 | 2025 hydro 5.915–5.926 TWh | outside |
| P3 | 2025 CC_REGULAR 109.26–110.22 TWh (point 109.90) | outside |
| P4 | 2025 CT_PEAKER 4.95–5.67 (point 5.19) | outside |
| P5 | 2025 ST_GAS 2.06–2.37 (point 2.16) | outside |
| P6 | 2025 COAL_PRB + COAL_BIT within ±0.15 of SOCO-59's 48.342 | outside |
| P7 | 2025 unserved energy ≤ 287 MWh and ≤ 2 h (July arm water +5.6 % over the control's) | more |
| P8 | Determination NOT-YET, C1 13/14, C2/C4/C6/C8 PASS, DOF 7/1, grade 5/4/1 | any status moves |
| P9 | On the rebuilt bench (SOCO's 2023/2024 hydro actual → 6.815 / 6.3014, PS fold removed), 2024 CC_REGULAR stays **+9.80 TWh**, share +3.72 → +3.5…+3.7 pp; 2023 ST_GAS share −2.78 → −2.78…−2.85 pp | outside |

**2024 CC_REGULAR is NOT reached by this arm.** Its dispatch is byte-identical to the control (P1). The
arm is taken on rule 14 alone: 2025's own measured water replaces a backfill stand-in, as SOCO-59 §6
argued. It buys no scored row.

## 4. THE SOLVE — THREE SHARDS, ONE YEAR EACH (rule 36 (a))

Each shard is pinned to this commit's SHA. It recovers its control leg at zero LP, curates the
classifier, and replays:

```
python3 scripts/data/curate_hydro_plant_modes.py --iso SOCO     # must print 45 plants, 17 run-of-river-class
python3 scripts/replay_keeper.py results/calibration/soco_h4_ror_<Y> --years <Y> \
  --out-dir results/calibration/soco60_arm_<Y> \
  --set hydro_backfill_year=2024 --set hydro_eia930_monthly=true \
  --note "SOCO-60 ARM <Y>: merged hydro recipe = keeper soco-h4-hydro-ror (hydro_ror_split) + SOCO-59 hydro_eia930_monthly with EIA930_PS_SPLIT_COMPLETE_FROM[SOCO]=2025; year-isolated (rule 36)"
```

**Hard stops:**
- the pinned SHA;
- the classifier count;
- post-solve, `scripts/probes/soco60b_compose_span.py --expect-arm true --check-only` on the leg, which
  checks the meta keys, `solve_surface.rows == 184`, the seven resolved postures and the classifier
  snapshot `hydro_plant_modes-ea00e49bf5be`.

Solves run in the foreground. Each shard pushes its full bundle via a `.gitignore` negation and a plain
`git add` (rule 34 (a)). The parent composes with `soco60b_compose_span.py`, then runs
`--rebuild-benchmark` on the composite.

## 5. THEN — 2024 CC_REGULAR PHASE 0 (addendum B, written before any CC arm is solved)

This covers the four leads in the handoff: CC capacity basis, net interchange, ST_GAS vs CC fuel
separation, and the over-dispatched CC tail. **Distance on the merged control: +9.80 TWh against a
±7.44 band means −2.36 TWh is needed; the share leg needs roughly −0.6 pp.** That is smaller than the
handoff's −2.98, because the RoR split already moved it −0.62. 2023 ST_GAS is the thinnest row
(margin ≈ 0.2 pp) and constrains any lever that takes energy from steam.

---

## ADDENDUM B — CC_REGULAR phase 0 found two BENCHMARK defects (written before any arm-B solve)

The four named leads were not needed. Measuring the object's **benchmark** before its dispatch showed
that the 2024 CC_REGULAR "actual" of 104.91 TWh sits **5.4 TWh below** the EIA-923 net generation of
the 18 SOCO CC_REGULAR plants the model carries (110.31). The model's plant-level CC total is 114.71.
Two defects produce that gap. Each is measured on SOCO's own data, and each is a rule 14 misalignment.
Probe: `scripts/probes/_soco60b_phase0.py` (`ba`, `bench`). Every bench number below is a fresh-process
rebuild on the control leg's own recipe. The control side reproduces the committed part exactly
(CC_REGULAR 104.909).

**B1 — PLANT BOUNDARY.** The benchmark's membership (`_iso_plant_ids` → eGRID 2023 `BACODE`) admits
the former Gulf Power plants: Lansing Smith 643, Gulf Clean Energy Center 641, Pea Ridge 7715,
Perdido 57502, and three Gulf solar plants. EIA-860 codes them SOCO through vintage 2023 and **FPL
from vintage 2024**. The model's fleet census (current 860, `BA == SOCO`) carries none of them. **EIA-930
SOCO has excluded them in every year:**

| year | 930 SOCO gas+coal | 930 / 923 fossil **without** them | 930 / 923 fossil **with** them | their fossil TWh |
|---|---|---|---|---|
| 2019 | 181.21 | 0.997 | 0.962 | 6.65 |
| 2020 | 165.11 | 1.008 | 0.971 | 6.13 |
| 2021 | 171.33 | 1.004 | 0.968 | 6.35 |
| 2022 | 177.51 | 1.006 | 0.973 | 6.06 |
| 2023 | 167.84 | 1.002 | 0.965 | 6.53 |
| 2024 | 166.61 | 0.981 | 0.943 | 6.85 |

**Repair:** `constants.ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE = {"SOCO": True}`. At the one
membership seam, plants the current EIA-860 recodes to another BA are dropped (7 plants). Plants that
are merely absent from the current file stay (3 plants, 0.03 TWh). It is per-ISO with zero free
parameters. It is solve-affecting only through the must-run injection: biomass −0.0174 / −0.0145 TWh
in 2023 / 2024 (Perdido landfill gas); OTHER is unchanged. Declared at `False`, so SOCO's cache key
moves (185 surface rows, 1 moved). No other ISO's surface moves.

**B2 — GAS-FOLD DEFLATION.** `gas_foldin_deflation` subtracts `OTHER + biomass − 930 Other` from the
EIA-930 gas reconcile target. For SOCO 2024 that is 6.35 TWh, an assertion that SOCO's 930 gas cell
carries 6.35 TWh of biomass. **Refuted.** SOCO 930 gas vs the 923 gas classes of in-BA plants, CHP
included, 2019–2024: 125.06/127.88, 125.88/126.08, 120.99/121.89, 130.64/130.96, 129.59/130.23,
126.08/129.54 TWh. 930 is at or below 923 in every year, which leaves no room for a fold. SOCO's
biomass is 82 % / 84 % CHP-flagged and 60 % black liquor: pulp-mill generation the BA does not meter.
**Repair:** `benchmark_semantics.EIA930_GAS_FOLD_REFUTED = {"SOCO"}` returns 0. This is benchmark-only;
no solve reads it.

**Why the two together:** B1 alone moves 2024 CC_REGULAR only to +9.28 TWh, because B2 still fires
the reconcile at ×0.956. B2 alone gets to +5.62 TWh, but the share leg reads +3.0 pp, because the Gulf
plants still inflate the actual. Each is a separate defect with separate evidence. Neither is chosen
because of what the other does.

### Predictions for arm B (= arm M + B1 + B2), scored on the rebuilt bench

Bench numbers are measured on the control's dispatch; arm B's dispatch differs by ≤0.02 TWh per class.

| # | row | control, current bench | **arm B, predicted** | falsifier |
|---|---|---|---|---|
| Q1 | 2024 CC_REGULAR | +9.80 TWh / +3.6 pp FAIL | **+4.41 ± 0.05 TWh / +2.7 ± 0.1 pp PASS** (share margin ~0.3 pp) | share ≥ +3.0 pp |
| Q2 | 2023 CC_REGULAR | +5.23 / +2.0 pp | +2.04 / +1.2 pp | — |
| Q3 | 2023 ST_GAS | −6.65 / −2.8 pp | −5.50 / −2.3 pp | — |
| Q4 | 2024 ST_GAS | −6.17 / −2.5 pp | −4.91 / −1.9 pp | — |
| Q5 | 2024 COAL_PRB | −2.37 / −1.0 pp | **−4.58 / −1.6 pp (worse, still PASS)** | outside ±7.66 |
| Q6 | 2023/2024 COAL_BIT | −1.24 / −0.80 | −2.12 / −1.89 (worse) | — |
| Q7 | 2023/2024 CT_PEAKER | +5.05 / +1.32 | +5.22 / +1.73 (worse) | — |
| Q8 | arm-B vs arm-M dispatch | — | biomass −0.017 / −0.015 / (0 to −0.015) TWh; every other class \|Δ\| ≤ 0.02 TWh | larger |
| Q9 | C1 | 13/14 | **14/14** | — |

**Scrutiny (check F).** If the only argument for B1 or B2 were that 2024 CC_REGULAR passes, neither
would be taken. Three rows get **worse** under the repaired benchmark: COAL_PRB, COAL_BIT and 2024
CT_PEAKER. The coal rows get worse because the uniform reconcile was hiding a model coal under-dispatch,
since it also scaled coal down 8 %. They are reported at full magnitude. The repairs rest on
EIA-930's own SOCO accounting across six years, not on the scored row.

**Solve:** three shards, one year each, pinned to this addendum's commit SHA. Each replays its
`soco60_arm_<Y>` leg with no `--set` (the change arrives through HEAD) into `soco60_armB_<Y>`.
