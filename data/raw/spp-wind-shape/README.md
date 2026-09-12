# spp-wind-shape — raw

`spp_<year>_wind_zone_shape.parquet` (**2019–2025**) — per-zone hourly wind SHAPE
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

**2019–2022 LANDED 2026-09-12 by lane SPP-30**, by exactly that command
(`--years 2019 2020 2021 2022`), to accompany the SPP out-of-training price-actual
intake — the years need a wind shape to be dispatchable at all. SPP-32's note that
they were "not built here … an unbuilt year is a smaller claim than an unused one"
is retained as its own reasoning; the need has now arisen. (Its parenthetical that
"nothing in rule 22 `[R-HOLDOUT]` restricts the *data*" is doubly true now: rule
22's `[R-HOLDOUT]` regime and every gate enforcing it were removed 2026-09-09 by
owner instruction, commit `b0a807a8`.) **2026 is not
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

| Zone | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | Reads as |
|---|---|---|---|---|---|---|---|---|
| SPP-South | 0.99 | 1.05 | 0.98 | 1.03 | 1.04 | 1.02 | 1.00 | overnight-weighted |
| SPP-North | 0.99 | 0.99 | 0.98 | 0.98 | 0.99 | 0.96 | 0.94 | afternoon-weighted |

(All seven columns re-measured by SPP-30 from the committed parquets on one
definition — `mean(hours 0–5) / mean(hours 12–17)` over the full 365×24 reshape.
The 2023–2025 cells therefore move against SPP-32's originally-published
1.04/1.06/1.03 and 0.97/0.96/0.91: **largest deviation 0.045** at SPP-South 2024
(1.06 → 1.015), then 0.033 at South 2025 and 0.031 at North 2025, with the other
three inside 0.02. The **qualitative reading is unchanged** — South overnight-weighted,
North afternoon-weighted, in every year — and the cause is the statistic, not the
data: these are recomputed over the reshape rather than read off the builder's
per-run log line. Flagged rather than reconciled, because nothing downstream reads
this ratio; it is a README diagnostic.)

Annual-mean CF, all seven years, as a cross-year coherence check — the new years sit
inside the committed years' band rather than beside it:

| Zone | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| SPP-North | 0.3395 | 0.3569 | 0.3435 | 0.3812 | 0.3102 | 0.3389 | 0.3307 |
| SPP-South | 0.3354 | 0.3384 | 0.3357 | 0.3505 | 0.3062 | 0.3307 | 0.3082 |

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

## NOTE 2026-09-07 — lane SPP-54: a three-zone (SPS-pocket) rebuild was made and NOT landed here

`docs/handoffs/PRECOMMIT-spp-54-2026-09-07.md` §4 / `FINDING-spp-54-2026-09-07.md` §4. The SPS /
Texas-Panhandle pocket (`SPP-North` / `SPP-South` / `SPP-SPS`) was designed and its parquets rebuilt by this
builder (54 point-years; night/afternoon **N 0.97 / S 1.06 / SPS 1.01** (2023), **0.96 / 0.96 / 1.13**
(2024), **0.91 / 0.95 / 1.12** (2025) — the SPS pocket is the most nocturnal zone; GenMix hourly r 0.842 /
0.829 / 0.829). They live on that branch's design commit **`8d427adc`** (with the three-zone `_spp_config`),
not here, because no solve of that topology has run: the link rating waits for SPP-58's ψ₂ and the lane's
pre-solve wind reconciliation STOPPED. **Do not copy the three-zone parquets in alone**: the two-zone loader
accepts any parquet whose columns include its zone names, so a three-zone file here would silently apply
Oklahoma's six-site shape to the whole two-zone South under keeper-3.

**What SPP-54 measured about this builder (its R-21, routed to SPP-DESK):** the redistribution weights each
zone by `cap_z · SHAPE_z(t)`, so the six-site samples' relative MEAN LEVELS act as zonal capacity-factor
levels, not only their diurnal shape ("the level is never pinned" above is true of the system total and of
the shape, not of the inter-zone level split). Splitting the old South's six-site set into Oklahoma's six
and the Panhandle's six moved the North's annual wind potential **+1.38 / +1.47 / +1.91 TWh** at an identical
system total (identity 6e-16), **75–85 % of it from the residual South's own sample changing**, not from
the SPS shape. A zone's level from its whole operable fleet (capacity-weighted over all plants) is the
candidate zero-DOF repair; nothing here was changed after that number was seen.
