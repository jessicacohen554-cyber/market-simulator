"""R-CAISO-9 Object 2 (ZERO LP): C4 2025 margin decomposition + the 2021 DSW evening gap.

(a) C4 2025. Rebuilds the scorer's CEMS-basis gas series
(``calibration_verdict._cems_gas_hourly_fit``, same arithmetic) for the keeper
``2026-09-27-caiso-r8-partial-year`` and splits the NRMSE by hour of day, month
and class; then splits the midday (h9-16) CC_REGULAR deficit per plant into
"CEMS on, model off" vs "both on, model loaded lower".

(b) 2021 DSW. Reads the R-CAISO-8 2021 leg's per-unit hourly
(``results/calibration/rcaiso8_A_2021``, extracted from shard commit
``2b93619a3dc242ec09dfb06800d54ccd1011154f`` with ``git archive``; gitignored,
provenance only) against EIA-930 corridor net import, split by the PALOVRDE
hub's printed / unprinted hours and by hour-of-day window; and compares the
model's SP15_rest price with the measured OASIS DAM TH_SP15 / PALOVRDE LMPs in
the printed hours.

Writes ``results/calibration/_rcaiso9/object2_census.json``.

Usage::

    PYTHONPATH=.:src:scripts python3 scripts/probes/_rcaiso9_object2_census.py
"""

from __future__ import annotations

import base64
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path[:0] = [".", "src", "scripts", "scripts/probes"]
import calibration_verdict as cv  # noqa: E402
from scripts.data.derive_caiso_import_tranches import corridor_net_import  # noqa: E402

KEEPER = "2026-09-27-caiso-r8-partial-year"
LEG_2021 = Path("results/calibration/rcaiso8_A_2021")
HUBS = Path("data/raw/_validation-source/wecc_intertie_lmp_hourly_CAISO.parquet")
DAM_2021 = Path("data/raw/lmp-data/CAISO/CAISO_dam_hourly_2021.csv")
OUT = Path("results/calibration/_rcaiso9/object2_census.json")
T = 8760
HOD = np.arange(T) % 24


def _cf(b64: str, cap: float) -> np.ndarray:
    return np.frombuffer(base64.b64decode(b64)[:T], np.uint8) * cap / 100.0


def c4_2025() -> dict:
    """Decompose the keeper's 2025 C4 gas NRMSE."""
    art = cv.load_artifacts(KEEPER)
    pay = art["payload"]
    ypay = pay["years"]["2025"] if "years" in pay else pay["2025"]
    yb = art["bench"][2025]
    model, act, btm = np.zeros(T), np.zeros(T), 0.0
    by_class: dict[str, np.ndarray] = {}
    cc_mid = {"model_off_mw": 0.0, "both_on_under_mw": 0.0, "model_over_mw": 0.0}
    mid = (HOD >= 9) & (HOD <= 16)
    for code, bp in yb["plants"].items():
        if bp.get("group") not in cv.GAS_CLASSES or bp.get("nodata"):
            continue
        cap = float(bp.get("npl") or 0.0)
        pp = ypay["plants"].get(str(code))
        if cap <= 0 or not bp.get("campd") or not pp or not pp.get("m"):
            continue
        a, m = _cf(bp["campd"], cap), _cf(pp["m"], cap)
        act += a
        model += m
        btm += float(bp.get("btm") or 0.0)
        g = bp["group"]
        by_class[g] = by_class.get(g, np.zeros(T)) + (m - a)
        if g == "CC_REGULAR":
            on_a, on_m = a > 0.5, m > 0.5
            cc_mid["model_off_mw"] += float(np.where(mid & on_a & ~on_m, -a, 0).sum())
            cc_mid["both_on_under_mw"] += float(
                np.where(mid & on_a & on_m, np.minimum(m - a, 0), 0).sum()
            )
            cc_mid["model_over_mw"] += float(np.where(mid & (m > a), m - a, 0).sum())
    cc_mid = {k: round(v / mid.sum()) for k, v in cc_mid.items()}
    rows = {r["fuel"]: r for r in ypay["fuelRows"]}
    cogen = yb["e930"]["gas_cogen_grid"]
    bm = btm * 1e6 / T
    act = act - bm + cogen * 1e6 / T
    fill = (rows["gas"]["m"] - (model.sum() / 1e6 - btm)) * 1e6 / T
    model = model - bm + fill
    d = model - act
    om = act.mean()
    sse = (d**2).sum()
    prof = np.array([d[HOD == h].mean() for h in range(24)])
    return {
        "nrmse": round(math.sqrt((d**2).mean()) / om, 4),
        "r": round(float(np.corrcoef(model, act)[0, 1]), 3),
        "hod_bias_mw": [round(float(x)) for x in prof],
        "hod_sse_share": [
            round(float((d[HOD == h] ** 2).sum() / sse), 3) for h in range(24)
        ],
        "nrmse_without_diurnal_mean_bias": round(
            math.sqrt(((d - prof[HOD]) ** 2).mean()) / om, 4
        ),
        "class_dev_mw": {
            g: {
                "mean": round(float(v.mean())),
                "h9_16": round(float(v[mid].mean())),
                "h17_22": round(float(v[(HOD >= 17) & (HOD <= 22)].mean())),
            }
            for g, v in by_class.items()
        },
        "cc_regular_midday_split_mw": cc_mid,
    }


def dsw_2021() -> dict:
    """Split the 2021 DSW import gap by hub-printed hours and hour-of-day."""
    u = pd.read_parquet(
        LEG_2021 / "hourly/unit_hourly_2021.parquet",
        filters=[("zone", "==", "WECC_DSW")],
    )
    m = u.groupby("hour").mw.sum().reindex(range(T)).fillna(0).to_numpy()
    a = (
        corridor_net_import(years=(2021,))
        .loc[2021]["WECC_DSW"]
        .reindex(range(T))
        .to_numpy()
    )
    hubs = pd.read_parquet(HUBS)
    pv = (
        hubs[(hubs.year == 2021) & (hubs.hub == "PALOVRDE")]
        .set_index("hour")
        .price.reindex(range(T))
        .to_numpy()
    )
    printed = ~np.isnan(pv)
    ev = (HOD >= 17) & (HOD <= 22)
    out: dict = {"printed_hours": int(printed.sum()), "gap": {}}
    for nm, msk in (
        ("all", np.ones(T, bool)),
        ("printed", printed),
        ("unprinted", ~printed),
    ):
        for wn, w in (("all", np.ones(T, bool)), ("h17_22", ev)):
            k = msk & w
            out["gap"][f"{nm}_{wn}"] = {
                "hours": int(k.sum()),
                "model_mw": round(float(m[k].mean())),
                "eia930_mw": round(float(np.nanmean(a[k]))),
                "gap_twh": round(float(np.nansum((m - a)[k]) / 1e6), 2),
            }
    dam = pd.read_csv(DAM_2021)
    t = pd.to_datetime(dam.interval_start_gmt).dt.tz_convert("Etc/GMT+8")
    dam["hr"] = (
        (t - pd.Timestamp("2021-01-01", tz="Etc/GMT+8")).dt.total_seconds() // 3600
    ).astype(int)
    p = dam.pivot_table(index="hr", columns="node", values="LMP").reindex(range(T))
    sysp = pd.read_parquet(LEG_2021 / "hourly/system_2021.parquet").pivot(
        index="hour", columns="zone", values="price"
    )
    out["price_printed_hours"] = {}
    for wn, w in (
        ("h17_22", ev),
        ("h8_16", (HOD >= 8) & (HOD <= 16)),
        ("h0_6", HOD <= 6),
    ):
        k = w & printed & ~p["TH_SP15_GEN-APND"].isna().to_numpy()
        out["price_printed_hours"][wn] = {
            "hours": int(k.sum()),
            "model_sp15_rest": round(float(sysp["SP15_rest"].to_numpy()[k].mean()), 1),
            "measured_dam_th_sp15": round(
                float(p["TH_SP15_GEN-APND"].to_numpy()[k].mean()), 1
            ),
            "measured_dam_palovrde": round(
                float(p["PALOVRDE_ASR-APND"].to_numpy()[k].mean()), 1
            ),
            "hub_input_palovrde": round(float(pv[k].mean()), 1),
        }
    return out


def main() -> None:
    """Run both censuses and write the JSON."""
    res = {"c4_2025": c4_2025(), "dsw_2021": dsw_2021()}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
