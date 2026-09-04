# FINDING — capx D52: the NYISO adequacy-requirement devintage (D45 §5.2.4 items 1–2) — BUILT default-off, zero DOF; the A/B closes the position artifact (seam positions +9.4 / +5.2 / +7.3 → −2.6 / −1.8 / −0.6 pts vs published, LOYO 3/3, FC-3 byte-identical at the curve-OFF default); the conditional curve-ON probe RAN (§6 condition met) and reads P9 (c) YES / (a) NO / (b) NO — the 2023 wave L3 fired at $0 is gone, the over-fire moves to the 2025/26 curve vintage (1.8 GW of gas_st at $28.65 where the market paid $51); neither default moves

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
| conditional probe | `nyiso-2021-2025-realized-t1h-d52-curveon` | `nyiso-t1h-d52-curveon` | `589f031432b6dc7d` (pre-declared, matched) | the arm + `--capacity-market-clearing` | **RUN** (§6 condition met): 11.6 min (23:22–23:34 UTC), HEAD `881c11d` |

The control is the D45-R L2 itself: the bare recipe keys `91686abe7a744a88` at
this branch's HEAD (measured through the harness path, validated on two known
answers — PREDECL §7), so the A/B is like-for-like at one solve-path posture with
no control replay. The NYISO backcast keeper at this HEAD is
`2026-09-04-nyiso-188-combined` (the owner's backcast lane promoted 188 after the
charter's "187 at issuance"; the shard is authoritative and untouched here).

## 0. Verdict (one paragraph)

**The requirement repair is real, zero-DOF and does exactly what D45 said it
would — and a little more than D45 measured.** With both gates on, the NYCA
requirement the three capacity screens consume IS NYSRC Table D.2's published
UCAP requirement (34,559 / 33,398 / 34,058 MW in 2023 / 2024 / 2025, to under
1 MW; the model's peak drops out), and the model's entering position moves from
**+9.4 / +5.2 / +7.3 points LONG** of the market's published NYCA position to
**−2.6 / −1.8 / −0.6 points** — inside the ±3-point band D45 §6 fixed, in every
scored year, with the rule-22 LOYO sign test 3/3 PASS. The OFF gap was larger
and more uniform than D45 §5.2 stated because D45 read the ledger's LP-basis
requirement: the four new seam ledger fields show the screens price adequacy on
the capacity-screen seam's growth-scaled 2024-weather peak (28,641 / 28,990 /
29,344 MW), 2.1–3.6 GW of requirement below the published bar in EVERY year,
2025 included (§2). At the shipped curve-OFF default the A/B is
**byte-identical on every FC-3 row** (pre-declared: the flat $110 term is
position-independent and every exit is exogenous), so the repair costs nothing
and decides nothing until a curve is consulted. **The conditional probe ran and
answers D45's question on the pre-stated conditions: P9 (c) YES, (a) NO,
(b) NO — one of three, so the curve stays OFF — but the reason has changed.**
The 2023 screen that L3 collapsed at $0 (3.5 GW of downstate steam) now pays
$63.34/kW-yr and fails nothing; 2024 pays $48.04 and fails nothing; the
over-fire moves to the 2025 screen, where the 2025/26 curve vintage (net-CONE
reset to $50.55) pays $28.65 at position 1.052 — a gas_st capacity leg of $26.6
against a $35 bar — and **1,801 MW of gas_st is decided and executed in 2025**
(total 3.257 GW, +90 %; false-retire 0.631), sized by the 2025 admission budget,
exactly as PREDECL P5 said. What remains is not the position: (i) the 2025/26
vintage pays half the real $51.36 spot at the published position (a curve /
records object, the same in both arms) and (ii) the NYCA-wide representation
pays downstate steam the NYCA price where Zone J clears at $141/kW-yr (D45
§5.2.4 item 3, the locality half — routed, not built). **Recommendations (§8):
arm the two requirement gates as NYISO's forecast default on the LOYO record —
an owner decision this lane does not make; keep the curve OFF.**

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

**The §6 condition — repaired positions within ±3 points of the published NYCA
positions in every scored year — was MET (−2.6 / −1.8 / −0.6), so the probe ran**
(the arm + `--capacity-market-clearing`, one field from the A/B; key
`589f031432b6dc7d` pre-declared and matched; 11.6 min).

| | A/B (curve OFF) | **probe (curve ON)** | L3 (D45-R curve ON, unrepaired) |
|---|---:|---:|---:|
| entering position 2023 / 2024 / 2025 (ledger `capacity_reserve_position`) | (seam) 1.0175 / 1.0403 / 1.0520 | **1.0175 / 1.0403 / 1.0520** | 1.137 / 1.006 / 1.028 |
| capacity leg the screen saw, $/kW-yr (gas_st at 0.93) | $110 flat (×0.93 = $102) | **$63.34 / $48.04 / $28.65** (×0.93 = $58.9 / $44.7 / $26.6) | $0 / $68.62 / $38.63 |
| screen events 2023 | none | **none** — every L3-failed row passes ($58.9 + ~$0 vs $35; gas_cc $60.2 + $10.7 vs $30; gas_ct $59.5 + $1.1 vs $21) | 3,496 MW gas_st decided + executed; 16.3 GW capped |
| screen events 2024 | none | **none** | none |
| screen events 2025 | none | **gas_st 17 units / 1,801 MW decided + executed** (nr $26.8 incl. the $26.6 leg vs $35.0); capped behind them: gas_st 7,567 MW, gas_cc 652 MW ($27.2 + $1.4 vs $30) | none |
| `retire.total_gw` | 1.457 (−14.9 %) | **3.257 (+90.4 %, FAIL)** | 4.953 (+189 %) |
| gas_st economic | 0 | **1.801 GW (2025)** | 3.496 GW (2023) |
| `false_retire` | 0.256 GW (0.176) | **2.057 GW (0.631)** | 3.752 GW (0.758) |
| `unit_recall_gt300` | 1/1 | 1/1 | 1/1 |
| additions gas_cc / gas_ct / storage | 2.0 / 0.5 / 0.000 | **1.0 / 0.0 / 0.000** (the 2022-decided unit lands 2024; no 2024 decision at a $45.6k/MW-yr term; no 2023 gas_ct at $60.2k) | 1.0 / 0.0 / 0.000 |
| LOYO −2023 / −2024 / −2025 false (raw) | 0.024 / 0.274 / 0.353 | 1.825 / 2.075 / 0.353 (FAIL ×3) | FAIL / FAIL |
| T-R10a / b | PASS / PASS | **FAIL / FAIL** (first mover gas_st) | — |
| position after 2025 | 1.070 (36,439 / 34,058) | **1.007** (34,289 / 34,058) | 0.951 |
| determination | HOLD | HOLD | HOLD |

**D45 P9, graded verbatim (all three required; "any two of three is not
enough"):** (a) `retire.total_gw` within ±10 % — **NO** (+90 %); (b)
`false_retire` in band — **NO** (0.631); (c) entering positions within ±3 points
of the published NYCA positions in every scored year — **YES** (−2.6 / −1.8 /
−0.6). One of three ⇒ the curve-ON default is NOT recommended (§8).

**The curve-attributable delta (probe − A/B), the honest reading:** retire
+1.80 GW (all 2025 gas_st), false-retire +1.80 GW, gas_cc entry −1.0 GW, gas_ct
entry −0.5 GW; NOTHING in 2023–2024. The D28 latent flip is no longer a
position artifact — the position is inside the market's band in every year —
it is a **2025/26 curve-vintage and locality artifact**: at the published 2025
position (1.058) the HEAD curve pays $26.12 where the real NYCA spot was $51.36
(the 2025 SOM margin row is itself flagged as a possible transcription
carry-over, D45 §8), and a downstate steam unit whose real ICAP revenue is the
Zone J price ($141/kW-yr at $11.76/kW-month) is paid the NYCA $28.65. At the
REAL 2025 NYCA spot the gas_st leg would be 0.93 × 51.36 = $47.8 > $35 and the
cohort would pass; at the NYC locality price it passes by 4×. The gas_st that
fail are the class §5.2.3 says the NYCA-wide representation underpays by 3–4× —
which is why the route is item 3, not a curve re-shape.

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

- **Registered** `nyiso-2021-2025-realized-t1h-d52-devintage` → **`nyiso-t1h-d52-devintage`**
  and `nyiso-2021-2025-realized-t1h-d52-curveon` → **`nyiso-t1h-d52-curveon`**
  (`VERDICT_MAP` rows; `register_forecast_run.py --bundle` each; canonical
  sidecars `frontend/data/hindcast/<run_id>.json`; reports
  `docs/hindcast-reports/<run_id>-2026-09-04.md`; `ff-verdicts.json` gains the
  two keys, purely additive, `provenance.session = capx-D52`). Scored
  `score_capacity_hindcast.py --bundle` + `--flip-gate-extras`, then
  `forecast_verdict.py --tier t1h --hindcast-score … --run-config …` (the
  D45-R / D48 sequence). The bare `nyiso-t1h` is untouched; the board
  (`program-status.json`) untouched (suffixed probes move no gate row).
- **Committed slim set** per bundle (the D45-R / D48 template, gitignore
  carve-out `nyiso-2021-2025-realized-t1h-d52-*`): `meta.json`,
  `run_config.json`, `forecast_verdict.json`, the five `evolution_<year>.json`
  ledgers (now carrying the four seam fields), `score.json`, the two
  `screen_signal_diag_*.npz` dumps.
- **Matrix:** two base rows (`nyiso_requirement_forecast_peak`,
  `nyiso_requirement_vintage_factors`, mode F, cat capacity) + a cell in every
  shard; the NYISO cells stamped `fc: "O"` with the measured A/B and probe
  readings — OPEN on a measured record (the owner arms or declines), neither
  rejected (structurally correct, reproduces its rows) nor inert (the
  requirement and position moved; FC-3 did not, by construction) nor a keeper.
  Off-queue by charter (the D45 §9 successor lane). `check_mechanism_matrix.py
  --base origin/main` green.

## 7. The pre-declaration, graded at full magnitude

**Cache keys: 2 pre-declared for solving, 2 realized exactly** (`911371a8cf23d5c3`,
`589f031432b6dc7d`); the control key held (`91686abe7a744a88`); the pinned
default key unmoved. Every posture as declared; every guard green.

| # | prediction | conf | outcome |
|---|---|---|---|
| P1 | arm requirement 35,604 / (bridge) / 34,559 / 33,397 / 34,059 to < 1 MW, independent of the model peak; Δ vs the seam OFF +3,637 / +2,097 / +2,377 | HIGH | **HIT** — 35,603.4 / 34,277.6 (bridge, also now recorded) / 34,559.1 / 33,397.9 / 34,058.3; both the LP-basis and seam-basis ledger fields agree in-table; Δ +3,637 / +2,098 / +2,377 |
| P2 | entering seam positions 1.0175 / 1.0404 / 1.0520, −2.5 / −1.8 / −0.6 pts ⇒ §6 MET ⇒ probe runs; 2023 within 0.5 pt of the edge | MED | **HIT** — 1.017473 / 1.040324 / 1.051998; −2.55 / −1.77 / −0.60; condition met; probe run |
| P3 | FC-3 byte-identical to L2; backstop 0; the 2023 post-exit fleet clears the bar by +186 MW | HIGH | **HIT** — every FC-3 row identical to the decimal; `pipeline_events` empty in every year; BLK-10 0.0 GW; 34,745 − 34,559 = +186 |
| P4 | LOYO 3/3 PASS (9.4 → 2.5 / 5.2 → 1.8 / 7.3 → 0.6); curve at position $63.3 / $48.0 / $28.7; 2025 at half the real spot in both arms | MED | **HIT** — 9.41 → 2.55 / 5.21 → 1.77 / 7.29 → 0.60; $63.34 / $48.04 / $28.65; 2025 $28.65 vs $51.36 |
| P5 | probe: no exits in 2023 (leg $58.9 vs $35) or 2024 ($44.7); a 2025 gas_st failure at $26.6 + ~$0.4 vs $35, decided_year 2024 / executed 2025, ≈ 1.8–1.9 GW budget-bound; total ≈ 3.3 GW (+90 %), false 0.55–0.60; gas entry below L2 (gas_cc ≤ 1.0, gas_ct 0–0.5), storage 0.000; P9 (a) NO / (b) NO / (c) YES | MED | **HIT on every limb but one magnitude** — 2023 / 2024 none; 2025 gas_st 17 units / 1,801 MW decided + executed (nr $26.8 incl. the leg, i.e. ~$0.2 of energy margin); total 3.257 (+90.4 %); gas_cc 1.0 / gas_ct 0.0 / storage 0.000; (a) NO (b) NO (c) YES. **MISS on false-retire magnitude:** 0.631 vs the 0.55–0.60 band (the 1.8 GW gas_st counts entirely as false — the actual has no gas_st exit — so false = 2.057 / 3.257) |
| P6 | seam peak 28,640 / 28,990 / 29,343 (±30); entering firm 35,163 / 34,745 / 35,829 (±60); OFF requirement 30,922 / 31,300 / 31,682 and positions 1.137 / 1.110 / 1.131 recorded as the control prediction | HIGH / MED | **HIT** — 28,640.6 / 28,990.0 / 29,343.6; 35,162.9 / 34,744.6 / 35,829.2 (the class-EFORd reconstruction reproduces the ledger to 0 MW); the control's seam values are the arm's seam peak × the composite (the control predates the fields) |
| P7 | both fields registered at `"False"`; bare key holds ⇒ no control replay; pinned default unmoved; other ISOs inert | HIGH | **HIT** |
| P8 | ~12 min / ~3.5 GB per leg, sequential by design | — | **HIT** — 11.1 / 11.6 min |

**Tally: 8 gradable items — 7 HIT, 1 SPLIT (P5: every mechanism limb hit, the
false-retire magnitude 0.631 vs 0.55–0.60).** The one miss is arithmetic the
pre-declaration should have done — a gas_st exit is 100 % false against a
target with no gas_st — not a model surprise. **Two D45 readings are corrected
on the ledger (§2):** the 2025 "other way by 0.4 GW" (the P7 falsifier D45-R
recorded as tripped) was the ledger's LP-peak requirement, and the 2023
identity firm was the 2021 fleet; both are records misses of the kind D45-R's
own §7 named ("built from the preserved record rather than from the artifacts
at HEAD"), now closed at the source by the seam fields.

## 8. The two arming recommendations (owner decides; this lane recommends on pre-stated conditions)

**(1) The requirement devintage — `nyiso_requirement_forecast_peak` +
`nyiso_requirement_vintage_factors` as NYISO's forecast default? RECOMMEND:
ARM BOTH.** On the pre-stated record: (i) structure (rules 1 / 13 / 14) — a
published per-capability-year market-design parameter on the published
forecast peak replaces a single mixed vintage on the model's own peak, the
exact construction NYSRC sets the NYCA requirement on, the NEISO Net ICR / PJM
FPR shape; zero free parameters, vintage-gated, regenerates forward from the
Gold Book + the adopted IRM; (ii) the rule-22 LOYO is 3/3 PASS with every fold
improving and no fleet contamination (unlike D40's NEISO record, the A/B fleet
is identical to the control's in every year, so every fold is clean); (iii)
the shipped-default cost is exactly zero — FC-3 byte-identical, the golden's
2026+ requirement moves +0.24 % (the hold-last pair vs the composite). Against:
nothing measured; the only open item is the rule-23 question of whether the
composite itself should also move to the 2025-26 derate (§5 item 3), which the
arm makes moot in-table and a +0.24 % question beyond it. The owner arms via
the two defaults (`scenarios.py`) plus the matrix / T1-F re-measure the
director's batched process requires; this lane flips nothing.

**(2) Consult the published ICAP demand curve at NYISO's default (the FF-3D
flip)? RECOMMEND: DO NOT ARM — for a new, pre-stated reason.** D45's P9
condition, re-affirmed verbatim, reads (c) YES / (a) NO / (b) NO on the
repaired posture; one of three is not enough, and the lane says so. But the
adjudication has moved: **the position artifact D45 §6 named is closed** —
the 2023 screen that fired 3.5 GW at $0 now pays $63/kW-yr and fires nothing —
and what fires instead is the 2025 screen at the 2025/26 vintage's $28.65,
where the market paid $51.36 and Zone J paid $141. That is (i) a **curve /
records object** (the 2025/26 net-CONE reset and a flagged 2025 SOM row: at the
published position the curve pays half the real spot, in both arms) and (ii)
the **locality half** (D45 §5.2.4 item 3): the gas_st that fail are downstate
steam paid the NYCA price. Neither is a curve-shape re-litigation (the D45 §9
line binds) and neither is this lane's to build. **Route:** item 3 (the NYCA /
NYC / LI / G-J locality requirement as the NYISO instance of
`capacity_deliverability_limits`) first; the 2025/26 vintage / 2025 SOM
transcription check as a records task; then re-run THIS probe against the SAME
P9 (a)/(b)/(c). The curve question re-opens on that record, not before.

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
  the remote tree after each push (14 files after the build push; the
  ff-verdicts snapshot, both shards' NYISO file, both sidecars, both
  run_config files and this finding after the results pushes).
- **Rule 28.** Two base rows + twelve cells in the same PR; NYISO cells
  re-stamped with the measured verdict; `check_mechanism_matrix.py` green.
  Off-queue by charter (the D45 §9 successor lane), stated.
- **Rule 15.** Every leg registered through `register_forecast_run.py` in the
  session that produced it, FORECAST namespace only.
- **Backcast blast radius: not triggered.** The fields are coerced to default
  in a plain backcast and dropped from the hash at their default; the pinned
  default key and every backcast key are unmoved (measured).
- **Environment cost, stated.** Cold container: `uv sync` + NYISO hydration +
  `regenerate_clean.py` (54 datatypes, 41 min wall; `emissions-unit-annual`
  SIGKILLed once under memory contention with a concurrent test lane and
  re-run solo afterwards); each NYISO T1-H leg 11–12 min, run one at a time.
