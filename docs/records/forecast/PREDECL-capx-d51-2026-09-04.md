# PRE-DECLARATION — capx D51: the MISO internal-supply accounting ratio re-identified on the dates-ON fleet (D49 §2.6), its A/B, and the records rider

**Lane:** capx D51 — the rule-23 `[R-FROZEN-DERIVE]` re-derivation D49 §2.6 routed:
`ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_BY_ISO["MISO"] = 0.8546` was identified (D31 §2)
on a census fleet that still carried the 2021–2023 real exits the fossil-dates channel
(owner ruling Q30 / capx D44, default ON) now removes explicitly at step 1b, so under the
run's own posture the same MW is netted twice. This lane moves ONE term of D31's arithmetic —
the denominators, net of the accredited dated exits — and nothing else.
**Branch:** `claude/capx-d51-miso-ratio-rc83dw` (harness-assigned; the dispatch named
`claude/capx-d51-miso-accounting-ratio`), FRESH off `origin/main` `a35c9f9`.
**Date:** 2026-09-04. **Pushed BEFORE the derive script exists and before any solve.**
Graded at full magnitude in `FINDING-capx-d51-2026-09-04.md`, misses included.

**NOTHING ARMS.** One `ScenarioConfig` field lands DEFAULT-OFF
(`adequacy_accounting_ratio_dated_net`, registered in `_CACHE_KEY_OPTIONAL_FIELDS` at
`False` — the bare `miso-t1h` recipe key stays `eff2c890746ec966`, verified after the field
was added); the re-identified value ships as a NEW registry entry
(`ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_DATED_NET_BY_ISO["MISO"]`) that only the armed
gate resolves; the A/B registers SUFFIXED (`miso-t1h-d51-ratio`); the bare `miso-t1h`
verdict key, every keeper / shard verdict / marker, and the backcast namespace are untouched.
The owner arms or declines on the condition in §5. Rules 12, 13, 14, 21, 22, 23, 24, 25, 27,
28 hold.

---

## 0. Disclosure — what was computed before this text was written

A pre-declaration that hides prior arithmetic is worse than one that declares it. The ratio is
an accounting identity over committed operands, not a fitted quantity, so "pre-registering" it
means pre-registering the A/B's CONSEQUENCES; the identity itself was checked by hand before
this push, as follows, and is disclosed rather than "predicted":

- **D31's own construction reproduced exactly on the committed D27 ledgers** (the
  known-answer check on the method): thermal `fleet_by_fuel_before` at 1 − EFORd
  (constants.EFORD) + the PRIOR solved year's wind × 0.166 / solar × 0.3875 / storage firm +
  the year's hydro `firm_clean_mw` × 0.62 → **143,822.1 (2023) / 143,749.5 (2024)**, D31's
  cited denominators to the decimal; Σ offered / Σ denominators = 0.854643 = the registry.
- **The one term moved, read from the committed D46 ledgers** (`miso-2021-2025-realized-t1h-d46`,
  key `eff2c890746ec966`): D27 − D46 `fleet_by_fuel_before` per fuel is EXACTLY the dated
  channel and nothing else — 2023: coal 4,727.1 / gas_st 138.1 / gas_cc 22.5 / oil 10.9 MW
  (4,898.6 nameplate = the 893.6 MW pre-start backlog + the 2022 bridge's 2,108.6 MW of fossil
  drops + 1,896.3 MW of derates); 2024: coal 7,936.0 / gas_st 693.9 / gas_cc 22.5 / oil 10.9
  (8,663.2 = the above + 2023's 2,162.3 drops + 1,602.4 derates). Nuclear (Palisades) and
  biomass are identical in both, confirming the non-fossil announced channel was already in
  D27's census and is NOT part of the moved term.
- **Accredited dated exits:** 4,508.5 (2023) / 7,977.6 (2024) MW.
- **The re-identified ratio (hand arithmetic; the derive script is what is graded):**
  122,375.6 / 139,313.6 = **0.87842**; 123,395.6 / 135,771.9 = **0.90884**; capacity-weighted
  two-year mean **(122,375.6 + 123,395.6) / (139,313.6 + 135,771.9) = 0.893436**, a 1.04539×
  scale on the D31 value. D49's back-of-envelope prior was ~0.88 / 0.91 — the prior, never a
  target; the derive script's output is the value, and §5's STOP fires on it.
- **The cache keys**, resolved through `run_capacity_hindcast.build_config` →
  `apply_iso_scenario_defaults` → `cache_key()` with the field added locally (name and
  default fixed by this text): bare recipe **`eff2c890746ec966`** (= D46, the known-answer
  check on the path), armed A/B **`b538d37b36a88247`** — no collision with any key under
  `results/`, `frontend/`, `docs/`. `ScenarioConfig()` stays `4c6b03ae098b6e3e`, the bare
  backcast `8211c72bb1960adc`. NEISO leg 7 (rider d) re-resolves to **`5925e67c572a910f`**,
  D45-R PREDECL §4.2's pre-declared value.
- **The ledger positions and the identity that scales them.** The position the screens
  consume is `(internal_raw × ratio + tie) / requirement` with the 3,505.9 MW tie unscaled,
  so under the new ratio `pos₁ = ((pos₀ × req − tie) × r₁/r₀ + tie) / req` exactly, for the
  SAME fleet. On the D46 ledgers: 2023 1.032186 → **1.0777**; 2024 0.976427 → **1.0194**;
  2025 0.948813 → **0.9905** (same fleet). The 2024 ledger position reconstructs EXACTLY from
  `fleet_by_fuel_before(2024)` + the 2023 pools (implied raw internal 135,772.0 = the dated-net
  denominator 135,771.9); the 2023 and 2025 ledger positions do NOT reconstruct from their
  entering fleets on the same construction (2023 implied raw 142,812 vs 139,314 built, +3,498,
  consistent with a position computed before the bridge's step-1 rows landed; 2025 implied
  128,575 vs 136,030 built, −7,455, unexplained). Stated now so the finding has to explain
  them from the A/B's own ledgers rather than read past them.
- **The curve, evaluated through the shipped seam** (`MARKET_DESIGN["MISO"]
  .capacity_price_per_firm_mw_yr` × coal accreditation, $/kW-yr): the PY2023 and PY2024
  vertical vintages pay $94.8 / $113.6 at x ≤ 1.0 and **$0 above 1.0**; the PY2025-26 RBDC
  pays 458 at 0.949, 385 at 0.97, 281 at 0.98, 216 at 0.99, 171 at 1.00, 112 at 1.01, 83.5 at
  the market's 1.0174.

Nothing else was read: no A/B has been solved, no derive script written.

## 1. What is re-identified, and how (frozen)

`scripts/data/derive_miso_adequacy_accounting_ratio.py` reads exactly three committed inputs —
`data/raw/capacity-market/auction-supply/miso/miso.csv` (the Summer offered Generation ZRC rows,
the same numerators as D31), the D27 evolution ledgers (D31's denominators, reproduced, never
retyped) and the D46 evolution ledgers (the dated-ON `fleet_by_fuel_before`) — and emits the
per-year and combined ratios. A reconciliation test asserts the registry constant equals the
derivation (the D31 RBDC precedent), so the value can never drift from the committed data.
**Zero free parameters.** Rule 23: the re-derivation is triggered by a POSTURE change of the
fleet the ratio was identified on (D44's default flip), cited in the derive script and the
registry block; it is never re-run on a residual. What is deliberately NOT moved: the PRA
numerators, the class accreditation bases (1 − EFORd; wind 0.166; solar 0.3875; hydro 0.62),
the prior-year pool convention, the Summer season, the two-year capacity-weighted mean, the
D33 VRE additions (a model outcome — D31's "no model outcome enters" holds, so the D27 pools
stay), and the tie. One term.

**Expected value:** combined **0.8934** (per-year 0.878 / 0.909). **STOP if the derive script's
combined value leaves [0.80, 0.95]** — the lane then registers nothing and routes.

## 2. The A/B (frozen)

| | control | arm |
|---|---|---|
| run id | `miso-2021-2025-realized-t1h-d46` (the live bare `miso-t1h`, VERDICT_MAP) — NOT re-solved | `miso-2021-2025-realized-t1h-d51-ratio` |
| recipe | `run_capacity_hindcast.py --iso MISO --start-year 2021 --end-year 2025 --vintage 2020 --fuel-variant realized --entry-screen-diagnostics` | the same + `--adequacy-accounting-ratio-dated-net` |
| key | `eff2c890746ec966` | **`b538d37b36a88247`** |
| posture | `fossil_announced_exits_enabled=True`, verified, diagnostics on, keeper `2026-09-04-miso-210-clock` (shard) — the arm inherits every one of these; the ONLY resolved-config delta is the gate | |
| registers as | untouched | suffixed **`miso-t1h-d51-ratio`** |

Solo (rule 12: ~10 GB on a 15 GB / no-swap box), years sequential, ~25 min. Scored
`score_capacity_hindcast.py --bundle` + `--flip-gate-extras` (LOYO within 2023–2025) then
`forecast_verdict.py --tier t1h --hindcast-score … --run-config …`, the D48 sequence,
like-for-like against the D46 record. STOP: realized key ≠ `b538d37b36a88247` unexplained; any
collision; anything beyond the suffixed key and the six matrix cells moving.

**Keeper note.** The MISO shard's keeper stamp moved 202 → `2026-09-04-miso-210-clock` on
`origin/main` today (the owner's miso-210 lane). The bare-recipe key is unchanged at HEAD
(`eff2c890746ec966` re-resolved), so the control is the D46 record and the keeper vintage is
NOT an axis of this A/B.

## 3. Predictions (graded at full magnitude in the finding)

**P1 — the ratio.** Combined 0.885–0.900 (central 0.8934); per-year 0.875–0.882 / 0.905–0.912.
Falsifier: outside [0.80, 0.95] (STOP), or the D31 reproduction failing by > 0.1 MW.

**P2 — positions the arm's screens consume** (ledger `capacity_reserve_position`): 2023
**1.070–1.085** (central 1.078); 2024 **1.015–1.024** (central 1.019 — NOT D49's "near 1.03":
the identity holds the D46 fleet fixed, and that fleet is 1.5 pts short of the market's own
1.034 because the model under-builds, the D39 object, not the ratio's); 2025 **0.965–0.995**
(0.990 on the D46 fleet, lower by the accredited MW of any 2022-admitted coal executed in 2024).
Falsifier: 2024 < 1.005 (the cliff not crossed) or > 1.035.

**P3 — the capacity term the screens credit** (coal, $/kW-yr): 2023 **$0** (unchanged,
already long of the PY2023 step); 2024 **$0** (was 113.6 — the cliff crossed, the whole rule-14
sign of the lane); 2025 **$200–390** on the RBDC (was 458.4) — **NOT the $91–110 D49 §2.6
stated**: that figure was evaluated at the market's own 1.0174, a position the model's fleet
does not reach without the additions it lacks. Falsifier: 2024 term > $0, or 2025 term < $150
or ≥ $458.

**P4 — the regime flip.** In the arm's 2024 screen the undated cohort FAILS the bar again on
energy-only margins (D49 §2.3's 2022/23 pattern: ~70–80 GW failing, `pipeline_events`
non-empty where D46's 2024 carries 0 rows) and is `entry_capped` or admitted; D46's "no unit
fails in 2024" reverses. 2025 keeps "no unit fails" (the term stays ≥ $200 against bars of
21–58.5). Falsifier: 2024 `pipeline_events` empty, or any 2025 failure.

**P5 — what the longer position admits (the exit direction), with its mechanism stated.**
The 2022 bridge screen's admission cap tests a counterfactual ≈ the 2024 entering fleet on the
2021 pools against the growth-projected 2024 requirement; at r₀ it was SHORT (D46 admitted
0), at r₁ it is LONG by 1.3–4.2 GW accredited (the range is the projected-vs-realized 2024
requirement, bounded above by D46's own zero admission), so the floor releases its LAST-retained
fuel — coal, in the float-noise order D32 §3.2 measured — **1.5–5.5 GW nameplate (central
3.0), decided 2022, executed 2024**. The 2023 and 2024 screens' counterfactuals (horizons 2025
/ 2026, netting the pending admits and the later dated rows) are predicted SHORT → 0 admitted.
Predicted FC-3: `retire.total_gw` **9.799 → 11.3–15.3 (central 12.8)**, err −43.6 % →
−35…−12 %, band **FAIL** (PASS needs 15.6–19.1; possible only at the very top of the range);
coal 7.877 → 9.4–13.4; gas_st / oil / gas_ct / gas_cc **unchanged to the decimal** (dates
channel only); `false_retire` **0.0 PASS** (per-fuel grain, coal stays below 12.434);
`retire.unit_recall_gt300` **16–17/19** (a gain only if the float-noise order happens to pick
Rush Island / South Oak Creek / Big Cajun 2 — not predicted, reported); plant-grain precision
of the NEWLY admitted MW **5–25 %** (D32's 13.5 %), so the precision of ALL released MW falls
from D46's 98.5 % to **75–90 %**. Falsifier: 2022 admits 0 (the position did not open the cap)
or > 7 GW; any non-coal economic exit; recall < 16/19.

**The rule-14 line, stated before the solve.** `retire.total_gw` reads BETTER in band terms
and the composition of the added exits is the floor's near-random pick — the "forcing variables
are wrong" signature D32 named. The repair does not close the under-build; it returns the
cohort to the floor-capped regime where D32 R2/R3's objects decide the composition. Neither
outcome is a reason to arm or decline; the ratio is an identity either way.

**P6 — additions and the backstop.** The 2024 entry screen prices thermal entry at a $0 term
(was 113.6) → the D46 2024-decided gas_cc 3,000 / gas_ct 1,471.6 MW (COD 2026/27, OUTSIDE the
scored window) shrink or vanish — no scored `add.*` row moves from that. The BLK-10 backstop:
D46 built 2,415 MW gas_ct in 2025 on a 2024 gap of 2,886 MW accredited; at r₁ the 2024 gap
closes, the 2025 gap is 1.1–3.3 GW (P2's range) → backstop **0.9–2.5 GW** (central 1.4),
`add.by_tech.gas_ct` **4.415 → 2.9–4.5** (FAIL either way vs 1.355), `add.shares.gas_ct`
down. Wind / solar / gas_cc / storage scored rows: **unchanged to the decimal** (their screens
saw $0 or the same RBDC plateau) — declared, with the storage row the one uncertainty (the
2025 storage screen prices at 200–390 instead of 458; the 4,000 MW entry is cap-bound and
predicted to hold). Falsifier: any wind/solar/gas_cc row moving.

**P7 — LOYO and verdict.** `retire.unit_recall_gt300` LOYO holds **≥ 2/3** as in D46 (the
recall is the dates channel's, untouched); `false_retire` folds all 0.0. Determination
**HOLD** (FC-3 FAIL on the additions rows regardless), FC-7 CAVEAT (no DOF ledger, the D46
reading), no verdict outside `miso-t1h-d51-ratio` moves.

**P8 — cost.** ~20–30 min wall, ≤ 10.5 GB, all four solve years {2021, 2023, 2024, 2025},
2022 bridged, `SOLVE-YEAR PARITY` held.

## 4. Rider (d) — NEISO leg 7, run EXACTLY as D45-R PREDECL §4.2 declared (owner ruling Q36)

`run_capacity_hindcast.py --iso NEISO --start-year 2021 --end-year 2025 --vintage 2020
--fuel-variant realized --entry-screen-diagnostics --no-fossil-announced-exits` →
`results/hindcast/neiso-2021-2025-realized-t1h-d45r-datesoff`, registered suffixed
**`neiso-t1h-d45r-datesoff`**, key **`5925e67c572a910f`** (= `neiso-t1h-d37-control`'s, by
construction — the director pre-accepted the equality; the record's identity is its run id and
its fresh out-dir). **P16 and P17 are graded AS WRITTEN in D45-R PREDECL §4.2** — no new
prediction is added here; if the realized key differs it is registered anyway, the drift
stated, and P16/P17 still graded. Its answer (whether Q30's default has a NEISO-side
counter-example) is reported as a finding to the owner, never a recommendation. ~7 min, ~3 GB,
solved BEFORE the MISO arm (rule 12: never concurrent with a ~10 GB MISO year).

## 5. Arming recommendation — the pre-stated condition

Recommend ARM (`adequacy_accounting_ratio_dated_net=True` for MISO via
`default_scenario_overrides`, rule 25) iff ALL of: (a) the derive script's combined ratio is
inside [0.85, 0.93] and the D31 reproduction is exact; (b) the arm's 2024 position lands within
±2.5 pts of the market's offered 1.034 (P2's band) — i.e. the double-netting is closed to the
same tolerance D31 closed the original defect; (c) no scored FC-3 row outside the retirement
block and `add.by_tech.gas_ct` / `add.shares.gas_ct` moves; (d) LOYO recall holds ≥ 2/3.
**`retire.total_gw`'s band reading is explicitly NOT a condition in either direction** (rule 14).
Recommend DECLINE if (a) fails; recommend HOLD-and-route if (b) or (c) fails (a second object is
moving the position). Any two of four is not enough.

## 6. What this lane registers and edits (frozen)

- VERDICT_MAP: `miso-2021-2025-realized-t1h-d51-ratio` → `miso-t1h-d51-ratio`;
  `neiso-2021-2025-realized-t1h-d45r-datesoff` → `neiso-t1h-d45r-datesoff`. Both
  insert-only in `ff-verdicts.json`; `program-status.json` gate rows untouched by either
  (suffixed probes move no gate row).
- Committed slim sets on the D45-R / D48 template (meta, `run_config.json`,
  `forecast_verdict.json`, `score.json`, the `evolution_<year>.json` ledgers, the diagnostics
  `.npz`), one `.gitignore` carve-out block per bundle.
- Matrix (rule 28): base row `adequacy_accounting_ratio_dated_net` + a cell in all six shards
  (MISO `fc: "O"` on the measured record, the other five `·` ISO-exclusive by construction);
  the MISO `adequacy_internal_supply_accounting` and `economic_retirement_screen` cells gain
  the D51 evidence; NEISO's `fossil_announced_exits` cell gains the leg-7 measurement.
- Records rider (a)–(c), (e): ff-verdicts notes + board provenance for the two un-diffable
  `-pre-d46` stubs; the board's NEISO `golden` field repointed to GOLDEN-3 with the GOLDEN-2 text
  preserved beneath; D49 §5 item 5 (oil unscreened after 2022) in the MISO retirement cell;
  rubric §5's second attestation limb (Q37) with a version bump and CHANGELOG line.
- No keeper, no shard verdict letter beyond the new row's own cells, no marker, no backcast
  file, no default flip, no parameter value beyond the new registry entry.

## 7. Kills

- K-a: the derive value outside [0.80, 0.95] → STOP, nothing registered, routed.
- K-b: any cache-key collision, or a realized key ≠ its pre-declared value unexplained from the
  resolved config → STOP for that leg.
- K-c: rule 22 — solve years {2021, 2023, 2024, 2025}, 2022 bridged and never scored, scoring
  and LOYO bounded to 2023–2025, the holdout freeze untouched, nothing scored against H1-2026.
- K-d: rules 13/14/21 — no operand of the ratio is a model outcome or a residual; the cleared
  PRA quantities are validation observables and enter nothing.
- K-e: rule 27 — every ≥300-line file pushed (`scenarios.py`, `capacity_market.py`,
  `retirements.py`, `adequacy.py`, `run_capacity_hindcast.py`, `register_forecast_run.py`,
  `ff-verdicts.json`, `program-status.json`, the matrix shards, the rubric, this lane's docs)
  is edited locally and blob-verified against the remote before the next commit.
- K-f: rule 25 — MISO's ratio never transfers; the other five shards receive an ISO-exclusive
  `·` cell, not a value.
- K-g: the preserved baselines (`*-pre-*`, `*-d42-*`, `neiso-t1h-d37-control`, …) are never
  written; on any collision the lane STOPS and routes.
