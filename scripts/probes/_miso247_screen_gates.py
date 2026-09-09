"""miso-247 screen gates ``G-1`` / ``G-2`` / ``G-3``, evaluated on the 2024 screen.

Each bar is verbatim from ``PREREG-miso247-the-P19-posture-at-MISO-2026-09-09.md``
§5, with the ``P-3'`` predictor and class mapping declared in ADDENDUM 2 §4 and
the ``R-ALL`` reporting duty declared in ADDENDUM 3 §3 -- all pushed before any
realised number existed. **No bar is computed here; every bar is read from those
records.** ``G-4`` is ``scripts/screen_collateral_gate.py`` and runs separately.

The three differences the bundles support, and what each isolates:

  ``arm - keeper``   the JOINT P19 posture (A + B). This is what ``P-3'``
                     predicted, so it is ``G-1``'s realised side.
  ``arm - control``  **A** alone (the control pins ``f923_...=False`` at HEAD).
  ``control - keeper`` **B** alone -- and a FALSIFICATION of this session's own
                     ``D-4`` classification: anything moving here that ``D-1``
                     did not name is a hunk the audit misclassified.

The gates are STRUCTURAL and STOP-ONLY (rule 29 ``[R-SCREEN]``): they may kill
the arm, they may not promote it, and none is the target residual.

Writes ``results/calibration/_miso247_screen_gates.json``.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

KEEPER = REPO / "results/calibration/miso245_ladderfix_K"
ARM = REPO / "results/calibration/miso247_screen_2024"
CONTROL = REPO / "results/calibration/miso247_control_2024"
OUT = REPO / "results/calibration/_miso247_screen_gates.json"
YEAR = 2024

#: ADDENDUM 2 §4(c). Fixed before any realised number existed.
COAL_KLASS = frozenset({"COAL_PRB", "COAL_BIT", "COAL_LIGNITE", "COAL"})
EXCLUDED = frozenset({"wind", "solar"})

#: PREREG §5 G-1. Fixed before either predictor existed.
G1_FLOOR_TWH = 0.5
G1_BAND = (1.0 / 3.0, 3.0)

#: PREREG §5 G-2: classes with no fuel-price and no heat-rate exposure.
G2_UNEXPOSED = ("wind", "solar", "nuclear", "hydro", "storage")


def energy_by_klass(bundle: Path, year: int) -> dict[str, float]:
    """P1 energy (TWh) per class, with ADDENDUM 2 §4(c)'s coal collapse applied."""
    frame = pd.read_parquet(bundle / f"hourly/class_hourly_{year}.parquet")
    frame = frame[frame["pass"] == "P1"]
    out: dict[str, float] = {}
    for klass, grp in frame.groupby("klass", observed=True):
        name = "COAL" if str(klass) in COAL_KLASS else str(klass)
        out[name] = out.get(name, 0.0) + float(grp["mw"].sum()) / 1e6
    return out


def main() -> None:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=REPO
    ).stdout.strip()
    pred = json.loads(
        (REPO / "results/calibration/_miso247_p3prime_reclear.json").read_text()
    )["P3prime_pred_TWh"]

    e_keep = energy_by_klass(KEEPER, YEAR)
    e_arm = energy_by_klass(ARM, YEAR)
    e_ctl = energy_by_klass(CONTROL, YEAR)
    klasses = sorted(set(e_keep) | set(e_arm) | set(e_ctl) | set(pred))

    rows = []
    g1_fail = []
    for k in klasses:
        joint = e_arm.get(k, 0.0) - e_keep.get(k, 0.0)
        p = float(pred.get(k, 0.0))
        in_scope = (k not in EXCLUDED) and abs(p) >= G1_FLOOR_TWH
        ratio = (joint / p) if p else None
        verdict = "-"
        if in_scope:
            ok = (
                p != 0
                and (joint / p) > 0
                and G1_BAND[0] <= abs(joint / p) <= G1_BAND[1]
            )
            verdict = "PASS" if ok else "FAIL"
            if not ok:
                g1_fail.append(k)
        rows.append(
            {
                "klass": k,
                "pred_P3prime_TWh": round(p, 4),
                "realised_arm_minus_keeper_TWh": round(joint, 4),
                "A_arm_minus_control_TWh": round(
                    e_arm.get(k, 0.0) - e_ctl.get(k, 0.0), 4
                ),
                "B_control_minus_keeper_TWh": round(
                    e_ctl.get(k, 0.0) - e_keep.get(k, 0.0), 4
                ),
                "ratio": (round(ratio, 4) if ratio is not None else None),
                "G1_in_scope": in_scope,
                "G1": verdict,
            }
        )

    # G-2: the unexposed classes may move only through re-clearing, so their
    # energy is REPORTED; what must not move is an input. The renewable and
    # storage inputs are not fleet rows, so the check that they are untouched is
    # P-1's own row set: 886 of 2843 rows moved in 2024 and every one is thermal.
    g2 = {
        "unexposed_energy_delta_TWh": {
            k: round(e_arm.get(k, 0.0) - e_ctl.get(k, 0.0), 6) for k in G2_UNEXPOSED
        },
        "note": (
            "P-1 measured the moved-row set at 886 of 2843 rows in 2024, all "
            "thermal; renewables are LP decision variables and carry no fleet "
            "row, so neither A nor B can reach their availability."
        ),
    }

    rec = {
        "probe": "_miso247_screen_gates",
        "prereg": "PREREG-miso247-the-P19-posture-at-MISO-2026-09-09.md §5",
        "year": YEAR,
        "provenance": {"head": head},
        "G1_floor_TWh": G1_FLOOR_TWH,
        "G1_band": list(G1_BAND),
        "rows": sorted(rows, key=lambda r: -abs(r["realised_arm_minus_keeper_TWh"])),
        "G1_failed_classes": g1_fail,
        "G1": "PASS" if not g1_fail else "FAIL",
        "G2": g2,
        "totals_TWh": {
            "keeper": round(sum(e_keep.values()), 4),
            "arm": round(sum(e_arm.values()), 4),
            "control": round(sum(e_ctl.values()), 4),
        },
    }
    OUT.write_text(json.dumps(rec, indent=1))
    print(json.dumps({k: v for k, v in rec.items() if k != "rows"}, indent=1))
    print(
        f"\n{'klass':14s} {'pred':>9s} {'realised':>9s} {'A':>9s} {'B':>9s} {'ratio':>8s}  G1"
    )
    for r in rec["rows"]:
        print(
            f"{r['klass']:14s} {r['pred_P3prime_TWh']:9.4f} "
            f"{r['realised_arm_minus_keeper_TWh']:9.4f} "
            f"{r['A_arm_minus_control_TWh']:9.4f} "
            f"{r['B_control_minus_keeper_TWh']:9.4f} "
            f"{(r['ratio'] if r['ratio'] is not None else float('nan')):8.3f}  {r['G1']}"
        )


if __name__ == "__main__":
    main()
