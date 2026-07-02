"""Quick C1 fuel-mix readout for a freshly-solved bundle (no dashboard write).

Calls render_calibration_html.build_payload on the bundle and prints, per year,
each fossil class's model vs actual grid-delivered TWh, the miss, the share-pp
gap, and a PASS/FAIL against the C1 band (min(2% annual gen, 8 TWh) volume AND
+/-3.0pp share). Lets the merit-order levers be iterated without registering
every probe iteration on the dashboard.

Usage: python scripts/probes/_c1_fuelmix_quick.py results/calibration/162 [year ...]
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

import render_calibration_html as rch  # noqa: E402

GAS = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP")
COAL = ("COAL_PRB", "COAL_LIGNITE", "COAL_BIT", "COAL_SUB", "COAL_WC")
# 2026-07-02 rubric re-balance — keep in lockstep with
# calibration_verdict.FUELMIX_* and session_score.py.
VOL_GEN_FRAC = 0.02
VOL_CAP_TWH = 8.0
SHARE_PP = 3.0


def main():
    bundle = Path(sys.argv[1])
    want = {int(y) for y in sys.argv[2:]} if len(sys.argv) > 2 else None
    D = rch.build_payload([("probe", bundle)], years=want)
    model = D["model"][0]["years"]
    bench = D["bench"]
    for year in sorted(model):
        if want and year not in want:
            continue
        gm = model[year]["gmModel"]
        cf = bench[year]["classFull"]
        a_gen = sum(float(v) for v in cf.values())
        m_gen = sum(float(gm.get(g, 0.0)) for g in cf)
        vol_band = min(VOL_GEN_FRAC * a_gen, VOL_CAP_TWH)
        print(f"\n=== {year}  (vol band ±{vol_band:.2f} TWh, share ±{SHARE_PP}pp) ===")
        print(
            f"{'class':<13}{'model':>9}{'actual':>9}{'miss':>8}{'miss%':>8}"
            f"{'share_pp':>9}  verdict"
        )
        classes = [c for c in (*GAS, *COAL) if c in cf]
        for c in classes:
            a = float(cf[c])
            m = float(gm.get(c, 0.0))
            d = m - a
            miss_pct = 100.0 * d / a if a else float("nan")
            share = 100.0 * m / m_gen - 100.0 * a / a_gen if m_gen and a_gen else 0.0
            ok = abs(d) <= vol_band and abs(share) <= SHARE_PP
            print(
                f"{c:<13}{m:>9.2f}{a:>9.2f}{d:>+8.2f}{miss_pct:>+7.1f}%"
                f"{share:>+9.2f}  {'PASS' if ok else 'FAIL'}"
            )
        print(f"{'TOTAL fossil':<13}{m_gen:>9.2f}{a_gen:>9.2f}")


if __name__ == "__main__":
    main()
