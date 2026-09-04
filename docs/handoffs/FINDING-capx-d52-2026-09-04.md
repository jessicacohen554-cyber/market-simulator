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
| A/B arm | `nyiso-2021-2025-realized-t1h-d52-devintage` | `nyiso-t1h-d52-devintage` | `911371a8cf23d5c3` (pre-declared, matched) | + `--nyiso-requirement-forecast-peak --nyiso-requirement-vintage-factors` | 11.1 min (23:10–23:21 UTC), HEAD `881c11d` |
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

The four new seam fields make the screens' inputs readable for the first time.
The arm's ledger (the seam peak is requirement-independent, so it is the
control's too) against the pre-declaration:

| CY | seam peak (ledger) | PREDECL §1 | ledger LP peak | published peak | entering firm (ledger) | PREDECL | seam requirement OFF (composite on the seam peak) | ledger `adequacy_requirement_mw` OFF (D45's reading) | published |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2021 | 27,954 | — | 30,919 | 32,333 | (base year) | — | 30,182 | 33,382 | 35,604 |
| 2022 (bridge) | 28,295 | — | — | 31,767 | 36,164 | 36,153 (recon.) | 30,550 | — | 34,277 |
| 2023 | **28,641** | 28,640 | 30,206 | 32,049 | **35,163** | 35,163 | **30,922** | 32,612 | 34,559 |
| 2024 | **28,990** | 28,990 | 28,990 | 31,542 | **34,745** | 34,745 | **31,300** | 31,300 | 33,397 |
| 2025 | **29,344** | 29,343 | 31,857 | 31,469 | **35,829** | 35,829 | **31,681** | 34,395 | 34,059 |

Three readings, each now a ledger fact rather than a reconstruction:

1. **The screens price adequacy on the capacity-screen seam's peak** — the
   2024 weather-year load compounded by the demand-growth path (1.22 %/yr)
   to the target year (`_scale_demand`), 27,954 → 29,344 MW across 2021–2025 —
   while the ledger's `peak_demand_mw` / `adequacy_requirement_mw` are
   re-derived from the LP's MEASURED load and coincide with the seam only in
   the weather year (2024). D45 §5.2 read the LP-basis fields, so it had the
   screens' requirement **2.1 GW low in 2023 and 2.4 GW low in 2025 where they
   were 3.6 and 2.4 GW low**, and read 2025 as the one year the model's bar
   was HIGHER than NYSRC's (+336 MW) where the screens' bar was 2,377 MW
   LOWER. The OFF position gap is **+9.4 / +5.2 / +7.3 pts**, not
   +6.5 / +5.2 / −1.6 — every scored year long, the same sign. (D45's P7
   "falsifier tripped" reading is withdrawn by this measurement; the position
   artifact was larger and more uniform than D45 stated.)
2. **The entering-2023 firm is 35,163 MW, not 36,145.** D45's identity firm
   carried the 2021 post-evolution fleet across the un-ledgered 2022 bridge;
   the fleet that entered 2023 had already lost Indian Point 3 (−1,036 MW ICAP)
   in the bridge. 2024 and 2025 were unaffected (no bridge between them).
3. **Under the arm the two requirement fields agree** in every in-table year
   (34,559 / 33,398 / 34,058 on both bases), because the published peak
   replaces both model peaks — the requirement no longer depends on which
   load the model happens to be pricing.

The reconstruction the pre-declaration was built on (class-EFORd thermal +
prior-year pools + hydro / storage / tie) reproduces the ledger's entering firm
to **0 / 0 / 0 MW** in 2023–2025 and to 11 MW in the bridge year; the seam
peaks backed out of the L3 ledger positions were within 1 MW.

## 3. The A/B on the published basis

### 3.1 Requirement and position, before / after

Instrument `docs/handoffs/d52/ab-compare-2026-09-04.py` (stdout + rows
committed beside it); control rows use the arm's seam peak (identical by
construction) with HEAD's composite.

| CY | seam requirement OFF → ON | Δ | published | entering firm | seam position OFF → ON | published | gap OFF → ON (pts) | curve at position OFF → ON ($/kW-yr) | curve at published | real spot | exit budget OFF → ON (MW) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2022 (bridge) | 30,550 → **34,278** | +3,728 | 34,277 | 36,164 | 1.184 → **1.055** | 1.083 | +10.1 → −2.8 | (no 2022/23 curve — flat) | — | 36.60 | 5,614 → 1,886 |
| 2023 | 30,922 → **34,559** | +3,637 | 34,559 | 35,163 | 1.137 → **1.0175** | 1.043 | +9.4 → **−2.6** | $0.00 → **$63.34** | $47.57 | 49.32 | 4,241 → **604** |
| 2024 | 31,300 → **33,398** | +2,097 | 33,397 | 34,745 | 1.110 → **1.0403** | 1.058 | +5.2 → **−1.8** | $5.99 → **$48.04** | $37.38 | 41.64 | 3,445 → **1,347** |
| 2025 | 31,681 → **34,058** | +2,377 | 34,059 | 35,829 | 1.131 → **1.0520** | 1.058 | +7.3 → **−0.6** | $0.00 → **$28.65** | $26.12 | 51.36 | 4,148 → **1,771** |

Readings. (i) **The in-table requirement IS Table D.2's UCAP requirement to
under 1 MW in every year** (P1 HIT), the model's peak dropping out. (ii) **The
position artifact is closed**: the model's census now sits 0.6–2.6 pts SHORT
of the market's published position in every scored year — inside the ±3-point
band D45 §6 fixed (P2 HIT; the 2023 reading, −2.6, is the closest to the
edge, exactly where the pre-declaration put it). (iii) The **exit budget the
admission cap prices** falls 85 % in 2023 (4,241 → 604 MW) and 61 % in 2024 —
the L3 3.5 GW wave was budget-bound at 3,533 MW on the ledger-basis reading
and 4,241 MW on the seam reading; under the arm the same cap admits at most
604 MW in 2023. (iv) The curve's reading at the repaired position moves from
the $0 class to **+28 % / +15 % / −44 %** of the real spot in 2023 / 2024 /
2025 — the 2025 half-price reading is the 2025/26 vintage's net-CONE reset
($50.55) at a published position D45 §8 flagged as a possible SOM transcription
carry-over, and it is the same in both arms (P4's stated caveat).

### 3.2 FC-3 — the rows that moved

**None.** Every FC-3 row of `score.json` is byte-identical to the control's
(P3 HIT): `retire.total_gw` 1.457 (FAIL −14.9 %, the 2026-09-02 target move),
per-fuel 1.036 nuclear / 0.420 gas_ct / 0 elsewhere, `unit_recall_gt300` 1/1,
`false_retire` 0.256 GW (0.176, FAIL), additions wind / solar / gas_cc / gas_ct
/ storage 1.902 / 1.782 / 2.0 / 0.5 / 0.000, every share row, the LOYO folds
(−2023 / −2024 / −2025: recall 1/1; false 0.024 / 0.274 / 0.353 GW), T-R10a/b
PASS, BLK-10 backstop 0.0 GW. The mechanism is structurally real and, at the
curve-OFF default, decides nothing — exactly as pre-declared: the flat $110
capacity term is position-independent, every L2 exit is exogenous, and the
smaller budget capped nothing because nothing failed at $110. `pipeline_events`
is empty in every year of both arms; the backstop did not fire (the 2023
post-exit fleet clears the published bar by +186 MW, the reading the
pre-declaration flagged). Determination **HOLD**, criteria identical to the
control's (FC-3 FAIL on the same band list; FC-7 CAVEAT, DOF ledger absent, as
on the bare key).

The only score.json difference outside `flip_gate_extras.utc` is the
REPORTED-ONLY `co2.model` stream (−0.13 % / +0.04 % / +0.21 % in 2023–2025),
which the mechanism cannot reach (it never enters dispatch): the control was
solved at HEAD `334be8c2` and this arm at `881c11d`, and between them the
NYISO backcast lane's nyiso-188 promotion (`2cc95aa`) re-derived the v2 plant
emission-rate artifact and ramp envelopes the dispatch reads. Input-vintage
drift under a held cache key — the same class D45-R recorded for its L1/L2
HEADs — stated, not absorbed.

### 3.3 The rule-22 LOYO sign test

A zero-parameter mechanism trains on a sign (does arming reduce
|position − published| in both training years?) and is held out on the same
criterion:

| held-out | training pair arms? | held-out \|err\| OFF → ON (pts) | fold |
|---|---|---:|---|
| 2023 | yes (2024, 2025 both improve) | 9.41 → 2.55 | **PASS** |
| 2024 | yes | 5.21 → 1.77 | **PASS** |
| 2025 | yes | 7.29 → 0.60 | **PASS** |

**3/3 PASS, every fold improves** (P4 HIT). No in-sample gain is bought with
held-out degradation anywhere; the identification is the published table.

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
