"""CAISO-102 evening merit-stack diagnosis (priority 2, no new LP).

The caiso-101 promotion deepened the evening (hod 17-21) under-price to
-5.8/-4.9/-3.0 $/MWh (2023/24/25) — the largest remaining lambda-ladder
residual (the flat CHP cogen baseload displaced marginal evening gas). This
probe asks WHO SERVES THE MEASURED EVENING THAT THE MODEL PRICES TOO CHEAP:
an hour-paired composition decomposition of the evening supply stack, model
vs measured, conditioned on the residual itself.

MODEL side (same-machine repro of the caiso-101 keeper,
``_caiso102_repro_A.py`` -> gitignored ``caiso102_repro_A``, FINDING-caiso92b
protocol): dispatch/{y}_P1.parquet by klass; flows.parquet net imports into CA
zones (topology-robust, the _caiso_who_serves_night construction);
storage.parquet net battery; system.parquet demand-weighted CA lambda.
MEASURED side: EIA-930 CISO hourly (imports=-interchange, gas=NG:NG,
hydro/solar/wind/nuclear, battery=NG:OTH), CAMPD facility CEMS CA_{y}.parquet
by model klass (LA-Basin ORISPL crosswalk), actual_lmp_hourly_CAISO.parquet.

Hour pairing: model hours are the repo 8760 non-leap calendar; measured series
drop Feb-29 (2024) and zero-pad short tails (2025 EIA-930 ends 8751 h — the
pad hours carry zero weight in every conditioned stat because pairing masks on
finite actuals).

Emits, per year:
  1. evening composition (TWh): model vs measured, by source + gas by klass;
  2. per-hod (17..21) lambda residual + the model-minus-measured avg-MW deltas
     (imports, gas, battery-net, hydro);
  3. the residual-quartile conditioning: evening hours bucketed by resid
     (model - actual rt); per bucket the composition deltas — who over-serves
     the hours the model prices too cheap;
  4. monthly evening resid (locates the season);
  5. CT_PEAKER/CC_REGULAR evening MW model-vs-CEMS in the deep bucket.

Usage: python scripts/probes/_caiso102_evening_merit.py <bundle_dir>
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
EIA930 = REPO / "data" / "raw" / "eia-930-hourly" / "CISO hourly.parquet"
CAMPD = REPO / "data" / "raw" / "campd-facility-level"
LMP = REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_CAISO.parquet"
YEARS = (2023, 2024, 2025)
EVENING = [17, 18, 19, 20, 21]
CA_ZONES = {"NP15", "ZP26", "LA_BASIN", "SDGE", "SP15_rest"}
LA_BASIN = {"315": 62115, "335": 62116, "330": 57901}
GAS_KLASSES = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP")
_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
MONTH_OF_HOUR = np.repeat(np.arange(1, 13), [d * 24 for d in _DAYS])  # len 8760


def _pad(v: np.ndarray) -> np.ndarray:
    """Zero-pad to 8760."""
    v = np.nan_to_num(v[:8760].astype(float))
    return np.pad(v, (0, 8760 - len(v))) if len(v) < 8760 else v


def eia930_hourly(year: int) -> dict[str, np.ndarray]:
    """(8760,) measured series on the non-leap calendar (Feb-29 dropped)."""
    d = pd.read_parquet(EIA930)
    d["Local date"] = pd.to_datetime(d["Local date"])
    dy = d[
        (d["Local date"].dt.year == year)
        & ((d["Local date"].dt.month != 2) | (d["Local date"].dt.day != 29))
    ].sort_values(["Local date", "Hour"])
    return {
        "imports": _pad(-dy["Total interchange"].to_numpy(float)),
        "gas": _pad(dy["NG: NG"].to_numpy(float)),
        "hydro": _pad(dy["NG: WAT"].to_numpy(float)),
        "solar": _pad(dy["NG: SUN"].to_numpy(float)),
        "wind": _pad(dy["NG: WND"].to_numpy(float)),
        "nuclear": _pad(dy["NG: NUC"].to_numpy(float)),
        "battery": _pad(dy["NG: OTH"].to_numpy(float)),
        "demand": _pad(dy["Demand"].to_numpy(float)),
    }


def cems_hourly_by_klass(year: int, klass_map: dict) -> dict[str, np.ndarray]:
    """(8760,) measured gas MW by model klass from CAMPD facility CEMS."""
    d = pd.read_parquet(
        CAMPD / f"CA_{year}.parquet",
        columns=["facilityId", "date", "hour", "grossLoad"],
    )
    dt = pd.to_datetime(d.date)
    d = d[(dt.dt.month != 2) | (dt.dt.day != 29)].copy()
    dt = pd.to_datetime(d.date)
    doy = dt.dt.dayofyear.to_numpy()
    # after Feb-29 in a leap year, dayofyear is +1 vs the non-leap calendar
    if year % 4 == 0:
        doy = np.where((dt.dt.month > 2).to_numpy(), doy - 1, doy)
    hidx = (doy - 1) * 24 + d.hour.to_numpy()
    fid = d.facilityId.astype(str)
    pc = fid.map(LA_BASIN)
    pc = pd.to_numeric(pc.fillna(pd.to_numeric(fid, errors="coerce")))
    d = d.assign(hidx=hidx, klass=pc.map(klass_map))
    out = {}
    for k in GAS_KLASSES:
        sub = d[d.klass == k]
        v = np.zeros(8760)
        np.add.at(v, sub.hidx.to_numpy(int), sub.grossLoad.fillna(0.0).to_numpy(float))
        out[k] = v
    return out


def model_hourly(bundle: Path, year: int) -> dict[str, np.ndarray]:
    """(8760,) model series: lambda, demand, net imports, battery net, by-klass MW."""
    out = {}
    s = pd.read_parquet(bundle / "system.parquet")
    s = s[(s["pass"] == "P1") & (s.year == year)]
    ca = s[~s.zone.str.startswith("WECC")]
    dw = (
        ca.assign(pw=ca.price * ca.demand)
        .groupby("hour")[["pw", "demand"]]
        .sum()
        .sort_index()
        .reindex(range(8760))
    )
    out["lambda"] = (dw.pw / dw.demand).to_numpy()
    out["demand"] = dw.demand.to_numpy()

    f = pd.read_parquet(bundle / "flows.parquet")
    f = f[(f["pass"] == "P1") & (f.year == year)]
    into = f[(~f.from_zone.isin(CA_ZONES)) & (f.to_zone.isin(CA_ZONES))]
    outof = f[(f.from_zone.isin(CA_ZONES)) & (~f.to_zone.isin(CA_ZONES))]
    imp = np.zeros(8760)
    np.add.at(imp, into.hour.to_numpy(int), into.mw.to_numpy(float))
    np.add.at(imp, outof.hour.to_numpy(int), -outof.mw.to_numpy(float))
    out["imports"] = imp

    st = pd.read_parquet(bundle / "storage.parquet")
    st = st[(st["pass"] == "P1") & (st.year == year)]
    bat = st[st.tech != "pumped_storage"]
    ps = st[st.tech == "pumped_storage"]
    for tag, sub in (("battery", bat), ("ps", ps)):
        v = np.zeros(8760)
        np.add.at(
            v,
            sub.hour.to_numpy(int),
            (sub.discharge_mw - sub.charge_mw).to_numpy(float),
        )
        out[f"{tag}_net"] = v

    d = pd.read_parquet(
        bundle / "dispatch" / f"{year}_P1.parquet",
        columns=["klass", "plant_code", "hour", "mw"],
    )
    out["_klass_map"] = {
        int(pc): k
        for pc, k in d[["plant_code", "klass"]]
        .drop_duplicates()
        .itertuples(index=False)
    }
    for k, sub in d.groupby("klass", observed=True):
        v = np.zeros(8760)
        np.add.at(v, sub.hour.to_numpy(int), sub.mw.to_numpy(float))
        out[f"k_{k}"] = v
    return out


def actual_rt(year: int) -> np.ndarray:
    a = pd.read_parquet(LMP)
    a = a[a.year == year].sort_values("hour")
    return _pad(a.rt.to_numpy(float))


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    bundle = Path(sys.argv[1])
    ev_mask = np.isin(np.arange(8760) % 24, EVENING)

    for y in YEARS:
        m = model_hourly(bundle, y)
        e = eia930_hourly(y)
        c = cems_hourly_by_klass(y, m["_klass_map"])
        rt = actual_rt(y)
        resid = m["lambda"] - rt
        ok = ev_mask & np.isfinite(resid) & (np.abs(rt) > 1e-9)

        print(f"\n===================== {y} =====================")
        dwr = float((resid[ok] * m["demand"][ok]).sum() / m["demand"][ok].sum())
        print(f"evening demand-weighted resid (model - actual rt): {dwr:+.1f} $/MWh")

        # 1. composition TWh
        mgas = sum(m.get(f"k_{k}", np.zeros(8760)) for k in GAS_KLASSES)
        mhyd = sum(
            m.get(f"k_{k}", np.zeros(8760)) for k in ("HYDRO", "HYDRO_PS")
        ) + np.clip(m["ps_net"], 0, None)
        rows = [
            ("imports", m["imports"], e["imports"]),
            ("gas TOTAL", mgas, e["gas"]),
            ("hydro(+PSdis)", mhyd, e["hydro"]),
            ("solar", m.get("k_SOLAR", np.zeros(8760)), e["solar"]),
            ("wind", m.get("k_WIND", np.zeros(8760)), e["wind"]),
            ("nuclear", m.get("k_NUCLEAR", np.zeros(8760)), e["nuclear"]),
            ("battery(net)", m["battery_net"], e["battery"]),
            ("demand", m["demand"], e["demand"]),
        ]
        print(f"{'source':<16}{'MODEL TWh':>10}{'MEAS TWh':>10}{'dMW avg':>9}")
        for lbl, mv, ev in rows:
            print(
                f"{lbl:<16}{mv[ok].sum() / 1e6:>10.2f}{ev[ok].sum() / 1e6:>10.2f}"
                f"{(mv[ok] - ev[ok]).mean():>9.0f}"
            )
        for k in GAS_KLASSES:
            mv = m.get(f"k_{k}", np.zeros(8760))
            print(
                f"  {k:<14}{mv[ok].sum() / 1e6:>10.2f}{c[k][ok].sum() / 1e6:>10.2f}"
                f"{(mv[ok] - c[k][ok]).mean():>9.0f}   (MEAS=CEMS)"
            )

        # 2. per-hod resid + deltas
        print("hod:  resid | d_imp d_gas d_batnet d_hyd  (model-meas avg MW)")
        for h in EVENING:
            hm = ok & (np.arange(8760) % 24 == h)
            print(
                f"  {h:2d}: {np.average(resid[hm], weights=m['demand'][hm]):+6.1f} |"
                f" {(m['imports'] - e['imports'])[hm].mean():6.0f}"
                f" {(mgas - e['gas'])[hm].mean():6.0f}"
                f" {(m['battery_net'] - e['battery'])[hm].mean():6.0f}"
                f" {(mhyd - e['hydro'])[hm].mean():6.0f}"
            )

        # 3. residual-quartile conditioning
        q = np.nanquantile(resid[ok], [0.25, 0.5, 0.75])
        print("resid-quartile conditioning (evening hours; Q1=deepest under-price):")
        print(
            "  bucket   n  resid | d_imp d_gas d_batnet d_hyd d_solar | "
            "CT m|c   CC m|c  (avg MW)"
        )
        edges = [-np.inf, *q, np.inf]
        for i in range(4):
            b = ok & (resid >= edges[i]) & (resid < edges[i + 1])
            ct_m = m.get("k_CT_PEAKER", np.zeros(8760))
            cc_m = m.get("k_CC_REGULAR", np.zeros(8760))
            print(
                f"  Q{i + 1:d} {b.sum():6d} {np.average(resid[b], weights=m['demand'][b]):+6.1f} |"
                f" {(m['imports'] - e['imports'])[b].mean():6.0f}"
                f" {(mgas - e['gas'])[b].mean():6.0f}"
                f" {(m['battery_net'] - e['battery'])[b].mean():6.0f}"
                f" {(mhyd - e['hydro'])[b].mean():6.0f}"
                f" {(m.get('k_SOLAR', np.zeros(8760)) - e['solar'])[b].mean():7.0f} |"
                f" {ct_m[b].mean():5.0f}|{c['CT_PEAKER'][b].mean():5.0f}"
                f" {cc_m[b].mean():5.0f}|{c['CC_REGULAR'][b].mean():5.0f}"
            )

        # 4. monthly evening resid
        mo = MONTH_OF_HOUR
        vals = []
        for mm in range(1, 13):
            b = ok & (mo == mm)
            vals.append(
                np.average(resid[b], weights=m["demand"][b]) if b.any() else np.nan
            )
        print("monthly evening resid: " + " ".join(f"{v:+5.1f}" for v in vals))
    return 0


if __name__ == "__main__":
    sys.exit(main())
