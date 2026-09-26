# PRECOMMIT addendum — PJM-NEXT-2 JOINT arm (cards 1+2+3), the registrable candidate

Session PJM-NEXT-2, 2026-09-25. Written and pushed before the solve.

**Why a joint arm.** The keeper bundle on `main` (`pjmnext_c1_span`) carries no `dispatch/<y>_P1.parquet`, so a
single-flag arm solved only on the years it reaches (card 2: 2022-2025; card 3: 2019) cannot be composed with keeper
years into a registrable 7-year bundle (registration reads every year's dispatch). The registrable, promotable
candidate is therefore ONE configuration solved on EVERY year (rules 16 / 34(c) / 36): the keeper recipe plus
`unit_outage_membership_repair`, `pjm_zonal_gas_basis_skip_923_priced` and `nuclear_dormancy_defers_to_vintage_exit`.
Each is a zero-DOF structural repair justified on its own PRECOMMIT (card 1 / card 2 / card 3) — none was selected on
a residual (rule 1), and all three were committed before any solve. The single-flag arms already launched are the
attribution record, not candidates.

**Interactions (zero LP).** The three touch disjoint objects: card 1 availability rows of 21 never-scanned
facilities (+ shared floor-limb re-apportionment), card 2 gas fuel cells of print-priced rows 2022-2025, card 3 the
single row `8011_1` in 2019. No row is touched by more than one card except via LP re-dispatch.

**Execution.** Seven shards, one per year 2019-2025, `replay_keeper.py results/calibration/pjmnext_c1_span
--years <y> --set unit_outage_membership_repair=true --set pjm_zonal_gas_basis_skip_923_priced=true
--set nuclear_dormancy_defers_to_vintage_exit=true`, bundles `pjmnext2_joint_<y>` on `claude/pjmnext2-joint-<y>`.
Hard stops as card 1 §7 (outage extract = the `-memberrepair-` companion, sha `c6883c51…`) with all three flags
true. The parent composes the seven legs, rebuilds the benchmark, attests (DOF ledger carried, zero entries added),
scores against the keeper on the same benchmark, registers, and asks the promotion question.
