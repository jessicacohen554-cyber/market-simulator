"""Close-out CAISO w2, phase 0 (ZERO LP): reach of an R-CAISO-20-style unprinted arm for the
DSW DAYTIME (caiso-94, hod 6-21) and LATE-EVENING (caiso-269, hod 22-23) clean rungs.

This is the sizing an owner card needs, NOT a measured admission: R-CAISO-19 FINDING §3
found no measured trigger for either rung without a raw Palo Verde print, and the
R-CAISO-20 card armed only the overnight rung and ledgered the rest. What is new since
that card is the scored target: owner ruling R-33 (2026-10-03) moved the C1 bench, and
the 2019-21 CC_REGULAR misses are now +5.63 / +13.46 / +6.59 TWh against bands of
±4.84 / ±4.60 / ±4.83, so the volume a fold lever must deliver is 0.79 / 8.86 / 1.76 TWh
of in-state CC energy, not 5.9 / 12.9 / 3.3.

Transfer construction sized here (the overnight ruling's pattern, nothing re-sized):

* window: unprinted hours (``measured_intertie_hub_unprinted_year_mask``) at hod 6-21
  (daytime) and 22-23 (late evening); with no raw print the caiso-87 surplus trigger
  is undefined, so the daytime rung covers the whole band (surplus stays 0 MW);
* depth: the rung's own p95 of the EIA-930 WECC_DSW corridor net import over its
  window, computed for 2019 / 2020 exactly as ``--extra-years`` would (report), and
  the pooled static entry (what an unmapped year carries today);
* capability: max(0, depth − DSW_solar_PV firm capability[t]) (overnight is 0 there);
* pricing: the formula hub + ε, no wheel, EF 0 — the overnight rung's P1 offer row.

First-order added DSW net import (fixed duals): in hours where the corridor is not
binding (|λ_DSW − λ_SP15_rest| ≤ $1) and the clean offer clears CAISO
(offer < λ_SP15_rest), added = max(0, cap − DSW fossil MW already running); in binding
hours the clean MW only displaces DSW fossil (0 added). Compared with the EIA-930 DSW
gap in the same hours.

Usage::

    PYTHONPATH=.:src:scripts .venv/bin/python scripts/probes/_closeout_caiso_w2_unprinted_rungs.py [--out PATH]
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path[:0] = [".", "src", "scripts"]
from scripts.data.derive_caiso_import_tranches import corridor_net_import  # noqa: E402

from market_sim.data.eia930.envelopes import measured_intertie_hub_unprinted_year_mask  # noqa: E402
from market_sim.model.interchange.spec import (  # noqa: E402
    CAISO_DSW_DAYTIME_CLEAN_DEPTH_STATIC,
    CAISO_DSW_LATEEVENING_CLEAN_DEPTH_STATIC,
)

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "results/calibration/closeout_caiso_w1_a2_span/hourly"
T = 8760
HOD = np.arange(T) % 24
YEARS = (2019, 2020, 2021)
BIND_TOL = 1.0
FOSSIL = ("DSW_CCGT", "DSW_CT", "WECC_scarcity")
WINDOWS = {
    "daytime": ((HOD >= 6) & (HOD <= 21), CAISO_DSW_DAYTIME_CLEAN_DEPTH_STATIC),
    "lateevening": (HOD >= 22, CAISO_DSW_LATEEVENING_CLEAN_DEPTH_STATIC),
}
CC_NEEDED = {2019: 5.63 - 4.84, 2020: 13.46 - 4.60, 2021: 6.59 - 4.83}


def year_reach(year: int, meas: pd.DataFrame) -> dict:
    """Capability, first-order added import and the EIA-930 gap, per window."""
    mask = measured_intertie_hub_unprinted_year_mask(
        "CAISO", year, T, "PALOVRDE", gap_fill_measured_dam=True
    )
    mask = np.zeros(T, bool) if mask is None else mask
    um = pd.read_parquet(
        BUNDLE / f"unit_marginal_{year}.parquet",
        columns=["unit_id", "zone", "hour", "mw", "cap_mw", "mc"],
    )
    um = um[um.zone.astype(str) == "WECC_DSW"]
    piv = {
        str(u)[len("WECC_DSW_") :]: g.set_index("hour").reindex(range(T))
        for u, g in um.groupby("unit_id", observed=True)
    }
    sysd = pd.read_parquet(
        BUNDLE / f"system_{year}.parquet", columns=["zone", "hour", "price"]
    )
    lam = {
        z: sysd[sysd.zone == z].set_index("hour")["price"].reindex(range(T)).to_numpy()
        for z in ("WECC_DSW", "SP15_rest")
    }
    nonbinding = np.abs(lam["WECC_DSW"] - lam["SP15_rest"]) <= BIND_TOL
    firm = piv["DSW_solar_PV"]["cap_mw"].to_numpy()
    offer = piv["DSW_overnight_clean"][
        "mc"
    ].to_numpy()  # formula hub + ε, no wheel, EF 0
    fossil = sum(piv[n]["mw"].to_numpy() for n in FOSSIL)
    model_net = (
        sum(g["mw"].to_numpy() for n, g in piv.items() if not n.startswith("export"))
        - piv["export_PALOVRDE"]["mw"].to_numpy()
    )
    e930 = meas.loc[year, "WECC_DSW"].reindex(range(T)).to_numpy()
    sub = np.arange(T) < 2784 if year == 2021 else np.ones(T, bool)
    p95 = {
        k: float(np.nanpercentile(e930[w & sub], 95)) for k, (w, _) in WINDOWS.items()
    }
    out = {
        "unprinted_hours": int(mask.sum()),
        "measured_p95_depth_mw": p95,
        "windows": {},
    }
    tot = {"static": 0.0, "p95": 0.0}
    for k, (w, static) in WINDOWS.items():
        sel = mask & w
        row = {
            "hours": int(sel.sum()),
            "eia930_gap_twh": float(np.nansum((model_net - e930)[sel]) / 1e6),
        }
        for basis, depth in (("static", static), ("p95", p95[k])):
            cap = np.where(sel, np.clip(depth - firm, 0.0, None), 0.0)
            clears = offer < lam["SP15_rest"]
            added = np.where(
                sel & nonbinding & clears, np.clip(cap - fossil, 0.0, None), 0.0
            )
            row[basis] = {
                "depth_mw": depth,
                "capability_twh": float(cap.sum() / 1e6),
                "first_order_added_twh": float(added.sum() / 1e6),
                "displaced_fossil_twh": float(
                    np.where(sel, np.minimum(cap, fossil), 0.0).sum() / 1e6
                ),
            }
            tot[basis] += row[basis]["first_order_added_twh"]
        out["windows"][k] = row
    out["first_order_added_total_twh"] = tot
    out["cc_regular_needed_twh"] = CC_NEEDED[year]
    out["dsw_gap_whole_year_twh"] = float(np.nansum(model_net - e930) / 1e6)
    return out


def main() -> None:
    """Run the reach for the fold years and write the JSON."""
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--out",
        default=str(
            ROOT / "docs/records/caiso/closeout-caiso-w2/_unprinted_rungs.json"
        ),
    )
    a = ap.parse_args()
    meas = corridor_net_import(years=YEARS)
    res = {str(y): year_reach(y, meas) for y in YEARS}
    Path(a.out).write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
