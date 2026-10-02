```
SESSION SPP-108: SPP — ROOT-CAUSE THE 2021–22 COAL_PRB OVER-COUNT / CC UNDER-COUNT (zero LP first; then this session launches its own year-isolated shard chain). Chartered by the owner's SPP-107 card "Coal 21–22 over-count (Rec.)" (2026-10-02).
DATA PROFILE: spp
MODEL: Opus or Fable (rule 27). CLAUDE.md, docs/RUNBOOK.md and docs/backcast-closeout-plan-2026-10.md §3.4 are binding. Rules 1, 13, 14, 19, 21, 23, 28, 29(b), 31–36 matter most.
LAUNCH NOTE: this session is the PARENT. It writes the PRECOMMIT and launches its own shards (rule 32). Launch it top-level from the owner, not nested under another lane: SPP-94's shards were refused at lineage depth 8.

STATE (verify against origin/main)
- Keeper: 2026-10-02-spp-107-mmu-repair. Bundle results/calibration/spp107EXR_span, 2019–2025, carrying hourly/unit_marginal_<Y>.parquet for every year.
- Recipe: spp-100 + spp_mmu_offer_unavailability + spp_mmu_offer_repair.
- Train tier 2023–25: CALIBRATED (lone ledgered C3c; >$200 h 0/4/4 vs RT 42/59/68).
- Train C3a −5.4 / −8.2 / −2.9 %.
- Records: docs/records/spp/RESULT-spp-107-mmu-carrier-repair-2026-10-02.md; docs/calibration-log/spp.md.
- The only C1 FAILs (validation tier) on the keeper:

  | year | COAL_PRB | CC_REGULAR | C4 gas NRMSE |
  |---|---|---|---|
  | 2021 | +11.37 TWh | −8.52 TWh | PASS |
  | 2022 | +10.92 TWh | −9.29 TWh | 0.326 (FAIL) |

  SPP-107 already cut PRB by ~1.8–2.3 TWh/yr. Do not re-attribute that to a new lever.
- Close-out plan §3.4 diagnosis:
  * DA commitment of CCs (all of 2021, ~60 % of 2022).
  * A 2022 coal rail / markup object (~40 %; SPP-89; the 2022 ASOM names rail supply-chain problems and RR502 opportunity-cost offers).
  * On the EIA-930-aligned gross basis coal is over by only +2.0 / +5.5 TWh, not +13 (SPP-87).
  * EIA-923 carries 2.7–5.1 TWh/yr of gas outside SPP metering (SPP-88).

CHARTER (follow the plan §3.4 step order; go off-plan only with a reason stated in the PRECOMMIT)
1. Step 0a, zero LP: shadow-score C1 2021/22 on the EIA-930-aligned basis with the SPP-88 gas-coverage correction.
   - Read: CC 2021 ≥ −8.0; PRB 2021/22 within ±8.0.
   - Uses the keeper's committed sidecars. No solve.
   - Report how much of the "miss" is benchmark basis versus dispatch.
   - The basis ruling itself is OWNER-GATED (plan §5, W5). Put it to the owner as a clickable card with the measured numbers. Never adopt a basis because it passes.
2. Step 3: the coal rail-deliverability retest (SPP-44, cell R, re-opened only on the new evidence the plan names: STB EP 724 weekly BNSF/UP coal unit-train loadings vs plan, by basin).
   - If the series is not in data/raw, ask the owner to download it (card).
   - If it is present, intake it through the data-intake skill. Re-measure SPP-44 at zero LP.
   - Only if 2022 PRB loadings-vs-plan is anomalous AND 2021 is not: PRECOMMIT the RR502-form opportunity-cost adder keyed to that series, with zero fitted parameters (rules 13, 21).
3. If, and only if, a built lever survives zero LP:
   - field default off; matrix row plus a cell in every shard; tests;
   - PRECOMMIT pinned by full SHA; G-DRIFT vs spp107EXR_span;
   - shard check adapted from scripts/probes/_spp107_shard_check.py and tested on synthetic legs;
   - SEVEN year-isolated shards launched in ONE message by THIS session (scripts/shard_prompt.py or docs/records/spp/spp107/shard_prompt_template.txt; relaunch any PENDING > 15 min);
   - compose (scripts/probes/_rspp_compose.py --require), attest, score, RESULT, promotion card (rules 31/35).
   - The parent solves nothing.
4. If nothing survives, ledger the residual: C1 2021/22 under the basis ruling's outcome, C4 2022 per plan step 5.

DO NOT:
- re-open spp_ct_lole_efor, spp_gas_crow_residual_outage, wefor_residual, coal_fuel_inventory (R) without the new evidence above;
- tune offer_curve_by_group, wefor_multiplier or the MMU bands;
- add a coal haircut or derate fitted to the C1 residual (rules 1, 13);
- re-derive a frozen derive script against the residual (rule 23).
OUT OF SCOPE: the 2023+ upper-tercile gap; 2019–20 over-pricing (plan step 2, the commitment-posture pairing); topology (W/E partition, owner-gated); other ISOs.

KNOWN TOOLING DEFECT (SPP-107): scripts/promote_keeper.py runs audit_keepers (step 8) BEFORE the prune (step 9), so E13 always fails on the outgoing keeper.
- Workaround: run prune_iso_runs.py --iso SPP --force-uncite --keep <new id>, then re-point keepers/SPP.json config_partition run_id/bundle, then build_status.py, then audit_keepers.py --check, then check_registry_payload_parity.py.
- Also re-stamp the §5.7 header in docs/mechanism-testing-matrix.md.

EITHER WAY:
- owner decisions as clickable cards;
- merge when required checks pass;
- comment once per other-lane red check (open at SPP-107 close: the NYISO test_gas_offer_zonal_anchor_vintage pair, red on main; diff against main before calling it not-yours);
- archive all shards (rule 33);
- end with an SPP-109 handoff prompt.

Housekeeping owed to the owner (sessions cannot delete refs):
- claude/spp104-2019 … -2025
- claude/spp105a-*, claude/spp105b-*
- claude/spp106ex-2019 … -2025
- claude/spp107exr-2019 … -2025
- claude/spp-mmu-offer-carrier-repair-gonc4e
```
