"""SPP-80 (zero LP): decompose the 2022+ SPP upper-tercile price premium by MEASUREMENT.

SPP-79 (``docs/handoffs/FINDING-spp-79-c3a-is-a-cancellation-2026-09-25.md``) found
that the real SPP system hub's upper price tercile (RT p67-p99, February excluded)
cleared at a much higher implied heat rate from 2022 on (HR / Henry Hub 12.5-13.6
in 2019-21, 16.3 / 20.6 in 2023-24) and the model's did not. This probe splits
that upper tercile, per year, into the candidate drivers SPP-80's charter names:

  * **congestion + losses** — the hub's MCC + MLC (SPP publishes LMP = MEC + MCC +
    MLC per settlement location; ``actual_lmp_components_hourly_zonal_SPP.parquet``,
    landed by ``scripts/data/fetch_spp_hub_lmp_components.py``), plus the RTBM
    binding-constraint shadow-price mass as an independent witness;
  * **reserve / scarcity** — RTBM operating-reserve MCPs (``data/raw/spp-or-mcp``)
    in the same hours, and the MEC uplift carried by hours in which a reserve
    product priced above its offer cap (a price above the cap can only come from
    a Demand Curve, i.e. scarcity pricing — Protocols 119 §4.1.5 / §8.2.5);
  * **supply tightness** — SPP's own net load (load − wind − solar, GenMix) in the
    same hours, and the MEC heat rate at MATCHED net load across years;
  * **offer markup** — the SPP MMU's annual marginal-resource offer-price markup
    (``data/raw/spp-planning/som/spp_som_annual_metrics.csv``), which the hourly
    data cannot see and is therefore reported beside the table, not inside it.

Every price is on the model's fixed-CST non-leap 8760 clock. The hour selection
is SPP-79's exactly: the committed system-hub RT sidecar, hours present in the
keeper's P1 system hourly, unweighted p67 <= RT < p99, February excluded. Henry
Hub is the annual mean of ``gas-prices/henry_hub_monthly.csv`` as in SPP-79.

Solves nothing and writes nothing. Record:
``docs/handoffs/FINDING-spp-80-upper-tercile-premium-2026-09-25.md``.
"""

from __future__ import annotations

import io
import zipfile

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR

YEARS = range(2019, 2026)
BUNDLE = "results/calibration/rspp_span/hourly"
BASE_YEARS = (2019, 2020, 2021)  # SPP-79's pre-rise comparison years
# Offer caps above which a reserve MCP can only be a Demand Curve (scarcity) price:
# Integrated Marketplace Protocols r119 §8.2.5, as transcribed in
# data/raw/spp-planning/transcriptions/ (Contingency Reserve $100/MW,
# Regulation-Up $500/MW).
CONTINGENCY_OFFER_CAP = 100.0
REG_UP_OFFER_CAP = 500.0
GMT_TO_MODEL_H = 6  # build_spp_lmp_reference._GMT_TO_MODEL_CLOCK_HOURS (SPP-51c)
_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_MSTART = np.cumsum((0,) + _DAYS[:-1])


def model_hour(gmt_interval_end: pd.Series, year: int) -> np.ndarray:
    """Model-clock hour index (0..8759, -1 = off-calendar) of a GMT interval-end stamp."""
    t = pd.to_datetime(gmt_interval_end, format="mixed", utc=True).dt.tz_localize(None)
    t = t - pd.Timedelta(minutes=5) - pd.Timedelta(hours=GMT_TO_MODEL_H)
    m, d, h = t.dt.month.to_numpy(), t.dt.day.to_numpy(), t.dt.hour.to_numpy()
    idx = (_MSTART[m - 1] + d - 1) * 24 + h
    bad = (t.dt.year.to_numpy() != year) | ((m == 2) & (d == 29))
    return np.where(bad, -1, idx)


def _read_zip_csv(path, usecols=None) -> pd.DataFrame:
    """First CSV member of ``path`` with stripped, upper-cased, underscored headers."""
    z = zipfile.ZipFile(path)
    name = next(n for n in z.namelist() if n.lower().endswith(".csv"))
    df = pd.read_csv(io.BytesIO(z.read(name)), skipinitialspace=True, low_memory=False)
    df.columns = [c.strip().upper().replace(" ", "_") for c in df.columns]
    return df if usecols is None else df[[c for c in usecols if c in df.columns]]


def reserve_hourly(year: int) -> pd.DataFrame:
    """Hourly max-over-reserve-zones MCP per product and a scarcity flag."""
    df = _read_zip_csv(RAW_DATA_DIR / f"spp-or-mcp/RTBM_MCP_{year}.csv.zip")
    prods = [c for c in ("REGUPSERVICE", "SPIN", "SUPP", "RAMPUP", "UNCUP") if c in df]
    df["hour"] = model_hour(df["GMTINTERVALEND"], year)
    df = df[df.hour >= 0]
    iv = df.groupby(["hour", "GMTINTERVALEND"])[prods].max()  # BA-wide worst zone
    iv["scar"] = (iv.get("SPIN", 0) > CONTINGENCY_OFFER_CAP) | (
        iv.get("SUPP", 0) > CONTINGENCY_OFFER_CAP
    ) | (iv["REGUPSERVICE"] > REG_UP_OFFER_CAP)
    out = iv.groupby("hour").agg({**{p: "mean" for p in prods}, "scar": "max"})
    return out.reindex(range(8760))


def binding_hourly(year: int) -> pd.DataFrame:
    """Hourly RTBM binding-constraint shadow-price mass and binding count."""
    bc = RAW_DATA_DIR / "spp-binding-constraints"
    # 2019-2024 are one yearly roll-up (2022 without the ``.csv`` infix); 2025 is
    # landed as 12 monthly roll-ups (SPP-14).
    files = sorted(bc.glob(f"RTBM-BC-YEARLY-{year}*.zip")) or sorted(
        bc.glob(f"RTBM-BC-MONTHLY-{year}??.csv.zip")
    )
    parts = []
    for path in files:
        parts += _binding_parts(zipfile.ZipFile(path), year)
    iv = pd.concat(parts).groupby(level=[0, 1]).sum()
    return iv.groupby(level=0).mean().rename(columns={"sum": "bc_sp", "count": "bc_n"}).reindex(range(8760))


def _binding_parts(z: zipfile.ZipFile, year: int) -> list[pd.DataFrame]:
    """Per-(hour, interval) binding shadow-price sum and count from one BC zip."""
    member = next(n for n in z.namelist() if n.lower().endswith(".csv"))
    parts = []
    with z.open(member) as fh:
        for ch in pd.read_csv(
            fh, usecols=lambda c: c.strip() in ("GMTIntervalEnd", "State", "Shadow Price"),
            skipinitialspace=True, chunksize=2_000_000,
        ):
            ch.columns = [c.strip() for c in ch.columns]
            ch = ch[ch["State"].astype(str).str.upper().isin(["BINDING", "BREACHED"])]
            ch = ch.assign(hour=model_hour(ch["GMTIntervalEnd"], year))
            ch["sp"] = pd.to_numeric(ch["Shadow Price"], errors="coerce").abs()
            parts.append(ch[ch.hour >= 0].groupby(["hour", "GMTIntervalEnd"]).sp.agg(["sum", "count"]))
    return parts


def genmix_hourly(year: int) -> pd.DataFrame:
    """Hourly SPP load, wind, solar, gas and net load (GenMix, MW)."""
    g = pd.read_csv(RAW_DATA_DIR / f"spp-genmix/GenMix_{year}.csv", skipinitialspace=True)
    g.columns = [c.strip() for c in g.columns]
    col = lambda k: g[[c for c in g.columns if c.startswith(k)]].sum(axis=1)  # noqa: E731
    g = pd.DataFrame(
        {
            # Treated as an interval-END stamp like the MCP/BC files; the file's
            # first-row convention drifts (06:00Z in 2019, 06:05Z in 2024), which
            # moves at most one 5-min interval across an hour boundary.
            "hour": model_hour(g["GMT MKT Interval"], year),
            "load": g["Load"], "wind": col("Wind"), "solar": col("Solar"),
            "gas": col("Natural Gas") + g["Gas Self"],
        }
    )
    return g[g.hour >= 0].groupby("hour").mean().reindex(range(8760)).assign(
        net=lambda d: d.load - d.wind - d.solar
    )


def year_frame(y: int, lmp: pd.DataFrame, comp: pd.DataFrame) -> pd.DataFrame:
    """Hourly frame for ``y``: RT, model price, components, reserves, BC, genmix."""
    s = pd.read_parquet(f"{BUNDLE}/system_{y}.parquet")
    s = s[s["pass"] == "P1"]
    d = s.groupby("hour").demand.sum()
    m = (s.price * s.demand).groupby(s.hour).sum() / d
    f = pd.DataFrame({"d": d, "m": m})
    f["rt"] = lmp[lmp.year == y].set_index("hour").rt.reindex(f.index)
    c = comp[(comp.year == y) & (comp.market == "rt")].groupby("hour")[["lmp", "mec", "mcc", "mlc"]].mean()
    f = f.join(c).join(reserve_hourly(y)).join(binding_hourly(y)).join(genmix_hourly(y))
    f["mon"] = (pd.Timestamp(f"{y}-01-01") + pd.to_timedelta(f.index, unit="h")).month
    return f.dropna(subset=["rt", "m"])


def summarize(y: int, f: pd.DataFrame, hh: float) -> dict:
    """Upper-tercile (p67-p99, ex-Feb) means and the per-driver decomposition for ``y``."""
    f = f[f.mon != 2]
    q67, q99 = f.rt.quantile([0.67, 0.99])
    u = f[(f.rt >= q67) & (f.rt < q99)]
    sc = u.scar.fillna(False).astype(bool)
    mec_ns = u.mec[~sc].mean()
    return {
        "year": y, "hh": hh, "n_up": len(u),
        "up_rt": u.rt.mean(), "up_model": u.m.mean(), "hub_lmp": u.lmp.mean(),
        "mec": u.mec.mean(), "mcc": u.mcc.mean(), "mlc": u.mlc.mean(),
        "hr_rt": u.rt.mean() / hh, "hr_mec": u.mec.mean() / hh,
        "hr_cong": (u.mcc + u.mlc).mean() / hh,
        "scar_share": sc.mean(), "scar_uplift": u.mec.mean() - mec_ns,
        "hr_mec_noscar": mec_ns / hh,
        "spin": u.get("SPIN", pd.Series(dtype=float)).mean(),
        "regup": u.REGUPSERVICE.mean(),
        "rampup": u.RAMPUP.mean() if "RAMPUP" in u else 0.0,
        "uncup": u.UNCUP.mean() if "UNCUP" in u else 0.0,
        "bc_sp": u.bc_sp.mean(), "bc_n": u.bc_n.mean(),
        "net_gw": u.net.mean() / 1e3, "load_gw": u.load.mean() / 1e3,
        "wind_share": (u.wind / u.load).mean(), "gas_share": (u.gas / u.load).mean(),
        "net_pct_of_yr": (f.net < u.net.mean()).mean(),
        "q67": q67,
    }


def delivered_fuel_exfeb(year: int) -> tuple[float, float]:
    """(SPP-core delivered gas, SWPP delivered coal) $/MMBtu, quantity-weighted, ex-Feb.

    Gas: EIA-923 monthly delivered cost to KS/OK/NE plants (the SPP core states;
    ``_processed-legacy/eia923_monthly_fuel_costs.parquet``). Coal: EIA-923 Schedule 5
    receipts for plants whose ``Balancing Authority Code`` is ``SWPP``
    (``coal-receipts/``; FUEL_COST is cents/MMBtu). 2025 receipts are not landed.
    """
    g = pd.read_parquet(RAW_DATA_DIR / "_processed-legacy/eia923_monthly_fuel_costs.parquet")
    g = g[(g.fuel_group == "Natural Gas") & g.state.isin(["KS", "OK", "NE"])
          & (g.year == year) & (g.month != 2)].dropna(subset=["price_per_mmbtu"])
    gas = (g.price_per_mmbtu * g.quantity).sum() / g.quantity.sum()
    path = RAW_DATA_DIR / f"coal-receipts/coal_receipts_{year}.csv"
    if not path.exists():
        return gas, float("nan")
    c = pd.read_csv(path, low_memory=False)
    c = c[(c["Balancing Authority Code"] == "SWPP") & (c.FUEL_GROUP == "Coal") & (c.MONTH != 2)]
    mmbtu = c.QUANTITY * c["Average Heat Content"]
    cost = pd.to_numeric(c.FUEL_COST, errors="coerce") / 100
    ok = cost.notna()
    return gas, float((cost[ok] * mmbtu[ok]).sum() / mmbtu[ok].sum())


def matched_netload(frames: dict, hh: dict) -> pd.DataFrame:
    """MEC heat rate (MEC / HH) by net-load band, all ex-Feb hours, per year."""
    edges = [0, 15e3, 20e3, 25e3, 30e3, 35e3, 60e3]
    rows = []
    for y, f in frames.items():
        f = f[(f.mon != 2) & f.mec.notna()]
        b = pd.cut(f.net, edges)
        rows.append((f.mec / hh[y]).groupby(b, observed=False).median().rename(y))
    return pd.concat(rows, axis=1).round(2)


def main() -> None:
    """Print the per-year upper-tercile decomposition and the matched-net-load table."""
    lmp = pd.read_parquet(RAW_DATA_DIR / "_validation-source/actual_lmp_hourly_SPP.parquet")
    comp = pd.read_parquet(RAW_DATA_DIR / "_validation-source/actual_lmp_components_hourly_zonal_SPP.parquet")
    hhm = pd.read_csv(RAW_DATA_DIR / "gas-prices/henry_hub_monthly.csv")
    hh = {y: hhm[hhm.year == y].price_usd_mmbtu.mean() for y in YEARS}
    frames = {y: year_frame(y, lmp, comp) for y in YEARS}
    t = pd.DataFrame([summarize(y, frames[y], hh[y]) for y in YEARS]).set_index("year")
    base = t.loc[list(BASE_YEARS)]
    # Premium in HR units against the 2019-21 mean HR, split additively:
    #   rt HR = MEC HR + congestion(MCC+MLC) HR   (hub = MEC + MCC + MLC, RT sidecar = hub mean)
    #   MEC HR = MEC-ex-scarcity HR + scarcity uplift HR
    t["prem_hr"] = t.hr_rt - base.hr_rt.mean()
    t["d_cong"] = t.hr_cong - base.hr_cong.mean()
    t["d_scar"] = t.scar_uplift / t.hh - (base.scar_uplift / base.hh).mean()
    t["d_mec_noscar"] = t.hr_mec_noscar - base.hr_mec_noscar.mean()
    t["d_sidecar_gap"] = t.prem_hr - t.d_cong - t.d_scar - t.d_mec_noscar
    # The same ex-scarcity MEC against DELIVERED fuel, so regional basis is not
    # counted as premium (the gas-basis leg SPP-79 checked on annual averages).
    fuel = {y: delivered_fuel_exfeb(y) for y in YEARS}
    t["gas_deliv"] = [fuel[y][0] for y in YEARS]
    t["coal_deliv"] = [fuel[y][1] for y in YEARS]
    t["hr_mec_noscar_deliv"] = t.hr_mec_noscar * t.hh / t.gas_deliv
    # Reported beside, not inside, the HH-basis split: a delivered-gas HR is on a
    # different denominator, so the two are never differenced into a "basis" term.
    t["d_mec_noscar_deliv"] = t.hr_mec_noscar_deliv - t.hr_mec_noscar_deliv.loc[list(BASE_YEARS)].mean()
    pd.set_option("display.width", 250)
    print(t.round(3).T.to_string())
    print("\nMEC / Henry Hub, median by net-load band (MW), ex-Feb, all hours:")
    print(matched_netload(frames, hh).to_string())


if __name__ == "__main__":
    main()
