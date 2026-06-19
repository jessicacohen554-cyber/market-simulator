"""Parse ERCOT RTM/DAM Load-Zone-&-Hub Settlement Point Prices into hourly series.

Reads the committed ERCOT SPP archives in ``data/raw/lmp-data/``
(``*RTMLZHBSPP_<year>.zip`` real-time 15-min, ``*DAMLZHBSPP_<year>.zip``
day-ahead hourly). Each zip holds ONE .xlsx with 12 monthly sheets (Jan..Dec);
read every sheet. RTM is averaged 15-min -> hourly. Writes
``data/raw/_validation-source/actual_lmp_zonal_ERCOT.parquet``
(year, hour, settlement_point, rt, da) on the fixed 8760-hour clock.

This is the per-hub/zone counterpart to the system HB_HUBAVG series in
``derive_actual_lmp.py`` — used to scope the spatial reliability-deployment
overlay on each pocket plant's LOCAL load-zone price (see
docs/spatial-ruc-session-prompt.md).

Schema note: RTM uses columns ``Settlement Point Name`` + ``Delivery Hour``
(int 1-24) + ``Delivery Interval`` (1-4); DAM uses ``Settlement Point`` +
``Hour Ending`` ("HH:00"). Both are handled.
"""
import io
import glob
import zipfile
from pathlib import Path

import pandas as pd

KEEP = {'HB_NORTH', 'HB_HOUSTON', 'HB_SOUTH', 'HB_WEST', 'HB_PAN', 'HB_BUSAVG',
        'HB_HUBAVG', 'LZ_NORTH', 'LZ_HOUSTON', 'LZ_SOUTH', 'LZ_WEST', 'LZ_AEN',
        'LZ_CPS', 'LZ_LCRA', 'LZ_RAYBN'}
LMP_DIR = Path("data/raw/lmp-data")


def _parse(pattern: str, market: str) -> pd.DataFrame:
    out = []
    for f in sorted(glob.glob(str(LMP_DIR / pattern))):
        yr = int(f.split("SPP_")[1][:4])
        z = zipfile.ZipFile(f)
        sheets = pd.read_excel(io.BytesIO(z.read(z.namelist()[0])),
                               engine="openpyxl", sheet_name=None)
        df = pd.concat(sheets.values(), ignore_index=True)
        df.columns = [c.strip() for c in df.columns]
        spcol = ("Settlement Point Name" if "Settlement Point Name" in df.columns
                 else "Settlement Point")
        if "Delivery Hour" in df.columns:
            hour1 = df["Delivery Hour"].astype(int)
        else:  # DAM: "Hour Ending" = "HH:00"
            hour1 = df["Hour Ending"].astype(str).str.split(":").str[0].astype(int)
        df = df.assign(_h1=hour1)
        df = df[df[spcol].isin(KEEP)].copy()
        df["hoy"] = ((pd.to_datetime(df["Delivery Date"])
                      - pd.Timestamp(f"{yr}-01-01")).dt.days * 24 + df["_h1"] - 1)
        g = (df.groupby([spcol, "hoy"])["Settlement Point Price"]
             .mean().reset_index())
        g.columns = ["settlement_point", "hour", market]
        g["year"] = yr
        out.append(g)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def main() -> None:
    rt = _parse("*RTMLZHBSPP_*.zip", "rt")
    da = _parse("*DAMLZHBSPP_*.zip", "da")
    if len(da):
        df = rt.merge(da, on=["year", "hour", "settlement_point"], how="outer")
    else:
        df = rt
    out = Path("data/raw/_validation-source/actual_lmp_zonal_ERCOT.parquet")
    df.sort_values(["year", "settlement_point", "hour"]).to_parquet(out, index=False)
    print(f"wrote {out}: {len(df)} rows, years {sorted(df.year.dropna().unique())}, "
          f"points {df.settlement_point.nunique()}")


if __name__ == "__main__":
    main()
