#!/usr/bin/env python3
"""Holdout data-availability scan: per ISO x year coverage of measured inputs.

Read-only. No LP, no loader dispatch — pure file/row existence checks
(rule 22 channel-1 style no-LP validation).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
VS = RAW / "_validation-source"
YEARS = list(range(2018, 2027))

ISO_STATES = {
    "ERCOT": ("TX",),
    "CAISO": ("CA",),
    "NYISO": ("NY", "NJ"),
    "NEISO": ("ME", "NH", "MA", "CT", "RI", "VT"),
    "PJM": ("PA", "NJ", "MD", "DE", "IL", "OH", "IN", "KY", "WV", "VA", "NC", "TN", "MI", "DC"),
    "MISO": ("AR", "IA", "IL", "IN", "KY", "LA", "MI", "MN", "MO", "MS", "ND", "SD", "TX", "WI"),
}
BA = {"ERCOT": "ERCO", "CAISO": "CISO", "PJM": "PJM", "MISO": "MISO", "NYISO": "NYIS", "NEISO": "ISNE"}
ISOS = ["ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO"]

out: dict = {}


def sec(name):
    out[name] = {}
    return out[name]


# ---- 1. CAMPD unit-level & facility-level ------------------------------------
for kind in ("campd-unit-level", "campd-facility-level"):
    d = sec(kind)
    for iso in ISOS:
        d[iso] = {}
        for y in YEARS:
            present = [st for st in ISO_STATES[iso] if (RAW / kind / f"{st}_{y}.parquet").exists()]
            missing = [st for st in ISO_STATES[iso] if st not in present]
            d[iso][y] = f"{len(present)}/{len(ISO_STATES[iso])}" + (f" missing={','.join(missing)}" if missing and present else ("" if present else " NONE"))

# ---- 2. Outage window CSVs -----------------------------------------------------
d = sec("unit-outage-windows")
for iso in ISOS:
    f = RAW / ("campd-unit-outages.csv" if iso == "ERCOT" else f"campd-unit-outages-{iso}.csv")
    if not f.exists():
        d[iso] = "FILE ABSENT"
        continue
    df = pd.read_csv(f, usecols=lambda c: c in ("outage_start", "start", "start_date"), low_memory=False)
    col = df.columns[0]
    yrs = pd.to_datetime(df[col]).dt.year.value_counts().sort_index()
    d[iso] = {int(k): int(v) for k, v in yrs.items()}

d = sec("partial-outage-windows")
for iso in ISOS:
    f = RAW / ("campd-partial-outages.csv" if iso == "ERCOT" else f"campd-partial-outages-{iso}.csv")
    if not f.exists():
        d[iso] = "FILE ABSENT"
        continue
    df = pd.read_csv(f, low_memory=False)
    col = [c for c in df.columns if "start" in c.lower()][0]
    yrs = pd.to_datetime(df[col]).dt.year.value_counts().sort_index()
    d[iso] = {int(k): int(v) for k, v in yrs.items()}

# ---- 3. EIA-930: demand profiles, wide hourly, long-form ----------------------
d = sec("eia930-demand-profiles")
try:
    prof = pd.read_parquet(RAW / "eia-930" / "eia_demand_profiles.parquet")
    icol = [c for c in prof.columns if c.lower() in ("iso", "ba", "region")][0]
    ycol = [c for c in prof.columns if c.lower() == "year"][0]
    g = prof.groupby([icol, ycol]).size()
    for iso in ISOS:
        keys = [iso, BA[iso]]
        rows = {}
        for k in keys:
            if k in g.index.get_level_values(0):
                rows = {int(y): int(n) for (i, y), n in g.items() if i == k}
                break
        d[iso] = rows
except Exception as e:  # noqa: BLE001
    d["ERROR"] = repr(e)

d = sec("eia930-wide-hourly")
for iso in ISOS:
    f = RAW / "eia-930-hourly" / f"{BA[iso]} hourly.parquet"
    if not f.exists():
        d[iso] = "FILE ABSENT"
        continue
    df = pd.read_parquet(f)
    tcol = [c for c in df.columns if "utc" in c.lower() or "time" in c.lower() or "date" in c.lower()][0]
    yrs = pd.to_datetime(df[tcol]).dt.year.value_counts().sort_index()
    d[iso] = {int(k): int(v) for k, v in yrs.items() if 2018 <= k <= 2026}

d = sec("eia930-longform")
for iso in ISOS:
    d[iso] = {}
    for y in YEARS:
        have = [k for k in ("fueltype", "region") if (RAW / "eia-930" / f"{BA[iso]}_{k}_{y}.parquet").exists()]
        d[iso][y] = "+".join(have) if have else "-"

# multi-year single files (no year suffix)
d = sec("eia930-longform-multiyear")
for iso in ISOS:
    d[iso] = {}
    for k in ("fueltype", "region"):
        f = RAW / f"{BA[iso]}_{k}.parquet"
        if f.exists():
            df = pd.read_parquet(f, columns=None)
            tcol = [c for c in df.columns if "period" in c.lower() or "time" in c.lower() or "date" in c.lower()]
            if tcol:
                yrs = sorted(pd.to_datetime(df[tcol[0]]).dt.year.unique())
                d[iso][k] = f"{yrs[0]}-{yrs[-1]}"
            else:
                d[iso][k] = "present"

# ---- 4. F923 monthly fuel costs / generation ----------------------------------
d = sec("f923-monthly")
try:
    fc = pd.read_parquet(RAW / "_processed-legacy" / "eia923_monthly_fuel_costs.parquet")
    stc = [c for c in fc.columns if c.lower() in ("state", "plant_state")][0]
    yc = [c for c in fc.columns if c.lower() == "year"][0]
    for iso in ISOS:
        sub = fc[fc[stc].isin(ISO_STATES[iso])]
        d[iso] = {int(k): int(v) for k, v in sub.groupby(yc).size().items()}
except Exception as e:  # noqa: BLE001
    d["ERROR"] = repr(e)

# ---- 5. Emission rates ---------------------------------------------------------
d = sec("plant-emission-rates-v1")
try:
    v1 = pd.read_parquet(RAW / "_processed-legacy" / "plant_emission_rates.parquet")
    d["years"] = sorted(int(y) for y in v1["year"].unique())
except Exception as e:  # noqa: BLE001
    d["ERROR"] = repr(e)

d = sec("plant-emission-rates-v2")
try:
    v2 = pd.read_parquet(RAW / "_processed-legacy" / "plant_emission_rates_v2.parquet")
    icol = [c for c in v2.columns if c.lower() == "iso"]
    yc = [c for c in v2.columns if c.lower() == "year"][0]
    if icol:
        g = v2.groupby([icol[0], yc]).size()
        for iso in ISOS:
            d[iso] = {int(y): int(n) for (i, y), n in g.items() if i == iso}
    else:
        stc = [c for c in v2.columns if "state" in c.lower()][0]
        for iso in ISOS:
            sub = v2[v2[stc].isin(ISO_STATES[iso])]
            d[iso] = {int(k): int(v) for k, v in sub.groupby(yc).size().items()}
except Exception as e:  # noqa: BLE001
    d["ERROR"] = repr(e)

d = sec("fossil-co2-rates")
try:
    fr = pd.read_parquet(RAW / "_processed-legacy" / "fossil_co2_rates.parquet")
    yc = [c for c in fr.columns if c.lower() == "year"][0]
    d["years"] = {int(k): int(v) for k, v in fr.groupby(yc).size().items()}
except Exception as e:  # noqa: BLE001
    d["ERROR"] = repr(e)

d = sec("parasitic-load-factors")
try:
    pl = pd.read_parquet(RAW / "_processed-legacy" / "parasitic_load_factors.parquet")
    yc = [c for c in pl.columns if c.lower() == "year"][0]
    d["years"] = {int(k): int(v) for k, v in pl.groupby(yc).size().items()}
except Exception as e:  # noqa: BLE001
    d["ERROR"] = repr(e)

# ---- 6. eGRID + EIA-860 vintages ----------------------------------------------
d = sec("egrid-vintages")
d["files"] = sorted(p.name for p in (RAW / "fleet-egrid").glob("egrid*"))
d2 = sec("eia860-vintages")
d2["dirs"] = sorted(p.name for p in (RAW / "eia-860").glob("vintage_*"))

# ---- 7. Weather ---------------------------------------------------------------
d = sec("weather")
for iso in ISOS:
    wdir = RAW / f"{iso.lower()}-weather"
    if not wdir.exists():
        d[iso] = "DIR ABSENT"
        continue
    d[iso] = {}
    for f in sorted(wdir.glob("*.csv")):
        try:
            df = pd.read_csv(f, low_memory=False)
            dcol = [c for c in df.columns if "date" in c.lower()]
            if dcol:
                yrs = pd.to_datetime(df[dcol[0]]).dt.year
                d[iso][f.name] = f"{int(yrs.min())}-{int(yrs.max())}"
            else:
                d[iso][f.name] = f"{len(df)} rows (no date col)"
        except Exception as e:  # noqa: BLE001
            d[iso][f.name] = f"ERR {e}"

# ---- 8. Gas -------------------------------------------------------------------
d = sec("gas")
hh = pd.read_csv(RAW / "gas-prices" / "henry_hub_monthly.csv")
dcol = [c for c in hh.columns if "date" in c.lower() or "month" in c.lower()][0]
d["henry_hub_monthly"] = f"{hh[dcol].min()} .. {hh[dcol].max()}"
gb = pd.read_csv(RAW / "gas_basis_by_iso_month.csv")
icol = [c for c in gb.columns if c.lower() == "iso"][0]
ycol = [c for c in gb.columns if c.lower() == "year"][0]
g = gb.groupby([icol, ycol]).size()
d["gas_basis_by_iso_month"] = {}
for iso in ISOS:
    d["gas_basis_by_iso_month"][iso] = {int(y): int(n) for (i, y), n in g.items() if i == iso and 2018 <= y <= 2026}
for iso in ISOS:
    f = RAW / f"{iso.lower()}_zonal_gas_hub.csv"
    if f.exists():
        z = pd.read_csv(f)
        yc = [c for c in z.columns if c.lower() == "year"][0]
        d[f"{iso.lower()}_zonal_gas_hub"] = {int(k): int(v) for k, v in z.groupby(yc).size().items()}
for name in ("ercot_electric_power_gas_price.csv", "gas-prices/algonquin_citygate_daily.csv",
             "gas-prices/transco_z6_ny_daily.csv", "gas-prices/transco_z6_iroquois_monthly.csv",
             "gas-prices/nyiso_som_hub_fuel_annual.csv", "gas-prices/nyiso_downstate_ct_gas_basis_monthly.csv",
             "gas-prices/nyiso_downstate_ldc_transport_monthly.csv", "gas-prices/socal_citygate_daily.csv",
             "gas-prices/socal_citygate_monthly.csv", "gas-prices/chicago_citygate_daily.csv"):
    f = RAW / name
    if not f.exists():
        d[name] = "FILE ABSENT"
        continue
    z = pd.read_csv(f, low_memory=False)
    cand = [c for c in z.columns if c.lower() in ("date", "month", "year", "period")]
    if cand:
        c0 = cand[0]
        if c0.lower() == "year":
            yrs = z[c0]
        else:
            yrs = pd.to_datetime(z[c0], errors="coerce").dt.year
        vc = yrs.value_counts().sort_index()
        d[name] = {int(k): int(v) for k, v in vc.items() if 2018 <= k <= 2026}
    else:
        d[name] = f"{len(z)} rows cols={list(z.columns)[:6]}"

# ---- 9. Bench: LMP + tail + calref + renewable capacity ------------------------
d = sec("bench-lmp-json")
lmp = json.loads((VS / "actual_lmp.json").read_text())
for iso in ISOS:
    blk = lmp.get(iso) or {}
    yrs = sorted(k for k in blk if re.fullmatch(r"\d{4}", str(k)))
    if not yrs and isinstance(blk, dict):
        # maybe nested under 'annual'
        for sub in blk.values():
            if isinstance(sub, dict):
                yrs = sorted(set(yrs) | {k for k in sub if re.fullmatch(r"\d{4}", str(k))})
    d[iso] = yrs

d = sec("bench-lmp-hourly")
for iso in ISOS:
    f = VS / f"actual_lmp_hourly_{iso}.parquet"
    if not f.exists():
        d[iso] = "FILE ABSENT"
        continue
    df = pd.read_parquet(f)
    ycol = [c for c in df.columns if c.lower() == "year"]
    if ycol:
        grp = df.groupby(ycol[0])
        info = {}
        vcols = [c for c in df.columns if df[c].dtype.kind == "f"]
        for y, gdf in grp:
            nn = gdf[vcols].notna().mean().mean() if vcols else float("nan")
            info[int(y)] = f"{len(gdf)}h nonnull={nn:.2f}"
        d[iso] = info
    else:
        tcol = [c for c in df.columns if "time" in c.lower() or "date" in c.lower() or "hour" in c.lower()][0]
        yrs = pd.to_datetime(df[tcol]).dt.year.value_counts().sort_index()
        d[iso] = {int(k): int(v) for k, v in yrs.items()}

d = sec("bench-tail")
tail = json.loads((ROOT / "frontend/data/backcast/tail/actual_tail.json").read_text()) if (ROOT / "frontend/data/backcast/tail/actual_tail.json").exists() else {}
for iso in ISOS:
    blk = tail.get(iso) or {}
    d[iso] = sorted(blk.keys()) if isinstance(blk, dict) else str(type(blk))

d = sec("calibration-reference")
cr = json.loads((VS / "calibration_reference.json").read_text())
for iso in ISOS:
    d[iso] = sorted((cr.get("isos", {}).get(iso) or {}).keys())

d = sec("renewable-capacity-sidecars")
for iso in ISOS:
    d[iso] = sorted(int(m.group(1)) for p in VS.glob(f"{iso}_*_renewable_capacity.csv") if (m := re.match(rf"{iso}_(\d{{4}})_", p.name)))

# ---- 10. Zone-specific demand ---------------------------------------------------
d = sec("zone-specific-demand")
zd = RAW / "zone-specific-demand"
for iso in ISOS:
    idir = zd / iso
    if not idir.exists():
        cand = [p.name for p in zd.iterdir()] if zd.exists() else []
        d[iso] = f"DIR ABSENT (have {cand})"
        continue
    files = sorted(p.name for p in idir.rglob("*") if p.is_file())
    yrs = sorted({int(m.group(0)) for f in files for m in re.finditer(r"20\d\d", f)})
    d[iso] = {"n_files": len(files), "years_in_names": yrs}

# ---- 11. ISO-specific availability/outage/AS sources ---------------------------
d = sec("iso-specific")


def year_span_csv(path, label):
    try:
        z = pd.read_csv(path, low_memory=False, nrows=500000)
        cand = [c for c in z.columns if any(k in c.lower() for k in ("date", "day", "time", "start"))]
        if cand:
            yrs = pd.to_datetime(z[cand[0]], errors="coerce").dt.year
            vc = yrs.value_counts().sort_index()
            return {int(k): int(v) for k, v in vc.items() if k and 2015 <= k <= 2027}
        return f"{len(z)} rows"
    except Exception as e:  # noqa: BLE001
        return f"ERR {e}"


# ERCOT
d["ERCOT"] = {}
for f in ("ercot-thermal-dam-availability.csv", "ercot-thermal-dam-availability-hourly.csv",
          "ercot-outages.csv", "ercot-noncampd-availability.csv", "ercot-nuclear-availability.csv"):
    p = RAW / f
    d["ERCOT"][f] = year_span_csv(p, f) if p.exists() else "ABSENT"
d["ERCOT"]["ercot-hsl"] = sorted(p.name for p in (RAW / "ercot-hsl").glob("*")) if (RAW / "ercot-hsl").exists() else "ABSENT"
d["ERCOT"]["ercot-AS"] = sorted(p.name for p in (RAW / "ercot-AS").glob("*"))[:20] if (RAW / "ercot-AS").exists() else "ABSENT"
d["ERCOT"]["ercot dir"] = sorted(p.name for p in (RAW / "ercot").glob("*"))[:25] if (RAW / "ercot").exists() else "ABSENT"

# PJM
d["PJM"] = {}
pj = RAW / "pjm-outages" / "by-year"
d["PJM"]["pjm-outages/by-year"] = sorted(p.name for p in pj.glob("*.csv")) if pj.exists() else "ABSENT"
for sub in ("pjm-energy-offers", "pjm-zonal-lmp", "pjm-da-virtuals", "pjm-ehv-lmp", "pjm-binding-constraints"):
    p = RAW / sub
    d["PJM"][sub] = sorted(q.name for q in p.glob("*"))[:15] if p.exists() else "ABSENT"
d["PJM"]["PJM dir"] = sorted(p.name for p in (RAW / "PJM").glob("*"))[:25] if (RAW / "PJM").exists() else "ABSENT"
d["PJM"]["PJM-AS"] = sorted(p.name for p in (RAW / "PJM-AS").glob("*"))[:15] if (RAW / "PJM-AS").exists() else "ABSENT"

# CAISO
d["CAISO"] = {}
for sub in ("caiso-dam-outages", "caiso-hsl", "caiso-curtailment", "caiso-public-bids", "CAISO-AS", "storage-as-awards"):
    p = RAW / sub
    d["CAISO"][sub] = sorted(q.name for q in p.glob("*"))[:20] if p.exists() else "ABSENT"

# MISO
d["MISO"] = {}
for sub in ("miso-generation-outages", "miso-hsl", "miso-pra", "maxgen-events", "MISO", "MISO-AS", "miso-wind-shape"):
    p = RAW / sub
    d["MISO"][sub] = sorted(q.name for q in p.glob("*"))[:20] if p.exists() else "ABSENT"

# NYISO
d["NYISO"] = {}
ny = RAW / "NYISO"
d["NYISO"]["NYISO dir"] = sorted(p.name for p in ny.glob("*"))[:20] if ny.exists() else "ABSENT"
iff = ny / "interface-flows"
if iff.exists():
    files = sorted(p.name for p in iff.rglob("*") if p.is_file())
    yrs = sorted({int(m.group(0)) for f in files for m in re.finditer(r"20\d\d", f)})
    d["NYISO"]["interface-flows years"] = yrs
nyas = RAW / "NYISO-AS"
if nyas.exists():
    d["NYISO"]["NYISO-AS"] = sorted(p.name for p in nyas.glob("*"))[:30]
    req = nyas / "requirements"
    if req.exists():
        d["NYISO"]["requirements"] = sorted(p.name for p in req.glob("*"))[:30]

# NEISO
d["NEISO"] = {}
noc = RAW / "neiso-operable-capacity"
d["NEISO"]["operable-capacity"] = sorted(p.name for p in noc.glob("*")) if noc.exists() else "ABSENT"
nas = RAW / "NEISO-AS"
d["NEISO"]["NEISO-AS"] = sorted(p.name for p in nas.glob("*"))[:20] if nas.exists() else "ABSENT"
wfi = RAW / "winter-fuel-inventory"
d["NEISO"]["winter-fuel-inventory"] = sorted(str(p.relative_to(wfi)) for p in wfi.rglob("*") if p.is_file())[:10] if wfi.exists() else "ABSENT"
lmpd = RAW / "lmp-data"
if lmpd.exists():
    d["NEISO"]["lmp-data"] = sorted(str(p.relative_to(lmpd)) for p in lmpd.rglob("*.xlsx"))[:30]

# capacity-deliverability
d2 = sec("capacity-deliverability")
cd = RAW / "capacity-deliverability"
if cd.exists():
    for p in sorted(cd.rglob("*.csv")):
        try:
            z = pd.read_csv(p)
            yc = [c for c in z.columns if "year" in c.lower()]
            d2[str(p.relative_to(cd))] = sorted(z[yc[0]].astype(str).unique().tolist()) if yc else f"{len(z)} rows"
        except Exception as e:  # noqa: BLE001
            d2[str(p.relative_to(cd))] = f"ERR {e}"

print(json.dumps(out, indent=1, default=str))
