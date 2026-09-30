"""R-CAISO-16 phase 0: is CISO's published Total interchange late inside the window?

Independent clock: OASIS SLD TAC actual ``CA ISO-TAC`` (``interval_start_gmt``).
CAISO load ~= net generation + net import, so d(TAC) is regressed on
d(NG shifted j) and d(-TI shifted k) for j, k in {-1, 0, +1} (shift +1 = the
published stamp is one hour LATE). The (j, k) with the highest R^2 names each
column's clock, per window (pre / in / post the generation late window) and
year. Zero fitted clock parameters; reads measured inputs only (rule 23).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from market_sim.config import paths  # noqa: E402
from market_sim.config.constants import EIA930_CISO_CLOCK_LATE_WINDOWS_UTC  # noqa: E402

LO, HI = (pd.Timestamp(s) for s in EIA930_CISO_CLOCK_LATE_WINDOWS_UTC["generation"])


def main() -> None:
    e = pd.read_parquet(paths.RAW_DATA_DIR / "eia-930-hourly" / "CISO hourly.parquet")
    utc = pd.DatetimeIndex(e["UTC time"])
    utc = utc.tz_convert("UTC").tz_localize(None) if utc.tz is not None else utc
    start = utc - pd.Timedelta(hours=1)  # hour-ending -> interval start (UTC)
    x = pd.DataFrame(
        {
            "ng": pd.to_numeric(e["Net generation"], errors="coerce").to_numpy(),
            "imp": -pd.to_numeric(e["Total interchange"], errors="coerce").to_numpy(),
        },
        index=start,
    )
    x = x[~x.index.duplicated()].asfreq("h")
    tac = []
    for yr in range(2019, 2026):
        t = pd.read_csv(
            paths.RAW_DATA_DIR
            / "zone-specific-demand"
            / "CAISO"
            / f"CAISO_tac_load_hourly_{yr}.csv"
        )
        t = t[t["tac_area"] == "CA ISO-TAC"]
        tac.append(
            pd.Series(
                t["mw"].to_numpy(float),
                index=pd.to_datetime(t["interval_start_gmt"], utc=True).dt.tz_localize(
                    None
                ),
            )
        )
    tac = pd.concat(tac)
    tac = tac[~tac.index.duplicated()].sort_index()
    rows = []
    for j in (-1, 0, 1):
        for k in (-1, 0, 1):
            d = pd.DataFrame(
                {
                    "tac": tac.diff(),
                    "ng": x["ng"]
                    .shift(-j)
                    .diff(),  # value published at t+j is true for t
                    "imp": x["imp"].shift(-k).diff(),
                }
            ).dropna()
            d = d[(d.index >= "2019-01-01") & (d.index < "2026-01-01")]
            d["win"] = np.where(
                d.index < LO,
                "pre",
                np.where(d.index <= HI - pd.Timedelta(hours=1), "in", "post"),
            )
            for (yr, w), g in d.groupby([d.index.year, "win"]):
                if len(g) < 300:
                    continue
                A = np.c_[np.ones(len(g)), g["ng"], g["imp"]]
                coef, *_ = np.linalg.lstsq(A, g["tac"].to_numpy(), rcond=None)
                res = g["tac"].to_numpy() - A @ coef
                r2 = 1 - res.var() / g["tac"].var()
                rows.append(
                    {
                        "year": yr,
                        "win": w,
                        "j_ng": j,
                        "k_ti": k,
                        "n": len(g),
                        "r2": r2,
                        "b_ng": coef[1],
                        "b_imp": coef[2],
                    }
                )
    df = pd.DataFrame(rows)
    best = (
        df.sort_values("r2")
        .groupby(["year", "win"])
        .tail(1)
        .sort_values(["year", "win"])
    )
    piv = df.pivot_table(
        index=["year", "win"], columns=["j_ng", "k_ti"], values="r2"
    ).round(3)
    pd.set_option("display.width", 220)
    print(piv.to_string())
    print(best.round(3).to_string(index=False))
    if len(sys.argv) > 1:
        df.to_csv(sys.argv[1], index=False)


if __name__ == "__main__":
    main()
