#!/usr/bin/env python
"""Derive the ERCOT ST_GAS net-load drag curve at SEASON grain (rule-22 grain fix).

The armed ERCOT drag curve (``gas_st_drag_slope_per_gw`` / ``_intercept`` /
``_cap`` = 0.00906 / −0.1376 / 0.34, ``docs/ercot-st-gas-netload-drag-2026-06.md``)
is a season-POOLED fit of the CAMPD overnight (23–05h low-price) ST_GAS
capacity factor on contemporaneous system net-load, 2023–2025. The ERCOT-90
direct CEMS measurement (`docs/handoffs/ercot-stgas-shoulder-2026-07.md` §3.3,
artifact ``ercot90_stgas_shoulder_measurement.json``) found a season-axis grain
limit of that same source evidence: at the same net-load, measured 2024–25
DJF steam commitment sits FAR below the pooled curve (model 1.6–1.9 GW vs
measured 0.6–1.1 GW in sub-$150 winter control hours, only 40–55 % of hours
above even an upper-bound floor reconstruction), while the pooled curve still
tracks on its own overnight terms (Spearman ρ 0.69/0.75). The pooled net-load
axis conflates the two net-load limbs (cold-snap winter mornings vs summer
afternoons) that carry DIFFERENT overnight commitment levels.

This is the rule-22 lane named by ERCOT-90 §4 / the ERCOT-91 charter: a
re-derive of the SAME curve from the SAME CAMPD source at season grain —
a grain fix with citation, never a residual re-tune. Nothing here reads a
model output, a price, or a residual.

Construction (each leg mirrors the sibling standing derives):

1. Measured side — CAMPD unit-level TX hourly gross for the model's own
   17-plant ERCOT ST_GAS fleet (``custom-bin-assignments.csv``; the two split
   facilities unit-routed by the model's own ``data.outages`` rules; CT/CC
   unit types dropped; ×0.95 net = ``campd.DEFAULT_PARASITIC_LOAD_PCT``) —
   imported from the ERCOT-90 measurement probe so the fleet definition is
   single-sourced. Only DRAG-COVERED plants (non-``ST_GAS_PEAKER_PLANTS``)
   enter the CF numerator; the denominator is the same drag-covered
   net-of-peak-tranche base the floor multiplies onto
   (``Σ nameplate × (1 − pct_peaking)``), so the fitted fraction lands in the
   exact coordinates ``fleet.apply_gas_st_netload_drag_floor`` applies.
2. Net-load — EIA-930 ERCO ``Demand − NG: WND − NG: SUN`` (MW) on the model's
   fixed-CST non-leap 8760 clock (the ``derive_ercot_dam_cleared_share``
   convention; same EIA-930 wind+solar-actuals basis the original 2026-06
   derive cited).
3. Fit — per meteorological season (``SEASON_OF_MONTH``, the span/state
   artifact convention: 0=DJF, 1=MAM, 2=JJA, 3=SON), median overnight CF per
   2-GW net-load bin pooled over 2023–2025, hinge fit
   ``clip(slope·netGW + intercept, 0, cap)`` with the standing-family
   estimator (grid-search the knee, least-squares on bins at/above it, no
   scipy.optimize; cap = p95 of the season's overnight CF) — the exact
   functional form the floor applies, now per season. The pooled re-fit is
   printed as a consistency check against the armed scalars.

Both the trigger (net-load) and the season axis (calendar) regenerate for a
forward year and respond to changed conditions, so the seasonal curve stays
admissible in backcast AND forecast (CLAUDE.md rules 13/17). Zero parameters
fitted to a price or volume residual (rules 22/23: this artifact re-derives
only when the CAMPD/EIA-930 source data update).

Usage::

    python scripts/data/derive_ercot_stgas_drag_seasonal.py \
        [--years 2023 2024 2025] \
        [--out data/raw/_validation-source/ercot_stgas_drag_seasonal.json]

Apply via ``gas_st_drag_seasonal=True`` (default off) on an ERCOT run — the
floor owner ``fleet.apply_gas_st_netload_drag_floor`` swaps the pooled scalars
for this artifact's per-season coefficients (same mechanism id, same rows,
same all-hours window — a coefficient-grain fix inside the existing owner,
rule 19).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "data"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

from derive_ercot_dam_cleared_share import (  # noqa: E402
    EIA930_HOURLY,
    HOURS,
    _MONTH_START_HOUR,
    _STD_TZ,
)
from derive_ercot_shoulder_online_span import SEASON_OF_MONTH  # noqa: E402
from ercot90_stgas_shoulder_measure import (  # noqa: E402
    OVERNIGHT_END_H,
    OVERNIGHT_START_H,
    _MONTH_OF_HOY,
    _campd_st_hourly,
    _st_gas_plants,
)

DEFAULT_OUT = (
    REPO / "data" / "raw" / "_validation-source" / "ercot_stgas_drag_seasonal.json"
)

SEASON_NAMES = {0: "DJF", 1: "MAM", 2: "JJA", 3: "SON"}

# 2-GW net-load bins over the observed ERCOT range (the original 2026-06
# derive's bin width; net-load spans ~14-56 GW across 2023-2025).
_NL_BIN_EDGES_GW = np.arange(12, 60, 2)
# Minimum overnight hours for a (season, bin) cell to enter the fit — thin
# tail bins carry no stable median.
_MIN_CELL_HOURS = 12


def ercot_net_load_mw(year: int) -> np.ndarray:
    """ERCOT hourly net-load MW = EIA-930 ERCO Demand − wind − solar (8760).

    The ``derive_ercot_dam_cleared_share._netload_pct`` construction, returning
    LEVELS instead of percentile ranks: fixed-CST clock, Feb-29 dropped,
    duplicate stamps first-wins, gaps interpolated.
    """
    df = pd.read_parquet(EIA930_HOURLY)
    std = pd.DatetimeIndex(df["UTC time"]).tz_localize("UTC").tz_convert(_STD_TZ)
    ok = (std.year == year) & ~((std.month == 2) & (std.day == 29))
    idx = _MONTH_START_HOUR[std.month - 1] + (std.day - 1) * 24 + std.hour
    sub = df.loc[np.asarray(ok)].copy()
    sub["hoy"] = idx[np.asarray(ok)]
    sub = sub.groupby("hoy").first().reindex(range(HOURS))
    netload = (
        sub["Demand"].to_numpy(float)
        - sub["NG: WND"].to_numpy(float)
        - sub["NG: SUN"].to_numpy(float)
    )
    return pd.Series(netload).interpolate(limit_direction="both").to_numpy()


def _binned_median(nl_gw: np.ndarray, cf: np.ndarray) -> np.ndarray:
    """(center, median-CF) rows per 2-GW net-load bin with >= _MIN_CELL_HOURS."""
    rows = []
    for lo in _NL_BIN_EDGES_GW:
        m = (nl_gw >= lo) & (nl_gw < lo + 2)
        if m.sum() < _MIN_CELL_HOURS:
            continue
        rows.append((lo + 1.0, float(np.median(cf[m]))))
    return np.asarray(rows, dtype=float)


def _hinge_fit(binned: np.ndarray, cap: float) -> tuple[float, float, float]:
    """Hinge fit ``clip(s·x + b, 0, cap)`` on binned medians (NYISO estimator).

    Grid-search the knee over bin positions, least-squares on the bins at/above
    the knee (>= 4 bins), keep the (slope, intercept) minimizing SSE of the
    CLIPPED prediction over ALL bins. Returns (slope, intercept, sse).
    """
    best: tuple[float, float, float] | None = None
    for knee_i in range(max(1, len(binned) - 3)):
        seg = binned[knee_i:]
        if len(seg) < 4:
            break
        s, b = np.polyfit(seg[:, 0], seg[:, 1], 1)
        if s <= 0.0:
            continue
        pred = np.clip(s * binned[:, 0] + b, 0.0, cap)
        sse = float(((pred - binned[:, 1]) ** 2).sum())
        if best is None or sse < best[2]:
            best = (float(s), float(b), sse)
    if best is None:
        raise SystemExit("hinge fit found no positive-slope segment — inspect data")
    return best


def main() -> None:
    """Re-derive the season-resolved ERCOT ST_GAS drag curve and write the artifact."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    plants = _st_gas_plants()
    covered = plants[plants["drag_covered"]]
    base_mw = float(
        (covered["Nameplate_MW"] * (1.0 - covered["Pct_Peaking"] / 100.0)).sum()
    )
    print(
        f"drag-covered fleet: {len(covered)}/{len(plants)} plants, "
        f"floor base {base_mw:.0f} MW"
    )

    hod = np.arange(HOURS) % 24
    overnight = (hod >= OVERNIGHT_START_H) | (hod < OVERNIGHT_END_H)
    season_h = np.asarray(SEASON_OF_MONTH)[_MONTH_OF_HOY - 1]

    nl_gw_all: list[np.ndarray] = []
    cf_all: list[np.ndarray] = []
    season_all: list[np.ndarray] = []
    for year in args.years:
        meas, per_plant, notes = _campd_st_hourly(year, covered)
        for n in notes:
            print(f"  note {year}: {n}")
        nl = ercot_net_load_mw(year)
        cf = meas / base_mw
        rho = pd.Series(nl[overnight] / 1000.0).corr(
            pd.Series(cf[overnight]), method="spearman"
        )
        print(
            f"  {year}: measured {meas.sum() / 1e6:.2f} TWh net, overnight "
            f"Spearman(netload, CF) rho={rho:.2f}"
        )
        nl_gw_all.append(nl[overnight] / 1000.0)
        cf_all.append(cf[overnight])
        season_all.append(season_h[overnight])
    nl_gw = np.concatenate(nl_gw_all)
    cf = np.concatenate(cf_all)
    season = np.concatenate(season_all)

    seasons_out: dict[str, dict] = {}
    print("\n=== per-season overnight hinge fits (median CF per 2-GW bin) ===")
    for s in range(4):
        m = season == s
        binned = _binned_median(nl_gw[m], cf[m])
        cap = float(np.percentile(cf[m], 95))
        slope, intercept, sse = _hinge_fit(binned, cap)
        rho = float(pd.Series(nl_gw[m]).corr(pd.Series(cf[m]), method="spearman"))
        print(
            f"  {SEASON_NAMES[s]}: n={int(m.sum())} rho={rho:.2f} "
            f"slope {slope:.5f} intercept {intercept:+.4f} cap {cap:.3f} "
            f"zero-crossing {-intercept / slope:.1f} GW  SSE {sse:.4f}"
        )
        print("    bins  " + "  ".join(f"{c:.0f}:{v:.3f}" for c, v in binned))
        seasons_out[str(s)] = {
            "name": SEASON_NAMES[s],
            "slope_per_gw": round(slope, 5),
            "intercept": round(intercept, 4),
            "cap": round(cap, 3),
            "n_overnight_hours": int(m.sum()),
            "spearman_nl_vs_cf": round(rho, 3),
            "binned_median_cf": [[round(c, 1), round(v, 4)] for c, v in binned],
        }

    # Pooled consistency check against the armed 2026-06 scalars (printed,
    # recorded — never applied): same estimator on the season-pooled sample.
    binned_p = _binned_median(nl_gw, cf)
    cap_p = float(np.percentile(cf, 95))
    slope_p, icept_p, sse_p = _hinge_fit(binned_p, cap_p)
    print(
        f"\npooled re-fit check: slope {slope_p:.5f} intercept {icept_p:+.4f} "
        f"cap {cap_p:.3f} (armed keeper scalars: 0.00906 / -0.1376 / 0.34)"
    )

    out = {
        "_provenance": {
            "script": "scripts/data/derive_ercot_stgas_drag_seasonal.py",
            "iso": "ERCOT",
            "role": (
                "Season-resolved re-derive of the ERCOT ST_GAS net-load drag "
                "curve from its own CAMPD source (rule-22 grain fix; ERCOT-90 "
                "§3.3 season-axis finding, ERCOT-91 winter seam). Same "
                "mechanism owner (fleet.apply_gas_st_netload_drag_floor), "
                "same rows, same all-hours window — only the coefficient "
                "grain changes (per meteorological season instead of pooled)."
            ),
            "grain_fix_of": (
                "docs/ercot-st-gas-netload-drag-2026-06.md pooled curve "
                "(gas_st_drag_slope_per_gw/_intercept/_cap = "
                "0.00906/-0.1376/0.34)"
            ),
            "trigger": (
                "docs/handoffs/ercot-stgas-shoulder-2026-07.md §3.3 — DJF "
                "sub-$150 control hours: model 1.6-1.9 GW vs measured 0.6-1.1 "
                "GW at the same net-load (a source-grain limit, not a level "
                "error; overnight curve still tracks, rho 0.69/0.75)"
            ),
            "measured_source": (
                "campd-unit-level/TX_<year>.parquet — the model's drag-covered "
                "ST_GAS plants (custom-bin-assignments.csv, non-"
                "ST_GAS_PEAKER_PLANTS, split facilities unit-routed per "
                "data.outages), CT/CC unit types dropped, x0.95 net "
                "(campd.DEFAULT_PARASITIC_LOAD_PCT)"
            ),
            "netload_source": (
                "eia-930-hourly/ERCO hourly.parquet Demand - NG:WND - NG:SUN, "
                "fixed-CST non-leap clock (derive_ercot_dam_cleared_share "
                "convention)"
            ),
            "years": [int(y) for y in args.years],
            "floor_base_mw": round(base_mw, 1),
            "season_of_month": list(SEASON_OF_MONTH),
            "overnight_window_h": [OVERNIGHT_START_H, OVERNIGHT_END_H],
            "estimator": (
                "median overnight CF per 2-GW net-load bin (>=12 h/cell), "
                "hinge fit clip(slope*netGW + intercept, 0, cap) via knee "
                "grid-search + least-squares (no scipy.optimize), cap = p95 "
                "of the season's overnight CF — the NYISO/PJM standing-derive "
                "estimator"
            ),
            "pooled_refit_check": {
                "slope_per_gw": round(slope_p, 5),
                "intercept": round(icept_p, 4),
                "cap": round(cap_p, 3),
                "armed_keeper_scalars": {
                    "slope_per_gw": 0.00906,
                    "intercept": -0.1376,
                    "cap": 0.34,
                },
            },
            "frozen": (
                "rule 23 — re-derive only on a CAMPD/EIA-930 source-data "
                "update, never because a residual moved"
            ),
        },
        "seasons": seasons_out,
    }
    args.out.write_text(json.dumps(out, indent=1))
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
