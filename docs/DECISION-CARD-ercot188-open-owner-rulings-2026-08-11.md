# DECISION CARD — the ERCOT open-ruling backlog, assembled at ercot-188

**For the owner sitting. Assembled 2026-08-11 at HEAD `ce4d05e` (origin/main) by
session ercot-188. NOTHING IS DECIDED HERE.** No lever proposed, no
`ScenarioConfig` field added, no derive run, no LP solved, no run registered, no
matrix cell minted by this card. Every figure is read off **committed artifacts**
— no re-derivation, no replay, no new measurement.

**Scope:** ERCOT (rule 25 `[R-ISO-SCOPE]`). One non-ERCOT item is carried in §7
**only because it is explicitly marked un-acted**, and it is that ISO's lane to
own. ERCOT holds **no `complete` and no `final` marker**, so every year
referenced is inside {2023, 2024, 2025} (rule 22).

**Keeper: `2026-08-09-ercot185-shaped-partial`** — determination **NOT-YET**,
fail set **{C3a-2023, C3b-2023}**. Untouched by ercot-188.

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
| **E** | ercot-188 — promote SCHEME R1 on structural fidelity? | no | **DO NOT PROMOTE** |
| **F** | Nothing schedules the tier the ERCOT golden lives in | no | Schedule it |
| **G** | Rulings #2, #3, #5 — dead or alive? | no | **One line from you; I could not verify** |

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

## G. RULINGS #2, #3, #5 — dead or alive?

**I could not verify these and will not assert them.** The ercot-149 register
carried ten rulings. Verified since: **#7** closed (owner-promoted,
`ercot_dam_availability_gas_event_cap` cell `K`); **#6** closed (refused on data
2026-08-04, no paid daily gas licence); **#1** and **#4** discharged by the
rule-28(c) ERCOT column closure at ercot-156 (census debt **0/0/0**).

**Not verified either way:**

| # | Subject |
|---|---|
| **#2** | per-gate dispositions of the attributed gates |
| **#3** | `split_coal_tranches` delete-vs-inert (note rule 26 `[R-DELETE]`: a deprecated knob that still parses is a re-armable answer key) |
| **#5** | Martin Lake lignite class composition |

I found **no carry-forward and no explicit closure** for any of the three after
ercot-149, and the current matrix header lists only #9/#10 as open. They are
therefore either silently discharged or silently dropped. **One line from you
settles it; my asserting it would be a guess.**

---

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

## RESOLUTIONS — to be signed

| card | decision | signed | vs. recommendation |
|---|---|---|---|
| **A** | DAM-deriver lane #8/#9/#10 | | |
| **B** | Item 13 COAL limbs, 2023 application | | |
| **C** | ercot-165 daytime curtailment mode | | |
| **D** | RTC+B adapter | | |
| **E** | ercot-188 SCHEME R1 promotion | | |
| **F** | Golden test-tier scheduling | | |
| **G** | Rulings #2 / #3 / #5 status | | |

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
