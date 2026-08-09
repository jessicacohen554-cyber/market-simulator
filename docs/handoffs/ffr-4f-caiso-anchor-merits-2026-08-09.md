# FFR-4F — CAISO's capacity-price anchor, corrected on its own rule-14 merits

**Lane.** The anchor correction FFR-3W measured, FFR-4D routed and FFR-4E's
residual pointed at — chartered under the licence both predecessors granted:
*"it may be chartered later, by someone else, on its own rule-14 merits"*
(FFR-4E §P-4 / §5.4, FFR-3W §0). Branch
`claude/ffr-4f-caiso-anchor-merits-zohaem`, based on `origin/main` **`51d4e98`**
(fetched fresh at session start; even with origin at branch time).

---

## 0. THE FRAMING STATEMENT — binding, and it comes first

**THIS IS NOT A ROW-4 FIX.**

FC-2 row 4's movement is **REPORTED as a side effect** of this correction. It is
never claimed as the objective, never quoted as this lane's success metric, and
never offered as the justification for the mechanism.

The owner **declined the capacity anchor AS A ROUTE to row 4** (D-15's charter).
That refusal is honoured here in the only way that means anything: the lane's
claim — that the shipped anchor is the wrong object and the RA Market Price
Benchmark is the right one — is established **entirely from published market
design and rule 14 `[R-ACCURATE]`**, in §§1–3, *before* any arm is solved, and
**no solve outcome can validate or invalidate it**.

FFR-3W §5.3 named the trap in advance, and this document adopts it as a
pre-registered decision rule (§4, R-4/D-2):

> Correcting the `gas_ct` term would move row 4 **just as far** — by building
> *the same 14 GW of CTs California does not need* through the economic channel
> rather than the administrative one. **Row 4 would read PASS while the model
> still over-builds 14 GW of firm capacity into a market that is already long.**

So the single most important measurement in this document is **not** row 4. It
is the **entry-build composition** (§4 R-2/R-4): whether the 14 GW the old
anchor manufactured *dissolves*, or merely *changes channel*. If it merely
changes channel, this document says so, in those words, and does not present
row 4's movement as a win.

**Why the lane exists at all.** Two completed lanes isolated the residual to
this object — FFR-4D corrected the base-year **fleet vintage**, FFR-4E
corrected the **storage accreditation**, and row 4 still FAILs at 41.68 % with
both right (FFR-4E §5.4) — *and* the anchor is mis-specified **on its own
terms**, which is a rule 14 defect whatever it does to any gate.

---

## 1. What CAISO and CPUC actually publish — the first-party intake

Committed in `ffr-4f: intake CAISO's published RA capacity-price objects`
(`data/raw/capacity-market/demand-curve/caiso/`), with the source PDF alongside
the CSV so nothing here needs a re-fetch to re-derive.

### 1.1 There is no net-CONE, and that is structural

**CAISO publishes NO net-CONE and no new-entry capacity price, by technology or
otherwise.** It runs no centralized capacity auction and no sloped demand curve
— RA is procured bilaterally under CPUC jurisdiction — so the object our
registry slot is *named* after does not exist for this ISO. It is
**structurally absent, not un-fetched**. The repo already recorded half of this
(`capacity-market/auction-price/caiso/README.md`: "expected empty — no
centralized auction"); §1.2 completes it.

The charter asked for "published net-CONE by technology if it exists". It does
not exist. That is the finding, and it is why this is a rule 14 *misalignment*
case (document + reconcile) rather than a substitution.

### 1.2 The CPM soft-offer cap — a RETENTION price, by design

The shipped anchor `net_cone_per_kw_yr=88.08` is the CPM soft-offer cap, whose
provenance is carried verbatim in our own committed source row (FERC
ER24-1225-000 letter order, 187 FERC ¶ 61,032, effective 2024-06-01):

> *"$73.41/kW-yr **going-forward fixed cost** of 550 MW **CC** reference unit ×
> 1.20 = $88.09/kW-yr = $7.34/kW-month"*

Three category errors, each established from the source document's own words
and **none of them a residual argument** (this is FFR-3W §2.3, verified here
against the first-party design rather than re-derived):

| # | mismatch | why it is a category error for an ENTRY screen |
|---|---|---|
| **a** | **going-forward cost, not entry cost** | going-forward fixed cost is FOM + sustaining capital for an **existing** unit and contains **no capex annuity by construction**; the screen compares it against a new-entry gross fixed cost that is **78.2 % capex annuity** |
| **b** | **CC reference unit, not CT** | derived from a 550 MW **combined-cycle**; the candidate is a frame **combustion turbine** — different capex/kW, FOM/kW, duty cycle |
| **c** | **an administrative CEILING, not a price** | it caps what a CPM-designated resource may *offer* into CAISO's **backstop**; it is not what any resource is paid in the ordinary market |

**Two first-party confirmations this session adds.**

1. **(a) holds at the DESIGN level, not merely in this vintage's arithmetic.** A
   resource may offer *above* the cap only by cost-justifying to FERC **on its
   own going-forward fixed costs, "using the same cost categories used to
   establish the CPM soft offer cap"**. CPM compensation is a retention-price
   structure *end to end* — there is no path through it that prices new entry.
2. **(c) is measurable in our own committed data.** All **five** 2023 CPM
   designations cleared at **exactly** the then-effective cap ($6.31/kW-mo),
   on ≈256 MW of last-resort procurement
   (`capacity-market/auction-price/caiso/caiso.csv`). Every designation pinned
   to the ceiling is what a binding regulatory cap looks like — not a price
   discovered by competing bids.

*(Minor: trade press reports the 2024 cap as $7.32; our committed primary — the
FERC letter order's own arithmetic, $88.09/kW-yr ÷ 12 — gives **$7.34**. The
committed value is right.)*

### 1.3 What IS published: the CPUC RA Market Price Benchmark

The registry slot's real job is not "net-CONE"; it is **the price a firm MW of
CAISO RA is paid** — that is what all five consumers multiply by their
accreditation. CPUC publishes exactly that, on a **forward delivery year**:

The **PCIA Resource Adequacy Market Price Benchmark** — the volume-weighted
average of **all IOU, CCA and ESP RA market transactions** for a stated
**delivery** year, unified into a **single** RA value (no system/local/flexible
split) by **D.25-06-049 OP 1**, issued every October by CPUC Energy Division
under **D.22-01-023**.

| row | delivery | transactions executed | value |
|---|---|---|--:|
| **2026 Forecast — ADOPTED** | **2026** | 2022-12 → 2025-08 | **11.53 $/kW-mo = 138.36 $/kW-yr** |
| 2025 Final | 2025 | 2021-12 → 2025-08 | 11.21 $/kW-mo = 134.52 $/kW-yr |

*Source: CPUC "Market Price Benchmark Calculations 2025", 2025-10-01, p.1
Tables 1–2 + methodology p.3; PDF committed.*

The **2026 Forecast** vintage is adopted because the model's forecast base year
is 2026 and that row is the published **forward-delivery** price.

**Corroboration — four published CPUC values, two independent publications:**

| source | value ($/kW-mo) |
|---|--:|
| RA MPB 2026 Forecast (adopted) | 11.53 |
| RA MPB 2025 Final | 11.21 |
| RA Report transacted, 2023 system | 11.10 |
| RA Report transacted, 2025 system | 11.87 |
| *(RA Report transacted, 2024 system — high outlier)* | *14.51* |

Everything except the 2024 outlier sits inside **11.10–11.87**, against the
cap's **7.34**. Two CPUC publications, built from different transaction
windows, converge on the same number.

### 1.4 Rule 13 `[R-MEASURED]` admissibility

The MPB is a measured **input**, not a measured **outcome**. Rule 13's test —
*could this same quantity be produced for a forward year from forward drivers,
and would it respond to changed conditions?* — is met explicitly: CPUC Energy
Division publishes it **every October for the next delivery year** under a
standing decision, and it is a transaction-weighted average that moves with the
market. Nothing is pinned to a model residual.

---

## 2. The rule 14 misalignment reconciliation

FFR-3W §4 filed two objections against this replacement and refused to supply
it from a diagnosis lane, requiring "a **reconciled** intake (NQC-vs-UCAP basis
pairing; existing-weighted average vs new-entrant price), not a substitution".
Both are reconciled here — **not** guessed at, and neither is closed by an
adjustment fitted to anything.

### 2.1 "A whole-market average dominated by EXISTING resources is not a new-entrant price"

**Reconciled: a real property of the object, but not a defect for this slot.**

CAISO RA is a **fungible bilateral product**. A System RA MW from a new CT and
one from an existing CC are the same product and transact at the same price;
CAISO has **no vintage-differentiated RA price** because it has no auction in
which new entry sets a clearing price. So the transacted average *is* what a
new entrant is paid for its RA attribute.

The objection's real content is the worry that the RA price may be **too low to
call forth new entry**. But that is a **market outcome the screen exists to
report**, not an input to be adjusted. Grossing the price up until entry turns
profitable would be tuning an input to produce a desired output — rules 1
`[R-STRUCT]` and 13 `[R-MEASURED]` — and it is **deliberately not done**.

Consequence, stated before measuring: **the corrected anchor does not guarantee
the CT flips profitable.** FFR-3W §2.1 puts the CT break-even at
**10.88–11.36 $/kW-mo**, and the adopted anchor is **11.53** — astride that
band, not comfortably above it. The screen may still return `unprofitable` in
later horizon years as energy margin collapses.

### 2.2 "The price is per NQC kW; the screens apply a UCAP accreditation"

**Reconciled by measurement, and the residual is left uncorrected on purpose.**

The RA price is per kW of **NQC**. The screens compute
`price × accreditation_fraction × pmax`, where the fraction is `1 − EFORd`
(**UCAP**). The question is whether those two bases are compatible enough to
pair, and it is answerable from committed data rather than assumption:

| quantity | value | source |
|---|--:|---|
| CAISO published gas-class **NQC / NDC** | 25,866 / 26,958 = **0.9595** | 2026 SLRA Table 1.1, `capacity-market/loads-resources/caiso/` |
| model `1 − EFORd`, **gas_ct** | **0.9400** | `constants.EFORD` |
| model `1 − EFORd`, **gas_cc** | **0.9500** | `constants.EFORD` |

Pairing an NQC-basis price with the model's UCAP fraction therefore
**UNDER-credits** thermal capacity revenue by **≈2.0 %** (CT) / **≈1.0 %** (CC).

That residual is **conservative** (it under-pays, so it cannot flatter entry),
and it is **two orders of magnitude below** the 57 % price error being
corrected. It is left **uncorrected deliberately**: inventing a gross-up would
be a second, unmeasured mechanism (rule 19 `[R-ONE-MECH]`) fitted to nothing.
Documented rather than buried — rule 14's misalignment clause exactly.

---

## 3. What landed, and the keeper guard

### 3.1 The mechanism

`ScenarioConfig.caiso_ra_mpb_capacity_anchor` — **GATED, default-OFF**.
`config/capacity_market.py::resolve_caiso_ra_mpb_anchor` →
`CAISO_RA_MPB_ANCHOR_PER_KW_YR = 138.36`, resolved **inside**
`MarketDesign.capacity_price_per_firm_mw_yr` ahead of the curve branch, so it
**REPLACES** the anchor rather than stacking on or re-anchoring a curve
(rule 19 `[R-ONE-MECH]`).

### 3.2 Keeper guard — consumers enumerated, then the gate

The charter requires enumerating the consumers and either proving the CAISO
backcast keeper byte-inert or keeping the gate. **Five** consumers reach this
seam, and **every one threads `iso`** — verified by inspection — so the gate
can never fire for some screens and not others:

| # | consumer | site |
|---|---|---|
| 1 | retirement screen | `capacity_evolution/retirements.py:859` |
| 2 | thermal entry | `capacity_evolution/new_entry.py:1114` (via #1) |
| 3 | VRE entry | `capacity_evolution/new_entry.py:1246` |
| 4 | storage entry | `model/storage.py:1487` |
| 5 | plant-financials capacity revenue | `results/plant_financials.py:537` |

The CAISO **backcast keeper reaches this seam** through #1 and #5, so
byte-inertness is **NOT available by inspection**. The charter's second branch
is taken: **the gate stays default-OFF**, which makes keeper inertness hold
**by construction** rather than by measurement — the same posture, for the same
reason, as its FFR-4E sibling.

**Measured, and it identifies the seam:** gate-off CAISO `gas_ct` capacity
revenue is **82,795.2 $/MW-yr**, which reproduces **FFR-3W §1.2's capacity
column ($82,795) to the dollar** — confirming this is the same object that lane
decomposed. Armed it is **130,058.4**.

Pinned by `tests/unit/config/test_caiso_ra_mpb_anchor.py` (11 tests): gate-off
byte-identity, armed value, all five other ISOs byte-identical at both the seam
and the retirement screen, resolver CAISO-only (including a `None` config),
source-traceability of the constant to the committed CSV, and both cache keys.

### 3.3 Cache-key-pin verdict — **PASS**

| | |
|---|---|
| pinned default key | **`603c2498bf71d21d`** — **UNMOVED** (measured) |
| armed key | `bb8050a8368985df` — distinct |
| cache epoch needed? | **No.** Byte-identical at its default, so this is not a same-key invalidation |

`scripts/check_cache_key_registration.py`: *ok — 709 fields, 156 registered, all
resolve; 156 declared defaults all match HEAD.* Field,
`_CACHE_KEY_OPTIONAL_FIELDS` entry, defaults-ledger entry and mechanism-matrix
row all landed in **one commit**.

---

## 4. PRE-REGISTRATION — written and committed BEFORE either arm was solved

Committed in `ffr-4f: pre-register the paired FC-2 read` so nothing below can
be read as post-hoc. Results are appended in §5 afterwards.

### P-1. Arms

Both cold at this head, `scripts/run_full_horizon.py --iso CAISO --start-year
2026 --end-year 2030` — **5 solve-years, sequential inside one invocation**
(rule 12 `[R-PARALLEL]`), separate `--out-dir`s. Prereqs `uv sync` +
`scripts/regenerate_clean.py` completed first.

| arm | config |
|---|---|
| **control** | HEAD default (gate off) |
| **treated** | `--caiso-ra-mpb-capacity-anchor`, nothing else changed |

**Predicted control: FFR-4E's CONTROL arm — 8,186.3 MW backstop / 52.51 %
row 4.** Stated before solving; §5 reports what actually came back. A control
that does *not* reproduce it means the baseline moved, and the comparison is
re-based before anything is concluded.

**Why the control is 52.51 % and not FFR-4E's headline 41.68 %** — worth
stating precisely, because the charter quotes the latter. FFR-4E's 41.68 % was
measured with `caiso_storage_nqc_accreditation` **ARMED**, and that flag ships
**default-OFF** with its arming posture explicitly reserved as an OWNER
decision (FFR-4E §7 E-2, because arming it moves the designated backcast
keeper). So HEAD defaults reproduce FFR-4E's **control**, not its treated arm.

This lane therefore does **not** arm it: doing so would (i) arm a mechanism
whose posture is owner-pending, and (ii) confound two variables in one A/B.
The arms isolate the anchor **alone**, which is the only way the measurement
attributes anything to the anchor. The consequence for reading §5 is stated
here rather than discovered later: **this lane's control sits 10.8 pp above the
one the charter quotes**, so row-4 numbers here are not directly comparable to
FFR-4E's treated arm, and the two corrections are **not** additive without a
third arm nobody has run.

### P-2. The reads, all reported at full magnitude

* **R-1 — ALL FC-2 rows**, both arms, scored by `scripts/forecast_verdict.py
  --tier t1f`, **not by hand**. Every row reported, not only the ones that move.
* **R-2 — entry-build composition**, per year and cumulative: economic thermal
  entry MW, reserve-backstop thermal MW, renewable MW, storage MW.
* **R-3 — retirement composition**: economic retirement MW per arm. The anchor
  feeds the retirement screen too, so this is a real and separate channel.
* **R-4 — THE TRAP TEST: total thermal MW built (economic + backstop).**
* **R-5 — adequacy ledger**: accredited firm, requirement, reserve margin,
  invariants I7/I12.
* **R-6 — row 4**, reported **among** R-1's rows, without emphasis.

### P-3. Decision rules

* **D-1 — the lane's claim does not depend on any of this.** §§1–3 establish
  that the shipped anchor is the wrong *kind* of object and that the RA MPB is
  the published price of the quantity the slot needs. **No solve outcome can
  validate or invalidate that.** A solve measures *consequences*, not
  faithfulness.
* **D-2 — the trap rule (R-4).** If row 4 improves while **total thermal build
  is roughly unchanged**, then the improvement is **channel substitution** —
  precisely the FFR-3W §5.3 trap — and this document **says so in those words**
  and does **not** present it as a lane success. Row 4 reading better while the
  model still over-builds firm capacity into a long market is a rule 1
  `[R-STRUCT]` failure, not a result.
* **D-3 — adverse results are reported identically.** If the corrected anchor
  makes row 4 (or any other row) **worse**, it is reported at the same
  magnitude and the same prominence, and the mechanism **still stays merged**:
  rule 1 forbids reverting a structurally-correct published input because it
  moved a residual the wrong way, and rule 14 forbids reverting to the estimate
  because the estimate fit better.
* **D-4 — no further lever after the result.** Whatever §5 shows, no additional
  mechanism is armed, no parameter is re-picked, and the arming posture remains
  an **OWNER decision** (rules 5/24/28).
* **D-5 — rule 25.** CAISO's lane. No other ISO's anchor, verdict or parameter
  is read, changed or transferred.

---

## 5. Results

Both arms cold at this head, 2026–2030, 5 years sequential, exit 0.
`results/ffr4f/{caiso-control,caiso-treated}`.

| arm | runtime key | armed flag in `config.yaml` |
|---|---|---|
| control | **`3d3e836a176ac9cd`** | `caiso_ra_mpb_capacity_anchor: false` |
| treated | **`da19509d457988e5`** | `caiso_ra_mpb_capacity_anchor: true` |

**The control is verified by key identity, not just by matching numbers.**
`3d3e836a176ac9cd` is **exactly FFR-4E's control runtime key** — the resolved
configs are identical, so this *is* that baseline, and P-1's prediction
(8,186.3 MW / 52.51 %) is confirmed to the digit. The treated key differs, so
the flag demonstrably took effect.

### 5.1 R-1 — ALL FC-2 (and every other FC) row, both arms, at full magnitude

Scored by `scripts/forecast_verdict.py --tier t1f`, **not by hand**.
**Determination: HOLD in BOTH arms.**

| category / row | control | treated |
|---|---|---|
| **FC-1** structural integrity (I1–I14) | **FAIL** `['I12','I7']` | **FAIL** `['I12','I7']` — **worse** |
| **FC-2 row1** reserve-margin band (I12) | **FAIL** 2026 12.9 %, 2027 **7.7 %**, 2028 **10.3 %** | **FAIL** 2026 12.9 %, 2027 **5.9 %**, 2028 **8.5 %** — **worse** |
| **FC-2 row4** backstop share | **FAIL** **52.5 %** | **FAIL** **46.1 %** — better |
| FC-2 rows 2/3/5/6 | not applicable at t1f (T2/T3 drift; curve-ON; ERCOT-only) | same |
| FC-3 / FC-4 | n/a | n/a |
| FC-5 external corridor | SKIPPED (no committed corridor table) | SKIPPED |
| FC-6 driver response | SKIPPED | SKIPPED |
| FC-7 provenance & DOF | **FAIL** `run_config` + CAVEAT dof ledger | identical |
| FC-8 runtime feasibility | **PASS** | **PASS** |

*FC-7's `run_config.json absent` is a scorer path artifact, not a lane finding:
the file exists at `results/ffr4f/<arm>/run_config.json` and the scorer looks
elsewhere. It is identical in both arms and cancels from the comparison.*

**I7 shortfall deepens in the treated arm:** 2027 accredited firm
54,969 → **54,019** MW, 2028 57,621 → **56,671** MW (requirement unchanged at
58,671 / 60,082).

### 5.2 R-2/R-3/R-4 — the entry-build composition, and **the trap test**

Cumulative over 2026–2030 (MW):

| arm | thermal | ├ backstop | └ economic | renewable | storage | **TOTAL ADD** | retirements |
|---|--:|--:|--:|--:|--:|--:|--:|
| control | **10,186.3** | 8,186.3 | 2,000.0 | 5,404.4 | 0.0 | **15,590.7** | 2,615.3 |
| treated | **10,186.3** | 7,186.3 | 3,000.0 | 5,404.4 | 0.0 | **15,590.7** | 2,615.3 |
| **Δ** | **+0.0** | **−1,000.0** | **+1,000.0** | +0.0 | +0.0 | **+0.0** | +0.0 |

> ### **R-4, THE TRAP TEST: D-2 FIRES. The answer to the charter's question is NO.**
>
> **Does the CT build the old anchor manufactured dissolve? Not one megawatt.**
> Total thermal built is **identical to the megawatt** — 10,186.3 MW in both
> arms — as are total additions (15,590.7), renewables (5,404.4), storage (0.0)
> and retirements (2,615.3). **The only thing that changed is the label on
> 1,000 MW**: backstop −1,000.0, economic +1,000.0, a 1:1 substitution.
>
> Row 4 improves 52.51 % → 46.09 % **solely because 1,000 MW moved from the
> numerator's channel to a channel the numerator does not count.** The
> denominator is untouched. This is exactly, and only, the channel substitution
> **FFR-3W §5.3 predicted**, and per pre-registered **D-2** it is reported as
> such and is **NOT presented as a success of this lane**.

**Per-year — and the substitution is also a two-year DELAY:**

| year | control thermal | treated thermal | Δ | control RM | treated RM |
|---|--:|--:|--:|--:|--:|
| 2026 | 0.0 | 0.0 | — | 12.92 % | 12.92 % |
| **2027** | **1,396.4** | **396.4** | **−1,000.0** | **7.74 %** | **5.88 %** |
| 2028 | 2,792.8 | 2,792.8 | — | **10.29 %** | **8.47 %** |
| **2029** | **4,146.5** | **5,146.5** | **+1,000.0** | 16.60 % | 16.60 % |
| 2030 | 1,850.5 | 1,850.5 | — | 15.24 % | 15.24 % |

The 1,000 MW that the administrative channel delivered in **2027** is delivered
by the economic channel in **2029** — the arms re-converge exactly from 2029
(total capacity 93,589 MW in both at 2030). Corroborated in the evolution
ledgers: 2029 `entry_decided_mw_by_tech['gas_ct']` is 2,146.5 (control) vs
**3,146.5** (treated).

**So the treated arm buys row 4's 6.4 pp by making adequacy WORSE**: the same
capacity, two years later, deepening the 2027–28 trough (row1 and I7 above).
Per **D-3** that is reported at the same magnitude and prominence as the row-4
improvement — and it is the more decision-relevant half.

**R-3, the retirement channel, is inert here.** The anchor also feeds the
retirement screen, but retirements are **identical** in both arms (1,492.5 MW
in 2027, 0.8 in 2028, 1,122.0 in 2030). No CAISO unit's retirement decision
flips between $88.08 and $138.36/kW-yr in this window, so the whole effect
above runs through entry alone.

### 5.3 What this does and does not say about the mechanism

**It does not impeach the correction.** Per pre-registered **D-1**, the lane's
claim is that the CPM soft-offer cap is the wrong *kind* of object and the RA
MPB is the published price of the quantity the slot needs. That rests on §§1–3
— published market design, first-party intake, and the rule 14 reconciliation —
and **no solve outcome can validate or invalidate it**. §5 measures
*consequences*, not faithfulness. Per **D-3** the mechanism therefore **stays
merged**: rule 1 `[R-STRUCT]` forbids reverting a structurally-correct
published input because it moved a residual the wrong way, and rule 14 forbids
reverting to the estimate because the estimate scored better.

**What it does say — and this is the finding worth carrying forward.**
The corrected anchor makes exactly **one** additional 1,000 MW block of
merchant `gas_ct` viable across five years, and then stops. That is the
**self-limiting behaviour FFR-3W §2.1/§5.2 predicted**: the adopted anchor
(**11.53 $/kW-mo**) sits *astride* the CT's break-even band
(**10.88–11.36 $/kW-mo**), and the energy-margin ratchet lifts break-even as
CTs enter, so entry clears once and closes. §2.1's pre-registered consequence —
"the corrected anchor does not guarantee the CT flips profitable" — is what
actually happened, at the smallest non-zero scale the rate ladder permits.

**And it sharpens FFR-4E's E-1 rather than answering it.** With the fleet right
(FFR-4D), the accreditation right (FFR-4E) *and* the capacity price right
(here), CAISO adequacy in 2026–2030 is **still met administratively**:
economic entry supplies 3,000 of 10,186.3 thermal MW, storage entry supplies
**0.0 MW in both arms across the whole horizon**, and the backstop still
carries 7,186.3 MW. Correcting the price moved 1,000 MW; it did not change the
regime. **The residual is not the anchor's level either** — three corrections
have now each been isolated and none dissolves the over-build.

### 5.4 Nothing was tuned to the result

The anchor value was fixed in §1.3 from two published CPUC figures and
committed **before** either arm was solved (commit
`ffr-4f: intake CAISO's published RA capacity-price objects`, which precedes
both solves), and was not revisited afterwards. The NQC-vs-UCAP residual
(§2.2) is left uncorrected in the adverse-to-nothing direction. No parameter
was re-picked after the read, and per **D-4** no further lever was pulled.

### 5.5 Registration

Rule 15: forecast-family runs go on the **forecast** dashboard, never the
backcast registry. Both arms registered via `scripts/register_forecast_run.py`
(the single registration path) as
**`caiso-2026-2030-ffr4f-caiso-control`** and
**`caiso-2026-2030-ffr4f-caiso-treated`**. The slim artifacts
(`full_horizon_summary.json`, `run_config.json`, per-year evolution ledgers)
are committed so §5's table is auditable without a re-solve; only the
regenerable per-year dispatch parquet is gitignored, exactly as its FFR-4E
sibling.

---

## 6. Open items, routed not fixed

| id | item | why not here |
|---|---|---|
| **F-1** | **The over-build regime survives all three corrections.** Fleet (FFR-4D), accreditation (FFR-4E) and capacity price (here) have each been isolated; row 4 is 52.51 % at HEAD and no single correction takes it below 46 %. Storage entry is **0.0 MW across the whole horizon in every arm anyone has run**, which is the loudest unexplained signal left. | Not this lane's object. A storage-entry lane (why the value stack never clears in CAISO) is the natural successor and is a *different* mechanism from the three now measured. |
| **F-2** | **Economic entry and the backstop deliver on different timelines**, so substituting one for the other moves capacity two years later and deepens the near-term adequacy trough (§5.2). Whether that lag is the right representation of a merchant CT's development time vs a backstop procurement is unexamined. | A commissioning-lag question (`entry_commissioning_lag`), not an anchor question. It would change every ISO's forecast, so it needs its own charter and cannot be judged from one CAISO pair. |
| **F-3** | **Arming posture for `caiso_ra_mpb_capacity_anchor` is an OWNER decision** (rules 5/24/28). The mechanism is built, measured, default-OFF and keeper-inert by construction. Arming it in the forecast lane costs 1.9 pp of 2027 reserve margin and buys 6.4 pp of row 4; arming it in the backcast lane would move the designated keeper and needs a re-solve + re-gate. | Exactly its FFR-4E sibling's posture (E-2), for the same reason. |
| **F-4** | **The NQC-vs-UCAP ~2 % under-credit (§2.2) is documented, not corrected.** | Correcting it needs its own measured basis-conversion, not a gross-up invented here (rule 19). |
| **F-5** | **FC-7 `run_config.json absent`** — the scorer looks for it somewhere other than `results/ffr4f/<arm>/run_config.json`, where `run_full_horizon.py` writes it. Identical in both arms, so it cancels from this comparison, but it means **every** `run_full_horizon` pair scores a spurious FC-7 FAIL. | A scorer/runner path mismatch affecting all ISOs and all forecast pairs — not CAISO's lane, and fixing it here would be an unchartered change to shared scoring infrastructure. |

---

## 7. Governance

* **The framing the charter made binding — honoured.** §0 states it, §4 D-2
  pre-registers it, and §5.2 executes it: row 4's 6.4 pp improvement is
  reported as **channel substitution**, explicitly **not** claimed as this
  lane's objective, success metric or justification. The mechanism's case is
  made in §§1–3 from published market design alone. The owner's refusal of the
  anchor *as a route to row 4* is intact: this document reaches the opposite of
  the conclusion that route was declined for — it reports that the route
  **does not work**, and would have been a rule 1 `[R-STRUCT]` trap if it had.
* **Rule 1 `[R-STRUCT]` / rule 11.** Nothing is tuned to a residual. The
  correction makes I12/I7 **worse** and is adopted anyway; the mechanism stays
  merged on faithfulness, not fit.
* **Rule 5 `[R-NO-MAGIC]`.** Every number traces to a committed primary. The
  legacy per-IOU MPBs were **not** transcribed because their merged-cell
  alignment is ambiguous — a refusal to guess, recorded in the README.
* **Rule 13 `[R-MEASURED]`.** The MPB is a measured market **input** published
  annually for a forward delivery year under a standing CPUC decision, not a
  measured outcome. No model output is pinned to anything (§1.4).
* **Rule 14 `[R-ACCURATE]`.** The whole charter. The accurate published input
  replaces the estimate; both of FFR-3W §4's objections are **reconciled**
  (§2), and the residual basis mismatch is documented rather than buried.
* **Rule 19 `[R-ONE-MECH]`.** The anchor **replaces**; it does not stack. Five
  consumers, one seam, all threading `iso` (§3.2).
* **Rule 22 `[R-HOLDOUT]`.** Forecast-mode 2026–2030 only. No out-of-training
  year was solved, scored, read or approached; CAISO holds no marker and none
  was written.
* **Rule 24 `[R-REGISTRY]`.** A `ScenarioConfig` field landing in
  `run_config.json`. No env var, no per-plant dict, no `getattr` fallback
  literal.
* **Rule 25 `[R-ISO-SCOPE]`.** CAISO only. The resolver returns `None` for
  every other ISO, pinned by tests measuring all five as byte-identical at both
  the seam and the retirement screen. No other ISO's anchor or verdict was
  read, changed or transferred.
* **Rule 27 `[R-PUSH]`.** Opus. Every change is a local `Edit` of on-disk
  bytes; no file ≥300 lines was rewritten from generated content. All three
  ≥300-line files were blob-verified against local after push
  (`capacity_market.py`, `scenarios.py`, `mechanism-matrix.js` — all MATCH).
* **Rule 28 `[R-MECH-MATRIX]`.** Row minted with its field (duty c) and its
  forecast cell adjudicated by solve in the same session (duty b).
* **Cache.** Pinned default `603c2498bf71d21d` **unmoved**; armed
  `bb8050a8368985df`. Byte-identical at default ⇒ **no cache epoch**.
* **Rules 15/16.** Forecast-family runs, registered on the **forecast**
  dashboard only (§5.5). No backcast run was produced, and the backcast
  registry is untouched.

---

## 8. Reproduction

```bash
uv sync                                    # ~2 min
uv run python scripts/regenerate_clean.py  # ~55 min, 50 datatypes, 1.6 GB

# the mechanism, solve-free
uv run python -m pytest tests/unit/config/test_caiso_ra_mpb_anchor.py -q
uv run python scripts/check_cache_key_registration.py
uv run python scripts/check_mechanism_matrix.py

# the anchor's effect at the seam, no solve
uv run python -c "
from market_sim.config.scenarios import ScenarioConfig
from market_sim.config.constants import EFORD
from market_sim.model.capacity_evolution.retirements import capacity_revenue_per_mw_yr
for arm, cfg in [('off', ScenarioConfig()),
                 ('on', ScenarioConfig(caiso_ra_mpb_capacity_anchor=True))]:
    print(arm, capacity_revenue_per_mw_yr('CAISO','gas_ct',EFORD['gas_ct'],cfg,None))
"

# the paired arms (5 years each, sequential; run the two concurrently — rule 12)
MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
  uv run python scripts/run_full_horizon.py --iso CAISO \
    --start-year 2026 --end-year 2030 --out-dir results/ffr4f/caiso-control
MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
  uv run python scripts/run_full_horizon.py --iso CAISO \
    --start-year 2026 --end-year 2030 --caiso-ra-mpb-capacity-anchor \
    --out-dir results/ffr4f/caiso-treated

# the scored reads
for arm in control treated; do
  uv run python scripts/forecast_verdict.py \
    --summary results/ffr4f/caiso-$arm/full_horizon_summary.json --tier t1f
done
```
