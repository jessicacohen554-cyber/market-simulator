# PRECOMMIT — NWPP-NEXT-26: CAISO_NEVP priced only after Harry Allen–Eldorado, 2019–2025

Written before any solve. Phase 0: `FINDING-nwppnext26-nevp-hae-phase0-2026-10-03.md`. Owner card 2026-10-03:
"Serve pre-HAE".

## The arm

Keeper `2026-10-03-nwpp-next-25-served` (bundle `results/calibration/nwppnext25_span`, committed at the pin), replayed
with ONE key: `--set nwpp_seam_in_service_vintage=true`. Seven year-isolated shards (rule 36) at pin
`30c0e01790f3ee4085042193be816d47cc704c31` (branch `claude/nwppnext26-pin`); prompts in `nwppnext26/shards/`.

## What the arm changes

- **2019** (all 8,760 h) and **2020** (5,351 h before 2020-08-12 07:00 UTC): the CAISO_NEVP net flow is capped at 0
  and NEVP's measured CISO leg is served at SNV. 2020 keeps 3,409 priced hours.
- **2021–2025:** demand, caps and LP identical to the keeper — five control legs; any class-energy move > 0.01 TWh
  there is a defect, not a result.
- **Expected P1 demand, TWh (five zones ±0.05; per zone ±0.10):**

| year | total | NW | OR | INLAND | EAST | SNV |
|---|---:|---:|---:|---:|---:|---:|
| 2019 | 272.560 | 117.58 | 38.53 | 40.33 | 44.96 | 31.16 |
| 2020 | 274.340 | 118.53 | 39.85 | 40.32 | 46.11 | 29.53 |
| 2021–2025 | keeper | keeper | | | | |

## Gates (set ex ante)

- **(a) Governance.** `scenario_config` diff = exactly `[('nwpp_seam_in_service_vintage', None|False, True)]`; zero
  free parameters (a date with a FERC citation); DOF ledger unchanged; C6 must pass. Attestation:
  `scripts/gen_nwppnext26_attestation.py` = the NEXT-25 generator + this key.
- **(b) Verdict diff vs the keeper, same bench render, every record at full magnitude.** Hypothesis records:
  C1 CC_REGULAR 2019 +12.73 FAIL (predicted +4…+9) and 2020 +7.51 PASS (predicted −2…−5 TWh); NEVP seam net export
  2019 (10.47 → ~0, measured −0.30) and 2020 (11.98 → ~4–7, measured 3.11); SNV gas 2019/2020 toward NEVP EIA-930
  (22.2 / 22.8); C4 gas 2019 (r 0.649). Watch: COI exports 2019/2020 (re-routing), CT_PEAKER / ST_GAS 2019–2020,
  C4 coal 2019/2020, C1 COAL_* 2019/2020.
- **(c) Rule 20 / legitimacy.** D-2 forced energy 0 in every class-year; D-1 failure count vs the keeper's 16.

## Promotion rule

Owner standing ruling: promote if structural integrity improves, even if a gate regresses. The arm removes a priced
path that did not physically exist (rule 14) and keeps every counterparty priced or served, never both (rule 19).
Promotion goes on ONE owner card; the close-out desk (session_01ERkBTm23ZAP4CTZnJVD9Ss) is told the pin and the slot.

## G-DRIFT against the keeper's pin (d3965589)

`git diff d3965589 origin/main -- src scripts/run_* scripts/replay_keeper.py scripts/lib` is empty (main moved by
NEXT-25 records and promotion artefacts only). This branch's hunks on the backcast path are all INERT with the key
off: every new branch in `envelopes`, `demand`, `run_calibration`, `run_calibration_full` and `runner` is gated on
`nwpp_seam_in_service_vintage` (masks are all-true / all-false off, reproducing the keeper's year gate exactly;
`test_nwpp_seam_in_service_vintage.py`, fast lane 11,465 passed). No control solve (rule 29b).
