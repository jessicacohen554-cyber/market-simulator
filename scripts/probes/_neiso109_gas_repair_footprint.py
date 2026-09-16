"""THE REPAIRED AGT SERIES: what it changes, and WHERE it is largest (neiso-109, ZERO LP).

Phase 0 for the rule 29 ``[R-SCREEN]`` screen of the neiso-109 input repair to
``data/raw/gas-prices/algonquin_citygate_daily.csv`` (cross-hub contamination,
stale-republish misdating, and four unmatched EIA phrase variants — see
``docs/FINDING-neiso109-the-agt-series-is-contaminated-2026-09-16.md``).

Rule 29 (1) requires the screen year to be **named in the PRECOMMIT before the
screen runs**, and chosen where the mechanism's **own measured footprint is
largest** — NEVER where the residual is biggest, which would make the choice a
residual-driven one. This probe supplies that measurement and nothing else: it
reads no price residual and no criterion.

It compares the delivered gas series the keeper's own code path produces from the
OLD committed CSV against the same path over the REPAIRED CSV, so the delta is
the one the LP would actually see — not a diff of the raw files.

**THREE THINGS MAKE THE NEISO FOOTPRINT DIFFERENT FROM NYISO'S, and this probe
measures all three rather than assuming any of them.**

1. **The monthly anchor does NOT move.** NEISO's monthly AGT basis is an
   independent measured source (``gas_basis_by_iso_month.csv``, the ISO-NE MA gas
   index), not a quantity recomputed from these dailies the way NYISO's was. The
   daily leg is additively mean-preserved to it in every branch, so each month's
   mean is ``hh_m + b_m`` whatever the AGT prints say. The repair is therefore
   ONE-STEP — a pure within-month reshaping — and this probe ASSERTS the
   invariant per month rather than trusting it (``--check-mean-preservation``).
2. **A global price ceiling couples the years.** The Transco-shape fallback is
   capped at ``max`` over the WHOLE AGT print record (``hubs`` line ~1234), so a
   corrected print in any year can move the cap in every OTHER year's sparse
   months. Reported separately below.
3. **Five months have <2 AGT prints and borrow their shape from the measured
   Transco Z6 NY daily basis** — the series NYISO's own repair just changed. Two
   of them (2023-12, 2024-12) are inside NEISO's registered years, so part of
   this lane's control has already moved with no NEISO input touched. Reported as
   its own column so the PRECOMMIT can state it.

Run:
    .venv/bin/python scripts/probes/_neiso109_gas_repair_footprint.py OLD.csv NEW.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

#: Every year NEISO's keeper + its folded touchpoint run carry (rule 35 (b): the
#: registry year union, enumerated before anything is pruned).
YEARS = (2020, 2021, 2022, 2023, 2024, 2025)


def _with_csv(csv_path: Path) -> tuple[dict[int, np.ndarray], float, dict[int, list[int]]]:
    """Build every year's delivered AGT series from ``csv_path``.

    Repoints ``hubs.ALGONQUIN_DAILY_PATH`` and clears the loader's path-keyed
    caches, so **``data/raw`` is never written to** — the immutable-source-root
    rule holds even for a diagnostic, and the old and new series build in one
    process with no copy-restore dance a crash could leave half-done.

    Returns ``(series_by_year, global_price_ceiling, sparse_months_by_year)``.
    """
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.data.fuel import hubs

    prev = hubs.ALGONQUIN_DAILY_PATH

    def _clear() -> None:
        hubs._ALGONQUIN_DAILY_CACHE.clear()
        hubs._ALGONQUIN_DAILY_CLEAN_CACHE.clear()

    try:
        hubs.ALGONQUIN_DAILY_PATH = csv_path
        _clear()
        all_agt = hubs._algonquin_daily(None)
        ceiling = max(
            (p for yr in all_agt.values() for mo in yr.values() for p in mo.values()),
            default=float("inf"),
        )
        out: dict[int, np.ndarray] = {}
        sparse: dict[int, list[int]] = {}
        for year in YEARS:
            cfg = ScenarioConfig(
                iso="NEISO",
                mode="backcast",
                hindcast=True,
                start_year=year,
                end_year=year,
            )
            series = hubs.iso_hub_daily_gas_prices(cfg, year, None, None)
            out[year] = np.asarray(series, dtype=float)
            basis = hubs.load_winter_gas_basis(cfg, year)
            prints = all_agt.get(year, {})
            sparse[year] = [
                m
                for m in range(1, 13)
                if basis is not None
                and not np.isnan(basis[m - 1])
                and basis[m - 1] > 0
                and len(prints.get(m, {})) < 2
            ]
        return out, float(ceiling), sparse
    finally:
        hubs.ALGONQUIN_DAILY_PATH = prev
        _clear()


def _model_day_index(n_hours: int) -> np.ndarray:
    """Day-of-year (0-based) for each hour, on the MODEL's calendar.

    The model runs a fixed 365-day year in EVERY year (rule 8 ``[R-8760]``:
    ``config.hours`` is 8760 and ``hubs._DAYS_IN_MONTH`` sums to 365, with no
    Feb-29 branch), so a leap year's hours do NOT line up with
    ``pd.date_range(..., freq="h")``. Labelling 2020/2024 from a real calendar
    shifts every month after February by one day and makes a perfectly
    mean-preserving construction look like it moved the monthly mean by
    ~0.07 $/MMBtu. Build the index from the model's own month lengths instead.
    """
    return np.arange(n_hours) // 24


def _model_month_index(n_hours: int) -> np.ndarray:
    """Calendar month (1-12) for each hour, on the model's fixed 365-day year."""
    from market_sim.data.fuel.hubs import _DAYS_IN_MONTH

    months = np.repeat(np.arange(1, 13), [d * 24 for d in _DAYS_IN_MONTH])
    return months[:n_hours]


def _monthly_means(arr: np.ndarray, n: int) -> pd.Series:
    """Month means of an hourly series on the model's calendar."""
    return pd.Series(arr[:n]).groupby(_model_month_index(n)).mean()


def main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit(
            "usage: _neiso109_gas_repair_footprint.py OLD.csv NEW.csv"
        )
    old_csv, new_csv = Path(sys.argv[1]), Path(sys.argv[2])

    old, old_ceiling, old_sparse = _with_csv(old_csv)
    new, new_ceiling, new_sparse = _with_csv(new_csv)

    print("DELIVERED AGT GAS SERIES — repaired vs committed, as the LP sees it\n")
    print(
        f"{'year':>5} {'hrs moved':>10} {'% of yr':>8} {'mean |d|':>9} "
        f"{'max +d':>8} {'min -d':>8} {'sum |d|':>14}  {'sparse months':>14}"
    )
    rows: list[tuple[int, float]] = []
    for y in YEARS:
        a, b = old[y], new[y]
        n = min(a.size, b.size)
        d = b[:n] - a[:n]
        d = np.where(np.isnan(d), 0.0, d)
        moved = int((np.abs(d) > 1e-9).sum())
        foot = float(np.abs(d).sum())
        rows.append((y, foot))
        print(
            f"{y:>5} {moved:>10} {moved / n * 100:>7.1f}% "
            f"{(np.abs(d[d != 0]).mean() if moved else 0.0):>9.3f} "
            f"{d.max():>8.2f} {d.min():>8.2f} {foot:>14,.1f}  "
            f"{str(new_sparse[y]):>14}"
        )

    best = max(rows, key=lambda r: r[1])[0]
    print(
        f"\nSCREEN YEAR BY FOOTPRINT = {best} "
        "(largest summed |delta| in the delivered gas series).\n"
        "Chosen on the mechanism's own measured size, never on a residual — rule 29 (1)."
    )

    # ---- invariant 1: mean preservation, asserted per month -----------------
    print("\nMEAN-PRESERVATION CHECK (each month's mean must be unchanged):")
    worst = 0.0
    for y in YEARS:
        n = min(old[y].size, new[y].size)
        mo_o = _monthly_means(old[y], n)
        mo_n = _monthly_means(new[y], n)
        dd = (mo_n - mo_o).abs()
        dd = dd[~dd.isna()]
        worst = max(worst, float(dd.max()) if len(dd) else 0.0)
        flag = "OK" if (len(dd) == 0 or dd.max() < 1e-9) else "** MOVED **"
        print(f"  {y}: max |Δ monthly mean| = {(dd.max() if len(dd) else 0.0):.3e}  {flag}")
    print(
        f"  worst over all years/months: {worst:.3e} $/MMBtu\n"
        "  -> the repair is a WITHIN-MONTH RESHAPING only. The annual mean, and so\n"
        "     the frozen gas_offer_margin_anchor derived from it, does not move."
        if worst < 1e-9
        else f"  worst {worst:.3e} — mean preservation BROKEN, investigate before screening."
    )

    # ---- invariant 2: the global price ceiling ------------------------------
    print(
        f"\nGLOBAL AGT PRICE CEILING (caps the Transco-shape borrow in sparse months):"
        f"\n  old {old_ceiling:.4f} -> new {new_ceiling:.4f} $/MMBtu "
        f"({'UNCHANGED' if abs(new_ceiling - old_ceiling) < 1e-9 else 'MOVED — couples every year'})"
    )
    print(f"  sparse (<2 print, positive-basis) months, OLD: {old_sparse}")
    print(f"  sparse (<2 print, positive-basis) months, NEW: {new_sparse}")

    # ---- the days that move most, for the PRECOMMIT to cite -----------------
    from market_sim.data.fuel.hubs import _DAYS_IN_MONTH

    labels: list[str] = []
    for mi, nd in enumerate(_DAYS_IN_MONTH, start=1):
        labels += [f"{mi:02d}-{dd:02d}" for dd in range(1, nd + 1)]
    for y in (best,):
        a, b = old[y], new[y]
        n = min(a.size, b.size)
        daily = (
            pd.DataFrame({"old": a[:n], "new": b[:n]})
            .groupby(_model_day_index(n))
            .mean()
        )
        daily["d"] = daily.new - daily.old
        top = daily.reindex(daily.d.abs().sort_values(ascending=False).index).head(10)
        print(f"\n{y} — the ten days that move most (model calendar, 365-day):")
        for di, r in top.iterrows():
            print(
                f"  {y}-{labels[int(di)]}  {r.old:>7.2f} -> {r.new:>7.2f}  "
                f"({r.d:+.2f} $/MMBtu)"
            )


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
    main()
