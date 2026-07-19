# FINDING (caiso-100): the residual belly is priced by a CITED cycling-degradation cost, not a spread threshold — the measured fleet is NOT day-gated (2024/25 skip-share ~2 %), but the margin of its charge distribution reveals a conduct cost of $11-17/MWh that brackets the repo's derived $14.25 li-ion cycling cost, while the model's margin sits at its efficiency-loss floor (~$5); mechanism = battery_dispatch_adder at the DERIVED value (owner-gated, pre-registered here, NOT solved)

**Session 2026-07-19 (CAISO-100 — the belly charge-economics charter,
derive-first + owner-gated). Every number in §1-§5 is a committed-data or
same-machine-repro measurement — no new-mechanism LP was built or solved. §6
pre-registers the mechanism's bands and gates BEFORE any B-leg exists
(caiso-98/99 discipline). §7 is the owner ask's summary; the ask itself is
`docs/handoffs/caiso-100-charge-econ-ask-2026-07-19.md`.**

## 1. Where caiso-99 left the residual, and what this session measured

The caiso-99 keeper (`2026-07-19-caiso-99-storage-shape`) dispatches the
measured COD-ramped EIA-860 battery fleet inside the measured NG:OTH p95
diurnal envelope, and still over-prices the belly +7.7/+7.6/+6.3 $/MWh
(2023/24/25). FINDING-caiso99 §7 localized the residual INSIDE the envelope:
the zero-cycling-cost LP charges at the envelope cap in ~every economic hour,
while the measured fleet's mean belly rate is ~0.5-0.7 of its own p95. The
charter's hypothesis menu: (a) a cited Li-ion cycling/degradation cost, and/or
(b) a DA-spread day-level charging threshold. This session measured which one
the data supports.

Instruments (all committed, plus the same-machine repro protocol):

- `scripts/probes/_caiso100_charge_econ.py` (NEW, committed) — per (year, day):
  belly (hod 10-14) charge intensity as a fraction of the EIA-860 monthly
  fleet and of the frozen p95 envelope, against the day's realized spread
  (TB4 = top-4-minus-bottom-4 hourly, and evening(17-21)-minus-belly(10-14)),
  on the actual RT and DA LMP for the measured side and on the model's own
  demand-weighted CA λ for the model side. Battery-only on BOTH sides (PS
  excluded — NG:OTH does not carry Helms; note FINDING-caiso98/99's model
  charge totals summed storage.parquet across all units, i.e. include
  1.14/1.70/1.60 TWh of PS charge; this probe's battery-only basis is the
  clean one and is used throughout below).
- Fresh same-machine `caiso99_repro_A` + `caiso99_shape_B` (FINDING-caiso92b
  protocol — committed bundles are never the baseline; solved this session,
  gitignored, un-registered; the A-leg reproduces the caiso-97 recorded
  surface digit-for-digit: hod ladder +1.3/+10.9/−6.4 | +0.2/+9.0/−4.7 |
  +1.6/+8.4/−1.9, C3c 20/0/0).
- Measured battery = EIA-930 CISO `NG: OTH`; fleet basis = EIA-860 monthly
  battery MW via `load_eia860_storage` (PS excluded) — byte-identical to the
  envelope derivation's bases (`scripts/derive_caiso_storage_shape.py`).

## 2. The measured fleet is NOT day-gated on spread — hypothesis (b) is refuted

Per-day belly envelope-utilization u = (belly-mean charge rate) / (belly-mean
p95), against the day's RT TB4 spread:

| year | u deciles (p10/p25/p50/p75/p90) | skip-share (u<0.25) | skip by TB4 quintile Q1→Q5 | corr(u, TB4) |
|---|---|---|---|---|
| 2023 | 0.17/0.30/0.48/0.68/0.83 | **0.19** | 0.29/0.30/0.15/0.12/0.08 | 0.14 |
| 2024 | 0.41/0.53/0.64/0.75/0.84 | **0.02** | 0.04/0.01/0.03/0.01/0.00 | 0.07 |
| 2025 | 0.54/0.64/0.73/0.81/0.87 | **0.02** | 0.04/0.04/0.01/0.01/0.00 | 0.31 |

The mature fleet (2024/25) charges on essentially EVERY day — a broad unimodal
intensity band (u p10-p90 ≈ 0.4-0.9), weakly spread-correlated; true day-skips
are ~2 % of days. Only commissioning-year 2023 shows real day-skipping (19 %,
concentrated in the low-spread quintiles). A hard DA-spread day threshold
would produce a step in u-vs-spread and a charge-weighted spread median well
above the day median; the data shows neither (charge-weighted ≈ unweighted
median on every basis: e.g. 2024 RT TB4 37.1 vs 37.3; DA 37.7 vs 38.4).
**Hypothesis (b) — a fitted day-level spread threshold — is measured-refuted
and is NOT proposed.** (It would also have been the rule-25-riskier
construction: a threshold has no market rulebook analogue at the day grain,
while a cycling cost is priced in CAISO's own DEB design — §4.)

## 3. But the margin of the charge distribution reveals a conduct cost — and it brackets the derived physical cost

The spread S* below which only q of annual belly charge occurs, mapped to an
implied per-MWh-discharged conduct cost c* = S* − λ_chg·(1/rte − 1) (rte
0.86; λ_chg = charge-weighted median belly RT λ = 25.8/17.6/18.1, so the
efficiency-loss term is $4.2/2.9/2.9):

| basis | q | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| RT TB4 | 5 % | c* 15.2 | c* **14.9** | c* 10.8 |
| RT TB4 | 10 % | c* 19.7 | c* **17.7** | c* **14.8** |
| DA TB4 | 5 % | c* 14.4 | c* 17.0 | c* 10.9 |
| DA TB4 | 10 % | c* 23.9 | c* 21.2 | c* 15.5 |
| DA eve-belly | 10 % | c* 21.5 | c* 19.0 | c* 13.4 |

The repo's DERIVED li-ion cycling-degradation cost —
`storage._degradation_cost_per_mwh("li_ion_4hr")` = capex_per_kwh × 1000 /
cycles × STORAGE_DEGRADATION_REPLACEMENT_FRACTION = 285,000 / 5,000 × 0.25 =
**$14.25/MWh discharged** (NREL ATB 2024 capex, LFP warranty cycle life,
replacement fraction 0.25 — `constants.py:4128-4136`; the identical
construction ERCOT's cycling lane quoted at $14.25,
`docs/DIAGNOSIS-ercot-storage-cycling-lane-2026-07.md` §3) — sits inside the
revealed 5-10 % margin band ($11-17 in the mature years, $14-24 in 2023) on
every spread basis. The margin where reality's day-skipping and
intensity-thinning actually happens IS the physical cycling cost, to within a
few $/MWh.

Mechanism shape matters here: in the LP, a per-MWh-discharged cost does NOT
produce binary day-gating — it continuously shrinks the profitable
charge-window within each day (on a shallow-dip day fewer hours clear the
round-trip hurdle), with full skips only when the day's deepest dip fails it.
That is the same pattern class as §2's measured intensity modulation
(continuous thinning, rare skips) — unlike a day-level threshold, which is the
shape the data refutes.

## 4. Why the adder is the admissible mechanism (and the caiso-76 no-change ruling)

- **It is real market structure (rule 1).** CAISO's storage Default Energy Bid
  design carries an explicit cycling/degradation term (DMM 2024 storage report
  Eq 2.11.1 ρ "including cycling and cell degradation costs"; the MSC's
  Nov-2024 BCR opinion calls the degradation terms "appropriate to include";
  DMM notes resources' variable costs "often reflect a conservative estimate
  of potential cell degradation costs"). The model's current $0 is the
  *estimate*; the derived $14.25 is the measured-cost replacement (rule 14).
- **caiso-76 resolved this knob NO-CHANGE — both grounds have moved.**
  (i) *"RDT `STORAGE_VARIABLE_COST` defaults to $0"* — the default is the
  *fallback*, not the design: the DEB's ρ term exists precisely to carry
  resource-specific validated cycling costs, and §3's revealed conduct
  ($11-17/MWh at the margin) shows the fleet behaves as if it faces one.
  (ii) *"the zero-adder LP already UNDER-cycles CAISO"* — measured on the
  caiso-65-era model (5.33/7.60/10.48 TWh discharge vs LESR RTD
  5.67/10.04/12.06). On today's KEEPER stack (battery-only, NG:OTH basis)
  broad under-cycling is gone and the defect is price + belly
  concentration: belly charge +45 %/+6 %/+5 % (3.13/5.90/9.15 vs measured
  2.16/5.57/8.70 TWh) at a charge-weighted λ $12.2/$5.8/$7.6 ABOVE
  reality's glut floor, while annual charge is +14 %/−4 %/−8 % (and the
  −4/−8 % under-charge sits OUTSIDE the belly — the shoulder/overnight
  conduct channel, a recorded non-target of this mechanism, §5). The adder
  targets the price/margin defect; §6's two-sided throughput guard bounds
  the volume side so the belly fix cannot buy a new under-cycling defect
  (the LESR-RTD basis is reported alongside). Re-opening a resolved ruling
  is the owner's call — hence the gate on this whole mechanism.
- **Rule 13 (forward story):** the cost regenerates for any forward year from
  forward drivers (ATB capex projections × cycle life × replacement
  fraction) and responds to changed conditions (falling capex → falling
  adder → more cycling; exactly the observed 2023→2025 convergence of
  reality toward the LP's economic rate). Nothing pins dispatch to actuals.
- **Rule 24 (registered knob):** `ScenarioConfig.battery_dispatch_adder` is an
  existing registered field (enters the backcast battery objective via
  `load_eia860_storage` → `StorageUnit.vom`, i.e. $/MWh discharged; recorded
  in `run_config.json`; DOF-ledger row `scripts/build_dof_ledger.py:316`),
  already carried in `docs/parameter-citations.md` under the Xu et al. 2018
  cycle-aging citation. No new knob, no env channel; the B-leg delta rides
  the standard `prb_overrides` → `config.with_overrides` path.
- **Rule 25 (no residual-tuned scalar):** the value is the DERIVED $14.25 —
  the same formula every ISO's storage entry screen already prices
  (`_degradation_cost_per_mwh`) and the ERCOT lane quoted — fixed a priori by
  §3's cross-validation, NOT swept. (ERCOT's keeper $10 is ERCOT's tuned
  value and does not cross the boundary; CAISO takes the derived value, not
  ERCOT's.) If the owner rules the mechanism in, the B-leg solves ONE value.
- **Rule 19 (one mechanism per phenomenon):** the adder prices throughput
  *economics*; the envelope caps *capability*. They compose without stacking
  on the same phenomenon (the envelope is an upper bound, the adder a cost;
  neither replaces the other; the caiso-74 AS reservation stays off and
  embedded in the envelope). D-2: the adder is a COST, not a floor — it can
  force nothing; C8 is untouched by construction.

## 5. The model side (fresh same-machine repro): the LP's charge margin sits at its efficiency-loss floor on a spread surface it compresses itself

`_caiso100_charge_econ.py` on the fresh A-leg (caiso-97 recipe, pre-envelope)
and B-leg (the caiso-99 KEEPER recipe, envelope armed) — model spreads
computed on the model's OWN demand-weighted CA λ:

| metric (2023/24/25) | measured (RT) | model A-leg | model B-leg (keeper) |
|---|---|---|---|
| day-median TB4 spread | 47.3 / 37.3 / 33.5 | 18.0 / 13.2 / 13.4 | **24.5 / 16.9 / 19.4** |
| S05 revealed threshold → c* | 15.2 / 14.9 / 10.8 | 4.7 / 5.1 / 5.3 | **7.0 / 6.6 / 7.4** |
| S10 → c* | 19.7 / 17.7 / 14.8 | 5.8 / 6.1 / 5.7 | 9.2 / 7.4 / 7.9 |
| charge-wtd λ_chg (belly) | 25.8 / 17.6 / 18.1 | 40.7 / 26.0 / 30.6 | **38.0 / 23.4 / 25.7** |
| u deciles p50/p90 | 0.48-0.73 / 0.83-0.87 | 0.74-1.05 / 1.16-1.60 | 0.76-0.89 / 1.0 (clipped) |
| belly chg TWh | 2.16 / 5.57 / 8.70 | 4.04 / 6.34 / 9.66 | 3.13 / 5.90 / 9.15 |
| annual chg TWh | 4.07 / 8.71 / 13.02 | 5.68 / 8.82 / 12.61 | 4.62 / 8.36 / 11.93 |
| annual dis TWh | 4.02 / 7.57 / 11.26 | 4.83 / 7.49 / 10.72 | 3.93 / 7.11 / 10.14 |

Reading, in three parts:

- **The LP's charge margin prices nothing.** In both legs the model charges
  down to days whose spread just covers round-trip losses (c* ≈ $5-7 ≈ its
  efficiency-loss floor + LP ε), where reality's margin prices ≈ the derived
  cycling cost ($11-17). When the keeper charges, it charges AT the envelope
  (u p90 = 1.0, clipped): the envelope fixed capability; the economics
  inside it are still free.
- **The residual is now a PRICE defect more than a volume defect.** Under
  the envelope the keeper's belly volume excess is only +6/+5 % (2024/25)
  — but its charge-weighted λ sits $5.8-12.2 above reality's glut floor.
  The zero-cost LP's implied charge BID is nearly its full evening-implied
  value (≈ η·λ_eve − eff), so charging rides UP the supply curve to $23-38
  instead of clearing at the ~$18 floor where reality buys the SAME volume.
  The adder lowers the charge bid by ≈ η × $14.25 ≈ $12 — the clearing
  point moves DOWN the glut supply curve; volume holds wherever floor-priced
  glut supply exists (it does — reality charges 5.57/8.70 TWh there), and
  drops only where even floor-priced charging cannot cover the true cost
  (the 2023-style marginal days). This is why the coherent prediction is
  "belly λ falls, volume ≈ holds", not "volume collapses".
- **The model's annual under-charge (−4/−8 % in 2024/25) sits OUTSIDE the
  belly** (measured non-belly charge 3.14/4.32 TWh vs model 2.46/2.78) —
  the shoulder/overnight charging reality does for AS positioning and
  morning discharge, the price-inelastic conduct channel the ERCOT cycling
  lane documented (`DIAGNOSIS-ercot-storage-cycling-lane-2026-07.md` §4/§7).
  A cost CANNOT create this energy and must not be blamed for missing it;
  it is a recorded non-target and the residual re-charter's subject if the
  ask is refused.
- The model's own equilibrium compresses the daily spread to ~40-60 % of
  actual (B day-median TB4 16.9-24.5 vs actual 33.5-47.3); the over-charged
  belly and under-served evening are the two ends of one compression. A
  real per-MWh cycling cost moves the fixed point: marginal charge-hours
  drop out or clear lower, belly λ falls toward the glut floor, evening λ
  rises, the spread decompresses until the marginal stored MWh covers its
  true cost — the residual's exact signature, produced by a cost that
  exists in the real market's bid structure.

## 6. Pre-registered report-back (bands + gates, BEFORE any B-leg — binding on the build session)

If the owner rules the mechanism in, the B-leg is: fresh same-machine
`caiso100_repro_A` (= the caiso-99 keeper recipe, i.e. `_caiso99_shape_B.py`
verbatim with only the out-dir renamed) vs `caiso100_cycling_B` = A +
`battery_dispatch_adder = 14.25` (the ONLY delta, via
`overrides["battery_dispatch_adder"]`), 2023-2025 one bundle each (rule 16),
sequential, scored `_caiso92_report.py <A> <B>` + `_caiso_storage_timing.py
<B>` + `_caiso100_charge_econ.py <A> <B>`.

HARD GATES (all must clear; breaking a passing criterion FAILs):

- **Belly λ residual (+7.7/+7.6/+6.3) falls in all three years; must not go
  negative** (no overshoot).
- **Evening λ residual (−5.3/−4.4/−2.3) moves toward 0; must not cross above
  actual.** 2025 evening battery discharge (7.66 vs measured 8.00 TWh
  incl-PS basis in FINDING-caiso99 §6) must not move away from measured by
  more than 0.3 TWh.
- **Two-sided throughput guard (battery-only, NG:OTH basis; bands set from
  the measured B-leg baseline — chg +14/−4/−8 %, dis −2/−6/−10 %):** annual
  battery charge AND discharge stay within **15 % of the measured year
  value** in every year (charge floors 3.46/7.40/11.07 TWh, discharge
  floors 3.42/6.43/9.57; ceilings +15 %). The keeper baseline clears every
  band; the band hard-fails a volume collapse (the plausible failure mode
  of an over-large cost) while allowing the bounded movement the bid-shift
  mechanism (§5) predicts. Additionally, BELLY charge must not fall below
  the measured belly (2.16/5.57/8.70 TWh) — the λ no-overshoot gate has a
  volume twin.
- **Protected results:** C1 12/12 holds; overnight λ no new under-price; C3c
  unchanged or toward the actual tail; C7/C8 PASS; C5a improves or holds
  (2024 CAVEAT must not regress to FAIL).

REPORTED DIAGNOSTICS (directional, not gated — they compare distributions
across two different price surfaces): the model's S05/S10 revealed thresholds
and c* rise from the efficiency-loss floor (~$7) toward the measured rows
($11-20); the model's day-median TB4 spread decompresses from ~17-25 toward
the actual 33-47; the charge-weighted λ_chg gap ($5.8-12.2 above measured)
closes toward the glut floor; skip-share and u-distribution move toward §2's
measured rows (the keeper baseline already skips 12 % of days in 2023/24 and
6 % in 2025 on its compressed surface, so skip-share is reported, never
gated).

A worse aggregate fit that is more structurally faithful still passes
provided no hard gate breaks (rule 1). Registered whatever the result
(rule 15); promotion only on no-status-regression; CAISO retention is 14/15 —
the registration MUST prune to top-15.

DOF ledger delta: ONE parameter (`battery_dispatch_adder` 0.0 → 14.25),
identification source = derived cycling-degradation formula (NREL ATB 2024
capex ÷ LFP cycle life × replacement fraction 0.25, `constants.py:4128`),
cross-validated against §3's revealed conduct cost — zero residual-fitted
values; LOYO is vacuous for a derived constant but the verdict-flip clause
(rule 22) applies if promotion flips any criterion.

## 7. Disposition

- **Mechanism chosen on measured evidence: (a) the cited cycling-degradation
  cost at the derived $14.25/MWh discharged. Hypothesis (b), the DA-spread
  day threshold, is refuted (§2) and closed.** No LP was solved with the
  mechanism; no flag/knob was changed; nothing registered. The keeper stays
  `2026-07-19-caiso-99-storage-shape`.
- **Owner ask filed:** `docs/handoffs/caiso-100-charge-econ-ask-2026-07-19.md`
  — authorize the B-leg per §6, or rule the knob stays 0.0 (in which case the
  residual belly is re-chartered to the remaining conduct channels: DA-award
  allocation and AS-deployment variance, both currently unmeasured at the
  needed grain).
- WP-3 (CT_CHP steam-floor rule-23 re-derive) remains PENDING its own ask
  (`docs/handoffs/caiso-wp3-ctchp-steam-floor-ask-2026-07-18.md`) — untouched
  this session per the charter's "if ruled" condition.
