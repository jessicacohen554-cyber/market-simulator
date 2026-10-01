# FINDING — nyiso-207: the daily-aggregate/hourly-applied basis gap is a **property of the construction, not of one limb** — it is present, with the predicted sign, on **every one of the seven live NYISO floor knots that reproduce**, and its magnitude is **predicted by within-window dispersion alone (5 of 5, monotone)**. And the session's own pre-registered class verdict is **NOT MET**, which is reported first

**Session:** nyiso-207, NYISO backcast calibration. **Branch:**
`claude/nyiso-backcast-calibration-ak5xig`, off `main` `aeceb302`. **Date:** 2026-09-06.
**DATA PROFILE:** `nyiso`. **Keeper:** `2026-09-06-nyiso-202-startup-aware` — **UNCHANGED**.
Nothing promoted, nothing registered, no `ScenarioConfig` field, no coefficient edit, no CSV edit,
no `src/market_sim/` change, no scorer change.

**ZERO LP WAS SPENT.** Rule 29 `[R-SCREEN]` step 0 gated the solve to zero, as the PREREG said it
would: the only outcomes on the table were a measurement and a card, and **neither is an arm**, so
no screen year was pre-registered because there was nothing for a screen to gate.

**PREREG:** `results/calibration/PREREG-nyiso207-floor-coeff-basis-census.md` — committed and
pushed **before any number was read** (`c62ef3cc`), with **addendum §A declared POST-HOC and
labelled as such**, committed **before the check it declares was executed** (§5 below).
**Instruments:** `scripts/probes/_nyiso207_floor_coeff_basis_census.py` →
`results/calibration/_nyiso207_floor_coeff_basis_census.json`;
`scripts/probes/_nyiso207_ct_denominator_check.py` →
`results/calibration/_nyiso207_ct_denominator_check.json`.
**Companion:** `docs/DECISION-CARD-nyiso207-floor-coeff-basis-2026-09-06.md`.

**THERE ARE NO RUBRIC FAILURES TO FIX.** NYISO reads **fails 0**. C3c is the ledgered,
non-downgrading caveat (rubric v3.3 / v3.6) and was **not an objective**. **No metrics file, price
series or volume residual was opened at any point in this session.**

---

## 0. Verdict in one paragraph

Every live NYISO reliability-floor coefficient is a **percentile over a population of daily
aggregates**, applied as an **hourly** floor fraction. Two prior sessions each measured the
resulting gap on **one** limb — nyiso-203 §6 on the NYC `base_24h` (−4.9 %), nyiso-140 §3.2 on the
Long_Island `base_24h` (−23.3 %) — and the pending owner ruling could not be scoped without knowing
whether it concerns one coefficient or a construction. This session measured **all ten live knots**
from source. **Eight reproduce their frozen value** (median absolute error **0.0002**), and on
**every one of the seven that reproduce with a defined gap, the gap has the sign the mechanism
predicts** — base knots negative (**−1.62 / −4.89 / −6.97 / −13.35 / −23.34 %**), cap knots positive
(**+3.68 / +3.93 %**) — **7 of 7**. Its magnitude is explained by **one** variable: rank the base
knots by within-window dispersion and |gap| rises **monotonically, 5 of 5**, from 1.62 % at CV 0.117
to 23.34 % at CV 0.392. **So the defect is a property of the construction and is fully understood.**
**But the session's own pre-registered class verdict is NOT MET** — it required ≥ 2 *in-scope* limbs
at ≥ 5 %, and only one is (§4.3) — and the pre-registered magnitude prediction that **cut against
this session** was **confirmed**: evening-window knots gap ~3× *less* than the same zone's 24 h knot
(NYC 1.62 vs 4.89; LI 6.97 vs 23.34), because an 8-hour window holds less dispersion than a 24-hour
one. **The two results are both true, and the honest reading is the narrow one:** the construction
is systematically biased in a now-quantified way, and on the *live evening knots* the bias is small
and its reachability smaller still (measured band 0.89–3.37 % of hours; largest sizing **−0.068 TWh**
on a 1.318 TWh limb). **Nothing is taken** — rule 23 `[R-FROZEN-DERIVE]` has no source-data trigger,
and the PREREG fixed that before the numbers, precisely so a clean explanation could not become a
licence to act.

**Not a keeper candidate. There is nothing to promote, and nothing is proposed.**

---

## 1. The object, and a correction to the charter's premise

The charter offered as its alternative object *"a NYISO limb whose construction has never been
compared against its own derive-script basis (the **Long_Island persistent-24h base** is the obvious
untouched one)"*. **That premise is false, and PREREG §2 recorded the correction before measuring
rather than acting on it.** `FINDING-nyiso140-li-st-floor-membership-2026-08-16.md` §3.2 already
carries that limb's full 2×2 basis grid — {hourly, daily-mean} × {3 plants as frozen, 2 plants
excluding 2517} — and its membership question is adjudicated. Re-running it would have been a
DO-NOT-REDO violation dressed as new work.

**What the correction opened is a better object**, and it is the one the pending ruling needs. The
construction under audit, in `scripts/data/derive_nyiso_st_reliability_floor.py::main`:

```python
all_day = g.groupby("date").agg(gross=("gross", "sum"), avail=("avail", "sum"))
daily24 = (all_day["gross"] / all_day["avail"]).where(all_day["avail"] > 0)
base24  = float(cool24["cf"].quantile(0.25))   # p25 of a DAILY-MEAN population
cap     = float(P["cf"].quantile(0.97))        # p97 of a DAILY-MEAN population
base    = float(cool["cf"].quantile(0.25))     # p25 of a DAILY-EVENING-MEAN population
```

and identically in `derive_nyiso_ct_reliability_floor.py`. The delivered floor is
`frac × pmax × availability[t]`, **per hour** (`model/interchange/core.py::_apply_frac`). **A
percentile of daily means is not the percentile of the hourly population it is applied to**, whenever
there is dispersion inside the aggregation window. Ten live knots carry it; two had been measured;
**eight had not.**

## 2. The instrument, validated against two prior sessions before anything new was read

The probe calls the **shipped** derive-script functions (`zone_steam_plant_codes`,
`zone_available_capacity`, `downstate_peaker_plant_codes`) by file-path import rather than
re-implementing them, so the daily statistics it recomputes are the scripts' own. **M1 is a hard
gate**: a limb that does not reproduce its frozen value to within **0.002 absolute** is reported NOT
REPRODUCIBLE and **no gap is computed for it**, so a *pipeline* difference can never be reported as
a *basis* difference.

The two already-measured limbs are the calibration, and the agreement is exact on **four**
independent numbers produced by **three** different instruments across **three** sessions:

| quantity | nyiso-140 / nyiso-203 | **nyiso-207** |
|---|---:|---:|
| NYC `base_24h`, daily-mean basis | 0.1748 *(nyiso-203 §2)* | **0.1749** |
| NYC `base_24h`, hourly basis | 0.1663 *(nyiso-203 §6)* | **0.1663** |
| LI `base_24h`, daily-mean basis | 0.2623 *(nyiso-140 §3.2)* | **0.2623** |
| LI `base_24h`, hourly basis | 0.2011 *(nyiso-140 §3.2)* | **0.2011** |

## 3. The census

Pooled 2023–2025, the derive scripts' own `--years` default. `M1` is the re-derived frozen basis,
`M2` the same percentile on the hourly population it is applied to, with fleet, day selection,
availability normalisation and hour window all held identical — **one change only**.

| limb | scope | frozen | M1 | gate | M2 | **gap %** | band % | CV |
|---|---|---:|---:|:---:|---:|---:|---:|---:|
| NYC ST `base_24h` | gate | 0.1750 | 0.1749 | ✓ | 0.1663 | **−4.89** | 1.97 | 0.1658 |
| LI ST `base_24h` | gate | 0.2620 | 0.2623 | ✓ | 0.2011 | **−23.34** | 14.60 | 0.3920 |
| **NYC ST `base_ev`** | **in** | 0.1850 | 0.1849 | ✓ | 0.1819 | **−1.62** | 0.89 | 0.1173 |
| **NYC ST `cap`** | **in** | 1.0000 | 1.0358 | **✗** | — | — | — | 0.1275 |
| **LI ST `base_ev`** | **in** | 0.3500 | 0.3502 | ✓ | 0.3258 | **−6.97** | 3.37 | 0.2199 |
| **LI ST `cap`** | **in** | 0.8820 | 0.8815 | ✓ | 0.9140 | **+3.68** | 1.39 | 0.1804 |
| CH ST `base_ev` | census | 0.0000 | 0.0000 | ✓ | 0.0000 | *n/a (zero)* | 0.00 | 0.0858 |
| CH ST `cap` | census | 0.3200 | 0.8701 | **✗** | — | — | — | 0.0809 |
| **DS CT `base`** | census | 0.1320 | 0.1316 | ✓ | 0.1140 | **−13.35** | 5.54 | 0.3162 |
| DS CT `cap` | census | 0.6790 | 0.6789 | ✓ | 0.7056 | **+3.93** | 0.72 | 0.2916 |

*`band %` = the share of the limb's own applicable hours whose metered fleet when-available CF falls
strictly between the two coefficients — the only hours whose binding state a coefficient move can
change, so it bounds what the move can reach (nyiso-203 §6's instrument). `CV` = the median across
days of the within-window coefficient of variation of hourly when-available CF.*

### 3.1 The two M1 failures are both explained, and neither is a defect

- **NYC ST `cap`** re-derives to **1.0358** against a frozen **1.0000**. That is not a mismatch —
  the CSV's own `threshold_basis` says *"clamped at the 1.0 physical bound … **measured p97 avail-CF
  1.036** exceeds it"*. The probe reproduces **1.036** to three decimals. The frozen value is a
  **clamp at a physical bound, not a percentile**, so the M1 gate correctly withholds a gap for it:
  the hourly p97 is higher still, and a floor already clamped at 1.0 cannot be raised. **PREREG
  prediction 4 CONFIRMED — the limb is inert, and it is reported as inert rather than as a passing
  gap.**
- **CH ST `cap`** re-derives to **0.8701** against a frozen **0.3200**. Its own prose names a
  *different construction* — *"legacy CH slope 0.0246/C hot-limb to clamp @38C; measured hot-day CF
  **regression**"* — i.e. a slope extrapolation, not a p97. **The divergence is therefore NOT
  attributable to the time basis and is NOT reported as a gap.** It is a genuinely unexplained
  legacy value on a live limb; it is named in §7 as an observation for the owner and **nothing is
  inferred from it here.**

### 3.2 One census row surprised the pre-registration, and it is flagged rather than promoted

PREREG §4 predicted that the rows flagged *"legacy"* in their own prose — including the downstate
CT knots — **would fail M1**. **`DS_CT_base` and `DS_CT_cap` both reproduced** (0.1316 vs 0.1320;
0.6789 vs 0.6790). Their "legacy" label evidently marks that they predate the ramp restructure, not
that they came from a different construction. So the **−13.35 %** gap on `DS_CT_base` is a real
measurement on a **live limb that is carried twice** — NYC and Long_Island CT_PEAKER are both frozen
at 0.1320 from the same pooled-downstate derivation (CSV rows 5 and 7).

**It is NOT retroactively moved into the in-scope set to flip the §4.3 verdict.** The pre-registered
rule is applied as written and reported as failing; this row is reported **beside** it, labelled as
beyond the rule. Re-scoping a decision rule after seeing which rows would satisfy it is precisely
the selection rule 1 `[R-STRUCT]` exists to refuse.

## 4. The pre-registered predictions, scored — including the one that fails

### 4.1 P1 — SIGN. **CONFIRMED, 7 of 7.**

The mechanism claimed is that a percentile of daily means is computed on a **less dispersed**
population, so a **p25 must sit above** the hourly p25 and a **p97 below** it. Every base knot gaps
negative (−1.62, −4.89, −6.97, −13.35, −23.34) and every cap knot gaps positive (+3.68, +3.93).
**Not one of the seven dissents.** A single base knot gapping positive, or cap knot negative, would
have refuted the mechanism; none did.

### 4.2 P2 — MAGNITUDE. **CONFIRMED — and this is the prediction that cut against the session.**

PREREG §5 item 2 declared, before measuring, that the evening knots aggregate over **8 hours** and
are applied inside that same 8 hours, so **less dispersion is available** than in a 24-hour window,
and their gaps *"are expected to be SMALLER — plausibly much smaller"*, with the explicit commitment
that a small evening gap *"will not be spun as a class-wide defect."* Measured, same zone, same
fleet, same statistic:

| zone | 24 h knot | evening knot | ratio |
|---|---:|---:|---:|
| NYC | −4.89 % | **−1.62 %** | 3.0× |
| Long_Island | −23.34 % | **−6.97 %** | 3.3× |

**Confirmed in both zones, at almost the same ratio.** This is why §0's headline is the narrow
reading: the construction is biased everywhere, and on the **live evening limbs** the bias is small.

### 4.3 §6 CLASS VERDICT — **NOT MET.** Reported first, not last.

The rule was: *"If **≥ 2 in-scope** limbs clear M1 and show |relative gap| **≥ 5 %** with the §5.1
signs, the defect is reported as a construction-class property … Otherwise the card stays scoped to
the two `base_24h` limbs already measured, and the evening knots are reported as a **CLEAN
NEGATIVE**."* Of the three in-scope limbs that cleared M1 — NYC `base_ev` (−1.62), LI `base_ev`
(−6.97), LI `cap` (+3.68) — **exactly one** is ≥ 5 %. **The verdict is NOT MET, and the evening
knots are a CLEAN NEGATIVE on the pre-registered terms.** The machine record carries
`class_verdict_ge2_limbs_ge5pct: false`.

**What the session claims instead, and why that is not the verdict smuggled back in.** §4.1 and §4.4
establish the *sign* and the *predictor* across all seven reproducing limbs — a **different and
weaker claim** than the §6 rule's, which was about *magnitude on the in-scope rows*. The
construction is shown to be **systematically biased and fully explained**; it is **not** shown to be
materially large on the live evening limbs, and §6's answer to that question stands as written.

### 4.4 P3 — MONOTONICITY. **REFUTED as written, because the pre-registration was internally inconsistent.**

The machine record reads `P3_monotone_in_M5: false`. The rule asked for |gap| to increase
monotonically in CV **across all in-scope limbs pooled** — but **P1 had already predicted that base
and cap knots gap in opposite directions**, and pooling two oppositely-signed statistics into one
|gap| ordering could not have been monotone whatever the data did. **That is a defect in this
session's own pre-registration, not in the data**, and it is recorded as such rather than quietly
repaired.

**Split by statistic — declared POST-HOC, because it is** — the relationship is exact:

| base knots, by ascending CV | CV | \|gap\| % |
|---|---:|---:|
| NYC ST `base_ev` | 0.1173 | 1.62 |
| NYC ST `base_24h` | 0.1658 | 4.89 |
| LI ST `base_ev` | 0.2199 | 6.97 |
| DS CT `base` | 0.3162 | 13.35 |
| LI ST `base_24h` | 0.3920 | 23.34 |

**Strictly monotone, 5 of 5**, spanning a 14× range in |gap| — across two derive scripts, two plant
classes, three zones and two window widths. The cap knots agree on their own two points (+3.68 at CV
0.180, +3.93 at CV 0.292). **One variable — within-window dispersion — orders the entire census.**
That is the substantive positive result, and it is a post-hoc split of a pre-registered statistic,
which is why it is labelled and why it is not allowed to rescue §4.3.

## 5. Addendum §A — the confound check that could only hurt the session's largest number

`derive_nyiso_ct_reliability_floor.py` normalises by **nameplate with no outage derate**, unlike its
ST sibling. Outage hours therefore stay in the CT population as near-zero readings, which inflate
**hourly** dispersion far more than they move a **daily mean** — so they could have manufactured the
−13.35 % `DS_CT_base` gap for a reason having nothing to do with the time basis. **The check was
declared, with its withdrawal threshold, in PREREG addendum §A and committed before it was run**
(`0d665cdd`), for the reason `PREREG-nyiso206` addendum §B exists: it can only weaken this session's
most striking number.

| limb | as shipped (nameplate) | availability-derated | change |
|---|---:|---:|---:|
| `DS_CT_base` | −13.35 % | **−13.69 %** | **+0.34 pt — grows** |
| `DS_CT_cap` | +3.93 % | +4.10 % | +0.17 pt |

**The gap SURVIVES**, on the declared ≥ 10 % threshold. The un-derated denominator is not its cause;
the CT fleet's genuine intra-evening cycling is. **Stated against the session's convenience:** the
addendum's thresholds were written for the base limb and **mis-apply to the cap limb**, whose gap was
never ≥ 5 % to begin with, so the script's mechanical `WITHDRAWN_AS_CONFOUNDED` label on `DS_CT_cap`
is **wrong** — nothing was withdrawn there because nothing had been claimed. The correct reading is
that the cap limb is likewise unconfounded and simply small. The label is left in the machine record
as written rather than edited after the fact, and corrected here.

## 6. Reachability and size — what a basis repair would actually move

For the ramp limbs, under the model's own composition (the all-hours `base_24h` floor and the evening
ramp combined by **maximum**, per CLAUDE.md), moving **one knot at a time** to its basis-matched
value, pooled 2023–2025:

| zone | added TWh, frozen | base knot moved | Δ | cap knot moved | Δ |
|---|---:|---:|---:|---:|---:|
| NYC | 1.04953 | 1.03215 | **−0.01738** | *withheld (M1)* | — |
| Long_Island | 1.31762 | 1.24965 | **−0.06797** | 1.32203 | +0.00441 |
| Capital_Hudson | 0.03035 | 0.03035 | **0.00000** | *withheld (M1)* | — |

The largest live-evening-knot effect is **−0.068 TWh over three years on a 1.318 TWh limb (−5.2 %)**;
NYC's is **−0.017 TWh (−1.7 %)**; Capital_Hudson's is **exactly zero**, its `base_ev` being 0.0 —
inert by construction, as PREREG §3.1 recorded by inspection. Reachability agrees: the measured band
covers **0.89 % / 3.37 % / 1.39 %** of the in-scope limbs' own hours. For context the two
already-measured `base_24h` limbs are where the size actually sits — nyiso-203 sized NYC's at
**−0.133 TWh**, and Long_Island's band alone covers **14.60 %** of its hours.

## 7. What this means for the pending ruling — and what is deliberately NOT taken

The question the owner faces on nyiso-203 §6 was *"should this one coefficient be re-derived?"*
**This session re-specifies it**: the NYC gap is not a property of the NYC limb, it is one draw from
a construction whose bias is **systematic in sign (7/7)** and **ordered by a single measurable
variable (5/5)**. A ruling that moved NYC's coefficient alone would leave six other live knots
carrying the same construction, in the same direction, at magnitudes from 1.6 % to 23.3 %. That is
the fact the card carries.

**Deliberately NOT taken, named so silence is not read as absence.**

- **No coefficient is edited, and no replacement value is proposed for any limb.** Rule 23
  `[R-FROZEN-DERIVE]` has **no source-data trigger** — no source data has updated — and whether a
  construction repair is itself an adequate identification under rule 21 `[R-DOF]` is an **owner**
  call, exactly as nyiso-203 §7 reason 2 held. The PREREG §6 fixed this **before** the numbers so a
  clean explanation could not become a licence to act on it.
- **No derive script is changed**, and neither is `_apply_frac` or `_distribute_group_floor`.
- **No other ISO is measured.** The same two scripts have per-ISO siblings and `_apply_frac` is
  shared; their exposure is **unmeasured and was not measured here** (rule 25 `[R-ISO-SCOPE]`),
  exactly as nyiso-206 §5 refused for the shared fill kernel.
- **Row 1 (Capital_Hudson `commit_frac × min_stable_pct`) was left out of the census** so as not to
  blur two cards the owner should read separately. `DECISION-CARD-nyiso206` stays UNRULED.
- **The CH `cap` legacy value (0.3200 frozen vs 0.8701 on a p97 basis)** is reported as an
  unexplained legacy number on a live limb and **nothing is inferred from it** — its own prose names
  a regression construction this census does not evaluate. It is named for the owner, not diagnosed.
- **`DECISION-CARD-nyiso193` stays UNRULED**; nothing here rules it, and no scorer file was touched.

## 8. Governance

| item | state |
|---|---|
| **LP spent** | **none.** Rule 29 `[R-SCREEN]` step 0 gated the solve to zero; no screen year was pre-registered because no arm was ever on the table (PREREG §6) |
| **Rule 29(b) G-DRIFT** | **re-validated EMPIRICALLY at this HEAD, not by reading hunks**, as the charter requires: `scripts/probes/nyiso198_rebuild_checks.py --year 2024` re-run leaves `git status --porcelain -uno` **EMPTY** — the committed `_nyiso198_rebuild_checks_2024.json` regenerates byte-identically. G-CTRL **form 4** valid; **no control solve spent**, and none could be owed since nothing was differenced against a solve. *(That probe prints its own `"VERDICT": "STOP"` — the adjudicated nyiso-198 duct-peaking gate, an `R` cell. Part of the committed record, **not** a drift signal; nothing here re-opens it.)* |
| **Keeper** | `2026-09-06-nyiso-202-startup-aware`, **UNCHANGED**. Not a keeper candidate; no promotion, no re-stamp, no `build_status` / `prune_iso_runs` / gate-(a) re-key owed |
| **Markers** | untouched. `complete` (WITHDRAWN, Q5) and `frontier` re-entry are **owner** acts. Card C-19 / Q51 stays **PARKED** |
| **Rule 1 `[R-STRUCT]`** | no mechanism selected on a residual. NYISO reads **fails 0**; C3c is the ledgered non-downgrading caveat and was **not** an objective. **No metrics file, price series or volume residual was opened at any point.** The `offer_curve_by_group` channel is owner court under carve-out condition (c) and was **not touched** |
| **Rule 21 `[R-DOF]` / 23 `[R-FROZEN-DERIVE]`** | zero fields, zero DOF entries, **zero re-derivations into any artifact**. Every frozen coefficient was **read and none written**. No value is proposed for any of them |
| **Rule 22 `[R-HOLDOUT]`** | 2023–2025 only. No out-of-training year solved, scored or registered. The `NY_2020/2021/2022/2026.parquet` extracts present in this profile were **not read** |
| **Rule 25 `[R-ISO-SCOPE]`** | NYISO only. No other ISO's coefficients read, measured or cited |
| **Rule 26 / 28 `[R-MECH-MATRIX]`** | NYISO shard `reliability_floor` cell updated **in this session** with this outcome, per duty (b); key set verified identical to `main` before commit |
| **Rule 15 `[R-DASHBOARD]`** | nothing registered — no run finished, so there is no run. Git history + this finding + the card are the record |
| **Rule 29(c)** | no screen bundle and no control bundle exist, so there is nothing to delete before merge |
| **Files added** | 2 probes, 2 JSON records, 1 PREREG (+1 addendum), this finding, 1 decision card. **No `src/market_sim/` change, no CSV edit, no derive-script edit, no scorer edit** |

### 8.1 Reported, not fixed — other lanes' pre-existing failures at HEAD

Re-measured at this session's HEAD across the charter's named files, with this session's tracked
changes being **additive only** (new probes + docs + records; no tracked file that could affect them
was modified): **37 failed / 68 passed** — **identical to nyiso-206's measurement, file for file**,
so `main` has not moved on these since.

| file | failures | owner |
|---|---:|---|
| `tests/unit/model/test_d62_published_going_forward_bar.py` | 15 | capx |
| `tests/unit/model/test_d74_no_default_cap_convention.py` | 12 | capx |
| `tests/scoring/test_ff_readiness_battery.py` | 4 | FF-readiness |
| `tests/scoring/test_collate_scenario_campaign_common_set.py` | 4 | SCN-WS5A-LOAD |
| `tests/regression/test_constants_facade.py::test_moved_surface_is_complete` | 1 | — |
| `tests/unit/data/test_caiso_st_gas_peak_measured.py` | 1 | CAISO |

**Not fixed from this lane** (rule 25): none is NYISO's file or NYISO's number, and silently
re-baselining another lane's regression constant is how a real regression gets buried.

## 9. What this closes, what stays open

**Closed.** The basis of **every live NYISO reliability-floor knot** is now measured. The two M1
failures are explained (a physical clamp; a different construction). The evening knots are a
**CLEAN NEGATIVE on the pre-registered terms** (§4.3) and need not be re-measured. The
Long_Island `base_24h` limb is **not** an untouched object and must not be re-run as one (§1).
**DO-NOT-REDO** covers this census absent a source-data update to the CAMPD extracts.

**Established (positive).** The daily-aggregate/hourly-applied gap is **systematic in sign across
7 of 7 reproducing limbs** and its magnitude is **ordered monotonically, 5 of 5, by within-window
dispersion alone** — across two derive scripts, two plant classes, three zones and two window widths.

**Open, and unchanged by this session.** Rule 20 `[R-FORCED-BUDGET]` leg (a), and the unit-grain C8
exposure it rests on (`ST_GAS` 0.351 / 0.343 / 0.268 against the 0.30 cap, 2 of 3 years).
`DECISION-CARD-nyiso193` and `DECISION-CARD-nyiso206` both remain **UNRULED**. The construction
question this session measures is handed to the owner in
`docs/DECISION-CARD-nyiso207-floor-coeff-basis-2026-09-06.md`.

---

*(nyiso-207, 2026-09-06. Zero LP. A construction measured whole, a pre-registered class verdict that
failed on its own terms and is reported as failing, and nothing taken.)*
