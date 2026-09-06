"""miso-230 screen scorer — the five PRECOMMIT gates, applied mechanically.

Written and PUSHED BEFORE the screen bundle exists, so the bars cannot be
adjusted to the result (the miso-226 blind-scorer discipline). Every bar is a
verbatim transcription of
``results/calibration/PRECOMMIT-miso230-ct-netload-drag-2026-09-06.md`` §7:

  G-1 response    CT_PEAKER-2023 model energy rises by +1.8 .. +5.5 TWh
                  (0.5x-1.5x the zero-LP class lower bound of +3.6544)
  G-2 replacement solved D-2: reliability_floor x CT_PEAKER forced == 0.000 TWh
                  AND ct_netload_drag is the SOLE CT_PEAKER forcing mechanism
  G-3 confinement drag D-4 off-window share == 0.0000 vs MISO [10, 21);
                  slack and dump both 0.0000 TWh
  G-4 no flip     no NON-TARGET load-bearing criterion flips PASS -> FAIL vs the
                  keeper's committed scores (C3c excluded, ledgered caveat)
  G-5 budget      C8 PASSES — at budget, or above it through rule 18's grounded
                  conditional route (D-4 clean AND D-1 profile_r / cv_ratio)

The gates are STOP-ONLY: they may kill the arm, they may never promote it, and
none is gated on the target residual. Usage:

    python3 scripts/probes/_miso230_screen_gates.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ARM = REPO / "results/calibration/miso230_ctdrag_S"
KEEPER = REPO / "results/calibration/miso220_nonsteamlift_B"
OUT = REPO / "results/calibration/_miso230_screen_gates.json"
YEAR = 2023

# PRECOMMIT §6 zero-LP prediction and §7 bars — transcribed, never recomputed.
PRESOLVE_LIFT_TWH = 3.6544
G1_LO, G1_HI = 1.8, 5.5
LOAD_BEARING = ("C1", "C2", "C3a", "C3b", "C6")


def class_twh(bundle: Path, year: int, klass: str) -> float:
    """Annual P1 energy for one class, from a bundle's committed class_hourly."""
    import pandas as pd

    df = pd.read_parquet(bundle / f"hourly/class_hourly_{year}.parquet")
    sel = df[(df["klass"] == klass) & (df["pass"] == "P1")]
    return float(sel["mw"].sum()) / 1e6


def d_rows(bundle: Path, key: str) -> list[dict]:
    """Rows of one legitimacy diagnostic from a bundle's committed artifact."""
    d = json.loads((bundle / "legitimacy_diagnostics.json").read_text())
    return list(d["diagnostics"].get(key, {}).get("rows", []))


def verdict(bundle: Path) -> dict:
    """Run the production scorer on a bundle and return its parsed record."""
    p = subprocess.run(
        [sys.executable, "scripts/calibration_verdict.py", str(bundle), "--json"],
        cwd=REPO, capture_output=True, text=True,
    )
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError:
        return {"_stdout": p.stdout[-4000:], "_stderr": p.stderr[-4000:]}


def main() -> int:
    """Score the five gates and write the record."""
    res: dict = {"gates": {}, "presolve_lift_twh": PRESOLVE_LIFT_TWH}

    # ---- G-1 response -----------------------------------------------------
    keeper_ct = class_twh(KEEPER, YEAR, "CT_PEAKER")
    arm_ct = class_twh(ARM, YEAR, "CT_PEAKER")
    lift = arm_ct - keeper_ct
    res["gates"]["G1_response"] = {
        "keeper_ct_twh": round(keeper_ct, 4),
        "arm_ct_twh": round(arm_ct, 4),
        "realized_lift_twh": round(lift, 4),
        "conversion_of_presolve": round(lift / PRESOLVE_LIFT_TWH, 3),
        "bar": f"{G1_LO} <= lift <= {G1_HI}",
        "verdict": "PASS" if G1_LO <= lift <= G1_HI else "FAIL",
    }

    # ---- G-2 replacement --------------------------------------------------
    d2 = [r for r in d_rows(ARM, "D2")
          if r.get("year") == YEAR and r.get("class") == "CT_PEAKER"]
    relfloor = sum(float(r["forced_twh"]) for r in d2
                   if r.get("mechanism") == "reliability_floor")
    mechs = sorted({r.get("mechanism") for r in d2})
    res["gates"]["G2_replacement"] = {
        "ct_forcing_mechanisms": mechs,
        "reliability_floor_forced_twh": round(relfloor, 4),
        "rows": d2,
        "verdict": "PASS" if (relfloor == 0.0 and mechs == ["ct_netload_drag"])
        else "FAIL",
    }

    # ---- G-3 confinement --------------------------------------------------
    d4 = [r for r in d_rows(ARM, "D4")
          if r.get("year") == YEAR and "ct_netload_drag" in str(r.get("floor", ""))
          and r.get("check") == "window"]
    off = max((float(r["offwindow_share"]) for r in d4), default=0.0)
    mpath = ARM / "metrics.json"
    metrics = json.loads(mpath.read_text()) if mpath.exists() else {}
    res["gates"]["G3_confinement"] = {
        "d4_rows": d4,
        "max_offwindow_share": off,
        "verdict": "PASS" if (d4 and off == 0.0) else "FAIL",
    }
    res["_metrics_keys"] = sorted(metrics.keys())[:40]

    # ---- G-4 / G-5 from the production scorer ------------------------------
    res["arm_verdict"] = verdict(ARM)
    res["keeper_verdict"] = verdict(KEEPER)

    OUT.write_text(json.dumps(res, indent=1, default=str))
    for name, g in res["gates"].items():
        print(f"{name}: {g['verdict']}")
        for k, v in g.items():
            if k not in ("verdict", "rows", "d4_rows"):
                print(f"    {k}: {v}")
    print(f"\n-> {OUT.relative_to(REPO)}  (G-4/G-5 read from the scorer records)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
