"""Close-out CAISO w3, phase 0 (ZERO LP): validate L2 (CA-citygate daily shape on the DSW formula gas) on PRINTED days.

Pre-fixed bar (written before this ran, FINDING w3 §2): against the measured Palo Verde daily-mean
print, the daily-shaped formula ``gas_AZ(month) x f_CA(day) x HR x shape`` must beat the incumbent
flat-monthly formula ``gas_AZ(month) x HR x shape`` on BOTH the daily-mean Pearson r and the daily-mean
RMSE, in >= 3 of the 4 years 2022-2025. 2021 May-Dec is reported, not gated.

Usage::

    PYTHONPATH=.:src:scripts .venv/bin/python scripts/probes/_closeout_caiso_w3_l2_validation.py
"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path[:0] = [".", "src", "scripts"]
from _closeout_caiso_w3_levers import ca_daily_shape  # noqa: E402

from market_sim.data.eia930.envelopes import measured_intertie_hub_price_raw  # noqa: E402
from market_sim.data.eia930.frames import set_caiso_eia930_clock_repair  # noqa: E402
from market_sim.data.neighbor_price import caiso_hub_measured_gas_reference_price  # noqa: E402
from market_sim.model.interchange.spec import CAISO_PER_HUB_NEIGHBORS  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
T = 8760
DAY = np.arange(T) // 24


def score(year: int) -> dict:
    """Daily-mean r / RMSE of flat vs daily-shaped formula against the measured hub."""
    spec = CAISO_PER_HUB_NEIGHBORS["WECC_DSW"]
    flat = caiso_hub_measured_gas_reference_price(spec, year, T, eia923_fallback=True)
    meas = measured_intertie_hub_price_raw("CAISO", year, T, spec.hub)
    if flat is None or meas is None:
        return {"days": 0}
    shaped = flat * ca_daily_shape(year)
    out = {}
    sel = np.isfinite(meas) & np.isfinite(flat)
    days = np.unique(DAY[sel])
    dm = np.array([meas[sel & (DAY == d)].mean() for d in days])
    for name, f in (("flat", flat), ("shaped", shaped)):
        df = np.array([f[sel & (DAY == d)].mean() for d in days])
        out[name] = {
            "r": float(np.corrcoef(df, dm)[0, 1]),
            "rmse": float(np.sqrt(np.mean((df - dm) ** 2))),
        }
    out["days"] = int(days.size)
    out["shaped_wins"] = bool(
        out["shaped"]["r"] > out["flat"]["r"]
        and out["shaped"]["rmse"] < out["flat"]["rmse"]
    )
    return out


def main() -> None:
    """Score 2021-2025 and apply the bar."""
    set_caiso_eia930_clock_repair(True)
    res = {str(y): score(y) for y in (2021, 2022, 2023, 2024, 2025)}
    wins = sum(res[str(y)].get("shaped_wins", False) for y in (2022, 2023, 2024, 2025))
    res["gate"] = {"wins_2022_2025": wins, "pass": wins >= 3}
    Path(ROOT / "docs/records/caiso/closeout-caiso-w3/_l2_validation.json").write_text(
        json.dumps(res, indent=1)
    )
    for y, r in res.items():
        print(y, json.dumps(r))


if __name__ == "__main__":
    main()
