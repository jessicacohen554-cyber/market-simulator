"""miso-226 phase 0 — the SEAM-ALONE arm's own pre-solve arithmetic: how much import MW does the neighbour anchor RE-MERIT at the keeper's OWN unmoved prices?

miso-225 screened the neighbour-anchored PJM ladder JOINTLY with the ruled gas
offer and it failed G-2: every band got $2.3-4.6 cheaper and imports still
**fell** (-75 MW in the cheap hours), because the joint arm's fuel leg pulled
MISO's own price down $1.92 at the same time and a fixed ladder's bands leave
merit when the model's price falls.  The finding named the clean successor: run
the seam arm ALONE.  With MISO's price unmoved, cheaper bands MUST raise
imports, so the direction is unambiguous and unconfounded.

This is that arm's zero-LP phase 0 (rule 29 clause 0).  It computes the STATIC
re-merit: at the keeper's OWN committed hourly ``MISO_external`` price — the bus
the reference-price seam bands sit in — how many PJM import bands cross from
out-of-merit to in-merit when the ladder is re-anchored, and how much MW that is
after the measured deliverability envelope's derate.

Exact to the keeper's own composition:

* per-band width = ``interface_limit_mw / SEAM_FLOW_TRANCHES`` (the reference
  seam's equal-band grid);
* the keeper runs ``miso_seam_envelope_merit_cap = False``, i.e. the UNIFORM
  per-band derate, so band k's hourly availability is
  ``width x clip(cap(h)/interface_limit, 0, 1)`` with ``cap`` the measured
  (month x hour-of-day) import envelope;
* a band clears when its ladder price is strictly below the bus price.

The static number is an upper bound on the LP's response in the same sense
miso-224/225's static re-merit was: it re-prices the stack and re-clears it at
FIXED demand and FIXED everything else, so the LP — which must also re-dispatch
the thermal fleet the imports displace, and which faces the seam's own export
side and the other two seams — realizes some fraction of it.  Both predecessors
realized 0.27-0.39x on the dispatch legs; that conversion band is what makes
this instrument a prediction rather than a target.

Zero-LP.  Rule 22 ``[R-HOLDOUT]``: 2023 (the screen year) plus 2024/2025
band-level reporting only, no solve.  Writes ``_miso226_seam_static_remerit.json``.
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

KEEPER = REPO / "results/calibration/miso220_nonsteamlift_B"
OUT = REPO / "results/calibration/_miso226_seam_static_remerit.json"
YEAR = 2023
ZONE = "MISO-Indiana"          # the C1/G-2 reference hub (miso-224/225)
BUS = "MISO_external"          # the bus the reference-price seam bands sit in
HOURS = 8760


def _keeper_price(zone: str, year: int = YEAR) -> np.ndarray:
    s = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
    s = s[(s["pass"] == "P1") & (s["zone"] == zone)]
    return s.sort_values("hour")["price"].to_numpy(float)


def _keeper_imports(year: int = YEAR) -> np.ndarray:
    c = pd.read_parquet(KEEPER / f"hourly/class_hourly_{year}.parquet")
    c = c[(c["pass"] == "P1") & (c["klass"] == "import")]
    return (
        c.groupby("hour")["mw"].sum().reindex(range(HOURS)).fillna(0.0).to_numpy(float)
    )


def _actual_cheap_mask(year: int = YEAR) -> np.ndarray:
    """The frozen G-2 hour set: the hours the REAL Indiana hub cleared below $20."""
    sys.path.insert(0, str(REPO / "scripts" / "probes"))
    from _miso224_floor_anatomy_phase0 import actual_zone_price

    act = actual_zone_price(year)[ZONE].to_numpy(float)
    return np.isfinite(act) & (act < 20.0)


def main() -> int:
    from market_sim.config.interchange_config import (
        INTERFACE_NEIGHBORS,
        MISO_SEAM_LADDER_BY_YEAR,
        MISO_SEAM_LADDER_NEIGHBOUR_BY_YEAR,
    )
    from market_sim.data.eia_loader import measured_seam_import_envelope
    from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES

    spec = {s.name: s for s in INTERFACE_NEIGHBORS["MISO"]}["PJM"]
    limit = float(spec.interface_limit_mw)
    width = limit / SEAM_FLOW_TRANCHES

    inc = np.asarray(MISO_SEAM_LADDER_BY_YEAR[YEAR]["PJM"]["import"], float)
    neigh = np.asarray(MISO_SEAM_LADDER_NEIGHBOUR_BY_YEAR[YEAR]["PJM"]["import"], float)
    inc_x = np.asarray(MISO_SEAM_LADDER_BY_YEAR[YEAR]["PJM"]["export"], float)
    neigh_x = np.asarray(MISO_SEAM_LADDER_NEIGHBOUR_BY_YEAR[YEAR]["PJM"]["export"], float)

    env = measured_seam_import_envelope("MISO", YEAR, HOURS, None, direction="import")
    cap = np.asarray(env["PJM"], float)
    frac = np.clip(cap / limit, 0.0, 1.0)          # the keeper's uniform derate
    band_mw = width * frac                          # per band, per hour

    p_bus = _keeper_price(BUS)
    p_hub = _keeper_price(ZONE)
    imports = _keeper_imports()
    cheap = _actual_cheap_mask()

    # A band clears when its price is strictly below the bus price.
    in_inc = p_bus[None, :] > inc[:, None]          # (8, 8760)
    in_neigh = p_bus[None, :] > neigh[:, None]
    remerit = in_neigh & ~in_inc                    # bands that NEWLY clear

    mw_inc = (in_inc * band_mw[None, :]).sum(0)
    mw_neigh = (in_neigh * band_mw[None, :]).sum(0)
    d_mw = mw_neigh - mw_inc

    def _stats(mask: np.ndarray, label: str) -> dict:
        n = int(mask.sum())
        return {
            "hour_set": label,
            "n_hours": n,
            "keeper_bus_price_mean": round(float(p_bus[mask].mean()), 3),
            "keeper_hub_price_mean": round(float(p_hub[mask].mean()), 3),
            "keeper_import_mw_mean": round(float(imports[mask].mean()), 1),
            "envelope_derate_frac_mean": round(float(frac[mask].mean()), 4),
            "static_in_merit_mw_incumbent": round(float(mw_inc[mask].mean()), 1),
            "static_in_merit_mw_neighbour": round(float(mw_neigh[mask].mean()), 1),
            "static_delta_mw": round(float(d_mw[mask].mean()), 1),
            "bands_remerited_mean": round(float(remerit[:, mask].sum(0).mean()), 3),
            "hours_with_any_remerit_pct": round(
                100.0 * float((remerit[:, mask].sum(0) > 0).mean()), 1
            ),
        }

    allh = np.ones(HOURS, bool)
    # The model's own cheap hours, for contrast: miso-224 measured the keeper at
    # ZERO model hours below $20, so this set is expected to be empty or tiny —
    # which is exactly why the G-2 hour set is defined on the ACTUAL price.
    model_cheap = p_hub < 20.0

    # Export side: is the overlay's export leg reachable at all? An export band
    # clears only when the bus price is BELOW the band price; the 2023 PJM
    # export rungs are $11.72-12.34 (incumbent) and $7.02-7.73 (neighbour)
    # against a bus mean near $34.5, so this is expected to be structurally
    # inert and the arm a pure import-side test. Measured, not assumed.
    x_inc_hours = int((p_bus[None, :] < inc_x[:, None]).any(0).sum())
    x_neigh_hours = int((p_bus[None, :] < neigh_x[:, None]).any(0).sum())

    rec = {
        "probe": (
            "miso-226 phase 0 — static re-merit of the neighbour-anchored PJM "
            "import ladder at the KEEPER's own unmoved prices (seam-alone arm)"
        ),
        "keeper": "2026-09-05-miso-220-nonsteam-lift (miso220_nonsteamlift_B)",
        "year": YEAR,
        "seam": "PJM",
        "interface_limit_mw": limit,
        "band_width_mw": round(width, 2),
        "composition": "uniform per-band derate (keeper miso_seam_envelope_merit_cap=False)",
        "ladder_import_incumbent": [round(x, 2) for x in inc],
        "ladder_import_neighbour": [round(x, 2) for x in neigh],
        "ladder_import_delta": [round(n - i, 2) for n, i in zip(neigh, inc)],
        "ladder_export_incumbent": [round(x, 2) for x in inc_x],
        "ladder_export_neighbour": [round(x, 2) for x in neigh_x],
        "export_leg": {
            "hours_any_export_band_in_merit_incumbent": x_inc_hours,
            "hours_any_export_band_in_merit_neighbour": x_neigh_hours,
            "note": (
                "an export band clears only when the bus price is BELOW it; both "
                "ladders' export rungs sit far under the model's bus price, so the "
                "overlay's export leg is structurally inert and the arm is a pure "
                "import-side test"
            ),
        },
        "by_hour_set": {
            "all": _stats(allh, "all 8760 hours"),
            "actual_sub20": _stats(cheap, "the 1,230 hours the REAL Indiana hub cleared < $20 (the frozen G-2 set)"),
        },
        "model_sub20_hours": int(model_cheap.sum()),
        "band_marginality_in_g2_hours": {
            f"band{k+1}": {
                "incumbent_price": round(float(inc[k]), 2),
                "neighbour_price": round(float(neigh[k]), 2),
                "pct_g2_hours_in_merit_incumbent": round(
                    100.0 * float(in_inc[k, cheap].mean()), 1
                ),
                "pct_g2_hours_in_merit_neighbour": round(
                    100.0 * float(in_neigh[k, cheap].mean()), 1
                ),
            }
            for k in range(SEAM_FLOW_TRANCHES)
        },
    }
    OUT.write_text(json.dumps(rec, indent=1))
    print(json.dumps(rec["by_hour_set"], indent=1))
    print("export leg:", rec["export_leg"])
    print(f"-> {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
