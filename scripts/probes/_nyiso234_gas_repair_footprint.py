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

import sys
from pathlib import Path

import numpy as np
import pandas as pd

YEARS = (2022, 2023, 2024, 2025)


def _with_csv(csv_path: Path, basis_path: Path | None = None) -> dict[int, np.ndarray]:
    """Build every year's delivered gas series from ``csv_path`` (+ ``basis_path``).

    Repoints the module constants ``hubs.TRANSCO_Z6_NY_DAILY_PATH`` and
    ``basis.nyiso.TRANSCO_IROQUOIS_MONTHLY_PATH`` and clears the loader's
    path-keyed caches, so **``data/raw`` is never written to** — the
    immutable-source-root rule holds even for a diagnostic, and the old and new
    series can be built in one process without a copy-restore dance that a crash
    could leave half-done.

    BOTH inputs matter and measuring only the daily one understates the change.
    The construction is mean-preserving against the MONTHLY hub level, so the
    repair moves the delivered series through two doors: the daily shape and the
    monthly anchor recomputed from it
    (``docs/FINDING-nyiso234b-the-gas-series-was-published-2026-09-14.md`` §5).

    **The monthly level enters through ``basis_path``, NOT through
    ``basis.nyiso.TRANSCO_IROQUOIS_MONTHLY_PATH``.** Repointing that constant was
    measured to be a NO-OP here (0 of 8,760 hours moved): the level the daily
    shape renormalizes to is resolved from ``gas_basis_by_iso_month.csv``, which
    is the function's own third argument. Swapping the constant instead of the
    argument silently compares a HYBRID baseline — old dailies against the NEW
    monthly level — and overstates nothing but measures the wrong thing.
    """
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.data.fuel import hubs
    from market_sim.data.fuel.basis import nyiso as ny_basis

    prev_daily = hubs.TRANSCO_Z6_NY_DAILY_PATH

    def _clear() -> None:
        hubs._TRANSCO_DAILY_CACHE.clear()
        hubs._TRANSCO_DAILY_DATED_CACHE.clear()
        for name in dir(ny_basis):
            obj = getattr(ny_basis, name, None)
            if name.endswith("_CACHE") and isinstance(obj, dict):
                obj.clear()

    try:
        hubs.TRANSCO_Z6_NY_DAILY_PATH = csv_path
        _clear()
        out = {}
        for year in YEARS:
            cfg = ScenarioConfig(
                iso="NYISO",
                mode="backcast",
                hindcast=True,
                start_year=year,
                end_year=year,
            )
            out[year] = np.asarray(
                hubs._nyiso_hub_daily_gas_prices(cfg, year, basis_path, None),
                dtype=float,
            )
        return out
    finally:
        hubs.TRANSCO_Z6_NY_DAILY_PATH = prev_daily
        _clear()


def main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit(__doc__.strip().splitlines()[-1])
    old_csv, new_csv = Path(sys.argv[1]), Path(sys.argv[2])
    old_basis = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    new_basis = Path(sys.argv[4]) if len(sys.argv) > 4 else None

    old = _with_csv(old_csv, old_basis)
    new = _with_csv(new_csv, new_basis)

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
