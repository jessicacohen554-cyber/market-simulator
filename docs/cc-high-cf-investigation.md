# Why combined-cycle plants miss their >90% CF hours

**Status:** investigation / diagnosis (runs 115b, 118). The structural cause is
identified and reproduced from the committed bundles; the offer-curve retune
that would close the gap is *proposed*, not yet applied.

> **See also — the PJM mirror image (2026-06-24):**
> [§ PJM and the net-summer ISOs](#pjm-and-the-net-summer-isos-the-mirror-image-bug-2026-06-24).
> ERCOT (this doc) *under*-runs its top CF bands behind a duct wall at ~92% of
> nameplate. PJM/NYISO/NEISO had the *opposite-looking* symptom — a wall at
> **~75%** — from a different root cause (a triple-counted summer derate on a
> net-summer-capped fleet). Fixing the structure there flips the symptom to ERCOT's
> over-running side and exposes a CC offer level that is too cheap. The two are
> the same underlying lesson: the CF distribution is set by capacity definition +
> reserve/commitment structure + offer level, never by a fitted wall.

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
* `scripts/archive/plot_cf_histogram.py` — standalone, dependency-free (inline-SVG)
  per-plant model-vs-CAMPD CF histogram at a configurable band width, the
  visual companion to the `[7b]` table. Example:

  ```
  uv run python scripts/archive/plot_cf_histogram.py \
      results/calibration/run118_reldeploy_spatial \
      --plants 60122,59812,55226,55153,56350 \
      --years 2023,2024,2025 --band-width 0.05 --out /tmp/cc_cf_hist.html
  ```

## Experimental sweep — the peak band IS the lever, but a blanket cut isn't a keeper

Replaying the run115b keeper with the CC_REGULAR peak multiplier lowered from
2.57× toward a physical duct-firing increment (`scripts/archive/cc_peak_band_probe.py`,
which reproduces every other knob from the bundle's `run_config.json`) confirms
the diagnosis and bounds the lever. Hours ≥90% CF, base (peak 2.57×) →
**peak 2.0×** → CAMPD, all three years:

| plant | 2023 base/2.0/CAMPD | 2024 base/2.0/CAMPD | 2025 base/2.0/CAMPD |
|---|---|---|---|
| CB II (60122)   | 2003 / 2769 / 3845 | 3841 / 4345 / 3278 | 3678 / 3978 / **975** |
| WH II (59812)   | 344 / 1069 / 2314  | 196 / 936 / 2608   | 154 / 587 / 976 |
| Freestone (55226)| **0 / 0** / 1630  | **0 / 0** / 1338   | **0 / 0** / 3065 |
| Guadalupe (55153)| 2 / 31 / 1482     | 8 / 40 / 1082      | 2 / 16 / 668 |
| CB EC (56350)   | 2463 / 2473 / 449  | 570 / 649 / **61** | 363 / 405 / **20** |
| CC_REGULAR class Δ | **+1.50 TWh** | **+2.50 TWh** | **+1.75 TWh** |

(At peak **1.5×**, 2023 CB II/WH II reach 4331/2695 — closer still — but the
class total moves +3.37 TWh and CB EC blows out to 1332 hrs ≥90% vs CAMPD 449.)

What the sweep establishes:

1. **The peak band is the correct lever** for the price-limited plants: lowering
   it moves CB II, WH II and Guadalupe toward their observed >90% mass in the
   cheap-gas direction.
2. **A year-uniform blanket cut cannot close the gap.** Peak 2.0× lands the
   class total at the 0.33% gate in 2023 (+1.50 TWh) but **breaches it in
   2024/2025** (+2.50 / +1.75), and it pushes the plants that *already
   over-run* further off — CB II in 2025 is already 3678 hrs ≥90% against
   CAMPD's 975 (the documented "runs baseload when it should cycle"), and a
   cheaper peak makes that worse. WH II and CB II thus want **opposite**
   year treatment, the within-class misallocation the calibration log parks on
   the spatial axis.
3. **Freestone is capacity-limited, not price-limited.** It logs 0 hours ≥90%
   in every variant because its model nameplate (1036 MW, with only
   committed/econ tranches — no peak band dispatched) is **below its real CAMPD
   peak (1119 MW)**; the peak multiplier never touches it. Conversely CB EC's
   model nameplate (654 MW) is **above** its real peak (560 MW), so it
   over-runs the top regardless. These are per-plant capacity-data errors, a
   separate axis from the offer curve.

**Conclusion: no blanket peak retune is promotable as a keeper.** The honest
read is three coupled fixes, none a single knob:

- a **moderate** peak reduction (≈2.0×) is safe only in 2023 on the class gate;
  to use it in 2024/2025 it must be paired with the offsetting levers below;
- **per-plant** peak treatment (`cc_peaking_per_plant`) so CB EC (and CB II in
  high-gas years) keep a higher wall while WH II / Guadalupe get a lower one;
- **per-plant capacity reconciliation** against the CAMPD observed peak —
  Freestone up (~1036 → ~1120 MW, the cold-weather CC over-rating), CB EC down
  (~654 → ~560) — preferring the measured peak over the static nameplate, per
  the project's "accurate data over estimates" rule.

The residual after all three is the spatial/within-class misallocation already
documented in `docs/calibration-log.md` (parked on the missing NP6-785-ER zonal
prices), so closing the CC >90% gap fully is gated on that data, not on a new
offer lever. The probe tool and the 5%-band view ship here so the next
calibration session can drive the per-plant work with the operating-level
distribution in view.

## Capacity reconciliation — implemented, the data axis for the understated plants

The sweep above showed Freestone never reaches 90% at any peak price because
its model nameplate (1036 MW) is below its real CAMPD peak (1119 MW): an F-class
CC's **cold-weather over-rating** that the standard nameplate omits. EIA-860
winter capacity corroborates it (Freestone 1095, Hays 1048, Lamar 1149, Forney
1966 MW — all above their bin nameplate). `scripts/data/derive_cc_capacity_reconcile.py`
writes a **raise-only** reconciliation —
`cap = max(nameplate, demonstrated CAMPD p99.9 peak)` — committed as
`data/raw/_processed-legacy/cc_capacity_reconcile_ERCOT.csv` and applied in
`load_campd_bins` under `ScenarioConfig.cc_capacity_reconcile` (default off,
ERCOT backcast). It raises 8 CC_REGULAR plants by 1.5–11% (+377 MW total) and
never lowers one — CB EC (bin 654 = EIA-860 nameplate 654; over-runs on the
offer side, not capacity) is correctly untouched.

Result for 2023, capacity reconcile **only** (peak band unchanged at 2.57×),
hours ≥90% CF base → reconciled → CAMPD:

| plant | base | reconciled | CAMPD | model max MW |
|---|---|---|---|---|
| Freestone (55226) | **0** | **3956** | 1630 | 978 → 1050 |
| Lamar (55097)     | 0 | **2143** | 2082 | 982 → 1029 |
| Hays (55144)      | 0 | 1578 | 467 | 933 → 993 |
| Odessa (55215)    | 0 | 0 | 2786 | 1005 → 1020 |
| CC_REGULAR class Δ | | **+1.56 TWh** | | |

The reconciliation **unblocks the hard zero** (Freestone 0 → 3956; Lamar lands
almost exactly on CAMPD's 2082) and is the correct measured fix — those plants
demonstrably produced that output. But Freestone and Hays now *overshoot*, and
the class total moves +1.56 TWh (at the 0.33% gate). This is precisely the
`claude.md` rule-11 signal: **the understated capacity was silently compensating
for the offer curve's tendency to over-baseload efficient CCs.** Capping the
plant low hid the over-baseloading; restoring the real capacity surfaces it. So
capacity and the offer ramp are complementary — capacity gives the headroom to
reach the top, the econ-ramp shape (the merit-ramp axis) controls how much the
unit cycles vs sits there. A keeper pairs the two: reconcile capacity **and**
steepen/per-plant the offer ramp so the in-gate class total and the cycling
shape both hold. Odessa/Barney Davis need a larger reconciliation (their CAMPD
peak still exceeds the +1.5% applied) and are left for the combined pass.

## Earlier framing (superseded by the sweep above)

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

---

## PJM and the net-summer ISOs: the mirror-image bug (2026-06-24)

PJM, NYISO and NEISO showed the *opposite-looking* symptom of the ERCOT bug
above — the combined-cycle fleet parked at a **~75 % of nameplate** wall (the
70–75 % CF band ~3× over-stuffed, 75–85 % starved) — but the root cause was
**not** the offer curve. It was a **triple-counted summer derate** on a fleet
whose LP capacity was pinned at the net-summer rating. Diagnosed and structurally
fixed this session; the fix is correct and **exposes a separate, larger CC
offer-level miss** that is the real open item (see the handoff
`docs/handoffs/pjm-cc-level-tuning-2026-06.md`).

### Root cause: three stacked summer derates on a net-summer-capped fleet

The non-ERCOT ISOs run the per-plant EIA-860 fleet (`plant_level_fleet`), where
`_rows_to_generators` sets each unit's `pmax_mw` to its **net-summer** capacity
(`fleet.py` ~2855). On top of that already-summer-derated capacity the model then
applied, for combined cycles:

1. **`_SUMMER_CLASS_DERATE` (a flat 10 %)** again in the summer months
   (`fleet.py` ~1097) — a second summer derate on a number that was *already*
   the summer rating;
2. **`cc_duct_peaking`** sized the duct-firing peak band from the EIA-860
   `(nameplate − net_summer)/nameplate` gap (`fleet.cc_duct_peaking_pct`) — i.e.
   it re-priced *the very same summer-derate gap* as an expensive year-round duct
   wall. For Guernsey (62949) that gap is 13 %, so the steep band started at
   ~87 % of net-summer ≈ **75.7 % of nameplate** — in every hour, winter
   included;
3. the statistical **WEFOR** forced-outage rate, on top of the historic CAMPD
   outage overlay that already carries every sustained outage.

Net effect (PJM CC_REGULAR, measured): the dispatchable ceiling sat at ~86.7 %
of nameplate in winter and ~78 % in summer, against a real CAMPD fleet that runs
into the 85–95 % band. The "75 % wall" verdict-C1 symptom was this, not an
offer-curve discontinuity.

### The fix: nameplate capacity + one measured summer derate

`ScenarioConfig.cc_nameplate_summer_derate` (on for PJM/NYISO/NEISO; ERCOT and
CAISO/MISO/SPP unchanged) restructures CC_REGULAR / CC_CHP to the **physically
correct seasonal shape**, the same nameplate-anchored capacity ERCOT's CAMPD
bins already use:

- CC LP capacity is raised from net-summer to **full EIA-860 nameplate**
  (`fleet_to_bins`, scaled by the per-plant `net_summer/nameplate` ratio so it is
  robust to fleet-vs-EIA membership differences);
- the **one** allowed derate is the per-plant **measured** summer derate
  (`net_summer / nameplate`, `fleet.cc_summer_capacity`), applied in summer only
  — winter restores full cold-weather capability, which is real for an F-class
  CC. This supersedes the flat 10 % class derate (an improvement *over* ERCOT,
  which still uses the flat value);
- in a historic backcast the statistical **POF and age/performance derate are
  dropped** for CC (the CAMPD overlay supplies the sustained outages, net-summer
  captures performance); only the short-outage **`wefor_residual`** (~1.5 %, the
  brief forced events below the overlay's multi-day detector floor) remains;
- `cc_duct_peaking` is **capped at the F-class supplementary-firing physical
  maximum** (`cc_duct_peaking_cap_pct = 8`), so the duct band stops re-pricing
  the ambient summer gap and now sits at the **top of nameplate (~92 %)** where
  duct firing physically is.

Predicted/measured wall move: Guernsey **75.7 % → 92 %** of nameplate; PJM
CC_REGULAR winter wall median **86.7 % → 93.5 %**; the summer double-derate gone.
The 70–75 % over-stuffing empties. **ERCOT is byte-identical** (every flag gated
off for it).

### What the fix exposes: CC is too cheap (the real open item)

With the false wall removed, PJM 2024 (diagnostic, single-year) CC_REGULAR runs
at **73 % annual CF vs CAMPD's 61 %** and is **+64.7 TWh** over CAMPD net (model
394.9 vs 330.2); model gas ≈ 437 TWh vs ~370 actual, coal ≈ 92 vs ~120 actual.
The model now *over*-runs the top — 95–100 % CF holds **135 600 h vs CAMPD's
34 500** — and is offline only **12.5 %** of hours vs the real **22 %**. Model
peak ≈ CAMPD peak (ratio 1.00), so this is genuine over-generation, not a
normalization artifact.

This is the `CLAUDE.md` rule-11 signal in textbook form: **the 75 % wall had been
silently compensating for a CC offer level that is too cheap.** Capping the plant
low hid the over-running; restoring real capacity surfaces it. The fix must *not*
be a new wall — it must re-level the offer / add the real cycling structure. The
tuning direction (offer level vs commitment vs in-LP reserve co-optimization,
grounded in ERCOT's richer curve and PJM's published market design) is worked
through in `docs/handoffs/pjm-cc-level-tuning-2026-06.md`.

### NYISO confirmation (2026-06-25, `nyiso 26 cc-nameplate` keeper)

Re-solving the NYISO keeper config on the merged nameplate code reproduces the
same rule-11 signal — but **mildly**, as expected for NYISO's small, import-
constrained CC fleet. The 2023 within-gas merit split that the prior keeper left
open **over-closes** once CC carries full nameplate and the Ravenswood steam HR
sits correctly above CC: `CC_REGULAR −3.47 → +2.09 TWh`, `ST_GAS +2.76 → −1.48`
(2024 `CC_REGULAR −2.61 → +2.39`, `ST_GAS −0.96 → −4.31`). CC now over-runs on
energy by only **~+2 TWh/yr** (vs PJM's +64.7 TWh) and **depresses LMP**
(`C3a` 2023 −8.9 %, 2024 −11.0 %; 2025 +9.3 % → in-band). Same root cause and
same fix as PJM: the CC offer level is too cheap, re-levelled via
`_NYISO_OFFER_CURVE` `econ_high` per the tuning handoff — **not** a
re-walled capacity. Kept as the `nyiso 26` keeper per rule #1 (most faithful
structure; the miss is now localized to the single CC-offer lever). See
`results/calibration/nyiso_26_cc-nameplate/calibration_attestation.json` and
`docs/calibration-best-so-far-nyiso.md`.

**Resolved (2026-06-25, `nyiso 27 cc-offer` keeper).** The CC offer level was
re-levelled to the CAMPD CC marginal-HR reach: `_NYISO_OFFER_CURVE` `CC_REGULAR`
`econ_high` **1.12 → 1.21** and `CC_CHP` **1.15 → 1.24** — `1.21×` base_hr, the
**same fit ERCOT's keeper uses** (`econ_high 1.21`). The compressed `econ_high
1.12` had priced the top of each CC's econ body *below* the CAMPD CC marginal
HR; raising it to the grounded reach prices those marginal slices out so CC
stops over-running and stops setting too-low a clearing price. All movements in
the predicted direction, no re-walling, no merit inversion, no 2025 overshoot:
`2023 CC_REGULAR +2.09 → +1.70 TWh` / `ST_GAS −1.48 → −1.26`; `2024 CC_REGULAR
+2.39 → +2.09` / `ST_GAS −4.31 → −4.14`; `C3a` **2023 −8.9 % → in-band**, **2024
−11.0 % → −9.7 %**, 2025 in-band; `C3b` 2024 `0.250 → 0.243`. `econ_high` now
sits at the CAMPD/ERCOT-grounded `1.21×` reach — the lever is **spent at its
grounded landing**; the small residual is *at* that ceiling and is not chased
further (rule #12). The NYISO CC offer-level lever is **DONE**. See
`results/calibration/nyiso_27_cc-offer/calibration_attestation.json` and
`docs/calibration-best-so-far-nyiso.md`.

> **Update (2026-06-25, `nyiso 28 native-hr` — rejected probe):** the `1.21×`
> reach above is **borrowed from ERCOT's** CAMPD-CC fit, not NYISO's own. Run 28
> derived NYISO's native CC/ST incremental-HR curve from NY+NJ CEMS (new tool
> `scripts/data/derive_campd_marginal_hr.py`) and found NYISO's own CC reach is
> **0.925×** (CC_CHP 1.103×), well *below* 1.21 — so re-grounding to it craters
> `C3a` to −24/−26.5/−23.5 %. The lesson sharpens rule #1: CEMS gives the marginal
> **cost**, not the **offer**; the `1.21` reach was proxying the competitive
> offer **markup** that NYISO has no disclosure to measure. The per-ISO-per-class
> native-grounding principle stands, but for an ISO without offer disclosure the
> *markup* component still needs grounding (run 29: a NYISO markup on top of the
> native marginal HR). The steam-side re-level *was* directionally right (halved
> the 2024 `ST_GAS` under-run). Keeper stays `nyiso 27`.

### Code touchpoints (this session)

- `config/scenarios.py`: `cc_nameplate_summer_derate`, `cc_duct_peaking_cap_pct`.
- `data/fleet.py`: `cc_summer_capacity()` / `cc_summer_derate_ratio()`; CC cap
  raise in `fleet_to_bins`; the CC availability branch + per-plant summer derate
  in the availability builder; the duct-band cap in `bins_to_fleet`.
- `scripts/run_calibration.py`: flags wired on for PJM/NYISO/NEISO.
