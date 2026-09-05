#!/usr/bin/env python3
"""nyiso-189: the B2 arm vs the same-HEAD control, at full magnitude (no scorer).

Reads the two local bundles' P1 hourlies (``system_<y>``, ``class_hourly_<y>``,
``unit_hourly_<y>``) and writes ``results/calibration/_nyiso189_ab_report.json``:
per year the class energies, the load-weighted system and Capital-Hudson
prices, Bethlehem 2539's and World Generation X 54131's energy / available
energy / mean installed mc, the price hours differing and their max |Δ|, and
the ten largest per-plant annual energy movers. The criteria themselves come
from ``scripts/calibration_verdict.py`` on the registered bundle (committed
artifacts only) and are compared by ``scripts/probes/nyiso188_verdict_compare.py``.

Usage:
    python scripts/probes/nyiso189_ab_report.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
CAL = REPO / "results" / "calibration"
CONTROL = CAL / "nyiso189_control"
ARM = CAL / "nyiso189_steam_identity"
OUT = CAL / "_nyiso189_ab_report.json"
YEARS = (2023, 2024, 2025)
BETHLEHEM, WORLD_GEN_X = 2539, 54131
CAPITAL = "Capital_Hudson"


def _sys(b: Path, y: int) -> pd.DataFrame:
    df = pd.read_parquet(b / "hourly" / f"system_{y}.parquet")
    return df[df["pass"] == "P1"].sort_values(["zone", "hour"]).reset_index(drop=True)


def _cls(b: Path, y: int) -> dict[str, float]:
    df = pd.read_parquet(b / "hourly" / f"class_hourly_{y}.parquet")
    df = df[df["pass"] == "P1"]
    return {k: round(v / 1e6, 4) for k, v in df.groupby("klass").mw.sum().items()}


def _unit(b: Path, y: int) -> pd.DataFrame:
    df = pd.read_parquet(
        b / "hourly" / f"unit_hourly_{y}.parquet",
        columns=["pass", "plant_code", "hour", "mw", "cap_mw", "mc"],
    )
    return df[df["pass"] == "P1"]


def _lw(s: pd.DataFrame, zone: str | None = None) -> float:
    if zone is not None:
        s = s[s.zone == zone]
    return round(float((s.price * s.demand).sum() / s.demand.sum()), 3)


def _plant(u: pd.DataFrame, p: int) -> dict:
    x = u[u.plant_code == p]
    twh, avail = float(x.mw.sum() / 1e6), float(x.cap_mw.sum() / 1e6)
    return {
        "twh": round(twh, 4),
        "available_twh": round(avail, 4),
        "loading_of_available": round(twh / avail, 4) if avail > 0 else None,
        "mean_mc": round(float(x.mc.mean()), 3),
        "max_hourly_mw": round(float(x.groupby("hour").mw.sum().max()), 1),
    }


def main() -> None:
    report: dict = {"control": CONTROL.name, "arm": ARM.name, "by_year": {}}
    for y in YEARS:
        sc, sa = _sys(CONTROL, y), _sys(ARM, y)
        cc, ca = _cls(CONTROL, y), _cls(ARM, y)
        uc, ua = _unit(CONTROL, y), _unit(ARM, y)
        dprice = sa.price.values - sc.price.values
        pc = uc.groupby("plant_code").mw.sum() / 1e6
        pa = ua.groupby("plant_code").mw.sum() / 1e6
        dp = (pa - pc).dropna().sort_values()
        movers = pd.concat([dp.head(5), dp.tail(5)])
        report["by_year"][y] = {
            "class_twh": {k: [cc.get(k, 0.0), ca.get(k, 0.0)] for k in sorted(set(cc) | set(ca))},
            "load_weighted_price": [_lw(sc), _lw(sa)],
            "capital_hudson_lw_price": [_lw(sc, CAPITAL), _lw(sa, CAPITAL)],
            "zonal_lw_price": {
                z: [_lw(sc, z), _lw(sa, z)] for z in sorted(sc.zone.unique())
            },
            "price_hours_differing": int((abs(dprice) > 1e-9).sum()),
            "of_hours": int(len(dprice)),
            "max_abs_dprice": round(float(abs(dprice).max()), 3),
            "hours_gt_300": [int((sc.price > 300).sum()), int((sa.price > 300).sum())],
            "bethlehem": {"control": _plant(uc, BETHLEHEM), "arm": _plant(ua, BETHLEHEM)},
            "world_gen_x": {
                "control": _plant(uc, WORLD_GEN_X),
                "arm": _plant(ua, WORLD_GEN_X),
            },
            "plant_movers_twh": {int(k): round(float(v), 4) for k, v in movers.items()},
        }
    OUT.write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps(report, indent=1))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
