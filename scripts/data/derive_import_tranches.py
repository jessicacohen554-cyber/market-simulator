"""Fit an ISO's priced import/export node to a net-interchange duration curve.

The import/export node (playbook §8.2; ``model/transmission.py``) is a
static price-step curve: export sinks clear when the ISO's internal price
falls below their willingness-to-pay, import tranches when it rises above
their cost, so the modeled net export is a decreasing step function of the
internal price. Hour-to-hour the measured interchange is nearly price-
orthogonal (PJM 2023 corr ≈ −0.06 — exports are neighbor-demand-driven), so
the fit targets the *duration curve*.

Two fit modes:

* **Bundle mode** (``--bundle``): pair the price duration curve from a solved
  calibration bundle with the measured net-interchange duration curve
  quantile-by-quantile (anti-monotone: the cheapest hours carry the deepest
  exports), place block boundaries at chosen price quantiles, and size each
  block as the net-export drop across its boundary. Used for PJM/CAISO, where
  a calibrated bundle exists.

* **Measured-only mode** (no ``--bundle``): a pure offline fit on the EIA-930
  series, with no LP run. The priced node can produce only a discrete set of
  net-export *levels* (each level = the cumulative net position of the blocks
  in the money at some internal price). Since the series is price-orthogonal
  the fit is free to place each level's price wherever it best tiles the
  measured duration curve, so the achievable duration-curve RMSE depends only
  on the block *capacities*, not on a modeled price. This is the right metric
  for a node whose modeled price is owned by a downstream pack (NYISO/NEISO
  P9: the tranche prices are neighbor-hub proxies, and modeled-net-import
  validation lives in P11/P12 — self-validating the fit against a self-solved
  price here would be circular).

Either way the script prints the fitted block suggestion for hand-rounding
into ``constants.IMPORT_TRANCHES`` / ``constants.EXPORT_TRANCHES`` and scores
the *current* constants entries (annual TWh, duration RMSE, import-hour share,
and — in bundle mode — diurnal correlation).

Usage:
    # bundle mode (PJM/CAISO)
    python scripts/data/derive_import_tranches.py --iso PJM --year 2023 \
        --bundle results/calibration/pjm_6_ccpeak
    # measured-only mode (NYISO/NEISO P9 offline fit)
    python scripts/data/derive_import_tranches.py --iso NYISO --year 2023
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.interchange_config import (  # noqa: E402
    EXPORT_TRANCHES,
    IMPORT_TRANCHES,
)
from market_sim.data.eia_loader import (  # noqa: E402
    load_eia_hourly_benchmark,
    pjm_net_interchange,
)

# Price quantiles for the block boundaries: dense enough to follow the
# measured curve's shape, sparse enough to keep the node a handful of
# blocks (playbook §8.2).
_BREAKPOINT_QUANTILES: tuple[float, ...] = (0.03, 0.15, 0.40, 0.70, 0.92, 0.99)


def measured_net_interchange(iso: str, year: int) -> np.ndarray:
    """Return the measured hourly net export (MW, export-positive).

    PJM reads its tie-line actuals (the same series ``load_demand`` serves
    as the backcast schedule); other ISOs fall back to the EIA-930 per-BA
    net interchange.
    """
    if iso == "PJM":
        ix = pjm_net_interchange(year)
        if ix is not None:
            return ix
    bench = load_eia_hourly_benchmark(iso, year)
    if bench is None or "interchange" not in bench:
        raise SystemExit(f"no net-interchange series for {iso} {year}")
    return np.asarray(bench["interchange"], dtype=float)


def bundle_price(bundle: Path, year: int) -> np.ndarray:
    """Return the bundle's hourly load-weighted system price for ``year``."""
    sysdf = pd.read_parquet(bundle / "system.parquet")
    g = sysdf[sysdf["year"] == year]
    if g.empty:
        raise SystemExit(f"{bundle} has no year {year}")
    last_pass = sorted(g["pass"].unique())[-1]
    g = g[g["pass"] == last_pass]
    p = g.pivot_table(index="hour", columns="zone", values="price", observed=True)
    d = g.pivot_table(index="hour", columns="zone", values="demand", observed=True)
    return ((p * d).sum(axis=1) / d.sum(axis=1)).to_numpy(dtype=float)


def fit_blocks(
    price: np.ndarray, net_export: np.ndarray
) -> tuple[list[tuple[float, float]], list[float]]:
    """Return fitted ``(boundary price, block capacity MW)`` pairs.

    The net-export level on each side of a boundary is the measured
    net-export quantile at the surrounding segments' midpoint quantiles;
    the block capacity is the drop across the boundary. A negative level in
    the top segment(s) becomes import-tranche capacity.
    """
    bps = _BREAKPOINT_QUANTILES
    mids = [bps[0] / 2.0]
    mids += [(bps[i] + bps[i + 1]) / 2.0 for i in range(len(bps) - 1)]
    mids += [(bps[-1] + 1.0) / 2.0]
    levels = [float(np.quantile(net_export, 1.0 - m)) for m in mids]
    prices = [float(np.quantile(price, b)) for b in bps]
    return [(prices[i], levels[i] - levels[i + 1]) for i in range(len(bps))], levels


def model_levels(iso: str) -> np.ndarray:
    """Return the discrete net-export levels the priced node can produce.

    As the internal price sweeps from +∞ down to −∞ the set of in-the-money
    blocks changes one at a time: at the highest prices every import tranche
    clears (net export ``-sum(imports)``), each falling below an import price
    drops that tranche (net export rises by its capacity) until none clear
    (net export 0), then each falling below a sink price activates that sink
    (net export rises by its capacity) up to ``+sum(sinks)``. The achievable
    net-export levels are therefore the partial sums, returned ascending.
    """
    imports = IMPORT_TRANCHES.get(iso, [])
    sinks = EXPORT_TRANCHES.get(iso, [])
    total_imp = sum(c for _, c, _ in imports)
    levels = [-total_imp]
    running = -total_imp
    # Most-expensive import drops out first as price falls.
    for _, c, _ in sorted(imports, key=lambda t: -t[2]):
        running += c
        levels.append(running)
    # Richest sink activates first as price keeps falling.
    for _, c, _ in sorted(sinks, key=lambda t: -t[2]):
        running += c
        levels.append(running)
    return np.array(sorted(levels), dtype=float)


def _place_on_levels(levels: np.ndarray, net_export: np.ndarray) -> np.ndarray:
    """Map each measured hour to its nearest achievable model level.

    Both the sorted duration curve and ``levels`` are monotone, so nearest-
    level assignment (against the level midpoints) is itself monotone — i.e.
    this is the best price-orthogonal placement of the staircase, the lower
    bound on duration-curve RMSE for the given block capacities.
    """
    mids = (levels[:-1] + levels[1:]) / 2.0
    idx = np.searchsorted(mids, net_export)
    return levels[idx]


def evaluate_measured(iso: str, net_export: np.ndarray) -> None:
    """Score the current constants by the bundle-free duration-curve fit.

    Reports the lower-bound duration-curve RMSE (optimal price-orthogonal
    placement), the best-case annual TWh and import-hour share the level set
    can reach, and the level set itself.
    """
    levels = model_levels(iso)
    if levels.size <= 1:
        print(f"  no IMPORT_TRANCHES/EXPORT_TRANCHES entries for {iso}")
        return
    placed = _place_on_levels(levels, net_export)
    dur_m = np.sort(placed)
    dur_a = np.sort(net_export)
    rmse = float(np.sqrt(((dur_m - dur_a) ** 2).mean()))
    print(
        f"  achievable net-export levels (MW): {'/'.join(f'{v:+.0f}' for v in levels)}"
    )
    print(
        f"  annual: best-case {placed.sum() / 1e6:+.1f} TWh vs "
        f"actual {net_export.sum() / 1e6:+.1f} TWh "
        f"({100.0 * placed.sum() / net_export.sum():.0f}%)"
    )
    print(f"  duration RMSE (optimal placement, lower bound): {rmse:.0f} MW")
    print(
        f"  import hours: best-case {100.0 * (placed < 0).mean():.1f}% vs "
        f"actual {100.0 * (net_export < 0).mean():.1f}%"
    )


def fit_levels_measured(
    net_export: np.ndarray, n_steps: int
) -> list[tuple[float, bool]]:
    """Suggest block capacities from the measured duration curve alone.

    Places ``n_steps`` equal-population net-export levels at the measured
    quantiles; each gap between consecutive levels is one block's capacity.
    A block whose net-export band sits below zero is an import tranche, above
    zero an export sink (classified by the band midpoint). Returned
    deepest-import first (cheapest import clears the most hours).
    """
    qs = np.linspace(0.0, 1.0, n_steps + 1)
    levels = np.quantile(net_export, qs)
    out: list[tuple[float, bool]] = []
    for lo, hi in zip(levels[:-1], levels[1:]):
        cap = hi - lo
        is_import = (lo + hi) / 2.0 < 0.0
        out.append((cap, is_import))
    return out


def evaluate(iso: str, price: np.ndarray, net_export: np.ndarray) -> None:
    """Score the current constants entries against the measured series."""
    sinks = EXPORT_TRANCHES.get(iso, [])
    imports = IMPORT_TRANCHES.get(iso, [])
    n = min(price.shape[0], net_export.shape[0])
    p, nx = price[:n], net_export[:n]
    model = sum(c * (p < pi) for _, c, pi in sinks) - sum(
        c * (p > pi) for _, c, pi in imports
    )
    if np.isscalar(model):
        print(f"  no IMPORT_TRANCHES/EXPORT_TRANCHES entries for {iso}")
        return
    rmse = float(np.sqrt(((np.sort(model) - np.sort(nx)) ** 2).mean()))
    d24m = model[: n - n % 24].reshape(-1, 24).mean(axis=0)
    d24a = nx[: n - n % 24].reshape(-1, 24).mean(axis=0)
    print(
        f"  annual: model {model.sum() / 1e6:+.1f} TWh vs "
        f"actual {nx.sum() / 1e6:+.1f} TWh "
        f"({100.0 * model.sum() / nx.sum():.0f}%)"
    )
    print(f"  duration RMSE: {rmse:.0f} MW")
    print(
        f"  import hours: model {100.0 * (model < 0).mean():.1f}% vs "
        f"actual {100.0 * (nx < 0).mean():.1f}%"
    )
    print(f"  diurnal corr: {np.corrcoef(d24m, d24a)[0, 1]:.2f}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", default="PJM")
    parser.add_argument("--year", type=int, default=2023)
    parser.add_argument(
        "--bundle",
        default=None,
        help="calibration bundle supplying the price duration curve for the "
        "bundle-mode fit (e.g. results/calibration/pjm_6_ccpeak). Omit "
        "for the offline measured-only fit (NYISO/NEISO P9).",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=6,
        help="number of equal-population blocks for the measured-only fit "
        "suggestion (default 6).",
    )
    args = parser.parse_args()
    iso = args.iso.upper()

    nx = measured_net_interchange(iso, args.year)

    if args.bundle is None:
        # Offline measured-only mode: fit and score on the EIA-930 duration
        # curve, no LP run (P9).
        print(
            f"{iso} {args.year}: measured net export "
            f"{nx.sum() / 1e6:+.1f} TWh ({nx.mean():+.0f} MW avg), "
            f"import {100.0 * (nx < 0).mean():.0f}% of hours "
            f"[measured-only fit, no bundle]"
        )
        caps = fit_levels_measured(nx, args.steps)
        print(
            f"\nSuggested {args.steps}-block capacities from the measured "
            f"duration curve, deepest-import first:"
        )
        for cap, is_import in caps:
            kind = "import tranche" if is_import else "export sink"
            print(f"  {kind:14s}: {cap:6.0f} MW")
        print(
            "Price each block at its neighbor-hub proxy (cite the source), "
            "imports above every sink."
        )
        print(f"\nCurrent constants entries for {iso}:")
        evaluate_measured(iso, nx)
        return

    price = bundle_price(Path(args.bundle), args.year)
    n = min(price.shape[0], nx.shape[0])
    price, nx = price[:n], nx[:n]

    print(
        f"{iso} {args.year}: measured net export "
        f"{nx.sum() / 1e6:+.1f} TWh ({nx.mean():+.0f} MW avg), "
        f"hourly corr(price, net export) "
        f"{np.corrcoef(price, nx)[0, 1]:+.2f}"
    )

    blocks, levels = fit_blocks(price, nx)
    print(
        f"\nFitted blocks (boundary price $/MWh, capacity MW); "
        f"segment net-export levels {np.round(levels, -2)}:"
    )
    for boundary, cap in blocks:
        kind = "export sink" if cap > 0 else "import tranche"
        print(f"  {kind:14s} @ ${boundary:5.1f}: {abs(cap):6.0f} MW")
    print(
        "Round these into constants.EXPORT_TRANCHES[iso] (sink price = "
        "its boundary) and constants.IMPORT_TRANCHES[iso] (price above "
        "every sink)."
    )

    print(f"\nCurrent constants entries for {iso}:")
    evaluate(iso, price, nx)


if __name__ == "__main__":
    main()
