# FINDING — closeout-PJM-balance: the +2.2–4.0 TWh generation residual is the loss surface's dissipation, counted a second time against a loss-inclusive demand (ZERO LP)

**Verdict.** The residual is fully attributed. It is the energy dissipated on the internal links of
`pjm_zonal_loss_surface`, which the keeper arms. It closes to within 0.002 TWh in every year.

- **Physics.** The loss physics is real, and it is not missing: PJM's measured demand row (EIA-930 BA demand)
  already includes every transmission and distribution loss.
- **Accounting.** The LP's dissipation is a double count. It is a demand-basis bookkeeping error introduced
  when pjm-136 M2 was armed (2026-07-28), not a sidecar or aggregation artefact.
- **What serves it.** Fossil marginal units serve it, mostly CC_REGULAR.

Nothing was built, solved or registered. Keeper `2026-10-03-closeout-pjm-nuc-keeper` is unchanged. Desk item
R-56 §5.1 (from `docs/records/pjm/closeout-pjm-cc22/` on `claude/closeout-pjm-cc22`).

**Probe.** `scripts/probes/_closeoutpjm_balance_trace.py` writes `results/phase0/pjm/_closeoutpjm_balance_trace.json`.
- It reads the keeper's committed hourly sidecars.
- It reads each leg's `flows.parquet` by full shard SHA. The shard branches are cut, but the commits are still
  fetchable; the SHAs are listed in the probe's `LEG_SHA`.
- It reads the measured `PJM_loss_surface.csv`.

## 1. The cc22 premise was wrong

The cc22 FINDING (§5.1) states: "The PJM LP has no line losses (`link_loss` is MISO-only)." That is not the code:

- The keeper's `run_config_<Y>.json` carries `pjm_zonal_loss_surface: true` in all 7 years. That is pjm-136 M2,
  matrix cell `zonal_loss_surface` = **K** for PJM.
- `model/interchange/spec.py:4534` splits each internal PJM link into a one-way pair
  (`apply_pjm_zonal_loss_links`).
- `runner.py:3583` passes `build_pjm_link_loss(...)` as `link_loss` into the energy balance.
- In `model/lp/rows.py:1701–1713`, the receiving zone of link *l* gains `(1 − ε_l,t)·F_l,t` while the sender
  gives up `F_l,t`. The constraint is `ε = max(0, (dev_to − dev_from)/(1 + dev_to))`, with ε taken monthly from
  PJM's own MLC/MEC record.
- The five `PJM_external` star links stay lossless (`_pjm_internal`).

The LP's own identity is therefore

    Σ gen + Σ import-node net − storage net charge − Σ demand = Σ_l,t ε_l,t · F_l,t   (slack = dump = 0)

## 2. The identity closes on the committed bytes

| TWh | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| residual R (sidecars) | 2.189 | 2.160 | 2.554 | 3.141 | 2.529 | 3.394 | 3.972 |
| Σ ε·F (flows × surface) | 2.189 | 2.160 | 2.554 | 3.141 | 2.529 | 3.396 | 3.973 |
| R − Σ ε·F | −0.0005 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | −0.0015 | −0.0011 |
| flow on lossy links | 96.2 | 99.8 | 113.5 | 130.1 | 116.9 | 136.3 | 142.4 |
| flow-weighted ε | 2.28 % | 2.16 % | 2.25 % | 2.42 % | 2.16 % | 2.49 % | 2.79 % |
| peak-hour loss (MW) | 717 | 611 | 775 | 889 | 800 | 1,265 | 1,399 |

**De-minimis open item.** All of the identity closes to the MWh except 12 hours of the 61,320:
- one hour in 2019, six in 2024 and five in 2025;
- all evening peaks with pumped storage discharging at or near its limit;
- all negative (R < Σ ε·F) and ≤ 0.0015 TWh a year.

It is not traced further.

**Where the loss arises.** It sits on the persistent west→east and west→south transfers. Each of the following
links carries 0.3–1.0 TWh a year:
- `West_APS>SWMAAC` (0.64–0.91)
- `Central_PA>EMAAC` (0.33–1.05)
- `ComEd>AEP_Ohio` (0.33–0.99)

`AEP_Ohio>Dominion` grows from 0.07 to 0.42 TWh over the span. The loss runs about 25 % higher overnight (h00–08)
than in the afternoon, and is highest in winter and July.

**Rows that close by construction.** These cover every alternative in the charter:
- **Demand definition.** The model's demand matches EIA-930 D to within 0.1 TWh, except 2020 (−2.95) and 2024
  (−2.18) per the cc22 ledger. Either way it does not enter R, because R uses the model's own demand row.
- **Interchange.** The external star is lossless. The import node's net is inside the sum.
- **Storage.** Net charge, which includes round-trip loss, is subtracted.
- **Aggregation.** R is computed hour by hour.

## 3. (1) Real physics or (2) bookkeeping? Both, and the energy half is bookkeeping

The **price** half is real and measured. PJM's LMP carries a marginal-loss component, and the delivery-factor
ratio is what separates the zonal duals (pjm-136; rule 4).

The **energy** half is a double count, for two reasons.

**(a) The demand basis already includes losses.** EIA-930 BA demand is derived as D = NG + TI. In 2021–2024 the
PJM rows close to that identity within ±0.16 TWh:

| TWh | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| D − (NG − export) | 9.84 | 8.75 | 0.13 | −0.05 | −0.13 | −0.16 | −14.75 |

Source: the cc22 ledger, `_closeoutpjm_cc22_ledger.json`. The 2019, 2020 and 2025 offsets are EIA-930 reporting
artefacts, not losses: their sign is mixed, and losses would be about 2 % of load, not 1.2 % and then −1.7 %.

Measured D is therefore generator-side energy. All of PJM's real transmission and distribution losses, roughly
2 % of load and on the order of 15 TWh a year, are already inside it. The LP dissipates a further Σ ε·F on top of
that, so real PJM's `NG − export` equals D while the model's equals `D + 2.2…4.0 TWh`.

**(b) It dissipates at the marginal rate, not the average rate.** ε is the *marginal* delivery-factor deviation.
For I²R losses, marginal ≈ 2 × average. That is why PJM refunds the marginal-loss over-collection (the loss
surplus). So even on a loss-exclusive demand basis, the LP's inter-zonal dissipation would roughly double the
physical inter-zonal loss.

**Answer.** (1) This is not physics the model lacks. It is physics the measured demand already contains.
(2) It is a demand-basis bookkeeping error: a rule-14 "boundary/aggregation misalignment" between a loss-inclusive
measured demand and a loss-dissipating network. It is not a scoring or aggregation artefact in the bench.

## 4. (3) Which classes serve it, and how much of the C1 over-runs it explains

The LP is not re-solved, so this is first order.

- **Peel.** Each hour's `ε·F` is taken off the top of the running P1 merit order in `unit_marginal`, highest
  offer `mc` first, excluding nuclear, hydro, the import node and virtuals.
- **Split.** As a cross-check, each hour's `ε·F` is split evenly over the hour's `marginal`-flagged units. The
  split covers 76–79 % of the loss; the remainder falls in hours where only excluded or VRE units are flagged.

| TWh | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| C1 CC_REGULAR model − bench | +3.62 | +6.02 | +0.77 | **+8.96** | +3.40 | −4.95 | −12.64 |
| loss on CC_REGULAR (peel / split) | 1.13 / 0.63 | 0.67 / 0.59 | 1.44 / 0.90 | **1.91 / 0.93** | 1.00 / 0.59 | 0.93 / 0.72 | 2.49 / 1.07 |
| share of the over-run (peel) | 31 % | 11 % | (> 100 %) | **21 %** | 29 % | (worsens an under-run) | (worsens an under-run) |
| C1 COAL_BIT model − bench | +19.73 | +12.74 | +16.72 | +6.97 | +3.05 | +0.60 | +9.46 |
| loss on COAL_BIT (peel / split) | 0.18 / 0.46 | 0.68 / 0.43 | 0.05 / 0.36 | 0.06 / 0.46 | 0.85 / 0.26 | 1.57 / 0.37 | 0.35 / 0.36 |
| share of the over-run (peel) | 1 % | 5 % | 0.3 % | 1 % | 28 % | (> 100 %) | 4 % |
| rest of the loss (peel) | CT_PEAKER 0.31, ST_GAS 0.31, CC_CHP 0.16 | CT/ST 0.55 | CT_PEAKER 0.40, ST_GAS 0.30 | CT_PEAKER 0.47, ST_GAS 0.33 | CC_CHP 0.35, CT 0.31 | CT 0.72 | CT 0.95 |

**Reading.**
- **CC_REGULAR.** The loss carries 0.6–2.5 TWh of it a year. For the **2022 C1 flip** (+8.96 against the ±8 TWh
  band; band = min(max(2 % load, 3 % gen), 8) = 8 TWh for PJM), removing the double count lands at about +7.05
  (peel) to +8.03 (split): inside the band, or at the knife-edge. In 2024–25, where CC_REGULAR already
  under-runs, the same repair makes C1 worse by 0.7–2.5 TWh.
- **COAL_BIT.** The 2019–21 over-run (+12.7 to +19.7, R-56 open) is **not** this. The loss explains 0.3–5 % of
  it.

## 5. Is it PJM-specific or LP-wide?

It is LP-wide wherever a zonal loss surface is armed, and absent elsewhere. Same identity, same sidecars:

| residual R (TWh) | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | loss surface armed |
|---|---|---|---|---|---|---|---|---|
| MISO `closeout_miso_nuc_span` | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | −0.008 (= slack) | 0.000 | no |
| ERCOT `closeout_ercot_l1_span` | 0.000 | 0.000 | −0.003 (= slack) | 0.000 | 0.000 | 0.000 | 0.000 | no |
| CAISO `closeout_caiso_w1_a2_span` | 0.36 | 0.36 | 0.44 | 2.42 | 0.60 | 2.24 | 2.32 | `caiso_zonal_loss_surface` |
| NYISO `w0_nyiso_span` | — | — | 2.17 | 1.93 | 1.65 | 1.89 | 1.73 | `nyiso_zonal_loss_surface` |

The CAISO and NYISO rows are the bare residual. They are not yet decomposed into Σ ε·F, because their leg flows
were not fetched here. As a share of load, NYISO's residual (about 1.1–1.4 %) is larger than PJM's (0.3–0.5 %).

## 6. Structural repair: none built; for the desk and the owner

- **(A) Demand-basis reconciliation (recommended). Est. C1: 2022 CC_REGULAR +8.96 → about +7.0 to +8.0.**
  Net the modeled dissipation out of the demand row at the existing P0→P1 seam, as a one-pass measurement:
  - Each zone's P1 demand becomes `D_z,t − (its receiving-side share of Σ ε·F from P0 flows)`. This follows the
    pattern of the three P1 commitment bridges, and it complies with rule 10.
  - Prices keep the measured MLC separation, because the (1 − ε) coefficient is untouched.
  - P1 generation then satisfies `NG − export = D` up to the P0→P1 flow change.
  - It is a reconciled form of the measured D (the rule-14 exception: D is defined generator-side, and the
    network dissipates a part of what D already contains). It responds to forward drivers (rule 13). It has no
    free scalar (rule 21).
  - First-order C1 effect, as in §4: about −2.2 to −4.0 TWh of fossil a year, mostly CC_REGULAR (−0.7 to −2.5)
    and CT/ST gas, and −0.05 to −1.6 TWh COAL_BIT.
  - It is a solve-affecting ScenarioConfig field. It needs a matrix row plus a cell in every shard (rule 28), and
    the full span (rule 29), with CAISO and NYISO as transfers at `U`.
- **(B) Average-loss energy.** Dissipate ε/2 and keep pricing at ε. This cannot be done in one LP: the column
  coefficient sets both the primal energy and the dual ratio. Not recommended.
- **(C) Loss-exclusive measured demand.** Use D minus published PJM losses, then let the LP add back inter-zonal
  marginal losses. This replaces one misalignment with another (only the inter-zonal component is modeled, at
  the marginal rate). Not recommended.
- **(D) Disarming `pjm_zonal_loss_surface`.** This removes a keeper-armed measured price mechanism (pjm-136, the
  first lever that moved the Dominion inversion). Rule 1 rules it out as a fit fix.

**Caveat on the estimate.** The C1 deltas are first order. In a re-solve, removing 2–4 TWh of load lowers some
duals and can reorder the gas–coal margin. The 2024–25 CC_REGULAR under-runs would widen. The C1 ledger cannot be
read off this table as a prediction.

## 7. Matrix

`zonal_loss_surface` (PJM) stays **K**. The cell's mechanism was audited, not lever-tested. Evidence appended:
"closeout-PJM-balance 2026-10-03: energy double-counts against the loss-inclusive EIA-930 demand (+2.2–4.0
TWh/yr); price half unaffected". No other cell is touched.
