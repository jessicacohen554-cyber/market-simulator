# FINDING — miso-297: the IMM marginal-share census cannot identify a single coal econ multiplier — one value serves two regimes in opposite directions, and the ruled gas form raises, not lowers, gas cost in 2019–2022. No shard launched; keeper unchanged.

```
LANE    : miso-297 (owner rulings 2026-10-01, miso-296 decision cards: "PRECOMMIT the joint arm (Recommended)" +
          "IMM marginal-share census (Recommended)")
KEEPER  : 2026-09-28-miso-280-splitremap (results/calibration/miso280_span, 2019-2025), unchanged
LP      : none. Fleet-only rebuilds of the keeper recipe (keeper gas; owner-ruled gas form), the P0 base stack and the
          P1 bid stack (miso-287 markup) cleared at the keeper's own P1 thermal quantity, 15 coal econ multipliers x
          2 legs x 7 years; keeper P1 hourly sidecars; zone-resolved hub RT; measured zonal demand
PRECOMMIT: docs/records/miso/PRECOMMIT-miso297-joint-gas-coal-2026-10-01.md (rules fixed at 025012a7 before the pooled curve)
PROBES  : scripts/probes/_miso297_joint_census.py -> results/phase0/miso/_miso297_joint_census.json
          scripts/probes/_miso297_shard_readout.py -> results/phase0/miso/_miso297_readout_keeper.json (K-3/K-4 baseline)
          scripts/probes/_miso297_arm_table.py, _miso297_shard_check.py, _miso297_compose_span.py (ready, unused)
G-DRIFT : docs/records/miso/GDRIFT-miso297-keeper-8f765fef-2026-10-01.md (0 LIVE; MISO moved rows 0)
CELLS   : gas_marginal_commodity_pricing O, gas_variable_transport O (evidence added, not re-tested alone, no solve);
          offer_curve_by_group K (note); no R/I/G cell re-tested (rule 28)
```

## 1. Answer

1. **The identification fails on its own pre-stated rule.** Pooled 2019–2024 (equal-year mean, 8760 h each), the IMM
   SOM Table 1 coal SMP share is 0.363. The joint leg's pooled bid-stack coal marginal share is 0.285 at m = 1.00,
   rises to a maximum of **0.305 at m = 0.80**, and falls to 0.116 at m = 0.30. It never crosses 0.363, so no m*
   exists; no arm table was written and no shard was launched (PRECOMMIT §3.1, §3.3).
2. **Why: one lever, two regimes.** In the low-gas years the coal econ ramp sits above the CC margin and lowering it
   raises coal's share — 2020 reaches the IMM's 0.40 at m = 0.70, 2023 and 2024 top out at 0.26 against 0.36. In
   2019 / 2021 / 2022 (and 2025) the ramp is already at or inside the margin (coal econ 28–89 % dispatched in the
   keeper stack) and lowering it pushes coal below gas, so coal becomes fully infra-marginal and the margin returns to
   gas: 2019 0.46 → 0.38 by m = 0.60, 2021 0.38 → 0.23, 2022 0.16 → 0.10. One value across years (rule 1 (b)) cannot
   raise the pool to the IMM because every point of share gained in 2020/2023/2024 costs share in 2019/2021/2022.
3. **The share it does gain is at the wrong end of the load curve.** At m = 0.80 the joint leg's quintile-5 coal share
   is 0.55–0.57 in 2019/2020 while quintile 1 is 0.17–0.35; the IMM's coal margin is "generally in off-peak hours".
   The model's coal econ is a ~9–15 GW block at one level: it is marginal only in the narrow band of hours where the
   stack passes through it, which under lower m moves to high load, not to the night.
4. **The owner-ruled gas form raises gas cost in 2019–2022.** The measured variable transport on the fleet's own
   plants is $0.24–0.36/MMBtu cap-weighted on CC_REGULAR and $0.71–0.84 on all gas (own-plant rung on 86–91 % of CC
   and 68–74 % of all gas capacity; the rest on the pooled rungs), against a print-over-hub wedge of $0.13–0.39 in
   those years. CC_REGULAR fuel moves +$0.11 / +$0.07 / +$0.09 / +$0.14 (2019–2022) and −$0.25 / −$0.13 / −$0.05
   (2023–2025). Static q1–q2 error: +0.5 / +0.5 / +0.3 / +1.2 in 2019–2022, −0.8 / −0.4 / 0.0 in 2023–2025. At zero
   LP the ruled form does not take coal's margin (pooled share +0.010) — the miso-224 collapse was the bare hub.
5. **What the hump would have cost.** At m = 0.80 (joint) the static re-merit adds +1.3 to +3.0 GW of coal (+12 to
   +26 TWh/yr static; the LP converts 0.27× of a static coal move, miso-224/225, so ~+3 to +7 TWh) and takes −0.3 to
   −1.9 GW of CC_REGULAR, with COAL_PRB already at +6.40 / +5.69 / +5.28 TWh in 2019 / 2021 / 2022 inside an 8 TWh band;
   the low-load price falls $0.1–1.1 in 2019/2020/2023/2024 (q1–q2 error 2.9–4.8 → 2.0–3.4) and the all-hours price
   falls $1.4–2.2 in every year, deepening 2021 / 2022 / 2025 (already −5.6 / −5.1 / −1.1 %).

(All numbers: PRECOMMIT §3.2–3.7 tables; the JSON carries every (leg, m, year) cell.)

## 2. The curve (pooled bid-stack coal marginal share; IMM pooled 0.363)

| m | 1.00 | 0.95 | 0.90 | 0.85 | **0.80** | 0.75 | 0.70 | 0.65 | 0.60 | 0.55 | 0.50 | 0.45 | 0.40 | 0.35 | 0.30 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| joint (ruled gas) | 0.285 | 0.288 | 0.296 | 0.303 | **0.305** | 0.303 | 0.297 | 0.282 | 0.267 | 0.241 | 0.216 | 0.183 | 0.161 | 0.133 | 0.116 |
| coal-only (print gas) | 0.274 | 0.281 | 0.292 | 0.292 | 0.298 | 0.296 | 0.288 | 0.274 | 0.257 | 0.232 | 0.207 | 0.175 | 0.150 | 0.125 | 0.107 |

Per year, joint leg (IMM in brackets): 2019 0.46 → 0.49 (m 0.85) → 0.15 [0.47]; 2020 0.28 → 0.40 (m 0.60–0.70) → 0.15
[0.40]; 2021 0.38 → 0.13 [0.35]; 2022 0.16 → 0.09 [0.24]; 2023 0.22 → 0.26 (m 0.70–0.75) → 0.08 [0.36]; 2024 0.20 → 0.26
(m 0.70) → 0.10 [0.36]; 2025 0.28 → 0.19 (m 0.70) [unpublished].

## 3. What this is, and what it is not

- **It is a structural statement about the coal offer curve's shape, not its level.** The real fleet's coal is
  marginal 36–47 % of intervals in low-gas years because its offers are spread across a continuum of units and
  increments at and around $15; the model's coal econ is a block whose level a single multiplier moves up or down as
  a whole. Scaling the block cannot put coal at the off-peak margin in 2020/2023/2024 without taking it out of the
  margin in 2019/2021/2022 — the same arithmetic in reverse of the miso-224 finding that any gas re-pricing below ~$30
  takes coal's energy wholesale.
- **It is not evidence against the gas convention.** The ruled form (hub + measured variable transport) is a
  convention with a forward analogue; what the census adds is its sign by year: it lowers CC fuel only where the
  print premium exceeds the plant's measured variable transport (2023–2025), and raises it where the print premium is
  smaller than the transport (2019–2022). Its C1 behaviour in a full-span LP is untested (the 2023 screen passed C1 and
  died on a 0.30× conversion line that is not a rubric criterion).
- **It does not move any cell.** `gas_marginal_commodity_pricing` and `gas_variable_transport` stay `O` with this
  evidence; `offer_curve_by_group` stays `K` with a note that the coal econ bands are not identifiable from the pooled
  IMM share under the one-value rule.
- **Not swept.** No m was solved; no m is proposed from the residuals. The hump (m = 0.80) is reported as the curve's
  maximum, which is a different statistic from the one the owner ruled.

## 4. Owner decision (cards in the session's final message; recorded here for the record)

- **(A) Record and move on.** Keeper unchanged; C3a 2020 stays a known miss (FINDING-miso296 §8 option C). The chain
  picks the next lane from the three open full-span failures, all routed misses (C1 ST_GAS 2019, C3b 2021) or
  without an admissible identified lever (C3a 2020).
- **(B) Re-identify m at the census maximum (m = 0.80) and solve the joint arm.** A new ex-ante rule the owner would
  set now ("the m that maximizes the pooled coal marginal share"); PRECOMMIT §5 kill rules unchanged. Phase-0
  prediction, stated against it: K-1 is at risk in 2019 (COAL_PRB +6.40 TWh with +3 to +7 TWh of static-converted
  coal coming), K-4 should pass in all four low-gas years, and C3a 2021/2022/2025 move further negative.
- **(C) Solve the owner-ruled gas form ALONE over the full span (7 shards, no coal change).** The convention
  question on structure (rule 1): the census says it does not collapse coal at zero LP and that it moves 2023/2024
  toward actual and 2019/2020 away. Its named cost is the early-year sign.
- **(D) Something else** (the owner names it).

## 5. Where MISO stands

Keeper unchanged. Train 2023–2025 CALIBRATED (C3c ledgered). Full span NOT-YET on C1 ST_GAS 2019 (routed), C3a 2020
(+11.6 %) and C3b 2021 (0.201). **No frontier** (owner, 2026-09-28: routed misses are failures).

## Retrievability

No solve. The probe, its JSON, the keeper readout JSON, the G-DRIFT record, the (unlaunched) PRECOMMIT and this record
are in this PR. The pre-stated rules are verifiable at commit 025012a7 (PRECOMMIT §3.1 with the tables still
placeholders), pushed before `_pooled` existed in the JSON. Disclosed: that commit was made after the 2020 slice of the
scan (both legs, all 15 grid points) had been read, and before any other year or the pool existed; the 2020 slice alone
reaches the IMM (0.40 at m = 0.70), so it did not foretell the failure.
