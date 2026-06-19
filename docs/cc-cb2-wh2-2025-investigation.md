# Why Colorado Bend II (60122) & Wolf Hollow II (59812) over-generate in 2025

**Status:** diagnosis only — no parameter changed. Keeper = **run120**
(`results/calibration/run120_meritramp_defensible`, merit-ramp + outage overlay
+ sigmoids + lignite floor + cc-duct, CT deployment OFF). All numbers below are
measured from that bundle, the CEMS facility files, and the model's own
zone/fleet code. Companion reads: `docs/cc-high-cf-investigation.md`,
`docs/binning-methodology.md`, `docs/audit-followup-tests-2026-06.md`.

## The thing to explain

Both plants over-run *mildly* in cheap-gas years and *badly* in high-gas 2025
(`plant_hourly_fit.parquet`):

| plant | base_hr | 2023 (gas $2.54) | 2024 ($2.19) | 2025 ($3.52) | CAMPD GWh 23→25 | model GWh 23→25 |
|---|---|---|---|---|---|---|
| CB2 (60122) | **6.57** | +2.3% | +1.6% | **+13.0%** | 7859 → 6102 (**−22%**) | 8043 → 6893 (**−14%**) |
| WH2 (59812) | **6.65** | +5.1% | +5.3% | **+18.5%** | 7012 → 5505 (**−21%**) | 7369 → 6522 (**−12%**) |

The single sentence that frames everything: **the real plants cut output ~21–22%
from 2023 to 2025 as gas rose; the model cut only 12–14%.** The over-run *is* the
model's failure to follow the high-gas back-down. In 2025 both plants run at a
model online-CF of ~0.86 while CEMS shows them at a mean online CF of **0.66**
(`TX_2025.parquet`: CB2 mean online CF 0.665, WH2 0.662; 36–38% of online hours
below 0.6 CF). The whole gap lives in *dispatch intensity*, not starts.

CF-band view, 2025, `--cf-band-width 0.05` rolled to 0.10 bands
(`plant_cf_bands.parquet`), model **M** vs CAMPD **C**:

```
              0-.1  .1-.2  .2-.3  .3-.4  .4-.5  .5-.6  .6-.7  .7-.8  .8-.9  .9-1.0
CB2  M         820     9   1433    71     46    129    278    523   2622   2829
     C         948   409    159  1154    893    178    224    478   3342    975
WH2  M        1412     0     30   116    257    462   1374    665   4287    157
     C        1492   350    171  1573    536    132    171   1671   1688    976
```

CAMPD parks ~1500–2000 hours at 0.3–0.5 CF (real cycling); the model puts almost
nothing there and instead piles into 0.8–1.0. That pile is the over-run.

---

## Ranked causes (by measured contribution)

### 1. MERIT / heat-rate — PRIMARY driver, and the reason 2025 is worst — *offer-tunable, but only partly*

CB2 and WH2 carry the **two lowest base heat rates in the entire CC_REGULAR
fleet**: 6.57 and 6.65 MMBtu/MWh against a fleet median of 7.39 and mean of 8.10
(min 6.52, max 15.4 — `data/raw/reference/custom-bin-assignments.csv`). At 2025 gas $3.52
their econ-tranche marginal cost is ≈ 6.6 × ~1.0 × 3.52 + VOM ≈ **$25/MWh**, the
cheapest gas in ERCOT; the fleet-mean CC sits at ≈ $28.5 and the worst at ≈ $54.

Consequence: when gas rises in 2025 and the system backs gas down, the LP backs
down the $35–54 units first and **never reaches the $25 units** — so the lowest-HR
plants get *over-protected at the bottom of the merit order* precisely in the
high-gas year. That is the mechanism behind the table above (real −21%, model
−12%). The cheaper a unit is relative to its peers, the more the model pins it
flat when gas climbs.

The intra-zone signature confirms it: **Houston is balanced at the zone level
(+0.9%) yet CB2 inside it is +13%** (see §3 table). The LP fills the single
cheapest Houston unit (CB2) flat-out and backs its Houston neighbours down to
compensate; reality spreads the duty (AS, local limits, commitment rotation).

- **Evidence:** `data/raw/reference/custom-bin-assignments.csv` (base_hr fleet-min);
  `plant_cf_bands.parquet` (flat pin vs CAMPD cycling); `meta.json` gas $3.52;
  the year-gradient table above.
- **Tunable?** Partly. D4 (`docs/audit-followup-tests-2026-06.md`) showed the
  merit-ramp cut WH2 from +21.7% → +17.6% — it helps the *shape* (cf_emd/r 18/18)
  but **no offer lever closes the 2025 volume over-run**, because the residual is
  the structural pieces below. Offer-tunable on the margin, structural at the core.

### 2. AS withholding — STRUCTURAL (absent from dispatch) — *not offer-tunable; needs the AS dispatch fix*

The model represents ERCOT AS **only as a capacity-economics credit**
(`src/market_sim/model/ancillary.py`: a per-kW-yr revenue stream for the
retirement/entry screens, default off, explicitly "NOT an AS co-optimization").
There is **no AS reserve constraint in the dispatch LP** — nothing holds an online
unit below its max to carry RRS/ECRS/Reg/Non-Spin. So the backcast dispatches
CB2/WH2 flat-out with zero reserved headroom.

CB2 and WH2 are exactly the flexible F-class 2×1 CCs that carry ERCOT reserves.
The CEMS signature of that withholding is unmistakable in 2025: each plant exceeds
0.9 of its own demonstrated max in only **12% (CB2) / 16% (WH2) of its online
hours** (`TX_2025.parquet`) — a persistent ~10% headroom ceiling even when running
hard. ECRS launched mid-2023 and its procurement scaled through 2024–2025, so the
withholding is *larger in 2025*, matching the year gradient.

- **Estimated contribution:** ~10% of nameplate held off across the ~4,500
  hard-run online hours ≈ **0.4–0.5 of the over-run** (~0.5 TWh on WH2, ~0.5 TWh
  on CB2). Bounded estimate — no per-plant AS award file is in-repo to measure it
  exactly; quantified from the online-hour CF ceiling.
- **Evidence:** `ancillary.py` (capacity-only AS, no dispatch reserve);
  `TX_2025.parquet` online-hour CF ceiling.
- **Tunable?** Structural. This is the headroom the **parallel-session AS fix**
  targets; an offer-curve proxy (a higher peak wall) cannot reproduce a reserve
  obligation cleanly.

### 3. SPATIAL / zonal — STRUCTURAL — *not offer-tunable; sub-zonal, needs nodal*

Zone assignment (`src/market_sim/data/zone_assignment.py`, via eGRID coords):
**WH2 → North**, **CB2 → Houston** (Wharton county 481).

WH2's over-run is part of the documented North-over / South_Central-under
imbalance. CC_REGULAR by model zone, 2025 (`plant_hourly_fit` + `assign_zone`):

| zone | n | model GWh | CAMPD GWh | over | over% |
|---|---|---|---|---|---|
| **North** (WH2) | 15 | 72663 | 68042 | **+4621** | **+6.8%** |
| **South_Central** (Guadalupe) | 7 | 21124 | 23506 | **−2383** | **−10.1%** |
| Houston (CB2) | 5 | 14049 | 13923 | +126 | +0.9% |
| South | 6 | 8571 | 7840 | +731 | +9.3% |
| Northeast | 1 | 2918 | 4624 | −1705 | −36.9% |
| West | 2 | 9226 | 10696 | −1470 | −13.7% |

The class **nets to −79 GWh** — a near-balanced volume that is badly
*misallocated in space*. WH2 (North, +18.5%) and Guadalupe (South_Central, −8.8%)
are a textbook North-over/SC-under pair.

Why the model can't self-correct: **prices are identical across Houston / North /
South / South_Central in every year** (2025 = $31.98 in all four;
`system.parquet`). The reduced network is a copper plate among the load zones —
those interfaces never bind — so a CC faces the *same* LMP wherever it sits and
nothing throttles it locationally.

The throttle reality applies lives **below zonal resolution**. From the SCED
binding-constraint archive (`docs/sced-binding-constraints-2023-2025.csv`,
confirming the audit's D4-spatial pre-test): 94% of congestion rent is on local
< 200 kV pockets. CB2 sits in the Wharton/coastal cluster behind STP-area 345 kV
+ 138 kV limits that bind thousands of intervals (`STPWAP39_1` 7,776 binds /
24.4%; `BLESSING_1382` 2,525 binds; `BLESSI_LOLITA1_1` 2,268) — local pockets that
back the coastal CCs down in reality. WH2 sits in the DFW-southwest North pocket.
None of these maps onto a model zonal interface, so the model cannot reproduce the
local back-down.

- **Evidence:** `zone_assignment.py` (zones); the by-zone table above;
  `system.parquet` (identical zonal prices); `sced-binding-constraints-2023-2025.csv`.
- **Tunable?** Structural — and *not even finer-zone-tunable* (D4-spatial
  pre-test: no zonal interface binds; capturing it needs a nodal model or a
  data-targeted out-of-merit floor over dozens of SCED pockets).

### 4. CAPACITY / vintage — RULED OUT (measured) — n/a

Not a driver for these two. Run120 cap_mw (capacity-reconciled) is at or slightly
**below** the demonstrated CEMS peak, not inflated:

| plant | model cap_mw (2025) | CEMS max | CEMS p99.9 |
|---|---|---|---|
| CB2 | 1172.8 | 1201 | 1195 |
| WH2 | 1163.5 | 1175 | 1169 |

(`plant_hourly_fit.parquet` cap_mw; `TX_2025.parquet`.) The raise-only
reconciliation (`docs/cc-high-cf-investigation.md`) sized these correctly. This is
the opposite of CB EC (60122's neighbour 56350, nameplate *above* real peak) and
Freestone (nameplate *below* real peak) — those are capacity-axis problems; CB2/WH2
are not.

### 5. COMMITMENT — RULED OUT (measured) — n/a

Not a driver. Per-plant committed (min-stable) shares are CAMPD-P5-derived:
**CB2 36.6%, WH2 32.3%** (`fleet.CC_REGULAR_COMMITTED_PCT_BY_PLANT`, applied under
`cc_committed_per_plant`) — moderate floors, not a high pin. Online fraction is
about right: model near-zero (0–0.1 CF) hours are CB2 820 / WH2 1412 vs CAMPD 948 /
1492 — the model is online *slightly more* but comparably. The plants are not
"stuck on"; they are stuck **high**, which is the merit cause (§1), not commitment.
If anything the model lacks CAMPD's 0.1–0.2 CF startup/min-load hours (CB2 9 vs 409;
WH2 0 vs 350) — a minor ramp-shape miss, not the over-run.

---

## Summary

| # | cause | 2025 contribution | offer-tunable? |
|---|---|---|---|
| 1 | Merit / lowest-HR units over-protected at bottom of stack when gas rises | **primary** — drives the 2025-specific blow-up | partly (merit-ramp helps shape; volume not closable) |
| 2 | AS headroom absent from dispatch (capacity-credit only) | **~0.4–0.5 of over-run** (~0.5 TWh each) | structural (parallel AS dispatch fix) |
| 3 | Zonal copper-plate → no locational throttle; congestion is sub-zonal | real, sets the North-over/SC-under split | structural (sub-zonal; nodal-only) |
| 4 | Capacity/vintage | **none** — cap ≈ CEMS peak | n/a (ruled out) |
| 5 | Commitment / stuck-on | **none** — committed share moderate, online frac ~right | n/a (ruled out) |

Causes 1–3 overlap (they all explain the same missing back-down — the ~20-point
gap between the model's ~0.86 online CF and CEMS's ~0.66), so they are not cleanly
additive; the ranking is by which lever moves the 2025 over-run most. The honest
read matches the audit: the offer lever (merit-ramp) is largely spent, and the
residual CB2/WH2 2025 over-run is **structural — AS dispatch headroom plus
sub-zonal congestion — not a merit-tuning problem.**
