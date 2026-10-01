# PRECOMMIT — PJM-NEXT-2 card 3: TMI-1 (8011) dispatches 0 MWh in 2019

Session PJM-NEXT-2, 2026-09-25. Keeper `2026-09-25-pjm-next-c1`. Written and pushed **before the solve**. One gated
field, `nuclear_dormancy_defers_to_vintage_exit`, zero free parameters.

## Trace (zero LP, fleet-only rebuild of the keeper recipe, 2019)

`mid_vintage_exit_carry` injects `8011_1` (802.8 MW, PJM_Central_PA, `mid_vintage_exit_unit=True`, retirement
2019-09) — correct. Its availability is then **0.0 in every hour**: `data/fleet/arrays.py::_nuclear_monthly`'s
dormant-nuclear block zeroes any nuclear unit with `year < NUCLEAR_DORMANT_UNTIL[plant]` (8011 → 2027). That table
was written for the Crane/TMI-1 *restart* (EIA-860 2025 lists the dormant unit OP) and has no dormancy START, so it
also erases the months TMI-1 genuinely ran (Jan – 20 Sep 2019). Rule-19 collision between two mechanisms on one
unit. Effect on the keeper: model nuclear 2019 271.98 vs 277.92 TWh measured (−5.9).

No double count: `scripts/data/derive_nuclear_monthly_cf.py` excludes the dormant plant's generation **and**
capacity, so the 2019 fleet CF describes the other reactors only.

## Arm

Armed, a unit flagged `mid_vintage_exit_unit` is exempt from the dormancy zeroing; its exit month's retirement mask
still removes it afterwards. Census: **only `8011_1` moves** (availability and its flat must-run floor), 5.005 TWh of
capacity-hours through end-September 2019 (month-grain exit mask; the unit stopped on the 20th). TMI is injected
only in 2019, so 2020-2025 are inert by construction and are carried from the keeper (rule 34(c) exception stated).

## Prediction

Model nuclear 2019 rises ≈ +5 TWh toward 277.9; the LP backs down marginal coal/gas by about the same energy.
Scored classes move by small amounts; direction on COAL_BIT 2019: down.

## Execution

One shard, 2019: `replay_keeper.py results/calibration/pjmnext_c1_span --years 2019
--set nuclear_dormancy_defers_to_vintage_exit=true`, pinned SHA, bundle to `claude/pjmnext2-c3-2019`. Hard stops as
card 1 §7 with (b) outage extract sha `312a11b8` and (d) the arm flag true.
