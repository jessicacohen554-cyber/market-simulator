# NYISO — the overnight price-setter is the hydro budget dual, not a thermal offer

**Date:** 2026-07-25 · **Keeper under study:** `2026-07-23-nyiso-72-netrev-margin`
(`results/calibration/nyiso72_netrev_margin`, determination NOT-YET, load-bearing
FAILs C3a/C3b/C3c 2023). Every number in §1–§4 is measured from the keeper's
committed `hourly/` sidecars and from raw sources — **no solve**. §5 reports the
`nyiso-74` A/B.

All hourly work is on the repo's non-leap 8760 model clock (Feb 29 dropped).

---

## 0. Headline

The prior session's named Lane A — *"a committed CC's low-load tranche is priced
at its tranche-AVERAGE heat rate where the real market's setter is the
INCREMENTAL heat rate"* — is **refuted as the dominant C3a-2023 overnight
mechanism**, and refuted for a reason that also explains every earlier refuted
A/B on this residual:

> **In the majority of overnight hours no thermal offer sets the NYISO price at
> all. The price is the shadow price of the conventional-hydro monthly energy
> budget — a water value.**

Markup, per-plant gas, zonal gas basis, the net-revenue margin offer form and
the ERCOT-63 gas commitment bridge all move the *thermal* stack. The trough is
not on the thermal stack. That is why all of them were inert or
spread-compressing.

---

## 1. What is marginal overnight — measured

`d(class MW)/d(system demand MW)` over hod 0–6, demeaned **within (month ×
hour-of-day)** so neither the seasonal fuel path nor the diurnal shape can
confound it (`hourly/class_hourly_<y>.parquet` + `system_<y>.parquet`, P1):

| class | 2023 | 2024 | 2025 |
|---|---|---|---|
| **hydro** | **+0.776** | **+0.804** | **+0.576** |
| CC_REGULAR | +0.210 | +0.119 | +0.192 |
| ST_GAS | +0.136 | +0.205 | +0.286 |
| import | −0.139 | −0.223 | −0.128 |
| CC_CHP | +0.065 | +0.078 | +0.055 |

Hydro absorbs **58–80 %** of the marginal overnight MW. It is the swing
resource, not a price-taker.

This is consistent with, and completes, the 2026-07-24 finding that the import
node is pinned at a rung boundary in 69.7 % of overnight hours and that rung
prices set the price in ~2 % of them: **neither imports nor a gas band is the
overnight setter.**

## 2. Why hydro is marginal — it is an inter-temporal budget resource

`data/hydro.py` represents conventional hydro as a **monthly energy budget**
(`sum_{t in month m} P[g,t] <= monthly_energy[g,m]`) with a two-sided
`min_mw`/`max_mw` envelope (`monthly_min_energy` → the `hydro_monthly_min` row
family). Within the month the LP chooses *when* to generate, with perfect
foresight.

When a budgeted plant is interior (strictly between its bounds), its optimality
condition is `price = λ`, the budget dual. That is a **per-month constant**, not
a fuel-linked marginal cost.

**The keeper's prices show exactly that.** Upstate_West, hod 0–6, 2023 — modal
price per month and the share of overnight hours sitting on it:

| month | modal $ | share | p25 / p50 / p75 |
|---|---|---|---|
| Jan | 37.86 | 72.4 % | 37.86 / 37.86 / 37.86 |
| Feb | 32.33 | 50.0 % | 32.33 / 32.33 / 33.17 |
| Mar | 34.13 | 81.1 % | 34.13 / 34.13 / 34.13 |
| Apr | 28.74 | 86.2 % | 28.74 / 28.74 / 28.74 |
| May | 26.19 | 37.3 % | 25.35 / 26.19 / 26.19 |
| Jun | 35.06 | 31.9 % | 32.01 / 34.48 / 35.06 |
| Jul | 37.79 | 49.3 % | 35.55 / 37.79 / 37.79 |
| Aug | 34.06 | 59.4 % | 33.26 / 34.06 / 34.06 |
| Sep | 30.01 | 31.0 % | 26.82 / 30.01 / 30.76 |
| Oct | 27.06 | 39.2 % | 25.18 / 26.74 / 27.06 |
| Nov | 34.31 | 57.6 % | 34.31 / 34.31 / 34.31 |
| Dec | 34.12 | 59.4 % | 34.12 / 34.12 / 34.12 |

In five of twelve months the entire interquartile range collapses onto one
cent-exact value. A thermal tranche's MC moves with the delivered-fuel overlay
hour to hour and could not pin 86 % of a month's overnight hours to one cent.

NYISO is uncongested overnight — Capital_Hudson / Long_Island / Lower_Hudson /
NYC carry identical overnight price levels — so this single resource prices the
whole system.

### The decisive discriminator: the price ignores its supposed fuel

Implied marginal heat rate of each month's modal overnight price, at the
model's own ISO-month delivered gas (`iso_monthly_gas_prices("NYISO", 2023)`),
VOM $2:

| month | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gas $/MMBtu | 10.02 | 5.62 | 3.13 | 1.93 | 1.77 | 1.79 | 2.44 | 1.78 | 1.96 | 1.81 | 2.71 | 3.35 |
| implied HR | 3.58 | 5.40 | 10.26 | 13.84 | 13.70 | **18.49** | 14.65 | 18.01 | 14.28 | 13.84 | 11.91 | 9.60 |

**Implied HR spans 3.58 → 18.49, a 5.2× swing**, while the price itself stays
inside $26–38 as gas moves 5.7× ($1.77 → $10.02). No gas band has a heat rate
that swings 5×. **A price that is invariant to a 5.7× move in its supposed
marginal fuel is not being set by that fuel.**

> The 2026-07-24 finding's "overnight marginal HR 9.97 → a ~10 HR steam unit"
> used the *annual* gas price ($3.09). 9.97 is simply where the middle of a
> 3.6–18.5 monthly range lands. The steam-band attribution was an averaging
> artifact.

## 3. The water value is too high because the LP over-arbitrages hydro

Model vs measured (EIA-930 `NYIS NG: WAT`) hydro diurnal concentration:

| year | source | overnight (0–6) | evening peak (16–19) | ratio | TWh |
|---|---|---|---|---|---|
| 2023 | model | 1,970 MW | 4,248 MW | **0.464** | 28.38 |
| 2023 | measured | 2,432 MW | 3,565 MW | **0.682** | 26.84 |
| 2024 | model | 2,144 | 4,155 | **0.516** | 27.85 |
| 2024 | measured | 2,420 | 3,646 | **0.664** | 26.78 |
| 2025 | model | 1,775 | 3,134 | **0.566** | 21.05 |
| 2025 | measured | 2,009 | 3,532 | **0.569** | 24.10 |

The model **withholds 462 MW of hydro overnight in 2023** (276 MW in 2024) and
over-runs the evening peak by **683 MW** (509 MW). Real NYISO hydro is dominated
by Niagara (~2.4 GW) and St. Lawrence (~0.9 GW) — licensed, largely run-of-river
projects with limited pondage that physically cannot move a month's energy from
nights into evening peaks. The LP grants them a full month of arbitrage freedom.

**The year-by-year tracking is the corroboration:**

| year | hydro ratio model vs measured | C3a |
|---|---|---|
| 2023 | 0.464 vs 0.682 — **worst over-arbitrage** | **FAIL +18.3 %** |
| 2024 | 0.516 vs 0.664 | PASS +1.8 % |
| 2025 | 0.566 vs 0.569 — **matched** | PASS −2.4 % |

The only year whose hydro diurnal shape matches measurement is the only year
C3a passes cleanly on both bands. And the residual's own shape is the
signature: **+$7.62 overnight, +$1.62 at evening peak** — precisely what
withholding cheap energy from the trough and dumping it on the peak produces.

Hydro also carries **no D-2 floor** (0.0 % forced, all three years), so this is
pure LP economics — not a forced-dispatch artifact.

## 4. Rule-19 enumeration before touching anything

D-2 mechanism attribution, `legitimacy_diagnostics.json`:

* **ST_GAS** is floored by **exactly one** mechanism — `reliability_floor`
  (31.0 % / 41.2 % / 27.7 %). Nothing is stacked. Its D-4 window is declared
  `h0-23`, i.e. all hours, so the off-window test is trivially 0.0 — that is a
  weak window under rule 12 and is noted, not acted on (the floor is pinned).
* **hydro** is floored by nothing.

So the hydro lane requires no reconcile-or-replace: it is an *unoccupied*
mechanism slot, not a second floor on an existing one.

## 5. `nyiso-74` — the A/B

`hydro_dispatch_envelope` (ScenarioConfig, GATED default off) already implements
exactly the missing physics, and was built for this failure mode on CAISO:

> "Without it the budget LP **hoards the monthly hydro energy into the top price
> hours with perfect foresight** (CAISO 2024: model evening p95 exceeds measured
> p95 by 1–2+ GW in 9 of 12 months), displacing the evening gas/CT reality runs."
> — `scenarios.py`, citing `FINDING-caiso72-step0-evening-displacement-2026-07-10.md`

It caps the hydro fleet's hourly dispatch at the measured per-(month × hod)
p95 of EIA-930 `NG: WAT` — a deliverability ceiling, not a pin: the LP still
clears its merit order below the ceiling. It is armed in the CAISO keeper lane.

**Rule-13 posture (stated explicitly, because the prior session forbade
`interchange_shaping` from the same family).** The two are *not* the same
object. `measured_interchange_envelope` returns `None` for a forecast year by
construction — no forward analogue exists, which is why it was ruled forbidden.
`measured_hydro_hourly_envelope` falls back to the **pooled
`HYDRO_CLIMATOLOGY_YEARS` (2021–2025) per-bucket percentile** for any year the
extract does not cover, so it regenerates forward and responds to changed
conditions (a different fleet, a different water year via `hydro_year`). It is
a ceiling on a physical capability (head/flow/scheduling), the same class as the
published SIL — not the scored outcome fed back.

Probe: `nyiso-74`, `replay_keeper` of the nyiso-72 keeper with the single delta
`hydro_dispatch_envelope=True`, 2023 only (scoping).

*(Result recorded in §6 below and in `docs/calibration-log/nyiso.md`.)*

---

## 6. Result — mechanism CONFIRMED, instrument INSUFFICIENT, C3a level WORSE

2023, `nyiso-74` vs the `nyiso-72` keeper. Flag confirmed bound **from the LP
output**, not from `run_config` (`NYISO 2023: hydro deliverability envelope on
154 units (evening p95 4394 MW)`) — the `prb_overrides` stomp check.

| | keeper | nyiso-74 | Δ | measured |
|---|---|---|---|---|
| hydro overnight MW | 1,970 | **2,269** | **+300** | 2,432 |
| hydro evening-peak MW | 4,248 | **4,018** | **−231** | 3,565 |
| hydro overnight/peak ratio | 0.464 | **0.565** | **+0.101** | 0.682 |
| **hydro hourly r vs EIA-930** | 0.638 | **0.717** | **+0.079** | — |
| hydro TWh | 28.38 | 28.38 | 0.00 | 26.84 |
| overnight LMP $/MWh | 33.20 | 32.41 | **−0.79** | — |
| evening-peak LMP | 45.83 | 49.44 | +3.61 | — |
| **peak−trough spread** | 12.63 | **17.03** | **+4.40** | — |
| load-wtd mean LMP | 38.23 | 39.47 | +1.25 | RT 32.30 |
| ⇒ C3a 2023 | +18.3 % | **+22.2 %** | worse | — |

**The mechanism is confirmed.** The decisive evidence is not the price level but
the water value itself. Upstate_West overnight modal price by month — the budget
dual — fell in **all twelve months** when the *only* changed input was hydro
deliverability:

| mon | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| keeper | 37.86 | 32.33 | 34.13 | 28.74 | 26.19 | 35.06 | 37.79 | 34.06 | 30.01 | 27.06 | 34.31 | 34.12 |
| nyiso-74 | 33.08 | 29.61 | 28.92 | 26.38 | 24.32 | 31.60 | 33.79 | 30.25 | 29.23 | 23.93 | 32.04 | 31.05 |
| Δ | −4.78 | −2.72 | −5.21 | −2.36 | −1.87 | −3.46 | −4.00 | −3.81 | −0.78 | −3.13 | −2.27 | −3.07 |

Mean −$3.1. A hydro-side constraint moved the overnight price in every month:
**§1–§3's identification of the trough's price-setter is established
experimentally, not just by inference.**

**Why the trough nevertheless barely moved (−$0.79).** The modal share collapses
with the ceiling on (Jan 72.4 % → 18.0 %, Mar 81.1 % → 29.0 %). Capping hydro
lowers the water value *and* removes hydro from the margin in the freed hours,
handing those hours back to thermal at a **higher** price. The two effects
nearly cancel on the load-weighted mean.

**Why the peak rose (+$3.61).** Intended and correct — the model was running
683 MW more hydro at the evening peak than the real system does. Removing that
exposes the thermal unit reality actually runs there.

**Verdict on the instrument, not the mechanism.** A p95 hourly ceiling *bounds*
the hoarding but leaves the monthly optimization intact: the LP still arbitrages
one budget across ~700 hours, just under a cap. The physically faithful
representation of a run-of-river fleet with hours-to-days of pondage is a
**shorter budget period** (daily / pondage-duration), not a ceiling on top of a
monthly budget. Pondage volume is a licensed physical parameter, so a
duration-limited budget regenerates forward and responds to changed conditions.
That is the named successor lane; it is a new mechanism and needs its own
charter and owner sign-off — and under rule 19 it must **replace or reconcile
with** `hydro_dispatch_envelope`, never stack on it.

**Rule-1 disposition.** `nyiso-74` is NOT promoted, and the keeper stays
`nyiso-72` — not because C3a got worse, but because a single-year scoping probe
is not a keeper candidate (rule 16) and because the instrument is known to be
the wrong one. This is explicitly **not** a rejection on the residual: the
mechanism improved hydro shape (r +0.079), moved the water value in every month,
and **expanded** the peak–trough spread by $4.40 — the first NYISO lever to do
so (the gas-commitment bridge *compressed* it by $0.63, and the cross-ISO
markdown family compresses by construction). Whoever takes the successor lane
should treat spread expansion as the signature to preserve.

**A consequence worth stating: the thermal question is reinstated, scoped.**
With hydro capped, more overnight hours become thermal-set and the trough still
does not fall. So the C3a-2023 overnight residual has **two** components — an
over-high water value in hydro-set hours (this finding) and an over-high thermal
offer in the rest. The prior session's low-load incremental-heat-rate lane is
therefore *not dead*; it is demoted from "the mechanism" to "the second of two",
and it now has a cleaner test bed (a run with hydro's hoarding bounded).

---

## 7. What this does NOT claim

* It does not claim the low-load incremental-heat-rate question is settled as an
  *offer-form* matter. The measured artifact
  `data/raw/reference/nyiso_campd_marginal_hr_summary.csv` does carry both bases
  (`avg_*_p50` and `marg_*_p50`), and the registered NYISO curve uses a **mixed**
  basis by design — `phys_committed = avg_committed_p50` (0.964 for CC_REGULAR)
  while `phys_econ_low/high = marg_*_p50` (0.784 / 0.925); `marg_committed_p50`
  is 0.632. That mixed basis is deliberate and documented (`scenarios.py`
  offer_curve_by_group docstring). It is identifiable from measured data and
  remains a live question for the *thermal* hours. It is simply not the C3a-2023
  overnight lever, because the overnight hours are not thermal-set.
* It does not claim hydro explains C3b/C3c.
* The 2025 hydro energy under-run (−3.0 TWh vs EIA-930, −3.20 vs the NYISO
  posting) is a **separate, still-open** budget-level defect (Lane C). This
  finding is about hydro's *hour placement*, not its monthly level.
