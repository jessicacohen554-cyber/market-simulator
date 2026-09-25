# RESULT — R-PJM2-CS: the PJM keeper recipe re-solved on COAL-SUB HEAD, 2019–2025 — PROMOTED (2026-09-25)

**New PJM keeper:** `2026-09-25-r-pjm2-coal-sub` · bundle `results/calibration/rpjm2cs_span` (2019–2025, one bundle) ·
PRECOMMIT `docs/handoffs/r-pjm2-coalsub/PRECOMMIT.md`, pinned `afd8cbd61f7e31c7a55807e9219ddbde712372be`.
**Promoted on the owner's standing instruction**, given twice during this lane, verbatim: *"Is this a recommended keeper
candidate? If so plz promote. If structural integrity improves but gates regress that may still be a keeper."* This session
recommends it (§4), so it is promoted.
**Superseded and pruned (rule 35):** `2026-09-25-pjm-r-pjm-2` (bundle `rpjm2_span`).

## 1. What changed

Code only. The designated keeper's recipe (`rpjm2_span/meta.json`: h22 RGGI allowance pricing + F1 corrected inputs) was
replayed **with no `--set` and no config delta** at a HEAD carrying COAL-SUB (#6611/#6616, the bare `COAL` class
eliminated). G-DRIFT (PRECOMMIT §4) found COAL-SUB to be the only LIVE hunk. Its effect on PJM:

- The 11 former generic-bucket coal plants (5.37 / 3.89 / 4.62 / 1.31 GW in 2019–2022, none in 2023–2025) now resolve
  to COAL_BIT / COAL_PRB (Waukegan) / COAL_WC through their own EIA-860 energy-source code.
- They read their subclass's **existing** band multipliers and supply-class fuel pricing. The BIT units also get the armed
  bituminous passthrough sigmoid.
- The recipe's legacy `offer_curve_overrides["COAL"]` entry is folded away by `replay_keeper.translate_legacy_coal_keys`.
  It reaches no unit, because every subclass carries its own curve.
- Zero free parameters are added. Every subclass band is byte-equal to the keeper's (rule 1(c)). This is a
  representation correction (rules 1/14): no unit sits in a class that does not exist.

## 2. Class energy vs the outgoing keeper (model TWh, P1)

| year | COAL (old bucket) | COAL_BIT | COAL_PRB | COAL_WC | coal family | CC_REGULAR | CT_PEAKER |
|---|---|---|---|---|---|---|---|
| 2019 | 18.22 → 0 | +16.32 | +3.76 | +0.16 | **+2.02** | −1.32 | −0.24 |
| 2020 | 7.33 → 0 | +6.50 | +3.17 | −0.05 | **+2.29** | −1.28 | −0.42 |
| 2021 | 16.97 → 0 | +11.25 | +4.98 | +0.01 | **−0.73** | +0.60 | +0.08 |
| 2022 | 3.70 → 0 | +3.17 | 0 | 0 | **−0.53** | +0.25 | +0.11 |
| 2023 / 2024 / 2025 | — | 0 | 0 | 0 | **0** | 0 | 0 (every class byte-equal) |

## 3. Rubric, year by year (same benchmark, same scorer at HEAD)

The per-year pass/fail pattern is **identical** to the outgoing keeper's. The run-level determination is **NOT-YET**
for both runs (C1 CC_REGULAR 2024 −14.36 TWh, band 8, byte-identical).

| year | criteria failing (both runs) | C1 FAIL rows: keeper → new | C3a keeper → new | C3b NRMSE | C4 r gas / coal (new) |
|---|---|---|---|---|---|
| 2019 | C1 | CC_REG −13.39 → −14.71; COAL_BIT +11.36 → **+27.69** | +8.6 → +8.3 % | 0.109 → 0.108 | 0.923 / 0.936 |
| 2020 | C1, C3a | COAL_BIT +21.45 → **+27.95** | +16.2 → +15.6 % | 0.172 → 0.166 | 0.929 / 0.852 |
| 2021 | C1 | CC_REG −17.42 → −16.82; CT −11.11 → −11.04; COAL_BIT +25.70 → **+36.95** | −0.6 → −0.4 % | 0.098 → 0.098 | 0.930 / 0.947 |
| 2022 | C3b | none → none | −8.8 → −8.7 % | 0.246 → 0.246 | 0.932 / 0.938 |
| 2023 | — | none | +4.8 % | 0.122 | 0.950 / 0.930 |
| 2024 | C1 | CC_REG −14.36 → −14.36 | −0.8 % | 0.118 | 0.944 / 0.928 |
| 2025 | (C1 unscored, prelim 923) | — | −5.5 % | 0.133 | 0.948 / 0.946 |

**Why COAL_BIT reads worse, and why that is not a regression.** Actual COAL_BIT is unchanged (166.36 / 131.45 / 156.60
TWh). The outgoing keeper carried **18.22 / 7.33 / 16.97 TWh of model coal in a `COAL` class that C1 never scored**, so
its COAL_BIT rows compared a model total missing that energy against an actual total that included it. Every model MWh is
now scored against its subclass. The physical change is the coal-family column of §2 (+2.0 / +2.3 / −0.7 TWh). The larger
miss is the pjm-168 coal over-run, now fully visible. It is an offer-ordering question for a future lane, and it is
reported here, never re-tuned. Price and dispatch metrics are flat or slightly better (C3a 2020 −0.6 pt, C3b 2020 −0.006).

## 4. Recommendation: promote — executed

- **Structural integrity improves:** the model no longer carries a class that does not exist, and C1 now sees all model
  coal.
- **Nothing structural regresses:** there is no config delta, 2023–2025 are byte-identical, and the per-year gate
  pattern is unchanged.
- **Only the visibility of an existing miss grows.** That is the case the owner's instruction names.

## 5. Phase 0 and promotion mechanics

- **Census (PRECOMMIT §3):** zero bare-COAL rows in all seven years. The EIA-860 vintage resolves to the solve year
  (2025 canonical). Class-table heat-rate MW is 0.05–0.65 %. The outage files are byte-identical (sha `312a11b8…`).
- **Rule 35:** the year union is 2019–2025 before and after. The incoming stores were verified by `audit_keepers`
  (E13 was the only failure pre-promotion; 0 failures after). The following were all updated:
  - `keepers/PJM.json`;
  - `calibration-complete.json` (keeper, determination, rekeyed, keeper_history);
  - `program-status.json` gate (a) (`check_gate_a_provenance` OK);
  - `status/PJM.js`;
  - the matrix shard: keeper stamp, and `coal_subclass_at_load` O → K.

  Then `prune_iso_runs.py --iso PJM --force-uncite` removed the outgoing keeper's three stores.

## 6. Provenance and retrievability

| year | shard commit (provenance only; the branches are transport) |
|---|---|
| 2019 | `808869cc44fe03e6de3a9a67995074cce825eaf8` |
| 2020 | `e1682c13bbbd10c8c909c12e33b4d339523db189` |
| 2021 | `77877b565af55172c5a7530c6b13c980501fed90` |
| 2022 | `e2aeb98d153a7e3eb8f23b123eb85172f4c0faa7` |
| 2023 | `d26499fd4c28598ff39148946abd576941438f47` |
| 2024 | `d4772ab2c1e7221d6477b3c9da105b80b310bc20` |
| 2025 | `8b5b1355665035b2862d0ff8bf774eb781b90d04` |

**On `main`:** the keeper bundle `rpjm2cs_span` in rule-15 shape (attestation, diagnostics, per-year configs, hourly
sidecars), its sidecar, its payload and the rebuilt bench parts. The per-plant `dispatch/` parquets follow the repo-wide
`.gitignore`. A question that needs them costs a 7-shard re-solve (~30 min per year).

**Shard operations** (`SHARDS.md`), 16 sessions for 7 years:
- v1 containers cloned `main` rather than the unmerged pin, so they failed their pin check.
- 2019 hit a missing `hydro-plant-modes` clean partition. The v3+ prompts add its ~30 s curate step.
- 2020 and 2025 were OOM-killed at load in their first containers.
- 2022, 2023 and 2025 waited up to 2 h 15 m for capacity.

All shards are archived. The leftover `claude/rpjm2cs-*` shard branches cannot be deleted from a session
(rule 33(f)(2)); the owner needs to clear them.

## 7. Still open (not this lane's)

- The coal over-run in 2019–2021 (pjm-168 offer ordering), now fully visible in C1 COAL_BIT.
- C1 CC_REGULAR 2024 (−14.36 TWh), unchanged.
- A concurrent PJM lane (PJM-NEXT, card 1) was solving against `2026-09-25-pjm-r-pjm-2` as its control. That control is
  now pruned from `main`, so its promotion comparison should be re-based on `2026-09-25-r-pjm2-coal-sub`. For 2023–2025
  the two are byte-identical.
