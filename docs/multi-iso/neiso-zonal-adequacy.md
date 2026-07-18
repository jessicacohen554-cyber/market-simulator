# NEISO Zonal-Sufficiency Test — doc-08 Design Decision (2026-06-12)

Status: **complete — 4 zones stand, but weakly; the split is structural, not
price-driven.** This is the empirical gate for the ISO-NE topology (doc 08,
prompt P10 step 2): does ISO-NE need its load-pocket split (the 4-zone model —
North, Central, Boston, Connecticut), or is one copper-plate price good enough?
The model zones are the simple mean of their constituent SMD load-zone sheets
and the hub is the `.H.INTERNAL_HUB` ("ISO NE CA" sheet), so the actual
day-ahead zone-vs-hub spreads answer it directly.

Reproduce with `python scripts/neiso_zonal_sufficiency.py --md` (reads the
committed `NEISO/*_smd_hourly.xlsx` via `scripts/data/derive_actual_lmp.py`).

## Zone-vs-hub spread duration curves — day-ahead, $/MWh

Signed mean is `zone − hub` (positive ⇒ the pocket is dearer than the hub);
the percentiles and threshold shares are on the **absolute** spread. `North` is
the ME/NH/VT (Maine-led) zone; `Boston` is NEMASSBOST; `Connecticut` is CT.

| year | spread | signed mean | \|s\| p50 | \|s\| p90 | \|s\| p99 | % \|s\|>$5 | % \|s\|>$20 |
|---|---|---|---|---|---|---|---|
| 2023 | Boston-Hub | +0.30 | 0.23 | 0.62 | 2.01 | 0.2% | 0.1% |
| 2023 | Connecticut-Hub | -0.78 | 0.51 | 1.54 | 4.98 | 1.0% | 0.1% |
| 2023 | North-Hub | -0.18 | 0.25 | 0.85 | 2.73 | 0.2% | 0.0% |
| 2024 | Boston-Hub | +0.55 | 0.35 | 1.09 | 4.39 | 0.8% | 0.2% |
| 2024 | Connecticut-Hub | -1.18 | 0.79 | 2.44 | 6.94 | 2.7% | 0.0% |
| 2024 | North-Hub | -0.06 | 0.28 | 1.08 | 4.49 | 0.8% | 0.1% |
| 2025 | Boston-Hub | +0.81 | 0.52 | 1.90 | 3.80 | 0.3% | 0.0% |
| 2025 | Connecticut-Hub | -1.87 | 0.97 | 4.46 | 13.47 | 7.4% | 0.7% |
| 2025 | North-Hub | -0.40 | 0.54 | 2.42 | 6.94 | 1.8% | 0.1% |

All three years carry a full 8760 (the SMD workbook is a fixed 24-hour clock).

## What the curves say

1. **ISO-NE's zones track the hub very closely — the price separation is an
   order of magnitude smaller than NYISO's or CAISO's.** Every pocket-vs-hub
   median is **under $1/MWh**, every p90 under $5 except CT-2025, and **> $20
   hours are rare everywhere** (≤ 0.2% for Boston and North in all years; 0.7%
   for CT at its widest). A single copper-plate ISO-NE price reproduces the
   day-ahead energy value to within a dollar or two for the overwhelming
   majority of hours. This matches the post-2018 reality: the NEEWS / Greater
   Boston / Maine-NH transmission build-out and the gas-on-the-margin price
   formation make ISO-NE largely a **level** market — when prices spike it is
   the whole pool moving together on winter gas, not one pocket separating.

2. **Connecticut carries what little separation there is, and it is on the
   *cheap* side.** CT-Hub is the only spread with a meaningful tail — p99 grows
   from $5 (2023) to $13.5 (2025) and the > $5 share reaches 7.4% in 2025 — and
   its signed mean is **negative** (CT $0.8–1.9/MWh *below* hub, 0% of the wide
   hours dear). CT and SW-CT are well-supplied (Millstone plus the NEEWS
   imports) and sit below the system hub when the eastern load pockets pull the
   hub up. The widening through 2025 is worth watching but is still a minor
   effect. Its wide hours are **winter, HB 17:00–18:00** — the cold-snap
   evening peak.

3. **Boston is dear but barely, and the Maine-led North is a wash.** Boston-Hub
   is positive every year (the NEMA import pocket) but only **+$0.3–0.8/MWh**
   mean with a p99 under $4.5 — the Greater Boston upgrades have all but erased
   the old NEMA premium. North-Hub straddles zero (mean −$0.4 to −$0.1): the
   export-constrained Maine corner shows up as a thin negative tail (Maine wind
   spilling below hub) but nothing structural. Neither pocket separates enough
   on price to *require* its own zone.

## Decision

**Keep the 4-zone topology (North / Central / Boston / Connecticut), but on
structural grounds, not price separation.** The empirical gate passes only
weakly: unlike NYISO (large, one-signed downstate-dear spreads) or CAISO
(recurring north-south congestion), ISO-NE's zones rarely part from the hub by
more than a few dollars, and a single-zone price would be a defensible
approximation for level (not congestion) accuracy. The zones are retained
because (a) they match ISO-NE's own load zones and the interface topology the
backcast's imports/TTC logic keys off, (b) **Connecticut** is the one pocket
with a growing tail (CT-Hub p99 $5→$13.5 over 2023–2025) and is cheap to keep,
and (c) zonal **load** — which the SMD workbooks also carry, see the note below
— is the load-bearing reason for the split even where price is flat.

The next refinement lever is therefore **not** finer topology nor (yet) the
interface TTCs: the spreads are too small to be TTC-limited in most hours.
Upload U6 (interface flows + limits) was **not present** in this drop, so the
RSP Tier-3 TTC seeds stand; revisit only if CT-Hub keeps widening or a
calibrated run over-states the inter-zone spreads above.

## Note — zonal load (out of scope here)

The ISO-NE SMD workbooks (`*_smd_hourly.xlsx`) carry per-zone **`DA_Demand` /
`RT_Demand`** alongside the LMPs used here. That is a clean, hourly,
already-zonal load series — a better source than the current EIA-930 / load-
share path for the NEISO **U3 / P8 demand refresh**. Flagged for that follow-on
task; it is deliberately not actioned in this P10 LMP pass.
