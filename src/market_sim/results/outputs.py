"""Structured simulation output assembly.

Extends :class:`~market_sim.model.dispatch.DispatchResult` with Parquet
serialization. The on-disk schema is one row per simulated hour; every
time-indexed array becomes a list-valued column whose entries hold that
hour's vector across generators, zones, storage units or links. Scalar
fields and array dimensions are stored in the table's schema metadata so a
saved result reconstructs exactly.
"""

import json
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from market_sim.model.dispatch import DispatchResult

_METADATA_KEY = b"market_sim"

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
    the vector across entities that becomes a single list cell.
    """
    by_hour = np.asarray(array, dtype=float).T
    return pa.array(by_hour.tolist(), type=pa.list_(pa.float64()))


def to_parquet(self: DispatchResult, path) -> Path:
    """Write this dispatch result to a Parquet file at ``path``.

    Args:
        path: Destination ``.parquet`` path; parent directories are created.

    Returns:
        The path written, as a :class:`~pathlib.Path`.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    T = self.dispatch.shape[1]  # T: number of hours
    columns: dict[str, pa.Array] = {
        "hour": pa.array(np.arange(T), type=pa.int32())
    }
    for col_name, attr, _optional in _ARRAY_COLUMNS:
        value = getattr(self, attr)
        if value is not None:
            columns[col_name] = _list_column(value)

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
    }

    table = pa.table(columns).replace_schema_metadata(
        {_METADATA_KEY: json.dumps(metadata).encode()}
    )
    pq.write_table(table, path)
    return path


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
        """Return the ``(n_entity, T)`` array stored under ``col_name``."""
        return np.array(table.column(col_name).to_pylist(), dtype=float).T

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
    )


DispatchResult.to_parquet = to_parquet
DispatchResult.from_parquet = classmethod(from_parquet)
