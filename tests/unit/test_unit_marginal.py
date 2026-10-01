"""Tests for the committed per-unit keeper layer (``scripts/lib/unit_marginal.py``).

The layer drops ``red_cost`` and adds an int8 ``marginal`` flag; a unit-hour is
marginal iff it is interior by more than ``TOL_MW`` off both bounds AND its
reduced cost is within ``TOL_RC`` of zero (the PJM-NEXT-14 definition).
"""

import pyarrow as pa
import pyarrow.parquet as pq

from scripts.lib import unit_marginal as um


def _frame():
    # hour 0: interior, rc 0 -> marginal; 1: at pmin (mw 0) -> not; 2: at cap -> not;
    # 3: interior but rc 5 -> not; 4: interior, rc at the tolerance -> marginal.
    return pa.table(
        {
            "unit_id": ["u"] * 5,
            "hour": [0, 1, 2, 3, 4],
            "mw": pa.array([50.0, 0.0, 100.0, 40.0, 60.0], pa.float32()),
            "cap_mw": pa.array([100.0] * 5, pa.float32()),
            "mc": pa.array([20.0] * 5, pa.float32()),
            "red_cost": pa.array([0.0, 3.0, -2.0, 5.0, um.TOL_RC], pa.float32()),
        }
    )


def test_slim_table_flags_exactly_the_interior_zero_rc_rows():
    out = um.slim_table(_frame())
    assert "red_cost" not in out.schema.names
    assert out["marginal"].to_pylist() == [1, 0, 0, 0, 1]
    assert out["mw"].to_pylist() == _frame()["mw"].to_pylist()


def test_write_unit_marginal_streams_every_row_group(tmp_path):
    src = tmp_path / "hourly" / "unit_hourly_2020.parquet"
    src.parent.mkdir()
    pq.write_table(_frame(), src, row_group_size=2)  # three row groups
    paths = um.write_bundle_unit_marginal(tmp_path)
    assert paths == [tmp_path / "hourly" / "unit_marginal_2020.parquet"]
    got = pq.read_table(paths[0])
    assert got.num_rows == 5 and got["marginal"].to_pylist() == [1, 0, 0, 0, 1]


def test_missing_source_writes_nothing(tmp_path):
    assert (
        um.write_unit_marginal(tmp_path / "nope.parquet", tmp_path / "o.parquet")
        is None
    )


def test_promote_preflight_derives_or_refuses(tmp_path):
    from scripts import promote_keeper as pk

    hourly = tmp_path / "hourly"
    hourly.mkdir()
    pq.write_table(_frame(), hourly / "unit_hourly_2023.parquet")
    # 2023 derivable, 2024 has neither: a NEW keeper is refused ...
    try:
        pk.ensure_unit_marginal(tmp_path, [2023, 2024], new=True)
        raise AssertionError("expected refusal")
    except SystemExit as exc:
        assert "[2024]" in str(exc)
    assert (hourly / "unit_marginal_2023.parquet").exists()
    # ... a re-designated keeper only warns.
    assert pk.ensure_unit_marginal(tmp_path, [2023, 2024], new=False) == [2024]
