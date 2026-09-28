# RESULT — PJM-NEXT-6: F2 outage re-derive "Split" (PROMOTED); pre-2023 surplus traced to the DA virtual layer (2026-09-28)

**New keeper: `2026-09-28-pjm-next-6-f2`** (bundle `results/calibration/pjmnext6_sp_span`, 2019–2025, one shard per year
at `81dcf974`, composed at zero LP).
- **Prior keeper:** `2026-09-27-pjm-next-5-shape`, pruned (rule 35).
- **Control:** the prior keeper's committed bundle + G-DRIFT, all hunks INERT (rule 29(b)).
- **Pre-registration:** `docs/PRECOMMIT-pjm-next-6-card1-f2-split-2026-09-27.md`.
- **Card 2 record:** `docs/FINDING-pjm-next-6-card2-energy-balance-2026-09-28.md`.

## 1. Headline

**The training span 2023–2025 stays CALIBRATED.** Run-level 2019–2025 stays NOT-YET, and failures go from 8 to 7, all
out of span (reported, never gating, rule 30(c)).

| criterion (same scorer) | shape keeper | **split (promoted)** |
|---|---|---|
| 2023–2025 alone | CALIBRATED | **CALIBRATED** |
| C1 CC_REGULAR 2019 | +11.10 FAIL | **+6.11 PASS** |
| C1 CC_REGULAR 2020 | +16.86 | +12.75 |
| C1 CC_REGULAR 2022 | +13.45 | +11.25 |
| C1 COAL_BIT 2019 | +13.83 | +17.29 |
| C1 COAL_BIT 2021 | +18.84 | +18.92 |
| C1 COAL_BIT 2022 | +8.59 | +9.67 |
| C3a 2020 | +15.1 % | +18.0 % |
| C3b 2022 NRMSE | 0.236 | 0.229 |
| ST_GAS (F2's defect) | pass | **pass every year** |
| C2 / C4 / C6 / C8 | PASS | PASS |
| C3c | ledgered caveat | ledgered caveat |

## 2. Card 1 — the split (promoted)

- **What:** `unit_outage_full_rederive` + `unit_outage_rederive_peaker_windows`. The standard PJM CAMPD outage extract is
  the F2 full HEAD re-derive with the listed ST_GAS peakers' measured full-dark dead-period windows kept (owner ruling
  "Split"). The companion's control reproduces the F2 file byte-for-byte; the switch is the only difference.
- **Zero DOF.** No offer or multiplier touched (offers byte-identical in the census, every year).
- **Predictions vs outcome** (class energy, arm − keeper, TWh):

| year | CC_REGULAR | ST_GAS | COAL_BIT | CT_PEAKER |
|---|---|---|---|---|
| 2019 | −4.99 | −1.69 | +3.46 | +1.27 |
| 2020 | −4.17 | −1.84 | +2.38 | +2.11 |
| 2021 | −2.44 | −1.60 | +0.09 | +2.19 |
| 2022 | −2.20 | −1.22 | +1.08 | +1.41 |
| 2023 | −1.52 | −1.38 | −0.95 | +1.97 |
| 2024 | ~0 | −1.50 | −0.35 | +1.15 |
| 2025 | −0.15 | −3.51 | +0.06 | +2.00 |

  - CC fell 2–5 TWh pre-2023 ✓, 0–1.5 in span ✓.
  - ST_GAS fell 1.2–3.5 ✓ (2025 slightly past the 3 TWh bound).
  - Coal rose pre-2023 as flagged against interest (2019 +3.5, beyond the 0–3 range); 2024 coal fell less than
    predicted (−0.35 vs −0.5 to −2).
  - C3a 2020 +3 pts (predicted 0 to +2).
- **Why promoted:** the owner-ruled measured input, one construction for every year (rule 14), no training-span
  regression, and one fewer failing row. Coal 2019 and C3a 2020 worsen; they are reported, not hidden.

## 3. Card 2 — the pre-2023 joint CC+coal surplus (zero LP)

- **Not a physical-balance input.** Seams, demand, nuclear, hydro and wind/solar match or are neutral; the model
  under-exports 9–13 TWh in every year, flat across 2023.
- **It is the DA virtual layer.** The measured INC/DEC curves cleared at *actual* DA system prices net to virtual
  demand +5.5 / +15.1 / +14.8 / +6.8 TWh in 2019–22 (net supply −4.1 / −6.9 / −7.9 in 2023–25). The LP serves net DEC
  with physical thermal while C1 scores RT-physical generation: 18 / 27 / 60 / 44 % of the 2019–22 thermal over-run.
- **Admissibility claim falsified:** `virtual_bids.py:49-52` ("net ≈ 0 at actual DA prices") holds for neither period
  on the system-price basis.
- **No measured-input lever.** The next step is structural (rule 1) and needs an owner decision: make the virtual
  layer price-forming but not physical-energy-forming (e.g. settle the net virtual position financially).

## 4. Card 3 — C3a 2020 / C3b 2022

- C3a 2020 (+18.0 %) and C3b 2022 (0.229) sit in the same years as the virtual net DEC; they are read as downstream of
  card 2, not as separate levers. No solve.

## 5. Governance and retrievability

- **Attestation:** `scripts/gen_pjmnext6_sp_attestation.py`. DOF ledger carried verbatim, zero entries added,
  `authorized_price_tuning.used = false`.
- **Rule 35:** year set before pruning = 2019–2025 (both runs); incoming covers it. Keeper shard, calibration-complete
  (run-level NOT-YET recorded; 2023–25 alone CALIBRATED beside it), program-status gate (a), status part, matrix stamp,
  §5.3 header updated. `audit_keepers --iso PJM` PASS; `check_promotion_completeness --iso PJM` OK.
- **Retrievability:** the keeper composite is on `main` (slim bundle + hourlies). The 7 per-year legs sit gitignored on
  this session's disk and will not survive it; leg SHAs in `.gitignore` are provenance only (rule 33(d)). Recovering a
  leg = re-solve (~25 min per year in parallel shards).
- **Shards:** all 7 archived. Leftover branches for the owner to delete: `claude/pjmnext6-sp-{2019..2025}`.
