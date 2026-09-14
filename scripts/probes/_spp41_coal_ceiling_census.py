"""spp-41 step 2 (ZERO LP): is the model's PRB dispatch outside SPP's own measured envelope?

The question rule 1 ``[R-STRUCT]`` forces before any "hold coal back" mechanism
can be proposed: does the model's PRB fleet do something SPP's real coal fleet
demonstrably never did? A MEASURED ceiling is a real mechanism; a number chosen
to make 2022 score is the fitted adder the rule forbids.

Reads CAMPD unit-level hourly gross load for the model's own PRB plant set
(taken from the ``fleet_only`` rebuild, so the plant set is the model's, not a
hand list) across every vintage on disk, and reports per year:

* fleet annual energy (TWh) and fleet capacity factor against the model's pmax;
* the fleet's annual MAXIMUM hourly output, and its maximum sustained output at
  24 h / 168 h / 720 h averaging -- the shape a stockpile or rail constraint
  would bind on;
* the per-plant annual maximum, so a plant-level ceiling is visible;
* the model's own 2022 numbers beside them.

Run: ``python3 scripts/probes/_spp41_coal_ceiling_census.py``
"""

from __future__ import annotations

import glob
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

CACHE = Path(
    os.environ.get(
        "SPP41_CACHE",
        "/tmp/claude-0/-home-user-market-simulator/"
        "d1272d6d-a347-5fa8-85cd-cf88fd75dd3e/scratchpad/spp41",
    )
)
CAMPD = Path("data/raw/campd-unit-level")


def model_prb_plants() -> tuple[set[int], dict[int, float]]:
    """Return the model's PRB plant codes and their per-plant pmax (2022 fleet)."""
    z = np.load(CACHE / "rows_2022.npz", allow_pickle=True)
    klass = z["klass"].astype(str)
    uid = z["unit_id"].astype(str)
    pmax = z["pmax"].astype(float)
    m = klass == "COAL_PRB"
    codes: set[int] = set()
    tot: dict[int, float] = {}
    for u, p in zip(uid[m], pmax[m]):
        hit = re.search(r"_p(\d+)_", u)
        if not hit:
            continue
        c = int(hit.group(1))
        codes.add(c)
        tot[c] = tot.get(c, 0.0) + float(p)
    return codes, tot


def main() -> None:
    codes, pmax_by_plant = model_prb_plants()
    model_pmax = sum(pmax_by_plant.values())
    print(f"Model PRB plant set: {len(codes)} plants, {model_pmax:,.1f} MW pmax (2022 fleet)")

    frames: dict[int, pd.DataFrame] = {}
    for path in sorted(glob.glob(str(CAMPD / "*_*.parquet"))):
        year = int(Path(path).stem.split("_")[1])
        df = pd.read_parquet(path, columns=["facilityId", "date", "hour", "grossLoad"])
        df = df[df["facilityId"].astype(int).isin(codes)]
        if df.empty:
            continue
        frames.setdefault(year, [])
        frames[year].append(df)

    print(
        f"\n{'year':>5} {'plants':>7} {'TWh':>9} {'fleetCF':>8} "
        f"{'maxHr GW':>9} {'max24h':>8} {'max168h':>8} {'max720h':>8}"
    )
    for year in sorted(frames):
        df = pd.concat(frames[year], ignore_index=True)
        df["grossLoad"] = pd.to_numeric(df["grossLoad"], errors="coerce").fillna(0.0)
        ser = (
            df.groupby(["date", "hour"], observed=True)["grossLoad"]
            .sum()
            .sort_index()
            .to_numpy(dtype=float)
        )
        twh = ser.sum() / 1e6
        cf = ser.sum() / (model_pmax * len(ser)) if len(ser) else float("nan")

        def roll_max(n: int) -> float:
            if len(ser) < n:
                return float("nan")
            c = np.concatenate([[0.0], np.cumsum(ser)])
            return float(((c[n:] - c[:-n]) / n).max()) / 1000.0

        print(
            f"{year:>5} {df['facilityId'].nunique():>7} {twh:>9.2f} {cf:>8.3f} "
            f"{ser.max() / 1000:>9.2f} {roll_max(24):>8.2f} "
            f"{roll_max(168):>8.2f} {roll_max(720):>8.2f}"
        )

    print(
        "\nMODEL, 2022 (from the SPP-40 RESULT): 101.3 TWh, mean 11.56 GW, "
        "peak 17.91 GW, fleet CF "
        f"{101.3e6 / (model_pmax * 8760):.3f}"
    )
    print(
        "MODEL, 2021 (same source):            98.8 TWh\n"
        "ACTUAL, per the same source:          78.0 TWh (2022), 80.2 TWh (2021)"
    )

    # Per-plant annual maxima, to expose a plant-level ceiling if one exists.
    print("\nPer-plant annual MAX hourly gross load (MW), by year:")
    per: dict[int, dict[int, float]] = {}
    for year in sorted(frames):
        df = pd.concat(frames[year], ignore_index=True)
        df["grossLoad"] = pd.to_numeric(df["grossLoad"], errors="coerce").fillna(0.0)
        g = df.groupby(["facilityId", "date", "hour"], observed=True)["grossLoad"].sum()
        per[year] = g.groupby("facilityId").max().to_dict()
    years = sorted(per)
    head = "  plant  model_pmax " + " ".join(f"{y:>7}" for y in years)
    print(head)
    for c in sorted(codes, key=lambda c: -pmax_by_plant.get(c, 0)):
        row = " ".join(f"{per[y].get(c, float('nan')):>7.0f}" for y in years)
        print(f"  {c:>5}  {pmax_by_plant.get(c, 0):>10.1f} {row}")


if __name__ == "__main__":
    main()
