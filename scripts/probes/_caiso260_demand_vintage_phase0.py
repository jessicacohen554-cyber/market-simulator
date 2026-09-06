"""caiso-260 estimator + phase 0 (ZERO LP): the demand-artifact vintage re-derive.

Registered in
``results/calibration/PRECOMMIT-caiso260-demand-vintage-rederive-2026-09-06.md``
(pushed first). The keeper's demand input
(``data/raw/reference/caiso-supply-consistent-demand/*.csv``, caiso-80 Option A)
was derived on a bench whose CEMS anchors pre-date the caiso-196/199/200 plant-map
landings; the bench parts C1/C4 score against today carry the wider map. The arm
is the committed producer (``derive_caiso_supply_consistent_demand.py``) re-run
UNCHANGED on the current bench.

Legs (PRECOMMIT sec 1-2):

* snapshot the committed artifact bytes; run the derive (its own guards must
  pass unchanged - R-1); diff regenerated vs committed;
* **G-REPRO** R-2: max |Δdemand| 1,452 / 863 / 583 MW and annual +69 / -33 /
  -753 GWh, ±1 MW / ±1 GWh; R-3: only ``cems_gas_grid_mw`` moved, netgen / ng_cell
  / ti byte-identical, ``Δdemand ≡ Δcems + Δflat`` with Δflat constant per year;
* phase 0: Δdemand by hour-of-day and month (flat term split out); hod 22-23 and
  belly 10-15; plant attribution of Δcems by least squares on the current bench
  per-plant hourly (El Segundo 57901 / Desert Star 55077 named ex ante);
  the gross footprint ``F(y) = Σ|Δdemand|`` naming the screen year; the C4-2025
  direction statistic ``S = Σ e_t Δd_t`` on the keeper's CEMS-basis gas error
  (the caiso-258 instrument) with its first-order bound.

By default the regenerated files are RESTORED to the committed bytes on exit
(``git checkout``); ``--keep`` leaves them on disk (the arm, for the screen).

Output: ``results/calibration/_caiso260_demand_vintage_phase0.json``.

Usage::

    PYTHONPATH=.:src uv run python scripts/probes/_caiso260_demand_vintage_phase0.py [--keep]
"""

from __future__ import annotations

import argparse
import gzip
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
_ARGV = list(sys.argv)
sys.argv = [sys.argv[0]]

ART_DIR = REPO / "data/raw/reference/caiso-supply-consistent-demand"
FILES = [
    ART_DIR / f"caiso_supply_consistent_demand_{y}.csv" for y in (2023, 2024, 2025)
] + [ART_DIR / "provenance.json"]
OUT = REPO / "results/calibration/_caiso260_demand_vintage_phase0.json"
YEARS = (2023, 2024, 2025)
T = 8760
HOD = np.arange(T) % 24
MD = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
MOH = np.repeat(np.arange(1, 13), np.array(MD) * 24)
#: PRECOMMIT sec 1 R-2 targets (ASSESSMENT-caiso259 sec 8), and tolerances.
R2_MAX_MW = {2023: 1452.0, 2024: 863.0, 2025: 583.0}
R2_ANNUAL_GWH = {2023: 69.0, 2024: -33.0, 2025: -753.0}
R2_TOL_MW, R2_TOL_GWH = 1.0, 1.0
NAMED_PLANTS = ("57901", "55077")  # El Segundo, Desert Star (P-3)


def _git_show(path: Path) -> bytes:
    rel = str(path.relative_to(REPO))
    return subprocess.run(
        ["git", "show", f"HEAD:{rel}"], cwd=REPO, check=True, capture_output=True
    ).stdout


def _run_derive() -> None:
    spec = importlib.util.spec_from_file_location(
        "derive_scd", REPO / "scripts/data/derive_caiso_supply_consistent_demand.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    rc = mod.main()
    if rc not in (None, 0):
        raise SystemExit(f"derive returned {rc}")


def _bench_plants_hourly(year: int) -> dict[str, np.ndarray]:
    """Current bench per-plant grid-delivered CEMS hourly, the derive's own construction."""
    import scripts.legitimacy_diagnostics as L
    from scripts import render_calibration_html as rch

    part = json.loads(
        gzip.decompress(
            (
                REPO / "frontend/data/backcast/bench/CAISO" / f"{year}.json.gz"
            ).read_bytes()
        )
    )
    bench = part["bench"]
    gas_groups = set(rch._GAS_GROUPS)
    plants = L.load_bench(REPO, "CAISO", year)
    out = {}
    for pid, meta in bench["plants"].items():
        if meta.get("nodata") or meta["group"] not in gas_groups:
            continue
        h = plants.get(pid)
        if h is None:
            continue
        c_ann = float(meta.get("c_ann") or 0.0)
        btm = float(meta.get("btm") or 0.0)
        share = (1.0 - btm / c_ann) if c_ann > 0 else 1.0
        out[str(pid)] = {
            "mw": h["mw"] * share,
            "name": meta.get("name"),
            "group": meta["group"],
        }
    return out


def _keeper_gas_error(year: int) -> np.ndarray:
    """The keeper's CEMS-basis gas error e_t (caiso-258 instrument, scorer's basis)."""
    spec = importlib.util.spec_from_file_location(
        "c258", REPO / "scripts/probes/_caiso258_hod2223_closure.py"
    )
    c258 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(c258)
    art = c258.load_artifacts(c258.KEEPER)
    return c258.cems_fleet(art, year)["e"]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--keep",
        action="store_true",
        help="leave the regenerated artifact on disk (the arm)",
    )
    a = ap.parse_args(_ARGV[1:])

    committed = {p: _git_show(p) for p in FILES}
    on_disk = {p: p.read_bytes() for p in FILES}
    if any(committed[p] != on_disk[p] for p in FILES):
        raise SystemExit(
            "artifact on disk is NOT the committed bytes — restore before running"
        )
    old = {
        y: pd.read_csv(ART_DIR / f"caiso_supply_consistent_demand_{y}.csv")
        for y in YEARS
    }
    old_prov = json.loads(committed[ART_DIR / "provenance.json"])

    res: dict = {"session": "caiso-260", "gates": {}, "years": {}}
    try:
        _run_derive()  # R-1: its own guards must pass unchanged
        res["gates"]["R1_derive_guards_pass"] = True
        new = {
            y: pd.read_csv(ART_DIR / f"caiso_supply_consistent_demand_{y}.csv")
            for y in YEARS
        }
        new_prov = json.loads((ART_DIR / "provenance.json").read_text())
        r2_ok, r3_ok = True, True
        F = {}
        for y in YEARS:
            o, n = old[y], new[y]
            d = (n["demand_mw"] - o["demand_mw"]).to_numpy(float)
            dc = (n["cems_gas_grid_mw"] - o["cems_gas_grid_mw"]).to_numpy(float)
            same = {
                c: bool(n[c].equals(o[c])) for c in ("netgen_mw", "ng_cell_mw", "ti_mw")
            }
            dflat = d - dc
            dflat_const = float(np.median(dflat))
            r3_year = (
                all(same.values()) and float(np.max(np.abs(dflat - dflat_const))) < 0.01
            )
            r3_ok &= r3_year
            mx, ann = float(np.abs(d).max()), float(d.sum() / 1e3)
            r2_year = (
                abs(mx - R2_MAX_MW[y]) <= R2_TOL_MW
                and abs(ann - R2_ANNUAL_GWH[y]) <= R2_TOL_GWH
            )
            r2_ok &= r2_year
            F[y] = float(np.abs(d).sum() / 1e3)
            # plant attribution: least squares of dcems on the named plants (+ const), then residual by plant
            bp = _bench_plants_hourly(y)
            X = np.column_stack(
                [bp[p]["mw"] for p in NAMED_PLANTS if p in bp] + [np.ones(T)]
            )
            coef, *_ = np.linalg.lstsq(X, dc, rcond=None)
            fitted = X @ coef
            resid = dc - fitted
            r2 = (
                1.0 - float((resid**2).sum() / ((dc - dc.mean()) ** 2).sum())
                if dc.std() > 0
                else None
            )
            # single-plant screen: which plants' series best explain dcems
            single = sorted(
                (
                    (
                        p,
                        float(np.corrcoef(v["mw"], dc)[0, 1])
                        if v["mw"].std() > 0
                        else 0.0,
                        v["name"],
                        float(v["mw"].sum() / 1e6),
                    )
                    for p, v in bp.items()
                ),
                key=lambda r: -abs(r[1]),
            )[:8]
            e = _keeper_gas_error(y)
            S = float((e * d).sum())
            bound = float(2 * abs(S) / T + (d**2).sum() / T)
            res["years"][str(y)] = {
                "R2": {
                    "max_abs_mw": mx,
                    "annual_gwh": ann,
                    "target": [R2_MAX_MW[y], R2_ANNUAL_GWH[y]],
                    "pass": r2_year,
                },
                "R3": {
                    "unchanged_columns": same,
                    "dflat_const_mw": dflat_const,
                    "dflat_max_dev_mw": float(np.max(np.abs(dflat - dflat_const))),
                    "pass": r3_year,
                },
                "provenance": {
                    "old": old_prov["years"][str(y)],
                    "new": new_prov["years"][str(y)],
                },
                "footprint_gross_gwh": F[y],
                "net_gwh": ann,
                "d_by_hod_mw": [float(d[HOD == h].mean()) for h in range(24)],
                "dcems_by_hod_mw": [float(dc[HOD == h].mean()) for h in range(24)],
                "d_by_month_mw": [float(d[MOH == m].mean()) for m in range(1, 13)],
                "d_hod2223_mw": float(d[np.isin(HOD, (22, 23))].mean()),
                "d_belly_1015_mw": float(d[np.isin(HOD, range(10, 16))].mean()),
                "d_night_0005_mw": float(d[np.isin(HOD, range(0, 6))].mean()),
                "d_evening_1721_mw": float(d[np.isin(HOD, range(17, 22))].mean()),
                "plant_attribution": {
                    "named": [p for p in NAMED_PLANTS if p in bp],
                    "coef": [float(c) for c in coef],
                    "r2": r2,
                    "named_share_of_abs_dcems": float(
                        np.abs(fitted - coef[-1]).sum() / np.abs(dc).sum()
                    )
                    if np.abs(dc).sum()
                    else None,
                    "top_corr_plants": single,
                },
                "C4_direction": {
                    "S_mw2h": S,
                    "sign": "worse" if S > 0 else "better",
                    "first_order_mse_bound_mw2": bound,
                    "keeper_mse_mw2": float((e**2).mean()),
                    "bound_share_of_mse": bound / float((e**2).mean()),
                },
            }
        res["gates"]["R2_pass"] = r2_ok
        res["gates"]["R3_pass"] = r3_ok
        res["screen_year"] = int(max(F, key=F.get))
        res["footprint_gross_gwh"] = F
        res["G_REPRO_pass"] = bool(r2_ok and r3_ok)
    finally:
        if not a.keep:
            for p, b in committed.items():
                p.write_bytes(b)
            res["artifact_state"] = "RESTORED to committed bytes"
        else:
            res["artifact_state"] = "REGENERATED files LEFT ON DISK (--keep: the arm)"
    OUT.write_text(json.dumps(res, indent=1, default=float) + "\n")

    print(
        f"R-1 {res['gates'].get('R1_derive_guards_pass')}  R-2 {res['gates'].get('R2_pass')}  R-3 {res['gates'].get('R3_pass')}  -> G-REPRO {res.get('G_REPRO_pass')}"
    )
    for y in YEARS:
        r = res["years"][str(y)]
        print(
            f"{y}: max|d| {r['R2']['max_abs_mw']:.1f} MW annual {r['R2']['annual_gwh']:+.1f} GWh | gross F {r['footprint_gross_gwh']:.1f} GWh | dflat {r['R3']['dflat_const_mw']:+.1f} MW | hod22-23 {r['d_hod2223_mw']:+.0f} belly {r['d_belly_1015_mw']:+.0f} night {r['d_night_0005_mw']:+.0f} eve {r['d_evening_1721_mw']:+.0f}"
        )
        print(f"     d by hod {[round(x) for x in r['d_by_hod_mw']]}")
        print(f"     d by month {[round(x) for x in r['d_by_month_mw']]}")
        pa = r["plant_attribution"]
        print(
            f"     attribution named {pa['named']} coef {[round(c, 3) for c in pa['coef']]} r2 {pa['r2']} named share {pa['named_share_of_abs_dcems']}"
        )
        for p in pa["top_corr_plants"][:5]:
            print(
                f"        {p[0]:>6} corr {p[1]:+.3f} {str(p[2])[:30]:30s} {p[3]:.2f} TWh"
            )
        c4 = r["C4_direction"]
        print(
            f"     C4 S {c4['S_mw2h']:+.3e} -> {c4['sign']}; bound {c4['bound_share_of_mse'] * 100:.2f} % of keeper MSE"
        )
    print(
        f"screen year by gross footprint: {res.get('screen_year')}  ({res.get('footprint_gross_gwh')})"
    )
    print(res["artifact_state"], "| wrote", OUT)


if __name__ == "__main__":
    main()
