# FINDING pjm-146 — PJM RGGI allowance cost: the mechanism is real and live, the model's response to it is too elastic

**Verdict: `state_carbon_pricing` PJM `U → O`. Built, solved, registered, all five
pre-registered gates PASS — and LEFT PENDING, not armed.** Keeper UNCHANGED
(`2026-07-31-pjm-143b-hy-level`); `pjm_rggi_allowance_pricing` stays default-**off**.
Promotion is an owner decision (PREREG §4 verdict mapping: `U → K` only on owner
promotion, `U → O` if left pending).

Charter: `docs/handoffs/pjm-matrix-column-triage-2026-08.md` §2.1 (the triage's rank-1
live candidate). Pre-registration: `results/calibration/PREREG-pjm146-rggi-allowance-2026-08-02.md`,
committed before either arm solved. Machine record: `results/calibration/_pjm146_rggi_ab.json`.

## 1. The arms

| | run id | bundle |
|---|---|---|
| control | `2026-08-02-pjm-146a-control-zerodelta` | `pjm146_control_A` |
| arm | `2026-08-02-pjm-146b-rggi-allowance` | `pjm146_rggi_B` |

Single delta: `ScenarioConfig.pjm_rggi_allowance_pricing=true`. Years 2023/2024/2025 in
one bundle per arm (rule 16 `[R-ALLYEARS]`), sequential, chained with `--reuse-solved`
(rule 12 `[R-PARALLEL]`).

**Same-HEAD equivalence, proven not assumed.** The control solved at `7cc95fa`, the arm at
`886fbe8`. The entire `src/` delta between them is one new `"ERCOT"` entry in
`GAS_OFFER_MARGIN_ANCHOR_BY_ZONE`; every other changed line in `constants.py` is a comment.
The PJM keeper carries `gas_offer_margin_zonal_anchor` off (pjm-144 adjudicated it `I`), so
an ERCOT-keyed dict entry cannot reach a PJM solve. Main moved again mid-session (FFR-2A
`resolve_gas_scenario_path`), but that refactor diverges only for crossover runs and this
keeper is `mode=backcast, crossover_forward_year=None` — a no-op here, so no re-solve is owed.

## 2. Zero fitted parameters

Prices are the published RGGI quarterly-auction clearing-price annual means,
metric-converted at 1 short ton = 0.907185 t: **14.87 / 22.83 / 24.35 $/tCO2** for
2023/2024/2025. Membership is an exact per-plant EIA-860 state test against
`RGGI_MEMBER_STATES_BY_YEAR` (NJ/MD/DE all years; VA 2023 only), with the committed
`PJM_RGGI_ZONE_SHARE` fractional fallback used only for synthetic rows. Emission rates are
the fleet's own. DOF ledger **18 → 19 entries** (`identification: measured-external`) with
**`n_residual` UNCHANGED at 6**.

Rule-13 `[R-MEASURED]` admissibility: the quantity regenerates for a forward year from a
forward driver (an allowance-price path) and responds to changed conditions. It is an input,
not an answer.

## 3. Gates — all five pass

| gate | result |
|---|---|
| **K1** mechanism live at its own grain | PASS — mc identity exact to **3.7e-13** (tol 1e-9), hour-invariance 4.5e-13; 871/456/457 units carry a nonzero adder (bar: ≥50) |
| **K2** control integrity (strict byte) | PASS — **0.0 MW** max diff on every class in all three years vs the committed keeper |
| **K3** membership audit | PASS — `va_expected` 1.0 in 2023, 0.0 in 2024/25 across 719 VA units; non-member zero and member-core both confirmed |
| **K4** sign | PASS — ΔLMP > 0 in all three years |
| **K5** liveness | PASS — see §4 |

**Two honest caveats on the audit itself.** (a) K1/K3 recompute from a
`run_year(fleet_only=True)` **rebuild** (3407 rows), not the solved fleet (2816) — that is
what PREREG §4 asks for ("probe recomputes from the built fleet"), and K2 is what covers the
solved side. Both arms share the rebuild, so the identity test is valid. (b) The runtime
logs `(carbon_mc > 0)` — rows in member zones of *any* fuel — while the scorer counts rows
with a nonzero *mc adder*; that is why the solve log reads 966/496/497 and K1 reads
871/456/457. The two count different populations and neither contradicts the other.

## 4. It is price-live, and that refutes the pjm-144 read

| year | control | arm | Δ | Δ% |
|---|---|---|---|---|
| 2023 | $31.4213 | $32.8439 | **+$1.4226** | +4.53 % |
| 2024 | $31.1943 | $32.6222 | **+$1.4278** | +4.58 % |
| 2025 | $42.3679 | $43.6275 | **+$1.2595** | +2.97 % |

All three inside the ex-ante **E1b band of +$0.20 … +$2.50/MWh** — prediction CONFIRMED.

The near-flat dollar delta across 2023→2024 reconciles arithmetically despite the footprint
halving: the member-CC adder rises 54 % ($5.50 → $8.45/MWh at ~0.37 t/MWh) while
member-marginal frequency falls ~35 % with Virginia's exit; 0.65 × 1.54 ≈ 1.00.

**This is NOT the pjm-144 outcome, and the contrast is structural.** At pjm-144 PJM's
price-coupled zones absorbed a *mean-zero* redistribution into inertness (`I` by its own K3
rule). Here the same coupling **transmits** a *one-signed level* shift: ComEd carries 0.0
membership and still rises +$1.204, Dominion rises +$1.415 in 2024 when Virginia is already
out. Coupling is therefore **not a general bar on PJM zonal-cost levers** — it kills
zero-sum spreads and propagates level shifts. That is a reusable finding.

**E1's zonal secondary is PARTIALLY REFUTED, recorded not patched.** Its "EMAAC/SWMAAC lead,
ComEd trails" half holds; its "+DOM 2023" clause does not discriminate, because Dominion
rises just as much in the years it is not a member. The zonal signature is driven by
coupling and the marginal-unit mix, not by the membership map.

## 5. What improves — and it is real

- **D-2 strictly improves.** All three CT_PEAKER forced-share FAILures clear:
  0.1541/0.1579/0.1591 → **0.1328/0.1203/0.1298** against the 0.15 peaker cap. Cause is
  mechanical: CT_PEAKER economic dispatch rises (+3.67/+5.89/+5.09 TWh) and dilutes a fixed
  floor.
- **C3a-2025 improves** (−9.0 % → −6.3 % vs DA). **C3c bit-identical** — the 1 h / 2.5 h
  margins the PJM queue flags as its thinnest are untouched. C3b, C4, C6, C7, C8 all PASS.
- **RGGI leakage is reproduced endogenously**, not assumed. Member-state CC is taxed while
  non-member coal is not, so:

| TWh | 2023 | 2024 | 2025 |
|---|---|---|---|
| CC_REGULAR | −12.80 | −14.78 | −10.00 |
| CT_PEAKER | +3.67 | +5.89 | +5.09 |
| COAL (BIT+PRB+WC) | +3.54 | +2.29 | −0.12 |
| ST_GAS | +1.16 | +1.27 | +1.43 |
| import (net) | +2.42 | +1.96 | +1.32 |

Nuclear, wind, solar and hydro are bit-unchanged. Imports are **not** charged —
`PJM_RGGI_ZONE_SHARE` covers only the 8 internal zones, so external nodes take 0.0
membership; imports rise because domestic member CC got dearer.

## 6. Why the keeper is unchanged

**Determination CALIBRATED → NOT-YET; 0 fails → 2 fails.**

- **C3a 2023 FAILS at +11.1 %** (from the control's +2.99 %; band ±10 %). E1d
  **pre-declared this direction and licensed it** under rules 1/14 — the fitted offer
  surfaces were identified on an uncompensated stack, so a level shift was expected.
- **C1 FAILS on CC_REGULAR VOLUME**: −16.06 TWh in 2023 (share −1.3 pp) and −13.84 TWh in
  2024 (−0.7 pp), against the control's passing −3.3 TWh. C1 all 16/16 · free 12/12 →
  **all 14/16 · free 10/12**.

**E1d did not license the C1 move.** No C1 magnitude gate was pre-registered, so this is an
**unpredicted regression on a load-bearing criterion in the class carrying ~40 % of ISO
load**. That distinction is the whole basis of the recommendation: a price-level regression
was anticipated and argued for in advance; a fuel-mix volume regression was not.

**Reading: right in KIND, too elastic in MAGNITUDE.** The RGGI cost is real and measured, and
charging it is correct. But real PJM CC units did not shed 16 TWh to non-member coal — the
measured fuel mix says so. Something damps real-world leakage that the model lacks
(bilateral/capacity cost recovery, contractual must-run, or a wider true merit gap between
member CC and non-member coal). Rule 14 `[R-ACCURATE]` is explicit that a worse fit from an
accurate input is a signal to **find the root cause, not bury it** — so the input stays
available and default-off while the elasticity is investigated, rather than being deleted or
being armed on the level story alone.

**Unscored consequence, flagged not hidden.** System CO2 likely **RISES** — roughly
+1.3 Mt in 2023 on representative class rates (CC 0.37, coal 0.95, CT 0.55, ST_GAS 0.60
t/MWh) — and net imports rise, moving emissions off-footprint entirely. PJM's rubric scores
no CO2 criterion and the committed sidecars carry no emissions column, so this is an
**estimate**, not a measurement. It is the expected consequence of a partial-footprint
carbon price and it is what makes the elasticity question consequential rather than cosmetic.

## 7. Successor — the named lane

**The CC→coal substitution elasticity under a partial-footprint carbon price.** This arm
measured it for the first time, and the C1 volume miss sizes it: the model moves ~13–16 TWh
where reality moves materially less. A successor needs its own charter and must identify the
damping mechanism from PJM's own record — not tune a haircut onto the adder, which rule 13
forbids and which would destroy the zero-DOF property that makes this mechanism admissible
at all.

**Do NOT** re-arm `pjm_rggi_allowance_pricing` on the price-level story alone, and do not
place the price registry in `STATE_CARBON_PRICE_BY_ISO` without an owner decision — that
would silently re-arm every PJM backcast under default-True `state_carbon_pricing` (a
same-key cache invalidation).

## 8. Incidental: a diagnostics-basis defect worth carrying

The arm's `legitimacy_diagnostics.json` had to be regenerated **three times** before it was
comparable to the control's, and the reason generalises. D-2's failure list depends on
artifacts that are not all committed:

1. Run **unregistered** → `load_share` is `null`, so rule 20's ≥2 %-of-load materiality test
   cannot be applied and a different class set is flagged.
2. Run registered but scored on the **full** bundle → `dispatch/`, `floors/`, `unit_hourly_*`
   and `network_*` are **gitignored**, so a full-basis artifact resolves mechanisms
   (`nuclear_mustrun`, CHP classes) that no one can reproduce from the committed tree, and
   that the slim-basis control cannot match.
3. Only on the **committed slim file set** are the two arms comparable (both 12 summary rows,
   6 mechanisms).

This is the same class of defect as the caiso-155 `diagnostics_plant_set` charter. Any A/B
that compares a fresh bundle's diagnostics against a committed bundle's is comparing
coverage, not dispatch. **Score both arms on the committed file set.**
