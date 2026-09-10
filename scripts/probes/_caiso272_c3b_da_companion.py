"""caiso-272: the C3b **DA companion** the scorer does not emit. ZERO LP.

``calibration_verdict.score_price_shape`` computes C3b as the monthly
load-weighted price NRMSE against the committed ``rt_lw_mon`` actual, and —
unlike C3a and C3c, which both carry a non-gated ``da_diagnostic`` row — it
emits **no** day-ahead companion. CAISO's 2022 C3b is one of the ISO's two open
failures (0.2402 against a ≤0.20 target / ≤0.25 commercial band), so the
question "how much of it is the DA−RT premium the rubric lists as OUT OF
REPRESENTATION" has no committed answer.

This probe supplies it, and changes nothing: it calls the scorer's **own**
``_nrmse`` on the scorer's **own** model-monthly construction, so the ONLY
thing that differs between the two columns is which committed actual series is
on the other side (``rt_lw_mon``, the gated basis, vs ``da_lw_mon``). The RT
column is printed beside it as the reproduction check — it must return the
published 0.2402 / 0.0827 / 0.1392 / 0.1070 exactly, and it does.

**This is a REPORTING instrument, not a proposal.** Nothing here rebases a
criterion; C3b gates on RT and this session does not ask for that to change
(``FINDING-caiso272`` §5).
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import scripts.calibration_verdict as cv  # noqa: E402

RUNS: tuple[tuple[str, tuple[int, ...]], ...] = (
    ("2026-09-10-caiso-269-lateevening-2022", (2022,)),
    ("2026-09-10-caiso-269-lateevening-clean", (2023, 2024, 2025)),
)
OUT = REPO / "results/calibration/_caiso272_c3b_da_companion.json"


def model_monthly(ypay: dict) -> list:
    """The scorer's own model-monthly construction (score_price_shape)."""
    lmp = ypay.get("lmp", {})
    out = []
    for mo in range(12):
        pairs = []
        for zpay in lmp.values():
            pm = (zpay.get("pMon") or [None] * 12)[mo]
            dm = (zpay.get("dMon") or [0.0] * 12)[mo]
            if pm is not None:
                pairs.append((pm, dm))
        out.append(cv._wmean(pairs) if pairs else None)
    return out


def main() -> None:
    rows = []
    print(
        f"{'year':>5s} {'C3b vs RT (GATED)':>18s} {'C3b vs DA (companion)':>22s}"
        f"   band ≤0.20 target / ≤0.25 commercial"
    )
    for run_id, years in RUNS:
        payload = cv._decode_run_js(
            (REPO / f"frontend/data/backcast/runs/{run_id}.js").read_text()
        )
        for year in years:
            ypay = (payload.get("years") or {}).get(str(year))
            if ypay is None:
                print(f"{year:>5d}  no payload year in {run_id}")
                continue
            avg = json.load(
                gzip.open(REPO / f"frontend/data/backcast/bench/CAISO/{year}.json.gz")
            )["bench"]["avgLMP"]
            mm = model_monthly(ypay)
            rt = cv._nrmse(mm, avg.get("rt_lw_mon"))
            da = cv._nrmse(mm, avg.get("da_lw_mon"))
            rows.append(
                {
                    "year": year,
                    "run_id": run_id,
                    "c3b_nrmse_vs_rt_gated": round(rt, 4),
                    "c3b_nrmse_vs_da_companion": round(da, 4),
                }
            )
            print(f"{year:>5d} {rt:>18.4f} {da:>22.4f}")
    OUT.write_text(
        json.dumps(
            {
                "session": "caiso-272",
                "iso": "CAISO",
                "note": "C3b gates on RT; the DA column is a REPORTING companion only.",
                "rows": rows,
            },
            indent=1,
        )
    )
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
