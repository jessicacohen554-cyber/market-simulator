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

**Both gates FAIL, badly — a fourth refusal, for a new and more
informative reason than Stages 2-4.** Grid:
`fom-scarcity-grid-2026-07-06-stage5-energy-only-floor.json` (6 ERCOT
cells, 2026-2031, mid growth, backstop ON, corrected CDR accreditation
basis, `market_design_retirement_floor=True` via `--energy-only-floor`,
fresh cache, 6 cells / 51 min / 2 workers).

| Gate (plan §5.4, ATB × ORDC cell) | Stage 4 (floor free) | Stage 5 (mechanism ON) | Pass? |
|---|---|---|---|
| 2027-2029 thermal retirement pace 0.5-2 GW/yr | 0 GW/yr | **14.79 GW/yr mean** (12.68 / 31.69 / 0.0) | **✗ — far over** |
| Backstop ≈ 0 in years 1-3 (backstop ON) | 0 MW | **34,124.5 MW** | **✗ — far over** |
| Overall | ✗ | — | **✗** |

Per-year detail, ATB×ORDC (the gate cell) and legacy×ORDC:

| GW | 2027 | 2028 | 2029 | 2030 | 2031 |
|---|--:|--:|--:|--:|--:|
| retired, atb:ordc | 12.68 | 31.69 | 0 | 0 | 30.86 |
| backstop, atb:ordc | 10.12 | 12.00 | 12.00 | 0 | 12.00 |
| retired, legacy:ordc | 12.68 | 0.67 | 20.56 | 0 | 0 |
| backstop, legacy:ordc | 10.12 | 0.86 | 12.00 | 5.56 | 0 |

**Diagnosis: this is the §1 grain-cliff risk materializing, not a bug in
the mechanism.** All six cells retire the *entire* 12.68 GW coal class in
2027 in one shot — same magnitude Stage 4 found un-retired at zero cost;
here it actually exits, and the backstop (correctly, per its own logic)
force-builds 10.1 GW of gas_ct that same year to cover most of the
resulting gap. But that new gas_ct — plus the pre-existing gas_ct
zone-bin — then fails **as one aggregate** the very next evolution step:
31.7-32.7 GW of gas_ct retires in 2028 (roughly the whole class in most
cells), because the entering year's price signal (2027's, priced *before*
the coal exit's own scarcity had time to form — the one-year-lag every
screen already carries) still sits at $22-23/MWh, identical to Stage 4.
The backstop then rebuilds at its annual queue cap (12 GW/yr — ERCOT's
`QUEUE_CAP_GW`) for 3 of 5 remaining years, and a second gas_ct aggregate
retires again in 2031 (~30 GW) once the rebuilt tranche re-fails. The
result is a multi-year retire→force-build→re-retire whipsaw entirely
inside gas_ct, not a staggered, plant-by-plant exit.

**This is exactly the G-31 zone-bin re-aggregation cliff
(`capacity-economics-retirement-grain-2026-07.md`), now hitting gas_ct
instead of coal.** The floor was never fixing that grain bug — it was
*masking* it, by never letting any fully-aggregated bin actually leave the
fleet. Disabling the floor for energy-only ERCOT removes the mask and lets
the pre-existing whole-bin-at-once retirement mechanic run at full force,
one class at a time, for as many classes as the (still floor-free, now
uncapped) screen flags. **This elevates G-31 from a hindcast-recall
diagnosis to a blocking prerequisite for this mechanism's forecast-side
use**, not merely cosmetic.

**What this DOES validate (the positive half of the result):** the causal
chain the design argued for in §1 — exit → tighter reserves → ORDC-priced
scarcity → revenue that could retain a marginal survivor — genuinely fires
for the first time in this grid's history. Mean prices, which were
byte-identical ($22.9-27.5/MWh) across every Stage 2-4 cell regardless of
FOM or scarcity-axis setting, now range **$23 to $476/MWh** across years
and swing hugely by cell (e.g. atb:ordc: 23.2 → 306.9/462 → 88.0 → 220-312
→ 454-476). The floor really was the thing suppressing scarcity
end-to-end, exactly as Stage 4 §3 argued. The mechanism is structurally
doing what it was built to do; it is the retirement *grain* feeding it
that is not yet trustworthy at this magnitude.

## 3. ATB FOM flip A/B and recommendation (owner decision, not flipped here)

**Refused a fourth time — for a different reason than Stages 2-4.** Not
run as a clean A/B: with the retirement pace unusable (§2), no comparison
read off it — FOM-legacy or FOM-ATB — would be evidence of anything. The
FOM axis is no longer *inert* (Stage 4's finding) — legacy and ATB cells
now retire different amounts in different years (compare the legacy:ordc
vs atb:ordc per-year table in §2) — but the numbers it's decisive over are
themselves an artifact of the G-31 grain cliff, not a market signal. Flipping
defaults on the strength of this grid would launder a grain bug into a
"FOM-driven" retirement-pace claim. **Recommendation: hold the FOM defaults
at legacy (12/8/40) and do not re-attempt this A/B until G-31 lands** (a
fleet-representation change — capacity-economics-retirement-grain-2026-07.md
candidates A/B/C, owner picks). The externally-identified ATB values
(NREL ATB 2024 / EIA S&L) remain frozen and ready to test the moment the
grain fix ships; nothing in this stage re-tunes either side of the
comparison (DOF ledger unchanged from Stage 2).

## 4. Hindcast closure (G-30 / G-31 disposition)

- **G-30 (harness scarcity flip + solar-entry re-run): already closed on
  main before this session, re-verified here.** The one-line flip is in
  `run_capacity_hindcast.py::build_config` (`scarcity_pricing_enabled=True`)
  and the s3 re-run recorded the honest outcome: byte-identical to s2 —
  the hindcast LP on the ample 2020-vintage fleet against realized demand
  never goes scarce, so the ORDC overlay prices ≈ $0 and solar entry still
  fails on a $14-24/MWh flat curve
  (`docs/hindcast-reports/ercot-2021-2025-realized-s3-2026-07-05.md`). No
  new hindcast work was needed to close this — it already was.
- **G-31 (retirement-recall grain): design note already on main**
  (`capacity-economics-retirement-grain-2026-07.md`, candidates A/B/C,
  owner picks; candidate B co-scopes with G-28 identity loss). Nothing in
  this stage pre-empts that decision, but §2 above supplies NEW evidence
  for it: the same zone-bin-at-once retirement mechanic the hindcast
  showed retiring 94 % false-positive coal is now shown, independently, on
  the *forecast* side retiring an entire gas_ct class at once the moment
  the floor stops masking it. Two independent runs (hindcast s2/s3, this
  stage's forecast grid) now implicate the same root cause in two fuel
  classes and two model modes — this is no longer a hindcast-only
  curiosity.
- **The stage-4/5 handoffs' originally-planned "s4 hindcast probe"
  (floor-disabled hindcast re-run) is explicitly SKIPPED this session.**
  The lane brief's sequencing ("in order, each gated on the previous")
  gates hindcast closure work behind the forecast acceptance gates (§2),
  which failed. Beyond following that sequencing, running the probe now
  would spend a second heavy multi-year solve to reconfirm a root cause
  §2 already demonstrated with high confidence (the identical grain
  mechanic, on a different fuel class) — not new information. It is
  correctly deferred to the session that takes up G-31 itself; at that
  point the hindcast probe becomes a validation step for the grain fix,
  not a probe of the floor-disable mechanism in isolation.

## 6. Folded-in items (same files, this lane) — both landed

- **Storage-ELCC portfolio dilution** (#1496 follow-up, accreditation audit
  §3): "model 2026 storage firm 11.7 GW vs the CDR-implied 12.3 GW
  (ELCC 60.2 % on 20,438 MW installed) — close at fleet level," with the
  flagged follow-up "the CDR's own BESS ELCC dilutes 60 % → 46 % by 2030 as
  penetration triples; the duration table has no penetration term."
  Landed as `_storage_portfolio_elcc_dilution` (`capacity.py`) + two new
  registries (`STORAGE_ELCC_DILUTION_REFERENCE_MW_BY_ISO`,
  `STORAGE_ELCC_DILUTION_CEILING_RATIO_BY_ISO`, `constants.py`, ERCOT
  only). Rather than fit a new exponent to an unverified intermediate MW
  ("triples" has no stated denominator we can reconstruct precisely), it is
  a straight LINE between the two actually-cited (penetration, ELCC)
  anchors: factor 1.0 at/below today's validated 20,438 MW (preserving the
  audit's "close at fleet level today" finding exactly), the CDR's own
  ratio 46/60.2 = 0.764 at/above the deployment ceiling
  (`STORAGE_DEPLOYMENT_CEILING_MW`), linear in between. Applied where
  `evolve_fleet` reads the pre-accredited `storage_firm_mw` from
  `prior_results` (`capacity.py`) — `runner.py` untouched, its persisted
  ledger value stays undiluted, the same seam the accreditation audit
  named. ISOs absent from either registry: byte-identical (factor 1.0).
  5 new tests (`TestStoragePortfolioElccDilution`), full capacity/storage
  suites re-pass.
- **PJM/MISO ICAP-vs-UCAP pairing** (audit §3 flag): **audited against the
  ISOs' own filings — the mismatch is REAL — and fixed.**
  - **PJM** states the IRM/FPR duality directly: "The IRM expresses the
    required reserve level in terms of installed capacity (ICAP) as a
    percent of forecast peak; the FPR expresses the same required level in
    terms of unforced/accredited capacity." 2026/27 BRA planning
    parameters: IRM **19.1 %** (ICAP) pairs with FPR **0.9170** (UCAP). Our
    ledger was testing `peak × (1+0.178)` (registered ICAP-basis IRM)
    against `Σ pmax × (1 − EFORd)` (UCAP supply) — a phantom-margin
    double-count, the same error class as the ERCOT CDR basis errors and a
    direct candidate for the Stage-2 PJM FOM-invariant ~10 GW/yr backstop
    flood.
  - **MISO** publishes both numbers side by side (PY 2025-26 LOLE Study
    Report, Module E-1): Summer PRM **ICAP 15.7 %** vs PRM **UCAP 7.9 %**.
  - **Fix (landed):** a new registry,
    `PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO` (`constants.py`) —
    each ISO's OWN published ICAP↔UCAP conversion ratio (PJM:
    FPR/(1+IRM) = 0.9170/1.191 = 0.7699; MISO:
    (1+PRM_UCAP)/(1+PRM_ICAP) = 1.079/1.157 = 0.9326), NOT a model-derived
    pool EFORd — these ratios are directly cited, so nothing depends on
    guessing which of the model's own fleet-composition numbers the ISOs'
    filings intend. `resolve_adequacy_requirement_mw` (`capacity.py`)
    multiplies the existing `firm_peak × (1+PRM)` by this ratio, defaulting
    to 1.0 (byte-identical) for every ISO absent from the registry — ERCOT
    untouched (its own pairing was already fixed at CDR seasonal-rating
    basis by the accreditation audit).
  - **Consequence, found while fixing tests, worth flagging explicitly:**
    correcting the basis REVERSES the naive comparison the Stage-2 report
    implicitly relied on. PJM's raw registered PRM (17.8 %) is higher than
    ERCOT's (13.75 %), but PJM's corrected EFFECTIVE requirement factor —
    `(1+0.178) × 0.7699 = 0.907` — is *lower* than ERCOT's `1.1375`: PJM's
    own published UCAP-basis requirement really is under 100 % of forecast
    peak. A same-inputs backstop comparison that used to build MORE for
    PJM than ERCOT now builds LESS — direct, mechanical evidence the two
    registered percentages were never comparable pre-fix (test
    `test_icap_ucap_ratio_reverses_naive_pjm_vs_ercot_comparison`,
    `tests/test_capacity.py`). This plausibly explains a meaningful share
    of the Stage-2 §2.1 PJM FOM-invariant ~10 GW/yr backstop flood, though
    re-testing that specifically would need a PJM cell re-run (out of this
    stage's ERCOT-only grid; left for the PJM lane or a future stage).
  - NYISO/NEISO/CAISO margins are flagged as follow-up audit candidates
    (NYSRC's 24.4 % IRM is also ICAP-stated; CAISO's 15 % PRM pairs with
    NQC) — each needs its own filing check before touching, the same bar
    the accreditation audit set. 2 pre-existing tests updated to the
    corrected basis (`test_higher_target_iso_builds_more_than_ercot` →
    renamed/rewritten to test the reversal directly;
    `test_iso_absent_from_registry_falls_back_to_scalar` now clears both
    registries to isolate the true full-fallback case). Full capacity
    suite re-passes (144/144); full repo suite passes except one
    pre-existing, unrelated failure
    (`test_clean_io.py::test_datatype_list_matches_schemas`, a duplicate
    `ramp-capability` entry in `scripts/regenerate_clean.py` — confirmed
    present before this session's changes, not touched by this lane).

## 7. Artifacts

- Mechanism: `market_design_retirement_floor` (`config/scenarios.py`,
  `model/capacity.py`), 4 tests in `TestMarketDesignRetirementFloor`.
- Storage-ELCC dilution: `_storage_portfolio_elcc_dilution`
  (`model/capacity.py`), 5 tests in `TestStoragePortfolioElccDilution`.
- ICAP/UCAP fix: `PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO`
  (`config/constants.py`), `resolve_adequacy_requirement_mw`
  (`model/capacity.py`).
- Grid JSON: `docs/handoffs/fom-scarcity-grid-2026-07-06-stage5-energy-only-floor.json`
- Harness variants: `run_fom_scarcity_grid.py --energy-only-floor`,
  `run_capacity_hindcast.py --energy-only-floor` (the latter NOT run this
  stage — see §4).

## 8. Summary for the next session

- **Do not enable `market_design_retirement_floor` as a recommendation**
  until G-31 (retirement grain) lands — it is structurally correct (§1,
  and the price-formation evidence in §2 confirms the causal chain works)
  but currently inherits a severe whole-bin-at-once retirement artifact
  that makes any pace/backstop number it produces untrustworthy.
- **G-31 is now a harder blocker than before this session** — two
  independent runs (hindcast s2/s3, this stage's forecast grid) implicate
  the same zone-bin re-aggregation cliff in two fuel classes and two model
  modes. Recommend prioritizing it in the next capacity-fleet-
  representation session.
- **ATB FOM flip stays refused** (fourth time) — not for Stage 4's reason
  (inert) but because the pace numbers it would be judged on are currently
  grain artifacts, not market signal. Re-attempt after G-31.
- **Storage-ELCC dilution and the ICAP/UCAP fix are unconditionally
  landed** (not gated behind the floor mechanism or G-31) — independent,
  smaller corrections, fully tested.

*Produced 2026-07-06, L-7 successor lane (capacity economics — floor
fidelity). All sections above reflect what was actually run/audited/
implemented this session; nothing here is a placeholder.*
