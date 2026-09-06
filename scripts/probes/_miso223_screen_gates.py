"""miso-223 screen gates — arm vs same-HEAD control, 2024 only.

Committed BLIND, before either solve finished, so the gates cannot be written to
fit the result (the miso-201 discipline). Scores exactly the five gates
pre-registered in ``results/calibration/PREREG-miso223-committed-band-debody-2026-09-06.md``
section 5. Every gate is STRUCTURAL and STOP-ONLY: a gate may kill the arm, none
may promote it, and none reads the target price residual (rule 1 ``[R-STRUCT]``,
rule 29 ``[R-SCREEN]``).

S-1  single delta      exactly 11 offer_curve_by_group ``committed`` values differ
S-2  liveness          the arm's recorded table == keeper table with those 11 subs
G-1  direction/size    2024 body (bottom-90%) mean price falls by $1.0-$2.2
G-2  confinement       2024 tail (top-10%) mean price moves by less than |$3.0|
G-3  no flip           no 2024 C1/C2 cell flips PASS -> FAIL

Usage::

    python3 scripts/probes/_miso223_screen_gates.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
CAL = REPO / "results" / "calibration"
KEEPER = CAL / "miso220_nonsteamlift_B"
ARM = CAL / "miso223_debody_B"
CONTROL = CAL / "miso223_control_A"
YEAR = 2024

REVERTED = {
    "CC_REGULAR": 1.0050, "CC_INTERMEDIATE": 1.0050, "CC_CHP": 1.0,
    "CT_CHP": 1.0, "CT_PEAKER": 1.0250, "CT_INTERMEDIATE": 1.0,
    "COAL_LIGNITE": 1.0, "COAL_PRB": 1.0, "COAL_BIT": 1.0,
    "COAL_WC": 1.0, "COAL": 1.0,
}


def _cfg(bundle: Path) -> dict:
    raw = json.loads((bundle / "run_config.json").read_text())
    return raw.get("scenario_config", raw)


def _system_price(bundle: Path, year: int) -> np.ndarray:
    """Load-weighted system price, one value per hour, P1 only."""
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    df = df[df["pass"] == "P1"]
    g = df.groupby("hour").apply(
        lambda d: np.average(d["price"], weights=d["demand"]), include_groups=False
    )
    return g.sort_index().to_numpy()


def _body_tail(p: np.ndarray) -> tuple[float, float]:
    """Mean of the bottom 90% and of the top 10% of the own-year distribution."""
    s = np.sort(p)
    k = int(np.ceil(0.10 * s.size))
    return float(s[:-k].mean()), float(s[-k:].mean())


def gate_s1(arm: dict, keeper: dict) -> dict:
    """Exactly the 11 pre-registered ``committed`` values differ; nothing else."""
    a, k = arm["offer_curve_by_group"], keeper["offer_curve_by_group"]
    diffs = []
    for cls in sorted(set(a) | set(k)):
        for band in sorted(set(a.get(cls, {})) | set(k.get(cls, {}))):
            va, vk = a.get(cls, {}).get(band), k.get(cls, {}).get(band)
            if va != vk:
                diffs.append({"class": cls, "band": band, "keeper": vk, "arm": va})
    expected = {(c, "committed") for c in REVERTED}
    got = {(d["class"], d["band"]) for d in diffs}
    other = {key: (arm.get(key), keeper.get(key)) for key in sorted(set(arm) | set(keeper))
             if key != "offer_curve_by_group" and arm.get(key) != keeper.get(key)}
    return {"gate": "S-1 single delta", "n_band_diffs": len(diffs), "diffs": diffs,
            "other_config_diffs": other,
            "pass": got == expected and len(diffs) == 11 and not other}


def gate_s2(arm: dict, keeper: dict) -> dict:
    """The arm's recorded table equals the keeper's with the 11 substitutions."""
    want = {c: dict(b) for c, b in keeper["offer_curve_by_group"].items()}
    for cls, val in REVERTED.items():
        want[cls]["committed"] = val
    got = arm["offer_curve_by_group"]
    return {"gate": "S-2 liveness", "table_matches_declared": got == want, "pass": got == want}


def gate_g1_g2(arm_p: np.ndarray, ctl_p: np.ndarray) -> list[dict]:
    """Direction/magnitude on the body; confinement on the tail."""
    ab, at = _body_tail(arm_p)
    cb, ct = _body_tail(ctl_p)
    dbody, dtail = ab - cb, at - ct
    return [
        {"gate": "G-1 body direction & magnitude", "control_body": round(cb, 3),
         "arm_body": round(ab, 3), "delta": round(dbody, 3),
         "band": "[-2.2, -1.0]", "pass": -2.2 <= dbody <= -1.0},
        {"gate": "G-2 tail confinement", "control_tail": round(ct, 3),
         "arm_tail": round(at, 3), "delta": round(dtail, 3),
         "band": "|delta| < 3.0", "pass": abs(dtail) < 3.0},
    ]


def gate_g3() -> dict:
    """No 2024 C1/C2 cell flips PASS -> FAIL (scored from each bundle's metrics.json)."""
    def cells(bundle: Path) -> dict:
        path = bundle / "metrics.json"
        if not path.exists():
            return {}
        m = json.loads(path.read_text())
        return {k: v.get("status") for k, v in (m.get("criteria") or {}).items()
                if k in {"fuelmix", "sysvol"}}
    a, c = cells(ARM), cells(CONTROL)
    flips = [k for k in c if c[k] == "PASS" and a.get(k) not in (None, "PASS")]
    return {"gate": "G-3 no non-target load-bearing flip", "control": c, "arm": a,
            "flips": flips, "scored": bool(a and c), "pass": bool(a and c) and not flips}


def main() -> None:
    keeper, arm = _cfg(KEEPER), _cfg(ARM)
    rows = [gate_s1(arm, keeper), gate_s2(arm, keeper)]
    rows += gate_g1_g2(_system_price(ARM, YEAR), _system_price(CONTROL, YEAR))
    rows.append(gate_g3())
    verdict = "SCREEN CLEARED" if all(r["pass"] for r in rows) else "SCREEN KILLS THE ARM"
    out = {"probe": "miso-223 screen gates", "year": YEAR, "arm": str(ARM),
           "control": str(CONTROL), "keeper": str(KEEPER),
           "prereg": "results/calibration/PREREG-miso223-committed-band-debody-2026-09-06.md",
           "gates": rows, "verdict": verdict}
    dest = CAL / "_miso223_screen_gates.json"
    dest.write_text(json.dumps(out, indent=1))
    for r in rows:
        print(f'{"PASS" if r["pass"] else "FAIL"}  {r["gate"]}')
    print(f"\n{verdict}  ->  {dest}")


if __name__ == "__main__":
    main()
