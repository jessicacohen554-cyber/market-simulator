# R-PJM2-CS shards — pinned afd8cbd61f7e31c7a55807e9219ddbde712372be (launched 2026-09-25 03:56Z)

| year | session | branch | out-dir |
|---|---|---|---|
| 2019 | session_01DERaDzyjQpBjdQ6oP7myck | claude/rpjm2cs-2019 | results/calibration/rpjm2cs_2019 |
| 2020 | session_01YKaZ1ifjdaVSqHELeqguLV | claude/rpjm2cs-2020 | results/calibration/rpjm2cs_2020 |
| 2021 | session_014NRRBbiyk71as2NdRQotiU | claude/rpjm2cs-2021 | results/calibration/rpjm2cs_2021 |
| 2022 | session_01KBmhzDMnPn1yPswu7DW21r | claude/rpjm2cs-2022 | results/calibration/rpjm2cs_2022 |
| 2023 | session_01EjQ3r5YJM2c9cdnjPedGQg | claude/rpjm2cs-2023 | results/calibration/rpjm2cs_2023 |
| 2024 | session_01KGfbCcpVFZ19EfduPJrsbU | claude/rpjm2cs-2024 | results/calibration/rpjm2cs_2024 |
| 2025 | session_01TA5TD6XPdzKDFizdmvPqqk | claude/rpjm2cs-2025 | results/calibration/rpjm2cs_2025 |

## v2 relaunch (2026-09-25 04:20Z)

The v1 containers cloned `main` rather than the pin (the pin sat on an unmerged branch at launch; it has since
merged, so it is an ancestor of `main`). Five v1 shards hit hard stop 1 and stopped cleanly without solving; the
2022/2023 v1 shards never left PENDING. All seven v1 sessions are archived. v2 adds a sanctioned
`git fetch origin <pin> && git checkout --detach <pin>` step before the HEAD check.

| year | v2 session |
|---|---|
| 2019 | session_01HJo24HdeKDGyidE5MiqwJR |
| 2020 | session_01FCjc6NkbHzhGkqVxZKTvju |
| 2021 | session_01LdbB3sMUVMNb6XdieRvFmn |
| 2022 | session_017ZCEAycDiroTmy7LHhqojD |
| 2023 | session_01No7EwGTkMgTXYqitUkXcd5 |
| 2024 | session_01BV7NUfrhPBwSdyxwQmXBFR |
| 2025 | session_01KGmFh8jcezDB341dTvz4DH |

## v2 outcomes / v3 (2026-09-25 04:48Z)

- 2019 v2: blocked — `hydro-plant-modes` clean partition absent (its curate script runs in ~30 s, no LP; the
  shard's "LP solver OOM" reading was a misdiagnosis). Archived.
- 2020 v2: solve OOM-killed 69 s in (container ceiling reported 18.4 GiB vs the preflight's 24 GiB swap
  target). Archived.
- 2021 / 2024 / 2025 v2: solving. 2022 / 2023 v2: waiting for container capacity.
- v3 relaunch for 2019 / 2020 adds the hydro-modes curate step and a one-heavy-process rule:
  2019 `session_01CNy1qVn74MRUpx1Qr8MV3V`, 2020 `session_012qwxpdikWgHduvgJhSRc9V`.

## Legs landed (verified 2026-09-25 05:0xZ)

| year | shard commit (provenance) | files | recipe check | class TWh vs keeper |
|---|---|---|---|---|
| 2021 | `77877b565af55172c5a7530c6b13c980501fed90` | 17 (incl. `dispatch/2021_P1.parquet`) | OK (bare COAL folded) | COAL 16.97 → 0; COAL_BIT +11.25; COAL_PRB +4.98 (Waukegan); coal family total −0.73; CC_REGULAR +0.60 |
| 2024 | `d4772ab2c1e7221d6477b3c9da105b80b310bc20` | 17 (incl. `dispatch/2024_P1.parquet`) | OK | every class byte-equal to the keeper (as G-DRIFT predicted) |

## 05:19Z — 2019 / 2020 landed; 2022 / 2023 / 2025 relaunched (v3)

| year | shard commit (provenance) | files | class TWh vs keeper |
|---|---|---|---|
| 2019 | `808869cc44fe03e6de3a9a67995074cce825eaf8` | 17 | COAL 18.22 → 0; COAL_BIT +16.32; COAL_PRB +3.76; COAL_WC +0.16; coal family +2.02; CC_REGULAR −1.32; CT_PEAKER −0.24 |
| 2020 | `e1682c13bbbd10c8c909c12e33b4d339523db189` | 17 | COAL 7.33 → 0; COAL_BIT +6.50; COAL_PRB +3.17; coal family +2.29; CC_REGULAR −1.28; CT_PEAKER −0.42 |

Recipe check OK on 2019/2020/2021/2024. 2025 v2 failed at load (same OOM pattern as 2020 v2); 2022/2023 v2 never
left PENDING. v3: 2022 `session_01KsL3ruKYWorRHSxcdBLygT`, 2023 `session_0111UC4YT7exYybZY7fGPj57`,
2025 `session_01TkRN51LFBitT7ZCp1GBq7R`. Shards whose bytes are in hand are archived.

## 06:07Z — 2022 landed

| 2022 | `e2aeb98d153a7e3eb8f23b123eb85172f4c0faa7` | 17 | COAL 3.70 → 0; COAL_BIT +3.17; coal family −0.53; CC_REGULAR +0.25; CT_PEAKER +0.11 |

5 of 7 legs verified on parent disk (2019–2022, 2024). 2023 / 2025 v3 shards still PENDING on container capacity.

## 07:35Z — 2023 / 2025 v3 never left PENDING (2 h 15 m) — recreated as v4

2023 `session_013VY4v2cq2U1e6We1cVfVJJ`, 2025 `session_013RFEKXe9966zYTWqu9uPw1`.
