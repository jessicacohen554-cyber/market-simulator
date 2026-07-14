# PJM capacity-market-elcc (ELCC Class Ratings)

Drop the retrieved unified CSV here as **`pjm.csv`**. PJM's ELCC Class Ratings
are typically a single current-fleet class-average rating per delivery year —
leave `penetration_pct`/`penetration_unit` blank unless a specific study
publishes a marginal curve, and note that explicitly here once retrieved.

## Authoritative sources

- PJM ELCC Class Ratings postings (Planning Committee / Capacity Adequacy
  Planning Department): https://www.pjm.com/committees-and-groups/committees/pc
  (search "ELCC Class Ratings [delivery year]")

**STATUS:** `pjm.csv` committed — three tranches, covering both the
renewable/storage/demand-resource classes and (as of the
2026-07-14 intake, accreditation-basis-memo-2026-07-12.md §4.3 R3) the
thermal classes PJM also rates — nuclear, coal, gas combined-cycle/combustion
turbine (incl. dual-fuel), diesel, steam: (1) official/final 2026/27 + 2027/28
class ratings paired with installed MW (2 points per class, from the 2025 PJM
ELCC/Reserve Requirement Study; thermal installed MW is the RRS Table 5
"Installed Capacity" column, same as the renewable rows — except Gas Combined
Cycle, whose Table 5 row combines Single+Dual Fuel MW with no clean
single-fuel-only split, so its penetration_pct/unit are left null, see the row
comment); (2) a preliminary, explicitly non-binding 9-year indicative table
(2026/27-2034/35, ER24-99 marginal-ELCC methodology) — the closest thing PJM
publishes to a declining/rising-with-buildout trend for both renewables and
thermal, though indexed by delivery year rather than a raw penetration %; (3)
single 2024/2025 points from the superseded Dec-2021 ELCC Report (a narrower
predecessor methodology, not directly comparable to (1)/(2)) — this tranche
has NO thermal rows: the Dec-2021 report predates the reform that extended
ELCC class ratings to thermal at all (confirmed by reading the full document,
not merely absent from what had been transcribed). No genuine MW- or
%-of-peak-load-indexed penetration curve is publicly available for PJM (for
thermal or renewables). See `docs/handoffs/capacity-market-intake-2026-07.md`
and `docs/handoffs/pjm-thermal-elcc-intake-2026-07-14.md`.
