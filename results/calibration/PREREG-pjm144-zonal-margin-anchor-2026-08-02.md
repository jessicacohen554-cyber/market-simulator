# PREREG — pjm-144: resolve the gas-offer margin anchor PER ZONE at PJM (`--gas-offer-margin-zonal-anchor`)

**Written and pushed BEFORE either arm solves.** Everything below — the
admissibility analysis that shaped the lever, the construction gates, the
REPORTED/KILL split, the declared expected effect STRUCTURE, and the rule-1
scrutiny clause — is fixed in advance.

**Session:** pjm-144. **Scope item:** the cross-ISO transfer nyiso-109 §7
chartered (*"ERCOT, PJM and MISO also arm a zonal gas basis on their keepers,
so the same grain mismatch exists in their lanes; their matrix cells enter as
`U` — each needs its own derived table and its own A/B in its own lane
(rule 25)"*), taken up at PJM under this session's handoff. This is
**off the §5.3 queue and deliberately so**: the queue's price-formation items
are closed/blocked (the flat-stack amplitude defect has an EMPTY lever queue
per pjm-141/142; the Dominion CT routes are measured-closed or data-blocked),
and this lever is not addressed to any of them — it is a **structural-integrity
correction to a mechanism already armed on the keeper**, chartered by the
nyiso-109 measurement. **Keeper under test:** `2026-07-31-pjm-143b-hy-level`
(bundle `results/calibration/pjm143_hy_level_B`, **CALIBRATED**, 9/9 target
grade, C1 16/16 all-class / 12/12 free-class, zero FAILs).
**Frozen HEAD:** `a92ae97` + this session's mechanism-registration commits.

---

## §1 — The no-LP admissibility check, and how it SHAPED the experiment

### 1.1 The grain error, restated at PJM

`apply_gas_offer_margin` adds `markup_hr × (anchor − fuel)` and states its own
identity: *at `fuel == anchor` the reformed offer reduces EXACTLY to the
registered band multiplier.* That is a statement about **a unit's own delivered
fuel**. `GAS_OFFER_MARGIN_ANCHOR_BY_ISO["PJM"] = 3.3483` is derived from
`data.fuel.trajectories._gas_series` — ISO-level, carrying the monthly-actuals
overlay but **not** the per-zone basis. The pjm-143b keeper arms
`pjm_zonal_gas_basis=True` (run_config, recorded), which afterwards shifts
every gas unit's `(n_gen, T)` fuel by its zone's measured basis
(`data/raw/pjm_zonal_gas_hub.csv`: each zone's primary-state EIA
delivered-to-electric-power price minus Henry Hub). So marked-up gas tranches
price their markup at a fuel level they do not pay — the identical defect
class nyiso-109 measured and closed on NYISO.

### 1.2 The convention finding that makes PJM's defect GEOMETRY different

**PJM's applier is NOT NYISO's.** `apply_pjm_zonal_gas_basis` delegates to the
shared `_apply_meanzero_zonal_gas_basis` core
(`src/market_sim/data/fuel/basis/meanzero.py`): the per-zone basis has the
**gas-capacity-weighted fleet mean subtracted** before it is applied, so the
calibrated fleet-aggregate delivered level is preserved and **only the
cross-zonal spread opens**. Consequences, each pre-registered here:

* **The defect is TWO-SIDED.** NYISO's convention holds a reference zone fixed
  and shifts every other zone strictly down, so its ISO anchor was the maximum
  level and the fix was one-sided (offers could only fall). PJM's ISO anchor
  sits at the capacity-weighted **centroid**: premium-basis zones (east —
  SWMAAC, Dominion, EMAAC) pay above it and are today **under-marked** (the
  margin term is negative for them); discount zones (west — West_APS,
  Central_PA, ATSI, AEP_Ohio, ComEd) pay below it and are **over-marked**.
  Arming the zone anchors RAISES eastern marked-up gas offers and LOWERS
  western ones.
* **nyiso-109's K6 direction-integrity gate is DROPPED, not copied.** A
  two-sided mechanism must not be scored on a one-sided gate. The zonal
  direction pattern is REPORTED (§3.2) and can never kill.
* **K3 liveness prices on the ZONAL grain** (§4). The mean-zero re-centring
  preserves the aggregate offer level by construction, so the system-level
  price delta can legitimately be ~0 while the mechanism is fully live. The
  system load-weighted delta is REPORTED with no threshold.
* **The derivation must carry the solve's own fleet weights.** The mean
  removed is capacity-weighted over the fleet's gas rows
  (`weights = fleet.pmax[gas_rows]`), so a synthetic one-row-per-zone fleet
  with unit pmax would measure an UNWEIGHTED re-centring — not the runtime
  transform. `derive_gas_offer_margin_anchor.py --by-zone` therefore gains a
  `--weights-bundle` path for capacity-weighted ISOs: the keeper bundle's own
  per-year fleet is rebuilt no-LP via
  `scripts.lib.bundle_fleet.reconstruct_bundle_fleet` (the sanctioned
  reconstruction every PJM no-LP pre-check uses) and the RUNTIME applier is
  called on that real fleet. The derive also cross-checks that the weights
  bundle arms the registered delivered-series recipe (`GAS_SERIES_FLAGS`),
  hard-failing on drift.

### 1.3 The derived table (the admissibility numbers)

`PYTHONPATH=.:src .venv/bin/python scripts/data/derive_gas_offer_margin_anchor.py
--iso PJM --by-zone --weights-bundle results/calibration/pjm143_hy_level_B`
applies the runtime transform to the same delivered series over the same
2023–2025 window, so the values are by construction the levels the solve
prices those zones' gas units at. Raw measured basis (2023–25 means vs HH,
`pjm_zonal_gas_hub.csv`): SWMAAC +1.185, Dominion +0.632, EMAAC +0.242,
ComEd +0.010, AEP_Ohio/ATSI −0.127, Central_PA −0.277, West_APS −0.298 — a
1.483 $/MMBtu cross-zonal spread.

| zone | 2023 | 2024 | 2025 | **anchor** | vs ISO 3.3483 |
|---|---|---|---|---|---|
| PJM_SWMAAC | 3.7841 | 3.6357 | 5.8786 | **4.4328** | +1.0845 |
| PJM_Dominion | 4.1211 | 3.3207 | 4.1976 | **3.8798** | +0.5315 |
| PJM_EMAAC | 3.0401 | 2.8117 | 4.6176 | **3.4898** | +0.1415 |
| PJM_ComEd | 3.2521 | 2.8067 | 3.7136 | **3.2575** | −0.0909 |
| PJM_AEP_Ohio | 3.1141 | 2.7427 | 3.5036 | **3.1201** | −0.2282 |
| PJM_ATSI | 3.1141 | 2.7427 | 3.5036 | **3.1201** | −0.2282 |
| PJM_Central_PA | 2.9281 | 2.5497 | 3.4346 | **2.9708** | −0.3775 |
| PJM_West_APS | 2.7871 | 2.5917 | 3.4696 | **2.9495** | −0.3989 |

Three zones sit above the ISO anchor and five below — the two-sided geometry
§1.2 predicted from the applier's construction. The per-year
capacity-weighted means the applier removes are −0.105 / +0.169 / +0.239
$/MMBtu (2023/2024/2025) — materially different from zero AND year-varying,
which is why the derivation carries the keeper's own fleet weights rather
than a synthetic unweighted mean. Consistency stat (the mean-zero
invariant): the gas-capacity-weighted mean of the zone anchors is **{CAPW}**
against the ISO anchor 3.3483 (window-mean weights; the invariant is exact
per-year, so the residual is year-to-year weight drift only — recorded in
`results/calibration/_pjm144_zonal_anchor_derivation.json`) — the aggregate
identification point is preserved and only the cross-section moves, exactly
as the applier's construction requires.

**Inertness bar (pre-declared in the handoff): if every zone anchor were
within ~0.1 $/MMBtu of 3.3483 the arm would be recorded `I` ex-ante with no
solve spent.** Result: max |anchor − 3.3483| = **1.0845** $/MMBtu (SWMAAC),
with 7 of 8 zones beyond the bar — the arm is **LIVE** and the A/B proceeds.

### 1.4 What the ISO-level identification misprices today

At the registered curve, `markup_hr × (anchor − fuel)` with the ISO anchor
hands every eastern marked-up tranche a NEGATIVE margin shift (fuel above
anchor) and every western one a POSITIVE shift, on top of band multipliers
that were calibrated as the conduct level. The zone anchor restores the
mechanism's identity — offer == the registered multiplier at the zone's own
delivered level — in all eight zones. Nothing else about the mechanism moves:
same markups, same bands, same ISO anchor recorded in both arms.

---

## §2 — The lever: the mechanism's own identification point, at the right grain

`--set gas_offer_margin_zonal_anchor=true` on the keeper recipe. The solve
resolves `constants.GAS_OFFER_MARGIN_ANCHOR_BY_ZONE["PJM"]` into
`gas_offer_margin_anchor_by_zone` so the bundle's run_config records the
values (rule 21); an ISO without a table hard-fails (rule 24); the table is
PJM's own, derived from PJM's own basis data and PJM's own keeper fleet, and
never transfers (rule 25). A band-scoped rebasis anchor (`margin_anchor_*`)
keeps precedence (rule 19) — the pjm-143b curve carries none, so all marked-up
gas tranches resolve their zone anchor.

**Zero fitted parameters** (+1 DOF entry, +0 residual-identified; 18 → 19
entries, `n_residual` 6 → 6). Rule 23: the table re-derives only when the gas
source data, the per-zone hub table, or the keeper fleet recipe the weights
are read from changes — never because a residual moved. The anchors are what
the derive script printed; they are not swept, in any direction, whatever the
gates do (§5 P5).

---

## §3 — Declarations fixed IN ADVANCE

### 3.1 The expected effect STRUCTURE, and the rule-1 posture

**PJM is CALIBRATED with zero FAILs, so this is a pure structural-integrity
test: there is NO residual this lever is wanted to close.** That is the
cleanest possible rule-1 setting, and it cuts both ways, pre-registered:

* An improvement on any criterion is **not** evidence the lever is right.
* A regression on any criterion is **not** by itself grounds to reject a
  structurally correct identification — the owner's standing instruction
  applies (*if structural integrity improves but gates regress it may still be
  a keeper, put to the owner with the numbers in hand*), via the §5 escalation
  path, never silently.

**Declared expected structure** (not a gate; deviations are findings to
report): zonal λ moves two-sided — premium-anchor zones up, discount-anchor
zones down as the first-order offer arithmetic, with congestion/re-dispatch
free to reshuffle locally; the SYSTEM load-weighted λ delta is
sign-unconstrained and expected materially smaller than nyiso-109's
(−0.60 … −0.87 $/MWh), because the mean-zero construction cancels the level
term by design. **No magnitude band is declared** — there is no measured basis
for one, and pjm-143's refuted band is the precedent for not inventing one.

### 3.2 What is NOT claimed, declared before the solve

* **No amplitude claim, and this arm is NOT a pjm-141 lever.** The pjm-141
  defect is hour-varying offer conduct; this arm's spread is per-zone and
  per-year, constant across the hours of a day, so within-day offer σ remains
  $0.000000 by construction. The flat-stack amplitude boundary stands exactly
  as diagnosed. Any amplitude movement (via congestion re-dispatch) is
  REPORTED, never banked.
* **No C3c claim.** C3c is the keeper's thinnest margin (model tail counts
  3/10/32 vs actual 6/18/59 at a 0.5× floor: margins 0 h / ~1 h / ~2.5 h) and
  a cross-zonal offer redistribution CAN move tail counts in either direction.
  Movement is REPORTED; a C3c FAIL is a §5 kill (P2) and escalates.
* **No Dominion CT-leg claim** (§5.3 items 1–3 untouched), no claim on any
  keeper-note root cause, no forecast-lane result.
* **No re-litigation of pjm-143's hydro repair** or any other armed mechanism;
  both arms carry the keeper recipe exactly, ± the single delta.

### 3.3 Holdout

Both arms solve **[2023, 2024, 2025]** and nothing else (rules 16 / 22). The
holdout spend freeze is ACTIVE; PJM holds `complete` (validation tier), 2022
is deliberately not spent, and no out-of-training year is touched by any
solve, score or probe in this session.

---

## §4 — Construction gates (these, and ONLY these, can invalidate the experiment)

* **K1 flag fidelity.** Arm B's run_config records
  `gas_offer_margin_zonal_anchor == true` **and**
  `gas_offer_margin_anchor_by_zone` equal to
  `constants.GAS_OFFER_MARGIN_ANCHOR_BY_ZONE["PJM"]` (all 8 zones); the
  control records `false`/absent and `null`. Both record
  `gas_offer_net_revenue_margin == true` and
  `gas_offer_margin_anchor == 3.3483`.
* **K2 control integrity — TWO BASES, only the first is a gate.** The
  **scorecard** basis (the control reproduces the committed keeper's
  determination and every per-criterion status) is the pre-registered gate.
  The stricter **byte** basis (class-hour for class-hour, < 1e-6 MW) is
  computed and **REPORTED**; a byte miss is same-HEAD drift and is its own
  finding, not a failed gate. Drift is possible: HEAD has moved from the
  keeper's `a1a3a60` to `a92ae97` (27 src files: ercot-149's ERCOT-gated gas
  event cap, miso-113's MISO-gated coal night floor, caiso-152/153, neiso-74,
  nyiso-109's own default-off mechanism, FFR-1D config hygiene, plus
  runner/pipeline/capacity-evolution refactors). Every one is ISO-gated,
  default-off, or intended behavior-preserving for a PJM backcast — **that
  expectation is recorded so the control can falsify it.**
* **K3 mechanism is LIVE — zonal price leg** (§1.2). `max |Δ class MW|` on a
  class-hour **> 50 MW** in **every** year, AND
  `max over internal zones |Δ zonal mean λ|` **> $0.10/MWh** in **every**
  year. The system load-weighted λ delta is REPORTED with no threshold.
  Failing K3 is verdict `I` (inert), not `R`.
* **K4 single delta.** The two arms' run_config scenario blocks differ in
  **exactly** the two zonal-anchor keys and nothing else.
* **K5 year span.** Both bundles `[2023, 2024, 2025]`.
* *(No K6 — dropped per §1.2; direction is two-sided and REPORTED.)*

A construction-gate failure invalidates the experiment (fix and re-solve);
it never adjudicates the mechanism.

---

## §5 — What can KILL the arm (pre-registered non-degradation gates)

Scored from `scripts/calibration_verdict.py`'s metrics.json on the arm vs the
**control**, never against the committed keeper, by
`scripts/probes/_pjm144_zonal_anchor_ab.py` (no criterion re-derived).

* **P1 — C1 must not regress.** The control's expectation is 16/16 all-class,
  12/12 free-class; the arm must hold **12/12 free** and **16/16 all**.
* **P2 — no NEW FAIL.** The arm's FAIL set must be a **subset** of the
  control's — expected **empty**, so ANY new FAIL kills. The named fragile
  cells: C3c (price_tail — margins 0 h / ~1 h / ~2.5 h, §3.2) and C3a 2025
  (price_mean at −9.04 % of ±10 %).
* **P3 — protective gates hold.** C6/C7/C8 (`governance`/`shape`/
  `forced_share`) each stay PASS. C8's watched cell is CT_PEAKER
  (15.2/15.4/15.8 % grounded share at pjm-143).
* **P4 — slack and dump stay exactly 0.0** in every year of both arms.
* **P5 — no fitted follow-up.** Whatever the gates do, no parameter moves in
  this session to "finish" the result, and the anchor table is **not**
  re-derived against it (rule 23). The anchors are what the derive script
  printed.

**Promotion rule, pre-committed:**

* Every §4 gate passes AND no §5 kill fires → the arm is **promoted to
  keeper**: it is the structurally-correct identification grain of a
  mechanism the keeper already arms, at zero fitted parameters, and PJM stays
  CALIBRATED (rule 1: the most structurally faithful run is the keeper).
* K3 fails → the arm is **`I` (inert)** on the matrix; registered; keeper
  unchanged.
* Any §5 kill fires (with §4 clean) → the arm is **registered, not promoted
  in-session**; the matrix cell records **`O`** with the evidence, and the
  decision is **put to the owner with the numbers in hand** (rule 1 both
  directions; the owner's standing instruction quoted in §3.1). It is not
  recorded `R` — a fit regression under a correct identification is an
  escalation, not a refutation.

Both arms are registered on the dashboard whatever the verdict (rule 15).

---

## §6 — Solves

Two, three years each, one invocation apiece (rule 16), years sequential
inside an invocation. **Arms run SEQUENTIALLY, not concurrently**: the keeper
note (14) records this recipe peaking at **15.55 GB RSS on a 15 GB box** with
`ramp_limits=True`, so rule 12's two-concurrent ceiling is unreachable here —
swap is re-asserted before each arm (`swapon /swapfile`).

```
PYTHONPATH=.:src .venv/bin/python scripts/replay_keeper.py \
  results/calibration/pjm143_hy_level_B \
  --out-dir results/calibration/pjm144_control_A \
  --note "pjm-144 same-HEAD zero-delta control"

PYTHONPATH=.:src .venv/bin/python scripts/replay_keeper.py \
  results/calibration/pjm143_hy_level_B \
  --out-dir results/calibration/pjm144_zonalanchor_B \
  --set gas_offer_margin_zonal_anchor=true \
  --note "pjm-144 single delta: gas_offer_margin_zonal_anchor=true on the pjm-143b keeper"
```

Post-solve, per arm: `legitimacy_diagnostics.py` (else C7/C8 score SKIPPED),
dashboard registration, `calibration_verdict.py --write-metrics`, then the
A/B scorer and an attestation generated from the committed JSON (the
`gen_nyiso109_attestation.py` pattern — nothing hand-transcribed).
