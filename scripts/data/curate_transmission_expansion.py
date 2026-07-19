"""Curate the ``transmission-expansion`` clean datatype.

Reconciles each ISO's committed transmission-expansion registry (PUCT-ordered
Permian/765 kV work, MISO board-approved LRTP tranches, PJM RTEP designations,
CAISO TPP approvals, NYISO Tier 4 / public-policy selections, ISO-NE
state-contracted HVDC) onto the single tidy schema in
``data/dictionary/schema/transmission-expansion.schema.yaml`` and writes each
ISO partition through the frozen :func:`scripts.lib.clean_io.write_clean` seam.

Per-ISO parsing lives in ``scripts/lib/transmission_expansion/<iso>.py`` (each
registers an :class:`~scripts.lib.transmission_expansion.IsoSpec`); this script
is a thin dispatcher over the registry, so adding an ISO never touches it.
Every ``link``/``interface``/``import_tranche``/``intra_zonal`` row is
validated against the LIVE model topology
(:func:`market_sim.config.iso_configs.get_iso_config`): named zones must exist,
a ``link`` row's zone pair must resolve to a declared
:class:`~market_sim.config.iso_configs.TransferLink` in either orientation, and
an ``interface`` row's name must match a declared
:class:`~market_sim.config.iso_configs.InterfaceLimit` — so a typo or a
topology drift (e.g. the WP-A Far_West re-cut) fails loudly at curation rather
than silently uplifting the wrong corridor. ``in_service_year`` is a *column*
(the registry spans years), so each ISO writes one partition
``data/clean/transmission-expansion/<ISO>/…parquet`` (``year=None``). Reads
only ``data/raw``; idempotent. Run
``python scripts/data/curate_transmission_expansion.py [--isos ERCOT NEISO ...]``.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import pandas as pd

from scripts.lib import clean_io
from scripts.lib import transmission_expansion as tx
from scripts.lib.clean_io import paths

# Earliest plausible in-service year for a registry row: the model's earliest
# base-static vintage is 2023 (data.transmission_expansion.TRANSMISSION_BASE_STATIC_VINTAGE), so
# anything earlier is embedded in every ISO's base statics by construction and
# can never be additive — a row before this is a data-entry error, not history.
IN_SERVICE_FLOOR: int = 2023


def _rel(path: Path) -> str:
    """Path relative to the repo root for compact provenance (else absolute)."""
    try:
        return str(path.relative_to(paths.REPO_ROOT))
    except ValueError:
        return str(path)


def _validate_against_topology(iso: str, df: pd.DataFrame) -> None:
    """Raise if any row names a zone/link/interface the live topology lacks.

    Checks, per row: ``in_service_year >= IN_SERVICE_FLOOR``; every named
    ``from_zone``/``to_zone`` is a declared zone of the ISO; a ``link`` row's
    pair joins two zones connected by a declared TransferLink in either
    orientation; an ``interface`` row's ``interface_name`` matches a declared
    InterfaceLimit. ``import_tranche``/``intra_zonal`` rows only need their
    named zone(s) to exist (they are dispatch-inert in V1).
    """
    from market_sim.config.iso_configs import get_iso_config

    iso_config = get_iso_config(iso)
    zones = set(iso_config.zone_names)
    link_pairs = {(ln.from_zone, ln.to_zone) for ln in iso_config.links}
    interface_names = {lim.name for lim in iso_config.interface_limits}

    problems: list[str] = []
    for row in df.itertuples(index=False):
        label = f"{iso} {row.row_id}"
        year = row.in_service_year
        if pd.isna(year) or int(year) < IN_SERVICE_FLOOR:
            problems.append(
                f"{label}: in_service_year {year} < floor {IN_SERVICE_FLOOR} "
                f"(predates every base-static vintage; cannot be additive)"
            )
        for col in ("from_zone", "to_zone"):
            zone = getattr(row, col)
            if pd.notna(zone) and zone not in zones:
                problems.append(f"{label}: {col} {zone!r} not a {iso} model zone")
        kind = row.target_kind
        if kind == "link":
            a, b = row.from_zone, row.to_zone
            if (
                pd.notna(a)
                and pd.notna(b)
                and (a, b) not in link_pairs
                and (b, a) not in link_pairs
            ):
                problems.append(
                    f"{label}: no declared TransferLink joins ({a}, {b}) in "
                    f"either orientation"
                )
        elif kind == "interface":
            name = row.interface_name
            if pd.notna(name) and name not in interface_names:
                problems.append(
                    f"{label}: interface_name {name!r} not a declared "
                    f"InterfaceLimit (have: {sorted(interface_names)})"
                )
    if problems:
        raise ValueError(
            f"transmission-expansion topology validation failed for {iso}:\n  - "
            + "\n  - ".join(problems)
        )


def curate(
    raw_root: Path | None = None,
    isos: Iterable[str] | None = None,
) -> list[Path]:
    """Curate and write every requested ISO's transmission-expansion partition.

    Parameters
    ----------
    raw_root:
        Root of the raw tree (defaults to ``paths.RAW_DIR``); tests point it at
        a fixture directory.
    isos:
        Subset of ISOs to curate (default: every registered ISO). An ISO whose
        raw CSV has not landed yet (DATA NEEDED) yields an empty frame and is
        skipped.

    Returns the list of paths written. Reads only ``data/raw``; safe to re-run.
    """
    raw_root = Path(raw_root) if raw_root is not None else paths.RAW_DIR
    registry = tx.load_registry()
    wanted = [s.upper() for s in isos] if isos else sorted(registry)

    written: list[Path] = []
    for iso in wanted:
        df = tx.parse_iso(iso, raw_root)
        if df.empty:
            print(f"[skip] {iso}: no rows in {_rel(tx.raw_csv_for(iso, raw_root))}")
            continue
        _validate_against_topology(iso, df)
        source = _rel(tx.raw_csv_for(iso, raw_root))
        path = clean_io.write_clean(df, tx.DATATYPE, iso=iso, year=None, source=source)
        clean_io.validate_clean(path)
        written.append(path)
        live = int((~df["superseded"].astype(bool)).sum())
        applies = int(df["target_kind"].isin(["link", "interface"]).sum())
        print(f"wrote {path}  ({len(df)} rows, {live} live, {applies} apply-kind)")
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--isos",
        nargs="*",
        default=None,
        help="subset of ISOs to curate (default: every registered ISO)",
    )
    args = parser.parse_args(argv)
    written = curate(isos=args.isos)
    print(f"\n{len(written)} partition(s) written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
