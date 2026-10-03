# PRECOMMIT — closeout-PJM-cc22 phase 0: the 2022 C1 CC_REGULAR over-run (ZERO LP)

Lane: closeout-PJM-cc22 (branch `claude/closeout-pjm-cc22`, cut from `4fcad76b`). Chartered by the backcast close-out
desk on **owner ruling R-56** (2026-10-03, verbatim): *"Leave open, go to CC_REGULAR 2022."* Keeper under test:
`2026-10-03-closeout-pjm-nuc-keeper` (bundle `results/calibration/closeout_pjm_nuc_full_span`). COAL_BIT 2019–21 stays
OPEN and unsigned; it is not touched. Measured nuclear rows (R-35/R-52) are not reverted (rule 14).

**Disclosure of order.** The pass bars below are the charter's, fixed by the desk before this session started. The
decomposition (§1 of the FINDING) and the reach screen were computed **before** this file was written. Nothing in
this file was chosen after seeing a candidate's reach: the screen standard is the closeout-PJM-decommit convention
(static re-clear on the keeper's own P1 dispatch, CC replacement share `s` ∈ [0.35, 0.50] from the keeper's measured
displacement, PJM-NEXT-16 / RESULT-closeout-pjm-nuc R2).

## 0. Rule 28 check (PJM.js cells, §5.3 queue)

| Channel | Cell | Status here |
|---|---|---|
| `cc_mustrun_per_plant` (CC committed floor, POOLED 2023–25 window) | K | the incumbent floor |
| `mustrun_online_frac_per_year` (window at the solve year's own CEMS share) | **U** | candidate (A), never armed in PJM |
| `pjm_gas_commitment_bridge` / `gas_commitment_bridge` / `cc_mustrun_conduct_window` | R | not re-tested |
| `partial_plant_exit_carry` (Morgantown/Waukegan 2022 boundary, NEXT-16) | K (W0) | closed: both plants are in the 2022 LP fleet |
| `zonal_gas_basis` hub series (Dominion Z5/M3) | K, DATA-BLOCKED | not re-tested |
| `internal_congestion_split` | G | not re-tested |
| CT_PEAKER 2021 frontier (out-of-merit CT conduct) | R-36 | not a lever |
| `coal_passthrough_sigmoids` (gas_mid R, pjm-h7), `pjm_replacement_cost_fuel` (R) | K / R | not re-tested |
| `nuclear_unit_availability` (the R-35 rows' 1.0 clip) | U | candidate (B), sized only |
| Elliott (C3a/C3b/C3c 2022) | R-26 data-limited | read only |

## 1. Questions (charter)

Q1 Elliott week? Q2 gas-price months? Q3 capability / availability (EIA-860, CAMPD outages)? Q4 the measured-nuclear
displacement itself? Q5 which lever, with reach?

## 2. Bars (charter, verbatim in substance)

- **B1** 2022 C1 CC_REGULAR back inside ±8 TWh: static CC reach ≤ **−0.96 TWh** (from +8.96) at `s` = 0.50 *and* 0.35.
- **B2** no C1 PASS→FAIL in any other year (static class moves against each year's keeper margin).
- **B3** C3a / C3b 2022 not worse beyond the band (R-26 holds them data-limited; a candidate must not move them
  materially).
- **B4** admissibility: rules 1, 13, 14, 17, 19, 24, 25. No haircut, adder, revert, or fitted value; a measured
  input at its own grain; PJM-scoped, default off, `--no-` arm if a new field.

**Decision.** CHARTER a solve only if one candidate (or a rule-19-compatible pair) clears B1–B4 statically. Otherwise
NOT CHARTERED, with the reach table.
