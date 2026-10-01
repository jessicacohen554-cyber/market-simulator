# RESULT — SPP-27 SPAN. The per-plant must-run window at the **whole-operating-day commitment grain**, 2023–2025.

**Lane** SPP-27 · **Registered run** `2026-09-10-spp-27-commitment-grain`, bundle
`results/calibration/spp27_span` · **Control** `2026-09-10-spp-64-stgas-selfcommit` /
`results/calibration/spp64_span`, **differenced, never re-solved** (rule 29(b) form 4) ·
**Charter** `docs/handoffs/PRECOMMIT-spp-27-commitment-grain-2026-09-10.md` (pushed at `32dfd75e`,
before any LP) · **Screen** `docs/RESULT-spp27-screen-2023.md` (six of six STOP gates PASS) ·
**Shard report** `docs/SHARDREPORT-spp27-span.md` · **Object** card **R-be**.

**SCORER'S DETERMINATION: `CALIBRATED`** — grade 7 of 8, **0 fails**, 1 ledgered C3c caveat.
**Identical to the keeper on every scored criterion**, both re-scored live at HEAD (rubric v3.7).

**THIS LANE'S PROMOTION RECOMMENDATION: PROMOTE — but the case is narrow and the case against is
real, and §5 states it first. Promotion is the OWNER's call (rule 31 `[R-RETAIN]`); this lane has
NOT acted.** `frontend/data/backcast/keepers/SPP.json` is UNTOUCHED, SPP's designated keeper remains
`2026-09-10-spp-64-stgas-selfcommit`, and no `complete` marker or `frontier` declaration was added
or implied.

---

## 1. The solve

ONE invocation, three years, sequential in one process (rules 12 `[R-PARALLEL]` / 16 `[R-ALLYEARS]`):

```
replay_keeper.py results/calibration/spp64_span --years 2023 2024 2025 \
  --out-dir results/calibration/spp27_span --set mustrun_window_commitment_grain=true
```

Exit 0, **499 s (8 min 19 s)**. Rule 32 `[R-SHARD]`: the parent ran **no LP** — phase 0, the
scoring, the composition and this document are the parent's; the solve, the attestation and the
registration were the shard's (the seam deviation is declared in
`docs/handoffs/ADDENDUM-spp-27-registration-seam-2026-09-10.md`, pushed before the span).

**Config identity — EXACTLY ONE differing key across the entire `scenario_config`:**
`mustrun_window_commitment_grain`, control `None` (the declared default materializing for a field
that did not exist when keeper 8 solved) → arm `True`. `offer_curve_by_group` **byte-identical** —
the authorized price-tuning channel was not touched, re-cut or swept (rule 1 `[R-STRUCT]` (c)).
This is cleaner than keeper 8's own A/B, which carried four differing keys.

**G-DRIFT (rule 29(b) form 4):** `git diff` on the solve path between the keeper's `basis_sha`
`7de0b789a4f709b19bacc…` and this lane's base returns **EMPTY — zero files**. Nothing to classify;
the keeper's committed bundle IS the control and **no control solve was spent**.

## 2. THE SCORER — every criterion, both runs, re-scored live at HEAD

| criterion | tier | KEEPER | **ARM** |
|---|---|---|---|
| C1 fuel-mix by class | LOAD | PASS | **PASS** |
| C2 system volume | LOAD | PASS | **PASS** |
| C3a mean LMP | LOAD | PASS | **PASS** |
| C3b price duration/shape | LOAD | PASS | **PASS** |
| C3c price tail / scarcity | SUPP | CAVEAT *(ledgered)* | **CAVEAT** *(ledgered)* |
| C4 fleet hourly dispatch corr | SUPP | PASS | **PASS** |
| C6 governance gate | PROT | PASS | **PASS** |
| C8 forced-energy share | PROT | PASS | **PASS** |
| **determination** | | **CALIBRATED** | **CALIBRATED** |
| grade / fails / ledgered | | 7 of 8 · 0 · 1 | **7 of 8 · 0 · 1** |
| D-10 free-class C1 | | all 16/16 · free 12/12 | **all 16/16 · free 12/12** |

**Nothing scored moves in either direction.** C3a +1.0/+0.1/+0.7 % → **+0.9/+0.1/+0.7 %**; C3b
0.173/0.171/0.163 → **0.173/0.171/0.164**; C5a CO2 −1.8/−1.4/+2.8 % → **−1.9/−1.4/+2.7 %**.
`dump` is 0.0000 MWh in every year on both runs and `slack` is **byte-identical** (0 / 370.1017 / 0
MWh). The system price max is **byte-identical** (59.3126 / 2000.0000 / 73.7731), which is the
mechanical reason **C3c cannot and does not move a single hour**.

**So this run buys no score.** That is the point: what it buys is §3.

## 3. WHAT IT REPAIRS — the floor's own shape and the starts it asserts

The floor claims a **commitment** — a day-ahead, whole-operating-day decision by a
vertically-integrated utility — and the engine placed it by ranking **individual hours** by system
load, giving it the diurnal shape of **load** instead of the diurnal shape of **commitment**.

**The driver, measured at zero LP from the plants' own CAMPD record** (22 ST_GAS plants × 3 years,
via the committed bench): the peak-to-mean of each plant's **online** hour-of-day profile — 1.000
for a unit committed for whole days, ≫ 1 for a daily cycler — is **1.007–1.146 on 21 of the 22
plants**, and the night(h0-5)/afternoon(h12-17) share of online hours is **0.78–1.09 on 19 of 22**.
Only **Mooreland 3008 (1.609)** genuinely two-shifts. When these units are synchronized they run
through the overnight trough.

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| mechanism-16 window peak-to-mean, **keeper** | 1.2349 | 1.2159 | 1.2159 |
| mechanism-16 window peak-to-mean, **ARM** | **1.0000** | **1.0000** | **1.0000** |
| **implied STARTS**, keeper | **2,843** | **3,002** | **2,792** |
| **implied STARTS**, ARM | **288** | **342** | **315** |
| measured runs (the meter) | 647 | 746 | 778 |
| keeper ÷ meter | **4.39×** | 4.02× ‡ | 3.59× ‡ |
| ARM ÷ meter | 0.45× | 0.46× | 0.41× |

‡ The 2024 and 2025 CONTROL columns of this table are affected by the reconstruction
order-dependence recorded in §9 — the parent's own independent rebuild read 2,740 / 2,335 instead of
3,002 / 2,792. **2023 is stable at 2,843 in every rebuild**, the ARM row is 288 / 342 / 315 in every
rebuild, and the conclusion — the keeper's window asserts several times the meter's starts and the
arm's asserts fewer — holds under every history. The control/arm ratios within a year are measured in
the same process and are unaffected.

Per plant the keeper's window asserts **202 starts on 989 MW Muskogee in 2024** (measured 27), 307
on Plant X in 2023 (45), 179 on 883 MW Wilkes (11), 166–169 on Maddox (6–16). **A gas-steam unit
cannot start 200 times in a year** — rule 18 `[R-PHYSICS]`. The armed window asserts **fewer** starts
than the meter records in every year: a conservative commitment scaffold, which is what a floor is
for. Floored energy rises **+5.2 / +3.1 / +3.3 %** on an all-on basis (control and arm measured in the
same process, so the ratio is unaffected by §9); realized forced energy
2.3238 → **2.555**, 2.3398 → **2.5195**, 2.5291 → **2.6803** TWh.

## 4. Where the energy went

| class | 2023 Δ | 2024 Δ | 2025 Δ |
|---|---|---|---|
| **ST_GAS** | **+0.2801** | **+0.2004** | **+0.2403** |
| COAL_PRB | −0.1709 | −0.1071 | −0.2026 |
| CC_REGULAR | −0.0976 | −0.0745 | −0.0481 |
| COAL_LIGNITE | −0.0145 | −0.0049 | −0.0386 |
| CT_PEAKER | +0.0195 | −0.0003 | +0.0640 |
| **wind** | **−0.0128** | **−0.0126** | **−0.0148** |
| CHP (CC/CT/ST) | −0.0013 | +0.0004 | +0.0042 |
| nuclear / hydro / biomass / oil | 0.0000 | 0.0000 | ≈0.0000 |
| **TOTAL** | **+0.0026** | **+0.0014** | **+0.0035** |

Paid by coal and CC_REGULAR, **not** by curtailing wind (−0.011 %). Energy conserved to
≤ 0.0035 TWh on ~285–302 TWh.

## 5. THE ADVERSE FINDING — the arm does **NOT** close card R-be

`D4.passed` is **False** on the arm, as on the keeper. The conduct-FAIL count is **4 / 4 / 4**
against the keeper's **4 / 5 / 3** — **the same total of 12 rows across the span.**

| plant | 2023 keeper → ARM | 2024 keeper → ARM | 2025 keeper → ARM |
|---|---|---|---|
| 1230 Cimarron River | 0.7018 → **0.6096** FAIL | 0.5906 → **0.4408 PASS** | 0.7569 → 0.7191 FAIL |
| 1235 Great Bend | 0.6230 → **0.5606** FAIL | 0.7016 → **0.5760** FAIL | 0.8256 → **0.7452** FAIL |
| 1271 Coffeyville | 0.6976 → **0.5875** FAIL | 0.7734 → **0.6938** FAIL | 0.7298 → **0.6411** FAIL |
| **3008 Mooreland** | 0.5357 → **0.6002** FAIL | 0.5173 → 0.5725 FAIL | 0.4735 → **0.5262 FAIL** |
| 6193 Harrington | *(no bench)* | 0.8193 → 0.7919 FAIL | pass → pass |

*(`measured_zero_share` — the share of the hours the floor binds in which the plant's own meter reads
zero; the rider FAILs at ≥ 0.50.)*

**Read honestly: the arm moves the three flat-profile plants materially toward the bar in every
year — nine of nine year-rows improve, one of them (1230/2024) crossing to PASS — and it moves
Mooreland the other way, crossing it to FAIL in 2025.** Net zero rows. **That is exactly what the
charter predicted, in both directions, before the solve**, from the p2m census: a uniform whole-day
window is right for the 21 plants whose commitment is flat and wrong for the one that two-shifts.

**Mooreland is NOT special-cased.** A per-plant grain predicate needs a threshold, which is a free
parameter (rule 21 `[R-DOF]`), and choosing it against this statistic is the fitted-mechanism
selection rule 1 `[R-STRUCT]` (c) forbids. A plant-level exclusion is refused on miso-170's own
warning that it *"would bury that error inside a membership list"*.

**What remains of R-be, named rather than absorbed:**
1. **Day SELECTION.** For 1230 / 1235 / 1271 the day-selection lift over chance is only ~2×; their
   commitment answers to their own utility's conditions, not to SPP-wide load. **No
   forecast-admissible signal available to this model reaches it.**
2. **A SIZE component that is NOT a defect.** Pooled `online_frac` is the rule-13-admissible
   construction and necessarily mis-sizes an individual year (1230: k = 1,428 h against 839 metered
   online hours in 2023 and 2,186 in 2024). The per-year alternative
   (`mustrun_online_frac_per_year`) is registered **backcast-only** for exactly that reason and is
   **refused** here.
3. **The grain, which this arm fixes**, and which was the only repairable part.

## 6. The other diagnostics

- **C8 / rule 20 `[R-FORCED-BUDGET]`:** ST_GAS forced share 0.1962/0.1849/0.1744 →
  **0.2112 / 0.1969 / 0.1825** against `d2_merchant_max_share` 0.30. Still under in all three years,
  so the rule's conditional-pass limb is again not reached and the "is a 100 %-regulated class a
  *merchant* class" question stays open. Every other class is **0.0 %** forced — rule 19
  `[R-ONE-MECH]` holds on the solved artifact.
- **D-1:** `D1.passed = True`. ST_GAS `profile_r` 0.997/0.999/0.997 → **0.987 / 0.997 / 0.992**
  (bar 0.80) and `cv_ratio` 2.117/1.844/1.717 → **1.672 / 1.515 / 1.338** (bar 0.50, one-sided) —
  the ratio moves further **toward** 1.0 in all three years. The small `profile_r` slip is real,
  reported, and nowhere near its bar.
- **D-A diurnal price amplitude** (reported-only, band-free): 38.8 / 38.6 / 24.6 % of measured,
  phase OK in all three years, hod r +0.946 / +0.968 / +0.892.

## 7. Rules

- **Rule 21 `[R-DOF]`: ZERO free parameters added.** Ledger inherited at **n_entries 3 /
  n_residual 2** (`offer_curve_by_group`, `offer_curve_smoothing`, `wefor_multiplier`), verified
  from the written attestation. There is no threshold, share, multiplier or length: the grain is the
  **operating day**, and `round(k/24)` is arithmetic on the existing `online_frac`.
- **Rule 13 `[R-MEASURED]`: nothing measured enters the PLACEMENT** — the ranking is the model's own
  load shape — so the field is deliberately **not** in `_BACKCAST_ONLY_OVERLAY_FIELDS` and it
  regenerates for a forecast year from forward drivers.
- **Rule 25 `[R-ISO-SCOPE]`:** armed for SPP alone via `--set`; the dataclass default stays `False`
  and is registered in `_CACHE_KEY_OPTIONAL_FIELDS` at that declared default, so **every
  pre-existing cache key of all seven ISOs is byte-stable and no other ISO moves.** The matrix cell
  is `O` in SPP's shard and `U` in every other.
- **Rule 19 `[R-ONE-MECH]`:** window PLACEMENT alone; SIZE, LEVEL, MEMBERSHIP and hour-eligibility
  untouched, their four gates all off. The COAL and CT_PEAKER seams deliberately keep the hour
  grain — separate mechanism ids whose own conduct evidence this lane does not carry, and the coal
  half is the parallel `spp-64-price-formation-rbb` lane's object.
- **Variants measured at phase 0 and DELIBERATELY NOT TAKEN**, declared so the choice is not hidden:
  a day-**PEAK** ranking key and a **NET-load** (load − wind − solar) signal each score marginally
  better on the conduct-overlap statistic (net+peak 0.8368 against day-mean-gross 0.8238 over 65
  plant-years). Both refused: each bundles a second, independently-unmotivated change into the same
  arm, and net-vs-gross is a **wash at the hour grain** (0.8168 vs 0.8168), so SPP's own data does
  not establish net load as the better commitment signal here. **Nothing was swept against any
  gate.**

## 8. PROMOTION — the case against, first

**AGAINST.** The arm buys **no score at all** — every criterion, the grade, the caveat count and the
free-class score are identical to the keeper — and it does **not** close the defect it was chartered
against: `D4.passed` is still False and the conduct-FAIL total is unchanged at 12. It costs +3–5 %
forced energy and pushes C8's ST_GAS share from 0.1962 to 0.2112 (still well under 0.30). A
defensible owner ruling is: **a repair that fixes a diagnostic nobody scores, changes no number, and
leaves the named card open is not worth a keeper churn** — keep keeper 8 and let the next lane
attack day selection.

**FOR, which is why this lane nonetheless recommends it.** Rule 1 `[R-STRUCT]` is explicit that a
run is a keeper because it is **the most structurally faithful**, and that a structurally-correct
mechanism is *"never rejected because the residual didn't move"*. On that test:

- On 2023 — the one year whose reconstruction is stable in every rebuild — the keeper's floor
  asserts **2,843 starts against the meter's 647, 4.39×**, and the arm asserts **288**. The other
  two years are the same order under every history, and one plant alone carries **202 asserted
  starts on a 989 MW steam unit in 2024 against 27 measured**. That is not a marginal defect; it is a
  physically impossible commitment pattern, and rule 18 `[R-PHYSICS]` names it.
- The measured driver is unambiguous and is **SPP's own**: 21 of 22 plants run flat across the
  committed day (p2m 1.007–1.146). The keeper places the floor with the shape of load (1.216–1.235);
  the arm places it with the shape of commitment (1.0000).
- It adds **zero free parameters**, moves **one** field, leaves the authorized price channel
  byte-identical, and is byte-stable for every other ISO.
- Nothing regressed. Not one scored criterion, not dump, not slack, not the price tail.

**The choice is: the same numbers with a floor that asserts a possible commitment, or the same
numbers with a floor that asserts an impossible one.** On rule 1's own test that is not a close
call — but it is also not a scoreboard argument, and this lane will not dress it up as one.

**The successor card is unchanged and specific — R-be's remaining half: day SELECTION for plants
whose commitment is not system-load-driven.** This lane found no forecast-admissible signal that
reaches it and says so rather than inventing one.

## 9. RETENTION AND HONEST LIMITS

- **Rule 31 `[R-RETAIN]`: nothing was deleted.** `results/calibration/spp27_*/` is gitignored, which
  is what discharges rule 29(c); the screen and span bundles live on ephemeral shard containers and
  **do not survive them**. What IS committed and permanent: the bundle's slim files + `hourly/`
  sidecars, the registry sidecar, `runs/2026-09-10-spp-27-commitment-grain.js`, and this record —
  everything a later lane needs to difference against this run without re-solving it. Registration
  used **`--no-prune`** for the same reason.
- **The full bundle's `unit_hourly_*` and `network_*` parquets (≈ 48 MB) were deliberately NOT
  carried into this branch.** The shard committed them on its own branch; the keeper's committed set
  is `class_band_hourly` / `class_hourly` / `storage` / `system`, and this bundle matches it (3.1 MB).
- **An instrument defect found and routed, not fixed:** `scripts/lib/bundle_fleet.reconstruct_bundle_fleet`
  is **order-dependent across years within a process** for SPP. The control's 2025 mechanism-16
  floored energy read **3.477892** (built after 2024 in one process), **3.758881** (built alone,
  reproduced exactly twice) and **4.263776** (built after 2023 and 2024). **2023 is stable at
  3.870051 in all three histories**, which is why the screen gates — all set on 2023 — are
  unaffected, and the qualitative span conclusions (arm p2m exactly 1.0000, arm starts an order of
  magnitude below the control) hold under every history. **Nothing scored is affected**: every
  scored number comes from the solved bundles, and the solve itself builds years sequentially in one
  process identically for control and arm. This is not this lane's object and is left open.
- **A duplicate screen shard and a stalled span shard exist.** The parent misread the wall clock and
  launched a second screen shard; the first span shard went idle asking for clarification and was
  re-launched with a plainer prompt. Neither produced results that were destroyed. Cost: one
  duplicated ~5-minute LP. Recorded rather than tidied away.
- **`[R-HOLDOUT]` was removed 2026-09-09**, so no year is protected from having been iterated
  against. 2023–2025 are all model-**SELECTION** evidence. **`CALIBRATED` here is a determination
  under the rubric, not a certified out-of-sample skill claim**, and nothing here should be quoted
  as one.
