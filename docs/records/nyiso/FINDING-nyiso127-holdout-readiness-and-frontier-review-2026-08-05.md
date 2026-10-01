# nyiso-127 — NYISO is NOT READY to spend 2022, and the reason is the freeze's own defect, still 1.7–2.9× the norm on this ISO

**Session:** nyiso-127 (successor to nyiso-126). **Keeper unchanged:**
`2026-08-04-nyiso-125-seam-envelope`. **No solve ran. No mechanism was armed, no
parameter moved, no bundle was produced, nothing was registered.** No
out-of-training year (2022 / 2019 / ≤2021 / H1-2026) was solved, scored, read or
registered; the holdout spend freeze was checked first and is **ACTIVE**.
Everything below is scorer-side on committed artifacts and `data/raw`.

**ITEM 1 (the one chartered lane) was NOT executed — it is owner-gated and the
authorisation was not given in this session.** ITEM 2 (Q1–Q5) and ITEM 3 are
complete and need no authorisation, no intake and no solve.

---

## §0 — verification at this session's own head

| check | result |
|---|---|
| NYISO keeper shard | `2026-08-04-nyiso-125-seam-envelope` |
| nyiso-125 promotion on `main` | **yes** — `20127fd0`, contained in `origin/main` |
| nyiso-126 on `main` | **yes** — `25dbf462` (PR #3555), contained in `origin/main` |
| `calibration_verdict.py --run-id 2026-08-04-nyiso-125-seam-envelope --json` | determination **NOT-YET**; reason *"undocumented out-of-tolerance (FAIL) criteria: `price_mean`"*; C3a **+7.7 / −0.8 / −10.2 %** (2025 model $59.76 vs actual $66.53); C3c **CAVEAT (ledgered)**, model **18 / 2 / 21 h** vs actual **10 / 12 / 42 h**, failing **2024 alone**; C1 all 14/14 · free 10/10; C2/C3b/C4/C6/C7/C8 PASS |
| `audit_keepers.py --iso NYISO` | **PASS, 0 failures / 0 warnings** |
| holdout | NYISO holds **`complete`** (validation tier), **absent from `final`**; the **spend freeze is ACTIVE** (declared 2026-07-25, HELD 2026-07-26) and outranks both |
| nyiso-126 decomposition | re-run at this head, reproduces exactly (decile 10 **141.6 %** of the 2025 signed residual; h16/17/18 = **25.0 / 24.6 / 21.0 %**) |

Ledger budget: **1 of 3 ledgered slots spent** (C3c). Protective 0 of 1. DOF
`n_entries 34 / n_residual 6`.

---

## §1 — ITEM 2 / Q3: does the freeze's stated reason still bind for NYISO? **YES, and it is large.**

The freeze's reason is that the CAMPD unit-outage detector books sustained
economic layup as mechanical outage, so *"every ISO books 23–46 % of its CC
capacity-year as outage against a real EFOR + planned norm of ~10–15 %"*
(`FINDING-neiso63-campd-economic-layup-2026-07.md`). The merit-order guard was
**ADOPTED-AS-IMPROVEMENT** 2026-07-26 and the freeze was **HELD** because a
residual over-count survived it — measured then on **NEISO**. This section
measures it on **NYISO**, on the **current, post-guard** extract.

Instrument: `scripts/probes/_nyiso127_cc_outage_envelope.py`, record
`results/calibration/_nyiso127_cc_outage_envelope.json`. Inputs are
`data/raw/campd-unit-outages-NYISO.csv` (the mechanical extract every keeper is
calibrated against), its `-layup-` companion (the windows the guard vetoed), and
`bin_assignments_NYISO.csv` for coverage. **No LP, no model output except the
keeper's committed `class_hourly` sidecar in §1.3.**

### 1.1 Capacity-weighted: MW-days booked out ÷ installed CC MW-days

| population | class | 2023 | 2024 | 2025 |
|---|---|---:|---:|---:|
| BASELINE (pre-guard) | CC_REGULAR | 41.4 % | 40.8 % | 42.5 % |
| **CURRENT (post-guard)** | **CC_REGULAR** | **25.4 %** | **29.6 %** | **35.8 %** |
| VETOED (layup) | CC_REGULAR | 15.9 % | 11.1 % | 6.7 % |
| BASELINE (pre-guard) | CC_ALL | 38.8 % | 36.4 % | 36.5 % |
| **CURRENT (post-guard)** | **CC_ALL** | **26.7 %** | **28.0 %** | **31.1 %** |

Denominator is the **detector's own capacity basis** (`unit_capacity_mw` over its
own unit panel, CC_REGULAR 8,949.8 MW / 47 units / 23 plants). It is **not** the
model fleet's nameplate (6,856.5 MW over the same 23 plants — a different basis;
mixing them inflates every share by ~1.31× and an earlier draft of this probe did
exactly that before it was caught). Coverage against the model fleet is
near-complete: **23 of 23** CC_REGULAR plants and **16 of 17** CC_CHP plants
appear in the panel, so the "units with no window are invisible" bias is small.

### 1.2 neiso-63's own unit-year metric, reproduced for like-for-like comparison

Mean days out per unit-year ÷ 365, full-year windows excluded — the exact
construction behind the **46 %** neiso-63 quoted for NYISO CC_REGULAR:

| population | class | 2023 | 2024 | 2025 |
|---|---|---:|---:|---:|
| BASELINE (pre-guard) | CC_REGULAR | 47 % (n=41) | 47 % (n=40) | 44 % (n=40) |
| **CURRENT (post-guard)** | **CC_REGULAR** | **37 % (n=32)** | **37 % (n=32)** | **37 % (n=34)** |
| VETOED (layup) | CC_REGULAR | 75 % (n=10) | 68 % (n=10) | 57 % (n=9) |

The baseline row reproduces neiso-63's 46 % (44–47 %), which validates the
construction. **The guard removed 10 pp and left 37 %.**

### 1.3 THE ANSWER, and the part of it that is against interest

**The residual over-count for NYISO is LARGE.** On the current extract, NYISO
books **25.4 / 29.6 / 35.8 %** of its CC_REGULAR capacity-year as mechanically
unavailable, against the **~10–15 %** EFOR + planned norm the freeze cites —
**1.7× to 2.9×**, and it is **worst in 2025**, the one year C3a fails. The
guard's veto shrinks year over year (15.9 → 11.1 → **6.7** pp), so the correction
is smallest exactly where the residual is largest.

**Reported against interest — the obvious mechanism does NOT show up.** The
natural story is that a too-tight envelope pins the CC fleet against its ceiling,
so CC cannot be marginal and something dearer sets the price, producing the
stable **+$3.79 to +$5.51/MWh bulk over-pricing** nyiso-126 measured and left
unattributed. **Measured on the keeper's own committed `class_hourly` sidecar,
that is not what the fleet is doing:**

| year | CC_REGULAR annual max MW | mean MW | mean/max | hours ≥95 % of max |
|---|---:|---:|---:|---:|
| 2023 | 6,490 | 3,792 | 58.4 % | 47 (0.5 %) |
| 2024 | 6,088 | 4,356 | 71.5 % | 78 (0.9 %) |
| 2025 | 5,973 | 4,081 | 68.3 % | 398 (4.5 %) |

The keeper's CC fleet has headroom in 95.5–99.5 % of hours. **The pinned-fleet
mechanism is not supported and is not claimed.** What the measurement supports is
narrower and sufficient for the question asked: **the availability envelope NYISO
is calibrated against is materially wrong in a known direction, and the freeze's
premise — that a 2022 miss would be uninterpretable and a 2022 pass actively
misleading — still holds for this ISO on its current keeper.** (The 2025
co-incidence of the tightest residual envelope with the failing C3a year is one
observation of three. It is noted as suggestive and **not** advanced as a
finding, and no lever is proposed from it — the NYISO lever queue stays empty.)

### 1.4 A separate defect found while checking the ledger — one phantom DOF entry

Sweeping every ALL-CAPS symbol the keeper's DOF ledger cites in its `where`
fields against `src/market_sim/` (9 symbols): **one does not exist at HEAD.**

* `GAS_AVAILABILITY_FACTOR[NYISO] = 0.866`, ledgered with
  `where: "constants.py GAS_AVAILABILITY_FACTOR"` and
  `identification: "published"` (NERC GADS Brochure 3). **There is no
  `GAS_AVAILABILITY_FACTOR` anywhere in `src/market_sim/`, and no `0.866`
  either.** The only other occurrence in the repo is
  `market-sim-build-plan.md:406`, the **pre-extraction** manifest of the legacy
  `lmp_engine.py` — i.e. it is a symbol that was never carried into the current
  engine, ledgered forward through the NYISO attestation lineage.

This is an **over-count**, not a hidden tuning channel: a listed parameter that
cannot bind a solve, not an unlisted one that can. It is a rule 20 `[R-DOF]`
provenance defect (the ledger must list each free parameter *with its
identification source*, and an entry pointing at a symbol that does not exist
cannot be verified). **Flagged, not edited** — the ledger is generated by
`scripts/gen_nyiso125_attestation.py`, so editing the emitted JSON would be
reverted by the next generator run, and the correction belongs in the same owner
disposition as ITEM 3.

---

## §2 — ITEM 2 / Q1: is the frontier declaration still valid on its own premise?

**Recommendation: (iii) LAPSED — re-declare rather than amend a third time.**

**The facts.** The frontier block (`keepers/NYISO.json`) was declared 2026-07-31
(nyiso-104) on the premise *"C3c was the SOLE blocker and every other criterion
already PASSED"*, and it wrote the determination label
**CALIBRATED-WITH-CAVEATS**. It was amended once, 2026-08-01 (nyiso-109), whose
own text records that nyiso-108 had found the premise **lapsed** (the hydro
repair exposed a 2023 C3a failure) and that nyiso-109 **restored** it.

**It lapsed again at nyiso-120 and has not been restored since.** nyiso-120 moved
C3a-2025 from **−9.5 % (PASS)** to **−10.0 % (FAIL)** — a 0.5 pp knife-edge
crossing worth $0.39/MWh, of which **94 % of the gap was pre-existing** — and its
own log entry records `determination control CALIBRATED-WITH-CAVEATS → treatment
NOT-YET` (`docs/calibration-log/nyiso.md` §nyiso-120). Every re-verification
since, including this session's, returns **NOT-YET**. So the frontier block's
label and the live determination — and the `complete` marker's own
`determination` field, which correctly says NOT-YET — **disagree**, and have for
two days.

**Why (iii) and not (ii).** By the owner's own 2026-08-04 restatement,
`complete` / frontier means exactly two things: (a) the 2022 touchpoint is
allowed, and (b) *"frontier — we have tested everything we could have"*
(`docs/mechanism-testing-matrix.md`, caiso-171 block). Measured against the
current record, **every load-bearing clause of the 2026-07-31 note has since been
falsified or superseded**:

1. *"C3c was the SOLE blocker and every other criterion already PASSES"* —
   **false** since nyiso-120 (C3a-2025 FAIL, unledgered).
2. *"the five-zone representation **cannot** form the sub-zonal … scarcity"* —
   **too strong**: nyiso-125 moved the tail 3/0/14 → 18/2/21 h with a seam-side
   **input** correction carrying no scarcity parameter.
3. *"RE-OPEN CONDITION … a `Capital_Hudson` → Zone-F/Zone-G TOPOLOGY SPLIT"* —
   **falsified as written**: nyiso-124 closed that charter with cause at G0.
4. The determination **label** it wrote is stale.

A third amendment bolted onto a note whose premise, its stated escape hatch, its
strength claim and its label have all failed is bookkeeping, not governance. The
substantive frontier claim (limb b — the C3c lever queue is exhausted, nine items
adjudicated on the record) **survives and should be re-stated**; what should not
survive is the surrounding text. If the owner prefers the minimal action, (ii)
with clauses 1–4 above as the explicit edit list reaches the same end state — the
diff is the same either way.

**Not edited here.** The frontier block is an owner disposition (charter ITEM 2
hard limit), and this session did not touch it.

---

## §3 — ITEM 2 / Q2: does nyiso-126 collapse the two blockers into one?

**Physically, yes. For the rubric, no — recommendation: do NOT ledger C3a-2025.**

**The case FOR collapsing.** nyiso-126 measured that decile 10 alone is **141.6 %**
of the 2025 signed residual (model $108.69 vs actual $187.98 over an actual range
starting at $113.6/MWh), and C3c gates the >$300 tail **inside that same decile**.
One physical object, two gates reading it. On that reading, "C3c is the sole
blocker" becomes true again the moment C3a's FAIL is accepted as a **symptom** of
the already-ledgered caveat — and the mechanics support it exactly: a FAIL with a
matching exceptions entry is reclassified to CAVEAT by
`calibration_verdict._apply_ledger`, the determination reason
*"undocumented out-of-tolerance (FAIL) criteria: price_mean"* disappears, and
NYISO reads **CALIBRATED-WITH-CAVEATS** with **2 of 3** ledgered slots spent.
That is a one-line disposition with a real evidentiary basis behind it.

**The case AGAINST, which is why the recommendation is "no".**

1. **The rubric names what a ledgered caveat is, and this is not it.** A ledgered
   caveat is `MEASURED_LIMIT` — *"an out-of-tolerance criterion reclassified by
   an explicit exceptions-ledger entry (**the actual is the limitation**)"* — and
   the budget comment is explicit that *"each ledgered caveat still requires its
   own named **measured-input** reason — the budget bounds excuses, it never
   grants them."* C3a-2025's cause per nyiso-126 is a **model** defect on both
   halves (a +$4–7/MWh bulk over-pricing and a −$9.35/MWh top-decile
   under-pricing). The actual is not the limitation. Ledgering it would file a
   model miss under a heading reserved for a data limitation.
2. **Explaining a miss does not stop it missing.** The charter states this and it
   is right: a criterion does not stop failing because we have attributed it.
   nyiso-120 already declined to ledger this exact FAIL twice, on the record
   (*"C3a-2025 −10.1 %, a criterion failure **deliberately NOT ledgered**"*).
3. **Tier.** C3c is a *supporting* criterion; C3a `price_mean` is
   **load-bearing** — it certifies the intended use directly. The precedent for
   ledgering a structural model miss (C3c itself, classified `MODEL MISS
   (structural…)`) exists only at the supporting tier. Extending it to the
   load-bearing tier is a materially larger step than the one-line diff makes it
   look.
4. **One object, two slots.** If the owner nonetheless ledgers it, the honest
   construction is to **broaden the existing C3c entry to cover both criteria**
   (one defect, one slot) rather than open a second entry — otherwise the ledger
   double-counts a single physical defect and reads as two independent
   limitations, which is precisely the misstatement §4 below flags.

**Recommendation: keep C3a-2025 an unledgered FAIL and NYISO at NOT-YET.** The
collapse is real physics and belongs in the ledger's *text* (§4), not in its
*classification*. **Not re-classified here** — this session did not touch the
attestation, the generator or the emitted JSON.

---

## §4 — ITEM 3: the C3c ledger text is stale in THREE ways

Surfaced, **not edited**. The text lives in `scripts/gen_nyiso125_attestation.py`
(the generator is the source of truth; editing only the emitted JSON is reverted
by the next run). All three belong to the same owner disposition as §2 and §3 —
**one decision package, not four scattered flags.**

**(a) Its stated re-open condition is falsified as written.** The ledger's
re-open route is *"a `Capital_Hudson` → Zone-F/Zone-G TOPOLOGY SPLIT"*. nyiso-124
closed that charter with cause at G0: NYISO publishes **no** F/G (UPNY-SENY)
transfer limit in P-32, in the ATC/TTC posting over all 36 training months, or in
any of four Gold Book editions, and it **ceased studying the interface in 2013**;
independently, the split targets the wrong boundary (measured annual eastward
basis F|G **−$2.65 / −$0.36 / −$1.48**, i.e. Zone G prices *below* Zone F, while
E|F carries **+$10.17 / +$5.09 / +$11.69**). Citation:
`docs/handoffs/nyiso-124-charter-g0-g1-2026-08-04.md`; probe
`scripts/probes/_nyiso124_charter_g0_g1.py`. Already flagged-not-edited at
`docs/codebase-site/data/mechanism-matrix.js` §5.5 and `docs/calibration-log/nyiso.md` §(6).

**(b) Its premise is partly falsified.** The ledger classifies C3c as
*"structural — five-zone representation **cannot** form the sub-zonal NYC/LI
load-pocket scarcity"*. nyiso-125 moved the tail **3/0/14 → 18/2/21 h** with a
**seam-side input correction carrying no scarcity parameter** — no ORDC change,
no floor, no reserve mechanism — taking the gate from failing all three years to
failing 2024 alone. "Cannot" is too strong; "has not been formed by any admissible
*scarcity* mechanism tried" is what the record supports. Citation:
`results/calibration/FINDING-nyiso125-seam-envelope-2026-08-04.md` §5.5.

**(c) NEW at nyiso-126, and it is the one that changes what is being carried.**
C3a-2025 and C3c are **one object measured twice** (§3). The ledger currently
carries C3c as a *supporting* caveat while C3a is the *load-bearing* FAIL, with no
text connecting them. Whatever the owner decides in §3, the ledger text should say
that the two gates read the same defect — because as written it understates the
scope of what the single ledgered slot is covering. Citation:
`results/calibration/FINDING-nyiso126-seam-identification-and-c3a-decomposition-2026-08-04.md` §2.3(3).

**(d) A fourth item for the same package, from §1.4:** the DOF ledger's
`GAS_AVAILABILITY_FACTOR[NYISO]` entry cites a symbol that does not exist at
HEAD. Same generator, same disposition.

---

## §5 — ITEM 2 / Q4: order of operations

**Recommendation: (b) resolve ITEM 1 first, and spend 2022 on whatever keeper
survives — but ITEM 1 is not the binding reason to wait.**

ITEM 1 is pre-registered
(`PREREG-nyiso126-eastern-seam-attribution-2026-08-04.md`) and, if authorised and
its seven kill gates stay silent, **§8 rule 2 promotes it even if C3a and C3c are
unchanged or modestly worse** — so a successful arm changes the keeper by
construction, not by luck. Its own P1/P2 predict material movement in Central-East
utilisation (from 0.668/0.335/0.383 toward a measured 0.807/0.616/0.591) and the
first zonal price separation the model has ever produced (2025 model: NYC $58.65 =
Upstate_West $58.65, against a real, large downstate premium). Spending the 2022
touchpoint against a keeper with a live, pre-registered, keeper-changing candidate
in front of it wastes selection evidence for no gain, and the same reasoning is
already the standing cross-ISO recommendation — CAISO's frontier assessment
carries *"re-audit the keeper on the corrected availability envelope before
spending 2022"* as follow-on work.

**But the ordering argument is not what blocks 2022, and it should not be quoted
as if it were.** Even if the owner refuses ITEM 1 today and the keeper is
therefore stable, §1 blocks 2022 on its own: the availability envelope is 1.7–2.9×
the norm and about to change. **ITEM 1 is a reason to sequence; §1 is the reason
to wait.**

---

## §6 — ITEM 2 / Q5: readiness verdict

> **NOT READY.** Reason: the availability envelope NYISO's keeper is calibrated
> against still books **25.4 / 29.6 / 35.8 %** of CC_REGULAR capacity-year as
> mechanical outage — **1.7–2.9× the ~10–15 % EFOR+planned norm**, worst in the
> failing year — so the freeze's own stated premise (a miss uninterpretable, a
> pass actively misleading) binds for **this ISO on this keeper**, independent of
> any other consideration.

Two secondary reasons, either of which would independently counsel deferral:
the load-bearing C3a-2025 FAIL is unledgered and NYISO's determination is
**NOT-YET** (§2); and a pre-registered, keeper-changing candidate is queued
behind an owner authorisation (§5).

**Standing restatements, which hold whatever the readiness verdict is:**

* **2022 remains UNSPENDABLE until the owner lifts the freeze**, explicitly and
  in `holdout-freeze.json`'s `history` — never by inference from a passing
  metric, and never by this or any session. NYISO's `complete` marker authorises
  the validation ladder; the freeze **suspends** that authorisation and is
  checked first (`scripts/lib/holdout_policy.py`, fails closed).
* **A validation number is SELECTION EVIDENCE and is never quotable as a
  certified out-of-sample skill number** (rule 22 `[R-HOLDOUT]`). 2022 is
  iterable by design: a miss may legitimately send the lane back to re-tune
  2023–2025, which is exactly what disqualifies it as a skill claim.
* NYISO is **ABSENT from `final`**. 2019 and H1-2026 stay blocked by the marker
  *and* by the freeze. Nothing here requests or implies a locked-test grant.

---

## §7 — governance

* **Rule 22 `[R-HOLDOUT]`.** No out-of-training year solved, scored, read or
  registered. The freeze was checked before the marker. No edit to
  `holdout-freeze.json`, `calibration-complete.json`, or the keeper shard's
  frontier block — all three are owner dispositions and all three are untouched.
  No promotion, so D-5(b) does not fire.
* **Rule 15 `[R-DASHBOARD]`.** **No run was produced** — no keeper, no probe
  bundle, no rejected arm — so there is nothing to register on the backcast
  dashboard. The keeper's dashboard entry is untouched.
* **Rule 16 / rule 12.** No solve, so neither binds; §1 covers all three years
  from committed artifacts in one pass.
* **Rule 28 `[R-MECH-MATRIX]`.** **No mechanism was tested, so no cell verdict
  moves and no citation is owed.** The NYISO lever queue is empty and stays
  empty; nothing in §1 is advanced as a lever.
* **Rules 20 / 24.** No parameter added or moved. §1.4 reports an existing DOF
  ledger entry whose cited symbol does not resolve at HEAD; it is flagged for the
  owner disposition, not edited.
* **Rule 1 `[R-STRUCT]` / rule 13 `[R-MEASURED]`.** §1 measures an input against
  its published norm; it proposes no adjustment and pins nothing to a residual.
* **Reported against interest** in three places: the capacity-basis error caught
  and corrected mid-probe (§1.1), the pinned-fleet mechanism that the keeper's own
  sidecar does **not** support (§1.3), and the fact that the ordering argument in
  §5 is not the binding reason to defer (§5, last paragraph).

---

## §8 — reproduce

```
uv run python scripts/probes/_nyiso127_cc_outage_envelope.py
uv run python scripts/probes/_nyiso126_c3a_decomposition.py
uv run python scripts/calibration_verdict.py --run-id 2026-08-04-nyiso-125-seam-envelope --json
uv run python scripts/audit_keepers.py --iso NYISO
```
