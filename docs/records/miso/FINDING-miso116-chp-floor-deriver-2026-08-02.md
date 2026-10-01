# FINDING miso-116 — the `CC_CHP` overnight deficit is a **reporting-basis artifact**, and its heat-rate half is a **probe-flag artifact**: both of miso-115 §3–§4's CHP results are withdrawn, the floor's deriver is clean, NO SOLVE SPENT

Session miso-116, 2026-08-02, branch `claude/miso-116-chp-floor-phase0-llt4t9`,
off `origin/main` at `0d49cc4`. **NO LP SOLVED.** Every number is read from
committed artifacts: the keeper bundle `results/calibration/miso109_hy_level_B`,
`thermal_tranches_MISO.csv`, `chp_power_only_heat_rates_MISO.csv`,
`parasitic_load_factors.parquet`, `data/raw/campd-unit-level/`, and the repo's
own fleet build. Probe
`scripts/probes/_miso116_chp_floor_deriver_audit.py` (re-runnable, ~8 min, zero
LP); transcript `results/calibration/PROBE-miso116-chp-floor-deriver-2026-08-02.txt`;
pre-registration `results/calibration/PREREG-miso116-chp-floor-deriver-2026-08-02.md`,
written and committed **before** the probe ran.

**Keeper UNCHANGED** (`2026-07-31-miso-109b-hy-level`). Rule 15: no run
produced, nothing to register.

## 0. Verdict

**The pre-registered decision rule returns BASIS-ARTIFACT. No charter, no
solve.** Both of miso-115's CHP results are withdrawn — for two *different*
reasons, each an artifact of how the predecessor probe measured, not of the
model.

| `CC_CHP`, h1–3 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| miso-115 `R_raw` (CAMPD **gross** ÷ model **grid-only**) | 2.156 | 2.246 | 2.555 |
| **reproduced here (K3)** | **2.156** | **2.246** | **2.555** |
| `R_btm` — × (1 − btm), upper bound | 1.065 | 1.125 | 1.237 |
| **`R_basis` — basis-matched** | **1.062** | **1.123** | **1.234** |

The pre-registered BASIS-ARTIFACT band was `R_basis ∈ [0.80, 1.25]` in ≥ 2 of 3
years. It holds in **3 of 3**, and on the parasitic-free upper bound as well.
**The ~2.1–2.4 GW "deficit" is a unit mismatch: a whole-plant quantity divided
by a grid-only quantity.**

## 1. Why the two sides were never comparable

`fleet/assembly.py:399–404` removes a cogen's behind-the-meter host self-supply
from the LP **as capacity**, not as a floor:

```
mustrun_cap = 0.0
grid_cap    = nameplate × (1 − pct_mr/100)      # pct_mr = chp_btm_pct(...)
```

The BTM share is never created as a `Generator`; the calibration bench closes
the basis on the *actual* side instead (`run_calibration_full._btm_frame`:
`classFull = EIA-923 class total − BTM host self-supply`). So the model's
`class_hourly.mw` for a CHP class is **grid-facing output only**, by
construction — verified from code as pre-registered kill **K4**
(`_write_class_hourly_sidecar` is a pure aggregation of the LP unit dispatch,
with no add-back).

miso-115 divided CAMPD `grossLoad` — the **whole plant**, host steam load
included — by that grid-only number. The gap it measured is mostly the
definition of the two quantities.

The arithmetic is forced, not fitted: MISO `CC_CHP` analytic `grid_cap` is
**3,458 MW** against a CAMPD gross trough of **3,891 / 4,098 / 4,018 MW**. The
model *cannot* produce the number it was scored against — the comparison had no
feasible pass.

## 2. The floor's deriver is clean — and the one real defect it does have is small and elsewhere

**Q1 — what does it identify?** Not a per-prime-mover export obligation. The
artifact is written per `(plant_code, plant_group)`, but
`derive_thermal_tranches` emits a row **only for the plant's primary group**
(`if primary.get(code) != group: continue`), and `chp.chp_overrides` then keys
the map by **`plant_code` alone**. Measured: 104 CHP rows over 104 plants, 0
plants with more than one row. So the floor is **one pooled per-plant CF,
derived from the primary prime mover, applied to every prime mover at that
plant**.

**Q2 — does that explain the `CC_CHP` deficit?** No — after §0 there is no
`CC_CHP` deficit to explain. The mis-apportionment is real but small and lands
elsewhere: **17 plants, 2,284 / 11,593 MW = 19.7 % of MISO CHP capacity** carry
≥ 2 CHP classes and hand every class the primary group's CF (e.g. plant 50625
applies a `CT_CHP`-derived 104.5 % to its `ST_CHP` bins; plant 50973 applies a
`CC_CHP`-derived 0.0 to its `CT_CHP` bin). The exposure is concentrated in
`CT_CHP`/`ST_CHP`, whose ratios are **VOID on miso-115's own K1 coverage kill**
(10.4 %, 26.9 %) and are not quoted here.

**Q3 — is any term model-dependent?** **No.** Every term in
`pmin_cf → grid floor → LP capacity → reported MW` is measured or
derived-from-measured: CAMPD p2 available-CF under the measured outage overlay
(`status=ok`, 20 of 104 rows), EIA-923 class CF (`status=eia923_cf`, 84 rows),
EIA-923-net/CAMPD-gross parasitic factors, EIA-860 `Sector`, and EIA-923
Schedule-8 useful-thermal shares. **Nothing reads an LP price, an LP dispatch or
a scored residual.** The floor chain is rule 13 `[R-MEASURED]`-admissible as
constructed.

**The one exception, reported as pre-registered kill K1.**
`CHP_BTM_PCT_BY_SECTOR["merchant"] = 35.0` carries its own comment in
`constants.py:404`: *"residual-identified, forecast-risk — no independent source
yet"*. It sizes **54.6 %** of MISO `CC_CHP` capacity (3,841 of 7,036 MW). It
does not *read* a residual at derive time, so it does not fire the
pre-registered MODEL-DEPENDENT branch — it is an **unsourced constant**, a rule
5 `[R-NO-MAGIC]` / rule 21 `[R-DOF]` exposure, and it is named here rather than
left implicit. Split on it (denominator apportioned by `grid_cap` share, so
suggestive only):

| `CC_CHP` `R_basis` | share of grid_cap | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|
| sector-**sourced** (industrial/commercial) | 20.5 % | 1.409 | 1.399 | 1.774 |
| **merchant** (unsourced 35.0) | 79.5 % | 0.973 | 1.052 | 1.095 |

A ~1.4× under-run may survive in the ~20 % sector-sourced subset — worth
**≈ 0.3 GW**, not 2.1–2.4 GW, on an apportioned denominator. That is not a
charter; it is a note for whoever revisits the merchant share.

## 3. Q4 — the "priced 23 % too cheap" reading is REFUTED, and its source is a probe flag

miso-115 §4 read `CC_CHP` as *"priced 23 % too cheap while dispatching half the
measured volume — the signature of a class whose output is set by a floor, not
by economics."* Three separate things are wrong with that, and the first is
mechanical:

**(a) A floor is a lower bound. It cannot hold a class down.** If a too-cheap
class under-runs, the binding constraint is an *upper* bound. Measured, the
class is at neither: it runs at **45.5–52.8 % of its own `grid_cap` ceiling**
and its analytic floor is 56–65 % of its trough MW. It is dispatching
economically in between. D-1 agrees — `profile_r` = **0.989 / 0.987 / 0.967**,
a class whose diurnal shape tracks the actual almost exactly, which a
floor-pinned class does not do.

**(b) The 6.76 MMBtu/MWh was never the keeper's heat rate.**
`load_fleet_from_csv` defaults `measured_chp_heat_rates=False`; the keeper
**arms it**. miso-115's `model_fleet()` omitted the flag, so it read the
pre-correction eGRID steam-credited rate. Measured both ways on the identical
fleet:

| MISO cap-weighted heat rate | `CC_CHP` | `CT_CHP` | `CT_PEAKER` |
|---|---:|---:|---:|
| flag **off** (what miso-115 §4 read) | 6.76 | 6.62 | 12.37 |
| flag **on** (what the keeper solved) | **8.77** | **7.75** | 12.37 |

Against miso-115's own measured CAMPD gross **8.83**, the keeper's `CC_CHP`
rate is **8.77 — a 0.7 % agreement, not a 23 % discount.**

**(c) On the keeper's flags the ordering is right way up.** Plant-matched over
the 14 CAMPD-covered `CC_CHP` plants, full year, no trough selection:
cap-weighted model **9.12** vs CAMPD gross **9.48**, ratio **1.056 / 1.054 /
1.032**. eGRID's rate is on a **net** denominator and CAMPD's on a **gross**
one, so the model sitting just above is the expected ordering. The flag-off
comparison inverted it, which is what made the reading look like a finding.

**`CT_PEAKER` is unaffected — miso-115 §4's other half stands.** The keeper does
not arm `measured_ct_heat_rates`, so 12.37 is its true value and the measured
+9.9…+11.1 % pricing error is real, exactly as published.

**Residual, reported not acted on:** 4 of 14 matched plants (52.7 % of matched
capacity) still sit below 0.85× CAMPD — 10745, 55089, 55259, 55088, all on the
measured artifact. A per-plant item under rule 14 `[R-ACCURATE]`, not a
class-level mispricing.

## 4. Kills — all pre-registered, all resolved

* **K3 comparability — PASSED EXACTLY.** All nine published miso-115 ratios
  reproduce to 3 dp (`CC_CHP` 2.156/2.246/2.555, `CT_CHP` 0.272/0.356/0.269,
  `ST_CHP` 0.000) before any correction. The correction is applied to the same
  plant set, family map, trough window and calendar.
* **K4 basis premise — VERIFIED IN CODE**, §1. Had `class_hourly` carried the
  BTM, the whole correction would have been void and miso-115's `R` would have
  stood.
* **K2 parasitic coverage — FIRED**, and handled as pre-registered. Only 24.1 %
  of `CC_CHP` class capacity carries a factor, so the verdict is read off the
  **`R_btm` upper bound** (1.065 / 1.125 / 1.237) — same band, same verdict, in
  3 of 3 years. The fallback used for uncovered plants is `factor = 1.0`, which
  is exactly what `campd.plant_hourly_net` itself uses, so probe and deriver
  share one convention.
* **K1 BTM provenance — FIRED**, reported in full at §2.
* **K5 exemption — noted.** `MECH_CHP_STEAM` sits in `D2_EXEMPT_MECHS`, so
  miso-115's 19.5 / 35.6 / 5.5 % D-2 shares are **exempt** from the rule 20
  `[R-FORCED-BUDGET]` merchant arithmetic. "Over-forced" is not a gate verdict
  for this mechanism.

## 5. What is withdrawn, and what still stands

**Withdrawn** (both miso-115, both probe artifacts, neither a model defect):

* §3 "`CC_CHP` runs less than half its metered overnight output; deficit
  2,086 / 2,274 / 2,446 MW, the largest identified component of the gas hole"
  — a gross-vs-grid basis mismatch.
* §4 "`CC_CHP` priced 23 % too cheap … held down by its floor" — a probe-flag
  artifact plus a mechanically impossible attribution.
* §6's named successor ("does the CHP floor explain a CC-cogen floor at under
  half of metered output") — **the premise does not exist**. Retired.

**Stands, unchanged:** miso-115 §0–§2 (the trough marginal unit is not
mis-specified; `CT_PEAKER`/`ST_GAS`/`CC_REGULAR` all reproduce), §4's
`CT_PEAKER` +9.9…+11.1 % measured pricing error, the `CT_CHP`/`ST_CHP` VOID
status, and miso-114's decomposition. **The ~3 GW model-vs-CAMPD all-gas
overnight difference in miso-115 §3's reconciliation table is measured on that
same uncorrected basis** — the model column is grid-only for CHP while CAMPD
and EIA-930 are whole-plant — so that table does not size a hole either, and no
successor should inherit it as one.

## 6. What must NOT be done with this

* **This does not license raising or lowering any CHP floor.** The floor's
  identification is measured and clean (§2, Q3); there is no residual it was
  invoked to close.
* **`miso_cc_coal_rebalance` stays refused** — no measured identification (rules
  5 / 21 / 24), and its premise was already removed by miso-115 §2.
* **Do not re-open the trough quantity question** for `CT_PEAKER` / `ST_GAS` /
  `CC_REGULAR` (miso-115, measured, refused); **do not quote the `CT_CHP` /
  `ST_CHP` ratios** (VOID on coverage, on either basis).
* `miso_firm_import_floor` stays rejected (outcome pin);
  `miso_pjm_lmp_import_pricing` stays refuted ex ante (miso-114 §4); the seam
  hour-of-day mis-shape stays a rule 1 `[R-STRUCT]` item at 4–7 % of the
  residual; the top-decile convexity deficit stays miso-89's ledgered object;
  the regulated-PRB self-commitment family stays SPENT.
* **No derive script was re-run** (rule 23 `[R-FROZEN-DERIVE]`). The deriver
  defect at §2 is documented, not patched against a residual.

## 7. The named successor

C7 `COAL_PRB` remains the keeper's one failing criterion, and **three sessions
of overnight-gas hypotheses have now closed without reaching it** (miso-114
seam, miso-115 marginal unit, miso-116 CHP). The two best-identified remaining
objects, in order:

1. **`measured_ct_heat_rates` (matrix item 4, MISO cell `U`)** — miso-115 §4's
   `CT_PEAKER` +9.9…+11.1 % measured pricing error survives this audit intact
   and is worth $3.15 / $2.45 / $3.91 per MWh at the keeper's gas prices.
   Admissible on rule 14 `[R-ACCURATE]` grounds regardless of the residual.
   **PR status checked and CORRECTED: #3140 is CLOSED, NOT MERGED** (closed
   2026-07-30; miso-115 recorded it as "open and unmerged"). But the successor
   is **not** blocked on a re-derivation, as the handoff assumed: MISO's
   artifact `campd_ct_heat_rates_MISO.csv` **is on `main` and loadable** — 86
   entries via `measured_ct_heat_rates("MISO")`, landed under PR #3217
   (neiso-71), not #3140. The cell correctly stays `U` because no merged MISO
   *result* exists; what is missing is the arm and its A/B, not the input.
2. **The 4 plant-level `CC_CHP` heat-rate outliers** at §3 (52.7 % of matched
   capacity below 0.85× CAMPD) — a per-plant rule 14 item inside an
   already-armed mechanism.

**A methodological note for the lane, which is the more durable result here:**
both withdrawn findings came from a probe reading the model side with a
*different configuration than the keeper solved* — once on the reporting basis
(grid vs whole-plant), once on a default-off flag. Neither was visible in the
ratio itself. A probe that compares against a keeper should build its model side
from that keeper's own `run_config.json`, which this session's probe now does
and which costs nothing.

## 8. Rule duties

* **Rule 15** — no run produced; nothing to register.
* **Rule 16** — no bundle; the 2023–2025 span was audited in one pass.
* **Rule 22 `[R-HOLDOUT]`** — 2023–2025 only; MISO holds no
  `calibration-complete` marker and no holdout year was read.
* **Rule 23 `[R-FROZEN-DERIVE]`** — no derive re-run; no artifact regenerated.
* **Rule 24 `[R-REGISTRY]`** — every crosswalk is the repo's own
  (`states_for_iso`, `_hour_index_8760`, `unit_family`, `chp_btm_pct`,
  `chp_pmin_cf`, `chp_overrides`, `pooled_factor_map`). No hand map.
* **Rule 19 / 26** — nothing armed, nothing stacked.
* **Rule 28 duty (b)** — `chp_steam_following` and `measured_chp_heat_rates`
  MISO cells annotated in this session. Both keep status `K`: no mechanism was
  armed, rejected or promoted — the corrections are to the *evidence*, not to
  either mechanism.
* **Record correction** — miso-115's probe carries a docstring note pointing
  here. Its numbers are left exactly as run; the record of what miso-115
  measured is preserved.
* **Contamination declared** — the session read miso-115's and miso-114's
  findings and the CHP sources before writing the pre-registration, so it was
  **not blind** to the expected direction; the handoff itself named the
  hypothesis. K3 forced a byte-level reproduction of the predecessor's figure
  before any correction was allowed, and the verdict went **against** the
  handoff's framing (which expected a mis-apportioned floor).
* Next number: **miso-117.**
