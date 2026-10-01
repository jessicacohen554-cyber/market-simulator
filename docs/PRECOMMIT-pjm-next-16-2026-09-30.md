# PRECOMMIT — PJM-NEXT-16: arm A (OVEC fleet boundary) and arm B (+ PJM CC commitment bridge)

**Written before any solve.** Zero-LP evidence: `docs/FINDING-pjm-next-16-cc-loading-and-the-ovec-boundary-2026-09-30.md`.

**Owner rulings (2026-09-30, decision cards):**
- OVEC fix: *"Build + solve"*.
- CC bridge: *"Charter + solve with OVEC"*, with its volume sign stated as unpredictable at zero LP.

**Keeper / control:** `2026-09-28-pjm-next8-exitfix` (bundle `pjmnext8_xf_span`, solved at `e9fc1a5e`). Control = its committed bundle plus G-DRIFT (§4); there are no control solves (rule 29(b)).

## 1. Arms

| arm | out-dir | recipe | what it tests |
|---|---|---|---|
| **A** | `pjmnext16_A_<y>` | keeper recipe at the pinned SHA, **no `--set`** | `ISO_BA_JOINS["PJM"] = {"OVEC": (2019, 1)}`, vintages 2019/2020 rescoped (+11 generator rows each), and the outage-apportionment join seam (`outages._joining_ba_generators`). Ungated registry fact (the SOCO/AEC precedent), zero free parameters. |
| **B** | `pjmnext16_B_<y>` | A + `--set pjm_gas_commitment_bridge=true --set cc_mustrun_per_plant=false` | The PJM leg of the gas commitment bridge. It **replaces** `cc_mustrun_per_plant` (rule 19; the config refuses both armed). Measured plant-basis CAMPD 2023–2025 statistics: min-load 0.436, min-run 11 h. gas_cc only. |

- One shard per year per arm, 2019–2025: 14 shards (rule 36).
- B − A isolates the bridge at one SHA.
- A 2021–2025 − keeper measures HEAD drift directly: the OVEC change is inert there, verified on the rebuilt fleets for 2021 and 2023.

## 2. Predictions (fixed now)

### Arm A (OVEC)
Built on the keeper's own displacement shares (CC 0.35, coal 0.38–0.41, CT 0.18) and supply slope (≈ $0.2/MWh per GW).

| | 2019 | 2020 |
|---|---|---|
| OVEC model generation (actual 11.24 / 9.03 TWh) | **9–14** (point ~11.7) | **8–13** (point ~10.3) |
| C1 CC_REGULAR (keeper +10.86 / +14.08) | **+5 to +8 → PASS** | +9 to +12, still FAIL |
| C1 COAL_BIT (keeper +10.61 / +3.91) | +15 to +20, worse | **+8 to +12 → NEW FAIL** |
| C1 CT_PEAKER (keeper −4.59 / −3.51) | −6 to −7.5, still pass | −4.5 to −6, still pass |
| C3a (keeper +11.8 % / +15.9 %) | −0.5 to −2 pts, still FAIL | −0.5 to −2 pts, still FAIL |

- **2021–2025:** identical to the keeper, apart from HEAD drift (§4).
- **Falsifiers for the mechanism, not the gates:**
  - OVEC generation outside the ranges above;
  - CC_REGULAR 2019 moving by less than 2 TWh;
  - any 2021–2025 movement that §4 does not name.

### Arm B (bridge; sign NOT predictable)
Registered expectations, stated as bounds rather than signs:
- **(B1) Placement, rule 17.** CC committed MW in hours the real plant was OFF falls from the keeper's 20–28 TWh/yr window-energy bound.
  - Measured post-solve from `unit_hourly` vs CAMPD, on the bridge's floored unit-hours.
- **(B2) Price-setting.** The share of low-end hours where a CC's committed/min-load rung is the marginal unit falls from 11 % (2020, NEXT-14).
  - The bridge floor is must-take by construction.
- **(B3) Legitimacy.** D-4 shows no off-window binding for `pjm_gas_commitment_bridge`, and C8 CC_REGULAR's forced share is ≤ 30 % or grounded.
- **(B4) Reported, not predicted:** CC_REGULAR C1 and C3a in every year, B − A.

## 3. Decision rule (fixed now; the owner rules on promotion, rule 31)

- **A is a keeper candidate on structure** (rules 1/14): it removes a measured boundary defect with zero free parameters. That holds even if COAL_BIT 2019/2020 regresses as predicted. The owner has stated that a structural gain with gate regressions "may still be a keeper".
- **B is a keeper candidate** only if B1 and B3 hold. It is refused on B3 failing. B2 and B4 are reported at full magnitude either way.
- Nothing is swept, and no parameter is chosen on the result. Min-load and min-run are the measured constants above.

## 4. G-DRIFT (rule 29(b)), keeper `e9fc1a5e` → origin/main `0da56737`, plus this lane's commits

**Other lanes' drift.** `git diff e9fc1a5e 0da56737` over `src/market_sim`, `scripts/run_calibration*.py`, `scripts/lib`, `data/raw/_validation-source` and `data/raw/reference` covers 84 files and 264 commits. Every hunk is **INERT for PJM**:
- `solve_surface_register --diff`: 0 values moved, 10 names added. They are read only under default-off flags or by ERCOT-only registries (`ISO_PLANT_ENTRIES`/`EXITS`).
- 25 new `ScenarioConfig` fields, all `bool = False` and registered at a `"False"` drop, so none is a default flip. The retired `nyiso_firm_imports` is dropped by `replay_keeper`.
- The rest is another ISO's branch (NYISO F/G, the CAISO clock repair, SPP/ERCOT/SOCO postures, the MISO EcoMin floor), or a flag that is off in the keeper recipe (`pjm_replacement_cost_fuel`, `cc_committed_offer_margin`, `coal_fuel_inventory`, `campd_split_remap_companions`, `unit_outage_exit_ym_from_eia860`, …).
- The PJM input artifacts the keeper resolves (`thermal_tranches_PJM.csv`, the exitfix outage extract) are byte-unchanged.

**This lane's own hunks: LIVE by design, and they are the arms.**
- `ISO_BA_JOINS["PJM"]`, the vintage 2019/2020 rescope and `outages._joining_ba_generators` move **2019/2020 only**.
  - The rebuilt 2021 and 2023 fleets are identical to the keeper (max |Δ mc| 6e-5, float32 storage).
- `pjm_gas_commitment_bridge` is default-off and armed only in B.

**Solve path.** Rule 36(d) defaults both warm-start knobs off, as they were at the keeper's solve. One year per shard.

**Conclusion.** Form 4 is valid. The keeper's committed bundle is the control for A, and A's 2021–2025 legs double as a direct drift measurement.

## 5. Execution

- 14 shards at the pinned SHA, `permission_mode auto`, `clone_depth 1`, `blob_limit_kb 2048`.
- Each shard runs `replay_keeper.py results/calibration/pjmnext8_xf_span --years <y> --out-dir results/calibration/pjmnext16_<A|B>_<y> [--set …]`.
- Each shard pushes its full bundle (incl. `dispatch/<y>_P1.parquet` and `hourly/unit_hourly_<y>.parquet`) via a `.gitignore` negation plus a plain `git add` (rule 34).
- The parent composes, scores (run-level and train tier), attests and registers.

## 6. Addendum (2026-09-30, before any B solve): arm B re-pinned

- The first B launch (pinned `6d4c7749`) was **stopped during setup, before any solve**.
- The regression sweep caught `tests/unit/pipeline/test_p1_prep_wiring.py`: the new P1 prep was wired into `pipeline/year.py` only.
  - `scripts/run_calibration.py` (the backcast path the shards run) and `runner.py` keep their own chains.
  - B would therefore have solved with the bridge flag set and the hook **inert**.
- Fixed in the next commit. B's seven shards are relaunched at that commit's SHA.
- Arm A is unaffected (the bridge flag is off there) and keeps pin `6d4c7749`.
- The fix only adds a flag-gated hook, so A's legs at `6d4c7749` and any leg at the new SHA are identical for A's recipe.
- Predictions and decision rule are unchanged.

## 7. Addendum (2026-09-30): arm B re-pinned a second time — export sinks

- The first completed B leg (2021, pin `5b813f34`) showed PJM net export at **0 in every hour**, against 24.6 TWh in the keeper.
- Cause: `_bridge_floored_fleet` max-composed the bridge's zero-initialised floor onto the priced export sinks (`pmin < 0`), pinning them off in P1. This is the caiso-138 §D defect; the existing remedy is `preserve_absorption=True`, which the PJM leg omitted.
- The unbridged keeper P1 keeps its sinks, so passing it restores the keeper's export outlet and changes nothing else.
- Every `5b813f34` B leg is invalid by construction. The six still running were stopped and archived; the two that finished (2020, 2021) are not used.
- B is relaunched at the next commit's SHA, with a new hard stop: the leg's annual net `import` must be below −5 TWh (PJM is a net exporter in every year).
- Arm A is unaffected (no P1 prep) and keeps pin `6d4c7749`.
- Predictions and decision rule are unchanged.
