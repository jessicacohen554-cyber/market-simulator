# ERCOT backcast audit — follow-up tests D1–D4 (results)

**Date:** 2026-06-16
**Companion:** `docs/ercot-backcast-audit-2026-06.md` (the audit; finding IDs
B1/B2/… referenced here).
**Scope:** the four tests the audit prioritised, run against the keeper
(run 115b). **2022 and H1-2026 were deliberately excluded** (the user's
untrained holdout sets). All runs are committed bundles under
`results/calibration/`; the tooling is `scripts/run_calibration_full.py
--statistical-mode`, `scripts/score_backcast_shape_emissions.py`, and the
volume scorer at the 0.33% universal gate.

**`keeper_anchor` reproduces run 115b exactly** (same 5 in-scope fails at the
0.33% gate: CT 2023/2024, CC_REGULAR 2024/2025, PRB 2024) — so every delta
below is measured against a same-environment baseline, not the older bundle.

---

## Headline

| Test | What it measures | Result |
|---|---|---|
| **D1** out-of-sample (all overlays off) | the forecast-machinery skill prior | **fails double 5 → 10**; CT collapses −75/−88%; coal +7–8 TWh; total CO₂ +8/+9%; hourly-r 0/18 |
| **D2** single-overlay ablation | which overlay carries the fit | **historic-outage overlay dominates** (5→9 alone); CT deployment floor smaller (5→6, ~1.5 TWh) but the most answer-injecting |
| **D3** new gates (CO₂ / shape) | what the volume gate misses | built + applied; catches a real keeper fail: **2024 coal CO₂ −8.9%** hidden under a passing total |
| **D4** CC_REGULAR fix | can the shape failure be closed | **merit-ramp fixes the shape cleanly** (cf_emd & r improve 18/18) but the 2024/25 volume over-run is **not** offer-closable — confirms the spatial/year-gradient diagnosis |

The audit's three headline claims are now **measured, not asserted**: the
backcast is not yet a forecast prior (D1); the leakage is mostly the
*defensible* outage overlay with a smaller *circular* CT piece (D2); the
volume gate hides a real CO₂/shape failure (D3); and the CC problem needs
spatial resolution, not tuning (D4).

---

## D1 — Statistical-mode (out-of-sample) backcast  `results/calibration/statmode_d1`

Re-ran 2023/24/25 with `--statistical-mode`: every per-hour/per-year
answer-injection overlay off (historic outages → statistical WEFOR/POF, the CT
AS/RUC-deployment floor, the spatial reliability-deployment floor, the ST
WEFOR-residual relief, per-plant monthly coal pricing), keeping only the
structural model (per-plant heat rates, offer curves, coal passthrough
sigmoids, cc-duct band, storage) and the realized annual Henry Hub gas price
(the "realized-fuel" variant — isolates dispatch machinery from fuel-forecast
error). Residual devices with no clean toggle and left on (small-order,
documented): the 2023-only ERCOT wind HSL rescale, the nuclear monthly-CF
overlay, and per-plant CEMS emission rates (the last does not affect dispatch
at carbon_price = 0).

**Volumes — in-scope fails double, 5 → 10** (overlay contribution = the
`vsKeeper` swing, TWh):

| class | 2023 d (stat / keeper) | 2024 d | 2025 d | overlay carried |
|---|---|---|---|---|
| CT_PEAKER | **−5.21** / −1.61 | **−6.62** / −2.10 | **−5.70** / −0.43 | +3.6 / +4.5 / +5.3 |
| COAL_PRB | **+7.83** / +0.42 | +3.41 / −4.49 | **+7.60** / −0.27 | +7.4 / +7.9 / +7.9 |
| COAL_LIGNITE | +1.78 / +0.92 | −0.28 | **+4.88** / +0.29 | +0.9 / +0.6 / +4.6 |
| ST_GAS | −0.75 | **−3.46** / −0.76 | +0.94 | −1.7 / −2.7 / +0.5 |
| CC_REGULAR | −0.55 | **+9.84** / +6.31 | +0.07 / +3.61 | +0.3 / +3.3 / −3.7 |

CT_PEAKER **collapses to 0.8–1.8 TWh against ~7 actual** — i.e. the deployment
floor was supplying essentially the entire CT match; the energy-only LP prices
peakers out. Coal **over-runs +7–8 TWh** once the historic-outage overlay stops
removing it. This is the audit's B1, quantified: the overlays are load-bearing,
and they have no forward analogue — so the dispatch logic being validated is
not the dispatch logic being forecast.

**CO₂ — out-of-sample carbon is materially over-estimated.** Total fossil CO₂
**fails 2023 (+8.1%) and 2025 (+9.4%)** driven by coal CO₂ **+15.5% / +20.9%**
(the coal over-run). CO₂ gates 5/9 vs the keeper's 8/9.

**Hourly shape — `pearson_r` degrades on 0/18 class-years** (coal r 0.80→0.55,
CC_REGULAR 0.74→0.49–0.54): the overlays carry timing too, not just annual
volume. `cf_emd` 4/18 pass.

> **Read:** the headline backcast number is not a forecast-skill prior. The
> dispatch machinery alone is much weaker — roughly *double* the volume fails,
> ~8–9% high on system CO₂, and materially worse hourly timing.

---

## D2 — Single-overlay ablation (localising the leakage)

Each run is the keeper with **one** overlay removed; fail counts at the 0.33%
gate, against keeper = 5:

| run | overlay removed | fails | what moved |
|---|---|---|---|
| `d2_noCT` | CT AS/RUC-deployment floor | **6** | CT_PEAKER −0.9/−1.5/−1.7 TWh (2025 → FAIL); others < 0.9 |
| `d2_noOutage` | historic outage overlay | **9** | coal +7.2/+7.7/+7.6; CC_CHP −3 (WEFOR relief); ST_GAS 2024 → FAIL; CT craters |
| `statmode_d1` | **all** answer-injection | **10** | (the sum, above) |

**The historic-outage overlay is the dominant lever** — removing it alone
takes 5 → 9 fails, drives the +7 TWh coal swing, and is what makes both CO₂
(8/9 → 5/9) and hourly-r (15/18 → 0/18 vs the CT case) hold. Crucially it is
also the **most defensible** device: real ≥5-day outages happened, and the
statistical WEFOR cannot place them in the right hours, so most of this "gap"
is legitimately-unforecastable availability, not a fitting artifact.

**The CT deployment floor is the most answer-injecting but the smallest
lever** — removing it is +1 fail (5 → 6) and ~1.5 TWh. It pins peakers to
their observed CEMS output, so its fit is close to definitional; yet even
*with* it CT still fails (the non-CEMS small peakers, ~1 TWh/yr, are
unreachable). So the genuinely-circular piece of the leakage is real but
bounded to ~1.5 TWh on a single small class.

> **Read:** "overlay leakage" is not monolithic. ~80% of it is the outage
> overlay (defensible, large), ~1.5 TWh is the CEMS-pinned CT floor (circular,
> small). The honest forecast-error prior should be read off D1; the CT floor
> is the one to treat with most suspicion when quoting CT economics.

---

## D3 — The missing gates (CO₂ + operating-shape), now built and applied

`scripts/score_backcast_shape_emissions.py` adds the three checks the volume
gate is blind to (no LP re-solve — reads `plant_hourly_fit.parquet` + CEMS
intensities): carbon-weighted CO₂ (total ±5%, per-fuel ±7%), the `cf_emd`
operating-shape regression gate, and the hourly-`r` regression gate.

**It immediately caught a real keeper failure the volume gate passes:**

| keeper (run 115b) CO₂ | 2023 | 2024 | 2025 |
|---|---|---|---|
| coal | +1.9% | **−8.9% FAIL** | +0.7% |
| gas | +4.2% | +5.9% | +4.9% |
| **total** | +3.2% | **−0.2% PASS** | +3.1% |

2024 total CO₂ passes (−0.2%) while **coal CO₂ is −8.9%** — the gas over-run
(+5.9%) compensates in MWh but not in carbon (coal is ~2× the intensity). This
is exactly the split-compensation the audit predicted (B5d): the 2024 coal
under-run is a genuine carbon-accounting error the volume gate cannot see. Gas
CO₂ also runs persistently +4–6% hot (the gas fleet absorbs the CT/coal
misses). **Recommendation: adopt the CO₂ gate and the cf_emd/r regression
gates** — they are nearly free and catch failures the volume gate passes.

---

## D4 — CC_REGULAR fix: shape is closable, volume is not (by an offer lever)

Two variants vs keeper (CC_REGULAR runs flat-baseload and misses its >90% CF
hours — audit B2):

| run | change | fails | CC_REGULAR shape (cf_emd; r) | CC volume d (23/24/25) |
|---|---|---|---|---|
| keeper | — | 5 | 0.099/0.105/0.113; 0.74/0.73/0.72 | −1.06 / +6.31 / +3.61 |
| `d4a_meritramp` | restore rising econ ramp | 6 | **0.088/0.098/0.101; 0.76/0.76/0.74** (18/18 PASS) | −2.08 / **+5.18** / **+2.77** |
| `d4b_ccfix` | merit-ramp + cheapen duct wall 2.57→1.55× | 6 | same as d4a (16/18 r) | +1.08 / **+8.82** / **+5.46** |

**The merit-ramp (d4a) cleanly fixes the operating-shape failure** — cf_emd and
hourly-r improve in every class-year (18/18 regression-gate PASS, no class
regresses), reproducing the run-118 finding that WH2/CB2 shed their 0.8–0.9 CF
pin and fill the cycling bands. It also *reduces* the 2024/2025 volume over-run
(+6.31→+5.18, +3.61→+2.77). Its only cost is CC 2023 over-correcting low
(−2.08, a fail by 0.6 TWh).

**Cheapening the duct wall (d4b) adds no shape benefit over the merit-ramp and
worsens volume** — a cheaper peak band lets the efficient CCs generate *more*,
inflating the 2024/2025 over-run (+8.82, +5.46) and dragging ST_GAS 2024 into a
fail. So the audit's proposed duct-band cheapening is **not** worth it; the
merit-ramp alone is the better move.

Decisively, **no D4 variant closes the CC_REGULAR 2024/2025 volume over-run** —
the over-run survives every offer-curve move because it is the gas-price
year-gradient (clearing 2025 over-corrects 2023) plus the North/South_Central
spatial misallocation, neither of which an offer lever can reach. This is the
audit's B2 spatial axis, now confirmed empirically: **the CC fix is a
shape/spatial problem, not a merit-tuning problem.** And the 2024 coal CO₂
−7.7% fail persists in both D4 runs — the CC fix does not touch the coal split.

> **Recommendation:** adopt the merit-ramp deltas for the shape fix (and gate
> cf_emd so it can't regress); pursue the CC volume over-run through the
> spatial overlay / finer zones (NP6-785-ER), not further offer tuning.

---

## What this changes in the audit's recommendations

- **B1 (leakage) — confirmed and quantified, with nuance.** The backcast is
  not a forecast prior (D1: 5→10 fails, +8/9% CO₂, r 0/18). But the leakage is
  *mostly the defensible outage overlay* (D2: the dominant lever, real
  outages) with only ~1.5 TWh of genuinely-circular CEMS-pinned CT. Quote D1 as
  the dispatch-error prior; treat CT economics with the most caution.
- **B5d / D3 (gates) — adopt.** The CO₂ and cf_emd/r regression gates caught a
  real keeper failure (2024 coal CO₂ −8.9%) and a clean D4 shape win. They
  belong in the live pass/fail path (the peer-review §D.4 single-evaluator
  recommendation).
- **B2 (CC shape) — fixable on shape, blocked on volume.** Adopt the
  merit-ramp; the residual volume over-run is spatial and needs the parked
  NP6-785-ER work, not tuning.

---

## D4-spatial pre-test — would finer zones + a joint retune be impactful? **No.**

Before building any finer-zone topology, the decisive, no-LP pre-test: rank
ERCOT's actually-binding transmission constraints from the published SCED NP6-86
shadow-price archive (`scripts/archive/analyze_sced_binding.py` over 24,881 intervals,
2023–25; full table `docs/sced-binding-constraints-2023-2025.csv`). The question
was whether a North↔South_Central (or load-zone) split would place a *binding*
limit between the CC_REGULAR over-zone and the under-zone — the only way a
finer topology lets the offer curves relax toward physical instead of re-fitting
the same global compensation.

**Result — the congestion is nodal, not zonal:**

- **94% of all binding-constraint congestion rent is on local pockets
  (< 200 kV); only 6.2% is on the ≥ 345 kV backbone.** The single largest 345 kV
  constraint (PAWNEE–CALAVERAS, internal to the San Antonio/SC area) is **0.73%**
  of total rent; no zonal-scale interface carries meaningful congestion.
- **The rent is extremely diffuse: 33 constraints to reach 50% of it, 123 to
  reach 80%** (1,052 distinct binders). The top binders are deep sub-load-zone
  pockets — the **Rio Grande Valley** cluster (FALFUR–PREMONT, BURNS–RIOHONDO,
  CATARINA, LOYOLA, LA_PALMA), the **Permian/West** cluster (ODESSA–YARBR,
  VEALMOOR–KOCHTAP, KNAPP, MIDLAND), and scattered 138 kV autotransformers — all
  far below any practical zonal boundary.

**Conclusion.** A finer-zone split would **not bind** (exactly why the earlier
inter-zonal TTC moves, the run118 spatial overlay, and the run119 CPS floor were
all weak — they operate at zonal/few-pocket resolution while the binding lives at
nodal-pocket resolution). So **finer zones + a joint offer/sigmoid retune is not
a promising lever**: with no binding zonal interface, the offer curves can't
relax, and the retune would just re-fit the same global compensation on a
slightly finer grid. The CC_REGULAR over-run's spatial component is real but
lives **below zonal resolution** — capturing it needs a genuinely nodal model,
or a data-targeted out-of-merit floor over dozens of the top SCED pockets (a
heavy generalization of run119's single CPS floor, with steep diminishing
returns given the 123-constraint tail). **Recommendation: do not build finer
zones for this; accept the residual CC volume over-run as a documented
zonal-reduction limitation, and keep the merit-ramp as the shape fix.**

---

**Not done (out of scope here):** the capacity hindcast (audit D-series is
dispatch-only), the 2022/H1-2026 holdout (the user's untrained sets — excluded
by request), and a tightness-responsive ORDC reliability-deployment offset
(audit B3). These remain open.
