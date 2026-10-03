# BARS — closeout-MISO-w2 phase 0: L3/L4 census retest on the nuclear-repaired keeper (written before any new-keeper number)

```
LANE    : closeout-MISO-w2 (desk charter 2026-10-03; plan §3.3 step 2)
KEEPER  : 2026-10-03-closeout-miso-nuc-r (results/calibration/closeout_miso_nuc_span), unchanged
LP      : none. Fleet-only rebuild + the wave-1 bid-stack census, re-pointed at the new keeper
PROBE   : scripts/probes/_closeout_miso_w2_l3l4_retest.py (wrapper; the wave-1 census code unchanged)
```

## Why a retest (rule 28: new evidence)

Wave 1 (FINDING-closeout-miso-wave1-2026-10-02 §2) killed every L3/L4 arm on the miso-280 keeper, where C3a 2020
read +11.6 % (need −$0.35/MWh annual) and COAL_PRB 2019/21/22 read +6.40/+5.68/+5.28 TWh. The R-43/R-53 nuclear
repair (rule 14 data) changed both sides of that gate: C3a 2020 now reads +10.2 % (model $24.21 vs $21.97; need
−$0.043/MWh annual) and COAL_PRB reads +4.56/+5.03/+5.72. The pre-stated gate was sized to the old residual, so the
cells are re-measured on the new baseline. **Disclosure:** the wave-1 old-keeper arm numbers are known to this lane;
the bars below rescale the plan's own ex-ante gate by the same margin, they are not chosen from those numbers.

## Admissible arms

`L3` (registered `coal_econ_marginal_hr_two_sided`), `L3flag` (the registered flag exactly), `L4a`, `L4b`,
`L3+L4a`, `L3+L4b`. **`L3stack` is excluded**: the registered field's own docstring says the ratio *replaces* the
band multiplier, never stacked (rule 19); it is reported for the record only and can never clear.

## Bars (2020 primary; every bar must hold for an arm to clear)

| bar | statement | source of the number |
|---|---|---|
| B1 price | 2020 static q1–q4 load-weighted ΔP ≤ −$0.13/MWh **and** all-hours load-weighted ΔP ≤ −$0.13/MWh | plan gate ratio: −$1.0 q1–q4 against a −$0.35 need (≈ 2.9×) applied to the new need −$0.043 |
| B2 coal C1 | keeper C1 + 0.27 × static Δ inside ±8 TWh for COAL_PRB, COAL_BIT, COAL_LIGNITE, every year 2019–2025 | plan gate (PRB 2019/21/22) widened to every coal row/year |
| B3 C3a elsewhere | keeper C3a + static all-hours ΔP / actual (no attenuation, conservative) stays within ±10 % in 2019, 2021–2025 | rubric C3a band |
| B4 gas C1 | 0.27 × static coal Δ taken as gas displacement: CC_REGULAR 2021 not below −8.65 TWh (keeper −8.15, already FAIL; +0.5 TWh worsening is a kill); no other CC_REGULAR / CT / ST_GAS row PASS→FAIL | ex-ante declaration |
| B5 | an arm that clears B1–B4 goes to a PRECOMMIT with ≥ 1 C1 PASS→FAIL declared ex ante if B2/B4 margins < 1 TWh | — |

Static-to-LP conversion 0.27 is the miso-224/225 constant the wave-1 census used (FINDING-miso297 §1.5).
An arm failing any bar is NOT CHARTERED and the lane moves to the next open step.
