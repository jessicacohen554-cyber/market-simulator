"""Reconstruct ``eia_generation_profiles.parquet`` from committed EIA-930 — VERIFY ONLY.

``data/raw/eia-930/eia_generation_profiles.parquet`` (per-ISO, per-fuel,
8760-hour normalized generation distributions, 2021-2025) has no producer in
the repo: it was hand-assembled (``data/raw/eia-930/README.md``). This script
is the reconstruction attempt of session I-NYISO (2026-09-24), written to
answer one question before any 2019/2020 row is emitted: **can the committed
2021-2025 rows be reproduced byte-identically from committed EIA-930
sources?** It never writes the artifact; it only reports the diff
(``docs/handoffs/FINDING-i-nyiso-2019-2021-intake-2026-09-24.md``).

The table is two constructions stacked, recovered from the committed rows
(every clause measured against them, none chosen for fit). Both read the
EIA-930 BALANCE bulk archive ``Net Generation (MW) from <fuel>`` of the ISO's
balancing authority (legacy and 2024-H2+ split taxonomies coalesced row by
row), or the per-BA ``eia-930-hourly/<BA> hourly.parquet`` extract:

``local6`` — CAISO / ERCOT / PJM / NYISO / NEISO
    * clock: the first 8,760 LOCAL wall-clock hours, row ``i`` = the hour
      ENDING at local ``i:00`` (row 0 is the prior year's last hour); a leap
      year keeps Feb 29 and so loses Dec 31;
    * the source stops at UTC hour-END ``<year>-12-31T0<cut>`` and every later
      hour — plus the spring-DST gap hour — is forward-filled;
    * value = round(series / series.sum(), 6); an all-zero series (NYIS
      solar) is the uniform ``round(1/8760, 6)``.

``utc10`` — MISO / SPP
    * clock: UTC hour-END stamps ``<year>-01-01T00`` … ``<year>-12-31T23``
      with Feb 29 dropped (the repo's non-leap convention — unlike
      ``local6``); missing hours are 0;
    * value = round(series / series.sum(), 10).

Not constructed here (no EIA-930 series): ``offshore_wind`` (a constant
profile), CAISO ``geothermal``, NYISO ``solar_proxy``.

Run::

    python scripts/data/reconstruct_eia_generation_profiles.py [--json out.json]
"""

from __future__ import annotations

import argparse
import functools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from market_sim.config.paths import EIA_930_DIR, EIA_HOURLY_DIR  # noqa: E402

TABLE = EIA_930_DIR / "eia_generation_profiles.parquet"
HOURS = 8760

#: Model ISO -> (EIA-930 BA, IANA zone of the BA's local clock, construction).
ISO_BA: dict[str, tuple[str, str, str]] = {
    "CAISO": ("CISO", "America/Los_Angeles", "local6"),
    "ERCOT": ("ERCO", "America/Chicago", "local6"),
    "PJM": ("PJM", "America/New_York", "local6"),
    "NYISO": ("NYIS", "America/New_York", "local6"),
    "NEISO": ("ISNE", "America/New_York", "local6"),
    "MISO": ("MISO", "America/Chicago", "utc10"),
    "SPP": ("SWPP", "America/Chicago", "utc10"),
}

#: Table fuel -> BALANCE column sets (legacy taxonomy, then the 2024-H2+
#: split taxonomy whose columns are summed back to the legacy fuel).
BALANCE_COLUMNS: dict[str, tuple[tuple[str, ...], ...]] = {
    "solar": (
        ("Solar",),
        (
            "Solar without Integrated Battery Storage",
            "Solar with Integrated Battery Storage",
        ),
    ),
    "wind": (
        ("Wind",),
        (
            "Wind without Integrated Battery Storage",
            "Wind with Integrated Battery Storage",
        ),
    ),
    "nuclear": (("Nuclear",),),
    "hydro": (
        ("Hydropower and Pumped Storage",),
        ("Hydropower Excluding Pumped Storage", "Pumped Storage"),
    ),
}
HOURLY_COLUMN = {
    "solar": "NG: SUN",
    "wind": "NG: WND",
    "nuclear": "NG: NUC",
    "hydro": "NG: WAT",
}
SOURCES = ("balance", "hourly")


@functools.lru_cache(maxsize=None)
def _balance_year(year: int) -> pd.DataFrame | None:
    """Both halves of one BALANCE year (None when absent)."""
    halves = [
        EIA_930_DIR / f"EIA930_BALANCE_{year}_{h}.parquet"
        for h in ("Jan_Jun", "Jul_Dec")
    ]
    frames = [pd.read_parquet(p) for p in halves if p.exists()]
    return pd.concat(frames, ignore_index=True) if frames else None


@functools.lru_cache(maxsize=None)
def _balance_series(ba: str, fuel: str, year: int) -> pd.Series:
    """UTC-hour-END indexed BALANCE series for ``ba``/``fuel`` over year±1."""
    parts = []
    for y in (year - 1, year, year + 1):
        b = _balance_year(y)
        if b is None:
            continue
        b = b[b["Balancing Authority"] == ba]
        # Coalesce the taxonomies row by row: a 2024 year concatenates an H1
        # half in the legacy columns and an H2 half in the split ones.
        v = pd.Series(np.nan, index=b.index)
        for cols in BALANCE_COLUMNS[fuel]:
            names = [f"Net Generation (MW) from {x}" for x in cols]
            if all(n in b.columns for n in names):
                v = v.fillna(b[names].astype(float).sum(axis=1, min_count=1))
        idx = pd.to_datetime(
            b["UTC Time at End of Hour"], format="%m/%d/%Y %I:%M:%S %p"
        )
        parts.append(pd.Series(v.to_numpy(), index=idx.to_numpy()))
    s = pd.concat(parts) if parts else pd.Series(dtype=float)
    return s[~s.index.duplicated()]


@functools.lru_cache(maxsize=None)
def _hourly_series(ba: str, fuel: str) -> pd.Series:
    """UTC-hour-END indexed series from the per-BA wide extract."""
    h = pd.read_parquet(EIA_HOURLY_DIR / f"{ba} hourly.parquet")
    s = pd.Series(
        h[HOURLY_COLUMN[fuel]].to_numpy(dtype=float), index=h["UTC time"].to_numpy()
    )
    return s[~s.index.duplicated()]


def _series(ba: str, fuel: str, year: int, source: str) -> pd.Series:
    return (
        _balance_series(ba, fuel, year)
        if source == "balance"
        else _hourly_series(ba, fuel)
    )


def reconstruct(
    iso: str, year: int, fuel: str, source: str = "balance", cut_hour: int = 1
) -> np.ndarray:
    """One reconstructed 8760 distribution (constructions: module docstring)."""
    ba, tz, construction = ISO_BA[iso]
    series = _series(ba, fuel, year, source)
    if construction == "utc10":
        full = pd.date_range(f"{year}-01-01", f"{year}-12-31 23:00", freq="h")
        utc_end = full[~((full.month == 2) & (full.day == 29))]
        v = np.nan_to_num(series.reindex(utc_end).to_numpy(dtype=float))
        total = v.sum()
        return np.round(v / total, 10) if total > 0 else np.zeros(HOURS)
    local = pd.date_range(f"{year}-01-01", periods=HOURS, freq="h")
    utc_end = (
        local.tz_localize(tz, nonexistent="NaT", ambiguous=True)
        .tz_convert("UTC")
        .tz_localize(None)
    )
    v = series.reindex(utc_end).to_numpy(dtype=float).copy()
    cut = pd.Timestamp(f"{year}-12-31") + pd.Timedelta(hours=cut_hour)
    v[np.asarray(utc_end > cut) | pd.isna(utc_end)] = np.nan
    v = pd.Series(v).ffill().fillna(0.0).to_numpy()
    total = v.sum()
    if total <= 0:
        return np.full(HOURS, round(1.0 / HOURS, 6))
    return np.round(v / total, 6)


def diff_table(cut_hour: int = 1) -> list[dict]:
    """Per-row diff of the best source against every committed row."""
    table = pd.read_parquet(TABLE)
    rows = []
    for (iso, year, fuel), grp in table.groupby(["iso", "year", "fuel"], sort=True):
        target = grp.sort_values("hour")["value"].to_numpy()
        entry: dict = {"iso": iso, "year": int(year), "fuel": fuel}
        if iso not in ISO_BA or fuel not in BALANCE_COLUMNS:
            entry.update(status="no-construction")
            rows.append(entry)
            continue
        best = None
        for source in SOURCES:
            got = reconstruct(iso, int(year), fuel, source, cut_hour)
            n_ok = int((got == target).sum())
            if best is None or n_ok > best[0]:
                best = (n_ok, source, float(np.abs(got - target).max()))
        entry.update(
            status="exact" if best[0] == HOURS else "diff",
            construction=ISO_BA[iso][2],
            source=best[1],
            hours_exact=best[0],
            max_abs_diff=best[2],
        )
        rows.append(entry)
    return rows


def main(argv: list[str] | None = None) -> int:
    """CLI: diff the reconstruction against every committed row; exit 1 unless all exact."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", type=Path, help="write the per-row diff report here")
    ap.add_argument(
        "--cut-utc-end",
        type=int,
        default=1,
        help="local6: last UTC hour-END kept on Dec 31 (default 1)",
    )
    args = ap.parse_args(argv)
    rows = diff_table(args.cut_utc_end)
    built = [r for r in rows if r["status"] != "no-construction"]
    exact = [r for r in built if r["status"] == "exact"]
    cells_ok = sum(r["hours_exact"] for r in built)
    print(
        f"rows: {len(rows)} committed, {len(built)} reconstructable from EIA-930, "
        f"{len(exact)} byte-exact; cells exact {cells_ok:,}/{HOURS * len(built):,} "
        f"({100 * cells_ok / max(HOURS * len(built), 1):.2f} %)"
    )
    for r in rows:
        if r["status"] != "exact":
            print("  ", json.dumps(r))
    if args.json:
        args.json.write_text(json.dumps(rows, indent=1))
    return 0 if len(exact) == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
