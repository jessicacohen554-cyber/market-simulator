# FINDING miso-99 — the CHP heat-rate correction is UNBLOCKED: the gross→net basis miso-98 §6.1 could not obtain is **not needed**, because eGRID publishes the steam credit it removed (`CHPCHTI`) and adding it back lands on the model's own NET denominator

**Status: STEP 1 + STEP 2 COMPLETE, STEP 3 A/B IN FLIGHT.** Keeper
`2026-07-27-miso-98b-sectormeasured` unchanged pending the arms.

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

*(pending — the six year-solves are in flight; this section is written after
the arms are read, and §3 above is frozen.)*

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
