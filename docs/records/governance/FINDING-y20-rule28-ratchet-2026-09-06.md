# FINDING — Y-20: the rule-28(c) post-merge ratchet, the validate-only disclosure, and the anchor-severity call

**Lane:** Y-20, Model Audit & Release-Finalization Program. **Model:** Opus.
**Data profile:** code. **Branch:** `claude/y20-rule28-duty-c-ratchet-bnigp8`.
**Main pin at start:** `fca3b656`. **Zero solves, zero matrix rows minted, zero cell verdicts
moved, zero new `ScenarioConfig` fields, zero workflow files added.** This lane changed the
CHECKER, not the matrix content.

Charter items → sections: R2 (post-merge ratchet) → §1–§3; R3 (validate-only disclosure) → §4;
R4 (anchor-blame severity, the design call) → §5; R1 (required status check, owner-only) → §6.
The fields the new ratchet admits, and where they route → §7.

---

## 0. Bottom line

| item | outcome |
|---|---|
| **R2 — post-merge ratchet** | **Shipped.** New `absent_shared` block in `mechanism-matrix-gaps.json` (**185 fields**) + `check_mechanism_matrix.absent_shared_ratchet`, and **all three diff-free ratchets moved above `if not args.base: return 0`** so validate-only mode is now a registration verdict. Measured: the PR-#4870 field shape (shared, forecast-only, keeper-unarmed) went from **invisible in both post-merge modes** to **exit 1, named, in both**. §2 has the four-run before/after. |
| **R3 — say what was not checked** | **Shipped.** One line, printed on every `--base`-less run: `diff gate NOT RUN — pass --base <sha> … A 0 from this mode is not a registration verdict for a NEW field.` |
| **R4 — anchor severity** | **Decided: downgrade the mechanically-repairable class to a warning; keep the hard fail for anchors no command can repair.** Reasoning in §5. Measured at this pin: 244 stale anchors, **244 of them digit-drift (`fix` derivable), 0 unrepairable** — so today the guard's red can only mean an unregistered field, which is the point. |
| **R1 — required status check** | **NOT this lane's; recorded as owed to the owner.** §6. It is a repo-settings act, and until it is taken every leg here is advisory in effect — PR #4870 merged with this guard red and six other checks red. |
| **Bonus defect found & fixed** | `--write-baseline` run from a partial checkout silently emptied `shared_armed_on_keeper` for any ISO whose keeper bundle was not on disk — a ratchet shrinking by accident. Prior entries are now carried forward and the ISO is named. §3.3. |

Verification: `20 passed` in the ratchet test file (11 before, **9 new**), `715 passed, 21 skipped`
across `tests/unit/config/`, `ruff check` + `ruff format --check` clean on all four changed
source files, and the checker exits 0 in both modes on the committed tree.

---

## 1. What was broken, in one paragraph

`check_mechanism_matrix.py` had exactly one leg that could see a new field's registration — the
`--base` diff gate — and two ratchets that ran diff-free but only over qualified subsets
(`gap_ratchet`: fields carrying an ISO stem; `shared_gap_ratchet`: shared fields a designated
**backcast keeper** arms away from default). A **shared, keeper-unarmed** field therefore had no
census on either side of a merge: the diff gate sees it in its own PR and never again, and neither
ratchet's qualifier can ever be satisfied by a forecast-only field that `__post_init__` refuses in
backcast mode. `FINDING-scn-mxr-2026-09-06.md` §1.1 diagnosed this on `federal_ces_acp_usd_per_mwh`
and `federal_ces_target_by_year`, which merged in PR #4870 five seconds after it opened, past a red
diff gate nobody read. Two consequences, both repaired here: (i) the checker's **validate-only**
mode returned 0 before any registration leg ran, which is what made three desk readings of
"CI exited 0" false; (ii) **post-merge, nothing could see the field again.**

---

## 2. R2 — the post-merge ratchet, and the proof it bites

### 2.1 The mechanism

A third leg, `absent_shared_ratchet`, with **both qualifiers dropped**: its census is every SHARED
(non-ISO-stemmed) `ScenarioConfig` field, **by name**. No default value is parsed and no bundle is
read, because registration asks only whether the matrix mentions the field — which is also why this
leg reaches the 18 fields whose defaults `_scenarioconfig_defaults` cannot parse
(`default_factory`/computed) and the keeper-armed leg therefore skips. Same shrink-only contract and
same mention-anywhere escape hatch as its two siblings; baseline block `absent_shared`, written by
`mechanism_matrix_gap_sweep.py --write-baseline`.

Together with `gap_ratchet`'s ISO-scoped half, the diff-free coverage is now **every field in the
class**: 798 fields = 339 ISO-scoped + 459 shared. And all three legs now run **before** the
validate-only return, which is what makes a slipped field red on `main` and on every later PR until
its row lands.

`shared_gap_ratchet` is deliberately **not** subsumed. It stays the sharper alarm on the same class
— a field shaping a *published keeper* — with its own, empty baseline, so a field forgiven by
`absent_shared` still fails there the moment a keeper arms it. **No existing leg was weakened.**

### 2.2 The four-run proof

Method: insert one shared, keeper-unarmed field (`y20_probe_unregistered_field: bool = False`) into
`ScenarioConfig` in the working tree, add **no** matrix row and **no** baseline entry, then run both
the pre-change checker (`origin/main` blob, run from `scripts/` so its `REPO` resolves) and the new
one. `--base HEAD` is the post-merge shape exactly: the field is in the tree, and the diff contains
nothing, so the diff gate's new-field leg cannot fire. Tree restored afterwards; `scenarios.py` is
byte-unchanged on this branch.

| run | mode | pre-change checker | this branch |
|---|---|---|---|
| **A** | validate-only | **exit 0**, field never named | **exit 1**, `absent-shared ratchet: shared field \`y20_probe_unregistered_field\` is in neither the mechanism matrix … nor the … ratchet (rule 28c)` |
| **B** | `--base HEAD` (post-merge: field in base *and* head) | **exit 1 for anchor noise only** — `grep -c y20_probe… = 0`, both ratchets print OK | **exit 1**, same error line, field named |
| **C** | validate-only, field added to `absent_shared` | n/a | **exit 0**, `absent-shared ratchet OK` |
| **D** | validate-only, field named in a matrix note instead | n/a | **exit 0** — the mention-anywhere escape hatch still works |

Run **B** is the finding's REPRO B and the whole point: the old checker was red on that tree, but
red for the *wrong reason* (two line anchors the inserted line staled, 244 → 246), while the
unregistered field passed both ratchets silently. That is the pathology R2 and R4 close together.

**ISO-scoped complement, same method** with `pjm_y20_probe_unregistered_field`: pre-change
validate-only **exit 0**; this branch **exit 1**, `gap ratchet: PJM-scoped field … is in neither the
mechanism matrix … nor the … ratchet`. The ISO-scoped leg was never broken — it simply never ran
without a diff.

### 2.3 The durable tests

`tests/unit/config/test_mechanism_matrix_shared_ratchet.py`, +9 tests (11 → **20 passed**):

- `TestAbsentSharedRatchetClosesThePostMergeHole` — 4 tests, the post-merge shape: fails on an
  unbaselined shared field; passes once baselined; passes once *registered*; and the
  `test_a_keeper_unarmed_forecast_only_field_is_reachable` case asserting that the same field is
  invisible to `gap_ratchet` and `shared_gap_ratchet` and visible only to the new leg — i.e. it pins
  the hole itself, not just the patch.
- `TestValidateOnlyModeIsHonest` — 2 tests: the R3 line is printed, and all three ratchet legs run.
- `TestCheckerIsNeverStricterThanTheSweep` — +3: the committed baseline satisfies the new leg; the
  two halves see the identical field set (798 = 798); `ISO_STEMS` is the same object in both scripts.
- `TestBaselineShape` — +1: `absent_shared` is one flat sorted list of strings.

---

## 3. The baseline: 185 fields, what they are, and why they are admitted

### 3.1 Size and shape

`absent_shared` opens at **185** — the shared fields with no mention anywhere in
`mechanism-matrix.js` + the six ISO shards, out of 459 shared fields (798 total, 339 ISO-scoped).
It is **one flat list, not a per-ISO map**: a shared field is shared.

**Why 185 and not 0.** This is the first check ever to look at this class, so the number is a
measurement of a pre-existing backlog, not something this change created — the same shape as
`gap_ratchet`'s own opening (161 ISO-scoped fields across six ISOs, since worked to 0) and
`shared_gap_ratchet`'s (twelve on NYISO alone). Populating 185 rows here would be this lane minting
verdict-bearing rows for six ISOs' markets, which rule 25 `[R-ISO-SCOPE]` and rule 28(d) forbid and
the charter refuses outright. §7 routes them instead.

### 3.2 What is admitted, and what deliberately is not

**Admitted:** every shared field the matrix does not name, no exceptions minted. In particular
`SHARED_CENSUS_EXCLUSIONS` is **not** applied to this leg and **was not extended** — its one entry
(`weather_year`) is an *arming* argument ("non-default carries no information for this field"),
which says nothing about whether a mechanism deserves a row, and adding path/identity fields to it
would be exactly the "weaken a leg to make the baseline smaller" the charter refuses. An excluded
field that is genuinely absent is simply baselined like any other.

**The one invariant that had to hold.** The sweep WRITES the baseline (importing the live
`ScenarioConfig`); the stdlib-only checker ENFORCES it. When those two halves last disagreed — `\b`
vs substring — the checker came out *stricter* and demanded a baseline nobody could write. So the
recogniser and the predicate now live once, in `scripts/lib/mech_matrix.py`
(`scenarioconfig_field_names`, `is_iso_scoped`, `absent_shared_fields`, `ISO_FIELD_STEMS`), and both
scripts call them; `ISO_STEMS` stops being two copies under a "keep in sync" comment. Belt and
braces: the sweep takes its census over the **union** of the live dataclass names and the parse, so
the baseline is a superset of anything the checker can compute, and prints a loud warning if the two
sets ever differ (they do not — 798 = 798, pinned by a test).

### 3.3 A defect found while writing the baseline (fixed)

`--write-baseline` derives `shared_armed_on_keeper` from each ISO's keeper `run_config.json`. In a
`code`-profile checkout those bundles are absent, `keeper_config` returns `{}`, and the ISO's census
comes out empty — **silently forgiving whatever it had allowed**. The sweep already refuses a
partial `--iso` set for precisely this reason; this is the same hazard arriving through the checkout
instead of the CLI. Fixed: an ISO with no readable keeper bundle now has its **prior entry carried
forward** and is named in the run report. No values moved in this instance (all six were already
`[]`) — the guard is for the next lane.

Related, and why this PR does **not** touch `results/calibration/_matrix_gap_sweep_<ISO>.json`:
`--write-baseline` rewrites those diagnostic dumps as a side effect, and from this checkout they
would have regressed (NEISO `n_bundles_scanned` 15 → 3). They were reverted; the sweep now warns
about exactly this before a lane commits them. They remain stale on `main` (676 fields, 2026-08-03
keepers) and should be refreshed by a lane holding a full `results/calibration/`.

---

## 4. R3 — the cheapest item on the board

Every `--base`-less run now ends with:

```
mechanism-matrix: diff gate NOT RUN — pass --base <sha> to check new-field registration,
keeper-promotion stamps and anchor blame. A 0 from this mode is not a registration verdict
for a NEW field.
```

The mode itself is no longer empty of registration content — the three ratchets run there now — so
the line says precisely what remains uncovered: a field the PR at hand *adds* is still the diff
gate's job. Module docstring and `Exit codes:` updated to match.

---

## 5. R4 — the anchor-blame call, and why

**Decision: an anchor whose repair is mechanical never fails this script. An anchor no command can
repair fails, and only when the PR at hand created it.** The blame split, the measurement, the
shrink-only baseline and every reported line are kept; only the severity of one class moves.

The split is on `finding["fix"]`, which the checker already computes: the `field` and `row` kinds
carry a derived line number (`--fix-anchors` rewrites the digits, zero judgment), the `path` kind
carries `None` (a file anchor past end of file — nothing can compute a correct value, a human must).

**Why not the other option.** "Auto-repair inside the job" has no honest form here: the guard job
runs on a PR checkout with no commit or push step, so a repair it makes is discarded; making it real
means a bot pushing to contributors' branches (and failing on forks), which is far past what this
lane should build and against the repo's CI-cost posture.

**Why downgrading is right rather than merely convenient** — three reasons, in order of weight:

1. **It is the failure mode that cost the registration gate.** PR #4870's 132 inserted lines in
   `scenarios.py` staled 100+ anchors beneath them; the two real rule-28(c) errors were the last two
   lines of a job that was red for anchors anyway. A guard whose red usually means "you moved line
   numbers" trains everyone to merge through red — and that is exactly what happened.
2. **The class is a treadmill, not a backlog.** A line anchor is an absolute line number into a file
   nearly every lane edits. xiso-3 shipped this check with an empty ratchet and `main` re-staled 214
   anchors within the day. A PR can clear them and be stale again before it merges, so no amount of
   diligence converges — a hard gate on this class is unpayable by construction.
3. **The checker already says the digits are not the identifier.** Its own `--fix-anchors` message
   reads "repairs the digits only; the field NAME is the durable identifier". A correct name on a
   wrong anchor sends a reader to the wrong line; it does not hide a mechanism. That is a
   documentation defect, and it is now reported as one.

**What this does not do.** Nothing about the measurement changes: 244 anchors are still found, still
blamed (`staled by this PR` vs `pre-existing, not this PR`), still printed with their one-command
repair, and the shrink-only anchor baseline still holds. What changes is only that digit drift no
longer decides the exit code — so a **red Rule-28 guard now means a mechanism is unregistered**,
which is a signal worth blocking a merge on and the necessary precondition for R1.

**Measured at this pin:** 244 unresolvable anchors, all in `mechanism-matrix.js`, spanning 236
distinct fields — **195 `field` + 49 `row`, and 0 `path`**. So every one of them is currently in the
downgraded class, and the hard-fail leg is currently inert by measurement rather than by design.
(For the record: the charter's "6 WARNs at this pin" does not match what this lane measures at
`fca3b656` — 244, on both the pre-change and post-change checkers. The 244 are pre-existing on
`main`, belong to `--fix-anchors` in whichever lane next edits the base file, and are not this
lane's to clear.)

---

## 6. R1 — recorded as owed to the owner

**Make "Rule-28 mechanism-matrix guard" a REQUIRED status check on `main`.** This is a repo-settings
act, owner-only, and it is not this lane's. Until it is taken, everything above is advisory in
effect: PR #4870 merged with this guard red *and six other checks red*, five seconds after opening,
so no check governed the merge whatever it printed.

Two things this PR changes about that decision, both in the direction of making it safe to take:

- The guard's red now means "a mechanism is unregistered" rather than "you moved line numbers"
  (§5), so requiring it does not make line-digit drift a merge blocker.
- The guard now fails post-merge as well as in-PR (§2), so requiring it actually closes the hole
  rather than closing it only for PRs whose checks are allowed to finish.

One caution for whoever takes it, already documented in `ci.yml`'s own header: this workflow is
path-filtered, and GitHub leaves a **path-skipped** required check *Pending* forever. The
`mechanism-matrix-guard` job's paths already include `src/**`, `scripts/**`, `CLAUDE.md` and the
matrix files, and three record-doc paths were enrolled for this reason — but the interaction is the
owner's to verify before flipping the setting, not a lane's to assume.

**Not done here, deliberately:** no `push: branches: [main]` trigger was added. It would run all ten
CI jobs on every merge to `main` (billed runner minutes on a private repo, against the repo's stated
CI-cost policy) to buy a signal the ratchet already delivers on the next PR to run. If the owner
wants a true on-main signal, that is a separate, costed decision.

---

## 7. What the new ratchet surfaces, and where it routes

**These are LISTED, not fixed.** The charter refuses row-minting in this lane, and rule 25
`[R-ISO-SCOPE]` / rule 28(d) make a per-ISO verdict the owning market's session to derive. A desk
closing any of these edits `mechanism-matrix.js` (base row) plus a cell line in every shard, then
re-runs `mechanism_matrix_gap_sweep.py --write-baseline` — which is what shrinks the baseline.

| family | n | route to |
|---|---|---|
| offer curve / heat rate / passthrough | 43 | the offer-curve lane — **highest priority**: these are the neighbourhood of rule 1 `[R-STRUCT]`'s *authorized price-tuning channel*, and a tuning channel with no matrix row is an unregistered channel in spirit (rule 24 `[R-REGISTRY]`) |
| retirement & capacity evolution | 37 | capx desk (`retirement_*`, `fixed_om_*`, `ccs_*`, entry/WACC) |
| policy: IRA / CES / carbon / EAC | 32 | scenario/policy desk — note SCN-WS2a's open PR #4902 mints the `federal_ces_target` row; the other `federal_ces_*` sub-scalars ride it if its `def` names them |
| AS / ORDC / scarcity & deployment floors | 18 | the AS/scarcity lane; the three `*_deployment_*` / `*_floor_frac` fields are rule 17 `[R-FLOOR-WINDOW]` objects and want a window statement, not just a row |
| renewables / storage / new tech | 14 | forecast tech lane |
| weather / derate / outage physics | 10 | physics lane |
| fuel prices & basis | 8 | fuel lane |
| input paths & fleet representation | 8 | **judgment needed, owner-adjacent**: `campd_bins_path`, `plant_registry_path`, `end_year`, `heat_rate_bin_count`, `unknown_zone_default` … are plumbing/run identity, not mechanisms. Either a family row names them or they earn a *declared, justified* `SHARED_CENSUS_EXCLUSIONS` entry — this lane made neither call |
| interchange & neighbours | 6 | seams lane |
| demand & datacenter | 5 | forecast demand lane |
| commitment (incl. archived P2) | 4 | commitment lane; `commitment_enabled` is the **archived P2** flag, so its row should say so rather than imply an available option |

Full per-family field lists: §A below.

---

## 8. Files changed

| file | change |
|---|---|
| `scripts/lib/mech_matrix.py` | +81: `ISO_FIELD_STEMS`, `iso_field_prefixes`, `is_iso_scoped`, `scenarioconfig_field_names`, `absent_shared_fields` — the single recogniser + predicate both halves call |
| `scripts/check_mechanism_matrix.py` | new `absent_shared_ratchet`; three ratchets moved above the validate-only return with a `ratchet_failed` flag feeding both exit paths; R3 line; R4 severity split; `ISO_STEMS`/`scenarioconfig_fields` delegate to the lib; docstring + exit codes rewritten |
| `scripts/mechanism_matrix_gap_sweep.py` | `absent_shared_census`; third baseline block + its own growth check; keeper-bundle carry-forward guard (§3.3); partial-checkout warning; docstring |
| `docs/codebase-site/data/mechanism-matrix-gaps.json` | new `absent_shared` block (185) + rewritten `_comment` describing all three censuses |
| `tests/unit/config/test_mechanism_matrix_shared_ratchet.py` | +9 tests (§2.3) |
| `.github/workflows/ci.yml` | **untouched** — the job passes `--base` and needed no change; no new workflow file was added |
| the matrix tree (`mechanism-matrix.js` + six shards) | **untouched** — no row minted, no cell verdict moved |

Rule 27 `[R-PUSH]`: `check_mechanism_matrix.py` (1,191), `mech_matrix.py` (700) and
`mechanism_matrix_gap_sweep.py` (668) are ≥300 lines (the test file is 275, below the threshold).
No file was rewritten from regenerated content — every change is a local `Edit` — and every push is
the exact on-disk bytes over `git push`, blob-verified by fetch-back (line count + sha256) against
local before the next commit.

---

## A. The 185 admitted fields, by family

**offer curve / heat rate / passthrough — 43**

`cc_committed_hr_mult`, `cc_committed_hr_override`, `cc_econ_hr_mult`, `cc_econ_hr_override`,
`cc_peak_hr_override`, `cc_peak_hr_penalty`, `chp_btm_floor_pct`, `chp_startup_covered`,
`coal_bit_committed_takeorpay`, `coal_bit_dispatchable`, `coal_bit_passthrough_ceil`,
`coal_bit_passthrough_gas_mid`, `coal_bit_passthrough_gas_slope`, `coal_committed_takeorpay_all`,
`coal_lignite_mustrun_override`, `coal_lignite_passthrough_gas_mid`,
`coal_lignite_passthrough_gas_slope`, `coal_prb_contract_passthrough`, `coal_prb_follower_ceil`,
`coal_prb_follower_gas_mid`, `coal_prb_follower_gas_slope`, `coal_prb_mustrun_override`,
`coal_prb_passthrough_ceil`, `coal_prb_passthrough_gas_mid`, `coal_prb_passthrough_gas_slope`,
`coal_sub_passthrough_ceil`, `coal_sub_passthrough_gas_mid`, `coal_sub_passthrough_gas_slope`,
`coal_supply_repricing`, `coal_waste_passthrough_ceil`, `coal_waste_passthrough_floor`,
`coal_waste_passthrough_gas_mid`, `coal_waste_passthrough_gas_slope`,
`coal_waste_passthrough_sigmoid`, `ct_committed_hr_mult`, `ct_drag_ramp_end`, `ct_econ_hr_mult`,
`ct_peak_hr_penalty`, `gas_st_committed_hr_override`, `gas_st_drag_seasonal_path`,
`gas_st_econ_hr_mult`, `gas_st_econ_hr_override`, `gas_st_peak_hr_override`

**retirement & capacity evolution — 37**

`ccs_capture_rate`, `ccs_retrofit_hr_penalty`, `ccs_retrofit_max_gw_per_year`,
`ccs_retrofit_min_remaining_life`, `cod_ramp_enabled`, `control_retrofit_forward`,
`control_retrofit_path`, `entry_price_signal_alpha`, `fixed_om_coal`, `fixed_om_gas_ct`,
`fixed_om_gas_st`, `fixed_om_oil`, `nominal_discount_rate`, `per_tech_wacc_enabled`,
`retirement_aggressiveness`, `retirement_consecutive_years`, `retirement_execution_lag_coal`,
`retirement_execution_lag_gas_cc`, `retirement_execution_lag_gas_cc_ccs`,
`retirement_execution_lag_gas_ct`, `retirement_execution_lag_gas_st`,
`retirement_execution_lag_nuclear`, `retirement_execution_lag_oil`,
`retirement_fom_multiplier_coal`, `retirement_fom_multiplier_gas_cc`,
`retirement_fom_multiplier_gas_cc_ccs`, `retirement_fom_multiplier_gas_ct`,
`retirement_fom_multiplier_gas_st`, `retirement_fom_multiplier_nuclear`,
`retirement_fom_multiplier_oil`, `retirement_years_gas_cc`, `retirement_years_gas_cc_ccs`,
`retirement_years_gas_ct`, `retirement_years_gas_st`, `retirement_years_nuclear`,
`retirement_years_oil`, `vintage_capacity_ramp`

**policy: IRA / CES / carbon / EAC — 32**

`carbon_program_price_path`, `eac_price_gas_cc_ccs`, `eac_price_geothermal`,
`eac_price_offshore_wind`, `eac_price_solar`, `eac_price_storage`, `eac_price_wind`,
`federal_ces_ccs_capture_fraction`, `federal_ces_ci_benchmark_t_per_mwh`, `federal_ces_crediting`,
`federal_ces_eligible_fuels`, `federal_ces_premium_by_year`, `federal_ces_premium_escalation_real`,
`federal_ces_premium_usd_per_mwh`, `federal_ces_storage_eligible`,
`federal_ces_unabated_ci_threshold_t_per_mwh`, `ira_45q_credit_window_years`, `ira_45u_last_year`,
`ira_ccus_45q_last_year`, `ira_h2_45v_last_year`, `ira_itc_solar`, `ira_itc_storage`,
`ira_other_clean_50pct_year`, `ira_other_clean_75pct_year`, `ira_other_clean_last_full_year`,
`ira_other_clean_phaseout_end`, `ira_ptc_wind`, `ira_wind_solar_last_year`, `mass_cap_program`,
`mass_cap_tons`, `nox_price`, `so2_price`

**AS / ORDC / scarcity & deployment floors — 18**

`as_reserve_withholding`, `as_revenue_multiplier`, `commitment_storage_in_merit_floor`,
`commitment_storage_weight`, `ct_deployment_floor_frac`, `ct_deployment_overlay`,
`ct_mustrun_floor_frac`, `must_run_cf`, `ordc_as_plan_mw`, `ordc_lolp_mu_mw`,
`ordc_lolp_params_path`, `ordc_lolp_shift_sigma`, `ordc_lolp_sigma_mw`, `ordc_mcl_mw`,
`ordc_multistep_floor`, `reliability_deployment_floor_frac`, `reliability_deployment_overlay`,
`rtcb_reliability_deployment_mw`

**renewables / storage / new tech — 14**

`egs_available_year`, `egs_pmin_fraction`, `electrolyzer_efficiency_override`, `electrolyzer_type`,
`h2_available_year`, `offshore_wind_available_year`, `offshore_wind_cf_override`,
`offshore_wind_eligible_isos`, `renewable_cf_adjustment`, `renewable_keep_running_value`,
`storage_rte_4hr`, `storage_rte_8hr`, `tech_cost_path`, `tech_cost_percentile`

**weather / derate / outage physics — 10**

`correlated_outage_sigma_scale`, `correlated_outage_t0_c`, `correlated_outage_winterized_year`,
`gt_ambient_derate_slope_cc`, `gt_ambient_derate_slope_ct`, `temp_derate_ref_c`,
`temp_derate_ref_c_coal`, `temp_derate_slope_cc`, `temp_derate_slope_coal`,
`temp_derate_slope_st_gas`

**fuel prices & basis — 8**

`basis_differential_factor`, `coal_price_path`, `crossover_forward_gas_path`, `gas_price_factor`,
`gas_seasonality`, `hindcast_fuel_variant`, `nuclear_fuel_price_override`, `oil_price_path`

**input paths & fleet representation — 8**

`campd_bins_path`, `end_year`, `heat_rate_bin_count`, `plant_emission_rates_path`,
`plant_emission_rates_v2_path`, `plant_registry_path`, `plant_tranche_config_path`,
`unknown_zone_default`

**interchange & neighbours — 6**

`interchange_shape_export_pct`, `interchange_shape_import_pct`, `interchange_shaping`,
`interchange_shaping_export_only`, `neighbor_hr_forward_skill`, `planning_reserve_margin_override`

**demand & datacenter — 5**

`datacenter_load_factor`, `datacenter_percentile`, `demand_growth_path`, `demand_growth_percentile`,
`strict_demand_profile`

**commitment (incl. archived P2) — 4**

`class_commitment_overrides`, `commitment_enabled`, `commitment_irr_hurdle`,
`commitment_screen_coal`

---

## B. Sources

- `docs/handoffs/FINDING-scn-mxr-2026-09-06.md` §1.1–§1.4 (the diagnosis, REPRO A/B/C, R1–R4).
- `scripts/check_mechanism_matrix.py` and `scripts/mechanism_matrix_gap_sweep.py` at `fca3b656`
  (pre-change behaviour, measured by running the `origin/main` blob against a modified tree).
- `.github/workflows/ci.yml`, `mechanism-matrix-guard` job and the workflow's `on:` path filters.
- CLAUDE.md rule 28 `[R-MECH-MATRIX]` duties (b)–(d), rule 24 `[R-REGISTRY]`, rule 25
  `[R-ISO-SCOPE]`, rule 27 `[R-PUSH]`, and the "no per-task workflows / billed runner minutes"
  CI-cost policy.
- `tests/unit/config/test_mechanism_matrix_shared_ratchet.py` (the nyiso-114 `\b`-vs-substring
  lesson this change is built to respect).
