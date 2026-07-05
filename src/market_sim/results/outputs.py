"""Structured simulation output assembly.

Extends :class:`~market_sim.model.dispatch.DispatchResult` with Parquet
serialization. The on-disk schema is one row per simulated hour; every
time-indexed array becomes a list-valued column whose entries hold that
hour's vector across generators, zones, storage units or links. Scalar
fields and array dimensions are stored in the table's schema metadata so a
saved result reconstructs exactly.
"""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from market_sim.data.fleet import FUEL_TYPE_NAMES
from market_sim.model.dispatch import DispatchResult

# Schema-metadata key for the dispatch result's scalars and dimensions.
_METADATA_KEY = b"market_sim"
# Schema-metadata key for the fleet context (see :class:`FleetContext`).
_FLEET_METADATA_KEY = b"market_sim_fleet"


@dataclass(frozen=True)
class FleetContext:
    """Fleet and resource attributes that produced a dispatch result.

    Stored in the Parquet schema metadata so an aggregated export can
    attribute dispatch to fuels and compute emissions and curtailment
    without re-deriving the fleet. The per-generator lists are aligned
    with the generator axis of :attr:`DispatchResult.dispatch`.

    Attributes:
        fuel_types: Fuel type of each generator.
        pmax_mw: Nameplate capacity of each generator, in MW.
        emission_rate: CO2 rate of each generator, in tCO2/MWh.
        efficiency_bins: Efficiency bin of each generator (e.g. ``h_class``,
            ``older``).
        heat_rates: Heat rate of each generator, in MMBtu/MWh.
        zones: Zone name of each generator (e.g. ``North``, ``Houston``).
        unit_ids: Generator unit identifier of each generator.
        wind_cap_mw: Total installed wind capacity, in MW.
        solar_cap_mw: Total installed solar capacity, in MW.
        wind_potential_mwh: Annual available wind energy (capacity factor
            times capacity, summed over zones and hours), in MWh.
        solar_potential_mwh: Annual available solar energy, in MWh.
        storage_energy_cap_mwh: Total storage energy capacity, in MWh.
    """

    fuel_types: list[str]
    pmax_mw: list[float]
    emission_rate: list[float]
    efficiency_bins: list[str]
    heat_rates: list[float]
    zones: list[str]
    unit_ids: list[str]
    wind_cap_mw: float
    solar_cap_mw: float
    wind_potential_mwh: float
    solar_potential_mwh: float
    storage_energy_cap_mwh: float
    # Model plant group per generator (CC_CHP, CC_REGULAR, COAL, CT_PEAKER,
    # CT_CHP, ST_GAS, ST_CHP), for ISOs whose dispatch classes come from the
    # group rather than the efficiency bin. Defaults empty for older contexts.
    plant_groups: list[str] = field(default_factory=list)

    @classmethod
    def from_arrays(
        cls,
        fleet,
        iso_config,
        wind_cf,
        wind_cap,
        solar_cf,
        solar_cap,
        storage_energy_cap,
    ) -> "FleetContext":
        """Build a context from a run's vectorized fleet and resource inputs.

        Args:
            fleet: The :class:`~market_sim.data.fleet.FleetArrays` dispatched.
            iso_config: The :class:`~market_sim.config.iso_configs.ISOConfig`
                whose zone ordering maps ``fleet.zone_idx`` back to zone names.
            wind_cf: Hourly wind capacity factor, shape ``(n_zones, T)``.
            wind_cap: Installed wind capacity per zone, shape ``(n_zones,)``.
            solar_cf: Hourly solar capacity factor, shape ``(n_zones, T)``.
            solar_cap: Installed solar capacity per zone, shape ``(n_zones,)``.
            storage_energy_cap: Storage energy capacity per unit.

        Returns:
            The assembled :class:`FleetContext`.
        """
        wind_cap = np.asarray(wind_cap, dtype=float)
        solar_cap = np.asarray(solar_cap, dtype=float)
        zone_names = iso_config.zone_names
        return cls(
            fuel_types=[FUEL_TYPE_NAMES[i] for i in fleet.fuel_type_idx],
            pmax_mw=[float(p) for p in fleet.pmax],
            emission_rate=[float(r) for r in fleet.emission_rate],
            efficiency_bins=list(fleet.efficiency_bin),
            heat_rates=[float(h) for h in fleet.heat_rate],
            zones=[zone_names[i] for i in fleet.zone_idx],
            unit_ids=list(fleet.unit_ids),
            plant_groups=(
                list(fleet.plant_group)
                if getattr(fleet, "plant_group", None) is not None
                else [""] * len(fleet.unit_ids)
            ),
            wind_cap_mw=float(wind_cap.sum()),
            solar_cap_mw=float(solar_cap.sum()),
            wind_potential_mwh=float(
                (np.asarray(wind_cf, dtype=float) * wind_cap[:, None]).sum()
            ),
            solar_potential_mwh=float(
                (np.asarray(solar_cf, dtype=float) * solar_cap[:, None]).sum()
            ),
            storage_energy_cap_mwh=float(
                np.asarray(storage_energy_cap, dtype=float).sum()
            ),
        )


# Per-hour list-valued columns and whether each is optional. Optional
# columns are omitted entirely when their source array is ``None``.
_ARRAY_COLUMNS: tuple[tuple[str, str, bool], ...] = (
    ("dispatch", "dispatch", False),
    ("wind", "wind_dispatched", False),
    ("solar", "solar_dispatched", False),
    ("slack", "slack", False),
    ("dump", "dump", False),
    ("price", "prices", False),
    ("storage_charge", "storage_charge", True),
    ("storage_discharge", "storage_discharge", True),
    ("storage_soc", "storage_soc", True),
    ("flows", "flows", True),
    ("emissions", "emissions", True),
)


def _list_column(array: np.ndarray) -> pa.Array:
    """Return a ``list<float64>`` column holding one row per hour.

    ``array`` has shape ``(n_entity, T)``; the transpose gives, per hour,
    the vector across entities that becomes a single list cell. The
    PyArrow column is built directly from the contiguous buffer, so no
    temporary Python float objects are materialized.
    """
    arr = np.ascontiguousarray(np.asarray(array).T, dtype=np.float64)
    T, n_entity = arr.shape
    flat = pa.array(arr.ravel(), type=pa.float64())
    offsets = pa.array(np.arange(0, (T + 1) * n_entity, n_entity, dtype=np.int32))
    return pa.ListArray.from_arrays(offsets, flat)


def to_parquet(
    self: DispatchResult,
    path,
    context: FleetContext | None = None,
    demand: np.ndarray | None = None,
) -> Path:
    """Write this dispatch result to a Parquet file at ``path``.

    Args:
        path: Destination ``.parquet`` path; parent directories are created.
        context: Optional fleet context written to the schema metadata so
            an aggregated export can interpret the dispatch arrays.
        demand: Optional ``(n_zones, T)`` served demand for the year, stored
            as a ``demand`` list-column so the forecast-invariant checker can
            verify the per-zone-hour energy balance without re-deriving load.
            Omitted (and ``has_demand`` False) for callers that do not supply
            it, keeping every existing reader unaffected.

    Returns:
        The path written, as a :class:`~pathlib.Path`.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    T = self.dispatch.shape[1]  # T: number of hours
    columns: dict[str, pa.Array] = {"hour": pa.array(np.arange(T), type=pa.int32())}
    for col_name, attr, _optional in _ARRAY_COLUMNS:
        value = getattr(self, attr)
        if value is not None:
            columns[col_name] = _list_column(value)
    if demand is not None:
        columns["demand"] = _list_column(np.asarray(demand, dtype=float))

    metadata = {
        "objective_value": self.objective_value,
        "status": self.status,
        "build_time": self.build_time,
        "solve_time": self.solve_time,
        "T": T,
        "n_gen": self.dispatch.shape[0],
        "n_zones": self.prices.shape[0],
        "has_storage": self.storage_soc is not None,
        "has_flows": self.flows is not None,
        "has_emissions": self.emissions is not None,
        "has_demand": demand is not None,
        "rps_shadow_price": self.rps_shadow_price,
    }

    schema_metadata = {_METADATA_KEY: json.dumps(metadata).encode()}
    if context is not None:
        schema_metadata[_FLEET_METADATA_KEY] = json.dumps(asdict(context)).encode()

    table = pa.table(columns).replace_schema_metadata(schema_metadata)
    pq.write_table(table, path)
    return path


def read_fleet_context(path) -> FleetContext:
    """Read the :class:`FleetContext` stored in a Parquet file's metadata.

    Args:
        path: Path to a ``.parquet`` file written by :func:`to_parquet`
            with a ``context``.

    Returns:
        The stored :class:`FleetContext`.

    Raises:
        FileNotFoundError: When ``path`` does not exist.
        ValueError: When the file carries no fleet context metadata.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"no cached dispatch result at {path}")

    raw_meta = (pq.read_schema(path).metadata or {}).get(_FLEET_METADATA_KEY)
    if raw_meta is None:
        raise ValueError(f"{path} carries no fleet context metadata")
    return FleetContext(**json.loads(raw_meta))


def read_demand(path) -> np.ndarray | None:
    """Return the ``(n_zones, T)`` served demand stored by :func:`to_parquet`.

    Args:
        path: Path to a ``.parquet`` file written by :func:`to_parquet`.

    Returns:
        The demand array, or ``None`` when the file predates the demand
        column (``has_demand`` absent/False) so callers can fall back.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"no cached dispatch result at {path}")
    schema = pq.read_schema(path)
    raw_meta = (schema.metadata or {}).get(_METADATA_KEY)
    if raw_meta is None or not json.loads(raw_meta).get("has_demand"):
        return None
    col = pq.read_table(path, columns=["demand"]).column("demand")
    flat = col.combine_chunks().values.to_numpy(zero_copy_only=False)
    n_zones = len(col[0].as_py())
    T_actual = len(col)
    return flat.reshape(T_actual, n_zones).T


def from_parquet(cls: type[DispatchResult], path) -> DispatchResult:
    """Load a dispatch result previously written by :func:`to_parquet`.

    Args:
        path: Path to a ``.parquet`` file written by :func:`to_parquet`.

    Returns:
        The reconstructed :class:`DispatchResult`.

    Raises:
        FileNotFoundError: When ``path`` does not exist.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"no cached dispatch result at {path}")

    table = pq.read_table(path)
    raw_meta = (table.schema.metadata or {}).get(_METADATA_KEY)
    if raw_meta is None:
        raise ValueError(f"{path} is missing market_sim schema metadata")
    meta = json.loads(raw_meta)

    def array(col_name: str) -> np.ndarray:
        """Return the ``(n_entity, T)`` array stored under ``col_name``.

        The list column's values buffer is read straight into NumPy, so
        no temporary Python float objects are materialized.
        """
        col = table.column(col_name)
        flat = col.combine_chunks().values.to_numpy(zero_copy_only=False)
        n_entity = len(col[0].as_py())
        T_actual = len(col)
        return flat.reshape(T_actual, n_entity).T

    has_storage = meta["has_storage"]
    has_flows = meta["has_flows"]
    has_emissions = meta["has_emissions"]

    return cls(
        dispatch=array("dispatch"),
        wind_dispatched=array("wind"),
        solar_dispatched=array("solar"),
        slack=array("slack"),
        dump=array("dump"),
        prices=array("price"),
        storage_charge=array("storage_charge") if has_storage else None,
        storage_discharge=array("storage_discharge") if has_storage else None,
        storage_soc=array("storage_soc") if has_storage else None,
        flows=array("flows") if has_flows else None,
        objective_value=meta["objective_value"],
        status=meta["status"],
        build_time=meta["build_time"],
        solve_time=meta["solve_time"],
        emissions=array("emissions") if has_emissions else None,
        rps_shadow_price=meta.get("rps_shadow_price"),
    )


DispatchResult.to_parquet = to_parquet
DispatchResult.from_parquet = classmethod(from_parquet)
