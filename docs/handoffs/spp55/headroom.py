"""SPP-55 phase 0 (zero LP): keeper-3's reserve-eligible thermal headroom, hour by
hour, against the SPP Contingency Reserve requirement the design builds.

Rebuilds the keeper-3 (``spp43_screened_B``) LP fleet with ``run_year(fleet_only=True)``
per year (the only sanctioned reconstruction, ``scripts.replay_keeper.run_year_kwargs``),
takes the reserve-eligible available capacity ``sum(pmax x availability)`` over
``_reserve_eligible`` rows, subtracts the committed P1 dispatch of the same classes from
``hourly/class_hourly_<year>.parquet``, and compares the headroom with the family's
requirement (``_spp_design`` on the same fleet). The LP's reserve balance row can only
run short — and the demand curve can only fire — in an hour where this headroom is
below the requirement, so the count of such hours is the pre-solve answer to the STOP
gate's window-agreement leg.

Usage: uv run python docs/handoffs/spp55/headroom.py
"""

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs  # noqa: E402
from scripts.run_calibration import run_year  # noqa: E402
from market_sim.model.reserves.spec import _reserve_eligible, _spp_design  # noqa: E402

BUNDLE = REPO / "results/calibration/spp43_screened_B"
OUT = REPO / "docs/handoffs/spp55"
# The class_hourly classes whose members are RESERVE_FUEL_TYPES (gas_cc / gas_ct /
# gas_st / coal / nuclear / oil) — the same set _reserve_eligible admits.
ELIGIBLE_CLASSES = (
    "CC_CHP",
    "CC_REGULAR",
    "COAL_LIGNITE",
    "COAL_PRB",
    "CT_CHP",
    "CT_PEAKER",
    "ST_GAS",
    "ST_CHP",
    "nuclear",
    "oil",
)


def main() -> None:
    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    rows = []
    for year in (2023, 2024, 2025):
        kw_y = dict(kw)
        kw_y.update(derived_run_year_inputs(BUNDLE, year))
        r = run_year(
            year,
            "SPP",
            8760,
            float(meta["gas_prices"][str(year)]),
            {},
            fleet_only=True,
            **kw_y,
        )
        fa = r["fleet_arrays"]
        elig = _reserve_eligible(fa)
        cap_t = (fa.pmax[:, None] * fa.availability)[elig].sum(axis=0)
        ch = pd.read_parquet(BUNDLE / f"hourly/class_hourly_{year}.parquet")
        ch = ch[ch["pass"] == "P1"]
        piv = (
            ch.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum")
            .reindex(range(8760))
            .fillna(0.0)
        )
        disp_t = piv[[c for c in ELIGIBLE_CLASSES if c in piv.columns]].sum(axis=1).values
        head = cap_t - disp_t
        design = _spp_design(
            SimpleNamespace(iso="SPP", mode="backcast", weather_year=year),
            fa,
            8760,
            ["SPP-North", "SPP-South"],
        )
        req = design.families[0].requirement
        short = head < req
        rows.append(
            {
                "year": year,
                "req_median_mw": round(float(np.median(req))),
                "req_max_mw": round(float(req.max())),
                "headroom_min_mw": round(float(head.min())),
                "headroom_p1_mw": round(float(np.percentile(head, 1))),
                "headroom_median_mw": round(float(np.median(head))),
                "hours_headroom_below_req": int(short.sum()),
                "short_hours": [int(i) for i in np.flatnonzero(short)],
                "max_shortfall_mw": round(float((req - head).max()), 1),
            }
        )
        pd.DataFrame(
            {"hour": range(8760), "cap_elig": cap_t, "disp_elig": disp_t, "headroom": head, "req": req}
        ).to_parquet(OUT / f"headroom_{year}.parquet")
    df = pd.DataFrame(rows)
    print(df.to_string())
    df.to_csv(OUT / "headroom_summary.csv", index=False)


if __name__ == "__main__":
    main()
