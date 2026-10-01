# PRECOMMIT — NYISO-NEXT-9: remove the always-on 900 MW HQ_hydro firm-import floor

- **Session:** NYISO-NEXT-9, the orchestrator. No LP runs in this container (rule 32 (a)).
- **Written before any solve.**
- **Keeper (control, form 4):** `2026-09-27-nyisonext8-hq-dedupe-span`, bundle `results/calibration/nyisonext8_span` (2022–2025), plus the stamped 2021 run `2026-09-27-nyisonext8-hq-dedupe-2021` (bundle `results/calibration/nyisonext8_2021`). Keeper `git_sha` `8184ca75`.
- **Probe:** `scripts/probes/nyisonext9_hq_floor_phase0.py` writes `results/calibration/_nyisonext9_phase0.json` (zero LP).
- **Routed from:** NEXT-8 PRECOMMIT §3. It is a rule-17 `[R-FLOOR-WINDOW]` question on `nyiso_firm_imports`.

## 1. The object

The keeper arms `nyiso_firm_imports`. `inject_nyiso_firm_imports` floors the `HQ_hydro` import row at `NYISO_FIRM_IMPORT_FLOOR_FRAC["HQ_hydro"] = 1.0 × 900 MW` in every hour. `IESO_Ontario` has frac 0.0, so it is inert.

## 2. Identification (rule 17: driver, window, forward story)

**Stated driver: "the HQ Châteauguay/Cedars firm contract." No published firm energy quantity exists.**

- **Gold Book 2021/2022 Table V-1** gives net capacity purchases from all external areas combined: 2,465 MW summer 2022. That is an ICAP product, not an hourly energy schedule. ICAP external suppliers carry a DAM *offer* obligation, not a must-flow obligation. The repo already cites this table for adequacy in `capacity_market.py` and says explicitly that the 900 MW is *not* it.
- **Gold Book Table III-3d** gives scheduled transactions by proxy bus, e.g. HQ Chateaugay 2021 net 9,907 GWh. That is a realized outcome, not a contract.
- **CHPE (1,250 MW, NYSERDA Tier 4)** is the first contracted HQ→NYC delivery. Its in-service date is 2026, outside every backcast year.
- **The level's own identification is an outcome.** `scenarios.py` justifies the floor as "NY imported ≥922 MW in 98 % of 2023 hours": a percentile of *measured total net import*, which is the pin rule 13 refuses. `FIRM_BASE_MW = 900.0` in the producer is "kept at its established value". The docstring's claim that the floor "can never force a phantom over-import" is falsified by the measurement below.
- **Window.** The legitimacy diagnostics register the floor with window `h0-23` (`D4_WINDOWS[(MECH_FIRM_IMPORT, None)] = (0, 24)`). So D-4 passes vacuously. D-2 books 7.884 TWh/yr (900 MW × 8,760 h) as `firm_import` in every year.

**Driver data against the floor (measured, HQ duplicate removed):**

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| hours measured total net import < 900 MW | 46 | 322 | 277 | 572 | 514 |
| minimum hour (MW) | −97 | −611 | −377 | −852 | −640 |
| HQ seam alone, annual mean (MW) | 1,228 | 1,082 | 303 | −153 | −545 |

**Decision (ex ante): REMOVE.**

- **Why not window it?** A window needs a driver series (an HQ contract schedule or HQ derate postings). None is published or on disk.
- **Why not re-base it?** Re-basing needs a published quantity, and there is none. Any level fitted to measured flow is an outcome pin (rule 13).
- **Why remove is admissible (rule 19).** Removing leaves one mechanism per phenomenon:
  - The *monthly* import level is already set by `nyiso_import_reconciliation`, a band on measured EIA-930 net interchange.
  - The *hourly shape* is set by the measured Q–Q ladder, on which `HQ_hydro` is the cheapest rung.

**What removal changes.** `HQ_hydro` becomes an ordinary economic rung at its measured Q–Q price ($11.41 / 23.77 / 13.59 / 17.50 / 20.43 for 2021–2025).

## 3. Phase 0 footprint on the keeper (zero LP)

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| keeper hours with import exactly at 900 MW | 0 | 0 | 145 | 541 | 706 |
| upper bound on forced energy (TWh) | 0 | 0 | 0.13 | 0.49 | 0.64 |
| of those hours, measured net import < 900 | — | — | 56 | 153 | 86 |
| of those hours, Upstate_West model price < HQ rung | — | — | 47 | 24 | 180 |
| model / actual DA price in those hours ($/MWh) | — | — | 19.81 / 25.55 | 26.00 / 26.08 | 39.98 / 46.89 |
| annual-mean effect if those hours closed their whole gap ($/MWh) | 0 | 0 | +0.10 | +0.005 | +0.56 |

- **Where the energy lands.** It lands at the import node, which delivers into Upstate_West and Capital_Hudson. Upstate_West is the congested landing zone: its model price in the binding hours averages $9.35, $24.03 and $34.32 (2023–2025).
- **How much truly binds.** Most keeper hours at exactly 900 MW are ladder-cleared, not floor-bound. The monthly-band dual is not persisted, so the exact binding footprint is measured only by the A/B.
- **Prediction.**
  - 2021 and 2022 should be near byte-identical, because the floor is slack there.
  - In 2023–2025, import should drop below 900 in some low-Upstate-price hours, and the band should re-place that volume in other hours of the same month.
  - The price effect should be small, at most ~$0.6/MWh on the annual mean. **This is not a C3a closer**, and that is stated now.

## 4. G-DRIFT (keeper `8184ca75` → pin, on `origin/main` `365e39af`)

Scope: `git diff 8184ca75 365e39af -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py scripts/lib scripts/replay_keeper.py data/raw/_validation-source data/raw/reference` (25 files). **Every hunk is INERT for NYISO.**

| hunk | why inert |
|---|---|
| `zone_assignment.py`, `topology_variant.py`, `renewables.py`, `eia930/zonal_shares.py`, `eia930/envelopes.py`, `eia860.py`, `runner.py` / `run_calibration*.py` `set_spp_zone_partition`, `data/raw/reference/spp_plant_reserve_zone.csv` | SPP-93 / SPP-94: SPP branch only; `spp_zone_partition` is forced to `north_south` for any other ISO |
| `campd_bins.py`, `assembly.py` (`coal_econ_marginal_hr_two_sided`), `run_calibration*.py` CLI | soco-81: default off, absent from the keeper recipe, and no NYISO artifact |
| `offer_surfaces.py` (`pjm_offer_midcurve_shape_segments`) | PJM-NEXT-5: default `None`, absent from the keeper recipe |
| `outages.py`, `fleet/arrays.py`, `fleet/__init__.py`, `backcast_config.py`, `persist.py` (`retiree_cems_cap` deleted, rule 26) | the keeper recipe carries `retiree_cems_cap: false`; `replay_keeper.py` translates it (`("PJM", (False, None, True))`), so the off-path is unchanged |
| `constants.py` `ST_GAS_PEAK_MEASURED_HR_MULT_BY_ISO` | CAISO key only |
| `interchange/caiso.py` (`caiso_intertie_partial_year_measured`) | CAISO branch, default off |
| `scenarios.py` | the four new fields above, all default-off |
| `data/raw/_validation-source/actual_lmp.json`, `actual_lmp_zonal_ERCOT.parquet` | only the ERCOT key changed (verified: `new["NYISO"] == old["NYISO"]`) |

**Form 4 is valid.** The keeper's committed bundles are the control. The only LIVE change is this arm's `--set nyiso_firm_imports=false`.

## 5. Landing: a recipe flip on an existing field, no code change

- The arm is `replay_keeper.py <keeper bundle> --set nyiso_firm_imports=false`.
- `nyiso_firm_imports` already exists (default `False`), so the change adds no field, no matrix row and no DOF. It removes one hardcoded level (900 MW) from the keeper's recipe.
- The matrix cell `nyiso_firm_imports` is updated this session under rule 28 (b), whatever the result.
- **Deleting** the field, `NYISO_FIRM_IMPORT_FLOOR_FRAC` and `inject_nyiso_firm_imports` (rule 26) is **not** done here. That is a separate change that touches forecast recipes and tests. If this arm is promoted, it is listed for the owner.

## 6. Gates (fixed now; arm vs the keeper's committed bundles)

- **G-1 leg acceptance (shard hard stop + parent check).**
  - Each leg solves at the pinned SHA.
  - The leg's `run_config.json` `scenario_config` equals the keeper's except `nyiso_firm_imports: false`, plus any keys `replay_keeper` translates identically for the control (`retiree_cems_cap`).
  - The leg's `legitimacy_diagnostics.json` has no D-2 `firm_import` row.
- **G-2 structure.**
  - **(a) The floor is gone.** At least one year's hourly import minimum falls below 900 MW, or, if none does, the arm is inert and reported as `I` (not promoted: nothing changed).
  - **(b) The monthly band holds.** |Δ annual import TWh| ≤ 4 % of the keeper's in every year. That is two ±2 % band half-widths.
- **G-3 protective.** C6 and C8 PASS in every year. The D-4 FAIL row set is reported against the keeper's.
- **G-4 reported, NOT a criterion:** C1, C2, C3a, C3b, C3c per year, the determination, the load-weighted Δ price per zone, and the hours with import < 900 MW against the measured count.

## 7. Promotion rule (ex ante)

- **Promote iff G-1 is exact in all five legs, G-2 (a) and (b) hold, and G-3 holds.**
- The basis is rules 13, 17 and 19: an outcome-level, windowless floor is removed, and the keeper's forcing ledger drops 7.884 TWh/yr of `firm_import`.
- C3a moving in either direction neither promotes nor blocks (rule 1).
- If G-3 fails, the response is investigated and the owner is asked (rule 31).
- **Year set.** The union of `years` over the NYISO sidecars is {2021, 2022, 2023, 2024, 2025}. All five are solved, one shard per year (rules 34 (c), 35 (b), 36).
