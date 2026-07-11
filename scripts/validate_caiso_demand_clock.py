"""Guard the measured CAISO demand-clock realignment window (rule 23 freeze).

Re-derives, from the EIA-930 CISO extract alone, the ``Demand``-column clock
window that ``eia_loader._CAISO_DEMAND_CLOCK_LAG_H`` /
``_CAISO_DEMAND_CLOCK_REALIGN_END`` encode: for each train-year month, the
best integer lag of ``Demand`` against the extract's own balance identity
(``Net generation − Total interchange``, the wall-true generation frame). The
constants are frozen against residuals — they may change ONLY when this scan
says the source data changed (e.g. EIA re-publishes the 2023 series aligned,
in which case the scan reports lag 0 everywhere and the realignment window
must be emptied, so the correction cannot silently double-shift).

Derivation record (2026-07-11, FINDING-caiso75-demand-clock-2026-07-11.md):
2023-01..2023-10 best lag −1 (r = 0.984-0.997), 2023-11 mixed (transition
month, r = 0.68 at 0), 2023-12 and all 2024/2025 months best lag 0.

Exit 1 when the on-disk extract disagrees with the encoded window.
Run: ``python scripts/validate_caiso_demand_clock.py``
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from market_sim.data.eia_loader import (  # noqa: E402
    _CAISO_DEMAND_CLOCK_LAG_H,
    _CAISO_DEMAND_CLOCK_REALIGN_END,
)

#: Train years scanned (rule 22 — the guard never touches holdout years).
YEARS = (2023, 2024, 2025)

#: Minimum monthly correlation for a lag call to count as decisive. The
#: 2023-11 transition month sits far below this on every candidate lag.
_MIN_DECISIVE_R = 0.90


def monthly_best_lags() -> dict[tuple[int, int], tuple[int, float]]:
    """Return {(year, month): (best_lag, r)} for Demand vs net_gen − interchange."""
    df = pd.read_parquet(RAW_DATA_DIR / "eia-930-hourly" / "CISO hourly.parquet")
    df["utc"] = pd.to_datetime(df["UTC time"], utc=True)
    df = df.set_index("utc").sort_index()
    out: dict[tuple[int, int], tuple[int, float]] = {}
    for year in YEARS:
        d = df[df.index.year == year]
        dem = d["Demand"]
        si = d["Net generation"] - d["Total interchange"]
        months = pd.Series(
            d.index.tz_convert("America/Los_Angeles").month, index=d.index
        )
        for mo in range(1, 13):
            sub = d.index[months == mo]
            best: tuple[int, float] | None = None
            for lag in (-2, -1, 0, 1, 2):
                a = dem.shift(lag).reindex(sub)
                b = si.reindex(sub)
                m = a.notna() & b.notna()
                if int(m.sum()) < 100:
                    continue
                r = float(np.corrcoef(a[m], b[m])[0, 1])
                if best is None or r > best[1]:
                    best = (lag, r)
            if best is not None:
                out[(year, mo)] = best
    return out


def main() -> int:
    """Validate the encoded window against the re-derived monthly lags."""
    end = pd.Timestamp(_CAISO_DEMAND_CLOCK_REALIGN_END)
    lags = monthly_best_lags()
    failures: list[str] = []
    for (year, mo), (lag, r) in sorted(lags.items()):
        month_start = pd.Timestamp(year=year, month=mo, day=1)
        in_window = month_start < end and (month_start + pd.offsets.MonthEnd(0) < end)
        boundary_month = month_start < end <= month_start + pd.offsets.MonthBegin(1)
        expected = -_CAISO_DEMAND_CLOCK_LAG_H if in_window else 0
        if boundary_month or r < _MIN_DECISIVE_R:
            status = "transition/indecisive"
        elif lag == expected:
            status = "ok"
        else:
            status = "MISMATCH"
            failures.append(
                f"{year}-{mo:02d}: best lag {lag:+d} (r={r:.3f}), "
                f"window expects {expected:+d}"
            )
        print(f"{year}-{mo:02d}: lag {lag:+d} r={r:.3f} [{status}]")
    if failures:
        print(
            "\nFAIL: the extract's Demand clock no longer matches the encoded "
            "realignment window — re-derive _CAISO_DEMAND_CLOCK_* from this "
            "scan (source-data change), citing the new derivation:"
        )
        print("\n".join(failures))
        return 1
    print("\nOK: encoded realignment window matches the source data.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
