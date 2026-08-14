"""pjm-161 Phase-0(b): is C3b's 2022 miss an independent defect, or the C1 object in price space?

C3b is a **12-month load-weighted price NRMSE** (``calibration_verdict
.score_price_shape``), not a duration-curve statistic — so "which bands carry
the NRMSE" is answered month by month. This probe rebuilds the scorer's own
metric from the committed run payloads and reports each month's contribution,
for 2022 alongside 2023-2025, and cross-plots it against the same months' gas
price and the layer's own net virtual position.

No LP, no scoring, no registration: it reads committed payloads and bench parts
and reproduces a number the scorer already published.

Run:  uv run python scripts/probes/_pjm161_c3b_months.py
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

RUNS = REPO / "frontend" / "data" / "backcast" / "runs"
BENCH = REPO / "frontend" / "data" / "backcast" / "bench" / "PJM"

PAYLOAD_OF = {
    2022: "2026-08-05-pjm-2022-touchpoint",
    2023: "2026-08-04-pjm-152-collapse",
    2024: "2026-08-04-pjm-152-collapse",
    2025: "2026-08-04-pjm-152-collapse",
}


def load_payload(run_id: str) -> dict:
    """Decode a committed ``runs/<id>.js`` sidecar via the scorer's own reader."""
    sys.path.insert(0, str(REPO / "scripts"))
    from calibration_verdict import _decode_run_js

    return _decode_run_js((RUNS / f"{run_id}.js").read_text())


def bench(year: int) -> dict:
    with gzip.open(BENCH / f"{year}.json.gz") as fh:
        return json.load(fh)["bench"]


def _wmean(pairs):
    tot = sum(w for _, w in pairs)
    if tot <= 0:
        return float(np.mean([v for v, _ in pairs]))
    return sum(v * w for v, w in pairs) / tot


def model_monthly(ypay: dict) -> list[float]:
    """Reproduce the scorer's demand-weighted monthly model LMP."""
    lmp = ypay.get("lmp", {})
    out = []
    for mo in range(12):
        pairs = []
        for z in lmp.values():
            pm = (z.get("pMon") or [None] * 12)[mo]
            dm = (z.get("dMon") or [0.0] * 12)[mo]
            if pm is not None:
                pairs.append((pm, dm))
        out.append(_wmean(pairs) if pairs else float("nan"))
    return out


def main() -> None:
    pd.set_option("display.width", 200)
    summary = []
    for year, run_id in PAYLOAD_OF.items():
        pay = load_payload(run_id)
        yb = bench(year)
        years_blk = pay.get("years") or pay.get("byYear") or {}
        ypay = years_blk.get(str(year)) or years_blk.get(year)
        if ypay is None:
            print(f"{year}: no year block in {run_id} (keys={list(years_blk)[:6]})")
            continue
        m = np.array(model_monthly(ypay), dtype=float)
        avg = yb.get("avgLMP") or {}
        a = avg.get("rt_lw_mon") or avg.get("da_lw_mon")
        basis = "rt_lw" if avg.get("rt_lw_mon") else "da_lw"
        if a is None:
            a = avg.get("rt_mon") or avg.get("da_mon")
            basis = "rt_mon(legacy)"
        a = np.array(a, dtype=float)

        resid = m - a
        denom = float(np.sqrt(np.mean(a**2)))
        nrmse = float(np.sqrt(np.mean(resid**2))) / denom
        # per-month share of the squared error
        share = resid**2 / np.sum(resid**2)

        tbl = pd.DataFrame(
            {
                "model": m.round(2),
                "actual": a.round(2),
                "resid": resid.round(2),
                "resid%": (100 * resid / a).round(1),
                "sq_share%": (100 * share).round(1),
            },
            index=[f"M{i+1:02d}" for i in range(12)],
        )
        print("=" * 92)
        print(f"C3b {year}  NRMSE = {nrmse:.3f}   (basis {basis}, denom RMS actual {denom:.2f})")
        print("=" * 92)
        print(tbl.T.to_string())
        top = tbl["sq_share%"].sort_values(ascending=False).head(3)
        print(f"  top-3 months by squared-error share: {dict(top)}")
        # NRMSE with the single worst month removed — is it one month or all twelve?
        worst = int(np.argmax(resid**2))
        keep = [i for i in range(12) if i != worst]
        n_wo = float(np.sqrt(np.mean(resid[keep] ** 2))) / float(
            np.sqrt(np.mean(a[keep] ** 2))
        )
        print(f"  drop worst month (M{worst+1:02d}): NRMSE {nrmse:.3f} -> {n_wo:.3f}")
        summary.append(
            dict(
                year=year,
                nrmse=round(nrmse, 4),
                worst_month=worst + 1,
                worst_resid=round(float(resid[worst]), 2),
                worst_share_pct=round(float(100 * share[worst]), 1),
                nrmse_ex_worst=round(n_wo, 4),
                mean_resid=round(float(resid.mean()), 2),
                mean_abs_resid=round(float(np.abs(resid).mean()), 2),
            )
        )
        print()

    s = pd.DataFrame(summary).set_index("year")
    print("=" * 92)
    print("SUMMARY — C3b by year (tolerance: target ≤0.20, commercial ≤0.30)")
    print("=" * 92)
    print(s.T.to_string())
    dest = REPO / "results" / "calibration" / "_pjm161_c3b_months.json"
    dest.write_text(
        json.dumps(json.loads(s.reset_index().to_json(orient="records")), indent=1) + "\n"
    )
    print(f"\nwrote {dest.relative_to(REPO)}")


if __name__ == "__main__":
    main()
