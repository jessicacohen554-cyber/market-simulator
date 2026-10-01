"""SPP-57 PRECOMMIT §3.4: the residual-South price p_S (the third point of the spread) from the
monthly RT LMP-by-settlement-location files, on the LMP builder's own calendar.

  P_SPS  = RT LMP of SPS's load-zone SL `SPS_SPS` (fallback where absent: mean of the SPS-area
           LOAD SLs GSEC_SPS / SPS_WTMN_SPS / WFEC_ENMC)
  P_SW   = simple mean of the SWEPCO-side SLs fixed by name in the PRECOMMIT
  p_S    = w_SPS * P_SPS + w_SW * P_SW, weights = the residual zone's measured 2023-25 energy
           composition E_SPS : (1 - w_OK) E_CSWS (per year)

Writes data/raw/_validation-source/actual_lmp_hourly_area_SPP.parquet (year, hour, p_sps, p_sw,
n_sw_sl, p_s, w_sps) and prints per-month SL coverage."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, "/home/user/market-simulator/scripts/data")
import build_spp_lmp_reference as b  # noqa: E402

S = Path(sys.argv[1])
OUT = Path(sys.argv[2])
SPS_LOAD = "SPS_SPS"
SPS_FALLBACK = ["GSEC_SPS", "SPS_WTMN_SPS", "WFEC_ENMC"]
SW = [
    "AECC_CSWS",
    "CSWARSENALHILL5",
    "CSWETTURK",
    "CSWMSTURK",
    "CSWSWTURK",
    "CSWFLINTCREEK1",
    "CSWJLSTALL",
    "CSWKNOXLEE5",
    "CSWLIEBERMAN3",
    "CSWLIEBERMAN4",
    "CSWMATTISON1",
    "CSWMATTISON2",
    "CSWMATTISON3",
    "CSWMATTISON4",
    "CSWNARROWS1",
    "CSWWELSH1",
    "CSWWELSH3",
    "CSWWILKES1",
    "CSWWILKES2",
    "CSWWILKES3",
    "CSWSEASTMAN",
    "AECC_ELKINS",
    "AECC_FITZHUGH",
    "AECC_FLTCREEK",
    "AECC_FULTON",
    "AECC_HYDRO13",
    "AECC_JWTURK",
    "CSWS.OMPA.TURK",
    "CSWS.AECC.FITZHUGH34",
]
# residual composition weights (PRECOMMIT §3.4; sub-BA energies x the EIA-861 w_OK, computed in
# the FINDING §2): E_SPS : (1 - w_OK) E_CSWS
W_SPS = {2023: 0.6053, 2024: 0.6218, 2025: 0.6205}
HUBS = ("SPPNORTH_HUB", "SPPSOUTH_HUB")

rows = []
cover = []
for year in (2023, 2024, 2025):
    frames = []
    for m in range(1, 13):
        f = S / "rt_sl" / f"RTBM-LMP-MONTHLY-SL-{year}{m:02d}.csv"
        df = pd.read_csv(f, skipinitialspace=True)
        df.columns = [c.strip() for c in df.columns]
        df = df[df["Price Type"] == "LMP"]
        names = set(df["Settlement Location Name"])
        sw_present = [n for n in SW if n in names]
        cover.append(
            {
                "year": year,
                "month": m,
                "sps_sps": SPS_LOAD in names,
                "n_sw": len(sw_present),
                "hubs": all(h in names for h in HUBS),
            }
        )
        df = df[
            df["Settlement Location Name"].isin(
                set(SW) | {SPS_LOAD} | set(SPS_FALLBACK) | set(HUBS)
            )
        ]
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)

    def dense(sl_set):
        rows_ = df[df["Settlement Location Name"].isin(sl_set)]
        if rows_.empty:
            return np.full(8760, np.nan), np.zeros(8760)
        grp = rows_.groupby("Date")[b.HE_COLS].mean()
        cnt = rows_.groupby("Date")[b.HE_COLS].count()
        return b._dense_from_daily(grp, year), b._dense_from_daily(cnt, year)

    p_sps, _ = dense({SPS_LOAD})
    p_fb, _ = dense(set(SPS_FALLBACK))
    p_sps = np.where(np.isnan(p_sps), p_fb, p_sps)
    p_sw, n_sw = dense(set(SW))
    p_n, _ = dense({"SPPNORTH_HUB"})
    p_ok, _ = dense({"SPPSOUTH_HUB"})
    w = W_SPS[year]
    p_s = w * p_sps + (1 - w) * p_sw
    rows.append(
        pd.DataFrame(
            {
                "year": year,
                "hour": np.arange(8760),
                "p_sps": p_sps,
                "p_sw": p_sw,
                "n_sw_sl": n_sw,
                "p_s": p_s,
                "w_sps": w,
                "p_n_rebuilt": p_n,
                "p_ok_rebuilt": p_ok,
            }
        )
    )
    print(
        year,
        "p_sps NaN",
        int(np.isnan(p_sps).sum()),
        "p_sw NaN",
        int(np.isnan(p_sw).sum()),
        "p_s NaN",
        int(np.isnan(p_s).sum()),
        "mean n_sw_sl",
        float(np.nanmean(n_sw)),
        flush=True,
    )
A = pd.concat(rows, ignore_index=True)
C = pd.DataFrame(cover)
print(C.to_string(index=False))
# cross-check: the rebuilt hubs against the committed per-hub parquet (rule 14 gate, SPP-14 §3.1)
L = pd.read_parquet(
    "/home/user/market-simulator/data/raw/_validation-source/actual_lmp_hourly_zonal_SPP.parquet"
)
P = L.pivot_table(index=["year", "hour"], columns="zone", values="rt")
M = A.set_index(["year", "hour"]).join(P)
for hub, col in (("SPPNORTH_HUB", "p_n_rebuilt"), ("SPPSOUTH_HUB", "p_ok_rebuilt")):
    d = (M[col] - M[hub]).abs()
    print(
        hub,
        "max |rebuilt - committed|",
        float(d.max()),
        "corr",
        float(M[[col, hub]].corr().iloc[0, 1]),
    )
A.drop(columns=["p_n_rebuilt", "p_ok_rebuilt"]).to_parquet(OUT, index=False)
C.to_csv(S / "bc" / "area_price_coverage.csv", index=False)
print("wrote", OUT, len(A))
