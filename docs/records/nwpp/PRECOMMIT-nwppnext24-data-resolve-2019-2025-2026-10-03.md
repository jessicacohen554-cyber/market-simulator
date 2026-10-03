# PRECOMMIT — NWPP-NEXT-24: keeper recipe replayed unchanged at main HEAD (rule-14 data re-solve), 2019–2025

Desk rulings (close-out desk session_01ALecU5Wjde4tkbLrnMExT9, recorded in plan §5.0, 2026-10-03):
- Q1 "Close seam, pivot C3a". The COI-depth lane closes with no admissible driver
  (`FINDING-nwppnext24-coi-depth-phase0-2026-10-03.md`). No lever arm is solved this session.
- Q2 "7-shard replay at HEAD".

## What is solved

`replay_keeper.py results/calibration/nwppnext23_span --years Y` runs at the pin with **no `--set` key**, for
Y = 2019 … 2025. There is one shard per year (rule 36), at most 6 alive at once, and the out-dir is
`results/calibration/nwppnext24_<Y>`.

The recipe is identical to keeper `2026-10-03-nwpp-next-23-coi`. The solve differs from the keeper's legs (pin
`33dc5647`) only by two data inputs on main:

1. #7134 EIA-923 coal stocks 2015–17 (`9f2fe6df`). NWPP yard maxima rise in 65 plant-years, which moves the take
   floor and monthly pile S_max.
2. SolveEpoch 2026-10-03b: the NWPP 2019–22 `NUCLEAR_MONTHLY_CF_BY_YEAR` rows (Columbia; owner ruling R-35).

**G-DRIFT** (`33dc5647` → `b54e1d84`): classified at the NEXT-23 promotion (RESULT-nwppnext23 §Promotion). Only these
two hunks are LIVE. Everything else is INERT.

## Hard stops (per shard)

The zero-LP construction line, the data-delta checks, and the demand frame all equal the keeper's per-year values,
reproduced locally at the pin. The `scenario_config` diff against the keeper's year config is empty. The remaining
hard stops (a)–(h) are as in NEXT-23.

## Expected direction (pre-registered)

- **Coal.** Larger yard maxima loosen the take floor and pile ceiling where the 2015–17 stocks exceed the old
  maxima (Boardman, Bonanza, Valmy, plant 3845). Expect a small coal energy move, sign plant-specific; C4 coal stays
  PASS.
- **Nuclear.** Columbia's measured 2019–22 monthly CF replaces the fleet smear. Expect a ±0.1–0.5 TWh/yr
  nuclear-energy shift in 2019–22 and a matching gas/hydro offset. 2023–25 are unchanged by this input.
- **Rubric.** No predicted status flip. The 10 FAIL records (CC_REGULAR 2019/24/25, C4 gas 2019/23/24, C3a and C3b
  2023/24) are expected to persist.

## Promotion rule

This is a rule-14 data re-solve: the measured data replaces the older data on structure. Under the owner's standing
ruling it is promotable even if a gate regresses, and every regression is reported at full magnitude. The desk
serialises the NWPP slot.
