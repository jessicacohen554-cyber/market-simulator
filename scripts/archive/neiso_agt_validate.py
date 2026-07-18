"""Quick AGT daily-basis validation: modeled vs EIA-930 oil + winter LMP tail.

Reads a run bundle (dispatch + system + eia930) and reports, for the final
commitment pass, modeled oil TWh vs the measured EIA-930 ``NG: OIL`` column,
gas TWh, the load-weighted hub price, and the >$100 / >$200 hour counts — the
discriminating winter-tail metrics for the NEISO AGT calibration.

Usage: uv run python scripts/archive/neiso_agt_validate.py <run_dir> [<run_dir> ...]
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.lib.bundle_io import bundle_input_path  # noqa: E402


def _final_pass(df: pd.DataFrame) -> pd.DataFrame:
    order = sorted(df["pass"].unique(), key=lambda p: str(p))
    return df[df["pass"] == order[-1]]


def report(run_dir: Path) -> None:
    disp = _final_pass(
        pd.read_parquet(
            run_dir
            / "dispatch"
            / sorted(p.name for p in (run_dir / "dispatch").glob("*.parquet"))[-1]
        )
    )
    year = int(disp["year"].iloc[0])
    oil_twh = disp.loc[disp["fuel"] == "oil", "mw"].sum() / 1e6
    gas_twh = (
        disp.loc[disp["fuel"].str.contains("gas", case=False, na=False), "mw"].sum()
        / 1e6
    )

    sysdf = _final_pass(pd.read_parquet(run_dir / "system.parquet"))
    # Load-weighted hub price across zones, per hour.
    g = sysdf.groupby("hour")
    price = g.apply(
        lambda d: np.average(d["price"], weights=d["demand"].clip(lower=1e-6))
    )
    price = price.to_numpy()
    over100 = int((price > 100).sum())
    over200 = int((price > 200).sum())

    eia_oil = np.nan
    eia_path = bundle_input_path(run_dir, "eia930")
    if eia_path is not None:
        e = pd.read_parquet(eia_path)
        oil = e[e["series"] == "oil"]
        if not oil.empty:
            eia_oil = oil["mw"].clip(lower=0).sum() / 1e6

    print(f"{run_dir.name} ({year}):")
    print(f"  oil  TWh model={oil_twh:6.3f}  EIA-930={eia_oil:6.3f}")
    print(f"  gas  TWh model={gas_twh:6.2f}")
    print(f"  hub price avg=${price.mean():6.2f}  max=${price.max():7.1f}")
    print(f"  hours >$100={over100:4d}   >$200={over200:4d}")


if __name__ == "__main__":
    for d in sys.argv[1:]:
        report(Path(d))
