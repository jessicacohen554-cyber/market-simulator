# G2 — Posture commitment family documented in the spec

Session 2026-10-03, lane `claude/audit-rulings-2026-10`. Owner ruling
(2026-10-03): document the posture commitment family in the spec beside the
three P1-native bridges, as a default-off fourth family; the code stays.

## What was written

1. `model-methodology-spec.md` §1.6, directly after the "P1-native commitment
   bridges" paragraph: new subsection **"Posture commitment family (default
   off)"** (two paragraphs). Covers the LP object (continuous `U[p,t]` online and
   `SU[p,t]` start-up columns pooled per plant / zone × gas-class; headroom,
   measured min-load, cyclic start-up counting, SPP min-up / min-down rows with
   the availability allowance; the pergen re-anchor variant for MISO/PJM/CAISO),
   that it is a clustered-UC LP relaxation and not a floor (no D-2 id, no D-4
   window, no ablation twin, forces no exogenous energy), its parameters and
   measured sources, rule-19 mutual exclusivity with the gas bridges, defaults,
   which keepers arm it (none), and its mechanism-matrix rows.
2. `docs/codebase/03-capacity-and-commitment.md` "P1-native commitment
   mechanisms": the existing posture paragraph rewritten to one consistent
   paragraph linking the spec subsection; corrected the claim that all three
   fields build through `_build_posture_energy_rows` (MISO rides
   `_build_reserve_rows_pergen`, `reserve_rows.py:562`).

## What was verified (file:line)

- Fields and defaults: `ercot_commitment_posture` `False`
  (`src/market_sim/config/scenarios.py:14773`), `ercot_commitment_posture_min_load_frac`
  0.574 (`:14780`), `miso_commitment_posture` `False` (`:11008`),
  `spp_commitment_posture` `False` (`:9457`); siblings `pjm_commitment_posture`
  (`:11880`) and `caiso_commitment_posture` (`:11234`) `False`.
- Builder: `src/market_sim/model/lp/rows.py::_build_posture_energy_rows`
  (`:1214`, docstring `:1224-1262` — headroom / min-load / startup / min-up /
  min-down families); pergen variant `src/market_sim/model/lp/reserve_rows.py:562`;
  columns `src/market_sim/model/lp/layout.py:70` (`n_posture`); SU cost
  `src/market_sim/model/lp/costs.py:24,64-66`.
- Spec functions: `src/market_sim/model/reserves/spec.py::_posture_pool_params`
  (`:1178`, fast-start gate), `ercot_commitment_posture_spec` (`:1305`),
  `_standalone_posture_pools` (`:1350`), `spp_commitment_posture_spec` (`:1427`).
- Pipeline: `src/market_sim/pipeline/kwargs.py::apply_ercot_commitment_posture`
  (`:625`), `apply_spp_commitment_posture` (`:677`), merged at
  `src/market_sim/pipeline/year.py:314`; `src/market_sim/pipeline/solve.py::zero_posture_markup`
  (`:321`, SPP-gated, called `:656`).
- Constants: `SPP_GAS_BRIDGE_MIN_LOAD_FRAC["gas_cc"]` 0.209
  (`src/market_sim/config/constants.py:444`), `SPP_GAS_BRIDGE_MIN_RUN_HOURS["gas_cc"]`
  15 (`:445`), `SPP_POSTURE_MIN_DOWN_HOURS` 8.0 (`:488`), `MIN_STABLE_PCT_PHYSICAL`
  (`:580`); start-up tables `src/market_sim/model/commitment.py:48`
  (`COMMITMENT_PARAMS_BY_FUEL`), `src/market_sim/data/fleet/eia860.py:4348`
  (`BIN_STARTUP_COST_PER_MW`).
- Mutual exclusivity (rule 19): `scenarios.py:23809-23820` (SPP posture +
  bridge refused), `:23839-23846` (PJM), `:23927-23933` (CAISO posture +
  online-scoped); ERCOT disjointness is declared in the field docstring
  (`:14770-14772`), no validator.
- Keepers: every `results/calibration/*/run_config.json` (nine bundles) carries
  `ercot_/miso_/spp_/pjm_/caiso_commitment_posture: false`.
- Matrix: row `spp_commitment_posture`
  (`docs/codebase-site/data/mechanism-matrix.js:1759`; SPP cell `R`,
  `mechanism-matrix/SPP.js:148`); ERCOT/MISO/PJM legs on row
  `online_capacity_envelope` (`:1642-1644`; `ERCOT.js:73` `R`, `MISO.js:73` `R`).

## Proposed CLAUDE.md sentence ("Dispatch and commitment", after the bridges sentence)

A default-off fourth family, the commitment posture (`ercot_commitment_posture`,
`miso_commitment_posture`, `spp_commitment_posture`), is an in-LP clustered-UC
relaxation (`model/lp/rows.py::_build_posture_energy_rows`: online `U`/start-up
`SU` columns, measured min-load, start-up charge) — not a floor, never stacked on
a gas bridge (rule 19).

Not edited: `CLAUDE.md`, `src/`, `frontend/`, `results/`,
`docs/governance/rule-history.md`.
