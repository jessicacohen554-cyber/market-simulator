# FINDING miso-99 — the CHP heat-rate correction is UNBLOCKED and PROMOTED: the gross→net basis miso-98 §6.1 could not obtain is **not needed**, because eGRID publishes the steam credit it removed (`CHPCHTI`) and adding it back lands on the model's own NET denominator

**Determination: A/B SOLVED, REGISTERED, AND PROMOTED. MISO keeper →
`2026-07-28-miso-99b-chp-power`** (supersedes
`2026-07-27-miso-98b-sectormeasured`; same determination NOT-YET, same
criterion profile, C3a better in all three years, no criterion regressed).

| arm | run id | bundle | `measured_chp_heat_rates` |
|---|---|---|---|
| A | `2026-07-28-miso-99a-chp-hr` | `miso99_chp_hr_A` | off (control) |
| B | `2026-07-28-miso-99b-chp-power` | `miso99_chp_hr_B` | **on** |

---

## 1. STEP 1 — the blocker, and why the answer is to delete the gross basis rather than estimate it

miso-98 §6.1 stopped on caiso-128 §6(a)'s non-optional step: *"the plant's own
same-year measured gross→net ratio"*, which fires on **0 of 19** MISO rows
because `compute_parasitic_factors` sends every cogen to `class_default`. The
prompt's STEP 1 asked for a CHP-specific station-service ratio that separates
station service from host supply, warning that reusing `net923/gross_CEMS`
double-counts the host share `chp_btm_pct` already holds out.

**Measured: the plant-level gross→net ratio is not obtainable for CC_CHP at
all, and it is also not the quantity the correction needs.**

* Not obtainable: at a cogen, CAMPD's `grossLoad` channel and EIA-923's net
  generation cover **different unit sets**, in both directions and by large
  margins. Midland Cogeneration Venture reports CEMS gross 7.89 TWh against
  EIA-923 net **9.76 TWh** (ratio 0.809 — CEMS misses the steam turbines);
  Portside Energy reports 0.070 against 0.232 (0.303); Primient reports 0.674
  against 0.389 (1.732). caiso-128's `g2n` survived this only by
  `clip(1.0, 1.35)`, which is a hand bound doing the work at exactly the
  plants where the raw ratio is meaningless.
* Not needed: **eGRID `PLNGENAN` IS the model's net basis.** The incumbent
  offer heat rate is `PLHTRT = PLHTIAN / PLNGENAN`
  (`process_eia860._join_egrid_heat_rate`, PLNT23), and `PLNGENAN` is
  identical to the EIA-923 combustion net the benchmark holds out against
  (`net923 / PLNGENAN` = 1.000000 on every MISO thermal plant measured). A
  correction expressed on that denominator never touches a gross number.

### 1.1 The measurement: eGRID publishes both halves of the split

The eGRID plant sheet carries `PLHTIAN` (heat input allocated to **electricity**
— the numerator of the rate the model loads) **and `CHPCHTI`** (heat input
allocated to **useful thermal output** — the steam credit itself), zero at a
plant eGRID credits nothing and blank at every non-CHP plant. So

```
heat_rate_power_only  =  (PLHTIAN + CHPCHTI) / PLNGENAN
```

is the incumbent input with eGRID's own published CHP allocation undone: same
source, same vintage, same plant, same denominator, **one change**.

**No double-count of the host.** `chp_btm_pct` holds the host share out as a
*volume* (LP capacity, the steam floor, the benchmark subtrahend); this is an
*intensity* (MMBtu per net MWh) applied to whatever the LP dispatches. Host-
served MWh sit in the denominator of the plant's own rate because they come off
the same machine burning the same fuel — that is what makes it the right
intensity, not a leak.

### 1.2 Validation: the split is arithmetic on metered fuel, not an eGRID model

`PLHTIAN + CHPCHTI` is checked against the plant's **independently metered**
CAMPD/CEMS annual heat input, MISO 2023:

| quantity | median ratio to CEMS metered heat input | within 1 % |
|---|---|---|
| `PLHTIAN + CHPCHTI` | **1.00000** | **22 / 25 plants** |
| `PLHTIAN` alone (what the model loads) | 1.47290 | 2 / 25 |

Midland: CEMS 86,087,081 MMBtu vs `PLHTIAN + CHPCHTI` = 67,243,318 +
18,843,760 = 86,087,078 — agreement to 3 MMBtu in 86 million (3.5 × 10⁻⁸).
The three misses (10328, 55096, 55799) are plants with combustion units below
the Part-75 threshold, where **CEMS undercounts** and eGRID is the complete
source; the check fails toward CEMS, never toward eGRID. Every row carries its
own `cems_vs_egrid_total`.

### 1.3 Scope, on turbine physics — and it is a real restriction

Adding the credit back charges **all** the plant's fuel to its power. That is
the power-only rate for a **topping cycle** (fuel through the prime mover
first; the process steam is recovered from its exhaust, so no fuel is avoided
by making it). It is emphatically **not** the rate for a **boiler-first /
back-pressure** cogen, whose boiler exists for the host's process heat and
whose turbine sits in the let-down path: MISO `ST_CHP` add-backs run to
**435 MMBtu/MWh**. Two definitional gates, both frozen at derive time:

1. **Prime mover** — `CC_CHP` and `CT_CHP` only. `ST_CHP` is out of scope for
   that physical reason and keeps the existing chain; it is 0.4–0.8 TWh in
   MISO, far below the rule-20 line.
2. **Unfired-topping thermal share ≤ 0.50.** Not swept: eGRID's credit is
   `T / 0.8` (the fuel a displaced 80 %-efficient boiler would have burned), and
   the EPA CHP Partnership gas-turbine envelope caps useful thermal at ~40 % of
   fuel input, so an unfired topping cycle cannot exceed `0.40 / 0.8 = 0.50`.
   Above it the plant is firing fuel straight to steam.

Plus the repo's **existing committed** physical bands on the corrected value
(`EGRID_CC_HR_PHYSICAL_CEILING` for CC; `derive_campd_ct_heat_rates`' 6.0/25.0
for CT) and a `basis_mismatch` gate excluding plants whose incumbent is a
boundary repair or `HEAT_RATE_BINS` fallback rather than a plain `PLHTRT`.
**Zero fitted parameters.** Rows outside any gate are written with their
measured value and a flag, and are **not applied** — rule 14 `[R-ACCURATE]`'s
named "different boundary" exception, never replaced by a guess.

### 1.4 What lands, MISO

`data/raw/_processed-legacy/chp_power_only_heat_rates_MISO.csv`, 76 rows,
25 applied:

| class | plants | MW | **% class MW** | model (credited) | measured (power-only) | model error |
|---|---|---|---|---|---|---|
| **CC_CHP** | 14 / 24 | 5,755 / 7,036 | **81.8 %** | 6.70 | **9.16** | **−26.8 %** |
| **CT_CHP** | 11 / 52 | 977 / 2,625 | **37.2 %** | 6.39 | **9.43** | **−32.2 %** |

Flag census: `not_unfired_topping` 41, `ok` 25, `no_chp_credit` 5,
`no_egrid_row` 2, `basis_mismatch` 2, `above_physical_band` 1.
In the LP: **72 generators / 6,732 MW** repriced, all CC_CHP or CT_CHP.

**This supersedes the CEMS route entirely.** `derive_campd_chp_heat_rates.py`
and its two artifacts are **DELETED** (rule 26 `[R-DELETE]` — a wrong-basis
derive that still parses is a re-armable answer key). Its measurement was worse
in a way the new route makes visible: it computed `heatInput / grossLoad` over
CEMS units only, which at a CC cogen is the **bare gas-turbine** rate with the
steam turbine's MWh missing from the denominator (Midland 11.23 vs the correct
8.82), and it over-corrected Primient by +68 % against a plant eGRID gives
**no credit at all** (`CHPCHTI = 0`, so the incumbent 12.16 was already right).

---

## 2. STEP 2 — the gate

`ScenarioConfig.measured_chp_heat_rates`, **default off, byte-identical off**,
ISO-generic. Cache-key-optional at its default (armed runs get a distinct key).
Applied in `chp.apply_measured_chp_heat_rates` at the `load_fleet_from_csv`
seam, keyed on the **`(plant_code, plant_group)` pair** so a mixed facility's
out-of-scope trains keep their rate; it runs **before**
`_correct_chp_steam_credit_hr` and returns the ids it repriced, which that
function then **skips** — a plant on its own measured rate must never also take
the 1.8× hand factor (rule 19 `[R-ONE-MECH]`). Threaded through `assembly.py`
(3 sites) **and `scripts/run_calibration.py::run_year`**, whose inlined
`fleet_to_bins(load_fleet_from_csv(...))` is the nyiso-89 inert-flag defect
class; a test parses that file and asserts every call forwards it.
`CHP_STEAM_CREDIT_HR_CORRECTION_ISOS` is **unchanged** — MISO is NOT added, and
the 1.8× topping factor is NOT armed (miso-98 §7 DO-NOT-REDO).

---

## 3. PRE-REGISTERED PREDICTION — written and committed BEFORE any arm was read

The prompt's pre-registration assumed the CEMS route's coverage (83.2 % CC_CHP
/ 10.4 % CT_CHP). **This mechanism's coverage is different and the prediction is
restated against the actual numbers**: CC_CHP 81.8 %, CT_CHP **37.2 %** — still
asymmetric in the helpful direction, but CT_CHP is reached ~3.6× harder than the
prompt assumed, so the predicted CT_CHP degradation is correspondingly larger.

Post-miso-98 residual: **CC_CHP +11.8 / +11.1 % (over)**, **CT_CHP −33.3 /
−32.9 % (under)** (2023 / 2024; 2025 is skipped by the scorer for the miso-97
§2.2 coverage trap).

1. **CC_CHP improves materially.** 81.8 % of the class MW gets 37 % dearer
   (6.70 → 9.16), which pushes it down the merit order. Direction: the +11.8 /
   +11.1 % over-run shrinks.
2. **CT_CHP degrades**, and by more than the prompt's framing implied. 37.2 %
   of the class MW gets 48 % dearer (6.39 → 9.43) against a class already
   under-running by a third. **A CT_CHP degradation is NOT grounds to revert**
   (rules 1 `[R-STRUCT]` / 14 `[R-ACCURATE]`): the credited rate is measurably
   the wrong quantity, validated to 1e-7 against metered fuel, while non-CHP
   classes measure 0–3 % accurate on the same pipeline.
3. **Prices rise.** Withdrawing 6.7 GW of artificially-cheap thermal from the
   bottom of the stack lifts λ. C3a is currently **−2.5 / −7.8 / −15.4 %**
   (under), so this should help — but C3b is the **kill guard**: miso-98b
   passes it at **0.198 against a ≤ 0.20 bound**, so it can flip back, and
   **if it does that will be reported as a FAIL, not explained away**.
4. **C3a-2025 / C3c / C7 are expected to remain the blocking criteria** — they
   decided miso-98b and none of them is a CHP-cost story.
5. **Non-CHP classes** move only as an indirect merit/price response. CT_PEAKER
   and CC_REGULAR picking up the displaced CHP energy would be the coherent
   story; a large move in COAL_LIGNITE or ST_GAS would want naming.
6. **No peer ISO may move at all.** The artifact is MISO-only and the gate is
   default-off, so any peer movement is a bug in the arm, not a result.

---

## 4. RESULTS

### 4.1 The control is an EQUALITY check, not structural agreement

miso-98 could only claim its A arm *structurally agreed* with the keeper
(post-CAMPD-envelope drift). Here arm A reproduces
`2026-07-27-miso-98b-sectormeasured` **exactly — 0.0000 % on all 17 classes in
2023, 2024 and 2025.** So every arm-B movement below is fully attributable to
the single flag. Two further invariants were **measured, not assumed**:

* all **nine** `shared_inputs` hashes are byte-identical across the arms after
  both `--rebuild-benchmark` runs;
* the **benchmark is identical on all 21 class-year rows** — §5's claim that a
  heat rate cannot move `_btm_frame` holds, so the miso-98 §5 shared-`bench/`
  trap cannot bite this A/B.

### 4.2 Criteria — identical verdicts, C3a better every year, nothing regresses

| criterion | arm A (off) | arm B (on) | |
|---|---|---|---|
| C1 fuel-mix | PASS | PASS | unchanged |
| C2 system volume | PASS | PASS | unchanged |
| **C3a mean LMP** | −6.4 / −10.2 / **−15.4** % | −5.4 / −9.1 / **−14.3** % | **better every year** |
| **C3b price shape** | **PASS** | **PASS** | **kill guard HELD** |
| C3c price tail | 1 / 6 / 0 h vs 30 / 37 / 88 | **bit-identical** | untouched |
| C4 dispatch corr | PASS | PASS | unchanged |
| C7 diurnal (D-1) | FAIL COAL_PRB | FAIL COAL_PRB | unchanged, unrelated |
| C8 forced share | PASS | PASS | unchanged |
| **determination** | NOT-YET | NOT-YET | C3a-2025 / C3c / C7 decide both |

C3b was the pre-registered kill guard — miso-98b passes it at 0.198 against a
≤0.20 bound and **could** have flipped back. It did not. C3c being
*bit-identical* is reported as what it is: a CHP cost change does not reach the
scarcity tail. It is not evidence of improvement.

*(Arm A is an unattested control probe, so its C3a/C3c render as raw FAIL
rather than the ledgered CAVEAT arm B carries. The underlying numbers are the
ones tabulated above; the ledger is inherited unchanged at 2/3.)*

### 4.3 Class energies — the pre-registered lines

| class | year | A err | B err | \|err\| move |
|---|---|---|---|---|
| **CC_CHP** | 2023 | +11.8 % | **−9.8 %** | **−2.0 pp** |
| **CC_CHP** | 2024 | +11.1 % | **−10.1 %** | **−1.0 pp** |
| **CC_CHP** | 2025 | +31.7 % | **−4.9 %** | **−26.8 pp** |
| **CT_CHP** | 2023 | −33.3 % | **−38.4 %** | **+5.1 pp** |
| **CT_CHP** | 2024 | −32.9 % | **−37.8 %** | **+4.9 pp** |
| **CT_CHP** | 2025 | +15.7 % | +6.2 % | −9.4 pp |
| CC_REGULAR | 23/24/25 | −5.4 / −1.5 / −5.9 | −4.2 / −0.2 / −4.0 | better ×3 |
| CT_PEAKER | 23/24/25 | −14.4 / −2.5 / −1.8 | −10.7 / +1.3 / +2.7 | better ×2 |
| COAL_LIGNITE | 23/24/25 | −12.5 / −19.3 / −6.7 | −11.7 / −18.9 / −5.9 | better ×3 |
| COAL_PRB | 23/24/25 | +0.7 / +0.8 / +4.7 | +1.5 / +1.4 / +5.6 | worse ×3 (≤0.9 pp) |
| ST_GAS | 23/24/25 | +16.2 / −8.3 / +6.8 | +17.6 / −7.3 / +8.0 | mixed, ≤1.4 pp |

**§3's prediction 1 holds and then some**: CC_CHP's absolute error falls in all
three years, including a 26.8 pp improvement in 2025. **Prediction 2 holds**:
CT_CHP degrades in 2023/2024, by ~5 pp, and it is **not** grounds to revert
(rules 1 / 14) — the credited rate is measurably the wrong quantity, validated
to 1e-7 against metered fuel, while non-CHP classes measure 0–3 % accurate on
the same pipeline. **Prediction 3 holds**: prices rise (mean system price
31.458 → 31.818 in 2023, 28.863 → 29.214 in 2024) and C3a improves. **Prediction
5 holds**: the displaced energy goes to CC_REGULAR, imports, CT_PEAKER and
COAL_PRB — the merchant continuum that actually served it.

Year-over-year the class response is stable (CC_CHP −19.3 / −19.1 %, CT_CHP
−7.6 / −7.3 % of arm A's energy in 2023 / 2024), which is what a measured input
carrying no per-year parameter should look like.

### 4.4 THREE adverse movements, reported not smoothed

1. **CT_CHP's C1 fit degrades** in 2023/2024 (above) — pre-registered.
2. **CC_CHP's diurnal AMPLITUDE overshoots.** D-1 `cv` 0.026 → 0.141 against an
   actual 0.066, so `cv_ratio` 0.392 → 2.132 (2023), 0.473 → 3.058 (2024),
   0.737 → 2.713 (2025). The class was too flat and is now too peaky.
3. **CT_CHP's profile correlation degrades**: `profile_r` 0.768 → 0.652,
   0.084 → **−0.104**, 0.627 → 0.171.

Against that, **CC_CHP's profile correlation improves** (0.959 → 0.989,
0.980 → 0.986, 0.860 → 0.965). Neither CHP class is D-1-gated (the gate covers
CT_PEAKER / ST_GAS / COAL*), so no gate moves — but all three are real and are
the named open items, not caveats absorbed into the ledger.

**COAL_PRB's D-1 FAIL and MISO ST_CHP's −0.79 profile anti-correlation are
UNCHANGED by this delta** (−0.795 → −0.797, −0.763 → −0.762, −0.801 → −0.771),
which independently confirms both are orthogonal to CHP heat rates — relevant
to the ST_CHP shape lane, which should not expect this mechanism to have moved
its signal.

### 4.5 A blocker fixed in shared infrastructure, on the way

Registering on post-fix main crashed in `render_calibration_html.build_payload`
with `IndexError: index 11 is out of bounds for axis 0 with size 11`.
`bench_multiclass.map_e923_to_model_classes` (PR #3062) is length-agnostic and
fell back to a **12**-vector when a plant has no EIA-923 rows, while the render
path builds 13-vectors `[annual, m01..m12]` and slices `[1:]` for twelve months.
A multi-class plant absent from EIA-923 therefore yielded an 11-month array.
Fixed with an explicit `empty_len` (default 12, so every existing caller is
byte-unchanged; the render site passes 13) plus three regression tests. **This
was not specific to miso-99 — it would block registration for any ISO carrying
such a plant.**

---

## 5. SOLVE HYGIENE

* Four clean partitions regenerated before the chain
  (`capacity-deliverability` MISO 776 rows, `ramp-capability` MISO 991 rows;
  `transfer-interface-limits` is PJM-only and `winter-fuel-inventory`
  ISONE-only in the current registries, both regenerated for the ISOs that
  have them). Every solve log carries the healthy miso-93 tell:
  `MISO 2023: seasonal CIL/CEL interface caps on 5 zone group(s) … static
  summer fallbacks replaced`.
* `--reuse-solved` NOT used (miso-98 §8 — OOM at 15.9 GB on the assembly
  stage). One process per year into one bundle dir, reassembled with
  `scripts/probes/pjm119_merge_year_chain.py`, then `--rebuild-benchmark`.
* **The benchmark does not move between the arms.** `_btm_frame` is EIA-923
  class totals × measured host shares; a heat rate does not enter it. The
  miso-98 §5 shared-`bench/MISO/<year>.json.gz` trap therefore cannot bite this
  A/B — asserted by comparing `btm.parquet` across the arms, not assumed.
* Rule 22 `[R-HOLDOUT]`: 2023–2025 only, MISO freeze active, no marker.
* Rule 16 `[R-ALLYEARS]`: all three years, fresh, in one bundle per arm.

---

## 6. DO-NOT-REDO

* Deriving a CHP-specific gross→net / station-service ratio from
  `net923 / gross_CEMS` (§1 — the unit sets differ by up to 3.3× in both
  directions at a cogen; the ratio is not a station-service ratio and
  caiso-128's `clip(1.0, 1.35)` is what was holding it together).
* Re-deriving CHP heat rates from CAMPD `heatInput / grossLoad`
  (§1.4 — at a CC cogen CEMS's gross-load channel omits the steam turbine, so
  the "measured" rate is the bare GT rate; Midland 11.23 vs the correct 8.82).
* Re-validating that eGRID's `PLHTIAN + CHPCHTI` reproduces metered CEMS heat
  input (§1.2 — 1.00000 median, 22/25).
* Applying the add-back to `ST_CHP` or to any plant above the unfired-topping
  thermal share (§1.3 — 435 MMBtu/MWh on a back-pressure cogen).
* Adding MISO to `CHP_STEAM_CREDIT_HR_CORRECTION_ISOS` / arming the 1.8×
  topping factor (miso-98 §7, unchanged — and now superseded where the
  measurement covers).
* Treating a plant with `CHPCHTI = 0` as under-priced (Primient 64854, Holland
  59093: eGRID applied no credit, the incumbent rate is already the power-only
  rate, and the old CEMS derive's +68 % "over-correction" there was the derive's
  error, not eGRID's).
