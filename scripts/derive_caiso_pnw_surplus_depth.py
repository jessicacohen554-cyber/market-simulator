"""Derive the CAISO NORTH-corridor (COI/Path-66) surplus-clean import depth — gate check.

The north-corridor analogue of the caiso-87 south-corridor surplus-clean depth
(``interchange_config.CAISO_DSW_SURPLUS_CLEAN_DEPTH_BY_YEAR``), chartered by the
2026-07-16 caiso-87 handoff (Session 1b): the caiso-87 session found the north
depth NOT year-stable (1.2-2.5 GW) under the misaligned SoCal-citygate trigger
and required a Malin-side gas series before the lane could be adjudicated.

Construction (identical to the south block, north inputs):

  trigger[t] = MALIN nodal DA LMP[t] < HR_CCGT x Sumas_gas[t] + remote VOM
               (HR_CCGT = 6.97, the same transmission._CAISO_IMPORT_COUPLE_HR
               coupling ratio; VOM = $2.5; gas = the measured Northwest Sumas
               weekly Wednesday print, data/raw/gas-prices/sumas_weekly.csv —
               EIA: "the main pricing point for natural gas in the Pacific
               Northwest", i.e. the gas the PNW CCGT fleet actually burns;
               fetch_sumas_weekly.py)
  depth[y]   = p95 of measured WECC_PNW corridor net import (EIA-930 CISO
               DIBAs, model clock) over trigger-ON hours of year y

Estimation-stage honesty gates (caiso-81/86/87 precedent — run BEFORE any
solve): per-year depth CV <= 0.20 and LOYO (mean-of-other-two predicts the
held-out year) worst error <= 25%. If either gate fails the lane files a
FINDING and does NOT solve (the derive-first discipline). No LP is run here.

Result 2026-07-16 (FINDING-caiso88-pnw-surplus-depth-gates in
docs/calibration-log.md): FAIL — depths 2,377 / 1,149 / 1,191 MW (2023/24/25),
CV 0.362, LOYO worst 55.2%. The 2023 spring-runoff year carries twice the
surplus depth of 2024/25: the PNW surplus-hour import capability rides the
hydro regime, which three years cannot identify as a stable forward rule. The
aligned Malin-side (Sumas) trigger does NOT rescue the caiso-87 session's
instability read.

Usage: python scripts/derive_caiso_pnw_surplus_depth.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from derive_caiso_import_tranches import (  # noqa: E402
    YEARS,
    corridor_net_import,
    hub_prices,
)

SUMAS = REPO / "data" / "raw" / "gas-prices" / "sumas_weekly.csv"
# Same coupling constants as the south trigger (interchange_config /
# transmission._CAISO_IMPORT_COUPLE_HR["DSW_CCGT"] and
# CAISO_DSW_SURPLUS_REMOTE_VOM) — the remote-CCGT floor construction.
HR_CCGT = 0.37 / 0.0531  # ~6.97
REMOTE_VOM = 2.5
CV_MAX = 0.20
LOYO_MAX = 0.25


def sumas_hourly(year: int) -> np.ndarray:
    """Northwest Sumas weekly print forward-filled to the model's 8760 clock."""
    s = (
        pd.read_csv(SUMAS, parse_dates=["date"])
        .set_index("date")["sumas_usd_mmbtu"]
        .dropna()
    )
    idx = pd.date_range("2023-01-01", "2025-12-31", freq="D")
    daily = s.reindex(idx.union(s.index)).sort_index().ffill().bfill().reindex(idx)
    dsel = pd.date_range(
        f"{year}-01-01", periods=366 if year % 4 == 0 else 365, freq="D"
    )
    v = daily.reindex(dsel)
    if year % 4 == 0:
        v = v[~((v.index.month == 2) & (v.index.day == 29))]
    return np.repeat(v.to_numpy(dtype=float), 24)


def main() -> None:
    """Derive per-year north depths, print the gates, exit 0 PASS / 2 FAIL."""
    net = corridor_net_import()
    hub = hub_prices()
    depths: dict[int, float] = {}
    print("=== CAISO north-corridor (WECC_PNW) surplus-clean depth ===")
    print(f"trigger: MALIN < {HR_CCGT:.2f} x Sumas + {REMOTE_VOM}")
    for yr in YEARS:
        malin = hub.loc[yr]["MALIN"].to_numpy()
        flow = net.loc[yr]["WECC_PNW"].to_numpy()
        floor = HR_CCGT * sumas_hourly(yr) + REMOTE_VOM
        on = np.isfinite(malin) & (malin < floor)
        m = on & np.isfinite(flow)
        depths[yr] = float(np.percentile(flow[m], 95))
        print(
            f"  {yr}: trigger-ON {on.mean():5.1%} of hours "
            f"({int(m.sum())} measured) -> p95 depth {depths[yr]:,.0f} MW"
        )

    vals = np.array([depths[y] for y in YEARS])
    cv = float(vals.std() / vals.mean())
    stability_ok = cv <= CV_MAX
    print(
        f"\n  year-stability CV = {cv:.3f}  (gate <= {CV_MAX}): "
        f"{'PASS' if stability_ok else 'FAIL'}"
    )

    loyo_ok = True
    for held in YEARS:
        pred = float(np.mean([depths[y] for y in YEARS if y != held]))
        err = abs(pred - depths[held]) / depths[held]
        ok = err <= LOYO_MAX
        loyo_ok = loyo_ok and ok
        print(
            f"  LOYO held-out {held}: mean-of-others {pred:,.0f} vs "
            f"{depths[held]:,.0f} -> {err:.1%}  (gate <= {LOYO_MAX:.0%}): "
            f"{'PASS' if ok else 'FAIL'}"
        )

    passed = stability_ok and loyo_ok
    print(
        f"\n  OVERALL: "
        f"{'PASS — depth admissible, may solve' if passed else 'FAIL — file FINDING, do NOT solve'}"
    )
    sys.exit(0 if passed else 2)


if __name__ == "__main__":
    main()
