# PJM capacity-market-elcc (ELCC Class Ratings)

Drop the retrieved unified CSV here as **`pjm.csv`**. PJM's ELCC Class Ratings
are typically a single current-fleet class-average rating per delivery year —
leave `penetration_pct`/`penetration_unit` blank unless a specific study
publishes a marginal curve, and note that explicitly here once retrieved.

## Authoritative sources

- PJM ELCC Class Ratings postings (Planning Committee / Capacity Adequacy
  Planning Department): https://www.pjm.com/committees-and-groups/committees/pc
  (search "ELCC Class Ratings [delivery year]")

**STATUS:** `pjm.csv` committed — six tranches, covering both the
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

## The DELIVERY-YEAR VINTAGE tranches (capx D75-R, 2026-09-06)

Tranches (4)-(6) were added — and (3) relabelled — by capx D75-R, executing
`docs/handoffs/FINDING-capx-d75-2026-09-06.md` §6 item 1. The card they serve
(`FINDING-capx-d66-2026-09-06.md` §8 card B) is that the model accredits PJM VRE
at the 2026/27+ marginal-ELCC ratings in EVERY delivery year, including years
whose auctions cleared on a different published rating set. Fixing that needs
each delivery year's OWN ratings on disk. Every row is transcribed verbatim from
the primary PJM posting named in its `source_doc`, whose sha256 is recorded in
the row's `source_page` and re-verified in
`tests/curation/test_curate_capacity_market_elcc.py`. Rule 14 `[R-ACCURATE]`:
nothing here is estimated, blended, or adjusted.

4. **`2023/2024 BRA (final for DY 2023/2024; posted 2021-12-16)`** — 13 classes.
   PJM's ELCC regime BEGAN with the 2023/2024 BRA, not 2024/25 (the Dec-2021
   report's own Table 3 is titled *"Comparison of ELCC Class Ratings, 2024/2025
   BRA vs 2023/2024 BRA"*). Onshore Wind 15 %, Solar Fixed 38 %, Solar Tracking
   54 %. No thermal rows — pre-CIFP, same methodology gap as tranche (3).
5. **`2024/2025 (Dec 2023 ELCC Report -- FINAL for DY 2024/2025)`** — 13 classes.
   **This, not tranche (3), is the operative 2024/25 rating set.** The 2024/25
   BRA was delayed and re-executed (FERC ER23-729; the compressed schedule is
   recorded in `../../demand-curve/pjm/README.md`) and PJM re-ran the ELCC study.
   The December 2023 ELCC Report's Introduction states in terms: *"ELCC Class
   Ratings are calculated for each delivery year in the period 2024/2025 –
   2033/2034 but only the 2024/2025 values are final (the results for the rest of
   the delivery years are preliminary)."* Onshore Wind 21 %, Solar Fixed 33 %,
   Solar Tracking 50 % — against tranche (3)'s 16 / 36 / 54 %.
6. **`2025/2026 3IA (final for DY 2025/2026; posted 2025-03-12)`** — 18 classes,
   the FIRST vintage on disk to rate thermal for a delivery year before 2026/27.
   Onshore Wind 38 %, Fixed-Tilt Solar 10 %, Tracking Solar 14 %; Nuclear 95 %,
   Coal 83 %, Gas CC 78 %, Gas CT 63 %, Steam 74 %, Diesel 92 %. Post-reform
   (marginal-ELCC) construct, and it confirms
   `THERMAL_ACCREDITATION_REFORM_DELIVERY_YEAR_BY_ISO["PJM"] == "2025/2026"` by
   rating thermal at all — but the VALUES differ from the wired 2026/27 set
   (wind 41, fixed 8, tracking 11; nuclear 95, coal 83, gas CC 74, CT 60, steam
   73, diesel 91). **This is the 3IA rating set** — PJM's final for the delivery
   year, applied to the Third Incremental Auction. The 2025/26 **BRA** (held July
   2024) cleared on the ratings current then, and the 2025/26 BRA Report's own
   tables are images that do not extract; a lane wiring this year must fix which
   vintage it reads (BRA vs delivery-year-final) and say so — see
   `FINDING-capx-d75-2026-09-06.md` §5.

Tranche (3) is **relabelled**, not replaced: PJM's December 2021 ratings are a
real published artifact (they were final for the 2024/25 BRA *as then scheduled*)
and stay on disk as `2024/2025 BRA (Dec 2021 ELCC Report -- PRELIMINARY/
SUPERSEDED for DY 2024/2025, re-studied Dec 2023; …)`. Rule 26 `[R-DELETE]` does
not reach it: it is a source record, not a re-armable tuning knob, and the label
is what stops it being read as the operative set.

**What PJM does NOT publish, for any pre-reform vintage: the fixed-tilt /
tracking installed-MW SPLIT.** Only the 2025 ELCC/RRS Table 5 (pp.16-17) pairs
installed MW with ratings, and only for 2026/27 and 2027/28 — the two tranche-(1)
vintages. Seven primary documents were read and none carries a pre-reform
pairing (`FINDING-capx-d75-2026-09-06.md` §2). Any consumer needing to blend
PJM's two solar classes into one must therefore carry a documented
cross-vintage reconciliation and say so at the seam; it must never estimate the
split, size it to a residual, or back it out of PJM's cleared solar UCAP
(rules 13/14).
