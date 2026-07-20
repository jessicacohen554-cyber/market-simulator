"""CAISO-106 priority-1: state-conditioned INTERTIE ELASTICITY measurement (derive-first).

FINDING-caiso105 landed BOTH open λ-ladder residuals on ONE locus — the
model's WECC intertie supply is hub-anchored and too ELASTIC in both
directions:

  * BELLY (hod 10-14, over-price +6.0/+6.6/+4.3): in the deepest over-price
    quartile the model imports 3.3-4.2 GW at hub-linked prices while measured
    net imports are only 0.5-1.8 GW and measured RT ≤ 0 in 22-56 % of those
    hours (FINDING-caiso105 §4). The model props λ ABOVE a surplus-collapsed
    real market.
  * EVENING (hod 17-21, under-price -5.8/-4.9/-1.1): CA λ is hub-EQUALIZED to
    a WECC node in 76/100/97 % of the deepest-under-price quartile (the elastic
    import rung sets λ), while measured RT prints 8-40 $ ABOVE the measured
    hubs (FINDING-caiso103 §6). The model holds λ BELOW an exhausted real
    intertie.

This probe MEASURES the state-conditioned intertie conduct that the flat
hub-linked elastic supply curve misses — NO LP, NO mechanism, NO fitted
throttle (rule 1: the eventual ask must be a measured depth/direction
conditioned on an observable, forward-reproducible CAISO state, never a
residual-tuned haircut). It answers, per window and per observable-state
bucket:

  (a) DEEP-SURPLUS BELLY — what does the measured corridor actually do
      (net import DEPTH and DIRECTION, incl. the EXPORT tail) as CAISO drops
      into midday surplus? Conditioned on net-load percentile (the model's own
      observable surplus depth) and, as a cross-check, on hub-negative hours.
  (b) TIGHT EVENING — does the measured corridor net import SATURATE/exhaust
      as CAISO tightens, while CA RT separates ABOVE the hubs (the 8-40 $
      gap)? Conditioned on net-load percentile (the model's observable
      tightness).

Measured series, all on the model clock (interval-beginning, non-leap 8760):
  * corridor net import  — EIA-930 CISO BA-to-BA interchange, per corridor
    (WECC_PNW = COI/Path-66; WECC_DSW = Path-46/WOR) and TOTAL, via
    ``derive_caiso_import_tranches.corridor_net_import`` (negative = export).
  * hub DA LMP           — MALIN / PALOVRDE intertie prints
    (``hub_prices``; NaN in the 2023 Jan-Feb OASIS gap — masked out).
  * CA RT / DA LMP       — ``actual_lmp_hourly_CAISO.parquet``.
  * net-load             — EIA-930 CISO demand − solar − wind (the observable
    surplus/tightness state; the model computes the same quantity internally).

Derived candidate-envelope quantities (with the caiso-81/86/87 estimation-
stage honesty gates — CV ≤ 0.20 across years, LOYO mean-of-others ≤ 25 %) so
the ask can pre-register a MEASURED, year-stable structure rather than a fit:
  * EVENING import CEILING  = measured p95 TOTAL net import in the tightest
    net-load quintile of the evening (the exhaustion depth).
  * BELLY import CEILING    = measured p95 TOTAL net import in the deepest-
    surplus net-load quintile of the belly (near-zero / export).

Usage: .venv/bin/python scripts/probes/_caiso106_intertie_elasticity.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "data"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _caiso102_evening_merit import actual_rt, eia930_hourly  # noqa: E402
from derive_caiso_import_tranches import (  # noqa: E402
    corridor_net_import,
    hub_prices,
)

YEARS = (2023, 2024, 2025)
HOURS = 8760
BELLY = (10, 11, 12, 13, 14)
EVENING = (17, 18, 19, 20, 21)
N_BUCKET = 5  # net-load quintiles
CV_MAX = 0.20  # estimation-stage honesty gate (caiso-81/86/87 standard)
LOYO_MAX = 0.25


def _da_lmp(year: int) -> np.ndarray:
    """CA DA LMP (8760,) on the model clock."""
    import pandas as pd

    lmp = (
        REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_CAISO.parquet"
    )
    a = pd.read_parquet(lmp)
    a = a[a.year == year].sort_values("hour")
    v = np.full(HOURS, np.nan)
    v[a.hour.to_numpy(int)] = a.da.to_numpy(float)
    return v


def _load(year: int) -> dict[str, np.ndarray]:
    """All measured series for ``year`` on the model clock."""
    net = corridor_net_import().loc[year]
    hub = hub_prices().loc[year]
    e = eia930_hourly(year)
    pnw = net["WECC_PNW"].to_numpy(float)
    dsw = net["WECC_DSW"].to_numpy(float)
    return {
        "pnw": pnw,
        "dsw": dsw,
        "total": pnw + dsw,
        "malin": hub["MALIN"].to_numpy(float),
        "palo": hub["PALOVRDE"].to_numpy(float),
        "rt": actual_rt(year),
        "da": _da_lmp(year),
        "netload": e["demand"] - e["solar"] - e["wind"],
    }


def _stats(x: np.ndarray) -> str:
    """Compact depth/direction summary of a net-import sample."""
    x = x[np.isfinite(x)]
    if x.size == 0:
        return "  (no data)"
    return (
        f"mean {x.mean():+6.0f}  p05 {np.percentile(x, 5):+6.0f}  "
        f"p50 {np.percentile(x, 50):+6.0f}  p95 {np.percentile(x, 95):+6.0f}  "
        f"export {float((x < 0).mean()):4.0%}"
    )


def _window_table(d: dict[str, np.ndarray], hods, label: str, deep_low: bool) -> None:
    """Print the net-load-conditioned intertie table for one window.

    ``deep_low`` True  → bucket 1 is the LOWEST net-load (deep-surplus belly);
    ``deep_low`` False → bucket 1 is the HIGHEST net-load (tight evening).
    """
    hod = np.arange(HOURS) % 24
    win = np.isin(hod, hods)
    nl = d["netload"]
    ok = win & np.isfinite(nl) & np.isfinite(d["total"])
    nlw = nl[ok]
    edges = np.percentile(nlw, np.linspace(0, 100, N_BUCKET + 1))
    order = range(N_BUCKET) if not deep_low else range(N_BUCKET - 1, -1, -1)

    print(f"\n--- {label} (hod {hods[0]}-{hods[-1]}), net-load-conditioned ---")
    print(
        "bucket  net-load(GW)   n   TOTAL net import (MW)                        "
        "|  RT   PALO  RT-PALO  RTneg | model-imp*"
    )
    for rank, b in enumerate(order, start=1):
        lo, hi = edges[b], edges[b + 1]
        sel = ok & (nl >= lo) & (nl <= hi if b == N_BUCKET - 1 else nl < hi)
        tot = d["total"][sel]
        rt, palo = d["rt"][sel], d["palo"][sel]
        sep = rt - palo
        finm = np.isfinite(rt) & np.isfinite(palo)
        tag = (
            " DEEPEST-SURPLUS"
            if (deep_low and rank == 1)
            else " TIGHTEST"
            if (not deep_low and rank == 1)
            else ""
        )
        print(
            f"  B{rank}  [{lo / 1e3:5.1f},{hi / 1e3:5.1f}] {int(sel.sum()):4d}  "
            f"{_stats(tot)} | {np.nanmean(rt):5.0f} {np.nanmean(palo):5.0f} "
            f"{np.nanmean(sep[finm]):+7.1f} {float((rt < 0).mean()):4.0%}{tag}"
        )


def _hubneg_belly(d: dict[str, np.ndarray]) -> None:
    """Cross-check: belly corridor conduct conditioned on hub-negative state."""
    hod = np.arange(HOURS) % 24
    belly = np.isin(hod, BELLY)
    palo = d["palo"]
    finite = belly & np.isfinite(palo) & np.isfinite(d["total"])
    for name, mask in (
        ("PALO < 0 (hub-negative)", finite & (palo < 0.0)),
        ("PALO in [0,15)", finite & (palo >= 0.0) & (palo < 15.0)),
        ("PALO >= 15", finite & (palo >= 15.0)),
    ):
        n = int(mask.sum())
        if not n:
            continue
        print(
            f"  {name:24s} n={n:4d}  TOTAL {_stats(d['total'][mask])}  "
            f"RTneg {float((d['rt'][mask] < 0).mean()):4.0%}"
        )


def _gate(name: str, vals: dict[int, float]) -> bool:
    """caiso-81/86/87 CV + LOYO honesty gate on a derived per-year quantity."""
    arr = np.array([vals[y] for y in YEARS], dtype=float)
    cv = float(np.std(arr) / np.mean(arr)) if np.mean(arr) else float("nan")
    g_cv = np.isfinite(cv) and cv <= CV_MAX
    print(
        f"\n  {name}: "
        + " ".join(f"{y}={vals[y]:,.0f}" for y in YEARS)
        + f"  |  CV {cv:.3f} ({'PASS' if g_cv else 'FAIL'})"
    )
    g_loyo = True
    for held in YEARS:
        pred = float(np.mean([vals[y] for y in YEARS if y != held]))
        err = abs(pred - vals[held]) / abs(vals[held]) if vals[held] else float("inf")
        ok = err <= LOYO_MAX
        g_loyo = g_loyo and ok
        print(
            f"    LOYO {held}: mean-of-others {pred:,.0f} vs {vals[held]:,.0f}"
            f" -> {err:.1%} ({'PASS' if ok else 'FAIL'})"
        )
    return g_cv and g_loyo


def _ceiling(d: dict[str, np.ndarray], hods, deep_low: bool, pct: float) -> float:
    """Measured pXX TOTAL net import in the extreme net-load quintile."""
    hod = np.arange(HOURS) % 24
    win = np.isin(hod, hods)
    nl = d["netload"]
    ok = win & np.isfinite(nl) & np.isfinite(d["total"])
    nlw = nl[ok]
    edges = np.percentile(nlw, np.linspace(0, 100, N_BUCKET + 1))
    if deep_low:
        sel = ok & (nl <= edges[1])
    else:
        sel = ok & (nl >= edges[N_BUCKET - 1])
    return float(np.percentile(d["total"][sel], pct))


# Fixed net-load bands (GW) for the FORWARD-REPRODUCIBLE response envelope —
# absolute net-load thresholds (not year-relative quintiles), so the same band
# means the same physical system state in every year and in a forecast.
NL_BANDS_GW = [
    (-10.0, 5.0),
    (5.0, 10.0),
    (10.0, 15.0),
    (15.0, 20.0),
    (20.0, 25.0),
    (25.0, 30.0),
    (30.0, 45.0),
]


def _response_curve(d: dict[str, np.ndarray], hods, pct: float) -> dict[tuple, float]:
    """Measured pXX TOTAL net import per FIXED net-load band, for one window."""
    hod = np.arange(HOURS) % 24
    win = np.isin(hod, hods)
    nl = d["netload"]
    out: dict[tuple, float] = {}
    for lo, hi in NL_BANDS_GW:
        sel = (
            win
            & np.isfinite(nl)
            & np.isfinite(d["total"])
            & (nl >= lo * 1e3)
            & (nl < hi * 1e3)
        )
        out[(lo, hi)] = (
            float(np.percentile(d["total"][sel], pct))
            if sel.sum() >= 20
            else float("nan")
        )
    return out


def _band_gate(name: str, per_year: dict[int, dict[tuple, float]]) -> bool:
    """Per-band cross-year CV of the response function (the envelope's stability)."""
    print(f"\n  {name} — measured pXX TOTAL net import (MW) by FIXED net-load band:")
    print("    band(GW)      " + "".join(f"{y:>8}" for y in YEARS) + "     CV")
    all_ok = True
    for band in NL_BANDS_GW:
        vals = np.array([per_year[y][band] for y in YEARS], dtype=float)
        if np.isnan(vals).any():
            print(
                f"    [{band[0]:5.0f},{band[1]:4.0f})  "
                + "".join(f"{v:>8.0f}" for v in vals)
                + "   (sparse)"
            )
            continue
        # CV on the ABSOLUTE spread relative to the band's own scale; for bands
        # that straddle zero (export<->import) an absolute std in MW is the
        # honest stability read (a ratio CV explodes near zero crossing).
        std = float(np.std(vals))
        mean = float(np.mean(vals))
        cv = std / abs(mean) if abs(mean) > 500 else float("nan")
        # near a zero crossing, gate on absolute MW spread instead (<= 750 MW)
        ok = (np.isfinite(cv) and cv <= CV_MAX) or (
            not np.isfinite(cv) and std <= 750.0
        )
        all_ok = all_ok and ok
        cvs = f"{cv:.2f}" if np.isfinite(cv) else f"±{std:.0f}MW"
        print(
            f"    [{band[0]:5.0f},{band[1]:4.0f})  "
            + "".join(f"{v:>8.0f}" for v in vals)
            + f"   {cvs} {'ok' if ok else 'FAIL'}"
        )
    return all_ok


def main() -> int:
    data = {y: _load(y) for y in YEARS}

    for y in YEARS:
        d = data[y]
        print(f"\n===================== {y} =====================")
        _window_table(d, BELLY, "BELLY / deep-surplus", deep_low=True)
        print("  belly hub-negative cross-check:")
        _hubneg_belly(d)
        _window_table(d, EVENING, "EVENING / tight", deep_low=False)

    # --- derived candidate-envelope quantities + honesty gates -------------
    print("\n\n========== DERIVED CANDIDATE ENVELOPE (honesty gates) ==========")
    ev_ceiling = {y: _ceiling(data[y], EVENING, deep_low=False, pct=95) for y in YEARS}
    be_ceiling = {y: _ceiling(data[y], BELLY, deep_low=True, pct=95) for y in YEARS}
    g1 = _gate(
        "EVENING tight import CEILING (p95 TOTAL, tightest NL quintile)", ev_ceiling
    )
    g2 = _gate(
        "BELLY deep-surplus import CEILING (p95 TOTAL, deepest NL quintile)", be_ceiling
    )
    print(
        f"\n  quintile-based ceilings: evening {'PASS' if g1 else 'FAIL'} / "
        f"belly {'PASS' if g2 else 'FAIL'}"
    )

    # --- FORWARD-REPRODUCIBLE net-load-response envelope (fixed GW bands) ---
    print(
        "\n\n===== NET-LOAD-RESPONSE ENVELOPE (fixed GW bands, forward-reproducible) ====="
    )
    be_p50 = {y: _response_curve(data[y], BELLY, pct=50) for y in YEARS}
    be_p95 = {y: _response_curve(data[y], BELLY, pct=95) for y in YEARS}
    ev_p50 = {y: _response_curve(data[y], EVENING, pct=50) for y in YEARS}
    ev_p95 = {y: _response_curve(data[y], EVENING, pct=95) for y in YEARS}
    gb50 = _band_gate("BELLY p50", be_p50)
    gb95 = _band_gate("BELLY p95 (import ceiling)", be_p95)
    ge50 = _band_gate("EVENING p50", ev_p50)
    ge95 = _band_gate("EVENING p95 (import ceiling)", ev_p95)
    print(
        "\n  RESPONSE-ENVELOPE gate (per-band CV<=0.20 or ±<=750MW near zero):"
        f"\n    belly  p50 {'PASS' if gb50 else 'FAIL'} / p95 {'PASS' if gb95 else 'FAIL'}"
        f"\n    evening p50 {'PASS' if ge50 else 'FAIL'} / p95 {'PASS' if ge95 else 'FAIL'}"
    )
    print(
        "\n  READ: the response FUNCTION (net import at a FIXED system state) is the"
        "\n  forward-reproducible candidate — it absorbs the surplus-growth"
        "\n  non-stationarity that failed the year-relative quintile depth."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
