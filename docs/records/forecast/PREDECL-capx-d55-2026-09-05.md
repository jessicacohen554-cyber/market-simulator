# PRE-DECLARATION — capx D55: the floor-retention key repaired to the class constant (D32 §3.2 / §7 R2), its A/B, and the plant-grain release-precision scorer row (D32 §7 R4)

**Lane:** capx D55 — a small correctness lane. D32
(`docs/handoffs/FINDING-capx-d32-floor-retention-2026-09-02.md` §3.2, §7 R2/R4) found
that `_floor_retention_merit` key 1 is computed per unit as
`(FOM × pmax × 1000) / (pmax × (1 − EFORd))` instead of the class constant
`FOM × 1000 / (1 − EFORd)`, so IEEE-754 rounding puts same-fuel units on different floats
at the 1e-11 level and the CO2 / heat-rate tie-breaks fire only inside rounding buckets
(Marion, 1.533 t/MWh, retained ahead of cleaner coal in MISO 2022). At `a35c9f9b` and at
this branch's base `b1964e7` the defect is still in
`src/market_sim/model/capacity_evolution/retirements.py` (the quotient form).
**Branch:** `claude/capx-d55-retention-key-fix-xqrcfv` (harness-assigned; the dispatch
named `claude/capx-d55-retention-key-fix`), FRESH off `origin/main` `b1964e7`.
**Date:** 2026-09-05. **Pushed BEFORE the repair commit and before any solve.** Graded at
full magnitude in `FINDING-capx-d55-2026-09-05.md`, misses included.

**NOTHING ARMS. NO PARAMETER, NO FIELD, NO ROW.** A code fix that changes no
`ScenarioConfig` field (rule 28: no matrix row; the defect citation goes on the MISO
`economic_retirement_screen` cell note), a heterogeneous-pmax test, and a REPORTED-ONLY
scorer row. The A/B registers SUFFIXED (`miso-t1h-d55-keyfix`); the bare `miso-t1h`
verdict key, every keeper / shard verdict / marker and the backcast namespace are
untouched. Rules 12, 21, 22, 27, 28 hold.

---

## 0. Disclosure — what was computed before this text was written

- **The cache key (item (d)).** `run_capacity_hindcast.build_config("MISO", 2021, 2025,
  "realized", vintage=2020, entry_screen_diagnostics=True)` →
  `apply_iso_scenario_defaults` → `cache_key()` resolves **`eff2c890746ec966`** at the
  working tree that already carries the repair (= D46's key, the bare `miso-t1h`
  recipe); `ScenarioConfig()` stays `4c6b03ae098b6e3e`, the bare backcast
  `8211c72bb1960adc`. D46's committed `scenario_config` block re-hashes to the same
  key at HEAD. The key is a function of the config alone.
- **The zero-solve replay instrument (item (b)).** `scripts/probes/_capxd55_retention_replay.py`
  (committed with this text) rebuilds the run's fleet attributes (fuel / EFORd / CO2 /
  heat rate; `pmax` read from the event row itself) and replays
  `_apply_reliability_floor`'s retention loop on the committed 2022 `pipeline_events`
  with BOTH key forms. It was run ONCE before this text, on a `data/clean` tree that
  had not been regenerated: 224 of 1,663 event ids (5 of the 23 decided tranches)
  matched no rebuilt unit and the defective-key validation FAILED on that tree, so
  that output is DISCARDED, not used, and not committed. The regenerated-tree run is
  graded in the FINDING against §2's predictions. Nothing was solved.
- **The unit test.** Written and run at both trees: it FAILS at the quotient form
  (the dirtiest of three heterogeneous-pmax coal units is retained first, the cleanest
  released) and PASSES at the class constant.

## 1. (a) Cross-fuel: NOTHING moves

Key 1 differs only across fuels at the shipped FOM table (D32 §3.1: coal 45 × 1.3 / 0.92
= 63,587 $/firm-MW-yr; gas_st, gas_cc, gas_ct, oil each on their own constant), so the
cross-fuel order of the retention loop is FIXED by the table whichever form key 1 takes.
Prediction, at full magnitude:

- **P1.** The A/B's `evolution_<year>.json` `retirements` rows are IDENTICAL to D46's in
  every year, per fuel and per unit — total, coal, gas_st, gas_cc, gas_ct, oil, nuclear,
  biomass — and so is every FC-3 band verdict, every LOYO fold and the determination
  (`HOLD`).
- **P2 — the stronger claim, and the reason this A/B is worth 25 minutes.** On the bare
  `miso-t1h` recipe the 2022 and 2023 admission floors EXHAUST the eligible set (D46:
  1,497 / 948 `entry_capped` rows, ZERO `decided` — D49 §2.3's H-FLOOR regime), and 2024
  / 2025 fail nothing. When the loop retains everything, the retention ORDER is
  irrelevant, so the fix is INERT on this recipe: `pipeline_events`, `floor_retained`
  and `retirements` are byte-identical to D46, not merely cross-fuel-identical. The
  only floats that may differ are the `going_forward_cost` entries of a
  `floor_retained` log row (the same product in a different association order, at
  1e-11) — and D46 has no such row in any year.
- **STOP condition.** Any unit crossing fuels, any per-fuel exit total moving, or any
  2022/2023 `decided` row appearing on the bare recipe means a SECOND mechanism reads
  the key (or the fixed key changed the exhausted-set condition, which it cannot):
  route it, do not interpret it.

The A/B is therefore the byte-identity instrument for "no second mechanism reads the
key" — not the instrument that shows the within-coal reorder. That is shown by §2 on the
two committed bundles where the floor actually released something.

## 2. (b) Within coal: the release becomes the highest-CO2 tranches

The within-fuel consequence is visible only where the 2022 floor released a suffix:
**D31** (`miso-2021-2025-realized-t1h-d31`, key `3649264ca98a1fb4`, dates OFF: 23
tranches / 3,684.0 MW decided) and **D51** (`miso-2021-2025-realized-t1h-d51-ratio`,
key `b538d37b36a88247`, dates ON + the re-identified ratio: 5 tranches / 477.4 MW). The
replay (disclosed in §0) is graded on two things: it must REPRODUCE the committed
decision under the defective key (validation), and it then PREDICTS the released set
under the fixed key.

Predictions, at full magnitude, graded in the FINDING from the replay's committed
JSON (`docs/handoffs/d55/replay-<bundle>.json`):

- **P3 — validation.** Under the DEFECTIVE key the replay reproduces the committed
  2022 decision on BOTH bundles: every `entry_capped` unit sorts before every
  `decided` unit (the released set is exactly the sorted suffix), and the D31 coal
  eligible set lands on 4–5 distinct key-1 floats (D32 §3.2's buckets). A failed
  validation withholds the prediction — it means the replay, not the model, is wrong.
- **P4 — D31 (3,684 MW released, 23 tranches).** Under the FIXED key the released
  suffix is the highest-CO2 coal tranches of the 165-unit coal eligible set, ordered
  CO2-descending from the tail: **Marion (976, 1.533 t/MWh) released first, then
  Prairie Creek (1073, 1.230), Culley (1012, 1.186), 6098, 4271 (Madgett), 963, …**
  (D32 §3.2's list) — with the boundary tranche possibly ambiguous, since the loop's
  shortfall is bounded, not persisted. The released CO2 range moves from D31's
  committed [0.990, 1.230] head-to-tail (with 976 / 1012 retained) to a range whose
  MAXIMUM is 1.533 and whose minimum is at or above the committed one; the two
  largest committed releases, White Bluff (6009, 990.8 MW) and Independence (6641,
  633.9 MW, both ~0.99 t/MWh), are NOT in the fixed-key release unless the
  MW-shortfall reaches that deep into the CO2 order. Released MW is within one
  boundary tranche of 3,684 MW; released tranche COUNT may differ (the MW are
  covered by whichever tranches sit at the CO2 tail).
- **P5 — D51 (477.4 MW released: Madgett 4271, Nelson 1393, D B Wilson 6823, plus
  ~5 MW at Prairie Creek 1073 / Muscatine 1167).** Same construction on the D51
  eligible set (85 coal candidates): the fixed-key release is the CO2 tail of THAT
  set — Marion (976) first if it is among the 2022 failing candidates there, else the
  dirtiest candidates present — within one boundary tranche of 477.4 MW.
- **P6 — cross-fuel identity in the replay.** Both releases are 100 % coal under both
  keys; no gas / oil / nuclear tranche enters either release (§1).
- **P7 — D46 (the bare recipe).** The replay reports the 2022 / 2023 floors as
  EXHAUSTED (zero decided) and the fixed key releasing the same empty set — the
  zero-solve twin of §1 P2.

Against the real cohort this is neither better nor worse (D32 §4.3: CO2 rate does not
discriminate real exits; §2.3: plant-grain precision 13.5 % on D31). The prediction
here is about the RULE doing what its docstring says, not about skill.

## 3. (c) Which committed stage-0 goldens go stale: NONE

Every entry of every manifest under `results/regression-goldens/` (45 manifests; the
enforced `perfb-stage0` one holds CAISO, ERCOT, ERCOT__carveout-2023, MISO, NEISO,
NYISO, PJM) is a **backcast keeper capture** (`capture_keeper_goldens.py` resolves
`keepers/<ISO>.json`; the hashed files are `btm` / `flows` / `storage` / `system` /
`dispatch/<yr>_P1[_fleet]` parquets), and a backcast has no capacity evolution
(`runner.py`: "backcast mode has no capacity evolution"), so no golden ever executes
`_apply_reliability_floor`. The fix's only footprint is in forecast / hindcast
evolution ledgers, which are not golden-captured. **Prediction: `check_golden_manifest.py`
reads 0 stale before and after; the stale-golden list handed to the audit programme is
EMPTY.** (The dispatch's reading that "the golden manifest is the instrument that
catches" a key move is therefore corrected below.)

## 4. (d) The cache key does not move — and what actually catches a key-move

A code fix moves no `ScenarioConfig` field, so `cache_key()` is unchanged:
**`eff2c890746ec966`** (§0). The A/B therefore lands at the SAME key as D46 under a
different `--out-dir`, which is exactly what makes P2 a byte-identity assertion between
two directories. The instrument that would catch an unintended key move is NOT the
golden manifest (§3: the goldens never see this code path) but the CI `cache-key-guard`
job plus this pre-declared key against the A/B's `meta.json`.

## 5. What is built (frozen)

1. `_floor_retention_merit` key 1 → `FOM × multiplier × 1000 / thermal_accreditation_fraction(...)`,
   the ISO's accreditation-basis convention from `_thermal_firm_mw` preserved (the same
   resolver), `inf` for a unit with no firm value as before; D32 §3.2 cited at the
   definition. Keys 2–3 unchanged. `_apply_reliability_floor` untouched.
2. `tests/unit/model/test_capacity.py::TestReliabilityFloorAccredited::
   test_retention_merit_within_fuel_co2_order_heterogeneous_pmax` (pmax 1000 / 291.535 /
   613.2 — the values that split the quotient into three floats at UCAP 0.95); the
   existing `test_retention_merit_cost_then_co2` kept verbatim.
3. `score_capacity_hindcast.py`: `retirements.plant_release_precision` — released MW at
   real-exit plants (same plant code + fuel, anywhere in the window) ÷ released MW, per
   window and per ledger year, split `economic` / `all` — REPORTED ONLY (no band, no
   verdict, no consumer). Documented in the scorer docstring and the rubric's FC-3
   report-only list. Sanity anchor: D31 economic window reads **13.5 %** (D32 §2.3's
   497 / 3,684 MW).
4. A/B: the bare `miso-t1h` recipe at the fixed code, `--entry-screen-diagnostics`,
   out-dir `results/hindcast/miso-2021-2025-realized-t1h-d55-keyfix`, registered
   suffixed `miso-t1h-d55-keyfix`. Solo (rule 12).

## 6. Governance

Rule 21: zero DOF (no parameter, no threshold). Rule 22: no out-of-training year. Rule
27: `retirements.py` (2,9xx lines) and the scorer (2,5xx lines) are edited locally and
pushed as on-disk bytes, blob-verified after push. Rule 28: no row; the MISO
`economic_retirement_screen` cell note gains the defect citation in the same PR. No
keeper / shard / marker.
