# spp-wind-shape — raw

`spp_<year>_wind_zone_shape.parquet` (2023–2025) — per-zone hourly wind SHAPE
for SPP's two model zones, built from reanalysis wind speed + fleet siting.

Opened **2026-09-07** by lane **SPP-32**
(`docs/multi-iso/spp-addition-plan-2026-09.md` §5 row SPP-32).

**Source and full method: see `SOURCES.md` in this directory** — NASA POWER
hourly WS50M (50 m wind speed, MERRA-2 reanalysis,
`https://power.larc.nasa.gov/api/temporal/hourly/point`, keyless), combined with
EIA-860 wind-plant siting, placed on the model clock via the EIA-930 `SWPP`
hourly extract, and cross-checked against SPP's own metered generation mix.
NASA POWER data is public domain (NASA open-data policy).

**Regeneration:**
`python scripts/data/build_spp_wind_shape.py --years 2023 2024 2025 --reconcile`.
2019–2022 are buildable by the same command and were **not** built here: nothing
in rule 22 `[R-HOLDOUT]` restricts the *data*, but this lane had no need for
them and an unbuilt year is a smaller claim than an unused one. **2026 is not
buildable**: the shape is placed on the model's full-8760 UTC clock via
`eia_loader._eia_hourly_frame_filled`, which returns `None` for a half year
(H1-2026 is 4,344 h) — rebuild once the 2026 EIA-930 extract completes. This is
the same limitation the MISO and ERCOT shapes carry.

## Why SPP needs one

SPP's 35.5 GW wind fleet splits almost exactly in half across the North/South
seam (EIA-860 operable: **17.7 GW / 135 plants** in SPP-North, **17.8 GW / 119
plants** in SPP-South; the 35.5 GW total reconciles with SPP's own published
35,934 MW of registered wind nameplate at end-2025, `data/raw/spp-hsl/`), and the
two halves do not peak at the same hour. One SWPP-wide hourly profile applied to
both averages them together.

**The measured contrast — and it runs OPPOSITE to the MISO intuition.** The
builder's own night(00-06)/afternoon(12-18) ratios:

| Zone | 2023 | 2024 | 2025 | Reads as |
|---|---|---|---|---|
| SPP-South | 1.04 | 1.06 | 1.03 | overnight-weighted |
| SPP-North | 0.97 | 0.96 | 0.91 | afternoon-weighted |

The **South** is the nocturnal zone. That is what the meteorology says once you
look instead of assuming: the Great-Plains nocturnal low-level jet's
climatological core sits over Oklahoma / Kansas / the Texas Panhandle — i.e. over
SPP-**South** — and weakens northward into Nebraska and the Dakotas. In MISO the
north/south contrast points the other way because MISO-North *is* the upper
Plains while MISO-South is the Gulf. **Do not carry the MISO intuition across.**

## The level is never pinned

Only the *relative inter-zone shape* is used. `market_sim.data.renewables`
reconciles these shapes to the measured SWPP-wide series so the
capacity-weighted system total and annual energy are preserved exactly
(`_redistribute_preserving_total`). The mean CF the builder prints is a
diagnostic; nothing downstream reads it, and no constant in the builder is
fitted to it (rule 13 `[R-MEASURED]`).

## Reconciliation against SPP's own metered wind (diagnostic, not a fit)

`--reconcile` scores the built shape against SPP's public Integrated Marketplace
generation mix (`data/raw/spp-genmix/GenMix_<year>.csv`, delivered wind =
`Wind Market` + `Wind Self`, 5-minute, UTC), after normalising **both** series to
unit mean so the score is invariant to level by construction:

| Year | hours | hourly r | diurnal (24h) r | seasonal (12m) r |
|---|---|---|---|---|
| 2023 | 8,760 | 0.8479 | 0.6671 | 0.9837 |
| 2024 | 8,760 | 0.8356 | 0.6862 | 0.9309 |
| 2025 | 8,760 | 0.8332 | 0.6805 | 0.9065 |

**Read the diurnal column with its caveat, which is a real effect and not a
miss.** GenMix is *delivered* wind — net of the ~10 %/yr SPP curtails
(`data/raw/spp-hsl/spp_wind_curtailment_annual.csv`) — while the built shape is
an *uncurtailed potential*. SPP's curtailment is concentrated in the overnight
low-load hours, which is exactly where the two series are expected to part
company, and it flattens the measured diurnal profile relative to the potential.
The seasonal and hourly agreement, which curtailment distorts far less, is the
stronger evidence that the shape is right.

Nothing in this reconciliation feeds back into the parquet: `--reconcile` prints
and returns, and the written values are byte-identical with and without it.

**Consumer:** `src/market_sim/data/renewables.py` (`_wind_zone_reanalysis_shapes`,
via `market_sim.config.paths.WIND_SHAPE_DIRS["SPP"]`).

---

## NOTE 2026-09-07 — lane SPP-57: a three-zone rebuild was made and NOT landed

The SPP-57 rule-29(a) screen (`docs/handoffs/FINDING-spp-57-2026-09-07.md` §5) killed the
three-zone arm, so the parquets here stay the SPP-32 two-zone build. The three-zone rebuild
(`SPP-North` / `SPP-Oklahoma` / `SPP-South`; night/afternoon ratios 0.97 / 1.06 / 1.01 (2023),
0.96 / 0.96 / 1.13 (2024), 0.91 / 0.95 / 1.12 (2025); GenMix reconciliation hourly r 0.842 /
0.829 / 0.829) is recorded in that FINDING §4 and lives in the branch history
(`claude/spp-57-oklahoma-pocket-yedapf`, the design commit) for a re-issue to reuse — the same
builder regenerates it in minutes.
