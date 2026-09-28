"""PJM-NEXT-7 zero-LP census: what removing the cleared net virtual position
from the PHYSICAL balance would do, per class and to the price, estimated from
the keeper's own committed hourlies (no LP).

Method (a merit-order envelope, labelled an ESTIMATE, not a solve): per
year x month, S_t = Σ responsive-class MW (thermal + import + storage net);
the net virtual position v_t = −(VIRTUAL_DEC + VIRTUAL_INC) MW (positive =
net virtual DEMAND served physically). Class c's month envelope f_c(S) is the
running mean of its MW over hours sorted by S; the counterfactual is
f_c(S_t − v_t) − f_c(S_t). Price envelope likewise from system_<y> (load-
weighted over zones). Keeper: results/calibration/pjmnext6_sp_span.
"""

import gzip
import json
import numpy as np
import pandas as pd

B = "results/calibration/pjmnext6_sp_span/hourly"
FIXED = {"wind", "solar", "nuclear", "hydro", "VIRTUAL_DEC", "VIRTUAL_INC"}
WIN = 101  # hours in the running-mean window (resolution only)


def envelope(S, Y):
    o = np.argsort(S)
    ys = pd.Series(Y[o]).rolling(WIN, center=True, min_periods=1).mean().to_numpy()
    return S[o], ys


def run(y):
    ch = pd.read_parquet(f"{B}/class_hourly_{y}.parquet")
    ch = (
        ch[ch["pass"] == "P1"]
        .pivot_table(
            index="hour", columns="klass", values="mw", aggfunc="sum", observed=True
        )
        .fillna(0.0)
    )
    sy = pd.read_parquet(f"{B}/system_{y}.parquet")
    sy = sy[sy["pass"] == "P1"]
    g = sy.groupby("hour")
    price = (
        (g.apply(lambda d: (d.price * d.demand).sum() / d.demand.sum()))
        .reindex(ch.index)
        .to_numpy()
    )
    v = -(ch.get("VIRTUAL_DEC", 0) + ch.get("VIRTUAL_INC", 0)).to_numpy()
    resp = [c for c in ch.columns if c not in FIXED]
    S = ch[resp].sum(axis=1).to_numpy()
    T = len(S)
    month = (np.arange(T) // 730).clip(0, 11)
    d = {c: 0.0 for c in resp}
    dp = np.zeros(T)
    for m in range(12):
        idx = np.where(month == m)[0]
        Sm, vm = S[idx], v[idx]
        for c in resp:
            xs, ys = envelope(Sm, ch[c].to_numpy()[idx])
            d[c] += (np.interp(Sm - vm, xs, ys) - np.interp(Sm, xs, ys)).sum() / 1e6
        xs, ps = envelope(Sm, price[idx])
        dp[idx] = np.interp(Sm - vm, xs, ps) - np.interp(Sm, xs, ps)
    lw = sy.groupby("hour").demand.sum().reindex(ch.index).to_numpy()
    b = json.load(gzip.open(f"frontend/data/backcast/bench/PJM/{y}.json.gz"))["bench"]
    cf = b["classFull"]
    mdl = ch.sum() / 1e6
    mprice = (price * lw).sum() / lw.sum()
    out = {
        "year": y,
        "net_virt_TWh": v.sum() / 1e6,
        "price_model": mprice,
        "price_cf": ((price + dp) * lw).sum() / lw.sum(),
        "rt_lw": b["avgLMP"]["rt_lw"],
    }
    for c in ("CC_REGULAR", "COAL_BIT", "CT_PEAKER", "ST_GAS", "import"):
        out[f"d_{c}"] = d.get(c, 0.0)
        if c in cf:
            out[f"err_{c}"] = mdl.get(c, 0) - cf[c]
            out[f"errcf_{c}"] = mdl.get(c, 0) + d.get(c, 0) - cf[c]
    return out


rows = [run(y) for y in range(2019, 2026)]
df = pd.DataFrame(rows).set_index("year")
pd.set_option("display.width", 250)
print(df.round(2).T.to_string())
