# PRECOMMIT — SPP-72, card R-bf: is the model's own load tight in the hours the market priced?

**Pushed BEFORE any tightness number is read.** Base `aaaaeb61aeb6353d5c531ea2605c0a46d0e27e82`.
Lane branch `claude/spp-demand-measurement-7qf5w9`. **Zero LP** — a measurement over committed
sidecars and raw inputs; no shard is launched (rule 32(a) is met trivially).

Charter: `docs/RESULT-xiso-stack-climb-attribution-2026-09-22.md` §10, lever (c).

---

## 1. Phase 0, step 1 — the four failing rows, re-verified at base

`scripts/calibration_verdict.py --run-id 2026-09-22-spp-71-rung-ensemble` → **NOT-YET**:
C3a 2020 **+17.3 %**; C3b 2020 / 2021 / 2022 NRMSE **0.267 / 0.243 / 0.208**; C3c ledgered
(2019 0 h vs 47, 2020 0 h vs 23, 2022 4 h vs 99, >$200). Matches the brief.

## 2. What the "model demand" object is — established from code before any number

The object measured is **the LP's dispatch demand**, the `demand` column of the keeper/rung's
committed `hourly/system_<year>.parquet` summed over `SPP-North` + `SPP-South`. It is **not** the
capacity screen's peak: every leg is `mode="backcast"`, `hindcast=False`, and
`capacity_screen_peak_measured_hindcast` reads `False` in every `run_config_<year>.json` (it is
coerced off outside hindcast), so the screen peak is not an object in these runs.

How the LP builds it (rule 19 `[R-ONE-MECH]` enumeration — everything that sets SPP demand today):

| step | code | effect |
|---|---|---|
| source | `data/eia930/demand.py:573-610` `_load_spp_hourly_demand` | **same calendar year's** EIA-930 SWPP `Demand` from `data/raw/eia-930-hourly/SWPP hourly.parquet`; spike/dropout screens |
| clock | `data/eia930/frames.py:278-337` | fixed CST (UTC−6); index 0 = Jan 1 00:00 CST; **local Feb 29 dropped** |
| net exports | `demand.py:1183-1192`, `model/interchange/envelopes.py:1771-1794` | **+ measured SWPP `Total interchange`** (export-positive), same frame |
| zonal split | `demand.py:1210-1220`, `curate_zonal_shares.py:580-663` | SPP-11 sub-BA hourly shares (static 0.5125/0.4875 only if absent) |
| must-run | `run_calibration.py:3078-3082`, `run_calibration_full.py:2426-2485` | **− biomass/OTHER**, EIA-923 annual energy shaped flat within month |
| losses / scaling | `backcast_config.py:1364` | `td_loss_factor = 0`; no energy/peak scaling; `_scale_demand` is never reached in backcast |

So the LP's array differs from measured load by exactly three terms: **+ net exports, − flat
must-run, and the clock.** No weather-year shape enters (`weather_year = year` on every leg).

## 3. THE TEST — fixed here

**Hours.** For each year Y ∈ 2019–2025, `H_Y` = the **88 hours** (top 1 % of 8,760) with the
highest **measured RT price** `rt` in `data/raw/_validation-source/actual_lmp_hourly_SPP.parquet`
(two-hub mean = the C3c benchmark, SPP-29 §1). Selection is on the market's price, **never** on
the model's output. Ties broken by index order.

**Statistic — percentile-within-own-year, NOT absolute MW. Why:** the question is whether the
model's hours are as *tight relative to its own year* as reality's. The model's array is a
different object from measured load by construction (it carries net exports and nets must-run),
so an absolute-MW difference would mostly measure that accounting offset rather than tightness.
Rank is invariant to such an offset and asks only about shape in the hours that matter.

- `p_mod(h)` = percentile rank (0–100) of model system demand at h within its own 8,760.
- `p_meas(h)` = percentile rank of **measured EIA-930 SWPP load** at h within its own 8,760,
  read from an **independent** file, `data/raw/SWPP_region.parquet` (`type == "D"`, UTC
  `period`), aligned onto the model clock by my own code, not the loader's. That independence
  makes the alignment check (§4) non-circular.
- **PRIMARY:** `Δ_Y = median_{h∈H_Y} p_meas(h) − median_{h∈H_Y} p_mod(h)`, in percentile points.

**Verdict per year, fixed now:**
- **EXONERATED:** |Δ_Y| ≤ 5 pts.
- **SHAVED (demand indicted):** Δ_Y > +10 pts (model less tight than reality in the market's hours).
- **Inconclusive:** otherwise (includes Δ_Y < −10, i.e. model *tighter* than reality).

**Lane verdict:** demand is **EXONERATED** as a cause of the rung's price-shape failures iff
2020, 2021 and 2022 (the years carrying the live C3a/C3b rows) are each EXONERATED. 2019 and
2023–2025 are reported with the same rule, not gating.

**Descriptive only (not a gate), declared now so it cannot be chosen later:**
1. `median_{H} p_meas` itself — whether the market's top-price hours are high-*load* hours at all.
   Below 90 means the tail is not predominantly a load event.
2. **Decomposition of any gap** into the three terms of §2: percentile of (measured load +
   measured net interchange) at H, and of the LP array with must-run added back.
3. Same statistics on the **top-10 %** (876 h) as a robustness read.

## 4. Trap (e) — the alignment check, fixed now

`SWPP_region.parquet` `period` is treated as **hour-ending UTC** (EIA API convention), so hour-
beginning UTC = `period − 1 h`; model index k ↔ hour beginning `Y-01-01 06:00 UTC + k h`, with
the 24 CST-Feb-29 hours removed in leap years. **Verified before any result is quoted** by:
(a) a lag scan, −3…+3 h, of corr(model demand, measured load) computed **separately for each
half-year** — the argmax must be lag 0 in both halves of **2020 and 2024** (a leap-day error
shows as ±24 h in H2 only; a DST error as ±1 h in one season); (b) the annual measured peak hour
must be the model's own peak hour or within 1 h.

Known benchmark seam (from code, `build_spp_lmp_reference.py:396-449`): the price index drops
**GMT** Feb 29 before the −6 h shift, the demand drops **CST** Feb 29, so in **2024 model hours
1410–1415** price and demand sit 24 h apart. I will report whether any of those six hours is in
`H_2024`; if one is, it is excluded from the 2024 statistic and the exclusion stated.

## 5. Predictions (scored in the RESULT, honestly)

- P1: every year EXONERATED, |Δ| ≤ 3 pts — because the LP array *is* the measured series plus
  two smooth terms. **Confidence moderate**: net exports are not smooth and SPP may import in its
  tight hours, which would shave the LP array relative to load.
- P2: alignment lag = 0 in both halves of every year.
- P3: `median_H p_meas` falls between 75 and 95 — a real part of SPP's price tail is not a load
  event (wind lulls, congestion, the five-minute RT wedge SPP-29 identified).
- P4: no 2024 benchmark-seam hour falls in `H_2024`.

## 6. What this lane will NOT do

No offer-curve lever (xiso: refused by construction). No curtailment channel (SPP-71 §0). No
new `ScenarioConfig` field unless a SHAVED year and a measured, forward-reproducible cause both
appear — and then only proposed, not armed, in this session. Keeper 15 (2023–2025) untouched.
