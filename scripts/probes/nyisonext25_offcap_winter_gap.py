"""NYISO-NEXT-25 phase 0 (ZERO LP): decompose the NYC off-cap winter price gap (model vs DA).

Population: J/F/D days on which the dual-fuel parity cap does NOT bind for any capable NYC
tranche (the NEXT-24 test on the flow-dated, uncapped gas series). For each such day it
reads, with no LP:

* model price (keeper sidecar; NEXT-23 arm sidecar when ``--arm-ref`` is given) vs NYISO DA,
  NYC and upstream zones, by hour band;
* the model's delivered gas for NYC gas tranches (keeper fleet-only rebuild, final
  post-cap ``fuel_prices``), MW-weighted, by class, vs measured Transco Z6 NY daily spot;
* the implied market heat rate (price / gas) on each side and a split of the gap into a
  fuel-level part and a heat-rate (stack) part;
* the NYC - upstream spread on each side (a fuel-level error moves every zone; a
  downstate-stack or congestion error moves the spread);
* which NYC class's base cost (``mc_base``, P0 cost, no P1 band) sits nearest the model
  price and the DA price each hour -- a diagnostic of the marginal class, never a target.

Every number is a diagnostic; nothing here is fed back into a solve (rule 13).

Usage: uv run python scripts/probes/nyisonext25_offcap_winter_gap.py --out <json>
"""

from __future__ import annotations

import argparse
import importlib
import io
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

ZONAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_zonal_NYISO.parquet"
Z6 = REPO / "data/raw/gas-prices/transco_z6_ny_daily.csv"
Z6_IROQ = REPO / "data/raw/gas-prices/transco_z6_iroquois_monthly.csv"
DAM_DIR = (
    REPO / "data/raw/lmp-data/NYISO"
)  # *damlbmp_zone_csv.zip, fetch_nyiso_zonal_lmp.py --kind da
BANDS = {"00-06": range(0, 7), "07-10": range(7, 11), "11-16": range(11, 17),
         "17-21": range(17, 22), "22-23": range(22, 24)}  # fmt: skip
WINTER = (1, 2, 12)


def _bundle(year: int) -> Path:
    """Keeper bundle carrying ``year``."""
    name = "nyisonext21_2021" if year == 2021 else "nyisonext21_span"
    return REPO / "results/calibration" / name


def fleet_state(year: int, overrides: dict) -> dict:
    """Fleet-only rebuild of the keeper recipe with ``overrides`` merged into prb_overrides."""
    os.environ["NYISO_KEEPER_BUNDLE"] = str(_bundle(year))
    import scripts.probes.nyiso242_tail_reachability as t

    t = importlib.reload(t)
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((t.BUNDLE / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(t.BUNDLE, year))
    prb = dict(kw.get("prb_overrides") or {})
    prb.update(overrides)
    kw["prb_overrides"] = prb
    return run_year(
        year, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw
    )


def cap_binding_days(year: int) -> set[int]:
    """Days (0-based) the NYC parity cap binds, NEXT-24 test (flow-dated, uncapped)."""
    from market_sim.data.fleet import dual_fuel_plant_groups
    from market_sim.data.fuel.dual_fuel import _GAS_FUEL_IDX, dual_fuel_oil_price_series

    st = fleet_state(year, {"nyiso_gas_flow_date": True, "dual_fuel_switching": False})
    fa, cfg = st["fleet_arrays"], st["config"]
    nyc = list(st["iso_config"].zone_names).index("NYC")
    gas = np.asarray(st["fuel_prices"], float)[:, :8760]
    oil = dual_fuel_oil_price_series(cfg, year)[:8760]
    capable = dual_fuel_plant_groups()
    sel = [
        g
        for g in np.nonzero(np.isin(fa.fuel_type_idx, _GAS_FUEL_IDX))[0]
        if (int(fa.plant_code[g]), str(fa.plant_group[g])) in capable
        and int(fa.zone_idx[g]) == nyc
    ]
    bind = (gas[sel] > oil).reshape(len(sel), 365, 24).any((0, 2))
    return set(np.nonzero(bind)[0].tolist())


def _hourly_price(path_or_bytes, year: int, zone: str) -> np.ndarray:
    """Hourly P1 price for one zone from a system sidecar."""
    s = pd.read_parquet(path_or_bytes)
    s = s[(s.zone == zone) & (s["pass"] == "P1")].sort_values("hour")
    return s.price.to_numpy()[:8760]


def _arm_sidecar(year: int, ref: str):
    """NEXT-23 arm system sidecar bytes from a git ref (None if absent)."""
    b = "nyisonext23_2021" if year == 2021 else "nyisonext23_span"
    p = f"results/calibration/{b}/hourly/system_{year}.parquet"
    r = subprocess.run(
        ["git", "show", f"{ref}:{p}"], cwd=REPO, capture_output=True, check=False
    )
    return io.BytesIO(r.stdout) if r.returncode == 0 else None


def _z6_daily(year: int) -> np.ndarray:
    """Transco Z6 NY daily spot on a 365-day grid (non-trading days carried forward)."""
    z = pd.read_csv(Z6, parse_dates=["date"]).set_index("date")
    idx = pd.date_range(f"{year - 1}-12-20", f"{year}-12-31")
    s = z.transco_z6_ny_usd_mmbtu.reindex(idx).ffill()
    s = s[s.index.year == year]
    s = s[~((s.index.month == 2) & (s.index.day == 29))]
    return s.to_numpy()[:365]


def da_components(year: int) -> pd.DataFrame | None:
    """Hourly DA LBMP / loss / congestion for zones E (MHK VL), F (CAPITL), J (N.Y.C.)."""
    import zipfile

    fr = []
    for f in sorted(DAM_DIR.glob(f"{year}??01damlbmp_zone_csv.zip")):
        z = zipfile.ZipFile(f)
        fr += [pd.read_csv(z.open(n)) for n in z.namelist()]
    if not fr:
        return None
    d = pd.concat(fr)
    d = d[d.Name.isin(["MHK VL", "CAPITL", "N.Y.C."])]
    d["ts"] = pd.to_datetime(d["Time Stamp"])
    d = d.rename(
        columns={
            "LBMP ($/MWHr)": "lbmp",
            "Marginal Cost Losses ($/MWHr)": "loss",
            "Marginal Cost Congestion ($/MWHr)": "cong",
        }
    )
    p = d.pivot_table(index="ts", columns="Name", values=["lbmp", "loss", "cong"])
    # DST: spring-forward has 23 stamps, fall-back's repeat is averaged by
    # pivot_table; re-grid onto the model's 8760-hour local calendar.
    grid = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
    p = p.reindex(grid).ffill()
    return p


def gap(year: int, arm_ref: str | None) -> dict:
    """Off-cap winter gap decomposition for one year."""
    from market_sim.data.fuel.dual_fuel import _GAS_FUEL_IDX

    bind = cap_binding_days(year)
    st = fleet_state(year, {})
    fa = st["fleet_arrays"]
    zones = list(st["iso_config"].zone_names)
    nyc = zones.index("NYC")
    fuel = np.asarray(st["fuel_prices"], float)[:, :8760]
    mc = np.asarray(st["mc_base"], float)[:, :8760]
    is_gas = np.isin(fa.fuel_type_idx, _GAS_FUEL_IDX)
    sel = np.nonzero(is_gas & (np.asarray(fa.zone_idx) == nyc))[0]
    pg = np.asarray(fa.plant_group).astype(str)[sel]
    mw = np.asarray(fa.pmax, float)[sel]
    hr = np.asarray(fa.heat_rate, float)[sel]

    days = pd.date_range(f"{year}-01-01", periods=365, freq="D")
    win = np.isin(days.month, WINTER)
    off = win & ~np.isin(np.arange(365), sorted(bind))

    a = pd.read_parquet(ZONAL)
    a = a[a.year == year]
    da = {z: a[a.zone == z].sort_values("hour").da.to_numpy()[:8760] for z in a.zone.unique()}  # fmt: skip
    kb = _bundle(year) / "hourly" / f"system_{year}.parquet"
    mk = {z: _hourly_price(kb, year, z) for z in ("NYC", "Capital_Hudson", "Upstate_West", "Long_Island", "Lower_Hudson")}  # fmt: skip
    arm = None
    if arm_ref:
        ab = _arm_sidecar(year, arm_ref)
        arm = _hourly_price(ab, year, "NYC") if ab is not None else None

    z6 = _z6_daily(year)
    gas_d = fuel[sel].reshape(len(sel), 365, 24).mean(2)
    w = mw[:, None]
    gas_nyc = (gas_d * w).sum(0) / w.sum()
    gas_cls = {
        c: (gas_d[pg == c] * mw[pg == c, None]).sum(0) / mw[pg == c].sum()
        for c in np.unique(pg)
        if mw[pg == c].sum() > 0
    }

    def dmean(x):
        return x.reshape(365, 24).mean(1)

    m_nyc, d_nyc = dmean(mk["NYC"]), dmean(da["NYC"])
    out = {
        "year": year,
        "winter_days": int(win.sum()),
        "cap_binding_winter_days": int((win & ~off).sum()),
        "offcap_days": int(off.sum()),
    }
    o = off
    out["nyc_offcap"] = {
        "da_mean": round(float(d_nyc[o].mean()), 2),
        "keeper_mean": round(float(m_nyc[o].mean()), 2),
        "keeper_gap_sum_usd_day": round(float((m_nyc - d_nyc)[o].sum()), 0),
        "keeper_gap_mean": round(float((m_nyc - d_nyc)[o].mean()), 2),
    }
    if arm is not None:
        a_nyc = dmean(arm)
        out["nyc_offcap"]["arm_mean"] = round(float(a_nyc[o].mean()), 2)
        out["nyc_offcap"]["arm_gap_sum_usd_day"] = round(float((a_nyc - d_nyc)[o].sum()), 0)  # fmt: skip
        out["nyc_offcap"]["arm_gap_mean"] = round(float((a_nyc - d_nyc)[o].mean()), 2)

    # hour bands
    hmask = np.repeat(o, 24)
    hod = np.tile(np.arange(24), 365)
    out["nyc_by_hour_band"] = {
        b: {
            "da": round(float(da["NYC"][hmask & np.isin(hod, list(r))].mean()), 2),
            "keeper": round(float(mk["NYC"][hmask & np.isin(hod, list(r))].mean()), 2),
            "gap": round(
                float((mk["NYC"] - da["NYC"])[hmask & np.isin(hod, list(r))].mean()), 2
            ),
        }
        for b, r in BANDS.items()
    }

    # zones: is the gap NYC-specific (spread) or system-wide (level)?
    out["zone_gap_offcap"] = {
        z: {
            "da": round(float(dmean(da[z])[o].mean()), 2),
            "keeper": round(float(dmean(mk[z])[o].mean()), 2),
            "gap": round(float((dmean(mk[z]) - dmean(da[z]))[o].mean()), 2),
        }
        for z in mk
        if z in da
    }
    for up in ("Capital_Hudson", "Upstate_West"):
        out[f"spread_nyc_minus_{up}"] = {
            "da": round(float((d_nyc - dmean(da[up]))[o].mean()), 2),
            "keeper": round(float((m_nyc - dmean(mk[up]))[o].mean()), 2),
        }

    # fuel: model delivered gas vs measured Z6 daily
    out["gas_offcap"] = {
        "z6_ny_daily_mean": round(float(z6[o].mean()), 3),
        "model_nyc_gas_mw_wtd": round(float(gas_nyc[o].mean()), 3),
        "model_minus_z6_mean": round(float((gas_nyc - z6)[o].mean()), 3),
        "corr_model_gas_vs_z6": round(float(np.corrcoef(gas_nyc[o], z6[o])[0, 1]), 3),
        "by_class": {c: round(float(v[o].mean()), 3) for c, v in gas_cls.items()},
        "corr_da_vs_z6": round(float(np.corrcoef(d_nyc[o], z6[o])[0, 1]), 3),
        "corr_keeper_vs_model_gas": round(
            float(np.corrcoef(m_nyc[o], gas_nyc[o])[0, 1]), 3
        ),
    }
    # implied market heat rates and split of the gap: P = IHR * g
    ihr_da_z6 = d_nyc / z6
    ihr_m = m_nyc / gas_nyc
    fuel_part = ihr_da_z6 * (gas_nyc - z6)  # model's gas vs Z6, at DA's IHR
    hr_part = (ihr_m - ihr_da_z6) * gas_nyc  # stack (IHR) diff, at model gas
    out["implied_heat_rate_offcap"] = {
        "da_over_z6_median": round(float(np.median(ihr_da_z6[o])), 2),
        "keeper_over_model_gas_median": round(float(np.median(ihr_m[o])), 2),
        "keeper_over_z6_median": round(float(np.median((m_nyc / z6)[o])), 2),
        "gap_split_mean": {
            "fuel_level_part": round(float(fuel_part[o].mean()), 2),
            "heat_rate_part": round(float(hr_part[o].mean()), 2),
            "total": round(float((m_nyc - d_nyc)[o].mean()), 2),
        },
        "nyc_gas_mw_wtd_hr": round(float(np.average(hr, weights=mw)), 3),
    }
    # nearest-cost class each hour (model price vs DA price) on off-cap hours
    mcs = mc[sel]

    def nearest(p):
        i = np.abs(mcs - p[None, :]).argmin(0)
        dev = np.abs(mcs[i, np.arange(8760)] - p)
        lab = np.where(dev <= 3.0, pg[i], "none_within_3")
        lab = np.where(p < mcs.min(0) - 3.0, "below_nyc_gas", lab)
        return lab

    for nm, p in (("keeper", mk["NYC"]), ("da", da["NYC"])):
        lab = nearest(p)[hmask]
        v, c = np.unique(lab, return_counts=True)
        out[f"nearest_class_{nm}"] = {
            str(k): round(float(n / hmask.sum()), 3) for k, n in zip(v, c)
        }
    # what fuel would DA imply at the model's own NYC IHR (diagnostic only)
    impl = d_nyc / ihr_m
    out["da_implied_gas_at_model_ihr_offcap"] = {
        "mean": round(float(impl[o].mean()), 3),
        "minus_model_gas": round(float((impl - gas_nyc)[o].mean()), 3),
        "minus_z6": round(float((impl - z6)[o].mean()), 3),
    }
    # CE attribution: NYC gap = upstream (Upstate_West) gap + missing NYC-UW spread
    uw_gap = (dmean(mk["Upstate_West"]) - dmean(da["Upstate_West"]))[o].mean()
    ch_uw = (dmean(mk["Capital_Hudson"]) - dmean(mk["Upstate_West"])) - (
        dmean(da["Capital_Hudson"]) - dmean(da["Upstate_West"])
    )
    nyc_ch = (m_nyc - dmean(mk["Capital_Hudson"])) - (
        d_nyc - dmean(da["Capital_Hudson"])
    )
    out["nyc_gap_attribution_offcap"] = {
        "upstate_west_level": round(float(uw_gap), 2),
        "capital_minus_upstate_spread_deficit": round(float(ch_uw[o].mean()), 2),
        "nyc_minus_capital_spread_deficit": round(float(nyc_ch[o].mean()), 2),
        "total": round(float((m_nyc - d_nyc)[o].mean()), 2),
    }
    comp = da_components(year)
    if comp is not None and len(comp) >= 8760:
        c = comp.iloc[:8760]
        fe = (c.lbmp.CAPITL - c.lbmp["MHK VL"]).to_numpy()
        fe_c = (c.cong.CAPITL - c.cong["MHK VL"]).to_numpy()
        fe_l = (c.loss.CAPITL - c.loss["MHK VL"]).to_numpy()
        out["da_F_minus_E_offcap"] = {
            "lbmp": round(float(dmean(fe)[o].mean()), 2),
            "loss": round(float(dmean(fe_l)[o].mean()), 2),
            "congestion_sign_as_published": round(float(dmean(fe_c)[o].mean()), 2),
            "share_hours_congestion_gt_5": round(
                float((np.abs(fe_c)[hmask] > 5).mean()), 3
            ),  # fmt: skip
        }
    # class gas by month, NYC and Capital_Hudson, vs Z6 daily / Iroquois Z2 monthly
    iq = pd.read_csv(Z6_IROQ)
    iq = iq[iq.date.str.startswith(str(year))].set_index("date")
    ch = zones.index("Capital_Hudson")
    out["class_gas_by_month_offcap"] = {}
    for zname, zi in (("NYC", nyc), ("Capital_Hudson", ch)):
        zsel = np.nonzero(is_gas & (np.asarray(fa.zone_idx) == zi))[0]
        zpg = np.asarray(fa.plant_group).astype(str)[zsel]
        zmw = np.asarray(fa.pmax, float)[zsel]
        zg = fuel[zsel].reshape(len(zsel), 365, 24).mean(2)
        rec = {}
        for m in WINTER:
            km = o & (days.month == m)
            if not km.any():
                continue
            r = {"z6_daily": round(float(z6[km].mean()), 2)}
            key = f"{year}-{m:02d}"
            if key in iq.index:
                r["iroquois_z2_monthly"] = round(float(iq.loc[key, "iroquois_z2_usd_mmbtu"]), 2)  # fmt: skip
            for cl in ("CC_REGULAR", "CC_CHP", "ST_GAS", "CT_PEAKER"):
                k = zpg == cl
                if zmw[k].sum() > 0:
                    r[cl] = round(float((zg[k][:, km] * zmw[k, None]).sum(0).mean() / zmw[k].sum()), 2)  # fmt: skip
            rec[int(m)] = r
        out["class_gas_by_month_offcap"][zname] = rec
    # by month
    out["by_month"] = {
        int(m): {
            "n": int((o & (days.month == m)).sum()),
            "gap": round(float((m_nyc - d_nyc)[o & (days.month == m)].mean()), 2),
            "model_gas": round(float(gas_nyc[o & (days.month == m)].mean()), 3),
            "z6": round(float(z6[o & (days.month == m)].mean()), 3),
        }
        for m in WINTER
        if (o & (days.month == m)).any()
    }
    return out


def main() -> None:
    """Run 2021-2025 and write JSON."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    ap.add_argument("--arm-ref", default="origin/claude/nyisonext23-result")
    ap.add_argument(
        "--years", nargs="+", type=int, default=[2021, 2022, 2023, 2024, 2025]
    )
    a = ap.parse_args()
    res = [gap(y, a.arm_ref) for y in a.years]
    Path(a.out).write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
