# HANDOFF — NWPP-NEXT-10: NWPP calibration after NEXT-9 (keeper #15 stands)

```
SESSION NWPP-NEXT-10 — NWPP calibration, keeper #15 (2026-09-28-nwppnext8-coal-monthly-pile) stands
DATA PROFILE: nwpp
MODEL: Opus or Fable
CLAUDE.md is binding. Pay particular attention to rules 1, 5, 13, 14, 19, 21, 23, 24, 28, 29 and 31–36.
The parent never solves (rule 32(a)). Every backcast year gets its own shard (rule 36).

CHAIN DIRECTIONS (owner, standing; pass them on verbatim to every handoff you launch)
- First, when it is safe, archive the previous session: session_01XR5q2FfzNUvsMa65skKNss (NWPP-NEXT-9).
  Safe means: its PR has merged on main, and get_session shows it idle.
- Check for unmerged NWPP branches and PRs. Salvage anything needed into your branch, and close or merge the PRs.
  Say which branches can be deleted.
- Rebase and merge your work.
- Present every decision for the owner as clickable decision cards (AskUserQuestion), NEVER as inline text.
- When done: promote if it is a good candidate, create a PR and merge it, archive all your shards, and launch the next
  handoff session to continue calibration while rubric failures remain. Give it these same chain directions, including
  "archive the previous session when safe".
- If NWPP becomes calibrated and the rubric clears for all years, check the complete / frontier declaration criteria.
  Settle the keeper config and clear the tasks that enable declaration. If complete / frontier is reached, say so in
  your final message so the owner can approve.
- If you are at the session-nesting limit, make your last message a handoff prompt that starts a new chain.
- Owner standing ruling: promote if structural integrity improves, even if a gate regresses. Report every regression
  at full magnitude.

STATE ON MAIN
- Keeper #15 is unchanged: 2026-09-28-nwppnext8-coal-monthly-pile. Bundle: results/calibration/nwppnext8mp_span.
  Years: 2019–2025.
- Determination: NOT-YET on {dispatch_corr}, ONE record. C4 coal 2023 is r 0.695 / NRMSE 0.283 against the 0.70 floor.
  Price is UNSCORED (rubric v3.8).
- NEXT-9 was REJECTED by the owner on 2026-09-29.
  - It tested coal_monthly_pile_measured_receipts (default-off field, still in code): same-year EIA-923 Page 5 receipts
    on the monthly pile.
  - Annual coal volume became more accurate: C1 COAL_BIT 2023 +4.73 → +0.72 TWh.
  - C4 went from 1 to 3 failing records: coal 2022 0.695, 2023 0.648, 2024 0.664.
- Records to read first:
  - docs/records/nwpp/RESULT-nwppnext9-coal-measured-receipts-2019-2025-2026-09-28.md (§2 finding, §5 routed)
  - docs/records/nwpp/PRECOMMIT-nwppnext9-coal-measured-receipts-2019-2025-2026-09-28.md (§0 census, §4a G-DRIFT)
  - docs/calibration-log/nwpp.md, docs/codebase-site/data/mechanism-matrix/NWPP.js, docs/mechanism-testing-matrix.md §5.9

WHAT DRIVES C4 COAL 2023 (NEXT-9 census, zero LP)
- 2023 was a PacifiCorp coal-supply shortfall year:
  - Page 5 receipts fell: Bridger 105.1 → 86.6, Hunter 58.8 → 39.2, Huntington 56.0 → 26.5 TBtu.
  - December stocks hit record lows: Bridger 1,285 → 798 kt.
- Jim Bridger (8066) alone is +2.0 TWh of the Jan–Mar over-burn.
  - Its four units were online but at ~20 % load from Feb to May while the pile was rebuilt.
  - CEMS Jan–Mar was 906 / 416 / 294 GWh against the model's 1,393 / 1,217 / 984.
- NEXT-9 showed that fixing volume alone makes timing worse. The perfect-foresight LP spends scarcer coal in the
  dear-gas months, whereas the real operator held stock.
- So the missing structure is OPERATOR INVENTORY MANAGEMENT.

CLOSED — do NOT redo:
- Everything closed in HANDOFF-nwppnext7, -nwppnext8 and -nwppnext9.
- The pile never dropping below its historical minimum (S_min). Refuted at phase 0: Bridger drew 0.33 Mt below its
  prior minimum in 2022.
- Measured same-year receipts alone (NEXT-9, rejected).
- Offer-multiplier tuning on C1, C4 or CT (rules 1 and 13).

OPEN LEVERS, highest value first
1. C4 coal 2023: an inventory-management mechanism with a MEASURED, forward-regenerable identification.
   - Example: a published utility fuel-inventory target, such as a days-of-burn policy in PacifiCorp's IRP or rate-case
     filings. A new raw source goes through the data-intake skill.
   - The owner rules via a decision card before any build.
   - No fitted parameter (rules 5 / 21). Zero-LP phase 0 first: size it against keeper #15's per-plant m_mon and CEMS.
   - The NEXT-9 flag may combine with it, but the owner has already rejected it standalone.
2. Colstrip 2020 available energy is 5.86 TWh against 7.94 TWh generated (EIA-923). Check the outage/availability inputs.
3. SNV residual shed (2020: 46.6 GWh; 2021: 34.0).
4. Internal-link over-flow: a structural FINDING plus an owner question.
5. Jim Bridger (8066) has no measured COAL tranche row.
6. Solve time (performance only). The 2019 leg takes ~2.5 h. A pile-state formulation must reproduce keeper #15
   byte-identically before it may be used.

ZERO-LP TOOLS (NEXT-9)
- Per-plant monthly census: keeper payload m_mon (frontend/data/backcast/runs/<keeper>.js, gz+b64) against CAMPD gross,
  via scripts/probes/_nwppnext4_coal_census.py::campd_plant_hourly.
- C4 recompute against EIA-930 from hourly/class_hourly_<Y>.parquet: it matches the scorer exactly.
  - EIA-930 comes from run_calibration_full._eia930_frame(Y,'NWPP',None).
  - Gas is CC_REGULAR + CC_CHP + CT_PEAKER + CT_CHP + ST_GAS + ST_CHP.
- scripts/probes/_nwppnext9_measured_receipts_phase0.py rebuilds the fleet on keeper #15's recipe and calls the pile
  builders.
  - It needs /tmp/n49 restored, then curate_hydro_plant_modes, curate_coal_receipts and curate_coal_stocks.

PROCEDURE FOR ANY SOLVE — follow PRECOMMIT-nwppnext9 as the template (§4a G-DRIFT, §5 recipe, §6 hard stops)
- G-DRIFT runs against keeper #15's git_sha e7478536. NEXT-9 found ALL INERT at main 40fc286b; re-audit from there.
- Replay source: restore the NWPP-49 bundle from commit 909cdd30bfdd8a398b10a4255b1340d0d9ef1943 into /tmp/n49.
  - Use keeper #15's full --set list from PRECOMMIT-nwppnext8 §5.
  - Add hydro_backfill_year=null for 2019–2022.
- Pin a full 40-character SHA. The shard prompts in NEXT-9 are a working template:
  - pre-authorize the pin checkout;
  - nohup plus a PID file, with ~9-min in-turn polls;
  - push the FULL bundle with a .gitignore negation and a plain git add;
  - forbid the shared generated files.
- Budgets: 2019 needs ~200 min; other years take 35–60 min.
- Hard stops:
  - campd_ct_heat_rates_NWPP.csv sha256 = 29baa2f1ecfa10d9734c7e44cc306a88d527adb28968ea260f3409de37d7ff92.
  - The run_config diff against keeper #15's run_config_<Y>.json may differ only in the arm's key. A missing retired
    nyiso_firm_imports (False in the keeper) is benign.
  - P1 demand: 279.581 / 292.940 / 289.358 / 298.960 / 280.261 / 290.216 / 302.532 TWh.
- Compose, then score and register:
  - compose with scripts/probes/_nwpp42_compose_span.py --out results/calibration/<name>_span --skip-diagnostics
    (2023 leg first);
  - legitimacy_diagnostics.py (exit 1 is normal);
  - attestation: wrap scripts/gen_nwppnext9_attestation.py, which chains 8 → 7 → 6;
  - dashboard_add_run.py --no-prune;
  - calibration_verdict.py --run-id <id> --json, then diff per record.
- A DECLINED probe is pruned with prune_iso_runs.py --iso NWPP after the owner rules (audit_keepers E13; MISO-276 and
  NEXT-9 precedent).
- Promote by rule 35: keeper_store --set, build_status, audit_keepers (E1), prune, check_promotion_completeness, the
  matrix stamp and cell, §5.9, the calibration log, and the calibration-keeper-auditor subagent.
- Gitignore per-year leg dirs with a pattern that does NOT match the _span dir.

HOUSEKEEPING (owner)
- Leftover shard branches to delete. A session cannot delete refs (HTTP 403):
  - claude/nwppnext9mr-{2019..2025}
  - claude/nwppnext8mp-{2019..2025}, if still present
  - claude/nwppnext8, empty beyond main
- Known pre-existing test failures, not NWPP's:
  - the 27 in tests/unit/data/test_firm_import_*, test_gas_offer_zonal_anchor_vintage and tests/unit/results/test_export;
  - test_d53, test_d60, test_reserve_config and test_ccs_retrofit;
  - test_summer_availability_constants::test_coal_is_exempt (the COAL subtest fails on main).
- test_nwpp_demand_plant_basis::test_artifact_matches_bench_parts is FIXED by NEXT-9's hash re-derive.
  - Any future NWPP registration re-renders the bench parts, so re-run scripts/data/derive_nwpp_plant_basis_energy.py
    after registering. Only source_sha256 moves; the file is not on the solve surface.
```
