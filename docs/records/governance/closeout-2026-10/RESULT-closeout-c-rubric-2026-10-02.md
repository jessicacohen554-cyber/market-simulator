# RESULT — close-out C: rubric / verdict amendments (v3.14 – v3.17), 2026-10-02

Lane `closeout-c-rubric`, chartered by the Backcast close-out desk (session_017wUwd6xxLRQKAYiT8G722P).
Branch `claude/closeout-c-rubric` from `origin/main` `00648e6e`. **Zero LP.** Rulings: plan
`docs/backcast-closeout-plan-2026-10.md` §5.0 R-6, R-8, R-9, R-13 (verbatim below).

## 1. Determination table (ISO headline, `calibration_verdict.iso_determination`, every registered year)

| ISO | before (v3.13) | after (v3.17) | moved by |
|---|---|---|---|
| **SOCO** | NOT-YET (caveat budget 3/1) | **CALIBRATED-WITH-CAVEATS** (budget 1/1 + 2 reference-definition criteria) | v3.15 (R-8) |
| ERCOT | NOT-YET | NOT-YET | v3.14 (R-6) moved the **carve-out-2023 scope NOT-YET → CALIBRATED**; the ISO stays NOT-YET on forward 2024 C3a −11.4 % and the 2019–2022 validation config (C1 2019/20/22, C3b 2019/20) |
| NWPP | NOT-YET (C4 coal 2023; price unscored) | NOT-YET (C4 coal 2023; **C3a/C3b 2023, 2024 FAIL vs the labelled ELAP**) | v3.16 (R-9) |
| PJM | NOT-YET | NOT-YET | v3.17 (R-13): C3a 2020 FAIL → PASS; C3a/C3b 2022 still FAIL; C1 coal 2019–23 untouched |
| MISO | NOT-YET | NOT-YET | — (W4: attestation already declares the channel; no edit) |
| CAISO | NOT-YET | NOT-YET | — (W4: keeper never used the post-2026-09-05 channel; no edit) |
| NYISO | CALIBRATED | CALIBRATED | — |
| NEISO | CALIBRATED | CALIBRATED | — |
| SPP | NOT-YET | NOT-YET | — |

Scope-level detail (`build_status` / `audit_keepers` read the same function):

| ISO | scope | before | after |
|---|---|---|---|
| ERCOT | forward 2024–2025 | NOT-YET (C3a 2024) | NOT-YET (C3a 2024) |
| ERCOT | carveout-2023 | NOT-YET (C3a −24.5 %, C3b 0.385) | **CALIBRATED** — both read CAVEAT *configuration exception*, off budget, non-downgrading |
| ERCOT | validation 2019–2022 | NOT-YET | NOT-YET (unchanged) |
| SOCO | 2019–2025 | NOT-YET (budget 3/1) | **CALIBRATED-WITH-CAVEATS** |
| NWPP | 2019–2025 | NOT-YET (C4 2023) | NOT-YET (C4 2023, C3a/C3b 2023/2024) |
| NWPP | per-year 2019, 2020, 2021, 2022 | (no-block class) | **PHYSICALLY-CALIBRATED (PRICE UNSCORED)** each — as R-9 rules |

## 2. What each amendment does

**v3.14 — R-6 ERCOT** (*"We had it set up so 2023 was allowed to have a different config because of the ECRS; then that
got eliminated. I'm comfortable with a different config for a single year we know was off."*). New caveat kind
`OWNER-SIGNED CONFIGURATION EXCEPTION` (`calibration_verdict.CONFIG_EXCEPTION_ENTRIES`, `_apply_config_exceptions`).
Exactly two rows: (ERCOT, 2023, C3a) direction *under*; (ERCOT, 2023, C3b) *above band*. Bound to the year's own
solved config (`run_config_2023.json` must carry `ercot_offer_swcap_clip: true` — the declared carve-out signature;
`load_artifacts` now reads every `run_config_<year>.json` of a composed bundle). Governance must pass; never a PASS;
off every budget; not downgrading; named on the basis on every route (NOT-YET included). Citation: Potomac Economics,
*2023 State of the Market Report for the ERCOT Electricity Markets* §II.H / Fig. 13.

| ERCOT 2023 | model | actual (LZ load-weighted RT) | error | IMM counterfactual (ECRS-neutral LW) | model vs counterfactual |
|---|---:|---:|---:|---:|---:|
| C3a | $49.12 | $65.02 | −24.5 % | ≈ $35 (actual $62–65) | +40.3 % |
| C3b | NRMSE 0.385 | — | above 0.20 | monthly bars not digitized (plan §4 row 19) | — |

**v3.15 — R-8 SOCO** (*"scope the caveat budget for a lambda-referenced BA → CALIBRATED-WITH-CAVEATS"*). On an ISO in
`LAMBDA_REFERENCED_ISOS` (SOCO only) a scoped C3a/C3b row is flagged `reference_definition` and its criterion leaves
the single-slot count; it still downgrades. The 2019 C1 COAL_BIT row still spends the slot. `MAX_LEDGERED_CAVEATS` 1.

| SOCO (λ reference) | 2019 | 2020 | 2022 | slot |
|---|---:|---:|---:|---|
| C1 COAL_BIT | −10.6 TWh (scoped) | — | — | spends the 1 slot |
| C3a vs λ | +14.3 % | +14.5 % | −12.0 % | off slot (v3.15), downgrading |
| C3b vs λ | — | — | 0.266 | off slot (v3.15), downgrading |

**v3.16 — R-9 NWPP** (*"WEIM ELAP 2023-06 onward as a labelled imbalance-price benchmark, STOP-gated like SOCO's lambda;
2019–2022 stay PHYSICALLY-CALIBRATED (price unscored)"*). Data: `build_nwpp_weim_price_index.py land-labelled` rebuilt
the footprint series from the committed 15-min store + EIA-930 demand by the same functions the NWPP-13 gate scored,
gated on D1/D2/D4 (all PASS in the committed `gate.json`; D3 — the Mid-C-proxy test, `NO` — is answered by the label).
`actual_lmp_hourly_NWPP.parquet` (2023: 5,137 priced hours from 2023-06-01; 2024/2025: 8,760) →
`derive_actual_lmp --isos NWPP` → `--lw-retrofit` → bench parts 2023–2025 `avgLMP` patched surgically. Scorer:
`PRICE_BENCHMARK_LABEL["NWPP"]`, `C3C_NOT_SCORED["NWPP"]` (an imbalance price's tail is not footprint scarcity —
this C3c posture is this lane's reading of "like SOCO's lambda"; **flagged for desk confirmation**),
`LABELLED_PRICE_REFERENCE_FROM["NWPP"] = 2023`.

| NWPP vs ELAP | model | actual LW | C3a | C3b NRMSE |
|---|---:|---:|---:|---:|
| 2023 (Jun–Dec masked) | $35.93 | $45.72 | **−21.4 % FAIL** | **0.303 FAIL** |
| 2024 | $29.39 | $40.65 | **−27.7 % FAIL** | **0.676 FAIL** (Jan 2024 ELAP $141) |
| 2025 | $32.95 | $32.13 | +2.6 % PASS | 0.179 PASS |

**v3.17 — R-13 PJM** (*"adopt zonal load-weighted C3a for PJM"*). Data intake: PJM DataMiner2 `rt_hrl_lmps` +
`da_hrl_lmps`, `type = ZONE`, **2019-01 → 2025-12, 168 feed-months fetched this session** (every month full; March reads
743 h = the EST spring-forward hour) into the gitignored `data/raw/pjm-zonal-lmp/` (sha256 manifest committed).
`scripts/data/derive_pjm_zonal_lmp.py` reduces them to the 8 model zones (simple mean of constituent transmission
zones, `_PJM_LOAD_ZONE_GROUPS` crosswalk — the NYISO/MISO construction) →
`_validation-source/actual_lmp_zonal_PJM.parquet` (490,560 rows, 0 NaN) → `ZONAL_LW_SOURCES["PJM"]` →
`--lw-retrofit --isos PJM` → bench `avgLMP` patched (0 STALE).

| PJM C3a (model $) | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| model | 28.08 | 23.82 | 39.21 | 65.58 | 31.12 | 31.51 | 45.04 |
| actual, system-hub LW (before) | 26.54 | 21.20 | 38.53 | 74.07 | 29.58 | 31.36 | 45.89 |
| actual, zone-resolved LW (after) | 27.21 | 21.75 | 39.75 | 79.37 | 30.82 | 33.29 | 49.83 |
| C3a before | +5.8 % | **+12.4 %** | +1.8 % | **−11.5 %** | +5.2 % | +0.5 % | −1.9 % |
| C3a after | +3.2 % | +9.5 % | −1.4 % | **−17.4 %** | +1.0 % | −5.3 % | −9.6 % |
| C3b before → after | 0.093 → 0.083 | 0.163 → 0.139 | 0.094 → 0.103 | **0.253 → 0.292** | 0.164 → 0.144 | 0.157 → 0.156 | 0.172 → 0.182 |

PJM 2025 now passes C3a with a 0.4-pt margin; 2022's Elliott object widens on the zonal basis (Dominion/EMAAC carried
the December spike).

**W4 hygiene — no edit, premise did not hold.** MISO `miso280_span` already carries a complete
`authorized_price_tuning` block (channel `offer_curve_by_group`, the 2026-09-05 ruling and the miso-275 CC exemption;
C6 PASS, machine-validated by `_authorized_tuning_finding`) — `SHARD-MISO-closeout-research` §"Bundle facts" reads it
as null in error. CAISO `rcaiso20_A_span` is null **because** the keeper never used the post-2026-09-05 price channel:
its records state "no `authorized_price_tuning` block" at every promotion since caiso-260 (the ×0.92 band cut was
rejected at caiso-267/268); its bands are measured DAM bids or pre-ruling residual rows already in the DOF ledger.
Writing a declaration would assert `set_ex_ante` / `not_swept` facts no record supports, so none was written.

## 3. Verification (all zero LP)

- `pytest tests/scoring tests/curation/test_lw_zonal_registry.py -m "not integration"`: all pass (1,607 + new). New:
  `tests/scoring/test_calibration_verdict_closeout_c.py` (v3.14 / v3.16), PJM cases in
  `tests/curation/test_lw_zonal_registry.py`, v3.15 cases in `test_calibration_verdict_scoped_ledger.py`. Two
  pre-existing tests changed **because the rulings change the behaviour they pinned**: SOCO C3a+C3b / C1+C3a no longer
  read NOT-YET (R-8); NWPP is no longer a no-block region (R-9 — the v3.8 synthetic tests now hide its block).
- Pre-existing, not this lane: `test_bench_classfull_sign[SOCO 2025 OTHER]` (integration) fails against the EIA-923
  Final 2025 landed by #7015 — lane A's 2025 re-bench.
- `check_bench_freshness.py`: 61 parts, **0 STALE** before and after.
- `build_status.py` (all 9) then `--check`: in sync. `audit_keepers.py`: **PASS, 0 failures, 6 warnings** — identical
  to `origin/main` (E11 lineage ×2, E14 package pins ×4).
- `data/raw/reference/nwpp_plant_basis_energy.csv` re-derived (`derive_nwpp_plant_basis_energy.py`, rule 23: its
  source — the NWPP bench parts — changed): only the `source_sha256` provenance column moved; every `twh` is identical.
- Fast tier (`-m "not slow and not integration and not fulldata"`): green except two pre-existing
  `test_gas_offer_zonal_anchor_vintage` cases that fail identically on `origin/main` (NYISO, untouched here) and one
  xdist-only `test_cache_control` flake that passes when run alone.
- `calibration_verdict.py --write-metrics` re-run on r_ercot24_span, soco96_span, nwppnext16c_span, pjmnext16_A_span,
  miso280_span, rcaiso20_A_span, rcaiso20_A_tp_2019_2021.

## 4. Open items for the desk

1. **NWPP C3c posture** — not scored on the ELAP (mirrors SOCO). The ruling text does not name C3c; confirm or rule.
2. **PJM data licensing** — the committed `actual_lmp_zonal_PJM.parquet` is a reduced DataMiner2 derivative, the same
   class as the already-committed hub file (`docs/data-licensing.md` §4, owner review still open).
3. **Plan board §1** is the desk's file and was not edited; SOCO's row now reads CALIBRATED-WITH-CAVEATS.
