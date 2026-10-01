# FINDING neiso-103 — NEISO's 2020 validation rung: the inputs are at parity, and the `NOT-YET` is a denominator effect

**Session.** neiso-103, NEISO lane. Branch `claude/neiso-2020-input-audit-j0gyum`, cut from
`origin/main` at **`1aab49a0`** (fetched in-session, clean tree). 2026-09-06.
**DATA PROFILE: code** (the `data/raw` subtrees this audit reads were already materialised;
no widening was needed).

**PHASE 0 ONLY. ZERO LP MINUTES SPENT.** No solve, no score of a new year, no registration, no
keeper change, no `ScenarioConfig` default moved, no mechanism tested — therefore **no
mechanism-matrix verdict moves** (neiso-102 / pjm-166 / pjm-167 precedent: refuting an object or
repairing a record moves no cell). Every number below is read from committed artifacts or from
calling committed loaders. The 2020 and 2021 rungs were **already spent and registered** by
`2026-09-05-neiso-2020-2021-touchpoints`; nothing here re-spends them.

---

## 0. Headline

The lane asked one question: **are NEISO's 2020 inputs as prepared as 2021's and 2022's?**

**They are. On every input family the keeper recipe consumes, 2020 is at parity with the tuned
years or better.** The census below is 24 families wide; not one is short in 2020 in a way
2021 and 2022 are not equally short.

**And the rung's `NOT-YET` does not mean what the ladder makes it look like.** C3a is a pure
±10 % *relative* band (`score_price_mean` → `err = _pct(model, actual)`;
`PRICE_MEAN_TOL = 0.10`), with no absolute-dollar floor. On absolute error the two rungs rank
the other way round:

| year | tier | model $/MWh | actual RT (lw) | **abs err** | rel err | C3a |
|---|---|---:|---:|---:|---:|---|
| **2020** | touchpoint | 28.59 | 25.14 | **+3.45** | **+13.7 %** | **FAIL** |
| **2021** | touchpoint | 52.11 | 47.77 | **+4.34** | +9.1 % | PASS |
| 2022 | touchpoint | 90.60 | 91.15 | −0.55 | −0.6 % | PASS |
| 2023 | keeper | 39.29 | 38.10 | +1.19 | +3.1 % | PASS |
| 2024 | keeper | 44.04 | 41.68 | +2.36 | +5.7 % | PASS |
| 2025 | keeper | 71.39 | 70.23 | +1.16 | +1.7 % | PASS |

**The year that FAILS is closer to its actual, in dollars, than the year that PASSES.** The
split is the denominator and nothing else — 2020 is the cheapest year in the record ($25.14
load-weighted RT, against $38–91 everywhere else):

- 2020's own +$3.45 error **PASSES at all five other years' price levels** (+7.2 % at 2021,
  +9.1 % at 2023, +8.3 % at 2024, +4.9 % at 2025, +3.8 % at 2022).
- 2021's +$4.34 error **FAILS at 2020's price level** (+17.3 %).
- Swap the two years' price levels and the two verdicts swap.

2020 misses the band by **$0.94/MWh**: it needs ≤ $2.51 absolute to clear ±10 % and carries
$3.45.

**This does not overturn the score.** The rung is correctly `NOT-YET` — the band *is* the
certification claim (`calibration_verdict.py` §"for those the band IS the certification claim —
C3a mean LMP most of all"), and a model 13.7 % high on price is 13.7 % high. What the audit
retires is a specific **inference**: that 2020 is worse-prepared, or worse-modelled, than the
rungs that pass. It is neither.

**One methodological catch, recorded because it nearly became a finding.** A standalone call of
`load_renewable_profiles('NEISO', 2020, …)` raises `ValueError: No EIA-930 data for ISO 'NEISO'
in year 2020`, and `eia_generation_profiles.parquet` really does hold zero rows before 2021 for
every ISO. That looked like a hard 2020 gap. **It is a harness artifact** — the negative control
(§5) shows the identical raise for **ERCOT 2020**, an approved weather-pool year, and shows
ERCOT 2023 returning the hardcoded `RENEWABLE_INSTALLED_MW` fallback (42,000/38,000 MW) rather
than measured capacity. The real solve's committed 2020 output matches measured EIA-930 to
**0.3 %** on wind, solar and nuclear. Nothing was written down until the control ran.

---

## 1. The census — every keeper-consumed input family, 2020 against the tuned years

Keeper recipe: `2026-08-17-neiso-99-joint-p1`, replayed frozen on 2020/2021 by
`2026-09-05-neiso-2020-2021-touchpoints` (bundle `results/calibration/neiso_tp2021_2020_k99`,
solved at `6619fb4a`). Flags read from that bundle's `run_config.json`.

Grades follow the equivalency register's own scale: **EQUIVALENT** (same source + grain +
recipe) / **DEGRADED** / **MISSING**. The column that decides the lane's question is the last
one — **discriminating?** — because 2020 and 2021 were solved in **one bundle, one recipe, one
HEAD**, and diverge in verdict. An input equally degraded in both cannot explain the split.

| # | input family | 2020 | 2021 | 2022 | 2023–25 | grade | discriminating? |
|---|---|---|---|---|---|---|---|
| 1 | Driver demand (`_load_neiso_hourly_demand`, first precedence) | 8760 h | 8760 h | 8760 h | 8760 h | EQUIVALENT | no |
| 2 | `eia_demand_profiles.parquet` NEISO rows | 0 | 8760 | 8760 | 8760 | **INERT** — fallback never reached (§2) | no |
| 3 | Measured net interchange (EIA-930) | 8760 h, −2,648 MW avg | 8760 h, −2,119 | 8760 h | 8760 h | EQUIVALENT | no |
| 4 | CAMPD unit-level, 6 states | all present | all | all | all | EQUIVALENT | no |
| 5 | Unit-outage windows | 401 | 373 | 321 | 338/289/260 | EQUIVALENT (declining fleet) | no |
| 6 | Layup windows | 150 | 209 | 161 | 104/153/187 | EQUIVALENT | no |
| 7 | e923 outage fallback | 3 | 1 | 3 | 2/2/2 | EQUIVALENT | no |
| 8 | Gas hub basis, **monthly** | 12/12 measured | 12/12 | 12/12 | 12/12 | EQUIVALENT | no |
| 9 | Gas hub basis, **daily** (Algonquin) | 45 prints | 94 | 62 | 44/49/30 | EQUIVALENT (in family) | no |
| 10 | Henry Hub daily | 251 prints | 251 | 250 | 249/251/247 | EQUIVALENT | no |
| 11 | Gas anchor `gas_price_override` | 2.03 | 3.72 | — | — | EQUIVALENT (EIA HH annual avg) | no |
| 12 | F923 delivered fuel cost | **50 rows** | 31 | 31 | 27/27/32 | **RICHER than in-sample** | no |
| 13 | `plant_emission_rates_v2` (NEISO) | **189 rows** | 187 | 179 | 174/162/156 | **RICHER** | no |
| 14 | Parasitic factors (NEISO plants) | **100 %** | 100 % | 100 % | 99/99/100 % | EQUIVALENT+ | no |
| 15 | `fossil_co2_rates` | present | present | present | present | EQUIVALENT | no |
| 16 | `eia860_chp_by_year` | present | present | present | present | EQUIVALENT | no |
| 17 | Nuclear availability (daily) | 3 reactors × 366 d | 3 × 365 | 3 × 365 | 3 × 365/366/365 | EQUIVALENT | no |
| 18 | `NUCLEAR_MONTHLY_CF_BY_YEAR` | real per-year (Apr 0.43, Oct 0.64) | real | real | real | EQUIVALENT | no |
| 19 | Zone temp / load-weighted temp | 1464 / 366 | 1460 / 365 | 1460 / 365 | leap-aware | EQUIVALENT | no |
| 20 | Renewable-capacity CSV | 120 rows | 120 | 120 | 120 | EQUIVALENT | no |
| 21 | Renewables **as served** (vs measured EIA-930) | wind −0.3 %, solar −0.3 %, nuclear −0.2 % | exact | — | — | EQUIVALENT (§5) | no |
| 22 | Import/export tranches | present | present | present | present | **INERT** (`priced_interchange=false`) | no |
| 23 | Fleet statics (year-agnostic bins/tranches) | covers **91.58 %** of CAMPD gen | 93.80 % | **91.72 %** | 94.8/95.5/97.1 % | DEGRADED, uniform | **no — see §3** |
| 24 | Winter-fuel-security figures | static by design | static | static | static | DEGRADED (accepted) | no |

Out of scope by construction: NEISO-AS measured hourly reserve requirements are absent in
**every** year and are read only by the non-keeper `neiso57_dynamic_rr` limb.

Bench / scoring side, for completeness: `actual_lmp_hourly_NEISO.parquet` carries a full 8760
for **every** year 2019–2025 (2020 RT $23.39 equal-hour / $25.14 load-weighted);
`actual_tail.json` carries NEISO 2020–2025; `calibration_reference.json` carries `isos.NEISO`
2019–2025. All EQUIVALENT for 2020.

---

## 2. The one gap that looks real and is inert

`eia_demand_profiles.parquet` holds **zero NEISO rows for 2019 and 2020**. The equivalency
register grades this **MISSING / HIGH** ("without it 2018-2020 cannot be dispatched at all
regardless of every other input's status"), and the pjm-160 correction block claims the gap
**CLOSED for 2019-2020** via `curate_demand_profile.py::curate_pre_window`. **For NEISO neither
statement is operative at HEAD**: the partition is still absent, *and* it does not matter.

`load_demand` precedence (`data/eia930/demand.py`) is: `DEMAND_LOADERS[iso]` → clean seam
(default off) → `_demand_profile_clean` → the profiles parquet. NEISO holds a real adapter
(`_neiso_demand_source` → `_load_neiso_hourly_demand` over `data/raw/eia-930-hourly/ISNE
hourly.parquet`, which covers 2018–2026), so **the profiles parquet is never reached for any
NEISO year**. Called directly:

```
2019 8760 h  mean 13,503 MW   2022 8760 h  mean 13,348 MW
2020 8760 h  mean 13,161 MW   2023 8760 h  mean 12,786 MW
2021 8760 h  mean 13,370 MW   2024 8760 h  mean 13,026 MW
                              2025 8760 h  mean 13,160 MW
```

2020's mean sits 1.6 % below 2021's — the COVID load depression, present in the model because
the demand is measured. Leap handling is exercised in-sample too (2024 is also 8784 raw hours).

---

## 3. The year-agnostic fleet statics — graded, and cleared by an internal control

`thermal_tranches_NEISO.csv` (76 plants) and `bin_assignments_NEISO.csv` (108 plants) carry no
year column: one committed vintage sets the committed / must-run / peaking tranche shares that
build the offer curve — i.e. price — for every year. The deriver's default is `--years 2024`
and the committed sidecar records its vintage as **UNKNOWN** ("DESCRIPTIVE BACKFILL", xiso-6).
Applying a late-vintage snapshot to 2020 is a real extrapolation, and it is the one axis where
2020 is genuinely further from the derivation window than 2021 is.

It still does not discriminate, and the reason is an internal control rather than an argument.
Share of each year's actual CAMPD generation covered by the statics:

| year | 2019 | **2020** | 2021 | **2022** | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| coverage | 90.35 % | **91.58 %** | 93.80 % | **91.72 %** | 94.80 % | 95.51 % | 97.08 % |

**2020 (91.58 %) and 2022 (91.72 %) are twins — and 2022 scores `CALIBRATED` with C3a at
−0.6 %.** Coverage at ~91.6 % is demonstrably compatible with the tightest C3a in the record,
so the statics' vintage cannot be what fails 2020. The uncovered mass is dominated by plant
1588 in *every* year, in-sample included (1,934 GWh in 2020; 1,339/1,297 in 2023/2024) — a
standing, uniform gap, not a 2020 one.

NEISO coal is likewise immaterial and points the wrong way: **0.32 %** of CAMPD generation in
2020 against **1.14 %** in 2021 (both far under rule 19 `[R-FORCED-BUDGET]`'s 2 % floor), so
the single-COAL-plant statics gap bites *2021* harder than 2020.

---

## 4. What the finding is, and what it is not

**Is:** 2020's input set is at parity. The `NOT-YET` is a scoring-denominator effect on the
cheapest year in the record, not evidence of a readiness shortfall or of degraded model
fidelity in 2020.

**Is not:**

- **Not a challenge to the rung's score.** `NOT-YET` stands. C3a's relative band is the
  rubric's certification claim, and this session neither proposes nor requests a rubric change.
  Rule 30(c) is untouched: the rung is **reported, not chased**, and NEISO's headline remains
  the train-tier verdict, **CALIBRATED**.
- **Not a lever, and not a proposal for one.** No mechanism was tested; no cell moves.
- **Not a re-spend.** 2020 and 2021 were already solved, scored and registered. Nothing here
  re-solves them, and the locked test (2019 / H1-2026) is untouched and stays frozen
  (`scope.tiers = ['locked_test']`).

**The one thing a future lane should take from it, stated without acting on it.** The model runs
**high in 5 of 6 years, mean +$1.99/MWh**. That is not a 2020 object — it is present at
+$1.19 / +$2.36 / +$1.16 in 2023 / 2024 / 2025. Anyone who wants to close 2020's $0.94/MWh
shortfall can therefore work the level bias **entirely in-sample**, which is where rule 22
step 3 requires the fitting to happen anyway. **2020 needs no lane of its own**; it is a
readout of an in-sample bias magnified by a small denominator. This session opens nothing.

---

## 5. Method note — the harness artifact, and the control that killed it

Recorded in full because it is the exact failure the neiso-102 handoff warns about (*"a guard
test that PASSES is not a guard … prove it fails when it should"*), inverted: a probe that
**failed** and looked like a finding.

**The apparent finding.** `load_renewable_profiles('NEISO', 2020, cfg, sc)` raises
`ValueError: No EIA-930 data for ISO 'NEISO' in year 2020`, tracing to
`_eia930_cf → load_generation_profiles → _filter_iso_year`. And
`eia_generation_profiles.parquet` genuinely holds **0 rows before 2021 for all six ISOs**. It
reproduced with the keeper's own 794-field `ScenarioConfig` reconstructed from the bundle, and
`git log 6619fb4a..HEAD` shows `renewables.py` and `data/eia930/` **unchanged since the solve**
— so "the code moved" was excluded too.

**The control.** Same call, ERCOT: **`ERCOT 2020` raises identically**, though ERCOT 2020 is a
listed `WEATHER_YEAR_POOL_BY_ISO` year verified end-to-end. And `ERCOT 2023` returns
42,000 / 38,000 MW — the hardcoded `RENEWABLE_INSTALLED_MW` constants, not EIA-860-derived
capacity. `_eia860_monthly_capacity` returns `None` for **every ISO and fuel** in this
checkout, so every call falls to the legacy `_eia930_cf` branch. The probe was measuring my own
environment, not the model.

**The positive evidence that settles it.** The committed 2020 bundle's own P1 output against
measured EIA-930 ISNE:

| GWh | model 2020 | measured 2020 | Δ |
|---|---:|---:|---:|
| wind | 3,539 | 3,549 | −0.3 % |
| solar | 361 | 362 | −0.3 % |
| nuclear | 25,486 | 25,536 | −0.2 % |

2020's renewables and nuclear were served essentially exactly. **Row 21 of the census is graded
on this output evidence, not on the probe.** The probe result is reported here and used for
nothing.

---

## 6. Records corrections (no action taken beyond the dated block)

Appended as a dated correction to `docs/holdout-data-equivalency-register-2026-07.md` §NEISO,
following that file's own convention (existing rows left unedited as the historical record).
Five of its NEISO rows are stale at HEAD, all in the *closed* direction:

| register row | as written (2026-07-13) | at HEAD |
|---|---|---|
| Driver demand — model profile | MISSING 2018-2020, **HIGH**, "no dispatch is possible" | still absent for NEISO — and **INERT**; the adapter serves 2019–2025 |
| `calibration_reference` | MISSING 2018-2020 | **2019–2025 all present** |
| `NEISO_<year>_renewable_capacity.csv` | MISSING 2018-2020 | **120 rows every year 2019–2025** |
| `actual_tail` NEISO | MISSING 2018-2021 | **2020–2025 present** |
| Gas hub basis, daily (Algonquin) | MISSING 2018-2022, medium | **45 prints in 2020**, in family with in-sample 30–49 |

**One handoff-prompt inaccuracy, noted and not acted on.** The neiso-103 prompt states NEISO's
2019 is "unsolvable at HEAD — Pilgrim absent from the 860 operable snapshot, **no demand rows
before 2021**". The second clause is contradicted by `ASSESSMENT-neiso101-2019-input-prep-2026-08-18.md`
(*"`load_demand("NEISO", 2019)` returns a full `(5, 8760)` array"*, 17 of 18 inputs resolve) and
by this session's own measurement (8760 h, mean 13,503 MW) — and it is contradicted structurally
by 2020 having solved with the same partition absent. **Nothing follows and nothing is
re-opened**: NEISO's `final` readiness is owner-closed, the other stated grounds are untouched
by this session, and the locked test is frozen for every ISO regardless.

---

## 7. Predictions, scored against interest

Registered before the census ran, from the handoff's framing (*"PJM's 2020 is known NOT
data-ready … NEISO's has never been checked. If inputs are short, the finding is that the rung
cannot mean what it appears to mean"*):

| # | prediction | outcome |
|---|---|---|
| 1 | At least one input family is materially short in 2020 but not 2021 | **WRONG.** Zero of 24. Three are *richer* in 2020 (F923, emission rates, parasitic coverage). |
| 2 | The daily Algonquin gas basis is the likeliest gap (register: MISSING 2018-2022) | **WRONG.** 45 prints in 2020, in family with in-sample 30–49; the register row is stale. |
| 3 | The year-agnostic fleet statics penalise 2020 more than 2021 | **RIGHT on the mechanism, WRONG on the consequence.** 2020 is further from the vintage, but its 91.58 % coverage twins 2022's 91.72 %, which scores `CALIBRATED`. |
| 4 | The rung "cannot mean what it appears to mean" | **RIGHT — via a route not anticipated.** Not an input shortfall: a relative-band denominator effect, with 2020's absolute error *smaller* than the rung that passes. |

Prediction 4 was reached by the opposite evidence from the one that motivated it. Recorded that
way rather than claimed as a hit.

---

## 8. Session ledger

- **LP minutes: 0.** No solve, no screen, no control run (rule 29 `[R-SCREEN]` order not
  entered — no arm was proposed).
- **No run produced** ⇒ no dashboard registration, no prune (rule 15 `[R-DASHBOARD]` not
  triggered).
- **No mechanism tested** ⇒ `docs/codebase-site/data/mechanism-matrix/NEISO.js` **untouched**
  (neiso-102 precedent).
- **No keeper-shard edit** ⇒ `frontend/data/backcast/keepers/NEISO.json` untouched; no
  determination re-key, no `calibration-complete.json` change.
- **Holdout tiers untouched.** No out-of-training year solved, scored or registered.

**Next shorthand: `neiso-104`.** No NEISO lever is open. The 2020 rung is closed as an
input-readiness question and should not be re-audited; if the +$2/MWh level bias is ever worked,
it is an **in-sample** object (2023–2025), never a 2020 one.
