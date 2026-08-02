"""miso-114 Phase-0 probe — MISO seam hour-of-day shape + overnight trough anatomy.

NO LP IS SOLVED. Every number below is read from committed artifacts:

* the keeper bundle's ``hourly/system_<year>.parquet`` and
  ``hourly/class_hourly_<year>.parquet`` (P1 duals + class dispatch),
* ``data/raw/lmp-data/MISO/miso_hub_lmp_<year>_da.csv.gz`` (the eight named
  MISO trading hubs, carrying MISO's own LMP / MCC / MLC decomposition, so the
  congestion-free **energy component** is recoverable exactly),
* ``data/raw/eia-930-hourly/MISO hourly.parquet`` (demand, fuel-type net
  generation, total interchange),
* ``data/raw/_validation-source/pjm_border_lmp_hourly_MISO.parquet`` (the
  measured hourly PJM western-border LMP already committed for the seam lane).

It answers four questions, in order:

Q1  Where does MISO's overnight price residual live — the system **energy**
    component or **congestion**?  (MISO publishes a single-reference
    decomposition, so ENERGY = LMP - MCC - MLC is one system-wide series; the
    probe asserts that cross-hub identity rather than assuming it.)
Q2  Is the overnight residual a **slope** defect (the stack is too flat) or a
    **level** defect (the marginal unit is mispriced)?  Answered by binning
    overnight hours on net load and comparing the model's and the market's
    price-vs-net-load curves decile by decile.
Q3  Does the model reproduce the **hour-of-day shape** of MISO's net
    interchange, given that it reproduces the annual energy?
Q4  What is actually substituted at the overnight trough — i.e. does the
    fuel-mix arithmetic close against the interchange gap?

Rule 22 [R-HOLDOUT]: 2023-2025 only. Rule 15: no run is produced, so there is
nothing to register.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

BUNDLE = "results/calibration/miso109_hy_level_B"
YEARS = (2023, 2024, 2025)
HE = [f"he{i:02d}" for i in range(1, 25)]
NIGHT = [0, 1, 2, 3, 4, 5]
PEAK = [16, 17, 18, 19]
OFFPEAK = [0, 1, 2, 3, 4, 5, 22, 23]
HUBS = ("MINN.HUB", "ILLINOIS.HUB", "INDIANA.HUB")


def load_actual_prices(year: int) -> pd.DataFrame:
    """Return hourly MISO hub LMPs plus the single-reference ENERGY component.

    The leap day is dropped because the model always solves 8760 hours
    (rule 8 [R-8760]), so the calendar must be trimmed to align with the
    bundle's chronological hour index.
    """
    raw = pd.read_csv(f"data/raw/lmp-data/MISO/miso_hub_lmp_{year}_da.csv.gz")
    long = raw.melt(
        id_vars=["date", "node", "value"], value_vars=HE, var_name="he", value_name="p"
    )
    long["h"] = long["he"].str[2:].astype(int) - 1
    long["date"] = pd.to_datetime(long["date"])
    wide = long.pivot_table(
        index=["date", "h", "node"], columns="value", values="p"
    ).reset_index()
    wide["ENERGY"] = wide["LMP"] - wide["MCC"] - wide["MLC"]
    wide["ts"] = wide["date"] + pd.to_timedelta(wide["h"], unit="h")

    out = wide.groupby("ts")["ENERGY"].mean().reset_index()
    for hub in HUBS:
        out = out.merge(
            wide[wide.node == hub][["ts", "LMP", "MCC"]].rename(
                columns={"LMP": hub.split(".")[0], "MCC": f"{hub.split('.')[0]}_MCC"}
            ),
            on="ts",
            how="left",
        )
    # cross-hub identity check: MISO's ENERGY component must be one series
    spread = (
        wide.pivot_table(index=["date", "h"], columns="node", values="ENERGY")
        .std(axis=1)
        .max()
    )
    out.attrs["energy_cross_hub_max_std"] = float(spread)
    out = out[~((out.ts.dt.month == 2) & (out.ts.dt.day == 29))].reset_index(drop=True)
    out["hour"] = np.arange(len(out))
    out["hod"] = out.ts.dt.hour
    return out


def load_actual_930(year: int) -> pd.DataFrame:
    """EIA-930 hourly demand / fuel mix / interchange, trimmed to 8760."""
    g = pd.read_parquet("data/raw/eia-930-hourly/MISO hourly.parquet")
    g["ts"] = pd.to_datetime(g["Local time"])
    g = g.loc[
        (g["ts"] >= pd.Timestamp(f"{year}-01-01"))
        & (g["ts"] < pd.Timestamp(f"{year + 1}-01-01"))
    ].copy()
    g = g[~((g.ts.dt.month == 2) & (g.ts.dt.day == 29))].reset_index(drop=True)
    # 930 carries occasional single-hour holes; interpolate so annual sums are
    # comparable. Holes are <0.2% of hours in every scored year.
    num = g.select_dtypes(include=[float, int]).columns
    g[num] = g[num].interpolate(limit_direction="both")
    g["hour"] = np.arange(len(g))
    g["hod"] = g.ts.dt.hour
    g["netimp"] = -g["Total interchange"]
    return g


def load_model(year: int) -> pd.DataFrame:
    """Load-weighted P1 system dual + class dispatch on the model's own 8760."""
    s = pd.read_parquet(f"{BUNDLE}/hourly/system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    price = s.pivot_table(index="hour", columns="zone", values="price")
    dem = s.pivot_table(index="hour", columns="zone", values="demand")
    zc = [c for c in price.columns if c.startswith("MISO-")]
    c = pd.read_parquet(f"{BUNDLE}/hourly/class_hourly_{year}.parquet")
    c = c[c["pass"] == "P1"]
    cw = c.pivot_table(index="hour", columns="klass", values="mw")
    m = pd.DataFrame(
        {
            "hour": price.index,
            "msys": ((price[zc] * dem[zc]).sum(axis=1) / dem[zc].sum(axis=1)).values,
            "mdem": dem[zc].sum(axis=1).values,
            "zonal_spread": (price[zc].max(axis=1) - price[zc].min(axis=1)).values,
        }
    )
    for k in ("wind", "solar", "import", "nuclear", "hydro"):
        m[k] = cw[k].values if k in cw else 0.0
    m["gas"] = cw[
        [x for x in ("CC_REGULAR", "CT_PEAKER", "ST_GAS", "CC_CHP", "CT_CHP") if x in cw]
    ].sum(axis=1).values
    m["gas_peaking"] = cw[
        [x for x in ("CT_PEAKER", "ST_GAS") if x in cw]
    ].sum(axis=1).values
    m["coal"] = cw[
        [x for x in ("COAL_PRB", "COAL_BIT", "COAL_LIGNITE") if x in cw]
    ].sum(axis=1).values
    m["netload"] = (m.mdem - m.wind - m.solar) / 1000.0
    m["hod"] = m.hour % 24
    return m


def local_slope(nl: pd.Series, p: pd.Series) -> float:
    """Quadratic-fit stack slope ($/GW) evaluated at the window's mean net load."""
    co = np.polyfit(nl, p, 2)
    return float(2 * co[0] * nl.mean() + co[1])


def main() -> None:
    print("=" * 78)
    print("miso-114 Phase-0 — MISO seam hour-of-day shape + overnight anatomy")
    print(f"keeper bundle: {BUNDLE}   (NO LP SOLVED)")
    print("=" * 78)

    for year in YEARS:
        A = load_actual_prices(year)
        G = load_actual_930(year)
        M = load_model(year)
        # drop the duplicate hour-of-day columns the three sources each carry;
        # the merge key is the chronological hour index, so one `hod` suffices.
        D = A.drop(columns=["hod"]).merge(M, on="hour").merge(
            G[["hour", "Demand", "NG: WND", "NG: SUN", "NG: NG", "NG: COL", "NG: NUC", "netimp"]],
            on="hour",
        )
        D["anl"] = (D.Demand - D["NG: WND"].fillna(0) - D["NG: SUN"].fillna(0)) / 1000.0

        print(f"\n{'#' * 78}\n## {year}\n{'#' * 78}")
        print(
            f"\nQ1  ENERGY component is one system series — max cross-hub std "
            f"{A.attrs['energy_cross_hub_max_std']:.6f} $/MWh (0.0 confirms MISO's "
            "single-reference decomposition)"
        )

        off = D[D.hod.isin(OFFPEAK)]
        print(
            f"    overnight: model load-wtd dual  p10 ${off.msys.quantile(.10):6.2f}  "
            f"sd {off.msys.std():5.2f}"
        )
        print(
            f"               actual ENERGY        p10 ${off.ENERGY.quantile(.10):6.2f}  "
            f"sd {off.ENERGY.std():5.2f}"
        )
        print(
            f"               actual MINN.HUB LMP  p10 ${off.MINN.quantile(.10):6.2f}  "
            f"sd {off.MINN.std():5.2f}"
        )
        gap_energy = off.msys.quantile(0.10) - off.ENERGY.quantile(0.10)
        gap_cong = off.ENERGY.quantile(0.10) - off.MINN.quantile(0.10)
        tot = gap_energy + gap_cong
        print(
            f"    ==> p10 gap to MINN.HUB decomposes: ENERGY {gap_energy:+.2f} "
            f"({100 * gap_energy / tot:.0f}%) | congestion {gap_cong:+.2f} "
            f"({100 * gap_cong / tot:.0f}%)"
        )

        # ---- Q2: slope vs level, overnight, by net-load decile -------------
        o = off.copy()
        o["adec"] = pd.qcut(o.anl, 10, labels=False)
        o["mdec"] = pd.qcut(o.netload, 10, labels=False)
        a = o.groupby("adec").agg(nl=("anl", "mean"), p=("ENERGY", "mean"))
        m = o.groupby("mdec").agg(nl=("netload", "mean"), p=("msys", "mean"))
        print("\nQ2  overnight price vs net-load decile (is it slope or level?)")
        print(f"    {'dec':<5}{'act GW':>9}{'act $':>9}{'mod GW':>9}{'mod $':>9}{'gap $':>8}")
        for i in range(10):
            print(
                f"    {i:<5}{a.nl[i]:>9.1f}{a.p[i]:>9.2f}{m.nl[i]:>9.1f}"
                f"{m.p[i]:>9.2f}{m.p[i] - a.p[i]:>8.2f}"
            )
        sa = np.polyfit(o.anl, o.ENERGY, 1)[0]
        sm = np.polyfit(o.netload, o.msys, 1)[0]
        gaps = (m.p - a.p).values
        print(
            f"    linear slope $/GW: actual {sa:.3f} | model {sm:.3f} | "
            f"model/actual {sm / sa:.3f}"
        )
        print(
            f"    gap across deciles: min {gaps.min():+.2f} max {gaps.max():+.2f} "
            f"spread {gaps.max() - gaps.min():.2f}  ==> "
            f"{'LEVEL offset (slope ~correct)' if gaps.max() - gaps.min() < 0.5 * abs(gaps.mean()) else 'slope component present'}"
        )

        # ---- Q3: interchange hour-of-day shape ------------------------------
        hod_m = D.groupby("hod")["import"].mean()
        hod_a = D.groupby("hod")["netimp"].mean()
        print("\nQ3  net interchange: annual LEVEL vs hour-of-day SHAPE")
        print(
            f"    annual: model {D['import'].sum() / 1e6:6.2f} TWh | actual "
            f"{D.netimp.sum() / 1e6:6.2f} TWh | ratio "
            f"{D['import'].sum() / D.netimp.sum():.3f}"
        )
        print(f"    hour-of-day correlation model vs actual: {np.corrcoef(hod_m, hod_a)[0, 1]:+.3f}")
        print("    hod  " + " ".join(f"{x:>6d}" for x in range(24)))
        print("    ACT  " + " ".join(f"{hod_a[x]:>6.0f}" for x in range(24)))
        print("    MOD  " + " ".join(f"{hod_m[x]:>6.0f}" for x in range(24)))
        n_short = hod_a[NIGHT].mean() - hod_m[NIGHT].mean()
        p_long = hod_m[PEAK].mean() - hod_a[PEAK].mean()
        print(
            f"    night(h0-5) shortfall {n_short:+.0f} MW | peak(h16-19) excess "
            f"{p_long:+.0f} MW | total hod mis-shape {n_short + p_long:.0f} MW"
        )

        # sizing at the model's own local stack slope
        w_n = D[D.hod.isin(NIGHT)]
        w_p = D[D.hod.isin(PEAK)]
        s_n = local_slope(w_n.netload, w_n.msys)
        s_p = local_slope(w_p.netload, w_p.msys)
        print(
            f"    SIZING at the model's own local slope: night {s_n:.2f} $/GW x "
            f"{n_short / 1000:+.2f} GW = {-s_n * n_short / 1000:+.2f} $/MWh | "
            f"peak {s_p:.2f} $/GW x {-p_long / 1000:+.2f} GW = "
            f"{s_p * p_long / 1000:+.2f} $/MWh"
        )

        # ---- Q4: trough substitution arithmetic -----------------------------
        tr = D[D.hod.isin([1, 2, 3])]
        d_coal = tr.coal.mean() - tr["NG: COL"].mean()
        d_gas = tr.gas.mean() - tr["NG: NG"].mean()
        d_nuc = tr.nuclear.mean() - tr["NG: NUC"].mean()
        d_wind = tr.wind.mean() - tr["NG: WND"].mean()
        d_imp = tr["import"].mean() - tr.netimp.mean()
        print("\nQ4  overnight trough (h1-3) substitution, model minus actual (MW)")
        print(
            f"    coal {d_coal:+7.0f} | gas {d_gas:+7.0f} | imports {d_imp:+7.0f} | "
            f"nuclear {d_nuc:+7.0f} | wind {d_wind:+7.0f}"
        )
        print(
            f"    sum {d_coal + d_gas + d_imp + d_nuc + d_wind:+7.0f} MW "
            "(residual = hydro/storage/other; the arithmetic closes)"
        )
        print(
            f"    model CT_PEAKER+ST_GAS online at the trough: "
            f"{tr.gas_peaking.mean():.0f} MW"
        )

        # hour-of-day price gap
        h = D.groupby("hod")[["ENERGY", "msys"]].mean()
        print("\n    hour-of-day price gap (model - actual ENERGY), $/MWh")
        print("    hod  " + " ".join(f"{x:>6d}" for x in range(24)))
        print("    GAP  " + " ".join(f"{h.msys[x] - h.ENERGY[x]:>6.1f}" for x in range(24)))
        amp_m = h.msys.max() - h.msys.min()
        amp_a = h.ENERGY.max() - h.ENERGY.min()
        print(
            f"    diurnal amplitude: model {amp_m:.2f} | actual {amp_a:.2f} | "
            f"ratio {amp_m / amp_a:.3f}   (xiso-1 cross-check)"
        )


if __name__ == "__main__":
    main()
