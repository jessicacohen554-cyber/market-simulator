# FINDING — miso-145: MISO's real submitted-offer corpus is INTAKEN, and the pre-registered LEVEL-markup hypothesis is REFUTED — the model's summer-afternoon deficit is not an offer-LEVEL object

**Session:** miso-145, 2026-08-09, branch `claude/miso-offer-conduct-phase-0-0ue55p`,
off `origin/main` at `c452919`. §5.4 queue **item 6** (owner-opened 2026-08-08).

**NO LP SOLVED. NO KEEPER MOVED. NO MECHANISM ARMED. NO RUN REGISTERED. NO
`ScenarioConfig` FIELD ADDED. NO PARAMETER DERIVED. NO CELL VERDICT MINTED**
(no mechanism was armed, refused, or proposed for arming — the miso-143/144
precedent). MISO keeper unchanged at **`2026-08-05-miso-132b-cc-committed`**.

**Pre-registration**
`results/calibration/PREREG-miso145-summer-offer-conduct-2026-08-09.md`, pushed
at **`083222bf`** *before any adjudicating statistic*, with a two-sided prior,
six numerically falsifiable predictions, pre-committed branches, kill-gate bars
and all seven look-alike traps with their counter-measurements.

*(§2–§6 follow the gates in PREREG order; §7 is the verdict, §8 the successor.)*

---

## 1. Headline

**The pre-registered hypothesis is REFUTED and the pre-committed branch that
fires is `BRANCH-CONDUCT-ABSENT`.** MISO's real summer-afternoon offers do **not**
sit above the model's at matched position in the stack. On every measured
variant — both markets, all three declaration universes, all three years — the
LEVEL term is **negative**: at the model's own clearing percentile the real book
offers **$8 to $15/MWh CHEAPER** than the model does (2025 JJA h12–17: RT
**−$14.376**, DA **−$8.298**, against a pre-registered bar of **≥ +$18**). No
offer-level lever is licensed, and none is proposed.

**Reported against interest, before anything is claimed from it: that LEVEL
statistic is universe-contaminated, and the contamination points the way the
refutation went.** The corpus carries MISO's wind and solar as offer rows —
**measured, not assumed: 19.9 GW (RT) / 17.7 GW (DA) offered at or below
$0/MWh** in this very window — while the model's fleet carries none of them as
rows (they are LP decision variables; the keeper dispatches **16.3 GW** of
wind + solar in the same hours), and *does* carry 17.2 GW of import tranches
the corpus has no analogue for. The pre-registered declaration
screen was supposed to remove the intermittent population and **it does not**:
it removes 0.5 of 107 GW. So the negative LEVEL sign is at least partly the
renewables' weight in the corpus's body. The pre-committed rule fires on the
number as measured and the verdict stands — but it is recorded as
**rule-fired, not independently established**, and this session claims no clean
measurement of the level question. *(This is the TRAP-3 failure mode PREREG §5
named as most likely, caught by the guard rather than by hindsight.)*

**What DID survive the universe critique is a different object, and it is
large.** Two readings are universe-free — both sides are "MW priced in a stated
band", so a population that sits far below the band cannot move them:

* **In 2025 JJA h12–17 the model carries 5.698 GW of capability priced between
  its own clearing price ($44.245) and the hour's actual RT price. MISO's real
  book carries essentially none there: −0.056 GW (RT), −0.234 GW (DA).**
* **Immediately above its own clearing the real curve rises at $73.46/MWh per
  GW (RT) and $17.90 (DA). The model's rises at $1.496 (`lo`) / $1.470 (`hi`)** —
  a factor of **49×** and **12×** on the two instruments, and the same sign and
  order of magnitude in all three years and both windows.

So the model's stack is not mis-*levelled*; it is mis-*shaped*. MISO's real book
is near-vertical just above where it clears, and the model's is a gentle ramp
through the very price band the real market does not offer into. **The model
clears at the 79.1st percentile of its own capability where MISO clears at the
93.8th (RT) / 87.8th (DA) — it holds 22.5 GW above its margin where the real
book holds 6.6 / 16.1 GW.** That object — call it *the missing offer wall* — is
named here, is NOT pre-registered, is labelled post-hoc throughout, and is filed
as the successor charter (§8), not as a result of this lane's registered test.

---

## 2. G-A — the intake. The corpus is landed, and its limits are measured, not assumed

MISO's masked submitted-offer corpus is now a first-class on-disk datatype:

* **Raw** `data/raw/miso-energy-offers/<market>/<YYYYMMDD>_<market>_co.zip`
  (verbatim source bytes, immutable, gitignored; tracked README +
  `manifest.json` with per-file sha256/size), fetched by
  `scripts/data/fetch_miso_energy_offers.py`.
* **Clean** `data/clean/energy-offers/MISO/<DA|RT>/energy-offers_<year>.parquet`
  through the frozen `clean_io.write_clean` seam, curated by
  `scripts/data/curate_miso_energy_offers.py`.
* **Schema** `energy-offers` bumped **v1 → v2**: generalised from PJM-only to
  ISO-generic, `market` (DA/RT) joins the key, every MISO column added
  **nullable** so PJM's writer stays valid (it gains only the `market="RT"`
  constant). Every path resolves through `config/paths.py`
  (`MISO_ENERGY_OFFERS_DIR`).

**Rule 13 `[R-MEASURED]` is enforced by the curator, not by convention.** The
source carries dispatch AWARDS — RT `Cleared MW1`–`Cleared MW12`, DA `MW`, and
`Target MW Reduction`. They are the answer class. They are dropped in
`_transform_day`, their absence asserted, and they have **no column in the
schema**, so no downstream reader can consume them even by accident.

**Landed span (rule 22 audit line):** June 1 – August 31 of **2023, 2024 and
2025**, both markets — 276 days × 2 = **552 files**. Every fetched day is inside
2023–2025; the fetcher refuses any other year without `--allow-out-of-train`.

### 2.1 The pre-registered coverage predictions, scored as written

| id | prediction | measured | verdict |
|---|---|---|---|
| **P-A1** | ≥ 99 % of 552 files retrievable, parseable single-member zips | **552 / 552 = 100 %**, 429.6 MB, 0 files with ≠ 1 member | **PASS** |
| **P-A2** | 900–1,600 units/day; 20k–40k rows/RT day; 24 h present; h12–17 populated | 24 h in **every** sampled day; h12–17 populated in **every** day; DA 1,319–1,407 units / 31.7–33.8 k rows. **RT 852–1,115 units / 18.8–23.9 k rows — BELOW the 900 lower bound on 4 of 9 sampled RT days** | **FAIL (lower bound), reported at full magnitude; bar not moved** |
| **P-A3** | zero columns matching `fuel\|type\|technolog` | **zero, across all 552 files** — the miso-136 absence re-verified on the full landed span, not a sample | **PASS** |
| **P-A4** | masked `Unit Code` ≥ 90 % Jun-1 → Aug-31 overlap, all years | DA **1.0000 / 0.9985 / 0.9986**; **RT 0.8154 / 0.9301 / 0.8664** | **FAIL on RT** (2 of 3 years). The pre-registered *falsification* threshold (< 0.80, "longitudinal statistics unsupported") **did not fire**; and this session computes no per-unit longitudinal statistic in any case |
| **P-A5** | cumulative MW and price breakpoints monotone on ≥ 99 % of rows | **1.00000 / 1.00000** on both, minimum across all sampled days | **PASS** |

**The P-A2 / P-A4 misses are one fact, and it is a real one about the
instrument: the RT offer book is a genuine SUBSET of the DA book.** DA carries
essentially the whole registered fleet (1,319–1,407 units, ≥ 99.8 % persistent
across a summer); RT carries 852–1,115 and its membership churns day to day,
because not every unit re-submits an RT offer. That is not a fetch defect and
not a curation defect — it is what the RT book is. It is disclosed here, carried
into every RT reading below, and is the reason the DA book is reported alongside
RT as a separate instrument and **never averaged with it** (TRAP 4).

**Two further source facts, both reported rather than smoothed away.**

* **Exact duplicate rows exist in 2023 and only 2023.** A handful of units
  (8 on 2023-07-15 RT) are published two or three times for the same unit-hour
  with byte-identical content. The curator drops them on the schema key and logs
  the count (121,680 DA-2023 and 49,620 RT-2023 of ~10.9 M / 6.6 M rows;
  **zero** in 2024 and 2025). Keeping them would multiply those units' capability
  two- and three-fold in every aggregate.
* **`Region` carries a blank (`" "`) level** alongside North / Central / South.
  No zone crosswalk is asserted from `Region` anywhere in this session.

### 2.2 The crosswalk question, answered by citing the measurement that already exists

The charter asked for "a documented crosswalk from masked offer units to model
classes … whatever the data actually supports; document the mapping's limits
rather than overclaiming grain."

**The data supports no class crosswalk, and that is a measured result, not an
assumption.** P-A3 re-confirms there is no fuel/technology attribute anywhere in
552 files. miso-138 then built the offer-side classifier from declarations and
the pre-committed verdict was **REFUTED**: CC carries `|S_cap| > 0.50` at both
EIA-860 grains in 2024 and 2025 (generator grain +1.240 / +1.335 / +1.283), and
COAL recall was 0.382 *with the labels in hand*. Coal and CC — the one split
this lane would need — are the split this feature family cannot make.
Re-attempting it is DO-NOT-REDO (rule 28(a)).

**So PREREG §2(a) declared the limit before any number was seen, and this
session honours it: every statistic below is at FLEET grain.** What is claimed
rests on miso-138's *passing* leg — the corpus IS the MISO fleet, reconciling to
EIA-860 MISO at fleet grain at **+12.9 / +9.0 / +6.0 %** on MW.

The only screens used are **declaration-based and named as such**, never fuel
labels: `all` (every offer row), `conventional` (no curtailment-offer price, no
storage SOC bounds — which removes dispatchable-intermittent and storage rows,
and, being a declaration screen, may also remove some demand response), and
`available` (`Unit Available Flag` set). Every headline is reported on all
three.

---

## 3. G-F1 — the footing gate, and it passes exactly

Before any verdict, the instrument reproduces miso-142/143's six committed
window deficits on the single C3a weight (TRAP 7), from the keeper's own
committed P1 sidecar and the miso-137 `*_lw` comparator reused not re-derived:

| year · window | committed | this session |
|---|---|---|
| 2023 · W1 Jun+Jul h8–20 | −4.750 | **−4.750** |
| 2023 · JJA h12–17 | −8.333 | **−8.333** |
| 2024 · W1 | −10.676 | **−10.676** |
| 2024 · JJA h12–17 | −10.671 | **−10.671** |
| 2025 · W1 | −30.999 | **−30.999** |
| 2025 · JJA h12–17 | −30.435 | **−30.435** |

**All six to the last committed digit. G-F1 PASSES**, and the model-side ladder
readings (`+1/+2/+5 GW` slopes) reproduce miso-143's committed values as well.

---

## 4. G-F4 — the tail separation (TRAP 5), fixed before the verdict

This lane's object is **ordinary** hours, not the exhausted C3c spike tail. The
window's own composition, by measured RT actual price:

| year · window | n hours | ≤ $100 | $100–200 | > $200 | deficit, all hours | deficit, ordinary (≤ $200) |
|---|---|---|---|---|---|---|
| 2023 · JJA h12–17 | 552 | 529 | 18 | 5 | −8.333 | **−5.169** |
| 2024 · JJA h12–17 | 552 | 515 | 29 | 8 | −10.671 | **−6.011** |
| 2025 · JJA h12–17 | 552 | 485 | 48 | **19** | −30.435 | **−12.874** |
| 2023 · W1 | 793 | 767 | 22 | 4 | −4.750 | −3.341 |
| 2024 · W1 | 793 | 760 | 24 | 9 | −10.676 | −5.848 |
| 2025 · W1 | 793 | 698 | 62 | 33 | −30.999 | −12.261 |

**The separation is material and it cuts against a convenient story.** In 2025
JJA h12–17, 19 of 552 hours (3.4 %) carry $17.6 of the $30.4 window deficit;
the 533 ordinary hours carry **−$12.874**. So the ordinary-hours object is real
and large — a −17 % miss on 533 hours at a $73 actual mean — but it is **not**
the whole −$30.4 headline, and no reading below quotes the headline as if it
were an ordinary-hours number. Every G-B statistic is reported on both the full
window and the ordinary subset.

---

## 5. G-F2 — the universe gate passes its number, and the pass is not meaningful

The gate asked that the corpus's offered capability and the model's available
capability reconcile at fleet grain to within ±25 %. **It passes**: 2025 JJA
h12–17, model **107.519 GW** vs corpus **107.007 GW** (RT, −0.5 %) and
**131.969 GW** (DA, +22.7 %).

**And the RT pass is a coincidence of two large offsetting differences, which
is worth more than the gate.** The model's fleet carries **17.2 GW of import
tranches** (`runner` log: 32 import tranches / 17,200 MW) that have no analogue
in an offer book of MISO-internal resources; the corpus carries MISO's **wind
and solar**, which the model does not represent as generator rows at all (they
are LP decision variables with MC = 0). **Both sides of that cancellation are
measured, not inferred** (`_miso145_cheap_mass.json`, 2025 JJA h12–17, unweighted
window means): the corpus offers **19.945 GW (RT) / 17.654 GW (DA) at or below
$0/MWh** and 22.1 / 21.7 GW at or below $5, while the keeper's own sidecar
dispatches **7.007 GW wind + 9.279 GW solar = 16.286 GW** in the same hours with
no fleet row behind either. The two absences are of the same size and they
cancel. The DA figure — +22.7 %, i.e. ≈ +24 GW on a fleet whose non-import
capability is ≈ 90 GW — is the honest read of that composition difference.

**The pre-registered declaration screen does not fix it.** `conventional` (no
curtailment-offer price, no storage SOC bounds) removes **0.459 GW of 107.007**
(RT 2025) and **0.512 GW of 131.969** (DA); `available` removes a further
1.2 GW (RT) / 13.1 GW (DA). So the screens do **not** identify MISO's
dispatchable-intermittent population, and no renewables exclusion was achieved
on either instrument. Stated plainly rather than worked around: **any statistic
whose value depends on where the *body* of the curve sits is contaminated on
this construction, and only the band-restricted statistics of §6.2 are clean.**

---

## 6. G-B — the conduct measurement

Every number below is load-weighted on C3a's own model-demand weight (ONE
weight, TRAP 7), positions are located by PRICE on each side's own curve, and
the model side is `_miso143_stack`'s reconstruction reused verbatim at both
offer brackets. RT and DA are separate instruments and are never averaged
(TRAP 4).

### 6.1 The contaminated leg — the LEVEL / POSITION decomposition (P-B2)

The PREREG §4 identity, evaluated at the **model's own** clearing percentile
applied to the real curve (an early implementation read that percentile off the
real curve instead, which makes the level term identically zero by construction;
the bug was found and fixed before any verdict was taken, and the circular
version appears in no result):

| year · JJA h12–17 | deficit | instrument | LEVEL | POSITION | LEVEL as share of deficit |
|---|---|---|---|---|---|
| 2023 | −8.333 | RT (all) | **−11.823** | +20.156 | −1.42 |
| 2023 | −8.333 | DA (all) | **−7.329** | +15.662 | −0.88 |
| 2024 | −10.671 | RT (all) | **−8.072** | +18.743 | −0.76 |
| 2024 | −10.671 | DA (all) | **−4.996** | +15.667 | −0.47 |
| 2025 | −30.435 | RT (all) | **−14.376** | +44.811 | −0.47 |
| 2025 | −30.435 | DA (all) | **−8.298** | +38.733 | −0.27 |

Every variant is negative; the `conventional` and `available` universes move it
by at most $2 (2025 RT: −14.376 / −14.621 / −14.685), and the ordinary-hours
(≤ $200) restatement moves it by less than $1.3 anywhere. **P-B2's bar was
≥ +$18 and the measured value is negative on every instrument, universe, year
and hour-subset. `BRANCH-CONDUCT-ABSENT` fires as pre-committed.**

**And this leg is the contaminated one (§5).** The real book's body carries
~25–35 GW of near-zero renewable offers the model's stack does not carry, which
depresses the real curve's price at any fixed percentile — biasing LEVEL
**negative**, i.e. *toward* the refutation. The refutation is therefore recorded
as **fired by the pre-committed rule on the number as measured**, not as an
independently established clean result. Either way, **no offer-level lever is
licensed by this session and none is proposed** — the direction that would have
licensed one was not observed on any variant.

**P-B4 (the 2025 signature) is FALSIFIED as written.** The prediction was a
monotone LEVEL rise of ≥ +$5 from 2023 to 2025; the measured LEVEL is
−11.823 / −8.072 / −14.376 (RT), non-monotone and of the wrong sign. It carries
the same contamination and no weight is placed on it.

**P-B1 was NOT SCORED, and the reason is the gate above.** As written it asked
for the corpus curve to be cleared at "the measured MISO load" — which requires
exactly the demand-universe alignment §5 shows cannot be made (the corpus has no
imports; the model's fleet has no renewables). PREREG §5 named that alignment as
the most likely failure mode, and the probe was built to avoid it rather than to
paper over it. The price-identified analogue is reported instead and is
recorded as such, not as P-B1: the actual price lies **interior** to the real
book in every hour of every window (clearing percentile 0.92–0.94 RT / 0.87–0.88
DA, unreached fraction zero), i.e. the real offer book does contain and price
the measured outcome without extrapolation. **P-B5 was not scored either**: it
was a supporting characterisation for the `BRANCH-CONDUCT-OWNED` path, which did
not fire, and running it would only decorate a settled verdict.

### 6.2 The clean leg — band-restricted readings (P-B3, P-B3b)

These two compare "MW priced inside a stated price band" and "the price
increment above a price-identified point" on both sides. A population sitting
far below the band (renewables, must-run self-schedules) cannot move either, so
§5's contamination does not reach them.

**P-B3b — capability between the model's clearing price and the hour's actual
price. PASSES; the pre-registered bar was ≤ 6 GW on the real side.**

| year · window | model (`lo` / `hi`) | real RT | real DA |
|---|---|---|---|
| 2023 JJA h12–17 | 4.338 / 4.493 GW | **−0.212** | −0.316 |
| 2024 JJA h12–17 | 5.798 / 5.958 | **−0.886** | −1.138 |
| 2025 JJA h12–17 | **5.698 / 6.038** | **−0.056** | −0.234 |
| 2023 W1 | 3.517 / 3.654 | −2.046 | −3.748 |
| 2024 W1 | 5.505 / 5.593 | −2.089 | −2.938 |
| 2025 W1 | 6.113 / 6.416 | −0.267 | −0.335 |

(The small negatives are hours in which the actual price fell *below* the
model's; they are carried, not clipped.)

**P-B3 — the ladder slope immediately above each curve's own clearing, on
miso-143's construction. PASSES by 12× to 49×; the bar was ≥ 3.0 $/MWh/GW.**

| year · JJA h12–17 | model `lo` (+1/+2/+5 GW) | real RT (+1 GW) | real DA (+1 GW) |
|---|---|---|---|
| 2023 | 1.767 / 1.684 / 2.104 | **51.70** | **10.44** |
| 2024 | 1.246 / 1.005 / 1.288 | **56.06** | **14.29** |
| 2025 | **1.496 / 1.895 / 2.890** | **73.46** | **17.90** |

Both hold on the `conventional` and `available` universes (2025 RT: 55.94 /
56.25) and in the W1 window (2025: real RT 73.65, DA 19.26, model 1.582).

### 6.3 The percentile grid — what the two curves actually look like

Load-weighted offer price at percentiles of each side's **own** capability,
2025 JJA h12–17 (contaminated in level per §5; reported for shape):

| percentile | model `lo` | real RT | real DA |
|---|---|---|---|
| p50 | 27.76 | 18.63 | 21.23 |
| p70 | 37.12 | 24.28 | 28.17 |
| p80 | 43.35 | 28.78 | 32.85 |
| p85 | 47.11 | 31.39 | 37.16 |
| p90 | 55.29 | 35.14 | 47.56 |
| p95 | 87.46 | 46.96 | 98.03 |
| p98 | 211.34 | 75.30 | 213.79 |
| **clears at** | **p79.11 → $44.245** | **p93.80 → $74.68** | **p87.80 → $74.68** |

The DA book and the model reach almost the same place at the top (p95 98.03 vs
87.46; p98 213.79 vs 211.34) — **the difference is where each one clears.** The
model stops 16 percentile points short of its own wall and prices in the ramp
below it; MISO clears 8 points higher and prices on the wall. In GW: capability
above the margin is **22.46** (model) vs **6.63** (RT) / **16.10** (DA).

### 6.4 Reproduce-before-extend

The model-side walk was computed on **both** constructions so the comparison to
miso-143 is like-for-like:

* miso-143's construction (target = the **window-mean** actual): **11.041 /
  17.698 / 16.117 GW** for 2023/2024/2025 JJA h12–17, against its committed
  **11.062 / 18.444 / 16.142** — reproduced to **0.021 / 0.746 / 0.025 GW**. The
  2024 residual is the construction difference (this probe counts capability in
  a price band; miso-143 walks the ladder cumulatively, so block ties land
  differently), not a defect, and it is the only year where it exceeds 0.03 GW.
* the hour-matched construction used here (target = **that hour's** actual):
  **4.338 / 5.798 / 5.698 GW**. It is the smaller number because the window-mean
  actual is pulled up by the skewed tail; it is the one quoted above because the
  real-side reading uses the same hour-matched target on both sides.

---

## 7. Verdicts, gates and traps, closed out

| item | verdict |
|---|---|
| **G-F1** footing (HARD STOP) | **PASS** — all six committed deficits to the last digit (§3) |
| **G-F2** universe | **PASS on its number (−0.5 % RT / +22.7 % DA), reported as not meaningful** (§5) |
| **G-F3** instrument | **HONOURED** — RT primary, DA separate, never averaged |
| **G-F4** tail separation | **DONE** (§4); every headline also given on the ordinary (≤ $200) subset |
| **P-A1 / P-A3 / P-A5** | **PASS** |
| **P-A2 / P-A4** | **FAIL on the RT lower bounds, bars not moved** (§2.1) |
| **P-B1** | **NOT SCORED** — its construction requires the alignment §5 shows cannot be made |
| **P-B2** | **FALSIFIED**, negative on every variant (bar ≥ +$18) |
| **P-B3** | **PASS**, 12×–49× the bar |
| **P-B3b** | **PASS**, real side ≈ 0 GW against a ≤ 6 GW bar |
| **P-B4** | **FALSIFIED** as written |
| **P-B5** | **NOT SCORED** — supporting statistic for a branch that did not fire |
| **branch** | **`BRANCH-CONDUCT-ABSENT`**, pre-committed, fired by P-B2 |

**Traps.** **T1** (re-sweeping `gas_offer_margin`) — did not fire; nothing was
re-identified. Its counter-measurement is reported: miso-143 B-1 measured that
mechanism's price-relevant haircut at **$0.33** with a $0.18 swing, a LEVEL
device acting near the margin; the object measured here at the margin is a
**$73/GW slope**, not a level — different in kind, not a re-run. **T2** (the
outcome overlay) — closed at the curation seam: the award columns have no
column in the schema (§2). **T3** (the universe) — **FIRED, and was caught by
the guard**: §5 is the whole subject of the level leg's disqualification.
**T4** — honoured; DA and RT never averaged, no as-bid/SRMC subtraction is
performed anywhere (the LEVEL term is price-vs-price). **T5** — §4; the verdict
holds on the ordinary subset. **T6** — no parameter was sized to anything; no
search over C3a was run. **T7** — G-F1.

**Kill gates:** not reached. No solve was run, no mechanism armed, no
`ScenarioConfig` field added, so C3b-2025's 0.009 of headroom, the 2023/2024
C3a PASSes, C1/C2, C8 and the spent C3c ledger are all untouched. The fail set
is unchanged at **{C3a}** and the keeper is unchanged.

**Rule-13 adjudication, recorded even though no arm follows.** Nothing measured
here is admissible as a same-year overlay, and none is proposed. The admissible
form for any successor remains what PREREG §9 fixed in advance: a conduct
parameter derived from **multi-year** offer history and conditioned on drivers
that exist in a forecast year (position in the stack / headroom, load
percentile, gas price), which would regenerate forward and respond to changed
conditions. Pinning the measured curve is forbidden and stays forbidden.

---

## 8. The successor, named and NOT opened

**The object:** *the missing offer wall* — the model holds **22.5 GW** of
capability above its clearing where MISO's book holds **6.6 GW** (RT) /
**16.1 GW** (DA), and it prices **5.70 GW** into the $44–$75 band where the real
book prices **~0.1 GW**. It is a **curve-shape** object, distinct from every
family already closed: not quantity (miso-142 — nothing is displaced), not merit
order (miso-143 — no re-ranking is proposed), not dispatch (miso-144 — the LP
still clears its own stack optimally), and not a floor (miso-144 exonerated
them).

**The named successor is a MISO `measured_offer_surface`, position-conditioned,
built from the corpus this session landed** — and it carries two hard
constraints that must be settled *before* it is chartered, which is why it is
named and not opened (rules 19/24, an owner decision):

1. **It cannot be class-conditioned.** Every other ISO's offer surface is
   conditioned on class; MISO's cannot be, because miso-138 refuted the
   offer-side class bridge and P-A3 re-confirms there is no fuel attribute in
   552 files. A position-conditioned surface has to map a *fleet-level* shape
   onto *per-unit* offers, and how to do that without inventing a class is an
   open design question, not a detail.
2. **It must reconcile with `gas_offer_margin` (rule 19 `[R-ONE-MECH]`)**, which
   is armed on this keeper and acts on the same offer path — replace or subsume,
   never stack.

**A second, cheaper prerequisite is now visible and should precede it:** the
level question is unanswerable until the corpus's intermittent population can be
identified, because the declaration screen removes 0.5 of 107 GW (§5). MISO's
`Curtailment Offer Price` does not mark the DIR fleet in this corpus. Until a
screen exists, no level statistic from this corpus should be quoted — by this
lane or any other.

**Artifacts.** `results/calibration/_miso145_coverage.json`,
`results/calibration/_miso145_offer_conduct.json`,
`results/calibration/_miso145_cheap_mass.json`; probes
`scripts/probes/_miso145_coverage.py`, `scripts/probes/_miso145_offer_conduct.py`;
intake `scripts/data/fetch_miso_energy_offers.py`,
`scripts/data/curate_miso_energy_offers.py`,
`data/dictionary/schema/energy-offers.schema.yaml` (v2),
`data/raw/miso-energy-offers/README.md`.
