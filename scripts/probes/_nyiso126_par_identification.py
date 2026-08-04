"""Phase-0 identification probe: does NYISO's published NY-NJ PAR interchange
percentage table reproduce in the measured P-34 ParFlows record?

Regresses each PAR PTID's measured hourly flow on the measured `SCH - PJ - NY`
hourly schedule (P-32 ExternalLimitsFlows, already intaken). If the posting
(NY-NJ_PAR_Interchange_and_OBF.pdf) is the real attribution rule, the PARs it
names at 16 % / 5 % / 7 % must show those slopes on measured data.

Keying is by LOCAL wall-clock (month, day, hour) on both sides, never positional.
"""

from __future__ import annotations

import glob
import io
import os
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

# P-34 ParFlows is NOT intaken (nyiso-126 filed no intake); point CACHE at a
# directory holding the monthly ParFlows zips fetched per the finding §1.4.
CACHE = Path(os.environ.get("NYISO_PARFLOWS_CACHE", "parflows-cache"))
REPO = Path(__file__).resolve().parents[2]


def load_parflows(year: int) -> pd.DataFrame:
    """Hourly-mean PAR flow per PTID, keyed by local wall-clock."""
    frames = []
    for z in sorted(glob.glob(str(CACHE / f"{year}??.zip"))):
        zf = zipfile.ZipFile(z)
        for n in zf.namelist():
            df = pd.read_csv(io.BytesIO(zf.read(n)))
            frames.append(df)
    pf = pd.concat(frames, ignore_index=True)
    ts = pd.to_datetime(pf["Timestamp"], format="%m/%d/%Y %H:%M:%S")
    pf["local_hour"] = ts.dt.floor("h")
    out = (
        pf.groupby(["local_hour", "Point ID"])["Flow (MWH)"]
        .mean()
        .unstack("Point ID")
    )
    return out


def load_pj_ny(year: int) -> pd.Series:
    p = REPO / "data/raw/NYISO/interface-flows" / f"NYISO_interface_flows_hourly_{year}.csv.gz"
    e = pd.read_csv(p)
    e = e[e["interface"] == "SCH - PJ - NY"].copy()
    e["local_hour"] = pd.to_datetime(e["interval_start_local"]).dt.floor("h")
    # the DST fall-back hour repeats one local wall-clock label; average it so
    # the key stays a unique (month, day, hour) on both sides of the join.
    return e.groupby("local_hour")["flow_mw"].mean().sort_index()


def main() -> None:
    for year in (2023, 2024, 2025):
        pf = load_parflows(year)
        pj = load_pj_ny(year)
        idx = pf.index.intersection(pj.index)
        pf, pj = pf.loc[idx], pj.loc[idx]
        print(f"\n===== {year}: {len(idx)} matched hours, "
              f"SCH-PJ-NY mean {pj.mean():+.1f} MW =====")
        rows = []
        for ptid in pf.columns:
            y = pf[ptid].to_numpy(float)
            x = pj.to_numpy(float)
            m = np.isfinite(x) & np.isfinite(y)
            if m.sum() < 1000 or np.std(y[m]) < 1e-9:
                continue
            slope = np.polyfit(x[m], y[m], 1)[0]
            r = np.corrcoef(x[m], y[m])[0, 1]
            rows.append((int(ptid), slope, r, float(np.mean(y[m]))))
        d = pd.DataFrame(rows, columns=["ptid", "slope", "r", "mean_mw"])
        d = d.sort_values("slope", ascending=False)
        print(d[(d["r"].abs() > 0.30)].to_string(index=False,
              float_format=lambda v: f"{v:8.4f}"))
        strong = d[d["r"].abs() > 0.30]
        print(f"  sum of slopes (|r|>0.30): {strong['slope'].sum():.4f}")


if __name__ == "__main__":
    main()
