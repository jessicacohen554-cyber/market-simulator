# FINDING — caiso-149: `tranche_startup_amortization` is REFUSED EX ANTE for CAISO, no solve spent. The mechanism is the Order-825 **fast-start pricing** analogue — folding a fast-start unit's start cost *into the LMP* — and **CAISO does not have fast-start pricing**: across the whole 2023–2025 window CAISO recovers exactly those costs as **Bid Cost Recovery uplift settled OUTSIDE the price** (CAISO DMM, 2017 and 2025, two independent filings). Separately and sufficiently, the target rows are already occupied: **92.9 % of the targeted capacity carries a MEASURED CAISO DAM bid** plus an explicitly-identified fuel-invariant $/MWh margin of **$8.42–$22.69**, against a candidate component of **$3.85** measured on CAISO's own CEMS run lengths. Cell `U` → **`G`**. Keeper unchanged.

**Session:** 2026-07-31. **Keeper (unchanged):**
`2026-07-31-caiso148-nuclear-availability` (bundle `caiso148_nucavail_B`).
**Probe:** `scripts/probes/caiso149_tranche_startup_phase0.py` (no LP, no solve,
no parameter changed). **New measured artifact:**
`data/raw/_processed-legacy/campd_ct_run_lengths_CAISO.csv` (frozen rule-23
derive, CAISO's own CAMPD units, 2023–2025 only — produced for this
adjudication and committed for any future lane).

**Charter.** Matrix §5.2 item 4: `tranche_startup_amortization`, untested in
CAISO (cell `U`), named against evening-ramp start economics. The handoff bound
this session to read both standing adjudications before proposing it — NYISO
`R` (nyiso-96, rule 1) and ERCOT `G` (ERCOT-145, rule 19, ex ante) — and to
**state what makes CAISO different from both**. Phase 0 was run as no-LP with
an explicit no-solve-closure exit (the caiso-136 / caiso-144 pattern). It
closes: **the A/B is not licensed.**

**What makes CAISO different from both precedents** (rule 25 — this is a CAISO
verdict derived on CAISO's own market design, fleet, bids and CEMS; nothing is
transferred):

* **vs NYISO** (`R`, rejected on rule 1 after a registered A/B): NYISO's
  rejection was *conduct-based* — its CT fleet demonstrably does not add a
  start markup to SRMC. NYISO **has** FERC-approved fast-start pricing, so the
  mechanism was real there and the question was whether it was *identified*;
  the owner ultimately promoted it. In CAISO the prior question fails first:
  the pricing rule the mechanism represents **does not exist in this market**.
* **vs ERCOT** (`G`, refused ex ante on rule 19): ERCOT's incumbent on the
  target rows is a **fitted** multiplier set, which is why ERCOT-145 could name
  a reopen condition — *retire the fit by measured re-identification, then the
  start component enters as one term of that identification*. **In CAISO that
  reopen condition is already spent**: the re-identification happened
  (`caiso_offer_surface_measured`, CAISO's own OASIS DAM Public Bid Data), and
  its result **is** the incumbent. There is no fit left to retire, and rule 14
  `[R-ACCURATE]` runs the other way. CAISO's refusal is therefore strictly
  stronger than ERCOT's, and it has **no reopen condition on the offer side at
  all**.

---

## §A — The decisive ground: CAISO has no fast-start pricing (rule 1 `[R-STRUCT]`)

`tranche_startup_amortization` is, by its own source docstring, the "Order 825
analogue": it takes a fast-start unit's start cost, amortizes it over the
unit's run, and adds it to the unit's **price-setting energy bid** so the cost
reaches the LMP. Its `min_run` / `min_down` stay 0 — "bid markup only, no new
UC coupling" (`data/fleet/assembly.py`) — so it changes **nothing but price
formation**. It is exactly, and only, the fast-start-pricing object.

That object is a market-design *rule*, and it is per-ISO. The four `K` cells
(PJM, MISO, NEISO, NYISO) are the four ISOs that have it. **CAISO does not**,
and did not at any point in the 2023–2025 calibration window. Two independent
CAISO Department of Market Monitoring filings, nine years apart, say so
explicitly — and both name what CAISO does instead:

* **2017, FERC Docket RM17-3** (DMM comments opposing the fast-start-pricing
  NOPR): *"CAISO sets locational marginal prices based on marginal production
  costs. **CAISO provides bid cost recovery payments made to compensate
  resources for any discrete commitment costs that are not recovered through
  marginal cost pricing.**"* FERC never finalized RM17-3 as a generic rule.
* **2025-01-10, Body of State Regulators** (DMM, "Fast start pricing issues and
  analysis"): *"If energy revenues do not cover full startup and minimum load
  bid costs after being committed, **unit receives bid cost recovery (BCR)
  payments**."* And on status: *"DMM understands that in response to requests
  from numerous stakeholders, **CAISO is examining the possibility of some form
  of FSP in the WEIM**."* — i.e. as of **January 2025**, deep inside the
  calibration window, fast-start pricing is a *candidate enhancement under
  evaluation*, not a market rule. The same deck sizes the object: BCR to
  fast-start gas units in CAISO was **$19M / $33M / $27M in 2021 / 2022 /
  2023** — 12 % / 13 % / 10 % of total CAISO BCR.
* **2026 status:** fast-start pricing remains a *future* item in the Price
  Formation Enhancements Initiative (Phase 2), not an implemented rule.

BCR is a make-whole payment settled **outside** the LMP. The LP's price is the
energy-balance dual (rule 4 `[R-DUALS]`); an uplift never enters it. So
representing CAISO faithfully means **no start component in the price-setting
bid on the fast-start rows** — which is what the keeper already does. Arming
the mechanism would model a price-formation rule CAISO does not have. That is
rule 1's converse — *never reach the right number through a mechanism that
isn't real* — and it is dispositive on its own, independent of any fit
consideration.

**Independence of this evidence (METHOD step 1).** The validating source is
CAISO's own market monitor, which is independent of **both** inputs the
supporting legs consume: the OASIS Public Bid Data the offer-surface derive
reads, and the EPA CAMPD extracts the run-length derive reads. §A does not
depend on either.

## §B — Rule 19 `[R-ONE-MECH]`: the target rows are occupied, and the occupant is 2.2×–7.9× the candidate

Enumerated on the keeper's own `run_config.json` (probe leg 1). The rows the
mechanism would mark up are the `econ*` tranches of `CT_PEAKER` / `CT_CHP` and
the `peak*` tranches of `CT_PEAKER` / `CT_CHP` / `CC_REGULAR` / `CC_CHP`
(`assembly.py` `_fsp_econ` / `_fsp_peak`). Their incumbents:

| rows | current owner of start-cost price formation |
|---|---|
| **every** `_committed` tranche, all classes | `compute_monthly_markup` at the P0→P1 seam — **unconditional**, runs with the flag OFF (`pipeline/solve.py:254`) |
| `CT_PEAKER` + `CC_REGULAR` `econ*`/`peak*` | **`caiso_offer_surface_measured`** — the cap-weighted medians of the CAISO fleet's OWN submitted DAM energy bids (OASIS Public Bid Data, carbon/VOM-netted) |
| the same rows, decomposed | **`gas_offer_net_revenue_margin`** (anchor 4.7964 $/MMBtu) — already splits each into physical marginal HR × delivered fuel **+ a fixed, fuel-invariant $/MWh margin** |
| `CT_CHP` / `CC_CHP` `econ*`/`peak*` | band multipliers (ERCOT-inherited placeholders, *not* CAISO-grounded) + the same margin decomposition |

The second and third rows are the point. **`gas_offer_net_revenue_margin` is
already the explicit, identified owner of the fuel-invariant $/MWh component of
these offers** — structurally the same object an amortized start cost is. Sized
per plant on the keeper's resolved bands and each plant's own measured base heat
rate (probe leg 1, capacity-weighted within each band):

| group | band | MW | mult | phys | margin $/MWh | min | max |
|---|---|---:|---:|---:|---:|---:|---:|
| CT_PEAKER | econ_low | 3,289 | 1.147 | 0.686 | **22.16** | 14.53 | 55.77 |
| CT_PEAKER | econ_high | 2,964 | 1.182 | 0.710 | **22.69** | 14.88 | 57.10 |
| CT_PEAKER | peak | 533 | 1.176 | 1.000 | **8.42** | 5.55 | 21.29 |
| CT_CHP | econ_low | 199 | 1.200 | 0.594 | **30.26** | 23.91 | 66.60 |
| CT_CHP | econ_high | 199 | 1.200 | 0.598 | **30.06** | 23.75 | 66.16 |
| CT_CHP | peak | 96 | 1.400 | 1.000 | **20.21** | 15.78 | 43.96 |
| CC_REGULAR | peak | 472 | 1.333 | 2.250 | **0.00** | 0.00 | 0.00 |
| CC_CHP | peak | 56 | 2.250 | 2.250 | **0.00** | 0.00 | 0.00 |

Against the candidate's own reach (§C): **$3.85/MWh**. Ratios **2.19× / 5.75× /
5.89×** on CT_PEAKER and **5.25× / 7.81× / 7.86×** on CT_CHP. Arming as designed
is **stacking a second start-recovery mechanism onto rows whose existing
fuel-invariant margin already over-covers the phenomenon several times over** —
the configuration rule 19 forbids.

**The two zero-margin rows do not rescue it.** `CC_REGULAR peak` (472 MW) and
`CC_CHP peak` (56 MW) clip to 0 — together **6.8 %** of the 7,808 MW the
mechanism targets, so **92.9 % of targeted capacity is occupied**. And they clip
for a reason that cuts the same way: `CC_REGULAR peak`'s multiplier **1.333 is
the MEASURED DAM bid**, sitting *below* the 2.250 physical F-class duct ratio —
the CAISO CC fleet measurably offers its duct band **below its own physical duct
cost**. Adding a start markup there moves the model's offer *away* from measured
conduct, in the direction the measurement says is wrong. `CC_CHP peak` is
registered exactly at physical (2.250 = 2.250) and is host-steam-pinned.

## §C — Reach: $3.85/MWh, measured on CAISO's own CEMS (rule 25)

`data/raw/_processed-legacy/campd_ct_run_lengths_CAISO.csv`, derived this
session by the frozen rule-23 deriver (`scripts/data/derive_campd_ct_run_lengths.py
--iso CAISO`) from CAISO's own CAMPD unit-level extracts, simple-cycle
`Combustion turbine` units only, 2023–2025 only (rule 22 — CAISO holds no
calibration-complete marker):

* **50 plants + a pooled ISO-class fallback row; 26,623 measured start-to-stop
  runs.** Class median run **4.0 h**, mean 6.47 h, p90 10.0 h. Per-plant medians
  span 2–8 h.
* Crossed with the NREL class start costs the mechanism amortizes
  (`constants.CT_COMMITMENT_PARAMS`: $12.3 / $24.5 / $19.0 per MW by heat-rate
  class), over each plant's own measured horizon:
  **capacity-weighted $3.85/MWh**, median $4.10, range $0.09–9.50.

This is the maximum price effect the candidate can produce, and it is
comfortably inside the margin already on the rows.

The artifact is committed regardless of the verdict: it is a rule-23-frozen
measured operating statistic of CAISO's CT fleet, useful to any future lane
(it re-derives only when CAMPD updates, never because a residual moved).

## §D — Direction, reported for completeness — NOT the ground of the refusal

Rule 1 forbids judging a structurally-correct mechanism by its effect on the
residual, so this leg is context, not evidence. On the keeper's committed class
hourlies against the committed CAMPD/EIA benchmark:

| year | CT_PEAKER model | actual | % of actual | shortfall |
|---|---:|---:|---:|---:|
| 2023 | 1.832 TWh | 4.128 | 44.4 % | −2.30 |
| 2024 | 0.659 TWh | 4.326 | 15.2 % | −3.67 |
| 2025 | 0.471 TWh | 2.374 | 19.8 % | −1.90 |

The mechanism makes the CT econ/peak bands **dearer**, so it pushes the class
the CAISO lane's own diagnosis says is deeply under-produced further down — the
nyiso-96 signature (27–39 % degradation there), from a far worse base. Recorded
so no successor mistakes the refusal for a fit argument: **the refusal is §A
(the rule does not exist here) and §B (the row is occupied); §D would not have
licensed a rejection on its own, and would not have licensed an arming either.**

This also does **not** reopen caiso-119 R4. R4's guardrail stands unchanged: a
successor lever for the CT gap must be a real obligation-keyed mechanism with a
cited D-4 window — and this candidate is an offer *markup*, which is the wrong
sign for R4 besides.

## §E — Adjudication

**Cell verdict: `G` — governance-refused ex ante, no solve spent.** Grounds, in
order of sufficiency:

1. **Rule 1 `[R-STRUCT]`** — the mechanism represents fast-start pricing;
   CAISO does not have fast-start pricing in the calibration window and
   recovers the same costs as BCR uplift outside the LMP (§A, two independent
   DMM filings). Dispositive alone.
2. **Rule 19 `[R-ONE-MECH]`** — 92.9 % of targeted capacity already carries a
   fuel-invariant $/MWh margin 2.2×–7.9× the candidate, explicitly owned by
   `gas_offer_net_revenue_margin` over a `caiso_offer_surface_measured` level
   (§B). Sufficient alone.
3. **Rule 14 `[R-ACCURATE]`** — the incumbent on those rows is a *measurement*
   of CAISO's own conduct. The only rule-19-clean form (replace the incumbent
   with physical + amortization) would replace a measurement with a model, and
   the ERCOT-145 reopen route (retire the fit by re-identification) **is
   already spent in CAISO** (§B). No reopen condition remains on the offer side.

**No reopen condition is offered.** The one event that could change §A is a
FERC-accepted CAISO fast-start-pricing tariff *and* a calibration window that
falls after its effective date — a market-design change, not a modelling
decision, and it would arrive as a new mechanism with its own identification,
never as this flag turned on over the measured bands.

## §F — One observation, FILED not absorbed (out of scope)

`compute_monthly_markup` amortizes the NREL start cost into the P1 bid of every
`_committed` tranche **unconditionally**, in all six ISOs, independent of this
flag — it is the P0→P1 bid-cost seam that *defines* P1 (`pipeline/solve.py:254`,
spec §1.6). §A's reasoning about CAISO's BCR-not-LMP recovery touches that seam
too, at least in principle. It is **not** this session's lever and is not opened
here: it is architecture-level (the two-pass structure shared by every ISO and
every keeper), a spec question rather than a per-ISO lever, and any change would
move six keepers at once. Surfaced for an owner-scoped charter; **do not absorb
it into a CAISO lever session** (rule 25).

## §G — DO-NOT-REDO (new, binding on successors)

1. **Do not propose `tranche_startup_amortization` for CAISO again.** The cell
   is `G` on three independent grounds and carries **no reopen condition**. In
   particular, do not re-propose it on the strength of the four `K` cells:
   verdicts are per-ISO (rule 25) and those four ISOs have a pricing rule CAISO
   does not.
2. **Do not "fix" §B by scoping the flag to the zero-margin CC peak rows.** No
   such scope exists, inventing one is a new mechanism needing its own row and
   identification (rule 28c), and the `CC_REGULAR peak` incumbent is itself a
   measured bid — marking it up moves the model away from CAISO's measured
   conduct (rule 14).
3. **Do not strip `caiso_offer_surface_measured` or the
   `gas_offer_net_revenue_margin` decomposition to "make room" for the
   amortization.** That is the rule-19 replacement form ERCOT-145 already
   called the wrong direction, and in CAISO it additionally deletes a
   measurement (rule 14). The CAISO CT band levels are **already** measured
   conduct; there is no fitted incumbent to retire.
4. **Do not re-derive `campd_ct_run_lengths_CAISO.csv` against a residual**
   (rule 23 `[R-FROZEN-DERIVE]`). It re-derives only when CAMPD updates, and the
   commit must cite the data change.
5. **Do not cite this session as evidence about CAISO's CT under-production.**
   §D is context reported for completeness, not a measurement of the CT gap's
   cause; the CT gap's heat-rate route is closed by caiso-146 and R4's
   obligation-keyed guardrail is untouched.
6. **Do not open the `compute_monthly_markup` committed-row seam from a CAISO
   lever session** (§F). It needs an owner-scoped, cross-ISO charter.

## §H — Session governance

* **No solve spent.** No LP ran; no bundle was produced; **nothing is
  registered on the dashboard** (rule 15 registers *completed runs*, and there
  is none — the caiso-136 / caiso-144 precedent).
* **Keeper unchanged:** `2026-07-31-caiso148-nuclear-availability`,
  determination CALIBRATED-WITH-CAVEATS, 0 FAILs, 2 of 3 non-protective ledger
  slots spent, protective 0/1. No `keepers/CAISO.json` edit, no re-audit.
* **Rule 22:** CAISO holds **no** calibration-complete marker; every artifact
  and every read in this session is confined to 2023–2025, and **no marker was
  written**.
* **Rule 28b:** the `tranche_startup_amortization` CAISO cell is updated to `G`
  with its evidence citation in `docs/codebase-site/data/mechanism-matrix.js`
  in this same session, and matrix §5.2 item 4 is struck.
* **Live CAISO lever queue after this session: items 2 and 3.** Item 2's only
  live prerequisite remains caiso-138 §C firm-block elasticity (the export half
  stays closed with nothing unbuilt, caiso-143); item 3 is the S2 DA/RT
  two-settlement separation charter.
