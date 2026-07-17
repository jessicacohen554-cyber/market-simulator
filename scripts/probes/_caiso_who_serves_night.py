"""WHO-SERVES-THE-NIGHT decomposition (C1 WP-B precondition, no new LP).

Decomposes overnight (hod 0-5) CAISO supply, MODEL vs MEASURED, to adjudicate
FINDING-caiso91c disclosed tension #1: de-committing overnight CC RAISES
overnight lambda (already +2..+4 over) UNLESS the displaced 1.3-2.5 TWh/yr is
served by cheaper overnight IMPORTS. This script measures the model's overnight
import headroom against reality.

MODEL side (from a solved bundle):
  * dispatch/{y}_P1.parquet  -> overnight TWh by klass (CC/CT/ST_GAS/hydro/
    nuclear/solar/wind/geo/...) and the plant_code->klass map used to classify
    the measured CEMS.
  * flows.parquet            -> net overnight imports = flow on
    WECC_import->NP15 + WECC_import->SP15_rest (positive = into CA).
  * storage.parquet          -> net overnight storage = discharge - charge.
  * system.parquet           -> overnight CA-zone demand + demand-weighted price.

MEASURED side:
  * EIA-930 CISO hourly (data/raw/eia-930-hourly/CISO hourly.parquet):
    imports=-Total interchange, hydro=NG:WAT, nuclear=NG:NUC, wind=NG:WND,
    gas=NG:NG, solar=NG:SUN, other=NG:OTH  (Local time = Pacific clock).
  * CAMPD facility CA_{y}.parquet -> measured gas by MODEL klass, via the
    plant_code->klass map + the LA-Basin repowering ORISPL crosswalk
    (CEMS 315/335/330 -> EIA 62115/62116/57901; without it ~1.6 TWh/yr
    phantom missing CEMS). facilityId is a STRING; absent rows = offline (a
    SUM over present hod 0-5 rows already treats them as 0).

Usage: python scripts/probes/_caiso_who_serves_night.py <bundle_dir>
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
EIA930 = REPO / "data" / "raw" / "eia-930-hourly" / "CISO hourly.parquet"
CAMPD = REPO / "data" / "raw" / "campd-facility-level"
YEARS = (2023, 2024, 2025)
OVERNIGHT = [0, 1, 2, 3, 4, 5]
# CA load zones. Imports = net flow into these from any NON-load (external) zone.
# Topology-robust: the keeper's caiso_per_hub_intertie renames WECC_import into
# per-hub corridor source zones, so hardcoding ("WECC_import", ...) would MISS
# every import. from_zone not in CA_ZONES => external import source.
CA_ZONES = {"NP15", "ZP26", "LA_BASIN", "SDGE", "SP15_rest"}
# LA-Basin repowering: CEMS facilityId -> EIA plant_code (fleet/klass key).
LA_BASIN = {"315": 62115, "335": 62116, "330": 57901}


def model_overnight(bundle: Path) -> dict:
    out = {}
    klass_map = {}  # plant_code -> klass (model's own classification)
    disp_klass = {}
    for y in YEARS:
        d = pd.read_parquet(
            bundle / "dispatch" / f"{y}_P1.parquet",
            columns=["klass", "plant_code", "hour", "mw", "zone"],
        )
        for pc, k in (
            d[["plant_code", "klass"]].drop_duplicates().itertuples(index=False)
        ):
            klass_map[int(pc)] = k
        hod = d.hour.to_numpy() % 24
        ov = d[np.isin(hod, OVERNIGHT)]
        disp_klass[y] = (ov.groupby("klass", observed=True).mw.sum() / 1e6).to_dict()

    # imports from flows — topology-robust net into CA load zones.
    flows = pd.read_parquet(bundle / "flows.parquet")
    fp1 = flows[flows["pass"] == "P1"]
    link_pairs = fp1[["from_zone", "to_zone"]].drop_duplicates()
    out["_link_pairs"] = [tuple(x) for x in link_pairs.itertuples(index=False)]
    imp = {}
    imp_detail = {}
    for y in YEARS:
        fy = fp1[fp1.year == y]
        hod = fy.hour.to_numpy() % 24
        fyov = fy[np.isin(hod, OVERNIGHT)]
        # external->CA links: +flow imports; CA->external links: -flow imports
        into = fyov[(~fyov.from_zone.isin(CA_ZONES)) & (fyov.to_zone.isin(CA_ZONES))]
        outof = fyov[(fyov.from_zone.isin(CA_ZONES)) & (~fyov.to_zone.isin(CA_ZONES))]
        net = into.mw.sum() - outof.mw.sum()
        imp[y] = net / 1e6
        det = {}
        for fr, to in out["_link_pairs"]:
            if fr in CA_ZONES and to in CA_ZONES:
                continue  # internal link
            sub = fyov[(fyov.from_zone == fr) & (fyov.to_zone == to)]
            det[f"{fr}->{to}"] = round(float(sub.mw.sum() / 1e6), 2)
        imp_detail[y] = det

    # storage net + demand + price
    stor, dem, price = {}, {}, {}
    sp = None
    stpath = bundle / "storage.parquet"
    if stpath.exists():
        st = pd.read_parquet(stpath)
        st = st[st["pass"] == "P1"]
    else:
        st = None
    sysdf = pd.read_parquet(bundle / "system.parquet")
    sysp1 = sysdf[sysdf["pass"] == "P1"]
    for y in YEARS:
        if st is not None:
            sty = st[st.year == y]
            hod = sty.hour.to_numpy() % 24
            styov = sty[np.isin(hod, OVERNIGHT)]
            stor[y] = (styov.discharge_mw.sum() - styov.charge_mw.sum()) / 1e6
        s = sysp1[sysp1.year == y]
        ca = s[~s.zone.str.startswith("WECC")]
        hod = ca.hour.to_numpy() % 24
        caov = ca[np.isin(hod, OVERNIGHT)]
        dem[y] = caov.groupby("hour").demand.sum().sum() / 1e6
        dw = (
            caov.assign(pw=caov.price * caov.demand)
            .groupby("hour")[["pw", "demand"]]
            .sum()
        )
        price[y] = float((dw.pw.sum() / dw.demand.sum()))

    out["disp_klass"] = disp_klass
    out["imports"] = imp
    out["imports_detail"] = imp_detail
    out["storage_net"] = stor
    out["demand"] = dem
    out["price_dw"] = price
    out["klass_map"] = klass_map
    return out


def measured_eia930() -> dict:
    df = pd.read_parquet(EIA930)
    lt = pd.to_datetime(df["Local time"])
    df = df.assign(year=lt.dt.year, hod=lt.dt.hour)
    ov = df[df.hod.isin(OVERNIGHT)]
    comps = {
        "imports": lambda d: -d["Total interchange"],
        "gas": lambda d: d["NG: NG"],
        "hydro": lambda d: d["NG: WAT"],
        "nuclear": lambda d: d["NG: NUC"],
        "wind": lambda d: d["NG: WND"],
        "solar": lambda d: d["NG: SUN"],
        "geo": lambda d: d["NG: GEO"],
        "other": lambda d: d["NG: OTH"],
        "demand": lambda d: d["Demand"],
    }
    res = {}
    for y in YEARS:
        dy = ov[ov.year == y]
        res[y] = {name: float(fn(dy).sum() / 1e6) for name, fn in comps.items()}
    return res


def measured_cems_by_klass(klass_map: dict) -> dict:
    """Measured overnight gas TWh by MODEL klass, from CAMPD facility CEMS."""
    res = {}
    for y in YEARS:
        f = CAMPD / f"CA_{y}.parquet"
        d = pd.read_parquet(f, columns=["facilityId", "date", "hour", "grossLoad"])
        d = d[d.hour.isin(OVERNIGHT)].copy()
        # facilityId str -> EIA plant_code int (LA-Basin remap first)
        fid = d.facilityId.astype(str)
        pc = fid.map(LA_BASIN)
        pc = pc.fillna(pd.to_numeric(fid, errors="coerce"))
        d["plant_code"] = pc
        d["klass"] = d.plant_code.map(klass_map)
        by = d.groupby("klass", observed=True).grossLoad.sum() / 1e6
        total = d.grossLoad.sum() / 1e6
        unmapped = d[d.klass.isna()].grossLoad.sum() / 1e6
        res[y] = {
            "by_klass": by.to_dict(),
            "total": float(total),
            "unmapped": float(unmapped),
        }
    return res


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    bundle = Path(sys.argv[1])
    m = model_overnight(bundle)
    e = measured_eia930()
    c = measured_cems_by_klass(m["klass_map"])

    gas_klasses = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP")
    print(
        "\n================ WHO SERVES THE NIGHT (overnight hod 0-5) ================"
    )
    for y in YEARS:
        dk = m["disp_klass"][y]
        print(f"\n===================== {y} =====================")
        print(f"{'source':<16}{'MODEL TWh':>12}{'MEAS TWh':>12}   note")
        # imports
        print(
            f"{'imports':<16}{m['imports'][y]:>12.2f}{e[y]['imports']:>12.2f}"
            f"   MODEL=flows WECC->CA ; MEAS=-interchange"
        )
        # gas by class (model dispatch vs measured CEMS)
        cby = c[y]["by_klass"]
        for k in gas_klasses:
            mo = dk.get(k, 0.0)
            me = cby.get(k, 0.0)
            if mo == 0 and me == 0:
                continue
            print(f"{k:<16}{mo:>12.2f}{me:>12.2f}   ")
        # gas total (model gas klasses vs EIA930 NG:NG and CEMS total)
        mgas = sum(dk.get(k, 0.0) for k in gas_klasses)
        print(
            f"{'gas TOTAL':<16}{mgas:>12.2f}{e[y]['gas']:>12.2f}"
            f"   (MEAS=EIA930 NG:NG; CEMS gas total={c[y]['total']:.2f}, "
            f"unmapped={c[y]['unmapped']:.2f})"
        )
        # hydro, nuclear, wind, solar, storage from model dispatch/storage
        for lbl, mk_opts, ek in [
            ("hydro", ("HYDRO", "HYDRO_PS", "PUMPED_STORAGE"), "hydro"),
            ("nuclear", ("NUCLEAR",), "nuclear"),
            ("wind", ("WIND",), "wind"),
            ("solar", ("SOLAR", "SOLAR_PV"), "solar"),
            ("geo", ("GEOTHERMAL", "GEO"), "geo"),
        ]:
            mo = sum(dk.get(k, 0.0) for k in mk_opts)
            print(f"{lbl:<16}{mo:>12.2f}{e[y][ek]:>12.2f}   ")
        print(
            f"{'storage(net)':<16}{m['storage_net'].get(y, float('nan')):>12.2f}"
            f"{'--':>12}   MODEL=discharge-charge"
        )
        print(f"{'demand':<16}{m['demand'][y]:>12.2f}{e[y]['demand']:>12.2f}   ")
        print(f"overnight demand-weighted MODEL price = ${m['price_dw'][y]:.2f}/MWh")
        print("  [model external-link overnight TWh]:", m["imports_detail"][y])
        # all model klasses (audit)
        print(
            "  [all model dispatch klasses overnight TWh]:",
            {k: round(v, 2) for k, v in sorted(dk.items(), key=lambda kv: -kv[1])},
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
