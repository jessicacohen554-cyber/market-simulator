# DIAGNOSIS — miso-152 addendum: MISO's C3a miss is a SUMMER-PEAK failure, not a uniform level offset. The model forms no summer peak, and its price barely responds to load.

**Session** miso-152 (addendum, after charter B closed) · **ISO** MISO ·
**Keeper** `2026-08-09-miso-148-basis-aware` (`miso148_basis_B`), **UNCHANGED** ·
**Date** 2026-08-11 · **Status** DESCRIPTIVE localization from **committed
artifacts only** — no solve, no run, no fleet build, no holdout spend
(2023/2025 training years). **No verdict is taken from it and no mechanism is
proposed here**; it exists so the next session does not re-derive it
(DO-NOT-REDO discipline).

**Method.** Model = `hourly/system_<year>.parquet` P1, the six carry zones
(`MISO-East/Illinois/Indiana/Plains/South/West`; the two `MISO_external*` import
nodes excluded), simple cross-zone mean. Actual = `frontend/data/backcast/bench/
MISO/<year>.json.gz` → `bench.avgLMP` (`rt`, `rt_mon`, `rt_lw`).

---

## 1. The annual number is not the shape

Model vs actual RT mean: **2023 $31.71 vs $31.79 (−0.3 %)**, **2025 $37.19 vs
$42.85 (−13.2 %)**. (Load-weighted: 2023 −0.1 %, 2025 −12.0 %. The registered
C3a −1.98 / −8.03 / −15.58 % is the scorer's own zonal construction; this
addendum's simple-mean reproduces its **sign, magnitude and year ordering**, and
is used only to localize.)

**Monthly miss, model vs actual RT (%):**

| year | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2023 | −2.5 | +18.0 | +4.5 | −1.9 | −7.1 | +2.0 | −4.4 | −4.4 | −4.5 | −9.3 | −0.6 | +16.8 |
| **2025** | −18.3 | −7.0 | −5.9 | −7.6 | **+11.9** | **−27.9** | **−30.9** | −8.4 | −19.8 | −7.4 | −8.1 | −11.6 |

2023 is flat and two-sided. **2025 fails in JUNE and JULY**: actual $51.3 / $55.4
against model $37.0 / $38.3 — a **$14–17/MWh** hole in the two most expensive
months of the year.

**Concentration.** June+July are **17 % of hours** and carry **46 % of the
annual mean gap** ($2.63 of $5.66/MWh).

---

## 2. The model's summer tail is thinner than its own winter tail

Model price distribution, 2025 ($/MWh):

| window | p10 | p25 | p50 | p75 | p90 | p95 | p99 | max |
|---|---|---|---|---|---|---|---|---|
| Jun+Jul | 31.0 | 33.2 | 36.7 | 41.6 | 46.1 | 47.6 | **59.1** | **75.1** |
| rest of year | 29.9 | 32.2 | 35.7 | 39.6 | 45.0 | 50.5 | **71.4** | **100.8** |

The model's summer p99 and max sit **BELOW** its own rest-of-year p99 and max,
and its summer median is **$1.0** above the rest of the year where reality's is
roughly **$15** above. **The model does not form a summer peak at all.**

**This is NOT the C3c scarcity tail.** C3c is about hours > $200 (model 0 vs
actual 88 in 2025) and is ledgered/frontier-designated. What §1–§2 measure is
the **whole summer distribution sitting at winter levels** — a mean-level defect
that the C3c ledger does not cover and does not excuse.

---

## 3. Demand is RIGHT; the supply stack is FLAT

The obvious first suspect is eliminated:

* Model demand peaks in **July** (annual max **118.7 GW**), monthly means
  Jun/Jul/Aug **82.1 / 90.5 / 84.2 GW** against a ~76 GW annual mean.
* The **top-200 model demand hours are 100 % summer** (Jun 36 / Jul 102 /
  Aug 62).

So the seasonal load shape is correct. What fails is the **price response to
it**:

* Model **price-vs-demand slope $0.35/MWh per GW** (Jun+Jul $0.37, rest $0.42).
* At the top-200 demand hours — **110.4 GW**, ~34 GW above the annual mean —
  the model prices only **$46.70**, against an annual model mean of $37.19.

Going from ~76 GW to 119 GW moves the model roughly **$15/MWh**. That is the
defect in one number: **too much capacity remains available too cheaply at the
top of MISO's summer load**.

---

## 4. Named candidate causes — NONE tested, NONE endorsed

Listed only so the next session's PREREG can adjudicate rather than rediscover.
No prior is attached to any of them here.

1. **Summer availability / outages.** MISO's outage extract is **un-re-tuned
   (X_cc = 0.240)** and is flagged as needing a cross-ISO charter. §3 gives that
   flag a MISO-specific, quantified summer cost for the first time.
2. **Summer capacity basis.** The keeper's own delta is
   `summer_derate_basis_aware`, which *removed* a double-counted summer derate.
   Whether the net summer capability it leaves is right at PEAK (as opposed to
   on average) is not established by miso-141/148, which measured the basis, not
   the peak-hour cushion.
3. **The across-unit dispersion object** (miso-151 G-5): the real book's
   steepness comes from WHICH unit is marginal, dispersion the model collapses.
   Still an **owner decision**, not chartered.
4. **Reserve co-optimization not binding in summer.** Directly checkable from
   the committed `hourly/reserve_family_<year>.parquet`, the only artifact in
   which a locational family's binding is observable.
5. **Imports at peak.** `docs/multi-iso/miso-import-starvation-rootcause-2026-07.md`
   reports the model UNDER-importing, i.e. the wrong sign to cause this — worth
   confirming at peak hours specifically before dismissing.

**Interpretive caution (rule 1).** §3's $0.35/GW is a REALIZED price-vs-load
slope; miso-145's $73.4591/GW wall is an OFFER slope on the fleet-cumulative
supply curve. They are different objects measured on different axes — the
resemblance is suggestive, **not** evidence, and must not be quoted as a
matched pair.
