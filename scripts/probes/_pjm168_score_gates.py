"""Score the pjm-168 F1 (G1-G7) / F2 (H1-H6) screen gates from committed sidecars.

Reads two bundles' ``hourly/`` sidecars (arm and control, same HEAD, same year)
and evaluates the STOP gates exactly as
``docs/handoffs/PRECOMMIT-pjm167-fleet-vintage-screen-2026-09-06.md`` §4 and
``docs/handoffs/PRECOMMIT-pjm167-interface-feed-admissibility-2026-09-06.md`` §4
fix them. Zero LP.

The gates may KILL an arm and may never promote one; none reads the target
price/fuel-mix residual (rule 1 ``[R-STRUCT]``, rule 29 ``[R-SCREEN]``).

Usage:
    python scripts/probes/_pjm168_score_gates.py --arm DIR --control DIR \
        --year 2021 --suite f1
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

import pandas as pd  # noqa: E402

#: Every coal plant_group present in EITHER bundle. The F1 arm restores
#: vintage-2021 units that carry the generic ``COAL`` group in addition to the
#: CAMPD-binned COAL_BIT/PRB/WC subclasses, so the family must be discovered
#: from the data rather than hardcoded (pjm-168 instrument fix).
def coal_groups(*frames) -> tuple[str, ...]:
    """Return every class name starting with COAL across *frames*."""
    ks = set()
    for f in frames:
        ks |= {k for k in f.klass.unique() if str(k).upper().startswith("COAL")}
    return tuple(sorted(ks))
#: G5 / H4 footprint classes the mechanism claims NOT to touch.
FOOTPRINT_CLASSES = ("nuclear", "wind", "solar", "hydro", "biomass", "OTHER")


def load(bundle: Path, year: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (class_hourly, system) P1 frames for *year*."""
    ch = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    sy = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return ch[ch["pass"] == "P1"], sy[sy["pass"] == "P1"]


def class_peak(ch: pd.DataFrame, klasses) -> float:
    """System-wide hourly peak MW summed across *klasses*."""
    sub = ch[ch.klass.isin(klasses)]
    return float(sub.groupby("hour")["mw"].sum().max()) if len(sub) else 0.0


def class_twh(ch: pd.DataFrame, klass: str) -> float:
    """Annual energy TWh for one class."""
    return float(ch[ch.klass == klass]["mw"].sum()) / 1e6


def main() -> int:
    """Evaluate and print the gate table."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", required=True)
    ap.add_argument("--control", required=True)
    ap.add_argument("--year", type=int, default=2021)
    ap.add_argument("--suite", choices=("f1", "f2"), default="f1")
    ap.add_argument("--census", default=None,
                    help="_pjm168_f1_census_<year>.json for G1/G3")
    args = ap.parse_args()

    arm_dir, ctl_dir = Path(args.arm), Path(args.control)
    a_ch, a_sy = load(arm_dir, args.year)
    c_ch, c_sy = load(ctl_dir, args.year)

    rows: list[tuple[str, str, str, str]] = []

    CG = coal_groups(a_ch, c_ch)
    a_coal_pk, c_coal_pk = class_peak(a_ch, CG), class_peak(c_ch, CG)
    a_stgas_pk = class_peak(a_ch, ("ST_GAS",))
    c_stgas_pk = class_peak(c_ch, ("ST_GAS",))
    a_slack = float(a_sy["slack"].sum())
    c_slack = float(c_sy["slack"].sum())

    if args.suite == "f1":
        # ---- G1 / G3 need the registry census -------------------------------
        if args.census:
            cen = json.loads(Path(args.census).read_text())
            a_reg = cen["arm"]["_COAL_TOTAL"]
            c_reg = cen["control"]["_COAL_TOTAL"]
            g1 = abs(a_reg - 48708) <= 1 and abs(c_reg - 38722) <= 1
            rows.append(("G1", "fleet identity",
                         f"arm {a_reg:.1f} (exp 48708+-1) / control {c_reg:.1f} (exp 38722+-1)",
                         "PASS" if g1 else "FAIL"))
            ratio = a_coal_pk / a_reg * 100 if a_reg else 0.0
            c_ratio = c_coal_pk / c_reg * 100 if c_reg else 0.0
            rows.append(("G3", "ceiling released",
                         f"arm {ratio:.1f}% (control {c_ratio:.1f}%, need <90%)",
                         "PASS" if ratio < 90 else "FAIL"))
        else:
            rows.append(("G1", "fleet identity", "census not supplied", "SKIP"))
            rows.append(("G3", "ceiling released", "census not supplied", "SKIP"))

        d = a_coal_pk - c_coal_pk
        rows.append(("G2", "direction & order of magnitude",
                     f"coal peak {c_coal_pk:.0f} -> {a_coal_pk:.0f} MW (delta {d:+.0f}; need +2000..+9986)",
                     "PASS" if 2000 <= d <= 9986 else "FAIL"))
        rows.append(("G4", "phantom capacity gone",
                     f"arm ST_GAS peak {a_stgas_pk:.0f} MW (control {c_stgas_pk:.0f}; need <=7411)",
                     "PASS" if a_stgas_pk <= 7411 else "FAIL"))

        worst, ok = None, True
        for k in FOOTPRINT_CLASSES:
            ca, cc = class_twh(a_ch, k), class_twh(c_ch, k)
            pct = (ca - cc) / cc * 100 if cc else 0.0
            if worst is None or abs(pct) > abs(worst[1]):
                worst = (k, pct)
            if abs(pct) >= 1.0:
                ok = False
        rows.append(("G5", "footprint confined",
                     f"largest move {worst[0]} {worst[1]:+.2f}% (need each <1.0%)",
                     "PASS" if ok else "FAIL"))
        rows.append(("G6", "no non-target load-bearing flip",
                     "C2/C4 scored separately from metrics.json", "SEE-BELOW"))
        rows.append(("G7", "EMAAC not made worse",
                     f"arm slack {a_slack:,.0f} MWh vs control {c_slack:,.0f} (need <=)",
                     "PASS" if a_slack <= c_slack + 1e-6 else "FAIL"))
    else:
        em_a = a_sy[a_sy.zone == "PJM_EMAAC"]["slack"].sum()
        em_c = c_sy[c_sy.zone == "PJM_EMAAC"]["slack"].sum()
        rows.append(("H2", "artifact is gone",
                     f"arm EMAAC slack {em_a:,.0f} MWh (control {em_c:,.0f}; need 0)",
                     "PASS" if em_a <= 1e-6 else "FAIL"))
        for tag, sy in (("arm", a_sy), ("control", c_sy)):
            em = sy[sy.zone == "PJM_EMAAC"].groupby("hour")["price"].mean()
            rest = sy[sy.zone != "PJM_EMAAC"].groupby("hour")["price"].mean()
            wedge = float((em - rest).mean())
            rows.append((f"H3-{tag}", "east-west wedge",
                         f"{tag} EMAAC-rest = ${wedge:+.2f}/MWh (arm needs <+10)",
                         "PASS" if (tag == "control" or wedge < 10) else "FAIL"))
        worst, ok = None, True
        for k in ("nuclear", "wind", "solar", "hydro"):
            ca, cc = class_twh(a_ch, k), class_twh(c_ch, k)
            pct = (ca - cc) / cc * 100 if cc else 0.0
            if worst is None or abs(pct) > abs(worst[1]):
                worst = (k, pct)
            if abs(pct) >= 1.0:
                ok = False
        rows.append(("H4", "footprint confined",
                     f"largest renewable/nuclear move {worst[0]} {worst[1]:+.2f}% (need <1.0%)",
                     "PASS" if ok else "FAIL"))

    print(f"\n{'gate':<10} {'name':<34} {'measurement':<74} verdict")
    print("-" * 132)
    for g, n, m, v in rows:
        print(f"{g:<10} {n:<34} {m:<74} {v}")
    print()
    kills = [r[0] for r in rows if r[3] == "FAIL"]
    print(f"KILLED BY: {kills}" if kills else "No gate in this suite FAILED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
