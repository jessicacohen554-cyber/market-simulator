"""Curate the ``nyiso-som-hub-fuel-annual`` clean datatype (Ask C1, annual floor).

Reads the hand-transcribed NYISO State-of-the-Market annual fuel-index price
table (``data/raw/gas-prices/nyiso_som_hub_fuel_annual.csv``; transcribed
from Figure A-6 of the 2020/2022/2023/2024/2025 SOM reports under
``data/raw/NYISO/``), shapes it onto
``data/dictionary/schema/nyiso-som-hub-fuel-annual.schema.yaml`` and writes a
single spanning partition through :func:`scripts.lib.clean_io.write_clean`.

This is the free measured Iroquois Zone 2 price *level* (annual); the daily/
monthly Z2 series remains Platts-licensed (Ask C1 licence ask). Index prices
exclude transportation charges and local taxes.

Run ``python scripts/data/curate_nyiso_som_hub_fuel_annual.py``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.lib import clean_io  # noqa: E402
from scripts.lib.clean_io import paths  # noqa: E402

DATATYPE = "nyiso-som-hub-fuel-annual"
_CSV = "nyiso_som_hub_fuel_annual.csv"


def _rel(path: Path) -> str:
    """Path relative to the repo root for compact provenance (else absolute)."""
    try:
        return str(path.relative_to(paths.REPO_ROOT))
    except ValueError:
        return str(path)


def build_frame(raw_root: Path) -> pd.DataFrame:
    """Read and dtype-shape the transcription CSV onto its schema."""
    df = pd.read_csv(raw_root / "gas-prices" / _CSV)
    df.insert(0, "iso", "NYISO")
    df["year"] = df["year"].astype("int64")
    df["price_usd_per_mmbtu"] = df["price_usd_per_mmbtu"].astype("float64")
    df["source_page"] = df["source_page"].astype("int64")
    return df


def curate(raw_root: Path | None = None) -> list[Path]:
    """Curate and write the spanning ``nyiso-som-hub-fuel-annual`` partition.

    Reads only ``data/raw``; safe to re-run. Returns the paths written.
    """
    raw_root = Path(raw_root) if raw_root is not None else paths.RAW_DIR
    df = build_frame(raw_root)
    path = clean_io.write_clean(
        df,
        DATATYPE,
        iso="NYISO",
        source=f"{_rel(raw_root / 'gas-prices' / _CSV)} (hand-transcribed from "
        "NYISO SOM Figure A-6 annual tables; PDFs under data/raw/NYISO/)",
    )
    clean_io.validate_clean(path)
    print(f"wrote {path}  ({len(df)} rows)")
    return [path]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    args = parser.parse_args(argv)
    del args
    written = curate()
    print(f"\n{len(written)} partition(s) written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
