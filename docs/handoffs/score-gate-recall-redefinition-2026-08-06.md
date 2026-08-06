# SCORE-GATE — the >=300 MW retirement recall gate, redefined against the REACHABLE set

**Owner decision D-24**, SIGNED at the sitting, Addendum **X.6**, 2026-08-06.
**Evidence:** FFR-7C `docs/handoffs/ffr-7c-exit-decode-corrected-target-2026-08-06.md`
§5 + sitting Addendum X.1.

**Lane: SCORER-ONLY.** No model mechanism, no `ScenarioConfig` field, no solve, no keeper
contact, no bundle mutation, no registration. Branch
`claude/score-gate-recall-metric-crwjww`.

---

## 1. Why

FFR-7C §5 established that ERCOT's `unit_recall_gt300` gate was measuring something **no
admissible screen can pass**. Its denominator held exactly two units, and both are
unreachable:

* **Decker Creek 2** (`3548_2`, 405 MW) — 405 MW of the corrected target is capacity the
  arm's fleet never carried. Plant 3548 appears in the CAMPD bin sheet only as `CT8`, a
  206.0 MW `CT_PEAKER` block; the steam unit has no bin (FFR-7C §2.4 item 2).
* **Sandy Creek 1** (`56611_S01`, 1,008 MW) — clears its going-forward bar at measured RT
  prices in the year before exit (73.4 vs 58.5 $/kW-yr) and in the screen's own loss year
  (298.7 vs 58.5), on every heat-rate and fuel-price variant computed. A **correct**
  economic screen must NOT retire it (FFR-7C §2.2 row 1, §4).

A gate whose members are unreachable grades plumbing, not skill — it can only ever read
0/2, whatever the screen does, and it reads that as a *miss*. That is rule 1
`[R-STRUCT]` inverted: the metric punishes the structurally-correct behaviour.

---

## 2. The member rule, as implemented

`scripts/score_capacity_hindcast.py::classify_exit_reachability`. A target exit is a
**gate member** iff BOTH hold:

1. **(i) Fleet basis** — the unit exists in the run's fleet basis (the vintage fleet the
   run actually built).
2. **(ii) Reachable channel** — its exit is reachable by an admissible channel, either
   * **economic** — no economic exclusion is recorded for it, **OR**
   * **instrument-driven** — a non-superseded confirmed-registry instrument whose
     `instrument_date <= the run's vintage cutoff`. That is the confirmed-exits
     information gate's **own** rule
     (`data.confirmed_retirements.load_confirmed_exits(as_of=...)`), not a scorer
     invention: an instrument dated after the vintage is unknowable at forecast start, so
     the channel cannot fire in that hindcast.

Everything else follows from those two:

* **Unreachable exits leave the denominator** and are listed in a **NON-GATED** diagnostic
  (`retirements.reachability`) carrying unit, MW, fuel, exit year, **driver**, and **why
  unreachable** (`not_in_fleet_basis` / `post_vintage_instrument` / `no_instrument`), so
  the blind spot stays visible on every report instead of silently shrinking the metric.
* **Empty member set ⇒ n/a, never 0/N.** `band = "SKIP"`, `recall = null`, plus an
  explicit `n_a: true` / `n_a_reason`.
* **The vintage cutoff is the RUN's**, not a scorer constant: `vintage_cutoff_of()` reads
  `eia860_vintage_year` from the solved config, then `meta.json`'s `vintage_year`, and
  falls back to `IS2020_CUTOFF` (2020-12-31 — what every registered bundle uses).

### 2.1 Fail-closed, in three places

The gate **only ever excludes on positive, cited evidence from committed artifacts**. Three
distinct fail-closed guards, each tested:

| guard | when it fires | effect |
|---|---|---|
| **No evidence** | the unit appears in neither the exit decode nor the registry | stays IN the member set |
| **Seam-dependent verdict** | the decode's economic verdict flips between the target-taxonomy bar and the physical-class bar (the known `gas_st`↔`gas_ct` seam) | not positive evidence ⇒ stays IN |
| **Evidence basis ≠ run basis** | the decode's fleet facts are read off the CAMPD bin sheet, so they describe the fleet only under `use_campd_bins`; and the economic exclusion is only decisive when the economic screen governs fossil exits (`forecast_fossil_retirement_economic`) | the exclusion is **not taken** |

The third guard is why **no other ISO's gate changes**: only ERCOT has a committed decode
(`EXIT_DECODE_EVIDENCE`), so PJM / MISO / NYISO / NEISO classify every large target row as
reachable and their denominators are byte-identical to pre-D-24.

Measured across all five committed targets:

| ISO | rows >=300 MW | members | unreachable rows reported | of which gated |
|---|--:|--:|--:|--:|
| PJM | 20 | **20** | 0 | 0 |
| MISO | 19 | **19** | 0 | 0 |
| NYISO | 1 | **1** | 0 | 0 |
| NEISO | 4 | **4** | 0 | 0 |
| **ERCOT** | 2 | **0** | **5** | **2** |

### 2.2 What the rule does NOT do

* It does not touch `total_gw`, `per_fuel`, `false_retire`, the additions bands, CO2, or
  T-R10 — verified by assertion in the re-score probe (`before[key] == after[key]`).
* It does not change any band **threshold**. `BANDS["retire_recall_min"] = 0.70` is
  untouched; only the denominator's membership is redefined.
* It excludes nothing on prose. Every exclusion carries a machine-readable citation to a
  committed artifact (see §3).

---

## 3. Per-unit classification — ERCOT corrected target

Evidence sources, all committed:
`data/raw/_validation-source/capacity_actuals_ercot.csv` (md5
`03b34821ba53854a410de42ca69afbc0`) · `data/raw/confirmed-retirements/ercot.csv` ·
`docs/handoffs/ffr-7c/exit-decode-2026-08-06.json` (FFR-7C §2.2 per-unit margins / §2.4
fleet-basis facts).

Run basis: `use_campd_bins = True`, `eia860_vintage_year = 2020` ⇒ **cutoff 2020-12-31**
(both FFR-5D arms, from their committed `run_config.json`).

| unit | MW | fuel | exit | in fleet? | economic channel | instrument channel | verdict | gated |
|---|--:|---|--:|---|---|---|---|:--|
| `56611_S01` Sandy Creek 1 | 1008.0 | coal | 2025 | **yes** — `SC_COAL3 (plant 56611, 936.0 MW, HR 9.50)` | **EXCLUDED** — margin **73.41** vs bar **58.5** $/kW-yr in 2024 (unit-net), bar-invariant | **none** — no registry row exists (ERCOT file holds only the three Braunig units) | **UNREACHABLE** `no_instrument` | **yes** |
| `3548_2` Decker Creek 2 | 405.0 | gas_ct | 2022 | **NO** — `ABSENT (3548 carries only CT8, CT_PEAKER 206.0 MW)` | (moot) | (moot) | **UNREACHABLE** `not_in_fleet_basis` | **yes** |
| `3612_2` V H Braunig 2 | 252.0 | gas_ct | 2025 | yes — `SC_STGAS3 (plant 3612, 1138.0 MW, HR 8.49)` | **EXCLUDED** — margin **63.35** vs bar **21.0**, bar-invariant | `ercot-nso-braunig-2`, `rto_deactivation`, **instrument_date 2024-03-13 > 2020-12-31** | **UNREACHABLE** `post_vintage_instrument` | no (<300 MW) |
| `3612_1` V H Braunig 1 | 225.0 | gas_ct | 2025 | yes — `SC_STGAS3 (plant 3612, 1138.0 MW, HR 8.49)` | **EXCLUDED** — margin **69.74** vs bar **21.0**, bar-invariant | `ercot-nso-braunig-1`, `rto_deactivation`, **instrument_date 2024-03-13 > 2020-12-31** | **UNREACHABLE** `post_vintage_instrument` | no (<300 MW) |
| `52120_G-66` Freeport Energy G-66 | 119.0 | gas_cc | 2023 | yes — `H_CHP2 (plant 52120, 419.3 MW, HR 5.86, class CC_CHP)` | **EXCLUDED** — margin **176.44** vs bar **30.0**, bar-invariant | **none** | **UNREACHABLE** `no_instrument` | no (<300 MW) |

**Members = {} ⇒ the ERCOT >=300 MW recall gate reports n/a.**

The three sub-300 MW rows never gated in the first place; they are in the diagnostic
because the diagnostic's job is the **blind spot**, not the denominator delta. Braunig 1/2
in particular are the clean illustration of the instrument leg: they are real, confirmed,
instrument-driven exits that this hindcast's information set could not have known — the
NSO post-dates the 2020 vintage by 3.2 years, which is exactly why the shipped confirmed-exit
injector correctly does not fire on them (FFR-7C §4).

The remaining 39 thermal target rows carry **no** evidence either way and stay in the
member set by the fail-closed rule; none is >=300 MW, so none gates.

---

## 4. Before / after — the two FFR-5D arms

Re-emitted **committed-artifact-only, no solve**, by
`scripts/probes/score_gate_d24_rescore_ffr5d.py`, which extends FFR-7A's re-score
construction: the model side is reconstructed from each arm's own committed
`crossover_score.json` per-fuel `model_gw` and graded by the **shipped**
`score_capacity_hindcast.score_retirements`. **Neither registered bundle was touched and
nothing was re-registered.**

| arm | metric | BEFORE (pre-D-24) | AFTER (D-24) |
|---|---|---|---|
| **shipped** | unit recall >=300 MW | 0/2 = **0 % (FAIL)** | **n/a** — 0 of 2 target rows reachable (band `SKIP`) |
| | thermal GW retired | 0.0 vs 2.294 actual, −100 % (**FAIL**) | *unchanged* |
| | false-retire | 0.0 GW, 0 % of model (**PASS**) | *unchanged* |
| | plant-exact recall (diagnostic) | 0.0 | n/a |
| **unified** | unit recall >=300 MW | 0/2 = **0 % (FAIL)** | **n/a** — 0 of 2 target rows reachable (band `SKIP`) |
| | thermal GW retired | 10.943 vs 2.294 actual, +377 % (**FAIL**) | *unchanged* |
| | false-retire | 10.943 GW, 100 % of model (**FAIL**) | *unchanged* |
| | plant-exact recall (diagnostic) | 0.0 | n/a |

The reachability classification is **identical for both arms** — it is a property of the
target and the fleet basis, not of the screen — so the gate change is not an arm-selective
effect.

**It launders nothing.** Both arms' FC-3 verdicts are unmoved, because the D-24 change
removes one FAIL and every other failing band stands:

| arm | FC-3 fails BEFORE | FC-3 fails AFTER | FC-3 verdict |
|---|---|---|---|
| shipped | `retire.total_gw`, `retire.unit_recall_gt300`, + 7 additions bands | `retire.total_gw`, + 7 additions bands (recall → `skips`) | **FAIL → FAIL** |
| unified | `retire.total_gw`, `retire.unit_recall_gt300`, `retire.false_retire`, + 10 additions bands | `retire.total_gw`, `retire.false_retire`, + 10 additions bands (recall → `skips`) | **FAIL → FAIL** |

And FFR-7C §5's standing reading is unchanged: the unified arm's 10.9 GW `gas_st` wave is
still a pure false-retire at `false_retire_frac = 1.00`. D-24 removes a metric that could
not discriminate; it does not soften one that can.

---

## 5. Downstream-consumer check

Grepped: `scripts/`, `src/`, `tests/`, `.github/workflows/`, `frontend/`,
`docs/codebase-site/`. Everything that reads the recall metric, and what D-24 does to it:

| # | consumer | reads | effect | action taken |
|---|---|---|---|---|
| 1 | `score_capacity_hindcast.write_report` | `unit_recall_gt300` row | renders `n/a` instead of a blank; the D-24 membership line + the unreachable table are appended under the retirement table | **updated** |
| 2 | `score_capacity_hindcast.render_rescore_section` (T-R8 raw vs IS-2020) | `recall`, `plant_recall_frac` | already `None`-safe; now prints `n/a`, and renders the same diagnostic | **updated** |
| 3 | `score_capacity_hindcast.loyo_folds` → `holds_2of3["recall_pass"]` (the **rule-22 LOYO promotion bar**) | per-fold `recall_band == "PASS"` | a >=2/3 bar over three n/a folds would have read **False** — a phantom failure | **updated**: `recall_pass` is `null` when *every* fold is n/a, with the reason in `note`. Mixed folds are unaffected |
| 4 | `score_crossover.score_capacity_events` | calls `CH.score_retirements` | would have kept the pre-D-24 denominator, so one run's recall verdict would depend on which scorer produced it | **updated**: same rule, same evidence, same fail-closed fallback; report row + diagnostic wired |
| 5 | `forecast_verdict._collect_hindcast_bands` → **FC-3 "hindcast bands"** | `retirements.unit_recall_gt300.band` | `SKIP` is already a first-class state there: only `FAIL` fails the row, and `SKIP` is disclosed in the reason string (`"; SKIP bands [...]"`). An n/a recall therefore **removes** a FAIL and is reported, never hidden | **no change needed** (verified empirically, §4) |
| 6 | `register_hindcast.py` (dashboard payload JS) | `rr.recall`, `rr.band` | rendered `—` with a `SKIP` chip | **updated** to `n/a` + `no reachable member — D-24` |
| 7 | `docs/codebase-site/forecast-runs.html` (Run Explorer) | `unit_recall_gt300.recall/.band` | same | **updated** to the same wording |
| 8 | `.github/workflows/*.yml` | — | **no workflow reads the recall metric.** The CI jobs (`quarantine-gates`, `forecast-invariant-artifacts`, `forecast-staleness-warn`, `forecast-parity-guard`, `mechanism-matrix-guard`, `cache-key-guard`, `lint`, `fast-tests`, `refactor-guards`) contain no reference to it | none |
| 9 | `check_forecast_staleness.py` | *not* a metric consumer — but `scripts/score_crossover.py` is in `SOLVE_AFFECTING_PATHS` | this PR increments the WARN-only commit-distance for boards scored before it | reported, no action (WARN-only by design) |
| 10 | `scripts/probes/ffr7a_rescore_ffr5d_arms.py` | `unit_recall_gt300` | unchanged: it calls `score_retirements` with no reachability, i.e. the pre-D-24 denominator, which is what that FFR-7A record documents | left as-is (historical record) |
| 11 | committed sidecars `frontend/data/hindcast/*.json` | *data*, not consumers | they carry pre-D-24 recall numbers and are **not** rewritten here — a registered run keeps its committed verdict until re-emitted | reported, no action |

**No gate other than the recall band itself changes verdict.** The two that could have
moved silently — the LOYO `recall_pass` bar (#3) and FC-3 (#5) — were checked directly:
one is fixed to report n/a, the other already handles `SKIP` correctly.

---

## 6. Tests

`tests/scoring/test_capacity_hindcast_scoring.py`, 11 new cases (44 pass in the file):

| test | asserts |
|---|---|
| `test_d24_ercot_corrected_target_has_no_reachable_member` | the committed case: `n_target_large == 2`, `members == []`, **5-row** diagnostic with the exact per-unit reasons, and `recall is None` / `band == "SKIP"` / `n_a is True` |
| `test_d24_margin_driven_exit_is_a_member` | a synthetic margin-driven exit **stays** in the gate and still scores `FAIL` when the model misses it |
| `test_d24_fail_closed_no_evidence_stays_in` | no evidence ⇒ member |
| `test_d24_pre_vintage_instrument_reaches_an_econ_excluded_exit` | economic excluded **but** instrument dated <= V ⇒ member; the same instrument dated after V ⇒ excluded |
| `test_d24_fleet_absence_excludes_only_on_the_matching_fleet_basis` | fleet exclusion applies under `use_campd_bins`, and is **not taken** under `False` or an absent config |
| `test_d24_economic_exclusion_needs_the_economic_screen_to_govern` | `forecast_fossil_retirement_economic = False` ⇒ exclusion not taken |
| `test_d24_seam_dependent_verdict_does_not_exclude` | a bar-seam-dependent verdict is not positive evidence |
| `test_d24_reachability_none_keeps_the_pre_d24_denominator` | every pre-D-24 caller is byte-unchanged |
| `test_d24_target_without_unit_ids_is_not_filtered` | no `unit_id` column ⇒ no filtering |
| `test_d24_loyo_recall_pass_is_na_not_false_when_every_fold_is_na` | the LOYO bar reports `null`, not `False` |
| `test_d24_vintage_cutoff_follows_the_run` | the cutoff comes from the run, solved config over `meta.json` |

Suite state: `tests/scoring/test_capacity_hindcast_scoring.py` 44 passed;
`test_score_crossover.py` + `test_forecast_verdict.py` 100 passed. The 6 failures in
`test_ff_readiness_battery.py` / `test_forecast_parity.py` are **pre-existing on clean
HEAD** (verified by stashing this branch's diff) and untouched by this change; so is
`check_site_sri.py`'s exit-1 (KaTeX pins in `policy-scarcity.html`).

---

## 7. Governance

* **Rule 22 — nothing spent.** No solve, no out-of-training year touched, no registration,
  no keeper contact. The re-score reads committed artifacts only.
* **Rule 15/16.** No run solved, none registered, no dashboard *data* file written. The two
  FFR-5D arms keep their existing registrations and their committed bundles are untouched;
  their pre-D-24 committed verdicts stand until someone re-emits them.
* **Rule 28.** **Scorer change, no mechanism** — no `ScenarioConfig` field added, nothing
  armed or refuted, so **no matrix cell is adjudicated and no header re-stamp is due**.
  `scripts/check_mechanism_matrix.py` passes (exit 0).
* **Rule 5 `[R-NO-MAGIC]`.** No new numeric parameter. `LARGE_UNIT_MW` and
  `BANDS["retire_recall_min"]` are unchanged; the vintage cutoff is read from the run.
* **Rule 24 `[R-REGISTRY]`.** No new tuning channel: the scorer gained no knob that can
  change a solve, and the classification is a pure function of committed artifacts + the
  run's own recorded config.
* **Rule 27.** No file >=300 lines was rewritten from regenerated content; all edits are
  local `Edit` calls pushed as the exact on-disk bytes. `git status --short` was checked
  after every Python write — the ruff hook reformatted only this session's own edits and
  never touched `src/market_sim/config/constants.py`.
* **Rule 1 `[R-STRUCT]`.** This removes a metric that could not distinguish a correct screen
  from an incorrect one; it does not move a band to make a run look better, and §4 shows
  both arms' verdicts are unmoved.

## 8. Artifacts

| path | what |
|---|---|
| `scripts/score_capacity_hindcast.py` | `classify_exit_reachability`, `load_exit_decode`, `load_instrument_index`, `load_solved_scenario_config`, `vintage_cutoff_of`, `render_reachability_section`; `score_retirements(..., reachability=...)` |
| `scripts/score_crossover.py` | same rule wired into the crossover capacity-events path |
| `scripts/register_hindcast.py`, `docs/codebase-site/forecast-runs.html` | n/a rendering on the two dashboard surfaces |
| `scripts/probes/score_gate_d24_rescore_ffr5d.py` | the committed-artifact re-emission (no solve) |
| `tests/scoring/test_capacity_hindcast_scoring.py` | the 11 D-24 cases |

Reproduce with:

```
uv run python scripts/probes/score_gate_d24_rescore_ffr5d.py
uv run python -m pytest tests/scoring/test_capacity_hindcast_scoring.py -q -k d24
```
