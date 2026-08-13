"""ercot-193 — C3b-2023 monthly-residual decomposition of the ERCOT keeper.

Read-only counterfactual re-scoring in the ercot-189 pattern: NO lever, NO
derive, NO LP, no run registered, keeper untouched. Reads the keeper's own
REGISTERED dashboard payload (`frontend/data/backcast/runs/<id>.js`) and the
committed ERCOT bench actuals, reproduces the rubric's C3b statistic with the
scorer's own `_wmean`/`_nrmse` (imported, not re-implemented), and then asks
one question: **where does the C3b-2023 NRMSE live, month by month?**

Counterfactual scoring only — measured actuals enter as the score's reference,
never as any model input (rule 13 `[R-MEASURED]` clean, identical footing to
`ercot189_c3a_c3c_overlap.py`). Output:
``results/calibration/ercot193_c3b_decomposition.json``.

Usage::

    python scripts/probes/ercot193_c3b_decomposition.py \
        [--run-id 2026-08-12-run192-arm-coal-peak]
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RUNS_DIR = REPO / "frontend" / "data" / "backcast" / "runs"
BENCH_DIR = REPO / "frontend" / "data" / "backcast" / "bench" / "ERCOT"
OUT = REPO / "results" / "calibration" / "ercot193_c3b_decomposition.json"

sys.path.insert(0, str(REPO / "scripts"))
from calibration_verdict import _nrmse, _wmean  # noqa: E402  (the rubric's own arithmetic)

DEFAULT_RUN = "2026-08-12-run192-arm-coal-peak"


def load_payload(run_id: str) -> dict:
    """Decode the registered run payload (window.BC.runGz base64-gzip blob)."""
    raw = (RUNS_DIR / f"{run_id}.js").read_text()
    m = re.search(r'runGz\["[^"]+"\]="([^"]+)"', raw)
    if m is None:
        raise SystemExit(f"no runGz blob in {run_id}.js")
    return json.loads(gzip.decompress(base64.b64decode(m.group(1))))


def load_bench(year: int) -> dict:
    return json.loads(gzip.decompress((BENCH_DIR / f"{year}.json.gz").read_bytes()))[
        "bench"
    ]


def model_monthly(ypay: dict) -> list[float | None]:
    """The scorer's own C3b model vector: demand-weighted across zones of pMon."""
    lmp = ypay.get("lmp", {})
    out: list[float | None] = []
    for mo in range(12):
        pairs = []
        for z in lmp.values():
            pm = (z.get("pMon") or [None] * 12)[mo]
            dm = (z.get("dMon") or [0.0] * 12)[mo]
            if pm is not None:
                pairs.append((pm, dm))
        out.append(_wmean(pairs) if pairs else None)
    return out


def actual_monthly(bench: dict) -> list[float | None]:
    """The scorer's v2.4 basis ladder: rt_lw_mon first, then da_lw_mon."""
    avg = bench.get("avgLMP") or {}
    return avg.get("rt_lw_mon") or avg.get("da_lw_mon") or avg.get("rt_mon")


def decompose(run_id: str) -> dict:
    pay = load_payload(run_id)
    years = pay["years"]
    result: dict = {"run_id": run_id, "years": {}}
    for yr, ypay in sorted(years.items()):
        model = model_monthly(ypay)
        act = actual_monthly(load_bench(int(yr)))
        nrmse = _nrmse(model, act)
        cells = [
            (mo, m, a)
            for mo, (m, a) in enumerate(zip(model, act), start=1)
            if m is not None and a is not None
        ]
        sq = [(mo, (m - a) ** 2) for mo, m, a in cells]
        total_sq = sum(s for _, s in sq)
        months = [
            {
                "month": mo,
                "model": round(m, 2),
                "actual": round(a, 2),
                "resid": round(m - a, 2),
                "sq_share": round(s / total_sq, 4) if total_sq else None,
            }
            for (mo, m, a), (_, s) in zip(cells, sq)
        ]
        # Counterfactual NRMSEs: each replaces a month subset's MODEL value with
        # the ACTUAL (i.e. "that subset scored perfect"), all else unchanged.
        def cf(perfect: set[int]) -> float | None:
            mvec = [
                (a if (mo in perfect) else m)
                for mo, (m, a) in enumerate(zip(model, act), start=1)
                if m is not None
            ]
            avec = [a for m, a in zip(model, act) if m is not None]
            return _nrmse(mvec, avec)

        aug_sep = {8, 9}
        summer = {6, 7, 8, 9}
        non_aug_sep = {mo for mo, _, _ in cells} - aug_sep
        result["years"][yr] = {
            "nrmse": round(nrmse, 4),
            "months": months,
            "counterfactuals": {
                "aug_sep_perfect": round(cf(aug_sep), 4),
                "jun_jul_aug_sep_perfect": round(cf(summer), 4),
                "all_but_aug_sep_perfect": round(cf(non_aug_sep), 4),
                "sq_share_aug_sep": round(
                    sum(s for mo, s in sq if mo in aug_sep) / total_sq, 4
                ),
                "sq_share_jun_jul_aug_sep": round(
                    sum(s for mo, s in sq if mo in summer) / total_sq, 4
                ),
            },
        }
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-id", default=DEFAULT_RUN)
    args = ap.parse_args()
    result = decompose(args.run_id)
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    for yr, y in result["years"].items():
        cfs = y["counterfactuals"]
        print(
            f"{yr}: NRMSE {y['nrmse']:.3f} | Aug+Sep sq-share "
            f"{cfs['sq_share_aug_sep']:.1%} | Aug+Sep perfect -> "
            f"{cfs['aug_sep_perfect']:.3f} | everything-else perfect -> "
            f"{cfs['all_but_aug_sep_perfect']:.3f}"
        )
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
