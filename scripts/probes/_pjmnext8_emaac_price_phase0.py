"""PJM-NEXT-8 zero-LP phase 0: why is the keeper's EMAAC price above the NJ hub?

Rule 32 ``[R-SHARD]`` (a): no LP. Reads only committed artifacts and curated
inputs, plus a ``fleet_only`` rebuild of the keeper recipe (the pattern of
``_pjmnext8_cc2023_phase0.py``) for per-unit zone / class / mc / availability:

1. price decomposition — model zonal RT price vs the actual hub LMP split into
   energy / congestion / loss (``data/clean/lmp/PJM/RTM``);
2. EMAAC net position — model vs bench (EIA-923) fossil energy by class in
   EMAAC, nuclear from the rebuild, model demand vs PJM metered EMAAC load;
3. interface — published "Average Eastern" limit / transfer / utilisation and
   whether actual NJ congestion or model EMAAC separation coincides with it;
4. price setter — in hours model EMAAC > NJ hub + $5, the class/zone of the
   available unit whose mc is nearest the model EMAAC price, EMAAC's separation
   from Central_PA, and the EMAAC CC mc stack against the actual NJ price;
5. EMAAC gas — model EMAAC CC delivered fuel vs Henry Hub + the zonal hub basis.

Run: ``uv run python scripts/probes/_pjmnext8_emaac_price_phase0.py 2023 2024``
Writes ``results/phase0/pjm/_pjmnext8_emaac_price_phase0.json``.
"""

from __future__ import annotations

import base64
import gzip
import json
import logging
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

BUNDLE = REPO / "results/calibration/pjmnext7_vs_span"
RUN_JS = REPO / "frontend/data/backcast/runs/2026-09-28-pjm-next-7-virtual.js"
EMAAC = "PJM_EMAAC"
EMAAC_METER_ZONES = (
    "AE",
    "DPL",
    "JC",
    "PS",
    "RECO",
    "PE",
)  # iso_configs._pjm_config docstring
HUBS = ("NEW JERSEY HUB", "EASTERN HUB", "WESTERN HUB", "DOMINION HUB")


def load_payload() -> dict:
    """Decode the registered keeper run payload."""
    s = RUN_JS.read_text()
    b64 = re.search(r'="([A-Za-z0-9+/=]+)"', s).group(1)
    return json.loads(gzip.decompress(base64.b64decode(b64)))["years"]


def _drop_feb29(ts: pd.Series) -> np.ndarray:
    """Mask that drops Feb 29 (the model's 8760 clock)."""
    return ~((ts.dt.month == 2) & (ts.dt.day == 29)).to_numpy()


def actual_hubs(y: int) -> dict[str, pd.DataFrame]:
    """Hourly actual RT hub LMP components, UTC-sorted, 8760 rows each."""
    lm = pd.read_parquet(REPO / f"data/clean/lmp/PJM/RTM/lmp_{y}.parquet")
    out = {}
    for h in HUBS:
        d = lm[lm.node == h].sort_values("interval_start_utc")
        d = d[_drop_feb29(d.interval_start_local)].iloc[:8760].reset_index(drop=True)
        out[h] = d
    return out


def metered_emaac(y: int) -> np.ndarray:
    """PJM metered EMAAC load (MW), UTC-sorted, 8760 rows."""
    m = pd.read_csv(REPO / f"data/raw/zone-specific-demand/PJM{y}_hrl_load_metered.csv")
    m = m[m.zone.isin(EMAAC_METER_ZONES)]
    m["t"] = pd.to_datetime(m.datetime_beginning_utc, format="%m/%d/%Y %I:%M:%S %p")
    s = m.groupby("t").mw.sum().sort_index()
    loc = s.index.tz_localize("UTC").tz_convert("America/New_York").to_series()
    s = s[_drop_feb29(loc)]
    return s.to_numpy()[:8760]


def interface(y: int, name: str) -> pd.DataFrame:
    """Hourly published interface limit / transfer."""
    t = pd.read_parquet(
        REPO
        / f"data/clean/transfer-interface-limits/PJM/transfer-interface-limits_{y}.parquet"
    )
    return (
        t[t.interface == name]
        .sort_values("hour")
        .set_index("hour")[["limit_mw", "transfer_mw"]]
    )


def best_lag(a: np.ndarray, b: np.ndarray) -> int:
    """Shift of b that maximises correlation with a (alignment check)."""
    best = max(
        range(-6, 7), key=lambda k: np.corrcoef(a[6:-6], np.roll(b, k)[6:-6])[0, 1]
    )
    return best


def main() -> None:
    """Run the five zero-LP tests per year and write the JSON."""
    logging.disable(logging.CRITICAL)
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    pay = load_payload()
    hh = pd.read_parquet(REPO / "data/clean/fuel-hub-monthly/fuel-hub-monthly.parquet")
    zh = pd.read_parquet(REPO / "data/clean/fuel-zonal-hub/PJM/fuel-zonal-hub.parquet")
    out: dict = {"bundle": BUNDLE.name, "years": {}}
    for y in [int(a) for a in sys.argv[1:]] or [2023, 2024]:
        R: dict = {}
        sysh = pd.read_parquet(BUNDLE / f"hourly/system_{y}.parquet")
        sysh = sysh[sysh["pass"] == "P1"]
        P = sysh.pivot(index="hour", columns="zone", values="price").sort_index()
        D = sysh.pivot(index="hour", columns="zone", values="demand").sort_index()
        hubs = actual_hubs(y)
        met = metered_emaac(y)
        lag = best_lag(D[EMAAC].to_numpy(), met)
        # align actual series to the model clock with the lag the load match selects
        al = lambda a: np.roll(np.asarray(a, float), lag)  # noqa: E731
        nj = al(hubs["NEW JERSEY HUB"].lmp_usd_per_mwh)
        wh = al(hubs["WESTERN HUB"].lmp_usd_per_mwh)
        njc = al(hubs["NEW JERSEY HUB"].congestion_usd_per_mwh)
        pe, pc = P[EMAAC].to_numpy(), P["PJM_Central_PA"].to_numpy()
        R["alignment_lag_h"] = lag
        R["load_corr"] = float(np.corrcoef(D[EMAAC], al(met))[0, 1])

        # 1. price decomposition
        R["model_price_mean"] = {z: round(float(P[z].mean()), 2) for z in P.columns}
        R["actual_hub_components"] = {
            h: {
                c: round(float(d[c].mean()), 2)
                for c in (
                    "lmp_usd_per_mwh",
                    "energy_usd_per_mwh",
                    "congestion_usd_per_mwh",
                    "loss_usd_per_mwh",
                )
            }
            for h, d in hubs.items()
        }
        sep = pe - pc
        R["model_emaac_minus_cpa"] = {
            "mean": round(float(sep.mean()), 2),
            "frac_abs_lt_0p5": round(float((np.abs(sep) < 0.5).mean()), 3),
            "frac_gt_2": round(float((sep > 2).mean()), 3),
            "frac_lt_m2": round(float((sep < -2).mean()), 3),
        }
        R["actual_nj_minus_western"] = {
            "mean": round(float((nj - wh).mean()), 2),
            "frac_lt_m2": round(float(((nj - wh) < -2).mean()), 3),
            "frac_gt_2": round(float(((nj - wh) > 2).mean()), 3),
            "nj_congestion_frac_lt_m1": round(float((njc < -1).mean()), 3),
        }
        R["model_emaac_minus_nj"] = round(float((pe - nj).mean()), 2)
        R["model_emaac_minus_nj_median"] = round(float(np.median(pe - nj)), 2)
        spike = sep > 20
        R["model_sep_spike_hours_gt20"] = int(spike.sum())
        R["model_sep_mean_share_from_spikes"] = (
            round(float(sep[spike].sum() / sep.sum()), 3) if sep.sum() else None
        )
        ps = P["PJM_SWMAAC"].to_numpy()
        R["model_emaac_minus_swmaac"] = {
            "mean": round(float((pe - ps).mean()), 2),
            "frac_lt_m2_(EMAAC_export_bound)": round(float(((pe - ps) < -2).mean()), 3),
        }
        R["model_cpa_minus_western"] = round(float((pc - wh).mean()), 2)

        # 2./4. fleet rebuild (zero LP)
        kw = run_year_kwargs(meta)
        kw.update(derived_run_year_inputs(BUNDLE, y))
        kw["pjm_da_virtual_bids"] = False  # demand-side overlay, inert for offers
        r = run_year(
            y, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw
        )
        fa = r["fleet_arrays"]
        zn = list(r["iso_config"].zone_names)
        R["links_touching_emaac"] = [
            f"{ln.from_zone}->{ln.to_zone} ttc={getattr(ln, 'ttc_mw', None)}"
            for ln in r["iso_config"].links
            if EMAAC in (ln.from_zone, ln.to_zone)
        ]
        mc = np.asarray(r["mc_base"], float)
        T = mc.shape[1]
        avail = np.asarray(fa.availability, float)
        if avail.ndim == 1:
            avail = avail[:, None] * np.ones((1, T))
        pmax = np.asarray(fa.pmax, float)
        cls = np.asarray(fa.plant_group).astype(str)
        zi = np.asarray(fa.zone_idx).astype(int)
        zone = np.array([zn[i] for i in zi])
        fuel = np.asarray(r["fuel_prices"], float)
        if fuel.ndim == 1:
            fuel = fuel[:, None] * np.ones((1, T))
        # nuclear / firm by zone from the rebuild (must-run ~ pmax x avail)
        firm = {}
        for c in np.unique(cls):
            m = (zone == EMAAC) & (cls == c)
            if m.any():
                firm[c] = round(float((pmax[m, None] * avail[m]).sum() / 1e6), 2)
        R["emaac_available_twh_by_class_rebuild"] = firm

        # net position: model payload vs bench per class in EMAAC
        bench = json.load(
            gzip.open(REPO / f"frontend/data/backcast/bench/PJM/{y}.json.gz")
        )["bench"]["plants"]
        mp = pay[str(y)]["plants"]
        pos: dict = {}
        for k, b in bench.items():
            if (
                b.get("zone") != EMAAC
                or b.get("nodata") in (True, "True")
                or k not in mp
            ):
                continue
            g = pos.setdefault(b["group"], [0.0, 0.0])
            g[0] += float(mp[k]["m_ann"])
            g[1] += float(b.get("e_ann") or 0)
        R["emaac_fossil_twh_model_vs_e923"] = {
            c: [round(a, 2), round(e, 2), round(a - e, 2)] for c, (a, e) in pos.items()
        }
        fm = sum(v[0] for v in pos.values())
        fe = sum(v[1] for v in pos.values())
        # nuclear carries an empty plant_group in the rebuild (the only ~56 TWh
        # blank-class block in EMAAC); it enters model and actual identically
        nuc = sum(v for c, v in firm.items() if c == "" or "NUC" in c.upper())
        dm = float(D[EMAAC].sum() / 1e6)
        da = float(met.sum() / 1e6)
        R["emaac_net_position_twh"] = {
            "model_demand": round(dm, 2),
            "metered_load": round(da, 2),
            "fossil_model": round(fm, 2),
            "fossil_e923": round(fe, 2),
            "nuclear_avail_rebuild": round(nuc, 2),
            "net_import_model_(demand-fossil-nuc)": round(dm - fm - nuc, 2),
            "net_import_actual_(load-fossil-nuc)": round(da - fe - nuc, 2),
        }

        # 3. interface
        ie = interface(y, "Average Eastern")
        if len(ie) >= 8000:
            lim = ie.limit_mw.reindex(range(8760)).to_numpy()
            tr = ie.transfer_mw.reindex(range(8760)).to_numpy()
            ut = tr / lim
            ok = np.isfinite(ut)
            bind = ok & (ut >= 0.9)
            R["average_eastern"] = {
                "limit_mean": round(float(np.nanmean(lim)), 0),
                "transfer_mean": round(float(np.nanmean(tr)), 0),
                "frac_transfer_negative": round(float((tr[ok] < 0).mean()), 3),
                "frac_util_ge_0p9": round(float(bind.mean()), 3),
                "nj_cong_mean_when_bind": round(float(njc[bind].mean()), 2)
                if bind.any()
                else None,
                "nj_cong_mean_when_slack": round(float(njc[ok & ~bind].mean()), 2),
                "model_sep_mean_when_bind": round(float(sep[bind].mean()), 2)
                if bind.any()
                else None,
                "model_sep_mean_when_slack": round(float(sep[ok & ~bind].mean()), 2),
            }
        f5 = interface(y, "50045005 Post-Contingency")
        if len(f5):
            lim = f5.limit_mw.reindex(range(8760)).to_numpy()
            tr = f5.transfer_mw.reindex(range(8760)).to_numpy()
            ok = np.isfinite(tr / lim)
            R["iface_5004_5005"] = {
                "limit_mean": round(float(np.nanmean(lim)), 0),
                "transfer_mean": round(float(np.nanmean(tr)), 0),
                "frac_util_ge_0p9": round(float((ok & (tr / lim >= 0.9)).mean()), 3),
            }

        # 4. price setter in the over-priced hours
        hot = (pe - nj) > 5
        R["hot_hours"] = int(hot.sum())
        cand = (avail > 0.01) & (pmax[:, None] > 1) & np.isfinite(mc)
        mcm = np.where(cand, mc, np.nan)
        nearest = np.nanargmin(np.abs(mcm - pe[None, :]), axis=0)
        gap = np.abs(mc[nearest, np.arange(T)] - pe)
        tab: dict = {}
        for t in np.where(hot)[0]:
            if gap[t] > 1.0:
                key = "none_within_$1"
            else:
                key = f"{zone[nearest[t]][4:]}:{cls[nearest[t]]}"
            tab[key] = tab.get(key, 0) + 1
        R["hot_nearest_mc_setter"] = dict(
            sorted(tab.items(), key=lambda kv: -kv[1])[:10]
        )
        R["hot_model_emaac_minus_cpa_mean"] = round(float(sep[hot].mean()), 2)
        R["hot_actual_nj_minus_western_mean"] = round(float((nj - wh)[hot].mean()), 2)
        R["hot_nj_congestion_mean"] = round(float(njc[hot].mean()), 2)
        cc = (zone == EMAAC) & (cls == "CC_REGULAR") & (pmax > 1)
        ccmc = np.where(cand[cc], mc[cc], np.nan)
        p10 = np.nanpercentile(ccmc, 10, axis=0)
        p50 = np.nanpercentile(ccmc, 50, axis=0)
        R["emaac_cc_mc"] = {
            "p10_mean": round(float(np.nanmean(p10)), 2),
            "p50_mean": round(float(np.nanmean(p50)), 2),
            "frac_hours_nj_below_p10": round(float((nj < p10).mean()), 3),
            "frac_hours_model_emaac_below_p10": round(float((pe < p10).mean()), 3),
        }
        # 5. gas: model EMAAC CC delivered fuel vs HH + zonal basis
        hhy = float(
            hh[(hh.hub == "henry_hub") & (hh.year == y)].price_usd_per_mmbtu.mean()
        )
        gas = {"henry_hub": round(hhy, 3)}
        for z in (EMAAC, "PJM_Central_PA", "PJM_Dominion", "PJM_SWMAAC"):
            m = (zone == z) & (cls == "CC_REGULAR") & (pmax > 1)
            ww = pmax[m][:, None] * avail[m]
            b = zh[(zh.zone == z) & (zh.year == y)]
            gas[z] = {
                "model_cc_fuel": round(float((fuel[m] * ww).sum() / ww.sum()), 3),
                "model_cc_mc": round(float((mc[m] * ww).sum() / ww.sum()), 2),
                "hub": b.hub.iloc[0] if len(b) else None,
                "hh_plus_basis": round(hhy + float(b.basis_vs_hh_usd_mmbtu.iloc[0]), 3)
                if len(b)
                else None,
            }
        R["gas"] = gas
        R["emaac_cc_gw"] = round(float(pmax[cc].sum() / 1e3), 1)
        mon = pd.Series(pe - nj).groupby(np.minimum(np.arange(8760) // 730, 11)).mean()
        R["monthly_model_emaac_minus_nj"] = [round(float(v), 1) for v in mon]
        out["years"][str(y)] = R
        print(json.dumps({y: R}, indent=1, default=str))
    dest = REPO / "results/phase0/pjm/_pjmnext8_emaac_price_phase0.json"
    dest.write_text(json.dumps(out, indent=1, default=str))
    print("wrote", dest)


if __name__ == "__main__":
    main()
