# FINDING — SCN-WS2a: the endogenous federal CES target row is built, wired to the screens, and probed on NEISO 2026 (escape regime); the G-S3 coupling is relaxed for WS-3b; D-2 stays open

**Lane:** SCN-WS2a, plan §3 WS-2 items 1–2 / §7 "WS-2a" (`docs/handoffs/forecast-scenario-readiness-plan-2026-09.md`).
**Model:** Fable (`claude-fable-5-1`), per the desk's §5.1 assignment. **Branch:** `claude/scn-ws2a-federal-ces-qm512t`
(harness-assigned; the desk's issuance stem was `claude/scn-ws2a-t9xb` — same lane, one branch). **Base:**
`origin/main` `5cc1e7ce` (desk pin `d01ab8b0` is an ancestor; every §2 anchor re-verified by reading at
HEAD before editing — `rows.py:145-202` = `_resolve_clean_region_gen_idx`, `:1346` = the "requires the
RPS region family" docstring line, `runner.py:1195-1229` = `_rps_region_grain_active`, `:2851-2864` the
arming, `:4484-4521` the `prior_results` mapping, `scenarios.py:3084-3157` the `federal_ces_*` block,
`:15584` its backcast guard).
**Commits:** `089eb401` (code + tests), `73e5351f` (docs, G-S6), `6e6449ab` (PRECOMMIT, pushed before the
solves), then the probe registration + this finding, then the mechanism-matrix row as the LAST commit.
**Solves:** exactly two, both named in the PRECOMMIT — NEISO 2026 T0 REF and NEISO 2026 T0 target row.

## 0. Bottom line

1. **The standard is expressible (G-S1 closed).** `federal_ces_target_by_year` (sparse `{year: credited
   share}` knots, `None` = no row) + `federal_ces_acp_usd_per_mwh` build ONE annual federal CES row per
   ISO on the clean-tier row family: `Σ_g credit[g]·P[g,t] + Σ W + Σ S + escape ≥ target(y)·Σ demand`,
   a federal region spanning every load zone, credited by `federal_ces.unit_credit_fractions` (both
   crediting modes unchanged; a CCS column carries 0.95), escaping at the ACP. Its dual is the
   endogenous federal EAC price and reaches entry/retirement through the EXISTING
   `clean_attribute_price_by_fuel → max(EAC, RPS dual, clean dual)` seam — no new consumer.
2. **The coupling is relaxed (G-S3 closed) — WS-3b's precondition.** The clean family no longer requires
   the RPS region grain: it stands alone or beside either RPS grain, its escape slots after whichever
   RPS escapes exist. A region's qualifying spec is a fuel-name tuple OR an `(n_gen,)` credit vector.
   §6 states what a second consumer must supply.
3. **Byte-identity is proven, not asserted.** All six keeper cache keys are identical to `origin/main`
   with the fields present at their `None` defaults (§5); the pinned default keys hold; the MISO state
   family object is returned unchanged (`is`) when no target is set; the full `tests/unit` suite
   passes (with `data/clean` regenerated).
4. **The NEISO 2026 probe lands in the pre-registered ESCAPE regime.** `clean_region_duals[FEDERAL_CES]
   = 50.0` = the ACP exactly; credited share 0.345 of LP demand against the 0.55 illustrative target;
   escape 24.03 TWh; every credited column byte-identical across the pair; objective identity to
   5e-6. **One gate leg is missed by 2e-4 relative and is reported, not smoothed:** CO2 is +3.3 kt
   (+0.020 %) from a solver tie reshuffle confined to non-credited columns (§4.3). The screen may
   kill, never promote; the desk adjudicates whether a tolerance-free "≤" written into a PRECOMMIT is
   a kill at 2e-4 — this lane's reading is in §4.3 and claims nothing beyond it.
5. **D-2 is open.** `{2026: 0.55, 2035: 0.80, 2050: 1.00}` / ACP $50 is the plan's illustrative
   placeholder (§3 WS-2 item 5), used because the owner box was PRESENTED at SCN-DESK r#1 and unsigned.
   It is labelled illustrative in the field docstring, the PRECOMMIT, both sidecars' `d2_status`, and
   here. No value in this lane is a committed campaign level.

## 1. What landed (item 1 — the row)

| where | change |
|---|---|
| `model/lp/rows.py` | `_resolve_clean_region_gen_idx` accepts a per-generator crediting VECTOR as a region's qualifying spec (validated: length = `n_gen`, finite, in [0, 1] — a misaligned vector is a hard error, never a silent mis-credit); new `_validate_credit_vector`, `_resolve_clean_region_gen_coeff`; `_build_rps_region_rows` takes `region_gen_coeff` so a generator column carries its fraction (the tuple-form path keeps the ones vector, byte-identical). The clean family assembly moved OUT of the `rps_region_zone_mask` branch: it appends after whichever RPS family exists, with `acp_k0 = layout.n_rec_acp − K2` (K1 beside the region grain, 1 beside a legacy row with an escape, 0 alone). The former `elif clean_region_zone_mask is not None: raise` is gone. The WS-3b seam is documented at the assembly point. |
| `model/lp/model.py` | the `if not rps_region_on: raise` gate dropped; the ACP price vector is the RPS leg (K1 / 1 / 0 entries) + the clean escapes, so `costs.py` prices the block unchanged. Dual read-back (`_n_clean_rows` tail) already generic. **Outside the desk's named file list** — the charter's own instruction ("relax `rows.py:1346`'s requirement") cannot execute without it, because the model-level assembler enforced the same coupling (`model.py:385`, the docstring at `rows.py:1346` said so). No other lane holds `model/lp/`. Routed here for the desk's record. |
| `model/lp/__init__.py` | `solve_dispatch` docstring for the three `clean_region_*` args. |
| `policy/clean_tiers.py` | `CleanRegionArrays.qualifying_fuels` widened to tuple-or-vector; optional `fuel_credit` map (consumer side only); `append_clean_region` — the ONE composition point; `clean_credit_by_fuel` credits `dual × fraction` for vector-form regions, unchanged for name-tuple regions. |
| `policy/federal_ces.py` | `_interp_knots` (factored from the premium path, semantics identical), `target_for_year` (edge-held), `federal_ces_target_row_active`, `federal_ces_row_fuel_credit` (class-level `tech_credit_fraction` per eligible fuel), `append_federal_ces_region` / `build_federal_ces_region`, `FEDERAL_CES_REGION_LABEL`. |
| `runner.py` | `_clean_region_arrays_for_year` (placed directly after `_rps_region_grain_active`, inside the arming region's spirit): THE single resolver of the family's region list — state rows gated EXACTLY as before (`rps_enabled` ∧ ¬suppressed ∧ region grain ∧ `miso_clean_tier_rows`) + the federal row appended last. Used by the solve-side arming (`:2851-2864` region) and by the `prior_results` mapping (`:4484-4521` region), so a cached year maps its restored duals onto the identical region list. One import line (`:160`) widened. |

## 2. Fields and guards (item 2)

`config/scenarios.py`, inside the `federal_ces_*` block (after `federal_ces_replaces_state_rps`):
`federal_ces_target_by_year: dict[int, float] | None = None`, `federal_ces_acp_usd_per_mwh: float | None = None`.
Registered in `_CACHE_KEY_OPTIONAL_FIELDS` and `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` at `"None"` (shared
fields, very end per HOUSE-3), `TIER_TAGS` 1. `scripts/check_cache_key_registration.py --base origin/main`:
"2 new field(s), all registered; 251 declared defaults all match HEAD".

`__post_init__` guards (directly after the premium's backcast guard, the `~:15584` region):

| guard | why |
|---|---|
| backcast mode + target → refused | rule 13; the premium's own construction ("coerced inert" is implemented as the family's existing hard refusal — a backcast never carries it) |
| target without `federal_ces_enabled` → refused | the master gate is what credits the columns; an unarmed gate would build a row nothing can satisfy |
| target + non-zero exogenous premium (`_usd_per_mwh` ≠ 0, or any non-zero `_by_year` knot) → refused | **rule 19 `[R-ONE-MECH]`**: the row's dual IS the federal EAC price; pricing it exogenously too pays one certificate twice |
| target without a positive ACP → refused | every clean row carries its own escape (FFR-6B §6.3) |
| ACP without a target → refused | rule 24: a dangling price with no row is an unregistered knob |
| target + `federal_ces_storage_eligible` → refused | the row has no discharge column; a storage-crediting row is a separate design |
| target with wind or solar absent from `federal_ces_eligible_fuels` → refused | the family's W/S zone columns always credit 1.0; an ineligible listing would be silently overridden |
| knot values outside [0, 1] / non-year keys / empty mapping → refused | data hygiene |

## 3. Postures (item 3) — documented in `docs/codebase/05-policy.md`, tested in `TestRunnerPostures`

| posture | region list (`_clean_region_arrays_for_year`) | attribute price at the screens |
|---|---|---|
| state rows + federal row (default when both exist — MISO) | `(MN, MI, FEDERAL_CES)` | `max(EAC, RPS dual, max over admitting clean regions)`; a MWh may satisfy a state row AND the federal row (two constraints, one MWh — FFR-6B §6.4) |
| `federal_ces_replaces_state_rps=True` | `(FEDERAL_CES,)` — the flag removes the state RPS **and** state clean rows, never the federal row | federal dual only |
| state only / REF | `(MN, MI)` in MISO, `None` elsewhere | unchanged |

Trivial-first LP tests (1 zone, 24 h, nuclear mc 60 vs gas mc 50, target 0.5): binding dual = 10 =
`mc_clean − mc_dirty`; ACP $5 → dual = 5 and the escape fires; in-merit clean → dual 0; footprint on
the assembled matrix = P columns of credited units at their fractions (CCS 0.95, unabated 0), W/S, one
ACP column and nothing else; beside a legacy RPS row with its own escape (slot 0 RPS, slot 1 federal);
beside a MISO-style region RPS + state clean row the federal build is the state build with one appended
row on the shared columns. 33 tests in `tests/unit/policy/test_federal_ces_target_row.py`; the former
`test_clean_rows_require_rps_region_family` now asserts the standalone row.

## 4. The probe (item 4) — NEISO 2026 T0, REF vs target row

### 4.1 Recipe and cost

Both arms from `run_full_horizon.reference_config("NEISO", 2026, 2026, cmc=False)`; the target arm
re-instantiates `ScenarioConfig` with the SAME explicitly-set fields plus the three federal fields
(never `dataclasses.replace`, which would mark every field explicit and disarm the ISO's
`default_scenario_overrides`). `data/clean` regenerated first (the FF plan §2.4 prerequisite; the
`confirmed-retirements` partition is required in forecast mode).

| arm | run id (forecast namespace, kind `scenario`) | cache key | wall | peak RSS | LP |
|---|---|---|---|---|---|
| REF | `neiso-2026-2026-scn-ws2a-neiso-2026-t0-ref` | `c3592c1adbc8ac17` | 130 s | 3.36 GB | 646 gen cols, build 1.9 s, solve 16.1 s |
| target row | `neiso-2026-2026-scn-ws2a-neiso-2026-t0-target` | `277e96c45549a70e` | 154 s | 3.28 GB | 646 gen cols, build 1.8 s, solve 20.8 s |

Bundles: `results/scenario-probes/scn-ws2a/neiso-2026-t0-{ref,target}/` (summary, run_config,
`config.yaml`, `evolution_2026.json`, `year_2026.parquet`). Sidecars: `frontend/data/hindcast/<run id>.json`.

### 4.2 Phase 0 (zero LP, pre-registered)

Credited potential at full availability 33.40 TWh = 0.314 of 106.53 TWh demand → escape pre-registered,
dual = ACP. **Phase-0 limitation, stated:** the census used `build_base_fleet`, which does not carry the
non-thermal hydro that `build_dispatch_fleet` adds (6.97 TWh dispatched in the solve), so the census
undercounted credited potential; the solve's credited share is 0.345, still 20.5 pp short of 0.55. The
expectation's direction was unaffected.

### 4.3 STOP gate, leg by leg

| leg | measured | verdict |
|---|---|---|
| binds or escapes | dual 50.0 > 0; credited 40.37 TWh < 0.55 × 117.09 = 64.40 TWh → escape 24.03 TWh | **escapes** ✓ |
| dual = ACP iff escape | `clean_region_duals = [50.0]` = ACP to solver precision; escape fired | ✓ |
| credited share ≥ target otherwise | n/a (escape regime) | — |
| CO2 falls / not up | REF 16.3081 Mt → 16.3114 Mt, **+3.3 kt (+0.020 %)** | **literal "≤" missed by 2e-4; see below** |
| footprint = eligible columns only | credited columns byte-identical across the pair (nuclear 26,482,159.0 MWh, hydro 6,973,518.0, wind 3,664,192.5, solar 3,252,042.9 in both; dump 0, slack 0); the row's non-zeros are the credited P columns, W/S, one ACP (unit test on the assembled matrix) | ✓ |
| no invariant PASS → FAIL | I1–I14 PASS in both arms | ✓ |

**The CO2 leg.** The pair's dispatch deltas are `gas_cc −155.1 MWh` (moved between CC bins),
`biomass +60.2 MWh`, and `−94.9 MWh` of total generation (storage cycling losses) — all in columns the
row does not touch — while every credited column is identical to 0.1 MWh. The objective identity
`objective(target) − objective(REF) = $1,201,482,404` vs `ACP × escape = $1,201,458,786` holds to
$23,618 = 5.0e-6 of the objective. A row that is satisfied entirely by its escape column adds a constant
to the objective and changes no other column's optimal value; the observed deltas are a different
optimal-within-tolerance vertex (a 5.7 M-column LP re-pivoted with one more row), i.e. the
marginal-tie reshuffle class the repo's warm-start neutrality standard already names. The PRECOMMIT
wrote "CO2 falls or is unchanged, never rises" without a tolerance and pre-registered "SMALL or ZERO"
magnitude; the measured +0.020 % is inside any solver-meaningful tolerance and outside the row's
footprint, but it is a literal miss of an inequality this lane wrote, so it is recorded as such. The
lane's reading: the structural identity the gate exists to test — the mechanism does what its own
arithmetic says, in the columns it claims, and nothing else — holds; the desk decides whether the
tolerance-free wording kills. Either way nothing is promoted (a screen never promotes).

### 4.4 What 2026 cannot show

- **A binding (non-escape) year.** NEISO's credited potential is far below 0.55, so 2026 only exercises
  the escape leg. The binding regime (`0 < dual < ACP`, credited share ≥ target) is proven on the
  trivial-first LP and needs, on the real fleet, either a D-2 schedule near the current share or the
  T1-F horizon where entry moves the credited columns.
- **The deployment response.** The dual is delivered to `prior_results.clean_attribute_price_by_fuel`
  and would enter the 2027 screens' `max()`; a 1-year T0 has no evolution step. Not claimed.
- **Additivity with the state RPS.** NEISO's own RPS row escapes at its $50 ACP in BOTH arms
  (`rps_shadow_price = 50.0`), so the screens' `max()` reads 50 with or without the federal row in
  2026; the federal dual would be the binding attribute price only in a year the state row clears.

## 5. Byte-identity — the deliverable

Every keeper's cache key rebuilt from its committed `run_config.json` at HEAD equals `origin/main`
`5cc1e7ce` (computed in the SAME checkout via `git stash`, because a scratch tree at another path
folds checkout-relative artifact paths differently and is not a valid comparison):

| ISO | keeper | key |
|---|---|---|
| ERCOT | `2026-09-05-ercot248-two-config-keeper` | `cd0e3973702af5ca` |
| CAISO | `2026-09-05-caiso-251-b1-nomargin` | `d638578c933b062a` |
| PJM | `2026-08-15-pjm-162-inputclock` | `77dd72dd1666e3b1` |
| MISO | `2026-09-05-miso-217-intermphys` | `2a12a416679c5db2` |
| NYISO | `2026-09-05-nyiso-192-astoria-panel` | `0ac15036eacc3d22` |
| NEISO | `2026-08-17-neiso-99-joint-p1` | `799b359ab8aa5ced` |

Plus: `tests/regression/test_persisted_identity.py` (pinned default forecast + backcast keys) 14/14;
`test_miso_state_family_is_untouched_when_off` (`is`); `test_beside_state_family_appends_only`
(shared rows/bounds identical on the shared columns); `test_arming_clean_family_only_appends_rows` and
`test_default_path_never_reaches_the_resolver` unchanged and passing; `tests/unit` full suite green
after `data/clean` regeneration.

## 6. Downstream contract — what SCN-WS3b must supply

The voluntary-demand row attaches as additional clean regions at ONE point,
`policy.clean_tiers.append_clean_region` (the runner composes through
`_clean_region_arrays_for_year`; add the new leg there, after the federal row or before it — region
order is the only thing that fixes dual order). Per region it supplies:

1. an `(n_zones,)` bool eligibility mask (where its attribute may be generated);
2. an `(n_zones,)` float obligation fraction (its share × that zone's annual demand — the RHS);
3. an escape price ($/MWh; the layout allocates one ACP column per region — mandatory);
4. a qualifying spec: a fuel-name tuple (indicator coefficients) OR an `(n_gen,)` credit vector aligned
   with `fleet_arrays` (the row builder hard-errors on a length mismatch);
5. for a vector-form region, a `{fuel: fraction}` map (`fuel_credit`) so `clean_credit_by_fuel` can
   deliver its dual to the fuel-keyed screens — or `None` if its dual must NOT reach the screens
   (then also filter it out of `clean_attribute_price_by_fuel` at the runner: today every region's dual
   is mapped).

Its duals come back as its slice of `DispatchResult.clean_region_duals` in region order. The netting
question (D-6 — does voluntary demand count toward the standard?) is a coefficient/RHS choice inside
this same family (one MWh satisfying both rows is the "counts toward" default; "additional" means the
voluntary row's credited MWh are subtracted from the federal row's LHS, which the vector form
expresses). Nothing else in the LP moves.

## 7. Files touched outside the named regions — routed to SCN-DESK

- `src/market_sim/model/lp/model.py` (the coupling gate + ACP vector) and `model/lp/__init__.py`
  (docstring): required by the charter's own instruction; no other lane holds `model/lp/`.
- `runner.py:160` import widening; `_clean_region_arrays_for_year` placed immediately after
  `_rps_region_grain_active` (line ~1230), adjacent to the `:1195-1229` region.
- `scenarios.py`: the two cache-key registry appends (`_CACHE_KEY_OPTIONAL_FIELDS` end,
  `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` end) and the `TIER_TAGS` lines — the registration the charter
  demands; one-line appends, outside the `federal_ces_*` block and the D34 guard.
- NOT touched: `results/export.py`, `matrix.py`, `configs/*`, `constants.py`, `datacenter.py`,
  `policy/carbon.py`, `cap_and_trade.py`, `interchange/spec.py`, `results/cache.py`, the `assemble_mc`
  region, the D34 guard, `scripts/forecast_verdict.py`, `program-status.json`,
  `scripts/run_full_horizon.py` (the probe driver lives in the session scratchpad and reuses
  `reference_config` + `solve_and_summarize` unchanged).
- Deferred, not done: `scripts/generate_parameter_registry.py --check` regenerates
  `frontend/data/parameters.json` + `docs/parameter-citations.md` for the two fields but also pulls in
  other lanes' pending rows (miso-217, capx D50/D57, nuclear CF vintages); the regen was reverted and
  the registry refresh left to its owner cadence (CI does not run it). Both fields carry their
  citation in the field docstring (D-2 open; illustrative).
- Pre-existing red, not this lane's: `scripts/ci_refactor_guards.py` (`tests/scoring/test_bench_stamp_ast.py`
  references `scripts/fake_builder.py` — present at `origin/main`), `scripts/check_forecast_parity.py`
  (ERCOT `ercot_storage_as_soc_reserve`, NYISO `nyiso_seam_deliverability_envelope`).

## 8. Scorecard (plan §5.1 / ledger §3, "CES target" column)

| criterion | before | after |
|---|---|---|
| 1 expressible in committed config | no | **yes** (illustrative level; D-2 open) |
| 2 reaches dispatch + deployment | no | **yes** — dispatch by the row, deployment through the existing `max()` seam (deployment leg not exercised by a T0) |
| 3 paired probe right-signed, per ISO | no | **NEISO only, escape regime** (dual = ACP; CO2 leg at +2e-4, §4.3) |
| 4 backcast byte-identity | — | **yes** (six keeper keys) |
| 5 matrix duty | — | **stamped** (row + six cells, last commit) |
| 6 emissions grain | — | scalar only (WS-0) |
| 7 registered probes on dashboard | — | **NEISO T0 pair** (kind `scenario`) |
