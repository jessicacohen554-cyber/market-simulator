"""pjm-161 Phase-1: score the pre-registered A/B of the measured-outage event cap.

Scores P3-P6 of PREREG-pjm161-measured-outage-event-cap-2026-08-14.md §4 from
the two solved bundles (P1/P2 were scored ex ante and on the fleet path):

  P3 prices rise      — load-weighted mean dual, and hourly MAE vs actual RT
  P4 the tail fills   — hours above $200 on the max zonal dual
  P5 CC_REGULAR falls — Δ class TWh, arm − control
  P6 the inversion narrows — corr(model unavailable MW, net load), which needs
                        the availability array and so rebuilds each arm's fleet
                        (``fleet_only=True``: no LP, exits before the matrix
                        builder). Skipped with ``--no-p6``.

Run:  PYTHONPATH=. uv run python scripts/probes/_pjm161_ab.py [--no-p6]
"""

from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

CTL = REPO / "results/calibration/pjm161_ctl_A"
ARM = REPO / "results/calibration/pjm161_evcap_B"
KEEPER = REPO / "results/calibration/pjm152_collapse_A"
BENCH = REPO / "frontend/data/backcast/bench/PJM"
CANON = REPO / "data/raw/_validation-source/actual_lmp_hourly_PJM.parquet"
E930 = REPO / "data/raw/eia-930-hourly/PJM hourly.parquet"
YEARS = (2023, 2024, 2025)


def cls_twh(bundle: Path, year: int) -> pd.Series:
    d = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    return d[d["pass"] == "P1"].groupby("klass")["mw"].sum().div(1e6)


def sysframe(bundle: Path, year: int) -> pd.DataFrame:
    d = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return d[(d["pass"] == "P1") & (d["zone"] != "PJM_external")]


def price_stats(bundle: Path, year: int) -> dict:
    sy = sysframe(bundle, year)
    price = sy.pivot_table(index="hour", columns="zone", values="price")
    dem = sy.pivot_table(index="hour", columns="zone", values="demand")
    lw = ((price * dem).sum(axis=1) / dem.sum(axis=1)).reindex(range(8760))
    mx = price.max(axis=1).reindex(range(8760))
    a = pd.read_parquet(CANON)
    a = a[a["year"] == year].set_index("hour")["rt"].reindex(range(8760)).ffill().bfill()
    return {
        "mean_lw": float(lw.mean()),
        "mae_vs_rt": float((lw - a).abs().mean()),
        "hours_gt200": int((mx > 200).sum()),
        "hours_gt500": int((mx > 500).sum()),
        "max": float(mx.max()),
        "actual_rt_mean": float(a.mean()),
        "actual_hours_gt200": int((a > 200).sum()),
    }


def actual_cls(year: int) -> dict:
    import gzip

    with gzip.open(BENCH / f"{year}.json.gz") as fh:
        return json.load(fh)["bench"]["classFull"]


def _kwargs():
    from scripts.replay_keeper import build_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((KEEPER / "meta.json").read_text())
    sk = build_kwargs(meta)
    params = set(inspect.signature(run_year).parameters)
    rename = {"commitment": "commitment_enabled", "screen_coal": "commitment_screen_coal"}
    skip = {"year", "iso", "hours", "gas_price", "ttc_overrides", "fleet_only"}
    kw = {
        rename.get(k, k): v
        for k, v in sk.items()
        if rename.get(k, k) in params and rename.get(k, k) not in skip
    }
    return meta, kw


def p6_inversion() -> dict:
    """corr(model unavailable MW, net load) for both arms — needs a fleet build."""
    from market_sim.data.pjm_outages import PJM_OUTAGE_COVERED_GROUPS
    from scripts.run_calibration import run_year

    meta, base_kw = _kwargs()
    e = pd.read_parquet(E930)
    out: dict = {}
    for year in YEARS:
        gas = float(meta["gas_prices"].get(str(year), 0.0))
        ey = e[pd.to_datetime(e["Local date"]).dt.year == year]
        nl = (
            pd.to_numeric(ey["Demand"], errors="coerce").to_numpy()
            - pd.to_numeric(ey["NG: WND"], errors="coerce").fillna(0).to_numpy()
            - pd.to_numeric(ey["NG: SUN"], errors="coerce").fillna(0).to_numpy()
        )
        # 930's local-clock year can be 8759/8761 rows (DST); the LP is fixed at
        # 8760, so pad/truncate to the model clock before comparing.
        nl = np.pad(nl[:8760], (0, max(0, 8760 - len(nl))), mode="edge")
        row: dict = {}
        for arm in ("control", "arm"):
            kw = dict(base_kw)
            if arm == "arm":
                prb = dict(kw.get("prb_overrides") or {})
                prb["pjm_measured_outage_event_cap"] = True
                kw["prb_overrides"] = prb
            st = run_year(year, "PJM", 8760, gas, {}, fleet_only=True, **kw)
            fa = st["fleet_arrays"]
            grp = np.array([str(g) for g in fa.plant_group])
            cov = np.isin(grp, sorted(PJM_OUTAGE_COVERED_GROUPS))
            cap = np.asarray(fa.pmax, dtype=float)[cov]
            av = np.asarray(fa.availability, dtype=float)[cov][:, :8760]
            unavail = (cap[:, None] * (1.0 - av)).sum(axis=0)
            ok = np.isfinite(nl) & np.isfinite(unavail)
            q = pd.Series(nl[ok]).rank(pct=True).to_numpy()
            row[arm] = {
                "corr": float(np.corrcoef(unavail[ok], nl[ok])[0, 1]),
                "mean_unavail_MW": float(unavail[ok].mean()),
                "top1pct_unavail_MW": float(unavail[ok][q >= 0.99].mean()),
                "ratio_top1_over_mean": float(
                    unavail[ok][q >= 0.99].mean() / unavail[ok].mean()
                ),
            }
        out[year] = row
    return out


def main() -> None:
    pd.set_option("display.width", 200)
    no_p6 = "--no-p6" in sys.argv
    res: dict = {"class_twh": {}, "prices": {}}

    print("=" * 96)
    print("P5 — Δ class TWh (arm − control), and the error against EIA-923 classFull")
    print("=" * 96)
    for year in YEARS:
        c, a = cls_twh(CTL, year), cls_twh(ARM, year)
        act = actual_cls(year)
        keys = sorted(set(c.index) | set(a.index))
        rows = []
        for k in keys:
            cv, av = float(c.get(k, 0.0)), float(a.get(k, 0.0))
            ak = act.get(k)
            rows.append(
                dict(
                    klass=k,
                    control=round(cv, 3),
                    arm=round(av, 3),
                    delta=round(av - cv, 3),
                    actual=(round(ak, 3) if ak is not None else None),
                    err_ctl=(round(cv - ak, 3) if ak is not None else None),
                    err_arm=(round(av - ak, 3) if ak is not None else None),
                )
            )
        t = pd.DataFrame(rows).set_index("klass")
        big = t[t[["control", "arm"]].abs().max(axis=1) > 1.0]
        print(f"\n--- {year} (classes > 1 TWh) ---")
        print(big.to_string())
        res["class_twh"][year] = rows

    print()
    print("=" * 96)
    print("P3 / P4 — prices and the tail")
    print("=" * 96)
    pr = []
    for year in YEARS:
        pc, pa = price_stats(CTL, year), price_stats(ARM, year)
        pr.append(
            dict(
                year=year,
                mean_ctl=round(pc["mean_lw"], 2),
                mean_arm=round(pa["mean_lw"], 2),
                d_mean=round(pa["mean_lw"] - pc["mean_lw"], 2),
                actual_rt=round(pc["actual_rt_mean"], 2),
                mae_ctl=round(pc["mae_vs_rt"], 2),
                mae_arm=round(pa["mae_vs_rt"], 2),
                d_mae=round(pa["mae_vs_rt"] - pc["mae_vs_rt"], 2),
                h200_ctl=pc["hours_gt200"],
                h200_arm=pa["hours_gt200"],
                h200_actual=pc["actual_hours_gt200"],
                max_ctl=round(pc["max"], 0),
                max_arm=round(pa["max"], 0),
            )
        )
        res["prices"][year] = {"control": pc, "arm": pa}
    print(pd.DataFrame(pr).set_index("year").T.to_string())

    if not no_p6:
        print()
        print("=" * 96)
        print("P6 — does the envelope's scarcity inversion narrow? (fleet build, no LP)")
        print("=" * 96)
        p6 = p6_inversion()
        res["p6"] = p6
        rows = []
        for y, r in p6.items():
            rows.append(
                dict(
                    year=y,
                    corr_ctl=round(r["control"]["corr"], 3),
                    corr_arm=round(r["arm"]["corr"], 3),
                    d_corr=round(r["arm"]["corr"] - r["control"]["corr"], 3),
                    top1_ratio_ctl=round(r["control"]["ratio_top1_over_mean"], 3),
                    top1_ratio_arm=round(r["arm"]["ratio_top1_over_mean"], 3),
                    top1_MW_ctl=round(r["control"]["top1pct_unavail_MW"], 0),
                    top1_MW_arm=round(r["arm"]["top1pct_unavail_MW"], 0),
                )
            )
        print(pd.DataFrame(rows).set_index("year").T.to_string())

    dest = REPO / "results/calibration/_pjm161_ab.json"
    dest.write_text(json.dumps(res, indent=1, default=float) + "\n")
    print(f"\nwrote {dest.relative_to(REPO)}")


if __name__ == "__main__":
    main()
