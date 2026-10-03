# RESULT — closeout-PJM-impl: owner rulings R-36 / R-37 applied to the PJM keeper ledger (zero LP)

**Keeper:** `2026-10-02-w0-pjm-fix2`, bundle `results/calibration/w0_pjm_span/`.

**Determination:** NOT-YET before and after.

**What was not done:** no LP, no shard, no promotion, no ScenarioConfig change. The only matrix edit is
evidence text on the PJM shard; no cell moved.

## Rulings (verbatim, owner cards 2026-10-03; `docs/backcast-closeout-plan-2026-10.md` §5.0)

- **R-36.** *"Sign CT 2021 now; hold COAL_BIT 1b for NEXT-31"*
- **R-37.** *"Documented FAIL; no re-open"*

## What changed

The entries were written from the merged records, because no HANDOFF was written (desk instruction, 2026-10-03).
The records are:
- `DRAFT-closeout-pjm-2-frontier-text-2026-10-03.md` Statement 2;
- `FINDING-closeout-pjm-2-2025-regression-attribution-2026-10-03.md`;
- `RESULT-closeout-pjm-2-heatwave-reserve-census-2026-10-03.md`.

| file | change |
|---|---|
| `results/calibration/w0_pjm_span/calibration_attestation.json` | `exceptions`: `[]` → 3 entries. No other field changed. |
| `frontend/data/backcast/status/PJM.js` | Rebuilt with `build_status.py --iso PJM`. |
| `docs/codebase-site/data/mechanism-matrix/PJM.js` | R-37 evidence prepended on `reserve_pergen`. |
| `docs/calibration-log/pjm.md` | New closeout-PJM-impl entry. |
| `DRAFT-closeout-pjm-2-frontier-text-2026-10-03.md` | Dated hold note: "held for NEXT-31 (R-36)". |

### The three ledger entries

| criterion | year | key | `kind` / `classification` | magnitude |
|---|---|---|---|---|
| `fuelmix` (C1) | 2021 | `CT_PEAKER` | `kind: "model-class"` (signed frontier) | −8.07 TWh |
| `price_mean` (C3a) | 2025 | — | no `kind`; `classification: "MODEL MISS — DOCUMENTED FAIL (owner ruling R-37) …"` | −11.6 % |
| `price_shape` (C3b) | 2025 | — | the same | NRMSE 0.222 |

**How the `kind` was chosen.**
- **Signed model-class frontier.** The rubric's kind for this is `"model-class"` (v3.0). This follows the form of
  `closeout_ercot_l1_span`: criterion / year / kind / magnitude / reason, plus `klass` for the C1 sub-key.
- **Documented FAIL.** The rubric has no kind for it. The repo's existing representation is a record-only entry with
  no `kind` and a free-text `classification: "MODEL MISS …"`. Precedents:
  - `w0_neiso_span`: `storage` 2025, and `fuelmix` oil 2020–2025 ("NOT ledgered as a caveat");
  - `w0_miso_span`.
- **No rubric amendment was needed.**

**Why nothing is reclassified.**
- Under rubric v3.1, `LEDGERABLE_CRITERIA = {"price_tail"}`, and `_apply_ledger` ignores every other criterion
  fail-closed.
- C1 is also load-bearing, so the v3.0 tier guard would refuse the model-class entry on its own.
- The entries document the FAILs and change no status.
- `promote_keeper.py` carries non-C3c entries forward verbatim as "record only".

**Each entry's `reason` carries:**
- the ruling, verbatim;
- the mechanism and evidence (CT: IMM 2021 SOM Table 4-3, 92.8 % of balancing credits);
- the exhaustion record or attribution;
- the re-open trigger: for CT, a measured commitment-state input; for 2025, the frontier candidate, an online-gated
  reserve pool.

## Status part: before and after

The before is `origin/main` at merge, `generated 2026-10-03 02:12`. The comparison is a structural JSON diff.

| path | before | after |
|---|---|---|
| `keeper.determination` | NOT-YET | NOT-YET |
| `keeper.ledger_entries` | `[]` | 3 entries (above) |
| `generated` | 2026-10-03 02:12 | 2026-10-03 02:37 (rebuild time) |
| every criterion record, caveat list, reason, scope | — | unchanged |

The FAIL rows stand as before:
- C1 COAL_BIT 2019/20/21, +19.81 / +13.18 / +16.58 TWh;
- C1 CT_PEAKER 2021, −8.07 TWh;
- C3a 2022/2025, −16.9 % / −11.6 %;
- C3b 2022/2025, 0.287 / 0.222.

The C3c 2019/2021/2022 CAVEATs are unchanged.

## Gates

| gate | result |
|---|---|
| `audit_keepers.py --iso PJM --check` | PASS, 0 failures and 0 warnings |
| `check_registry_payload_parity.py` | OK: 9 runs, 9 bundle dirs |
| `check_mechanism_matrix.py --base origin/main` | OK |
| fast lane | see the PR description |

## Notes for the desk

1. **`pjm_reserve_pergen_sync` has no row of its own.** It is the SYNC sub-leg that is R on the `reserve_pergen`
   family row (cell K), under the pjm-151 sub-leg convention. The R-37 evidence was prepended there, and the cell
   stays K.
2. **Two PR numbers.** Plan row R-36 cites the frontier draft as PR #7102, and the charter cites the ruling record as
   PR #7107. The entry text cites #7107 for the §5.0 record.
