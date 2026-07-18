# NYISO Zonal-Sufficiency Test — doc-07 Design Decision 1 (2026-06-12)

Status: **complete — 5 zones stand, decisively.** This is the empirical gate
for the NYISO topology (doc 07, prompt P10 step 2 / design decision 1): does
NYISO need its downstate split (the 5-zone model — Upstate_West, Capital_Hudson,
Lower_Hudson, NYC, Long_Island), or is one copper-plate price good enough? The
model zones are the simple mean of their constituent NYISO load zones, so the
actual day-ahead zonal LBMP spreads against Upstate_West (zone A's aggregate)
answer it directly.

Reproduce with `python scripts/nyiso_zonal_sufficiency.py --md` (reads the
committed `NYISO/` LBMP zips via `scripts/data/derive_actual_lmp.py`).

## Zone-spread duration curves — day-ahead, $/MWh

Signed mean is `A − B` (positive ⇒ the downstate zone is dearer than upstate);
the percentiles and threshold shares are on the **absolute** spread. `J-A` is
NYC − Upstate_West, `K-A` Long_Island − Upstate_West, `F-A` Capital_Hudson −
Upstate_West.

| year | spread | signed mean | \|s\| p50 | \|s\| p90 | \|s\| p99 | % \|s\|>$5 | % \|s\|>$20 |
|---|---|---|---|---|---|---|---|
| 2023 | J-A | +7.86 | 4.33 | 18.56 | 39.15 | 46.4% | 8.2% |
| 2023 | K-A | +14.68 | 10.23 | 29.98 | 88.88 | 74.2% | 21.4% |
| 2023 | F-A | +10.30 | 3.93 | 25.92 | 74.53 | 46.0% | 16.2% |
| 2024 | J-A | +5.81 | 2.68 | 10.11 | 66.80 | 23.5% | 4.9% |
| 2024 | K-A | +9.80 | 4.45 | 21.11 | 85.28 | 45.9% | 10.4% |
| 2024 | F-A | +4.54 | 1.49 | 6.05 | 68.00 | 12.1% | 4.5% |
| 2025 | J-A | +9.52 | 4.53 | 23.01 | 85.70 | 45.4% | 11.2% |
| 2025 | K-A | +12.98 | 4.99 | 39.39 | 97.76 | 50.0% | 19.0% |
| 2025 | F-A | +9.26 | 2.50 | 22.93 | 117.71 | 28.9% | 10.8% |

All three years carry a full 8760; the spreads agree on the regime.

## What the curves say

1. **Downstate–upstate congestion is large, persistent, and one-signed — a
   single zone would miss the defining feature of NYISO.** Every spread is
   **positive in 100% of the > $20 hours**: NYC, Long Island and the Capital
   region are *always* the dear side, upstate (Niagara/St-Lawrence hydro plus
   the western wind belt) always the cheap side. This is the UPNY-SENY /
   Central-East / Long-Island-cable congestion that the 11 NYISO zones exist to
   price, and it is not a tail curiosity: the signed mean is **+$5 to +$15/MWh**
   on every pair every year, and the median K-A spread alone is $4–10.

2. **Long Island (K-A) is the load-bearing split.** It is the widest spread in
   all three years — p99 **$85–98/MWh**, **>$20 in 10–21% of hours**, and >$5
   in **46–74%**. The Y-49/Y-50 and Neptune/CSC cable limits make Long Island a
   chronic import pocket; a copper-plate model would mis-state a fifth of the
   year's downstate energy value. K-A separation spreads across the year —
   winter gas peaks plus a real **summer** share (37% of the 2024 wide hours)
   as the island's air-conditioning peak loads the cables.

3. **NYC (J-A) and the Capital region (F-A) separate materially too.** J-A
   runs p99 $39–86 with >$20 in 5–11% of hours; F-A p99 $74–118 with >$20 in
   4.5–16%. The Capital spread (the Central-East interface, zone F vs the
   upstate west) is as wide as NYC's at the tail — Central-East is one of the
   most-bound interfaces on the system — which is why Capital_Hudson is kept
   distinct from both Upstate_West and the Lower-Hudson/NYC pocket.

4. **Separation concentrates in the evening peak and in winter.** The top
   hours-of-day are **HB 17:00–19:00** for every spread every year — the
   downstate evening ramp when the in-city and Long Island gas/oil units set
   price over the import limits. Seasonally the wide hours are **winter-heavy in
   2024–2025** (82–87% of J-A/F-A wide hours land in winter — the gas-spike
   cold snaps that hit downstate hardest), with 2023 more evenly split into the
   spring shoulder; Long Island adds the summer-peak share noted above.

## Decision

**Keep the 5-zone topology (Upstate_West / Capital_Hudson / Lower_Hudson / NYC
/ Long_Island).** The empirical gate of design decision 1 passes decisively:
the actual zonal LBMPs show a large, recurring, one-signed downstate-dear
congestion regime that a single zone cannot reproduce — far stronger than the
CAISO north-south case. The load-bearing splits are **Long Island (K)** and
the **NYC/Lower-Hudson downstate pocket (J/H-I)** behind the UPNY-SENY and
cable interfaces, with the **Capital/Central-East (F)** split a close third.

The next refinement lever, per design decision 1, is the **interface TTCs**
(Central-East, UPNY-SENY/Total-East, Dunwoodie-South, and the Long Island
cables — upload U7) rather than more zones: the binding constraints are a
handful of named interfaces, not finer geography. U7 (interface flows + limits)
was **not present** in this drop, so the Gold-Book Tier-3 TTC seeds stand for
now; when a calibrated run's modelled K-A / J-A duration curves fall short of
the table above, refine those interface limits before reaching for more
topology.
