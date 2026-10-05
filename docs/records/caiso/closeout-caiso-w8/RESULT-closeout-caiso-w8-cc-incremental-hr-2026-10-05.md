# RESULT closeout-CAISO-w8: CC_REGULAR econ tranches at the measured incremental heat rate (2026-10-05)

**Records.** `PRECOMMIT-closeout-caiso-w8-cc-incremental-hr-2026-10-05.md` (bars, kills, G-DRIFT);
`_cc_linear_census.csv`; `_verdict_w8.json` (this run, rubric 3.20).

**Runs.**
- **Control:** the w6 probe `2026-10-05-closeout-caiso-w6-a1` (`../closeout-caiso-w6/_verdict_w6.json`), on the same
  bench parts. This registration re-rendered no bench part.
- **Arm A1:** probe **`2026-10-05-closeout-caiso-w8-a1`** (bundle `results/calibration/closeout_caiso_w8_a1_span`).
  Recipe: the w6 recipe + `cc_econ_incremental_hr=true`. The CC offer bands are unchanged (rule 1(c), declared).
- **Registration:** on `claude/closeout-caiso-w8` only (E13). The code, the derive and its artifact stay on that branch
  (desk ruling, rule 26).

**Verdict: T1 MET, but K1 FIRES (C1 CC_REGULAR 2020 and 2021 PASS → FAIL). Matrix cell → R. NOT PROMOTED, no slot
request.**

- C3a 2021 moves from +11.0 % to **+8.8 %** (FAIL → PASS on the probe), and C3a improves by 1.4–2.5 pp in every scored
  year.
- C1 CC_REGULAR 2020 moves from +4.00 to **+6.24 TWh** (band ±4.66). 2021 moves from +2.67 to **+6.59 TWh** (band ±4.89).
- C4 gas NRMSE 2020 / 2021 crosses 0.30 (0.293 → 0.303, 0.299 → 0.304). This is the reported K4.
- The determination stays NOT-YET. The probe reads "governance UNATTESTED"; on the metrics, C1 CC_REGULAR 2020/21 and
  C4 gas 2020/21 join the fail set.

## Solves

Seven year-isolated shards, pinned to `725554dcecb3d5c85cd8259c8a5598620e80ab20`. Each leg was fetched and verified
before its shard was archived: parent `725554dc`; 17 files, including `dispatch/<y>_P1.parquet`;
`cc_econ_incremental_hr = true`. The legs were composed by `_closeout_caiso_w1_compose_span.py` (keeper
`closeout_caiso_w1_a2_span` + 6 arm fields, one solve surface, one source SHA). Unserved energy is 0 in every leg.
Shards report 21 (2019) to 24 (2020–25) CC plants repriced.

| Year | A1 shard commit (provenance; branch `claude/closeout-caiso-w8-a1-<y>`) |
|---|---|
| 2019 | `716a9d71cde62dedd236d3d89ffe5c2e2896f988` |
| 2020 | `389ec75efa61db3fed111f15fd8a5f899cd9a3f3` |
| 2021 | `a6e289be9b432e95578b2d5fd901c2f6b5dc7423` |
| 2022 | `581a1125994c94d1b7daa0aa22796045d1a1abf0` |
| 2023 | `8060e3b766cfab8c3b85d09e4f7e4cfc38c1876f` |
| 2024 | `c54611a9a0d816a359cf3984db916c0270f1bcc9` |
| 2025 | `8fdbd7730a41249afe61e7fbcf8c2168c3cc5032` |

The per-leg legitimacy gate reads FAIL (D-1 ST_GAS, D-4 CHP steam unit conduct) in every leg. The w6 control fails the
same D1/D4 rows; it is not caused by this arm.

## 1. Gate table (w6 → w8; every scored record whose status or magnitude moved)

| Criterion | Year | w6 | w8 | Status |
|---|---|---|---|---|
| **C3a price mean (T1)** | **2021** | +11.0 % | **+8.8 %** | **FAIL → PASS** |
| C3a | 2022 / 23 / 24 / 25 | +7.1 / +6.8 / +5.5 / +5.1 % | +4.9 / +4.3 / +3.7 / +3.8 % | PASS (improves) |
| C3b NRMSE | 2021 … 2025 | 0.134 / 0.119 / 0.113 / 0.116 / 0.084 | 0.114 / 0.103 / 0.093 / 0.113 / 0.078 | PASS (improves) |
| **C1 CC_REGULAR (K1)** | **2020** | +4.00 | **+6.24** | **PASS → FAIL** (±4.66; share +3.1 pp) |
| **C1 CC_REGULAR (K1)** | **2021** | +2.67 | **+6.59** | **PASS → FAIL** (±4.89) |
| C1 CC_REGULAR | 2019 / 22 / 23 / 24 / 25 | −2.94 / +0.01 / −1.94 / −2.50 / +0.06 | −2.11 / +2.57 / +0.33 / −0.70 / +1.61 | PASS |
| C1 CC_CHP | 2019 … 2025 | +0.59 … +1.14 | +0.39 … +1.00 | PASS |
| C1 CT_PEAKER | 2019 … 2025 | −1.59 / −2.07 / +1.22 / −0.77 / −1.37 / −1.23 / −1.77 | −1.61 / −2.10 / +1.09 / −0.90 / −1.63 / −1.76 / −1.98 | PASS |
| **C4 gas NRMSE (K4)** | **2020 / 2021** | 0.293 / 0.299 | **0.303 / 0.304** | **PASS → FAIL** (reported kill) |
| C4 gas NRMSE | 2019 / 22 / 23 / 24 / 25 | 0.294 / 0.250 / 0.234 / 0.237 / 0.283 | 0.284 / 0.224 / 0.209 / 0.212 / 0.236 | PASS (improves) |
| C3c tail hours | 2022 / 2023 | 509 / 45 | 500 / 25 (actual 510 / 47) | PASS (2023 at 0.53×, watch) |
| CO2 | 2019 … 2025 | −13.6 / −4.1 / −4.2 / −9.8 / −7.5 / −5.7 / −2.8 % | −12.4 / −1.4 / +0.1 / −7.0 / −4.9 / −4.3 / −0.8 % | 2023 CAVEAT → PASS; the rest unchanged in status |
| C8 CC_REGULAR forced | 2019 … 2025 | 7.5–12.7 % | 5.7–11.2 % | PASS (K3 clear) |

**Kills.** K1 fires (2020 and 2021). K2 clear: no C3a or C3b cell moves PASS → FAIL; every one improves. K3 clear.
K4 (reported) fires in 2020 and 2021. K5: C2 unchanged.

## 2. Mechanism readout (P1 class sums, TWh, w8 − w6)

| Year | CC_REGULAR | import | CC_CHP | CT_PEAKER |
|---|--:|--:|--:|--:|
| 2019 | +0.98 | −0.77 | −0.21 | −0.02 |
| 2020 | +2.36 | −2.07 | −0.26 | −0.03 |
| 2021 | **+3.99** | **−3.65** | −0.16 | −0.13 |
| 2022 | +2.73 | −2.40 | −0.16 | −0.13 |
| 2023 | +2.37 | −1.98 | −0.10 | −0.26 |
| 2024 | +1.80 | −1.17 | −0.06 | −0.53 |
| 2025 | +1.55 | −1.27 | −0.12 | −0.21 |

**What moved the price.** Cheaper CC econ steps displace the hub-priced DSW/PNW import rungs almost one for one
(65–91 % of the added CC energy; 88–91 % in 2020–22). Those rungs set λ in about 80 % of 2021 hours (w7), so removing marginal rung volume
lowers λ. The price gain is real in the LP, but it is bought with import volume.

**Why it is not admissible as a fix.** The w6 overnight import volume already matched EIA-930 (w7: 8.67 GW each). w8
takes 3.65 TWh of imports out of 2021 and puts it on CC_REGULAR, which the CEMS-anchored C1 bench refuses in 2020 and
2021. Rule 1 forbids reaching a price through a mechanism that breaks a structurally measured quantity; the arm's price
fit comes from the merit-order swap, not from a better level on the price-setting unit.

## 3. Reading for the ledger (DRAFT frontier row; signing is the owner's act, R-66)

> **CAISO C3a 2021 (+11.0 % on the w6 probe; reference-coverage caveat on the keeper, R-40).** The level gap sits at
> the merit boundary between in-state CC_REGULAR and the hub-priced DSW/PNW import ladder. Pricing the CC econ steps
> at their measured CEMS incremental heat rate (closeout-CAISO-w8, zero DOF) closes it (+8.8 %), but only by
> displacing 1–4 TWh/yr of import volume that already matched EIA-930, which breaks C1 CC_REGULAR 2020/21 and C4 gas
> 2020/21. Re-pricing the import rungs at the RT intertie print is circular (w7, rule 13). No admissible lever moves
> the level without moving the measured CC/import split. Data-limited: RT reference coverage in 2021 is 65 %, and
> CAISO's in-state CC offers and intertie bid stacks are not public.

CAISO has no frontier block in `keepers/CAISO.json`, so this text is a draft only. It goes into the CAISO calibration
log for the owner to sign or refuse.

## 4. Owner question (rule 1(c), raised separately as the desk directed)

The arm moved the price through measured incremental cost, not through the authorized bands, and the bands were left
unchanged. The result does **not** point to a band re-set: lowering CC econ_low/econ_high would cause the same
CC-for-import swap and break the same C1 cells. No band question is raised.

## 5. Matrix and records

- `cc_econ_incremental_hr` CAISO cell: **U → R** (this RESULT; on `claude/closeout-caiso-w8`). The row and the other
  shards' cells live on that branch only, with the code (the row can land only with its field).
- Lever queue §5.2 CAISO entry and the draft frontier row in `docs/calibration-log/caiso.md` land on `main` via the
  records PR, with this RESULT, the PRECOMMIT, the census and `_verdict_w8.json`.
- **DO-NOT-REDO:** pricing CC_REGULAR econ tranches at incremental HR in CAISO while the import ladder stays at the
  incumbent depth. It re-opens only with a measured import-ladder depth that holds the CC/import split, or with new
  in-state CC offer data.

## 6. Retention (rule 31)

The seven leg bundles are on their shard branches (above); the composed span is local and gitignored. The probe is
not a promotion candidate (K1). The span and legs will not survive this container; the shard branches carry every leg
byte for byte. Branch deletion is the owner's (sessions get 403).
