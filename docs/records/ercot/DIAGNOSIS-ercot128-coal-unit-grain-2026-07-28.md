# DIAGNOSIS — ERCOT-128: unit-grain commitment for multi-unit coal plants IS expressible in pure LP — exactly, for 97.8 % of ERCOT coal capacity, with no detector and no integrality. The lane still fails, because the correctly-grained instrument is worth nothing on the gates and the one gate that demands a win (D-1 diurnal shape) is unreachable by the ORACLE

**Date** 2026-07-28 · **ISO** ERCOT · **Lane** ercot128-unit-grain ·
**Keeper under audit** `2026-07-26-ercot115-coal-marginal-hr` (bundle
`results/calibration/ercot115_coal_floor_only`) — **unchanged by this session** ·
**Chartered by** `DIAGNOSIS-ercot127` §5.3, which closed the coal dispatch-band
lane and routed the residual to a single architectural question ·
**Method** Phase 1 only — the keeper's committed payload and bench, EIA-860
generator registrations, the 60-Day DAM Gen Resource corpus and CAMPD
unit-level operation, through `scripts/probes/ercot128_coal_unit_grain.py`
(sections A–G), plus code traces of the floor, detector and
mechanism-attribution paths.
**No LP was built. No year was solved. No arm was registered. No
`ScenarioConfig` field, cache-key surface or solve path was touched. No keeper
file was touched.**

> **SUPERSEDED IN PART — read the PHASE 2 ADDENDUM at the end of this file.**
> The owner reversed the §8 recommend-and-STOP on rule 1 `[R-STRUCT]` (a
> structurally-correct measured mechanism may not be rejected because the
> residual didn't move, nor on a gate belonging to another mechanism's residual).
> Phase 2 WAS built, solved full-span and registered as
> `2026-07-28-ercot128-unit-grain-coal`. Everything in §§0-7 below stands as
> measured; §8's *recommendation* is superseded by §P5. The Phase 2 verdict is
> still "do not promote", but for an entirely different and better-evidenced
> reason: the arm passes every absolute gate and fails its own pre-registered
> STRUCTURAL claim (§P3), with a specified fix (§P4).

**Outcome of Phase 1: it does NOT license a mechanism** —
the seventh consecutive abstention on the coal residual, and the first one that
answers its charter's question in the AFFIRMATIVE and still refuses.

The charter asked whether multi-unit coal plants can carry unit-grain
commitment inside the pure-LP rule. **They can — the specific part that
matters.** Unit-grain commitment *state* is not expressible (§1); but the
minimum-load lower envelope, which is the only part ERCOT-127's measured
parameter ever needed, is expressible **exactly**, as a static plant-grain
`pmin` at the plant's *minimum online configuration*, for nine of ten coal
plants and 97.8 % of coal capacity, with **no detector, no integrality, and no
change to the tranche offer curve** (§1.3, §3). The instrument behind it is
registration-grade and independently corroborates ERCOT-127 §2 to within 0.03
(§3.2).

What refutes the lane is the size of the prize, measured ex ante (§4–§5). The
correctly-grained floor scores **19/21 G1 bands against the keeper's 19/21** —
a swap, not a gain — and the **ORACLE** (the floor applied to exactly the
capacity reality held online each hour, an upper bound no implementable rule
can beat) reaches only **20/21**. And gate **G3 — the one gate in the charter's
set that demands a win rather than do-no-harm — moves the WRONG WAY under every
variant including the oracle** (§5). That is structural, not numerical: the
keeper's coal is too FLAT overnight, and a lower bound applied uniformly across
hour-of-day can only flatten it further. §6 locates the flatness and routes the
successor. §8 is the recommendation.

---

## 0. What is inherited, re-verified rather than assumed

| claim | source, verified this session |
|---|---|
| keeper G1 19/21 on the fleet-aggregate basis, failing only `<$15` 2023 (−0.064) and 2025 (−0.069) | reproduced exactly — §4's `keeper` column is 6/7 + 7/7 + 6/7 |
| the plant-grain blanket floor at 0.3636 collapses G1 | reproduced: this session's `plant_0.364` column matches ERCOT-127 §3.1's own `floor_0.364` column to **±0.001 in every one of the 21 bands** |
| keeper C1 coal −1.07 / −0.22 / −1.88 TWh | reproduced to −1.067 / −0.213 / −1.886 |
| keeper forces ZERO coal energy; none of the four live floors touches coal | keeper `legitimacy_diagnostics.json` — D-2 carries no COAL row in any year |
| coal is CLLIG only; ten ERCOT coal plants | ERCOT-126 §0 filters reused verbatim |

**One correction to ERCOT-127 §3.1's published tally, on its own numbers.** That
table reports the blanket floor at **8/21**. Recomputing the same construction
gives **9/21**: the difference is a single knife-edge band, 2025 `$15–20`, where
the floor lands 0.779 against actual 0.730 (|Δ| = 0.049) rather than the
published 0.780 (|Δ| = 0.050) — a last-digit rounding straddling the 0.05
tolerance. Nothing turns on it: 8/21 and 9/21 are the same verdict against the
keeper's 19/21, and every other band agrees to ±0.001. Recorded so the two
lanes' tables reconcile.

**One correction to the charter's framing of the detector, with receipts.** The
charter (following ERCOT-127 §5.3) states that "the keeper's coal never reaches
zero in P0, so a run-pattern detector marks it committed every hour". On the
keeper's own payload the coal plant series *is* at zero in **12.1 / 12.9 /
16.8 %** of plant-hours. That does not rescue the detector — §2 shows why, and
the conclusion is unchanged — but the premise as written is not what the data
says, and the corrected version is the sharper argument.

## 1. Is unit-grain commitment expressible without integrality? (charter task a)

### 1.1 The design space, enumerated

A unit-grain commitment representation needs, for each unit `u` and hour `t`, a
state `x[u,t] ∈ {0,1}` and the coupled bound `x·MinLoad_u ≤ p[u,t] ≤ x·Cap_u`.
Four ways to get it, and only four:

| form | verdict |
|---|---|
| **integer** `x ∈ {0,1}` | **forbidden** — CLAUDE.md Stack: no MIP, HiGHS LP only |
| **continuous relaxation** `x ∈ [0,1]` | **VACUOUS.** Projecting out a continuous `x` from `x·MinLoad ≤ p ≤ x·Cap` gives `0 ≤ p ≤ Cap`. The min-load constraint *disappears entirely* — the relaxation deletes the very thing the mechanism exists to impose. This is not a weak representation; it is no representation. |
| **exogenous `x` from a P0/P1 run-pattern detector** | **self-satisfying** — §2, measured |
| **exogenous `x` from measured unit operation** | **rule 13 `[R-MEASURED]` forbidden** — pinning a measured *outcome*; no forward analogue |

So unit-grain commitment **state** is not available. That is the charter's
question answered in the negative — and it is the wrong question, which §1.3
shows.

### 1.2 What the parameter actually needs

ERCOT-127 §2's parameter is a **lower bound**. It never needed the upper leg of
the commitment bound, and it never needed hour-varying state. What it needed was
the correct *grain* for one number: the smallest load a plant can hold while
synchronised. That is not a commitment variable. It is a property of the plant's
unit inventory.

### 1.3 And the lower envelope IS exactly expressible — measured, not asserted

A plant with units `u` carrying `[MinLoad_u, Cap_u]` has the exact online
feasible set

```
F = ∪ over non-empty subsets S of units:  [ Σ_{u∈S} MinLoad_u , Σ_{u∈S} Cap_u ]
```

If that union is **connected**, it equals the single interval
`[min_u MinLoad_u, Σ_u Cap_u]` — and a plant-grain LP variable bounded by
exactly that interval represents the plant's unit-commitment dispatch range
**with no relaxation error at all**. Enumerating all 2^N − 1 configurations on
the EIA-860 registrations (probe §B):

| | result |
|---|---|
| plants whose feasible set is **connected** | **9 of 10** |
| **coal capacity exactly representable** by the interval | **97.76 %** |
| the one exception | **Major Oak** — units 152.5 / 152.5 MW at min-load 95 MW each, so `[95,153] ∪ [190,305]` leaves a gap 153–190 MW, **17.6 % of its range** (305 MW of 13.6 GW of coal) |

The reason it is connected almost everywhere is arithmetic, not luck: adjacent
configurations overlap whenever `MinLoad/Cap < 0.5`, and every ERCOT coal unit
except San Miguel (0.639) and Major Oak (0.625) sits below that line. **For
97.8 % of ERCOT coal capacity, unit-grain commitment's lower envelope costs the
LP nothing but a `pmin`.** Where it is not exact (Major Oak) the interval is a
strict *relaxation* — it admits levels no unit combination can deliver, which is
the safe direction (it never forbids something the real plant did, per rule 14
`[R-ACCURATE]`), and it is on the record here rather than assumed away.

## 2. The detector, measured on the keeper's own payload (the charter's named killer)

The charter demanded that any detector-dependent design be proved ex ante on the
keeper's payload before being proposed. Both detector families were tested and
both fail, for different reasons.

**Plant-level run detector** (what the three existing P1-native bridges use). The
keeper's coal is at zero in 12.1 / 12.9 / 16.8 % of plant-hours — but those are
whole-month outages, not hour-scale decommitment (the monthly guard in §4's
construction sees the same months dark). Over the 83–88 % of plant-hours the
plant is running, the detector marks it committed, and a floor gated on it is
**the same blanket floor ERCOT-127 §3 refuted**. The charter's conclusion holds
even though its premise needed the correction in §0.

**Tranche-prefix detector** — the natural unit-grain detector: mark online the
minimal prefix of the merit stack whose capacity carries the hour's dispatch,
then floor at `0.3636 ×` that online capacity. It is **self-satisfying by
construction**. Because the prefix is chosen to cover the dispatch,
`C_on(t) < P(t) + c_last`, so the floor binds only where
`P(t) < 0.3636/(1−0.3636) × c_last = 0.571 × c_last` — a sliver whose width is
set by the last unit's size and by nothing the detector learned. Measured:

| year | binding share of plant-hours | lift | share of coal energy |
|---|---|---|---|
| 2023 | 16.0 % | 1.74 TWh | 2.9 % |
| 2024 | 16.4 % | 1.63 TWh | 2.8 % |
| 2025 | 8.9 % | 0.82 TWh | 1.4 % |

The detector **cannot force on a unit the LP chose to leave off, because it
infers "off" from the LP's own choice.** That is the general statement, and it
closes the detector family for good: any commitment state inferred from the
dispatch it is meant to constrain is circular.

## 3. The instrument at the right grain (charter task b)

### 3.1 What the mechanism would be

A per-plant `min_gen` floor at the plant's **minimum online configuration**,
`min_u MinLoad_u`, scaled by availability — `floor[g,t] = min_config_frac[g] ×
pmax[g] × availability[g,t]`. Note *scaled by*, not *capped at*: the existing
`fleet/floors.py::apply_netload_reliability_floor` caps at `avail × pmax`, which
at low availability pins a unit at 100 % of what is available and must not be
reused for a min-load floor.

**It does not re-base tranches onto units.** The tranches stay exactly what
`docs/binning-methodology.md` describes — cost bands forming a rising offer
curve, no tranche capacity or heat rate moved, no band multiplier touched, so
nothing propagates to `mc_cost` or the step-3 retirement screen. The floor acts
on the plant's total dispatch. **No other ERCOT class is affected** (coal-only
eligibility), and the mechanism is **ERCOT-scoped** (rule 25 `[R-ISO-SCOPE]`):
the parameter is derived from ERCOT-registered plants, and another ISO would
enter as `U` and derive its own.

### 3.2 The parameter, and its independent corroboration

Per plant, from EIA-860 `generator_operable` — a **registration** filing, not
measured operation, so it is rule-13 admissible as a forward input (it exists
for any vintage, and a retired unit leaves the file):

| plant | units | cap MW | `min_u MinLoad_u` | frac of model pmax | DAM min resource LSL p50 | COP resources / units |
|---|---|---|---|---|---|---|
| Limestone | 2 | 1688 | 300 | 0.162 | 262 | 2 / 2 |
| W A Parish | 4 | 2514 | 175 | 0.072 | 159 | 4 / 4 |
| Martin Lake | 3 | 2455 | 175 | 0.073 | 215 | 3 / 3 |
| Coleto Creek | 1 | 655 | 175 | 0.281 | **175** | 1 / 1 |
| Fayette | 3 | 1615 | 156 | 0.092 | 78 | **5 / 3** |
| Oak Grove | 2 | 1710 | 348 | 0.194 | **348** | 2 / 2 |
| San Miguel | 1 | 391 | 250 | 0.610 | 220 | 1 / 1 |
| Major Oak | 2 | 305 | 95 | 0.272 | 80 | 2 / 2 |
| J K Spruce | 2 | 1345 | 130 | 0.087 | **130** | 2 / 2 |
| Sandy Creek | 1 | 933 | 360 | 0.385 | 41 | **4 / 1** |

**The cross-check validates the instrument and explains its own exceptions.**
The three plants whose COP resources are *whole units* — Coleto Creek, Oak Grove,
J K Spruce — match **exactly** (175/175, 348/348, 130/130) across two entirely
independent filings, a federal design registration and an ERCOT market
registration. The two large misses are exactly the plants where COP resources
are **ownership shares** rather than units (Fayette 5 resources on 3 units,
Sandy Creek 4 on 1) — the same joint-ownership artifact ERCOT-124/125 diagnosed
on the offer curve, reappearing on the registration side. EIA-860 is the correct
unit-grain source; the COP is the corroborator where its resources are units.

**And it corroborates ERCOT-127 §2 independently.** The cap-weighted mean of
per-unit `MinLoad_u / Cap_u` across the fleet is **0.3325**, against the DAM
corpus's cap-weighted p50 `LSL/HSL` of **0.3636**. Two unrelated instruments,
0.03 apart. ERCOT-127's parameter was right.

**The fleet-effective floor is 0.159, not 0.3636.** Summing `min_u MinLoad_u`
across the ten plants gives 2,164 MW against 13,611 MW of capacity — the
correctly-grained floor is **44 % of the blanket one**, which is the whole
quantitative content of "the units reality shut down stay shut down".

## 4. Size the prize (charter task c)

Three floors, each applied by lifting the keeper's own per-plant series (the
ERCOT-127 §3 construction, a hard lower bound on what the LP would produce):
`plant_0.364` the blanket control; `oracle` the floor applied only to the
capacity CAMPD says reality held online that hour — **an oracle, rule-13
inadmissible as an input, used only as the ceiling no implementable rule can
beat**; `min_config` the §3 candidate.

**G1 — loading vs price, fleet-aggregate basis, |model − actual| ≤ 0.05:**

| | 2023 | 2024 | 2025 | **total** |
|---|---|---|---|---|
| keeper | 6/7 | 7/7 | 6/7 | **19/21** |
| `plant_0.364` (control) | 1/7 | 1/7 | 7/7 | **9/21** |
| **`oracle` (the CEILING)** | 7/7 | 6/7 | 7/7 | **20/21** |
| `min_config` (the candidate) | 7/7 | 6/7 | 6/7 | **19/21** |

**C1 coal, TWh against actual** (gate G2: within 2.0 every year):

| | 2023 | 2024 | 2025 | mean abs |
|---|---|---|---|---|
| keeper | −1.07 | −0.21 | −1.89 | 1.06 |
| `plant_0.364` | +5.85 | +5.33 | +2.00 | 4.39 |
| `oracle` | +1.70 | +1.83 | −0.63 | 1.39 |
| `min_config` | +0.66 | +1.09 | −1.13 | 0.96 |

**C8 forced share of coal energy** (cap 30 %): `min_config` **4.8 / 3.4 / 2.8 %**,
`oracle` 9.9 / 7.8 / 4.5 %, `plant_0.364` 17.2 / 15.9 / 12.1 %.

**Read honestly, this is a wash, and the ceiling is one band.** `min_config`
passes G2 comfortably (and is marginally better than the keeper on mean absolute
level), passes C8 with room, and **ties** G1 at 19/21 — but the 19 are not the
same 19: it repairs 2023 `<$15` (0.488 → 0.512 against 0.552) and **breaks** 2024
`≥$50` (0.767 → 0.776 against 0.720, an already-marginal band pushed over). G1 is
a do-no-harm gate, so a tie is a pass on the letter and a nothing on the
substance. **The oracle — reality's own commitment, which no forward rule can
improve on — buys exactly one band more than the keeper, and does it while
making C1 worse in two years of three.**

**And it barely touches the defect it was built for.** ERCOT-127 §4's per-plant
p05 finding (the model drives coal far below anything the real fleet does) under
`min_config`, 2023: Limestone 0.093 → **0.093** (actual 0.261); W A Parish 0.026
→ 0.057 (0.171); J K Spruce 0.013 → 0.088 (0.106); Martin Lake 0.058 → 0.085
(0.233). The physical floor is far below observed conduct — reality does not run
W A Parish on one of four units at min load, it runs two or three — so closing
that gap would require choosing a floor **above** the physical minimum. Rule 21
`[R-DOF]`: that is a residual-identified parameter, i.e. an open root-cause
issue, not a parameter.

## 5. G3 — the gate that demands a win, and refutes the whole family

The charter's G3 requires `COAL_LIGNITE` 2023 to **clear** both D-1 gates
(`profile_r ≥ 0.8`, `cv_ratio ≥ 0.5`) in the committed legitimacy artifact. The
keeper is a **live FAIL** there at 0.745 / 0.294, and coal is inside
`D1_GATED_CLASSES` since rubric v2.8 (the keeper's own artifact predates that and
carries `gated: false`). G3 is the only gate in the set that demands an
improvement rather than do-no-harm.

Computed exactly as `legitimacy_diagnostics.py` computes it — the probe's keeper
row reproduces the committed artifact (0.744 / 0.300 against 0.745 / 0.294):

| year · class | keeper | `min_config` | **`oracle`** | `plant_0.364` |
|---|---|---|---|---|
| **2023 COAL_LIGNITE** (the gate) | 0.744 / 0.300 | 0.724 / **0.274** | 0.741 / **0.283** | 0.738 / 0.272 |
| 2023 COAL_PRB | 0.995 / 1.114 | 0.995 / 1.058 | 0.992 / 0.925 | 0.991 / 0.800 |
| 2024 COAL_LIGNITE | 0.862 / 1.128 | 0.879 / 0.966 | 0.896 / 0.940 | 0.892 / 0.873 |
| 2025 COAL_LIGNITE | 0.914 / 1.624 | 0.918 / 1.366 | 0.928 / 1.313 | 0.930 / 1.206 |

**Every variant moves the gated cell further from passing, and so does the
ORACLE.** `cv_ratio` falls in all twelve class-years. G3 is therefore
**unreachable ex ante by the entire min-load-floor family, at any grain and any
value, including a perfect one.**

This is structural, and it generalises. `cv_ratio` is the model's off-peak
(h0–14) hour-of-day-mean CV over the actual's. The keeper's model CV is 0.017
against actual 0.057 — the model is **3.4× too flat overnight**. A lower bound
is constant across hour-of-day, so it raises the trough and leaves the rest: it
can only reduce the model's CV. **No floor can fix an over-flatness defect.** A
floor with an hour-of-day window could, but unit min-load has no diurnal driver,
so that window would be shaped to the residual — rule 17 `[R-FLOOR-WINDOW]` and
rule 23 `[R-FROZEN-DERIVE]` both forbid it.

## 6. Where the D-1 failure actually is — and it is already a named finding

Measuring the ERCOT-126 §1.4 flat-top pin statistic **on the off-peak window the
gate is computed over** (probe §G, share of h0–14 energy delivered within 0.5 %
of that plant-month's own maximum):

| year · class | model | actual | ratio |
|---|---|---|---|
| **2023 COAL_LIGNITE** | **73.3 %** | **6.2 %** | **11.8×** |
| 2024 COAL_LIGNITE | 66.7 % | 4.6 % | 14.4× |
| 2025 COAL_LIGNITE | 77.3 % | 18.6 % | 4.2× |
| 2023 COAL_PRB | 17.6 % | 1.5 % | 12.1× |

**The D-1 cv_ratio failure and the ERCOT-126 §1.4 ceiling pin are the same
phenomenon.** Three-quarters of the model's lignite energy overnight is
delivered on a binding flat top; a series pinned at its ceiling has no
overnight variance, which is precisely `model_offpeak_cv = 0.017`. The coal
residual's remaining open item is therefore **not** that coal needs holding up
at the bottom — it is that **nothing holds it down at the top**, which is
exactly what ERCOT-126 §5.2 and ERCOT-127 §5.2 said and what only the ERCOT-116
measured availability envelope touches.

**This is a new argument for owner decision (1), and it is the strongest one
yet.** ERCOT-116 halves the pin (43/41/50 % → 20/16/17 %). The pin is what fails
D-1. G3 — a gate the charter itself wrote — is failing on the keeper *now*, and
this session establishes that no mechanism in the min-load family can ever clear
it. The standing objection to ERCOT-116 has been "premature, wait until
something caps coal below its ceiling"; ERCOT-127 §5.3 showed nothing will on
the current architecture, and this session closes the last candidate that might
have.

## 7. Rule 19 and the attribution path, stated before proposing (charter task d)

Confirmed against the code, so the design is complete on paper even though it is
not recommended:

* **What it would stack on: nothing.** D-2 carries no COAL row in any year of
  the keeper's artifact, and none of the four live floors (`chp_steam`,
  `reliability_floor` on CC_REGULAR + CT_PEAKER, `gas_commitment_bridge` on
  CC_REGULAR, `st_netload_drag` on ST_GAS) touches coal. Rule 19
  `[R-ONE-MECH]` is clean. Note `MECH_COAL_MUSTRUN` (id 3) already exists as a
  distinct mechanism for the coal must-run tranche and must not be reused.
* **Attribution:** a new `MECH_COAL_MIN_CONFIG` id in
  `src/market_sim/data/floor_mechanisms.py` (next free id 21) with its
  `MECH_NAMES` entry, plus a `D4_WINDOWS[(MECH_COAL_MIN_CONFIG, None)] = (0, 24)`
  entry in `scripts/legitimacy_diagnostics.py` — all-hours by driver, since a
  registered minimum load applies in every hour the unit is synchronised and
  there is no hour its own driver evidence says it is offline.
* **Expected C8, declared:** 4.8 / 3.4 / 2.8 % (§4), far under the 30 % merchant
  cap, so no rule-20 escalation path is engaged.
* **DOF ledger (rule 21):** one new parameter, per-plant `min_config_mw`,
  `lineage_solves = 0`, identified from EIA-860 `Minimum Load (MW)` and
  corroborated by the COP `LSL`. It would have to reach the LP through a derived
  artifact on the data path (the `thermal_tranches_<ISO>.csv` pattern), never a
  hardcoded per-plant dict — rule 26 `[R-REGISTRY]`.

## 8. Recommendation — recommend-and-STOP (keeper untouched; owner decides)

1. **Phase 2 is NOT run and no mechanism is licensed.** The correctly-grained
   unit-grain min-load floor is refuted **ex ante** on the charter's own gates:
   G1 19/21 against the keeper's 19/21 (a swap, §4), and **G3 unreachable — the
   gated cell moves the wrong way under the ORACLE**, so no implementable rule
   can clear it (§5). Solving would spend ~50 minutes to measure a verdict §4
   and §5 already bound. Abstaining is the charter's own listed valid outcome
   and this is the seventh precedent.
2. **The architectural question is ANSWERED and should not be re-opened as an
   architecture question.** Unit-grain commitment *state* is unavailable in pure
   LP (§1.1) and every detector for it is circular (§2) — but the lower envelope
   is exactly expressible for 97.8 % of ERCOT coal capacity as a static `pmin`
   (§1.3), with a registration-grade parameter (§3.2) and no change to the
   tranche curve (§3.1). **The obstacle was never the architecture. It is that
   the physically-correct floor is far below observed conduct, so it buys
   nothing** — and closing the rest would require choosing a value above the
   physical minimum, which rule 21 makes an open root-cause issue rather than a
   parameter.
3. **The coal band lane should now CLOSE, as ERCOT-127 §5.4 proposed.** With
   ERCOT-122 (offer level), -123 (reach), -124 (upper tail), -125 (owner split),
   -126 (availability), -127 (dispatch band) and this session (unit grain), every
   instrument is closed. The residual stays **attributed**, not tuned (rule 1
   `[R-STRUCT]`).
4. **Owner decision (1) — the ERCOT-116 keeper question — is materially
   strengthened and is now the lane's only live item.** §5 and §6 establish that
   the keeper carries a **live G3/C7 FAIL** on `COAL_LIGNITE` 2023, that the
   failure IS the ceiling pin, and that **no min-load mechanism can ever repair
   it**. ERCOT-116 is the only registered instrument that touches the pin. This
   session does **not** arm or promote it (hard constraint), and does not
   re-litigate its C1 cost (+5.7 / +8.9 / +11.0 TWh) — that trade is the
   owner's. What changes is that "premature" no longer has a successor to wait
   for.
5. **The derived artifacts stand as the committed measured record.**
   `data/raw/_validation-source/ercot128_coal_unit_grain.json` (sections A–G),
   produced by `scripts/probes/ercot128_coal_unit_grain.py`. Nothing is on a
   loader path; no artifact can arm anything by accident.
6. **Owner decisions surfaced, NOT decided.** All four inherited from ERCOT-127
   stand unchanged except as noted:
   (a) **ERCOT-116** — see item 4; the only change is that its standing
   objection has lost its successor.
   (b) `BIN_FORCED_DERATE_BY_YEAR` (`eia860.py:2392-2404`) — the live rule-26
   `[R-REGISTRY]` breach, untouched since ERCOT-126 flagged it. `"SC_COAL3":
   {2025: 0.0}` redundant and wrong with a correctly-dated measured replacement
   already committed; `"N_COAL4": {2025: 0.67}` factually right but load-bearing.
   Still its own default-changing lane. This session touched neither entry.
   (c) **The ramp-envelope gross/net basis error** (ERCOT-127 §1) — unchanged,
   still a real cross-ISO correctness bug in a registered mechanism, default-
   affecting for any ISO arming `ramp_limits`, including the live CAISO artifact
   on the loader path. Not fixed here (out of scope, and this lane builds no LP).
   (d) **The ERCOT-122 offer-LEVEL controlled refutation** — one `replay_keeper`
   away, separate bundle, `DIAGNOSIS-ercot122` §5.1 as its pre-commit. This
   session adds no new argument either way.
   (e) **NEW, and it is stop-the-line for the whole repo, not this lane: the
   default cache key is BROKEN on `origin/main`.** Found while re-measuring test
   state on an empty tracked diff (§9), root-caused, and **deliberately not
   fixed here** — it belongs to another lane and it is default-affecting.
   `tests/regression/test_persisted_identity.py` fails 2 of 11 at `c5681fb`:
   `ScenarioConfig().cache_key()` is `2904ac9ad9ed5c0c` against the pinned
   `603c2498bf71d21d`. Bisected by checking out `scenarios.py` alone at each
   commit that touched it since the pin was last set: clean at `fb8a34f`,
   `9df6be7`, `09b5141`, `acc13fd`, `c45fed4`, `98a5655`; **broken at `b9d2b4d`
   (pjm-134)**, which added `pjm_apsouth_interface_cut: bool = False` without
   registering it in `_CACHE_KEY_OPTIONAL_FIELDS`. The test's own message states
   the stake: this orphans every on-disk cache and breaks keeper
   reproducibility. Two exact precedents fixed the identical mistake with a
   one-line registration — `9df6be7` (`coal_committed_takeorpay_sunk_fixed`) and
   `c45fed4` (`measured_ct_heat_rates`) — so the fix is that one line, **not**
   re-pinning the literal.

## 9. Scope, closed items honoured, environment

No year solved, no run registered, no arm built;
`frontend/data/backcast/keepers/ERCOT.json` untouched. The session's diff against
`origin/main` is **one probe script, one derived artifact, this diagnosis and the
calibration-log entry**. No `ScenarioConfig` field, cache-key surface, solve path
or existing artifact was touched, so no config pin moved and no existing run can
change. No derive script was modified (rule 23 `[R-FROZEN-DERIVE]`); no floor
parameter was chosen against a residual. No GitHub Actions workflow was added,
and no CI job was used for any part of this work.

Rule 22 `[R-HOLDOUT]`: every window is {2023, 2024, 2025}. No 2022-or-earlier
quantity appears anywhere; the 60-Day DAM `*_Jan-Mar` files carry trailing
Nov/Dec-2022 delivery rows and §3.2's corpus drops them explicitly before any
aggregate, exactly as the ERCOT-126/127 probes do.

Closed lists honoured: all four coal offer-surface lanes (level, reach, tail,
owner split); the whole coal availability layer (ERCOT-126 §§2–3); coal ramp
trajectory bounds (ERCOT-127 §1); the **plant-grain** coal min-load floor
(ERCOT-127 §3), which appears here only as a reproduced control and is not
re-opened; ERCOT-117 §5.3, which remains subsumed; age/temp coal derates
(ERCOT-121 §1a); the EP-rebasis lane as a C3c fix and the peak-p50/quantile-ladder
legs (ERCOT-119); the pooled HH-0.50 artifacts; `ercot_zonal_gas_basis`
ablations; the West/Panhandle topology split. ERCOT-120 remains a separate
un-renumbered lane, neither folded in nor blocked on.

**Sampling bounds, carried on every number.** Sections C–G are **FULL SPAN**
(8760 h × 3 years). §3.2's DAM corpus is the ERCOT-127 §2 corpus (627,641
CLLIG resource-hours across all three years). §1.3 and §3.2's registrations are
census, not sample. Nothing here rests on the 82-probe-day SCED corpus — the
bound that killed ERCOT-124 and -125.

**Environment parity.** Fresh container: the `gtc-limits` clean partition is
absent, so the "static TTC kept" fallback applies as it did for every
ercot115–127 baseline; the `hydro-plant-modes` clean-partition WARNING is
expected. Neither affects this session, which builds no LP.

**Test state, re-measured on an empty tracked diff** (this session's three files
are all untracked additions, so nothing here is attributable to it):
`tests/unit/config/test_flag_registry.py` **12/12 PASS**;
`tests/regression/test_persisted_identity.py` **9/11 — 2 PRE-EXISTING FAILURES**,
root-caused in §8(6e) to `b9d2b4d` and **not** this lane's to fix;
`tests/unit/results/test_export.py` 4 pre-existing failures and
`tests/scoring/test_ff_readiness_battery.py` 4 pre-existing failures, both
unchanged from the ERCOT-127 baseline. No pin was updated in either direction.

---

# PHASE 2 ADDENDUM — the arm was BUILT and SOLVED. It passes every absolute gate and fails its own structural claim

**Added 2026-07-28, after the owner reversed §8's abstention on rule 1
`[R-STRUCT]`.** The reversal was correct and is recorded as such: §8 rejected a
structurally-correct measured mechanism partly because the residual didn't move,
and partly on a gate (G3) belonging to a different mechanism's residual — both
of which rule 1 forbids as grounds for rejection. Phase 2 was therefore run.

**Arm** `results/calibration/ercot128_unit_grain` ·
run id `2026-07-28-ercot128-unit-grain-coal` · pre-commit
`docs/PRECOMMIT-ercot128-coal-min-config-2026-07-28.md`, pushed before the first
solve · single delta `ercot_coal_min_config_floor=true` · three years, one
invocation, years sequential.

**Verdict: NOT a recommended keeper candidate — and NOT for a fit reason.** Every
absolute gate passes, G1 ties, and G2 improves in all three years. What fails is
the mechanism's **own pre-registered structural evidence** (§4.4 of the
pre-commit): the arm does not remove the physically-impossible plant loadings it
exists to remove. §P4 gives the root cause and the fix.

## P1. The gates, as pre-committed

| gate | criterion | keeper | **arm** | verdict |
|---|---|---|---|---|
| **G0** arming + bite | 3/3 logs, run_config, non-zero D-2 row | no COAL row | 6 `ARMED` lines (P0+P1 × 3 yr), 10 plants / **2164 MW**; `run_config.ercot_coal_min_config_floor: true`; D-2 `coal_min_config` **1.749 / 1.679 / 1.393 TWh** | **PASS** |
| **G1** loading-vs-price | do-no-harm, ≥ 19/21 | 19/21 | **19/21** (6/7 · 7/7 · 6/7 — the same two `<$15` bands fail) | **PASS** |
| **G2** C1 coal level | within ±2.0 TWh every year | −1.078 / −0.294 / −1.926 | **−0.955 / −0.102 / −1.678** | **PASS**, better in all three years (mean abs 0.91 vs 1.10) |
| **G3** D-1 do-no-harm | ≤ 0.030 fall vs keeper, every coal class-year | — | see §P2 | **FAIL as written** |
| **G4** rubric + C8 | C1 16/16 · free 12/12; forced share < 30 % | — | **C1 all 16/16 · free 12/12**; coal forced **2.94 / 2.92 / 2.30 %** | **PASS** |
| **G5** LOYO | per-year, 2-of-3 fails | — | G1 and G2 verdicts hold independently in each of 2023, 2024, 2025 | **PASS** |
| **G6** DOF ledger | measured, `lineage_solves = 0` | — | per-plant `min_config_mw`, EIA-860 registration, no fitted value | **PASS** |

D-4 is clean: `coal_min_config`, window `h0-23`, **off-window share 0.0 %** in
all three years. The arm introduces **no new rubric failure** — its failing
gates (C3a/C3b 2023, C3c all years, C7 `COAL_LIGNITE` 2023) are exactly the
keeper's known open set.

## P2. G3 fails as written, and the tolerance was mine and mis-specified

| year · class | keeper `r`/`cv_ratio` | arm | fall in `cv_ratio` | vs the 0.030 bound |
|---|---|---|---|---|
| 2023 COAL_LIGNITE | 0.745 / 0.294 | 0.736 / 0.281 | 0.013 | pass |
| 2023 COAL_PRB | 0.995 / 1.110 | 0.995 / 1.113 | rose | pass |
| 2024 COAL_LIGNITE | 0.862 / 1.117 | 0.885 / 0.976 | **0.141** | **FAIL** |
| 2024 COAL_PRB | 0.986 / 0.813 | 0.987 / 0.813 | 0.000 | pass |
| 2025 COAL_LIGNITE | 0.913 / 1.612 | 0.927 / 1.375 | **0.237** | **FAIL** |
| 2025 COAL_PRB | 0.975 / 1.161 | 0.977 / 1.123 | **0.038** | **FAIL** |

**Reported as a FAIL, and not rewritten.** The pre-commit says a gate that fails,
fails. The tolerance is nonetheless a bad one and that is my error, stated
plainly rather than repaired: an **absolute** 0.030 band applied to a ratio whose
keeper values span 0.294 to 1.612 is ~10 % of one cell and ~2 % of another.

The substantive picture, for the owner's judgement and not as a substitute for
the verdict above: on the gate the **scorer actually enforces** (`r ≥ 0.8`,
`cv_ratio ≥ 0.5`) the arm fails exactly one coal class-year — 2023
`COAL_LIGNITE` — which is precisely the cell the keeper fails, and it **improves
`profile_r` in four of six** class-years while never dropping one from pass to
fail.

## P3. The structural claim — the arm's own pre-registered evidence, and it is negative

Pre-commit §4.4 fixed the affirmative case in advance: *"evidenced by the
per-plant p05 loading moving toward, and never past, the real fleet's — reported
for every plant-year whatever it shows."*

**It does not move toward.** Across 29 scoreable plant-years the arm's p05 moves
closer to the real fleet's in **10** and away in **19**. Nothing overshoots
(1 of 29 sits above actual — Oak Grove 2023 — and it was already above on the
keeper, 0.767, which the arm *reduces* to 0.721). Examples, 2023: Limestone
0.093 → 0.104 (actual 0.261); W A Parish 0.026 → **0.011** (0.171); J K Spruce
0.013 → 0.015 (0.106). The one real closure is **San Miguel**, the single-unit
plant whose min-config is 0.639 of capacity: 0.507 → 0.569 in 2023,
0.317 → 0.376 in 2024, 0.493 → 0.558 in 2025 against ~0.58 actual.

**And the direct measure — the one the mechanism literally controls — confirms
it.** Counting online plant-hours delivering **below** the plant's own
`min_u MinLoad_u`, i.e. a level no combination of its units can produce:

| year | keeper | **arm** | keeper share of online hours | **arm share** |
|---|---|---|---|---|
| 2023 | 14,582 | **14,886** | 18.7 % | **19.0 %** |
| 2024 | 13,020 | **13,051** | 17.0 % | **16.9 %** |
| 2025 | 9,558 | **9,561** | 13.1 % | **13.0 %** |

**The arm removes essentially none of them.** That is the whole structural claim,
measured directly, and it is not delivered.

## P4. Root cause — the floor is availability-SCALED, and it should be availability-CONDITIONAL

The floor is built as `min_config_frac[g] × pmax[g] × availability[g,t]`, the
scaling form chosen deliberately (§3.1) because `min_gen` must not exceed
`pmax × availability` or the LP is infeasible, and because the existing
`apply_netload_reliability_floor` *caps* instead of scaling and would pin a unit
at 100 % of what is available.

**Scaling is the wrong physics for this quantity.** A minimum online
configuration does not shrink when units go out: a 4-unit plant with 2 units on
outage still cannot run below **one unit's** 175 MW — it either makes 175 MW or
it is off. ERCOT coal availability under the DAM water-fill sits well below 1.0
in most hours, so the applied floor lands *below* the physical minimum in exactly
the hours the defect lives in. The decomposition shows the consequence: of the
arm's change against the keeper, **89 / 72 / 68 %** is raising plants that were
already online, and only 554 / 643 / 885 plant-hours are newly on. The floor is
nudging, not bounding.

**The fix is small and stays inside pure LP.** `availability[g,t]` is exogenous
data, not a decision variable, so a *conditional* is a data-side computation with
no integrality:

```
floor[g,t] = min_config_mw[g]   if availability[g,t] × pmax[g] ≥ min_config_mw[g]
           = 0                  otherwise      # plant cannot reach min config → off
```

This is the mechanism §1.3's exactness proof actually describes — the proof was
always conditional on *at least one unit online*, and the availability-scaled
build quietly dropped that condition. It is the natural successor and it is
cheap: one expression in `_compose_min_gen_floors`, the same artifact, the same
flag, the same mechanism id, one re-solve.

## P5. Recommendation

1. **Do NOT promote `2026-07-28-ercot128-unit-grain-coal`.** Registered on the
   dashboard as a rejected probe (rule 15). `frontend/data/backcast/keepers/ERCOT.json`
   untouched.
2. **The reason is NOT the fit** — G1 ties, G2 improves in all three years, no new
   rubric failure. Under rule 1 those would not be grounds. The reason is that it
   **costs 1.4–1.7 TWh/yr of forced energy and removes ~0 of the 9.5–14.9 k
   physically-impossible plant-hours it exists to remove** (§P3). Forcing without
   the mechanism actually biting is the one outcome rule 1 does not protect.
3. **The successor is specified and narrow** (§P4): re-solve the same flag with an
   availability-**conditional** floor. If that removes the impossible plant-hours
   while holding G1/G2, it is a genuine keeper candidate on rule-1 grounds, and
   the arm here is its control.
4. **Everything built stands and is reusable**: the derive, artifact, loader,
   `ScenarioConfig` flag (default off, cache key unmoved at the pinned
   `603c2498bf71d21d`), `MECH_COAL_MIN_CONFIG`, the D-4 window, and 14 unit tests.
   The successor changes one expression.
5. **Owner decisions (§8 item 6) all stand unchanged**, including (e), the
   `pjm_apsouth_interface_cut` cache-key regression — **fixed on this branch** in
   its own commit, restoring the default key to the pinned literal.
