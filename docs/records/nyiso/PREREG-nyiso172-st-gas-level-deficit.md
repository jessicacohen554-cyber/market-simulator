# PRE-REGISTRATION — nyiso-172: the ST_GAS level deficit

**Session:** nyiso-172 · **Date:** 2026-09-01 · **Keeper:**
`2026-08-30-nyiso-159-loss-surface` (NOT-YET on {C3a-2025 −11.5 %, C3c}).
**Registered BEFORE the probe was run.** Phase 0 is ZERO SOLVE.

## The object

Model vs committed benchmark `classFull`, 2025: **ST_GAS 9.7866 vs 13.7121 TWh
= −3.9255 TWh (−28.63 %)** — the largest absolute class error in the failing
year, negative in all twelve months, and already the most heavily floored
merchant class in NYISO (D-2: `reliability_floor` 16.70/22.67/18.43 % of class
energy plus `nyiso_gas_commitment_bridge` 0.82/1.46/1.21 %).

nyiso-170 §4 closed with: *"A successor who opens it needs a THIRD thing — an
identification of why the model's gas composition is wrong in a way that is NOT
a swap."* A pure LEVEL deficit in one class is that third thing. This
pre-registration fixes what would count as identifying it, and what would
refuse it, **before** the measurement.

## Instruments

Zero solve. Every series is a committed artifact or a raw measured record.

| instrument | source |
|---|---|
| model hourly MW by class | keeper `hourly/class_hourly_<year>.parquet`, pass **P1** |
| model hourly zonal price + demand | keeper `hourly/system_<year>.parquet`, pass **P1** |
| what already forces ST_GAS | keeper `legitimacy_diagnostics.json`, D-2 rows |
| measured hourly MW per unit | `data/raw/campd-unit-level/NY_<year>.parquet` |
| class construction | CAMPD `unitType` × EIA-860 CHP flag — the nyiso-169b/170/171 construction, unchanged |
| class volume reference | `frontend/data/backcast/bench/NYISO/<year>.json.gz` `classFull` |
| actual price | `data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet` (`da`, `rt`) |
| gas price | `data/raw/gas-prices/transco_z6_ny_daily.csv` (Transco Z6 NY) |
| model ST_GAS capacity | `data/raw/_processed-legacy/thermal_tranches_NYISO.csv` |

**Anchoring.** The nyiso-170 construction: one scalar
`anchor = benchmark_TWh / CAMPD_TWh` per class-year, applied to the measured
hourly series. It preserves the annual level error **exactly** and therefore
compares shape without pinning anything.

**Rule 13 `[R-MEASURED]`.** CAMPD enters ONLY as conduct identification. Nothing
is pinned to observed generation; no statistic is tuned to any residual.
**Rule 22 `[R-HOLDOUT]`.** 2023/2024/2025 only. NYISO holds no `complete` marker
(declared 2026-07-31, **withdrawn 2026-08-30**) and is absent from `final`; no
out-of-training year is read, solved, scored or registered, and no marker is
requested.

## Conditioning variable

`IMH(h) = actual_DA_price(h) / Transco_Z6_gas(h)` — the market's own implied
marginal heat rate, in MMBtu/MWh. It is **exogenous to the model** (no model
output enters it), which is what makes it admissible as a binning variable for
both series at once.

## Pre-registered gates

### S1 — rule 19 `[R-ONE-MECH]` attribution (phase 0c)

Enumerate every mechanism forcing or shaping ST_GAS from the committed D-2 rows.
**PASS** = the enumeration is complete and unambiguous, so any proposed change
can be stated as REPLACING or RECONCILING a named mechanism rather than
stacking on it. Reported, not gating.

### S2 — is the deficit PRICE-CONDITIONAL? (phase 0a) — **THE STOP CONDITION**

Bin hours by `IMH` decile. In each decile measure mean model ST_GAS MW, mean
anchored-measured MW, and the deficit. Two statistics:

* **T50** — the `IMH` at which each series first reaches 50 % of its own p95
  output, linearly interpolated across deciles. A class that "exits too readily
  as fuel rises" has its model turn-on threshold to the RIGHT of the market's.
* **profile spread** — `max − min` of the per-decile deficit, against the mean
  absolute deficit.

**PASS (price-conditional — a dropout object, proceed):** `model T50 > measured
T50` in **all three years**, AND profile spread ≥ 0.20 × mean |deficit| in all
three years.

**FAIL (flat — a capacity/availability object):** otherwise. On FAIL the finding
must **say so explicitly** and record that this is a different lane; no offer or
commitment lever may be proposed off a flat profile.

### S3 — CAPACITY or CONDUCT? (phase 0b)

Compare the model's ST_GAS available capacity against what the benchmark volume
requires and against the measured fleet's own output percentiles.

* required annual CF = `benchmark_TWh × 1e6 / (model_nameplate × 8760)`
* model realized CF, model max and p95 hourly MW
* measured fleet max, p95, and CAMPD-derived availability proxy

**INPUT DEFECT (stop):** the model's ST_GAS capacity cannot reach the benchmark
volume even at a physically attainable availability — then this is an input
defect, not an offer one, and no offer/commitment lever is admissible.

**CONDUCT:** capacity is sufficient and the class is simply not dispatched.

### S4 — start conduct, the `gas_st_startup_cost` grounding (the brief's named trap)

Measured, from CAMPD, for the ST_GAS population: per-unit start counts,
run-length distribution (median/mean/p90), and off-run lengths. Compared against
the model on the **class-aggregate on/off statistic only** — the one
direction-safe comparison available, because a class-aggregate start requires at
least one unit start and a class-aggregate zero implies every unit is off
(nyiso-171's portfolio-artifact caveat forbids inferring anything from a
non-zero fleet minimum, but not these two).

Also: does `ST_GAS_COMMITMENT_PARAMS` (min-run **24/48 h**, min-down **8/12 h**,
startup **$55/$75 per MW**) sit inside NYISO's measured distribution?

**ARM-SUPPORTIVE:** measured ST_GAS run lengths materially exceed the model's
class-aggregate run lengths, **and** the 24/48 h min-run constants sit inside
the measured NYISO distribution.
**REFUSE:** otherwise. Per the brief, arming because ST_GAS under-runs is
residual-driven and rule 1 `[R-STRUCT]` forbids it.

### S5 — the DIRECTION gate on `gas_st_startup_cost` (code-proven, ex ante)

`compute_monthly_markup` returns `startup / max(avg_run, 1.0) ≥ 0` and
`solve.py` forms `mc_bid = mc_base + markup`, P1-only (P0 run lengths, and hence
every injected `min_gen` floor, are unchanged).

**DIRECTION ADMISSIBLE:** the mechanism can raise ST_GAS output.
**DIRECTION REFUSES:** the mechanism can only weakly lower it, and therefore
cannot address a −28.63 % volume deficit. Sized by the markup ST_GAS would
actually carry.

S5 is decided on the code, so it is reported whatever S4 says; if S4 and S5
disagree, **S5 governs the volume claim** and S4 governs whether the underlying
physics is real.

### S6 — does the deficit track gas price WITHIN sample?

The brief's fact 3 is an annual pattern (+40.9/−6.0/−28.6 % against gas
2.54/2.19/3.52 $/MMBtu), n=3. Test it at monthly grain: regress the monthly
ST_GAS relative error on that month's mean gas price, pooled over all 36
training months and per year.

**SUPPORTED:** pooled slope < 0 and the per-year slopes carry the same sign in
all three years.
**NOT SUPPORTED:** otherwise — then the annual pattern is an n=3 coincidence and
must not be quoted as a mechanism.

## Stop condition

If **S2 FAILs** (flat profile) or **S3 returns INPUT DEFECT**, the lane stops at
phase 0 and reports the object as capacity/availability rather than conduct. No
parameter is touched and no solve is run in either case.

## What would make this session arm something

An arm requires **all** of: S2 PASS, S3 CONDUCT, and a mechanism that is
(a) grounded in a NYISO measurement, (b) directionally able to raise ST_GAS,
(c) a REPLACEMENT for or RECONCILIATION with a named S1 mechanism rather than a
stack on it, and (d) declared with kills and expected direction/size in C1
ST_GAS volume, D-1 diurnal profile and C3a-2025 before it is run. Absent all
four, the honest outcome is an adjudication with no solve — the nyiso-168/169/
170/171 precedent.
