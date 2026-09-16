# PRECOMMIT — nyiso-238: solve `hydro_budget_period_by_instrument` across ALL FOUR registered years

**Session** nyiso-238 (ORCHESTRATOR — rule 32 `[R-SHARD]` (a); the parent runs ZERO LP).
**Date** 2026-09-16. **Keeper** `2026-09-14-nyiso-235-gas-repair`
(`results/calibration/nyiso235_gasrepair_span`), years {2022, 2023, 2024, 2025}.
**Pushed BEFORE the first LP.**

## 0. WHAT THIS IS, IN ONE LINE

`hydro_budget_period_by_instrument` was built by nyiso-220 on **2026-09-08**, screened and spanned
by nyiso-236 on 2026-09-16, and **its bundles no longer exist** — every leg SHA recorded in
`RESULT-nyiso236` §A6 (`4f82866b…`, `5041ca0d…`, `eee2a08b…`, `e77c597d…`) is **UNREACHABLE** and
only four branches remain on the remote. This session re-solves the arm across all four registered
years into ONE bundle the owner can actually promote.

**This is NOT a new screen.** The arm is already screened (nyiso-236, 2025, cleared) and already
spanned. Rule 29 `[R-SCREEN]` clause (0)'s pre-solve gate has been spent; what was lost is the
artifact, not the adjudication. Rule 16 `[R-ALLYEARS]` + rule 32(b): **one shard, one
`--years 2022 2023 2024 2025` invocation, one bundle.** Rule 34 `[R-SHARD-PROMOTABLE]` (a): the
shard **pushes** the bundle, `dispatch/<year>_P1.parquet` and the bundle-root `system.parquet`
included, so a promotion costs zero re-solves.

## 1. THE ARM

```
python3 scripts/replay_keeper.py results/calibration/nyiso235_gasrepair_span \
  --years 2022 2023 2024 2025 \
  --out-dir results/calibration/nyiso238_hydroperiod_span \
  --set hydro_budget_period_by_instrument=true
```

**ONE field moves.** Per-year fields (`gas_price_override`, `weather_year`,
`gas_offer_margin_anchor_by_zone`) and `mustrun_commitment_feasibility_clip` materialising at its
dataclass default are the replay driver's own, exactly as nyiso-236 recorded. Config signature the
shard must verify before it pushes: `hydro_budget_period_by_instrument = true` and
`solve_surface.fingerprint = bd2b4657f9b5df7e`.

The registry the arm reads (`HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT["NYISO"]`) is **instrument-derived
and NEVER swept** (rule 23 `[R-FROZEN-DERIVE]`): Niagara 2693 → 24 h (1950 Niagara Treaty + INBC
1993 Directive state no conservation period; 0.244 h measured forebay pondage ⇒ use-it-or-lose-it,
and 24 h is the unique granularity that removes cross-day banking while leaving the treaty's own
Art. IV diurnal swing free); St Lawrence 2694 → 168 h (IJC 2016-12-08 Supplementary Order, weekly
regulation plan + the peaking-and-ponding directive, stated in words). **Zero free parameters.**

## 2. G-DRIFT (rule 29 (b) form 4) — DONE, AT THIS HEAD, BEFORE THE SOLVE

* `moved_rows("NYISO") == {}` ✓
* `surface_stamp("NYISO", keeper_cfg)["fingerprint"] == bd2b4657f9b5df7e` ✓
* The keeper's recorded `git_sha 2ebc58df` is **UNREACHABLE** (deleted shard branch — rule 33
  `[R-SHARD-ARCHIVE]` (d) encountered live), so the hunk audit is chained from `a3df8337`, the head
  nyiso-237 certified. **Every changed solve-path hunk since is INERT:**
  * 15 of 17 files are the NWPP-36 hydraulic-cascade wiring, gated on `hydro_cascade_coupling`
    (dataclass default `False`, absent from every ISO's `default_scenario_overrides` AND from the
    keeper's `run_config.json`) ⇒ `resolve_hydro_cascade` returns `UNSET` at `kwargs.py:146`
    ⇒ `n_cascade = 0` ⇒ every LP block is zero-width and the layout is byte-identical.
  * `data/eia930/actuals.py` is NWPP-39's fuel-spike zero-baseline guard, which can only RELEASE a
    series. Measured on this session's own instrument over NYIS 2022–2025: exactly one series is
    flagged by the unguarded screen (2024 `NG: OTH`), its p99.9/p99.0 ratio is **1.051 < 2.5**, so
    the guard does not release it — **byte-identical**.
  * `data/eia930/frames.py` adds `_screen_pool_member_frame`, reached only for a `_POOL_HOURLY_MEMBERS`
    code; **NYIS is not a pool**. `data/eia930/envelopes.py` is **comments and docstrings only**.

**Form 4 valid. The keeper's committed bundle is the control. NO control solve is spent.**

## 3. THE GATES — nyiso-236's G1–G5, re-run EXACTLY AS WRITTEN

| gate | threshold, as written | kill? |
|---|---|---|
| **G1 FEASIBILITY** | LP solves to optimality; slack / dump as the keeper | yes |
| **G2 IDENTITY** | annual hydro within **0.1 %**, every month within **0.5 %** | **YES** |
| **G3 DIRECTION & MAGNITUDE** | cross-day footprint FALLS from the keeper's into **1.0–6.0 %**, never to 0.00 | yes |
| **G4-as-written** | every non-hydro class within **2 %** | no (reported) |
| **G4-material** | 2 % on classes ≥ 2 % of ISO load, plus conservation | no (reported) |
| **G5 NO NON-TARGET FLIP** | no non-hydro load-bearing criterion flips PASS → FAIL | yes |

**BOTH G4 forms are reported, as nyiso-236 required.** G4-as-written is known miscalibrated
(`RESULT-nyiso236` §A4: it fails in opposite directions in 2023 and 2025 at 0.01–0.02 % of ISO
load); its repair is another session's.

**PRE-REGISTERED EXPECTATION, written before the solve so it cannot be fitted after.** nyiso-236
measured G2 **FAIL in 2022 (−0.2155 %, −55.2 GWh) and 2023 (−0.0957 %, −25.5 GWh)** and **PASS at
0.000 % in 2024 and 2025**, with G3 passing all four years (footprints 6.36→4.00, 5.31→3.18,
4.71→2.71, 7.46→4.16) and G5 passing all four. **This solve is expected to reproduce that.** A
material departure from it is a finding about determinism, not about the arm.

Nothing here is gated on C3a. C3a is reported at full magnitude (keeper 2022 −9.67 %) and
**neither promotes nor kills** (rule 1 `[R-STRUCT]`).

## 4. WHY G2's TWO FAILING YEARS ARE NOT THE ARM'S DEFECT — and the phase-0 result that settles it

nyiso-236 §A2 measured the cause: the LP **declines to run Niagara when `Upstate_West` goes
negative**, and a 24 h use-it-or-lose-it budget cannot move that water to a positive-price day.
nyiso-237 measured the price: the keeper prices `Upstate_West` ≤ $0 in **498 h of 2022** against a
measured **21** (WEST alone) / **127** (the five-zone A–E mean that IS the model zone).

**This session's phase 0 (zero LP, `scripts/probes/nyiso238_central_east_seam_phase0.py`) tested all
four handed candidates for that price defect and KILLED EVERY ONE:**

* **(a) flat monthly-mean TTC applied hourly — KILLED BY ARITHMETIC.** Against the committed MIS
  P-32 hourly `positive_limit_mw`, the hourly posting is **above** the monthly mean in only
  **32.3 %** of the 498 hours and the mean headroom is **−58.5 MW** (2023: **−74.9 MW**). The repair
  moves the wrong way, and the reason is measured: the posted limit is **211 MW LOWER** in the
  lowest `Upstate_West` load quintile than the highest (Q1→Q5 −101 · −60 · +2 · +49 · +110 MW) —
  planned-outage derates co-occur with exactly the low-load hours the model fabricates.
  *(Level reconciliation, so the product swap is not the issue: the armed DAM monthly means and the
  P-32 hourly means agree to ~1 % in 11 of 12 months of 2022; annual 1,821 vs 1,825 MW.)*
* **(b) no West export outlet — KILLED.** The real West-landing ties ran **net export in 2.2 %** of
  the 498 hours. Reality's response was to cut imports **−641 MW**, not to export.
* **(c) firm imports into a saturated zone — KILLED.** The model holds **433 MW** into the West in
  those hours; reality imported **962 MW** in the same hours. The model **under**-imports by 529 MW,
  so the floor is not the cause and removing it moves away from the measurement.
* **(d) nested-cutset topology — ALREADY ADJUDICATED CLOSED, and NOT re-opened here** (rule 28
  `[R-MECH-MATRIX]` (a) DO-NOT-REDO): nyiso-225, 2026-09-10, **owner accepted the kill**, three
  independent legs — `TOTAL EAST` is ≥95 % loaded in **0.01 / 0.00 / 0.00 / 0.00 %** of hours so
  there is no nested pair to separate; the non-CE leg bypasses zone F into zone G and **both legs
  leave the same upstate zone**, so no split of A–E separates them and the F|G limit does not exist
  in P-32, in 36 months of MIS ATC/TTC, or in any of the four Gold Books; the identifiable A–E split
  binds in 0.00–0.02 % of hours.
* **NEW, and it removes the last non-seam explanation:** the model's `Upstate_West` **demand is
  exact** — it reproduces the measured A–E zonal load to **−0.3 MW** on 2022 (−0.5 on 2023) and
  −14.5 MW inside the fabricated hours. On the supply side the model runs nuclear **+219 MW** above
  the EIA-930 meter in those hours, which is real but ~20 % of the **966 MW** by which the real
  TOTAL EAST flow exceeded the model's cap in **97.8 %** of them.

**So the arm is right where the model is right** (G2 exact in 2024 and 2025) **and is killed in
2022–23 by a price defect with no identifiable repair.** That is the finding; the solve makes it
promotable.

## 5. WHAT THE SHARD MUST DO

Pinned SHA, its own out-dir and branch, the bundle pushed via a `.gitignore` NEGATION plus a **plain
`git add`** (never `-f`, never `-A`). It edits nothing under `src/` or `scripts/`, touches nothing
under `frontend/data/backcast/**`, runs no `dashboard_add_run` / `build_manifest` / `build_status` /
`prune_iso_runs`, opens no PR, and deletes no result (rule 31 `[R-RETAIN]`). **Budget: ~60 min**
(four NYISO years at ~15 min, sequential inside the one invocation per rule 12 `[R-PARALLEL]`) —
stated here because rule 32(b) requires a whole span to be one shard with its budget named, not a
fan-out whose legs cannot be reassembled.

**A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a
FAILURE.**

## 6. GOVERNANCE

* Rule 1 `[R-STRUCT]`: `authorized_price_tuning` = **NONE**. Zero offer-curve multipliers move.
* Rule 21 `[R-DOF]`: **zero free parameters** — two published instrument durations.
* Rule 31 `[R-RETAIN]`: the bundle is pushed, not gitignored-and-stranded; the promotion question
  goes to the owner with both arms' numbers.
* Rule 33 `[R-SHARD-ARCHIVE]`: the shard is archived once the parent has fetched, checked out and
  verified its bundle, and its recovery is recorded by **full SHA**.

---

## ADDENDUM 1 (2026-09-16, BEFORE any bundle landed) — **PER-YEAR FAN-OUT, ON OWNER INSTRUCTION**

**Owner instruction, verbatim: "What the fuck one shard PER YEAR no screen".** §5 above launched the
span as ONE shard per rule 32(b) `[R-SHARD]`. That shard (`session_01Cyb9mZQoSzj3JsqX6JKmqV`) was
**interrupted and archived** ~5 min in, and the span is now **four parallel per-year shards**:

| year | out-dir | branch | session |
|---|---|---|---|
| 2022 | `results/calibration/nyiso238_hydro_2022` | `claude/nyiso238-hydro-2022` | `session_01AsujaPD2wsZLYsXFSeGFxW` |
| 2023 | `results/calibration/nyiso238_hydro_2023` | `claude/nyiso238-hydro-2023` | `session_01MpPddw87k3hs9UE3ehmHN4` |
| 2024 | `results/calibration/nyiso238_hydro_2024` | `claude/nyiso238-hydro-2024` | `session_01PkVyNRV6MbxLjWxNEexApG` |
| 2025 | `results/calibration/nyiso238_hydro_2025` | `claude/nyiso238-hydro-2025` | `session_01SwC4WmLGGKmp4qgEMJPEMF` |

All four at the same pinned SHA `69c6d4a7e1b7c8e458373bc5ce9db51a5a7a6a39`, same one-field arm, same
three hard stops, each pushing its OWN bundle under rule 34 `[R-SHARD-PROMOTABLE]` (a). Wall time
~15 min instead of ~60.

**WHICH READING OF RULE 32(b) THIS FOLLOWS, stated as the handoff requires.** Rule 32(b) bans slim
per-year fan-out, and its stated reason is mechanical: a shard can only commit the *slim* file set,
so the legs cannot be composed and the span has to be re-solved anyway. **That reason does not apply
here, and the difference is the whole point:** each shard pushes its FULL bundle — `dispatch/<yr>_P1.parquet`
and the bundle-root `system.parquet` included — via the rule 34(a) `.gitignore`-negation route, which
is exactly the artifact set `render_calibration_html.build_payload` and the per-plant D-1/D-2/D-4
diagnostics need. The legs therefore compose, which is the precondition rule 32(b)'s ban assumes is
missing. The composition recipe is the one this lane already has on record (`RESULT-nyiso236` §4,
owner-authorized for NYISO): every root parquet carries a `year` column, `meta.json` years/gas_prices
merge, and `metrics.json` + `legitimacy_diagnostics.json` are regenerated **in the parent, zero LP**.

**Nothing else in this PRECOMMIT changes** — not the arm, not the pinned SHA, not the G-DRIFT
audit, and above all **not the gates in §3, which were written and pushed before any solve.** The
"no screen" half of the instruction is already the posture of §0: this is not a screen, the arm was
screened by nyiso-236 and its adjudication stands; what is being re-created is the lost artifact.

**Rule 32(d) still binds the parent**: the per-year bundle dirs are kept OUT of `main`; the composite
is what gets registered.
