"""Lead-0 probe (part 4) — model price vs its EXACT solve input.

Rebuilds the model's PJM demand exactly as the keeper's solve loaded it
(EIA-930 total + measured tie-line net export via pjm_net_interchange) and
nets the 930 wind/solar/hydro it dispatches against, then repeats the
event-based daily-peak test against the reconstructed model price. If the
model's price peak matches its exact input at lag 0, the "internal lead" was
a proxy artifact; if the -1 lead survives, the lead is inside the
LP/price-formation layer (or in the interchange series' own clock).

Also reports the interchange series' DST behaviour (it is EPT-indexed —
prevailing labels mapped raw onto the EST chronological calendar).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from market_sim.data import eia_loader  # noqa: E402

sys.path.insert(0, str(REPO / "scripts" / "probes"))
from _pjm2025_payload_lag import (  # noqa: E402
    HOURS,
    MONTH_OF_HOY,
    SEASONS,
    best_lag,
    decode_i16,
    load_payload,
)
from _pjm2025_event_phase import daily_extreme_hours, offset_stats  # noqa: E402


def main() -> None:
    payload = load_payload("2026-07-14-pjm-110-bench-hygiene")
    lmp = pd.read_parquet(
        RAW_DATA_DIR / "_validation-source" / "actual_lmp_hourly_PJM.parquet"
    )
    for year in (2023, 2024, 2025):
        delta = decode_i16(payload["years"][str(year)]["lmpDeltaHr"])
        sub = lmp[lmp["year"] == year].set_index("hour")
        rt = np.full(HOURS, np.nan)
        rt[sub.index.to_numpy()] = sub["rt"].to_numpy()
        da = np.full(HOURS, np.nan)
        da[sub.index.to_numpy()] = sub["da"].to_numpy()
        rt_padded = np.where(np.isfinite(rt), rt, da)
        model = rt_padded + delta

        frame = eia_loader._eia_hourly_frame_filled("PJM", year)
        d = frame["Demand"].interpolate().bfill().ffill().to_numpy(dtype=float)
        w = frame["NG: WND"].interpolate().bfill().ffill().to_numpy(dtype=float)
        s = frame["NG: SUN"].interpolate().bfill().ffill().to_numpy(dtype=float)
        h = frame["NG: WAT"].interpolate().bfill().ffill().to_numpy(dtype=float)
        exp = eia_loader.pjm_net_interchange(year)
        if exp is None:
            exp = np.zeros(HOURS)
        exact = d + exp  # generation requirement the fleet must serve
        exact_net = exact - w - s - h

        print(f"===== {year}")
        for label, series in (
            ("exact gen-req (D+X)", exact),
            ("exact net-load (D+X-W-S-H)", exact_net),
        ):
            for ssn in ("DJF", "JJA"):
                mask = np.isin(MONTH_OF_HOY, SEASONS[ssn])
                r = best_lag(model, series, mask)
                print(
                    f"  corr {label} {ssn}: "
                    + " ".join(f"{lag:+d}:{r[lag]:.3f}" for lag in (-1, 0, 1))
                    + f" best={r['best']:+d}"
                )
        mp = daily_extreme_hours(model)
        ep = daily_extreme_hours(exact_net)
        offset_stats(mp, ep, "model-price peak vs exact-netload peak")
        # interchange clock sanity: correlation of export vs -actual price
        # (exports track neighbour scarcity) not needed; just report DST split
        xdjf = np.isin(MONTH_OF_HOY, SEASONS["DJF"])
        print(
            f"  interchange: mean export {exp.mean():,.0f} MW"
            f" (DJF {exp[xdjf].mean():,.0f})"
        )


if __name__ == "__main__":
    main()
