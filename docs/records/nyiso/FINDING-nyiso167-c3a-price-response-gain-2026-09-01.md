# FINDING — nyiso-167: C3a-2025 is not a year-specific miss. It is a year-invariant PRICE-RESPONSE GAIN of ~0.70, and the "winter face" is 87 % that gain

**Date:** 2026-09-01 · **Lane:** NYISO calibration · **Shorthand:** nyiso-167
**Object:** the single load-bearing rubric failure standing between NYISO and a
CALIBRATED determination — **C3a mean LMP, 2025, −11.5 % (MODEL MISS)** on the
designated keeper `2026-08-30-nyiso-159-loss-surface`.
**Zero solve.** Committed artifacts only: the keeper's run payload, its
`hourly/system_<year>.parquet` sidecars, the committed per-ISO bench parts, the
committed hourly/zonal actual-LMP reference and the measured Transco Z6 NY daily
gas series. No LP ran. No `ScenarioConfig` field, mechanism, matrix cell, keeper,
shard, marker or determination changed. **Rule 22 `[R-HOLDOUT]`: every year read
is 2023, 2024 or 2025** — no out-of-training year was solved, scored, registered
or read; the spend freeze is untouched and no marker was requested.
**Probe of record:** `scripts/probes/nyiso167_price_gain_attribution.py`
→ `results/calibration/_nyiso167_price_gain_attribution.json`.

---

## 0. The result in one paragraph

C3a-2025 has been carried as a **year-specific** miss, decomposed at nyiso-156
into a "winter face" (Jan+Feb-2025 downstate premium, −$3.92) and a "summer
face" (the ledgered C3c scarcity days, −$3.94), with the winter half
identification-blocked behind the walled MyNYISO AORR table — the state the
unruled `DECISION-CARD-nyiso161` asks the owner to rule on. **That framing does
not survive contact with the keeper's own committed record.** The model's price
response across all 36 training months is one stable affine law,

> **model = 0.7032 × actual_RT + $11.03**  (R² 0.910, residual sd $4.93)
> **model = 0.7236 × actual_DA + $10.06**  (R² 0.947, residual sd $3.80)

whose gain is reproduced independently by the price-vs-load gradient
(0.752 / 0.662 / 0.664 per year, R² ≥ 0.99) and by the gas passthrough slope
(0.714). A gain below 1 makes the model's error a pure function of the year's
price LEVEL — `(gain − 1)·A + offset` — so C3a passes only for an annual actual
mean inside **$27.8 … $56.0/MWh**. 2023 ($32.25) and 2024 ($38.12) are inside
it; **2025 ($66.43) is 19 % above its upper edge, and that alone is the −11.5 %.**
Measured against this law, **87.4 % of the card's winter face is the same
system-wide gain**, leaving −$0.51/MWh genuinely winter-specific — and neither
January nor February is a statistical outlier (z −0.32, −0.92). The **only**
month in 2025 that is (June, z −2.71) is the RT-only scarcity event already
ledgered as C3c.

---

## 1. What was measured, and off what

Every number below is read from artifacts that were already committed before
this session; nothing was re-derived, re-solved or re-fitted.

| input | path | role |
|---|---|---|
| keeper run payload | `frontend/data/backcast/runs/2026-08-30-nyiso-159-loss-surface.js` | per-zone monthly model price `pMon` and demand weight `dMon` — the **same** two fields `calibration_verdict.score_price_mean` weights to produce the gated C3a number |
| bench parts | `frontend/data/backcast/bench/NYISO/{2023,2024,2025}.json.gz` | `avgLMP.rt_lw_mon` / `da_lw_mon` — the gated like-for-like load-weighted actual |
| keeper hourlies | `results/calibration/nyiso159_lossarm_B/hourly/system_<year>.parquet` | P1 zonal price + demand → the model's hourly load-weighted system price and load (rule 15's stated purpose for the sidecars: read the keeper, do not replay it) |
| hourly actual | `data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet` | RT/DA hub series on the model's own standard-time calendar |
| zonal actual | `data/raw/_validation-source/actual_lmp.json` → `NYISO.<year>.zones` | per-model-zone monthly RT/DA |
| gas driver | `data/raw/gas-prices/transco_z6_ny_daily.csv` | measured Transco Z6 NY daily spot, month-meaned, used **only as a regressor** |

Reproduction: `python scripts/probes/nyiso167_price_gain_attribution.py`.

## 2. The gain law, and why it is the whole of C3a-2025

### 2.1 The pooled monthly fit

Load-weighted over all 36 training months (weights = the scorer's own `dMon`):

| basis | gain | offset | R² | resid sd | crossover | **C3a pass window** |
|---|---|---|---|---|---|---|
| vs RT (gated) | **0.7032** | $11.03 | 0.910 | $4.93 | $37.15 | **$27.79 … $56.03** |
| vs DA (like-for-like) | **0.7236** | $10.06 | 0.947 | $3.80 | $36.40 | $26.73 … $57.02 |

The DA basis is the honest comparable — the scorer's own docstring says the
model "is structurally a real-time analogue" but a perfect-foresight LP has no
mechanism for the DART risk premium, so DA is where the model's *deterministic*
price formation is visible and RT adds the scarcity tail it cannot form. The law
is tighter there (R² 0.947), which is the expected direction.

**Each year's own monthly law reproduces that year's gated C3a number to $0.17
or better**, and the pooled law to $1.07 — the annual mean the scorer gates on
is very nearly *nothing but* the year's price level put through the gain:

| year | own-year law | predicted mean | pooled-law prediction | keeper's actual model mean |
|---|---|---|---|---|
| 2023 | 0.7118·A + 10.05 | $33.00 | $33.70 | $33.01 |
| 2024 | 0.6550·A + 12.65 | $37.62 | $37.83 | $37.66 |
| 2025 | 0.6704·A + 14.11 | $58.64 | $57.74 | $58.81 |

The three own-year gains (0.712 / 0.655 / 0.670) are the invariance: they move
by less than the fit's own residual scatter while the year's price level moves
by a factor of two.

### 2.2 The pass window is the whole story

Under `model = g·A + c`, relative error is `(g − 1) + c/A`, monotone decreasing
in `A`. With `g = 0.703, c = 11.03` the model **over**-prices a cheap year and
**under**-prices an expensive one, and C3a's ±10 % band is cleared only inside
`c/(0.10 + 1 − g) ≤ A ≤ c/(1 − g − 0.10)`:

| year | actual RT lw | position | model | error | C3a |
|---|---|---|---|---|---|
| 2023 | $32.25 | inside ($27.8–$56.0) | $33.01 | +2.4 % | PASS |
| 2024 | $38.12 | inside | $37.66 | −1.2 % | PASS |
| 2025 | **$66.43** | **19 % above the upper edge** | $58.81 | **−11.5 %** | **FAIL** |

2023 and 2024 do not pass because the model prices those years well. They pass
because their price level sits near the gain law's crossover, where the
gain deficiency and the positive offset cancel. **The three years are one
observation of one defect at three price levels, not two successes and a
failure.**

### 2.3 The same gain, measured two other ways

**Price-vs-load gradient** (hourly, from the keeper's own sidecars; deciles of
model load, model price vs actual DA):

| year | model d0 → d9 | actual DA d0 → d9 | model spread | DA spread | **decile-ladder gain** | R² |
|---|---|---|---|---|---|---|
| 2023 | 21.45 → 46.37 | 18.65 → 49.90 | $24.92 | $31.25 | **0.752** | 0.990 |
| 2024 | 25.80 → 51.29 | 21.81 → 60.01 | $25.49 | $38.20 | **0.662** | 0.998 |
| 2025 | 33.73 → 84.31 | 29.38 → 106.40 | $50.58 | $77.02 | **0.664** | 0.995 |

The model **over**-prices the bottom deciles by $3–4 and **under**-prices the
top by $17–22 (2025), on a ladder that is linear to R² ≥ 0.99. This is a
supply-curve slope deficiency at both ends, not a level error and not a tail
artifact — the top decile is nowhere near capacity-bound (measured on
`class_hourly_2025.parquet`, decile-9 mean dispatch is 43 % of ST_GAS's annual
max, 23 % of CT_PEAKER's, 53 % of imports', 4 % of oil's).

**Gas passthrough slope** ($/MWh per $/MMBtu of Transco Z6 NY, 36 months):

| series | system | Upstate_West | Capital_Hudson | Lower_Hudson | NYC | Long_Island |
|---|---|---|---|---|---|---|
| model | 6.38 | 5.98 | 6.63 | 6.69 | 6.66 | 6.66 |
| actual RT | 8.33 | 6.95 | 9.92 | 9.00 | 10.16 | 9.82 |
| actual DA | 8.94 | 7.48 | 10.74 | 9.55 | 10.42 | 10.59 |
| **model / actual DA** | **0.714** | 0.799 | 0.618 | 0.700 | 0.639 | 0.629 |

Two things are visible. First, the system ratio **0.714** is the same number as
the monthly gain — the passthrough deficit *is* the gain deficit. Second, the
model's slope is **essentially flat across all five zones (5.98–6.69)** while the
market's rises from 7.48 upstate to 10.4–10.7 downstate: the model's marginal
unit is the same efficient combined-cycle everywhere, at every gas price, while
the market's downstate marginal unit is materially less efficient and/or pays a
gas basis that widens with the hub. The upstate leg of the deficit (0.799) is
**not** covered by any downstate/in-city explanation.

## 3. The decisive test — the winter and summer "faces" as residuals

A face that is a **separate component** of the miss must appear as a large
negative residual off a law fitted to every *other* month. Residuals off the
pooled 36-month law, and the annual load-weighted contributions in the units
the decision card states its arithmetic in:

**Gated RT basis** (the card's basis; 2025 raw total −$7.870/MWh):

| component | raw contribution | of which the gain law | **genuinely month-specific** | share explained by the gain | month z |
|---|---|---|---|---|---|
| whole year 2025 | −$7.870 | −$8.763 | **+$0.893** | — | — |
| **winter face** (Jan+Feb) | −$4.072 | −$3.558 | **−$0.514** | **87.4 %** | −0.32, −0.92 |
| summer face (Jun+Jul) | −$3.701 | −$2.422 | −$1.278 | 65.5 % | **−2.71**, −0.21 |

**DA basis** (2025 raw total −$6.715/MWh):

| component | raw | law | residual | share | month z |
|---|---|---|---|---|---|
| whole year 2025 | −$6.715 | −$8.049 | +$1.334 | — | — |
| **winter face** | −$4.295 | −$3.411 | **−$0.883** | **79.4 %** | −1.77, −0.82 |
| summer face | −$1.108 | −$1.580 | **+$0.471** | (over-explained) | +1.13, +0.23 |

Read these three ways:

1. **The winter face is not a component.** Once the gain law is applied,
   Jan-2025 and Feb-2025 are −$0.51/MWh of annual contribution between them on
   the gated basis, and **neither month is a statistical outlier** (|z| ≤ 0.92
   on RT, ≤ 1.77 on DA, against a $4.93/$3.80 residual sd). They are the two
   highest-price months of the year, and a 0.70-gain model under-prices the
   highest-price months by construction. The −$3.92 the card attributes to a
   blocked AORR input is, on this measurement, ~$3.4–3.6 of the same deficiency
   that also produces the Mar–Dec errors.
2. **The summer face behaves exactly as its ledger says.** On the DA basis it
   has no residual at all (+$0.47 — the model matches DA in June to −0.6 %:
   $52.80 vs $53.12); the whole June miss is RT-only. On the RT basis June is
   the **one** genuine outlier of 2025 (z −2.71). That is the C3c scarcity
   limitation, correctly ledgered, appearing in the mean — and it confirms the
   probe is capable of detecting a real separate component when one exists.
3. **After the gain, 2025 has no unexplained deficit left.** The year's residual
   is **+$0.893** (RT) / **+$1.334** (DA) — positive. There is nothing else to
   find in 2025.

### 3.1 What this means for the unruled nyiso-161 card

`DECISION-CARD-nyiso161` §4.5 proposes an ACCESS-BLOCKED INPUT caveat class
whose **eligibility test (a)** is *"decisive attribution — a committed
same-keeper attribution probe (no solve) shows the named blocked component
alone, removed arithmetically, returns the record to band (here: −7.62 + 3.92 →
in band). **A component that merely helps does not qualify.**"*

This probe is that probe, and it answers **NO on test (a) as written**. The
arithmetic (−7.62 + 3.92) is correct; the *attribution* is not. 87.4 % of that
$3.92 is a system-wide gain deficiency that is equally present in 2023 and 2024
and in every month of 2025, and the residue that is genuinely winter-specific
is **−$0.51/MWh — 0.8 % of the actual mean**, an eighth of the value the test
would credit to the blocked input. Removing Jan+Feb does return the year to
band, but it does so by removing the two months where a level-dependent error
is largest, which is the definition of "merely helps."

**Nothing here rules the card, and nothing here is a recommendation on it.** The
card is the owner's; this finding supplies the measurement its own test (a)
calls for, which did not exist when the card was filed, and it points in the
direction of the card's own **Option A** (no amendment) — not because the label
is unearned, but because the named blocked component is not the object. Two
further consequences the owner should have in front of them:

* **The AORR intake would not have closed C3a-2025 either.** Leg 2's promise, as
  recorded, was ≈ −5.6 % → in band. On this measurement the in-city commitment
  object can reach at most the winter-specific residue plus whatever share of
  the *downstate gain* it carries; the **upstate** passthrough deficit (0.799,
  on 34 % of ISO load) is outside its reach entirely. The access wall is real,
  but it was never the whole gate.
* **The gain law predicts the holdout ladder.** Any year whose actual
  load-weighted mean is outside $27.8–$56.0/MWh fails C3a on this keeper
  *before* any year-specific physics is considered. This is a standing property
  of the current recipe and belongs in the touchpoint-loop planning, not in a
  surprise after a spend. (No out-of-training year was read, scored or estimated
  here; the statement is a property of the fitted law, not a prediction quoted
  from any 2019–2022 actual.)

## 4. The gain deficiency is not NYISO's — and NEISO is the in-repo counterexample

The same pooled monthly fit, run on **every ISO's designated keeper** at this
session's HEAD (rule 25 `[R-ISO-SCOPE]`: this is a **measurement**, and it fills
no other ISO's matrix cell, transfers no verdict, and adjudicates nothing
outside NYISO):

| ISO | keeper | **gain** | offset | R² | C3a pass window ($/MWh) |
|---|---|---|---|---|---|
| ERCOT | `2026-08-25-234-eastex-identity` | 0.347 | $19.24 | 0.876 | 25.6 … 34.8 |
| MISO | `2026-08-30-miso-191-bexit` | 0.500 | $16.10 | 0.689 | 26.8 … 40.2 |
| PJM | `2026-08-15-pjm-162-inputclock` | 0.668 | $11.16 | 0.722 | 25.9 … 48.2 |
| **NYISO** | `2026-08-30-nyiso-159-loss-surface` | **0.703** | $11.03 | 0.910 | **27.8 … 56.0** |
| CAISO | `2026-08-26-caiso-220-c1-crosswalk` | 0.837 | $10.49 | 0.971 | 39.9 … 167.4 |
| NEISO | `2026-08-17-neiso-99-joint-p1` | **0.986** | $2.29 | 0.977 | 20.1 … ∞ |

Every keeper but NEISO's carries a gain below 1 and therefore a bounded C3a
pass window in price level. NYISO's is the **fourth best of six** and its window
is the second widest. **NEISO's keeper reproduces essentially the full measured
price gradient** (gain 0.986, offset $2.29, R² 0.977) — so the deficiency is not
an inevitable property of an hourly perfect-foresight LP. Something structural
closes it.

**What NEISO arms that NYISO does not** (diff of the two keepers'
`meta.json`, restricted to price-formation gates; stated as an **association and
an open question, not an attribution** — this session measured no mechanism):

| flag | NEISO | NYISO | NYISO matrix cell |
|---|---|---|---|
| `neiso_winter_fuel_inventory` | True | — | `winter_fuelsec_posture` `·` |
| `neiso_winter_fuel_mustrun` | True | — | `·` |
| `neiso_gas_coldsnap_derate` | True | — | `gas_coldsnap_derate` `·` |
| `scarcity_price_overlay` | True | — | `ordc_scarcity_overlay` `·` |
| `temp_dependent_derate` | True | **False** | **`G`** |

All five are **supply-side capability contraction at physical extremes** — the
mechanism class that steepens a supply curve where the model's is flattest. Two
disciplines apply and are recorded so a successor does not misread this table:

* **`temp_dependent_derate` is closed for NYISO on the merits and stays closed.**
  It is `G`, refused ex-ante at nyiso-111 on NYISO's **own** measured conduct
  (the fleet's capability–temperature slope comes out sign-inverted, i.e. the
  physics is measured absent, exactly as ERCOT's own refutation at ercot-177
  found for ERCOT). Rule 28(a): do not re-test it. Nothing in this finding is
  new evidence on that cell.
* **The four `·` cells are NYISO-lane questions, not transfers.** Rule 28(d): a
  NEISO verdict never fills a NYISO cell. If a successor re-examines whether
  the winter-fuel-security class is genuinely n/a for a market with NYISO's
  downstate winter gas constraint, it enters as `U` and is parameterized from
  NYISO's own data or not at all.

## 5. Lines this session closes, and one it does not open

* **CLOSED — "C3a-2025 needs a 2025-specific driver."** Falsified at R² 0.91/0.95
  over 36 months with 2025's whole-year residual off the law reading **+$0.89**.
  Do not open a 2025-only input, weather-year or regime hypothesis without new
  evidence that survives this law.
* **CLOSED — "the DA−RT premium sign flip in 2025 points at an input defect."**
  It does not. The 2025 flip (−$1.13, vs +$0.69/+$0.62 in 2023/24) is a
  **market** fact concentrated in one month: June-2025 actual RT $78.42 vs DA
  $53.12, a $25/MWh RT-over-DA in the RT scarcity hours C3c already ledgers.
  The model matches June DA to **−0.6 %**. **Excluding June alone, 2025's
  load-weighted DA−RT premium is +$1.15/MWh** — same sign and same family as
  2023 (+$0.69) and 2024 (+$0.62); the entire −$1.16 flip is one month. There
  is no instrument defect here — the
  nyiso-165 §5 cascade-defect class was ruled out by direct measurement (the
  model's DA-basis error is a smooth function of price level, which a summed or
  clock-shifted input would not produce).
* **NOT OPENED — the offer-side `gas_offer_net_revenue_margin` line.** The
  mechanism (cell `K`, nyiso-72) does mechanically reduce passthrough slope: it
  reprices each gas tranche's markup as a fixed $/MWh margin at a per-zone
  delivered-gas anchor, so a tranche's `d(mc)/d(fuel)` becomes `phys × HR`
  rather than `mult × HR`. On NYISO's registered `offer_curve_by_group` the
  `phys/mult` ratios are 0.825/0.925 (CC_REGULAR econ), 0.769/0.733 (ST_GAS
  econ) and 0.661/0.658 (CT_PEAKER econ), which bounds the mechanism's share of
  the 0.714 passthrough ratio at roughly a third — **and it is not a defect**:
  the anchor is a measured identification point (`mean(3.3566, 2.7969, 5.5602)`
  over the same 2023–2025 window the band multipliers were calibrated on,
  `derive_gas_offer_margin_anchor.py`, rule 23 frozen), the bands were pooled on
  that same window, and re-anchoring per year would be a **derivation⇄dispatch
  basis mismatch in the opposite direction** with the residual as its only
  motive. Recorded here so a successor does not spend a solve rediscovering it;
  **no cell moves.**

## 5.1 Side repair, found while discharging rule 28(a): the NYISO shard did not parse

Checking `docs/codebase-site/data/mechanism-matrix/NYISO.js` before touching it
showed the **committed file is not valid JavaScript**: line 143's
`egrid_identity_heat_rates` entry ends `... [8.3434,8.5266])." }` with **no
trailing comma**, so the next entry (`da_virtual_bids`) is a syntax error and
`window.MECH_MATRIX_SHARDS.NYISO` never gets assigned — i.e. **NYISO's entire
column has been missing from the rendered `mechanism-matrix.html` page**, not
just the annotated cell. Verified with `node --check` against the HEAD blob
before any edit of mine, so it is pre-existing (introduced with the nyiso-151
evidence rewrite, merged in `c66a595d`); all five other shards and the base file
compile. **Repaired here** — one character — and every shard now passes
`node --check`.

Why CI did not catch it: `scripts/check_mechanism_matrix.py` reads the shards
with its own Python-side parser and reports "integrity OK" on a file no browser
can load. It passed before this repair and passes after. A `node --check` leg
over `docs/codebase-site/data/**/*.js` would have caught it on the PR that
introduced it. That is a governance-round change to the guard, not this lane's,
and is filed here rather than built.

## 6. Why no lever was solved, stated plainly

The object this session hands forward is **the price-response gain**, not the
winter face. No admissible lever for it survived pre-registration today:

1. The in-city commitment object (`scuc_load_pocket_commitment` `G`,
   `nyiso_incity_commitment_obligation` `R`) is access-blocked and, per §3.1,
   reaches at most a fraction of the object even if the wall fell.
2. `nyiso_iroquois_winter_spread` is `R` twice with a sharpened re-open bar
   (nyiso-150, nyiso-157); this finding is **not** new evidence on it — it
   argues the winter face is smaller than believed, which strengthens the
   rejection rather than reopening it.
3. `temp_dependent_derate` is `G` on NYISO's own measured conduct (§4).
4. The offer-side line is bounded and not a defect (§5).

Building a mechanism that steepens the supply curve *because the residual wants
it steeper* is precisely what rule 1 `[R-STRUCT]` forbids, and there is no
measured NYISO driver in the repo today that identifies one. So this session
delivers the attribution and stops, rather than spending a solve on a lever it
can already predict will not close the gate.

## 7. Honest expected value

**What is delivered.** A committed, reproducible, zero-solve attribution that
(a) falsifies the year-specific framing of C3a-2025 at R² 0.91–0.95, (b) shows
87.4 % of the decision card's winter face is a system-wide gain deficiency and
answers the card's own eligibility test (a) **NO as written**, (c) supplies the
`$27.8–$56.0/MWh` pass window as a standing property of the recipe that the
touchpoint ladder must plan around, (d) confirms the summer face is exactly the
ledgered C3c limitation and nothing more, and (e) establishes that the gain
deficiency is a cross-ISO model-class property with NEISO as the in-repo
existence proof that it is closable.

**What is NOT delivered.** No gate moves. C3a-2025 is still −11.5 %, C3c still
fails, the determination is still **NOT-YET on {C3a-2025, C3c}**, and NYISO
still does not read CALIBRATED. No mechanism was tested, so no matrix cell
verdict moves and no run is registered (rule 15 governs completed solves; this
session ran none). No keeper, shard or marker changed. The nyiso-161 card
remains **filed and unruled** — this finding is evidence for the owner's
ruling, not a ruling.

**What could still be wrong.** The affine law is a *description*, not a
mechanism: it says the model's price response is uniformly too weak, not why.
A single mechanism might account for all of it, or five might account for a
fifth each. The cross-ISO gains are read off six keepers with different fleets,
years and armed recipes, so the ordering is suggestive and the NEISO/NYISO flag
diff in §4 is an association only — a successor must adjudicate any of it on
NYISO's own data. And the gas-passthrough regressions use one hub series
(Transco Z6 NY) as the regressor for all five zones, which is correct for
detecting a *relative* zonal slope gradient but is not a per-zone delivered-cost
measurement.

## 8. Evidence

* `results/calibration/_nyiso167_price_gain_attribution.json` — the probe record
  (all five measurements, both bases, per-month residuals).
* `scripts/probes/nyiso167_price_gain_attribution.py` — the probe.
* `results/calibration/nyiso159_lossarm_B/` — the keeper bundle read
  (`metrics.json`, `run_config.json`, `meta.json`, `hourly/`).
* `docs/DECISION-CARD-nyiso161-winter-face-waiver-2026-08-30.md` §2, §4.5(a),
  §5 — the framing this finding tests, and the eligibility test it answers.
* `docs/DECISION-CARD-nyiso156-2025-offer-level-2026-08-25.md` §4 — the face
  arithmetic (−$3.92 / −$3.94 / +$0.59) reproduced and re-attributed here.
* `docs/FINDING-nyiso164-c3c-product-level-2026-09-01.md`,
  `docs/FINDING-nyiso165-as-reference-repair-2026-09-01.md` — the C3c and
  instrument-defect lines this session did not re-open (§5).
* `docs/codebase-site/data/mechanism-matrix/NYISO.js` — the shard, annotated
  (no verdict moves) and syntax-repaired (§5.1);
  `scripts/check_mechanism_matrix.py` — the guard that passed either way.
* `results/calibration/FINDING-nyiso111-ramp-envelopes-2026-08-02.md` §2 —
  `temp_dependent_derate` refused ex-ante on NYISO's own conduct.
* `scripts/data/derive_gas_offer_margin_anchor.py`,
  `src/market_sim/config/constants.py` `GAS_OFFER_MARGIN_ANCHOR_BY_ZONE`,
  `src/market_sim/data/offer_curves.py::apply_gas_offer_margin` — the offer-side
  line bounded in §5.
* CLAUDE.md rules 1 `[R-STRUCT]`, 13 `[R-MEASURED]`, 14 `[R-ACCURATE]`,
  22 `[R-HOLDOUT]`, 25 `[R-ISO-SCOPE]`, 28 `[R-MECH-MATRIX]`.

Next shorthand: nyiso-168.
