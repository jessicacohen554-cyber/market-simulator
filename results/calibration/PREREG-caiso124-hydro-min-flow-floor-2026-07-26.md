# PRE-REGISTRATION — caiso-124 hydro minimum-flow floor (single delta)

**Written and committed BEFORE arm B was solved.** Arm A (same-HEAD control) was
already running when this was written; no B-arm result existed. Gates below are
final — a gate this document does not contain cannot be quoted as a pass.

---

## §1 — the delta

ONE registered switch: `ScenarioConfig.hydro_min_flow_floor` (default off,
`--set hydro_min_flow_floor=true` through `scripts/replay_keeper.py`, the only
sanctioned keeper-recipe reconstruction). Everything else is the
`2026-07-23-caiso-netrev-margin-keeper` recipe replayed at this session's HEAD.

- **Arm A** `results/calibration/caiso124_control_A` — keeper recipe, no delta,
  same HEAD, same container, same regenerated `capacity-deliverability` clean
  partition. NOT registered (FINDING-caiso92b protocol; never A/B against the
  keeper's committed bytes — caiso-123 is the cautionary tale).
- **Arm B** `results/calibration/caiso124_minflow_B` — identical + the floor.
- Both `--year 2023 2024 2025` in one invocation (rule 16), years sequential
  within the run, arms sequential to each other (rule 12; CAISO is
  single-solve-only on this 15 GB box).

**Mechanism** (rule 17 declaration, mirrored in the `ScenarioConfig` field, the
`MECH_HYDRO_MIN_FLOW` registry entry and the `D4_WINDOWS` row):

| | |
|---|---|
| driver | run-of-river inflow that physically cannot be stored + environmental / FERC-licence minimum releases. The hydro budget family caps monthly ENERGY with no lower bound, so the purely-economic LP may park the fleet at 0 MW. |
| window | ALL 24 h — inflow and licence releases are around-the-clock; the measured series never approaches zero in any hour-of-day bucket. Binds where the economic solution sinks below the sustained level (solar belly, overnight shoulder). |
| forward story | level re-derives from the same EIA-930 `NG: WAT` history the committed p95 ceiling uses — own year in a backcast, pooled `HYDRO_CLIMATOLOGY_YEARS` per-month percentile otherwise — and scales with the water year through the budget it is clipped against. |
| level | per-month exceedance percentile `HYDRO_MIN_FLOW_PERCENTILE = 100 − HYDRO_ENVELOPE_PERCENTILE = 5` (the hydrological Q95 low-flow index), i.e. the **exact mirror of the ceiling's**, allocated per plant pro-rata by its own share of that month's energy budget. |
| DOF added | **zero.** No new free parameter: the percentile is the ceiling's, mirrored; the allocation weight is the LP's own measured budget. |

Derived level (MW by month, measured, `basis` = each solve year's own EIA-930):

| year | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2023 | 615 | 664 | 1403 | 2102 | 1731 | 1598 | 1958 | 1722 | 1620 | 852 | 610 | 565 |
| 2024 | 842 | 869 | 1620 | 928 | 1403 | 1179 | 1639 | 1555 | 843 | 766 | 736 | 685 |
| 2025 | 969 | 1406 | 1429 | 849 | 1033 | 634 | 715 | 996 | 876 | 30 | 434 | 1099 |

Floor energy = 46.3 / 42.2 / 35.7 % of the monthly budget (2023/24/25), so
54–64 % of each month stays economically shaped. Worst plant-month floor/budget
0.595 / 0.531 / 0.561 — the feasibility clip does **not** bind anywhere, and no
plant is asked for more than 0.80 of its nameplate.

## §2 — baseline (arm A expectation, measured off the keeper's committed hourlies)

The keeper's own `hourly/class_hourly_<year>.parquet` vs measured EIA-930
`NG: WAT` on the model clock:

| quantity | 2023 | 2024 | 2025 |
|---|---|---|---|
| model hours < 100 MW | 926 | 1342 | 1169 |
| model hours < 10 MW | 270 | 693 | 601 |
| model hourly p5 (MW) | 25 | 0 | 0 |
| measured hourly p5 (MW) | 954 | 876 | 738 |
| belly (hod 9–15) hydro, model − measured (MW) | **−594** | **−612** | **−557** |
| evening (hod 17–21) hydro, model − measured (MW) | +110 | −143 | −19 |
| diurnal profile r (model vs measured, 24 hod means) | 0.958 | 0.972 | 0.982 |

Arm A is expected to reproduce these within vertex-wander noise; a material
divergence is itself a finding (the caiso-123 §5 residual) and is reported, not
absorbed.

## §3 — PRIMARY gates (the floor's OWN gates — rule 1: never judged on C3a recovery)

All three years must clear each.

- **P1 parks-at-zero eliminated.** Hours with model hydro < 10 MW → **0**;
  hours < 100 MW → **< 150/yr** (from 926/1342/1169).
- **P2 belly gap closes.** |belly (hod 9–15) hydro gap| ≤ **200 MW** in every
  year, and strictly smaller than arm A's in every year.
- **P3 shape does not degrade.** Diurnal-profile `r` ≥ arm A's in every year,
  and the 24-hour profile MAE strictly falls in every year.
- **P4 mechanism accounting is clean.** `legitimacy_diagnostics.json` carries a
  D-2 row for `hydro_min_flow` and a D-4 row for it with **off-window share
  0.0000** (window is all-hours, so any non-zero is a wiring bug, not a
  verdict). Forced share is *reported*: hydro carries no CAMPD `plant_group`, so
  it sits in the unclassified `''` bucket the D-2 summary never gates, and
  `MECH_HYDRO_MIN_FLOW` is in `NON_THERMAL_MECHS` — it can never consume a
  merchant thermal class's C8 budget. Expected ≈ 30–46 % of hydro energy.

## §4 — SECONDARY, directional only (the caiso-120/121 regime-conditional set)

Recorded and reported; **not** pass/fail for this delta (the selected belly
family is export-path/corridor, not hydro — caiso-121 §4).

- **S1 surplus regime** (measured RT ≤ $20): net-export hours appear (arm A: 0;
  measured 40–57 %); λ − min-hub → 0; CA λ − WECC_DSW λ → 0.
- **S2 firm regime**: import → measured 0.9–2.4 GW.
- **S3 C3c h>$200 direction**: the finding's mechanism story says removing
  over-saved evening water should RAISE evening prices, i.e. move the model's
  h>$200 count *toward* measured. Direction is recorded either way.
- **S4** C3a / C3b / C3c / C4 / C5a rubric verdicts and the λ level, both arms.
  C3a-2025 is expected to FAIL in **both** arms (caiso-123 §3: any honest
  same-HEAD control reads ≈ +11.1 %); that failure is the attributed extract
  basis, not this delta, and the floor is not credited or debited for it.

## §5 — KILL criteria (any one ⇒ delta rejected, whatever the headline)

- **K1 evening overshoot.** Model evening (hod 17–21) hydro exceeds measured by
  > 300 MW in any year. The floor must not push MORE water into the evening.
- **K2 evening starvation.** Model evening hydro falls below measured by
  > 600 MW in any year (the over-correction mirror: the floor takes so much
  water out of the peak that the evening is starved). A crude energy-neutral
  redistribution of the keeper's own hydro predicts −265/−460/−255 MW under a
  *proportional* clawback; the LP should claw back from the cheap overnight
  hours instead (model overnight runs +250…+350 MW above measured), so a
  reading past −600 MW means the LP is paying for the floor out of the peak.
- **K3 shape degradation.** Diurnal `r` falls below arm A's in any year.
- **K4 derivation/budget disagreement.** Any LP infeasibility, or any
  plant-month where the feasibility clip binds (the level would then exceed the
  month's average power — a data problem, not a result).
- **K5 off-window binding.** D-4 off-window share > 0 for `hydro_min_flow`.
- **K6 a new C8 breach on a thermal merchant class** traceable to the floor
  (the floor forces no thermal unit, so a breach would mean the mechanism
  leaked outside the hydro fleet).

## §6 — what a PASS does and does not authorize

A clean pass registers arm B on the backcast dashboard (rule 15, top-15
retention — one CAISO run pruned first) and scores the mechanism
leave-one-year-out within 2023–2025 (rule 22). **Promotion to the keeper is an
OWNER call regardless of score** — and it sits behind the two open sequencing
decisions this session does not touch: the extract over-count freeze
(neiso-66, ACTIVE) and the caiso-123 §6 re-tune-vs-wait question. Arm A is not
registered. Nothing here promotes anything.

Rule 21 applies to the level from this point: `HYDRO_MIN_FLOW_PERCENTILE` and
the monthly derivation re-derive only when the EIA-930 source extends, never
because a residual moved.
