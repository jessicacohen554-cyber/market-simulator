# D-28 — How a clean-tier attribute dual composes with the IRA §45U existing-nuclear PTC

**Owner decision D-28, sitting Addendum AC.4 (2026-08-07): memo BEFORE any composition is adopted.**
**DESIGN-ONLY.** No code, no `ScenarioConfig` field, no solve, no mechanism-matrix cell was touched by
this session. The open question is FFR-6B §6.4 row 3
(`docs/handoffs/ffr-6b-rps-grain-clean-tiers-2026-08-05.md`); the consumer would be **Arm 3**
(`miso_clean_tier_rows`, landed default-OFF by FFR-7B-2, arming blocked on this question).

---

## 0. The answer in five lines

1. **The statute already decides it, and decides it twice.** §45U(b)(2)(B) is a purpose-built
   anti-stacking rule: state zero-emission-credit-program payments are **inside** the gross-receipts
   phase-down base (clause (i)), *unless* the state program itself nets out the federal credit, in
   which case they are excluded (clause (iii)). Either branch caps total support. Neither branch is
   "add them freely".
2. So **phase-down-then-add is correct — and it is self-limiting**, but only when the attribute
   payment is put **inside the phase-down basis**, which is not what "phase-down-then-add" is
   usually taken to mean.
3. **The recommended composition is `attribute = max(eac, ces, rps, clean)` (unchanged doctrine)
   `+ §45U(gross receipts = energy + attribute)`** — i.e. §45U comes *out* of the `max()`, because it
   is not an attribute buyer, and the certificate's price goes *into* §45U's basis.
4. Working the arithmetic surfaced something bigger than the composition question:
   **`policy/ira.py` applies the §45U(d)(1) 5× prevailing-wage multiplier to the 0.3¢ rate instead of
   to the net credit**, which is the opposite of what the statute and IRS-facing practice do. At MISO's
   2025 realised price this overpays existing nuclear by **$11.42/MWh ≈ $90/kW-yr against a
   $130/kW-yr going-forward bar (69 % of the bar)** — roughly **$1.04 B/yr** across the MISO nuclear
   fleet, entirely independent of Arm 3.
5. **Arming Arm 3 at MISO's $30 ACP changes nothing** — at a $30 dual all three defensible
   compositions give the identical $30.00/MWh, because the credit has fully phased out. The
   composition choice only bites at *interior* duals. **The §45U ordering defect bites everywhere.**

---

## 1. The statute, worked

Primary text read from the Office of the Law Revision Counsel US Code (uscode.house.gov, prelim
edition) and Cornell LII on **2026-08-08**. Clause numbering below is as it appears there.

### 1.1 The credit is a *net* quantity, and the 5× multiplies the net

> **§45U(a) Amount of credit.** "For purposes of section 38, the zero-emission nuclear power
> production credit for any taxable year is an amount equal to the amount by which—(1) the product
> of—(A) 0.3 cents, multiplied by (B) the kilowatt hours of electricity—(i) produced by the taxpayer
> at a qualified nuclear power facility, and (ii) sold by the taxpayer to an unrelated person during
> the taxable year, exceeds (2) the reduction amount for such taxable year."

> **§45U(d)(1).** "In the case of any qualified nuclear power facility which satisfies the
> requirements of paragraph (2)(A), the amount of the credit determined under **subsection (a)** shall
> be equal to **such amount (as determined without regard to this sentence) multiplied by 5**."

The 5× operand is *the amount determined under subsection (a)* — and subsection (a) is already
`0.3¢ × kWh − reduction amount`. **The multiplier applies after the phase-down, not to the rate.**

Corroborated independently by Crux's §45U explainer, whose worked example runs
`$0.0022 × 5 = $0.011`/kWh — i.e. it multiplies the *net* $0.0022 post-phase-down figure by five.

### 1.2 The reduction amount

> **§45U(b)(2)(A).** The "reduction amount" is the **lesser of** (i) the amount determined under
> subsection (a)(1), or (ii) **16 percent** of the excess of—
> **(ii)(I)** "the gross receipts from any electricity produced by such facility (including any
> electricity services or products provided in conjunction with the electricity produced by such
> facility) and sold to an unrelated person during such taxable year", over
> **(ii)(II)** the product of **(aa) 2.5 cents** and **(bb)** the kWh in (a)(1)(B).

Dividing through by kWh gives the per-unit form (this is exactly the model's algebra, and it is
right): `reduction/MWh = 16 % × max(0, GR/MWh − $25)`, capped at the $3/MWh gross rate. The
`lesser of` cap is what floors the credit at zero.

**Combining §1.1 and §1.2, the statutory wage-compliant credit is:**

```
§45U ($/MWh) = 5 × max(0, 3 − 0.16 × max(0, GR_per_MWh − 25))
             = max(0, 15 − 0.80 × max(0, GR_per_MWh − 25))
```

**As implemented** (`src/market_sim/policy/ira.py:24-26`, `:118-125`), the model folds the 5× into the
rate and then subtracts an unmultiplied reduction:

```
§45U_model ($/MWh) = max(0, 15 − 0.16 × max(0, P_energy − 25))
```

The phase-down slope is **5× too shallow** (0.16 vs 0.80 $/$), so the credit zeroes out at
**$118.75/MWh instead of $43.75/MWh** — a $75/MWh error in where the credit dies. See §4, F-1.

### 1.3 The crux: is state attribute/ZEC revenue inside the gross-receipts base?

**Yes by default, and the statute says so explicitly.** §45U(b)(2)(B) — heading **"Treatment of
certain receipts"** — exists for precisely this question:

> **(b)(2)(B)(i).** "Subject to clause (iii), the amount determined under subparagraph (A)(ii)(I)
> shall **include** any amount received by the taxpayer during the taxable year with respect to the
> qualified nuclear power facility **from a zero-emission credit program**."

> **(b)(2)(B)(ii).** "…the term 'zero-emission credit program' means **any payments** with respect to
> a qualified nuclear power facility **as a result of any Federal, State or local government
> program**."

> **(b)(2)(B)(iii) Exclusion.** "For purposes of clause (i), any amount received by the taxpayer from
> a zero-emission credit program shall be **excluded** from the amount determined under subparagraph
> (A)(ii)(I) **if the full amount of the credit calculated pursuant to subsection (a)** (determined
> without regard to this subparagraph) **is used to reduce payments from such zero-emission credit
> program**."

This is a two-branch anti-stacking design, and **both branches cap the total**:

| branch | condition | consequence for a unit earning a state clean/ZEC payment `D` |
|---|---|---|
| **(i) — default** | state program does **not** net out the federal credit | `D` enters gross receipts ⇒ each $1 of `D` costs **$0.80** of §45U (16 % × 5). Total = `D + §45U(P+D)`. **Self-limiting.** |
| **(iii) — exclusion** | state program **does** reduce its payments by the full federal credit | `D` leaves gross receipts, but the state pays `D − §45U` instead. Total = **`D`**. Also capped. |

**This is the direct answer to the owner's question as posed.** The memo brief asked whether, if state
attribute revenue is *outside* the base, "adding a dual on top can exceed what a real unit could
receive". It cannot — because the statute does not leave it outside the base unless the state program
has already clawed the credit back on its own side.

**Branch (iii) is real, not hypothetical.** It is the design NY's ZEC and Illinois' carbon-mitigation
credit already use (a state payment set as a target minus market/federal revenue). MISO's Arm 3 clean
tier is **not** such a program: it is an LSE compliance obligation whose certificate price is set by
the LP row's dual, with no federal-credit offset anywhere in it. **So Arm 3 is a branch-(i) program,
and branch (i) is the composition the model should implement.**

### 1.4 Genuinely unsettled points (findings, not gaps)

* **Whether an LSE-paid compliance certificate is a "payment … as a result of any … State … program".**
  (b)(2)(B)(ii) is broad — "any payments … as a result of any … State … program" — and a state clean
  standard plainly *causes* the payment. But the payer is a private LSE, not the government, which is
  the interpretive edge. **Unsettled.**
* **Treasury has issued no §45U regulations or computational guidance.** The IRS's §45U landing page
  cites exactly one item, **Notice 2022-49** — a *request for comments*. Claiming is via Form 7213,
  Part II. There is no published rule resolving the point above.
* **The industry is actively asking for that resolution.** The Large Public Power Council's
  **2026-02-17** letter to Treasury asks for clarity on "how 'gross receipts' should be calculated
  across different utility sales models (organized wholesale markets, bilateral wholesale
  transactions, and bundled retail sales)". Four years post-enactment, the base is still contested.

**How the memo treats that unsettledness:** it does not matter for the recommendation. Both readings
of the edge case cap the total — if the dual is inside the base, branch (i) phases the credit down; if
a future rule puts it outside, the model's number is then *conservative* rather than inflated, and the
error is bounded by the credit itself ($15/MWh max). The forbidden composition — naive addition with
an energy-only basis — is the one reading the statute supports under **no** interpretation.

### 1.5 Inflation adjustment (a third, smaller defect)

> **§45U(c)(1).** The 0.3¢ amount in (a)(1)(A) and the 2.5¢ amount in (b)(2)(A)(ii)(II)(aa) "shall each
> be adjusted by multiplying such amount by the inflation adjustment factor … for the calendar year in
> which the sale occurs", base calendar year **2023**. Rounding: 0.3¢ to the nearest **0.05¢**, 2.5¢ to
> the nearest **0.1¢**.

Published factors: **2025 = 1.0242** (Notice 2025-37; deflators 125.234/122.273) and
**2026 = 1.053** (Notice 2026-41, IRB 2026-29, 2026-07-13; deflators 128.986/122.39).

Applying the 2026 factor and the rounding rule: `0.3 × 1.053 = 0.3159 → 0.30¢` (rate unchanged) and
`2.5 × 1.053 = 2.6325 → 2.6¢`, i.e. a **$26/MWh** threshold rather than $25. The model hardcodes both
amounts nominal (`ira.py:22`, `:31`) with no adjustment. Effect is one-sided and modest — see §2.3.

> **Verification limit, stated rather than papered over:** the *factor* 1.053 and its deflators are
> from Notice 2026-41; I could **not** extract the notice's own printed applicable amounts (the IRB
> PDF did not parse). The 0.30¢/2.6¢ figures above are **my arithmetic from the factor and the
> statutory rounding rule**, not quoted from the notice. Any implementation should read the printed
> amounts. Same caveat on the rounding denominations themselves, which came from LII's rendering of
> §45U(c)(2) rather than a verbatim primary read.

---

## 2. Worked examples — MISO nuclear, committed data only

### 2.1 The units and which ones a clean dual would actually pay

MISO's fleet is the 10-plant / 13-unit EIA-860 operable nuclear fleet, **11,519 MW** nameplate
(`config/constants.py:2059-2062`). Arm 3 builds **two** rows (`MISO_CLEAN_TIER_REGIONS`,
`config/capacity_market.py:3219`), and the credit is **zone**-resolved, not state-resolved
(`policy/clean_tiers.py::clean_credit_for_zone`), so:

| plant | state | model zone | earns MN row? | earns MI row? |
|---|---|---|---|---|
| Monticello, Prairie Island 1+2 | MN | MISO-West | ✅ | — |
| Point Beach 1+2 | WI | MISO-West | ✅ | — |
| Clinton | IL | MISO-Illinois | ✅ | — |
| Fermi 2 | MI | MISO-East | ✅ | ✅ |
| Callaway | MO | MISO-Plains | ✅ | — |
| Grand Gulf, Waterford 3, River Bend, ANO 1+2 | MS/LA/AR | MISO-South | ❌ | ❌ |

MN's eligibility mask is `MISO_RPS_MIDWEST_FOOTPRINT_ZONES` — all five northern zones
(`capacity_market.py:3077`) — so **a Wisconsin, Illinois or Missouri reactor earns Minnesota's dual**.
Only the four southern plants are outside both rows. Worth flagging on its own terms: Arm 3 is a
northern-nuclear revenue mechanism, not an ISO-wide one.

### 2.2 Basis for the arithmetic (all committed)

| quantity | value | source |
|---|---|---|
| MISO RT ATC price, 2024 | **$30.80/MWh** | `frontend/data/backcast/bench/MISO/2024.json.gz` → `bench.avgLMP.rt` |
| MISO RT ATC price, 2025 | **$42.85/MWh** | `…/2025.json.gz` → `bench.avgLMP.rt` |
| MISO nuclear generation, 2025 | **90.7308 TWh** | `…/2025.json.gz` → `bench.classFull.nuclear` |
| MISO nuclear CF | **0.8992** | 90.7308 TWh ÷ (11,519 MW × 8760 h) |
| **⇒ $1/MWh** | **$7.88/kW-yr** | 0.8992 × 8760 ÷ 1000 |
| nuclear going-forward bar | **$130/kW-yr** | `fixed_om_nuclear`, `config/scenarios.py:2088` |
| MISO clean-row ACP ceiling | **$30/MWh** | `STATE_RPS_ACP["MISO"]`, `capacity_market.py:3011-3016` |

Nuclear runs essentially all hours, so its generation-weighted price ≈ the ATC average; the $60 row is
an **illustrative** stress level, not a measured one.

### 2.3 The four compositions

`P` = energy price, `D` = clean-tier dual. Total **attribute + §45U** revenue, $/MWh:

* **(a) naive phase-down-then-add** — `§45U_model(P) + D` (energy-only basis)
* **(b) `max(§45U, clean)`** — today's doctrine, `retirements.py:1969-1999`
* **(c) statute branch (i)** — `D + §45U_stat(P + D)` ← **recommended**
* **(d) statute branch (iii)** — `max(D, §45U_stat(P))`

| P | D | (a) add | (b) max — today | **(c) branch (i)** | (d) branch (iii) | today − (c) | today − (c) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| | | $/MWh | $/MWh | $/MWh | $/MWh | $/MWh | **$/kW-yr** |
| **30.80** (2024) | 0 | 14.07 | 14.07 | **10.36** | 10.36 | +3.71 | **+29.2** |
| 30.80 | 10 | 24.07 | 14.07 | **12.36** | 10.36 | +1.71 | +13.5 |
| 30.80 | 30 (ACP) | 44.07 | 30.00 | **30.00** | 30.00 | 0.00 | 0.0 |
| **42.85** (2025) | 0 | 12.14 | 12.14 | **0.72** | 0.72 | +11.42 | **+90.0** |
| 42.85 | 10 | 22.14 | 12.14 | **10.00** | 10.00 | +2.14 | +16.9 |
| 42.85 | 30 (ACP) | 42.14 | 30.00 | **30.00** | 30.00 | 0.00 | 0.0 |
| 60.00 (illus.) | 0 | 9.40 | 9.40 | **0.00** | 0.00 | +9.40 | +74.0 |
| 60.00 | 10 | 19.40 | 10.00 | **10.00** | 10.00 | 0.00 | 0.0 |
| 60.00 | 30 (ACP) | 39.40 | 30.00 | **30.00** | 30.00 | 0.00 | 0.0 |

**Where they diverge, and by how much:**

* **(a) is indefensible at every level** — it is the only column that exceeds what a real unit could
  receive, by $10–14/MWh ($79–110/kW-yr, up to 85 % of the whole going-forward bar). It is the
  composition the FFR-6B note feared, and the fear was justified — but the fear was misdirected: (a) is
  wrong because it uses an **energy-only basis**, not because adding is wrong.
* **(c) and (d) — the two statutory branches — never differ by more than $2.00/MWh**, and coincide
  exactly wherever the dual is large enough to phase the credit out. They are the same policy seen
  from two sides.
* **(b), today's `max()`, is exactly right at the ACP ceiling and wrong in between.** At `D = $30` it
  reproduces (c) to the cent in every price row. At `D = 0` it overstates by $29–90/kW-yr — but that
  gap is the **§45U ordering defect** (§1.1), not the composition choice.
* **The composition choice alone** — holding the ordering defect fixed — is worth **$0–2.14/MWh
  ($0–17/kW-yr)**. The **ordering defect alone** is worth **up to $11.42/MWh ($90/kW-yr)**. The second
  is 5× the first.

**Fleet-scale:** at 2025's realised price with no clean row armed, the ordering defect alone is
`$11.42/MWh × 90.7308 TWh` ≈ **$1.04 B/yr** of §45U credited to MISO nuclear that the statute does not
allow. Against 11,519 MW that is $90/kW-yr on a $130/kW-yr bar.

**2026 applicable-amount sensitivity** (§1.5, threshold $25 → $26): shifts (c) by **+$0.80/MWh**
wherever the credit is live and unphased — e.g. `P=42.85, D=0`: $0.72 → $1.52/MWh. Immaterial next to
F-1, but it is a real one-sided understatement and it grows with each year's factor.

---

## 3. Interaction audit — the full nuclear revenue stack (rule 19 checkable by inspection)

### 3.1 As the code stands today

`retirements.py` builds one nuclear unit's per-MWh attribute price in three nested `max()` folds:

```
eac_price   = max(eac_price_nuclear,                       # policy/federal_ces.py:452  (default 0.0)
                  federal_ces_premium(year) × unit_credit_fraction)   # :453-455
eac_price   = max(eac_price, §45U(P_energy_only))          # retirements.py:1964-1972
attribute   = max(eac_price, max(rps_for_unit, clean_for_unit))       # :1979-1999
                                   ↑ always 0 for nuclear (CX-6a)
```

⇒ **today's stack = `max(eac_price_nuclear, federal_ces, §45U, clean_dual)`** — a single four-way
`max()`, plus energy margin, plus the MISO capacity payment, plus reserve.

`federal_ces_replaces_state_rps` (`scenarios.py:1786`, default False) suppresses the state clean rows
exactly as it suppresses the state RPS rows, so the pure-federal counterfactual sets `clean_dual = 0`
and the stack collapses to `max(eac_price_nuclear, federal_ces, §45U)`. That half is already correct
and needs no change.

### 3.2 Under each composition

| composition | full nuclear per-MWh stack | rule 19 verdict |
|---|---|---|
| **(a) naive add** | `max(eac, ces, clean) + §45U(P)` | ❌ **Fails.** The clean certificate is paid in full *and* leaves §45U untouched — the same zero-emission attribute is monetised twice with no offset anywhere. |
| **(b) max — today** | `max(eac, ces, §45U, clean)` | ⚠️ **Passes by coincidence.** `max()` is the right doctrine *among attribute buyers*, but §45U is not an attribute buyer — it is a production tax credit with its own statutory offset. Putting it in the `max()` implements branch (iii) semantics for a program (Arm 3) that has no branch-(iii) netting. Right answer, wrong mechanism. |
| **(c) branch (i) — recommended** | `max(eac, ces, rps, clean) + §45U(GR = P + max(eac, ces, rps, clean))` | ✅ **Passes structurally.** Two distinct instruments with two distinct payers: the LSE buys the certificate, the Treasury pays the credit. The one-certificate-sold-once doctrine keeps its `max()` **unchanged** across the attribute buyers; §45U's own statutory phase-down is the anti-stacking mechanism, and it is the statute's, not ours. |
| **(d) branch (iii)** | `max(eac, ces, rps, clean, §45U)` | ✅ Passes — but only for a state program that actually nets the federal credit out. Arm 3 does not. |

**Why (c) is the rule-19-cleanest reading.** Rule 19 asks for one mechanism per *phenomenon*. There are
genuinely two phenomena here: (1) *"who buys this MWh's clean attribute"* — one certificate, several
competing buyers (state EAC, federal CES premium, RPS row, clean row), resolved by `max()`, unchanged;
and (2) *"what does the federal government pay this reactor for producing zero-emission MWh"* —
resolved by §45U, which carries its **own** statutory anti-double-dip rule keyed to phenomenon (1)'s
outcome. Collapsing them into one `max()` is what conflates two mechanisms; (c) separates them and lets
each do its own job.

**Note it preserves the existing doctrine.** (c) requires *no change* to `compute_attribute_revenue`
(`retirements.py:347-370`) and no change to the `max(eac, rps_shadow)` doctrine. It is one deletion
(§45U leaves the `max()` fold at `:1969-1972`) and one addition (the resolved attribute price joins
§45U's basis argument). Arm 3's clean dual then enters exactly where FFR-6B already put it.

---

## 4. Findings this memo surfaced (all outside D-28's own scope)

| id | finding | severity |
|---|---|---|
| **F-1** | **§45U(d)(1) 5× ordering is inverted in `ira.py`.** The multiplier is applied to the 0.3¢ rate (`ira.py:24-26`) instead of to the net credit under subsection (a). Phase-down slope is 5× too shallow; zero-out price is $118.75 vs $43.75/MWh. Worth up to **$90/kW-yr / ~$1.04 B/yr** at MISO. Corroborated by primary text **and** an independent industry worked example. | **HIGH — dominates D-28** |
| **F-2** | **The gross-receipts basis is energy-only** (`retirements.py:1964-1972` passes `avg_energy_price`). §45U(b)(2)(B)(i) requires state zero-emission-program payments in the base. Inert today (nuclear's attribute price is 0 by default) — **becomes live the moment Arm 3, `eac_price_nuclear`, or the federal CES is armed.** | MEDIUM (latent) |
| **F-3** | **No §45U(c)(1) inflation adjustment.** Both statutory amounts are hardcoded nominal (`ira.py:22`, `:31`). 2026 threshold should be ~$26/MWh, not $25. One-sided understatement, growing yearly. | LOW |
| **F-4** | **The credit is applied to `year > ira_45u_last_year` only.** §45U applies to tax years *beginning after 2023*; there is no start-year gate. Harmless for forecast years ≥2026, noted for completeness. | NONE (forecast-inert) |

F-1 and F-2 are the same fix site and should be one charter. **F-1 changes forecast nuclear retirement
economics on its own and is not gated on D-28** — it should not wait for the Arm 3 arming decision.

---

## 5. THE CARD — owner decision

### Recommendation: **adopt composition (c), branch (i) — but land F-1 first**

> **Nuclear attribute + credit revenue in the retirement screen becomes:**
>
> ```
> attribute = max(eac_price_nuclear, federal_ces_premium × fraction, rps_dual, clean_dual)
> §45U      = 5 × max(0, R_year − 0.16 × max(0, (P_energy + attribute) − T_year))
> revenue  += (attribute + §45U) × attainable_in_merit_MWh
> ```
>
> where `R_year` / `T_year` are the §45U(c)(1) inflation-adjusted 0.3¢ and 2.5¢ amounts.

**Sequencing (this is the operative part of the card):**

1. **F-1 + F-3 first, as their own charter** — statutory-compliance fix to `ira.py`, no new DOF, no
   ScenarioConfig field, affects forecast nuclear retirement economics today with Arm 3 still OFF.
2. **F-2 / composition (c) second** — the seam change in `retirements.py`, which is what actually
   unblocks Arm 3's arming.
3. **Arm 3 arming third**, on its own evidence, per the FFR-6B/rule 25 discipline.

Doing (2) before (1) would be the worst order: composition (c) with the inverted 5× still in place
(column (e) of my working: $22.47/MWh at `P=30.80, D=10` vs the statutory $12.36) is *nearly as
inflated as naive addition*, and would make the correct composition look unsafe.

**Why not keep `max()` (the rejected option), and its real cost.** `max()` is not wrong at the ACP
ceiling — at `D = $30` it reproduces the statute to the cent, so the *immediate* measured cost of
keeping it is **$0.00/MWh in the case Arm 3 is most likely to produce**. Its real costs are three:

* **$0–17/kW-yr of understatement at interior duals** (up to 13 % of the $130 bar) — small, but
  one-sided, and it lands precisely on the northern reactors Arm 3 exists to value.
* **It is right for the wrong reason**, which is the expensive part. It implements branch-(iii)
  semantics for a program that has no branch-(iii) netting. The moment any *genuine* branch-(iii)
  program is modelled (a NY-ZEC- or IL-CMC-style netting contract, which is exactly what
  `eac_price_nuclear` is documented as — "e.g. NY/IL Zero Emission Credit ~$17", `scenarios.py:1697`),
  the same `max()` would silently be doing two different statutory jobs at once with no way to tell
  them apart.
* **It permanently masks F-2.** With §45U inside the `max()`, the gross-receipts basis never has to be
  right, so the defect cannot surface through any test.

**What the winning composition would hardcode — rule 5 [R-NO-MAGIC] citations, every number:**

| value | where it would live | citation |
|---|---|---|
| 0.3 ¢/kWh base rate | `ira.py:22` (exists) | 26 U.S.C. §45U(a)(1)(A) |
| ×5 prevailing-wage multiplier, **applied to the net credit** | `ira.py:23` (exists; **operand moves**) | 26 U.S.C. §45U(d)(1) |
| 2.5 ¢/kWh threshold | `ira.py:31` (exists) | 26 U.S.C. §45U(b)(2)(A)(ii)(II)(aa) |
| 16 % phase-down rate | `ira.py:32` (exists) | 26 U.S.C. §45U(b)(2)(A)(ii) |
| inflation factor, base year **2023**; rounding 0.05¢ / 0.1¢ | new (F-3) | 26 U.S.C. §45U(c)(1)-(2); **1.0242** (2025) Notice 2025-37; **1.053** (2026) Notice 2026-41, IRB 2026-29, 2026-07-13 |
| state-program payments **in** the gross-receipts base | `retirements.py` seam (F-2) | 26 U.S.C. §45U(b)(2)(B)(i)-(ii); exclusion at (b)(2)(B)(iii) |
| termination year 2032 | `ira_45u_last_year`, `scenarios.py:2121` (exists, correct) | 26 U.S.C. §45U — no application to tax years beginning after 2032-12-31 |
| MISO clean-row ACP $30/MWh | `capacity_market.py:3016` (exists) | `STATE_RPS_ACP`, documented MISO forward-REC-ceiling proxy |
| MN / MI clean-tier targets & qualifying sets | `capacity_market.py:3219` (exists) | `MISO_CLEAN_TIER_REGIONS`; FFR-6B §6.1-§6.3 |
| nuclear going-forward bar $130/kW-yr | `scenarios.py:2088` (exists) | `fixed_om_nuclear` |

**No number in the recommended composition is fitted, swept, or identified against a residual.** Every
one is either statutory or already-cited committed config; the composition adds **zero degrees of
freedom** (rule 21 [R-DOF]).

### Decision requested

- [ ] **A — Adopt (c) with the stated sequencing** (F-1+F-3 charter → F-2/composition → Arm 3 arming). *Recommended.*
- [ ] **B — Adopt (c) but land it in a single charter** with F-1/F-2/F-3 together. Faster; costs the ability to attribute a forecast-nuclear-retirement change to the ordering fix vs the composition.
- [ ] **C — Keep `max()`, close FFR-6B §6.4 row 3 as decided-by-doctrine**, and open F-1/F-3 separately. Arm 3 unblocks immediately at zero measured cost at the ACP ceiling; accepts the three costs listed above.
- [ ] **D — Defer**, pending Treasury guidance on the (b)(2)(B)(ii) edge case. Note this is an indefinite wait: the only IRS §45U item is Notice 2022-49 (a request for comments, 2022), and LPPC was still asking for gross-receipts clarity in **2026-02**.

---

## 6. Sources

**Primary statute** — 26 U.S.C. §45U, read 2026-08-08 from
[uscode.house.gov (prelim)](https://uscode.house.gov/view.xhtml?req=%28title%3A26+section%3A45U+edition%3Aprelim%29)
and [Cornell LII](https://www.law.cornell.edu/uscode/text/26/45U). Subsections (a), (b)(2)(A),
(b)(2)(B)(i)-(iii), (c)(1)-(2), (d)(1), termination.

**IRS** — [Zero-Emission Nuclear Power Production Credit landing page](https://www.irs.gov/credits-deductions/zero-emission-nuclear-power-production-credit)
(cites only Notice 2022-49; Form 7213 Part II);
[Notice 2026-41 / IRB 2026-29](https://www.irs.gov/irb/2026-29_irb) (2026 factor 1.053);
[Notice 2025-37 summary](https://kpmg.com/us/en/taxnewsflash/news/2025/07/notice-2025-37-inflation-adjustment-factors-credits-sections-45u-45v-45z.html)
(2025 factor 1.0242).

**Industry** — [LPPC letter to Treasury on §45U guidance, 2026-02-17](https://www.lppc.org/advocacy/lppc-letter-to-treasury-on-section-45u-nuclear-tax-credit-guidance)
(gross-receipts calculation still unclarified); [Crux, "Understanding the §45U tax credit"](https://www.crux.com/insights/understanding-the-45u-tax-credit-for-existing-nuclear-power-plants)
(independent corroboration of the 5×-on-net ordering and ZEC-in-gross-receipts).

**In-repo** — `src/market_sim/policy/ira.py`, `policy/clean_tiers.py`, `policy/federal_ces.py`,
`model/capacity_evolution/retirements.py`, `config/scenarios.py`, `config/capacity_market.py`,
`config/constants.py`, `frontend/data/backcast/bench/MISO/{2023,2024,2025}.json.gz`,
`docs/handoffs/ffr-6b-rps-grain-clean-tiers-2026-08-05.md` §6.4.
