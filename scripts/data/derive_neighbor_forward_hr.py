"""Derive each seam's FORWARD heat rate as the seam-own flat mean of ``hr_by_year``.

The reference-price interface (``market_sim.data.neighbor_price``) prices a
seam in a year its registry tabulates off the measured per-year anchor
``hr_by_year[year]`` and, in every untabulated (forecast) year, off a forward
value. For the SOCO seams the owner ruled (2026-10-02, card recorded in
``docs/records/soco/r-soco/FINDING-soco-100-fpl-tal-lambda-basis-2026-10-02.md``
§7) that the forward value is the seam's OWN flat mean of its registered
``hr_by_year`` cells — not the FINDING-soco-98 §3 elasticity fits and not the
structural 11.6 flat. This script computes that mean from the registry itself,
so ``NeighborInterface.forward_heat_rate`` is re-derivable, never typed
(rule 23 [R-FROZEN-DERIVE]: it moves only when the cells it averages move,
i.e. when their FERC-714 / LMP source data updates).

    forward_heat_rate = mean(hr_by_year.values())   (equal weight per year)

rounded to the cells' own two-decimal precision. A year the producer of
``hr_by_year`` refused (SOCO_FPL 2021, a re-filed series) is absent from the
cells and therefore from the mean. A seam with no cells (SOCO_SCEG) gets no
forward value and keeps its ``marginal_heat_rate``. Run::

    python scripts/data/derive_neighbor_forward_hr.py --iso SOCO

and paste each ``forward_heat_rate=`` line into the matching block.
"""

from __future__ import annotations

import argparse

from market_sim.config.interchange_config import INTERFACE_NEIGHBORS

#: ISOs whose seams carry a ruled forward heat rate (owner ruling 2026-10-02
#: covers the SOCO seams only; another ISO enters by its own ruling).
FORWARD_HR_ISOS: frozenset[str] = frozenset({"SOCO"})

#: Decimal places of the result — the precision ``derive_neighbor_hr_by_year``
#: writes the cells at, so the mean carries no false precision.
FORWARD_HR_DECIMALS: int = 2


def seam_own_flat_mean(hr_by_year: dict[int, float] | None) -> float | None:
    """Return the equal-weight mean of a seam's ``hr_by_year`` cells, or ``None``.

    Args:
        hr_by_year: The seam's registered per-year heat rates (MMBtu/MWh).

    Returns:
        The mean rounded to :data:`FORWARD_HR_DECIMALS`, or ``None`` for a seam
        with no cells.
    """
    if not hr_by_year:
        return None
    values = list(hr_by_year.values())
    return round(sum(values) / len(values), FORWARD_HR_DECIMALS)


def derive(iso: str) -> dict[str, float | None]:
    """Return ``{seam name: forward heat rate}`` for every seam of ``iso``.

    Args:
        iso: An ISO in :data:`FORWARD_HR_ISOS`.

    Raises:
        KeyError: ``iso`` has no ruled forward heat rate.
    """
    if iso not in FORWARD_HR_ISOS:
        raise KeyError(f"{iso}: no owner ruling sets a forward heat rate")
    return {n.name: seam_own_flat_mean(n.hr_by_year) for n in INTERFACE_NEIGHBORS[iso]}


def main() -> None:
    """Print each seam's forward heat rate and the cells it averages."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", default="SOCO")
    args = ap.parse_args()
    blocks = {n.name: n for n in INTERFACE_NEIGHBORS[args.iso]}
    for name, value in derive(args.iso).items():
        cells = blocks[name].hr_by_year or {}
        if value is None:
            print(f"# {name}: no hr_by_year cells -> no forward_heat_rate")
            continue
        years = ",".join(str(y) for y in sorted(cells))
        print(f"# {name}: mean of {len(cells)} cells ({years})")
        print(f"            forward_heat_rate={value},")


if __name__ == "__main__":
    main()
