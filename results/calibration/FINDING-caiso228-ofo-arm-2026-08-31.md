# FINDING — caiso-228: the SoCalGas OFO gas-deliverability ARM **DIES AT GATE D1 WITH NO SOLVE** — pre-registered outcome 1. The physically-identified low-OFO derate is **≤998 MW** at its most generous reading against a **12.6–12.8 GW** band (3.2–7.9 %), and the kill is **size-independent**: the band's import limb (3,411 / 4,431 / 10,365 MW) is delivered across the WECC seam, so **no gas-side quantity mechanism of ANY magnitude — SoCalGas-scoped or not — can exhaust the band and lift λ past $200** in CAISO's measured tail hours. caiso-131 **A3 is ANSWERED, NEGATIVELY AND CONCLUSIVELY**. No `ScenarioConfig` field, no mechanism, no matrix cell minted, no LP run, keeper UNCHANGED (2026-08-31)

**Session:** caiso-228 · **Date:** 2026-08-31 · **Keeper at session:**
`2026-08-26-caiso-220-c1-crosswalk`, verified on disk against
`frontend/data/backcast/keepers/CAISO.json` (NOT-YET on C3a alone, +4.0 PASS /
+12.5 / +15.5 vs ±10 %; C3c the single ledgered caveat, budget 1 of 1;
C1 12/12 free 8/8; C2/C3b/C4/C6/C8 PASS) · **Solves run: NONE.**

**NUMBERING.** The binding pre-registration for this arm is
`results/calibration/PRECOMMIT-caiso227-ofo-arm-2026-08-31.md`. Its "227" label
is historical — caiso-227 was the C3a root-cause round
(`FINDING-caiso227-c3a-rootcause-ps-intake-2026-08-31.md`) — and **caiso-228 is
the session executing it**, funded by the owner dispatching the arm prompt (the
precommit was filed item 11, "pre-registered and unfunded, an owner call").
Nothing in the precommit's design was altered: the §2 trigger definition was
frozen before D0 was computed and is unchanged below.

---

## §1 — the verdict, in one table

| gate | pre-registered kill criterion (PRECOMMIT §4) | measured | verdict |
|---|---|---|---|
| **D0** | coverage of the measured tail by qualifying gas days, *measured but not used to choose* | **13/47 (27.7 %) · 22/35 (62.9 %) · 3/8 (37.5 %)** | reported; 2023's 13 h is **below** the 24 h C3c requirement |
| **D1** | derate identified from gas-system physics **not material** vs the 12.6–12.8 GW band ⇒ **stop, no solve** | **≤998 / ≤959 / ≤684 MW** = **7.9 % / 7.5 % / 3.2 %** of band | **KILL** |
| D2–D4, G1–G6 | — | **NOT REACHED** | the arm stopped at D1, as pre-registered |

**Pre-registered outcome 1** (PRECOMMIT §6): *"Dies at D1 — the
physically-identified derate cannot reach the 12.6–12.8 GW band. No solve. C3c
stays ledgered; caiso-131 A3 is answered negatively but conclusively, which is
worth more than an open ask."* That is exactly what happened, and it is the
reason the precommit named the outcome before the yield was known.

Artifacts (committed, reproducible from committed bytes in seconds, no solve):
`scripts/probes/caiso228_ofo_d0_coverage.py` → `_caiso228_d0_coverage.json`;
`scripts/probes/caiso228_ofo_d1_derate.py` → `_caiso228_d1_derate.json`.

## §2 — D0: coverage, measured with the trigger frozen

The PRECOMMIT §2 trigger — **any SoCalGas `side="low"` OFO gas day, every stage,
waived days included, SP15-scoped** — was fixed before this measurement and is
**unchanged by it** (§7 prohibition; caiso-226 §4(e)). The SoCalGas gas-day
offset is applied: gas day *D* owns operating hours [*D* 07:00, *D*+1 07:00)
Pacific, per the `gas-ofo-events` schema's `gas_day` description and PRECOMMIT
D4. The naive midnight-to-midnight mapping is computed alongside and differs by
1 h (2023) / 0 h (2024) / 1 h (2025) — small here, but the offset is applied
because it is the correct mapping, not because it moved a number.

| year | low OFOs | measured RT tail (h) | **on a qualifying gas day** | coverage | C3c hours required | qualifying tail days | trigger duty (share of year's hours) |
|---|---|---|---|---|---|---|---|
| 2023 | 43 | 47 | **13** | 27.7 % | **24** | 6 of 26 | 11.8 % (1,032 h) |
| 2024 | 34 | 35 | **22** | 62.9 % | **18** | 3 of 10 | 9.3 % (816 h) |
| 2025 | 25 | 8 | **3** | 37.5 % | 0 (already PASSES) | 2 of 7 | 6.8 % (599 h) |

Three things this says, none of which is a design input:

1. **2023's coverage is below its own requirement.** C3c-2023 needs ≥24 model
   hours above $200; only **13** of the 47 measured tail hours sit on a
   qualifying gas day at all. A mechanism confined to qualifying gas days and
   *faithful* — lifting the hours reality actually priced, not manufacturing new
   ones — cannot produce a compliant 2023 tail. (The rubric's C3c is a *count*,
   so a mechanism could in principle reach 24 by lifting 11 hours reality left
   cheap out of the 1,032 qualifying-gas-day hours. That is an invented tail
   under rule 1 `[R-STRUCT]`, it spends C3a-2023 band headroom on hours with no
   measured event, and it is not proposed here.)
2. **The January-2023 cluster largely PRE-DATES the OFO record.** 14 of 2023's
   47 tail hours fall on Jan 1–3, and only Jan 3 carries a low OFO; the
   15-day January-2023 low-OFO month (Jan 3–31) covers the *later*, thinner
   tail days. The blowout and the declarations are adjacent, not coincident.
3. **2024's coverage is carried by one day.** `2024-01-15` alone is 19 of the
   35 tail hours and is a qualifying gas day — which is why 2024 reads 63 %
   while 2023 reads 28 %. A trigger whose yield rests on a single gas day is
   not a discriminating instrument, and the PRECOMMIT forbade rescuing it by
   selecting a stage/tolerance/waived cut (§2, §7).

**The G2 exposure caiso-226 §5 predicted is confirmed and is not hypothetical:**
the frozen trigger fires on **599 hours of 2025** — the year whose C3c already
PASSES and whose C3a (+15.5 %) is CAISO's sole open gate. Had the arm survived
D1, G2 would have been a live, hard gate with no admissible escape (a 2025
exclusion is a year-keyed fitted term, PRECOMMIT §5/§7).

## §3 — D1: the physically-identified derate — the KILL

### 3.1 What a low OFO actually does, from the tariff mechanic alone

A SoCalGas low OFO constrains each shipper's **daily imbalance**: on a declared
gas day, deliveries into the system may fall short of burn by no more than the
published tolerance band (`tolerance_pct`, signed negative on the low side)
before a noncompliance charge attaches. **It does not confiscate gas already
nominated and delivered.** The quantity it removes from the generation fleet is
the fleet's *unhedged incremental burn* — the energy it could otherwise have
drawn out of system linepack above its nominations — and that quantity is
exactly `|tolerance_pct| × (measured daily burn)`. This is the "declared
tolerance applied to measured gas burn" route PRECOMMIT §4 D1 names, and it has
**zero free parameters**: the tolerance is published per gas day, the burn is
measured per unit-hour, and the conversion uses the fleet's own measured heat
rate that day.

**A structural observation that is not a workaround.** The instrument's own
mechanics are **price-side** — a *charge* per MMBtu of out-of-tolerance
imbalance, not a physical block on MW. Representing it as a quantity derate is
already a modelling choice made in the arm's favour; representing it as the
price it actually is would be an adder on OFO days, which PRECOMMIT §1 excludes
by name ("No adder, uplift or scarcity price applied on OFO days. A price-side
response is what the LP must *produce*, never what it is handed"). Both readings
are closed, and the quantity reading is the more generous of the two.

### 3.2 The measurement

Measured inputs, committed bytes only: `data/clean/gas-ofo-events/CAISO`
(caiso-226 intake) for the qualifying days and each day's published tolerance;
`data/raw/campd-unit-level/CA_<year>.parquet` for measured hourly heat input and
gross load; `data/raw/reference/caiso-plant-hub-membership.csv` (the caiso-217
measured crosswalk that is the caiso-220 keeper's own input) to scope the fleet
to `TH_SP15`. `TH_NP15` / `TH_ZP26` are PG&E-served and outside a SoCalGas OFO
entirely.

| year | qualifying days with CAMPD burn | SP15 gas fleet measured HR | SP15 share of CAISO gas burn | derate MW, **day-avg** (min/med/max) | derate MW, **whole allowance in a 6 h block** (min/med/max) |
|---|---|---|---|---|---|
| 2023 | 43 | 8.008 | 44.1 % | 6.3 / 52.5 / **249.4** | 25.2 / 210.1 / **997.5** |
| 2024 | 34 | 7.321 | 47.9 % | 4.6 / 142.2 / **239.7** | 18.2 / 568.7 / **958.7** |
| 2025 | 25 | 7.385 | 39.0 % | 10.1 / 69.3 / **171.1** | 40.3 / 277.1 / **684.2** |

The 6-hour-block column is deliberately the **most arm-favourable** number
available: it assumes the whole fleet's entire daily imbalance allowance is
taken inside the tail block, and it aggregates the tolerance across all
shippers when the tariff applies it shipper-by-shipper. Even so:

**max derate ÷ band = 7.9 % (2023) · 7.5 % (2024) · 3.2 % (2025).**

Against caiso-131 §5's committed band (12,600 / 12,780 / 21,212 MW — **quoted,
not re-measured**, per §10 DO-NOT-REDO), the physically-identified derate is
**not material**. That is D1's kill criterion, met.

### 3.3 The kill is SIZE-INDEPENDENT — the sharper result

D1's arithmetic would still leave a re-scaled successor arguable. It does not,
because the band's composition closes the family outright.

For λ to exceed $200 in a measured tail hour, **every** MW offered between λ and
$200 must leave the stack. caiso-131 §5's band decomposes as:

| year | gas limbs (cc+ct+st) | **import + hydro — surviving ANY gas-side derate** | band total |
|---|---|---|---|
| 2023 | 9,189 MW | **3,411 MW** | 12,600 |
| 2024 | 8,349 MW | **4,431 MW** | 12,780 |
| 2025 | 10,847 MW | **10,365 MW** | 21,212 |

Imports are delivered across the WECC seam and are burned on no California LDC
system; the hydro limb is 0. So even the physically impossible extreme —
removing **100 % of the band's gas**, PG&E-served NP15/ZP26 gas included, which
no SoCalGas instrument can touch — leaves 3.4 / 4.4 / 10.4 GW of offers still
priced at or under $200. **λ lands back on an import tranche and the tail does
not form.** The conclusion holds at every magnitude, so it is not a statement
about this candidate's size:

> **No gas-side quantity mechanism can reach C3c for CAISO.** This generalises
> caiso-131 §5 from *"the band is 12.8 GW, too deep for a derate"* to *"the
> band's residual limb is not gas at all"*, and it is the caiso-129 §3(a)
> scale-invariance form at limb rather than magnitude grain.

The SP15-scoped ceiling is tighter still: at the measured SP15 share of CAISO
gas burn, the whole SoCalGas-served gas contribution to the band is
**4,048 / 3,997 / 4,228 MW** — 32 % / 31 % / 20 % of it.

### 3.4 The LOLP-overlay path is closed too

The remaining route to a tail is the armed CAISO scarcity overlay
(`caiso_scarcity_pricing=True`; VOLL $2,000, MCL 1,400 MW, σ 2,500 MW), whose
adder is `LOLP(R) × (VOLL − λ)`. Applying the derate to caiso-131 §4's committed
minimum-headroom hour:

| year | min headroom (caiso-131 §4) | after the max derate | σ above MCL | after the **full SP15 gas ceiling** | σ above MCL |
|---|---|---|---|---|---|
| 2023 | 12,173 MW | 11,175 MW | **3.91 σ** | 8,125 MW | **2.69 σ** |
| 2024 | 12,689 | 11,730 | **4.13 σ** | 8,692 | **2.92 σ** |
| 2025 | 13,137 | 12,453 | **4.42 σ** | 8,909 | **3.00 σ** |

At 2.7–4.4 σ the LOLP adder is worth single dollars per MWh against the $88–150
the tail needs — **and this is the year's single tightest hour, not a tail
hour**: caiso-131 §6 measures 22.6 / 27.5 GW of headroom remaining in the tail
hours themselves. The overlay's mis-specified reserve *measure* (caiso-131 §4,
the PJM honesty-gate class defect) remains a real, separately-named defect;
this table shows that repairing it is **necessary but nowhere near sufficient**,
and that an OFO derate does not move it.

## §4 — what was NOT done, and why that is the deliverable

Per PRECOMMIT §4 the gates are kills, not hurdles, and the arm stopped at the
first one it failed:

- **No `ScenarioConfig` field was added.** The mechanism was never built.
- **No LP solve was run**, in any year. Rules 12/16 were never reached.
- **No dashboard registration.** Rule 15 attaches to a completed *run*; there is
  no run. The deliverable is this FINDING plus the two committed probes, which
  is what a kill-before-solve outcome produces (the ercot-177 / ercot-175
  precedent: a lever refused before the precommit stage files its finding and
  nothing else, so that a missing bundle is not misread as a skipped rule-15
  registration).
- **No matrix cell was minted** (rule 26). Duty (c) attaches to a PR adding a
  solve-affecting `ScenarioConfig` field — none was added, so no base row and no
  six-shard cell line is owed, and minting a row for a mechanism that does not
  exist would put a phantom field in every ISO's column. Duty (b) attaches to a
  session that *tests* a mechanism; this session adjudicated a **design** ex
  ante and never built one. The record instead lands as a CAISO shard stamp
  block and a §5.2 lane note, both citing this FINDING, so the DO-NOT-REDO is
  discoverable from the matrix without a fabricated cell.
- **Keeper, keeper shards, `calibration-complete.json`, `holdout-freeze.json`
  and every other ISO's files: UNTOUCHED.** All reads were 2023–2025; the
  holdout spend freeze was never approached. CAISO holds no `complete` and no
  `final` marker and this session neither requests nor implies one.
- **C3c remains the keeper's single ledgered caveat**, exactly as PRECOMMIT §6
  states for all four outcomes. Under rubric v3.3 a lone ledgered C3c does not
  downgrade a determination, so **nothing here was ever a gate need** and the
  negative result costs the keeper nothing. CAISO stays **NOT-YET on C3a alone**.

## §5 — what remains of caiso-131 A3, honestly stated

A3 asked for the OFO event record so a C3c trigger could come *from the source
event* rather than from a citygate threshold fitted to the residual. That ask is
now fully discharged and fully answered:

- **caiso-226 landed the record** and adjudicated it rule-13 admissible.
- **caiso-228 (this session) finds the record cannot carry a C3c mechanism** —
  not because the record is poor, but because the *object* it would drive is
  the wrong shape for the residual. The trigger is real; the lever it would pull
  is 3–8 % of a band whose surviving limb is not gas.

**Gas deliverability is still real market structure the LP does not represent,
and this finding does not claim otherwise.** What it establishes is that
representing it as a *quantity* limit on the SoCalGas-served fleet cannot
produce CAISO's measured price tail, at any magnitude. Under rule 1
`[R-STRUCT]` a faithful mechanism would stay in even with no residual movement
— but a mechanism whose only claimed purpose was C3c, which cannot reach C3c,
and which would put a 599-hour 2025 duty cycle against the sole open C3a gate,
has no structural case left to make on this evidence. It is not built.

The channels caiso-131 §5 leaves are unchanged and neither is opened here: a
**price** adder stacked on λ (the G-20a settlement-price construction —
CAISO's instance is the LOLP overlay whose reserve *measure* is mis-specified,
§3.4), or **re-pricing the marginal rung** (caiso-114's mechanism, excluded for
2024/2025 by caiso-131 §3's envelope and re-armament forbidden by §10).

## §6 — DO-NOT-REDO (new, binding)

1. **Never re-run this arm.** The SoCalGas low-OFO gas-deliverability mechanism
   is **ADJUDICATED CLOSED for CAISO** on the §3.3 size-independent ground. A
   successor differing only in derate magnitude, stage/tolerance cut, waived
   handling, run-length or gas-day windowing is refuted in advance: none of
   those dials changes which *limbs* of the band survive a gas-side derate.
2. **Never re-derive D0 or D1.** Both probes reproduce from committed bytes in
   seconds; the JSONs carry the per-day tolerance, burn, heat rate and derate.
   Re-run the probes, do not re-measure the inputs.
3. **Never re-measure the caiso-131 §5 band, the §4 headroom surface or the
   overlay parameters** — quoted here, committed there, and carried by
   caiso-131 §10's own DO-NOT-REDO.
4. **The "no gas-side quantity mechanism reaches C3c" result is CAISO-scoped
   (rule 25 `[R-ISO-SCOPE]`).** It rests on CAISO's own band composition — a
   large import limb inside (λ, $200]. It transfers to no other ISO, and a
   northeast gas-deliverability lever (NEISO/NYISO pipeline-constraint
   analogues, whose band composition is different) is untouched by it and
   enters its own ISO as `U`.
5. **The `gas-ofo-events` datatype stays intaken, admissible and UNCONSUMED.**
   Nothing here retracts caiso-226 §4. It remains available to any *forecast*
   or non-C3c use that can state its own forward analogue (caiso-226 §4(d));
   what is closed is the C3c backcast derate, not the data.
6. **Never argue this arm was a gate need.** C3c is ledgerable and a lone C3c
   run reads `CALIBRATED` under rubric v3.3. This was root-cause work, and its
   result is a closed question, not a lost opportunity.

Carried forward unchanged and in full: caiso-131 §10, caiso-226 §6, caiso-227
§K, caiso-222 §9 Q1 terminal rest, the caiso-225 watch sweep's dated trigger
(Order-881 effective ≤ 2026-12-01 or the next DMM print — **not re-run here**),
and every `R`/`I`/`G` cell in
`docs/codebase-site/data/mechanism-matrix/CAISO.js`.

Next number: caiso-229.
