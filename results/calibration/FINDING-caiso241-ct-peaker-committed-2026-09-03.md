# FINDING — caiso-241: the CT_PEAKER `committed` band is OUTSIDE the Lever-A refusal, grounded, promoted — and the object it was meant to explain SURVIVES

**Session caiso-241, 2026-09-03. Branch `claude/caiso-ct-peaker-admissibility-bnjtvb`.**
Pre-registered in `PRECOMMIT-caiso241-ct-peaker-committed-2026-09-03.md`
(`cf05a372`, pushed **before any fleet was rebuilt or any number below measured**),
`PRECOMMIT-caiso241-ADDENDUM-arm-2026-09-03.md` (`81b1aa80`, the evaluated
envelope, pushed **before any solve**) and
`PRECOMMIT-caiso241-ADDENDUM2-owner-ruling-2026-09-03.md` (`bc22e5ef`, the
owner's two rulings and the run design they changed, pushed **before any LP**).

CAISO holds **no `complete` and no `final` marker**; the holdout spend freeze is
**ACTIVE**; every read and both solves stayed inside **2023–2025**.

**Keeper: `2026-09-03-caiso-240-b1-stgas` → `2026-09-03-caiso-241-b1-ctpeaker`.**
Determination **UNCHANGED at NOT-YET**, C3a the sole load-bearing FAIL,
`audit_keepers --iso CAISO` **PASS 0/0**.

---

## §1 — HEADLINE

**The first deliverable was a ruling, not a solve, and it is the session's
primary result.** caiso-238 graded the five live CAISO `committed` bands **F4 —
refused on rule**, and caiso-231 applied that refusal uniformly. §2 rules that
grounding `CT_PEAKER.committed` on its own measured **physical** counterpart is
**OUTSIDE** that refusal, on five limbs — three of them new, any one sufficient.

**The repair is then the smallest possible one:** `committed := phys_committed`,
1.350 → 0.991, the value the band's own dict already carries. No new literal, no
registry value to pick, **zero free parameters**.

**It passed every pre-registered gate and was promoted.** And it was scored
against a **real control**, because the owner amended the caiso-231
no-control-arms directive for exactly this case — an arm live in every solved
year, for which no prior form of G-CTRL could bind.

**Three things went against the session, and all three are reported at full
size:**
1. **The CT_PEAKER object SURVIVES the repair.** Volume closes only
   **7.6 / 6.6 / 7.0 %** of the miss. P-2 and P-6, written to be uncomfortable
   before anything was measured, both hold.
2. **The pre-registered VOLUME ceiling was BREACHED** in two of three years
   (+2.4 %, +23.1 %) — an estimator defect, disclosed, never re-fitted.
3. **Prediction P-7 is FALSIFIED**, and its root cause is a general defect in
   the DOF instrument that four consecutive sessions have now walked into.

**And one thing the owner paid for and got: a measurement instead of an
assumption.** The control's HEAD drift is **exactly zero**.

---

## §2 — THE ADMISSIBILITY RULING: **OUTSIDE**, ON FIVE LIMBS

Full text and citations: precommit §1. In brief, with the two adjudicated limbs
first and the three new ones after.

| # | limb | status |
|---|---|---|
| 1 | **The refusal is ROUTE-scoped, and caiso-238 §3 said so in the assessment that ISSUED the F4** — it covers the measured **BID** multiplier (CT bucket 1.166, *still unarmed*), while *"grounding on the physical min-load burn is the same class of instrument Lever A itself used."* Bracketing fact: **1.350 > 1.166 > 0.991**, so the repair's DIRECTION is invariant to which measurement route one accepts. | already adjudicated |
| 2 | **Lever A's own ground refuses 1.35 symmetrically** — *"any avoided-startup credit belongs in an explicit UC layer, not the P1 offer"* — and `_CAISO_OFFER_CURVE` itself calls 1.35 a *"start-cost hurdle"*. Reading the refusal to protect it preserves an unidentified commitment adder **because** it is unidentified. | already adjudicated |
| 3 | **NEW — rule 19 `[R-ONE-MECH]` double-count.** The `_committed` tranche is the **only** tranche carrying the bin's start cost (`bins_to_fleet` docstring), and P1 already amortizes it: `BIN_STARTUP_COST_PER_MW["CT_PEAKER"] = $20/MW` (NREL/SR-5500-55433) ÷ the P0 run length, **no CT exemption**, and `tranche_startup_amortization` is **OFF** on this keeper, so the identified markup lands on the very band at issue. | **new** |
| 4 | **NEW — rule 25 `[R-ISO-SCOPE]` citation ring.** `committed = 1.35` appears in the CAISO, NYISO and NEISO `CT_PEAKER` curves, each comment citing the others (*"NYISO-grounded"* / *"NYISO/CAISO-grounded"*), **none citing a measurement**, against their own 0.991 (n=75) / 0.843 (n=70) / 0.985 (n=18). | **new** |
| 5 | **NEW — the band is the class's MOST EXPENSIVE MW, and the refusal created that.** The predecessor keeper reads `committed 1.350 > peak 1.166 = econ_high 1.166 > econ_low 1.145`. When 1.35 was set the class read 1.35/1.10/1.50/4.0 — a properly rising curve. **caiso-231's measured static surface inverted it** by re-grounding econ/peak while withholding `committed`. A refusal cannot coherently require maintaining the defect Lever A exists to remove. | **new** |

**The scoping is measured, not chosen (P-1, confirmed).** `CT_PEAKER` is the
**only** CAISO gas class that is both armed above **both** its measured
counterparts and inverted at the top. CC_REGULAR 1.000 < peak 1.386; CC_CHP
1.000 < 1.386; CT_CHP 1.100 < 1.166; ST_GAS 0.810 < 1.166 — all four rise, and
three of them are armed *below* both their measured values.

---

## §3 — THE OWNER'S TWO RULINGS, AND WHAT THE SECOND ONE BOUGHT

**Ruling 1 — the solve is FUNDED**, lifting the caiso-201/222 terminal rest for
this object, on caiso-240's CT_PEAKER measurement as the case.

**Ruling 2 — the caiso-231 "no control arms" directive is AMENDED.** An arm
measured **live in every solved year** — so that neither the `run_config`
field-diff form of G-CTRL nor caiso-240's dispatch-identity form can bind — may
spend **one** control solve, and its effect is measured against that control. An
arm with even one inert year still takes the caiso-240 leg and spends nothing.
*(Raised caiso-239 §6.1, escaped by caiso-240 §6.3 because that arm had an inert
year, met for the first time here.)*

**WHAT THE CONTROL MEASURED, REPORTED WHETHER OR NOT IT FLATTERS THE
AMENDMENT: HEAD DRIFT IS EXACTLY ZERO.** `caiso241_a0_control` — the keeper
recipe replayed at HEAD with no flag delta — reproduces
`caiso240_b1_stgas_peak_measured` **in every class, in every year, with an empty
delta set**, and its C3a reads the predecessor's own **+4.1 / +12.6 / +15.6 %**.

Two honest readings, and both belong on the record:
* **It cost ~65 minutes of LP to learn that a keeper five commits old had not
  drifted.** That is the case for keeping the carve-out narrow.
* **It converted an assumption into a measurement, and the assumption was
  load-bearing.** caiso-239 measured **22 differing `run_config` fields** on a
  one-day-old keeper and could not tell drift from mechanism; every keeper-relative
  number this lane has quoted since has rested on the *hope* that those fields
  were inert. This run is the first time that hope was tested, and P-8 held —
  the mechanism is live in all three years, so **no other check existed.**

---

## §4 — GATES, ALL SCORED ON **B1 − A0**

| gate | verdict | measurement |
|---|---|---|
| **G-STRUCT** | **PASS** | Verified **pre-solve** in all three years: exactly **44 of ~1,800** rows move, all CAISO `CT_PEAKER` `_committed`, at the **exact** ratio 0.991/1.350 = **0.734074074074**, with `offer_markup_hr` driven to **exactly 0.0** and **zero** rows moving in any other band, group or ISO. 829.8 MW = **11.0 %** of the 7,528–7,539 MW class. |
| **G-INERT** | **PASS** | Not byte-identical in any year; CT_PEAKER gains 0.206/0.253/0.148 TWh. |
| **G-CTRL (form 3)** | **PASS** | Every scored criterion's verdict in A0 matches the committed keeper's, and the class-energy drift set is **empty** in all three years. |
| **G-C1** | **PASS** | 12/12, free 8/8, unchanged. |
| **G-C3a — verdict leg** | **PASS** | No flip. 2023 stays PASS. **+4.1→+3.9 / +12.6→+12.3 / +15.6→+15.5 %.** |
| **G-C3a — envelope leg** | **PASS** | Measured **−0.0777 / −0.0426 / −0.0169 $/MWh**, inside the pre-registered two-sided **[−0.8798, +0.05] / [−0.3804, +0.05] / [−0.1979, +0.05]**. |
| **G-C3b** | **PASS** | Unchanged. |
| **G-C8** | **PASS** | Unchanged; the arm lowers an *offer* and adds no floor, so no mechanism enters D-2/D-4. |
| **G-CAVEAT** | **PASS** | Budget 1 of 1 — C3c alone, ledgered; 0 protective. |
| **G-C6** | **PASS** | Attested on **both** bundles (an unattested C6 would make C3c FAIL rather than CAVEAT, and would have injected a scorecard difference into B1 − A0 that was a measurement artifact). |

**Every scored criterion is identical across keeper, control and arm**
(`fuelmix` PASS, `sysvol` PASS, `price_mean` FAIL, `price_shape` PASS,
`price_tail` CAVEAT, `dispatch_corr` PASS, `governance` PASS, `forced_share`
PASS; grade summary scored 8 / target 6 / commercial 0 / ledgered 1 / fails 1).

---

## §5 — THE PROMOTION, AND WHAT IT IS **NOT** BASED ON

Promoted under the pre-registered §5.9 rule. **The basis is structural:** one
uncited, cross-ISO-circular scalar retires to CAISO's own measured counterpart,
removing a rule-19 double-count and a class-internal merit-order inversion, at
**zero free parameters**, with **no scored criterion regressing**.

**C3a improved, and that is excluded from the basis by pre-registration.** The
precommit §0.7 declared the favourable direction **before any solve** and named
it the session's principal hazard; §5.9 deliberately does not key on C3a; and
§A6 established **from the arm's own maximum, before it ran**, that it could not
flip C3a in any year even at its ceiling (0.880/0.380/0.198 $/MWh against a
required 0.00/−0.848/−1.893). It delivered **9 % of its own price ceiling**.
This object must never be re-proposed as a C3a lever.

---

## §6 — THE DECOMPOSITION: THE QUANTITY REMOVED IS **EXACTLY** THE FUEL-INVARIANT COMMITMENT MARGIN

Under `gas_offer_net_revenue_margin` the reformed cost is
`phys·base_hr·fuel + (mult − phys)⁺·base_hr·anchor`, so grounding `mult := phys`
leaves the fuel-scaled **physical** cost untouched and removes **only** the
fuel-invariant margin. Measured on the moved rows:

| | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| capacity-weighted Δ mc | **−18.6197** | **−18.6197** | **−18.6197** $/MWh |

**Identical to four decimals across gas at 2.54 / 2.19 / 3.52 $/MMBtu.**
Per-row −15.04 to −29.39 (median −18.63); `offer_markup_hr` 3.136–6.128 → 0.0.
The precommit's route arithmetic predicted ≈ $18.7 from the class base heat
rate; measured **$18.62**.

**So rule 19 here is arithmetic, not interpretation.** The entire effect of the
fitted 1.35 was a fixed $/MWh commitment adder — the margin mechanism had
already isolated it into exactly the form that makes it a start-cost adder — and
it sat on top of P1's identified amortized startup markup on the same tranche.

**Corroboration found AFTER the precommit push, labelled as such (addendum
§A4): MISO has already made this repair.** Its `CT_PEAKER` committed is
**1.025 = its own `phys_committed` 1.025**, and `_MISO_OFFER_CURVE` states limb
3 verbatim: *"The commitment-cost component of the real MISO CT offer (start +
no-load recovery) is **NOT a static heat-rate multiplier** … **represented by
the P1 startup amortization** … not by a band multiplier here"* (FERC Order 825
/ ELMP). Five of six ISOs price the CT min-load band above their own measured
basis — ERCOT 1.480/1.022, CAISO 1.350/0.991, PJM 1.250/1.049, NYISO
1.350/0.843, NEISO 1.350/0.985 — and MISO is the one that grounded it. **The
repair is precedent-following, not novel in kind.**

**Rule 25 disposition, executed strictly: nothing transfers.** ERCOT / PJM /
NYISO / NEISO cells stay `U`. Each lane grounds its own band on its own measured
`avg_committed_p50`, or the cell stays `U`.

---

## §7 — WHAT THE REPAIR DOES **NOT** DO. THE CT_PEAKER OBJECT SURVIVES.

Per-class TWh, model vs the plant-level actual (EIA-923/CAMPD — **never**
EIA-930's corrupt CISO NG cell):

| year | class | actual | A0 | B1 | A0 miss | B1 miss |
|---|---|--:|--:|--:|--:|--:|
| 2023 | CT_PEAKER | 4.128 | 1.421 | 1.627 | −2.708 | **−2.502** |
| 2024 | CT_PEAKER | 4.326 | 0.491 | 0.744 | −3.835 | **−3.582** |
| 2025 | CT_PEAKER | 2.339 | 0.230 | 0.378 | −2.109 | **−1.961** |

* **Gain +0.206 / +0.253 / +0.148 TWh — closing 7.6 % / 6.6 % / 7.0 % of the
  miss.**
* **P-2 HOLDS** (registered: the class stays below **half** its actual in ≥ 2
  years). Measured **39.4 % / 17.2 % / 16.2 %** — below half in **all three**.
* **P-6 HOLDS** (registered: CT_PEAKER remains the largest single-class gas miss
  in ≥ 2 years). It is the largest in **2024** and **2025**. In 2023
  CC_REGULAR is larger (−3.079 vs −2.502) — and **was already larger on the
  control** (−2.929 vs −2.708), so this is not caused by the arm.

**The dominant cause of the CT_PEAKER defect is therefore elsewhere** — the
econ/peak bands, availability, or a structural absence — and is a **separate,
larger, unfunded object**. The class's other rungs are already cheaper than the
committed band was, carry no `pmin` and no commitment coupling on the P1 path,
so the committed band never gated them; the precommit said so in §1.2 and
predicted the outcome in P-2/P-6 before measuring it.

---

## §8 — TWO DISCLOSURES AGAINST INTEREST

### §8.1 — THE VOLUME CEILING WAS BREACHED, AND IT IS AN ESTIMATOR DEFECT

| | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| pre-registered ceiling (§A6) | 0.432 | 0.247 | 0.120 TWh |
| **measured gain** | 0.206 | **0.253** | **0.148** TWh |
| | inside | **+2.4 %** | **+23.1 %** |

**Root cause, and it is the same blindness caiso-240 found, one level up.** The
crossing envelope §H′ counts hours in which the tranche crosses **the control's**
price. Once the tranche dispatches it displaces CC_REGULAR (−0.149/−0.185/−0.105
TWh), ST_GAS, imports and CC_CHP, and that re-dispatch **opens further hours the
estimator never counted**. §H could not see indirect re-dispatch at all;
§H′ sees the first order of it and not the second.

**The asymmetry is worth recording precisely, because it is useful:** §H′'s
**price** leg is *conservative* (it assumes the tranche sets price in every
crossing hour — a large overstatement, and the measured move came in at 9 % of
it), while its **volume** leg is *anti-conservative* (it misses re-dispatch-opened
hours). A future session should quote the price leg as an envelope and the
volume leg as an **order-of-magnitude indication only**.

**Nothing was re-fitted.** The precommit fixed the response in advance: *"a
bound violation is a defect in the estimator or the mechanism, reported as such,
never re-fitted."* The registered **price** falsifiers — the two-sided envelope
endpoints — both passed, with margin.

### §8.2 — P-7 IS FALSIFIED, AND THE REASON IS A DEFECT IN THE DOF INSTRUMENT

**Registered:** *"the DOF ledger DOES move this time. Unlike the last three arms
(whose retired literals lived in `campd_bins.py`, outside `_count_scalars`), this
one retires a scalar inside `offer_curve_by_group`, which the counter reads."*

**Measured: it did not move.** 9 entries / 6 residual on keeper, control and arm
alike.

**Root cause.** `build_dof_ledger._count_scalars` counts **numeric leaves**, and
the ledger's rows are a curated table. The repair **changes a value, it does not
remove a key** — the band must still carry a multiplier — so the count is
identical whether that multiplier is a fitted guess or a measurement. **Being
inside `offer_curve_by_group` is not the discriminator; having the key survive
is.** caiso-240's P-7 note said the counter *"measures the offer surface's SIZE,
not its fitted content"*; I read that as a statement about **location** and it is
a statement about **provenance**. It is the same error one level up, and I made
it in the session that quoted the note.

**CONSEQUENCE, and it is larger than one prediction:** **four consecutive
grounding repairs — caiso-239, caiso-240 and this one twice over — are invisible
to the DOF ledger.** A lane whose whole programme is retiring fitted scalars to
measured ones has an instrument that cannot see its own progress. **ASK, filed
for the owner:** give the ledger a per-leaf `fitted` / `measured` provenance
count, or an `identification` field at band grain, so a substitution registers.
Rule 21 `[R-DOF]` is currently enforced by prose, not by the counter.

---

## §9 — PREDICTIONS, SCORED AGAINST INTEREST

| # | prediction | verdict |
|---|---|---|
| **P-1** | CT_PEAKER is the only CAISO gas class armed above both its measured counterparts AND inverted at the top | **HOLDS** — measured on the resolved band dicts of all five live gas classes |
| **P-2** | the arm does **NOT** close the volume gap; the class stays below half its actual in ≥ 2 years | **HOLDS** — 39.4 / 17.2 / 16.2 % of actual, below half in all three |
| **P-3** | < 25 % of CT_PEAKER grid capacity is in `_committed` tranches | **HOLDS** — 11.0 %, confirmed pre-solve |
| **P-4** | the price effect is materially smaller than the raw multiplier ratio suggests: \|ΔP̄\| < 0.35 $/MWh every year | **HOLDS** — max 0.078, a 4.5× margin |
| **P-5** | G-STRUCT exact: the ratio, the zeroed markup, nothing else moving | **HOLDS** — confirmed pre-solve in all three years |
| **P-6** | the arm is **NOT** the dominant cause; CT_PEAKER remains the largest single-class gas miss in ≥ 2 years | **HOLDS** — largest in 2024 and 2025 |
| **P-7** | the DOF ledger **does** move this time | **FALSIFIED** — §8.2 |
| **P-8** | no inert year exists | **HOLDS** — all three years live, which is what made the control necessary |

**Seven hold, one falsified.** The three predictions written to be uncomfortable
(P-2, P-4, P-6) all held in the direction that constrains the session's claim,
and the one that flattered the session's instrument (P-7) is the one that broke.

---

## §10 — DO-NOT-REDO ADDS

1. **Never re-propose `CT_PEAKER.committed` as a C3a lever.** It is now grounded
   at its measured basis and there is nothing left to move; the direction was
   favourable and is spent, and the promotion basis deliberately excluded it.
2. **Never arm the measured BID committed multiplier (CT bucket 1.166, or CC
   1.030) for any CAISO gas class.** The Lever-A refusal stands uniformly on the
   bid route; this session used the **physical** route and did not touch it.
3. **Never transfer 0.991 to NYISO, NEISO, ERCOT or PJM** (rule 25). Their cells
   are `U`; each lane grounds its own band on its own measured
   `avg_committed_p50` — 0.843 (n=70) / 0.985 (n=18) / 1.022 / 1.049 — or the
   cell stays `U`. **MISO is already grounded (1.025) and is the precedent, not
   a source.**
4. **Never quote §H′ (or §H) as a bound on VOLUME.** Its price leg is an
   envelope; its volume leg under-predicted by up to 23 % here because
   re-dispatch opens hours it cannot see. §H is not an upper bound either
   (caiso-240).
5. **Never expect the DOF ledger to register a fitted→measured substitution**
   until `_count_scalars` carries provenance. Four repairs are invisible to it.
6. **Never treat the CT_PEAKER volume defect as closed.** This repair delivers
   ≈ 7 % of it. The remaining ≈ 93 % is a separate, larger, unfunded object.

---

## §11 — CARRIED, PROPOSE-ONLY, NOT STARTED

The residual CT_PEAKER root cause (§7, the largest open CAISO volume object);
caiso-238 object 4 (`battery_dispatch_adder` → measured AS reservation + ATB
degradation; F2, the strongest standing ask, materiality COMPOUNDING li-ion
1.87 → 5.29 % of generation); object 3 (own-curve shape derive); the SoCalGas
OFO arm (`PRECOMMIT-caiso227-ofo-arm-2026-08-31.md`); the
`IMPORT_TRANCHES[CAISO]` LEVEL object; the DOF-provenance instrument ask (§8.2);
and — for other lanes under rule 25 — the four un-grounded `CT_PEAKER.committed`
bands, the `ST_CHP` offer surface, and the `COAL:mr` citation ask.
