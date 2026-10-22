"""UC-SPP-WIND: fetch SPP `resource-forecast-by-reserve-zone` and reduce it to hourly ACTUALS.

Source: portal.spp.org file-browser, fsName=resource-forecast-by-reserve-zone ("Wind and Solar
Forecast for the next 168hrs and Actual for the previous 24hrs by Reserve Zone"), anonymous HTTPS.
Yearly ZIPs for 2017-2024 (/<y>/<y>.zip); 2025 is served per day (/2025/MM/DD/RF_RESERVE_ZONE-
YYYYMMDDHH00.csv) and the 00:00 and 12:00 files of each day are fetched (each restates the prior 24 h).
Reduction: for every (GMTIntervalEnd, ReserveZone) keep WindActualMW / SolarActualMW from the
latest-published file carrying a non-blank actual.

Usage: python fetch_reduce_rz_actuals.py <workdir> <out.csv.gz> [years...]
"""
import datetime as dt
import glob
import io
import os
import subprocess
import sys
import zipfile

import pandas as pd

B = "https://portal.spp.org/file-browser-api"
FS = "resource-forecast-by-reserve-zone"


def _get(url: str, out: str) -> bool:
    """curl one URL to a file; True on success."""
    r = subprocess.run(["curl", "-sS", "--fail", "--retry", "2", "-m", "600", url, "-o", out])
    return r.returncode == 0


def fetch(work: str, years: list[int]) -> None:
    """Download the yearly ZIPs (<=2024) or the per-day files (2025) into work/."""
    os.makedirs(work, exist_ok=True)
    for y in years:
        if y <= 2024:
            out = f"{work}/{y}.zip"
            if not os.path.exists(out):
                _get(f"{B}/download/{FS}?path=/{y}/{y}.zip", out)
            continue
        d, end = dt.date(y, 1, 1), dt.date(y + 1, 1, 1)
        with zipfile.ZipFile(f"{work}/{y}.zip", "w") as z:
            while d <= end:
                for hh in ("0000", "1200"):
                    f = f"RF_RESERVE_ZONE-{d:%Y%m%d}{hh}.csv"
                    tmp = f"{work}/{f}"
                    if _get(f"{B}/download/{FS}?path=/{d:%Y/%m/%d}/{f}", tmp):
                        z.write(tmp, f"{y}/{f}")
                        os.remove(tmp)
                d += dt.timedelta(1)


def reduce(work: str, years: list[int]) -> pd.DataFrame:
    """Latest-published actual per (GMT interval end, reserve zone) over the years' ZIPs."""
    frames = []
    for y in years:
        with zipfile.ZipFile(f"{work}/{y}.zip") as z:
            for n in sorted(z.namelist()):
                if not n.endswith(".csv"):
                    continue
                df = pd.read_csv(io.BytesIO(z.read(n)), skipinitialspace=True)
                df.columns = [c.strip() for c in df.columns]
                df = df[df.WindActualMW.notna() | df.SolarActualMW.notna()]
                if not df.empty:
                    df["pub"] = os.path.basename(n)[16:28]
                    frames.append(df[["GMTIntervalEnd", "ReserveZone", "WindActualMW", "SolarActualMW", "pub"]])
    a = pd.concat(frames)
    a["t_utc_end"] = pd.to_datetime(a.GMTIntervalEnd, format="%m/%d/%Y %H:%M:%S")
    a = a.sort_values("pub").groupby(["t_utc_end", "ReserveZone"]).last().reset_index()
    return a[["t_utc_end", "ReserveZone", "WindActualMW", "SolarActualMW", "pub"]]


if __name__ == "__main__":
    work, out = sys.argv[1], sys.argv[2]
    yrs = [int(v) for v in sys.argv[3:]] or list(range(2019, 2026))
    fetch(work, yrs)
    reduce(work, yrs).to_csv(out, index=False, compression="gzip")
