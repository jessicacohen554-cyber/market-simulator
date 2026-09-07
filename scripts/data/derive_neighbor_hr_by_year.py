"""Derive per-backcast-year neighbor marginal heat rates from measured LMP.

The reference-price interface (``market_sim.data.neighbor_price``) prices each
seam as ``(henry_hub + gas_basis) x marginal_heat_rate x load_shape``. The
registry carries ONE ``marginal_heat_rate`` per neighbor — a 3-year *mean* of
the neighbor's realized LMP / delivered-gas ratio. Because the real ratio drifts
year to year (MISO 12.5 / 14.1 / 12.2 for 2023-25), the single mean over-prices
the neighbor in the dear-gas year and under-prices it in the cheap-gas year,
opening (closing) a fake export spread on the seam — the root of the PJM 2025
over-export / 2024 under-export.

This script re-anchors the heat rate PER YEAR to the neighbor's OWN measured
annual-mean realized LMP so the constructed seam reference reproduces the
neighbor's realized annual mean each backcast year:

    HR[year] = measured_mean_LMP[year]
               / ((henry_hub[year] + gas_basis) x K[year])

where ``K[year] = mean(load_shape ** exponent)`` is the convexity inflation of
the load-shape multiplier (so the constructed ANNUAL MEAN, not just the
baseload, equals the measured mean). This is a measured neighbor price-formation
input (claude.md rule #12 — measured over estimate; the forward analogue is the
structural ``marginal_heat_rate``, used whenever a year has no measured LMP), it
is NOT tuned to the ISO's net interchange (rule #11) — it never sees the flow.

THE ANCHOR MAP IS PER ISO (lane SPP-51, 2026-09-07, repairing FINDING-spp-33
§2 / §6 R1). It used to be keyed by neighbour NAME alone, globally, which (a)
sent SPP's ``MISO`` seam to the MISO *system* file where the registration
anchors on the West/South zonal rows, and (b) silently ``continue``-d past any
neighbour with no key (SPP's ``AECI`` / ``ERCOT``), printing one wrong-anchor
row and no diagnostic. Now each ISO names, per neighbour, the committed
realized-LMP product and an optional zone filter, exactly as its ``spec.py``
block documents; a neighbour with no anchor (no organized market — PJM's
Carolinas/TVA/LGEE) is PRINTED as such rather than skipped, an ISO with no map
FAILS, and a declared anchor whose file or rows are absent FAILS instead of
being dropped. Run::

    python scripts/data/derive_neighbor_hr_by_year.py --iso PJM

and paste the emitted block into the ISO's ``INTERFACE_NEIGHBORS`` entry.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass

import numpy as np
import pandas as pd

from market_sim.config import paths
from market_sim.config.interchange_config import INTERFACE_NEIGHBORS
from market_sim.data.neighbor_price import neighbor_gas_price, neighbor_load_shape


@dataclass(frozen=True)
class Anchor:
    """One neighbour's measured price anchor.

    Attributes:
        product: The ``actual_lmp_hourly_<product>.parquet`` stem under
            ``paths.CALIBRATION_DIR`` (an ISO code, or ``zonal_<ISO>`` for a
            zonal product).
        zones: For a zonal product, the ``zone`` values to average; ``None``
            takes the whole file (a system product). A multi-zone anchor is
            averaged PER ZONE and then over zones — one price per zone, never a
            hub census (FINDING-spp-33 §2).
        proxy: A declared proxy (the anchor is not the neighbour's own price).
    """

    product: str
    zones: tuple[str, ...] | None = None
    proxy: bool = False


# ISO -> neighbour name -> the measured anchor its registry block documents.
# A neighbour absent from its ISO's map (no organized-market LMP, e.g. PJM's
# Carolinas / TVA / LGEE) keeps the structural marginal_heat_rate and gets no
# year table; it is REPORTED, not silently skipped. An ISO absent here fails.
# Other ISOs' entries are the pre-2026-09-07 global map, unchanged (rule 25:
# each ISO's anchors are its own; PJM's "MISO" seam and SPP's "MISO_*" legs
# read different products because they are different physical seams).
NEIGHBOR_LMP_ANCHORS: dict[str, dict[str, Anchor]] = {
    "PJM": {
        "MISO": Anchor("MISO"),
        "NYISO": Anchor("NYISO"),
    },
    "MISO": {
        "PJM": Anchor("PJM"),
        "SPP": Anchor("SPP"),
    },
    # CAISO's corridor seams are anchored by their own per-hub derive
    # (scripts/data/derive_caiso_*); no realized-LMP product is registered here.
    "CAISO": {},
    # SPP (lane SPP-51): the anchors INTERFACE_NEIGHBORS["SPP"] documents block
    # by block — the two MISO legs on their own zonal rows, AECI on the SPP
    # system hub as a DECLARED PROXY (AECI publishes no LMP), ERCOT on its
    # system file.
    "SPP": {
        "MISO_West": Anchor("zonal_MISO", ("MISO-West",)),
        "MISO_South": Anchor("zonal_MISO", ("MISO-South",)),
        "AECI": Anchor("SPP", proxy=True),
        "ERCOT": Anchor("ERCOT"),
    },
}

_HOURS = 8760


def _measured_mean_lmp(anchor: Anchor, year: int, run: str = "rt") -> float | None:
    """Return the anchor's realized annual-mean LMP ($/MWh), or None if absent.

    A zonal anchor averages per zone and then equal-weight over the listed
    zones; a system anchor is the nan-mean of the file's rows for ``year``.
    """
    path = paths.CALIBRATION_DIR / f"actual_lmp_hourly_{anchor.product}.parquet"
    if not path.is_file():
        return None
    df = pd.read_parquet(path)
    rows = df[df["year"] == year]
    if rows.empty or run not in rows.columns:
        return None
    if anchor.zones is not None:
        rows = rows[rows["zone"].isin(anchor.zones)]
        if rows.empty:
            return None
        return float(rows.groupby("zone")[run].mean().mean())
    return float(np.nanmean(rows[run].to_numpy(dtype=float)))


def derive(iso: str, years: list[int], run: str = "rt") -> dict[str, dict[int, float]]:
    """Return ``{neighbor_name: {year: hr}}`` anchored to measured neighbor LMP.

    Raises:
        KeyError: ``iso`` has no anchor map (an unregistered ISO never emits
            a silently-empty table).
        FileNotFoundError: a DECLARED anchor's product file or year rows are
            absent — the former silent ``continue`` (FINDING-spp-33 §2).
    """
    if iso not in NEIGHBOR_LMP_ANCHORS:
        raise KeyError(
            f"{iso}: no neighbour anchor map registered in NEIGHBOR_LMP_ANCHORS"
        )
    anchors = NEIGHBOR_LMP_ANCHORS[iso]
    out: dict[str, dict[int, float]] = {}
    for neighbor in INTERFACE_NEIGHBORS.get(iso, []):
        anchor = anchors.get(neighbor.name)
        if anchor is None:
            continue
        per_year: dict[int, float] = {}
        for year in years:
            measured = _measured_mean_lmp(anchor, year, run)
            if measured is None:
                raise FileNotFoundError(
                    f"{iso}/{neighbor.name}: declared anchor "
                    f"actual_lmp_hourly_{anchor.product}.parquet has no {run} "
                    f"rows for {year}"
                    + (f" in zones {anchor.zones}" if anchor.zones else "")
                )
            shaped = neighbor_load_shape(neighbor, year, _HOURS)
            if shaped is None:
                raise FileNotFoundError(
                    f"{iso}/{neighbor.name}: no EIA-930 load shape resolves for "
                    f"{year} (ba_code={neighbor.ba_code}, proxy_ba={neighbor.proxy_ba})"
                )
            k = float(np.nanmean(shaped[0] ** 1.0))  # shape already exponentiated
            gas = neighbor_gas_price(neighbor, year)
            hr = measured / (gas * k)
            per_year[year] = round(hr, 2)
        out[neighbor.name] = per_year
    return out


def unanchored(iso: str) -> list[str]:
    """Return the ISO's registered neighbours that carry no measured anchor."""
    anchors = NEIGHBOR_LMP_ANCHORS.get(iso, {})
    return [n.name for n in INTERFACE_NEIGHBORS.get(iso, []) if n.name not in anchors]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", default="PJM")
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument("--run", default="rt", choices=("rt", "da"))
    args = ap.parse_args()
    iso = args.iso.upper()
    try:
        table = derive(iso, args.years, args.run)
    except (KeyError, FileNotFoundError) as exc:
        sys.exit(f"derive_neighbor_hr_by_year: {exc}")
    print(f"# Derived measured-anchored neighbor heat rates for {iso} ({args.run})")
    for name, per_year in table.items():
        cur = next(
            n.marginal_heat_rate for n in INTERFACE_NEIGHBORS[iso] if n.name == name
        )
        anchor = NEIGHBOR_LMP_ANCHORS[iso][name]
        tag = " PROXY anchor" if anchor.proxy else ""
        cells = ", ".join(f"{y}: {hr}" for y, hr in sorted(per_year.items()))
        print(f'    "{name}": {{{cells}}},   # structural HR {cur}{tag}')
    for name in unanchored(iso):
        print(
            f"# {name}: no measured anchor registered — structural "
            "marginal_heat_rate kept (no organized-market LMP)"
        )


if __name__ == "__main__":
    main()
