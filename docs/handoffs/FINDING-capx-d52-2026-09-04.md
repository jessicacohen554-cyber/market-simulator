# FINDING — capx D52: the NYISO adequacy-requirement devintage (D45 §5.2.4 items 1–2) — [TO FILL: one-line verdict]

**Lane:** capx D52 — NYISO's per-ISO repair lane, the successor D45's §9 close-out
names. Branch `claude/capx-d52-nyiso-devintage-sl3rj2`, fresh off `origin/main`
(`a35c9f9`; no rebase was needed — main did not move during the session). The
pre-declaration `PREDECL-capx-d52-2026-09-04.md` was committed BEFORE any code
(`08c02e9`), its §7 keys appended after the build and BEFORE any solve
(`1b9c24d`, pushed), and is graded at full magnitude in §7, misses included.
**NOTHING ARMS**: both fields ship DEFAULT-OFF, every leg registers SUFFIXED, the
bare `nyiso-t1h` verdict key is untouched, no keeper / shard / marker, the backcast
namespace untouched. Both arming recommendations return to the owner (§8).

| leg | run id | registers as | key | posture | wall / peak RAM |
|---|---|---|---:|---|---|
| control | `nyiso-2021-2025-realized-t1h-d45r` (D45-R L2, not re-solved) | bare `nyiso-t1h` | `91686abe7a744a88` | shipped (curve OFF, flat $110) | 12.2 min (D45-R) |
| A/B arm | `nyiso-2021-2025-realized-t1h-d52-devintage` | `nyiso-t1h-d52-devintage` | `911371a8cf23d5c3` | + `--nyiso-requirement-forecast-peak --nyiso-requirement-vintage-factors` | [TO FILL] |
| conditional probe | `nyiso-2021-2025-realized-t1h-d52-curveon` | `nyiso-t1h-d52-curveon` | `589f031432b6dc7d` | the arm + `--capacity-market-clearing` | [TO FILL / NOT RUN] |

The control is the D45-R L2 itself: the bare recipe keys `91686abe7a744a88` at
this branch's HEAD (measured through the harness path, validated on two known
answers — PREDECL §7), so the A/B is like-for-like at one solve-path posture with
no control replay. The NYISO backcast keeper at this HEAD is
`2026-09-04-nyiso-188-combined` (the owner's backcast lane promoted 188 after the
charter's "187 at issuance"; the shard is authoritative and untouched here).

## 0. Verdict (one paragraph)

[TO FILL]

## 1. What landed (default-off, zero DOF)

| surface | change |
|---|---|
| `config/capacity_market.py` | `NYCA_ICAP_FORECAST_PEAK_MW_BY_ISO`, `NYCA_IRM_ADOPTED_BY_ISO`, `NYCA_ICAP_UCAP_TRANSLATION_BY_ISO` — NYSRC 2026-27 IRM Study Appendices Table D.2 (report p.68 / PDF p.86; sha256 `714aeeb9…`, re-fetched and hash-matched), capability years 2020/21–2025/26: forecast peak 32,296 / 32,333 / 31,767 / 32,049 / 31,542 / 31,469 MW; adopted IRM 18.9 / 20.7 / 19.6 / 20.0 / 22.0 / 24.4 %; derate 0.0830 / 0.0877 / 0.0978 / 0.1014 / 0.1321 / 0.1300. Reconciled row-for-row to the committed csv and to the table's own identity `peak × (1 + IRM) × (1 − derate) = UCAP requirement` (< 1 MW) by test. The shipped composite ratio (`1 − 0.1321`) is untouched. |
| `model/capacity_evolution/retirements.py` | `nyiso_requirement_forecast_peak_armed` / `nyiso_requirement_vintage_factors_armed` (the gate predicates — flag AND registry entry, rule 25), `resolve_nyiso_requirement_peak_mw` (published peak in-table, else the caller's own float object — no hold-last of a MW peak), `resolve_nyiso_requirement_factor` (adopted IRM × (1 − derate) in-table; hold-last as the last pair beyond; None pre-table / in-gap); consumed by `gross_adequacy_requirement_mw` AFTER the FPR paths and BEFORE the composite, so `resolve_adequacy_requirement_mw` — the one requirement the CR-1 position, the reliability floor / admission cap and the reserve-margin backstop share (rule 19) — moves as one. Unarmed: byte-identical (the same peak object into the same composite expression). |
| `config/scenarios.py` | `nyiso_requirement_forecast_peak: bool = False`, `nyiso_requirement_vintage_factors: bool = False` (end of the field list); registered in `_CACHE_KEY_OPTIONAL_FIELDS` / `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` at `"False"` and `TIER_TAGS` at 1; coerced to the dataclass default in a plain backcast, kept in a hindcast. Pinned default key `4c6b03ae098b6e3e` unmoved; the bare `nyiso-t1h` key unmoved. |
| `runner.py` | FOUR additive, decision-neutral, cache-key-neutral ledger fields on every year (bridge included): `screen_peak_demand_mw`, `screen_adequacy_requirement_mw`, `screen_entering_firm_mw`, `screen_reserve_position` — the capacity-screen SEAM peak, the requirement resolved on it, the entering accredited firm the screens price, and their ratio on the ISO's curve convention, written whether or not the clearing gate is on. Nothing reads them back. |
| `scripts/run_capacity_hindcast.py` | `--nyiso-requirement-forecast-peak` / `--nyiso-requirement-vintage-factors` (BooleanOptionalAction, `None` inherits the default), threaded into the config and the run record as `FromConfig` (the record reads the SOLVED gates). |
| `scripts/register_forecast_run.py` | `VERDICT_MAP` rows for the two suffixed D52 keys. |
| data | 19 rows appended to `data/raw/capacity-market/demand-curve/nyiso/nyiso.csv` (`icap_market_forecast_peak`, `irm_adopted`, `ucap_requirement` × 6 capability years; `icap_ucap_translation_factor` 2025-2026); README block; schema + `scripts/lib/capacity_market_demand_curve` metric vocabulary + the rendered data dictionary line. `regenerate_clean.py capacity-market-demand-curve` green. |
| rule 28 | two base rows (mode F, cat capacity) + a cell in all six shards (NYISO `fc: O`; the five others `.` with the rule-25 reason each). `check_mechanism_matrix.py --base origin/main` green after `--fix-anchors` (digits only). `check_cache_key_registration.py --base origin/main`: ok, 2 new fields registered. `generate_parameter_registry.py --check`: OK (20 new entries). |
| tests | `tests/unit/model/test_capacity.py::TestNyisoRequirementDevintage` (12): csv/table-identity reconciliation, default-off byte-identity (incl. the same-object peak), both-armed = published UCAP requirement independent of the model peak, single-gate decomposition with the D45 item-2 sign, pre-table / `None` fall-through, no hold-last on the peak, hold-last pair on the factors (a ratio that scales with peak; +0.24 % over the composite), gap never bridged, the information gate (a later row never read earlier), the pre-declared seam-position sign, other-ISO inertness, backcast coercion / hindcast keep / four distinct keys. The R5a test (`TestNyisoIcapUcapTranslation`) now pins the registry's documented 2024-25 vintage explicitly instead of `max(csv)`. |

**Choices the charter left open, decided and recorded.**

- **Two gates, not one** (the D48 convention over D40's): items 1 and 2 have
  different signs in 2024 and the owner may want either alone; the LOYO
  decomposes by construction. BOTH on reproduces the published requirement.
- **The forecast peak has no hold-last; the factor pair does.** Beyond the
  table the model's own peak IS the forward load forecast, so holding a
  published MW peak would fail the rule-13 forward test; the factor pair is a
  ratio and holds like PJM's FPR / NEISO's Net-ICR ratio (card C-A).
- **The composite stays pinned to the 2024-25 derate.** The 2025-26 factor
  (0.1300) is now on disk; re-deriving the SHIPPED
  `PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO["NYISO"]` onto it is a
  rule-23 re-derivation on a source-data update that would move every NYISO
  forecast default (+0.24 % of requirement) — an owner decision, routed (§9),
  not smuggled in under a default-off lane.
- **Information gate as a label construction, not an invented date table.**
  The row of capability year Y/Y+1 is read in model year Y only; the IRM
  adoption dates are on file in the csv citations (2020-12-04 … 2024-12-06);
  the 2020/21 date is not in-repo and was not invented.

## 2. A correction to D45 §5.2, confirmed by the arm's ledger

[TO FILL — the seam fields: predicted 28,640 / 28,990 / 29,343 seam peak;
30,922 / 31,300 / 31,682 seam requirement OFF; entering firm 35,163 / 34,745 /
35,829; what the arm recorded]

## 3. The A/B on the published basis

### 3.1 Requirement and position, before / after

[TO FILL]

### 3.2 FC-3 — the rows that moved

[TO FILL]

### 3.3 The rule-22 LOYO sign test

[TO FILL]

## 4. The conditional probe

[TO FILL — the §6 condition's fate; if run, the P9 (a)/(b)/(c) grade verbatim
and the curve-attributable delta vs the A/B]

## 5. Explicitly NOT built, routed

1. **The locality half** (D45 §5.2.4 item 3): NYC / LI / G-J LCRs + import
   limits as the NYISO instance of `capacity_deliverability_limits`. The
   published rows are committed; the crosswalk exists. Not this lane's.
2. **The base-year 1.2 GW supply gap** (item 4): hydro accreditation / SCR
   counting — a D2-class intake.
3. **The shipped composite's derate vintage** (rule 23): see §1.
4. **The ledger records defect** the seam fields expose: in every hindcast year
   that is not the weather year, `peak_demand_mw` / `adequacy_requirement_mw`
   (LP-peak basis) are NOT the quantities the screens consumed. The new fields
   make both readable; whether the LP-basis fields should be renamed or the
   forecast-verdict I7/I12 rows re-based on the seam is the director's call.

## 6. Matrix (rule 28) and registration

[TO FILL]

## 7. The pre-declaration, graded at full magnitude

[TO FILL — P1 … P8]

## 8. The two arming recommendations (owner decides; this lane recommends on pre-stated conditions)

[TO FILL]

## 9. Governance attestation

- **Rule 13 / 14 / 21 / 23.** Every value is a published NYSRC market-design
  parameter reconciled to its committed source row by test; the SOM margins
  and cleared quantities entered nothing; nothing was sized by a residual; the
  sign was pre-stated by D45 and re-stated here before the solve.
- **Rule 22.** T1-H solves {2021, 2023, 2024, 2025} with 2022 bridged; scored
  2023–2025 only; no out-of-training year solved, scored or registered; the
  holdout freeze untouched; the LOYO sign test scored BEFORE any default moves
  (and no default moves).
- **Rule 24.** Both gates are `ScenarioConfig` fields threaded to
  `run_config.json` and the hindcast run record; the three registries are
  cited constants.
- **Rule 25.** NYISO-only by construction (one-ISO registries, entry-requiring
  predicates); measured inert on PJM / MISO / NEISO / ERCOT / CAISO with the
  flags armed (test).
- **Rule 27.** Fable session; every file edited locally with the Edit tool and
  the exact on-disk bytes pushed; every ≥300-line file blob-verified against
  the remote tree after each push (14 files after the build push; [TO FILL]
  after the results push).
- **Rule 28.** Two base rows + twelve cells in the same PR; NYISO cells
  re-stamped with the measured verdict; `check_mechanism_matrix.py` green.
  Off-queue by charter (the D45 §9 successor lane), stated.
- **Rule 15.** Every leg registered through `register_forecast_run.py` in the
  session that produced it, FORECAST namespace only.
- **Backcast blast radius: not triggered.** The fields are coerced to default
  in a plain backcast and dropped from the hash at their default; the pinned
  default key and every backcast key are unmoved (measured).
- **Environment cost, stated.** Cold container: `uv sync` + NYISO hydration +
  `regenerate_clean.py` (54 datatypes, ~[TO FILL] min; `emissions-unit-annual`
  SIGKILLed once under memory contention and re-run solo).
