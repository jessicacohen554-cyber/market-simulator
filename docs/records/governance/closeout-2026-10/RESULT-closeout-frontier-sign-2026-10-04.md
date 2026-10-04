# RESULT — closeout-frontier-sign: owner-signed frontier rows for PJM, MISO, SPP, ERCOT and SOCO (zero LP)

Lane `closeout-frontier-sign`, chartered by the backcast close-out desk (session_01ERkBTm23ZAP4CTZnJVD9Ss). Branch
`claude/closeout-frontier-sign`, cut from `e857053252d65b893bb171422002b5d75428cc36`. **Zero LP. No solve, no shard.**

## Rulings

- **R-66** (2026-10-04, decision card), verbatim: *"Sign as frontier rows (Recommended)"*. Card: *"One desk lane writes
  the frontier text per ISO from the lanes' findings into each keeper's frontier/ledger record. No determination
  changes; re-opens only on new evidence."*
- **R-65** (downloads), verbatim: *"None right now"*. Rows that wait on an owner download are signed DATA-LIMITED, each
  with its named re-open source.

## What a signed row does

Rubric v3.20 ledgers C3c alone (`calibration_verdict.LEDGERABLE_CRITERIA`). A signed C1 / C3a / C3b / C4 row therefore
**documents** a FAIL and does not reclassify it. Every criterion keeps reporting its own magnitude, and all five ISOs
stay NOT-YET. Nothing was written to any keeper's `calibration_attestation.json`.

## Where the rows live

`frontend/data/backcast/keepers/<ISO>.json` → `frontier` with `scope: "rows"`, `declared: "2026-10-04"`, the ruling, a
contract note and one object per row (`id`, `criterion`, `years`, `magnitude`, `class`, `object`, `evidence`, `levers`,
`why`, `reopen`). Each ISO's `docs/calibration-log/<iso>.md` carries the same rows. PJM's stale 2026-07-31 pjm-142 note
(a CALIBRATED keeper since superseded) is replaced.

**Display.** The Calibration Status page used to read any declared frontier as "frontier achieved": a FRONTIER badge,
and a WITH-CAVEATS headline upgraded to CALIBRATED (`effectiveDet`). A `scope: "rows"` block now renders a
**FRONTIER ROWS** badge with the row list and never upgrades the headline
(`docs/codebase-site/js/calibration-status.js`, display only).

## Rows signed

| ISO | row | criterion / years | class | re-opens on |
|---|---|---|---|---|
| PJM | PJM-F1 | C1 COAL_BIT 2019/20/21 (+19.73 / +12.74 / +16.72 TWh) | MODEL-CLASS | unit-identified PJM offer or RT commitment records; an online-gated sync-reserve mechanism that clears rule 19; a decommitment form that separates 2019–21 from 2023/24 at zero LP |
| PJM | PJM-F2 | C1 CT_PEAKER 2021 (signed R-36) | MODEL-CLASS, inert on keeper | unit-level BOR / RT-commitment records, or published local reliability requirements |
| MISO | MISO-F1 | C1 ST_GAS 2019 (−8.71 TWh), VLR steam | DATA-LIMITED | MISO Max Gen declaration history (OATI PDF, R-15 0b), or a published VLR pocket MW |
| MISO | MISO-F2 | C1 CC_REGULAR 2021 (−8.15 TWh) + C3b 2021 fall share (0.219; Uri routed) | MODEL-CLASS | a measured cumulative stock path that holds fall coal without releasing summer/2022 coal, or a unit-level record of the fall-2021 conservation adders |
| MISO | MISO-F3 | C3a 2020 (+10.2 %), low-load level shift with West/Plains congestion G | MODEL-CLASS | RO-1 congestion split with a published constraint set, or a measured coal low-load offer form within the regulated scope |
| SPP | SPP-F1 | C3a / C3b 2024 (−11.2 % / 0.216) | DATA-LIMITED | SPP RTBM binding-constraint files 2023–24 with effective-limit columns, or SPP 2024 planned transmission outages; ST_GAS minor |
| SPP | SPP-F2 | C3a 2019/20 (+12.3 / +27.7 %) + C3b 2020 (0.345) | MODEL-CLASS (commitment state) | a commitment mechanism that also lifts 2023–25, or an owner ruling re-opening West/East (SPP-93) |
| SPP | SPP-F3 | C1 CC/PRB 2021/22 + C4 gas 2022 (0.313) | DATA-LIMITED (basis pending W5) | the W5 basis ruling, or STB EP 724 rail data |
| SPP | SPP-F4 | C3c 2023–25 (0 h vs 42 / 59 / 68) | MODEL-CLASS (5-minute scarcity) | caveat route opens by itself under rule 22 once SPP-F1 closes; as a lever, only a measured sub-hourly scarcity input |
| ERCOT | ERCOT-F1 | C1 CC/PRB 2019/20 + C3b 2019/20 (0.216 / 0.208) | DATA-LIMITED | R-7 intake (G1 NP3-965 SCED coal TPO 2019-01→2022-12 + G3 NP6-576-ER), or the Q5 CSV migration paired with a compensating-error lane |
| ERCOT | ERCOT-F2 | C3a 2024 (−11.3 %) | DATA-LIMITED | same as ERCOT-F1 |
| SOCO | SOCO-F1 | C1 CC_REGULAR 2019 (+3.97 TWh, +3.2 pp) | DATA-LIMITED | Georgia PSC FCR / Alabama ECR fuel testimony |

Each row's evidence chain, adjudicated levers with matrix cells, and model-class or data-limited reasoning is in its
keeper shard.

## Re-check: PJM CT_PEAKER 2021 (R-36)

On keeper `2026-10-03-closeout-pjm-nuc-keeper`, C1 CT_PEAKER 2021 reads **−7.92 TWh, PASS** (it was −8.07 FAIL on
`2026-10-02-w0-pjm-fix2`, where it was signed). The R-36 entry was carried into
`results/calibration/closeout_pjm_nuc_full_span/calibration_attestation.json` verbatim at the R-52 promotion
(`remeasured: false`, because fuelmix is not ledgerable). It is not mis-keyed and was not edited. It documents no live
FAIL and is inert. If a later keeper fails CT 2021 again, the signed text applies as written.

## Verification

- `build_status.py --iso PJM MISO SPP ERCOT SOCO`. Semantic diff of the five status parts: only `generated` and
  `keeper.frontier` change. The other four ISOs are unchanged, and every determination stays NOT-YET.
- `audit_keepers.py --check`, `build_status.py --check`, `check_registry_payload_parity.py`, `check_mechanism_matrix.py`,
  `check_rubric_freeze.py --base e857053`: see the PR.
- Untouched: `calibration_verdict.py`, the rubric doc and constants, `calibration-complete.json`, every keeper
  designation, every attestation and every matrix cell.

## Open owner items (rule 37: rubric questions, not landed here)

1. **SOCO step-0 caveat budget** (closeout-SOCO-w2 §Verdict step 0; R-8): the budget for a lambda-referenced BA. It
   cannot change SOCO's determination today, because CC_REGULAR 2019 fails on its own.
2. **SOCO step-3 ledger-text scope sentence** (closeout-SOCO-w2 §3): one sentence added to `_C3A_REASON` and the C3b
   2022 reason in `calibration_verdict.py`. Text only, and zero-LP identical for every ISO. It needs its own PR on an
   owner ruling.
3. **SPP C3c 2023–25 attestation entry.** SPP-F4 is prose. A `"kind": "model-class"` C3c entry in the SPP attestation
   would be applied by the scorer, so the C3c FAIL rows would read CAVEAT. That would change the status part, so it was
   not done. While the train C3a/C3b 2024 rows fail, it would not change the determination.
