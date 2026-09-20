# RESULT — nyiso-243: the chartered intake landed, its kill test REFUSED it, and in refusing it FALSIFIED the availability hypothesis and identified an admissible successor

**Session** nyiso-243 (ORCHESTRATOR — rule 32 `[R-SHARD]` (a); **zero LP in this container, no shard launched**).
**Date** 2026-09-20. **Base** `origin/main` at `48151074`.
**Keeper** `2026-09-19-nyiso241-ct-committed-measured`, bundle `results/calibration/nyiso241_ctcommitted_span`, years {2022, 2023, 2024, 2025} — **UNCHANGED. Nothing armed, screened, solved, promoted or registered. No `ScenarioConfig` field moves.**
**PRECOMMIT** `docs/PRECOMMIT-nyiso243-outage-intake-kill-test-2026-09-20.md`, committed at `51620eef` **before any price-conditioned number below was computed**.
**Charter** `docs/RESULT-nyiso242-cc-winter-refused-and-the-intake-charter-2026-09-20.md` §2.5.

> ## HEADLINE
> 1. **THE INTAKE EXISTS.** NYISO MIS **P-27** masked generator bid data is now in the
>    repo — 2022–2025, 48/48 monthly archives, 172 MB, `scripts/data/fetch_nyiso_bid_data.py`.
>    It states **availability directly** (`Upper Oper Limit`), exactly as the charter required,
>    and it carries the resource's own **AS offers**, which separate "held as reserve, therefore
>    available" from "not available" — the confounder that refuted the CAMPD census.
> 2. **THE KILL TEST REFUSES IT, ON SIGN.** In the 70 winter missed hours of 2022 the NYISO
>    fleet offered **MORE** capacity than in ordinary winter hours — **+781 MW** (DAM) and
>    **+2,208 MW** (HAM) — and offered availability rises **monotonically with the day-ahead
>    price** (HAM ladder **−3,759 → −4,335 → −5,052 → −5,864 MW** across DA > $100/150/200/300;
>    negative = *more* offered). A cold-snap availability derate does the opposite. Refused at
>    the gate, no solve, per PRECOMMIT §3.2.
> 3. **THIS FALSIFIES THE AVAILABILITY HYPOTHESIS — it does not merely fail to confirm it.**
>    nyiso-233 and nyiso-242 reached "the tail is an availability object" **by elimination**.
>    A direct measurement now contradicts it: in those 70 hours the market itself declared
>    **32,709 MW** available and **still cleared at $383/MWh**. The **4,716 MW** the model holds
>    idle below the gate was idle in reality too. Leg 2 agrees — the model's believed-available
>    fleet exceeds the measured offer by only **118 MW = 2.5 %** of the object.
> 4. **THE SUCCESSOR IS IDENTIFIED, AND FOR THE FIRST TIME IT IS ADMISSIBLE.** The same corpus
>    carries the submitted 12-block offer curves. In those 70 hours NYISO's fleet offered
>    **4,986 MW above $300** (and 21,561 MW above $100) against **1,953 MW** in ordinary winter
>    hours, and the quantity rises monotonically with the DA price —
>    **3,833 → 4,561 → 9,328 → 10,183 MW**. The tail is an **offer-level** object, and the
>    offer level is now **measured** rather than fitted.
> 5. **`measured_offer_surface` NYISO `G` → `U`, on the refusal's OWN stated re-open condition.**
>    nyiso-115 refused it verbatim *"Re-openable only by a NEW NYISO offer-data source, which is
>    what 'new evidence' would mean for this cell under rule 28a."* That source now exists.
>    **Nothing is armed** — the cell moves to untested, not to keeper.
> 6. **NO SHARD, NO SOLVE, DELIBERATELY.** The gate failed, so rule 34
>    `[R-SHARD-PROMOTABLE]` forbids spending one; §6 states what a successor would need first.

---

## 1. THE SOURCE — and what the charter's own shortlist actually contained

The charter named NYISO's outage postings as *"the first thing to check"*. They were checked
first, and they are the wrong product:

| product | what it is | verdict |
|---|---|---|
| **P-54A / P-54B / P-54C** (`outSched`) | **Transmission-line** outages. The archive's rows are `FARRAGUT_345KV_5W`, `RAMAPO___345KV_35-4500-5`, `VERNON___138KV_9E` — line, bus and breaker facilities. | **no generators**; useless for this object |
| **P-14 / P-14B** *Outage Schedules* | same scheduler, current snapshot only | no archive |
| **P-15** *Generation Maintenance Report* | a genuine **fleet-wide forced-plus-planned outage MW** daily series — the right quantity | **31-day forward snapshot, no archive**; cannot reach 2022 |
| **P-27** *NYISO Bid Data* (`biddata_genbids`) | per masked generator × hour × market: `Upper Oper Limit`, `Emer Oper Limit`, `Fixed Min Gen MW`, the 12-block economic curve, self-commit blocks, **AS offers**, `On Dispatch` | **monthly archive back to 1999-11** — the intake |

P-27 is the one public NYISO product that states per-resource availability **and** keeps
history. Fetched 2022–2025: 48/48 archives, 172 MB, 332 masked gens and 182 masked bidders in
2022, ~390 k rows/month, two markets per file (**DAM** day-ahead; **HAM** hour-ahead/RTC,
resubmittable ~75 min out, so it carries a derate that appeared after the DAM close).

**The UTC convention is checked, not assumed** — the January file spans `01JAN:05:00 →
31JAN:04:00` and July `01JUL:04:00 → 01AUG:03:00`, which holds iff the stamps are UTC. Hours
are mapped onto the model's own calendar through the gate's own mapper
(`derive_actual_lmp._std_hour_index`, `_STD_TZ["NYISO"] = Etc/GMT+5`), so the join convention
is identical by construction rather than by reimplementation. 8,736 of 8,760 hours covered in
2022; 8,760 in 2025.

**One repo claim needs a precise correction, and only a precise one.** nyiso-115 recorded
*"There is no offer or bid artifact for NYISO anywhere under `data/raw/`"* and
`mechanism-testing-matrix.md` records *"NYISO publishes no submitted-curve equivalent"*. The
first is now false. The second is false **as written** but true in the sense that matters for
its original use: NYISO publishes submitted curves **masked**, with no crosswalk to a PTID, a
plant, a zone or a fuel. **CLAUDE.md's "NYISO publishes no 60-Day-DAM equivalent" therefore
stands as written** — what NYISO withholds is the *unit identity*, not the offer data — and the
nyiso-87 gas-bridge reconstruction it justifies is untouched. §5 says which cells this moves and
which it does not.

---

## 2. LEG 1 — THE KILL TEST. Refused on sign and on monotonicity.

The charter's bar: *"the derived derate must deepen with price … flat across price conditions =
refused at the gate."* It is not flat. It runs the other way.

Median MW of `Upper Oper Limit` offered, 2022, against a **within-season** ordinary baseline
(a shoulder-month maintenance trough is not a cold-snap signal):

| window | n | RT median | DA median | **DAM offered** | **HAM offered** |
|---|---:|---:|---:|---:|---:|
| ordinary winter | 1,080 | 46.1 | 56.8 | 31,928 | 22,474 |
| **missed winter** | **70** | **383.3** | 170.4 | **32,709** | **24,683** |
| ordinary summer | 1,104 | 59.5 | 62.1 | 31,854 | 23,074 |
| missed summer | 23 | 359.3 | 165.8 | 32,709 | 31,407 |
| DA > $100 | 1,550 | 120.3 | 128.5 | 32,375 | 25,086 |
| DA > $150 | 465 | 160.1 | 178.7 | 32,720 | 25,663 |
| DA > $200 | 114 | 176.1 | 236.9 | 32,662 | 26,380 |
| DA > $300 | 10 | 277.6 | 329.3 | 31,979 | 27,192 |

**Deficit against baseline (positive = LESS offered, the direction the object needs):**

| window | DAM | HAM |
|---|---:|---:|
| missed winter | **−781.2** | **−2,208.5** |
| missed summer | −855.7 | −8,332.6 |
| DA > $100 / 150 / 200 / 300 | −3,733 / −4,079 / −4,021 / −3,338 | **−3,759 / −4,335 / −5,052 / −5,864** |

Every entry is negative. The HAM ladder is monotone in the **wrong** direction: the higher the
day-ahead price, the **more** capacity the fleet declares. That is ordinary economics — units
offer in when it pays — and it is the exact opposite of the signature a cold-snap derate must
leave. **2025 replicates the refusal**: its DAM winter deficit (+1,134 MW) clears the magnitude
bar alone, but the ladder is non-monotone and HAM reads **−2,694 MW** with a ladder running
−2,970 → −9,906. The PRECOMMIT requires **both** conditions; both years FAIL.

---

## 3. LEG 2 — the magnitude leg, with its scope corrected in public

**The first cut of this leg was mis-scoped and the correction matters more than the number.**
P-27 `genbids` carries NYCA **internal generators** only — external transactions are a separate
product (`tranbids`) and demand-side resources are not bid generators at all. The keeper's fleet
arrays carry both: **7,110 MW** of `NYISO_external_*` import tranches and **1,170 MW** of
`NYISO_DR_*` in 2022. The DR rows are the dangerous half — SCR/EDRP is armed only in emergency
hours, so it switches on *exactly in the windows under study* and would have read as a model
"over-belief" the measured side never had the chance to state. Both are excluded below; the
all-in total is reported beside it so the adjustment is visible rather than implicit.

The statistic that decides is a **difference of differences** — (missed − ordinary) of
(believed − offered) — because any constant scope error cancels in it exactly:

| year · window | believed (internal) | DAM offered | **excess gap vs ordinary** | **as % of the 4,716 MW object** |
|---|---:|---:|---:|---:|
| **2022 winter** | 25,209 | 32,709 | **+118.2 MW** | **2.5 %** |
| 2022 summer | 30,027 | 32,709 | +4,373.4 | — |
| 2025 winter | 25,179 | 29,781 | +2,505.2 | 53.1 % |
| 2025 summer | 28,837 | 32,074 | +1,913.9 | — |

**2022's winter cluster — the 70 hours holding 70 % of the object — shows 118 MW.** The model is
not over-believing availability there; it believes very nearly exactly what the market declared.

**The 2025 winter +2,505 MW does not rescue the intake, and here is why, stated rather than
waved away.** (a) The gate is Leg 1, and Leg 1 fails in 2025 too. (b) The statistic is
contaminated by the model's own **diurnal availability shape** — CHP duty curves and hydro
shaping give the believed series several GW of intra-day swing while the measured DAM series is
near-flat at ~32 GW — which is visible as the same statistic reading **+4,373 MW in 2022 summer**,
a window where believed availability *rises* 5.2 GW in the missed hours. (c) **HAM reads the
opposite sign in every window of both years.** A statistic that flips sign with the market you
read it from is not identifying anything. Reported at full magnitude because a successor would
otherwise rediscover it and act on it — which is exactly what nyiso-242 said of its own
4,575.8 MW.

**Leg 3, the reserve control (diagnostic, never a gate).** Explicit AS offers are
**866 MW** in the 2022 winter missed hours against **794 MW** in ordinary hours — too small to
be the explanation for anything, and *larger* in the extreme hours. This is the honest answer to
the predecessor's flat ~50 %: the fleet metered ~50 % of its ceiling in those hours because it
offered ~32.7 GW against a load near 20 GW. **The market was long, and priced at $383 anyway.**
(Caveat kept in view: headroom above dispatch is reserve-capable without a separate AS offer, so
this column understates reserve holding; it bounds the explicit part.)

---

## 4. WHAT THE MEASUREMENT POINTS AT INSTEAD — an offer-level object, measured

*(Descriptive. **Not a gate, and nothing is selected on it** — the session's gate was §2 and it
failed. Recorded because the kill test's own result points here: the capacity was there, so the
price was made by what it was offered at.)*

Median MW **offered above** each price, from the submitted 12-block curves, 2022 DAM:

| window | n | RT median | **> $100** | **> $300** | > $500 | > $1,000 |
|---|---:|---:|---:|---:|---:|---:|
| ordinary winter | 1,080 | 46.1 | 9,844 | 1,953 | 813 | 0.0 |
| **missed winter** | **70** | **383.3** | **21,561** | **4,986** | 1,235 | 0.0 |
| DA > $100 | 1,550 | 120.3 | 17,182 | 3,833 | 1,010 | 0.0 |
| DA > $150 | 465 | 160.1 | 21,255 | 4,561 | 993 | 0.0 |
| DA > $200 | 114 | 176.1 | 21,709 | **9,328** | 2,675 | 0.0 |
| DA > $300 | 10 | 277.6 | 22,472 | **10,183** | 3,626 | 473 |

Three things follow, and the third is the one that makes it admissible.

1. **The magnitude matches the object.** The model holds **4,716 MW idle below $300** in these
   hours; the market offered **4,986 MW above $300** in them. Those are the same object seen
   from the two sides.
2. **It is a conditioning, not a level shift.** 1,953 MW above $300 in ordinary winter hours
   against 4,986 MW in the missed ones — the fleet's offer curve *rises into* the event.
3. **It deepens monotonically with a DAY-AHEAD-observable driver** (3,833 → 4,561 → 9,328 →
   10,183 across the DA ladder). That is precisely the "offer distribution conditioned on a
   **forward-reproducible** tightness driver" that makes a measured offer surface rule-13
   `[R-MEASURED]` admissible, and it is the property the availability leg conspicuously lacked.
   The DA-anticipated / DA-surprise split corroborates it: **10,112 MW** above $300 in the 4
   anticipated hours against **3,787 MW** in the 97 surprises — DAM offers respond to
   anticipated tightness, as a forward-reproducible construction requires.

**2025's summer cluster is a DIFFERENT object and this does not reach it.** In its 31 missed
hours (RT median **$598**) the fleet offered only **740 MW** above $300 in DAM and **424 MW** in
HAM. There is no high offer stack there to find: that price was made by real-time shortage
pricing, not by an energy offer. nyiso-242 §4 was right that 2022-winter and 2025-summer need
different mechanisms; this says which is which, and **it leaves 2025 summer open** rather than
claiming a mechanism for it.

*Construction limit, stated: "offered above P" is `UOL − (largest cumulative MW priced ≤ P)`,
which counts as "above P" any headroom a curve does not reach. The reading of **0.0 MW above
$1,000** in DAM — NYISO's offer cap — is the check that this is not materially inflating the
numbers, since a unit with no usable curve would land there.*

---

## 5. MECHANISM MATRIX (rule 28 `[R-MECH-MATRIX]`)

**No mechanism was tested in this session** — what was tested is a data source's identification
power — so by the nyiso-239/240/242 precedent no verdict cell moves *on a test*. **One cell
moves anyway, and it moves because its own refusal said it should:**

* **`measured_offer_surface` NYISO `G` → `U`.** nyiso-115's refusal is quoted verbatim in §1;
  its stated re-open condition — a new NYISO offer-data source — is now met, and the refusal's
  factual premise (*"no offer or bid artifact for NYISO anywhere under `data/raw/`"*) is
  superseded. Leaving it `G` would tell a successor DO-NOT-REDO about the one cell this
  session's evidence re-opens. **`U`, not `K`: nothing is armed, nothing is screened.**
* **`cc_committed_offer_margin` NYISO stays `G`**, with its evidence annotated. Its refusal has
  two legs and only one is superseded: the corpus exists, but that mechanism needs a **per-class,
  per-unit** curve bottom, and masking withholds exactly that. The cell is honestly still
  refused.
* Nothing else moves. `unit_outage_short_windows` / `_gas` stay `I`, `temp_dependent_derate`
  stays `G`, `cc_winter_capability_basis` stays `G`, the ST_GAS blanket DO-NOT-REDO stands —
  this session corroborates all of them on a new instrument, which is not a verdict change.

---

## 6. WHAT A SUCCESSOR SHOULD DO, AND WHAT IT MUST NOT

**Do not re-run the availability question.** It is now refuted twice on two independent
instruments — CAMPD operation (nyiso-242) and P-27 declared availability (this session) — and
the second is the stronger. Add it to the DO-NOT-REDO set.

**The open object is `measured_offer_surface` for NYISO, and the honest blocker is masking.**
Before any solve, a successor owes a zero-LP design pass answering:

1. **What does the surface key on?** ERCOT's and CAISO's are net-load-binned and applied by
   class. NYISO's corpus has **no class, no fuel, no zone**. Either the surface is applied
   fleet-wide (crude, but identified), or a cohort attribution is derived from bid signatures
   (min-gen fraction, start-up cost, block count, UOL stability) — and **that attribution is
   itself a modelling choice that must be validated before it is used**, not assumed.
2. **Does it double-count?** `gas_offer_net_revenue_margin` is **`K` and armed** at NYISO, and
   it is already a measured markup over marginal cost. A measured offer surface on top of it is
   two mechanisms doing one job — rule 19 `[R-ONE-MECH]` requires enumerate-and-reconcile
   **before** anything is built, not after.
3. **Is it the authorized band-multiplier channel in disguise?** No — a distribution identified
   from NYISO's own submitted curves is a measured input under rule 13, not a tuned multiplier.
   But it becomes one the instant its level is chosen because the residual moved, and
   rule 1 `[R-STRUCT]` refuses that however well-motivated the physics.

**And the cost, stated up front as the charter asked of this session:** the prior is better than
it was — the object is sized, its magnitude matches a measured quantity, and the conditioning
driver is day-ahead-observable — but the masking limit is real and may yet make the surface
unbuildable at NYISO. A successor should still budget a zero-LP design and feasibility pass
before any shard.

---

## 7. ARTEFACTS AND GOVERNANCE

| artefact | what it is |
|---|---|
| `scripts/data/fetch_nyiso_bid_data.py` | the intake; re-fetches 2022–2025 in ~3 min |
| `data/raw/nyiso-bid-data/README.md` + `genbids/SHA256SUMS.txt` | the tracked record; payload gitignored (corpus-conversion class), recovery is re-fetch |
| `scripts/probes/nyiso243_offered_availability.py` → `_nyiso243_offered_availability.json` | **the kill test** (legs 1–3) |
| `scripts/probes/nyiso243_measured_offer_stack.py` → `_nyiso243_measured_offer_stack.json` | §4, descriptive |

**Governance.** Rule 32 `[R-SHARD]` (a): **zero LP**; the only model-side call is a fleet-only
rebuild, which enters no LP. Rules 33/34/35 have no subject — **no shard was launched**, and §2
is why launching one could not have backed a promotion. Rule 31 `[R-RETAIN]`: nothing deleted;
**no bundle was produced, so there is no promotion question to put to the owner.** Rule 15
`[R-DASHBOARD]`: no run produced, nothing to register; the keeper's dashboard entry is untouched.
Rules 21 / 24: zero free parameters, zero new literals, no `ScenarioConfig` field touched — the
PRECOMMIT's thresholds are this session's decision gate, not model parameters, and they were
fixed before the numbers. Rule 25 `[R-ISO-SCOPE]`: every number here is NYISO's own; no donor
ISO's parameter is carried, and the `U` in §5 is an *opening*, not a transfer. Rule 1
`[R-STRUCT]`: nothing was selected on a residual — the intake was refused on its own
pre-registered discriminator, and §4 is reported as a measurement with its own construction limit
rather than as a chosen mechanism. Rule 27 `[R-PUSH]`: no existing source file ≥300 lines was
rewritten; all four artefacts are new files.

**`tests/scoring` is untouched**: this session wrote no solve-path code — two new probe scripts,
one new fetch script, one new raw corpus, docs and one matrix shard line — so the unowned 22-failure
baseline on clean `main` is neither improved nor worsened by it, and this session adds zero.
