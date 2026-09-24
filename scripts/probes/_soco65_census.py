"""SOCO-65 (NO branch) keeper start-markup census, ZERO LP.

Measures, on the SOCO-61 keeper legs for 2023-2025, which tranches carry the
P1 bid-cost start amortization (``model.commitment.compute_monthly_markup``)
and at what level. SOCO-64 §6 measured 2023 only; this extends it to every
year the keeper carries.

Construction (declared before any number was read):

* Start markup on a tranche = (solved P1 ``mc`` - ``fleet_only`` ``mc_base``)
  of that tranche MINUS the same quantity on the same plant's econ*/peak
  sibling (median over siblings, hour by hour). The raw ``mc - mc_base`` carries
  a fuel-linked offset that is IDENTICAL across one plant's tranches (same heat
  rate) and holds no start term; the sibling difference removes it. Plants with
  no econ/peak sibling are skipped.
* ``mc_base`` must come from a fleet built at the keeper's OWN ``git_sha``
  (``1d7edc1b``), not HEAD: HEAD carries later solve-path changes
  (heat-rate vintage, campd_bins, eia860) that move ``mc_base``. Build it with
  ``_soco63_phase0.py fleet --year Y --out <dir>/fleet_Y.npz`` run from a tree
  extracted at that sha (``git archive 1d7edc1b src scripts configs``, with
  ``data`` and ``results/calibration`` symlinked in).

Usage: ``python3 scripts/probes/_soco65_census.py --fleet-dir <dir> [--out-csv f]``
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
LEG = _ROOT / "results/calibration/soco61_arm_{y}"
YEARS = (2023, 2024, 2025)
GROUPS = ("CT_PEAKER", "CC_REGULAR", "ST_GAS", "COAL", "CT_CHP", "CC_CHP", "ST_CHP")
#: Markup threshold, $/MWh: below this a tranche-hour is read as unmarked
#: (the sibling difference is exact to float precision on unmarked tranches).
EPS = 0.01


def _suffix(uid: str) -> str:
    s = uid.rsplit("_", 1)[-1]
    return "econ" if s.startswith("econ") else s


def census(fleet_dir: Path) -> pd.DataFrame:
    """Per (year, class, tranche suffix): tranches, marked count, level, energy, start $."""
    rec = []
    for y in YEARS:
        u = pd.read_parquet(Path(str(LEG).format(y=y)) / f"hourly/unit_hourly_{y}.parquet",
                            columns=["unit_id", "plant_code", "plant_group", "hour", "mw", "mc"])
        u = u[u.plant_group.isin(GROUPS)]
        f = np.load(fleet_dir / f"fleet_{y}.npz")
        fi = {x: i for i, x in enumerate(f["ids"])}
        for (grp, plant), g in u.groupby(["plant_group", "plant_code"]):
            tr = {}
            for uid, h in g.groupby("unit_id"):
                h = h.sort_values("hour")
                tr[uid] = (h.mc.values - f["mc_base"][fi[uid], : len(h)], h.mw.values)
            sib = [k for k in tr if "_econ" in k or k.endswith("_peak")]
            if not sib:
                continue
            ref = np.median(np.vstack([tr[k][0] for k in sib]), axis=0)
            for uid, (d, mw) in tr.items():
                m, w = np.nan_to_num(d - ref), np.nan_to_num(mw)
                rec.append({"year": y, "group": grp, "suffix": _suffix(uid), "unit_id": uid,
                            "marked": bool((m > EPS).any()), "max": m.max(), "twh": w.sum() / 1e6,
                            "cost_musd": (m * w).sum() / 1e6, "pos": m[m > EPS]})
    df = pd.DataFrame(rec)
    g = df.groupby(["year", "group", "suffix"])
    out = g.agg(tranches=("unit_id", "size"), marked=("marked", "sum"), max=("max", "max"),
                twh=("twh", "sum"), start_cost_musd=("cost_musd", "sum"))
    out["median_marked_hr"] = g.pos.apply(
        lambda s: float(np.median(np.concatenate(list(s.values)))) if sum(map(len, s)) else 0.0)
    out["gen_wtd_usd_mwh"] = out.start_cost_musd / out.twh.replace(0, np.nan)
    return out


def main() -> None:
    """CLI."""
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fleet-dir", type=Path, required=True)
    ap.add_argument("--out-csv", type=Path, default=None)
    a = ap.parse_args()
    out = census(a.fleet_dir)
    pd.set_option("display.width", 200)
    print(out.round(3).to_string())
    if a.out_csv:
        out.round(4).to_csv(a.out_csv)


if __name__ == "__main__":
    main()
