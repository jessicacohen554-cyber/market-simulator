"""R-CAISO-33 Amendment A: G-RT-H, the hour-grain round-trip gate. ZERO LP.

Pre-registered in ``PRECOMMIT-r-caiso-33-joint-gas-rebasis-2026-10-02.md`` §10
(pushed before this probe existed). Per consumed class x band x year, at the
derive's own grain: model offer per resource-hour = m x HR x (g_h + a + c_y) + VOM
(the solve's pricing), residual = offer - measured band price, statistic =
cap-weighted median over resources of the resource-year median residual. Arms:
K (keeper pooled multiplier, from the keeper pin), R (re-based, stage1/rebased),
C (same-corpus control, stage1/control; reported only).

Needs the reduced public-bid store on disk (``derive_caiso_offer_surface.REDUCED_STORE``).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO), str(REPO / "src")]

from market_sim.config.constants import CAISO_CITYGATE_TRANSPORT_ADDER as A  # noqa: E402
from scripts.data import derive_caiso_offer_surface as D  # noqa: E402

REC = REPO / "docs/records/caiso/r-caiso-33"
KEEPER_SHA = "cd5897987106193b34b84c5f4bb4a7c9bb1e4760"
ART = "data/raw/_validation-source/caiso_offer_curve_measured.json"
BANDS = ("econ_low", "econ_high", "peak")
TOL_POOLED, TOL_WORSE = 0.75, 0.25
YEARS = [2023, 2024, 2025]


def main() -> int:
    """Compute the G-RT-H table and verdict; write roundtrip_gate_hour.json."""
    arms = {
        "K": json.loads(
            subprocess.check_output(["git", "show", f"{KEEPER_SHA}:{ART}"], cwd=REPO)
        ),
        "R": json.loads(
            (REC / "stage1/rebased/caiso_offer_curve_measured.json").read_text()
        ),
        "C": json.loads(
            (REC / "stage1/control/caiso_offer_curve_measured.json").read_text()
        ),
    }
    geom = D._fleet_geometry()
    delivered = D._gas_staircase()  # composite + A (the solve's series)
    bids = D._load_bids_reduced(YEARS)
    cap_ry = bids.groupby(["resource_seq", "year"]).segment_mw.quantile(0.98)
    bids = bids.join(cap_ry.rename("cap"), on=["resource_seq", "year"])
    bids = bids[bids.cap >= D.MIN_CAP_MW]
    res, _ = D._classify(bids, delivered, 8.5)
    st_cut = D.locate_st_cut(res, 8.5)
    res["cls"] = D._assign_classes(res, 8.5, st_cut)
    gas_res = res[res.is_gas]
    bids["day"] = (
        bids.interval_start_utc.dt.tz_convert("US/Pacific")
        .dt.normalize()
        .dt.tz_localize(None)
    )
    carbon = {y: float(D._carbon_price(y)) for y in YEARS}
    rows = []
    for cls in ("CC_REGULAR", "CT_PEAKER"):
        sub = gas_res[gas_res.cls == cls]
        seg = bids[bids.resource_seq.isin(sub.index)]
        hr, vom = geom[cls]["base_hr"], D.VOM_BY_CLASS[cls]
        win = D.class_band_windows(geom, cls)
        meta = seg[
            ["resource_seq", "interval_start_utc", "day", "year"]
        ].drop_duplicates(["resource_seq", "interval_start_utc"])
        for band in BANDS:
            lo, hi = win[band]
            bp = (
                D._band_price(seg, lo, hi)
                .rename("p")
                .reset_index()
                .merge(meta, on=["resource_seq", "interval_start_utc"], how="left")
            )
            bp["g"] = bp.day.map(delivered)
            bp = bp.dropna(subset=["g"])
            c = bp.year.map(carbon) * D.CO2_FACTOR
            for arm, doc in arms.items():
                m = doc[cls]["bands"][band]
                bp[f"r_{arm}"] = m * hr * (bp.g + c) + vom - bp.p
            ry = (
                bp.groupby(["resource_seq", "year"])[[f"r_{k}" for k in arms]]
                .median()
                .reset_index()
            )
            ry["cap"] = ry.resource_seq.map(sub.cap)
            for y in YEARS + ["pooled"]:
                s = ry if y == "pooled" else ry[ry.year == y]
                stat = {
                    k: round(
                        D._wquantile(
                            s[f"r_{k}"].to_numpy(float), s.cap.to_numpy(float), 0.5
                        ),
                        3,
                    )
                    for k in arms
                }
                rows.append(
                    {
                        "class": cls,
                        "band": band,
                        "year": y,
                        **{f"stat_{k}": v for k, v in stat.items()},
                        "mult_K": arms["K"][cls]["bands"][band],
                        "mult_R": arms["R"][cls]["bands"][band],
                    }
                )
    ok = True
    for r in rows:
        if r["year"] == "pooled":
            r["pass_1"] = abs(r["stat_R"]) <= TOL_POOLED
            ok &= r["pass_1"]
        else:
            r["pass_2"] = abs(r["stat_R"]) <= abs(r["stat_K"]) + TOL_WORSE
            ok &= r["pass_2"]
    doc = {
        "gate": "G-RT-H (Amendment A)",
        "adder": A,
        "st_cut": st_cut,
        "tol_pooled": TOL_POOLED,
        "tol_worse": TOL_WORSE,
        "pass": bool(ok),
        "rows": rows,
    }
    (REC / "roundtrip_gate_hour.json").write_text(
        json.dumps(doc, indent=1, default=float) + "\n"
    )
    print(pd.DataFrame(rows).to_string(index=False))
    print("st_cut", st_cut, "G-RT-H", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
