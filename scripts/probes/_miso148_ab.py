"""miso-148 A/B — the arm's effect against its SAME-HEAD zero-delta control.

Every quantity here is arm-vs-CONTROL. **No arm-vs-keeper delta is computed or
quoted anywhere**: K0 failed as written (HEAD drift since the keeper's own
solve, measured and attributed in the attestation), so the committed keeper is
not a valid comparator — which is precisely why a same-HEAD control was solved.

Reports, in the order the PREREG's kill gates name them:

* **C3a / C3b** per year, both arms, from the bundles' own system sidecars on
  the C3a demand weight — cross-checked against the committed scorer.
* **MAY 2025**, the charter's explicitly-required report: *a mechanism that does
  not report its May effect has not been measured*.
* **MONTHLY** model-vs-actual mean LMP, both arms, so the level move is visible
  where it happens rather than only in the annual mean.
* **C8** forced-energy shares from each bundle's committed
  ``legitimacy_diagnostics.json`` (kill gate: no material class's forced share
  rises), and the **D-4** off-window-binding rows.
* **Class energy** deltas (the K4 live check).

Probe hygiene (miso-140b §6): ``hygiene()`` at the entry point; the ACTUAL
hourly series comes from ``_miso137_c3a_gap_decomposition.actual_hourly``, the
same instrument miso-137/146/147 used.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _i, _p in enumerate((REPO, REPO / "src", REPO / "scripts", REPO / "scripts" / "probes")):
    sys.path.insert(_i, str(_p))

from _miso143_stack import YEARS, hygiene  # noqa: E402
from _miso137_c3a_gap_decomposition import actual_hourly  # noqa: E402

OUT = REPO / "results" / "calibration" / "_miso148_ab.json"
CONTROL = REPO / "results" / "calibration" / "miso148_basis_A"
ARM = REPO / "results" / "calibration" / "miso148_basis_B"
HOURS = 8760


def _system(bundle: Path, year: int) -> tuple[np.ndarray, np.ndarray]:
    """(demand-weighted hourly price, hourly total demand) for the P1 pass."""
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    df = df[df["pass"] == "P1"]
    g = df.groupby("hour")
    dem = g["demand"].sum()
    num = df.assign(pd_=df["price"] * df["demand"]).groupby("hour")["pd_"].sum()
    price = (num / dem).reindex(range(HOURS)).to_numpy(float)
    return price, dem.reindex(range(HOURS)).to_numpy(float)


def _month_of_hour(n: int = HOURS) -> np.ndarray:
    doy = np.arange(n) // 24
    return pd.to_datetime(
        pd.Series(doy), unit="D", origin=pd.Timestamp("2023-01-01")
    ).dt.month.to_numpy()


def _wmean(x: np.ndarray, w: np.ndarray, m: np.ndarray) -> float:
    k = m & np.isfinite(x) & np.isfinite(w)
    return float((x[k] * w[k]).sum() / w[k].sum()) if w[k].sum() > 0 else float("nan")


def year_block(year: int) -> dict:
    rt, _da = actual_hourly(year)
    pc, wc = _system(CONTROL, year)
    pa, wa = _system(ARM, year)
    w = wc  # ONE weight for both arms — the control's demand (K3: d_demand == 0)
    allh = np.isfinite(rt)
    month = _month_of_hour()

    def _pct(model: float, act: float) -> float:
        return round(100.0 * (model - act) / act, 2)

    a_all = _wmean(rt, w, allh)
    c_all = _wmean(pc, w, allh)
    r_all = _wmean(pa, w, allh)
    out = {
        "annual": {
            "actual": round(a_all, 3),
            "control": round(c_all, 3),
            "arm": round(r_all, 3),
            "control_pct": _pct(c_all, a_all),
            "arm_pct": _pct(r_all, a_all),
            "delta_pp": round(_pct(r_all, a_all) - _pct(c_all, a_all), 2),
            "delta_usd": round(r_all - c_all, 3),
        },
        "monthly": [],
        "demand_identity_max_abs_diff_mw": round(
            float(np.nanmax(np.abs(wa - wc))), 6
        ),
    }
    for m in range(1, 13):
        k = allh & (month == m)
        am, cm, rm = _wmean(rt, w, k), _wmean(pc, w, k), _wmean(pa, w, k)
        out["monthly"].append(
            {
                "month": m,
                "actual": round(am, 3),
                "control": round(cm, 3),
                "arm": round(rm, 3),
                "control_pct": _pct(cm, am),
                "arm_pct": _pct(rm, am),
                "delta_usd": round(rm - cm, 3),
            }
        )
    return out


def class_energy(year: int) -> dict:
    a = pd.read_parquet(CONTROL / "hourly" / f"class_hourly_{year}.parquet")
    b = pd.read_parquet(ARM / "hourly" / f"class_hourly_{year}.parquet")
    a = a[a["pass"] == "P1"].groupby("klass")["mw"].sum() / 1e6
    b = b[b["pass"] == "P1"].groupby("klass")["mw"].sum() / 1e6
    d = (b - a).sort_values(key=abs, ascending=False)
    return {
        "twh_delta": {k: round(float(v), 4) for k, v in d.items() if abs(v) > 5e-4},
        "control_twh": {k: round(float(v), 3) for k, v in a.items()},
        "net_twh": round(float(d.sum()), 4),
    }


def c8_shares() -> dict:
    out: dict = {}
    for tag, b in (("control", CONTROL), ("arm", ARM)):
        p = b / "legitimacy_diagnostics.json"
        if not p.exists():
            out[tag] = None
            continue
        d = json.loads(p.read_text())
        rows = {}
        for r in d.get("D2", {}).get("rows", []) if isinstance(d.get("D2"), dict) else []:
            rows[(r.get("year"), r.get("klass"))] = r
        out[tag] = {
            "d2_rows": len(rows),
            "shares": {
                f"{y}|{k}": round(float(r.get("forced_share", float("nan"))), 4)
                for (y, k), r in sorted(rows.items(), key=lambda kv: str(kv[0]))
            },
        }
    return out


def run() -> dict:
    hygiene()
    res: dict = {
        "session": "miso-148",
        "prereg": "results/calibration/PREREG-miso148-cc-availability-summer-basis-2026-08-09.md",
        "control_run_id": "2026-08-09-miso-148-control",
        "arm_run_id": "2026-08-09-miso-148-basis-aware",
        "comparator_note": (
            "EVERY delta is arm-vs-CONTROL at ONE HEAD. K0 failed as written "
            "(HEAD drift since the keeper's own solve), so the committed keeper "
            "is not a valid comparator and no arm-vs-keeper delta is quoted."
        ),
        "years": {},
    }
    for y in YEARS:
        res["years"][str(y)] = {
            "price": year_block(y),
            "class_energy": class_energy(y),
        }
    res["C8"] = c8_shares()
    OUT.write_text(json.dumps(res, indent=1, default=str) + "\n")
    return res


if __name__ == "__main__":
    r = run()
    for y in YEARS:
        a = r["years"][str(y)]["price"]["annual"]
        print(
            f"{y} C3a: control {a['control_pct']:+.2f}% -> arm {a['arm_pct']:+.2f}% "
            f"({a['delta_pp']:+.2f} pp, {a['delta_usd']:+.3f} $/MWh) | "
            f"d_demand max {r['years'][str(y)]['price']['demand_identity_max_abs_diff_mw']} MW"
        )
    m = r["years"]["2025"]["price"]["monthly"][4]
    print(
        f"MAY-2025 (kill gate): actual {m['actual']:.2f} | control {m['control_pct']:+.2f}% "
        f"-> arm {m['arm_pct']:+.2f}% ({m['delta_usd']:+.3f} $/MWh)"
    )
    print("2025 monthly arm-control $/MWh:",
          [x["delta_usd"] for x in r["years"]["2025"]["price"]["monthly"]])
    print(f"-> {OUT}")
