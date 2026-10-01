# FINDING nwpp-48: C4 phase 0. No lever is ready, so no solve.

**Lane:** NWPP-48 · **Date:** 2026-09-23 · **Zero LP.** No mechanism tested, nothing registered, no
matrix cell moves (rule 28(b) does not bind a lane that tests nothing).
**Control:** keeper `2026-09-22-nwpp-47-grid-wind` (`results/calibration/nwpp47_gridwind_span`).
**Probe:** `scripts/probes/_nwpp48_c4_phase0.py` reproduces every number below.

## 0. In one line

C4 fails because coal's **price-responsive MW are dispatched at the wrong times**, and there are too
few of them, while hydro carries the diurnal swing coal should share. Every coal-stack lever is
therefore predicted inert or negative until price timing changes. The lever that would change it,
`hydro_pondage_bound`, is not armable yet: it needs a data intake **and** a rule-19 design decision.
**Per the charter: STOP and report.**

## 1. A chartered premise is out of date

The charter says INLAND / NW / OR carry "~12 distinct P1 prices per year". **That is false for this
keeper.** It held before the NWPP-46 envelope. It no longer holds:

| year | zone | distinct prices / yr | days with intra-day variation | mean hour-of-day amplitude |
|---|---|---|---|---|
| 2023 | NW / INLAND / OR | 452 | 302 | $4.32 |
| 2024 | NW / INLAND / OR | 541 | 322 | $5.92 |
| 2025 | NW / INLAND / OR | 532 | 333 | $5.80 |
| 2023–25 | EAST | 468 / 543 / 557 | 328 / 346 / 351 | $5.24 / $3.13 / $4.96 |

So the price varies within the day, but by only $3–6. NW / INLAND / OR clear at one price (no
internal congestion).

## 2. (c) Both terms fail, and the daily term is the larger one

| year | r | r_daily | r_intra | share of **actual** variance: daily / intra-day | r if intra-day timing were perfect, at the model's amplitude / at the actual amplitude | r if the daily term were perfect |
|---|---|---|---|---|---|---|
| 2023 | 0.659 | 0.694 | 0.374 | 0.87 / 0.13 | 0.693 / 0.731 | 0.942 |
| 2024 | 0.617 | 0.678 | 0.396 | 0.78 / 0.22 | 0.653 / 0.759 | 0.897 |
| 2025 | 0.638 | 0.734 | 0.365 | 0.70 / 0.30 | 0.701 / 0.819 | 0.853 |

Getting the timing right at today's tiny amplitude **does not clear** 0.70. C4 needs amplitude, or
better day-to-day placement.

## 3. (d) Three PacifiCorp plants in NWPP-EAST carry the miss

For each plant, the **gain** is how much fleet r rises when that one plant's model output is replaced
by its own CAMPD shape at the model's own energy. Mean gain over the three years:

| plant | gain 2023 / 24 / 25 | intra-day sd, model / CAMPD (MW), 2024 |
|---|---|---|
| **Jim Bridger 8066** | **+0.091 / +0.166 / +0.177** | 53 / 298 |
| Huntington 8069 | +0.059 / +0.121 / +0.111 | 0 / 130 |
| Hunter 6165 | +0.093 / +0.091 / +0.100 | 29 / 137 |
| next (Centralia, Colstrip, Naughton, …) | ≤ +0.05 each | |

**Substituting Jim Bridger's coal units alone clears C4 in every year:** r → **0.750 / 0.705 /
0.767**. NWPP-EAST holds ~70 % of model coal. Its intra-day sd is 76–157 MW in the model against
534–784 MW measured.

**Jim Bridger carries two input defects, both measured:**

1. **2023 fleet vintage.** All four units burned coal in 2023 (CAMPD 9.11 TWh gross, 2.13–2.35 TWh per
   unit). Units 1–2 converted to gas in Jan-2024. The keeper reads the canonical 2025 EIA-860 for
   every year (`eia860_vintage_tracks_solve_year: false`), so in 2023 units 1–2 sit as 1,070 MW of
   `ST_GAS` and dispatch **0.002 TWh**. The committed `vintage_2023` registry lists them as `SUB`.
2. **No measured coal tranche row.** `derive_thermal_tranches.py` gives a plant's CEMS to its
   largest-nameplate bin, which here is ST_GAS. The COAL bin then falls through to
   `_DEFAULT_TRANCHE_PCT_BY_GROUP["COAL"]` = 45 / 5 / 2. That leaves 472 MW of fuel-free must-run
   running all 8,760 hours. This is the attribution defect nyiso-175b repaired (FINDING-nwpp-30 §7.3
   flagged the plant).

## 4. (b) Why fixing coal inputs alone is predicted not to work

**The model's price-responsive coal is dispatched at the wrong times.** Across the three years, the
econ/peak bands' hourly dispatch correlates with each plant's measured output as follows:

| plant | r (econ/peak bands vs measured output) |
|---|---|
| Jim Bridger | −0.12 / 0.17 / −0.05 |
| Huntington | 0.39 / 0.00 / 0.03 |
| Hunter | 0.32 / 0.09 / 0.09 |

Moving flat MW into those bands (withdrawing the default must-run, adding a measured row, or fixing
the stacking in §6) would scale up a mistimed signal. **Predicted: C4 unchanged or worse.** This
confirms NWPP-46's routing of the coal ladder to "after the price acquires the right timing".

**Where the swing goes instead** (intra-day sd in MW, measured / model; r_intra with EIA-930 net
load = net_gen − wind − solar):

| year | net-load sd | hydro sd | coal sd | gas sd | hydro r | coal r | NW LMP r | EAST LMP r |
|---|---|---|---|---|---|---|---|---|
| 2023 | 2,949 | 2,004 / 2,154 | 489 / 208 | 1,093 / 959 | 0.91 / 0.94 | 0.62 / 0.47 | 0.27 | 0.29 |
| 2024 | 3,239 | 1,918 / 2,216 | 615 / 117 | 1,291 / 1,149 | 0.88 / 0.93 | 0.77 / 0.46 | 0.03 | 0.68 |
| 2025 | 3,605 | 1,913 / 2,236 | 751 / 123 | 1,497 / 1,368 | 0.81 / 0.91 | 0.74 / 0.46 | 0.08 | 0.73 |

Hydro still swings 7–17 % more than measured (sd +150 to +320 MW) and follows net load more tightly
than the real fleet. Gas is 130–140 MW short. Coal's missing 280–630 MW of sd is of the same order.
The hydro-zone price carries almost no net-load timing in 2024–25 (NW r 0.03 / 0.08). EAST's price
does carry it (0.68 / 0.73), but with a $3–5 amplitude that sits below the coal econ-band offers
(the LMP when those bands are marginal is ~$31–57).

**Which row sets the price.** Hydro is partially loaded in 8,542–8,760 hours of every zone-year, so
hydro is marginal almost everywhere. The committed `hydro_cascade` sidecar carries the **coupling-row
dual, not the monthly-budget dual**. That dual is ≈0 except the known Chief Joseph pond dual (plant 3921, −$298.9
for 5,808 hours of 2025). The budget dual and the envelope dual are **not written to any sidecar**,
so the split between budget, envelope and cascade cannot be read at zero LP. That is an
observability gap. It is reported here, not worked around.

## 5. Candidate levers, with verdicts

| lever | NWPP cell | what it fixes | predicted C4 effect | status |
|---|---|---|---|---|
| `hydro_pondage_bound` | U | hydro over-flexibility, the root cause | the only candidate aimed at timing | **NOT ARMABLE:** needs `data/raw/nwpp-hydro/nwpp_hydro_pondage.csv` (NID/HILARRI intake), and the resolver raises when it and `hydro_cascade_coupling` (K) are both on. Rule 19 needs a design ruling: extend pondage to the non-cascade plants only, or fold it into the cascade row family. |
| `eia860_vintage_tracks_solve_year` | U (SPP K, PJM R) | 2023: JB 1–2 + North Valmy 1 → coal (1,441 MW). 2024: Valmy 1 (277 MW). 2025: none (canonical). | small: added coal lands mostly on the flat default block, and a constant does not move r | rule-14 accurate on its own merits. **C1 risk:** 2023 CC_REGULAR sits at −7.21 against ±8.00, so ~0.8 TWh of displacement flips C1. |
| `campd_per_unit_attribution` | U | a measured JB coal row | inert or negative (§4) | **collateral:** the per-unit outage companion (derived here, not committed) cuts CC_REGULAR outage windows from **1,882 to 460**. JB's routing is identical under both. An unexplained, unrelated change to CC_REGULAR availability. |
| `coal_mustrun_requires_measured_row` | U | removes JB's default 45 % must-run | inert or negative (§4); likely coal volume loss | not recommended |
| measured coal ladder (0.821 / 0.932 / 1.004 / 1.029) | routed (NWPP-46) | econ-band spacing | inert until the timing is right | stays routed |

## 6. Reported, not acted on

* **The mustrun and committed bands add up, but both are measured from zero.**
  `assembly.py` sizes `_mustrun` at `pct_mr × nameplate` and `_committed` at `pct_mc × nameplate`,
  stacked. `derive_thermal_tranches.py` defines both as levels from 0 MW: committed = P5 of online
  CF, mustrun = P5 of all-hours CF. At an always-on plant they are nearly equal (Hunter 22.3 / 22.3,
  Dave Johnston 48.3 / 47.9), so the flat block is **~2× the measured minimum stable load** (Hunter
  608 MW against a CAMPD p10 of 234). This is cross-ISO infrastructure, and ERCOT's bins may rely on
  it. It needs its own owner-scoped audit, not an NWPP lane.
* Tiny coal plants with model output and zero CAMPD (54318, 57915, 10784, 62319; ≤0.24 TWh each) are
  on the same 45 / 5 / 2 default.
* Inherited, untouched: the C1 demand-basis gap (FINDING-nwpp-45 §8, framing 2, an open owner
  decision); C5a CO2; the NWPP-40/41/42 attestation corrections still owed; the EIA-930 2025 hydro
  −44,969 MW hour.

## 7. What the owner needs to decide (no LP spent; none requested yet)

1. **Pondage vs cascade (rule 19).** Charter a design lane to make `hydro_pondage_bound` coexist with
   `hydro_cascade_coupling`, plus the NID/HILARRI pondage intake? This is the only lever aimed at the
   root cause. Cost: one design + intake session at zero LP, then 3 year-isolated shards
   (~60–100 min each, in parallel).
2. **Jim Bridger 2023 vintage.** Arm `eia860_vintage_tracks_solve_year` for NWPP as a rule-14
   accuracy fix, **not** as a C4 lever, accepting the stated C1 CC_REGULAR risk? Cost: 3 shards (2025
   is predicted byte-identical, but rule 36 still solves it).
3. **Stacking audit (§6).** Route it to a cross-ISO audit lane?

## 8. Retrievability and cleanup

* No bundle was produced. Nothing is on ephemeral disk that a promotion would need.
* The per-plant legs were read from the NWPP-47 shard commits `28c30ecf` / `9b490454` / `6e375b43`
  (provenance only, rule 33(d)). Those branches still await owner deletion.
* The per-unit outage companion was derived into scratch space and **not committed**. It can be
  regenerated with
  `derive_campd_unit_outages.py --iso NWPP --years 2023 2024 2025 --per-unit-crosswalk` (~13 s).
