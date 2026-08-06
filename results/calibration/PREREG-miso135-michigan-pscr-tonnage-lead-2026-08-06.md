# PRE-REGISTRATION — miso-135: the Michigan PSCR state lead for ex-ante coal contract tonnage

**Session:** miso-135, 2026-08-06, branch `claude/miso-135-calibration-zya3y5`,
off `origin/main` at `2321ce86`.

**Keeper at entry:** `2026-08-05-miso-132b-cc-committed` (bundle
`results/calibration/miso132_ccmin_B`), **NOT-YET**, sole FAIL C7 `COAL_PRB`
2025 `cv_ratio` 0.338 vs the 0.50 gate (via `R_dfrac` 0.347; 2023/2024 pass at
0.505/0.524), ledgered caveats 2/3 {C3a, C3c}.

**Charter lane:** **(a)** — the **Michigan PSCR state lead**, the sole unspent
item on the MISO board and the only route around the 2026-10-30 Form 580
calendar to the only remaining admissible route to C7-2025. Source under test:
the Michigan PSCR process, MCL 460.6j, as filed at the MPSC by **DTE Electric**
and **Consumers Energy** — named at
`docs/handoffs/miso-coal-contract-tonnage-data-ask-2026-07.md` **§3(b)** as
*"Not yet checked, and the highest-value remaining state"*, with the open
question stated there verbatim:

> Whether the *public* PSCR plan exhibits carry per-plant contracted coal
> tonnage (as opposed to cost projections, with volumes confidential) is
> **open**.

**Adjudicating instrument:** the standing ask's own acceptance test — **§4.1**
(the A–F specification) and **§4.2** (the five-measure pin-strength battery),
**with every threshold binding exactly as written**. Per the charter: *do not
soften them to make the lead clear.*

**Rule 22 `[R-HOLDOUT]`:** 2023–2025 ONLY. MISO holds **no** calibration-complete
marker. No 2022 / 2019 / H1-2026 year is solved, scored or read at any point in
this session. Any PSCR document vintage covering an out-of-training delivery year
is read for **structure only** and no out-of-training quantity is extracted,
tabulated or carried into any gate.

**NO LP. NO SOLVE. NO SCORING. NO RUN REGISTRATION.** This is a data/sourcing
adjudication; none is expected and none is authorised by this document.

**This document is pushed BEFORE any adjudicating statistic is computed, and
before any MPSC document is opened.**

---

## §0. FULL DISCLOSURE — every number and fact already in hand before this PREREG

Per the miso-131 §0 duty, everything known before pre-registration, so no result
below can be back-fitted to a number already seen. All of it is from committed
artifacts and the standing ask; **nothing here is a measurement of the source
under test, and no MPSC document has been opened.**

1. **The target set** (ask §1, `scripts/probes/miso104_contract_source_coverage.py`,
   committed artifacts only): **39 plants, 26 owners, 12 states**, all EIA-860
   regulated. **93.99 / 80.67 / 89.52 Mt** in 2023 / 2024 / 2025 (re-derived for
   the record at xiso-4, unchanged from miso-104).
2. **The Michigan headline already published** (ask §3(b)): DTE Electric +
   Consumers Energy = **11.4 Mt = 12.8 % of 2025** target tonnage. The per-year
   split, and the Michigan **plant count**, are **not** in hand and are gate G-2.
3. **The §2C coverage bar, as written:** ≥ **15 of the 39** plants **AND** ≥ **60 %**
   of target-set tonnage, in **EACH** of 2023, 2024, 2025.
4. **A consequence of (2) and (3) that is arithmetic, and is stated here in
   advance so it cannot later be presented as a finding:** at 12.8 % of 2025
   tonnage, **Michigan alone cannot clear §2C's tonnage leg**, by a factor of
   ~4.7×. The ask says so itself (§3(b): *"It cannot clear §2C alone, but combined
   with a Form 580 pull it is the second-largest block of addressable tonnage"*).
   **This is NOT a reason to soften C**, and C is not softened. It is the reason
   the decision rule in §4 has a distinct **SUB-SCALE** branch that is neither a
   pass nor a closure.
5. **miso-103's failing receipts construction**, the comparison baseline for
   §4.2: log-space cross-section R² **0.923 / 0.874 / 0.935**; aggregate floor ÷
   actual **0.964 / 1.136 / 0.978**; energy-weighted floor **90.3 / 95.9 / 90.9 %**
   of actual CAMPD coal energy; plants bound **22 / 33 / 20** of 38; TWh forced
   **32.0 / 44.0 / 19.6**; within-plant delta R² **0.172**.
6. **The §4.2 thresholds**, quoted so they are fixed before measurement:
   (1) level-R² **≥ 0.80 FAILS**; (2) a candidate that lands annual coal energy
   on actuals **FAILS regardless of provenance**; (3) **no** year may put the
   aggregate floor **above** actual burn; (4) the delta test is **the one that
   must PASS**, and the admissible signature is **LOWER level-R² and HIGHER
   delta-R² than the receipts construction**; (5) binding margin is **reported**
   against the discount-free control `2026-07-29-miso-102b-sunkfixed`.
7. **Form 580 status, inherited:** the §8 count is **environment-blocked**
   (eLibrary is an SPA with no machine surface — the same 22,464-byte shell
   re-verified at xiso-4; `data.ferc.gov` does not carry the form; the
   headless-browser fallback fails because Chromium cannot traverse the session
   proxy) **and calendar-blocked** — the 2026 form (CY2024–2025) is due
   **2026-10-30**, so the CY2024/CY2025 contract data **does not yet exist**.
8. **Access probe run before this PREREG, and disclosed:** two HTTP status codes
   only, no document opened, no content read — `https://www.michigan.gov/mpsc`
   → **403** (bot-blocked from this environment), `https://mi-psc.my.site.com/s/`
   → **200**. This is the §G-0 access question and it is **not** an adjudicating
   statistic about the datum; it is disclosed here because it was observed before
   pre-registration and it is why lane (a) was chosen over a lane that would have
   been environment-blocked on arrival.
9. **Closed on kind, and NOT to be re-attempted** (ask §3(c) and the "Explicitly
   ruled OUT" list): IRP fuel-budget exhibits and **any modelled/projected burn**;
   any receipts-derived tonnage in any window/lag/smoothing/shrink; EIA-923
   Schedule 2 purchase-type flags; SEC 10-K dollar-denominated purchase
   obligations; coal-producer committed-and-priced tons; FERC Form 1 page 402;
   STB Waybill; penalty-priced or scalar-shrunk soft floors.
10. **Keeper C7 state, for context only and used in no gate:** `COAL_PRB` 2025
    `cv_ratio` 0.338 vs 0.50, `R_dfrac` 0.347; 2023/2024 pass 0.505/0.524. **No
    quantity in this session is identified off that residual**, which is the
    whole point of the ask.

---

## §1. What is being adjudicated

**One question, in the ask's own terms:** does the Michigan PSCR process publish,
**publicly**, a **per-plant coal tonnage that was fixed by contract before the
delivery year**, for delivery years 2023, 2024 and 2025 — and if so, does that
series survive §4.2?

This is a **source adjudication**, not a mechanism test. Per ask §6, even a fully
clearing source **only unblocks the charter** for the minimum-take constraint
session (miso-96 §7); it authorises no build, and this session builds nothing.

---

## §2. The gates, in order, with bars fixed before measurement

### G-0 — ACCESS (gating, environment)

Can the MPSC public docket be **enumerated** from this session for DTE Electric
and Consumers Energy PSCR **plan** cases whose plan years are 2023, 2024 and 2025?

* **PASS** iff, for each utility and each of the three plan years, a public case
  index resolves and its filing list is machine-readable from this environment.
* **FAIL** → verdict **ENVIRONMENT-BLOCKED**, recorded on the same boundary as
  the Form 580 §9 record (what was tried, what closed, what a working environment
  would need). No inference about the datum is drawn from an access failure.

### G-1 — KIND (gating; **this is §3(b)'s open question**)

Do the **public** PSCR plan exhibits carry a per-plant coal tonnage that is a
**contract/commitment** quantity fixed **before** the plan year? All three legs
must hold:

* **A (ex-ante by construction).** The quantity is stated in a filing whose plan
  year begins **after** the filing date, **and** it is presented as
  contracted/committed/under-contract tonnage. **A projected or forecast BURN
  FAILS A** — it is another model's forecast of the outcome, rejected on kind at
  ask §3(c), and it is rejected here identically no matter how convenient its
  grain. A tonnage that is a *delivery* or *receipt* forecast fails equally.
* **B (plant grain from the source, no receipts bridge).** The tonnage attaches
  to a **named generating plant by the document itself**. A system-total,
  fleet-total, or contract-grain tonnage that would need apportioning across
  plants is **DISQUALIFYING**, per §2B, because the apportionment weights are the
  forbidden series.
* **E (terms, not just a number).** Duration, price/quantity reopeners,
  make-up/carry-over tons, force majeure, buy-out/buy-down — enough that a
  forecast year could regenerate the quantity and it could move when conditions
  move.

* **PASS** → proceed to G-2.
* **FAIL** → verdict **CLOSED ON KIND** for the Michigan lead. Per the charter,
  the closure is **recorded explicitly**, with (i) exactly which leg failed and
  on what document evidence, (ii) a DO-NOT-REDO statement so no future session
  re-derives it, and (iii) a statement of what would be needed instead.

### G-2 — COVERAGE (§2C, and §4.1's per-year measurement)

Measured from committed artifacts against the `miso104_contract_source_coverage.py`
denominators: the **Michigan plant count** (of 39) and the **Michigan tonnage
share** (of 93.99 / 80.67 / 89.52 Mt), **per year**; then the count and share of
those plants for which a G-1-clearing series actually exists per year.

* **§2C PASS** iff ≥ 15 plants **AND** ≥ 60 % tonnage in **each** year. Per §0.4
  this is expected to **FAIL** on the tonnage leg and is **not softened**.
* **Battery-power sub-bar, fixed here:** the §4.2 battery is a **cross-section**
  test (miso-103 ran n ≈ 38). If fewer than **8** plants carry a G-1-clearing
  series in all three years, the battery is **UNDERPOWERED** and **no acquittal
  may be read from it** — a battery that cannot reject also cannot accept, and
  §4.2 is the ask's **sufficiency** test. An underpowered battery is reported
  with its numbers and the candidate is **NOT ACCEPTED**.

### G-3 — THE PIN-STRENGTH BATTERY (§4.2, thresholds binding as written)

Run the miso-103 methodology (`scripts/probes/miso103_mintake_pin_strength.py`)
on the candidate, substituting it for the trailing-mean construction. Report all
five per year, against the §0.5 baseline and the §0.6 thresholds:

1. **Level identity** — log-space cross-section R² of same-year actual receipt
   tons on the candidate. **≥ 0.80 FAILS.**
2. **Floor ÷ actual** — aggregate and energy-weighted. Landing annual coal energy
   on actuals **FAILS regardless of provenance.**
3. **No overshoot** — any year with aggregate floor **> actual burn FAILS.**
4. **Delta test** — within-plant YoY R² of Δactual on Δcandidate. **Must PASS**,
   and the admissible signature is **lower level-R² AND higher delta-R²** than
   the receipts construction's 0.923–0.935 / 0.172.
5. **Binding margin** — plants bound and TWh forced above unconstrained
   economics vs `2026-07-29-miso-102b-sunkfixed`, **reported**.

**Symmetry clause (ask §4.2), pre-honoured:** a source that clears §4.1 and §4.2
but shows contracted minimums are **NOT binding** on MISO coal has **refuted**
the minimum-take hypothesis rather than enabled it. That is a **finding to be
reported, not a source to be discarded**, and it closes the lane honestly. It is
pre-registered here as a **third named outcome**, not a disappointment.

---

## §3. Two-sided prior, declared before measurement

Both directions are live and **closure is declared at least as likely as
clearance** — in fact somewhat more likely.

* **For clearance:** PSCR is the most genuinely ex-ante state mechanism in MISO —
  a plan-year filing plus a five-year forecast filed **before** the plan year,
  with an annual reconciliation against it (MCL 460.6j). Utilities support PSCR
  plans with detailed fuel exhibits, and the statute's forward-looking structure
  is exactly the shape requirement A asks for. Michigan is also the
  second-largest addressable block after a Form 580 pull.
* **For closure:** the **Indiana pattern** (ask §3(b)) is the base rate and it is
  discouraging — IURC Cause 38702 FAC-91's *"VI. COAL CONTRACTS AND INVENTORY"*
  is entirely **qualitative**, with contract specifics in confidential
  attachments. Kentucky's un-redacted repository (§2a) is explicitly the
  **exception** among MISO states, not the rule. The most likely Michigan
  outcome, stated in advance, is **public $/MWh and cost projections with
  volumes either absent, system-total, or confidential** — i.e. a **G-1 FAIL on
  A or B**. A second plausible failure is a public **projected burn** at plant
  grain, which looks like the datum and **fails A on kind** (§0.9, §2 G-1-A);
  this PREREG names that trap in advance precisely so it cannot be walked into.
* **Third live outcome:** G-1 passes and §2C fails → **SUB-SCALE**, a real
  contribution that does not stand alone.
* **Prior on the battery, if reached:** genuinely unknown. A contractual Base
  Quantity of the §2a kind would be expected to show the admissible signature
  (lower level-R², higher delta-R²), but the symmetry clause outcome — minimums
  well below observed burn, i.e. **not binding** — is equally plausible and would
  refute the minimum-take hypothesis rather than enable it.

**No outcome of this session is a "success" or "failure" of the lane.** Per the
charter: *a NO is as valuable as a YES and must be recorded so the successor is
not re-proposed blind.*

---

## §4. Decision rule, fixed in advance

| branch | condition | disposition |
|---|---|---|
| **ENVIRONMENT-BLOCKED** | G-0 FAIL | record the boundary as §9 did for Form 580; no inference about the datum; lead stays UNSPENT |
| **CLOSED ON KIND** | G-1 FAIL | record the closure + failing leg + document evidence + DO-NOT-REDO + what would be needed instead |
| **SUB-SCALE** | G-1 PASS, §2C FAIL | record exactly what Michigan contributes per year and the residual gap to §2C; it becomes a **composition input** to the Form 580 pull, never a standalone clearance |
| **UNDERPOWERED** | G-2 sub-bar FAIL (n < 8) | battery reported, **no acquittal read**, candidate NOT ACCEPTED |
| **REFUTES THE HYPOTHESIS** | G-1+G-2+G-3 pass on provenance, minimums not binding | ask §4.2 symmetry clause — a finding, closes the lane honestly |
| **CLEARS** | G-0 ∧ G-1 ∧ §2C ∧ G-3 all pass | hand forward a **DERIVE CHARTER** (never a fitted level; rules 1/23/24); the coal offer-LEVEL lane re-opens ahead of the 2026-10-30 calendar |

**No branch of this table authorises building anything in this session** (ask §6).

---

## §5. Kill conditions — binding, declared in advance

* **K1.** **NO LP, no solve, no scoring, no dashboard registration.** Rule 22:
  2023–2025 only; no out-of-training year solved, scored or read, and no
  out-of-training quantity extracted from any document.
* **K2.** **Assessment, not intake.** Nothing is written under `data/raw/`; every
  document is read in the session scratchpad and cited by URL, preserving the
  ask §5 posture (*"miso-104 intook nothing"*). No rule-22 intake authorization
  is claimed, because none is requested. If a clearing source is found, the
  **intake** is a separate authorized step, not this session's to take.
* **K3.** **No receipts variant is re-tested** in any window, lag, smoothing or
  shrink (miso-103 DO-NOT-REDO), and no candidate is repaired by blending one in.
* **K4.** **No threshold is softened, re-scoped or re-based** — not §2C, not any
  of the five §4.2 measures — whatever the data shows. No penalty-priced soft
  floor, no scalar shrink, no "0.7 ×" (ask §6, rules 13/24).
* **K5.** **No mechanism is built, named as armed, or sized.** No `ScenarioConfig`
  field is added. Even a clearing source yields only a **charter**, handed
  forward.
* **K6.** **No adjudicated cell is re-opened** and **no other ISO's cell is
  touched** (rule 25). The miso-134 DO-NOT list is carried forward intact: the
  `CT_PEAKER` econ LEVEL stays closed and no partial Δ is proposed.
* **K7.** **A projected/modelled burn is REJECTED ON KIND** if found, and is not
  carried into G-2 or G-3 as a proxy, a sensitivity, or a "best available".
* **K8.** **No quantity in this session is identified off the C7 or C1 residual.**
  If the only way to make a candidate work is a residual-identified adjustment,
  that is rule 20 `[R-DOF]` — an open root-cause issue, not a parameter — and it
  is reported as such.

---

## §6. Secondary item — a RECORD-CONSISTENCY REPAIR, minting no verdict

miso-134 §9.5 flagged and deliberately did not edit: the `measured_offer_surface`
matrix row's `cells` string is `KKRUGI` (MISO = **`U`**) while its own `note`
prose says *"MISO cell R"*. **The two disagree, and one of them is wrong.**

Pre-registered handling, so this cannot become a back-door verdict:

* This session **tests no part of that mechanism** and **mints no new verdict**
  on it. The repair is to make the row **internally consistent with the evidence
  already cited in the record**, nothing more.
* **The rule, fixed now:** whichever of the two the cited evidence actually
  supports is the one that stands, and the other is corrected to match. If the
  cited evidence is **ambiguous or absent**, **nothing is changed** and the
  discrepancy is escalated in the FINDING rather than resolved by preference.
* No other cell moves on this item, and no ISO other than MISO is touched.

---

## §7. Artifacts this session will produce

* This PREREG, **pushed before any adjudicating statistic**.
* A probe under `scripts/probes/` for the G-2 coverage measurement (committed
  artifacts only, no network, no LP) and, only if G-1 passes, the G-3 battery.
* A record JSON under `results/calibration/`.
* A FINDING under `results/calibration/` stating the branch taken and, on any
  closure branch, the explicit DO-NOT-REDO and the what-would-be-needed-instead.
* Rule 28(b): the §5.4 queue stamp and any matrix touch, in this session.
* Rule 15: **no LP is solved, so there is no run to register** — the
  miso-131/132(a)/133/134 no-LP precedent.
