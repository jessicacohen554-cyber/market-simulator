"""Build ERCOT 2023 uncurtailed renewable potential (HSL) hourly profiles.

Downloads the UMass nodal-curtailment dataset (derived from ERCOT's 60-Day
SCED Disclosure Reports), aggregates the per-plant 15-minute High Sustained
Limit (HSL) and curtailment series into system-wide hourly totals, and writes
them to ``inputs/raw-data/ercot-hsl/ercot_2023_hsl_hourly.parquet``.

HSL is the uncurtailed generation *potential*: the most a resource could have
produced given wind/sun at that moment. Delivered generation is

    GEN = HSL - curtailment

so the GEN/HSL ratio yields the endogenous curtailment that a transmission-
constrained dispatch model should be able to reproduce.

Source dataset:
    https://github.com/codecexp/nodal-curtailment-analysis
    Maji, Irwin, Shenoy, Sitaraman (UMass Amherst), ACM e-Energy 2025.

Run:
    python scripts/build_ercot_hsl.py
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

REPO_URL = "https://github.com/codecexp/nodal-curtailment-analysis"
YEAR = 2023
HOURS_PER_YEAR = 8760
INTERVALS_PER_HOUR = 4  # 15-minute SCED telemetry

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "inputs" / "raw-data" / "ercot-hsl"
OUT_FILE = OUT_DIR / "ercot_2023_hsl_hourly.parquet"

# EIA-930 (Hourly Grid Monitor) reference totals for the ERCOT balancing
# authority, 2023, used only as a sanity check on the aggregated GEN series.
# Texas-wide wind/solar (~108 / ~32 TWh, EIA Today in Energy id=66464) is
# larger than the ERCOT BA alone because it also counts SPP Panhandle wind
# that lies outside ERCOT, so the ERCOT-only comparison is approximate.
EIA_REFERENCE_TWH = {"wind": 105.0, "solar": 32.0}


def clone_dataset(dest: Path) -> Path:
    """Shallow-clone the UMass nodal-curtailment dataset.

    Args:
        dest: Directory into which the repository is cloned.

    Returns:
        Path to the cloned repository's ``data`` directory.

    Raises:
        subprocess.CalledProcessError: if the ``git clone`` fails.
    """
    print(f"Cloning {REPO_URL} ...")
    subprocess.run(
        ["git", "clone", "--depth", "1", REPO_URL, str(dest)],
        check=True,
        capture_output=True,
    )
    return dest / "data"


def aggregate_system_hourly(data_dir: Path) -> pd.DataFrame:
    """Aggregate per-plant 15-minute series into system-wide hourly totals.

    For each of wind and solar, the per-plant HSL and curtailment CSVs are
    summed across plants at each 15-minute timestamp, then averaged over
    each block of four consecutive intervals to form an hourly MW series
    (an average of MW over an hour equals MWh of energy).

    The CSV timestamps are ERCOT local (Central) time and so contain a DST
    spring-forward gap and a fall-back repeat. Grouping by clock hour would
    yield 8759 distinct hours; instead the intervals are grouped positionally
    (four-at-a-time over the chronologically sorted rows), giving a clean,
    continuous 8760-hour sequence indexed 0..8759. Delivered generation is
    ``HSL - curtailment``, floored at zero and capped at HSL to absorb
    telemetry noise.

    Args:
        data_dir: The dataset's ``data`` directory holding the ERCOT CSVs.

    Returns:
        A DataFrame of 8760 rows with columns ``hour``, ``wind_gen_mw``,
        ``wind_hsl_mw``, ``solar_gen_mw``, ``solar_hsl_mw`` and a ``month``
        helper column (1-12).

    Raises:
        AssertionError: if a fuel does not aggregate to exactly 8760 hours.
    """

    def hourly_sum(csv_name: str) -> np.ndarray:
        """Sum a per-plant CSV across plants and average to hourly MW."""
        df = pd.read_csv(data_dir / csv_name)
        ts = pd.to_datetime(df["datetime"], format="%m/%d/%Y %H:%M:%S")
        system = df.drop(columns=["datetime"]).sum(axis=1)
        # Sort chronologically, then collapse each block of four 15-minute
        # intervals into one hour by position (DST-safe; see docstring).
        system = system[ts.argsort(kind="stable").to_numpy()].to_numpy()
        n_hours = len(system) // INTERVALS_PER_HOUR
        assert n_hours == HOURS_PER_YEAR, (
            f"{csv_name} has {len(system)} intervals -> {n_hours} hours, "
            f"expected {HOURS_PER_YEAR}"
        )
        return system.reshape(n_hours, INTERVALS_PER_HOUR).mean(axis=1)

    fuels = {}
    for fuel, hsl_csv, curt_csv in (
        (
            "wind",
            "ercotWindHSLByPlant-2023.csv",
            "ercotWindCurtailmentByPlant-2023.csv",
        ),
        (
            "solar",
            "ercotSolarHSLByPlant-2023.csv",
            "ercotSolarCurtailmentByPlant-2023.csv",
        ),
    ):
        hsl = hourly_sum(hsl_csv)
        curt = hourly_sum(curt_csv)
        gen = np.minimum(np.clip(hsl - curt, 0.0, None), hsl)
        fuels[fuel] = {"hsl": hsl, "gen": gen}

    out = pd.DataFrame(
        {
            "hour": np.arange(HOURS_PER_YEAR, dtype="int64"),
            "wind_gen_mw": fuels["wind"]["gen"],
            "wind_hsl_mw": fuels["wind"]["hsl"],
            "solar_gen_mw": fuels["solar"]["gen"],
            "solar_hsl_mw": fuels["solar"]["hsl"],
        }
    )
    # Calendar month per hour for the monthly curtailment breakdown. 2023 is
    # not a leap year, so a plain 8760-hour range maps cleanly to months.
    out["month"] = (
        pd.date_range("2023-01-01", periods=HOURS_PER_YEAR, freq="h")
        .month.to_numpy()
    )
    return out


def print_validation(df: pd.DataFrame) -> None:
    """Print annual totals, peaks, monthly curtailment and the EIA check.

    Args:
        df: The aggregated hourly DataFrame from
            :func:`aggregate_system_hourly`, including the ``month`` column.
    """
    print("\n=== ERCOT 2023 uncurtailed renewable potential (HSL) ===")
    print(f"Rows: {len(df)} (expected {HOURS_PER_YEAR})")

    for fuel in ("wind", "solar"):
        gen = df[f"{fuel}_gen_mw"]
        hsl = df[f"{fuel}_hsl_mw"]
        gen_twh = gen.sum() / 1e6
        hsl_twh = hsl.sum() / 1e6
        curt_pct = 100.0 * (1.0 - gen.sum() / hsl.sum())
        print(
            f"\n{fuel.capitalize()}:"
            f"\n  GEN  annual = {gen_twh:7.2f} TWh   peak = "
            f"{gen.max() / 1000:6.2f} GW"
            f"\n  HSL  annual = {hsl_twh:7.2f} TWh   peak = "
            f"{hsl.max() / 1000:6.2f} GW"
            f"\n  annual curtailment = {curt_pct:.2f}%"
        )

    print("\nMonthly curtailment rate (%):")
    print(f"  {'month':>5} {'wind':>8} {'solar':>8}")
    for month in range(1, 13):
        m = df[df["month"] == month]
        w = 100.0 * (1.0 - m["wind_gen_mw"].sum() / m["wind_hsl_mw"].sum())
        s = 100.0 * (1.0 - m["solar_gen_mw"].sum() / m["solar_hsl_mw"].sum())
        print(f"  {month:>5} {w:>8.2f} {s:>8.2f}")

    print("\nEIA-930 cross-check (delivered generation):")
    for fuel in ("wind", "solar"):
        gen_twh = df[f"{fuel}_gen_mw"].sum() / 1e6
        ref = EIA_REFERENCE_TWH[fuel]
        diff = 100.0 * (gen_twh - ref) / ref
        print(
            f"  {fuel:>5}: nodal {gen_twh:6.2f} TWh vs EIA ~{ref:.0f} TWh "
            f"({diff:+.1f}%)"
        )
    print(
        "  Note: EIA Texas-wide totals include SPP Panhandle wind outside\n"
        "  ERCOT, so the ERCOT-only nodal total is expected to run lower."
    )


def main() -> None:
    """Download, aggregate and write the ERCOT 2023 HSL hourly parquet."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        data_dir = clone_dataset(Path(tmp) / "nodal-curtailment-analysis")
        df = aggregate_system_hourly(data_dir)

    print_validation(df)

    table = pa.Table.from_pandas(
        df[["hour", "wind_gen_mw", "wind_hsl_mw", "solar_gen_mw",
            "solar_hsl_mw"]],
        preserve_index=False,
    )
    table = table.replace_schema_metadata(
        {
            "source": REPO_URL,
            "description": (
                "ERCOT 2023 system-wide hourly wind/solar HSL (uncurtailed "
                "potential) and delivered generation, aggregated from the "
                "UMass nodal-curtailment dataset (60-Day SCED Disclosure)."
            ),
            "units": "MW (hourly-average; numerically equal to MWh per hour)",
            "year": str(YEAR),
        }
    )
    pq.write_table(table, OUT_FILE)
    print(f"\nWrote {OUT_FILE.relative_to(REPO_ROOT)} "
          f"({OUT_FILE.stat().st_size / 1024:.1f} KiB)")


if __name__ == "__main__":
    sys.exit(main())
