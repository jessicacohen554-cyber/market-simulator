"""THE REPAIRED GAS SERIES: what it changes, and WHERE it is largest (nyiso-234, ZERO LP).

Phase 0 for the rule 29 ``[R-SCREEN]`` screen of the nyiso-234b input repair
(``docs/FINDING-nyiso234b-the-gas-series-was-published-2026-09-14.md``): the EIA
NGWU catch-up tables the fetcher dropped, plus the one-day header misalignment.

Rule 29 (1) requires the screen year to be **named in the PRECOMMIT before the
screen runs**, and chosen where the mechanism's **own measured footprint is
largest** — NEVER where the residual is biggest, which would make the choice a
residual-driven one. This probe supplies that measurement and nothing else: it
reads no price residual and no criterion.

It compares the delivered gas series the keeper's own code path produces from the
OLD committed CSV against the same path over the REPAIRED CSV, so the delta is
the one the LP would actually see — not a diff of the raw files.

Run: ``python3 scripts/probes/_nyiso234_gas_repair_footprint.py <old.csv> <new.csv>``
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

YEARS = (2022, 2023, 2024, 2025)
LIVE = Path("data/raw/gas-prices/transco_z6_ny_daily.csv")


def _series(year: int) -> np.ndarray:
    """The delivered gas series the keeper's own path builds for ``year``."""
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.data.fuel import hubs

    for mod in (hubs,):
        for name in ("_nyiso_hub_daily_gas_prices",):
            getattr(mod, name)
    cfg = ScenarioConfig(
        iso="NYISO", mode="backcast", hindcast=True, start_year=year, end_year=year
    )
    return np.asarray(
        hubs._nyiso_hub_daily_gas_prices(cfg, year, None, None), dtype=float
    )


def _with_csv(csv_path: Path) -> dict[int, np.ndarray]:
    """Build every year's series with ``csv_path`` installed as the live source."""
    backup = None
    if LIVE.exists():
        backup = Path(tempfile.mkdtemp()) / "live.csv"
        shutil.copy2(LIVE, backup)
    try:
        shutil.copy2(csv_path, LIVE)
        # the loaders cache on module import; re-import cleanly per install
        for m in [k for k in list(sys.modules) if k.startswith("market_sim")]:
            del sys.modules[m]
        return {y: _series(y) for y in YEARS}
    finally:
        if backup is not None:
            shutil.copy2(backup, LIVE)


def main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit(__doc__.strip().splitlines()[-1])
    old_csv, new_csv = Path(sys.argv[1]), Path(sys.argv[2])

    old = _with_csv(old_csv)
    new = _with_csv(new_csv)

    print("DELIVERED GAS SERIES — repaired vs committed, as the LP sees it\n")
    print(
        f"{'year':>5} {'hours moved':>12} {'% of yr':>8} {'mean |d|':>9} "
        f"{'max d':>8} {'sum |d| MMBtu-h':>16}  {'FOOTPRINT':>10}"
    )
    rows = []
    for y in YEARS:
        a, b = old[y], new[y]
        n = min(a.size, b.size)
        d = b[:n] - a[:n]
        moved = int((np.abs(d) > 1e-9).sum())
        foot = float(np.abs(d).sum())
        rows.append((y, foot))
        print(
            f"{y:>5} {moved:>12} {moved / n * 100:>7.1f}% {np.abs(d[d != 0]).mean() if moved else 0:>9.3f} "
            f"{d.max():>8.2f} {foot:>16,.0f}  {foot:>10,.0f}"
        )

    best = max(rows, key=lambda r: r[1])[0]
    print(
        f"\nSCREEN YEAR BY FOOTPRINT = {best} "
        "(largest summed |delta| in the delivered gas series).\n"
        "Chosen on the mechanism's own measured size, never on a residual — rule 29 (1)."
    )

    # Name the largest single days so the PRECOMMIT can cite them.
    y = best
    a, b = old[y], new[y]
    n = min(a.size, b.size)
    idx = pd.date_range(f"{y}-01-01", periods=n, freq="h")
    df = pd.DataFrame({"old": a[:n], "new": b[:n]}, index=idx)
    daily = df.resample("D").mean()
    daily["d"] = daily.new - daily.old
    top = daily.reindex(daily.d.abs().sort_values(ascending=False).index).head(8)
    print(f"\n{y} — the eight days that move most:")
    for ts, r in top.iterrows():
        print(f"  {ts.date()}  {r.old:>7.2f} -> {r.new:>7.2f}  ({r.d:+.2f} $/MMBtu)")


if __name__ == "__main__":
    main()
