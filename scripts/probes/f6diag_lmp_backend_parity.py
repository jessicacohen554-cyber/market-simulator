"""F6-DIAG probe: measure WHICH neighbour-LMP backend is wrong, not merely that they differ.

``tests/curation/test_consume_lmp.py::test_clean_backed_lmp_matches_raw_loader`` is a
*parity* test: it can tell you the two ``neighbor_lmp_hourly`` backends disagree, but not
which side is broken. This probe adjudicates that by reducing the **first-party source**
(``data/raw/lmp-data/PJM_<year>_rt_da_monthly_lmps.csv``, the published PJM hourly nodal
export) independently, on both candidate clocks, and scoring each backend against it.

Reads only. Writes nothing but stdout/JSON to the path given by ``--out``. No solve, no
production behaviour, no committed artifact regenerated (CLAUDE.md rule 22 does not bind —
nothing is solved; rule 25 — every ISO's number is reported as its own, no transfer).

Sections
--------
R1  reproduce the parity failure and characterize the diff distribution
R2  score BOTH backends against the published source at the worst hours
R3  name the shape: segment agreement, the lag-1 test, the two DST singularities
R4  scope sweep across every ISO/market/year the clean tree carries

Usage::

    uv run python scripts/probes/f6diag_lmp_backend_parity.py --out /tmp/f6.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config import paths  # noqa: E402
from market_sim.data import neighbor_price as npx  # noqa: E402

_HOURS = 8760
_DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_MONTH_START = tuple(int(sum(_DAYS_IN_MONTH[:m]) * 24) for m in range(12))
# The ISO's fixed STANDARD-time offset — the chronological clock the model's 8760
# calendar rides (derive_actual_lmp._STD_TZ; eia_loader._eia_hourly_frame sorts by UTC).
_STD_TZ = {
    "PJM": "Etc/GMT+5",
    "NYISO": "Etc/GMT+5",
    "NEISO": "Etc/GMT+5",
    "CAISO": "Etc/GMT+8",
    "ERCOT": "Etc/GMT+6",
    "MISO": "Etc/GMT+5",
}


def _hoy_from_parts(month, day, hour) -> np.ndarray:
    """Non-leap 8760 hour-of-year from (month, day, hour); Feb 29 -> -1."""
    month = np.asarray(month)
    day = np.asarray(day)
    idx = (
        np.asarray([_MONTH_START[m - 1] for m in month])
        + (day - 1) * 24
        + np.asarray(hour)
    )
    return np.where((month == 2) & (day == 29), -1, idx)


def _dense_mean(hoy: np.ndarray, values: np.ndarray) -> np.ndarray:
    """Mean of ``values`` per hour-of-year slot on a dense 8760 array (NaN where empty)."""
    ok = hoy >= 0
    g = pd.Series(np.asarray(values, float)[ok]).groupby(np.asarray(hoy)[ok]).mean()
    return g.reindex(range(_HOURS)).to_numpy(float)


# ---------------------------------------------------------------------------
# The independent third-party reduction: the published PJM CSV, both clocks
# ---------------------------------------------------------------------------
def source_series(year: int, run: str = "rt") -> dict[str, np.ndarray | int]:
    """Reduce the published PJM hourly nodal export to a hub mean on BOTH clocks.

    Returns ``std`` (UTC -> fixed EST, the chronological model clock), ``prev``
    (the ``datetime_beginning_ept`` prevailing wall clock), the per-slot row counts
    on each clock, and the node count. Neither backend is consulted.
    """
    path = paths.RAW_DATA_DIR / "lmp-data" / f"PJM_{year}_rt_da_monthly_lmps.csv"
    fmt = "%m/%d/%Y %I:%M:%S %p"
    df = pd.read_csv(
        path,
        usecols=[
            "datetime_beginning_utc",
            "datetime_beginning_ept",
            "pnode_name",
            f"total_lmp_{run}",
        ],
    )
    utc = pd.DatetimeIndex(
        pd.to_datetime(df["datetime_beginning_utc"], format=fmt, utc=True)
    )
    std = utc.tz_convert(_STD_TZ["PJM"])
    hoy_std = np.where(
        np.asarray(std.year) == year, _hoy_from_parts(std.month, std.day, std.hour), -1
    )
    ept = pd.DatetimeIndex(pd.to_datetime(df["datetime_beginning_ept"], format=fmt))
    hoy_prev = np.where(
        np.asarray(ept.year) == year, _hoy_from_parts(ept.month, ept.day, ept.hour), -1
    )
    v = df[f"total_lmp_{run}"].to_numpy(float)
    cnt_std = pd.Series(1, index=hoy_std)[lambda s: s.index >= 0].groupby(level=0).sum()
    cnt_prev = (
        pd.Series(1, index=hoy_prev)[lambda s: s.index >= 0].groupby(level=0).sum()
    )
    return {
        "std": _dense_mean(hoy_std, v),
        "prev": _dense_mean(hoy_prev, v),
        "n_std": cnt_std.reindex(range(_HOURS)).fillna(0).to_numpy(int),
        "n_prev": cnt_prev.reindex(range(_HOURS)).fillna(0).to_numpy(int),
        "n_nodes": int(df["pnode_name"].nunique()),
        "n_rows": int(len(df)),
        "path": str(path),
    }


def _stamp(hoy: int, year: int, tz: str) -> str:
    """Human-readable ``tz`` timestamp of a non-leap 8760 slot."""
    m = int(np.searchsorted(np.asarray(_MONTH_START[1:] + (_HOURS,)), hoy, "right"))
    d, h = divmod(hoy - _MONTH_START[m], 24)
    return f"{year}-{m + 1:02d}-{d + 1:02d} {h:02d}:00 {tz}"


def _agree(a: np.ndarray, b: np.ndarray, tol: float = 1e-2) -> dict:
    """Max/mean abs difference and exceedance count over the shared finite support."""
    ok = np.isfinite(a) & np.isfinite(b)
    d = np.abs(a[ok] - b[ok])
    return {
        "n": int(ok.sum()),
        "max": float(d.max()) if d.size else float("nan"),
        "mean": float(d.mean()) if d.size else float("nan"),
        "n_gt_tol": int((d > tol).sum()),
        "argmax_hoy": int(np.flatnonzero(ok)[int(d.argmax())]) if d.size else -1,
    }


def sweep() -> list[dict]:
    """Backend agreement for every clean ``lmp`` partition with a raw counterpart.

    Establishes SCOPE — whether the disagreement is PJM-specific or shared curation
    infrastructure. Purely input-vs-input: no model output is produced, scored or
    registered, so no holdout tier is spent (CLAUDE.md rule 22, "what is held out is the
    SCORE, never the DATA"). Rule 25: each ISO's row stands on its own; no verdict is
    transferred between ISOs.
    """
    rows: list[dict] = []
    root = paths.CLEAN_DIR / "lmp"
    for part in sorted(root.glob("*/*/lmp_*.parquet")):
        iso, market = part.parent.parent.name, part.parent.name
        year = int(part.stem.split("_")[1])
        run = "da" if market == "DAM" else "rt"
        raw = npx._neighbor_lmp_raw(iso, year, run)
        if raw is None:
            rows.append(
                {
                    "iso": iso,
                    "market": market,
                    "year": year,
                    "status": "no raw counterpart",
                }
            )
            continue
        clean = npx._neighbor_lmp_clean(iso, year, run, market)
        if clean is None:
            rows.append(
                {
                    "iso": iso,
                    "market": market,
                    "year": year,
                    "status": "clean read failed",
                }
            )
            continue
        if np.isnan(raw).all():
            rows.append(
                {
                    "iso": iso,
                    "market": market,
                    "year": year,
                    "status": "raw column all-NaN",
                }
            )
            continue
        # DST window on the ISO's own fixed-standard clock (US rules: 2nd Sun Mar
        # 02:00 -> 1st Sun Nov 01:00 standard). Derived, not hardcoded per year.
        mar = pd.Timestamp(year=year, month=3, day=1)
        nov = pd.Timestamp(year=year, month=11, day=1)
        d_mar = 8 + (6 - mar.dayofweek) % 7  # 2nd Sunday of March
        d_nov = 1 + (6 - nov.dayofweek) % 7  # 1st Sunday of November
        lo = _MONTH_START[2] + (d_mar - 1) * 24 + 2
        hi = _MONTH_START[10] + (d_nov - 1) * 24 + 1
        overall = _agree(raw, clean)
        rows.append(
            {
                "iso": iso,
                "market": market,
                "year": year,
                "status": "compared",
                "max_abs_diff": round(overall["max"], 4),
                "mean_abs_diff": round(overall["mean"], 4),
                "n_gt_1e-2": overall["n_gt_tol"],
                "outside_DST_max": round(
                    max(
                        _agree(raw[:lo], clean[:lo])["max"],
                        _agree(raw[hi:], clean[hi:])["max"],
                    ),
                    6,
                ),
                "inside_DST_n_gt_1e-2": _agree(raw[lo:hi], clean[lo:hi])["n_gt_tol"],
                "lag1_max": round(
                    _agree(raw[lo : hi - 1], clean[lo + 1 : hi])["max"], 6
                ),
            }
        )
    return rows


# The hub definition each raw realized product actually carries
# (scripts/data/derive_actual_lmp.py). The clean backend ignores all of this and
# takes a simple mean over EVERY node in the partition.
_RAW_HUB_DEF: dict[str, dict] = {
    # PJM: mean of the 12 trading hubs = every node in the clean partition.
    "PJM": {"nodes": None, "weights": None},
    # NEISO: the .H.INTERNAL_HUB sheet alone, NOT the zone mean.
    "NEISO": {"nodes": ("ISO NE CA",), "weights": None},
    # NYISO: the 11 INTERNAL zones; the 4 external proxy buses are excluded.
    "NYISO": {
        "nodes": (
            "WEST",
            "GENESE",
            "CENTRL",
            "NORTH",
            "MHK VL",
            "CAPITL",
            "HUD VL",
            "MILLWD",
            "DUNWOD",
            "N.Y.C.",
            "LONGIL",
        ),
        "weights": None,
    },
    # CAISO: the 3 trading hubs LOAD-WEIGHTED by zone share, not a simple mean.
    "CAISO": {
        "nodes": None,
        "weights": {
            "TH_NP15_GEN-APND": 0.3969,
            "TH_ZP26_GEN-APND": 0.0646,
            "TH_SP15_GEN-APND": 0.5385,
        },
    },
}


def corrected_clean(iso: str, market: str, year: int, hub_def: bool) -> np.ndarray:
    """Re-reduce a clean ``lmp`` partition the way the raw product defines the hub.

    ``hub_def=False`` applies ONLY the clock repair — index on ``interval_start_utc``
    converted to the ISO's fixed standard offset, instead of the prevailing-clock
    ``interval_start_local`` the shipped consumer uses. ``hub_def=True`` additionally
    restricts/weights the nodes to the raw product's hub definition. Measures what each
    candidate fix would actually buy; nothing here is production code.
    """
    from scripts.lib.clean_io import read_clean

    df = read_clean(
        "lmp",
        iso=iso,
        market=market,
        year=year,
        columns=["interval_start_utc", "node", "lmp_usd_per_mwh"],
    )
    std = pd.DatetimeIndex(
        pd.to_datetime(df["interval_start_utc"], utc=True)
    ).tz_convert(_STD_TZ[iso])
    hoy = np.where(
        np.asarray(std.year) == year, _hoy_from_parts(std.month, std.day, std.hour), -1
    )
    spec = _RAW_HUB_DEF.get(iso, {"nodes": None, "weights": None})
    node = df["node"].to_numpy()
    v = df["lmp_usd_per_mwh"].to_numpy(float)
    if hub_def and spec["nodes"] is not None:
        keep = np.isin(node, np.asarray(spec["nodes"]))
        hoy, v = hoy[keep], v[keep]
    if hub_def and spec["weights"] is not None:
        w = np.asarray([spec["weights"].get(n, 0.0) for n in node], float)
        num = (
            _dense_mean(hoy, v * w)
            * pd.Series(1, index=hoy)[lambda s: s.index >= 0]
            .groupby(level=0)
            .sum()
            .reindex(range(_HOURS))
            .to_numpy()
        )
        den = (
            _dense_mean(hoy, w)
            * pd.Series(1, index=hoy)[lambda s: s.index >= 0]
            .groupby(level=0)
            .sum()
            .reindex(range(_HOURS))
            .to_numpy()
        )
        return npx._fill_hourly(
            np.divide(num, den, out=np.full(_HOURS, np.nan), where=den > 0)
        )
    return npx._fill_hourly(_dense_mean(hoy, v))


def fixcheck() -> list[dict]:
    """Score two candidate repairs of the clean-backed reduction against the raw product.

    ``clock_only`` = index on ``interval_start_utc``@std instead of the prevailing
    ``interval_start_local``. ``clock+hub`` = that, plus the raw product's own hub
    definition (node subset / load weights). Rule 25: per-ISO rows, no transfer.
    """
    rows: list[dict] = []
    for part in sorted((paths.CLEAN_DIR / "lmp").glob("*/*/lmp_*.parquet")):
        iso, market = part.parent.parent.name, part.parent.name
        year = int(part.stem.split("_")[1])
        run = "da" if market == "DAM" else "rt"
        raw = npx._neighbor_lmp_raw(iso, year, run)
        if raw is None or np.isnan(raw).all():
            continue
        shipped = npx._neighbor_lmp_clean(iso, year, run, market)
        rows.append(
            {
                "iso": iso,
                "market": market,
                "year": year,
                "shipped_max": round(_agree(raw, shipped)["max"], 4),
                "clock_only_max": round(
                    _agree(raw, corrected_clean(iso, market, year, False))["max"], 6
                ),
                "clock_plus_hub_max": round(
                    _agree(raw, corrected_clean(iso, market, year, True))["max"], 6
                ),
            }
        )
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--fixcheck",
        action="store_true",
        help="Score the two candidate repairs against the raw product.",
    )
    ap.add_argument(
        "--sweep",
        action="store_true",
        help="Scope sweep across every clean lmp partition, then exit.",
    )
    ap.add_argument("--iso", default="PJM")
    ap.add_argument("--year", type=int, default=2024)
    ap.add_argument("--run", default="rt")
    ap.add_argument("--market", default="RTM")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    if a.fixcheck:
        rows = fixcheck()
        print(json.dumps(rows, indent=2))
        if a.out:
            Path(a.out).write_text(json.dumps(rows, indent=2) + "\n")
        return
    if a.sweep:
        rows = sweep()
        print(json.dumps(rows, indent=2))
        if a.out:
            Path(a.out).write_text(json.dumps(rows, indent=2) + "\n")
        return
    out: dict = {"iso": a.iso, "year": a.year, "run": a.run, "market": a.market}

    # ---- R1 reproduce -----------------------------------------------------
    raw = npx._neighbor_lmp_raw(a.iso, a.year, a.run)
    clean = npx._neighbor_lmp_clean(a.iso, a.year, a.run, a.market)
    if raw is None or clean is None:
        raise SystemExit(f"backend missing: raw={raw is None} clean={clean is None}")
    d = np.abs(raw - clean)
    hmax = int(d.argmax())
    out["R1"] = {
        "max_abs_diff": float(d.max()),
        "argmax_hoy": hmax,
        "argmax_stamp_std": _stamp(hmax, a.year, "EST"),
        "n_gt_1e-2": int((d > 1e-2).sum()),
        "n_gt_1": int((d > 1.0).sum()),
        "mean_abs_diff": float(d.mean()),
        "raw_at_argmax": float(raw[hmax]),
        "clean_at_argmax": float(clean[hmax]),
    }

    # ---- R2 adjudicate against the published source -----------------------
    src = source_series(a.year, a.run)
    out["R2"] = {
        "source": src["path"],
        "n_nodes": src["n_nodes"],
        "n_rows": src["n_rows"],
        "raw_vs_source_STD": _agree(raw, src["std"]),
        "raw_vs_source_PREVAILING": _agree(raw, src["prev"]),
        "clean_vs_source_STD": _agree(clean, src["std"]),
        "clean_vs_source_PREVAILING": _agree(clean, src["prev"]),
    }
    worst = np.argsort(-d)[:12]
    out["R2"]["worst_hours"] = [
        {
            "hoy": int(h),
            "stamp_std": _stamp(int(h), a.year, "EST"),
            "raw": float(raw[h]),
            "clean": float(clean[h]),
            "published_at_this_STD_hour": float(src["std"][h]),
            "published_at_this_PREVAILING_label": float(src["prev"][h]),
            "abs_diff": float(d[h]),
        }
        for h in worst
    ]

    # ---- R3 shape ---------------------------------------------------------
    # 2024 US DST: begins 10 Mar 02:00 EST, ends 3 Nov 01:00 EST (std-clock slots).
    dst_lo = _MONTH_START[2] + (10 - 1) * 24 + 2
    dst_hi = _MONTH_START[10] + (3 - 1) * 24 + 1
    seg = {
        "pre_DST[0:%d]" % dst_lo: _agree(raw[:dst_lo], clean[:dst_lo]),
        "DST[%d:%d]" % (dst_lo, dst_hi): _agree(
            raw[dst_lo:dst_hi], clean[dst_lo:dst_hi]
        ),
        "post_DST[%d:]" % dst_hi: _agree(raw[dst_hi:], clean[dst_hi:]),
    }
    lag = _agree(raw[dst_lo : dst_hi - 1], clean[dst_lo + 1 : dst_hi])
    out["R3"] = {
        "dst_window_std_slots": [int(dst_lo), int(dst_hi)],
        "segments": seg,
        "lag1_clean_k_vs_raw_k_minus_1_inside_DST": lag,
        "spring_forward_slot": {
            "hoy": int(dst_lo),
            "published_rows_on_STD_clock": int(src["n_std"][dst_lo]),
            "published_rows_on_PREVAILING_clock": int(src["n_prev"][dst_lo]),
        },
        "fall_back_slot": {
            "hoy": int(dst_hi),
            "published_rows_on_STD_clock": int(src["n_std"][dst_hi]),
            "published_rows_on_PREVAILING_clock": int(src["n_prev"][dst_hi]),
        },
        "prevailing_clock_slots_with_zero_rows": int((src["n_prev"] == 0).sum()),
        "std_clock_slots_with_zero_rows": int((src["n_std"] == 0).sum()),
    }

    print(json.dumps(out, indent=2))
    if a.out:
        Path(a.out).write_text(json.dumps(out, indent=2) + "\n")


if __name__ == "__main__":
    main()
