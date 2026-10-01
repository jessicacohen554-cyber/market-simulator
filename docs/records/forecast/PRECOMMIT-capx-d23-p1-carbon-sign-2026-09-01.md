# PRECOMMIT — capx D23: attribution frame for the FC-6 P1 carbon-sign failure

**Session:** D23 (capacity-expansion / Forecast Finalization track), branch
`claude/capx-d23-p1-carbon-sign-0x5whn` (charter name `claude/capx-d23-p1-carbon-sign`
plus the harness session suffix). **Date:** 2026-09-01. **HEAD at launch:** `6c7f82da`
(origin/main). **Phase 0:** zero solves beyond the committed arms; precommit-first;
build nothing, tune nothing, arm nothing.

**The object** (D21, `docs/handoffs/FINDING-capx-d21-fc6-battery-2026-08-31.md` §5.2):
under `carbon_price=25.0` on the NEISO t3 golden posture, cumulative 2026–2050 CO2
RISES 210.52 → 320.84 Mt (+52.4 %). Two legs, kept apart throughout:

- **Leg D (dispatch-side):** 2026, byte-identical fleet, CO2 +0.21 Mt (16.32 → 16.53).
- **Leg C (capacity-side):** the CCS retrofit screen converts less under the carbon
  price — 2040 base 13,049 MW `gas_cc_ccs` / 0 MW unabated CC vs carbon arm
  9,993.5 / 4,000 MW; annual CO2 2040 4.49 vs 11.77, 2045 2.67 vs 11.86,
  2050 3.21 vs 13.26 Mt; carbon-arm LW price LOWER in 2040 (59.45 vs 70.53 $/MWh).

This document freezes, BEFORE any number in the committed arms is opened beyond what
D21's finding itself quotes: the candidate causes per leg, the committed evidence for
each, the adjudication rule, the kill that retires each candidate, and my expectations.

---

## 1. Frozen decision rules

- **DEFECT** — the implemented arithmetic deviates from the spec/contract
  (spec §1.5.2, §5.2, §5.6; CLAUDE.md objective line) in a way that changes the
  response sign under the committed configs; OR the pair moved more than its named
  knob (a code conditional lets `carbon_price` arm/disarm/replace a second mechanism).
  A defect in the *instrument or arm construction* (P1's expectation mis-specified for
  the mechanism actually armed) counts as a defect of the INSTRUMENT, not the model,
  and is reported as such.
- **REAL** — code is faithful to spec and the sign is reproduced by the mechanism's
  own economics from the committed inputs. Then per rule 1 `[R-STRUCT]` the result
  STANDS at full magnitude; P1's expectation is routed to its owner for re-examination.
  This lane edits no threshold, no expectation, no verdict.
- **UNATTRIBUTED** — all candidates for a leg die at committed-evidence resolution.
  The honest exit: say so, and route the cheapest discriminating diagnostic (a third
  arm is a director decision; it is priced, named, NOT run here).

**Dependency rule, frozen:** Leg D is adjudicated FIRST. The retrofit screen consumes
the prior year's price signal from the arm's own solves, so any dispatch-side distortion
in 2026–2031 contaminates the capacity screen's inputs. Leg C's attribution must state
whether it is downstream of Leg D or independent of it.

**No-touch list:** no solve; no config/threshold/expectation edit; no verdict or board
write (D21's FC-6 FAIL and the golden's HOLD stand as scored); no keeper/shard/marker
touch; backcast namespace untouched; no holdout year; no new workflow. Mechanism-matrix
duty (a): the NEISO shard is consulted before any repair is proposed; no cell is minted
(nothing is tested here — rule 28's duty (b) does not fire on attribution-by-reading).

## 2. Frozen evidence inventory

Committed artifacts (all already on main; nothing new is produced):

- `results/ff-t3-neiso-golden/bau/fc6/arms/{base,carbon25}/full_horizon_summary.json`
  and `run_config.json` (the pair; gasup150/gaspm5 only as sanity context).
- `results/ff-t3-neiso-golden/bau/full_horizon_summary.json`, `run_config.json`,
  `dof_ledger.json` (the golden = base twin).
- `results/ff-t3-neiso-golden/bau/NEISO/a4b11ef4aaa1be35/evolution_20{26..50}.json` —
  the BASE evolution ledger (per-year exits/retrofits/entries). The carbon arm has NO
  ledger and NO hourly artifacts: its capacity story is read from its summary's
  per-year fields only.
- `results/ff-t3-neiso-golden/bau/fc6/paired_invariants.json` (P1 row as scored).

Code (read, never edited): `src/market_sim/model/capacity.py::apply_ccs_retrofit` and
the retirement screen it is joint with; the marginal-cost assembly site(s) and every
consumer of `carbon_price` under `src/market_sim/` (located by grep — the set of
consumers is itself evidence for D4/C5); the emissions-accounting arithmetic
(`scripts/run_full_horizon.py::_co2_tons`,
`scripts/check_forecast_invariants.py::_annual_co2_tons`) and the per-generator
emission-rate source it reads; `policy/` carbon / cap-and-trade module and its arming;
`scripts/run_full_horizon.py::reference_config` (golden posture);
`config/scenarios.py` + `config/constants.py` for units and citations.

Spec anchors: §1.5.2 (CCUS dispatch mc; "CCUS becomes more competitive as carbon
prices rise"), §5.2 (retirement screen: attainable pro-forma margin, never realized
dispatch), §5.6 (the joint retrofit-or-retire screen: the six-line formula block,
attribute term, §45Q gating `ira_ccus_45q_last_year` at commit year, two-segment
credit-window payback, 3 GW/yr cap, "Known simplifications"), §5.1 step order.

## 3. Leg D (dispatch, 2026, fixed fleet) — candidates and kills

With one consistent per-generator emission-rate array used by BOTH the offer path and
the accounting, a uniform `+er×carbon_price` adder cannot re-order two units so that
accounted CO2 rises materially: switching moves toward lower-er units by construction.
So a genuine +0.21 Mt (+1.3 %) same-fleet rise needs an asymmetry, a second armed
instrument, or an inter-temporal/storage channel. Candidates:

- **D1 — offer/accounting emission-rate asymmetry** (the priced set ≠ the accounted
  set). Concrete flavors: a class whose ACCOUNTING er > 0 but whose OFFER carries
  er = 0 or omits the carbon term (suspect flavor: biomass/wood/refuse — a biogenic
  carbon-price exemption in offers, defensible as market design, colliding with
  stack-CO2 accounting rates ~1 t/MWh; also any branch of the mc assembly that skips
  the term for a subset — imports, must-run tranches, bin tranches).
  **Kill:** the mc assembly consumes the SAME er array as `_co2_tons` /
  `_annual_co2_tons`, with no mask/zero/exemption/branch between them, for every
  dispatchable class in the NEISO fleet context.
  **Confirm:** such a class exists AND the summaries' aggregate deltas are consistent
  with it expanding under the carbon price (its accounting er above the displaced
  class's).
- **D2 — sign or unit error in the carbon term** (subtraction; $/ton vs t/MWh vs
  lb/MWh mismatch; price applied per-MMBtu).
  **Kill:** the term is `+ er × carbon_price` with er in t/MWh and price in $/t
  (constants citations confirm), and the 2026 LW-price delta between arms is positive
  and order-of-magnitude `er_marginal × 25` (≈ +$5–15/MWh). A ~0 or negative 2026
  price delta re-opens D2/D4 hard.
- **D3 — storage/renewable interaction** (higher/reshaped prices → more cycling
  losses or shifted charge sourcing; curtailment/dump changes).
  **Kill:** no carbon-dependent term in storage/renewable offers other than through
  prices, AND any summary-visible storage/curtailment delta implies ΔCO2 well under
  the 0.21 Mt it would need to carry (bound: Δlosses × max fleet er). If the summary
  carries no such fields, D3 is bounded structurally and reported as residual-possible
  only if D1/D2/D4/D5/D6 all die.
- **D4 — pair semantics / second carbon instrument** (shared with C5): the base is not
  actually a zero-carbon-signal world (an armed cap-and-trade/RGGI mechanism — NEISO
  is a RGGI region and `policy/` has a carbon module), or `carbon_price>0` disarms or
  replaces that mechanism in code, so the pair is "instrument A" vs "flat $25", not
  "0 vs $25" — and the effective 2026 signal may have gone DOWN. A cap with an
  endogenous dual also fails P1's premise honestly (waterbed): that would be an
  INSTRUMENT mis-specification finding, not a model defect.
  **Kill:** (i) the resolved run_config diff is exactly `carbon_price: 0→25`; (ii) no
  other carbon-signal field is armed/nonzero in the base config; (iii) no code path
  conditions any other mechanism on `carbon_price` (the grep set from §2 is the
  check); (iv) the base 2026 LW price and CO2 are consistent with a carbon-free base.
- **D5 — commitment/floor interaction**: a P0-pattern-detected floor mechanism binds
  differently across arms (carbon changes P0 → different detected min-gen → forced
  dirty MWh). Static floors (fractions of capacity) cancel across arms.
  **Kill:** the NEISO golden posture arms no P0-pattern-dependent mechanism (the three
  bridges are CAISO/ERCOT/NYISO-gated per CLAUDE.md; verify in the resolved config),
  and floor overrides present are static.
- **D6 — import/accounting scope**: the HQ import node (or slack/dump) carries a
  nonzero accounting er, or import offers carry a carbon term they shouldn't, so an
  import-volume shift moves accounted CO2 the wrong way.
  **Kill:** accounting scope is exactly in-region generators × er (imports er = 0 or
  excluded; slack/dump excluded), and import offers carry no `carbon_price` term.

## 4. Leg C (capacity / CCS screen) — candidates and kills

Spec §5.6's own arithmetic prices carbon on both states (full er unabated, residual er
post) against the same price signal; §1.5.2 promises the crossover moves TOWARD CCS as
carbon rises. Under that arithmetic ∂uplift/∂carbon ≥ 0 in every hour class I can
construct (unabated loses er·carbon where inframarginal; post loses only the residual;
price effects enter both sides through the same p[t]). Fewer retrofits under carbon is
therefore contra-spec unless a second input to the screen moved. Candidates:

- **C1 — real mechanism (the charter's benign story, sharpened):** the joint
  retrofit-or-retire choice + two-segment credit-window payback + 3 GW/yr cap +
  §45Q commit-year eligibility (`ira_ccus_45q_last_year`, default 2032) produce a
  genuine "carbon price delays/displaces marginal retrofits past the eligibility
  edge, after which `uplift_post ≤ 0` strands them unabated" outcome, or a genuine
  certificate-interaction (attr term) crowding-out.
  **Confirm (residual + reconstruction):** C2–C5 all die AND the sign is reproduced
  arithmetically from the code's actual formulas under the committed config values
  with price levels taken from the arms' own per-year summaries (no new solve). The
  reconstruction must name WHICH screen input moved (p[t] level/shape, attr, window
  edge, pool) and survive the Leg-D contamination check (§1 dependency rule).
  If confirmed: the result STANDS (rule 1); P1's expectation goes to its owner.
- **C2 — carbon asymmetry inside the screen** (counts carbon on one side only, full
  er on the post state, q45 netted against carbon, price signal and cost stacks at
  inconsistent carbon vintages).
  **Kill:** `apply_ccs_retrofit` implements the §5.6 block verbatim-in-substance:
  carbon in `mc_unabated` at full er and in `mc_post` at residual er, both margins
  over the SAME prior-year price signal, ΔFOM per spec, attr per
  `effective_eac_price_for_unit`, q45 only in `m_window`.
- **C3 — wrong-counterfactual volume** (a margin valued on realized prior dispatch
  instead of the pro-forma attainable construction — carbon suppresses unabated
  running, dragging the computed CCS value down with it).
  **Kill:** both continuations are `Σ_t max(0, p[t] − net_mc) × avail` per MW —
  no realized-generation volume anywhere in the screen.
- **C4 — pool/entry channel:** the 2040 carbon-arm 4,000 MW unabated CC (and the
  +944.5 MW CC-family excess over base) is not surviving-screened capacity at all but
  (a) new entry of unabated CC whose entry screen misprices carbon (missing er×carbon
  in the candidate's cost, or no CCS-new-build alternative offered), or (b) an
  eligibility-pool artifact (carbon-arm CCs retired pre-`ccs_retrofit_available_year`,
  then scarcity backfilled with new unabated CC).
  **Adjudicate:** base evolution ledger (exits/retrofits/entries per year) + both
  summaries' per-year capacity-by-fuel steps (a rise in CC-family total = entry; a
  fall = exit) + entry-screen code for the carbon term. Entry of unabated CC with
  carbon correctly priced and no cheaper abated alternative available is a REAL
  component; carbon missing from the entry economics is a DEFECT.
- **C5 — pair semantics** (= D4, shared kill).

## 5. Frozen adjudication order

1. Pair construction: diff the two resolved `run_config.json`s; enumerate every
   `carbon_price` consumer in `src/market_sim/` (kills or confirms D4/C5 first —
   cheapest, and everything else conditions on it).
2. Series extraction from the two summaries: per-year co2, LW price, capacity-by-fuel
   (whatever the 13 fields are). Decompose the +110.32 Mt cumulative gap into
   pre-2028 (pure dispatch era) vs 2028+ (screen era); locate the CCS-trajectory
   divergence year; record the 2026 price delta (D2's sanity leg).
3. Dispatch-side code reading: mc assembly + er sources + accounting scope + storage /
   import / floor gating → adjudicate D1, D2, D3, D5, D6.
4. Capacity-side code reading: `apply_ccs_retrofit` vs the §5.6 block; retirement
   interplay; entry screen carbon handling → adjudicate C2, C3, C4.
5. Synthesis per leg against these frozen kills; C1 residual reconstruction if
   reached; magnitude accounting (attributed cause must plausibly carry the Mt).
6. Routing: repairs named, priced, admissibility screened (rules 13/21), NOT built;
   any REAL verdict escalated to the P1 expectation's owner (rule 1); director report.

## 6. Pre-stated expectations (before looking)

- **Leg D: I expect a DEFECT.** Primary: D1 (emission-rate asymmetry between the
  offer path and the accounting; the biogenic/biomass exemption is my named concrete
  flavor). Secondary: D4 (a second armed carbon instrument / knob semantics). I
  consider a benign explanation unlikely (~1-in-10): a uniform, consistently-priced
  carbon adder on a fixed fleet should not raise accounted CO2 by +1.3 %.
- **Leg C: I expect a DEFECT on balance, but with a real chance the model is right in
  a surprising way.** The spec's own text promises the opposite sign, so EITHER the
  implementation deviates (C2/C3/C4-defect flavors) OR the composite mechanism
  (window-edge stranding / certificate crowding / joint-choice, C1) genuinely
  produces it — I put it roughly 60/40 defect-vs-real, and if it is real the result
  stays and P1's expectation is the object under re-examination, not the model.
- **Magnitude:** I expect Leg C to carry the large majority of the +110.32 Mt
  (the three quoted late years already sum to +26.5 Mt and the fleet divergence is
  persistent), and Leg D to contribute ≲ 0.3 Mt/yr before 2028. If the pre-2028 gap
  is instead multi-Mt/yr, my leg model is wrong and I say so in the finding.
- **Interaction:** I expect the capacity leg to be at least partly downstream of the
  dispatch leg through the screen's prior-year price signal; the finding will state
  the direction of that contamination explicitly.

## 7. Exit contract

`docs/handoffs/FINDING-capx-d23-p1-carbon-sign-2026-09-01.md`: each leg attributed
against its own frozen kill above; repairs ROUTED (priced, rules 13/21 admissibility)
and NOT built; an explicit statement of which leg is a defect and which — if either —
is the model being right in a way we did not expect; leg magnitudes at full size;
director report in-session. Any candidate adjudicated outside this frame (a cause I
did not enumerate) is reported as such, flagged as post-hoc, and held to the same
evidence standard.
