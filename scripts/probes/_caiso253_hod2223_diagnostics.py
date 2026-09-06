"""caiso-253 POST-REGISTRATION diagnostics on the hod 22-23 gap (ZERO LP).

**Labelled post-registration and scored NOWHERE.** The four registered gates
live in ``_caiso253_hod2223_gates.py``; this probe characterises the block the
charter closed, so the next session inherits measurements rather than a null.

(a) **Would an at-hub row even CLEAR at 22-23?** The model's own P1 duals at
    22-23 against the raw Palo Verde hub the row would price at. A row priced
    at the hub clears only where the CA-side dual exceeds it — the same test
    ``_caiso252_evening_trim_phase0.py`` applied at 18-21.
(b) **Who serves 22-23** — model class dispatch vs EIA-930 CISO by fuel.
(c) **Seasonality** of the raw-hub discriminator at 22-23 (is 2023's failure
    concentrated in the gas-spike months?).
(d) The keeper's **storage** net at 22-23 — caiso-252's P-A2 falsification put
    evening storage discharge in the displacement path.
(e) **The diurnal SHAPE of each price series**, normalised to its own annual
    mean — the mechanism behind the raw-hub discriminator's sign at 22-23.
(f) The raw-hub discriminator against **MALIN** as well as PALOVRDE — is the
    north corridor the alternative carrier? (caiso-88 closed its depth.)

Output: ``results/calibration/_caiso253_hod2223_diagnostics.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

BUNDLE = REPO / "results/calibration/caiso252_b1_notrim"
E930 = REPO / "data/raw/eia-930-hourly/CISO hourly.parquet"
YEARS = (2023, 2024, 2025)
T = 8760
HOD = np.arange(T) % 24
GAP = (22, 23)
OVN = (0, 1, 2, 3, 4, 5)
_MDAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
MONTH = np.repeat(np.arange(1, 13), np.array(_MDAYS) * 24)
OUT = REPO / "results/calibration/_caiso253_hod2223_diagnostics.json"


def _model_hour(ts: pd.Series, year: int) -> np.ndarray:
    dt = pd.DatetimeIndex(ts)
    doy = dt.dayofyear.to_numpy()
    if year % 4 == 0:
        doy = np.where(dt.month.to_numpy() > 2, doy - 1, doy)
    return (doy - 1) * 24 + dt.hour.to_numpy()


def _m930(year: int) -> dict[str, np.ndarray]:
    d = pd.read_parquet(E930)
    lt = pd.to_datetime(d["Local time"]) - pd.Timedelta(hours=1)
    d = d.assign(lt=lt)
    d = d[
        (d["lt"].dt.year == year) & ~((d["lt"].dt.month == 2) & (d["lt"].dt.day == 29))
    ]
    h = _model_hour(d["lt"], year)
    out = {}
    for col, name in [
        ("Demand", "demand"),
        ("Total interchange", "ti"),
        ("NG: NG", "gas"),
        ("NG: SUN", "solar"),
        ("NG: WND", "wind"),
        ("NG: WAT", "hydro"),
        ("NG: NUC", "nuclear"),
        ("NG: OTH", "oth"),
        ("NG: GEO", "geo"),
    ]:
        a = np.full(T, np.nan)
        a[h] = d[col].to_numpy(float)
        out[name] = a
    return out


def _blk(x, hods):
    return float(np.nanmean(x[np.isin(HOD, hods)]))


def main() -> None:
    from market_sim.data.eia930.envelopes import measured_intertie_hub_price_raw

    lmp = pd.read_parquet(
        REPO / "data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet"
    )
    res: dict = {"note": "POST-REGISTRATION, labelled, scored nowhere", "years": {}}
    for y in YEARS:
        pv = measured_intertie_hub_price_raw("CAISO", y, T, "PALOVRDE")
        meas = np.isfinite(pv)
        sysf = pd.read_parquet(BUNDLE / f"hourly/system_{y}.parquet")
        sysf = sysf[sysf["pass"] == "P1"]
        lam = {
            z: g.set_index("hour")["price"].reindex(range(T)).to_numpy(float)
            for z, g in sysf.groupby("zone")
        }
        dem = {
            z: g.set_index("hour")["demand"].reindex(range(T)).to_numpy(float)
            for z, g in sysf.groupby("zone")
        }
        tot = sum(dem.values())
        lam_lw = sum(lam[z] * dem[z] for z in lam) / tot

        # (a) would an at-hub row clear at 22-23?
        clear = {}
        for label, series in (
            ("load_weighted", lam_lw),
            *((z, lam[z]) for z in sorted(lam)),
        ):
            for name, hods in (
                ("gap_22_23", GAP),
                ("ovn_0_5", OVN),
                ("eve_18_21", (18, 19, 20, 21)),
            ):
                m = np.isin(HOD, hods) & meas
                clear[f"{label}|{name}"] = {
                    "lambda_mean": round(float(np.nanmean(series[m])), 2),
                    "hub_mean": round(float(np.nanmean(pv[m])), 2),
                    "lambda_minus_hub_mean": round(
                        float(np.nanmean(series[m] - pv[m])), 2
                    ),
                    "share_lambda_above_hub": round(
                        float(np.nanmean(series[m] > pv[m])), 4
                    ),
                }
        # (b) who serves 22-23
        ch = pd.read_parquet(BUNDLE / f"hourly/class_hourly_{y}.parquet")
        ch = ch[ch["pass"] == "P1"]
        cls = {
            k: g.set_index("hour")["mw"].reindex(range(T)).to_numpy(float)
            for k, g in ch.groupby("klass")
        }
        m9 = _m930(y)
        model_gas = sum(
            cls.get(k, np.zeros(T))
            for k in ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS")
        )
        serve = {
            "model": {k: round(_blk(v, GAP), 1) for k, v in sorted(cls.items())},
            "model_gas_total": round(_blk(model_gas, GAP), 1),
            "e930": {k: round(_blk(v, GAP), 1) for k, v in m9.items() if k != "ti"},
            "e930_net_import": round(_blk(-m9["ti"], GAP), 1),
        }
        # (c) seasonality of the raw-hub discriminator at 22-23
        seas = {}
        for basis in ("da", "rt"):
            a = pd.to_numeric(
                lmp[lmp["year"] == y].sort_values("hour")[basis], errors="coerce"
            ).to_numpy(float)[:T]
            sp = a - pv
            seas[basis] = {
                "by_month_median": [
                    round(
                        float(
                            np.nanmedian(sp[(MONTH == mo) & np.isin(HOD, GAP) & meas])
                        ),
                        2,
                    )
                    if ((MONTH == mo) & np.isin(HOD, GAP) & meas).any()
                    else None
                    for mo in range(1, 13)
                ],
                "gap_median": round(
                    float(np.nanmedian(sp[np.isin(HOD, GAP) & meas])), 2
                ),
                "ovn_median": round(
                    float(np.nanmedian(sp[np.isin(HOD, OVN) & meas])), 2
                ),
            }
        # (d) storage
        st = pd.read_parquet(BUNDLE / f"hourly/storage_{y}.parquet")
        st = st[st["pass"] == "P1"]
        agg = st.groupby("hour")[
            [c for c in ("charge_mw", "discharge_mw") if c in st.columns]
        ].sum()
        stor = {}
        if not agg.empty:
            for c in agg.columns:
                a = agg[c].reindex(range(T)).to_numpy(float)
                stor[c] = {
                    "by_hod": [
                        round(float(np.nanmean(a[HOD == h])), 1) for h in range(24)
                    ]
                }
        # (e) diurnal SHAPE, each series normalised to its own annual mean
        ml = measured_intertie_hub_price_raw("CAISO", y, T, "MALIN")
        da_full = pd.to_numeric(
            lmp[lmp["year"] == y].sort_values("hour")["da"], errors="coerce"
        ).to_numpy(float)[:T]
        rt_full = pd.to_numeric(
            lmp[lmp["year"] == y].sort_values("hour")["rt"], errors="coerce"
        ).to_numpy(float)[:T]
        shape = {}
        for name, ser in (("caiso_da", da_full), ("palovrde", pv), ("malin", ml)):
            if ser is None:
                continue
            mk = meas & np.isfinite(ser)
            lv = float(np.nanmean(ser[mk]))
            shape[name] = {
                "level": round(lv, 2),
                "by_hod_over_own_mean": [
                    round(float(np.nanmean(ser[(HOD == h) & mk]) / lv), 3)
                    for h in range(24)
                ],
            }
        # (f) raw-hub discriminator against MALIN as well as PALOVRDE
        malin = {}
        for basis, a in (("DA", da_full), ("RT", rt_full)):
            malin[basis] = {}
            for lab, hods in (
                ("gap_22_23", GAP),
                ("ovn_0_5", OVN),
                ("eve_18_21", (18, 19, 20, 21)),
            ):
                mm = np.isin(HOD, hods) & np.isfinite(a)
                row = {
                    "vs_PALOVRDE": round(
                        float(np.nanmedian((a - pv)[mm & np.isfinite(pv)])), 2
                    )
                }
                if ml is not None:
                    row["vs_MALIN"] = round(
                        float(np.nanmedian((a - ml)[mm & np.isfinite(ml)])), 2
                    )
                malin[basis][lab] = row
        res["years"][y] = {
            "a_would_it_clear": clear,
            "b_who_serves": serve,
            "c_seasonality": seas,
            "d_storage": stor,
            "e_diurnal_shape": shape,
            "f_malin_vs_palovrde": malin,
            "storage_columns": list(st.columns),
        }
        print(f"\n===== {y} =====")
        for k in (
            "load_weighted|gap_22_23",
            "load_weighted|ovn_0_5",
            "load_weighted|eve_18_21",
            "SP15_rest|gap_22_23",
            "NP15|gap_22_23",
        ):
            if k in clear:
                c = clear[k]
                print(
                    f"  (a) {k:28s} lambda {c['lambda_mean']:7.2f} hub {c['hub_mean']:7.2f} "
                    f"diff {c['lambda_minus_hub_mean']:+7.2f} | share lambda>hub {c['share_lambda_above_hub']:.3f}"
                )
        print(
            f"  (b) 22-23 model gas {serve['model_gas_total']:.0f} vs 930 gas {serve['e930']['gas']:.0f} | "
            f"model import {serve['model'].get('import', 0):.0f} vs 930 net import {serve['e930_net_import']:.0f} | "
            f"model hydro {serve['model'].get('hydro', 0):.0f} vs 930 {serve['e930']['hydro']:.0f} | "
            f"930 oth {serve['e930']['oth']:.0f}"
        )
        for basis in ("da", "rt"):
            print(
                f"  (c) {basis.upper()} raw-hub 22-23 by month:",
                seas[basis]["by_month_median"],
                f"| gap {seas[basis]['gap_median']:+.2f} vs ovn {seas[basis]['ovn_median']:+.2f}",
            )
        for c, v in stor.items():
            print(f"  (d) {c} by hod:", [round(x) for x in v["by_hod"]])
        for name, sh in shape.items():
            b = sh["by_hod_over_own_mean"]
            print(
                f"  (e) {name:9s} lvl {sh['level']:6.2f} | hod22 {b[22]:.3f} hod23 {b[23]:.3f} "
                f"| hod00 {b[0]:.3f} hod04 {b[4]:.3f} hod05 {b[5]:.3f}"
            )
        for basis in ("DA", "RT"):
            g = malin[basis]["gap_22_23"]
            print(
                f"  (f) {basis} 22-23 raw-hub: vs PV {g['vs_PALOVRDE']:+.2f} "
                f"| vs MALIN {g.get('vs_MALIN', float('nan')):+.2f}"
            )
    OUT.write_text(json.dumps(res, indent=1, default=float) + "\n")


if __name__ == "__main__":
    main()
