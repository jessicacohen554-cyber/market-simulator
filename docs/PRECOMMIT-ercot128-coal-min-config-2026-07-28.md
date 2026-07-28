# PRE-COMMIT — ERCOT-128 Phase 2: the coal MINIMUM ONLINE CONFIGURATION floor

**Date** 2026-07-28 · **ISO** ERCOT · **Lane** ercot128-unit-grain ·
**Keeper under test** `2026-07-26-ercot115-coal-marginal-hr` (bundle
`results/calibration/ercot115_coal_floor_only`) ·
**Arm bundle** `results/calibration/ercot128_unit_grain` ·
**Written and pushed BEFORE any year is solved.** Nothing below may be edited
after the first solve starts; a gate that fails, fails.

---

## 0. Why Phase 2 is being run at all, after Phase 1 recommended against it

`DIAGNOSIS-ercot128` §8 recommended recommend-and-STOP. **The owner reversed
that, on rule 1 `[R-STRUCT]`, and the reversal is correct.** Phase 1's refusal
rested on two arguments, and rule 1 disqualifies both as *reasons to reject a
structurally-correct mechanism*:

* *"G1 ties 19/21 — the prize is nothing."* Rule 1: "never judge a
  structurally-correct mechanism by whether it improves the backcast fit, and
  never reject/revert it because the residual didn't move."
* *"Gate G3 moves the wrong way."* G3 measures **over-flatness**, which §6 of
  the diagnosis itself attributes to a different phenomenon (the ERCOT-126 §1.4
  ceiling pin) that this mechanism does not own and was never going to fix.
  Rejecting a floor because it fails a gate belonging to another mechanism's
  residual is exactly the error rule 1 names.

What Phase 1 *did* establish stands, and is the affirmative case:

1. The model currently drives coal to levels **no combination of the plant's
   units can physically deliver** — keeper per-plant p05 loading 0.013–0.093 of
   declared on J K Spruce / W A Parish / Limestone, against a real fleet whose
   floor is 0.106–0.261. That is a structural falsehood in the LP today.
2. The bound that removes it is **exactly representable in pure LP** — the
   plant's online unit-commitment feasible set is connected for 9 of 10 plants
   and **97.76 %** of ERCOT coal capacity, so the plant-grain interval
   `[min_u MinLoad_u, Cap]` carries zero relaxation error there.
3. The level is a **registration fact with zero free parameters** (EIA-860
   `Minimum Load (MW)`), corroborated exactly by the ERCOT COP on the three
   plants whose resources are whole units.
4. It stacks on nothing (coal forces zero today; rule 19 clean).

**So the question Phase 2 answers is not "does it help the fit" — it is "does
putting real physics in break anything."** The gates below are written to that
standard.

## 1. The single declared delta

`ScenarioConfig.ercot_coal_min_config_floor: bool = False` → `True`, and
**nothing else**. Replay of the keeper's own recorded config:

```
python scripts/replay_keeper.py results/calibration/ercot115_coal_floor_only \
  --set ercot_coal_min_config_floor=true \
  --out-dir results/calibration/ercot128_unit_grain \
  --years 2023 2024 2025
```

One invocation, years sequential (rule 12 `[R-PARALLEL]`), full span in one
bundle (rule 16 `[R-ALLYEARS]`). Holdout years untouched (rule 22).

**Already landed and verified before this document was written** (so the arm is
not being built while the gates are being read):

| piece | where | status |
|---|---|---|
| derive | `scripts/data/derive_eia860_coal_min_config.py` | reproduces the probe exactly: 10 plants, 13,611 MW, cap-weighted min-config frac **0.1590**, 9/10 gap-free (**0.9776** of capacity) |
| artifact | `data/raw/_processed-legacy/coal_min_config_ERCOT.csv` | committed |
| loader | `fleet.coal_min_config` | 10 rows |
| flag | `ScenarioConfig.ercot_coal_min_config_floor` | default **False**; `_CACHE_KEY_OPTIONAL_FIELDS` + `TIER_TAGS` registered |
| cache key | — | default **`603c2498bf71d21d`** (the pinned literal, unmoved); armed **`5f497a0ab6b142be`** (distinct) |
| mechanism id | `MECH_COAL_MIN_CONFIG = 21` + `MECH_NAMES` + `MECH_ABLATION_FIELDS` | done |
| D-4 window | `D4_WINDOWS[(MECH_COAL_MIN_CONFIG, None)] = (0, 24)` | done, all-hours **by driver** |
| tests | `tests/unit/data/test_coal_min_config_floor.py` | **14/14 pass** |
| regression | persisted-identity + flag-registry + coal-sync + cc-mustrun + campd-bins | **105 pass** |

## 2. The gates — fixed now, scored as written

| gate | criterion | keeper baseline | verdict rule |
|---|---|---|---|
| **G0 arming + bite** | 3/3 solve logs carry `coal_min_config floor ARMED`; `run_config.json` carries `ercot_coal_min_config_floor: true`; D-2 shows a non-zero `coal_min_config` row | keeper: no COAL row at all | a silent arm is a FAIL, not a pass |
| **G1 loading-vs-price** | fleet-aggregate, `\|model − actual\| ≤ 0.05`, all 21 bands, computed by `scripts/probes/ercot128_coal_unit_grain.py` §D | **19/21** | **DO-NO-HARM: < 19/21 FAILS.** ≥ 19/21 passes. Ex-ante estimate 19/21 |
| **G2 C1 coal level** | within **2.0 TWh** of actual, every year | −1.07 / −0.21 / −1.89 | any year outside ±2.0 FAILS. Ex-ante estimate +0.66 / +1.09 / −1.13 |
| **G3 D-1 COAL_LIGNITE 2023** | see §3 — **restated**, because Phase 1 proved the original form unreachable by the oracle | 0.745 / 0.294 (live FAIL) | see §3 |
| **G4 rubric + C8** | C1 16/16 · free 12/12; `coal_min_config` forced share under the 30 % merchant cap | coal forced 0.0 % | ex-ante declared **4.8 / 3.4 / 2.8 %**; over 30 % FAILS |
| **G5 LOYO** | leave-one-year-out within 2023–2025 on the G1/G2 verdict | — | **2-of-3 is a FAIL** |
| **G6 DOF ledger** | the new parameter is MEASURED, `lineage_solves = 0` | — | a residual-identified value FAILS (rule 21) |

## 3. G3, restated — and why restating it now is legitimate

**The original G3** (charter): `COAL_LIGNITE` 2023 must CLEAR both D-1 gates
(`profile_r ≥ 0.8`, `cv_ratio ≥ 0.5`). **Phase 1 proved this is unreachable by
ANY member of the min-load-floor family, including the ORACLE** — the floor at
reality's own hour-by-hour commitment scores 0.741 / 0.283, and `cv_ratio` falls
in all twelve class-years, because the defect is over-flatness (off-peak
flat-top pin 73.3 % model vs 6.2 % actual) and a bound constant across
hour-of-day can only flatten further.

A gate no admissible mechanism can pass is not a test of *this* mechanism; it is
a test of the ceiling pin, which ERCOT-116 owns. **Keeping it unchanged would
make Phase 2 unfalsifiable in the wrong direction** — guaranteed to fail for a
reason the arm does not control.

**G3 as scored here — a do-no-harm bound on the same statistic:**

> `COAL_LIGNITE` 2023 `cv_ratio` may not fall **more than 0.030** below the
> keeper's 0.294 (i.e. ≥ **0.264**), and `profile_r` may not fall more than
> 0.030 below the keeper's 0.745 (i.e. ≥ **0.715**). The same bound applies to
> `COAL_PRB` and to 2024/2025, none of which the keeper fails.

**The 0.030 tolerance is declared here, ex ante, and is not fitted:** it is the
ex-ante `min_config` movement Phase 1 already measured (0.294 → 0.274, a fall of
0.020) plus a 0.010 margin for the LP's redistribution, which the lift
construction cannot see. If the solved arm falls further than that, the floor is
doing something the ex-ante bound did not predict and G3 FAILS. **This is a
weakening of the original gate and it is recorded as such**; it is not a claim
that the arm improves diurnal shape, and no promotion argument may cite G3 as
evidence of anything but "did no additional harm".

## 4. What "structural integrity improves but gates regress" means for the verdict

Per the owner's rule-1 direction, the promotion recommendation is scored in this
order, and the order is fixed now:

1. **G0 and G6 are absolute.** A mechanism that does not arm, or that carries a
   residual-identified parameter, is not a candidate at any fit.
2. **G2, G4, G5 are absolute.** Level outside ±2.0 TWh, forced share over cap,
   or a LOYO 2-of-3 means the mechanism is not doing what it claims.
3. **G1 and G3 are DO-NO-HARM bounds, not win conditions.** Passing them is
   necessary; *improving* them is not required and their improvement is not
   evidence for promotion.
4. **The affirmative case is structural and is stated in advance:** the arm
   removes physically-impossible plant loadings from the LP. It will be
   evidenced by the per-plant **p05 loading** moving toward, and never past,
   the real fleet's — reported for every plant-year whatever it shows. A p05
   that overshoots actual would mean the floor is above the real minimum, which
   would be a FAIL of the mechanism's own premise.

**If every absolute gate passes and G1/G3 hold their do-no-harm bounds, this is
a recommended keeper candidate even with a flat or slightly worse fit** — that
is rule 1, and it is the whole reason Phase 2 is being run.

## 5. What would make me recommend AGAINST, stated before seeing a number

* any absolute gate (G0, G2, G4, G5, G6) fails;
* G1 below 19/21 or G3 outside the §3 bounds;
* p05 loading overshoots the real fleet's on a material plant (the floor would
  then be above the true minimum online configuration, i.e. the artifact is
  wrong);
* the D-2 row shows the mechanism binding on non-coal rows, or `MECH_COAL_MUSTRUN`
  and `MECH_COAL_MIN_CONFIG` co-binding the same MWh in a way that indicates
  stacking rather than max-composition (rule 19).

## 6. Scope and standing constraints

`frontend/data/backcast/keepers/ERCOT.json` is **NOT** touched under any
outcome — the promotion recommendation is a recommendation. Holdout years
2022 / 2019 / ≤2021 / H1-2026 are untouched (rule 22); the solve is
`--years 2023 2024 2025` in ONE invocation (rules 12 and 16). No GitHub Actions
workflow is added; the solve runs in-session. `scripts/data/derive_eia860_coal_min_config.py`
is frozen against residuals from creation (rule 23) — it reads one registration
file and takes a minimum, so there is no residual input to it by construction.
Closed lanes stay closed: this is **not** the plant-grain fractional floor
ERCOT-127 §3 refuted (that is a different level on a different grain, and it
appears in the ercot128 probe only as a reproduced control), and ERCOT-116 is
neither armed nor promoted here.
