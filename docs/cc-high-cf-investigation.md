# Why combined-cycle plants miss their >90% CF hours

**Status:** investigation / diagnosis (runs 115b, 118). The structural cause is
identified and reproduced from the committed bundles; the offer-curve retune
that would close the gap is *proposed*, not yet applied.

## The observation

In runs **115b** and **118**, efficient grid-serving combined cycles
(`CC_REGULAR`) spend far too few hours above 90 % capacity factor. The real
plants (EPA CAMPD net generation) run thousands of hours per year at 90–97 %
CF; the model parks them just below that and almost never enters the top bins.

Hours each plant spends at **≥90 % CF** (normalized to the larger of the model
and CAMPD per-plant peaks), run 118:

| Plant (EIA) | 2023 model / CAMPD | 2024 model / CAMPD | 2025 model / CAMPD | model peak as % of real peak |
|---|---|---|---|---|
| Freestone (55226)        | **0** / 1 630 | **0** / 1 338 | **0** / 3 065 | 87–90 % every year |
| Guadalupe (55153)        | 88 / 1 482 | 22 / 1 082 | 22 / 668 | 91–92 % |
| Wolf Hollow II (59812)   | 1 522 / 2 801 | **206** / 2 608 | **153** / 976 | 95–102 % |
| Colorado Bend II (60122) | 1 438 / 3 845 | 2 995 / 3 278 | 2 797 / 975 | 99–100 % |
| Colorado Bend EC (56350) | 2 049 / 449 | 444 / 61 | 632 / 86 | ~100 % (over-runs) |

Two distinct failure modes show up:

* **Hard ceiling (Freestone, Guadalupe).** The model's *maximum* hourly output
  is itself only 87–92 % of the real plant's observed peak. The top ~10 % of
  the unit's capability is never dispatched in *any* hour, so it is
  arithmetically impossible to log a 90–100 % CF hour. Freestone never exceeds
  ~978 MW against a real peak of 1 119 MW.
* **Right ceiling, wrong distribution (Wolf Hollow II, Colorado Bend II).** The
  unit *can* reach the top occasionally, but its dispatch mass piles up in the
  80–90 % band instead of spreading into 90–97 % the way CAMPD does.

At 5 % CF resolution the cliff is unmistakable — Colorado Bend II, 2023:

```
                     80-85% 85-90% 90-95% 95-100%
Colorado Bend II  M   3033   2436   1433     5
                  C   2061    692   2686  1159
```

The model puts **5** hours in 95–100 % CF; the real plant put **1 159**.

## Root cause

The `CC_REGULAR` offer curve (run 118: `committed 0.87 · econ_low 0.92 ·
econ_high 1.21 · peak 2.57 · pct_peaking 8 %`) builds each plant as:

```
committed block   base_hr × 0.87        (per-plant CAMPD min-stable share)
econ ramp         base_hr × 0.92 → 1.21  (6 rising slices, the dispatch body)
── discontinuity ──
peak tranche      base_hr × 2.57         (top 8 % of nameplate, FLAT)
```

`fleet.bins_to_fleet` renders the economic region as the rising
`_econ_curve_steps` ramp spanning **econ_low → econ_high only**, and keeps the
duct-firing **peak band as a separate flat tranche above the ramp** (see
`fleet.py` — "Every group spans econ-low to econ-high and keeps the
duct-firing / scarcity peak as a separate flat tranche above the ramp").
There is no longer any fold of the peak into the CC ramp (`_CURVE_FOLD_PEAK`
was removed; `fleet.py:3554` "Nothing is folded into the ramp"). So at the top
of a CC's range there is a **price discontinuity**: marginal cost jumps from
`econ_high × base_hr` (1.21×) straight to `peak × base_hr` (2.57×).

That 2.57× block is a duct-firing / scarcity price. For a plant whose
base_hr ≈ 7 and gas ≈ $3/MMBtu it offers near **$54/MWh** versus ~$25/MWh at
the top of the econ ramp — so the top 8 % of capacity only clears in genuine
scarcity hours. Combine that with the availability derate on `pmax`
(`pmax = nameplate × availability[g,t]`, ~5 % for a CC), and the unit's
**effective steady ceiling is ≈ (1 − 8 %) × (1 − ~5 %) ≈ 87–92 % of
nameplate**. That is precisely the ceiling measured above.

Whether a given plant ever pokes above the wall depends on its own `base_hr`
and zonal LMP exposure: Colorado Bend II's peak block clears in enough hours to
reach ~100 %, Freestone's never does. The heterogeneity is a symptom of the
same lever, not a different bug.

**Why this is wrong physically.** For a modern 2×1 F-class CC, the incremental
heat rate *near full load is flat or improving* up to the base rating; true
duct firing is a smaller slice (~5 % of nameplate) and even then ~1.3–1.5×
incremental, not 2.0–2.6×. Pricing the top 8 % of nameplate at 2.57× base_hr
treats ordinary baseload output as if it were duct firing, so the model cannot
reproduce the sustained 90–97 % CF these units actually ran in 2023 when gas
was cheap. This is the failure the binning methodology already warns about
under "Why a plant over/under-runs": the ramp anchored on annual-average
base_hr prices the upper output too high.

## The "random spikes" the precision CF chart shows

Because the econ region is a finite set of flat sub-tranches (6 slices) plus a
committed block and a flat peak block, the LP parks an already-committed unit
at the **discrete edges** of those tranches. A per-CF-value ("precision") line
of hours-at-each-CF is therefore a comb of spikes at the committed floor, each
econ-slice boundary, and the top-of-econ — which never lines up with the smooth
physical CAMPD density. The spikes are an artifact of the tranche discretization,
not a signal. **Binning the same hours into fixed 5 % intervals collapses the
comb into a comparable shape** and is the right default for eyeballing
operating-level fit. (It does not fix the >90 % gap — that is the peak-band
wall above — it only makes the gap legible.)

## Tooling added with this investigation

* `--cf-band-width` on `scripts/run_calibration_full.py` — sets the CF-band
  resolution of the `[7b]` panel and `plant_cf_bands.parquet`. Default stays
  0.10; pass **0.05** for twenty 5 % bands. The `cf_emd` metric reads the width
  back from the parquet, so it stays comparable across band widths.
* `scripts/plot_cf_histogram.py` — standalone, dependency-free (inline-SVG)
  per-plant model-vs-CAMPD CF histogram at a configurable band width, the
  visual companion to the `[7b]` table. Example:

  ```
  uv run python scripts/plot_cf_histogram.py \
      results/calibration/run118_reldeploy_spatial \
      --plants 60122,59812,55226,55153,56350 \
      --years 2023,2024,2025 --band-width 0.05 --out /tmp/cc_cf_hist.html
  ```

## Proposed fix (not yet applied — needs a calibration sweep)

The lever is the CC duct-firing peak band, not the histogram. Candidate moves,
in order of preference (keep accurate inputs per the project rules; do not bury
the error in an inaccurate one):

1. **Shrink and cheapen the peak band.** Drop `pct_peaking` for grid-serving
   F-class CCs toward the real duct-firing share (~4–5 %) and lower the peak
   multiplier from ~2.5 toward ~1.4–1.6, so the top of nameplate clears at
   normal prices and the econ→peak discontinuity nearly disappears.
2. **Raise `econ_high`'s reach / extend the ramp** so the rising curve covers
   more of the upper output before the flat peak begins.
3. Re-check `cc_peaking_per_plant` — it currently moves the peak band *earlier*
   on the CF axis for four late-F-class plants (Wolf Hollow II, Colorado Bend
   II, Temple, Rayburn), which is the wrong direction for the >90 % problem and
   should be re-derived against the per-plant CAMPD upper-CF mass.

Any change must be swept across the full ERCOT panel: Colorado Bend EC already
*over*-runs the top bins, so a blanket loosening would push it further off.
Validate with the 5 %-band `[7b]` / `plant_cf_bands` and the `cf_emd` metric
before adopting.
