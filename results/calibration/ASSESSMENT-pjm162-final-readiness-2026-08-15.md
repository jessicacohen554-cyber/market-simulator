# ASSESSMENT (pjm-162): is PJM ready for a `final` (locked-test) declaration?

**Session:** pjm-162 · **Date:** 2026-08-15 · **Branch:**
`claude/pjm-162-envelope-final-53eoug`
**Scope:** assessment only. **This document grants nothing and spends nothing.**
`final` remains EMPTY for every ISO; the holdout spend freeze remains ACTIVE; no
PJM year outside 2023–2025 was solved, scored or registered in this session.
Granting the locked tier is the owner's separate, explicit act (an entry in
`final`), never an inference from an assessment.

**Evidence basis:** committed artifacts only, plus one no-LP measurement of a raw
measured INPUT (§2), which is data characterisation and not a spend — the posture
rule 22's 2026-08-06 clarification makes explicit (*what is held out is the
SCORE, never the DATA*) and the one pjm-160's 2019/2021/2022 seam-ladder
derivation already established.

---

## §0 — recommendation

> ## **NOT YET.**

**On the merits, not on process.** PJM's keeper is genuinely and currently
CALIBRATED (§1), its lane is clean, and its cross-ISO lever queue is cleared.
What blocks the locked tier is not the model's standing but the fact that **2019
would today be scored on a run carrying two known, quantified, unrepaired
artifacts, one of which is 3.4× larger in 2019 than in any training year.** The
locked test is **touch-once, ever**. Spending it now buys a number that could not
be interpreted and could never be re-run.

Four independent grounds, **any one of which is sufficient**:

| # | ground | status |
|---|---|---|
| 1 | The **holdout spend freeze** is ACTIVE and its own stated lift condition is unmet — and this session *quantified* PJM's share of the residual the freeze names, rather than closing it (§4). | **blocking, and owner-level** |
| 2 | The **DA-virtual architecture escalation**: 2019's net DA virtual position is **+7.08 TWh**, against −0.82 / −2.11 / −0.84 in the training years on the same basis. At pjm-158's measured channel that is **≈ +5.7 TWh of phantom physical energy onto `CC_REGULAR`** — larger than the keeper's entire in-sample `CC_REGULAR` error range (§2). | **blocking** |
| 3 | The **validation tier is unresolved and cannot be resolved by re-spending it**: the 2022 arithmetic has no passing combination (§3). Spending the touch-once tier while the iterable tier below it is still open inverts the ladder. | **blocking** |
| 4 | The **availability envelope's basis defect** is now measured for PJM and is unrepaired: 19.2–20.4 % of fossil nameplate held at hard zero, asserted unavailability 30 % of nameplate against PJM's published 24 % (§4). | **contributing** |

**What would change the answer** is in §5, and it is a short list.

---

## §1 — (a) does the keeper still re-verify CALIBRATED at HEAD rubric?

> ## **YES — CALIBRATED, every criterion PASS, zero caveats, governance attested.**

`scripts/calibration_verdict.py --run-id 2026-08-04-pjm-152-collapse`, committed
artifacts only, **no solve**, run at HEAD this session:

| criterion | tier | verdict |
|---|---|---|
| C1 fuel-mix by class (grid-delivered) | LOAD | **PASS** |
| C2 system volume (gas/coal families) | LOAD | **PASS** |
| C3a mean LMP | LOAD | **PASS** |
| C3b price duration/shape | LOAD | **PASS** |
| C3c price tail / scarcity (RT hourly) | SUPP | **PASS** |
| C4 fleet hourly dispatch correlation | SUPP | **PASS** |
| C6 governance gate | PROT | **PASS** |
| C8 forced-energy share (D-2) | PROT | **PASS** |

`D-10 free-class C1: C1 all 16/16 · free 12/12`; basis line *"all criteria pass,
governance attested"*. The four C8 report notes (CT_PEAKER 2023/2024/2025 at
16.2 / 16.4 / 16.7 %, ST_GAS 2025 at 39.9 %) are **grounded above budget** — all
binding mechanisms clear D-4, profile *r* 0.896–0.974, off-peak CV ratio
0.719–2.242 — i.e. clean PASSes under rule 21's grounded-pass clause, **not
caveats**. `scripts/audit_keepers.py --iso PJM` returns **0 failures, 0 warnings**
across the keeper, holdout, marker and status checks.

**Note on the bundle's own `metrics.json`,** which reads `NOT-YET`: that is the
frozen record from the pjm-152 bundle write, when the governance attestation did
not yet exist. pjm-153 generated it (`gen_pjm153_collapse_attestation.py`, every
premise computed), which is what makes the live verdict above scoreable. The
`complete` marker already records this. It is not a discrepancy.

**So ground (a) is satisfied and is not what blocks the declaration.**

---

## §2 — (b) the DA-virtual escalation, MEASURED for 2019

**The question, stated exactly.** pjm-161 §2 established that the DA-virtual
layer's contribution to C1 **IS the annual net Day-Ahead virtual position**: the
LP carries one price and one energy balance, so a financial position that closes
out in real time and contributes zero physical energy is served as physical MWh.
That position is a real market quantity and it is **not stable across price
regimes** — ≈ 0 across 2023–2025 and **+12.25 TWh in 2022**. Nobody had measured
it for 2019.

**Measured here, no LP** (`scripts/probes/_pjm162_virtual_2019.py` →
`_pjm162_virtual_2019.json`): PJM's own submitted DA bid curves, evaluated at
PJM's own published 2019 DA prices — the rule-13 admissibility anchor — using the
pjm-158 helper chain unchanged (`load_curve` / `build_hour_arrays` /
`eval_net_fast` / `actual_da_price`); only the year set differs.

| TWh, **+ = net virtual DEMAND** | **2019** | *2022* | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| **net DA virtual position at actual DA prices** | **+7.08** | *+11.71* | −0.82 | −2.11 | −0.84 |
| same curves at DA − $5 | +25.32 | +22.78 | +19.18 | +19.33 | +15.87 |
| same curves at DA + $5 | −10.01 | +2.38 | −17.03 | −20.45 | −14.48 |
| mean actual DA ($/MWh) | 25.54 | 67.31 | 29.33 | 29.79 | 43.72 |

**Basis note, because it differs from pjm-161's headline and the difference must
not be papered over.** pjm-161's table quoted the anchor on the *canonical
committed system DA series* (`anchor_DA_canon`: +12.25 / −0.76 / −1.62 / +0.20).
2019 has **no** canonical series — there is no PJM 2019 bundle, by construction —
so the only available basis is the **RTO hub-mean published DA price**
(`actual_da_price`). Every column above is on that single hub-mean basis, so the
whole row is internally like-for-like. The two bases agree closely: **2022 reads
+11.71 hub-mean against pjm-161's +12.25 canon**, and the training years read
−0.82 / −2.11 / −0.84 against −0.76 / −1.62 / +0.20. The conclusion does not turn
on which basis is used. *(2022 is shown in italics as already-measured context —
it is read from raw input curves, exactly as pjm-161 §2 read it, and no 2022
model output is touched.)*

### The reading

**2019 is not a training-like year for this layer. It is a 2022-like year.**
+7.08 TWh is **3.4× the largest training-year magnitude**, has the **opposite
sign** to two of the three, and sits at **60 % of 2022's** — the year whose C1
miss this same layer was measured to drive. Applying pjm-158 §5.2's own measured channel (~80 %
of a virtual-volume change lands on physical generation, predominantly
`CC_REGULAR`), the 2019 position implies **≈ +5.7 TWh of phantom physical energy
on `CC_REGULAR`**.

Set that against the keeper's in-sample `CC_REGULAR` C1 errors — **−3.45 /
+0.32 / +3.96 TWh** (`_pjm161-KEEPER-ADJUDICATION-2026-08-14.md`): **the
artifact alone is larger than the keeper's entire in-sample error range on the
class it lands on.**

**And the uncertainty runs the wrong way, not the reassuring way.** The ±$5 rows
show the anchor is **steep** — a $5 price error moves it ~18 TWh. The model's own
2019 price error is *unmeasured and unmeasurable without spending the year*, so
the realized position could be materially larger or smaller than +7.08 TWh. That
does not make the risk speculative; it makes the resulting number
**uninterpretable**, which is precisely the condition a touch-once tier must not
be spent under. A miss could not be attributed between forecast error and the
known architectural artifact, and a pass would be actively misleading.

> **Answer to (b): YES, the DA-virtual architecture escalation is a blocker for a
> one-touch 2019 spend — and it is a *stronger* blocker than it was for 2022,
> because 2022 was iterable and 2019 is not.**

---

## §3 — (c) the standing 2022 arithmetic

Reproduced from `FINDING-pjm161-...-2026-08-14.md` §5, re-checked against the
committed record, not re-derived:

| term | direction on `CC_REGULAR` | magnitude |
|---|---|---:|
| removing the DA-virtual phantom energy | **−** | ≈ −8.9 TWh |
| the pjm-160 seam-ladder year-keying repair (already at HEAD) | **+** | +5 to +7 TWh |
| **net of the two** | — | **≈ −1.9 to −3.9 TWh against a +18.28 TWh miss** |

**There is no combination of the two identified objects that makes 2022 pass**,
and the seam repair — the single largest thing a re-spend would change — moves
C1 the **wrong** way, because exports are a sink and PJM's 2022 marginal class is
`CC_REGULAR`. A 2022 re-spend is not a route to a passing touchpoint and should
not be requested as one.

**Why this bears on `final` rather than only on 2022.** The tiers are a ladder:
validation exists to be iterated against so that the locked test is spent on a
model whose known defects have been sent back to the training window and
resolved. PJM's validation rung is **open with a named, unresolved architectural
cause**. Declaring `final` now would spend the touch-once tier while the iterable
tier below it is still unresolved — and, per §2, would spend it on the year where
that same unresolved cause is **largest**.

---

## §4 — two further grounds the committed record supplies

**(i) The holdout spend freeze is ACTIVE, and this session did not close its lift
condition.** `holdout-freeze.json` names its own exit: *"the merit-order-guard fix
charter reaches a decision — either the corrected detector is adopted and each
affected ISO's keeper is re-audited on the corrected envelope, or the charter is
closed with cause and the extract is confirmed fit for purpose."* The 2026-07-26
`held` entry records why it stayed armed: *"a residual over-count survives the
guard"*. That is not met. The freeze outranks both markers and is checked first;
lifting it is an owner action and *"no session lifts it by inference from a
passing metric."*

**(ii) This session quantified PJM's share of exactly that residual — and it is
substantial.** `FINDING-pjm162-outage-envelope-basis-closure-2026-08-15.md` §3:

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| model asserted fossil unavailability, % of model fossil nameplate | 30.3 % | 31.4 % | 29.9 % |
| PJM's published TOTAL outage, on the same denominator | 24.2 % | 24.0 % | 26.0 % |
| of the model's, **held at HARD ZERO every day** | **19.6 %** | **20.4 %** | **19.2 %** |
| model vs published on the **top-1 % net-load days** (MW) | 21,253 / 10,785 | 25,487 / 13,010 | 23,806 / 16,674 |

**On the peak days the model asserts roughly twice the unavailability the
operator publishes for its entire system.** This is the freeze's named residual,
located and measured for PJM for the first time — the finding *sharpens* the
freeze's rationale rather than discharging it, and it is not repairable from
PJM's published data (§7 of the finding: the only surviving re-open needs
GADS-style unit detail PJM does not publish).

---

## §5 — what would change this answer

Stated as a short, checkable list, so the next assessment is not a re-litigation:

1. **The owner lifts the freeze**, or records that the merit-order-guard charter
   is closed with cause. Owner-level; no session can infer it.
2. **The DA-virtual architecture question is decided** (pjm-158 raised it,
   pjm-161 re-escalated it, §2 now prices it for 2019). The decision does not
   have to be a *fix* — an owner ruling that the layer stays as-is with the
   artifact disclosed would also unblock, provided the 2019 result is read with
   the +7.08 TWh position on the record **in advance**, which is why it is
   measured here rather than after the fact.
3. **A defensible disposition of 2022** — not necessarily a pass, which §3 shows
   is unreachable, but an explicit owner determination of what the validation
   rung has told us and that it has been sent back to 2023–2025.

Ground (a) needs nothing: the keeper is CALIBRATED today and re-verifies clean.

**Nothing here is a criticism of PJM's calibration standing.** PJM holds the
frontier and `complete`, its queue is cleared, and it is the most thoroughly
adjudicated non-ERCOT lane in the program. The recommendation is about *when to
spend an irreplaceable measurement*, not about whether the model is good.

---

## §6 — posture attestation

* `final` is EMPTY; **this document changes nothing in it.**
* The holdout freeze is ACTIVE and untouched.
* No PJM year outside 2023–2025 was **solved, scored or registered** in this
  session. §2 evaluates measured input curves at measured published prices and
  produces **no model output for 2019** — no bundle, no determination, no
  registry entry, no dashboard artifact.
* `scripts/audit_keepers.py --iso PJM`: **PASS, 0 failures, 0 warnings** (keeper,
  holdout, marker, status).
* Keeper unchanged at `2026-08-04-pjm-152-collapse`.
