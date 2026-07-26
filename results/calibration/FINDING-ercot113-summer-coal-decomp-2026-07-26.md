# FINDING — ERCOT-113 Task A: the summer coal over-run is a WITHIN-ENVELOPE utilization error, and it is not priced

**Date** 2026-07-26 · **ISO** ERCOT · **Years** 2023–2025 · **No LP** ·
**Probes** `scripts/probes/ercot113_summer_coal_decomp.py`,
`scripts/probes/ercot113_summer_merit_basis.py` ·
**Read** `results/calibration/ercot112_coal_marginal_hr_fullspan/hourly/` (rule 15 — no re-solve)
and `data/raw/ercot-thermal-dam-availability-site-hourly.parquet`

ERCOT-112 fixed the annual coal LEVEL and left a seasonal residual with the same signature in all
three years (Jun–Sep ratio 1.169 / 1.292 / 1.256 against shoulder months at or below 1.0). The
ERCOT-113 charter enumerated three candidates. **All three were measured before any mechanism was
built. Two are refuted, the third is confirmed — and then its own price-side explanation is
refuted too.**

## 1. The pinning fact that governs candidates (a) and (b)

Both ERCOT-112 arms already run `ercot_thermal_dam_availability_coal` **together with**
`ercot_thermal_dam_availability_hourly` and `ercot_thermal_dam_availability_plant`, plus
`coal_nameplate_summer_derate=True`. So the model's coal availability is **already pinned to the
measured 60-Day DAM live-HSL / rating fraction at plant-hour grain**, in every hour of every year.

Whatever seasonal structure exists in the measured DAM envelope — ambient derate, maintenance
timing, anything — is therefore *already in the model's envelope by construction*. Candidates (a)
and (b) cannot be missing drivers unless the measured envelope itself shows something the model
fails to reproduce. It does not.

## 2. Candidate (a) — summer ambient derate: **REFUTED, and the sign is backwards**

The measured coal `live_mw / rating_mw` fraction does not dip in summer. It **rises**:

| year | shoulder | Jun–Sep | delta |
|---|---|---|---|
| 2023 | 0.773 | 0.870 | **+0.097** |
| 2024 | 0.739 | 0.867 | **+0.128** |
| 2025 | 0.712 | 0.812 | **+0.100** |

There is no summer ambient capability derate in the DAM data to add. The charter's instruction to
"verify it is actually biting and at the right magnitude" resolves as: whatever ambient derate
exists is already transferred by the pinning overlay, and the *net* seasonal movement of measured
coal capability is upward, not downward.

## 3. Candidate (b) — summer planned-outage asymmetry: **real, already captured, and pushes the wrong way**

Real coal genuinely does take spring/fall maintenance and carry more capability in summer:

| year | shoulder live MW | Jun–Sep live MW | delta |
|---|---|---|---|
| 2023 | 10,502 | 11,820 | +1,318 (+12.6 %) |
| 2024 | 10,037 | 11,772 | +1,736 (+17.3 %) |
| 2025 | 9,093 | 10,371 | +1,278 (+14.1 %) |

The driver is real and the charter was right to flag the sign question. It is already pinned into
the model's envelope — and it pushes the wrong way: **more** summer capability makes the model run
**more** coal in summer, not less. Capturing it better cannot close an over-run.

## 4. The decisive measurement — utilization of the *measured* envelope

Because the envelope is pinned, the over-run must show up as utilization, and it does:

| year | season | model util | actual util | **gap** | model MW | actual MW |
|---|---|---|---|---|---|---|
| 2023 | shoulder | 0.567 | 0.588 | −2.1 pp | 5,947 | 6,149 |
| 2023 | **summer** | 0.891 | 0.762 | **+12.9 pp** | 10,531 | 9,007 |
| 2024 | shoulder | 0.608 | 0.602 | +0.6 pp | 6,078 | 6,031 |
| 2024 | **summer** | 0.880 | 0.681 | **+20.0 pp** | 10,356 | 8,014 |
| 2025 | shoulder | 0.808 | 0.744 | +6.4 pp | 7,338 | 6,751 |
| 2025 | **summer** | 0.992 | 0.790 | **+20.2 pp** | 10,289 | 8,194 |

The model runs the *same measured envelope* 13–20 pp harder than reality did in summer, while
tracking it in the shoulder. This is ERCOT-111's annual finding (99 % economic dispatch inside the
real committed HSL envelope) localized to the season that carries the residual.

Sharpest form: in Jun–Sep the model dispatches coal at **84–103 % of the measured committed HSL** —
essentially flat out, and in Jul/Aug 2025 slightly *above* it — while reality ran **66–82 %**.
**The model has no mechanism that keeps coal off its ceiling in summer.**

## 5. Candidate (c) — displacement: **CONFIRMED**

Monthly model-minus-actual coal against model-minus-actual gas are near-perfect mirror images:

| year | corr(dCoal, dGas) | summer dCoal | summer dGas |
|---|---|---|---|
| 2023 | **−0.973** | +1,524 MW | −1,672 MW |
| 2024 | **−0.981** | +2,342 MW | −2,112 MW |
| 2025 | **−0.947** | +2,095 MW | −2,074 MW |

The coal surplus is the gas deficit, month for month. The marginal unit is being mis-ranked in
summer — exactly the reading the charter attached to this candidate.

## 6. …but the price side of (c) is **refuted too**

The charter's pointer was "the summer gas price / heat-rate basis". Measured directly off the
model's own built offer curve (no LP), the deliverable-weighted coal→CC spread by season:

| year | shoulder spread | Jun–Sep spread | widening |
|---|---|---|---|
| 2023 | $53.04 | $58.63 | +5.59 |
| 2024 | $46.28 | $49.32 | +3.05 |
| 2025 | $67.06 | $58.20 | **−8.86** |

Two things kill the price explanation:

1. **The sign is not consistent.** 2025 has the *largest* summer over-run (Jun–Sep util gap
   +20.2 pp) with a *narrowing* spread. A driver that reverses sign while the effect holds steady
   is not the driver.
2. **The spread is far too large for price to be the binding consideration at all.** Model coal
   offers $15.6–23.2/MWh against CC at $48–97/MWh — coal sits **$46–67/MWh inframarginal in every
   month of every year**. At that depth no plausible fuel-basis correction changes coal's rank; the
   LP will run it to its bound whenever it is available.

This also disposes of the open coal-SRMC question in the charter's separate-lanes list *for this
residual*: the model's coal SRMC being ~$28 against a ~$21 top submitted DAM offer would make model
coal look too **expensive**, which pushes coal *down*. It cannot explain an over-run, and it remains
its own F923 charter.

## 7. What this leaves

The summer coal over-run is **a quantity-side mechanism, not a price-side one**. Coal is deeply
inframarginal, its envelope is measured-pinned and correct, and the model dispatches it to that
envelope in summer while the real fleet held it near 70 % of committed HSL. The missing structure
is something that **limits coal ENERGY or its sustained output rate independently of price**.

Everything already closed stays closed: coal capability ceiling and coal commitment/min-down bridge
(ERCOT-111, 0.01 and 0.17 TWh against an 11.7 TWh error), coal AS headroom (1.3 %), coal ramp
(the model ramps *less* than reality), and the reserve side (ERCOT-107/108). None is reopened here.

**Recommended next charter (ERCOT-114), with the enumeration this probe supports.** Measure, before
building, whether real ERCOT coal is held off its ceiling by an energy/rate budget. Two candidates
have a real driver, a window and a forward story (rule 18), and both are measurable with data
already in the repo:

* **Ozone-season NOx allowance budget.** Texas coal is in the CSAPR Group 3 ozone-season NOx
  program, whose window is **May 1 – Sep 30** — which matches the over-run window in all three
  years (the elevation starts in May: 1.085 / 1.136 / 1.181, and falls back in October). The
  objective already carries a `nox_rate × nox_price` term and `policy/cap_and_trade.py` already
  resolves carbon-style programs, so the mechanism has somewhere to land. Measure first: per-unit
  CAMPD ozone-season NOx mass against the published Texas Group 3 budget, by year.
* **Coal fuel supply / delivery-rate limit.** A stockpile drawn down against a roughly constant
  rail/mine delivery rate produces exactly a flat utilization ceiling that does not respond to
  price — the observed signature. Measure first: EIA-923 monthly coal receipts vs consumption and
  end-of-month stocks for the ERCOT coal plants.

Both are rule-13-admissible in principle (published forward budgets / delivery physics that
regenerate for a forecast year and respond to changed conditions), but **neither should be built
before its driver is measured** — which is the discipline that closed four candidates across
ERCOT-111 and this probe without writing a line of mechanism code.

## 8. Rules observed

Nothing was reverted or weakened to chase a residual: `ercot_thermal_dam_availability_coal` and
`coal_econ_marginal_hr_bound` are untouched measured inputs (rules 1, 13, 14), the take-or-pay /
PRB sigmoid was not touched (rule 23), and the CAMPD marginal-HR artifact was not re-derived
(no source-data change). No solve was run for this finding.
