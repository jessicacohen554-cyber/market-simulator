# PRE-COMMIT ADJUDICATION — ERCOT-115 promotion gate of `coal_econ_marginal_hr_bound`

**Written 2026-07-26, BEFORE the floor-alone arm was solved.** Rule 1: the criteria are
fixed here so the verdict cannot be reverse-engineered from the residual.

## What is being gated

`ScenarioConfig.coal_econ_marginal_hr_bound` (default **off**): each coal class's economic
band (`econ_low`/`econ_high`) is floored at the ISO's own measured CAMPD marginal-HR p50
(`data/raw/reference/ercot_campd_marginal_hr_summary.csv`, `marg_econ_low_p50 = 0.886`,
`marg_econ_high_p50 = 0.898`). Against the keeper's resolved ERCOT curve this lifts
**exactly one band**:

| class | band | keeper | measured basis | lifted? |
|---|---|---|---|---|
| **COAL_PRB** | `econ_low` | **0.400** *(fitted)* | 0.886 | **YES → 0.886** |
| COAL_PRB | `econ_high` | 1.380 | 0.898 | no (markup above basis) |
| COAL_LIGNITE | `econ_low` | 1.216 | 0.886 | no |
| COAL_LIGNITE | `econ_high` | 1.113 | 0.898 | no |
| COAL / COAL_BIT / COAL_WC | both | 0.90–1.10 | 0.886 / 0.898 | no (generic, no ERCOT plants) |

This is a **rule-13 measured input** (a physical incremental heat rate, reproducible for a
forward year, responsive to changed conditions) replacing a **fitted 0.400 with no
measurement behind it**. Per rules 1/13/14 the mechanism stays in the codebase regardless
of what the residual does; rule 26 `[R-DELETE]` says the fitted value should ultimately be
*removed*, not left re-armable. **This gate decides promotion into the ERCOT keeper only —
not the mechanism's legitimacy.** Not promoting is NOT reverting.

## Why this solve exists

The floor has never been solved on the configuration promotion would create.

| config | coal floor | `ercot_thermal_dam_availability_coal` |
|---|---|---|
| keeper `ercot_netrev_margin` | no | **no** (the keeper pins CC_REGULAR / CT_PEAKER / ST_GAS only — gas, not coal) |
| ERCOT-112 arm **B** | no | yes |
| ERCOT-112 arm **T** (the 4/4 PASS) | **yes** | yes |
| **ERCOT-115 arm F** (this solve) | **yes** | **no** ← never solved |

## Correction to the charter's assumed baseline (recorded before solving)

The ERCOT-115 charter set a criterion "annual coal ratio moves toward 1.0 in ≥2/3 years
(keeper baseline is in the ERCOT-112 finding's table)". **That premise is wrong and is
corrected here, before any ERCOT-115 result exists.** The ERCOT-112 table's baseline is
**arm B**, not the keeper. Re-scoring the keeper's own committed `hourly/` sidecars
against the same EIA-930 benchmark
(`ercot112_score_coal_arms.py --baseline results/calibration/ercot_netrev_margin`) gives:

| year | **keeper** coal TWh | actual | **ratio** | JAS | gas | act gas | C3a% | C3c |
|---|---|---|---|---|---|---|---|---|
| 2023 | 64.02 | 62.29 | **1.028** | 1.171 | 197.76 | 201.46 | −16.8 | 76/181 |
| 2024 | 60.46 | 58.77 | **1.029** | 1.223 | 200.45 | 203.68 | +0.2 | 14/53 |
| 2025 | 62.59 | 63.37 | **0.988** | 1.130 | 198.05 | 200.21 | +0.7 | 1/31 |

The keeper's annual coal ratio is **already 0.99–1.03**. There is no room to "move toward
1.0", so that criterion is unachievable and meaningless on this baseline. The honest test
— and the one the charter's own decision rule and rationale state ("**the bar is 'does not
regress', not 'must improve'**") — is **non-degradation**. P3 below is written that way.

*(This also relocates what ERCOT-112 measured: arm B's coal ratios of 1.161 / 1.213 / 1.207
are the **availability overlay's** damage, and the floor repaired roughly half of it. The
floor's 4/4 PASS was measured against a degraded baseline, not against the keeper.)*

## Arm

Single arm, full span, one invocation, years sequential (rules 12 + 16):

```
python scripts/replay_keeper.py results/calibration/ercot_netrev_margin \
  --set coal_econ_marginal_hr_bound=true \
  --out-dir results/calibration/ercot115_coal_floor_only \
  --years 2023 2024 2025 \
  --note "ERCOT-115: coal_econ_marginal_hr_bound ALONE on the keeper (promotion test)"
```

## Criteria (fixed now)

**P0 — ARMING + BITE.** The solve log must show
`ERCOT coal econ marginal-HR floor (1): COAL_PRB.econ_low 0.400 -> 0.886` in **all three
years**, `run_config.json['scenario_config']['coal_econ_marginal_hr_bound']` must be
`true`, and the resolved `offer_curve_by_group['COAL_PRB']['econ_low']` must read `0.886`.
Plus a **bite** check: annual coal TWh must differ from the keeper's by > 0.5 TWh in at
least one year. Armed-but-byte-identical ⇒ the floor is inert on the keeper config and the
promotion question is **void**.

*Pre-verified no-LP, before solving (so P0 is a confirmation, not a discovery):*
`_offer_curve_for_group` remaps `plant_group == "COAL"` **per plant** through
`_COAL_SUPPLY_TO_CURVE[coal_supply_class(plant_code)]` → `COAL_PRB` / `COAL_LIGNITE`, so
the whole-fleet `"COAL"` grouping does **not** hide the `COAL_PRB` key. `COAL_PRB` carries
**6 of ERCOT's 9 coal plants, 10,473.3 of 13,027.9 MW = 80.4 %** of coal nameplate.
Inertness-by-construction is therefore already refuted; the availability overlay plays no
part in this lookup.

**P1 (PRIMARY) — C1 fuel-mix must HOLD.** `free_class_score` must stay **all 16/16 and
free 12/12**, and `criteria.fuelmix` must stay **PASS**. Any regression ⇒ **do not promote**.

**P2 — scarcity and dispatch not degraded.** `criteria.dispatch_corr` stays **PASS**;
`criteria.sysvol` and `criteria.co2` stay PASS; `grade_summary.fails` does not increase
above the keeper's **3**. On the pinned scorer numerics (same tolerances as ERCOT-112 P2b,
not re-invented): **C3a** (load-weighted price + `ordc_adder` + `rtordpa_overlay`) no worse
than the keeper by more than **2.0 pp** in any year, and **C3c** (settled hours ≥ $200/MWh)
no worse by more than **5 hours** in any year.

**P3 — the coal class specifically does not regress.** Isolated from P1 so a coal
regression cannot hide behind another class flipping the other way. In **every** gated
year, coal must stay inside its own C1 bands — volume within `±min(2.0 % ISO-load, 8 TWh)`
and share within `±3.0 pp` — **and** `|coal_model − coal_actual|` must not increase by
more than **4.0 TWh** in any year. The 4.0 TWh figure is not a new tunable: it is **half
the C1 volume band**, i.e. a move that consumes more than half the gate's own headroom in a
single year is material even while nominally in band. Keeper starting errors: **+1.73 /
+1.69 / −0.78 TWh**.

**P4 — leave-one-year-out (rule 24).** Each year is scored independently on P1–P3.
Promotion requires **all three** years to pass. A 2-of-3 pass is a **FAIL for promotion**:
a measured physical input should be uniformly admissible, and a single-year failure means a
year-specific driver is unexplained. In-sample gain with held-out degradation is
overfitting, not skill.

## Decision rule (fixed now)

* **P0 fails** (floor inert without the availability overlay) → report inert; the promotion
  question is **void**; no keeper change.
* **P1 holds and P2 + P3 + P4 pass** → **RECOMMEND PROMOTION, ERCOT-SCOPED ONLY.** Enable it
  in the ERCOT branch of `pipeline/backcast_config.py` (the
  `ercot_wtx_curtailment_driver=(iso.upper() == "ERCOT")` pattern at backcast_config.py:1536);
  **leave the global `coal_econ_marginal_hr_bound: bool = False` default alone** so
  PJM (0.803/0.809), MISO (0.838/0.838) and NEISO (0.933/0.631 — a large floor) adopt it in
  their own lanes rather than being silently re-pointed.
* **P1 regresses** → **do NOT promote.** The finding then becomes the rule-14 question:
  *what is the fitted `econ_low = 0.400` silently compensating for?* — a discovered bug
  elsewhere, not a licence to keep the fitted value forever.

## Declared in advance: what would NOT count

* A **lower** price MAE is not evidence **for** the mechanism (rule 1 — the objective is
  structural fidelity, not fit) and will not be used to argue for promotion.
* A **higher** price MAE is not, by itself, grounds to **reject** the mechanism. Only the
  pre-committed criteria decide promotion, and rules 1/13/14 forbid reverting a measured
  input because a residual moved. The gate stays in the codebase either way.
* The **summer (Jun–Sep) coal over-run** — the live ~19 pp seasonal-term lane — is
  **reported, not gated**. ERCOT-112 already established the floor barely touches it.
* The ≥$300 scarcity set is **not** read as evidence: ERCOT-111 measured the arms
  byte-identical in 140 of 144 such hours (coal runs at 99.5 % of its measured live envelope
  there, so no offer-level change can move it). C3c stability there is a confirmed
  prediction, not a null result.

## What is already known at write time (so the verdict is auditable)

Known: the keeper's three-year baseline table above; the ERCOT-112 arm B and arm T results
(B: C1 12/16, dispatch_corr FAIL, target_grade 2, fails 5 · T: C1 15/16, dispatch_corr PASS,
target_grade 3, fails 4 · keeper: C1 16/16, dispatch_corr PASS, target_grade 6, fails 3);
the exact single band the floor lifts; the 80.4 % COAL_PRB capacity exposure.

**Not known:** any ERCOT-115 floor-alone result. No year of arm F had been solved when this
document was written and pushed.

---

## Verdict recorded after the fact

**ALL FIVE CRITERIA PASS → PROMOTION RECOMMENDED, ERCOT-SCOPED — and PROMOTED on owner sign-off
2026-07-26.** Keeper `2026-07-23-ercot100-netrev-margin-keeper` →
`2026-07-26-ercot115-coal-marginal-hr`; the gate is ERCOT backcast default-ON with the global
`ScenarioConfig` default left at `False`. Scored 2026-07-26; full write-up in
`FINDING-ercot115-coal-floor-promotion-2026-07-26.md`. Run id
`2026-07-26-ercot115-coal-marginal-hr`.

| criterion | result |
|---|---|
| **P0** arming + bite | **PASS** — 3/3 arming lines with `ercot_thermal_dam_availability_coal=False`; coal −4.68 / −3.14 / −2.30 TWh |
| **P1** C1 holds 16/16 · free 12/12 | **PASS** — identical to the keeper |
| **P2** scarcity/dispatch not degraded | **PASS** — dispatch_corr/sysvol/co2 PASS, fails 3 (not increased), C3a worst drift 1.1 pp (≤2.0), C3c 76→72 / 14→13 / 1→1 (≤5) |
| **P3** coal in band, \|err\| increase ≤ 4.0 TWh | **PASS** — every coal class PASSes every year; Δ +1.22 / −0.24 / +2.30 |
| **P4** LOYO, all three years | **PASS** — 3/3 |

**One P0 sub-clause failed and is reported as a failure, not reinterpreted:** the recorded
`offer_curve_by_group['COAL_PRB']['econ_low']` reads `0.400`, not `0.886`. Root cause was a
`_recorded_config` mirror that recorded the floor's bool but not its curve — a real registry bug,
fixed in this session. It is not evidence the floor was inert: the arming line fired 3/3 and
dispatch moved 4.7 TWh.

Declared-not-counted, honoured: **no price-MAE argument was made for the mechanism.** C3 is
reported on both bases (§4 of the finding) precisely so the promotion's price cost is on the
record — on the pinned load-weighted basis 2024/2025 *degrade* by 1.1 and 0.8 pp, inside tolerance.
The ≥$300 scarcity set was not read as evidence. The summer over-run was reported, not gated —
and the finding records that the shoulder months get **worse** (Feb–Apr 0.59–0.83).
