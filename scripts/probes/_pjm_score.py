"""Session helper: PJM tolerance scorecard for a calibration bundle.

Usage: python scripts/probes/_pjm_score.py <bundle> [<bundle> ...]

Per year scores gas/nuclear/wind/solar from the payload fuelRows (m vs b),
COAL_BIT/PRB/WC from gmModel vs bench[year].classFull, coal-total as the sum
of the COAL_* classes, and LMP as the load-weighted model price vs
bench[year].avgLMP["rt"].  Tolerance: |model-actual| <= 1 TWh when actual
< 20 TWh, else <= 5% of actual.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from render_calibration_html import build_payload  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
COAL = ["COAL_BIT", "COAL_PRB", "COAL_WC"]


def verdict(model: float, actual: float) -> tuple[float, str]:
    d = model - actual
    if actual < 20.0:
        return d, ("PASS" if abs(d) <= 1.0 else "FAIL")
    return d, ("PASS" if abs(d) <= 0.05 * actual else "FAIL")


def score(bundle: str) -> int:
    pay = build_payload([(bundle, ROOT / bundle)])
    run = pay["model"][0]["years"]
    bench = pay["bench"]
    fails = 0
    print(f"\n=== {bundle} ===")
    hdr = f"{'year':>4} {'class':<10} {'model':>8} {'actual':>8} {'resid':>7} {'pct':>7}  verdict"
    print(hdr)
    for year in sorted(run):
        y = run[year]
        b = bench[year]
        rows = []
        for fr in y["fuelRows"]:
            if fr["fuel"] in ("gas", "nuclear", "wind", "solar") and fr["b"] is not None:
                rows.append((fr["fuel"], float(fr["m"]), float(fr["b"])))
        ctot_m = ctot_a = 0.0
        for cls in COAL:
            m = float(y["gmModel"].get(cls, 0.0))
            a = float(b["classFull"].get(cls, 0.0))
            ctot_m += m
            ctot_a += a
            rows.append((cls, m, a))
        rows.append(("coal-tot", ctot_m, ctot_a))
        for name, m, a in rows:
            d, v = verdict(m, a)
            if v == "FAIL":
                fails += 1
            print(f"{year:>4} {name:<10} {m:>8.2f} {a:>8.2f} {d:>+7.2f} "
                  f"{100 * d / a if a else float('nan'):>+6.1f}%  {v}")
        # Net interchange (informational, no tolerance gate; net-export
        # positive). Present only for priced-interchange bundles.
        ix = next((fr for fr in y["fuelRows"]
                   if fr["fuel"] == "interchange"), None)
        if ix is not None and ix["b"]:
            im, ib = float(ix["m"]), float(ix["b"])
            print(f"{year:>4} {'interchg':<10} {im:>8.2f} {ib:>8.2f} "
                  f"{im - ib:>+7.2f} {100 * (im - ib) / ib:>+6.1f}%  (info)")
        # LMP (informational, no tolerance gate)
        lmp = y["lmp"]
        pd_sum = sum(z["p"] * z["d"] for z in lmp.values())
        d_sum = sum(z["d"] for z in lmp.values())
        mp = pd_sum / d_sum if d_sum else float("nan")
        rt = (b.get("avgLMP") or {}).get("rt")
        if rt:
            print(f"{year:>4} {'LMP':<10} {mp:>8.2f} {rt:>8.2f} "
                  f"{mp - rt:>+7.2f} {100 * (mp - rt) / rt:>+6.1f}%  (info)")
        else:
            print(f"{year:>4} {'LMP':<10} {mp:>8.2f} {'n/a':>8}")
    print(f"in-tolerance fails: {fails}")
    return fails


if __name__ == "__main__":
    for bn in sys.argv[1:]:
        score(bn)
