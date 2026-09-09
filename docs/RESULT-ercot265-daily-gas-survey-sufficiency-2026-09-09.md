# RESULT — ercot-265: the daily-gas survey returns EMPTY, and the procurement it blocks is now measured SUFFICIENT

**Session:** ercot-265, 2026-09-09. Branch `claude/ercot-uri-february-fuel-baynmi`.
**Base:** `07bdee7a` (origin/main at session start).
**Keeper:** `2026-09-09-ercot261-corroborated-gas-level` — **UNCHANGED, untouched, not re-solved.**
**Scope:** SURVEY + ZERO-LP DIAGNOSTIC + DOCS. **Zero LP spent. No shard launched. No
`ScenarioConfig` field changed. No `src/` or `scripts/` file edited. Nothing armed, nothing
registered, nothing deleted (rule 31 `[R-RETAIN]`).**

---

## 0. Option chosen, and why

**Option (A), the daily gas basis.** (B) touches the ERCOT bin sheet and moves every ERCOT
keeper — the handoff itself requires an explicit owner decision first, and none exists. (C) is
the fallback the handoff conditions on (A) surveying empty. (A) is the only route that closes
ERCOT's last rubric failure, its first step is free, and the handoff's instruction is explicit:
**report before spending anything.** Nothing was spent.

No PRECOMMIT was owed: rule 29 `[R-SCREEN]` gates *solves*, and this session ran none.

---

## Headline

**Two results, and the second is the one that matters.**

1. **The survey is EMPTY, and the emptiness is now structural rather than merely unlucky.** No
   admissible public daily Waha/HSC series exists for 2019–2025. The two reopen conditions
   formally recorded at ercot-224 are both still false.
2. **NEW — the procurement is measured SUFFICIENT, not merely necessary.** Inverting the
   keeper's own committed February-2021 hourly prices for the delivered gas path that would
   make them match actual yields a burn-weighted February gas price of **$56.79/MMBtu against
   the independently measured EIA N3045TX3 print of $59.73/MMBtu — a 4.9 % gap**, with the
   measured print falling *inside* the band across every plausible marginal heat rate. The
   lane has had a necessity argument for three sessions; it did not have a sufficiency number.
   It does now.

**ERCOT's determination is untouched.** Train tier {2023, 2024, 2025} carries no failure; the
ISO still reads **CALIBRATED** (rule 30(c)); the five-year determination stays **NOT-YET on
`price_shape` (C3b) alone.**

---

## 1. The survey — EMPTY, and why that is now a settled fact rather than a search

Re-confirming the on-disk absence a fourth time would have been worthless, so this session
surveyed the **external** side and the **prior adjudications**. Both are closed.

| Route | Status | Record |
|---|---|---|
| **EIA NGWU daily spot table** (the route four ISOs already scrape) | **CLOSED — structural** | Verified directly this session: the table carries **exactly four rows** — Henry Hub, New York, Chicago, Cal. Comp. Avg. **No Texas hub of any kind, in any issue.** This is the free-EIA path ercot-160/163 fenced; the fence is re-confirmed, not re-litigated. |
| **CME / NYMEX** basis + swing futures, Waha and HSC | **CLOSED — the products do not exist** | ercot-224 screen: the Platts regional gas complex was delisted 2017-10; Waha basis 2020-12-07; HSC basis 2022-01-10 — all on **zero open interest**, i.e. even archived settlements would be no-trade marks. |
| **ICE** (live Waha/HSC basis futures) | **CLOSED — paid** | Owner ruling 2026-08-04: *NO PAID DAILY GAS DATA.* |
| **NGI / Platts / Argus** | **CLOSED — paid** | Same ruling. |
| **EIA NGWU narrative prose** | **Not a series** | The prose *does* quote Texas prints (see §3) but only sporadically — a handful of days per storm week, nothing resembling 2019–2025 daily coverage. Usable as a citable **anchor**, never as an input. |

**Reopening requires one of exactly two things, neither of which has happened** (ercot-224 §4,
restated verbatim here so it is never re-litigated from memory): **(a)** a new *free* daily
Waha/HSC source, or **(b)** the owner reversing the no-paid-daily-gas decision.

Per the handoff's own instruction, the survey therefore **STOPS here**. What follows cost no
data and no LP, and it exists because the owner is being asked to spend money: the right thing
to hand them is not "we couldn't find it" but **what it would buy.**

## 2. What the procurement would buy — the sufficiency measurement

### 2.1 The object, on the basis C3b actually scores

C3b is an NRMSE over **twelve monthly points**. On the keeper's committed 2021 payload, load-weighted:

| month | model $/MWh | actual $/MWh | gap | SSE share |
|---|---:|---:|---:|---:|
| Jan | 26.48 | 21.26 | −5.22 | 0.0 % |
| **Feb** | **1422.13** | **1752.04** | **+329.91** | **94.8 %** |
| Mar | 26.63 | 19.93 | −6.70 | 0.0 % |
| Apr | 67.57 | 51.42 | −16.15 | 0.2 % |
| May | 28.60 | 24.07 | −4.54 | 0.0 % |
| Jun | 67.72 | 43.14 | −24.58 | 0.5 % |
| Jul | 63.00 | 39.58 | −23.42 | 0.5 % |
| Aug | 55.78 | 37.14 | −18.64 | 0.3 % |
| Sep | 55.29 | 44.20 | −11.08 | 0.1 % |
| Oct | 112.62 | 49.53 | −63.09 | 3.5 % |
| Nov | 43.16 | 41.28 | −1.89 | 0.0 % |
| Dec | 30.78 | 26.30 | −4.48 | 0.0 % |

**February is the only month the model is UNDER. All eleven others are OVER.** That asymmetry
is the whole diagnosis in one line: this is not a level error, it is one month with a missing
cost. NRMSE 0.546 on this basis; February exact ⇒ **0.125, a clean PASS** (reproduces the
addendum's 0.559 / 0.116 to rounding).

### 2.2 The inversion

Take the keeper's own committed February hourlies. For each hour, hold the model's **ORDC
adder and dispatch fixed**, and ask what delivered gas price would move the *energy* component
onto the actual price:

> `gas_required[h] = gas_model[h] + (actual[h] − ordc[h] − energy_model[h]) / HR`

floored at a physical $1.50/MMBtu, then burn-weighted over the month. `HR` is the marginal heat
rate; the repo's own identified value is **7.36** (ercot-258's Jan-vs-Oct fit).

| marginal HR | implied Feb delivered gas | vs measured $59.73 |
|---:|---:|---:|
| 6.00 | $67.27 | +12.6 % |
| 6.50 | $62.91 | +5.3 % |
| **7.00** | **$59.17** | **−0.9 %** |
| **7.36** (repo's own) | **$56.79** | **−4.9 %** |
| 7.50 | $55.92 | −6.4 % |
| 8.00 | $53.09 | −11.1 % |
| 9.00 | $48.37 | −19.0 % |
| 10.00 | $44.59 | −25.4 % |

**The measured print sits inside the band across the entire plausible range, and lands almost
exactly at HR 7.0.** The result is not knife-edge.

### 2.3 Why this is evidence and not circularity

The inversion is an identity by construction — of course it returns "the gas that makes it
match." **That is not the result.** The result is that this gas path's *monthly mean* lands on
a number the inversion never saw: **$59.73/MMBtu, the EIA N3045TX3 Feb-2021 delivered
electric-power print** — measured from gas cost and volume surveys, entirely independently of
any ERCOT price. Two unrelated measurements of "how expensive was February gas" agree to 5 %.

That is the corroboration the lane was missing. It says the February price gap is a **fuel gap
of the right size**, not a scarcity gap wearing a fuel costume — which was the live alternative
hypothesis, and which this session set out to test precisely because the prior sessions had
ruled it out only from `slack = 0` / `dump = 0` (which rules out unserved energy, not tight
reserves).

### 2.4 The daily path it implies, checked against the primary record

Implied daily delivered gas at HR 7.36, $/MMBtu:

```
Feb  1- 10:   4   5   6   6   5  12   6   5  10   8
Feb 11- 19:  56  36 240 201 203 180 165  77  44
Feb 20- 28:   6   6   4   4   3   5   8   3   3
```

Against the primary record — EIA's own Natural Gas Weekly Update for the week ending
2021-02-17, retrieved this session
(`eia.gov/naturalgas/weekly/archivenew_ngwu/2021/02_18/`), quoting NGI:

> *"Prices at major Texas hubs set all-time records on Tuesday (going back to 1993) with the
> Katy Hub at $352.64/MMBtu and Houston Ship Channel at $400/MMBtu, before falling yesterday to
> still record-setting levels of $216.54/MMBtu and $358.77/MMBtu"* — and the Waha Hub *"rose to
> over $206/MMBtu on February 16 … the highest reported price at the Waha Hub since at least
> 1995."*

The implied storm-day values ($165–240) sit **inside** the observed Texas hub range for those
days ($64 Waha … $400 HSC). The implied calm-day values ($3–6) sit at the observed pre-storm
level. The shape is right, not merely the total.

### 2.5 Why Henry Hub cannot substitute — the arithmetic, closed

`gas_daily_shape` (HH daily, mean-preserving) is **already armed on the ERCOT keeper**
(matrix cell `K`), and the keeper's February gas already carries an HH-shaped hump: mean
$10.20/MMBtu, calm days $5.34–7.55, peaking at **$47.90 on Feb 17**. It is not enough, and it
structurally cannot be:

| | calm-day | storm-peak | ratio |
|---|---:|---:|---:|
| Henry Hub daily, Feb 2021 | $2.88 | $23.86 | **8.3×** |
| Texas hubs (HSC), Feb 2021 | ~$3 | $400.00 | **~133×** |

A mean-preserving reshape can only redistribute; with an 8.3× dynamic range, hitting the storm
days forces ~$29/MMBtu onto the twenty-three calm days that never paid it. This is ercot-258's
refutation, and this session confirms it quantitatively from the keeper's own array rather than
by argument. **Only a series with the Texas hubs' own dynamic range resolves February**, which
is exactly the series that is unobtainable.

## 3. Two things this result explicitly does NOT license

1. **The inverted gas path must NEVER be used as an input.** It is derived *from* the price
   residual it would close; installing it is precisely the pinning-to-actuals that rule 13
   `[R-MEASURED]` forbids absolutely, and rule 1 `[R-STRUCT]`'s carve-out does not reach it (it
   is not an `offer_curve_by_group` band multiplier). It is a **diagnostic yardstick and
   nothing else** — its only job is to answer "would the real series be big enough?", and it
   has now done that job and is finished. The input to be procured is measured Waha/HSC
   actuals.
2. **It does not promote or license anything.** Nothing is armed, no cell verdict changes, no
   determination moves.

## 4. Honest limits, declared

- **First-order / partial equilibrium.** ORDC adder and dispatch are held fixed; the real LP
  would re-dispatch and re-price ORDC, so the required path could differ materially. This is a
  magnitude check, not a prediction of the solve.
- **One system-wide marginal heat rate**, where the true marginal HR varies hour to hour —
  which is why §2.2 reports a band rather than a point.
- **35.4 % of the required fuel-cost increment falls in hours whose ORDC adder already exceeds
  $500**, where the model is near the cap and additional fuel cost will be partly clipped. The
  true conversion of fuel cost into monthly-mean price is therefore **below** 1:1, and the
  sufficiency margin is correspondingly thinner than the headline 4.9 % suggests. Stated at the
  gate rather than absorbed: this is the one factor that could make a real series close *less*
  of February than the arithmetic implies.
- **The deep-event days are already largely right** (Feb 15–18 model $5,459/$7,898/$8,140/$8,546
  vs actual $6,765/$8,970/$9,002/$8,989) and the model is in genuine deep scarcity there
  (ORDC adder $4,659/$2,992/$1,502/$63). The onset — Feb 11–14, model ORDC ≈ $0.82/$20.85/
  $71.87/$36.19 against actual $443/$374/$1,907/$2,356 — is where a daily series would bite,
  and it is **64.6 %** of the required increment.

## 5. The decision this puts to the owner

ERCOT's only remaining rubric failure is C3b-2021. It is 94.8 % one month, that month is
Winter Storm Uri, and the missing object is one measured input that no free source publishes.
This session did not find a new route and does not claim one. What it adds is the number the
decision needs:

> **A licensed daily Waha/HSC series for 2019–2025 is measured sufficient in magnitude to close
> February 2021, and with it C3b-2021 (0.559 → ~0.12), which is ERCOT's last open rubric
> failure. It requires no new mechanism, no new parameter and no fitted value — `gas_hub_basis_daily`
> already exists and is proven in four other ISOs.**

The decision is reversing the 2026-08-04 no-paid-daily-gas ruling for this one series, and it
is the owner's alone.

---

**Governance.** Zero LP; no shard launched (rule 32 `[R-SHARD]` — the parent solved nothing,
and nothing needed solving). Keeper untouched and not re-solved (ercot-264 already certified it
reproduces exactly at HEAD). No bundle produced, so rules 29(c)/31 have no object. The
pre-existing `check_registry_payload_parity` RED on `results/calibration/ercot262_arm_{2021..2025}`
is **not this session's and was left alone** — rule 31 forbids deleting it before the owner
rules on ercot-262's promotion.
