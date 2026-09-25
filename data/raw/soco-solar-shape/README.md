# soco-solar-shape — raw

`soco_<year>_solar_zone_shape.parquet` (**2023–2025**) — per-zone hourly solar
SHAPE for SOCO's three model zones, built from **measured all-sky irradiance at
every operable solar plant** plus that plant's own EIA-860 array geometry.

Opened **2026-09-16** by lane **SOCO-32**
(`docs/multi-iso/soco-addition-plan-2026-09.md` §5 row SOCO-32; FINDING
`docs/handoffs/FINDING-soco-32-2026-09-16.md`).

**Source and full method: see `SOURCES.md` in this directory** — NASA POWER
hourly `ALLSKY_SFC_SW_DNI` / `ALLSKY_SFC_SW_DIFF`
(`https://power.larc.nasa.gov/api/temporal/hourly/point`, keyless), transposed
onto each generator's plane of array and capacity-weighted into the three model
zones, placed on the model clock via the EIA-930 `SOCO` hourly extract. NASA
POWER data is public domain (NASA open-data policy).

**Regeneration:**
`python scripts/data/build_soco_solar_shape.py --years 2023 2024 2025 --reconcile`

Schema: `hour` (0..8759, the model's fixed non-leap clock) + one float column
per model zone (`SOCO_AL`, `SOCO_GA`, `SOCO_MS`), 8,760 rows, hour-sorted — the
same table `renewables._wind_zone_reanalysis_shapes` reads for wind, so the
reader needs no new parsing code. Units are Wh/m² of plane-of-array irradiance,
which is a *relative* series: `renewables._redistribute_preserving_total`
divides by the capacity-weighted mean and preserves the measured EIA-930
ISO-wide solar total exactly in every hour. **No level is pinned to an actual**
(rule 13 `[R-MEASURED]`); this file can only move WHICH ZONE holds the solar.

**2026 is not buildable** — the shape is placed on the model's full-8760 UTC
clock via `eia_loader._eia_hourly_frame_filled`, which returns `None` for a part
year. Same limitation the MISO / SPP / ERCOT wind shapes carry.

## Why SOCO needs one — and why the existing clear-sky path cannot serve it

The repo's per-zone SOLAR path (`renewables._solar_zone_clearsky_shapes`, armed
for CAISO) builds a clear-sky plane-of-array series from each zone's **latitude**
and tracking mix, and its own docstring records that longitude and the equation
of time are *deliberately omitted* because "a constant timing offset shared by
all zones cancels". For CAISO's north–south stack that holds. For SOCO it does
not: the zones are separated **east–west**.

Capacity-weighted centroids of the EIA-860 solar fleet (2025 vintage):

| Zone | centroid lon | centroid lat | single-axis | fixed | dual-axis |
|---|---:|---:|---:|---:|---:|
| SOCO_GA | −83.63 | 31.96 | 81.3 % | 14.3 % | 4.4 % |
| SOCO_AL | −86.35 | 31.28 | 69.7 % | 30.3 % | — |
| SOCO_MS | −89.16 | 31.45 | 84.2 % | 15.8 % | — |

**5.53° of longitude = 22.1 minutes of solar time** between Georgia and
Mississippi, against a 0.68° latitude spread. One latitude-keyed shape puts all
three zones' solar peak in the same model hour, which is the one thing the
geography says is wrong.

## The measured contrast

Built by this directory's own builder, on SOCO's single Central clock:

| Statistic | Zone | 2023 | 2024 | 2025 | Reads as |
|---|---|---:|---:|---:|---|
| energy-weighted mean hour-of-day | SOCO_GA | 11.026 | 11.033 | 11.024 | earliest — furthest **east** |
| | SOCO_AL | 11.246 | 11.283 | 11.268 | |
| | SOCO_MS | 11.392 | 11.382 | 11.368 | latest — furthest **west** |
| morning(07–10)/afternoon(13–16) | SOCO_GA | 1.256 | 1.233 | 1.233 | morning-weighted |
| | SOCO_AL | 1.136 | 1.100 | 1.105 | |
| | SOCO_MS | 1.071 | 1.072 | 1.079 | flattest |
| peak(11–13)/shoulder(08–10,14–16) | SOCO_AL | 1.333 | 1.331 | 1.312 | **peakiest** — 2× the fixed-tilt share |
| | SOCO_GA | 1.296 | 1.271 | 1.264 | |
| | SOCO_MS | 1.319 | 1.265 | 1.271 | |

The GA↔MS mean-hour gap is **0.366 / 0.349 / 0.344 h**, against the 0.369 h a
5.53° longitude span predicts from solar geometry alone — the builder reproduces
the pure-geometry prediction to ~0.02 h without being told it.

Size of the effect: normalised zone shapes correlate **GA↔MS r = 0.90 / 0.90 /
0.91**, and **3,508 / 3,488 / 3,402 hours a year** (≈ 40 %) carry a >10 %
relative gap between the two. This is not a marginal refinement.

## Reconciliation against EIA-930 (a CHECK, never an input)

`--reconcile` correlates the capacity-weighted footprint shape against the
measured `SOCO` `NG: SUN` series over −3…+3 h and prints the result. It changes
no value in the parquet.

| Year | best shift | r at best | r at ±1 h | mean hour-of-day built vs measured |
|---|---:|---:|---:|---|
| 2023 | **+0 h** | 0.9878 | 0.9364 / 0.9313 | 11.07 vs 11.05 |
| 2024 | **+0 h** | 0.9753 | 0.9237 / 0.9182 | 11.08 vs 11.06 |
| 2025 | **+0 h** | 0.9331 | 0.8824 / 0.8763 | 11.07 vs 11.07 |

A sharp single peak at zero in every year: NASA POWER's hour-**beginning** UTC
stamp maps onto the model's hour-**ending** clock with the +1 h offset the
builder applies, and nothing further. The 2025 correlation is the weakest of the
three and is **reported, not repaired** — 2025 is also the year whose EIA-930
extract is 7 hours short and whose `NG: SUN` cell carries the largest reporting
noise (`docs/multi-iso/soco-data-audit.md` §3.2–§3.3).

## What is deliberately NOT modelled

* **Inverter clipping.** Capacity-weighted DC:AC is 1.367 (AL) / 1.382 (GA) /
  1.401 (MS) — a 2.5 % spread — so clipping flattens all three midday peaks by
  very nearly the same amount, and the downstream reconciliation preserves the
  ISO aggregate exactly regardless.
* **Cell-temperature derate and the ground-reflected POA term.** Each needs a
  coefficient (a temperature coefficient, an albedo) this lane would have to
  invent, and both are common-mode across three zones of one climate at ~20° of
  tilt (rules 21 `[R-DOF]` / 24 `[R-REGISTRY]`).

## Wind

There is no `soco-wind-shape`. SOCO's EIA-860 operable fleet carries **zero
wind generators / 0.0 MW**, and the EIA-930 `SOCO` extract reports `NG: WND` as
**exactly 0.0 in every one of the 26,257 hours it publishes** for 2023–2025 (the
column exists; it is not null, it is zero). There is no series to shape and
nothing to split, so a wind builder here would divide by zero.

## 2019-2022 (I-SOCO, 2026-09-24)

`soco_{2019,2020,2021,2022}_solar_zone_shape.parquet` built by the same command
(`--years 2019 2020 2021 2022 --reconcile`); every year places at a zero-hour
best shift against EIA-930 `NG: SUN` (r 0.967 / 0.984 / 0.977 / 0.986). The
same run rebuilt 2023-2025 and those frames equal the committed files exactly
(only parquet writer-metadata bytes differ), so the committed 2023-2025 files
were kept. Record: `docs/handoffs/FINDING-i-soco-2019-2022-intake-2026-09-24.md`.
