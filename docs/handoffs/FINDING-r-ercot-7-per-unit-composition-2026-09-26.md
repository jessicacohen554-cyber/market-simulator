# FINDING — R-ERCOT-7: the per-unit window × partial composition, and the fleet-coverage repairs (zero LP)

**Session:** R-ERCOT-7, 2026-09-26.
**Keeper:** `2026-09-25-r-5-hour-grain` (bundle `results/calibration/r_ercot5_hourgrain_span`, 2019–2025), unchanged. Preconditions checked on `main`: `keepers/ERCOT.json` names it, and the R-ERCOT-6 RESULT is merged (`bfc3dd3a` is an ancestor of `main`).
**LP spent:** none. 35 instrumented `fleet_only` rebuilds of the keeper recipe: 7 years × {keeper on new code, keeper on `main`, D, D2}, plus the 7 keeper caches the comparer reads.

## Headline

- **ERCOT stays CALIBRATED. No arm was run.**
- **The per-unit composition fails its pre-stated test.**
  - The test was to beat R-ERCOT-6's B on the ≤ own-CEMS share of the coal lift.
  - The committed attribution supports two zero-parameter builds, D and D2. Both restore **more** coal capability than B in every year, and both have a **lower** ≤ CEMS share in every year.
  - The extra over B is almost entirely **above** CEMS.
- **The R-ERCOT-6 diagnosis is not what drives B's lift.**
  - That diagnosis: B over-restores because `min()` drops *other* units' plateau at a shared hour.
  - If that were the dominant case, removing each unit's downtime once would restore *less* than B. It restores more.
  - The dominant case is different. At most shared hours the plateau is carried **only** by the windowed unit(s), and the plant plateau reads **deeper** than the window.
    - B's `min()` keeps that extra depth.
    - A per-unit split drops it, because no attributed unit explains it.
- **Step 2.** One repair has a material footprint and a cited source: **Jack Fusco / Brazos Valley (55357)**.
  - It is an ERCOT resource in ERCOT's own 60-Day DAM disclosure: `BVE_CC1_1/_2`, QSE `QCALP`, 2023–2026.
  - It is missing from the fleet: ~602 MW net-summer CC in Fort Bend (Houston), 2.4–3.8 TWh/yr gross CEMS.
  - The other three repairs are small, or matter only in validation years.

## 1. The per-unit composition (Step 1)

### Construction

**Rule 19 check.** No existing field can carry this construction:
- `ercot_dam_availability_event_cap_unit_scoped` (R) is `min()` at shared hours. Re-defining it would silently change the meaning of every registered config that carries it.
- So the construction is a new default-off field, `ercot_dam_availability_event_cap_per_unit`.
- It is **mutually exclusive** with `unit_scoped`, and a `ValueError` at the point of use enforces that.

It changes only the window × partial seam inside the ERCOT-148/149 precedence cap (`fleet/arrays.py`):

    f_p*(t) = 1 − (1 − f_p(t)) · Σ_{u not windowed} d_u(t) / Σ_u d_u(t)      (D)
    ceiling = f_w(t) · f_p*(t)

- `f_p` is the keeper's own plant plateau: shaped, day-guarded, class grain.
- `d_u` is the carrying unit's own measured deficit, `(1 − ceiling_ratio) × unit_capacity_mw`. It comes from `campd-partial-outages-units.csv`, the frozen ercot-174 attribution, with no new constant (rule 23).
- A unit is "windowed" when it sits inside a ≥ 5-day or short (coal + gas, hour-grain) full stop, i.e. the same window family the ceiling multiplies in.
- An unattributed plateau keeps the product (fail-safe).
- `product ≤ D` pointwise.
- The new helpers are `outages.partial_outage_unit_deficits`, `unit_outage_short_active_units` and `per_unit_partial_factor`.

**D2, a pre-declared sensitivity** (probe only, `--variant resid`). It keeps plateau depth that no carrying unit explains:

    f_p*(t) = 1 − max(0, (1 − f_p) − Σ_{u windowed} d_u / cap_bin)

**Unit-grain partial layer.** The handoff named `unit_partial_outage_derate_factors`, but it cannot serve here:
- It reads `campd-partial-outages-ERCOT.csv`, which does not exist.
- The units CSV's `derate_factor` is the **plant's** factor repeated per unit, so feeding that file to the accumulator would apply a plant factor to unit capacity.
- `ceiling_ratio` is the only unit-grain depth in the data.

### A/A null

The flag off on this branch is **byte-identical to `main`** on all 242–251 stage arrays in each of the 7 years:
- `pre`, `dam`, `fin`, every `W`/`S`/`P`/`D` layer, `pmax`, `mc`, `min_gen`;
- compared as raw bytes, which is NaN-safe.

### Census, coal (TWh; B from FINDING-r-ercot-6 §1, same method and keeper)

| year | lift B / D / D2 | ≤ CEMS B / D / D2 | ≤ CEMS share B / D / D2 | gap after B / D / D2 (from A) | in-merit B / D / D2 | keeper coal vs actual |
|---|---|---|---|---|---|---|
| 2019 | 5.13 / 6.25 / 5.34 | 2.72 / 3.00 / 2.77 | **0.53** / 0.48 / 0.52 | 1.11 / 0.83 / 1.07 (3.83) | 3.43 / 4.11 / 3.57 | −14.03 |
| 2020 | 4.21 / 5.11 / 4.34 | 1.58 / 1.69 / 1.56 | **0.38** / 0.33 / 0.36 | 0.63 / 0.52 / 0.65 (2.21) | 1.89 / 2.25 / 1.93 | −16.96 |
| 2021 | 6.41 / 6.86 / 6.57 | 3.70 / 3.63 / 3.64 | **0.58** / 0.53 / 0.55 | 0.97 / 1.04 / 1.03 (4.67) | 5.47 / 5.86 / 5.63 | −3.35 |
| 2022 | 4.26 / 4.43 / 4.31 | 2.52 / 2.50 / 2.49 | **0.59** / 0.56 / 0.58 | 0.79 / 0.80 / 0.81 (3.30) | 3.68 / 3.79 / 3.73 | **+4.78** |
| **2023** | 3.67 / 4.40 / 3.93 | 1.04 / 1.01 / 1.02 | **0.28** / 0.23 / 0.26 | 0.69 / 0.73 / 0.71 (1.73) | 1.84 / 2.13 / 1.95 | −2.40 |
| **2024** | 5.04 / 5.47 / 5.18 | 1.96 / 1.98 / 1.92 | **0.39** / 0.36 / 0.37 | 0.79 / 0.78 / 0.83 (2.75) | 2.99 / 3.18 / 3.05 | −1.93 |
| **2025** | 4.23 / 4.76 / 4.28 | 2.15 / 2.24 / 2.11 | **0.51** / 0.47 / 0.49 | 0.71 / 0.63 / 0.75 (2.86) | 3.34 / 3.71 / 3.37 | **+1.23** |

- **D − B:** lift +0.17 to +1.12 TWh/yr, of which the ≤ CEMS part is −0.07 to +0.28. The increment is 75–100 % above CEMS.
- **D2 − B:** lift +0.05 to +0.26, ≤ CEMS −0.06 to +0.05.
- **In-merit lift** exceeds B's in every year, so the risk that coal is added where it already runs over actual (2022, 2025) is larger, not smaller.
- **Scarcity-hour / top-100 MW** (D): 76 / 68 (2019), 0 / 164 (2020), 444 / 442 (2021), 235 / 192 (2022), **70 / 99 (2023), 485 / 247 (2024), — / 163 (2025)**. These are the same order as B's.
- **CC_REGULAR lift (D):** 0.58–1.84 TWh/yr, 0.35–0.97 of it ≤ CEMS. This is close to B's.
- Full output: `docs/handoffs/r-ercot/r_ercot7_perunit_seam.txt`.

### Reading

- **On direction, any construction that removes this double count adds cheap coal.** In the train years that lowers prices:
  - C3a already reads −7.5 / −5.6 / −6.9 %;
  - 2023 has ~2.5 pts of headroom before −10 %;
  - R-ERCOT-6's B, with a smaller lift, took 2023 to −10.6 % and 2024 to −10.3 %.
- **On structure (rule 1), the per-unit composition is not the better construction on this data.** The attribution is thresholded:
  - a unit "carries" a plateau only if its own ceiling falls below `_CEILING_FRAC`;
  - so plateau depth from units with smaller deficits, or from basis differences, belongs to no unit.
  - At a shared hour, the exact split therefore cannot tell "the windowed unit's downtime, counted twice" from "extra depth nobody's ceiling explains".
  - B keeps that depth; D drops it; D2 roughly keeps it, and lands close to B.
- **What a true per-unit composition would need.** A complete per-unit deficit decomposition of each plateau (every unit's deficit, not thresholded). That means re-deriving the units extract under rule 23, which needs its own charter, and no residual may motivate it.
- **Recommendation:** do not arm D. Record the field as **R** (zero-LP, failed its pre-stated test). The window × partial family has now been measured four ways (product, blanket `min`, unit-scoped `min`, per-unit). Close it unless a complete unit decomposition is derived.

## 2. Fleet-coverage repairs (Step 2), proposed and not implemented

| plant | what is wrong | cited source | zero-LP footprint | train-year reach |
|---|---|---|---|---|
| **Jack Fusco / Brazos Valley (55357)** | absent from the fleet entirely | ERCOT 60-Day DAM Gen Resource Data (`data/raw/ercot/60_DAY_DAM_DISCLOSURE_…`, 19 files 2023–2026): `BVE_CC1_1/_2`, SP `BVE_CC1`, QSE `QCALP` (Calpine), DAM awards 0.25–1.14 TWh per file; EIA-860 NERC `TRE`, county Fort Bend. The BA field `MISO` is the outlier. `ercot-dam-plant-crosswalk.csv` already carries `BVE_CC1` (p98 613 MW) but mis-matched to Lost Pines 55154, `accepted=0` | EIA-860 602 MW net summer (CTG1/2 + STG1), CEMS gross 2.42 / 3.53 / 2.85 / 3.49 / 3.40 / 3.50 / 3.76 TWh (2019–25), gross HR 7.0–7.2 | **yes, all years**: ~600 MW of Houston CC |
| Decker Creek steam 1–2 (3548) | bin sheet has only the 206 MW CT row | EIA-860 retired: unit 1 320 MW (RE 2020), unit 2 404 MW (RE 2022) | CEMS 0.68 / 0.69 / 0.67 / 0.08 TWh (2019–22), HR 11.3–12.2 | **none** (retired before 2023) |
| Hidalgo (55545 ↔ CAMPD 7762) | zone `Unknown` → `unknown_zone_default` = South_Central; HR NaN → 7.0 default | EIA-860 Hidalgo County (Southern weather zone); `ercot_noncampd_dam_crosswalk.csv` `DUKE_CC1` | zone move 551 MW South_Central → South; CEMS gross HR 6.81–7.13, so the default is within the measurement | small: a zonal move only |
| Arthur Von Rosenberg (7512 ↔ CAMPD 3612 CT01/CT02) | zone `Unknown`, HR NaN | EIA-860 Bexar County; same coordinates as V H Braunig 3612; CAMPD reports its CTs under 3612 | zone default South_Central **is already correct**; CEMS gross HR 6.73–7.10 (2024 5.9–6.1) ≈ default | ~none |

Notes:
- **Only Jack Fusco is a material train-year repair.** It adds ~600 MW of in-merit CC, which lowers train-year prices.
  - Rule 14 decides it, not C3a.
  - It is a data-intake edit to the curated bin sheet and the DAM crosswalk. The BVE → 55357 match is by name and owner (Calpine), and the owner should confirm it.
- **A side finding, not fixed here.** Hidalgo and AVR *are* in CAMPD, under different facility ids (7762, and 3612 units CT01/CT02). Two consequences follow:
  - Their CAMPD outage windows never reach bins 55545 / 7512.
  - The CAMPD 3612 facility mixes AVR's CC units with Braunig's steam units, so any facility-grain CEMS consumer of 3612 sees both.
  - The fix is a unit-level CAMPD → EIA crosswalk row for each.

## 3. Step 4 (report only)

- **The `derive_campd_unit_outages.py` non-ERCOT `plant_group` break is already fixed on `main`.**
  - Both fleet-map sites (L430, L1668) now go through `artifact_class` (the miso-273 COAL-SUB translation).
  - No action is needed.
- **`campd_bins._APPLIED_MEASURED_FLAGS = {"ok", "eia923_identity"}` is a shared change that is not gated by any flag.**
  - It stays inert for ERCOT only while no ERCOT heat-rate artifact carries `eia923_identity` rows. Today `ercot_campd_marginal_hr_summary.csv` carries 0.
  - Re-check it if any ERCOT HR artifact is re-derived.

## Owner ruling (2026-09-26)

- **Step 1: "Record R, no arm (Recommended)."**
  - `ercot_dam_availability_event_cap_per_unit` is recorded as **R** in the ERCOT matrix shard.
  - The default-off field stays in code as the tested record.
  - No LP was spent, and the keeper `2026-09-25-r-5-hour-grain` is unchanged.
- **Step 2: "Add Fusco, test in next lane (Recommended)."**
  - A follow-up lane adds Jack Fusco / Brazos Valley (55357):
    - the bin-sheet row;
    - the `BVE_CC1` DAM crosswalk re-match from Lost Pines 55154 to 55357.
  - It then tests the addition under a PRECOMMIT with 7 one-year shards.
  - Decker Creek steam, Hidalgo's zone and AVR ride along with separable attribution.
