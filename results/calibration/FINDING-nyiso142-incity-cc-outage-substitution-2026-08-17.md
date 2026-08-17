# FINDING nyiso-142 — the 2025 downstate ST_GAS rise is an **in-city CC outage** substitution, and it is **zone-local to New York City**

**Session nyiso-142, 2026-08-17.** Takes up job 3 of the prompt — the successor
object nyiso-140 §7 named and nyiso-141 left open: after the Astoria measurement
artifact is removed, ≈ −2.4 TWh of genuine 2025 downstate ST_GAS under-production
remains, 2023 carries +2.26 TWh of over-production, and the model's CC/ST
merit-order boundary does not move the way the market's did.

**IDENTIFICATION ONLY — no mechanism was written, no `ScenarioConfig` field was
added, and no lever is proposed or pre-registered.** §§1–3 are measured entirely
from committed artifacts and model INPUTS: the per-plant benchmark sidecars
(`frontend/data/backcast/bench/NYISO/<year>.json.gz`), the committed CAMPD
unit-outage extract (`data/raw/campd-unit-outages-NYISO.csv`) and the LP's own
availability multipliers. §4 additionally reads the **control** bundle of this
session's Astoria A/B — a solve spent for job 1, not for this job, and the
incumbent keeper's own recipe on its own uncorrected basis. **No price or volume
residual was used to *find* the object at any step**; the residual appears only
in §5, to state honestly what is and is not accounted for.

Reproducible: `.venv/bin/python scripts/probes/_nyiso142_incity_cc_substitution.py`.

---

## 1. THE SUBSTITUTION IS NOT ISO-WIDE — IT IS ZONE J

nyiso-141 §1 established the class-level shape: 2023 → 2025 reality added
**+7.30 TWh of ST_GAS** while CC_REGULAR was flat (**+0.12**); the model added
**+1.30 ST_GAS** and **+8.97 CC**. That framing invites a merit-order reading —
*the model's CC is too cheap relative to ST*. **The zonal decomposition refutes
that reading.** Per-plant benchmark `e_ann` (the metered basis the scorer uses),
summed to zone (TWh):

| zone | CC_REGULAR 2023 | 2024 | 2025 | **Δ25−23** | ST_GAS 2023 | 2024 | 2025 | **Δ25−23** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **NYC** | 9.393 | 9.735 | **8.435** | **−0.959** | 2.574 | 2.778 | **5.727** | **+3.152** |
| Capital_Hudson | 15.902 | 16.878 | 15.973 | +0.071 | 1.148 | 1.542 | 2.636 | +1.488 |
| Long_Island | 3.384 | 2.865 | 3.423 | +0.039 | 3.984 | 5.030 | 5.340 | +1.357 |
| Upstate_West | 0.450 | 0.562 | 0.643 | +0.193 | 0.635 | 0.679 | 0.684 | +0.049 |

**Correcting for nyiso-141** (the 2025 NYC figure still carries the Astoria
double-count; 2.672 → 1.359 TWh) the NYC ST_GAS entry becomes **≈4.414**, i.e.
**Δ25−23 ≈ +1.84 TWh** — still the largest single move in the table, and still
paired with the **only zone where CC output fell.**

That pairing is the finding. **A cheaper CC does not step aside for a dearer
steam unit on economics.** In Zone J, combined cycle gave way to steam — which
is the signature of an availability constraint, not of a merit order.

## 2. THE CC SIDE — the three in-city combined cycles all lost availability in 2025

Booked outage windows from the committed detector extract, summed over units
per plant-year (unit-days, **not** capacity-weighted — the delta is the signal):

| plant | zone | 2023 | 2024 | **2025** | **Δ25−23** |
|---|---|---:|---:|---:|---:|
| **Astoria Energy** (55375) | NYC | 88.2 | 91.4 | **325.0** | **+236.8** |
| **Ravenswood Generating Station** (2500) | NYC | 385.2 | 428.9 | **619.2** | **+234.0** |
| **Poletti 500 MW CC** (56196, "Zeltmann") | NYC | 76.2 | 70.0 | **141.3** | **+65.1** |
| Cricket Valley Energy Center (57185) | Capital_Hudson | 189.5 | 450.5 | 397.5 | +208.0 |
| Bethlehem Energy Center (2539) | Capital_Hudson | 57.0 | 91.4 | 80.3 | +23.3 |

**All three in-city CCs move the same way at once: +536 unit-outage-days in
2025 against 2023.** The pattern at Astoria Energy is not a longer outage but a
*fragmented* one — CT3 goes from 2 windows / 34.1 days in 2023 to **13 windows /
129.4 days** in 2025, CT4 from 2 / 18.1 to **10 / 102.8**. Its metered output
falls in step: CAMPD gross **8.29 → 8.42 → 6.33 TWh** (−1.96 TWh, −24 %).
Poletti falls 3.50 → 3.78 → 3.09.

So the market's 2025 sequence reads, end to end and without a residual anywhere
in it: **in-city CC availability collapsed → in-city load still had to be served
inside the pocket → the only in-city thermal left is steam (Astoria GT, Arthur
Kill, Ravenswood ST) → downstate ST_GAS rose.** Note what the market did *not*
do: Capital_Hudson CC is flat at **+0.07 TWh**, so the loss was **not** backfilled
from outside the city. That is exactly what a binding in-city requirement looks
like.

## 3. THE PLUMBING IS INTACT — the model SEES the constraint and still does not use the steam

The obvious first reading is a plumbing failure: the outages never reach the LP.
**Measured, and REFUTED.** `outages.unit_outage_derate_factors(year, iso="NYISO")`
is the per-bin availability multiplier the LP is built from; read directly (an
input inspection, no LP constructed):

| model bin | 2023 | 2024 | **2025** | equiv. full-outage days 2023 → 2025 |
|---|---:|---:|---:|---|
| **(55375, CC_REGULAR)** Astoria Energy | 0.868 | 0.854 | **0.552** | 48.3 → **163.7** |
| **(56196, CC_REGULAR)** Poletti | 0.883 | 0.897 | **0.798** | 42.6 → **73.6** |
| **(2500, ST_GAS)** Ravenswood | 0.772 | 0.465 | **0.297** | 83.4 → **256.7** |

Mean annual availability, all 8,760 hours. Astoria Energy's in-city CC bin loses
**a third of its availability** between 2023 and 2025 in the model's own input.
So the model is not blind to the §2 event — it sees it, and still grows
CC_REGULAR by **+4.85 TWh** while adding only +1.30 of ST_GAS.

### 3.1 A second hypothesis of my own, tested and also refuted

Ravenswood (2500) routes through `outages._FLEET_GROUP_OVERRIDE = {2500: "ST_GAS"}`
— a *deliberate, documented* override, because CAMPD tags every Ravenswood unit
`CC_REGULAR` while the NYISO fleet carries the plant as a single 1,724.8 MW
ST_GAS bin. That raised an obvious suspicion: the override may push the plant's
**CC and CT** outage rows onto the **steam** bin, over-derating the very in-city
steam the model under-produces. **Measured, and it is not what is happening.**
Splitting the plant's rows into its steam units (10 / 20 / 30) and everything
else (UCC001, CT0001, CT0010, CT0011):

| year | ST_GAS bin as modelled | steam units only | difference (equiv. full-outage days) |
|---|---:|---:|---:|
| 2023 | 0.7715 | 0.7860 | 5.3 |
| 2024 | 0.4653 | 0.4786 | 4.9 |
| 2025 | 0.2968 | 0.3092 | **4.5 of 256.7** |

The non-steam contamination is **under 2 %** of the derate. Ravenswood's steam
bin is held at 29.7 % availability in 2025 by **its own steam units' booked
outages**, and the override is not the cause. Recorded because it was my own
hypothesis and it failed: the routing is sound.

### 3.2 What survives — and it is not an availability story

Note the arithmetic that closes off the availability reading entirely: at 0.297
mean availability Ravenswood's steam bin still offers an energy ceiling of
**≈4.49 TWh**, against an actual 2025 output of **1.070 TWh**. The in-city steam
the market used was **available in the model and was not dispatched.** So the
surviving readings are both economic/structural, not physical:

* **(b) A pocket-representation failure** — the model replaces the lost in-city
  CC from **outside Zone J**, in hours the real market could not.
* **(d) In-city offer ordering** — within Zone J, the model's steam is priced
  above whatever it actually dispatches instead, so the pocket clears without
  it.

**Neither may be reached for casually.** (b)'s natural lever family is already
adjudicated: nyiso-101 REFUSED the G-J locality limit ex-ante for want of a
representable boundary (Capital_Hudson straddles the locality; two of its four
real boundary legs are not LP quantities), and nyiso-130 established that Zone-K
reliability is already carried by two proxies that trade off against each other
under rule 19 `[R-ONE-MECH]`. Under rule 28 those cells do not reopen without new
evidence, and **§2–§3 are new evidence about the CC and availability sides, not
about the boundary.**

The discriminating measurement between (b) and (d) is **zonal**: how much of
Zone J load is served by in-city generation versus net flow, hour by hour, in
2023 against 2025, and whether the NYC import boundary binds. **That measurement
turns out to be available without any further solve** — the
`hourly/network_<year>.parquet` and `hourly/unit_hourly_<year>.parquet` sidecars
this session's A/B writes carry per-link hourly `mw`, `dual`, `limit_up` and
`limit_dn` and per-unit generation by zone and class. **§4 takes it, and it
refutes (b) as well.**

## 4. THE ZONE-J MEASUREMENT — the transfer-bound reading fails too, and what survives is a COMMITMENT question

Read from the nyiso-142 **control** bundle's own committed sidecars
(`hourly/unit_hourly_*`, `network_*`, `system_*` — the control is the keeper's
recipe on the keeper's own uncorrected basis, so this describes the incumbent):

| year | NYC demand | in-city gen | **in-city ST_GAS** | in-city CC_REG | from `Lower_Hudson>NYC` | hours that link is AT its bound |
|---|---:|---:|---:|---:|---:|---:|
| 2023 | 48.284 | 30.545 | **7.455** | 15.325 | 12.212 | **29** |
| 2024 | 49.576 | 27.641 | **5.293** | 15.326 | 17.158 | **237** |
| 2025 | 50.106 | 28.865 | **6.129** | 13.595 | 15.104 | **138** |

TWh, P1. The model's account of 2023 → 2025 is now fully legible: NYC demand
**+1.82**, in-city generation **−1.68**, in-city CC **−1.73** (it *does* respond
to the §2 outages), and the gap closed by **+2.89 TWh of extra Lower-Hudson
import**. In-city ST_GAS **FALLS 1.33 TWh** over exactly the span in which the
market's rose ≈1.84. That is reading (b) in numbers.

### 4.1 But the boundary is NOT what permits it — the bound barely binds

`nyiso_nyc_lcr_tsl` **is armed on the keeper** and does exactly what it says:
it replaces the Dunwoodie-South link's 3,900 MW Gold-Book energy rating with
the published **2,875 MW** NYC-locality transmission-security limit inside the
HB14-21 design window, keeping 3,900 MW off-peak. Both limits appear in the
sidecar, and the binding hours are almost entirely in-window (29/29, 215/237,
138/138). So the mechanism is working.

**And it is not the constraint.** Mean flow into Zone J is 1,340-2,093 MW
against caps of 2,875 / 3,900 — the link sits well below its bound in the
overwhelming majority of hours, and binds in **0.3 % / 2.7 % / 1.6 %** of the
year. **The model does not import more because it is allowed to; it imports
more because nothing requires the in-city units to be on.** Tightening the
transfer bound is therefore the wrong instrument — and that is a measurement,
not a preference. (For completeness, the off-window flow does exceed the
published 2,875 MW in 102 / 642 / 265 hours, which is the windowed design's
deliberate choice and is separately justified in its own docstring; it is not
what is doing the work here.)

### 4.2 What survives, and where it already sits on the matrix

The surviving reading is **(d)**: within Zone J the model has **no in-city
commitment obligation**, so the pocket clears on economics alone and the dear
in-city steam never starts. The real market does not work that way — NYC's
in-city units run under local reliability commitments and a locality capacity
obligation, which is a **commitment** instrument, not a flow limit.

That object already has a name and an untested cell:
**`nyiso_incity_commitment_obligation`**, `None` on the keeper, matrix verdict
**`U`**, evidence *"nyiso-105 section A (named as the compliant replacement
path)"*. It is not adjudicated `R`/`I`/`G`, so rule 28's DO-NOT-REDO discipline
does not bar it — but **this finding does not arm it, does not pre-register it
and does not propose parameters.** Under rule 20 `[R-ONE-MECH]` the next
session's first duty is to enumerate what already commits in-city gas (the
`nyiso_gas_commitment_bridge`, the NYC reliability-floor limbs the keeper
disables via `reliability_floor_overrides`, and this cell) and reconcile rather
than stack — the exact failure mode nyiso-130 documented for Zone K.

## 5. WHAT THIS DOES AND DOES NOT EXPLAIN — stated against my own result

* It gives the **2025** under-production a named, measured, zone-local
  mechanism, and it explains why the class-level view mis-suggests a merit-order
  cause.
* It explains **nothing about 2023's +2.26 TWh over-production**, which is the
  opposite sign and remains completely open.
* It is **not** a quantification. This finding does not claim the +536
  unit-outage-days are worth ≈2.4 TWh, and it does not claim an in-city
  commitment obligation would recover them. It establishes WHERE the 2025 half
  of the residual lives (Zone J), WHAT the market did there (steam replaced
  outaged in-city CC), and — by eliminating the availability, routing and
  transfer-bound readings on measurement — WHICH KIND of object is left.
* **Three candidate readings were tested and refuted, two of them my own.** That
  is the substance here: an identification that survives its own attempts to
  kill it is worth more than a fourth untested hypothesis.
* The hydro over-drop nyiso-141 flagged (model −7.34 vs actual −3.93 TWh) is
  **untouched here** and remains a separate open item. NY hydro is overwhelmingly
  upstate, so on the evidence above it is unlikely to be the same object.

## 6. GOVERNANCE

No mechanism proposed, no cell verdict moved, no keeper touched, no year outside
2023–2025 read. Rule 25 `[R-ISO-SCOPE]`: NYISO only. Rule 28 `[R-MECH-MATRIX]`:
**no matrix cell verdict changes on this finding.** `nyiso_incity_commitment_obligation`
stays `U` — naming a cell as the place the evidence points is not testing it, and
this session neither armed it nor derived a parameter for it. The named successor
for nyiso-143 is that cell, entered the ordinary way: enumerate the existing
in-city commitment mechanisms first (rule 20 `[R-ONE-MECH]`), identify any
parameter from NYISO's own published local-reliability rules rather than from the
residual (rule 23 `[R-FROZEN-DERIVE]`), and pre-register before solving.
