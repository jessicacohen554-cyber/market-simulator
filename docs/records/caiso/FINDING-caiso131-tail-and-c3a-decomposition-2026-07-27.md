# FINDING — caiso-131: C3a-2025 and C3c are **NOT one defect** — they do not even share a year. C3c fails **2023/2024 only** (2025 already PASSES on the rubric's small-count rule); C3a fails **2025 only**. The tail is worth −$0.25 to −$1.41/MWh of a +$0.97…+$2.90 residual that lives in the *belly*, in different months, and closing C3c costs 2023/2024 only +$0.60/+$0.36 against +$3.67/+$0.69 of band headroom. The leading "shift level out of the belly into the tail" hypothesis is REFUTED as a mechanism identity — and the refutation is good news: the two criteria are **separable and can be worked independently**.

**Keeper `2026-07-27-caiso-130-nameplate-aware` UNCHANGED. Measurement-only
session — NO LP was built or solved, no mechanism was armed, nothing was
registered.** Per the charter's step 3, the deliverable is a FINDING plus a
filed ask; step 4 (prereg + A/B) is conditional on the diagnosis landing a
candidate with a real driver, and §8 states honestly that it does not — the
kill-before-solve arithmetic in §5 and the band envelope in §1 kill every
candidate now on the table before a solve.

Instrument (committed): `scripts/probes/_caiso131_tail_and_level_decomp.py`,
sections A–E. Every number below is reproducible from the keeper's **committed
hourly sidecars** (`hourly/system_<y>.parquet`, `class_hourly_<y>.parquet`,
`storage_<y>.parquet` — never a replay), the committed actual-LMP reference,
the committed `bench/CAISO/<y>.json.gz` and `tail/actual_tail.json` parts, the
committed CA citygate daily print, and a `run_year(fleet_only=True)`
reconstruction (sections C/D) that assembles the P0 objective and the exact
availability caps without building a matrix or calling HiGHS.

Basis note, stated up front: §1 scores on the **rubric's** basis and
reproduces its numbers digit-for-digit (C3a-2025 **+10.91 %** vs the rubric's
+10.9 %). §2/§3 decompose on ONE common weight vector (the rubric's own
`rt_lw` measured-load weights applied to both sides) so the bin contributions
sum exactly to the printed gap; that gap is smaller than §1's by the
weight-basis term reported at the foot of each year (+0.77/+0.48/+0.81 $/MWh).
The extract basis is frozen (caiso-123 / neiso-66) — the term is reported as a
measured fact and is **not actionable**.

---

## §1 — the two gates, per year, with their margins (§A)

| year | C3a model | C3a actual (`rt_lw`) | C3a | band margin | C3c model | C3c actual RT | C3c required | C3c |
|---|---|---|---|---|---|---|---|---|
| 2023 | 55.91 | 54.17 | **+3.22 % PASS** | **+$3.67** | 0 h | 47 h | [23.5, 94] h | **FAIL** |
| 2024 | 37.37 | 34.60 | **+8.00 % PASS** | **+$0.69** | 0 h | 35 h | [17.5, 70] h | **FAIL** |
| 2025 | 38.14 | 34.39 | **+10.91 % FAIL** | **−$0.31** | 0 h | 8 h | \|Δ\| ≤ 10 h | **PASS** |

**The single most consequential line in this FINDING is the 2025 C3c cell.**
The rubric's small-count rule (`TAIL_SMALL_COUNT = 10`,
`scripts/calibration_verdict.py:326`) replaces the ratio band with
`|model − actual| ≤ 10 h` whenever the RT actual is under 10 hours. CAISO's
2025 RT actual is **8 h**, so `|0 − 8| = 8 ≤ 10` and **2025 already passes
C3c**. The keeper's own scorer confirms it: `calibration_verdict.py` prints a
FAIL row for 2023 and 2024 and no gated row at all for 2025 (only the
non-gated DA companion), because passing rows are not printed.

So the determination basis is not "two criteria" but **three ISO-years**:
C3c-2023, C3c-2024, C3a-2025. **No year fails both.**

## §2 — the leading hypothesis, TESTED and REFUTED (§B)

The charter's leading hypothesis — the model is too expensive in the belly and
absent in the tail, so one redistribution closes both — is refuted three
independent ways.

**(i) They live in different years.** §1. C3a's only failing year is the one
year C3c already passes.

**(ii) They live in different months.** Monthly contributions to the C3a
residual ($/MWh of the annual weighted mean):

| year | Jan | Sep | Oct | Nov | Dec | where the C3c tail hours are |
|---|---|---|---|---|---|---|
| 2023 | **−0.31** | +0.37 | −0.12 | +0.09 | +0.27 | **24 of 47 in January** |
| 2024 | **−0.35** | +0.28 | +0.07 | −0.10 | +0.28 | **26 of 35 in January** |
| 2025 | **−0.23** | **+0.60** | **+0.81** | +0.35 | **+0.60** | 8 of 8 in Jan/Mar/Apr |

January is a **negative** contributor to C3a in all three years — the model is
too *cheap* in exactly the month that carries the tail. The C3a-2025 failure is
**Sep–Dec**: +0.60/+0.81/+0.35/+0.60 = **+$2.36 of the +$2.90 gap (81 %)**.
A redistribution out of Sep–Dec into January mornings is not one mechanism; it
is two.

**(iii) The magnitudes do not net.** Contributions by actual-price regime:

| year | belly (actual < $60) | shoulder ($60–200) | tail (> $200) | total |
|---|---|---|---|---|
| 2023 | **+5.72** | −3.35 | **−1.41** | +0.97 |
| 2024 | **+4.36** | −1.33 | **−0.80** | +2.24 |
| 2025 | **+4.12** | −0.96 | **−0.25** | +2.90 |

The belly excess is **3–6× the tail deficit** and of the opposite sign, so the
tail cannot be the belly's counterpart. In 2025 the entire >$200 bin is 8 hours
worth **−$0.25/MWh** against a residual of +$2.90 — a 9 % term.

**What IS true, and is worth keeping:** the model's price *distribution* is
compressed. It runs +$4.1…+$5.7/MWh hot across the bottom ~90 % of hours and
−$1.0…−$3.4 cold across the top ~6 %, and its absolute maximum zonal price over
the whole year is **$192.3 / $155.3 / $94.3** — it never reaches $200 in any
hour of any year. That compression is real and is the common *symptom*. It is
not a common *mechanism*, and treating it as one walks straight into the
caiso-127 §1 trap.

## §3 — the practical consequence: the two are SEPARABLE, and the ordering is fixed

Closing C3c means lifting ≥24 h (2023) and ≥18 h (2024) above $200. At the
measured tail-hour mean price, and lifting only those hours, that adds:

| year | hours needed | cost to the C3a mean | C3a band headroom | verdict |
|---|---|---|---|---|
| 2023 | 24 | **+$0.60** | **+$3.67** | ample — 6× cover |
| 2024 | 18 | **+$0.36** | **+$0.69** | **tight — 52 % of the remaining band** |
| 2025 | 0 (already passes) | — | **−$0.31 required** | must not move UP at all |

Three binding design constraints fall straight out, and they are the envelope
any C3c candidate must clear **before** it is solved:

1. **2025 must be untouched (or moved down).** 2025 needs no tail and has
   *negative* band room. A candidate that lifts 2025's annual mean by any
   amount makes the only currently-failing C3a year worse.
2. **2024 has $0.69 of room and a C3c fix already spends $0.36 of it.** A
   candidate whose off-tail spillover exceeds ~+$0.30/MWh in 2024 converts a
   C3c fix into a C3a-2024 failure — trading one fail for another.
3. **The candidate must be NARROW in hours.** It must lift ~24/18 hours and
   essentially nothing else. Any broad evening/import repricing is excluded by
   (1) and (2) by arithmetic, not by preference.

This is the concrete, quantified form of the caiso-127 §1 trap, and it is why
the "redistribution" framing had to be tested rather than assumed: the *sign*
of the hypothesis is right, its *arithmetic* is not.

## §4 — the C3c discriminator: it is (a) surplus, not (b) reserve dual, not (c) offer ceiling (§C)

The charter asks which of three causes produces a zero-hour tail. Measured on
the keeper:

**(c) An offer ceiling that truncates — REFUTED, decisively.** The top of the
model's own offer stack is **$1,266 / $687 / $1,632 per MWh**, and the fleet
offers **732 / 248 / 250 MW/h** above $200 on average. In the measured tail
hours specifically the stack carries **3,749 / 9,570 / 108 MW** priced above
$200. The expensive rungs exist and are correctly gas-priced (§6). The LP never
climbs onto them. **C3c is not an offer-curve question, and no offer-curve work
can close it.**

**(b) A reserve requirement that never binds / a dual that never crosses — TRUE
but DERIVED, not causal.** `reserve_price` is identically **0.00 in all 61,320
zone-hours of every year**: `caiso_reserve_coopt` and `energy_reserve_coopt`
are both off, so there is no in-LP reserve product to bind. The published
scarcity mechanism *is* armed — the keeper runs `caiso_scarcity_pricing=True`,
so the persisted prices already include the CAISO LOLP overlay
(`runner.py:2029`, `results/scarcity.caiso_scarcity_overlay`; VOLL $2,000,
MCL 1,400 MW, σ 2,500 MW) — and it produces essentially nothing. It cannot: the
adder is `LOLP(R) × (VOLL − λ)` and R never approaches MCL (below). **The
inert dual is a consequence of (a), not an independent cause.**

**(a) A supply surplus that never tightens — THE CAUSE.** Dispatchable headroom
(gas + import + hydro, `pmax × availability − dispatch`):

| year | median | at the model's own top-50 λ hours | in the measured tail hours | **MIN over all 8,760 h** |
|---|---|---|---|---|
| 2023 | 27,692 MW | 24,799 | 22,628 | **12,173 MW** |
| 2024 | 28,157 | 28,575 | 27,511 | **12,689 MW** |
| 2025 | 27,932 | 18,691 | 24,242 | **13,137 MW** |

**At its tightest hour of the year the model still holds 12.2–13.1 GW of
unloaded dispatchable capability**, and `slack` (unserved energy) is zero in
every hour of every year. Against an MCL of 1,400 MW and σ of 2,500 MW, an
LOLP adder needs R within a few σ of 1.4 GW; the model's R is an order of
magnitude above that, always.

**Cross-ISO: this is the same class the charter flags, and CAISO's diagnosis is
the sharpest instance of it.** The `results/scarcity.py` HONESTY GATE for PJM
records the identical finding in the code itself — *"on TOTAL fleet headroom
the perfect-foresight LP carries ~39 GW and never goes short"* — and PJM's
answer was to move to a plant-level **online (synchronized)** reserve measure.
CAISO's overlay is still evaluated on total headroom, i.e. precisely the
measure PJM's own honesty gate documents as never-binding. That is a real,
named, cross-ISO defect in the CAISO overlay's reserve *measure* — and §5 shows
why fixing it is necessary but nowhere near sufficient.

## §5 — the kill-before-solve arithmetic: the (λ, $200] band is 12.6–12.8 GW deep (§D)

For the energy dual to reach $200 in a measured tail hour, every MW offered
between λ and $200 must be removed from the stack or re-priced through. In the
measured tail hours that band holds:

| year | gas_cc | gas_ct | gas_st | import | hydro | **TOTAL** |
|---|---|---|---|---|---|---|
| 2023 | 2,690 | **5,219** | 1,280 | **3,411** | 0 | **12,609 MW** |
| 2024 | 2,772 | **5,163** | 414 | **4,431** | 0 | **12,816 MW** |
| 2025 | 1,541 | 7,255 | 2,051 | 10,365 | 0 | 21,372 MW |

**12.6–12.8 GW.** That is 52 % of the *entire available gas fleet* in those
hours (headroom/available = 0.52 in both 2023 and 2024), spread across three
gas classes and the import tranches with no single dominant limb. No
physically-grounded derate removes it: a SoCalGas OFO curtails single-GW
quantities of burn, not 12.8 GW; the measured corridor import envelope leaves
only 1.6/2.8 GW of deliverable import headroom to take away.

**Therefore: no quantity-side (derate / availability / deliverability)
mechanism can reach C3c on the energy dual for CAISO.** This is the general
form, not a property of any particular candidate — it is scale-invariant in the
same sense as FINDING-caiso129 §3(a), because the band is measured against the
LP's own clearing price in its own tail hours.

The only channels that remain are (i) a **price** adder stacked on λ — which is
exactly the G-20a settlement-price construction every other ISO already uses,
and which for CAISO is the LOLP overlay whose reserve measure §4 shows is
mis-specified — or (ii) **re-pricing the marginal rung** rather than removing
it, which is caiso-114's mechanism and is excluded for 2024/2025 by §3's
envelope (below).

## §6 — what actually makes the measured tail hours expensive (§E)

CAISO's measured RT tail is **not** a summer-evening net-peak phenomenon, and
this closes a whole family of candidates by itself.

| year | hours | distinct days | concentration | net load | 1-h net-load ramp | CA citygate |
|---|---|---|---|---|---|---|
| 2023 | 47 | 22 | **24 in January**, hod 6–7 | 24.3 GW (p88) | +1,066 MW (p76) | **$11.25 (p90)**, yr mean 5.20 |
| 2024 | 35 | 9 | **26 in January**, one 16-h run | 22.3 GW (p78) | +641 MW (p69) | **$10.41 (p99)**, yr mean 2.43 |
| 2025 | 8 | 5 | Jan/Mar/Apr, **hod 5–9 only** | 19.6 GW (p65) | +804 MW (p71) | $3.05 (p57), yr mean 3.04 |

- **2023 and 2024 are winter gas events**, at the 90th and 99th percentile of
  the year's own citygate distribution, at load and ramp percentiles that are
  unremarkable. The model's gas passthrough *works* on those days — its
  capacity-weighted CC offer rises to **$103 / $121** (year means $61 / $42)
  and its CT offer to **$145 / $164** — and λ still only reaches $112 / $123,
  because 22.6/27.5 GW of headroom remains. The real market was pricing **gas
  deliverability**, a commodity the LP does not represent; even a perfect fuel
  price leaves a $150–200/MWh gap.
- **2025's 8 hours have no driver expressible in an hourly cost-based LP on
  measured drivers at all** — not gas (57th percentile), not load (65th), not
  ramp (71st), all at hod 5–9. They are RT-only sub-hourly formations. This is
  the same anatomy MISO and NEISO put on the record when they ledgered C3c.
  Fortunately 2025 needs no tail (§1).
- **A gas-event trigger is automatically inert in 2025** — the 2025 citygate
  never exceeds **$5.61/MMBtu** against 2023's $24.29 and 2024's $17.34, so
  zero 2025 hours sit above any 2023/24-relevant threshold. That is the right
  *shape* for §3's envelope. But it is not sufficient: a citygate > $8/MMBtu
  trigger covers only **27 of 47** (2023) and **17 of 35** (2024) tail hours,
  against needs of 24 and 18 — 2023 clears, **2024 misses by one hour**. Moving
  the threshold until 2024 clears is a value fitted to the residual (rules 13
  `[R-MEASURED]` / 24 `[R-DOF]`) and is forbidden. Any such trigger must be
  derived from the *source event* — an actual SoCalGas OFO declaration record —
  which the repo does not currently hold.

## §7 — the C3a-2025 side: what is different about 2025, and where the residual is (§B)

Before attributing anything to a mechanism, the year's own facts, from the
keeper's committed sidecars and the committed gas print:

| | 2023 | 2024 | **2025** |
|---|---|---|---|
| gas price (run) | 2.54 | 2.19 | **3.52** ($/MMBtu) |
| CA citygate mean / p95 / **max** | 5.20 / 15.56 / **24.29** | 2.43 / 3.67 / **17.34** | 3.04 / 3.93 / **5.61** |
| storage discharge | 6.00 TWh | 9.85 | **13.60** (fleet 7.6 → 11.4 → **15.2 GW**) |
| solar | 39.3 TWh | 46.8 | **52.5** |
| gas | 60.5 TWh | 53.3 | **45.3** |
| hydro | 24.3 TWh | 22.3 | 21.2 |

2025 is the year with the largest storage fleet, the most solar, the least
gas — and, decisively for C3c, **no citygate spike whatsoever** (max $5.61).
That last fact is *why* its measured tail is only 8 hours and why it passes C3c
on the small-count rule. It is not a modelling success; it is a quiet year.

The C3a-2025 residual is **Sep–Dec (81 % of the gap)** and sits in the
surplus/belly regime (the `0–20` and `20–40` actual bins carry +1.13 and +2.39
of the +2.90). Re-measured on the caiso-130 keeper, the caiso-121 attribution
**holds and sharpens**:

| window | CA λ | actual | resid | model WECC_DSW λ | **CA − DSW congestion** | WECC_PNW λ |
|---|---|---|---|---|---|---|
| 2025 all | 38.14 | 35.50 | +2.64 | 35.53 | **+2.61** | 18.12 |
| **2025 Sep–Dec** | 46.19 | 39.44 | **+6.75** | 42.33 | **+3.87 (57 %)** | 4.97 |

**57 % of the Sep–Dec 2025 over-price is DSW→CA corridor congestion rent** —
CA cannot reach its own import node — with the northern node stranded at $4.97
against a CA λ of $46.19. This is exactly caiso-121's LOAD-BEARING result
(59–101 % congestion share), reproduced on the current keeper without a solve.
**C3a-2025 already has a diagnosis and a selected family** (caiso-121:
corridor / export-path in surplus); it has never been armed, and arming it
remains a separate owner ask.

The size of the required move is small: **−$0.31/MWh**, i.e. −0.8 % of the
model level. Closing a quarter of the Sep–Dec congestion term (+$3.87 on 33 %
of the year's weight ≈ +$1.29 annually) is more than enough.

## §8 — the real coupling, and why the ranking is what it is

The two criteria are not one defect, but they are not independent either:
**they share one structural object — the WECC import node and the DSW→CA
corridor — and they pull it in opposite directions.**

- C3c needs the marginal import/CT rung **re-priced upward** so λ can leave the
  band (§5). The only mechanism on record that has ever achieved a CAISO C3c
  PASS did exactly that: **caiso-114** (`caiso_endogenous_wecc_node`, West gas
  priced at the measured intertie hub) **fixed C3c and C5a** — and **broke
  C3a** with an evening over-price of +18/+12/+4 $/MWh.
- C3a-2025 needs the corridor rent **removed**, i.e. CA λ pulled *down* toward
  its own (correctly-priced) import node (§7).

caiso-114's breakage is no longer unexplained: it is FINDING-caiso127 §1's
fixed point — an evening-scoped supply-side steepening that the interior
battery re-equalizes at a higher common level. And §3's envelope now prices it
exactly: caiso-114 spent $2–4/MWh of annual mean across all three years, where
2024 has $0.69 and 2025 has −$0.31. **caiso-114 is not re-armable as-is, and
its charter-era justification is gone anyway** — its primary goal was C5a,
which the v2.9 owner amendment removed from the scored rubric.

**Ranking, stated plainly:**

1. **C3a-2025 is the tractable one and should go first.** It needs −$0.31/MWh,
   it has a diagnosed cause (corridor congestion, 57 % of the Sep–Dec term), a
   family already selected at caiso-121, and it is the *load-bearing* criterion
   of the two. It is also the only one of the three failing ISO-years whose
   mechanism is a structural improvement in its own right.
2. **C3c-2023 is next, and is genuinely reachable** — +$3.67 of band headroom,
   a real measured driver (the January citygate blowout), and only 24 hours
   needed.
3. **C3c-2024 is the hard one**, and may not be reachable at all inside §3's
   $0.69 envelope with a trigger that is not fitted (§6: 17 hours available
   against 18 needed at the only non-arbitrary threshold tried).

## §9 — the ask (filed, NOT built)

Full design memo with derive-first gates D0–D4 and kill-before-solve criteria:
`docs/handoffs/caiso-131-c3c-c3a-ask-2026-07-27.md`.

Three items, in the ranking above. Nothing here is armed and no promotion is
requested; promotion remains a separate owner act (rule 1 `[R-STRUCT]`).

- **A1 (primary) — arm the caiso-121 corridor / export-path family in
  surplus.** The owner ask caiso-121 filed and never funded, now with §7's
  re-measurement on the current keeper and §3's envelope as its guard. Single
  delta, 3-year, rule-22 LOYO.
- **A2 — re-specify the CAISO LOLP overlay's reserve measure to the
  plant-level ONLINE (synchronized) basis**, the change PJM already made under
  its own honesty gate (§4). Zero new free parameters (the published VOLL/MCL/σ
  are unchanged); it corrects a measure the code itself documents as
  never-binding. **Stated honestly: §5 says this is necessary but almost
  certainly not sufficient** — it is a defensible structural correction whose
  C3c yield is expected to be small, and it must be judged as a structural
  correction (rule 1), not on whether the tail count moves.
- **A3 — a data intake ask, not a mechanism: the SoCalGas OFO declaration
  record.** §6 shows the 2023/2024 tail has a real, physical, forward-
  reproducible driver (gas deliverability) that the repo cannot currently
  express because it holds citygate *prices* but no *event* record. Without it
  the only available trigger is a fitted price threshold, which rules 13/24
  forbid. This is the one intake that could make C3c-2024 reachable.
- **A4 — the honest fallback: ledger C3c.** If A2/A3 do not land, CAISO's C3c
  has the same anatomy MISO and NEISO already ledgered as an ACCEPTED
  MEASURED-INPUT LIMITATION with a frontier designation, and CAISO's evidence
  is stronger than either (§4's 12–13 GW minimum headroom, §5's 12.8 GW band,
  §6's RT-only 2025 formations). CAISO carries **0** ledgered caveats against a
  budget of 3. This is an owner call and is filed as such — **it is not
  proposed as a substitute for A1**, which is a real defect with a real fix.

## §10 — DO-NOT-REDO (new, binding)

- **Re-testing the "one defect / belly-to-tail redistribution" hypothesis.**
  §2 refutes it three independent ways (different years, different months,
  magnitudes 3–6× apart). The compression is a shared symptom, not a shared
  mechanism.
- **Treating C3c as a three-year failure, or C3a as a multi-year one.** §1:
  C3c-2025 PASSES on the rubric's `TAIL_SMALL_COUNT` rule and C3a fails 2025
  only. Any candidate scoped to "fix the tail in all years" is mis-scoped, and
  a candidate that lifts 2025 makes the only C3a failure worse.
- **Any offer-curve, offer-rung or heat-rate work aimed at C3c.** §4: the stack
  already carries $687–$1,632 rungs and 108–9,570 MW above $200 in the tail
  hours. The rungs are not the constraint.
- **Any quantity-side derate / availability / deliverability mechanism aimed at
  reaching λ > $200.** §5: the band is 12.6–12.8 GW, 52 % of the available gas
  fleet, spread across three gas classes and imports. Scale-invariant, the
  caiso-129 §3(a) form.
- **Re-arming `caiso_endogenous_wecc_node` (caiso-114) as a C3c fix.** §8: it
  spends $2–4/MWh of annual mean against a $0.69 (2024) / −$0.31 (2025)
  envelope, its C3a breakage is now identified in advance as the caiso-127 §1
  fixed point, and its original C5a justification was removed from the rubric
  by v2.9.
- **Deriving a citygate price threshold that makes C3c-2024 clear.** §6: the
  only non-arbitrary threshold tried yields 17 hours against 18 needed;
  choosing a threshold so 2024 clears is a fitted value (rules 13 / 24). The
  trigger must come from the OFO event record (A3) or not at all.
- **"Fixing" C3a-2025 by changing the extract basis**, including the
  +$0.77/+$0.48/+$0.81 weight-basis term §2 reports. The basis is frozen
  (caiso-123 attributed extract; neiso-66 freeze ACTIVE) and C3a-2025 is a
  GUARD, never a tuning target.
- **Re-measuring any of:** the per-year C3a margins or C3c band requirements
  (§1); the regime/month decomposition (§2); the dispatchable-headroom surface
  or the offer-stack top (§4); the (λ, $200] band (§5); the tail hours' timing,
  load, ramp or gas percentiles (§6); the Sep–Dec 2025 corridor-congestion
  split (§7). The committed instrument carries all of them and needs no solve.

Carried forward unchanged: everything in FINDING-caiso130 §7, FINDING-caiso129
§6, FINDING-caiso127 §7 and FINDING-caiso128's DO-NOT-REDO. Notably still
binding: the allocation-floor family is CLOSED against the storage pin; the
whole AS-award family is CLOSED; the CT offer-heat-rate lane is CLOSED; an
evening-scoped supply-side repricing may never be filed as a **stand-alone**
first delta; S2 (the DA/RT two-settlement separation) must be chartered
separately and was **not** opened here.

Next number: caiso-132.
