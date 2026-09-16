# FINDING — nyiso-236: the offer anchor's grain is unidentified, and Object B is a slope/intercept pair

**Session** nyiso-236 · **Date** 2026-09-16 · **ZERO LP SPENT** (rule 32 `[R-SHARD]` (a): the
orchestrator never solves; everything below is read off the committed keeper bundle, the committed
input series and `data/raw/_validation-source/`).
**Keeper under examination** `2026-09-14-nyiso-235-gas-repair`, bundle
`results/calibration/nyiso235_gasrepair_span` — **UNCHANGED by this session**. No `ScenarioConfig`
field was added, moved or armed; no mechanism was tested, so no matrix cell moves (rule 28
`[R-MECH-MATRIX]` (b)).

> ## THE TWO RESULTS
>
> **1. OBJECT C (the annual-mean offer anchor) IS NOT SCREENED — STOPPED AT PHASE 0 ON
> IDENTIFICATION, NOT ON THE RESIDUAL.** The defect nyiso-235 named is real and is now located to
> the line. But the anchor's *grain* is not a measurement choice: it is the mechanism's own
> structural claim about markup fuel-elasticity, and in NYISO there is no instrument that can
> discriminate month from quarter from season from year. Choosing among them could only be done
> against the gates, which rule 1 `[R-STRUCT]` condition (c) refuses.
>
> **2. OBJECT B IS RE-MEASURED CORRECTLY FOR THE FIRST TIME, AND IT IS NOT OBJECT C.** The actual
> hourly NYISO RT LMP series **is on disk** and always was —
> `data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet`, 2018–2026, 8,760 h/yr. With both
> sides tail-stripped on the same hours, the model's entire year-to-year price bias resolves into
> **two numbers**: a gas-slope that is **14.0 % too shallow** and a fixed intercept that is
> **47.4 % too high**, crossing at **$5.00/MMBtu**. Both bootstrap CIs exclude zero.

---

## 1. G-DRIFT, RE-RUN AT THIS SESSION'S HEAD (rule 29 `[R-SCREEN]` (b))

Required because the handoff records that nyiso-235 inherited a stale "zero LIVE hunks" finding.
This session's head is `edd40943`; the keeper solved at `2ebc58df8e5d0425a0f35dbad1eeac11d039c0a3`.

| check | result |
|---|---|
| `moved_rows("NYISO")` | **`{}`** — zero |
| `surface_stamp("NYISO", keeper_cfg).fingerprint` at HEAD | **`bd2b4657f9b5df7e`** = the keeper's recorded `solve_surface.fingerprint` |
| solve-path diff `2ebc58df…HEAD` | **35 files, +2,500 / −19** |

Hunk classification — **every hunk INERT for NYISO**:

* SOCO registration (`zone_assignment.py` `_SOCO_STATE_ZONES` / `_soco_zone` / `_LARGEST_ZONE`,
  `iso_configs.py`, `scripts/lib/transmission_expansion/soco.py`) — another ISO's branch.
* NWPP onboarding (`eia930/*`, `renewables.py` set membership, `interchange/spec.py`,
  `capacity_market.py`) — another ISO's branch; NYISO is absent from every membership set touched.
* The **only** edit inside a code path NYISO executes is `_eia860_ba_zones`, and it is
  behaviour-identical for a non-SOCO ISO: `if oris is None or lat != lat or lon != lon: continue`
  became `if oris is None: continue` → `if iso == "SOCO": …` (not taken) → `if lat != lat or
  lon != lon: continue`. Same predicate, same order, one extra column read that changes no output.

**Rule 29(b) form 4 is VALID. The keeper's committed bundle is the control; no control solve was
spent, and none is owed.**

## 2. OBJECT C — LOCATED TO THE LINE

`src/market_sim/data/fuel/zonal_anchor.py:145`:

```python
return {zone: float(np.nanmean(prices[i])) for i, zone in enumerate(zone_names)}
```

`np.nanmean` over all 8,760 hours. The keeper carries `gas_offer_margin_zonal_anchor_vintage = True`
(nyiso-230), so the identification point is resolved per **(zone, solve-year)** — an **annual
scalar**. The offer adjustment is `mc[g,t] += offer_markup_hr[g] × (anchor − fuel_price[g,t])`
(`offer_curves.py:797`), where `fuel_prices` is the post-overlay, post-dual-fuel `(n_gen, T)` array.

**Phase-0 reconstruction verified against the keeper's own record**: rebuilding the anchor from the
keeper's recorded `scenario_config` reproduces its 2022 values exactly —
`Capital_Hudson 8.656486`, `Upstate_West 5.586486`, `NYC 6.876486`.

### 2.1 The within-year index error is LARGER than the between-year one nyiso-230 closed

Delivered gas $/MMBtu, Capital_Hudson (every zone carries the same spread; the zonal basis is a
level shift):

| year | annual anchor | monthly min … max | **within-year spread** | mean abs. dev. from annual anchor |
|---|---:|---|---:|---:|
| 2022 | 8.656 | 6.239 … 12.745 | **6.506** | 1.452 |
| 2023 | 3.337 | 2.613 … 5.095 | **2.482** | 0.589 |
| 2024 | 2.822 | 2.170 … 6.060 | **3.890** | 0.799 |
| 2025 | 5.463 | 3.240 … 14.095 | **10.855** | 2.208 |

The **between-year** spread nyiso-230 was promoted to close is `8.656 − 2.822 = 5.834`. The
within-year spread exceeds it in 2022 and is **1.86×** it in 2025. So by nyiso-230's own argument —
"the further a year's delivered gas sits from the anchor the further the offer departs from the band
multiplier the ISO was calibrated with" — the residual index error is larger than the one that was
fixed. **The defect is real.**

### 2.2 Why it is still STOPPED, and the stop is structural rather than residual-driven

**(a) The grain is the mechanism's core claim, not a measurement detail.** Write the markup as
`A × fuel(t) + B`. The rejected multiplicative form is `A = markup_hr, B = 0`; the
`gas_offer_net_revenue_margin` reform is `A = 0, B = markup_hr × anchor`. Making the anchor
time-varying produces **neither** — it makes `B` a step function, i.e. a *frequency* split of markup
fuel-elasticity (elastic below 1/grain, inelastic above it) with no market referent. Taken to its
limit the same extrapolation argument gives `anchor = fuel(t)`, which is the pure multiplicative
form **rejected on measured evidence** by the 2022 NEISO validation rotation (bulk 40–80 overshoot
+57.7 $/MWh at ~2.9× anchor gas; neiso-45/46/47). An argument whose limit destroys the mechanism
cannot license an arbitrary step along it.

**(b) The year grain has a forced justification the finer grains lack.** In a **forecast** year there
is no training window, so the anchor must resolve on that year's own trajectory or be undefined —
rule 13 `[R-MEASURED]`'s forward test *forces* the year index. Nothing forces month, quarter or
NYISO capability period. This is what makes nyiso-230 admissible and a finer grain optional.

**(c) The markup is a FITTED quantity, so its fuel-elasticity is unidentified by construction.**
`markup_hr = (mult − phys) × HR_base`, where `phys_*` is measured (CAMPD `avg_committed_p50`, the
capacity-weighted median *average* heat rate — so it already carries no-load burn) but `mult` is the
registered `offer_curve_by_group` band multiplier, i.e. the **authorized price-tuning channel** of
rule 1's carve-out. Asking "over what horizon is this quantity's dollar level fixed" is asking to
refine the units of a fitted number.

**(d) NYISO has no instrument.** NYISO publishes no 60-Day-DAM equivalent (the same gap that forced
the WP-3 loading-when-on reconstruction for the bridge min-load fractions), and there is **no
`data/raw/nyiso-energy-offers` corpus**; the PJM / MISO / CAISO offer corpora on disk are
README-only under the corpus conversion, and a verdict from them would not transfer anyway
(rule 25 `[R-ISO-SCOPE]`). With no offer book, month vs quarter vs season could be discriminated
**only** by what each does to the gates — the fitted-mechanism selection rule 1 condition (c)
forbids.

**This is a `G` (governance-refused) disposition on identification, not an `R`.** It is not a
statement that a finer anchor would fail; it is a statement that this lane cannot legitimately
choose one. **Re-open condition:** a published NYISO unit-level energy-offer book, or any measured
NYISO conduct series from which the markup's fuel-elasticity can be identified directly.

## 3. OBJECT B — THE DEAD END WAS A WRONG-FILE PROBLEM

nyiso-235 recorded that Object B could not be re-measured because
`frontend/data/backcast/tail/actual_tail.json` carries only tail **hour counts** (`rt_gt`). That is
true of that file. **The actual hourly series is a different file and it is committed:**

```
data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet   # year, hour, rt, da — 2018-2026, 8760 h/yr
```

It is the source `scripts/data/derive_actual_amplitude.py` already reads. **Object B needs no new
data and no solve.**

### 3.1 Basis reconciliation — the model side reproduces the scorer exactly

| year | scorer actual | mine | scorer model | mine |
|---|---:|---:|---:|---:|
| 2022 | 81.12 | 80.37 | 72.59 | **72.59** |
| 2023 | 32.25 | 32.05 | 31.68 | **31.68** |
| 2024 | 38.12 | 38.13 | 38.07 | **38.07** |
| 2025 | 66.43 | 66.34 | 60.32 | **60.32** |

The model side is identical in all four years. The actual side differs by 0.03–0.9 % because this
measurement load-weights the hub RT series with the **model's** zonal load; the scorer uses its own
weighting. The gap is far smaller than any effect below and does not move a conclusion.

### 3.2 Tail-stripping the SAME hours from BOTH sides

Top 1 % of hours **by actual price**, removed from model and actual alike:

| year | full-year bias | tail threshold | **non-tail bias** | tail's share of the miss |
|---|---:|---:|---:|---:|
| 2022 | −9.67 % | $322 | **−3.57 %** | 6.10 pp |
| 2023 | −1.14 % | $119 | **+5.93 %** | 7.07 pp |
| 2024 | −0.17 % | $139 | **+5.85 %** | 6.02 pp |
| 2025 | −9.07 % | $223 | **−2.18 %** | 6.89 pp |

Object B's original framing is **confirmed in direction**: stripping the tail from both sides leaves
a **9.50 pp** spread (−3.57 … +5.93) that the tail does not explain, and two years flip to
**over**-priced. nyiso-235's warning is also confirmed — stripping only the model's tail against the
full-year actual gives the opposite sign and is a different measurement.

### 3.3 The whole tilt is a SLOPE and an INTERCEPT

Regressing non-tail load-weighted price on that period's delivered gas, **48 month-points** pooled
over 2022–2025 (gas range $2.17–$14.09/MMBtu):

| | slope ($/MWh per $/MMBtu) | intercept ($/MWh) | r |
|---|---:|---:|---:|
| **actual**, non-tail | **+7.481** | **+11.05** | +0.900 |
| **model**, non-tail | **+6.432** | **+16.29** | +0.888 |
| **gap** | **−1.049 (−14.0 %)** | **+5.239 (+47.4 %)** | |

**Bootstrap 95 % CI (4,000 resamples): slope gap [−1.506, −0.500], intercept gap [+3.18, +6.91] —
both exclude zero.** The two errors cross at **$5.00/MMBtu**, so the model over-prices below that gas
level and under-prices above it; that crossover is what produces the year-to-year sign flips, and
`r(non-tail bias, annual gas) = −0.916` reproduces the handoff's −0.92 … −0.99.

The annual-resolution fit (n = 4) agrees: slope 6.708 vs 7.550, crossover $5.02. **The decomposition
is stable across resolutions.**

Reading, stated as inference rather than measurement: the slope is the **effective marginal heat
rate of the price-setting stack**, so the model's price-setting unit is ~14 % too efficient; the
intercept is the non-fuel component of price, and the model carries **$5.24/MWh more of it** than the
market. Caveats owed: the actual is a **hub** series while the model side is a five-zone load-weighted
average, so inter-zonal congestion sits in the intercept; and this is a diagnosis derived from
prices, so it **identifies a defect but cannot set a parameter** — any repair must come from measured
unit data (rule 13 `[R-MEASURED]`).

## 4. OBJECT B IS **NOT** OBJECT C — MEASURED PRE-SOLVE

The handoff asked whether they are the same object. They are not, and the test is zero-LP.

A month-grain anchor changes the load-weighted annual price by `markup_hr × (gas_load_weighted −
gas_annual)`, because within-year redistribution only survives load-weighting to the extent gas and
load are correlated. Using `markup_hr = 2.691` (nyiso-230's marginal-weighted value) and the keeper's
own hourly zonal load:

| year | annual anchor | load-weighted gas | diff | **implied Δ load-weighted price** |
|---|---:|---:|---:|---:|
| 2022 | 8.656 | 8.764 | +0.108 | **+0.290** |
| 2023 | 3.337 | 3.338 | +0.001 | **+0.003** |
| 2024 | 2.822 | 2.846 | +0.024 | **+0.064** |
| 2025 | 5.463 | 5.594 | +0.131 | **+0.353** |

Regressed on gas level that is a slope contribution of **+0.049 $/MWh per $/MMBtu** against a
measured deficit of **−1.049**: a month-grain anchor supplies **4.7 %** of it. The anchor grain moves
prices *within* the year — Dec-2022 swings of ±$23/MWh on the CT_PEAKER peak band — while leaving the
annual slope essentially untouched, because NYISO's gas–load correlation contributes at most
$0.13/MMBtu of load-weighting uplift.

**So Object C cannot be Object B's cause, and fixing Object C would not close Object B.** Note this
is reported as a *separation* result, not as grounds for the §2.2 stop: rule 1 `[R-STRUCT]` forbids
judging a structural mechanism by the residual, and the stop above rests on identification alone.

## 5. WHAT THIS HANDS FORWARD

1. **The successor to Object B is a MARGINAL-UNIT question, not an offer-markup one.** `phys_*` is
   the measured *average* heat rate over committed hours, so it already carries no-load fuel; the
   markup sits above full physical burn and has no physical reason to scale with gas. The fixed-$
   form is therefore structurally right for that residual, and the −14 % slope gap points instead at
   **which unit is marginal**. The handoff's item 4 is the visible end of the same chain: model
   CT_PEAKER runs 2.449 TWh against 2.687 actual in 2022 and drifts further away in all four years,
   and its share of gas-family energy tracks the gas level (3.91 % / 0.41 % / 0.45 % / 1.08 % at
   $8.66 / $3.34 / $2.82 / $5.46). Too few CT-marginal hours is the leading hypothesis for a
   price-setting stack that is too efficient. **Not tested here.**
2. **`gas_offer_margin_anchor_vintage` (cell `U`) should stay `U`.** It is mutually exclusive with
   the zonal vintage flag the keeper carries, and §2.2 applies to it identically.
3. **Nothing about the keeper changes.** Determination, gates, DOF ledger and matrix cells all stand
   exactly as nyiso-235 left them.

## 6. REPRODUCTION (all zero-LP, from a `--profile nyiso` hydration)

```
python3 -m pip install --ignore-installed PyYAML -r requirements.txt
python3 scripts/probes/nyiso236_anchor_grain_phase0.py --out /tmp/a.json   # §2.1 + §4
python3 scripts/probes/nyiso236_gas_slope_phase0.py --anchors /tmp/a.json  # §3.2 + §3.3
```

Both read only the committed keeper bundle, the committed `scenario_config`, and
`data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet`. Neither builds a fleet or touches an
LP.
