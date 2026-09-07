"""miso-233 screen gates — scored BLIND, written and pushed while the LP runs.

Reads the four gates fixed in
``results/calibration/PRECOMMIT-miso233-spp-hourly-seam-2026-09-07.md`` §4 off the
screen bundle's committed sidecars and the keeper's, prints a verdict table and
writes ``results/calibration/_miso233_screen_gates.json``. Exit 1 on any FAIL.

**The bars are copied from the PRECOMMIT, not recomputed here**, and this file is
committed before the arm's bundle is opened so it cannot be written to fit a
result. Rule 29 ``[R-SCREEN]``: the screen is a STOP gate — it may kill this arm
and it may never promote one; nothing printed here is a determination.

**NONE OF THE FOUR GATES IS THE TARGET RESIDUAL.** The price-decile slope this
lane wants to move is REPORTED at the bottom and gates nothing: a screen that
read "did the slope improve" would be the fitted-mechanism selection rule 1
``[R-STRUCT]`` forbids, done one year at a time.

G-4 (no collateral flip) is scored by the standing ``screen_collateral_gate.py``
tool, not here; its verdict is folded in by the session.

Usage: python3 scripts/probes/_miso233_screen_gates.py <screen-bundle-dir>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

KEEPER = REPO / "results/calibration/miso232_hourlyseam_K"
OUT = REPO / "results/calibration/_miso233_screen_gates.json"
YEAR = 2023
BUS = "MISO_external"
ZONE = "MISO-Indiana"
HOURS = 8760

# --- BARS, copied verbatim from the PRECOMMIT §4 ------------------------------
G2_IMPORT_TWH_TOL = 1.5      # |delta annual gross imports| vs the keeper
G3_CORR_RISE_TOL = 0.05      # corr(imports, own hub price) may not RISE past this
G1_BASE_TWH_TOL = 0.05       # per-class must-take energy tolerance
G1_BASE_CLASSES = ("wind", "solar", "nuclear", "hydro")


def _class_energy(bundle: Path, year: int) -> dict[str, float]:
    f = pd.read_parquet(bundle / f"hourly/class_hourly_{year}.parquet")
    f = f[f["pass"] == "P1"]
    return {
        str(k): float(v) / 1e6
        for k, v in f.groupby("klass")["mw"].sum().items()
    }


def _imports(bundle: Path, year: int) -> np.ndarray:
    f = pd.read_parquet(bundle / f"hourly/class_hourly_{year}.parquet")
    f = f[(f["pass"] == "P1") & (f["klass"] == "import")]
    return (
        f.groupby("hour")["mw"].sum().reindex(range(HOURS)).fillna(0.0).to_numpy(float)
    )


def _system(bundle: Path, year: int) -> pd.DataFrame:
    f = pd.read_parquet(bundle / f"hourly/system_{year}.parquet")
    return f[f["pass"] == "P1"]


def _bus_price(bundle: Path, year: int, zone: str) -> np.ndarray:
    s = _system(bundle, year)
    return s[s["zone"] == zone].sort_values("hour")["price"].to_numpy(float)


def _hub_price(bundle: Path, year: int) -> np.ndarray:
    """The model's own MISO-Indiana hub price — the G-3 basis (miso-231's)."""
    return _bus_price(bundle, year, ZONE)


def decile_slope(price: np.ndarray, series: np.ndarray) -> float:
    order = np.argsort(price, kind="stable")
    parts = np.array_split(order, 10)
    means = [float(series[p].mean()) for p in parts]
    return means[0] - means[-1]


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__.strip().splitlines()[-1])
        return 2
    arm = Path(argv[1])
    if not arm.is_absolute():
        arm = REPO / arm

    k_imp, a_imp = _imports(KEEPER, YEAR), _imports(arm, YEAR)
    k_sys, a_sys = _system(KEEPER, YEAR), _system(arm, YEAR)
    k_cls, a_cls = _class_energy(KEEPER, YEAR), _class_energy(arm, YEAR)
    k_hub, a_hub = _hub_price(KEEPER, YEAR), _hub_price(arm, YEAR)

    gates: dict[str, dict] = {}

    # --- G-1 CONFINEMENT ------------------------------------------------------
    k_slack = float(k_sys["slack"].sum()) / 1e6
    a_slack = float(a_sys["slack"].sum()) / 1e6
    a_dump = float(a_sys["dump"].sum()) / 1e6
    base_moves = {
        c: round(a_cls.get(c, 0.0) - k_cls.get(c, 0.0), 4) for c in G1_BASE_CLASSES
    }
    g1 = (
        a_slack <= k_slack + 1e-9
        and abs(a_dump) <= 1e-9
        and all(abs(v) <= G1_BASE_TWH_TOL for v in base_moves.values())
    )
    gates["G-1 confinement"] = {
        "bar": f"slack <= keeper {k_slack:.4f} TWh; dump = 0; "
        f"{'/'.join(G1_BASE_CLASSES)} each within {G1_BASE_TWH_TOL} TWh",
        "keeper_slack_twh": round(k_slack, 4),
        "arm_slack_twh": round(a_slack, 4),
        "arm_dump_twh": round(a_dump, 4),
        "must_take_moves_twh": base_moves,
        "verdict": "PASS" if g1 else "FAIL",
    }

    # --- G-2 FOOTPRINT SCALE --------------------------------------------------
    k_twh, a_twh = k_imp.sum() / 1e6, a_imp.sum() / 1e6
    d_twh = float(a_twh - k_twh)
    g2 = abs(d_twh) <= G2_IMPORT_TWH_TOL
    gates["G-2 footprint scale"] = {
        "bar": f"|delta annual gross imports| <= {G2_IMPORT_TWH_TOL} TWh",
        "keeper_twh": round(float(k_twh), 3),
        "arm_twh": round(float(a_twh), 3),
        "delta_twh": round(d_twh, 3),
        "verdict": "PASS" if g2 else "FAIL",
    }

    # --- G-3 DIRECTION --------------------------------------------------------
    k_corr = float(np.corrcoef(k_imp, k_hub)[0, 1])
    a_corr = float(np.corrcoef(a_imp, a_hub)[0, 1])
    g3 = (a_corr - k_corr) <= G3_CORR_RISE_TOL
    gates["G-3 direction"] = {
        "bar": f"corr(imports, own hub price) may not RISE more than "
        f"+{G3_CORR_RISE_TOL} above the keeper",
        "keeper_corr": round(k_corr, 4),
        "arm_corr": round(a_corr, 4),
        "change": round(a_corr - k_corr, 4),
        "verdict": "PASS" if g3 else "FAIL",
    }

    # --- REPORTED, GATES NOTHING ---------------------------------------------
    from _miso224_floor_anatomy_phase0 import actual_zone_price

    act = actual_zone_price(YEAR)[ZONE].to_numpy(float)
    ok = np.isfinite(act)
    reported = {
        "note": "the target residual. REPORTED, NEVER GATED (rule 1 [R-STRUCT], "
        "PRECOMMIT §4).",
        "keeper_decile_slope_measured_price_mw": round(
            decile_slope(act[ok], k_imp[ok]), 1
        ),
        "arm_decile_slope_measured_price_mw": round(
            decile_slope(act[ok], a_imp[ok]), 1
        ),
        "measured_target_mw": 1303.0,
        "keeper_corr_imports_measured_price": round(
            float(np.corrcoef(k_imp[ok], act[ok])[0, 1]), 4
        ),
        "arm_corr_imports_measured_price": round(
            float(np.corrcoef(a_imp[ok], act[ok])[0, 1]), 4
        ),
        "class_energy_moves_twh": {
            c: round(a_cls.get(c, 0.0) - k_cls.get(c, 0.0), 3)
            for c in sorted(set(k_cls) | set(a_cls))
            if abs(a_cls.get(c, 0.0) - k_cls.get(c, 0.0)) >= 0.005
        },
    }

    report = {
        "probe": "miso-233 screen gates (2023)",
        "keeper": "2026-09-06-miso-232-hourly-seam",
        "arm_bundle": str(arm.relative_to(REPO)),
        "gates": gates,
        "reported_not_gated": reported,
        "g4": "scored separately by scripts/screen_collateral_gate.py",
    }
    OUT.write_text(json.dumps(report, indent=1) + "\n")

    print(f"\nmiso-233 SCREEN GATES — {YEAR}, arm {arm.name}\n")
    failed = []
    for name, g in gates.items():
        print(f"  {g['verdict']:<4}  {name}")
        print(f"        bar: {g['bar']}")
        for k, v in g.items():
            if k in ("bar", "verdict"):
                continue
            print(f"        {k}: {v}")
        if g["verdict"] == "FAIL":
            failed.append(name)
    print("\n  REPORTED, GATES NOTHING:")
    for k, v in reported.items():
        print(f"        {k}: {v}")
    print(f"\nwrote {OUT}")
    if failed:
        print(f"\nSCREEN VERDICT: KILLED on {', '.join(failed)}")
        return 1
    print("\nSCREEN VERDICT: G-1..G-3 CLEAR (G-4 scored separately)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
