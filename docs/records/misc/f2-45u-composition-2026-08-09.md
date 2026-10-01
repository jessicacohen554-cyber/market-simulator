# F2-45U — the §45U gross-receipts composition seam

**Owner decision D-28 option A, sequencing step 2 of 3.** F-1 + F-3 landed first
(PR #3746, merged `6c3b551`, `docs/handoffs/f1-45u-ordering-2026-08-08.md`). This charter is the
`model/capacity_evolution/retirements.py` seam ONLY. **Arm-3 arming is the next charter and was
not performed here** — `miso_clean_tier_rows` stays default-OFF.

Authority: `docs/handoffs/d28-45u-composition-memo-2026-08-08.md` §1.3 (the two-branch
anti-stacking design), §3 (the interaction audit), §5 (the signed card); and
`docs/handoffs/f1-45u-ordering-2026-08-08.md` §7 (what F-1 deliberately left).

---

## 0. The answer in five lines

1. **§45U left the attribute `max()`.** It is not an attribute buyer — it is a production tax
   credit carrying its own statutory anti-double-dip — so it now composes with the winner of the
   (unchanged) `max(eac, ces, rps, clean)` fold instead of competing inside it.
2. **Branch assignment is PER INSTRUMENT**, which is the part the memo's own §5 card flattened.
   LSE-paid compliance certificates (Arm-3 clean dual, federal CES premium, RPS dual) are
   **branch (i)** — inside gross receipts, paying `D + §45U(P + D)`. `eac_price_nuclear` is the
   documented NY-ZEC / IL-CMC netting design, so it is **branch (iii)** — excluded from the base,
   paying `max(D, §45U(P))`.
3. **The composition choice is worth $0.00 at the $30 MISO ACP ceiling** (to the cent, at both
   committed price bases) and **at most $2.07/MWh ($16.22/kW-yr)** over all duals — *smaller* than
   the memo's nominal-curve $0–2.14/MWh, because F-1/F-3 already steepened the phase-down under it.
4. **Stage 2 SKIPPED.** No unit crosses the $130/kW-yr `fixed_om_nuclear` bar under any
   composition, settled in CF space rather than at two price points; and at `D = 0` — every
   shipped config — the new seam is **identical** to HEAD.
5. **Notable side-result:** post-F-1, HEAD's `max()` is byte-for-byte **branch (iii)** at every
   grid point. The memo's "right for the wrong reason" diagnosis is now measurable, not rhetorical.

---

## 1. The statutory read on §45U(b)(2)(B)

`§45U(a)` is a *net* quantity and `(d)(1)`'s 5× multiplies that net — settled by F-1 and not
re-litigated here. What F-2 settles is the **base**.

> **(b)(2)(B)(i).** "Subject to clause (iii), the amount determined under subparagraph
> (A)(ii)(I) shall **include** any amount received by the taxpayer during the taxable year with
> respect to the qualified nuclear power facility **from a zero-emission credit program**."
>
> **(b)(2)(B)(ii).** "…the term 'zero-emission credit program' means **any payments** with respect
> to a qualified nuclear power facility **as a result of any Federal, State or local government
> program**."
>
> **(b)(2)(B)(iii) Exclusion.** "…any amount received by the taxpayer from a zero-emission credit
> program shall be **excluded** from the amount determined under subparagraph (A)(ii)(I) **if the
> full amount of the credit calculated pursuant to subsection (a)** … **is used to reduce payments
> from such zero-emission credit program**."

This is a purpose-built anti-stacking rule with two branches, and **both cap total support**:

| branch | condition | a unit earning attribute price `D` receives |
|---|---|---|
| **(i)** default | the program does **not** net the federal credit out | `D + §45U(P + D)` — each $1 of `D` costs $0.80 of credit (16 % × 5). Self-limiting. |
| **(iii)** exclusion | the program **does** reduce its payments by the full federal credit | `max(D, §45U(P))` — the state tops the unit up to its own target. |

The forbidden composition — naive `D + §45U(P)` on an energy-only basis — is the one reading the
statute supports under **neither** branch. That, and only that, is what F-2 removes.

### 1.1 Why this is a rule 19 `[R-ONE-MECH]` question, not an arithmetic one

The crux is not which formula is bigger. It is that **there are two phenomena here**, and rule 19
asks for one mechanism for each (memo §3.2, reproduced because it is the actual argument):

1. *"Who buys this MWh's clean attribute?"* — **one certificate, several competing buyers** (state
   EAC contract, federal CES premium, RPS row, clean-tier row). Resolved by `max()`. **Unchanged
   by this charter**, along with `compute_attribute_revenue`.
2. *"What does Treasury pay this reactor for producing a zero-emission MWh?"* — **§45U**, which
   carries its **own** statutory anti-double-dip keyed to phenomenon 1's outcome.

Collapsing both into one `max()` is what conflates two mechanisms. And the collapse **passed by
coincidence, not by design**: `max(§45U, D)` is exactly branch (iii)'s formula, applied to Arm 3,
which is an LSE compliance obligation with **no branch-(iii) netting anywhere in it**. The old seam
was implementing the right arithmetic for the wrong program. That is the defect — not the number.

§2.3 below makes the coincidence measurable: after F-1, HEAD's `max()` and column (d) agree at
every point of the grid.

---

## 2. The `eac_price_nuclear` branch adjudication — ADJUDICATED HERE, NOT ESCALATED

**Ruling: `eac_price_nuclear` is a branch-(iii) instrument. It stays out of §45U's gross-receipts
basis and pays `max(contract, §45U(P))`.**

This **differs from the memo's §5 card**, which writes
`attribute = max(eac_price_nuclear, federal_ces × fraction, rps_dual, clean_dual)` and puts the
whole thing inside §45U's basis — i.e. classifies `eac_price_nuclear` as branch (i). The memo is
internally inconsistent on exactly this point: its §5 *"right for the wrong reason"* bullet names
`eac_price_nuclear` as "exactly what a genuine branch-(iii) program is … 'e.g. NY/IL Zero Emission
Credit ~$17'", while its card flattens it into branch (i). The charter's scope guard flags the
tension and asks for an explicit decision.

Three independent reasons for branch (iii), and one reason no owner call is needed:

1. **The instrument's own documentation.** `scenarios.py:1761` — `eac_price_nuclear: float = 0.0
   # $/MWh, e.g. NY/IL Zero Emission Credit ~$17`. NY's ZEC and Illinois' carbon-mitigation credit
   are both *target-minus-other-revenue* contracts; memo §1.3 states this in terms
   ("Branch (iii) is real, not hypothetical. It is the design NY's ZEC and Illinois'
   carbon-mitigation credit already use").
2. **A committed test already encodes it.** `test_45u_and_eac_nuclear_do_not_stack`
   (`tests/unit/model/test_capacity.py`) constructs a gap only the *sum* of §45U and
   `eac_price_nuclear` could close and asserts the unit **retires**. Under branch (iii) the pair
   pays `max(15, §45U(20) = 15) = 15 $/MWh` → 35,000 < 40,000 → retire, and the test passes
   unchanged. Under the memo card's branch (i) it would pay `15 + §45U(35) = 22.8 $/MWh` →
   42,800 ≥ 40,000 → **survive**, and the test would fail. The repo's existing rule-19 pin is a
   branch-(iii) pin.
3. **Symmetry with the actual payer.** The two legs differ in exactly the way the statute cares
   about: a netting contract's payer already claws the credit back on its own side; a compliance
   certificate's payer (an LSE) has no mechanism to.

**Why this needs no owner escalation: it is measurement-inert at every committed input.**
`eac_price_nuclear` defaults to **0.0** in every shipped config (the only occurrence outside the
default is `tests/golden/ercot_2026_2040.run_config.json`, also `0.0`), so the two readings are
bit-identical in every run the repo can currently produce. Even at the documented **$17** ZEC level
they agree exactly at both committed price bases — they can only diverge below **P = $26.75/MWh**
(2024 amounts) or **$27.75/MWh** (2025 amounts), because above that the credit is already dead on
top of the contract. Measured in §2.4.

**A note on the (b)(2)(B)(ii) edge case, unchanged from the memo.** Whether an LSE-paid compliance
certificate is a "payment … as a result of any … State … program" is genuinely unsettled — the
payer is private, the cause is a state standard, Treasury has issued no §45U computational
guidance (only Notice 2022-49, a request for comments), and LPPC was still asking for
gross-receipts clarity in 2026-02. It does not change the ruling: if a future rule puts compliance
certificates outside the base, the model's number becomes *conservative* rather than inflated, and
the error is bounded by the credit itself.

---

## 3. The change

Two files, no new `ScenarioConfig` field, no new degree of freedom (rule 21 `[R-DOF]`): every
number is statutory or already-cited committed config.

### 3.1 `policy/federal_ces.py` — the two legs, separable

New `eac_price_components_for_unit(config, fuel_type, emission_rate, year) -> (legacy, federal)`
returns the two prices the fold was already taking `max()` of.
`effective_eac_price_for_unit` becomes that function's `max()` and returns **the same number as
before at every input**. The screen needs to know *which* buyer won, because the two legs sit on
opposite branches of (b)(2)(B); collapsing them before that test is what would make one `max()`
silently do two different statutory jobs.

### 3.2 `model/capacity_evolution/retirements.py` — the seam

The `max(eac, ces, rps, clean)` fold, `compute_attribute_revenue`, and the attribute revenue
credited from them are **untouched**. §45U now runs *after* that block:

```
branch_i_price  = max(federal_ces_price, rps_for_unit, clean_for_unit)
branch_i_total  = branch_i_price + §45U(P_energy + branch_i_price)
branch_iii_total = max(state_eac_price, §45U(P_energy))
attribute_price = max(eac_price, rps_for_unit, clean_for_unit)     # already credited above
§45U revenue   += (max(branch_i_total, branch_iii_total) − attribute_price) × attainable_MWh
```

The unit sells **one** certificate, so it takes whichever route pays more. Each route's total is
monotone in its own price (branch (i)'s slope is `1 − 0.8 = 0.2 > 0` inside the phase-down and 1
outside it), so **the winner within branch (i) is still that branch's `max()`** — the doctrine
survives intact. Both route totals are `≥ attribute_price`, so the increment added here is the
credit **net of any branch-(iii) clawback**, never a second attribute payment.

**The attainable basis is preserved on BOTH sides of the ratio** (the backlog-#4 adjudication,
carried forward verbatim: a realized ratio is not tie-invariant, because a marginal-tie reshuffle
moves realized MW between hours carrying different prices). The branch-(i) attribute price added
to gross receipts is a per-MWh certificate price on **exactly the output the denominator counts**,
so the basis stays one notion of quantity throughout.

Also updated: the `miso_clean_tier_rows` field comment (`scenarios.py`) and
`section_45u_credit_per_mwh`'s docstring, both of which asserted the now-retired `max()` fold; and
the "owner call pending" annotation at the seam, replaced with the D-28 citation.

### 3.3 Backcast inertness — kept, not weakened

`tests/regression/test_45u_backcast_inertness.py` still passes. One assertion changed shape: it
now pins the set of **distinct production modules** that call `section_45u_credit_per_mwh` rather
than a raw call count, because the two statutory branches need two different gross-receipts bases
and therefore two calls — **inside the one already-forecast-only function**
`apply_economic_retirements`. The reachability argument is about which *module* can reach §45U;
links 2 (`evolve_fleet` is the only runner) and 3 (`runner.py` is `evolve_fleet`'s only call site)
are untouched, and link 3 is still pinned by its own test. Two calls in one forecast-only function
weaken nothing.

---

## 4. Stage 1 — the composition grid (no solve)

`scripts/probes/_f2_45u_stage1_composition.py`, which imports the F-1 probe's fleet loader,
capacity-factor reader and crossing-band algebra rather than restating them (F-1's probe is left
byte-unchanged as its own calibration record). Fleet: the 13-unit / 11,519 MW EIA-860 operable
MISO nuclear fleet. Compositions, with `P` the energy price and `D` the dual:

* **(a) naive add** `§45U(P) + D` — energy-only basis
* **(b) max** `max(§45U(P), D)` — HEAD before this charter
* **(c) branch (i)** `D + §45U(P + D)` — **adopted**
* **(d) branch (iii)** `max(D, §45U(P))`

### 4.1 The memo's nominal-amount curve, reproduced as published

Per the charter's do-not-silently-re-baseline instruction, the memo's §2.3 table is reproduced
first, on the credit that was HEAD when it was written — (a)/(b) pre-F-1, (c)/(d) statutory at the
nominal 0.3¢/2.5¢ amounts. **Every figure matches the memo to the cent.**

| P | D | (a) | (b) | (c) | (d) | (b) − (c) |
|---:|---:|---:|---:|---:|---:|---:|
| 30.80 | 0 | 14.07 | 14.07 | **10.36** | 10.36 | 3.71 |
| 30.80 | 10 | 24.07 | 14.07 | **12.36** | 10.36 | 1.71 |
| 30.80 | 30 (ACP) | 44.07 | 30.00 | **30.00** | 30.00 | 0.00 |
| 42.85 | 0 | 12.14 | 12.14 | **0.72** | 0.72 | 11.42 |
| 42.85 | 10 | 22.14 | 12.14 | **10.00** | 10.00 | 2.14 |
| 42.85 | 30 (ACP) | 42.14 | 30.00 | **30.00** | 30.00 | 0.00 |

### 4.2 The shipped (post-F-1/F-3) curve — all four on today's credit

| P | D | (a) | (b) | (c) | (d) | (c) − (b) | $/kW-yr |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 30.80 (2024, amounts 0.3¢/2.5¢) | 0 | 10.36 | 10.36 | **10.36** | 10.36 | 0.00 | 0.00 |
| 30.80 | 10 | 20.36 | 10.36 | **12.36** | 10.36 | 2.00 | 15.66 |
| 30.80 | 30 (ACP) | 40.36 | 30.00 | **30.00** | 30.00 | 0.00 | 0.00 |
| 42.85 (2025, amounts 0.3¢/2.6¢) | 0 | 1.52 | 1.52 | **1.52** | 1.52 | 0.00 | 0.00 |
| 42.85 | 10 | 11.52 | 10.00 | **10.00** | 10.00 | 0.00 | 0.00 |
| 42.85 | 30 (ACP) | 31.52 | 30.00 | **30.00** | 30.00 | 0.00 | 0.00 |

Fleet CF 0.8939 (2024) / 0.8978 (2025) ⇒ $1/MWh = $7.83 / $7.86 per kW-yr.

**Readings:**

* **(b) and (c) coincide TO THE CENT at the $30 ACP ceiling**, at both price bases — the charter's
  first pre-registered check, confirmed. Since an ACP caps the dual, that is the level an armed
  Arm 3 is most likely to actually produce, and there the composition choice is worth **$0.00**.
* **Column (b) ≡ column (d) at every grid point.** After F-1, HEAD's `max()` *is* branch (iii),
  exactly. This is the memo §5 "right for the wrong reason" bullet made measurable: the old seam
  was not approximately branch (iii), it was branch (iii), applied to a program with no
  branch-(iii) netting.
* **The composition choice alone, scanned over ALL duals** (not just the three tabulated levels):
  max **$2.07/MWh at D = $10.36 ⇒ $16.22/kW-yr** (2024) and **$0.30/MWh at D = $1.52 ⇒
  $2.39/kW-yr** (2025). The charter pre-registered $0–2.14/MWh ($0–17/kW-yr) from the memo's
  nominal curve; **the shipped curve is smaller**, because F-1/F-3 steepened the phase-down
  (0.16 → 0.80 $/$) and moved the zero-out basis $118.75 → $43.75–44.75/MWh, so there is less live
  credit left for the composition to move. Reported rather than re-baselined.
* **(a), naive add, is the only column that ever exceeds what a real unit could receive** — by up
  to $10/MWh at an interior dual. It is what the seam no longer does.

### 4.3 Margin vs the $130/kW-yr bar — settled in CF space

Nuclear `mc = $8.26/MWh` (fuel × 10 MMBtu/MWh + VOM). Since `(c) ≥ (b)` everywhere, a crossing
means a unit that **retires under (b) and survives under (c)**; the band is where
`bar/per_cf_(c) ≤ CF < bar/per_cf_(b)`.

| P | D | crossing CF band | modelled fleet CF |
|---:|---:|---|---:|
| 30.80 | 0 | **none at any CF** — (b) ≡ (c) | 0.894 |
| 30.80 | 10 | 0.425 ≤ CF < 0.451 → **outside** | 0.894 |
| 30.80 | 30 | **none at any CF** | 0.894 |
| 42.85 | 0 / 10 / 30 | **none at any CF** — (b) ≡ (c) at all three | 0.898 |

The single non-degenerate band sits at roughly **half** the modelled fleet capacity factor, i.e. at
a reactor operating like a mid-merit unit. No MISO reactor is near it.

### 4.4 The `eac_price_nuclear` branch, measured

At the documented **$17** ZEC level, adopted branch (iii) and the memo card's branch (i) give the
**identical** $17.00/MWh at both committed bases, with **no bar crossing at any capacity factor**.
They can diverge only below **P = $26.75/MWh** (2024 amounts) / **$27.75/MWh** (2025 amounts) —
the credit's zero-out basis less the contract. At the shipped default (`eac_price_nuclear = 0.0`)
they are identical everywhere.

---

## 5. Stage 2 — explicitly SKIPPED

The charter fires stage 2 (a bounded paired MISO forecast run, ≤5 yr, registered to the **forecast**
namespace) **only on a stage-1 crossing**. There is none, and the evidence is stronger than "no
crossing":

1. **At `D = 0` the new seam is identical to HEAD** — not "close", identical. Both
   `miso_clean_tier_rows` and `federal_ces_enabled` are default-off and `eac_price_nuclear`
   defaults to 0.0, so **every config the repo currently ships produces the same numbers as before
   this PR**. A paired solve would compare a run against itself.
2. **No unit crosses the $130/kW-yr bar under any composition**, settled in CF space across the
   whole grid (§4.3), not at two price points.
3. The composition's largest possible effect anywhere — $2.07/MWh ⇒ $16.22/kW-yr — is **12 % of
   the going-forward bar**, and it requires a dual that no shipped config produces.

The margin tables in §4.2–§4.4 are that evidence, per the charter's "no crossing ⇒ stage 2
explicitly SKIPPED with the margin table as evidence".

**Backcast:** still inert by reachability, unchanged and pinned (§3.3). No keeper metric can move,
so no backcast re-solve or dashboard registration is owed (rule 15 does not fire — no calibration
run was produced).

---

## 6. What Arm-3 arming still needs

This charter **unblocks** `miso_clean_tier_rows`; it does not arm it, and the mechanism-matrix cell
stays **`O`** (rule 25 — a blocker being cleared is not a verdict). What the arming charter owes:

1. **Its own per-ISO evidence.** A bounded MISO forecast pair (armed vs the Arm-2 control) on
   MISO's own market data. FFR-7B-2's 2026–2030 leg already measured the rows **SLACK in every
   window year** for structural reasons that this charter does not touch: MI's tier starts 2035
   (beyond any ≤5-yr window from 2026) and MN's 2030 obligation is covered under the shipped
   delivery-based Midwest-footprint mask. **So the arming charter probably cannot be decided in a
   5-year window at all** — it needs the 2035+ binding years, which needs a full-horizon
   authorization.
2. **The MN mask ruling.** FFR-7B-2's one stated divergence from FFR-6B §6.2 — §6.2's
   West-binds-by-2030 sizing implicitly used host-zone-only eligibility, while the shipped mask
   mirrors MN's renewable-tier delivery construction. That is **data**, one line in
   `MISO_CLEAN_TIER_REGIONS`, and it is an owner adjudication of §216B.1691's carbon-free tier, not
   a code change. Still open.
3. **The full-horizon authorization** for the 2035–2040 binding years.
4. **Nothing further on §45U.** The composition is decided, implemented, tested and measured. If
   the arming run produces an interior dual (i.e. below the $30 ACP), §4.2 is the table that says
   what the composition is worth there: at most $2.07/MWh, and $0.00 at the ceiling.

---

## 7. Sources

**Primary statute** — 26 U.S.C. §45U(a), (b)(2)(A), (b)(2)(B)(i)–(iii), (c)(1)–(2), (d)(1), read
via the D-28 memo's own verified citations (uscode.house.gov prelim; Cornell LII), 2026-08-08.

**In-repo** — `docs/handoffs/d28-45u-composition-memo-2026-08-08.md` §1.3/§2.3/§3/§5;
`docs/handoffs/f1-45u-ordering-2026-08-08.md` §7;
`docs/handoffs/ffr-6b-rps-grain-clean-tiers-2026-08-05.md` §6.4;
`docs/handoffs/ffr-7b2-rps-krow-clean-rows-2026-08-06.md`;
`src/market_sim/policy/ira.py`, `policy/federal_ces.py`, `policy/clean_tiers.py`,
`model/capacity_evolution/retirements.py`, `config/scenarios.py`, `config/capacity_market.py`;
`frontend/data/backcast/bench/MISO/{2024,2025}.json.gz` (the committed RT ATC price basis);
`scripts/probes/_f1_45u_stage1_margin.py`, `scripts/probes/_f2_45u_stage1_composition.py`.

**Environment note.** `data/clean` is derived and gitignored, so a fresh container has none;
`scripts/regenerate_clean.py` was run for this session. The `test_soundness::TestEndToEnd`,
`test_export::TestExportScenarioJson` and `test_fleet_arrays_golden` failures seen before it
completes are that missing-partition artifact — **verified identical at HEAD with the branch
stashed**, not a regression from this change.
