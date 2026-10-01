"""NYISO-NEXT-11 phase 0 (ZERO LP): the NE AC tie as its own two-way node.

Owner ruling Q-a (2026-09-28): split the NY-New England AC tie (P-32
``SCH - NE - NY``, landing Capital_Hudson) off the pooled ``NYISO_external``
star node as its own two-way node priced at its own measured spread
(CAPITL DA - ISO-NE ``.I.ROSETON 345 1`` DA). This probe designs that node
from measured inputs only and sizes its footprint before any solve.

Per year 2021-2025 it computes:

1. **Band grid.** ``SEAM_FLOW_TRANCHES`` (8) equal bands per direction, sized
   on the year's MEDIAN posted import / export limit of the tie (P-32
   ``positive_limit_mw`` / ``-negative_limit_mw``). The hourly posted limits are
   the node link's hourly TTC in each direction.
2. **Offsets.** The frozen Q-Q duration coupling transferred in kind from
   ``derive_pjm_seam_ladders._derive_one_spread`` (``qq_import`` /
   ``qq_export`` on ``spread = CAPITL DA - Roseton DA`` at the midpoint-depth
   grid, same-seam no-wash clamp). Band k's hourly offer is
   ``Roseton(t) + offset_k``.
3. **Measured-driven score** (the estimator's own consistency): the flow the
   bands imply when driven by the MEASURED spread, vs the measured flow.
4. **Model-driven footprint**: the same bands driven by the KEEPER's own
   Capital_Hudson price (committed hourly sidecars) against measured Roseton —
   first order, no price feedback.
5. **Pooled-link removal**: the keeper's Capital_Hudson PAR-attributed p90
   import envelope with and without the NE AC row, and the import it stops
   delivering in the hours the keeper held that link at its import cap
   (Capital_Hudson price above ``NYISO_external``).
6. **Pooled ladder re-derivation**: the frozen NYISO ladder formula
   (``derive_nyiso_import_tranches.derive``) on net import WITHOUT the NE AC
   row, vs the committed rungs.

Output: ``results/phase0/nyiso/_nyisonext11_phase0.json``. Reads raw inputs and
the keeper's committed hourlies only.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts" / "data"))

import derive_nyiso_ne_ac_ladder as dne  # noqa: E402

from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES  # noqa: E402
from market_sim.data.nyiso_par_attribution import (  # noqa: E402
    attributed_envelope_by_zone,
)
from market_sim.model.interchange.spec import IMPORT_TRANCHES_BY_YEAR  # noqa: E402

YEARS = dne.YEARS
CAL = REPO / "results" / "calibration"
OUT = CAL.parent / "phase0" / "nyiso" / "_nyisonext11_phase0.json"
NE_ROW = dne.NE_ROW
H = dne.H
PCT = 90.0  # constants.NYISO_SEAM_FLOW_PERCENTILE (the keeper's envelope)
NEXT7_EXCESS_TWH = {2021: 4.65, 2022: 4.00, 2023: 3.80, 2024: 2.79, 2025: 2.33}


def implied_flow(spread, imp, exp, step_i, step_e, cap_i, cap_e) -> np.ndarray:
    """Net flow the bands clear at a given hourly spread, within hourly posted limits."""
    s = spread[:, None]
    q_imp = ((s > np.asarray(imp)[None, :]) * step_i).sum(axis=1)
    q_exp = ((s < np.asarray(exp)[None, :]) * step_e).sum(axis=1)
    return np.minimum(q_imp, cap_i) - np.minimum(q_exp, cap_e)


def keeper_prices(year: int) -> tuple[np.ndarray, np.ndarray]:
    bundle = "nyisonext9_2021" if year == 2021 else "nyisonext9_span"
    s = pd.read_parquet(CAL / bundle / "hourly" / f"system_{year}.parquet")
    s = s[s["pass"] == "P1"].pivot_table(index="hour", columns="zone", values="price")
    return (
        s["Capital_Hudson"].reindex(range(H)).to_numpy(dtype=float),
        s["NYISO_external"].reindex(range(H)).to_numpy(dtype=float),
    )


def year_block(year: int) -> dict:
    d = dne.derive_year(year)
    df, flow, lim_i, lim_e, spread = (
        d["frame"],
        d["flow"],
        d["limit_import"],
        d["limit_export"],
        d["spread"],
    )
    ros = dne.load_roseton_da(year)
    L_i, L_e = d["node"]["import_mw"], d["node"]["export_mw"]
    step_i, step_e = L_i / SEAM_FLOW_TRANCHES, L_e / SEAM_FLOW_TRANCHES
    imp, exp, clamped = d["node"]["import"], d["node"]["export"], d["export_clamped"]
    ci, ce = np.nan_to_num(lim_i, nan=L_i), np.nan_to_num(lim_e, nan=L_e)

    # 3. measured-driven
    q_meas = implied_flow(np.nan_to_num(spread), imp, exp, step_i, step_e, ci, ce)
    ok = np.isfinite(flow)
    # 4. model-driven (keeper Capital_Hudson price vs measured Roseton)
    p_ch, p_ext = keeper_prices(year)
    sp_model = p_ch - np.nan_to_num(ros, nan=np.nanmean(ros))
    q_model = implied_flow(sp_model, imp, exp, step_i, step_e, ci, ce)

    # 5. pooled Capital_Hudson envelope with / without the NE row
    frame = df.rename(columns={})
    env_k = attributed_envelope_by_zone(frame, year, H, PCT)["Capital_Hudson"][0]
    env_a = attributed_envelope_by_zone(
        frame[frame["interface"] != NE_ROW], year, H, PCT
    )["Capital_Hudson"][0]
    at_cap = p_ch > p_ext + 1e-6  # keeper link at import bound (NEXT-7 §1 test)
    removed = np.where(at_cap, env_k - env_a, 0.0)

    # 6. pooled ladder without NE (the incumbent formula, NE AC row removed)
    net_all, net_wo = d["net_all"], d["net_without_ne"]
    rungs_new, rungs_repro = d["pooled_without_ne"], d["pooled_with_ne"]
    rungs_old = IMPORT_TRANCHES_BY_YEAR["NYISO"].get(year)

    return {
        "hours_spread": int(np.isfinite(spread).sum()),
        "posted_limit_median_mw": {"import": L_i, "export": L_e},
        "posted_limit_p10_p90": {
            "import": [
                float(np.nanpercentile(lim_i, 10)),
                float(np.nanpercentile(lim_i, 90)),
            ],
            "export": [
                float(np.nanpercentile(lim_e, 10)),
                float(np.nanpercentile(lim_e, 90)),
            ],
        },
        "offsets": {"import": imp, "export": exp, "export_clamped": clamped},
        "measured": {
            "twh": round(float(np.nansum(flow)) / 1e6, 3),
            "mean_mw": round(float(np.nanmean(flow)), 1),
            "hours_export": int((flow < 0).sum()),
            "hours_at_posted_import": int((flow >= lim_i - 1).sum()),
            "hours_at_posted_export": int((-flow >= lim_e - 1).sum()),
        },
        "measured_driven": {
            "twh": round(float(q_meas.sum()) / 1e6, 3),
            "spearman_vs_measured": round(
                float(pd.Series(q_meas[ok]).rank().corr(pd.Series(flow[ok]).rank())), 3
            ),
        },
        "model_driven": {
            "twh": round(float(q_model.sum()) / 1e6, 3),
            "hours_at_import_cap": int((q_model >= ci - 1).sum()),
            "hours_at_export_cap": int((-q_model >= ce - 1).sum()),
            "hours_export": int((q_model < 0).sum()),
        },
        "pooled_capital_hudson": {
            "keeper_env_mean_mw": round(float(env_k.mean()), 1),
            "arm_env_mean_mw": round(float(env_a.mean()), 1),
            "keeper_hours_at_import_cap": int(at_cap.sum()),
            "import_removed_twh": round(float(removed.sum()) / 1e6, 3),
        },
        "capital_hudson_net_change_twh": round(
            (float(q_model.sum()) - float(removed.sum())) / 1e6, 3
        ),
        "next7_excess_twh": NEXT7_EXCESS_TWH[year],
        "ladder": {
            "committed": [list(r) for r in rungs_old] if rungs_old else None,
            "reproduced_with_ne": [list(r) for r in rungs_repro],
            "without_ne_ac": [list(r) for r in rungs_new],
            "net_import_mean_mw": {
                "with_ne": round(float(np.nanmean(net_all)), 1),
                "without_ne": round(float(np.nanmean(net_wo)), 1),
            },
        },
    }


def main() -> None:
    res = {str(y): year_block(y) for y in YEARS}
    OUT.write_text(json.dumps(res, indent=1) + "\n")
    for y, b in res.items():
        print(
            y,
            "L",
            b["posted_limit_median_mw"],
            "meas",
            b["measured"]["twh"],
            "meas-driven",
            b["measured_driven"],
            "model",
            b["model_driven"],
            "removed",
            b["pooled_capital_hudson"],
            "net",
            b["capital_hudson_net_change_twh"],
        )
        print("   imp", b["offsets"]["import"], "exp", b["offsets"]["export"])


if __name__ == "__main__":
    main()
