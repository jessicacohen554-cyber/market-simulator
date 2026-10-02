# RESULT — PJM close-out L2 (incremental-HR pricing of CC econ tranches): CLOSED at phase 0

Lane `closeout-PJM`, 2026-10-02. **Zero LP.** **Desk ruling (b): close L2 at phase 0, record the finding, no field lands on main.** The pre-registered S3 was **not** rewritten after the number was seen (rule 29c).

Records:
- PRECOMMITs: `PRECOMMIT-pjm-closeout-l2-incremental-hr-2026-10-02.md` (with the desk REPLACE ruling) and its build addendum `…-addendum-build-2026-10-02.md` (on branch `claude/closeout-pjm-l2`).
- Prediction: `results/phase0/pjm/_pjmco_l2_phase0_prediction.json`.

## What was built (provenance only; not merged)

Branch `claude/closeout-pjm-l2` @ `d8cf825a90939b5c73da77d98d938e4dc4ae831a`:
- `scripts/data/derive_pjm_cc_incremental_hr.py` and `data/raw/_validation-source/pjm_cc_incremental_hr.csv`. The artifact holds 422 plant-years and reproduces census 0d to 5e-7.
- Field `pjm_cc_econ_incremental_hr` (default off), with its `offer_surfaces` branch and 9 tests. Fast lane: 11,347 passed, 0 failed.
- Matrix row plus a cell in every shard.

Per the desk ruling, **none of this lands on main**. The branch is transport, recorded here by SHA.

## The finding

Under the build spec (§2), the econ bid is `max(own-cost × HR_incr/HR_committed, committed-row mc)`. The second term is PJM's monotone-offer rule: energy offer segments may not decrease.

The measured incremental HR (6.77–6.95 MMBtu/MWh, cap-weighted 2019–25) sits **below** the committed rung's average HR including no-load (7.26–7.35). So the monotone term binds almost everywhere, and **incremental-HR pricing collapses to committed-rung pricing.**

| year | keeper econ HR | L2 bid HR | incremental HR | committed HR | covered | median-row Δmc ($/MWh) |
|---|---|---|---|---|---|---|
| 2019 | 7.517 | 7.527 | 6.769 | 7.317 | 96.5 % | −0.16 |
| 2020 | 8.060 | 7.594 | 6.944 | 7.319 | 96.3 % | −0.75 |
| 2021 | 7.931 | 7.563 | 6.881 | 7.345 | 90.3 % | −1.00 |
| 2022 | 7.894 | 7.529 | 6.884 | 7.325 | 92.9 % | **+0.01** |
| 2023 | 8.091 | 7.503 | 6.951 | 7.279 | 87.6 % | −0.54 |
| 2024 | 8.838 | 7.476 | 6.903 | 7.262 | 91.0 % | −0.90 |
| 2025 | 8.826 | 7.547 | 6.924 | 7.335 | 93.8 % | −2.11 |

What L2 does:
- It flattens the **upper** econ ladder: the cap-weighted bid HR falls 0.4–1.4 in 2020–25.
- It **raises** the low econ slices that the keeper's shape form prices below the committed rung. Cap-weighted Δmc rises in 2019, 2020, 2021 and 2023.
- It cannot lower the low-end **floor**, which is what C3a 2020 needs. That floor is set at or below the committed rung, and the monotone rule forbids pricing below it. Census 0d already noted that the lowest econ slice sits at incremental cost.
- S3 ("econ mc falls in every year, median") is predicted to fail in 2022.

**Conclusion:** incremental-HR pricing of CC econ tranches is **not the C3a 2020 lever** in an LP that folds no-load into the committed rung under PJM's monotone-offer rule. A real floor effect would need no-load moved out of the committed rung, meaning a separate no-load or uplift construct. That is a commitment-cost representation change, not an offer-curve one, and it is out of scope for this lane.

## Matrix

There is no new row on main, because no field landed. The finding is recorded in the PJM cell of `pjm_midcurve_belt`, which stays K: the CC_LIKE shape form L2 would have replaced remains the keeper's construction.
