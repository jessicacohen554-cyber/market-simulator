# FINDING — SCN-WS0: emissions grain + scenario harness (foundation)

**Lane:** SCN-WS0 · **Branch:** `claude/scn-ws0-k7m2-8743yi` · **Date:** 2026-09-05
**Charter:** `docs/handoffs/forecast-scenario-readiness-plan-2026-09.md` §3 WS-0 / §7 "WS-0"
**PRECOMMIT:** `docs/handoffs/PRECOMMIT-scn-ws0-t0-2026-09-05.md`
**Data profile:** `neiso` · **Model:** `claude-opus-5` (rule 27 `[R-PUSH]`: this lane
writes `src/market_sim/` and `scripts/`)

---

## 0. Bottom line

All six deliverables land, plus the G-E4 rider SCN-WS1a routed here after it merged
(§4b: the mass-cap allowance price now persists and is exported; the tons-valued slack
needs a `runner.py` region this lane does not hold and is routed back). The paired NEISO 2026 T0 solves clean on both arms (0 FAIL /
0 WARN across the 14 forecast invariants, each) and **passes all five structural
STOP-gate checks**. Both arms are registered in the forecast namespace under the new
`scenario` kind, campaign `scn-ws0-smoke`.

**The T0's substantive result is a leakage finding, and it is exactly the thing the new
import line was built to make visible.** A $25/tCO2 adder cuts NEISO's *modeled in-ISO*
CO2 by **−2.71 Mt (−16.6 %)** — and **+1.85 Mt of that reduction leaves through the
NYISO seam**, where imports rise +4.32 TWh on a single tranche. On the scored
`emissions_mt` basis alone the case reads as a 16.6 % cut. With the disclosure line
read beside it, the *modeled* net is closer to **−0.85 Mt (−5.2 %)**, i.e. roughly
**two thirds of the headline reduction is displaced across the border and invisible to
the number the model scores**. Nothing about this is a defect in the solve; it is
G-E3 (plan §2.5), measured, on a real case, for the first time.

---

## 1. What landed (six commits)

| # | Commit | What |
|---|---|---|
| 1 | `a66ea7c8` | Emissions grain: `emissions_by_fuel_mt`, `emissions_by_zone_mt`, `import_co2_mt_reported` + `import_co2_basis`, `unserved_mwh` in `_summarize_year`; `DispatchResult.emissions` populated on read |
| 2 | `cf7170f4` | `build_matrix_frame` carries every scalar metric; new `scripts/report_scenario_deltas.py`; `report_ces_campaign.py` delegates the generic tables |
| 3 | `a248c8ac` | `scripts/collate_scenario_campaign.py` — the six-ISO rollup, three side lines, never "national" |
| 4 | `e6464bde` | Twelve REF base YAMLs; `configs/scenario_campaign_matrix.yaml`; `--set FIELD=VALUE` on both runners |
| 5 | `c95f59de` | `scenario` registration kind + campaign grouping and CO2 delta-vs-reference in the run explorer |
| 6 | this | The paired T0 through the new tables; both arms registered; this FINDING; the §5.1 scorecard |

Test suite: **1,515 passed** across `tests/scoring` + `tests/unit/results` with the new
files in place. The only failures in that sweep, `test_golden_manifest_provenance.py`
(2, ERCOT `carveout-2023` keeper-shard/golden-manifest disagreement), **reproduce
identically on a clean `origin/main` checkout** and are outside this lane entirely —
routed to SCN-DESK below, untouched here.

---

## 2. The paired T0 — measured

Two NEISO invocations, 2026 only, launched concurrently (rule 12 `[R-PARALLEL]`).

| | REF | CARB (`--set carbon_price_delta=25`) |
|---|---|---|
| cache key | `c3592c1adbc8ac17` | `eed460b6ddfaab1c` |
| **wall** | **2.3 min** (median year 140.1 s) | **2.2 min** (median year 132.9 s) |
| **peak RSS** | **3.31 GB** | **2.94 GB** |
| invariants | 0 FAIL / 0 WARN (14 scored) | 0 FAIL / 0 WARN (14 scored) |
| `emissions_mt` | 16.3081 | 13.5987 |
| `import_co2_mt_reported` | 4.5718 | 6.4266 |
| `unserved_mwh` | 0.0 | 0.0 |
| load-weighted price | $52.13/MWh | $62.28/MWh |
| `clean_share` | 0.3447 | 0.3446 |

### 2.1 Where the CO2 went (by fuel, Mt)

| fuel | REF | CARB | Δ |
|---|---|---|---|
| gas_cc | 15.6171 | 12.9732 | **−2.6438** |
| gas_ct | 0.5296 | 0.4658 | −0.0638 |
| gas_st | 0.1614 | 0.1596 | −0.0018 |
| **total** | **16.3081** | **13.5987** | **−2.7094** |

Every other fuel class is exactly zero in both arms, which is the partition working:
the reduction is entirely inside the gas stack, as a marginal-cost adder must make it.

### 2.2 What replaced it (generation, TWh)

| fuel | REF | CARB | Δ |
|---|---|---|---|
| gas_cc | 40.4186 | 34.6052 | **−5.8134** |
| **import** | 28.5403 | 33.1048 | **+4.5645** |
| biomass | 5.7411 | 7.1158 | **+1.3747** |
| gas_ct | 1.5384 | 1.4371 | −0.1013 |
| gas_st | 0.5158 | 0.5108 | −0.0050 |

Displaced gas is replaced ~78 % by imports and ~22 % by biomass. Biomass carries a zero
CO2 rate in the model (biogenic, carbon-neutral under EPA/RGGI accounting — the basis
`compute_fossil_avg_rate` documents), so its 1.37 TWh contributes an in-ISO reduction of
its own that the accounting treats as real. Whether a 24 % jump in biomass output is a
supply-realistic response on this fleet is a question for the campaign's credibility
disclosure (plan §4), not for this lane.

### 2.3 Where it went — by zone (Mt)

| zone | REF | CARB | Δ |
|---|---|---|---|
| Connecticut | 6.8018 | 5.7677 | −1.0341 |
| Boston | 3.9338 | 3.2720 | −0.6617 |
| North | 3.2707 | 2.5947 | −0.6760 |
| Central | 2.3018 | 1.9642 | −0.3375 |
| HQ_import | 0.0000 | 0.0000 | 0.0000 |

`HQ_import` reads exactly zero in both arms, which is the design under test: the LP
holds every import tranche's emission rate at zero and prices border carbon in the
tranche VOM, so no import MWh can inflate the scored in-ISO total.

### 2.4 The leakage, per tranche (the disclosure line)

| tranche | EF (t/MWh) | REF TWh | CARB TWh | Δ TWh | Δ reported Mt |
|---|---|---|---|---|---|
| HQ_PhaseII | 0.000 (firm hydro) | 15.888 | 16.118 | +0.231 | 0.0000 |
| Highgate | 0.000 (firm hydro) | 1.971 | 1.971 | 0.000 | 0.0000 |
| **NYISO_CT_peak** | 0.428 (disclosure default) | 3.061 | 7.378 | **+4.318** | **+1.8480** |
| NB_north | 0.428 (disclosure default) | 0.000 | 0.016 | +0.016 | +0.0068 |
| NYISO_CT_base | 0.428 | 7.621 | 7.621 | 0.000 | 0.0000 |
| **total** | | | | **+4.565** | **+1.8548** |

The whole import increase is **one rung: NYISO_CT_peak**. The firm Hydro-Québec seams
are already near their measured depth and barely move; the carbon price pushes NEISO's
marginal gas across the New York border, onto a rung the ladder itself names as
CT-priced.

**And the 1.85 Mt is more likely an UNDER-statement than an over-statement.** The
disclosure default for a seam with no derived EF is CARB's unspecified 0.428 t/MWh. A
gas CT — which is what the rung is named for — runs nearer 0.53 t/MWh
(≈10 MMBtu/MWh × the repo's own 0.0531 tCO2/MMBtu gas factor). At that rate the
displaced 4.32 TWh is ≈2.29 Mt, and the modeled net reduction shrinks from −0.85 Mt to
≈−0.42 Mt. The disclosure string says plainly that 0.428 is a default and not a
measured seam rate; this T0 is the first evidence that the distinction has real
magnitude. **Filed for the data-intake queue** (§5, item 1).

---

## 3. The STOP gate — verdict PASS

The PRECOMMIT's five checks, run on both arms:

| # | Check | REF | CARB |
|---|---|---|---|
| 1 | `Σ emissions_by_fuel_mt` = `emissions_mt` at the scalar's grain | 16.308071 → 16.3081 ✓ | 13.598698 → 13.5987 ✓ |
| 2 | `Σ emissions_by_zone_mt` = `Σ emissions_by_fuel_mt` to 6 dp | 16.30807 ✓ | 13.598697 ✓ |
| 3 | import line reported, non-zero, and `by_fuel["import"] == 0.0` | 4.5718 / 0.0 ✓ | 6.4266 / 0.0 ✓ |
| 4 | delta table reproduces the arithmetic (by-fuel and by-zone deltas each sum to −2.7094) | ✓ | ✓ |
| 5 | no non-target load-bearing criterion flips | 0 FAIL / 0 WARN | 0 FAIL / 0 WARN |

**The gate passes. It could only have killed the deliverable; it promotes nothing**, and
none of its checks reads a residual.

### 3.1 One prediction in the PRECOMMIT was wrong, and it was mine

The PRECOMMIT predicted the CO2 delta would be "**low single-digit percent**". It is
**16.6 %**. The sign, the footprint (confined to the gas stack, the imports and prices)
and the unserved-energy prediction were all right; the magnitude was not. The reasoning
that produced the estimate under-weighted how thin NEISO's gas-to-import margin is:
$25/t is ≈$9–10/MWh on a gas CC, and the NYISO_CT_peak rung sits inside that spread, so
a single adder moves 4.3 TWh across the seam rather than nudging the stack's internal
order. Recorded here because a pre-registered expectation that missed is evidence about
the system and about the estimate, and a precommit whose misses go unreported is not
a precommit. **This did not and could not change the gate**, whose checks are structural
and were fixed before the solve.

---

## 4. Deviation from the charter, stated plainly

**One, in deliverable 1.** The charter says to populate `DispatchResult.emissions` "at
solve time". Doing so would persist a second full `(n_gen, T)` float64 column through
`cache.save_result` → `to_parquet`, roughly doubling the dispatch payload of every
cached scenario-year across six ISOs and 25 horizon years, to store a product exactly
implied by two things the file already holds (the `dispatch` column and `emission_rate`
in the fleet metadata). The array is therefore **derived on read** in
`outputs.py::from_parquet` instead.

This delivers the charter's stated purpose exactly — the declared field stops being a
null on every loaded result, and `run_full_horizon._co2_tons` reads it rather than
falling back — at zero disk cost and with no change to the LP, the cache key, or any
scored number. The four consumers that each carried their own identical fallback
(`_co2_tons`, `check_forecast_invariants`, `score_crossover`,
`score_capacity_hindcast`) are unaffected either way, because the fallback and the
derivation are the same product. **Routed to SCN-DESK as an information item** — no file
outside this lane's regions was touched, and the desk may reverse the call cheaply if
the persisted column is wanted for another reason.

**No other deviation.** No default moved, no ScenarioConfig field was added, no LP row
or objective coefficient changed, no CI workflow was created, and no file outside the
lane's declared regions was edited.

---

## 4b. The G-E4 rider from SCN-WS1a — CLOSED (the price half), scoped (the slack half)

WS-1a landed on `main` while this lane was open and routed one item here
(`FINDING-scn-ws1a-2026-09-05.md` §4.3): `DispatchResult.co2_cap_price` — the emissions
mass-cap row's negated dual, i.e. the endogenous power-sector allowance price — had **no
reader anywhere under `src/market_sim/results/`**, so a CAP-STATE-TIGHT arm "has no
exported read-out and cannot be scored". The ask was `co2_cap_price` **and**
`co2_cap_slack_t` in `summarize_year` and in the trajectory row.

It was worse than "no reader": the field **was not persisted at all**. `to_parquet`'s
metadata block carried `rps_shadow_price`, `rps_region_duals` and `clean_region_duals`
and not this one, so the price was discarded the moment the solve ended and no cache
read could have recovered it.

**Closed here, in this lane's own two files:**

* `results/outputs.py` — `co2_cap_price` now round-trips through the Parquet metadata (a
  short list of floats; `from_parquet` reads it with `.get`, so a year written before the
  key existed still loads and still means `None`).
* `results/export.py::_summarize_year` — emits `co2_cap_price_usd_per_t` (the max across
  active caps, a per-year SCALAR, so it rides `build_matrix_frame` and the headline delta
  table on its own via `matrix.scalar_metrics`), `co2_cap_price_by_cap` (the full list),
  and `n_co2_caps_binding` (a cap binds iff its dual is positive — the binding flag WS-1a
  named as missing, as a count so it too reaches the frame). All three are present at
  `0.0 / [] / 0` when no cap is active, so the frame's column set does not depend on
  posture.

That is the read-out the case exists for: WS-1a's own §4.2 says the row dual is "to be
compared against the adder path's exogenous escalator in the same year — the
price-vs-quantity instrument comparison the case exists for". It is now a column in the
delta table beside the CO2 it bought.

**Not closed, and why — `co2_cap_slack_t`.** Slack in tons is
`cap_tons − Σ_g m[g]·rate[g]·gen_mwh[g]`. Neither `m[g]` (the per-generator membership
weight from `per_generator_membership`) nor `cap_tons` is carried by the cached result or
its `FleetContext`; both are assembled on the solve path in `runner.py:3294-3309`, which
this lane may not write (`runner.py` has no SCN-WS0 region — desk ledger §4). Persisting
them would mean threading the cap block into the `cache.save_result` call site, i.e. a
`runner.py` edit. **Routed back to SCN-DESK** as a one-line change for whichever lane
next holds a `runner.py` region: pass the cap labels + RHS + per-generator coefficient
row-sums into `save_result`, and `outputs.py` will carry them the same way it now carries
the price. Until then the binding COUNT stands in for the sign of the slack (binding, or
room) without a tons figure that would have to be guessed. **The half that blocked
scoring is closed**; the half outstanding is a diagnostic refinement, and no number is
fabricated in its place.

**Not attempted: the trajectory row.** The rider also asks for the cap price in
`full_horizon_summary.json`'s trajectory row. That is `run_full_horizon.py::
extract_trajectory`, and this lane's write scope in that file is **the `--set` override
only** (desk ledger §4). Routed with the slack half; the `_summarize_year` half already
reaches every delta table, which is where the comparison is actually read.

## 5. Routed to SCN-DESK

1. **The NYISO seam's emission factor is a live number now, not a placeholder.**
   §2.4 shows the campaign's headline CO2 answer on NEISO is materially sensitive to a
   constant this repo has never derived. Deriving measured EFs for the non-HQ seams
   (NYISO CT/base, NB, IESO, the PJM rungs) is a `data-intake` question of the same
   class as card D-4, and it now has a magnitude attached to it: on this single T0 it is
   worth ≈0.4 Mt of NEISO's 2.7 Mt answer. Recommend the desk present it alongside D-4
   rather than as a separate card.
2. **`carbon_price_delta` leakage is a cross-ISO question, not a NEISO one.**
   This T0 measured it on the one ISO whose imports are 10–30 % of energy. CAISO's WECC
   seam is the other. SCN-WS1b's six-ISO paired probe should read the import line in
   every arm — the harness now emits it — and the campaign's §4 caveat block should
   carry the leakage number per ISO, not a generic sentence.
3. **`co2_cap_slack_t` and the cap price's trajectory row** — §4b. Both need a
   `runner.py` region this lane does not hold; both are one-line changes for whichever
   lane next holds one. The scoring-blocking half is already closed.
4. **`test_gate_a_provenance.py::test_live_board_passes` fails on `origin/main`**
   (`108235d2`): MISO's `gate.a_keeper_marker` cites the superseded keeper
   `2026-09-05-miso-217-intermphys` while the shard designates
   `2026-09-05-miso-220-nonsteam-lift`. Pre-existing, reproduced on a clean checkout,
   and outside every SCN lane's regions — it belongs to the MISO backcast lane. Flagged
   only so a wave-2 lane does not spend time re-diagnosing it. (The earlier
   `test_golden_manifest_provenance.py` failures this FINDING first reported were fixed
   on main between this lane's two pushes and are green again.)
4. **`data/clean` is a genuine session prerequisite** (FF plan §2.4). Four
   `tests/unit/results/test_export.py` cases fail on a fresh checkout until
   `scripts/data/curate_confirmed_retirements.py` has been run. Worth putting in the
   wave-2 prompts verbatim rather than leaving each lane to rediscover it.

---

## 6. Mechanism matrix

**No cell moves, and none may.** This lane tested no mechanism: `carbon_price_delta` is
a long-registered field with settled semantics, used here only to give the new reporting
surface something real to report. No `ScenarioConfig` field was added, so rule 28
`[R-MECH-MATRIX]` duty (c) does not apply, and duty (b) is not triggered because no
mechanism was probed. `scripts/check_mechanism_matrix.py` passes at HEAD (integrity OK,
anchors checked, keeper stamps and §5.x prose headers match every shard). No shard was
edited by this lane.

---

## 7. Artifacts

- Registered, forecast namespace, kind `scenario`, campaign `scn-ws0-smoke`:
  `neiso-2026-2026-scn-ws0-smoke-ref` and `neiso-2026-2026-scn-ws0-smoke-carb`.
  The committed inputs are the two `frontend/data/hindcast/*.json` sidecars; the
  namespace's `registry/`, `runs/`, `manifest.js` are generated and gitignored (rule 15
  `[R-DASHBOARD]`, FF plan §7.5), rebuilt by the Pages deploy.
- The manifest carries the campaign block: both arms group under `scn-ws0-smoke`, CARB
  showing `co2_delta_mt [[2026, -2.71]]` and REF its explicit `[[2026, 0.0]]` baseline.
- `results/scn-ws0-smoke/` follows the committed `ffr-sa-smoke` T0 convention exactly:
  the **slim artifacts are committed** (192 KB — each arm's `full_horizon_summary.json`
  and `run_config.json`, the matrix bundle, and the delta-report / campaign-rollup
  tables that are the evidence behind every number in §2), while the nested per-ISO LP
  cache each arm writes is gitignored as transient and regenerable from config
  (`.gitignore` `/results/scn-ws0-smoke/*/*/NEISO/`, the same class as
  `/results/<ISO>/`). A T0 harness exercise is not a keeper and is not
  dashboard-registered as one — the registered record is the pair of
  `frontend/data/hindcast` sidecars above.
