# PRECOMMIT — PJM-NEXT-7: DA virtual position settled financially (design A′), 2026-09-28

- **Owner approval.** The owner approved design A′ on 2026-09-28 (decision card): *"A′ P0-DA / P1-RT"*. Design: `docs/records/pjm/DESIGN-pjm-next-7-virtual-settlement-2026-09-28.md`.
- **Keeper and control.** Keeper `2026-09-28-pjm-next-6-f2` (`results/calibration/pjmnext6_sp_span`). The control is the keeper's committed bundle plus G-DRIFT (§3), so no control solve is run (rule 29(b)).

## 1. Arm (single delta)

`replay_keeper.py results/calibration/pjmnext6_sp_span --years <y> --out-dir results/calibration/pjmnext7_vs_<y> --set pjm_da_virtual_settle_financial=true`
- There is one shard per year, 2019–2025 (rule 36). Each shard is pinned to this commit's SHA.
- Zero new free parameters. The only change is a bool sub-gate of `pjm_da_virtual_bids`.
- **What the flag does:**
  - P0 (the DA stage) is unchanged and keeps the virtual pseudo-units.
  - The scored P1 zeroes their bounds (DEC `min_gen` and INC `availability` set to 0).
  - Virtuals still reach P1 through P0's run lengths, i.e. through the startup markup.
- **Leg hard stop:** every leg's P1 `VIRTUAL_DEC` and `VIRTUAL_INC` must be 0 in every hour.

## 2. Predictions (zero-LP envelope census, `scripts/probes/_pjmnext7_settlement_census.py`)

All values are model − actual in TWh; the band is ±8.

| year | CC_REGULAR | COAL_BIT | CT_PEAKER | mean LMP vs RT actual ($/MWh) |
|---|---|---|---|---|
| 2019 | +6.1 → +7.3 | +17.3 → +17.4 | −4.4 → −6.1 | 28.1 → 27.9 (26.5) |
| 2020 | +12.8 → +14.1 | +4.8 → +4.4 | −1.0 → −3.4 | 25.0 → 24.5 (21.2) |
| 2021 | +4.6 → +2.3 | +18.9 → +16.4 | −5.8 → −9.1 | 41.0 → 39.6 (38.5) |
| 2022 | +11.3 → +12.0 | +9.7 → +6.6 | −1.8 → −7.3 | 68.4 → 66.3 (74.1) |
| 2023 | +4.6 → +9.5 | −0.5 → +0.6 | −1.8 → −2.8 | 31.0 → 31.1 (29.6) |
| 2024 | −4.9 → 0.0 | −0.3 → +0.6 | +2.6 → +1.0 | 31.0 → 30.7 (31.4) |
| 2025 | −10.4 → −8.0 | +9.9 → +11.4 | +7.4 → +5.0 | 44.9 → 44.0 (45.9) |

- **Falsifiers of the envelope:**
  - The sign of Δthermal disagrees with the sign of the keeper's net virtual position in any year.
  - |Δthermal| is outside 0.5–1.5 × |net virtual|.
- **Expected verdict:**
  - Run-level stays NOT-YET.
  - The training span is **likely to lose CALIBRATED**: CC_REGULAR 2023 is estimated at +9.5, and pjm-158's equivalent arm failed C3c-2025.
  - Only COAL_BIT 2022 is expected to flip to PASS.
- **Promotion is decided on structure (rule 1) and by the owner (rule 31), not by this table.**

## 3. G-DRIFT (keeper `git_sha` 81dcf974 → this pin)

Recorded below before any solve. The keeper was solved at 81dcf974; the arm will be solved at this commit's SHA.

G-DRIFT-RESULT: (filled in the addendum before launch)
