# DECISION CARD — nyiso-234: the G-cell re-read, and whether to fund the gas-price intake

**Session** nyiso-234 · **Date** 2026-09-14 · **ZERO LP.** Keeper **UNCHANGED**
(`2026-09-13-nyiso-232-st-gas`). Nothing armed. Evidence:
`docs/FINDING-nyiso234-tail-gas-is-unobserved-2026-09-14.md`.

Two questions. **Q1 is a ruling to confirm or overturn. Q2 is a spend.**

---

## Q1 — `temp_dependent_derate` sits at `G`. Does nyiso-233's headroom measurement re-open it?

**The session's ruling: NO. The cell stays `G`.** Put to you because rule 28(a) makes re-opening a
`G` cell an owner call, and because the handoff correctly flagged the headroom measurement as new
evidence that did not exist when nyiso-111 refused.

**What nyiso-111 refused, and on what basis.** It refused **ex ante, with no solve**, on
**identification** — NYISO's own CAMPD conduct cannot measure an ambient capability slope. Four
grounds, any one decisive: only 2 of 15 candidate plants identify; the measured sign **inverts**
(−0.00745/°C, capability *rising* with temperature — impossible for a gas turbine, and in fact the
NYC air-conditioning dispatch shape); the estimator's premise fails (the one near-pinned plant
measures no response at all, r = 0.006); and phase validation fails (best lag −5 h — a load shape,
not a contemporaneous physical response). It named its own re-open condition: *"a future intake
with an actual capability instrument (unit DMNC test results, or a plant pinned at capability)."*

**Why the headroom measurement does not defeat it.** nyiso-233 measured a **residual** (3.4–6.2 GW
idle in the tail). That is **motive**, not **identification**. The re-open condition nyiso-111 set
is **unmet** — no capability instrument has entered the repo. Arming on a residual with the slope
still unidentified is the move rule 1 `[R-STRUCT]` exists to forbid, and rule 21 `[R-DOF]` would
have nothing to write as the identification source.

**And a second bar the refusal never needed.** Even granting identification, the **committed curve
is identically 1.0 in cold hours** — the hinge form is flat below 15 °C, and the mean-anchored form
clips to 1.0 below the annual mean. So it cannot reach, **at any slope**:

| year | share of tail gap below the hinge | C3a status |
|---|---:|---|
| **2022** | **79.8 %** | **FAILS −11.6 %** |
| 2023 | 49.4 % | PASS |
| 2024 | 38.4 % | PASS |
| 2025 | 15.8 % | PASS |

Stable across tail depth (2022: 77–86 % at every cut). **In the only year that fails, the mechanism
cannot touch four-fifths of the object.**

☐ **CONFIRM — cell stays `G`** *(session's recommendation)*
☐ **OVERTURN — re-open it**, which requires funding a capability instrument (DMNC test records);
the reach bar above would still cap what it could buy

---

## Q2 — The availability family is closed. Do we fund the gas-price intake?

### What changed this session

The handoff ranked Object A (availability) as lever #1. **It is closed — by arithmetic, not by
identification** — and this is the first time the two measurements have been put side by side:

| | measured | source |
|---|---:|---|
| model's idle thermal in tail hours | **3,390 – 6,247 MW** | nyiso-233 |
| peak of NYISO's **entire** measured sub-5-day outage family | **1,653 – 2,351 MW** | nyiso-227 (2026-09-11) |
| `temp_dependent_derate` reach | unidentified, **0 below 15 °C** | this session |

Every availability instrument in the repo is **2–3× too small** to make the model short — and it
would have to eat all that idle headroom *before* removing a single MW the model is using.
nyiso-227 measured the binding hours on ST_GAS at **0 / 0 / 0 of 8,760** and said the family would
need to be **~20× larger**.

### What that forces, and what was found

The one fork left is the one nyiso-233 §6 flagged and declined to test: **reality may not have been
short either — it may have cleared $573 on a marginal unit burning very expensive gas.**

**Measured:** in 2022's tail, **69.8 %** of the gap falls on calendar dates for which the committed
daily gas series **has no row at all**.

| date | share of 2022 tail gap | model gas | observed? |
|---|---:|---:|---|
| **2022-12-24** (Elliott) | **33.8 %** | **$8.05/MMBtu** | **NO ROW** |
| **2022-12-23** (Elliott) | **13.9 %** | **$8.05/MMBtu** | **NO ROW** |
| 2022-01-16 | 7.6 % | $10.79 | **NO ROW** |

**$8.05 is the year's own median.** The model burns median-priced gas flat for eleven days,
Dec 21–31 2022, straight through the largest gas event in Northeast history.

Across years — % of tail gap on unobserved dates: **69.8 / 29.0 / 66.8 / 15.8** (2022/23/24/25),
stable across tail depth. The holes are systematic: **every year has a 14–15 day hole spanning
Christmas–New Year**, plus 7-day Thanksgiving holes and multi-day summer holes — and they land on
the named events. 2024's Dec 21–23 sit inside the December hole (66.8 % unobserved); 2025's
Jun 23–25 are covered (15.8 %, the lowest year).

**No committed source can fix it.** The monthly series is **not** an independent cross-check — its
Dec-2022 value ($7.3200) is *exactly* the mean of the 15 surviving dailies. Algonquin Citygate has
the **same hole** (last print $6.51 on Dec 21). **Nothing in this repository observes Elliott.**

### Why this candidate is unusually clean

- **Zero free parameters** — it fills holes in a measured series with measured values. Not a
  mechanism, not an adder; rules 21 / 24 untouched.
- **It has the property nyiso-232 proved a tail lever must have.** The hub overlay *supersedes* the
  monthly level in covered months, so a repair raises the **tail** and leaves ordinary hours alone
  — structurally, not by tuning. (A tidier story where the monthly anchor also fixed the
  ordinary-hour over-pricing was hypothesised and is **false**; the code contradicts it and it was
  dropped.)
- **Both seasons**, which the object requires and a temperature mechanism cannot give.
- **Bounded by machinery already armed — and the bound is MEASURED.** Through the repo's own
  `dual_fuel_oil_price_series`, the model's delivered **oil parity on Dec 23–24 2022 is
  $24.85/MMBtu** against the **$8.05** gas fill — **3.1×**. The model burns $8.05 only because
  `min(8.05, 24.85) = 8.05`; at any observed gas above $24.85 the downstate dual-fuel fleet flips
  to oil at parity. **A repaired gas price cannot run away**, and the switch Elliott actually
  triggered is already in the model. *(A bound, not a prediction — the non-dual-fuel fleet has no
  such cap and no $/MWh figure is derived from it.)*
- **The gap is a source property, not an unavoidable fact about holidays.** The model's *other*
  fuel series, `ny_harbor_ulsd_daily.csv`, **does** print Dec 22 and **Dec 23 2022** — ULSD is
  NYMEX-traded and quotes through the holiday week. Same model, same days, different coverage.
- **Clean forward story** (rule 13) — a complete daily series regenerates for any year.
- **It may be cross-ISO.** NEISO's Algonquin series has the identical defect. Under rule 25 that is
  NEISO's lane to measure, not this one's — but the intake would likely serve both.

### The honest limits

**The magnitude is unmeasured and is deliberately not estimated.** No committed source carries the
missing prints. Guessing Elliott's gas price would be the magic number rule 5 forbids; sizing it
against the residual would be the fitted selection rule 1 forbids. **The intake must land before
anyone can say what it buys** — this card asks you to fund a measurement, not to approve a result.

☐ **FUND THE INTAKE** *(session's recommendation)* — acquire the missing trading-day Transco Z6 NY
(and Algonquin) prints for the gap windows 2022–2025, land them via the `data-intake` skill, then
re-screen under rule 29 on one year
☐ **DEFER** — the object stays open and NYISO has **no admissible lever for the tail**; §2 of the
finding closes the availability family and §1 closes the temperature route
☐ **SOMETHING ELSE** — direct the lane elsewhere (Object B, the gas-monotone tilt, remains open and
untouched)

---

## Q3 (FYI, no decision needed) — the 2022 budget question the handoff asked me to answer

The handoff asked me to decide explicitly whether closing C3a-2022 was worth this session's solve
budget, since under rule 30(c) it buys the **four-year bundle**, not the ISO headline.

**Answer: no, and not on cost grounds — on rule 14.** 69.8 % of 2022's tail gap sits on dates the
gas input does not observe. Spending a solve on an offer-curve or availability lever for 2022 now
would be tuning a mechanism to compensate for a known-missing input — precisely what rule 14
`[R-ACCURATE]` names: *"that is a signal that something else in the model is miscalibrated and the
estimate was silently compensating for it … do not bury the error back inside an inaccurate
input."*

**No shard was launched and no LP was spent.** The correct order is: land the input, then re-screen.
