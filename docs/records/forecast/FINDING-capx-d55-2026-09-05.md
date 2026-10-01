# FINDING — capx D55: the floor-retention key repaired to the class constant — inert on the bare `miso-t1h` recipe (byte-identical A/B, as pre-declared), a real within-coal reorder wherever the 2022 floor releases (replay-graded), no stale golden, and the plant-grain release-precision row now reported

**Lane:** capx D55 — a small correctness lane (D32 §3.2 / §7 R2 and R4). Pre-declaration
`PREDECL-capx-d55-2026-09-05.md` (pushed at `8462e7a`, before the repair and before any
solve). **Branch:** `claude/capx-d55-retention-key-fix-xqrcfv`, rebased on `origin/main`
`09f99f0`.
**Scope honoured:** one code fix (no parameter, no field, no row), one unit test, one
REPORTED-ONLY scorer row, one suffixed A/B, one zero-solve replay probe. No keeper, shard,
marker or verdict key touched; the bare `miso-t1h` record keeps its verdict.
**Rules:** 12 (MISO solo), 21 (zero DOF), 22, 27 (every ≥300-line file edited locally and
blob-verified after each push), 28 (no row; the MISO `economic_retirement_screen` cell note
carries the defect citation).

---

## 0. Verdict (one paragraph)

**The defect is real, the repair is exact, and — on the recipe every MISO T1-H leg since D46
runs — it changes nothing, because the 2022 / 2023 admission floors retain every failing unit
and an order over a fully-retained set is unobservable.** The A/B `miso-t1h-d55-keyfix` at the
fixed code reproduces D46 (`eff2c890746ec966`, the same key) byte-for-byte across every
evolution ledger, every FC-3 band and the determination — the pre-declared P1/P2, and the
byte-identity assertion that no second mechanism reads the key. Where the floor DID release a
suffix (D31 dates-OFF: 3,684 MW; D51 ratio-ON: 477 MW), the committed decision is reproduced
by the defective-key replay to within one boundary-adjacent swap per bundle, and the fixed key
turns the release into the CO2 tail of the coal candidate set: on D31 the 990.8 + 633.9 MW
White Bluff / Independence releases (≈0.99 t/MWh, both still operating) give way to Schahfer
(6085, 1,625 MW, 1.106 t/MWh — a real exit), A B Brown, Madgett, Culley, Newton and Big Stone,
with Marion (976, 1.533 t/MWh, D32's headline) released FIRST but contributing only 2.4 MW —
its failing tranche is that small. Plant-grain release precision on D31 reads **13.5 %**
committed (the D32 anchor, now a scorer row) and would read **60–63 %** under the fixed key —
a two-bundle observation dominated by one plant, reported and NOT claimed as skill (D32 §4.3:
CO2 does not discriminate real exits; on D51 the same construction reads 0.2–32 %). **No
stage-0 golden goes stale** (every golden is a backcast keeper capture; a backcast has no
capacity evolution). Nothing arms.

## 1. What was fixed (R2)

`_floor_retention_merit` key 1 (`retirements.py`) is now
`FOM_f × multiplier_f × 1000 / thermal_accreditation_fraction(fuel, EFORd, iso, config, year)` —
the same resolver `_thermal_firm_mw` prices the unit's firm MW through, so the ISO's
accreditation-basis convention (UCAP / seasonal rating / claimed capability / ELCC class
rating) is preserved — instead of `(FOM × pmax × 1000) / (pmax × fraction)`. `inf` is kept for
a unit with no firm value (`pmax ≤ 0` or a zero fraction), so the degenerate-unit ordering is
unchanged. Keys 2–3 (CO2 rate, heat rate) and `_apply_reliability_floor` are untouched; the
retention-log `going_forward_cost` is the same product (`cost_per_firm_mw × firm_mw`).

Why the quotient was wrong in IEEE-754 and not in arithmetic: at UCAP 0.95,
`45 × 1.3 × 1000 × p / (p × 0.95)` over `p ∈ {1000, 291.535, 613.2}` yields
`61578.94736842105 / …046 / …07`, three floats; Python's tuple sort orders on key 1 first, so
the CO2 / heat-rate keys were consulted only inside a rounding bucket. On D31's 165-unit 2022
coal candidate set the defective key lands on **5** distinct floats (D32 §3.2 said 4–5).

**Test.** `TestReliabilityFloorAccredited::test_retention_merit_within_fuel_co2_order_heterogeneous_pmax`
— three coal units of pmax 1000 / 291.535 / 613.2 and CO2 0.95 / 1.50 / 0.60, requirement
sized so two are retained. At the quotient form the DIRTIEST (291.535 MW, 1.50) sorted first
and the CLEANEST (613.2 MW, 0.60) last, so the test FAILS there (verified by stashing the fix:
`1 failed`); at the class constant key 1 is bit-identical across the three, C then A are
retained and B released (`301 passed` for the whole file). The pre-existing
`test_retention_merit_cost_then_co2` (equal pmax 1000, where the quotient is bit-identical and
the defect invisible) is kept verbatim.

## 2. The zero-solve replay — what the fixed key does where the floor released something

`scripts/probes/_capxd55_retention_replay.py` rebuilds the run's base-fleet attributes through
the runner's own seam (`set_eia860_vintage(2020)` → `get_iso_config` → interchange topology →
`load_or_synthesize_bins` → `build_base_fleet`; `pmax` read from the event row), and replays
`_apply_reliability_floor`'s loop on the committed 2022 `pipeline_events` under BOTH keys. The
first run of this probe (disclosed in the PREDECL §0) had NOT set the vintage — the rebuilt
fleet was the canonical 2025ER census, 224 event ids matched nothing — and was discarded; with
the seam mirrored, 11 / 8 / 8 ids stay unmatched (2022's planned thermal additions, none
decided).

### 2.1 P3 — validation: reproduced to within one boundary-adjacent swap per bundle

| bundle | eligible (2022) | capped / decided | defective-key order vs committed decision |
|---|--:|--:|---|
| D31 `3649264ca98a1fb4` | 1,652 | 1,629 / 23 (3,684.0 MW) | **one swap at the boundary**: Gibson `p6113_econ` (1,365.6 MW, base CO2 0.9974) retained by the run but sorting into the tail; Milton R Young `p2823_peak` (13.7 MW, 0.9904) released by the run but sorting into the head |
| D51 `b538d37b36a88247` | 1,489 | 1,484 / 5 (477.4 MW) | **one swap at the boundary**: Independence `p6641_econ` (633.9 MW, 1.0775) retained; Prairie Creek `p1073_peak` (0.6 MW, 1.0716) released |
| D46 `eff2c890746ec966` | 1,489 | 1,489 / 0 | exhausted — every failing unit retained, order unobservable (P7 ✔) |

Every other unit of both bundles sorts on the committed side of the boundary: the cross-fuel
spans of the defective order are gas_ct → oil → gas_cc → gas_st → coal (the FOM table alone,
D32 §3.1), all 23 / 5 released units are coal (P6 ✔), and the released tail of D31 runs CO2
0.9904 → 1.1672 with Marion (1.533), Culley (1.186), Big Stone (1.177) and Madgett's econ
tranche (1.167) retained ahead of it — D32 §3.2's finding, reproduced from the ledgers. The
one swap per bundle is the **crossing unit**: the loop retains in order and `break`s the
moment the requirement clears, so the run's order had the large unit (Gibson / Independence)
ONE place before the small one. The base-fleet CO2 rate this replay reads is the 2021 value;
the screen-year rate the run held is not persisted in the ledger (`campd_bins.py` stamps the
tranche rate; D32 §3.2's own reconstruction lists Gibson at 0.997 in the retained head, the
same anomaly). The probe therefore reports the contradiction and PINS both units to their
committed status for the prediction; it withholds the prediction only past
`max(2, decided // 4)` contradictions. **P3 read strictly is a MISS by one unit per bundle;
read as the pre-declaration intended (the replay is exact against the run's own record except
where the record does not carry the attribute) it validates.** Stated at full magnitude.

### 2.2 P4 — D31: the fixed-key release (committed `docs/handoffs/d55/replay-d31.json`)

The shortfall the floor covered is bounded by the committed decision at
[75,525, 76,599] ratio-scaled firm MW (the last-retained Gibson tranche is 1,365.6 MW wide, so
the interval is wide and the boundary set is 36 tranches at CO2 1.080–1.101). Under the fixed
key, ordered CO2-ascending within coal, the released suffix is:

| | committed (defective key) | fixed key — certain | fixed key — boundary-ambiguous (in, depending on the shortfall) |
|---|---|---|---|
| MW | 3,684.0 (23 tranches) | **3,357.4 (21)** | + up to 1,250.7 (36 tranches) → ≤ 4,608.1 |
| plants | White Bluff 990.8, Independence 633.9, AES Petersburg 362.4, Columbia 342.7, Michigan City 288.5, Merom 235.9, Edgewater 199.2, D B Wilson 178.9, Nelson 170.3, Madgett 123.2, Erickson 74.2, Big Cajun 2 22.2, Prairie Creek 14.3, Milton R Young 13.7, Brame 9.9, + 5 slivers | **Schahfer 6085 1,625.0; A B Brown 6137 490.0; Madgett 4271 389.8; Culley 1012 360.0; Nelson 1393 180.8; Newton 6017 151.1; Big Stone 6098 144.6; Milton R Young 2823 13.7 (pinned); Marion 976 2.4** | Warrick 6705 342.7, D B Wilson 6823 417.0, Coyote 8222 156.6, St Clair 1743 74.6, Trenton Channel 1745 34.7, and 31 small 1.08-t/MWh tranches (Erickson, Genoa, Lansing, …) |
| CO2 range | 0.9904 → 1.1672 (with 1.533 / 1.186 / 1.177 retained) | **0.9904 (pinned) → 1.5331**; ex-pinned 1.106 → 1.533 | 1.080 → 1.101 |

**P4 graded.** Marion (976) IS released first under the fixed key — and contributes **2.4 MW**:
its only failing tranche is the 2.4 MW peak sliver (D32 named the plant, not the MW). Culley
(1012), Big Stone (6098) and Madgett (4271) are in the certain release as predicted; Prairie
Creek (1073) is NOT in D31's fixed release (its tranches sit at 1.0716, inside the retained
head once the tail is ordered properly) and **Dallman (963) is not in the 2022 candidate set
at all** (it never failed the screen; D32's list drew it from a different join) — two named
plants MISSED. White Bluff and Independence leave the release as predicted. Released MW is
3,357–4,608 vs the predicted "within one boundary tranche of 3,684" — the boundary is wider
than pre-declared because the crossing unit is Gibson's 1,366 MW econ tranche. Count moves
23 → 21 (+ up to 36). Cross-fuel: 100 % coal both keys (P6 ✔).

### 2.3 P5 — D51 (`replay-d51-ratio.json`)

Committed release 477.4 MW: D B Wilson 178.9, Nelson 170.3, Madgett 123.2, Muscatine 4.5,
Prairie Creek 0.6 (D51 §3.2). Fixed key, shortfall bounds [62,933, 63,454]: **certain
release 278.6 MW — Big Stone 144.6, Madgett 131.0 (committed + peak tranches), Marion 2.4,
Prairie Creek 0.6 (pinned)**; boundary-ambiguous 782 MW — Warrick 342.7, Nelson 180.8,
Madgett's 258.8 MW econ tranche. Marion is first as predicted (P5 ✔); D B Wilson leaves the
release. Muscatine (1167) is not in the fixed release.

### 2.4 What this is and is not evidence of

Graded with the new scorer row on the SAME actuals (`plant_release_precision`, economic
channel, window real-exit set of 127 (plant, fuel) pairs):

| release | MW | at real-exit plants | precision |
|---|--:|--:|--:|
| D31 committed | 3,684.0 | 497.2 | **13.5 %** (D32 §2.3's number, now the scorer's) |
| D31 fixed key, certain | 3,357.4 | 2,115.0 | 63.0 % |
| D31 fixed key, incl. ambiguous | 4,608.1 | 2,759.7 | 59.9 % |
| D51 committed | 477.4 | 5.1 | 1.1 % |
| D51 fixed key, certain | 278.6 | 0.6 | 0.2 % |
| D51 fixed key, incl. ambiguous | 1,060.9 | 343.3 | 32.4 % |

The D31 jump is ONE plant: Schahfer's three tranches (1,625 MW; units 14/15/17/18 really
retired 2021–2023) sit at 1.106 t/MWh, inside the tail. D51 moves the other way. This is
consistent with D32 §4.3 (CO2 rate has no plant-grain discriminating power against the real
cohort — AUC ≈ chance) and is reported as what a corrected rule does on two bundles, not as
skill. It does not change D32's routing (R1 owner posture, R3 sector gate).

## 3. The A/B — `miso-t1h-d55-keyfix` vs the bare `miso-t1h` (D46), both `eff2c890746ec966`

Solved solo (rule 12) at the fixed code on the bare recipe (`--iso MISO --start-year 2021
--end-year 2025 --vintage 2020 --fuel-variant realized --entry-screen-diagnostics`), 2021 /
2023 / 2024 / 2025 solved, 2022 bridged, 12.5 min wall (P0+P1 per year 342 / 146 / 152 / ~150 s),
`SOLVE-YEAR PARITY` and the leakage guard clean, the holdout freeze asserted by the banner.
**Cache key `eff2c890746ec966` — the pre-declared value, the same key as D46** (item (d) ✔),
so the comparison is directory-vs-directory at one key.

**P2 — byte-identity.** For every ledger year 2021–2025 the `retirements` and
`pipeline_events` blocks are byte-identical to D46's (canonical-JSON equality), and
`floor_retained` is empty in both: 2022 caps 1,489 / 2023 caps 948 failing units with ZERO
`decided` rows in both arms — the exhausted floor, exactly as pre-declared. The ONLY ledger
difference is four diagnostic keys D46's ledgers do not carry (`screen_peak_demand_mw`,
`screen_adequacy_requirement_mw`, `screen_entering_firm_mw`, `screen_reserve_position`) —
written by `runner.py` since capx D52 (`2f12544`, 2026-09-04, after D46 was solved), a
ledger-schema addition unrelated to this fix. No `going_forward_cost` float exists to differ.

**P1 — cross-fuel identity.** All 21 FC-3 rows compared (retire total / recall / false-retire
/ per-fuel model GW for every fuel / additions by tech / tech-mix shares / 2025 CO2): **zero
differences**, level or band; `retire.total_gw` 9.799 FAIL (−43.6 %), recall 16/19 PASS,
false-retire 0.0 PASS, LOYO 3/3, determination **HOLD → HOLD**, reasons and caveats
identical. Registered suffixed **`miso-t1h-d55-keyfix`** (verdict key via `VERDICT_MAP`;
`ff-verdicts.json` insert-only); the bare `miso-t1h` (D46) record is untouched. STOP
condition not triggered: no second mechanism reads the key.

`plant_release_precision` on the A/B: economic `None` (0 MW released), all channels 98.5 % —
the same as D46 (§4).

## 4. The scorer row (R4)

`score_capacity_hindcast.py` now emits `retirements.plant_release_precision` — `{grain,
n_real_exit_plants, window: {economic, all}, per_year: {<y>: {economic, all}}}`, each block
`{released_mw, released_mw_at_real_exit_plants, released_mw_no_plant_identity, precision}` —
REPORTED ONLY: no band, no verdict, sits beside `unit_recall_gt300` (whose schema is
unchanged), rendered as a blockquote in both the default report and the `--rescore` section,
documented in the module docstring and the rubric's FC-3 report-only list
(`docs/forecast-determination-rubric.md`). Tested on synthetic cases
(`tests/scoring/test_capacity_hindcast_scoring.py::test_plant_release_precision_reported_only`:
hit / miss / no-identity / cross-fuel / empty → `None`).

Re-scored (`--rescore`, committed artefacts only, no solve): **D31 economic 13.5 %** (497 /
3,684 MW — the sanity anchor lands exactly), all channels 28.3 %; **bare `miso-t1h` (D46)
economic `None`** (0 MW released — the exhausted floor), all channels 98.5 % (9,650 / 9,799 MW:
the dated channel's plant identity is an input). Both `score.json`s and the two hindcast
reports carry the row; the D46 sidecar is NOT re-emitted (its committed verdict stands, as the
D-24 consumer table prescribes).

## 5. Stale-golden list for the audit programme: EMPTY

All 45 manifests under `results/regression-goldens/` (the enforced `perfb-stage0` one holds
CAISO, ERCOT, ERCOT__carveout-2023, MISO, NEISO, NYISO, PJM) are backcast keeper captures
(`capture_keeper_goldens.py` resolves `keepers/<ISO>.json`; hashed files `btm / flows /
storage / system / dispatch/<yr>_P1[_fleet]`), and a backcast has no capacity evolution, so no
golden executes `_apply_reliability_floor`. `check_golden_manifest.py` reads the same before
and after. Nothing is handed to R-AF. (PREDECL §3 ✔; the dispatch's "golden manifest catches a
key move" reading is corrected: the goldens never see this code path.)

## 6. The pre-declaration, graded

| | prediction | result |
|---|---|---|
| P1 cross-fuel identity in the A/B | identical per fuel / unit / band | ✔ 21/21 FC-3 rows identical, HOLD → HOLD |
| P2 byte-identity on the bare recipe | ledgers byte-identical to D46 | ✔ `retirements` + `pipeline_events` byte-identical every year (only D52's four post-D46 ledger diagnostic keys differ) |
| P3 replay validation | exact | **MISS by one boundary swap per bundle** (Gibson / Independence — the crossing unit; screen-year CO2 not persisted); pinned, prediction not withheld |
| P4 D31 fixed release | CO2 tail; 976 first; 1073, 1012, 6098, 4271, 963 in; White Bluff / Independence out; within one tranche of 3,684 MW | 976 first (2.4 MW), 1012 / 6098 / 4271 in, White Bluff / Independence out ✔; **1073 out, 963 not a candidate** ✗; MW 3,357–4,608 (boundary wider than pre-declared) |
| P5 D51 fixed release | CO2 tail of the 85-coal set, Marion first | ✔ Marion first; 278.6 MW certain (+782 ambiguous) vs 477.4 |
| P6 cross-fuel in the replay | 100 % coal both keys | ✔ |
| P7 D46 replay | exhausted, empty release | ✔ |
| (c) stale goldens | none | ✔ |
| (d) cache key | `eff2c890746ec966` | ✔ (A/B `meta.json`) |

## 7. Routed

- **The screen-year CO2 rate is not in the ledger.** One float per `pipeline_events` row
  (`co2_rate` at screen time) would make a replay exact and D-2-style attribution of the
  floor's order checkable without a solve; a ledger-schema addition, not this lane's.
- **The fix has no observable on the current MISO recipe.** Any future D32 R1/R3 successor
  that moves MISO off the exhausted-floor regime inherits the corrected order; the next lane
  that sees a MISO 2022 `decided` set is the first to observe it in a solve.
- Pre-existing, unrelated: 4 tests in `tests/scoring/test_ff_readiness_battery.py` fail on
  `origin/main` before and after this branch (verified by stash); not touched.

## 8. Governance attestation

Zero DOF (rule 21): no parameter, threshold, weight or field. Rule 22: solve years 2021 +
2023–2025, 2022 bridged; no out-of-training year. Rule 27: `retirements.py`, the scorer, the
two test files and the probe blob-verified after every push. Rule 28: no `ScenarioConfig`
field, no matrix row; MISO `economic_retirement_screen` cell note updated in this PR. No
keeper / shard / marker / verdict-key change; A/B registered SUFFIXED.

## 9. Reproduction

```
uv run python scripts/regenerate_clean.py
uv run python scripts/probes/_capxd55_retention_replay.py results/hindcast/miso-2021-2025-realized-t1h-d31 --year 2022 --json docs/handoffs/d55/replay-d31.json
uv run python scripts/probes/_capxd55_retention_replay.py results/hindcast/miso-2021-2025-realized-t1h-d51-ratio --year 2022 --json docs/handoffs/d55/replay-d51-ratio.json
uv run python scripts/probes/_capxd55_retention_replay.py results/hindcast/miso-2021-2025-realized-t1h-d46 --json docs/handoffs/d55/replay-d46.json
uv run python scripts/score_capacity_hindcast.py --bundle results/hindcast/miso-2021-2025-realized-t1h-d31 --rescore
uv run python scripts/score_capacity_hindcast.py --bundle results/hindcast/miso-2021-2025-realized-t1h-d46 --rescore
uv run python scripts/run_capacity_hindcast.py --iso MISO --start-year 2021 --end-year 2025 --vintage 2020 --fuel-variant realized --entry-screen-diagnostics --out-dir results/hindcast/miso-2021-2025-realized-t1h-d55-keyfix
# then: score_capacity_hindcast.py --bundle <dir>; --flip-gate-extras; forecast_verdict.py --tier t1h ...; register_forecast_run.py --bundle <dir>
uv run python -m pytest tests/unit/model/test_capacity.py tests/scoring/test_capacity_hindcast_scoring.py -q
```
