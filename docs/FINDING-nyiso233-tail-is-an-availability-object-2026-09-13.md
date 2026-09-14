# FINDING — OBJECT A: NYISO's price tail is an **AVAILABILITY** object, not a price-formation one. The model is **not short** in the hours the real market priced highest, and its own offer stack already reaches those prices

**Session** nyiso-233 · **Date** 2026-09-13 · **ZERO LP**. Every number is read from the designated
keeper's committed `hourly/` sidecars (`2026-09-13-nyiso-232-st-gas`) and the committed validation
actuals `data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet`. **The tail is selected on the
ACTUAL series only**, so the model's own behaviour can never choose the hours it is judged on.

**No mechanism is proposed, armed, or tested here, and no matrix cell moves.** This is the phase-0
that has to come first (rule 1 `[R-STRUCT]`): it decides which *family* of mechanism could possibly
be right, before anyone spends a solve on one.

---

## 1. THE QUESTION, AND WHY IT HAD TO BE ASKED FIRST

nyiso-232 established that NYISO's C3a residual is **two separable objects**
(`docs/FINDING-nyiso232-c3a-is-two-objects-2026-09-13.md`): strip each year's top actual-price hours
and the model is **over**-priced by +4.1 to +14.2 % in all four years. The headline C3a is therefore
a **difference of two large errors of opposite sign**, and any mechanism that lifts ordinary-hour
prices to close C3a makes the tail worse. A tail mechanism must raise the **tail** without raising
ordinary hours.

Two families could do that, and they are mutually exclusive:

* **PRICE FORMATION** — the model reproduces the physical scarcity but prices it too cheaply (ORDC,
  reserve demand curve, VOLL shape, RCPF). Only works if something is actually binding.
* **AVAILABILITY** — the model's fleet is more available than reality's was, so it never becomes
  scarce at all. Then a steeper scarcity curve prices nothing, because nothing binds.

## 2. THE ANSWER: THE MODEL IS NOT SHORT

Top 1 % of hours by **actual** RT price (88 h/yr). `spare MW` is `cap_mw − mw` summed over
classified thermal units, averaged over those hours:

| year | actual $/MWh | model $/MWh | reserve shortfall MW | hrs with any shortfall | **spare thermal MW** | **spare %** | slack |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2022 | 572.90 | 108.76 | 5.2 | 2 / 88 | **5,866** | **29.5 %** | **0.00** |
| 2023 | 216.60 | 57.17 | 43.2 | 12 / 88 | **6,247** | **29.6 %** | **0.00** |
| 2024 | 228.57 | 68.09 | 0.0 | 0 / 88 | **4,684** | **23.8 %** | **0.00** |
| 2025 | 446.49 | 146.44 | 141.8 | 25 / 88 | **3,390** | **16.3 %** | **0.00** |

**Zero slack in every hour of every year, near-zero reserve shortfall, and 3.4–6.2 GW of thermal
capacity sitting idle** while the real market cleared at $573 (2022) and $446 (2025).

**Robust across tail depth** — the conclusion does not depend on where the tail is cut:

| depth | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| top 0.5 % (44 h) | 6,266 MW / 31.8 % | 5,555 / 25.9 % | 4,552 / 22.4 % | 2,414 / 10.9 % |
| top 1 % (88 h) | 5,866 / 29.5 % | 6,247 / 29.6 % | 4,684 / 23.8 % | 3,390 / 16.3 % |
| top 2 % (175 h) | 6,066 / 30.7 % | 6,312 / 30.4 % | 4,949 / 25.7 % | 4,253 / 21.3 % |
| top 5 % (438 h) | 5,831 / 29.6 % | 6,475 / 32.1 % | 5,488 / 28.7 % | 5,071 / 26.4 % |

Slack is **exactly 0.00 in all 16 cells**. The tightest case in the whole study is 2025's top 0.5 %,
where the model still carries **2,414 MW idle (10.9 %)** against an actual of $642/MWh.

## 3. AND THE STACK IS NOT THE LIMIT — which rules out the obvious objection

The natural objection is that the model simply has no offers up there, so no amount of derating could
reach the observed price. **Measured, it is false.** In the same top-1 % hours:

| year | actual $/MWh | idle thermal MW | **of which priced ≤ actual** | max thermal mc $/MWh |
|---|---:|---:|---:|---:|
| 2022 | 572.90 | 5,866 | **5,507 (94 %)** | 1,229.6 |
| 2023 | 216.60 | 6,247 | **5,972 (96 %)** | 490.5 |
| 2024 | 228.57 | 4,684 | **4,162 (89 %)** | 746.1 |
| 2025 | 446.49 | 3,390 | **2,798 (83 %)** | 1,890.5 |

The model's own thermal offer stack **already extends above the observed price in every year**, and
**83–96 % of the idle capacity is offered at or below the price the real market actually paid**.
The depth is there. What is absent is the **scarcity** that would climb into it: the model's demand
is met with gigawatts to spare, so the marginal unit never gets near the top of its own stack.

**This is the whole finding in one line: the model is not mispricing scarcity, it is not experiencing
scarcity.**

## 4. WHAT THE TAIL IS MADE OF — extreme events of both seasons

Worst 5 days per year, by summed load-weighted gap:

| year | worst days | share of annual gap |
|---|---|---|
| 2022 | **Dec 24, Dec 23** (Winter Storm Elliott), Jan 16, Dec 26, Aug 08 | 49.3 % |
| 2023 | **Feb 04, Feb 03** (Arctic outbreak), **Sep 05, Sep 06** (Sep heat), Jan 11 | — see note |
| 2024 | **Dec 22, Dec 21, Dec 23** (winter), Jun 17, Jul 31 (summer) | — see note |
| 2025 | **Jun 24, Jun 23, Jun 25** (June heat dome), Jul 01, Jul 29 | 57.5 % |

**Note on the missing percentages, stated rather than quoted:** in 2023 and 2024 the *annual*
load-weighted gap is near zero (C3a −1.26 % and −0.75 %), so "share of the annual gap" exceeds
100 % and is numerically unstable — a small denominator, not a large tail. That instability **is**
the two-objects structure: the tail deficit and the ordinary-hour surplus nearly cancel. The
percentage is reported for 2022 and 2025 only, where the denominator is meaningful.

The events are **both winter cold snaps and summer heat**, which is a constraint on any candidate
mechanism: a winter-only story does not cover 2025, and a summer-only story does not cover 2022.

## 5. WHAT THIS MEANS FOR THE LEVER QUEUE — and what rule 28(a) says about it

The measurement **de-prioritises the price-formation family** for this object. ORDC / RCPF / reserve
demand-curve work cannot close a gap in hours where the reserve requirement is met, slack is zero and
3–6 GW sits idle: there is nothing for a steeper curve to price. That is a statement about *this*
object only — it says nothing about whether NYISO's reserve mechanisms are otherwise right.

It **points at** availability: outage depth, ambient/temperature derates, correlated forced outages,
gas deliverability to the downstate fleet in cold snaps, and energy limits.

**The matrix was checked before any of that was written down** (rule 28(a) DO-NOT-REDO,
`docs/codebase-site/data/mechanism-matrix/NYISO.js`):

| cell | NYISO verdict | note |
|---|---|---|
| `temp_dependent_derate` | **G** (governance-refused) | nyiso-111, **ex-ante refusal on NYISO's own conduct, no solve** |
| `gas_coldsnap_derate` | `.` | not applicable for NYISO as the row stands |
| `winter_fuelsec_posture` | `.` | — |
| `correlated_forced_outage` | `.` (fc `I`) | — |
| `ordc_scarcity_overlay` | `.` | — |
| `nyiso_iroquois_winter_spread` | tested & rejected-as-armed | nyiso-150, on its own pre-registered gates |
| `dual_fuel_switching` | line closed as the ST_GAS dear-hour lever | nyiso-179, rule 19 `[R-ONE-MECH]` |

**This session re-opens none of them.** The disciplined statement is that §2–§3 is **new evidence**
that did not exist when `temp_dependent_derate` was refused ex-ante, and the G cell's refusal basis
should be **re-read against it** before that cell is either re-opened or left closed. Re-reading a
refusal is the owner's call and a separate session's work; asserting the refusal was wrong on the
strength of a residual would be exactly the move rule 1 forbids.

## 6. WHAT THIS DOES NOT CLAIM

* It does **not** claim the model's availability inputs are wrong. It claims the model is **not
  short** in these hours — which is a measurement — and that a price-formation mechanism therefore
  has nothing to bind on. Whether the correct repair is outage depth, derates, fuel deliverability,
  energy limits, or something else is **not** decided here.
* It does **not** claim reality's scarcity was purely physical. NYISO's RT price in a cold snap is
  partly set by administrative scarcity pricing, and some of the $573 is that. §3 shows the model's
  stack *could* reach the level physically; it does not prove reality reached it that way.
* It does **not** touch C3a. Closing the tail would make the **ordinary-hour over-pricing** the
  visible residual, since the two currently cancel — that is the point of the two-objects finding
  and is a reason to expect C3a to get **worse** before it gets better.
* Object B (the ~10.1–10.8 pp gas-monotone tilt that survives tail removal) is **untouched** and
  still open.

## 7. RULES

1 `[R-STRUCT]` — the fork is decided by what the model is doing, never by what would improve the
residual; a mechanism family is de-prioritised on measurement, not on fit. 13 `[R-MEASURED]` — the
tail is selected on the actual series, so no model outcome selects its own test.
28 `[R-MECH-MATRIX]` (a) — the queue and the adjudicated cells were read before anything was
proposed, and no `R`/`I`/`G` cell is re-tested. 32 `[R-SHARD]` — zero LP.

Probe: `scripts/probes/_nyiso233_tail_mechanism_census.py` (argument = tail depth in %).
