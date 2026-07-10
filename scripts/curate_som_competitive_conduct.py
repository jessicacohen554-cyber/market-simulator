"""Curate the ``som-competitive-conduct`` clean datatype.

Reads the hand-transcribed market-monitor competitive-conduct statistics
(``data/raw/som-competitive-conduct/som_competitive_conduct.csv``; price-cost
mark-up, output-gap economic-withholding levels, and the SOM coal
economic-offer vs must-run/self-commitment start decomposition — transcribed
from the Potomac Economics State-of-the-Market reports and IMM quarterlies,
PDFs under the ISO raw dirs, e.g. ``data/raw/MISO/``), shapes it onto
``data/dictionary/schema/som-competitive-conduct.schema.yaml`` and writes one
spanning partition per ISO through :func:`scripts.lib.clean_io.write_clean`.

Only train-window years are transcribed (CLAUDE.md rule 22; see the raw
README). Run ``python scripts/curate_som_competitive_conduct.py``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.lib import clean_io  # noqa: E402
from scripts.lib.clean_io import paths  # noqa: E402

DATATYPE = "som-competitive-conduct"
_CSV = "som_competitive_conduct.csv"


def _rel(path: Path) -> str:
    """Path relative to the repo root for compact provenance (else absolute)."""
    try:
        return str(path.relative_to(paths.REPO_ROOT))
    except ValueError:
        return str(path)


def build_frame(raw_root: Path) -> pd.DataFrame:
    """Read and dtype-shape the transcription CSV onto its schema."""
    df = pd.read_csv(raw_root / DATATYPE / _CSV)
    df["year"] = df["year"].astype("int64")
    df["value"] = df["value"].astype("float64")
    df["source_page"] = df["source_page"].astype("int64")
    for col in ("iso", "period", "fleet_segment", "metric", "unit", "source_doc"):
        df[col] = df[col].astype("string")
    return df


def curate(raw_root: Path | None = None, isos: list[str] | None = None) -> list[Path]:
    """Curate and write one spanning partition per ISO in the transcription.

    Reads only ``data/raw``; safe to re-run. ``isos`` filters which ISOs are
    written (default: every ISO present). Returns the paths written.
    """
    raw_root = Path(raw_root) if raw_root is not None else paths.RAW_DIR
    df = build_frame(raw_root)
    written: list[Path] = []
    for iso, part in df.groupby("iso", sort=True):
        if isos is not None and str(iso) not in isos:
            continue
        path = clean_io.write_clean(
            part.reset_index(drop=True),
            DATATYPE,
            iso=str(iso),
            source=f"{_rel(raw_root / DATATYPE / _CSV)} (hand-transcribed from "
            "the market monitor's SOM / IMM-quarterly PDFs under "
            f"data/raw/{iso}/; source_doc+source_page per row)",
        )
        clean_io.validate_clean(path)
        print(f"wrote {path}  ({len(part)} rows)")
        written.append(path)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--iso",
        action="append",
        dest="isos",
        help="Restrict to this ISO (repeatable; default: all in the CSV).",
    )
    args = parser.parse_args(argv)
    written = curate(isos=args.isos)
    print(f"\n{len(written)} partition(s) written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
