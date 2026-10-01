# RESULT — SPP-69 (2026-09-20): the cost half of the Schedule-5 intake is dead too, and 2020 is a different object

```
SESSION : spp-69        ISO: SPP        KEEPER: 2026-09-20-spp-67-yearown-rate (UNCHANGED)
RUNG    : 2026-09-20-spp-67-rung-yearown (UNCHANGED)
ASK     : build the EIA-923 Schedule-5 receipts/stocks intake as the forecast-admissible
          route to SPP's 2022 coal offer markup (SPP-41's named successor).
RESULT  : (0) THE LANE'S PREMISE WAS FOUR DAYS STALE. The intake landed 2026-09-14 and
              SPP-44 (2026-09-16) already adjudicated the mechanism DEAD on measurement.
              This session re-derived that independently before finding it (see §1).
          (1) ONE GENUINELY NEW LEG: the delivered-COST channel, which SPP-44 did not
              touch. Also dead -- the 2022 spot/contract spread is $1.49/MWh against a
              $21.12/MWh markup, 7.1% of it. Both economic routes from Schedule-5 to the
              markup are now closed.
          (2) 2020 CHARACTERISED, and it is NOT the same object: the model's whole 2020
              price lives in a $13.35 band with a $36.21 annual maximum. That is the
              already-named R-ba / SPP-64 thermal-stack-width defect at its extreme.
LP SPENT: ZERO. No shard launched, no bundle produced, no run registered, no cell armed
          beyond one evidence update.
```

---

## 0. Headline

> **The EIA-923 Schedule-5 intake exists, is complete for SPP, and refutes the hypothesis
> it was requested for — on tonnage (SPP-44) and now on cost (this session).**

SPP's MMU publishes a coal offer markup the model sets to zero by construction:

| year | 2021 | **2022** | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| **MMU coal markup $/MWh** | 6.02 | **21.12** | 6.88 | 4.29 | 5.81 |
| model markup | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

The MMU names the driver (ASOM 2023 fn. 194): *"Several coal resources experienced coal
deliverability issues as a result of rail limitations, which resulted in many resources
offering higher than typical mark-ups."*

Two economic routes lead from that sentence to a model mechanism. **Both are now closed on
measurement, and neither was closed by a residual.**

| route | hypothesis | closed by | verdict |
|---|---|---|---|
| **tonnage** | the markup is a physical deliverability / inventory signal | SPP-44, six legs | **dead** |
| **cost** | the markup is a fuel replacement-cost passthrough | **this session, §3** | **dead** |

---

## 1. The lane's premise was stale, and this session partly re-did adjudicated work

Stated plainly because rule 28(a) `[R-MECH-MATRIX]` exists to prevent exactly this.

The SPP-69 brief was written from `RESULT-spp-41` (2026-09-14), which recorded the intake
as **not on disk** and named it the blocker. Two things had already happened:

* **2026-09-14** — `data/raw/coal-receipts` + `data/raw/coal-stocks` landed (via miso-258,
  then extended by pjm-h11 at `4c13c65a`), 2018–2024, keyless, with readers and schemas.
* **2026-09-16** — `RESULT-spp-44-coal-deliverability-2026-09-16.md` adjudicated the
  mechanism **dead on measurement** across six legs and moved `coal_fuel_inventory`
  `U` → **`R`** in SPP's shard.

This session re-derived the tonnage result independently before discovering SPP-44. That
is a process cost, owned here rather than buried. It has one redeeming property: the
re-derivation used a **different statistic** from SPP-44's, and **agrees**, which is a
genuine cross-check rather than a repeat (§2).

**The correct entry point for any successor is SPP-44, not SPP-41.**

---

## 2. Cross-check: the tonnage route, on a different statistic

SPP-44 leg C measured per-plant **receipts/burn coverage ratio**. This session measured
per-plant **days-of-burn** — a different construction from the same intake. Minima per
plant, count below each threshold, 28 SPP coal plants:

| year | p25 | median | n<30 d | n<45 d | n<60 d | MMU markup |
|---|---:|---:|---:|---:|---:|---:|
| 2019 | 31.3 | 46.5 | 7 | 14 | 18 | — |
| 2020 | 52.4 | 64.4 | 5 | 5 | 12 | — |
| 2021 | 32.9 | 43.3 | 6 | **15** | 19 | **6.02** |
| **2022** | 29.5 | 47.6 | 7 | 13 | 19 | **21.12** |
| 2023 | 43.4 | 88.9 | 4 | 8 | 10 | 6.88 |
| 2024 | 82.3 | 108.0 | 3 | 4 | 6 | 4.29 |

**2021 and 2022 are indistinguishable, and on two of the five statistics 2021 is the
tighter year** (median 43.3 vs 47.6; n<45 of 15 vs 13; n<60 identical at 19). The markup
differs between them by **3.51×**. **2019 is as tight as 2022 on every measure and is the
one rung year that passes every criterion.** Same verdict as SPP-44, reached independently.

Two further reads, both also flat:

* **Fleet minimum days-of-burn** — 61.8 / 91.7 / 68.3 / **58.5** / 84.9 / 153.6
  (2019→2024). 2022 is the minimum, but by 9.8 days over 2021, against a 3.51× markup gap.
* **Drawdown rate** (peak-to-trough, Mt) — −2.180 / −0.714 / −2.682 / **−4.073** / 0.000 /
  −3.411. 2024 reaches 84% of 2022's drawdown and carries the record's **lowest** markup
  ($4.29). The rate inverts the hypothesis rather than rescuing it.

### 2a. And the physically correct constraint never binds

An admissible coal energy budget — opening stock (the prior December's state) plus a
delivery rate from years ≤ Y−1, the only construction rule 13 `[R-MEASURED]` and the
`coal-stocks` README permit — against the keeper's own model coal burn, all Mt:

| year | opening | delivery rate | **budget** | **model burn** | headroom | binds |
|---|---:|---:|---:|---:|---:|---|
| 2019 | 12.729 | 59.260 | 71.988 | 51.580 | +20.408 | no |
| 2020 | 12.885 | 56.463 | 69.347 | 40.743 | +28.605 | no |
| 2021 | 12.610 | 53.058 | 65.668 | 57.251 | +8.417 | no |
| **2022** | 12.874 | 51.299 | **64.174** | **60.348** | **+3.825** | **no** |
| 2023 | 12.219 | 51.259 | 63.478 | 42.828 | +20.650 | no |
| 2024 | 20.686 | 53.183 | 73.869 | 40.831 | +33.039 | no |

**Zero of six years.** The tightest year still clears by 3.825 Mt, 6.0% of its own budget.
This is the same conclusion SPP-44 reached on its cumulative-constraint leg, on annual
rather than monthly grain.

---

## 3. NEW — the cost route, and why it is dead

SPP-44 measured tonnage and timing. It did not read `FUEL_COST` or `Purchase Type` at all.
That leaves a distinct and reasonable hypothesis standing: **a generator offers at the cost
of replacing the ton it burns, not at its average contract cost.** If spot coal diverged
from contract coal in 2022, ordinary opportunity-cost economics would raise coal offers
with no deliverability story needed — and it would be forward-regenerable from forward
coal curves, so rule 13 admits it.

Measured on the SPP coal fleet's own deliveries, volume-weighted by MMBtu:

| year | contract $/MMBtu | spot $/MMBtu | **spread $/MMBtu** | spot vol share | **spread $/MWh** | all-in YoY $/MWh | **MMU markup $/MWh** |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2019 | 1.540 | 1.552 | +0.011 | 0.237 | +0.12 | −0.46 | — |
| 2020 | 1.473 | 1.425 | −0.048 | 0.195 | −0.50 | −0.84 | — |
| 2021 | 1.502 | 1.514 | +0.012 | 0.237 | +0.12 | +0.44 | **6.02** |
| **2022** | 1.807 | 1.948 | **+0.142** | 0.170 | **+1.49** | **+3.42** | **21.12** |
| 2023 | 1.790 | 1.739 | −0.052 | 0.228 | −0.54 | −0.56 | **6.88** |
| 2024 | 1.694 | 1.623 | −0.072 | 0.286 | −0.75 | −1.09 | **4.29** |

*($/MWh at a 10.5 MMBtu/MWh nominal subcritical PRB heat rate; the $/MMBtu column is
reported so the conclusion does not rest on that constant.)*

**The 2022 spot-minus-contract spread is $1.49/MWh against a $21.12/MWh markup — 7.1% of
it.** The most generous available cost read, the year-on-year move in the *all-in*
delivered cost, reaches $3.42/MWh — **16.2%**. Neither is within a factor of six.

**It is not a suppression artifact.** `FUEL_COST` coverage is **98.5% of delivered MMBtu**
in every year 2019–2024, and **98.5% of that volume is filed `REG`** — SPP's coal fleet is
almost entirely regulated utility, so there is no withheld merchant tail hiding a
different cost basis.

### 3a. What that leaves the markup as

The fleet did not run out (58.5 days minimum), the deliveries arrived (53.5 Mt in 2022
against 54.0 Mt in 2021, a 0.8% difference), and the fuel cost moved $3.42/MWh. **The
$21.12/MWh markup was a precautionary risk premium against a tail event that did not
occur** — regulated utilities offering high to conserve a pile they feared they could not
replace, which is exactly what the MMU's own wording describes.

That is a real market behaviour, and it is the reason no measured quantity reproduces it:
the premium is priced against a *risk*, and the risk did not materialise in any of the
measured outcomes. **Reaching it would require a behavioural parameter identified against
the markup series itself** — the fitted-mechanism selection rule 1 `[R-STRUCT]` (c)
forbids and rule 21 `[R-DOF]` would book as a residual-identified free parameter.
**Refused, and refused on structure rather than on fit.**

---

## 4. The model's actual defect is not 2022-only, and the band is what separates the years

Reported because the brief targets "2022 COAL_PRB" as one row. It is two, and the
underlying error is nearly as large in the passing year. C1 grid-delivered, TWh:

| class | 2019 | 2020 | **2021** | **2022** | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| **COAL_PRB** Δ | −1.72 | −7.10 | **+7.10** | **+9.95** | +0.89 | +0.23 | +5.42 |
| **CC_REGULAR** Δ | +6.09 | +2.67 | **−7.10** | **−7.84** | −3.76 | −5.04 | −6.95 |
| ST_GAS Δ | −5.49 | −5.91 | −4.41 | −5.58 | −5.78 | −7.41 | −9.40 |
| gas price $/MMBtu | 2.57 | 2.03 | 3.72 | 6.45 | 2.54 | 2.19 | 3.52 |

* **2021 and 2022 carry the same defect** — coal displacing CC gas, +7.10 and +9.95 TWh,
  mirrored almost exactly by CC_REGULAR at −7.10 and −7.84. Only 2022 fails, because
  2021's +7.10 TWh / 2.41 pp sits just inside the ±8.00 TWh / ±3 pp band. **The band
  separates them; the physics does not.**
* **The sign follows gas price.** The two highest-gas years over-run coal; the lowest-gas
  year (2020, $2.03) under-runs it by 7.10 TWh. The coal/gas crossover is **too
  gas-responsive in both directions** — one defect with a consistent sign, not two.
* **ST_GAS is short in all seven years**, 4.41–9.40 TWh. It is the most persistent single
  error in the table and it is unrelated to coal markup.

---

## 5. 2020 — the brief's second object, characterised

The brief asks that 2020 be characterised before anything is proposed, and warns against
assuming it is the same object. **It is not.** Model price distribution, load-weighted
across zones, P1:

| year | mean | p05 | median | p95 | **max** | **p05→p95 width** | h>$100 | CT_PEAKER h online | CT_PEAKER TWh |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2019 | 22.19 | 17.49 | 22.23 | 28.32 | 181.28 | 10.83 | 1 | 8,518 | 13.80 |
| **2020** | **19.19** | **12.99** | **20.16** | **26.34** | **36.21** | **13.35** | **0** | **8,348** | **15.33** |
| 2021 | 36.37 | −26.00 | 27.35 | 149.41 | 314.26 | 175.41 | 501 | 6,899 | 8.68 |
| 2022 | 39.77 | −26.00 | 41.54 | 74.05 | 1102.11 | 100.05 | 5 | 7,317 | 8.52 |

**The model's entire 2020 price lives in a $13.35 band and never exceeds $36.21 all year,
against an actual that had 23 hours above $200.** C3a (+19.3%) and C3b (NRMSE 0.273) are
not two failures — they are one flat distribution sitting above the actual mean and
carrying no shape. CT_PEAKER is in-merit in **8,348 of 8,784 hours (95%)** at a mean
1,836 MW, and appears in *every* price decile including the lowest.

**This is the already-named object, at its extreme.** `FINDING-spp-64` §6 measured SPP's
whole thermal fleet clearing "within a ~$5 band" that "should be tens of dollars wide",
and bounded R-ba (the ST_GAS/CT_PEAKER inversion) as a re-ranking *inside* that band.
2020 is that finding's worst year. **The brief's line that R-ba was "falsified at phase 0"
is incorrect** — SPP-64 §6 confirms the inversion is real and reproduces it; what it
establishes is that R-ba is **bounded**, not false, and cannot independently fix the price
distribution.

**So the successor object for 2020 is the thermal stack's vertical extent, not a coal
markup.** No mechanism is proposed here; the measurement is the deliverable.

---

## 6. Rules

* **Rule 1 `[R-STRUCT]` / 13 `[R-MEASURED]`** — both routes are refused on structure and
  measurement. No mechanism was selected, kept or rejected because a residual moved.
* **Rule 21 `[R-DOF]` / 24 `[R-REGISTRY]`** — zero free parameters proposed, zero
  `ScenarioConfig` fields added, zero tunables introduced.
* **Rule 25 `[R-ISO-SCOPE]`** — nothing transferred from MISO. The MISO finding
  (`FINDING-miso258`) shows a fleet opening 2022 at its lowest January on record; **SPP's
  opens at the third-highest of 2019–22.** The two footprints do not share the story, and
  that is why the cell is measured per ISO.
* **Rule 28 `[R-MECH-MATRIX]`** — `coal_fuel_inventory` stays **`R`**; its evidence line
  gains this session's independent cross-check and the cost leg. No cell is armed.
* **Rule 31 `[R-RETAIN]`** — nothing was solved, so nothing is at risk. See §7.
* **Rule 32 `[R-SHARD]` (a)** — the parent solved nothing and launched no shard.

---

## 7. Promotion question (rule 31 `[R-RETAIN]`) — asked, not pre-empted

**There is nothing to promote.** Zero LP was spent, no bundle was produced, no keeper or
rung file was touched, and no gitignored artifact exists that would die with the container.
The keeper `2026-09-20-spp-67-yearown-rate` and the rung
`2026-09-20-spp-67-rung-yearown` are byte-unchanged, and SPP's headline stays **CALIBRATED**
on its train tier.

**The open question this session does NOT decide** is SPP-68's, which remains outstanding:
`2026-09-20-spp-68-ceiling-span` and `2026-09-20-spp-68-rung-ceiling` are still registered
as non-keeper runs, which is why `audit_keepers --iso SPP` reports 2 E13 failures by
design. That is SPP-68's promotion question, not this lane's, and this session did not
prune them.

---

## 8. Probe committed (zero-LP, re-runnable)

`scripts/probes/_spp69_coal_cost_channel_phase0.py` — legs A (budget), B (spot/contract
spread), C (suppression check), D (per-plant days-of-burn), E (2020 price distribution).
Reads only committed artifacts; reproduces every number in this document.
