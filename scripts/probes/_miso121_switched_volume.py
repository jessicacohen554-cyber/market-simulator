#!/usr/bin/env python3
"""miso-121 — switched-volume (K7) and the LITERAL L5 marginality test.

The Phase-0 screen could only report the model's binding **tranche**-hours
against CAMPD's observed **unit**-hours — different grains, which is why
PREREG §8.3 made K7 reported-only with no ratio between the columns. The
Phase-1 bundles carry ``hourly/unit_hourly_<year>.parquet`` (``plant_code``,
``plant_group``, ``mw``, ``cap_mw`` at P1), which the older keeper bundle does
not, and that makes two things measurable that the prereg had to defer:

* **K7 at a comparable grain** — the model's switched generation (MWh
  dispatched by capable units in hours where their delivered gas price exceeds
  oil parity) against **CAMPD's own** observed switched generation (grossLoad
  summed over gas-labelled unit-hours whose measured CO2 intensity sits in the
  distillate band). Both are "MWh produced by a dual-fuel gas unit while
  burning oil". This is REPORTED, never a gate — but it is now an honest
  comparison rather than two incomparable columns.
* **L5 exactly as PREREG §5.2 wrote it** — restricted to tranches the P1 run
  leaves *partially loaded* (``0 < mw < cap_mw``, i.e. genuinely price-setting)
  rather than the binding-hour p50 substitute §8.1 had to fall back on. The
  control arm is a same-HEAD zero-delta reproduction of the keeper, so its P1
  is the faithful stand-in for "the keeper's own P1" and is *better*, being at
  this session's HEAD.

Rule 22: 2023-2025 only. Rule 23: nothing here is fitted; the capable set, the
oil series and the emission factors are read from measured registries.

    uv run python scripts/probes/_miso121_switched_volume.py \
        --json results/calibration/_miso121_switched_volume.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from market_sim.data.fleet.eia860 import dual_fuel_plant_groups  # noqa: E402
from market_sim.data.fuel._shared import _GAS_FUEL_IDX  # noqa: E402
from market_sim.data.fuel.dual_fuel import dual_fuel_oil_price_series  # noqa: E402
from market_sim.data.fuel.resolve import resolve_fuel_prices  # noqa: E402
from scripts.lib.bundle_fleet import reconstruct_bundle_fleet  # noqa: E402

ISO = "MISO"
YEARS = (2023, 2024, 2025)
ARM_A = REPO / "results/calibration/miso121_control_A"
ARM_B = REPO / "results/calibration/miso121_dualfuel_B"
CAMPD_UNIT_DIR = REPO / "data" / "raw" / "campd-unit-level"

WINTER_MONTHS = (1, 2, 12)
CO2_RATE_OIL_BAND_LO = 70.0
CO2_RATE_OIL_BAND_HI = 80.0
SHORT_TON_KG = 907.18474
_GAS_LABELS = ("Pipeline Natural Gas", "Natural Gas")

#: PREREG §5.2 L5 bar.
BAR_MARGINAL_P50_DOFFER = 0.10


def _binding_by_plant_group(bundle: Path, year: int) -> tuple[dict, dict]:
    """Return ``{(plant_code, plant_group): binding (T,) bool}`` and Δ_offer rows.

    All tranches of one ``(plant_code, plant_group)`` share a zone and a
    per-plant delivered gas series, so the oil-parity comparison is well
    defined at that key — which is exactly the key ``unit_hourly`` carries.
    """
    state, _meta = reconstruct_bundle_fleet(bundle, year, verbose=False)
    fleet = state["fleet_arrays"]
    config = state["config"]
    prices = resolve_fuel_prices(config, fleet, year)
    oil = dual_fuel_oil_price_series(config, year)
    capable = dual_fuel_plant_groups()
    is_gas = np.isin(fleet.fuel_type_idx, _GAS_FUEL_IDX)
    heat = np.asarray(fleet.heat_rate, dtype=float)
    binding: dict[tuple[int, str], np.ndarray] = {}
    doffer: dict[tuple[int, str], np.ndarray] = {}
    for g in np.nonzero(is_gas)[0]:
        key = (int(fleet.plant_code[g]), str(fleet.plant_group[g]))
        if key not in capable or key in binding:
            continue
        delta = prices[g] - oil
        binding[key] = delta > 0.0
        doffer[key] = np.maximum(delta, 0.0) * heat[g]
    return binding, doffer


def _unit_hourly(bundle: Path, year: int) -> pd.DataFrame:
    """P1 unit-hour dispatch for one bundle-year."""
    frame = pd.read_parquet(bundle / "hourly" / f"unit_hourly_{year}.parquet")
    if "pass" in frame.columns:
        frame = frame[frame["pass"] == "P1"]
    return frame


def model_switched(bundle: Path, year: int, binding: dict) -> dict:
    """Model MWh dispatched by capable units in oil-parity (switched) hours."""
    df = _unit_hourly(bundle, year)
    df = df.assign(_key=list(zip(df["plant_code"].astype(int), df["plant_group"])))
    cap = df[df["_key"].isin(binding.keys())]
    if cap.empty:
        return {"capable_twh": 0.0, "switched_twh": 0.0, "switched_share": None}
    # Vectorised lookup: binding[key][hour].
    hours = cap["hour"].to_numpy()
    keys = cap["_key"].to_numpy()
    mask = np.fromiter(
        (binding[k][h] for k, h in zip(keys, hours)), dtype=bool, count=len(cap)
    )
    mw = cap["mw"].to_numpy(dtype=float)
    return {
        "capable_twh": round(float(mw.sum()) / 1e6, 6),
        "switched_twh": round(float(mw[mask].sum()) / 1e6, 6),
        "switched_share": (
            round(float(mw[mask].sum() / mw.sum()), 6) if mw.sum() > 0 else None
        ),
        "switched_unit_hours_dispatching": int((mw[mask] > 0).sum()),
    }


def campd_switched(capable_plants: set[int], year: int) -> dict:
    """CAMPD-observed MWh from gas-labelled units burning in the oil band."""
    want = {str(int(p)) for p in capable_plants}
    cols = [
        "facilityId",
        "unitId",
        "date",
        "grossLoad",
        "co2Mass",
        "heatInput",
        "primaryFuelInfo",
    ]
    frames = []
    for path in sorted(CAMPD_UNIT_DIR.glob(f"*_{year}.parquet")):
        df = pd.read_parquet(path, columns=cols)
        df = df[df["facilityId"].astype(str).isin(want)]
        if not df.empty:
            frames.append(df)
    if not frames:
        return {"observed_switched_twh": None, "note": "no CAMPD rows"}
    df = pd.concat(frames, ignore_index=True)
    df["month"] = pd.to_datetime(df["date"]).dt.month
    win = df[df["month"].isin(WINTER_MONTHS)].copy()
    win = win[win["heatInput"].astype(float) > 0.0]
    win["rate"] = (
        win["co2Mass"].astype(float) * SHORT_TON_KG / win["heatInput"].astype(float)
    )
    gas = win[win["primaryFuelInfo"].isin(_GAS_LABELS)]
    band = gas[
        (gas["rate"] >= CO2_RATE_OIL_BAND_LO) & (gas["rate"] <= CO2_RATE_OIL_BAND_HI)
    ]
    return {
        "observed_switched_twh": round(
            float(band["grossLoad"].astype(float).sum()) / 1e6, 6
        ),
        "observed_switched_unit_hours": int(len(band)),
        "capable_gas_winter_twh": round(
            float(gas["grossLoad"].astype(float).sum()) / 1e6, 6
        ),
        "coverage_note": (
            "CAMPD covers only the capable plants that report to it; this is a "
            "LOWER bound on fleet-wide observed switching"
        ),
    }


def l5_literal(bundle: Path, year: int, binding: dict, doffer: dict) -> dict:
    """PREREG §5.2 L5, restricted to PARTIALLY LOADED (price-setting) tranches."""
    df = _unit_hourly(bundle, year)
    df = df.assign(_key=list(zip(df["plant_code"].astype(int), df["plant_group"])))
    cap = df[df["_key"].isin(binding.keys())].copy()
    mw = cap["mw"].to_numpy(dtype=float)
    capmw = cap["cap_mw"].to_numpy(dtype=float)
    marginal = (mw > 1e-6) & (mw < capmw - 1e-6)
    hours = cap["hour"].to_numpy()
    keys = cap["_key"].to_numpy()
    bind = np.fromiter(
        (binding[k][h] for k, h in zip(keys, hours)), dtype=bool, count=len(cap)
    )
    sel = marginal & bind
    if not sel.any():
        return {"n_marginal_binding": 0, "passed": False}
    d = np.fromiter(
        (doffer[k][h] for k, h in zip(keys[sel], hours[sel])),
        dtype=float,
        count=int(sel.sum()),
    )
    w = capmw[sel]
    order = np.argsort(d)
    cw = np.cumsum(w[order])
    p50 = float(d[order][np.searchsorted(cw, 0.5 * cw[-1])])
    return {
        "n_marginal_binding": int(sel.sum()),
        "n_binding_total": int(bind.sum()),
        "marginal_share_of_binding": round(float(sel.sum() / max(bind.sum(), 1)), 6),
        "capw_p50_doffer": round(p50, 4),
        "bar": BAR_MARGINAL_P50_DOFFER,
        "passed": bool(p50 >= BAR_MARGINAL_P50_DOFFER),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    capable = dual_fuel_plant_groups()
    out: dict = {"iso": ISO, "years": list(YEARS), "by_year": {}}
    print("=" * 78)
    print("miso-121 — K7 switched volume + LITERAL L5 marginality")
    print("=" * 78)

    for year in YEARS:
        binding, doffer = _binding_by_plant_group(ARM_A, year)
        plants = {pc for (pc, _g) in binding}
        row: dict = {"n_capable_plant_groups": len(binding)}
        row["L5_literal_on_control"] = l5_literal(ARM_A, year, binding, doffer)
        row["model_switched_arm_B"] = (
            model_switched(ARM_B, year, binding)
            if (ARM_B / "hourly" / f"unit_hourly_{year}.parquet").exists()
            else {"note": "arm B not solved yet"}
        )
        row["model_switched_control_A_counterfactual"] = model_switched(
            ARM_A, year, binding
        )
        row["campd_observed"] = campd_switched(plants, year)
        out["by_year"][str(year)] = row
        print(f"\n{year}:")
        print(f"  L5 literal: {json.dumps(row['L5_literal_on_control'])}")
        print(f"  model switched (B): {json.dumps(row['model_switched_arm_B'])}")
        print(f"  CAMPD observed:     {json.dumps(row['campd_observed'])}")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(out, indent=2, default=str))
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
