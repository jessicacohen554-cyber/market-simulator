# FINDING — nyiso-208: the shipped derive scripts reproduce **nine of ten** live NYISO floor coefficients to four decimal places at HEAD. The tenth — Capital_Hudson's hot-limb slope — is **UNIDENTIFIED**, at **2.04× the frozen value**, and **nine constructions fail to reach it**

**Session:** nyiso-208, NYISO backcast calibration. **Branch:**
`claude/nyiso-backcast-calibration-dlfexh`, off `main` `a6e4b6db`. **Date:** 2026-09-06.
**DATA PROFILE:** `nyiso`. **Keeper:** `2026-09-06-nyiso-202-startup-aware` — **UNCHANGED**.
Nothing promoted, nothing registered, no `ScenarioConfig` field, no coefficient edit, no CSV edit,
no derive-script edit, no `src/market_sim/` change, no scorer change, no marker touched.

**ZERO LP WAS SPENT.** Rule 29 `[R-SCREEN]` step 0 gated the solve to zero, as the PREREG said it
would: the only outcomes on the table were a measurement and a card, **neither is an arm**, so no
screen year was pre-registered because there was nothing for a screen to gate.

**PREREG:** `results/calibration/PREREG-nyiso208-ramp-slope-census.md` — committed and pushed
**before any number was read** (`8b7fefd8`); **addendum A declared POST-HOC**, committed and pushed
**before the checks it declares were executed**.
**Instruments:** the **shipped** `scripts/data/derive_nyiso_{st,ct}_reliability_floor.py`, run
directly (`--no-fetch --years 2023 2024 2025`); `scripts/probes/_nyiso208_ramp_slope_census.py` →
`results/calibration/_nyiso208_ramp_slope_census.json`; addendum A →
`_nyiso208_posthoc_addendumA.json`.
**Companion:** `docs/DECISION-CARD-nyiso208-ch-ramp-slope-2026-09-06.md`.

**THERE ARE NO RUBRIC FAILURES TO FIX.** NYISO reads **fails 0**. C3c is the ledgered,
non-downgrading caveat (rubric v3.3 / v3.6) and was **not an objective**. **No metrics file, price
series, volume residual or scored criterion was opened at any point in this session.**

---

## 0. Verdict in one paragraph

nyiso-207 censused every live NYISO floor **percentile** and left one row explicitly undiagnosed:
Capital_Hudson's `CH_ST_ev` cap knot, frozen at **0.3200**, whose prose names a *regression* rather
than a percentile. This session ran the **complement** — the ramp **slopes**, which no session had
ever reproduced. Three of the four reproduce **exactly**: NYC `0.0628`, Long_Island `0.0424`,
downstate CT `0.0535`, alongside every percentile those same runs print and **both** recorded
Pearson r values (NYC `+0.186`, LI `+0.547`). The fourth does not. Capital_Hudson's shipped hot-limb
slope measures **0.0502/°C against a frozen 0.0246/°C — a factor of 2.041** — and the pre-registered
alternative that would have explained it (a stale pre-guard-fix vintage) is **REFUTED in direction**:
the frozen value is *lower*, not higher. **Nine constructions were measured** — six spans, two
denominator bases, one physical clip — and the **minimum of all nine is 0.0400, still 1.63× the
frozen value**. The pre-registered verdict is **U — UNIDENTIFIED**, and it is reported first.
**Two things cut the other way and both are good news:** the frozen slope does **not** over-force
(**64.6 %** of CH hot days meter at or above it, P5 PASS) and the h14–21 window is **correct** for
this zone (median CF inside the window is **4.49×** the complementary hours, block profile peaking
h16–19, P6 PASS) — so the charter's alternative object closes as a **clean negative**.
**Nothing is taken.** Rule 23 `[R-FROZEN-DERIVE]` has no source-data trigger, no replacement value
is proposed, and the direction of the gap means a "repair" would **more than double** this limb's
forcing — a cost, not a benefit.

**Not a keeper candidate. There is nothing to promote, and nothing is proposed.**

---

## 1. The object, and the arithmetic that reduces it to one number

`reliability_floor_coeffs_NYISO.csv` rows 46–47, the `CH_ST_ev` ramp family:

| row | threshold | `floor_pct` | prose |
|---|---:|---:|---|
| 46 | 25.0 °C | 0.0000 | *"legacy CH weak hot-limb, base_ev=0 (no persistent base per CH data)"* |
| 47 | 38.0 °C | **0.3200** | *"legacy CH slope **0.0246/C** hot-limb to clamp @38C (>CH max 35.6); measured hot-day CF **regression**"* |

`model/interchange/core.py` composes a ramp family with `np.interp` over its knots, so the applied
fraction is

```
frac(T) = 0.3200 × (T − 25) / (38 − 25) = 0.024615 × (T − 25)
```

and, since CH's observed max tmax is **35.6 °C < 38 °C**, **the 0.3200 knot is never reached** — the
floor tops out at `0.024615 × 10.6 = 0.2609`. Conversely `0.0246 × 13 = 0.3198 → 0.320`. **The frozen
cap value and the prose slope are the same number written twice**, so identification reduces
entirely to the slope. *(Stated in PREREG §1.1 before any data was touched.)*

## 2. The instrument, and why its verdict is not arguable

The instrument is the **shipped script itself**, run with its own defaults — not a
re-implementation. Its printed `nyiso_st_floor_slope_per_c` is literally

```python
slope = np.polyfit(hot["tmax"] - 25.0, hot["cf"], 1)[0]     # hot = days with tmax >= 25 C
```

Run once, it emits all four zones. **Everything it prints for the two control zones matches the
frozen CSV to the digit** — including two numbers no census had ever checked:

| control quantity | frozen / prose | **nyiso-208** | |
|---|---:|---:|:---:|
| **NYC ST slope** | 0.0628 | **0.0628** | ✓ |
| **Long_Island ST slope** | 0.0424 | **0.0424** | ✓ |
| **downstate CT slope** | 0.0535 | **0.0535** | ✓ |
| NYC `base_ev` / `base_24h` / `cap` | 0.185 / 0.175 / 1.036 | 0.185 / 0.175 / 1.036 | ✓ |
| LI `base_ev` / `base_24h` / `cap` | 0.350 / 0.262 / 0.882 | 0.350 / 0.262 / 0.882 | ✓ |
| CT `base` / `cap` | 0.132 / 0.679 | 0.132 / 0.679 | ✓ |
| NYC evening Pearson r | +0.186 | **+0.186** | ✓ |
| LI evening Pearson r | +0.547 | **+0.547** | ✓ |

**P3 and P4 CONFIRMED.** Two independent cross-validations back this up: the percentiles agree with
nyiso-207's independently-written census, and this session's forced-energy sizing for the CH limb
comes out at **0.03035 TWh**, matching nyiso-207 §6's CH figure **to five decimals** from a
different instrument. A CH miss is therefore **CH's**, not the instrument's.

## 3. The result — and the pre-registered alternative that it refutes

**M1: Capital_Hudson hot-limb slope = `0.050219 /°C`. Frozen = `0.0246 /°C`. Ratio = 2.041.**

PREREG §5 declared two mutually exclusive outcomes and a third:

| prediction | window | measured | verdict |
|---|---|---:|:---:|
| **P1** — reproduces | \|slope − 0.0246\| ≤ 0.0010 | 0.0502 | **FALSE** |
| **P2** — guard-stale (*the one that cut against P1*) | slope **< 0.0200** | 0.0502 | **FALSE — and refuted in DIRECTION** |
| — | neither | — | **VERDICT U — UNIDENTIFIED** |

**P2 deserves its own sentence, because it was this session's own alternative and it is wrong twice
over.** It reasoned that rows 46–47 carry no *"re-derived 2026-07-26 on the guard-corrected outage
extract"* note where the NYC and LI ramp rows both do, so CH's value might be a pre-guard-fix
leftover — which would have made it **too high**. It is **too low**. And **M4 kills the mechanism
outright**: the outage derate reaches **26,208 of 26,304 CH hours (99.64 %)**, so the extract
emphatically *does* reach this fleet, and turning the derate off moves the slope only to
**0.0400** — still **1.63×** frozen. The vintage story explains neither the sign nor the size.

## 4. Nine constructions, and the minimum still overshoots by 1.63×

**M5 (pre-registered) — every span, shipped basis.** No span comes within **0.018** of frozen:

| span | 2023 | 2024 | 2025 | 2023–24 | 2024–25 | **2023–25 (shipped default)** |
|---|---:|---:|---:|---:|---:|---:|
| slope | 0.0443 | 0.0586 | 0.0474 | 0.0509 | 0.0535 | **0.0502** |
| hits ±0.0010? | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

**M4 + addendum A (POST-HOC, declared and committed before execution) — every basis.**

| variant | slope | ÷ frozen |
|---|---:|---:|
| shipped (`avail` basis) | 0.0502 | 2.04× |
| nameplate basis, derate off | **0.0400** | **1.63×** |
| A1 — CF clipped at the 1.0 physical bound | 0.0496 | 2.02× |
| A2 — nameplate basis + clip | 0.0400 | 1.63× |

Addendum A's own prediction — that clipping would move the slope **down** — is **CONFIRMED**, and it
is confirmed *trivially*: 0.0502 → 0.0496. The clip barely bites, because the CF > 1 readings are
not concentrated on hot days. **Reporting rule applied as written (addendum §A.4):** the census now
carries **seven** comparisons against a ±0.0010 window, **none hit**, and the honest reading is that
the multiple-comparison caveat never had to be invoked — there was nothing to caveat.

**The minimum over all nine measured constructions is 0.0400 — 1.63× the frozen 0.0246. No
construction this session could reach produces it.**

## 5. Why the CH regressand is pathological — and what that means

*(The distribution stats are labelled **POST-HOC DIAGNOSTIC** in the machine record. They explain a
number; they claim nothing.)*

Capital_Hudson's daily when-available evening CF is not a well-behaved regressand:

| | value |
|---|---:|
| days at CF exactly 0 | **60.4 %** |
| **hot** days at CF exactly 0 | **40.2 %** |
| days at CF > 1.0 | 2.28 % |
| max CF | **4.63** |
| Pearson r (CF, tmax) | **+0.041** |
| Spearman r | +0.104 |
| hot-day median CF / mild-day median CF | **0.311 / 0.000** |

Two readings follow, and they are compatible:

1. **The temperature response is real but it is a COMMITMENT response, not a loading-level one.**
   Hot-day median CF is 0.311 against a mild-day median of exactly **0.000** — a large effect — yet
   both correlations are near zero, because **40 % of hot days are also at zero**. The fleet's answer
   to heat is *whether it starts*, not *how hard it loads*. An OLS slope on daily CF is a poor
   estimator of that, which is a property of the shipped construction and not of this session's
   measurement. **This bears on pending owner ruling (i)** — nyiso-206's "is `floor_pct` an aggregate
   class-commitment share or a per-unit loading rule?" — and CH is a live instance where the
   distinction is not academic. **This session does not take that ruling.**
2. **CH is the marginal zone by the script's own stated test.** The docstring says it prints the
   Pearson r *"so a weak class (Capital) can be judged on the data, not forced"* — naming Capital
   explicitly. Ordered by that statistic:

   | zone | evening Pearson r | floored? |
   |---|---:|---|
   | Long_Island | **+0.547** | yes (ramp) |
   | NYC | **+0.186** | yes (ramp) |
   | **Capital_Hudson** | **+0.041** | **yes (ramp)** |
   | Upstate_West | −0.090 | **no** — *"flat vs temperature … printed for completeness, not floored"* |

   CH sits between the weakest floored zone and the one the script deliberately excludes, and its r
   is the only one of the three **never recorded** in the CSV prose (rows 46–47 leave `rho` empty,
   where rows 7 and 25 both state theirs). **This is an observation, not a proposal:** nothing here
   argues CH should be unfloored, and the hot/mild median split is large and real.

## 6. What cuts the OTHER way — both pre-registered, both PASS

### 6.1 P5 — the frozen floor does **not** exceed observed conduct. **PASS.**

Over 328 CH hot days: **64.6 %** meter at or above the applied `frac(tmax)`. The frozen floor
reaches **0.0812** at the median hot day (28.3 °C) and **0.2609** at the hottest observed day
(35.6 °C), against a hot-day median CF of **0.311** — so even at the top of the observed range the
floor sits **below** the class's own hot-day median. There is no rule-17 `[R-FLOOR-WINDOW]`
over-forcing defect here. *(At the measured 0.0502 slope the share falls to 61.3 %, and the floor at
35.6 °C would be **0.532** — well **above** the hot-day median.)*

### 6.2 P6 — the h14–21 window is correct for this zone. **PASS, decisively.**

The charter's alternative object was to audit the CH ramp family's **window** against its own driver
evidence, since the h14–21 block has never had the nyiso-203 §3 block-CF treatment on this zone.
It does now. Hot-day median when-available CF by block:

```
h00-03  0.000  ▏
h04-07  0.022  ▎
h08-11  0.137  ██▎
h12-15  0.283  ████▊
h16-19  0.321  █████▍   <- peak, inside the window
h20-23  0.206  ███▌
```

Median inside h14–21 = **0.298**; outside = **0.066**; **ratio 4.49×** against a pre-registered
threshold of 1.5×. **The window selects exactly the block the zone actually runs.** Clean negative:
no window defect, and this object should not be re-opened.

## 7. Size — and why the direction of the gap matters more than its magnitude

Pooled 2023–2025, over the limb's own h14–21 hours (`frac × available MW`; **not** an LP result —
the model's *added* energy also depends on what the LP would have dispatched anyway):

| | frozen slope 0.0246 | measured slope 0.0502 | change |
|---|---:|---:|---:|
| floor energy demanded | 0.334 TWh | 0.607 TWh | **1.82×** |
| **excess over metered** | **0.030 TWh** | **0.072 TWh** | **2.39×** |
| metered CH evening energy | 2.358 TWh | — | — |

**The decision-relevant asymmetry:** nyiso-207's construction gap, if repaired, would **reduce**
forcing (−0.068 TWh on the largest live evening limb). This one, if "repaired" toward its own named
construction, would **increase** it — an extra **+0.042 TWh** of forcing on a limb that currently
sits below its class's observed conduct and passes both structural gates. **The two open coefficient
questions push in opposite directions**, and that fact belongs on the owner's desk more than either
magnitude does.

## 8. What is deliberately NOT taken — named so silence is not read as absence

- **No coefficient is edited and no replacement value is proposed.** `0.0502`, `0.0400`, `0.0496`
  are **measurements of the gap**, never candidate values — PREREG §7 and addendum §A.4 bound this
  in **every** branch, including before the numbers were seen. Rule 23 `[R-FROZEN-DERIVE]` has no
  source-data trigger (no source data has updated), and whether a construction repair is an adequate
  identification under rule 21 `[R-DOF]` is an **owner** call, exactly as nyiso-203 §7 reason 2 and
  nyiso-207 §7 held.
- **No derive script is changed**, and neither is `_apply_frac` or any `ScenarioConfig` field.
- **No other ISO is measured** (rule 25 `[R-ISO-SCOPE]`). Both scripts have per-ISO siblings whose
  slopes are equally untested; that exposure is **unmeasured and was not measured here**.
- **One hypothesis is left explicitly UNTESTED, by the PREREG's own binding.** A pre-2023
  identification span would explain the gap, and testing it means reading `NY_2019/2020/2021/2022`.
  PREREG §7 declared those extracts would not be read, and they were not. This is named on the card
  as the leading untested explanation rather than resolved here.
- **No metrics file, price series, volume residual or scored criterion was opened at any point.**
  The `offer_curve_by_group` channel is owner court under carve-out condition (c) and was not
  touched.
- **The four pending owner rulings are untouched** — nyiso-206 (i), nyiso-207 (ii), nyiso-203 §6
  (iii), `DECISION-CARD-nyiso193` §5/§5.1 (iv). §5 notes that CH bears on (i); it does not rule it.
- **Rule 20 `[R-FORCED-BUDGET]` leg (a) stays open**; the unit-grain C8 exposure (ST_GAS 0.351 /
  0.343 / 0.268 against the 0.30 cap) is unchanged.
- **No marker is touched.** `complete` (WITHDRAWN, Q5) and `frontier` re-entry are owner acts;
  C-19 / Q51 stays **PARKED**.

## 9. Governance

| item | state |
|---|---|
| **LP spent** | **none.** Rule 29 step 0 gated it; no arm was on the table, so no screen year was pre-registered |
| **Rule 29(b) G-DRIFT** | **re-validated EMPIRICALLY at this HEAD, not by reading hunks:** `scripts/probes/nyiso198_rebuild_checks.py --year 2024` re-run leaves `git status --porcelain -uno` **EMPTY** — the committed `_nyiso198_rebuild_checks_2024.json` regenerates byte-identically. G-CTRL **form 4** valid; **no control solve spent**, and none could be owed since nothing was differenced against a solve. *(That probe prints its own `"VERDICT": "STOP"` — the adjudicated nyiso-198 duct-peaking gate, an `R` cell; part of the committed record, **not** a drift signal.)* |
| **Keeper** | `2026-09-06-nyiso-202-startup-aware`, **UNCHANGED**. Not a keeper candidate; no promotion, no re-stamp, no `build_status` / `prune_iso_runs` / gate-(a) re-key owed |
| **Rule 1 `[R-STRUCT]`** | no mechanism selected on a residual; none selected at all. NYISO reads **fails 0** and C3c was not an objective |
| **Rule 21 / 23** | zero fields, zero DOF entries, **zero re-derivations into any artifact**. Every frozen coefficient was read and none written |
| **Rule 22 `[R-HOLDOUT]`** | 2023–2025 only. No out-of-training year solved, scored or registered — and, by the PREREG's own binding, the out-of-training CAMPD extracts were **not read at all** |
| **Rule 25 `[R-ISO-SCOPE]`** | NYISO only |
| **Rule 26 / 28 `[R-MECH-MATRIX]`** | NYISO shard `reliability_floor` cell updated **in this session**; key set verified identical to `main` before commit |
| **Rule 15 `[R-DASHBOARD]`** | nothing registered — no run finished, so there is no run. Git history + this finding + the card are the record |
| **Rule 29(c)** | no screen bundle and no control bundle exist, so there is nothing to delete before merge |
| **Files added** | 1 probe, 2 JSON records, 1 PREREG + 1 POST-HOC addendum, this finding, 1 decision card. **No `src/market_sim/` change, no CSV edit, no derive-script edit, no scorer edit** |

### 9.1 Reported, not fixed — other lanes' pre-existing failures at HEAD

**Re-measured** at this session's HEAD (this session's tracked changes are additive only — a new
probe plus docs and records; no tracked file that could affect them was modified):
**37 failed / 68 passed** — **identical to nyiso-207 and nyiso-206, file for file**, so `main` has
not moved on these.

| file | failures | owner |
|---|---:|---|
| `tests/unit/model/test_d62_published_going_forward_bar.py` | 15 | capx |
| `tests/unit/model/test_d74_no_default_cap_convention.py` | 12 | capx |
| `tests/scoring/test_ff_readiness_battery.py` | 4 | FF-readiness |
| `tests/scoring/test_collate_scenario_campaign_common_set.py` | 4 | SCN-WS5A-LOAD |
| `tests/regression/test_constants_facade.py::test_moved_surface_is_complete` | 1 | — |
| `tests/unit/data/test_caiso_st_gas_peak_measured.py` | 1 | CAISO |

**Not fixed from this lane** (rule 25): none is NYISO's file or NYISO's number.

## 10. What this closes, what stays open

**Closed — DO-NOT-REDO.** Every live NYISO ramp **slope** is now reproduced or measured as
unreproducible; three of four match to four decimals. The CH `CH_ST_ev` **window** is audited
against its own block-CF driver evidence and is **correct** (4.49×, peak inside) — a **clean
negative** that should not be re-opened. The CH slope's **span** and **denominator-basis**
explanations are ruled out (nine constructions, minimum 1.63× frozen). Together with nyiso-207's
percentile census, **every live NYISO floor coefficient has now been tested against its own stated
construction**, and exactly one fails.

**Established (positive).** The shipped derive scripts are faithful: nine of ten live coefficients,
plus both recorded Pearson r values, regenerate byte-exactly at HEAD from committed source data. The
NYISO floor derivation pipeline is **not** drifting — which is what makes the tenth row a real
finding rather than noise.

**Open.** The identification of `CH_ST_ev`'s 0.0246/°C, handed to the owner in
`docs/DECISION-CARD-nyiso208-ch-ramp-slope-2026-09-06.md`, with the pre-2023-span hypothesis named
and deliberately untested. Rule 20 `[R-FORCED-BUDGET]` leg (a) and the unit-grain C8 exposure are
unchanged. `DECISION-CARD-nyiso193`, `-nyiso206` and `-nyiso207` all remain **UNRULED**.

---

*(nyiso-208, 2026-09-06. Zero LP. An instrument validated to four decimals on three controls, one
coefficient that does not reproduce under any of nine constructions, this session's own alternative
hypothesis refuted in direction, and two structural gates passed that cut against the finding —
reported as passing.)*
