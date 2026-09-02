"""Derive MISO's seasonal SYSTEM RBDC curves from the committed published data.

Rebuilds the four normalized seasonal system demand curves that
``src/market_sim/config/capacity_market.py`` encodes as
``_MISO_RBDC_{SUMMER,FALL,WINTER,SPRING}_POINTS`` (capx D31, 2026-09-02) from
exactly two committed raw inputs:

* ``data/raw/capacity-market/demand-curve/miso/miso.csv`` — the digitized
  subregional PY2025-26 RBDC polylines (``curve_point`` rows appended by
  ``digitize_miso_rbdc_charts.py``; the published curves exist only as chart
  images) plus the published seasonal CONE caps and the annual North/Central
  net-CONE anchor.
* ``data/raw/capacity-market/auction-supply/miso/miso.csv`` — the PY2025-26
  subregional and System Initial PRMR operands (the normalization
  denominators).

Construction (documented reductions, in order):

1. Each subregional polyline whose chart top clipped below its published
   seasonal CONE cap (fall/winter/spring rise past their y-axes) is BRIDGED
   from its highest observed point up to the cap along the measured
   near-clip log-linear slope (the curves are near-exponential: log-linear
   R^2 0.99-1.00 on every observed segment); the summer panels observed
   their cap plateaus directly and are pinned at the published cap.
2. The SYSTEM curve is the horizontal (quantity) sum of the two subregional
   curves at a common price grid — the market's own total-demand
   construction absent a binding Sub-Regional Power Balance Constraint.
   (When the SRPBC binds and subregional prices separate, as Fall 2025 did
   at $91.60/$74.09, a single system curve cannot express the separation —
   the same representation class as the documented one-position limit; the
   aggregate reproduces that season's cleared point within ~4%.)
3. x is normalized by the System Initial PRMR (position 1.0 = the
   pre-auction requirement); y by the flat daily net-CONE
   (annual North/Central net-CONE / 365), the same normalization the
   existing seasonal-RBDC seam prices in.
4. The 500-point aggregate is compressed to <=16 points (greedy
   max-relative-error <=1%) and, for seasons whose charts reach ~$0 inside
   the plot (summer, spring), the tail is closed at the extrapolated zero;
   the fall/winter tails end at the chart edge and flat-clamp there
   (winter's last observed point is ~$7/MW-day at x~1.09 — the published
   curve approaches zero asymptotically and the chart window ends).

Validation at intake: the compressed system curves reproduce the four
seasonal cleared points (position -> ACP) at +0.1% / -3.5% / -1.1% / -1.0%
(summer/fall/winter/spring; fall carries the SRPBC reduction) and the
market's own seasonal revenue sum at its cleared positions within -0.4%
($78,743 vs $79,070.6 per MW-yr). The reconciliation test
(``tests/test_capacity_demand_curve.py``) recomputes this derivation and
asserts the capacity_market.py constants match it, so the encoded curves can
never drift from the committed data.

Run ``python scripts/data/derive_miso_rbdc_system_curves.py`` to print the
constants block. Re-derive only when the source data updates (rule 23
``[R-FROZEN-DERIVE]``) — e.g. a PY2026-27 posting intake — never on a
residual.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

SEASONS: tuple[str, ...] = ("summer", "fall", "winter", "spring")
_AREAS: tuple[str, ...] = ("North/Central", "South")
_PY = "2025-2026"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_operands(raw_root: Path | None = None) -> dict:
    """Load curve polylines, caps, PRMRs and the net-CONE anchor from raw CSVs."""
    raw_root = raw_root or (_repo_root() / "data" / "raw")
    dc = pd.read_csv(
        raw_root / "capacity-market" / "demand-curve" / "miso" / "miso.csv"
    )
    asup = pd.read_csv(
        raw_root / "capacity-market" / "auction-supply" / "miso" / "miso.csv"
    )

    dc_py = dc[dc["delivery_year"] == _PY]
    # digitized polylines: curve_point rows with point_index >= 1 (index 0 is
    # the posting's labeled clearing intersection, kept as its own anchor row)
    curves: dict[tuple[str, str], tuple[np.ndarray, np.ndarray]] = {}
    for season in SEASONS:
        for area in _AREAS:
            rows = dc_py[
                (dc_py["metric"] == "curve_point")
                & (dc_py["season"] == season)
                & (dc_py["area"] == area)
                & (dc_py["point_index"] >= 1)
            ].sort_values("point_index")
            if rows.empty:
                raise ValueError(f"no digitized curve_point rows for {area} {season}")
            curves[(season, area)] = (
                rows["x_value"].to_numpy() / 1000.0,  # MW -> GW
                rows["y_value"].to_numpy(),
            )
    # published seasonal CONE caps ($/MW-day) by area incl. "System"
    caps: dict[tuple[str, str], float] = {}
    for season in SEASONS:
        for area in (*_AREAS, "System"):
            row = dc_py[
                (dc_py["metric"] == "net_cone")
                & (dc_py["season"] == season)
                & (dc_py["area"] == area)
            ]
            if len(row) != 1:
                raise ValueError(f"expected 1 seasonal CONE row for {area} {season}")
            caps[(season, area)] = float(row["y_value"].iloc[0])
    # annual North/Central net-CONE anchor ($/MW-yr)
    anc = dc_py[
        (dc_py["metric"] == "net_cone")
        & (dc_py["season"].isna())
        & (dc_py["area"] == "North/Central")
    ]
    if len(anc) != 1:
        raise ValueError("expected 1 annual North/Central net_cone row")
    daily_net_cone = float(anc["y_value"].iloc[0]) / 365.0

    prmr: dict[tuple[str, str], float] = {}
    sup_py = asup[asup["planning_year"] == _PY]
    for season in SEASONS:
        for area in (*_AREAS, "System"):
            row = sup_py[
                (sup_py["metric"] == "initial_prmr")
                & (sup_py["season"] == season)
                & (sup_py["area"] == area)
            ]
            if len(row) != 1:
                raise ValueError(f"expected 1 initial_prmr row for {area} {season}")
            prmr[(season, area)] = float(row["value_mw"].iloc[0])
    return dict(curves=curves, caps=caps, prmr=prmr, daily_net_cone=daily_net_cone)


def _bridge_to_cap(gw: np.ndarray, usd: np.ndarray, cap: float):
    """Extend a clipped polyline to its published cap along the measured log slope."""
    if usd.max() >= 0.97 * cap:
        out = usd.copy()
        out[out >= 0.985 * cap] = cap  # pin the observed plateau at the cap
        out = np.minimum(out, cap)
        return gw, np.maximum.accumulate(out[::-1])[::-1]
    m = usd >= usd.max() / 4.0
    z = np.polyfit(gw[m], np.log(usd[m]), 1)
    gw_cap = (np.log(cap) - z[1]) / z[0]
    gw_b = np.linspace(gw_cap, gw[0], 8, endpoint=False)
    usd_b = np.exp(np.polyval(z, gw_b))
    return np.concatenate([gw_b, gw]), np.concatenate([usd_b, usd])


def _q_at(gw: np.ndarray, usd: np.ndarray, p: float) -> float:
    """Quantity demanded at price ``p`` on a monotone-decreasing polyline (GW)."""
    if p >= usd[0]:
        return float(gw[0])
    if p <= usd[-1]:
        return float(gw[-1])
    return float(np.interp(p, usd[::-1], gw[::-1]))


def _compress(x: np.ndarray, y: np.ndarray, max_pts: int = 16, rel_tol: float = 0.01):
    """Greedy point selection minimizing the polyline's max relative error."""
    n = len(x)
    keep = {0, n - 1}
    floor_ = max(y.max() * 0.002, 0.5)
    while len(keep) < max_pts:
        ks = sorted(keep)
        approx = np.interp(x, x[ks], y[ks])
        e = np.abs(approx - y) / np.maximum(y, floor_)
        i = int(np.argmax(e))
        if e[i] < rel_tol:
            break
        keep.add(i)
    ks = sorted(keep)
    return x[ks], y[ks]


def derive_system_curves(
    raw_root: Path | None = None,
) -> dict[str, tuple[tuple[float, float], ...]]:
    """Return {season: ((reserve_ratio, frac_of_daily_net_cone), ...)}.

    The exact point tuples encoded as capacity_market.py's
    ``_MISO_RBDC_<SEASON>_POINTS`` constants (4-decimal rounding applied here
    so the reconciliation test compares like with like).
    """
    ops = load_operands(raw_root)
    out: dict[str, tuple[tuple[float, float], ...]] = {}
    for season in SEASONS:
        nc = _bridge_to_cap(
            *ops["curves"][(season, "North/Central")],
            ops["caps"][(season, "North/Central")],
        )
        so = _bridge_to_cap(
            *ops["curves"][(season, "South")], ops["caps"][(season, "South")]
        )
        cap_sys = ops["caps"][(season, "System")]
        tail = max(min(nc[1][-1], so[1][-1]), 0.05)
        grid = np.geomspace(max(tail, 0.25), cap_sys, 500)
        q = np.array([_q_at(*nc, p) + _q_at(*so, p) for p in grid])
        x = q * 1000.0 / ops["prmr"][(season, "System")]
        fr = grid / ops["daily_net_cone"]
        order = np.argsort(x)
        x, fr = x[order], fr[order]
        cg, cu = _compress(x, fr)
        # seasons whose charts reach ~$0 in-window close at the extrapolated
        # zero; drop near-zero stragglers so x stays strictly ascending
        both_zero = (
            ops["curves"][(season, "North/Central")][1][-1] <= 4.0
            and ops["curves"][(season, "South")][1][-1] <= 4.0
        )
        if both_zero:
            z = np.polyfit(cu[-4:], cg[-4:], 1)
            x0 = float(np.polyval(z, 0.0))
            keepm = cg < x0 - 1e-4
            cg, cu = cg[keepm], cu[keepm]
            cg = np.append(cg, x0)
            cu = np.append(cu, 0.0)
        cu = np.minimum.accumulate(cu)
        # 4-decimal rounding for the encoded constants; drop rounding-collided
        # x duplicates (keep the first) so reserve_ratio stays strictly
        # ascending for evaluate_demand_curve
        pts: list[tuple[float, float]] = []
        for a, b in zip(cg, cu):
            ra, rb = round(float(a), 4), round(float(b), 4)
            if pts and ra <= pts[-1][0]:
                continue
            pts.append((ra, rb))
        # the tail point wins a collision (it carries the terminal value)
        if round(float(cg[-1]), 4) == pts[-1][0]:
            pts[-1] = (pts[-1][0], round(float(cu[-1]), 4))
        out[season] = tuple(pts)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.parse_args(argv)
    curves = derive_system_curves()
    for season, pts in curves.items():
        print(f"_MISO_RBDC_{season.upper()}_POINTS = (")
        for a, b in pts:
            print(f"    CapacityDemandCurvePoint({a:.4f}, {b:.4f}),")
        print(")")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
