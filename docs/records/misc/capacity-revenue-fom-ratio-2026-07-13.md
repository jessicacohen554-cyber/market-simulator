# Per-fuel capacity-revenue / going-forward-cost ratio check — 2026-07-13

**Session.** Direct follow-up to
`docs/handoffs/equilibrium-battery-2026-07-12.md` §6 item 3 (P-3B), which
found NEISO retires **0 MW of thermal capacity across the entire 25-year
reference horizon** and hypothesized the flat `$95k/firm-MW-yr` capacity
payment alone exceeds FOM-only going-forward cost for every unit, making the
energy-margin term irrelevant to the retirement screen. This is a pure
arithmetic check against `ScenarioConfig`/`constants.py` — **no LP solve**.

## 1. Method

`apply_economic_retirements` (`market_sim/model/capacity.py:1386-1400`)
compares, per unit:

```
net_revenue        = energy/reserve margin + attribute revenue + capacity revenue + AS revenue
going_forward_cost  = fixed_om_<fuel>(config) * fom_multiplier_<fuel>(config) * pmax_mw * 1000   # $/yr
```

The capacity term alone is `capacity_revenue_per_mw_yr` (`capacity.py:604`):

```
capacity_revenue_per_mw_yr = net_cone_per_kw_yr(iso) * 1000 * (1 - EFORd[fuel])   # $/MW-yr, flat
```

(`capacity_market_clearing=False`, the P-2A default active in every P-3A/P-3B
run — see prior handoff §2.) This report computes, per fuel, per ISO:

```
ratio = capacity_revenue_per_mw_yr / going_forward_cost_per_mw_yr
      = net_cone_per_kw_yr(iso) * (1 - EFORd[fuel]) / (fixed_om_<fuel> * fom_multiplier_<fuel>)
```

`ratio > 1.0` means the capacity payment **alone** clears the going-forward
cost bar with room to spare — the energy-margin, attribute-revenue, and AS
terms are all structurally unnecessary for that unit's retirement decision
never to trigger (`net_revenue < going_forward_cost` can never hold, since
`net_revenue >= capacity term` and `capacity term / going_forward_cost > 1`
already). Inputs, all direct reads, no derivation:

| Source | Fields |
|---|---|
| `config/constants.py:760-773` | `EFORD` (per-fuel forced-outage rate) |
| `config/constants.py:2558-2650` | `MARKET_DESIGN[iso].net_cone_per_kw_yr` (fixed-mode anchor) |
| `config/scenarios.py:338-362` | `ScenarioConfig.fixed_om_*` defaults (NREL ATB 2024 / EIA-S&L) |
| `config/scenarios.py:289-296` | `ScenarioConfig.retirement_fom_multiplier_*` defaults (coal=1.3, else 1.0) |

## 2. Result — NEISO (net_cone = $95,000/firm-MW-yr)

| Fuel | EFORd | UCAP (1-EFORd) | Cap. revenue $/kW-yr | FOM×mult $/kW-yr | **ratio** | Verdict |
|---|--:|--:|--:|--:|--:|---|
| gas_ct | 0.06 | 0.94 | 89.30 | 21.0 | **4.25** | capacity alone covers 4.3x |
| gas_cc_ccs | 0.05 | 0.95 | 90.25 | 25.0 | **3.61** | capacity alone covers 3.6x |
| oil | 0.10 | 0.90 | 85.50 | 25.0 | **3.42** | capacity alone covers 3.4x |
| gas_cc | 0.05 | 0.95 | 90.25 | 30.0 | **3.01** | capacity alone covers 3.0x |
| gas_st | 0.07 | 0.93 | 88.35 | 35.0 | **2.52** | capacity alone covers 2.5x |
| coal | 0.08 | 0.92 | 87.40 | 58.5 (45×1.3) | **1.49** | capacity alone covers 1.5x |
| **nuclear** | 0.03 | 0.97 | 92.15 | 130.0 | **0.71** | **capacity alone is NOT enough** |

**Hypothesis: confirmed for every fossil fuel, refuted for nuclear.** All six
fossil/CCS classes clear ratio > 1.0 on the capacity payment alone (1.49x–4.25x)
— for those units the energy-margin term in `net_revenue` is provably
irrelevant to the retirement decision; they cannot fail the screen regardless
of how negative the energy margin gets. Nuclear is the one fuel where
`capacity_revenue < going_forward_cost` on its own (ratio 0.71) — nuclear's
observed zero-retirement instead depends on the *other* revenue terms
(§45U PTC / ZEC-CES attribute revenue, `capacity.py:1330-1342`, plus energy
margin), which the model does supply and which is why nuclear also retired 0
MW in the P-3B run — but that's a *different*, non-degenerate mechanism from
the fossil case, not a second instance of the same bug.

## 3. Cross-ISO comparison (all capacity-market ISOs, fixed-mode net-CONE)

`ratio = net_cone_per_kw_yr(iso) × (1-EFORd) / (FOM × mult)` — only `net_cone`
varies by ISO (FOM/EFORd/multiplier are ISO-agnostic globals):

| ISO | net_cone $/kW-yr | gas_ct | gas_cc | gas_st | coal | oil | gas_cc_ccs | nuclear |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| NYISO | 110.0 | 4.92 | 3.48 | 2.92 | 1.73 | 3.96 | 4.18 | 0.82 |
| PJM | 100.0 | 4.48 | 3.17 | 2.66 | 1.57 | 3.60 | 3.80 | 0.75 |
| **NEISO** | **95.0** | **4.25** | **3.01** | **2.52** | **1.49** | **3.42** | **3.61** | **0.71** |
| CAISO | 90.0 | 4.03 | 2.85 | 2.39 | 1.42 | 3.24 | 3.42 | 0.67 |
| MISO | 80.0 | 3.58 | 2.53 | 2.13 | 1.26 | 2.88 | 3.04 | 0.60 |
| ERCOT | 0.0 (energy-only) | **0** | **0** | **0** | **0** | **0** | **0** | **0** |

**Every capacity-market ISO clears ratio > 1.0 for all six fossil/CCS fuels**
(range 1.26–4.92 across the registry) — the finding is not NEISO-specific;
it is a structural property of the flat fixed-mode capacity price wherever
it is active. MISO's coal ratio (1.26) is the closest to the ratio=1.0
cliff of any ISO/fuel pair in the registry, meaning MISO's economic-coal
retirement screen is the least insulated from the energy-margin term among
the five capacity-market ISOs — everywhere else the buffer is larger.
Nuclear is below 1.0 in **every** capacity-market ISO (0.60–0.82), so the
nuclear caveat in §2 generalizes: nuclear retirement decisions are never
capacity-payment-only anywhere in the registry, by construction (its FOM,
$130/kW-yr, exceeds every registered `net_cone_per_kw_yr` outright before
even applying UCAP or fuel-specific multipliers).

**ERCOT (`ratio = 0` by construction, `MARKET_DESIGN["ERCOT"].capacity_market
= False`)** is the structural contrast the P-3B report already surfaced
(T2.5): with the capacity term forced to zero, `net_revenue < going_forward_cost`
can only be avoided through energy/reserve margin and attribute revenue —
exactly the channel a negative demand shock (the +10 GW overbuild probe)
suppresses, which is why ERCOT retired 11.7 GW in the first post-shock year
while NEISO retired 0 MW under the identical shock. This ratio check gives
the *static*, config-level explanation for that *dynamic* result: NEISO's
fossil fleet is retirement-screen-immune by construction (ratio > 1 for
every fossil fuel, in every capacity-market ISO), while ERCOT's fleet has no
such floor at all.

## 4. Scope and caveats

- **Fixed-mode only** (`capacity_market_clearing=False`, the P-2A-recommended
  default, active in every run cited above). A `capacity_market_clearing=True`
  run would replace `net_cone_per_kw_yr` with the CR-1 sloped VRR-curve price
  for PJM/NYISO/NEISO (CAISO and MISO keep the fixed anchor even when the
  flag is on — no `demand_curve` registered for MISO, and CAISO is
  documented low-fidelity, §2571-2571 constants.py) — untested here per the
  P-2A degeneracy caveat already on record; not attempted (rules 1/11/14,
  findings only).
- **FOM-only comparison, not the full screen.** `going_forward_cost` in the
  real screen is unconditional (always FOM × multiplier); this report
  isolates `capacity_revenue` as the sole numerator to show it alone clears
  the bar. The real `net_revenue` also adds energy margin, attribute
  revenue, and AS revenue on top — all strictly ≥ 0 in the model's
  `max(0, ...)` construction — so a ratio > 1.0 here is sufficient, not
  merely suggestive, proof that the unit's `net_revenue < going_forward_cost`
  branch is unreachable.
- **Fleet composition not independently re-verified this session.** The
  ratio is fuel-type-generic (keyed on `ScenarioConfig`/`constants.py`
  fields, not a specific unit), so it applies to whichever of these seven
  fuel types NEISO's registered thermal fleet contains; a fleet-loader
  call to enumerate NEISO's actual fuel mix was attempted but the
  general-purpose fleet loader entry point wasn't located in the time
  available (`market_sim.data.fleet` exposes no top-level `load_fleet`; the
  master-plant-registry reference CSV on disk is ERCOT-only). Does not
  affect the ratio arithmetic itself, which holds for any unit of a given
  fuel type regardless of which ISO's fleet it sits in.
- **Confirms, does not fix.** No model code, threshold, or FOM value was
  touched (rules 1/11/14). This is a prerequisite finding for the
  `capacity_market_clearing=True` / CR-1 chain already tracked in
  `equilibrium-battery-2026-07-12.md` §8 item 1, and specifically answers
  that report's item 3 follow-up request.

## 5. Bottom line

The P-3B hypothesis is **confirmed for fossil fuels, in every capacity-market
ISO in the registry, not just NEISO**: under the active fixed-price capacity
mechanism, the flat capacity payment alone exceeds FOM-only going-forward
cost for every fossil/CCS fuel class (ratio 1.26–4.92), so the energy-margin
term is structurally decorative for those units' retirement decisions — no
amount of energy-price collapse can retire them through the economic screen
as currently gated. Nuclear is the one class where the capacity term alone is
insufficient everywhere (ratio 0.60–0.82); its own zero-retirement result
runs through the attribute-revenue channel instead, which is a distinct,
identifiable mechanism (§45U/ZEC-CES) rather than a second copy of the same
degeneracy. This sharpens the P-2A/CR-1 prerequisite chain: the flip to
`capacity_market_clearing=True` needs to move fossil ratios below the
retirement-relevance line for the energy-margin term to start mattering
again — a soft (CR-1 sloped) price is necessary but not obviously
sufficient unless the resulting cleared price falls under the lowest fossil
FOM bar (`fixed_om_gas_ct = $21/kW-yr`, the binding constraint) at some
achievable reserve position.
