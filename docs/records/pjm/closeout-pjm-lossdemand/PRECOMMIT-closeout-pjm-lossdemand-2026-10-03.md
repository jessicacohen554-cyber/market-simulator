# PRECOMMIT — closeout-PJM-lossdemand: net the loss surface's own dissipation out of the P1 demand (PROBE, 7 years)

Lane closeout-PJM-lossdemand, chartered by the backcast close-out desk (session_01ERkBTm23ZAP4CTZnJVD9Ss) on
**owner ruling R-59 (2026-10-03, verbatim): "Fix PJM first, then others (Recommended)"**. Evidence:
`docs/records/pjm/closeout-pjm-balance/FINDING-closeout-pjm-balance-2026-10-03.md` (option A of §6).
Bars below are fixed **before** any leg is solved. This run is a **probe**; it is not promoted in this lane.

## 1. Mechanism (rule 13 / 14 / 21)

- **Defect.** The keeper arms `pjm_zonal_loss_surface`, so each internal one-way link delivers `(1 − ε)·F`. The
  measured demand (EIA-930 BA demand, `D = NG − TI`) already contains every T&D loss. The LP therefore
  generates `Σ ε·F` a second time: +2.189 / 2.160 / 2.554 / 3.141 / 2.529 / 3.394 / 3.972 TWh in 2019–25, equal to
  the keeper's generation residual to 0.002 TWh.
- **Repair.** New field `zonal_loss_demand_reconciliation` (default **off**). At the P0→P1 seam
  (`pipeline/solve.py::run_energy_solve`) each zone's P1 demand becomes `D_z,t − Σ_{l received by z} ε_l,t·F⁰_l,t`,
  with `F⁰` the P0 flows (`model/loss_demand.py`). The `(1 − ε)` coefficient is untouched, so the MLC price
  separation is unchanged (rule 4). One pass (rule 10). An armed pass always takes the cold P1 route (a changed RHS
  cannot ride the cost-only warm re-solve).
- **Admissibility.** Rule 14 reconciled form of measured demand on a boundary the representation does not share
  (loss-inclusive measurement vs loss-dissipating network). Rule 13: the solve's own flows × the measured surface,
  forward-reproducible. Rule 21: no free scalar; the DOF ledger is unchanged. Rule 19: replaces nothing and
  stacks on nothing (no other mechanism touches the demand basis of the loss surface).
- **Config delta vs keeper.** Exactly one: `--set zonal_loss_demand_reconciliation=true` on the keeper recipe
  (`results/calibration/closeout_pjm_nuc_full_span`). Not armed in `iso_configs` defaults.

## 2. G-DRIFT (rule 29b): keeper legs → this SHA

Keeper legs: 2019/20/22–25 at `8c3ea46192074cfd422fff6532acc035d37297bb`, 2021 at
`e2e296a43a86f70da5babc7f386d1bbc71e0874d`. Changed hunks on the backcast path to HEAD (`dd28b645` + this lane):

| hunk | class | reason |
|---|---|---|
| `constants.py` `NUCLEAR_MONTHLY_CF_BY_YEAR` MISO / SOCO rows, `COAL_PLANT_GRAIN_ISOS` / `COAL_TAKE_FLOOR_ISOS` + SOCO, `NWPP_MEMBER_LOCAL_TZ` | INERT | other-ISO rows; PJM rows untouched |
| `solve_surface.py` epochs 2026-10-03c/d | INERT | `isos=("SOCO",)` / `("MISO",)` |
| `run_calibration.py` coal take-floor guard, NWPP served-schedule attribution | INERT | SOCO / NWPP-gated |
| `eia930/envelopes.py`, `eia930/demand.py`, `interchange/import_nodes.py`, `interchange/spec.py` | INERT | NWPP-gated, default-off fields |
| `caiso_as_requirements.py` | INERT | CAISO-only |
| `egrid.py` `engine="calamine"` | INERT | benchmark read, identical frame (as adjudicated in the closeout-PJM-nuc PRECOMMIT addendum A) |
| `pipeline/persist.py`, `results/cache.py`, `lib/solve_container.py` | INERT | provenance / infra |
| `scenarios.py` new fields | INERT | all default off, none armed by the PJM recipe |
| **this lane: `pipeline/solve.py` hook, `model/loss_demand.py`, field** | **LIVE (the arm)** | off ⇒ `p1_demand is demand`, byte-identical; on ⇒ the declared delta |

**Measured:** `solve_surface.surface_rows("PJM")` fingerprint at HEAD = `d8230f36c0059245` (233 rows), equal to every
keeper leg. No control solve is earned (rule 29b); the keeper's committed bundle is the control.

## 3. Predictions (first order, from FINDING §4; a re-solve can reorder the gas–coal margin)

| TWh | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| P0 dissipation netted (≈ keeper Σε·F) | 2.19 | 2.16 | 2.55 | 3.14 | 2.53 | 3.39 | 3.97 |
| total fossil Δ (predicted band) | −2.2 | −2.2 | −2.6 | −3.1 | −2.5 | −3.4 | −4.0 |
| CC_REGULAR Δ (peel…split) | −1.13…−0.63 | −0.67…−0.59 | −1.44…−0.90 | −1.91…−0.93 | −1.00…−0.59 | −0.93…−0.72 | −2.49…−1.07 |
| C1 CC_REGULAR keeper → predicted | +3.62 → +2.5…+3.0 | +6.02 → +5.4 | +0.77 → −0.7…−0.1 | **+8.96 → +7.05…+8.03** | +3.40 → +2.4…+2.8 | −4.95 → −5.9…−5.7 | −12.64 (SKIPPED, prelim) → −15.1…−13.7 |

Fossil band widened ±50 % around the point for the reorder caveat: total fossil Δ ∈ [−1.5 × L, −0.5 × L] per year.

**Identity residual after the fix.** `R = Σgen + import-node net − storage net charge − Σ D_measured` from the
committed sidecars, as the closeout-PJM-balance probe computes it. By construction `R = Σ ε·(F¹ − F⁰)`, the P0→P1
flow change (proved exactly on the trivial case, `tests/unit/model/test_loss_demand.py`). Netting the receiving
zone's demand also shrinks the flow that dissipates, so in hours where the receiver imports at the margin the
residual is second order, `≈ −ε̄·Σε·F⁰` (−0.05 to −0.11 TWh/yr at ε̄ 2.2–2.8 %); where the link is congested it is
zero. The leg flows carry no P0 pass, so this is bounded, not measured, zero-LP. **Declared risk:** the kill K1 at
0.05 TWh/yr can trip on a fully uncongested year (2024–25 most exposed). It is the desk's bar and stays as set.

## 4. Kills and passes (fixed ex ante)

| id | test | reading |
|---|---|---|
| **K1** | `|R|` ≤ 0.05 TWh in every year (sidecars; slack = dump = 0) | any year above → KILL |
| **K2** | no C1 PASS→FAIL other than the **declared** CC_REGULAR 2024 widening (−4.95 → may cross −8.0); 2025 CC is SKIPPED (preliminary vintage) | any other PASS→FAIL → KILL |
| **K3** | C3a: no year's `|mean-LMP error|` worse by > 1.5 pp vs keeper, and no C3a PASS→FAIL | breach → KILL |
| **K4** | C3b: no year's NRMSE worse by > 0.020 vs keeper, and no C3b PASS→FAIL | breach → KILL |
| P1 | total fossil Δ in the band of §3 in every year | out of band → report, not a kill (re-solve reorder) |
| P2 | C1 CC_REGULAR 2022 FAIL→PASS (`< +8.0`) | expected; knife-edge (+7.05…+8.03) — not a kill if it misses |
| P3 | zonal price separation preserved: P1 dual ratios across lossy links unchanged within marginal-tie noise | reported |
| P4 | C8 / D-2 forced-energy shares and C6 governance unchanged in verdict | reported; a C6/C8 FAIL is a KILL |

## 5. Solve plan

- 7 shards, one per year (rules 32/34/36), from `scripts/shard_prompt.py --iso PJM --all-years --bundle
  results/calibration/closeout_pjm_nuc_full_span --set zonal_loss_demand_reconciliation=true`, pinned to one full
  40-char SHA; env `env_016R8xUY4maDbppZ6TEns5V8`; ≤ 6 alive.
- Compose (`_miso260_compose_span.py` pattern), score (`calibration_verdict.py`, `legitimacy_diagnostics.py`), the
  identity residual per year (`scripts/probes/_closeoutpjm_balance_trace.py` on the probe bundle), and register as a
  **probe** (`scripts/dashboard_add_run.py`). No promotion; the desk raises the owner card.
