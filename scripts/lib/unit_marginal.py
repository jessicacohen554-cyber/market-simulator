"""The committed per-unit layer of a keeper bundle: ``hourly/unit_marginal_<year>.parquet``.

Owner instruction 2026-10-01 (PJM-NEXT-18): keeper bundles carry the per-unit hourly
layer in every ISO, so a unit-grain question never again costs a keeper replay. The
full ``hourly/unit_hourly_<year>.parquet`` the solve writes is too large to commit
for a large ISO: PJM measures 69-81 MB per year, and 65 of every 77 MB is the raw
HiGHS ``red_cost`` float. The owner's decision card ("Slim layer") is the
construction here, a pure function of the full frame:

* every column of ``unit_hourly`` **except** ``red_cost`` (``mw``, ``cap_mw``, the
  P1 offer ``mc``, and the unit labels), unchanged and lossless;
* plus ``marginal`` (int8): 1 where the unit-hour is the LP's own price-setting
  column, i.e. interior by more than :data:`TOL_MW` off both bounds AND
  ``|red_cost| <= TOL_RC``. That is the PJM-NEXT-14 marginal-unit definition
  (``scripts/probes/_pjmnext14_lowend_lp.py``), so a census on this layer
  reproduces a census on the full frame exactly.

What is given up, stated: the distance-to-margin of a NON-marginal unit-hour (the
signed ``red_cost`` value). A question that needs it reads the full
``unit_hourly`` from a replay, which the solve still writes locally (gitignored).

Measured on the PJM 2020 keeper replay: 10.6 MB (vs 74 MB), 14,293 marginal
unit-hours, identical to the full-frame census. The conversion streams one
parquet row group at a time, so it never holds a second copy of a 25 M-row
frame (the MISO solve-memory constraint, ``FINDING-miso92``).
"""

from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

#: MW off both bounds before a unit-hour counts as interior (PJM-NEXT-14 definition,
#: ``_pjmnext14_lowend_lp.TOL_MW``): below it a column sits at a bound up to solver noise.
TOL_MW: float = 0.5
#: $/MWh reduced-cost tolerance for a basic (price-setting) column
#: (``_pjmnext14_lowend_lp.TOL_RC``); HiGHS reports basic columns at ~1e-9.
TOL_RC: float = 0.01
#: Low-cardinality label columns written dictionary-encoded.
DICT_COLS: tuple[str, ...] = (
    "pass",
    "unit_id",
    "plant_group",
    "fuel",
    "zone",
    "year",
    "plant_code",
)
#: Float columns that compress materially better byte-stream-split before zstd.
BSS_COLS: tuple[str, ...] = ("mw", "cap_mw", "mc")


def slim_table(t: pa.Table) -> pa.Table:
    """Return ``t`` (a ``unit_hourly`` slice) with ``red_cost`` replaced by ``marginal``.

    Args:
        t: A pyarrow table carrying at least ``mw``, ``cap_mw`` and ``red_cost``.

    Returns:
        The same rows, every column but ``red_cost`` unchanged, plus an int8
        ``marginal`` flag (1 = interior and ``|red_cost| <= TOL_RC``).
    """
    interior = pc.and_(
        pc.greater(t["mw"], TOL_MW),
        pc.less(t["mw"], pc.subtract(t["cap_mw"], TOL_MW)),
    )
    flag = pc.and_(interior, pc.less_equal(pc.abs(t["red_cost"]), TOL_RC))
    return t.drop(["red_cost"]).append_column("marginal", flag.cast(pa.int8()))


def write_unit_marginal(src: Path, out: Path) -> Path | None:
    """Stream ``src`` (a ``unit_hourly_<year>.parquet``) into the slim layer at ``out``.

    Args:
        src: Path to the full ``unit_hourly`` sidecar.
        out: Destination ``unit_marginal_<year>.parquet``.

    Returns:
        ``out``, or ``None`` when ``src`` does not exist or carries no ``red_cost``.
    """
    if not src.is_file():
        return None
    pf = pq.ParquetFile(src)
    if "red_cost" not in pf.schema_arrow.names:
        return None
    writer = None
    try:
        for i in range(pf.num_row_groups):
            t = slim_table(pf.read_row_group(i))
            if writer is None:
                writer = pq.ParquetWriter(
                    out,
                    t.schema,
                    compression="zstd",
                    compression_level=9,
                    use_dictionary=[c for c in DICT_COLS if c in t.schema.names],
                    use_byte_stream_split=[c for c in BSS_COLS if c in t.schema.names],
                    column_encoding={"hour": "DELTA_BINARY_PACKED"},
                )
            writer.write_table(t)
    finally:
        if writer is not None:
            writer.close()
    return out if writer is not None else None


def write_bundle_unit_marginal(
    bundle: Path, years: list[int] | None = None
) -> list[Path]:
    """Derive ``hourly/unit_marginal_<y>.parquet`` for every ``unit_hourly`` in a bundle.

    Args:
        bundle: A calibration bundle directory.
        years: Restrict to these years; default every ``unit_hourly_<y>`` present.

    Returns:
        The written paths.
    """
    hourly = bundle / "hourly"
    out: list[Path] = []
    for src in sorted(hourly.glob("unit_hourly_*.parquet")):
        y = int(src.stem.rsplit("_", 1)[-1])
        if years is not None and y not in years:
            continue
        p = write_unit_marginal(src, hourly / f"unit_marginal_{y}.parquet")
        if p is not None:
            out.append(p)
    return out


if __name__ == "__main__":
    import sys

    for path in write_bundle_unit_marginal(Path(sys.argv[1])):
        print(path, path.stat().st_size)
