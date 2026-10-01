# PRECOMMIT — PJM-NEXT-14: a 2020 keeper replay to read the LP's own low-end marginal units

**Keeper:** `2026-09-28-pjm-next8-exitfix` (bundle `results/calibration/pjmnext8_xf_span`). **No arm.** This is a byte-faithful keeper replay of ONE year, used only for diagnosis. It is never registered and never a promotion candidate: it IS the keeper.

## Why a replay, and why 2020

- Card 1 asks which units price the keeper's low-end hours, and at what offer. The committed payload's per-plant hourly MW (1 % CF bytes) cannot answer it at zero LP. A payload-based detector (`scripts/probes/_pjmnext14_lowend_marginal.py`) names CHP committed rungs as "marginal" in 30 % of zone-hours, because host-steam CHP holds partial load in every hour, and it matches a bid within $1 in only 50 % of zone-hours. It omits P1's startup-amortization markup, which needs P0.
- Every solve writes `hourly/unit_hourly_<y>.parquet`: per LP unit-hour `mw`, `cap_mw`, the P1 offer `mc` the LP installed, and HiGHS `red_cost`. An interior unit with zero reduced cost is the LP's own marginal unit. `scripts/probes/_pjmnext14_lowend_lp.py` reads it, smoke-tested on a synthetic frame built from the 2020 `fleet_only` dump.
- 2020 has the largest C3a miss (+15.9 %) and 45 % of its hours below 6.5 × delivered gas.

## Solve

`python3 scripts/replay_keeper.py results/calibration/pjmnext8_xf_span --years 2020 --out-dir results/calibration/pjmnext14_replay_2020 --note "PJM-NEXT-14 card 1 diagnostic replay"`, one shard (rule 32/36), pinned to this commit.

- **G-DRIFT (rule 29(b)).** No control solve. The keeper's committed `hourly/class_hourly_2020.parquet` is the control, and it doubles as a reproducibility check: every class's P1 TWh must reproduce the keeper to ≤ 0.05 TWh (rule 36: the keeper's legs were year-isolated shards). A larger move is reported at full magnitude and makes the diagnostic conditional on HEAD code, not the keeper's.

## Predictions (fixed before the replay; `low_delivered` = actual RT < 6.5 × HH + PJM basis)

| # | prediction | falsified if |
|---|---|---|
| P1 | The keeper almost never offers a marginal unit below an efficient CC's delivered fuel cost: the share of `low_delivered` zone-hour weight whose marginal offer implies < 6.5 MMBtu/MWh at delivered gas is ≤ 0.05. | > 0.05 |
| P2 | Gas CCs (CC_REGULAR + CC_CHP) plus coal (COAL_*) are ≥ 60 % of the `low_delivered` marginal weight. | < 60 % |
| P3 | Marginal CCs on production-area supply (tiers `imm_production` + `appalachian_receipt`) offer at a median implied HR ≥ 7.5 against IMM **production** gas (i.e. above an efficient CC at production spot). | median < 7.5 |
| P4 | Zone-hours with no interior zero-reduced-cost thermal unit (storage, imports or a transmission limit sets the price) are ≤ 20 % of `low_delivered` weight. | > 20 % |

**What each outcome means:**
- **P2 fails because coal dominates** (coal > 50 % of `low_delivered` marginal weight): the low-end object is the coal offer level (the mid-curve LONG_RUN floor), not gas supply.
- **P3 fails** (production-area CCs already offer near production cost): the supply-point route is closed.
- **P4 fails:** the floor is a network or storage object, not an offer-level one.

## Retrievability

The shard pushes its bundle to its own branch through a `.gitignore` negation and a plain `git add` (rule 34). Commit 1 is the probe JSON plus the slim bundle. Commit 2 is `dispatch/` + `hourly/unit_hourly_2020.parquet`, best effort. It is a keeper replay, so a promotion never needs it.
