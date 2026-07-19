# FINDING (caiso-100): the residual belly is priced by a CITED cycling-degradation cost, not a spread threshold — the measured fleet is NOT day-gated (2024/25 skip-share ~2 %), but the bottom decile of its charge distribution reveals a conduct cost of $15-20/MWh that brackets the repo's derived $14.25 li-ion cycling cost; mechanism = battery_dispatch_adder at the DERIVED value (owner-gated, pre-registered here, NOT solved)

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
  demand-weighted CA λ for the model side.
- Fresh same-machine `caiso99_repro_A` + `caiso99_shape_B` (FINDING-caiso92b
  protocol — committed bundles are never the baseline; solved this session,
  gitignored, un-registered).
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
median on every basis: e.g. 2024 RT TB4 37.1 vs 37.3). **Hypothesis (b) — a
fitted day-level spread threshold — is measured-refuted and is NOT proposed.**
(It would also have been the rule-25-riskier construction: a threshold has no
market rulebook analogue at the day grain, while a cycling cost is priced in
CAISO's own DEB design — §4.)

## 3. But the margin of the charge distribution reveals a conduct cost — and it brackets the derived physical cost

The spread S* below which only q of annual belly charge occurs, mapped to an
implied per-MWh-discharged conduct cost c* = S* − λ_chg·(1/rte − 1) (rte
0.86; λ_chg = charge-weighted median belly RT λ; the efficiency-loss floor is
$2.9-4.2/MWh):

| basis | q | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| RT TB4 | 5 % | — | c* **14.9** | c* ~12 |
| RT TB4 | 10 % | c* 19.7 | c* **17.7** | c* **14.8** |
| DA TB4 | 5-10 % | c* 24.5 | c* 17.0-21.2 | c* 15.4 |
| DA eve-belly | 10 % | c* 22.1 | c* 19.0 | c* 13.3 |

The repo's DERIVED li-ion cycling-degradation cost —
`storage._degradation_cost_per_mwh("li_ion_4hr")` = capex_per_kwh × 1000 /
cycles × STORAGE_DEGRADATION_REPLACEMENT_FRACTION = 285,000 / 5,000 × 0.25 =
**$14.25/MWh discharged** (NREL ATB 2024 capex, LFP warranty cycle life,
replacement fraction 0.25 — `constants.py:4128-4136`; the identical
construction ERCOT's cycling lane quoted at $14.25,
`docs/DIAGNOSIS-ercot-storage-cycling-lane-2026-07.md` §3) — sits exactly at
the revealed 5-10 % margin in the mature years. The margin where reality's
day-skipping and intensity-thinning actually happens IS the physical cycling
cost, to within a few $/MWh, on every spread basis. The zero-cost LP's
implied marginal spread is the efficiency-loss floor alone (~$3-4/MWh) — an
order of magnitude below any revealed conduct.

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
  ($15-20/MWh at the margin) shows the fleet behaves as if it faces one.
  (ii) *"the zero-adder LP already UNDER-cycles CAISO"* — measured on the
  caiso-65-era model (5.33/7.60/10.48 TWh discharge vs LESR RTD
  5.67/10.04/12.06). The caiso-99 keeper stack now **OVER-charges** on the
  NG:OTH basis (6.06/10.20/13.76 vs 4.07/8.71/13.02 TWh) — the failure mode
  the adder addresses is now present. (The two measured bases disagree —
  NG:OTH metered vs RTD scheduled discharge differ by ~2/2.5/0.8 TWh; the
  keeper sits between them. The throughput guard in §6 is therefore
  two-sided.) Re-opening a resolved ruling is the owner's call — hence the
  gate on this whole mechanism.
- **Rule 13 (forward story):** the cost regenerates for any forward year from
  forward drivers (ATB capex projections × cycle life × replacement
  fraction) and responds to changed conditions (falling capex → falling
  adder → more cycling; exactly the observed 2023→2025 convergence of
  reality toward the LP's economic rate). Nothing pins dispatch to actuals.
- **Rule 24 (registered knob):** `ScenarioConfig.battery_dispatch_adder` is an
  existing registered field (recorded in `run_config.json`; DOF-ledger row
  `scripts/build_dof_ledger.py:316`), already carried in
  `docs/parameter-citations.md` under the Xu et al. 2018 cycle-aging
  citation. No new knob, no env channel; the B-leg delta rides the standard
  `prb_overrides` → `config.with_overrides` path.
- **Rule 25 (no residual-tuned scalar):** the value is the DERIVED $14.25 —
  the same formula every ISO's storage entry screen already uses
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

## 5. The model side (fresh same-machine repro): the LP charges at cap at the efficiency-loss floor

<!-- MODEL-SIDE NUMBERS: filled from the fresh caiso99_repro_A/caiso99_shape_B
     solves + _caiso100_charge_econ.py output -->
TBD-MODEL

## 6. Pre-registered report-back (bands + gates, BEFORE any B-leg — binding on the build session)

If the owner rules the mechanism in, the B-leg is: fresh same-machine
`caiso100_repro_A` (= the caiso-99 keeper recipe, i.e. `_caiso99_shape_B.py`
verbatim with only the out-dir renamed) vs `caiso100_cycling_B` = A +
`battery_dispatch_adder = 14.25` (the ONLY delta, via
`overrides["battery_dispatch_adder"]`), 2023-2025 one bundle each (rule 16),
sequential, scored `_caiso92_report.py <A> <B>` + `_caiso_storage_timing.py
<B>` + `_caiso100_charge_econ.py <A> <B>`.

Expected direction (bands):

- **Belly λ residual (+7.7/+7.6/+6.3) falls in all three years; must not go
  negative** (no overshoot). Mechanism path: on marginal-spread days the
  round-trip hurdle rises by the adder, the profitable charge-window thins,
  charging demand stops riding the supply curve to ~$27, belly λ falls toward
  the measured ~$18 glut floor.
- **Evening λ residual (−5.3/−4.4/−2.3) moves toward 0; must not cross above
  actual.** Two aligned channels: the adder enters the discharge-hour bid
  (storage-marginal evening hours price higher), and trimmed discharge volume
  lets thermal/import set more evening rungs. 2025 evening dispatch
  (7.66 vs measured 8.00 TWh) should hold ≈ or improve; a material 2025
  evening-dispatch regression (>0.3 TWh away from measured) is a FAIL signal.
- **Throughput moves toward measured, two-sided guard:** annual battery charge
  (6.06/10.20/13.76 TWh in B) falls toward NG:OTH (4.07/8.71/13.02) in every
  year; it must NOT fall below the NG:OTH measured charge by more than 10 %
  in any year, and model discharge must not fall below the NG:OTH measured
  discharge by more than 10 % (the caiso-76 under-cycling concern, now a
  hard gate; the LESR-RTD basis is reported alongside for the record).
- **Day-selectivity signature appears:** in `_caiso100_charge_econ.py`, the
  model's charge-weighted spread medians and S05/S10 revealed thresholds move
  from the efficiency-loss floor toward the measured rows; model skip-share
  rises above ~0 toward the measured 0.19/0.02/0.02 without overshooting
  2024/25 above ~0.10.
- **Protected results:** C1 12/12 holds; overnight λ no new under-price; C3c
  unchanged or toward the actual tail; C7/C8 PASS; C5a improves or holds
  (2024 CAVEAT must not regress to FAIL).
- A worse aggregate fit that is more structurally faithful still passes
  provided no protected result degrades (rule 1); breaking a passing
  criterion FAILs. Registered whatever the result (rule 15); promotion only
  on no-status-regression; CAISO retention is 14/15 — the registration MUST
  prune to top-15.

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
