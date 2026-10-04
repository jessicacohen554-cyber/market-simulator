"""Zero-LP (closeout-SPP-w3 desk item 2): C3c 2023-25 tail hours on the SPP keeper -- event structure, DA, net-load rank, model headroom, wind ramp."""

import pandas as pd
import numpy as np

K = "results/calibration/closeout_spp_nuc_span/hourly/"
z = pd.read_parquet("data/raw/_validation-source/actual_lmp_hourly_SPP.parquet")
e = pd.read_parquet("data/raw/SWPP_fueltype.parquet").pivot_table(
    index="period", columns="fueltype", values="value_mwh"
)
for y in (2023, 2024, 2025):
    a = z[z.year == y].set_index("hour").reindex(range(8760))
    s = pd.read_parquet(K + f"system_{y}.parquet")
    s = s[s["pass"] == "P1"]
    mp = s.groupby("hour").apply(lambda b: (b.price * b.demand).sum() / b.demand.sum())
    dem = s.groupby("hour").demand.sum()
    um = pd.read_parquet(
        K + f"unit_marginal_{y}.parquet", columns=["fuel", "hour", "mw", "cap_mw"]
    )
    th = um[~um.fuel.astype(str).isin(["wind", "solar", "hydro", "nuclear"])]
    head = (th.cap_mw - th.mw).groupby(th.hour).sum()
    idx = pd.date_range(f"{y}-01-01 07:00", periods=8760, freq="h", tz="UTC")
    w = e.reindex(idx)["WND"].values
    df = pd.DataFrame(
        {"rt": a.rt, "da": a.da, "m": mp, "d": dem, "hdr": head, "wind": w}
    )
    df["dw"] = df.wind.diff()
    df["nl"] = df.d - df.wind
    df["mon"] = (pd.Timestamp(f"{y}-01-01") + pd.to_timedelta(df.index, unit="h")).month
    df["hod"] = df.index % 24
    t = df[df.rt > 200]
    print(
        y,
        "tail h",
        len(t),
        "| model price mean %.1f max %.1f | DA mean %.1f, DA>200 %d | headroom min/med %.0f/%.0f vs all-hours med %.0f"
        % (
            t.m.mean(),
            t.m.max(),
            t.da.mean(),
            (t.da > 200).sum(),
            t.hdr.min(),
            t.hdr.median(),
            df.hdr.median(),
        ),
    )
    print(
        "   netload pctile med %.2f | dwind med %.0f (all %.0f) | months %s | hod %s"
        % (
            (df.nl.rank(pct=True)[t.index]).median(),
            t.dw.median(),
            df.dw.median(),
            t.mon.value_counts().sort_index().to_dict(),
            t.hod.value_counts().sort_index().to_dict(),
        )
    )
    # consecutive clustering
    runs = (np.diff(t.index) != 1).sum() + 1 if len(t) else 0
    print(
        "   distinct events (runs of consecutive hours): %d ; days %d"
        % (runs, len(set(t.index // 24)))
    )
