# FINDING — miso-105: MISO **does** publish the submitted virtual curve, and that is exactly how we can prove the lever is REFUSED (ex-ante, 2026-07-29)

**Verdict: `da_virtual_bids` is GOVERNANCE-REFUSED for MISO — adjudicated
ex-ante, NO SOLVE SPENT.** Unlike nyiso-94, the data exists, is submitted, is
priced, and was fully measured across all three training years. The refusal is
therefore *stronger*, not weaker: the mechanism was evaluated on MISO's own
complete book and **its admissible channel is immaterial to the target while its
material channel is inadmissible.**

Matrix cell `da_virtual_bids` × MISO: **U → G**
(`docs/codebase-site/data/mechanism-matrix.js`, cat `offer`). Lever-queue basis:
`docs/mechanism-testing-matrix.md` §5.4 MISO item **3** ("DA virtual depth …
the diurnal-spread compression is a DA-formation signature; untested").

Reproduce:

```
uv run python scripts/probes/miso105_da_virtual_identifiability.py --semantics
uv run python scripts/probes/miso105_da_virtual_identifiability.py --years 2023 2024 2025
uv run python scripts/probes/miso105_da_virtual_identifiability.py --analyze
```

**No keeper candidate. No dashboard registration** — rule 15 `[R-DASHBOARD]`
governs *completed runs*, and there is none (same posture as nyiso-93/94 and
miso-104). **Keeper `2026-07-28-miso-101b-tempgrain` is untouched.**

---

## 1. The one-line reason

**MISO's virtual book is a convergence instrument, not a depth instrument.** Its
*net* position — the only part of it the PJM mechanism is built on — is
+0.4/+1.2/−0.2 GW at peak against PJM's +7–11 GW, and it buys **1.3–5.1 % of the
C3b diurnal-spread gap**. The only part of the measured curve large enough to
move C3b is its **price elasticity**, and that elasticity is centred, to
**$0.09–$1.80**, on the price at which the book actually cleared. Arming it would
hand roughly **one third of every hour's price formation — and ~two thirds in the
tight summer hours C3b is decided in** — to a measured clearing outcome. That is
rule 1 `[R-STRUCT]`'s prohibition on reaching the right number through something
that is not doing the model's job, and it fails rule 13 `[R-MEASURED]`'s forward
test.

## 2. Source, grain and vintage (Stage-1 question (a)) — **PASSES**

MISO **does** publish a submitted, priced virtual bid/offer curve. This is a new
fact for the repo; no prior session had located it.

| feed | what it carries | grain | vintage |
|---|---|---|---|
| **MISO `YYYYMMDD_bids_cb.zip`** (`docs.misoenergy.org/marketreports/`) | `Region, Market Participant Code, Date/Time Beginning (EST), MW, LMP, Type of Bid, Bid ID, PRICE1..9, MW1..9` | one row per **bid × hour**, `Region` ∈ {North, Central, South, ·} | FERC-Order-719 masked archive, **~90-day lag** (2023-06-15 posted 2023-09-13). Probed: 2023-01-01 → 2026-01-01 all HTTP 200; 2022-06-01 and earlier **404** |
| **MISO 2024 SOM Appendix** Table A2 (in repo, `data/raw/MISO/`) | published **cleared** virtual volume as % of load, five RTOs | annual | 2025-06 |
| **MISO 2025 SOM** §IV.B, Figure 20 (in repo) | offered **and** cleared virtual supply/demand, IMM commentary | annual/monthly | 2026-05 |

`Type of Bid`: **`D`** = virtual demand (DEC), **`I`** = virtual supply (INC),
`F` = fixed physical demand, `P` = price-sensitive physical demand.

**The rolling window is quarantine-safe by construction**: it covers exactly
2023–2025 (+2026 forecast-side) and 404s on every rule-22 holdout year, so no
authorization question arises.

### 2.1 The ladder semantics were IDENTIFIED from the file, not assumed

The cleared `MW` column is an exact function of the submitted ladder and the
clearing `LMP` (a DEC block clears at or above the LMP, an INC block at or
below). Whichever reading of `MW_i` reproduces the published cleared MW *is* the
file's semantics. On 2023-06-15, 207,549 priced virtual bid-hours:

| reading of `(PRICE_i, MW_i)` | reproduces cleared `MW` | MAE |
|---|---|---|
| **INCREMENTAL blocks** | **99.36 %** | **0.028 MW** |
| CUMULATIVE ladder | 93.49 % | 0.410 MW |

That same test settles provenance in the strong direction: **66.66 % of priced
bid-hours carry submitted blocks that did not clear**, so the ladder is the
*submitted* curve, and clearing is derivable from it rather than being a separate
series. This is PJM's `hrl_da_incs_decs` structure — per-bid rather than
pre-aggregated to price points.

### 2.2 Grain caveat, stated up front

`Region` is populated for only ~66 % of the book. Shares of submitted / cleared
virtual MW, 2023–2025 pooled:

| region | submitted | cleared |
|---|---|---|
| North | 34.2 % | 29.2 % |
| Central | 26.9 % | 24.0 % |
| South | 5.0 % | 4.5 % |
| **(no region tag)** | **34.0 %** | **42.2 %** |

The *system* curve is complete, and the PJM mechanism is system-wide anyway
(`virtual_bids._load_bids_frame` reads no location column and allocates by zonal
load share), so this is not the blocker. It is recorded because any future
zone-scoped variant would be building on a third of the book with no location.

## 3. Provenance cross-check (Stage-1 question (b)) — **PASSES, positively**

nyiso-94 used the IMM cross-check to prove a candidate series was *cleared*. Here
it runs in both directions on the same file, which is a stronger result: the
`MW` column reproduces the IMM's published cleared volume, **and the submitted
ladder is 2.5–2.8× larger**, so the submitted half is positively identified
rather than merely not-excluded.

| year | submitted DEC / INC (GW/h) | cleared DEC / INC (GW/h) | cleared as % of model load | submitted ÷ cleared |
|---|---|---|---|---|
| 2023 | 32.79 / 34.19 | 12.08 / 11.93 | 16.5 % / 16.3 % | 2.79× |
| **2024** | 32.40 / 26.23 | 11.99 / 10.97 | **16.3 % / 14.9 %** | 2.55× |
| 2025 | 34.87 / 24.90 | 12.00 / 11.97 | 15.8 % / 15.8 % | 2.49× |

**MISO IMM 2024 SOM Appendix Table A2: cleared virtual load 15.8 %, cleared
virtual supply 14.5 % of load.** Measured here: 16.3 % / 14.9 % (the residual is
the denominator — Table A2 uses the IMM's own load basis, this uses the keeper's
73.6 GW mean). Same table: **PJM 5.9 % / 5.6 %**, NYISO 6.3 % / 7.4 %.

So MISO's *gross* virtual market is ~2.7× PJM's as a share of load. That is what
makes the next section decisive rather than obvious.

## 4. The premise is FALSE in MISO (Stage-1 question (c)) — the charter's stop condition

PJM's mechanism exists because its DA market clears **more** than the physical
load the model serves: **+7–11 GW net DEC at the top summer hours**
(`src/market_sim/data/virtual_bids.py` module docstring). MISO's does not.

Net **cleared** virtual (DEC − INC), model-clock hours, full 26,304-hour corpus:

| year | mean hour | peak HE16-18 | night HE01-03 | peak − night |
|---|---|---|---|---|
| 2023 | +153 MW | +378 | −1,018 | **+1,396** |
| 2024 | +1,023 MW | +1,223 | −54 | **+1,277** |
| 2025 | +31 MW | **−173** | −601 | **+428** |

By season, at the peak:

| season | 2023 | 2024 | 2025 |
|---|---|---|---|
| winter | −354 | +939 | +453 |
| shoulder | +379 | +737 | −399 |
| **summer** | **+1,090** | **+2,471** | **−337** |

**MISO's summer-peak net position is +1.1 / +2.5 / −0.3 GW against PJM's +7–11
GW — 5–30 % of it, and NEGATIVE in 2025, the year C3b actually fails.** The
mechanism would push the 2025 summer peak the wrong way.

In the measured RT>$300 tail (the nyiso-94 framing), net cleared virtual is
**−158 / +1,336 / −62 MW** across 6 / 13 / 28 tail hours — near zero and
sign-unstable. (NYISO's, for reference, was +580/+293/+917 MW, and nyiso-94
refused on it.)

**The IMM says the same thing in its own words.** 2025 SOM §IV.B: virtual
transactions are *"essential to price convergence because they arbitrage
differences between the day-ahead and real-time prices"*; participants use most
price-insensitive trades *"to arbitrage congestion-related price differences by
establishing an energy-neutral position between two locations (offsetting virtual
supply and demand trades)"* — these **matched** transactions alone average
**1,694 MW/h**. A book that is 15.8 %/14.5 % of load gross and ≈ 0 net is a
convergence and congestion instrument. It is not depth.

### 4.1 What the admissible channel is actually worth on C3b — 1.3 % to 5.1 %

C3b is diurnal-spread compression: the model reproduces 29–47 % of the observed
peak-minus-night spread (miso-89 §1). The peak-minus-night **net** virtual
differential is the entire admissible depth effect. Priced at the keeper's own
measured summer stack slope — re-measured this session from
`results/calibration/miso101_tempgrain_B/hourly/` by the miso-89 §2 ventile
method: **0.54 / 0.56 / 0.64 $/GW** mean (p90 0.87 / 0.91 / 2.50):

| year | peak−night net virtual | × stack slope | C3b summer spread gap (actual − model) | share closed |
|---|---|---|---|---|
| 2023 | +1.396 GW | **+$0.75** | 26.3 − 11.7 = $14.6 | **5.1 %** |
| 2024 | +1.277 GW | **+$0.72** | 30.1 − 14.2 = $15.9 | **4.5 %** |
| 2025 | +0.428 GW | **+$0.27** | 32.7 − 12.2 = $20.5 | **1.3 %** |

The admissible part of the mechanism closes **one to five percent** of the target,
and its contribution **shrinks as the miss grows**. On materiality alone this
would not be worth a solve.

### 4.2 The nyiso-94 blocker-3 test, run in MISO — and what carries the wedge

nyiso-94 killed its lever partly on the whole DA book sitting **below** RT load
(−846/−859/−869 MW). MISO's does not, so that specific blocker does **not**
transfer — and running it anyway is what shows the depth is not the virtuals':

| year | DA physical (F+P cleared) | net virtual | DA book | RT actual | DA − RT | peak HE16-18 DA − RT |
|---|---|---|---|---|---|---|
| 2023 | 73.9 GW | +0.15 | 74.0 | 73.2 | **+844 MW** | **+2,368 MW** |
| 2024 | 73.1 GW | +1.03 | 74.1 | 73.6 | **+469 MW** | **+1,942 MW** |
| 2025 | 75.5 GW | +0.03 | 75.5 | 75.8 | **−232 MW** | **+760 MW** |

Two things follow. **(i) The wedge is carried by the physical demand bid, not by
virtuals** — net virtual contributes +0.15/+1.03/+0.03 GW of a +0.8/+0.5/−0.2 GW
mean wedge, so `da_virtual_bids` is the wrong instrument for it even for a
session that wanted to chase it. **(ii) It moves the wrong way across years**:
the peak wedge shrinks 2,368 → 1,942 → 760 MW while the C3b miss grows
($14.6 → $15.9 → $20.5), the same sign problem as the net virtual position in §4.

**Stated as an observation, deliberately NOT chartered.** The comparison is
MISO's cleared physical demand bids against EIA-930 BA `Demand`, and those two
are not verified like-for-like — MISO's DA cleared demand can carry scheduling
elements (wheeling, export obligations) that EIA-930 BA demand excludes. Anyone
who wants to make something of the residual wedge owes it a boundary
reconciliation first (rule 14's named misalignment clause). It is recorded here
only because it is the measurement that rules the virtuals out of it.

## 5. The material channel is the inadmissible one (question (d), this session's addition)

MISO's book is big enough that the interesting question is not its net level but
its **elasticity**. Measured on the full corpus:

| year | crossing price λ0 of the measured net curve | price at which that book actually cleared (same MW weighting) | gap |
|---|---|---|---|
| 2023 | $28.50 | $28.41 | **$0.09** |
| 2024 | $27.94 | $26.14 | **$1.80** |
| 2025 | $38.05 | $37.88 | **$0.17** |

**The measured net virtual curve crosses zero at the price the market cleared
at.** That is not a defect of the data — it is what efficient arbitrage looks
like, and the IMM says so. But it is decisive for what the mechanism *does* in
the LP.

Local stiffness of the curve, and of the model's own stack:

| quantity | 2023 | 2024 | 2025 |
|---|---|---|---|
| \|d net / d λ\| at λ0 (GW per $/MWh) | 0.93 | 0.93 | 0.69 |
| gross submitted mass within ±$5 of λ0 (DEC / INC, GW) | 4.52 / 4.74 | 4.92 / 4.39 | 3.73 / 3.17 |
| model stack elasticity S = 1 ÷ (summer $/GW slope) | 1.85 | 1.79 | 1.56 |
| **share of any price displacement the curve would supply, N ÷ (S+N)** | **33 %** | **34 %** | **31 %** |
| same, at the steepest 2025 summer ventile (2.50 $/GW ⇒ S = 0.40) | — | — | **63 %** |

Reading: in any hour where the model's dual differs from λ0, arming this
mechanism closes about **one third** of the difference — and in the tight summer
hours that decide C3b, **nearly two thirds**. The model's price would
substantially *become* the crossing price of the measured book.

**Why that is not admissible here.**

* **Rule 1 `[R-STRUCT]`.** The gain would not come from the model's dispatch
  becoming right. It would come from a measured clearing price being blended into
  the dual at a ~⅓–⅔ weight. Rule 1 forbids reaching the right number through a
  mechanism that is not doing the model's job — and §4.1 has already established
  that the part of this mechanism which *is* doing the model's job is worth
  1.3–5.1 %.
* **Rule 13 `[R-MEASURED]`, the forward test.** *"Could this same quantity be
  produced for a forward year from forward drivers, and would it respond to
  changed conditions?"* Whatever carries the effect must reproduce **λ0** — and
  λ0 is, to $0.09–$1.80, the day-ahead price. A forward MISO virtual surface
  would have to be conditioned on the price the model exists to forecast. The
  submitted ladder is admissible in provenance; the *effect* has no forward
  analogue.
* **Rule 21 `[R-DOF]`.** A residual that closes only because a measured clearing
  price was injected at a fitted-in-effect weight is an open root-cause issue,
  not a parameter.

**This is a blocker nyiso-94 never reached**, because NYISO's data did not exist
to test it. It is recorded here as a new, general admissibility question for this
mechanism family: *how much of the model's price formation would the measured
book supply, and where is its crossing price relative to the answer?*

## 6. Rule 19 `[R-ONE-MECH]` — nothing was stacked

Enumerated from the keeper's own committed `legitimacy_diagnostics.json` (D-2)
before proposing anything, per rule 19's duty:

| mechanism forcing MISO dispatch on the keeper | window (D-4) | off-window share |
|---|---|---|
| `nuclear_mustrun` | — | — |
| `chp_steam` (CC_CHP / CT_CHP / ST_CHP) | h0–23 | 0.0 |
| `reliability_floor × CT_PEAKER` | h14–21 | 0.0 |
| `reliability_floor × ST_GAS` | h0–23 | 0.0 |
| `st_gas_mustrun_per_plant × ST_GAS` | h0–23 | 0.0 |

**None of these is a diurnal-price-spread mechanism** — they are commitment
floors, all D-4-clean. The DA-virtual layer is also not a floor (PJM's DEC rungs
carry `pmax = 0` with a negative `min_gen` and are excluded from D-2 attribution
by construction; the INC rungs carry no floor at all). So no stacking question
arose. **C3b's ledgered root cause is untouched**: the ~10 GW 2025 summer-peak
under-derate remains the instrument-blocked driver
(miso-89 §7; `docs/handoffs/miso-outage-grain-data-ask-2026-07.md`), and this
finding does not widen, re-scope or substitute for that ledger entry.

## 7. Rule 25 `[R-ISO-SCOPE]` — and one honest cross-ISO flag

**No parameter crossed a boundary in either direction.** PJM's `K` was not
ported; MISO's `G` touches no other cell. CAISO/NEISO stay `U` — whether either
publishes a submitted virtual curve is untested, and per rule 25 each must derive
its own answer from its own market.

**PJM's cell is NOT re-adjudicated by this finding, and must not be.** But the §5
question is a general property of the mechanism family, not a MISO quirk, and it
was never asked in PJM's lane. It is recorded here as an *observation for PJM's
lane to answer on PJM's own data*, not a verdict: what is PJM's λ0-versus-cleared
gap, and what is `N ÷ (S+N)` on PJM's own stack? PJM's premise is genuinely
different (+7–11 GW net DEC at peak is real depth that MISO does not have), so
the answer may well be that PJM's lever is carried by depth and not by the
attractor — which is exactly why it needs PJM's own measurement rather than
MISO's inference.

## 8. DOF ledger

**No parameter added, no scalar fitted, no solve spent.** The keeper's DOF ledger
is untouched (25 entries / 2 residual). Every number in this finding is either
measured from MISO's public archive, read from a committed keeper sidecar, or
quoted from a committed IMM report.

## 9. Governance

* Rule 22 `[R-HOLDOUT]` — 2023–2025 only. MISO carries no calibration-complete
  marker; the probe hard-fails any other year, and MISO's archive 404s on every
  holdout year regardless. Nothing was intaken and no authorization was needed:
  every byte was read in scratch and is re-fetchable from §2.
* Rule 15 `[R-DASHBOARD]` — no run produced, nothing to register.
* Rule 26 `[R-MECH-MATRIX]` duty (b) — `da_virtual_bids` MISO cell updated in
  this session.
* Rule 13 — nothing written under `data/raw/`. The archive carries cleared `MW`
  and `LMP` alongside the submitted ladder; parking that in the input tree would
  be a re-armable answer key (rule 26 `[R-DELETE]` in spirit).
* **Caveat budget unchanged at 3/3** (C3a, C3b, C3c). Nothing was ledgered, added,
  widened or re-scoped. C3b's determination is exactly where miso-90 left it.

## 10. DO-NOT-REDO

Do not re-open `da_virtual_bids` for MISO on this data. The blockers are
measurement, not access — the corpus is complete and committed to this finding.
Specifically **do not**:

* re-test the mechanism scoped to peak hours, to summer, or to a subset of
  regions (scoping to where the residual lives is rule 13/24 fitting);
* re-derive it with a different rung count, price grid, or crossing convention —
  §5's ratio is set by the measured book against the measured stack, not by
  rendering resolution;
* propose a "net-only" or "DEC-only" clamped variant — pjm-102/103/104 already
  adjudicated the clamped form as diagnostic scaffolding, and MISO's net is ≈ 0
  so a clamp would be pure phantom demand;
* treat the §5 finding as a reason to add an offsetting adder anywhere.

It would be re-opened legitimately only by **new evidence that the net position
changed regime** — e.g. MISO implementing the virtual spread product its IMM
recommends (2025 SOM §IV.B), which would move the matched 1,694 MW/h out of the
net book and could make the net position mean something different. That is a
market-design change, not a re-analysis.
