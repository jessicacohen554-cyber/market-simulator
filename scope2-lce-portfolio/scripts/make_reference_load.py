#!/usr/bin/env python
"""Generate the stylized ADR-ratification reference load.

Writes ``data/reference/reference_load_100mw.csv`` — a deterministic 8760
hourly load shape (long form: ``hour, iso, load_mwh, facility``) replicated
identically across all six supported ISOs. This is a **stylized reference
case for ADR (Anchor Data center Ratification) wiring validation**, not
measured customer data: a 100 MW-average data-center-style facility with a
mild diurnal swing (cooling/IT load varies gently through the day, unlike a
commercial building's sharp daytime peak — data centers run close to flat).

Determinism: pure function of the constants below, no RNG and no wall-clock,
so re-running reproduces the file byte-for-byte (mirrors ADR 0011's
reproducibility spirit and ``examples/run_sample_sweep.py``'s synthetic-input
pattern).

Usage (run from inside ``scope2-lce-portfolio/``)::

    ../.venv/bin/python scripts/make_reference_load.py
    ../.venv/bin/python scripts/make_reference_load.py --out /tmp/foo.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

HOURS_PER_YEAR = 8760
AVG_LOAD_MW = 100.0
DIURNAL_SWING_FRACTION = 0.10  # +/-10% around the 100 MW average
FACILITY_NAME = "adr_reference_facility"
ISOS: tuple[str, ...] = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO")

_TOOL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_PATH = _TOOL_ROOT / "data" / "reference" / "reference_load_100mw.csv"


def make_shape(hours_per_year: int = HOURS_PER_YEAR) -> np.ndarray:
    """Return the deterministic ``(hours_per_year,)`` load-shape vector (MWh).

    A cosine with period 24h, trough at midnight and peak at midday (cooling
    load tracks ambient/solar-heating load through the day); the discrete
    24-hour cosine's mean is (numerically) exactly 0, so the annual average
    is exactly :data:`AVG_LOAD_MW` regardless of swing amplitude.
    """
    hod = np.arange(hours_per_year) % 24  # t: hour of day
    diurnal = np.cos((hod - 12) / 24.0 * 2 * np.pi)
    return AVG_LOAD_MW * (1.0 + DIURNAL_SWING_FRACTION * diurnal)


def build_reference_load(isos: tuple[str, ...] = ISOS) -> pd.DataFrame:
    """Return the long-form ``(hour, iso, load_mwh, facility)`` reference load.

    The identical 8760 shape from :func:`make_shape` is replicated across
    every ISO in ``isos`` (same stylized facility sited in each market).
    """
    hours = np.arange(HOURS_PER_YEAR)
    shape = make_shape()
    frames = [
        pd.DataFrame(
            {
                "hour": hours,
                "iso": iso,
                "load_mwh": shape,
                "facility": FACILITY_NAME,
            }
        )
        for iso in isos
    ]
    return pd.concat(frames, ignore_index=True)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: write the reference-load CSV, print a sanity summary."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out", type=Path, default=DEFAULT_OUT_PATH, help="output CSV path."
    )
    args = parser.parse_args(argv)

    df = build_reference_load()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False, float_format="%.3f")

    per_iso = df.groupby("iso")["load_mwh"]
    print(
        f"wrote {args.out} ({len(df)} rows, {len(ISOS)} ISOs x {HOURS_PER_YEAR} hours)"
    )
    for iso, mean in per_iso.mean().items():
        print(
            f"  {iso:7} mean={mean:.2f} MW min={per_iso.min()[iso]:.2f} max={per_iso.max()[iso]:.2f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
