# FINDING — ERCOT-112 Task-B prerequisites: the wind bound is sound; the error is a curtailment **tilt**

**Date** 2026-07-25 · **ISO** ERCOT · **Years** 2023–2025 · **No LP** ·
**Probe** `scripts/probes/ercot112_wind_basis_audit.py` ·
**Keeper read** `results/calibration/ercot_netrev_margin/hourly/class_hourly_*.parquet` (rule 15 — no re-solve)

Both cheap prerequisites the ERCOT-112 charter put ahead of the wind-shape lane come back
**clean**, and together they change what the wind lane can be expected to buy.

## 1. Prereq (a) — `ercot_wtx_curtailment_driver` does **not** double-count. Premise refuted.

The charter's concern was that "the EIA-930 wind bound is DELIVERED output", which would make the
West/Panhandle curtailment ceiling a *second* curtailment on an already-curtailed series.

Measured: **all three ERCOT backcast years take the HSL branch**, not the EIA-930 delivered branch.

| year | CF branch that fires |
|---|---|
| 2023 | HSL (uncurtailed potential) |
| 2024 | HSL (uncurtailed potential) |
| 2025 | HSL (uncurtailed potential) |

`data/raw/ercot-hsl/ercot_{2023,2024,2025}_hsl_hourly.parquet` all exist, so
`renewables._hsl_cf_profile` returns non-`None` and the delivered-output fallback
(`_eia_hourly_cf_profile`) is never reached. The bound the LP sees is **uncurtailed potential**, so
a curtailment ceiling on top of it is the correct construction, not a double count.

Two supporting facts:
* The forecast gross-up at `renewables.py:2061` is gated `not is_backcast` — it cannot fire in a
  keeper backcast at all.
* The bound sits **above** delivered actual in every quintile of every year (+4 % to +10 %), which
  is exactly the HSL-minus-delivered curtailment headroom the LP is supposed to re-curtail into.

**Verdict: no defect. The driver stays as-is.** (Rule 14 — it is a measured input; nothing here
would justify weakening it.)

## 2. Prereq (b) — the CF round-trip is **exact**. No capacity-vintage bug.

The bound is built `MW -> CF -> MW`: `_mw_to_cf` divides by the month's online capacity and
`_distribute_by_eia860` multiplies back by December capacity times the vintage ramp. Those legs
cancel to a single scale factor `installed_mw / monthly_capacity[:, -1].sum()`, and in **backcast**
mode `installed_mw` is *set* to `monthly[:, -1].sum()` (`renewables.py:2019-2020`). Measured:

| year | EIA-860 Dec cap | round-trip factor | source HSL | rebuilt bound | delta | hours clipped at CF=1.0 |
|---|---|---|---|---|---|---|
| 2023 | 36,980 MW | 1.000000 | 114.044 TWh | 114.044 TWh | +0.000 % | 0 / 8760 |
| 2024 | 38,715 MW | 1.000000 | 118.710 TWh | 118.706 TWh | −0.004 % | 1 / 8760 |
| 2025 | 40,382 MW | 1.000000 | 123.694 TWh | 123.694 TWh | −0.000 % | 0 / 8760 |

The only leak available — the `_CF_MAX = 1.0` clip inside `_mw_to_cf` — costs **0.005 TWh in one
hour of 2024** and nothing in the other two years.

**Verdict: no defect. The vintage matches by construction.**

## 3. What the prereqs reframe — the annual LEVEL is already right

The charter's motivating numbers (+7.0 % at the lowest actual-wind quintile, −2.1 % at the highest)
are reproduced exactly from the keeper's committed hourlies, and extended to all three years:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| model wind dispatch | 108.41 TWh | 112.33 TWh | 116.80 TWh |
| actual (EIA-930) | 107.99 TWh | 111.54 TWh | 115.12 TWh |
| **annual error** | **+0.4 %** | **+0.7 %** | **+1.5 %** |

Per-quintile of actual wind (model dispatch vs actual):

| quintile | 2023 | 2024 | 2025 |
|---|---|---|---|
| Q1 (lowest wind) | **+7.0 %** | +5.5 % | +3.7 % |
| Q2 | +3.5 % | +3.6 % | +2.7 % |
| Q3 | +1.8 % | +2.1 % | +2.0 % |
| Q4 | −0.4 % | +0.2 % | +1.6 % |
| Q5 (highest wind) | **−2.1 %** | −1.4 % | +0.2 % |

The annual level is within 0.4–1.5 %. What is wrong is a **monotone tilt**: the model curtails too
*little* at low wind and too *much* at high wind. The Q1→Q5 spread narrows year over year
(9.1 pp → 6.9 pp → 3.5 pp). Because scarcity hours are low-wind hours (8,183 vs 12,327 MW annual
mean), the Q1 end of that tilt is what over-supplies the grid exactly when it is short.

## 4. The consequence for the wind-shape lane — bounded, and worth stating before the solve

`_redistribute_preserving_total` (`renewables.py:1769-1800`) preserves the capacity-weighted ISO
aggregate **exactly, every hour**. A per-zone wind SHAPE therefore **cannot change the annual bound
or the system wind series at all** — it can only change *which zone* holds the wind.

That is not an argument against the lane; it is the correct scoping of it. The tilt in §3 is a
curtailment-*timing* error, and per-zone shape is precisely the channel that decides curtailment
timing: it changes how much wind sits behind the West/Panhandle congestion ceiling and the
transmission limits in any given hour. So the hypothesis is well-posed —

* **what it can move:** the hour-by-hour split of wind between the Panhandle nocturnal jet and the
  Gulf coastal sea breeze, hence when the corridor ceiling and the zonal links bind, hence the
  Q1/Q5 tilt;
* **what it cannot move:** annual wind energy, or the ISO-wide bound in any hour.

Anyone scoring this lane on annual wind TWh will measure zero by construction. It must be scored on
the **quintile tilt** and on the scarcity-hour cheap-stack surplus.

## 5. Data + tooling landed here (inert — no keeper change)

* `scripts/data/build_miso_wind_shape.py` generalized with `--iso` (MISO default and MISO output
  byte-unchanged; 30/30 `tests/test_renewables.py` pass). Fixed a latent MISO-only assumption on
  the way: the EIA-930 hourly clock is keyed by **BA code**, not ISO name, so the ISO name was
  being passed straight through — correct only because `MISO` is its own BA code. Now resolved via
  the shared `ISO_TO_BA_CODE` crosswalk (`ERCOT -> ERCO`, `CAISO -> CISO`).
* `market_sim.config.paths.WIND_SHAPE_DIRS` / `wind_shape_dir(iso)` — per-ISO registry, no
  `if iso ==` ladder. An unregistered ISO returns `None` (no-op).
* `data/raw/ercot-wind-shape/ercot_{year}_wind_zone_shape.parquet` — built from NASA POWER
  hourly `WS50M` (MERRA-2) at EIA-860 ERCOT wind-plant locations. ERCOT wind plants map across six
  model zones (West 89, South 44, North 40, Panhandle 33, Houston 2, South_Central 2; Northeast has
  none and takes the documented placeholder).

**This data is inert.** `renewables._WIND_ZONE_SHAPE_ISOS` is still `frozenset({"MISO"})`, so
ERCOT keeps its single ISO-wide profile and the keeper is byte-unchanged. Arming it is a
keeper-affecting change and belongs to **ercot-113** behind its own gate and probe — not to a
session whose primary deliverable was the coal gate.
