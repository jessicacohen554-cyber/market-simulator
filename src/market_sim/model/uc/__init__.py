"""The MILP unit-commitment stage (``ScenarioConfig.unit_commitment_milp``).

P0 -> [UC] -> P1 (CLAUDE.md "Dispatch and commitment", owner ruling R2
2026-10-03; design record
``docs/records/governance/uc-milp-2026-10/DESIGN-uc-milp-engine-2026-10-03.md``).
A rolling-horizon MILP over the year CHOOSES the commitment of the slow-start
clusters and enters the scored P1 LP only as per-unit-hour bounds (D-2 id
``MECH_UC_SCHEDULE``). The MILP never prices (rule 4): P1's duals stay THE
prices.

Modules:

* :mod:`params` — the cluster struct-of-arrays (rule 6) from the frozen
  ``uc-params`` derive and the published class tables;
* :mod:`window` — one rolling window: the production LP blocks sliced to the
  window (``model/lp`` untouched), the integer columns and the commitment rows
  added on the HiGHS handle, the boundary edits;
* :mod:`solve` — the HiGHS MILP call (integrality, gap, time limit, warm start);
* :mod:`schedule` — stitching the kept hours into the year schedule, the
  per-month checkpoint and the ``uc_schedule`` sidecar frame;
* :mod:`uplift` — the zero-LP post-P1 make-whole sidecar.

The pipeline glue (the ``p1_fleet_prep`` hook and the markup zeroing) is
:mod:`market_sim.pipeline.uc`.
"""
