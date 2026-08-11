# DECISION CARD — the ERCOT open-ruling backlog, assembled at ercot-188

**For the owner sitting. Assembled 2026-08-11 at HEAD `ce4d05e` (origin/main) by
session ercot-188. ALL SEVEN CARDS ARE NOW SIGNED — see RESOLUTIONS at the foot.**
The card bodies below are preserved AS PUT TO THE OWNER, unedited by the outcome,
so the recommendation each decision was taken against stays legible. No lever proposed, no
`ScenarioConfig` field added, no derive run, no LP solved, no run registered, no
matrix cell minted by this card. Every figure is read off **committed artifacts**
— no re-derivation, no replay, no new measurement.

**Scope:** ERCOT (rule 25 `[R-ISO-SCOPE]`). One non-ERCOT item is carried in §7
**only because it is explicitly marked un-acted**, and it is that ISO's lane to
own. ERCOT holds **no `complete` and no `final` marker**, so every year
referenced is inside {2023, 2024, 2025} (rule 22).

**Keeper at assembly: `2026-08-09-ercot185-shaped-partial`** — determination
**NOT-YET**, fail set **{C3a-2023, C3b-2023}**. *Superseded by card E's signature:
the keeper is now `2026-08-11-run188-arm-topfine-cliff`, same determination and
same fail set.*

**Why now.** ercot-188 closed the last offer-side face of C3a-2023 (§6), which
moves the program's critical path onto a lane that is **blocked behind three of
these rulings**. The backlog stopped being bookkeeping and became the thing in
the way.

---

## 0. THE BOARD

| card | decision | blocking? | recommendation |
|---|---|---|---|
| **A** | The DAM-deriver / crosswalk lane — rulings **#8, #9, #10** | **YES — blocks ercot-189** | **Authorize as ONE lane, #9 first** |
| **B** | Item 13 — the two COAL limbs' 2023 application | no | Re-adjudicate before any arm |
| **C** | ercot-165 — the daytime curtailment mode successor | no | **Decline the DOF; re-point the object** |
| **D** | RTC+B adapter authorization (27 quarantined parts) | soft — caps future corpus work | **Authorize, scoped to a read adapter** |
| **E** | ercot-188 — promote SCHEME R1 on structural fidelity? | no | **DO NOT PROMOTE** — *owner signed **E2, PROMOTE**; see RESOLUTIONS* |
| **F** | Nothing schedules the tier the ERCOT golden lives in | no | Schedule it |
| **G** | Rulings #2, #3, #5 — **INVESTIGATED 2026-08-11** | no | **#2 spent · #3 delete · #5 mis-titled, re-open the real object** |

---

## A. THE DAM-DERIVER / CROSSWALK LANE — rulings #8, #9, #10

> **THE QUESTION: do you authorize a re-derive of the DAM availability family,
> knowing it re-gates every armed DAM keeper?**

Three rulings, one lane, one repair. They were opened separately (ERCOT-148 §6.2;
ercot-149 diagnosis §6.1–6.2 and §6.3) and have been carried as open ever since;
the current matrix header still lists **#9 and #10** as ERCOT's open rulings.

| # | The defect | Origin |
|---|---|---|
| **#8** | The DAM deriver's **rating basis for all-year-OUT sites** | ERCOT-148 §6.2 |
| **#9** | The deriver's **`_site()` cross-train collapse** takes the **MAX** HSL among ON rows, **not the SUM** — understating ON at every multi-train site and inflating the OFF increment. Plus the **gas crosswalk's partial site acceptance** | ercot-149 §6.1–6.2 |
| **#10** | The pin's **remove-direction over-removal** at partial-coverage plants | ercot-149 §6.3 |

**The measured size of #9.** A CC train submits one DAM row per configuration
(**4.3 configs/train**), and every non-operating configuration of a *running*
train carries `Resource Status = OFF` at full HSL. Name-grain OFF CC therefore
reads **48.9 GW** against **14.1 GW** train-collapsed — and the `_site()` collapse
that was supposed to fix this takes the max rather than the sum, so it *mitigated
but did not fix* the inflation.

**The measured size of #10.** V H Braunig 2025: VHB3 down pins the **whole plant**
to ~0.075 while VHB1/2's status is unmeasured by the accepted subset. Sized small
on the keeper — VHB model 0.31 vs CAMPD 4.23 TWh in 2025 — **and the record is
explicit that most of that gap is offer-economics under-dispatch, not the pin.**
Do not authorize #10 expecting a residual move.

### A.1 Why this is now on the critical path

ercot-188 closed the **resolution** face of C3a-2023, joining level, grain and
position (§6). The only named, unclosed ERCOT object left in the record is the
**CC headroom/capability** gap handed forward UNCHARTERED at ERCOT-163:

> model **3.07 GW** undispatched vs the market's **0.35 GW** (~2.7 GW), with model
> CC dispatch right to **+0.30 GW** — a rule-14 fleet-scope question on the
> existing `ercot_thermal_dam_availability_*` channel, **never a new commitment
> gate and never an aggregate cap** (ERCOT-159 killed the aggregate form on four
> gates).

Identifying it needs a **per-unit SCED-train ↔ model-unit crosswalk**, and **#9 is
the reason that crosswalk cannot be built today**: any per-unit capability number
computed on the MAX-collapse is built on a known-wrong aggregation.

### A.2 The cost, stated before you decide rather than after

* The re-derive **re-derives all three grains** and **re-gates every armed DAM
  keeper**.
* Under rule 23 `[R-FROZEN-DERIVE]` it **also re-triggers the zone-anchor table**
  (ercot-150). That is a second, non-obvious blast radius and it is the reason
  this has sat open.
* It is a derive/crosswalk lane, so it is Opus/Fable scope (rule 27) and needs its
  own precommit.

### A.3 Options

* **(A1) AUTHORIZE AS ONE LANE, #9 FIRST — recommended.** #9 is the aggregation
  defect the other two sit on top of; repairing it separately and then re-opening
  for #8/#10 pays the re-gate cost twice. Sequence: #9 → #8 → #10, one precommit,
  one re-derive, one re-gate sweep.
* **(A2) AUTHORIZE #9 ONLY**, defer #8/#10. Cheaper to reason about, but you pay
  the re-gate cost again later — and #8 is in the same deriver.
* **(A3) REFUSE.** Then say so explicitly, because it **closes ercot-189's only
  named object**, and the honest consequence is that ERCOT has no chartered lane
  left for C3a-2023 within this model class. That is a legitimate answer — but it
  should be taken deliberately, not by leaving the ruling open.

**Recommendation: (A1).** Not because it will move the residual — nothing in the
record predicts that — but because the alternative is identifying a capability
object on an aggregation the record already calls wrong, which rule 14
`[R-ACCURATE]` forbids.

---

## B. ITEM 13 — the two COAL limbs' 2023 application

> **THE QUESTION: how should the two COAL limbs be applied in 2023, given the
> lane's own REFUTED branch was never reached?**

**The record is explicit that no arm may be built without a fresh adjudication:**
the pre-registered REFUTED branch **was not reached** — the licensing gate fired
first — so **no candidate arm is named**.

**What was measured.** The two most common submitted TOP steps in the
delivery-2023 COAL corpus are **$78.00** (21,677 intervals) and **$75.01**
(17,869); **$34.82**, the 2024/25 level, is a distant tenth. That gives
level₂₀₂₃ **71.3378**, i.e. **14.4× outside its ±$2.5062 band** — the armed
constant is roughly **half** the measured 2023 top. A 1.7 pp coverage shortfall
cannot produce a 2× level shift, and the direction corroborates at fleet scale,
on an independent instrument, what ercot-168 already measured and promoted (Oak
Grove's overnight top $60.26/$61.46).

**Also filed, not acted on:** the three margin constants have **no dedicated
DOF-ledger entries** in the keeper attestation. Zero fitted scalars, so this is
bookkeeping rather than hidden freedom — but the next ERCOT keeper-promoting
session should add them and carry limb B's verification into that ledger.

**Options:** (B1) re-adjudicate under a fresh precommit before any arm —
recommended; (B2) close the item as refused; (B3) leave open (status quo, which
silently blocks anyone who reaches for limb C).

---

## C. ercot-165 — the daytime curtailment mode

> **THE QUESTION: do you authorize a per-family weight — a DOF the ercot-164
> charter explicitly fences — or re-point the object?**

The WP-B v2 keeper (`ercot_wtx_curtail_unpooled`, promoted at ercot-165) **MISSED
its charter's SHAPE target**, and that limit is carried openly in the attestation
and the keeper's `market_story` as an **OPEN ROOT-CAUSE ISSUE**. The named
successor is the daytime curtailment mode, and it needs **either** a per-family
weight **or** a different object.

**The tension you are resolving:** a per-family weight is exactly the kind of free
parameter the ercot-164 charter fenced. Authorizing it trades a rule-23
`[R-DOF]` boundary for a shape improvement.

**Options:** **(C1) DECLINE the DOF and re-point the object — recommended**, on
the same reasoning that has held across this lane: a fitted weight that closes a
shape residual is the thing rule 23 exists to stop. (C2) Authorize the weight
under an explicit DOF-ledger entry and a pre-registered identification source.
(C3) Close the successor entirely and let the shape miss stand as a declared
limitation (it already is one).

---

## D. RTC+B ADAPTER AUTHORIZATION

> **THE QUESTION: do you authorize a read adapter for ERCOT's RTC+B-era SCED
> format?**

**27 parts** (deliveries **2025-12-05..31**, **8.66M rows**) carry the RTC+B-era
Gen member: **`HASL`/`LASL` REMOVED**, the netout trailing-space spelling dropped,
AS responsibilities → `AS Awards/Capability`, and rows ~3× as the disclosure scope
widens. **`HASL` is a required read column of every corpus consumer**, so these
**crash the derives** — the exact ercot-95/97 defect class.

They are quarantined at `data/raw/ercot/SCED/rtcb-format-2026/`, invisible to the
consumers' non-recursive globs, **awaiting an owner-authorized adapter**. Nothing
is silently mis-reading them today; the quarantine is working. What it costs is
**forward** corpus coverage: every future SCED-corpus lane stops at 2025-12-04.

**Options:** **(D1) AUTHORIZE, scoped to a READ ADAPTER — recommended** (map the
RTC+B member onto the existing schema; no mechanism, no re-derive of frozen
artifacts, no keeper movement). (D2) Defer until a lane actually needs
post-2025-12-04 data. (D3) Refuse and accept the corpus ends there.

---

## E. ercot-188 — promote SCHEME R1 on structural fidelity?

> **THE QUESTION: your standing standard is "structural integrity improves but
> gates regress may still be a keeper." Does it apply here?**

**RECOMMENDATION: DO NOT PROMOTE.** ercot-188 did not promote and does not assume
your standard.

**What it delivers.** The build works exactly as specified: the supply-curve top
goes from a 6-block equal-width approximation carrying **33** econ rows in the
measured top decile to **382 rows above ladder `rel` 0.9**, quoting up to **145×
delivered gas**, MW conserved to 1.5e-11. Seam proof ALL_ASSERTIONS_PASS,
including the cross-ISO assertion on all five other ISOs with the gate armed.
Seven of eight gates PASS, including **G-SHED** (4/2/0 → 4/2/0).

**Why the standard nonetheless does not carry it.**

1. **The added rows are measured never to be cleared on.** C3a-2023 moves
   **−$0.21/MWh** (43.44 → 43.23 vs actual 64.32). This is representational
   fidelity the LP demonstrably does not read.
2. **The price is a structural REGRESSION, not a gate regression.** It is the
   first offer-side ERCOT mechanism since ERCOT-86 that does not ride the P1-only
   `mc_bid_adjust` seam. It **permanently forfeits the offer-surface family's P0
   bit-identity proof** — a verification property **every future offer-side
   mechanism inherits the loss of**. Measured: 73 of 132 committed rows
   (12,474 MW) carry a different P0 commitment pattern.
3. **Both precedents differ in exactly this respect.** Item 23 was promoted INERT
   but cost **zero** LP columns and kept a **bit-identical P0**. ercot-185 was
   promoted over a rejected verdict, but it **deleted a measurably WRONG
   mechanism** (a multi-week median imposed as an hourly ceiling) and **improved**
   the residual. ercot-188 fixes nothing wrong — equal-width slicing is *coarse*,
   not *incorrect* — costs **×1.295** columns, and moves the residual the wrong
   way.

**If you promote anyway**, the record must carry the forfeited P0 proof as a named
permanent limitation in the keeper note (it is already written that way in the
FINDING §6 and the matrix cell), and the mechanical verdict stays
REJECTED-AS-ARMED, unrewritten.

**Options:** **(E1) DO NOT PROMOTE — recommended**; (E2) promote on the standing
structural standard with the limitation carried; (E3) revert the field entirely
(**not recommended** — it is default-off, seam-proven inert at default, and the
measurement is worth keeping arm-able).

---

## F. NOTHING SCHEDULES THE TIER THE ERCOT GOLDEN LIVES IN

> **THE QUESTION: which tier owns `test_fleet_arrays_golden`, and who runs it?**

The ERCOT fleet-arrays golden went red on **2026-07-26** and was carried as
incidental noise by **seven** later sessions (caiso-143, ffr-1b, ffr-3d, ffr-3u,
ffr-5c, f2-45u, miso-148) **because nothing schedules the tier it lives in** —
CI's own `-m "not slow and not integration and not fulldata"` deselects it, and a
runner has neither `data/raw` nor `data/clean`.

ercot-187 attributed and regenerated the golden, so it is green now. **The
scheduling gap is not fixed.** A golden nothing schedules is not a guard.

**Options:** (F1) schedule the data-provisioned tier on a cadence — recommended,
but note CLAUDE.md's GitHub-Actions rule: this is durable infrastructure, not a
per-task workflow, and cron spend needs your explicit sign-off; (F2) require each
ERCOT session to run it (weakest — it is what already failed seven times);
(F3) accept it as unguarded and say so.

---

## G. RULINGS #2, #3, #5 — INVESTIGATED, 2026-08-11

**Owner asked ercot-188 to explore rather than leave these unverified. Done —
all three now have an evidenced answer.** Nothing below is a decision; each still
needs your signature, but none is a guess any more.

### G.2 — Ruling #2: per-gate dispositions of the attributed gates · **SPENT**

The ruling asked for a disposition on each attributed gate, named at ercot-147 as
**C3a / C3b / C3c tail** and **C7-2023 non-offer-surface**. Every one has since
been dispositioned by a named, signed decision — the ruling was overtaken and
nobody closed the register entry:

| gate | disposition | where |
|---|---|---|
| **C7-2023** (lignite cv-leg) | **CLOSED** — cv 0.331 → 1.193, r 0.976, on the year's own measured curves | ercot-168 promotion |
| **C3c** ×3 years | **LEDGERED** `ACCEPTED MODEL-CLASS LIMITATION`, then generalized | owner decision 2026-08-05; C3c standing rule, extended to every year 2026-08-09 |
| **C3a-2023 / C3b-2023** | **REFUSED the ledger carve-out**; C3a stands a MODEL MISS at full magnitude; the model-class lane authorized instead | ercot-182 sitting, card **D1 SIGNED** |

That lane then ran to its end: ercot-184 costed (c2), ercot-188 built and measured
it, and the offer-curve **resolution** face is now closed alongside level, grain
and position. **There is no undispositioned gate left under #2.**

> **Recommendation: close #2 as SPENT** — not as answered-by-this-card, but as
> answered by D1 + the 2026-08-05 C3c decision + ercot-168, none of which
> back-referenced it.

### G.3 — Ruling #3: `split_coal_tranches` delete-vs-inert · **DEAD ON ALL SIX KEEPERS**

Measured at HEAD, not inferred. `build_dispatch_fleet` branches on
`campd_bins is not None`, and `split_coal_tranches` lives **only in the `else`
limb**. Read from each keeper's own `run_config.json` scenario dump:

| ISO | `use_campd_bins` | reaches `split_coal_tranches`? |
|---|---|---|
| ERCOT / CAISO / PJM / MISO / NYISO / NEISO | **True** (all six) | **No — dead limb** |

Every keeper nonetheless carries **six registered scalars** that reach nothing:
`coal_tranche_{1,2,3}_frac` and `coal_tranche_{1,2,3}_fuel_passthrough`
(`coal_tranche_1_frac = 0.3` on all six). miso-128 §4 already proved the
inertness the hard way at MISO — assembling the real fleet twice under the
keeper's config, once with the committed fractions and once materially
perturbed, and measuring **zero** difference in `pmax_mw` and `fuel_fracs`.

**Rule 26 `[R-DELETE]` is squarely on point:** *"Deprecated fitted knobs are
removed, not zeroed — a deprecated parameter that still parses is a re-armable
answer key."* Six such parameters currently parse.

> **Recommendation: DELETE.** Not "mark inert" — delete the function and the six
> scalars, in a lane that first proves the legacy limb is unreachable for every
> registered bundle, not just the six current keepers.

### G.5 — Ruling #5: Martin Lake lignite class composition · **MIS-STATED; the real object is ONE-CLASS-PER-PLANT**

**The narrow question is already answered in code, and the answer is that Martin
Lake is NOT in the lignite class.** Resolved live at HEAD via
`data.coal._coal_class_for`:

| plant | scoring class |
|---|---|
| Martin Lake (6146) | **`COAL_PRB`** |
| Limestone (298), W A Parish (3470) | `COAL_PRB` |
| Oak Grove (6180), Major Oak (7030), San Miguel (6183) | `COAL_LIGNITE` |

It is curated in `COAL_PLANT_SUPPLY` with its reason on the line —
*"now PRB by rail (was East Texas lignite)"* — and ercot-143 §7.3 corroborates
behaviourally: the fleet's disputed 31.3 pp mid-band segment is carried by
**Martin Lake 0.535, Parish 0.539, Limestone 0.455** (all PRB), while the true
lignite plants Oak Grove and Major Oak — **84 % of the lignite class** —
contribute **0.016 / 0.018 / 0.001 / 0.000**.

**But the ruling's real object is bigger than Martin Lake,** and ERCOT-146 §3 is
what enlarged it: the curated bin sheet is **one class per plant**, so a
physically mixed facility gets one label. **Nine plants carrying 1,708 MW of
EIA-860 CT capacity** — T H Wharton, V H Braunig, R W Miller, Decordova, Sand
Hill, Colorado Bend, C R Wing, Dansby, Ray Olinger — have **no `CT_PEAKER` row at
all**; the sheet carries them as `CC_REGULAR` / `ST_GAS` / `CC_CHP`. ERCOT-146
recorded their measured CT rates in the artifact expressly as *"evidence-in-waiting
for the class-composition question (same family as the open Martin Lake ruling)."*

So #5 is not a plant question. It is: **does the one-class-per-plant bin sheet
need to become multi-class per plant?** That is a fleet-representation change with
real scope — it moves C1 class denominators and every per-class gate.

> **Recommendation: close #5 as stated (the Martin Lake assignment is correct and
> evidenced) and re-open its real object under an accurate title** — *"one-class-
> per-plant bin sheet vs mixed facilities"* — carrying the ERCOT-146 nine-plant
> evidence. Do not leave it filed under a plant name that resolves the other way.

### G.0 — the register's own defect

Three rulings sat open for eleven days across at least four sessions, and **all
three were already decidable from committed artifacts** — one spent, one dead
code, one mis-titled. The register carries no closure discipline: #2 was
overtaken by decisions that never back-referenced it, and #5 kept a title its own
evidence contradicts. Worth a standing rule that a signed decision names the
rulings it discharges.

## H. WHAT THIS CARD DOES NOT ASK FOR

* **No rubric amendment.** Nothing here touches `LEDGERABLE_CRITERIA`,
  `MAX_LEDGERED_CAVEATS` or the v3.0 tier guard.
* **No holdout marker.** ERCOT stays absent from `complete` and `final`; no
  out-of-training year is proposed for solve, score or registration.
* **No keeper movement** other than card **E**, where the recommendation is not
  to move it.
* **No re-opening of the closed C3a-2023 faces** — level (items 21–23), grain
  (both forms `R`), position (item 23), resolution (item 26). ercot-177 §3 closed
  ORDC/RTORPA/reserve level; ercot-177 §6 / ercot-181 §7 closed the quantity and
  capability *faces* as then-posed; (c1) sub-hourly is refused on scale.

---

## §7. ONE NON-ERCOT ITEM, CARRIED ONLY BECAUSE IT IS MARKED UN-ACTED

**NEISO scores on P2.** All **15** committed NEISO bundles carry
`commitment: true`; all **111** bundles of the other five ISOs carry `false`. That
is against CLAUDE.md's "Dispatch & Commitment" (*"P1 is THE main run … what every
run is scored on"*; *"No keeper uses it"*). It survives the `--enable-legacy-p2`
gate because that gate runs on parsed CLI args while `run_replay_bundle`
re-injects the recipe's flags from `meta.json` afterwards, so **every replay
carries P2 forward invisibly**. Materiality is small but non-nil: 2025 `COAL_BIT`
−2.3 %; mean LMP +0.058 / +0.011 / +0.038 $/MWh; the 2024 annual max +18 %.

Marked **"ESCALATED TO THE OWNER, NOT ACTED ON"** — resolving it needs a re-solve.
**This is the NEISO lane's to own; ercot-188 read the entry and verified nothing
beyond it** (rule 25).

---

## RESOLUTIONS — ALL SEVEN SIGNED BY THE OWNER, 2026-08-11

Recorded verbatim. Where the owner departed from the card's recommendation the
departure is stated as such, not smoothed over.

| card | decision | **SIGNED** | vs. recommendation |
|---|---|---|---|
| **A** | DAM-deriver lane #8/#9/#10 | **A1 — authorize as ONE lane, #9 first** | as recommended |
| **B** | Item 13 COAL limbs, 2023 application | **B1 — re-adjudicate under a fresh precommit** | as recommended |
| **C** | ercot-165 daytime curtailment mode | **C1 — decline the DOF, re-point the object** | as recommended |
| **D** | RTC+B adapter | **D1 — authorize, scoped to a read adapter** | as recommended |
| **E** | ercot-188 SCHEME R1 promotion | **E2 — PROMOTE on the standing structural standard** | **DEPARTS — the card recommended E1, do not promote** |
| **F** | Golden test-tier scheduling | **F1 — schedule the data-provisioned tier** | as recommended |
| **G** | Rulings #2 / #3 / #5 | **#2 close as SPENT · #3 DELETE the function and the six scalars · #5 close as stated and re-open the real object** | as recommended, on all three |

### E — the departure, recorded as the owner's

The card recommended **E1 (do not promote)** on three grounds, none of which the
owner disputed: the added rows are measured never to be cleared on, the residual
moves the wrong way in all three years, and the price is a permanent forfeiture
of the offer-surface family's P0 bit-identity proof. **The owner took E2**, under
the standing standard that *structural integrity outranks gate regression*.

**What that does and does not change.** The keeper moves to
`2026-08-11-run188-arm-topfine-cliff`. **The pre-registered mechanical verdict
stays REJECTED-AS-ARMED and is NOT rewritten** — G-C3c still fails at full
magnitude, and the promotion is the owner's standard applied *on top of* that
verdict, never a re-score of it (the ercot-185 posture). The determination is
**NOT-YET {C3a-2023, C3b-2023}, unchanged** — the promotion buys structural
fidelity, not a better public claim. **The forfeited P0 bit-identity proof is
carried as a named permanent limitation** on the keeper, in the matrix cell, in
the §5.1 header and in the FINDING; it does not expire when a later gate passes.

### What these seven signatures do NOT do

* **No rubric amendment.** `LEDGERABLE_CRITERIA`, `MAX_LEDGERED_CAVEATS` and the
  v3.0 tier guard are byte-unchanged.
* **No holdout marker granted or spent.** ERCOT still holds no `complete` and no
  `final`; no out-of-training year was solved, scored or registered, so no
  `calibration-complete.json` re-key applies (rule 22 / D-5(b)).
* **No determination change.** ERCOT remains NOT-YET on both load-bearing 2023
  criteria.
* **No lane authorized beyond card A.** B/C/D/F/G are dispositions, not charters;
  each still needs its own pre-registered round before any solve.

### Execution order implied by the signatures

1. **A1** — the DAM-deriver lane (#9 → #8 → #10), one precommit, one re-derive,
   one re-gate sweep. It is the only blocking item and it unblocks ercot-189's CC
   headroom object.
2. **G#3** — delete `split_coal_tranches` and its six scalars, after proving the
   legacy limb unreachable for every registered bundle.
3. **G#5** — re-file the one-class-per-plant object under an accurate title with
   the ERCOT-146 nine-plant evidence.
4. **D1** — the RTC+B read adapter (independent; unblocks forward corpus work).
5. **B1 / C1 / F1 / G#2** — dispositions to record; B1 needs a precommit before
   any arm.

**Evidence appendix — every figure above is read off these committed artifacts,
with no re-derivation:** `docs/PRECOMMIT-ercot149-dam-gas-event-cap-2026-08-01.md`
§5 (the ten-ruling register); `docs/DIAGNOSIS-ercot149-gas-cop-window-2026-08-01.md`
§6.1–6.3; `docs/DIAGNOSIS-ercot151-offline-increment-phase0-2026-08-02.md`;
`results/calibration/FINDING-ercot163-cc-commitment-state-refuted-2026-08-04.md`
§3–§4; `docs/mechanism-testing-matrix.md` §5.1 (items 13, 21–26 and the open-ruling
header); `docs/calibration-log/ercot.md` (ercot-165, ercot-183, ercot-187 entries);
`results/calibration/FINDING-ercot188-cliff-offer-curve-2026-08-11.md` §5–§7;
`results/calibration/ercot188_p0_delta.json`;
`frontend/data/backcast/keepers/ERCOT.json`.
