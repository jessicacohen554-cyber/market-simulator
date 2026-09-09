#!/usr/bin/env python3
"""miso-248 screen gates G-1 .. G-3 (G-4 is scripts/screen_collateral_gate.py).

Bars fixed in ``results/calibration/PREREG-miso248-the-spp-hourly-ladder-
rederive-on-the-repaired-clock-2026-09-09.md`` §7 before any of them was
computed. Nothing here reads an actual, a criterion or a residual.

``G-2`` is ZERO LP and runs on its own (``--gates g2``); ``G-1``/``G-3`` need the
arm and control bundles.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
import sys  # noqa: E402

sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

OUT = REPO / "results" / "calibration" / "_miso248_screen_gates.json"

# The two tables, frozen here as literals so the gate does not depend on which
# one happens to be in the working tree when it runs. OLD = the committed
# pre-repair registry (the control's); NEW = the miso-248 re-derive (the arm's).
OLD = {
    2023: {
        "import": (13.44, 30.30, 50.82, 83.92, 123.33, 152.94, 152.94, 152.94),
        "export": (-2.39, -21.49, -41.89, -90.15, -178.51, -212.03, -212.03, -212.03),
    },
    2024: {
        "import": (17.26, 37.56, 65.15, 139.78, 230.88, 230.88, 230.88, 230.88),
        "export": (1.44, -12.98, -23.83, -33.09, -43.06, -48.41, -55.24, -66.13),
    },
    2025: {
        "import": (18.58, 41.90, 78.87, 152.95, 197.69, 237.84, 271.99, 338.83),
        "export": (-2.37, -19.00, -31.11, -44.88, -70.49, -122.45, -254.63, -254.63),
    },
}
NEW = {
    2023: {
        "import": (10.62, 25.73, 43.07, 62.47, 83.98, 90.56, 90.56, 90.56),
        "export": (0.24, -10.16, -25.87, -56.57, -153.04, -166.65, -166.65, -166.65),
    },
    2024: {
        "import": (14.40, 33.33, 56.44, 109.27, 203.29, 203.29, 203.29, 203.29),
        "export": (2.84, -6.48, -14.46, -20.33, -27.41, -32.26, -36.24, -47.02),
    },
    2025: {
        "import": (16.86, 37.50, 67.75, 140.17, 182.10, 232.18, 252.79, 290.12),
        "export": (0.34, -10.42, -18.49, -28.01, -45.96, -69.66, -140.45, -140.45),
    },
}


def _provenance() -> dict:
    def sh(*a: str) -> str:
        return subprocess.run(
            a, cwd=REPO, capture_output=True, text=True, check=False
        ).stdout.strip()

    return {
        "git_head": sh("git", "rev-parse", "HEAD"),
        "dirty": sh("git", "status", "--porcelain") != "",
    }


def gate_g2(year: int) -> dict:
    """G-2 confinement, proved at ZERO LP on the injector itself."""
    from market_sim.data.fleet import generators_to_fleet_arrays
    from market_sim.model.interchange import spec as ispec
    from market_sim.model.transmission import (
        _REF_EXPORT_MARK,
        _REF_IMPORT_MARK,
        build_reference_price_node,
        inject_miso_seam_ladder_prices,
    )

    T = 48
    node = build_reference_price_node("MISO")
    zones = sorted({g.zone for g in node})
    fleet = generators_to_fleet_arrays(node, zones, hours=T)

    def run(table: dict) -> np.ndarray:
        saved = ispec.MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR
        ispec.MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR = {
            y: {"SPP": {s: tuple(v[s]) for s in ("import", "export")}}
            for y, v in table.items()
        }
        try:
            mc = np.full((len(node), T), -123.0)
            inject_miso_seam_ladder_prices(
                fleet,
                mc,
                "MISO",
                year,
                neighbour_anchored=True,
                neighbour_hourly=True,
                neighbour_hourly_spp=True,
            )
            return mc
        finally:
            ispec.MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR = saved

    a_old, a_new = run(OLD), run(NEW)
    diff = a_new - a_old
    moved_rows, offending, exact = [], [], True
    for row, uid in enumerate(fleet.unit_ids):
        d = diff[row, :]
        if not np.any(np.abs(d) > 1e-9):
            continue
        moved_rows.append(uid)
        if _REF_IMPORT_MARK in uid:
            tag, side = uid.rsplit(_REF_IMPORT_MARK, 1)[1], "import"
        elif _REF_EXPORT_MARK in uid:
            tag, side = uid.rsplit(_REF_EXPORT_MARK, 1)[1], "export"
        else:
            offending.append(uid)
            continue
        name, _, k = tag.partition("#")
        if name != "SPP":
            offending.append(uid)
            continue
        want = float(NEW[year][side][int(k) - 1]) - float(OLD[year][side][int(k) - 1])
        if not (np.allclose(d, want, atol=1e-9) and float(d.std()) == 0.0):
            exact = False
            offending.append(f"{uid}: want {want}, got {d[0]} std {d.std()}")
    return {
        "year": year,
        "n_rows_total": len(fleet.unit_ids),
        "n_rows_moved": len(moved_rows),
        "n_non_spp_rows_moved": len(offending),
        "offending": offending[:20],
        "all_moves_exact_and_hour_constant": exact,
        "PASS": len(offending) == 0 and exact and len(moved_rows) == 16,
    }


def _spp_seam_energy(bundle: Path, year: int) -> dict:
    """Net SPP seam import energy (TWh) from a bundle's own unit_hourly."""
    import pandas as pd

    from market_sim.model.transmission import _REF_EXPORT_MARK, _REF_IMPORT_MARK

    path = bundle / "hourly" / f"unit_hourly_{year}.parquet"
    if not path.exists():
        return {"available": False, "path": str(path)}
    d = pd.read_parquet(path)
    d = d[d["pass"].astype(str) == "P1"]
    uid = d["unit_id"].astype(str)
    is_imp = uid.str.contains(_REF_IMPORT_MARK, regex=False)
    is_exp = uid.str.contains(_REF_EXPORT_MARK, regex=False)
    seam = uid.str.rsplit(_REF_IMPORT_MARK, n=1).str[-1]
    seam = seam.where(is_imp, uid.str.rsplit(_REF_EXPORT_MARK, n=1).str[-1])
    seam_name = seam.str.partition("#")[0]
    spp = d[(is_imp | is_exp) & (seam_name == "SPP")]
    return {
        "available": True,
        "n_rows": int(spp["unit_id"].nunique()),
        "net_import_TWh": round(float(spp["mw"].sum()) / 1e6, 6),
        "import_TWh": round(float(spp[is_imp.loc[spp.index]]["mw"].sum()) / 1e6, 6),
        "export_TWh": round(float(spp[is_exp.loc[spp.index]]["mw"].sum()) / 1e6, 6),
    }


def gate_g1(arm: Path, control: Path, year: int, de_pred: float) -> dict:
    a = _spp_seam_energy(arm, year)
    c = _spp_seam_energy(control, year)
    out = {"year": year, "dE_pred_TWh": de_pred, "arm": a, "control": c}
    if not (a.get("available") and c.get("available")):
        out["FALLBACK_USED"] = True
        import pandas as pd

        def agg(b: Path) -> float:
            d = pd.read_parquet(b / "hourly" / f"class_hourly_{year}.parquet")
            d = d[
                (d["pass"].astype(str) == "P1") & (d["klass"].astype(str) == "import")
            ]
            return float(d["mw"].sum()) / 1e6

        realised = agg(arm) - agg(control)
        out["note"] = (
            "unit_hourly absent -- G-1 falls back to the AGGREGATE import class, "
            "which pools all four seams and cannot separate the SPP response"
        )
    else:
        out["FALLBACK_USED"] = False
        realised = a["net_import_TWh"] - c["net_import_TWh"]
    out["realised_TWh"] = round(realised, 6)
    same_sign = (realised > 0) == (de_pred > 0) and realised != 0.0
    ratio = abs(realised) / abs(de_pred) if de_pred else float("inf")
    out["ratio"] = round(ratio, 4)
    out["same_sign"] = bool(same_sign)
    out["form"] = "A" if abs(de_pred) >= 0.05 else "B"
    out["PASS"] = (
        bool(same_sign and (1 / 3) <= ratio <= 3.0)
        if out["form"] == "A"
        else bool(abs(realised) <= 0.15)
    )
    return out


def gate_g3(bundle: Path, year: int, table: dict, label: str) -> dict:
    """The applied identity mc[row,t] == hub(t) + delta_k, in the SOLVED year."""
    import pandas as pd

    from market_sim.data.eia_loader import measured_miso_spp_hub_prices
    from market_sim.model.transmission import _REF_EXPORT_MARK, _REF_IMPORT_MARK

    path = bundle / "hourly" / f"unit_hourly_{year}.parquet"
    if not path.exists():
        return {"label": label, "available": False}
    hub = np.asarray(measured_miso_spp_hub_prices("MISO", year, 8760), dtype=float)
    d = pd.read_parquet(path)
    d = d[d["pass"].astype(str) == "P1"]
    if "mc" not in d.columns:
        return {"label": label, "available": False, "reason": "no mc column"}
    worst, checked, bad = 0.0, 0, 0
    for uid, grp in d.groupby(d["unit_id"].astype(str)):
        if _REF_IMPORT_MARK in uid:
            tag, side = uid.rsplit(_REF_IMPORT_MARK, 1)[1], "import"
        elif _REF_EXPORT_MARK in uid:
            tag, side = uid.rsplit(_REF_EXPORT_MARK, 1)[1], "export"
        else:
            continue
        name, _, k = tag.partition("#")
        if name != "SPP":
            continue
        g = grp.sort_values("hour")
        mc = g["mc"].to_numpy(dtype=float)
        want = hub[: mc.size] + float(table[year][side][int(k) - 1])
        err = np.abs(mc - want)
        checked += 1
        worst = max(worst, float(err.max()))
        bad += int((err > 0.01).sum())
    return {
        "label": label,
        "available": True,
        "rows_checked": checked,
        "hours_violating_atol_0.01": bad,
        "max_abs_err": round(worst, 6),
        "PASS": checked == 16 and bad == 0,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gates", default="all")
    ap.add_argument("--year", type=int, default=2023)
    ap.add_argument("--arm", type=Path)
    ap.add_argument("--control", type=Path)
    ap.add_argument("--de-pred", type=float, default=0.2085)
    args = ap.parse_args()

    rec: dict = {
        "probe": "miso-248 screen gates",
        "prereg": (
            "results/calibration/PREREG-miso248-the-spp-hourly-ladder-rederive-"
            "on-the-repaired-clock-2026-09-09.md"
        ),
        "screen_year": args.year,
        "provenance": _provenance(),
    }
    if OUT.exists():
        rec = {**json.loads(OUT.read_text()), **rec}
    if args.gates in ("all", "g2"):
        rec["G2_confinement"] = gate_g2(args.year)
    if args.gates in ("all", "g1g3") and args.arm and args.control:
        rec["G1_direction_magnitude"] = gate_g1(
            args.arm, args.control, args.year, args.de_pred
        )
        rec["G3_identity_arm"] = gate_g3(args.arm, args.year, NEW, "arm/NEW")
        rec["G3_identity_control"] = gate_g3(
            args.control, args.year, OLD, "control/OLD"
        )
        rec["G3_PASS"] = bool(
            rec["G3_identity_arm"].get("PASS")
            and rec["G3_identity_control"].get("PASS")
        )
    OUT.write_text(json.dumps(rec, indent=1) + "\n")
    print(json.dumps(rec, indent=1))


if __name__ == "__main__":
    main()
