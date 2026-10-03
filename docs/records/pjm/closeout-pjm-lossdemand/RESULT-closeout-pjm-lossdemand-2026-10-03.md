# RESULT — closeout-PJM-lossdemand: P1 demand netted by the loss surface's P0 dissipation (PROBE, 7 years) — KILLED (K1, K2)

Probe `2026-10-03-closeout-pjm-lossdemand-probe`, bundle `results/calibration/closeout_pjm_lossdemand_span`.
Pre-registered in `PRECOMMIT-closeout-pjm-lossdemand-2026-10-03.md` at `9817047a`. Owner ruling R-59 ("Fix PJM first,
then others"). **Not promotable.** The keeper `2026-10-03-closeout-pjm-nuc-keeper` is unchanged.

## 1. Provenance

| item | value |
|---|---|
| code + PRECOMMIT | `9817047af5d667a5326911c2538943cffa0ee2be` (PR #7168, merged at `cee1ae46`) |
| config delta | `--set zonal_loss_demand_reconciliation=true` on `closeout_pjm_nuc_full_span`; nothing else (composer recipe check) |
| solve surface | `d8230f36c0059245` in all 7 legs (= keeper); G-DRIFT all INERT |
| legs (one shard each, archived after verification) | 2019 `8a99e44e`, 2020 `c7573c25`, 2021 `14a894cd`, 2022 `2af2e4d1`, 2023 `c97088b9`, 2024 `ec3306d8`, 2025 `c6d17679` |
| composer | `scripts/probes/_closeoutpjm_lossdemand_compose_span.py` (the keeper's `_pjmnext26` composer + the one declared field) |
| residual probe | `scripts/probes/_closeoutpjm_lossdemand_residual.py` → `results/phase0/pjm/_closeoutpjm_lossdemand_residual.json` |

Full leg SHAs: 2019 `8a99e44e1a3955070737143d7fb6fb70407ef6f3`, 2020 `c7573c2542162041e5855bb63e814d3acff2fb9a`,
2021 `14a894cd411a30011653fd7bbb600a58af2e5393`, 2022 `2af2e4d10672e77997b4e6804ceb5b404ce2cec8`,
2023 `c97088b989fb4a26b81781f0e3b7b25e65ee8829`, 2024 `ec3306d8cff41274f984421d9521b727e03cd4a4`,
2025 `c6d1767916ba535b9c6c9fcf0b26858f180ba82d`.

## 2. The identity (K1)

`R = Σgen + import-node net − storage net charge − Σ D_measured` (P1 sidecars). Under the arm, `R = Σε·F¹ − Σε·F⁰`
exactly; the netted P0 column reproduces each shard's logged `P1 demand netted by` to ≤ 0.0005 TWh.

| TWh | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| keeper R (= Σε·F, double count) | +2.189 | +2.160 | +2.554 | +3.141 | +2.529 | +3.394 | +3.972 |
| netted from P1 demand (Σε·F⁰) | 2.212 | 2.230 | 2.607 | 3.365 | 2.580 | 3.646 | 3.949 |
| P1 dissipation (Σε·F¹) | 2.145 | 2.122 | 2.510 | 3.082 | 2.477 | 3.319 | 3.894 |
| **probe R** | **−0.067** | **−0.109** | **−0.096** | **−0.283** | **−0.104** | **−0.327** | **−0.055** |
| share of the double count removed | 97 % | 95 % | 96 % | 91 % | 96 % | 90 % | 99 % |
| **K1** (`|R|` ≤ 0.05) | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL |

**Why.** P0 is solved at base cost, P1 at bid cost. P1's flows on the lossy links run 1–9 % below P0's. The
one-pass netting is sized on P0, so P1 over-nets by `ε·(F⁰ − F¹)`. The bound declared in the PRECOMMIT
(−0.05 to −0.11, second order) was too small: the bid markup changes the flows by first order, not just the
netting feedback. One pass cannot close this (rule 10). Netting P1's own dissipation inside the LP is the same
thing as a unit receiving-end coefficient, which removes the loss price separation (option B of the FINDING).

## 3. Gates vs keeper (rubric unchanged; same scorer)

| gate | keeper | probe | reading |
|---|---|---|---|
| C1 CC_REGULAR 2022 | FAIL +8.96 | **PASS +7.54** | P2: predicted FAIL→PASS (+7.05…+8.03) — hit |
| C1 CC_REGULAR 2024 | PASS −4.95 | PASS −6.22 | declared widening; stays PASS |
| **C1 CT_PEAKER 2021** | PASS −7.92 | **FAIL −8.28** | **undeclared PASS→FAIL → K2 KILL** |
| C1 COAL_BIT 2019 / 20 / 21 | FAIL +19.73 / +12.74 / +16.72 | FAIL +18.77 / +11.91 / +15.98 | −0.8…−1.0, still out of band (R-56 open) |
| C1 failing cells (run) | 4 | 4 | CC 2022 swaps for CT 2021 |
| C3a mean LMP, worst Δ | — | 2024 −5.4 % → −6.8 % (1.4 pp); 2025 −11.6 → −12.8 (1.2 pp) | **K3 PASS** (≤ 1.5 pp, no PASS→FAIL) |
| C3b NRMSE, worst Δ | — | 2024 0.175 → 0.189 (+0.014); 2025 0.222 → 0.230 | **K4 PASS** (≤ 0.020, no PASS→FAIL) |
| C3c (supporting) | CAVEAT 2019/21/22 | FAIL 2019/21/22 (governance unattested on a probe, so the ledger caveat cannot apply); **2025 PASS→FAIL** (30 h → 24 h of 59 h) | reported; not a pre-registered kill |
| C2, C4, C8 | PASS | PASS | unchanged (C8 CT_PEAKER grounded, 15.6→16.3 % etc.) |
| C6 governance | PASS (attested keeper) | UNATTESTED (probe) | mechanical: probes carry no attestation |
| fossil Δ (P1 class_hourly) | — | −2.20 / −2.23 / −2.55 / −3.23 / −2.35 / −3.46 / −3.77 | P1 in band (§3 PRECOMMIT) |

## 4. Determination

**KILLED on K1 and K2.** The mechanism does what the FINDING said it would: 90–99 % of the loss double count leaves,
and the 2022 CC_REGULAR flip lands as predicted. But its one-pass, P0-sized construction cannot close the identity to
the pre-registered 0.05 TWh, and the extra ~0.3–1.3 TWh it removes from peakers pushes C1 CT_PEAKER 2021 over the
band. That flip was not declared.

**What stays open.** The double count is real (FINDING closeout-PJM-balance), and the keeper still carries it. A repair
that closes the identity has to size the netting on the flows the scored pass actually runs. In one LP pass that
means either option B (a unit receiving-end energy coefficient, which loses the measured loss price separation) or
a forward-defined netting that does not read P0 (for example the measured monthly zonal loss share applied to D,
which is a new construction needing its own PRECOMMIT). Both are owner decisions; neither is built here.

**Matrix.** `zonal_loss_demand_reconciliation` PJM: **R** for this construction (P0-sized one-pass netting), with the
evidence above. CAISO and NYISO stay **U** (the transfer inherits this K1 finding as a prior: their P0/P1 flow gap
will set their residual the same way).

## 5. Bundles and promotion cost (rule 34)

- **The dashboard registration is NOT on `main`.** `dashboard_add_run.py` registered the probe as
  `2026-10-03-closeout-pjm-lossdemand-probe`, but `audit_keepers.py` E13 (rule 35 (f), keeper-only retention) refuses
  any PJM run that is neither the keeper nor stamped to it. Stamping a probe as a keeper touchpoint would misuse rule
  30. The registration commit is therefore reverted inside the lane PR, and nothing is destroyed:
  - The complete registration lives in commit `8c368d00` on `claude/closeout-pjm-lossdemand`: sidecar,
    `runs/<id>.js` payload, and the span's hourly sidecars including `unit_marginal` and JSON. Every gate number in
    §3 is reproducible from it with `calibration_verdict.py`.
  - The full per-leg bundles, including `dispatch/<y>_P1.parquet` and `flows.parquet`, are on the seven
    `claude/closeout-pjm-lossdemand-<year>` branches at the SHAs in §1.
- All of these are on branches the owner cuts. Per rule 31 nothing should be cut before the owner rules on this
  result. A promotion is **not** recommended (K1/K2), so after the ruling nothing needs to be kept.
- Re-solve cost if a successor construction is chartered: 7 shards, about 30 minutes each.
