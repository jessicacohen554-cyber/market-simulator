# FINDING — SPP-97: the SPP CC_REGULAR shape miss. It is not a duct offer, and a gap bridge can't reach it. Zero LP.

**Trigger.** Owner review of the Run Explorer's "CF Distribution — CC Regular" (2020): the model sits near its own
ceiling far more often than CAMPD, while ST_GAS, coal and lignite under-run. The owner proposed a duct-peaking offer
adjustment, then chose "CC min-load commit" on the decision card.
**Control.** Keeper `2026-09-28-spp-94-curtail-rows` (`spp94_arm_span`). **LP spent: 0.**
**Probes.**
- `scripts/probes/_spp97_cc_incremental_hr.py` → `docs/handoffs/spp97/cc_incremental_hr.json`
- `scripts/probes/_spp97_cc_commit_reach.py` → `docs/handoffs/spp97/cc_commit_reach.json`

## 1. How the dashboard defines CF

The Run Explorer's CF Distribution divides each series by **its own annual maximum hour**, not by nameplate
(`backcast-runs.js::drawCfDistribution`). So "model at 80–100 %" means the fleet sits at its own ceiling. On a
nameplate basis the class never reaches 80 % on either side. The shape difference is real under both definitions.

Class CF on a nameplate basis, over the same plants on both sides:

| year | model median | CAMPD median | model hours < 20 % | CAMPD hours < 20 % |
|---|---|---|---|---|
| 2019 | 49.5 | 43.9 | 693 | 478 |
| 2020 | 53.7 | 46.7 | 939 | 825 |
| 2021 | 20.0 | 30.8 | 4,378 | 2,493 |
| 2022 | 16.7 | 32.0 | 4,576 | 2,281 |
| 2023 | 45.8 | 43.2 | 2,241 | 1,061 |
| 2024 | 45.2 | 41.9 | 2,210 | 979 |
| 2025 | 37.3 | 37.0 | 2,585 | 1,133 |

The model's CC fleet is **bimodal**: it has too many near-off hours in every year, and too many near-ceiling hours in
2019–20. The real fleet sits mid-range. It is committed and part-loaded (SPP-75: 0.41–0.44 of output).

## 2. The keeper's CC offer is one flat step per plant

The fleet was rebuilt with `fleet_only` (2020). Every CC_REGULAR plant has four tranches (committed / econ-low /
econ-high / peak), and all four carry the **identical** offer heat rate, measured average HR × 0.93. For example, plant
165 is 6.680 × 0.93 = 6.213 on every tranche. `cc_peak_hr_penalty` (1.15) never reaches the offer. The reason is that
`offer_curve_by_group.CC_REGULAR` covers the group, and all four of its bands are 0.93.

## 3. SPP's own CEMS shows no duct-firing step (the duct-offer hypothesis)

The data is 15 `flag=='ok'` CC plants (steam turbine metered, per the existing boundary guard), 2019–2025. For each
plant, heat input is binned against load, and the incremental HR over each band is taken as a ratio to the plant's
average HR.

| band | capacity-weighted | median | p25–p75 |
|---|---|---|---|
| committed (average HR at min-load) | **1.101** | 1.054 | 1.025–1.171 |
| econ-low incremental | 0.940 | 0.889 | 0.772–1.003 |
| econ-high incremental | 0.908 | 0.936 | 0.867–0.994 |
| **peak / duct incremental** | **0.931** | 0.948 | 0.794–1.058 |

The top band is **not** costlier per MWh than average. Pricing the duct band up would therefore be a number with no
measured source (rules 1 and 13). Separately, the rule-1(c) channel needs one value across all years, and raising CC
offers would push CC further under in 2021–25, where it already runs −7 to −29 % against EIA-923.
**Not pursued.**

## 4. A P0-anchored gap bridge cannot reach the miss (the chosen lane)

"Missing commitment" plant-hours are those where CAMPD is online (≥ 5 %) and the model is off. Those hours were
classified by the model's own off-gaps, and the precision of flooring every gap ≤ N hours was computed. Precision is
the share of floored hours in which CAMPD really was online.

| year | missing-commit TWh @ min-load | in gaps ≤ 24 h | precision ≤ 4 h | precision ≤ 24 h | unconditional online |
|---|---|---|---|---|---|
| 2019 | 1.52 | 0.72 | 0.595 | 0.458 | 0.599 |
| 2020 | 1.74 | 0.96 | 0.566 | 0.448 | 0.588 |
| 2021 | 4.66 | 2.19 | 0.705 | 0.543 | 0.506 |
| 2022 | 5.41 | 2.43 | 0.627 | 0.582 | 0.540 |
| 2023 | 3.41 | 1.42 | 0.568 | 0.530 | 0.604 |
| 2024 | 3.13 | 1.34 | 0.672 | 0.570 | 0.621 |
| 2025 | 3.70 | 1.72 | 0.677 | 0.608 | 0.587 |

The reach is larger than SPP-44's realized 0.41 TWh, but the **precision is at or below chance in 2019, 2020, 2023 and
2024**. The model's own off-gaps do not mark when SPP kept its CCs committed. This is the failure that killed SPP-44
(0.694 against 0.660 unconditional), now shown across all seven years. `spp_gas_commitment_bridge` **stays R**, and
no PRECOMMIT or shard was launched.

## 5. What would reach it

The object is CC **commitment state** that is exogenous to the LP's own run pattern. The only admissible form is a
measured, forward-reproducible online profile: each plant's multi-year CEMS online probability by season × hour, the
same kind of input as the thermal-tranche `online_frac`. It would hold the committed tranche at measured min-load
(0.209) in the hours the plant is typically online.

That is a new mechanism and needs a design charter:
- a new field;
- a matrix row in every shard (rule 28(c));
- a rule-17 window / driver / forward story;
- a check that it does not stack on `coal_sync_ensemble_level` or `mustrun_commitment_feasibility_clip` (rule 19).

It is also the SPP-82/83 commitment-state lane, which is owner-gated.
