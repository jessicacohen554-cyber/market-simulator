"""Ad-hoc helper: re-price CAISO import/export tranches at FIXED capacities.

Holds the IMPORT_TRANCHES/EXPORT_TRANCHES["CAISO"] block CAPACITIES fixed (they
tile the measured net-interchange duration curve correctly) and re-derives only
the per-block PRICES so the modeled net-interchange tracks the measured series
against a bundle's SOLVED CAISO price duration curve.

Method (fixed-capacity inverse of derive_import_tranches.fit_blocks): the priced
node's net export is a staircase in the internal price whose step EDGES are the
cumulative block boundaries. For each edge we anti-monotone-match the modeled
price duration curve to the measured net-export duration curve: the edge price is
the modeled price quantile at the fraction of hours whose measured net export is
>= the edge's net-export midpoint.

Border carbon: an import tranche clears when the modeled price P exceeds
const_import + border_carbon (CARB unspecified-import EF x allowance, layered at
build time); export sinks carry NO border carbon. So the STORED import constant =
matched threshold - border_carbon, while the STORED sink constant = matched
threshold. Across a multi-year pool border carbon differs by year, so the import
edges are matched in the per-year carbon-shifted price frame (P - border(y))
pooled, and the sink edges in the raw price frame P pooled.

Usage: python scripts/probes/_caiso_reprice_fit.py <bundle> [year ...]   (no years => pooled 2023-2025)
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.constants import (  # noqa: E402
    CARB_UNSPECIFIED_IMPORT_EF,
    STATE_CARBON_PRICE_BY_ISO,
)
from market_sim.config.interchange_config import (  # noqa: E402
    EXPORT_TRANCHES,
    IMPORT_TRANCHES,
)

sys.path.insert(0, str(REPO / "scripts"))
from derive_import_tranches import (  # noqa: E402
    bundle_price,
    measured_net_interchange,
)


def border_carbon(year: int) -> float:
    return CARB_UNSPECIFIED_IMPORT_EF * STATE_CARBON_PRICE_BY_ISO["CAISO"][year]


def _pooled(
    bundle: Path, years: list[int]
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (raw modeled price, carbon-shifted price P-border(y), net export),
    each pooled hour-by-hour across ``years``."""
    raw, shifted, nxs = [], [], []
    for year in years:
        p = bundle_price(bundle, year)
        x = measured_net_interchange("CAISO", year)
        n = min(p.shape[0], x.shape[0])
        raw.append(p[:n])
        shifted.append(p[:n] - border_carbon(year))
        nxs.append(x[:n])
    return (np.concatenate(raw), np.concatenate(shifted), np.concatenate(nxs))


def _edge_midpoints() -> tuple[list[tuple[str, float]], list[tuple[str, float]]]:
    """Return (sink edges, import edges) as (name, net-export midpoint), built
    from the FIXED block capacities. Net export runs from +sum(sinks) (all sinks
    active, no imports) down to -sum(imports); the cheapest sink drops out first
    as price rises, then the cheapest import activates first."""
    imports = IMPORT_TRANCHES["CAISO"]
    sinks = EXPORT_TRANCHES["CAISO"]
    running = sum(c for _, c, _ in sinks)
    sink_edges = []
    for name, cap, _ in sorted(sinks, key=lambda t: t[2]):  # cheap sink off first
        prev = running
        running -= cap
        sink_edges.append((name, (prev + running) / 2.0))
    import_edges = []
    for name, cap, _ in imports:  # cheapest activates first
        prev = running
        running -= cap
        import_edges.append((name, (prev + running) / 2.0))
    return sink_edges, import_edges


def reprice(bundle: Path, years: list[int] | int) -> tuple[list[float], list[float]]:
    """Return (import constants cheapest->dearest, export sink constants)."""
    if isinstance(years, int):
        years = [years]
    raw, shifted, nx = _pooled(bundle, years)
    sink_edges, import_edges = _edge_midpoints()

    def edge_price(prices: np.ndarray, mid: float) -> float:
        # fraction of hours whose measured net export >= mid (the more-export,
        # lower-price hours) -> price quantile at that fraction.
        return float(np.quantile(prices, float((nx >= mid).mean())))

    # imports matched in the carbon-shifted frame (const = threshold - border),
    # sinks in the raw frame (no border carbon).
    import_const = {name: edge_price(shifted, mid) for name, mid in import_edges}
    sink_const = {name: edge_price(raw, mid) for name, mid in sink_edges}
    imp_out = [import_const[name] for name, _, _ in IMPORT_TRANCHES["CAISO"]]
    exp_out = [sink_const[name] for name, _, _ in EXPORT_TRANCHES["CAISO"]]
    return imp_out, exp_out


def score(bundle: Path, imp: list[float], exp: list[float], years: list[int]) -> None:
    """Offline-score candidate constants against ``bundle``'s solved price.

    Approximate (the price shifts once the node is repriced and re-solved) but a
    fast direction check. An import tranche clears when P > const+border(y); a
    sink when P < const (no border)."""
    imports = IMPORT_TRANCHES["CAISO"]
    sinks = EXPORT_TRANCHES["CAISO"]
    for year in years:
        p = bundle_price(bundle, year)
        x = measured_net_interchange("CAISO", year)
        n = min(p.shape[0], x.shape[0])
        p, x = p[:n], x[:n]
        bc = border_carbon(year)
        model = sum(c * (p < pr) for (_, c, _), pr in zip(sinks, exp)) - sum(
            c * (p > pr + bc) for (_, c, _), pr in zip(imports, imp)
        )
        pct = 100.0 * model.sum() / x.sum()
        rmse = float(np.sqrt(((np.sort(model) - np.sort(x)) ** 2).mean()))
        print(
            f"  {year}: model {model.sum() / 1e6:+.1f} TWh vs "
            f"{x.sum() / 1e6:+.1f} ({pct:.0f}%), import "
            f"{100.0 * (model < 0).mean():.1f}% vs "
            f"{100.0 * (x < 0).mean():.1f}%, dur RMSE {rmse:.0f} MW, "
            f"export p99 {np.quantile(model, 0.99):+.0f} MW"
        )


def main() -> None:
    bundle = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path("results/calibration/caiso_1_priced_ix")
    )
    arg_years = [int(a) for a in sys.argv[2:]]
    imports = IMPORT_TRANCHES["CAISO"]
    sinks = EXPORT_TRANCHES["CAISO"]
    print(f"bundle={bundle}")

    # Per-year fits (diagnostic) then the pooled fit (what gets written).
    for year in arg_years or [2023, 2024, 2025]:
        imp, exp = reprice(bundle, [year])
        bc = border_carbon(year)
        print(f"\n=== {year} (border carbon ${bc:.2f}/MWh) ===")
        print("  IMPORT (stored | effective=stored+border):")
        for (name, cap, old), new in zip(imports, imp):
            print(
                f"    {name:16s} {cap:6.0f} MW  ${old:6.1f} -> ${new:6.1f} "
                f"(eff ${new + bc:6.1f})"
            )
        print("  EXPORT:")
        for (name, cap, old), new in zip(sinks, exp):
            print(f"    {name:16s} {cap:6.0f} MW  ${old:6.1f} -> ${new:6.1f}")

    if not arg_years:
        imp, exp = reprice(bundle, [2023, 2024, 2025])
        print("\n=== POOLED 2023-2025 (stored pre-carbon) ===")
        print("  IMPORT:")
        for (name, cap, old), new in zip(imports, imp):
            print(f"    {name:16s} {cap:6.0f} MW  ${old:6.1f} -> ${new:6.1f}")
        print("  EXPORT:")
        for (name, cap, old), new in zip(sinks, exp):
            print(f"    {name:16s} {cap:6.0f} MW  ${old:6.1f} -> ${new:6.1f}")
        print("\n  offline score (pooled fit vs baseline bundle price):")
        score(bundle, imp, exp, [2023, 2024, 2025])


if __name__ == "__main__":
    main()
