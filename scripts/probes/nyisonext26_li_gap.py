"""NYISO-NEXT-26 phase 0 (ZERO LP): where does the Long Island under-pricing sit?

Splits the keeper's Zone K price error into two pieces with no LP:

    model_K - DA_K = (model_J - DA_J) + [(model_K - model_J) - (DA_K - DA_J)]
                     \\__ NYC level __/   \\_______ K-over-J spread error ______/

and splits the measured DA K-over-J spread into its published loss and
congestion components (NYISO convention: LBMP = energy + loss - congestion, so
the congestion contribution to a zone's price is ``-cong``; verified on the
archive: the implied energy component is identical across zones each hour).

If the miss is in the spread and the measured spread is congestion, the gap is
transfer into K (or K's internal stack being cheaper than the binding import);
if the miss is in the NYC level, K inherits it and the LI stack is not the
object. Every number is a diagnostic; nothing here feeds a solve (rule 13).

Usage: uv run python scripts/probes/nyisonext26_li_gap.py --out <json>
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
ZONAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_zonal_NYISO.parquet"
DAM_DIR = REPO / "data/raw/lmp-data/NYISO"  # fetch_nyiso_zonal_lmp.py --kind da
BANDS = {"00-06": range(0, 7), "07-10": range(7, 11), "11-16": range(11, 17),
         "17-21": range(17, 22), "22-23": range(22, 24)}  # fmt: skip
SEASONS = {"winter": (1, 2, 12), "spring": (3, 4, 5), "summer": (6, 7, 8), "fall": (9, 10, 11)}  # fmt: skip
YEARS = (2021, 2022, 2023, 2024, 2025)


def keeper_bundle(year: int) -> Path:
    """Keeper bundle carrying ``year`` (override with --span/--y2021)."""
    return (
        REPO
        / "results/calibration"
        / ("nyisonext21_2021" if year == 2021 else "nyisonext21_span")
    )


def model_prices(bundle: Path, year: int) -> dict[str, np.ndarray]:
    """Hourly P1 zone prices from a bundle's system sidecar."""
    s = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    return {
        z: g.sort_values("hour").price.to_numpy()[:8760] for z, g in s.groupby("zone")
    }


def da_components(year: int) -> pd.DataFrame:
    """Hourly DA LBMP / loss / congestion for LONGIL and N.Y.C. on the 8760 local grid."""
    fr = []
    for f in sorted(DAM_DIR.glob(f"{year}??01damlbmp_zone_csv.zip")):
        z = zipfile.ZipFile(f)
        fr += [pd.read_csv(z.open(n)) for n in z.namelist()]
    d = pd.concat(fr)
    d = d[d.Name.isin(["LONGIL", "N.Y.C.", "CENTRL"])]
    d["ts"] = pd.to_datetime(d["Time Stamp"])
    d = d.rename(columns={"LBMP ($/MWHr)": "lbmp", "Marginal Cost Losses ($/MWHr)": "loss",
                          "Marginal Cost Congestion ($/MWHr)": "cong"})  # fmt: skip
    p = d.pivot_table(index="ts", columns="Name", values=["lbmp", "loss", "cong"])
    grid = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
    return p.reindex(grid).ffill()


def summarize(year: int, bundle: Path) -> dict:
    """All splits for one year."""
    a = pd.read_parquet(ZONAL)
    a = a[a.year == year]
    act = {z: g.sort_values("hour") for z, g in a.groupby("zone")}
    da_k, da_j = (
        act["Long_Island"].da.to_numpy()[:8760],
        act["NYC"].da.to_numpy()[:8760],
    )
    rt_k, rt_j = (
        act["Long_Island"].rt.to_numpy()[:8760],
        act["NYC"].rt.to_numpy()[:8760],
    )
    m = model_prices(bundle, year)
    mk, mj = m["Long_Island"], m["NYC"]
    c = da_components(year)
    # energy-component identity check (convention LBMP = E + loss - cong)
    e_k = c["lbmp"]["LONGIL"] - c["loss"]["LONGIL"] + c["cong"]["LONGIL"]
    e_j = c["lbmp"]["N.Y.C."] - c["loss"]["N.Y.C."] + c["cong"]["N.Y.C."]
    ident = float(np.nanmax(np.abs(e_k - e_j)))
    loss_kj = (c["loss"]["LONGIL"] - c["loss"]["N.Y.C."]).to_numpy()
    cong_kj = (-(c["cong"]["LONGIL"] - c["cong"]["N.Y.C."])).to_numpy()
    cong_k = (-c["cong"]["LONGIL"]).to_numpy()
    cong_j = (-c["cong"]["N.Y.C."]).to_numpy()
    idx = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
    hr, mo = idx.hour.to_numpy(), idx.month.to_numpy()

    def row(mask: np.ndarray) -> dict:
        def mu(x):
            return round(float(np.nanmean(x[mask])), 2)

        return {
            "n": int(mask.sum()),
            "da_K": mu(da_k), "model_K": mu(mk), "err_K_vs_DA": mu(mk - da_k),
            "err_K_pct": round(100 * float(np.nanmean(mk[mask] - da_k[mask]) / np.nanmean(da_k[mask])), 1),
            "err_J_vs_DA": mu(mj - da_j),
            "spread_da": mu(da_k - da_j), "spread_model": mu(mk - mj),
            "spread_err": mu((mk - mj) - (da_k - da_j)),
            "da_spread_loss": mu(loss_kj), "da_spread_cong": mu(cong_kj),
            "da_cong_K": mu(cong_k), "da_cong_J": mu(cong_j),
            "rt_K": mu(rt_k), "spread_rt": mu(rt_k - rt_j),
            "share_h_da_cong_kj_gt5": round(float(np.mean(cong_kj[mask] > 5)), 3),
            "share_h_model_spread_gt5": round(float(np.mean((mk - mj)[mask] > 5)), 3),
        }  # fmt: skip

    allm = np.ones(8760, bool)
    out = {"year": year, "bundle": str(bundle.relative_to(REPO)), "energy_identity_max_abs": round(ident, 3),
           "annual": row(allm),
           "season": {s: row(np.isin(mo, ms)) for s, ms in SEASONS.items()},
           "winter_band": {b: row(np.isin(mo, SEASONS["winter"]) & np.isin(hr, list(r))) for b, r in BANDS.items()},
           "band": {b: row(np.isin(hr, list(r))) for b, r in BANDS.items()},
           "month": {int(x): row(mo == x) for x in range(1, 13)}}  # fmt: skip
    # Concentration: how much of the annual K miss sits in hours where DA K-over-J
    # congestion > 5 $/MWh (a measured binding-import proxy) vs the rest.
    bind = cong_kj > 5
    tot = float(np.nansum(mk - da_k))
    out["miss_split_by_da_binding"] = {
        "share_hours_binding": round(float(bind.mean()), 3),
        "share_of_K_miss_in_binding_h": round(
            float(np.nansum((mk - da_k)[bind]) / tot), 3
        ),
        "binding": row(bind),
        "nonbinding": row(~bind),
    }
    return out


def main() -> None:
    """CLI."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", required=True)
    ap.add_argument(
        "--span", default=None, help="span bundle (2022-2025); default keeper"
    )
    ap.add_argument("--y2021", default=None, help="2021 bundle; default keeper")
    ap.add_argument(
        "--legs",
        default=None,
        help="dir holding <year>/{unit_hourly,network}_<year>.parquet from the keeper legs",
    )
    a = ap.parse_args()
    res = []
    for y in YEARS:
        b = keeper_bundle(y)
        if y == 2021 and a.y2021:
            b = REPO / a.y2021
        elif y != 2021 and a.span:
            b = REPO / a.span
        res.append(summarize(y, b))
        r = res[-1]["annual"]
        print(y, json.dumps({k: r[k] for k in ("err_K_pct", "err_K_vs_DA", "err_J_vs_DA", "spread_da",
                                                  "spread_model", "da_spread_loss", "da_spread_cong")}),
              file=sys.stderr)  # fmt: skip
    bal = []
    if a.legs:
        for y in YEARS:
            b = keeper_bundle(y) if not (a.span and y != 2021) else REPO / a.span
            bal.append(balance(y, Path(a.legs) / str(y), b))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps({"price_split": res, "balance": bal}, indent=1))


# --------------------------------------------------------------------------
# Leg 2: the Zone K energy balance, model vs measured (zero LP).
# --------------------------------------------------------------------------
IFLOWS = REPO / "data/raw/NYISO/interface-flows"
LOADS = REPO / "data/raw/zone-specific-demand/NYISO"
CAMPD = REPO / "data/raw/campd-unit-level"
LI_SEAMS = ("SCH - PJM_NEPTUNE", "SCH - NPX_CSC", "SCH - NPX_1385")


def _grid(year: int) -> pd.DatetimeIndex:
    return pd.date_range(f"{year}-01-01", periods=8760, freq="h")


def measured_balance(year: int, li_plants: list[int]) -> dict[str, np.ndarray]:
    """Measured Zone K load, CAMPD gross gen of the model's LI plants, and LI seam schedules."""
    g = _grid(year)
    ld = pd.read_csv(
        LOADS / f"NYISO_load_actuals_{year}.csv", parse_dates=["Time Stamp"]
    )
    ld = ld[ld.Name == "LONGIL"].groupby("Time Stamp").Load.mean()
    load = ld.reindex(g).interpolate().to_numpy()
    f = pd.read_csv(IFLOWS / f"NYISO_interface_flows_hourly_{year}.csv.gz",
                    parse_dates=["interval_start_local"])  # fmt: skip
    f = f[f.interface.isin(LI_SEAMS)]
    seams = f.groupby("interval_start_local").flow_mw.sum()
    seams = seams[~seams.index.duplicated()].reindex(g).ffill().to_numpy()
    c = pd.read_parquet(
        CAMPD / f"NY_{year}.parquet",
        columns=["facilityId", "date", "hour", "grossLoad"],
    )
    c["facilityId"] = pd.to_numeric(c.facilityId, errors="coerce")
    c = c[c.facilityId.isin(li_plants)]
    c["ts"] = pd.to_datetime(c.date) + pd.to_timedelta(c.hour, unit="h")
    gen = c.groupby("ts").grossLoad.sum().reindex(g).fillna(0.0).to_numpy()
    return {"load": load, "seams": seams, "campd_gross": gen}


def model_balance(year: int, leg_dir: Path) -> dict[str, np.ndarray]:
    """Model Zone K demand, fossil gen, NYC->LI net flow and external->LI flow from a full leg."""
    u = pd.read_parquet(leg_dir / f"unit_hourly_{year}.parquet",
                        columns=["plant_code", "fuel", "zone", "hour", "mw"])  # fmt: skip
    u = u[(u.zone == "Long_Island")]
    fos = u[u.fuel != "demand_response"]
    gen = fos.groupby("hour").mw.sum().reindex(range(8760), fill_value=0.0).to_numpy()
    n = pd.read_parquet(leg_dir / f"network_{year}.parquet")

    def link(name):
        return n[n.name == name].sort_values("hour").mw.to_numpy()[:8760]

    def dual(name):
        return n[n.name == name].sort_values("hour").dual.to_numpy()[:8760]

    return {
        "fossil_gen": gen,
        "ac_import": link("NYC>Long_Island") - link("Long_Island>NYC"),
        "ext_import": link("NYISO_external>Long_Island"),
        "ac_dual": dual("NYC>Long_Island"),
        "plants": sorted(int(p) for p in fos.plant_code.unique() if int(p) > 0),
    }


def balance(year: int, leg_dir: Path, bundle: Path) -> dict:
    """Model vs measured Zone K balance by season x band, plus the DA-binding split."""
    m = model_balance(year, leg_dir)
    x = measured_balance(year, m["plants"])
    sysd = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    sysd = sysd[(sysd.zone == "Long_Island") & (sysd["pass"] == "P1")].sort_values(
        "hour"
    )
    m_dem = sysd.demand.to_numpy()[:8760]
    # measured mainland AC import implied by the balance (gross CAMPD: an upper
    # bound on net output, so this implied import is a LOWER bound by ~3-5 % of gen)
    x_ac = x["load"] - x["campd_gross"] - x["seams"]
    m_other = (
        m_dem - m["fossil_gen"] - m["ac_import"] - m["ext_import"]
    )  # non-fossil K supply
    c = da_components(year)
    ckj = (-(c["cong"]["LONGIL"] - c["cong"]["N.Y.C."])).to_numpy()
    idx = _grid(year)
    hr, mo = idx.hour.to_numpy(), idx.month.to_numpy()

    def row(mask):
        def mu(v):
            return round(float(np.nanmean(v[mask])), 0)

        return {"n": int(mask.sum()), "load_meas": mu(x["load"]), "demand_model": mu(m_dem),
                "fossil_campd_gross": mu(x["campd_gross"]), "fossil_model": mu(m["fossil_gen"]),
                "seams_meas": mu(x["seams"]), "ext_model": mu(m["ext_import"]),
                "ac_import_meas_implied": mu(x_ac), "ac_import_model": mu(m["ac_import"]),
                "other_supply_model": mu(m_other),
                "model_ac_bind_share": round(float(np.mean(np.abs(m["ac_dual"][mask]) > 1e-6)), 3),
                "da_cong_gt5_share": round(float(np.mean(ckj[mask] > 5)), 3)}  # fmt: skip

    out = {"year": year, "annual": row(np.ones(8760, bool)),
           "season": {s: row(np.isin(mo, ms)) for s, ms in SEASONS.items()},
           "band": {b: row(np.isin(hr, list(r))) for b, r in BANDS.items()},
           "da_binding": row(ckj > 5), "da_nonbinding": row(ckj <= 5)}  # fmt: skip
    return out


if __name__ == "__main__":
    main()
