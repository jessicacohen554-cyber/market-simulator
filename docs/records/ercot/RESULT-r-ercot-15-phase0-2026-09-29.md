# RESULT — R-ERCOT-15 phase 0: the 2020 C3b object is offer level; vintage anchor rejected; one zero-DOF arm staged, NOT solved

Date 2026-09-29. Keeper `2026-09-28-r-14-oklaunion-swcap` (unchanged; ISO NOT-YET). Full numbers: `PRECOMMIT-r-ercot-15-phase0-oklaunion-hr-2026-09-29.md`.

## Headline

- **No LP spent.** The session hit the platform's session-nesting limit (lineage depth 8), so it could not launch shards, and rule 32(a) forbids solving in the parent. The staged arm is handed to a new chain.
- **2020 C3b 0.242 has no admissible zero-DOF lever.** 45 % of its squared error is August, 25 % Feb/Mar and 20 % Jun/Jul. What drives it is a system-wide mid-distribution over-price of +0.9 to +4.2 $/MWh, present in every year (2019–2025) and every zone. That is the offer level, which is the owner-held channel. Feb/Mar misses actual spikes (7 / 6 h > $200 vs 1 / 2).

## §2 Vintage anchor — `R` (zero LP)

`gas_offer_margin_{zonal_,}anchor_vintage`. Each year's zone anchors were measured from its own solve fuel array (7 no-LP rebuilds). If the frozen 2023–2025 anchor were the defect, the price bias would move about −3 $/MWh per $/MMBtu of gap. It does not: slope +0.11, r² 0.02. 2022 is +4.2 over where ≈ −11 is predicted. ERCOT's markups are fuel-invariant across years. Matrix cells stamped `R`.

## §3 Routed (not armed)

- South 2020 F923 basis HH+3.53 from a 3-plant / 5M MMBtu sample.
- No West Waha row before 2022. 2019 has a citable −1.66 (EIA TIE 53919); 2020/2021 have no EIA annual figure, and there is no 2019 `neg_day_freq`.

## §4 Landed (this PR)

- Sandy Creek `COAL_PLANT_COMMISSION_YEAR` re-keyed 56257 → 56611. Measured byte-inert: the 2020 fleet is identical.
- `derive_campd_coal_heat_rates.py` now measures every curated-sheet coal plant (ERCOT). Re-derived because the population changed (rule 23). There are +3 rows (Oklaunion: pooled 11.68, 2019 11.77, 2020 11.47 vs eGRID 11.90 / 11.70); every other row reproduces.
- **This CSV is LIVE for 2019/2020** (Oklaunion mc −0.21 / −0.34 $/MWh, four rows, nothing else). The keeper's 2019/2020 legs predate it, so the next lane solves the two-shard arm first.

## Retrievability

Nothing was solved, so there is nothing stranded. The keeper legs for composing are verified fetchable by full SHA with `dispatch/<y>_P1.parquet`:
- B-2021 `9a8f340833b323eafb09f5c1f34cca531582a6dd`
- 2022 `e7a4832bdb15a0c7c2ac57ae0df800e53a775f08`
- 2023 `3d4a490452a28e6394d2be24c6dadb0f37b38435`
- 2024 `41061da2db3a81995b8a31d7fdd2d20a01264b80`
- 2025 `6ad0a04b9e3a60e34f036bb3178c3bfb4fdf846e`

These are provenance (rule 33(d)). Cost any leg that fails to fetch as a ~17 min re-solve.
