"""PJM-NEXT-11 card 1 bound (zero LP): the most an offered-EcoMax cap could remove from COAL_BIT.

For each bench COAL_BIT plant (the keeper's registered run payload, PJM-NEXT-10's helpers), the
energy the model dispatches above ``r x`` the plant's own model maximum, where ``r`` is that year's
measured LONG_RUN ``E/T`` (``_pjmnext11_offered_ecomax.json``). That is an UPPER bound on what
capping the plant at its offered EcoMax could remove (it assumes every coal unit carries the
segment-mean ratio and that the model maximum is the curve top). CAMPD is read the same way, so
the bound's model-minus-actual difference is the most the cap could move C1.
Writes ``results/phase0/pjm/_pjmnext11_ecomax_bound.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts/probes"))
import _pjmnext10_coal_phase0 as P10  # noqa: E402

RATIO = REPO / "results/phase0/pjm/_pjmnext11_offered_ecomax.json"
OUT = REPO / "results/phase0/pjm/_pjmnext11_ecomax_bound.json"


def above(x: np.ndarray, r: float) -> float:
    """MWh above ``r`` x the series maximum."""
    return float(np.maximum(0.0, x - r * x.max()).sum()) if x.max() > 0 else 0.0


def main() -> None:
    """Bound per year at the year's own ratio and at the 2023/24 reference ratio."""
    ratio = json.loads(RATIO.read_text())
    ref = np.mean([ratio[y]["year"]["E_over_T"] for y in ("2023", "2024")])
    run = P10.load_run()
    out = {}
    for y in P10.YEARS:
        r = ratio[str(y)]["year"]["E_over_T"]
        ps = P10.plant_series(y, run)
        rec = {"ratio": r, "ref_ratio": round(float(ref), 4)}
        for tag, rr in (("own", r), ("ref", ref)):
            rec[f"model_above_{tag}_twh"] = round(
                sum(above(m, rr) for m, _c, _v in ps.values()) / 1e6, 2
            )
            rec[f"campd_above_{tag}_twh"] = round(
                sum(above(c, rr) for _m, c, _v in ps.values()) / 1e6, 2
            )
        rec["cap_effect_on_c1_twh"] = round(
            -(rec["model_above_own_twh"] - rec["campd_above_own_twh"]), 2
        )
        rec["year_discriminating_part_twh"] = round(
            -(rec["model_above_own_twh"] - rec["model_above_ref_twh"]), 2
        )
        out[str(y)] = rec
        print(y, rec)
    OUT.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
