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

*(appended after the arms completed — see below)*
