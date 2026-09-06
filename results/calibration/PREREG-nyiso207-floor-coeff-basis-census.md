# PREREG — nyiso-207: is the daily-aggregate-identified / hourly-applied basis gap a property of ONE limb, or of the construction that derives EVERY live NYISO reliability-floor coefficient?

**Session:** nyiso-207, NYISO backcast calibration. **Branch:**
`claude/nyiso-backcast-calibration-ak5xig`, off `main` `aeceb302`. **Date:** 2026-09-06.
**DATA PROFILE:** `nyiso`. **Keeper:** `2026-09-06-nyiso-202-startup-aware` — unchanged by this
session. **ZERO LP is budgeted and none is expected to be earned.**

Written **before any number of this session's object is read.** Numbers land in the FINDING and
in the decision card, not here.

---

## 1. The statements the charter requires this PREREG to carry

- **THERE ARE STILL NO RUBRIC FAILURES TO FIX.** NYISO reads **fails 0** on the keeper
  (grade 7/8); **C3c is the lone ledgered caveat**, is non-downgrading under rubric v3.3 / v3.6,
  and **is not an objective of this session**. No criterion is hunted. Nothing below is selected
  because a residual moved (rule 1 `[R-STRUCT]`). **No metrics file, price series or volume
  residual will be opened at any point in this session.**
- **THE OFFER-CURVE CHANNEL IS OWNER COURT AND IS NOT TAKEN.** The `offer_curve_by_group` band
  multipliers are the authorized price-tuning channel under rule 1's 2026-09-05 carve-out, whose
  condition (c) reserves them to the owner, set ex ante and never swept. This session does not
  touch them.
- **MARKERS ARE NOT MINE.** `complete` is WITHDRAWN (Q5, nyiso-192); `frontier` is withdrawn on
  the determination limb. Re-entry to either is an explicit **owner** act. Neither is edited,
  prepared, or treated as earned. Card **C-19 / Q51 stays PARKED**. Rule 22 `[R-HOLDOUT]`:
  **2023–2025 is the entire world of this session.** The `NY_2020/2021/2022/2026.parquet`
  extracts are present on disk in this profile and **will not be read**; every population below
  is pooled over 2023–2025 exactly as the derive scripts' own `--years` default is.
- **`DECISION-CARD-nyiso193-d2-unit-grain-2026-09-05.md` §5/§5.1 stays UNRULED.** This session
  does not rule it and does not rely on a ruling of it. Neither does it rule
  `DECISION-CARD-nyiso206`.
- **DO-NOT-REDO is respected in full.** Not re-tested: the Capital_Hudson **membership** arm in
  either form (2480+8006, nyiso-204; 2480 alone, nyiso-204b); the **fill-order operator**
  question (nyiso-205 — `cheapest_first` CONFIRMED, `pro_rata` REFUTED); the **min-stable-capped
  fill** (nyiso-206, REFUTED); the NYC limb's **window, membership or operator** (nyiso-203
  §§3–5, all three measured clean); the Long_Island limb's **membership** (nyiso-140, 2517
  excluded and adjudicated). **No matrix cell marked `R`/`I`/`G` is re-tested.**
- **Nothing is proposed for promotion.** No arm, no `ScenarioConfig` field, no coefficient edit,
  no CSV edit, no `src/market_sim/` change, no scorer change. The deliverable is a measurement
  and an owner card.

## 2. A correction to the charter's premise, recorded before measuring

The charter offers as its alternative object *"a NYISO limb whose construction has never been
compared against its own derive-script basis (the **Long_Island persistent-24h base** is the
obvious untouched one)"*. **That premise is false and is corrected here rather than acted on.**
`FINDING-nyiso140-li-st-floor-membership-2026-08-16.md` §3.2 already carries the full 2×2 basis
grid for that limb — {hourly, daily-mean} × {3 plants as frozen, 2 plants excluding 2517} — and
its membership question is adjudicated. Re-running it would be a DO-NOT-REDO violation dressed as
new work.

**What that correction opens is a better object.** Two *different* sessions have now measured the
daily-aggregate/hourly-applied gap on the two `base_24h` limbs — nyiso-203 §6 on NYC, nyiso-140
§3.2 on Long_Island — and **nobody has measured it on the SIX other live NYISO floor knots that
are produced by the same two derive scripts under the identical construction.** Those knots are
armed in the keeper of a **CALIBRATED** ISO. Pending owner ruling (ii) — nyiso-203 §6's NYC gap,
which §8 point 3 says *"needs a ruling, not another measurement"* — cannot be responsibly scoped
without knowing whether the owner is being asked to rule on **one coefficient or on a
construction**. Supplying that fact is this session's object.

## 3. The object

Every live NYISO reliability-floor coefficient is a **percentile over a population of DAILY
aggregates** and is applied as an **HOURLY** floor fraction. In
`scripts/data/derive_nyiso_st_reliability_floor.py::main`:

```python
all_day = g.groupby("date").agg(gross=("gross", "sum"), avail=("avail", "sum"))
daily24 = (all_day["gross"] / all_day["avail"]).where(all_day["avail"] > 0)
...
base24 = float(cool24["cf"].quantile(0.25))    # p25 of a DAILY-MEAN population
cap    = float(P["cf"].quantile(0.97))         # p97 of a DAILY-MEAN population
base   = float(cool["cf"].quantile(0.25))      # p25 of a DAILY-EVENING-MEAN population
```

and in `scripts/data/derive_nyiso_ct_reliability_floor.py::main`:

```python
daily = ev.groupby("date")["grossLoad"].sum() / (nameplate * len(EVENING_HOURS))
cap = float(P["cf"].quantile(0.97)); base = float(cool["cf"].quantile(0.25))
```

The delivered floor is `frac × pmax × availability[t]` **per hour**
(`model/interchange/core.py::_apply_frac`). **A percentile of daily means is not the percentile of
the hourly population it is applied to** whenever there is dispersion inside the aggregation
window. That is the object: not a level choice, and not an operator choice — a basis audit of the
identification, of exactly the class nyiso-140 §3.2 and nyiso-203 §6 each named on one limb.

### 3.1 Scope — the live limbs, and which are in

Live (`enabled=True`) rows of `data/raw/reference/reliability_floor_coeffs_NYISO.csv`:

| # | zone | class | driver | thr | `floor_pct` | window | statistic | status |
|---|---|---|---|---:|---:|---|---|---|
| 1 | Capital_Hudson | ST_GAS | tmax | 31.1 | 0.0973 | all-h | `commit_frac × min_stable_pct` | **OUT** — nyiso-206's object, already before the owner |
| 2 | NYC | ST_GAS | tmax | −50.0 | 0.1750 | all-h | `base_24h` p25 | **gate only** — measured by nyiso-203 |
| 3 | NYC | ST_GAS | tmax | 25.0 | 0.1850 | h14–21 | `base_ev` p25 | **IN** |
| 4 | NYC | ST_GAS | tmax | 38.0 | 1.0000 | h14–21 | `cap` p97, clamped at the 1.0 physical bound | **IN** |
| 5 | NYC | CT_PEAKER | tmax | 25.0 | 0.1320 | h14–21 | legacy `base` p25 | **IN (census)** |
| 6 | NYC | CT_PEAKER | tmax | 35.22 | 0.6790 | h14–21 | legacy `cap` p97 | **IN (census)** |
| 7 | Long_Island | CT_PEAKER | tmax | 25.0 | 0.1320 | h14–21 | legacy, pooled downstate | **IN (census)** |
| 8 | Long_Island | CT_PEAKER | tmax | 35.22 | 0.6790 | h14–21 | legacy, pooled downstate | **IN (census)** |
| 9 | Long_Island | ST_GAS | tmax | −50.0 | 0.2620 | all-h | `base_24h` p25 | **gate only** — measured by nyiso-140 |
| 10 | Long_Island | ST_GAS | tmax | 25.0 | 0.3500 | h14–21 | `base_ev` p25 | **IN** |
| 11 | Long_Island | ST_GAS | tmax | 37.55 | 0.8820 | h14–21 | `cap` p97 | **IN** |
| 12 | Capital_Hudson | ST_GAS | tmax | 25.0 | 0.0000 | h14–21 | legacy, `base_ev = 0` | **IN (census)** — inert at zero by inspection |
| 13 | Capital_Hudson | ST_GAS | tmax | 38.0 | 0.3200 | h14–21 | legacy `cap` | **IN (census)** |

**Out of scope and named so silence is not read as absence:** row 1 (nyiso-206's card — measuring
its time basis too would blur two cards the owner should read separately); every disabled row;
**every other ISO** (rule 25 `[R-ISO-SCOPE]` — the same two derive scripts have per-ISO siblings
and their exposure is NOT this lane's to measure, exactly as nyiso-206 §5 refused for the shared
fill kernel); and the model's `_apply_frac` / `_distribute_group_floor` delivery path, which this
session does not touch.

## 4. The measurements, fixed before running

Per in-scope limb, on the derive scripts' own inputs only (`data/raw/campd-unit-level/NY_{yr}.parquet`,
`campd-unit-outages-NYISO.csv`, `bin_assignments_NYISO.csv`, `nyiso-weather/nyiso_zone_tmax_daily.csv`),
pooled 2023–2025:

- **M1 — IDENTITY GATE.** Re-derive the frozen value on the script's own construction.
  **Tolerance |re-derived − frozen| ≤ 0.002 absolute.** *(For calibration: nyiso-203 reproduced
  0.17485 against a frozen 0.17500, gap 0.00015; nyiso-140 reproduced 0.2623 against 0.2620.)*
  **A limb that fails this gate is reported NOT REPRODUCIBLE and NO gap is computed for it** —
  the gate exists so a *pipeline* difference can never be reported as a *basis* difference. Rows
  5–8 and 12–13 are flagged "legacy" in their own `threshold_basis` prose and **are expected to
  fail M1**; that expectation is recorded here so a failure reads as confirmation, not surprise.
- **M2 — BASIS-MATCHED VALUE.** The same percentile computed on the **hourly** population — the
  population the floor is applied to — with the fleet, the cool/hot day selection, the
  availability normalisation and the hour window all held identical. One change only.
- **M3 — GAP.** `M2 − M1`, absolute and relative to the frozen value.
- **M4 — REACHABILITY AND SIZE.** (a) the **measured band %**: the share of the limb's own
  applicable hours whose metered fleet when-available CF falls strictly between the frozen and
  basis-matched coefficients — the only hours whose binding state a coefficient move can change,
  so it bounds what the move can reach (nyiso-203 §6's instrument); (b) for the ramp limbs, the
  added forced energy `Σ max(0, floor − metered gross)` in TWh over h14–21, at the frozen ramp
  and with **one knot moved at a time** to its basis-matched value, the other held.
- **M5 — THE PREDICTOR.** Per limb, the fleet's coefficient of variation of hourly
  when-available CF **within** the aggregation window on the limb's own cool-day population.

## 5. Pre-registered predictions, and the ones that can hurt the session's preferred answer

The session's preferred answer is *"the gap is a construction-class property and deserves a
ruling."* These are declared **now** so the numbers can refuse it.

1. **SIGN, and it is sharp.** A percentile of daily means is computed on a **less dispersed**
   population than the hourly one. So the **p25 base knots must gap NEGATIVE** (hourly p25 below
   daily-mean p25) and the **p97 cap knots must gap POSITIVE** (hourly p97 above daily-mean p97).
   **A base knot that gaps positive, or a cap knot that gaps negative, REFUTES the mechanism this
   session claims is operating**, and will be reported as such.
2. **MAGNITUDE, and this one cuts against the session.** The two already-measured limbs aggregate
   over **all 24 h**; the in-scope knots aggregate over the **8-hour evening window** and are
   applied inside that same window. Less dispersion is available inside 8 h than inside 24 h, so
   **the evening knots' gaps are expected to be SMALLER — plausibly much smaller — than NYC's
   −5.0 % and Long_Island's −23.3 %.** A small evening gap is therefore the *expected* result and
   **will not be spun as a class-wide defect.**
3. **M5 monotonicity.** |relative gap| is expected to increase monotonically in the M5 dispersion
   statistic across the in-scope limbs. **Refuted if it does not**, and reported either way.
4. **Row 4 (NYC cap, 1.0) is expected to be INERT** — it is a clamp at the physical bound, not a
   measured p97, so a basis move cannot raise it. Reported as inert, not as a passing gap.

## 6. The decision rule, fixed before the numbers

- **CLASS VERDICT.** If **≥ 2** in-scope limbs clear M1 and show |relative gap| **≥ 5 %** with the
  §5.1 signs, the defect is reported as a **construction-class property of the derive scripts**
  and the owner card is scoped to the construction. Otherwise the card stays scoped to the two
  `base_24h` limbs already measured, and the evening knots are reported as a **CLEAN NEGATIVE**.
  **A clean negative is the session's full result and needs no compensating finding.**
- **NOTHING IS TAKEN, WHATEVER THE NUMBERS SAY.** No coefficient is edited, no replacement value
  is proposed, no derive script is re-run into the CSV, and no LP is spent. Rule 23
  `[R-FROZEN-DERIVE]` has **no source-data trigger** — no source data has updated — and rule 21
  `[R-DOF]` makes "is a construction repair an adequate identification?" an **owner** question,
  exactly as nyiso-203 §7 reason 2 held. **This is fixed here so that a large measured gap cannot
  become a licence to act on it.**
- **NO SCREEN YEAR IS PRE-REGISTERED**, because **no arm is on the table.** Rule 29 `[R-SCREEN]`
  phase 0 gates the solve, and the only outcomes here are a measurement and a card — neither is an
  arm, so there is nothing for a screen to gate. If that changes, this PREREG is amended in an
  addendum **before** the arm is built.

## 7. Governance

| item | commitment |
|---|---|
| **Rule 29(b) G-DRIFT** | re-validated **empirically** at this HEAD, not by reading hunks: `uv run python scripts/probes/nyiso198_rebuild_checks.py --year 2024` must leave `git diff` **clean**. Its stored `"VERDICT": "STOP"` is the adjudicated nyiso-198 duct gate, part of the committed record, **not** a drift signal |
| **Rule 26 `[R-MECH-MATRIX]`** | the NYISO shard cell is updated in **this** session whatever the verdict, and its key set diffed against `main` before commit |
| **Rule 27 `[R-PUSH]`** | any push touching a file ≥ 300 lines gets a blob verification before the next commit |
| **Rule 15 `[R-DASHBOARD]`** | nothing will be registered — no run will be produced. Git history, the finding and the card are the record |
| **Rule 25 `[R-ISO-SCOPE]`** | NYISO only. No other ISO's coefficients are read, measured or cited as a verdict |
| **Addenda** | any cut or counterfactual added after this document is committed is declared in an addendum and **labelled POST-HOC if it is** (`PREREG-nyiso206` addendum §B is the model) |

---

*(nyiso-207, 2026-09-06. Pre-registered before measurement. Zero LP budgeted.)*
