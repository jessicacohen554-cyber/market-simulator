# PREREG miso-206 — bound the WIND-AVAILABILITY object in the object's own hours, zero-solve (2026-09-04)

**Session:** miso-206, branch `claude/miso-wind-availability-backcast-yr4i67`.
**Keeper at open: `2026-09-03-miso-202-unitclip`** (bundle
`results/calibration/miso202_unitclip_B`) — determination **NOT-YET** on
`{C3a-2025 −12.3845}` alone, C3c the single ledgered caveat, C6 attested
(ledger 41/2, n_residual 2). `HEAD == origin/main` at `b168260e`; `git diff
HEAD origin/main -- src/ scripts/run_calibration*.py` is EMPTY — one code state.

**This is a ZERO-SOLVE phase 0.** Rule 22 `[R-HOLDOUT]` — 2023/2024/2025 only;
MISO holds no `complete`/`final` marker and the locked-test freeze is active.
Committed artifacts + the production loaders only. Nothing here enters a solve.

---

## 0. DISCLOSURE — what was measured BEFORE this PREREG was written

The charter's instrument note requires the measured-wind transform to be
asserted against production BEFORE any comparison is read. Establishing that
pre-condition produced two numbers that are, strictly, part of deliverable (b),
and they are disclosed here rather than presented later as predictions:

1. **The production wind bound is an IDENTITY on the delivered series.** Rebuilding
   the keeper's `ScenarioConfig` from `run_config.json` (`mode="backcast"`) and
   calling the production `load_renewable_profiles("MISO", year, …)`, the ISO
   aggregate wind bound `Σ_z cf·cap` equals `delivered_930(t) / (1 − r)` with
   `r = 0.048947` (the Potomac 2023+2024 firm-row mean;
   `_miso_wind_reference_curtailment_rate`) at **max|diff| = 0.0000 MW in all
   8,760 hours of all three years**. Solar's bound equals delivered at 0.0000.
2. **The keeper's P1 wind sits ON that bound in every hour** (bound − P1 max
   0.002 MW; **0 hours** with P1 more than 1 MW below the bound; endogenous
   curtailment **0.0 MWh** in every year). So `P1_wind(t) = 1.051466 ×
   delivered_930(t)` **in every hour of every year**, and the annual excess is
   **+4.720 / +5.057 / +5.096 TWh** (2023/2024/2025) against the committed
   bench's `e930.wind` 91.715 / 98.251 / 98.938 — the standing "~+5 TWh/yr"
   figure, confirmed to the third decimal, and it is **the curtailment gross-up
   and nothing else**.

Consequence, stated before the object-hour numbers are read: because the
model's wind is a **constant multiple** of the measured series, (i) the excess in
ANY hour set is `0.048947 × model wind` there, and (ii) **every percentile rank
of measured wind equals the model's** (a uniform scale preserves rank). The
predictions in §3 are therefore arithmetically constrained by §0, and are
written as such. What §0 does NOT settle — and what this session actually
adjudicates — is §3 P6/P7 (the bound against the marginal stack, and the
mechanism claim) and §4 (the record repairs).

---

## 1. The matrix check (rule 28(a)) — which cells this touches

Read in full from `docs/codebase-site/data/mechanism-matrix/MISO.js` and the base
`mechanism-matrix.js`:

| cell (MISO) | verdict | what it is | bearing on this object |
|---|---|---|---|
| `ercot_wind_zone_shape` | **K** | per-zone MERRA-2 wind SHAPE (MISO's builder, unconditional in `_WIND_ZONE_SHAPE_ISOS`) | `_redistribute_preserving_total` preserves the ISO aggregate **exactly in every hour** — it cannot move the object's aggregate wind by construction. Not touched. |
| `vre_avg_cf_level` | `.` | `RENEWABLE_AVG_CF` normalisation of the EIA-930 *distribution* profile | n/a in MISO backcasts: MISO takes the measured hourly `MISO hourly` series, never the distribution. Not touched. |
| `negative_renewable_offers`, `wind_ptc_vintage_offers` | `.` | offer-side renewable constructs | offer side, not availability. Not touched. |
| `wtx_curtailment_driver`, `wtx_curtail_unpooled`, `solar_deliverability` | `.` | ERCOT / CAISO curtailment mechanisms | ISO-scoped elsewhere (rule 25). Not touched. |
| `wefor_statistical_stack`, `wefor_residual`, `summer_wefor_share_override` | K / I / K | **thermal forced-outage** family (WEFOR = weighted-equivalent forced outage rate) | the charter's "`wefor_multiplier` 1.0 in MISO vs 0.7 in five ISOs" (doc §3 line 178) is an OUTAGE-family fact, not a wind one; the unit-outage family is EXHAUSTED as a C3a route per the charter and is not touched here. |

**The construction actually at issue — the reference-rate curtailment gross-up
(`_forecast_uncurtailed_cf`, provenance `forecast_uncurtailed`, an UNGATED data
construction with no `ScenarioConfig` field) — has NO ROW in the matrix.** Rule
28(c) says a mechanism missing from the matrix is an unregistered tuning channel
in spirit. This session therefore mints its base row
(`vre_reference_rate_curtailment_grossup`, cat `vre`) plus a cell line in every
shard — the one deliberately non-parallel edit rule 28(c) licenses — with MISO's
cell **K** (it is live in every MISO keeper since the construction's inception)
carrying this session's evidence, and every other ISO's cell `.` (ERCOT/CAISO
backcast years are HSL-covered `measured_potential`; NYISO/NEISO/PJM are not in
`_UNCURTAILED_FALLBACK_ISOS`). No cell adjudicated R/I/G is re-tested.

---

## 2. Instrument, and the reproduction PRE-CONDITIONS (any failure stops the session)

* **N-1 (clock).** The measured MISO wind is rebuilt INDEPENDENTLY from the raw
  `data/raw/eia-930/EIA930_BALANCE_<year>_{Jan_Jun,Jul_Dec}.parquet` rows
  (`Balancing Authority == "MISO"`, `"Net Generation (MW) from Wind without
  Integrated Battery Storage"` + `"… with Integrated Battery Storage"` summed
  NaN-aware, exactly `extend_eia930_hourly_from_balance._NEW_SUM_MAP`), filtered
  to the `Data Date` year, sorted by `UTC Time at End of Hour`, local Feb 29
  dropped, and asserted against the production loader
  `load_eia_hourly_renewable_gen("MISO", year)["wind"]` at **max|diff| = 0.0 on
  8,760/8,760 hours** in every year (the miso-204 N-3 discipline). Same for
  solar. A non-zero difference anywhere means the transform is not production's
  and NOTHING downstream is read.
* **N-2 (bound ≡ P1).** §0's identity is re-asserted inside the probe: bound
  vs `delivered/(1−r)` at 0.0000 MW; P1 within 0.01 MW of the bound in every
  hour; 0 curtailed hours.
* **N-3 (object set).** OBJ = top 1 % of Jun–Jul hours of
  `actual_lmp_hourly_zonal_MISO.parquet` (hub `INDIANA.HUB`, col `rt`) on the
  model's fixed-CST non-leap 8760 — miso-205's construction verbatim — asserted
  to reproduce miso-205's thresholds **121.43 / 159.01 / 373.02** and its 15
  2025 stamps exactly.
* Drivers (load, net load) from the keeper's `hourly/system_<year>.parquet` P1
  rows; class dispatch from `class_hourly_<year>.parquet` P1; both on the model
  clock. The model price is reported BOTH as zone-mean and load-weighted, as
  miso-205 does.
* Margins for the bound are **read** from
  `_miso203_summer_peak_anchor_phase0.json::g_d_reserve_binding`
  (`margin_broad_mw_min_scarce` 42,735.7 / 38,374.8 / 30,533.2;
  `idle_armed_classes_mw_mean_scarce` 15,788.8 / 11,751.6 / 5,620.9) and the
  miso-202 A-3 ceiling from `_miso202_c3a_2025_anatomy.json::a3_ceiling`
  (`jun_jul_price_max` 183.22, unserved 0.0, ORDC shortfall 3 h) — never
  re-derived (the miso-205 TRAP-5 discipline).

---

## 3. Predictions — each driver's SIGN against its OWN normal population, plus the magnitude

Decision rules are fixed here. "Excess" = model P1 wind − measured EIA-930
wind, MW, mean over the hour set.

| # | prediction | direction / reference | conf. | decision rule |
|---|---|---|---:|---|
| **P1** | OBJ-hour excess = 0.048947 × OBJ model wind: **262 / 285 / 251 MW** (2023/2024/2025), and in the top-15 gross-load hours **360 / 282 / 282 MW**, and across all Jun–Jul **298 / 417 / 390 MW** | *identity, ±1 MW* | 0.97 | a deviation > 2 MW anywhere means N-2 silently failed → STOP |
| **P2** | Measured wind's percentile ranks in the OBJ hours are IDENTICAL to the model's: Jun–Jul **p45.5 / p34.5 / p32.4**, hour-of-day-matched **p54.5 / p36.1 / p36.5** | *identity, ±0.1 pp* | 0.97 | a difference > 0.5 pp → the identity is broken somewhere in the pipeline → STOP |
| **P3** | **SIGN of measured wind vs its own hour-of-day-matched Jun–Jul normal:** 2024 and 2025 **BELOW** (deficit, p < 40); 2023 **ORDINARY** (p in [45, 60]) — the 2023 object is NOT a low-wind set | vs own h-o-d population | 0.85 | rule as written per year |
| **P4** | **Solar control:** measured 930 solar equals model P1 solar within 1 MW in ≥ 14 of 15 OBJ hours in every year; its ranks are identical to miso-205's (2025 h-o-d matched **p48.1**, ORDINARY). If the instrument reads solar as anomalous, the instrument is wrong | identity + miso-205 | 0.95 | mismatch > 1 MW in ≥ 2 hours, or 2025 h-o-d solar outside [43, 53] → STOP |
| **P5** | Annual excess **+4.720 / +5.057 / +5.096 TWh**, ratio model/930 = **1.05147** in each year — §0, restated | disclosed | — | — |
| **P6 — THE BOUND (pre-committed).** Removing ALL of the phantom headroom in the OBJ hours takes out **262 / 285 / 251 MW**. Against miso-203 G-D's own margins that is **0.6 / 0.7 / 0.8 %** of the broad reserve margin and **1.7 / 2.4 / 4.5 %** of the armed-class idle. **Even removing ALL model wind in the OBJ hours** (5,359 / 5,822 / 5,120 MW — the total-removal ceiling) is **12.5 / 15.2 / 16.8 %** of the broad margin — still under the 25 % licensing line every year. | vs miso-203's 25 % line | 0.95 | **REFUSE iff excess/broad_margin_min < 0.25 in every year** (miso-203 G-D's rule, verbatim). Report the armed-idle limb too, but the broad limb decides, as it did at miso-203. |
| **P7 — THE MECHANISM RULE beside the magnitude rule.** The OBJ-hour excess as a share of the object's net-load elevation over the Jun–Jul mean (10,050 / 18,590 / 23,922 MW) is **2.6 / 1.5 / 1.0 %**; the wind DEFICIT in those hours (719 / 2,690 / 2,848 MW, miso-205) is a MEASURED fact, not a model error — the model's wind is low there because MISO's wind was low there. | own normal | 0.9 | the object is a wind-availability object only if excess/net-load-elevation ≥ 0.10 in 2025; predicted 0.010 → NOT an availability object |
| **P8 — against interest.** The one place a 5 % uniform headroom COULD price-set is an hour where the LP curtails wind (price ≤ wind MC). Count of Jun–Jul hours with P1 wind > 1 MW below bound: **0** in every year (from §0). If it is > 0 in any OBJ hour the headroom is live there and P6 must be re-bounded on the curtailed MW, not the excess | model | 0.95 | stated, no gate |
| **P9 — the form defect, named not chartered.** The gross-up puts a constant 4.9 % of headroom in EVERY hour, including scarce hours where real curtailment is ~0 (curtailment is a low-price / congested-hour phenomenon). In the object's hours the headroom is therefore phantom supply of the P1 size; a price- or congestion-conditioned rate is the correct FORM (rule 14 reconciled-data clause). But by P6 the form cannot move C3a-2025. Predicted: NAMED as a defect in the record, NOT chartered, no field | — | 0.9 | — |
| **P10** | Verdict **REFUSED on the bound** — DEAD like the ambient derate; nothing armed, no LP, no field, no keeper move | — | 0.95 | the P6 rule |

**The pre-committed verdict logic, in words:** if P6's rule fires (it is
expected to, by three orders of magnitude on the excess and by 8–13 pp even at
total removal), the wind-availability object is **REFUSED in this session** and
the cell minted in §1 records it. There is **no branch in which a solve is
spent**: the total-removal ceiling is an upper bound no admissible mechanism
can reach, so no arm could pass the miso-203 licensing line.

---

## 4. Second deliverable — repair of the two wrong-clock committed records

`_miso202_c3a_2025_anatomy.json` (blocks a2/a4) and
`_miso203_scarce_hour_identity.json` build their hourly actual as the eight-hub
equal-weighted mean on the raw EST hour-ending index (miso-204 §6). Repair =
route `hub_hourly_rt` in both generator probes through the committed
`actual_lmp_hourly_zonal_MISO.parquet` (hub `INDIANA.HUB`, col `rt`, the C3a
comparator) and regenerate. The anatomy keeps its own basis (keeper
`miso201_stbasis_B`, on which it was made); the identity keeps `miso202_unitclip_B`.
Pre-repair values of every hour-matched statistic are preserved inside each
record under a `pre_repair_defective_clock` key so the history stays legible.

Decision rules:

* **R-0** the annual/monthly blocks (a0/a1/a3 of the anatomy;
  `jun_jul_peaks_for_reference` and `driver_contrast.top_gross_load_hours` of
  the identity) are **byte-identical** before and after — the charter's "bench
  aggregates are FINE" claim, tested rather than assumed.
* **R-1** the repaired thresholds are **121.43 / 159.01 / 373.02** and the
  repaired 2025 stamps are miso-205's 15, exactly.
* **R-2** the repaired identity's `obj_hours_REPAIRED`-equivalent drivers
  reproduce miso-205's `g_a_g_b_driver_contrast.obj_hours_REPAIRED` to ±0.5 in
  every driver, every year (same keeper, same construction ⇒ must be exact).
* **R-3** the repaired anatomy a4 2025 import delta lands within **±150 MW** of
  miso-205's `+3,673.3` (different keeper basis, miso-201 vs miso-202, so not
  exact; a larger gap means the unitclip delta moved the seam in those hours and
  is reported as such, not hidden).
* **R-4** the repaired a2 2025 Jun–Jul `top1pct_of_actual_hours.share_of_mean_gap`
  stays ≥ 0.95 (the tail verdict is robust to the clock — miso-204 §6.4 says so;
  this tests it on the anatomy's own instrument).

---

## 5. Traps, each with its pre-committed counter-measurement

| trap | counter-measurement |
|---|---|
| **T1 clock** — a BALANCE-file rebuild that is one hour off | N-1 at max|diff| = 0.0 on every hour; also report the lag-scan r at k ∈ {−1, 0, +1} (must be 1.000000 at k = 0) |
| **T2 the 2025 extract has 8,759 rows** | identify the missing hour (predicted: the LAST hour, local 2025-12-31 HE24, so the filled frame pads ONE trailing NaN by ffill) and assert it is outside Jun–Jul |
| **T3 "with Integrated Battery Storage"** | assert the MISO column is all-NaN/zero in every year (measured: 2025 H1 sum 0.0) so "without" alone equals the production sum |
| **T4 leap-year 2024** | the production frame drops local Feb 29; assert N-1/N-2 hold on the Jun–Jul 2024 hours specifically |
| **T5 aggregate stability is not hour-set correctness** (miso-205 §9.7) | every comparison is hour-of-day-matched or stamp-level; the Jun–Jul aggregate is reported only as context |
| **T6 solar as the instrument's control** | P4 |
| **T7 a bound argued on the mean when the object is a max** | report the per-hour excess for all 15 stamps, and the bound at the single largest hour (2025-07-28 HE18) too |
| **T8 the identity makes the object-hour numbers trivially "right"** | §0 disclosed; the adjudication is P6/P7 (bound + mechanism), not P1/P2 |

---

## 6. Stop rule

Nothing is armed and no LP is spent unless P6's rule FAILS to fire (excess ≥
25 % of the broad margin in some year) **and** P7 reads the object as an
availability object (share ≥ 0.10) — both against prediction. Even then the
branch is a re-charter, not a solve: the form (P9) has no field, no D-4
window and no forward rate identification yet.

**Rule duties.** Rule 15: zero-solve, nothing registered. Rule 28(b): the new
base row + MISO cell stamped in-session; §5.4 queue stamp. Rule 28(c): base row
+ a cell in all six shards (no `ScenarioConfig` field added). Rule 25: no other
ISO's keeper/status file touched. Rule 27: two existing probes (< 300 lines
each) edited locally with the Edit tool; no ≥300-line file rewritten. Rule 13:
every input is a committed artifact or a production loader; nothing enters a
solve.
