# RESULT — R-PJM-2: the RGGI keeper on corrected inputs, 2019–2025 — PROMOTED (2026-09-25)

**New PJM keeper:** `2026-09-25-pjm-r-pjm-2` · bundle `results/calibration/rpjm2_span` (2019–2025, one bundle) ·
PRECOMMIT `docs/PRECOMMIT-r-pjm-2-rggi-keeper-corrected-inputs-2026-09-25.md`, pinned
`651fac089742fb4fb9163d032915ab48f2296ade` · **owner ruling, verbatim: "Yes promote"** (2026-09-25).
**Superseded, and pruned per rule 35:** `2026-09-24-pjm-h22-rggi-span` and its touchpoint
`2026-09-24-pjm-h22-rggi-touchpoint`, plus `2026-09-24-pjm-r-pjm-corrected` (R-PJM's h19-based run).

## 1. What changed

The keeper is the h22 recipe (RGGI allowance pricing) plus the four corrected-input flags of audit §5.3.7:
`eia860_vintage_tracks_solve_year` and `measured_{coal,st,cc}_heat_rates`, each False → True (CT and CHP were
already on). Every year now runs on its own EIA-860 vintage, with year-matched eGRID and measured CAMPD
heat rates. **2019 is added.** Its RGGI rows (MD/DE members, 5.97 $/t, zone share derived on
`vintage_2019`) landed in this lane, so 2019 is priced like every other year. The offer curves are
byte-identical to h22's, and zero free parameters were added. Each shard verified its RGGI adder log line:
2019 320/2800 generators, 2023 882/2684, 2025 534/3081.

## 2. Determination: unchanged, year for year, on the same benchmark

| year | h22 | R-PJM-2 |
|---|---|---|
| 2019 | — | NOT-YET (C1) |
| 2020 | NOT-YET (C1, C3a) | NOT-YET (C1, C3a) |
| 2021 | NOT-YET (C1) | NOT-YET (C1) |
| 2022 | NOT-YET (C3b) | NOT-YET (C3b) |
| 2023 | CALIBRATED | CALIBRATED |
| 2024 | NOT-YET (C1) | NOT-YET (C1) |
| 2025 | CALIBRATED-WITH-CAVEATS (prelim 923) | CALIBRATED-WITH-CAVEATS |
| **2023–25 (headline)** | **NOT-YET, C1 alone** | **NOT-YET, C1 alone** |

| year | C3a h22 → new | C3b NRMSE | C4 r gas/coal | C1 FAIL rows (h22 → new) |
|---|---|---|---|---|
| 2019 | — → +8.6 % | — → 0.109 | — → 0.926/0.938 | — → CC_REGULAR −13.39, COAL_BIT +11.36 |
| 2020 | +17.3 → +16.2 % F | 0.182 → 0.172 | 0.928/0.836 → 0.929/0.854 | COAL_BIT +29.23 → **+21.45** |
| 2021 | +4.0 → −0.6 % | 0.107 → 0.098 | 0.931/0.943 → 0.933/0.950 | CT −8.57 → −11.11, COAL_BIT +22.38 → +25.70, **CC_REGULAR newly −17.42** |
| 2022 | −8.2 → −8.8 % | 0.235 → 0.246 F | 0.934/0.945 → 0.932/0.938 | none → none |
| 2023 | +4.9 → +4.8 % | 0.119 → 0.122 | 0.948/0.922 → 0.950/0.930 | none → none |
| 2024 | +1.3 → −0.8 % | 0.115 → 0.118 | 0.943/0.935 → 0.944/0.928 | CC_REGULAR −13.61 → −14.36 |
| 2025 | −4.1 → −5.5 % | 0.129 → 0.133 | 0.947/0.941 → 0.948/0.946 | none (C1 unscored, prelim 923) |

The same pattern as R-PJM on h19 holds. In 2021 the vintage restores ~10 GW of coal and the model spends it
(COAL_BIT +3.3 TWh further over actual, CC −17.4 TWh). This is the offer-ordering finding (pjm-168)
re-earned on clean inputs; a coal/CC offer question, routed and not tuned. 2020 improves by 7.8 TWh of coal
over-run. 2023–25 barely move.

## 3. Promotion mechanics (rule 35), executed in this session

1. **Year union before the delete:** 2019–2025 across every PJM sidecar. The incoming bundle covers all of
   it, so there is no stamped rung.
2. **Incoming stores registered and verified:** sidecar, payload and bundle all present (`audit_keepers` has
   no E1 failure).
3. **Keeper re-keyed:** `keepers/PJM.json`, the `calibration-complete.json` PJM entry (keeper,
   determination, rekeyed, keeper_history), the matrix shard stamp (the four F1 cells O → K), and
   `build_status.py --iso PJM`.
4. **Pruned:** `prune_iso_runs.py --iso PJM --force-uncite` removed the three superseded runs' three
   stores each. After the prune, `audit_keepers.py --iso PJM` reports **0 failures, 0 warnings**.

## 4. Provenance and retrievability

The per-year shard commits (all at pin `651fac08`) are provenance only; the shard branches are transport.

| year | shard commit |
|---|---|
| 2019 | `2b417715c373cd3ef5b0563fb7c6f81a5ab9efbd` |
| 2020 | `7a9eacbb1647ff2097370d362d34579311841e35` |
| 2021 | `26b5740322a0a8f4aa7eac318cf93ec4ef1ec883` |
| 2022 | `5df5096923ba4eeff2c910a6a71edd6415388ca3` |
| 2023 | `0fabf298655fc3eaad4b7021c467cf51a47aad3c` |
| 2024 | `ddeeb87219fdf2a7352db6bc3a50581fc67ee823` |
| 2025 | `d858a45fc5dc6247fab5bb7da4b76c4e12d07601` |

**On `main`:** the keeper bundle `rpjm2_span` in rule-15 shape (attestation, diagnostics, per-year configs,
hourly sidecars), its sidecar, its payload and the rebuilt bench parts. The per-plant `dispatch/` parquets
follow the repo-wide `.gitignore` (as every PJM keeper before it); a question that needs them costs a
7-shard re-solve (~45 min wall). All 14 shards across R-PJM and R-PJM-2 are archived. Leftover shard
branches `claude/rpjm-inputs-*` and `claude/rpjm2-*` cannot be deleted from a session (rule 33(f)(2)), so
the owner needs to clear them.

## 5. Still open (not this lane's to close)

- The std / short-coal outage re-derive (F2 findings 1–2, R-PJM RESULT §6) is measured and not installed.
- The unit partial-derate family emits 0 windows at HEAD: the revealed-availability filter drops every
  partial plateau, so fixing it needs a detector change.
- `mid_vintage_exit_carry` (U in PJM, default off) is not in the recipe. It carries 12 mid-year
  retirements (~6.9 TWh) that full year-correct vintage would include.
