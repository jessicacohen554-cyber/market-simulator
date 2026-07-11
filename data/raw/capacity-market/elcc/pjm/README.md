# PJM capacity-market-elcc (ELCC Class Ratings)

Drop the retrieved unified CSV here as **`pjm.csv`**. PJM's ELCC Class Ratings
are typically a single current-fleet class-average rating per delivery year —
leave `penetration_pct`/`penetration_unit` blank unless a specific study
publishes a marginal curve, and note that explicitly here once retrieved.

## Authoritative sources

- PJM ELCC Class Ratings postings (Planning Committee / Capacity Adequacy
  Planning Department): https://www.pjm.com/committees-and-groups/committees/pc
  (search "ELCC Class Ratings [delivery year]")

**STATUS:** `pjm.csv` committed — three tranches, scoped to renewable/storage/
demand-resource classes (thermal classes PJM also rates — nuclear, coal, gas,
diesel, steam — are out of scope for this datatype's intended CR-3.1
consumption and were not transcribed): (1) official/final 2026/27 + 2027/28
class ratings paired with installed MW (2 points per class, from the 2025 PJM
ELCC/Reserve Requirement Study); (2) a preliminary, explicitly non-binding
9-year indicative table (2026/27-2034/35, ER24-99 marginal-ELCC methodology) —
the closest thing PJM publishes to a declining-with-buildout trend, though
indexed by delivery year rather than a raw penetration %; (3) single 2024/2025
points from the superseded Dec-2021 ELCC Report (a narrower predecessor
methodology, not directly comparable to (1)/(2)). No genuine MW- or
%-of-peak-load-indexed penetration curve is publicly available for PJM. See
`docs/handoffs/capacity-market-intake-2026-07.md`.
