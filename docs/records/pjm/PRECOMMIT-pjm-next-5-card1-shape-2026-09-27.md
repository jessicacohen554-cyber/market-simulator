# PRECOMMIT — PJM-NEXT-5 card 1: CC econ rungs at PJM's measured offer SHAPE on each plant's own cost (2026-09-27)

Keeper `2026-09-26-pjm-next-4-midcurve2019` (bundle `results/calibration/pjmnext4_c1_span`). Owner ruling 2026-09-27:
**build + solve**. Written and pushed **before any solve**. Phase 0: `docs/FINDING-pjm-next-5-phase0-cards-1-2-3b-2026-09-27.md`
card 1.

## 1. The arm (one field, zero DOF)

`pjm_offer_midcurve_shape_segments = ["CC_LIKE"]` (new, default None) sets every CC_LIKE **econ** row's P1 bid to:

    bid[g,t] = (mc_base[c,t] − vom[c]) × m(s_g, bin t) / m(s_c, bin t) + vom[g]

- `c` is the same plant's `committed` row.
- `m` is PJM's measured CC_LIKE ladder for that year (DataMiner, the keeper's own surface).
- The gas-day index cancels in the ratio. So each plant keeps its **own** delivered gas, measured heat rate and RGGI
  cost, which pjm-h21 showed the level form erased. Only the rise above min load is measured.
- It **replaces** the residual-identified `econ_low 0.96 → econ_high 1.5` ladder on those rows (rule 14). That is a
  measured construction in place of a fitted one; no multiplier value is changed or tuned.
- **Rule 19:** a segment cannot be in both the level scope and the shape scope; the builder raises if it is. The
  committed, peak and min-load rungs are untouched, as are all non-CC rows (byte-identical, census §2).
- **P1-only**, like every mid-curve form: P0 run discovery still reads the fitted ladder. That is stated, not hidden.
- **Cost:** it moves one CC_REGULAR econ curve; it adds no DOF (the carve-out channel is not used).

Tests: `tests/iso/pjm/test_pjm_offer_midcurve_shape_form.py`.

## 2. Zero-LP census (fleet-only rebuild, keeper recipe; the model's own builder)

`scripts/probes/pjm_next5_card1_shape_census.py` → `results/calibration/_pjm_next5_card1_shape_census.json`. All
values are cap-weighted, ex startup amortization, in $/MWh.

| year | CC econ keeper | CC econ shape | COAL_BIT econ | order (shape) |
|---|---|---|---|---|
| 2019 | 27.14 | **24.19** | 25.05 | CC < coal (keeper: coal < CC) |
| 2020 | 23.53 | **21.18** | 23.34 | CC < coal (keeper: ≈ tie) |
| 2021 | 36.34 | 36.34 | 32.79 | coal < CC (unchanged) |
| 2022 | 58.93 | 59.90 | 61.69 | CC < coal (unchanged) |
| 2023 | 27.79 | 26.50 | 38.58 | — |
| 2024 | 27.41 | 27.35 | 36.69 | — |
| 2025 | 38.14 | 40.77 | 39.42 | — |

- **By rung:** the lower econ rungs fall and the top rung rises every year. In 2019 the rungs go c00 −0.4 … c03 −4.0,
  c05 −4.8. In 2024 the top rung rises to PJM's steep measured top.
- **By zone, 2024:** Dominion rises 28.7 → 30.8, SWMAAC 37.5 → 38.2 and EMAAC 33.7 → 33.8. ComEd, APS and ATSI fall
  $1–2.

## 3. Predictions (stated before the solve)

- **2019:** CC_REGULAR rises and COAL_BIT falls, both by +2 to +8 TWh. The 2019 C1 CC −8.54 FAIL narrows and could
  pass; the COAL_BIT +25.8 FAIL narrows but stays FAIL. C3a moves −0.5 to −2 pts.
- **2020:** the same direction, smaller (+1 to +4 TWh).
- **2021 and 2024:** |Δ CC| < 2 TWh. **C1 CC_REGULAR 2024 −9.33 stays FAIL.** The shape form does not close it; that
  half is the delivered-gas level, which is data-blocked.
- **2022 and 2025:** CC falls 0 to 3 TWh as the top rungs rise.
- **Determination:** no training-span criterion flips. PJM stays NOT-YET.

## 4. G-DRIFT (rule 29(b))

The control is the keeper's committed bundle. Code between the keeper's `7394a279` and this pin is INERT for the PJM
backcast:
- **Committed other-lane hunks:** classified in `PRECOMMIT-pjm-next-5-card3a-f2-rederive-2026-09-27.md` §5.
- **`unit_outage_full_rederive`:** default off.
- **`retiree_cems_cap` deletion:** the owner ruled delete. It was **measured** to move 0 rows on the keeper recipe in
  every year 2019–2025 (FINDING §3(b)). `replay_keeper` declares the keeper's recorded True inert (rule-26 registry).
- **This field:** default None.

## 5. Execution

- **Shards:** one per year 2019–2025, pinned to the full SHA of the commit carrying this doc. Each runs
  `replay_keeper.py results/calibration/pjmnext4_c1_span --years <y> --out-dir results/calibration/pjmnext5_sh_<y>
  --set 'pjm_offer_midcurve_shape_segments=["CC_LIKE"]'`.
- **Hard stops:** the pin; `scenario_config.pjm_offer_midcurve_shape_segments == ["CC_LIKE"]`;
  `unit_outage_full_rederive` false.
- **Push:** the full bundle to `claude/pjmnext5-sh-<y>`.
- **Separate from card 3(a):** the two cards are solved as separate single-delta arms against the same keeper. If both
  are promotable, a joint span is owed before promotion.
