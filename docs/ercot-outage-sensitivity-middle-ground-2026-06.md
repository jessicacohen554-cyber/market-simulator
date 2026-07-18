# ERCOT outage sensitivity — finding the middle ground (2026-06)

**Date:** 2026-06-22
**Branch:** `claude/ercot-outage-sensitivity-j6a0p5`
**Touches:** `scripts/derive_campd_outages.py` (`high_load_mask`, `WINDOW_DAYS`),
`scripts/data/derive_campd_unit_outages.py` (shares the filter), and the regenerated
ERCOT `data/raw/campd-outages.csv` + `data/raw/campd-unit-outages.csv`.

## The problem

The revealed-availability **net-load filter** (`b0c41cb`, see
`docs/multi-iso/cross-iso-outage-regate-handoff-2026-06.md`) was added to drop
*economic-idle* coal/CC down-spans — a unit out of merit in a low-demand shoulder
week looks identical to a mechanical outage in CEMS, and feeding those false
outages to the energy+reserve co-opt read as a reserve shortfall and over-fired
ERCOT shoulder/winter prices to VOLL.

The filter kept a down span only if it overlapped ≥ `MIN_INMERIT_HOURS` (24)
hours above the **year's** `HIGH_LOAD_PCTL` (0.85) net-load percentile. That
single *annual* percentile makes "high load" mean **only the summer/winter
peak**. A genuine multi-week CCGT **shoulder maintenance** outage — by
definition entirely inside spring/fall — never spans an annual-top-15% hour, so
it was wrongly dropped as economic idle. The unit was then modelled fully
available all shoulder, i.e. the real outage *disappeared*.

Measured on the ERCOT CC fleet (2023–2025), the annual filter cut **69 %** of CC
outage GW-days and deleted unmistakably-real long continuous outages, e.g.:

| plant | year | window | length | cap |
|-------|------|--------|--------|-----|
| T H Wharton | 2024 | Jan 23 → Apr 27 | 96 d | 1190 MW |
| Gregory Power Plant | 2023 | Oct 02 → Dec 31 | 90 d | 470 MW |
| Tenaska Gateway | 2023 | Mar 01 → May 16 | 76 d | 940 MW |
| Barney M Davis [CC] | 2023 | Feb 02 → Apr 20 | 76 d | 730 MW |

No economically-idle unit stays continuously off for 90 days — it would return
the moment any afternoon tightened — so these are revealed real outages.

## The middle ground: a LOCAL (seasonal) net-load band

Keep the filter keyed on **exogenous net load** (no LMP, no price fit — the
non-negotiable rule), but compare each hour to the `pctl` percentile of a
**centered rolling ± `WINDOW_DAYS` (30) net-load window** instead of the single
annual percentile. The test becomes *"did the unit stay down through the
high-net-load hours of **its own period**?"*:

- A real shoulder outage spans that period's **local** peaks → **kept**.
- A short economic-idle gap **returns to service** during those same local peaks
  → its down-spans don't overlap them → **still dropped**.

Set `--high-load-window-days 0` to fall back to the legacy single-annual
percentile (the over-tight band).

## Result (ERCOT CC, 2023–2025, GW-days)

| regime | CC GW-days | vs unfiltered |
|--------|-----------|---------------|
| no filter (pre-fix, over-stated, incl. economic idle) | 9380 | — |
| **annual-0.85 (over-tight — killed shoulder outages)** | 2906 | −69 % |
| **local-30 (this change — middle ground)** | 5997 | −36 % |

It is **not a revert** — it is *more* selective at the short end and *recovers*
the long end. By continuous span length:

| span length | total GWd | annual keeps | local-30 keeps |
|-------------|-----------|--------------|----------------|
| 2–7 d (economic idle) | 2438 | 133 | **82** ← drops *more* |
| 7–14 d | 1742 | 196 | 763 |
| 14–21 d | 852 | 171 | 804 |
| 21–30 d | 803 | 187 | 803 |
| 30 d+ (real maintenance) | 3545 | 2219 | **3545** ← recovers all |

Summer binding outages are preserved (Jul kept 572 → 539, Aug 211 → 190), so the
fix restores shoulder maintenance without re-inflating the economic-idle mass
that caused the original over-fire and without under-firing the summer.

## Scope / follow-ups

- The filter (`high_load_mask`) is **shared** by the facility- and unit-level
  detectors and across all ISOs. Only the **ERCOT** CSVs were regenerated here
  (the user's scope). Every other ISO's `campd-*-outages-<ISO>.csv` is still on
  the annual band and will pick up the local band automatically on its next
  per-ISO re-gate (see `cross-iso-outage-regate-handoff-2026-06.md`).
- **Not yet re-gated:** the ERCOT keeper was scored against the over-tight
  outages. Re-solve it byte-faithfully on these regenerated inputs (changing only
  the outage CSVs) and gate vs actuals for all years + the tail before adopting
  as the keeper, per the handoff rules. Expect *more* coal/CC offline in
  shoulder months → modestly firmer shoulder prices than the over-tight run, but
  cooler than the pre-fix VOLL over-fire.

## Reproduce

```bash
python scripts/derive_campd_outages.py      --iso ERCOT --years 2023 2024 2025
python scripts/data/derive_campd_unit_outages.py --iso ERCOT --years 2023 2024 2025
# legacy annual band for A/B: add  --high-load-window-days 0
```
</content>
</invoke>
