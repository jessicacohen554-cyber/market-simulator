# FINDING — pjm-167: PJM's 2021/2022 miss is an INPUT-CLOCK defect, in three parts

**Session:** pjm-167 · **Date:** 2026-09-06 · **HEAD:** `82a7742d`
**Branch:** `claude/pjm-price-cc-regular-review-al60pj`
**Keeper:** `2026-08-15-pjm-162-inputclock` (`pjm_debugb_inputclock_A`) — **UNCHANGED**
**Touchpoints read:** `2026-09-05-pjm-2022-2021-touchpoints` (`pjm_tp2022_2021_k162`)
**Supersedes in part:** `FINDING-pjm166-c1-object-phase0-2026-09-06.md` §2 and §7.4 (see §6)

Everything below is **zero-LP**: committed `hourly/` sidecars, committed bench sidecars,
`data/raw` EIA-930 / EIA-860 / CAMPD / PJM Data Miner extracts, and two `fleet_only`
reconstructions. No solve produced any of it.

---

## 0. The answer

> PJM 2021 is **not** a market-design outlier. Three independent objects in the model were
> **frozen on the 2023–2025 training window and never moved back** when the program's span
> became 2019–2025 (rule 22, owner decision 2026-08-06). Each is nearly inert inside that
> window — which is why none was caught — and each is large outside it.
>
> 1. **The fleet registry does not move with the solve year.** The model carries **38.72 GW
>    of PJM coal in 2021, 2022 and 2023 alike**; the year-matched EIA-860 vintage carries
>    **48.71 / 41.94 / 37.12**. In 2021 the model's dispatched coal peak is **95.4 % of its own
>    registry ceiling**, and its `ST_GAS` peak is **117.3 % of the gas-steam capacity that
>    existed that year**. This is the `CC_REGULAR` overshoot.
> 2. **The EMAAC import cut is enforced on a pre-2023 vintage of the interface feed that
>    contradicts itself.** In 2021 the measured flow exceeds the posted limit in **27.9 % of
>    hours**; in 2024/2025, **0.0 %**. Enforcing it produces 74 h of unserved energy at VOLL in
>    one zone — **51 % of the 2021 C3a error** — and inverts PJM's real east–west price
>    gradient.
> 3. **Two offer transforms are anchored on the 2023–2025 fuel-price window and extrapolated
>    linearly outside it.** Hypothesis, not proven here; it predicts the 2022 sign flip.
>
> The only genuine "real event the model cannot handle" is **Dec-2022 Elliott** (model $70.7
> vs actual $128.3). Winter Storm Uri is **not** one: PJM's Western Hub actually averaged
> **$137.35** on 2021-02-17 and the model produces ~$185 — over, not invented.

---

## 1. Where the 2021 price error lives

Model load-weighted RT LMP vs `bench.avgLMP.rt_lw` (the keeper's own basis), by month:

| | J | F | M | A | M | J | J | A | S | O | N | D |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| model | 33.3 | 52.4 | 29.6 | 28.9 | 31.6 | **51.9** | **57.9** | **80.0** | 49.7 | 54.8 | 56.4 | 43.1 |
| actual | 24.5 | 41.0 | 27.2 | 25.0 | 27.8 | 33.5 | 36.6 | 45.8 | 47.6 | 56.8 | 58.9 | 37.5 |
| err | +36 % | +28 % | +9 % | +16 % | +14 % | **+55 %** | **+58 %** | **+75 %** | +5 % | −4 % | −4 % | +15 % |
| **share of the annual error** | 8 % | 10 % | 2 % | 3 % | 3 % | **16 %** | **21 %** | **34 %** | 2 % | −2 % | −2 % | 5 % |

Annual: model **48.43** vs actual **38.53** = **+9.90 $/MWh (+25.7 %)**. Sep–Nov are within
±5 %. **Jun–Aug carry 71 % of the error.** This is a summer object, not a level object.

---

## 2. Defect 2 — the EMAAC import cut, enforced on a self-contradicting data vintage

### 2.1 The model runs out of energy in one zone

| year | slack hours | slack MWh | zone | months |
|---|---|---|---|---|
| **2021** | **74** | **99,100** | **PJM_EMAAC, 100 %** | Jun 14 / Jul 20 / Aug 40 |
| **2022** | **45** | **42,582** | **PJM_EMAAC, 100 %** | Jul 31 / Aug 14 |
| 2023 / 2024 / 2025 | **0** | **0** | — | — |

Slack prices at VOLL. During those hours EMAAC clears at **$2,000** while every other PJM zone
clears at **$57–87** — and PJM as a whole is **exporting 3,726 MW**. The system is not short;
one pocket is unreachable. `CT_PEAKER` runs **14,387 MW** in those hours against **16,920 MW**
in the year's top-100 net-load hours, so it is a deliverability result, not a capacity result.

### 2.2 The feed changes basis at exactly the tier boundary

`pjm_east_interface_cut` caps Flow(Central_PA→EMAAC) + Flow(SWMAAC→EMAAC) at PJM's published
hourly "Average Eastern" limit. Both columns come from the same file
(`data/raw/iso-specific-transmission/PJM_<year>_transfer_limits_and_flows.csv`):

| year | distinct hourly limit values (of ~8,760) | hours the **measured flow exceeds the posted limit** | max excess MW |
|---|---|---|---|
| 2019 | 7,063 | 1.6 % | — |
| 2020 | **1** | 18.7 % | 4,939 |
| **2021** | **85** (5,504 h at 4,971; 3,173 h at 7,526) | **27.9 %** | **5,242** |
| **2022** | **58** | **17.5 %** | 3,773 |
| 2023 | 5,677 | 2.1 % | 2,595 |
| 2024 | 8,767 | **0.0 %** | −640 |
| 2025 | 8,750 | **0.0 %** | −241 |

A security limit that the actual flow exceeds in a quarter of all hours is not an enforceable
limit. From 2024 the feed is a true hourly-averaged TLC series and the flow never once exceeds
it. Pre-2023 it is a near-static seasonal limit-set posting — **a different quantity under the
same series name**. Applied verbatim it forbids **2.99 TWh (2021) / 1.79 TWh (2022)** of
transfer that actually flowed, against **0.00 TWh** in 2024/2025.

### 2.3 Falsified against PJM's own published LMPs

If EMAAC had really been held to a 4,971 MW import cut in 12 % of 2021 hours, the east would
have priced above the west. It did the opposite, every year:

| year | model EMAAC − rest of PJM | model hrs separated >$1 | **actual** NJ Hub − AEP-Dayton | **actual** Eastern − Western Hub |
|---|---|---|---|---|
| **2021** | **+$34.50** | **1,054 (12.0 %)** | **−$5.43** | **−$1.68** |
| **2022** | **+$24.18** | **1,180 (13.5 %)** | **−$3.26** | **−$3.45** |
| 2023 | −$0.32 | 167 (1.9 %) | −$5.72 | −$4.46 |
| 2024 | +$0.62 | 181 (2.1 %) | −$2.90 | −$2.45 |
| 2025 | +$1.59 | 191 (2.2 %) | −$2.01 | −$3.30 |

The model reproduces the real (negative) gradient in-sample and inverts it by $25–35/MWh
out-of-sample. Source: `data/raw/lmp-data/PJM_<year>_rt_da_monthly_lmps.csv` (hourly hub LMPs).

### 2.4 What it costs

Repricing EMAAC at the max non-EMAAC zonal price:

| | VOLL hours only | every separated hour |
|---|---|---|
| 2021 | 48.43 → **43.35** (removes **51 %** of the error) | 48.43 → **42.41**, +25.7 % → **+10.1 %** |
| 2022 | 70.41 → 67.9 | 70.41 → **66.19**, −4.9 % → −10.6 % |

### 2.5 Rule 14 posture

This is `[R-ACCURATE]`'s **named exception**, not a licence to drop measured data: the pre-2023
vintage is *"a different time/area aggregation"* than the post-2023 series, so "using it
literally would make overall results less reflective of reality." The repair is a *reconciled*
version of the real data, never a guess and never a tuned limit.

---

## 3. Defect 1 — the fleet registry does not move with the solve year (**the CC_REGULAR object**)

### 3.1 The model is coal-capacity-bound in 2021 and not in 2023

Against EIA-930 PJM-metered coal (`Net Generation (MW) from Coal (Adjusted)`, int32 sentinels
guarded):

| year | model coal TWh | 930 metered | Δ | model coal **peak MW** | 930 peak | gap | hrs model < metered |
|---|---|---|---|---|---|---|---|
| **2021** | 152.3 | 183.5 | **−31.3** | 36,955 | 42,678 | **−5,723** | **8,291 / 8,760** |
| **2022** | 154.7 | 167.4 | −12.7 | 33,790 | 39,903 | −6,113 | 6,514 |
| 2023 | 112.6 | 121.0 | −8.4 | 31,277 | 31,430 | **−153** | 6,823 |
| 2025 | 142.8 | 145.9 | −3.1 | 31,424 | 33,428 | −2,004 | 4,948 |

The model never reaches PJM's 2021 coal output in **any** hour. This is a capability gap.

### 3.2 The cause: one snapshot, every year

`scripts/data/process_eia860.py:74` → `RETIREMENT_WINDOW_START: int = 2023`, commented *"Bump
only if the supported window moves."* It never was moved. So:

- the operable fleet is the **2025 Early Release** snapshot, for every solve year;
- `eia860_generator_retired_within_window.parquet` carries retirement years **2023 and 2024
  only** (181 PJM units, 6,431 MW — of which **261 MW in EMAAC**);
- `load_retired_within_window` emits **whole-plant exits only** — a partially-retired plant
  keeps its survivors in the snapshot and its retired units stay out. `partial_plant_exit_carry`
  (miso-190) is the complement and is **default-off**;
- `eia860_vintage_year` is **`None`** in both the keeper and the touchpoint.

Nothing that retired in 2021 or 2022 is in any of these paths.

PJM coal capacity by EIA-860 vintage (`eia860_generator_operable` × `eia860_plant` BA join):

| vintage | PJM coal units | GW |
|---|---|---|
| **vintage_2021** | 124 | **52.97** |
| vintage_2022 | 109 | 45.54 |
| vintage_2023 | 100 | 40.18 |
| vintage_2024 | 98 | 39.30 |
| **current 2025 ER — what the model reads for every year** | 96 | **37.99** |

20 PJM coal units, **11.24 GW**, are in vintage_2021 and absent from the 2025 snapshot: Homer
City 2.01, W H Sammis 1.69, W H Zimmer 1.43, Morgantown 1.25, Chesterfield 1.05, Waukegan 0.68,
Avon Lake 0.68, Cheswick 0.64, Will County 0.60, Indian River 0.45, Chambers 0.29, Logan 0.24,
Warrior Run 0.23.

### 3.3 Phase-0 census — what the year-matched vintage actually changes (no LP)

`run_year(..., fleet_only=True)` on each bundle's own recorded recipe, with
`paths.set_eia860_vintage` pinned to the solve year. *(Instrument note: the DA-virtual pseudo-unit
build is disabled for the census because `data/raw/pjm-da-virtuals/` is an untracked BLOAT-B
corpus; virtual pseudo-units are not physical fleet, so a fleet census is unaffected.)*

| class (MW) | 2021 now | 2021 vintage | Δ | 2022 Δ | 2023 Δ |
|---|---|---|---|---|---|
| **COAL** | 38,722 | **48,708** | **+9,986** | **+3,222** | **−1,605** |
| **CC_REGULAR** | 59,857 | 54,600 | **−5,256** | −2,992 | +216 |
| **ST_GAS** | 11,111 | 7,411 | **−3,701** | −2,290 | −2,883 |
| CT_PEAKER | 25,989 | 25,223 | −766 | −1,103 | −711 |
| nuclear | 33,492 | 32,654 | −838 | −838 | −800 |
| oil | 4,466 | 4,949 | +483 | +505 | +6 |
| **TOTAL** | 197,141 | 197,075 | **−66** | −3,439 | −5,786 |

**The current snapshot yields an identical 38,722 MW coal fleet in 2021, 2022 and 2023** — the
COD ramp can only age out a unit it is given, so PJM's real coal retirement trajectory is
invisible to the model. The year-matched vintage restores it (48.7 → 41.9 → 37.1 GW).

### 3.4 The census predicts the sign of the C1 miss, class by class

| class | 2021 C1 miss (model − actual, TWh) | vintage fleet Δ (MW) | agrees? |
|---|---|---|---|
| `CC_REGULAR` | **+28.7** | **−5,256** | ✅ |
| `ST_GAS` | **+8.1** | **−3,701** | ✅ |
| COAL (all) | **−12.9** | **+9,986** | ✅ |
| `CT_PEAKER` | −5.0 | −766 | ❌ (worsens; see §5) |

Three of the four named C1 failures are corrected in sign by an input repair with **zero free
parameters**. Two harder confirmations:

- **Coal is at its ceiling in 2021 and not in 2023.** Dispatched coal peak / registry pmax:
  **2021 95.4 %**, 2022 87.3 %, **2023 80.8 %**. Under the year-matched vintage 2021 falls to
  75.9 % — real headroom.
- **The model dispatches gas steam that did not exist.** 2021 `ST_GAS` peak **8,692 MW** against
  a vintage-2021 `ST_GAS` fleet of **7,411 MW** = **117.3 %**. The same ratio is 96.0 % in 2023.
  The +8.1 TWh `ST_GAS` overshoot is phantom capacity, not conduct.

### 3.5 A separate, tier-neutral hole: BA mis-attribution in EMAAC

`Linden Cogeneration` (974 MW) and `Bayonne Energy Center` (644 MW) are physically in New Jersey
inside EMAAC but carry `balancing_authority_code = NYIS` in EIA-860, so the model's `BA == 'PJM'`
filter drops them in **every** year — **1,618 MW / 8.2 TWh of 2021 CEMS output**. Present in-sample
too, so it cannot explain a tier boundary; it raises the EMAAC pocket's exposure everywhere and
only bites when defect 2 makes the import cut spuriously tight. In-sample-diagnosable.

---

## 4. Defect 3 — offer transforms anchored on 2023–2025 (HYPOTHESIS, not proven)

`apply_gas_offer_margin` (`data/offer_curves.py:664`):

    mc[g,t] += offer_markup_hr[g] × (anchor − fuel_price[g,t])

with `gas_offer_margin_anchor = 3.3483` — the **2023–2025 mean**, and per-zone anchors in
`constants.GAS_OFFER_MARGIN_ANCHOR_BY_ZONE["PJM"]` each documented as `mean(2023, 2024, 2025)`.
In-sample delivered gas ran **$2.19–$3.52**, so `(anchor − fuel)` is ±$1 and **the mechanism is
nearly inert exactly where it was identified**. In 2022 delivered gas was **$7.12**: the term is
~4× anything the identification window ever saw, and it marks gas offers *down*.
`COAL_SIGMOID_BACKCAST_GAS_MIN_MMBTU` (`config/fuel_trajectories.py:637`) is anchored the same
way — its own comment says *"minimum delivered gas price observed over the backcast window
(2023-2025)"*.

The residual **after** removing defect 2 matches the prediction's sign:

| | J | F | M | A | M | J | J | A | S | O | N | D |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2021 de-congested err | +35 % | +27 % | +8 % | +16 % | +14 % | +13 % | +14 % | +7 % | +3 % | −4 % | −4 % | +15 % |
| **2022 de-congested err** | −4 % | +19 % | +16 % | +6 % | +4 % | **−19 %** | **−17 %** | **−16 %** | +1 % | +1 % | +10 % | **−45 %** |

2022 flips to systematic **under**-pricing in the high-gas months while `CC_REGULAR` over-runs by
22.3 TWh — both what too-cheap gas offers produce. **Not measured here:** the fleet
reconstruction that would size `offer_markup_hr` needs `data/raw/pjm-da-virtuals/`, whose payload
is an untracked BLOAT-B corpus. This stays a hypothesis with a pre-registered screen (§7 F4).

---

## 5. What this does NOT establish

- **§4 is a hypothesis.** No magnitude was measured; the sign agreement is 2 years.
- **§3 predicts signs, not magnitudes.** +9,986 MW of coal *nameplate* is not +5,723 MW of
  *deliverable* peak; outages and derates sit in between. Only a solve settles it.
- **`CT_PEAKER` moves the wrong way** under the vintage (−766 MW against a −5.0 TWh under-run).
  Its likely owner is the registered `peak`-band multiplier (4.0), not the fleet.
- **The hydro −6 to −7 TWh and oil −1 to −2 TWh deficits are untouched and tier-neutral** —
  pjm-166 §7.5's lane, still open, still in-sample-diagnosable.
- **Nothing here is an out-of-sample skill number.** Validation tier is iterable
  model-SELECTION evidence (rule 22), and no parameter was identified against 2021 or 2022.
- **HEAD drift is not discharged.** pjm-166 §6 measured PJM's backcast path BIT-IDENTICAL at
  `4373b348c`, but `git diff 4373b348c..82a7742d` over the solve path is 59 files / +9,088
  lines. Unclassifiable at that size ⇒ LIVE ⇒ the screen earns a same-HEAD control
  (rule 29 (b)). Recorded in the PRECOMMIT.

---

## 6. Correction to pjm-166

pjm-166 §2 concluded the miss is *"an additive over-generation … not a reordering at constant
total"* and §7.4 recommended **retiring the coal↔CC merit-order framing** from the PJM lever
queue. That reading rests on the `classFull` coal benchmark (165.2 TWh). On **EIA-930 PJM-metered
generation** the 2021 miss is a near-conserving swap:

| basis | model gas | benchmark | Δ | model coal | benchmark | Δ | **net** |
|---|---|---|---|---|---|---|---|
| `classFull` (pjm-166's basis) | 346.5 | 312.9 | +33.6 | 152.3 | 165.2 | −12.9 | **+20.6** |
| **EIA-930 metered** | 346.5 | 311.7 | +34.8 | 152.3 | **183.5** | **−31.3** | **+3.5** |

The two bases agree on gas to 1.2 TWh and disagree on **coal by 18.3 TWh** (`classFull` 165.2 vs
EIA-930 183.5 vs CEMS 157.2) — so the entire "additive surplus vs swap" question is a coal-
benchmark question, not a model question. Same three-bases trap pjm-158 recorded. EIA-930 is
PJM's own BA-metered net generation and is the basis C2 itself scores against
(`fuelRows.coal.b = 183.54`). **§7.4's recommendation should not be actioned** — the
coal↔CC channel is the object, though its cause is the fleet registry (§3), not offer position,
so pjm-166 §1's elasticity work stands and is not contradicted.

Note also that **C2 passed on both held-out years** while model coal sits 17 % below metered:
C2 scores hourly shape (`r` 0.934, `nrmse` 0.217), not annual level. A class can be a third of a
fleet short and still pass C2. Flagged for the audit desk; no gate is changed here.

---

## 7. Recommendations

1. **F1 — make the backcast fleet registry track the solve year.** The machinery exists
   (`paths.set_eia860_vintage`, `ScenarioConfig.eia860_vintage_year`, vintages 2018–2024 all
   committed); what is missing is that the knob is a **run-level scalar** while a rule-16 bundle
   spans three years. Add a gate that resolves the vintage **per solve year**, falling through to
   the canonical snapshot where no vintage directory exists. Zero fitted scalars; forward-
   applicable (a forecast takes the latest vintage, as it does today). PRECOMMIT:
   `docs/handoffs/PRECOMMIT-pjm167-fleet-vintage-screen-2026-09-06.md`.
   *Note the field's own docstring calls its effect "small (~0.4 % of ERCOT installed capacity)"
   — an assessment made on ERCOT inside 2023–2025, where it is small. For PJM 2021 it is 39 % of
   the coal fleet. The docstring should be corrected in the same PR.*
2. **F1b — extend `RETIREMENT_WINDOW_START` to 2019 and arm `partial_plant_exit_carry` for PJM.**
   The complement of F1 for any year with no committed vintage, and the only route to *unit*-grain
   exits at surviving plants (Morgantown, Chalk Point, Waukegan). Rebuilding the retiree parquet
   needs the raw EIA-860 release zips, which are not on disk — re-fetch required.
3. **F2 — repair the EMAAC interface-limit intake** with a per-year admissibility test on the
   feed itself (e.g. `P(flow > limit) < 5 %`), falling through to the static seed where the
   posted series fails it. Screen **after** F1 lands: both act on the same pocket and would
   otherwise be confounded.
4. **F3 — fix the Linden/Bayonne BA attribution** (§3.5). In-sample-diagnosable; screen on
   2023–2025 first, where it costs no holdout.
5. **F4 — screen the offer-anchor extrapolation** (§4). Screen year **2022**, chosen because the
   mechanism's own footprint is largest there ($7.12 gas against a $3.35 anchor), *not* because
   the residual is largest. Structural gate only.
6. **Do not tune anything to 2021 or 2022** (rule 22 step 3). Every repair above is an input or
   construction change applied identically to all years, which is what rule 22's "what is held
   out is the SCORE, never the DATA" requires.

## 8. Matrix

No mechanism cell moves: nothing was tested (rule 32 duty (b) binds on a test, not a diagnosis).
Open item for the F1 session: `eia860_vintage_year` has **no row** in
`docs/codebase-site/data/mechanism-matrix.js` — it predates the duty-(c) CI guard and is named
only inside other rows' `def` text. The session that screens it adds the row and its per-ISO cells.
