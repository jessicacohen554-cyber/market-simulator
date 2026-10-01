"""neiso-117 gate G2 (zero LP): per-yard coal burn vs budget, arm leg vs keeper; class TWh deltas.

For each year, reads the keeper's P1 dispatch (``results/calibration/neiso114b_span/
dispatch/<Y>_P1.parquet``, restored from the neiso-115 legs) and the arm leg's
(``results/calibration/neiso117_<Y>/dispatch/<Y>_P1.parquet``), sums coal-class MWh
per yard, converts to TBtu at the yard's LP heat rate recorded by the neiso-116
census (the fleet is identical in both runs, so the rate is too), and compares with
the budget ``build_coal_plant_budget`` produced on the armed path
(``phase0_yard_rows_probe.json``). Also reports per-class TWh deltas (arm - keeper).

Usage::

    uv run python docs/handoffs/neiso117/g2_yard_burn.py [--years 2019 ...] --out docs/handoffs/neiso117/g2_yard_burn.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
CAL = REPO / "results/calibration"
HERE = Path(__file__).resolve().parent
CENSUS = REPO / "docs/handoffs/neiso116/phase0_coal_budget_census.json"
BIND_TOL = 0.005  # PRECOMMIT §6 G2: binding = burn within 0.5 % of budget
INERT_TOL_TWH = 0.01  # PRECOMMIT §6 G2: slack-year class TWh equality


def _dispatch(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path, columns=["plant_code", "klass", "mw"])


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", nargs="+", type=int, default=list(range(2019, 2026)))
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    census = json.loads(CENSUS.read_text())
    probe = {
        r["year"]: r
        for r in json.loads((HERE / "phase0_yard_rows_probe.json").read_text())
    }
    hr = {(r["year"], r["plant"]): r["hr"] for r in census if r.get("hr") is not None}
    out = []
    for y in args.years:
        leg = CAL / f"neiso117_{y}/dispatch/{y}_P1.parquet"
        if not leg.exists():
            print(f"{y}: leg dispatch absent, skipped")
            continue
        k = _dispatch(CAL / f"neiso114b_span/dispatch/{y}_P1.parquet")
        a = _dispatch(leg)
        kc = k.groupby("klass")["mw"].sum() / 1e6
        ac = a.groupby("klass")["mw"].sum() / 1e6
        dcls = ac.reindex(kc.index.union(ac.index), fill_value=0) - kc.reindex(
            kc.index.union(ac.index), fill_value=0
        )
        yards = []
        for row in probe[y]["rows"]:
            plants = row["plants"]
            rec = {"plants": plants, "budget_tbtu": row["budget_tbtu"]}
            for tag, df in (("keeper", k), ("arm", a)):
                c = df[df.plant_code.isin(plants) & df.klass.str.startswith("COAL")]
                twh = 0.0
                tbtu = 0.0
                for p, g in c.groupby("plant_code"):
                    e = g["mw"].sum() / 1e6
                    if e == 0.0:
                        continue
                    twh += e
                    tbtu += e * hr[(y, int(p))]
                rec[f"{tag}_twh"] = round(float(twh), 4)
                rec[f"{tag}_tbtu"] = round(float(tbtu), 3)
            b = row["budget_tbtu"]
            rec["arm_within_budget"] = bool(rec["arm_tbtu"] <= b * (1 + 1e-6) + 1e-3)
            rec["binding"] = bool(
                rec["arm_tbtu"] >= b * (1 - BIND_TOL) and rec["keeper_tbtu"] > b
            )
            yards.append(rec)
        moved = {c: round(float(v), 4) for c, v in dcls.items() if abs(v) >= 1e-4}
        max_abs = float(dcls.abs().max()) if len(dcls) else 0.0
        r = {
            "year": y,
            "yards": yards,
            "class_twh_delta": moved,
            "max_abs_class_delta_twh": round(max_abs, 4),
            "inert_within_tol": bool(max_abs <= INERT_TOL_TWH),
        }
        print(json.dumps(r))
        out.append(r)
    if args.out:
        Path(args.out).write_text(json.dumps(out, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
