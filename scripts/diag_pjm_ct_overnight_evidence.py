"""THROWAWAY DIAG (rule 15): resolve the CT overnight-reliability question.

Owner question (L-13 step 3): the ct_netload_drag binds only in hours [15,22)
on a net-load hinge (~90 GW). Do real PJM CT_PEAKER units ALSO run overnight
(hours 0-6) for reliability, and under what conditions (cold snaps, high
net-load)? If yes, the [15,22) window is too narrow and misses real structure;
if overnight CF is ~0, the window is correct.

Method: measured CAMPD pure-play PJM CT_PEAKER fleet CF (the exact model
CT_PEAKER plant codes, same series the drag is regressed from), pooled
2023-2025, cross-tabulated by:
  (a) hour-of-day x net-load decile  -- is there an overnight net-load response?
  (b) season x hour-block            -- is overnight running winter-only (cold)?
  (c) overnight (h0-5) net-load decile, with hour counts, vs the ramp window at
      the SAME net-load -- would extending the ramp hinge over-floor overnight?

NOT registered; no LP solve. Reads only measured CAMPD + EIA-930.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from scripts.derive_pjm_ct_netload_drag import (  # noqa: E402
    CT_EVENING_HOURS,
    HOURS,
    measured_ct_mw,
    model_ct_peaker_plants,
    pjm_net_load_mw,
)

YEARS = (2023, 2024, 2025)

# Season by hour-of-year (non-leap 8760 grid, local standard clock).
# Winter = Dec-Feb, Summer = Jun-Aug, Shoulder = the rest.
_MONTH_STARTS_H = np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30]) * 24


def _month_of_hoy(hours: int) -> np.ndarray:
    m = np.zeros(hours, dtype=int)
    for mi, start in enumerate(_MONTH_STARTS_H):
        m[start:] = mi  # 0-based month
    return m


def _season_of_hoy(hours: int) -> np.ndarray:
    mon = _month_of_hoy(hours)  # 0=Jan .. 11=Dec
    season = np.full(hours, "shoulder", dtype=object)
    season[np.isin(mon, [11, 0, 1])] = "winter"
    season[np.isin(mon, [5, 6, 7])] = "summer"
    return season


def _decile_edges(x: np.ndarray) -> np.ndarray:
    return np.percentile(x, np.arange(0, 101, 10))


def main() -> None:
    cf_list, nl_list, hod_list, season_list = [], [], [], []
    for year in YEARS:
        plants, nameplate = model_ct_peaker_plants(year)
        mw = measured_ct_mw(year, set(plants))
        nl = pjm_net_load_mw(year) / 1000.0  # GW
        cf = mw / nameplate
        hod = np.arange(HOURS) % 24
        cf_list.append(cf)
        nl_list.append(nl)
        hod_list.append(hod)
        season_list.append(_season_of_hoy(HOURS))
    cf = np.concatenate(cf_list)
    nl = np.concatenate(nl_list)
    hod = np.concatenate(hod_list)
    season = np.concatenate(season_list)

    start, end = CT_EVENING_HOURS
    print(f"=== PJM CT_PEAKER measured CF, pooled {YEARS} ({cf.size} h) ===")
    print(f"annual mean fleet CF {cf.mean():.4f}; drag ramp window [{start},{end})")
    print(
        f"net-load range {nl.min():.0f}-{nl.max():.0f} GW; hinge zero-cross 90.1 GW\n"
    )

    # ---- (a) hour-of-day x net-load decile ------------------------------
    edges = _decile_edges(nl)
    dec = np.clip(np.digitize(nl, edges[1:-1]), 0, 9)
    print("(a) mean CF by hour-of-day (rows) x net-load decile (cols, GW upper edge)")
    hdr = "  ".join(f"D{d}<{edges[d + 1]:.0f}" for d in range(10))
    print(f"  hod  {hdr}")
    for h in range(24):
        row = []
        for d in range(10):
            m = (hod == h) & (dec == d)
            row.append(f"{cf[m].mean():.3f}" if m.sum() >= 5 else "  .  ")
        tag = "*" if start <= h < end else (" o" if h < 6 else "  ")
        print(f"  {h:>2}{tag} " + "  ".join(f"{v:>6}" for v in row))
    print("  (* = ramp window [15,22);  o = overnight h0-5)\n")

    # ---- (b) season x hour-block ---------------------------------------
    blocks = [
        ("overnight 0-5", (hod >= 0) & (hod < 6)),
        ("morning 6-9", (hod >= 6) & (hod < 10)),
        ("midday 10-14", (hod >= 10) & (hod < 15)),
        ("ramp 15-21", (hod >= 15) & (hod < 22)),
        ("late 22-23", hod >= 22),
    ]
    print("(b) mean CF by season x hour-block")
    print(
        f"  {'block':<15} "
        + "  ".join(f"{s:>9}" for s in ("winter", "shoulder", "summer"))
    )
    for label, bm in blocks:
        cells = []
        for s in ("winter", "shoulder", "summer"):
            m = bm & (season == s)
            cells.append(f"{cf[m].mean():.3f}" if m.sum() else "  .  ")
        print(f"  {label:<15} " + "  ".join(f"{v:>9}" for v in cells))
    print()

    # ---- (c) overnight net-load response vs ramp at same net-load -------
    slope, intercept, cap = 0.01108, -0.9979, 0.46
    hinge = np.clip(slope * nl + intercept, 0.0, cap)
    on = (hod >= 0) & (hod < 6)
    rw = (hod >= start) & (hod < end)
    nl_edges = np.arange(60, 130, 10)
    print("(c) overnight (h0-5) vs ramp-window CF, and the ramp hinge, by net-load bin")
    print("  net-load(GW)   n_ovn  CF_overnight   n_ramp  CF_ramp   hinge_pred")
    for lo in nl_edges:
        hi = lo + 10
        bm = (nl >= lo) & (nl < hi)
        om, rm = bm & on, bm & rw
        h_pred = np.clip(slope * (lo + 5) + intercept, 0, cap)
        cf_o = f"{cf[om].mean():.3f}" if om.sum() else "  .  "
        cf_r = f"{cf[rm].mean():.3f}" if rm.sum() else "  .  "
        print(
            f"  {lo:>3}-{hi:<3}      {int(om.sum()):>6}   {cf_o:>10}   "
            f"{int(rm.sum()):>6}   {cf_r:>7}   {h_pred:>8.3f}"
        )
    print(
        "\n  Read: if CF_overnight << hinge_pred at high net-load, extending the\n"
        "  ramp hinge overnight would OVER-floor -- the [15,22) gate is correct\n"
        "  and any real overnight uptick is weaker & belongs to reserve/ORDC."
    )


if __name__ == "__main__":
    main()
