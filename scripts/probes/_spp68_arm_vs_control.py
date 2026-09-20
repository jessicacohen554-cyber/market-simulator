"""SPP-68: difference each solved CEILING-ARM year against its COMMITTED control.

Rule 29(b) form 4 — the control is keeper 14's own committed bundle, never a
control solve. The G-DRIFT audit validating form 4 for this lane is
``docs/handoffs/PRECOMMIT-spp-68-curtailment-ceiling-retest-2026-09-20.md`` §6.

Scores every limb of the PRE-REGISTERED prediction and kill condition in that
document (§4, §5) against what actually solved, and says plainly which
predictions were wrong.

Run: ``PYTHONPATH=src uv run python scripts/probes/_spp68_arm_vs_control.py [year ...]``
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "probes"))
CAL = ROOT / "results" / "calibration"

YEARS = (2019, 2020, 2021, 2022, 2023, 2024, 2025)
CONTROL = {y: "spp67_yearown_rung" for y in (2019, 2020, 2021, 2022)}
CONTROL.update({y: "spp67_yearown_span" for y in (2023, 2024, 2025)})
ARM = "spp68_ceiling_{y}"

#: PRECOMMIT §4 P-1, the point prediction for the arm's wind TWh, and the bench.
PRED_WIND = {
    2019: 70.6223,
    2020: 81.7418,
    2021: 92.6605,
    2022: 107.1168,
    2023: 101.8479,
    2024: 110.3313,
    2025: 110.5410,
}
BENCH = {
    2019: 77.0300,
    2020: 82.0300,
    2021: 92.8600,
    2022: 107.4400,
    2023: 103.0500,
    2024: 109.3200,
    2025: 110.4600,
}
TOL = {y: 0.25 for y in YEARS}
TOL[2019] = 0.50

#: PRECOMMIT §4 P-2 bands, as a fraction of |delta wind|.
PRED_SPLIT = {
    "COAL_PRB": (0.45, 0.70),
    "CC_REGULAR": (0.18, 0.42),
    "CT_PEAKER": (0.00, 0.20),
    "ST_GAS": (-0.12, 0.12),
}
CLASSES = (
    "wind",
    "COAL_PRB",
    "COAL_LIGNITE",
    "CC_REGULAR",
    "CT_PEAKER",
    "ST_GAS",
    "CC_CHP",
    "CT_CHP",
    "ST_CHP",
    "solar",
    "nuclear",
    "hydro",
)


def _twh(bundle: str, year: int) -> pd.Series:
    """Return P1 annual TWh by class."""
    f = pd.read_parquet(CAL / bundle / "hourly" / f"class_hourly_{year}.parquet")
    f = f[f["pass"] == "P1"]
    return f.groupby("klass")["mw"].sum() / 1e6


def _sys(bundle: str, year: int) -> dict:
    """Return load-weighted hourly price stats, slack and dump."""
    f = pd.read_parquet(CAL / bundle / "hourly" / f"system_{year}.parquet")
    f = f[f["pass"] == "P1"]
    dem = f.groupby("hour")["demand"].sum()
    hp = f.assign(w=f["price"] * f["demand"]).groupby("hour")["w"].sum() / dem
    return {
        "mean": float((f["price"] * f["demand"]).sum() / f["demand"].sum()),
        "neg": int((hp < 0).sum()),
        "deep": int((hp <= -25.9).sum()),
        "min": float(hp.min()),
        "slack": float(f["slack"].sum()),
        "dump": float(f["dump"].sum()),
    }


def main() -> int:
    """Difference every solved arm year against its committed control."""
    years = [int(a) for a in sys.argv[1:]] or [
        y for y in YEARS if (CAL / ARM.format(y=y)).is_dir()
    ]
    print("=" * 108)
    print(
        "SPP-68 — the CEILING arm vs KEEPER 14's COMMITTED bundle (rule 29(b) form 4)"
    )
    print(f"solved years present: {years}")
    print("=" * 108)

    print("\n## 1 — WIND: the pre-registered point prediction, scored")
    print(
        f"\n{'year':6s}{'bench':>10s}{'control':>10s}{'ARM':>10s}{'d wind':>10s}"
        f"{'excess now':>12s}{'excess ARM':>12s}{'PREDICTED':>11s}{'|miss|':>9s}"
        f"{'tol':>7s}  verdict"
    )
    dwind = {}
    for y in years:
        c = _twh(CONTROL[y], y)["wind"]
        a = _twh(ARM.format(y=y), y)["wind"]
        dwind[y] = a - c
        miss = abs(a - PRED_WIND[y])
        print(
            f"{y:<6d}{BENCH[y]:10.4f}{c:10.4f}{a:10.4f}{a - c:+10.4f}"
            f"{c - BENCH[y]:+12.4f}{a - BENCH[y]:+12.4f}{PRED_WIND[y]:11.4f}"
            f"{miss:9.4f}{TOL[y]:7.2f}  {'HIT' if miss <= TOL[y] else 'MISS'}"
        )

    print("\n## 2 — WHERE THE ENERGY WENT, against the pre-registered P-2 bands")
    print(
        f"\n{'year':6s}"
        + "".join(f"{c:>14s}" for c in CLASSES[1:6])
        + f"{'sum/|dW|':>10s}"
    )
    for y in years:
        c, a = _twh(CONTROL[y], y), _twh(ARM.format(y=y), y)
        d = {k: float(a.get(k, 0.0) - c.get(k, 0.0)) for k in CLASSES}
        tot = sum(v for k, v in d.items() if k != "wind")
        print(
            f"{y:<6d}"
            + "".join(f"{d[k]:+14.4f}" for k in CLASSES[1:6])
            + f"{tot / abs(dwind[y]):10.3f}"
        )
    print(f"\n   as a FRACTION of |d wind| — band from the PRECOMMIT §4 P-2:")
    print(f"{'year':6s}" + "".join(f"{c:>20s}" for c in PRED_SPLIT))
    for y in years:
        c, a = _twh(CONTROL[y], y), _twh(ARM.format(y=y), y)
        row = ""
        for k, (lo, hi) in PRED_SPLIT.items():
            frac = float(a.get(k, 0.0) - c.get(k, 0.0)) / abs(dwind[y])
            row += f"{frac:+.3f}{'  in' if lo <= frac <= hi else ' OUT':>6s}       "
        print(f"{y:<6d}{row}")

    print("\n## 3 — PRICE, and the kill condition's limbs K-3 / K-4")
    print(
        f"\n{'year':6s}{'ctl mean':>10s}{'ARM mean':>10s}{'d':>8s}"
        f"{'ctl h<=-25.9':>14s}{'ARM h<=-25.9':>14s}{'ratio':>8s}"
        f"{'ARM min $':>11s}{'ARM slack':>11s}{'ARM dump':>10s}"
    )
    for y in years:
        cs, as_ = _sys(CONTROL[y], y), _sys(ARM.format(y=y), y)
        ratio = as_["deep"] / cs["deep"] if cs["deep"] else float("nan")
        print(
            f"{y:<6d}{cs['mean']:10.3f}{as_['mean']:10.3f}{as_['mean'] - cs['mean']:+8.3f}"
            f"{cs['deep']:14d}{as_['deep']:14d}{ratio:8.3f}"
            f"{as_['min']:11.3f}{as_['slack']:11.4f}{as_['dump']:10.4f}"
        )

    print("\n## 4 — THE PRE-REGISTERED KILL CONDITION (PRECOMMIT §5), limb by limb")
    k1 = [(y, BENCH[y] - _twh(ARM.format(y=y), y)["wind"]) for y in years]
    k1t = [(y, d) for y, d in k1 if d > 2.00]
    print(
        f"\n   K-1 over-removal (arm wind > 2.00 TWh BELOW bench): "
        f"{'TRIPPED' if k1t else 'holds'}"
    )
    for y, d in k1:
        print(
            f"       {y}: {d:+.4f} TWh below bench{'   <-- TRIPS' if d > 2.00 else ''}"
        )
    k3t = []
    for y in years:
        cs, as_ = _sys(CONTROL[y], y), _sys(ARM.format(y=y), y)
        if cs["deep"] >= 100 and as_["deep"] < 0.5 * cs["deep"]:
            k3t.append((y, cs["deep"], as_["deep"]))
    print(
        f"\n   K-3 price floor (h<=-25.9 falls below 50 % where control >= 100): "
        f"{'TRIPPED' if k3t else 'holds'}"
    )
    for y, c_, a_ in k3t:
        print(f"       {y}: {c_} -> {a_}   <-- TRIPS")
    k4t = [
        (y, _sys(ARM.format(y=y), y)["slack"])
        for y in years
        if _sys(CONTROL[y], y)["slack"] == 0.0
        and _sys(ARM.format(y=y), y)["slack"] > 100.0
    ]
    print(
        f"\n   K-4 new forcing (slack > 100 MWh where control is 0): "
        f"{'TRIPPED' if k4t else 'holds'}"
    )
    for y, s in k4t:
        print(f"       {y}: {s:.4f} MWh   <-- TRIPS")
    print(
        "\n   K-2 (load-bearing PASS -> FAIL in 2023-2025) is scored by "
        "calibration_verdict.py on the composed span, not here."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
