"""Resource catalog and cost resolution for the LCE portfolio optimizer.

Loads the clean/low-carbon resource table (``data/lcoe/resource_costs.csv``) and
converts each row into the annualized-fixed-cost + VOM representation the LP
consumes, at the chosen low/mid/high sensitivity. Storage rows also carry
duration and round-trip efficiency.

Cost basis (finalized in ``docs/planning-sessions/PS-01`` and ``PS-03``):
  * ``lcoe_mwh``   — generation. ``fixed_mwyr = lcoe * cf_assumed * 8760`` so a
    resource running at its assumed capacity factor recovers exactly its LCOE.
  * ``fixed_mwyr`` — storage. The cost column is already an all-in annualized
    $/MW-yr for power+energy at the listed duration.

This is a *pay-for-capacity* treatment: capacity is paid for whether or not it
runs, so over-building to dump excess is correctly penalized. A PPA-style
pay-per-MWh alternative is a decision captured in PS-01.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from lce_portfolio.config import HOURS_PER_YEAR, PortfolioConfig

# Resolve the packaged cost table without any dependence on market_sim paths.
_PKG_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_COST_TABLE = _PKG_ROOT / "data" / "lcoe" / "resource_costs.csv"


@dataclass(frozen=True)
class ResourceArrays:
    """Struct-of-arrays view of the active resources, indexed by resource ``r``.

    Parallel arrays (length ``n_res``) plus a storage mask. Mirrors the
    market-sim ``FleetArrays`` pattern so the LP builder touches only numpy.
    """

    names: list[str]
    is_storage: np.ndarray  # (n_res,) bool
    fixed_mwyr: np.ndarray  # (n_res,) annualized $/MW-yr
    vom: np.ndarray  # (n_res,) $/MWh
    cap_max_mw: np.ndarray  # (n_res,) upper build bound
    cap_min_mw: np.ndarray  # (n_res,) lower build bound (existing floor)
    cf_assumed: np.ndarray  # (n_res,) placeholder CF (generation only)
    duration_h: np.ndarray  # (n_res,) storage energy/power hours (0 if not storage)
    rte: np.ndarray  # (n_res,) round-trip efficiency (1.0 if not storage)

    @property
    def n_res(self) -> int:
        """Number of active resources."""
        return len(self.names)

    @property
    def storage_idx(self) -> np.ndarray:
        """Indices ``r`` of storage resources, in resource order."""
        return np.flatnonzero(self.is_storage)


def _read_cost_table(path: Path) -> list[dict[str, str]]:
    """Read the resource-cost CSV into a list of row dicts."""
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def load_resource_arrays(
    config: PortfolioConfig,
    cost_table: Path | None = None,
) -> ResourceArrays:
    """Build :class:`ResourceArrays` for the resources active under ``config``.

    Selects rows by ``config.active_resources`` (or the table's
    ``active_minimal`` flag when unset), reads the ``config.lcoe_sensitivity``
    cost column, converts to annualized fixed cost, and applies per-resource
    cap/floor overrides from the config.
    """
    path = cost_table or DEFAULT_COST_TABLE
    rows = _read_cost_table(path)

    sens = config.lcoe_sensitivity
    if sens not in ("low", "mid", "high"):
        raise ValueError(f"lcoe_sensitivity must be low/mid/high, got {sens!r}")
    cost_col = f"cost_{sens}"

    if config.active_resources is not None:
        wanted = set(config.active_resources)
        rows = [r for r in rows if r["resource"] in wanted]
        missing = wanted - {r["resource"] for r in rows}
        if missing:
            raise ValueError(f"unknown resources requested: {sorted(missing)}")
    else:
        rows = [r for r in rows if r["active_minimal"].strip() == "1"]

    if not rows:
        raise ValueError("no active resources selected")

    names: list[str] = []
    is_storage, fixed_mwyr, vom = [], [], []
    cap_max, cap_min, cf_assumed, duration_h, rte = [], [], [], [], []

    for row in rows:
        name = row["resource"]
        basis = row["cost_basis"]
        cost = float(row[cost_col])
        cf = float(row["cf_assumed"])
        stor = row["category"] == "storage"

        if basis == "lcoe_mwh":
            # $/MWh LCOE -> annualized $/MW-yr at the assumed capacity factor.
            fixed = cost * cf * HOURS_PER_YEAR
        elif basis == "fixed_mwyr":
            fixed = cost
        else:
            raise ValueError(f"unknown cost_basis {basis!r} for {name}")

        cap = config.resource_caps_mw.get(name, float(row["cap_max_default_mw"]))
        floor = config.resource_floors_mw.get(name, 0.0)

        names.append(name)
        is_storage.append(stor)
        fixed_mwyr.append(fixed)
        vom.append(float(row["vom"]))
        cap_max.append(cap)
        cap_min.append(floor)
        cf_assumed.append(cf)
        duration_h.append(float(row["duration_h"]))
        rte.append(float(row["rte"]) if stor else 1.0)

    return ResourceArrays(
        names=names,
        is_storage=np.array(is_storage, dtype=bool),
        fixed_mwyr=np.array(fixed_mwyr, dtype=float),
        vom=np.array(vom, dtype=float),
        cap_max_mw=np.array(cap_max, dtype=float),
        cap_min_mw=np.array(cap_min, dtype=float),
        cf_assumed=np.array(cf_assumed, dtype=float),
        duration_h=np.array(duration_h, dtype=float),
        rte=np.array(rte, dtype=float),
    )
