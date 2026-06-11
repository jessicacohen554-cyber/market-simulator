# CAISO Zonal-Sufficiency Test — doc-06 Design Decision 3 (2026-06-11)

Status: **complete — 3 zones stand.** This is the empirical gate for the
CAISO topology (doc 06, prompt P10 step 2 / design decision 3): does CAISO
need to be modelled zonally (NP15 / ZP26 / SP15), or is one copper-plate
price good enough? The trading hubs *are* the model zones, so the actual
day-ahead hub-LMP spreads answer it directly.

Reproduce with `python scripts/caiso_zonal_sufficiency.py --md`
(reads the committed `CAISO_dam_hourly_{year}.csv` aggregates).

## Hub-spread duration curves — day-ahead, $/MWh

Signed mean is `A − B` (positive ⇒ the first hub is dearer); the percentiles
and threshold shares are on the **absolute** spread.

| year | spread | signed mean | \|s\| p50 | \|s\| p90 | \|s\| p99 | % \|s\|>$5 | % \|s\|>$20 |
|---|---|---|---|---|---|---|---|
| 2024 | NP15-SP15 | +7.99 | 2.28 | 28.79 | 66.38 | 35.1% | 16.8% |
| 2024 | NP15-ZP26 | +8.58 | 1.98 | 28.35 | 63.98 | 34.5% | 16.3% |
| 2024 | SP15-ZP26 | +0.58 | 0.94 | 5.98 | 22.27 | 12.5% | 1.3% |
| 2025 | NP15-SP15 | +6.01 | 2.99 | 20.50 | 46.02 | 35.5% | 10.3% |
| 2025 | NP15-ZP26 | +5.73 | 2.13 | 19.43 | 47.12 | 32.2% | 9.5% |
| 2025 | SP15-ZP26 | -0.28 | 1.16 | 4.87 | 17.22 | 9.5% | 0.7% |

2023 is excluded: OASIS's ~39-month retention had aged most of the 2023 DAM
out by the mid-2026 pull, leaving a ~3-trade-date stub (see
`caiso-data-audit.md` §4 U2). The two full years agree on the regime.

## What the curves say

1. **North–south congestion is real and material — a single zone would miss
   it.** NP15 separates from the south (SP15/ZP26) by more than $20/MWh in
   **16.8% of hours (2024)** and **10.3% (2025)**; the p99 spread is
   $46–66/MWh and the p90 is $20–29/MWh. A copper-plate model collapsing
   these into one price would mis-state a sixth of the year's day-ahead
   energy value at the zone level. The median is small ($2–3) — the hubs sit
   on top of each other most hours — but the *tail* is where the dispatch
   and the congestion rent live.

2. **NP15 is almost always the expensive side** (98–99% of the >$20 hours).
   This is Path 15 binding north-of-import: the south is long on solar and
   the constrained north pays up. The separation concentrates in the
   **solar shoulder seasons** (Mar–May and Oct–Nov carry ~55–60% of the
   >$20 hours) and in **midday/morning-ramp hours** (08:00–14:00 local hold
   the top hour-of-day shares) — exactly when south-to-north solar flows
   load Path 15.

3. **The two southern hubs move together — ZP26 carries little independent
   price signal.** SP15−ZP26 exceeds $20 in only **0.7–1.3%** of hours
   (p90 ≈ $5), versus ~10–17% for NP15 against either. ZP26 (the small
   ~6%-of-load central zone) and SP15 are effectively one price node in the
   day-ahead. Keeping ZP26 separate costs nothing and matches CAISO's
   trading hubs, but the load-bearing split is **NP15 vs. South**.

## Decision

**Keep the 3-zone topology (NP15 / ZP26 / SP15).** The empirical gate of
design decision 3 passes: the actual hub spreads show a recurring
north-south congestion regime that a single zone cannot reproduce, so zonal
modelling is justified. The next refinement lever, per design decision 3, is
the **Path 15 TTC** (upload U5) rather than adding zones — the binding
constraint is one interface, not many. If a calibrated run's modelled
NP15−SP15 duration curve falls short of the table above, refine that TTC
before reaching for finer topology. ZP26 could be folded into a southern
zone with minimal price error if simplification is ever wanted, but there is
no cost to leaving it as its own hub.
