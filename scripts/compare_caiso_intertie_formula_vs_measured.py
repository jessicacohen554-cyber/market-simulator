#!/usr/bin/env python
"""Compare the CAISO forward intertie seam against the measured realization.

The honesty gate for the forward CAISO WECC seam (``--caiso-intertie-reference-
price`` + ``--caiso-corridor-atc-forward``): the forward path must form its
import PRICE from forward gas/HR/load-shape and its deliverability LIMIT from a
capability (ATC) — neither pinned to the measured realization. This script puts
the two side by side so the gate is auditable:

1. **Price** — the per-hub forward reference price
   (:func:`market_sim.data.neighbor_price.caiso_hub_reference_price`) vs the
   MEASURED WECC hub LMP (Malin / Palo Verde, the OASIS series in
   ``wecc_intertie_lmp_hourly_CAISO.parquet``): annual mean, MAE, diurnal-shape
   correlation, and the midday/evening levels that carry the solar duck.

2. **Deliverability** — the forward ATC envelope
   (:func:`market_sim.model.transmission.forward_corridor_atc_envelope`, a
   capability limit = corridor TTC × posted-ATC fraction × forward solar derate)
   vs the MEASURED p95 net-import envelope
   (:func:`market_sim.data.eia_loader.measured_corridor_flow_envelope`): annual
   mean and midday level per corridor.

The measured series are the *validation* target, never an input to the forward
path — this script only reads them to score the formula. Optionally, with
``--measured-bundle`` / ``--forward-bundle`` pointing at two solved calibration
bundles, it also prints the solved net-import volume each path produced (the
realized-flow half of the price/volume comparison).

Usage::

    python scripts/compare_caiso_intertie_formula_vs_measured.py \
        --year 2023 2024 2025
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config import paths
from market_sim.config.interchange_config import CAISO_PER_HUB_NEIGHBORS
from market_sim.config.iso_configs import get_iso_config
from market_sim.data.eia_loader import measured_corridor_flow_envelope
from market_sim.data.neighbor_price import caiso_hub_reference_price
from market_sim.model.transmission import (
    forward_corridor_atc_envelope,
    split_caiso_import_node_per_hub,
)

HOURS = 8760


def _measured_hub_lmp(year: int) -> dict[str, np.ndarray]:
    """Return the measured WECC hub LMP per corridor zone for ``year`` (or {})."""
    path = paths.CALIBRATION_DIR / "wecc_intertie_lmp_hourly_CAISO.parquet"
    if not path.exists():
        return {}
    frame = pd.read_parquet(path)
    frame = frame[frame["year"] == year]
    if frame.empty:
        return {}
    hub_to_zone = {spec.hub: spec.zone for spec in CAISO_PER_HUB_NEIGHBORS.values()}
    out: dict[str, np.ndarray] = {}
    for hub, sub in frame.groupby("hub"):
        zone = hub_to_zone.get(str(hub))
        if zone is None:
            continue
        price = (
            pd.to_numeric(sub.sort_values("hour")["price"], errors="coerce")
            .interpolate(limit=2)
            .to_numpy(dtype=float)
        )
        if price.shape[0] >= HOURS and np.all(np.isfinite(price[:HOURS])):
            out[zone] = price[:HOURS]
    return out


def _diurnal(series: np.ndarray) -> np.ndarray:
    """Return the 24-hour-of-day mean profile of an 8760 series."""
    hod = np.arange(series.shape[0]) % 24
    return np.array([series[hod == h].mean() for h in range(24)])


def _window(series: np.ndarray, lo: int, hi: int) -> float:
    """Return the mean of ``series`` over hours-of-day in ``[lo, hi]``."""
    hod = np.arange(series.shape[0]) % 24
    return float(series[(hod >= lo) & (hod <= hi)].mean())


def compare_year(year: int, gas_scenario: str = "mid") -> dict:
    """Return the price + deliverability comparison metrics for one year."""
    measured_price = _measured_hub_lmp(year)
    cfg = split_caiso_import_node_per_hub(get_iso_config("CAISO"))
    fwd_atc = forward_corridor_atc_envelope(cfg, "CAISO", year, HOURS) or {}
    meas_atc = measured_corridor_flow_envelope("CAISO", year, HOURS) or {}

    rows: dict = {"year": year, "corridors": {}}
    for zone, spec in CAISO_PER_HUB_NEIGHBORS.items():
        formula = caiso_hub_reference_price(spec, year, HOURS, gas_scenario)
        c: dict = {"hub": spec.hub}
        if formula is not None:
            c["formula_mean"] = round(float(formula.mean()), 2)
            c["formula_midday"] = round(_window(formula, 10, 15), 2)
            c["formula_evening"] = round(_window(formula, 18, 21), 2)
            c["formula_neg_hours"] = int((formula < 0).sum())
        meas = measured_price.get(zone)
        if meas is not None:
            c["measured_mean"] = round(float(meas.mean()), 2)
            c["measured_midday"] = round(_window(meas, 10, 15), 2)
            c["measured_evening"] = round(_window(meas, 18, 21), 2)
            c["measured_neg_hours"] = int((meas < 0).sum())
        if formula is not None and meas is not None:
            c["price_mae"] = round(float(np.mean(np.abs(formula - meas))), 2)
            c["price_bias"] = round(float(np.mean(formula - meas)), 2)
            df, dm = _diurnal(formula), _diurnal(meas)
            c["diurnal_corr"] = round(float(np.corrcoef(df, dm)[0, 1]), 3)
        if zone in fwd_atc:
            c["atc_forward_mean_mw"] = round(float(fwd_atc[zone].mean()))
            c["atc_forward_midday_mw"] = round(_window(fwd_atc[zone], 10, 15))
        if zone in meas_atc:
            c["atc_measured_mean_mw"] = round(float(meas_atc[zone].mean()))
            c["atc_measured_midday_mw"] = round(_window(meas_atc[zone], 10, 15))
        rows["corridors"][zone] = c
    return rows


def _bundle_net_import(bundle: Path, year: int) -> float | None:
    """Return a solved bundle's CAISO net import (TWh) for ``year``, if present.

    Reads the per-year metrics the calibration bundle records; falls back to
    ``None`` when the bundle or the field is absent (the script then skips the
    realized-volume line). The exact metric key is bundle-version-dependent, so
    several likely names are probed.
    """
    for name in (f"metrics_{year}.json", "metrics.json", "summary.json"):
        p = bundle / name
        if not p.exists():
            continue
        try:
            data = json.loads(p.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        blob = data.get(str(year), data)
        for key in ("net_import_twh", "net_interchange_twh", "import_twh"):
            if isinstance(blob, dict) and key in blob:
                return float(blob[key])
    return None


def main() -> None:
    """CLI entry: print the measured-vs-formula comparison for each year."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--gas-scenario", default="mid")
    ap.add_argument("--measured-bundle", type=Path, default=None)
    ap.add_argument("--forward-bundle", type=Path, default=None)
    ap.add_argument("--json", action="store_true", help="emit JSON, not a table")
    args = ap.parse_args()

    results = [compare_year(y, args.gas_scenario) for y in args.year]
    if args.json:
        print(json.dumps(results, indent=2))
        return

    for r in results:
        year = r["year"]
        print(f"\n=== CAISO {year}: forward seam vs measured realization ===")
        for zone, c in r["corridors"].items():
            print(f"  {zone} ({c['hub']}):")
            print(
                f"    price  formula mean {c.get('formula_mean'):>7} "
                f"(mid {c.get('formula_midday')}, eve {c.get('formula_evening')}, "
                f"neg {c.get('formula_neg_hours')})"
            )
            if "measured_mean" in c:
                print(
                    f"           measured mean {c.get('measured_mean'):>6} "
                    f"(mid {c.get('measured_midday')}, eve {c.get('measured_evening')}, "
                    f"neg {c.get('measured_neg_hours')})"
                )
                print(
                    f"           MAE {c.get('price_mae')}  bias {c.get('price_bias')}  "
                    f"diurnal-corr {c.get('diurnal_corr')}"
                )
            if "atc_forward_mean_mw" in c:
                line = (
                    f"    ATC    forward mean {c.get('atc_forward_mean_mw')} MW "
                    f"(midday {c.get('atc_forward_midday_mw')})"
                )
                if "atc_measured_mean_mw" in c:
                    line += (
                        f"  |  measured p95 mean {c.get('atc_measured_mean_mw')} MW "
                        f"(midday {c.get('atc_measured_midday_mw')})"
                    )
                print(line)
        if args.measured_bundle or args.forward_bundle:
            mi = (
                _bundle_net_import(args.measured_bundle, year)
                if args.measured_bundle
                else None
            )
            fi = (
                _bundle_net_import(args.forward_bundle, year)
                if args.forward_bundle
                else None
            )
            if mi is not None or fi is not None:
                print(
                    f"    volume solved net import — measured {mi} TWh | "
                    f"forward {fi} TWh"
                )


if __name__ == "__main__":
    main()
