"""Reader over the ``coal-receipts`` clean datatype (plant-level monthly deliveries).

The DELIVERY half of the coal fuel-inventory state.
:mod:`market_sim.data.coal_stocks` carries the month-ending stockpile; this
module carries the tonnage that arrived to refill it. Together they are the two
halves of the inventory identity::

    ending[m] = ending[m-1] + receipts[m] - burn[m]

**RULE 13 ``[R-MEASURED]`` — THE TRAP, STATED AT THE SEAM.**
``quantity_tons`` is a measured deliveries-to-tank OUTCOME for the year it is
reported in, and the precedent on it is explicit rather than inferred:
:mod:`market_sim.data.winter_fuel_inventory` records that the F923 petroleum
*receipts* budget (``fuel.py:load_oil_burn_budget``) was REJECTED as "a measured
deliveries-to-tank OUTCOME inadmissible under CLAUDE.md #13", and that the
accepted NEISO budget was rebuilt from forward-regenerable capacity/logistics
quantities instead. So **year Y's own receipts are not an admissible delivery
rate for year Y's budget**, exactly as year Y's own stock path is not.

What IS admissible is a rate over years ``<= Y-1``. That passes rule 13's own
forward test — it is producible for a forward year from then-current filings,
and it responds to changed conditions (a fleet that shrinks or re-contracts
carries a different rate). :func:`prior_years_delivery_rate` is that read, and
it exists so the admissible construction is the easy one: there is deliberately
no convenience function here that returns the target year's own receipts.

Rule 25 ``[R-ISO-SCOPE]``: the datatype is national and ISO scoping is a
read-time join on the caller's own plant ids, never a partition of the data, so
one curation serves every coal ISO with no per-ISO branch.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from market_sim.config import paths

_DATATYPE = "coal-receipts"

#: EIA purchase types that represent a forward commitment rather than a spot
#: buy: ``C`` contract and ``NC`` new contract. Exposed so a "contracted
#: tonnage only" delivery-rate construction is selectable by the caller without
#: any module here hard-coding which construction is the right one.
CONTRACT_PURCHASE_TYPES: tuple[str, ...] = ("C", "NC")

#: EIA primary transportation modes that move coal by rail — ``RR`` railroad.
#: Exposed for a rail/logistics-capacity construction, same rationale.
RAIL_TRANSPORT_MODES: tuple[str, ...] = ("RR",)


@dataclass(frozen=True)
class DeliveryRate:
    """A prior-years coal delivery rate for one footprint.

    Every field is derived from years strictly before the target year, so the
    whole object is admissible as an input to that year's budget (rule 13).

    Attributes:
        tons_per_year: Mean annual coal receipts over the source years.
        mmbtu_per_ton: Quantity-weighted mean heat content over the same years.
        source_years: The years averaged, for the DOF ledger and provenance.
        purchase_types: Purchase types included, or ``None`` for all of them.
    """

    tons_per_year: float
    mmbtu_per_ton: float
    source_years: tuple[int, ...]
    purchase_types: tuple[str, ...] | None

    @property
    def mmbtu_per_year(self) -> float:
        """The delivery rate expressed as fuel energy (MMBtu/yr)."""
        return self.tons_per_year * self.mmbtu_per_ton


def _read_clean():
    """Import the shared ``scripts.lib.clean_io`` reader seam, lazily.

    ``clean_io`` lives under ``scripts/`` (not an installed package), so the repo
    root goes on ``sys.path`` the way :mod:`market_sim.data.coal_stocks` and
    :mod:`market_sim.data.winter_fuel_inventory` do.
    """
    root = str(paths.REPO_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    from scripts.lib import clean_io

    return clean_io


def load_coal_receipts(years: list[int] | None = None) -> pd.DataFrame:
    """Return plant x rank x month x purchase-type x mode coal receipts.

    Args:
        years: Calendar years to load. ``None`` loads every curated year.

    Returns:
        Frame on the ``coal-receipts`` schema grain, empty if no year is
        curated.
    """
    clean_io = _read_clean()
    frames: list[pd.DataFrame] = []
    root = paths.CLEAN_DIR / _DATATYPE
    if not root.is_dir():
        return pd.DataFrame()
    for path in sorted(root.glob(f"{_DATATYPE}_*.parquet")):
        year = int(Path(path).stem.rsplit("_", 1)[1])
        if years is not None and year not in years:
            continue
        frames.append(clean_io.read_clean(_DATATYPE, year=year))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def footprint_receipts(
    plant_ids: set[int] | list[int],
    years: list[int] | None = None,
    *,
    purchase_types: tuple[str, ...] | None = None,
    transport_modes: tuple[str, ...] | None = None,
) -> pd.DataFrame:
    """Aggregate monthly coal receipts over one ISO footprint.

    ISO scoping is a READ-TIME join (rule 25 ``[R-ISO-SCOPE]``): callers pass
    the plant ids their own fleet resolves rather than trusting the EIA
    ``balancing_authority_code``, which disagrees with the modelled zone at
    several seams.

    Args:
        plant_ids: EIA plant codes making up the footprint.
        years: Calendar years to include; ``None`` for every curated year.
        purchase_types: Restrict to these EIA purchase types (e.g.
            :data:`CONTRACT_PURCHASE_TYPES`); ``None`` for all.
        transport_modes: Restrict to these primary transportation modes (e.g.
            :data:`RAIL_TRANSPORT_MODES`); ``None`` for all.

    Returns:
        Frame with ``year``, ``month``, ``quantity_tons`` and the
        quantity-weighted ``heat_content_mmbtu_per_ton``, one row per month.
    """
    df = load_coal_receipts(years)
    if df.empty:
        return df
    sel = df[df["plant_id"].isin({int(p) for p in plant_ids})]
    if purchase_types is not None:
        sel = sel[sel["purchase_type"].isin(purchase_types)]
    if transport_modes is not None:
        sel = sel[sel["primary_transportation_mode"].isin(transport_modes)]
    if sel.empty:
        return sel.iloc[0:0]
    sel = sel.assign(_mmbtu=sel["quantity_tons"] * sel["heat_content_mmbtu_per_ton"])
    out = sel.groupby(["year", "month"], as_index=False).agg(
        quantity_tons=("quantity_tons", "sum"),
        _mmbtu=("_mmbtu", "sum"),
    )
    out["heat_content_mmbtu_per_ton"] = out["_mmbtu"] / out["quantity_tons"].where(
        out["quantity_tons"] > 0
    )
    return (
        out.drop(columns="_mmbtu").sort_values(["year", "month"]).reset_index(drop=True)
    )


def prior_years_delivery_rate(
    plant_ids: set[int] | list[int],
    year: int,
    *,
    n_years: int = 2,
    purchase_types: tuple[str, ...] | None = None,
    transport_modes: tuple[str, ...] | None = None,
) -> DeliveryRate | None:
    """Return the admissible prior-years coal delivery rate for ``year``.

    Averages the footprint's annual receipts over the ``n_years`` calendar years
    immediately before ``year`` — never ``year`` itself, which is the measured
    outcome rule 13 forbids as a budget input (see the module docstring). The
    heat content is the quantity-weighted mean over the same source years, so a
    tonnage rate converts to MMBtu on the coal the fleet was actually being sent
    rather than on an assumed rank.

    A year with no curated receipts is skipped rather than counted as zero
    deliveries; ``None`` comes back when none of the source years is curated, so
    a caller must handle the gap instead of silently budgeting on nothing.

    Args:
        plant_ids: EIA plant codes making up the footprint.
        year: The target year whose budget is being sized.
        n_years: How many prior years to average (default 2).
        purchase_types: Restrict to these EIA purchase types; ``None`` for all.
        transport_modes: Restrict to these transportation modes; ``None`` for
            all.

    Returns:
        A :class:`DeliveryRate`, or ``None`` when no source year is curated.
    """
    source = [year - k for k in range(1, int(n_years) + 1)]
    df = footprint_receipts(
        plant_ids,
        years=source,
        purchase_types=purchase_types,
        transport_modes=transport_modes,
    )
    if df.empty:
        return None
    df = df.assign(_mmbtu=df["quantity_tons"] * df["heat_content_mmbtu_per_ton"])
    per_year = df.groupby("year", as_index=False).agg(
        tons=("quantity_tons", "sum"), mmbtu=("_mmbtu", "sum")
    )
    tons = float(per_year["tons"].mean())
    total_tons = float(per_year["tons"].sum())
    if tons <= 0.0 or total_tons <= 0.0:
        return None
    return DeliveryRate(
        tons_per_year=tons,
        mmbtu_per_ton=float(per_year["mmbtu"].sum()) / total_tons,
        source_years=tuple(sorted(int(y) for y in per_year["year"])),
        purchase_types=purchase_types,
    )
