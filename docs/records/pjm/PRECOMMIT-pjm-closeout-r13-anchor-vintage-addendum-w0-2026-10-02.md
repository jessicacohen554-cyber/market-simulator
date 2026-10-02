# PRECOMMIT addendum — R-13 `gas_offer_margin_anchor_vintage`: control, G-DRIFT and launch (post-W0)

Addendum to `PRECOMMIT-pjm-closeout-r13-anchor-vintage-2026-10-02.md` (merged in #7031). It is written before any arm solve. **The gates and readings of the parent §5 are unchanged.** The desk released the lane on 2026-10-02 after W0's PJM keeper merged (#7069 @ `0d5f3e32`).

## Control (parent §4, now resolved)

- **Keeper:** `2026-10-02-w0-pjm-fix2`, bundle `results/calibration/w0_pjm_span`. It has mixed-SHA legs: 2019–2023 at `25da60220c506a54c7a1fb4ba86c9a70a5be7887`, 2024–2025 at `ce8820dd73feec31181f2e215251ec6dcb9a3b4f`. The inert proof is `docs/records/governance/closeout-2026-10/W0-phase3/KEPT-LEG-INERT-PROOF-2026-10-02.md`.
- **Rule 29(b):** no control solve. The keeper's committed bundle is the control. The arm replays its recipe with the one `--set`.

## G-DRIFT: `25da6022` / `ce8820dd` → `0d5f3e32`, backcast solve path

The `ce8820dd` → `25da6022` link is already closed by the inert proof above. Every commit `25da6022..0d5f3e32` that touches `src/`, `run_calibration_full.py`, `replay_keeper.py` or `scripts/lib/replay_recipe.py`:

| commit | hunk | verdict for PJM |
|---|---|---|
| 2f69901a | `backcast_config.caiso_ra_min_load_frac` 0.26 → 0.570 for CAISO only | INERT: non-CAISO still records 0.40, and every reader is behind `caiso_ra_mustoffer and iso == "CAISO"` |
| 106d6bb7 | `coal_fuel_inventory` multi-month budget branch | INERT: `coal_fuel_inventory` and the monthly pile are False in every PJM keeper year |
| c463d503, 6c492459 | `interchange/spec.py` `forward_heat_rate` (forecast fallback) and SOCO_FPL `hr_by_year`; `neighbor_price` fallback 3 | INERT: SOCO seams only, and the forward fallback is forecast-only |
| 625420ff | `spp_mmu_offer_repair` (arrays, runner, export, models, scenarios) | INERT: SPP-only gate (`spp_mmu_offer_unavailability` False for PJM). The new field defaults off |
| b84878f3 | `run_calibration_full` classes the `emergency_band` fuel | INERT: there are no such rows in PJM |
| 15c66030, c327931e | `replay_recipe` guard: rule-26 inert recorded fields and fields registered after the solve | INERT for LP inputs: a replay-acceptance check only |
| 9402af20, 65d5f902 | `data/stb_ep724.py` new reader | INERT: not on the solve path |

**No LIVE hunk, so no control solve.** The arm pins the full SHA of this branch's head. That is `0d5f3e32` plus records only.

## Phase 0 re-check

The anchor delta (parent §3) depends only on `_gas_series` and the keeper HH. Neither changed under W0 (`gas_price_override` is identical in every `w0_pjm_span/run_config_<Y>.json`, 2.57 … 3.52, and `gas_offer_margin_anchor` = 3.3483 frozen). §3's table stands.

## Launch

Seven shards, one per year 2019–2025 (rule 36), each made by `scripts/shard_prompt.py --iso PJM --all-years --bundle results/calibration/w0_pjm_span --set gas_offer_margin_anchor_vintage=true --lane closeout-pjm-r13`. The parent composes them with `_miso260_compose_span.py`, then runs `calibration_verdict.py`, `legitimacy_diagnostics.py`, and the S4a/S4b probe against the keeper's `unit_marginal_<Y>`.
