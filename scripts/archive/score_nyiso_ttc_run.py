"""Score a NYISO backcast run's zonal RT LMP fit against the measured actuals.

Reads ``<run_dir>/system.parquet`` (the per-zone hourly clearing price the
calibration writes) and compares the P2 annual-mean price per zone to
``data/raw/_validation-source/actual_lmp.json["NYISO"][year]["zones"][zone]["rt"]``.
Highlights the Capital_Hudson - Upstate_West congestion spread that the
Central-East interface governs.

    uv run python scripts/archive/score_nyiso_ttc_run.py results/calibration/<run>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ZONES = ["Upstate_West", "Capital_Hudson", "Lower_Hudson", "NYC", "Long_Island"]
ACTUAL = Path("data/raw/_validation-source/actual_lmp.json")


def score(run_dir: Path, which_pass: str = "P2") -> None:
    df = pd.read_parquet(run_dir / "system.parquet")
    df = df[df["pass"] == which_pass]
    model = df.groupby(["year", "zone"])["price"].mean().unstack()
    actual = json.loads(ACTUAL.read_text())["NYISO"]

    for year in sorted(model.index):
        yr = str(year)
        if yr not in actual:
            continue
        act = {
            z: actual[yr]["zones"][z]["rt"] for z in ZONES if z in actual[yr]["zones"]
        }
        print(f"\n=== {year} (pass {which_pass}) ===")
        print(f"  {'zone':14} {'model':>7} {'actual':>7} {'err':>7}")
        errs = []
        for z in ZONES:
            if z not in act:
                continue
            m, a = model.loc[year, z], act[z]
            errs.append(m - a)
            print(f"  {z:14} {m:7.1f} {a:7.1f} {m - a:+7.1f}")
        mae = sum(abs(e) for e in errs) / len(errs)
        m_sp = model.loc[year, "Capital_Hudson"] - model.loc[year, "Upstate_West"]
        a_sp = act["Capital_Hudson"] - act["Upstate_West"]
        print(f"  {'MAE':14} {mae:7.2f}")
        print(
            f"  spread Cap-Up: model {m_sp:+.1f}  actual {a_sp:+.1f}  err {m_sp - a_sp:+.1f}"
        )


if __name__ == "__main__":
    score(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("."))
