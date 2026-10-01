# FINDING — NWPP's C4 coal miss is an AMPLITUDE defect, not a shape defect

**Lane:** NWPP-45 · **Date:** 2026-09-22 · **Zero LP.**
**Source:** the designated keeper `2026-09-20-nwpp-44-measured-take`
(`nwpp44_takeorpay_reg`) — its committed `hourly/` sidecars (rule 15
`[R-DASHBOARD]`) plus its EIA-930 benchmark frame, restored at zero LP by the
`--restore-shared-inputs` entry this lane added.
**Status:** diagnostic. **No mechanism was tested, nothing is promoted, no matrix
cell changes** (rule 28 `[R-MECH-MATRIX]` duty (b) does not bind on a lane that
tests nothing).

---

## 0. In one line

The model's coal fleet runs the **right diurnal shape at one-tenth the
amplitude**: mean-profile correlation with the measured series is 0.76–0.94 and
the peak hour is off by one, but the peak-to-trough swing is **0.063–0.090 GW
against a measured 0.892–1.683 GW** — 4–10 % of reality. C4 fails on `r`
because coal barely cycles, not because it cycles at the wrong times.

## 1. Reproduction of the scored numbers first

Computed here from the committed sidecar and the EIA-930 `coal` series — the
same two vectors `render_calibration_html` builds `fuelRows` from, and
`calibration_verdict.score_dispatch_corr` reads:

| year | r | NRMSE | scored r | scored NRMSE |
|---|---|---|---|---|
| 2023 | 0.605 | 0.260 | 0.605 | 0.260 |
| 2024 | 0.595 | 0.246 | 0.595 | 0.246 |
| 2025 | 0.610 | 0.284 | 0.610 | 0.284 |

Exact. So the decomposition below is of the scored quantity, not of a lookalike.

## 2. Where the correlation is lost

Splitting the hourly series into a daily-mean component and a within-day
deviation:

| year | r overall | r of daily means | r of within-day deviation | r of monthly means |
|---|---|---|---|---|
| 2023 | 0.605 | 0.645 | **0.218** | 0.686 |
| 2024 | 0.595 | 0.664 | **0.376** | 0.793 |
| 2025 | 0.610 | 0.715 | **0.425** | 0.866 |

Seasonal placement is good and improving (0.69 → 0.87). Day selection is
middling. **The intra-day term is the weak one in every year**, and C4's floor
is applied to the raw hourly series, so that term is what holds `r` near 0.60.

## 3. The shape is right — the amplitude is not

Mean diurnal profile, model vs measured:

| year | model peak h | actual peak h | model trough h | actual trough h | profile r |
|---|---|---|---|---|---|
| 2023 | 18 | 19 | 9 | 11 | 0.757 |
| 2024 | 18 | 19 | 11 | 10 | **0.941** |
| 2025 | 18 | 19 | 12 | 11 | **0.903** |

The model puts coal's evening peak and midday trough in very nearly the right
hours — the midday solar trough and the h18–20 evening ramp are both present.
What is missing is the size of the move:

| year | model peak−trough | actual peak−trough | ratio |
|---|---|---|---|
| 2023 | 0.090 GW | 0.892 GW | **0.10** |
| 2024 | 0.068 GW | 1.302 GW | **0.05** |
| 2025 | 0.063 GW | 1.683 GW | **0.04** |

**This is the single most useful number in the document.** A fleet that swings
one-twentieth as much as the real one cannot correlate hour-to-hour however
well-timed its swing is.

## 4. The mechanism, read off the keeper's own band sidecar

Share of model coal energy by offer band, and how much each band moves:

| year | mustrun | committed | **mustrun+committed** | econlo | econhi | peak |
|---|---|---|---|---|---|---|
| 2023 | 40.6 % | 36.7 % | **77.3 %** | 11.6 % | 9.5 % | 1.5 % |
| 2024 | 50.5 % | 42.2 % | **92.7 %** | 3.7 % | 3.0 % | 0.7 % |
| 2025 | 49.7 % | 43.2 % | **92.9 %** | 3.4 % | 2.8 % | 0.9 % |

The two price-insensitive bands carry 77–93 % of coal energy, with per-band
`cv` of 0.15–0.24 against 0.50–1.53 for the econ/peak bands. In 2024 and 2025
the price-responsive bands carry **~7 %** of coal energy — there is almost
nothing left that can respond to an hourly price.

**This is the take-or-pay keeper's own disclosed cost, now measured.** The
keeper note states the arm "ENLARGES the cheap block (`_mustrun` and
`_committed` collapse to one price at every regulated contracted plant) and
leaves the econlo/econhi/peak shelf within $0.51/MWh of itself", and that it
"does NOT build the rising coal offer curve that NWPP-43 §4.1 diagnosed as the
C4 root cause". The band table is what that looks like in energy terms: the
flat share rose from 77 % to 93 %.

That is **not an argument against the keeper.** The arm is measured-input,
zero-free-parameter, and improved C4 on both metrics in all three years
(NRMSE moved inside the 0.30 gate everywhere). Rule 1 `[R-STRUCT]` and rule 14
`[R-ACCURATE]` both say a structurally-correct measured input stays in and the
residual gets root-caused. This document is the root-causing.

## 5. What this rules IN and OUT for a successor

**Ruled OUT as the C4 driver** — each contradicted by a measurement above:

* *Wrong hours / phase error.* Profile `r` 0.76–0.94, peak hour off by one.
* *Wrong season.* Monthly `r` 0.69–0.87 and rising.
* *Coal volume.* NWPP-44 already cut `sum|error|` 25.574 → 10.866 TWh (−57 %)
  and `r` moved only 0.570 → 0.605. Volume was necessary and is not sufficient.

**Ruled IN:** the offer stack's **vertical extent** across the coal fleet — how
much MW sits at a price a normal NWPP day actually crosses. The fleet has the
right silhouette and no dynamic range.

**Open, and deliberately not answered here** (this lane tested nothing): whether
the binding constraint is the *price* spacing of the bands (the ≤$0.51/MWh
shelf), the *MW* allocation between them (`econ_low_share` / `pct_peaking` are
structural shares, and rule 1's price-tuning carve-out explicitly does **not**
extend to them), or a genuine commitment-physics floor that should be cycling
and is not (rule 17 `[R-FLOOR-WINDOW]`: a floor binding where its driver says
the class should be moving is a bug by definition). A successor picks one on
its own evidence and pre-registers it.

## 6. Caveats, carried not absorbed

* The measured series is the EIA-930 `coal` aggregate over NWPP's BAs, which
  carries its own reporting artifacts (this lane's own restore logged spike
  repairs in AVA / NWMT / NEVP 2025). It is used because it is exactly what the
  scorer uses — the comparison is apples-to-apples for C4 whatever the series'
  absolute quality.
* §3's table is the **mean** diurnal profile, so day-to-day variation is
  averaged out. §2's within-day term is the un-averaged statement and agrees.
* 2023 has both the largest econ-band share (22.6 %) **and** the worst
  within-day `r` (0.218). So econ share alone does not predict intra-day fit —
  the timing of the econ band's dispatch matters too. Stated rather than
  smoothed into a cleaner story.
* NWPP remains **PRICE UNSCORED** (rubric v3.8): C3a/C3b/C3c are not scored in
  any year, so nothing here is evidence about price formation. Every NWPP-40/41/42
  disclosure is inherited, the −10.02 TWh 2025 energy balance included.
