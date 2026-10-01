# RESULT — R-CAISO-15 (2026-09-30): clock repair COMPLETED, solved, PROMOTED

**New keeper `2026-09-29-caiso-r15-clockfull`** (bundle `rcaiso15_A_span`, 2022–25), fold
`2026-09-29-caiso-r15-clockfull-touchpoints` (bundle `rcaiso15_A_tp_2019_2021`). Owner decision card
2026-09-29: **"Promote"**. Outgoing keeper `2026-09-28-caiso-r11-tacpst` + fold pruned (rule 35).

## What was built (same flag `caiso_eia930_clock_repair`, zero parameters)
| Seam | Status |
|---|---|
| EIA-930 frame, caiso-80 demand | R-CAISO-13 |
| HSL solar/wind generation term (`renewables._repair_caiso_hsl_clock`) | this lane, PR #6878 |
| Battery shape envelope (`storage._caiso_storage_envelope_clock_repaired`) | this lane, owner card "Add battery envelope" |
| Vintage-scoped envelope denominator (shard crash fix) | PR #6880 |
| Zero-LP benchmark rebuild arms from the bundle (`run_calibration_full.build_benchmark_frames`) | this lane, found at compose |

The compose probe gained `--absent-default KEY=JSON`. Reason: the 2025 leg predates `unit_outage_exit_ym_from_eia860`
(default off, INERT). The option is used for that key only, and only for the cross-leg comparison.

## Solve
- 7 shards, one per year. Pins: 2019–24 at `789c70a0`; 2025 at `893545e3` (valid, ADDENDUM §8).
- Every leg carries the arm and was built from a clean tree.
- First launch: shards 2019–24 crashed on my envelope vintage guard. No results were lost; the relaunch cost ~25 min per leg.

## Scores, span 2022–25 (keeper → new)
| | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| Determination | CALIBRATED → **CALIBRATED** (single ledgered C3c 2024) | | | |
| C3a mean LMP (actual 84.49/54.17/34.65/34.42) | 91.77 → 91.74 | 57.62 → 57.58 | 36.41 → 36.47 | 36.78 → 36.81 |
| C3b monthly NRMSE | 0.108 → 0.107 | 0.107 → 0.107 | 0.111 → 0.116 | 0.094 → 0.096 |
| C4 gas NRMSE (≤ 0.30) | 0.262 → 0.262 | 0.247 → 0.248 | 0.254 → **0.249** | 0.294 → **0.290** |
| C3c h > $200 (RT 510/47/35/8) | 513 → 513 | 59 → 60 | 0 → 0 | 0 → 0 |
| C1 CT_PEAKER TWh (actual 4.48/4.13/4.33/2.34) | 3.26 → 3.27 | 2.50 → 2.54 | 1.99 → 2.06 | 1.14 → 1.17 |

Fold 2019–21 is NOT-YET and reported only (rule 30(c)). It degrades on the same three criteria as the outgoing fold (C1, C3a, C4).

## Predictions (PRECOMMIT-r-caiso-13 §3; P4′ amended in ADDENDUM §7 before any solve)
| | Result |
|---|---|
| P1: solar centroid 11.5–12.0 h, 2024–25, every month | **Narrow miss.** Model dispatch: 20 of 24 months in band; 4 months at 12.02–12.09 (Feb 2024; Jan–Mar 2025). The repaired EIA-930 delivered term is 11.52–12.00 in all 24 months. The overshoot is the CAISO curtailment term (spring curtailment around and after midday). |
| P2: battery best lag vs Outlook +1 → 0 | **PASS.** r at lag 0: 0.991 (2024), 0.988 (2025) |
| P3: SP15 Jun–Sep price peak ~1 h earlier | **Mixed.** 2025 21 → 20; 2024 stays 19. DAM peak is 18 |
| P4′: 2019–22 move only through the battery caps | Holds. 2022 prices within $0.03 |
| P5: C1–C4 reported | Table above |

The decision rule (CALIBRATED **and** P1/P2 hold) was not cleanly met, so it went to the owner as a card. The owner answered "Promote".

## Retrievability
The keeper bundles (slim + hourly sidecars) are committed on `main` with this PR. Per-year legs stay off `main`
(gitignored, provenance SHAs in `.gitignore`); recovering a leg is a re-solve (~25 min per year, in parallel).

## Open (recorded, not built)
- Per-DIBA interchange feed: its fixed 1 h / 2 h lag was fitted against the unrepaired extract (ADDENDUM §4 #2). The DSW
  depth constants (#3) depend on it.
- Weak or scalar gaps: #4 conditional offer surface net-load bins; #5 CT and ST-gas drag scalars.
- Whether the CAISO curtailment workbook's prevailing-time hours map onto the fixed-PST model clock in DST months. This is
  unverified; it would bear on P1's summer months, not on the four winter months that overshoot.
- Evening under-price (carried).

Leftover branches for the owner to delete (a ref delete returns 403):
- `claude/r-caiso-15-A-2019` … `-2025`
- `claude/caiso-eia930-clock-repair-8xy6ie`
