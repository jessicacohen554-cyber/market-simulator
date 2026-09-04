"""caiso-242 ADDENDUM — the derive's OWN round-trip identity, tested against the model as built.

NO LP, NO SOLVE, NOTHING ARMED.

``derive_caiso_offer_surface.py`` states the identity its multipliers are
built to satisfy, verbatim in its own docstring:

    a model tranche prices at  mult x base_HR x gas + VOM
                             + 0.057 x (mult x base_HR) x P_carbon

and it inverts the measured bid against exactly that form
(``denom = base_hr * (gas + CO2_FACTOR * carbon)``, on the **CA-composite
citygate** daily spot).

This probe evaluates BOTH sides of that identity on the committed keeper:

* the **measured bid** the multiplier encodes,
  ``VOM + mult x base_hr x (cg + 0.057 x P)``;
* the **model's actual offer** for the same band, from the rebuilt fleet's
  assembled ``mc`` — which prices fuel at the model's delivered series and
  carbon at the fleet's **measured** emission rate, not at
  ``0.057 x tranche_HR``.

Two independent mismatches are separated and sized:

  L1  GAS INDEX — the CA-composite citygate the multiplier was normalised by
      vs the model's delivered series (EIA N3050CA3 + transport adder).
  L2  CARBON — the ``0.057 x tranche_HR`` the derive assumed the model would
      charge vs the measured ``emission_rate`` it actually charges.

and the affine reconciliation that makes the identity hold is reported per
class: ``mult' = A x mult - B`` with

    A = mean(cg + CO2_FACTOR x P) / mean(model_fuel)
    B = mean(emission_rate x P) / (base_hr x mean(model_fuel))

both coefficients ratios of committed measured series, no free parameter.

Writes ``results/calibration/_caiso242_roundtrip.json``.

Usage:
    PYTHONPATH=.:src uv run python scripts/probes/_caiso242_roundtrip.py
"""

from __future__ import annotations

import contextlib
import importlib.util
import inspect
import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

BUNDLE = REPO / "results/calibration/caiso241_b1_ctpeaker_committed"
MEASURED = REPO / "data/raw/_validation-source/caiso_offer_curve_measured.json"
CITYGATE = REPO / "data/raw/gas-prices/caiso_citygate_daily.csv"
YEARS = (2023, 2024, 2025)
HOURS = 8760
OUT = REPO / "results/calibration/_caiso242_roundtrip.json"

#: The derive's own CO2 factor (t/MMBtu) and per-class VOM, from
#: ``caiso_offer_curve_measured.json::_provenance``.
CO2_FACTOR = 0.057
#: Classes carrying measured-surface bands on the keeper, with the measured
#: bucket each was grounded on (``backcast_config`` `_ungrounded_source`).
CLASS_BUCKET = {
    "CC_REGULAR": "CC_REGULAR",
    "CC_CHP": "CC_REGULAR",
    "CT_PEAKER": "CT_PEAKER",
    "CT_CHP": "CT_PEAKER",
    "ST_GAS": "CT_PEAKER",
}
#: Bands the measured surface arms (the `committed` band is NEVER measured-armed).
MEASURED_BANDS = ("econ_low", "econ_high", "peak")

_spec = importlib.util.spec_from_file_location(
    "_caiso240_default_hr_mult_census",
    REPO / "scripts/probes/_caiso240_default_hr_mult_census.py",
)
CENSUS = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(CENSUS)


def _band(unit_id: str) -> str:
    return str(unit_id).rsplit("_", 1)[-1]


def rebuild(year: int, gas_price: float) -> dict:
    """Rebuild the keeper fleet as recorded (no LP, no flag delta)."""
    from run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    params = inspect.signature(run_year).parameters
    skip = {
        "year",
        "iso",
        "hours",
        "gas_price",
        "ttc_overrides",
        "fleet_only",
        "xyear_cache",
        "must_run_mw",
    }
    kwargs = {k: v for k, v in meta.items() if k in params and k not in skip}
    CENSUS._clear_fleet_caches()
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        st = run_year(
            year, meta["iso"], HOURS, gas_price, {}, fleet_only=True, **kwargs
        )
    from market_sim.policy.carbon import resolve_carbon_price

    fa = st["fleet_arrays"]
    gens = st.get("fleet") or []
    mc = np.asarray(st["mc_base"], dtype=float)
    if mc.ndim == 1:
        mc = np.tile(mc[:, None], (1, HOURS))
    fp = np.asarray(st["fuel_prices"], dtype=float)
    if fp.ndim == 1:
        fp = np.tile(fp[:, None], (1, HOURS))
    return {
        "group": np.array([str(getattr(g, "plant_group", "")) for g in gens]),
        "band": np.array([_band(u) for u in fa.unit_ids]),
        "pmax": np.asarray(fa.pmax, dtype=float),
        "hr": np.asarray(fa.heat_rate, dtype=float),
        "er": np.asarray(fa.emission_rate, dtype=float),
        "vom": np.asarray(fa.vom, dtype=float),
        "mc": mc,
        "fuel": fp,
        "carbon": float(resolve_carbon_price(st["config"], year)),
    }


def citygate_year_mean() -> dict:
    d = pd.read_csv(CITYGATE)
    d["date"] = pd.to_datetime(d["date"])
    return {
        y: float(
            d.loc[d["date"].dt.year == y, "ca_composite_usd_mmbtu"].dropna().mean()
        )
        for y in YEARS
    }


def main() -> None:
    meas = json.loads(MEASURED.read_text())
    geom = meas["_provenance"]["band_windows_geometry"]
    vom_by_bucket = meas["_provenance"]["vom_usd_per_mwh"]
    per_year_mults = meas["_provenance"]["per_year_band_mults"]
    cfg = json.loads((BUNDLE / "run_config.json").read_text())["scenario_config"]
    curves = cfg["offer_curve_by_group"]
    cg = citygate_year_mean()
    gas_prices = json.loads((BUNDLE / "meta.json").read_text())["gas_prices"]

    fleets = {y: rebuild(y, float(gas_prices[str(y)])) for y in YEARS}

    out: dict = {
        "_provenance": {
            "session": "caiso-242",
            "bundle": str(BUNDLE.relative_to(REPO)),
            "keeper_run_id": "2026-09-03-caiso-241-b1-ctpeaker",
            "co2_factor_derive": CO2_FACTOR,
            "note": "no LP, no flag delta; derive round-trip identity vs the model as built",
        },
        "per_year_inputs": {},
        "classes": {},
    }
    for y in YEARS:
        f = fleets[y]
        gas_sel = np.isin(f["group"], list(CLASS_BUCKET))
        w = f["pmax"][gas_sel]
        out["per_year_inputs"][y] = {
            "citygate_mean": round(cg[y], 4),
            "model_fuel_capwt_mean": round(
                float((f["fuel"][gas_sel].mean(axis=1) * w).sum() / w.sum()), 4
            ),
            "carbon_usd_per_t": round(f["carbon"], 4),
        }

    for cls, bucket in CLASS_BUCKET.items():
        base_hr = float(geom[bucket]["base_hr"]) if "base_hr" in geom[bucket] else None
        if base_hr is None:
            # the geometry block carries no base_hr; take it from the CAMPD summary
            base_hr = {"CC_REGULAR": 7.442, "CT_PEAKER": 10.862}[bucket]
        vom = float(vom_by_bucket[bucket])
        curve = curves.get(cls, {})
        rows: dict = {"bucket": bucket, "base_hr": base_hr, "vom": vom, "per_year": {}}
        A_y, B_y = [], []
        for y in YEARS:
            f = fleets[y]
            sel = f["group"] == cls
            if not sel.any():
                continue
            w = f["pmax"][sel]
            fuel_m = float((f["fuel"][sel].mean(axis=1) * w).sum() / w.sum())
            er_m = float((f["er"][sel] * w).sum() / w.sum())
            P = f["carbon"]
            A = (cg[y] + CO2_FACTOR * P) / fuel_m
            B = (er_m * P) / (base_hr * fuel_m)
            A_y.append(A)
            B_y.append(B)
            # measured bid and model offer at the armed econ_low multiplier
            m_armed = float(curve.get("econ_low", float("nan")))
            m_meas = per_year_mults.get(bucket, {}).get("econ_low", {}).get(str(y))
            bid_armed = vom + m_armed * base_hr * (cg[y] + CO2_FACTOR * P)
            # model's ACTUAL assembled offer for the class's econ rungs
            econ = sel & np.char.startswith(f["band"], "econc")
            model_mc = (
                float((f["mc"][econ].mean(axis=1) * f["pmax"][econ]).sum()
                      / max(f["pmax"][econ].sum(), 1e-9))
                if econ.any()
                else float("nan")
            )
            rows["per_year"][y] = {
                "model_fuel_capwt": round(fuel_m, 4),
                "citygate": round(cg[y], 4),
                "emission_rate_capwt_t_per_mwh": round(er_m, 5),
                "carbon_usd_per_t": round(P, 3),
                "A_gas_index_term": round(A, 5),
                "B_carbon_term": round(B, 5),
                "L1_gas_index_ratio_cg_over_model": round(cg[y] / fuel_m, 4),
                "L2_carbon_model_over_derive_assumed": round(
                    (er_m * P) / max(CO2_FACTOR * m_armed * base_hr * P, 1e-9), 4
                ),
                "measured_bid_at_armed_mult_usd_mwh": round(bid_armed, 3),
                "model_econ_mc_capwt_usd_mwh": round(model_mc, 3),
                "model_minus_bid_usd_mwh": round(model_mc - bid_armed, 3),
                "model_over_bid": round(model_mc / max(bid_armed, 1e-9), 4),
                "measured_mult_that_year": m_meas,
            }
        A = float(np.mean(A_y))
        B = float(np.mean(B_y))
        rows["A"] = round(A, 5)
        rows["B"] = round(B, 5)
        rows["A_dispersion"] = round(float(np.max(A_y) - np.min(A_y)) / 2.0, 5)
        rows["B_dispersion"] = round(float(np.max(B_y) - np.min(B_y)) / 2.0, 5)
        rec = {}
        for band in MEASURED_BANDS:
            if band not in curve:
                continue
            m = float(curve[band])
            rec[band] = {
                "armed": m,
                "reconciled": round(A * m - B, 5),
                "ratio": round((A * m - B) / m, 4),
                "phys": curve.get(f"phys_{band}"),
                "in_derive_G4_range_0p5_6p0": bool(0.5 <= (A * m - B) <= 6.0),
            }
        rows["reconciled_bands"] = rec
        out["classes"][cls] = rows

    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
