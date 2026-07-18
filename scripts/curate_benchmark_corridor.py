"""Curate the ``benchmark-corridor`` clean datatype.

Assembles every external forecast-corridor source (AEO2025 regional electricity
tables, NREL Standard Scenarios, ISO planning documents) onto the single tidy
schema in ``data/dictionary/schema/benchmark-corridor.schema.yaml`` and writes
ONE combined partition through the frozen
:func:`scripts.lib.clean_io.write_clean` seam — so FC-5 reads one parquet
(rubric §6). Per-source parsing lives in
``scripts/lib/benchmark_corridor/<source>.py`` (each registers a
:class:`~scripts.lib.benchmark_corridor.SourceSpec`); this script is a thin
dispatcher over the registry, so adding a source never touches it.

The target year is a *column* (sources span 2030/2035/2040 in one file), ISOs
span the whole frame, so the combined file is written with ``iso=None,
year=None`` at ``data/clean/benchmark-corridor/benchmark-corridor.parquet``.
Reads only ``data/raw``; idempotent (re-running rebuilds from whatever raw
sources are present). A registered source whose raw file has not landed yet is
reported as *missing*, never written as a placeholder value (rule 5).

``--emit-corridor-json`` writes the committed machine-readable anchor table the
FC-5 scorer reads as CONTEXT (``forecast_verdict.py --benchmark-corridor``).

Run:
    python scripts/curate_benchmark_corridor.py [--sources AEO2025 ...]
    python scripts/curate_benchmark_corridor.py --emit-corridor-json out.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

import pandas as pd

from scripts.lib import benchmark_corridor as bc
from scripts.lib import clean_io
from scripts.lib.clean_io import paths


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(paths.REPO_ROOT))
    except ValueError:
        return str(path)


def assemble(
    raw_root: Path | None = None, sources: Iterable[str] | None = None
) -> tuple[pd.DataFrame, list[str], list[str]]:
    """Parse every requested source and stack the rows into one canonical frame.

    Returns ``(df, present, missing)``: the combined frame (possibly empty),
    the sources that yielded rows, and the registered sources whose raw file is
    absent. Reads only ``data/raw``.
    """
    registry = bc.load_registry()
    wanted = list(sources) if sources else sorted(registry)
    frames: list[pd.DataFrame] = []
    present: list[str] = []
    missing: list[str] = []
    for source in wanted:
        if source not in registry:
            raise KeyError(f"unknown source {source!r}; registered: {sorted(registry)}")
        df = bc.parse_source(source, raw_root)
        if df.empty:
            missing.append(source)
            print(
                f"[missing] {source}: no raw rows under {_rel(bc.raw_dir_for(source, raw_root))}"
            )
            continue
        present.append(source)
        frames.append(df)
        print(f"[ok]      {source}: {len(df)} rows")
    if frames:
        combined = bc.finalize(pd.concat(frames, ignore_index=True))
    else:
        combined = pd.DataFrame(columns=list(bc.CANONICAL_COLUMNS))
    return combined, present, missing


def curate(
    raw_root: Path | None = None, sources: Iterable[str] | None = None
) -> list[Path]:
    """Assemble present sources and write the one combined clean partition.

    Returns the list of paths written (empty when no source has landed yet).
    """
    combined, present, missing = assemble(raw_root, sources)
    if combined.empty:
        print("[skip] no benchmark-corridor rows on disk yet (all sources missing)")
        return []
    src = "benchmark-corridor sources: " + ", ".join(present)
    if missing:
        src += " | missing: " + ", ".join(missing)
    path = clean_io.write_clean(combined, bc.DATATYPE, iso=None, year=None, source=src)
    clean_io.validate_clean(path)
    print(f"wrote {path}  ({len(combined)} rows; sources={present}; missing={missing})")
    return [path]


def emit_corridor_json(
    out_path: str | Path,
    raw_root: Path | None = None,
    sources: Iterable[str] | None = None,
    iso: str | None = None,
) -> Path:
    """Write the committed FC-5 context table (anchors + missing-source list).

    The JSON the forecast scorer reads via ``--benchmark-corridor``: anchor rows
    carry NO verdict (context only — divergence dispositions are authored by the
    scoring session, never here), plus the machine-readable missing-source list.
    """
    from market_sim.data import benchmark_corridor as loader

    combined, present, missing = assemble(raw_root, sources)
    payload = loader.corridor_context(combined, missing_sources=missing, iso=iso)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {out}  ({len(payload['rows'])} anchor rows; missing={missing})")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--sources",
        nargs="*",
        default=None,
        help="subset of sources to curate (default: every registered source)",
    )
    ap.add_argument(
        "--emit-corridor-json",
        dest="emit_corridor_json",
        default=None,
        help="also write the FC-5 context anchor table (JSON) here",
    )
    ap.add_argument(
        "--iso", default=None, help="restrict --emit-corridor-json to one ISO"
    )
    args = ap.parse_args(argv)

    curate(sources=args.sources)
    if args.emit_corridor_json:
        emit_corridor_json(args.emit_corridor_json, sources=args.sources, iso=args.iso)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
