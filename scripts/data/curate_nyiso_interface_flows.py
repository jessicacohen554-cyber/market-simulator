"""Curate the ``nyiso-interface-flows`` clean datatype (Ask D1).

Reads the hourly per-year interface flow/limit CSVs under
``data/raw/NYISO/interface-flows/`` (built from the NYISO MIS 5-minute
ExternalLimitsFlows posting by ``scripts/data/fetch_nyiso_interface_flows.py``;
aggregation documented there), shapes them onto
``data/dictionary/schema/nyiso-interface-flows.schema.yaml`` and writes one
clean partition per year through the frozen
:func:`scripts.lib.clean_io.write_clean` seam.

Reconciliation applied here (documented per CLAUDE.md rule 14): the source
posts +/-9999 MW as an "effectively unbounded" sentinel on interfaces whose
direction is not limit-monitored (e.g. WEST CENTRAL positive, most internal
interfaces' negative direction). Those sentinels are nulled so a consumer
never mistakes them for a measured rating; every |limit| >= _SENTINEL_MW is
treated as unposted.

Run ``python scripts/data/curate_nyiso_interface_flows.py [--years 2023 2024]``.
"""

from __future__ import annotations

import argparse
import sys
import re
from pathlib import Path

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.lib import clean_io  # noqa: E402
from scripts.lib.clean_io import paths  # noqa: E402

DATATYPE = "nyiso-interface-flows"

# Source sentinel for "no limit posted in this direction" (observed as
# +/-9999 across the 2018-2026 corpus; see fetch script docstring).
_SENTINEL_MW = 9999.0

_FILE_RE = re.compile(r"NYISO_interface_flows_hourly_(\d{4})\.csv\.gz$")


def _rel(path: Path) -> str:
    """Path relative to the repo root for compact provenance (else absolute)."""
    try:
        return str(path.relative_to(paths.REPO_ROOT))
    except ValueError:
        return str(path)


def _raw_dir(raw_root: Path) -> Path:
    return raw_root / "NYISO" / "interface-flows"


def build_year_frame(csv_path: Path) -> pd.DataFrame:
    """Read one hourly per-year raw CSV and shape it onto the schema."""
    df = pd.read_csv(csv_path)
    df.insert(0, "iso", "NYISO")
    df["interval_start_utc"] = pd.to_datetime(df["interval_start_utc"], utc=True)
    df["interval_start_local"] = pd.to_datetime(df["interval_start_local"])
    df["point_id"] = df["point_id"].astype("int64")
    df["n_intervals"] = df["n_intervals"].astype("int64")
    for col in ("flow_mw", "positive_limit_mw", "negative_limit_mw"):
        df[col] = df[col].astype("float64")
    for col in ("positive_limit_mw", "negative_limit_mw"):
        df[col] = df[col].where(df[col].abs() < _SENTINEL_MW)
    return df


def curate(raw_root: Path | None = None, years: list[int] | None = None) -> list[Path]:
    """Curate and write one ``nyiso-interface-flows`` partition per year.

    Parameters
    ----------
    raw_root:
        Root of the raw tree (defaults to ``paths.RAW_DIR``); tests point it
        at a fixture directory.
    years:
        Optional subset of years; default every year present in raw.

    Returns the list of paths written. Reads only ``data/raw``; safe to re-run.
    """
    raw_root = Path(raw_root) if raw_root is not None else paths.RAW_DIR
    written: list[Path] = []
    for csv_path in sorted(_raw_dir(raw_root).glob("*.csv.gz")):
        m = _FILE_RE.search(csv_path.name)
        if not m:
            continue
        year = int(m.group(1))
        if years is not None and year not in years:
            continue
        df = build_year_frame(csv_path)
        path = clean_io.write_clean(
            df,
            DATATYPE,
            iso="NYISO",
            year=year,
            source=f"{_rel(csv_path)} (NYISO MIS P-32 ExternalLimitsFlows via "
            "scripts/data/fetch_nyiso_interface_flows.py)",
        )
        clean_io.validate_clean(path)
        written.append(path)
        print(f"wrote {path}  ({len(df)} rows)")
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--years", nargs="*", type=int, default=None)
    args = parser.parse_args(argv)
    written = curate(years=args.years)
    print(f"\n{len(written)} partition(s) written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
