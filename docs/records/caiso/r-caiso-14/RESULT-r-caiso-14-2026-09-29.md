# RESULT — R-CAISO-14 (2026-09-29): `caiso_eia930_clock_repair` solved; NOT promoted (repair incomplete)

**Owner decision card 2026-09-29: "Complete repair, re-solve".** Keeper unchanged: `2026-09-28-caiso-r11-tacpst`.

## What was solved
- Keeper recipe + `caiso_eia930_clock_repair=true`, one shard per year 2019–2025 (rule 36), pinned `332c8048`.
- G-DRIFT: all INERT (`ADDENDUM-r-caiso-14-gdrift-2026-09-29.md`).
- Every hard stop passed, including arm liveness at the exact PRECOMMIT row counts.
- Composites `rcaiso13_A_span` (2022–25) and `rcaiso13_A_tp_2019_2021`.
- **Where the bytes are:** local disk of the R-CAISO-14 container, and shard branches `claude/r-caiso-13-A-{Y}`, with SHAs in `.gitignore`. Neither is durable (rule 33(f)), so treat recovery as a re-solve: ~7 parallel shards, ~30 min.
- Registered locally as `2026-09-29-caiso-r14-clockfix` (+`-touchpoints`), but kept off `main`. The owner ruled no promotion, and audit E13 fails any non-keeper CAISO run.

## Scores (span 2022–25; keeper → arm)

| | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| Determination | CALIBRATED → CALIBRATED (single ledgered C3c 2024) | | | |
| C3a mean LMP $/MWh (actual 84.49/54.17/34.65/34.42) | 91.77 → 91.77 | 57.62 → 57.61 | 36.41 → 36.34 | 36.78 → 36.83 |
| C4 gas NRMSE (≤ 0.30) | 0.262 → 0.262 | 0.247 → 0.247 | 0.254 → **0.262** | 0.294 → **0.300** |
| C3c h > $200 (RT actual 510/47/35/8) | 513 → 513 | 59 → 59 | 0 → 1 | 0 → 0 |
| C1 CT_PEAKER ΔTWh | −1.22 → −1.22 | −1.63 → −1.66 | −2.34 → −2.59 | n/a (prelim. 923) |

Fold 2019–21: byte-identical to the keeper fold, NOT-YET, reported only (rule 30(c)).

## Predictions (PRECOMMIT-r-caiso-13 §3)

| | Result |
|---|---|
| P1 solar centroid → 11.5–12.0 h in 2024–25 | **FAIL.** Model solar centroid unchanged: 2024 12.73–12.95, 2025 11.88–13.00 (Dec is outside the window) |
| P2 battery best lag vs Outlook +1 → 0 | **FAIL.** Stays +1 (2024 0.990, 2025 0.989) |
| P3 SP15 Jun–Sep price peak ~1 h earlier | **FAIL.** 2024 19 → 20 (wrong way); 2025 21 → 20. DAM peak is 18 |
| P4 2019–22 byte-identical | **PASS.** Max \|Δ class TWh\| 0.0000, 0 price cells moved |
| P5 C1–C4 reported | See the scores table |

## Why: the repair does not reach the solar/wind profiles
- CAISO wind and solar CF come from `data/raw/caiso-hsl/caiso_{Y}_hsl_hourly.parquet`. `scripts/data/build_caiso_hsl.py` builds it offline as EIA-930 delivered + CAISO 5-min reported curtailment, and it is read by `renewables._hsl_file`.
- The file was built from the late-stamped EIA-930. Its `solar_gen_mw` monthly centroid (h PST) is:

| Year | Monthly centroid |
|---|---|
| 2022 | 11.2–12.0 |
| 2023 | 11.6–11.9, then Nov/Dec 12.63/12.78 |
| 2024 | 12.54–13.00 |
| 2025 | 12.58–13.00, then Dec 11.86 |

  This is exactly the frame defect's generation window.
- The arm repairs only the frame seam and the caiso-80 SC demand. **Demand therefore moved 1 h earlier (hour-level fit best at lag −1), and solar did not.**
- Before the arm, demand and solar were late together. With it, they are 1 h apart through Nov 2023–Dec 2025. The C4 gas NRMSE rise in exactly 2024–25 is consistent with this: net load is mis-timed around the ramps.

## Next link (owner card "Complete repair, re-solve")
- Extend `caiso_eia930_clock_repair` to the HSL generation term.
  - The EIA-930 `*_gen_mw` columns shift earlier by one hour in the generation late window; the curtailment term (`hsl − gen`, CAISO 5-min, already on the right clock) is untouched; HSL is then recomposed.
  - Gate it at the reader (the frozen parquet is not rewritten, rule 23). Zero parameters.
- Re-solve 7 shards, and apply the same decision rule and predictions.
- Mechanism matrix cell: `O` (was `U`).
