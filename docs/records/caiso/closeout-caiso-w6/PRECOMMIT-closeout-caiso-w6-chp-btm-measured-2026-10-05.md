# PRECOMMIT closeout-CAISO-w6: measured CAISO CHP behind-the-meter share (2026-10-05)

**Charter (desk, 02:44Z).** Take the `chp_btm_measured` lever (U in CAISO): replace the sector-default
`chp_btm_pct` with measured EIA-923 Schedules 6/7 CHP on-site use. Phase-0 its reach on C1 CC_REGULAR
2020. If it reaches T1, PRECOMMIT and 7 legs on w3; if not, record it and stand down.

**Build.**
- The solve surface lands at `a7100366` on `claude/closeout-caiso-w6`.
- `15c13cd8` is an AST-identical ruff format of the test.
- Every shard pins the commit that carries this PRECOMMIT. Its full SHA is in the launch table, Addendum A.

## 1. Mechanism and identification

**What the share does.** Under the keeper's `chp_steam_following`, a CHP bin's LP capacity is
nameplate × (1 − BTM share), and its steam floor is scaled by the same factor (`data/fleet/assembly.py`).
The withheld share is reported as behind-the-meter (BTM) generation, and the benchmark subtracts the same
share × EIA-923 net generation from the class actual (`_btm_frame`).

**Demand is not touched.** CISO-metered load already excludes host load served on site. The share
therefore decides how much of a CHP plant's output the LP can sell to the grid, and so how much
in-market gas (mostly CC_REGULAR) has to cover the remainder.

**The incumbent share is a sector default:** merchant 35 / industrial 70 / commercial 65 %, plus
thermal-tranche overrides. Its own constant comment calls it residual-identified.

**Measured share** (`scripts/data/derive_caiso_chp_btm_share.py` →
`data/raw/_processed-legacy/chp_btm_share_measured_CAISO.csv`, rule 23):
- Formula: `100 × clip(1 − (sales for resale + tolling + outgoing) / (gross − station use))`, pooled over
  CY2022–2024 (the nyiso-147 window).
- Source: each plant's own EIA-923 Schedules 6/7 disposition filing (`data/raw/eia-923-disposition/`).
- Retail sales count as host supply. This is the conservative reading: a non-utility cogen's retail
  customer is its co-located host, as for Watson → the Carson refinery and Los Medanos → the Pittsburg
  steel works.
- Plants absent from Schedules 6/7 keep the default.
- Rule 13: the filing regenerates every year and responds to changed host arrangements, so a forward
  year can derive the same quantity.
- Rule 14: the plants' own filings refute the default.

| Plant | Default % | Measured % |
|---|--:|--:|
| Watson 50216 | 65 | 34.6 |
| Los Medanos 55217 | 35 | 15.1 |
| Crockett 55084 | 35 | 3.6 |
| Elk Hills 55400 | 35 | 33.7 |
| Richmond 52109 | 65 | 99.7 |
| Martinez Refining 54912 | 70 | 95.4 |
| El Segundo Cogen 10213 | 70 | 95.4 |

**Rule 19.** This replaces the share; it does not stack on it. It is one share with three readers: the
carve, the add-back and the bench subtrahend, which is the nyiso-147 structure. The forecast-only CEMS
`chp-btm-share` datatype is untouched.

**Rule 25.** The field is CAISO-only (`caiso_chp_btm_measured`), and the identity is CAISO's own filing.

**DOF:** zero fitted parameters.

## 2. Zero-LP reach (`_chp_btm_reach_all.json`)

**Method.** For each w3 CHP unit, compute model TWh × ((1 − new)/(1 − old) − 1). This is a capacity-bound
upper bound: in w3 2020 the large CHP units sit at their grid capacity about 86 % of hours.

| Year | CHP grid Δ, upper bound (TWh) | CC_CHP actual Δ (bench) | CC_REGULAR miss, w3 (band) |
|---|--:|--:|--:|
| 2019 | +1.33 | +0.89 | −2.04 (±4.84) |
| **2020** | **+1.59** | +0.87 | **+5.00 (±4.60)** |
| 2021 | +1.95 | +1.01 | +3.47 (±4.83) |
| 2022 | +1.64 | +0.90 | +0.95 (±5.01) |
| 2023 | +1.38 | +0.75 | −1.07 (±5.27) |
| 2024 | +1.42 | +0.69 | −1.67 (±5.29) |
| 2025 | +1.14 | +0.46 | −0.36 (±5.08) |

T1 needs a CC_REGULAR reduction of ≥ 0.40 TWh in 2020 (D1 alone moves it only −0.006). The upper bound
is 1.59, so T1 is reachable if ≥ 25 % of the added CHP energy displaces CC_REGULAR.

## 3. Recipe, bars, kills (ex ante)

**Arm A1** = `closeout_caiso_w1_a2_span` replayed with:
- `caiso_dsw_daytime_lateevening_unprinted_arm=true`;
- `caiso_dsw_clean_depth_own_year=true`;
- `caiso_intertie_unprinted_daily_gas_shape=true` (together, the w3 recipe);
- `measured_ct_heat_rates_crosswalk_remap=true` (D1, the confirmed rule-14 correction);
- `caiso_chp_btm_measured=true`.

D3 and D4 stay out. Seven year-isolated legs.

**Control.** The w3 probe `2026-10-04-closeout-caiso-w3-own` (no control solve; G-DRIFT below).

**Bars.**
- **T1:** C1 CC_REGULAR 2020 |model − actual| ≤ 4.60 TWh.
- **Report** for every year: C1 CC_CHP, CT_PEAKER and ST_GAS, and CHP grid TWh against the §2 upper
  bound.

**Kills.**

| Kill | Condition |
|---|---|
| K1 | any C1 cell PASS → FAIL (all classes, all years). This includes CC_REGULAR 2019, now −2.04 against ±4.84. |
| K2 | C4 gas NRMSE worse than w3 by > 0.02 in any year |
| K3 | C3a worse than w3 by > 1 pp in any year |
| K4 | C8 forced-share breach |
| K5 | C2 leaves its band |
| K6 | 2020 CHP grid TWh exceeds w3 + 1.59 + 0.20. That would mean the carve does more than the identification allows, so stop and diagnose. |

**Decision rule.**
- T1 met and K1–K6 clear: request a promotion slot from the desk. The render leg (§5) has to be ruled
  on first.
- T1 missed: record the result, set the matrix cell, stand down.

**Scoring basis.** The CC_CHP actual moves with the measured bench subtrahend.
- For a like-for-like comparison, w3's CHP C1 cells are recomputed zero-LP on the same measured
  subtrahend.
- CC_REGULAR, CT_PEAKER and ST_GAS actuals are not touched by the CHP share.

## 4. G-DRIFT (`d24bd6aa` → build, backcast path)

The diff contains only this lane's w6 hunks:

| Hunk | Classification |
|---|---|
| `data/fleet/assembly.py` (carve) | **INERT off.** The measured branch runs only under `chp_btm_measured_armed`, and the NYISO path is behaviourally identical. |
| `data/chp.py` (three new functions) | **INERT** (new code, called only from the above) |
| `config/paths.py` (two constants) | **INERT** |
| `config/scenarios.py` (field, default off, cache key optional at default) | **INERT** |
| `run_calibration_full._btm_frame` | **LP-INERT; scoring-LIVE for CAISO.** The bench column `btm_bench_twh` now reads the CAISO artifact whenever it exists (nyiso-149), and the run column follows the flag. This is handled by the §3 scoring basis. |
| `build_bench_part_zero_lp.py`, `derive_*`, `fetch_*` | **INERT** for the solve |

No LIVE solve hunk, so no control solve.

## 5. Declared side effects

1. **Bench subtrahend (CAISO).** Every CAISO registration from this SHA subtracts the measured CHP BTM
   (CC_CHP ≈ 4.3–5.0 TWh/yr instead of ≈ 6.9–7.4). The CC_CHP actual rises by about 0.5–1.0 TWh/yr (§2).
   This is a reference-construction change in the same family as the D2-c ruling the desk is taking to the
   owner.
2. **Render leg held back.** `render_calibration_html.py` also reads the measured share:
   - for the per-plant BTM fields;
   - for the CAISO gas-family cogen anchor (`EIA930_NG_CELL_CORRUPT`, C2 basis);
   - for the run-side add-back.

   That file is a bench `PAYLOAD_SOURCES` member. Any semantic edit to it moves the payload fingerprint
   of every ISO's committed bench part (`test_bench_stamp_payload::test_d`), which is a cross-ISO re-stamp
   event. The edit is therefore held as `_render_leg_pending.patch` and is not committed. Until it lands,
   a CAISO render under the flag computes the C2 cogen anchor and the per-plant BTM fields on the sector
   default, while the class subtrahend uses the measured share. The RESULT will state which cells that
   touches. **A promotion needs the render leg**, so it needs a desk/owner-scheduled bench re-stamp.
