# FINDING miso-246 — **THE MISO BACKCAST LEVER-QUEUE CENSUS: `QUEUE NON-EMPTY`.** 33 LIVE routes, named. **And the number that makes it readable: neither is any granted ISO's** — MISO carries **44** backcast-lane-reachable `O`/`U` cells against PJM's **60**, NEISO's **66**, ERCOT's **55**, CAISO's **49**, NYISO's **31**; median over the five `complete` holders **55**. Two of my own gates FAILED and are published first

**Keeper: `2026-09-08-miso-245-ladderfix`** (bundle `results/calibration/miso245_ladderfix_K`),
DETERMINATION **CALIBRATED**, C3c the single ledgered non-downgrading caveat, DOF ledger **41/2** —
**all unchanged.** **ZERO LP: nothing was solved, screened, registered or promoted.** Rule 22
`[R-HOLDOUT]`: **2023–2025 only**; MISO holds no `complete` marker, **none is sought, inferred or
granted here**, and no out-of-training year was solved, scored or registered.

**Queue item taken (rule 28(a)): the handoff's RECOMMENDED item** — the census
`ASSESSMENT-miso245-complete-declaration-2026-09-08.md` **§6** names as the one respect in which
MISO's `complete` case is weaker than PJM's.

**Records, each pushed BEFORE the numbers it governs.**
PREREG `PREREG-miso246-the-backcast-lever-queue-census-2026-09-08.md` (`d769c3fd`), pushed with the
probe (`2d0767a5`) before either ran. Addendum 1
`ADDENDUM-miso246-my-own-gate-G-PARSE-failed-because-main-moved-under-it-2026-09-08.md` (`56d70600`).
Addendum 2 `ADDENDUM-miso246-M-a4-failed-and-item-a-is-unresolved-2026-09-08.md` (`718811a0`).
Probes `_miso246_lever_queue_census_phase0.py` (`c4ba68a1`, repaired, pushed before it re-ran) and
`_miso246_census_adjudication.py`. Machine records `_miso246_lever_queue_census_phase0.json` and
`_miso246_census_adjudication.json`.

**AND `G-PARSE′`'s provenance limb immediately earned itself.** `origin/main` moved **twice more**
during this session, so the census was **re-run after the final rebase** and the committed artifact
is stamped at HEAD **`e408f9c7`**, tree clean. **Every measured number in this document is
byte-identical between the two runs** — the only diff in the JSON is the provenance block itself
(the HEAD sha, and MISO's shard blob sha, which moved because of this session's own `ev` edits).
That is the check `G-PARSE`'s original literal could not perform, doing its job on its first
outing.

**Basis, named on every statement below.** `p_bus` = the keeper's committed **P1** price at
**`MISO_external`**; the seam regressor and every ladder anchor are the Indiana-hub **DA**
(`actual_lmp_hourly_MISO.parquet` `da`, float32); the price-decile column is the Indiana-hub **RT**.
`G-BASIS` measured them distinct at **0.4023 / 0.4237 / 0.5527**, reproducing the lane's published
+0.402 / +0.424 / +0.553.

---

## 0. STATED FIRST, AGAINST INTEREST — **TWO of my own gates failed, and the second one cost me the session's most interesting classification**

### 0a. `G-PARSE` failed because I froze a literal from a file that moved under me

Published in full in **addendum 1**, before any repair. The bar `== 312 cells` came from this
session's own **pre-PREREG** reconnaissance at session-start HEAD `de837c38`; `origin/main` then
landed `5df6192f` (`hydro_budget_period_by_instrument`, `U` at mode `BF` **in all seven shards**,
rule 28(c)) and the count became **313**. **Measured at three commits, the added cell shifts every
ISO's count by exactly +1, so `median − MISO` is 11 at both and the §3a verdict is IDENTICAL.**
The literal was **DELETED, not widened** (rule 26 `[R-DELETE]`) in favour of three limbs carrying no
hand-copied count — cross-shard identity, an upper-bound identity per shard, and a provenance stamp —
applied to **seven** shards where the original checked one. **`G-PARSE′` passes.** My PREREG's
disclosed `43` is superseded by `44`, and neither is wrong: the file moved.

### 0b. **`M-a4` FAILED, so item (a) is `UNRESOLVED` — and that is the classification the session wanted**

`M-a4` was declared in a pushed addendum **before its number existed** and written so it could
**only refuse**. It refused:

| year | limb (i) share \|`p_bus` − `p_Indiana`\| ≤ $0.01, bar ≥ **0.99** | limb (ii) \|σ(`p_bus`) − σ(`p_Indiana`)\|, bar ≤ **$0.05** | |
|---|---:|---:|---|
| **2023** | 0.9993 PASS | **$1.0027** | **FAIL** |
| 2024 | 0.9999 PASS | $0.0157 | PASS |
| 2025 | 1.0000 PASS | $0.0000 | PASS |

**`M-a4` was SATISFIABLE** — two of three years clear both limbs, 2025 to the bit — **so no repair is
made and no bar moves.** Re-scoping to 2024–25, excluding hours or relaxing the σ bar would each
convert the failure into a pass by construction; none is done. **`M-a3`, the lever enumeration, also
did not close, for the same reason the measurement gives (§3c).** Item (a) is `UNRESOLVED`, and item
(b) inherits that rather than being closed by it.

**What this costs me, plainly:** `M-a4` was the leg that would have let item (a) be *classified* —
refused as an already-scored object (C3b PASS / C3c the frontier) instead of left open. Without it
the census carries two more open items than it otherwise would.

### 0c. **A reading that FAVOURS me, labelled post-hoc, and used for nothing**

`P-a5` was declared with **no decision rule** in addendum 2 §3, before it was computed. In 2023 the
hour set where `p_bus ≠ p_Indiana` is **6 hours of 8,760** (0.068 %); **all six are in price decile
10**, five of them consecutive (h5653–h5657), with `p_Indiana` reaching **$231.40** against a
`p_bus` of **$76.05**. In 2024 it is **1 hour** (also decile 10), in 2025 **zero**. **With those
hours removed, σ(`p_bus`) = σ(`p_Indiana`) EXACTLY — 6.0242 vs 6.0242 in 2023, 16.5210 vs 16.5210 in
2024, gap 0.0000 to four decimals.** A reader may judge that limb (ii) was the wrong operand and
that item (a) is in fact identified. **I am not entitled to act on that**: the rule was fixed before
the number, it failed, and the excluded-hours σ is precisely the computation addendum 2 §1 refuses
to make the bar. §6 names the successor's leg instead.

### 0d. **A fact against a published claim, reported as measured**

miso-174 recorded the keeper's Midwest as *"a perfect copper plate (zonal price spread exactly 0.00
in all 8,760 h of all three years)"*. On **this** keeper the max cross-zone spread over the five
Midwest zones is **$0.746786 in 2023** and **exactly $0.000000 in 2024 and 2025**. Seven promotions
separate the two keepers, so this contradicts no session — but the claim does not hold verbatim at
HEAD, and 2023 is the year `M-a4` fails in.

---

## 1. **THE CENSUS VERDICT: `QUEUE NON-EMPTY`**

On PREREG §3's rule — *`QUEUE EMPTY` iff the `LIVE` set is empty* — applied with the conservative
default fixed before the table was written (**where the record is AMBIGUOUS or SILENT for MISO, the
route is `LIVE`** — the direction that makes the queue non-empty):

| enumeration | n | `LIVE` | `A` | `G` | `D` | `B` | `S` | `I` | `Q` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **E1** shard cells, `O`/`U` at mode `B`/`BF` | **44** | **34** | 1 | 0 | 0 | 1 | 4 | 4 | 0 |
| **E2** curated named items | 13 | 2 | 2 | 2 | 2 | 1 | 0 | 0 | 4 |
| **E3** the three handoff items | 3 | **1** | 0 | 0 | 0 | 0 | 0 | 0 | 2 |

**34 `LIVE` cells; 33 `LIVE` ROUTES** after the rule 19 `[R-ONE-MECH]` merge of
`gas_marginal_commodity_pricing` with `gas_variable_transport` (the owner-ruled form arms them
together). **Class `Q` — open attribution with no candidate mechanism — is a class the PREREG did
not provide**, disclosed in addendum 2 §2 rather than papered over; on the PREREG's own rule a `Q`
route is **not** `LIVE`, and `|Q| = 6` is reported separately so a reader who holds otherwise applies
their own reading. Full per-route ledger with each row's class, **basis (`MEASURED` /
`READ-EXPLICIT` / `NONE`)** and citation: `_miso246_census_adjudication.json`.

**SO THE ASSESSMENT'S §6 GAP IS NOT CLOSED IN THE DIRECTION A `complete` GRANT WOULD WANT.** MISO's
case is **not** PJM's: PJM's `frontier_basis` reads *"Structural lever queue measured EMPTY at
pjm-142"*, and MISO's census does not return empty. **That is the honest headline and it is stated
before the number that softens it.**

## 2. **THE NUMBER THAT MAKES §1 READABLE — measured on ONE parser at ONE commit, across all six ISOs**

`N_bc` = backcast-lane-reachable (`mode` ∈ {`B`, `BF`}) `O`/`U` cells:

| ISO | cells | `O`/`U` | **`N_bc`** | fc-only | `N_bc` / non-`.` backcast cells | `complete`? |
|---|---:|---:|---:|---:|---:|---|
| NEISO | 313 | 83 | **66** | 17 | 0.550 | **yes** |
| PJM | 313 | 78 | **60** | 18 | 0.451 | **yes** |
| ERCOT | 313 | 71 | **55** | 16 | 0.379 | **yes** |
| CAISO | 313 | 66 | **49** | 17 | 0.345 | **yes** |
| **MISO** | 313 | 59 | **44** | 15 | **0.299** | **no** |
| NYISO | 313 | 49 | **31** | 18 | 0.210 | **yes** |
| | | | median over the five `complete` holders | | **55** | |

**§3a's PRIMARY BAR — fixed in the PREREG against a comparator I had not measured and could not
see — CLEARS: MISO `N_bc` 44 ≤ median 55.** The secondary share (declared secondary *before either
number existed*, so it cannot be promoted after the fact) agrees: MISO **0.299**, second-lowest of
six.

**WHAT THIS ESTABLISHES, AND WHAT IT DOES NOT.** It establishes that *"structural lever queue
measured EMPTY"*, the basis PJM was granted on while carrying **60** such cells, **demonstrably did
not mean this grain** — no ISO has ever met a zero-shard-cell bar, and MISO is the second-lowest of
six. miso-192 already put the distinction on the record (*"empty of CURATED NAMES, not of TESTABLE
CELLS"*) and this measures it. **It does not establish that MISO should be granted anything.** It is
a comparison, not a standard, and it says nothing about whether any of the five grants was right.

## 3. THE THREE NAMED HANDOFF ITEMS

### 3a. Item (a) — bus-price compression: **`Q`, UNRESOLVED. And it is NOT A SEAM OBJECT**

**`M-a1` reproduces the object at HEAD** (reported, not gated; two keeper promotions intervened
since miso-242, so near-agreement is **EXPECTED**, not corroboration):

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| σ(`p_bus`) — miso-242 published 6.09 / 16.51 / 15.22 | **6.09** | **16.53** | **15.21** |
| σ(Indiana **DA**) — published 12.81 / 19.89 / 26.12 | **12.81** | **19.89** | **26.12** |
| ratio · corr | 0.4756 · 0.6926 | 0.8308 · 0.5881 | 0.5823 · 0.7827 |

**`M-a2` fired at `R_rung` = 1.0000 in all three years — zero unmatched hours, maximum
min-distance $0.00 — AND THE PREREG'S OWN REQUIRED DECOMPOSITION FALSIFIED ITS STATED GROUND:**

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| ladder-rung candidates alone | 0.1522 | 0.1508 | 0.1242 |
| **ladder-EXCLUSIVE** | **0.0007** | **0.0001** | **0.0000** |
| **zone-EXCLUSIVE** | **0.8478** | **0.8492** | **0.8758** |

`p_bus` is **not** rung-determined; it is **zone-determined**. Read with `M-a4` limb (i)
(0.9993 / 0.9999 / **1.0000**) and `P-a5`: **`p_bus` IS the model's own internal Midwest price, to
the cent, in 8,754 / 8,759 / 8,760 hours of the three years, and the frozen seam ladders explain
essentially nothing of it exclusively.** The handful of exceptions are **all** top-decile scarcity
hours in which the internal price runs away from the external bus — the tie fully loaded and the two
duals correctly separating.

**Consequences, stated because they are the useful part even though the item is `UNRESOLVED`:**
1. **miso-242's Q-B is filed as a seam object and it is not one.** The "model bus-price compression"
   is the model's **own MISO price distribution** — an object the rubric already scores twice, at
   **C3b** (duration / shape, **PASS**) and **C3c** (tail, the **designated frontier**, ledgered).
2. **The standing structural item is explained, not by a defect but by the architecture.** miso-241
   §8.4 / miso-245 §9.3 record that *"the model's SPP seam is 0.70–0.79 spread-correlated while the
   measured one is +0.0409 / −0.0200 / +0.0502 … the seam being idle is not the anomaly; its being
   spread-driven is."* The merit operand is `p_bus − anchor`, and `p_bus` is the internal price, so
   **the model's seam is a hub-pair spread BY CONSTRUCTION** — exactly what miso-236 §4 asserted from
   the code and what this measures. That does not make it right; it makes it a **price-formation**
   question rather than a seam-representation one.

**`M-a3` DID NOT CLOSE, and the gate FAILS as pre-registered.** Its enumeration was eight seam-side
objects. The identity above means **every internal MISO supply or demand object also changes
`p_bus`** in 8,754+ hours a year, so a ninth, tenth and n-th object exist. The PREREG fixed that
outcome in advance: *"If the code reveals a ninth object, the enumeration has NOT closed, the gate
FAILS, and item (a) is reported UNRESOLVED"* — **it is not patched by adding the object after the
fact.**

### 3b. Item (b) — Manitoba determinism: **`Q`. `M-b2` answered its own question and (a) did not answer its**

`M-b1` reproduces both sides on the current keeper (measured-side agreement is **EXPECTED** — it
reads no model artifact):

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| `R²_tmpl(r_measured)` — miso-236: 0.7380 / 0.7205 / 0.6594 | **0.7380** | **0.7205** | **0.6594** |
| `R²_tmpl(r_model)` — miso-236: 0.6036 / 0.5207 / 0.2869 | **0.6029** | **0.5225** | **0.2868** |
| ceiling-active share — miso-241: 0.4279 / 0.4152 / 0.2492 | **0.4281** | **0.4170** | **0.2490** |

**`M-b2` returns MERIT 3–0** on its pre-registered rule, and the internal consistency is the part
worth reading:

| subset | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| `Γ_ceiling` = `R²(meas)` − `R²(model)` | **−0.1290** | **−0.1912** | +0.1254 |
| `Γ_merit` | **+0.1791** | **+0.1866** | **+0.3559** |

In **ceiling-set** hours the model is *more* diurnally templated than reality in 2023 and 2024 —
which is what it must be, since the ceiling **is** the measured `(month × hod)` envelope. The whole
deficit sits in **merit-set** hours, whose share rises as the ceiling's collapses (0.428 → 0.249).
**So Manitoba's determinism collapse is the merit test on `p_bus` — and `p_bus` is item (a), which is
`UNRESOLVED`. Item (b) inherits that.**

**POWER, declared before the numbers and honoured now:** 2025's ceiling subset is ~25 % of hours, so
its 288-cell block fits on ~7.6 samples/cell before the ≥ 8 drop rule; **2025's `Γ_ceiling` is the
weakest number in the leg and the verdict does not rest on it** — 2023 and 2024 carry it, and both
are the *opposite sign*, which is stronger evidence than 2025's.

### 3c. Item (c) — CC_REGULAR shape emergence: **`LIVE`, and the direction is now named**

`M-c1` reproduces miso-234's object on the current keeper (agreement **EXPECTED**: the two
intervening promotions moved nothing scored). Price deciles on the Indiana-hub **RT**,
shape-normalised so every level and coverage term cancels — **no C1 claim is made**:

| year | plants | deficit as % of measured, d1 → d10 | shape deficit d1 → d10 (MW) | span | hod argmin / argmax |
|---|---:|---|---|---:|---|
| 2023 | 40 | **9.3 … 10.7 %** — flat, a pure LEVEL object | −96.6 → +134.2 | 270.8 | **0** / 3 |
| 2024 | 40 | 4.7 → 6.9 % | −63.1 → **+344.3** | 593.2 | **0** / **19** |
| 2025 | 39 | **−0.8** → 7.7 % | **−800.8** → **+454.0** | **1,254.8** | **0** / **19** |

**The direction, which the handoff named but did not fix:** shape deficit = measured − model, so
**the model runs CC_REGULAR in EXCESS overnight and SHORT at the evening peak**, and the wedge
roughly doubles each year. **`M-c2`'s pre-registered candidate set splits three ways on that:**

* **DIRECTION-ADVERSE — `gas_commitment_bridge`.** A min-gen bridge *adds* overnight CC output,
  which is the side the model already over-runs. miso-130's descriptive pool census agrees from the
  other end (3 plants / 1,601 MW of day-anchored night-off CC in July 2023, **0** in 2024 and 2025).
  **Not a candidate for (c)**; the cell stays `LIVE` in E1 because no verdict is minted.
* **`S` — the four coal/CC per-plant offer cells** (`cc_committed_offer_margin`,
  `coal_perplant_offer_level`, `coal_peak_offer_margin`, `coal_offer_net_revenue_margin`):
  structurally blocked by MISO's masked offer corpus, class bridge REFUTED at miso-138, *"do not
  charter them"* (miso-192).
* **DIRECTION-MATCHED and `LIVE` — the CC CAPACITY-BASIS family**: `cc_duct_peaking_row_scoped`,
  `cc_nameplate_summer_derate`, `cc_summer_derate_reconciled_basis`, `cc_capacity_reconcile_path`
  (and `cc_winter_capability_basis` in winter only). All `U` at MISO, all built and shipped by other
  lanes, all DOF-free in kind (published EIA-860 / eGRID rows, no fitted scalar), and all raising
  **peak-hour** CC capability without touching the overnight side.

**THE SUCCESSOR'S FIRST ZERO-LP PRE-CHECK, named and deliberately NOT run here** (running it would be
an adjudicating quantity this PREREG did not register): **does MISO's CC_REGULAR have headroom at
h19, or is it capacity-bound there?** If it has headroom, **no** capacity-basis lever can move the
shape and the whole family is inert for (c) — which would kill four arms before any LP. That is the
`rule 29` phase-0 gate this item needs.

## 4. **THE SINGLE LIVE HUNK ON THE BACKCAST SOLVE PATH — POST-HOC, LABELLED, AND IT MOVES NO CLASS**

PREREG §6 reported `G-DRIFT` as **not empty** (25 files, +1,817/−36 since the keeper's `git.sha`
`d059fcf7`, verified an ancestor of `origin/main` **after** a fetch) and explicitly left it
**unclassified**, because a zero-LP census earns and spends no control solve. **Classifying it is
therefore POST-HOC and not pre-registered.** Measured anyway, because a successor cannot assume rule
29(b) form 4 without it:

* **Exactly ONE declared default flip** landed in `d059fcf7..origin/main`:
  **`f923_gas_price_plausibility_screen` → `True`** (`203c031e`, 2026-09-08 06:40Z — **49 minutes
  after** the keeper's own solve commit; frozen cache-key drop value `"False"`).
* Three new `ScenarioConfig` fields landed; **none appears in the keeper's recorded
  `scenario_config`.** Two are default-**off** (`hydro_budget_period_by_instrument`, which the MISO
  shard's own ev measures a **byte-identical no-op** here; `netload_drag_merit_allocation`).
* `data/raw/_validation-source/actual_lmp.json` is in the changed set and **MISO's block is
  byte-identical** — only CAISO's moved — so **no MISO scored band is exposed.**

**Consequence: a MISO arm at HEAD does not get form 4 for free.** The keeper solved with the
pre-flip fuel-price construction and HEAD defaults to the post-flip one, so the keeper's committed
bundle is the control **only with `f923_gas_price_plausibility_screen` explicitly set to its frozen
drop value `False`** — otherwise the arm and the control differ by an input SPP-49 already measured
as material at MISO (**CT cheaper by $19 / $13 / $9 per MWh class-wide; CT +3.6 / +2.5 / +1.0 TWh**).

**THE ARITHMETIC SHOWING THIS MOVES NOTHING IN THE CENSUS:** `f923_gas_price_plausibility_screen` is
classified `LIVE` by the conservative default on the strength of being an unadjudicated `U` cell,
**with or without** this paragraph; no other route's class reads it; and the §3a bar, the E1 tally
and the verdict are all unchanged.

## 5. **WHAT THIS MEANS FOR THE OPEN OWNER DECISION — both sides, and the decision is not mine**

The `complete` marker authorises exactly one thing: solving, scoring and registering MISO's **2022**
validation touchpoint on the frozen keeper recipe. **This session grants, infers and recommends
nothing.** What it changes in the evidence:

**AGAINST granting on the assessment's §4 reasoning.** §4's load-bearing claim is that *"in-sample
work has stopped discriminating"*, inferred from eleven sessions arming nothing. **The census shows
those eleven sessions were all in ONE family.** miso-235 … miso-245 are seam sessions, the seam
family **is** adjudicated to exhaustion, and the SPP charter is genuinely refused for want of a
DOF-free form — **but the FUEL family and the CC CAPACITY-BASIS family are neither.** MISO's most
advanced open route is `gas_variable_transport`: owner-ruled, phase-0 sourced with **zero fitted
scalars**, field minted, and it **died on ONE gate by 37 MW** at miso-225. That is not a lane out of
in-sample instruments.

**FOR granting anyway.** MISO's untested surface is **44** against a granted-ISO median of **55**,
and **below PJM's own 60** at the moment PJM's queue was called EMPTY. A `complete` marker is
re-keyable, its spend is iterable, a validation number can never certify or decertify the ISO
(rule 30 (c)), and rule 22's touchpoint loop exists precisely to surface objects that in-sample work
has not. The open items above are reasons to keep working **either way** — none of them is a reason
the 2022 touchpoint would be uninformative.

**The honest summary in one line: MISO's queue is not empty, no granted ISO's was either, and
MISO's is smaller than four of the five.** The choice between those two readings is the owner's.

## 6. WHAT IS HANDED FORWARD

1. **THE FOUR NAMED LIVE ROUTES, in the order the evidence supports.** (i) **`gas_variable_transport`
   + `gas_marginal_commodity_pricing`** — one phenomenon (rule 19), owner-ruled, sourced, minted,
   killed on G-3 by 37 MW; the successor's question is that gate, not the charter. (ii)
   **`f923_gas_price_plausibility_screen`** — default-ON at HEAD, **untested in any MISO solve**,
   material footprint already measured, and §4 makes testing it unavoidable anyway. (iii) **the CC
   CAPACITY-BASIS family** for item (c), behind the h19-headroom pre-check of §3c. (iv)
   **`nearby_fuel_price_zone_donor_guard` / `fleet_state_from_eia860`** — MISO's exposure is the
   largest of the six.
2. **ITEM (a)'S SUCCESSOR LEG, stated so it can be pre-registered cleanly.** The identity is
   established on limb (i) in all three years; what failed is a **full-year σ** limb that six
   scarcity hours decide. A successor should register the identity limb **and** a separately-declared
   scarcity-decoupling limb (*"in the hours where they differ, `p_bus` is the last priced tranche and
   the border link binds"*), rather than one σ bar that mixes the two regimes. **I could not
   re-register that here without writing a rule around a number I had already seen.**
3. **THE `Q` SET — 6 open attribution questions with no candidate mechanism**: the SPP seam's
   spread-driven idleness, PJM's residual price alignment, **MISO's own state as an UNUSED input on
   every seam** (`R²_B` 0.12–0.18 of the measured residual on PJM and SPP, which the model reproduces
   none of, and which miso-236 named as *"cheaper to reach and requiring no new data at all"*), the
   export-leg asymmetry, and items (a) and (b).
4. **THE CENSUS'S OWN CEILING, restated.** It certifies **recorded** routes. A genuinely novel
   mechanism appears in no matrix row and in no handoff record, so E1 ∪ E2 ∪ E3 cannot reach it —
   **and PJM's census had the identical limitation.** That is the honest bound on what either
   artifact establishes.
5. **UNCHANGED AND NOT RE-TESTED** (rule 28(a)): every standing adjudication the handoff lists —
   queue item 1 CLOSED; the per-seam external-node split REFUSED; saturation REFUTED; the merit
   test's sign and basis REFUTED; `miso_manitoba_seam` CLOSED as already-armed;
   `internal_congestion_split` **G**; `measured_interface_limits` **R**; `miso_rdt_measured_limit`
   **R**; `m2m_seam_entitlement_cap` **G**; `miso_south_firm_export_block` **G**;
   `miso_south_export_ladder_rt_tail` **R**; `miso_south_gas_delivered_cost_basis` **R**;
   `miso_seam_coincident_envelope` **R**. **Nothing here re-opens any of them.**

## 7. Governance

**Rule 1** `[R-STRUCT]`: **no criterion, band or residual appears in ANY bar in this session**, in
either direction; the census's classes turn on construction, provenance and standing rules alone.
**Rule 12** `[R-PARALLEL]`: no solve. **Rule 13** `[R-MEASURED]`: no measured outcome entered
anything; every series read is a committed measured input or a committed model artifact. **Rule 14**
`[R-ACCURATE]`: the standing envelope / ladder / `K` freeze is applied as a refusal ground and is
never relaxed. **Rule 15** `[R-DASHBOARD]`: **no run was produced**, so nothing is registered and
MISO still carries exactly one registered run. **Rule 16** `[R-ALLYEARS]`: n/a, no solve. **Rules
17 / 18 / 19**: no floor, no bridge, no mechanism added; rule 19 is applied twice as a *merge*
(the two fuel cells; items (a) and (b)). **Rule 21** `[R-DOF]`: **41/2, unchanged** — zero free
parameters created. **Rule 22** `[R-HOLDOUT]`: 2023–2025 only; **no marker sought, inferred or
granted**; no out-of-training year touched. **Rule 23** `[R-FROZEN-DERIVE]`: nothing re-derived.
**Rule 24** `[R-REGISTRY]`: no field, no env knob, no CLI flag. **Rule 25** `[R-ISO-SCOPE]`: MISO's
shard, section and lane only; the cross-ISO `N_bc` measurement **reads** other shards and **moves no
cell in any of them**, which is a census, not a transfer. **Rule 26** `[R-DELETE]`: the stale `312`
literal is deleted, not widened. **Rule 27** `[R-PUSH]`: on-disk edits only; every pushed blob
≥ 300 lines verified against local after push. **Rule 28**: the handoff's recommended item taken;
every standing adjudication corroborated or untouched, never re-tested; MISO's shard alone updated
in-session. **Rule 29** `[R-SCREEN]`: zero-LP phase 0 only; no screen, no arm, no control solve — and
§4 records the one **LIVE** hunk that would earn one. **Rule 31** `[R-RETAIN]`: no bundle was
produced, so nothing is at risk of loss; see §8.

## 8. NON-CLAIMS

1. **This session grants, infers and recommends no marker**, and `complete` remains an explicit owner
   act. **§5 gives both readings and takes neither.**
2. **Zero LP.** Nothing solved, screened, registered or promoted; **no bundle exists**, so rule 31
   `[R-RETAIN]` has no object and there is no promotion question outstanding on any artifact.
3. **The keeper is unchanged** at `2026-09-08-miso-245-ladderfix`, DOF **41/2**, and **no cell verdict
   moves** on the strength of a classification — the census's classes live in the FINDING and the
   ledger, not in the shard.
4. **Two of my own gates failed** and both are published before anything they govern; **no bar was
   moved anywhere**, and the one repair deletes a literal rather than widening it.
5. **Item (a) is `UNRESOLVED` and item (b) inherits it**, notwithstanding a post-hoc reading (§0c)
   that points the other way and is used for nothing.
6. **The §3a comparison is a comparison, not a standard.** It says where MISO sits relative to the
   granted ISOs; it says nothing about whether any of those grants was correct.
7. **MISO has no failing gate**, this session did not invent one, and **C3c is untouched** — it stays
   the designated frontier and opens only by a new admissible measured identification under its own
   charter **plus an owner ruling**. **None was proposed, computed or armed here.**
8. **2025 C1/C2 are SKIPPED on the preliminary EIA-923 vintage** and no 2025 C1 pass is read as
   evidence anywhere above.
