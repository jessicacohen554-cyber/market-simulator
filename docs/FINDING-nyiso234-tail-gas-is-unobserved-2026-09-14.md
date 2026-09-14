# FINDING — nyiso-234: the availability family is closed by ARITHMETIC, and NYISO's price tail sits on gas the model never observed

**Session** nyiso-234 · **Date** 2026-09-14 · **ZERO LP.** Nothing armed, no cell promoted,
keeper **UNCHANGED** at `2026-09-13-nyiso-232-st-gas`.

Every number is read from committed artifacts: the keeper's `hourly/system_<year>.parquet`, the
validation actuals `data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet`, the committed
gas corpus under `data/raw/gas-prices/`, and the keeper's **own code path** for the delivered gas
series (`data/fuel/hubs.py::_nyiso_hub_daily_gas_prices`, called directly — never reconstructed by
hand). The tail is selected on the **ACTUAL** series only, so no model outcome chooses the hours it
is judged on.

Probes: `scripts/probes/_nyiso234_tail_season_reach.py`,
`scripts/probes/_nyiso234_gas_coverage_tail.py` (both take tail depth in % as their argument).

---

## 0. HEADLINE — three results, in the order they have to be read

1. **The `temp_dependent_derate` G cell STAYS G.** nyiso-233's headroom measurement is new
   evidence about the **object**, but it does not defeat nyiso-111's **refusal basis**, which was
   *identification* — and it adds a second, independent bar the refusal never needed:
   the committed curve is **identically 1.0 in cold hours**, so it cannot reach
   **15.8 – 79.8 %** of the object at **any** slope.
2. **The whole availability family is closed, and it is closed by ARITHMETIC, not by
   identification.** Putting nyiso-227 beside nyiso-233 for the first time: the largest measured
   sub-5-day outage instrument NYISO owns peaks at **1.65 – 2.35 GW**, against **3.39 – 6.25 GW**
   of idle thermal in the tail hours. Every availability instrument in the repo is **2–3× too
   small** to make the model short.
3. **The fork nyiso-233 §6 left open is the live one, and it is an INPUT defect.** In 2022's tail,
   **69.8 %** of the gap falls on calendar dates for which the committed daily gas series **has no
   row at all**. On Elliott — Dec 23–24 2022, the top two gap days, **47.7 %** of the year's tail
   gap between them — the model burns gas at **$8.05/MMBtu, its own annual median**, flat for
   eleven days.

**Nothing here is a mechanism proposal.** (3) is a rule 14 `[R-ACCURATE]` input-coverage gap whose
repair is a **data intake**, and the intake is an owner decision — `docs/DECISION-CARD-nyiso234-tail-gas-coverage-2026-09-14.md`.

---

## 1. THE G-CELL RULING (the session's first task, and it is not a solve)

### 1.1 What nyiso-111 §2 actually refused, and on what basis

`results/calibration/FINDING-nyiso111-ramp-envelopes-2026-08-02.md` §2 refused
`temp_dependent_derate` for NYISO **ex ante, with no solve**, taking the miso-101 route (derive the
slope from the target ISO's own fleet, because rule 25 `[R-ISO-SCOPE]` forbids importing the
literature values and pjm-95 refuted them on PJM's CAMPD). `derive_campd_temp_derate_params.py
--iso NYISO` over NY CAMPD 2023–2025 failed on **four independent grounds, any one decisive**:

| # | ground | NYISO measurement |
|---|---|---|
| a | identifiable plants | **2 of 15** candidates (East River NYC, Nissequogue LI); MISO had 6 |
| b | class parameter | **−0.00745/°C — capability RISING with temperature**, physically impossible for a gas turbine |
| c | pinned-plant premise | East River loading ratio **0.5995** (dispatch freedom, so its within-day shape *is* dispatch); the near-pinned plant measures **−0.000086 at r = 0.006** — no response at all |
| d | phase validation | best lag **−5 h** (r = +0.289) vs lag 0 (r = +0.088); a physical ambient response is contemporaneous, a 5-hour **lead** is a load shape |

**The verdict was `REFUSED on identification (U → G), not rejected on fit.**" And it named its own
re-open condition, verbatim: *"A future intake with an actual capability instrument (unit DMNC test
results, or a plant pinned at capability) would be a new identification and could re-open the
cell."*

### 1.2 Does nyiso-233's headroom measurement defeat that basis? — **NO.**

The refusal is about whether NYISO's data can **measure a slope**. nyiso-233 measured a **residual**
— 3.4–6.2 GW of idle thermal in the tail. That is a statement of **motive**, not of
**identification**, and the re-open condition nyiso-111 itself set (a DMNC record, or a plant pinned
at capability) is **unmet**: nyiso-233 introduced no capability instrument, and none has been taken
into the repo since.

Arming on the strength of a residual, with the slope still unidentified, is precisely the move
rule 1 `[R-STRUCT]` forbids — *"never reach the right number through a mechanism that isn't real"* —
and rule 21 `[R-DOF]` would have no identification source to write in the ledger. **The refusal
stands undefeated on its own terms.**

### 1.3 A SECOND, INDEPENDENT BAR the refusal never needed: the curve cannot reach the object

Even granting identification *arguendo*, the mechanism still cannot address this object, and that
is a property of the **committed code**, not a fit judgement. `data/fleet/arrays.py` evaluates
exactly two forms, and **neither derates a cold hour**:

* **hinge form** (`temp_derate_mean_anchored` False, the default) —
  `raw = 1 − slope · max(0, Tmax − temp_derate_ref_c)` with `temp_derate_ref_c = 15.0 °C`
  (`scenarios.py:14710`). At `Tmax ≤ 15 °C` the curve is **exactly 1.0**.
* **mean-anchored form** — `raw = 1 − slope · (Tmax − mean(Tmax))`, which for `Tmax < mean`
  **exceeds** 1.0 and is then clipped back to 1.0 by `np.clip(availability, 0, 1)`.

So the share of the tail gap lying below the hinge is a **ceiling on the mechanism's reach at any
slope**. Measured on the actual-selected tail, taking the **warmest zone** per hour (the most
generous possible reading — the curve is evaluated per zone, so a hour escapes the dead zone if
*any* zone is above the hinge, which makes every number below a **lower bound**):

| year | tail h | DJF h | DJF % of gap | JJAS h | JJAS % of gap | Tmax ≤ 15 °C h | **DEAD % of gap** |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2022 | 88 | 60 | 76.2 | 22 | 19.0 | 64 | **79.8** |
| 2023 | 88 | 45 | 46.0 | 31 | 42.9 | 48 | **49.4** |
| 2024 | 88 | 57 | 36.1 | 25 | 53.1 | 60 | **38.4** |
| 2025 | 88 | 39 | 15.3 | 45 | 82.3 | 40 | **15.8** |

**Robust across depth** (the dead share, top 0.5 / 1 / 2 / 5 %):

| year | 0.5 % | 1 % | 2 % | 5 % |
|---|---:|---:|---:|---:|
| 2022 | 85.7 | 79.8 | 78.5 | 77.4 |
| 2023 | 45.1 | 49.4 | 49.9 | 48.1 |
| 2024 | 24.9 | 38.4 | 46.9 | 50.5 |
| 2025 | 4.7 | 15.8 | 23.9 | 38.7 |

**In 2022 — the only year that actually fails C3a — the mechanism cannot touch 77–86 % of the
object at every depth.** Only 2025's shallow tail is a genuinely summer object, and 2025 already
passes C3a.

### 1.4 Ruling

**The cell stays `G`, on both legs.** The evidence string is sharpened (the reach bar is new and
did not exist at nyiso-111), the verdict does not move, and **nothing was armed.** Recorded to the
NYISO shard per rule 28(b).

This is deliberately **not** routed to a `.` neighbour. §2 says why that route is closed too.

---

## 2. THE AVAILABILITY FAMILY IS CLOSED BY ARITHMETIC

nyiso-233 §5 pointed at availability — *"outage depth, ambient/temperature derates, correlated
forced outages, gas deliverability … and energy limits."* That pointer is **correct about the kind
of object and does not survive as a lever recommendation**, and the reason is a number nobody had
put beside it.

**nyiso-227** (2026-09-11, `docs/FINDING-nyiso227-shortgas-outage-inert-2026-09-11.md`) derived
NYISO's own sub-5-day gas outage family and measured it **near-inert**, three days before nyiso-233
was written:

> 438 windows, 38 plants, 77 units, median duration 2.6 d. Annual-mean removed **208.2 / 191.5 /
> 280.7 MW**; **peak 2,351.0 / 1,653.1 / 1,800.0 MW**. Hours the extra removal could bind, on
> ST_GAS: **0 / 0 / 0 of 8,760**. *"The family would have to be roughly 20× larger to touch it."*

The coverage gap it names is **total**, not partial: `unit_outage_short_windows` is `False` in the
keeper and NYISO's coal-scoped short extract is header-only (NYISO has no coal), so the sub-5-day
layer is **empty**. And the parent overlay cannot fill it — the committed extract
`campd-unit-outages-perunitmerit-NYISO.csv` has **`min(duration_days) = 5.000` and ZERO of its
3,717 windows shorter than 5 days** (`outages.py::UNIT_OUTAGE_MIN_DAYS = 5`). Every extreme event
nyiso-233 named — Elliott Dec 23–24 2022, Feb 3–4 2023, Dec 21–23 2024, Jun 23–25 2025 — is
**shorter than the extract's minimum detectable window.**

**Put the two sessions together, which neither did:**

| | measured | source |
|---|---:|---|
| model's idle thermal in the tail hours | **3,390 – 6,247 MW** | nyiso-233 §2 |
| peak of the entire measured sub-5-day gas outage family | **1,653 – 2,351 MW** | nyiso-227 §1 |
| `temp_dependent_derate` reach in the tail | **unidentified, and 0 below 15 °C** | §1 above |

**The largest availability instrument NYISO owns is 2–3× smaller than the headroom it would have to
eat**, and it must eat that headroom *before* it removes a single MW the model is actually using.
So no availability instrument in this repository can make the model short in these hours. That
closes the family on **reach**, the same way miso-139 closed the temp-derate family for MISO — on
arithmetic, not on fit and not on identification.

**This does not overturn nyiso-233.** Its measurement stands exactly as made: the model is not
short, and a price-formation mechanism has nothing to bind on. What §2 adds is that the *other*
branch of its fork is closed too — which forces the third reading, the one nyiso-233 §6 flagged
and did not test.

---

## 3. THE LIVE FORK: reality may not have been short either

nyiso-233 §6 stated it and declined to test it:

> *"It does not claim reality's scarcity was purely physical. NYISO's RT price in a cold snap is
> partly set by administrative scarcity pricing, and some of the $573 is that."*

There is a third possibility beside "the model has too much capacity" and "the model prices
scarcity too cheaply": **the real market was not physically short either, and cleared at
$573 because its marginal unit was burning extremely expensive gas.** That is not a scarcity
question at all — it is a **fuel price** question, and it is answerable from committed artifacts.

It also has the one property nyiso-232 proved a tail mechanism must have. Because the hub overlay
**supersedes** the monthly level in covered months (`hubs.py::_hub_overlay_series`, and
`trajectories.py::_electric_power_level_series`' own docstring: *"is itself superseded in covered
months by the measured constrained-hub index applied immediately after"*), a repair to the tail
days' gas price carries **no compensating re-level onto ordinary days**. It raises the tail and
leaves ordinary hours alone — which is exactly nyiso-232's requirement, met **structurally rather
than by tuning**.

*(A redistribution story — the monthly anchor pushing the missing extreme-day cost onto ordinary
December days, which would have tied both of nyiso-232's objects to one defect — was hypothesised
and is **FALSE**. The code above contradicts it and it is dropped rather than told.)*

---

## 4. THE MEASUREMENT: the tail sits on dates the gas series never observed

The model's NYISO delivered gas is built by `_nyiso_hub_daily_gas_prices`, reached under the
keeper's `gas_hub_basis_overlay = True` + `gas_hub_basis_daily = True`. Its source is
`data/raw/gas-prices/transco_z6_ny_daily.csv` — a **trading-day** series, 1,858 rows over 2018–2025
(~232/yr against ~365 calendar days). Non-trading days are filled by a **mean-preserving**
interpolation of the daily shape factors, renormalized so the month's mean equals the monthly hub
level.

**Both halves of that construction are blind to an event that falls entirely inside a non-trading
stretch** — the shape has no print to place, and the monthly level is computed only over observed
days.

### 4.1 Share of the tail gap falling on dates with NO row in the source

| year | tail h | unobserved h | **% of gap unobserved** | gas in tail $/MMBtu | year median | year max |
|---|---:|---:|---:|---:|---:|---:|
| 2022 | 88 | 49 | **69.8** | 10.05 | 8.05 | 23.36 |
| 2023 | 88 | 36 | **29.0** | 4.16 | 3.09 | 44.53 |
| 2024 | 88 | 55 | **66.8** | 4.95 | 2.28 | 22.84 |
| 2025 | 88 | 16 | **15.8** | 8.88 | 4.36 | 84.97 |

**Robust across depth** (% of gap unobserved, top 0.5 / 1 / 2 / 5 %):

| year | 0.5 % | 1 % | 2 % | 5 % |
|---|---:|---:|---:|---:|
| 2022 | 78.6 | 69.8 | 64.1 | 56.1 |
| 2023 | 17.5 | 29.0 | 30.6 | 31.0 |
| 2024 | 70.0 | 66.8 | 67.6 | 65.8 |
| 2025 | 13.9 | 15.8 | 16.1 | 18.0 |

### 4.2 2022, named rather than summarised

The three days carrying the most tail gap, and the gas the model burnt on them:

| date | share of 2022 tail gap | model gas $/MMBtu | observed? |
|---|---:|---:|---|
| **2022-12-24** (Elliott) | **33.8 %** | **8.05** | **NO ROW** |
| **2022-12-23** (Elliott) | **13.9 %** | **8.05** | **NO ROW** |
| 2022-01-16 | 7.6 % | 10.79 | **NO ROW** |

**55.3 % of 2022's tail gap on three days, none of which the gas series observes.** The model's
December 2022 gas is **flat at $8.05/MMBtu for eleven consecutive days, Dec 21 – Dec 31** — and
$8.05 is the year's own **median**. On the single largest gas event in Northeast history, the model
burns median-priced gas.

The mechanism works correctly where data exists: Dec 16 2022 carries a real $15.10 print and the
model prices that day at **$19.32**. The defect is the **coverage hole**, not the construction.

### 4.3 The holes are systematic, and they land on the events

Every multi-day gap ≥ 4 calendar days, 2022–2025, is a US holiday or holiday weekend. **Every year
carries a 14–15 day hole spanning Christmas–New Year:**

| window | length |
|---|---:|
| 2022-12-21 → 2023-01-04 | **14 d** |
| 2023-12-20 → 2024-01-04 | **15 d** |
| 2024-12-18 → 2025-01-02 | **15 d** |
| 2025-12-17 → 2025-12-31 | **14 d** |

plus 7-day Thanksgiving holes each year and multi-day summer holes (2024-06-12 → 06-20, 8 d;
2025-06-11 → 06-20, 9 d; 2025-06-25 → 07-03, 8 d).

**These align with the measured tail hour-for-hour.** 2024's named events (Dec 21–23) fall inside
the 15-day December hole — 66.8 % unobserved. 2025's named events (Jun 23–25) fall in a covered
stretch — 15.8 % unobserved, the lowest of the four years. The coverage number is not an artifact
of how the tail was cut; it tracks which events the calendar happened to hide.

### 4.4 There is NO committed cross-check, and that is itself a result

* `transco_z6_iroquois_monthly.csv` is **not independent** — its Dec-2022 value of **$7.3200** is
  *exactly* the mean of the 15 surviving daily observations, to four decimal places. Same source,
  same hole.
* `algonquin_citygate_daily.csv` — the committed NEISO series for the same region and the same
  event — has the **same hole**, last printing **$6.51 on 2022-12-21**.
* No other `$/MMBtu` daily series in `data/raw/` covers the Northeast.

**No committed source in this repository observes Winter Storm Elliott.** This is therefore not a
wiring bug to fix in code — it is a **data intake**, and that is an owner decision.

---

## 5. WHAT THIS DOES AND DOES NOT CLAIM

**It claims**, all measured: the tail gap concentrates on dates the gas series does not observe
(15.8–69.8 %, 56–79 % in 2022); the fill there is the year's median; the holes are systematic and
land on the named events; no committed source can price them; and the hub overlay's supersession
order means a repair would raise the tail **without** re-levelling ordinary hours.

**It does NOT claim** that repairing the input closes C3a, or by how much. **No committed source
carries the missing prints, so the magnitude is unmeasured and is deliberately not estimated** —
inventing a number for Elliott's gas price would be exactly the magic number rule 5
`[R-NO-MAGIC]` forbids, and sizing it against the residual would be the fitted-mechanism selection
rule 1 `[R-STRUCT]` forbids. **The intake must land before the effect can be measured.**

**The response is bounded by machinery that is already built and already armed.**
`dual_fuel_switching = True` and `dual_fuel_oil_daily_parity = True` on the keeper, and
`dual_fuel.py::apply_dual_fuel_pricing` caps a dual-fuel unit at `min(gas_mc, oil_mc)` — applied
*after* the hub overlay by construction. A repaired gas price cannot run away: the downstate
dual-fuel fleet re-prices to **oil parity**, which is what those units actually did in Elliott.

**One observation, explicitly NOT a result:** 2022 has the highest annual gas ($6.45), the worst
C3a (−11.6 %) and the highest unobserved share (69.8 %), which is *consistent with* Object B's
gas-monotone tilt (r vs gas −0.92 to −0.99). With n = 4 that is an observation and nothing more; it
is recorded so the next session can test it properly, not offered as evidence.

---

## 6. RULES

1 `[R-STRUCT]` — the G cell is ruled on identification and reach, never on what would improve the
residual; no mechanism is armed and no parameter is sized against a gate.
5 `[R-NO-MAGIC]` — the unobserved gas price is left unmeasured rather than invented.
13 `[R-MEASURED]` — the tail is selected on the actual series; the proposed repair is a measured
input with a forward analogue (a complete daily series regenerates for any year), never an outcome
fed back in.
14 `[R-ACCURATE]` — the object is an accurate input the model does not have; §4.4 establishes it
cannot be reconciled from anything committed.
19 `[R-ONE-MECH]` — what already owns each phenomenon was enumerated before anything was proposed:
daily gas basis is **already armed** (`gas_hub_basis_daily`), so a "gas granularity" mechanism was
ruled out at phase 0; short-duration outages are owned by the flat statistical WEFOR
(`wefor_multiplier = 0.7`, `wefor_residual = None`).
28 `[R-MECH-MATRIX]` (a) — the NYISO shard and §5.5 queue were read before anything was proposed;
`unit_outage_short_windows_gas` (`I`, nyiso-227), `unit_outage_short_windows` (`I`, nyiso-93/173),
`nyiso_iroquois_winter_spread` (`R`, nyiso-150/157) and `dual_fuel_switching` (closed, nyiso-179)
were **not** re-tested. (b) — `temp_dependent_derate`'s cell is re-stamped this session with the
new reach bar.
29 `[R-SCREEN]` (0) — zero-LP phase 0 killed two candidate families before any solve was requested.
32 `[R-SHARD]` — **the parent ran zero LP. No shard was launched, because there is nothing to solve
until the intake lands.**
