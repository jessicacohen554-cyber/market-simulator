# FINDING (pjm-162): route (1) is ANTI-TARGETED, and the PJM availability family closes on a CAPACITY-BASE mismatch, not an outage-type one

**Session:** pjm-162 · **Date:** 2026-08-15 · **Branch:**
`claude/pjm-162-envelope-final-53eoug`
**Predecessors:** `FINDING-pjm161-outage-inversion-and-da-virtual-energy-2026-08-14.md`
§7.4 (which named this successor), `_pjm161-KEEPER-ADJUDICATION-2026-08-14.md`,
`FINDING-pjm145-dam-availability-2026-08-02.md` §9 (whose re-open condition (1)
this closes).

**Holdout posture (rule 22 [R-HOLDOUT]).** The freeze is ACTIVE and untouched;
`final` is EMPTY. **No out-of-training year was solved, scored or registered.**
Every measurement below is on 2023–2025 or on raw measured inputs. **No LP was
solved at all** — this is the pjm-145 / ERCOT-145-146-147 no-solve-closure
pattern, and the reason there is no pre-registration is that there is no arm to
pre-register: the mechanism is refused *before* it is built, on its own
prerequisite check, which is what the session prompt asked Phase 0 to decide.

---

## §0 — the verdict in one table

| object | status |
|---|---|
| **pjm-145 route (1)** — "restore ceiling composed with the structural-derate registry (port the ercot137 fix)", the successor pjm-161 §7.4 selected by measurement | **REFUSED EX ANTE, no solve.** Its water-fill's net direction is **RESTORE** in every year, on **both** candidate bases, and in **every** slice — including the top-1 % net-load days (**+7.0 to +12.4 GW**) and the named winter-event windows (**+2.2 to +9.2 GW**). It would hand capacity BACK exactly where the defect is that it is too shallow. A restore **ceiling** bounds how much is restored; it cannot change the **sign**. |
| **the prerequisite the prompt asked about** (a planned/forced split of the model's envelope) | **DERIVABLE — and measured to be real — but NOT sufficient.** The CAMPD record separates cleanly on window duration, and the split's kill test passes. It is not what blocks route (1). |
| **what actually blocks it** | **A CAPACITY-BASE mismatch, roughly twice the size of the type-composition one, that neither pjm-145 nor pjm-161 named.** **19.2–20.4 % of the model's fossil nameplate sits at HARD ZERO every day** — layup, retiree CEMS caps, COD masks, full outage windows — capacity PJM's published outage record does not carry as "outage" at all. Every comparison against that aggregate therefore reads "the model is more derated than PJM says", on every day, whatever the outage-type basis. |
| **the family** | **CLOSED for now.** Routes (3) `R` (pjm-161), (1) refused here. Route (2) — a class- or unit-resolved PJM outage source — is the only surviving re-open, and it needs data **PJM does not publish**. |

---

## §1 — the test, and why it is the right one

Route (1) repairs pjm-145's refusal ground **(ii)**, structural-zero
resurrection. It says nothing about whether the water-fill's target is correctly
**signed** in the hours the defect lives in. A bidirectional water-fill fixes a
SHAPE defect only if it moves the envelope the right way there, so the
pre-registered prerequisite is:

> pjm-161 measured that the envelope is too **shallow** in scarcity. So on
> high-net-load days route (1) must **REMOVE**. If it **RESTORES**, the
> mechanism is anti-targeted and no ceiling saves it.

`scripts/probes/_pjm162_route1_phase0.py` → `_pjm162_route1_phase0.json`. Fleet
built on the keeper's own configuration (`pjm152_collapse_A/meta.json`,
`fleet_only=True`), so this is the keeper's envelope, not a reconstruction.

## §2 — DIRECTION: it restores, everywhere, on both bases

Net signed MW the water-fill would move, summed over the covered fossil-thermal
classes (**+ = RESTORE**, − = REMOVE):

| year | basis | all days | top-10 % net load | **top-1 % net load** | **winter event** |
|---|---|---:|---:|---:|---:|
| 2023 | total | +8,048 | +12,237 | **+10,367** | **+7,614** |
| 2023 | unplanned | +25,720 | +12,237 | **+10,367** | **+11,227** |
| 2024 | total | +9,882 | +11,411 | **+12,354** | **+9,241** |
| 2024 | unplanned | +27,671 | +11,412 | **+12,359** | **+11,493** |
| 2025 | total | +4,984 | +6,521 | **+6,961** | **+2,166** |
| 2025 | unplanned | +22,877 | +6,919 | **+7,024** | **+3,109** |

**Twenty-four of twenty-four cells restore.** There is no year, no basis and no
slice in which route (1) deepens the envelope in scarcity. The prediction the
prerequisite was written to test fails in the strongest available form.

*(Per-class disagreement exists — some covered classes restore and others
remove on the same day, which is why the restore-day and remove-day counts in
the JSON both run high. The table reports the **net**, which is unambiguous.)*

## §3 — WHY: the level, and the capacity base underneath it

The direction follows mechanically from the level, and the level is not close:

| MW | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| model fossil-thermal unavailable, **annual mean** | 41,658 | 43,196 | 41,222 |
| PJM published **total** (forced + maintenance + planned) | 33,298 | 33,002 | 35,870 |
| model, **top-1 % net-load days** | **21,253** | **25,487** | **23,806** |
| PJM published total, same days | **10,785** | **13,010** | **16,674** |
| PJM published **forced**, same days | 9,351 | 10,944 | 15,736 |

**On the peak days the model asserts roughly twice the unavailability the
operator publishes for its entire system.** So a target built from that
aggregate is *above* the model's own availability on those days, and the
water-fill restores toward it.

**The cause is a capacity-base mismatch, and it is measured:**

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| model fossil nameplate (MW) | 137,700 | 137,713 | 137,820 |
| asserted unavailable, as % of it | 30.3 % | 31.4 % | 29.9 % |
| of which **HARD ZERO** (MW / % of nameplate) | 27,009 / **19.6 %** | 28,091 / **20.4 %** | 26,428 / **19.2 %** |
| of which partially derated (rescalable) | 14,653 | 15,131 | 14,794 |

A fifth of the model's fossil capacity base is held at **zero every day** by the
layup windows, retiree CEMS caps, COD masks and full outage windows. PJM's
`gen_outages_by_type` is an **operational availability report over units in
commercial operation**: a mothballed or retiring unit is not "on outage" in it,
it is outside its accounting. The two records are therefore **not measuring the
same fleet**, and the gap between the fleets (≈ 19–20 % of nameplate) is about
**twice** the outage-type composition gap a planned/forced split would repair
(§4). This is pjm-145's rule-14 [R-ACCURATE] misalignment ground — "the accurate
datum is defined on a different boundary than our representation" — located
precisely and quantified for the first time.

## §4 — the split IS derivable, and it is a real result; it is just not the blocker

`_pjm162_split_derivability.py` → `_pjm162_split_derivability.json`. Stratifying
the CAMPD windows the model consumes by duration, against PJM's own published
typed series:

| 2024, per stratum | ann MW | r vs pub FORCED | r vs pub PLANNED+MAINT | r vs net load | **event/annual** |
|---|---:|---:|---:|---:|---:|
| 0–3 d | 115 | **+0.398** | −0.201 | +0.390 | **9.88** |
| 3–7 d | 2,165 | **+0.221** | −0.224 | +0.122 | **1.60** |
| 7–21 d | 8,595 | −0.087 | +0.278 | −0.376 | 0.62 |
| 21–60 d | 10,339 | −0.563 | **+0.912** | −0.781 | 0.30 |
| > 60 d | 11,416 | −0.647 | **+0.765** | −0.752 | 0.23 |
| *PJM published FORCED* | *7,698* | *1.000* | *−0.490* | *+0.679* | *1.91* |
| *PJM published PLANNED+MAINT* | *25,275* | *−0.490* | *1.000* | *−0.725* | *0.05* |

The separation is clean and it holds in all four years (2022–2025 in the JSON):
short windows track the operator's **forced** series and **rise** in every named
winter event (4.35 / 9.17 / 9.88 / 6.05 ×, against the published forced series'
own 2.84 / 1.53 / 1.91 / 1.30 ×); long windows track **planned + maintenance**
and fall (0.19–0.74 ×). **The kill test passes** — forced-outage information IS
present in the CAMPD record, in the short-duration family, contrary to what a
reading of pjm-161 §3.3 alone would suggest.

It also quantifies a genuine composition defect: **the model's window envelope is
~94 % planned-like and ~6 % forced-like (≈ 2.1 GW), against PJM's real ~73 % /
~27 % (forced ≈ 7.7–10.5 GW).**

**Two reasons this does not rescue route (1).** First, §3: the capacity-base gap
is about twice as large and points the same way, so fixing composition alone
leaves the direction unchanged. Second, the boundary is **not sharply picked by
the data** — `_pjm162_split_threshold.json` sweeps it and finds
corr(short-family, published forced) positive across **2–10 days** in every year
with no clear optimum, so any specific cut is a **free parameter** requiring a
DOF-ledger entry (rule 20) and an external definitional identification. It is
recorded here as a derivable, measured, currently-unused input.

## §5 — the ceiling: measured, and it does not reach far enough

| restore-day lift, MW/day | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| structural-zero resurrection (what the ceiling removes) | 9,281 | 10,660 | 8,304 |
| living-unit lift (what **survives** the ceiling) | **6,499** | **6,861** | **5,404** |
| zero share | 58.8 % | 60.8 % | 60.6 % |

The ercot137 ceiling works as advertised — it removes ~60 % of the lift,
reproducing pjm-145 §5's 66–68 % on this envelope. **And 5.4–6.9 GW/day of
living-unit restore survives it, still pointed the wrong way in scarcity.** Route
(1)'s repair is real and insufficient, which is the honest verdict on it.

## §6 — this EXPLAINS pjm-161's null result rather than merely recording it

pjm-161's event cap failed P4 and P6: it added ~zero outage in the top-1 %
net-load hours (unavailable MW unchanged to within 27 MW). pjm-161 §7.2
attributed that to the published TOTAL being planned-dominated and scheduled away
from peaks. §3 above supplies the mechanism underneath: **there was no room for a
remove-only cap to bind, because the model was already ~2× more derated than the
published total on those days.** A cap that can only deepen cannot bind against a
target it is already below. The two accounts agree and this one is the more
fundamental.

**A correction to how pjm-161's headline should be read, stated against
interest.** pjm-161 measured the CAMPD *window family* and found it inverts
(corr −0.68..−0.77; top-1 % hours carry 0.22–0.38× the annual mean derate). That
finding **stands** — it is a property of that family and it is real. But the
conclusion drawn from it, "the envelope is too shallow in scarcity", does **not**
survive comparison of the **whole** envelope against the operator's record: at
the top-1 % net-load days the full envelope is 21–25 GW against a published total
of 10.8–16.7 GW. Both statements are true of different objects. The prescription
that followed from the shorter one — *deepen the envelope in scarcity* — is not
supported.

## §7 — what is closed, what is open, and the successor

**CLOSED (DO-NOT-REDO, rule 28a).** The whole "compare the model's availability
envelope against PJM's published aggregate" family. Route (3) is `R` (pjm-161);
route (1) is refused here on direction; and the refusal generalises, because
§3's capacity-base gap is a property of the **comparison**, not of any particular
transform over it. No re-test of any member without new evidence.

**The only surviving re-open is pjm-145 route (2)** — a class- or unit-resolved
PJM outage source, or at minimum a numerator restricted to units in the model's
own commercial-operation base. PJM publishes no GADS-style unit detail today, so
this is **data-blocked, not analysis-blocked**.

**Two things this hands forward, both usable without re-deriving anything:**

1. **The planned/forced split (§4)** is derived, validated against PJM's own
   typed record, and committed. Any future mechanism with a *correctly-based*
   target can use it; it needs one DOF-ledger entry for the boundary.
2. **A redirection, which is the session's most consequential output.** PJM's
   scarcity defect (pjm-161's C3b / Elliott object) is **not** an availability
   defect: on the hours in question the model already holds twice the operator's
   published unavailability. Deepening the envelope is not the repair, and three
   sessions have now spent their lever on that hypothesis. The next PJM scarcity
   lever should come from **price formation, imports, or the demand side** — not
   from the availability family.

**Nothing is promoted, disarmed or armed.** Keeper unchanged at
`2026-08-04-pjm-152-collapse` (re-verified **CALIBRATED**, every criterion PASS, governance
attested, at HEAD rubric this session — see
`ASSESSMENT-pjm162-final-readiness-2026-08-15.md` §1). No dashboard registration:
**no run exists**, the pjm-145 no-solve-closure precedent.
