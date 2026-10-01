# FINDING — ERCOT-114 Task A: both quantity candidates are REFUTED, and the residual is a model-only seasonal term

**Date** 2026-07-26 · **ISO** ERCOT · **Years** 2023–2025 · **No LP** (rule 15 — reads the
committed keeper sidecars and raw measured data; nothing re-solved) ·
**Probe** `scripts/probes/ercot114_coal_quantity_drivers.py` ·
**Read** `results/calibration/ercot_netrev_margin/hourly/` (keeper
`2026-07-23-ercot100-netrev-margin-keeper`), `data/raw/campd-unit-level/TX_{2023,2024,2025}.parquet`,
`data/raw/ercot-thermal-dam-availability-site-hourly.parquet`,
`data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet`

ERCOT-113 established that the summer coal over-run is **quantity-side**: coal's availability
envelope is measured-pinned and correct, its seasonal movement is *upward*, and it sits
$46–67/MWh inframarginal so no plausible price correction changes its rank. The ERCOT-114 charter
enumerated the two quantity candidates that have a driver, a window and a forward story (rule 18).
**Both were measured before any mechanism was written. Both are refuted** — and the measurement
that refutes the second one relocates the defect precisely.

---

## 1. A1 — CSAPR ozone-season NOx allowance budget: **REFUTED** on both quantity and price

Texas coal is in CSAPR NOx Ozone Season **Group 2** (`CSOSG2`; the Good Neighbor Plan's move of
Texas to Group 3 was stayed, so Group 2 is operative). The statutory Texas trading budget is
**52,301 tons**, "2017 and thereafter" — 40 CFR 97.810, confirmed current on eCFR 2026-07-26 —
with a variability limit of 10,983 tons and therefore an assurance level of 63,284 tons
(40 CFR 97.825; variability is set at 21 % of the state budget for ozone-season NOx). EPA's
published state-budget workbook `budgets_ozoneseasonnox.xls` carries the same three numbers.

Measured Texas ozone-season (May 1 – Sep 30) NOx mass, all `CSOSG2` units, from CAMPD:

| year | state ozone tons | coal tons | coal share | **% of budget** | % of assurance | headroom |
|---|---|---|---|---|---|---|
| 2023 | 46,919 | 23,012 | 0.490 | **89.7 %** | 74.1 % | 5,382 t |
| 2024 | 42,981 | 20,452 | 0.476 | **82.2 %** | 67.9 % | 9,320 t |
| 2025 | 42,028 | 21,581 | 0.513 | **80.4 %** | 66.4 % | 10,273 t |

**Quantity: the cap never binds.** The state runs at 80–90 % of budget and 66–74 % of the assurance
level, in every year, with headroom growing. A slack constraint has a **zero shadow price** — a
mass-cap mechanism built on it would be provably inert in all three backcast years. Nothing to
build.

**Price: the channel is four hundred times too small.** The objective already carries
`nox_rate × nox_price`, so this is the exact channel a mechanism would use. At the measured coal NOx
rate and the last CSAPR Group 2 allowance prices EPA published (the program "started 2021 at $200
per ton and ended 2021 at $166 per ton", power-sector Progress Report market-activity series):

| year | coal NOx rate lb/MWh | adder @ $166/t | adder @ $200/t | **break-even price to close $46/MWh** | shortfall |
|---|---|---|---|---|---|
| 2023 | 1.147 | $0.095/MWh | $0.115/MWh | **$80,188/ton** | **401×** |
| 2024 | 1.171 | $0.097/MWh | $0.117/MWh | **$78,576/ton** | **393×** |
| 2025 | 1.225 | $0.102/MWh | $0.123/MWh | **$75,098/ton** | **375×** |

To reverse coal's merit position the allowance would have to trade at $75k–117k/ton. Even the
Group 3 price spike of 2022 (~$28,500/ton — a program Texas is *not* in) delivers only ~$16/MWh
against a $46–67/MWh gap. **A1 is dead on arrival and is closed in writing. Do not build it.**

This also confirms ERCOT-113's tempering read: the flat ozone-season NOx *rate* (ratios
0.964 / 0.940 / 0.957) was never evidence *for* the mechanism, and the budget test now shows there
is no output channel either.

---

## 2. A2 — coal fuel supply / delivery-rate limit: **REFUTED**

### 2a. The decisive test — real coal's price-response curve is season-invariant

Coal utilization of the *measured committed HSL envelope*, binned by **absolute actual RT price**
so summer and shoulder are directly comparable, model and actual inside the same bin against the
same envelope. Mean summer-minus-shoulder utilization lift across the eight matched price bands:

| year | bands | **actual** summer lift | **model** summer lift | excess | ratio |
|---|---|---|---|---|---|
| 2023 | 8 | **+8.74 pp** | **+28.00 pp** | +19.26 pp | 3.2× |
| 2024 | 8 | **+3.06 pp** | **+20.99 pp** | +17.93 pp | 6.9× |
| 2025 | 8 | **+0.58 pp** | **+20.45 pp** | +19.87 pp | 35.4× |

**Real ERCOT coal runs at essentially the same fraction of its envelope at a given price whether it
is July or March** (+0.6 to +8.7 pp, shrinking to nil by 2025). The model runs it **20–28 pp
harder in summer at the same price** — an excess that is remarkably stable at **≈19 pp in all three
years**.

This refutes A2 directly. A binding summer fuel or delivery budget would push real summer
utilization *below* shoulder at matched price. It does not: summer is at or slightly **above**
shoulder. And in the top summer price band real coal reaches **0.93 / 0.88 / 0.89** of committed
HSL — a fleet rationing fuel cannot buy its way to its envelope at any price, and this one does.

The within-season decile tables show the same thing from the other side: the summer gap is largest
in the *cheapest* hours (+18.5 to +24.3 pp in deciles 1–3) and closes to +1.9 to +3.7 pp in decile
10. The model does not over-run coal when coal is genuinely needed; it over-runs it when coal is
merely cheap.

### 2b. The direct driver — receipts track consumption, with a normal stock cycle

EIA-923 Schedule 5 monthly coal receipts against CAMPD monthly heat input. Coverage is partial and
this is stated plainly: only **3 of the ~10 ERCOT coal plants file market fuel receipts** — Fayette
(6179), San Miguel (6183), J K Spruce (7097). The mine-mouth lignite plants burn captive fuel and
file no Schedule 5 receipts, so they carry consumption with no receipt side and are excluded rather
than read as a fleet-wide shortfall.

Per-plant heat content is backed out by balancing receipts against consumption over the whole
2023–2025 window. The implied values validate the method — **17.15, 11.54 and 18.76 MMBtu/ton**,
correctly separating PRB sub-bituminous (~17–19) from Texas lignite (~11.5).

The covered fleet's receipts-over-consumption ratio in Jun–Sep runs **0.68–1.05**, with the
cumulative balance drawing down through summer and rebuilding every autumn — an ordinary seasonal
stockpile cycle, not a ceiling. Annual receipts track annual burn.

**Caveat, stated rather than buried:** monthly receipts are demand-following and therefore partly
endogenous, and true end-of-month stocks (EIA-923 Schedule 8) are not in the repo, so 2b on its own
could not have closed A2. It does not have to — 2a is fleet-wide, needs no fuel data, and is
decisive. Were anyone to reopen A2, a plant-level stocks series is the artifact that would settle
it, and a delivery cap fitted to observed receipts would in any case be pinning to a measured
outcome (rule 13), not an admissible input.

---

## 3. What the refutation relocates — the successor charter

Both candidates are closed, and the matched-price measurement names the defect far more sharply
than "the model over-runs coal in summer":

> **The model carries a ≈19 pp seasonal term in coal dispatch that the real market does not have.**
> At matched price and against the same measured envelope, real coal's utilization is
> season-invariant; the model's is not.

Two further facts constrain any successor:

* **The shoulder gap is negative.** The model *under*-runs coal at every shoulder price band
  (−1.9 to −9.5 pp). This is not a global "coal is too cheap" error — the sign flips by season, so
  a uniform offer-level change would fix one season by breaking the other.
* **Model price overshoot is not seasonal.** The model's load-weighted P1 price sits ~$7–9 above
  actual in the cheapest hours of *both* seasons, so price formation does not explain a
  summer-specific dispatch term.

Since utilization is already normalized by coal's measured envelope, and coal's own price-response
is not the seasonal actor, the seasonal term has to enter through **what coal is competing
against** — consistent with ERCOT-113's confirmed displacement (corr(dCoal, dGas) = −0.97 / −0.98 /
−0.95, the coal surplus *is* the gas deficit, month for month). The reading this probe supports for
ERCOT-115 is that the **asymmetry in how the two fleets get their availability** is the place to
look. Under rule 14 that asymmetry is exactly the shape of a defect — the accurate input on one
side and an estimate on the other, with the estimate free to absorb the difference.

> **Correction (2026-07-26, same session).** An earlier revision of this paragraph stated the
> asymmetry as "coal is pinned … while gas is not." **That is backwards for the bundle these
> numbers come from.** The measurements above are taken against the keeper
> `ercot_netrev_margin`, whose `run_config.json` carries
> `ercot_thermal_dam_availability_hourly=True` and `_plant=True` but **no
> `ercot_thermal_dam_availability_coal`** (default `False`). Its solve log pins exactly three
> classes — `CC_REGULAR`, `CT_PEAKER`, `ST_GAS` — and **no COAL line**. So in the keeper it is
> **gas that is pinned to the measured 60-Day DAM envelope, and coal that runs on the statistical
> availability model.** (The ERCOT-112 arms are the ones that arm `_coal`; ERCOT-113's decomposition
> read those bundles, which is where the inverted description came from.)

The corrected asymmetry points the same way but more sharply: **coal — the class that over-runs — is
the one whose availability is *not* measured-pinned, while the class it displaces is.** A
statistical coal availability model that is too generous in summer, competing against a gas fleet
held to its measured envelope, reproduces the observed signature directly.

The obvious candidate, `ercot_thermal_dam_availability_coal`, has already been solved full-span as
ERCOT-112 arm B — and it makes the raw fit **worse** (C1 fuel-mix 16/16 → 12/16, target grade
6 → 2). Per rule 14 that is a *discovered bug elsewhere*, not grounds to reject the accurate input;
what it means is that pinning coal cannot be adopted on its own. **Measure the coal envelope
against the same disclosure, and identify what the statistical model was silently compensating for,
before building anything** — the discipline that has now closed eight candidates across
ERCOT-111/112/113/114 without a line of mechanism code.

---

## 4. Rules observed

No mechanism was built and no parameter was tuned. Nothing was reverted or weakened to chase a
residual: `ercot_thermal_dam_availability_coal` and `coal_econ_marginal_hr_bound` are untouched
(rules 1, 13, 14); take-or-pay / the PRB sigmoid were not touched and the CAMPD marginal-HR artifact
was not re-derived, its source data being unchanged (rule 23). Every reference value carries a
primary-source citation in the probe (rule 5). No LP was run and no out-of-training year was
touched (rules 15, 22). Both refutations are recorded in writing so neither candidate is re-opened
without new data.
