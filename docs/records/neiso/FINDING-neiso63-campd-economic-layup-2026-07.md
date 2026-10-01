# FINDING — CAMPD unit-outage detector books ECONOMIC LAYUP as outage (neiso-63, 2026-07-24)

**Charter.** Owner-authorized re-audit of the NEISO CAMPD unit-outage extract,
opened by `neiso-62` (2026-07-24): arming ISO-NE's own published availability
instrument restored ~4,458 MW annual / ~5,779 MW winter of thermal capacity and
moved mean LMP −7 to −9 %, which put the keeper's offer curves under the rule-11
"the estimate was silently compensating" condition. This audit asks whether the
extract is wrong, why, and what a fix would have to look like. **No solve, no
keeper change, no parameter touched.** Model Opus.

## Verdict

The detector over-counts thermal outages, the cause is **sustained economic
layup being booked as mechanical outage**, and the defect is **not
NEISO-specific — it is present in every one of the six ISO extracts**. The
`2026-07-19` phantom-outage re-audit did not catch it because that audit
screened for the ERCOT-79 *daily-cycling* signature, which is a different
failure mode with a different fingerprint.

## Evidence — four independent signatures

### 1. Seasonal profile is anti-correlated with the published truth

Extract outage MW vs ISO-NE Morning Report Section 3 line C (published
generation outages and reductions), daily means, full-year windows excluded:

| year | DJF | MAM | JJA | SON | annual |
|---|---:|---:|---:|---:|---:|
| 2023 detector / published | 7,544 / 2,929 = **2.58×** | 8,265 / 6,073 = 1.36× | 4,862 / 2,515 = 1.93× | 7,166 / 6,780 = **1.06×** | 1.52× |
| 2024 detector / published | 6,879 / 2,493 = **2.76×** | 8,362 / 5,180 = 1.61× | 4,452 / 2,369 = 1.88× | 6,417 / 6,663 = **0.96×** | 1.56× |
| 2025 detector / published | 4,478 / 2,545 = **1.76×** | 6,207 / 5,627 = 1.10× | 2,306 / 1,897 = 1.22× | 4,727 / 5,469 = **0.86×** | 1.14× |

ISO-NE's own profile is the textbook maintenance profile — **low in both peak
seasons (winter, summer), high in the shoulders**. The detector agrees almost
exactly in autumn (0.86–1.06×) and blows out in winter (1.76–2.76×). A detector
that reproduces the published series when real maintenance dominates, and
diverges hardest in the season when New England gas-fired CCs are priced out of
merit by winter basis, is not making a random error.

### 2. Simultaneity: half the CC fleet "out" at once

January 2023, `CC_REGULAR`: **31 of 58 units (53 %, 6,645 MW) flagged
simultaneously out**, against ISO-NE's 2,929 MW across *all* generation. July —
the month CCs actually run — carries the fewest, 11 units / 2,388 MW. Mechanical
outages are idiosyncratic; this is common-mode.

### 3. Repeat-event count is mechanically implausible

NEISO `CC_REGULAR`, 2023: **median 7 separate "outages" per unit-year**, max 15,
**mean 153 days out = 42 % of the year**. Two units at facility 55661 carry 15
windows each. No combined-cycle plant breaks fifteen times a year. This is a unit
cycling in and out of the market on economics, with every ≥5-day idle gap booked
as an outage.

### 4. The defect is in the filter's stated premise

`scripts/lib/outage_detect.py::filter_revealed_outages` keeps a down span when it
is **down through ≥ `MIN_INMERIT_HOURS` (24) high-net-load hours**, and
separately when it is a ≥5-day full stop below `FULL_STOP_OVERRIDE_CF`. The
override's docstring states the governing assumption outright:

> *economic idling backs down but does not fully stop for weeks*

That premise is **false for a New England gas CC in a high-basis winter**, which
simply does not start for weeks. Both surviving branches therefore keep exactly
the wrong windows: an economically laid-up unit is (a) down through its period's
local high-load hours and (b) a sustained full stop. The `high_load_mask` is a
*local* rolling percentile, so a unit laid up for a whole month is still scored
against that month's own peaks.

## What a fix must and must not look like

Two candidate repairs were tested against the published series and **both are
ruled out**. Recording them so a future session does not rebuild them.

**Unit-level frequency filtering — ruled out.** Restricting to units with ≤3
windows/unit-year sharply improves the *shape* (monthly correlation with the
published series +0.53→+0.84, +0.47→+0.75, +0.70→+0.96 for 2023/24/25) but
collapses the *level* (410 vs 4,575 MW in 2023). Real outages also live inside
high-frequency units' records. **The contamination is window-level, not
unit-level** — that is the binding constraint on any fix.

**Common-mode (class-simultaneity) discrimination — ruled out.** Dropping
windows whose span-mean class-down fraction exceeds τ, one τ across all three
years: at every τ ∈ [0.30, 0.50] the seasonal correlation is *worse than applying
no filter at all* (best case +0.18/+0.28/+0.58 at τ=0.45 where the level roughly
lands, against +0.53/+0.47/+0.70 unfiltered). Genuine shoulder maintenance is
itself strongly clustered, so simultaneity does not separate the two populations.

**Leading remaining candidate: a merit-order guard.** The phenomenon is
fuel-economic, so the discriminator should be too — delivered fuel price plus the
unit's heat rate to test whether the unit was out of merit across the window.
Delivered fuel prices are an explicitly admissible physical input (rule 13), and
the detector already carries class-specific economic guards (`ST_GAS_CF_PEAK`,
`SHORT_BASELOAD_CF`). This is a **mechanism change** and needs its own charter
with the design frozen before the build, plus leave-one-year-out scoring
(rule 22) — it is deliberately *not* attempted here.

**Not admissible:** reconciling the extract by scaling or trimming it until the
model's prices match actuals. The published outage series may anchor the
*input* (rule 14 reconciliation), never the dispatch outcome (rule 13).

## Cross-ISO: this is a detector-wide systematic

Repeat-event signature, 2023–2025, full-year windows excluded, per unit-year:

| ISO | class | median windows | max | mean days out | % of year |
|---|---|---:|---:|---:|---:|
| ERCOT | CC_REGULAR | 3.0 | 26 | 86 | 24 % |
| ERCOT | COAL | 3.0 | 16 | 92 | 25 % |
| CAISO | CC_REGULAR | 7.0 | 21 | 134 | 37 % |
| MISO | CC_REGULAR | 4.0 | 18 | 85 | 23 % |
| MISO | COAL | 4.0 | 16 | 110 | 30 % |
| NEISO | CC_REGULAR | 7.0 | 16 | 142 | 39 % |
| NYISO | CC_REGULAR | 6.0 | 17 | 168 | **46 %** |
| PJM | CC_REGULAR | 3.0 | 18 | 83 | 23 % |
| PJM | COAL | 4.0 | 16 | 152 | 42 % |

Every ISO books 23–46 % of its CC capacity-year as outage. Typical real CC
EFOR plus planned maintenance is roughly 10–15 % combined. Since the four
DAM-first availability gates wired 2026-07-24 (`caiso_dam_outages`,
`miso_native_outage_source`, `neiso_operable_capacity_availability`,
`pjm_dam_availability`) give CAISO / MISO / NEISO / PJM a *published* instrument
to check against, the same published-vs-detector comparison run here is now
available for four of the six ISOs at no solve cost.

## Consequences

- **The NEISO keeper's offer curves are co-dependent on the over-count.**
  Relieving it (neiso-62 A1) moved mean LMP −7 to −9 % and halved h>$200
  (70→26 in 2023, 102→42 in 2025). That is the ERCOT-79 / nyiso-63 condition.
- **The `neiso-62` denominator question is now secondary.** Reconciling the
  ISO-NE fraction to a thermal basis matters only if the overlay is load-bearing;
  the correct sequencing is to fix the detector first and let the overlay serve
  as the *validation instrument* it is well suited to be (fleet-grain aggregates
  cannot carry per-unit availability).
- **The NEISO frontier (2026-07-11) and calibration-complete marker
  (2026-07-07) are open questions**, not withdrawn: unlike nyiso-63 the
  determination did not flip and the fit improved. Recommend freezing further
  holdout spending until the extract settles.
- **Scope is all six ISOs**, so this is a governance item, not a NEISO-lane item.

## Reproduction

All figures are derived from committed artifacts with no LP solve:
`data/raw/campd-unit-outages{,-CAISO,-MISO,-NEISO,-NYISO,-PJM}.csv` and
`data/raw/neiso-operable-capacity/neiso_operable_capacity_<YYYY>.csv`.
Impact figures are from `2026-07-24-neiso-62-opcap-a0` / `-a1`.
