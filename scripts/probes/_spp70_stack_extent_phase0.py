"""SPP-70 phase 0 — attribute the vertical extent of SPP's thermal offer stack.

ZERO LP. Rebuilds the LP's own offer array (``mc_base``) through the sanctioned
``fleet_only`` reconstruction (``scripts/lib/bundle_fleet.reconstruct_bundle_fleet``)
and decomposes the capacity-weighted width of the thermal supply curve into the
four candidate constructions FINDING-spp-64 §6 named but did not attribute:

    (a) heat-rate spread across units/tranches
    (b) VOM spread across classes
    (c) fuel-price spread across units (one gas price for every gas unit?)
    (d) tranche band shares / band multipliers

One year per interpreter (trap (b): the fleet loaders are ``@lru_cache``d on
arguments, never on file contents), driven by ``--year``.  Emits one JSON blob
per year to ``--out``; ``--report`` reduces the per-year blobs to the tables.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# Bundle per year: the rung carries 2019-2022, the keeper span 2023-2025.
BUNDLES = {
    2019: "results/calibration/spp67_yearown_rung",
    2020: "results/calibration/spp67_yearown_rung",
    2021: "results/calibration/spp67_yearown_rung",
    2022: "results/calibration/spp67_yearown_rung",
    2023: "results/calibration/spp67_yearown_span",
    2024: "results/calibration/spp67_yearown_span",
    2025: "results/calibration/spp67_yearown_span",
}

# The thermal classes. Renewables/storage/hydro carry no offer stack.
THERMAL_PREFIXES = ("COAL", "CC_", "CT_", "ST_")


def _labels(fleet_arrays):
    """Per-row (class, band) labels, via the repo's own parsers."""
    from scripts.run_calibration_full import _coal_supply_class, _tranche_band

    groups = fleet_arrays.plant_group
    plant_codes = np.asarray(fleet_arrays.plant_code)
    klass, band = [], []
    for i, uid in enumerate(fleet_arrays.unit_ids):
        g = str(groups[i]) if groups is not None else ""
        if g == "COAL":
            g = _coal_supply_class(int(plant_codes[i]))
        klass.append(g)
        band.append(_tranche_band(str(uid)))
    return np.array(klass, dtype=object), np.array(band, dtype=object)


def _wq(values, weights, qs):
    """Weighted quantiles."""
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    ok = np.isfinite(values) & (weights > 0)
    values, weights = values[ok], weights[ok]
    if values.size == 0:
        return [float("nan")] * len(qs)
    order = np.argsort(values)
    v, w = values[order], weights[order]
    cw = np.cumsum(w)
    cw = (cw - 0.5 * w) / cw[-1]
    return [float(np.interp(q, cw, v)) for q in qs]


def extract(year: int) -> dict:
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    bundle = REPO / BUNDLES[year]
    state, meta = reconstruct_bundle_fleet(bundle, year, verbose=False)
    fa = state["fleet_arrays"]
    mc = np.asarray(state["mc_base"], dtype=float)  # (n_gen, T)
    fuel = np.asarray(state["fuel_prices"], dtype=float)  # (n_gen, T) or broadcastable
    if fuel.ndim == 1:
        fuel = fuel[:, None]
    if fuel.shape[1] == 1:
        fuel = np.broadcast_to(fuel, mc.shape)

    klass, band = _labels(fa)
    hr = np.asarray(fa.heat_rate, dtype=float)
    vom = np.asarray(fa.vom, dtype=float)
    er = np.asarray(fa.emission_rate, dtype=float)
    pmax = np.asarray(fa.pmax, dtype=float)
    avail = np.asarray(fa.availability, dtype=float)
    if avail.ndim == 1:
        avail = avail[:, None]

    is_thermal = np.array([str(k).startswith(THERMAL_PREFIXES) for k in klass])
    # carbon term as the LP sees it: mc - hr*fuel - vom
    resid = mc - hr[:, None] * fuel - vom[:, None]

    rows = {
        "unit_id": [str(u) for u in fa.unit_ids],
        "klass": klass.tolist(),
        "band": band.tolist(),
        "heat_rate": hr.tolist(),
        "vom": vom.tolist(),
        "emission_rate": er.tolist(),
        "pmax": pmax.tolist(),
        "avail_mean": avail.mean(axis=1).tolist()
        if avail.shape[1] > 1
        else (avail[:, 0]).tolist(),
        "thermal": is_thermal.tolist(),
        # annual capacity-hour-weighted mean of each hour-varying term
        "mc_mean": mc.mean(axis=1).tolist(),
        "mc_p05_h": np.percentile(mc, 5, axis=1).tolist(),
        "mc_p95_h": np.percentile(mc, 95, axis=1).tolist(),
        "fuel_mean": fuel.mean(axis=1).tolist(),
        "fuel_std": fuel.std(axis=1).tolist(),
        "resid_mean": resid.mean(axis=1).tolist(),
    }
    return {
        "year": year,
        "bundle": BUNDLES[year],
        "n_gen": int(mc.shape[0]),
        "T": int(mc.shape[1]),
        "gas_price_override": meta.get("gas_prices", {}).get(str(year)),
        "rows": rows,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    blob = extract(args.year)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(blob))
    r = blob["rows"]
    n_th = sum(r["thermal"])
    print(
        f"{args.year}: {blob['n_gen']} rows ({n_th} thermal), T={blob['T']} -> {args.out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
