# FINDING — closeout-PJM-lossshare (R-60 phase 0, ZERO LP): no measured loss share can close the identity; closed as a known boundary (R-61)

Owner ruling **R-60** (2026-10-03, verbatim): "New route: measured loss share (Recommended)". Card: "New lane: reduce each
zone's demand by PJM's measured monthly loss share instead of reading the first pass. It's forward-reproducible and keeps
loss pricing. Zero-LP check first, new PRECOMMIT, then 7 shards."

Owner ruling **R-61** (2026-10-03, verbatim): "Close as known boundary (Recommended)". Card: "Keepers unchanged. The
+2.2–4.0 TWh (PJM), 0.4–2.4 (CAISO) and 1.7–2.2 (NYISO) are ledgered as a disclosed demand-basis double count; matrix
stays R for both constructions."

Nothing was built or solved under R-60. Keeper `2026-10-03-closeout-pjm-nuc-keeper` is unchanged. Inputs: the seven
committed legs of probe `2026-10-03-closeout-pjm-lossdemand-probe` (RESULT in this directory; shard SHAs in its §1) and
the measured `PJM_loss_surface.csv`. Arithmetic: `scripts/probes/_closeoutpjm_balance_trace.py::link_losses` on each
leg's P1 `flows.parquet`, against the leg's P1 `system` demand.

## 1. K1 is unreachable for any netting that does not read the solve

Let `X` be any demand netting fixed before the solve (a measured share, a published loss total, a constant). The LP
identity of closeout-PJM-balance §1 then gives

    R = Σ gen + import net − storage net charge − Σ D_measured = Σ_l,t ε_l,t · F¹_l,t(X) − X.

K1 (`|R| ≤ 0.05` TWh/yr) therefore needs `X` to equal the model's own P1 dissipation to within 0.05 TWh. That
dissipation is an endogenous model quantity: it is the marginal-rate ε on the model's eight aggregated zones times the
model's own flows. It is not what any meter records.

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| Σε·F¹ (TWh) | 2.145 | 2.122 | 2.510 | 3.082 | 2.477 | 3.319 | 3.894 |
| share of D (%) | 0.268 | 0.276 | 0.315 | 0.380 | 0.316 | 0.408 | 0.462 |
| monthly share range (%) | 0.16–0.33 | 0.15–0.35 | 0.21–0.45 | 0.26–0.47 | 0.22–0.40 | 0.25–0.62 | 0.20–0.77 |
| R under a pooled constant 0.348 % | −0.641 | −0.551 | −0.262 | +0.261 | −0.255 | +0.489 | +0.958 |

By receiving zone the share of zonal demand is:

| zone | 2019–2025 range (%) |
|---|---|
| ComEd | 0.00 |
| Central_PA | 0.00–0.05 |
| West_APS | 0.01–0.08 |
| Dominion | 0.10–0.43 |
| ATSI | 0.18–0.37 |
| AEP_Ohio | 0.20–0.55 |
| EMAAC | 0.25–0.76 |
| SWMAAC | 1.31–1.72 |

The pooled constant in the last row of the first table is fitted in-sample to all seven years. That makes it a tuned
scalar, forbidden by rules 1 and 21. Even so it misses K1 by a factor of 5–19. A measured share that is not fitted can
only do worse, except by coincidence.

## 2. The candidates (rule 13 / rule 14)

| candidate | measured? | forward-reproducible (rule 13 form) | maps to the representation (rule 14) | intake | verdict |
|---|---|---|---|---|---|
| PJM Data Miner / IMM published transmission-loss MWh | yes | yes (republished yearly; forward as a share of load) | no | needs fetch + schema | rejected |
| EIA-861 utility losses | yes | yes | no | needs fetch + schema | rejected |
| ε surface × measured link flows | flows not measured | — | no | — | rejected |

Why each candidate fails to map to the representation:
- **PJM published loss MWh.** It is TOTAL physical transmission loss at all voltages, intra-zonal included, at the
  AVERAGE rate: on the order of 2 % of load. The model's dissipation is 0.27–0.46 % inter-zonal at the MARGINAL rate
  (closeout-PJM-balance §3b: marginal ≈ 2 × average). Netted unscaled it over-nets by about 10 TWh/yr. Scaling it down
  needs an unmeasured inter-zonal fraction, which is a fitted scalar.
- **EIA-861 losses.** Annual, at utility/state level, with T&D combined. It has no PJM-zone or month grain, and its
  magnitude mismatch is worse than PJM's.
- **ε surface × measured flows.** Measured zone-to-zone flows on the LP's eight-zone links do not exist. Data Miner
  `transfer_limits_and_flows` (on disk, 2019–25) carries ten interface series (AP-South, AEP/DOM, 5004/5005,
  Bedington–Black Oak, …), not links. Mapping them onto links would be an estimate, and the product would still have
  to match the model's own `F¹`.

## 3. CT_PEAKER 2021 headroom (C1)

The keeper's C1 CT_PEAKER 2021 is −7.92 TWh against the ±8.00 band, so it has 0.08 TWh of headroom. The P0 probe's
2.61 TWh netting moved it by −0.36 TWh. **Any** repair that removes the double count at a scale of about 0.6 TWh or
more in 2021 flips CT_PEAKER 2021 PASS→FAIL. This is structural to every fix and must be declared ex ante by any
successor. For comparison, C1 CC_REGULAR 2022 (keeper +8.96) needs about 1 TWh or more removed in 2022 to pass.

## 4. Disposition (R-61)

Closed as a disclosed rule-14 representation boundary. The keepers are unchanged. The double count is ledgered as
disclosed by the desk in the close-out plan: PJM +2.2–4.0, CAISO 0.4–2.4, NYISO 1.7–2.2 TWh/yr.

Matrix `zonal_loss_demand_reconciliation`:
- PJM stays **R**, now citing R-61, for both constructions: P0-sized netting (RESULT in this directory) and measured
  share (this note).
- The CAISO and NYISO cells are untouched by this lane.

Retention: `claude/closeout-pjm-lossdemand` (registration commit `8c368d00`) and the seven
`claude/closeout-pjm-lossdemand-<year>` leg branches are kept as evidence until the owner deletes them.
