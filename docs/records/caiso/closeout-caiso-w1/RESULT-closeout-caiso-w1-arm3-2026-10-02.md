# RESULT closeout-CAISO wave 1, arm 3: `caiso_ra_min_load_frac` 0.26 → measured 0.570, PROMOTED (2026-10-02)

PRECOMMIT: `PRECOMMIT-closeout-caiso-w1-arm3-ra-min-load-2026-10-02.md` (desk ruling: arm 3 first). Released by the
desk on 2026-10-02 after the W0 CAISO keeper promotion (`#7044`, `eec4eb5c`).

- **Control:** `2026-10-02-w0-caiso` (bundle `w0_caiso_span`, 2019–2025 one span).
- **Arm:** `--set caiso_ra_min_load_frac=0.570`. That is the only delta.
- **Keeper:** **`2026-10-02-closeout-caiso-w1-arm3`** (bundle `results/calibration/closeout_caiso_w1_a3_span`).

## Solves (rules 32, 34, 36)

Seven year-isolated shards, all pinned to `eec4eb5ccba5b138a4befb047042c00b2eafb84e` (step-0 checkout) in environment
"Full access". Every leg was verified before its shard was archived:
- `dispatch/<y>_P1.parquet` present, and the bytes in hand;
- parent commit `eec4eb5c`;
- `run_config.json` recording `caiso_ra_min_load_frac: 0.57`.

Leg provenance (transport only; the composed bundle is what lands on `main`):

| Year | Shard commit | Branch |
|---|---|---|
| 2019 | `0436be77c414a0b18783523075a8e5994255b070` | `claude/closeout-caiso-w1-a3-2019` |
| 2020 | `95b2906b345fa2970b9d63de5eb578c6b99ed49f` | `claude/closeout-caiso-w1-a3-2020` |
| 2021 | `a7eb2a050cde957d411aca11fd30de2d74b02857` | `claude/closeout-caiso-w1-a3-2021` |
| 2022 | `780036c2707a7bd221102ae809b419353192a157` | `claude/closeout-caiso-w1-a3-2022` |
| 2023 | `09c11f6d29e90fb7e8c5440dd15b168933ae8093` | `claude/closeout-caiso-w1-a3-2023` |
| 2024 | `95ca03a86eead52e5df6774460beecb04666d00d` | `claude/closeout-caiso-w1-a3-2024` |
| 2025 | `efc85cb66287739d3e151643b079d9255459f8c2` | `claude/closeout-caiso-w1-a3-2025` |

Composed at zero LP by `scripts/probes/_closeout_caiso_w1_compose_span.py`. It is the W0 composer's construction with
the arm check:
- each leg equals `w0_caiso_span`'s recorded config for its year on every field except `caiso_ra_min_load_frac = 0.57`;
- all legs share solve-surface fingerprint `95343377bacdb2ed`, the same as the control;
- all legs share source `eec4eb5c`.

`legitimacy_diagnostics.json` was regenerated over the composite.

## Gate table (control → arm), every moved record

| Criterion | Year | W0 keeper | Arm 3 | Bar | |
|---|---|---|---|---|---|
| **Determination** | all | **NOT-YET** (C1, C3a, C4) | **NOT-YET** (C1, C3a, C4) | does not fall | ✓ |
| C1 CC_REGULAR | 2019 / 2020 / 2021 | +9.99 / +16.28 / +8.70 FAIL | +10.19 / +16.44 / +8.69 FAIL | (fold, report) | |
| C1 CC_REGULAR | 2022 / 2023 / 2024 / 2025 | +1.23 / −0.88 / +0.02 / −0.51 | +1.02 / −1.16 / +0.03 / −0.59 | \|Δ\| ≤ 0.5 TWh, PASS | ✓ (max 0.28) |
| C3a vs RT | 2021 | +12.8 % FAIL | +12.8 % FAIL | \|Δ\| ≤ 1 pp | ✓ |
| C3a vs RT | 2022 / 2023 / 2024 / 2025 | +8.2 / +7.5 / +5.9 / +6.0 % | +8.5 / +7.9 / +6.1 / +6.3 % | \|Δ\| ≤ 1 pp; 2025 ≤ +10 % | ✓ (max +0.4) |
| C3b NRMSE | 2021–2025 | 0.149 / 0.117 / 0.116 / 0.117 / 0.088 | 0.150 / 0.121 / 0.118 / 0.120 / 0.091 | PASS | ✓ |
| C3c | 2021 | 90 h vs 27 h CAVEAT | 89 h vs 27 h CAVEAT | — | |
| C3c | 2024 (ledgered) | 0 h vs 35 h CAVEAT | 0 h vs 35 h CAVEAT | — | |
| C4 gas r / NRMSE | 2019 / 2020 / 2021 | 0.889/0.383, 0.89/0.402, 0.855/0.351 FAIL | 0.888/0.385, 0.89/0.403, 0.855/0.351 FAIL | (fold, report) | |
| C4 gas r / NRMSE | 2022 / 2023 / 2024 | 0.907/0.248, 0.905/0.244, 0.918/0.247 | 0.909/0.248, 0.907/0.245, 0.92/0.244 | PASS | ✓ |
| **C4 gas NRMSE** | **2025** | 0.291 | **0.286** | ≤ 0.30 | ✓ |
| C8 CC_REGULAR forced | 2019–2025 | 7.4 / 5.0 / 5.9 / 7.2 / 7.5 / 9.1 / 12.3 % | 8.6 / 5.9 / 6.1 / 7.0 / 7.0 / 9.6 / 12.4 % | ≤ 30 % | ✓ |
| C6 governance | — | PASS | PASS | — | |

Load-weighted model price, 2019–2024 ($/MWh): 38.70 → 38.60, 35.56 → 35.48, 56.30 → 56.27, 91.43 → 91.70,
58.24 → 58.46, 36.71 → 36.76. CC_REGULAR |ΔTWh| ≤ 0.29 every year, with imports taking the opposite sign. The C8
response (≤ +1.2 pt) confirms the caiso-119 reading: the bridge level is capped, so a +119 % fraction moves floored
energy only marginally. It sits far inside the upper bound pre-registered in PRECOMMIT §3 (26.8 % in 2025).

**Decision (pre-registered, R-11 "promoted only if nothing regresses"): PROMOTE.** Every bar holds. Rule 21: the DOF
ledger keeps its 10 entries (no addition). The unledgered, residual-identified 0.26 is retired. Its stale "CEMS 0.259"
justification is deleted from `pipeline/backcast_config.py` (rule 26), and the CAISO backcast default is now 0.570.

## Promotion notes (two tooling items for the desk)

1. **`promote_keeper.py` step order defect.** Step 8 (`audit_keepers --check`) runs before step 9 (prune), but audit
   E13 fails on the not-yet-pruned outgoing keeper. Any promotion over a registered keeper therefore stops at step 8.
   Every other audit check passed. I ran steps 9 → 8 → 10 by hand in that order: prune `2026-10-02-w0-caiso` (the
   promotion ruling authorises it), re-audit to `PASS: 0 failure(s)`, then parity. The tool is not patched here.
2. **The C3c 2024 ledger entry is not carried by the fresh attestation.** `promote_keeper` writes a new governance
   block when the bundle has none, and it drops the outgoing keeper's `exceptions`. C3c 2024 then scored FAIL instead
   of the ledgered CAVEAT. I carried the entry over in `calibration_attestation.json`, re-measured on this bundle
   (0 h vs 35 h, identical), and the determination read back the W0 keeper's exactly.

The seven per-year leg directories stay on local disk only, gitignored via `.git/info/exclude` and never `rm`'d
(rule 31). Their bytes are in the shard commits above and in the composed span.
