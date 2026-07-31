# ERCOT-145 — `tranche_startup_amortization` on ERCOT: REFUSED ex ante, no solve spent

**Session:** 2026-07-31. **Keeper (unchanged):** `2026-07-31-ercot144-coal-perplant-offer`
(bundle `ercot144_perplant_arm`). **Probe:**
`scripts/probes/ercot145_tranche_startup_phase1.py`. **New measured artifact:**
`data/raw/_processed-legacy/campd_ct_run_lengths_ERCOT.csv` (frozen rule-23
derive, ERCOT's own CAMPD units, 2023–2025 only — produced for this
adjudication and committed for any future lane).

**Charter.** Matrix §5.1 item 5: A/B the PJM/MISO/NEISO(/NYISO-by-owner) form
(`tranche_startup_amortization` + measured-run v3) on ERCOT — the named
mid-merit/peak price-formation candidate bearing on the NON-TAIL component of
C3a-2024/25 and C3b. Phase 1 was pre-committed as no-LP with an explicit
no-solve-closure exit (the ERCOT-143 pattern). Phase 1 adjudicates:
**the A/B is not licensed — the ERCOT cell is stamped `G`** on three
independent measured grounds.

## 1. Rule 19 — the tranche rows are already occupied, and the occupant is 3–60× the candidate

What ERCOT's P1 already prices for startup, enumerated on the keeper's own
`run_config.json` (probe leg 1):

| rows | current owner of start recovery |
|---|---|
| every CAMPD bin's `_committed` tranche | NREL start cost amortized over P0 monthly run lengths (`compute_monthly_markup`, the P0→P1 seam) |
| ST_GAS (committed row) | the same markup with the May–Sep season-spread (`gas_st_startup_cost` + `gas_st_startup_spread`, both armed) |
| merchant gas-CC state | the commitment-bridge economic leg (`ercot_gas_bridge_startup`, startup-restart inequality on P0 duals — a STATE mechanism, not a bid) |
| **CT_PEAKER/CT_CHP econ+peak, CC peak** (the tranche form's target rows) | **no explicit startup term — the FITTED `offer_curve_by_group` band multipliers** (residual-identified DOF; ledger row `offer_curve_by_group`, gas side, 107 scalars) |

The queue's "vs ERCOT's season-spread ST startup" framing resolves cleanly:
the ST form and the tranche form are row-disjoint (ST_GAS committed vs CT
econ/peak) — the real incumbent on the tranche rows is the fitted multiplier
set. Sized on the keeper's resolved CT_PEAKER values against their own
recorded physical basis (cap-wt base HR 10.91):

| band | fitted | phys | fitted margin @$2.2 / @$3.4 gas | measured amortization |
|---|---|---|---|---|
| econ_low | 1.27 | 0.723 | **+$13.1 / +$20.3** | $2.9–4.0 |
| econ_high | 2.18 | 0.727 | **+$34.9 / +$53.9** | $2.9–4.0 |
| peak | 13.15 | 1.00 | **+$292 / +$451** | $2.9–4.0 |

The measured fuel-invariant component ($20/MW ÷ the CAMPD-measured 5–7 h
plant-median run, class fallback 6 h) is **$2.9–4.0/MWh** — the fitted margins
already on those rows are 3–60× larger. So:

- **Arming as designed = stacking** a second start-recovery mechanism onto
  rows whose fitted margin already over-covers the phenomenon — the exact
  configuration rule 19 forbids, and immaterial besides ($3–4 against bands
  that already carry $13–54 of fitted markup).
- **The rule-19 replacement** (strip the fitted bands to physical + the
  amortization) **lowers** the CT curve by ~$10–50/MWh — the wrong direction
  for every underpriced hour, a guaranteed C3a crash. Re-identifying the CT
  band level from a measured instrument is queue item 6's territory
  (`measured_ct_heat_rates` / the SCED TPO corpus on the CT fleet), not this
  lever.

Contrast with the four keeper ISOs: there the tranche rows sit at or below
their physical basis (the `backcast_config` `phys_*` clip comments — markup
clips to 0), so the amortization added a genuinely missing component. ERCOT's
CT stack is the opposite regime. Verdicts never transfer (rule 25) — and this
is why not.

## 2. The target is not a level object — the sub-$200 residual is signed both ways

On the keeper's committed hourly sidecars, model demand-weighted hub vs the
committed hourly RT actual (probe leg 2; hourly-lw diagnostic basis — the
official C3a weights zone annual means, so headline %s differ from the
rubric's):

- **The sub-$200 load-weighted gap is tiny and, in 2024, POSITIVE:**
  2023 −$0.21, **2024 +$0.72**, 2025 −$1.64 /MWh — against tail
  (act ≥ $200) contributions of −$20.99 / −$3.30 / −$1.18. The official
  load-weighted miss is dominated by the attributed RT scarcity-formation
  object (closed lane), not by a mid-merit level deficit.
- **Within the top load quintile the sub-$200 residual is signed both ways:**
  act < $30 hours are OVERPRICED (+$7.9 / +$7.3 / +$5.7 in 2023/24/25) while
  act ∈ [$50, $200) hours are UNDERPRICED (−$11 to −$66) — an
  under-dispersion / near-tail-frequency signature, the same family as the
  attributed tail, extending below the $200 threshold. A near-uniform adder
  on CT-marginal hours (CT_PEAKER is partially dispatched in 57–83 % of BOTH
  bands) shifts both signs together: it buys ~$2 on a −$21…−$66 gap while
  worsening the +$6–8 overpricing roughly one-for-one. No Δ exists that
  closes one side without opening the other — the lever has the wrong SHAPE
  for the defect.
- **2024's mid-quintiles are already overpriced** (q2 +$1.00, q3 +$2.30 mean
  in sub-$200 hours): the "high-load sub-$200 underpricing" the charter named
  does not exist in 2024 below the near-tail band; in 2025 it is real but
  lives at −$21/−$66 magnitudes in the [$50,$200) actual band, unreachable by
  a $3–4 offer component.

## 3. C3b — the monthly residual is not the amortization's signature either

2024 monthly gaps (model − act): shoulder/winter negative (Jan −3.0 … May
−5.9, Nov −7.9), summer POSITIVE (Jun +2.6, Jul +2.8, Sep +2.2) — with Aug
−4.1 being the scarcity-month tail expression. 2025: negative nearly every
month, worst Apr −5.1 / May −8.2. A shoulder-up/summer-flat amortization
shape points the right way in 2024's shoulder but stacks onto the summer
overpricing, and per §1 it is not armable anyway. The Apr–May/Oct–Nov
concentration (outage-season tightness) and the 2023 winter-volatility C3b
miss are the named objects of **queue item 4** (the five-ISO fuel-stack
consistency audit: `gas_daily_shape` / `gas_monthly_actuals` /
`gas_plant_monthly_fuel_pricing`), which is the chartered successor.

## 4. Adjudication and what would reopen it

**Cell verdict: `G` (governance-refused ex ante, no solve)** — rule 19 (the
rows are occupied by fitted multipliers that over-cover the component; the
only admissible replacement moves the curve the wrong way by an order of
magnitude) + rule 1 (the quantified target is a dispersion/frequency object,
already attributed to RT scarcity formation, that a level adder cannot
re-disperse). The refusal is measured, not stylistic: probe legs 1–3 carry
the numbers.

Reopening requires **retiring the incumbent first**: a measured re-identification
of the ERCOT CT band levels from ERCOT's own conduct (the SCED TPO instrument
on the CT fleet, or item 6's `measured_ct_heat_rates` on the physical side).
If a future lane replaces the fitted CT multipliers with measured levels, the
fuel-invariant start component becomes a legitimate part of THAT
identification — as one term of a measured replacement, never a stack on the
fitted bands. The measured run-length artifact this session committed is
ready for that lane.

**Not touched:** no ScenarioConfig change, no solve, no dashboard
registration (no run produced). Keeper, DOF ledger (n_residual 6), and all
gate verdicts unchanged. Holdouts untouched (derive years 2023–2025 only).
