# FINDING — SPP-91: SPP coal's flat on-line shortfall is not reserve headroom. About a third to a half of it is intra-zone congestion. No admissible, material change.

**Lane** SPP-91 · **ZERO LP** · keeper `2026-09-26-spp-86-coal-extract` (bundle `spp86_arm_span`, basis_sha `d72e5f10`)
· probes `scripts/probes/_spp91_flat_coal_series.py` (stage 1), `_spp91_node_lmp_fetch.py` (node LMPs),
`_spp91_flat_coal_tests.py` (stage 2) · record `results/calibration/_spp91_flat_coal_tests.json`.
Nothing solved, registered or promoted. Keeper unchanged. No promotion question (rule 31).

## 0. Object

SPP-90's largest component: **F** = coal units on line, output flat (|ΔG| ≤ 2 % D/h), below their own same-week in-money
capability, in hours with the actual hub RT LMP ≥ $30. Stage 1 reproduces SPP-90 exactly:
F = 1.145 / 1.113 / 0.983 / 1.348 / 1.043 / 1.258 / 1.015 GW (2019–25).

F is **spread across the fleet**. Every plant carries about 5–10 % of its own on-line MW, and no single pocket dominates.

## 1. (a) Regulation-up / spin headroom — NOT the object

Source: SPP RTBM cleared MW (`spp_rtbm_or_cleared_hourly.parquet`, SPP-81) and RTBM MCPs (`data/raw/spp-or-mcp`).
Both are **system-wide**. Cleared reserve **by resource or fuel is not published**. SPP-82 §1: the masked offer files are
the only resource grain, and they carry no dispatch or award.

| ≥ $30 hours | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| F, flat coal shortfall (GW) | 1.15 | 1.11 | 0.98 | 1.35 | 1.04 | 1.26 | 1.02 |
| SPP reg-up + spin cleared, **all fuels** (GW) | 1.10 | 1.12 | 1.12 | 1.12 | 1.16 | 1.17 | 1.14 |
| F ÷ (reg-up + spin) | **1.04** | **0.99** | 0.88 | **1.20** | 0.90 | **1.07** | 0.89 |
| r(F, cleared reg-up + spin), within-week | 0.26 | 0.13 | 0.08 | 0.17 | 0.22 | 0.28 | 0.30 |
| r(F, reg-up MCP), within-week | −0.08 | −0.07 | 0.09 | −0.04 | −0.05 | −0.09 | −0.03 |
| r(F, spin MCP), within-week | −0.10 | −0.12 | 0.06 | −0.11 | −0.09 | −0.11 | −0.07 |

- **Size bound fails.** Headroom would need coal to hold 88–120 % of **all** of SPP's reg-up plus spin. Gas, hydro and
  storage also carry those products.
- **No price signal.** When reserves are dear, F does not rise; the MCP correlation is slightly negative.
- **No step at 2022.** The ramp product (+0.5 GW cleared from 2022-03) leaves F unchanged: 2021 0.98 vs 2023 1.04.
- **Reserve headroom can be at most a minor part of F.** `energy_reserve_coopt` stays `I` (SPP-55). `reserve_pergen` and
  `dynamic_reserve_requirements` stay `U`. There is no by-fuel instrument to derive either from.

## 2. (b) Nodal congestion — REAL, and mostly INSIDE the model's zones

Source: SPP RTBM `rtbm-lmp-by-location`, the twelve `RTBM-LMP-MONTHLY-SL` members per year, range-read (anonymous, SPP-14
route). There are 16 coal plants, mapped by settlement-location and PNODE name, covering **72–75 % of F**. **Clock:** the
monthly file's Date/HE label is **GMT hour-ending**. Subtracting 7 h reproduces the committed model-clock hub series
(`actual_lmp_hourly_zonal_SPP.parquet`) exactly, r = 1.000 with zero error, in 2019, 2023 and 2025. Local-time readings
misalign it by 5–6 h, and a successor must not repeat that.

| mapped plants, ≥ $30 hours | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| share of F MWh with plant-node LMP < the keeper's own top coal offer for that plant | 0.33 | 0.34 | 0.27 | 0.31 | **0.43** | **0.49** | **0.38** |
| share of F MWh with plant-node LMP < $25 | 0.36 | 0.35 | 0.30 | 0.31 | 0.42 | 0.52 | 0.42 |
| node − hub, F-weighted ($/MWh) | −14.4 | −13.5 | −7.3 | −17.2 | −20.6 | −29.6 | −20.2 |
| node − hub, on line with no F ($/MWh) | −10.7 | −7.2 | −11.4 | −14.6 | −10.4 | −19.5 | −12.6 |
| node − **own-zone** hub, F-weighted, North plants | −6.4 | −11.1 | −3.3 | −8.7 | −24.5 | −9.9 | −21.1 |
| node − **own-zone** hub, F-weighted, South plants | −20.0 | −8.0 | −15.4 | −17.2 | −13.3 | −40.4 | −7.8 |

- **About a third to a half of F is correct economic dispatch at the plant's own node.** Hub ≥ $30 does not mean "in the
  money" for SPP coal. In 27–49 % of the flat-shortfall MWh, the plant's node cleared below the keeper's own top coal offer.
  The share is highest in 2023–25.
- **The discount is intra-zone.** Plant nodes sit $3–40 below **their own** zone hub. A 2-zone North/South model cannot
  carry it at any TTC.
- **The keeper's N–S seam barely separates** (side observation, and not a lever for this lane). Mean N−S spread in ≥ $30
  hours: keeper −0.0 to −4.4 vs actual −28.6 / −24.1 / −28.3 in 2021 / 2022 / 2024. The p10 is keeper 0 vs actual −34 to
  −117. This corroborates SPP-40 (`measured_interface_limits` O) and SPP-57 (the three-zone arm was killed at its screen).
- **The remaining ~50–70 % of F is unattributed.** In those hours the node LMP is above the keeper's top offer. The known
  candidates are small reserve holds, self-scheduled fixed-MW output, and the upward bias of a same-week-max capability
  statistic. None has a public unit-grain instrument.

## 3. Verdict

- **No admissible, material change. No PRECOMMIT, no G-DRIFT, no shard.**
- (a) fails the size bound and has no price signal. There is also no by-fuel instrument to build a forward-reproducible
  input from (rule 13).
- (b) is real, but its only seam is SPP's zone topology (`internal_congestion_split`, U). A new intra-zone split is a
  structural lane of its own, and SPP-57 already killed the simplest pocket.
- **The level test also blocks it.** Congestion-driven backdown would **lower** keeper coal. The keeper already offers
  0.6–1.3 GW less than the fleet had on line (SPP-90), and it is already short in the money in 2019, 2020, 2023 and 2024.
  Reproducing F explicitly would widen that shortfall in the passing years. What F adds is **placement** evidence (which
  plants back down), not a missing level.
- Nothing here closes 2022, and nothing was selected on it (rule 1). The multipliers were not touched (rule 1(c)).

## 4. Matrix

Cells stay put. Evidence is appended to `internal_congestion_split` (U), `energy_reserve_coopt` (I) and `reserve_pergen` (U)
in `docs/codebase-site/data/mechanism-matrix/SPP.js`. The DO-NOT-REDO note is at the top of `docs/mechanism-testing-matrix.md` §5.7.

## 5. Status against `complete` / `frontier`

- **`complete` is already declared for SPP** (`calibration-complete.json` `complete` block). Train tier 2023–25 is
  CALIBRATED with a lone ledgered C3c.
- **`frontier` is NOT reached.** The validation tier 2019–22 reads NOT-YET (reported, not gating, rule 30(c)). The SPP
  lever queue also still carries most matrix cells untested (SPP-31 §1).
