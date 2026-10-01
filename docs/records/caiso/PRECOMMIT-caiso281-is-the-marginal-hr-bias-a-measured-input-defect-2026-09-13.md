# PRECOMMIT caiso-281 — is the +1.024 marginal-heat-rate bias a MEASURED-INPUT defect, or is it the offer markup?

**Lane:** CAISO calibration · **Date:** 2026-09-13 · **LP budget: ZERO.**
**Predecessor:** `docs/RESULT-caiso280-the-envelope-binds-above-the-actuals-2026-09-13.md`.
**Keeper unchanged:** `2026-09-12-caiso-275-gascoupling` (CALIBRATED 2023–2025, one ledgered C3c).
Rule 32 `[R-SHARD]` (a) is not reached: no solve is chartered. Nothing will be promoted here.

---

## 1. THE QUESTION

caiso-276 §3 measured CAISO 2022's residual as **one object**: an implied-marginal-heat-rate bias
of **+1.024 MMBtu/MWh** (sd 0.642), gas-proportional, reproducing caiso-270's cross-ISO **+1.01**
from a different construction. caiso-279 and caiso-280 then closed the seam route: on the hours
carrying the miss λ is set by an import-envelope dual, and that envelope binds **above** the
actuals (model **+1,773.3 MW** over CAISO's own measured net import). So the residual is
**internal marginal-cost formation**, and the handoff's §4 names the trap: the only channel
*measured* to move it is the owner-blocked flat ×0.92 multiplier, and rule 1 `[R-STRUCT]` (c)
forbids re-running it at a swept value.

This session asks the one question that decides whether an **admissible** route exists:

> **Is the model's gas fleet mis-ordered and/or mis-rated against the SAME units' MEASURED CAMPD
> heat rates — a rule 14 `[R-ACCURATE]` input defect — or does the +1.024 live in
> `Generator.offer_markup_hr`, which IS the owner-blocked channel?**

The two have opposite governance consequences and are distinguishable with **zero LP**.

## 2. THE STRUCTURAL FACT ESTABLISHED FIRST, FROM CODE, BEFORE ANY MEASUREMENT

`scripts/calibration_verdict.py::_cems_gas_hourly_fit` builds `model[h] += …` and `act[h] += …`
by **summing over plants**, and only then calls `_pearson_nrmse`. **C4's gas NRMSE is a
FLEET-TOTAL hourly fit.** Therefore *pure within-fleet reallocation is invisible to C4 by
construction* — a plant swap at constant fleet total cancels exactly.

This is load-bearing on the handoff's own framing. "A common root in **CC dispatch-order
formation**" can reach C4 **only** through the component of the per-plant error that survives
aggregation. The measurement must therefore report that component's size rather than assume it,
and the gates below are written accordingly. Recorded here, before the numbers, so it cannot be
produced afterwards to explain a result.

## 3. THE DECISION RULE — FIXED HERE, PUSHED BEFORE ANY NUMBER IS COMPUTED

### GATE A1 — ORDER. Does the model's within-class heat-rate ORDER match the measured order?

Per CAISO gas plant *p* and year *y* ∈ {2022, 2025}:

* **model HR(p)** = `pmax`-weighted mean of `FleetArrays.heat_rate` over that plant's tranches,
  from `run_year(fleet_only=True)` driven by the keeper bundle's own `meta.json`
  (`scripts/legitimacy_diagnostics.py` §2484 recipe) — the model's **physical** rate, excluding
  `offer_markup_hr`, which Gate B handles separately.
* **measured HR(p)** = `Σ heatInput / Σ grossLoad` over that plant's CAMPD unit-hours in year *y*
  (`data/raw/campd-unit-level/CA_<y>.parquet`), **restricted to high-load hours**
  (`grossLoad ≥ 0.80 × that unit's own p95 grossLoad`, `opTime > 0`). The restriction is fixed
  here and is not optional: unrestricted measured HR is part-load- and start-dominated, a confound
  that biases *toward* finding a defect.
* Plant admitted only with **≥ 500** admissible unit-hours in the year.

**Metric: Spearman ρ between model HR and measured HR across plants**, computed for `CC_REGULAR`
and for all gas, in each year. Spearman is chosen because it is invariant to the gross-vs-net
basis difference (CAMPD `grossLoad` is gross; the model's `heat_rate` is net), which a level
comparison is not.

* **A1-OPEN (order defect exists):** ρ ≤ **0.40** on `CC_REGULAR` in **both** years.
* **A1-KILL:** ρ ≥ **0.70** on `CC_REGULAR` in **both** years — the model's within-class merit
  order matches the market's measured order; there is no order defect to repair.
* Otherwise **INDETERMINATE**. An indeterminate does **not** open the route.

### GATE A2 — LEVEL. Reported, deliberately NOT gated on its own.

Cap-weighted mean **Δ = model HR − measured HR**, by class and year. **Declared bias, before the
number:** CAMPD `grossLoad` > net output, so measured-gross HR **understates** the net HR, which
makes Δ **too positive** — i.e. biased *toward* a defect finding. A2 is therefore reported with
its sign of bias stated and used only to say whether a level defect is *plausible*; the order
gate A1, which the basis difference cannot touch, is what decides.

### GATE B — THE IDENTITY. What carries the +1.024 if the physical HRs are right?

`pmax`-weighted mean `offer_markup_hr` over the tranches caiso-276 §5c measured as carrying the
marginal weight (`CC_REGULAR:committed`/`econc*`, `CT_CHP:econc00`/`econc01`), 2022. **No
threshold** — this is an accounting identity, reported at full magnitude:
`markup + Δ_physical` either accounts for the measured **+1.024** or it does not, and the shortfall
is composition.

### GATE C — THE HANDOFF'S OWN KILL CONDITION, at LP-row grain.

Per-plant mean hourly dispatch error `ē_p = mean_h(model_p(h) − actual_p(h))` MW, decoded from the
**committed** artifacts only: payload `plants[<code>].m` and bench `plants[<code>].campd`
(uint8 CF% of `npl`), `frontend/data/backcast/runs/2026-09-12-caiso-275-gascoupling{,-2022}.js`
and `frontend/data/backcast/bench/CAISO/{2022,2025}.json.gz`.

* **C-KILL:** Pearson |r| < **0.20** **and** Spearman |ρ| < **0.20** between `ē_p(2022)` and
  `ē_p(2025)` over the common plant set → the two years' plant-level errors are different objects
  → **no common root → the handoff §4 direction dies at phase 0**, exactly as it instructs.
* **C-PASS:** |r| ≥ **0.35** → a persistent plant-level object; named as the successor.
* Otherwise INDETERMINATE.

**Also reported, ungated (per §2): the aggregation-survival ratio**
`ρ_agg = Σ_h |Σ_p e_p(h)| / Σ_h Σ_p |e_p(h)|` for 2025, plus the bias/shape split of the aggregate
error `Σ_h E(h)² = mean(E)² + var(E)`. These say how much of the plant-level error C4 can see at
all, and whether C4-2025's 0.298 is a **level** or a **shape** object.

## 4. VERDICT LOGIC — fixed here

| A1 | C | verdict |
|---|---|---|
| OPEN | any | A rule-14 `[R-ACCURATE]` input repair route EXISTS and is admissible where the multiplier is not. Named as the successor; **not solved in this session.** |
| KILL | KILL | **Both limbs of the handoff §4 direction are dead.** The residual is the offer-markup channel, which is owner-blocked. Deliverable = the written case to the owner, per handoff §4's own instruction, **not a solve.** |
| KILL | PASS | No HR-input defect, but a persistent plant-level object exists. Named; not acted on. |

## 5. WHAT THIS SESSION WILL NOT DO

* **No LP.** No shard, no screen, no arm (rules 29/32). Nothing registered on the dashboard.
* **No re-run of ×0.92 at any value** (rule 1 `[R-STRUCT]` (c)). If the verdict lands on the
  markup, the output is prose to the owner, not a multiplier.
* **No widening of the corridor envelope** — closed and inverted by caiso-280.
* **No NYISO file touched** (rule 25 `[R-ISO-SCOPE]`); the parity-gate remedy of handoff §6 is put
  to the owner before anything is removed (rule 31 `[R-RETAIN]`).
* **No mechanism cell moved** unless a mechanism is actually tested; a phase-0 measurement that
  tests no `ScenarioConfig` flag moves no cell (rule 28 duty (b) is keyed to testing a mechanism).

## 6. THE KNOWN CONFOUNDS, DECLARED BEFORE THE NUMBERS

1. **Gross vs net** (A2) — direction stated above; A1 is immune by rank invariance.
2. **Duty-cycle contamination of measured HR** — mitigated by the ≥0.80×p95 high-load restriction,
   fixed in §3, not chosen afterwards.
3. **Tranche→plant aggregation** — a plant's tranches share one physical `heat_rate` in the CAMPD
   binning path only when the binner assigns one; where they differ the `pmax` weighting is the
   declared reduction, fixed here.
4. **CHP hosts** (`CC_CHP`, `CT_CHP`) carry `steamLoad`, so their electrical-basis measured HR is
   overstated. They are **reported separately and excluded from the A1 gate**, which is scored on
   `CC_REGULAR`. Fixed here.
5. **Gate C's b64 quantization** — uint8 CF% of nameplate, ≈0.4 % of `npl` per plant per hour.
   Reported; it attenuates correlations toward zero, i.e. biases Gate C **toward KILL**. Declared.

## 7. THE TWO STANDING OWNER ITEMS THIS SESSION CARRIES FORWARD, UNACTED

1. **The rubric ruling** (handoff §5): C3a on the DA basis — mean |gap| 7.65 % RT → 4.33 % DA, but
   2023 over-corrects to −9.4 %. Not a rescue, and not this session's to decide.
2. **The parity-gate RED** (handoff §6): measured at this session's start as **FOUR** tracked
   bundle dirs, not three — `caiso279_ablate_dswcouple_span` (CAISO) plus `nyiso230_arm_y2022`,
   `nyiso231_arm_y2022` and **`nyiso231_ctl_y2022`** (NYISO, appeared since the handoff was
   written). Put to the owner; not acted on unilaterally.
