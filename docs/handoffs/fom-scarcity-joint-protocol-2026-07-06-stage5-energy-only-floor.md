# FOM + scarcity joint protocol — Stage 5: floor fidelity for energy-only designs (2026-07-06, L-7 successor)

*Executes the Stage-4 §3 successor mechanism ("no free floor for energy-only
market designs"): the retirement reliability floor's zero-cost retention is
the last identified masker of the FOM axis, the retirement-pace gate, and
hindcast scarcity/solar entry. This stage (a) states the design decision,
(b) lands the mechanism gated and default-off, (c) re-runs the Stage-2
acceptance gates with the mechanism ON, and (d) records the parked ATB FOM
flip A/B against the outcome. Forecast probes only; nothing here touches a
backcast keeper, the registry, offer/floor configs, 2022, or H1-2026
(rule 22).*

## 1. Design decision: option (a) — the floor follows the market design

Stage 4 §3 named two candidate mechanisms: **(a)** disable the retirement
reliability floor where `MARKET_DESIGN[iso].capacity_market == False`
(energy-only ERCOT), or **(b)** RMR-priced retention (retention carries its
real going-forward cost, and the retained MW is removed from the ORDC
headroom it currently pads). **We build (a).** The argument, on the
mechanisms and not on authority:

- **(a) is the mechanism the real market actually has.** ERCOT procures no
  capacity to a requirement; its answer to an under-remunerated unit is an
  actual exit (the observed ~0.5–2 GW/yr the pace gate measures), which
  tightens operating reserves, moves the ORDC into its priced range, and
  keeps the *marginal* survivor whole on scarcity rent. That
  exit → scarcity → revenue → retention/entry loop is exactly what the model
  already implements (ORDC overlay / AS co-opt feeding the screens'
  reserve-price signal, scarcity-priced new entry) — the floor was simply
  sitting upstream of it, un-retiring the fleet before the loop could form a
  price. Removing the floor for energy-only designs is not a new mechanism;
  it is un-blocking mechanisms that are already built and identified.
- **(b) models a channel ERCOT does not have.** Real RMR (Nodal Protocols
  §3.14.1) is *transmission-security*-scoped: a unit is retained only when
  its exit would violate grid-security criteria in a specific study area,
  it is compensated at cost under a filed agreement, and it is rare and
  temporary (single units, not fleets — and ERCOT may not procure capacity
  for system-wide resource adequacy at all). Modeling 12–47 GW of
  economically-failing capacity as RMR-retained would price a *system-wide
  adequacy* RMR channel that does not exist — the right number through a
  mechanism that isn't real, which rule 1 forbids in both directions.
- **(b)'s scarcity accounting is also physically wrong in our frame.** Its
  "remove retained MW from the ORDC headroom" leg deletes real reserves to
  synthesize scarcity: an online retained unit's headroom genuinely is
  operating reserve (ERCOT settles RMR energy/AS like any resource's when
  deployed), so the ORDC would be pricing a shortage the dispatch does not
  have. That is an administrative price overlay tuned to produce revenue —
  a fitted adder in structure if not in intent.
- **What (b) would buy, honestly, and why we still decline it:** (b) caps
  the one-shot retirement cliff — with the floor off, nothing stops the
  economic screen from dumping the entire 12.7 GW coal class in 2027 at
  Stage-4's ~$22/MWh price level (coal's loss threshold is 1 year), which
  can overshoot the 0.5–2 GW/yr observed pace from the high side. But that
  cliff is a *known granularity/sequencing artifact*, not market structure:
  the screen retires whole classes at once because (i) the fleet is
  zone-bin aggregated after year 1 (G-31, the 94 %-false-retire grain
  diagnosis — `capacity-economics-retirement-grain-2026-07.md`) and (ii)
  the one-pass annual evolution (rule 10) lets no within-year price
  feedback stagger exits the way sequential real-world decisions are
  staggered. Papering over a grain artifact with a pseudo-RMR channel
  would bury the G-31 root cause inside a second unreal mechanism (rule
  19: one mechanism per phenomenon). The gates below are re-run with (a)
  and the outcome recorded whatever it is — the Stage-2/3/4 refusals were
  recorded honestly and this stage keeps that bar.

**Mechanism as landed** (`market_design_retirement_floor`, default **off**):

- `ScenarioConfig.market_design_retirement_floor: bool = False`. When on,
  `_apply_reliability_floor` (`model/capacity.py`) returns immediately —
  retaining nothing and logging nothing — for ISOs **explicitly registered**
  energy-only (`MARKET_DESIGN[iso].capacity_market == False`, i.e. ERCOT).
- Capacity-market ISOs (PJM/MISO/NYISO/NEISO/CAISO) are **byte-identical
  with the flag on or off**: their capacity constructs really do procure to
  a requirement, so the floor is the faithful mechanism there (Stage-4 §3).
- ISOs **absent** from `MARKET_DESIGN` keep the floor even with the flag on
  (conservative fallback — an unregistered ISO's design is unknown, and
  `DEFAULT_MARKET_DESIGN`'s energy-only default exists to withhold capacity
  *revenue*, not to assert the ISO has none).
- The reserve-margin build backstop (`reserve_margin_build_enabled`,
  default off) is untouched and remains the modeling-safety valve, exactly
  per Stage-4 §3.
- Flag off = byte-identical everywhere (tested, the #1496/#1501 pattern).
  No other mechanism changes ride along in this commit.

Interactions declared up front: with the floor off and the backstop ON (the
grid's Stage-2 A/A configuration), a mass exit year can pull the accredited
ledger below the requirement and the backstop may legitimately fire *later
in the window* — the "backstop ≈ 0 in years 1-3" gate is evaluated exactly
as written (2027-2029), and any later backstop MW is reported alongside,
not hidden. Economic new entry (step 5) sees the post-exit scarcity prices
one year after the exit and runs before the backstop (step 6), so the
backstop only picks up what priced entry declines.

## 2. Stage-2 acceptance gates, mechanism ON — results

**[PENDING — grid running; this section is filled from the actual grid
JSON when it completes, whatever the outcome. Nothing below this line in
§2-§3 is a result until the placeholder is replaced.]** Grid
configuration: `fom-scarcity-grid-2026-07-06-stage5-energy-only-floor.json`
(6 ERCOT cells, 2026-2031, mid growth, backstop ON, corrected CDR
accreditation basis, `market_design_retirement_floor=True` via the harness
`--energy-only-floor` variant, fresh cache).

## 3. ATB FOM flip A/B and recommendation (owner decision, not flipped here)

**[PENDING — read off the grid's FOM axis once §2 lands. Gated on the §2
gates: if they fail, the flip is refused a fourth time and the refusal
recorded here.]** Whatever the outcome, the defaults are NOT flipped in
this PR (owner sign-off required). DOF ledger: both sides of the
comparison remain externally identified (NREL ATB 2024 / EIA S&L);
nothing in this stage re-tunes either side (unchanged from Stage 2).

## 4. Hindcast closure (G-30 / G-31 disposition)

- **G-30 (harness scarcity flip + solar-entry re-run): already closed on
  main, verified this session.** The one-line flip is in
  `run_capacity_hindcast.py::build_config` (`scarcity_pricing_enabled=True`)
  and the s3 re-run recorded the honest outcome: byte-identical to s2 —
  the hindcast LP on the ample 2020-vintage fleet against realized demand
  never goes scarce, so the ORDC overlay prices ≈ $0 and solar entry still
  fails on a $14-24/MWh flat curve
  (`docs/hindcast-reports/ercot-2021-2025-realized-s3-2026-07-05.md`).
- **Should the hindcast now adopt the floor mechanism (an s4 leg)?** The
  s3 evolution ledgers show the floor retaining 10.7-26.0 GW/yr in
  2023-2025 — it *is* load-bearing there. With the mechanism ON those
  units exit, the following year's LP tightens, and scarcity CAN form in
  the hindcast for the first time — mechanically unblocking the solar-entry
  probe the s2 report asked for. This stage runs that leg as a mechanism
  probe; results in §5.
- **G-31 (retirement-recall grain): design note already on main**
  (`capacity-economics-retirement-grain-2026-07.md`, candidates A/B/C,
  owner picks; candidate B co-scopes with G-28 identity loss). Nothing in
  this stage pre-empts that decision; the §1 cliff analysis above is the
  same diagnosis feeding the same choice.

## 5. Hindcast s4 leg (mechanism ON) — recorded honestly

**[PENDING — probe leg queued behind the §2 grid (≤2 heavy solves
concurrent). Filled from the scored s4 bundle when it completes.]**
Expectations stated before the run, so the record shows what was predicted
vs found: §1 predicts the over-retirement *worsens* (the floor was
retaining 10.7-26.0 GW/yr; the hindcast's perfect-foresight price signal
stays scarcity-free until after the first mass exit because the screens see
year-N-1 prices), and solar entry becomes mechanically possible only once a
post-exit year's solve goes scarce. Whatever lands, the s4 leg is a
mechanism probe, NOT a proposed harness footing change.

## 6. Folded-in items (same files, this lane)

- **Storage-ELCC penetration dilution** (#1496 follow-up, accreditation
  audit §3): the CDR's own BESS ELCC dilutes 60.2 % (20.4 GW installed,
  2026) → 46 % by 2030 as penetration ~triples; the duration table had no
  penetration term. **[PENDING implementation this session]** — plan:
  a CDR-cited penetration-dilution registry (constants, ERCOT anchors
  only — absent ISOs byte-identical), applied where `evolve_fleet`
  consumes the pre-accredited `storage_firm_mw` (capacity.py; runner.py
  untouched — its persisted ledger value stays undiluted, same seam as
  the audit §3 runner note).
- **PJM/MISO ICAP-vs-UCAP pairing** (audit §3 flag): **audited against the
  ISOs' own filings — the mismatch is REAL.** Both ISOs publish the pairing
  explicitly, and both publications show the requirement and the supply
  count must share a basis:
  - **PJM** states the IRM/FPR duality directly: "The IRM expresses the
    required reserve level in terms of installed capacity (ICAP) as a
    percent of forecast peak; the FPR expresses the same required level in
    terms of unforced/accredited capacity." 2026/27 BRA planning
    parameters: IRM **19.1 %** (ICAP) pairs with FPR **0.9170** (accredited
    UCAP; 2025/26: FPR 0.9387) — i.e. PJM's own UCAP-basis requirement
    multiplier is ≈ 0.92-0.94 × peak, not 1.178 × peak. Our ledger was
    testing `peak × 1.178` (ICAP-basis IRM) against `Σ pmax × (1 − EFORd)`
    (UCAP supply): a ~7-9 point phantom margin, the same double-count class
    as the ERCOT CDR errors and a direct candidate for the Stage-2 PJM
    FOM-invariant ~10 GW/yr backstop flood.
  - **MISO** publishes both numbers side by side (PY 2025-26 LOLE Study
    Report, Module E-1): Summer PRM **ICAP 15.7 %** vs PRM **UCAP 7.9 %**.
    Our `PLANNING_RESERVE_MARGIN_BY_ISO["MISO"] = 0.179` (PY24-25 ICAP
    PRM) against UCAP supply overstates the requirement by ~8-10 points.
  - **Fix (landed with this stage):** requirement-side conversion, not a
    supply-side recount — `PLANNING_RESERVE_MARGIN_BASIS_BY_ISO` registers
    PJM/MISO margins as ICAP-basis, and `resolve_adequacy_requirement_mw`
    converts to the ledger's own supply convention by multiplying with the
    *model fleet's* capacity-weighted `(1 − EFORd)` (the pre-ELCC-reform
    FPR construction, PJM Manual 20: FPR = (1 + IRM) × (1 − pool EFORd)).
    Using the model's own pool EFORd keeps the two sides of the comparison
    on one convention by construction (dividing both sides of the ICAP
    comparison by the same factor), regenerates forward with the fleet
    (rule 13), and introduces no new tunable. We deliberately do NOT adopt
    the published FPR/PRM-UCAP *values* (0.917 / 7.9 %): those are stated
    on the ISOs' post-reform accreditation depth (PJM marginal-ELCC pool
    accreditation ≈ 77 %), far deeper than our `(1 − EFORd)` supply derate,
    so pairing their numbers with our supply would flip the error's sign.
    ERCOT is untouched (its pairing was fixed at seasonal-rating/CDR basis
    by the accreditation audit); NYISO/NEISO/CAISO margins are flagged as
    follow-up audit candidates (NYSRC's 24.4 % IRM is also ICAP-stated;
    CAISO's 15 % PRM pairs with NQC) — each needs its own filing check
    before touching, the same bar the accreditation audit set.

## 7. Artifacts

- Grid JSON: `docs/handoffs/fom-scarcity-grid-2026-07-06-stage5-energy-only-floor.json`
- Hindcast s4: `results/hindcast/ercot-2021-2025-realized-s4/` + report
- PJM ICAP/UCAP probe: recorded alongside the grid JSON if the §6 fix lands

*Produced 2026-07-06, L-7 successor lane (capacity economics — floor
fidelity). Sections 2/3/5/6 are filled from runs/audits produced in this
session; a version with [PENDING] markers means that step had not yet
completed and carries no results.*
