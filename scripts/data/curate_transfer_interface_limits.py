"""Curate the ``transfer-interface-limits`` clean datatype.

Measured hourly transmission-interface transfer limits (PJM Data Miner 2
``transfer_limits_and_flows`` for the committed 2023-2025 raw drops; other
ISOs additive via ``scripts/lib/transfer_interface_limits``) reconciled onto
the fixed non-leap 8760-hour ISO-local model clock — Feb 29 dropped, the DST
fall-back repeat merged by the clock-hour group-by, the spring-forward hour
filled from its neighbours and flagged (``n_source_rows = 0``). Pre- and
post-contingency variants of the same interface stay separate series.

Rule #13/#14 admissibility: an interface transfer limit is the RTO's
published operating-security transfer capability — a reproducible
physical/market input that regenerates every year from the same feed and
responds to changed grid conditions. Nothing here reads model outputs; the
measured ``transfer_mw`` column is carried only for crosswalk sanity checks
(binding frequency / flow direction), never as a dispatch target.

Writes one Parquet per (ISO, calendar year) via
:func:`scripts.lib.clean_io.write_clean`. Idempotent; reads only ``data/raw``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config import paths  # noqa: E402
from scripts.lib.clean_io import validate_clean, write_clean  # noqa: E402
from scripts.lib.transfer_interface_limits import (  # noqa: E402
    DATATYPE,
    IsoSpec,
    load_specs,
    to_model_clock,
)


def _curate_iso(spec: IsoSpec, raw_root: Path) -> list[Path]:
    """Curate every raw year found for one ISO spec; return written paths."""
    raw_dir = raw_root / spec.raw_subdir
    files = sorted(raw_dir.glob(spec.raw_glob))
    if not files:
        print(
            f"{spec.iso}: no {spec.raw_glob} files under {raw_dir} — see the "
            "README.md there for sources"
        )
        return []

    parsed = pd.concat([spec.parse(p) for p in files], ignore_index=True)
    # Overlapping drops (a re-upload, a supplement) must not double-count:
    # fully-identical rows collapse; genuinely distinct rows survive.
    parsed = parsed.drop_duplicates(ignore_index=True)
    years = sorted(parsed["ts_utc"].dt.tz_convert(spec.tz).dt.year.unique())

    source = "; ".join(
        [f"data/raw/{spec.raw_subdir}/{p.name}" for p in files]
        + [f"{spec.iso} published hourly interface transfer limits"]
    )
    written: list[Path] = []
    for year in years:
        hourly = to_model_clock(parsed, spec, int(year))
        if hourly.empty:
            continue
        path = write_clean(
            hourly, DATATYPE, iso=spec.iso, year=int(year), source=source
        )
        validate_clean(path)
        written.append(path)
        n_if = hourly["interface"].nunique()
        n_fill = int((hourly["n_source_rows"] == 0).sum())
        print(
            f"{spec.iso} {year}: {len(hourly)} rows across {n_if} interfaces "
            f"({n_fill} filled spring-forward hour rows) -> {path}"
        )
    return written


def curate(raw_root: Path | None = None, isos: list[str] | None = None) -> list[Path]:
    """Curate every registered ISO (or the requested subset).

    ``raw_root`` overrides ``data/raw`` for tests; ``isos`` filters to a
    subset of registered ISO codes. Returns the written clean paths.
    """
    raw_root = Path(raw_root) if raw_root is not None else paths.RAW_DIR
    specs = load_specs()
    wanted = {i.upper() for i in isos} if isos is not None else set(specs)
    written: list[Path] = []
    for iso, spec in sorted(specs.items()):
        if iso in wanted:
            written.extend(_curate_iso(spec, raw_root))
    return written


def main() -> None:
    """CLI entry point: curate the raw drops under ``data/raw`` (or override)."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--raw-root", default=None, help="Override the data/raw root (for testing)."
    )
    ap.add_argument(
        "--isos", nargs="*", default=None, help="Subset of ISO codes to curate."
    )
    args = ap.parse_args()
    written = curate(raw_root=args.raw_root, isos=args.isos)
    if not written:
        raise SystemExit(1)
    print(f"wrote {len(written)} clean file(s)")


if __name__ == "__main__":
    main()
