"""ERCOT-96 A/B readout: compare two bundle dirs (base vs probe) on the 2023
C3c/C3a-direction metrics plus guard diagnostics, straight from the bundles'
hourly parquets (no registration — rule-16 throwaway probes never touch the
dashboard; the full rubric run happens only for a registered candidate).

Usage::

    python scripts/probes/_ercot96_ab_readout.py BASE_BUNDLE PROBE_BUNDLE [--year 2023]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
THRESH = 200.0


def load(bundle: Path, year: int) -> dict:
    """Return the readout dict for one bundle-year."""
    sysp = pd.read_parquet(bundle / f"hourly/system_{year}.parquet")
    sysp = sysp[sysp["pass"] == "P1"] if "pass" in sysp.columns else sysp
    px = sysp.groupby("hour")["price"].max().reindex(range(8760))
    dem = sysp.groupby("hour")["demand"].sum().reindex(range(8760))
    slack = sysp.groupby("hour")["slack"].sum().reindex(range(8760))
    ch = pd.read_parquet(bundle / f"hourly/class_hourly_{year}.parquet")
    ch = ch[ch["pass"] == "P1"] if "pass" in ch.columns else ch
    disp = {
        k: g.groupby("hour")["mw"].sum().reindex(range(8760)).fillna(0.0)
        for k, g in ch.groupby("klass")
    }
    return {"px": px, "dem": dem, "slack": slack, "disp": disp}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("base", type=Path)
    ap.add_argument("probe", type=Path)
    ap.add_argument("--year", type=int, default=2023)
    args = ap.parse_args()

    res = pd.read_parquet(
        REPO / f"data/raw/ercot/ercot_{args.year}_ordc_reserves_hourly.parquet"
    )
    lam = res.set_index("hour")["system_lambda"].reindex(range(8760))
    actual_tail = set(np.flatnonzero((lam > THRESH).values).tolist())

    rows = []
    both = {}
    for name, bundle in (("base", args.base), ("probe", args.probe)):
        d = load(bundle, args.year)
        both[name] = d
        px, dem = d["px"], d["dem"]
        tail = set(np.flatnonzero((px > THRESH).values).tolist())
        month = pd.Series(range(8760)).floordiv(24).add(1)
        doy = np.arange(8760) // 24 + 1
        mo = pd.to_datetime(f"{args.year}-01-01") + pd.to_timedelta(doy - 1, "D")
        mo = pd.DatetimeIndex(mo).month
        aug_aft = (mo == 8) & (np.arange(8760) % 24 >= 13) & (np.arange(8760) % 24 <= 19)
        sep_aft = (mo == 9) & (np.arange(8760) % 24 >= 13) & (np.arange(8760) % 24 <= 19)
        rows.append(
            {
                "run": name,
                "tail_h": len(tail),
                "tail_in_actual": len(tail & actual_tail),
                "spurious": len(tail - actual_tail),
                "mean_px": px.mean(),
                "lw_mean_px": (px * dem).sum() / dem.sum(),
                "aug_aft_px": px[aug_aft].mean(),
                "sep_aft_px": px[sep_aft].mean(),
                "px_gt50": int((px > 50).sum()),
                "px_lt0": int((px < 0).sum()),
                "slack_h": int((d["slack"] > 1e-3).sum()),
                "cap_h": int((px >= 4999).sum()),
            }
        )
    t = pd.DataFrame(rows).set_index("run")
    t["actual_tail"] = len(actual_tail)
    t["actual_mean_lambda"] = lam.mean()
    pd.set_option("display.width", 200)
    print(t.round(2).to_string())

    # class dispatch deltas on the actual tail hours + full-year energy
    ta = sorted(actual_tail)
    print("\nclass dispatch: probe - base (GWh full-year | MW mean on actual tail hours)")
    for k in sorted(set(both["base"]["disp"]) | set(both["probe"]["disp"])):
        b = both["base"]["disp"].get(k)
        p = both["probe"]["disp"].get(k)
        if b is None or p is None:
            continue
        dgwh = (p.sum() - b.sum()) / 1e3
        dtail = (p.iloc[ta].mean() - b.iloc[ta].mean())
        if abs(dgwh) > 0.5 or abs(dtail) > 10:
            print(f"  {k:12s} {dgwh:+8.1f} GWh | {dtail:+7.0f} MW tail")

    # diurnal price profile (C7-direction): hod means, both runs vs actual
    hod = np.arange(8760) % 24
    prof = pd.DataFrame(
        {
            "actual": lam.groupby(hod).mean(),
            "base": both["base"]["px"].groupby(hod).mean(),
            "probe": both["probe"]["px"].groupby(hod).mean(),
        }
    )
    print("\nhod price profile (Jun-Sep):")
    summer = np.isin(pd.DatetimeIndex(
        pd.to_datetime(f"{args.year}-01-01") + pd.to_timedelta(np.arange(8760) // 24, "D")
    ).month, [6, 7, 8, 9])
    profs = pd.DataFrame(
        {
            "actual": lam[summer].groupby(hod[summer]).mean(),
            "base": both["base"]["px"][summer].groupby(hod[summer]).mean(),
            "probe": both["probe"]["px"][summer].groupby(hod[summer]).mean(),
        }
    )
    print(profs.round(1).to_string())
    for nm in ("base", "probe"):
        r = np.corrcoef(profs["actual"], profs[nm])[0, 1]
        print(f"  summer hod-profile corr vs actual: {nm} {r:.3f}")


if __name__ == "__main__":
    main()
