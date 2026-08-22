"""miso-177 pre-solve instrument: the rho A/B's frozen coefficients and surface.

Engine-frozen BEFORE either solve (the miso-175 discipline): everything here
is read from the PRODUCTION seam at HEAD and the KEEPER'S OWN COMMITTED
sidecars (``results/calibration/miso175_hourkey/hourly``) — no LP, no
re-derivation. Freezes, for PREREG-miso177's gates:

* **I-1 the coefficients** — the exact value each arm consumes through
  ``data.online_reserve_rho`` (control: ``rho_used`` = the 0.5 floor; arm:
  ``rho_used_no_floor`` = the measured statistic), plus the artifact's
  sha256, so R-1 can verify the solved coefficient against a digest fixed
  before any result existed.
* **I-2 the static binding surface** — per year, the hours where
  ``rho x SumP_elig(t) < requirement(t)`` on the keeper's committed
  dispatch, at BOTH rho values. At those hours the gated Reg+Spin family
  cannot reach its requirement from the coupling rows alone at the keeper's
  dispatch — the LP must either re-dispatch (commit more) or price the
  published $65/$98 curve. A LOWER-BOUND prediction of where the arm can
  act, and the basis of the frozen direction (R-2b) and the honest ceiling.

``SumP_elig`` is the class-grain sum over the pergen-eligible classes
(RESERVE_FUEL_TYPES minus nuclear, which carries no RAMP10_FRAC entry):
coal x3, CC_REGULAR/CC_CHP, CT_PEAKER/CT_CHP, ST_GAS/ST_CHP, oil. Class
grain slightly OVERSTATES SumP wherever an in-class tranche carries zero
ramp10 (understating the surface) — disclosed; the kill gates score the
actual LP, never this instrument.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

import pandas as pd  # noqa: E402

from market_sim.data.online_reserve_rho import (  # noqa: E402
    RHO_CLIP,
    _artifact_path,
    load_online_rho,
)

KEEPER = REPO / "results" / "calibration" / "miso175_hourkey"
ELIGIBLE_KLASSES = [
    "COAL_BIT",
    "COAL_LIGNITE",
    "COAL_PRB",
    "CC_REGULAR",
    "CC_CHP",
    "CT_PEAKER",
    "CT_CHP",
    "ST_GAS",
    "ST_CHP",
    "oil",
]
OUT = REPO / "results" / "calibration" / "_miso177_rho_instrument.json"


def main() -> None:
    measured = load_online_rho("MISO", "miso_reg_spin")
    assert measured is not None, "MISO measured-rho artifact missing"
    art = _artifact_path("MISO")
    record: dict = {
        "session": "miso-177",
        "keeper": "2026-08-22-miso-175-hourkey",
        "artifact": {
            "path": str(art.relative_to(REPO)),
            "sha256": hashlib.sha256(art.read_bytes()).hexdigest(),
        },
        "coefficients": {
            "rho_measured": measured.rho,
            "rho_control_consumes": measured.rho_used,
            "rho_arm_consumes": measured.rho_used_no_floor,
            "rho_clip": list(RHO_CLIP),
            "tightening_factor": measured.rho_used / measured.rho_used_no_floor,
            "online_unit_hours": measured.online_unit_hours,
            "campd_coverage_frac": measured.campd_coverage_frac,
        },
        "years": {},
    }
    for year in (2023, 2024, 2025):
        rf = pd.read_parquet(KEEPER / "hourly" / f"reserve_family_{year}.parquet")
        rs = rf[rf["family"] == "miso_rbdc_regspin"].sort_values("hour")
        req = rs["requirement_mw"].to_numpy()
        dual = rs["dual"].to_numpy()
        ch = pd.read_parquet(KEEPER / "hourly" / f"class_hourly_{year}.parquet")
        p1 = ch[ch["pass"] == "P1"] if "pass" in ch.columns else ch
        elig = (
            p1[p1["klass"].isin(ELIGIBLE_KLASSES)]
            .groupby("hour")["mw"]
            .sum()
            .reindex(range(len(req)), fill_value=0.0)
            .to_numpy()
        )
        floor_surface = (RHO_CLIP[0] * elig) < req
        arm_surface = (measured.rho_used_no_floor * elig) < req
        record["years"][str(year)] = {
            "requirement_mean_mw": float(req.mean()),
            "requirement_max_mw": float(req.max()),
            "keeper_regspin_dual_pos_hours": int((dual > 1e-9).sum()),
            "keeper_regspin_dual_max": float(dual.max()),
            "sum_p_elig_mean_mw": float(elig.mean()),
            "sum_p_elig_min_mw": float(elig.min()),
            "static_surface_hours_at_floor_0p5": int(floor_surface.sum()),
            "static_surface_hours_at_measured": int(arm_surface.sum()),
            "new_static_surface_hours": int((arm_surface & ~floor_surface).sum()),
            # Crude ceiling: every new static-surface hour pricing the full
            # $98 Schedule-28 step into the energy balance, demand-weighted
            # flat. The real effect is bounded far below (the LP re-dispatches
            # first; the curve steps down to $65/$0).
            "annual_price_ceiling_pct_of_40usd": float(
                (arm_surface & ~floor_surface).sum() * 98.0 / 8760 / 40.0 * 100.0
            ),
        }
    OUT.write_text(json.dumps(record, indent=1) + "\n")
    print(json.dumps(record, indent=1))
    print(f"\nfrozen -> {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
