# RESULT — PJM-NEXT-5: measured CC offer shape on own cost (PROMOTED); F2 outage re-derive (solved, not promoted) (2026-09-27)

**New keeper: `2026-09-27-pjm-next-5-shape`** (bundle `results/calibration/pjmnext5_sh_span`, 2019–2025, one shard per
year at `2111658c`, composed at zero LP).
- **Prior keeper:** `2026-09-26-pjm-next-4-midcurve2019`, pruned (rule 35).
- **Control:** the prior keeper's committed bundle, plus G-DRIFT (rule 29(b)).
- **Phase 0:** `docs/records/pjm/FINDING-pjm-next-5-phase0-cards-1-2-3b-2026-09-27.md`.
- **Pre-registrations:** `docs/records/pjm/PRECOMMIT-pjm-next-5-card1-shape-2026-09-27.md` and
  `docs/records/pjm/PRECOMMIT-pjm-next-5-card3a-f2-rederive-2026-09-27.md`.

## 1. Headline

**The PJM training span 2023–2025 is CALIBRATED on the new keeper.**
- C1 CC_REGULAR 2024 went from −9.33 TWh (FAIL) to passing.
- The run-level determination over 2019–2025 stays **NOT-YET**, but every remaining FAIL is in 2019–2022. Those years
  are reported and never gating (rule 30(c)).

| same scorer | keeper (next-4) | **shape (promoted)** | F2 (not promoted) |
|---|---|---|---|
| 2023–2025 alone | NOT-YET | **CALIBRATED** | NOT-YET |
| C1 fails | 8 (incl. 2024 CC −9.33) | **6, none in 2023–25** | 10 |
| 2019 COAL_BIT | +25.84 | **+13.83** | +27.57 |
| 2019 CC_REGULAR | −8.54 | +11.10 | −11.84 |
| 2020 COAL_BIT | +10.47 FAIL | **pass** | +11.08 |
| 2020 CC_REGULAR | pass | **+16.86 FAIL** | pass |
| 2021 CT_PEAKER | −8.19 FAIL | **pass** | −8.05 |
| 2021 COAL_BIT | +20.73 | +18.84 | +20.22 |
| 2022 CC / COAL_BIT | +14.90 / +8.09 | +13.45 / +8.59 | +12.40 / +8.51 |
| 2023/2024 ST_GAS | pass | pass | **+8.28 / +8.13 FAIL** |
| C3a 2020 | +19.4 % | +15.1 % | +19.5 % |
| C3b | 2020, 2022 | **2022 only** | 2020, 2022 |
| C2 / C4 / C6 / C8 | PASS | PASS | PASS |
| C3c | caveat | caveat (2019/21/22, ledgered) | caveat |

## 2. Card 1 — shape on own cost (promoted)

- **What changed:** `pjm_offer_midcurve_shape_segments=["CC_LIKE"]`. Each CC econ rung is now priced at the plant's
  own committed-rung cost times PJM's measured offer-ladder ratio.
- **What it replaced:** the residual-identified `econ_low 0.96 → econ_high 1.5` ladder on those rows. It adds zero
  DOF, and no multiplier was touched.
- **Predictions:**
  - 2019/2020 direction ✓: COAL_BIT down, CC up.
  - Size ✗: CC overshot to +11.1 in 2019 and +16.9 in 2020, larger than the pre-registered +2 to +8.
  - 2024 ✗ **against prediction**: the pre-registered |ΔCC| < 2 TWh; the actual was +4.4 TWh. The static census read
    only the cap-weighted mean, while redispatch acted on the lowered lower rungs.
- **Remaining pre-2023 defect:** CC now over-runs in 2019, 2020 and 2022 while coal still over-runs in 2019, 2021 and
  2022. That points at load or supply balance in those years (net imports, nuclear/hydro, demand), not the CC-vs-coal
  ordering alone.
- **`retiree_cems_cap` deleted** at the same pin (rule 26, owner ruling). It was measured inert, 0 rows, in every year.

## 3. Card 3(a) — F2 full outage re-derive (solved, NOT promoted; owner decision)

- **What it is:** the committed standard + short-coal CAMPD extracts re-derived at HEAD (membership union, COAL-SUB
  fix, and this session's unit-scoped `ST_GAS_PEAKER_PLANTS` fix), then per-unit fuel routing applied.
- **Result:** the training span becomes NOT-YET. CC 2024 moves −9.33 → −12.06, and ST_GAS 2023/2024 reach +8.3/+8.1
  TWh. Both are within the pre-registered direction, and larger than predicted for ST_GAS.
- **Cause:** the pjm-d4-2 listed gas-steam peakers (Martins Creek, Chalk Point, Edge Moor, Joliet 29) lose their
  dead-period windows and the LP runs them.
- **Why it is not a clean input correction:** the ST_GAS move comes from removing *measured* dark periods. Whether a
  listed peaker's dead period is an availability event or economic idleness is a structural question for the owner.
- **Status:** the run was pruned at this promotion and is recoverable from git `9fcee5e8`. The flag and companions
  stay on `main`, default off.

## 4. Governance and retrievability

- **Attestations:** `scripts/gen_pjmnext5_sh_attestation.py` and `gen_pjmnext5_attestation.py`. The DOF ledger is
  carried verbatim with zero entries added, and `authorized_price_tuning.used = false`.
- **Rule 35:**
  - Keeper shard, calibration-complete (run-level NOT-YET recorded honestly; 2023–25 alone CALIBRATED), program-status
    gate (a), status part, matrix stamp and §5.3 header are all updated.
  - Prior keeper and F2 are pruned. `audit_keepers --iso PJM`: 0 failures. `check_promotion_completeness --iso PJM`:
    OK.
- **Retrievability:** the keeper composite is on `main`. The 14 per-year legs (with dispatch parquets) sit gitignored
  on this session's disk and will not survive it; recovering them would be a 7-shard re-solve (~20 min each, in
  parallel). Leg SHAs are in `.gitignore` as provenance only.
- **Shards:** all 14 are archived. Leftover branches for the owner to clear:
  - `claude/pjmnext5-f2-{2019..2025}`
  - `claude/pjmnext5-sh-{2019..2025}`
