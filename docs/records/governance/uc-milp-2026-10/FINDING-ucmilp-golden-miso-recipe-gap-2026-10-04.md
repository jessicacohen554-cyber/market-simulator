# FINDING — the MISO golden FAIL under uc-milp UC-1 is a golden-harness recipe gap, not the UC engine and not main drift

Lane UC-1-FINISH (`session_01CghV9pMqkD5TDmYicDuMCx`, Fable), 2026-10-04, chartered by
UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`). Method: the NYISO record
(`FINDING-ucmilp-golden-nyiso-main-drift-2026-10-04.md` §2, Appendix A), zero LP.
The charter named this file `FINDING-ucmilp-golden-miso-main-drift-<date>.md`; the
evidence shows no main drift, so the name states what was found.

## 1. Facts

| Item | Value |
|---|---|
| Keeper | `2026-10-03-closeout-miso-nuc-r`, bundle `results/calibration/closeout_miso_nuc_span`, 2019–2025, seven single-year legs |
| Keeper basis | `f98c456401918eba82c338676e303a90004bb94c` for all seven legs (`run_config_<y>.json`) |
| Golden shard | `ucmilp-golden-miso`, off-gate replay at `ec758d64`; report on `claude/ucmilp-golden-miso` @ `61b30834` |
| Golden result | 2019–2021 exact; 2023–2025 FAIL in every file (price max \|Δ\| 40.4 / 305.4 / 35.6 $/MWh); 2022 cut off at the 2-h limit |
| Golden's own lead | `reserve_family_2023–2025`: 35,040 keeper rows vs 26,280 golden rows — the golden lacks the `miso_rbdc_regspin` family |
| Keeper recipe | `meta.json` carries ONE base recipe (the 2019 leg's) plus a `config_partition_overrides` block (`composite-per-year-recipe/v1`, `stamp_config_partition.py`). For 2023, 2024 and 2025 it adds `miso_measured_reserve_requirements = true` and `miso_reserve_online_gated = true`; every other year adds only the year-driven `gas_offer_margin_anchor` |
| Harness | `scripts/capture_keeper_goldens.py::capture_one` builds kwargs from `meta.json` alone (`build_solve_kwargs`) and never reads `config_partition_overrides`. `replay_keeper.enforce_single_recipe_partition` is the consumer and it is not called. The golden fidelity check compares against the top-level `run_config.json` (the 2019 leg), so the two missing flags did not show as drift |

## 2. Zero-LP reproduction

The keeper recipe of each year is replayed through `replay_keeper.build_kwargs` →
`run_calibration_full.solve_and_persist`, with `run_calibration.run_energy_solve`
replaced by a spy that records every input (`fleet`, `FleetArrays`, `demand`,
`mc_base`, every keyword, `dispatch_kwargs`, the config) and aborts before any LP.
"Faithful" applies `enforce_single_recipe_partition` and `flipped_default_overlay`
for the one year, as `replay_keeper.py --years <y>` does. "Golden-style" skips both,
as `capture_keeper_goldens.py` does. One `data/clean` (MISO solve profile,
regenerated at the branch) serves every tree. Every comparison is at
atol = rtol = 0 (`np.array_equal`; sparse by `(A != B).nnz`), ignoring only
checkout-absolute path strings and the branch's nine new config fields at their
defaults.

| Tree | Checkout |
|---|---|
| basis | sparse worktree at `f98c4564` |
| main-without-UC | sparse worktree at `e8570532` (the golden's merge-base); repeated at `d62ae1a7` after the rebase |
| branch | `6d47c762` (= `ec758d64` + two FINDING-only commits); repeated at the rebased tip |

| Comparison, faithful recipe | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| main-without-UC vs branch | identical | identical | identical | identical | identical | identical | identical |
| basis vs branch | identical¹ | identical¹ | identical¹ | identical¹ | identical¹ | identical¹ | identical¹ |

¹ Arrays, keywords and fleet identical. The only difference is five config fields
present at HEAD and absent at the basis, all at their default-off values
(`caiso_dsw_daytime_lateevening_unprinted_arm`, `nwpp_coi_pnw_delivery_basis`,
`nwpp_seam_in_service_vintage`, `nwpp_served_schedule_zonal_attribution`,
`zonal_loss_demand_reconciliation`).

| Comparison on the branch | 2019–2022 | 2023, 2024, 2025 |
|---|---|---|
| golden-style vs faithful recipe | identical | config: `miso_measured_reserve_requirements` False vs True, `miso_reserve_online_gated` False vs True; dispatch kwargs: reserve classes 3 vs 4 (`reserve_requirement` (3, 8760) vs (4, 8760)), ORDC steps 12 vs 14, per-gen reserve pools 30 vs 60, plus the online-gating arrays present only in the faithful recipe |

The fourth reserve class in the faithful recipe is the `miso_rbdc_regspin` family
(capture log: "requirement 1315 MW at h0 (measured hourly South reservation)"),
which is exactly the family the golden lacks.

## 3. G-OFF MISO verdict

**PASS (engine-inert), by zero-LP input identity, all seven years.** The branch
and main-without-UC give `run_energy_solve` identical inputs in every year, and
the only code inside `run_energy_solve` that differs is the
`if config.unit_commitment_milp:` hunk, which does not run off-gate. The keeper
basis gives the same inputs as well, so the faithful recipe reproduces the keeper's
LP inputs at HEAD. The 2023–2025 golden FAIL is caused by the golden harness
solving a different recipe: it dropped the per-year reserve overlay. 2022 is
covered by the same identity (no re-solve needed: its golden-style and faithful
inputs are identical, and so are basis, main and branch). Not an engine leak, so
UC-2-SPP is unaffected.

Limits, stated: this proves input identity, not output identity. The LP is
deterministic given its inputs under the pinned env (the five exact goldens and
the 2019–2021 MISO years show that), but no MISO 2023–2025 replay with the faithful
recipe has been solved. The basis tree read the branch's `data/raw` and
`data/clean`; the only `data/raw` changes in `f98c4564..e8570532` are EIA-923 coal
stocks 2015–2017 and NWPP interchange files, and neither reaches the MISO inputs
(identical arrays).

## 4. Scope — which other goldens could the gap reach?

The gap bites only where a keeper's per-year overlay carries a non-year-driven
field in a year the golden replayed. From the nine committed `meta.json`:

| Keeper bundle | Overlay fields | Golden years | Reached |
|---|---|---|---|
| MISO `closeout_miso_nuc_span` | `gas_offer_margin_anchor`; `miso_measured_reserve_requirements`, `miso_reserve_online_gated` (2023–2025) | 2019–2025 | **yes, 2023–2025 (this record)** |
| ERCOT `closeout_ercot_l1_span` | eight ERCOT fields, 2019–2023 | 2024–2025 (forward span) | no; exact |
| SPP `closeout_spp_nuc_span` | `nwpp_seam_measured_limits`, all years | 2019–2025 | no; exact |
| NEISO `w0_neiso_span` | `gas_offer_margin_anchor` (year-driven) | 2019–2025 | no; exact |
| CAISO, NYISO, PJM, SOCO, NWPP | none | — | no |

## 5. Hand-off

* **UC-DESK / owner:** `scripts/capture_keeper_goldens.py` does not replay a
  composite keeper's per-year recipe. Any golden over a span whose overlay arms a
  mechanism will read FAIL without a code change. The fix is to call
  `replay_keeper.enforce_single_recipe_partition` (one recipe group per call) in
  `capture_one`, and to run the fidelity check against `run_config_<y>.json`. That
  file is outside this lane's region; nothing on `main` is changed here.
* **UC-1-FINISH:** records this verdict in the PR's G-OFF table.

## Appendix A — commands

Prerequisites: `uv sync`; `uv run python scripts/regenerate_clean.py --solve-profile MISO`.
Worktrees as in the NYISO record's Appendix A, at `f98c4564` (basis) and
`e8570532` / `d62ae1a7` (main-without-UC), with `data`, `results`, `.venv`
symlinked to the main checkout.

```bash
B=/home/user/market-simulator/results/calibration/closeout_miso_nuc_span
GOLDEN=1 MAIN=/home/user/ms-main ./run_iso.sh miso  $B /home/user/ms-basis 2023 2024 2025 2022 2019 2020 2021
MAIN=/home/user/ms-main2           ./run_iso.sh miso2 $B -                  2019 2020 2021 2022 2023 2024 2025
```

`run_iso.sh` runs, per year, `capture_inputs.py` on each tree (two in parallel),
then `compare.py` on each pair, ignoring the nine `uc_*` / `unit_commitment_milp`
fields and five checkout-path fields. `capture_inputs.py` is the NYISO record's
`capture_mc.py` generalised to any bundle. It records the whole `run_energy_solve`
argument set, and `CAP_GOLDEN_RECIPE=1` skips the per-year overlay to mimic
`capture_keeper_goldens.py`. Both scripts are session scratch, not committed. Their
full mechanism is the NYISO Appendix A spy plus this one switch:

```python
GOLDEN_RECIPE = os.environ.get("CAP_GOLDEN_RECIPE") == "1"
if not GOLDEN_RECIPE:
    rk.enforce_single_recipe_partition(meta, kwargs["years"], kwargs)
if hasattr(rk, "flipped_default_overlay") and not GOLDEN_RECIPE:
    rk.apply_config_overlay(kwargs, rk.flipped_default_overlay(BUNDLE, kwargs["years"], meta))
```
