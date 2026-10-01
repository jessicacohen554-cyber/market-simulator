# PJM M-3 gas-CC commitment bridge — session status + handoff (2026-07-21)

## ⚠️ Read first: this session ran on a STALE clone

This session's container was provisioned with the repo at `066fb98` — **1572
commits behind real `main` (`50e5ac9b4`)**. The session-start `git fetch origin
main` timed out, and every subsequent sync attempt (full and `--depth=1`) fails
through the agent proxy with `fatal: early EOF / unexpected disconnect while
reading sideband packet`; `git push` 413s; the raw Git Data API write path is
403-blocked. So this session could **not** sync to real main and could not push
large-file edits. Everything below was built against the stale base.

**Do NOT `git apply docs/handoffs/pjm-m3-gas-bridge.patch` directly** — it was
generated against `066fb98` and will not apply on real main (the
orchestrator-unification refactor, PR #2753, rewrote the P0→P1 seam files it
touches). Use it as a **reference implementation**, not an applyable patch.

## What's reusable (base-independent)

### 1. Committed-state evidence + `min_load_frac` — VALID on real main
`scripts/derive_pjm_gas_bridge_params.py` (in the reference patch) derives, from
the PJM DataMiner2 `energy_market_offers` corpus using the SAME frozen
`derive_pjm_offer_surface` physics segmentation (both exist on real main):

| quantity | value |
|---|---|
| **`pjm_gas_bridge_min_load_frac`** (cap-weighted p50 `avg_ecomin/avg_ecomax`, CC segment) | **0.564** |
| CC-like units / total EcoMax | 302 / 76.8 GW (matches PJM gas-CC fleet) |
| CC unit-hours with `avg_ecomin>0`, overnight h0–6 / midday h12–18 | 0.968 / 0.968 |

Cross-season 2024 (Jan/Apr/Jul/Oct). Committed-state evidence is confirmed:
PJM CC units carry an LSL floor through the overnight hours (0.968), the
market-side counterpart of the model's D-1p flat-overnight residual. `0.564`
sits physically alongside the ERCOT committed-CC p50 (`0.574`). The params JSON
is pushed (`data/raw/_validation-source/pjm_gas_bridge_params.json`).

### 2. Mechanism design — M-3 does NOT yet exist on real main
Confirmed via API: `pjm_gas_commitment_bridge` / `build_pjm_gas_bridge_p1_prep`
/ `MECH_PJM_GAS_COMMITMENT_BRIDGE` are absent from real-main scenarios.py,
commitment.py, floor_mechanisms.py. So M-3 is worth implementing. The design
(verified by 8 unit tests + 265 touched-area tests on the stale base, whose
shared internals — `caiso_ra_mustoffer_min_gen`, `_bridge_floored_fleet`,
`find_runs` — are unchanged on real main):

- **config/scenarios.py** (after `ercot_gas_bridge_da_horizon`):
  `pjm_gas_commitment_bridge: bool = False`, `pjm_gas_bridge_min_load_frac:
  float = 0.564`, `pjm_gas_bridge_startup: bool = True`,
  `pjm_gas_bridge_da_horizon: bool = True` + `TIER_TAGS` (1/2/1/1).
- **pipeline/commitment.py**: `_pjm_gas_bridge_floor` +
  `build_pjm_gas_bridge_p1_prep` — mirror `_ercot_gas_bridge_floor` /
  `build_ercot_gas_bridge_p1_prep` exactly, reading the `pjm_*` config,
  `fuel_types=("gas_cc",)`, tagging `MECH_PJM_GAS_COMMITMENT_BRIDGE`, and
  raising on `pjm_reserve_commitment_scoped` (rule 19, both replace the P1
  fleet). **Re-locate against real main's refactored file** — the ERCOT bridge
  builder is the anchor.
- **runner.py + scripts/run_calibration.py**: build the prep at the P0→P1 seam
  and add to the `p1_fleet_prep` `or` chain
  (`… or pjm_gas_bridge_prep or pjm_fleet_prep`). **Note:** real main's PR #2753
  moved this seam into `pipeline/solve.py` / `pipeline/commitment.py` — verify
  where the ERCOT/CAISO preps are wired on real main and match that.
- **data/floor_mechanisms.py**: `MECH_PJM_GAS_COMMITMENT_BRIDGE = 18` (next free
  id — CHECK real main's max id) + `MECH_NAMES` + `MECH_ABLATION_FIELDS`
  (`{"pjm_gas_commitment_bridge": False}`). Separate id per the
  `MECH_ST_GAS_MUSTRUN_PER_PLANT` precedent.
- **scripts/legitimacy_diagnostics.py**: D-4 window
  `(MECH_PJM_GAS_COMMITMENT_BRIDGE, "CC_REGULAR"): (0, 24)` (economic
  self-windowing).
- **tests/test_pjm_gas_commitment_bridge.py**: 8-case suite (in the reference
  patch) — gate/ISO guards, overnight floor+tag, startup/DA-horizon legs,
  CT-never-floored, rule-19 raise, registry.

Full rationale: the reference patch's embedded
`docs/handoffs/pjm-m3-gas-bridge-evidence-2026-07.md`.

## Probe (deferred, per owner)
Baseline = the real-main keeper `2026-07-19-pjm-gasshape-interpfix` (pjm-115).
A/B: `replay_keeper.py <keeper-bundle> --set pjm_gas_commitment_bridge=true
--out-dir … --note …` across 2023–2025 (rule 16). The keeper's gitignored data
corpora (pjm-da-virtuals, energy-offers, …) must be regenerated first.

## Recommendation
Do M-3 (and the ready-to-apply DAM edits in
`docs/handoffs/pjm-dam-availability-wiring-2026-07.md`) from a **fresh session
with a working clone of real main** — this session cannot sync or push. The
evidence (`0.564`, overnight 0.968) and the mechanism recipe above make M-3 a
~1-hour implement-and-test once on real main.
