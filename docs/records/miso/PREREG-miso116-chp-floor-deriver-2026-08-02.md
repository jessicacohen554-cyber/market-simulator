# PRE-REGISTRATION miso-116 — does the CHP floor's own deriver explain the `CC_CHP` overnight deficit?

**Written and committed BEFORE any number was computed.** Session miso-116,
2026-08-02, branch `claude/miso-116-chp-floor-phase0-llt4t9`, off `origin/main`
at `0d49cc4`. Phase 0 is a **no-LP deriver audit** — the miso-107 discipline. No
solve is spent unless this document's decision rule charters one.

## 1. The question

miso-115 §3 relocated MISO's ~3 GW overnight gas hole to `CC_CHP`: measured
`R = CAMPD / model = 2.156 / 2.246 / 2.555` at h1–3, kill-clean (K1 83.2 %,
K5 97 %, 8.7 % multi-class), a deficit of 2,086 / 2,274 / 2,446 MW. §4 read the
class as "priced 23 % too cheap while dispatching half the measured volume —
the signature of a class whose output is set by a **floor**, not by economics",
with D-2 forcing 19.5 % of `CC_CHP`, 35.6 % of `CT_CHP`, 5.5 % of `ST_CHP`.

This session audits the floor's **own construction**, in this order:

1. **What does `chp_steam` / `chp_export_floor_measured` identify** — a
   per-**prime-mover** steam-host export obligation, or one pooled CHP number
   apportioned by something else?
2. **Does that construction explain** a CC-cogen floor set at under half of
   metered output while CT-cogen is over-forced?
3. **Is any term model-dependent** (price, dispatch, residual)? If yes that is a
   rule 13 `[R-MEASURED]` defect *independent of the residual*.
4. **Does the `CC_CHP` heat rate carry the same defect** — and is "a too-cheap
   class that still under-runs is held down by a floor" the right reading?

## 2. Sources — committed artifacts only, no LP

* Keeper bundle `results/calibration/miso109_hy_level_B` —
  `hourly/class_hourly_<year>.parquet` (`pass == "P1"`), `run_config.json`,
  `legitimacy_diagnostics.json`.
* `data/raw/_processed-legacy/thermal_tranches_MISO.csv` (the floor artifact),
  `chp_power_only_heat_rates_MISO.csv` (the measured-HR artifact).
* `data/raw/campd-unit-level/{STATE}_{YEAR}.parquet` via the repo's own
  `campd.states_for_iso` / `_hour_index_8760` / `plant_hourly_net`.
* The repo's own fleet build (`load_fleet_from_csv`) and the repo's own
  `chp.chp_btm_pct` / `chp.chp_pmin_cf` — **rule 24 `[R-REGISTRY]`: no hand
  map, no re-derived constant.**

## 3. Pre-registered estimators — definitions fixed before the numbers

### A. Apportionment structure (Q1)

* **A1 key grain.** For every MISO plant carrying ≥ 1 model CHP bin, record the
  `(plant, class)` pairs the artifact supplies a floor row for, and the
  `(plant, class)` pairs the *consumer* (`fleet.assembly`) actually applies a
  floor to. **Reported statistic:** the number of MISO plants carrying ≥ 2 model
  CHP classes, and for those, whether every class receives the *same* CF.
* **A2 prime-mover resolution of the BTM share.** The distinct values of
  `chp_btm_pct(plant, class, "MISO")` per model class, capacity-weighted.
  **Reported statistic:** whether the share varies *within* a plant across
  prime movers.
* **A3 floor provenance.** The `status` distribution (`ok` / `eia923_cf` /
  `chp_floor_only` / absent) over MISO CHP `(plant, class)` pairs, by class
  capacity.

### B. Basis test (Q2, Q4) — the decisive estimator

miso-115's `R` divides **CAMPD `grossLoad`** (whole-plant output) by the model's
`class_hourly.mw`. This test recomputes it on a **basis-matched** denominator,
per plant, using the repo's own measured objects and nothing else:

```
meas_grid_p(h) = campd_net_p(h) × (1 − chp_btm_pct(p, class, "MISO") / 100)
R_basis        = Σ_p mean_{h∈trough} meas_grid_p(h) ÷ model_class_trough_mw
```

* `campd_net_p` is the repo's own `campd.plant_hourly_net` (measured parasitic
  factors) — the identical function `derive_thermal_tranches` uses.
* `R_btm_only` (gross × (1 − btm), parasitic **not** applied) is reported as the
  **upper bound**, since the parasitic factor is < 1 and can only move `R_basis`
  down.
* Plant set, class→CAMPD-family map, trough hours, 8760 calendar and the keeper
  bundle are **taken verbatim from miso-115's probe** so the corrected number is
  comparable to the number it corrects (see K3/K4).

### C. Ceiling test (Q4)

* `util = model_class_trough_mw ÷ Σ pmax_mw(class)` over the **as-loaded** LP
  fleet (BTM already removed), at h1–3.
* `floor_share = Σ chp_grid_pmin_mw(class) ÷ model_class_trough_mw`.

### D. Model-dependence audit (Q3)

Every term in the chain `pmin_cf → grid floor → LP capacity → reported MW` is
enumerated and classified **measured / derived-from-measured / model-dependent
/ unsourced-constant**, with the file and line. A term is *model-dependent* if it
reads an LP price, an LP dispatch, or a scored residual.

## 4. Decision rule — PRE-REGISTERED

Evaluated in order; the first branch that fires wins.

| verdict | condition | consequence |
|---|---|---|
| **MODEL-DEPENDENT** | D finds any term in the floor chain reading an LP price, LP dispatch, or scored residual | Rule 13 `[R-MEASURED]` defect **independent of the residual**. Report; the repair is a *deriver* change, and it is chartable on rule 13 grounds alone. |
| **BASIS-ARTIFACT** | `R_basis ∈ [0.80, 1.25]` in **≥ 2 of 3** years | miso-115's `CC_CHP` deficit is a **reporting-basis mismatch**, not a market fact. The floor is not starving the class. **REFUSE, no solve**, correct the record, retire the named successor. |
| **MIS-APPORTIONED** | `R_basis ≥ 1.40` in **≥ 2 of 3** years **AND** A1/A2 show one pooled number applied across prime movers **AND** the apportionment plausibly sizes the surviving deficit | Structural cause with a measured identification → **charter Phase 1**: its own prereg with gates + kills, then **ONE** single-delta A/B against a same-HEAD zero-delta control. |
| **CORRECT-AND-ELSEWHERE** | `R_basis ≥ 1.40` in ≥ 2 of 3 years **AND** A1/A2 show the floor already correctly identified per prime mover | The deficit sits in fleet assignment / capacity / availability, not the floor. Say so, narrow, **stop**. |
| **INCONCLUSIVE** | anything else (incl. `1.25 < R_basis < 1.40` majority, or split signs) | **Defaults to refuse.** An inconclusive audit is not a charter. |

The middle band defaults to *refuse* deliberately: a MISO per-plant A/B is ~3 h
and ~15.5 GB peak, and this lane's discipline
(miso-103/104/105/107/108/114/115) is that a refusal on measurement is a full
result.

## 5. Kills — conditions that void the verdict regardless of the numbers

1. **K1 BTM provenance.** `CHP_BTM_PCT_BY_SECTOR["merchant"] = 35.0` is
   annotated in `constants.py` as *"residual-identified, forecast-risk — no
   independent source yet"*. If **> 20 %** of MISO `CC_CHP` capacity lands on
   that unsourced default, the B correction partly rests on a residual-identified
   constant: report B with and without those plants, and **the exposure itself
   is a reportable rule 13 / rule 5 finding** in its own right.
2. **K2 parasitic coverage.** If `plant_hourly_net` cannot produce a finite
   series for **> 20 %** of matched `CC_CHP` capacity, `R_basis` is void and only
   the `R_btm_only` upper bound is reported.
3. **K3 comparability.** The plant set, class→family map, trough window and
   calendar must reproduce miso-115's published `R` (2.156 / 2.246 / 2.555) to
   **within 0.005** before any correction is applied. If the uncorrected
   reproduction fails, the correction is not comparable and the audit is void.
4. **K4 basis premise.** `class_hourly.mw` must be verified **from code** to be
   grid-facing only (BTM removed at fleet build, never added back into the
   hourly artifact). If the BTM is already inside `class_hourly`, the entire B
   correction is void and miso-115's `R` stands as published.
5. **K5 exemption check.** `MECH_CHP_STEAM` is in `D2_EXEMPT_MECHS`, so the D-2
   forced shares miso-115 quoted (19.5 / 35.6 / 5.5 %) are **exempt** from the
   rule 20 `[R-FORCED-BUDGET]` merchant arithmetic. Any claim that the class is
   "over-forced" must be stated against that exemption, not against the merchant
   cap.

## 6. Bars this session inherits and will not cross

* **No CHP floor set to metered hourly output** — an outcome pin, rule 13
  `[R-MEASURED]`. The only admissible object is a floor identified from **steam
  host demand** per prime mover, which has a forward analogue.
* **No `miso_cc_coal_rebalance`** — no measured identification (rules 5
  `[R-NO-MAGIC]` / 21 `[R-DOF]` / 24 `[R-REGISTRY]`), and miso-115 §2 removed its
  stated premise.
* **No re-opening the trough QUANTITY question** for `CT_PEAKER` / `ST_GAS` /
  `CC_REGULAR` (miso-115, measured, refused).
* **No quoting or acting on the `CT_CHP` / `ST_CHP` ratios** — VOID on K1
  coverage (10.4 %, 26.9 %); `ST_CHP`'s zero is a Part-75 artifact.
* **No re-licensing `miso_firm_import_floor`** (outcome pin) or
  `miso_pjm_lmp_import_pricing` (refuted ex ante, miso-114 §4); **no**
  chartering the seam hour-of-day mis-shape as a C7/C3a instrument (4–7 % of the
  residual, rule 1 `[R-STRUCT]` only); **no** re-opening the top-decile
  convexity deficit (miso-89, ledgered).
* **The regulated-PRB self-commitment family stays SPENT** —
  `coal_prb_committed_dispatchable` (miso-111 R), `coal_prb_committed_split`
  (miso-112 R), `miso_coal_night_floor` (miso-113 I).
* **Rule 22 `[R-HOLDOUT]`** — 2023–2025 only; MISO holds no
  `calibration-complete` marker, so no holdout year is touched, in measurement
  or in any solve.
* **Rule 23 `[R-FROZEN-DERIVE]`** — no derive script is re-run against a
  residual. If the audit finds a deriver defect, the finding is the deliverable;
  any re-derivation commit must cite a *source-data* change or a demonstrated
  construction error, never a residual.

## 7. If Phase 0 refuses

The cross-ISO queue (`docs/mechanism-testing-matrix.md` §5.4) items still
genuinely untested at MISO, in the order this session would consider them:
**item 4 `measured_ct_heat_rates`** (cell `U`, motivated by miso-115 §4's
measured +10 % `CT_PEAKER` pricing error; MISO derives its own artifact per rule
25, and PR #3140's status must be checked first), **item 5
`dual_fuel_switching`**, and **`gas_offer_margin_zonal_anchor`** (cell `U`;
PJM's `I` and ERCOT's `K` both transfer nothing).

## 8. Contamination declared

This session read miso-115's finding, miso-114's finding, the MISO calibration
log and the CHP source files **before** writing this pre-registration, so it is
**not blind** to the expected direction — the handoff itself names the
hypothesis. The estimators, bands and kills above are fixed here so the verdict
turns on the numbers rather than on the reading, and K3 forces the audit to
reproduce miso-115's published figure before it is allowed to correct it.
