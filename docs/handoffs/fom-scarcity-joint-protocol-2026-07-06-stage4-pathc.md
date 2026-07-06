# FOM + scarcity joint protocol — Stage 4: path (c), the grid under the corrected accreditation basis (2026-07-06, L-7c)

*Executes Stage-2 §3 / Stage-3 unblocking **path (c)**: the FOM observability
grid under an accreditation configuration where ERCOT is NOT perpetually
accredited-short. The configuration is the corrected CDR accreditation basis
(`ercot-accreditation-audit-2026-07-06.md`, landed this session) with the
standard grid otherwise unchanged (mid growth, backstop ON — the Stage-2
A/A). Forecast probes only, 2026-2031, legacy bins, 6 ERCOT cells,
`--skip-pjm`, fresh cache (the per-cell cache keys on `ScenarioConfig` and
cannot see a constants-level change — never resume a pre-fix cache across a
basis change). Grid JSON: `fom-scarcity-grid-2026-07-06.json`. Nothing here
touches 2022 / H1-2026 or the dashboard (rule 22).*

**Headline: the FOM defaults are NOT flipped — the third refusal, now with
the masker fully identified.** The accreditation fix removed the phantom
requirement (the backstop gate now passes with real content), but zero MW
retires in any cell, so flipping CT 8→21 / CC 12→30 / coal 40→45 still moves
zero realized MW and zero tonnes. What remains is no longer a ledger error:
it is the floor's **zero-cost retention sitting upstream of the price
signal** — a market-design fidelity question for energy-only ERCOT, named
below as the single remaining blocker for both the FOM axis and hindcast
scarcity.

## 1. Acceptance gates (plan §5.4), honestly

| Gate | Stage 2 (old basis) | Stage 4 (corrected basis) | Pass? |
|---|---|---|---|
| 2026-2028 thermal retirement pace 0.5-2 GW/yr | 0 GW | 0 GW | ✗ |
| Backstop ≈ 0 in years 1-3 (backstop ON) | 15,214 MW | **0 MW** | **✓ (real, not vacuous)** |
| Overall | ✗ | — | **✗ — DO NOT flip** |

The backstop gate passing with the backstop enabled is the direct
validation of the accreditation fix: Stage 2's 15.2 GW of 2027-2029 forced
CT was phantom requirement, and it is gone. The backstop now first fires in
2030 (4.6 GW) and 2031 (6.1 GW) — where mid-growth demand (gross peak
93.7 → 119.6 GW over 2026-2031) genuinely outruns the static fleet, matching
the audit §5 static projection of a ~2028-29 crossing.

## 2. What the FOM axis now moves — bookkeeping, not outcomes

CO₂, prices, and retirements are byte-identical across the FOM axis in all
six cells (2026-2031 cumulative CO₂ ≈ 1,107.5 Mt, mean price $22.9 →
$27.5/MWh, retired = 0 everywhere). But the FOM axis is no longer *inert*:
it visibly changes the **floor-retention ledger** —

| floor-retained MW | 2027 | 2028 | 2029 |
|---|---:|---:|---:|
| legacy × ordc | 12,678 | **13,349** | 34,653 |
| atb × ordc | 12,678 | **34,242** | 36,907 |

Under ATB FOM the CT class (bar 21 > 2027 screen revenue 17.2 $/kW-yr)
accrues its first loss year in 2027 and reaches eligibility in 2028; under
legacy (bar 8 < 17.2) it starts failing only in 2028 and joins in 2029. The
FOM level now decides *when units are flagged and floor-retained* — and the
floor puts every one of them back, so nothing downstream changes. FOM is
observable in the ledger, unobservable in every realized outcome. A flip
would still be a no-op falsely credited with the plan §1.4 emissions effect.

## 3. The remaining masker, precisely — and why it is the last one

The chain in every cell: mean energy price $22-27/MWh with no scarcity →
screen revenue (coal ≈ energy margin ~0; CT 0.6-17.2; CC 30-45 $/kW-yr)
sits below the coal bar (52 effective) and the CT bars (8 or 21) → the
economic screen flags the entire coal fleet in 2027 (12.7 GW) and the CT
fleet a year or two later (~22 GW) → the floor un-retires nearly all of it
for **genuine** late-decade adequacy → the physical fleet stays whole → the
dispatch is never short → the ORDC overlay has ~0 to price (CT revenue
collapses to 1-4 $/kW-yr from 2028) → prices stay at $22-27 → repeat. The
Stage-3 circularity ("the floor is upstream of the price signal") survives
the basis fix intact; only the phantom-requirement layer is gone.

The audit's §5 prediction was right on the requirement side (backstop quiet
in years 1-3) and wrong on one point, recorded honestly: the floor is NOT
quiet in 2027 — not because the ledger says short at entry (it doesn't),
but because the economic screen dumps 12.7 GW of coal in one year at these
price levels and the *post-retirement* ledger then genuinely needs most of
it back.

**Why this is a fidelity defect and not just a calibration nuisance:** the
real ERCOT has no reliability floor. An energy-only market's answer to an
under-remunerated unit is an actual exit (~1-2 GW/yr of thermal exits are
observed — the very pace gate this grid keeps failing), which tightens
reserves, raises scarcity prices, and keeps the *marginal* survivor whole
on scarcity rent; RMR is a rare, unit-specific, compensated exception. Our
floor implements permanent, free, system-wide RMR: it retains ~35-47 GW at
zero cost, which (a) deletes the exits the pace gate measures, (b) deletes
the scarcity that would make the revenue side of every screen realistic,
and (c) makes both sides of the FOM comparison irrelevant. The floor
mechanism is sound for ISOs whose capacity constructs actually procure to
the requirement (PJM/MISO/NYISO/NEISO/CAISO); for ERCOT it substitutes an
administrative outcome for the market's actual adequacy mechanism.

**Recommended next mechanism work (out of this lane's scope, capacity.py
owner's queue):** either (a) disable the retirement reliability floor for
energy-only market designs (`MARKET_DESIGN[iso].capacity_market == False`),
letting adequacy express as scarcity price → revenue → retention/entry the
way the market actually works (the backstop, default-off, remains the
modeling-safety valve); or (b) make floor retention carry its real cost
(RMR-style compensation priced into the screens, retained MW removed from
the ORDC headroom it currently pads). Option (a) is the structurally
faithful one for ERCOT (rule 1). Only after one of these lands can the
Stage-2 gates — including retirement pace — be re-tested meaningfully; the
FOM flip decision stays parked behind that re-test.

## 4. Item-4 disposition: tornado re-centring and the 2035 re-run stay deferred

Per the Stage-1/Stage-2 convention (re-centring bands on unmoved defaults
would misreport the base case): with the flip refused a third time, the
tornado FOM bands stay centred on the legacy defaults (CT 8, CC 12, coal
40; `run_sensitivity_tornado.py`), and the owed `--end-year 2035` tornado
re-run stays deferred — its purpose was to exercise retirement-DOF leverage,
which this grid demonstrates is still floor-suppressed at any horizon. The
ATB targets (21/30/45) remain the frozen, externally-identified values
(Stage-2 DOF ledger unchanged; nothing in this stage re-tuned either side
of the comparison).

## 5. Disposition of the unblocking paths (final for this wave)

- **(a) Foresight lookahead** — adjudicated separately
  (`foresight-adjudication-memo-2026-07-06.md`): stays default-off pending
  the signal-fidelity fix; not a floor unmasker either way.
- **(b) Backstop-off** — closed negative (Stage-3 addendum).
- **(c) Corrected accreditation basis** — **this stage: partially
  effective.** It removed the phantom requirement (backstop gate now truly
  passes) and made FOM visible in the retention ledger, but the floor's
  zero-cost retention still suppresses every realized outcome. Path (c) is
  closed as *diagnostic success, unmasking failure*; the successor path is
  the floor-fidelity change of §3.

*Grid JSON: `docs/handoffs/fom-scarcity-grid-2026-07-06.json` (6 ERCOT
cells, 2026-2031, mid growth, backstop ON, corrected CDR accreditation
basis, 1,610 s solve). Produced 2026-07-06, lane L-7c, Stage 4.*
