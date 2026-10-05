"""BUG-1 leap-clock census: each live consumer, old (date_range keeps Feb 29) vs fixed model_clock."""
import sys, json, importlib, inspect
import numpy as np, pandas as pd
sys.path.insert(0, "scripts")
from market_sim.utils import hour_calendar as hc

NEW = hc.model_clock
def OLD(year, hours=8760):
    return pd.date_range(f"{int(year)}-01-01", periods=int(hours), freq="h")
MODS = ["market_sim.model.reserves.spec","market_sim.model.interchange.neiso","market_sim.model.interchange.caiso",
        "market_sim.data.neighbor_price","market_sim.data.offer_curves","market_sim.data.fleet.offer_surfaces",
        "market_sim.data.eia930.weather","market_sim.data.eia930.envelopes"]
mods = [importlib.import_module(m) for m in MODS]
def use(fn):
    for m in mods: m.model_clock = fn
def clear():
    for m in mods:
        for _, f in inspect.getmembers(m):
            if hasattr(f, "cache_clear"): f.cache_clear()
def both(f):
    use(OLD); clear(); a = f()
    use(NEW); clear(); b = f()
    return a, b
def stat(a, b, unit):
    a = np.asarray(a, float); b = np.asarray(b, float)
    d = np.abs(np.nan_to_num(a) - np.nan_to_num(b))
    nh = int((d > 1e-9).sum()) if d.ndim == 1 else int((d > 1e-9).any(axis=0).sum())
    return {"hours_changed": nh, "sum_abs": round(float(d.sum()), 1), "max_abs": round(float(d.max()), 2),
            "sum_level": round(float(np.nansum(np.abs(b))), 1), "unit": unit}
out = {}
YEARS = (2020, 2024)
from market_sim.data.fleet import offer_surfaces as osf
for y in YEARS:
    a, b = both(lambda: osf._ercot_gas_day(y, 8760)); out[f"ERCOT {y} _ercot_gas_day (cleared-share + fast-start pool offer gas)"] = stat(a, b, "$/MMBtu-h")
    # PJM midcurve gas day (same normalizer, PJM basis)
    from market_sim.config.constants import GAS_BASIS_DIFFERENTIAL
    from market_sim.data.fuel import HENRY_HUB_DAILY_PATH
    hh = pd.read_csv(HENRY_HUB_DAILY_PATH, parse_dates=["date"]); s = hh.set_index("date")["price_usd_mmbtu"].sort_index()
    full = pd.date_range(s.index.min(), s.index.max() + pd.Timedelta(days=14), freq="D")
    daily = s.reindex(full).ffill() + float(GAS_BASIS_DIFFERENTIAL["PJM"])
    g = lambda clk: daily.reindex(clk(y, 8760).normalize()).ffill().bfill().to_numpy(float)
    out[f"PJM {y} _pjm_midcurve_context gas_day"] = stat(g(OLD), g(NEW), "$/MMBtu-h")
from market_sim.data.eia930 import envelopes as env
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.constants import PJM_EXTERNAL_FLOW_PERCENTILE, PJM_SEAM_FLOW_PERCENTILE
from market_sim.config.interchange_config import INTERFACE_NEIGHBORS
pjm_z = [z.name for z in get_iso_config("PJM").zones]
nb = [n.name for n in INTERFACE_NEIGHBORS.get("PJM", [])]
for y in YEARS:
    try:
        a, b = both(lambda: env.pjm_zonal_interchange_envelope(y, pjm_z, 8760, PJM_EXTERNAL_FLOW_PERCENTILE))
        if a is not None:
            out[f"PJM {y} pjm_zonal_interchange_envelope import_cap (pjm_congestion)"] = stat(a[0], b[0], "MWh")
            out[f"PJM {y} pjm_zonal_interchange_envelope export_cap"] = stat(a[1], b[1], "MWh")
        a, b = both(lambda: env.pjm_neighbor_interchange_envelope(y, nb, 8760, PJM_SEAM_FLOW_PERCENTILE))
        if a is not None:
            out[f"PJM {y} pjm_neighbor_interchange_envelope import_cap (pjm_seam_flow_limit)"] = stat(a[0], b[0], "MWh")
            out[f"PJM {y} pjm_neighbor_interchange_envelope export_cap (pjm_seam_export_limit)"] = stat(a[1], b[1], "MWh")
        a, b = both(lambda: env.pjm_net_interchange_envelope(y, 8760, PJM_EXTERNAL_FLOW_PERCENTILE))
        if a is not None: out[f"PJM {y} pjm_net_interchange_envelope (net position cut)"] = stat(a, b, "MWh")
    except Exception as e: out[f"PJM {y} envelopes"] = repr(e)
    try:
        a, b = both(lambda: env.measured_gas_floor_profile("CAISO", y, 8760))
        if a is not None: out[f"CAISO {y} measured_gas_floor_profile (x0.8 midday floor; p50 default)"] = stat(np.asarray(a)*0.8, np.asarray(b)*0.8, "MWh")
    except Exception as e: out[f"CAISO {y} gas floor"] = repr(e)
    try:
        from market_sim.config.interchange_config import CAISO_PER_HUB_NEIGHBORS
        from market_sim.data import neighbor_price as npx
        for k, spec in CAISO_PER_HUB_NEIGHBORS.items():
            a, b = both(lambda: npx.caiso_hub_measured_gas_reference_price(spec, y, 8760))
            if a is not None: out[f"CAISO {y} measured-gas ref price {k} (gap hours only consume it)"] = stat(a, b, "$/MWh-h")
    except Exception as e: out[f"CAISO {y} gas ref"] = repr(e)
from market_sim.model.reserves import spec as rs
a, b = both(lambda: rs.nyiso_li_30min_requirement_mw(2024, 8760, 270.0, 540.0))
out["NYISO 2024 LI 30-min requirement (On-Peak weekday mask)"] = stat(a, b, "MWh")
# temperature broadcast, every ISO zone with weather
from market_sim.data.eia930 import weather as w
for iso in ["CAISO","ERCOT","MISO","PJM","NEISO","NYISO","SPP","SOCO","NWPP"]:
    for y in YEARS:
        tot = {"tmax": [0.0, 0, 0.0], "tmin": [0.0, 0, 0.0]}; nz = 0
        for z in [z.name for z in get_iso_config(iso).zones]:
            try:
                a, b = both(lambda: w.iso_zone_tmax(iso, y, 8760, zone=z))
            except Exception as e:
                continue
            if a is None or b is None: continue
            nz += 1
            for i, k in enumerate(("tmax", "tmin")):
                if a[i] is None: continue
                d = np.abs(a[i] - b[i]); tot[k][0] += d.sum(); tot[k][1] = max(tot[k][1], int((d > 0).sum())); tot[k][2] = max(tot[k][2], float(d.max()))
        if nz: out[f"{iso} {y} iso_zone_tmax daily temp ({nz} zones)"] = {k: {"sum_abs_degC_h": round(v[0]), "hours_changed_max_zone": v[1], "max_abs_degC": round(v[2], 1)} for k, v in tot.items()}
    if iso == "NEISO":
        for y in YEARS:
            try:
                a, b = both(lambda: w.neiso_load_weighted_temp(y, 8760))
                if a is not None:
                    a0 = a[0] if isinstance(a, tuple) else a; b0 = b[0] if isinstance(b, tuple) else b
                    out[f"NEISO {y} neiso_load_weighted_temp (coldsnap derate driver)"] = stat(a0, b0, "degC-h")
            except Exception as e: out[f"NEISO {y} lwt"] = repr(e)
json.dump(out, open(sys.argv[1], "w"), indent=1, default=str)
for k, v in out.items(): print(k, "=>", v)
