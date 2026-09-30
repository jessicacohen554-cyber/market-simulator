# RESULT — PJM-NEXT-14 (2026-09-30): low-end price-setters named; supply point, normalizer and median aggregation refuted

**Keeper unchanged:** `2026-09-28-pjm-next8-exitfix`.
- **Solves:** one diagnostic keeper replay (2020, one shard, Δ = 0.000 TWh vs the keeper). Nothing registered or promoted.
- **Owner ruling:** *"Record, hand off"*.
- **Detail:** `docs/FINDING-pjm-next-14-lowend-units-supply-point-midcurve-2026-09-30.md`.

| card | result |
|---|---|
| 1 — who prices the low end | In 2020 low-end hours, the LP's marginal units are CC econ/min-load (32 %) and coal econ (18 %), at 7.8 × delivered gas; the real price sits at 5.5 ×. |
| 2 — plant gas supply point | EIA-860 pipeline fields put 28–33 % of CC MW on production-area supply. The keeper prices these CCs at their measured delivered cost, tracking the EIA-923 premium year by year. **Closed.** |
| 3 — mid-curve floor | The normalizer is inert (shape form cancels it; LONG_RUN round-trips exactly). Rank-matching the median **raises** bids (coal +2.3/+9.6, marginal CC +2.7 $/MWh). PJM's cheap CC block (a quarter of capacity at ≤ 3.5 × delivered gas) exists in both a fit year and a miss year. |

**Status (unchanged):** training span NOT-YET on one row (C1 CC_REGULAR 2023 +8.48); run-level NOT-YET, 14 out-of-span rows.

**OPEN (not limits):** C3a 2019/2020 and the floor; COAL_BIT 2019/2021; CT_PEAKER 2021.

**Next (PJM-NEXT-15):** PJM's price-taking CC offer block by year (all seven years of the corpus), jointly with the CC volume over-run it would worsen (pjm-h20/h21).
