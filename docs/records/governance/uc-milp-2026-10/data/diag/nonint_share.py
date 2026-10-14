# UC-DIAG zero-LP reading (FINDING-ucmilp-diag-undercommit-2026-10-14). Usage: python <script> <bundle_dir> [<arm_dir>] <year>
import pandas as pd
import numpy as np
import sys

keeper, arm, yr = sys.argv[1], sys.argv[2], sys.argv[3]
s = pd.read_parquet(f"{arm}/hourly/system_{yr}.parquet")
s = s[s["pass"] == "P1"]
dem = s.groupby("hour").demand.sum()
pk = set(dem.sort_values().index[-100:])
u = pd.read_parquet(f"{arm}/hourly/uc_schedule_{yr}.parquet")
cls = u[["plant_code", "uc_class"]].drop_duplicates()


def load(b):
    m = pd.read_parquet(
        f"{b}/hourly/unit_marginal_{yr}.parquet",
        columns=["plant_code", "plant_group", "hour", "mw", "cap_mw"],
    )
    m = m[m.hour.isin(pk)]
    g = m.plant_group.str.upper()
    m["k"] = np.select(
        [
            g.str.startswith("CC"),
            g.str.startswith("COAL"),
            g.str.startswith("ST_GAS"),
            g.str.startswith("CT"),
        ],
        ["cc", "coal", "st_gas", "ct"],
        "other",
    )
    m = m.merge(cls, on="plant_code", how="left")
    m["integer"] = m.uc_class == m.k
    return m


K = load(keeper)
A = load(arm)
rows = {}
for k in ["cc", "st_gas", "coal"]:
    kk = K[K.k == k]
    aa = A[A.k == k]
    capK = kk.groupby("hour").cap_mw.sum().mean()
    capK_int = (
        kk[kk.integer].groupby("hour").cap_mw.sum().mean() if kk.integer.any() else 0
    )
    dK = kk.groupby("hour").mw.sum().mean()
    dA = aa.groupby("hour").mw.sum().mean()
    capA = aa.groupby("hour").cap_mw.sum().mean()
    rows[k] = dict(
        avail_cap=capK,
        nonint_share=1 - capK_int / capK if capK else np.nan,
        disp_keeper=dK,
        disp_arm=dA,
        P1_cap_arm=capA,
        sync_head_arm=capA - dA,
    )
print(arm.split("/")[-1], yr)
print(pd.DataFrame(rows).T.round(2).to_string())
