# PRECOMMIT — SCN-WS2a: the endogenous federal CES target row, NEISO 2026 T0 (REF vs target row)

**Lane:** SCN-WS2a (`docs/handoffs/forecast-scenario-readiness-plan-2026-09.md` §3 WS-2 items 1–2,
§7 "WS-2a"). **Branch:** `claude/scn-ws2a-federal-ces-qm512t` (harness-assigned; the desk stem was
`claude/scn-ws2a-t9xb`). **Base:** `origin/main` `5cc1e7ce` (desk pin `d01ab8b0` is an ancestor).
**Rule 29 `[R-SCREEN]`:** written and pushed BEFORE the only solves of this lane. Zero LP spent before
this document.

## 1. What is being screened

The new LP row family member landed in `089eb401` (code) — one annual **federal CES target row**
per ISO on the clean-tier region machinery (`model/lp/rows.py`), spanning every load zone, credited by
`policy.federal_ces.unit_credit_fractions` (clean_capture: nuclear/wind/solar/hydro/geothermal/
offshore wind/hydrogen 1.0, `gas_cc_ccs` 0.95, unabated fossil and imports 0), escaping at the ACP.
Config: `federal_ces_enabled=True`, `federal_ces_target_by_year={2026: 0.55, 2035: 0.80, 2050: 1.00}`,
`federal_ces_acp_usd_per_mwh=50.0`; premium fields at 0 (rule 19 — the row and an exogenous premium
are mutually exclusive). **The schedule and the ACP are ILLUSTRATIVE** — owner box D-2 (plan §6) is
OPEN as of 2026-09-05; nothing here is a committed campaign level.

## 2. Screen year, arm, control

- **Screen year: 2026** (a T0 — one solve year, inside the FF plan §2.1b window cap). Named here
  before any solve. It is the year the mechanism's own footprint is measured (phase 0 below); it is
  also the only year a T0 can touch, and the charter names it.
- **Arm:** NEISO 2026, `run_full_horizon.reference_config("NEISO", 2026, 2026, cmc=False)` re-instantiated
  with the SAME explicitly-set fields plus the three federal CES fields (driver: the scratch
  `t0_neiso.py`; it never uses `dataclasses.replace`, which would mark every field explicit and
  disarm the ISO's `default_scenario_overrides`).
- **Control (REF):** the same `reference_config`, unchanged (`federal_ces_enabled=False`). The charter
  names both T0 arms as deliverables ("both T0 arms registered"), so REF is charter-authorized; it is
  not a HEAD-drift control (rule 29(b) form 4 is not engaged — no backcast keeper is the comparator
  here). Both arms solve serially in this session (rule 12: never two years in parallel; here one
  year each).

## 3. Phase 0 — zero-LP footprint census (NEISO 2026, the runner's own fleet/demand loaders)

Run at HEAD `73e5351f` with the runner's own loaders (`load_or_synthesize_bins` → `build_base_fleet`
→ `generators_to_fleet_arrays`, `load_demand` → `_scale_demand`, `load_renewable_profiles`; scratch
`phase0_neiso.py`), `announced_fossil_exits=[]` (no 2026 fossil-dated exit changes a credited column):

| quantity | value |
|---|---|
| annual demand 2026 (weather year 2024, scaled) | 106.53 TWh |
| wind + solar potential (CF × capacity, 5 zones) | 6.92 TWh |
| credited generator potential at full availability — nuclear (3 units) | 26.48 TWh |
| credited potential total | **33.40 TWh = 0.314 of demand** |
| credited fuels present in the NEISO 2026 fleet | nuclear only (no hydro / geothermal / offshore-wind / CCS / hydrogen generator column exists in this posture; HQ imports are `import` fuel, credit 0) |
| eligible columns | P for 3 nuclear units + W/S for 5 zones + 1 ACP column |
| fleet | 490 generator columns |

The credited potential is an UPPER bound (full availability, no curtailment) and is 24 pp short of
the 0.55 target, so the escape must carry ≥ 0.236 × 106.53 TWh ≈ 25.1 TWh in 2026.

## 4. Pre-registered expectation (sign, magnitude, footprint)

- **Binds-or-escapes.** With credited potential ≤ 0.314 of annual demand against a 0.55 target,
  the pre-registered expectation is ****ESCAPE FIRES**: the row is certificate-short by ≥ 24 pp of demand, the escape column carries the gap, and the dual is pinned at the ACP, $50/MWh. Sign of the dispatch response: the row moves every credited MWh it can — nuclear is already baseload in REF (in-merit), so the expected dispatch/CO2 delta vs REF is SMALL or ZERO (nuclear at ~full availability in both arms; the 2026 arm has no deployment step); the row's entire visible effect in 2026 is the dual = ACP and the escape volume. A near-zero CO2 delta therefore does NOT fail gate 3 (≤ holds) and is the pre-registered magnitude**.
- **Dual.** If the escape fires: `clean_region_duals[FEDERAL_CES] == 50.0` (the ACP) to solver
  tolerance. If the row binds without escape: `0 < dual < 50`, equal to the marginal
  clean-minus-dirty offer gap in the marginal hour set. If slack: dual 0 (then the arm is INERT in
  2026 and the screen reports it as such — an inert screen year is the one clause-(a) exemption).
- **Credited share.** `Σ credit×gen / Σ demand ≥ 0.55` when the row does not escape; `< 0.55` iff
  the escape fires (the escape MWh closes the gap exactly).
- **CO2.** Falls or is unchanged vs REF, never rises: the row can only move energy from
  zero-credit (fossil) columns to credited columns or into the escape. Magnitude bounded above by the
  fossil energy displaced = max(0, 0.55·demand − REF credited MWh) × the displaced fleet's CO2 rate.
- **Footprint = eligible columns only.** The row's non-zeros are exactly: P columns of generators
  with credit > 0 (3 units: nuclear), the W and S columns of all 5 zones, and the one
  ACP column; nothing else in the LP moves except through the energy balance. Prices: the energy
  duals may move in hours where the row re-orders the merit stack; no reserve, storage or
  transmission row coefficient changes.
- **Deployment (2026 has no evolution step in a 1-year T0):** none expected; the dual reaches
  `prior_results.clean_attribute_price_by_fuel` and would enter the 2027 screens' `max()` — not
  exercised by this T0 and not claimed.

## 5. STOP gate (structural identity — may kill, never promote; never a residual)

The arm PASSES the screen iff ALL hold on the 2026 solve:

1. The row **binds or escapes** (dual > 0) — OR is measured inert (dual 0, credited share ≥ 0.55 in
   REF too), which is reported, not scored.
2. `dual == ACP (50.0)` **iff** the escape fires (credited share < target); otherwise `dual < ACP`
   and credited share ≥ target (to 1e-6 relative).
3. `co2_mt(arm) ≤ co2_mt(REF)`.
4. Row footprint = the eligible columns above (checked on the assembled matrix by the unit test
   `test_footprint_is_the_eligible_columns_at_their_fractions` and, on the solved model, by the
   sidecar's per-region dual + credited-share arithmetic).
5. No I1–I14 invariant that PASSES in REF FAILS in the arm.

A failure on any item KILLS the arm (the FINDING reports it and the row is not claimed
"expressible"). Passing promotes nothing — it moves the §5.1 scorecard's "CES target" column to
"yes" on criteria 1/2/4/5 and the probe half of 3, exactly what the charter asks; campaign levels
remain D-2's.

## 6. Byte-identity (deliverable, proven before this document)

Every backcast keeper cache key rebuilt from its committed `run_config.json` at HEAD `089eb401`
equals origin/main `5cc1e7ce` (both fields present at their `None` defaults, registered in
`_CACHE_KEY_OPTIONAL_FIELDS` / `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS`):

| ISO | keeper | bundle | cache_key (HEAD = main) |
|---|---|---|---|
| ERCOT | 2026-09-05-ercot248-two-config-keeper | ercot248_two_config_keeper | `cd0e3973702af5ca` |
| CAISO | 2026-09-05-caiso-251-b1-nomargin | caiso251_arm_nomargin | `d638578c933b062a` |
| PJM | 2026-08-15-pjm-162-inputclock | pjm_debugb_inputclock_A | `77dd72dd1666e3b1` |
| MISO | 2026-09-05-miso-217-intermphys | miso217_intermphys_B | `2a12a416679c5db2` |
| NYISO | 2026-09-05-nyiso-192-astoria-panel | nyiso192_astoria_panel | `0ac15036eacc3d22` |
| NEISO | 2026-08-17-neiso-99-joint-p1 | neiso99_joint_B | `799b359ab8aa5ced` |

(ERCOT/PJM/NEISO run_configs carry retired field names — `renewable_buildout_pace`,
`caiso_bidir_intertie`, … — dropped before reconstruction on BOTH sides identically.) The pinned
default forecast and backcast keys (`tests/regression/test_persisted_identity.py`) are unchanged.
The MISO clean-tier family object is returned unchanged (`is`) by the federal append when no target
is set (`test_miso_state_family_is_untouched_when_off`), and the assembled matrix with the federal
row is the state build with one appended row (`test_beside_state_family_appends_only`).

## 7. Budget

FF plan §2.4: NEISO ≈ 85 s median per solve year, ≈ 3.9 GB RSS. Two one-year arms ≈ 5 min LP
total. Wall/RSS are recorded per arm in the FINDING.
